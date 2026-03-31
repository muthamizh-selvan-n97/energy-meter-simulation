# CLAUDE.md — Project Guide for Claude Code

This file tells Claude Code how to work with this repository.
Read this before making any changes.

---

## Project Overview

3-phase electrical energy meter simulation modelling the complete
signal chain from analog input through delta-sigma ADC quantization
to IEC 62053-22 Class 0.5S accuracy verification.

**Architecture reference:** TI ADS131M08 (24-bit Δ-Σ ADC) + TIDA-010243  
**Standard:** IEC 62053-22 Class 0.5S  
**Grid:** 3-phase 4-wire Wye, 230V L-N, 50 Hz, India  

---

## Repo Structure

```
energy-meter-simulation/
├── CLAUDE.md                        ← you are here
├── README.md                        ← project overview for humans
├── requirements.txt                 ← pip dependencies
├── run_all.py                       ← single entry point, run from repo root
├── .vscode/
│   └── settings.json                ← VS Code workspace settings
├── modules/                         ← one .py file per simulation module
│   ├── m00_config.py                ← ALL parameters live here
│   ├── m01_signal_gen.py            ← signal generation + quantization
│   ├── m02_rms.py                   ← (next) Vrms, Irms
│   ├── m03_power.py                 ← (next) P, Q, S, PF
│   ├── m04_harmonics.py             ← (next) FFT, THD
│   ├── m05_energy.py                ← (next) kWh, kVARh, kVAh
│   ├── m06_accuracy.py              ← (next) Class 0.5S verification
│   ├── m07_dashboard.py             ← (next) full visualization
│   └── m08_modbus.py                ← (next) Modbus register map
├── notebook/
│   └── energy_meter_sim.ipynb       ← Colab notebook (mirrors modules/)
├── outputs/                         ← generated plots and CSVs (.gitignored)
│   └── .gitkeep
└── docs/
    ├── architecture.md              ← ADS131M08 signal chain reference
    └── references.md                ← TI app notes, IEC standards links
```

---

## How to Run

```bash
# From repo root — runs all implemented modules
python run_all.py

# Run individual module directly
python modules/m00_config.py
python modules/m01_signal_gen.py
```

**Never** run modules with `cd modules && python mXX.py` — path resolution
uses `pathlib.Path(__file__).resolve()` which works from any cwd.

---

## Architecture Rules — Follow These When Adding Modules

### Rule 1 — All parameters in m00_config.py only
Never hardcode values (fs, F0, V_NOM_LN, ADC_BITS, etc.) in any module.
Always import from m00_config:

```python
from m00_config import FS, F0, SPC, N_SAMPLES, V_NOM_LN, ADC_BITS, LSB, ...
```

### Rule 2 — Module structure template
Every module follows this pattern:

```python
# mXX_name.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m00_config import (...)          # import only what this module needs

def compute_something(inputs):
    """Core computation — returns dict or np.ndarray."""
    ...
    _print_results(results)
    return results

def plot_something(results, save_path=None):
    """Visualization — dark theme, PHASE_COLORS."""
    ...

def _print_results(results):
    """Console summary with ── dividers."""
    ...

if __name__ == "__main__":
    import pathlib
    REPO_ROOT  = pathlib.Path(__file__).resolve().parent.parent
    OUTPUT_DIR = REPO_ROOT / "outputs"
    OUTPUT_DIR.mkdir(exist_ok=True)

    # import and run upstream modules to get inputs
    from m01_signal_gen import generate_signals
    t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon = generate_signals()

    results = compute_something(v_recon, i_recon)
    plot_something(results, save_path=str(OUTPUT_DIR / "mXX_name.png"))
```

### Rule 3 — Module inputs and outputs

| Module | Inputs | Returns |
|--------|--------|---------|
| m00_config | — | constants (import directly) |
| m01_signal_gen | — | `t, v_actual, i_actual, v_counts, i_counts, v_recon, i_recon` |
| m02_rms | `v_recon, i_recon` | `results_rms` dict |
| m03_power | `v_recon, i_recon` | `results_power` dict |
| m04_harmonics | `v_recon, i_recon` | `results_harmonics` dict |
| m05_energy | `results_power` | `results_energy` dict |
| m06_accuracy | `v_recon, i_recon` | `results_accuracy` dict |
| m07_dashboard | all results dicts | figure (saved to outputs/) |
| m08_modbus | all results dicts | printed register map |

### Rule 4 — run_all.py is the integration file
When a new module is added, uncomment its lines in `run_all.py` and
pass the correct inputs. Do not change the function signatures.

### Rule 5 — Plot style
All plots use the dark theme defined in m00_config.py via `plt.rcParams`.
Phase colors are always: A=`#58a6ff`, B=`#3fb950`, C=`#f78166`.
Never override rcParams inside individual modules.

### Rule 6 — Notebook mirrors modules
After adding a new module `.py`, add the corresponding cell to
`notebook/energy_meter_sim.ipynb`. The notebook imports from `modules/`
via `sys.path.insert(0, "energy-meter-simulation/modules")` (Colab path).

---

