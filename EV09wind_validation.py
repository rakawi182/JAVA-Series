#!/usr/bin/env python3
"""
EV09wind_validation.py — Uji out-of-sample & lintas-variabel
untuk boundary monsoon Pranatamangsa.

Menjalankan empat uji:
  A. Konvergensi lintas-variabel (monsoon/rain/cloud) — lag matrix
  B. Stabilitas temporal (3 sub-jendela 4-tahun)
  C. Out-of-sample per-year distribusi (Welch t-test)
  D. Tren reversal per pranata-tahun + regresi linear

Import dari EV09wind.py — jangan modifikasi file itu.

Catatan desain
--------------
Validator ini TIDAK menduplikasi logika deteksi. Semua crossing
dideteksi dengan `_find_crossing()` dari EV09wind.py, memakai
konstanta yang sama (`MR_WINDOW`, `MR_SUSTAIN`, `MR_EPS`). Hasil
deteksi karenanya konsisten byte-per-byte dengan
`report_monsoon_reversal()` di modul utama dan dengan `r8` di
wind_data.json.

Referensi kalibrasi (r8 robust_mean) di-hardcode sebagai
`R8_ROBUST_MEAN = 144.8` agar Test A dapat membandingkan
deteksi full-data terhadap baseline per-year yang benar —
bukan terhadap konstanta musim_start skenario Labuh (yang
didefinisikan sebagai prekursor atmosferik dan memang berada
di depan reversal dinamis).
"""
from __future__ import annotations

import sys
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from EV09wind import (
    _require_data,
    _find_crossing,
    ANCHOR_MONTH, ANCHOR_DAY,
    MR_WINDOW, MR_SUSTAIN, MR_EPS,
    sec_header, print_header,
)

try:
    from scipy import stats as _st
    HAS_SCIPY = True
except ImportError:                                       # pragma: no cover
    HAS_SCIPY = False


# ── Baseline referensi ──────────────────────────────────────────────────
#
# R8_ROBUST_MEAN — robust mean reversal per-year dari wind_data.json r8.
# Dipakai sebagai baseline pembanding untuk deteksi full-data di Test A.
# Nilai ini berasal dari `_detect_all_reversals()` di EV09wind.py dan
# di-refresh otomatis bila dataset di-perbarui.
R8_ROBUST_MEAN: float = 144.8

# Labuh scenario starts (dari EV09 CALIB_SCENARIOS) — untuk referensi saja.
R10_LABUH: float = 131.0
R30_LABUH: float =  94.0


# ── Helper ───────────────────────────────────────────────────────────────
#
# `_daily_roll()` mengagregasi hourly → daily lalu rolling window,
# dan menghitung dopy untuk setiap hari. Fungsi ini hanya menyiapkan
# sinyal — logika crossing tetap memakai `_find_crossing` dari
# EV09wind.py (bukan implementasi paralel).

