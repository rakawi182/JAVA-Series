#!/usr/bin/env python3
"""
EV09wind_precursor.py — Uji precursor angin ekstrem
====================================================

Menguji apakah variabel meteorologi (tekanan, suhu, radiasi, VPD) dapat
mendeteksi angin ekstrem sebelum terjadi.

Scope
-----
  1. Korelasi harian variabel-variabel vs ws10_max harian
  2. Komposit hari ekstrem (>P99 ws10) vs hari normal
  3. Precursor pagi (06:00–09:00) vs kejadian sore (12:00–16:00)
  4. Contingency table: probabilitas event diberikan kondisi
  5. Autocorrelation ws10: berapa lama persistensi

Interpretasi: bukan prediksi operasional, tapi skrining variabel mana yang
layak dipakai untuk model prediktif di iterasi berikutnya.
"""
from __future__ import annotations

import sys
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from EV09wind import (
    _read_openmeteo_csv, find_data_file, attach_time_features,
    DEFAULT_HOURLY_P1, DEFAULT_HOURLY_P2,
    TARGET_LAT, TARGET_LON, STATION_P1, STATION_P2,
    idw_weights, _find_col,
    box_top, box_row, box_mid, box_bot, thin_hbar, sec_header,
    MONTH_SHORT, W,
)


# ══════════════════════════════════════════════════════════════════════════
# Loader khusus dengan kolom precursor
# ══════════════════════════════════════════════════════════════════════════

_PRECURSOR_CACHE: Optional[pd.DataFrame] = None


