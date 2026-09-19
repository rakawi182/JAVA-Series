#!/usr/bin/env python3
"""
extract.py — Ekstrak data analisis angin ke wind_data.json.

Tidak menyentuh HTML, tidak unduh apapun, tidak server.
Cukup import EV09wind, hitung report 1–10, tulis JSON.

Jalankan: python extract.py
Output:   wind_data.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from EV09wind import (
    _require_data, _detect_all_reversals, _daily_aggregate,
    _detect_onset_events, _cross_corr_profile, _peak_lag,
    _dopy_to_approx_date, _linear_trend, _dir_to_compass,
    wind_rose, monthly_stats, seasonal_rose, diurnal_matrix,
    diurnal_direction, gust_stats, shear_exponent, directional_shear,
    persistence_runs, sector_transition_matrix, mangsa_wind_profile,
    circ_mean_deg, circ_R, circ_diff_deg,
    MUSIM_ORDER, MUSIM_MEMBERS, MANGSAS_INFO,
    MONTH_SHORT, SECTOR_NAMES_8, SECTOR_NAMES_16,
    MR_OUTLIER_Z, SCENARIO_LABUH_DOPY,
)


def n(v):
    """float atau None."""
    try:
        x = float(v)
        return None if (np.isnan(x) or np.isinf(x)) else x
    except Exception:
        return None


def build(df) -> dict:
    out = {"meta": {
        "n_rows": int(len(df)),
        "start": str(df["time"].min().date()),
        "end": str(df["time"].max().date()),
        "generated": datetime.now().isoformat(timespec="seconds"),
    }}

    # ═══ R1 · Wind rose ═══
    r16 = wind_rose(df, 16)
    seas = seasonal_rose(df)
    ms = monthly_stats(df)
    out["r1"] = {
        "composite": {"sectors": list(SECTOR_NAMES_16),
                       "freq": r16.sector_freq.tolist(),
                       "n": int(r16.total)},
        "seasonal": {k: {"sectors": list(SECTOR_NAMES_8),
                          "freq": v.sector_freq.tolist(),
                          "n": int(v.total)} for k, v in seas.items()},
        "monthly": [{"m": m, "nama": MONTH_SHORT[m],
                      "n": ms[m]["n"], "mean": n(ms[m]["mean"]),
                      "p10": n(ms[m]["p10"]), "p50": n(ms[m]["p50"]),
                      "p90": n(ms[m]["p90"]), "max": n(ms[m]["max"]),
                      "gust": n(ms[m]["gust_mean"]),
                      "dir": n(ms[m]["dir"]), "R": n(ms[m]["R"])}
                     for m in range(1, 13)],
    }

    # ═══ R2 · Diurnal ═══
    mat, _ = diurnal_matrix(df, "ws10")
    dirn = diurnal_direction(df)
    sb = []
    for m in range(1, 13):
        col = mat[:, m - 1]
        v = np.isfinite(col)
        if not v.any():
            continue
        h = np.arange(24)
        cv, sv, vv = np.cos(2*np.pi*h/12)[v], np.sin(2*np.pi*h/12)[v], col[v]
        Ac, As = 2*np.mean(vv*cv), 2*np.mean(vv*sv)
        A = float(np.hypot(Ac, As))
        ph = float(np.degrees(np.arctan2(As, Ac)) % 360)
        dsub = df[df["month"] == m]
        am = circ_mean_deg(dsub[dsub["hour"].between(0,5)]["wd10"].values)
        pm = circ_mean_deg(dsub[dsub["hour"].between(11,16)]["wd10"].values)
        sb.append({"m": m, "A": A, "phase": ph,
                    "peak_h": float((ph/30) % 24),
                    "shift": float(abs(circ_diff_deg(pm, am)))})
    out["r2"] = {"matrix": mat.tolist(),
                  "direction": [float(dirn[h]) for h in range(24)],
                  "sea_breeze": sb,
                  "months": [MONTH_SHORT[m] for m in range(1, 13)]}

    # ═══ R3 · Gust ═══
    gs = gust_stats(df)
    edges = np.arange(0.5, 8.0, 0.5)
    hist, _ = np.histogram(gs["gf"], bins=edges)
    diurnal_gf = []
    for h in range(24):
        sub = df[df["hour"] == h]
        w, g = sub["ws10"].values, sub["gust10"].values
        m = np.isfinite(w) & np.isfinite(g) & (w >= 1.0)
        diurnal_gf.append(float(np.mean(g[m]/w[m])) if m.any() else None)
    out["r3"] = {
        "stats": {"n": int(len(gs["gf"])), "mean": n(gs["mean"]),
                   "median": n(gs["p50"]), "p90": n(gs["p90"]),
                   "p99": n(gs["p99"])},
        "hist": {"edges": edges.tolist(), "counts": hist.tolist()},
        "exceedance": [{"t": int(k), "pct": n(v)}
                        for k, v in gs["exceedance_pct"].items()],
        "diurnal": diurnal_gf,
    }

    # ═══ R4 · Shear ═══
    a = shear_exponent(df)
    a = a[np.isfinite(a)]
    diurnal_a = []
    for h in range(24):
        aa = shear_exponent(df[df["hour"] == h])
        aa = aa[np.isfinite(aa)]
        diurnal_a.append(float(aa.mean()) if len(aa) else None)
    ds = directional_shear(df)
    out["r4"] = {
        "stats": {"n": int(len(a)), "mean": n(a.mean()),
                   "median": n(np.median(a)),
                   "p10": n(np.percentile(a, 10)),
                   "p90": n(np.percentile(a, 90))},
        "diurnal": diurnal_a,
        "directional": {"median": n(np.median(ds)),
                         "p90": n(np.percentile(ds, 90)),
                         "max": n(np.max(ds))},
    }

    # ═══ R5 · Persistence ═══
    runs = persistence_runs(df, 8)
    M = sector_transition_matrix(df, 8)
    out["r5"] = {
        "runs": [{"sector": SECTOR_NAMES_8[i],
                   "n": int(len(runs[i])),
                   "mean": n(np.mean(runs[i])) if len(runs[i]) else None,
                   "p90": n(np.percentile(runs[i], 90)) if len(runs[i]) else None}
                  for i in range(8)],
        "transition": M.tolist(),
        "sectors": list(SECTOR_NAMES_8),
    }

    # ═══ R6 · Mangsa ═══
    prof = mangsa_wind_profile(df)
    per_musim = []
    for mu in MUSIM_ORDER:
        sub = df[df["mangsa"].isin(MUSIM_MEMBERS[mu])]
        ws, wd = sub["ws10"].dropna().values, sub["wd10"].dropna().values
        per_musim.append({"musim": mu, "mean": n(ws.mean()) if len(ws) else None,
                           "p90": n(np.percentile(ws, 90)) if len(ws) else None,
                           "dir": n(circ_mean_deg(wd)), "n": int(len(ws))})
    val = []
    for mu in MUSIM_ORDER:
        wd = df[df["mangsa"].isin(MUSIM_MEMBERS[mu])]["wd10"].dropna().values
        if len(wd) == 0:
            continue
        wq = float(((wd >= 202) & (wd < 292)).mean() * 100)
        eq = float(((wd >= 90) & (wd < 180)).mean() * 100)
        val.append({"musim": mu, "w": wq, "e": eq})
    out["r6"] = {
        "profile": [{"no": no, "nama": nama, "musim": musim,
                      "n": prof[no]["n"], "mean": n(prof[no]["mean"]),
                      "p90": n(prof[no]["p90"]), "max": n(prof[no]["max"]),
                      "dir": n(prof[no]["dir"]), "R": n(prof[no]["R"]),
                      "gf": n(prof[no]["gf"])}
                     for no, nama, musim in MANGSAS_INFO],
        "per_musim": per_musim,
        "validation": val,
    }

    # ═══ R7 · Coupling ═══
    bins = [(0, .05, "Kering"), (.05, 1, "Ringan"),
            (1, 5, "Sedang"), (5, 1e9, "Lebat")]
    comp = []
    for lo, hi, lbl in bins:
        sub = df[(df["precip"] >= lo) & (df["precip"] < hi)]
        if len(sub) == 0:
            continue
        ws, wd = sub["ws10"].dropna().values, sub["wd10"].dropna().values
        m = (np.isfinite(sub["ws10"].values)
             & np.isfinite(sub["gust10"].values) & (sub["ws10"].values >= 1.0))
        gf = (float(np.mean(sub["gust10"].values[m] / sub["ws10"].values[m]))
              if m.any() else None)
        comp.append({"label": lbl, "n": int(len(sub)),
                      "ws": n(ws.mean()) if len(ws) else None, "gf": n(gf),
                      "dir": n(circ_mean_deg(wd)), "R": n(circ_R(wd)),
                      "cloud": n(sub["cloud"].mean()),
                      "cloud_lo": n(sub["cloud_lo"].mean())})

    daily = _daily_aggregate(df)
    lags, prof_u = _cross_corr_profile(daily["u_anom"], daily["p_anom"], 14)
    peak_L, peak_r = _peak_lag(lags, prof_u)

    p_arr = df["precip"].fillna(0).values
    w_arr, u_arr = df["ws10"].values, df["u_comp"].values
    ev = _detect_onset_events(p_arr, 6, 0.5)
    onset = []
    if ev:
        offs = np.arange(-12, 13)
        ws_p, u_p, c = np.zeros(25), np.zeros(25), 0
        for e in ev:
            if e-12 < 0 or e+12 >= len(p_arr):
                continue
            ws_p += w_arr[e-12:e+13]
            u_p += u_arr[e-12:e+13]
            c += 1
        if c:
            ws_p /= c
            u_p /= c
            onset = [{"off": int(o), "ws": n(w), "u": n(u)}
                     for o, w, u in zip(offs, ws_p, u_p)]

    wd_all = df["wd10"].values
    v = np.isfinite(wd_all) & np.isfinite(df["cloud"].values)
    wd_v, c_tot = wd_all[v], df["cloud"].values[v]
    c_lo = df["cloud_lo"].values
    v2 = np.isfinite(wd_all) & np.isfinite(c_lo)
    c_lo_v, wd_lo = c_lo[v2], wd_all[v2]
    sec_t = (((wd_v + 22.5) % 360) // 45).astype(int) % 8
    sec_l = (((wd_lo + 22.5) % 360) // 45).astype(int) % 8
    cloud_sec = [{"sector": SECTOR_NAMES_8[i],
                   "cloud": n(c_tot[sec_t == i].mean()) if (sec_t == i).any() else None,
                   "cloud_lo": n(c_lo_v[sec_l == i].mean()) if (sec_l == i).any() else None}
                  for i in range(8)]

    dj = []
    for h in range(24):
        sub = df[df["hour"] == h]
        dj.append({"h": h, "ws": n(sub["ws10"].dropna().mean()),
                    "precip": n(sub["precip"].fillna(0).mean()),
                    "cloud": n(sub["cloud"].dropna().mean())})

    out["r7"] = {"composite": comp, "onset": {"n": len(ev), "profile": onset},
                  "lag": {"lags": lags.tolist(), "prof": prof_u.tolist(),
                           "peak_lag": int(peak_L), "peak_r": n(peak_r)},
                  "cloud_sector": cloud_sec, "diurnal_joint": dj}

    # ═══ R8 · Reversal ═══
    res = _detect_all_reversals(df)
    if res:
        vals = np.array([r[1] for r in res])
        mean_v, std_v = float(vals.mean()), float(vals.std(ddof=1))
        if std_v > 0:
            z = (vals - mean_v) / std_v
            inl = np.abs(z) < MR_OUTLIER_Z
        else:
            z = np.zeros_like(vals)
            inl = np.ones(len(vals), bool)
        rm = float(vals[inl].mean()) if inl.any() else mean_v
        ys = np.array([r[0] for r in res], dtype=float)
        slope, _, rp, tp = _linear_trend(ys, vals)
        out["r8"] = {
            "per_year": [{"year": int(r[0]), "dopy": float(r[1]),
                           "date": _dopy_to_approx_date(r[0], r[1]),
                           "z": float(zz), "inlier": bool(ok)}
                          for r, zz, ok in zip(res, z, inl)],
            "stats": {"mean": mean_v, "median": float(np.median(vals)),
                       "std": std_v, "robust_mean": rm,
                       "n_outliers": int((~inl).sum()),
                       "min": float(vals.min()), "max": float(vals.max())},
            "trend": {"slope": float(slope), "r": float(rp), "t": float(tp)},
            "offsets": [{"scenario": k, "labuh": float(v),
                          "delta": float(v - rm)}
                         for k, v in SCENARIO_LABUH_DOPY.items()],
        }

    # ═══ R9 · Ekstrem ═══
    def top(field, nn):
        s = df.dropna(subset=[field]).sort_values(field, ascending=False).head(nn)
        return [{"time": str(r["time"]), "value": n(r[field]),
                  "dir": _dir_to_compass(r["wd10"]) if np.isfinite(r["wd10"]) else None,
                  "wd10": n(r["wd10"]), "gust": n(r["gust10"]),
                  "ws10": n(r["ws10"]), "precip": n(r["precip"]) or 0.0,
                  "cloud": n(r["cloud"]),
                  "mangsa": int(r["mangsa"]) if np.isfinite(r["mangsa"]) else None}
                 for _, r in s.iterrows()]

    pcts = [50, 75, 90, 95, 99, 99.9, 99.99]
    perc = []
    for col in ("ws10", "gust10", "ws100"):
        v = df[col].dropna().values
        d = {"field": col, "n": int(len(v))}
        for p in pcts:
            d[f"p{p}"] = n(np.percentile(v, p))
        d["max"] = n(v.max())
        perc.append(d)

    ths = [10, 15, 20, 25, 30, 35, 40, 50]
    exc = []
    for col in ("ws10", "gust10", "ws100"):
        v = df[col].dropna().values
        d = {"field": col, "n": int(len(v))}
        for t in ths:
            d[f"gt_{t}"] = int((v > t).sum())
            d[f"pct_{t}"] = n((v > t).mean() * 100)
        exc.append(d)

    d = df.dropna(subset=["ws10"]).copy()
    d["_y"] = pd.to_datetime(d["time"]).dt.year
    my = []
    for y, sub in d.groupby("_y"):
        r = sub.loc[sub["ws10"].idxmax()]
        my.append({"year": int(y), "ws10": n(r["ws10"]),
                    "dir": _dir_to_compass(r["wd10"]) if np.isfinite(r["wd10"]) else None,
                    "time": str(r["time"])})

    out["r9"] = {"top_ws10": top("ws10", 30), "top_gust": top("gust10", 30),
                  "percentiles": perc, "exceedance": exc,
                  "max_year": my, "thresholds": ths}

    # ═══ R10 · Precursor ═══
    dd = df.copy()
    dd["_date"] = pd.to_datetime(dd["time"]).dt.normalize()
    morn = dd[dd["hour"].between(6, 9)].groupby("_date").agg(
        ws10_morning=("ws10", "mean"), cloud_lo=("cloud_lo", "mean"),
        n=("ws10", "count")).reset_index()
    morn = morn[morn["n"] >= 3].drop(columns=["n"])
    aft = dd[dd["hour"].between(12, 16)].groupby("_date").agg(
        ws10_aft=("ws10", "max"), n=("ws10", "count")).reset_index()
    aft = aft[aft["n"] >= 3].drop(columns=["n"])
    mg = morn.merge(aft, on="_date").dropna()
    if len(mg) >= 30:
        thr = float(mg["ws10_aft"].quantile(0.99))
        mg["ev"] = mg["ws10_aft"] >= thr
        br = float(mg["ev"].mean())
        cont = []
        for col, q, lbl in [
            ("ws10_morning", 0.90, "Angin pagi ≥ P90"),
            ("ws10_morning", 0.75, "Angin pagi ≥ P75"),
            ("ws10_morning", 0.50, "Angin pagi ≥ Median"),
            ("cloud_lo", 0.25, "Cloud rendah ≤ P25"),
        ]:
            t = mg[col].quantile(q)
            sub = mg[mg[col] <= t] if q <= 0.5 else mg[mg[col] >= t]
            if len(sub) < 20:
                continue
            pe = float(sub["ev"].mean())
            cont.append({"condition": lbl, "n": int(len(sub)),
                          "p_event": pe*100, "lift": pe/br if br > 0 else 0})
        rr = float(np.corrcoef(mg["ws10_morning"], mg["ws10_aft"])[0, 1])
        v = df["ws10"].dropna().values
        ac = []
        for lag in (1, 2, 3, 6, 12, 24):
            if len(v) <= lag:
                continue
            a, b = v[:-lag], v[lag:]
            m = np.isfinite(a) & np.isfinite(b)
            if m.sum() < 100:
                continue
            ac.append({"lag": lag, "r": float(np.corrcoef(a[m], b[m])[0, 1])})
        out["r10"] = {"n_days": int(len(mg)), "event_threshold": thr,
                       "base_rate_pct": br*100, "n_events": int(mg["ev"].sum()),
                       "corr_morning": rr, "contingency": cont, "autocorr": ac}

    return out


def main():
    print("Load data ...")
    df = _require_data()
    if df is None:
        sys.exit("Gagal load data.")

    print("Build report 1-10 ...")
    data = build(df)

    print("Tulis wind_data.json ...")
    with open("wind_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    size = Path("wind_data.json").stat().st_size
    print(f"✓ wind_data.json ({size // 1024} kB)")
    print(f"  {data['meta']['n_rows']:,} baris · "
          f"{data['meta']['start']} → {data['meta']['end']}")


if __name__ == "__main__":
    main()