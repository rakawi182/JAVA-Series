#!/usr/bin/env python3
"""
Pranata Mangsa — Wind Analysis Module (EV09-WIND)
==================================================

Hourly wind, precipitation and cloud diagnostics for the MJS observation
point (−7.5220°S, 112.5661°E, 28 m a.s.l.), built on the same Open-Meteo
ERA5/ERA5-Land/IFS-HRES hourly archives used by Pranatamangsa_EV09.

Scope
-----
  1. Wind Rose & Monthly Statistics         (16-sector × 4 speed-bin)
  2. Diurnal Cycle & Sea-Breeze Diagnostics (hour × month heatmap)
  3. Gust Factor Analysis                   (GF, exceedance, diurnal)
  4. Vertical Shear 10m↔100m                (Hellmann exponent α)
  5. Directional Persistence                (run-length + Markov matrix)
  6. Pranatamangsa Wind Profile             (12 mangsa, R30 dopy ranges)
  7. Wind ↔ Rain ↔ Cloud Coupling           (composite, lag-corr, onset)
  8. Monsoon Reversal Detection             (per pranata-year, trend)

Data source
-----------
  CSV 1: open-meteo-7.49S112.54E28m_hourly10yr.csv  (P1)
  CSV 2: open-meteo-7.56S112.56E28m_hourly10yr.csv  (P2)

Both files are ~102,576 hourly rows spanning 2015-01-01 → 2026-09-13.
IDW-merging uses Haversine distance with p=2 → w1≈0.395, w2≈0.605
(matches the EV06b VPD weight set in the parent module).  Directional
fields are merged via unit-vector averaging, NOT scalar average.

Lag convention (canonical — see Section 8)
-------------------------------------------
    profile[L] = corr( base.shift(L), target )
    Positive L ⇒ BASE LEADS TARGET by L samples.

Self-tested by _self_test_lag_convention() at program entry; any change
to `.shift()` direction MUST re-run the self-test.

Monsoon reversal detection (Report 8)
--------------------------------------
The reversal of the low-level wind from easterly (East monsoon) to
westerly (West monsoon) is detected from the westerly wind component

    u_comp[t] = −sin( wd10[t] · π/180 )        u > 0 ⇒ wind FROM west

via a 30-day rolling mean, with two strict conditions:

  (1) The crossing of u=0 must occur inside the search window
      dopy ∈ [60, 200]  (≈ 21 Aug → 8 Jan) — the physically plausible
      interval for the reversal at this site.

  (2) The signal must remain ≥ −0.005 for at least 15 consecutive days
      after the crossing (sustain check).

Without the window restriction the detector produces false positives
at dopy ≈ 290 (March, East-monsoon onset) in years where the West
monsoon is weak (El Niño years 2015, 2019, 2023).

Design note
-----------
Self-contained — does not import from Pranatamangsa_EV09 — so it can be
shipped and run independently.  The mangsa boundary table
(R30_DOPY_RANGES) is duplicated verbatim from EV09; if EV09's scenario
calibration is updated, mirror the change here.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import textwrap
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:                                       # pragma: no cover
    HAS_PANDAS = False


# ══════════════════════════════════════════════════════════════════════════
# Section 1 · Constants
# ══════════════════════════════════════════════════════════════════════════

W: int = 70
IND: str = "  "

MONTH_SHORT: Dict[int, str] = {
    1: "Jan",  2: "Feb",  3: "Mar",  4: "Apr",  5: "Mei",  6: "Jun",
    7: "Jul",  8: "Agu",  9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
}

TARGET_LAT: float = -7.521951
TARGET_LON: float = 112.566089
STATION_P1: Tuple[float, float] = (-7.486819, 112.538210)
STATION_P2: Tuple[float, float] = (-7.5571175, 112.557350)

DEFAULT_HOURLY_P1 = "open-meteo-7.49S112.54E28m_hourly10yr.csv"
DEFAULT_HOURLY_P2 = "open-meteo-7.56S112.56E28m_hourly10yr.csv"

SECTOR_NAMES_8: Tuple[str, ...] = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
SECTOR_NAMES_16: Tuple[str, ...] = (
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
)
SECTOR_NAMES_4: Tuple[str, ...] = ("N", "E", "S", "W")

# Wind rose speed bins (km/h)  → bins: [0,2), [2,5), [5,10), [10,∞)
SPEED_BINS: Tuple[float, ...] = (2.0, 5.0, 10.0)
SPEED_BIN_LABELS: Tuple[str, ...] = ("0–2", "2–5", "5–10", ">10")

# Char-ramp used by all heatmaps
HEAT_CHARS: str = " ·░▒▓█"

# Mangsa table (matches EV09 MANGSAS)
MANGSAS_INFO: Tuple[Tuple[int, str, str], ...] = (
    ( 1, "Kasa",     "Katiga"),
    ( 2, "Karo",     "Katiga"),
    ( 3, "Katiga",   "Katiga"),
    ( 4, "Kapat",    "Labuh"),
    ( 5, "Kalima",   "Labuh"),
    ( 6, "Kanem",    "Labuh"),
    ( 7, "Kapitu",   "Rendheng"),
    ( 8, "Kawolu",   "Rendheng"),
    ( 9, "Kasanga",  "Rendheng"),
    (10, "Kasadasa", "Mareng"),
    (11, "Desta",    "Mareng"),
    (12, "Sada",     "Mareng"),
)

# R30 dopy ranges — verbatim from EV09 R30_DOPY_RANGES
R30_DOPY_RANGES: Dict[int, Tuple[float, float]] = {
     1: ( 19.00,  53.94),  2: ( 53.94,  73.55),  3: ( 73.55,  94.00),
     4: ( 94.00, 124.00),  5: (124.00, 156.40),  6: (156.40, 208.00),
     7: (208.00, 243.68),  8: (243.68, 265.26),  9: (265.26, 286.00),
    10: (286.00, 312.73), 11: (312.73, 338.34), 12: (338.34, 384.00),
}

MUSIM_MEMBERS: Dict[str, Tuple[int, ...]] = {
    "Katiga":   (1, 2, 3),
    "Labuh":    (4, 5, 6),
    "Rendheng": (7, 8, 9),
    "Mareng":  (10, 11, 12),
}
MUSIM_ORDER: Tuple[str, ...] = ("Katiga", "Labuh", "Rendheng", "Mareng")

ANCHOR_MONTH: int = 6
ANCHOR_DAY: int = 22

# Monsoon-reversal detection parameters (Report 8)
MR_WINDOW: Tuple[float, float] = (60.0, 200.0)   # dopy search window
MR_ROLL_WIN: int = 30                            # days
MR_SUSTAIN: int = 15                             # days
MR_EPS: float = 0.005                            # tolerance around 0
MR_THRESHOLD: float = 0.0                        # crossing threshold u=0
MR_OUTLIER_Z: float = 2.0                        # z-cutoff for outliers

# Labuh start per scenario (for reporting relative offset in Report 8)
SCENARIO_LABUH_DOPY: Dict[str, float] = {
    "TRAD":   112.0,
    "R30":     94.0,
    "R10":    131.0,
    "ALL":     91.0,
    "ELNINO": 133.0,
    "LANINA":  79.0,
    "NETRAL": 102.0,
}


# ══════════════════════════════════════════════════════════════════════════
# Section 2 · Presentation primitives
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
    cw = W - 6
    lines: List[str] = []
    for raw in str(text).splitlines() or [""]:
        if len(raw) <= cw:
            lines.append("║  " + raw + " " * (cw - len(raw)) + "  ║")
        else:
            lines.extend(
                "║  " + ln + " " * (cw - len(ln)) + "  ║"
                for ln in textwrap.wrap(raw, width=cw)
            )
    return "\n".join(lines)


def thin_hbar(indent: int = 2) -> str:
    return " " * indent + "─" * (W - indent)


def sec_header(label: str, sub: str = "") -> None:
    title = f"▌▌ {label.upper()}"
    if sub:
        title += f" — {sub}"
    print()
    print(title)
    print(thin_hbar(0))


def wprint(label: str, value: str, lw: int = 12, indent: int = 6) -> None:
    pre = " " * indent + f"{label:<{lw}}: "
    sub = " " * (indent + lw + 2)
    print(textwrap.fill(value, width=W,
                        initial_indent=pre, subsequent_indent=sub))


# ══════════════════════════════════════════════════════════════════════════
# Section 3 · Data ingestion
# ══════════════════════════════════════════════════════════════════════════

def find_data_file(filename: str) -> Optional[str]:
    """Search cwd and script dir for a data file."""
    if not filename:
        return None
    for folder in (".", os.path.dirname(os.path.abspath(__file__))):
        p = os.path.join(folder, filename)
        if os.path.exists(p):
            return p
    return None


def _read_openmeteo_csv(path: str) -> "pd.DataFrame":
    """Read Open-Meteo CSV, auto-detect header via 'time,' signature."""
    with open(path, "r", encoding="utf-8") as fh:
        skip = 0
        for i, line in enumerate(fh):
            if line.lstrip().startswith("time,"):
                skip = i
                break
    df = pd.read_csv(path, skiprows=skip)
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").reset_index(drop=True)


def _find_col(df: "pd.DataFrame", *patterns: str) -> Optional[str]:
    """Return first column matching any case-insensitive substring."""
    cols_lower = {c.lower(): c for c in df.columns}
    for p in patterns:
        pl = p.lower()
        for c_low, c_orig in cols_lower.items():
            if pl in c_low:
                return c_orig
    return None


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    p1, l1 = math.radians(lat1), math.radians(lon1)
    p2, l2 = math.radians(lat2), math.radians(lon2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2)
    return 2.0 * R * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def idw_weights(
    lat_t: float, lon_t: float,
    coords: Sequence[Tuple[float, float]],
    power: float = 2.0,
) -> List[float]:
    """Haversine-based IDW weights (normalised)."""
    dists = [_haversine(c[0], lat_t, c[1], lon_t) for c in coords]
    raw = [1.0 / (d ** power) for d in dists]
    s = sum(raw)
    return [r / s for r in raw]


def _extract_wind_cols(df: "pd.DataFrame") -> "pd.DataFrame":
    """Rename the raw Open-Meteo wind columns to canonical short names."""
    out = pd.DataFrame()
    out["time"] = df["time"]
    for short, patterns in (
        ("ws10",   ("wind_speed_10m",)),
        ("wd10",   ("wind_direction_10m",)),
        ("gust10", ("wind_gusts_10m",)),
        ("ws100",  ("wind_speed_100m",)),
        ("wd100",  ("wind_direction_100m",)),
    ):
        col = _find_col(df, *patterns)
        out[short] = df[col].astype(float) if col is not None else np.nan
    return out


def _extract_met_cols(df: "pd.DataFrame") -> "pd.DataFrame":
    """Extract precipitation + cloud columns from an Open-Meteo CSV.

    `cloud_cover (%)` (total) is matched by EXACT name only — a substring
    match would wrongly grab `cloud_cover_low (%)`.
    """
    out = pd.DataFrame()
    out["time"] = df["time"]
    spec = (
        ("precip",    "precipitation (mm)",  "precipitation"),
        ("cloud",     "cloud_cover (%)",     None),
        ("cloud_lo",  "cloud_cover_low (%)",  "cloud_cover_low"),
        ("cloud_mid", "cloud_cover_mid (%)",  "cloud_cover_mid"),
        ("cloud_hi",  "cloud_cover_high (%)", "cloud_cover_high"),
    )
    for short, exact, sub in spec:
        col: Optional[str] = None
        if exact in df.columns:
            col = exact
        elif sub:
            col = _find_col(df, sub)
        out[short] = df[col].astype(float) if col is not None else np.nan
    return out


def load_hourly_full(
    csv_p1: str = DEFAULT_HOURLY_P1,
    csv_p2: str = DEFAULT_HOURLY_P2,
    lat_t: float = TARGET_LAT, lon_t: float = TARGET_LON,
) -> Optional["pd.DataFrame"]:
    """Load hourly wind + precipitation + cloud, IDW-merged onto target.

    Scalar fields use arithmetic IDW.  Directional fields use unit-vector
    IDW (circular-safe).  Single-station fallback picks whichever file is
    present.
    """
    if not HAS_PANDAS:
        return None
    p1, p2 = find_data_file(csv_p1), find_data_file(csv_p2)
    if p1 is None and p2 is None:
        return None

    def _read(path: str) -> "pd.DataFrame":
        raw = _read_openmeteo_csv(path)
        wind = _extract_wind_cols(raw)
        met = _extract_met_cols(raw).drop(columns=["time"])
        return pd.concat([wind, met], axis=1)

    if p1 is None:
        return _read(p2).sort_values("time").reset_index(drop=True)
    if p2 is None:
        return _read(p1).sort_values("time").reset_index(drop=True)

    d1 = _read(p1).set_index("time")
    d2 = _read(p2).set_index("time")
    w1, w2 = idw_weights(lat_t, lon_t, [STATION_P1, STATION_P2])
    idx = d1.index.union(d2.index)
    out = pd.DataFrame(index=idx)

    scalar_cols = ("ws10", "gust10", "ws100",
                   "precip", "cloud", "cloud_lo", "cloud_mid", "cloud_hi")
    for col in scalar_cols:
        if col not in d1.columns and col not in d2.columns:
            out[col] = np.nan
            continue
        v1 = (d1[col].reindex(idx) if col in d1.columns
              else pd.Series(np.nan, index=idx))
        v2 = (d2[col].reindex(idx) if col in d2.columns
              else pd.Series(np.nan, index=idx))
        s = pd.Series(np.nan, index=idx)
        both = v1.notna() & v2.notna()
        s.loc[both] = w1 * v1[both] + w2 * v2[both]
        o1 = v1.notna() & ~v2.notna();  s.loc[o1] = v1[o1]
        o2 = ~v1.notna() & v2.notna();  s.loc[o2] = v2[o2]
        out[col] = s

    for src in ("wd10", "wd100"):
        if src not in d1.columns and src not in d2.columns:
            out[src] = np.nan
            continue
        r1 = (np.deg2rad(d1[src].reindex(idx).values)
              if src in d1.columns else np.full(len(idx), np.nan))
        r2 = (np.deg2rad(d2[src].reindex(idx).values)
              if src in d2.columns else np.full(len(idx), np.nan))
        s_ = w1 * np.sin(r1) + w2 * np.sin(r2)
        c_ = w1 * np.cos(r1) + w2 * np.cos(r2)
        n1 = ~np.isfinite(r1);  n2 = ~np.isfinite(r2)
        s_[n1 & ~n2] = np.sin(r2[n1 & ~n2]); c_[n1 & ~n2] = np.cos(r2[n1 & ~n2])
        s_[~n1 & n2] = np.sin(r1[~n1 & n2]); c_[~n1 & n2] = np.cos(r1[~n1 & n2])
        out[src] = (np.rad2deg(np.arctan2(s_, c_)) + 360.0) % 360.0

    out = out.reset_index().rename(columns={"index": "time"})
    return out.sort_values("time").reset_index(drop=True)


def attach_time_features(df: "pd.DataFrame") -> "pd.DataFrame":
    """Add hour, month, year, dopy, mangsa, u_comp, v_comp columns."""
    df = df.copy()
    t = pd.to_datetime(df["time"])
    df["hour"]  = t.dt.hour
    df["month"] = t.dt.month
    df["year"]  = t.dt.year

    anchor = pd.to_datetime(dict(year=t.dt.year, month=ANCHOR_MONTH,
                                  day=ANCHOR_DAY))
    anchor_prev = pd.to_datetime(dict(year=t.dt.year - 1, month=ANCHOR_MONTH,
                                       day=ANCHOR_DAY))
    before = t < anchor
    df["dopy"]  = np.where(before,
                            (t - anchor_prev).dt.total_seconds() / 86400.0,
                            (t - anchor).dt.total_seconds() / 86400.0)
    df["dopy"] = df["dopy"] % 365.0

    df["mangsa"] = df["dopy"].apply(_dopy_to_mangsa_no)

    # Meteorological wind components.
    # wd10 is the direction wind blows FROM, so:
    #     u = −speed·sin(wd)  → u > 0 means wind FROM west (westerly)
    #     v = −speed·cos(wd)  → v > 0 means wind FROM south (southerly)
    if "wd10" in df.columns:
        rad = np.deg2rad(df["wd10"].values)
        df["u_comp"] = -np.sin(rad)
        df["v_comp"] = -np.cos(rad)
    return df


def _dopy_to_mangsa_no(dopy: float) -> Optional[int]:
    """Map a dopy value to its R30 mangsa number (12 wraps)."""
    dopy = dopy % 365.0
    for no, (rs, re) in R30_DOPY_RANGES.items():
        if no == 12:
            if dopy >= rs or dopy < (re - 365.0):
                return 12
        else:
            if rs <= dopy < re:
                return no
    return None


# ══════════════════════════════════════════════════════════════════════════
# Section 4 · Circular statistics
# ══════════════════════════════════════════════════════════════════════════

def circ_mean_deg(theta_deg: np.ndarray) -> float:
    r = np.deg2rad(theta_deg[np.isfinite(theta_deg)])
    if len(r) == 0:
        return float("nan")
    s, c = np.sin(r).mean(), np.cos(r).mean()
    return float((np.rad2deg(np.arctan2(s, c)) + 360.0) % 360.0)


def circ_R(theta_deg: np.ndarray) -> float:
    """Resultant length R ∈ [0,1] — 0 = uniform, 1 = mono-directional."""
    r = np.deg2rad(theta_deg[np.isfinite(theta_deg)])
    if len(r) == 0:
        return float("nan")
    return float(np.hypot(np.sin(r).mean(), np.cos(r).mean()))


def circ_std_deg(theta_deg: np.ndarray) -> float:
    """Circular standard deviation (deg)."""
    R = circ_R(theta_deg)
    if not np.isfinite(R) or R <= 0:
        return float("nan")
    return float(np.rad2deg(np.sqrt(-2.0 * np.log(R))))


def circ_diff_deg(a: float, b: float) -> float:
    """Signed smallest angular difference a−b ∈ (−180, 180]."""
    return float((a - b + 180.0) % 360.0 - 180.0)


# ══════════════════════════════════════════════════════════════════════════
# Section 5 · Wind analysis kernels (reports 1–6)
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class WindRoseResult:
    sector_freq: np.ndarray
    total: int
    n_sectors: int
    n_bins: int


def wind_rose(
    df: "pd.DataFrame",
    n_sectors: int = 16,
    speed_bins: Sequence[float] = SPEED_BINS,
) -> WindRoseResult:
    """Directional frequency × speed-bin distribution (% of samples)."""
    wd = df["wd10"].values
    ws = df["ws10"].values
    valid = np.isfinite(wd) & np.isfinite(ws)
    wd, ws = wd[valid], ws[valid]
    total = len(wd)
    if total == 0:
        return WindRoseResult(np.zeros((n_sectors, len(speed_bins) + 1)),
                              0, n_sectors, len(speed_bins) + 1)
    width = 360.0 / n_sectors
    sectors = (((wd + width / 2.0) % 360.0) // width).astype(int) % n_sectors
    bins = np.digitize(ws, list(speed_bins), right=False)
    freq = np.zeros((n_sectors, len(speed_bins) + 1))
    for i in range(n_sectors):
        mask = sectors == i
        if not mask.any():
            continue
        for b in range(len(speed_bins) + 1):
            freq[i, b] = (bins[mask] == b).sum() / total * 100.0
    return WindRoseResult(freq, total, n_sectors, len(speed_bins) + 1)


def monthly_stats(df: "pd.DataFrame") -> Dict[int, Dict[str, float]]:
    """Per-month wind statistics (scalar + circular)."""
    out: Dict[int, Dict[str, float]] = {}
    for m in range(1, 13):
        sub = df[df["month"] == m]
        ws = sub["ws10"].values
        wd = sub["wd10"].values
        gust = sub["gust10"].values
        ws_c = ws[np.isfinite(ws)]
        wd_c = wd[np.isfinite(wd)]
        gust_c = gust[np.isfinite(gust)]
        out[m] = {
            "n":     int(len(ws_c)),
            "mean":  float(np.mean(ws_c)) if len(ws_c) else float("nan"),
            "p10":   float(np.percentile(ws_c, 10)) if len(ws_c) else float("nan"),
            "p50":   float(np.percentile(ws_c, 50)) if len(ws_c) else float("nan"),
            "p90":   float(np.percentile(ws_c, 90)) if len(ws_c) else float("nan"),
            "max":   float(np.max(ws_c)) if len(ws_c) else float("nan"),
            "gust_mean": float(np.mean(gust_c)) if len(gust_c) else float("nan"),
            "gust_max":  float(np.max(gust_c)) if len(gust_c) else float("nan"),
            "dir":   circ_mean_deg(wd_c),
            "R":     circ_R(wd_c),
            "cstd":  circ_std_deg(wd_c),
        }
    return out


def seasonal_rose(df: "pd.DataFrame") -> Dict[str, WindRoseResult]:
    """Wind rose per DJF/MAM/JJA/SON."""
    seasons = {
        "DJF": (12, 1, 2), "MAM": (3, 4, 5),
        "JJA": (6, 7, 8), "SON": (9, 10, 11),
    }
    return {s: wind_rose(df[df["month"].isin(ms)], n_sectors=8)
            for s, ms in seasons.items()}


def diurnal_matrix(df: "pd.DataFrame", field: str = "ws10"
                   ) -> Tuple[np.ndarray, np.ndarray]:
    """Return (mean_matrix[24,12], count_matrix[24,12]) for a field."""
    hour = df["hour"].values
    month = df["month"].values
    vals = df[field].values
    valid = np.isfinite(vals)
    s = np.zeros((24, 12))
    n = np.zeros((24, 12))
    for h, m, v in zip(hour[valid], month[valid], vals[valid]):
        s[h, m - 1] += v
        n[h, m - 1] += 1
    with np.errstate(invalid="ignore"):
        mean = np.where(n > 0, s / n, np.nan)
    return mean, n


def diurnal_direction(df: "pd.DataFrame") -> np.ndarray:
    """Circular-mean direction per hour (24,)."""
    out = np.full(24, np.nan)
    for h in range(24):
        sub = df[df["hour"] == h]["wd10"].values
        out[h] = circ_mean_deg(sub)
    return out


def gust_stats(df: "pd.DataFrame") -> Dict[str, np.ndarray]:
    """Gust factor = gust / speed, restricted to speed ≥ 1 km/h."""
    ws = df["ws10"].values
    gs = df["gust10"].values
    valid = np.isfinite(ws) & np.isfinite(gs) & (ws >= 1.0)
    gf = gs[valid] / ws[valid]
    exceedances = {}
    for thr in (15, 20, 25, 30, 40):
        exceedances[thr] = float((gs[np.isfinite(gs)] > thr).mean() * 100.0)
    return {
        "gf":              gf,
        "mean":            float(np.mean(gf)) if len(gf) else float("nan"),
        "p50":             float(np.percentile(gf, 50)) if len(gf) else float("nan"),
        "p90":             float(np.percentile(gf, 90)) if len(gf) else float("nan"),
        "p99":             float(np.percentile(gf, 99)) if len(gf) else float("nan"),
        "exceedance_pct":  exceedances,
    }


def shear_exponent(df: "pd.DataFrame") -> np.ndarray:
    """Hellmann exponent α = ln(V100/V10) / ln(100/10)."""
    v10 = df["ws10"].values
    v100 = df["ws100"].values
    valid = np.isfinite(v10) & np.isfinite(v100) & (v10 > 0.5) & (v100 > 0.5)
    ratio = v100[valid] / v10[valid]
    return np.log(np.maximum(ratio, 1e-6)) / np.log(10.0)


def directional_shear(df: "pd.DataFrame") -> np.ndarray:
    """|Δθ| between 10m and 100m (deg, wrapped into [0, 180])."""
    d10 = df["wd10"].values
    d100 = df["wd100"].values
    valid = np.isfinite(d10) & np.isfinite(d100)
    diff = np.abs(((d100[valid] - d10[valid] + 180.0) % 360.0) - 180.0)
    return diff


def persistence_runs(
    df: "pd.DataFrame", n_sectors: int = 8,
) -> Dict[int, np.ndarray]:
    """Per-sector run-length distribution (consecutive hourly samples)."""
    wd = df["wd10"].values
    ws = df["ws10"].values
    valid = np.isfinite(wd) & np.isfinite(ws) & (ws >= 1.0)
    wd = wd[valid]
    width = 360.0 / n_sectors
    sectors = (((wd + width / 2.0) % 360.0) // width).astype(int) % n_sectors

    runs: Dict[int, List[int]] = {i: [] for i in range(n_sectors)}
    if len(sectors) == 0:
        return {i: np.array([]) for i in range(n_sectors)}
    cur = sectors[0]
    length = 1
    for s in sectors[1:]:
        if s == cur:
            length += 1
        else:
            runs[cur].append(length)
            cur, length = s, 1
    runs[cur].append(length)
    return {i: np.array(v, dtype=float) for i, v in runs.items()}


def sector_transition_matrix(
    df: "pd.DataFrame", n_sectors: int = 8,
) -> np.ndarray:
    """Row-normalised transition probability between direction sectors."""
    wd = df["wd10"].values
    ws = df["ws10"].values
    valid = np.isfinite(wd) & np.isfinite(ws) & (ws >= 1.0)
    wd = wd[valid]
    if len(wd) < 2:
        return np.zeros((n_sectors, n_sectors))
    width = 360.0 / n_sectors
    sectors = (((wd + width / 2.0) % 360.0) // width).astype(int) % n_sectors
    M = np.zeros((n_sectors, n_sectors))
    for a, b in zip(sectors[:-1], sectors[1:]):
        M[a, b] += 1
    row = M.sum(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        M = np.where(row > 0, M / row, 0.0)
    return M


def mangsa_wind_profile(df: "pd.DataFrame") -> Dict[int, Dict[str, float]]:
    """Per-mangsa (R30 dopy) aggregated wind statistics."""
    out: Dict[int, Dict[str, float]] = {}
    for no, nama, musim in MANGSAS_INFO:
        sub = df[df["mangsa"] == no]
        ws = sub["ws10"].values
        wd = sub["wd10"].values
        gust = sub["gust10"].values
        ws_c = ws[np.isfinite(ws)]
        wd_c = wd[np.isfinite(wd)]
        gust_c = gust[np.isfinite(gust)]
        gf_mask = (np.isfinite(sub["ws10"].values)
                   & np.isfinite(sub["gust10"].values)
                   & (sub["ws10"].values >= 1.0))
        gf = (sub["gust10"].values[gf_mask]
              / sub["ws10"].values[gf_mask]) if gf_mask.any() else np.array([])
        out[no] = {
            "nama":   nama,
            "musim":  musim,
            "n":      int(len(ws_c)),
            "mean":   float(np.mean(ws_c)) if len(ws_c) else float("nan"),
            "p90":    float(np.percentile(ws_c, 90)) if len(ws_c) else float("nan"),
            "max":    float(np.max(ws_c)) if len(ws_c) else float("nan"),
            "dir":    circ_mean_deg(wd_c),
            "R":      circ_R(wd_c),
            "gust":   float(np.mean(gust_c)) if len(gust_c) else float("nan"),
            "gf":     float(np.mean(gf)) if len(gf) else float("nan"),
        }
    return out


# ══════════════════════════════════════════════════════════════════════════
# Section 6 · Text chart primitives
# ══════════════════════════════════════════════════════════════════════════

def _heat_index(v: float, vmin: float, vmax: float, n_levels: int) -> int:
    if not np.isfinite(v) or vmax <= vmin:
        return 0
    frac = (v - vmin) / (vmax - vmin)
    return max(0, min(n_levels - 1, int(round(frac * (n_levels - 1)))))


def render_wind_rose(rose: WindRoseResult, label: str = "") -> None:
    if rose.total == 0:
        print("  (tidak ada data)")
        return
    names = {
        4: SECTOR_NAMES_4, 8: SECTOR_NAMES_8, 16: SECTOR_NAMES_16,
    }[rose.n_sectors]
    n_bins = rose.n_bins
    print(f"  ── Wind Rose {label}  (N = {rose.total:,}) ──")
    print()
    hdr = f"  {'Dir':<5}" + "".join(f"{lbl:>7}" for lbl in SPEED_BIN_LABELS[:n_bins])
    hdr += f"  {'Total':>7}  Bar"
    print(hdr)
    print("  " + "─" * (min(len(hdr), W - 4)))
    totals = rose.sector_freq.sum(axis=1)
    max_t = float(totals.max()) if len(totals) else 1.0
    for i, name in enumerate(names):
        row = f"  {name:<5}"
        for b in range(n_bins):
            row += f"{rose.sector_freq[i, b]:>7.2f}"
        t = totals[i]
        bar_n = int(round(18 * t / max_t)) if max_t > 0 else 0
        row += f"  {t:>7.2f}  {'█' * bar_n}"
        print(row[:W])
    print()


def render_heatmap(
    mat: np.ndarray,
    row_labels: Sequence[str],
    col_labels: Sequence[str],
    title: str = "",
    fmt_value: str = "{:.2f}",
    row_label_w: int = 5,
) -> None:
    """2-char cell heatmap. mat may contain NaN (renders as blank)."""
    finite = mat[np.isfinite(mat)]
    if len(finite) == 0:
        print("  (tidak ada data)")
        return
    vmin, vmax = float(finite.min()), float(finite.max())
    n_rows, n_cols = mat.shape
    n_levels = len(HEAT_CHARS)

    if title:
        print(f"  ── {title} ──")
        print()
    hdr = " " * (row_label_w + 3) + "".join(f"{c:>6}" for c in col_labels)
    print(hdr[:W])
    print("  " + "─" * (min(len(hdr) - 2, W - 4)))
    for i, rlab in enumerate(row_labels):
        row = f"  {rlab:<{row_label_w}} "
        for j in range(n_cols):
            v = mat[i, j]
            if not np.isfinite(v):
                row += "     ·"
                continue
            idx = _heat_index(v, vmin, vmax, n_levels)
            row += f"    {HEAT_CHARS[idx]}{HEAT_CHARS[idx]}"
        print(row[:W])
    print()
    print(f"  Ramp: {HEAT_CHARS[1]}={fmt_value.format(vmin)}  "
          f"{HEAT_CHARS[-1]}={fmt_value.format(vmax)}")
    print()


# ══════════════════════════════════════════════════════════════════════════
# Section 7 · Report generators 1–6
# ══════════════════════════════════════════════════════════════════════════

_FULL_CACHE: Optional["pd.DataFrame"] = None


def _require_data() -> Optional["pd.DataFrame"]:
    """Cached unified loader: wind + precip + cloud + time features.

    Single source of truth — all reports share this one cached DataFrame.
    """
    global _FULL_CACHE
    if _FULL_CACHE is not None:
        return _FULL_CACHE
    if not HAS_PANDAS:
        print("  [!] pandas tidak tersedia — modul angin tidak bisa jalan.")
        return None
    df = load_hourly_full()
    if df is None or len(df) == 0:
        print("  [!] File hourly10yr P1/P2 tidak ditemukan.")
        print(f"      Cari: {DEFAULT_HOURLY_P1}")
        print(f"            {DEFAULT_HOURLY_P2}")
        return None
    df = attach_time_features(df)
    print(f"  [i] {len(df):,} baris hourly  ·  "
          f"{df['time'].min().date()} → {df['time'].max().date()}")
    _FULL_CACHE = df
    return df


def print_header(title: str, subtitle: str = "") -> None:
    print()
    print(box_top())
    print(box_row("WIND ANALYSIS — EV09-WIND"))
    print(box_row(title))
    if subtitle:
        print(box_row(subtitle))
    print(box_row("ERA5/ERA5-Land IFS-HRES · P1+P2 IDW (Haversine p=2)"))
    print(box_bot())


def report_wind_rose() -> None:
    df = _require_data()
    if df is None:
        return
    print_header("1 · WIND ROSE & MONTHLY STATISTICS",
                 "Distribusi arah × bin kecepatan · 16-sektor")

    sec_header("KOMPOSIT — 16 sektor")
    render_wind_rose(wind_rose(df, n_sectors=16), "16-sektor")

    sec_header("PER MUSIM — 8 sektor (DJF/MAM/JJA/SON)")
    for s, rose in seasonal_rose(df).items():
        render_wind_rose(rose, s)

    sec_header("STATISTIK BULANAN")
    stats = monthly_stats(df)
    hdr = (f"  {'Bln':<4}{'N':>8}{'Mean':>7}{'P10':>7}{'P50':>7}"
           f"{'P90':>7}{'Max':>7}{'Gust':>7}{'Dir°':>7}{'R':>6}")
    print(hdr[:W]); print("  " + "─" * (min(len(hdr), W - 4)))
    for m in range(1, 13):
        s = stats[m]
        print(f"  {MONTH_SHORT[m]:<4}"
              f"{s['n']:>8,}"
              f"{s['mean']:>7.2f}"
              f"{s['p10']:>7.2f}"
              f"{s['p50']:>7.2f}"
              f"{s['p90']:>7.2f}"
              f"{s['max']:>7.2f}"
              f"{s['gust_mean']:>7.2f}"
              f"{s['dir']:>7.1f}"
              f"{s['R']:>6.3f}"[:W])
    print()
    print("  Keterangan:")
    print("    Mean/P10/P50/P90/Max — kecepatan (km/h)")
    print("    Gust — rata-rata gust (km/h)")
    print("    Dir° — arah angin rata-rata (circular mean)")
    print("    R    — resultant length (0=uniform, 1=mono-arah)")


def _dir_to_compass(deg: float) -> str:
    if not np.isfinite(deg):
        return "—"
    names = SECTOR_NAMES_16
    width = 360.0 / 16
    idx = int(((deg + width / 2.0) % 360.0) // width) % 16
    return names[idx]


def report_diurnal() -> None:
    df = _require_data()
    if df is None:
        return
    print_header("2 · SIKLUS DIURNAL & DIAGNOSTIK SEA-BREEZE",
                 "Matriks jam × bulan + deteksi angin darat/laut")

    sec_header("HEATMAP KECEPATAN (km/h) — jam × bulan")
    mat, _ = diurnal_matrix(df, "ws10")
    render_heatmap(mat,
                    row_labels=[f"{h:02d}" for h in range(24)],
                    col_labels=[MONTH_SHORT[m] for m in range(1, 13)],
                    title="Mean wind speed 10m (jam lokal WIB)",
                    fmt_value="{:.2f}", row_label_w=3)

    sec_header("DIURNAL DIRECTION (circular mean per jam)")
    dirn = diurnal_direction(df)
    for h in range(24):
        d = dirn[h]
        sector = "—" if not np.isfinite(d) else _dir_to_compass(d)
        print(f"  {h:02d}:00  {d:>6.1f}°  {sector}")

    sec_header("DIAGNOSTIK SEA-BREEZE")
    print("  Amplitudo harmonik 12-jam (sea-breeze signature):")
    print(f"  {'Bln':<4}{'mean':>8}{'h12_A':>8}{'h12_phase°':>12}"
          f"{'peak_h':>9}{'dir_shift°':>12}")
    print("  " + "─" * 42)
    for m in range(1, 13):
        col = mat[:, m - 1]
        valid = np.isfinite(col)
        if not valid.any():
            continue
        h = np.arange(24)
        c = np.cos(2 * np.pi * h / 12)
        s = np.sin(2 * np.pi * h / 12)
        cv = c[valid]; sv = s[valid]; vv = col[valid]
        A_cos = 2 * np.mean(vv * cv)
        A_sin = 2 * np.mean(vv * sv)
        A = math.hypot(A_cos, A_sin)
        phase = math.degrees(math.atan2(A_sin, A_cos)) % 360.0
        peak_h = (phase / 30.0) % 24.0
        dsub = df[df["month"] == m]
        d_am = circ_mean_deg(dsub[dsub["hour"].between(0, 5)]["wd10"].values)
        d_pm = circ_mean_deg(dsub[dsub["hour"].between(11, 16)]["wd10"].values)
        shift = abs(circ_diff_deg(d_pm, d_am))
        print(f"  {MONTH_SHORT[m]:<4}"
              f"{col[valid].mean():>8.2f}"
              f"{A:>8.2f}"
              f"{phase:>12.1f}"
              f"{peak_h:>9.1f}"
              f"{shift:>12.1f}")
    print()
    print("  Interpretasi:")
    print("    h12_A    — amplitudo gelombang 12-jam; >0.8 km/h = sea-breeze kuat")
    print("    peak_h   — jam WIB puncak angin 12-jam (modulo 12)")
    print("    dir_shift— beda arah siang (11–16) vs dini hari (00–05)")


def report_gust() -> None:
    df = _require_data()
    if df is None:
        return
    print_header("3 · ANALISIS GUST",
                 "Gust factor GF = gust / speed · distribusi & exceedance")

    gs = gust_stats(df)
    if len(gs["gf"]) == 0:
        print("  [!] Tidak ada kolom gust atau speed valid.")
        return

    sec_header("STATISTIK GUST FACTOR")
    print(f"  N (ws ≥ 1 km/h)       : {len(gs['gf']):,}")
    print(f"  GF mean               : {gs['mean']:.3f}")
    print(f"  GF median             : {gs['p50']:.3f}")
    print(f"  GF P90                : {gs['p90']:.3f}")
    print(f"  GF P99                : {gs['p99']:.3f}")

    sec_header("HISTOGRAM GF (bin 0.5)")
    edges = np.arange(0.5, 8.0, 0.5)
    hist, _ = np.histogram(gs["gf"], bins=edges)
    max_h = int(hist.max()) if len(hist) else 1
    for i in range(len(hist)):
        bar = int(round(30 * hist[i] / max_h))
        print(f"  {edges[i]:.1f}–{edges[i+1]:.1f}  {hist[i]:>8,}  "
              f"{'█' * bar}")

    sec_header("EXCEEDANCE — % waktu gust > threshold")
    print(f"  {'Threshold km/h':<16}{'% waktu':>10}")
    print("  " + "─" * 26)
    for thr, pct in gs["exceedance_pct"].items():
        print(f"  >{thr:<15}{pct:>9.3f}%")

    sec_header("GUST FACTOR DIURNAL (per jam)")
    mat_gf = np.full(24, np.nan)
    for h in range(24):
        sub = df[df["hour"] == h]
        ws = sub["ws10"].values; g = sub["gust10"].values
        m = np.isfinite(ws) & np.isfinite(g) & (ws >= 1.0)
        if m.any():
            mat_gf[h] = float(np.mean(g[m] / ws[m]))
    max_gf = float(np.nanmax(mat_gf))
    min_gf = float(np.nanmin(mat_gf))
    for h in range(24):
        v = mat_gf[h]
        if not np.isfinite(v):
            continue
        bar_n = int(round(30 * (v - min_gf) / max(1e-6, max_gf - min_gf)))
        print(f"  {h:02d}:00  GF={v:.2f}  {'█' * bar_n}")


def report_shear() -> None:
    df = _require_data()
    if df is None:
        return
    print_header("4 · VERTICAL SHEAR 10m↔100m",
                 "Hellmann exponent α = ln(V100/V10)/ln(10)")

    if not df["ws100"].notna().any():
        print("  [!] Kolom wind_speed_100m tidak tersedia.")
        return

    alpha = shear_exponent(df)
    if len(alpha) == 0:
        print("  [!] Tidak cukup data untuk perhitungan shear.")
        return
    alpha = alpha[np.isfinite(alpha)]

    sec_header("STATISTIK HELLMANN EXPONENT α")
    print(f"  N              : {len(alpha):,}")
    print(f"  Mean α         : {alpha.mean():.3f}")
    print(f"  Median α       : {np.median(alpha):.3f}")
    print(f"  P10–P90        : {np.percentile(alpha, 10):.3f} – "
          f"{np.percentile(alpha, 90):.3f}")
    print()
    print("  Referensi: α≈0.14 (netral), α≈0.25 (stabil/malam), "
          "α≈0.10 (unstable/siang)")

    sec_header("DIURNAL PROFIL α (per jam)")
    for h in range(24):
        sub = df[df["hour"] == h]
        a = shear_exponent(sub)
        a = a[np.isfinite(a)]
        if len(a) == 0:
            continue
        mean_a = float(a.mean())
        bar_n = int(round(30 * max(0.0, min(0.5, mean_a)) / 0.5))
        stab = ("stabil" if mean_a > 0.20
                else "netral" if mean_a > 0.12 else "unstable")
        print(f"  {h:02d}:00  α={mean_a:.3f}  {'█' * bar_n}  [{stab}]")

    sec_header("DIRECTIONAL SHEAR (|Δθ| 10m↔100m)")
    dshear = directional_shear(df)
    if len(dshear):
        print(f"  Median  : {np.median(dshear):.1f}°")
        print(f"  P90     : {np.percentile(dshear, 90):.1f}°")
        print(f"  Max     : {np.max(dshear):.1f}°")
        print()
        print("  Δθ > 30° mengindikasikan Ekman spiral / sea-breeze reversal")


def report_persistence() -> None:
    df = _require_data()
    if df is None:
        return
    print_header("5 · PERSISTENCE & TRANSITION MATRIX",
                 "Run-length per sektor · Markov chain antar sektor")

    sec_header("PERSISTENCE PER SEKTOR (8-sektor, ws ≥ 1 km/h)")
    runs = persistence_runs(df, n_sectors=8)
    print(f"  {'Sektor':<8}{'N_runs':>9}{'Mean':>8}{'P50':>6}"
          f"{'P90':>6}{'Max':>6}")
    print("  " + "─" * 42)
    for i, name in enumerate(SECTOR_NAMES_8):
        r = runs[i]
        if len(r) == 0:
            print(f"  {name:<8}{0:>9}")
            continue
        print(f"  {name:<8}{len(r):>9,}"
              f"{np.mean(r):>8.2f}"
              f"{np.median(r):>6.0f}"
              f"{np.percentile(r, 90):>6.0f}"
              f"{np.max(r):>6.0f}")

    sec_header("TRANSITION MATRIX P(next sector | current sector)")
    M = sector_transition_matrix(df, n_sectors=8)
    hdr = "  From\\To " + "".join(f"{s:>6}" for s in SECTOR_NAMES_8)
    print(hdr[:W])
    print("  " + "─" * (min(len(hdr) - 2, W - 4)))
    for i, name in enumerate(SECTOR_NAMES_8):
        row = f"  {name:<8}"
        for j in range(8):
            row += f"{M[i, j]:>6.2f}"
        print(row[:W])
    print()
    print("  Catatan: baris = sektor asal; kolom = sektor tujuan.")
    print("           Self-transition tinggi (di diagonal) = arah stabil.")


def report_mangsa_wind() -> None:
    df = _require_data()
    if df is None:
        return
    print_header("6 · PROFIL ANGIN PER PRANATAMANGSA",
                 "Agregasi R30 dopy → 12 mangsa × 4 musim")

    profile = mangsa_wind_profile(df)

    sec_header("TABEL UTAMA")
    hdr = (f"  {'No':>3}  {'Nama':<10} {'Musim':<10} {'N':>8} "
           f"{'Mean':>7} {'P90':>7} {'Max':>7} {'Dir°':>7} "
           f"{'R':>6} {'GF':>6}")
    print(hdr[:W])
    print("  " + "─" * (min(len(hdr) - 2, W - 4)))
    for no, nama, musim in MANGSAS_INFO:
        p = profile[no]
        print(f"  {no:>3}  {nama:<10} {musim:<10} "
              f"{p['n']:>8,} "
              f"{p['mean']:>7.2f} "
              f"{p['p90']:>7.2f} "
              f"{p['max']:>7.2f} "
              f"{p['dir']:>7.1f} "
              f"{p['R']:>6.3f} "
              f"{p['gf']:>6.2f}"[:W])

    sec_header("RINGKASAN PER MUSIM (durasi-weighted)")
    print(f"  {'Musim':<12}{'Mean':>8}{'P90':>8}{'Dir°':>8}{'N':>10}")
    print("  " + "─" * 46)
    for mu in MUSIM_ORDER:
        members = MUSIM_MEMBERS[mu]
        sub = df[df["mangsa"].isin(members)]
        ws = sub["ws10"].dropna().values
        wd = sub["wd10"].dropna().values
        if len(ws) == 0:
            continue
        print(f"  {mu:<12}"
              f"{ws.mean():>8.2f}"
              f"{np.percentile(ws, 90):>8.2f}"
              f"{circ_mean_deg(wd):>8.1f}"
              f"{len(ws):>10,}")

    sec_header("WIND ROSE PER MUSIM (8-sektor)")
    for mu in MUSIM_ORDER:
        rose = wind_rose(df[df["mangsa"].isin(MUSIM_MEMBERS[mu])],
                         n_sectors=8)
        render_wind_rose(rose, f"Musim {mu}")

    sec_header("VALIDASI EMPIRIS PRANATAMANGSA")
    print("  Fraksi angin dari kuadran barat (202–292°) vs timur (90–180°):")
    print()
    for mu in MUSIM_ORDER:
        sub = df[df["mangsa"].isin(MUSIM_MEMBERS[mu])]
        wd = sub["wd10"].dropna().values
        if len(wd) == 0:
            continue
        nw_frac = float(((wd >= 202) & (wd < 292)).mean() * 100)
        se_frac = float(((wd >= 90) & (wd < 180)).mean() * 100)
        print(f"  {mu:<12}  W-quad%={nw_frac:>5.1f}  "
              f"E-quad%={se_frac:>5.1f}  "
              f"→ dominan {'BARAT' if nw_frac > se_frac else 'TIMUR'}")


# ══════════════════════════════════════════════════════════════════════════
# Section 8 · Coupling kernels + Report 7
# ══════════════════════════════════════════════════════════════════════════
#
# LAG CONVENTION (canonical, verified by _self_test_lag_convention):
#
#   profile[k] = corr( base.shift(lags[k]), target )
#
# Positive lag ⇒ BASE LEADS TARGET.
# ══════════════════════════════════════════════════════════════════════════

def _cross_corr_profile(
    base: "pd.Series",
    target: "pd.Series",
    max_lag: int = 14,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (lags, profile) — profile[k] = corr(base.shift(lags[k]), target)."""
    lags = np.arange(-max_lag, max_lag + 1)
    prof = np.full(len(lags), np.nan)
    for i, L in enumerate(lags):
        a = base.shift(L)
        m = a.notna() & target.notna()
        if m.sum() < 50:
            continue
        prof[i] = float(np.corrcoef(a[m], target[m])[0, 1])
    return lags, prof