def _extract_all_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Ambil semua kolom meteorologi relevan dari CSV Open-Meteo."""
    out = pd.DataFrame()
    out["time"] = df["time"]
    spec = (
        ("ws10",      ("wind_speed_10m",)),
        ("gust10",    ("wind_gusts_10m",)),
        ("wd10",      ("wind_direction_10m",)),
        ("ws100",     ("wind_speed_100m",)),
        ("wd100",     ("wind_direction_100m",)),
        ("temp",      ("temperature_2m (",)),
        ("pressure",  ("surface_pressure",)),
        ("rh",        ("relative_humidity_2m (",)),
        ("rad",       ("shortwave_radiation (",)),
        ("vpd",       ("vapour_pressure_deficit (",)),
        ("cloud",     ("cloud_cover (%)",)),
        ("cloud_lo",  ("cloud_cover_low (%)",)),
        ("precip",    ("precipitation (mm)",)),
    )
    for short, patterns in spec:
        col = None
        # Coba exact match dulu
        for p in patterns:
            if p in df.columns:
                col = p
                break
        if col is None:
            col = _find_col(df, *patterns)
        out[short] = df[col].astype(float) if col is not None else np.nan
    return out


def _idw_merge_full(d1: pd.DataFrame, d2: pd.DataFrame,
                     w1: float, w2: float) -> pd.DataFrame:
    """IDW merge semua kolom numerik. Direction pakai unit vector."""
    idx = d1.index.union(d2.index)
    out = pd.DataFrame(index=idx)
    skip = {"wd10", "wd100"}
    for col in d1.columns:
        if col not in d2.columns:
            out[col] = d1[col].reindex(idx).fillna(
                d2[col].reindex(idx) if col in d2.columns else np.nan)
            continue
        if col in skip:
            r1 = np.deg2rad(d1[col].reindex(idx).values)
            r2 = np.deg2rad(d2[col].reindex(idx).values)
            s_ = w1 * np.sin(r1) + w2 * np.sin(r2)
            c_ = w1 * np.cos(r1) + w2 * np.cos(r2)
            out[col] = (np.rad2deg(np.arctan2(s_, c_)) + 360.0) % 360.0
            continue
        v1 = d1[col].reindex(idx)
        v2 = d2[col].reindex(idx)
        both = v1.notna() & v2.notna()
        s = pd.Series(np.nan, index=idx)
        s.loc[both] = w1 * v1[both] + w2 * v2[both]
        o1 = v1.notna() & ~v2.notna();  s.loc[o1] = v1[o1]
        o2 = ~v1.notna() & v2.notna();  s.loc[o2] = v2[o2]
        out[col] = s
    return out.reset_index().rename(columns={"index": "time"})


def load_hourly_precursors(
    csv_p1: str = DEFAULT_HOURLY_P1,
    csv_p2: str = DEFAULT_HOURLY_P2,
) -> Optional[pd.DataFrame]:
    global _PRECURSOR_CACHE
    if _PRECURSOR_CACHE is not None:
        return _PRECURSOR_CACHE

    p1 = find_data_file(csv_p1)
    p2 = find_data_file(csv_p2)
    if p1 is None and p2 is None:
        print("  [!] File hourly10yr tidak ditemukan.")
        return None

    w1, w2 = idw_weights(TARGET_LAT, TARGET_LON, [STATION_P1, STATION_P2])

    if p1 is None:
        df = _extract_all_cols(_read_openmeteo_csv(p2))
    elif p2 is None:
        df = _extract_all_cols(_read_openmeteo_csv(p1))
    else:
        d1 = _extract_all_cols(_read_openmeteo_csv(p1)).set_index("time")
        d2 = _extract_all_cols(_read_openmeteo_csv(p2)).set_index("time")
        df = _idw_merge_full(d1, d2, w1, w2)

    df = df.sort_values("time").reset_index(drop=True)
    df = attach_time_features(df)
    _PRECURSOR_CACHE = df
    print(f"  [i] {len(df):,} baris hourly  ·  "
          f"{df['time'].min().date()} → {df['time'].max().date()}")
    return df


# ══════════════════════════════════════════════════════════════════════════
# Analisis kernel
# ══════════════════════════════════════════════════════════════════════════

def daily_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Agregasi harian: max ws10, mean pressure, max temp, dll."""
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    agg = d.groupby("_date").agg(
        ws10_max = ("ws10", "max"),
        ws10_mean = ("ws10", "mean"),
        gust_max = ("gust10", "max"),
        pressure = ("pressure", "mean"),
        temp_max = ("temp", "max"),
        temp_min = ("temp", "min"),
        temp_mean = ("temp", "mean"),
        vpd_max = ("vpd", "max"),
        vpd_mean = ("vpd", "mean"),
        rh_mean = ("rh", "mean"),
        rad_sum = ("rad", "sum"),
        rad_max = ("rad", "max"),
        cloud_lo = ("cloud_lo", "mean"),
        precip_sum = ("precip", "sum"),
        n = ("ws10", "count"),
    ).reset_index().rename(columns={"_date": "date"})
    agg = agg[agg["n"] >= 20].reset_index(drop=True)
    agg["month"] = agg["date"].dt.month
    # Anomali
    for col in ("pressure", "temp_max", "vpd_mean", "rad_sum", "ws10_max"):
        if col in agg.columns:
            agg[col + "_anom"] = (
                agg.groupby("month")[col].transform(lambda x: x - x.mean())
            )
    return agg


