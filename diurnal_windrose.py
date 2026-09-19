#!/usr/bin/env python3
"""
diurnal_rose_generator.py
=========================

Generate data wind rose per slot jam (diurnal wind rose) dari arsip
Open-Meteo hourly P1+P2 untuk titik MJS.

Input  : open-meteo-7.49S112.54E28m_hourly10yr.csv  (P1)
         open-meteo-7.56S112.56E28m_hourly10yr.csv  (P2)
         — sesuai EV09wind.py DEFAULT_HOURLY_P1 / _P2
Output : diurnal_rose.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


# ══════════════════════════════════════════════════════════════════════
# KONSTANTA — nama file dari EV09wind.py
# ══════════════════════════════════════════════════════════════════════

DEFAULT_HOURLY_P1 = "open-meteo-7.49S112.54E28m_hourly10yr.csv"
DEFAULT_HOURLY_P2 = "open-meteo-7.56S112.56E28m_hourly10yr.csv"

TARGET_LAT: float = -7.521951
TARGET_LON: float = 112.566089
STATION_P1: Tuple[float, float] = (-7.486819, 112.538210)
STATION_P2: Tuple[float, float] = (-7.5571175, 112.557350)

SECTORS_8 = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
SPEED_BINS = (2.0, 5.0, 10.0)
BIN_LABELS = ("0–2", "2–5", "5–10", ">10")
BIN_COLORS = ("#67e8f9", "#6ee7b7", "#ffc266", "#fb923c")

SLOT_8_DEFS = (
    (0,  2, "00–02", "Dini hari"),
    (3,  5, "03–05", "Menjelang fajar"),
    (6,  8, "06–08", "Transisi pagi"),
    (9, 11, "09–11", "Pagi"),
    (12, 14, "12–14", "Tengah hari"),
    (15, 17, "15–17", "Sore"),
    (18, 20, "18–20", "Transisi senja"),
    (21, 23, "21–23", "Malam"),
)

SLOT_12_DEFS = (
    (0, 1, "00–01"), (2, 3, "02–03"), (4, 5, "04–05"),
    (6, 7, "06–07"), (8, 9, "08–09"), (10, 11, "10–11"),
    (12, 13, "12–13"), (14, 15, "14–15"), (16, 17, "16–17"),
    (18, 19, "18–19"), (20, 21, "20–21"), (22, 23, "22–23"),
)


def find_file(name: str) -> Optional[str]:
    """Cari file di cwd atau script dir."""
    for folder in (".", os.path.dirname(os.path.abspath(__file__))):
        p = os.path.join(folder, name)
        if os.path.exists(p):
            return p
    return None


def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0088
    p1, l1 = math.radians(lat1), math.radians(lon1)
    p2, l2 = math.radians(lat2), math.radians(lon2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2)
    return 2.0 * R * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def idw_weights(lat_t, lon_t, coords, power: float = 2.0):
    d = [haversine(c[0], lat_t, c[1], lon_t) for c in coords]
    raw = [1.0 / (x ** power) for x in d]
    s = sum(raw)
    return [r / s for r in raw]


def read_openmeteo(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as fh:
        skip = 0
        for i, line in enumerate(fh):
            if line.lstrip().startswith("time,"):
                skip = i
                break
    df = pd.read_csv(path, skiprows=skip)
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").reset_index(drop=True)


def find_col(df: pd.DataFrame, *patterns: str) -> Optional[str]:
    cols_lower = {c.lower(): c for c in df.columns}
    for p in patterns:
        pl = p.lower()
        for c_low, c_orig in cols_lower.items():
            if pl in c_low:
                return c_orig
    return None


def load_merged(p1_path: str, p2_path: str) -> Tuple[pd.DataFrame, float, float]:
    """IDW-merge P1+P2 → DataFrame[time, ws10, wd10, hour] + bobot."""
    df1 = read_openmeteo(p1_path)
    df2 = read_openmeteo(p2_path)

    c_ws1 = find_col(df1, "wind_speed_10m")
    c_wd1 = find_col(df1, "wind_direction_10m")
    c_ws2 = find_col(df2, "wind_speed_10m")
    c_wd2 = find_col(df2, "wind_direction_10m")

    if None in (c_ws1, c_wd1, c_ws2, c_wd2):
        raise RuntimeError("Kolom wind_speed_10m / wind_direction_10m "
                           "tidak ditemukan di CSV.")

    d1 = pd.DataFrame({
        "time": df1["time"],
        "ws10": df1[c_ws1].astype(float),
        "wd10": df1[c_wd1].astype(float),
    }).set_index("time")
    d2 = pd.DataFrame({
        "time": df2["time"],
        "ws10": df2[c_ws2].astype(float),
        "wd10": df2[c_wd2].astype(float),
    }).set_index("time")

    w1, w2 = idw_weights(TARGET_LAT, TARGET_LON, [STATION_P1, STATION_P2])
    idx = d1.index.union(d2.index)

    ws_out = pd.Series(np.nan, index=idx)
    v1 = d1["ws10"].reindex(idx)
    v2 = d2["ws10"].reindex(idx)
    both = v1.notna() & v2.notna()
    ws_out.loc[both] = w1 * v1[both] + w2 * v2[both]
    o1 = v1.notna() & ~v2.notna(); ws_out.loc[o1] = v1[o1]
    o2 = ~v1.notna() & v2.notna(); ws_out.loc[o2] = v2[o2]

    r1 = np.deg2rad(d1["wd10"].reindex(idx).values)
    r2 = np.deg2rad(d2["wd10"].reindex(idx).values)
    s_ = w1 * np.sin(r1) + w2 * np.sin(r2)
    c_ = w1 * np.cos(r1) + w2 * np.cos(r2)
    n1 = ~np.isfinite(r1); n2 = ~np.isfinite(r2)
    s_[n1 & ~n2] = np.sin(r2[n1 & ~n2]); c_[n1 & ~n2] = np.cos(r2[n1 & ~n2])
    s_[~n1 & n2] = np.sin(r1[~n1 & n2]); c_[~n1 & n2] = np.cos(r1[~n1 & n2])
    wd_out = (np.rad2deg(np.arctan2(s_, c_)) + 360.0) % 360.0

    out = pd.DataFrame({
        "time": idx,
        "ws10": ws_out.values,
        "wd10": wd_out,
    }).sort_values("time").reset_index(drop=True)
    out["hour"] = out["time"].dt.hour

    valid = np.isfinite(out["ws10"]) & np.isfinite(out["wd10"])
    out = out[valid].reset_index(drop=True)
    return out, w1, w2


def rose_for_subset(sub: pd.DataFrame, n_sectors: int = 8) -> Dict:
    wd = sub["wd10"].values
    ws = sub["ws10"].values
    N = len(wd)
    if N == 0:
        return {
            "N": 0,
            "freq": [[0.0] * 4 for _ in range(n_sectors)],
            "mean_speed": 0.0,
            "mean_dir": float("nan"),
            "constancy": 0.0,
        }

    width = 360.0 / n_sectors
    sectors = (((wd + width / 2.0) % 360.0) // width).astype(int) % n_sectors
    bins = np.digitize(ws, list(SPEED_BINS), right=False)

    freq = np.zeros((n_sectors, len(SPEED_BINS) + 1))
    for i in range(n_sectors):
        m = sectors == i
        if not m.any():
            continue
        for b in range(len(SPEED_BINS) + 1):
            freq[i, b] = (bins[m] == b).sum() / N * 100.0

    rad = np.deg2rad(wd)
    u = -np.sin(rad)
    v = -np.cos(rad)
    u_mean = float(np.mean(u))
    v_mean = float(np.mean(v))
    vec_spd = float(np.hypot(u_mean, v_mean))
    scalar_spd = float(np.mean(np.hypot(u, v)))
    constancy = vec_spd / scalar_spd if scalar_spd > 0 else 0.0
    mean_dir = float((np.rad2deg(np.arctan2(-u_mean, -v_mean)) + 360.0) % 360.0)

    return {
        "N": int(N),
        "freq": [[float(freq[i, b]) for b in range(freq.shape[1])]
                 for i in range(freq.shape[0])],
        "mean_speed": scalar_spd,
        "mean_dir": mean_dir,
        "constancy": constancy,
    }


def hourly_summary(df: pd.DataFrame) -> list:
    out = []
    for h in range(24):
        sub = df[df["hour"] == h]
        if len(sub) == 0:
            out.append({"hour": h, "N": 0,
                        "mean_speed": 0.0, "mean_dir": float("nan"),
                        "constancy": 0.0})
            continue
        rad = np.deg2rad(sub["wd10"].values)
        u = -np.sin(rad); v = -np.cos(rad)
        u_m = float(np.mean(u)); v_m = float(np.mean(v))
        vec = float(np.hypot(u_m, v_m))
        scalar = float(np.mean(np.hypot(u, v)))
        const = vec / scalar if scalar > 0 else 0.0
        mdir = float((np.rad2deg(np.arctan2(-u_m, -v_m)) + 360.0) % 360.0)
        out.append({
            "hour": h,
            "N": int(len(sub)),
            "mean_speed": scalar,
            "mean_dir": mdir,
            "constancy": const,
        })
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="diurnal_rose_generator")
    ap.add_argument("--p1", default=None)
    ap.add_argument("--p2", default=None)
    ap.add_argument("--out", default="diurnal_rose.json")
    args = ap.parse_args(argv)

    print("═" * 66)
    print("  DIURNAL WIND ROSE GENERATOR")
    print("  Titik: −7.521951°LS, 112.566089°BT")
    print("═" * 66)

    p1 = args.p1 or find_file(DEFAULT_HOURLY_P1)
    p2 = args.p2 or find_file(DEFAULT_HOURLY_P2)

    if p1 is None or p2 is None:
        print(f"[!] Tidak menemukan:")
        print(f"      {DEFAULT_HOURLY_P1}")
        print(f"      {DEFAULT_HOURLY_P2}")
        return 1

    print(f"  P1 : {p1}")
    print(f"  P2 : {p2}")
    print()

    df, w1, w2 = load_merged(p1, p2)
    print(f"  Merge       : {len(df):,} baris hourly valid")
    print(f"  Rentang     : {df['time'].min().date()} → {df['time'].max().date()}")
    print(f"  Bobot IDW   : w1={w1:.6f}  w2={w2:.6f}")
    print()

    out: Dict = {
        "meta": {
            "n_rows": int(len(df)),
            "start": str(df["time"].min().date()),
            "end": str(df["time"].max().date()),
            "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "target_lat": TARGET_LAT,
            "target_lon": TARGET_LON,
            "idw_w1": round(w1, 6),
            "idw_w2": round(w2, 6),
            "sectors": list(SECTORS_8),
            "bin_labels": list(BIN_LABELS),
            "bin_colors": list(BIN_COLORS),
        },
        "slots_8": [],
        "slots_12": [],
        "composite": None,
        "hourly": [],
    }

    print("── Slot 8 × 3 jam " + "─" * 46)
    for slot_id, (h0, h1, lbl, lbl_id) in enumerate(SLOT_8_DEFS):
        sub = df[(df["hour"] >= h0) & (df["hour"] <= h1)]
        r = rose_for_subset(sub, n_sectors=8)
        out["slots_8"].append({
            "slot_id": slot_id, "hour_start": h0, "hour_end": h1,
            "label": lbl, "label_id": lbl_id, **r,
        })
        print(f"  [{slot_id}] {lbl}  {lbl_id:<18} "
              f"N={r['N']:>7,}  dir={r['mean_dir']:>5.1f}°  "
              f"spd={r['mean_speed']:.2f}  const={r['constancy']:.3f}")

    print()
    print("── Slot 12 × 2 jam " + "─" * 45)
    for slot_id, (h0, h1, lbl) in enumerate(SLOT_12_DEFS):
        sub = df[(df["hour"] >= h0) & (df["hour"] <= h1)]
        r = rose_for_subset(sub, n_sectors=8)
        out["slots_12"].append({
            "slot_id": slot_id, "hour_start": h0, "hour_end": h1,
            "label": lbl, **r,
        })
        print(f"  [{slot_id:>2}] {lbl}  N={r['N']:>7,}  "
              f"dir={r['mean_dir']:>5.1f}°  spd={r['mean_speed']:.2f}")

    out["composite"] = rose_for_subset(df, n_sectors=8)
    out["hourly"] = hourly_summary(df)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    kb = os.path.getsize(args.out) / 1024
    print()
    print("═" * 66)
    print(f"  ✓ Output: {args.out}  ({kb:.1f} KB)")
    print("═" * 66)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Dibatalkan.")
        sys.exit(0)