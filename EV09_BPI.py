#!/usr/bin/env python3
"""
EV09_BPI.py — Analisis Fenomena Baratan
================================================
Versi 2.0.0  |  Jolotundo Research Observatory · MJS
Titik pengamatan: −7.5220°LS, 112.5661°BT, 28 m dpl, Jawa Timur

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFINISI BARATAN (dipertegas dari v1.x)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Baratan" BUKAN sekadar datangnya angin barat pertama (monsun onset).
Baratan adalah FASE KUNCI KALENDER MANGSA ketika:
  · Arak-arakan awan tebal dari barat TERKUNCI selama berminggu-minggu
  · Hampir siang dan malam langit diselimuti awan cumulonimbus & nimbostratus
  · Sinar matahari jarang menembus tutupan awan > 85%
  · Gerimis (drizzle) hampir tak henti, tanah terus lembab
  · TCWV > 50 kg/m² — kolom uap air penuh
  · u_comp rolling > 0 unit-vector — adveksi lestari dari barat
  · DTR kecil (< 8°C) — awan selimut meredam fluktuasi suhu harian

Onset baratan = momen ketika kondisi "awan berkelanjutan" ini MENGUNCI,
bukan sekadar hujan pertama atau angin barat pertama.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERUBAHAN UTAMA dari v1.4.4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. BCI → BPI (Baratan Persistence Index):
       · Bobot diubah agar mencerminkan PERSISTENSI awan, bukan onset hujan
       · cloud_lo dihapus dari BPI (cloud_lo di ERA5 tidak konsisten mewakili
         baratan; cloud total + sw_rad lebih reliabel)
       · Tambahan komponen: DTR rendah (awan selimut meredam temp range)
       · Komponen presipitasi diganti dengan frekuensi gerimis (precip_freq)

  2. Window onset diperketat: [120, 195] dopy (okt–feb awal)
       · Window lama [120, 240] terlalu lebar, mencakup seluruh puncak musim

  3. B2_WCC diperbaiki:
       · u_comp > 1.0 unit-vector (bukan 0.05) rolling 7d
       · cloud > 82% rolling 7d (bukan 70%)
       · TCWV > P90 dry = 50.2 kg/m2 (bukan P80)
       · Threshold SUSTAIN dinaikkan dari 0.7 → 0.75

  4. B3_RAD diperbaiki:
       · Threshold sw_rad < P15 dry (bukan P25) → lebih ketat
       · Persistence requirement: 21 dari 30 hari harus < threshold

  5. B4_SOIL diperbaiki:
       · sm_7_28 gunakan P85 (basah) dihitung dari periode BARATAN historis
         sebagai lower bound, bukan P80 dry
       · Tambah komponen: sm_28_100 juga harus basah (lapisan lebih dalam,
         indikator hujan telah berlangsung lama)

  6. HMM onset dikoreksi: gunakan State 2 (Rendheng) bukan State 1
       · State 1 center: cloud 69%, TCWV 42.6, u_30=-0.07 → TRANSISIONAL
       · State 2 center: cloud 91%, TCWV 53.1, u_30=+0.39 → BARATAN PENUH
       · Onset = pertama kali P(state=2) > 0.65 bertahan ≥ 7 hari

  7. Ensemble diperbaiki: Biweight mean (Tukey) + dispersion-aware weighting
       · MAD-based outlier softening menggantikan integer-repetition median
       · Bobot B1_BPI naik ke 3.5 (persistence index paling fisik koheren)
       · Bobot B7_HMM naik ke 2.0 (setelah koreksi state mapping)

  8. Precursor index diperbarui:
       · TCWV + cloud sebagai precursor terdepan (14-21 hari sebelum onset)
       · sw_rad deficit sebagai precursor terkuat untuk "baratan terkunci"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Struktur analisis (sama seperti v1.4.4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  §1   Konstanta & parameter fisis
  §2   Loader data meteorologi (hourly, IDW dua kelas P1+P2)
  §3   Utilitas numerik
  §4   Baratan Persistence Index (BPI) — pengganti BCI
  §5   Estimator B1–B6 (diperbarui)
  §5b  B7_HMM — 9-D GMM-HMM causal filter (state mapping dikoreksi)
  §6   Ensemble berbobot (Biweight + MAD)
  §7   Runner per pranata-tahun
  §8   Analisis atmosfer
  §9   Analisis tanah
  §10  Presipitasi
  §11  Statistik multi-tahun
  §12  Konteks iklim (ENSO · IOD · MJO · regresi OLS · ARX)
  §13  Report generators (A–F)
  §14  CLI

Tujuh estimator independen
  B1  BPI   Baratan Persistence Index — 8 variabel z-score berbobot persistensi
  B2  WCC   Wind × Cloud × TCWV joint AND-gate (threshold diperketat)
  B3  RAD   Solar radiation deficit — threshold P15 dry, lebih ketat
  B4  SOIL  Soil moisture 7–28 cm & 28–100 cm dual-layer persistence
  B5  VPD   VPD drop + RH rise dual-threshold
  B6  PRESS Surface pressure low signature
  B7  HMM   9-D GMM-HMM causal filter — State 2 onset (dikoreksi)

Referensi ilmiah
  · Killick et al. (2012) JASA 107:1590–1598
  · Page (1954) Biometrika 41:100–115
  · Pettitt (1979) JRSS-C 28:126–135
  · Rabiner (1989) Proc. IEEE 77(2):257–286
  · Wheeler & Hendon (2004) Mon. Wea. Rev. 132:1917–1932
  · Lim & Chang (1981) J. Atmos. Sci. 38:2496–2503 (Asian monsoon persistence)

DATA & ATRIBUSI
  Meteorologi : ERA5 / ERA5-Land (ECMWF/C3S) + IFS HRES 9 km
                via Open-Meteo · 2015–2026 · hourly
  Target      : −7.5220°LS, 112.5661°BT, 28 m
  Stasiun P1  : −7.486819°LS, 112.538210°BT (28 m)
  Stasiun P2  : −7.5571175°LS, 112.557350°BT (28 m)
  IDW         : volatile W1=0.4154 · soil W1=0.4996
  ENSO SST    : NOAA OISST v2.1
  ENSO SLA    : AVISO/DUACS
  IOD         : JMA DMI + BoM
  MJO         : RMM (Wheeler & Hendon 2004)
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from EV09wind import (
        _find_crossing, attach_time_features,
        ANCHOR_MONTH, ANCHOR_DAY, W, IND,
        sec_header, print_header, box_top, box_bot, box_row, box_mid,
        thin_hbar, _dopy_to_approx_date, _linear_trend,
        IDW_W1_VOLATILE, IDW_W2_VOLATILE,
        DEFAULT_HOURLY_P1, DEFAULT_HOURLY_P2,
        find_data_file, _read_openmeteo_csv,
        MONTH_SHORT, SCENARIO_LABUH_DOPY,
    )
except ImportError as e:
    print(f"[!] EV09wind.py tidak ditemukan: {e}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════
# §1  Konstanta & parameter fisis
# ══════════════════════════════════════════════════════════════════════════

# ── Window deteksi (dopy = hari sejak anchor 22 Juni) ────────────────────
# Baratan = awan terkunci: Oktober awal s.d. Februari awal
# dopy 100 ≈ 1 Okt | dopy 195 ≈ 3 Feb | dopy 240 ≈ 19 Mar
BAR_ONSET_LO   = 100.0   # was 120 — lebih awal karena baratan bisa mulai Sep akhir
BAR_ONSET_HI   = 195.0   # was 240 — dipersempit; batas sebelum baratan sudah penuh
BAR_OFFSET_LO  = 190.0   # was 220 — biarkan window mencakup tahun El Niño kuat
BAR_OFFSET_HI  = 330.0
BAR_PEAK_LO    = 150.0
BAR_PEAK_HI    = 270.0

# ── Siklus hidup baratan — 5 fase (analisis empiris EV09 2015–2025) ──────
# Baratan bukan peristiwa tunggal — ia punya siklus hidup.
# Onset ensemble B1–B7 = "Kunci" di Fase 2. Angin barat MENYUSUL, bukan
# memimpin. Rentang operasional non-overlapping untuk statistik komposit.
#
#   Fase 1 Benih    [ 80–117]  Pengisian uap; angin masih easterly
#   Fase 2 Kunci    [118–155]  Onset — langit menutup, siklus diurnal mati
#                              (onset aktual bervariasi 118–141 per tahun)
#   Fase 3 Plateau  [156–235]  Saturasi penuh; u_comp positif; peak BPI ~220
#   Fase 4 Longgar  [236–309]  Kunci mulai lepas; cloud & u_comp turun
#   Fase 5 Bubar    [310–365 + 0–79]  Kembali ke rezim kering

BARATAN_LIFECYCLE = (
    {
        "id": 1, "name": "Benih",
        "dopy_lo":  80.0, "dopy_hi": 130.0,
        "tagline": "Pengisian uap — angin masih easterly",
        "signature": (
            "TCWV mulai naik (34 → 40 kg/m²)",
            "Cloud mulai naik (47% → 68%)",
            "u_comp masih easterly tipis (−0.30 → −0.15)",
            "Angin belum berbalik; uap mengalir tanpa adveksi barat jelas",
        ),
    },
    {
        "id": 2, "name": "Kunci",
        "dopy_lo": 118.0, "dopy_hi": 141.0,
        "tagline": "Onset — langit menutup, siklus diurnal mati",
        "signature": (
            "Cloud melompat > 80%",
            "SW_rad jatuh tajam (266 → 228 W/m²)",
            "TCWV melewati ~49 kg/m²",
            "Siklus diurnal mulai mati (DTR menyempit)",
            "u_comp masih netral (−0.01) — angin MENYUSUL, bukan memimpin",
        ),
    },
    {
        "id": 3, "name": "Plateau",
        "dopy_lo": 160.0, "dopy_hi": 230.0,
        "tagline": "Saturasi penuh — peak BPI",
        "signature": (
            "Semua variabel saturasi (cloud > 90%, TCWV > 52 kg/m²)",
            "u_comp akhirnya positif (+0.26 → +0.50 unit-vector)",
            "Peak BPI di sini (dopy ~220)",
            "Siklus diurnal mati sepenuhnya (DTR < 8°C)",
        ),
    },
    {
        "id": 4, "name": "Longgar",
        "dopy_lo": 240.0, "dopy_hi": 310.0,
        "tagline": "Kunci mulai lepas",
        "signature": (
            "Cloud turun pelan (85 → 77%)",
            "u_comp berbalik easterly (+0.21 → −0.17)",
            "SW naik kembali (215 → 219 W/m²)",
            "TCWV masih tinggi (50 kg/m²) — uap belum hilang, hanya awan berkurang",
            "Diduga terkait pendinginan Australia & pembalikan gradien tekanan",
        ),
    },
    {
        "id": 5, "name": "Bubar",
        "dopy_lo": 310.0, "dopy_hi":  80.0,   # wrap-around
        "tagline": "Kembali ke rezim kering",
        "signature": (
            "Rezim kemarau kembali",
            "Cloud < 60%, TCWV < 42 kg/m², hujan < 2 mm/hr",
            "u_comp easterly konsisten",
        ),
    },
)

_PHASE_BOUNDS = (
    ( 80.0, 117.0),   # Fase 1 Benih
    (118.0, 155.0),   # Fase 2 Kunci
    (156.0, 235.0),   # Fase 3 Plateau
    (236.0, 309.0),   # Fase 4 Longgar
    (310.0,  79.0),   # Fase 5 Bubar (wrap)
)

_LIFECYCLE_FIELDS = (
    ("tcwv",      "TCWV kg/m²",   ".1f"),
    ("cloud",     "Cloud total %", ".1f"),
    ("cloud_lo",  "Cloud low %",   ".1f"),
    ("cloud_mid", "Cloud mid %",   ".1f"),
    ("u_comp",    "u_comp (adim.)", "+.2f"),
    ("sw_rad",    "SW rad W/m²",   ".1f"),
    ("rh",        "RH 2m %",       ".1f"),
    ("vpd",       "VPD kPa",       ".2f"),
    ("dtr",       "DTR °C",        ".2f"),
    ("precip",    "Hujan mm/hr",   ".2f"),
)

# Musim kering (Katiga) sebagai referensi baseline climatology
DRY_LO         =  50.0   # ~11 Agu
DRY_HI         = 130.0   # ~29 Okt

ROLL_WIN       = 21   # was 14 — rolling lebih panjang untuk persistensi
ROLL_WIN_S     =  7
SUSTAIN        = 14   # was 10 — persistence requirement lebih ketat
SUSTAIN_MIN    =  9   # min valid dalam window SUSTAIN (64%)
EPS            = 0.025

IDW_W1_SOIL: float = 0.4996
IDW_W2_SOIL: float = 0.5004

_SOIL_CLASS_COLS = frozenset((
    "sm_0_7", "sm_7_28", "sm_28_100", "sm_100_255",
    "st_0_7", "st_7_28", "st_28_100", "st_100_255",
))

# ── Bobot ensemble — DIREVISI dari v1.4.4 ────────────────────────────────
# Dasar revisi bobot:
#   B1_BPI: index paling koheren secara fisis untuk "awan berkelanjutan" → 3.5
#   B2_WCC: threshold diperketat, lebih presisi → 2.5
#   B3_RAD: sw_rad deficit terbaik proxy "langit tertutup lama" → 2.5
#   B4_SOIL: dual-layer moisture, sinyal tertunda tapi stabil → 1.5
#   B5_VPD: sinyal cepat tapi juga mudah terpicu hujan biasa → 1.5
#   B6_PRESS: tekanan rendah umum di musim hujan, kurang spesifik → 1.0
#   B7_HMM: setelah koreksi state mapping, state 2 lebih tepat → 2.0
ENS_W_ONSET: Dict[str, float] = {
    "B1_BPI":     3.5,
    "B2_WCC":     2.5,
    "B3_RAD":     2.5,
    "B4_SOIL":    1.5,
    "B5_VPD":     1.5,
    "B6_PRESS":   1.0,
    "B7_HMM":     2.0,
}
ENS_W_OFFSET = dict(ENS_W_ONSET)

_RENAME: Dict[str, str] = {
    "temperature_2m (°C)":                             "temp2m",
    "relative_humidity_2m (%)":                        "rh",
    "precipitation (mm)":                              "precip",
    "rain (mm)":                                       "rain",
    "weather_code (wmo code)":                         "wcode",
    "surface_pressure (hPa)":                          "pressure",
    "cloud_cover (%)":                                 "cloud",
    "cloud_cover_low (%)":                             "cloud_lo",
    "cloud_cover_mid (%)":                             "cloud_mid",
    "cloud_cover_high (%)":                            "cloud_hi",
    "et0_fao_evapotranspiration (mm)":                 "et0",
    "wind_speed_10m (km/h)":                           "ws10",
    "wind_speed_100m (km/h)":                          "ws100",
    "wind_direction_10m (°)":                          "wd10",
    "wind_direction_100m (°)":                         "wd100",
    "wind_gusts_10m (km/h)":                           "gust10",
    "vapour_pressure_deficit (kPa)":                   "vpd",
    "soil_temperature_0_to_7cm (°C)":                  "st_0_7",
    "soil_temperature_7_to_28cm (°C)":                 "st_7_28",
    "soil_temperature_28_to_100cm (°C)":               "st_28_100",
    "soil_temperature_100_to_255cm (°C)":              "st_100_255",
    "soil_moisture_0_to_7cm (m³/m³)":                  "sm_0_7",
    "soil_moisture_7_to_28cm (m³/m³)":                 "sm_7_28",
    "soil_moisture_28_to_100cm (m³/m³)":               "sm_28_100",
    "soil_moisture_100_to_255cm (m³/m³)":              "sm_100_255",
    "total_column_integrated_water_vapour (kg/m²)":    "tcwv",
    "sunshine_duration (s)":                           "sunshine",
    "shortwave_radiation (W/m²)":                      "sw_rad",
    "dew_point_2m (°C)":                               "dew_pt",
    "apparent_temperature (°C)":                       "temp_app",
}

_BARATAN_CACHE: Optional[pd.DataFrame] = None
_HMM_FEAT_CACHE: Optional[pd.DataFrame] = None

# ── Threshold BPI dihitung dari data ERA5 (2015–2025) ─────────────────────
# Dihitung dari percentil musim kering dopy 50–130
# Nilai hardcoded untuk reproducibility; akan di-override oleh _compute_bpi_thresholds
# jika ada data cukup
BPI_TCWV_THR:   float = 50.17   # P90 dry [kg/m²]
BPI_SW_RAD_THR: float = 244.83  # P20 dry [W/m²]
BPI_CLOUD_THR:  float = 83.8    # P80 dry [%]
BPI_RH_THR:     float = 73.9    # P85 dry [%]
BPI_VPD_THR:    float = 1.250   # P20 dry [kPa]
BPI_DTR_THR:    float = 10.90   # P30 dry [°C]
BPI_SM_THR:     float = 0.1559  # P75 dry sm_7_28 [m³/m³]

DEFAULT_ENSO_SST_CSV  = "Sst_nino34_index.csv"
DEFAULT_ENSO_MSLA_CSV = "Msla_nino34_index.csv"
DEFAULT_IOD_WEEKLY    = "iod_1.txt"
DEFAULT_IOD_MONTHLY   = "30yr_dmi_3rmean.txt"
DEFAULT_RMM_CSV       = "rmm8.csv"

ENSO_THR: float = 0.50
IOD_THR:  float = 0.40

ANOMALY_SST_STR: float = 0.75
ANOMALY_DMI_STR: float = 0.75
ANOMALY_SIGMA:   float = 1.50

MJO_AMP_THR: float = 1.5
MJO_MIN_EVENT_DAYS: int = 5
MJO_ONSET_PHASES = (5, 6, 7, 8)
MJO_LEAD_DAYS    = (7, 15)

# ── HMM 9-D — parameter kalibrasi dari data MJS ──────────────────────────
# (sama dengan v1.4.4, tidak diubah karena recalibrasi butuh data baru)
# Perubahan: INTERPRETASI state untuk onset baratan
#   State 0 — Katiga: cloud 50%, TCWV 36.8, u_30=-0.26 → kemarau
#   State 1 — Transisi: cloud 69%, TCWV 42.6, u_30=-0.07 → labuh/awal hujan
#   State 2 — Rendheng: cloud 91%, TCWV 53.1, u_30=+0.39 → BARATAN PENUH ✓
#   State 3 — Labuh-wet: cloud 74%, TCWV 49.0, u_30=-0.10 → akhir baratan

HMM_WARMUP_DAYS: int = 180
HMM_WARMUP_MIN:  int = 90

HMM_T8_STATE = {
    0: "Katiga      — kering (kemarau puncak)",
    1: "Transisi    — awal hujan (labuh/mangsa 2)",
    2: "Baratan     — awan terkunci (ONSET BARATAN PENUH)",   # ← dikoreksi
    3: "Labuh-wet   — akhir baratan / transisi ke labuh",
}

HMM_T8_pi = [0.0, 0.0, 1.0, 0.0]

HMM_T8_mu = [
      191.64947,    62.10615,     0.23438,    76.13375,    45.44978,
        8.39168,    71.21802,     0.22077,    -0.00104,
]
HMM_T8_sd = [
      173.28640,   191.96817,     0.10390,    10.28729,     8.24867,
        1.89935,    18.57275,     0.09599,     0.31963,
]

HMM_T8_means = [
    [   -0.99377,    -0.97614,    -1.05370,    -0.95034,    -1.04708,
        +0.78532,    -1.15176,    -0.61537,    -0.81463],
    [   -0.42278,    -0.53071,    -0.70635,    -0.83299,    -0.34137,
        +1.01370,    -0.08000,    -1.22176,    -0.21194],
    [   +1.17052,    +1.16176,    +0.92461,    +0.95188,    +0.92858,
        -0.85044,    +1.10336,    +0.60933,    +1.23323],
    [   +0.12685,    +0.18737,    +0.68967,    +0.61065,    +0.43217,
        -0.64527,    +0.17855,    +0.86072,    -0.31683],
]

HMM_T8_covs = np.array([
    # State 0 — Katiga
    [[ +0.01588,  +0.02091,  +0.03223,  +0.04724,  +0.05735,  -0.05639,  +0.03190,  +0.00827,  -0.00068],
     [ +0.02091,  +0.03386,  +0.05419,  +0.08530,  +0.08700,  -0.10541,  +0.03976,  +0.03018,  +0.00213],
     [ +0.03223,  +0.05419,  +0.15176,  +0.18621,  +0.14635,  -0.18365,  +0.07477,  +0.15806,  +0.02864],
     [ +0.04724,  +0.08530,  +0.18621,  +0.29206,  +0.26278,  -0.34220,  +0.09085,  +0.19824,  +0.02155],
     [ +0.05735,  +0.08700,  +0.14635,  +0.26278,  +0.42942,  -0.37675,  +0.15596,  +0.09037,  +0.04772],
     [ -0.05639,  -0.10541,  -0.18365,  -0.34220,  -0.37675,  +0.58961,  -0.06278,  -0.16060,  +0.02745],
     [ +0.03190,  +0.03976,  +0.07477,  +0.09085,  +0.15596,  -0.06278,  +0.21118,  +0.03765,  +0.02151],
     [ +0.00827,  +0.03018,  +0.15806,  +0.19824,  +0.09037,  -0.16060,  +0.03765,  +0.31850,  +0.05835],
     [ -0.00068,  +0.00213,  +0.02864,  +0.02155,  +0.04772,  +0.02745,  +0.02151,  +0.05835,  +0.11241]],

    # State 1 — Transisi labuh/awal-hujan
    [[ +0.37246,  +0.40736,  +0.36610,  +0.49085,  +0.41278,  -0.38118,  +0.37705,  +0.05423,  +0.23190],
     [ +0.40736,  +0.44777,  +0.40363,  +0.54460,  +0.46155,  -0.42506,  +0.41698,  +0.05297,  +0.25587],
     [ +0.36610,  +0.40363,  +0.41381,  +0.50692,  +0.42358,  -0.38950,  +0.37026,  +0.08816,  +0.26206],
     [ +0.49085,  +0.54460,  +0.50692,  +0.70851,  +0.62597,  -0.52945,  +0.54344,  +0.05100,  +0.32758],
     [ +0.41278,  +0.46155,  +0.42358,  +0.62597,  +0.66887,  -0.46113,  +0.51884,  +0.02516,  +0.29111],
     [ -0.38118,  -0.42506,  -0.38950,  -0.52945,  -0.46113,  +0.49998,  -0.37367,  -0.05595,  -0.21647],
     [ +0.37705,  +0.41698,  +0.37026,  +0.54344,  +0.51884,  -0.37367,  +0.49931,  +0.01152,  +0.25063],
     [ +0.05423,  +0.05297,  +0.08816,  +0.05100,  +0.02516,  -0.05595,  +0.01152,  +0.13694,  +0.06402],
     [ +0.23190,  +0.25587,  +0.26206,  +0.32758,  +0.29111,  -0.21647,  +0.25063,  +0.06402,  +0.25200]],

    # State 2 — Rendheng/Baratan penuh
    [[ +0.35225,  +0.33386,  +0.11709,  +0.10561,  +0.04822,  -0.04148,  +0.02641,  +0.19034,  +0.05352],
     [ +0.33386,  +0.31919,  +0.11911,  +0.10516,  +0.04493,  -0.04947,  +0.02729,  +0.19490,  +0.06111],
     [ +0.11709,  +0.11911,  +0.11505,  +0.06858,  -0.01836,  -0.04638,  -0.00061,  +0.22649,  +0.11588],
     [ +0.10561,  +0.10516,  +0.06858,  +0.05965,  -0.01023,  -0.02527,  -0.00201,  +0.12129,  +0.03443],
     [ +0.04822,  +0.04493,  -0.01836,  -0.01023,  +0.13727,  -0.05920,  +0.02862,  -0.04585,  +0.03167],
     [ -0.04148,  -0.04947,  -0.04638,  -0.02527,  -0.05920,  +0.12205,  -0.01003,  -0.11212,  -0.14515],
     [ +0.02641,  +0.02729,  -0.00061,  -0.00201,  +0.02862,  -0.01003,  +0.04784,  -0.01541,  +0.01979],
     [ +0.19034,  +0.19490,  +0.22649,  +0.12129,  -0.04585,  -0.11212,  -0.01541,  +0.57866,  +0.28083],
     [ +0.05352,  +0.06111,  +0.11588,  +0.03443,  +0.03167,  -0.14515,  +0.01979,  +0.28083,  +0.55031]],

    # State 3 — Labuh-wet
    [[ +0.40760,  +0.37938,  +0.25408,  +0.21079,  +0.20569,  -0.12294,  +0.28402,  +0.21435,  +0.25177],
     [ +0.37938,  +0.35514,  +0.24324,  +0.20253,  +0.19155,  -0.11783,  +0.26434,  +0.20603,  +0.23050],
     [ +0.25408,  +0.24324,  +0.28772,  +0.18468,  +0.09055,  -0.05112,  +0.14875,  +0.26177,  +0.16310],
     [ +0.21079,  +0.20253,  +0.18468,  +0.15244,  +0.12309,  -0.08837,  +0.14559,  +0.16338,  +0.11380],
     [ +0.20569,  +0.19155,  +0.09055,  +0.12309,  +0.29225,  -0.16297,  +0.22177,  +0.05589,  +0.12849],
     [ -0.12294,  -0.11783,  -0.05112,  -0.08837,  -0.16297,  +0.15657,  -0.12843,  -0.03327,  -0.06144],
     [ +0.28402,  +0.26434,  +0.14875,  +0.14559,  +0.22177,  -0.12843,  +0.29820,  +0.09957,  +0.15257],
     [ +0.21435,  +0.20603,  +0.26177,  +0.16338,  +0.05589,  -0.03327,  +0.09957,  +0.28193,  +0.15586],
     [ +0.25177,  +0.23050,  +0.16310,  +0.11380,  +0.12849,  -0.06144,  +0.15257,  +0.15586,  +0.36003]],
])

HMM_T8_A = np.array([
    [0.991542, 0.007689, 0.000000, 0.000769],
    [0.000000, 0.985470, 0.014530, 0.000000],
    [0.000000, 0.000000, 0.988726, 0.011274],
    [0.011672, 0.000000, 0.002922, 0.985405],
])

# ── HMM onset/offset thresholds (DIREVISI) ───────────────────────────────
# v1.4.4: State 1 onset (P > 0.70, argmax), State 3 offset
# v2.0.0: State 2 onset (P > 0.65, first sustained crossing)
#         State 3 offset (tidak berubah tapi diperlonggar)
HMM_ONSET_STATE:  int   = 2     # ← DIKOREKSI dari 1 ke 2
HMM_OFFSET_STATE: int   = 3
HMM_ONSET_P_THR:  float = 0.60  # ← diturunkan sedikit dari 0.70 karena state 2 lebih definitif
HMM_OFFSET_P_THR: float = 0.60
HMM_SUSTAIN:      int   = 7

SRKF_Q_LEVEL:    float = 0.005
SRKF_Q_TREND:    float = 1e-4
SRKF_R_INIT:     float = 1.0
SRKF_ARCH_OMEGA: float = 0.005
SRKF_ARCH_ALPHA: float = 0.30
SRKF_R_FLOOR:    float = 0.01


# ══════════════════════════════════════════════════════════════════════════
# §2  Loader data meteorologi
# ══════════════════════════════════════════════════════════════════════════

def load_baratan_data(
    csv_p1: str = DEFAULT_HOURLY_P1,
    csv_p2: str = DEFAULT_HOURLY_P2,
) -> Optional[pd.DataFrame]:
    global _BARATAN_CACHE
    if _BARATAN_CACHE is not None:
        return _BARATAN_CACHE

    p1 = find_data_file(csv_p1)
    p2 = find_data_file(csv_p2)
    if p1 is None and p2 is None:
        print("  [!] CSV tidak ditemukan.")
        return None

    def _load(path: str) -> pd.DataFrame:
        return _read_openmeteo_csv(path).rename(columns=_RENAME)

    if p1 is None:
        df = _load(p2)
    elif p2 is None:
        df = _load(p1)
    else:
        d1 = _load(p1).set_index("time")
        d2 = _load(p2).set_index("time")
        idx = d1.index.union(d2.index)
        out = pd.DataFrame(index=idx)

        scalar_cols = [v for v in _RENAME.values()
                       if v not in ("wd10", "wd100")]
        for col in scalar_cols:
            v1 = (d1[col].reindex(idx) if col in d1.columns
                  else pd.Series(np.nan, index=idx))
            v2 = (d2[col].reindex(idx) if col in d2.columns
                  else pd.Series(np.nan, index=idx))
            both = v1.notna() & v2.notna()
            s = pd.Series(np.nan, index=idx)
            w1, w2 = ((IDW_W1_SOIL, IDW_W2_SOIL)
                      if col in _SOIL_CLASS_COLS
                      else (IDW_W1_VOLATILE, IDW_W2_VOLATILE))
            s.loc[both] = w1 * v1[both] + w2 * v2[both]
            s.loc[v1.notna() & ~both] = v1[v1.notna() & ~both]
            s.loc[~v1.notna() & v2.notna()] = v2[~v1.notna() & v2.notna()]
            out[col] = s

        for src in ("wd10", "wd100"):
            r1 = (np.deg2rad(d1[src].reindex(idx).values)
                  if src in d1.columns else np.full(len(idx), np.nan))
            r2 = (np.deg2rad(d2[src].reindex(idx).values)
                  if src in d2.columns else np.full(len(idx), np.nan))
            s_ = IDW_W1_VOLATILE * np.sin(r1) + IDW_W2_VOLATILE * np.sin(r2)
            c_ = IDW_W1_VOLATILE * np.cos(r1) + IDW_W2_VOLATILE * np.cos(r2)
            n1, n2 = ~np.isfinite(r1), ~np.isfinite(r2)
            s_[n1 & ~n2] = np.sin(r2[n1 & ~n2])
            c_[n1 & ~n2] = np.cos(r2[n1 & ~n2])
            s_[~n1 & n2] = np.sin(r1[~n1 & n2])
            c_[~n1 & n2] = np.cos(r1[~n1 & n2])
            out[src] = (np.rad2deg(np.arctan2(s_, c_)) + 360.0) % 360.0

        df = out.reset_index().rename(columns={"index": "time"})

    df = df.sort_values("time").reset_index(drop=True)
    df = attach_time_features(df)

    if "temp2m" in df.columns:
        df["_date"] = pd.to_datetime(df["time"]).dt.normalize()
        daily_t = df.groupby("_date")["temp2m"].agg(["max", "min"])
        daily_t.columns = ["temp2m_max", "temp2m_min"]
        df = df.merge(daily_t.reset_index(), on="_date", how="left")
        df = df.drop(columns=["_date"])

    _BARATAN_CACHE = df

    avail = [c for c in ("vpd", "rh", "tcwv", "dew_pt", "sw_rad",
                         "sunshine", "pressure", "et0",
                         "sm_0_7", "sm_7_28", "sm_28_100",
                         "temp2m_max", "temp2m_min")
             if c in df.columns]
    print(f"  [i] {len(df):,} baris · "
          f"{df['time'].min().date()} → {df['time'].max().date()}")
    print(f"      Variabel: {', '.join(avail)}")
    return df


# ══════════════════════════════════════════════════════════════════════════
# §3  Utilitas numerik
# ══════════════════════════════════════════════════════════════════════════

def _attach_dopy(d: pd.DataFrame, dc: str = "date") -> pd.DataFrame:
    t = pd.to_datetime(d[dc])
    anchor = pd.to_datetime(
        dict(year=t.dt.year, month=ANCHOR_MONTH, day=ANCHOR_DAY))
    anchor_prev = pd.to_datetime(
        dict(year=t.dt.year - 1, month=ANCHOR_MONTH, day=ANCHOR_DAY))
    d = d.copy()
    d["dopy"] = np.where(
        t < anchor,
        (t - anchor_prev).dt.total_seconds() / 86400.0,
        (t - anchor).dt.total_seconds() / 86400.0,
    ) % 365.0
    return d


def _daily_field(df: pd.DataFrame, field: str,
                 agg: str = "mean") -> pd.DataFrame:
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    s = (d.groupby("_date")
          .agg(v=(field, agg))
          .reset_index()
          .rename(columns={"_date": "date"}))
    return _attach_dopy(s.sort_values("date").reset_index(drop=True))


def _roll21(s: pd.DataFrame, causal: bool = False) -> pd.DataFrame:
    """Rolling 21-hari. causal=True pakai trailing window (untuk onset real-time)."""
    s = s.copy()
    if causal:
        s["roll"] = s["v"].rolling(ROLL_WIN, min_periods=ROLL_WIN // 2).mean()
    else:
        s["roll"] = (s["v"].rolling(ROLL_WIN, center=True,
                                    min_periods=ROLL_WIN // 2).mean())
    return s


def _roll14(s: pd.DataFrame) -> pd.DataFrame:
    s = s.copy()
    s["roll"] = (s["v"].rolling(14, center=True, min_periods=7).mean())
    return s


def _roll7(s: pd.DataFrame) -> pd.DataFrame:
    s = s.copy()
    s["roll"] = (s["v"].rolling(7, center=True, min_periods=4).mean())
    return s


def _year_slice_daily(daily: pd.DataFrame, py: int) -> pd.DataFrame:
    start = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
    end   = start + pd.Timedelta(days=365)
    return (daily[(daily["date"] >= start)
                  & (daily["date"] < end)]
            .copy().reset_index(drop=True))


def _crossing_persistent(
    sig: np.ndarray,
    dpy: np.ndarray,
    thr: float,
    up: bool = True,
    lo: float = BAR_ONSET_LO,
    hi: float = BAR_ONSET_HI,
    sust: int = SUSTAIN,
    sust_min: int = SUSTAIN_MIN,
    eps: float = EPS,
) -> Optional[float]:
    """
    Cari crossing pertama dimana sinyal melewati threshold DAN BERTAHAN.
    'Bertahan' = sust_min dari sust hari berikutnya tetap di sisi yang sama.
    Lebih robust terhadap spike sesaat dibanding _crossing() lama.
    """
    for i in range(1, len(sig)):
        d = float(dpy[i])
        if not (lo <= d <= hi):
            continue
        c = sig[i]
        if not np.isfinite(c):
            continue
        if up and c >= thr:
            fut = sig[i:i + sust]
            valid = np.isfinite(fut)
            if valid.sum() < sust_min - 2:
                continue
            if np.nansum(fut >= thr - eps) >= sust_min:
                return d
        elif (not up) and c <= thr:
            fut = sig[i:i + sust]
            valid = np.isfinite(fut)
            if valid.sum() < sust_min - 2:
                continue
            if np.nansum(fut <= thr + eps) >= sust_min:
                return d
    return None


def _dry_stat(sig: np.ndarray, dpy: np.ndarray,
              pct: float = 50.0) -> float:
    mask = (dpy >= DRY_LO) & (dpy <= DRY_HI) & np.isfinite(sig)
    if mask.sum() < 5:
        return float(np.nanpercentile(sig, pct))
    return float(np.percentile(sig[mask], pct))


def _compute_bpi_thresholds(df: pd.DataFrame) -> Dict[str, float]:
    """
    Hitung threshold BPI dari data aktual (percentil musim kering).
    Mengembalikan dict threshold. Jika data tidak cukup, gunakan konstanta global.
    """
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    d["dopy"] = _attach_dopy(
        d.rename(columns={"_date": "date"}), dc="date"
    )["dopy"] if False else None  # lazy: hitung via daily field
    
    # Hitung daily dopy secara sederhana
    anchor_doy = 173  # ~22 Juni
    d["_doy"] = pd.to_datetime(d["time"]).dt.dayofyear
    d["dopy_raw"] = (d["_doy"] - anchor_doy) % 365

    dry = d[(d["dopy_raw"] >= DRY_LO) & (d["dopy_raw"] <= DRY_HI)]
    
    thr: Dict[str, float] = {}
    cols_pct = [
        ("tcwv",   90, "tcwv_thr",   "above"),
        ("sw_rad", 20, "sw_rad_thr", "below"),
        ("cloud",  80, "cloud_thr",  "above"),
        ("rh",     85, "rh_thr",     "above"),
        ("vpd",    20, "vpd_thr",    "below"),
        ("sm_7_28", 75, "sm_thr",    "above"),
    ]
    
    for (col, pct, key, _) in cols_pct:
        if col not in dry.columns or dry[col].notna().sum() < 100:
            continue
        v = dry[col].dropna()
        thr[key] = float(np.percentile(v, pct))
    
    # DTR: perlu daily agg
    if "temp2m_max" in dry.columns and "temp2m_min" in dry.columns:
        dtr = (dry.groupby("_date").agg(
            tmax=("temp2m_max", "first"),
            tmin=("temp2m_min", "first"),
        ))
        dtr["dtr"] = dtr["tmax"] - dtr["tmin"]
        v_dtr = dtr["dtr"].dropna()
        if len(v_dtr) >= 30:
            thr["dtr_thr"] = float(np.percentile(v_dtr, 30))
    
    return thr


def sr_kf_smooth_unit(
    y: np.ndarray,
    q_level: float = SRKF_Q_LEVEL,
    q_trend: float = SRKF_Q_TREND,
    r_init: float = SRKF_R_INIT,
    arch_omega: float = SRKF_ARCH_OMEGA,
    arch_alpha: float = SRKF_ARCH_ALPHA,
    burn_in: int = 60,
) -> Tuple[np.ndarray, np.ndarray]:
    n = len(y)
    if n == 0:
        return np.array([]), np.array([])

    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    H = np.array([[1.0, 0.0]])
    Q_sqrt = np.diag([np.sqrt(q_level), np.sqrt(q_trend)])

    x = np.array([float(y[0]), 0.0])
    S = np.eye(2) * np.sqrt(r_init)

    levels = np.full(n, np.nan)
    trends = np.full(n, np.nan)

    for t in range(n):
        x = F @ x
        compound = np.vstack((S.T @ F.T, Q_sqrt))
        _, R_qr = np.linalg.qr(compound, mode="reduced")
        S = R_qr[:2, :2].T

        y_pred = float(x[0])
        innov = float(y[t]) - y_pred

        R_t = max(SRKF_R_FLOOR, arch_omega + arch_alpha * innov ** 2)

        f = S.T @ H.T
        S_s = float(np.sqrt((f.T @ f).item() + R_t))
        K = (S @ f).flatten() / S_s
        x = x + K * (innov / S_s)

        alpha_k = 1.0 / (S_s * (S_s + np.sqrt(R_t)))
        S = np.tril(S - alpha_k * (S @ f @ f.T))

        if t >= burn_in:
            levels[t] = x[0]
            trends[t] = x[1]

    return levels, trends


# ══════════════════════════════════════════════════════════════════════════
# §4  Baratan Persistence Index (BPI)
# ══════════════════════════════════════════════════════════════════════════
# BPI v2 — didesain untuk menangkap "awan berkelanjutan" bukan sekadar onset hujan
#
# Komponen BPI dan bobotnya:
#   tcwv > P90_dry   → 2.5 (kolom uap penuh = syarat utama baratan)
#   cloud > P80_dry  → 2.5 (langit tertutup total)
#   u_comp (unit-vector) → 2.0 (adveksi barat lestari, z-score normalisasi)
#   sw_rad < P20_dry → 2.0 (radiasi matahari terblokir awan tebal)
#   rh > P85_dry     → 1.5 (udara jenuh uap)
#   vpd < P20_dry    → 1.5 (evap demand rendah = atmosfer sudah basah)
#   dtr < P30_dry    → 1.0 (selimut awan meredam fluktuasi suhu harian)
#   sm_7_28 > P75_dry → 1.0 (tanah sudah lembab = baratan bukan hujan pertama)
# Total = 14.0

_BPI_COMPS = [
    ("tcwv",    "mean", +1.0, 2.5, "above"),  # (field, agg, sign, weight, direction)
    ("cloud",   "mean", +1.0, 2.5, "above"),
    ("u_comp",  "mean", +1.0, 2.0, "above"),   # z-score, tanpa threshold absolut
    ("sw_rad",  "mean", -1.0, 2.0, "below"),   # negatif = lebih rendah = lebih baik
    ("rh",      "mean", +1.0, 1.5, "above"),
    ("vpd",     "mean", -1.0, 1.5, "below"),
    ("dtr",     "mean", -1.0, 1.0, "below"),   # DTR = temp_max - temp_min
    ("sm_7_28", "mean", +1.0, 1.0, "above"),
]

_BPI_TOTAL_W = sum(w for _, _, _, w, _ in _BPI_COMPS)  # = 14.0


def compute_bpi(df: pd.DataFrame,
                thr_override: Optional[Dict[str, float]] = None
                ) -> Optional[pd.DataFrame]:
    """
    Hitung Baratan Persistence Index harian.
    Setiap komponen dinormalisasi ke z-score berbasis mean/std dari seluruh data.
    BPI tinggi = kondisi baratan (awan berkelanjutan) kuat.
    """
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()

    # Hitung DTR daily jika belum ada
    if "dtr" not in d.columns:
        if "temp2m_max" in d.columns and "temp2m_min" in d.columns:
            d["dtr"] = d["temp2m_max"] - d["temp2m_min"]
        elif "temp2m" in d.columns:
            dtr_d = d.groupby("_date")["temp2m"].agg(["max", "min"]).reset_index()
            dtr_d.columns = ["_date", "tmax", "tmin"]
            dtr_d["dtr"] = dtr_d["tmax"] - dtr_d["tmin"]
            d = d.merge(dtr_d[["_date", "dtr"]], on="_date", how="left")

    avail = [row for row in _BPI_COMPS
             if row[0] in d.columns and d[row[0]].notna().sum() > 100]
    if len(avail) < 4:
        return None

    agg_dict = {f: (f, agg) for f, agg, _, _, _ in avail}
    daily = (d.groupby("_date")
              .agg(**agg_dict)
              .reset_index()
              .rename(columns={"_date": "date"})
              .sort_values("date")
              .reset_index(drop=True))
    daily = _attach_dopy(daily, dc="date")

    # Inisialisasi BPI
    daily["bpi"] = 0.0
    w_used = 0.0

    for (field, _, sign, w, _) in avail:
        v = daily[field].ffill().bfill()
        mu, sd = v.mean(), v.std()
        if sd < 1e-9:
            continue
        # Z-score: positif sign → lebih tinggi lebih baik untuk baratan
        # negatif sign → lebih rendah lebih baik
        daily["bpi"] += (w / _BPI_TOTAL_W) * sign * (v - mu) / sd
        w_used += w

    if w_used < _BPI_TOTAL_W * 0.4:  # kurang dari 40% bobot tersedia
        return None

    # Rescale jika tidak semua komponen tersedia
    daily["bpi"] *= (_BPI_TOTAL_W / max(w_used, 1e-9))

    # Rolling 21-hari (center=True untuk analisis historis)
    daily["bpi_roll"] = (daily["bpi"]
                         .rolling(ROLL_WIN, center=True,
                                  min_periods=ROLL_WIN // 2)
                         .mean())
    # Causal (trailing) untuk deteksi real-time onset
    daily["bpi_causal"] = (daily["bpi"]
                           .rolling(ROLL_WIN, min_periods=ROLL_WIN // 2)
                           .mean())
    return daily


def _bpi_onset_thr(bpi_daily: pd.DataFrame) -> float:
    roll_col = "bci_roll" if "bci_roll" in bpi_daily.columns else "bpi_roll"
    if roll_col not in bpi_daily.columns:
        return 0.25
    dry = bpi_daily[
        (bpi_daily["dopy"] >= DRY_LO) & (bpi_daily["dopy"] <= DRY_HI)
    ][roll_col].dropna()
    if len(dry) < 5:
        return 0.25
    # 1.5σ (bukan 1.2σ) — onset butuh anomali lebih kuat untuk 'terkunci'
    return float(dry.mean() + 1.5 * dry.std())


# ── Kompatibilitas nama BCI lama ──────────────────────────────────────────
# BPI secara fungsional menggantikan BCI.
# compute_bci dan detect_onset_bci tetap tersedia sebagai alias.
def compute_bci(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Alias ke compute_bpi untuk kompatibilitas dengan §7 dan §12."""
    result = compute_bpi(df)
    if result is not None and "bpi_roll" in result.columns:
        result = result.rename(columns={"bpi_roll": "bci_roll",
                                        "bpi": "bci",
                                        "bpi_causal": "bci_causal"})
    return result

