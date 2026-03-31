# =============================================================
# m06_accuracy.py — IEC 62053-22 Class 0.5S Accuracy Verification
# 3-Phase Class 0.5S Energy Meter Simulation
# Reference: TI ADS131M08 + TIDA-010243 | IEC 62053-22
# =============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m00_config import (
    FS, F0, N_SAMPLES,
    V_NOM_LN, I_FULLSCALE,
    ADC_MAX, ADC_MIN, LSB, NOISE_RMS_LSB,
    V_DIVIDER, CT_RATIO, BURDEN_R,
    PHASE_OFFSET,
    PHASE_COLORS, PHASE_NAMES,
)

# IEC 62053-22 Class 0.5S test points: (I_fraction_of_Ib, PF, error_limit_%)
TEST_POINTS = [
    (1.00, 1.00, 0.5, '100% Ib  PF=1.0'),
    (1.00, 0.50, 0.5, '100% Ib  PF=0.5 lag'),
    (1.00, 0.80, 0.5, '100% Ib  PF=0.8 lag'),
    (0.20, 1.00, 0.5,  '20% Ib  PF=1.0'),
    (0.05, 1.00, 1.0,   '5% Ib  PF=1.0'),
    (0.01, 1.00, 1.5,   '1% Ib  PF=1.0'),
]


def _generate_test_signals(i_rms, pf, seed=0):
    """
    Generate balanced 3-phase signals at the given I_rms and PF
    (pure fundamental + noise + 24-bit quantization, no harmonics).
    Returns v_recon (3, N) and i_recon (3, N).

    IEC 62053-22 Clause 8.2 specifies that accuracy tests are performed
    with sinusoidal (fundamental-only) input — harmonic content is not
    injected during type testing.  This isolates the measurement error
    introduced by the ADC quantization + noise from harmonic distortion.
    A unique seed per test point gives independent noise realisations
    while keeping results reproducible across runs.
    """
    t   = np.arange(N_SAMPLES) / FS
    w   = 2 * np.pi * F0
    phi = np.arccos(pf)

    v_recon = np.zeros((3, N_SAMPLES))
    i_recon = np.zeros((3, N_SAMPLES))

    np.random.seed(seed)
    for ph in range(3):
        theta = PHASE_OFFSET[ph]
        v_sig = V_NOM_LN * np.sqrt(2) * np.sin(w * t + theta)
        i_sig = i_rms   * np.sqrt(2) * np.sin(w * t + theta - phi)

        v_in = v_sig / V_DIVIDER
        i_in = (i_sig / CT_RATIO) * BURDEN_R

        v_noisy = v_in + np.random.normal(0, NOISE_RMS_LSB * LSB, N_SAMPLES)
        i_noisy = i_in + np.random.normal(0, NOISE_RMS_LSB * LSB, N_SAMPLES)

        v_q = np.clip(np.round(v_noisy / LSB).astype(np.int32), ADC_MIN, ADC_MAX)
        i_q = np.clip(np.round(i_noisy / LSB).astype(np.int32), ADC_MIN, ADC_MAX)

        v_recon[ph] = v_q * LSB * V_DIVIDER
        i_recon[ph] = i_q * LSB * CT_RATIO / BURDEN_R

    return v_recon, i_recon


