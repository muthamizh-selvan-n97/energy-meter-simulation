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
# from m02_rms import compute_rms, plot_rms
# from m03_power import compute_power, plot_power
# from m04_harmonics import compute_harmonics, plot_harmonics
# from m05_energy import compute_energy
# from m06_accuracy import verify_accuracy, plot_accuracy
# from m07_dashboard import plot_dashboard
# from m08_modbus import print_modbus_map