# =============================================================
# m08_modbus.py — Modbus RTU/TCP Register Map
# 3-Phase Class 0.5S Energy Meter Simulation
# Reference: TI ADS131M08 + TIDA-010243 | IEC 62053-22
# =============================================================
#
# Maps all computed meter values to 16-bit Modbus holding
# registers (Function Code 0x03).  Follows common energy-meter
# register conventions (e.g. Eastron SDM630, ISKRA MT174).
#
# Scaling:  floats stored as uint16 with a fixed scale factor
#           so the master divides by that factor to recover SI.
# Two-register (32-bit) values use hi-word / lo-word pairs.
# =============================================================

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m00_config import (
    F0, FS, N_SAMPLES, N_CYCLES,
    V_NOM_LN, V_NOM_LL, I_FULLSCALE,
    ADC_BITS,
    PHASE_NAMES,
)

# ---------------------------------------------------------------------------
# Register definition table
# Each entry: (address, name, unit, scale, source_key, source_idx)
#   address    : Modbus holding-register address (0-based, FC03)
#   name       : human-readable register name
#   unit       : physical unit string
#   scale      : raw_value = round(physical_value * scale)  → stored as uint16
#                (master reads raw, divides by scale)
#   source_key : key in the results dict (or 'config' for static values)
#   source_idx : None → scalar, int → array index (phase 0/1/2 or tp index)
# ---------------------------------------------------------------------------

