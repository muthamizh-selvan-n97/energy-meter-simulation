# =============================================================
# m02_rms.py — True RMS Computation
# 3-Phase Class 0.5S Energy Meter Simulation
# Reference: TI ADS131M08 + TIDA-010243 | IEC 62053-22
# =============================================================
#
# Computes per-phase Vrms, Irms, line-to-line voltages,
# and phase/load unbalance from reconstructed ADC signals.
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m00_config import (
    FS, F0, N_SAMPLES,
    V_NOM_LN, V_NOM_LL, I_RMS, I_FULLSCALE,
    PHASE_COLORS, PHASE_NAMES,
)


def compute_rms(v_recon, i_recon):
    """
    Compute true RMS values from reconstructed ADC signals.

    Parameters
    ----------
    v_recon : np.ndarray (3, N_SAMPLES) — reconstructed voltage (V)
    i_recon : np.ndarray (3, N_SAMPLES) — reconstructed current (A)

    Returns
    -------
    results_rms : dict with keys:
        vrms            (3,)  — per-phase Vrms (V)
        irms            (3,)  — per-phase Irms (A)
        vll             (3,)  — line-to-line Vrms: AB, BC, CA (V)
        vrms_err_pct    (3,)  — % deviation of Vrms from V_NOM_LN
        irms_err_pct    (3,)  — % deviation of Irms from configured I_RMS
        v_unbalance_pct float — NEMA voltage unbalance %
        i_unbalance_pct float — NEMA current unbalance %
    """
    print(f"{'─'*62}")
    print(f"  MODULE 2 — True RMS Computation")
    print(f"{'─'*62}")

    # ── Per-phase Vrms and Irms ───────────────────────────────
    vrms = np.sqrt(np.mean(v_recon ** 2, axis=1))   # (3,)
    irms = np.sqrt(np.mean(i_recon ** 2, axis=1))   # (3,)

    # ── Line-to-line voltages ─────────────────────────────────
    vll = np.array([
        np.sqrt(np.mean((v_recon[0] - v_recon[1]) ** 2)),  # V_AB
        np.sqrt(np.mean((v_recon[1] - v_recon[2]) ** 2)),  # V_BC
        np.sqrt(np.mean((v_recon[2] - v_recon[0]) ** 2)),  # V_CA
    ])

    # ── Deviation from nominal ────────────────────────────────
    vrms_err_pct = (vrms - V_NOM_LN) / V_NOM_LN * 100
    irms_err_pct = (irms - np.array(I_RMS)) / np.array(I_RMS) * 100

    # ── Unbalance (NEMA MG1 definition) ──────────────────────
    # NEMA MG1 Part 14.35: unbalance % = max deviation of any phase
    # from the 3-phase average, divided by the average, times 100.
    # This is the worst-case (most conservative) definition and is
    # used by motor and power-quality standards in India/US.
    # IEC 61000-4-27 uses negative-sequence / positive-sequence ratio,
    # but the NEMA method is simpler and sufficient for this meter model.
    vrms_avg       = np.mean(vrms)
    v_unbalance_pct = np.max(np.abs(vrms - vrms_avg)) / vrms_avg * 100

    irms_avg       = np.mean(irms)
    i_unbalance_pct = np.max(np.abs(irms - irms_avg)) / irms_avg * 100

    results_rms = {
        'vrms':            vrms,
        'irms':            irms,
        'vll':             vll,
        'vrms_err_pct':    vrms_err_pct,
        'irms_err_pct':    irms_err_pct,
        'v_unbalance_pct': v_unbalance_pct,
        'i_unbalance_pct': i_unbalance_pct,
    }

    _print_results(results_rms)
    return results_rms


