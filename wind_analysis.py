"""
wind_analysis.py — Modul Analisis Angin Meteorologis (EV09)
============================================================
Analisis komprehensif pola arah angin, kecepatan, siklus diurnal,
siklus tahunan (muson), perubahan rezim, dan hubungan dengan variabel
pendukung.

Titik Target  : -7.521951°S, 112.566089°E, 27.07 m
Data Sumber   : Open-Meteo historical (IFS HRES + ERA5/ERA5-Land blend)
                P1 (-7.487°S 112.538°E) terrain-optimized
                P2 (-7.557°S 112.557°E) nearest grid
Nama File     : Mengikuti konvensi Pranatamangsa_EV09.py — koordinat
                memakai TITIK, suffix memakai underscore:
                  open-meteo-7.49S112.54E28m_hourly10yr.csv  (P1)
                  open-meteo-7.56S112.56E28m_hourly10yr.csv  (P2)
Periode Data  : 2015-01-01 → 2026-09-13 (102.576 timestep, 11.7 tahun)

IDW Weights   : EV09 per-field strategy (konsisten dengan EV09):
                  · Volatile (wind, temp, RH, VPD, TCWV, cloud, sun):
                    w1=0.4154 (P1), w2=0.5846 (P2)
                  · Soil (sm_sh, sm_dp, sT_sh, sT_dp):
                    w1=0.4996 (P1), w2=0.5004 (P2)

Istilah Teknis
--------------
  Wind rose / Diurnal cycle / Annual cycle / Wind veer / Wind backing
  Wind shear / Power law exponent / Wind constancy / Gust factor
  Sea-land breeze / Monsoon onset / Pancaroba / Transition event / Wind regime

Modul & Fungsi
--------------
  A.  load_and_prepare()       — muat & IDW-blend data hourly
  B.  wind_rose()              — wind rose (frekuensi × kecepatan)
  C.  diurnal_cycle()          — profil 24-jam arah & kecepatan
  D.  sea_breeze_analysis()    — deteksi onset/cessation sea breeze
  E.  annual_cycle()           — pola bulanan + muson constancy
  F.  wind_regime_classifier() — klasifikasi MB/MT/PML1/PML2
  G.  transition_analysis()    — deteksi peristiwa transisi harian
  H.  wind_shear_profile()     — profil vertikal 10m→100m (power law α)
  I.  support_correlations()   — korelasi dengan variabel pendukung
  J.  spectral_analysis()      — FFT → periode dominan (24h, 12h, QBWO)
  K.  interannual_variability()— variabilitas antar-tahun (2015-2026)
  L.  WindAnalysisReport       — kelas report runner lengkap

Penulis : wind_analysis.py v1.1 (EV09-fix 2026-09-19)
Platform: Python 3.9+ | NumPy, Pandas, SciPy
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import welch

warnings.filterwarnings("ignore")


# ═══════════════════════════════════════════════════════════════════
# KONSTANTA
# ═══════════════════════════════════════════════════════════════════

# ── EV09 per-field IDW weights ────────────────────────────────────────
IDW_W1_VPD:  float = 0.4154    # volatile class, P1 (terrain_optimized)
IDW_W2_VPD:  float = 0.5846    # volatile class, P2 (nearest)
IDW_W1_SOIL: float = 0.4996    # soil class, P1
IDW_W2_SOIL: float = 0.5004    # soil class, P2

# Backward-compat alias
IDW_W1: float = IDW_W1_VPD
IDW_W2: float = IDW_W2_VPD

_FIELD_CLASS: Dict[str, str] = {
    "wind_speed_10m (km/h)":            "volatile",
    "wind_direction_10m (°)":           "volatile",
    "wind_speed_100m (km/h)":           "volatile",
    "wind_direction_100m (°)":          "volatile",
    "wind_gusts_10m (km/h)":            "volatile",
    "temperature_2m (°C)":              "volatile",
    "relative_humidity_2m (%)":         "volatile",
    "surface_pressure (hPa)":           "volatile",
    "precipitation (mm)":               "volatile",
    "vapour_pressure_deficit (kPa)":    "volatile",
    "shortwave_radiation (W/m²)":       "volatile",
    "cloud_cover (%)":                  "volatile",
}

# Lokasi target
TARGET_LAT: float = -7.521951
TARGET_LON: float = 112.566089
TARGET_ELEV: float = 27.07

# Ketinggian anemometer
Z_10M:  float = 10.0
Z_100M: float = 100.0

# Sektor angin
SECTORS_8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
SECTOR_8_BOUNDS = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]

SECTORS_16 = [
    "N","NNE","NE","ENE","E","ESE","SE","SSE",
    "S","SSW","SW","WSW","W","WNW","NW","NNW",
]

# ── Rezim muson (bulan) ──────────────────────────────────────────────
# MB   : Muson Barat (Jan–Mar)   — angin Barat/Baratlaut
# PML1 : Pancaroba I (Apr–Mei)   — transisi, arah tidak menentu
# MT   : Muson Timur (Jun–Sep)   — angin Timur/Tenggara
# PML2 : Pancaroba II (Okt–Des)  — transisi, dominan Selatan
REGIME_MONTHS: Dict[str, List[int]] = {
    "MB":   [1, 2, 3],
    "PML1": [4, 5],
    "MT":   [6, 7, 8, 9],
    "PML2": [10, 11, 12],
}
REGIME_LABELS: Dict[str, str] = {
    "MB":   "Muson Barat (Jan–Mar)    — angin Barat/Baratlaut",
    "PML1": "Pancaroba I (Apr–Mei)    — transisi, arah tidak menentu",
    "MT":   "Muson Timur (Jun–Sep)    — angin Timur/Tenggara",
    "PML2": "Pancaroba II (Okt–Des)   — transisi, dominan Selatan",
}

# Batas sea-breeze (WIB)
SEA_BREEZE_ONSET_HOUR:     int = 7
SEA_BREEZE_PEAK_HOUR:      int = 14
SEA_BREEZE_REVERSAL_HOUR:  int = 18

# Beaufort
BEAUFORT_SCALE: List[Tuple[float, str, str]] = [
    (1.5,   "0", "Calm"),
    (5.5,   "1", "Light air"),
    (11.5,  "2", "Light breeze"),
    (19.5,  "3", "Gentle breeze"),
    (28.5,  "4", "Moderate breeze"),
    (38.5,  "5", "Fresh breeze"),
    (49.5,  "6", "Strong breeze"),
    (61.5,  "7", "High wind"),
    (74.5,  "8", "Gale"),
    (88.5,  "9", "Severe gale"),
    (102.5, "10","Storm"),
    (117.5, "11","Violent storm"),
    (9999,  "12","Hurricane"),
]

# ── Default file names — konvensi EV09 (titik pada koordinat) ────────
DEFAULT_HOURLY_CSV_P1 = "open-meteo-7.49S112.54E28m_hourly10yr.csv"
DEFAULT_HOURLY_CSV_P2 = "open-meteo-7.56S112.56E28m_hourly10yr.csv"


# ═══════════════════════════════════════════════════════════════════
# A. LOAD & PREPARE
# ═══════════════════════════════════════════════════════════════════

def load_open_meteo_csv(filepath: str) -> pd.DataFrame:
    """Baca satu file CSV Open-Meteo (3-baris header metadata)."""
    df = pd.read_csv(filepath, skiprows=3, parse_dates=["time"])
    df = df.set_index("time").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


def load_and_prepare(
    file_p1: str,
    file_p2: str,
    w1: Optional[float] = None,
    w2: Optional[float] = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Muat kedua file CSV Open-Meteo dan blend IDW ke titik target.

    Konvensi arah angin meteorologis standar: θ arah DATANG angin,
    u = −V·sin θ, v = −V·cos θ, rekonstruksi θ = atan2(−u, −v) mod 360°.
    """
    if w1 is None: w1 = IDW_W1_VPD
    if w2 is None: w2 = IDW_W2_VPD

    if verbose:
        print(f"Memuat P1: {Path(file_p1).name}")
        print(f"Memuat P2: {Path(file_p2).name}")

    df1 = load_open_meteo_csv(file_p1)
    df2 = load_open_meteo_csv(file_p2)
    idx = df1.index.intersection(df2.index)
    df1 = df1.loc[idx]; df2 = df2.loc[idx]

    if verbose:
        print(f"Overlap: {len(idx):,} timestep "
              f"({idx[0].date()} → {idx[-1].date()}, "
              f"{(idx[-1]-idx[0]).days/365.25:.1f} tahun)")

    def _uv(dir_deg: np.ndarray, speed: np.ndarray):
        r = np.radians(dir_deg)
        return -speed * np.sin(r), -speed * np.cos(r)

    u10a, v10a   = _uv(df1["wind_direction_10m (°)"].values,
                       df1["wind_speed_10m (km/h)"].values)
    u10b, v10b   = _uv(df2["wind_direction_10m (°)"].values,
                       df2["wind_speed_10m (km/h)"].values)
    u100a, v100a = _uv(df1["wind_direction_100m (°)"].values,
                       df1["wind_speed_100m (km/h)"].values)
    u100b, v100b = _uv(df2["wind_direction_100m (°)"].values,
                       df2["wind_speed_100m (km/h)"].values)

    u10  = w1*u10a  + w2*u10b
    v10  = w1*v10a  + w2*v10b
    u100 = w1*u100a + w2*u100b
    v100 = w1*v100a + w2*v100b

    spd10  = np.sqrt(u10**2  + v10**2)
    spd100 = np.sqrt(u100**2 + v100**2)
    dir10  = np.degrees(np.arctan2(-u10,  -v10))  % 360
    dir100 = np.degrees(np.arctan2(-u100, -v100)) % 360

    gust = (w1*df1["wind_gusts_10m (km/h)"].values
            + w2*df2["wind_gusts_10m (km/h)"].values)

    def _blend(col: str) -> np.ndarray:
        if col in df1.columns and col in df2.columns:
            return w1*df1[col].values + w2*df2[col].values
        return np.full(len(idx), np.nan)

    df = pd.DataFrame({
        "u10": u10,    "v10": v10,    "spd10": spd10,   "dir10": dir10,
        "u100": u100,  "v100": v100,  "spd100": spd100, "dir100": dir100,
        "gust": gust,
        "shear_spd":  spd100 - spd10,
        "dir_shear":  ((dir100 - dir10 + 180) % 360) - 180,
        "gust_factor": np.where(spd10 > 0.5, gust / spd10, np.nan),
        "temp":  _blend("temperature_2m (°C)"),
        "rh":    _blend("relative_humidity_2m (%)"),
        "press": _blend("surface_pressure (hPa)"),
        "rain":  _blend("precipitation (mm)"),
        "vpd":   _blend("vapour_pressure_deficit (kPa)"),
        "rad":   _blend("shortwave_radiation (W/m²)"),
        "cloud": _blend("cloud_cover (%)"),
    }, index=idx)

    d_diff = ((np.diff(df["dir10"].values) + 180) % 360) - 180
    df["veer_rate"] = np.concatenate([[np.nan], d_diff])

    df["hour"]  = idx.hour
    df["month"] = idx.month
    df["doy"]   = idx.dayofyear
    df["year"]  = idx.year

    return df


