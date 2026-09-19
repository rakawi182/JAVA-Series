#!/usr/bin/env python3
"""
EV09wind_validation.py — Uji out-of-sample & lintas-variabel
untuk boundary monsoon Pranatamangsa.

Menjalankan empat uji:
  A. Konvergensi lintas-variabel (monsoon/rain/cloud/cloud_lo)
  B. Stabilitas temporal (3 sub-jendela 4-tahun)
  C. Out-of-sample (latih 2015-2020, uji 2021-2026)
  D. Tren reversal per tahun + regresi linear

Import dari EV09wind.py — jangan modifikasi file itu.
"""
from __future__ import annotations
import sys
from typing import Optional, Tuple
import numpy as np
import pandas as pd

from EV09wind import (_require_data, ANCHOR_MONTH, ANCHOR_DAY, W,
                      sec_header, print_header)


# ── Helper ───────────────────────────────────────────────────────────────

def to_dopy(dates):
    t = pd.to_datetime(dates)
    a  = pd.to_datetime(dict(year=t.dt.year,     month=ANCHOR_MONTH, day=ANCHOR_DAY))
    ap = pd.to_datetime(dict(year=t.dt.year - 1, month=ANCHOR_MONTH, day=ANCHOR_DAY))
    d = np.where(t < a,
                 (t - ap).dt.total_seconds() / 86400.0,
                 (t - a ).dt.total_seconds() / 86400.0)
    return d % 365.0


