# =============================================================
# m04_harmonics.py — FFT Harmonic Analysis + THD
# 3-Phase Class 0.5S Energy Meter Simulation
# Reference: TI ADS131M08 + TIDA-010243 | IEC 62053-22
# =============================================================
#
# Hanning-windowed FFT → per-harmonic magnitudes (V and A) →
# THD_V and THD_I per phase.  Harmonics 2–31 (up to 1550 Hz).
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m00_config import (
    FS, F0, N_SAMPLES,
    HARMONICS, PHASE_COLORS, PHASE_NAMES,
)

# Highest harmonic order to include in THD summation
THD_MAX_ORDER = 31


def compute_harmonics(v_recon, i_recon):
    """
    Compute FFT harmonic spectrum and THD for voltage and current.

    Parameters
    ----------
    v_recon : np.ndarray (3, N_SAMPLES) — reconstructed voltage (V)
    i_recon : np.ndarray (3, N_SAMPLES) — reconstructed current (A)

    Returns
    -------
    results_harmonics : dict with keys:
        freqs       (N_SAMPLES//2+1,) — frequency axis (Hz)
        v_mag       (3, N_SAMPLES//2+1) — one-sided voltage spectrum (V)
        i_mag       (3, N_SAMPLES//2+1) — one-sided current spectrum (A)
        v_harm      (3, THD_MAX_ORDER+1) — harmonic magnitudes V, index=order
        i_harm      (3, THD_MAX_ORDER+1) — harmonic magnitudes A, index=order
        thd_v       (3,) — voltage THD% per phase
        thd_i       (3,) — current THD% per phase
    """
    print(f"{'─'*62}")
    print(f"  MODULE 4 — FFT Harmonic Analysis + THD")
    print(f"{'─'*62}")

    n_fft   = N_SAMPLES
    freqs   = np.fft.rfftfreq(n_fft, d=1.0 / FS)          # Hz

    # Hanning window reduces spectral leakage: energy from a non-integer
    # number of cycles spreads into neighbouring bins without windowing.
    # With 10 exact cycles at 50 Hz and fs=8 kHz the leakage is already
    # zero, but the window is kept for robustness to slight freq offsets.
    window  = np.hanning(n_fft)

    # w_norm = sum of window coefficients.  Dividing the FFT magnitude
    # by w_norm corrects for the amplitude attenuation the window applies
    # to the signal, recovering true peak amplitude at each frequency bin.
    w_norm  = np.sum(window)                                # amplitude correction

    # Bin index for harmonic h: h * F0 / (FS/N_SAMPLES) = h * F0 * N_SAMPLES / FS
    freq_res = FS / n_fft                                   # 5 Hz per bin

    v_mag  = np.zeros((3, len(freqs)))
    i_mag  = np.zeros((3, len(freqs)))
    v_harm = np.zeros((3, THD_MAX_ORDER + 1))
    i_harm = np.zeros((3, THD_MAX_ORDER + 1))

    for ph in range(3):
        v_fft = np.fft.rfft(v_recon[ph] * window)
        i_fft = np.fft.rfft(i_recon[ph] * window)

        # One-sided amplitude spectrum (amplitude-correct with window norm).
        # Factor of 2 folds the energy of the negative-frequency mirror
        # bins back onto the positive side (rfft discards them), so the
        # magnitude here represents the true peak amplitude of each sinusoid.
        v_mag[ph] = 2 * np.abs(v_fft) / w_norm
        i_mag[ph] = 2 * np.abs(i_fft) / w_norm
        # DC bin (index 0) has no negative-frequency mirror, so the factor
        # of 2 is undone for it.  Nyquist bin (last) is similar but DC is
        # the only one that matters for energy meters.
        v_mag[ph, 0] /= 2
        i_mag[ph, 0] /= 2

        # Extract magnitudes at harmonic bin indices.
        # bin_idx = round(h × F0 / freq_res): the FFT bin whose centre
        # frequency is closest to the h-th harmonic.  With freq_res = 5 Hz
        # and F0 = 50 Hz, harmonics land exactly on bin centres (50/5 = 10),
        # so there is no spectral interpolation error.
        for h in range(1, THD_MAX_ORDER + 1):
            bin_idx = round(h * F0 / freq_res)
            if bin_idx < len(freqs):
                v_harm[ph, h] = v_mag[ph, bin_idx]
                i_harm[ph, h] = i_mag[ph, bin_idx]

    # THD: sqrt(sum of harmonics 2..THD_MAX_ORDER squared) / fundamental * 100
    thd_v = (np.sqrt(np.sum(v_harm[:, 2:THD_MAX_ORDER+1] ** 2, axis=1))
             / v_harm[:, 1] * 100)
    thd_i = (np.sqrt(np.sum(i_harm[:, 2:THD_MAX_ORDER+1] ** 2, axis=1))
             / i_harm[:, 1] * 100)

    results_harmonics = {
        'freqs':  freqs,
        'v_mag':  v_mag,
        'i_mag':  i_mag,
        'v_harm': v_harm,
        'i_harm': i_harm,
        'thd_v':  thd_v,
        'thd_i':  thd_i,
    }

    _print_results(results_harmonics)
    return results_harmonics


