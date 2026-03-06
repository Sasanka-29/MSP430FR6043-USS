
#!/usr/bin/python
"""
Serial Monitor GUI - Reads UART data, parses it via uart_parse logic,
and displays live graphs for AbsTof-UPS, AbsTof-DNS, DToF, and VFR.
"""

import re
import struct
import struct
import threading
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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

# ── Parse logic (inline from uart_parse.py) ──────────────────────────────────
DELIM_DICT = {"$": "AbsTof-UPS", "#": "AbsTof-DNS", "%": "DToF", "!": "VFR"}
CHANNELS   = ["AbsTof-UPS", "AbsTof-DNS", "DToF", "VFR"]
COLORS     = {"AbsTof-UPS": "#00e5ff", "AbsTof-DNS": "#ff4081",
              "DToF":       "#69ff47", "VFR":        "#ffd740"}

def parse_line(raw_line: str):
    """Parse one raw serial line. Returns (channel_name, float_value) or None."""
    line = raw_line.strip()
    line = re.sub(r"\s+", " ", line)
    parts = line.split(",")
    if len(parts) < 2:
        return None
    key = parts[0].strip()
    if key not in DELIM_DICT:
        return None
    try:
        value = struct.unpack("f", struct.pack("I", int(parts[1].strip(), 16)))[0]
        return DELIM_DICT[key], value
    except (ValueError, struct.error):
        return None


# ── Main Application ──────────────────────────────────────────────────────────
MAX_POINTS = 200   # rolling window

class SerialMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial UART Monitor")
        self.root.configure(bg="#0d1117")
        self.root.geometry("1200x780")
        self.root.minsize(900, 600)

        # Data buffers
        self.data   = {ch: deque(maxlen=MAX_POINTS) for ch in CHANNELS}
        self.times  = {ch: deque(maxlen=MAX_POINTS) for ch in CHANNELS}
        self.t0     = time.time()

        # Serial state
        self.ser          = None
        self.running      = False
        self.read_thread  = None
        self.csv_file     = None
        self.csv_writer   = None
        self.csv_path     = None

        self._build_ui()
        self._refresh_ports()
        self._start_animation()

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame",       background="#0d1117")
        style.configure("TLabel",       background="#0d1117", foreground="#c9d1d9",
                        font=("Consolas", 10))
        style.configure("Header.TLabel",background="#0d1117", foreground="#58a6ff",
                        font=("Consolas", 11, "bold"))
        style.configure("TCombobox",    fieldbackground="#161b22", background="#161b22",
                        foreground="#c9d1d9", selectbackground="#1f6feb")
        style.configure("TButton",      background="#21262d", foreground="#c9d1d9",
                        font=("Consolas", 10), relief="flat", padding=6)
        style.map("TButton",
                  background=[("active","#30363d"), ("pressed","#1f6feb")])
        style.configure("Connect.TButton", foreground="#3fb950",
                        font=("Consolas", 10, "bold"))
        style.configure("Danger.TButton",  foreground="#f85149",
                        font=("Consolas", 10, "bold"))

        # ── Top toolbar ──
        toolbar = ttk.Frame(self.root, style="TFrame")
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(10, 4))

        ttk.Label(toolbar, text="⬡ SERIAL UART MONITOR",
                  style="Header.TLabel").pack(side=tk.LEFT, padx=(0,20))

        # COM port
        ttk.Label(toolbar, text="PORT").pack(side=tk.LEFT, padx=(8,2))
        self.port_var = tk.StringVar()
        self.port_cb  = ttk.Combobox(toolbar, textvariable=self.port_var,
                                     width=10, state="readonly")
        self.port_cb.pack(side=tk.LEFT, padx=(0,8))

        # Baud rate
        ttk.Label(toolbar, text="BAUD").pack(side=tk.LEFT, padx=(0,2))
        self.baud_var = tk.StringVar(value="115200")
        baud_cb = ttk.Combobox(toolbar, textvariable=self.baud_var,
                               values=["9600","19200","38400","57600",
                                       "115200","230400","460800","921600"],
                               width=9, state="readonly")
        baud_cb.pack(side=tk.LEFT, padx=(0,12))

        # Refresh ports
        ttk.Button(toolbar, text="↺ Refresh",
                   command=self._refresh_ports).pack(side=tk.LEFT, padx=(0,4))

        # Connect / Disconnect
        self.connect_btn = ttk.Button(toolbar, text="▶  Connect",
                                      style="Connect.TButton",
                                      command=self._toggle_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=(0,12))

        # Save CSV
        self.save_btn = ttk.Button(toolbar, text="💾 Save CSV",
                                   command=self._toggle_save)
        self.save_btn.pack(side=tk.LEFT, padx=(0,4))

        # Clear
        ttk.Button(toolbar, text="✕ Clear", style="Danger.TButton",
                   command=self._clear_data).pack(side=tk.LEFT, padx=(0,4))

        # Status indicator (right-aligned)
        self.status_var = tk.StringVar(value="● Disconnected")
        self.status_lbl = ttk.Label(toolbar, textvariable=self.status_var,
                                    foreground="#f85149",
                                    font=("Consolas", 10, "bold"))
        self.status_lbl.pack(side=tk.RIGHT, padx=8)

        # ── Stats bar ──
        stats_frame = ttk.Frame(self.root, style="TFrame")
        stats_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0,4))

        self.stat_vars = {}
        for ch in CHANNELS:
            col = COLORS[ch]
            f = tk.Frame(stats_frame, bg="#161b22", bd=0, padx=10, pady=4)
            f.pack(side=tk.LEFT, padx=4)
            tk.Label(f, text=ch, bg="#161b22", fg=col,
                     font=("Consolas", 9, "bold")).pack(side=tk.LEFT, padx=(0,8))
            sv = tk.StringVar(value="—")
            self.stat_vars[ch] = sv
            tk.Label(f, textvariable=sv, bg="#161b22", fg="#e6edf3",
                     font=("Consolas", 9)).pack(side=tk.LEFT)

        # ── Plot area ──
        plot_frame = tk.Frame(self.root, bg="#0d1117")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,8))

        self.fig = Figure(figsize=(12, 5.5), facecolor="#0d1117")
        self.fig.subplots_adjust(hspace=0.45, wspace=0.3,
                                 left=0.07, right=0.97, top=0.93, bottom=0.1)

        self.axes = {}
        self.lines = {}
        for i, ch in enumerate(CHANNELS):
            ax = self.fig.add_subplot(2, 2, i+1)
            ax.set_facecolor("#161b22")
            ax.set_title(ch, color=COLORS[ch],
                         fontsize=10, fontfamily="Consolas", pad=4)
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

        # ── Raw log ──
        log_frame = tk.Frame(self.root, bg="#0d1117")
        log_frame.pack(fill=tk.X, padx=12, pady=(0,8))

        tk.Label(log_frame, text="RAW LOG", bg="#0d1117", fg="#8b949e",
                 font=("Consolas", 8, "bold")).pack(anchor="w")
        self.log_text = tk.Text(log_frame, height=5, bg="#161b22",
                                fg="#8b949e", font=("Consolas", 8),
                                relief="flat", insertbackground="#c9d1d9",
                                state="disabled")
        self.log_text.pack(fill=tk.X)
        sb = ttk.Scrollbar(log_frame, command=self.log_text.yview)
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
            self.connect_btn.configure(text="■  Disconnect", style="Danger.TButton")
            self.status_var.set(f"● {port} @ {baud}")
            self.status_lbl.configure(foreground="#3fb950")
            self._log(f"[Connected] {port} @ {baud} baud\n")
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", str(e))

    def _disconnect(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None
        self.connect_btn.configure(text="▶  Connect", style="Connect.TButton")
        self.status_var.set("● Disconnected")
        self.status_lbl.configure(foreground="#f85149")
        self._log("[Disconnected]\n")
        if self.csv_file:
            self._stop_save()

    def _read_loop(self):
        while self.running:
            try:
                raw = self.ser.readline().decode("utf-8", errors="replace")
                if not raw.strip():
                    continue
                self._log(raw)
                result = parse_line(raw)
                if result:
                    ch, val = result
                    t = time.time() - self.t0
                    self.data[ch].append(val)
                    self.times[ch].append(t)
                    # Update stat label
                    self.stat_vars[ch].set(f"{val:.4e}")
                    # Write CSV
                    if self.csv_writer:
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        self.csv_writer.writerow([ts, ch, f"{val:e}"])
            except Exception:
                if self.running:
                    time.sleep(0.05)

    # ── Animation ─────────────────────────────────────────────────────────────
    def _start_animation(self):
        self.anim = FuncAnimation(self.fig, self._update_plots,
                                  interval=150, blit=False)

    def _update_plots(self, frame):
        for ch in CHANNELS:
            xs = list(self.times[ch])
            ys = list(self.data[ch])
            ax = self.axes[ch]
            ln = self.lines[ch]
            if len(xs) >= 2:
                ln.set_data(xs, ys)
                ax.set_xlim(xs[0], max(xs[-1], xs[0]+1))
                margin = (max(ys)-min(ys))*0.15 if max(ys) != min(ys) else 1e-6
                ax.set_ylim(min(ys)-margin, max(ys)+margin)
        self.canvas.draw_idle()

    # ── CSV Save ──────────────────────────────────────────────────────────────
    def _toggle_save(self):
        if self.csv_file:
            self._stop_save()
        else:
            self._start_save()

    def _start_save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv"),("All files","*.*")],
            title="Save output CSV"
        )
        if not path:
            return
        self.csv_path   = path
        self.csv_file   = open(path, "w", newline="")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Timestamp", "Channel", "Value"])
        self.save_btn.configure(text="⏹ Stop Saving")
        self._log(f"[Saving to] {path}\n")

    def _stop_save(self):
        if self.csv_file:
            self.csv_file.close()
        self.csv_file   = None
        self.csv_writer = None
        self.save_btn.configure(text="💾 Save CSV")
        self._log(f"[Saved] {self.csv_path}\n")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _clear_data(self):
        for ch in CHANNELS:
            self.data[ch].clear()
            self.times[ch].clear()
            self.stat_vars[ch].set("—")
        self.t0 = time.time()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

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