def rolling_daily(df, field, agg="mean", win=30):
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    s = d.groupby("_date").agg(v=(field, agg)).reset_index()
    if agg == "mean":
        s["s"] = s["v"].rolling(win, center=True, min_periods=win // 2).mean()
    else:
        s["s"] = s["v"].rolling(win, min_periods=win // 2).sum()
    s["dopy"] = to_dopy(s["_date"])
    return s


def find_crossing(sig, dopys, thr, up=True, sustain=15,
                  window=(100, 250)):
    """
    window = (dopy_min, dopy_max) — batasi pencarian di jendela
    monsoon (Agustus–Februari). Default: cari hanya di 100–250
    (≈ 30 Sep – 27 Feb), di mana monsoon reversal seharusnya terjadi.
    """
    lo, hi = window
    for i in range(1, len(sig)):
        # Skip kalau di luar jendela
        if dopys[i] < lo or dopys[i] > hi:
            continue
        if not (np.isfinite(sig[i]) and np.isfinite(sig[i-1])):
            continue
        if up and sig[i - 1] < thr <= sig[i]:
            fut = sig[i:i + sustain]
            if np.isfinite(fut).sum() >= sustain - 5 and \
               np.nanmin(fut) >= thr - 0.05 * abs(thr):
                return float(dopys[i])
        if not up and sig[i - 1] > thr >= sig[i]:
            fut = sig[i:i + sustain]
            if np.isfinite(fut).sum() >= sustain - 5 and \
               np.nanmax(fut) <= thr + 0.05 * abs(thr):
                return float(dopys[i])
    return None


# ── Detektor ─────────────────────────────────────────────────────────────

def det_monsoon(df):
    if "u_comp" not in df.columns: return None
    s = rolling_daily(df, "u_comp", "mean", 30)
    return find_crossing(s["s"].values, s["dopy"].values, 0.0, up=True)


def det_rain(df):
    s = rolling_daily(df, "precip", "sum", 30)
    return find_crossing(s["s"].values, s["dopy"].values, 100.0, up=True)


def det_cloud(df):
    s = rolling_daily(df, "cloud", "mean", 30)
    return find_crossing(s["s"].values, s["dopy"].values, 75.0, up=True)


def det_cloud_lo(df):
    s = rolling_daily(df, "cloud_lo", "mean", 30)
    return find_crossing(s["s"].values, s["dopy"].values, 20.0, up=True)


DETECTORS = (
    ("Monsoon rev (u→0)",       det_monsoon),
    ("Rain onset (>100mm/30d)", det_rain),
    ("Cloud rise (>75%)",       det_cloud),
    ("Low-cloud rise (>20%)",   det_cloud_lo),
)

R10_LABUH = 131.0
R30_LABUH =  94.0


# ── Uji A ────────────────────────────────────────────────────────────────

def test_A(df):
    sec_header("A · KONVERGENSI LINTAS-VARIABEL",
               "4 detektor independen, data 2015–2026")
    print(f"\n  {'Detektor':<28}{'dopy':>8}{'vs R10':>9}{'vs R30':>9}")
    print("  " + "─" * 56)
    vs = []
    for name, fn in DETECTORS:
        try: v = fn(df)
        except Exception: v = None
        if v is None:
            print(f"  {name:<28}{'n/a':>8}{'':>9}{'':>9}")
        else:
            vs.append(v)
            print(f"  {name:<28}{v:>8.1f}{v-R10_LABUH:>+9.1f}{v-R30_LABUH:>+9.1f}")
    if vs:
        m = float(np.mean(vs)); spr = float(max(vs) - min(vs))
        print(f"\n  Rata-rata lintas metode : dopy {m:.1f}")
        print(f"  Spread (max−min)        : {spr:.1f} hari")
        print(f"  R10 = dopy 131 → err    : {abs(m-R10_LABUH):.1f} hari")
        print(f"  R30 = dopy  94 → err    : {abs(m-R30_LABUH):.1f} hari")
        if spr < 15:
            print("  → Konvergensi BAIK (semua dalam ±7 hari).")
        elif spr < 30:
            print("  → Konvergensi SEDANG.")
        else:
            print("  → Konvergensi LEMAH — menangkap aspek berbeda.")
    return vs


# ── Uji B ────────────────────────────────────────────────────────────────

def test_B(df):
    sec_header("B · STABILITAS TEMPORAL",
               "3 jendela 4-tahun dari pranata-year anchor 22 Jun")
    windows = [
        ("2015–2018", "2015-06-22", "2018-06-21"),
        ("2019–2022", "2019-06-22", "2022-06-21"),
        ("2023–2026", "2023-06-22", "2026-06-21"),
    ]
    print(f"\n  {'Detektor':<28}" + "".join(f"{l:>12}" for l, _, _ in windows)
          + f"{'Spread':>9}")
    print("  " + "─" * (28 + 3 * 12 + 9))
    for name, fn in DETECTORS:
        vals = []
        row = f"  {name:<28}"
        for lbl, s, e in windows:
            sub = df[(df["time"] >= s) & (df["time"] <= e)]
            try: v = fn(sub) if len(sub) > 500 else None
            except Exception: v = None
            vals.append(v)
            row += f"{v:>12.1f}" if v is not None else f"{'n/a':>12}"
        valid = [x for x in vals if x is not None]
        spr = (max(valid) - min(valid)) if len(valid) >= 2 else float("nan")
        row += f"{spr:>9.1f}" if np.isfinite(spr) else f"{'n/a':>9}"
        print(row)
    print("\n  Spread < 10 hari → boundary stasioner.")
    print("  Spread > 20 hari → non-stationarity terdeteksi.")


# ── Uji C ────────────────────────────────────────────────────────────────

def test_C(df):
    sec_header("C · OUT-OF-SAMPLE",
               "Latih 2015–2020, uji 2021–2026")
    tr = df[(df["time"] >= "2015-01-01") & (df["time"] <= "2020-12-31")]
    te = df[(df["time"] >= "2021-01-01") & (df["time"] <= "2026-12-31")]
    print(f"\n  Train N={len(tr):,}   Test N={len(te):,}\n")
    print(f"  {'Detektor':<28}{'train':>9}{'test':>9}{'|Δ|':>8}")
    print("  " + "─" * 54)
    for name, fn in DETECTORS:
        try: a, b = fn(tr), fn(te)
        except Exception: a = b = None
        if a is None or b is None:
            print(f"  {name:<28}{'n/a':>9}{'n/a':>9}{'':>8}")
        else:
            print(f"  {name:<28}{a:>9.1f}{b:>9.1f}{b-a:>+8.1f}")
    print("\n  |Δ|<7 → prediksi out-of-sample akurat.")
    print("  |Δ|>14 → pergeseran iklim antar dekade.")


# ── Uji D ────────────────────────────────────────────────────────────────

def test_D(df):
    sec_header("D · TREN REVERSAL PER PRANATA-TAHUN",
               "Deteksi monsoon reversal tiap tahun + regresi")
    rows = []
    for py in range(2015, 2027):
        s = pd.Timestamp(year=py, month=6, day=22)
        e = s + pd.Timedelta(days=366)
        sub = df[(df["time"] >= s) & (df["time"] < e)]
        if len(sub) < 5000: continue
        try: v = det_monsoon(sub)
        except Exception: v = None
        if v is not None:
            rows.append((py, v))
    if not rows:
        print("  [!] tidak cukup data"); return
    print(f"\n  {'Tahun':<8}{'rev dopy':>10}   Bar")
    print("  " + "─" * 40)
    for y, v in rows:
        bar = int(round((v - 100) / 2)) if 100 <= v <= 200 else 0
        print(f"  {y:<8}{v:>10.1f}   {'█' * max(0, min(30, bar))}")
    if len(rows) >= 3:
        ys = np.array([r[0] for r in rows])
        vs = np.array([r[1] for r in rows])
        coef = np.polyfit(ys, vs, 1)
        r = float(np.corrcoef(ys, vs)[0, 1])
        print(f"\n  Slope  : {coef[0]:+.2f} hari/tahun")
        print(f"  Pearson: {r:+.3f}")
        if abs(r) < 0.3:
            print("  → Tidak ada tren signifikan (stasioner).")
        elif coef[0] > 0:
            print(f"  → Reversal MUNDUR {coef[0]:.2f} hari/tahun.")
        else:
            print(f"  → Reversal MAJU {abs(coef[0]):.2f} hari/tahun.")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    df = _require_data()
    if df is None: return 1
    print_header("VALIDASI OUT-OF-SAMPLE — EV09-WIND",
                 "Empat uji: cross-var · stability · OOS · trend")
    test_A(df)
    test_B(df)
    test_C(df)
    test_D(df)
    return 0


if __name__ == "__main__":
    sys.exit(main())