def morning_signature(df: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan pagi (06:00–09:00) per hari."""
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    morning = d[d["hour"].between(6, 9)]
    agg = morning.groupby("_date").agg(
        ws10_morning = ("ws10", "mean"),
        pressure_morning = ("pressure", "mean"),
        temp_morning = ("temp", "mean"),
        rad_morning = ("rad", "mean"),
        cloud_lo_morning = ("cloud_lo", "mean"),
        vpd_morning = ("vpd", "mean"),
        rh_morning = ("rh", "mean"),
        n = ("ws10", "count"),
    ).reset_index().rename(columns={"_date": "date"})
    return agg[agg["n"] >= 3].reset_index(drop=True)


def afternoon_peak(df: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan siang (12:00–16:00) per hari."""
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    aft = d[d["hour"].between(12, 16)]
    agg = aft.groupby("_date").agg(
        ws10_aft_max = ("ws10", "max"),
        gust_aft_max = ("gust10", "max"),
        n = ("ws10", "count"),
    ).reset_index().rename(columns={"_date": "date"})
    return agg[agg["n"] >= 3].reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════
# Reports
# ══════════════════════════════════════════════════════════════════════════

def print_header(title: str, sub: str = "") -> None:
    print()
    print(box_top())
    print(box_row("PRECURSOR ANALYSIS — EV09-WIND"))
    print(box_row(title))
    if sub:
        print(box_row(sub))
    print(box_bot())


def report_correlation() -> None:
    df = load_hourly_precursors()
    if df is None:
        return
    print_header("1 · KORELASI HARIAN",
                 "Hubungan variabel meteo vs ws10_max harian")

    daily = daily_aggregate(df)
    print(f"  N hari = {len(daily):,}\n")

    candidates = [
        ("pressure",  "Tekanan permukaan (hPa)"),
        ("temp_max",  "Suhu maks harian (°C)"),
        ("temp_min",  "Suhu min harian (°C)"),
        ("vpd_mean",  "VPD rata-rata (kPa)"),
        ("rad_sum",   "Radiasi total (W/m²·h)"),
        ("rh_mean",   "RH rata-rata (%)"),
        ("cloud_lo",  "Cloud rendah rata-rata (%)"),
    ]

    sec_header("KORELASI PEARSON (semua hari)")
    print(f"  {'Variabel':<32}{'r vs ws10_max':>15}{'N':>10}")
    print("  " + "─" * 58)
    for col, label in candidates:
        if col not in daily.columns:
            continue
        x = daily[col].values
        y = daily["ws10_max"].values
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() < 30:
            continue
        r = float(np.corrcoef(x[mask], y[mask])[0, 1])
        marker = ""
        if abs(r) > 0.4:
            marker = " ***"
        elif abs(r) > 0.2:
            marker = " **"
        elif abs(r) > 0.1:
            marker = " *"
        print(f"  {label:<32}{r:>+15.3f}{mask.sum():>10,}{marker}")
    print()
    print("  Signifikansi kasar: |r|>0.1 * ; >0.2 ** ; >0.4 ***")
    print()

    sec_header("KORELASI SETELAH DESEASONALISASI")
    print("  (anomali terhadap climatology bulanan)")
    print()
    print(f"  {'Variabel':<32}{'r vs ws10_max_anom':>20}")
    print("  " + "─" * 54)
    for col, label in candidates:
        col_anom = col + "_anom"
        if col_anom not in daily.columns:
            continue
        x = daily[col_anom].values
        y = daily["ws10_max_anom"].values
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() < 30:
            continue
        r = float(np.corrcoef(x[mask], y[mask])[0, 1])
        marker = ""
        if abs(r) > 0.4:
            marker = " ***"
        elif abs(r) > 0.2:
            marker = " **"
        elif abs(r) > 0.1:
            marker = " *"
        print(f"  {label:<32}{r:>+20.3f}{marker}")
    print()


def report_composite() -> None:
    df = load_hourly_precursors()
    if df is None:
        return
    print_header("2 · KOMPOSIT HARI EKSTREM vs HARI NORMAL",
                 "Perbandingan kondisi rata-rata")

    daily = daily_aggregate(df)
    thr = float(daily["ws10_max"].quantile(0.99))

    ext = daily[daily["ws10_max"] >= thr]
    norm = daily[daily["ws10_max"] < thr]

    print(f"  Ambang ekstrem (P99 ws10_max) = {thr:.2f} km/h")
    print(f"  N hari ekstrem = {len(ext):,}   "
          f"N hari normal = {len(norm):,}")
    print()

    metrics = [
        ("pressure", "Tekanan permukaan (hPa)"),
        ("temp_max", "Suhu maks harian (°C)"),
        ("temp_mean","Suhu rata-rata harian (°C)"),
        ("vpd_mean", "VPD rata-rata (kPa)"),
        ("vpd_max",  "VPD maks harian (kPa)"),
        ("rh_mean",  "RH rata-rata (%)"),
        ("rad_sum",  "Radiasi total (W/m²·h)"),
        ("rad_max",  "Radiasi maks (W/m²)"),
        ("cloud_lo", "Cloud rendah rata-rata (%)"),
        ("precip_sum","Hujan harian total (mm)"),
    ]

    sec_header("RATA-RATA PER KELOMPOK")
    print(f"  {'Variabel':<30}{'Ekstrem':>10}{'Normal':>10}{'Δ%':>8}")
    print("  " + "─" * 60)
    for col, label in metrics:
        if col not in daily.columns:
            continue
        e = ext[col].dropna()
        n = norm[col].dropna()
        if len(e) == 0 or len(n) == 0:
            continue
        em, nm = float(e.mean()), float(n.mean())
        delta_pct = (em - nm) / abs(nm) * 100 if abs(nm) > 1e-9 else 0.0
        print(f"  {label:<30}{em:>10.2f}{nm:>10.2f}{delta_pct:>+7.1f}%")
    print()
    print("  Δ% = (ekstrem − normal) / normal × 100%")
    print()

    sec_header("DISTRIBUSI — EKSTREM")
    print(f"  {'Variabel':<30}{'P10':>8}{'P50':>8}{'P90':>8}")
    print("  " + "─" * 56)
    for col, label in metrics[:8]:
        if col not in daily.columns:
            continue
        v = ext[col].dropna().values
        if len(v) == 0:
            continue
        print(f"  {label:<30}"
              f"{np.percentile(v, 10):>8.2f}"
              f"{np.percentile(v, 50):>8.2f}"
              f"{np.percentile(v, 90):>8.2f}")
    print()


def report_morning_precursor() -> None:
    df = load_hourly_precursors()
    if df is None:
        return
    print_header("3 · PRECURSOR PAGI (06:00–09:00)",
                 "Sinyal pagi untuk kejadian sore (12:00–16:00)")

    daily = daily_aggregate(df)
    morning = morning_signature(df)
    aft = afternoon_peak(df)

    merged = (morning.merge(aft, on="date", how="inner")
                     .merge(daily[["date", "month"]], on="date", how="left"))
    if len(merged) < 100:
        print("  [!] Data tidak cukup.")
        return

    print(f"  N hari = {len(merged):,}\n")

    # Definisi event: ws10_aft_max >= P99
    thr = float(merged["ws10_aft_max"].quantile(0.99))
    merged["is_event"] = merged["ws10_aft_max"] >= thr
    n_ev = int(merged["is_event"].sum())
    print(f"  Ambang event (P99 ws10 siang) = {thr:.2f} km/h")
    print(f"  N event = {n_ev}  ({n_ev / len(merged) * 100:.2f}% hari)\n")

    sec_header("KORELASI PAGI → SIANG")
    print(f"  {'Variabel pagi':<30}{'r vs ws10_aft_max':>20}")
    print("  " + "─" * 52)
    for col in ("ws10_morning", "pressure_morning", "temp_morning",
                 "rad_morning", "cloud_lo_morning", "vpd_morning",
                 "rh_morning"):
        if col not in merged.columns:
            continue
        x = merged[col].values
        y = merged["ws10_aft_max"].values
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() < 50:
            continue
        r = float(np.corrcoef(x[mask], y[mask])[0, 1])
        marker = ""
        if abs(r) > 0.4:
            marker = " ***"
        elif abs(r) > 0.2:
            marker = " **"
        elif abs(r) > 0.1:
            marker = " *"
        print(f"  {col:<30}{r:>+20.3f}{marker}")
    print()

    sec_header("RATA-RATA PAGI — HARI EVENT vs NON-EVENT")
    print(f"  {'Variabel pagi':<30}{'Event':>10}{'Non':>10}{'Δ%':>8}")
    print("  " + "─" * 60)
    for col in ("ws10_morning", "pressure_morning", "temp_morning",
                 "rad_morning", "cloud_lo_morning", "vpd_morning",
                 "rh_morning"):
        if col not in merged.columns:
            continue
        e = merged.loc[merged["is_event"], col].dropna()
        n = merged.loc[~merged["is_event"], col].dropna()
        if len(e) == 0 or len(n) == 0:
            continue
        em, nm = float(e.mean()), float(n.mean())
        delta_pct = (em - nm) / abs(nm) * 100 if abs(nm) > 1e-9 else 0.0
        print(f"  {col:<30}{em:>10.2f}{nm:>10.2f}{delta_pct:>+7.1f}%")
    print()


def report_contingency() -> None:
    df = load_hourly_precursors()
    if df is None:
        return
    print_header("4 · CONTINGENCY TABLE",
                 "Probabilitas event diberikan kondisi pagi")

    daily = daily_aggregate(df)
    morning = morning_signature(df)
    aft = afternoon_peak(df)
    merged = morning.merge(aft, on="date", how="inner")
    if len(merged) < 100:
        return

    thr = float(merged["ws10_aft_max"].quantile(0.99))
    merged["is_event"] = merged["ws10_aft_max"] >= thr

    base_rate = merged["is_event"].mean()
    print(f"  Base rate event = {base_rate * 100:.2f}%\n")

    conditions = [
        ("ws10_morning",  "P90", "Angin pagi ≥ P90"),
        ("pressure_morning", "P75", "Tekanan pagi ≥ P75"),
        ("pressure_morning", "P25", "Tekanan pagi ≤ P25"),
        ("temp_morning", "P75", "Suhu pagi ≥ P75"),
        ("cloud_lo_morning", "P25", "Cloud rendah pagi ≤ P25"),
        ("vpd_morning", "P75", "VPD pagi ≥ P75"),
        ("rad_morning", "P75", "Radiasi pagi ≥ P75"),
    ]

    sec_header("PROBABILITAS EVENT DIBERIKAN KONDISI PAGI")
    print(f"  {'Kondisi':<40}{'N':>8}{'P(event)':>10}{'Lift':>8}")
    print("  " + "─" * 68)
    for col, q, label in conditions:
        if col not in merged.columns:
            continue
        if q == "P90":
            thr_q = merged[col].quantile(0.90)
            cond = merged[col] >= thr_q
        elif q == "P75":
            thr_q = merged[col].quantile(0.75)
            cond = merged[col] >= thr_q
        else:  # P25
            thr_q = merged[col].quantile(0.25)
            cond = merged[col] <= thr_q
        sub = merged[cond]
        if len(sub) < 30:
            continue
        p_ev = sub["is_event"].mean()
        lift = p_ev / base_rate if base_rate > 0 else float("nan")
        print(f"  {label:<40}{len(sub):>8,}"
              f"{p_ev * 100:>9.2f}%"
              f"{lift:>7.2f}×")
    print()
    print("  Lift > 2 → kondisi ini meningkatkan probabilitas event 2× lipat.")
    print()


def report_autocorrelation() -> None:
    df = load_hourly_precursors()
    if df is None:
        return
    print_header("5 · AUTOCORRELATION WS10",
                 "Persistensi angin: berapa lama bertahan")

    v = df["ws10"].dropna().values
    n = len(v)
    if n < 1000:
        return

    sec_header("AUTOCORRELATION HINGGA 24 JAM")
    print(f"  {'Lag (jam)':<10}{'r':>8}   Bar")
    print("  " + "─" * 50)
    for lag in (1, 2, 3, 6, 12, 18, 24):
        if n - lag < 100:
            continue
        a = v[:-lag]
        b = v[lag:]
        mask = np.isfinite(a) & np.isfinite(b)
        if mask.sum() < 100:
            continue
        r = float(np.corrcoef(a[mask], b[mask])[0, 1])
        bar_n = int(round(abs(r) * 30))
        sign = "+" if r >= 0 else "−"
        print(f"  {lag:<10}{r:>+8.3f}   {sign}{'█' * bar_n}")
    print()
    print("  Interpretasi: r(lag=1) menunjukkan persistensi 1 jam ke depan.")
    print("  r(lag=3) > 0.7 → angin sangat persistent dalam 3 jam.")


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════

def main() -> int:
    df = load_hourly_precursors()
    if df is None:
        return 1
    report_correlation()
    report_composite()
    report_morning_precursor()
    report_contingency()
    report_autocorrelation()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Dihentikan.")
        sys.exit(0)