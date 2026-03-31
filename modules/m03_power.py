# =============================================================
# m03_power.py — Active, Reactive, Apparent Power & PF
# 3-Phase Class 0.5S Energy Meter Simulation
# Reference: TI ADS131M08 + TIDA-010243 | IEC 62053-22
# =============================================================
#
# Computes per-phase P, Q, S, PF and 3-phase totals from
# reconstructed ADC signals using true power method.
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m00_config import (
    N_SAMPLES,
    I_RMS, PF_LAG,
    PHASE_COLORS, PHASE_NAMES,
)


def compute_power(v_recon, i_recon):
    """
    Compute per-phase and total active, reactive, apparent power and PF.

    Parameters
    ----------
    v_recon : np.ndarray (3, N_SAMPLES) — reconstructed voltage (V)
    i_recon : np.ndarray (3, N_SAMPLES) — reconstructed current (A)

    Returns
    -------
    results_power : dict with keys:
        p        (3,)  — per-phase active power (W)
        q        (3,)  — per-phase reactive power (VAR)
        s        (3,)  — per-phase apparent power (VA)
        pf       (3,)  — per-phase true power factor
        vrms     (3,)  — per-phase Vrms (V)   [for m05, m06 convenience]
        irms     (3,)  — per-phase Irms (A)
        p_total  float — total active power (W)
        q_total  float — total reactive power (VAR)
        s_total  float — total apparent power (VA)
        pf_total float — system power factor
    """
    print(f"{'─'*62}")
    print(f"  MODULE 3 — Active / Reactive / Apparent Power & PF")
    print(f"{'─'*62}")

    # ── RMS (needed for S) ────────────────────────────────────
    vrms = np.sqrt(np.mean(v_recon ** 2, axis=1))   # (3,)
    irms = np.sqrt(np.mean(i_recon ** 2, axis=1))   # (3,)

    # ── Per-phase power ───────────────────────────────────────
    # P = mean(v·i) over the full integration window — this is the
    # exact definition of active power for any waveform (including
    # non-sinusoidal / harmonic-distorted signals).
    p = np.mean(v_recon * i_recon, axis=1)          # true active power (W)
    s = vrms * irms                                  # apparent power (VA)

    # Q = sqrt(S²-P²): the "IEEE Std 1459" single-phase definition.
    # np.maximum(..., 0.0) guards against tiny negative values caused
    # by floating-point rounding when PF ≈ 1 (S ≈ P), which would make
    # the sqrt argument marginally negative without this clamp.
    q = np.sqrt(np.maximum(s**2 - p**2, 0.0))       # reactive power (VAR)
    pf = p / s                                       # true power factor

    # ── 3-phase totals ────────────────────────────────────────
    p_total  = np.sum(p)
    q_total  = np.sum(q)
    # S_total is NOT the sum of per-phase S — it is the Pythagorean
    # combination of total P and total Q.  Summing S directly would
    # ignore phase relationships and over-estimate apparent power.
    s_total  = np.sqrt(p_total**2 + q_total**2)
    pf_total = p_total / s_total

    results_power = {
        'p':        p,
        'q':        q,
        's':        s,
        'pf':       pf,
        'vrms':     vrms,
        'irms':     irms,
        'p_total':  p_total,
        'q_total':  q_total,
        's_total':  s_total,
        'pf_total': pf_total,
    }

    _print_results(results_power)
    return results_power


def _print_results(r):
    ph_labels = ['A (R)', 'B (Y)', 'C (B)']

    print(f"\n  {'Phase':<12} {'P (W)':<12} {'Q (VAR)':<12} "
          f"{'S (VA)':<12} {'PF':<10} {'PF cfg'}")
    print(f"  {'─'*65}")
    for ph in range(3):
        print(f"  {ph_labels[ph]:<12} {r['p'][ph]:<12.3f} {r['q'][ph]:<12.3f} "
              f"{r['s'][ph]:<12.3f} {r['pf'][ph]:<10.5f} {PF_LAG[ph]:.2f}")

    print(f"\n  3-PHASE TOTALS")
    print(f"  {'─'*65}")
    print(f"  P total  = {r['p_total']:>10.3f} W")
    print(f"  Q total  = {r['q_total']:>10.3f} VAR")
    print(f"  S total  = {r['s_total']:>10.3f} VA")
    print(f"  PF total = {r['pf_total']:>10.5f}")
    print(f"\n  ✓ m03_power — P, Q, S, PF computed | "
          f"{N_SAMPLES} samples/phase\n")


