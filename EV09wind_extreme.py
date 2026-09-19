#!/usr/bin/env python3
"""
EV09wind_extreme.py — Ekstraksi kecepatan angin & gust ekstrem
================================================================

Membaca langsung file hourly10yr P1+P2 melalui loader di EV09wind.py,
kemudian mengekstrak:

  A. Top-N jam dengan wind speed 10m tertinggi (absolut)
  B. Top-N jam dengan gust tertinggi (absolut)
  C. Top-N jam dengan wind speed 100m tertinggi
  D. Max per tahun (untuk indikasi return period)
  E. Max per bulan (musiman)
  F. Distribusi persentil: P50, P90, P95, P99, P99.9, P99.99
  G. Exceedance count: berapa jam di atas threshold
  H. Event clustering: gabungkan jam-jam berurutan > P99.9 jadi event

Jalankan: python EV09wind_extreme.py
"""
from __future__ import annotations

import sys
from typing import List, Tuple
import numpy as np
import pandas as pd

from EV09wind import (
    _require_data, _dir_to_compass, MONTH_SHORT,
    box_top, box_row, box_mid, box_bot, thin_hbar, sec_header, W,
)


# ─────────────────────────────────────────────────────────────────────────

def top_n_events(df: pd.DataFrame, field: str, n: int = 30
                 ) -> pd.DataFrame:
    cols = ["time", "ws10", "wd10", "wd100", "gust10", "ws100",
            "precip", "cloud", "mangsa", "year"]
    cols = [c for c in cols if c in df.columns]
    sub = df[cols].copy()
    sub = sub.dropna(subset=[field])
    sub = sub.sort_values(field, ascending=False).head(n).reset_index(drop=True)
    sub["dir_compass"] = sub["wd10"].apply(_dir_to_compass)
    return sub


def max_per_year(df: pd.DataFrame, field: str = "ws10"
                 ) -> pd.DataFrame:
    """Max field per tahun Gregorian."""
    d = df.dropna(subset=[field]).copy()
    d["year"] = pd.to_datetime(d["time"]).dt.year
    base_cols = ["year", "time", "wd10"]
    extra = [c for c in ("gust10", "ws100", "ws10") if c in df.columns]
    cols = list(dict.fromkeys(base_cols + [field] + extra))
    out = d.loc[d.groupby("year")[field].idxmax(), cols
                ].reset_index(drop=True)
    out["dir_compass"] = out["wd10"].apply(_dir_to_compass)
    return out


def max_per_month(df: pd.DataFrame, field: str = "ws10"
                  ) -> pd.DataFrame:
    """Max field per bulan kalender (12 bulan)."""
    d = df.dropna(subset=[field]).copy()
    d["month"] = pd.to_datetime(d["time"]).dt.month
    base_cols = ["month", "time", "wd10"]
    extra = [c for c in ("gust10", "ws100", "ws10") if c in df.columns]
    cols = list(dict.fromkeys(base_cols + [field] + extra))
    out = d.loc[d.groupby("month")[field].idxmax(), cols
                ].reset_index(drop=True)
    out["dir_compass"] = out["wd10"].apply(_dir_to_compass)
    return out.sort_values("month").reset_index(drop=True)


def percentile_table(df: pd.DataFrame) -> pd.DataFrame:
    """Persentil tinggi untuk ws10, gust10, ws100."""
    rows = []
    pcts = [50, 75, 90, 95, 99, 99.9, 99.99]
    for col in ("ws10", "gust10", "ws100"):
        if col not in df.columns:
            continue
        v = df[col].dropna().values
        if len(v) == 0:
            continue
        row = {"field": col, "N": len(v)}
        for p in pcts:
            row[f"P{p}"] = float(np.percentile(v, p))
        row["max"] = float(v.max())
        rows.append(row)
    return pd.DataFrame(rows)