REGISTER_MAP = [
    # ── Static / Configuration (0x0000–0x000F) ──────────────────
    (0x0000, 'Meter_Type',        '',    1,    'config',  'meter_type'),
    (0x0001, 'ADC_Bits',          'bit', 1,    'config',  'adc_bits'),
    (0x0002, 'Fs_Hz',             'Hz',  1,    'config',  'fs'),
    (0x0003, 'F0_Hz',             'Hz',  1,    'config',  'f0'),
    (0x0004, 'N_Cycles',          '',    1,    'config',  'n_cycles'),
    (0x0005, 'Vnom_LN_V',         'V',   10,   'config',  'vnom_ln'),
    (0x0006, 'Vnom_LL_V',         'V',   10,   'config',  'vnom_ll'),
    (0x0007, 'I_FullScale_A',     'A',   10,   'config',  'i_fs'),

    # ── Voltage RMS — Phase A/B/C (0x0010–0x0015) ───────────────
    (0x0010, 'Vrms_A_V',          'V',   100,  'rms',     ('vrms', 0)),
    (0x0011, 'Vrms_B_V',          'V',   100,  'rms',     ('vrms', 1)),
    (0x0012, 'Vrms_C_V',          'V',   100,  'rms',     ('vrms', 2)),
    (0x0013, 'VLL_AB_V',          'V',   100,  'rms',     ('vll',  0)),
    (0x0014, 'VLL_BC_V',          'V',   100,  'rms',     ('vll',  1)),
    (0x0015, 'VLL_CA_V',          'V',   100,  'rms',     ('vll',  2)),

    # ── Current RMS — Phase A/B/C (0x0016–0x0018) ───────────────
    (0x0016, 'Irms_A_A',          'A',   1000, 'rms',     ('irms', 0)),
    (0x0017, 'Irms_B_A',          'A',   1000, 'rms',     ('irms', 1)),
    (0x0018, 'Irms_C_A',          'A',   1000, 'rms',     ('irms', 2)),

    # ── Unbalance (0x0019–0x001A) ────────────────────────────────
    (0x0019, 'V_Unbalance_pct',   '%',   1000, 'rms',     ('v_unbalance_pct', None)),
    (0x001A, 'I_Unbalance_pct',   '%',   1000, 'rms',     ('i_unbalance_pct', None)),

    # ── Active Power W (0x0020–0x0024) ───────────────────────────
    (0x0020, 'P_A_W',             'W',   10,   'power',   ('p', 0)),
    (0x0021, 'P_B_W',             'W',   10,   'power',   ('p', 1)),
    (0x0022, 'P_C_W',             'W',   10,   'power',   ('p', 2)),
    (0x0023, 'P_Total_W',         'W',   10,   'power',   ('p_total', None)),

    # ── Reactive Power VAR (0x0025–0x0029) ───────────────────────
    (0x0025, 'Q_A_VAR',           'VAR', 10,   'power',   ('q', 0)),
    (0x0026, 'Q_B_VAR',           'VAR', 10,   'power',   ('q', 1)),
    (0x0027, 'Q_C_VAR',           'VAR', 10,   'power',   ('q', 2)),
    (0x0028, 'Q_Total_VAR',       'VAR', 10,   'power',   ('q_total', None)),

    # ── Apparent Power VA (0x002A–0x002E) ────────────────────────
    (0x002A, 'S_A_VA',            'VA',  10,   'power',   ('s', 0)),
    (0x002B, 'S_B_VA',            'VA',  10,   'power',   ('s', 1)),
    (0x002C, 'S_C_VA',            'VA',  10,   'power',   ('s', 2)),
    (0x002D, 'S_Total_VA',        'VA',  10,   'power',   ('s_total', None)),

    # ── Power Factor (0x002F–0x0033) ─────────────────────────────
    (0x002F, 'PF_A',              '',    10000,'power',   ('pf', 0)),
    (0x0030, 'PF_B',              '',    10000,'power',   ('pf', 1)),
    (0x0031, 'PF_C',              '',    10000,'power',   ('pf', 2)),
    (0x0032, 'PF_Total',          '',    10000,'power',   ('pf_total', None)),

    # ── THD (0x0040–0x0045) ───────────────────────────────────────
    (0x0040, 'THD_V_A_pct',       '%',   100,  'harmonics',('thd_v', 0)),
    (0x0041, 'THD_V_B_pct',       '%',   100,  'harmonics',('thd_v', 1)),
    (0x0042, 'THD_V_C_pct',       '%',   100,  'harmonics',('thd_v', 2)),
    (0x0043, 'THD_I_A_pct',       '%',   100,  'harmonics',('thd_i', 0)),
    (0x0044, 'THD_I_B_pct',       '%',   100,  'harmonics',('thd_i', 1)),
    (0x0045, 'THD_I_C_pct',       '%',   100,  'harmonics',('thd_i', 2)),

    # ── Energy — 32-bit hi/lo pairs (0x0050–0x005B) ───────────────
    # kWh × 10000 split into hi-word (upper 16 bits) / lo-word (lower 16 bits)
    (0x0050, 'kWh_Total_Hi',      'kWh', None, 'energy',  ('kwh_hi',   None)),
    (0x0051, 'kWh_Total_Lo',      'kWh', None, 'energy',  ('kwh_lo',   None)),
    (0x0052, 'kVARh_Total_Hi',    'kVARh',None,'energy',  ('kvarh_hi', None)),
    (0x0053, 'kVARh_Total_Lo',    'kVARh',None,'energy',  ('kvarh_lo', None)),
    (0x0054, 'kVAh_Total_Hi',     'kVAh', None,'energy',  ('kvah_hi',  None)),
    (0x0055, 'kVAh_Total_Lo',     'kVAh', None,'energy',  ('kvah_lo',  None)),
    (0x0056, 'kWh_Rate_x1000',    'kWh/hr',1000,'energy', ('kwh_hr',   None)),

    # ── IEC 62053-22 Accuracy (0x0060–0x0066) ────────────────────
    (0x0060, 'Accuracy_TP1_err',  '%',   10000,'accuracy',('error_pct', 0)),
    (0x0061, 'Accuracy_TP2_err',  '%',   10000,'accuracy',('error_pct', 1)),
    (0x0062, 'Accuracy_TP3_err',  '%',   10000,'accuracy',('error_pct', 2)),
    (0x0063, 'Accuracy_TP4_err',  '%',   10000,'accuracy',('error_pct', 3)),
    (0x0064, 'Accuracy_TP5_err',  '%',   10000,'accuracy',('error_pct', 4)),
    (0x0065, 'Accuracy_TP6_err',  '%',   10000,'accuracy',('error_pct', 5)),
    (0x0066, 'Class05S_Pass',     '',    1,    'accuracy',('all_passed_int', None)),
]