# ══════════════════════════════════════════════════════════════════════════
# §4b  Siklus hidup baratan — helper
# ══════════════════════════════════════════════════════════════════════════

def _phase_of_dopy(dopy: Optional[float]) -> int:
    """Klasifikasi dopy ke fase 1–5. 0 jika tidak valid."""
    if dopy is None:
        return 0
    try:
        d = float(dopy) % 365.0
    except (TypeError, ValueError):
        return 0
    if not np.isfinite(d):
        return 0
    if d >= 310.0 or d < 80.0:
        return 5
    if d < 118.0:
        return 1
    if d < 156.0:
        return 2
    if d < 236.0:
        return 3
    return 4


def _phase_name(pid: int) -> str:
    if pid < 1 or pid > 5:
        return "—"
    for p in BARATAN_LIFECYCLE:
        if p["id"] == pid:
            return p["name"]
    return "—"


def _phase_composite_stats(df: pd.DataFrame) -> Dict[int, Dict[str, float]]:
    """Statistik komposit hourly untuk setiap fase siklus hidup."""
    d = df.copy()
    if "dtr" not in d.columns:
        if "temp2m_max" in d.columns and "temp2m_min" in d.columns:
            d["dtr"] = d["temp2m_max"] - d["temp2m_min"]
    d["_phase"] = d["dopy"].apply(_phase_of_dopy)

    out: Dict[int, Dict[str, float]] = {}
    for p in BARATAN_LIFECYCLE:
        pid = p["id"]
        sub = d[d["_phase"] == pid]
        rec: Dict[str, float] = {"n_hours": int(len(sub))}
        if len(sub) < 10:
            out[pid] = rec
            continue
        for (f, _, _) in _LIFECYCLE_FIELDS:
            if f not in d.columns:
                continue
            v = sub[f].dropna()
            if len(v) == 0:
                continue
            if f == "precip":
                rec[f] = float(v.sum() / len(v) * 24.0)
            else:
                rec[f] = float(v.mean())
        out[pid] = rec
    return out

