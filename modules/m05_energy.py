# =============================================================
# m05_energy.py — Energy Accumulation (kWh, kVARh, kVAh)
# 3-Phase Class 0.5S Energy Meter Simulation
# Reference: TI ADS131M08 + TIDA-010243 | IEC 62053-22
# =============================================================
#
# Computes energy consumption from the 200 ms integration window
# power results (m03_power) and projects to hourly / daily rates.
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m00_config import (
    FS, N_SAMPLES,
    PHASE_COLORS, PHASE_NAMES,
)

# Duration of one measurement window in hours.
# N_SAMPLES / FS = 1600 / 8000 = 0.200 s (200 ms per TIDA-010243 spec).
# Dividing by 3600 converts seconds → hours, the standard unit for energy
# (kWh = kW × h).  This constant is the bridge between power (W) and
# energy (Wh) for a single 10-cycle integration window.
T_HOURS = N_SAMPLES / FS / 3600          # 1600/8000/3600 ≈ 5.556e-5 h


def compute_energy(results_power):
    """
    Compute energy totals from a single 200 ms integration window.

    Parameters
    ----------
    results_power : dict — output of m03_power.compute_power()
        Must contain: p (3,), q (3,), s (3,),
                      p_total, q_total, s_total  (floats, W/VAR/VA)

    Returns
    -------
    results_energy : dict with keys:
        kwh_phase   (3,)  — per-phase active energy (kWh, window)
        kvarh_phase (3,)  — per-phase reactive energy (kVARh, window)
        kvah_phase  (3,)  — per-phase apparent energy (kVAh, window)
        kwh         float — total active energy (kWh, window)
        kvarh       float — total reactive energy (kVARh, window)
        kvah        float — total apparent energy (kVAh, window)
        kwh_hr      float — projected active energy rate (kWh/hr)
        kvarh_hr    float — projected reactive energy rate (kVARh/hr)
        kvah_hr     float — projected apparent energy rate (kVAh/hr)
        kwh_day     float — projected active energy (kWh/day)
        t_hours     float — window duration (hours)
    """
    print(f"{'─'*62}")
    print(f"  MODULE 5 — Energy Accumulation (kWh / kVARh / kVAh)")
    print(f"{'─'*62}")

    p = results_power['p']          # (3,) W
    q = results_power['q']          # (3,) VAR
    s = results_power['s']          # (3,) VA
    p_total = results_power['p_total']
    q_total = results_power['q_total']
    s_total = results_power['s_total']

    # ── Per-phase energy in this window ──────────────────────────
    kwh_phase  = p * T_HOURS / 1000.0    # W·h → kWh
    kvarh_phase = q * T_HOURS / 1000.0
    kvah_phase  = s * T_HOURS / 1000.0

    # ── 3-phase totals for this window ───────────────────────────
    kwh   = p_total * T_HOURS / 1000.0
    kvarh = q_total * T_HOURS / 1000.0
    kvah  = s_total * T_HOURS / 1000.0

    # ── Projected rates ───────────────────────────────────────────
    kwh_hr   = kwh   / T_HOURS       # kWh per hour = P_total/1000
    kvarh_hr = kvarh / T_HOURS
    kvah_hr  = kvah  / T_HOURS
    kwh_day  = kwh_hr * 24.0

    results_energy = {
        'kwh_phase':   kwh_phase,
        'kvarh_phase': kvarh_phase,
        'kvah_phase':  kvah_phase,
        'kwh':         kwh,
        'kvarh':       kvarh,
        'kvah':        kvah,
        'kwh_hr':      kwh_hr,
        'kvarh_hr':    kvarh_hr,
        'kvah_hr':     kvah_hr,
        'kwh_day':     kwh_day,
        't_hours':     T_HOURS,
    }

    _print_results(results_energy)
    return results_energy


