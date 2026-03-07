#!/usr/bin/python
"""
Serial Monitor GUI - Reads UART data, parses it via uart_parse logic,
and displays live graphs for AbsTof-UPS, AbsTof-DNS, DToF, and VFR.
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

import serial
import serial.tools.list_ports
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.signal import butter, lfilter_zi, lfilter

# ── Parse logic ───────────────────────────────────────────────────────────────
DELIM_DICT = {"$": "AbsTof-UPS", "#": "AbsTof-DNS", "%": "DToF", "!": "VFR"}
CHANNELS   = ["AbsTof-UPS", "AbsTof-DNS", "DToF", "VFR"]
COLORS     = {"AbsTof-UPS": "#00e5ff", "AbsTof-DNS": "#ff4081",
              "DToF":       "#69ff47", "VFR":        "#ffd740"}
MAX_POINTS   = 300
LPF_CUTOFF   = 3.0   # Hz - low-pass filter cutoff
LPF_ORDER    = 2     # 2nd-order Butterworth (low lag)
SAMPLE_RATE  = 500.0 # Hz - fixed sample rate

def _make_butter(cutoff_hz, fs, order=2):
    """Return (b, a) Butterworth low-pass coefficients."""
    nyq = fs / 2.0
    cutoff_hz = min(cutoff_hz, nyq * 0.95)  # never exceed Nyquist
    b, a = butter(order, cutoff_hz / nyq, btype="low", analog=False)
    return b, a


def parse_line(raw_line: str):
    """
    Parse one raw serial line.
    Handles both \\n and \\r\\n endings.
    Returns (channel_name, float_value) or None on failure.
    """
    line = raw_line.strip()           # strips \r, \n, spaces
    line = re.sub(r"\s+", "", line)   # remove any embedded whitespace
    parts = line.split(",")
    if len(parts) < 2:
        return None
    key   = parts[0]
    hex_s = parts[1]
    if key not in DELIM_DICT:
        return None
    # Validate hex string before conversion
    if not re.fullmatch(r"[0-9A-Fa-f]{1,8}", hex_s):
        return None
    try:
        int_val = int(hex_s, 16)
        value   = struct.unpack(">f", struct.pack(">I", int_val))[0]
        return DELIM_DICT[key], value
    except (ValueError, struct.error):
        return None


# ── Main Application ──────────────────────────────────────────────────────────
class SerialMonitorApp:
    POLL_MS = 50    # drain queue every 50 ms (20x/sec)
    PLOT_MS = 100   # redraw plot every 100 ms (10 fps)

    def __init__(self, root):
        self.root = root
        self.root.title("Serial UART Monitor")
        self.root.configure(bg="#0d1117")
        self.root.geometry("1200x780")
        self.root.minsize(900, 600)

        # Thread-safe queue: serial thread -> UI thread
        self.rx_queue = queue.Queue()

        # Data buffers (only written from UI thread after draining queue)
        self.data  = {ch: deque(maxlen=MAX_POINTS) for ch in CHANNELS}
        self.times = {ch: deque(maxlen=MAX_POINTS) for ch in CHANNELS}
        self.t0    = time.time()

        # Only redraw plot when new data arrived
        self.plot_dirty = False

        # Per-channel IIR filter state — fixed at 500 Hz sample rate
        b0, a0 = _make_butter(LPF_CUTOFF, SAMPLE_RATE, LPF_ORDER)
        zi0 = lfilter_zi(b0, a0)
        self.filter_b  = {ch: b0.copy() for ch in CHANNELS}
        self.filter_a  = {ch: a0.copy() for ch in CHANNELS}
        self.filter_zi = {ch: zi0.copy() for ch in CHANNELS}

        # Serial state
        self.ser         = None
        self.running     = False
        self.read_thread = None

        # CSV state
        self.csv_file   = None
        self.csv_writer = None
        self.csv_path   = None

        self._build_ui()
        self._refresh_ports()
        self._poll_queue()
        self._schedule_plot()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame",          background="#0d1117")
        style.configure("TLabel",          background="#0d1117", foreground="#c9d1d9",
                        font=("Consolas", 10))
        style.configure("Header.TLabel",   background="#0d1117", foreground="#58a6ff",
                        font=("Consolas", 11, "bold"))
        style.configure("TCombobox",       fieldbackground="#161b22", background="#161b22",
                        foreground="#c9d1d9", selectbackground="#1f6feb")
        style.configure("TButton",         background="#21262d", foreground="#c9d1d9",
                        font=("Consolas", 10), relief="flat", padding=6)
        style.map("TButton",
                  background=[("active", "#30363d"), ("pressed", "#1f6feb")])
        style.configure("Connect.TButton", foreground="#3fb950",
                        font=("Consolas", 10, "bold"))
        style.configure("Danger.TButton",  foreground="#f85149",
                        font=("Consolas", 10, "bold"))

        # Toolbar
        toolbar = ttk.Frame(self.root, style="TFrame")
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(10, 4))

        ttk.Label(toolbar, text="SERIAL UART MONITOR",
                  style="Header.TLabel").pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(toolbar, text="PORT").pack(side=tk.LEFT, padx=(8, 2))
        self.port_var = tk.StringVar()
        self.port_cb  = ttk.Combobox(toolbar, textvariable=self.port_var,
                                     width=10, state="readonly")
        self.port_cb.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(toolbar, text="BAUD").pack(side=tk.LEFT, padx=(0, 2))
        self.baud_var = tk.StringVar(value="115200")
        ttk.Combobox(toolbar, textvariable=self.baud_var,
                     values=["9600","19200","38400","57600",
                             "115200","230400","460800","921600"],
                     width=9, state="readonly").pack(side=tk.LEFT, padx=(0, 12))

        ttk.Button(toolbar, text="Refresh",
                   command=self._refresh_ports).pack(side=tk.LEFT, padx=(0, 4))

        self.connect_btn = ttk.Button(toolbar, text="Connect",
                                      style="Connect.TButton",
                                      command=self._toggle_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 12))

        self.save_btn = ttk.Button(toolbar, text="Save CSV",
                                   command=self._toggle_save)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(toolbar, text="Clear", style="Danger.TButton",
                   command=self._clear_data).pack(side=tk.LEFT, padx=(0, 4))

        self.status_var = tk.StringVar(value="Disconnected")
        self.status_lbl = ttk.Label(toolbar, textvariable=self.status_var,
                                    foreground="#f85149",
                                    font=("Consolas", 10, "bold"))
        self.status_lbl.pack(side=tk.RIGHT, padx=8)

        # Stats bar
        stats_frame = ttk.Frame(self.root, style="TFrame")
        stats_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0, 4))

        self.stat_vars = {}
        for ch in CHANNELS:
            f = tk.Frame(stats_frame, bg="#161b22", bd=0, padx=10, pady=4)
            f.pack(side=tk.LEFT, padx=4)
            tk.Label(f, text=ch, bg="#161b22", fg=COLORS[ch],
                     font=("Consolas", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))
            sv = tk.StringVar(value="--")
            self.stat_vars[ch] = sv
            tk.Label(f, textvariable=sv, bg="#161b22", fg="#e6edf3",
                     font=("Consolas", 9)).pack(side=tk.LEFT)

        # Plot area
        plot_frame = tk.Frame(self.root, bg="#0d1117")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        self.fig = Figure(figsize=(12, 5.5), facecolor="#0d1117")
        self.fig.subplots_adjust(hspace=0.45, wspace=0.32,
                                 left=0.07, right=0.97, top=0.93, bottom=0.1)

        self.axes  = {}
        self.lines = {}
        for i, ch in enumerate(CHANNELS):
            ax = self.fig.add_subplot(2, 2, i + 1)
            ax.set_facecolor("#161b22")
            ax.set_title(ch, color=COLORS[ch], fontsize=10,
                         fontfamily="Consolas", pad=4)
            ax.tick_params(colors="#8b949e", labelsize=8)
            for spine in ax.spines.values():
                spine.set_edgecolor("#30363d")
            ax.xaxis.label.set_color("#8b949e")
            ax.yaxis.label.set_color("#8b949e")
            ax.set_xlabel("Time (s)", fontsize=8, fontfamily="Consolas")
            line, = ax.plot([], [], color=COLORS[ch], linewidth=1.4,
                            solid_capstyle="round")
            self.axes[ch]  = ax
            self.lines[ch] = line

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Raw log
        log_frame = tk.Frame(self.root, bg="#0d1117")
        log_frame.pack(fill=tk.X, padx=12, pady=(0, 8))

        tk.Label(log_frame, text="RAW LOG", bg="#0d1117", fg="#8b949e",
                 font=("Consolas", 8, "bold")).pack(anchor="w")

        log_inner = tk.Frame(log_frame, bg="#0d1117")
        log_inner.pack(fill=tk.X)

        self.log_text = tk.Text(log_inner, height=5, bg="#161b22",
                                fg="#8b949e", font=("Consolas", 8),
                                relief="flat", insertbackground="#c9d1d9",
                                state="disabled")
        self.log_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        sb = ttk.Scrollbar(log_inner, command=self.log_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text["yscrollcommand"] = sb.set

    # ── Serial ────────────────────────────────────────────────────────────────
    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_cb["values"] = ports
        if ports:
            self.port_var.set(ports[0])

    def _toggle_connect(self):
        if self.running:
            self._disconnect()
        else:
            self._connect()

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
            self.connect_btn.configure(text="Disconnect", style="Danger.TButton")
            self.status_var.set(f"Connected: {port} @ {baud}")
            self.status_lbl.configure(foreground="#3fb950")
            self._log(f"[Connected] {port} @ {baud} baud\n")
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", str(e))

    def _disconnect(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None
        self.connect_btn.configure(text="Connect", style="Connect.TButton")
        self.status_var.set("Disconnected")
        self.status_lbl.configure(foreground="#f85149")
        self._log("[Disconnected]\n")
        if self.csv_file:
            self._stop_save()

    def _read_loop(self):
        """Background thread: read lines and push to queue."""
        while self.running:
            try:
                raw = self.ser.readline().decode("utf-8", errors="replace")
                if raw.strip():
                    self.rx_queue.put_nowait(raw)
            except Exception:
                if self.running:
                    time.sleep(0.02)

    # ── Queue drain (UI thread) ───────────────────────────────────────────────
    def _poll_queue(self):
        """Drain up to 50 items per tick to avoid UI freeze at high baud."""
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

                # ── Apply IIR low-pass filter @ 3 Hz / 500 Hz ─────────────
                filtered, self.filter_zi[ch] = lfilter(
                    self.filter_b[ch], self.filter_a[ch],
                    [val], zi=self.filter_zi[ch]
                )
                val_filtered = float(filtered[0])

                self.data[ch].append(val_filtered)
                self.times[ch].append(t)
                self.stat_vars[ch].set(f"{val_filtered:.4e}")
                self.plot_dirty = True
                if self.csv_writer:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    self.csv_writer.writerow([ts, ch, f"{val_filtered:e}"])

        self.root.after(self.POLL_MS, self._poll_queue)

    # ── Plot redraw ───────────────────────────────────────────────────────────
    def _schedule_plot(self):
        if self.plot_dirty:
            self._redraw_plots()
            self.plot_dirty = False
        self.root.after(self.PLOT_MS, self._schedule_plot)

    def _redraw_plots(self):
        for ch in CHANNELS:
            xs = list(self.times[ch])
            ys = list(self.data[ch])
            if len(xs) < 2:
                continue
            self.lines[ch].set_data(xs, ys)
            ax = self.axes[ch]
            ax.set_xlim(xs[0], max(xs[-1], xs[0] + 1))
            if ch == "VFR":
                ax.set_ylim(0, 999)
            else:
                mn, mx = min(ys), max(ys)
                margin = (mx - mn) * 0.15 if mx != mn else abs(mx) * 0.1 or 1e-6
                ax.set_ylim(mn - margin, mx + margin)
        self.canvas.draw_idle()

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
            title="Save output CSV"
        )
        if not path:
            return
        self.csv_path   = path
        self.csv_file   = open(path, "w", newline="")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Timestamp", "Channel", "Value"])
        self.save_btn.configure(text="Stop Saving")
        self._log(f"[Saving to] {path}\n")

    def _stop_save(self):
        if self.csv_file:
            self.csv_file.close()
        self.csv_file   = None
        self.csv_writer = None
        self.save_btn.configure(text="Save CSV")
        self._log(f"[Saved] {self.csv_path}\n")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _clear_data(self):
        for ch in CHANNELS:
            self.data[ch].clear()
            self.times[ch].clear()
            self.stat_vars[ch].set("--")
            # Reset filter state so history doesn't bleed into new data
            b, a = _make_butter(LPF_CUTOFF, SAMPLE_RATE, LPF_ORDER)
            self.filter_b[ch]  = b
            self.filter_a[ch]  = a
            self.filter_zi[ch] = lfilter_zi(b, a)
        self.t0 = time.time()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self._redraw_plots()

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