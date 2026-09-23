#!/usr/bin/env python3
"""
EV09wind_monsoon_reversal.py — Versi 5.4
==========================================
Deteksi monsoon reversal dengan 11 estimator independen, ensemble
berbobot, validasi silang, dan anotasi anomali ENSO×IOD (baru v5.4).

PERUBAHAN v5.4
──────────────
  § baru  Identifikasi anomali ENSO×IOD pada tabel deteksi
    · Loader mandiri: SST ASO, MSLA ASO, DMI SON, IOD fase
    · Anotasi COUNTER/SINERGI/NETRAL per pranata-tahun
    · Flag anomali aktif bila: interaksi COUNTER kuat
      (|SST|≥0.75, |DMI|≥0.75, simetris) DAN reversal menyimpang
      >1.5σ dari median
    · Section J baru di akhir laporan: tabel penuh + interpretasi
  § Threshold anomali simetris: 0.75 untuk SST dan DMI
  § Narasi J2 tidak lagi hardcode contoh historis
  § Section F: diagnosa khusus Netral murni + koreksi besar →
    sinyal internal (MJO/cold-surge) dominan
  § Konsol width = 72 kolom; textwrap untuk semua narasi panjang
  § _rule() 70 kolom → aman dari auto-wrap terminal
  § _wrap_block() mempertahankan hanging indent sumber

STRUKTUR METODE
───────────────
  Tier 1 — Change-point & filter berkaliber internasional
    M1   PELT               Killick, Fearnhead & Eckley (2012)
    M2   Shiryaev-Roberts   Pollak (1985)
    M11  Lanczos + recovery + gerbang MJO
        · Duchon (1979) Lanczos low-pass, zero phase-shift
        · Wheeler & Hendon (2004) RMM sebagai gate MJO

  Tier 2 — Statistik hidroklimatologi standar
    M3   Pettitt non-parametrik   Pettitt (1979)
    M4   Slope VPD 7-hari
    M5   CUSUM                    Page (1954)

  Tier 3 — Precursor fisik & baseline
    M6   VPD level rendah
    M7   Titik embun tinggi
    M8   Shear vertikal 10m↔100m
    M9   Soil moisture
    M10  u_comp 30-hari rolling (baseline EV09wind)

DETAIL M11 (v5.3)
─────────────────
  Sinyal     : u_lanczos = konvolusi simetris u_comp harian dengan
               kernel Lanczos windowed-sinc (window 241 hari,
               cutoff 80 hari). Zero phase-shift — tidak menggeser
               tanggal.
  Ambang     : threshold = u_min + 0.20 × (u_max − u_min), dengan
               u_min = minimum u di musim kering (dopy 60–120),
               u_max = maksimum u di musim basah (dopy 180–280).
               Fallback: threshold = 0.02 jika amplitudo < 0.15.
  Crossing   : Persilangan naik threshold di dalam jendela dopy
               [60, 200].
  Gerbang MJO: Kandidat ditolak jika MJO aktif (RMM amp ≥ 2.0)
               pada hari persilangan.

  Karakteristik filter Lanczos pada konfigurasi ini:
    Monsun tahunan (T=365 hr)  |H| = 1.00  → lolos
    MJO            (T= 45 hr)  |H| = 0.003 → diredam
    Gelombang Kelvin (T=15 hr) |H| < 0.001 → diredam
    Cold surge     (T= 5 hr)   |H| = 0.000 → diredam

REFERENSI
─────────
  Duchon, C. E. (1979). Lanczos filtering in one and two dimensions.
    J. Appl. Meteor. 18(8):1016–1022.
  Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal detection
    of changepoints with a linear computational cost.
    JASA 107(500):1590–1598.
  Page, E. S. (1954). Continuous inspection schemes.
    Biometrika 41:100–115.
  Pettitt, A. N. (1979). A non-parametric approach to the change-point
    problem. JRSS-C 28(2):126–135.
  Pollak, M. (1985). Optimal detection of a change in distribution.
    Ann. Stat. 13(1):206–227.
  Wheeler, M. C., & Hendon, H. H. (2004). An all-season real-time
    multivariate MJO index. Mon. Wea. Rev. 132(8):1917–1932.
"""

from __future__ import annotations

import math
import sys
import textwrap
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import signal as spsig
from scipy import stats as spstats

try:
    from EV09wind import (
        _find_crossing, _rolling_daily_ucomp,
        attach_time_features,
        ANCHOR_MONTH, ANCHOR_DAY,
        sec_header, print_header,
        _dopy_to_approx_date, _linear_trend,
        SCENARIO_LABUH_DOPY,
        IDW_W1_VOLATILE, IDW_W2_VOLATILE,
        DEFAULT_HOURLY_P1, DEFAULT_HOURLY_P2,
        find_data_file,
    )