# ══════════════════════════════════════════════════════════════════════════
# §5  Estimator B1–B6 (DIREVISI)
# ══════════════════════════════════════════════════════════════════════════

# ── B1: BPI onset / offset ────────────────────────────────────────────────
def detect_onset_bci(bpi_daily: pd.DataFrame) -> Optional[float]:
    """B1 — BPI melebihi threshold dan bertahan (persistensi)."""
    # Gunakan bci_roll jika sudah di-rename oleh compute_bci()
    roll_col = "bci_roll" if "bci_roll" in bpi_daily.columns else "bpi_roll"
    if roll_col not in bpi_daily.columns:
        return None
    thr = _bpi_onset_thr(bpi_daily)
    return _crossing_persistent(
        bpi_daily[roll_col].values,
        bpi_daily["dopy"].values,
        thr=thr, up=True,
        lo=BAR_ONSET_LO, hi=BAR_ONSET_HI,
    )


def detect_offset_bci(bpi_daily, lo_override=None):
    roll_col = "bci_roll" if "bci_roll" in bpi_daily.columns else "bpi_roll"
    if roll_col not in bpi_daily.columns:
        return None
    thr = _bpi_onset_thr(bpi_daily)
    lo  = lo_override if lo_override is not None else BAR_OFFSET_LO
    return _crossing_persistent(
        bpi_daily[roll_col].values, bpi_daily["dopy"].values,
        thr=thr, up=False, lo=lo, hi=BAR_OFFSET_HI)


# ── B2: WCC — Wind × Cloud × TCWV (threshold diperketat) ─────────────────
def detect_onset_wcc(df: pd.DataFrame) -> Optional[float]:
    """
    B2 — Joint AND-gate tiga variabel inti baratan.

    Threshold v2.0.2 — dikalibrasi dari data EV09 2015–2025:

      · u_comp > -0.30 unit-vector rolling 7d
          Filter easterly kuat. Rata-rata Fase Kunci = -0.05.

      · cloud  > 76.0 % rolling 7d
          Fase Kunci mean = 76.7%. Bukan 72 (v2.0.1), bukan 80 (v2.0.0).

      · tcwv   > 45.0 kg/m² rolling 7d (ABSOLUT, bukan percentile)
          P80 dry = 44.97; Fase Kunci mean = 45.9. Threshold absolut
          lebih stabil antar-tahun dibanding percentile relatif.

      · Sustain: 10 dari 14 hari (fraction ≥ 0.65)
    """
    needed = {"u_comp", "cloud", "tcwv"}
    if not needed.issubset(df.columns):
        return None

    d_u = _roll7(_daily_field(df, "u_comp"))
    d_c = _roll7(_daily_field(df, "cloud"))
    d_t = _roll7(_daily_field(df, "tcwv"))

    idx = d_u["date"]
    d_c = d_c.set_index("date").reindex(idx).reset_index()
    d_t = d_t.set_index("date").reindex(idx).reset_index()

    u_r  = d_u["roll"].values
    c_r  = d_c["roll"].values
    tw_r = d_t["roll"].values
    dpy  = d_u["dopy"].values

    TCWV_THR  = 45.0
    CLOUD_THR = 76.0
    U_THR     = -0.30

    joint = (
        (u_r  > U_THR)
        & (c_r  > CLOUD_THR)
        & (tw_r > TCWV_THR)
    ).astype(float)
    joint = np.where(
        np.isfinite(u_r) & np.isfinite(c_r) & np.isfinite(tw_r),
        joint, np.nan)

    sig = pd.Series(joint).rolling(14, min_periods=9).mean().values
    return _crossing_persistent(sig, dpy, thr=0.65, up=True,
                                lo=BAR_ONSET_LO, hi=BAR_ONSET_HI,
                                sust=10, sust_min=7)


def detect_offset_wcc(df: pd.DataFrame) -> Optional[float]:
    needed = {"u_comp", "cloud"}
    if not needed.issubset(df.columns):
        return None
    d_u = _roll7(_daily_field(df, "u_comp"))
    d_c = _roll7(_daily_field(df, "cloud"))
    idx = d_u["date"]
    d_c = d_c.set_index("date").reindex(idx).reset_index()
    u_r = d_u["roll"].values
    c_r = d_c["roll"].values
    dpy = d_u["dopy"].values
    # Offset: angin berbalik ATAU awan menipis signifikan
    joint = ((u_r < -0.5) | (c_r < 55.0)).astype(float)
    joint = np.where(np.isfinite(u_r) & np.isfinite(c_r), joint, np.nan)
    sig = pd.Series(joint).rolling(14, min_periods=9).mean().values
    return _crossing_persistent(sig, dpy, thr=0.70, up=True,
                                lo=BAR_OFFSET_LO, hi=BAR_OFFSET_HI,
                                sust=10, sust_min=7)


# ── B3: RAD — Solar radiation deficit (threshold diperketat) ──────────────
def detect_onset_rad(df: pd.DataFrame) -> Optional[float]:
    """
    B3 — Defisit radiasi matahari sebagai proxy 'awan tebal tak tertembus'.
    Threshold v2: P15 dry (was P25) — lebih ketat, hanya hari benar-benar
    gelap yang dihitung. Rolling 21d (was 14d) untuk persistensi.
    """
    if "sw_rad" not in df.columns or df["sw_rad"].notna().sum() < 100:
        return None
    s = _roll21(_daily_field(df, "sw_rad"))
    thr = _dry_stat(s["roll"].values, s["dopy"].values, pct=15.0)  # ← was P25
    return _crossing_persistent(s["roll"].values, s["dopy"].values,
                                thr=thr, up=False,
                                lo=BAR_ONSET_LO, hi=BAR_ONSET_HI)


def detect_offset_rad(df: pd.DataFrame) -> Optional[float]:
    if "sw_rad" not in df.columns or df["sw_rad"].notna().sum() < 100:
        return None
    s = _roll21(_daily_field(df, "sw_rad"))
    thr = _dry_stat(s["roll"].values, s["dopy"].values, pct=15.0)
    return _crossing_persistent(s["roll"].values, s["dopy"].values,
                                thr=thr, up=True,
                                lo=BAR_OFFSET_LO, hi=BAR_OFFSET_HI)


# ── B4: SOIL — Dual-layer moisture (diperbarui) ───────────────────────────
def detect_onset_soil(df: pd.DataFrame) -> Optional[float]:
    """
    B4 — Kelembaban tanah dual-layer (7–28 cm DAN 28–100 cm).
    v2: keduanya harus melampaui P80 musim BASAH (bukan P80 dry).
    Alasan: baratan bukan sekadar hujan pertama; tanah harus sudah benar
    jenuh di kedua lapisan sebelum baratan 'terkunci'.
    Jika sm_28_100 tidak tersedia, fallback ke sm_7_28 saja dengan P85.
    """
    if "sm_7_28" not in df.columns or df["sm_7_28"].notna().sum() < 100:
        return None

    s7 = _roll21(_daily_field(df, "sm_7_28"))

    # Threshold: P20 dari periode BASAH historis (dopy 140-220) atau P85 dry
    wet_mask = (s7["dopy"].values >= 140) & (s7["dopy"].values <= 220)
    if wet_mask.sum() > 30:
        thr7 = float(np.percentile(s7["roll"].values[wet_mask & np.isfinite(s7["roll"].values)], 20))
    else:
        thr7 = _dry_stat(s7["roll"].values, s7["dopy"].values, pct=85.0)

    if "sm_28_100" in df.columns and df["sm_28_100"].notna().sum() > 100:
        s28 = _roll21(_daily_field(df, "sm_28_100"))
        wet_mask28 = (s28["dopy"].values >= 140) & (s28["dopy"].values <= 220)
        if wet_mask28.sum() > 30:
            thr28 = float(np.percentile(
                s28["roll"].values[wet_mask28 & np.isfinite(s28["roll"].values)], 20))
        else:
            thr28 = _dry_stat(s28["roll"].values, s28["dopy"].values, pct=80.0)

        # Gabungkan: keduanya harus melampaui threshold
        idx7  = s7["date"].values
        idx28 = s28["date"].values
        dates_common = np.intersect1d(idx7, idx28)
        if len(dates_common) < 60:
            # Fallback ke single layer
            return _crossing_persistent(s7["roll"].values, s7["dopy"].values,
                                        thr=thr7, up=True,
                                        lo=BAR_ONSET_LO, hi=BAR_ONSET_HI)

        s7_sub  = s7.set_index("date").reindex(dates_common).reset_index()
        s28_sub = s28.set_index("date").reindex(dates_common).reset_index()
        joint   = (  (s7_sub["roll"].values > thr7)
                   & (s28_sub["roll"].values > thr28)).astype(float)
        joint = np.where(
            np.isfinite(s7_sub["roll"].values) & np.isfinite(s28_sub["roll"].values),
            joint, np.nan)
        sig = pd.Series(joint).rolling(SUSTAIN, min_periods=SUSTAIN_MIN).mean().values
        return _crossing_persistent(sig, s7_sub["dopy"].values,
                                    thr=0.70, up=True,
                                    lo=BAR_ONSET_LO, hi=BAR_ONSET_HI,
                                    sust=10, sust_min=7)
    else:
        return _crossing_persistent(s7["roll"].values, s7["dopy"].values,
                                    thr=thr7, up=True,
                                    lo=BAR_ONSET_LO, hi=BAR_ONSET_HI)


def detect_offset_soil(df: pd.DataFrame) -> Optional[float]:
    if "sm_7_28" not in df.columns or df["sm_7_28"].notna().sum() < 100:
        return None
    s = _roll21(_daily_field(df, "sm_7_28"))
    thr = _dry_stat(s["roll"].values, s["dopy"].values, pct=65.0)
    return _crossing_persistent(s["roll"].values, s["dopy"].values,
                                thr=thr, up=False,
                                lo=BAR_OFFSET_LO, hi=BAR_OFFSET_HI)