def _print_results(r):
    ph_labels = ['A (R)', 'B (Y)', 'C (B)']

    print(f"\n  PER-PHASE VOLTAGE RMS")
    print(f"  {'─'*57}")
    print(f"  {'Phase':<12} {'Vrms (V)':<14} {'Nominal (V)':<14} {'Error (%)'}")
    print(f"  {'─'*57}")
    for ph in range(3):
        print(f"  {ph_labels[ph]:<12} {r['vrms'][ph]:<14.4f} "
              f"{V_NOM_LN:<14.1f} {r['vrms_err_pct'][ph]:+.4f}")

    vll_labels = ['V_AB', 'V_BC', 'V_CA']
    print(f"\n  LINE-TO-LINE VOLTAGE RMS")
    print(f"  {'─'*57}")
    print(f"  {'Pair':<12} {'VLL (V)':<14} {'Nominal (V)':<14} {'Error (%)'}")
    print(f"  {'─'*57}")
    for i, lbl in enumerate(vll_labels):
        err = (r['vll'][i] - V_NOM_LL) / V_NOM_LL * 100
        print(f"  {lbl:<12} {r['vll'][i]:<14.4f} {V_NOM_LL:<14.1f} {err:+.4f}")

    print(f"\n  PER-PHASE CURRENT RMS")
    print(f"  {'─'*57}")
    print(f"  {'Phase':<12} {'Irms (A)':<14} {'Nominal (A)':<14} {'Error (%)'}")
    print(f"  {'─'*57}")
    for ph in range(3):
        print(f"  {ph_labels[ph]:<12} {r['irms'][ph]:<14.4f} "
              f"{I_RMS[ph]:<14.1f} {r['irms_err_pct'][ph]:+.4f}")

    print(f"\n  UNBALANCE (NEMA MG1)")
    print(f"  {'─'*57}")
    print(f"  Voltage unbalance : {r['v_unbalance_pct']:.4f}%")
    print(f"  Current unbalance : {r['i_unbalance_pct']:.4f}%")
    print(f"\n  ✓ m02_rms — Vrms, Irms, VLL computed | "
          f"{N_SAMPLES} samples/phase\n")


