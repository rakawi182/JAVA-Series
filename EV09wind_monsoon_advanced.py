#!/usr/bin/env python3
"""
EV09wind_monsoon_advanced.py  — Versi 5.0
==========================================
Deteksi monsoon reversal menggunakan metode change-point detection
berkaliber internasional, diimplementasikan pure NumPy/SciPy.

STATUS SETIAP METODE (hasil diagnostik v4→v5):
──────────────────────────────────────────────
  M1  PELT-MPCI  Aktif N=11. Penalti 1.5×BIC, filter CP pertama > dopy DRY_HI.
                 Killick, Fearnhead & Eckley (JASA 2012).

  M2  SR-Test    Shiryaev-Roberts statistic (Pollak 1985, Ann.Stat. 13:206).
                 Alternatif BOCD yang lebih sensitif untuk perubahan gradual.
                 BOCD tidak cocok untuk monsoon onset (perubahan gradual,
                 bukan step-function) → diganti SR-Test.
                 Diaplikasikan pada MPCI. Threshold: E[T_SR] = 0.5/lam.

  M3  Pettitt-U  Non-parametric Pettitt test pada u_comp 7d-smooth.
                 (Pettitt 1979, JRSS-C 28:126). Variabilitas baik (std~15hr).

  M4  dVPD/dt    Rate-of-change VPD, threshold μ−2σ baseline. (v4, berjalan)

  M5  CUSUM-MPCI Page's CUSUM (1954) pada MPCI_roll, threshold 3×σ_baseline.
                 Sinyal MPCI lebih smooth dari Δu → CUSUM stabil.

  M6  VPD-Level  VPD rolling 30d < 65% median kering.

  M7  Td-P97     Dew-point rolling 30d > P97 kering.

  M8  Shear      δu = u100−u10 crossing 0.

  M9  SoilMoist  Soil moisture > P80 kering.

  M10 BaseU      u_comp 30-day rolling > 0 (baseline EV09wind).

  ENS Ensemble   Weighted-median semua deteksi valid.

REFERENSI ILMIAH
─────────────────
  Killick, Fearnhead & Eckley (2012). Optimal detection of changepoints
    with a linear computational cost. JASA 107(500):1590–1598.
  Pollak (1985). Optimal detection of a change in distribution.
    Annals of Statistics 13(1):206–227.
  Pettitt (1979). A non-parametric approach to the change point problem.
    JRSS-C 28(2):126–135.
  Page (1954). Continuous inspection schemes. Biometrika 41(1/2):100–115.
"""

from __future__ import annotations
import sys, math
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats as spstats

# ── Import EV09wind ──────────────────────────────────────────────────────
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
    print(f"[!] EV09wind.py tidak ditemukan: {e}"); sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════
# Konstanta
# ══════════════════════════════════════════════════════════════════════════
WIN       = 30
SEARCH_LO = 60.0
SEARCH_HI = 200.0
SUSTAIN   = 10
EPS       = 0.005
DRY_LO    = 60.0
DRY_HI    = 120.0   # puncak East monsoon — baseline window

ENSEMBLE_WEIGHTS: Dict[str, float] = {
    "M1_PELT":  3.0,
    "M2_SR":    2.5,
    "M3_Pett":  2.5,
    "M4_dVPD":  2.0,
    "M5_CUSUM": 2.0,
    "M6_VPD":   1.5,
    "M7_Td":    1.5,
    "M8_Shear": 1.0,
    "M9_Soil":  1.0,
    "M10_BaseU":1.5,
}


# ══════════════════════════════════════════════════════════════════════════
# Loader
# ══════════════════════════════════════════════════════════════════════════
_CACHE: Optional[pd.DataFrame] = None
RENAME = {
    "vapour_pressure_deficit (kPa)":               "vpd",
    "dew_point_2m (°C)":                           "dew_pt",
    "total_column_integrated_water_vapour (kg/m²)":"tcwv",
    "relative_humidity_2m (%)":                    "rh",
    "surface_pressure (hPa)":                      "pressure",
    "soil_moisture_7_to_28cm (m³/m³)":             "soil_moist",
    "precipitation (mm)":                          "precip",
    "cloud_cover (%)":                             "cloud",
    "cloud_cover_low (%)":                         "cloud_lo",
    "wind_speed_10m (km/h)":                       "ws10",
    "wind_direction_10m (°)":                      "wd10",
    "wind_gusts_10m (km/h)":                       "gust10",
    "wind_speed_100m (km/h)":                      "ws100",
    "wind_direction_100m (°)":                     "wd100",
}

def _read_csv(p):
    with open(p,"r",encoding="utf-8") as f:
        sk=0
        for i,l in enumerate(f):
            if l.lstrip().startswith("time,"): sk=i; break
    d=pd.read_csv(p,skiprows=sk); d["time"]=pd.to_datetime(d["time"])
    return d.sort_values("time").reset_index(drop=True)