def _resolve(entry, results):
    """Return the physical float value for a register entry."""
    addr, name, unit, scale, src, key = entry

    if src == 'config':
        cfg_map = {
            'meter_type': 305,          # arbitrary product code
            'adc_bits':   ADC_BITS,
            'fs':         FS,
            'f0':         F0,
            'n_cycles':   N_CYCLES,
            'vnom_ln':    V_NOM_LN,
            'vnom_ll':    V_NOM_LL,
            'i_fs':       I_FULLSCALE,
        }
        return float(cfg_map[key])

    # augment results with derived fields
    r = results

    if src == 'rms':
        field, idx = key
        val = r['rms'][field]
        return float(val) if idx is None else float(val[idx])

    if src == 'power':
        field, idx = key
        val = r['power'][field]
        return float(val) if idx is None else float(val[idx])

    if src == 'harmonics':
        field, idx = key
        val = r['harmonics'][field]
        return float(val) if idx is None else float(val[idx])

    if src == 'energy':
        field, idx = key
        return float(r['energy_derived'][field])

    if src == 'accuracy':
        field, idx = key
        val = r['accuracy'][field]
        return float(val) if idx is None else float(val[idx])

    return 0.0


def _build_energy_derived(results_energy):
    """Split kWh/kVARh/kVAh into 32-bit hi/lo uint16 words.

    Energy values are scaled by 10000 (resolution = 0.0001 kWh) and
    stored as a 32-bit unsigned integer split across two consecutive
    16-bit Modbus registers (big-endian word order: hi-word first).
    A uint16 can only hold values up to 6.5535 kWh, so the 32-bit
    pair allows up to 429496.7295 kWh — sufficient for a revenue meter
    that accumulates energy over months between resets.
    """
    def split32(fval, factor=10000):
        # Multiply by scale factor, mask to 32 bits, then split words.
        raw = int(round(abs(fval) * factor)) & 0xFFFFFFFF
        return (raw >> 16) & 0xFFFF, raw & 0xFFFF

    kwh_hi,   kwh_lo   = split32(results_energy['kwh'])
    kvarh_hi, kvarh_lo = split32(results_energy['kvarh'])
    kvah_hi,  kvah_lo  = split32(results_energy['kvah'])

    return {
        'kwh_hi':   kwh_hi,
        'kwh_lo':   kwh_lo,
        'kvarh_hi': kvarh_hi,
        'kvarh_lo': kvarh_lo,
        'kvah_hi':  kvah_hi,
        'kvah_lo':  kvah_lo,
        'kwh_hr':   results_energy['kwh_hr'],
    }


