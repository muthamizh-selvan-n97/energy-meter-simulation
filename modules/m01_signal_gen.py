# =============================================================
# m01_signal_gen.py — Signal Generation + 24-bit Quantization
# 3-Phase Class 0.5S Energy Meter Simulation
# Reference: TI ADS131M08 + TIDA-010243 | IEC 62053-22
# =============================================================
#
# Signal chain modelled:
#   Analog signal → Front-end scaling → Thermal noise →
#   24-bit quantization → Reconstruction to physical units
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m00_config import (
    FS, F0, N_CYCLES, SPC, N_SAMPLES,
    V_NOM_LN, I_RMS, PF_LAG,
    ADC_BITS, V_REF, ADC_MAX, ADC_MIN, LSB, NOISE_RMS_LSB,
    V_PEAK_NOMINAL, V_DIVIDER, CT_RATIO, BURDEN_R,
    HARMONICS, PHASE_OFFSET,
    PHASE_COLORS, PHASE_NAMES,
    print_config
)


def generate_signals(seed=42):
    """
    Generate 3-phase voltage and current signals with harmonics,
    scale to ADC input range, add thermal noise, quantize to 24-bit.

    Returns
    -------
    t          : np.ndarray (N_SAMPLES,)  — time vector (s)
    v_actual   : np.ndarray (3, N_SAMPLES) — actual voltage (V)
    i_actual   : np.ndarray (3, N_SAMPLES) — actual current (A)
    v_counts   : np.ndarray (3, N_SAMPLES, int32) — ADC counts, voltage
    i_counts   : np.ndarray (3, N_SAMPLES, int32) — ADC counts, current
    v_recon    : np.ndarray (3, N_SAMPLES) — reconstructed voltage (V)
    i_recon    : np.ndarray (3, N_SAMPLES) — reconstructed current (A)
    """
    print(f"{'─'*62}")
    print(f"  MODULE 1 — Signal Generation + Quantization")
    print(f"{'─'*62}")

    t          = np.arange(N_SAMPLES) / FS
    v_actual   = np.zeros((3, N_SAMPLES))
    i_actual   = np.zeros((3, N_SAMPLES))
    v_adc_in   = np.zeros((3, N_SAMPLES))
    i_adc_in   = np.zeros((3, N_SAMPLES))
    v_counts   = np.zeros((3, N_SAMPLES), dtype=np.int32)
    i_counts   = np.zeros((3, N_SAMPLES), dtype=np.int32)
    v_recon    = np.zeros((3, N_SAMPLES))
    i_recon    = np.zeros((3, N_SAMPLES))

    np.random.seed(seed)
    w = 2 * np.pi * F0

    for ph in range(3):
        phi    = np.arccos(PF_LAG[ph])
        theta  = PHASE_OFFSET[ph]

        # ── Fundamental ───────────────────────────────────────
        V_peak = V_NOM_LN * np.sqrt(2)
        I_peak = I_RMS[ph] * np.sqrt(2)

        v_sig  = V_peak * np.sin(w * t + theta)
        i_sig  = I_peak * np.sin(w * t + theta - phi)

        # ── Harmonics ─────────────────────────────────────────
        for order, (vp_pct, ip_pct) in HARMONICS.items():
            v_sig += (vp_pct / 100) * V_peak * np.sin(order * w * t + theta)
            i_sig += (ip_pct / 100) * I_peak * np.sin(order * w * t + theta - phi)

        v_actual[ph] = v_sig
        i_actual[ph] = i_sig

        # ── Scale to ADC input (front-end) ────────────────────
        v_in = v_sig / V_DIVIDER
        i_in = (i_sig / CT_RATIO) * BURDEN_R

        v_adc_in[ph] = v_in
        i_adc_in[ph] = i_in

        # ── Thermal noise ─────────────────────────────────────
        v_noisy = v_in + np.random.normal(0, NOISE_RMS_LSB * LSB, N_SAMPLES)
        i_noisy = i_in + np.random.normal(0, NOISE_RMS_LSB * LSB, N_SAMPLES)

        # ── 24-bit Quantization ───────────────────────────────
        v_q = np.round(v_noisy / LSB).astype(np.int32)
        i_q = np.round(i_noisy / LSB).astype(np.int32)

        v_counts[ph] = np.clip(v_q, ADC_MIN, ADC_MAX)
        i_counts[ph] = np.clip(i_q, ADC_MIN, ADC_MAX)

        # ── Reconstruct physical values from counts ───────────
        v_recon[ph] = v_counts[ph] * LSB * V_DIVIDER
        i_recon[ph] = i_counts[ph] * LSB * CT_RATIO / BURDEN_R

    _print_stats(v_actual, i_actual, v_adc_in, i_adc_in,
                 v_counts, i_counts, v_recon, i_recon)

    return t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon


def _print_stats(v_actual, i_actual, v_adc_in, i_adc_in,
                 v_counts, i_counts, v_recon, i_recon):

    print(f"\n  {'Phase':<14} {'V peak (V)':<14} {'I peak (A)':<14} "
          f"{'V ADC pk (mV)':<16} {'I ADC pk (mV)'}")
    print(f"  {'─'*70}")
    for ph in range(3):
        print(f"  {PHASE_NAMES[ph]:<14} "
              f"{np.max(np.abs(v_actual[ph])):<14.2f} "
              f"{np.max(np.abs(i_actual[ph])):<14.3f} "
              f"{np.max(np.abs(v_adc_in[ph]))*1000:<16.2f} "
              f"{np.max(np.abs(i_adc_in[ph]))*1000:.2f}")

    print(f"\n  ADC COUNT UTILIZATION:")
    print(f"  {'─'*70}")
    for ph in range(3):
        vc_pk  = max(abs(np.max(v_counts[ph])), abs(np.min(v_counts[ph])))
        ic_pk  = max(abs(np.max(i_counts[ph])), abs(np.min(i_counts[ph])))
        v_util = vc_pk / ADC_MAX * 100
        i_util = ic_pk / ADC_MAX * 100
        print(f"  Ph {['A','B','C'][ph]}: "
              f"V [{np.min(v_counts[ph]):>11,} to {np.max(v_counts[ph]):>11,}] "
              f"({v_util:.1f}% FS)  |  "
              f"I [{np.min(i_counts[ph]):>9,} to {np.max(i_counts[ph]):>9,}] "
              f"({i_util:.1f}% FS)")

    print(f"\n  QUANTIZATION ERROR (Phase A):")
    print(f"  {'─'*70}")
    q_err_v = v_recon[0] - v_actual[0]
    q_err_i = i_recon[0] - i_actual[0]
    print(f"  V error rms = {np.sqrt(np.mean(q_err_v**2))*1000:.4f} mV  "
          f"({np.sqrt(np.mean(q_err_v**2))/V_NOM_LN*100:.6f}% of Vnom)")
    print(f"  I error rms = {np.sqrt(np.mean(q_err_i**2))*1000:.4f} mA  "
          f"({np.sqrt(np.mean(q_err_i**2))/I_RMS[0]*100:.6f}% of Inom)")
    print(f"\n  ✓ m01_signal_gen — {N_SAMPLES} samples/phase | "
          f"24-bit quantized | reconstructed\n")