def plot_power(results_power, save_path=None):
    """6-panel power results visualization."""

    r         = results_power
    ph_labels = ['Ph A', 'Ph B', 'Ph C']
    x         = np.arange(3)
    bar_w     = 0.28

    fig = plt.figure(figsize=(18, 12), facecolor='#0d1117')
    fig.suptitle(
        'Module 3 — Active / Reactive / Apparent Power & Power Factor\n'
        '3-Phase 50 Hz | ADS131M08 | fs = 8 kHz | 10-Cycle Window',
        fontsize=13, color='#e6edf3', y=0.98, fontfamily='monospace'
    )
    gs = gridspec.GridSpec(2, 3, figure=fig,
                           hspace=0.50, wspace=0.38,
                           left=0.07, right=0.97,
                           top=0.91, bottom=0.08)

    # ── Plot 1: P, Q, S grouped bar per phase ────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    bars_p = ax1.bar(x - bar_w, r['p'], bar_w,
                     color=PHASE_COLORS, alpha=0.90, label='P (W)')
    bars_q = ax1.bar(x,          r['q'], bar_w,
                     color=PHASE_COLORS, alpha=0.55, label='Q (VAR)')
    bars_s = ax1.bar(x + bar_w,  r['s'], bar_w,
                     color=PHASE_COLORS, alpha=0.30, label='S (VA)')
    for bar, val in zip(bars_p, r['p']):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                 f'{val:.0f}', ha='center', fontsize=7, color='#e6edf3')
    ax1.set_xticks(x)
    ax1.set_xticklabels(ph_labels)
    ax1.set_title('Per-Phase Power (P / Q / S)')
    ax1.set_ylabel('Power (W / VAR / VA)')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3, axis='y')

    # ── Plot 2: Power factor per phase vs configured ──────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.bar(x - bar_w/2, r['pf'], bar_w,
            color=PHASE_COLORS, alpha=0.85, label='Measured PF')
    ax2.bar(x + bar_w/2, PF_LAG, bar_w,
            color='#30363d', alpha=0.7, label='Configured PF (lag)')
    for i, (meas, cfg) in enumerate(zip(r['pf'], PF_LAG)):
        ax2.text(x[i] - bar_w/2, meas + 0.003,
                 f'{meas:.4f}', ha='center', fontsize=7.5, color='#e6edf3')
    ax2.set_xticks(x)
    ax2.set_xticklabels(ph_labels)
    ax2.set_title('Power Factor — Measured vs Configured')
    ax2.set_ylabel('Power Factor')
    ax2.set_ylim(0, 1.12)
    ax2.axhline(1.0, color='#30363d', lw=0.8, ls='--')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')

    # ── Plot 3: 3-phase total power bar ──────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    totals = [r['p_total'], r['q_total'], r['s_total']]
    colors = ['#58a6ff', '#ffa657', '#3fb950']
    labels = [f"P\n{r['p_total']:.1f} W",
              f"Q\n{r['q_total']:.1f} VAR",
              f"S\n{r['s_total']:.1f} VA"]
    bars3 = ax3.bar([0, 1, 2], totals, 0.5, color=colors, alpha=0.85)
    ax3.set_xticks([0, 1, 2])
    ax3.set_xticklabels(labels, fontsize=9)
    ax3.set_title(f'3-Phase Totals  |  PF = {r["pf_total"]:.4f}')
    ax3.set_ylabel('Power (W / VAR / VA)')
    ax3.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars3, totals):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                 f'{val:.1f}', ha='center', fontsize=8.5, color='#e6edf3')

    # ── Plot 4: P / Q breakdown as % of S per phase ──────────
    # (normalised to avoid raw-watt coordinate range issues)
    ax4 = fig.add_subplot(gs[1, 0])
    p_pct = r['p'] / r['s'] * 100   # = PF * 100
    q_pct = r['q'] / r['s'] * 100   # = sin(phi) * 100
    bars_pp = ax4.bar(x, p_pct, 0.5, color=PHASE_COLORS, alpha=0.85, label='P/S (%)')
    bars_qp = ax4.bar(x, q_pct, 0.5, bottom=p_pct,
                      color=PHASE_COLORS, alpha=0.35, label='Q/S (%)', hatch='//')
    for i in range(3):
        ax4.text(x[i], p_pct[i] / 2,
                 f'P\n{r["p"][i]:.0f}W', ha='center', fontsize=7,
                 color='#e6edf3', va='center')
        ax4.text(x[i], p_pct[i] + q_pct[i] / 2,
                 f'Q\n{r["q"][i]:.0f}', ha='center', fontsize=7,
                 color='#e6edf3', va='center')
        ax4.text(x[i], p_pct[i] + q_pct[i] + 1.5,
                 f'S={r["s"][i]:.0f}VA', ha='center', fontsize=7,
                 color='#8b949e')
    ax4.set_xticks(x)
    ax4.set_xticklabels(ph_labels)
    ax4.set_ylim(0, 115)
    ax4.set_ylabel('% of Apparent Power S')
    ax4.set_title('Power Breakdown — P & Q as % of S')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3, axis='y')

    # ── Plot 5: Loading % (S / S_rated) per phase ─────────────
    ax5 = fig.add_subplot(gs[1, 1])
    # S_rated = V_nom * I_rated per phase
    from m00_config import V_NOM_LN
    s_rated = np.array([V_NOM_LN * I_RMS[ph] for ph in range(3)])
    loading_pct = r['s'] / s_rated * 100
    bars5 = ax5.bar(x, loading_pct, 0.5, color=PHASE_COLORS, alpha=0.85)
    ax5.axhline(100, color='#f78166', lw=1.0, ls='--', alpha=0.7, label='100% rated')
    for bar, val in zip(bars5, loading_pct):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f'{val:.2f}%', ha='center', fontsize=8, color='#e6edf3')
    ax5.set_xticks(x)
    ax5.set_xticklabels(ph_labels)
    ax5.set_title('Loading % (S / S_rated per phase)')
    ax5.set_ylabel('Loading (%)')
    ax5.set_ylim(0, 120)
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3, axis='y')

    # ── Plot 6: Summary table ─────────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')
    summary_lines = [
        ('POWER SUMMARY', None),
        ('', None),
        ('Per-Phase:', '#8b949e'),
        ('', None),
        *[(f'  {["A","B","C"][ph]}: P={r["p"][ph]:.2f} W  '
           f'Q={r["q"][ph]:.2f} VAR',
           PHASE_COLORS[ph]) for ph in range(3)],
        *[(f'     S={r["s"][ph]:.2f} VA  PF={r["pf"][ph]:.4f}',
           PHASE_COLORS[ph]) for ph in range(3)],
        ('', None),
        ('3-Phase Totals:', '#8b949e'),
        ('', None),
        (f'  P total  = {r["p_total"]:>9.2f} W',    '#58a6ff'),
        (f'  Q total  = {r["q_total"]:>9.2f} VAR',  '#ffa657'),
        (f'  S total  = {r["s_total"]:>9.2f} VA',   '#3fb950'),
        (f'  PF total = {r["pf_total"]:>9.4f}',     '#e6edf3'),
    ]
    y = 0.97
    for line, color in summary_lines:
        c = color if color else '#8b949e'
        weight = 'bold' if line and not line.startswith(' ') else 'normal'
        ax6.text(0.03, y, line, transform=ax6.transAxes,
                 fontsize=8.5, color=c, fontweight=weight,
                 verticalalignment='top', fontfamily='monospace')
        y -= 0.063

    ax6.set_title('Power Summary')

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

    results_power = compute_power(v_recon, i_recon)
    plot_power(results_power, save_path=str(OUTPUT_DIR / "m03_power.png"))