def _peak_lag(lags: np.ndarray, prof: np.ndarray) -> Tuple[int, float]:
    """Return (peak_lag, peak_r) at max |corr|; (0, nan) if no valid."""
    if not np.isfinite(prof).any():
        return 0, float("nan")
    k = int(np.nanargmax(np.abs(prof)))
    return int(lags[k]), float(prof[k])


def _daily_aggregate(df: "pd.DataFrame") -> "pd.DataFrame":
    """Aggregate hourly → daily, requiring ≥20 valid hours per day."""
    df = df.copy()
    df["_date"] = pd.to_datetime(df["time"]).dt.normalize()
    agg = df.groupby("_date").agg(
        u        = ("u_comp", "mean"),
        ws       = ("ws10",   "mean"),
        p        = ("precip", "sum"),
        cloud    = ("cloud",  "mean"),
        cloud_lo = ("cloud_lo", "mean"),
        n        = ("ws10",   "count"),
    ).reset_index().rename(columns={"_date": "date"})
    agg = agg[agg["n"] >= 20].reset_index(drop=True)

    for col in ("u", "p", "cloud", "ws", "cloud_lo"):
        if col in agg.columns:
            agg[col + "_anom"] = (
                agg.groupby(agg["date"].dt.month)[col]
                   .transform(lambda x: x - x.mean())
            )
    return agg