def plot_rms(results_rms, save_path=None):
    """6-panel RMS results visualization."""

    r          = results_rms
    ph_labels  = ['Ph A (R)', 'Ph B (Y)', 'Ph C (B)']
    vll_labels = ['V_AB', 'V_BC', 'V_CA']
    x_ph       = np.arange(3)
    x_ll       = np.arange(3)
    bar_w      = 0.35

    fig = plt.figure(figsize=(18, 12), facecolor='#0d1117')
    fig.suptitle(
        'Module 2 — True RMS Computation\n'
        '3-Phase 50 Hz | ADS131M08 | fs = 8 kHz | 10-Cycle Window',
        fontsize=13, color='#e6edf3', y=0.98, fontfamily='monospace'
    )
    gs = gridspec.GridSpec(2, 3, figure=fig,
                           hspace=0.50, wspace=0.38,
                           left=0.07, right=0.97,
                           top=0.91, bottom=0.08)

    # ── Plot 1: Per-phase Vrms vs Nominal ────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    bars = ax1.bar(x_ph - bar_w/2, r['vrms'], bar_w,
                   color=PHASE_COLORS, alpha=0.85, label='Measured Vrms')
    ax1.bar(x_ph + bar_w/2, [V_NOM_LN]*3, bar_w,
            color='#30363d', alpha=0.6, label=f'Nominal {V_NOM_LN} V')
    for bar, val in zip(bars, r['vrms']):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=8,
                 color='#e6edf3')
    ax1.set_xticks(x_ph)
    ax1.set_xticklabels(ph_labels)
    ax1.set_title('Per-Phase Vrms vs Nominal')
    ax1.set_ylabel('Voltage (V)')
    ax1.set_ylim(0, V_NOM_LN * 1.15)
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3, axis='y')

    # ── Plot 2: Per-phase Irms vs Nominal ────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    bars2 = ax2.bar(x_ph - bar_w/2, r['irms'], bar_w,
                    color=PHASE_COLORS, alpha=0.85, label='Measured Irms')
    ax2.bar(x_ph + bar_w/2, I_RMS, bar_w,
            color='#30363d', alpha=0.6, label='Configured Irms')
    for bar, val in zip(bars2, r['irms']):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=8,
                 color='#e6edf3')
    ax2.set_xticks(x_ph)
    ax2.set_xticklabels(ph_labels)
    ax2.set_title('Per-Phase Irms vs Configured')
    ax2.set_ylabel('Current (A)')
    ax2.set_ylim(0, I_FULLSCALE * 1.15)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')

    # ── Plot 3: Line-to-line voltages ─────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    vll_colors = ['#c084fc', '#67e8f9', '#86efac']
    bars3 = ax3.bar(x_ll - bar_w/2, r['vll'], bar_w,
                    color=vll_colors, alpha=0.85, label='Measured VLL')
    ax3.bar(x_ll + bar_w/2, [V_NOM_LL]*3, bar_w,
            color='#30363d', alpha=0.6, label=f'Nominal {V_NOM_LL} V')
    for bar, val in zip(bars3, r['vll']):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=8,
                 color='#e6edf3')
    ax3.set_xticks(x_ll)
    ax3.set_xticklabels(vll_labels)
    ax3.set_title('Line-to-Line Voltage Rms')
    ax3.set_ylabel('Voltage (V)')
    ax3.set_ylim(0, V_NOM_LL * 1.15)
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')

    # ── Plot 4: Vrms error % ──────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 0])
    err_colors = [PHASE_COLORS[ph] for ph in range(3)]
    errs = r['vrms_err_pct']
    bars4 = ax4.bar(x_ph, errs, 0.5, color=err_colors, alpha=0.85)
    ax4.axhline(0, color='#e6edf3', lw=0.8, ls='--')
    ax4.axhline( 0.5, color='#f78166', lw=0.8, ls=':', alpha=0.7, label='±0.5% limit')
    ax4.axhline(-0.5, color='#f78166', lw=0.8, ls=':', alpha=0.7)
    for bar, val in zip(bars4, errs):
        ypos = val + 0.002 if val >= 0 else val - 0.006
        ax4.text(bar.get_x() + bar.get_width()/2, ypos,
                 f'{val:+.4f}%', ha='center', va='bottom', fontsize=8,
                 color='#e6edf3')
    ax4.set_xticks(x_ph)
    ax4.set_xticklabels(ph_labels)
    ax4.set_title('Vrms Deviation from Nominal (%)')
    ax4.set_ylabel('Error (%)')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3, axis='y')

    # ── Plot 5: Irms error % ──────────────────────────────────
    ax5 = fig.add_subplot(gs[1, 1])
    ierrs = r['irms_err_pct']
    bars5 = ax5.bar(x_ph, ierrs, 0.5, color=PHASE_COLORS, alpha=0.85)
    ax5.axhline(0, color='#e6edf3', lw=0.8, ls='--')
    ax5.axhline( 0.5, color='#f78166', lw=0.8, ls=':', alpha=0.7, label='±0.5% limit')
    ax5.axhline(-0.5, color='#f78166', lw=0.8, ls=':', alpha=0.7)
    for bar, val in zip(bars5, ierrs):
        ypos = val + 0.002 if val >= 0 else val - 0.006
        ax5.text(bar.get_x() + bar.get_width()/2, ypos,
                 f'{val:+.4f}%', ha='center', va='bottom', fontsize=8,
                 color='#e6edf3')
    ax5.set_xticks(x_ph)
    ax5.set_xticklabels(ph_labels)
    ax5.set_title('Irms Deviation from Configured (%)')
    ax5.set_ylabel('Error (%)')
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3, axis='y')

    # ── Plot 6: Unbalance summary ─────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')

    summary_lines = [
        ('VOLTAGE RMS SUMMARY', None),
        ('', None),
        *[(f'  {["Ph A","Ph B","Ph C"][ph]}: {r["vrms"][ph]:.4f} V  '
           f'({r["vrms_err_pct"][ph]:+.4f}%)',
           PHASE_COLORS[ph]) for ph in range(3)],
        ('', None),
        ('LINE-TO-LINE', None),
        ('', None),
        *[(f'  {lbl}: {r["vll"][i]:.4f} V',
           '#c084fc') for i, lbl in enumerate(vll_labels)],
        ('', None),
        ('CURRENT RMS SUMMARY', None),
        ('', None),
        *[(f'  {["Ph A","Ph B","Ph C"][ph]}: {r["irms"][ph]:.4f} A  '
           f'({r["irms_err_pct"][ph]:+.4f}%)',
           PHASE_COLORS[ph]) for ph in range(3)],
        ('', None),
        ('UNBALANCE (NEMA MG1)', None),
        ('', None),
        (f'  V unbalance: {r["v_unbalance_pct"]:.4f}%', '#e6edf3'),
        (f'  I unbalance: {r["i_unbalance_pct"]:.4f}%', '#e6edf3'),
    ]

    y = 0.97
    for line, color in summary_lines:
        c = color if color else '#8b949e'
        weight = 'bold' if line and not line.startswith(' ') else 'normal'
        ax6.text(0.05, y, line, transform=ax6.transAxes,
                 fontsize=8.5, color=c, fontweight=weight,
                 verticalalignment='top', fontfamily='monospace')
        y -= 0.055

    ax6.set_title('RMS Summary')

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

    results_rms = compute_rms(v_recon, i_recon)
    plot_rms(results_rms, save_path=str(OUTPUT_DIR / "m02_rms.png"))