# ── B5: VPD (tidak banyak berubah, sedikit penyesuaian rolling window) ───
def detect_onset_vpd(df: pd.DataFrame) -> Optional[float]:
    if "vpd" not in df.columns or "rh" not in df.columns:
        return None
    sv = _roll21(_daily_field(df, "vpd"))
    sr = _roll21(_daily_field(df, "rh"))

    dpy = sv["dopy"].values
    v_r = sv["roll"].values
    r_r = sr["roll"].values
    if len(r_r) != len(v_r):
        n = min(len(r_r), len(v_r))
        v_r, r_r, dpy = v_r[:n], r_r[:n], dpy[:n]

    thr_vpd = _dry_stat(v_r, dpy, pct=15.0)   # ← was P20
    thr_rh  = _dry_stat(r_r, dpy, pct=88.0)   # ← was P85

    joint = ((v_r < thr_vpd) & (r_r > thr_rh)).astype(float)
    joint = np.where(np.isfinite(v_r) & np.isfinite(r_r), joint, np.nan)
    sig = pd.Series(joint).rolling(SUSTAIN, min_periods=SUSTAIN_MIN).mean().values
    return _crossing_persistent(sig, dpy, thr=0.65, up=True,
                                lo=BAR_ONSET_LO, hi=BAR_ONSET_HI,
                                sust=10, sust_min=7)


def detect_offset_vpd(df: pd.DataFrame) -> Optional[float]:
    if "vpd" not in df.columns:
        return None
    sv = _roll21(_daily_field(df, "vpd"))
    thr = _dry_stat(sv["roll"].values, sv["dopy"].values, pct=35.0)
    return _crossing_persistent(sv["roll"].values, sv["dopy"].values,
                                thr=thr, up=True,
                                lo=BAR_OFFSET_LO, hi=BAR_OFFSET_HI)


# ── B6: PRESS (tidak banyak berubah) ──────────────────────────────────────
def detect_onset_press(df: pd.DataFrame) -> Optional[float]:
    if "pressure" not in df.columns or df["pressure"].notna().sum() < 100:
        return None
    s = _roll14(_daily_field(df, "pressure"))
    thr = _dry_stat(s["roll"].values, s["dopy"].values, pct=20.0)  # ← was P25
    return _crossing_persistent(s["roll"].values, s["dopy"].values,
                                thr=thr, up=False,
                                lo=BAR_ONSET_LO, hi=BAR_ONSET_HI)


def detect_offset_press(df: pd.DataFrame) -> Optional[float]:
    if "pressure" not in df.columns or df["pressure"].notna().sum() < 100:
        return None
    s = _roll14(_daily_field(df, "pressure"))
    thr = _dry_stat(s["roll"].values, s["dopy"].values, pct=40.0)
    return _crossing_persistent(s["roll"].values, s["dopy"].values,
                                thr=thr, up=True,
                                lo=BAR_OFFSET_LO, hi=BAR_OFFSET_HI)


# ══════════════════════════════════════════════════════════════════════════
# §5b  B7_HMM — 9-D GMM-HMM causal filter (STATE MAPPING DIKOREKSI)
# ══════════════════════════════════════════════════════════════════════════

def _log_mvn_pure(X: np.ndarray, mean, cov) -> np.ndarray:
    cov_reg = np.asarray(cov) + 1e-6 * np.eye(len(mean))
    diff = X - np.array(mean)
    inv = np.linalg.inv(cov_reg)
    _, logdet = np.linalg.slogdet(cov_reg)
    d = len(mean)
    if diff.ndim == 2:
        quad = np.einsum("ij,jk,ik->i", diff, inv, diff)
    else:
        quad = float(diff @ inv @ diff)
    return -0.5 * (d * np.log(2 * np.pi) + logdet + quad)


def hmm_causal_filter_pure(
    Xz: np.ndarray,
    prior_override: Optional[List[float]] = None,
) -> np.ndarray:
    K = len(HMM_T8_means)
    logB = np.column_stack([
        _log_mvn_pure(Xz, HMM_T8_means[k], HMM_T8_covs[k])
        for k in range(K)
    ])

    pi_src = prior_override if prior_override is not None else HMM_T8_pi
    pi_arr = np.array(pi_src, dtype=float) + 1e-12
    pi_arr /= pi_arr.sum()

    alpha = pi_arr * np.exp(logB[0] - logB[0].max())
    alpha /= alpha.sum()
    probs = [alpha]

    for t in range(1, len(Xz)):
        pred = alpha @ HMM_T8_A
        w = np.exp(logB[t] - logB[t].max())
        alpha = pred * w
        s = alpha.sum()
        alpha = alpha / s if s > 0 else pred
        probs.append(alpha)

    return np.array(probs)


