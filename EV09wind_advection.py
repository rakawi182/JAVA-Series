#!/usr/bin/env python3
"""
EV09wind_adveksi.py — Analisis Adveksi Awan Baratan
=====================================================
Versi 1.0.1  |  Jolotundo Research Observatory · MJS
Titik pengamatan: −7.5220°LS, 112.5661°BT, 28 m dpl, Jawa Timur

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
APA YANG DIUKUR MODUL INI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modul ini BUKAN tentang "kapan baratan mulai" — itu domain modul
EV09_BPI.py (onset BPI). Modul ini menjawab pertanyaan lain:

  "Kapan awan bergerak MASIF dari barat, siang dan malam, dengan
   kecepatan konstan — meskipun tidak selalu hujan?"

Fenomena ini berbeda dari onset baratan:

  · Onset baratan (BPI)   : dopy ~128  (28 Okt)  — langit menutup
  · Adveksi awan stabil   : dopy ~215  (3 Feb)   — awan mengalir barat
  · Selisih               : ~87 hari (≈ 3 bulan)

  Onset baratan  = efek radiatif (cloud, SW, tcwv, VPD).
  Adveksi stabil = dinamik (u_mean, u_std, frac_west, cl_night).

Keduanya fenomena berbeda dalam siklus baratan yang sama.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KALIBRASI THRESHOLD — dari data EV09 2015–2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Diagnostik SWA v2 (probe distribusi) + evaluasi v1.0.0:

  Bulan    u_mean   frac_west   u_std   cl_night   cloud
  ────────────────────────────────────────────────────────
  Jan      +0.46     0.75       0.44    95.0       92.7
  Feb      +0.50     0.79       0.42    93.9       90.6

  Profil Jan-Feb (bin 5-hari):
    dopy 220   u=+0.70   u_std=0.34   frac_west=0.89
    dopy 225   u=+0.70   u_std=0.32   frac_west=0.90   ← puncak

  Persentil Des-Jan-Feb:
    DRY P50 / P90  →  WET P10 / P50 / P90
    u_mean   :  −0.30 / +0.07  →  −0.24 / +0.45 / +0.95
    frac_west:   0.38 /  0.58  →   0.38 /  0.79 /  1.00
    u_std    :   0.66 /  0.79  →   0.05 /  0.57 /  0.77
    cl_night :  49.28 / 89.86  →  81.86 / 98.54 / 100.0
    cloud    :  49.63 / 85.40  →  75.95 / 96.06 /  99.93

  Puncak adveksi per tahun (median):  31 Januari
  Rentang tipikal:                    25 Jan – 17 Feb

  Evaluasi v1.0.0 (AND-gate murni): hanya menangkap 4 dari 11 tahun.
  Penyebab: menuntut 5 kondisi bertemu 70% dari 14 hari. Tahun dengan
  El Niño lemah (2019) atau awan malam <94% (2018) gagal total.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REVISI v1.0.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. A1_WCA: AND-gate biner → SKOR 0–5, threshold rata-rata 14d ≥ 4.0
     Alasan: AND-gate terlalu rapuh — satu kondisi gagal = onset kosong.
     Skor 4/5 masih mencerminkan adveksi stabil tanpa menuntut
     kelima indikator sempurna.
  2. A3_NIGHT: tambah filter u_mean > 0.30
     Alasan: v1.0.0 memicu di dopy 150–163 (Oktober), jauh sebelum
     adveksi stabil. Filter angin menyaring "langit tertutup musim
     hujan" dari "awan bergerak dari barat".
  3. WCA_CL_NIGHT_THR: 94.0 → 90.0
     Alasan: tahun 2018 punya cl_night peak 90.2% — sudah jelas
     awan malam tebal, tapi tertolak oleh threshold 94.
  4. Report profile: label "AND-gate" diganti "skor komposit"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRUKTUR ANALISIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  §1   Konstanta & parameter
  §2   Loader (reuse dari EV09_BPI)
  §3   Fitur adveksi harian (daily)
  §4   WCA Index — Steady Westward Cloud Advection composite
  §5   Estimator A1, A2, A3 (independen)
  §6   Ensemble (Biweight Tukey)
  §7   Runner per pranata-tahun
  §8   Perbandingan dengan onset BPI (baratan)
  §9   Sub-fase Plateau 3a / 3b (untuk lifecycle baratan)
  §10  Statistik multi-tahun
  §11  Report generators (A–E)
  §12  CLI

Referensi
  · Wallace & Hobbs (2006) Atmospheric Science, 2nd ed.
  · Holton & Hakim (2013) An Introduction to Dynamic Meteorology
  · Houze (2014) Cloud Dynamics, 2nd ed. — stratiform advection
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from EV09wind import (
        ANCHOR_MONTH, ANCHOR_DAY, W,
        print_header, sec_header,
        box_top, box_bot, box_row, box_mid,
        thin_hbar, _dopy_to_approx_date, _linear_trend,
        MONTH_SHORT,
    )
    from EV09_BPI import (
        load_baratan_data,
        compute_bpi, run_year,
        _daily_field, _attach_dopy, _crossing_persistent,
        ensemble_baratan,
        BAR_ONSET_LO, BAR_ONSET_HI,
        BAR_OFFSET_LO, BAR_OFFSET_HI,
        DRY_LO, DRY_HI,
        SUSTAIN, SUSTAIN_MIN, EPS,
    )
except ImportError as e:
    print(f"[!] Import gagal: {e}")
    print("    Pastikan EV09wind.py & EV09_BPI.py ada di folder yang sama.")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════
# §1  Konstanta & parameter fisis
# ══════════════════════════════════════════════════════════════════════════

# ── Window deteksi adveksi (dopy = hari sejak anchor 22 Juni) ────────────
# Adveksi stabil terjadi Des–Feb. Window onset diperlebar untuk menangkap
# tahun yang lebih awal (2016: puncak 18 Des).
ADV_ONSET_LO    = 150.0   # ~19 Des
ADV_ONSET_HI    = 260.0   # ~8 Mar
ADV_OFFSET_LO   = 240.0
ADV_OFFSET_HI   = 320.0
ADV_PEAK_LO     = 180.0
ADV_PEAK_HI     = 260.0

# ── Threshold komponen WCA (dikalibrasi dari DIAG v2) ────────────────────
# Nilai di bawah adalah puncak adveksi Jan-Feb, bukan rata-rata bulanan.
WCA_U_MEAN_THR      = 0.65   # unit-vector   — u_comp rolling 7d
WCA_U_STD_THR       = 0.35   # unit-vector   — std harian u_comp rolling 7d
WCA_FRAC_WEST_THR   = 0.85   # fraksi jam u_comp > 0 rolling 7d
WCA_CL_NIGHT_THR    = 90.0   # %      — cloud malam (22–04) rolling 7d
                             #          v1.0.1: turun dari 94 → 90 agar
                             #          tahun El Niño lemah (2018) tidak gagal
WCA_CLOUD_THR       = 90.0   # %      — cloud total rolling 7d

# ── A1_WCA scoring (v1.0.1 — ganti AND-gate) ─────────────────────────────
# Skor 0–5 = jumlah kondisi terpenuhi per hari.
# Onset = rata-rata skor 14d ≥ WCA_SCORE_THR.
WCA_SCORE_THR       = 4.0

# ── Threshold A2 (wind-only, fallback untuk awan lemas) ──────────────────
WIND_U_MEAN_THR     = 0.70
WIND_FRAC_WEST_THR  = 0.90

# ── Threshold A3 (cloud-night-only, fallback untuk angin lemas) ──────────
# v1.0.1: ditambah filter u_mean > 0.30 agar tidak memicu saat labuh awal.
NIGHT_CL_THR        = 95.0
NIGHT_CLOUD_THR     = 92.0
NIGHT_U_MEAN_THR    = 0.30

# Persistence requirement (dipakai di _wca_score_signal & estimator lain)
ADV_SUSTAIN         = 14     # hari — window rolling sinyal
ADV_SUSTAIN_MIN     = 10     # min valid dalam window

# ── A1_WCA sustain requirement (relaksasi v1.0.2) ────────────────────────
# v1.0.1: sust=14, sust_min=10 → terlalu ketat; tahun dengan puncak
#         osilatif (2015, 2018, 2021) gagal terdeteksi.
# v1.0.2: sust=10, sust_min=6 → toleran terhadap dip sesaat tanpa
#         kehilangan spesifisitas.
A1_SUSTAIN      = 10
A1_SUSTAIN_MIN  = 6

# ── Ensemble bobot (A1 lebih spesifik karena kombinasi 5 indikator) ──────
ENS_W_ADV: Dict[str, float] = {
    "A1_WCA":   3.0,
    "A2_WIND":  1.5,
    "A3_NIGHT": 1.5,
}

# ── Sub-fase Plateau (untuk lifecycle baratan §4b) ────────────────────────
# 3a Saturasi : dopy 160–215, u_std 0.4–0.5, u_mean +0.3–0.5
# 3b Adveksi  : dopy 215–240, u_std < 0.35, u_mean > 0.65
SUB_PHASE_3A_LO = 160.0
SUB_PHASE_3A_HI = 215.0
SUB_PHASE_3B_LO = 215.0
SUB_PHASE_3B_HI = 240.0

# ── Cache global ──────────────────────────────────────────────────────────
_ADV_FEAT_CACHE: Optional[pd.DataFrame] = None


# ══════════════════════════════════════════════════════════════════════════
# §2  Loader — reuse dari EV09_BPI
# ══════════════════════════════════════════════════════════════════════════

def load_advection_data() -> Optional[pd.DataFrame]:
    """
    Load data hourly. Wrapper ke load_baratan_data — cache terpisah
    di modul baratan tidak masalah karena sifatnya read-only.
    """
    return load_baratan_data()


# ══════════════════════════════════════════════════════════════════════════
# §3  Fitur adveksi harian (daily)
# ══════════════════════════════════════════════════════════════════════════

def _daily_advection(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Agregasi harian fitur adveksi:

      · u_mean    — u_comp harian rata-rata (unit-vector)
      · u_std     — std u_comp harian (unit-vector) — ukuran "konstansi angin"
      · frac_west — fraksi jam dengan u_comp > 0 (indikator arah dominan)
      · cl_night  — cloud rata-rata jam 22–04 lokal (awan malam)
      · cl_day    — cloud rata-rata jam 10–16 lokal (awan siang)
      · cloud     — cloud total harian
      · tcwv      — kolom uap air harian
      · sw_rad    — radiasi harian
      · flux      — u_mean × tcwv (westward moisture flux proxy)

    Return DataFrame dengan kolom: date, dopy, + field di atas.
    """
    needed = {"u_comp", "cloud", "tcwv", "sw_rad"}
    if not needed.issubset(df.columns):
        return None

    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    d["_hour"] = pd.to_datetime(d["time"]).dt.hour
    d["_u_pos"] = (d["u_comp"] > 0).astype(float)

    # Split night vs day
    night_mask = d["_hour"].isin([22, 23, 0, 1, 2, 3, 4])
    day_mask   = d["_hour"].isin([10, 11, 12, 13, 14, 15])

    g = d.groupby("_date")
    n = d[night_mask].groupby("_date")["cloud"].mean()
    a = d[day_mask].groupby("_date")["cloud"].mean()

    out = pd.DataFrame({
        "u_mean":    g["u_comp"].mean(),
        "u_std":     g["u_comp"].std(),
        "frac_west": g["_u_pos"].mean(),
        "cloud":     g["cloud"].mean(),
        "tcwv":      g["tcwv"].mean(),
        "sw_rad":    g["sw_rad"].mean(),
    }).reset_index().rename(columns={"_date": "date"})

    out["cl_night"] = out["date"].map(n)
    out["cl_day"]   = out["date"].map(a)
    out["flux"]     = out["u_mean"] * out["tcwv"]

    out = out.sort_values("date").reset_index(drop=True)
    out = _attach_dopy(out, dc="date")
    return out