def _print_results(r):
    orders = sorted(HARMONICS.keys())
    ph_labels = ['A (R)', 'B (Y)', 'C (B)']

    print(f"\n  HARMONIC MAGNITUDES — VOLTAGE (V rms equivalent)")
    print(f"  {'─'*60}")
    header = f"  {'Order':<8} {'Freq':>6}"
    for ph in range(3):
        header += f"  {'Ph '+ph_labels[ph]:>12}"
    header += f"  {'Config V%':>10}"
    print(header)
    print(f"  {'─'*60}")
    for h in [1] + orders:
        cfg = f"{HARMONICS[h][0]:.1f}%" if h in HARMONICS else ('fund.' if h == 1 else '—')
        row = f"  {h:<8} {h*F0:>6.0f} Hz"
        for ph in range(3):
            row += f"  {r['v_harm'][ph, h]:>12.4f}"
        row += f"  {cfg:>10}"
        print(row)

    print(f"\n  HARMONIC MAGNITUDES — CURRENT (A rms equivalent)")
    print(f"  {'─'*60}")
    header2 = f"  {'Order':<8} {'Freq':>6}"
    for ph in range(3):
        header2 += f"  {'Ph '+ph_labels[ph]:>12}"
    header2 += f"  {'Config I%':>10}"
    print(header2)
    print(f"  {'─'*60}")
    for h in [1] + orders:
        cfg = f"{HARMONICS[h][1]:.1f}%" if h in HARMONICS else ('fund.' if h == 1 else '—')
        row = f"  {h:<8} {h*F0:>6.0f} Hz"
        for ph in range(3):
            row += f"  {r['i_harm'][ph, h]:>12.4f}"
        row += f"  {cfg:>10}"
        print(row)

    print(f"\n  THD SUMMARY")
    print(f"  {'─'*40}")
    print(f"  {'Phase':<12} {'THD_V (%)':<14} {'THD_I (%)'}")
    print(f"  {'─'*40}")
    for ph in range(3):
        print(f"  {ph_labels[ph]:<12} {r['thd_v'][ph]:<14.4f} {r['thd_i'][ph]:.4f}")
    print(f"\n  ✓ m04_harmonics — FFT + THD computed | "
          f"Hanning window | harmonics up to order {THD_MAX_ORDER}\n")