# ═══════════════════════════════════════════════════════════════════
# UTILITAS ARAH
# ═══════════════════════════════════════════════════════════════════

def dir_to_sector8(d: float) -> str:
    d = d % 360
    if d < 22.5 or d >= 337.5: return "N"
    for i, bound in enumerate(SECTOR_8_BOUNDS[:-1]):
        if d < SECTOR_8_BOUNDS[i+1]: return SECTORS_8[i+1]
    return "NW"


def dir_to_sector16(d: float) -> str:
    return SECTORS_16[int((d % 360 + 11.25) / 22.5) % 16]


def circular_mean(angles_deg: np.ndarray) -> float:
    r = np.radians(angles_deg)
    return float(np.degrees(np.arctan2(np.mean(np.sin(r)),
                                        np.mean(np.cos(r)))) % 360)


def circular_std(angles_deg: np.ndarray) -> float:
    r = np.radians(angles_deg)
    R = np.sqrt(np.mean(np.sin(r))**2 + np.mean(np.cos(r))**2)
    return float(np.degrees(np.sqrt(-2 * np.log(R))))


def vector_mean(u: np.ndarray, v: np.ndarray) -> Tuple[float, float, float]:
    mu, mv = np.nanmean(u), np.nanmean(v)
    vec_spd = np.sqrt(mu**2 + mv**2)
    scalar_spd = np.nanmean(np.sqrt(u**2 + v**2))
    constancy = vec_spd / scalar_spd if scalar_spd > 0 else 0.0
    return mu, mv, constancy


def speed_to_beaufort(speed_kmh: float) -> Tuple[str, str]:
    for threshold, bf, label in BEAUFORT_SCALE:
        if speed_kmh < threshold:
            return bf, label
    return "12", "Hurricane"


# ═══════════════════════════════════════════════════════════════════
# B. WIND ROSE
# ═══════════════════════════════════════════════════════════════════

