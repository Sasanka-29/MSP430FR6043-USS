#!/usr/bin/python
"""
Spirometer Serial Monitor GUI
- Volume Flow Rate live plot (flow vs time)
- Baseline calibration (no-flow offset removal)
- Real-time Flow-Volume loop: exhalation above zero, inhalation below,
  x-axis = cumulative volume (integral of flow), matching clinical spirometry curves
"""
import re
import struct
import threading
import queue
import time
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from collections import deque
from datetime import datetime
import numpy as np

import serial
import serial.tools.list_ports
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.signal import butter, lfilter_zi, lfilter

# ── Constants ──────────────────────────────────────────────────────────────────
DELIM_DICT  = {"!": "VFR"}
CHANNELS    = ["VFR"]
MAX_POINTS  = 600
LPF_CUTOFF  = 15.0
LPF_ORDER   = 2
SAMPLE_RATE = 500.0          # Hz

# VFR unit is L/h; convert to L/s for volume integration
LH_TO_LS    = 1.0 / 3600.0

FLOW_THRESHOLD  = 30.0       # L/h deadband
BREATH_MIN_SECS = 0.2
CAL_DURATION_S  = 5.0

# UI palette
BG_MAIN      = "#d4d0c8"
BG_PANEL     = "#ece9d8"
BG_PLOT      = "#ffffff"
BG_CTRL      = "#d4d0c8"
BG_CAL       = "#fff8e1"
BG_BREATH    = "#e8f5e9"
FG_LABEL     = "#1a1a1a"
ACCENT_GREEN = "#008000"
ACCENT_RED   = "#cc0000"
ACCENT_BLUE  = "#003399"
ACCENT_ORA   = "#e65100"
BORDER_CLR   = "#808080"

COL_EXHALE   = "#1a5fa8"    # dark blue — exhalation (above 0)
COL_INHALE   = "#c0392b"    # dark red  — inhalation (below 0)
COL_VFR      = "#4a90d9"
COL_LOOP     = "#1a3a6b"    # completed loop outline

FONT_TITLE  = ("Arial", 10, "bold")
FONT_LABEL  = ("Arial", 9)
FONT_STAT   = ("Arial", 8)
FONT_BTN    = ("Arial", 9, "bold")
FONT_MONO   = ("Courier New", 8)
FONT_BIG    = ("Arial", 13, "bold")


def _make_butter(cutoff_hz, fs, order=2):
    nyq = fs / 2.0
    cutoff_hz = min(cutoff_hz, nyq * 0.95)
    cutoff_hz = max(cutoff_hz, 0.01)
    b, a = butter(order, cutoff_hz / nyq, btype="low", analog=False)
    return b, a


def parse_line(raw_line: str):
    line = re.sub(r"\s+", "", raw_line.strip())
    parts = line.split(",")
    if len(parts) < 2:
        return None
    key, hex_s = parts[0], parts[1]
    if key not in DELIM_DICT:
        return None
    if not re.fullmatch(r"[0-9A-Fa-f]{1,8}", hex_s):
        return None
    try:
        int_val = int(hex_s, 16)
        value   = struct.unpack(">f", struct.pack(">I", int_val))[0]
        return DELIM_DICT[key], value
    except (ValueError, struct.error):
        return None


def _stats_str(vals):
    if len(vals) < 2:
        return "Mean= --  Min= --  Max= --  σ= --"
    a = np.array(list(vals), dtype=float)
    return (f"Mean= {np.mean(a):.2f}  Min= {np.min(a):.2f}  "
            f"Max= {np.max(a):.2f}  σ= {np.std(a):.2f}")


