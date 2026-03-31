# =============================================================
# m07_dashboard.py — Full System Dashboard
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
    FS, F0, N_SAMPLES, N_CYCLES,
    V_NOM_LN, I_RMS, I_FULLSCALE,
    PF_LAG,
    PHASE_COLORS, PHASE_NAMES,
)


def plot_dashboard(t, v_recon, i_recon,
                   results_rms, results_power,
                   results_harmonics, results_energy,
                   results_accuracy,
                   save_path=None):
    """
    12-panel full system dashboard combining all module outputs.

    Parameters
    ----------
    t                 : (N_SAMPLES,)    time vector (s)
    v_recon           : (3, N_SAMPLES)  reconstructed voltage (V)
    i_recon           : (3, N_SAMPLES)  reconstructed current (A)
    results_rms       : dict — from m02_rms.compute_rms()
    results_power     : dict — from m03_power.compute_power()
    results_harmonics : dict — from m04_harmonics.compute_harmonics()
    results_energy    : dict — from m05_energy.compute_energy()
    results_accuracy  : dict — from m06_accuracy.verify_accuracy()
    save_path         : str or None
    """
    print(f"{'─'*62}")
    print(f"  MODULE 7 — Full System Dashboard")
    print(f"{'─'*62}")

    fig = plt.figure(figsize=(22, 16), facecolor='#0d1117')
    fig.suptitle(
        '3-Phase Class 0.5S Energy Meter — System Dashboard\n'
        'ADS131M08 24-bit Δ-Σ | IEC 62053-22 | fs=8 kHz | 10-Cycle Window',
        fontsize=13, color='#e6edf3', y=0.99, fontfamily='monospace'
    )
    gs = gridspec.GridSpec(3, 4, figure=fig,
                           hspace=0.52, wspace=0.42,
                           left=0.05, right=0.97,
                           top=0.93, bottom=0.06)

    ph_labels = ['Ph A', 'Ph B', 'Ph C']
    x3  = np.arange(3)
    bw  = 0.35
    bw3 = 0.25
    show = 2 * (FS // F0)
    t_ms = t[:show] * 1000

    # ── [0,0] Voltage waveforms ───────────────────────────────────
    ax = fig.add_subplot(gs[0, 0])
    for ph in range(3):
        ax.plot(t_ms, v_recon[ph, :show],
                color=PHASE_COLORS[ph], lw=1.0, label=PHASE_NAMES[ph])
    ax.axhline(0, color='#30363d', lw=0.6)
    ax.set_title('Voltage Waveforms (2 cycles)')
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Voltage (V)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # ── [0,1] Current waveforms ───────────────────────────────────
    ax = fig.add_subplot(gs[0, 1])
    for ph in range(3):
        ax.plot(t_ms, i_recon[ph, :show],
                color=PHASE_COLORS[ph], lw=1.0, label=PHASE_NAMES[ph])
    ax.axhline(0, color='#30363d', lw=0.6)
    ax.set_title('Current Waveforms (2 cycles)')
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Current (A)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # ── [0,2] Vrms & Irms (% of nominal) ─────────────────────────
    ax = fig.add_subplot(gs[0, 2])
    ax.bar(x3 - bw/2, results_rms['vrms'] / V_NOM_LN * 100, bw,
           color=PHASE_COLORS, alpha=0.85, label='Vrms (% nom)')
    ax.bar(x3 + bw/2, results_rms['irms'] / np.array(I_RMS) * 100, bw,
           color=PHASE_COLORS, alpha=0.45, label='Irms (% cfg)', hatch='//')
    ax.axhline(100, color='#ffa657', lw=0.8, ls='--', alpha=0.6)
    ax.set_xticks(x3)
    ax.set_xticklabels(ph_labels)
    ax.set_title('Vrms & Irms (% of nominal)')
    ax.set_ylabel('%')
    ax.set_ylim(0, 115)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3, axis='y')

    # ── [0,3] Power factor ────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 3])
    ax.bar(x3 - bw/2, results_power['pf'], bw,
           color=PHASE_COLORS, alpha=0.85, label='Measured PF')
    ax.bar(x3 + bw/2, PF_LAG, bw,
           color='#30363d', alpha=0.7, label='Configured PF')
    for i, val in enumerate(results_power['pf']):
        ax.text(x3[i] - bw/2, val + 0.005, f'{val:.4f}',
                ha='center', fontsize=7, color='#e6edf3')
    ax.set_xticks(x3)
    ax.set_xticklabels(ph_labels)
    ax.set_title('Power Factor — Measured vs Configured')
    ax.set_ylabel('PF')
    ax.set_ylim(0, 1.12)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3, axis='y')

    # ── [1,0] Per-phase P / Q / S ─────────────────────────────────
    ax = fig.add_subplot(gs[1, 0])
    ax.bar(x3 - bw3, results_power['p'], bw3,
           color=PHASE_COLORS, alpha=0.90, label='P (W)')
    ax.bar(x3,       results_power['q'], bw3,
           color=PHASE_COLORS, alpha=0.55, label='Q (VAR)', hatch='//')
    ax.bar(x3 + bw3, results_power['s'], bw3,
           color=PHASE_COLORS, alpha=0.30, label='S (VA)',  hatch='xx')
    ax.set_xticks(x3)
    ax.set_xticklabels(ph_labels)
    ax.set_title('Per-Phase P / Q / S')
    ax.set_ylabel('Power (W / VAR / VA)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3, axis='y')

    # ── [1,1] 3-phase totals ──────────────────────────────────────
    ax = fig.add_subplot(gs[1, 1])
    totals = [results_power['p_total'],
              results_power['q_total'],
              results_power['s_total']]
    tot_colors = ['#58a6ff', '#ffa657', '#3fb950']
    tot_labels = [f"P\n{totals[0]:.1f}W",
                  f"Q\n{totals[1]:.1f}VAR",
                  f"S\n{totals[2]:.1f}VA"]
    bars = ax.bar([0, 1, 2], totals, 0.5, color=tot_colors, alpha=0.85)
    for bar, val in zip(bars, totals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                f'{val:.1f}', ha='center', fontsize=7.5, color='#e6edf3')
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(tot_labels, fontsize=8.5)
    ax.set_title(f'3-Phase Totals  |  PF = {results_power["pf_total"]:.4f}')
    ax.set_ylabel('Power (W / VAR / VA)')
    ax.grid(True, alpha=0.3, axis='y')

    # ── [1,2] THD per phase ───────────────────────────────────────
    ax = fig.add_subplot(gs[1, 2])
    ax.bar(x3 - bw/2, results_harmonics['thd_v'], bw,
           color=PHASE_COLORS, alpha=0.85, label='THD_V (%)')
    ax.bar(x3 + bw/2, results_harmonics['thd_i'], bw,
           color=PHASE_COLORS, alpha=0.45, label='THD_I (%)', hatch='//')
    for i in range(3):
        ax.text(x3[i] - bw/2, results_harmonics['thd_v'][i] + 0.05,
                f"{results_harmonics['thd_v'][i]:.2f}",
                ha='center', fontsize=7, color='#e6edf3')
        ax.text(x3[i] + bw/2, results_harmonics['thd_i'][i] + 0.05,
                f"{results_harmonics['thd_i'][i]:.2f}",
                ha='center', fontsize=7, color='#e6edf3')
    ax.set_xticks(x3)
    ax.set_xticklabels(ph_labels)
    ax.set_title('THD — Voltage & Current (%)')
    ax.set_ylabel('THD (%)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3, axis='y')

    # ── [1,3] Voltage spectrum (all phases) ───────────────────────
    ax = fig.add_subplot(gs[1, 3])
    for ph in range(3):
        ax.plot(results_harmonics['freqs'], results_harmonics['v_mag'][ph],
                color=PHASE_COLORS[ph], lw=0.8, alpha=0.85, label=ph_labels[ph])
    ax.set_xlim(0, 700)
    ax.set_title('Voltage Spectrum (Hanning FFT)')
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Magnitude (V)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # ── [2,0] IEC accuracy error % ────────────────────────────────
    ax = fig.add_subplot(gs[2, 0])
    n_tp = len(results_accuracy['test_labels'])
    x_tp = np.arange(n_tp)
    pass_c = '#3fb950'
    fail_c = '#f78166'
    bcolors = [pass_c if p else fail_c for p in results_accuracy['passed']]
    ax.bar(x_tp, results_accuracy['error_pct'], 0.55,
           color=bcolors, alpha=0.85)
    for k in range(n_tp):
        lim = results_accuracy['limit_pct'][k]
        ax.plot([k - 0.28, k + 0.28], [ lim,  lim],
                color='#ffa657', lw=1.2, ls='--')
        ax.plot([k - 0.28, k + 0.28], [-lim, -lim],
                color='#ffa657', lw=1.2, ls='--')
    ax.axhline(0, color='#e6edf3', lw=0.6, alpha=0.4)
    xlbls = [lbl.replace(' PF=', '\nPF=')
             for lbl in results_accuracy['test_labels']]
    ax.set_xticks(x_tp)
    ax.set_xticklabels(xlbls, fontsize=6.5)
    ax.set_title('IEC 62053-22 Class 0.5S — Error %')
    ax.set_ylabel('Error (%)')
    ax.grid(True, alpha=0.3, axis='y')

    # ── [2,1] Energy rates ────────────────────────────────────────
    ax = fig.add_subplot(gs[2, 1])
    e_vals = [results_energy['kwh_hr'],
              results_energy['kvarh_hr'],
              results_energy['kvah_hr']]
    e_cols = ['#58a6ff', '#ffa657', '#3fb950']
    e_lbls = [f"kWh/hr\n{e_vals[0]:.4f}",
              f"kVARh/hr\n{e_vals[1]:.4f}",
              f"kVAh/hr\n{e_vals[2]:.4f}"]
    bars = ax.bar([0, 1, 2], e_vals, 0.5, color=e_cols, alpha=0.85)
    for bar, val in zip(bars, e_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01,
                f'{val:.4f}', ha='center', fontsize=7.5, color='#e6edf3')
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(e_lbls, fontsize=8.5)
    ax.set_title(f'Energy Rates  ({results_energy["kwh_day"]:.3f} kWh/day)')
    ax.set_ylabel('kWh/hr | kVARh/hr | kVAh/hr')
    ax.grid(True, alpha=0.3, axis='y')

    # ── [2,2] Unbalance ───────────────────────────────────────────
    ax = fig.add_subplot(gs[2, 2])
    u_vals = [results_rms['v_unbalance_pct'],
              results_rms['i_unbalance_pct']]
    u_bars = ax.bar(['V unbalance', 'I unbalance'], u_vals, 0.45,
                    color=['#58a6ff', '#3fb950'], alpha=0.85)
    ax.axhline(2.0, color='#f78166', lw=0.8, ls='--',
               alpha=0.7, label='2% typical limit')
    for bar, val in zip(u_bars, u_vals):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.02,
                f'{val:.3f}%', ha='center', fontsize=9, color='#e6edf3')
    ax.set_title('NEMA MG1 Unbalance')
    ax.set_ylabel('Unbalance (%)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3, axis='y')

    # ── [2,3] System summary text ─────────────────────────────────
    ax = fig.add_subplot(gs[2, 3])
    ax.axis('off')
    verdict_col  = '#3fb950' if results_accuracy['all_passed'] else '#f78166'
    verdict_text = 'CLASS 0.5S : PASS' if results_accuracy['all_passed'] \
                   else 'CLASS 0.5S : FAIL'
    win_ms = results_energy['t_hours'] * 3600 * 1000

    lines = [
        ('SYSTEM SUMMARY', None),
        ('', None),
        (verdict_text, verdict_col),
        ('', None),
        ('Signal Chain:', '#8b949e'),
        (f'  fs={FS} Hz | {N_CYCLES}-cycle | {N_SAMPLES} smp', '#e6edf3'),
        (f'  24-bit ADC | Vnom={V_NOM_LN} V L-N', '#e6edf3'),
        ('', None),
        ('3-Phase Power:', '#8b949e'),
        (f'  P  = {results_power["p_total"]:>9.2f} W',   '#58a6ff'),
        (f'  Q  = {results_power["q_total"]:>9.2f} VAR', '#ffa657'),
        (f'  S  = {results_power["s_total"]:>9.2f} VA',  '#3fb950'),
        (f'  PF = {results_power["pf_total"]:>9.4f}',    '#e6edf3'),
        ('', None),
        ('Energy:', '#8b949e'),
        (f'  {results_energy["kwh_hr"]:.4f} kWh/hr', '#58a6ff'),
        (f'  {results_energy["kwh_day"]:.4f} kWh/day', '#58a6ff'),
        ('', None),
        ('Unbalance:', '#8b949e'),
        (f'  V: {results_rms["v_unbalance_pct"]:.3f}%  '
         f'I: {results_rms["i_unbalance_pct"]:.3f}%', '#e6edf3'),
        ('', None),
        ('THD (avg):', '#8b949e'),
        (f'  V: {np.mean(results_harmonics["thd_v"]):.2f}%  '
         f'I: {np.mean(results_harmonics["thd_i"]):.2f}%', '#e6edf3'),
    ]
    y = 0.97
    for line, color in lines:
        c = color if color else '#8b949e'
        weight = 'bold' if line and not line.startswith(' ') else 'normal'
        ax.text(0.03, y, line, transform=ax.transAxes,
                fontsize=8.5, color=c, fontweight=weight,
                verticalalignment='top', fontfamily='monospace')
        y -= 0.048
    ax.set_title('System Summary')

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight',
                    facecolor='#0d1117')
        print(f"  Plot saved: {save_path}")
    print(f"  ✓ m07_dashboard — 12-panel dashboard generated\n")
    plt.show()


if __name__ == "__main__":
    import pathlib
    REPO_ROOT  = pathlib.Path(__file__).resolve().parent.parent
    OUTPUT_DIR = REPO_ROOT / "outputs"
    OUTPUT_DIR.mkdir(exist_ok=True)

    from m01_signal_gen import generate_signals
    from m02_rms        import compute_rms
    from m03_power      import compute_power
    from m04_harmonics  import compute_harmonics
    from m05_energy     import compute_energy
    from m06_accuracy   import verify_accuracy

    t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon = generate_signals()
    results_rms       = compute_rms(v_recon, i_recon)
    results_power     = compute_power(v_recon, i_recon)
    results_harmonics = compute_harmonics(v_recon, i_recon)
    results_energy    = compute_energy(results_power)
    results_accuracy  = verify_accuracy(v_recon, i_recon)

    plot_dashboard(
        t, v_recon, i_recon,
        results_rms, results_power,
        results_harmonics, results_energy,
        results_accuracy,
        save_path=str(OUTPUT_DIR / "m07_dashboard.png")
    )