def plot_signals(t, v_actual, i_actual, v_counts, i_counts,
                 v_recon, i_recon, save_path=None):
    """Generate 6-panel signal generation + quantization plots."""

    fig = plt.figure(figsize=(18, 14), facecolor='#0d1117')
    fig.suptitle(
        'Module 1 — Signal Generation & Quantization\n'
        '3-Phase 50 Hz | ADS131M08 | fs = 8 kHz | 10-Cycle Window',
        fontsize=13, color='#e6edf3', y=0.98, fontfamily='monospace'
    )
    gs = gridspec.GridSpec(3, 2, figure=fig,
                           hspace=0.45, wspace=0.35,
                           left=0.07, right=0.97,
                           top=0.93, bottom=0.06)

    show2  = 2 * SPC
    t_ms   = t[:show2] * 1000
    t_1cyc = t[:SPC] * 1000

    # ── Plot 1: 3-Phase Voltage ───────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    for ph in range(3):
        ax1.plot(t_ms, v_recon[ph, :show2],
                 color=PHASE_COLORS[ph], lw=1.2, label=PHASE_NAMES[ph])
    ax1.axhline(0, color='#30363d', lw=0.8)
    ax1.set_title('3-Phase Voltage Waveforms (Reconstructed from ADC)')
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend(fontsize=8, loc='upper right')
    ax1.grid(True, alpha=0.4)
    ax1.set_xlim(0, t_ms[-1])

    # ── Plot 2: 3-Phase Current ───────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    for ph in range(3):
        ax2.plot(t_ms, i_recon[ph, :show2],
                 color=PHASE_COLORS[ph], lw=1.2, label=PHASE_NAMES[ph])
    ax2.axhline(0, color='#30363d', lw=0.8)
    ax2.set_title('3-Phase Current Waveforms (Reconstructed from ADC)')
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Current (A)')
    ax2.legend(fontsize=8, loc='upper right')
    ax2.grid(True, alpha=0.4)
    ax2.set_xlim(0, t_ms[-1])

    # ── Plot 3: Raw ADC counts Phase A ────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(t_1cyc, v_counts[0, :SPC],
             color=PHASE_COLORS[0], lw=1.0, label='V counts (Phase A)')
    ax3.axhline(ADC_MAX, color='#f78166', lw=0.7, ls='--',
                alpha=0.5, label=f'±FS ({ADC_MAX:,})')
    ax3.axhline(-ADC_MAX, color='#f78166', lw=0.7, ls='--', alpha=0.5)
    ax3.axhline(0, color='#30363d', lw=0.8)
    ax3.set_title('ADC Raw Integer Counts — Voltage Phase A (1 cycle)')
    ax3.set_xlabel('Time (ms)')
    ax3.set_ylabel('ADC Count (24-bit signed)')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.4)
    ax3.set_xlim(0, t_1cyc[-1])

    # ── Plot 4: Quantization staircase zoom ───────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    zc_idx = np.where(np.diff(np.sign(v_actual[0, :SPC])) > 0)[0]
    zc = zc_idx[0] if len(zc_idx) > 0 else 0
    zs = max(0, zc - 4)
    ze = min(SPC, zc + 9)

    t_z  = t[zs:ze] * 1000
    v_id = v_actual[0, zs:ze]
    v_qu = v_recon[0, zs:ze]

    ax4.step(t_z, v_qu, where='post',
             color='#f78166', lw=1.5, label='Quantized (ADC output)', zorder=3)
    ax4.plot(t_z, v_id,
             color='#58a6ff', lw=1.2, ls='--', label='Ideal analog', alpha=0.8)
    ax4.scatter(t_z, v_qu, color='#ffa657', s=30, zorder=4, label='Sample points')

    lsb_v = LSB * V_DIVIDER
    ax4.annotate(f'1 LSB = {lsb_v*1e3:.3f} mV\n(referred to actual V)',
                 xy=(t_z[3], v_qu[3]),
                 xytext=(t_z[3] + 0.05, v_qu[3] + lsb_v * 4),
                 fontsize=7.5, color='#ffa657',
                 arrowprops=dict(arrowstyle='->', color='#ffa657', lw=0.8))

    ax4.set_title('Quantization Staircase — Zero Crossing Zoom (Phase A)')
    ax4.set_xlabel('Time (ms)')
    ax4.set_ylabel('Voltage (V)')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.4)

    # ── Plot 5: Ideal vs quantized overlay ────────────────────
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.plot(t_1cyc, v_actual[0, :SPC],
             color='#58a6ff', lw=1.5, ls='--',
             label='Ideal (no quantization)', alpha=0.9)
    ax5.plot(t_1cyc, v_recon[0, :SPC],
             color='#3fb950', lw=1.0,
             label='Quantized + noise + reconstructed', alpha=0.8)
    ax5.set_title('Ideal vs Quantized Voltage — Phase A (1 cycle)')
    ax5.set_xlabel('Time (ms)')
    ax5.set_ylabel('Voltage (V)')
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.4)
    ax5.set_xlim(0, t_1cyc[-1])

    # ── Plot 6: Quantization error ────────────────────────────
    ax6 = fig.add_subplot(gs[2, 1])
    q_err = (v_recon[0, :SPC] - v_actual[0, :SPC]) * 1000
    half_lsb_mv = LSB * V_DIVIDER * 1000 / 2
    ax6.plot(t_1cyc, q_err,
             color='#ffa657', lw=0.9, label='Quantization + noise error')
    ax6.axhline(half_lsb_mv, color='#f78166', ls='--', lw=0.8,
                alpha=0.7, label=f'±½ LSB = {half_lsb_mv:.3f} mV')
    ax6.axhline(-half_lsb_mv, color='#f78166', ls='--', lw=0.8, alpha=0.7)
    ax6.axhline(0, color='#30363d', lw=0.8)
    ax6.set_title('Voltage Quantization + Noise Error — Phase A (1 cycle)')
    ax6.set_xlabel('Time (ms)')
    ax6.set_ylabel('Error (mV)')
    ax6.legend(fontsize=8)
    ax6.grid(True, alpha=0.4)
    ax6.set_xlim(0, t_1cyc[-1])

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight',
                    facecolor='#0d1117')
        print(f"  Plot saved: {save_path}")
    plt.show()


if __name__ == "__main__":
    import pathlib
    # Works regardless of where you run from (modules\ or repo root)
    REPO_ROOT  = pathlib.Path(__file__).resolve().parent.parent
    OUTPUT_DIR = REPO_ROOT / "outputs"
    OUTPUT_DIR.mkdir(exist_ok=True)

    print_config()
    t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon = generate_signals()
    plot_signals(t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon,
                 save_path=str(OUTPUT_DIR / "m01_signal_gen.png"))