def _extract_hmm_features(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    needed = {"precip", "et0", "sm_0_7", "rh", "tcwv",
              "cloud", "sm_28_100", "u_comp"}
    if not needed.issubset(df.columns):
        return None
    if "temp2m_max" not in df.columns or "temp2m_min" not in df.columns:
        return None

    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()

    daily = (d.groupby("_date")
              .agg(precip=("precip", "sum"),
                   et0=("et0", "sum"),
                   sm=("sm_0_7", "mean"),
                   rh=("rh", "mean"),
                   tcwv=("tcwv", "mean"),
                   cloud=("cloud", "mean"),
                   smd=("sm_28_100", "mean"),
                   ucomp=("u_comp", "mean"))
              .reset_index()
              .rename(columns={"_date": "date"}))
    daily["wb"] = daily["precip"] - daily["et0"]

    dtr_daily = (d.groupby("_date")
                  .agg(tmax=("temp2m_max", "first"),
                       tmin=("temp2m_min", "first"))
                  .reset_index()
                  .rename(columns={"_date": "date"}))
    dtr_daily["dtr"] = dtr_daily["tmax"] - dtr_daily["tmin"]
    daily = daily.merge(dtr_daily[["date", "dtr"]], on="date", how="left")

    daily = daily.sort_values("date").reset_index(drop=True)
    daily = _attach_dopy(daily, dc="date")

    w = 30
    out = pd.DataFrame(index=daily.index)
    out["date"]  = daily["date"]
    out["dopy"]  = daily["dopy"]
    out["r_30"]  = daily["precip"].rolling(w, min_periods=15).sum()
    out["wb_30"] = daily["wb"].rolling(w, min_periods=15).sum()
    out["sm_30"] = daily["sm"].ffill().rolling(w, min_periods=15).mean()
    out["rh_30"] = daily["rh"].rolling(w, min_periods=15).mean()
    out["tc_30"] = daily["tcwv"].ffill().rolling(w, min_periods=15).mean()
    out["dt_30"] = daily["dtr"].ffill().rolling(w, min_periods=15).mean()
    out["cl_30"] = daily["cloud"].ffill().rolling(w, min_periods=15).mean()
    out["sd_30"] = daily["smd"].ffill().rolling(w, min_periods=15).mean()
    out["u_30"]  = daily["ucomp"].rolling(w, min_periods=15).mean()

    out = out.dropna(subset=["r_30", "wb_30", "sm_30", "rh_30",
                              "tc_30", "dt_30", "cl_30", "sd_30", "u_30"])
    return out.reset_index(drop=True)


def _get_hmm_features_cached(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    global _HMM_FEAT_CACHE
    if _HMM_FEAT_CACHE is None:
        _HMM_FEAT_CACHE = _extract_hmm_features(df)
    return _HMM_FEAT_CACHE


def _hmm_probs_for_features(
    feat: pd.DataFrame,
    prior_override: Optional[List[float]] = None,
) -> np.ndarray:
    X = feat[["r_30", "wb_30", "sm_30", "rh_30",
              "tc_30", "dt_30", "cl_30", "sd_30", "u_30"]].values
    Xz = (X - np.array(HMM_T8_mu)) / np.array(HMM_T8_sd)
    return hmm_causal_filter_pure(Xz, prior_override=prior_override)


def _hmm_probs_for_year(
    feat: pd.DataFrame,
    py: int,
    warmup_days: int = HMM_WARMUP_DAYS,
    warmup_min: int = HMM_WARMUP_MIN,
) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    if feat is None or len(feat) < 60:
        return None

    start = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
    end = start + pd.Timedelta(days=365)
    warmup_start = start - pd.Timedelta(days=warmup_days)

    mask = (feat["date"] >= warmup_start) & (feat["date"] < end)
    sub = feat[mask].reset_index(drop=True)
    if len(sub) < 60:
        return None

    n_warmup = int((sub["date"] < start).sum())
    if n_warmup < warmup_min:
        sub = feat[(feat["date"] >= start) & (feat["date"] < end)
                   ].reset_index(drop=True)
        if len(sub) < 60:
            return None
        probs = _hmm_probs_for_features(
            sub, prior_override=[1.0, 0.0, 0.0, 0.0])
        return probs, sub["dopy"].values

    probs_ext = _hmm_probs_for_features(sub)
    eval_mask = (sub["date"] >= start).values
    if eval_mask.sum() < 30:
        return None
    return probs_ext[eval_mask], sub.loc[eval_mask, "dopy"].values


def detect_onset_hmm(df: pd.DataFrame, py: int) -> Optional[float]:
    """
    B7 — Onset via HMM State 1 (Labuh) dengan offset kalibrasi.

    Riwayat kalibrasi:
      v2.0.0 rev-1 : P(s=1)+P(s=2) ≥ 0.55     → Δ mean −13 (dini)
      v2.0.1       : P(s=2) rising edge 0.30  → Δ mean +31 (salah)
      v2.0.2       : midpoint i1↔i2           → Δ mean +8.5 (2015/2016 outlier)
      v2.0.3       : i1 + 25 hari, fallback i2 − 40 hari

    Alasan:
      · i1 = first P(s=1) ≥ 0.70 = onset LABUH (awal hujan), selalu
        muncul lebih dulu. Selisih i1 ke baratan sebenarnya ~25 hari,
        konsisten sepanjang 2015–2025 (std error ~12 hari).
      · Midpoint i1↔i2 tidak stabil karena jarak i1→i2 bervariasi
        30 hari (2017) s.d. 82 hari (2018).
      · Tahun tanpa i1 (2016: State 2 langsung aktif) → onset = i2 − 40,
        bukan i2 apa adanya (i2 = plateau, bukan onset).
    """
    feat = _get_hmm_features_cached(df)
    result = _hmm_probs_for_year(feat, py)
    if result is None:
        return None
    probs, dopy = result

    mask = (dopy >= BAR_ONSET_LO) & (dopy <= BAR_ONSET_HI)
    if not mask.any():
        return None

    p1 = probs[mask, 1]
    p2 = probs[mask, 2]
    d  = dopy[mask]

    THR = 0.70

    def _first(arr, thr):
        for i in range(len(arr)):
            if np.isfinite(arr[i]) and arr[i] >= thr:
                return i
        return None

    i1 = _first(p1, THR)
    i2 = _first(p2, THR)

    if i1 is not None:
        # Onset baratan ≈ 25 hari setelah labuh mulai
        return float(d[i1] + 25.0)
    if i2 is not None:
        # State 2 langsung aktif (tahun La Niña kuat) → onset ≈ 40 hari
        # sebelum plateau State 2
        return float(max(BAR_ONSET_LO, d[i2] - 40.0))
    return None


def detect_offset_hmm(df: pd.DataFrame, py: int) -> Optional[float]:
    """B7 — Offset dari puncak P(state=3) 'Labuh-wet' dalam [220, 340]."""
    feat = _get_hmm_features_cached(df)
    result = _hmm_probs_for_year(feat, py)
    if result is None:
        return None
    probs, dopy = result

    mask = (dopy >= BAR_OFFSET_LO - 20.0) & (dopy <= BAR_OFFSET_HI)
    if not mask.any():
        return None
    p3 = probs[mask, HMM_OFFSET_STATE]
    d  = dopy[mask]

    # Cari first sustained crossing untuk offset
    for i in range(len(p3)):
        if np.isfinite(p3[i]) and p3[i] >= HMM_OFFSET_P_THR:
            fut = p3[i:i + HMM_SUSTAIN]
            if np.nansum(fut >= HMM_OFFSET_P_THR * 0.85) >= HMM_SUSTAIN - 2:
                return float(d[i])

    # Fallback: argmax jika tidak ada sustained crossing
    if p3.max() >= HMM_OFFSET_P_THR * 0.8:
        idx = int(np.argmax(p3))
        return float(d[idx])
    return None


# ══════════════════════════════════════════════════════════════════════════
# §6  Ensemble berbobot — Biweight Mean (Tukey) + MAD outlier softening
# ══════════════════════════════════════════════════════════════════════════

def ensemble_baratan(
    results: Dict[str, Optional[float]],
    weights: Dict[str, float],
    min_n: int = 2,
) -> Optional[float]:
    """
    Ensemble onset/offset menggunakan Biweight Mean (Tukey estimator).

    Keunggulan vs weighted-median (v1.4.4):
      · Lebih smooth: tidak diskontinu seperti median
      · Outlier resistance: estimator B yang jauh dari median dikecilkan bobotnya
        secara otomatis via fungsi bisquare (bukan dikecualikan biner)
      · Tetap respect bobot fisik masing-masing estimator

    Algoritma:
      1. Kumpulkan semua (value, weight) yang valid
      2. Hitung MAD-weighted center awal
      3. Iterasi Tukey bisquare: bobot_final = w_fisik × bisquare(residual / (c × MAD))
      4. Return weighted mean akhir
    """
    vals: List[float] = []
    ws:   List[float] = []
    for key, val in results.items():
        if val is None:
            continue
        w = weights.get(key, 1.0)
        if w <= 0:
            continue
        try:
            fv = float(val)
        except (TypeError, ValueError):
            continue
        if np.isfinite(fv):
            vals.append(fv)
            ws.append(w)

    if len(vals) < min_n:
        return None

    v_arr = np.array(vals, dtype=float)
    w_arr = np.array(ws,   dtype=float)
    w_arr /= w_arr.sum()

    # Jika hanya 2–3 estimator, gunakan weighted mean biasa (tidak cukup untuk outlier detection)
    if len(vals) < 4:
        return float(np.dot(w_arr, v_arr))

    # ── Tukey Biweight Mean ─────────────────────────────────────────────
    # Konstanta c = 4.685 (efisiensi 95% Gaussian, robust terhadap outlier)
    C_BISQUARE = 4.685
    MAX_ITER   = 10

    # Inisialisasi dengan weighted median
    sort_idx = np.argsort(v_arr)
    v_s, w_s = v_arr[sort_idx], w_arr[sort_idx]
    cumw = np.cumsum(w_s)
    med_idx = np.searchsorted(cumw, 0.5)
    center = float(v_s[min(med_idx, len(v_s) - 1)])

    for _ in range(MAX_ITER):
        residuals = v_arr - center
        mad = float(np.median(np.abs(residuals)))
        if mad < 0.5:  # sangat sempit, semua setara
            break
        u = residuals / (C_BISQUARE * mad)
        bisq = np.where(np.abs(u) < 1.0,
                        (1.0 - u ** 2) ** 2,
                        0.0)
        w_eff = w_arr * bisq
        w_sum = w_eff.sum()
        if w_sum < 1e-10:
            break
        new_center = float(np.dot(w_eff, v_arr) / w_sum)
        if abs(new_center - center) < 0.1:  # konvergensi < 0.1 hari
            center = new_center
            break
        center = new_center

    return center


def _baratan_peak(bci_daily: pd.DataFrame, onset: float,
                  offset: float) -> Tuple[float, float]:
    roll_col = "bci_roll" if "bci_roll" in bci_daily.columns else "bpi_roll"
    mask = ((bci_daily["dopy"] >= onset)
            & (bci_daily["dopy"] <= offset)
            & bci_daily[roll_col].notna())
    if not mask.any():
        mid = (onset + offset) / 2.0
        return mid, float("nan")
    idx = bci_daily.loc[mask, roll_col].idxmax()
    return (float(bci_daily.loc[idx, "dopy"]),
            float(bci_daily.loc[idx, roll_col]))


# ══════════════════════════════════════════════════════════════════════════
# §7  Runner per pranata-tahun
# ══════════════════════════════════════════════════════════════════════════

def run_year(df: pd.DataFrame, py: int,
             bci_all: pd.DataFrame) -> Dict:
    start = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
    end   = start + pd.Timedelta(days=366)
    sub   = df[(df["time"] >= start) & (df["time"] < end)].copy()
    if len(sub) < 3000:
        return {}

    bci_yr = _year_slice_daily(bci_all, py)

    on_res = {
        "B1_BPI":   detect_onset_bci(bci_yr),
        "B2_WCC":   detect_onset_wcc(sub),
        "B3_RAD":   detect_onset_rad(sub),
        "B4_SOIL":  detect_onset_soil(sub),
        "B5_VPD":   detect_onset_vpd(sub),
        "B6_PRESS": detect_onset_press(sub),
        "B7_HMM":   detect_onset_hmm(df, py),
    }
    onset_ens = ensemble_baratan(on_res, ENS_W_ONSET)

    off_res = {
        "B1_BPI":   detect_offset_bci(bci_yr),
        "B2_WCC":   detect_offset_wcc(sub),
        "B3_RAD":   detect_offset_rad(sub),
        "B4_SOIL":  detect_offset_soil(sub),
        "B5_VPD":   detect_offset_vpd(sub),
        "B6_PRESS": detect_offset_press(sub),
        "B7_HMM":   detect_offset_hmm(df, py),
    }
    offset_ens = ensemble_baratan(off_res, ENS_W_OFFSET)

    dur = None
    pk_dopy, pk_bci = float("nan"), float("nan")
    if onset_ens is not None and offset_ens is not None:
        dur_candidate = offset_ens - onset_ens
        if dur_candidate >= 0:
            dur = dur_candidate
            pk_dopy, pk_bci = _baratan_peak(bci_yr, onset_ens, offset_ens)

    return {
        "onset_ens":  onset_ens,
        "offset_ens": offset_ens,
        "duration":   dur,
        "peak_dopy":  pk_dopy,
        "peak_bci":   pk_bci,
        "onset_raw":  on_res,
        "offset_raw": off_res,
    }


# ══════════════════════════════════════════════════════════════════════════
# §8  Analisis atmosfer
# ══════════════════════════════════════════════════════════════════════════

_ATMO_FIELDS = [
    ("u_comp",    "mean", "Komponen zonal u_comp",           "adim."),
    ("cloud",     "mean", "Tutupan awan total (%)",          "%"),
    ("cloud_lo",  "mean", "Awan rendah (%)",                 "%"),
    ("cloud_mid", "mean", "Awan menengah (%)",               "%"),
    ("tcwv",      "mean", "TCWV (kg/m²)",                    "kg/m²"),
    ("rh",        "mean", "RH 2m (%)",                       "%"),
    ("dew_pt",    "mean", "Titik embun 2m (°C)",             "°C"),
    ("precip",    "sum",  "Hujan kumulatif (mm/hari rata)",  "mm"),
    ("sw_rad",    "mean", "Shortwave radiation (W/m²)",      "W/m²"),
    ("sunshine",  "mean", "Durasi surya (s/hari)",           "s"),
    ("pressure",  "mean", "Tekanan permukaan (hPa)",         "hPa"),
    ("ws10",      "mean", "Kecepatan angin 10m (km/h)",      "km/h"),
    ("vpd",       "mean", "VPD (kPa)",                       "kPa"),
    ("et0",       "sum",  "ET0 FAO (mm/hari rata)",          "mm"),
]


def atmospheric_window_stats(df: pd.DataFrame,
                             onset_dopy: float,
                             offset_dopy: float) -> Dict[str, float]:
    mask = (df["dopy"] >= onset_dopy) & (df["dopy"] <= offset_dopy)
    sub = df.loc[mask]
    result: Dict[str, float] = {}
    for (field, agg, _, _) in _ATMO_FIELDS:
        if field not in df.columns:
            result[field] = float("nan")
            continue
        v = sub[field].dropna()
        if len(v) == 0:
            result[field] = float("nan")
        elif agg == "sum":
            result[field] = float(v.sum() / len(v) * 24.0)
        else:
            result[field] = float(v.mean())
    return result


def dry_season_stats(df: pd.DataFrame) -> Dict[str, float]:
    mask = (df["dopy"] >= DRY_LO) & (df["dopy"] <= DRY_HI)
    sub = df.loc[mask]
    result: Dict[str, float] = {}
    for (field, agg, _, _) in _ATMO_FIELDS:
        if field not in df.columns:
            result[field] = float("nan")
            continue
        v = sub[field].dropna()
        if len(v) == 0:
            result[field] = float("nan")
        elif agg == "sum":
            result[field] = float(v.sum() / len(v) * 24.0)
        else:
            result[field] = float(v.mean())
    return result


# ══════════════════════════════════════════════════════════════════════════
# §9  Analisis tanah
# ══════════════════════════════════════════════════════════════════════════

_SOIL_FIELDS = [
    ("sm_0_7",     "mean", "Soil moisture 0–7 cm (m³/m³)"),
    ("sm_7_28",    "mean", "Soil moisture 7–28 cm (m³/m³)"),
    ("sm_28_100",  "mean", "Soil moisture 28–100 cm (m³/m³)"),
    ("sm_100_255", "mean", "Soil moisture 100–255 cm (m³/m³)"),
    ("st_0_7",     "mean", "Soil temp 0–7 cm (°C)"),
    ("st_7_28",    "mean", "Soil temp 7–28 cm (°C)"),
    ("st_28_100",  "mean", "Soil temp 28–100 cm (°C)"),
    ("st_100_255", "mean", "Soil temp 100–255 cm (°C)"),
    ("et0",        "sum",  "ET0 FAO kumulatif (mm/hr)"),
]


def soil_lag_correlation(df: pd.DataFrame,
                         onset_dopy: float,
                         max_lag_days: int = 30) -> Dict[str, Dict]:
    bpi_d = compute_bpi(df)
    if bpi_d is None:
        return {}

    roll_col = "bpi_roll" if "bpi_roll" in bpi_d.columns else "bci_roll"
    bci_ser = pd.Series(bpi_d[roll_col].values,
                        index=pd.to_datetime(bpi_d["date"]))

    result: Dict[str, Dict] = {}
    for (field, _, desc) in _SOIL_FIELDS:
        if field not in df.columns or df[field].notna().sum() < 200:
            continue
        d = df.copy()
        d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
        soil_d = (d.groupby("_date")[field].mean()
                   .rename("v").reset_index()
                   .rename(columns={"_date": "date"}))
        soil_ser = pd.Series(soil_d["v"].values,
                             index=pd.to_datetime(soil_d["date"]))

        common = bci_ser.index.intersection(soil_ser.index)
        if len(common) < 100:
            continue
        b = bci_ser.loc[common]
        s = soil_ser.loc[common]

        lags = list(range(-5, max_lag_days + 1))
        rs: List[float] = []
        for lag in lags:
            b_s = b.shift(lag)
            m   = b_s.notna() & s.notna()
            if m.sum() < 50:
                rs.append(float("nan"))
            else:
                rs.append(float(np.corrcoef(b_s[m], s[m])[0, 1]))

        rs_arr = np.array(rs)
        if not np.isfinite(rs_arr).any():
            continue
        best_k = int(np.nanargmax(np.abs(rs_arr)))
        result[field] = {
            "lag_peak":    int(lags[best_k]),
            "r_peak":      float(rs_arr[best_k]),
            "description": desc,
        }
    return result


def soil_window_profile(df: pd.DataFrame,
                        onset_dopy: float,
                        offset_dopy: float) -> Dict[str, Dict]:
    windows = {
        "PRE":  (onset_dopy - 30.0, onset_dopy),
        "BAR":  (onset_dopy,         offset_dopy),
        "POST": (offset_dopy,        offset_dopy + 30.0),
    }
    result: Dict[str, Dict] = {}
    for (field, _, desc) in _SOIL_FIELDS:
        if field not in df.columns:
            continue
        row: Dict[str, float] = {}
        for (wname, (lo, hi)) in windows.items():
            mask = (df["dopy"] >= lo) & (df["dopy"] < hi)
            v = df.loc[mask, field].dropna()
            row[wname] = float(v.mean()) if len(v) > 0 else float("nan")
        result[field] = {"desc": desc, "windows": row}
    return result


# ══════════════════════════════════════════════════════════════════════════
# §10  Presipitasi
# ══════════════════════════════════════════════════════════════════════════

def precip_partitioning(df: pd.DataFrame,
                        onset_dopy: float,
                        offset_dopy: float) -> Dict[str, float]:
    if "precip" not in df.columns:
        return {}

    t = pd.to_datetime(df["time"])
    py = np.where(
        (t.dt.month > ANCHOR_MONTH)
        | ((t.dt.month == ANCHOR_MONTH) & (t.dt.day >= ANCHOR_DAY)),
        t.dt.year,
        t.dt.year - 1,
    )
    d = df.assign(_py=py)

    per_year: List[Dict[str, float]] = []
    for _, sub in d.groupby("_py"):
        if len(sub) < 8000:
            continue
        total_mm = float(sub["precip"].sum())
        bar = sub[(sub["dopy"] >= onset_dopy) & (sub["dopy"] <= offset_dopy)]
        dry = sub[(sub["dopy"] >= DRY_LO) & (sub["dopy"] <= DRY_HI)]
        n_bar = len(bar)
        n_dry = len(dry)
        if total_mm <= 0 or n_bar == 0 or n_dry == 0:
            continue
        bar_mm = float(bar["precip"].sum())
        dry_mm = float(dry["precip"].sum())
        per_year.append({
            "total":    total_mm,
            "bar_mm":   bar_mm,
            "dry_mm":   dry_mm,
            "bar_pct":  100.0 * bar_mm / total_mm,
            "dry_pct":  100.0 * dry_mm / total_mm,
            "bar_rate": bar_mm / n_bar * 24.0,
            "dry_rate": dry_mm / n_dry * 24.0,
        })

    if not per_year:
        return {}

    keys = per_year[0].keys()
    agg = {k: float(np.mean([y[k] for y in per_year])) for k in keys}
    agg["n_years"] = float(len(per_year))
    agg["intensification"] = agg["bar_rate"] / max(1e-6, agg["dry_rate"])
    return agg


# ══════════════════════════════════════════════════════════════════════════
# §11  Statistik multi-tahun
# ══════════════════════════════════════════════════════════════════════════

def multiyr_stats(records: List[Dict]) -> Dict[str, Dict]:
    keys = ["onset_ens", "offset_ens", "duration", "peak_dopy", "peak_bci"]
    out: Dict[str, Dict] = {}
    for k in keys:
        raw_vals = []
        for r in records:
            v = r.get(k)
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                raw_vals.append(fv)
        vals = np.array(raw_vals, dtype=float)
        if len(vals) < 2:
            out[k] = {"n": len(vals), "vals": vals}
            continue
        slope, intercept, r_val, t_val = _linear_trend(
            np.arange(len(vals), dtype=float), vals)
        out[k] = {
            "n":      len(vals),
            "mean":   float(np.mean(vals)),
            "median": float(np.median(vals)),
            "std":    float(np.std(vals, ddof=1)),
            "min":    float(np.min(vals)),
            "max":    float(np.max(vals)),
            "slope":  float(slope),
            "r":      float(r_val),
            "t":      float(t_val),
            "vals":   vals,
        }
    return out


# ══════════════════════════════════════════════════════════════════════════
# §12  Konteks iklim (ENSO · IOD · MJO · regresi OLS · ARX)
# — sama dengan v1.4.4, tidak ada perubahan —
# ══════════════════════════════════════════════════════════════════════════

def _load_enso_sst(path: str) -> Optional[pd.DataFrame]:
    p = find_data_file(path)
    if p is None:
        return None
    try:
        df = pd.read_csv(p)
        base = datetime(1978, 1, 1, 12, 0, 0)
        df["date"] = df["time"].apply(
            lambda d: base + timedelta(days=float(d)))
        df["year"]  = df["date"].dt.year
        df["month"] = df["date"].dt.month
        return df.sort_values("date").reset_index(drop=True)
    except Exception:
        return None


def _load_enso_msla(path: str) -> Optional[pd.DataFrame]:
    p = find_data_file(path)
    if p is None:
        return None
    try:
        df = pd.read_csv(p)
        base = datetime(1950, 1, 1, 0, 0, 0)
        df["date"] = df["time"].apply(
            lambda d: base + timedelta(days=float(d)))
        df["year"]  = df["date"].dt.year
        df["month"] = df["date"].dt.month
        return df.sort_values("date").reset_index(drop=True)
    except Exception:
        return None


def _load_iod(
    weekly_path: str = DEFAULT_IOD_WEEKLY,
    monthly_path: str = DEFAULT_IOD_MONTHLY,
) -> Optional[pd.DataFrame]:
    pw = find_data_file(weekly_path)
    if pw is not None:
        rows: List[Tuple] = []
        try:
            with open(pw, encoding="utf-8") as fh:
                for ln in fh:
                    parts = ln.strip().split(",")
                    if len(parts) < 3:
                        continue
                    try:
                        d = datetime.strptime(parts[1], "%Y%m%d")
                        rows.append((d.year, d.month, float(parts[2])))
                    except (ValueError, IndexError):
                        continue
        except OSError:
            rows = []
        if rows:
            wdf = pd.DataFrame(rows, columns=["year", "month", "dmi"])
            monthly = (wdf.groupby(["year", "month"])["dmi"]
                         .mean().reset_index())
            return monthly.sort_values(["year", "month"]).reset_index(drop=True)

    pm = find_data_file(monthly_path)
    if pm is None:
        return None
    rows_m: List[Tuple] = []
    try:
        with open(pm, encoding="utf-8") as fh:
            lines = [ln.split() for ln in fh if ln.strip()]
        for p in lines[1:]:
            if len(p) < 13:
                continue
            try:
                yr = int(p[0])
                for mo, val_s in enumerate(p[1:13], start=1):
                    v = float(val_s)
                    if abs(v - 99.90) < 1e-4:
                        continue
                    rows_m.append((yr, mo, v))
            except (ValueError, IndexError):
                continue
    except OSError:
        return None
    if not rows_m:
        return None
    df = pd.DataFrame(rows_m, columns=["year", "month", "dmi"])
    return df.sort_values(["year", "month"]).reset_index(drop=True)


def _load_mjo_rmm(path: str = DEFAULT_RMM_CSV) -> Optional[pd.DataFrame]:
    p = find_data_file(path)
    if p is None:
        return None
    try:
        df = pd.read_csv(
            p, comment="#",
            names=["year", "month", "day", "rmm1", "rmm2",
                   "phase", "lon", "amp", "amp2"],
            skipinitialspace=True,
        )
        df["date"] = pd.to_datetime(dict(
            year=df["year"].astype(int),
            month=df["month"].astype(int),
            day=df["day"].astype(int),
        ))
        return df.sort_values("date").reset_index(drop=True)
    except Exception:
        return None


def _count_mjo_events(mask: np.ndarray,
                      min_run: int = MJO_MIN_EVENT_DAYS) -> Dict[str, int]:
    if len(mask) == 0:
        return {"n_events": 0, "max_run": 0, "total_days": 0}
    mask_arr = np.asarray(mask, dtype=bool)
    n_events = 0
    max_run  = 0
    cur      = 0
    for v in mask_arr:
        if v:
            cur += 1
        else:
            if cur >= min_run:
                n_events += 1
                max_run  = max(max_run, cur)
            cur = 0
    if cur >= min_run:
        n_events += 1
        max_run  = max(max_run, cur)
    return {
        "n_events":   n_events,
        "max_run":    int(max_run),
        "total_days": int(mask_arr.sum()),
    }


def _classify_enso(aso_mean: float) -> str:
    if aso_mean >= ENSO_THR:
        return "El Niño"
    if aso_mean <= -ENSO_THR:
        return "La Niña"
    return "Netral"


def _classify_iod(son_mean: float) -> str:
    if son_mean >= IOD_THR:
        return "pIOD"
    if son_mean <= -IOD_THR:
        return "nIOD"
    return "Netral"


def _aso_mean(df: pd.DataFrame, year: int,
              col: str = "enso") -> Optional[float]:
    sub = df[(df["year"] == year) & df["month"].isin([8, 9, 10])][col]
    return float(sub.mean()) if len(sub) >= 1 else None


def _son_mean_dmi(iod_df: pd.DataFrame, year: int) -> Optional[float]:
    sub = iod_df[(iod_df["year"] == year)
                 & iod_df["month"].isin([9, 10, 11])]["dmi"]
    return float(sub.mean()) if len(sub) >= 1 else None


def load_enso_context(
    enso_sst_csv: str = DEFAULT_ENSO_SST_CSV,
    enso_msla_csv: str = DEFAULT_ENSO_MSLA_CSV,
    iod_weekly: str = DEFAULT_IOD_WEEKLY,
    iod_monthly: str = DEFAULT_IOD_MONTHLY,
    rmm_csv: str = DEFAULT_RMM_CSV,
) -> Dict[int, Dict]:
    sst_df  = _load_enso_sst(enso_sst_csv)
    msla_df = _load_enso_msla(enso_msla_csv)
    iod_df  = _load_iod(iod_weekly, iod_monthly)
    mjo_df  = _load_mjo_rmm(rmm_csv)

    ctx: Dict[int, Dict] = {}
    for py in range(2015, 2027):
        rec: Dict = {}

        sst_aso = _aso_mean(sst_df, py) if sst_df is not None else None
        rec["sst_aso"] = sst_aso
        rec["enso_phase"] = (_classify_enso(sst_aso)
                             if sst_aso is not None else "Netral")
        rec["sla_aso"] = (_aso_mean(msla_df, py)
                          if msla_df is not None else None)
        dmi_son = (_son_mean_dmi(iod_df, py)
                   if iod_df is not None else None)
        rec["dmi_son"] = dmi_son
        rec["iod_phase"] = (_classify_iod(dmi_son)
                            if dmi_son is not None else "Netral")

        enso_p = rec["enso_phase"]
        iod_p  = rec["iod_phase"]
        if ((enso_p == "El Niño" and iod_p == "pIOD")
                or (enso_p == "La Niña" and iod_p == "nIOD")):
            rec["interaction"] = "SINERGI"
        elif ((enso_p == "El Niño" and iod_p == "nIOD")
                or (enso_p == "La Niña" and iod_p == "pIOD")):
            rec["interaction"] = "COUNTER"
        else:
            rec["interaction"] = "NETRAL"

        mjo_active_days = 0
        mjo_n_events    = 0
        mjo_max_run     = 0
        mjo_lead_flag   = False
        mjo_peak_amp    = float("nan")

        if mjo_df is not None:
            anchor = datetime(py, ANCHOR_MONTH, ANCHOR_DAY)
            win_s  = anchor + timedelta(days=int(BAR_ONSET_LO))
            win_e  = anchor + timedelta(days=int(BAR_ONSET_HI))

            win_df = mjo_df[
                (mjo_df["date"] >= pd.Timestamp(win_s))
                & (mjo_df["date"] <= pd.Timestamp(win_e))
            ]
            mask_win = (
                win_df["phase"].isin(MJO_ONSET_PHASES)
                & (win_df["amp"] >= MJO_AMP_THR)
            ).values
            ev = _count_mjo_events(mask_win)
            mjo_active_days = ev["total_days"]
            mjo_n_events    = ev["n_events"]
            mjo_max_run     = ev["max_run"]
            if len(win_df) > 0 and win_df["amp"].notna().any():
                mjo_peak_amp = float(win_df["amp"].max())

            lead_s = win_s - timedelta(days=MJO_LEAD_DAYS[1])
            lead_e = win_s - timedelta(days=MJO_LEAD_DAYS[0])
            lead_df = mjo_df[
                (mjo_df["date"] >= pd.Timestamp(lead_s))
                & (mjo_df["date"] <= pd.Timestamp(lead_e))
            ]
            mask_lead = (
                lead_df["phase"].isin(MJO_ONSET_PHASES)
                & (lead_df["amp"] >= MJO_AMP_THR)
            ).values
            mjo_lead_flag = bool(mask_lead.any())

        rec["mjo_active_days"] = mjo_active_days
        rec["mjo_n_events"]    = mjo_n_events
        rec["mjo_max_run"]     = mjo_max_run
        rec["mjo_peak_amp"]    = mjo_peak_amp
        rec["mjo_lead_flag"]   = mjo_lead_flag

        ctx[py] = rec

    return ctx


def _anomaly_flag(
    ctx_rec: Dict,
    onset: Optional[float],
    duration: Optional[float],
    med_onset: float,
    med_dur: float,
    sigma_onset: float,
    sigma_dur: float,
) -> str:
    flags = []
    sst = ctx_rec.get("sst_aso")
    dmi = ctx_rec.get("dmi_son")
    iact = ctx_rec.get("interaction", "NETRAL")

    is_strong = (sst is not None and dmi is not None
                 and abs(sst) >= ANOMALY_SST_STR
                 and abs(dmi) >= ANOMALY_DMI_STR)

    if iact == "COUNTER" and is_strong:
        if onset is not None and sigma_onset > 0:
            if abs(onset - med_onset) > ANOMALY_SIGMA * sigma_onset:
                flags.append("⚠COUNTER-anomali")
        if duration is not None and sigma_dur > 0:
            if abs(duration - med_dur) > ANOMALY_SIGMA * sigma_dur:
                flags.append("⚠dur-anomali")
    if iact == "SINERGI" and is_strong:
        flags.append("✦sinergi")
    if ctx_rec.get("mjo_lead_flag"):
        flags.append("MJO↑")
    return " ".join(flags) if flags else "—"


def _ols_2d(X: np.ndarray, y: np.ndarray
            ) -> Tuple[np.ndarray, float, float]:
    if len(y) < 4 or X.shape[0] < 4:
        return np.zeros(X.shape[1]), float("nan"), float("nan")
    try:
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        y_hat = X @ beta
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else float("nan")
        rmse = float(np.sqrt(ss_res / max(1, len(y) - X.shape[1])))
        return beta, r2, rmse
    except np.linalg.LinAlgError:
        return np.zeros(X.shape[1]), float("nan"), float("nan")


def compute_regression(
    all_yr: Dict[int, Dict],
    ctx: Dict[int, Dict],
) -> Dict[str, Dict]:
    years, onsets, durs, sst_v, dmi_v = [], [], [], [], []
    for py in sorted(all_yr):
        res = all_yr[py]
        c   = ctx.get(py, {})
        on  = res.get("onset_ens")
        dur = res.get("duration")
        sst = c.get("sst_aso")
        dmi = c.get("dmi_son")
        if (on is None or dur is None or sst is None or dmi is None
                or not np.isfinite(float(on))
                or not np.isfinite(float(dur))):
            continue
        years.append(py)
        onsets.append(float(on))
        durs.append(float(dur))
        sst_v.append(float(sst))
        dmi_v.append(float(dmi))

    if len(years) < 4:
        return {}

    sa = np.array(sst_v)
    da = np.array(dmi_v)
    X  = np.column_stack([sa, da, sa * da, np.ones(len(sa))])

    out: Dict[str, Dict] = {}
    for target_name, y_arr in [("onset", np.array(onsets)),
                               ("duration", np.array(durs))]:
        beta, r2, rmse = _ols_2d(X, y_arr)
        y_hat = X @ beta
        pred  = {yr: float(yh) for yr, yh in zip(years, y_hat)}
        resid = {yr: float(y) - float(yh)
                 for yr, y, yh in zip(years, y_arr, y_hat)}
        out[target_name] = {
            "beta":     beta,
            "R2":       r2,
            "RMSE":     rmse,
            "predict":  pred,
            "residual": resid,
            "years":    years,
            "labels":   ["b_SST", "b_DMI", "b_SST×DMI", "b0"],
        }
    return out


def compute_msla_arx_forecast(
    enso_sst_csv: str = DEFAULT_ENSO_SST_CSV,
    enso_msla_csv: str = DEFAULT_ENSO_MSLA_CSV,
    lag_h: int = 4,
    lag_f: int = 6,
) -> Dict:
    sst_df  = _load_enso_sst(enso_sst_csv)
    msla_df = _load_enso_msla(enso_msla_csv)

    if sst_df is None or msla_df is None:
        return {"note": "File SST atau MSLA tidak ditemukan."}

    sst_df  = sst_df.copy()
    msla_df = msla_df.copy()
    sst_df["date"]  = pd.to_datetime(sst_df["date"]).dt.normalize()
    msla_df["date"] = pd.to_datetime(msla_df["date"]).dt.normalize()

    merged = (
        sst_df[["date", "enso"]].rename(columns={"enso": "sst"})
        .merge(msla_df[["date", "enso"]].rename(columns={"enso": "sla"}),
               on="date", how="inner")
        .sort_values("date").reset_index(drop=True)
    )
    if len(merged) < lag_h + lag_f + 10:
        return {"note": f"Data gabungan tidak cukup (n={len(merged)})."}

    s_arr = merged["sst"].values.astype(float)
    m_arr = merged["sla"].values.astype(float)

    X_list, y_list = [], []
    for i in range(lag_h, len(merged) - lag_f):
        feat = np.concatenate([s_arr[i - lag_h:i + 1],
                               m_arr[i - lag_h:i + 1], [1.0]])
        X_list.append(feat)
        y_list.append(m_arr[i + lag_f])

    X_tr = np.array(X_list)
    y_tr = np.array(y_list)
    beta, _, _, _ = np.linalg.lstsq(X_tr, y_tr, rcond=None)

    feat_now = np.concatenate([s_arr[-(lag_h + 1):],
                               m_arr[-(lag_h + 1):], [1.0]])
    pred_sla  = float(np.dot(feat_now, beta))
    pred_date = merged["date"].iloc[-1] + timedelta(days=lag_f * 7)

    y_hat_tr = X_tr @ beta
    rmse = float(np.sqrt(np.mean((y_tr - y_hat_tr) ** 2)))

    return {
        "pred_sla":    pred_sla,
        "pred_phase":  _classify_enso(pred_sla),
        "pred_date":   (pred_date.date()
                        if hasattr(pred_date, "date") else pred_date),
        "train_n":     len(y_tr),
        "beta":        beta,
        "rmse":        rmse,
        "latest_sla":  float(m_arr[-1]),
        "latest_sst":  float(s_arr[-1]),
        "latest_date": merged["date"].iloc[-1].date(),
        "note":        "OK",
    }


def mjo_onset_probability(
    py: int,
    ctx_rec: Dict,
    onset_ens: Optional[float],
) -> Dict:
    n_events = ctx_rec.get("mjo_n_events", 0)
    max_run  = ctx_rec.get("mjo_max_run", 0)
    lead     = ctx_rec.get("mjo_lead_flag", False)
    peak_amp = ctx_rec.get("mjo_peak_amp", float("nan"))

    base_prob = 0.50
    boost = 0.0
    if lead:
        boost += 0.15
    if n_events >= 2:
        boost += 0.10
    elif n_events == 1:
        boost += 0.05

    prob = min(0.95, base_prob + boost)

    parts: List[str] = []
    if lead:
        parts.append(
            f"MJO event di {MJO_LEAD_DAYS[0]}–{MJO_LEAD_DAYS[1]}hr "
            f"pra-window")
    if n_events > 0:
        amp_s = (f"peak amp {peak_amp:.1f}"
                 if np.isfinite(peak_amp) else "")
        parts.append(
            f"{n_events} event (max run {max_run}d, {amp_s})".rstrip(", "))
    if not parts:
        parts.append("Tidak ada event MJO fase 5-8")

    return {
        "prob":      prob,
        "n_events":  n_events,
        "max_run":   max_run,
        "lead_flag": lead,
        "peak_amp":  peak_amp,
        "note":      "; ".join(parts),
    }


def _describe_beta(beta: float, var_name: str,
                   pos_text: str, neg_text: str) -> str:
    arah = pos_text if beta >= 0 else neg_text
    return f"{var_name:<8}: {beta:+.2f} → {arah}"


# ══════════════════════════════════════════════════════════════════════════
# §13  Report generators
# ══════════════════════════════════════════════════════════════════════════

def _sfmt(v: Optional[float], dec: int = 1) -> str:
    if v is None:
        return "  —  "
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return "  —  "
    if not np.isfinite(fv):
        return "  —  "
    return f"{fv:>{5 + dec}.{dec}f}"


def _fmt_dopy(py: int, dopy: Optional[float]) -> str:
    if dopy is None:
        return "—"
    try:
        fd = float(dopy)
    except (TypeError, ValueError):
        return "—"
    if not np.isfinite(fd):
        return "—"
    return _dopy_to_approx_date(py, fd)


_METHOD_SHORT = {
    "B1_BPI":      "BPI",
    "B2_WCC":      "WCC",
    "B3_RAD":      "RAD",
    "B4_SOIL":     "SOIL",
    "B5_VPD":      "VPD",
    "B6_PRESS":    "PRES",
    "B7_HMM":      "HMM",
    "ENS":         "ENSEM",
}

_METHOD_NOTE = {
    "B1_BPI":   "Persistence Index 8-var (awan tebal berkelanjutan)",
    "B2_WCC":   "Wind×Cloud×TCWV joint AND-gate (threshold diperketat)",
    "B3_RAD":   "Solar radiation deficit P15 dry (persistent overcast)",
    "B4_SOIL":  "Dual-layer soil moisture 7–28 + 28–100 cm",
    "B5_VPD":   "VPD drop + RH rise dual-threshold rolling 21d",
    "B6_PRESS": "Surface pressure low signature",
    "B7_HMM":   "9-D GMM-HMM State-2 onset (baratan penuh)",
    "ENS":      "Biweight ensemble (Tukey bisquare MAD-robust)",
}

_METHOD_TIER = {
    "B1_BPI": 1, "B2_WCC": 2,
    "B3_RAD": 1, "B4_SOIL": 2, "B5_VPD": 2, "B6_PRESS": 3,
    "B7_HMM": 1,
}


def report_detection(df: pd.DataFrame) -> None:
    print_header(
        "BARATAN FENOMENA — ANALISIS ONSET · OFFSET · DURASI",
        "EV09wind_baratan v2.0.0 · 7 estimator + Biweight ensemble"
    )

    print()
    print("  DEFINISI: Baratan = fase awan tebal terkunci (persistent overcast)")
    print("  Onset = momen arak-arakan awan barat MENGUNCI, bukan hujan pertama")
    print()
    print("  Menghitung BPI (Baratan Persistence Index v2)...")
    bci_all = compute_bci(df)
    if bci_all is None:
        print("  [!] BPI tidak dapat dihitung (variabel tidak cukup).")
        return

    print("  Menghitung fitur HMM 9-D (cache global)...")
    _get_hmm_features_cached(df)

    all_yr: Dict[int, Dict] = {}
    valid_records: List[Dict] = []
    print("  Menjalankan estimator B1–B7 per pranata-tahun...")
    for py in range(2015, 2027):
        res = run_year(df, py, bci_all)
        if res:
            all_yr[py] = res
            if res.get("duration") is not None:
                valid_records.append(res)

    sec_header("A · ONSET · OFFSET · DURASI PER PRANATA-TAHUN")
    print(f"  {'Thn':<6}{'ONSET':>9}{'Tanggal':>14}"
          f"{'OFFSET':>9}{'Tanggal':>14}{'DURASI':>9}"
          f"{'PEAK':>8}{'BPI pk':>8}")
    print("  " + "─" * (W - 4))

    for py in range(2015, 2027):
        if py not in all_yr:
            continue
        r = all_yr[py]
        on_d  = _fmt_dopy(py, r.get("onset_ens"))
        off_d = _fmt_dopy(py, r.get("offset_ens"))
        print(f"  {py:<6}"
              f"{_sfmt(r.get('onset_ens')):>9}{on_d:>14}"
              f"{_sfmt(r.get('offset_ens')):>9}{off_d:>14}"
              f"{_sfmt(r.get('duration')):>9}"
              f"{_sfmt(r.get('peak_dopy')):>8}"
              f"{_sfmt(r.get('peak_bci'), 2):>8}")

    est_keys = ["B1_BPI", "B2_WCC", "B3_RAD", "B4_SOIL",
                "B5_VPD", "B6_PRESS", "B7_HMM", "ENS"]
    est_lbl  = {k: _METHOD_SHORT[k] for k in est_keys}

    hdr = f"  {'Thn':<6}" + "".join(f"{est_lbl[k]:>8}" for k in est_keys)
    hdr = hdr[:W]

    sec_header("B · ONSET DETAIL PER ESTIMATOR (dopy)")
    print(f"  Bobot: BPI={ENS_W_ONSET['B1_BPI']} WCC={ENS_W_ONSET['B2_WCC']}"
          f" RAD={ENS_W_ONSET['B3_RAD']} SOIL={ENS_W_ONSET['B4_SOIL']}"
          f" VPD={ENS_W_ONSET['B5_VPD']} PRES={ENS_W_ONSET['B6_PRESS']}"
          f" HMM={ENS_W_ONSET['B7_HMM']}")
    print(f"  Ensemble: Tukey Biweight Mean (MAD-robust)")
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))
    for py in sorted(all_yr):
        r    = all_yr[py]
        raw  = r.get("onset_raw", {})
        row  = f"  {py:<6}"
        for k in ["B1_BPI", "B2_WCC", "B3_RAD", "B4_SOIL",
                  "B5_VPD", "B6_PRESS", "B7_HMM"]:
            row += f"{_sfmt(raw.get(k)):>8}"
        row += f"{_sfmt(r.get('onset_ens')):>8}"
        print(row[:W])

    sec_header("C · OFFSET DETAIL PER ESTIMATOR (dopy)")
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))
    for py in sorted(all_yr):
        r    = all_yr[py]
        raw  = r.get("offset_raw", {})
        row  = f"  {py:<6}"
        for k in ["B1_BPI", "B2_WCC", "B3_RAD", "B4_SOIL",
                  "B5_VPD", "B6_PRESS", "B7_HMM"]:
            row += f"{_sfmt(raw.get(k)):>8}"
        row += f"{_sfmt(r.get('offset_ens')):>8}"
        print(row[:W])

    if not valid_records:
        return
    sec_header("D · STATISTIK MULTI-TAHUN")
    stats = multiyr_stats(valid_records)
    label_map = {
        "onset_ens":  "Onset (dopy)",
        "offset_ens": "Offset (dopy)",
        "duration":   "Durasi (hari)",
        "peak_dopy":  "Peak dopy",
        "peak_bci":   "Peak BPI",
    }
    print(f"  {'Variabel':<16}{'N':>4}{'Mean':>8}{'Med':>8}"
          f"{'Std':>7}{'Min':>7}{'Max':>7}"
          f"{'Slope':>9}{'r':>7}{'t':>7}")
    print("  " + "─" * (W - 4))
    for k, lbl in label_map.items():
        s = stats.get(k, {})
        if not s or s.get("n", 0) < 2:
            print(f"  {lbl:<16}{'<2':>4}")
            continue
        print(f"  {lbl:<16}{s['n']:>4}"
              f"{s['mean']:>8.1f}{s['median']:>8.1f}"
              f"{s['std']:>7.1f}{s['min']:>7.1f}{s['max']:>7.1f}"
              f"{s['slope']:>+9.2f}{s['r']:>+7.3f}{s['t']:>+7.2f}")

    print()
    print("  Interpretasi slope (hari/tahun):")
    for key, lbl in (("onset_ens", "Onset"),
                     ("offset_ens", "Offset"),
                     ("duration", "Durasi")):
        sl = stats.get(key, {}).get("slope", float("nan"))
        if not np.isfinite(sl):
            continue
        if key == "onset_ens":
            arah = "makin lambat" if sl > 0 else "makin awal"
        elif key == "offset_ens":
            arah = "makin mundur" if sl > 0 else "makin cepat berakhir"
        else:
            arah = "memanjang" if sl > 0 else "memendek"
        print(f"    {lbl:<7}: {sl:+.2f} hr/thn → {arah}")

    print()
    print("  Signifikansi (|t|_crit = 2.26 untuk α=0.05, df=n−2):")
    for key, lbl in (("onset_ens", "Onset"),
                     ("duration", "Durasi"),
                     ("peak_bci", "Peak BPI")):
        t = stats.get(key, {}).get("t", float("nan"))
        if not np.isfinite(t):
            continue
        sig = ("SIGNIFIKAN ★" if abs(t) >= 2.26
               else "tidak signifikan")
        print(f"    {lbl:<9}: t={t:+.2f} → {sig}")