def exceedance_table(df: pd.DataFrame,
                      thresholds: List[float] = None
                      ) -> pd.DataFrame:
    """Hitung jumlah jam > threshold untuk ws10, gust10, ws100."""
    if thresholds is None:
        thresholds = [10, 15, 20, 25, 30, 35, 40, 50]
    rows = []
    for col in ("ws10", "gust10", "ws100"):
        if col not in df.columns:
            continue
        v = df[col].dropna().values
        n = len(v)
        if n == 0:
            continue
        row = {"field": col, "N": n}
        for t in thresholds:
            cnt = int((v > t).sum())
            row[f">{t}"] = cnt
            row[f">{t}_%"] = cnt / n * 100.0
        rows.append(row)
    return pd.DataFrame(rows)


def cluster_events(df: pd.DataFrame, field: str = "ws10",
                    quantile: float = 0.999,
                    min_gap_hr: int = 6,
                    ) -> List[dict]:
    """Kelompokkan jam-jam ekstrem (>quantile) menjadi event.

    Dua jam ekstrem dianggap bagian dari event yang sama kalau jarak
    waktunya < min_gap_hr. Setiap event dilaporkan: waktu mulai, durasi,
    puncak, arah puncak, gust puncak.
    """
    d = df.dropna(subset=[field]).sort_values("time").reset_index(drop=True)
    thr = float(d[field].quantile(quantile))
    extreme = d[d[field] >= thr].copy()
    if len(extreme) == 0:
        return []

    times = pd.to_datetime(extreme["time"]).values
    events: List[dict] = []
    cur_idx = [0]
    for i in range(1, len(extreme)):
        gap_hr = (times[i] - times[i - 1]) / np.timedelta64(1, "h")
        if gap_hr <= min_gap_hr:
            cur_idx.append(i)
        else:
            events.append(_summarize_event(extreme, cur_idx, field, thr))
            cur_idx = [i]
    if cur_idx:
        events.append(_summarize_event(extreme, cur_idx, field, thr))
    events.sort(key=lambda e: e["peak"], reverse=True)
    return events


def _summarize_event(extreme: pd.DataFrame, idx: List[int],
                      field: str, thr: float) -> dict:
    sub = extreme.iloc[idx]
    peak_i = sub[field].idxmax()
    peak_row = extreme.loc[peak_i]
    t_start = pd.to_datetime(sub["time"].min())
    t_end = pd.to_datetime(sub["time"].max())
    duration_hr = (t_end - t_start) / pd.Timedelta(hours=1) + 1
    return {
        "start": t_start,
        "end": t_end,
        "duration_hr": int(duration_hr),
        "n_hours": len(sub),
        "peak": float(peak_row[field]),
        "peak_time": pd.to_datetime(peak_row["time"]),
        "peak_dir": _dir_to_compass(peak_row.get("wd10", float("nan"))),
        "peak_gust": float(peak_row.get("gust10", float("nan")))
                       if "gust10" in peak_row else float("nan"),
        "threshold": thr,
    }


# ─────────────────────────────────────────────────────────────────────────
# Reports
# ─────────────────────────────────────────────────────────────────────────

def print_header(title: str, sub: str = "") -> None:
    print()
    print(box_top())
    print(box_row("EXTREME WIND ANALYSIS — EV09-WIND"))
    print(box_row(title))
    if sub:
        print(box_row(sub))
    print(box_row("Sumber: hourly10yr P1+P2 · IDW merge · 2015-01-01 → 2026-09-13"))
    print(box_bot())