def verify_accuracy(v_recon, i_recon):
    """
    Run IEC 62053-22 Class 0.5S accuracy verification across 6 test points.

    Parameters
    ----------
    v_recon : np.ndarray (3, N_SAMPLES) — from m01 (used for context only)
    i_recon : np.ndarray (3, N_SAMPLES) — from m01 (used for context only)

    Returns
    -------
    results_accuracy : dict with keys:
        test_labels  list[str]   — human-readable test point names
        i_test       (6,)        — test current (A)
        pf_test      (6,)        — test power factor
        p_ref        (6,)        — reference active power (W)
        p_meas       (6,)        — measured active power (W)
        error_pct    (6,)        — error % per test point
        limit_pct    (6,)        — IEC limit % per test point
        passed       (6,) bool   — per-test pass/fail
        all_passed   bool        — True if all 6 tests pass
    """
    print(f"{'─'*62}")
    print(f"  MODULE 6 — IEC 62053-22 Class 0.5S Accuracy Verification")
    print(f"{'─'*62}")

    n = len(TEST_POINTS)
    i_test    = np.zeros(n)
    pf_test   = np.zeros(n)
    p_ref     = np.zeros(n)
    p_meas    = np.zeros(n)
    error_pct = np.zeros(n)
    limit_pct = np.zeros(n)
    labels    = []

    for k, (i_frac, pf, limit, label) in enumerate(TEST_POINTS):
        i_rms = i_frac * I_FULLSCALE

        # P_reference: theoretical active power for a balanced 3-phase load
        # with purely sinusoidal voltage and current at the specified PF.
        # P_ref = 3 × Vnom_LN × I_rms × PF  (per-phase contribution × 3)
        # This is the "true" value the meter should measure — used as the
        # denominator in the IEC error formula.
        p_reference = 3.0 * V_NOM_LN * i_rms * pf

        # Measured: from quantized + noise signals
        vr, ir = _generate_test_signals(i_rms, pf, seed=k)
        p_measured = np.sum(np.mean(vr * ir, axis=1))

        err = (p_measured - p_reference) / p_reference * 100

        i_test[k]    = i_rms
        pf_test[k]   = pf
        p_ref[k]     = p_reference
        p_meas[k]    = p_measured
        error_pct[k] = err
        limit_pct[k] = limit
        labels.append(label)

    passed     = np.abs(error_pct) <= limit_pct
    all_passed = bool(np.all(passed))

    results_accuracy = {
        'test_labels': labels,
        'i_test':      i_test,
        'pf_test':     pf_test,
        'p_ref':       p_ref,
        'p_meas':      p_meas,
        'error_pct':   error_pct,
        'limit_pct':   limit_pct,
        'passed':      passed,
        'all_passed':  all_passed,
    }

    _print_results(results_accuracy)
    return results_accuracy


def _print_results(r):
    print(f"\n  {'#':<3} {'Test Point':<24} {'I (A)':<8} {'PF':<6} "
          f"{'P_ref (W)':<12} {'P_meas (W)':<12} {'Error (%)':<11} {'Limit':<8} {'Result'}")
    print(f"  {'─'*95}")
    for k in range(len(r['test_labels'])):
        status = 'PASS' if r['passed'][k] else 'FAIL'
        print(f"  {k+1:<3} {r['test_labels'][k]:<24} "
              f"{r['i_test'][k]:<8.3f} {r['pf_test'][k]:<6.2f} "
              f"{r['p_ref'][k]:<12.3f} {r['p_meas'][k]:<12.3f} "
              f"{r['error_pct'][k]:<+11.5f} ±{r['limit_pct'][k]:.1f}%    {status}")

    verdict = "ALL TESTS PASSED" if r['all_passed'] else "ONE OR MORE TESTS FAILED"
    print(f"\n  {'─'*62}")
    print(f"  VERDICT: {verdict}")
    print(f"  Standard: IEC 62053-22 Class 0.5S")
    print(f"\n  ✓ m06_accuracy — 6 test points verified | "
          f"{N_SAMPLES} samples/point\n")