def _detect_onset_events(
    precip: np.ndarray, dry_hr: int = 6, thr_mm: float = 0.5,
) -> List[int]:
    """Indices where precip kicks from <0.1 to >thr after a dry window."""
    events: List[int] = []
    last = -10**9
    for i in range(dry_hr, len(precip) - 12):
        if precip[i] > thr_mm and np.all(precip[i - dry_hr:i] < 0.1):
            if i - last >= 12:
                events.append(i)
                last = i
    return events


def _render_lag_profile(
    lags: np.ndarray, prof: np.ndarray,
    label_base: str, label_target: str,
    peak_lag: Optional[int] = None,
) -> None:
    """ASCII bar-chart of a cross-correlation profile."""
    valid = np.isfinite(prof)
    if not valid.any():
        print("  (profil tidak tersedia)")
        return
    vmax = float(np.nanmax(np.abs(prof)))
    print(f"  ── Profil korelasi lag: {label_base} vs {label_target} ──")
    print(f"  Convention: corr({label_base}.shift(L), {label_target})")
    print(f"  → L>0: {label_base} MENDAHULUI {label_target}")
    print()
    for L, r in zip(lags, prof):
        if not np.isfinite(r):
            continue
        bar_len = int(round(24 * abs(r) / max(vmax, 1e-9)))
        sign = "+" if r >= 0 else "−"
        bar = "█" * bar_len
        mark = " ← PEAK" if (peak_lag is not None and L == peak_lag) else ""
        print(f"  L={L:+3d}  r={r:+6.3f}  {sign}{bar}{mark}")
    print()