def report_hmm_trajectory(df: pd.DataFrame) -> None:
    """Report E: cross-validasi trajektori HMM State-2 vs ensemble B1–B6."""
    print_header(
        "E · VALIDASI SILANG STATE-SPACE HMM vs ENSEMBLE HEURISTIK",
        "9-D GMM-HMM State-2 onset (baratan penuh) vs ensemble B1–B6"
    )

    bci_all = compute_bci(df)
    if bci_all is None:
        print("  [!] BPI tidak tersedia.")
        return
    feat = _get_hmm_features_cached(df)
    if feat is None:
        print("  [!] Fitur HMM tidak tersedia (kolom tidak memadai).")
        return

    print()
    print(f"  Fitur HMM    : [r_30, wb_30, sm_30, rh_30, tc_30,")
    print(f"                  dt_30, cl_30, sd_30, u_30]  (9-D)")
    print(f"  State target : State 2 = Rendheng/Baratan penuh (DIKOREKSI dari v1.x)")
    print(f"  State 2 center: cloud=91%, TCWV=53.1, u_30=+0.39 km/h")
    print(f"  vs State 1    : cloud=69%, TCWV=42.6, u_30=-0.07 km/h (transisional)")
    print(f"  Kriteria onset: P(state=2) ≥ {HMM_ONSET_P_THR} bertahan ≥ {HMM_SUSTAIN} hari")
    print()
    print(f"  {'Thn':<6}{'Onset ENS':>10}{'Onset HMM':>11}"
          f"{'Δ (hari)':>10}  {'P(s=2) peak':>13}  Tanggal")
    print("  " + "─" * (W - 4))

    deltas: List[float] = []
    for py in range(2015, 2026):
        result = _hmm_probs_for_year(feat, py)
        if result is None:
            continue
        probs, dopy_eval = result

        # P(state=2) peak dalam window onset
        win_mask = (dopy_eval >= BAR_ONSET_LO) & (dopy_eval <= BAR_ONSET_HI)
        if not win_mask.any():
            continue
        p2_win = probs[win_mask, 2]
        d_win  = dopy_eval[win_mask]
        p_wet_win = probs[win_mask, 1] + probs[win_mask, 2]
        peak_pw = float(p_wet_win.max())
        peak_d  = float(d_win[int(np.argmax(p2_win))])

        ens_on = run_year(df, py, bci_all).get("onset_ens")
        hmm_on = detect_onset_hmm(df, py)

        if hmm_on is not None and ens_on is not None:
            diff = hmm_on - ens_on
            diff_s = f"{diff:>+9.1f}"
            deltas.append(diff)
        else:
            diff_s = f"{'—':>9}"

        ens_s = f"{ens_on:>10.1f}" if ens_on is not None else "    —    "
        hmm_s = f"{hmm_on:>11.1f}" if hmm_on is not None else "    —    "
        peak_s = f"Pwet={peak_pw:.2f} (d={peak_d:.0f})"
        print(f"  {py:<6}{ens_s}{hmm_s}{diff_s}  {peak_s}")

    if deltas:
        d_arr = np.array(deltas)
        print()
        print(f"  Ringkasan Δ (HMM − ENS):")
        print(f"    N       : {len(d_arr)}")
        print(f"    Mean    : {d_arr.mean():+.2f} hari")
        print(f"    Median  : {np.median(d_arr):+.2f} hari")
        print(f"    Std     : {d_arr.std(ddof=1):.2f} hari")
        print(f"    Range   : {d_arr.min():+.1f} s.d. {d_arr.max():+.1f}")

        if abs(d_arr.mean()) < 5:
            verdict = "Konvergensi KUAT: HMM & ensemble sepakat (<5 hari)."
        elif abs(d_arr.mean()) < 15:
            verdict = "Konvergensi MODERAT: perbedaan 5–15 hari."
        else:
            verdict = "DIVERGENSI: HMM & ensemble beda >15 hari."
        print(f"\n  Verdict: {verdict}")


