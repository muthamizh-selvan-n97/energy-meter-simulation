# =============================================================
# m00_config.py — System Configuration
# 3-Phase Class 0.5S Energy Meter Simulation
# Reference: TI ADS131M08 + TIDA-010243 | IEC 62053-22
# =============================================================

import numpy as np
import matplotlib.pyplot as plt

# ── Plot Style ────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': '#0d1117',
    'axes.facecolor':   '#161b22',
    'axes.edgecolor':   '#30363d',
    'axes.labelcolor':  '#e6edf3',
    'xtick.color':      '#8b949e',
    'ytick.color':      '#8b949e',
    'text.color':       '#e6edf3',
    'grid.color':       '#21262d',
    'grid.linewidth':   0.8,
    'legend.facecolor': '#161b22',
    'legend.edgecolor': '#30363d',
    'font.family':      'monospace',
    'axes.titlesize':   11,
    'axes.labelsize':   9,
})

PHASE_COLORS = ["#ee4511", "#f5e321", "#0fa8ee"]   # R=blue, Y=green, B=red
PHASE_NAMES  = ['Phase A (R)', 'Phase B (Y)', 'Phase C (B)']

# ── ADC Parameters (ADS131M08) ────────────────────────────────
ADC_BITS       = 24
V_REF          = 1.2                          # ±1.2V input range
ADC_MAX        = 2**(ADC_BITS - 1) - 1        # +8,388,607
ADC_MIN        = -(2**(ADC_BITS - 1))         # -8,388,608
LSB            = (2 * V_REF) / (2**ADC_BITS)  # 143.05 nV
NOISE_RMS_LSB  = 3.5                          # thermal noise ~3-4 LSB rms

# ── Sampling Parameters ───────────────────────────────────────
FS             = 8000          # Hz — ADS131M08 output data rate
F0             = 50            # Hz — grid frequency
N_CYCLES       = 10            # integration window (200 ms, per TIDA-010243)
SPC            = FS // F0      # samples per cycle = 160
N_SAMPLES      = N_CYCLES * SPC  # total samples = 1600

# ── Grid / Load Configuration ─────────────────────────────────
V_NOM_LN       = 230.0         # Vrms L-N
V_NOM_LL       = 400.0         # Vrms L-L

# Per-phase Irms — unbalanced load example
I_RMS          = [15.0, 12.0, 18.0]   # A per phase

# Per-phase power factor (lagging) — independently configurable
PF_LAG         = [0.85, 0.90, 0.80]   # cos(phi) per phase

# ── Front-End Scaling ─────────────────────────────────────────
# Voltage: resistor divider — 230V peak → fits within ±1.2V (90% FS)
V_PEAK_NOMINAL = V_NOM_LN * np.sqrt(2)             # 325.27 V
V_DIVIDER      = V_PEAK_NOMINAL / (V_REF * 0.9)    # 301.2:1

# Current: CT (1000:1) + burden resistor 10Ω
CT_RATIO       = 1000
BURDEN_R       = 10.0
I_FULLSCALE    = 20.0          # A — meter full-scale current

# ── Harmonic Configuration ────────────────────────────────────
# Format: harmonic_order: (V_percent, I_percent)
HARMONICS = {
    3:  (2.0, 5.0),    # 150 Hz — triplen, dominant in 3-phase loads
    5:  (3.0, 8.0),    # 250 Hz — VFD / rectifier loads
    7:  (1.5, 4.0),    # 350 Hz — VFD / rectifier loads
    11: (1.0, 2.0),    # 550 Hz — 12-pulse drives
    13: (0.5, 1.5),    # 650 Hz — 12-pulse drives
}

# ── Phase Angle Offsets (120° balanced) ───────────────────────
PHASE_OFFSET = [0, -2*np.pi/3, -4*np.pi/3]  # A, B, C in radians


def print_config():
    """Print full configuration summary."""
    print("=" * 62)
    print("  3-Phase Class 0.5S Energy Meter Simulation")
    print("  ADS131M08 Architecture | IEC 62053-22")
    print("=" * 62)

    print(f"\n{'─'*62}")
    print(f"  SAMPLING PARAMETERS")
    print(f"{'─'*62}")
    print(f"  fs              = {FS} Hz")
    print(f"  f0              = {F0} Hz")
    print(f"  Samples/cycle   = {SPC}")
    print(f"  Integration     = {N_CYCLES} cycles = {N_CYCLES * 1000 // F0} ms")
    print(f"  Total samples   = {N_SAMPLES}")

    print(f"\n{'─'*62}")
    print(f"  ADC PARAMETERS (ADS131M08)")
    print(f"{'─'*62}")
    print(f"  Resolution      = {ADC_BITS}-bit signed")
    print(f"  Input range     = ±{V_REF} V")
    print(f"  LSB size        = {LSB*1e9:.2f} nV")
    print(f"  ADC counts max  = ±{ADC_MAX:,}")
    print(f"  Thermal noise   = {NOISE_RMS_LSB} LSB rms = {NOISE_RMS_LSB*LSB*1e9:.1f} nV rms")
    print(f"  Theoretical SNR = {6.02 * ADC_BITS + 1.76:.1f} dB")

    print(f"\n{'─'*62}")
    print(f"  LOAD CONFIGURATION")
    print(f"{'─'*62}")
    print(f"  {'Phase':<14} {'Vrms (V)':<12} {'Irms (A)':<12} {'PF':<8} {'φ (°)'}")
    print(f"  {'─'*57}")
    for ph in range(3):
        phi_deg = np.degrees(np.arccos(PF_LAG[ph]))
        print(f"  {PHASE_NAMES[ph]:<14} {V_NOM_LN:<12.1f} "
              f"{I_RMS[ph]:<12.1f} {PF_LAG[ph]:<8.2f} {phi_deg:.1f}°")

    print(f"\n{'─'*62}")
    print(f"  HARMONIC CONTENT")
    print(f"{'─'*62}")
    print(f"  {'Order':<8} {'Freq (Hz)':<12} {'V (%)':<10} {'I (%)'}")
    print(f"  {'─'*42}")
    for order, (vp, ip) in HARMONICS.items():
        print(f"  {order:<8} {order*F0:<12} {vp:<10.1f} {ip:.1f}")

    print(f"\n{'─'*62}")
    print(f"  FRONT-END SCALING")
    print(f"{'─'*62}")
    print(f"  V divider ratio = {V_DIVIDER:.1f}:1")
    v_adc_pct = V_PEAK_NOMINAL / V_DIVIDER / V_REF * 100
    print(f"  V at ADC input  = ±{V_PEAK_NOMINAL/V_DIVIDER*1000:.1f} mV pk ({v_adc_pct:.0f}% FS)")
    print(f"  CT ratio        = {CT_RATIO}:1")
    print(f"  Burden R        = {BURDEN_R} Ω")
    i_adc_mv = (I_FULLSCALE * np.sqrt(2) / CT_RATIO) * BURDEN_R * 1000
    print(f"  I at ADC input  = ±{i_adc_mv:.1f} mV pk @ {I_FULLSCALE}A FS")
    print(f"\n  ✓ m00_config — Configuration loaded\n")


if __name__ == "__main__":
    print_config()
