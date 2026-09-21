#!/usr/bin/env python3
"""
EV09baratan.py — Analisis Rezim Baratan (Arak-arakan Awan dari Barat)
=========================================================================

Modul ini menganalisis rezim baratan dari data meteorologi per-jam di
titik MJS (−7.522°S, 112.566°E). Baratan dideteksi sebagai rangkaian
episode kebasahan, digabung menjadi musim, kemudian dipetakan ciri
modernnya per mangsa Pranata Mangsa (basis R10).

KERANGKA ANALISIS
──────────────────
  1. KOMPOSIT BARATAN
     Indeks kontinu dari 6 variabel dengan pembobotan:
         u_comp (wind dir 10m)    bobot 2.0   — sinyal fisik primer
         cloud_cover (%)          bobot 1.0
         log1p(precipitation mm)  bobot 1.0
         relative_humidity (%)    bobot 1.0
         TCWV (kg/m²)             bobot 1.0
         soil_moisture 0-7 cm     bobot 1.0
     Setiap variabel di-z-score terhadap mean & std tahunan. Komposit
     adalah jumlah terbobot z-score. Nilai tinggi = rezim baratan.

  2. DETEKSI EPISODE
     Jam baratan: komposit ≥ +0.5σ.
     Hari baratan: fraksi jam baratan ≥ 0.40 setelah smoothing 7 hari.
     Episode: run berurutan hari baratan ≥ 5 hari.

  3. PENGGABUNGAN MUSIM
     Episode dengan jeda ≤ 10 hari digabung menjadi satu musim.
     Musim dengan durasi ≥ 15 hari dianggap lengkap.

  4. ONSET/PEAK/OFFSET
     Untuk 13 variabel kunci, cari waktu onset (z ≥ +0.5σ sustained
     5 hari setelah reversal), peak (z maksimum dalam jendela), dan
     offset (z < +0.5σ sustained 5 hari setelah peak).

  5. CIRI MODERN PER MANGSA
     Semua variabel dihitung rata-rata & z-score dalam batas mangsa
     R10 (kalibrasi 10 tahun terakhir, 2016–2025). Menghasilkan
     "sidik jari" atmosfer & tanah setiap mangsa.

REFERENSI
─────────
  · Wheeler, M. C., & Hendon, H. H. (2004). An all-season real-time
    multivariate MJO index. Mon. Wea. Rev. 132(8):1917–1932.
  · Duchon, C. E. (1979). Lanczos filtering in one and two dimensions.
    J. Appl. Meteor. 18(8):1016–1022.
  · BMKG. Kriteria Musim Hujan Indonesia. Definisi operasional onset.

DATA
────
  Data hourly Open-Meteo (ERA5/ERA5-Land/IFS-HRES), 2015–2026.
  Stasiun: P1 (−7.487°S, 112.538°E), P2 (−7.557°S, 112.557°E),
  keduanya 28 m. Titik target: MJS (−7.5220°S, 112.5661°E).
"""

from __future__ import annotations
import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ══════════════════════════════════════════════════════════════════════════
# Section 1 · Konstanta
# ══════════════════════════════════════════════════════════════════════════

W: int = 72

CANDIDATES = (
    "open-meteo-7.49S112.54E28m_hourly10yr.csv",
    "open-meteo-7.56S112.56E28m_hourly10yr.csv",
)

ANCHOR_MONTH = 6
ANCHOR_DAY   = 22

MONTHS = ("Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
          "Jul", "Agu", "Sep", "Okt", "Nov", "Des")

# ── Ambang komposit ──────────────────────────────────────────────────────
COMPOSITE_HOUR_THRESHOLD   = 0.5     # σ — jam baratan
BAR_DAILY_FRACTION         = 0.40    # fraksi jam baratan minimum untuk hari
SMOOTH_WINDOW_DAYS         = 7       # smoothing fraksi harian
EPISODE_MIN_DAYS           = 5       # durasi minimum episode
SEASON_GAP_MAX_DAYS        = 10      # jeda maksimum antar-episode untuk musim
SEASON_MIN_DAYS            = 15      # durasi minimum musim lengkap

# ── Ambang onset/peak/offset ─────────────────────────────────────────────
ONSET_Z_THRESHOLD          = 0.5
ONSET_SUSTAIN_DAYS         = 5

# ── Jendela analisis onset (setelah reversal monsoon) ────────────────────
REVERSAL_DOPY_REFERENCE    = 131.0
ONSET_WINDOW_HI            = 280.0

# ── Basis mangsa R10 ─────────────────────────────────────────────────────
R10_MUSIM_START = {
    "Katiga":   12,
    "Labuh":   131,
    "Rendheng":185,
    "Mareng":  305,
}

MUSIM_MEMBERS = {
    "Katiga":   (1, 2, 3),
    "Labuh":    (4, 5, 6),
    "Rendheng": (7, 8, 9),
    "Mareng":   (10, 11, 12),
}

MANGSA_NAMES = {
    1: "Kasa", 2: "Karo", 3: "Katiga",
    4: "Kapat", 5: "Kalima", 6: "Kanem",
    7: "Kapitu", 8: "Kawolu", 9: "Kasanga",
    10: "Kasadasa", 11: "Desta", 12: "Sada",
}

MANGSA_DUR = {
    1: 41, 2: 23, 3: 24, 4: 25, 5: 27, 6: 43,
    7: 43, 8: 26, 9: 25, 10: 24, 11: 23, 12: 41,
}

# ── Komponen komposit baratan (kolom_sumber, bobot, transformasi) ───────
# transformasi: "raw" | "log1p" | "u_from_wd"
COMPOSITE_VARIABLES: Tuple[Tuple[str, float, str], ...] = (
    ("wind_direction_10m (°)", 2.0, "u_from_wd"),
    ("cloud_cover (%)",        1.0, "raw"),
    ("precipitation (mm)",     1.0, "log1p"),
    ("relative_humidity_2m (%)", 1.0, "raw"),
    ("total_column_integrated_water_vapour (kg/m²)", 1.0, "raw"),
    ("soil_moisture_0_to_7cm (m³/m³)", 1.0, "raw"),
)