# ── Main App ───────────────────────────────────────────────────────────────────
class SerialMonitorApp:
    POLL_MS = 50
    PLOT_MS = 120

    STATE_IDLE   = "idle"
    STATE_EXHALE = "exhale"
    STATE_INHALE = "inhale"

    def __init__(self, root):
        self.root = root
        self.root.title("Spirometer Monitor")
        self.root.configure(bg=BG_MAIN)
        self.root.geometry("1200x940")
        self.root.minsize(1000, 800)

        # ── Data buffers ──────────────────────────────────────────────────────
        self.data       = {ch: deque(maxlen=MAX_POINTS) for ch in CHANNELS}
        self.times      = {ch: deque(maxlen=MAX_POINTS) for ch in CHANNELS}
        self.t0         = time.time()
        self.t_prev     = self.t0      # for dt integration
        self.plot_dirty = False
        self.locked     = False

        # ── Filter state ──────────────────────────────────────────────────────
        self.filter_enabled = tk.BooleanVar(value=True)
        self.cutoff_var     = tk.DoubleVar(value=LPF_CUTOFF)
        b0, a0 = _make_butter(LPF_CUTOFF, SAMPLE_RATE, LPF_ORDER)
        zi0 = lfilter_zi(b0, a0)
        self.filter_b  = {ch: b0.copy() for ch in CHANNELS}
        self.filter_a  = {ch: a0.copy() for ch in CHANNELS}
        self.filter_zi = {ch: zi0.copy() for ch in CHANNELS}

        # ── Baseline calibration ──────────────────────────────────────────────
        self.baseline_offset = 0.0
        self.cal_active      = False
        self.cal_samples     = []
        self.cal_start_time  = 0.0

        # ── Flow-Volume loop state ────────────────────────────────────────────
        # A full breath cycle = one exhalation + one inhalation (or vice versa)
        # We accumulate volume by integrating flow over time.
        self.breath_state    = self.STATE_IDLE
        self.breath_start_t  = 0.0
        self.breath_count    = 0

        # Buffers for the CURRENT in-progress breath segment (flow vs volume)
        self.seg_vol  = []    # cumulative volume within this segment (L)
        self.seg_flow = []    # flow values (L/h) — kept as-is for y-axis

        # The last completed full loop (exhalation + inhalation combined)
        self.loop_vol  = []   # volume axis for completed loop
        self.loop_flow = []   # flow axis for completed loop

        # Accumulated volume tracker across the full cycle
        self.cycle_vol_acc    = 0.0   # running volume accumulator (L)
        self.exhale_vol       = 0.0   # total exhaled volume
        self.exhale_peak_flow = 0.0   # PEF
        self.inhale_peak_flow = 0.0
        self.fev1_flow_pts    = []    # flow samples in first 1s of exhalation
        self.fev1_vol_pts     = []    # volume during first 1s

        # Live partial loop (drawn in real time as user breathes)
        self.live_vol  = []
        self.live_flow = []

        # ── Serial / CSV ──────────────────────────────────────────────────────
        self.rx_queue = queue.Queue()
        self.ser = self.running = self.read_thread = None
        self.csv_file = self.csv_writer = self.csv_path = None

        self._build_ui()
        self._refresh_ports()
        self._poll_queue()
        self._schedule_plot()

    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # ── Control Panel ─────────────────────────────────────────────────────
        cp = tk.LabelFrame(self.root, text="Control Panel",
                           bg=BG_CTRL, fg=FG_LABEL,
                           font=FONT_LABEL, relief="groove", bd=2)
        cp.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 2))

        r0 = tk.Frame(cp, bg=BG_CTRL)
        r0.pack(fill=tk.X, padx=6, pady=(4, 2))
        self._btn(r0, "▶  Start",          self._connect_wrap,   bg="#e8f5e9", fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=3)
        self._btn(r0, "■  Stop",            self._disconnect_wrap, bg="#ffebee", fg=ACCENT_RED).pack(side=tk.LEFT, padx=3)
        self._btn(r0, "🔒 Lock All",        self._toggle_lock,    bg=BG_PANEL).pack(side=tk.LEFT, padx=3)
        self._btn(r0, "💾 Save Waveforms",  self._toggle_save,    bg=BG_PANEL).pack(side=tk.LEFT, padx=3)
        self._btn(r0, "↺  Reset Graphs",    self._clear_data,     bg=BG_PANEL).pack(side=tk.LEFT, padx=3)
        self.status_lbl = tk.Label(r0, text="● Disconnected",
                                   bg=BG_CTRL, fg=ACCENT_RED, font=FONT_BTN)
        self.status_lbl.pack(side=tk.RIGHT, padx=8)

        r1 = tk.Frame(cp, bg=BG_CTRL)
        r1.pack(fill=tk.X, padx=6, pady=(2, 4))
        tk.Label(r1, text="PORT:", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_cb = ttk.Combobox(r1, textvariable=self.port_var,
                                    width=10, state="readonly", font=FONT_LABEL)
        self.port_cb.pack(side=tk.LEFT, padx=(2, 8))
        tk.Label(r1, text="BAUD:", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)
        self.baud_var = tk.StringVar(value="115200")
        ttk.Combobox(r1, textvariable=self.baud_var, width=9, state="readonly",
                     font=FONT_LABEL,
                     values=["9600","19200","38400","57600",
                             "115200","230400","460800","921600"]).pack(side=tk.LEFT, padx=(2, 8))
        self._btn(r1, "Refresh", self._refresh_ports, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 12))
        tk.Frame(r1, bg=BORDER_CLR, width=2, height=22).pack(side=tk.LEFT, padx=8)

        tk.Label(r1, text="LPF:", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT, padx=(0, 2))
        tk.Checkbutton(r1, text="On", variable=self.filter_enabled,
                       bg=BG_CTRL, fg=ACCENT_GREEN, font=FONT_LABEL,
                       selectcolor=BG_CTRL, activebackground=BG_CTRL,
                       command=self._on_filter_toggle).pack(side=tk.LEFT)
        tk.Label(r1, text="Cutoff:", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT, padx=(6, 2))
        self.cutoff_slider = tk.Scale(
            r1, from_=1, to=200, orient=tk.HORIZONTAL, resolution=0.5,
            variable=self.cutoff_var, bg=BG_CTRL, fg=FG_LABEL,
            troughcolor="#b0b0b0", highlightthickness=0, bd=1,
            length=140, font=("Arial", 7), showvalue=False,
            command=self._on_cutoff_change)
        self.cutoff_slider.pack(side=tk.LEFT, padx=(0, 2))
        vcmd = (self.root.register(self._validate_cutoff), "%P")
        self.cutoff_entry = tk.Entry(r1, textvariable=self.cutoff_var, width=6,
                                     bg="white", fg=ACCENT_BLUE, font=FONT_MONO,
                                     relief="sunken", bd=2,
                                     validate="key", validatecommand=vcmd)
        self.cutoff_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.cutoff_entry.bind("<Return>",   self._on_cutoff_commit)
        self.cutoff_entry.bind("<FocusOut>", self._on_cutoff_commit)
        tk.Label(r1, text="Hz", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)
        self.filter_status_lbl = tk.Label(
            r1, text=f"[{LPF_CUTOFF:.1f} Hz]",
            bg=BG_CTRL, fg=ACCENT_BLUE, font=("Arial", 8, "bold"))
        self.filter_status_lbl.pack(side=tk.LEFT, padx=(4, 0))

        # ── Main content area ─────────────────────────────────────────────────
        mid = tk.Frame(self.root, bg=BG_MAIN)
        mid.grid(row=1, column=0, sticky="nsew", padx=6, pady=2)
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)
        mid.rowconfigure(0, weight=0)   # calibration strip
        mid.rowconfigure(1, weight=1)   # live VFR
        mid.rowconfigure(2, weight=0)   # stats
        mid.rowconfigure(3, weight=2)   # flow-volume loop

        # ── Calibration panel ─────────────────────────────────────────────────
        cal_frame = tk.LabelFrame(mid, text="Baseline Calibration  (Ensure No Flow)",
                                  bg=BG_CAL, fg=ACCENT_ORA,
                                  font=FONT_TITLE, relief="groove", bd=2)
        cal_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        cal_inner = tk.Frame(cal_frame, bg=BG_CAL)
        cal_inner.pack(fill=tk.X, padx=8, pady=4)
        self._btn(cal_inner, "⬤  Start Calibration", self._start_calibration,
                  bg="#fff3cd", fg=ACCENT_ORA).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(cal_inner, text="Duration (s):", bg=BG_CAL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)
        self.cal_dur_var = tk.DoubleVar(value=CAL_DURATION_S)
        tk.Spinbox(cal_inner, from_=1, to=30, increment=1,
                   textvariable=self.cal_dur_var, width=4,
                   font=FONT_LABEL, bg="white").pack(side=tk.LEFT, padx=(2, 16))
        tk.Label(cal_inner, text="Offset:", bg=BG_CAL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)
        self.baseline_var = tk.StringVar(value="0.00 L/h")
        tk.Label(cal_inner, textvariable=self.baseline_var,
                 bg=BG_CAL, fg=ACCENT_BLUE, font=FONT_BIG).pack(side=tk.LEFT, padx=(4, 16))
        self.cal_status_var = tk.StringVar(value="Ready — connect and hold still before calibrating.")
        self.cal_status_lbl = tk.Label(cal_inner, textvariable=self.cal_status_var,
                                       bg=BG_CAL, fg=BORDER_CLR, font=FONT_STAT)
        self.cal_status_lbl.pack(side=tk.LEFT, padx=(0, 8))
        self.cal_progress = ttk.Progressbar(cal_inner, orient="horizontal",
                                            length=130, mode="determinate")
        self.cal_progress.pack(side=tk.LEFT)

        thr_row = tk.Frame(cal_frame, bg=BG_CAL)
        thr_row.pack(fill=tk.X, padx=8, pady=(0, 4))
        tk.Label(thr_row, text="Breath detection threshold:",
                 bg=BG_CAL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)
        self.thr_var = tk.DoubleVar(value=FLOW_THRESHOLD)
        tk.Spinbox(thr_row, from_=1, to=500, increment=5,
                   textvariable=self.thr_var, width=6,
                   font=FONT_LABEL, bg="white").pack(side=tk.LEFT, padx=(4, 4))
        tk.Label(thr_row, text="L/h", bg=BG_CAL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)

        # ── Live VFR plot (top-left) ───────────────────────────────────────────
        vfr_lf = tk.LabelFrame(mid, text="Volume Flow Rate — Live (Flow vs Time)",
                               bg=BG_MAIN, fg=FG_LABEL,
                               font=FONT_TITLE, relief="groove", bd=2)
        vfr_lf.grid(row=1, column=0, sticky="nsew", padx=(0, 3))
        vfr_lf.columnconfigure(0, weight=1)
        vfr_lf.rowconfigure(0, weight=1)

        self.fig_vfr = Figure(facecolor=BG_MAIN)
        self.ax_vfr  = self.fig_vfr.add_subplot(111)
        self._style_ax(self.ax_vfr, ylabel="Flow (L/h)")
        self.ax_vfr.set_ylim(-1000, 1000)
        self.ax_vfr.axhline(0, color="#999999", linewidth=0.8, linestyle="--")
        self.ax_vfr.set_xlabel("Time", fontsize=7, color="#555555")
        self.line_vfr, = self.ax_vfr.plot([], [], color=COL_VFR,
                                           linewidth=1.0, antialiased=True)
        self.fig_vfr.subplots_adjust(left=0.10, right=0.98, top=0.95, bottom=0.12)
        cv_vfr = FigureCanvasTkAgg(self.fig_vfr, master=vfr_lf)
        cv_vfr.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.canvas_vfr = cv_vfr

        # VFR stats
        self.vfr_stat_var = tk.StringVar(value="Mean= --  Min= --  Max= --  σ= --")
        tk.Label(mid, textvariable=self.vfr_stat_var,
                 bg=BG_MAIN, fg=FG_LABEL, font=FONT_STAT).grid(
                 row=2, column=0, sticky="ew", pady=(2, 2))

        # ── Breath state panel (top-right) ────────────────────────────────────
        state_lf = tk.LabelFrame(mid, text="Breath State",
                                 bg=BG_BREATH, fg=ACCENT_GREEN,
                                 font=FONT_TITLE, relief="groove", bd=2)
        state_lf.grid(row=1, column=1, sticky="nsew", padx=(3, 0))
        state_lf.columnconfigure(0, weight=1)

        self.breath_state_var = tk.StringVar(value="— IDLE —")
        self.breath_state_lbl = tk.Label(state_lf, textvariable=self.breath_state_var,
                                         bg=BG_BREATH, fg=BORDER_CLR, font=FONT_BIG)
        self.breath_state_lbl.pack(pady=(10, 4))

        # Live metric labels
        metrics_frame = tk.Frame(state_lf, bg=BG_BREATH)
        metrics_frame.pack(fill=tk.X, padx=10)

        self.breath_count_var = tk.StringVar(value="Breath cycles: 0")
        self.pef_var          = tk.StringVar(value="PEF:  --  L/h")
        self.fvc_var          = tk.StringVar(value="FVC:  --  L")
        self.fev1_var         = tk.StringVar(value="FEV1: --  L")
        self.ratio_var        = tk.StringVar(value="FEV1/FVC: --")
        self.dur_var          = tk.StringVar(value="Duration: --")
        self.live_flow_var    = tk.StringVar(value="Current flow: --")

        for sv, col in [
            (self.breath_count_var, FG_LABEL),
            (self.live_flow_var,    ACCENT_BLUE),
            (self.pef_var,          ACCENT_ORA),
            (self.fvc_var,          FG_LABEL),
            (self.fev1_var,         FG_LABEL),
            (self.ratio_var,        ACCENT_GREEN),
            (self.dur_var,          FG_LABEL),
        ]:
            tk.Label(metrics_frame, textvariable=sv, bg=BG_BREATH,
                     fg=col, font=("Arial", 9), anchor="w").pack(fill=tk.X, pady=1)

        # Breath history listbox
        tk.Label(state_lf, text="History:", bg=BG_BREATH,
                 fg=FG_LABEL, font=FONT_STAT).pack(anchor="w", padx=10, pady=(8, 0))
        hist_outer = tk.Frame(state_lf, bg=BG_BREATH)
        hist_outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))
        self.breath_hist_box = tk.Listbox(hist_outer, bg="white", fg=FG_LABEL,
                                          font=FONT_MONO, relief="sunken", bd=1,
                                          selectbackground="#cfe2ff")
        self.breath_hist_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hs = ttk.Scrollbar(hist_outer, command=self.breath_hist_box.yview)
        hs.pack(side=tk.RIGHT, fill=tk.Y)
        self.breath_hist_box["yscrollcommand"] = hs.set

        # ── Flow-Volume Loop plot (bottom-left) ───────────────────────────────
        fvl_lf = tk.LabelFrame(mid, text="Flow-Volume Loop  (Exhalation ↑  /  Inhalation ↓)",
                               bg=BG_MAIN, fg=FG_LABEL,
                               font=FONT_TITLE, relief="groove", bd=2)
        fvl_lf.grid(row=3, column=0, sticky="nsew", padx=(0, 3), pady=(4, 0))
        fvl_lf.columnconfigure(0, weight=1)
        fvl_lf.rowconfigure(0, weight=1)

        self.fig_fvl = Figure(facecolor=BG_MAIN)
        self.ax_fvl  = self.fig_fvl.add_subplot(111)
        self._style_ax(self.ax_fvl, ylabel="Flow (L/h)")
        self.ax_fvl.set_xlabel("Volume (L)", fontsize=7, color="#555555")
        self.ax_fvl.axhline(0, color="#999999", linewidth=0.8, linestyle="--")
        self.ax_fvl.axvline(0, color="#cccccc", linewidth=0.5, linestyle=":")

        # Completed loop — solid dark line
        self.line_loop,  = self.ax_fvl.plot([], [], color=COL_LOOP,
                                              linewidth=1.6, antialiased=True,
                                              zorder=3)
        # Exhalation segment of live breath — blue
        self.line_exhale_live, = self.ax_fvl.plot([], [], color=COL_EXHALE,
                                                    linewidth=1.4, antialiased=True,
                                                    linestyle="--", zorder=4)
        # Inhalation segment of live breath — red
        self.line_inhale_live, = self.ax_fvl.plot([], [], color=COL_INHALE,
                                                    linewidth=1.4, antialiased=True,
                                                    linestyle="--", zorder=4)

        # Annotation text objects for PEF, FVC, FEV1
        self.ann_pef  = self.ax_fvl.annotate("", xy=(0,0), xytext=(0,0),
                            fontsize=7, color=COL_EXHALE,
                            arrowprops=dict(arrowstyle="-", color=COL_EXHALE, lw=0.8))
        self.ann_fvc  = self.ax_fvl.annotate("", xy=(0,0), xytext=(0,0),
                            fontsize=7, color="#555555")
        self.ann_fev1 = self.ax_fvl.annotate("", xy=(0,0), xytext=(0,0),
                            fontsize=7, color="#555555")

        self.fig_fvl.subplots_adjust(left=0.10, right=0.97, top=0.93, bottom=0.14)
        cv_fvl = FigureCanvasTkAgg(self.fig_fvl, master=fvl_lf)
        cv_fvl.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.canvas_fvl = cv_fvl

        # ── Blank bottom-right (keeps grid balanced) ──────────────────────────
        ph = tk.LabelFrame(mid, text="Spirometry Parameters",
                           bg=BG_BREATH, fg=ACCENT_GREEN,
                           font=FONT_TITLE, relief="groove", bd=2)
        ph.grid(row=3, column=1, sticky="nsew", padx=(3, 0), pady=(4, 0))
        ph.columnconfigure(0, weight=1)

        self.param_pef_var   = tk.StringVar(value="PEF  (Peak Expiratory Flow)   --")
        self.param_fvc_var   = tk.StringVar(value="FVC  (Forced Vital Capacity)  --")
        self.param_fev1_var  = tk.StringVar(value="FEV1 (Forced Exp. Vol. 1s)    --")
        self.param_ratio_var = tk.StringVar(value="FEV1 / FVC                    --")
        self.param_pif_var   = tk.StringVar(value="PIF  (Peak Inspiratory Flow)  --")

        tk.Label(ph, text="Last completed cycle:", bg=BG_BREATH,
                 fg=FG_LABEL, font=("Arial", 8, "bold")).pack(anchor="w", padx=10, pady=(8,2))

        for sv in (self.param_pef_var, self.param_fvc_var,
                   self.param_fev1_var, self.param_ratio_var, self.param_pif_var):
            tk.Label(ph, textvariable=sv, bg=BG_BREATH, fg=FG_LABEL,
                     font=FONT_MONO, anchor="w").pack(fill=tk.X, padx=14, pady=1)

        # ── Log ───────────────────────────────────────────────────────────────
        self.root.rowconfigure(2, weight=0)
        log_frame = tk.Frame(self.root, bg=BG_MAIN)
        log_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))
        tk.Label(log_frame, text="RAW LOG:", bg=BG_MAIN,
                 fg=BORDER_CLR, font=FONT_STAT).pack(side=tk.LEFT, padx=(0, 4))
        self.log_text = tk.Text(log_frame, height=3, bg="#1a1a2e",
                                fg="#a0a0b0", font=FONT_MONO,
                                relief="sunken", bd=2, state="disabled")
        self.log_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        sb = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text["yscrollcommand"] = sb.set

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _btn(self, parent, text, cmd, bg=BG_PANEL, fg=FG_LABEL):
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg, font=FONT_BTN,
                         relief="raised", bd=2, padx=8, pady=3,
                         cursor="hand2", activebackground="#c0c0c0")

    def _style_ax(self, ax, ylabel=""):
        ax.set_facecolor(BG_PLOT)
        ax.tick_params(colors="#333333", labelsize=7)
        ax.set_ylabel(ylabel, fontsize=7, color="#555555")
        ax.grid(True, color="#e0e0e0", linewidth=0.5, linestyle="-")
        ax.spines[:].set_color(BORDER_CLR)
        ax.spines[:].set_linewidth(0.8)

    # ── Calibration ───────────────────────────────────────────────────────────
    def _start_calibration(self):
        if not self.running:
            messagebox.showwarning("Not connected",
                                   "Connect to a port before calibrating.")
            return
        if self.cal_active:
            return
        self.cal_active     = True
        self.cal_samples    = []
        self.cal_start_time = time.time()
        dur = self.cal_dur_var.get()
        self.cal_progress["value"] = 0
        self.cal_status_var.set(f"Collecting {dur:.0f}s no-flow samples…")
        self.cal_status_lbl.configure(fg=ACCENT_ORA)
        self._cal_tick(dur)

    def _cal_tick(self, dur):
        if not self.cal_active:
            return
        elapsed = time.time() - self.cal_start_time
        self.cal_progress["value"] = min(elapsed / dur * 100, 100)
        if elapsed >= dur:
            self._finish_calibration()
        else:
            self.root.after(200, lambda: self._cal_tick(dur))

    def _finish_calibration(self):
        self.cal_active = False
        self.cal_progress["value"] = 100
        if len(self.cal_samples) < 5:
            self.cal_status_var.set("Not enough samples received.")
            self.cal_status_lbl.configure(fg=ACCENT_RED)
            return
        self.baseline_offset = float(np.mean(self.cal_samples))
        std = np.std(self.cal_samples)
        n   = len(self.cal_samples)
        self.baseline_var.set(f"{self.baseline_offset:+.2f} L/h")
        self.cal_status_var.set(f"Done  n={n}  σ={std:.2f} L/h  — offset applied.")
        self.cal_status_lbl.configure(fg=ACCENT_GREEN)
        self._log(f"[CAL] offset={self.baseline_offset:.4f}  n={n}  σ={std:.2f}\n")

    # ── Breath / Flow-Volume state machine ────────────────────────────────────
    def _process_sample(self, flow_lh, t):
        """
        Integrate flow to build the Flow-Volume loop in real time.
        Convention (matches the reference image):
          - Exhalation: flow > 0  → plotted ABOVE zero
          - Inhalation: flow < 0  → plotted BELOW zero
          - Volume x-axis: increases during exhalation (left→right),
            decreases back during inhalation (right→left), closing the loop.
        """
        dt   = t - self.t_prev
        self.t_prev = t
        thr  = self.thr_var.get()

        # dV in litres (flow is L/h → convert to L/s × dt)
        dv = flow_lh * LH_TO_LS * dt

        if self.breath_state == self.STATE_IDLE:
            if flow_lh > thr:
                # Start of exhalation
                self.breath_state    = self.STATE_EXHALE
                self.breath_start_t  = t
                self.cycle_vol_acc   = 0.0
                self.exhale_vol      = 0.0
                self.exhale_peak_flow= 0.0
                self.inhale_peak_flow= 0.0
                self.fev1_flow_pts   = []
                self.fev1_vol_pts    = []
                self.seg_vol         = [0.0]
                self.seg_flow        = [flow_lh]
                self.live_vol        = [0.0]
                self.live_flow       = [flow_lh]
            elif flow_lh < -thr:
                # Start of inhalation (standalone, no preceding exhalation)
                self.breath_state    = self.STATE_INHALE
                self.breath_start_t  = t
                self.cycle_vol_acc   = 0.0
                self.seg_vol         = [0.0]
                self.seg_flow        = [flow_lh]
                self.live_vol        = [0.0]
                self.live_flow       = [flow_lh]

        elif self.breath_state == self.STATE_EXHALE:
            self.cycle_vol_acc += dv
            self.seg_vol.append(self.cycle_vol_acc)
            self.seg_flow.append(flow_lh)
            self.live_vol  = self.seg_vol[:]
            self.live_flow = self.seg_flow[:]

            if flow_lh > self.exhale_peak_flow:
                self.exhale_peak_flow = flow_lh

            # FEV1: volume accumulated in first 1 s
            elapsed = t - self.breath_start_t
            if elapsed <= 1.0:
                self.fev1_vol_pts.append(self.cycle_vol_acc)

            if flow_lh <= thr:
                # Exhalation ended — save exhaled volume
                self.exhale_vol = self.cycle_vol_acc
                # Transition to inhalation phase (stay at same volume point)
                self.breath_state = self.STATE_INHALE
                # Keep accumulating from exhale endpoint
                self.seg_vol  = [self.cycle_vol_acc]
                self.seg_flow = [flow_lh]

        elif self.breath_state == self.STATE_INHALE:
            self.cycle_vol_acc += dv
            self.seg_vol.append(self.cycle_vol_acc)
            self.seg_flow.append(flow_lh)

            if abs(flow_lh) > self.inhale_peak_flow:
                self.inhale_peak_flow = abs(flow_lh)

            # Append inhalation to live loop (continues from exhalation end)
            self.live_vol  = self.live_vol + self.seg_vol[1:]
            self.live_flow = self.live_flow + self.seg_flow[1:]

            if flow_lh >= -thr:
                # Inhalation ended — complete the loop
                self._finish_loop(t)

    def _finish_loop(self, t):
        dur = t - self.breath_start_t
        if dur < BREATH_MIN_SECS or len(self.live_vol) < 5:
            self.breath_state = self.STATE_IDLE
            return

        # Compute spirometry parameters
        fvc  = self.exhale_vol                      # L
        pef  = self.exhale_peak_flow                # L/h
        pif  = self.inhale_peak_flow                # L/h
        fev1_vol = self.fev1_vol_pts[-1] if self.fev1_vol_pts else 0.0   # L
        ratio = (fev1_vol / fvc * 100) if fvc > 0 else 0.0

        self.breath_count += 1
        self.loop_vol  = self.live_vol[:]
        self.loop_flow = self.live_flow[:]

        # Update parameter labels
        self.pef_var.set(  f"PEF:  {pef:.1f}  L/h")
        self.fvc_var.set(  f"FVC:  {fvc:.4f}  L")
        self.fev1_var.set( f"FEV1: {fev1_vol:.4f}  L")
        self.ratio_var.set(f"FEV1/FVC: {ratio:.1f}%")
        self.dur_var.set(  f"Duration: {dur:.2f} s")

        self.param_pef_var.set(  f"PEF  (Peak Expiratory Flow)   {pef:.1f} L/h")
        self.param_fvc_var.set(  f"FVC  (Forced Vital Capacity)  {fvc:.4f} L")
        self.param_fev1_var.set( f"FEV1 (Forced Exp. Vol. 1s)    {fev1_vol:.4f} L")
        self.param_ratio_var.set(f"FEV1 / FVC                    {ratio:.1f}%")
        self.param_pif_var.set(  f"PIF  (Peak Inspiratory Flow)  {pif:.1f} L/h")

        # History log
        self.breath_hist_box.insert(
            tk.END,
            f"#{self.breath_count:3d}  PEF={pef:.0f}  FVC={fvc:.3f}L  dur={dur:.2f}s")
        self.breath_hist_box.see(tk.END)
        self._log(f"[LOOP #{self.breath_count}] PEF={pef:.1f} FVC={fvc:.4f}L "
                  f"FEV1={fev1_vol:.4f}L ratio={ratio:.1f}%\n")

        # Clear live buffers
        self.live_vol  = []
        self.live_flow = []
        self.breath_state = self.STATE_IDLE

    # ── Redraw ────────────────────────────────────────────────────────────────
    def _update_breath_state_ui(self):
        state = self.breath_state
        if state == self.STATE_EXHALE:
            self.breath_state_var.set("↑ EXHALING")
            self.breath_state_lbl.configure(fg=COL_EXHALE)
            if self.seg_flow:
                self.live_flow_var.set(f"Current flow: {self.seg_flow[-1]:.1f} L/h")
        elif state == self.STATE_INHALE:
            self.breath_state_var.set("↓ INHALING")
            self.breath_state_lbl.configure(fg=COL_INHALE)
            if self.seg_flow:
                self.live_flow_var.set(f"Current flow: {self.seg_flow[-1]:.1f} L/h")
        else:
            self.breath_state_var.set("— IDLE —")
            self.breath_state_lbl.configure(fg=BORDER_CLR)
            self.live_flow_var.set("Current flow: 0.0 L/h")
        self.breath_count_var.set(f"Breath cycles: {self.breath_count}")

    def _redraw_fvl(self):
        """Redraw the Flow-Volume loop plot."""
        ax = self.ax_fvl
        dirty = False

        # Completed loop
        if len(self.loop_vol) >= 2:
            self.line_loop.set_data(self.loop_vol, self.loop_flow)
            dirty = True

        # Live breath-in-progress
        state = self.breath_state
        if state == self.STATE_EXHALE and len(self.seg_vol) >= 2:
            self.line_exhale_live.set_data(self.seg_vol, self.seg_flow)
            self.line_inhale_live.set_data([], [])
            dirty = True
        elif state == self.STATE_INHALE and len(self.live_vol) >= 2:
            # Split live loop: exhale part (flow>0) and inhale part (flow<0)
            # Find split index (where inhalation started)
            split = next((i for i, f in enumerate(self.live_flow) if f < 0), None)
            if split is not None:
                self.line_exhale_live.set_data(
                    self.live_vol[:split+1], self.live_flow[:split+1])
                self.line_inhale_live.set_data(
                    self.live_vol[split:],   self.live_flow[split:])
            else:
                self.line_exhale_live.set_data(self.live_vol, self.live_flow)
                self.line_inhale_live.set_data([], [])
            dirty = True
        else:
            if state == self.STATE_IDLE:
                self.line_exhale_live.set_data([], [])
                self.line_inhale_live.set_data([], [])

        # Auto-scale axes to the union of loop + live data
        all_v = self.loop_vol + self.live_vol
        all_f = self.loop_flow + self.live_flow
        if len(all_v) >= 2:
            vmin, vmax = min(all_v), max(all_v)
            fmin, fmax = min(all_f), max(all_f)
            vpad = max((vmax - vmin) * 0.12, 0.02)
            fpad = max((fmax - fmin) * 0.12, 20.0)
            ax.set_xlim(vmin - vpad, vmax + vpad)
            ax.set_ylim(fmin - fpad, fmax + fpad)
            dirty = True

        if dirty:
            self.canvas_fvl.draw_idle()

    def _schedule_plot(self):
        if self.plot_dirty:
            self._redraw()
            self.plot_dirty = False
        self.root.after(self.PLOT_MS, self._schedule_plot)

    def _redraw(self):
        # Live VFR (flow vs time)
        xs_v = list(self.times["VFR"])
        ys_v = list(self.data["VFR"])
        if len(xs_v) >= 2:
            self.line_vfr.set_data(xs_v, ys_v)
            self.ax_vfr.set_xlim(xs_v[0], max(xs_v[-1], xs_v[0] + 1))
            self.ax_vfr.set_ylim(-1000, 1000)
            self._fmt_time_axis(self.ax_vfr, xs_v)
            self.vfr_stat_var.set(_stats_str(self.data["VFR"]))
            self.canvas_vfr.draw_idle()

        # Flow-Volume loop
        self._redraw_fvl()
        self._update_breath_state_ui()

    def _fmt_time_axis(self, ax, xs):
        if not xs:
            return
        ticks  = ax.get_xticks()
        labels = []
        for t in ticks:
            if xs[0] <= t <= xs[-1]:
                m, s = divmod(int(t), 60)
                h, m = divmod(m, 60)
                labels.append(f"{h:02d}:{m:02d}:{s:02d}")
            else:
                labels.append("")
        ax.set_xticklabels(labels, fontsize=6, rotation=15)

    # ── Filter ────────────────────────────────────────────────────────────────
    def _on_filter_toggle(self):
        if self.filter_enabled.get():
            self.filter_status_lbl.configure(
                text=f"[{self.cutoff_var.get():.1f} Hz]", fg=ACCENT_BLUE)
            self.cutoff_slider.configure(state="normal")
            self.cutoff_entry.configure(state="normal")
            self._rebuild_filters()
        else:
            self.filter_status_lbl.configure(text="[OFF]", fg=ACCENT_RED)
            self.cutoff_slider.configure(state="disabled")
            self.cutoff_entry.configure(state="disabled")

    def _on_cutoff_change(self, _=None):
        self.filter_status_lbl.configure(text=f"[{self.cutoff_var.get():.1f} Hz]")
        self._rebuild_filters()

    def _on_cutoff_commit(self, _=None):
        try:
            hz = max(1.0, min(float(self.cutoff_entry.get()), 200.0))
            self.cutoff_var.set(hz)
            self._on_cutoff_change()
        except ValueError:
            pass

    def _validate_cutoff(self, val):
        return val == "" or re.fullmatch(r"\d{0,4}(\.\d{0,2})?", val) is not None

    def _rebuild_filters(self):
        hz = self.cutoff_var.get()
        b, a = _make_butter(hz, SAMPLE_RATE, LPF_ORDER)
        zi   = lfilter_zi(b, a)
        for ch in CHANNELS:
            self.filter_b[ch] = b.copy()
            self.filter_a[ch] = a.copy()
            last = self.data[ch][-1] if self.data[ch] else 0.0
            self.filter_zi[ch] = zi.copy() * last

    # ── Serial ────────────────────────────────────────────────────────────────
    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_cb["values"] = ports
        if ports:
            self.port_var.set(ports[0])

    def _connect_wrap(self):
        if not self.running:
            self._connect()

    def _disconnect_wrap(self):
        if self.running:
            self._disconnect()

    def _connect(self):
        port = self.port_var.get()
        baud = int(self.baud_var.get())
        if not port:
            messagebox.showerror("Error", "Select a COM port first.")
            return
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.running  = True
            self.t0       = time.time()
            self.t_prev   = self.t0
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            self.status_lbl.configure(text=f"● {port} @ {baud}", fg=ACCENT_GREEN)
            self._log(f"[Connected] {port} @ {baud}\n")
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", str(e))

    def _disconnect(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None
        self.status_lbl.configure(text="● Disconnected", fg=ACCENT_RED)
        self._log("[Disconnected]\n")
        if self.csv_file:
            self._stop_save()

    def _read_loop(self):
        while self.running:
            try:
                raw = self.ser.readline().decode("utf-8", errors="replace")
                if raw.strip():
                    self.rx_queue.put_nowait(raw)
            except Exception:
                if self.running:
                    time.sleep(0.02)

    # ── Queue drain ───────────────────────────────────────────────────────────
    def _poll_queue(self):
        for _ in range(50):
            try:
                raw = self.rx_queue.get_nowait()
            except queue.Empty:
                break
            self._log(raw)
            result = parse_line(raw)
            if result:
                ch, val = result
                t = time.time() - self.t0

                if self.filter_enabled.get():
                    filt, self.filter_zi[ch] = lfilter(
                        self.filter_b[ch], self.filter_a[ch],
                        [val], zi=self.filter_zi[ch])
                    val_out = float(filt[0])
                else:
                    val_out = val

                if self.cal_active:
                    self.cal_samples.append(val_out)

                corrected = val_out - self.baseline_offset

                if not self.locked:
                    self.data[ch].append(corrected)
                    self.times[ch].append(t)

                self._process_sample(corrected, t)
                self.plot_dirty = True

                if self.csv_writer:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    self.csv_writer.writerow([ts, ch, f"{corrected:e}"])

        self.root.after(self.POLL_MS, self._poll_queue)

    # ── Lock / Save / Clear ───────────────────────────────────────────────────
    def _toggle_lock(self):
        self.locked = not self.locked
        self._log(f"[{'LOCKED' if self.locked else 'LIVE'}]\n")

    def _toggle_save(self):
        self._stop_save() if self.csv_file else self._start_save()

    def _start_save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Waveforms")
        if not path:
            return
        self.csv_path   = path
        self.csv_file   = open(path, "w", newline="")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Timestamp", "Channel", "Value"])
        self._log(f"[Saving] {path}\n")

    def _stop_save(self):
        if self.csv_file:
            self.csv_file.close()
        self.csv_file = self.csv_writer = None
        self._log(f"[Saved] {self.csv_path}\n")

    def _clear_data(self):
        for ch in CHANNELS:
            self.data[ch].clear()
            self.times[ch].clear()
        self._rebuild_filters()
        self.t0 = self.t_prev = time.time()

        # Reset breath state
        self.breath_state     = self.STATE_IDLE
        self.breath_count     = 0
        self.cycle_vol_acc    = 0.0
        self.seg_vol = self.seg_flow = []
        self.live_vol = self.live_flow = []
        self.loop_vol = self.loop_flow = []
        self.exhale_peak_flow = self.inhale_peak_flow = 0.0
        self.fev1_flow_pts = self.fev1_vol_pts = []

        self.breath_hist_box.delete(0, tk.END)
        self.breath_count_var.set("Breath cycles: 0")
        self.pef_var.set("PEF:  --  L/h")
        self.fvc_var.set("FVC:  --  L")
        self.fev1_var.set("FEV1: --  L")
        self.ratio_var.set("FEV1/FVC: --")
        self.dur_var.set("Duration: --")
        self.live_flow_var.set("Current flow: --")
        self.param_pef_var.set(  "PEF  (Peak Expiratory Flow)   --")
        self.param_fvc_var.set(  "FVC  (Forced Vital Capacity)  --")
        self.param_fev1_var.set( "FEV1 (Forced Exp. Vol. 1s)    --")
        self.param_ratio_var.set("FEV1 / FVC                    --")
        self.param_pif_var.set(  "PIF  (Peak Inspiratory Flow)  --")
        self.vfr_stat_var.set("Mean= --  Min= --  Max= --  σ= --")

        self.line_loop.set_data([], [])
        self.line_exhale_live.set_data([], [])
        self.line_inhale_live.set_data([], [])
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self.canvas_vfr.draw_idle()
        self.canvas_fvl.draw_idle()

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, msg)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def on_close(self):
        self.running = False
        if self.csv_file:
            self.csv_file.close()
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.root.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = SerialMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()