def report_top_speed(df: pd.DataFrame, n: int = 30) -> None:
    print_header(f"TOP-{n} WIND SPEED 10m TERTINGGI",
                 "Setiap baris = 1 jam di titik target")
    sec_header(f"TOP-{n} KEJADIAN")
    tbl = top_n_events(df, "ws10", n)
    print(f"  {'#':>3}  {'Waktu':<17} {'ws10':>7} {'Dir':<5} {'wd°':>6} "
          f"{'Gust':>7} {'ws100':>7} {'Rain':>6} {'Cld%':>5} {'M':>3}")
    print("  " + "─" * 78)
    for i, row in tbl.iterrows():
        t = row["time"]
        ts = f"{t.day:02d} {MONTH_SHORT[t.month]} {t.year} {t.hour:02d}:00"
        print(f"  {i+1:>3}  {ts:<17} "
              f"{row['ws10']:>7.2f} "
              f"{row.get('dir_compass', '—'):<5} "
              f"{row['wd10']:>6.1f} "
              f"{row.get('gust10', float('nan')):>7.2f} "
              f"{row.get('ws100', float('nan')):>7.2f} "
              f"{row.get('precip', 0.0):>6.2f} "
              f"{row.get('cloud', float('nan')):>5.0f} "
              f"{int(row.get('mangsa', 0) or 0):>3}")
    print()


def report_top_gust(df: pd.DataFrame, n: int = 30) -> None:
    print_header(f"TOP-{n} GUST TERTINGGI",
                 "Gust = wind_gusts_10m dari model IFS HRES")
    sec_header(f"TOP-{n} KEJADIAN")
    tbl = top_n_events(df, "gust10", n)
    print(f"  {'#':>3}  {'Waktu':<17} {'Gust':>7} {'ws10':>7} "
          f"{'GF':>6} {'Dir':<5} {'wd°':>6} {'Rain':>6} {'Cld%':>5} {'M':>3}")
    print("  " + "─" * 78)
    for i, row in tbl.iterrows():
        t = row["time"]
        ts = f"{t.day:02d} {MONTH_SHORT[t.month]} {t.year} {t.hour:02d}:00"
        ws = row.get("ws10", float("nan"))
        gf = row["gust10"] / ws if ws and ws >= 1.0 else float("nan")
        print(f"  {i+1:>3}  {ts:<17} "
              f"{row['gust10']:>7.2f} "
              f"{ws:>7.2f} "
              f"{gf:>6.2f} "
              f"{row.get('dir_compass', '—'):<5} "
              f"{row['wd10']:>6.1f} "
              f"{row.get('precip', 0.0):>6.2f} "
              f"{row.get('cloud', float('nan')):>5.0f} "
              f"{int(row.get('mangsa', 0) or 0):>3}")
    print()


def report_top_speed_100m(df: pd.DataFrame, n: int = 20) -> None:
    if "ws100" not in df.columns or not df["ws100"].notna().any():
        print("  [!] Tidak ada kolom wind_speed_100m.")
        return
    print_header(f"TOP-{n} WIND SPEED 100m TERTINGGI",
                 "Kecepatan di ketinggian 100m — proxy untuk shear ekstrem")
    sec_header(f"TOP-{n} KEJADIAN")
    tbl = top_n_events(df, "ws100", n)
    print(f"  {'#':>3}  {'Waktu':<17} {'ws100':>7} {'ws10':>7} "
          f"{'α':>6} {'Dir100':<7} {'wd100°':>7} {'M':>3}")
    print("  " + "─" * 70)
    for i, row in tbl.iterrows():
        t = row["time"]
        ts = f"{t.day:02d} {MONTH_SHORT[t.month]} {t.year} {t.hour:02d}:00"
        ws10 = row.get("ws10", float("nan"))
        ws100 = row["ws100"]
        alpha = (np.log(ws100 / ws10) / np.log(10.0)
                 if ws10 and ws10 > 0.5 else float("nan"))
        wd100 = row.get("wd100", float("nan"))
        d100 = _dir_to_compass(wd100) if np.isfinite(wd100) else "—"
        print(f"  {i+1:>3}  {ts:<17} "
              f"{ws100:>7.2f} "
              f"{ws10:>7.2f} "
              f"{alpha:>6.3f} "
              f"{d100:<7} "
              f"{wd100:>7.1f} "
              f"{int(row.get('mangsa', 0) or 0):>3}")
    print()