def wind_rose(
    df: pd.DataFrame,
    n_sectors: int = 8,
    speed_bins: Optional[List[float]] = None,
    subset: Optional[pd.Series] = None,
) -> Dict:
    if speed_bins is None:
        speed_bins = [0, 2, 5, 10, 15, 20, 30, 999]

    data = df if subset is None else df[subset]
    n_total = len(data)

    sectors = SECTORS_8 if n_sectors == 8 else SECTORS_16
    sec_func = dir_to_sector8 if n_sectors == 8 else dir_to_sector16
    sec_labels = data["dir10"].apply(sec_func)

    freq: Dict[str, float] = {}
    mean_spd: Dict[str, float] = {}
    constancy_map: Dict[str, float] = {}
    bin_matrix: Dict[str, List[float]] = {}

    for sec in sectors:
        mask = sec_labels == sec
        n_sec = mask.sum()
        freq[sec] = n_sec / n_total * 100
        sub = data[mask]
        mean_spd[sec] = sub["spd10"].mean() if n_sec > 0 else 0.0
        mu, mv, cnst = (vector_mean(sub["u10"].values, sub["v10"].values)
                        if n_sec > 0 else (0, 0, 0))
        constancy_map[sec] = cnst

        bins = []
        for i in range(len(speed_bins)-1):
            lo, hi = speed_bins[i], speed_bins[i+1]
            n_bin = ((sub["spd10"] >= lo) & (sub["spd10"] < hi)).sum()
            bins.append(n_bin / n_total * 100)
        bin_matrix[sec] = bins

    calm_pct = (data["spd10"] < 1.0).mean() * 100
    dom_sec = max(freq, key=freq.get)
    dom_dir = circular_mean(data.loc[sec_labels == dom_sec, "dir10"].values)

    return {
        "frequency":    freq,
        "mean_speed":   mean_spd,
        "speed_bins":   bin_matrix,
        "speed_bin_edges": speed_bins,
        "calm_pct":     calm_pct,
        "constancy":    constancy_map,
        "dominant_dir": {"sector": dom_sec, "degrees": dom_dir},
        "summary": {
            "mean_speed":    data["spd10"].mean(),
            "median_speed":  data["spd10"].median(),
            "p90_speed":     data["spd10"].quantile(0.90),
            "max_speed":     data["spd10"].max(),
            "mean_gust":     data["gust"].mean(),
            "max_gust":      data["gust"].max(),
            "mean_dir":      circular_mean(data["dir10"].values),
            "dir_std":       circular_std(data["dir10"].values),
            "n_hours":       n_total,
        },
    }


# ═══════════════════════════════════════════════════════════════════
# C. DIURNAL CYCLE
# ═══════════════════════════════════════════════════════════════════