def plot_harmonics(results_harmonics, save_path=None):
    """6-panel harmonic analysis visualization."""

    r          = results_harmonics
    orders_cfg = sorted(HARMONICS.keys())
    ph_labels  = ['Ph A', 'Ph B', 'Ph C']

    fig = plt.figure(figsize=(18, 12), facecolor='#0d1117')
    fig.suptitle(
        'Module 4 — FFT Harmonic Analysis & THD\n'
        '3-Phase 50 Hz | ADS131M08 | Hanning Window | 10-Cycle',
        fontsize=13, color='#e6edf3', y=0.98, fontfamily='monospace'
    )
    gs = gridspec.GridSpec(2, 3, figure=fig,
                           hspace=0.50, wspace=0.38,
                           left=0.07, right=0.97,
                           top=0.91, bottom=0.08)

    freq_max = (THD_MAX_ORDER + 2) * F0

    # ── Plot 1: Voltage spectrum — all 3 phases ───────────────
    ax1 = fig.add_subplot(gs[0, 0])
    for ph in range(3):
        ax1.plot(r['freqs'], r['v_mag'][ph],
                 color=PHASE_COLORS[ph], lw=0.9, alpha=0.85,
                 label=ph_labels[ph])
    for h in [1] + orders_cfg:
        ax1.axvline(h * F0, color='#30363d', lw=0.6, ls='--', alpha=0.5)
    ax1.set_xlim(0, freq_max)
    ax1.set_title('Voltage Spectrum (Hanning FFT)')
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('Magnitude (V)')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # ── Plot 2: Current spectrum — all 3 phases ───────────────
    ax2 = fig.add_subplot(gs[0, 1])
    for ph in range(3):
        ax2.plot(r['freqs'], r['i_mag'][ph],
                 color=PHASE_COLORS[ph], lw=0.9, alpha=0.85,
                 label=ph_labels[ph])
    for h in [1] + orders_cfg:
        ax2.axvline(h * F0, color='#30363d', lw=0.6, ls='--', alpha=0.5)
    ax2.set_xlim(0, freq_max)
    ax2.set_title('Current Spectrum (Hanning FFT)')
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Magnitude (A)')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    # ── Plot 3: THD per phase ─────────────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    x    = np.arange(3)
    bw   = 0.35
    ax3.bar(x - bw/2, r['thd_v'], bw, color=PHASE_COLORS, alpha=0.85,
            label='THD_V (%)')
    ax3.bar(x + bw/2, r['thd_i'], bw, color=PHASE_COLORS, alpha=0.45,
            label='THD_I (%)', hatch='//')
    for i in range(3):
        ax3.text(x[i] - bw/2, r['thd_v'][i] + 0.05,
                 f"{r['thd_v'][i]:.2f}", ha='center', fontsize=7.5,
                 color='#e6edf3')
        ax3.text(x[i] + bw/2, r['thd_i'][i] + 0.05,
                 f"{r['thd_i'][i]:.2f}", ha='center', fontsize=7.5,
                 color='#e6edf3')
    ax3.set_xticks(x)
    ax3.set_xticklabels(ph_labels)
    ax3.set_title('THD — Voltage & Current (%)')
    ax3.set_ylabel('THD (%)')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')

    # ── Plot 4: Voltage harmonics as % of fundamental ─────────
    ax4 = fig.add_subplot(gs[1, 0])
    bar_w4 = 0.25
    x4 = np.arange(len(orders_cfg))
    for i, ph in enumerate(range(3)):
        vals = [r['v_harm'][ph, h] / r['v_harm'][ph, 1] * 100
                for h in orders_cfg]
        ax4.bar(x4 + (i - 1) * bar_w4, vals, bar_w4,
                color=PHASE_COLORS[ph], alpha=0.85, label=ph_labels[ph])
    # configured % markers
    cfg_v = [HARMONICS[h][0] for h in orders_cfg]
    ax4.plot(x4, cfg_v, 'D--', color='#ffa657', ms=5, lw=1,
             label='Configured %')
    ax4.set_xticks(x4)
    ax4.set_xticklabels([f'H{h}\n{h*F0:.0f}Hz' for h in orders_cfg])
    ax4.set_title('Voltage Harmonics — % of Fundamental')
    ax4.set_ylabel('Magnitude (% of V1)')
    ax4.legend(fontsize=7.5)
    ax4.grid(True, alpha=0.3, axis='y')

    # ── Plot 5: Current harmonics as % of fundamental ─────────
    ax5 = fig.add_subplot(gs[1, 1])
    bar_w5 = 0.25
    x5 = np.arange(len(orders_cfg))
    for i, ph in enumerate(range(3)):
        vals = [r['i_harm'][ph, h] / r['i_harm'][ph, 1] * 100
                for h in orders_cfg]
        ax5.bar(x5 + (i - 1) * bar_w5, vals, bar_w5,
                color=PHASE_COLORS[ph], alpha=0.85, label=ph_labels[ph])
    cfg_i = [HARMONICS[h][1] for h in orders_cfg]
    ax5.plot(x5, cfg_i, 'D--', color='#ffa657', ms=5, lw=1,
             label='Configured %')
    ax5.set_xticks(x5)
    ax5.set_xticklabels([f'H{h}\n{h*F0:.0f}Hz' for h in orders_cfg])
    ax5.set_title('Current Harmonics — % of Fundamental')
    ax5.set_ylabel('Magnitude (% of I1)')
    ax5.legend(fontsize=7.5)
    ax5.grid(True, alpha=0.3, axis='y')

    # ── Plot 6: Summary ───────────────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')
    ph_labels_s = ['A (R)', 'B (Y)', 'C (B)']
    lines = [
        ('HARMONIC SUMMARY', None),
        ('', None),
        ('Voltage Fundamentals (V):', '#8b949e'),
        ('', None),
        *[(f'  Ph {ph_labels_s[ph]}: {r["v_harm"][ph,1]:.3f} V',
           PHASE_COLORS[ph]) for ph in range(3)],
        ('', None),
        ('Current Fundamentals (A):', '#8b949e'),
        ('', None),
        *[(f'  Ph {ph_labels_s[ph]}: {r["i_harm"][ph,1]:.4f} A',
           PHASE_COLORS[ph]) for ph in range(3)],
        ('', None),
        ('THD (V% / I%):', '#8b949e'),
        ('', None),
        *[(f'  Ph {ph_labels_s[ph]}: {r["thd_v"][ph]:.3f}% / {r["thd_i"][ph]:.3f}%',
           PHASE_COLORS[ph]) for ph in range(3)],
        ('', None),
        (f'  Window : Hanning ({N_SAMPLES} pts)', '#8b949e'),
        (f'  Res    : {FS/N_SAMPLES:.1f} Hz/bin', '#8b949e'),
        (f'  Max ord: {THD_MAX_ORDER} ({THD_MAX_ORDER*F0:.0f} Hz)', '#8b949e'),
    ]
    y = 0.97
    for line, color in lines:
        c = color if color else '#8b949e'
        weight = 'bold' if line and not line.startswith(' ') else 'normal'
        ax6.text(0.03, y, line, transform=ax6.transAxes,
                 fontsize=8.5, color=c, fontweight=weight,
                 verticalalignment='top', fontfamily='monospace')
        y -= 0.060
    ax6.set_title('Harmonic Summary')

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight',
                    facecolor='#0d1117')
        print(f"  Plot saved: {save_path}")
    plt.show()


if __name__ == "__main__":
    import pathlib
    REPO_ROOT  = pathlib.Path(__file__).resolve().parent.parent
    OUTPUT_DIR = REPO_ROOT / "outputs"
    OUTPUT_DIR.mkdir(exist_ok=True)

    from m01_signal_gen import generate_signals
    t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon = generate_signals()

    results_harmonics = compute_harmonics(v_recon, i_recon)
    plot_harmonics(results_harmonics,
                   save_path=str(OUTPUT_DIR / "m04_harmonics.png"))
