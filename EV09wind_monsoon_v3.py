#!/usr/bin/env python3
"""
EV09wind_monsoon.py
================================================================================
DETEKSI REVERSAL MONSUD BARAT DI TITIK OBSERVASI MJS
Detektor Multi-Precursor dengan Ensemble Median Terboboti
================================================================================

1 · LATAR BELAKANG FISIK
--------------------------------------------------------------------------------
Kepulauan Indonesia terletak di zona pertemuan dua sistem sirkulasi
atmosfer skala benua:

    East Monsoon (Monsun Timur, Musim Kemarau)
        Periode : Juni – Oktober
        Asal    : massa udara dari Australia
        Sifat   : kering, komponen zonal u_comp < 0
        Angin dari sektor timur (wd ≈ 90–140°)

    West Monsoon (Monsun Barat, Musim Hujan)
        Periode : Desember – April
        Asal    : massa udara dari benua Asia melalui Samudra Hindia
        Sifat   : lembab, komponen zonal u_comp > 0
        Angin dari sektor barat (wd ≈ 240–290°)

REVERSAL MONSUD BARAT adalah peristiwa transisi ketika angin lapisan
batas berbalik dari sektor timur ke sektor barat. Peristiwa ini menandai
awal musim hujan di wilayah Jawa, khususnya Jawa Timur.

Konvensi komponen zonal (unit vektor):

    u_comp = −sin(wd10 · π/180)

    dengan wd10 = arah angin DARI mana ia bertiup (konvensi meteorologi).
    Angin dari barat (wd ≈ 270°) → u_comp ≈ +1
    Angin dari timur (wd ≈ 90°)  → u_comp ≈ −1

Siklus Pranata Mangsa memakai anchor 22 Juni sebagai awal siklus tahunan.
Variabel dopy (day-of-pranata-year) didefinisikan modular:
    dopy = 0    → 22 Juni (anchor)
    dopy ≈ 130  → 30 Oktober (reversal tipikal)
    dopy = 365  → wrap-around ke 22 Juni tahun berikutnya


2 · TANTANGAN ILMIAH
--------------------------------------------------------------------------------
Deteksi reversal secara objektif menghadapi empat tantangan:

    T1. Tidak ada satu variabel tunggal yang cukup. Angin permukaan
        dipengaruhi oleh breeze laut-darat, topografi, dan konveksi lokal.

    T2. ENSO memodulasi waktu reversal hingga ±20 hari. Tahun El Niño
        (2015, 2019, 2023) → reversal mundur. Tahun La Niña (2022) →
        reversal maju.

    T3. Precursor vs respons. Sebagian variabel termodinamika (dew point,
        VPD slope) merespon SEBELUM angin berbalik karena intrusi uap
        air mendahului perubahan gradien tekanan. Variabel lain
        (kelembaban tanah, tutupan awan) merespon SESUDAH.

    T4. Threshold kaku (u = 0) gagal pada tahun dengan onset lemah.
        Diperlukan pendekatan statistik adaptif (CUSUM) atau threshold
        berbasis baseline (persentil musim kering).


3 · ARSITEKTUR DELAPAN DETEKTOR
--------------------------------------------------------------------------------
Delapan detektor independen dikelompokkan berdasarkan sifat fisik:

  [A] DINAMIK — perubahan sirkulasi angin
      M4_Shear   : δu = u_100m − u_10m, crossing 0
      M7_BaseU   : u_comp langsung, 30-hari rolling, crossing 0

  [B] TERMODINAMIK PRECURSOR — surge uap air sebelum angin berbalik
      M2b_dVPD   : slope 5-hari VPD, threshold adaptif mean − 1.5σ
      M3_Tdew    : dew point 30-hari rolling, threshold mean + 1.5σ

  [C] TERMODINAMIK RESPONS — konfirmasi setelah angin berbalik
      M2_VPD     : level VPD turun < 65% median musim kering

  [D] HIDROLOGI — konfirmasi melalui akumulasi curah hujan
      M6_SoilMoist : kelembaban tanah 7–28 cm > P80 musim kering

  [E] STATISTIK — deteksi tanpa threshold manual
      M1_MPCI    : komposit Z-score 7 variabel, crossing 0
      M5_CUSUM   : CUSUM Page (1954) dengan pre-whitening AR(1)


4 · PROSEDUR CUSUM YANG RIGOR
--------------------------------------------------------------------------------
CUSUM klasik (Page 1954) mengasumsikan residual ε_t bersifat i.i.d.
N(0, σ²). Data u_comp harian MELANGGAR asumsi ini karena:

    • Siklus musiman monsun → mean bergeser sistematis sepanjang tahun
    • Autokorelasi lag-1 tinggi (φ ≈ 0.7)

Jika asumsi dilanggar, CUSUM menghasilkan alarm acak. Prosedur yang benar
adalah PRE-WHITENING (Montgomery, SPC Handbook, 7th ed., §10.3):

    Langkah 1. Fit model AR(1) pada residual r_t = u_t − ū
               r_t = φ · r_{t−1} + ε_t
               Estimasi φ̂ dengan OLS.

    Langkah 2. Whiten series:
               ε_t = r_t − φ̂ · r_{t−1}
               Residual ε_t sekarang ≈ i.i.d.

    Langkah 3. Estimasi μ₀ dan σ_ε dari window East Monsoon murni
               (dopy ≤ 100).

    Langkah 4. CUSUM satu sisi (mendeteksi kenaikan mean):
               S_t = max(0, S_{t−1} + (ε_t − μ₀) − k)

               dengan parameter TEORI (bukan tuning):
                 k = 0.5 σ_ε    (Page reference value, minimax-optimal)
                 h = 5.0 σ_ε    (Montgomery decision threshold, ARL₀ ≈ 465)

    Langkah 5. Change-point = indeks terakhir S kembali ke 0 sebelum
               alarm S > h tercapai.

Tidak ada constraint manual, tidak ada relaksasi. Semua parameter
berasal dari literatur SPC standar. Hasil `None` berarti tidak ada
bukti statistik perubahan rezim pada level 5σ — jawaban yang valid.


5 · PENGGABUNGAN ENSEMBLE
--------------------------------------------------------------------------------
Setiap detektor menghasilkan satu estimasi dopy. Ensemble menggunakan
MEDIAN TERBOBOTI:

    dopy_ensemble = weighted_median({dopy_i}, {w_i})

Median dipilih (bukan mean) karena robust terhadap outlier — jika satu
detektor memberikan estimasi ekstrem, ensemble tetap stabil. Bobot
mencerminkan independensi dan keandalan tiap detektor, ditetapkan dari
matriks korelasi antar-metode (Section D output).


6 · REFERENSI
--------------------------------------------------------------------------------
[1] Page, E.S. (1954). Continuous Inspection Schemes. Biometrika 41:100–115.
[2] Montgomery, D.C. (2013). Introduction to Statistical Quality Control,
    7th ed. Wiley. §10.3 (CUSUM untuk data autocorrelated).
[3] Basseville, M. & Nikiforov, I.V. (1993). Detection of Abrupt Changes:
    Theory and Application. Prentice Hall.
[4] Wang, B. & Ding, Q. (2008). Global Monsoon: Major Modes and Climate
    Change. In: The Global Monsoon System. World Scientific.
[5] Qian, W. & Lee, D.-K. (2000). Seasonal March of the East-Asian Summer
    Monsoon. Adv. Atmos. Sci. 17:417–431.
[6] Pettitt, A.N. (1979). A Non-Parametric Approach to the Change-Point
    Problem. Appl. Statist. 28(2):126–135.

================================================================================
"""