def _print_results(r):
    ph_labels = ['A (R)', 'B (Y)', 'C (B)']
    win_ms    = r['t_hours'] * 3600 * 1000

    print(f"\n  Window duration : {win_ms:.1f} ms = {r['t_hours']:.6f} h")

    print(f"\n  PER-PHASE ENERGY  (window = {win_ms:.0f} ms)")
    print(f"  {'─'*57}")
    print(f"  {'Phase':<12} {'kWh':>12} {'kVARh':>12} {'kVAh':>12}")
    print(f"  {'─'*57}")
    for ph in range(3):
        print(f"  {ph_labels[ph]:<12} "
              f"{r['kwh_phase'][ph]:>12.6f} "
              f"{r['kvarh_phase'][ph]:>12.6f} "
              f"{r['kvah_phase'][ph]:>12.6f}")

    print(f"\n  3-PHASE TOTALS  (window = {win_ms:.0f} ms)")
    print(f"  {'─'*45}")
    print(f"  kWh   = {r['kwh']:.8f} kWh")
    print(f"  kVARh = {r['kvarh']:.8f} kVARh")
    print(f"  kVAh  = {r['kvah']:.8f} kVAh")

    print(f"\n  PROJECTED RATES")
    print(f"  {'─'*45}")
    print(f"  Active power rate   = {r['kwh_hr']:>9.4f} kWh/hr")
    print(f"  Reactive power rate = {r['kvarh_hr']:>9.4f} kVARh/hr")
    print(f"  Apparent power rate = {r['kvah_hr']:>9.4f} kVAh/hr")
    print(f"  Daily consumption   = {r['kwh_day']:>9.4f} kWh/day")
    print(f"\n  ✓ m05_energy — kWh, kVARh, kVAh computed | "
          f"window = {win_ms:.0f} ms\n")