# ── Variabel onset/peak/offset (label, jenis) ───────────────────────────
ONSET_VARIABLES: Tuple[Tuple[str, str, str], ...] = (
    ("u_comp",              "Komponen barat angin 10m", "raw"),
    ("u_comp_100",          "Komponen barat angin 100m", "raw"),
    ("cloud_cover (%)",     "Tutupan awan total",       "raw"),
    ("cloud_cover_low (%)", "Tutupan awan rendah",      "raw"),
    ("cloud_cover_mid (%)", "Tutupan awan menengah",    "raw"),
    ("precipitation (mm)",  "Curah hujan",              "raw"),
    ("weather_code",        "Cuaca basah (kode ≥ 51)",  "wcode_wet"),
    ("relative_humidity_2m (%)", "Kelembaban relatif",  "raw"),
    ("dew_point_2m (°C)",   "Titik embun",              "raw"),
    ("total_column_integrated_water_vapour (kg/m²)",
                            "Uap air kolom (TCWV)",     "raw"),
    ("soil_moisture_0_to_7cm (m³/m³)",  "Soil moisture 0–7cm",   "raw"),
    ("soil_moisture_7_to_28cm (m³/m³)", "Soil moisture 7–28cm",  "raw"),
    ("soil_moisture_28_to_100cm (m³/m³)", "Soil moisture 28–100cm", "raw"),
)

# ── Variabel ciri modern per mangsa ──────────────────────────────────────
MANGSA_VARIABLES: Tuple[Tuple[str, str, str], ...] = (
    # Atmosfer
    ("u_comp",                     "u10",       "raw"),
    ("u_comp_100",                 "u100",      "raw"),
    ("cloud_cover (%)",            "cloud",     "raw"),
    ("cloud_cover_low (%)",        "cloud_lo",  "raw"),
    ("cloud_cover_mid (%)",        "cloud_mid", "raw"),
    ("cloud_cover_high (%)",       "cloud_hi",  "raw"),
    ("precipitation (mm)",         "precip",    "raw"),
    ("rain (mm)",                  "rain",      "raw"),
    ("relative_humidity_2m (%)",   "RH",        "raw"),
    ("dew_point_2m (°C)",          "Td",        "raw"),
    ("total_column_integrated_water_vapour (kg/m²)", "TCWV", "raw"),
    ("vapour_pressure_deficit (kPa)", "VPD",     "raw"),
    ("shortwave_radiation (W/m²)", "rad",       "raw"),
    ("sunshine_duration (s)",      "sun",       "raw"),
    # Tanah
    ("soil_moisture_0_to_7cm (m³/m³)",     "SM07",    "raw"),
    ("soil_moisture_7_to_28cm (m³/m³)",    "SM728",   "raw"),
    ("soil_moisture_28_to_100cm (m³/m³)",  "SM28100", "raw"),
    ("soil_temperature_0_to_7cm (°C)",     "sT07",    "raw"),
    ("soil_temperature_7_to_28cm (°C)",    "sT728",   "raw"),
    ("soil_temperature_28_to_100cm (°C)",  "sT28100", "raw"),
    ("soil_temperature_100_to_255cm (°C)", "sT100255","raw"),
    # Suhu & angin
    ("temperature_2m (°C)",             "T2m",     "raw"),
    ("apparent_temperature (°C)",       "Tapp",    "raw"),
    ("wind_gusts_10m (km/h)",           "gust",    "raw"),
    ("wind_speed_10m (km/h)",           "WS",      "raw"),
    ("surface_pressure (hPa)",          "pressure","raw"),
    ("et0_fao_evapotranspiration (mm)", "ET0",     "raw"),
    # Weather code (7 kategori probabilitas)
    ("weather_code", "wcode_clear",   "wcode:0"),
    ("weather_code", "wcode_cloudy",  "wcode:1"),
    ("weather_code", "wcode_fog",     "wcode:2"),
    ("weather_code", "wcode_drizzle", "wcode:3"),
    ("weather_code", "wcode_rain",    "wcode:4"),
    ("weather_code", "wcode_shower",  "wcode:5"),
    ("weather_code", "wcode_storm",   "wcode:6"),
)

WCODE_CATEGORIES: Tuple[Tuple[int, ...], ...] = (
    (0,),                           # clear
    (1, 2, 3),                      # cloudy
    (45, 48),                       # fog
    (51, 53, 55, 56, 57),           # drizzle
    (61, 63, 65, 66, 67),           # rain
    (80, 81, 82),                   # shower
    (95, 96, 99),                   # storm
)


# ══════════════════════════════════════════════════════════════════════════
# Section 2 · Utilitas tampilan
# ══════════════════════════════════════════════════════════════════════════

def box_top(title: str = "") -> str:
    if not title:
        return "╔" + "═" * (W - 2) + "╗"
    inner = f"  {title}  "
    pad = W - 2 - len(inner)
    if pad < 0:
        inner, pad = inner[:W - 2], 0
    left = pad // 2
    return "╔" + "═" * left + inner + "═" * (pad - left) + "╗"


def box_mid() -> str:
    return "╠" + "═" * (W - 2) + "╣"


def box_bot() -> str:
    return "╚" + "═" * (W - 2) + "╝"


def box_row(text: str) -> str:
    cw = W - 4
    raw = str(text)
    if len(raw) <= cw:
        return "║ " + raw + " " * (cw - len(raw)) + " ║"
    return "║ " + raw[:cw] + " ║"


def hbar(indent: int = 2) -> str:
    return " " * indent + "─" * (W - indent)


def sec_header(label: str, sub: str = "") -> None:
    title = f"▌▌ {label.upper()}"
    if sub:
        title += f" — {sub}"
    print()
    print(title)
    print("  " + "─" * (W - 4))