def report_max_per_year(df: pd.DataFrame) -> None:
    print_header("MAX PER TAHUN", "Wind speed & gust absolut per tahun")
    sec_header("WIND SPEED 10m")
    tbl = max_per_year(df, "ws10")
    print(f"  {'Tahun':<7}{'Waktu Puncak':<22}{'ws10':>8}"
          f"{'Dir':<6}{'wd°':>7}{'Gust':>8}")
    print("  " + "─" * 60)
    for _, r in tbl.iterrows():
        t = r["time"]
        ts = f"{t.day:02d} {MONTH_SHORT[t.month]} {t.year} {t.hour:02d}:00"
        print(f"  {int(r['year']):<7}{ts:<22}"
              f"{r['ws10']:>8.2f} "
              f"{r.get('dir_compass', '—'):<6}"
              f"{r['wd10']:>7.1f}"
              f"{r.get('gust10', float('nan')):>8.2f}")

    print()
    sec_header("GUST 10m")
    tbl_g = max_per_year(df, "gust10")
    print(f"  {'Tahun':<7}{'Waktu Puncak':<22}{'Gust':>8}"
          f"{'ws10':>8}{'GF':>7}")
    print("  " + "─" * 55)
    for _, r in tbl_g.iterrows():
        t = r["time"]
        ts = f"{t.day:02d} {MONTH_SHORT[t.month]} {t.year} {t.hour:02d}:00"
        ws = r.get("ws10", float("nan"))
        gf = r["gust10"] / ws if ws and ws >= 1.0 else float("nan")
        print(f"  {int(r['year']):<7}{ts:<22}"
              f"{r['gust10']:>8.2f}"
              f"{ws:>8.2f}"
              f"{gf:>7.2f}")
    print()


def report_max_per_month(df: pd.DataFrame) -> None:
    print_header("MAX PER BULAN", "Puncak absolut per bulan kalender")
    tbl_ws = max_per_month(df, "ws10").set_index("month")
    tbl_g  = max_per_month(df, "gust10").set_index("month")

    print(f"  {'Bln':<5}{'ws10max':>9}  {'Kapan':<18}"
          f"{'Gustmax':>9}  {'Kapan':<18}")
    print("  " + "─" * 64)
    for m in range(1, 13):
        ws_row = tbl_ws.loc[m] if m in tbl_ws.index else None
        g_row  = tbl_g.loc[m]  if m in tbl_g.index  else None
        ws_v = ws_row["ws10"] if ws_row is not None else float("nan")
        ws_t = ws_row["time"] if ws_row is not None else None
        g_v  = g_row["gust10"] if g_row is not None else float("nan")
        g_t  = g_row["time"] if g_row is not None else None
        ws_ts = (f"{ws_t.day:02d} {MONTH_SHORT[ws_t.month]} {ws_t.year}"
                 if ws_t is not None else "—")
        g_ts  = (f"{g_t.day:02d} {MONTH_SHORT[g_t.month]} {g_t.year}"
                 if g_t is not None else "—")
        print(f"  {MONTH_SHORT[m]:<5}"
              f"{ws_v:>9.2f}  {ws_ts:<18}"
              f"{g_v:>9.2f}  {g_ts:<18}")
    print()


def report_percentiles(df: pd.DataFrame) -> None:
    print_header("DISTRIBUSI PERSENTIL",
                 "Nilai ambang untuk klasifikasi ekstrem")
    sec_header("TABEL PERSENTIL")
    tbl = percentile_table(df)
    cols = [c for c in tbl.columns if c != "field" and c != "N"]
    hdr = f"  {'Field':<8}{'N':>10}" + "".join(f"{c:>10}" for c in cols)
    print(hdr[:W])
    print("  " + "─" * (min(len(hdr) - 2, W - 4)))
    for _, r in tbl.iterrows():
        row = f"  {r['field']:<8}{int(r['N']):>10,}"
        for c in cols:
            row += f"{r[c]:>10.2f}"
        print(row[:W])
    print()
    print("  Keterangan:")
    print("    ws10, gust10, ws100 — semua dalam km/h")
    print("    P99.9  = ambang untuk 'sangat ekstrem' (1 dari 1000 jam)")
    print("    P99.99 = ambang untuk 'ekstrem sekali' (1 dari 10000 jam)")