def plot_energy(results_energy, save_path=None):
    """4-panel energy visualization."""

    r         = results_energy
    ph_labels = ['Ph A', 'Ph B', 'Ph C']
    win_ms    = r['t_hours'] * 3600 * 1000
    x         = np.arange(3)
    bw        = 0.25

    fig = plt.figure(figsize=(18, 10), facecolor='#0d1117')
    fig.suptitle(
        'Module 5 — Energy Accumulation (kWh / kVARh / kVAh)\n'
        f'3-Phase 50 Hz | ADS131M08 | Window = {win_ms:.0f} ms',
        fontsize=13, color='#e6edf3', y=0.98, fontfamily='monospace'
    )
    gs = gridspec.GridSpec(1, 4, figure=fig,
                           hspace=0.40, wspace=0.40,
                           left=0.06, right=0.97,
                           top=0.88, bottom=0.10)

    # ── Plot 1: Per-phase kWh / kVARh / kVAh (window) ────────────
    ax1 = fig.add_subplot(gs[0, 0])
    bars_w  = ax1.bar(x - bw, r['kwh_phase']  * 1e6, bw,
                      color=PHASE_COLORS, alpha=0.90, label='kWh (×10⁻⁶)')
    bars_q  = ax1.bar(x,      r['kvarh_phase'] * 1e6, bw,
                      color=PHASE_COLORS, alpha=0.55, label='kVARh (×10⁻⁶)', hatch='//')
    bars_s  = ax1.bar(x + bw, r['kvah_phase']  * 1e6, bw,
                      color=PHASE_COLORS, alpha=0.30, label='kVAh (×10⁻⁶)', hatch='xx')
    for bar, val in zip(bars_w, r['kwh_phase']):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.02,
                 f'{val*1e6:.2f}', ha='center', fontsize=7, color='#e6edf3')
    ax1.set_xticks(x)
    ax1.set_xticklabels(ph_labels)
    ax1.set_title(f'Per-Phase Energy\n(window {win_ms:.0f} ms, ×10⁻⁶ units)')
    ax1.set_ylabel('Energy (×10⁻⁶ kWh/kVARh/kVAh)')
    ax1.legend(fontsize=7.5)
    ax1.grid(True, alpha=0.3, axis='y')

    # ── Plot 2: 3-phase total kWh / kVARh / kVAh (window) ────────
    ax2 = fig.add_subplot(gs[0, 1])
    totals = [r['kwh'] * 1e6, r['kvarh'] * 1e6, r['kvah'] * 1e6]
    colors = ['#58a6ff', '#ffa657', '#3fb950']
    labels = [f"kWh\n{r['kwh']*1e6:.3f}", f"kVARh\n{r['kvarh']*1e6:.3f}",
              f"kVAh\n{r['kvah']*1e6:.3f}"]
    bars2 = ax2.bar([0, 1, 2], totals, 0.5, color=colors, alpha=0.85)
    ax2.set_xticks([0, 1, 2])
    ax2.set_xticklabels(labels, fontsize=8.5)
    ax2.set_title(f'3-Phase Totals\n(window {win_ms:.0f} ms, ×10⁻⁶ units)')
    ax2.set_ylabel('Energy (×10⁻⁶ kWh / kVARh / kVAh)')
    ax2.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars2, totals):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                 f'{val:.3f}', ha='center', fontsize=8, color='#e6edf3')

    # ── Plot 3: Projected hourly rate (kWh/hr) ────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    rates = [r['kwh_hr'], r['kvarh_hr'], r['kvah_hr']]
    rate_labels = [f"kWh/hr\n{r['kwh_hr']:.4f}",
                   f"kVARh/hr\n{r['kvarh_hr']:.4f}",
                   f"kVAh/hr\n{r['kvah_hr']:.4f}"]
    bars3 = ax3.bar([0, 1, 2], rates, 0.5, color=colors, alpha=0.85)
    ax3.set_xticks([0, 1, 2])
    ax3.set_xticklabels(rate_labels, fontsize=8.5)
    ax3.set_title('Projected Hourly Rates\n(from 200 ms window)')
    ax3.set_ylabel('Energy Rate (kWh/hr / kVARh/hr / kVAh/hr)')
    ax3.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars3, rates):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                 f'{val:.4f}', ha='center', fontsize=8, color='#e6edf3')

    # ── Plot 4: Summary text ───────────────────────────────────────
    ax4 = fig.add_subplot(gs[0, 3])
    ax4.axis('off')
    ph_lbl = ['A (R)', 'B (Y)', 'C (B)']
    lines = [
        ('ENERGY SUMMARY', None),
        ('', None),
        (f'Window: {win_ms:.1f} ms', '#8b949e'),
        ('', None),
        ('Per-Phase kWh (×10⁻⁶):', '#8b949e'),
        ('', None),
        *[(f'  Ph {ph_lbl[ph]}: {r["kwh_phase"][ph]*1e6:.4f}',
           PHASE_COLORS[ph]) for ph in range(3)],
        ('', None),
        ('Per-Phase kVARh (×10⁻⁶):', '#8b949e'),
        ('', None),
        *[(f'  Ph {ph_lbl[ph]}: {r["kvarh_phase"][ph]*1e6:.4f}',
           PHASE_COLORS[ph]) for ph in range(3)],
        ('', None),
        ('3-Phase Totals:', '#8b949e'),
        ('', None),
        (f'  kWh   = {r["kwh"]*1e6:.4f} ×10⁻⁶',   '#58a6ff'),
        (f'  kVARh = {r["kvarh"]*1e6:.4f} ×10⁻⁶',  '#ffa657'),
        (f'  kVAh  = {r["kvah"]*1e6:.4f} ×10⁻⁶',   '#3fb950'),
        ('', None),
        ('Projected:', '#8b949e'),
        ('', None),
        (f'  {r["kwh_hr"]:.4f} kWh/hr',  '#58a6ff'),
        (f'  {r["kwh_day"]:.4f} kWh/day', '#58a6ff'),
    ]
    y = 0.97
    for line, color in lines:
        c = color if color else '#8b949e'
        weight = 'bold' if line and not line.startswith(' ') else 'normal'
        ax4.text(0.03, y, line, transform=ax4.transAxes,
                 fontsize=8.5, color=c, fontweight=weight,
                 verticalalignment='top', fontfamily='monospace')
        y -= 0.052
    ax4.set_title('Energy Summary')

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
    from m03_power import compute_power

    t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon = generate_signals()
    results_power = compute_power(v_recon, i_recon)

    results_energy = compute_energy(results_power)
    plot_energy(results_energy, save_path=str(OUTPUT_DIR / "m05_energy.png"))