def print_modbus_map(results_rms, results_power, results_harmonics,
                     results_energy, results_accuracy):
    """
    Print the full Modbus holding-register map and simulate
    a FC03 read-all frame.

    Parameters
    ----------
    results_rms       : dict from m02_rms
    results_power     : dict from m03_power
    results_harmonics : dict from m04_harmonics
    results_energy    : dict from m05_energy
    results_accuracy  : dict from m06_accuracy
    """
    print(f"{'─'*62}")
    print(f"  MODULE 8 — Modbus RTU/TCP Register Map")
    print(f"{'─'*62}")

    # augment accuracy with int flag
    results_accuracy = dict(results_accuracy)
    results_accuracy['all_passed_int'] = \
        1 if results_accuracy['all_passed'] else 0

    results = {
        'rms':            results_rms,
        'power':          results_power,
        'harmonics':      results_harmonics,
        'energy':         results_energy,
        'energy_derived': _build_energy_derived(results_energy),
        'accuracy':       results_accuracy,
    }

    # ── Build register values ─────────────────────────────────────
    reg_values = {}   # address → (name, unit, scale, physical, raw_uint16)

    for entry in REGISTER_MAP:
        addr, name, unit, scale, src, key = entry
        phys = _resolve(entry, results)

        if scale is None:
            # pre-computed uint16 (hi/lo words)
            raw = int(phys) & 0xFFFF
        else:
            raw = int(round(abs(phys) * scale)) & 0xFFFF

        reg_values[addr] = (name, unit, scale, phys, raw)

    # ── Print register table ──────────────────────────────────────
    print(f"\n  {'Addr':>6}  {'Register Name':<26} {'Physical':>12}  "
          f"{'Unit':<7} {'Scale':>8}  {'Raw (uint16)':>13}")
    print(f"  {'─'*80}")

    prev_block = -1
    for entry in REGISTER_MAP:
        addr = entry[0]
        block = addr >> 4
        if block != prev_block and prev_block != -1:
            print()
        prev_block = block

        name, unit, scale, phys, raw = reg_values[addr]
        scale_str = f'×{scale}' if scale else 'hi/lo'
        unit_str  = unit if unit else '—'
        print(f"  0x{addr:04X}  {name:<26} {phys:>12.4f}  "
              f"{unit_str:<7} {scale_str:>8}  {raw:>6} (0x{raw:04X})")

    # ── Simulated FC03 frame ──────────────────────────────────────
    _print_fc03_frame(reg_values)

    verdict = 'PASS' if results_accuracy['all_passed'] else 'FAIL'
    print(f"  ✓ m08_modbus — {len(REGISTER_MAP)} registers mapped | "
          f"IEC Class 0.5S: {verdict}\n")


def _print_fc03_frame(reg_values):
    """Print a simulated Modbus RTU FC03 response frame."""
    addrs  = sorted(reg_values.keys())
    n_regs = len(addrs)

    # Build byte payload (big-endian uint16 per register)
    payload = bytearray()
    for addr in addrs:
        raw = reg_values[addr][4]
        payload += struct.pack('>H', raw)

    # RTU frame: SlaveID(1) + FC(1) + ByteCount(1) + Data + CRC(2)
    slave_id   = 0x01
    func_code  = 0x03
    byte_count = n_regs * 2

    frame_body = bytes([slave_id, func_code, byte_count]) + bytes(payload)
    crc        = _crc16(frame_body)
    frame      = frame_body + struct.pack('<H', crc)   # CRC little-endian

    print(f"\n  SIMULATED MODBUS RTU FC03 RESPONSE FRAME")
    print(f"  {'─'*62}")
    print(f"  Slave ID    : 0x{slave_id:02X}")
    print(f"  Function    : 0x{func_code:02X}  (Read Holding Registers)")
    print(f"  Start Addr  : 0x{addrs[0]:04X}")
    print(f"  Qty Regs    : {n_regs}  ({byte_count} bytes)")
    print(f"  CRC-16      : 0x{crc:04X}")
    print(f"  Frame size  : {len(frame)} bytes")
    print(f"\n  First 32 bytes of frame (hex):")
    hex_line = ' '.join(f'{b:02X}' for b in frame[:32])
    print(f"  {hex_line} ...")


def _crc16(data: bytes) -> int:
    """Modbus CRC-16 (polynomial 0xA001).

    Standard Modbus RTU error-checking algorithm (IEC 62056-21 / MODBUS
    Application Protocol Specification V1.1b3, Section 2.5.1):
      1. Initialise CRC register to 0xFFFF.
      2. XOR each byte into the low byte of the CRC register.
      3. Shift right 8 times; if the shifted-out bit is 1, XOR with the
         reversed polynomial 0xA001 (bit-reverse of 0x8005).
      4. Continue until all bytes are processed.
    The resulting 16-bit value is appended to the frame in little-endian
    order (lo-byte first), which is the only Modbus RTU CRC convention.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


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

    print_modbus_map(results_rms, results_power, results_harmonics,
                     results_energy, results_accuracy)