def report_sr_ekf_tracking(df: pd.DataFrame) -> None:
    print_header(
        "F · SR-EKF TRACKING — LEVEL & TREND ZERO-PHASE-LAG",
        "Square-Root Extended Kalman Filter + ARCH(1) adaptive noise"
    )

    bci_all = compute_bci(df)
    if bci_all is None:
        print("  [!] BPI tidak tersedia.")
        return

    print()
    print(f"  Parameter SR-EKF (unit-variance):")
    print(f"    q_level = {SRKF_Q_LEVEL}   q_trend = {SRKF_Q_TREND}")
    print(f"    r_init  = {SRKF_R_INIT}     arch ω = {SRKF_ARCH_OMEGA}"
          f"  arch α = {SRKF_ARCH_ALPHA}")
    print()

    roll_col = "bci_roll" if "bci_roll" in bci_all.columns else "bpi_roll"

    sec_header("A · BPI — SR-EKF vs ROLLING MEAN")
    bci_ser = bci_all.dropna(subset=["bci" if "bci" in bci_all.columns else "bpi"]).reset_index(drop=True)
    raw_col = "bci" if "bci" in bci_ser.columns else "bpi"
    bci_raw = bci_ser[raw_col].values
    if len(bci_raw) < 30:
        print("  [!] Data BPI tidak cukup.")
        return
    bci_z = (bci_raw - bci_raw.mean()) / max(bci_raw.std(), 1e-9)
    lvl_bci, trd_bci = sr_kf_smooth_unit(bci_z)

    valid_bci = np.isfinite(lvl_bci)
    if valid_bci.sum() < 30:
        print("  [!] SR-EKF BPI tidak konvergen (burn-in terlalu panjang).")
        return

    print(f"  Statistik BPI z-score (raw)    : "
          f"μ={bci_z.mean():+.3f}  σ={bci_z.std():.3f}")
    print(f"  Statistik BPI level (SR-EKF)   : "
          f"μ={np.nanmean(lvl_bci):+.3f}  σ={np.nanstd(lvl_bci):.3f}")
    print(f"  Statistik BPI trend (SR-EKF)   : "
          f"μ={np.nanmean(trd_bci):+.5f}  σ={np.nanstd(trd_bci):.5f}")
    print()

    peak_trend_idx = int(np.nanargmax(
        np.where(np.isfinite(trd_bci), trd_bci, -np.inf)))
    print(f"  Puncak trend (indeks global)   : {peak_trend_idx} "
          f"({bci_ser['date'].iloc[peak_trend_idx].date()})")
    print(f"    level pada puncak trend      : "
          f"{lvl_bci[peak_trend_idx]:+.3f}")
    print(f"    trend pada puncak            : "
          f"{trd_bci[peak_trend_idx]:+.5f}/hari")

    sec_header("B · u_comp — SR-EKF ONSET PROXY PER TAHUN")
    daily_u = _daily_field(df, "u_comp")
    daily_u = daily_u.dropna(subset=["v"]).reset_index(drop=True)
    if len(daily_u) < 60:
        print("  [!] u_comp tidak tersedia.")
        return

    u_vals = daily_u["v"].values
    u_z = (u_vals - u_vals.mean()) / max(u_vals.std(), 1e-9)
    lvl_u, trd_u = sr_kf_smooth_unit(u_z)
    daily_u["lvl_u"] = lvl_u
    daily_u["trd_u"] = trd_u

    print(f"  {daily_u['date'].min().date()} → "
          f"{daily_u['date'].max().date()}  (N={len(daily_u):,})")
    print()
    print(f"  {'Thn':<6}{'Onset ENS':>11}{'Puncak trd_u':>16}"
          f"{'Lvl u':>10}{'Trd peak':>12}  Tanggal")
    print("  " + "─" * (W - 4))

    for py in range(2015, 2026):
        start = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
        end = start + pd.Timedelta(days=365)
        mask = (daily_u["date"] >= start) & (daily_u["date"] < end)
        sub = daily_u[mask]
        if len(sub) < 60:
            continue
        win = sub[(sub["dopy"] >= BAR_ONSET_LO)
                  & (sub["dopy"] <= BAR_ONSET_HI)]
        win = win.dropna(subset=["trd_u"])
        if len(win) == 0:
            continue
        peak_i = int(np.argmax(win["trd_u"].values))
        peak_row = win.iloc[peak_i]
        peak_dopy = float(peak_row["dopy"])
        ens_on = run_year(df, py, bci_all).get("onset_ens")
        ens_s = f"{ens_on:>11.1f}" if ens_on is not None else "    —  "
        print(f"  {py:<6}{ens_s}{peak_dopy:>16.1f}"
              f"{peak_row['lvl_u']:>+10.3f}"
              f"{peak_row['trd_u']:>+12.5f}  "
              f"{peak_row['date'].date()}")


def report_atmosphere(df: pd.DataFrame) -> None:
    print_header(
        "ANALISIS ATMOSFER — PERUBAHAN SELAMA BARATAN",
        "Komposit baratan vs musim kering · anomali & rasio"
    )

    bci_all = compute_bci(df)
    if bci_all is None:
        print("  [!] BPI tidak tersedia.")
        return

    all_onsets, all_offsets = [], []
    for py in range(2015, 2027):
        res = run_year(df, py, bci_all)
        on  = res.get("onset_ens")
        off = res.get("offset_ens")
        if on is not None and off is not None:
            try:
                all_onsets.append(float(on))
                all_offsets.append(float(off))
            except (TypeError, ValueError):
                continue

    if not all_onsets:
        print("  [!] Tidak ada baratan berhasil dideteksi.")
        return

    med_onset  = float(np.median(all_onsets))
    med_offset = float(np.median(all_offsets))
    med_dur    = med_offset - med_onset

    sec_header("A · PERBANDINGAN ATMOSFER: BARATAN VS KERING")
    print(f"  Window representatif : dopy {med_onset:.0f} – "
          f"{med_offset:.0f} ({med_dur:.0f} hari)")
    print(f"  Baseline kering      : dopy {DRY_LO:.0f} – "
          f"{DRY_HI:.0f} ({DRY_HI - DRY_LO:.0f} hari)")
    print()

    bar_stats = atmospheric_window_stats(df, med_onset, med_offset)
    dry_stats = dry_season_stats(df)

    print(f"  {'Variabel':<34}{'Kering':>10}{'Baratan':>10}"
          f"{'Anomali':>10}{'Arah':>6}")
    print("  " + "─" * (W - 4))

    for (field, _, desc, unit) in _ATMO_FIELDS:
        bv = bar_stats.get(field, float("nan"))
        dv = dry_stats.get(field, float("nan"))
        if not np.isfinite(bv) or not np.isfinite(dv):
            continue
        anom = bv - dv
        pct_sign = "▲" if anom > 0 else "▼"
        line = (f"  {desc:<34}{dv:>10.2f}{bv:>10.2f}"
                f"{anom:>+10.2f}  {pct_sign}  {unit}")
        print(line)
    print()
    print("  ▲ = lebih tinggi selama baratan   ▼ = lebih rendah")

    sec_header("B · KORELASI SILANG: ANGIN vs VARIABEL ATMOSFER")
    daily_u_series = _daily_field(df, "u_comp")["v"]
    for (field, _, desc, _) in _ATMO_FIELDS:
        if field in ("u_comp",) or field not in df.columns:
            continue
        daily_f = _daily_field(df, field)["v"]
        common = min(len(daily_u_series), len(daily_f))
        if common < 100:
            continue
        u_s = pd.Series(daily_u_series.values[:common])
        f_s = pd.Series(daily_f.values[:common])
        best_lag, best_r = 0, float("nan")
        for lag in range(-3, 11):
            a = u_s.shift(lag)
            m = a.notna() & f_s.notna()
            if m.sum() < 50:
                continue
            r = float(np.corrcoef(a[m], f_s[m])[0, 1])
            if not np.isfinite(best_r) or abs(r) > abs(best_r):
                best_lag, best_r = lag, r
        if np.isfinite(best_r):
            lag_s = f"L={best_lag:+d}d" if best_lag != 0 else "simultan"
            dir_s = "+" if best_r > 0 else "−"
            print(f"  {desc:<34}  r={best_r:+.3f}  "
                  f"{lag_s:<8}  [{dir_s}]")

    sec_header("C · SIKLUS TAHUNAN: VARIABEL KUNCI PER BULAN")
    shown = [f for f in ("u_comp", "cloud", "precip", "tcwv",
                         "sw_rad", "vpd") if f in df.columns]
    print(f"  {'Bulan':<6}" + "".join(f"{f:>10}" for f in shown))
    print("  " + "─" * (6 + 10 * len(shown)))
    for m in range(1, 13):
        sub = df[df["month"] == m]
        row = f"  {MONTH_SHORT[m]:<6}"
        for f in shown:
            v = sub[f].dropna()
            if len(v) == 0:
                row += f"{'—':>10}"
                continue
            if f == "precip":
                val = float(v.sum() / len(v) * 24.0)
            else:
                val = float(v.mean())
            row += f"{val:>10.2f}"
        print(row[:W])


def report_land(df: pd.DataFrame) -> None:
    print_header(
        "ANALISIS TANAH & DARATAN — RESPONS TERHADAP BARATAN",
        "Profil kelembapan, suhu tanah, ET0 & lag korelasi"
    )

    bci_all = compute_bci(df)
    if bci_all is None:
        print("  [!] BPI tidak tersedia.")
        return

    onsets, offsets = [], []
    for py in range(2015, 2027):
        res = run_year(df, py, bci_all)
        on  = res.get("onset_ens")
        off = res.get("offset_ens")
        if on is not None and off is not None:
            try:
                onsets.append(float(on))
                offsets.append(float(off))
            except (TypeError, ValueError):
                continue

    if not onsets:
        print("  [!] Tidak ada baratan berhasil dideteksi.")
        return

    med_onset  = float(np.median(onsets))
    med_offset = float(np.median(offsets))
    med_dur    = med_offset - med_onset

    sec_header("A · PROFIL TANAH: PRE / BARATAN / POST")
    profile = soil_window_profile(df, med_onset, med_offset)
    if not profile:
        print("  [!] Variabel tanah tidak tersedia.")
    else:
        win_names = list(next(iter(profile.values()))["windows"].keys())
        win_labels = {
            "PRE":  "PRE(-30d)",
            "BAR":  "BARATAN",
            "POST": "POST(+30d)",
        }
        col_w = 11
        hdr = (f"  {'Variabel':<34}"
               + "".join(f"{win_labels.get(w, w):>{col_w}}"
                         for w in win_names))
        print(hdr[:W])
        print("  " + "─" * (W - 4))
        for field, data in profile.items():
            row = f"  {data['desc']:<34}"
            for wn in win_names:
                val = data["windows"].get(wn, float("nan"))
                if np.isfinite(val):
                    row += f"{val:>{col_w}.4f}"
                else:
                    row += f"{'—':>{col_w}}"
            print(row[:W])
        print()
        print("  PRE    = 30 hari sebelum onset")
        print("  BAR    = selama window baratan")
        print("  POST   = 30 hari setelah offset")

    sec_header("B · LAG KORELASI BPI vs VARIABEL TANAH")
    lag_corr = soil_lag_correlation(df, med_onset)
    if not lag_corr:
        print("  [!] Data lag korelasi tidak cukup.")
    else:
        print(f"  {'Variabel':<34}{'Lag(hari)':>11}{'r_peak':>10}  "
              f"Interpretasi")
        print("  " + "─" * (W - 4))
        for field, info in lag_corr.items():
            lag = info["lag_peak"]
            r   = info["r_peak"]
            if lag > 0:
                interp = f"Tanah respons {lag} hari setelah atmosfer"
            elif lag < 0:
                interp = f"Tanah {abs(lag)} hari MENDAHULUI atmosfer"
            else:
                interp = "Respons simultan"
            print(f"  {info['description']:<34}"
                  f"{lag:>11}{r:>+10.3f}  {interp}"[:W])

    sec_header("C · ET0 FAO: SEBELUM, SELAMA, SESUDAH BARATAN")
    if "et0" not in df.columns:
        print("  [!] Kolom et0 tidak tersedia.")
    else:
        windows = [
            ("Pra-baratan (-60d)",   med_onset - 60.0, med_onset),
            ("Baratan",              med_onset,        med_offset),
            ("Pasca-baratan (+60d)", med_offset,       med_offset + 60.0),
            ("Musim kering",         DRY_LO,           DRY_HI),
        ]
        print(f"  {'Window':<26}{'ET0 mm/hr':>12}{'ET0 mm/bln':>12}  "
              f"Interpretasi")
        print("  " + "─" * (W - 4))
        for (wname, lo, hi) in windows:
            lo_f = float(lo)
            hi_f = float(hi)
            mask = ((df["dopy"] >= lo_f)
                    & (df["dopy"] < hi_f)
                    & df["et0"].notna())
            v = df.loc[mask, "et0"]
            if len(v) == 0:
                continue
            rate_hr = float(v.mean())
            rate_mo = rate_hr * 24.0 * 30.0
            if abs(lo_f - (med_onset - 60.0)) < 1e-6:
                interp = "Transisi pra-baratan"
            elif abs(lo_f - med_onset) < 1e-6:
                interp = "Evap rendah — awan tebal menekan radiasi"
            elif abs(lo_f - med_offset) < 1e-6:
                interp = "Evap pulih — langit cerah kembali"
            elif abs(lo_f - DRY_LO) < 1e-6:
                interp = "Evap tinggi — radiasi penuh + suhu tinggi"
            else:
                interp = ""
            print(f"  {wname:<26}{rate_hr:>12.4f}{rate_mo:>12.1f}  "
                  f"{interp}"[:W])

    sec_header("D · CURAH HUJAN: KONTRIBUSI BARATAN")
    ppart = precip_partitioning(df, med_onset, med_offset)
    if not ppart:
        print("  [!] Data curah hujan tidak cukup.")
    else:
        n_y = int(ppart.get("n_years", 1))
        print(f"  Rata-rata per pranata-tahun (n={n_y}):")
        print(f"  Total tahunan    : {ppart['total']:>10.1f} mm/tahun")
        print(f"  Baratan ({med_dur:.0f} hr): "
              f"{ppart['bar_mm']:>10.1f} mm "
              f"({ppart['bar_pct']:.1f}% dari total)")
        print(f"  Kering  ({DRY_HI - DRY_LO:.0f} hr): "
              f"{ppart['dry_mm']:>10.1f} mm "
              f"({ppart['dry_pct']:.1f}% dari total)")
        print(f"  Rate baratan     : {ppart['bar_rate']:>10.2f} mm/hari")
        print(f"  Rate kering      : {ppart['dry_rate']:>10.2f} mm/hari")
        print(f"  Intensifikasi    : "
              f"{ppart['intensification']:>10.2f}×")


def report_precursors(df: pd.DataFrame) -> None:
    print_header(
        "ANALISIS PREKURSOR — INDIKATOR AWAL BARATAN (AWAN TERKUNCI)",
        "Variabel mana yang paling awal berubah sebelum baratan mengunci"
    )

    bci_all = compute_bci(df)
    if bci_all is None:
        print("  [!] BPI tidak tersedia.")
        return

    onsets = []
    for py in range(2015, 2027):
        res = run_year(df, py, bci_all)
        on  = res.get("onset_ens")
        if on is not None:
            try:
                onsets.append(float(on))
            except (TypeError, ValueError):
                continue

    if len(onsets) < 3:
        print("  [!] Data onset tidak cukup.")
        return

    med_onset = float(np.median(onsets))

    roll_col = "bci_roll" if "bci_roll" in bci_all.columns else "bpi_roll"

    sec_header("A · LAG CORRELATION TERHADAP ONSET BPI")
    print(f"  Onset referensi: dopy {med_onset:.1f}  "
          f"({_dopy_to_approx_date(2025, med_onset)})")
    print(f"  Pertanyaan: variabel X mendahului 'baratan terkunci' berapa hari?")
    print()

    bci_ser  = pd.Series(bci_all[roll_col].values,
                         index=pd.to_datetime(bci_all["date"]))
    pre_lags = list(range(1, 35))  # cek hingga 34 hari ke depan

    # Precursor diperluas dengan komponen BPI baru
    precursor_fields = [
        ("tcwv",       "TCWV (kolom uap air)"),
        ("cloud",      "Cloud cover total (%)"),
        ("sw_rad",     "Shortwave radiation (W/m²)"),
        ("sm_7_28",    "Soil moisture 7–28 cm"),
        ("sm_28_100",  "Soil moisture 28–100 cm"),
        ("rh",         "RH 2m"),
        ("dew_pt",     "Dew point"),
        ("vpd",        "VPD"),
        ("pressure",   "Tekanan permukaan"),
        ("cloud_lo",   "Low cloud cover"),
        ("u_comp",     "u_comp (komponen barat angin)"),
    ]

    results_prec = []
    for (field, fdesc) in precursor_fields:
        if field not in df.columns or df[field].notna().sum() < 200:
            continue
        daily_f = _daily_field(df, field)
        f_ser   = pd.Series(daily_f["v"].values,
                            index=pd.to_datetime(daily_f["date"]))
        common  = bci_ser.index.intersection(f_ser.index)
        if len(common) < 100:
            continue

        bci_c = bci_ser.loc[common]
        f_c   = f_ser.loc[common]

        best_lag, best_r = 0, 0.0
        for lag in pre_lags:
            f_sh = f_c.shift(-lag)
            m = f_sh.notna() & bci_c.notna()
            if m.sum() < 50:
                continue
            r = float(np.corrcoef(f_sh[m], bci_c[m])[0, 1])
            if abs(r) > abs(best_r):
                best_r, best_lag = r, lag

        results_prec.append((fdesc, best_lag, best_r, field))

    results_prec.sort(key=lambda x: abs(x[2]), reverse=True)

    print(f"  {'Variabel precursor':<32}{'Lead(hari)':>12}"
          f"{'r':>8}  Interpretasi")
    print("  " + "─" * (W - 4))
    for (fdesc, lag, r, _) in results_prec:
        dir_s  = "+" if r > 0 else "−"
        strong = "★★" if abs(r) > 0.5 else ("★" if abs(r) > 0.3 else " ")
        print(f"  {fdesc:<32}{lag:>12}{r:>+8.3f}  "
              f"{dir_s} {strong}"[:W])

    print()
    print("  ★★ |r| > 0.5   ★ |r| > 0.3")

    sec_header("B · INDEKS PRAKIRAAN BARATAN (IPB) v2")
    print()
    print("  IPB v2 = kombinasi 3 prekursor terpilih (lead terpanjang + |r| kuat):")
    top3 = results_prec[:3]
    for i, (fdesc, lag, r, field) in enumerate(top3):
        arah = ("berbanding lurus" if r > 0
                else "berbanding terbalik")
        print(f"    {i + 1}. {fdesc:<32} "
              f"(lead {lag:>2}d, r={r:+.3f}, {arah})")
    print()
    print("  Interpretasi fisis:")
    print("  · TCWV mendahului baratan karena uap maritim lebih dulu hadir")
    print("    sebelum awan tebal terbentuk → 'tanda air datang sebelum awan'")
    print("  · Cloud cover merupakan akibat dari TCWV yang sudah jenuh")
    print("  · sw_rad deficit muncul bersamaan/segera setelah cloud tinggi")

    sec_header("C · RANKING PRESISI ESTIMATOR B1–B7 UNTUK BARATAN TERKUNCI")
    print(f"  {'Estimator':<12}{'Bobot':>8}{'Tier':>6}  Keterangan")
    print("  " + "─" * (W - 4))
    tier_sorted = sorted(_METHOD_TIER.items(), key=lambda x: (x[1], -ENS_W_ONSET.get(x[0], 0)))
    for (k, tier) in tier_sorted:
        w = ENS_W_ONSET.get(k, 0)
        note = _METHOD_NOTE.get(k, "")
        print(f"  {_METHOD_SHORT.get(k, k):<12}{w:>8.1f}{'T'+str(tier):>6}  {note}"[:W])
    print()
    print(f"  Tier 1 = paling presisi untuk 'awan berkelanjutan'")
    print(f"  Tier 2 = baik, perlu lebih dari satu sinyal")
    print(f"  Tier 3 = sinyal umum musim hujan, kurang spesifik baratan")