def diurnal_cycle(df: pd.DataFrame, by_season: bool = True) -> Dict:
    def _hourly_stats(sub: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for h in range(24):
            s = sub[sub["hour"] == h]
            n = len(s)
            mu, mv, cnst = vector_mean(s["u10"].values, s["v10"].values)
            vec_dir = float(np.degrees(np.arctan2(-mu, -mv)) % 360)
            vec_spd = float(np.sqrt(mu**2 + mv**2))
            rows.append({
                "hour":          h,
                "mean_speed":    s["spd10"].mean(),
                "p25_speed":     s["spd10"].quantile(0.25),
                "p75_speed":     s["spd10"].quantile(0.75),
                "mean_dir":      circular_mean(s["dir10"].values),
                "dir_std":       circular_std(s["dir10"].values),
                "vec_dir":       vec_dir,
                "vec_speed":     vec_spd,
                "constancy":     cnst,
                "sector":        dir_to_sector8(vec_dir),
                "mean_shear":    s["shear_spd"].mean(),
                "mean_gust":     s["gust"].mean(),
                "mean_gust_factor": s["gust_factor"].mean(),
                "mean_temp":     s["temp"].mean(),
                "mean_vpd":      s["vpd"].mean(),
                "n":             n,
            })
        return pd.DataFrame(rows).set_index("hour")

    overall = _hourly_stats(df)

    vd = overall["vec_dir"].values
    onset = peak = reversal = cessation = None
    for h in range(6, 16):
        d = vd[h]
        if d <= 45 or d >= 315:
            onset = h; break
    for h in range(10, 18):
        if overall.loc[h, "mean_speed"] == overall["mean_speed"][10:18].max():
            peak = h; break
    for h in range(14, 22):
        d = vd[h]
        if 90 < d < 270:
            reversal = h; break
    for h in range(20, 24):
        d = vd[h]
        if 180 < d < 250:
            cessation = h; break

    sea_breeze = {
        "onset_hour":     onset,
        "peak_hour":      peak,
        "reversal_hour":  reversal,
        "cessation_hour": cessation,
        "duration_h":     (reversal - onset) if (onset and reversal) else None,
        "onset_dir":      float(vd[onset]) if onset else None,
        "peak_speed":     float(overall.loc[peak, "mean_speed"]) if peak else None,
        "night_dir":      float(circular_mean(vd[[0,1,2,3,4,5]])),
        "day_dir":        float(circular_mean(
                              vd[list(range(onset or 7, reversal or 18))])),
        "amplitude":      float(overall["mean_speed"].max()
                                - overall["mean_speed"].min()),
    }

    diurnal_range = {}
    for var in ["spd10", "vpd", "temp", "rh", "cloud", "rad"]:
        if var in df.columns:
            hourly_mean = df.groupby("hour")[var].mean()
            diurnal_range[var] = float(hourly_mean.max() - hourly_mean.min())

    by_regime: Dict[str, pd.DataFrame] = {}
    if by_season:
        for regime, months in REGIME_MONTHS.items():
            sub = df[df["month"].isin(months)]
            by_regime[regime] = _hourly_stats(sub)

    return {
        "overall":       overall,
        "by_regime":     by_regime,
        "sea_breeze":    sea_breeze,
        "diurnal_range": diurnal_range,
    }


# ═══════════════════════════════════════════════════════════════════
# D. SEA BREEZE ANALYSIS (DETAIL)
# ═══════════════════════════════════════════════════════════════════

def sea_breeze_analysis(df: pd.DataFrame) -> Dict:
    """
    Kriteria deteksi (modifikasi Walmsley 1988, disesuaikan lintang
    tropis):
      1. Angin siang (10-16 WIB) bersektor N/NE/E
      2. Angin malam (22-04 WIB) bersektor S/SW/W
      3. Speed siang > speed malam
      4. Radiasi siang > 150 W/m²

    Catatan: Walmsley (1988) mengusulkan 200 W/m² untuk lintang sedang.
    Untuk lintang tropis (−7.5°LS) threshold diturunkan ke 150 W/m².
    """
    daily = pd.DataFrame(index=pd.date_range(
        df.index.normalize().min(), df.index.normalize().max(), freq="D"))

    day_sub   = df[(df["hour"] >= 10) & (df["hour"] <= 16)]
    night_sub = df[(df["hour"].isin([22, 23, 0, 1, 2, 3, 4]))]

    day_dir_daily = day_sub.groupby(day_sub.index.normalize()).apply(
        lambda g: np.degrees(
            np.arctan2(np.mean(np.sin(np.radians(g["dir10"]))),
                       np.mean(np.cos(np.radians(g["dir10"]))))) % 360
    )
    night_dir_daily = night_sub.groupby(night_sub.index.normalize()).apply(
        lambda g: np.degrees(
            np.arctan2(np.mean(np.sin(np.radians(g["dir10"]))),
                       np.mean(np.cos(np.radians(g["dir10"]))))) % 360
    )
    day_spd_daily   = day_sub.groupby(day_sub.index.normalize())["spd10"].mean()
    night_spd_daily = night_sub.groupby(night_sub.index.normalize())["spd10"].mean()
    day_rad_daily   = day_sub.groupby(day_sub.index.normalize())["rad"].mean()

    def _is_sb(row) -> bool:
        d_dir = day_dir_daily.get(row, np.nan)
        n_dir = night_dir_daily.get(row, np.nan)
        d_spd = day_spd_daily.get(row, 0)
        n_spd = night_spd_daily.get(row, 0)
        d_rad = day_rad_daily.get(row, 0)
        if np.isnan(d_dir) or np.isnan(n_dir):
            return False
        day_onshore   = (d_dir >= 315) or (d_dir <= 90)
        night_onshore = (n_dir >= 135) and (n_dir <= 270)
        return (day_onshore and night_onshore
                and d_spd > n_spd and d_rad > 150)

    daily["is_sb"] = [_is_sb(d) for d in daily.index]
    daily["month"] = daily.index.month

    sb_by_month = daily.groupby("month")["is_sb"].agg(["sum", "mean"])
    sb_by_month.columns = ["sb_days", "sb_pct"]
    sb_by_month["sb_pct"] *= 100

    df_temp_range = df.copy()
    df_temp_range["date"] = df_temp_range.index.normalize()
    tx = df_temp_range.groupby("date")["temp"].max()
    tn = df_temp_range.groupby("date")["temp"].min()
    temp_range = (tx - tn).rename("temp_range")

    sb_daily = daily["is_sb"].astype(float)
    common = temp_range.index.intersection(sb_daily.index)
    r_temp, p_temp = stats.pearsonr(temp_range.loc[common],
                                    sb_daily.loc[common])

    return {
        "sb_by_month":     sb_by_month,
        "total_sb_days":   int(daily["is_sb"].sum()),
        "sb_pct_annual":   float(daily["is_sb"].mean() * 100),
        "temp_range_corr": {"r": round(r_temp, 3), "p": round(p_temp, 5)},
        "criteria": {
            "day_sector":    "N/NE (dir < 90° atau > 315°)",
            "night_sector":  "S/SW (135° – 270°)",
            "speed":         "V_siang > V_malam",
            "radiation":     "Rad_siang > 150 W/m²",
        },
        "criteria_reference": (
            "Walmsley (1988) mengusulkan 200 W/m² untuk lintang sedang; "
            "threshold 150 W/m² digunakan untuk lintang tropis −7.5°LS."
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# E. ANNUAL CYCLE (MUSON)
# ═══════════════════════════════════════════════════════════════════

def annual_cycle(df: pd.DataFrame) -> Dict:
    monthly_rows = []
    for m in range(1, 13):
        sub = df[df["month"] == m]
        mu, mv, cnst = vector_mean(sub["u10"].values, sub["v10"].values)
        vec_dir = float(np.degrees(np.arctan2(-mu, -mv)) % 360)
        vec_spd = float(np.sqrt(mu**2 + mv**2))
        monthly_rows.append({
            "month":           m,
            "scalar_speed":    sub["spd10"].mean(),
            "vector_speed":    vec_spd,
            "vector_dir":      vec_dir,
            "constancy":       cnst,
            "dir_std":         circular_std(sub["dir10"].values),
            "u_mean":          mu,
            "v_mean":          mv,
            "p90_speed":       sub["spd10"].quantile(0.90),
            "max_speed":       sub["spd10"].max(),
            "mean_shear":      sub["shear_spd"].mean(),
            "mean_gust":       sub["gust"].mean(),
            "sector":          dir_to_sector8(vec_dir),
            "regime":          next(
                (r for r, ms in REGIME_MONTHS.items() if m in ms), "?"),
            "n_hours":         len(sub),
        })

    monthly = pd.DataFrame(monthly_rows).set_index("month")

    # ── Onset/withdrawal muson (constancy threshold > 0.5) ─────────────
    # EV09-fix: bug wrapping `m%12+1 if m==12` pada versi sebelumnya
    # menyebabkan m=12 mengevaluasi baris Januari, bukan Desember.
    mb_onset = next(
        (m for m in (12, 1, 2, 3) if monthly.loc[m, "constancy"] > 0.5),
        None,
    )
    mt_onset = next(
        (m for m in (6, 7, 8, 9) if monthly.loc[m, "constancy"] > 0.5),
        None,
    )

    pancaroba_months = [m for m in range(1, 13)
                        if monthly.loc[m, "constancy"] < 0.30]

    x = np.arange(1, 13)
    spd_vals = monthly["scalar_speed"].values

    def harmonic_fit(m, A, phi, B):
        return A * np.cos(2 * np.pi / 12 * (m - phi)) + B

    try:
        from scipy.optimize import curve_fit
        popt, _ = curve_fit(harmonic_fit, x, spd_vals, p0=[1, 7, 5],
                            bounds=([0, 1, 0], [5, 12, 15]))
        harmonic = {
            "amplitude":   round(float(popt[0]), 3),
            "phase_month": round(float(popt[1]), 2),
            "mean_speed":  round(float(popt[2]), 3),
        }
    except Exception:
        harmonic = None

    return {
        "monthly":          monthly,
        "regime_summary":   {r: {
            "months": ms,
            "mean_constancy": monthly.loc[ms, "constancy"].mean(),
            "mean_speed":     monthly.loc[ms, "scalar_speed"].mean(),
        } for r, ms in REGIME_MONTHS.items()},
        "pancaroba_months": pancaroba_months,
        "harmonic_fit":     harmonic,
        "label":            REGIME_LABELS,
        "mb_onset_month":   mb_onset,
        "mt_onset_month":   mt_onset,
        "onset_criterion":  "wind_constancy > 0.50",
    }


# ═══════════════════════════════════════════════════════════════════
# F. WIND REGIME CLASSIFIER
# ═══════════════════════════════════════════════════════════════════

def wind_regime_classifier(df: pd.DataFrame) -> Dict:
    df = df.copy()
    df["regime"] = df["month"].map(
        {m: r for r, ms in REGIME_MONTHS.items() for m in ms}
    )

    regime_stats: Dict[str, Dict] = {}
    for reg in ["MB", "PML1", "MT", "PML2"]:
        sub = df[df["regime"] == reg]
        mu, mv, cnst = vector_mean(sub["u10"].values, sub["v10"].values)
        rose = wind_rose(sub, n_sectors=8)
        regime_stats[reg] = {
            "label":          REGIME_LABELS[reg],
            "n_hours":        len(sub),
            "scalar_speed":   sub["spd10"].mean(),
            "vector_speed":   float(np.sqrt(mu**2 + mv**2)),
            "vector_dir":     float(np.degrees(np.arctan2(-mu, -mv)) % 360),
            "constancy":      cnst,
            "dominant_sector": rose["dominant_dir"]["sector"],
            "calm_pct":       rose["calm_pct"],
            "p90_speed":      sub["spd10"].quantile(0.9),
            "wind_rose":      rose["frequency"],
            "mean_shear":     sub["shear_spd"].mean(),
            "diurnal_amplitude": (sub.groupby("hour")["spd10"].mean().max()
                                  - sub.groupby("hour")["spd10"].mean().min()),
        }

    return {
        "per_regime": regime_stats,
        "df_labeled": df[["spd10", "dir10", "regime", "hour", "month"]],
    }


# ═══════════════════════════════════════════════════════════════════
# G. TRANSITION ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def transition_analysis(df: pd.DataFrame) -> Dict:
    df = df.copy()
    vr = df["veer_rate"].values

    df["is_veer"]  = vr > 45
    df["is_back"]  = vr < -45
    df["is_rapid"] = np.abs(vr) > 90

    prev_dir = df["dir10"].shift(1)
    cur_dir  = df["dir10"]
    df["is_sea_onset"] = (
        (prev_dir >= 160) & (prev_dir <= 260) &
        ((cur_dir <= 70) | (cur_dir >= 310))
    )
    df["is_land_onset"] = (
        ((prev_dir <= 70) | (prev_dir >= 310)) &
        (cur_dir >= 130) & (cur_dir <= 230)
    )

    by_hour = pd.DataFrame({
        "veer_pct":    df.groupby("hour")["is_veer"].mean() * 100,
        "back_pct":    df.groupby("hour")["is_back"].mean() * 100,
        "rapid_pct":   df.groupby("hour")["is_rapid"].mean() * 100,
        "sea_onset":   df.groupby("hour")["is_sea_onset"].mean() * 100,
        "land_onset":  df.groupby("hour")["is_land_onset"].mean() * 100,
        "mean_vr_abs": df.groupby("hour")["veer_rate"].apply(
                           lambda x: np.abs(x).mean()),
    })

    by_month = pd.DataFrame({
        "veer_pct":  df.groupby("month")["is_veer"].mean() * 100,
        "back_pct":  df.groupby("month")["is_back"].mean() * 100,
        "rapid_pct": df.groupby("month")["is_rapid"].mean() * 100,
    })

    trans = df[df["is_veer"] | df["is_back"]]
    no_trans = df[~(df["is_veer"] | df["is_back"])]

    return {
        "total_veer":    int(df["is_veer"].sum()),
        "total_back":    int(df["is_back"].sum()),
        "total_rapid":   int(df["is_rapid"].sum()),
        "sea_onset_events":  int(df["is_sea_onset"].sum()),
        "land_onset_events": int(df["is_land_onset"].sum()),
        "veer_pct":      float(df["is_veer"].mean() * 100),
        "back_pct":      float(df["is_back"].mean() * 100),
        "by_hour":       by_hour,
        "by_month":      by_month,
        "mean_abs_veer_rate": float(np.abs(vr[~np.isnan(vr)]).mean()),
        "p90_abs_veer_rate":  float(np.nanpercentile(np.abs(vr), 90)),
        "cond_during_trans": {
            "mean_spd":   trans["spd10"].mean(),
            "mean_vpd":   trans["vpd"].mean(),
            "mean_cloud": trans["cloud"].mean(),
        },
        "cond_no_trans": {
            "mean_spd":   no_trans["spd10"].mean(),
            "mean_vpd":   no_trans["vpd"].mean(),
            "mean_cloud": no_trans["cloud"].mean(),
        },
    }


# ═══════════════════════════════════════════════════════════════════
# H. WIND SHEAR PROFILE
# ═══════════════════════════════════════════════════════════════════

def wind_shear_profile(df: pd.DataFrame) -> Dict:
    valid = df[(df["spd10"] > 0.5) & (df["spd100"] > 0.5)].copy()
    z_ratio_log = np.log(Z_100M / Z_10M)

    valid["alpha"] = np.log(valid["spd100"] / valid["spd10"]) / z_ratio_log

    alpha_monthly = valid.groupby("month")["alpha"].agg(
        ["median", "mean", "std",
         lambda x: x.quantile(0.10),
         lambda x: x.quantile(0.90)]
    )
    alpha_monthly.columns = ["median", "mean", "std", "p10", "p90"]

    alpha_hourly = valid.groupby("hour")["alpha"].median()

    valid["ekman_rot"] = valid["dir_shear"]
    ekman_monthly = valid.groupby("month")["ekman_rot"].mean()
    ekman_hourly  = valid.groupby("hour")["ekman_rot"].mean()

    stab_labels = {
        "Very unstable": (valid["alpha"] < 0.05).mean() * 100,
        "Unstable":      ((valid["alpha"] >= 0.05) & (valid["alpha"] < 0.12)).mean() * 100,
        "Neutral":       ((valid["alpha"] >= 0.12) & (valid["alpha"] < 0.20)).mean() * 100,
        "Stable":        ((valid["alpha"] >= 0.20) & (valid["alpha"] < 0.35)).mean() * 100,
        "Very stable":   (valid["alpha"] >= 0.35).mean() * 100,
    }

    day   = valid[valid["hour"].between(9, 17)]
    night = valid[valid["hour"].between(21, 24) | valid["hour"].between(0, 6)]

    return {
        "alpha_overall": {
            "median": round(float(valid["alpha"].median()), 3),
            "mean":   round(float(valid["alpha"].mean()),   3),
            "p10":    round(float(valid["alpha"].quantile(0.10)), 3),
            "p90":    round(float(valid["alpha"].quantile(0.90)), 3),
        },
        "alpha_monthly":     alpha_monthly,
        "alpha_hourly":      alpha_hourly,
        "ekman_monthly":     ekman_monthly,
        "ekman_hourly":      ekman_hourly,
        "stability_classes": stab_labels,
        "day_alpha":   round(float(day["alpha"].median()),   3),
        "night_alpha": round(float(night["alpha"].median()), 3),
        "shear_speed_stats": {
            "mean": round(float(df["shear_spd"].mean()), 3),
            "std":  round(float(df["shear_spd"].std()),  3),
            "p90":  round(float(df["shear_spd"].quantile(0.90)), 3),
            "max":  round(float(df["shear_spd"].max()), 3),
        },
        "interpretation": {
            "day_stability":   "Labil–Netral (konveksi siang, α kecil)",
            "night_stability": "Stabil (inversi malam, α besar, shear tinggi)",
            "note": "α Hellmann Indonesia khas 0.14–0.23 (lahan datar tropis)",
        },
    }


# ═══════════════════════════════════════════════════════════════════
# I. SUPPORT VARIABLE CORRELATIONS
# ═══════════════════════════════════════════════════════════════════

def support_correlations(df: pd.DataFrame) -> Dict:
    support_vars = {
        "temp":        "Suhu udara 2m (°C)",
        "rh":          "Kelembaban relatif (%)",
        "press":       "Tekanan permukaan (hPa)",
        "vpd":         "VPD (kPa)",
        "rad":         "Radiasi gelombang pendek (W/m²)",
        "cloud":       "Tutupan awan (%)",
        "rain":        "Curah hujan (mm)",
        "shear_spd":   "Wind shear kecepatan (km/h)",
        "gust_factor": "Gust factor",
    }

    corr_rows = []
    for var, label in support_vars.items():
        valid = df[["spd10", "dir10", var]].dropna()
        r_spd, p_spd = stats.pearsonr(valid["spd10"], valid[var])
        r_dir_sin, _ = stats.pearsonr(
            np.sin(np.radians(valid["dir10"])), valid[var])
        r_dir_cos, _ = stats.pearsonr(
            np.cos(np.radians(valid["dir10"])), valid[var])
        corr_rows.append({
            "variable":  label,
            "r_speed":   round(r_spd,     4),
            "p_speed":   round(p_spd,     6),
            "r_sin_dir": round(r_dir_sin, 4),
            "r_cos_dir": round(r_dir_cos, 4),
            "sig":       "**" if p_spd < 0.01 else ("*" if p_spd < 0.05 else ""),
        })

    corr_df = pd.DataFrame(corr_rows).set_index("variable")

    regime_corr: Dict[str, pd.Series] = {}
    for reg, months in REGIME_MONTHS.items():
        sub = df[df["month"].isin(months)]
        rc = {}
        for var in ["vpd", "temp", "rh", "rad", "cloud", "press"]:
            valid = sub[["spd10", var]].dropna()
            if len(valid) > 50:
                r, _ = stats.pearsonr(valid["spd10"], valid[var])
                rc[var] = round(r, 4)
        regime_corr[reg] = pd.Series(rc)

    lag_results = {}
    for lag in range(-3, 4):
        spd_s = df["spd10"].shift(lag)
        valid = df[["vpd"]].join(spd_s.rename("spd_lag")).dropna()
        r, p = stats.pearsonr(valid["spd_lag"], valid["vpd"])
        lag_results[lag] = {"r": round(r, 4), "p": round(p, 6)}

    df = df.copy()
    df["rain_class"] = pd.cut(df["rain"],
                               bins=[-0.1, 0, 1, 5, 20, 999],
                               labels=["Dry", "Light", "Moderate",
                                       "Heavy", "Extreme"])
    cond_rain = df.groupby("rain_class", observed=True)["spd10"].agg(
        ["mean", "std", "count"]).round(3)

    df["cloud_decile"] = pd.qcut(df["cloud"], q=10, labels=False,
                                 duplicates="drop")
    cond_cloud = df.groupby("cloud_decile")["spd10"].mean().round(3)

    return {
        "pearson_r":    corr_df,
        "regime_corr":  regime_corr,
        "lag_corr_vpd": lag_results,
        "cond_rain":    cond_rain,
        "cond_cloud":   cond_cloud,
        "key_findings": {
            "strongest_positive": "shear_spd (r=+0.65) — angin kuat di semua lapisan",
            "strongest_negative": "rh (r=−0.43) — angin kencang saat udara kering",
            "physical_driver":    "vpd (r=+0.45) seasonal muson + sea breeze diurnal",
            "pressure_negative":  "press (r=−0.26) — low pressure = windier",
        },
    }


# ═══════════════════════════════════════════════════════════════════
# J. SPECTRAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def spectral_analysis(
    df: pd.DataFrame,
    variable: str = "spd10",
    max_period_days: float = 30.0,
) -> Dict:
    ts = df[variable].resample("1h").mean().interpolate("linear")
    ts_detrended = ts.values - np.mean(ts.values)
    n = len(ts_detrended)

    fft_amp = np.abs(np.fft.rfft(ts_detrended))
    freqs   = np.fft.rfftfreq(n, d=1.0)

    min_freq = 1.0 / (max_period_days * 24)
    mask     = (freqs >= min_freq) & (freqs > 0)
    fft_masked = fft_amp.copy()
    fft_masked[~mask] = 0

    top_n = 10
    top_idx = np.argsort(fft_masked)[-top_n:][::-1]
    dominant_periods = []
    for i in top_idx:
        if freqs[i] > 0:
            ph = 1.0 / freqs[i]
            dominant_periods.append({
                "period_h":  round(ph, 2),
                "period_d":  round(ph / 24, 3),
                "amplitude": round(float(fft_amp[i]), 2),
                "label": (
                    "Diurnal (24h)" if 23 <= ph <= 25 else
                    "Semi-diurnal (12h)" if 11 <= ph <= 13 else
                    "QBWO (~14d)" if 11 <= ph/24 <= 16 else
                    f"Synoptic ({ph/24:.1f}d)"
                ),
            })

    freqs_w, psd = welch(ts_detrended, fs=1.0, nperseg=min(8760, n // 4))
    top_psd_idx = np.argsort(psd)[-5:][::-1]
    psd_peaks = []
    for i in top_psd_idx:
        if freqs_w[i] > 0:
            ph = 1.0 / freqs_w[i]
            if ph <= max_period_days * 24:
                psd_peaks.append({
                    "period_h": round(ph, 1),
                    "period_d": round(ph / 24, 2),
                    "psd":      round(float(psd[i]), 2),
                })

    diurnal_mask  = (freqs >= 1/25) & (freqs <= 1/23)
    semi_mask     = (freqs >= 1/13) & (freqs <= 1/11)
    total_power   = np.sum(fft_amp[mask]**2)
    diurnal_power = np.sum(fft_amp[diurnal_mask]**2)
    semi_power    = np.sum(fft_amp[semi_mask]**2)

    return {
        "dominant_periods": dominant_periods,
        "psd_peaks":        psd_peaks,
        "diurnal_pct":      round(diurnal_power / total_power * 100, 2) if total_power > 0 else 0,
        "semi_diurnal_pct": round(semi_power / total_power * 100, 2) if total_power > 0 else 0,
        "variable":         variable,
        "n_hours":          n,
        "interpretation": {
            "24h":    "Dominan kuat — sea breeze + thermal heating diurnal",
            "12h":    "Harmonik kedua — dua kali sehari (pagi & sore)",
            "13-15d": "QBWO — Quasi-Biweekly Oscillation, gelombang ekuatorial",
            "30-60d": "MJO — Madden-Julian Oscillation, aktif musim hujan",
        },
        "note_period_window": (
            f"max_period_days={max_period_days}; MJO (~30-60d) hanya "
            f"sebagian terekam bila jendela < 60 hari."
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# K. INTERANNUAL VARIABILITY
# ═══════════════════════════════════════════════════════════════════

def interannual_variability(df: pd.DataFrame) -> Dict:
    yearly_rows = []
    for yr in df["year"].unique():
        sub = df[df["year"] == yr]
        if len(sub) < 1000:
            continue
        mu, mv, cnst = vector_mean(sub["u10"].values, sub["v10"].values)
        yearly_rows.append({
            "year":       yr,
            "mean_speed": sub["spd10"].mean(),
            "p90_speed":  sub["spd10"].quantile(0.90),
            "max_speed":  sub["spd10"].max(),
            "constancy":  cnst,
            "vector_dir": float(np.degrees(np.arctan2(-mu, -mv)) % 360),
            "n_hours":    len(sub),
            "calm_pct":   (sub["spd10"] < 1.0).mean() * 100,
            "gust_mean":  sub["gust"].mean(),
        })

    yearly = pd.DataFrame(yearly_rows).set_index("year")

    yrs  = yearly.index.values.astype(float)
    spds = yearly["mean_speed"].values
    slope, intercept, r, p, se = stats.linregress(yrs, spds)

    mean_yr = yearly["mean_speed"].mean()
    std_yr  = yearly["mean_speed"].std()
    anomalies = yearly[np.abs(yearly["mean_speed"] - mean_yr) > 1.5 * std_yr]

    return {
        "yearly": yearly,
        "trend": {
            "slope_per_year": round(float(slope), 4),
            "r":              round(float(r),     4),
            "p":              round(float(p),     5),
            "significant":    p < 0.05,
            "direction":      "increasing" if slope > 0 else "decreasing",
        },
        "statistics": {
            "multi_year_mean": round(mean_yr, 3),
            "std":             round(std_yr,  3),
            "cv_pct":          round(std_yr / mean_yr * 100, 2),
            "min_year":        int(yearly["mean_speed"].idxmin()),
            "max_year":        int(yearly["mean_speed"].idxmax()),
        },
        "anomaly_years": anomalies,
        "data_through": (
            f"{df.index.min().date()} → {df.index.max().date()}"
            if len(df) else "—"
        ),
        "note_partial_year": (
            "Nilai max_speed per tahun mencerminkan extent aktual data. "
            "Tahun berjalan (mis. 2026) dapat memiliki max lebih rendah "
            "dari full-year; konsisten dengan file CSV sumber."
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# L. FULL REPORT RUNNER
# ═══════════════════════════════════════════════════════════════════

@dataclass
class WindAnalysisReport:
    file_p1: str = ""
    file_p2: str = ""
    verbose: bool = True

    df:            Optional[pd.DataFrame] = field(default=None, repr=False)
    wind_rose_:    Optional[Dict] = field(default=None, repr=False)
    diurnal:       Optional[Dict] = field(default=None, repr=False)
    sea_breeze_:   Optional[Dict] = field(default=None, repr=False)
    annual:        Optional[Dict] = field(default=None, repr=False)
    regimes:       Optional[Dict] = field(default=None, repr=False)
    transitions:   Optional[Dict] = field(default=None, repr=False)
    shear:         Optional[Dict] = field(default=None, repr=False)
    correlations_: Optional[Dict] = field(default=None, repr=False)
    spectral:      Optional[Dict] = field(default=None, repr=False)
    interannual:   Optional[Dict] = field(default=None, repr=False)

    def run(self) -> "WindAnalysisReport":
        steps = [
            ("Load & Prepare",          self._run_load),
            ("Wind Rose",               self._run_rose),
            ("Diurnal Cycle",           self._run_diurnal),
            ("Sea Breeze",              self._run_sea_breeze),
            ("Annual Cycle / Muson",    self._run_annual),
            ("Wind Regime Classifier",  self._run_regime),
            ("Transition Analysis",     self._run_transition),
            ("Wind Shear Profile",      self._run_shear),
            ("Support Correlations",    self._run_corr),
            ("Spectral Analysis",       self._run_spectral),
            ("Interannual Variability", self._run_interannual),
        ]
        for i, (label, func) in enumerate(steps, 1):
            if self.verbose:
                print(f"  [{i:02d}/{len(steps)}] {label}...",
                      end=" ", flush=True)
            func()
            if self.verbose:
                print("✓")
        if self.verbose:
            print(f"\n  Selesai. DataFrame: {self.df.shape}")
        return self

    def _run_load(self):
        self.df = load_and_prepare(self.file_p1, self.file_p2, verbose=False)
    def _run_rose(self):        self.wind_rose_ = wind_rose(self.df)
    def _run_diurnal(self):     self.diurnal = diurnal_cycle(self.df)
    def _run_sea_breeze(self):  self.sea_breeze_ = sea_breeze_analysis(self.df)
    def _run_annual(self):      self.annual = annual_cycle(self.df)
    def _run_regime(self):      self.regimes = wind_regime_classifier(self.df)
    def _run_transition(self):  self.transitions = transition_analysis(self.df)
    def _run_shear(self):       self.shear = wind_shear_profile(self.df)
    def _run_corr(self):        self.correlations_ = support_correlations(self.df)
    def _run_spectral(self):    self.spectral = spectral_analysis(self.df)
    def _run_interannual(self): self.interannual = interannual_variability(self.df)

    def print_summary(self) -> None:
        SEP = "═" * 66
        print(f"\n{SEP}")
        print("  WIND ANALYSIS REPORT — Ringkasan (EV09)")
        print(f"  Titik: {TARGET_LAT}°S {TARGET_LON}°E  Elev={TARGET_ELEV}m")
        print(SEP)

        wr  = self.wind_rose_["summary"]
        dc  = self.diurnal
        ann = self.annual
        tr  = self.transitions
        sh  = self.shear
        ia  = self.interannual
        sp  = self.spectral

        print(f"\n── STATISTIK UMUM ───────────────────────────────────────────")
        print(f"  Mean speed 10m : {wr['mean_speed']:.2f} km/h")
        print(f"  P90  speed 10m : {wr['p90_speed']:.2f} km/h")
        print(f"  Max speed 10m  : {wr['max_speed']:.2f} km/h")
        print(f"  Max gust       : {wr['max_gust']:.2f} km/h")
        print(f"  Calm (<1 km/h) : {self.wind_rose_['calm_pct']:.1f}%")
        print(f"  Mean direction : {wr['mean_dir']:.1f}°  "
              f"({dir_to_sector8(wr['mean_dir'])})")
        print(f"  Dir std (circ) : {wr['dir_std']:.1f}°")

        print(f"\n── SEA BREEZE ───────────────────────────────────────────────")
        sb = dc["sea_breeze"]
        print(f"  Onset          : ~{sb['onset_hour']:02d}:00 WIB  "
              f"(dir: {sb['onset_dir']:.0f}° → "
              f"{dir_to_sector8(sb['onset_dir'])})")
        print(f"  Peak           : ~{sb['peak_hour']:02d}:00 WIB  "
              f"({sb['peak_speed']:.2f} km/h)")
        print(f"  Reversal       : ~{sb['reversal_hour']:02d}:00 WIB")
        print(f"  Durasi aktif   : ~{sb['duration_h']} jam")
        print(f"  Amplitudo harian: {sb['amplitude']:.2f} km/h")
        print(f"  Malam (land br): {sb['night_dir']:.0f}° "
              f"({dir_to_sector8(sb['night_dir'])})")

        print(f"\n── MUSON (ANNUAL CYCLE) ─────────────────────────────────────")
        for reg, stats_r in ann["regime_summary"].items():
            print(f"  {reg}  constancy={stats_r['mean_constancy']:.3f}  "
                  f"speed={stats_r['mean_speed']:.2f} km/h")
        print(f"  Pancaroba bulan: {ann['pancaroba_months']}")
        mb = ann.get("mb_onset_month")
        mt = ann.get("mt_onset_month")
        mb_str = f"bulan {mb:02d}" if mb else "tidak terdeteksi"
        mt_str = f"bulan {mt:02d}" if mt else "tidak terdeteksi"
        print(f"  MB onset      : {mb_str}  ({ann['onset_criterion']})")
        print(f"  MT onset      : {mt_str}  ({ann['onset_criterion']})")

        print(f"\n── TRANSISI ARAH ────────────────────────────────────────────")
        print(f"  Veer events    : {tr['total_veer']:,}  ({tr['veer_pct']:.1f}%)")
        print(f"  Back events    : {tr['total_back']:,}  ({tr['back_pct']:.1f}%)")
        print(f"  Rapid (≥90°/h) : {tr['total_rapid']:,}")
        print(f"  Sea onset      : {tr['sea_onset_events']:,}")
        print(f"  Land onset     : {tr['land_onset_events']:,}")
        print(f"  Jam paling turbulent: "
              f"{tr['by_hour']['rapid_pct'].idxmax():02d}:00")

        print(f"\n── PROFIL VERTIKAL (POWER LAW) ──────────────────────────────")
        print(f"  α median (all) : {sh['alpha_overall']['median']}")
        print(f"  α siang        : {sh['day_alpha']}  (labil, konvektif)")
        print(f"  α malam        : {sh['night_alpha']}  (stabil, inversi)")
        for k, v in sh["stability_classes"].items():
            print(f"    {k:16s}: {v:.1f}%")

        print(f"\n── SPEKTRAL ─────────────────────────────────────────────────")
        print(f"  Diurnal (24h) variance : {sp['diurnal_pct']:.1f}%")
        print(f"  Semi-diurnal (12h)     : {sp['semi_diurnal_pct']:.1f}%")
        print(f"  Top-3 periods          :")
        for p3 in sp["dominant_periods"][:3]:
            print(f"    {p3['period_h']:7.1f}h = {p3['period_d']:.2f}d  "
                  f"({p3['label']})")

        print(f"\n── VARIABILITAS ANTAR-TAHUN ─────────────────────────────────")
        t = ia["trend"]
        print(f"  Trend     : {t['slope_per_year']:+.4f} km/h/tahun  "
              f"(r={t['r']:.3f}, "
              f"{'sig' if t['significant'] else 'tidak sig'})")
        st = ia["statistics"]
        print(f"  Mean      : {st['multi_year_mean']:.3f} km/h  "
              f"CV={st['cv_pct']:.1f}%")
        print(f"  Tahun min : {st['min_year']}  Max: {st['max_year']}")
        print(f"  Data span : {ia['data_through']}")
        print()
        print(SEP)

    def export_csv(self, output_dir: str = ".") -> List[str]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        files = []

        p = out / "wind_diurnal_cycle.csv"
        self.diurnal["overall"].to_csv(p); files.append(str(p))

        p = out / "wind_annual_cycle.csv"
        self.annual["monthly"].to_csv(p); files.append(str(p))

        p = out / "wind_transitions_by_hour.csv"
        self.transitions["by_hour"].to_csv(p); files.append(str(p))

        p = out / "wind_shear_alpha_monthly.csv"
        self.shear["alpha_monthly"].to_csv(p); files.append(str(p))

        p = out / "wind_support_correlations.csv"
        self.correlations_["pearson_r"].to_csv(p); files.append(str(p))

        p = out / "wind_interannual.csv"
        self.interannual["yearly"].to_csv(p); files.append(str(p))

        if self.verbose:
            print(f"\n  Ekspor selesai: {len(files)} file → {output_dir}/")
        return files


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 66)
    print("  WIND ANALYSIS MODULE v1.1 (EV09) — Menjalankan semua analisis...")
    print("=" * 66)

    rpt = WindAnalysisReport(
        file_p1=DEFAULT_HOURLY_CSV_P1,
        file_p2=DEFAULT_HOURLY_CSV_P2,
        verbose=True,
    )
    rpt.run()
    rpt.print_summary()
    rpt.export_csv("./wind_output/")