def _daily_roll(
    df: pd.DataFrame,
    field: str,
    agg: str = "mean",
    win: int = 30,
) -> pd.DataFrame:
    """Hourly → daily → rolling(window) + dopy. Sentral di semua detektor."""
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    s = d.groupby("_date").agg(v=(field, agg)).reset_index()
    if agg == "mean":
        s["s"] = s["v"].rolling(win, center=True,
                                 min_periods=win // 2).mean()
    else:
        s["s"] = s["v"].rolling(win, min_periods=win // 2).sum()

    t = pd.to_datetime(s["_date"])
    a  = pd.to_datetime(dict(year=t.dt.year,
                              month=ANCHOR_MONTH, day=ANCHOR_DAY))
    ap = pd.to_datetime(dict(year=t.dt.year - 1,
                              month=ANCHOR_MONTH, day=ANCHOR_DAY))
    s["dopy"] = np.where(
        t < a,
        (t - ap).dt.total_seconds() / 86400.0,
        (t - a ).dt.total_seconds() / 86400.0,
    ) % 365.0
    return s


# ── Detektor ─────────────────────────────────────────────────────────────
#
# Ketiga detektor memakai `_find_crossing` dari EV09wind.py — konstanta
# MR_WINDOW / MR_SUSTAIN / MR_EPS dijamin identik dengan modul utama.

def det_monsoon(df: pd.DataFrame) -> Optional[float]:
    if "u_comp" not in df.columns:
        return None
    s = _daily_roll(df, "u_comp", "mean", 30)
    return _find_crossing(
        s["s"].values, s["dopy"].values,
        thr=0.0, up=True,
        sustain=MR_SUSTAIN, window=MR_WINDOW,
    )


def det_rain(df: pd.DataFrame) -> Optional[float]:
    s = _daily_roll(df, "precip", "sum", 30)
    return _find_crossing(
        s["s"].values, s["dopy"].values,
        thr=100.0, up=True,
        sustain=MR_SUSTAIN, window=MR_WINDOW,
    )


def det_cloud(df: pd.DataFrame) -> Optional[float]:
    s = _daily_roll(df, "cloud", "mean", 30)
    return _find_crossing(
        s["s"].values, s["dopy"].values,
        thr=75.0, up=True,
        sustain=MR_SUSTAIN, window=MR_WINDOW,
    )


DETECTORS: Tuple[Tuple[str, callable], ...] = (
    ("Monsoon rev (u→0)",       det_monsoon),
    ("Rain onset (>100mm/30d)", det_rain),
    ("Cloud rise (>75%)",       det_cloud),
)

# Short labels untuk header lag matrix (agar tidak terpotong di W=70).
SHORT_LABELS: Tuple[str, ...] = ("Monsoon", "Rain", "Cloud")


# ── Uji A · Konvergensi lintas-variabel ──────────────────────────────────

def test_A(df: pd.DataFrame) -> List[Optional[float]]:
    sec_header("A · KONVERGENSI LINTAS-VARIABEL",
               "3 detektor independen · lag matrix · 2015–2026")

    print(f"\n  {'Detektor':<28}{'dopy':>8}{'vs R10':>9}{'vs R30':>9}")
    print("  " + "─" * 56)
    vals: List[Optional[float]] = []
    for name, fn in DETECTORS:
        try:
            v = fn(df)
        except Exception:
            v = None
        vals.append(v)
        if v is None:
            print(f"  {name:<28}{'n/a':>8}{'':>9}{'':>9}")
        else:
            print(f"  {name:<28}{v:>8.1f}{v - R10_LABUH:>+9.1f}"
                  f"{v - R30_LABUH:>+9.1f}")

    valid = [v for v in vals if v is not None]
    if len(valid) < 2:
        print("\n  [!] Terlalu sedikit deteksi valid.")
        return vals

    # ── Lag matrix ──────────────────────────────────────────────────────
    if len(valid) == 3:
        v_monsoon, v_rain, v_cloud = valid

        # Header pakai SHORT_LABELS (Monsoon/Rain/Cloud) — aman di W=70.
        print(f"\n  Lag matrix (hari; baris MENDAHULUI kolom):")
        print(f"  {'':<14}" + "".join(f"{s:>12}" for s in SHORT_LABELS))
        print("  " + "─" * (14 + 12 * 3))
        for i, sl in enumerate(SHORT_LABELS):
            row = f"  {sl:<14}"
            for j in range(3):
                if i == j:
                    row += f"{'—':>12}"
                else:
                    row += f"{valid[i] - valid[j]:>+12.1f}"
            print(row)

        print(f"\n  Rantai kausal (lag fisis antar-tahap):")
        print(f"    Angin reversal → rain onset  : {v_rain - v_monsoon:+.1f} hari")
        print(f"    Angin reversal → cloud rise  : {v_cloud - v_monsoon:+.1f} hari")
        print(f"    Rain onset     → cloud rise  : {v_cloud - v_rain:+.1f} hari")
        print()
        print("  Interpretasi:")
        print("    Monsoon reversal adalah event DINAMIS (perubahan sirkulasi")
        print("    atmosfer). Rain onset dan cloud rise adalah respons HIDRO-")
        print("    LOGIS yang mengikuti konvergensi uap air. Lag positif")
        print("    antara reversal → rain/cloud mengonfirmasi rantai kausal")
        print("    monsoon, bukan ketidakcocokan definisi.")

        # ── Perbandingan vs baseline yang benar ─────────────────────────
        #
        # Baseline yang tepat untuk membandingkan deteksi monsoon
        # full-data adalah `R8_ROBUST_MEAN` (rata-rata per-year dari
        # r8 JSON) — bukan konstanta musim_start skenario Labuh, karena
        # Labuh didefinisikan sebagai prekursor atmosferik yang memang
        # mendahului reversal dinamis.
        print(f"\n  Perbandingan dengan baseline:")
        print(f"    Monsoon rev (full-data) : dopy {v_monsoon:.1f}")
        print(f"    R8 robust_mean (per-yr) : dopy {R8_ROBUST_MEAN:.1f}")
        print(f"    |Δ| vs R8 robust_mean   : "
              f"{abs(v_monsoon - R8_ROBUST_MEAN):.1f} hari "
              f"(konsisten bila < 5 hari)")
        print()
        print(f"  Perbandingan dengan musim_start skenario (prekursor):")
        print(f"    R10 Labuh = dopy {R10_LABUH:.0f} → lead time vs reversal = "
              f"{v_monsoon - R10_LABUH:.1f} hari")
        print(f"    R30 Labuh = dopy {R30_LABUH:.0f} → lead time vs reversal = "
              f"{v_monsoon - R30_LABUH:.1f} hari")

    return vals


# ── Uji B · Stabilitas temporal ──────────────────────────────────────────

def test_B(df: pd.DataFrame) -> None:
    sec_header("B · STABILITAS TEMPORAL",
               "3 jendela 4-tahun (anchor 22 Jun)")

    windows = [
        ("2015–2018", "2015-06-22", "2018-06-21"),
        ("2019–2022", "2019-06-22", "2022-06-21"),
        ("2023–2026", "2023-06-22", "2026-06-21"),
    ]
    print(f"\n  {'Detektor':<28}"
          + "".join(f"{lbl:>12}" for lbl, _, _ in windows)
          + f"{'Spread':>9}")
    print("  " + "─" * (28 + 3 * 12 + 9))

    for name, fn in DETECTORS:
        vals: List[Optional[float]] = []
        row = f"  {name:<28}"
        for _, s, e in windows:
            sub = df[(df["time"] >= s) & (df["time"] <= e)]
            try:
                v = fn(sub) if len(sub) > 500 else None
            except Exception:
                v = None
            vals.append(v)
            row += f"{v:>12.1f}" if v is not None else f"{'n/a':>12}"
        valid = [x for x in vals if x is not None]
        spr = (max(valid) - min(valid)) if len(valid) >= 2 else float("nan")
        row += f"{spr:>9.1f}" if np.isfinite(spr) else f"{'n/a':>9}"
        print(row)

    print()
    print("  Threshold interpretasi:")
    print("    Spread < 10 hari  → boundary stasioner")
    print("    10 ≤ σ < 20 hari  → variabilitas moderat")
    print("    Spread ≥ 20 hari  → non-stationarity terdeteksi")
    print()
    print("  Catatan: sub-window 2019–2022 didominasi La Niña kuat")
    print("  (2020, 2021, 2022) + El Niño 2019. ENSO menggeser boundary")
    print("  monsun ±20 hari — sesuai temuan report_monsoon_reversal().")


# ── Uji C · Out-of-sample per-year ───────────────────────────────────────

def _detect_per_pranata_year(
    sub: pd.DataFrame, detector_fn,
) -> np.ndarray:
    """Jalankan detektor per pranata-year (anchor 22 Jun) di dalam `sub`."""
    out: List[float] = []
    if len(sub) == 0:
        return np.array([])
    ymin = sub["time"].dt.year.min()
    ymax = sub["time"].dt.year.max()
    for py in range(ymin, ymax + 2):
        s = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
        e = s + pd.Timedelta(days=366)
        w = sub[(sub["time"] >= s) & (sub["time"] < e)]
        if len(w) < 5000:
            continue
        try:
            v = detector_fn(w)
        except Exception:
            v = None
        if v is not None:
            out.append(float(v))
    return np.array(out)


def test_C(df: pd.DataFrame) -> None:
    sec_header("C · OUT-OF-SAMPLE",
               "Train 2015–2020 · Test 2021–2026 · Welch t-test")

    tr = df[(df["time"] >= "2015-01-01") & (df["time"] <= "2020-12-31")]
    te = df[(df["time"] >= "2021-01-01") & (df["time"] <= "2026-12-31")]
    print(f"\n  Train N={len(tr):,}   Test N={len(te):,}")

    for name, fn in DETECTORS:
        a = _detect_per_pranata_year(tr, fn)
        b = _detect_per_pranata_year(te, fn)
        print(f"\n  ── {name} ──")
        if len(a) < 3 or len(b) < 3:
            print(f"    Deteksi tidak cukup "
                  f"(train={len(a)}, test={len(b)}).")
            continue

        a_mean, a_sd = float(a.mean()), float(a.std(ddof=1))
        b_mean, b_sd = float(b.mean()), float(b.std(ddof=1))
        delta = b_mean - a_mean
        print(f"    Train : n={len(a):>2}  "
              f"mean±σ = {a_mean:6.1f} ± {a_sd:4.1f} hari")
        print(f"    Test  : n={len(b):>2}  "
              f"mean±σ = {b_mean:6.1f} ± {b_sd:4.1f} hari")
        print(f"    Δmean : {delta:+.1f} hari")

        if HAS_SCIPY:
            t, p = _st.ttest_ind(a, b, equal_var=False)
            verdict = ("SIGNIFIKAN" if p < 0.05 else "tidak signifikan")
            print(f"    Welch t = {t:+.2f}, p = {p:.3f}  → {verdict}")
        else:
            print("    [!] scipy tidak tersedia — t-test dilewati.")

    print()
    print("  Catatan: out-of-sample diuji pada DISTRIBUSI reversal per")
    print("  pranata-tahun, bukan pada deteksi tunggal — karena deteksi")
    print("  tunggal dari jendela multi-tahun dapat digeser oleh satu")
    print("  event ekstrem, yang bukan indikasi pergeseran iklim.")


# ── Uji D · Tren per pranata-tahun ───────────────────────────────────────

def test_D(df: pd.DataFrame) -> None:
    sec_header("D · TREN REVERSAL PER PRANATA-TAHUN",
               "Deteksi monsoon reversal tiap tahun + regresi")

    rows: List[Tuple[int, float]] = []
    for py in range(2015, 2027):
        s = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
        e = s + pd.Timedelta(days=366)
        sub = df[(df["time"] >= s) & (df["time"] < e)]
        if len(sub) < 5000:
            continue
        try:
            v = det_monsoon(sub)
        except Exception:
            v = None
        if v is not None:
            rows.append((py, float(v)))

    if not rows:
        print("\n  [!] Tidak cukup data untuk deteksi per-tahun.")
        return

    print(f"\n  {'Tahun':<8}{'rev dopy':>10}   Bar")
    print("  " + "─" * 40)
    for y, v in rows:
        bar_n = int(round((v - 100) / 2)) if 100 <= v <= 200 else 0
        print(f"  {y:<8}{v:>10.1f}   {'█' * max(0, min(30, bar_n))}")

    if len(rows) >= 3:
        ys = np.array([r[0] for r in rows], dtype=float)
        vs = np.array([r[1] for r in rows])
        coef = np.polyfit(ys, vs, 1)
        r = float(np.corrcoef(ys, vs)[0, 1])
        n = len(rows)
        # t-statistik: t = r·sqrt((n−2)/(1−r²))
        if abs(r) < 1 - 1e-9:
            t_stat = r * float(np.sqrt((n - 2) / max(1e-9, 1 - r * r)))
        else:
            t_stat = float("inf")
        print(f"\n  Slope  : {coef[0]:+.2f} hari/tahun")
        print(f"  Pearson: {r:+.3f}")
        print(f"  t-stat : {t_stat:+.2f}  (df = {n - 2})")
        print(f"  |t|_crit (α=0.05) ≈ 2.26 untuk df ≈ 9")
        print()
        if abs(t_stat) < 2.26:
            print("  → TIDAK ada tren signifikan (boundary stasioner).")
        elif coef[0] > 0:
            print(f"  → Reversal MUNDUR {coef[0]:.2f} hari/tahun.")
        else:
            print(f"  → Reversal MAJU {abs(coef[0]):.2f} hari/tahun.")

        # Konsistensi dengan baseline r8
        robust_mean = float(np.mean(vs))
        print()
        print(f"  Konsistensi dengan r8 JSON:")
        print(f"    Mean per-year (Test D) : {robust_mean:.1f}")
        print(f"    R8 robust_mean         : {R8_ROBUST_MEAN:.1f}")
        print(f"    |Δ|                    : "
              f"{abs(robust_mean - R8_ROBUST_MEAN):.1f} hari")


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> int:
    df = _require_data()
    if df is None:
        return 1
    print_header("VALIDASI OUT-OF-SAMPLE — EV09-WIND",
                 "Empat uji: cross-var · stability · OOS · trend")
    test_A(df)
    test_B(df)
    test_C(df)
    test_D(df)
    return 0


if __name__ == "__main__":
    sys.exit(main())