def report_coupling() -> None:
    df = _require_data()
    if df is None:
        return
    print_header("7 · KOPPELING ANGIN ↔ HUJAN ↔ AWAN",
                 "Komposit · lag-correlation · onset signature · cloud-sector")

    # ── A · Composite by precipitation intensity ───────────────────────
    sec_header("A · KOMPOSIT PER INTENSITAS HUJAN",
               "WS/Dir/GF/Cloud per kategori curah hujan")
    bins = (
        (0.000,  0.050, "Kering  (0–0.05)"),
        (0.050,  1.000, "Ringan  (0.05–1)"),
        (1.000,  5.000, "Sedang  (1–5)"),
        (5.000,  1e9,   "Lebat   (>5)"),
    )
    print(f"  {'Kategori mm/h':<18}{'N':>9}{'WS':>6}{'GF':>6}"
          f"{'Dir°':>7}{'R':>6}{'Cld%':>7}{'CldLo':>7}")
    print("  " + "─" * 62)
    for lo, hi, lbl in bins:
        sub = df[(df["precip"] >= lo) & (df["precip"] < hi)]
        if len(sub) == 0:
            continue
        ws = sub["ws10"].dropna().values
        wd = sub["wd10"].dropna().values
        m = (np.isfinite(sub["ws10"].values)
             & np.isfinite(sub["gust10"].values)
             & (sub["ws10"].values >= 1.0))
        gf = (float(np.mean(sub["gust10"].values[m]
                            / sub["ws10"].values[m]))
              if m.any() else float("nan"))
        print(f"  {lbl:<18}{len(sub):>9,}"
              f"{ws.mean():>6.2f}{gf:>6.2f}"
              f"{circ_mean_deg(wd):>7.1f}{circ_R(wd):>6.3f}"
              f"{sub['cloud'].mean():>7.1f}"
              f"{sub['cloud_lo'].mean():>7.1f}")
    print()
    print("  Ekspektasi: kategori Lebat → WS naik (squall), GF tinggi,")
    print("              Cloud ~100%, CldLo tinggi (konvektif).")

    # ── B · Cross-correlation ─────────────────────────────────────────
    sec_header("B · KORELASI LAG — KOMPONEN BARAT vs HUJAN",
               "Harian · deseasonalised (anomali thd climatology bulanan)")
    daily = _daily_aggregate(df)
    if len(daily) < 200:
        print("  [!] data harian tidak cukup.")
    else:
        print(f"  N hari = {len(daily):,}  "
              f"({daily['date'].min().date()} → {daily['date'].max().date()})")
        print()
        print("  Konvensi: corr(base.shift(L), target). "
              "L>0 ⇒ base MENDAHULUI target.")
        print()
        print(f"  {'Lag L':<7}{'corr(u,P)':>12}{'corr(WS,P)':>13}"
              f"{'corr(Cld,P)':>14}")
        print("  " + "─" * 50)
        for L in (-5, -3, -1, 0, 1, 3, 5):
            u_s  = daily["u_anom"].shift(L)
            ws_s = daily["ws_anom"].shift(L)
            c_s  = daily["cloud_anom"].shift(L)
            p_v  = daily["p_anom"]
            m = p_v.notna() & u_s.notna()
            if m.sum() < 50:
                continue
            c_u  = float(np.corrcoef(u_s[m],  p_v[m])[0, 1])
            c_ws = float(np.corrcoef(ws_s[m], p_v[m])[0, 1])
            c_c  = float(np.corrcoef(c_s[m],  p_v[m])[0, 1])
            print(f"  {L:+d}{'':<4}{c_u:>+12.3f}{c_ws:>+13.3f}"
                  f"{c_c:>+14.3f}")
        print()

        lags, prof_u = _cross_corr_profile(
            daily["u_anom"], daily["p_anom"], max_lag=14)
        peak_L, peak_r = _peak_lag(lags, prof_u)
        _render_lag_profile(lags, prof_u,
                            label_base="u_anom", label_target="P_anom",
                            peak_lag=peak_L)
        print(f"  → Peak |r| pada L = {peak_L:+d} hari  (r = {peak_r:+.3f})")
        if peak_L > 0:
            print(f"    Angin barat MENDAHULUI hujan ~{peak_L} hari")
            print(f"    → konsisten dengan monsoon onset.")
        elif peak_L < 0:
            print(f"    Hujan MENDAHULUI angin barat ~{-peak_L} hari")
            print(f"    → konveksi lokal / ITCZ lebih dulu.")
        else:
            print("    Sinyal simultan (in-phase) — monsoon & hujan bersama.")

        _, prof_c = _cross_corr_profile(
            daily["cloud_anom"], daily["p_anom"], max_lag=14)
        pL_c, pR_c = _peak_lag(lags, prof_c)
        print()
        print(f"  Peak cloud↔hujan : L = {pL_c:+d} hari  (r = {pR_c:+.3f})")

    # ── C · Precipitation onset signature ─────────────────────────────
    sec_header("C · SIGNATURE ANGIN MENJELANG ONSET HUJAN",
               "Komposit ±12 jam dari transisi kering → hujan > 0.5 mm/h")
    p_arr = df["precip"].fillna(0).values
    w_arr = df["ws10"].values
    u_arr = df["u_comp"].values
    events = _detect_onset_events(p_arr, dry_hr=6, thr_mm=0.5)
    print(f"  Event onset terdeteksi: {len(events):,} "
          f"(rata-rata setiap {len(p_arr)//max(len(events),1):,} jam)")
    if events:
        offsets = np.arange(-12, 13)
        ws_prof = np.zeros(len(offsets))
        u_prof  = np.zeros(len(offsets))
        cnt = 0
        for ev in events:
            if ev - 12 < 0 or ev + 12 >= len(p_arr):
                continue
            ws_prof += w_arr[ev - 12: ev + 13]
            u_prof  += u_arr[ev - 12: ev + 13]
            cnt += 1
        if cnt:
            ws_prof /= cnt; u_prof /= cnt
            print(f"  Komposit dari {cnt:,} event")
            print()
            print(f"  {'Jam rel':<9}{'WS km/h':>9}{'u-comp':>10}{'':>2}Bar")
            print("  " + "─" * 54)
            wsmax = max(ws_prof.max(), 1e-6)
            for j, off in enumerate(offsets):
                bar_n = int(round(22 * ws_prof[j] / wsmax))
                mark = "  ← ONSET" if off == 0 else ""
                print(f"  {off:+3d} jam  {ws_prof[j]:>8.2f}"
                      f"{u_prof[j]:>10.3f}  {'█' * bar_n}{mark}")

    # ── D · Cloud per sector ──────────────────────────────────────────
    sec_header("D · TUTUPAN AWAN PER SEKTOR ANGIN",
               "8-sektor · total & low-cloud")
    wd_arr = df["wd10"].values
    valid = np.isfinite(wd_arr) & np.isfinite(df["cloud"].values)
    wd_v  = wd_arr[valid]
    c_tot = df["cloud"].values[valid]

    c_lo_v = df["cloud_lo"].values
    c_lo_valid = np.isfinite(wd_arr) & np.isfinite(c_lo_v)
    c_lo_v = c_lo_v[c_lo_valid]
    wd_lo  = wd_arr[c_lo_valid]

    width = 45.0
    sec_tot = (((wd_v + width / 2) % 360) // width).astype(int) % 8
    sec_lo  = (((wd_lo + width / 2) % 360) // width).astype(int) % 8

    print(f"  {'Sektor':<8}{'N':>9}{'Cld%':>8}{'CldLo%':>9}{'N(lo)':>9}  Bar")
    print("  " + "─" * 60)
    means = [float(c_tot[sec_tot == i].mean()) if (sec_tot == i).any()
             else np.nan for i in range(8)]
    cmax = max([m for m in means if np.isfinite(m)], default=1.0)
    for i, name in enumerate(SECTOR_NAMES_8):
        n_tot = int((sec_tot == i).sum())
        n_lo  = int((sec_lo  == i).sum())
        cm    = means[i]
        clo   = float(c_lo_v[sec_lo == i].mean()) if n_lo else np.nan
        bar_n = int(round(22 * cm / cmax)) if np.isfinite(cm) else 0
        print(f"  {name:<8}{n_tot:>9,}{cm:>8.1f}{clo:>9.1f}{n_lo:>9,}"
              f"  {'█' * bar_n}")

    # ── E · Diurnal cycle ─────────────────────────────────────────────
    sec_header("E · SIKLUS DIURNAL — ANGIN, HUJAN, AWAN",
               "Rata-rata per jam WIB")
    print(f"  {'Jam':<6}{'WS':>7}{'u-comp':>9}{'Precip':>9}"
          f"{'Cld%':>7}{'CldLo%':>8}")
    print("  " + "─" * 48)
    hr_ws, hr_u, hr_p, hr_c = [], [], [], []
    for h in range(24):
        sub = df[df["hour"] == h]
        ws_h = float(sub["ws10"].dropna().mean())
        u_h  = float(np.nanmean(sub["u_comp"].values))
        p_h  = float(sub["precip"].fillna(0).mean())
        c_h  = float(sub["cloud"].dropna().mean())
        cl_h = float(sub["cloud_lo"].dropna().mean())
        hr_ws.append(ws_h); hr_u.append(u_h); hr_p.append(p_h); hr_c.append(c_h)
        print(f"  {h:02d}:00 {ws_h:>6.2f}{u_h:>9.3f}{p_h:>9.3f}"
              f"{c_h:>7.1f}{cl_h:>8.1f}")
    peak_ws = int(np.argmax(hr_ws))
    peak_p  = int(np.argmax(hr_p))
    peak_c  = int(np.argmax(hr_c))
    peak_u  = int(np.argmax(hr_u))
    print()
    print(f"  Peak WS     : {peak_ws:02d}:00 WIB")
    print(f"  Peak u-comp : {peak_u:02d}:00 WIB (paling barat)")
    print(f"  Peak precip : {peak_p:02d}:00 WIB")
    print(f"  Peak cloud  : {peak_c:02d}:00 WIB")
    print()
    print(f"  → Lag puncak hujan − puncak angin = "
          f"{peak_p - peak_ws:+d} jam")


# ══════════════════════════════════════════════════════════════════════════
# Section 9 · Monsoon Reversal Detection kernels + Report 8
# ══════════════════════════════════════════════════════════════════════════
#
# The low-level wind at MJS alternates between:
#
#   East monsoon (Jun–Oct):   wd ≈ 110–140°  →  u_comp ≈ −0.6 to −0.8
#   West monsoon (Dec–Apr):   wd ≈ 240–290°  →  u_comp ≈ +0.8 to +1.0
#
# The reversal — East→West — marks the arrival of the West monsoon.
# Detected from a 30-day rolling mean of u_comp with a sustain check
# inside a dopy window, per pranata-year.
# ══════════════════════════════════════════════════════════════════════════

def _rolling_daily_ucomp(df: "pd.DataFrame",
                          win: int = MR_ROLL_WIN) -> "pd.DataFrame":
    """30-day rolling mean of u_comp per calendar day.

    Uses centered=True so the value at t represents a symmetric window
    around t — appropriate for retrospective diagnostics.
    """
    d = df.copy()
    d["_date"] = pd.to_datetime(d["time"]).dt.normalize()
    daily = d.groupby("_date").agg(u=("u_comp", "mean")).reset_index()
    daily = daily.sort_values("_date").reset_index(drop=True)
    daily["u30"] = (daily["u"].rolling(win, center=True,
                                        min_periods=win // 2).mean())

    t = pd.to_datetime(daily["_date"])
    a  = pd.to_datetime(dict(year=t.dt.year,     month=ANCHOR_MONTH,
                              day=ANCHOR_DAY))
    ap = pd.to_datetime(dict(year=t.dt.year - 1, month=ANCHOR_MONTH,
                              day=ANCHOR_DAY))
    daily["dopy"] = np.where(t < a,
                              (t - ap).dt.total_seconds() / 86400.0,
                              (t - a ).dt.total_seconds() / 86400.0) % 365.0
    return daily[["_date", "u30", "dopy"]].rename(columns={"_date": "date"})


def _find_crossing(
    sig: np.ndarray,
    dopys: np.ndarray,
    thr: float = MR_THRESHOLD,
    up: bool = True,
    sustain: int = MR_SUSTAIN,
    window: Tuple[float, float] = MR_WINDOW,
) -> Optional[float]:
    """Find first dopy where signal crosses `thr` inside `window`.

    Parameters
    ----------
    sig    : rolling signal (same length as dopys)
    dopys  : dopy values for each sample
    thr    : threshold (u=0.0 for monsoon reversal onset)
    up     : True = crossing from below to above thr
    sustain: number of subsequent samples that must remain on the correct
             side of thr − ε (or thr + ε if up=False)
    window : (dopy_min, dopy_max) — only search inside this range

    Returns
    -------
    dopy of the crossing, or None if no valid crossing.
    """
    lo, hi = window
    n = len(sig)
    tol = MR_EPS
    for i in range(1, n):
        d = dopys[i]
        if not (lo <= d <= hi):
            continue
        s_prev, s_curr = sig[i - 1], sig[i]
        if not (np.isfinite(s_prev) and np.isfinite(s_curr)):
            continue
        if up and s_prev < thr <= s_curr:
            fut = sig[i: i + sustain]
            if len(fut) < sustain - 5:
                continue
            if np.isfinite(fut).sum() < sustain - 5:
                continue
            if np.nanmin(fut) >= thr - tol:
                return float(d)
        elif (not up) and s_prev > thr >= s_curr:
            fut = sig[i: i + sustain]
            if len(fut) < sustain - 5:
                continue
            if np.isfinite(fut).sum() < sustain - 5:
                continue
            if np.nanmax(fut) <= thr + tol:
                return float(d)
    return None


def _detect_all_reversals(df: "pd.DataFrame"
                          ) -> List[Tuple[int, float, int]]:
    """Detect reversal per pranata-year.

    Returns list of (pranata_year, rev_dopy, n_valid_days).
    pranata_year = year of the 22-Jun anchor of that cycle.
    """
    daily = _rolling_daily_ucomp(df)
    out: List[Tuple[int, float, int]] = []
    for py in range(2015, 2027):
        anchor = pd.Timestamp(year=py, month=ANCHOR_MONTH, day=ANCHOR_DAY)
        end = anchor + pd.Timedelta(days=365)
        sub = daily[(daily["date"] >= anchor) & (daily["date"] < end)]
        if len(sub) < 300:
            continue
        rev = _find_crossing(sub["u30"].values, sub["dopy"].values)
        if rev is not None:
            out.append((py, rev, len(sub)))
    return out


def _linear_trend(xs: np.ndarray, ys: np.ndarray
                  ) -> Tuple[float, float, float, float]:
    """Return (slope, intercept, pearson_r, t_statistic).

    t-statistic = r·sqrt((n−2)/(1−r²)).  For n=11 (df=9) the two-tailed
    critical value at α=0.05 is |t| ≈ 2.26.
    """
    if len(xs) < 3:
        return float("nan"), float("nan"), float("nan"), float("nan")
    slope, intercept = np.polyfit(xs, ys, 1)
    r = float(np.corrcoef(xs, ys)[0, 1])
    n = len(xs)
    if abs(r) < 1e-9:
        return float(slope), float(intercept), r, 0.0
    t = r * math.sqrt((n - 2) / max(1e-9, 1 - r * r))
    return float(slope), float(intercept), r, float(t)


def _dopy_to_approx_date(py: int, dopy: float) -> str:
    """Approximate calendar date for (pranata_year, dopy)."""
    anchor = datetime(py, ANCHOR_MONTH, ANCHOR_DAY)
    d = anchor + timedelta(days=int(round(dopy)))
    return f"{d.day:02d} {MONTH_SHORT[d.month]} {d.year}"


def report_monsoon_reversal() -> None:
    df = _require_data()
    if df is None:
        return
    print_header("8 · DETEKSI REVERSAL MONSON BARAT",
                 "Kapan angin berbalik dari timur ke barat di MJS")

    sec_header("METODE")
    print(f"  Sinyal       : u_comp = −sin(wd10), rolling {MR_ROLL_WIN}-hari")
    print(f"  Kriteria     : u melintas dari negatif ke positif")
    print(f"                 sustain ≥ {MR_SUSTAIN} hari (u ≥ −{MR_EPS})")
    print(f"  Window cari  : dopy {MR_WINDOW[0]:.0f}–{MR_WINDOW[1]:.0f} "
          f"(≈ 21 Agu – 08 Jan)")
    print()
    print("  Catatan: tanpa window restriction, tahun El Niño lemah (2015,")
    print("  2019, 2023) memproduksi false-positive pada dopy ≈ 290 "
          "(onset East monsoon).")

    sec_header("DETEKSI PER PRANATA-TAHUN")
    results = _detect_all_reversals(df)
    if not results:
        print("  [!] Tidak ada reversal terdeteksi.")
        return

    vals = np.array([r[1] for r in results])
    mean_v = float(vals.mean())
    med_v  = float(np.median(vals))
    std_v  = float(vals.std(ddof=1)) if len(vals) > 1 else 0.0

    if std_v > 0:
        z = (vals - mean_v) / std_v
        inlier_mask = np.abs(z) < MR_OUTLIER_Z
    else:
        z = np.zeros_like(vals)
        inlier_mask = np.ones_like(vals, dtype=bool)

    robust_mean = float(vals[inlier_mask].mean()) \
                  if inlier_mask.any() else float("nan")
    robust_std  = float(vals[inlier_mask].std(ddof=1)) \
                  if inlier_mask.sum() > 1 else float("nan")
    n_outliers  = int((~inlier_mask).sum())

    print(f"  {'Tahun':<8}{'rev dopy':>10}{'Tanggal (±)':>18}"
          f"{'z':>7}{'Status':>14}")
    print("  " + "─" * 60)
    for (py, rev, _), z_val, is_in in zip(results, z, inlier_mask):
        if abs(z_val) < 1.0:
            status = "✓"
        elif abs(z_val) < MR_OUTLIER_Z:
            status = "⚠"
        else:
            status = "⚠⚠  outlier"
        tgl = _dopy_to_approx_date(py, rev)
        print(f"  {py:<8}{rev:>10.1f}{tgl:>18}"
              f"{z_val:>+7.2f}{status:>14}")

    sec_header("STATISTIK")
    print(f"  N deteksi       : {len(vals)}")
    print(f"  Median (robust) : {med_v:.1f}  "
          f"({_dopy_to_approx_date(2025, med_v)})")
    print(f"  Mean (raw)      : {mean_v:.1f}  "
          f"({_dopy_to_approx_date(2025, mean_v)})")
    print(f"  Std (raw)       : {std_v:.1f} hari")
    print(f"  ──")
    print(f"  Robust mean     : {robust_mean:.1f}  "
          f"(exclude |z|>{MR_OUTLIER_Z:.1f})")
    print(f"  Robust std      : {robust_std:.1f} hari")
    print(f"  N outliers      : {n_outliers}  "
          f"({', '.join(str(r[0]) for r, m in zip(results, inlier_mask) if not m)})")
    print(f"  Min – Max       : {vals.min():.1f} – {vals.max():.1f}")
    print(f"  Range           : {vals.max() - vals.min():.1f} hari")

    sec_header("ANALISIS TREN")
    ys = np.array([r[0] for r in results], dtype=float)

    slope_f, _, r_f, t_f = _linear_trend(ys, vals)
    if inlier_mask.sum() >= 3:
        slope_r, _, r_r, t_r = _linear_trend(ys[inlier_mask],
                                              vals[inlier_mask])
    else:
        slope_r, r_r, t_r = float("nan"), float("nan"), float("nan")

    print(f"  ── Full sample (n = {len(vals)}) ──")
    print(f"    Slope  : {slope_f:+.2f} hari/tahun")
    print(f"    Pearson: {r_f:+.3f}")
    print(f"    t-stat : {t_f:+.2f}   (df = {len(vals) - 2})")
    print()
    if np.isfinite(slope_r):
        n_r = int(inlier_mask.sum())
        print(f"  ── Robust sample (n = {n_r}) ──")
        print(f"    Slope  : {slope_r:+.2f} hari/tahun")
        print(f"    Pearson: {r_r:+.3f}")
        print(f"    t-stat : {t_r:+.2f}   (df = {n_r - 2})")
    print()
    print(f"  |t|_crit (α=0.05) ≈ 2.26 untuk df = 9")
    print()
    verdict_slope = slope_r if np.isfinite(slope_r) else slope_f
    verdict_t     = t_r if np.isfinite(t_r) else t_f
    if abs(verdict_t) < 2.26:
        print("  Verdict: TIDAK ada tren signifikan (boundary stasioner).")
    else:
        direction = "mundur" if verdict_slope > 0 else "maju"
        print(f"  Verdict: TREN signifikan — reversal {direction} "
              f"{abs(verdict_slope):.2f} hari/tahun.")

    sec_header("BAR CHART PER TAHUN")
    lo = vals.min() - 5
    hi = vals.max() + 5
    for (py, rev, _), is_in in zip(results, inlier_mask):
        bar_n = int(round(30 * (rev - lo) / max(1e-6, hi - lo)))
        marker = "  " if is_in else " ⚠"
        print(f"  {py}  {rev:>6.1f}  {'█' * bar_n}{marker}")

    sec_header("POSISI RELATIF TERHADAP SKENARIO LABUH")
    ref = robust_mean if np.isfinite(robust_mean) else mean_v
    print(f"  Reference reversal dopy = {ref:.1f}  "
          f"({_dopy_to_approx_date(2025, ref)})")
    print(f"  (robust mean, exclude |z|>{MR_OUTLIER_Z:.1f})")
    print()
    print(f"  {'Skenario':<12}{'Labuh start':>13}{'Selisih (hr)':>15}")
    print("  " + "─" * 44)
    for key, val in SCENARIO_LABUH_DOPY.items():
        delta = val - ref
        print(f"  {key:<12}{val:>13.1f}{delta:>+15.1f}")
    print()
    print("  Selisih negatif = Labuh start lebih awal dari reversal fisik.")


# ══════════════════════════════════════════════════════════════════════════
# Section 10 · Lag convention self-test
# ══════════════════════════════════════════════════════════════════════════

def _self_test_lag_convention() -> bool:
    """Assert corr(base.shift(+k), target) peaks at +k when target lags
    base by k samples.  Called once at program entry.
    """
    rng = np.random.default_rng(42)
    n = 400
    base = rng.normal(0, 1, size=n)
    target = np.concatenate([np.zeros(3), base[:-3]]) + 0.1 * rng.normal(0, 1, n)
    s_base = pd.Series(base)
    s_target = pd.Series(target)
    lags = np.arange(-10, 11)
    prof = np.full(len(lags), np.nan)
    for i, L in enumerate(lags):
        a = s_base.shift(L)
        m = a.notna() & s_target.notna()
        if m.sum() >= 50:
            prof[i] = float(np.corrcoef(a[m], s_target[m])[0, 1])
    if not np.isfinite(prof).any():
        return False
    return int(lags[int(np.nanargmax(prof))]) == 3


# ══════════════════════════════════════════════════════════════════════════
# Section 11 · CLI
# ══════════════════════════════════════════════════════════════════════════

MENU_ITEMS = (
    "  1 › Wind Rose & Statistik Bulanan",
    "  2 › Siklus Diurnal & Diagnostik Sea-Breeze",
    "  3 › Analisis Gust (gust factor, exceedance)",
    "  4 › Vertical Shear 10m↔100m (Hellmann α)",
    "  5 › Persistence & Transition Matrix",
    "  6 › Profil Angin per Pranatamangsa",
    "  7 › Koppeling Angin ↔ Hujan ↔ Awan",
    "  8 › Deteksi Reversal Monson Barat",
    "  9 › Jalankan semua (1–8)",
    "  0 › Keluar",
)


def show_menu() -> None:
    print()
    print(box_top("PRANATA MANGSA — WIND ANALYSIS (EV09-WIND)"))
    print(box_row("Hourly 10yr P1+P2 · IDW Haversine p=2 · MJS target point"))
    print(box_row("−7.5220°LS, 112.5661°BT, 28 m"))
    print(box_mid())
    for item in MENU_ITEMS:
        print(box_row(item))
    print(box_bot())


def _run_all() -> None:
    report_wind_rose()
    report_diurnal()
    report_gust()
    report_shear()
    report_persistence()
    report_mangsa_wind()
    report_coupling()
    report_monsoon_reversal()


def main_loop() -> None:
    while True:
        show_menu()
        pilihan = input("  Pilih menu (0–9): ").strip()
        if pilihan == "0":
            print()
            print(box_top())
            print(box_row("Terima kasih. Sampai jumpa! — Wind EV09"))
            print(box_bot())
            print()
            break
        elif pilihan == "1":
            report_wind_rose()
        elif pilihan == "2":
            report_diurnal()
        elif pilihan == "3":
            report_gust()
        elif pilihan == "4":
            report_shear()
        elif pilihan == "5":
            report_persistence()
        elif pilihan == "6":
            report_mangsa_wind()
        elif pilihan == "7":
            report_coupling()
        elif pilihan == "8":
            report_monsoon_reversal()
        elif pilihan == "9":
            _run_all()
        else:
            print("\n  Pilihan tidak valid. Masukkan angka 0–9.")
            input("\n  Tekan Enter untuk melanjutkan...")
            continue
        input("\n  Tekan Enter untuk kembali ke menu...")


def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="pranatamangsa_wind",
        description="Pranata Mangsa wind analysis (EV09-WIND).",
    )
    ap.add_argument("--rose", action="store_true",
                    help="Wind rose & statistik bulanan")
    ap.add_argument("--diurnal", action="store_true",
                    help="Siklus diurnal & sea-breeze")
    ap.add_argument("--gust", action="store_true",
                    help="Analisis gust factor")
    ap.add_argument("--shear", action="store_true",
                    help="Vertical shear 10m↔100m")
    ap.add_argument("--persistence", action="store_true",
                    help="Persistence & transition matrix")
    ap.add_argument("--mangsa", action="store_true",
                    help="Profil angin per Pranatamangsa")
    ap.add_argument("--coupling", action="store_true",
                    help="Koppeling angin–hujan–awan")
    ap.add_argument("--monsoon", action="store_true",
                    help="Deteksi reversal monson barat per tahun")
    ap.add_argument("--all", action="store_true",
                    help="Jalankan semua report")
    return ap


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_argparser().parse_args(argv)

    if HAS_PANDAS and not _self_test_lag_convention():
        print("  [!!!] LAG CONVENTION SELF-TEST FAILED — report 7 "
              "will produce unreliable lag interpretations.", file=sys.stderr)

    if args.all:
        _run_all(); return 0
    if args.rose:        report_wind_rose();        return 0
    if args.diurnal:     report_diurnal();          return 0
    if args.gust:        report_gust();             return 0
    if args.shear:       report_shear();            return 0
    if args.persistence: report_persistence();      return 0
    if args.mangsa:      report_mangsa_wind();      return 0
    if args.coupling:    report_coupling();         return 0
    if args.monsoon:     report_monsoon_reversal(); return 0

    main_loop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Program dihentikan. Sampai jumpa!")
        sys.exit(0)