def report_exceedance(df: pd.DataFrame) -> None:
    print_header("EXCEEDANCE COUNT",
                 "Berapa jam data > threshold (dari total ~102.576 jam)")
    sec_header("TABEL EXCEEDANCE")
    tbl = exceedance_table(df)
    # Kolom count
    count_cols = [c for c in tbl.columns if c.startswith(">")
                  and not c.endswith("_%")]
    pct_cols   = [c for c in tbl.columns if c.endswith("_%")]
    hdr = f"  {'Field':<8}{'N':>10}"
    for c in count_cols:
        hdr += f"{c:>8}"
    print(hdr[:W])
    print("  " + "─" * (min(len(hdr), W - 4)))
    for _, r in tbl.iterrows():
        row = f"  {r['field']:<8}{int(r['N']):>10,}"
        for c in count_cols:
            row += f"{int(r[c]):>8,}"
        print(row[:W])

    print()
    sec_header("PERSENTASE WAKTU (% dari total jam)")
    hdr = f"  {'Field':<8}{'N':>10}"
    for c in pct_cols:
        hdr += f"{c.replace('>','>').replace('_%',''):>8}"
    print(hdr[:W])
    print("  " + "─" * (min(len(hdr), W - 4)))
    for _, r in tbl.iterrows():
        row = f"  {r['field']:<8}{int(r['N']):>10,}"
        for c in pct_cols:
            row += f"{r[c]:>7.2f}%"
        print(row[:W])
    print()


def report_events(df: pd.DataFrame) -> None:
    print_header("EVENT CLUSTERING",
                 "Gabungkan jam-jam > P99.9 menjadi event tunggal")
    for field, label in (("ws10", "Wind Speed 10m"),
                          ("gust10", "Gust 10m")):
        if field not in df.columns or not df[field].notna().any():
            continue
        sec_header(f"EVENT DARI {label} (> P99.9)")
        events = cluster_events(df, field=field, quantile=0.999,
                                 min_gap_hr=6)
        if not events:
            print("  (tidak ada event)")
            continue
        print(f"  Total event: {len(events)}")
        print()
        print(f"  {'#':>3}  {'Mulai':<17}{'Selesai':<17}"
              f"{'Dur':>5}{'Jam':>5}{'Peak':>7}{'Dir':<6}{'Gust':>7}")
        print("  " + "─" * 72)
        for i, ev in enumerate(events[:20], start=1):
            ts1 = (f"{ev['start'].day:02d} "
                   f"{MONTH_SHORT[ev['start'].month]} "
                   f"{ev['start'].year} {ev['start'].hour:02d}:00")
            ts2 = (f"{ev['end'].day:02d} "
                   f"{MONTH_SHORT[ev['end'].month]} "
                   f"{ev['end'].year} {ev['end'].hour:02d}:00")
            print(f"  {i:>3}  {ts1:<17}{ts2:<17}"
                  f"{ev['duration_hr']:>5}"
                  f"{ev['n_hours']:>5}"
                  f"{ev['peak']:>7.2f} "
                  f"{ev['peak_dir']:<6}"
                  f"{ev['peak_gust']:>7.2f}")
        if len(events) > 20:
            print(f"  ... dan {len(events) - 20} event lainnya")
        print()


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main() -> int:
    df = _require_data()
    if df is None:
        return 1

    report_top_speed(df, n=30)
    report_top_gust(df, n=30)
    report_top_speed_100m(df, n=20)
    report_max_per_year(df)
    report_max_per_month(df)
    report_percentiles(df)
    report_exceedance(df)
    report_events(df)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Dihentikan.")
        sys.exit(0)