## Key Constants (from m00_config.py)

| Constant | Value | Description |
|----------|-------|-------------|
| `FS` | 8000 | Sampling rate (Hz) — ADS131M08 ODR |
| `F0` | 50 | Grid frequency (Hz) |
| `SPC` | 160 | Samples per cycle |
| `N_CYCLES` | 10 | Integration window (cycles) |
| `N_SAMPLES` | 1600 | Total samples per window |
| `ADC_BITS` | 24 | ADC resolution |
| `V_REF` | 1.2 | ADC input range ±V |
| `LSB` | 143.05e-9 | LSB size (V) |
| `ADC_MAX` | 8,388,607 | Max signed 24-bit count |
| `V_NOM_LN` | 230.0 | Nominal L-N voltage (Vrms) |
| `V_DIVIDER` | 301.2 | Resistor divider ratio |
| `CT_RATIO` | 1000 | Current transformer ratio |
| `BURDEN_R` | 10.0 | CT burden resistor (Ω) |
| `I_RMS` | [15, 12, 18] | Per-phase Irms (A) — unbalanced |
| `PF_LAG` | [0.85, 0.90, 0.80] | Per-phase power factor (lag) |
| `HARMONICS` | dict | {order: (V%, I%)} — 3,5,7,11,13 |
| `PHASE_COLORS` | list | Plot colors for A, B, C |
| `PHASE_NAMES` | list | ['Phase A (R)', ...] |

---

## Signal Arrays (from m01_signal_gen.generate_signals())

All arrays shape: `(3, N_SAMPLES)` = `(3, 1600)`

| Variable | Unit | Description |
|----------|------|-------------|
| `t` | s | Time vector, shape `(N_SAMPLES,)` |
| `v_actual` | V | Actual voltage before ADC (with harmonics) |
| `i_actual` | A | Actual current before ADC (with harmonics) |
| `v_counts` | int32 | Raw 24-bit ADC counts — voltage channel |
| `i_counts` | int32 | Raw 24-bit ADC counts — current channel |
| `v_recon` | V | Reconstructed voltage from ADC counts |
| `i_recon` | A | Reconstructed current from ADC counts |

`v_recon` and `i_recon` are what all downstream modules (m02–m08) use.
`v_actual` / `i_actual` are the ideal reference (used in m06 accuracy check).

---

## Formulas to Implement (per module)

### m02_rms
```
Vrms[ph] = sqrt( mean( v_recon[ph]² ) )        # true RMS, 1600 samples
Irms[ph] = sqrt( mean( i_recon[ph]² ) )
VLL[AB]  = Vrms computed on (v_recon[0] - v_recon[1])
```

### m03_power
```
P[ph]    = mean( v_recon[ph] * i_recon[ph] )    # W — instantaneous product
S[ph]    = Vrms[ph] * Irms[ph]                  # VA
Q[ph]    = sqrt( S[ph]² - P[ph]² )              # VAR
PF[ph]   = P[ph] / S[ph]                        # true PF
P_total  = sum(P),  Q_total = sum(Q),  S_total = sqrt(P_total²+Q_total²)
```

### m04_harmonics
```
FFT with Hanning window → rfft
Magnitude[h] = 2 * abs(FFT[h]) / N_SAMPLES
THD_V = sqrt( sum(Vh² for h=2..31) ) / V1 * 100
THD_I = sqrt( sum(Ih² for h=2..31) ) / I1 * 100
```

### m05_energy
```
kWh   = P_total_W  * T_hours
kVARh = Q_total_VAR * T_hours
kVAh  = S_total_VA  * T_hours
T_hours = N_SAMPLES / FS / 3600
```

### m06_accuracy (IEC 62053-22 Class 0.5S)
```
Test points: (100% Ib, PF=1.0), (100%, 0.5lag), (100%, 0.8lag),
             (20%, 1.0), (5%, 1.0), (1%, 1.0)
Error% = (P_measured - P_reference) / P_reference * 100
Limit:  ±0.5% for tests 1–4, ±1.0% for test 5, ±1.5% for test 6
```

---

## Git Commit Convention

```
feat: Module N — <short description>
fix:  <what was broken> — <how fixed>
docs: <what doc was updated>
refactor: <what changed and why>
```

Examples:
```
feat: Module 2 — Vrms, Irms true RMS computation
feat: Module 3 — Active, Reactive, Apparent power, PF
fix: m01 save_path — use pathlib for Windows compatibility
```

---

## Dependencies

```
numpy>=1.24.0       — signal arrays, FFT, RMS
matplotlib>=3.7.0   — all plots (dark theme)
scipy>=1.10.0       — signal processing (future use)
jupyter>=1.0.0      — notebook support
```

Install: `pip install -r requirements.txt`

---

## Do Not

- Do not hardcode any physical constant — use m00_config.py
- Do not change plot rcParams inside modules — set globally in m00_config.py
- Do not use relative paths like `../outputs/` — use pathlib resolution
- Do not add `.venv/`, `__pycache__/`, or `outputs/*.png` to git
- Do not modify `v_actual` or `i_actual` arrays downstream — they are reference signals