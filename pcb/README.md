# Blueberry Voice Assistant — Custom Pi Shield (PCB)

> A single-layer, hand-etched Raspberry Pi shield that integrates all peripheral components of the Blueberry Voice Assistant into one clean board — eliminating loose wiring and breadboard clutter.

**Designed by [Nikhil Misal](https://github.com/Nikhil-Misal-24)**  
ECE Undergraduate — Sagar Institute of Science and Technology (SISTec), Bhopal  
IoT Centre of Excellence, SISTec

---

## Overview

This board is a custom Raspberry Pi HAT-style shield designed specifically for the Blueberry Voice Assistant project. It sits directly on top of the Raspberry Pi 3B+ via a 40-pin female header that mates with the Pi's GPIO male header — making the entire assembly compact and self-contained.

Rather than using a breadboard or loose jumper wires, all peripheral connections — LEDs, OLED display, microphone, and ESP32 — are routed cleanly through this board, with dedicated headers and resistors in place.

---

## Specifications

| Property | Detail |
|---|---|
| **Design Tool** | KiCad |
| **Layer Count** | Single layer (one-sided) |
| **Fabrication Method** | Hand-etched copper PCB |
| **Form Factor** | Raspberry Pi HAT-style shield |
| **GPIO Interface** | 40-pin female header (mates directly with Pi 3B+ GPIO) |
| **Operating Voltage** | 3.3V (GPIO) for LEDs, Mic, ESP32 — 5V (GPIO) for OLED |

---

## What the Board Integrates

| Component | Interface | Voltage |
|---|---|---|
| RGB LED (Red, Green, Blue) | GPIO 8, 23, 24 | 3.3V |
| White Status LED | GPIO 25 | 3.3V |
| SSD1306 OLED (header) | I2C — SDA/SCL | 5V |
| INMP441 Microphone (header) | I2S | 3.3V |
| ESP32 (header) | UART — TX/RX | 3.3V |

All connections are broken out from the 40-pin GPIO interface — no external power supply is needed beyond what the Raspberry Pi provides.

---

## Files

```
pcb/
├── gerber/
│   ├── blueberry-shield.gbr       # Copper layer
│   ├── blueberry-shield.drl       # Drill file
│   └── blueberry-shield.zip       # Full Gerber package (ready for fabrication)
└── README.md                      # This file
```

> The `.zip` file can be uploaded directly to fabrication services like [JLCPCB](https://jlcpcb.com) or [PCBWay](https://pcbway.com) for professional manufacturing.

---

## Fabrication Notes

This board was hand-etched for prototyping. If you want to manufacture it professionally:

1. Upload `gerber/blueberry-shield.zip` to [JLCPCB](https://jlcpcb.com) or [PCBWay](https://pcbway.com)
2. Select **single layer**, standard 1.6mm FR4
3. Minimum order is typically 5 boards at very low cost

---

## Design Notes

- The board is designed as a **single-layer shield** to keep hand-etching feasible while maintaining a clean layout
- Trace routing follows a spiral-like pattern on the copper layer to efficiently connect all GPIO pins to their respective peripheral headers without crossovers
- Current-limiting resistors for the RGB and white LEDs are placed on-board
- The 40-pin female header footprint matches the standard Raspberry Pi HAT specification, so the board seats flush on top of the Pi 3B+

---

## Opening in KiCad

1. Install [KiCad](https://www.kicad.org/) (free and open source)
2. Open the `.kicad_pcb` file from the `pcb/` directory
3. Use **File → Plot** to re-export Gerbers if needed

---

*Part of the [Blueberry Voice Assistant](https://github.com/vviszard/blueberry-voice-assistant) project — IoT Centre of Excellence, SISTec, Bhopal.*