from __future__ import annotations
import sys
from typing import List, Optional, Dict

import numpy as np
import pandas as pd

try:
    from EV09wind import (
        _require_data, _find_crossing, _rolling_daily_ucomp,
        load_hourly_full, attach_time_features,
        ANCHOR_MONTH, ANCHOR_DAY,
        MR_WINDOW, MR_SUSTAIN, MR_EPS,
        sec_header, print_header,
        _dopy_to_approx_date, _linear_trend,
        SCENARIO_LABUH_DOPY,
        IDW_W1_VOLATILE, IDW_W2_VOLATILE,
        DEFAULT_HOURLY_P1, DEFAULT_HOURLY_P2,
        find_data_file,
    )
    HAS_EV09 = True
except ImportError as e:
    print(f"[!] EV09wind.py tidak ditemukan: {e}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# KONSTANTA GLOBAL
# ══════════════════════════════════════════════════════════════════════════════

WIN        = 30        # jendela rolling 30-hari untuk smoothing
SEARCH_LO  = 60.0      # batas bawah window pencarian (dopy)
SEARCH_HI  = 200.0     # batas atas window pencarian (dopy)
SUSTAIN    = 15        # jumlah hari minimum sinyal harus bertahan
EPS_CROSS  = 0.005     # toleransi noise saat verifikasi sustain

# ── Bobot ensemble ──────────────────────────────────────────────────────────
#  Prinsip: detektor independen (r antar-metode rendah) diberi bobot tinggi.
#  Detektor dengan redundansi (r > 0.9) diturunkan agar tidak mendominasi.
ENSEMBLE_WEIGHTS: Dict[str, float] = {
    "M1_MPCI":      1.0,
    "M2_VPD":       1.0,
    "M2b_dVPD":     1.5,
    "M3_Tdew":      1.5,
    "M4_Shear":     1.0,
    "M5_CUSUM":     1.0,  
    "M6_SoilMoist": 1.0,
    "M7_BaseU":     2.0,
}


# ══════════════════════════════════════════════════════════════════════════════
# PEMUATAN DATA
# ══════════════════════════════════════════════════════════════════════════════
_FULL_RICH_CACHE: Optional[pd.DataFrame] = None


def _read_raw_csv(path: str) -> pd.DataFrame:
    """Baca CSV Open-Meteo dengan auto-skip header metadata."""
    with open(path, "r", encoding="utf-8") as fh:
        skip = 0
        for i, line in enumerate(fh):
            if line.lstrip().startswith("time,"):
                skip = i
                break
    df = pd.read_csv(path, skiprows=skip)
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").reset_index(drop=True)


def _idw_scalar(v1: pd.Series, v2: pd.Series) -> pd.Series:
    """IDW merge dua seri skalar dengan bobot volatile EV09."""
    idx   = v1.index.union(v2.index)
    both  = v1.notna() & v2.notna()
    only1 = v1.notna() & v2.isna()
    only2 = v2.notna() & v1.isna()
    out   = pd.Series(np.nan, index=idx)
    out.loc[both]  = IDW_W1_VOLATILE * v1[both]  + IDW_W2_VOLATILE * v2[both]
    out.loc[only1] = v1[only1]
    out.loc[only2] = v2[only2]
    return out


def load_rich_hourly() -> Optional[pd.DataFrame]:
    """
    Muat semua kolom dari CSV P1+P2, IDW-merge, dan tambahkan kolom
    turunan EV09 (hour, month, dopy, u_comp, v_comp).

    Skalar di-merge dengan IDW arithmetic (bobot volatile EV09).
    Arah angin di-merge via unit-vector IDW (circular-safe).
    Hasil di-cache untuk mencegah pembacaan berulang.
    """
    global _FULL_RICH_CACHE
    if _FULL_RICH_CACHE is not None:
        return _FULL_RICH_CACHE

    p1_path = find_data_file(DEFAULT_HOURLY_P1)
    p2_path = find_data_file(DEFAULT_HOURLY_P2)
    if p1_path is None and p2_path is None:
        print("  [!] File CSV P1/P2 tidak ditemukan.")
        return None

    RENAME = {
        "vapour_pressure_deficit (kPa)":                "vpd",
        "dew_point_2m (°C)":                            "dew_pt",
        "total_column_integrated_water_vapour (kg/m²)": "tcwv",
        "relative_humidity_2m (%)":                     "rh",
        "surface_pressure (hPa)":                       "pressure",
        "soil_moisture_7_to_28cm (m³/m³)":              "soil_moist",
        "precipitation (mm)":                           "precip",
        "cloud_cover (%)":                              "cloud",
        "cloud_cover_low (%)":                          "cloud_lo",
        "cloud_cover_mid (%)":                          "cloud_mid",
        "cloud_cover_high (%)":                         "cloud_hi",
        "wind_speed_10m (km/h)":                        "ws10",
        "wind_direction_10m (°)":                       "wd10",
        "wind_gusts_10m (km/h)":                        "gust10",
        "wind_speed_100m (km/h)":                       "ws100",
        "wind_direction_100m (°)":                      "wd100",
    }

    def _read(path):
        return _read_raw_csv(path).rename(columns=RENAME)

    if p1_path is None:
        df = _read(p2_path)
    elif p2_path is None:
        df = _read(p1_path)
    else:
        d1  = _read(p1_path).set_index("time")
        d2  = _read(p2_path).set_index("time")
        idx = d1.index.union(d2.index)
        out = pd.DataFrame(index=idx)

        SCALARS = ["vpd", "dew_pt", "tcwv", "rh", "pressure", "soil_moist",
                   "precip", "cloud", "cloud_lo", "cloud_mid", "cloud_hi",
                   "ws10", "gust10", "ws100"]
        for col in SCALARS:
            c1 = d1[col].reindex(idx) if col in d1.columns else pd.Series(np.nan, index=idx)
            c2 = d2[col].reindex(idx) if col in d2.columns else pd.Series(np.nan, index=idx)
            out[col] = _idw_scalar(c1, c2)

        for src in ("wd10", "wd100"):
            r1 = np.deg2rad(d1[src].reindex(idx).values) if src in d1.columns else np.full(len(idx), np.nan)
            r2 = np.deg2rad(d2[src].reindex(idx).values) if src in d2.columns else np.full(len(idx), np.nan)
            s_ = IDW_W1_VOLATILE * np.sin(r1) + IDW_W2_VOLATILE * np.sin(r2)
            c_ = IDW_W1_VOLATILE * np.cos(r1) + IDW_W2_VOLATILE * np.cos(r2)
            n1, n2 = ~np.isfinite(r1), ~np.isfinite(r2)
            s_[n1 & ~n2] = np.sin(r2[n1 & ~n2]); c_[n1 & ~n2] = np.cos(r2[n1 & ~n2])
            s_[~n1 & n2] = np.sin(r1[~n1 & n2]); c_[~n1 & n2] = np.cos(r1[~n1 & n2])
            out[src] = (np.rad2deg(np.arctan2(s_, c_)) + 360.0) % 360.0

        df = out.reset_index().rename(columns={"index": "time"})

    df = df.sort_values("time").reset_index(drop=True)
    df = attach_time_features(df)

    print(f"  [i] {len(df):,} baris hourly (rich)  "
          f"· {df['time'].min().date()} → {df['time'].max().date()}")
    avail = [c for c in ["vpd", "dew_pt", "tcwv", "rh", "soil_moist"]
             if c in df.columns]
    print(f"      Precursor tersedia: {', '.join(avail)}")
    _FULL_RICH_CACHE = df
    return df


# ══════════════════════════════════════════════════════════════════════════════
# UTILITAS
# ══════════════════════════════════════════════════════════════════════════════

def _attach_dopy(d: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Tambah kolom dopy ke DataFrame harian. Anchor = 22 Juni."""
    t  = pd.to_datetime(d[date_col])
    a  = pd.to_datetime(dict(year=t.dt.year,     month=ANCHOR_MONTH, day=ANCHOR_DAY))
    ap = pd.to_datetime(dict(year=t.dt.year - 1, month=ANCHOR_MONTH, day=ANCHOR_DAY))
    d  = d.copy()
    d["dopy"] = np.where(t < a,
                         (t - ap).dt.total_seconds() / 86400.0,
                         (t - a ).dt.total_seconds() / 86400.0) % 365.0
    return d


def _daily_roll(df: pd.DataFrame, field: str,
                agg: str = "mean", win: int = WIN) -> pd.DataFrame:
    """
    Agregasi harian + rolling mean dengan jendela simetris.
    Center=True karena analisis bersifat retrospektif.
    """
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    s = d.groupby("_date").agg(v=(field, agg)).reset_index()
    s = s.rename(columns={"_date": "date"}).sort_values("date")
    s["roll"] = s["v"].rolling(win, center=True, min_periods=win // 2).mean()
    return _attach_dopy(s)


def _find_cross(sig: np.ndarray, dopys: np.ndarray,
                thr: float, up: bool = True,
                sustain: int = SUSTAIN,
                lo: float = SEARCH_LO, hi: float = SEARCH_HI,
                eps: float = EPS_CROSS) -> Optional[float]:
    """
    Threshold crossing dengan verifikasi sustain.

    Kriteria valid:
      (1) Crossing terjadi dalam window [lo, hi]
      (2) Setelah crossing, sinyal bertahan di sisi yang benar selama
          minimal `sustain` sampel
      (3) Toleransi noise `eps` diizinkan di sekitar threshold
    """
    for i in range(1, len(sig)):
        d = dopys[i]
        if not (lo <= d <= hi):
            continue
        prev, curr = sig[i - 1], sig[i]
        if not (np.isfinite(prev) and np.isfinite(curr)):
            continue
        crossed = (up and prev < thr <= curr) or (not up and prev > thr >= curr)
        if not crossed:
            continue
        fut = sig[i: i + sustain]
        if np.isfinite(fut).sum() < sustain - 5:
            continue
        ok = (np.nanmin(fut) >= thr - eps) if up else (np.nanmax(fut) <= thr + eps)
        if ok:
            return float(d)
    return None


def _year_slice(df: pd.DataFrame, py: int) -> pd.DataFrame:
    """Ekstrak subset dalam satu siklus pranata-tahun (22 Jun → 21 Jun)."""
    s = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
    return df[(df["time"] >= s) & (df["time"] < s + pd.Timedelta(days=366))].copy()


# ══════════════════════════════════════════════════════════════════════════════
# M1 · MULTI-PRECURSOR COMPOSITE INDEX (MPCI)
# ══════════════════════════════════════════════════════════════════════════════

def detect_mpci(df: pd.DataFrame) -> Optional[float]:
    """
    Indeks komposit Z-score dari tujuh variabel multi-skala.

    RASIONAL
    --------
    Transisi monsun melibatkan perubahan simultan pada banyak variabel
    atmosfer. Kombinasi Z-score mengurangi noise lokal karena efek
    rata-rata antar-variabel yang independen.

    FORMULASI
    ---------
    MPCI(t) = (1/N) · Σ_i s_i · (x_i(t) − μ_i) / σ_i

    dengan s_i = ±1 sesuai arah fisik masing-masing variabel:
        (+) u_comp, RH, dew_pt, tcwv, cloud, precip
        (−) vpd (defisit tekanan uap; turun saat lembab)

    Crossing MPCI_rolling dari bawah ke atas pada 0 menandakan
    transisi rezim kering → basah.

    CATATAN
    -------
    MPCI berkorelasi tinggi dengan M2_VPD (r ≈ 0.99) karena VPD
    merupakan komponen dominan. Bobot ensemble MPCI diturunkan
    untuk mencegah double-counting.
    """
    comps = [(f, s) for f, s in [
        ("u_comp", +1), ("rh", +1), ("dew_pt", +1),
        ("tcwv", +1), ("cloud", +1), ("precip", +1), ("vpd", -1),
    ] if f in df.columns and df[f].notna().sum() > 100]

    if len(comps) < 3:
        return None

    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    daily = (d.groupby("_date")
               .agg(**{f: (f, "mean") for f, _ in comps})
               .reset_index())
    daily = daily.rename(columns={"_date": "date"}).sort_values("date")
    daily = _attach_dopy(daily)

    daily["mpci"] = 0.0
    n = 0
    for f, sgn in comps:
        v = daily[f].ffill()
        mu, sd = v.mean(), v.std()
        if sd < 1e-9:
            continue
        daily["mpci"] += sgn * (v - mu) / sd
        n += 1
    if n == 0:
        return None
    daily["mpci"] /= n
    daily["mpci_roll"] = (daily["mpci"]
                          .rolling(WIN, center=True, min_periods=WIN // 2)
                          .mean())
    return _find_cross(daily["mpci_roll"].values, daily["dopy"].values,
                       thr=0.0, up=True)


# ══════════════════════════════════════════════════════════════════════════════
# M2 · VPD LEVEL DROP
# ══════════════════════════════════════════════════════════════════════════════

def detect_vpd_drop(df: pd.DataFrame) -> Optional[float]:
    """
    Deteksi penurunan level VPD di bawah 65% median musim kering.

    RASIONAL
    --------
    Vapour Pressure Deficit (VPD) mengukur "kekeringan udara":
        VPD = e_s(T) − e_a
    dengan e_s = tekanan uap jenuh (fungsi suhu) dan e_a = tekanan uap
    aktual. VPD tinggi selama East Monsoon (udara kering), rendah
    selama West Monsoon (udara lembab).

    THRESHOLD ADAPTIF
    -----------------
    Threshold = 65% × median VPD musim kering (dopy 60–150). Faktor 0.65
    dipilih sebagai kompromi antara sensitivitas (mendeteksi penurunan
    awal) dan spesifisitas (menghindari crossing palsu karena noise
    harian).

    KARAKTER
    --------
    Detektor ini termasuk RESPONS — VPD turun setelah angin berbalik
    membawa uap air (lead time negatif ~−18 hari dari ensemble).
    """
    if "vpd" not in df.columns or df["vpd"].notna().sum() < 100:
        return None
    s   = _daily_roll(df, "vpd", "mean", WIN)
    dry = s[(s["dopy"] >= 60) & (s["dopy"] <= 150)]["roll"].dropna()
    if len(dry) < 15:
        return None
    thr = float(np.median(dry) * 0.65)
    return _find_cross(s["roll"].values, s["dopy"].values, thr=thr, up=False)


# ══════════════════════════════════════════════════════════════════════════════
# M2b · dVPD/dt — KECEPATAN PENURUNAN VPD (PRECURSOR)
# ══════════════════════════════════════════════════════════════════════════════

def detect_dvpd(df: pd.DataFrame) -> Optional[float]:
    """
    Deteksi laju penurunan VPD (slope 5-hari) sebagai precursor.

    RASIONAL
    --------
    Level VPD dan laju perubahan VPD membawa informasi berbeda:

        Level VPD     : STATE saat ini (kering vs lembab)
        dVPD/dt       : TRANSISI yang sedang berlangsung

    Sebelum reversal angin, uap air mulai masuk lebih dulu, menurunkan
    VPD secara bertahap. Slope 5-hari VPD menjadi negatif signifikan
    BEBERAPA HARI SEBELUM crossing level. Karena itu dVPD/dt berperan
    sebagai PRECURSOR — peringatan dini 2–4 minggu sebelum reversal.

    METODE
    ------
    1. Hitung daily mean VPD
    2. Hitung slope 5-hari rolling (linear least-squares)
    3. Smoothing 7-hari untuk mengurangi noise
    4. Threshold adaptif: mean − 1.5σ dari slope musim kering (60–110)
    5. Deteksi saat slope turun di bawah threshold, sustained ≥ 5 hari

    Parameter sustain=5 (bukan 15) karena slope lebih noisy; eps=0.015
    memberi toleransi recovery kecil saat transisi.
    """
    if "vpd" not in df.columns or df["vpd"].notna().sum() < 100:
        return None

    s   = _daily_roll(df, "vpd", "mean", 1)
    vpd = s["v"].values
    dpy = s["dopy"].values
    n   = len(vpd)

    SLOPE_WIN = 5
    slopes = np.full(n, np.nan)
    xs = np.arange(SLOPE_WIN, dtype=float)
    for i in range(SLOPE_WIN - 1, n):
        blk = vpd[i - SLOPE_WIN + 1: i + 1]
        ok  = np.isfinite(blk)
        if ok.sum() >= 3:
            slopes[i] = np.polyfit(xs[ok], blk[ok], 1)[0]

    slope_roll = (pd.Series(slopes)
                    .rolling(7, center=True, min_periods=3)
                    .mean().values)

    base_mask = (dpy >= 60) & (dpy <= 110) & np.isfinite(slope_roll)
    if base_mask.sum() < 10:
        return None
    mu_base = float(np.nanmean(slope_roll[base_mask]))
    sd_base = float(np.nanstd(slope_roll[base_mask])) + 1e-9
    thr     = mu_base - 1.5 * sd_base

    return _find_cross(slope_roll, dpy, thr=thr, up=False,
                       sustain=5, eps=0.015)


# ══════════════════════════════════════════════════════════════════════════════
# M3 · DEW POINT MOISTURE SURGE (PRECURSOR)
# ══════════════════════════════════════════════════════════════════════════════

def detect_dewpoint_jump(df: pd.DataFrame) -> Optional[float]:
    """
    Deteksi lonjakan dew point (Td) di atas baseline musim kering.

    RASIONAL
    --------
    Dew point adalah suhu di mana udara menjadi jenuh terhadap uap air.
    Td berkorelasi langsung dengan kandungan uap air absolut melalui
    persamaan Clausius-Clapeyron, sehingga menjadi proxy langsung untuk
    intrusi massa udara lembab dari Samudra Hindia.

    Saat West Monsoon mendekat, Td naik 2–5°C di atas baseline musim
    kering SEBELUM angin permukaan berbalik — karena adveksi uap air
    di lapisan rendah didahului oleh perubahan gradien tekanan.

    THRESHOLD ADAPTIF
    -----------------
    Threshold = mean + 1.5σ dari distribusi Td musim kering dopy 60–120.
    Pendekatan percentile kaku (P90/P97) selalu memotong fenologi
    tahunan yang konstan dan tidak responsif terhadap variabilitas
    antar-tahun. Threshold mean + 1.5σ menghasilkan std antar-tahun
    ~7 hari — cukup untuk membedakan tahun El Niño vs La Niña.
    """
    if "dew_pt" not in df.columns or df["dew_pt"].notna().sum() < 100:
        return None

    s   = _daily_roll(df, "dew_pt", "mean", WIN)
    dry = s[(s["dopy"] >= 60) & (s["dopy"] <= 120)]["roll"].dropna()
    if len(dry) < 15:
        return None

    mu = float(np.mean(dry))
    sd = float(np.std(dry))
    if sd < 1e-6:
        return None
    thr = mu + 1.5 * sd

    return _find_cross(s["roll"].values, s["dopy"].values,
                       thr=thr, up=True, sustain=10, eps=0.01)


# ══════════════════════════════════════════════════════════════════════════════
# M4 · VERTICAL WIND SHEAR VEERING
# ══════════════════════════════════════════════════════════════════════════════

def detect_shear_veering(df: pd.DataFrame) -> Optional[float]:
    """
    Deteksi perubahan shear vertikal 10m↔100m.

    RASIONAL
    --------
    Angin permukaan (10m) dipengaruhi gesekan topografi dan termal lokal
    (breeze laut-darat), sementara angin 100m lebih mencerminkan sirkulasi
    sinoptik monsun. Perbedaan komponen zonal:

        δu = u_100m − u_10m

    menunjukkan VEERING vertikal — rotasi arah angin dengan ketinggian.

    Selama East Monsoon  : δu < 0 (100m lebih ke timur dari 10m)
    Selama West Monsoon  : δu > 0 (100m lebih ke barat dari 10m)

    Crossing δu = 0 menandai perubahan rezim sirkulasi vertikal.
    Sinyal sering mendahului perubahan angin permukaan absolut karena
    lapisan atas merespon gradien tekanan besar lebih dulu.
    """
    for col in ("ws10", "ws100", "wd10", "wd100"):
        if col not in df.columns or df[col].notna().sum() < 100:
            return None

    d = df.copy()
    d["du_shear"] = (
        -d["ws100"].values * np.sin(np.deg2rad(d["wd100"].values))
        - (-d["ws10"].values * np.sin(np.deg2rad(d["wd10"].values)))
    )
    s = _daily_roll(d, "du_shear", "mean", WIN)
    return _find_cross(s["roll"].values, s["dopy"].values,
                       thr=0.0, up=True)


# ══════════════════════════════════════════════════════════════════════════════
# M5 · CUSUM CHANGE-POINT (PAGE 1954, PRE-WHITENED)
# ══════════════════════════════════════════════════════════════════════════════

def detect_cusum(df: pd.DataFrame) -> Optional[float]:
    """
    CUSUM Page (1954) dengan pre-whitening AR(1).

    LATAR TEORI
    -----------
    CUSUM klasik mendeteksi pergeseran mean dari μ₀ ke μ₁ > μ₀ dengan
    statistik akumulatif:

        S_t = max(0, S_{t−1} + (x_t − μ₀) − k)

    Parameter teoritis (Page 1954, Montgomery 2013):
        k = 0.5 σ     reference value (minimax-optimal untuk δ = 1σ)
        h = 5.0 σ     decision threshold (ARL₀ ≈ 465 sampel)
    Alarm saat S_t > h. Change-point = indeks terakhir S_t = 0
    sebelum alarm.

    ASUMSI I.I.D. & PRE-WHITENING
    -----------------------------
    CUSUM mengasumsikan residual ε_t bersifat i.i.d. N(0, σ²).
    Data u_comp harian MELANGGAR asumsi ini (autokorelasi lag-1 ≈ 0.7).
    Prosedur yang benar (Montgomery, SPC Handbook §10.3):

        1. r_t = u_t − ū
        2. Fit AR(1): r_t = φ r_{t−1} + ε_t, φ̂ dari OLS
        3. Whiten: ε_t = r_t − φ̂ r_{t−1}
        4. Estimasi μ₀, σ_ε dari window East Monsoon (dopy ≤ 100)
        5. CUSUM pada ε_t dengan k = 0.5 σ_ε, h = 5.0 σ_ε

    TIDAK ADA constraint manual atau relaksasi. Parameter semua dari
    teori SPC standar.

    INTERPRETASI `None`
    -------------------
    Jika CUSUM tidak mencapai alarm h = 5σ, berarti tidak ada bukti
    statistik perubahan rezim pada level signifikansi tersebut.
    Ini adalah jawaban yang valid secara ilmiah, bukan kegagalan
    deteksi. Tahun dengan East Monsoon sangat lemah (El Niño/La Niña
    ekstrem) memang dapat tidak menunjukkan change-point tajam.
    """
    if "u_comp" not in df.columns:
        return None

    # Agregasi harian + window pencarian
    s = _daily_roll(df, "u_comp", "mean", 1)
    s = s[(s["dopy"] >= SEARCH_LO) & (s["dopy"] <= SEARCH_HI)].reset_index(drop=True)
    if len(s) < 90:
        return None

    u   = s["v"].values.astype(float)
    dpy = s["dopy"].values

    ok = np.isfinite(u)
    if ok.sum() < 80:
        return None
    u = np.where(ok, u, np.interp(np.arange(len(u)), np.where(ok)[0], u[ok]))

    # ── Langkah 1: residual terhadap mean global ──────────────────────
    r = u - u.mean()

    # ── Langkah 2: fit AR(1) ──────────────────────────────────────────
    r_lag = r[:-1]
    r_cur = r[1:]
    denom = float(np.sum(r_lag ** 2)) + 1e-9
    phi   = float(np.sum(r_lag * r_cur) / denom)
    phi   = max(-0.95, min(0.95, phi))

    # ── Langkah 3: whitening ──────────────────────────────────────────
    eps   = r[1:] - phi * r[:-1]
    dpy_e = dpy[1:]

    # ── Langkah 4: estimasi μ₀, σ_ε dari East Monsoon murni ──────────
    base_mask = dpy_e <= 100
    if base_mask.sum() < 15:
        return None
    mu0   = float(eps[base_mask].mean())
    sigma = float(eps[base_mask].std(ddof=1))
    if sigma < 1e-6:
        return None

    # ── Langkah 5: CUSUM satu sisi, parameter teori ───────────────────
    k = 0.5 * sigma          # Page reference value
    h = 5.0 * sigma          # Montgomery decision threshold

    S         = 0.0
    last_zero = 0
    alarm_idx = None
    for i, e in enumerate(eps):
        S = max(0.0, S + (e - mu0) - k)
        if S < 1e-9:
            last_zero = i
        if S > h:
            alarm_idx = i
            break

    if alarm_idx is None:
        return None

    cp = float(dpy_e[last_zero])
    return cp if SEARCH_LO <= cp <= SEARCH_HI else None


# ══════════════════════════════════════════════════════════════════════════════
# M6 · SOIL MOISTURE ONSET
# ══════════════════════════════════════════════════════════════════════════════

def detect_soil_moisture(df: pd.DataFrame) -> Optional[float]:
    """
    Deteksi onset kelembaban tanah lapisan 7–28 cm.

    RASIONAL
    --------
    Kelembaban tanah merupakan reservoir hidrologi yang terintegrasi
    dari curah hujan sebelumnya. Setelah beberapa hari hujan awal,
    kelembaban tanah lapisan dalam naik signifikan dan bertahan lama —
    berbeda dari kelembaban permukaan yang fluktuatif.

    Sinyal ini tertinggal beberapa hari dari hujan pertama (waktu
    infiltrasi), tetapi memberikan konfirmasi independen terhadap
    onset monsun dari sistem hidrologi, bukan atmosfer.

    Threshold: P80 dari distribusi soil moisture musim kering (dopy 60–140).
    """
    if "soil_moist" not in df.columns or df["soil_moist"].notna().sum() < 100:
        return None
    s   = _daily_roll(df, "soil_moist", "mean", WIN)
    dry = s[(s["dopy"] >= 60) & (s["dopy"] <= 140)]["roll"].dropna()
    if len(dry) < 15:
        return None
    thr = float(np.percentile(dry, 80))
    return _find_cross(s["roll"].values, s["dopy"].values, thr=thr, up=True)


# ══════════════════════════════════════════════════════════════════════════════
# M7 · BASELINE u_comp (METODE EV09wind ORIGINAL)
# ══════════════════════════════════════════════════════════════════════════════

def detect_base_u(df: pd.DataFrame) -> Optional[float]:
    """
    u_comp 30-hari rolling crossing 0 — metode original EV09wind.

    Digunakan sebagai referensi historis dan pembanding ensemble.
    Keterbatasan: averaging 30-hari menyebabkan keterlambatan
    deteksi ~15–20 hari setelah onset fisik.
    """
    daily = _rolling_daily_ucomp(df)
    return _find_crossing(daily["u30"].values, daily["dopy"].values)


# ══════════════════════════════════════════════════════════════════════════════
# ENSEMBLE MEDIAN TERBOBOTI
# ══════════════════════════════════════════════════════════════════════════════

def ensemble_vote(results: Dict[str, Optional[float]]) -> Optional[float]:
    """
    Gabungkan 8 detektor menjadi satu estimasi robust.

    ALGORITMA
    ---------
    1. Kumpulkan semua deteksi valid (bukan None) dalam window pencarian.
    2. Untuk setiap detektor m dengan bobot w, ulangi nilai dopy
       sebanyak round(w · 10) kali dalam daftar virtual.
    3. Ambil median dari daftar virtual.

    RASIONAL MEDIAN
    ---------------
    Median robust terhadap outlier — berbeda dengan mean. Jika satu
    detektor memberikan estimasi ekstrem, median tidak terpengaruh.
    """
    vals, ws = [], []
    for m, v in results.items():
        if v is not None and SEARCH_LO <= v <= SEARCH_HI:
            vals.append(v)
            ws.append(ENSEMBLE_WEIGHTS.get(m, 1.0))
    if not vals:
        return None
    rep: List[float] = []
    for v, w in zip(vals, ws):
        rep.extend([v] * max(1, int(round(w * 10))))
    return float(np.median(rep))


def run_all_detectors(df: pd.DataFrame, py: int) -> Dict[str, Optional[float]]:
    """Jalankan kedelapan detektor untuk satu siklus pranata-tahun."""
    sub = _year_slice(df, py)
    if len(sub) < 5000:
        return {}
    return {
        "M1_MPCI":      detect_mpci(sub),
        "M2_VPD":       detect_vpd_drop(sub),
        "M2b_dVPD":     detect_dvpd(sub),
        "M3_Tdew":      detect_dewpoint_jump(sub),
        "M4_Shear":     detect_shear_veering(sub),
        "M5_CUSUM":     detect_cusum(sub),
        "M6_SoilMoist": detect_soil_moisture(sub),
        "M7_BaseU":     detect_base_u(sub),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PELAPORAN
# ══════════════════════════════════════════════════════════════════════════════

METHOD_SHORT = {
    "M1_MPCI":      "MPCI",
    "M2_VPD":       "VPD↓",
    "M2b_dVPD":     "dVPD",
    "M3_Tdew":      "Td↑",
    "M4_Shear":     "Shear",
    "M5_CUSUM":     "CUSUM",
    "M6_SoilMoist": "SoilM",
    "M7_BaseU":     "BaseU",
}
METHODS = list(METHOD_SHORT.keys())

KETERANGAN = {
    "M1_MPCI":      "Komposit Z-score 7 variabel",
    "M2_VPD":       "VPD < 65% median musim kering",
    "M2b_dVPD":     "VPD slope < mean−1.5σ musim kering",
    "M3_Tdew":      "Dew point > mean+1.5σ musim kering",
    "M4_Shear":     "δu (100m−10m) crossing 0",
    "M5_CUSUM":     "CUSUM Page + pre-whitening AR(1)",
    "M6_SoilMoist": "Soil moisture > P80 musim kering",
    "M7_BaseU":     "u_comp 30d rolling crossing 0 (baseline)",
    "ENSEM":        "Median terboboti semua detektor valid",
}

SHORT_DESC = {
    "M3_Tdew":      "Moisture surge (precursor, lead ~+14 hr)",
    "M2b_dVPD":     "VPD slope turun (precursor, lead ~+26 hr)",
    "M6_SoilMoist": "Akumulasi hujan awal (konfirmasi hidrologi)",
    "M2_VPD":       "VPD collapse (respons, lag ~−18 hr)",
    "M1_MPCI":      "Perubahan rezim multi-variabel",
    "M5_CUSUM":     "Change-point statistik (konfirmasi)",
    "M4_Shear":     "Shear veering vertikal",
    "M7_BaseU":     "Reversal angin aktual (baseline)",
}

PRECURSOR_ORDER = ["M3_Tdew", "M2b_dVPD", "M6_SoilMoist", "M2_VPD",
                   "M1_MPCI", "M5_CUSUM", "M4_Shear", "M7_BaseU"]


def report_advanced_monsoon() -> None:
    print_header(
        "DETEKSI REVERSAL MONSUD BARAT — MULTI-PRECURSOR",
        "8 detektor  ·  CUSUM Page 1954 + pre-whitening AR(1)"
    )

    df = load_rich_hourly()
    if df is None:
        return

    all_res: Dict[int, Dict[str, Optional[float]]] = {}
    ens_vals: List[float] = []

    # ── A · Tabel per tahun ─────────────────────────────────────────────
    sec_header("A · HASIL DETEKSI PER PRANATA-TAHUN")
    print("  Setiap nilai = dopy (0=22 Jun, 130≈30 Okt, 200≈08 Jan).")
    print("  Tanda — menunjukkan detektor tidak mendeteksi change-point")
    print("  pada level signifikansi yang dipersyaratkan.")
    print()

    col_w = 6
    hdr = f"  {'Thn':<5}" + "".join(
        f"{METHOD_SHORT[m]:>{col_w}}" for m in METHODS
    )
    hdr += f"  {'ENSEM':>7}  Tanggal (Ensemble)"
    print(hdr[:100]); print("  " + "─" * 96)

    for py in range(2015, 2027):
        res = run_all_detectors(df, py)
        if not res:
            continue
        ens = ensemble_vote(res)
        all_res[py] = res
        if ens is not None:
            ens_vals.append(ens)

        row = f"  {py:<5}"
        for m in METHODS:
            v = res.get(m)
            row += f"{'—':>{col_w}}" if v is None else f"{v:>{col_w}.0f}"
        if ens is not None:
            row += f"  {ens:>7.1f}  {_dopy_to_approx_date(py, ens)}"
        else:
            row += f"  {'n/a':>7}  —"
        print(row[:100])

    # ── B · Statistik ringkasan ──────────────────────────────────────────
    sec_header("B · STATISTIK RINGKASAN PER DETEKTOR")
    print("  Std kecil = detektor stabil antar-tahun.")
    print("  Std besar = detektor sensitif terhadap ENSO.")
    print()
    print(f"  {'Metode':<10}{'N':>3}{'Mean':>7}{'Median':>8}{'Std':>6}"
          f"{'Min':>6}{'Max':>6}  Catatan")
    print("  " + "─" * 90)

    for m in METHODS + ["ENSEM"]:
        short = METHOD_SHORT.get(m, m) if m != "ENSEM" else "ENSEM"
        if m == "ENSEM":
            vals = ens_vals
        else:
            vals = [v for yr in all_res
                    for mm, v in all_res[yr].items()
                    if mm == m and v is not None]
        if len(vals) < 2:
            print(f"  {short:<10}{'<2':>3}  {KETERANGAN.get(m, '')}")
            continue
        arr = np.array(vals)
        print(f"  {short:<10}{len(arr):>3}"
              f"{arr.mean():>7.1f}{np.median(arr):>8.1f}"
              f"{arr.std(ddof=1):>6.1f}{arr.min():>6.1f}{arr.max():>6.1f}"
              f"  {KETERANGAN.get(m, '')}")

    # ── C · Lead time ────────────────────────────────────────────────────
    sec_header("C · LEAD TIME — PRECURSOR vs RESPONS")
    print("  Lead positif = detektor mendahului ensemble (PRECURSOR).")
    print("  Lead negatif = detektor tertinggal dari ensemble (RESPONS).")
    print()

    ens_mean = float(np.mean(ens_vals)) if ens_vals else np.nan
    if np.isfinite(ens_mean):
        print(f"  Ensemble mean = dopy {ens_mean:.1f}")
        print(f"  Ensemble median = dopy {np.median(ens_vals):.1f}\n")

    print(f"  {'Metode':<8}{'Lead (hr)':>11}  {'Klasifikasi':<11} Keterangan")
    print("  " + "─" * 76)
    for m in PRECURSOR_ORDER:
        vals = [v for yr in all_res for mm, v in all_res[yr].items()
                if mm == m and v is not None]
        if not vals or not np.isfinite(ens_mean):
            continue
        m_med = float(np.median(vals))
        lead  = ens_mean - m_med
        kls   = ("PRECURSOR" if lead > 2
                 else "≈sama" if abs(lead) <= 2
                 else "respons")
        print(f"  {METHOD_SHORT[m]:<8}{lead:>+11.1f}  {kls:<11} "
              f"{SHORT_DESC.get(m, '')}")
    print()
    print("  Detektor PRECURSOR berguna untuk peringatan dini.")
    print("  Detektor RESPONS berguna untuk konfirmasi akhir.")

    # ── D · Korelasi ─────────────────────────────────────────────────────
    sec_header("D · KORELASI ANTAR DETEKTOR")
    print("  r > 0.7 = saling melengkapi (konsisten).")
    print("  r < 0   = berlawanan arah (perlu investigasi).")
    print("  r > 0.9 = redundan (bobot ensemble diturunkan).")
    print()

    yr_list = sorted(all_res.keys())
    mser: Dict[str, np.ndarray] = {
        m: np.array([all_res[yr].get(m) if yr in all_res else np.nan
                     for yr in yr_list], dtype=float)
        for m in METHODS
    }
    active = [m for m in METHODS if np.isfinite(mser[m]).sum() >= 3]

    if len(active) >= 2:
        head = f"  {'':10}" + "".join(f"{METHOD_SHORT[m]:>7}" for m in active)
        print(head[:82]); print("  " + "─" * min(len(head) - 2, 80))
        for mi in active:
            row = f"  {METHOD_SHORT[mi]:<10}"
            for mj in active:
                if mi == mj:
                    row += f"  {'1.00':>5}"
                    continue
                ai, aj = mser[mi], mser[mj]
                mask = np.isfinite(ai) & np.isfinite(aj)
                if mask.sum() >= 3:
                    r = float(np.corrcoef(ai[mask], aj[mask])[0, 1])
                    row += f"  {r:>5.2f}"
                else:
                    row += f"  {'—':>5}"
            print(row[:82])

    # ── E · Perbandingan vs BaseU ─────────────────────────────────────
    sec_header("E · PERBANDINGAN ENSEMBLE vs BASELINE BaseU")
    print("  BaseU = metode original EV09wind (u_comp 30d crossing 0).")
    print("  Δ negatif = ensemble mengoreksi keterlambatan BaseU.")
    print()
    print(f"  {'Thn':<6}{'BaseU':>10}{'ENSEM':>10}{'Δ (hari)':>10}  Komentar")
    print("  " + "─" * 62)
    for yr in yr_list:
        bu  = all_res[yr].get("M7_BaseU")
        ens = ensemble_vote(all_res[yr])
        if bu is None or ens is None:
            continue
        delta = ens - bu
        note  = ("ensemble lebih lambat" if delta > 5
                 else "ensemble lebih cepat" if delta < -5
                 else "konsisten")
        print(f"  {yr:<6}{bu:>10.1f}{ens:>10.1f}{delta:>+10.1f}  {note}")

    # ── F · Tren ──────────────────────────────────────────────────────
    sec_header("F · TREN JANGKA PANJANG — ENSEMBLE")
    if len(ens_vals) >= 3:
        yrs = np.array(yr_list, dtype=float)
        ev  = np.array([ensemble_vote(all_res.get(yr, {})) or np.nan
                        for yr in yr_list])
        vld = np.isfinite(ev)
        if vld.sum() >= 3:
            sl, _, r, t = _linear_trend(yrs[vld], ev[vld])
            n_v = int(vld.sum())
            print(f"  Slope     : {sl:+.2f} hari/tahun")
            print(f"  Pearson r : {r:+.3f}")
            print(f"  t-stat    : {t:+.2f}  (df = {n_v - 2})")
            print()
            if abs(t) < 2.26:
                print("  Verdict: Tidak ada tren signifikan.")
                print("           Boundary monsun stasioner dalam periode ini.")
            else:
                direction = "mundur" if sl > 0 else "maju"
                print(f"  Verdict: TREN signifikan — reversal {direction} "
                      f"{abs(sl):.2f} hari/tahun.")

    # ── G · Skenario Labuh ────────────────────────────────────────────
    sec_header("G · POSISI ENSEMBLE vs SKENARIO LABUH")
    print("  Skenario Labuh = definisi alternatif awal musim Labuh.")
    print("  Δ negatif = Labuh mulai sebelum reversal fisik.")
    print("  Δ positif = Labuh mulai setelah reversal fisik.")
    print()

    ens_ref = float(np.median(ens_vals)) if ens_vals else np.nan
    if np.isfinite(ens_ref):
        print(f"  Ensemble median : dopy {ens_ref:.1f}  "
              f"({_dopy_to_approx_date(2025, ens_ref)})\n")
        print(f"  {'Skenario':<10}{'dopy Labuh':>11}{'Δ (hr)':>10}  Keterangan")
        print("  " + "─" * 60)
        for sc, val in SCENARIO_LABUH_DOPY.items():
            d = val - ens_ref
            print(f"  {sc:<10}{val:>11.1f}{d:>+10.1f}  "
                  f"{'Labuh lebih awal' if d < 0 else 'Labuh setelah reversal'}")


def main() -> int:
    report_advanced_monsoon()
    return 0


if __name__ == "__main__":
    sys.exit(main())