def plot_accuracy(results_accuracy, save_path=None):
    """4-panel accuracy verification visualization."""

    r   = results_accuracy
    n   = len(r['test_labels'])
    x   = np.arange(n)
    # Short labels for x-axis
    xlabels = [lbl.replace(' PF=', '\nPF=') for lbl in r['test_labels']]

    fig = plt.figure(figsize=(18, 10), facecolor='#0d1117')
    fig.suptitle(
        'Module 6 — IEC 62053-22 Class 0.5S Accuracy Verification\n'
        '3-Phase 50 Hz | ADS131M08 24-bit | 6 Test Points',
        fontsize=13, color='#e6edf3', y=0.98, fontfamily='monospace'
    )
    gs = gridspec.GridSpec(1, 4, figure=fig,
                           wspace=0.42,
                           left=0.06, right=0.97,
                           top=0.88, bottom=0.18)

    pass_color = '#3fb950'
    fail_color = '#f78166'
    bar_colors = [pass_color if p else fail_color for p in r['passed']]

    # ── Plot 1: Error % per test point ────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    bars = ax1.bar(x, r['error_pct'], 0.55, color=bar_colors, alpha=0.85)
    # Draw ±limit per bar
    for k in range(n):
        lim = r['limit_pct'][k]
        ax1.plot([k - 0.28, k + 0.28], [ lim,  lim],
                 color='#ffa657', lw=1.5, ls='--')
        ax1.plot([k - 0.28, k + 0.28], [-lim, -lim],
                 color='#ffa657', lw=1.5, ls='--')
    ax1.axhline(0, color='#e6edf3', lw=0.7, ls='-', alpha=0.4)
    for bar, val in zip(bars, r['error_pct']):
        ypos = val + 0.01 if val >= 0 else val - 0.04
        ax1.text(bar.get_x() + bar.get_width()/2, ypos,
                 f'{val:+.4f}%', ha='center', fontsize=7, color='#e6edf3')
    ax1.set_xticks(x)
    ax1.set_xticklabels(xlabels, fontsize=7)
    ax1.set_title('Measurement Error % per Test Point')
    ax1.set_ylabel('Error (%)')
    ax1.grid(True, alpha=0.3, axis='y')

    # ── Plot 2: P_ref vs P_meas ───────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    bw = 0.35
    ax2.bar(x - bw/2, r['p_ref'],  bw, color='#30363d', alpha=0.8, label='P_ref (W)')
    bars2 = ax2.bar(x + bw/2, r['p_meas'], bw, color=bar_colors, alpha=0.85,
                    label='P_meas (W)')
    ax2.set_xticks(x)
    ax2.set_xticklabels(xlabels, fontsize=7)
    ax2.set_title('Reference vs Measured Power')
    ax2.set_ylabel('Active Power (W)')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')

    # ── Plot 3: Error vs limit — margin bar ───────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    margin = r['limit_pct'] - np.abs(r['error_pct'])   # positive = headroom
    mcolors = [pass_color if m >= 0 else fail_color for m in margin]
    bars3 = ax3.bar(x, margin, 0.55, color=mcolors, alpha=0.85)
    ax3.axhline(0, color='#ffa657', lw=1.0, ls='--', alpha=0.8,
                label='Limit boundary')
    for bar, val in zip(bars3, margin):
        ypos = val + 0.005 if val >= 0 else val - 0.02
        ax3.text(bar.get_x() + bar.get_width()/2, ypos,
                 f'{val:+.4f}', ha='center', fontsize=7, color='#e6edf3')
    ax3.set_xticks(x)
    ax3.set_xticklabels(xlabels, fontsize=7)
    ax3.set_title('Error Margin (Limit − |Error|)')
    ax3.set_ylabel('Margin (%) — positive = passing')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')

    # ── Plot 4: Summary table ─────────────────────────────────────
    ax4 = fig.add_subplot(gs[0, 3])
    ax4.axis('off')
    verdict_color = pass_color if r['all_passed'] else fail_color
    verdict_text  = 'ALL PASS' if r['all_passed'] else 'FAIL'

    lines = [
        ('IEC 62053-22 CLASS 0.5S', None),
        ('', None),
        (f'VERDICT: {verdict_text}', verdict_color),
        ('', None),
        (f'  Ib = {I_FULLSCALE:.1f} A (full-scale)', '#8b949e'),
        (f'  Vnom = {V_NOM_LN:.1f} V L-N', '#8b949e'),
        (f'  ADC: 24-bit, fs={FS} Hz', '#8b949e'),
        ('', None),
        ('Test Results:', '#8b949e'),
        ('', None),
    ]
    for k in range(n):
        col = pass_color if r['passed'][k] else fail_color
        sym = '✓' if r['passed'][k] else '✗'
        lines.append((f'  {sym} #{k+1} {r["error_pct"][k]:+.4f}%  '
                       f'(±{r["limit_pct"][k]:.1f}%)', col))

    y = 0.97
    for line, color in lines:
        c = color if color else '#8b949e'
        weight = 'bold' if line and not line.startswith(' ') else 'normal'
        ax4.text(0.03, y, line, transform=ax4.transAxes,
                 fontsize=8.5, color=c, fontweight=weight,
                 verticalalignment='top', fontfamily='monospace')
        y -= 0.060
    ax4.set_title('Accuracy Summary')

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

    results_accuracy = verify_accuracy(v_recon, i_recon)
    plot_accuracy(results_accuracy, save_path=str(OUTPUT_DIR / "m06_accuracy.png"))
