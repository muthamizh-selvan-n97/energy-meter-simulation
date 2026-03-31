# 3-Phase Class 0.5S Energy Meter Simulation

A production-grade simulation of a three-phase electrical energy meter,
modelling the complete signal chain from analog input through delta-sigma
ADC quantization to IEC 62053-22 Class 0.5S accuracy verification.

## Architecture Reference

| Component         | Device / Standard         |
|-------------------|---------------------------|
| ADC               | TI ADS131M08 (24-bit Δ-Σ) |
| Reference Design  | TIDA-010243 (Class 0.1)   |
| Metering Standard | IEC 62053-22 Class 0.5S   |
| Grid              | 3-phase 4-wire Wye, 50 Hz |
| Sampling Rate     | 8 kSPS (160 samples/cycle)|
| Integration       | 10 cycles = 200 ms        |

## Signal Chain Modelled

```
230V L-N Grid Signal
      │
      ▼
Resistor Divider (301:1) ──► scales to ±1.08V at ADC input
CT (1000:1) + Burden 10Ω ──► scales I to ±282mV at ADC input
      │
      ▼
Thermal Noise Addition (3.5 LSB rms)
      │
      ▼
24-bit Quantization  (LSB = 143.05 nV)
      │
      ▼
Reconstruction to Physical Units
      │
      ▼
Metrology Computation (per TIDA-010243 firmware)
```

## Modules

| Module | File | Description |
|--------|------|-------------|
| 0 | `m00_config.py` | System configuration — all parameters |
| 1 | `m01_signal_gen.py` | Signal generation + 24-bit quantization |
| 2 | `m02_rms.py` | Vrms, Irms — true RMS computation |
| 3 | `m03_power.py` | Active (kW), Reactive (kVAR), Apparent (kVA), PF |
| 4 | `m04_harmonics.py` | FFT, THD-V, THD-I, harmonic spectrum |
| 5 | `m05_energy.py` | kWh, kVARh, kVAh accumulation |
| 6 | `m06_accuracy.py` | IEC 62053-22 Class 0.5S error band verification |
| 7 | `m07_dashboard.py` | Full visualization dashboard |
| 8 | `m08_modbus.py` | Modbus register map output (IEC 62056 / DL-T 645) |

## Quick Start

### Google Colab
Open `notebook/energy_meter_sim.ipynb` directly in Colab — no setup needed.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/muthamizhselvan152/energy-meter-simulation/blob/main/notebook/energy_meter_sim.ipynb)

### Local
```bash
git clone https://github.com/muthamizhselvan152/energy-meter-simulation.git
cd energy-meter-simulation
pip install -r requirements.txt
jupyter notebook notebook/energy_meter_sim.ipynb
```

## Load Configuration (Default)

| Phase | Vrms (V) | Irms (A) | PF   | φ (°) |
|-------|----------|----------|------|-------|
| A (R) | 230      | 15.0     | 0.85 | 31.8° |
| B (Y) | 230      | 12.0     | 0.90 | 25.8° |
| C (B) | 230      | 18.0     | 0.80 | 36.9° |

Unbalanced load — typical industrial scenario.

## Harmonic Content (Default)

| Order | Freq (Hz) | V (%) | I (%) |
|-------|-----------|-------|-------|
| 3rd   | 150       | 2.0   | 5.0   |
| 5th   | 250       | 3.0   | 8.0   |
| 7th   | 350       | 1.5   | 4.0   |
| 11th  | 550       | 1.0   | 2.0   |
| 13th  | 650       | 0.5   | 1.5   |

## ADC Parameters

| Parameter        | Value                          |
|------------------|--------------------------------|
| Resolution       | 24-bit signed two's complement |
| Input range      | ±1.2 V                         |
| LSB size         | 143.05 nV                      |
| ADC counts range | −8,388,608 to +8,388,607       |
| Theoretical SNR  | 146.2 dB                       |
| Thermal noise    | ~3.5 LSB rms (~500 nV rms)     |

## References

- [ADS131M08 Datasheet](https://www.ti.com/product/ADS131M08) — TI 24-bit 8-ch Δ-Σ ADC
- [TIDA-010243 Design Guide](https://www.ti.com/tool/TIDA-010243) — Class 0.1 3-phase CT meter reference design
- [AN-1076](https://www.analog.com/en/resources/app-notes/an-1076.html) — Calibrating ADE7878-based 3-phase energy meter
- IEC 62053-22 — Electricity metering equipment — Class 0.5S accuracy requirements
- IEC 62056 — DLMS/COSEM data exchange standard

## Author

Muthamil Selvan N  
Principal Engineer — Motor Control & Embedded Systems  
[LinkedIn](https://www.linkedin.com/in/muthamizhselvan) | muthamizhselvan152@gmail.com

---

*Part of a broader series on power electronics simulation and motor control.*  
*See also: [Motor Control — Fundamentals to FOC](https://github.com/muthamizhselvan152/motor-control-book)*