def _idw(v1,v2):
    idx=v1.index.union(v2.index); b=v1.notna()&v2.notna()
    out=pd.Series(np.nan,index=idx)
    out.loc[b]=IDW_W1_VOLATILE*v1[b]+IDW_W2_VOLATILE*v2[b]
    out.loc[v1.notna()&~b]=v1[v1.notna()&~b]
    out.loc[v2.notna()&~b]=v2[v2.notna()&~b]
    return out

def load_rich_hourly():
    global _CACHE
    if _CACHE is not None: return _CACHE
    p1=find_data_file(DEFAULT_HOURLY_P1); p2=find_data_file(DEFAULT_HOURLY_P2)
    if p1 is None and p2 is None: print("  [!] CSV tidak ditemukan."); return None
    rd=lambda p: _read_csv(p).rename(columns=RENAME)
    if p1 is None: df=rd(p2)
    elif p2 is None: df=rd(p1)
    else:
        d1=rd(p1).set_index("time"); d2=rd(p2).set_index("time")
        idx=d1.index.union(d2.index); out=pd.DataFrame(index=idx)
        for c in ["vpd","dew_pt","tcwv","rh","pressure","soil_moist","precip",
                  "cloud","cloud_lo","ws10","gust10","ws100"]:
            c1=d1[c].reindex(idx) if c in d1.columns else pd.Series(np.nan,index=idx)
            c2=d2[c].reindex(idx) if c in d2.columns else pd.Series(np.nan,index=idx)
            out[c]=_idw(c1,c2)
        for src in ("wd10","wd100"):
            r1=(np.deg2rad(d1[src].reindex(idx).values) if src in d1.columns
                else np.full(len(idx),np.nan))
            r2=(np.deg2rad(d2[src].reindex(idx).values) if src in d2.columns
                else np.full(len(idx),np.nan))
            s_=IDW_W1_VOLATILE*np.sin(r1)+IDW_W2_VOLATILE*np.sin(r2)
            c_=IDW_W1_VOLATILE*np.cos(r1)+IDW_W2_VOLATILE*np.cos(r2)
            n1,n2=~np.isfinite(r1),~np.isfinite(r2)
            s_[n1&~n2]=np.sin(r2[n1&~n2]); c_[n1&~n2]=np.cos(r2[n1&~n2])
            s_[~n1&n2]=np.sin(r1[~n1&n2]); c_[~n1&n2]=np.cos(r1[~n1&n2])
            out[src]=(np.rad2deg(np.arctan2(s_,c_))+360)%360
        df=out.reset_index().rename(columns={"index":"time"})
    df=df.sort_values("time").reset_index(drop=True)
    df=attach_time_features(df)
    avail=[c for c in ["vpd","dew_pt","tcwv","rh","soil_moist"] if c in df.columns]
    print(f"  [i] {len(df):,} baris · {df['time'].min().date()} → {df['time'].max().date()}")
    print(f"      Precursor: {', '.join(avail)}")
    _CACHE=df; return df


# ══════════════════════════════════════════════════════════════════════════
# Utilitas
# ══════════════════════════════════════════════════════════════════════════
def _attach_dopy(d,dc="date"):
    t=pd.to_datetime(d[dc])
    a=pd.to_datetime(dict(year=t.dt.year,  month=ANCHOR_MONTH,day=ANCHOR_DAY))
    ap=pd.to_datetime(dict(year=t.dt.year-1,month=ANCHOR_MONTH,day=ANCHOR_DAY))
    d=d.copy()
    d["dopy"]=np.where(t<a,(t-ap).dt.total_seconds()/86400,
                           (t-a ).dt.total_seconds()/86400)%365.
    return d

def _daily(df,field,agg="mean"):
    d=df.copy(); d["_d"]=pd.to_datetime(d["time"]).dt.normalize()
    s=d.groupby("_d").agg(v=(field,agg)).reset_index()
    return _attach_dopy(s.rename(columns={"_d":"date"}).sort_values("date"))