def print_header(title: str, subtitle: str = "") -> None:
    print()
    print(box_top())
    print(box_row("EV09-BARATAN — ARAK-ARAKAN AWAN DARI BARAT"))
    print(box_row(title))
    if subtitle:
        print(box_row(subtitle))
    print(box_row("ERA5/ERA5-Land IFS-HRES · 2015–2026 · MJS −7.5220°S 112.5661°E"))
    print(box_bot())


# ══════════════════════════════════════════════════════════════════════════
# Section 3 · Pemuatan data
# ══════════════════════════════════════════════════════════════════════════

def find_data_file(filename: str) -> Optional[str]:
    if not filename:
        return None
    for folder in (".", os.path.dirname(os.path.abspath(__file__))):
        p = os.path.join(folder, filename)
        if os.path.exists(p):
            return p
    return None


def _read_openmeteo_csv(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as fh:
        skip = 0
        for i, line in enumerate(fh):
            if line.lstrip().startswith("time,"):
                skip = i
                break
    df = pd.read_csv(path, skiprows=skip)
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").reset_index(drop=True)


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Tambahkan u_comp (unit vektor) dari arah angin 10m & 100m."""
    d = df.copy()
    if "wind_direction_10m (°)" in d.columns:
        d["u_comp"] = -np.sin(np.deg2rad(d["wind_direction_10m (°)"].values))
    if "wind_direction_100m (°)" in d.columns:
        d["u_comp_100"] = -np.sin(np.deg2rad(d["wind_direction_100m (°)"].values))
    return d


def _attach_dopy(df: pd.DataFrame) -> pd.DataFrame:
    """Hitung dopy (day-of-pranata-year, 0–364) untuk setiap baris."""
    t = df["time"]
    year = t.dt.year
    anchor = pd.to_datetime(dict(year=year, month=ANCHOR_MONTH,
                                 day=ANCHOR_DAY))
    anchor_prev = pd.to_datetime(dict(year=year - 1,
                                      month=ANCHOR_MONTH, day=ANCHOR_DAY))
    delta = np.where(t < anchor,
                     (t - anchor_prev).dt.days,
                     (t - anchor).dt.days)
    d = df.copy()
    d["dopy"] = np.clip(delta, 0, 364)
    return d


def load_hourly() -> Optional[pd.DataFrame]:
    """Muat data hourly P1 (fallback P2), tambahkan kolom turunan & dopy."""
    path = None
    for c in CANDIDATES:
        path = find_data_file(c)
        if path is not None:
            break
    if path is None:
        print("  [!] File hourly10yr tidak ditemukan.")
        return None
    print(f"  [i] Membaca: {os.path.basename(path)}")
    df = _read_openmeteo_csv(path)
    df = _add_derived_columns(df)
    df = _attach_dopy(df)
    print(f"  [i] {len(df):,} baris · "
          f"{df['time'].min().date()} → {df['time'].max().date()}")
    return df


# ══════════════════════════════════════════════════════════════════════════
# Section 4 · Komposit baratan
# ══════════════════════════════════════════════════════════════════════════

def _extract_series(df: pd.DataFrame,
                    col: str,
                    transform: str) -> Optional[np.ndarray]:
    """Ambil seri dari kolom & terapkan transformasi."""
    if transform == "u_from_wd":
        if col not in df.columns:
            return None
        return -np.sin(np.deg2rad(df[col].values.astype(float)))
    if col not in df.columns:
        return None
    v = df[col].values.astype(float)
    if transform == "log1p":
        return np.log1p(np.maximum(v, 0.0))
    return v


def compute_composite(df: pd.DataFrame
                      ) -> Tuple[Optional[np.ndarray],
                                 List[Tuple[str, float, float]]]:
    """Hitung indeks komposit baratan = jumlah terbobot z-score.

    Returns
    -------
    composite : np.ndarray atau None
    components : list of (nama_komponen, bobot, std_before_z)
    """
    z_list: List[np.ndarray] = []
    w_list: List[float] = []
    info:   List[Tuple[str, float, float]] = []

    for col, weight, transform in COMPOSITE_VARIABLES:
        arr = _extract_series(df, col, transform)
        if arr is None:
            continue
        mask = np.isfinite(arr)
        if mask.sum() < 5000:
            continue
        mu = np.nanmean(arr)
        sd = np.nanstd(arr)
        if sd < 1e-9:
            continue
        z = (arr - mu) / sd
        z_list.append(z)
        w_list.append(weight)
        info.append((col.split(" (")[0], weight, sd))

    if len(z_list) < 3:
        return None, []

    w_arr = np.array(w_list)
    w_arr = w_arr / w_arr.sum()
    stack = np.stack(z_list, axis=0)
    composite = np.nansum(stack * w_arr[:, None], axis=0)
    return composite, info


# ══════════════════════════════════════════════════════════════════════════
# Section 5 · Deteksi episode & musim
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class Episode:
    start: datetime
    end:   datetime
    days:  int


@dataclass
class Season:
    start:      datetime
    end:        datetime
    days:       int
    start_dopy: float
    end_dopy:   float
    episode_n:  int = 0


def _aggregate_daily_baratan(df: pd.DataFrame,
                             composite: np.ndarray
                             ) -> pd.DataFrame:
    """Hitung hari baratan dari komposit per-jam."""
    hour_bar = composite >= COMPOSITE_HOUR_THRESHOLD

    d = df[["time"]].copy()
    d["_date"] = d["time"].dt.normalize()
    d["flag"] = hour_bar.astype(float)
    daily = (d.groupby("_date")
              .agg(flag_sum=("flag", "sum"), n=("flag", "size"))
              .reset_index())
    daily["bar_frac"] = daily["flag_sum"] / daily["n"]
    daily = daily.sort_values("_date").reset_index(drop=True)
    daily["bar_smooth"] = (daily["bar_frac"]
                            .rolling(SMOOTH_WINDOW_DAYS, center=True,
                                     min_periods=SMOOTH_WINDOW_DAYS // 2)
                            .mean())
    daily["is_bar"] = daily["bar_smooth"] >= BAR_DAILY_FRACTION
    return daily


def _find_episodes(daily: pd.DataFrame) -> List[Episode]:
    """Cari episode baratan berurutan ≥ EPISODE_MIN_DAYS."""
    mask = daily["is_bar"].values
    dates = daily["_date"].values
    out: List[Episode] = []
    cur_len, cur_start = 0, None

    for i, v in enumerate(mask):
        if v:
            if cur_len == 0:
                cur_start = dates[i]
            cur_len += 1
        else:
            if cur_len >= EPISODE_MIN_DAYS:
                end = pd.Timestamp(dates[i - 1])
                out.append(Episode(
                    start=pd.Timestamp(cur_start).to_pydatetime(),
                    end=end.to_pydatetime(),
                    days=cur_len,
                ))
            cur_len = 0
    if cur_len >= EPISODE_MIN_DAYS:
        end = pd.Timestamp(dates[-1])
        out.append(Episode(
            start=pd.Timestamp(cur_start).to_pydatetime(),
            end=end.to_pydatetime(),
            days=cur_len,
        ))
    return out


def _merge_episodes(episodes: List[Episode],
                    gap_max_days: int = SEASON_GAP_MAX_DAYS
                    ) -> List[Season]:
    """Gabungkan episode dengan jeda ≤ gap_max_days menjadi musim."""
    if not episodes:
        return []
    seasons: List[Season] = []
    cur_start = episodes[0].start
    cur_end   = episodes[0].end
    cur_n     = 1

    for ep in episodes[1:]:
        gap = (ep.start - cur_end).days
        if gap <= gap_max_days:
            cur_end = ep.end
            cur_n += 1
        else:
            days = (cur_end - cur_start).days + 1
            if days >= SEASON_MIN_DAYS:
                seasons.append(Season(
                    start=cur_start, end=cur_end, days=days,
                    start_dopy=0.0, end_dopy=0.0, episode_n=cur_n,
                ))
            cur_start, cur_end, cur_n = ep.start, ep.end, 1

    days = (cur_end - cur_start).days + 1
    if days >= SEASON_MIN_DAYS:
        seasons.append(Season(
            start=cur_start, end=cur_end, days=days,
            start_dopy=0.0, end_dopy=0.0, episode_n=cur_n,
        ))
    return seasons


def _lookup_dopy(date_obj: datetime,
                 daily: pd.DataFrame) -> float:
    """Cari dopy untuk tanggal tertentu dari DataFrame daily."""
    ts = pd.Timestamp(date_obj)
    row = daily.loc[daily["_date"] == ts, "dopy"]
    if len(row) == 0:
        return float("nan")
    return float(row.iloc[0])


def detect_baratan(df: pd.DataFrame,
                   composite: np.ndarray
                   ) -> Tuple[List[Episode], List[Season], pd.DataFrame]:
    """Deteksi episode & musim baratan dari komposit."""
    daily = _aggregate_daily_baratan(df, composite)
    # tambahkan dopy
    t = daily["_date"]
    year = t.dt.year
    anchor = pd.to_datetime(dict(year=year, month=ANCHOR_MONTH,
                                 day=ANCHOR_DAY))
    anchor_prev = pd.to_datetime(dict(year=year - 1,
                                      month=ANCHOR_MONTH, day=ANCHOR_DAY))
    daily["dopy"] = np.clip(
        np.where(t < anchor,
                 (t - anchor_prev).dt.days,
                 (t - anchor).dt.days),
        0, 364,
    )
    episodes = _find_episodes(daily)
    seasons  = _merge_episodes(episodes)
    for s in seasons:
        s.start_dopy = _lookup_dopy(s.start, daily)
        s.end_dopy   = _lookup_dopy(s.end, daily)
    return episodes, seasons, daily


# ══════════════════════════════════════════════════════════════════════════
# Section 6 · Onset / peak / offset
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class OnsetCycle:
    label:      str
    onset_dopy: float
    peak_dopy:  float
    offset_dopy: float

    @property
    def duration(self) -> float:
        return self.offset_dopy - self.onset_dopy

    @property
    def delta_reversal(self) -> float:
        return self.onset_dopy - REVERSAL_DOPY_REFERENCE


def _climatology_daily(series: np.ndarray,
                       dopy: np.ndarray) -> Optional[np.ndarray]:
    """Rata-rata harian per dopy 0..364 (vektor, tanpa loop)."""
    mask = np.isfinite(series)
    if mask.sum() < 5000:
        return None
    s = series[mask]
    d = dopy[mask]

    sums = np.zeros(365)
    counts = np.zeros(365)
    np.add.at(sums, d, s)
    np.add.at(counts, d, 1)

    with np.errstate(invalid="ignore"):
        clim = np.where(counts > 0, sums / np.maximum(counts, 1),
                        np.nan)

    # Interpolasi linier untuk dopy yang kosong
    valid = np.isfinite(clim)
    if valid.sum() < 30:
        return None
    idx = np.arange(365)
    clim = np.interp(idx, idx[valid], clim[valid])
    return clim


def _find_onset_peak_offset(clim: np.ndarray,
                            start_dopy: float = REVERSAL_DOPY_REFERENCE,
                            end_dopy:   float = ONSET_WINDOW_HI,
                            threshold:  float = ONSET_Z_THRESHOLD,
                            sustain:    int   = ONSET_SUSTAIN_DAYS,
                            ) -> Optional[Tuple[float, float, float]]:
    """Cari (onset, peak, offset) dari klimatologi harian."""
    n = len(clim)
    if n < 30:
        return None
    mu = clim.mean()
    sd = clim.std()
    if sd < 1e-9:
        return None
    z = (clim - mu) / sd

    s = max(0, int(start_dopy))
    e = min(n, int(end_dopy))
    if e - s < 10:
        return None

    # Peak = argmax z dalam jendela
    peak_i = s + int(np.argmax(z[s:e]))

    # Onset = dopy pertama sebelum peak dengan z ≥ threshold sustained
    onset_i = None
    for i in range(s, peak_i):
        if i + sustain <= n and np.all(z[i:i + sustain] >= threshold):
            onset_i = i
            break
    if onset_i is None:
        return None

    # Offset = dopy pertama setelah peak dengan z < threshold sustained
    offset_i = None
    for i in range(peak_i, n - sustain):
        if np.all(z[i:i + sustain] < threshold):
            offset_i = i
            break
    if offset_i is None:
        offset_i = n - 1

    return float(onset_i), float(peak_i), float(offset_i)


def _wcode_wet_mask(df: pd.DataFrame) -> Optional[np.ndarray]:
    c = "weather_code (wmo code)"
    if c not in df.columns:
        return None
    wc = df[c].values
    wet = ((wc >= 51) & (wc <= 67)) | \
          ((wc >= 80) & (wc <= 82)) | \
          ((wc >= 95) & (wc <= 99))
    return wet.astype(float)


def compute_onset_cycles(df: pd.DataFrame) -> List[OnsetCycle]:
    """Hitung siklus onset/peak/offset untuk variabel kunci."""
    dopy = df["dopy"].values
    out: List[OnsetCycle] = []

    for col, label, kind in ONSET_VARIABLES:
        if kind == "wcode_wet":
            arr = _wcode_wet_mask(df)
        else:
            if col not in df.columns:
                continue
            arr = df[col].values.astype(float)
        if arr is None:
            continue

        clim = _climatology_daily(arr, dopy)
        if clim is None:
            continue
        cyc = _find_onset_peak_offset(clim)
        if cyc is None:
            continue
        out.append(OnsetCycle(
            label=label,
            onset_dopy=cyc[0],
            peak_dopy=cyc[1],
            offset_dopy=cyc[2],
        ))

    out.sort(key=lambda c: c.onset_dopy)
    return out


# ══════════════════════════════════════════════════════════════════════════
# Section 7 · Ciri modern per mangsa
# ══════════════════════════════════════════════════════════════════════════

def build_r10_boundaries() -> Dict[int, Tuple[float, float]]:
    """Hitung batas dopy tiap mangsa untuk skenario R10.

    Interpolasi linear di dalam musim mempertahankan durasi relatif
    tradisional.
    """
    orig_starts = {1: 0}
    cum = 0
    for i in range(1, 12):
        cum += MANGSA_DUR[i]
        orig_starts[i + 1] = cum

    orig_musim_start = {
        mu: orig_starts[MUSIM_MEMBERS[mu][0]]
        for mu in MUSIM_MEMBERS
    }
    orig_musim_next = {
        "Katiga":   orig_musim_start["Labuh"],
        "Labuh":    orig_musim_start["Rendheng"],
        "Rendheng": orig_musim_start["Mareng"],
        "Mareng":   365,
    }
    r10_start = R10_MUSIM_START
    r10_next = {
        "Katiga":   r10_start["Labuh"],
        "Labuh":    r10_start["Rendheng"],
        "Rendheng": r10_start["Mareng"],
        "Mareng":   365 + r10_start["Katiga"],
    }

    new_starts: Dict[int, float] = {}
    for musim, members in MUSIM_MEMBERS.items():
        o0 = orig_musim_start[musim]
        o_len = orig_musim_next[musim] - o0
        n0 = r10_start[musim]
        n_len = r10_next[musim] - n0
        for mno in members:
            frac = (orig_starts[mno] - o0) / o_len
            new_starts[mno] = n0 + frac * n_len

    sorted_nos = sorted(new_starts.keys())
    ranges: Dict[int, Tuple[float, float]] = {}
    for i, no in enumerate(sorted_nos):
        nxt = sorted_nos[(i + 1) % 12]
        s = new_starts[no]
        e = (new_starts[nxt] if nxt != 1
             else 365 + new_starts[1]) - 1
        ranges[no] = (s, e)
    return ranges


def _select_dopy_range(mask: np.ndarray,
                       dopy: np.ndarray,
                       s: float, e: float) -> np.ndarray:
    """Boolean selection untuk rentang dopy yang mungkin wrap (e ≥ 365)."""
    if e >= 365:
        return mask & ((dopy >= s) | (dopy <= e - 365))
    return mask & (dopy >= s) & (dopy <= e)


def _wcode_category_mask(df: pd.DataFrame,
                         cat_idx: int) -> Optional[np.ndarray]:
    if cat_idx < 0 or cat_idx >= len(WCODE_CATEGORIES):
        return None
    c = "weather_code (wmo code)"
    if c not in df.columns:
        return None
    wc = df[c].values
    mask = np.zeros(len(wc), dtype=bool)
    for code in WCODE_CATEGORIES[cat_idx]:
        mask |= (wc == code)
    return mask.astype(float)


@dataclass
class MangsaStats:
    """Statistik per-mangsa untuk satu variabel."""
    label:    str
    raw:      Dict[int, float] = field(default_factory=dict)
    zscore:   Dict[int, float] = field(default_factory=dict)


def compute_mangsa_stats(df: pd.DataFrame,
                         ranges: Dict[int, Tuple[float, float]]
                         ) -> Tuple[Dict[str, MangsaStats],
                                    Dict[str, MangsaStats]]:
    """Hitung rata-rata raw & z-score per mangsa.

    Return
    ------
    (raw_stats, z_stats) — setiap dict adalah label -> MangsaStats
    """
    dopy = df["dopy"].values
    raw_out: Dict[str, MangsaStats] = {}
    z_out:   Dict[str, MangsaStats] = {}

    for col, label, kind in MANGSA_VARIABLES:
        if kind.startswith("wcode:"):
            cat_idx = int(kind.split(":")[1])
            arr = _wcode_category_mask(df, cat_idx)
        else:
            if col not in df.columns:
                continue
            arr = df[col].values.astype(float)
        if arr is None:
            continue

        mask_all = np.isfinite(arr)
        if mask_all.sum() < 5000:
            continue
        mu = np.nanmean(arr)
        sd = np.nanstd(arr)
        if sd < 1e-9:
            # Konstan: simpan raw saja
            stats = MangsaStats(label=label)
            for no, (s_d, e_d) in ranges.items():
                sel = _select_dopy_range(mask_all, dopy, s_d, e_d)
                if sel.sum() >= 50:
                    stats.raw[no] = float(np.nanmean(arr[sel]))
            raw_out[label] = stats
            continue

        z = (arr - mu) / sd
        stats_r = MangsaStats(label=label)
        stats_z = MangsaStats(label=label)
        for no, (s_d, e_d) in ranges.items():
            sel = _select_dopy_range(mask_all, dopy, s_d, e_d)
            if sel.sum() < 50:
                continue
            stats_r.raw[no] = float(np.nanmean(arr[sel]))
            stats_z.zscore[no] = float(np.nanmean(z[sel]))
        raw_out[label] = stats_r
        z_out[label]   = stats_z

    return raw_out, z_out


# ══════════════════════════════════════════════════════════════════════════
# Section 8 · Laporan
# ══════════════════════════════════════════════════════════════════════════

def _dopy_date_str(dopy: float) -> str:
    anchor = datetime(2025, ANCHOR_MONTH, ANCHOR_DAY)
    d = anchor + timedelta(days=int(round(dopy)))
    return f"{d.day:02d} {MONTHS[d.month-1]}"


def _z_cell(v: Optional[float]) -> str:
    if v is None:
        return f"{'—':>8}"
    return f"{v:>+8.2f}"


def _raw_cell(v: Optional[float]) -> str:
    if v is None:
        return f"{'—':>9}"
    if abs(v) >= 100:
        return f"{v:>9.1f}"
    if abs(v) >= 10:
        return f"{v:>9.2f}"
    return f"{v:>9.3f}"


# ── A · Komposit & komponen ──────────────────────────────────────────────

def print_section_a_composite(composite: np.ndarray,
                              components: List[Tuple[str, float, float]],
                              df: pd.DataFrame) -> None:
    sec_header("A · KOMPOSIT BARATAN")

    print(f"  Jumlah jam total     : {len(composite):,}")
    print(f"  Ambang jam baratan   : z ≥ {COMPOSITE_HOUR_THRESHOLD:+.2f}")
    hour_bar = composite >= COMPOSITE_HOUR_THRESHOLD
    print(f"  Jam baratan          : {int(hour_bar.sum()):,} "
          f"({100 * hour_bar.mean():.1f}%)")

    print()
    print("  Komponen & bobot ternormalisasi:")
    print("  " + "─" * 62)
    print(f"  {'Komponen':<40}{'Bobot':>10}{'Std':>12}")
    print("  " + "─" * 62)
    w_sum = sum(w for _, w, _ in components)
    for name, weight, sd in components:
        w_norm = weight / w_sum
        print(f"  {name:<40}{w_norm:>10.3f}{sd:>12.3g}")


# ── B · Episode & musim ──────────────────────────────────────────────────

def print_section_b_baratan(episodes: List[Episode],
                            seasons: List[Season]) -> None:
    sec_header("B · DETEKSI EPISODE & MUSIM BARATAN")

    print(f"  Episode (run ≥ {EPISODE_MIN_DAYS} hari)   : {len(episodes)}")
    print(f"  Musim (gap ≤ {SEASON_GAP_MAX_DAYS} hr)     : {len(seasons)}")
    print()

    if not seasons:
        print("  [!] Tidak ada musim baratan terdeteksi.")
        return

    print("  MUSIM BARATAN KRONOLOGIS")
    print("  " + "─" * 68)
    print(f"  {'#':<3}{'Mulai':<14}{'Berakhir':<14}"
          f"{'Durasi':>8}{'Ep':>4}")
    print("  " + "─" * 68)
    for k, s in enumerate(seasons, 1):
        print(f"  {k:<3}{s.start.strftime('%d %b %Y'):<14}"
              f"{s.end.strftime('%d %b %Y'):<14}"
              f"{s.days:>6} hr{s.episode_n:>4}")

    # Statistik agregat
    starts = np.array([s.start_dopy for s in seasons
                       if np.isfinite(s.start_dopy)])
    ends   = np.array([s.end_dopy for s in seasons
                       if np.isfinite(s.end_dopy)])
    durs   = np.array([s.days for s in seasons])

    print()
    print("  STATISTIK AGREGAT")
    print("  " + "─" * 68)
    if len(starts) >= 2:
        print(f"  Mulai    : dopy {starts.mean():.1f} "
              f"± {starts.std(ddof=1):.1f}  "
              f"({_dopy_date_str(starts.mean())})")
    if len(ends) >= 2:
        print(f"  Berakhir : dopy {ends.mean():.1f} "
              f"± {ends.std(ddof=1):.1f}  "
              f"({_dopy_date_str(ends.mean())})")
    if len(durs) >= 2:
        print(f"  Durasi   : {durs.mean():.1f} ± {durs.std(ddof=1):.1f} hari"
              f"  (median {np.median(durs):.0f}, "
              f"rentang {durs.min()}–{durs.max()})")


# ── C · Onset/peak/offset ────────────────────────────────────────────────

def print_section_c_onset(cycles: List[OnsetCycle]) -> None:
    sec_header("C · SIKLUS ONSET / PEAK / OFFSET",
               f"Relatif terhadap reversal monsoon dopy "
               f"{REVERSAL_DOPY_REFERENCE:.0f}")

    if not cycles:
        print("  [!] Tidak ada siklus yang bisa dihitung.")
        return

    print(f"  Ambang onset  : z ≥ {ONSET_Z_THRESHOLD:+.2f} "
          f"sustained {ONSET_SUSTAIN_DAYS} hari")
    print(f"  Jendela cari  : dopy "
          f"[{REVERSAL_DOPY_REFERENCE:.0f}, {ONSET_WINDOW_HI:.0f}]")
    print()
    print(f"  {'Variabel':<32}{'Onset':>12}{'Peak':>12}"
          f"{'Offset':>12}{'Δ':>7}{'Durasi':>9}")
    print("  " + "─" * 84)
    for c in cycles:
        print(f"  {c.label:<32}"
              f"{_dopy_date_str(c.onset_dopy):>12}"
              f"{_dopy_date_str(c.peak_dopy):>12}"
              f"{_dopy_date_str(c.offset_dopy):>12}"
              f"{c.delta_reversal:>+7.0f}"
              f"{c.duration:>8.0f} hr")


# ── D · Ciri modern per mangsa ───────────────────────────────────────────

def _print_mangsa_table(title: str,
                        stats: Dict[str, MangsaStats],
                        use_z: bool,
                        cell_fn,
                        labels_order: List[str]) -> None:
    avail = [lb for lb in labels_order if lb in stats]
    if not avail:
        return

    # Hitung berapa kolom yang muat: prefix 16 char + 9 char per sel
    max_cols = max(1, (W - 16) // 9)
    chunks = [avail[i:i + max_cols]
              for i in range(0, len(avail), max_cols)]

    for k, chunk in enumerate(chunks, 1):
        sub = f" [{k}/{len(chunks)}]" if len(chunks) > 1 else ""
        print()
        print(f"  {title}{sub}")
        print("  " + "─" * (16 + 9 * len(chunk)))
        hdr = f"  {'No':<3}{'Mangsa':<10}"
        for lb in chunk:
            hdr += f"{lb:>9}"
        print(hdr[:W])
        print("  " + "─" * (16 + 9 * len(chunk)))

        for no in sorted(MANGSA_NAMES):
            row = f"  {no:<3}{MANGSA_NAMES[no]:<10}"
            for lb in chunk:
                v = (stats[lb].zscore.get(no) if use_z
                     else stats[lb].raw.get(no))
                row += cell_fn(v)
            print(row[:W])


def print_section_d_mangsa(raw_stats: Dict[str, MangsaStats],
                            z_stats: Dict[str, MangsaStats]) -> None:
    sec_header("D · CIRI MODERN PER MANGSA (BASIS R10)")

    atmosfer = ["u10", "u100", "cloud", "cloud_lo", "cloud_mid",
                "cloud_hi", "precip", "rain", "RH", "Td", "TCWV",
                "VPD", "rad", "sun"]
    tanah    = ["SM07", "SM728", "SM28100",
                "sT07", "sT728", "sT28100", "sT100255"]
    suhu     = ["T2m", "Tapp", "gust", "WS", "pressure", "ET0"]
    wcode    = ["wcode_clear", "wcode_cloudy", "wcode_fog",
                "wcode_drizzle", "wcode_rain", "wcode_shower",
                "wcode_storm"]

    print()
    print("  Nilai mentah & z-score per mangsa. "
          "z = (nilai − mean tahunan) / std tahunan.")

    _print_mangsa_table("ATMOSFER — raw", raw_stats, False,
                         _raw_cell, atmosfer)
    _print_mangsa_table("ATMOSFER — z-score", z_stats, True,
                         _z_cell, atmosfer)

    _print_mangsa_table("TANAH — raw", raw_stats, False,
                         _raw_cell, tanah)
    _print_mangsa_table("TANAH — z-score", z_stats, True,
                         _z_cell, tanah)

    _print_mangsa_table("SUHU & ANGIN — raw", raw_stats, False,
                         _raw_cell, suhu)
    _print_mangsa_table("SUHU & ANGIN — z-score", z_stats, True,
                         _z_cell, suhu)

    _print_mangsa_table("WEATHER CODE — probabilitas", raw_stats, False,
                         _raw_cell, wcode)
    _print_mangsa_table("WEATHER CODE — z-score", z_stats, True,
                         _z_cell, wcode)


# ── E · Kontras antar musim ──────────────────────────────────────────────

def print_section_e_kontras(z_stats: Dict[str, MangsaStats]) -> None:
    sec_header("E · KONTRAS ANTAR MUSIM (RATA-RATA Z)")

    labels = ["u10", "u100", "cloud", "cloud_lo", "cloud_mid",
              "cloud_hi", "precip", "RH", "Td", "TCWV", "VPD",
              "SM07", "SM728", "SM28100",
              "sT07", "sT728", "sT28100", "sT100255",
              "T2m", "gust", "WS", "pressure", "ET0",
              "wcode_clear", "wcode_cloudy", "wcode_rain"]

    print()
    print(f"  {'Label':<12}{'Katiga':>12}{'Labuh':>12}"
          f"{'Rendheng':>12}{'Mareng':>12}")
    print("  " + "─" * 60)
    for lb in labels:
        if lb not in z_stats:
            continue
        row = f"  {lb:<12}"
        for musim in ("Katiga", "Labuh", "Rendheng", "Mareng"):
            members = MUSIM_MEMBERS[musim]
            vals = [z_stats[lb].zscore[m] for m in members
                    if m in z_stats[lb].zscore]
            row += (f"{np.mean(vals):>+12.2f}" if vals
                    else f"{'—':>12}")
        print(row)


# ── F · Narasi per mangsa ────────────────────────────────────────────────

def print_section_f_narasi(z_stats: Dict[str, MangsaStats]) -> None:
    sec_header("F · NARASI CIRI MODERN PER MANGSA",
               "Variabel dengan |z| ≥ 0.5")

    for no in sorted(MANGSA_NAMES):
        # Kumpulkan tinggi / rendah
        high: List[Tuple[str, float]] = []
        low:  List[Tuple[str, float]] = []
        for label, stats in z_stats.items():
            v = stats.zscore.get(no)
            if v is None:
                continue
            if v >= 0.5:
                high.append((label, v))
            elif v <= -0.5:
                low.append((label, v))

        # Urutkan berdasarkan |z| menurun
        high.sort(key=lambda t: -t[1])
        low.sort(key=lambda t: t[1])

        print()
        print(f"  ▸ Mangsa {no} — {MANGSA_NAMES[no]}")
        if high:
            items = ", ".join(f"{lb} ({v:+.2f})" for lb, v in high)
            print(f"    Tinggi : {items}")
        if low:
            items = ", ".join(f"{lb} ({v:+.2f})" for lb, v in low)
            print(f"    Rendah : {items}")
        if not high and not low:
            print("    (semua variabel di kisaran normal)")


# ── G · Dokumentasi metode ───────────────────────────────────────────────

def print_section_g_method() -> None:
    sec_header("G · METODE & REFERENSI")

    print(f"""
  KOMPOSIT BARATAN
  ────────────────
  Indeks kontinu dari {len(COMPOSITE_VARIABLES)} variabel dengan
  pembobotan (u_comp = 2, sisanya = 1). Setiap variabel di-z-score
  terhadap mean & std tahunan sebelum dijumlahkan. Ambang jam baratan
  adalah z ≥ {COMPOSITE_HOUR_THRESHOLD:+.2f}.

  DETEKSI EPISODE & MUSIM
  ───────────────────────
  Hari baratan = fraksi jam baratan dalam sehari (setelah smoothing
  {SMOOTH_WINDOW_DAYS} hari) ≥ {BAR_DAILY_FRACTION:.2f}.
  Episode = run berurutan hari baratan ≥ {EPISODE_MIN_DAYS} hari.
  Musim = gabungan episode dengan jeda ≤ {SEASON_GAP_MAX_DAYS} hari,
  durasi total ≥ {SEASON_MIN_DAYS} hari.

  ONSET / PEAK / OFFSET
  ─────────────────────
  Untuk {len(ONSET_VARIABLES)} variabel kunci:
    onset  = dopy pertama (setelah reversal dopy
             {REVERSAL_DOPY_REFERENCE:.0f}) dengan z ≥ {ONSET_Z_THRESHOLD:+.2f}
             sustained {ONSET_SUSTAIN_DAYS} hari
    peak   = dopy dengan z maksimum dalam jendela
             [{REVERSAL_DOPY_REFERENCE:.0f}, {ONSET_WINDOW_HI:.0f}]
    offset = dopy pertama setelah peak dengan z < {ONSET_Z_THRESHOLD:+.2f}
             sustained {ONSET_SUSTAIN_DAYS} hari

  CIRI MODERN PER MANGSA
  ──────────────────────
  Batas mangsa mengikuti skenario R10 (kalibrasi 2016–2025):
    Katiga mulai dopy {R10_MUSIM_START['Katiga']},
    Labuh mulai dopy {R10_MUSIM_START['Labuh']},
    Rendheng mulai dopy {R10_MUSIM_START['Rendheng']},
    Mareng mulai dopy {R10_MUSIM_START['Mareng']}.
  Durasi relatif antar mangsa dalam setiap musim dipertahankan seperti
  Pranata Mangsa tradisional.

  REFERENSI
  ─────────
  · Wheeler, M. C., & Hendon, H. H. (2004). An all-season real-time
    multivariate MJO index. Mon. Wea. Rev. 132(8):1917–1932.
  · Duchon, C. E. (1979). Lanczos filtering in one and two dimensions.
    J. Appl. Meteor. 18(8):1016–1022.
  · BMKG. Kriteria Musim Hujan Indonesia.
""")


# ══════════════════════════════════════════════════════════════════════════
# Section 9 · Laporan utama
# ══════════════════════════════════════════════════════════════════════════

def run_report(mode: str = "all") -> int:
    print_header(
        "Analisis Rezim Baratan",
        "Deteksi episode, siklus onset-peak-offset, ciri modern per mangsa",
    )
    df = load_hourly()
    if df is None:
        return 1

    composite, components = compute_composite(df)
    if composite is None:
        print("  [!] Komponen tidak cukup untuk membentuk komposit.")
        return 1

    if mode in ("all", "composite"):
        print_section_a_composite(composite, components, df)

    episodes: List[Episode] = []
    seasons:  List[Season]  = []
    if mode in ("all", "baratan"):
        episodes, seasons, _ = detect_baratan(df, composite)
        print_section_b_baratan(episodes, seasons)

    if mode in ("all", "onset"):
        cycles = compute_onset_cycles(df)
        print_section_c_onset(cycles)

    if mode in ("all", "mangsa"):
        ranges = build_r10_boundaries()
        raw_stats, z_stats = compute_mangsa_stats(df, ranges)
        print_section_d_mangsa(raw_stats, z_stats)
        print_section_e_kontras(z_stats)
        print_section_f_narasi(z_stats)

    if mode == "all":
        print_section_g_method()

    return 0


# ══════════════════════════════════════════════════════════════════════════
# Section 10 · CLI
# ══════════════════════════════════════════════════════════════════════════

def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="EV09baratan",
        description=(
            "Analisis rezim baratan (arak-arakan awan dari barat) dari "
            "data hourly Open-Meteo 2015–2026 di titik MJS."
        ),
    )
    ap.add_argument("--all", action="store_true",
                    help="Tampilkan semua seksi (default).")
    ap.add_argument("--composite", action="store_true",
                    help="Hanya komposit & komponennya.")
    ap.add_argument("--baratan", action="store_true",
                    help="Hanya deteksi episode & musim baratan.")
    ap.add_argument("--onset", action="store_true",
                    help="Hanya siklus onset/peak/offset.")
    ap.add_argument("--mangsa", action="store_true",
                    help="Hanya ciri modern per mangsa.")
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_argparser().parse_args(argv)

    if args.composite:
        return run_report("composite")
    if args.baratan:
        return run_report("baratan")
    if args.onset:
        return run_report("onset")
    if args.mangsa:
        return run_report("mangsa")
    return run_report("all")


if __name__ == "__main__":
    sys.exit(main())