def _get_advection_features(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Cache global fitur adveksi."""
    global _ADV_FEAT_CACHE
    if _ADV_FEAT_CACHE is None:
        _ADV_FEAT_CACHE = _daily_advection(df)
    return _ADV_FEAT_CACHE


def _roll_daily(a: pd.DataFrame, col: str, win: int = 7,
                causal: bool = False) -> np.ndarray:
    """Rolling mean kolom tertentu di DataFrame adveksi harian."""
    if causal:
        r = a[col].rolling(win, min_periods=win // 2).mean()
    else:
        r = a[col].rolling(win, center=True, min_periods=win // 2).mean()
    return r.values


# ══════════════════════════════════════════════════════════════════════════
# §4  WCA Index & tiga estimator (A1, A2, A3)
# ══════════════════════════════════════════════════════════════════════════

def _year_slice(a: pd.DataFrame, py: int) -> pd.DataFrame:
    start = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
    end   = start + pd.Timedelta(days=365)
    return a[(a["date"] >= start) & (a["date"] < end)].copy().reset_index(drop=True)


def _wca_score_signal(a: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    WCA score — jumlah kondisi terpenuhi (0–5), bukan AND-gate biner.

    Skor dihitung per hari setelah smoothing rolling 7d:
      +1 jika u_mean    > WCA_U_MEAN_THR
      +1 jika u_std     < WCA_U_STD_THR
      +1 jika frac_west > WCA_FRAC_WEST_THR
      +1 jika cl_night  > WCA_CL_NIGHT_THR
      +1 jika cloud     > WCA_CLOUD_THR

    Skor 0 = tidak ada indikator adveksi
    Skor 5 = kelima indikator memenuhi (adveksi sempurna)

    Return (rolling mean 14d dari skor, dopy).

    Keunggulan vs AND-gate (v1.0.0):
      · Tidak rapuh terhadap satu kondisi yang gagal sesaat
      · Tahan terhadap tahun dengan satu indikator di batas (misal
        cl_night = 90.2% di tahun 2018)
      · Threshold dapat disetel halus (4.0, 4.2, 4.5) tanpa mengubah
        struktur deteksi
    """
    u_mean_r    = _roll_daily(a, "u_mean",   win=7)
    u_std_r     = _roll_daily(a, "u_std",    win=7)
    frac_west_r = _roll_daily(a, "frac_west",win=7)
    cl_night_r  = _roll_daily(a, "cl_night", win=7)
    cloud_r     = _roll_daily(a, "cloud",    win=7)

    score = (
        (u_mean_r    > WCA_U_MEAN_THR).astype(float)
        + (u_std_r     < WCA_U_STD_THR).astype(float)
        + (frac_west_r > WCA_FRAC_WEST_THR).astype(float)
        + (cl_night_r  > WCA_CL_NIGHT_THR).astype(float)
        + (cloud_r     > WCA_CLOUD_THR).astype(float)
    )
    valid = (np.isfinite(u_mean_r) & np.isfinite(u_std_r)
             & np.isfinite(frac_west_r) & np.isfinite(cl_night_r)
             & np.isfinite(cloud_r))
    score = np.where(valid, score, np.nan)

    sig = pd.Series(score).rolling(ADV_SUSTAIN,
                                    min_periods=ADV_SUSTAIN_MIN).mean().values
    return sig, a["dopy"].values


def _wind_joint_signal(a: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """A2 — hanya dari angin (fallback untuk awan lemas)."""
    u_mean_r    = _roll_daily(a, "u_mean",   win=7)
    frac_west_r = _roll_daily(a, "frac_west",win=7)

    cond = (u_mean_r > WIND_U_MEAN_THR) & (frac_west_r > WIND_FRAC_WEST_THR)
    valid = np.isfinite(u_mean_r) & np.isfinite(frac_west_r)
    joint = np.where(valid, cond.astype(float), np.nan)

    sig = pd.Series(joint).rolling(21, min_periods=14).mean().values
    return sig, a["dopy"].values


def _night_joint_signal(a: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    A3 — cloud malam tebal + sedikit angin barat.

    v1.0.1: ditambah filter u_mean > 0.30 agar TIDAK memicu di musim
    hujan awal (Okt–Nov) saat langit menutup tapi angin belum barat.
    """
    cl_night_r = _roll_daily(a, "cl_night", win=7)
    cloud_r    = _roll_daily(a, "cloud",    win=7)
    u_mean_r   = _roll_daily(a, "u_mean",   win=7)  # ← filter baru

    cond = (
        (cl_night_r > NIGHT_CL_THR)
        & (cloud_r  > NIGHT_CLOUD_THR)
        & (u_mean_r > NIGHT_U_MEAN_THR)   # ← wind gate
    )
    valid = (np.isfinite(cl_night_r) & np.isfinite(cloud_r)
             & np.isfinite(u_mean_r))
    joint = np.where(valid, cond.astype(float), np.nan)

    sig = pd.Series(joint).rolling(ADV_SUSTAIN,
                                    min_periods=ADV_SUSTAIN_MIN).mean().values
    return sig, a["dopy"].values


def detect_onset_wca(a_yr: pd.DataFrame) -> Optional[float]:
    """
    A1 — WCA composite score-based.

    Onset = hari pertama rata-rata skor 14d ≥ WCA_SCORE_THR (4.0).

    v1.0.2: sustain dilonggarkan dari 14/10 ke 10/6 agar tahun dengan
    puncak osilatif (2015 peak 4.79, 2018 peak 4.50, 2021 peak 4.29)
    tetap terdeteksi. Toleransi ini tidak melemahkan spesifisitas karena
    tahun El Niño ekstrem (2019 peak 3.50, 2023 peak 2.00) tetap di
    bawah threshold.
    """
    sig, dpy = _wca_score_signal(a_yr)
    return _crossing_persistent(sig, dpy, thr=WCA_SCORE_THR, up=True,
                                lo=ADV_ONSET_LO, hi=ADV_ONSET_HI,
                                sust=A1_SUSTAIN, sust_min=A1_SUSTAIN_MIN)


def detect_onset_wind(a_yr: pd.DataFrame) -> Optional[float]:
    """A2 — Wind-only onset."""
    sig, dpy = _wind_joint_signal(a_yr)
    return _crossing_persistent(sig, dpy, thr=0.75, up=True,
                                lo=ADV_ONSET_LO, hi=ADV_ONSET_HI,
                                sust=21, sust_min=14)


def detect_onset_night(a_yr: pd.DataFrame) -> Optional[float]:
    """A3 — Cloud-night-only onset (dengan filter angin v1.0.1)."""
    sig, dpy = _night_joint_signal(a_yr)
    return _crossing_persistent(sig, dpy, thr=0.70, up=True,
                                lo=ADV_ONSET_LO, hi=ADV_ONSET_HI,
                                sust=ADV_SUSTAIN, sust_min=ADV_SUSTAIN_MIN)


def detect_offset_wca(a_yr: pd.DataFrame) -> Optional[float]:
    """A1 — offset ketika angin melemah atau awan malam menipis."""
    u_mean_r    = _roll_daily(a_yr, "u_mean",   win=7)
    u_std_r     = _roll_daily(a_yr, "u_std",    win=7)
    cl_night_r  = _roll_daily(a_yr, "cl_night", win=7)

    cond = (u_mean_r < 0.30) | (cl_night_r < 85.0)
    valid = (np.isfinite(u_mean_r) & np.isfinite(u_std_r)
             & np.isfinite(cl_night_r))
    joint = np.where(valid, cond.astype(float), np.nan)

    sig = pd.Series(joint).rolling(ADV_SUSTAIN,
                                    min_periods=ADV_SUSTAIN_MIN).mean().values
    return _crossing_persistent(sig, a_yr["dopy"].values,
                                thr=0.55, up=True,
                                lo=220.0, hi=ADV_OFFSET_HI,
                                sust=A1_SUSTAIN, sust_min=A1_SUSTAIN_MIN)


# ══════════════════════════════════════════════════════════════════════════
# §5  Ensemble
# ══════════════════════════════════════════════════════════════════════════

def ensemble_advection(results: Dict[str, Optional[float]]) -> Optional[float]:
    """
    Ensemble biweight — reuse fungsi dari baratan.

    min_n=1 karena A1_WCA berbobot 3.0 dari total 6.0 (>50%).
    Saat A2 & A3 gagal (misal tahun 2018), A1 sendirian tetap
    dianggap sahih — 5-kondisi WCA terpenuhi secara konsisten.
    """
    return ensemble_baratan(results, ENS_W_ADV, min_n=1)


# ══════════════════════════════════════════════════════════════════════════
# §6  Runner per pranata-tahun
# ══════════════════════════════════════════════════════════════════════════

def run_year_advection(df: pd.DataFrame, py: int,
                       a_all: pd.DataFrame) -> Dict:
    """
    Deteksi onset adveksi untuk satu pranata-tahun.

    Return dict:
      onset_ens, offset_ens, duration, peak_dopy, peak_wca,
      onset_raw (dict A1/A2/A3), offset_raw
    """
    a_yr = _year_slice(a_all, py)
    if len(a_yr) < 180:
        return {}

    on_res = {
        "A1_WCA":   detect_onset_wca(a_yr),
        "A2_WIND":  detect_onset_wind(a_yr),
        "A3_NIGHT": detect_onset_night(a_yr),
    }
    onset_ens = ensemble_advection(on_res)

    off_res = {
        "A1_WCA": detect_offset_wca(a_yr),
    }
    offset_ens = ensemble_advection(off_res) if any(
        v is not None for v in off_res.values()) else None

    dur = None
    if onset_ens is not None and offset_ens is not None:
        d = offset_ens - onset_ens
        if d >= 0:
            dur = d

    # Peak WCA score: dopy dengan skor tertinggi di window peak
    sig_wca, _ = _wca_score_signal(a_yr)
    mask_peak = ((a_yr["dopy"] >= ADV_PEAK_LO)
                 & (a_yr["dopy"] <= ADV_PEAK_HI)
                 & np.isfinite(sig_wca))
    if mask_peak.any():
        idx = np.where(mask_peak)[0]
        best = idx[int(np.argmax(sig_wca[idx]))]
        peak_dopy = float(a_yr["dopy"].iloc[best])
        peak_wca  = float(sig_wca[best])
    else:
        peak_dopy, peak_wca = float("nan"), float("nan")

    return {
        "onset_ens":  onset_ens,
        "offset_ens": offset_ens,
        "duration":   dur,
        "peak_dopy":  peak_dopy,
        "peak_wca":   peak_wca,
        "onset_raw":  on_res,
        "offset_raw": off_res,
    }


# ══════════════════════════════════════════════════════════════════════════
# §7  Perbandingan dengan onset BPI (baratan)
# ══════════════════════════════════════════════════════════════════════════

def comparison_table(df: pd.DataFrame) -> List[Dict]:
    """
    Bandingkan onset adveksi (WCA) vs onset baratan (BPI) per tahun.
    Return list of dict dengan kolom: py, onset_bpi, onset_wca, lag.
    """
    a_all = _get_advection_features(df)
    if a_all is None:
        return []
    bpi_all = compute_bpi(df)
    if bpi_all is None:
        return []

    rows: List[Dict] = []
    for py in range(2015, 2027):
        on_bpi = run_year(df, py, bpi_all).get("onset_ens")
        adv    = run_year_advection(df, py, a_all)
        on_wca = adv.get("onset_ens")
        lag    = None
        if on_bpi is not None and on_wca is not None:
            lag = float(on_wca) - float(on_bpi)
        rows.append({
            "py":        py,
            "onset_bpi": on_bpi,
            "onset_wca": on_wca,
            "lag":       lag,
        })
    return rows


# ══════════════════════════════════════════════════════════════════════════
# §8  Sub-fase Plateau 3a / 3b (untuk lifecycle baratan)
# ══════════════════════════════════════════════════════════════════════════

def sub_phase_profile(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Statistik komposit untuk dua sub-fase Plateau:

      3a Saturasi  (dopy 160–215) : u_mean +0.3–0.5, u_std 0.4–0.5
      3b Adveksi   (dopy 215–240) : u_mean > 0.65, u_std < 0.35

    Return dict: {sub_phase_name: {field: mean}}
    """
    a = _get_advection_features(df)
    if a is None:
        return {}

    fields = ["u_mean", "u_std", "frac_west", "cl_night",
              "cl_day", "cloud", "sw_rad", "tcwv", "flux"]

    out: Dict[str, Dict] = {}
    phases = (
        ("3a_Saturasi", SUB_PHASE_3A_LO, SUB_PHASE_3A_HI),
        ("3b_Adveksi",  SUB_PHASE_3B_LO, SUB_PHASE_3B_HI),
    )
    for (name, lo, hi) in phases:
        sub = a[(a["dopy"] >= lo) & (a["dopy"] <= hi)]
        rec: Dict[str, float] = {"n_days": int(len(sub))}
        for f in fields:
            v = sub[f].dropna()
            rec[f] = float(v.mean()) if len(v) else float("nan")
        out[name] = rec
    return out


# ══════════════════════════════════════════════════════════════════════════
# §9  Statistik multi-tahun
# ══════════════════════════════════════════════════════════════════════════

def multiyr_stats_advection(records: List[Dict]) -> Dict[str, Dict]:
    keys = ["onset_ens", "offset_ens", "duration", "peak_dopy", "peak_wca"]
    out: Dict[str, Dict] = {}
    for k in keys:
        vals = []
        for r in records:
            v = r.get(k)
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals.append(fv)
        arr = np.array(vals, dtype=float)
        if len(arr) < 2:
            out[k] = {"n": len(arr)}
            continue
        slope, intercept, r_val, t_val = _linear_trend(
            np.arange(len(arr), dtype=float), arr)
        out[k] = {
            "n": len(arr),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std": float(np.std(arr, ddof=1)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "slope": float(slope),
            "r": float(r_val),
            "t": float(t_val),
        }
    return out


# ══════════════════════════════════════════════════════════════════════════
# §10  Report generators
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


def report_profile(df: pd.DataFrame) -> None:
    print_header(
        "PROFIL ADVESI AWAN — SIKLUS TAHUNAN",
        "EV09wind_adveksi v1.0.1 · Westward Cloud Advection (WCA)"
    )

    a = _get_advection_features(df)
    if a is None:
        print("  [!] Fitur adveksi tidak dapat dihitung.")
        return

    print()
    print("  Empat indikator inti:")
    print("    u_mean    — u_comp rata-rata harian (unit-vector)")
    print("    u_std     — std harian u_comp (kecil = stabil)")
    print("    frac_west — fraksi jam dengan u_comp > 0")
    print("    cl_night  — cloud malam 22–04 lokal (%)")
    print()

    sec_header("A · RATA-RATA PER BULAN")

    print(f"  {'Bln':<5}{'u_mean':>9}{'u_std':>8}{'frac_west':>11}"
          f"{'cl_night':>10}{'cl_day':>9}{'cloud':>8}{'SW':>8}{'flux':>9}")
    print("  " + "─" * (5 + 9 + 8 + 11 + 10 + 9 + 8 + 8 + 9))

    for m in range(1, 13):
        sub = a[a["date"].dt.month == m]
        if len(sub) < 5:
            continue
        print(f"  {MONTH_SHORT[m]:<5}"
              f"{sub['u_mean'].mean():>+9.2f}"
              f"{sub['u_std'].mean():>8.2f}"
              f"{sub['frac_west'].mean():>11.2f}"
              f"{sub['cl_night'].mean():>10.1f}"
              f"{sub['cl_day'].mean():>9.1f}"
              f"{sub['cloud'].mean():>8.1f}"
              f"{sub['sw_rad'].mean():>8.1f}"
              f"{sub['flux'].mean():>+9.2f}")

    sec_header("B · PROFIL 5-HARI — WINDOW ONSET/OFFSET ADVESI")

    win = a[(a["dopy"] >= ADV_PEAK_LO) & (a["dopy"] <= ADV_PEAK_HI + 20)].copy()
    if len(win) < 50:
        print("  [!] Data window tidak cukup.")
        return
    win["bin"] = (win["dopy"] // 5 * 5).astype(int)

    print(f"  {'dopy':>6}{'u_mean':>9}{'u_std':>8}{'frac_west':>11}"
          f"{'cl_night':>10}{'cloud':>8}{'SW':>8}")
    print("  " + "─" * 60)

    for b in sorted(win["bin"].unique()):
        sub = win[win["bin"] == b]
        if len(sub) < 5:
            continue
        print(f"  {b:>6}"
              f"{sub['u_mean'].mean():>+9.2f}"
              f"{sub['u_std'].mean():>8.2f}"
              f"{sub['frac_west'].mean():>11.2f}"
              f"{sub['cl_night'].mean():>10.1f}"
              f"{sub['cloud'].mean():>8.1f}"
              f"{sub['sw_rad'].mean():>8.1f}")

    print()
    print("  Threshold WCA komposit (skor 0–5, onset = rata-rata 14d ≥ 4.0):")
    print(f"    u_mean    > {WCA_U_MEAN_THR:.2f} unit-vector")
    print(f"    u_std     < {WCA_U_STD_THR:.2f} unit-vector")
    print(f"    frac_west > {WCA_FRAC_WEST_THR:.2f}")
    print(f"    cl_night  > {WCA_CL_NIGHT_THR:.1f} %")
    print(f"    cloud     > {WCA_CLOUD_THR:.1f} %")


def report_detection(df: pd.DataFrame) -> None:
    print_header(
        "DETEKSI ONSET · OFFSET · DURASI ADVESI AWAN",
        "EV09wind_adveksi v1.0.1 · ensemble A1+A2+A3 (score-based)"
    )

    a_all = _get_advection_features(df)
    if a_all is None:
        print("  [!] Fitur adveksi tidak dapat dihitung.")
        return

    print()
    print("  Menjalankan estimator A1_WCA, A2_WIND, A3_NIGHT...")

    all_yr: Dict[int, Dict] = {}
    records: List[Dict] = []
    for py in range(2015, 2027):
        r = run_year_advection(df, py, a_all)
        if r:
            all_yr[py] = r
            if r.get("onset_ens") is not None:
                records.append(r)

    sec_header("A · ONSET · OFFSET · DURASI PER TAHUN")
    print(f"  {'Thn':<6}{'ONSET':>9}{'Tanggal':>14}"
          f"{'OFFSET':>9}{'Tanggal':>14}{'DURASI':>9}"
          f"{'PEAK':>8}{'WCA pk':>9}")
    print("  " + "─" * (W - 4))

    for py in range(2015, 2027):
        if py not in all_yr:
            continue
        r = all_yr[py]
        print(f"  {py:<6}"
              f"{_sfmt(r.get('onset_ens')):>9}"
              f"{_fmt_dopy(py, r.get('onset_ens')):>14}"
              f"{_sfmt(r.get('offset_ens')):>9}"
              f"{_fmt_dopy(py, r.get('offset_ens')):>14}"
              f"{_sfmt(r.get('duration')):>9}"
              f"{_sfmt(r.get('peak_dopy')):>8}"
              f"{_sfmt(r.get('peak_wca'), 2):>9}")

    sec_header("B · ONSET DETAIL PER ESTIMATOR (dopy)")
    print(f"  Bobot: A1_WCA={ENS_W_ADV['A1_WCA']} "
          f"A2_WIND={ENS_W_ADV['A2_WIND']} "
          f"A3_NIGHT={ENS_W_ADV['A3_NIGHT']}")
    print(f"  {'Thn':<6}{'A1_WCA':>10}{'A2_WIND':>10}"
          f"{'A3_NIGHT':>10}{'ENS':>10}")
    print("  " + "─" * 50)

    for py in sorted(all_yr):
        r = all_yr[py]
        raw = r.get("onset_raw", {})
        print(f"  {py:<6}"
              f"{_sfmt(raw.get('A1_WCA')):>10}"
              f"{_sfmt(raw.get('A2_WIND')):>10}"
              f"{_sfmt(raw.get('A3_NIGHT')):>10}"
              f"{_sfmt(r.get('onset_ens')):>10}")

    if not records:
        print("\n  [!] Tidak ada onset adveksi terdeteksi.")
        return

    sec_header("C · STATISTIK MULTI-TAHUN")
    stats = multiyr_stats_advection(records)

    print(f"  {'Variabel':<16}{'N':>4}{'Mean':>9}{'Med':>9}"
          f"{'Std':>8}{'Min':>8}{'Max':>8}"
          f"{'Slope':>9}{'t':>8}")
    print("  " + "─" * (W - 4))

    labels = {
        "onset_ens":  "Onset (dopy)",
        "offset_ens": "Offset (dopy)",
        "duration":   "Durasi (hari)",
        "peak_dopy":  "Peak dopy",
        "peak_wca":   "Peak WCA",
    }
    for k, lbl in labels.items():
        s = stats.get(k, {})
        if not s or s.get("n", 0) < 2:
            print(f"  {lbl:<16}{s.get('n', 0):>4}   (data tidak cukup)")
            continue
        print(f"  {lbl:<16}{s['n']:>4}"
              f"{s['mean']:>9.1f}{s['median']:>9.1f}"
              f"{s['std']:>8.1f}{s['min']:>8.1f}{s['max']:>8.1f}"
              f"{s['slope']:>+9.2f}{s['t']:>+8.2f}")


def report_comparison(df: pd.DataFrame) -> None:
    print_header(
        "PERBANDINGAN: ONSET ADVESI (WCA) vs ONSET BARATAN (BPI)",
        "Berapa hari adveksi awan muncul SETELAH langit mengunci?"
    )

    rows = comparison_table(df)
    if not rows:
        print("  [!] Data tidak cukup.")
        return

    print()
    print("  Onset BPI  = hari langit mulai mengunci (efek radiatif)")
    print("  Onset WCA  = hari awan bergerak stabil dari barat (dinamik)")
    print()
    print(f"  {'Thn':<6}{'Onset BPI':>11}{'Onset WCA':>11}"
          f"{'Δ (hari)':>11}  Keterangan")
    print("  " + "─" * (W - 4))

    lags: List[float] = []
    for row in rows:
        py  = row["py"]
        bpi = row["onset_bpi"]
        wca = row["onset_wca"]
        lag = row["lag"]

        bpi_s = f"{bpi:>11.1f}" if bpi is not None else f"{'—':>11}"
        wca_s = f"{wca:>11.1f}" if wca is not None else f"{'—':>11}"

        if lag is not None:
            lag_s = f"{lag:>+11.1f}"
            lags.append(lag)
            if lag > 90:
                note = f"Adveksi {lag:.0f} hari setelah kunci"
            elif lag > 40:
                note = f"Adveksi {lag:.0f} hari setelah kunci"
            elif lag > 0:
                note = "Adveksi cepat menyusul"
            else:
                note = "Adveksi mendahului kunci (!)"
        else:
            lag_s = f"{'—':>11}"
            note = ""

        print(f"  {py:<6}{bpi_s}{wca_s}{lag_s}  {note}")

    if lags:
        arr = np.array(lags)
        print()
        print(f"  Ringkasan Δ (WCA − BPI):")
        print(f"    N      : {len(arr)}")
        print(f"    Mean   : {arr.mean():+.1f} hari")
        print(f"    Median : {np.median(arr):+.1f} hari")
        print(f"    Std    : {arr.std(ddof=1):.1f} hari")
        print(f"    Range  : {arr.min():+.0f} s.d. {arr.max():+.0f}")
        print()
        if arr.mean() > 60:
            print("  ⟹ Adveksi stabil SISTEMATIS terjadi ~3 bulan setelah")
            print("    langit mengunci. Ini mengonfirmasi bahwa keduanya")
            print("    adalah fenomena berbeda dalam siklus yang sama.")
            print("    Adveksi = Fase Plateau (puncak musim),")
            print("    Kunci   = Fase Kunci (awal baratan).")


def report_peak_years(df: pd.DataFrame) -> None:
    print_header(
        "PUNCAK ADVESI PER TAHUN — KAPAN AWAN PALING STABIL DARI BARAT?",
        "Diambil dari 30-hari rolling u_mean tertinggi di window Des-Feb"
    )

    a = _get_advection_features(df)
    if a is None:
        print("  [!] Data tidak tersedia.")
        return

    print()
    print(f"  {'Thn':<6}{'dopy_pk':>9}{'Tanggal':>16}"
          f"{'u_mean':>9}{'u_std':>8}{'frac_west':>11}"
          f"{'cl_night':>10}{'cloud':>8}")
    print("  " + "─" * (W - 4))

    for py in range(2015, 2027):
        sub = _year_slice(a, py)
        if len(sub) < 60:
            continue
        sub = sub.copy()
        sub["u_roll"] = sub["u_mean"].rolling(30, center=True,
                                              min_periods=20).mean()
        w = sub[(sub["dopy"] >= ADV_PEAK_LO)
                & (sub["dopy"] <= ADV_PEAK_HI)].dropna(subset=["u_roll"])
        if len(w) == 0:
            continue
        idx = w["u_roll"].idxmax()
        r = w.loc[idx]
        print(f"  {py:<6}{r['dopy']:>9.1f}"
              f"{pd.Timestamp(r['date']).strftime('%d %b %Y'):>16}"
              f"{r['u_mean']:>+9.2f}"
              f"{r['u_std']:>8.2f}"
              f"{r['frac_west']:>11.2f}"
              f"{r['cl_night']:>10.1f}"
              f"{r['cloud']:>8.1f}")

    print()
    print("  Catatan:")
    print("   · dopy_pk sekitar 217–240 = akhir Jan – pertengahan Feb")
    print("   · u_std < 0.35 = angin stabil (tidak fluktuatif)")
    print("   · frac_west ~1.00 = hampir 100% jam arah barat")
    print("   · cl_night ~95 = awan malam tetap tebal (siang-malam stabil)")


def report_sub_phase(df: pd.DataFrame) -> None:
    print_header(
        "SUB-FASE PLATEAU 3a vs 3b — UNTUK LIFECYCLE BARATAN",
        "Memisahkan 'saturasi' (3a) dari 'adveksi mapan' (3b)"
    )

    print()
    print("  Fase Plateau baratan (dopy 160–230) dapat dipilah menjadi:")
    print("    3a Saturasi : dopy 160–215 — semua jenuh, angin belum stabil")
    print("    3b Adveksi  : dopy 215–240 — angin stabil, awan bergerak barat")
    print()

    prof = sub_phase_profile(df)
    if not prof:
        print("  [!] Data tidak cukup.")
        return

    fields = [
        ("u_mean",    "u_comp rata-rata (unit-vector)"),
        ("u_std",     "u_comp std harian (unit-vector)"),
        ("frac_west", "fraksi jam u_comp > 0"),
        ("cl_night",  "cloud malam 22–04 (%)"),
        ("cl_day",    "cloud siang 10–16 (%)"),
        ("cloud",     "cloud total (%)"),
        ("sw_rad",    "SW radiation (W/m²)"),
        ("tcwv",      "TCWV (kg/m²)"),
        ("flux",      "u_mean × tcwv"),
    ]

    print(f"  {'Variabel':<28}{'3a Saturasi':>14}{'3b Adveksi':>14}"
          f"{'Δ (3b−3a)':>13}")
    print("  " + "─" * (W - 4))

    p3a = prof.get("3a_Saturasi", {})
    p3b = prof.get("3b_Adveksi", {})

    for (field, label) in fields:
        v_a = p3a.get(field, float("nan"))
        v_b = p3b.get(field, float("nan"))
        if not (np.isfinite(v_a) and np.isfinite(v_b)):
            continue
        delta = v_b - v_a
        print(f"  {label:<28}{v_a:>14.2f}{v_b:>14.2f}{delta:>+13.2f}")

    print()
    print(f"  n hari — 3a: {p3a.get('n_days', 0):,}    "
          f"3b: {p3b.get('n_days', 0):,}")
    print()
    print("  Yang paling kontras:")
    print("   · u_std   turun → angin jadi stabil")
    print("   · frac_west naik → hampir selalu dari barat")
    print("   · u_mean  naik → kecepatan adveksi meningkat")
    print("   · cloud & cl_night tetap tinggi → awan tetap, hanya bergerak")


def report_all(df: pd.DataFrame) -> None:
    report_profile(df)
    report_detection(df)
    report_comparison(df)
    report_peak_years(df)
    report_sub_phase(df)


# ══════════════════════════════════════════════════════════════════════════
# §11  CLI
# ══════════════════════════════════════════════════════════════════════════

MENU_ITEMS = (
    "  1 › Profil adveksi tahunan (bulan × indikator)",
    "  2 › Deteksi onset WCA per tahun (A1+A2+A3 ensemble)",
    "  3 › Perbandingan onset WCA vs onset BPI (baratan)",
    "  4 › Puncak adveksi per tahun (30-hari rolling u_mean)",
    "  5 › Sub-fase Plateau 3a / 3b — untuk lifecycle baratan",
    "  6 › Jalankan semua (1–5)",
    "  0 › Keluar",
)


def show_menu() -> None:
    print()
    print(box_top(
        "PRANATA MANGSA — ADVESI AWAN BARATAN (EV09-WIND-ADVEKSI v1.0.1)"))
    print(box_row(
        "Westward Cloud Advection (WCA) — kapan awan bergerak stabil "
        "dari barat"))
    print(box_row(
        "Fenomena berbeda dari onset baratan — terjadi ~3 bulan setelahnya"))
    print(box_row("−7.5220°LS, 112.5661°BT, 28 m · ERA5/IFS · P1+P2 IDW"))
    print(box_row("A1_WCA (score 0–5) · A2_WIND · A3_NIGHT · ensemble Biweight"))
    print(box_mid())
    for item in MENU_ITEMS:
        print(box_row(item))
    print(box_bot())


def main_loop(df: pd.DataFrame) -> None:
    while True:
        show_menu()
        pilihan = input("  Pilih menu (0–6): ").strip()
        if pilihan == "0":
            print()
            print(box_top())
            print(box_row("Terima kasih — EV09-Wind-Adveksi v1.0.1"))
            print(box_bot())
            break
        elif pilihan == "1":
            report_profile(df)
        elif pilihan == "2":
            report_detection(df)
        elif pilihan == "3":
            report_comparison(df)
        elif pilihan == "4":
            report_peak_years(df)
        elif pilihan == "5":
            report_sub_phase(df)
        elif pilihan == "6":
            report_all(df)
        else:
            print("\n  Pilihan tidak valid.")
            continue
        input("\n  Tekan Enter untuk kembali ke menu...")


def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="EV09wind_adveksi",
        description=("Westward Cloud Advection analysis — kapan awan "
                     "bergerak stabil dari barat. Fenomena berbeda dari "
                     "onset baratan (BPI); terjadi ~3 bulan setelahnya."),
    )
    ap.add_argument("--profile",    action="store_true",
                    help="Profil siklus tahunan adveksi")
    ap.add_argument("--detect",     action="store_true",
                    help="Deteksi onset WCA per tahun")
    ap.add_argument("--compare",    action="store_true",
                    help="Perbandingan WCA vs BPI")
    ap.add_argument("--peak",       action="store_true",
                    help="Puncak adveksi per tahun")
    ap.add_argument("--subphase",   action="store_true",
                    help="Sub-fase Plateau 3a/3b")
    ap.add_argument("--all",        action="store_true",
                    help="Jalankan semua laporan")
    return ap


def main(argv=None) -> int:
    args = _build_argparser().parse_args(argv)

    print()
    print(box_top("EV09wind_adveksi.py v1.0.1 — Memuat data..."))
    print(box_bot())

    df = load_advection_data()
    if df is None:
        return 1

    if args.all:       report_all(df);        return 0
    if args.profile:   report_profile(df);    return 0
    if args.detect:    report_detection(df);  return 0
    if args.compare:   report_comparison(df); return 0
    if args.peak:      report_peak_years(df); return 0
    if args.subphase:  report_sub_phase(df);  return 0

    main_loop(df)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Program dihentikan.")
        sys.exit(0)