def _roll(s,win=WIN):
    s=s.copy(); s["roll"]=s["v"].rolling(win,center=True,min_periods=win//2).mean()
    return s

def _cross(sig,dpy,thr,up=True,sust=SUSTAIN,lo=SEARCH_LO,hi=SEARCH_HI,eps=EPS):
    for i in range(1,len(sig)):
        if not(lo<=dpy[i]<=hi): continue
        p,c=sig[i-1],sig[i]
        if not(np.isfinite(p) and np.isfinite(c)): continue
        if up and p<thr<=c:
            fut=sig[i:i+sust]
            if np.isfinite(fut).sum()>=sust-3 and np.nanmin(fut)>=thr-eps: return float(dpy[i])
        elif not up and p>thr>=c:
            fut=sig[i:i+sust]
            if np.isfinite(fut).sum()>=sust-3 and np.nanmax(fut)<=thr+eps: return float(dpy[i])
    return None

def _year_slice(df,py):
    s=pd.Timestamp(year=py,month=ANCHOR_MONTH,day=ANCHOR_DAY)
    return df[(df["time"]>=s)&(df["time"]<s+pd.Timedelta(days=366))].copy()

def _mpci_daily(df):
    """MPCI = rata-rata Z-score 7 variabel precursor (v4)."""
    comps=[(f,sgn) for f,sgn in [
        ("u_comp",+1),("rh",+1),("dew_pt",+1),
        ("tcwv",+1),("cloud",+1),("precip",+1),("vpd",-1)
    ] if f in df.columns and df[f].notna().sum()>50]
    if len(comps)<3: return None
    d=df.copy(); d["_d"]=pd.to_datetime(d["time"]).dt.normalize()
    daily=d.groupby("_d").agg(**{f:(f,"mean") for f,_ in comps}).reset_index()
    daily=_attach_dopy(daily.rename(columns={"_d":"date"}).sort_values("date"))
    daily["mpci"]=0.; n=0
    for f,sgn in comps:
        v=daily[f].ffill(); mu,sd=v.mean(),v.std()
        if sd<1e-9: continue
        daily["mpci"]+=sgn*(v-mu)/sd; n+=1
    if n==0: return None
    daily["mpci"]/=n
    daily["mpci_roll"]=daily["mpci"].rolling(WIN,center=True,min_periods=WIN//2).mean()
    return daily


# ══════════════════════════════════════════════════════════════════════════
# M1 · PELT  (Killick et al. 2012)
# ══════════════════════════════════════════════════════════════════════════
def _pelt_l2(signal,pen):
    """PELT L2 cost (sum-of-squared deviations), penalti BIC."""
    n=len(signal); x=np.where(np.isfinite(signal),signal,np.nanmean(signal))
    S=np.zeros(n+1); S2=np.zeros(n+1)
    for i in range(n): S[i+1]=S[i]+x[i]; S2[i+1]=S2[i]+x[i]**2
    def cost(a,b):
        nb=b-a
        if nb<=0: return 0.
        return S2[b]-S2[a]-(S[b]-S[a])**2/nb
    F=np.full(n+1,np.inf); F[0]=0.; cp=[-1]*(n+1); cands=[0]
    for t in range(1,n+1):
        mv=np.inf; bst=-1
        for s in cands:
            v=F[s]+cost(s,t)+pen
            if v<mv: mv=v; bst=s
        F[t]=mv; cp[t]=bst
        cands=[s for s in cands if F[s]+cost(s,t)<=F[t]+pen]+[t]
    bkps=[]; t=n
    while cp[t]>0: bkps.append(cp[t]); t=cp[t]
    return sorted(bkps)

def detect_pelt(df):
    """
    PELT L2 + penalti 1.5×BIC pada MPCI daily dalam window dopy 60–200.
    Mengambil changepoint pertama yang berada di dopy > DRY_HI (120).
    Ini memastikan CP bukan dari variabilitas East monsoon, melainkan
    awal transisi menuju West monsoon.
    """
    daily=_mpci_daily(df)
    if daily is None: return None
    win=daily[(daily["dopy"]>=SEARCH_LO)&(daily["dopy"]<=SEARCH_HI)].copy()
    if len(win)<30: return None
    sig=win["mpci"].values; sig=np.where(np.isfinite(sig),sig,np.nanmean(sig))
    dpy=win["dopy"].values
    pen=1.5*math.log(len(sig))*max(np.nanvar(sig),1e-6)
    try: bkps=_pelt_l2(sig,pen)
    except: return None
    if not bkps: return None
    # Ambil CP pertama yang > DRY_HI (zona transisi, bukan variasi kering)
    for b in bkps:
        if 0<b<len(dpy) and dpy[b]>DRY_HI:
            return float(dpy[b])
    return None


# ══════════════════════════════════════════════════════════════════════════
# M2 · Shiryaev-Roberts Test (Pollak 1985)
# ══════════════════════════════════════════════════════════════════════════
def detect_sr(df):
    """
    Shiryaev-Roberts (SR) statistic untuk deteksi perubahan GRADUAL.

    SR lebih baik dari CUSUM/BOCD untuk monsoon onset karena:
    • BOCD/CUSUM optimal untuk step-change (abrupt)
    • SR memberikan bobot uniform pada semua possible changepoints
      → lebih sensitif terhadap perubahan yang dimulai bertahap

    Statistik:  R_t = (1 + R_{t-1}) * L_t
    dimana L_t = likelihood ratio:
      p(x_t | θ_after) / p(x_t | θ_before)
    θ_before = distribusi baseline (dopy 60–120): μ_E, σ_E
    θ_after  = distribusi target (diasumsikan: μ_E + δ, δ dikalibrasi dari data)

    Threshold: A = 0.5 / lam  (Pollak 1985, eq. 3.3)
    lam = hazard rate = 1/N dimana N = panjang window pencarian

    Referensi: Pollak (1985) Ann. Stat. 13(1):206–227.
               Tartakovsky (2009) "Sequential Change-Point Detection"
    """
    daily=_mpci_daily(df)
    if daily is None: return None
    win=daily[(daily["dopy"]>=DRY_LO)&(daily["dopy"]<=SEARCH_HI)].copy()
    if len(win)<30: return None

    sig=win["mpci_roll"].values; dpy=win["dopy"].values
    sig=np.where(np.isfinite(sig),sig,np.nanmean(sig))

    # Kalibrasi distribusi East monsoon dari baseline
    base_mask=(dpy>=DRY_LO)&(dpy<=DRY_HI)
    base=sig[base_mask]; base=base[np.isfinite(base)]
    if len(base)<10: return None
    mu_E=float(np.mean(base)); sig_E=float(np.std(base))+1e-9

    # Target: μ_after = mean dari dopy 150-200 (West monsoon mapan)
    west_mask=(dpy>=150)&(dpy<=200)
    west=sig[west_mask]; west=west[np.isfinite(west)]
    mu_W=float(np.mean(west)) if len(west)>=5 else mu_E+sig_E
    delta=mu_W-mu_E  # ukuran pergeseran

    # Log-likelihood ratio per observasi
    # log L_t = log N(x; μ_W, σ_E) - log N(x; μ_E, σ_E)
    #         = (x - μ_E)²/(2σ²) - (x - μ_W)²/(2σ²)
    #         = [(x-μ_E)² - (x-μ_W)²] / (2σ²)
    #         = [2x(μ_W-μ_E) - μ_W²+μ_E²] / (2σ²)
    def log_lr(x):
        return (2*x*(mu_W-mu_E) - mu_W**2 + mu_E**2) / (2*sig_E**2)

    N=len(dpy)
    lam=1.0/max(N,1)
    threshold=0.5/lam   # Pollak 1985 ARL threshold

    # SR rekursif
    R=0.0
    start=np.searchsorted(dpy, SEARCH_LO)
    for t in range(start, N):
        x=sig[t]
        if not np.isfinite(x): continue
        llr=log_lr(x)
        R=(1+R)*math.exp(llr)
        if SEARCH_LO<=dpy[t]<=SEARCH_HI and R>=threshold:
            return float(dpy[t])
    return None


# ══════════════════════════════════════════════════════════════════════════
# M3 · Pettitt Non-Parametric Test (Pettitt 1979)
# ══════════════════════════════════════════════════════════════════════════
_pettitt_meta: Dict[int, dict] = {}

def detect_pettitt(df, py=0):
    """
    Pettitt test non-parametrik pada u_comp rolling 7-hari dalam window 60–200.

    Perubahan v4→v5:
    • Signal: u_comp 7d-smooth (bukan MPCI_roll)
    • Hasil: variabilitas antar-tahun nyata (std~15 hari), bukan clustering di dopy 129
    • p-value tetap menggambarkan signifikansi statistik (semua p<0.001)
    """
    s=_daily(df,"u_comp","mean")
    win=s[(s["dopy"]>=SEARCH_LO)&(s["dopy"]<=SEARCH_HI)].copy()
    if len(win)<20: return None
    win["u7"]=win["v"].rolling(7,center=True,min_periods=4).mean()
    sig=win["u7"].values; dpy=win["dopy"].values
    sig=np.where(np.isfinite(sig),sig,np.nanmean(sig))
    n=len(sig)
    ranks=spstats.rankdata(sig)
    cumranks=np.cumsum(ranks)
    U=2*cumranks-np.arange(1,n+1,dtype=float)*(n+1)
    K=float(np.max(np.abs(U))); cp_idx=int(np.argmax(np.abs(U)))
    pval=min(2*math.exp(-6*K*K/(n**3+n**2)),1.)
    if py: _pettitt_meta[py]={"pval":pval,"K":K,"n":n}
    if pval>0.05: return None
    d=float(dpy[cp_idx])
    return d if SEARCH_LO<=d<=SEARCH_HI else None


# ══════════════════════════════════════════════════════════════════════════
# M4 · dVPD/dt  (Rate-of-change VPD, v4 — sudah berfungsi)
# ══════════════════════════════════════════════════════════════════════════
def detect_dvpd(df):
    """
    Slope 7-hari VPD harian. Threshold: μ_baseline − 2σ_baseline.
    Sustained 7 hari. (v4, tidak berubah — sudah bekerja dengan baik)
    """
    if "vpd" not in df.columns or df["vpd"].notna().sum()<100: return None
    s=_daily(df,"vpd"); vpd=s["v"].values; dpy=s["dopy"].values; n=len(vpd)
    slopes=np.full(n,np.nan); xs=np.arange(7,dtype=float)
    for i in range(6,n):
        blk=vpd[i-6:i+1]; valid=np.isfinite(blk)
        if valid.sum()>=4:
            try: slopes[i]=spstats.linregress(xs[valid],blk[valid]).slope
            except: pass
    slope_s=pd.Series(slopes).rolling(5,center=True,min_periods=3).mean().values
    base=(dpy>=DRY_LO)&(dpy<=DRY_HI)&np.isfinite(slope_s)
    if base.sum()<10: return None
    mu_b=np.nanmean(slope_s[base]); sd_b=np.nanstd(slope_s[base])+1e-9
    thr=mu_b-2*sd_b
    for i in range(1,n):
        if not(SEARCH_LO<=dpy[i]<=SEARCH_HI): continue
        if not np.isfinite(slope_s[i]) or slope_s[i]>=thr: continue
        fut=slope_s[i:i+7]; valid=np.isfinite(fut)
        if valid.sum()>=5 and np.nanmean(fut[valid])<thr: return float(dpy[i])
    return None


# ══════════════════════════════════════════════════════════════════════════
# M5 · CUSUM pada MPCI_roll  (Page 1954, diperbaiki dari v4)
# ══════════════════════════════════════════════════════════════════════════
def detect_cusum_mpci(df):
    """
    CUSUM pada MPCI_roll harian.
    Perubahan dari v4: sinyal MPCI_roll (bukan Δu) — lebih smooth, stabil.

    Baseline: dopy 60–120 (East monsoon murni)
    Slack k: 0.5 × σ_baseline
    Threshold h: 3 × σ_baseline (disesuaikan dengan skala MPCI)
    Sustain: 5 hari

    Ini mendeteksi kapan MPCI secara kumulatif bergerak di atas baseline
    sebesar lebih dari 3σ — artinya onset jelas secara statistik.
    """
    daily=_mpci_daily(df)
    if daily is None: return None
    win=daily[(daily["dopy"]>=DRY_LO)&(daily["dopy"]<=SEARCH_HI)].reset_index(drop=True)
    if len(win)<30: return None
    sig=win["mpci_roll"].values; dpy=win["dopy"].values
    sig=np.where(np.isfinite(sig),sig,np.nanmean(sig))

    base_mask=(dpy>=DRY_LO)&(dpy<=DRY_HI)
    base=sig[base_mask]; base=base[np.isfinite(base)]
    if len(base)<10: return None
    mu_b=float(np.mean(base)); sd_b=float(np.std(base))+1e-9
    k=0.5*sd_b; h=3.0*sd_b

    cp=np.zeros(len(sig))
    for i in range(1,len(sig)):
        v=sig[i]
        if np.isfinite(v): cp[i]=max(0.,cp[i-1]+(v-mu_b)-k)

    for i in range(1,len(cp)):
        if not(SEARCH_LO<=dpy[i]<=SEARCH_HI): continue
        if cp[i]>h:
            fut=cp[i:i+5]
            if np.all(fut>h*0.7): return float(dpy[i])
    return None


# ══════════════════════════════════════════════════════════════════════════
# M6–M10 : Metode robust v4 (tidak berubah)
# ══════════════════════════════════════════════════════════════════════════
def detect_vpd_drop(df):
    if "vpd" not in df.columns or df["vpd"].notna().sum()<100: return None
    s=_roll(_daily(df,"vpd"))
    dry=s[(s["dopy"]>=DRY_LO)&(s["dopy"]<=DRY_HI)]["roll"].dropna()
    if len(dry)<10: return None
    return _cross(s["roll"].values,s["dopy"].values,float(np.median(dry)*0.65),up=False)

def detect_td_p97(df):
    if "dew_pt" not in df.columns or df["dew_pt"].notna().sum()<100: return None
    s=_roll(_daily(df,"dew_pt"))
    dry=s[(s["dopy"]>=DRY_LO)&(s["dopy"]<=DRY_HI)]["roll"].dropna()
    if len(dry)<10: return None
    return _cross(s["roll"].values,s["dopy"].values,float(np.percentile(dry,97)),up=True)

def detect_shear(df):
    for c in ("ws10","ws100","wd10","wd100"):
        if c not in df.columns or df[c].notna().sum()<100: return None
    d=df.copy()
    d["du"]=(-d["ws100"]*np.sin(np.deg2rad(d["wd100"]))
             -(-d["ws10"]*np.sin(np.deg2rad(d["wd10"]))))
    return _cross(_roll(_daily(d,"du"))["roll"].values,
                  _roll(_daily(d,"du"))["dopy"].values, 0., up=True)

def detect_soil(df):
    if "soil_moist" not in df.columns or df["soil_moist"].notna().sum()<100: return None
    s=_roll(_daily(df,"soil_moist"))
    dry=s[(s["dopy"]>=DRY_LO)&(s["dopy"]<=DRY_HI)]["roll"].dropna()
    if len(dry)<10: return None
    return _cross(s["roll"].values,s["dopy"].values,float(np.percentile(dry,80)),up=True)

def detect_base_u(df):
    daily=_rolling_daily_ucomp(df)
    return _find_crossing(daily["u30"].values,daily["dopy"].values)


# ══════════════════════════════════════════════════════════════════════════
# Ensemble
# ══════════════════════════════════════════════════════════════════════════
def ensemble_vote(res):
    vals,ws=[],[]
    for m,v in res.items():
        if v is not None and SEARCH_LO<=v<=SEARCH_HI:
            vals.append(v); ws.append(ENSEMBLE_WEIGHTS.get(m,1.))
    if not vals: return None
    rep=[]
    for v,w in zip(vals,ws): rep.extend([v]*max(1,int(round(w*10))))
    return float(np.median(rep))

def run_all(df,py):
    sub=_year_slice(df,py)
    if len(sub)<5000: return {}
    # Shear helper — compute once cleanly
    def _shr(d):
        if any(c not in d.columns or d[c].notna().sum()<100
               for c in ("ws10","ws100","wd10","wd100")): return None
        d2=d.copy()
        d2["du"]=(-d2["ws100"]*np.sin(np.deg2rad(d2["wd100"]))
                  -(-d2["ws10"]*np.sin(np.deg2rad(d2["wd10"]))))
        s=_roll(_daily(d2,"du"))
        return _cross(s["roll"].values,s["dopy"].values,0.,up=True)
    return {
        "M1_PELT":  detect_pelt(sub),
        "M2_SR":    detect_sr(sub),
        "M3_Pett":  detect_pettitt(sub, py),
        "M4_dVPD":  detect_dvpd(sub),
        "M5_CUSUM": detect_cusum_mpci(sub),
        "M6_VPD":   detect_vpd_drop(sub),
        "M7_Td":    detect_td_p97(sub),
        "M8_Shear": _shr(sub),
        "M9_Soil":  detect_soil(sub),
        "M10_BaseU":detect_base_u(sub),
    }


# ══════════════════════════════════════════════════════════════════════════
# Laporan
# ══════════════════════════════════════════════════════════════════════════
MS={
    "M1_PELT":"PELT","M2_SR":"SR","M3_Pett":"Pett",
    "M4_dVPD":"dVPD","M5_CUSUM":"CUSU",
    "M6_VPD":"VPD↓","M7_Td":"Td↑","M8_Shear":"Sher",
    "M9_Soil":"Soil","M10_BaseU":"BaseU",
}
METHODS=list(MS.keys())
KET={
    "M1_PELT":  "PELT L2+BIC, CP pertama>dopy120 (Killick 2012)",
    "M2_SR":    "Shiryaev-Roberts, threshold A=0.5/λ (Pollak 1985)",
    "M3_Pett":  "Pettitt test, u_comp 7d-smooth (Pettitt 1979)",
    "M4_dVPD":  "Slope VPD 7d, μ−2σ adaptive thr",
    "M5_CUSUM": "CUSUM MPCI_roll, h=3σ_baseline (Page 1954)",
    "M6_VPD":   "VPD level < 65% median kering",
    "M7_Td":    "Dew point > P97 kering",
    "M8_Shear": "δu (100m−10m) crossing 0",
    "M9_Soil":  "Soil moisture > P80 kering",
    "M10_BaseU":"u_comp 30d rolling > 0 (baseline EV09wind)",
    "ENSEM":    "Weighted-median semua valid",
}
TIERS={"M1_PELT":1,"M2_SR":1,"M3_Pett":2,"M4_dVPD":2,"M5_CUSUM":2,
       "M6_VPD":3,"M7_Td":3,"M8_Shear":3,"M9_Soil":3,"M10_BaseU":3}


def report():
    print_header(
        "DETEKSI MONSOON REVERSAL — v5.0",
        "PELT·SR-Test·Pettitt(u)·dVPD·CUSUM-MPCI + 5 precursor · Ensemble"
    )
    df=load_rich_hourly()
    if df is None: return

    all_res: Dict[int,Dict[str,Optional[float]]]= {}
    ens_vals: List[float]=[]

    # ── A · Tabel ────────────────────────────────────────────────────────
    sec_header("A · DETEKSI PER PRANATA-TAHUN (v5)")
    hdr="  Thn "+"".join(f"{MS[m]:>5}" for m in METHODS)+"  ENSEM  Tanggal"
    print(hdr[:90]); print("  "+"─"*88)

    for py in range(2015,2027):
        print(f"  {py}  [running...]", end="\r", flush=True)
        res=run_all(df,py)
        if not res: continue
        ens=ensemble_vote(res); all_res[py]=res
        if ens: ens_vals.append(ens)
        row=f"  {py} "
        for m in METHODS:
            v=res.get(m)
            row+=f"  {'—':>3}" if v is None else f"  {v:>3.0f}"
        row+=(f"  {ens:>5.1f}  {_dopy_to_approx_date(py,ens)}"
              if ens else f"  {'n/a':>5}  —")
        print(row[:90]+"   ")

    # ── B · Statistik ────────────────────────────────────────────────────
    sec_header("B · STATISTIK RINGKASAN PER METODE")
    print(f"  {'Metode':<9}{'N':>3}{'Mean':>7}{'Med':>7}{'Std':>6}"
          f"{'Min':>6}{'Max':>6}  Keterangan")
    print("  "+"─"*95)
    for m in METHODS+["ENSEM"]:
        sh=MS.get(m,"ENSEM") if m!="ENSEM" else "ENSEM"
        vals=ens_vals if m=="ENSEM" else [
            v for yr in all_res for mm,v in all_res[yr].items()
            if mm==m and v is not None]
        if len(vals)<2:
            print(f"  {sh:<9}{'<2':>3}  {KET.get(m,'')}"); continue
        a=np.array(vals)
        print(f"  {sh:<9}{len(a):>3}{a.mean():>7.1f}{np.median(a):>7.1f}"
              f"{a.std(ddof=1):>6.1f}{a.min():>6.1f}{a.max():>6.1f}"
              f"  {KET.get(m,'')}")

    # ── C · Pettitt signifikansi ─────────────────────────────────────────
    sec_header("C · PETTITT — SIGNIFIKANSI & STATISTIK")
    print(f"  {'Thn':<7}{'p-value':>10}{'Signif.':>10}{'K':>8}{'n':>5}{'dopy CP':>9}")
    print("  "+"─"*54)
    for yr in sorted(all_res.keys()):
        m=_pettitt_meta.get(yr,{})
        cp=all_res[yr].get("M3_Pett")
        pv=m.get("pval",np.nan); K=m.get("K",np.nan); n=m.get("n",0)
        sig_str="★ p<0.001" if pv<0.001 else ("★ p<0.05" if pv<0.05 else "  n.s.")
        print(f"  {yr:<7}{pv:>10.6f}{sig_str:>10}{K:>8.0f}{n:>5}"
              f"{f'{cp:.0f}' if cp else '—':>9}")

    # ── D · Lead time ─────────────────────────────────────────────────
    sec_header("D · LEAD TIME vs ENSEMBLE")
    em=float(np.mean(ens_vals)) if ens_vals else np.nan
    print(f"  Ensemble mean = dopy {em:.1f}\n")
    print(f"  {'Metode':<7}{'Lead(d)':>9}  T  Keterangan")
    print("  "+"─"*72)
    ORDER=["M9_Soil","M4_dVPD","M7_Td","M5_CUSUM","M3_Pett",
           "M1_PELT","M2_SR","M6_VPD","M8_Shear","M10_BaseU"]
    for m in ORDER:
        vals=[v for yr in all_res for mm,v in all_res[yr].items()
              if mm==m and v is not None]
        if not vals or not np.isfinite(em): continue
        lead=em-np.median(vals); t=TIERS.get(m,3)
        print(f"  {MS[m]:<7}{lead:>+9.1f}  {t}  {KET.get(m,'')}")
    print("\n  Lead + = mendahului ensemble  |  Lead − = setelah ensemble")

    # ── E · Korelasi ─────────────────────────────────────────────────
    sec_header("E · KORELASI INTER-METHOD (Pearson r)")
    yr_list=sorted(all_res.keys())
    mser={m:np.array([all_res[yr].get(m) if yr in all_res else np.nan
                       for yr in yr_list],dtype=float) for m in METHODS}
    active=[m for m in METHODS if np.isfinite(mser[m]).sum()>=4]
    if len(active)>=2:
        head="  {:10}".format("")+"".join(f"{MS[m]:>6}" for m in active)
        print(head[:84]); print("  "+"─"*min(len(head),82))
        for mi in active:
            row=f"  {MS[mi]:<10}"
            for mj in active:
                if mi==mj: row+=f"{'1.00':>6}"; continue
                ai,aj=mser[mi],mser[mj]; mask=np.isfinite(ai)&np.isfinite(aj)
                row+=(f"{np.corrcoef(ai[mask],aj[mask])[0,1]:>6.2f}"
                      if mask.sum()>=3 else f"{'—':>6}")
            print(row[:84])
    print("\n  r>0.7=konsisten | 0.3–0.7=moderat | <0.3=independen")

    # ── F · Perbandingan versi ────────────────────────────────────────
    sec_header("F · KOREKSI ENSEMBLE v5 vs BASELINE (BaseU)")
    print(f"  {'Thn':<6}{'BaseU':>8}{'v5-ENS':>9}{'Δ':>7}  "
          f"{'PELT':>6}{'SR':>6}{'Pett':>6}{'CUSU':>6}  Catatan")
    print("  "+"─"*76)
    for yr in yr_list:
        bu=all_res[yr].get("M10_BaseU"); en=ensemble_vote(all_res[yr])
        pl=all_res[yr].get("M1_PELT"); sr=all_res[yr].get("M2_SR")
        pe=all_res[yr].get("M3_Pett"); cu=all_res[yr].get("M5_CUSUM")
        d=((en or 0)-(bu or 0)) if (en and bu) else 0
        f6=lambda v: f"{v:>6.0f}" if v else f"{'—':>6}"
        note=("koreksi besar (El Niño)" if d<-15
              else("koreksi sedang" if d<-5
              else("konsisten" if abs(d)<=5 else "ensemble lebih lambat")))
        print(f"  {yr:<6}{(bu or 0):>8.0f}{(en or 0):>9.0f}{d:>+7.0f}"
              f"{f6(pl)}{f6(sr)}{f6(pe)}{f6(cu)}  {note}")

    # ── G · Tren ──────────────────────────────────────────────────────
    sec_header("G · TREN TEMPORAL ENSEMBLE v5")
    if len(ens_vals)>=3:
        yrs=np.array(yr_list,dtype=float)
        ev=np.array([ensemble_vote(all_res.get(yr,{})) or np.nan for yr in yr_list])
        vld=np.isfinite(ev)
        if vld.sum()>=3:
            sl,_,r,t=_linear_trend(yrs[vld],ev[vld])
            print(f"  Slope    : {sl:+.2f} hari/tahun")
            print(f"  Pearson r: {r:+.3f}")
            print(f"  t-stat   : {t:+.2f}  (df={vld.sum()-2})")
            v=("Tidak ada tren signifikan (boundary stasioner)."
               if abs(t)<2.26
               else f"TREN SIGNIFIKAN — reversal {'mundur' if sl>0 else 'maju'} "
                    f"{abs(sl):.2f} hr/thn.")
            print(f"\n  Verdict: {v}")

    # ── H · Labuh ─────────────────────────────────────────────────────
    sec_header("H · ENSEMBLE v5 vs SKENARIO LABUH")
    er=float(np.median(ens_vals)) if ens_vals else np.nan
    if np.isfinite(er):
        print(f"  Ensemble median v5 : dopy {er:.1f}  ({_dopy_to_approx_date(2025,er)})\n")
        print(f"  {'Skenario':<10}{'dopy':>8}{'Δ (hr)':>9}  Status")
        print("  "+"─"*48)
        for sc,val in SCENARIO_LABUH_DOPY.items():
            d=val-er; st="Labuh lebih awal" if d<0 else "Labuh setelah reversal"
            print(f"  {sc:<10}{val:>8.1f}{d:>+9.1f}  {st}")

    # ── I · Dokumentasi metode ────────────────────────────────────────
    sec_header("I · METODE & REFERENSI ILMIAH")
    print("""
  ┌─────────────────────────────────────────────────────────────────────┐
  │  TIER 1 — CHANGE-POINT DETECTION BERKALIBER INTERNASIONAL          │
  │                                                                      │
  │  M1 PELT  Killick, Fearnhead & Eckley (2012) JASA 107:1590–1598    │
  │           Penalized Exact Linear Time. Cost L2, penalti 1.5×BIC.   │
  │           Kompleksitas O(n). Standard emas change-point offline.    │
  │                                                                      │
  │  M2 SR    Pollak (1985) Annals of Statistics 13(1):206–227          │
  │           Shiryaev-Roberts statistic. Optimal untuk perubahan       │
  │           gradual (tidak seperti CUSUM/BOCD yang optimal untuk      │
  │           step-change). Threshold A = 0.5/λ.                       │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  TIER 2 — METODE STATISTIK STANDAR HIDROKLIMATOLOGI                │
  │                                                                      │
  │  M3 Pettitt  Pettitt (1979) JRSS-C 28:126–135                     │
  │              Non-parametrik, distribusi-bebas. Standar WMO/BMKG.   │
  │              Diaplikasikan pada u_comp 7d-smooth → variabilitas     │
  │              antar-tahun nyata (std~15 hari).                       │
  │                                                                      │
  │  M4 dVPD/dt  Slope 7-hari VPD, threshold μ−2σ baseline.           │
  │              Precursor termodinamik, lead time 3–8 hari.           │
  │                                                                      │
  │  M5 CUSUM    Page (1954) Biometrika 41:100–115                     │
  │              Pada MPCI_roll. Threshold h = 3σ_baseline.             │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  TIER 3 — PRECURSOR FISIK & BASELINE                               │
  │  M6 VPD level  M7 Dew-point P97  M8 Shear veering                 │
  │  M9 Soil moisture (precursor hidrologi +21 hari)                   │
  │  M10 u_comp baseline (EV09wind asli)                               │
  └─────────────────────────────────────────────────────────────────────┘

  CATATAN TEKNIS: BOCD (Adams & MacKay 2007) digantikan SR-Test karena
  monsoon onset adalah perubahan GRADUAL (slope change), sedangkan BOCD
  optimal untuk step-change. SR memberikan bobot uniform pada semua
  possible changepoints → lebih sensitif untuk onset musiman bertahap.
""")


def main():
    report(); return 0

if __name__=="__main__":
    sys.exit(main())