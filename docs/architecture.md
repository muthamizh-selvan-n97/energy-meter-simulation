# Signal Chain Architecture

## ADS131M08 Delta-Sigma ADC — Signal Chain

### Oversampling Architecture

```
Analog Input (±1.2V)
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  ADS131M08 Internal                                 │
│                                                     │
│  CLKIN = 8.192 MHz (from 16.384 MHz XTAL ÷ 2)      │
│       │                                             │
│       ▼                                             │
│  Δ-Σ Modulator (2nd order)                         │
│  Runs at ~256 kHz – 1 MHz (OSR × ODR)              │
│  Output: 1-bit bitstream                            │
│       │                                             │
│       ▼                                             │
│  Sinc³ Decimation Filter                            │
│  Decimates by OSR = 1024                            │
│  Suppresses quantization noise                      │
│       │                                             │
│       ▼                                             │
│  Output: 24-bit word @ 8 kSPS ────────────► MCU SPI│
└─────────────────────────────────────────────────────┘
```

### Clock Chain (TIDA-010243)

```
16.384 MHz XTAL
    │
    ÷ 2
    │
8.192 MHz ──► CLKIN (ADS131M08)
    │          │
    │          ÷ OSR (1024)
    │          │
    │        8.000 kSPS ──► SPI to MSPM0G3507
    │
    × PLL
    │
64 MHz MCLK (CPU clock)
```

### Voltage Front-End

```
230V L-N (325V peak)
      │
   R1 (high side) ─────┐
      │                 │
   R2 (low side)  ──── ADC_IN (±1.08V peak = 90% FS)
      │
     GND
```

Divider ratio: 325V / (1.2V × 0.9) = 301:1

Anti-aliasing filter: RC, corner frequency > 2 kHz (per AN-1076)

### Current Front-End (CT)

```
Line current (up to 20A)
      │
   CT 1000:1
      │
   Burden R = 10Ω
      │
   ADC_IN (±283mV peak @ 20A)
      │
     GND
```

At 20A: V_adc = (20 × √2) / 1000 × 10 = 0.283 V peak = 23.6% FS

Note: 76.4% headroom for overcurrent events (up to 85A before clipping)

## Sampling Parameters

| Parameter            | Value       | Derivation                   |
|----------------------|-------------|------------------------------|
| Output data rate     | 8,000 Hz    | ADS131M08 @ CLKIN = 8.192MHz |
| Grid frequency       | 50 Hz       | Indian / EU grid             |
| Samples per cycle    | 160         | 8000 / 50                    |
| Integration window   | 10 cycles   | Per TIDA-010243 firmware     |
| Window duration      | 200 ms      | 10 × 20 ms                   |
| Total samples/window | 1,600       | 160 × 10                     |
| Nyquist frequency    | 4,000 Hz    | fs / 2                       |
| Highest harmonic     | 79th        | 4000 / 50 (theoretical)      |
| Practical harmonic   | 31st        | Used in metrology firmware   |

## Quantization

| Parameter          | Value              |
|--------------------|--------------------|
| Resolution         | 24-bit signed      |
| Full scale range   | ±8,388,607 counts  |
| LSB (voltage)      | 143.05 nV          |
| LSB (actual V)     | 143.05nV × 301 = 43.1 μV |
| Thermal noise      | ~3.5 LSB rms       |
| Effective bits     | ~22 ENOB (typical) |
| Quantization error | < 0.001% at full scale |

## IEC 62053-22 Class 0.5S Test Points

| Test | Load (% Ib) | PF    | Error limit |
|------|-------------|-------|-------------|
| 1    | 100%        | 1.00  | ±0.5%       |
| 2    | 100%        | 0.50 lag | ±0.5%    |
| 3    | 100%        | 0.80 lag | ±0.5%    |
| 4    | 20%         | 1.00  | ±0.5%       |
| 5    | 5%          | 1.00  | ±1.0%       |
| 6    | 1%          | 1.00  | ±1.5%       |