except ImportError as e:
    print(f"[!] EV09wind.py tidak ditemukan: {e}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════
# Section 1 · Konstanta
# ══════════════════════════════════════════════════════════════════════════

# ── Lebar konsol (spesifikasi tampilan) ──────────────────────────────────
CONSOLE_WIDTH = 72

# ── Jendela deteksi (semua metode) ───────────────────────────────────────
SEARCH_LO = 60.0            # awal jendela pencarian (dopy)
SEARCH_HI = 200.0           # akhir jendela pencarian (dopy)
DRY_LO    = 60.0            # baseline musim kering
DRY_HI    = 120.0           # puncak musim kering
ROLL_WIN  = 30              # jendela rolling default
SUSTAIN   = 10              # uji sustain default
EPS       = 0.005           # toleransi sustain

# ── M11 · Lanczos zero-phase ─────────────────────────────────────────────
LANCZOS_WINDOW      = 241   # ganjil; ≥ 3× cutoff
LANCZOS_CUTOFF_DAYS = 80.0  # cutoff frekuensi (periode ≥ 80 hr lolos)
U_RECOVERY_FRACTION = 0.20  # ambang = u_min + 0.20 × (u_max − u_min)

# ── M11 · Gerbang MJO (Wheeler–Hendon) ───────────────────────────────────
DEFAULT_RMM_FILE    = "rmm8.csv"
RMM_AMP_THRESHOLD   = 2.0   # ambang amplitudo RMM untuk "MJO aktif"
MJO_WINDOW_FRACTION = 1.0   # fraksi jendela; 1.0 = gerbang jendela nonaktif

# ── Ensemble berbobot ────────────────────────────────────────────────────
ENSEMBLE_WEIGHTS: Dict[str, float] = {
    "M1_PELT":     3.0,
    "M2_SR":       2.5,
    "M3_Pett":     2.5,
    "M4_dVPD":     2.0,
    "M5_CUSUM":    2.0,
    "M6_VPD":      1.5,
    "M7_Td":       1.5,
    "M8_Shear":    1.0,
    "M9_Soil":     1.0,
    "M10_BaseU":   1.5,
    "M11_Lanczos": 3.0,
}


# ══════════════════════════════════════════════════════════════════════════
# Section 2 · Loader data meteorologi
# ══════════════════════════════════════════════════════════════════════════

_METEO_CACHE: Optional[pd.DataFrame] = None

_RENAME = {
    "vapour_pressure_deficit (kPa)":                "vpd",
    "dew_point_2m (°C)":                            "dew_pt",
    "total_column_integrated_water_vapour (kg/m²)": "tcwv",
    "relative_humidity_2m (%)":                     "rh",
    "surface_pressure (hPa)":                       "pressure",
    "soil_moisture_7_to_28cm (m³/m³)":              "soil_moist",
    "precipitation (mm)":                           "precip",
    "cloud_cover (%)":                              "cloud",
    "cloud_cover_low (%)":                          "cloud_lo",
    "wind_speed_10m (km/h)":                        "ws10",
    "wind_direction_10m (°)":                       "wd10",
    "wind_gusts_10m (km/h)":                        "gust10",
    "wind_speed_100m (km/h)":                       "ws100",
    "wind_direction_100m (°)":                      "wd100",
}


def _read_openmeteo_csv(path: str) -> pd.DataFrame:
    """Baca CSV Open-Meteo, deteksi baris header via signature 'time,'."""
    with open(path, "r", encoding="utf-8") as fh:
        skip = 0
        for i, line in enumerate(fh):
            if line.lstrip().startswith("time,"):
                skip = i
                break
    df = pd.read_csv(path, skiprows=skip)
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").reset_index(drop=True)


def _idw_merge_series(v1: pd.Series, v2: pd.Series) -> pd.Series:
    """IDW-merge dua seri dengan fallback ke nilai yang tersedia."""
    idx = v1.index.union(v2.index)
    both = v1.notna() & v2.notna()
    out = pd.Series(np.nan, index=idx)
    out.loc[both] = IDW_W1_VOLATILE * v1[both] + IDW_W2_VOLATILE * v2[both]
    out.loc[v1.notna() & ~both] = v1[v1.notna() & ~both]
    out.loc[v2.notna() & ~both] = v2[v2.notna() & ~both]
    return out


def load_rich_hourly() -> Optional[pd.DataFrame]:
    """Muat data per-jam P1+P2, IDW-merge skalar & arah ke titik target."""
    global _METEO_CACHE
    if _METEO_CACHE is not None:
        return _METEO_CACHE

    p1 = find_data_file(DEFAULT_HOURLY_P1)
    p2 = find_data_file(DEFAULT_HOURLY_P2)
    if p1 is None and p2 is None:
        print("  [!] CSV meteorologi tidak ditemukan.")
        return None

    def _load(p: str) -> pd.DataFrame:
        return _read_openmeteo_csv(p).rename(columns=_RENAME)

    if p1 is None:
        df = _load(p2)
    elif p2 is None:
        df = _load(p1)
    else:
        d1 = _load(p1).set_index("time")
        d2 = _load(p2).set_index("time")
        idx = d1.index.union(d2.index)
        out = pd.DataFrame(index=idx)

        scalar_cols = ("vpd", "dew_pt", "tcwv", "rh", "pressure",
                       "soil_moist", "precip", "cloud", "cloud_lo",
                       "ws10", "gust10", "ws100")
        for col in scalar_cols:
            v1 = (d1[col].reindex(idx) if col in d1.columns
                  else pd.Series(np.nan, index=idx))
            v2 = (d2[col].reindex(idx) if col in d2.columns
                  else pd.Series(np.nan, index=idx))
            out[col] = _idw_merge_series(v1, v2)

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

    avail = [c for c in ("vpd", "dew_pt", "tcwv", "rh", "soil_moist")
             if c in df.columns]
    print(f"  [i] {len(df):,} baris · "
          f"{df['time'].min().date()} → {df['time'].max().date()}")
    print(f"      Precursor: {', '.join(avail)}")

    _METEO_CACHE = df
    return df


# ══════════════════════════════════════════════════════════════════════════
# Section 3 · Loader RMM (Wheeler–Hendon)
# ══════════════════════════════════════════════════════════════════════════

_RMM_CACHE: Optional[pd.DataFrame] = None


def _load_rmm() -> Optional[pd.DataFrame]:
    """Muat rmm8.csv (format BOM), tandai MJO aktif via ambang amplitudo."""
    global _RMM_CACHE
    if _RMM_CACHE is not None:
        return _RMM_CACHE

    path = find_data_file(DEFAULT_RMM_FILE)
    if path is None:
        print(f"  [!] {DEFAULT_RMM_FILE} tidak ditemukan — "
              f"gerbang MJO nonaktif")
        return None

    try:
        df = pd.read_csv(
            path, comment="#", skipinitialspace=True, header=None,
            names=["year", "month", "day", "rmm1", "rmm2",
                   "phase", "lon", "amp", "ampsq"],
        )
    except Exception as e:
        print(f"  [!] Gagal membaca {DEFAULT_RMM_FILE}: {e}")
        return None

    if len(df) == 0:
        print(f"  [!] {DEFAULT_RMM_FILE} kosong")
        return None

    try:
        out = pd.DataFrame({
            "date": pd.to_datetime(dict(
                year=df["year"].astype(int),
                month=df["month"].astype(int),
                day=df["day"].astype(int),
            )),
            "amp": df["amp"].astype(float),
        }).sort_values("date").reset_index(drop=True)
    except Exception as e:
        print(f"  [!] Format {DEFAULT_RMM_FILE} tidak dikenali: {e}")
        return None

    out["mjo_active"] = out["amp"] >= RMM_AMP_THRESHOLD
    _RMM_CACHE = out

    n_active = int(out["mjo_active"].sum())
    pct = 100.0 * n_active / max(len(out), 1)
    print(f"  [i] RMM dimuat: {len(out):,} hari  "
          f"({out['date'].min().date()} → {out['date'].max().date()})  "
          f"MJO aktif: {n_active:,} hari ({pct:.1f}%)")
    return out


def _mjo_active_on(rmm: Optional[pd.DataFrame],
                   dates: np.ndarray) -> np.ndarray:
    """Boolean mask MJO aktif untuk array tanggal datetime64.

    Tanggal di luar cakupan RMM dianggap MJO-netral (False).
    """
    if rmm is None:
        return np.zeros(len(dates), dtype=bool)
    s = rmm.set_index("date")["mjo_active"]
    idx = pd.DatetimeIndex(pd.to_datetime(dates))
    return s.reindex(idx, fill_value=False).values.astype(bool)


# ══════════════════════════════════════════════════════════════════════════
# Section 4 · Utilitas bersama
# ══════════════════════════════════════════════════════════════════════════

def _attach_dopy(d: pd.DataFrame, dc: str = "date") -> pd.DataFrame:
    """Tambahkan kolom dopy (day-of-pranata-year) ke DataFrame."""
    t = pd.to_datetime(d[dc])
    anchor = pd.to_datetime(dict(year=t.dt.year, month=ANCHOR_MONTH,
                                 day=ANCHOR_DAY))
    anchor_prev = pd.to_datetime(dict(year=t.dt.year - 1,
                                      month=ANCHOR_MONTH,
                                      day=ANCHOR_DAY))
    d = d.copy()
    d["dopy"] = np.where(
        t < anchor,
        (t - anchor_prev).dt.total_seconds() / 86400.0,
        (t - anchor).dt.total_seconds() / 86400.0,
    ) % 365.0
    return d


def _daily(df: pd.DataFrame, field: str,
           agg: str = "mean") -> pd.DataFrame:
    """Agregasi harian satu field dari data per-jam."""
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    s = (d.groupby("_date")
          .agg(v=(field, agg))
          .reset_index()
          .rename(columns={"_date": "date"}))
    return _attach_dopy(s.sort_values("date"))


def _roll(s: pd.DataFrame, win: int = ROLL_WIN) -> pd.DataFrame:
    """Rolling mean pada kolom 'v'."""
    s = s.copy()
    s["roll"] = (s["v"].rolling(win, center=True, min_periods=win // 2)
                 .mean())
    return s


def _cross(sig: np.ndarray, dpy: np.ndarray, thr: float, up: bool = True,
           sust: int = SUSTAIN, lo: float = SEARCH_LO,
           hi: float = SEARCH_HI, eps: float = EPS) -> Optional[float]:
    """Deteksi persilangan threshold dengan uji sustain.

    Parameters
    ----------
    sig  : sinyal (sudah dihaluskan)
    dpy  : dopy untuk setiap titik
    thr  : ambang persilangan
    up   : True = persilangan naik, False = turun
    sust : jumlah sampel berurutan yang harus bertahan di sisi threshold
    lo, hi, eps : jendela pencarian & toleransi sustain
    """
    for i in range(1, len(sig)):
        if not (lo <= dpy[i] <= hi):
            continue
        p, c = sig[i - 1], sig[i]
        if not (np.isfinite(p) and np.isfinite(c)):
            continue
        if up and p < thr <= c:
            fut = sig[i:i + sust]
            if (np.isfinite(fut).sum() >= sust - 3
                    and np.nanmin(fut) >= thr - eps):
                return float(dpy[i])
        elif not up and p > thr >= c:
            fut = sig[i:i + sust]
            if (np.isfinite(fut).sum() >= sust - 3
                    and np.nanmax(fut) <= thr + eps):
                return float(dpy[i])
    return None


def _year_slice(df: pd.DataFrame, py: int) -> pd.DataFrame:
    """Ambil subset data untuk pranata-tahun yang berjangkar 22 Juni py."""
    start = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
    return df[(df["time"] >= start)
              & (df["time"] < start + pd.Timedelta(days=366))].copy()


def _mpci_daily(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """MPCI = rata-rata Z-score 7 variabel precursor harian.

    Komponen: u_comp(+), rh(+), dew_pt(+), tcwv(+), cloud(+),
    precip(+), vpd(−). Memerlukan minimal 3 komponen valid.
    """
    comps = [(f, sgn) for f, sgn in (
        ("u_comp", +1), ("rh", +1), ("dew_pt", +1),
        ("tcwv", +1), ("cloud", +1), ("precip", +1), ("vpd", -1),
    ) if f in df.columns and df[f].notna().sum() > 50]
    if len(comps) < 3:
        return None

    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    daily = (d.groupby("_date")
              .agg(**{f: (f, "mean") for f, _ in comps})
              .reset_index()
              .rename(columns={"_date": "date"}))
    daily = _attach_dopy(daily.sort_values("date"))

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
                           .rolling(ROLL_WIN, center=True,
                                    min_periods=ROLL_WIN // 2)
                           .mean())
    return daily


# ══════════════════════════════════════════════════════════════════════════
# Section 5 · M1 — PELT  (Killick, Fearnhead & Eckley 2012)
# ══════════════════════════════════════════════════════════════════════════

def _pelt_l2(signal: np.ndarray, pen: float) -> List[int]:
    """PELT L2 cost (sum of squared deviations) dengan penalti."""
    n = len(signal)
    x = np.where(np.isfinite(signal), signal, np.nanmean(signal))
    S = np.zeros(n + 1)
    S2 = np.zeros(n + 1)
    for i in range(n):
        S[i + 1] = S[i] + x[i]
        S2[i + 1] = S2[i] + x[i] ** 2

    def cost(a: int, b: int) -> float:
        nb = b - a
        if nb <= 0:
            return 0.0
        return S2[b] - S2[a] - (S[b] - S[a]) ** 2 / nb

    F = np.full(n + 1, np.inf)
    F[0] = 0.0
    last = [-1] * (n + 1)
    cands = [0]
    for t in range(1, n + 1):
        best_v = np.inf
        best_s = -1
        for s in cands:
            v = F[s] + cost(s, t) + pen
            if v < best_v:
                best_v, best_s = v, s
        F[t] = best_v
        last[t] = best_s
        cands = [s for s in cands if F[s] + cost(s, t) <= F[t] + pen] + [t]

    bkps: List[int] = []
    t = n
    while last[t] > 0:
        bkps.append(last[t])
        t = last[t]
    return sorted(bkps)


def detect_pelt(df: pd.DataFrame) -> Optional[float]:
    """M1 — PELT pada MPCI daily, changepoint pertama > DRY_HI."""
    daily = _mpci_daily(df)
    if daily is None:
        return None
    win = daily[(daily["dopy"] >= SEARCH_LO)
                & (daily["dopy"] <= SEARCH_HI)].copy()
    if len(win) < 30:
        return None

    sig = win["mpci"].values
    sig = np.where(np.isfinite(sig), sig, np.nanmean(sig))
    dpy = win["dopy"].values

    pen = 1.5 * math.log(len(sig)) * max(np.nanvar(sig), 1e-6)
    try:
        bkps = _pelt_l2(sig, pen)
    except Exception:
        return None

    for b in bkps:
        if 0 < b < len(dpy) and dpy[b] > DRY_HI:
            return float(dpy[b])
    return None


# ══════════════════════════════════════════════════════════════════════════
# Section 6 · M2 — Shiryaev-Roberts  (Pollak 1985)
# ══════════════════════════════════════════════════════════════════════════

def detect_sr(df: pd.DataFrame) -> Optional[float]:
    """M2 — Shiryaev-Roberts pada MPCI_roll; threshold A = 0.5/λ."""
    daily = _mpci_daily(df)
    if daily is None:
        return None
    win = daily[(daily["dopy"] >= DRY_LO)
                & (daily["dopy"] <= SEARCH_HI)].copy()
    if len(win) < 30:
        return None

    sig = win["mpci_roll"].values
    dpy = win["dopy"].values
    sig = np.where(np.isfinite(sig), sig, np.nanmean(sig))

    base_mask = (dpy >= DRY_LO) & (dpy <= DRY_HI)
    base = sig[base_mask]
    base = base[np.isfinite(base)]
    if len(base) < 10:
        return None
    mu_E = float(np.mean(base))
    sig_E = float(np.std(base)) + 1e-9

    west_mask = (dpy >= 150) & (dpy <= 200)
    west = sig[west_mask]
    west = west[np.isfinite(west)]
    mu_W = float(np.mean(west)) if len(west) >= 5 else mu_E + sig_E

    def log_lr(x: float) -> float:
        return ((2 * x * (mu_W - mu_E) - mu_W ** 2 + mu_E ** 2)
                / (2 * sig_E ** 2))

    N = len(dpy)
    lam = 1.0 / max(N, 1)
    threshold = 0.5 / lam

    R = 0.0
    start = int(np.searchsorted(dpy, SEARCH_LO))
    for t in range(start, N):
        x = sig[t]
        if not np.isfinite(x):
            continue
        R = (1.0 + R) * math.exp(log_lr(x))
        if SEARCH_LO <= dpy[t] <= SEARCH_HI and R >= threshold:
            return float(dpy[t])
    return None


# ══════════════════════════════════════════════════════════════════════════
# Section 7 · M3 — Pettitt non-parametrik  (Pettitt 1979)
# ══════════════════════════════════════════════════════════════════════════

_pettitt_meta: Dict[int, dict] = {}


def detect_pettitt(df: pd.DataFrame, py: int = 0) -> Optional[float]:
    """M3 — Pettitt pada u_comp 7-hari smoothed, ambil CP pertama."""
    s = _daily(df, "u_comp", "mean")
    win = s[(s["dopy"] >= SEARCH_LO) & (s["dopy"] <= SEARCH_HI)].copy()
    if len(win) < 20:
        return None

    win["u7"] = win["v"].rolling(7, center=True, min_periods=4).mean()
    sig = win["u7"].values
    dpy = win["dopy"].values
    sig = np.where(np.isfinite(sig), sig, np.nanmean(sig))
    n = len(sig)

    ranks = spstats.rankdata(sig)
    cumranks = np.cumsum(ranks)
    U = 2 * cumranks - np.arange(1, n + 1, dtype=float) * (n + 1)
    K = float(np.max(np.abs(U)))
    cp_idx = int(np.argmax(np.abs(U)))
    pval = min(2 * math.exp(-6 * K * K / (n ** 3 + n ** 2)), 1.0)

    if py:
        _pettitt_meta[py] = {"pval": pval, "K": K, "n": n}
    if pval > 0.05:
        return None

    d = float(dpy[cp_idx])
    return d if SEARCH_LO <= d <= SEARCH_HI else None


# ══════════════════════════════════════════════════════════════════════════
# Section 8 · M4 — Slope VPD 7-hari
# ══════════════════════════════════════════════════════════════════════════

def detect_dvpd(df: pd.DataFrame) -> Optional[float]:
    """M4 — Slope VPD 7-hari turun di bawah μ − 2σ baseline musim kering."""
    if "vpd" not in df.columns or df["vpd"].notna().sum() < 100:
        return None

    s = _daily(df, "vpd")
    vpd = s["v"].values
    dpy = s["dopy"].values
    n = len(vpd)

    slopes = np.full(n, np.nan)
    xs = np.arange(7, dtype=float)
    for i in range(6, n):
        blk = vpd[i - 6:i + 1]
        valid = np.isfinite(blk)
        if valid.sum() >= 4:
            try:
                slopes[i] = spstats.linregress(
                    xs[valid], blk[valid]).slope
            except Exception:
                pass

    slope_s = (pd.Series(slopes)
               .rolling(5, center=True, min_periods=3)
               .mean()
               .values)

    base = (dpy >= DRY_LO) & (dpy <= DRY_HI) & np.isfinite(slope_s)
    if base.sum() < 10:
        return None
    mu_b = np.nanmean(slope_s[base])
    sd_b = np.nanstd(slope_s[base]) + 1e-9
    thr = mu_b - 2 * sd_b

    for i in range(1, n):
        if not (SEARCH_LO <= dpy[i] <= SEARCH_HI):
            continue
        if not np.isfinite(slope_s[i]) or slope_s[i] >= thr:
            continue
        fut = slope_s[i:i + 7]
        valid = np.isfinite(fut)
        if valid.sum() >= 5 and np.nanmean(fut[valid]) < thr:
            return float(dpy[i])
    return None


# ══════════════════════════════════════════════════════════════════════════
# Section 9 · M5 — CUSUM pada MPCI_roll  (Page 1954)
# ══════════════════════════════════════════════════════════════════════════

CUSUM_LO = 90.0     # akumulasi CUSUM dimulai fresh di sini


def detect_cusum_mpci(df: pd.DataFrame) -> Optional[float]:
    """M5 — CUSUM satu-sisi pada MPCI_roll, h = 3σ_baseline."""
    daily = _mpci_daily(df)
    if daily is None:
        return None
    win = daily[(daily["dopy"] >= DRY_LO)
                & (daily["dopy"] <= SEARCH_HI)].reset_index(drop=True)
    if len(win) < 30:
        return None

    sig = win["mpci_roll"].values
    dpy = win["dopy"].values
    sig = np.where(np.isfinite(sig), sig, np.nanmean(sig))

    base_mask = (dpy >= DRY_LO) & (dpy <= DRY_HI)
    base = sig[base_mask]
    base = base[np.isfinite(base)]
    if len(base) < 10:
        return None
    mu_b = float(np.mean(base))
    sd_b = float(np.std(base)) + 1e-9
    k = 0.5 * sd_b
    h = 3.0 * sd_b

    start_idx = int(np.searchsorted(dpy, CUSUM_LO))
    cp = np.zeros(len(sig))
    for i in range(start_idx + 1, len(sig)):
        v = sig[i]
        if np.isfinite(v):
            cp[i] = max(0.0, cp[i - 1] + (v - mu_b) - k)

    for i in range(start_idx + 1, len(cp)):
        if not (CUSUM_LO <= dpy[i] <= SEARCH_HI):
            continue
        if cp[i] > h:
            fut = cp[i:i + 5]
            if np.all(fut > h * 0.7):
                return float(dpy[i])
    return None


# ══════════════════════════════════════════════════════════════════════════
# Section 10 · M6–M10 — Precursor fisik
# ══════════════════════════════════════════════════════════════════════════

def detect_vpd_drop(df: pd.DataFrame) -> Optional[float]:
    """M6 — VPD 30-hari turun di bawah 65 % median musim kering."""
    if "vpd" not in df.columns or df["vpd"].notna().sum() < 100:
        return None
    s = _roll(_daily(df, "vpd"))
    dry = s[(s["dopy"] >= DRY_LO)
            & (s["dopy"] <= DRY_HI)]["roll"].dropna()
    if len(dry) < 10:
        return None
    return _cross(s["roll"].values, s["dopy"].values,
                  float(np.median(dry) * 0.65), up=False)


def detect_td_p97(df: pd.DataFrame) -> Optional[float]:
    """M7 — Titik embun 30-hari melewati P97 musim kering."""
    if "dew_pt" not in df.columns or df["dew_pt"].notna().sum() < 100:
        return None
    s = _roll(_daily(df, "dew_pt"))
    dry = s[(s["dopy"] >= DRY_LO)
            & (s["dopy"] <= DRY_HI)]["roll"].dropna()
    if len(dry) < 10:
        return None
    return _cross(s["roll"].values, s["dopy"].values,
                  float(np.percentile(dry, 97)), up=True)


def detect_shear(df: pd.DataFrame) -> Optional[float]:
    """M8 — Shear vertikal δu = u100 − u10 melintas 0 dari negatif
    ke positif."""
    for c in ("ws10", "ws100", "wd10", "wd100"):
        if c not in df.columns or df[c].notna().sum() < 100:
            return None
    d = df.copy()
    d["du"] = (-d["ws100"] * np.sin(np.deg2rad(d["wd100"]))
               - (-d["ws10"] * np.sin(np.deg2rad(d["wd10"]))))
    s = _roll(_daily(d, "du"))
    return _cross(s["roll"].values, s["dopy"].values, 0.0, up=True)


def detect_soil(df: pd.DataFrame) -> Optional[float]:
    """M9 — Soil moisture 30-hari melewati P80 musim kering."""
    if ("soil_moist" not in df.columns
            or df["soil_moist"].notna().sum() < 100):
        return None
    s = _roll(_daily(df, "soil_moist"))
    dry = s[(s["dopy"] >= DRY_LO)
            & (s["dopy"] <= DRY_HI)]["roll"].dropna()
    if len(dry) < 10:
        return None
    return _cross(s["roll"].values, s["dopy"].values,
                  float(np.percentile(dry, 80)), up=True)


def detect_base_u(df: pd.DataFrame) -> Optional[float]:
    """M10 — Baseline EV09wind: u_comp 30-hari rolling > 0."""
    daily = _rolling_daily_ucomp(df)
    return _find_crossing(daily["u30"].values, daily["dopy"].values)


# ══════════════════════════════════════════════════════════════════════════
# Section 11 · M11 — Lanczos zero-phase + recovery + gerbang MJO
# ══════════════════════════════════════════════════════════════════════════
#
# Konvensi fase (untuk referensi):
#   EV09wind mendefinisikan u_comp = −sin(wd10), v_comp = −cos(wd10),
#   maka rekonstruksi from-direction = atan2(u, v) + 180° (mod 360°).
#   Angin barat murni (wd10 = 270°) → u = +1, v = 0 → fase = 270°.
#
# Filter Lanczos:
#   Kernel sinc windowed (Duchon 1979), konvolusi simetris
#   (mode='same'). Window 241 hari, cutoff 80 hari. Zero phase-shift:
#   tanggal tidak bergeser, berbeda dengan rolling mean yang menggeser
#   W/2.
#
# Gerbang MJO:
#   RMM (Wheeler & Hendon 2004) amplitude ≥ RMM_AMP_THRESHOLD menandai
#   MJO aktif. Kandidat crossing yang bertabrakan dengan MJO aktif
#   ditolak — MJO adalah gangguan 30–60 hari yang dapat memicu lonjakan
#   angin barat sesaat yang menyerupai onset monsoon.

_LANCZOS_CACHE: Optional[pd.DataFrame] = None
_LANCZOS_PARAMS: Tuple[int, float] = (LANCZOS_WINDOW, LANCZOS_CUTOFF_DAYS)


def lanczos_low_pass_weights(window_length: int,
                             cutoff_frequency: float) -> np.ndarray:
    """Bobot kernel Lanczos 1D low-pass (windowed-sinc).

    Parameters
    ----------
    window_length    : panjang jendela (harus ganjil, ≥ 3× cutoff)
    cutoff_frequency : frekuensi cutoff (siklus/hari), harus di (0, 0.5)

    Returns
    -------
    np.ndarray panjang `window_length`, ternormalisasi sum = 1.

    Referensi
    ---------
    Duchon, C. E. (1979). J. Appl. Meteor. 18(8):1016–1022.
    """
    if window_length % 2 == 0:
        raise ValueError("window_length harus ganjil")
    if not 0.0 < cutoff_frequency < 0.5:
        raise ValueError("cutoff_frequency harus di (0, 0.5)")

    order = (window_length - 1) // 2
    n = np.arange(-order, order + 1, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        sinc_ideal = np.sin(2 * np.pi * cutoff_frequency * n) / (np.pi * n)
        sigma = np.sin(np.pi * n / order) / (np.pi * n / order)
    sinc_ideal[order] = 2.0 * cutoff_frequency
    sigma[order] = 1.0
    w = sinc_ideal * sigma
    return w / w.sum()


def _daily_lanczos(df: pd.DataFrame,
                   window_length: int = LANCZOS_WINDOW,
                   cutoff_days: float = LANCZOS_CUTOFF_DAYS
                   ) -> pd.DataFrame:
    """Agregasi harian u_comp, v_comp + Lanczos low-pass (cached)."""
    global _LANCZOS_CACHE, _LANCZOS_PARAMS
    if (_LANCZOS_CACHE is not None
            and _LANCZOS_PARAMS == (window_length, cutoff_days)):
        return _LANCZOS_CACHE

    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    daily = (d.groupby("_date")
              .agg(u_raw=("u_comp", "mean"), v_raw=("v_comp", "mean"))
              .reset_index()
              .rename(columns={"_date": "date"})
              .sort_values("date")
              .reset_index(drop=True))

    daily["u_raw"] = daily["u_raw"].interpolate(limit_direction="both")
    daily["v_raw"] = daily["v_raw"].interpolate(limit_direction="both")

    w = lanczos_low_pass_weights(window_length, 1.0 / cutoff_days)
    u_s = spsig.convolve(daily["u_raw"].values, w, mode="same")
    v_s = spsig.convolve(daily["v_raw"].values, w, mode="same")

    daily["u_lanczos"] = u_s
    daily["v_lanczos"] = v_s

    rad = np.arctan2(u_s, v_s)
    daily["wd_vector_phase"] = (np.rad2deg(rad) + 180.0) % 360.0

    daily = _attach_dopy(daily, dc="date")
    _LANCZOS_CACHE = daily
    _LANCZOS_PARAMS = (window_length, cutoff_days)
    return daily


def detect_lanczos_vecphase(df: pd.DataFrame, py: int,
                            window_length: int = LANCZOS_WINDOW,
                            cutoff_days: float = LANCZOS_CUTOFF_DAYS
                            ) -> Optional[float]:
    """M11 — Lanczos zero-phase + recovery-fraction + gerbang MJO.

    Logika:
      1. Hitung amplitudo musiman: u_min di dopy [DRY_LO, DRY_HI],
         u_max di dopy [180, 280].
      2. Threshold = u_min + U_RECOVERY_FRACTION × (u_max − u_min).
         Fallback threshold = 0.02 jika amplitudo < 0.15.
      3. Cari persilangan naik threshold dalam jendela
         [SEARCH_LO, SEARCH_HI].
      4. Tolak kandidat jika MJO aktif (RMM amp ≥ RMM_AMP_THRESHOLD)
         pada hari persilangan.
    """
    daily = _daily_lanczos(df, window_length, cutoff_days)

    anchor = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
    end = anchor + pd.Timedelta(days=365)
    sub = (daily[(daily["date"] >= anchor) & (daily["date"] < end)]
           .reset_index(drop=True))
    if len(sub) < 60:
        return None

    u_sig = sub["u_lanczos"].values
    dpy = sub["dopy"].values
    dates = sub["date"].values
    n = len(u_sig)

    rmm = _load_rmm()
    mjo = _mjo_active_on(rmm, dates)

    dry_mask = (dpy >= DRY_LO) & (dpy <= DRY_HI)
    wet_mask = (dpy >= 180) & (dpy <= 280)
    if dry_mask.sum() < 10 or wet_mask.sum() < 10:
        return None

    u_min = float(np.nanmin(u_sig[dry_mask]))
    u_max = float(np.nanmax(u_sig[wet_mask]))
    if not (np.isfinite(u_min) and np.isfinite(u_max)):
        return None
    if u_max - u_min < 0.05:
        return None

    threshold = u_min + U_RECOVERY_FRACTION * (u_max - u_min)
    if u_max - u_min < 0.15:
        threshold = 0.02

    for i in range(1, n - 1):
        d = float(dpy[i])
        if not (SEARCH_LO <= d <= SEARCH_HI):
            continue
        if not (np.isfinite(u_sig[i - 1]) and np.isfinite(u_sig[i])):
            continue
        if not (u_sig[i - 1] < threshold <= u_sig[i]):
            continue
        if mjo[i]:
            continue
        return d
    return None


# ══════════════════════════════════════════════════════════════════════════
# Section 12 · Ensemble
# ══════════════════════════════════════════════════════════════════════════

def ensemble_vote(res: Dict[str, Optional[float]]) -> Optional[float]:
    """Weighted-median ensemble dari semua deteksi valid."""
    vals, ws = [], []
    for m, v in res.items():
        if v is not None and SEARCH_LO <= v <= SEARCH_HI:
            vals.append(v)
            ws.append(ENSEMBLE_WEIGHTS.get(m, 1.0))
    if not vals:
        return None
    rep: List[float] = []
    for v, w in zip(vals, ws):
        rep.extend([v] * max(1, int(round(w * 10))))
    return float(np.median(rep))


def run_all(df: pd.DataFrame, py: int) -> Dict[str, Optional[float]]:
    """Jalankan semua metode M1–M11 untuk satu pranata-tahun."""
    sub = _year_slice(df, py)
    if len(sub) < 5000:
        return {}

    def _shear(d: pd.DataFrame) -> Optional[float]:
        if any(c not in d.columns or d[c].notna().sum() < 100
               for c in ("ws10", "ws100", "wd10", "wd100")):
            return None
        d2 = d.copy()
        d2["du"] = (-d2["ws100"] * np.sin(np.deg2rad(d2["wd100"]))
                    - (-d2["ws10"] * np.sin(np.deg2rad(d2["wd10"]))))
        s = _roll(_daily(d2, "du"))
        return _cross(s["roll"].values, s["dopy"].values, 0.0, up=True)

    return {
        "M1_PELT":     detect_pelt(sub),
        "M2_SR":       detect_sr(sub),
        "M3_Pett":     detect_pettitt(sub, py),
        "M4_dVPD":     detect_dvpd(sub),
        "M5_CUSUM":    detect_cusum_mpci(sub),
        "M6_VPD":      detect_vpd_drop(sub),
        "M7_Td":       detect_td_p97(sub),
        "M8_Shear":    _shear(sub),
        "M9_Soil":     detect_soil(sub),
        "M10_BaseU":   detect_base_u(sub),
        "M11_Lanczos": detect_lanczos_vecphase(df, py),
    }


# ══════════════════════════════════════════════════════════════════════════
# Section 13a · Loader ENSO / IOD (mandiri, tanpa import baratan)
# ══════════════════════════════════════════════════════════════════════════

_ENSO_SST_CSV  = "Sst_nino34_index.csv"
_ENSO_MSLA_CSV = "Msla_nino34_index.csv"
_IOD_WEEKLY    = "iod_1.txt"
_IOD_MONTHLY   = "30yr_dmi_3rmean.txt"

_ENSO_THR: float = 0.50         # |ASO mean SST| → El Niño/La Niña
_IOD_THR:  float = 0.40         # |SON mean DMI| → pIOD/nIOD

# Threshold "kuat" untuk flag anomali (v5.4: simetris 0.75)
_ANOMALY_SST_STR: float = 0.75  # |SST_ASO| ≥ nilai ini → "kuat"
_ANOMALY_DMI_STR: float = 0.75  # |DMI_SON| ≥ nilai ini → "kuat"

_ANOMALY_SIGMA:   float = 1.50  # flag aktif bila |residual| > n×σ


def _enso_classify(v: float) -> str:
    if v >= _ENSO_THR:   return "El Niño"
    if v <= -_ENSO_THR:  return "La Niña"
    return "Netral"


def _iod_classify(v: float) -> str:
    if v >= _IOD_THR:    return "pIOD"
    if v <= -_IOD_THR:   return "nIOD"
    return "Netral"


def _load_enso_context_adv() -> Dict[int, Dict]:
    """Bangun konteks ENSO + IOD per pranata-tahun (2015–2026).

    Setiap entri: {sst_aso, sla_aso, dmi_son, enso_phase, iod_phase,
                   interaction}.
    File yang tidak tersedia menghasilkan None pada field terkait.
    """
    # ── SST Niño3.4 (epoch 1978-01-01 12:00) ─────────────────────────────
    sst_df: Optional["pd.DataFrame"] = None
    ep = find_data_file(_ENSO_SST_CSV)
    if ep is not None:
        try:
            import pandas as _pd
            raw = _pd.read_csv(ep)
            base = datetime(1978, 1, 1, 12, 0, 0)
            raw["date"]  = raw["time"].apply(
                lambda d: base + timedelta(days=float(d)))
            raw["year"]  = raw["date"].dt.year
            raw["month"] = raw["date"].dt.month
            sst_df = raw.sort_values("date").reset_index(drop=True)
        except Exception:
            sst_df = None

    # ── MSLA Niño3.4 (epoch 1950-01-01 00:00) ────────────────────────────
    msla_df: Optional["pd.DataFrame"] = None
    mp = find_data_file(_ENSO_MSLA_CSV)
    if mp is not None:
        try:
            import pandas as _pd
            raw = _pd.read_csv(mp)
            base = datetime(1950, 1, 1, 0, 0, 0)
            raw["date"]  = raw["time"].apply(
                lambda d: base + timedelta(days=float(d)))
            raw["year"]  = raw["date"].dt.year
            raw["month"] = raw["date"].dt.month
            msla_df = raw.sort_values("date").reset_index(drop=True)
        except Exception:
            msla_df = None

    # ── DMI IOD — mingguan preferred, bulanan fallback ───────────────────
    iod_monthly: Optional["pd.DataFrame"] = None
    iw = find_data_file(_IOD_WEEKLY)
    if iw is not None:
        rows: List = []
        try:
            with open(iw, encoding="utf-8") as fh:
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
            import pandas as _pd
            wdf = _pd.DataFrame(rows, columns=["year", "month", "dmi"])
            iod_monthly = (wdf.groupby(["year", "month"])["dmi"]
                             .mean().reset_index()
                             .sort_values(["year", "month"])
                             .reset_index(drop=True))

    if iod_monthly is None:
        im = find_data_file(_IOD_MONTHLY)
        if im is not None:
            rows_m: List = []
            try:
                with open(im, encoding="utf-8") as fh:
                    lines = [ln.split() for ln in fh if ln.strip()]
                for p in lines[1:]:
                    if len(p) < 13:
                        continue
                    try:
                        yr = int(p[0])
                        for mo, vs in enumerate(p[1:13], 1):
                            v = float(vs)
                            if abs(v - 99.90) > 1e-4:
                                rows_m.append((yr, mo, v))
                    except (ValueError, IndexError):
                        continue
            except OSError:
                pass
            if rows_m:
                import pandas as _pd
                iod_monthly = (
                    _pd.DataFrame(rows_m,
                                  columns=["year", "month", "dmi"])
                    .sort_values(["year", "month"]).reset_index(drop=True)
                )

    # ── Rakit per pranata-tahun ───────────────────────────────────────────
    ctx: Dict[int, Dict] = {}
    for py in range(2015, 2027):
        rec: Dict = {}

        sst_aso: Optional[float] = None
        if sst_df is not None:
            sub = sst_df[(sst_df["year"] == py)
                          & sst_df["month"].isin([8, 9, 10])]["enso"]
            if len(sub) >= 1:
                sst_aso = float(sub.mean())
        rec["sst_aso"]    = sst_aso
        rec["enso_phase"] = (_enso_classify(sst_aso)
                             if sst_aso is not None else "Netral")

        sla_aso: Optional[float] = None
        if msla_df is not None:
            sub = msla_df[(msla_df["year"] == py)
                           & msla_df["month"].isin([8, 9, 10])]["enso"]
            if len(sub) >= 1:
                sla_aso = float(sub.mean())
        rec["sla_aso"] = sla_aso

        dmi_son: Optional[float] = None
        if iod_monthly is not None:
            sub = iod_monthly[(iod_monthly["year"] == py)
                               & iod_monthly["month"].isin([9, 10, 11])
                              ]["dmi"]
            if len(sub) >= 1:
                dmi_son = float(sub.mean())
        rec["dmi_son"]   = dmi_son
        rec["iod_phase"] = (_iod_classify(dmi_son)
                            if dmi_son is not None else "Netral")

        ep_s = rec["enso_phase"]
        ip_s = rec["iod_phase"]
        if ((ep_s == "El Niño" and ip_s == "pIOD")
                or (ep_s == "La Niña" and ip_s == "nIOD")):
            rec["interaction"] = "SINERGI"
        elif ((ep_s == "El Niño" and ip_s == "nIOD")
                or (ep_s == "La Niña" and ip_s == "pIOD")):
            rec["interaction"] = "COUNTER"
        else:
            rec["interaction"] = "NETRAL"

        ctx[py] = rec
    return ctx


def _anomaly_flag_adv(ctx_rec: Dict,
                      ens_val: Optional[float],
                      med_ens: float,
                      sigma_ens: float) -> str:
    """Tandai anomali ENSO×IOD pada monsoon reversal.

    Kriteria anomali aktif:
      · Interaksi COUNTER kuat: |SST_ASO| ≥ 0.75 DAN |DMI_SON| ≥ 0.75
        DAN |ensemble − median| > 1.5σ
      · Interaksi SINERGI kuat: sama, tapi tandai sebagai penguat
      · El Niño / La Niña murni tanpa IOD berlawanan: hanya catat fase
    """
    sst  = ctx_rec.get("sst_aso")
    dmi  = ctx_rec.get("dmi_son")
    iact = ctx_rec.get("interaction", "NETRAL")
    ep   = ctx_rec.get("enso_phase", "Netral")
    ip   = ctx_rec.get("iod_phase", "Netral")

    parts: List[str] = []

    is_strong = (sst is not None and dmi is not None
                 and abs(sst) >= _ANOMALY_SST_STR
                 and abs(dmi) >= _ANOMALY_DMI_STR)

    if ens_val is not None and np.isfinite(ens_val) and sigma_ens > 0:
        dev = abs(ens_val - med_ens)
        is_deviant = dev > _ANOMALY_SIGMA * sigma_ens
    else:
        is_deviant = False

    if iact == "COUNTER" and is_strong and is_deviant:
        parts.append("⚠COUNTER")
        if ens_val is not None:
            if ens_val > med_ens:
                parts.append("(reversal terlambat)")
            else:
                parts.append("(reversal lebih awal)")
    elif iact == "COUNTER" and is_strong:
        parts.append("⚠COUNTER-kuat")
    elif iact == "SINERGI" and is_strong:
        parts.append("✦SINERGI")

    if ep != "Netral" or ip not in ("Netral",):
        ep_s = ("ElN" if ep == "El Niño"
                else "LaN" if ep == "La Niña" else "—")
        ip_s = ip if ip != "Netral" else "—"
        parts.append(f"[{ep_s}/{ip_s}]")

    return " ".join(parts) if parts else "—"


_METHOD_SHORT = {
    "M1_PELT":     "PELT",
    "M2_SR":       "SR",
    "M3_Pett":     "Pett",
    "M4_dVPD":     "dVPD",
    "M5_CUSUM":    "CUSU",
    "M6_VPD":      "VPD↓",
    "M7_Td":       "Td↑",
    "M8_Shear":    "Sher",
    "M9_Soil":     "Soil",
    "M10_BaseU":   "BaseU",
    "M11_Lanczos": "Lancz",
}
_METHODS = list(_METHOD_SHORT.keys())

_METHOD_NOTE = {
    "M1_PELT":     "PELT L2+BIC, CP pertama>dopy120 (Killick 2012)",
    "M2_SR":       "Shiryaev-Roberts, threshold A=0.5/λ (Pollak 1985)",
    "M3_Pett":     "Pettitt test, u_comp 7d-smooth (Pettitt 1979)",
    "M4_dVPD":     "Slope VPD 7d, μ−2σ adaptive thr",
    "M5_CUSUM":    "CUSUM MPCI_roll, h=3σ_baseline (Page 1954)",
    "M6_VPD":      "VPD level < 65% median kering",
    "M7_Td":       "Dew point > P97 kering",
    "M8_Shear":    "δu (100m−10m) crossing 0",
    "M9_Soil":     "Soil moisture > P80 kering",
    "M10_BaseU":   "u_comp 30d rolling > 0 (baseline EV09wind)",
    "M11_Lanczos": ("Lanczos 241hr/80hr + recovery 20% + RMM gate "
                    "(Duchon 1979; Wheeler & Hendon 2004)"),
    "ENSEM":       "Weighted-median semua valid",
}

_METHOD_TIER = {
    "M1_PELT": 1, "M2_SR": 1, "M11_Lanczos": 1,
    "M3_Pett": 2, "M4_dVPD": 2, "M5_CUSUM": 2,
    "M6_VPD": 3, "M7_Td": 3, "M8_Shear": 3,
    "M9_Soil": 3, "M10_BaseU": 3,
}


# ══════════════════════════════════════════════════════════════════════════
# Section 13b · Utilitas format keluaran (konsol 72 kolom)
# ══════════════════════════════════════════════════════════════════════════

def _wrap(text: str,
          initial_indent: str = "  ",
          subsequent_indent: Optional[str] = None,
          width: int = CONSOLE_WIDTH) -> str:
    """Bungkus paragraf ke lebar konsol dengan indent konsisten."""
    if subsequent_indent is None:
        subsequent_indent = initial_indent
    return textwrap.fill(
        text, width=width,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _wrap_block(text: str,
                indent: str = "",
                width: int = CONSOLE_WIDTH) -> List[str]:
    """Bungkus blok teks multi-baris; leading whitespace asli
    dipertahankan sebagai hanging indent sehingga baris lanjutan
    sejajar dengan sumber aslinya.

    Setiap baris sumber dibungkus sendiri; baris kosong dipertahankan
    sebagai pemisah paragraf.
    """
    out: List[str] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            out.append("")
            continue
        lstripped = raw_line.lstrip()
        lead = raw_line[:len(raw_line) - len(lstripped)]
        total = indent + lead
        wrapped = textwrap.wrap(
            lstripped,
            width=width,
            initial_indent=total,
            subsequent_indent=total,
            break_long_words=False,
            break_on_hyphens=False,
        )
        out.extend(wrapped or [""])
    return out


def _print_wrapped_block(text: str,
                         indent: str = "",
                         width: int = CONSOLE_WIDTH) -> None:
    for line in _wrap_block(text, indent=indent, width=width):
        print(line)


def _rule(char: str = "─",
          indent: str = "  ",
          width: int = CONSOLE_WIDTH) -> str:
    """Garis horizontal; 2 kolom di bawah lebar konsol agar tidak
    memicu auto-wrap terminal pada beberapa emulator."""
    return indent + char * (width - len(indent) - 2)


# ══════════════════════════════════════════════════════════════════════════
# Section 13c · Bagian laporan
# ══════════════════════════════════════════════════════════════════════════

def _print_lanczos_characteristics() -> None:
    """Cetak karakteristik filter Lanczos pada konfigurasi saat ini."""
    print()
    print("  ── Karakteristik filter Lanczos (M11) ──")
    print(f"  Panjang jendela      : {LANCZOS_WINDOW} hari (~8 bulan)")
    print(f"  Cutoff               : {LANCZOS_CUTOFF_DAYS:.0f} hari "
          f"(f_c = 1/{LANCZOS_CUTOFF_DAYS:.0f} hari⁻¹)")
    print(f"  Konvolusi            : mode='same' → zero phase-shift")
    print(f"  Ambang pulih musiman : "
          f"{U_RECOVERY_FRACTION*100:.0f}% amplitudo")
    print(f"  Gerbang MJO          : RMM amp ≥ {RMM_AMP_THRESHOLD} "
          f"(fraksi jendela = {MJO_WINDOW_FRACTION:.1f})")
    print()
    print("  Respons gain |H(f)| pada frekuensi karakteristik:")

    w = lanczos_low_pass_weights(LANCZOS_WINDOW, 1.0 / LANCZOS_CUTOFF_DAYS)
    n_kernel = np.arange(-(len(w) // 2), len(w) // 2 + 1)
    for label, T in (
        ("MJO (30–60 hr)",   45.0),
        ("Gelombang Kelvin", 15.0),
        ("Siklon tropis",     7.0),
        ("Monsun tahunan",  365.0),
        ("ISO (10–20 hr)",   15.0),
        ("Cold surge",        5.0),
    ):
        f = 1.0 / T
        H = np.abs(np.sum(w * np.exp(-2j * np.pi * f * n_kernel)))
        print(f"    {label:<18}  T={T:>5.1f} hr  |H|={H:.3f}")
    print()


def _print_section_a(all_res, ens_vals) -> None:
    sec_header("A · DETEKSI PER PRANATA-TAHUN")

    _ctx_a   = _load_enso_context_adv()
    _med_a   = float(np.median(ens_vals)) if ens_vals else float("nan")
    _sigma_a = (float(np.std(ens_vals, ddof=1))
                if len(ens_vals) > 1 else 0.0)

    print("  Nilai = dopy deteksi; '—' = metode tidak mendeteksi.")
    print("  Baris 1: Tier-1/Tier-2. Baris 2: precursor.")
    print("  Baris 3: Lanczos + ensemble. Baris 4: anotasi iklim.")
    print(_rule())

    def _c(m, res):
        v = res.get(m)
        return f"{v:>4.0f}" if v is not None else "   —"

    for py in range(2015, 2027):
        res = all_res.get(py, {})
        if not res:
            continue
        ens = ensemble_vote(res)

        print(f"  {py} │ PELT {_c('M1_PELT',res)}"
              f"│ SR {_c('M2_SR',res)}"
              f"│ Pett {_c('M3_Pett',res)}"
              f"│ dVPD {_c('M4_dVPD',res)}"
              f"│ CUSU {_c('M5_CUSUM',res)}")
        print(f"       │ VPD↓ {_c('M6_VPD',res)}"
              f"│ Td↑ {_c('M7_Td',res)}"
              f"│ Sher {_c('M8_Shear',res)}"
              f"│ Soil {_c('M9_Soil',res)}"
              f"│ Base {_c('M10_BaseU',res)}")
        ens_s = f"{ens:>5.1f}" if ens else "  n/a"
        date_s = _dopy_to_approx_date(py, ens) if ens else "—"
        print(f"       │ Lancz {_c('M11_Lanczos',res)}"
              f"│ ENSEM {ens_s} → {date_s}")

        flag = _anomaly_flag_adv(
            _ctx_a.get(py, {}), ens, _med_a, _sigma_a)
        if flag and flag != "—":
            print(_wrap(flag,
                        initial_indent="       │ Iklim: ",
                        subsequent_indent="       │        "))
        print()


def _print_section_b(all_res, ens_vals) -> None:
    sec_header("B · STATISTIK RINGKASAN PER METODE")
    print("  Statistik dopy deteksi: N, μ, median, σ, [min..max].")
    print(_rule())

    for m in _METHODS + ["ENSEM"]:
        sh = _METHOD_SHORT.get(m, "ENSEM") if m != "ENSEM" else "ENSEM"
        if m == "ENSEM":
            vals = ens_vals
        else:
            vals = [v for yr in all_res for mm, v in all_res[yr].items()
                    if mm == m and v is not None]

        if len(vals) < 2:
            print(f"  {sh:<6}  (N<2, statistik tidak memadai)")
            print()
            continue

        a = np.array(vals)
        stat_line = (f"  {sh:<6}  N={len(a):>2}  "
                     f"μ={a.mean():>5.1f}  M={np.median(a):>5.1f}  "
                     f"σ={a.std(ddof=1):>4.1f}  "
                     f"[{a.min():.0f}..{a.max():.0f}]")
        print(stat_line)
        note = _METHOD_NOTE.get(m, "")
        if note:
            print(_wrap(note,
                        initial_indent="         · ",
                        subsequent_indent="           "))
        print()


def _print_section_c(all_res) -> None:
    sec_header("C · PETTITT — SIGNIFIKANSI & STATISTIK")
    print("  Uji Pettitt non-parametrik; p<0.05 → perubahan rezim "
          "signifikan.")
    print(_rule())
    print(f"  {'Thn':<6}{'p-value':>10}{'Signif.':>11}"
          f"{'K':>8}{'n':>5}{'CP':>7}")
    print("  " + "─" * 42)

    for yr in sorted(all_res.keys()):
        m = _pettitt_meta.get(yr, {})
        cp = all_res[yr].get("M3_Pett")
        pv = m.get("pval", np.nan)
        K = m.get("K", np.nan)
        n = m.get("n", 0)
        sig_str = ("★p<0.001" if pv < 0.001
                   else "★p<0.05" if pv < 0.05 else "  n.s.")
        cp_str = f"{cp:.0f}" if cp else "—"
        print(f"  {yr:<6}{pv:>10.6f}{sig_str:>11}"
              f"{K:>8.0f}{n:>5}{cp_str:>7}")


def _print_section_d(all_res, ens_vals) -> None:
    sec_header("D · LEAD TIME vs ENSEMBLE")
    em = float(np.mean(ens_vals)) if ens_vals else np.nan
    print(f"  Ensemble mean = dopy {em:.1f}")
    print("  Lead + = mendahului ensemble  |  Lead − = setelah ensemble")
    print(_rule())

    order = ["M9_Soil", "M4_dVPD", "M7_Td", "M5_CUSUM", "M3_Pett",
             "M1_PELT", "M2_SR", "M6_VPD", "M8_Shear", "M10_BaseU",
             "M11_Lanczos"]
    for m in order:
        vals = [v for yr in all_res for mm, v in all_res[yr].items()
                if mm == m and v is not None]
        if not vals or not np.isfinite(em):
            continue
        lead = em - np.median(vals)
        t = _METHOD_TIER.get(m, 3)
        print(f"  {_METHOD_SHORT[m]:<6}  Lead {lead:>+6.1f} d   Tier {t}")
        note = _METHOD_NOTE.get(m, "")
        if note:
            print(_wrap(note,
                        initial_indent="         · ",
                        subsequent_indent="           "))


def _print_section_e(all_res) -> None:
    sec_header("E · KORELASI INTER-METHOD (Pearson r)")

    yr_list = sorted(all_res.keys())
    series = {m: np.array(
        [all_res[yr].get(m) if yr in all_res else np.nan
         for yr in yr_list], dtype=float)
        for m in _METHODS}
    active = [m for m in _METHODS
              if np.isfinite(series[m]).sum() >= 4]
    if len(active) < 2:
        print("  Tidak cukup data untuk matriks korelasi.")
        return

    # Bagi matriks jadi dua blok kolom agar lebar lega
    mid    = (len(active) + 1) // 2
    blocks = [active[:mid], active[mid:]]

    label_w = 6   # lebar kolom label baris
    col_w   = 7   # lebar kolom nilai (longgar, tidak rapat)

    def _corr(mi: str, mj: str) -> str:
        if mi == mj:
            return "1.00"
        ai, aj = series[mi], series[mj]
        mask = np.isfinite(ai) & np.isfinite(aj)
        if mask.sum() < 3:
            return "—"
        return f"{np.corrcoef(ai[mask], aj[mask])[0, 1]:.2f}"

    print("  Baris = metode sumber; kolom = metode target.")
    print("  Nilai = Pearson r antar dopy deteksi (tahun valid).")
    print()

    for bi, cols in enumerate(blocks):
        title = (f"  ── Blok {bi+1}/{len(blocks)} · kolom "
                 f"{', '.join(_METHOD_SHORT[c] for c in cols)} ──")
        if len(title) > CONSOLE_WIDTH:
            title = title[:CONSOLE_WIDTH - 1] + "…"
        print(title)

        head = ("  " + " " * label_w
                + "".join(f"{_METHOD_SHORT[c]:>{col_w}}" for c in cols))
        print(head)
        print("  " + "─" * (len(head) - 2))

        for mi in active:
            row = f"  {_METHOD_SHORT[mi]:<{label_w}}"
            for mj in cols:
                row += f"{_corr(mi, mj):>{col_w}}"
            print(row)
        print()

    print("  r>0.7 = konsisten  |  0.3–0.7 = moderat  |  "
          "<0.3 = independen")


def _print_section_f(all_res) -> None:
    sec_header("F · KOREKSI ENSEMBLE vs BASELINE (BaseU)")
    print(_rule())

    _ctx_f = _load_enso_context_adv()

    def _f(v):
        return f"{v:>4.0f}" if v else "   —"

    for yr in sorted(all_res.keys()):
        bu = all_res[yr].get("M10_BaseU")
        en = ensemble_vote(all_res[yr])
        lz = all_res[yr].get("M11_Lanczos")
        pl = all_res[yr].get("M1_PELT")
        sr = all_res[yr].get("M2_SR")
        pe = all_res[yr].get("M3_Pett")
        cu = all_res[yr].get("M5_CUSUM")
        d = ((en or 0) - (bu or 0)) if (en and bu) else 0

        ep   = _ctx_f.get(yr, {}).get("enso_phase", "Netral")
        ip   = _ctx_f.get(yr, {}).get("iod_phase",  "Netral")
        iact = _ctx_f.get(yr, {}).get("interaction", "NETRAL")

        print(f"  {yr}  BaseU {_f(bu)} → ENS {_f(en)}  Δ {d:>+4.0f}")
        print(f"        Lancz {_f(lz)}  PELT {_f(pl)}  SR {_f(sr)}  "
              f"Pett {_f(pe)}  CUSU {_f(cu)}")

        # ── Diagnosa v5.4 dengan label fase yang informatif ─────────────
        is_netral_both = (ep == "Netral" and ip == "Netral")

        if is_netral_both and abs(d) > 15:
            note = ("koreksi besar (ENSO Netral/IOD Netral) → "
                    "kemungkinan MJO/cold-surge dominan")
        elif d < -15:
            if ep == "Netral" and ip != "Netral":
                phase_str = f"ENSO Netral/{ip}"
            elif ip == "Netral" and ep != "Netral":
                phase_str = f"{ep}/IOD Netral"
            elif ep != "Netral" and ip != "Netral":
                phase_str = f"{ep}/{ip}"
            else:
                phase_str = ep
            note = (f"koreksi besar ({phase_str})"
                    + (" ×COUNTER" if iact == "COUNTER" else ""))
        elif d < -5:
            note = "koreksi sedang"
        elif abs(d) <= 5:
            note = ("konsisten"
                    + (" ✦sinergi" if iact == "SINERGI" else ""))
        else:
            note = "ensemble lebih lambat"

        print(_wrap(note,
                    initial_indent="        → ",
                    subsequent_indent="          "))
        print()

    # ── Kalimat jembatan ke Section D ────────────────────────────────────
    print(_wrap(
        "Catatan lintas-section: koreksi besar cenderung terkonsentrasi "
        "di tahun-tahun ENSO Netral dengan BaseU di atas P90 "
        "(mis. 2017–2019). Pola ini konsisten dengan lead negatif BaseU "
        "di Section D — BaseU sistematis lebih lambat dari ensemble, "
        "terutama saat tidak ada forcing ENSO/IOD yang kuat.",
        initial_indent="  ",
        subsequent_indent="  "))


def _print_section_g(all_res, ens_vals) -> None:
    sec_header("G · TREN TEMPORAL ENSEMBLE")
    if len(ens_vals) < 3:
        return
    yr_list = sorted(all_res.keys())
    yrs = np.array(yr_list, dtype=float)
    ev = np.array([ensemble_vote(all_res.get(yr, {})) or np.nan
                   for yr in yr_list])
    vld = np.isfinite(ev)
    if vld.sum() < 3:
        return

    slope, _, r, t = _linear_trend(yrs[vld], ev[vld])
    print(f"  Slope    : {slope:+.2f} hari/tahun")
    print(f"  Pearson r: {r:+.3f}")
    print(f"  t-stat   : {t:+.2f}  (df={vld.sum()-2})")
    if abs(t) < 2.26:
        verdict = "Tidak ada tren signifikan (boundary stasioner)."
    else:
        verdict = (f"TREN SIGNIFIKAN — reversal "
                   f"{'mundur' if slope > 0 else 'maju'} "
                   f"{abs(slope):.2f} hr/thn.")
    print()
    print(_wrap(verdict, initial_indent="  Verdict: ",
                subsequent_indent="           "))


def _print_section_h(ens_vals) -> None:
    sec_header("H · ENSEMBLE vs SKENARIO LABUH")
    if not ens_vals:
        return
    er = float(np.median(ens_vals))
    print(f"  Ensemble median : dopy {er:.1f}  "
          f"({_dopy_to_approx_date(2025, er)})")
    print(_rule())
    print(f"  {'Skenario':<10}{'dopy':>8}{'Δ (hr)':>9}  Status")
    print("  " + "─" * 44)
    for sc, val in SCENARIO_LABUH_DOPY.items():
        d = val - er
        status = ("Labuh lebih awal" if d < 0
                  else "Labuh setelah reversal")
        print(f"  {sc:<10}{val:>8.1f}{d:>+9.1f}  {status}")


def _print_section_i() -> None:
    sec_header("I · METODE & REFERENSI ILMIAH")

    _print_wrapped_block(f"""
  TIER 1 — CHANGE-POINT & FILTER BERKALIBER INTERNASIONAL
  ──────────────────────────────────────────────────────
  M1   PELT — Killick, Fearnhead & Eckley (2012),
       JASA 107(500):1590–1598. Deteksi titik ganti optimal
       dengan biaya komputasi linear pada MPCI daily.
  M2   Shiryaev-Roberts — Pollak (1985), Ann. Stat. 13(1):206–227.
       Statistik likelihood-ratio kumulatif dengan threshold
       adaptif A = 0.5/λ.
  M11  Lanczos zero-phase — Duchon (1979), J. Appl. Meteor.
       18(8):1016–1022. Windowed-sinc low-pass {LANCZOS_WINDOW} hr,
       cutoff {LANCZOS_CUTOFF_DAYS:.0f} hr, konvolusi mode='same'
       (zero phase-shift). Ambang recovery
       {U_RECOVERY_FRACTION*100:.0f}% amplitudo musiman.
       Gerbang MJO — Wheeler & Hendon (2004), Mon. Wea. Rev.
       132(8):1917–1932. RMM amp ≥ {RMM_AMP_THRESHOLD} memblokir
       kandidat crossing.

  TIER 2 — STATISTIK STANDAR HIDROKLIMATOLOGI
  ───────────────────────────────────────────
  M3   Pettitt non-parametrik — Pettitt (1979),
       JRSS-C 28(2):126–135.
  M4   Slope VPD 7-hari dengan threshold adaptif μ−2σ.
  M5   CUSUM — Page (1954), Biometrika 41:100–115.

  TIER 3 — PRECURSOR FISIK & BASELINE
  ───────────────────────────────────
  M6   VPD level rendah (< 65% median kering).
  M7   Titik embun tinggi (> P97 kering).
  M8   Shear vertikal 10m↔100m crossing nol.
  M9   Soil moisture (> P80 kering).
  M10  u_comp 30-hari rolling > 0 (baseline EV09wind).

  KONVENSI FASE
  ─────────────
      u_comp = −sin(wd10)     v_comp = −cos(wd10)
      wd = atan2(u, v) + 180° (mod 360°)
      Verifikasi — angin barat murni (wd10 = 270°):
          u = +1, v = 0, atan2(1,0) = 90°, +180° = 270°  ✓
""")


def _print_section_j(all_res: Dict[int, Dict],
                     ens_vals: List[float]) -> None:
    """Section J · Anotasi ENSO × IOD pada monsoon reversal (v5.4)."""
    sec_header("J · ANOTASI ANOMALI ENSO × IOD — MONSOON REVERSAL")

    print("  Memuat data ENSO/IOD...")
    ctx = _load_enso_context_adv()

    has_any = any(
        ctx[py].get("sst_aso") is not None
        or ctx[py].get("dmi_son") is not None
        for py in ctx
    )
    if not has_any:
        print("  [!] File ENSO/IOD tidak ditemukan. Letakkan file")
        print("      berikut di direktori yang sama dengan skrip ini:")
        for fn in (_ENSO_SST_CSV, _ENSO_MSLA_CSV,
                   _IOD_WEEKLY, _IOD_MONTHLY):
            print(f"        · {fn}")
        return

    med_ens   = float(np.median(ens_vals)) if ens_vals else float("nan")
    sigma_ens = (float(np.std(ens_vals, ddof=1))
                 if len(ens_vals) > 1 else 0.0)

    print()
    print(f"  Ensemble median = dopy {med_ens:.1f}  "
          f"({_dopy_to_approx_date(2025, med_ens) if np.isfinite(med_ens) else '—'})")
    print(f"  Ensemble σ      = {sigma_ens:.1f} hari  "
          f"(batas anomali: ±{_ANOMALY_SIGMA * sigma_ens:.1f} hari)")
    print()

    # ── Tabel utama ──────────────────────────────────────────────────────
    print(f"  {'Thn':<5}{'SST_ASO':>9}{'SLA_ASO':>9}{'DMI_SON':>9}"
          f"  {'ENSO':<7}{'IOD':<6}{'Rev':>6}{'Δmed':>7}")
    print("  " + "─" * 60)

    def _ff(v):
        if v is None or not np.isfinite(float(v)):
            return f"{'—':>9}"
        return f"{float(v):>+9.3f}"

    for py in range(2015, 2027):
        c   = ctx.get(py, {})
        res = all_res.get(py, {})
        ens = ensemble_vote(res) if res else None

        sst = c.get("sst_aso")
        sla = c.get("sla_aso")
        dmi = c.get("dmi_son")
        ep  = c.get("enso_phase", "—")
        ip  = c.get("iod_phase", "—")

        ep_short = ("ElNino" if ep == "El Niño"
                    else "LaNina" if ep == "La Niña" else "Netral")

        delta_s = "—"
        if ens is not None and np.isfinite(med_ens):
            delta_s = f"{ens - med_ens:>+7.1f}"

        ens_s = f"{ens:>6.0f}" if ens is not None else f"{'—':>6}"

        print(f"  {py:<5}{_ff(sst)}{_ff(sla)}{_ff(dmi)}"
              f"  {ep_short:<7}{ip:<6}{ens_s}{delta_s:>7}")

        flag = _anomaly_flag_adv(c, ens, med_ens, sigma_ens)
        if flag and flag != "—":
            print(_wrap(flag,
                        initial_indent="        ↳ Iklim: ",
                        subsequent_indent="                 "))

    # ── Interpretasi interaksi ───────────────────────────────────────────
    sec_header("J2 · INTERPRETASI INTERAKSI ENSO × IOD")

    _print_wrapped_block("""
  Tiga pola interaksi dan dampaknya pada monsoon reversal.

  SINERGI — El Niño + pIOD  atau  La Niña + nIOD
  ──────────────────────────────────────────────
  Kedua osilasi mendorong sinyal ke arah yang sama.

    · El Niño + pIOD: musim kering lebih panjang, reversal
      terlambat, sinyal u_comp melemah → estimator Lanczos (M11)
      berpotensi lebih lambat dari ensemble.

    · La Niña + nIOD: reversal lebih awal, sinyal kuat, semua
      estimator cenderung konvergen.

  Sifat penting yang perlu dibaca hati-hati: sinergi kuat TIDAK
  selalu berarti simpangan besar dari median. Bisa juga muncul
  sebagai konvergensi antar-estimator pada posisi median (varians
  rendah). Baca kolom Δmed bersama lebar sebaran M1–M11 untuk
  membedakan kedua situasi.

  COUNTER — El Niño + nIOD  atau  La Niña + pIOD
  ──────────────────────────────────────────────
  Kedua osilasi saling bertentangan sehingga hasil tidak mengikuti
  prediksi linier sederhana. ENSO dan IOD mendorong anomali angin
  zonal di atas Jawa ke arah berlawanan, sehingga konvergensi
  kelembapan dan waktu reversal dapat menyimpang dari prediksi
  salah satu osilasi saja. Tahun-tahun COUNTER yang teridentifikasi
  ditampilkan pada tabel J di atas; arah penyimpangan (maju atau
  mundur) dibaca dari kolom Δmed bersama flag ⚠COUNTER.

  NETRAL — ENSO dan/atau IOD lemah
  ────────────────────────────────
  Salah satu atau keduanya lemah. Reversal mendekati median
  klimatologis. Variabilitas yang dominan berasal dari dinamika
  internal atmosfer: MJO (30–60 hari), cold surge dari daratan
  Asia, gelombang Kelvin/Rossby ekuator, atau siklon tropis.
""")

    counter_years = [py for py in range(2015, 2027)
                     if ctx.get(py, {}).get("interaction") == "COUNTER"]
    synergy_years = [py for py in range(2015, 2027)
                     if ctx.get(py, {}).get("interaction") == "SINERGI"]

    if counter_years:
        print(f"  Tahun COUNTER teridentifikasi: {counter_years}")
        print(_wrap(
            "Estimator ensemble mungkin menyebar lebar pada tahun "
            "ini; periksa konsistensi M1–M11 di Section A.",
            initial_indent="  → ",
            subsequent_indent="    "))
    if synergy_years:
        print()
        print(f"  Tahun SINERGI teridentifikasi: {synergy_years}")
        print(_wrap(
            "Sinyal biasanya lebih kuat; konsistensi inter-estimator "
            "umumnya tinggi.",
            initial_indent="  → ",
            subsequent_indent="    "))

    print()
    print("  ⚠ = anomali aktif (COUNTER kuat + reversal > 1.5σ "
          "dari median)")
    print("  ✦ = sinergi kuat (ENSO + IOD searah, ≥ threshold kuat)")
    print(f"  Threshold 'kuat' (simetris): |SST_ASO| ≥ "
          f"{_ANOMALY_SST_STR} DAN |DMI_SON| ≥ {_ANOMALY_DMI_STR}")


def report() -> None:
    """Hasilkan laporan lengkap."""
    print_header(
        "DETEKSI MONSOON REVERSAL — v5.4",
        "PELT · SR · Pettitt · dVPD · CUSUM + Lanczos-RMM (M11)"
        " + Ensemble + ENSO×IOD",
    )
    df = load_rich_hourly()
    if df is None:
        return

    _print_lanczos_characteristics()

    all_res: Dict[int, Dict[str, Optional[float]]] = {}
    ens_vals: List[float] = []

    print()
    print("  Menjalankan M1–M11 untuk 2015–2026...")
    for py in range(2015, 2027):
        res = run_all(df, py)
        if not res:
            continue
        all_res[py] = res
        ens = ensemble_vote(res)
        if ens:
            ens_vals.append(ens)

    _print_section_a(all_res, ens_vals)
    _print_section_b(all_res, ens_vals)
    _print_section_c(all_res)
    _print_section_d(all_res, ens_vals)
    _print_section_e(all_res)
    _print_section_f(all_res)
    _print_section_g(all_res, ens_vals)
    _print_section_h(ens_vals)
    _print_section_i()
    _print_section_j(all_res, ens_vals)


# ══════════════════════════════════════════════════════════════════════════
# Section 14 · Entry point
# ══════════════════════════════════════════════════════════════════════════

def main() -> int:
    report()
    return 0


if __name__ == "__main__":
    sys.exit(main())