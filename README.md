# 🫁 Incentive Spirometer — MSP430FR6043 USS

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: MSP430](https://img.shields.io/badge/Platform-MSP430FR6043-red.svg)](https://www.ti.com/product/MSP430FR6043)
[![IDE: CCS](https://img.shields.io/badge/IDE-Code%20Composer%20Studio-orange.svg)](https://www.ti.com/tool/CCSTUDIO)
[![Python: 3.7+](https://img.shields.io/badge/Python-3.7%2B-3776AB.svg)](https://www.python.org/)

> An ultrasonic sensing (USS) based incentive spirometer built on the **TI MSP430FR6043** microcontroller, designed for post-surgical lung rehabilitation and respiratory health monitoring.

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [What is an Incentive Spirometer?](#what-is-an-incentive-spirometer)
- [System Architecture](#system-architecture)
- [Hardware](#hardware)
- [Technologies Used](#technologies-used)
- [Data Output Methods](#data-output-methods)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 📖 About the Project

This project implements a **digital incentive spirometer** using the **MSP430FR6043** microcontroller's built-in **Ultrasonic Sensing Solution (USS)** module. The USS module measures airflow through an ultrasonic transducer pair, enabling accurate, non-mechanical spirometry readings.

**Key Highlights:**

- 🔊 Ultrasonic time-of-flight (ToF) based flow measurement — no moving parts
- 🎯 Calibrated using the **TI USS Design Center GUI**
- 💻 Firmware developed in **Code Composer Studio (CCS)**
- 📡 Dual data output: **USS GUI** or **UART serial communication**
- 🖥️ Custom **Python GUI** for real-time 4-channel data visualization
- 🔧 Planned migration from the **EVM430-FR6043** evaluation module to a **custom PCB** with hardware optimizations

---

## 💡 What is an Incentive Spirometer?

An **incentive spirometer** is a handheld medical device used to exercise and expand the lungs. It is commonly prescribed:

- **After surgery** — to prevent pulmonary complications during recovery
- **After chest/lung injury** — to restore lung capacity
- **During illness** — to reduce the risk of pneumonia and atelectasis (lung collapse)

The device encourages patients to take slow, deep breaths, helping keep the alveoli (air sacs) open and improving oxygen exchange.

### Why Digitize It?

Traditional incentive spirometers are purely mechanical — a ball or piston rises in a chamber as the patient inhales. This project aims to **digitize** the incentive spirometer using ultrasonic flow sensing, enabling:

| Feature | Traditional | This Project |
|---|---|---|
| Measurement | Visual (ball height) | Precise digital values |
| Data Logging | ❌ None | ✅ CSV export & real-time graphs |
| Remote Monitoring | ❌ Not possible | ✅ UART / future wireless |
| Accuracy | Approximate | IEEE 754 float precision |
| Moving Parts | Yes (ball/piston) | None (ultrasonic) |

---

## 🏗️ System Architecture

```
                         ┌──────────────────────────┐
                         │   Ultrasonic Transducers  │
                         │   (Upstream & Downstream) │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────┐
                    │         MSP430FR6043              │
                    │    USS Module (ToF Measurement)   │
                    │    Signal Processing & Firmware   │
                    └──────┬──────────────────┬────────┘
                           │                  │
                  ┌────────▼───────┐  ┌───────▼──────────┐
                  │   USS GUI       │  │   UART Output     │
                  │  (TI Design     │  │  (Serial → PC)    │
                  │   Center)       │  │                    │
                  │                 │  │  ┌──────────────┐  │
                  │  • Calibration  │  │  │ uart_parse.py│  │
                  │  • Visualization│  │  │ (CLI batch)  │  │
                  │  • Debugging    │  │  ├──────────────┤  │
                  │                 │  │  │ uart_gui.py  │  │
                  │                 │  │  │ (Live GUI)   │  │
                  └─────────────────┘  │  └──────────────┘  │
                                       └────────────────────┘
```

---

## 🔧 Hardware

### Current Development Platform

| Component | Details |
|---|---|
| **MCU** | [TI MSP430FR6043](https://www.ti.com/product/MSP430FR6043) |
| **Dev Board** | [EVM430-FR6043](https://www.ti.com/tool/EVM430-FR6043) Evaluation Module |
| **Sensing** | Ultrasonic Sensing Solution (USS) — Time-of-Flight |
| **Transducers** | Upstream & downstream ultrasonic transducer pair |
| **IDE** | [Code Composer Studio (CCS)](https://www.ti.com/tool/CCSTUDIO) |
| **Calibration** | [TI USS Design Center GUI](https://www.ti.com/tool/USS-DESIGN-CENTER) |

### Planned Custom PCB

The next phase of this project involves designing a **custom PCB** to replace the EVM430-FR6043, with the following goals:

- 🔩 **Hardware optimization** — reduced board size, optimized power routing
- ⚡ **Low power design** — leveraging MSP430FR6043 ultra-low-power modes (LPM3/LPM4)
- 🧩 **Application-specific layout** — tailored for spirometer enclosure integration
- 📡 **Communication interfaces** — UART, potential wireless (BLE/Wi-Fi) add-on
- 🔋 **Battery operation** — portable, handheld device form factor

---

## 🛠️ Technologies Used

### Firmware / Embedded

| Technology | Purpose |
|---|---|
| MSP430FR6043 | Ultra-low-power MCU with USS module |
| USS Library | TI's ultrasonic sensing signal processing |
| Code Composer Studio | IDE for firmware development |
| USS Design Center | Transducer calibration & flow config |

### Software / Host PC

| Technology | Purpose |
|---|---|
| Python 3.7+ | Host-side data acquisition scripts |
| pyserial | Serial UART communication |
| matplotlib | Real-time 4-channel graph plotting |
| Tkinter | GUI framework for serial monitor |

---

## 📤 Data Output Methods

There are **two methods** to obtain spirometry readings from the MSP430FR6043:

### Method 1: USS Design Center GUI

| Aspect | Details |
|---|---|
| **Connection** | USB to EVM430-FR6043 |
| **Software** | TI USS Design Center GUI |
| **Best For** | Development, calibration, debugging |
| **Data Format** | Visual plots + internal data export |

### Method 2: UART Communication ⭐

| Aspect | Details |
|---|---|
| **Connection** | USB/Serial to MSP430FR6043 |
| **Software** | `uart_gui.py` (live) or `uart_parse.py` (batch) |
| **Best For** | Standalone operation, data logging, integration |
| **Data Format** | `<delimiter>,<hex IEEE754>` → decoded float |
| **Channels** | AbsTof-UPS (`$`), AbsTof-DNS (`#`), DToF (`%`), VFR (`!`) |

> 📖 **See the full UART documentation:** [`Spirometer/UART/README.md`](Spirometer/UART/README.md)

---

## 📁 Repository Structure

```
MSP430FR6043-USS/
│
├── 📄 README.md                            ← You are here
│
└── 📂 Spirometer/
    │
    ├── 📂 GUI/                             ← USS Design Center GUI files
    │   └── README.md                       ← GUI module documentation
    │
    └── 📂 UART/                            ← UART communication module
        ├── 📄 README.md                    ← Detailed UART documentation
        ├── 🐍 uart_parse.py                ← CLI batch hex → float parser
        ├── 🐍 uart_gui.py                  ← Real-time serial monitor GUI
        ├── 📊 hex_in.csv                   ← Sample raw UART data (hex)
        ├── 📊 hex_out.csv                  ← Sample decoded output (float)
        └── 📄 tempCodeRunnerFile.python    ← Dev temp file (VS Code)
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Link |
|---|---|
| Code Composer Studio (CCS) | [Download](https://www.ti.com/tool/CCSTUDIO) |
| TI USS Design Center GUI | [Download](https://www.ti.com/tool/USS-DESIGN-CENTER) |
| EVM430-FR6043 (or custom HW) | [Product Page](https://www.ti.com/tool/EVM430-FR6043) |
| Python 3.7+ | [Download](https://www.python.org/downloads/) |
| USB Cable | For programming & UART |

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sasanka-29/MSP430FR6043-USS.git
   cd MSP430FR6043-USS
   ```

2. **Install Python dependencies** (for UART tools)
   ```bash
   pip install pyserial matplotlib
   ```

3. **Firmware Setup**
   - Open Code Composer Studio
   - Import the project from the `Spirometer/` directory
   - Connect the EVM430-FR6043 via USB

4. **Calibrate using USS Design Center**
   - Open the USS Design Center GUI
   - Follow the calibration workflow for your transducer configuration

5. **Flash and Run**
   - Build and flash the firmware to the MSP430FR6043

6. **View Output**

   **Option A — USS GUI:**
   Use the TI Design Center for visualization

   **Option B — UART (Recommended for data logging):**
   ```bash
   # Real-time GUI monitor
   cd Spirometer/UART
   python uart_gui.py

   # Or batch parse captured data
   python uart_parse.py hex_in.csv hex_out.csv
   ```

---

## 🗺️ Roadmap

- [x] Initial firmware development on EVM430-FR6043
- [x] USS Design Center GUI calibration
- [x] UART data output implementation
- [x] Python CLI parser (`uart_parse.py`)
- [x] Real-time serial monitor GUI (`uart_gui.py`)
- [ ] Custom PCB schematic design
- [ ] Custom PCB layout and fabrication
- [ ] Hardware optimization and power profiling
- [ ] Enclosure design for handheld spirometer
- [ ] Patient-facing display/indicator integration
- [ ] Wireless data transmission (BLE/Wi-Fi)
- [ ] Mobile app integration

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve this project:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m 'Add your feature'`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

### Ideas for Contribution

- 📐 Custom PCB design files (KiCad/Altium)
- 📱 Mobile app for Bluetooth data reception
- 📊 Advanced spirometry analytics (FEV1, FVC calculation)
- 🧪 Unit tests for the Python parsing scripts
- 📝 Additional documentation or translations

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

---

## 📚 References

- [MSP430FR6043 Product Page](https://www.ti.com/product/MSP430FR6043) — TI microcontroller datasheet & resources
- [USS Design Center User Guide](https://www.ti.com/tool/USS-DESIGN-CENTER) — Calibration and configuration tool
- [EVM430-FR6043 User Guide](https://www.ti.com/tool/EVM430-FR6043) — Evaluation module documentation
- [MSP430 USS Application Report (SLAA720)](https://www.ti.com/lit/an/slaa720c/slaa720c.pdf) — Ultrasonic sensing implementation guide

---

<p align="center">
  <b>Designed & Developed by <a href="https://github.com/Sasanka-29">Sasanka-29</a></b><br>
  <i>MSP430FR6043 Ultrasonic Sensing Solution — Incentive Spirometer</i><br><br>
  ⭐ Star this repo if you find it useful!
</p>
