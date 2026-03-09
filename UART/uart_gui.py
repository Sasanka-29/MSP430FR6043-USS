#!/usr/bin/python
"""
Serial Monitor GUI - Industrial-style layout inspired by professional flow meter software.
Layout: Control Panel top bar → large DToF plot (top) → AbsTof overlay + VFR side by side (bottom)
Stats panels below each plot. Filter controls integrated in control panel.
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
from matplotlib.gridspec import GridSpec
from scipy.signal import butter, lfilter_zi, lfilter

# ── Constants ─────────────────────────────────────────────────────────────────
DELIM_DICT   = {"!": "VFR"}
CHANNELS     = ["VFR"]
PLOT_COLORS  = {
    "VFR": "#4a90d9",
}
MAX_POINTS   = 500
LPF_CUTOFF   = 15.0
LPF_ORDER    = 2
SAMPLE_RATE  = 500.0

# UI Colors — light industrial theme matching reference
BG_MAIN      = "#d4d0c8"   # Windows classic gray
BG_PANEL     = "#ece9d8"   # slightly lighter panel
BG_PLOT      = "#ffffff"   # white plot backgrounds
BG_CTRL      = "#d4d0c8"
FG_TEXT      = "#000000"
FG_LABEL     = "#1a1a1a"
ACCENT_GREEN = "#008000"
ACCENT_RED   = "#cc0000"
ACCENT_BLUE  = "#003399"
BORDER_CLR   = "#808080"

FONT_TITLE  = ("Arial", 11, "bold")
FONT_LABEL  = ("Arial", 9)
FONT_STAT   = ("Arial", 8)
FONT_BTN    = ("Arial", 9, "bold")
FONT_MONO   = ("Courier New", 8)


def _make_butter(cutoff_hz, fs, order=2):
    nyq = fs / 2.0
    cutoff_hz = min(cutoff_hz, nyq * 0.95)
    cutoff_hz = max(cutoff_hz, 0.01)
    b, a = butter(order, cutoff_hz / nyq, btype="low", analog=False)
    return b, a


def parse_line(raw_line: str):
    line = raw_line.strip()
    line = re.sub(r"\s+", "", line)
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
    """Return Mean/Min/Max/σ string for a deque."""
    if len(vals) < 2:
        return "Mean= --  Min= --  Max= --  σ= --"
    a = list(vals)
    return (f"Mean= {np.mean(a):.2f}  Min= {np.min(a):.2f}  "
            f"Max= {np.max(a):.2f}  σ= {np.std(a):.2f}")


# ── App ───────────────────────────────────────────────────────────────────────
class SerialMonitorApp:
    POLL_MS = 50
    PLOT_MS = 120

    def __init__(self, root):
        self.root = root
        self.root.title("Flow Meter Serial Monitor")
        self.root.configure(bg=BG_MAIN)
        self.root.geometry("1100x820")
        self.root.minsize(900, 700)

        self.rx_queue   = queue.Queue()
        self.data       = {ch: deque(maxlen=MAX_POINTS) for ch in CHANNELS}
        self.times      = {ch: deque(maxlen=MAX_POINTS) for ch in CHANNELS}
        self.t0         = time.time()
        self.plot_dirty = False
        self.locked     = False

        # Filter state
        self.filter_enabled = tk.BooleanVar(value=True)
        self.cutoff_var     = tk.DoubleVar(value=LPF_CUTOFF)
        b0, a0 = _make_butter(LPF_CUTOFF, SAMPLE_RATE, LPF_ORDER)
        zi0 = lfilter_zi(b0, a0)
        self.filter_b  = {ch: b0.copy() for ch in CHANNELS}
        self.filter_a  = {ch: a0.copy() for ch in CHANNELS}
        self.filter_zi = {ch: zi0.copy() for ch in CHANNELS}

        # Serial / CSV state
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

        # ── Control Panel (top bar) ───────────────────────────────────────────
        cp = tk.LabelFrame(self.root, text="Control Panel",
                           bg=BG_CTRL, fg=FG_LABEL,
                           font=FONT_LABEL, relief="groove", bd=2)
        cp.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 2))

        # Row 0 – action buttons + connection
        row0 = tk.Frame(cp, bg=BG_CTRL)
        row0.pack(fill=tk.X, padx=6, pady=(4, 2))

        self._btn(row0, "▶  Start",  self._connect_wrap,   bg="#e8f5e9", fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=3)
        self._btn(row0, "■  Stop",   self._disconnect_wrap, bg="#ffebee", fg=ACCENT_RED).pack(side=tk.LEFT, padx=3)
        self._btn(row0, "🔒 Lock All",   self._toggle_lock,    bg=BG_PANEL).pack(side=tk.LEFT, padx=3)
        self._btn(row0, "💾 Save Waveforms", self._toggle_save, bg=BG_PANEL).pack(side=tk.LEFT, padx=3)
        self._btn(row0, "↺  Reset Graphs",   self._clear_data,  bg=BG_PANEL).pack(side=tk.LEFT, padx=3)

        # status indicator
        self.status_var = tk.StringVar(value="● Disconnected")
        tk.Label(row0, textvariable=self.status_var, bg=BG_CTRL,
                 fg=ACCENT_RED, font=FONT_BTN).pack(side=tk.RIGHT, padx=8)

        # Row 1 – port/baud + filter
        row1 = tk.Frame(cp, bg=BG_CTRL)
        row1.pack(fill=tk.X, padx=6, pady=(2, 4))

        tk.Label(row1, text="PORT:", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_cb = ttk.Combobox(row1, textvariable=self.port_var,
                                    width=10, state="readonly", font=FONT_LABEL)
        self.port_cb.pack(side=tk.LEFT, padx=(2, 8))

        tk.Label(row1, text="BAUD:", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)
        self.baud_var = tk.StringVar(value="115200")
        ttk.Combobox(row1, textvariable=self.baud_var, width=9, state="readonly",
                     font=FONT_LABEL,
                     values=["9600","19200","38400","57600",
                             "115200","230400","460800","921600"]).pack(side=tk.LEFT, padx=(2, 8))
        self._btn(row1, "Refresh", self._refresh_ports, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 16))

        # Separator line
        tk.Frame(row1, bg=BORDER_CLR, width=2, height=22).pack(side=tk.LEFT, padx=8)

        # Filter controls
        tk.Label(row1, text="LPF:", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT, padx=(0, 4))
        self.filter_chk = tk.Checkbutton(
            row1, text="Enabled", variable=self.filter_enabled,
            bg=BG_CTRL, fg=ACCENT_GREEN, font=FONT_LABEL,
            selectcolor=BG_CTRL, activebackground=BG_CTRL,
            command=self._on_filter_toggle)
        self.filter_chk.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(row1, text="Cutoff:", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)
        self.cutoff_slider = tk.Scale(
            row1, from_=1, to=200, orient=tk.HORIZONTAL,
            resolution=0.5, variable=self.cutoff_var,
            bg=BG_CTRL, fg=FG_LABEL, troughcolor="#b0b0b0",
            highlightthickness=0, bd=1, length=160,
            font=("Arial", 7), command=self._on_cutoff_change,
            showvalue=False)
        self.cutoff_slider.pack(side=tk.LEFT, padx=(2, 2))

        vcmd = (self.root.register(self._validate_cutoff), "%P")
        self.cutoff_entry = tk.Entry(
            row1, textvariable=self.cutoff_var, width=6,
            bg="white", fg=ACCENT_BLUE, font=FONT_MONO,
            relief="sunken", bd=2, validate="key", validatecommand=vcmd)
        self.cutoff_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.cutoff_entry.bind("<Return>",   self._on_cutoff_commit)
        self.cutoff_entry.bind("<FocusOut>", self._on_cutoff_commit)
        tk.Label(row1, text="Hz", bg=BG_CTRL, fg=FG_LABEL, font=FONT_LABEL).pack(side=tk.LEFT)

        self.filter_status_lbl = tk.Label(
            row1, text=f"[{LPF_CUTOFF:.1f} Hz]",
            bg=BG_CTRL, fg=ACCENT_BLUE, font=("Arial", 8, "bold"))
        self.filter_status_lbl.pack(side=tk.LEFT, padx=(6, 0))

        # ── Plots area ────────────────────────────────────────────────────────
        plots_outer = tk.Frame(self.root, bg=BG_MAIN)
        plots_outer.grid(row=1, column=0, sticky="nsew", padx=6, pady=2)
        plots_outer.columnconfigure(0, weight=1)
        plots_outer.rowconfigure(0, weight=1)

        # ── Full-width VFR plot ───────────────────────────────────────────────
        vfr_frame = tk.LabelFrame(plots_outer, text="Volume Flow Rate",
                                  bg=BG_MAIN, fg=FG_LABEL,
                                  font=FONT_TITLE, relief="groove", bd=2)
        vfr_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        vfr_frame.columnconfigure(0, weight=1)
        vfr_frame.rowconfigure(0, weight=1)

        self.fig_vfr = Figure(facecolor=BG_MAIN)
        self.ax_vfr  = self.fig_vfr.add_subplot(111)
        self._style_ax(self.ax_vfr, ylabel="L/h")
        self.line_vfr, = self.ax_vfr.plot([], [], color=PLOT_COLORS["VFR"],
                                           linewidth=0.9, antialiased=True)
        self.fig_vfr.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.12)
        cv3 = FigureCanvasTkAgg(self.fig_vfr, master=vfr_frame)
        cv3.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.canvas_vfr = cv3

        # ── Bottom stats strip ────────────────────────────────────────────────
        stats_strip = tk.Frame(self.root, bg=BG_CTRL, relief="groove", bd=1)
        stats_strip.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 4))
        stats_strip.columnconfigure(0, weight=1)

        self.vfr_stat_var = tk.StringVar(value="Mean= --  Min= --  Max= --  σ= --")
        tk.Label(stats_strip, textvariable=self.vfr_stat_var,
                 bg=BG_CTRL, fg=FG_LABEL, font=FONT_STAT,
                 anchor="center").grid(row=0, column=0, sticky="ew", padx=8, pady=2)

        # ── Raw log (collapsible bottom strip) ───────────────────────────────
        log_frame = tk.Frame(self.root, bg=BG_MAIN)
        log_frame.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 6))
        tk.Label(log_frame, text="RAW LOG:", bg=BG_MAIN, fg=BORDER_CLR,
                 font=FONT_STAT).pack(side=tk.LEFT, padx=(0, 4))
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
                         cursor="hand2",
                         activebackground="#c0c0c0")

    def _style_ax(self, ax, ylabel=""):
        ax.set_facecolor(BG_PLOT)
        ax.tick_params(colors="#333333", labelsize=7)
        ax.set_xlabel("Time", fontsize=7, color="#555555")
        ax.set_ylabel(ylabel, fontsize=7, color="#555555")
        ax.grid(True, color="#dddddd", linewidth=0.5, linestyle="-")
        ax.spines[:].set_color(BORDER_CLR)
        ax.spines[:].set_linewidth(0.8)
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_fontsize(7)
            lbl.set_color("#333333")

    # ── Filter controls ───────────────────────────────────────────────────────
    def _on_filter_toggle(self):
        if self.filter_enabled.get():
            hz = self.cutoff_var.get()
            self.filter_status_lbl.configure(text=f"[{hz:.1f} Hz]", fg=ACCENT_BLUE)
            self.cutoff_slider.configure(state="normal")
            self.cutoff_entry.configure(state="normal")
            self._rebuild_filters()
        else:
            self.filter_status_lbl.configure(text="[OFF]", fg=ACCENT_RED)
            self.cutoff_slider.configure(state="disabled")
            self.cutoff_entry.configure(state="disabled")

    def _on_cutoff_change(self, _=None):
        hz = self.cutoff_var.get()
        self.filter_status_lbl.configure(text=f"[{hz:.1f} Hz]")
        self._rebuild_filters()

    def _on_cutoff_commit(self, _=None):
        try:
            hz = float(self.cutoff_entry.get())
            hz = max(1.0, min(hz, 200.0))
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
            messagebox.showerror("Error", "Please select a COM port.")
            return
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.running = True
            self.t0 = time.time()
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            self.status_var.set(f"● {port} @ {baud}")
            self._status_color(ACCENT_GREEN)
            self._log(f"[Connected] {port} @ {baud}\n")
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", str(e))

    def _disconnect(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None
        self.status_var.set("● Disconnected")
        self._status_color(ACCENT_RED)
        self._log("[Disconnected]\n")
        if self.csv_file:
            self._stop_save()

    def _status_color(self, color):
        for w in self.root.winfo_children():
            self._find_status_label(w, color)

    def _find_status_label(self, widget, color):
        try:
            if hasattr(self, 'status_var') and isinstance(widget, tk.Label):
                if widget.cget("textvariable") == str(self.status_var):
                    widget.configure(fg=color)
                    return
        except Exception:
            pass

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
                if not self.locked:
                    self.data[ch].append(val_out)
                    self.times[ch].append(t)
                self.plot_dirty = True
                if self.csv_writer:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    self.csv_writer.writerow([ts, ch, f"{val_out:e}"])
        self.root.after(self.POLL_MS, self._poll_queue)

    # ── Plot redraw ───────────────────────────────────────────────────────────
    def _schedule_plot(self):
        if self.plot_dirty:
            self._redraw()
            self.plot_dirty = False
        self.root.after(self.PLOT_MS, self._schedule_plot)

    def _redraw(self):
        xs_v = list(self.times["VFR"])
        ys_v = list(self.data["VFR"])
        if len(xs_v) >= 2:
            self.line_vfr.set_data(xs_v, ys_v)
            self._autoscale(self.ax_vfr, xs_v, ys_v)
            self._fmt_time_axis(self.ax_vfr, xs_v)
            self.vfr_stat_var.set(_stats_str(self.data["VFR"]))
            self.canvas_vfr.draw_idle()

    def _autoscale(self, ax, xs, ys):
        if not xs or not ys:
            return
        ax.set_xlim(xs[0], max(xs[-1], xs[0] + 1))
        mn, mx = min(ys), max(ys)
        mg = (mx - mn) * 0.15 if mx != mn else abs(mx) * 0.1 or 1.0
        ax.set_ylim(mn - mg, mx + mg)

    def _fmt_time_axis(self, ax, xs):
        """Show elapsed seconds as HH:MM:SS-style ticks."""
        if not xs:
            return
        ticks = ax.get_xticks()
        labels = []
        for t in ticks:
            if xs[0] <= t <= xs[-1]:
                m, s = divmod(int(t), 60)
                h, m = divmod(m, 60)
                labels.append(f"{h:02d}:{m:02d}:{s:02d}")
            else:
                labels.append("")
        ax.set_xticklabels(labels, fontsize=6, rotation=15)

    # ── Lock toggle ───────────────────────────────────────────────────────────
    def _toggle_lock(self):
        self.locked = not self.locked
        state = "LOCKED" if self.locked else "LIVE"
        self._log(f"[Graphs {state}]\n")

    # ── CSV ───────────────────────────────────────────────────────────────────
    def _toggle_save(self):
        if self.csv_file:
            self._stop_save()
        else:
            self._start_save()

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

    # ── Clear ─────────────────────────────────────────────────────────────────
    def _clear_data(self):
        for ch in CHANNELS:
            self.data[ch].clear()
            self.times[ch].clear()
        self._rebuild_filters()
        self.t0 = time.time()
        self.vfr_stat_var.set("Mean= --  Min= --  Max= --  σ= --")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self.canvas_vfr.draw_idle()

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