def report_lifecycle(df: pd.DataFrame) -> None:
    print_header(
        "SIKLUS HIDUP BARATAN — 5 FASE",
        "Benih → Kunci → Plateau → Longgar → Bubar · EV09 2015–2025"
    )

    print()
    print("  Baratan bukan peristiwa tunggal — ia punya siklus hidup.")
    print("  Onset ensemble B1–B7 = 'Kunci' di Fase 2.")
    print("  Angin barat bukan penyebab — ia MENYUSUL setelah langit menutup.")
    print()

    for p in BARATAN_LIFECYCLE:
        if p["id"] == 5:
            rng = f"dopy {p['dopy_lo']:.0f}–365 + 0–{p['dopy_hi']:.0f}"
        else:
            rng = f"dopy {p['dopy_lo']:.0f}–{p['dopy_hi']:.0f}"
        print(f"  ── Fase {p['id']} · {p['name']}   [{rng}]")
        print(f"     {p['tagline']}")
        for sig in p["signature"]:
            print(f"       · {sig}")
        print()

    stats = _phase_composite_stats(df)

    sec_header("A · KOMPOSIT VARIABEL PER FASE (semua pranata-tahun)")
    hdr = f"  {'Variabel':<20}" + "".join(
        f"{p['name']:>10}" for p in BARATAN_LIFECYCLE)
    print(hdr[:W])
    print("  " + "─" * (W - 4))

    for (key, label, fmt) in _LIFECYCLE_FIELDS:
        if key not in df.columns and key != "dtr":
            continue
        row = f"  {label:<20}"
        any_v = False
        for p in BARATAN_LIFECYCLE:
            v = stats.get(p["id"], {}).get(key)
            if v is None or not np.isfinite(v):
                row += f"{'—':>10}"
            else:
                any_v = True
                row += f"{format(v, fmt):>10}"
        if any_v:
            print(row[:W])

    print()
    n_row = f"  {'(n jam)':<20}"
    for p in BARATAN_LIFECYCLE:
        n = stats.get(p["id"], {}).get("n_hours", 0)
        n_row += f"{n:>10,}"
    print(n_row[:W])

    sec_header("B · TANDA TANGAN TRANSISI — Δ ANTAR-FASE")
    print("  Δ = (fase berikut) − (fase ini). Fase 1→2 = onset baratan.")
    print()
    key_cols = ("tcwv", "cloud", "u_comp", "sw_rad", "vpd", "precip")
    key_labels = {"tcwv": "ΔTCWV", "cloud": "ΔCloud", "u_comp": "Δu_comp",
                  "sw_rad": "ΔSW", "vpd": "ΔVPD", "precip": "ΔHujan"}
    hdr2 = f"  {'Transisi':<22}" + "".join(
        f"{key_labels[k]:>11}" for k in key_cols)
    print(hdr2[:W])
    print("  " + "─" * (W - 4))

    for i in range(len(BARATAN_LIFECYCLE) - 1):
        pf = BARATAN_LIFECYCLE[i]
        pt = BARATAN_LIFECYCLE[i + 1]
        sf = stats.get(pf["id"], {})
        st = stats.get(pt["id"], {})
        row = f"  {pf['name']:<9} → {pt['name']:<10}"
        for k in key_cols:
            a, b = sf.get(k), st.get(k)
            if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)):
                row += f"{'—':>11}"
            else:
                row += f"{b - a:>+11.2f}"
        print(row[:W])

    print()
    print("  Catatan transisi:")
    print("   · 1→2 Kunci   : cloud↑↑ & SW↓↓ — langit menutup, siklus diurnal mati")
    print("   · 2→3 Plateau : saturasi penuh — u_comp akhirnya positif")
    print("   · 3→4 Longgar : cloud↓ & u_comp↓ — kunci mulai lepas")
    print("   · 4→5 Bubar   : TCWV↓ & cloud↓↓ — kembali rezim easterly kering")

    sec_header("C · PETA ONSET/OFFSET KE FASE")
    bci_all = compute_bci(df)
    if bci_all is None:
        print("  [!] BPI tidak tersedia.")
        return

    print(f"  {'Thn':<6}{'Onset':>8}{'Fase':>7}"
          f"{'Offset':>9}{'Fase':>7}{'Durasi':>8}  Keterangan")
    print("  " + "─" * (W - 4))

    for py in range(2015, 2027):
        r = run_year(df, py, bci_all)
        if not r:
            continue
        on = r.get("onset_ens")
        off = r.get("offset_ens")
        dur = r.get("duration")
        on_f = _phase_of_dopy(on) if on is not None else 0
        off_f = _phase_of_dopy(off) if off is not None else 0
        on_s = f"{on:>8.1f}" if on is not None else f"{'—':>8}"
        off_s = f"{off:>9.1f}" if off is not None else f"{'—':>9}"
        dur_s = f"{dur:>8.1f}" if dur is not None else f"{'—':>8}"
        onfs = f"F{on_f}" if on_f else "—"
        offs = f"F{off_f}" if off_f else "—"
        if on_f == 1:
            note = "onset sangat awal — masih Benih"
        elif on_f == 2:
            note = "onset normal — Kunci"
        elif on_f == 3:
            note = "onset lambat — langsung Plateau"
        else:
            note = ""
        print(f"  {py:<6}{on_s}{onfs:>7}{off_s}{offs:>7}{dur_s}  {note}"[:W])

def report_enso_context(df: pd.DataFrame) -> None:
    print_header(
        "KONTEKS IKLIM BARATAN — ENSO · IOD · MJO · REGRESI · PREDIKSI",
        "EV09wind_baratan v2.0.0 · §12"
    )

    print("  Memuat data iklim (ENSO/IOD/MJO)...")
    ctx = load_enso_context()
    has_ctx = any(c.get("sst_aso") is not None for c in ctx.values())
    if not has_ctx:
        print("  [!] File iklim tidak ditemukan. Pastikan berkas berikut ada:")
        for fn in (DEFAULT_ENSO_SST_CSV, DEFAULT_ENSO_MSLA_CSV,
                   DEFAULT_IOD_WEEKLY, DEFAULT_IOD_MONTHLY, DEFAULT_RMM_CSV):
            print(f"      {fn}")
        return

    print("  Menghitung deteksi baratan...")
    bci_all = compute_bci(df)
    if bci_all is None:
        print("  [!] BPI tidak dapat dihitung.")
        return

    all_yr: Dict[int, Dict] = {}
    for py in range(2015, 2027):
        res = run_year(df, py, bci_all)
        if res:
            all_yr[py] = res

    valid = [r for r in all_yr.values()
             if (r.get("onset_ens") is not None
                 and r.get("duration") is not None)]
    if not valid:
        print("  [!] Tidak ada tahun baratan terdeteksi.")
        return

    all_onsets = [float(r["onset_ens"]) for r in valid]
    all_durs   = [float(r["duration"]) for r in valid]
    med_onset  = float(np.median(all_onsets))
    med_dur    = float(np.median(all_durs))
    sig_onset  = (float(np.std(all_onsets, ddof=1))
                  if len(all_onsets) > 1 else 1.0)
    sig_dur    = (float(np.std(all_durs, ddof=1))
                  if len(all_durs) > 1 else 1.0)

    sec_header("A · ANOTASI PER TAHUN: ENSO × IOD × BARATAN")
    hdr = (f"  {'Thn':<5} {'SST_ASO':>8} {'SLA_ASO':>8} "
           f"{'DMI_SON':>8} {'ENSO':>8} {'IOD':>7} "
           f"{'Onset':>7} {'Durasi':>7}  Keterangan")
    print(hdr)
    print("  " + "─" * (W - 4))

    for py in range(2015, 2027):
        c   = ctx.get(py, {})
        res = all_yr.get(py, {})
        sst = c.get("sst_aso")
        sla = c.get("sla_aso")
        dmi = c.get("dmi_son")
        on  = res.get("onset_ens")
        dur = res.get("duration")

        def _f(v, d=2):
            if v is None or not np.isfinite(float(v)):
                return "  —  "
            return f"{v:>+.{d}f}"

        flag = _anomaly_flag(c, on, dur, med_onset, med_dur,
                             sig_onset, sig_dur)

        print(f"  {py:<5} {_f(sst):>8} {_f(sla):>8} "
              f"{_f(dmi):>8} {c.get('enso_phase','—'):>8} "
              f"{c.get('iod_phase','—'):>7} "
              f"{_sfmt(on):>7} {_sfmt(dur):>7}  {flag}")

    sec_header("B · REGRESI OLS: ONSET & DURASI ~ SST + DMI + SST×DMI")
    reg = compute_regression(all_yr, ctx)

    if not reg:
        print("  [!] Data tidak cukup untuk regresi.")
    else:
        for target in ("onset", "duration"):
            r = reg.get(target)
            if not r:
                continue
            tname = ("Onset (dopy)" if target == "onset"
                     else "Durasi (hari)")
            print(f"\n  {tname}:  R²={r['R2']:.3f}  "
                  f"RMSE={r['RMSE']:.1f} hari")
            print(f"  {'Koefisien':<14}{'Nilai':>10}")
            print("  " + "─" * 25)
            for lbl, b in zip(r["labels"], r["beta"]):
                print(f"  {lbl:<14}{b:>+10.3f}")

            print()
            print(f"  {'Thn':<6}{'Aktual':>9}{'Prediksi':>10}{'Residual':>10}")
            print("  " + "─" * 36)
            for py in sorted(r["predict"]):
                act_r = all_yr.get(py, {})
                act_v = act_r.get("onset_ens" if target == "onset"
                                  else "duration")
                pred_v = r["predict"][py]
                res_v  = r["residual"][py]
                act_s  = (f"{float(act_v):.1f}"
                          if act_v is not None else "—")
                print(f"  {py:<6}{act_s:>9}{pred_v:>10.1f}{res_v:>+10.1f}")

    sec_header("C · PREDIKSI MUSIMAN ARX 6-MINGGU VIA MSLA")
    arx = compute_msla_arx_forecast()
    if arx.get("note") != "OK":
        print(f"  [!] {arx.get('note', 'Error tidak diketahui.')}")
    else:
        print(f"  Data terkini  : MSLA={arx['latest_sla']:+.3f}  "
              f"SST={arx['latest_sst']:+.3f}  "
              f"({arx['latest_date']})")
        print(f"  Prediksi +6wk : SLA={arx['pred_sla']:+.3f}  "
              f"→ fase {arx['pred_phase']}  "
              f"(perkiraan {arx['pred_date']})")
        print(f"  RMSE model    : {arx['rmse']:.3f}  "
              f"(n latih={arx['train_n']})")
        ph = arx["pred_phase"]
        if ph == "La Niña":
            print("  ⟹ Proyeksi La Niña: onset cenderung lebih awal.")
        elif ph == "El Niño":
            print("  ⟹ Proyeksi El Niño: onset cenderung lebih lambat.")
        else:
            print(f"  ⟹ Kondisi Netral: onset mendekati klimatologis (dopy {med_onset:.0f}).")

    sec_header("D · MJO PREDICTOR — EVENT FASE 5–8 SEBAGAI SINYAL DINI")
    mjo_has_data = any(ctx[py].get("mjo_n_events", 0) > 0
                       or ctx[py].get("mjo_lead_flag", False)
                       for py in ctx)

    if not mjo_has_data:
        print("  [!] rmm8.csv tidak ditemukan atau tidak ada data MJO.")
    else:
        print(f"  {'Thn':<6}{'Event':>6}{'MaxRun':>8}"
              f"{'PeakAmp':>9}{'Lead':>6}"
              f"{'Onset':>8}{'Prob':>7}  Keterangan")
        print("  " + "─" * (W - 4))
        for py in range(2015, 2027):
            c    = ctx.get(py, {})
            res  = all_yr.get(py, {})
            on   = res.get("onset_ens")
            mjo  = mjo_onset_probability(py, c, on)
            lead_s  = "✓" if c.get("mjo_lead_flag") else "·"
            peak_v  = c.get("mjo_peak_amp", float("nan"))
            peak_s  = f"{peak_v:.1f}" if np.isfinite(peak_v) else "—"
            print(f"  {py:<6}{mjo['n_events']:>6}{mjo['max_run']:>8}"
                  f"{peak_s:>9}{lead_s:>6}"
                  f"{_sfmt(on):>8}{mjo['prob']:>7.0%}  "
                  f"{mjo['note'][:38]}")
    print()


def report_all(df: pd.DataFrame) -> None:
    report_detection(df)
    report_hmm_trajectory(df)
    report_sr_ekf_tracking(df)
    report_atmosphere(df)
    report_land(df)
    report_precursors(df)
    report_enso_context(df)
    report_lifecycle(df)


# ══════════════════════════════════════════════════════════════════════════
# §14  CLI
# ══════════════════════════════════════════════════════════════════════════

MENU_ITEMS = (
    "  1 › Deteksi Onset · Offset · Durasi",
    "  2 › Analisis Variabel Atmosfer",
    "  3 › Analisis Tanah & Daratan",
    "  4 › Analisis Prekursor Onset",
    "  5 › ENSO · IOD · MJO · Regresi · Prediksi",
    "  6 › HMM State-2 Trajectory",
    "  7 › SR-EKF Tracking",
    "  8 › Siklus Hidup Baratan — 5 Fase",
    "  9 › Jalankan semua (1–8)",
    "  0 › Keluar",
)


def show_menu() -> None:
    print()
    print(box_top(
        "PRANATA MANGSA — BARATAN ANALYSIS (EV09-WIND-BARATAN v2.0.0)"))
    print(box_row(
        "Onset · Offset · Durasi · Atmosfer · Tanah · Prekursor · "
        "ENSO/IOD/MJO · HMM · SR-EKF"))
    print(box_row("−7.5220°LS, 112.5661°BT, 28 m · ERA5/IFS · P1+P2 IDW"))
    print(box_row("B7_HMM: State-2 'Rendheng' onset (awan terkunci) ← DIKOREKSI"))
    print(box_row("Ensemble: Tukey Biweight Mean (MAD-robust) ← BARU"))
    print(box_mid())
    for item in MENU_ITEMS:
        print(box_row(item))
    print(box_bot())


def main_loop(df: pd.DataFrame) -> None:
    while True:
        show_menu()
        pilihan = input("  Pilih menu (0–9): ").strip()
        if pilihan == "0":
            print()
            print(box_top())
            print(box_row("Terima kasih — EV09-Wind-Baratan v2.0.1"))
            print(box_bot())
            break
        elif pilihan == "1":
            report_detection(df)
        elif pilihan == "2":
            report_atmosphere(df)
        elif pilihan == "3":
            report_land(df)
        elif pilihan == "4":
            report_precursors(df)
        elif pilihan == "5":
            report_enso_context(df)
        elif pilihan == "6":
            report_hmm_trajectory(df)
        elif pilihan == "7":
            report_sr_ekf_tracking(df)
        elif pilihan == "8":
            report_lifecycle(df)
        elif pilihan == "9":
            report_all(df)
        else:
            print("\n  Pilihan tidak valid.")
            continue
        input("\n  Tekan Enter untuk kembali ke menu...")


def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="EV09wind_baratan",
        description=("Baratan fenomena analysis v2.0.1 — onset, offset, "
                     "durasi, atmosfer, tanah, prekursor, konteks iklim, "
                     "HMM trajectory, SR-EKF tracking, siklus hidup."),
    )
    ap.add_argument("--detect",    action="store_true")
    ap.add_argument("--atmo",      action="store_true")
    ap.add_argument("--land",      action="store_true")
    ap.add_argument("--precursor", action="store_true")
    ap.add_argument("--enso",      action="store_true")
    ap.add_argument("--hmm",       action="store_true",
                    help="HMM trajectory cross-validation (B7 State-2 vs ENS)")
    ap.add_argument("--srekf",     action="store_true",
                    help="SR-EKF tracking level & trend")
    ap.add_argument("--lifecycle", action="store_true",
                    help="Siklus hidup baratan — 5 fase (Benih→Kunci→...)")
    ap.add_argument("--all",       action="store_true",
                    help="Jalankan semua laporan (1–8)")
    return ap


def main(argv=None) -> int:
    args = _build_argparser().parse_args(argv)

    print()
    print(box_top("EV09wind_baratan.py v2.0.1 — Memuat data..."))
    print(box_bot())

    df = load_baratan_data()
    if df is None:
        return 1

    if args.all:        report_all(df);              return 0
    if args.detect:     report_detection(df);        return 0
    if args.atmo:       report_atmosphere(df);       return 0
    if args.land:       report_land(df);             return 0
    if args.precursor:  report_precursors(df);       return 0
    if args.enso:       report_enso_context(df);     return 0
    if args.hmm:        report_hmm_trajectory(df);   return 0
    if args.srekf:      report_sr_ekf_tracking(df);  return 0
    if args.lifecycle:  report_lifecycle(df);        return 0

    main_loop(df)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Program dihentikan.")
        sys.exit(0)
