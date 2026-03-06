# 🫁 Incentive Spirometer — MSP430FR6043 USS

> An ultrasonic sensing (USS) based incentive spirometer built on the **TI MSP430FR6043** microcontroller, designed for post-surgical lung rehabilitation and respiratory health monitoring.

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [What is an Incentive Spirometer?](#what-is-an-incentive-spirometer)
- [System Architecture](#system-architecture)
- [Hardware](#hardware)
- [Data Output Methods](#data-output-methods)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Roadmap](#roadmap)
- [License](#license)

---

## 📖 About the Project

This project implements a **digital incentive spirometer** using the **MSP430FR6043** microcontroller's built-in **Ultrasonic Sensing Solution (USS)** module. The USS module measures airflow through an ultrasonic transducer pair, enabling accurate, non-mechanical spirometry readings.

**Key Highlights:**

- Ultrasonic time-of-flight (ToF) based flow measurement — no moving parts
- Calibrated using the **TI USS Design Center GUI**
- Firmware developed in **Code Composer Studio (CCS)**
- Dual data output: **USS GUI** or **UART serial communication**
- Planned migration from the **EVM430-FR6043** evaluation module to a **custom PCB** with hardware optimizations

---

## 💡 What is an Incentive Spirometer?

An **incentive spirometer** is a handheld medical device used to exercise and expand the lungs. It is commonly prescribed:

- **After surgery** — to prevent pulmonary complications during recovery
- **After chest/lung injury** — to restore lung capacity
- **During illness** — to reduce the risk of pneumonia and atelectasis (lung collapse)

The device encourages patients to take slow, deep breaths, helping keep the alveoli (air sacs) open and improving oxygen exchange.

This project aims to **digitize** the incentive spirometer using ultrasonic flow sensing, enabling:

- Precise digital volume and flow rate measurements
- Data logging and real-time monitoring
- Potential for remote patient monitoring and IoT integration

---

## 🏗️ System Architecture

```
                    ┌─────────────────────────┐
                    │   Ultrasonic Transducer  │
                    │      (Upstream &         │
                    │       Downstream)        │
                    └────────┬────────────────┘
                             │
                             ▼
                    ┌─────────────────────────┐
                    │     MSP430FR6043         │
                    │   USS Module (ToF)       │
                    │   Signal Processing      │
                    └────┬──────────┬─────────┘
                         │          │
                ┌────────▼──┐  ┌───▼──────────┐
                │  USS GUI   │  │  UART Output │
                │ (TI Design │  │  (Serial     │
                │  Center)   │  │   Terminal)  │
                └────────────┘  └──────────────┘
```

---

## 🔧 Hardware

### Current Development Platform

| Component | Details |
|---|---|
| **MCU** | TI MSP430FR6043 |
| **Dev Board** | EVM430-FR6043 Evaluation Module |
| **Sensing** | Ultrasonic Sensing Solution (USS) — Time-of-Flight |
| **Transducers** | Upstream & downstream ultrasonic transducer pair |
| **IDE** | Code Composer Studio (CCS) |
| **Calibration** | TI USS Design Center GUI |

### Planned Custom PCB

The next phase of this project involves designing a **custom PCB** to replace the EVM430-FR6043, with the following goals:

- 🔩 **Hardware optimization** — reduced board size, optimized power routing
- ⚡ **Low power design** — leveraging MSP430FR6043 ultra-low-power modes
- 🧩 **Application-specific layout** — tailored for spirometer enclosure integration
- 📡 **Communication interfaces** — UART, potential wireless (BLE/Wi-Fi) add-on

---

## 📤 Data Output Methods

There are **two methods** to obtain spirometry readings from the MSP430FR6043:

### 1. USS Design Center GUI

- Connect the EVM430-FR6043 to a PC
- Use the **TI USS Design Center GUI** to visualize and calibrate flow measurements
- Ideal for **development, calibration, and debugging**

### 2. UART Communication

- The MSP430FR6043 transmits processed flow data over **UART**
- Connect to any serial terminal (e.g., PuTTY, Tera Term, or a custom application)
- Ideal for **standalone operation, data logging, and integration** with external systems

---

## 📁 Repository Structure

```
MSP430FR6043-USS/
├── README.md                  # Project documentation
└── Spirometer/
    ├── README.md              # Spirometer module details
    ├── GUI/                   # USS Design Center GUI related files
    │   └── README.md
    └── UART/                  # UART communication implementation
```

---

## 🚀 Getting Started

### Prerequisites

- [Code Composer Studio (CCS)](https://www.ti.com/tool/CCSTUDIO) — TI's IDE for MSP430 development
- [TI USS Design Center GUI](https://www.ti.com/tool/USS-DESIGN-CENTER) — for transducer calibration and flow visualization
- **EVM430-FR6043** evaluation module (or compatible custom hardware)
- USB cable for programming and UART communication

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sasanka-29/MSP430FR6043-USS.git
   cd MSP430FR6043-USS
   ```

2. **Open in Code Composer Studio**
   - Import the project from the `Spirometer/` directory

3. **Calibrate using USS Design Center**
   - Connect the EVM430-FR6043 to your PC
   - Open the USS Design Center GUI
   - Follow the calibration workflow for your transducer configuration

4. **Flash and Run**
   - Build and flash the firmware to the MSP430FR6043
   - View output via the USS GUI or a UART serial terminal

---

## 🗺️ Roadmap

- [x] Initial firmware development on EVM430-FR6043
- [x] USS Design Center GUI calibration
- [x] UART data output implementation
- [ ] Custom PCB schematic design
- [ ] Custom PCB layout and fabrication
- [ ] Hardware optimization and power profiling
- [ ] Enclosure design for handheld spirometer
- [ ] Patient-facing display/indicator integration
- [ ] Wireless data transmission (BLE/Wi-Fi)

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  <b>Designed & Developed by <a href="https://github.com/Sasanka-29">Sasanka-29</a></b><br>
  <i>MSP430FR6043 Ultrasonic Sensing Solution — Incentive Spirometer</i>
</p>
