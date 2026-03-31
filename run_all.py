# =============================================================
# run_all.py — Run all modules from repo root
# Usage: python run_all.py
# Works from: VS Code, terminal, any working directory
# =============================================================

import sys
import pathlib

# ── Resolve paths robustly regardless of working directory ────
REPO_ROOT  = pathlib.Path(__file__).resolve().parent
MODULES    = REPO_ROOT / "modules"
OUTPUT_DIR = REPO_ROOT / "outputs"

sys.path.insert(0, str(MODULES))
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Module 0 — Configuration ──────────────────────────────────
from m00_config import print_config
print_config()

# ── Module 1 — Signal Generation + Quantization ───────────────
from m01_signal_gen import generate_signals, plot_signals

t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon = generate_signals()
plot_signals(
    t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon,
    save_path=str(OUTPUT_DIR / "m01_signal_gen.png")
)

# ── Module 2 onwards — uncomment as each module is added ──────
from m02_rms import compute_rms, plot_rms
results_rms = compute_rms(v_recon, i_recon)
plot_rms(results_rms, save_path=str(OUTPUT_DIR / "m02_rms.png"))

from m03_power import compute_power, plot_power
results_power = compute_power(v_recon, i_recon)
plot_power(results_power, save_path=str(OUTPUT_DIR / "m03_power.png"))

from m04_harmonics import compute_harmonics, plot_harmonics
results_harmonics = compute_harmonics(v_recon, i_recon)
plot_harmonics(results_harmonics, save_path=str(OUTPUT_DIR / "m04_harmonics.png"))

from m05_energy import compute_energy, plot_energy
results_energy = compute_energy(results_power)
plot_energy(results_energy, save_path=str(OUTPUT_DIR / "m05_energy.png"))

from m06_accuracy import verify_accuracy, plot_accuracy
results_accuracy = verify_accuracy(v_recon, i_recon)
plot_accuracy(results_accuracy, save_path=str(OUTPUT_DIR / "m06_accuracy.png"))

from m07_dashboard import plot_dashboard
plot_dashboard(
    t, v_recon, i_recon,
    results_rms, results_power,
    results_harmonics, results_energy,
    results_accuracy,
    save_path=str(OUTPUT_DIR / "m07_dashboard.png")
)
from m08_modbus import print_modbus_map
print_modbus_map(results_rms, results_power, results_harmonics,
                 results_energy, results_accuracy)