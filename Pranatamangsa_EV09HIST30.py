#!/usr/bin/env python3
"""
Pranata Mangsa — Meteorological, ENSO, IOD, and Astronomical Calendar Model
===========================================================================

EV09: Hybrid calibration — EV08 (adaptive IDW) × EV08b (GIDW). All calibration numbers, per-mangsa
deltas, confidence intervals, and limitation notes from EV06b are retained
in full. Physics is unchanged.

METEOROLOGICAL DATA SOURCES
---------------------------
  · Target point : −7.5220°S, 112.5661°E (MJS Obs., EAST JAVA), 28 m a.s.l.
  · Station P1   : ERA5/ERA5-Land/IFS-HRES Open-Meteo — daily 1950–2026,
                   6-hourly 2015–2026, hourly 2015–2026
                   Coordinates: −7.486819°S, 112.538210°E · Elev: 28 m
  · Station P2   : ERA5/ERA5-Land/IFS-HRES Open-Meteo — daily 1940–2026,
                   6-hourly 1995–2026, hourly 2015–2026
                   Coordinates: −7.5571175°S, 112.557350°E · Elev: 28 m
    Interpolation: HYBRID — per-field optimal source strategy
                   Volatile fields (vpd,tcwv,cloud,sun_h):
                     EV08 adaptive IDW (p adaptive, Haversine 3D, Q factor)
                     w1_vpd=0.4154 (P1), w2_vpd=0.5846 (P2)
                   Stable/consensus fields (sm_sh,sm_dp,sT_sh,sT_dp):
                     avg(EV08, EV08b) — two independent methods agree
                     sm_dp: EV08=0.139–0.328, EV08b=0.133–0.319 → RMS 0.019
                   GIDW (EV08b) lapse & hipsometric corrections: retained
                   VPD uncertainty (σ) stored in M6H_VPD_SIGMA per mangsa
                   (EV06b plain IDW p=2: w1=0.3953, w2=0.6047)
  · ENSO Niño3.4 weekly — AVISO/DUACS, 1993–2026

ASTRONOMICAL DATA SOURCES
-------------------------
  · Ephemeris       : VSOP87D (~1″ accuracy) via JRC_Ephemeris v5.0
  · Nutation & precession: IERS 2010, full tables (IAU 2000A/2006A)
  · ΔT (TT−UTC)     : HMNAO table, linear interpolation
  · Calibration span: 2020–2029 (10-year mean)
  · Location        : −7.521951°S, 112.566089°E, 28 m a.s.l.
  · Asterism        : Orion's Belt (Alnitak, Alnilam, Mintaka) mean

ASTRONOMICAL EVENTS CALIBRATED (2020–2029 mean)
-----------------------------------------------
  ┌───────────────────────────────────────────────┬────────┬──────────┬──────────┐
  │ Event                                         │ Date   │  dopy    │ Trad dpy │
  ├───────────────────────────────────────────────┼────────┼──────────┼──────────┤
  │ June solstice      (λ☉=90°)                   │ 21 Jun │   -0.81  │    0     │
  │ December solstice  (λ☉=270°)                  │ 21 Dec │  182.71  │  184     │
  │ March equinox      (λ☉=0°)                    │ 20 Mar │  271.75  │  273     │
  │ September equinox  (λ☉=180°)                  │ 23 Sep │   92.85  │   92     │
  │ Zenith Sun I       (δ☉=−7.52°, Oct)           │ 12 Oct │  112.37  │  113     │
  │ Zenith Sun II      (δ☉=−7.52°, Mar)           │ 01 Mar │  252.46  │  253     │
  │ Orion Heliacal Rise (dawn rising)             │ 25 Jun │    3.11  │    0     │
  │ Orion Acronychal Rise (first seen at dusk)    │ 05 Dec │  166.16  │  167     │
  │ Orion Evening Culmination (evening heliacal)  │ 01 Mar │  252.50  │  253     │
  │ Orion Midnight Culmination (HA=0°, 00:00)     │ 08 Dec │  168.91  │  252*    │
  │ Orion Acronychal Set (last seen at dusk)      │ 18 Jun │  361.93  │  347**   │
  └───────────────────────────────────────────────┴────────┴──────────┴──────────┘
  *  Traditional dopy≈252 (1 Mar) refers to Evening Heliacal Culmination
     (dusk culmination), not to noon transit; midnight culmination occurs
     on 8 Dec (Δ ≈ −84 days).
  ** Traditional dopy=347 (4 Jun) refers to the dawn heliacal set
     (Δ ≈ +15 d from acronychal set).

ASTRONOMICAL CALIBRATION FINDINGS (EV02 vs EV01, inherited by EV03/EV04)
------------------------------------------------------------------------
  · Year anchor (June solstice): occurs 21 Jun (~0.81 d before the
    traditional 22 Jun) → small correction of −1 day; precise anchor
    is 21 Jun.
  · December solstice: 21 Dec (not traditional 22 Dec), dopy 182.71 vs 184.
  · Zenith Sun I: 12 Oct (not traditional 13 Oct).
  · Zenith Sun II: 1 Mar (same as traditional, Δ−0.54 d, not significant).
  · Orion Heliacal Rise: 25 Jun (dopy≈3.1, not 22 Jun/dopy=0 traditional).
    → Mangsa-1 Kasa does NOT start at Orion heliacal rise.
    → Orion becomes first visible ~3 days after the June solstice.
  · Orion Evening Rise (first visible at dusk): 5 Dec (dopy=166.16, vs
    6 Dec/dopy=167) → consistent with traditional within ±1 day.
  · Orion Evening Heliacal Culmination (dusk culmination): ~1 Mar
    (dopy≈252.5). → Matches traditional "1 Mar" (Mangsa-9). Culmination
    occurs at ~18:30 WIB, during dusk (sun set ~37–60 min earlier).
    Ammarell (1991) Table 3: epoch 1850 = 26 Feb, epoch 2025 ≈ 1 Mar.
  · Orion Midnight Culmination: 8 Dec (dopy=168.91).
    → DIFFERENT from dusk culmination (1 Mar). On 8 Dec, Orion culminates
    exactly at midnight 00:00 WIB. This is not about noon transit.
  · Orion Acronychal Set: 18 Jun (dopy=361.93, vs traditional 4 Jun/
    dopy=347). → If using the dawn heliacal set definition: Alnilam
    becomes invisible at dawn ≈ 25 Jun (coinciding with the next
    heliacal rise).


6-HOURLY METEOROLOGICAL CALIBRATION FINDINGS (EV08b GIDW → EV09 HYBRID)
-------------------------------------------------------------------------
  · EV09 is a hybrid of EV08 (adaptive IDW, idw_meteorological_interpolation.py)
    and EV08b (GIDW, met_idw_blender.py).  Strategy per field:

    VOLATILE fields (EV08 wins): vpd, tcwv, cloud, cloud_aft, sun_h
      Reason: GIDW α=0.82–0.91 amplifies inter-station residuals ~4.5×
      during the transition season (Kalima M5, Kanem M6).  EV08 values
      are within ±5% of EV07 baseline and avoid over-fitting a linear
      gradient estimated from only 2 stations 8 km apart.
      VPD M5 EV08=1.169 vs EV08b=1.408 kPa (Δ=+0.239, 20%): EV08 retained.
      VPD M6 EV08=0.627 vs EV08b=0.812 kPa (Δ=+0.185, 29%): EV08 retained.

    CONSENSUS fields (avg(EV08, EV08b)):  sm_sh, sm_dp, sT_sh, sT_dp
      Reason: two independent methods converge (RMS difference < 0.020 m³/m³
      for soil moisture, < 0.39°C for soil temperature) → the average is
      more robust than either alone.

      sm_dp change (EV08b→EV09 avg):
        Kasa:    EV08=0.172, EV08b=0.176 → avg=0.174
        Katiga:  EV08=0.139, EV08b=0.141 → avg=0.140
        Kapitu:  EV08=0.306, EV08b=0.265 → avg=0.285  (Kanem: 0.230→0.182→avg=0.206)

      sT_sh change (EV08b→EV09 avg):
        Kasa:    EV08=28.4, EV08b=28.0 → avg=28.2°C
        Kalima:  EV08=29.5, EV08b=30.0 → avg=29.8°C

    RETAINED from EV08b (GIDW): lapse-rate & hypsometric corrections in the
      blending engine (met_idw_blender.py), available via live blending.
      For climatological constants the Δz=−0.93 m correction is negligible
      (ΔT<0.006°C) but retained in code for methodological completeness.

    NEW in EV09: M6H_VPD_SIGMA — per-mangsa VPD interpolation uncertainty
      σ = max(model_spread=|EV08−EV08b|, SE_GIDW from 11-yr sample)
      Interpretation: 1-σ range = value ± σ (not 95% CI; multiply by 1.96).
      High-σ mangsa (epistemic uncertainty, not just sampling noise):
        Kalima(5): σ=0.239 kPa — large gradient disagreement M5 transition
        Kanem(6):  σ=0.185 kPa — same pre-monsoon gradient uncertainty
        Kapat(4):  σ=0.122 kPa — ENSO-sensitive transition
      Low-σ mangsa (both methods agree):
        Kawolu(8): σ=0.025 kPa — deep wet season, gradient flat
        Kasanga(9):σ=0.029 kPa — stable wet season

    METEO_MUSIM_6H hybrid (duration-weighted from EV09 mangsa):
      Katiga:   vpd 1.491 (EV08b:1.407, EV08:1.496)  sun 10.95
      Labuh:    vpd 1.038 (EV08b:1.201, EV08:1.042)  sun  9.59
      Rendheng: vpd 0.501 (EV08b:0.532, EV08:0.484)  sun  8.37
      Mareng:   vpd 0.909 (EV08b:0.859, EV08:0.902)  sun 10.19

6-HOURLY METEOROLOGICAL CALIBRATION FINDINGS (EV04 vs EV03)
-----------------------------------------------------------
  · R10 musim_start = {12, 131, 185, 305} from the Composite Wetness
    Index (6H-enhanced, R10 window 2015–2024). Robust-mean values from
    the 10-year sample:

        Katiga   : mean 12.5, median 6,   robust_mean 12  → 12
        Labuh    : mean 131.1, median 133, robust_mean 131 → 131
        Rendheng : mean 185.0, median 178, robust_mean 185 → 185
        Mareng   : mean 305.2, median 310, robust_mean 305 → 305

    10-year sample (2015–2024), σ ≈ 12–35 days, dominated by ENSO
    variability.

  · 6H cross-validation at final musim_start (median, window ±3 days,
    R10 2015–2024, IDW 2 stations):
        dopy  12 (Katiga)   → VPD 1.11 kPa · TCWV 38.8 kg/m²
                              · precip 0.06 mm/hr · cloud 49%
        dopy 131 (Labuh)    → VPD 1.21 kPa · TCWV 42.7 kg/m²
                              · precip 0.65 mm/hr · cloud 78%
        dopy 185 (Rendheng) → VPD 0.62 kPa · TCWV 51.8 kg/m²
                              · precip 8.29 mm/hr · cloud 92%
        dopy 305 (Mareng)   → VPD 0.70 kPa · TCWV 47.7 kg/m²
                              · precip 2.00 mm/hr · cloud 81%

    Note: VPD at dopy 12 (Katiga) is only 1.11 kPa because it is still
    early in the dry season; the true dry peak occurs at dopy 40–50
    (VPD ~1.40). Significant rainfall begins at dopy 135–140, so
    Labuh=131 marks the onset of the transition signal, not the start
    of heavy rain.

6-HOURLY METEOROLOGICAL CALIBRATION FINDINGS (EV05 → EV06)
----------------------------------------------------------
  · Recalibration of METEO_MANGSA_6H from ERA5/Land 1H (hourly) P1:
    Source: open-meteo-7_49S112_54E28m_hourly10yr.csv
    Period: 2015–2025 (11 years, 96,432 hours, 100% annual coverage)
    VPD method  : 24-hour mean (true diurnal average, not a 6H snapshot)
    sun_h method: sum(sunshine_duration_s)/3600 per day → mean per mangsa
    cloud method: 24-hour mean (total) and 12–18 WIB mean (cloud_aft)
    tcwv method : 24-hour mean

    Causes of changes vs EV05:
    1. VPD INCREASED (+0.05 to +0.25 kPa): EV05 used 6H snapshots
       (00, 06, 12, 18 local time) so nighttime (low VPD) received 50%
       weight. 24-h hourly is more balanced.
    2. sun_h DECREASED (−0.1 to −1.6 h): EV05 used 6H interpolation →
       overestimated during the wet season when sky conditions change
       rapidly. Hourly sum is more precise.
    3. cloud DECREASED (−1 to −8%): cloud_aft (12–18) is more
       representative than 6H snapshot at 12 alone, which can be
       biased by morning cloud.
    4. tcwv INCREASED (+0.5 to +3.7 kg/m²): 1H resolution is finer than
       4 points/day.

    VPD change per mangsa (EV05 → EV06):
        Kasa(1): 1.159→1.387 (+0.228)    Karo(2): 1.350→1.597 (+0.247)
        Katiga(3): 1.480→1.716 (+0.236)  Kapat(4): 1.436→1.621 (+0.185)
        Kalima(5): 1.009→1.208 (+0.199)  Kanem(6): 0.514→0.649 (+0.135)
        Kapitu(7): 0.405→0.455 (+0.050)  Kawolu(8): 0.397→0.451 (+0.054)
        Kasanga(9): 0.447→0.509 (+0.062) Kasadasa(10): 0.539→0.644 (+0.105)
        Desta(11): 0.734→0.953 (+0.219)  Sada(12): 0.902→1.041 (+0.139)

    sun_h change per mangsa (EV05 → EV06):
        Kasa(1): 11.3→10.9 (−0.4)   Karo(2): 11.4→11.0 (−0.4)
        Katiga(3): 11.3→11.0 (−0.3) Kapat(4): 11.0→10.9 (−0.1)
        Kalima(5): 10.4→10.1 (−0.3) Kanem(6): 9.3→8.6 (−0.7)
        Kapitu(7): 9.4→7.8 (−1.6)   Kawolu(8): 9.8→8.5 (−1.3)
        Kasanga(9): 10.2→9.1 (−1.1) Kasadasa(10): 10.4→9.6 (−0.8)
        Desta(11): 10.7→10.3 (−0.4) Sada(12): 11.0→10.3 (−0.7)
    → Largest correction in Rendheng (Kapitu/Kawolu): EV05 overestimated
      by up to 1.6 h/day due to high cloud variability not captured by
      6H sampling.

    METEO_MUSIM_6H change (EV05 → EV06):
        Katiga:   vpd 1.296→1.531 (+0.235), sun 11.3→10.9 (−0.4)
        Labuh:    vpd 0.900→1.062 (+0.162), sun 10.1→9.6  (−0.5)
        Rendheng: vpd 0.413→0.468 (+0.055), sun  9.7→8.4  (−1.3)
        Mareng:   vpd 0.758→0.877 (+0.119), sun 10.7→10.1 (−0.6)

6-HOURLY METEOROLOGICAL CALIBRATION FINDINGS (EV06 → EV06b)
-----------------------------------------------------------
  · Recalibration of IDW P1+P2 hourly (w1=0.3953, w2=0.6047):
    Source: P1 & P2 hourly 2015–2026 (~102,500 rows each)
    Overlap: 2015-01-01 → 2026-09-09 (102,480 rows)
    Distance P1–P2: 8.05 km; correlation r_vpd = 0.90–0.98

    New per-mangsa values (IDW P1+P2 vs P1-only):
        Kasa(1): 1.387→1.352 (−0.035)    Karo(2): 1.597→1.551 (−0.046)
        Katiga(3): 1.716→1.690 (−0.026)  Kapat(4): 1.621→1.601 (−0.020)
        Kalima(5): 1.208→1.181 (−0.027)  Kanem(6): 0.649→0.629 (−0.020)
        Kapitu(7): 0.455→0.467 (+0.012)  Kawolu(8): 0.451→0.468 (+0.017)
        Kasanga(9): 0.509→0.532 (+0.023) Kasadasa(10): 0.644→0.656 (+0.012)
        Desta(11): 0.953→0.949 (−0.004)  Sada(12): 1.041→1.021 (−0.020)

    → All VPD changes < 0.05 kPa (< 3%). Sign reverses in Rendheng:
      P2 (further south) is slightly drier than P1.

    METEO_MUSIM_6H change (EV06 → EV06b):
        Katiga:   vpd 1.531→1.496 (−0.035), tcwv 35.2→35.0
        Labuh:    vpd 1.062→1.042 (−0.020), tcwv 47.7→47.4
        Rendheng: vpd 0.468→0.484 (+0.016), tcwv 53.3→53.0, sun 8.4→8.3
        Mareng:   vpd 0.877→0.902 (+0.025), tcwv 46.2→45.4

    Benefits of IDW P1+P2:
      · SE VPD dry season (M1–M6) down 2–8% (better spatial
        representation)
      · SE VPD Rendheng (M7–M9) up 0.4–9.7% — reflects genuinely higher
        spatial rainfall variability, not degraded mean accuracy
      · Consistent with EV05 6H methodology which also used IDW

6-HOURLY METEOROLOGICAL CALIBRATION FINDINGS (EV04 → EV05)
----------------------------------------------------------
  · Recompute of METEO_MANGSA_6H sun_h & vpd:
    Method: IDW-merged daily from P1-hourly (2015–2026) + P2-6H
    (1995–2026). Mangsa boundaries based on R30 thresholds. Reference
    period: 1996–2025 (10,958 days). Data coverage: IDW 4,018 days
    (P1∩P2), P2-only 6,940 days, P1-only 0 days.
    → Archived; final values are the EV06 recalibration above.

6-HOURLY METEOROLOGICAL CALIBRATION FINDINGS (EV06b → EV07 GIDW)
-------------------------------------------------------------------
  · Full GIDW recalibration — variable-specific Gradient-Enhanced IDW:
    Source:  P1 & P2 hourly 2015–2026 (102,480 aligned rows, inner join)
    Period:  11 pranata years (22 Jun 2015 → 21 Jun 2026)
    Method:  W_final = α·W_linear + (1−α)·W_IDW(p_variogram, Q_terrain)
             α = exp(−d_perp / (decorr_km / 4))
    Geometry: d1=4.971 km  d2=4.027 km  d12=8.097 km
              along_frac=56.47%  d_perp=1.949 km
    Effective GIDW weights per variable (EV07):
      vapour_pressure_deficit        W1=0.4419  W2=0.5581  p=0.976  α=0.823
      total_column_water_vapour      W1=0.4374  W2=0.5626  p=1.033  α=0.907
      cloud_cover                    W1=0.4378  W2=0.5622  p=0.724  α=0.907
      sunshine_duration              W1=0.4344  W2=0.5656  p=1.356  α=0.856
      soil_moisture_0-7cm            W1=0.4495  W2=0.5505  p=1.454  α=0.677
      soil_moisture_28-100cm         W1=0.4507  W2=0.5493  p=0.618  α=0.771
      soil_temperature_0-7cm         W1=0.4403  W2=0.5597  p=1.996  α=0.677
      soil_temperature_100-255cm     W1=0.4412  W2=0.5588  p=1.049  α=0.823
    GIDW terrain shift vs EV06b: terrain-optimized (P1) gains +4.5–5.5%
    weight through: (a) quality factor Q_terrain>1 for surface variables,
    (b) gradient interpolation penalising the larger d1>d2 asymmetry,
    (c) variogram-estimated p<2 for most variables (spatially smoother
    than p=2 assumed in EV06b).

    VPD change per mangsa (EV06b IDW → EV07 GIDW):
        Kasa(1):    1.352→1.244 (−0.108)    Karo(2):    1.551→1.447 (−0.104)
        Katiga(3):  1.690→1.645 (−0.045)    Kapat(4):   1.601→1.646 (+0.045)
        Kalima(5):  1.181→1.408 (+0.227)    Kanem(6):   0.629→0.812 (+0.183)
        Kapitu(7):  0.467→0.563 (+0.096)    Kawolu(8):  0.468→0.478 (+0.010)
        Kasanga(9): 0.532→0.536 (+0.004)    Kasadasa(10):0.656→0.604 (−0.052)
        Desta(11):  0.949→0.856 (−0.093)    Sada(12):   1.021→1.010 (−0.011)
    Dry-season VPD (M1–M3) decreases 3–7%: terrain cell (P1) at
    −7.487°S is slightly further from P2 and gains more weight under GIDW;
    P1 at its actual location shows lower VPD during the dry season.
    Transition-to-wet VPD (M5–M6) increases 18–29%: stronger gradient
    between P1 and P2 during the pre-monsoon; GIDW captures this.

    METEO_MUSIM_6H change (EV06b → EV07 GIDW):
        Katiga:   vpd 1.496→1.407 (−0.089), sun 10.9→10.89 (−0.01)
        Labuh:    vpd 1.042→1.201 (+0.159), sun  9.6→9.96  (+0.36)
        Rendheng: vpd 0.484→0.532 (+0.048), sun  8.3→8.36  (+0.06)
        Mareng:   vpd 0.902→0.859 (−0.043), sun 10.1→10.07 (−0.03)

    Soil-moisture deep (sm_dp) correction:
      EV06b sm_dp values (0.291–0.404) were inconsistent with the raw
      soil_moisture_28_to_100cm data:
        S1 (terrain): overall mean 0.244 m³/m³, dry-season 0.216
        S2 (nearest): overall mean 0.204 m³/m³, dry-season 0.148
      EV07 GIDW sm_dp (0.133–0.319) is derived directly from the raw
      hourly data and is physically consistent with East Java's seasonal
      soil-moisture cycle (drying through Aug–Sep, rewetting Jan–Mar).

    Soil-temperature deep (sT_dp) — slight increase vs EV06b (+0.7–1.1°C)
      consistent with regional warming signal (2015–2026 period warmer
      than the EV06b calibration window).

    Lapse-rate elevation correction applied (Δz = target − source = −0.93 m):
      Soil temperatures: +0.006°C (dry-adiabatic ×0.93 m) — negligible
      but retained for methodological completeness.

IMPACT ON THE CALIBRATED CALENDAR
---------------------------------
  · Year anchor shift: −1 day (from 22 Jun → 21 Jun precision). For
    display consistency, ANCHOR_DAY remains 22 Jun, but ASTRO_CALIB
    stores the precise value.
  · R30 calibration (primary scenario) unchanged (meteorology-based).
  · ASTRO_CALIB table is available for precision reference and for
    placing astronomical markers in each scenario.
  · build_ciri() places astronomical markers dynamically according to
    the actual dopy range of each scenario.

CIRI PLACEMENT NOTES (EV03 correction, inherited by EV04)
---------------------------------------------------------
  · Dec solstice (dopy 182.7) → Mangsa-6 Kanem in all modern scenarios.
  · Zenith II & Orion Evening Culm (dopy ≈252.5) → Mangsa-8 Kawolu in
    R30/R10; Mangsa-9 Kasanga only in TRAD.
  · From EV03 onward, astronomical marker placement for calibrated
    scenarios is computed automatically by build_ciri() according to
    the actual dopy range.

LIMITATIONS AND UNCERTAINTY ANALYSIS
------------------------------------

  I. METEOROLOGICAL CALIBRATION LIMITATIONS

  I.1  Hourly data period span
       METEO_MANGSAs_6H recalibration uses ERA5/Land IFS-HRES 1-hour
       resolution data from TWO reference stations (P1 −7.487°S
       112.538°E and P2 −7.557°S 112.557°E, both 28 m elevation) over
       1995–2026 (31 pranata-tahun; ~277.800 timestep IDW-merged).
       The standard WMO climatological reference period is 30 years
       (1991–2020 or 1996–2025); the current span meets and slightly
       exceeds this requirement. The 31-year period resolves the
       degrees-of-freedom limitation that affected the previous
       11-year calibration (EV09 v2.0.0).

  I.2  Warm-period bias
       Comparative analysis against daily P1 1996–2025 (R30) shows
       that 2015–2025 is systematically warmer (+0.6–1.1°C in maximum
       air temperature) and drier (relative humidity 1.8–5.1% lower)
       than the R30 mean as a whole. This difference reflects a
       regional climate-warming signal, not a sampling artifact.

       The 11-year (2015–2025) calibration inherent in EV09 v2.0.0
       inherited this warm-period bias. The 31-year recalibration
       (EV09-HIST30) partially corrects it by averaging over the
       pre-warming baseline (1995–2014) and the recent decade
       (2015–2026). Residual bias is estimated at less than 0.05 kPa
       in most mangsa; the largest corrections are observed in
       Kasa (−0.130 kPa), Karo (−0.150 kPa), and Desta (−0.190 kPa).

  I.3  Spatial representation
       EV09 uses HYBRID calibration — EV08 for volatile fields, avg(EV08,EV08b)
       for stable consensus fields.  VPD M5/M6 carry σ>0.15 kPa epistemic
       uncertainty; field verification at MJS Obs. recommended.
       W1 (terrain_optimized) ≈ 0.434–0.451, W2 (nearest) ≈ 0.549–0.566.
       This improves on EV06b (flat IDW w1=0.3953, w2=0.6047) by:
         • Using Haversine-based 3-D distance (vs. Euclidean degree-space)
         • Estimating IDW power p from the empirical variogram per variable
           (p=0.62–2.00 vs. fixed p=2 in EV06b)
         • Applying terrain-quality factors Q_terrain (1.05–1.25) from
           physical knowledge of which cell selection method is more
           representative for each variable type
         • Blending linear-gradient and IDW interpolation via α factor
           (α=0.677–0.907) derived from target's off-axis distance (1.95 km)
           and the variable's decorrelation length
       Inter-station correlation r_vpd = 0.90–0.98 (unchanged from EV06b).

  I.4  musim_start calibration and mangsa boundaries
       Season boundaries (musim_start) and mangsa grouping remain
       from EV04–EV05 (based on the Composite Wetness Index, 6H data
       2015–2024). musim_start uncertainty: ±12–35 days, dominated by
       interannual ENSO variability. An alternative K-means method
       using 5 features produced boundaries differing by up to 9
       days for Labuh; the composite was chosen because it is more
       robust to ENSO outliers.

  II. METEO_MANGSA_6H UNCERTAINTY ANALYSIS (EV06b)

  Four uncertainty components are identified and quantified:

  II.A  Type A uncertainty — Estimation precision (interannual SE)
        Computed as SE = σ/√n, with σ = standard deviation of annual
        values and n = 11 years. 95% confidence interval = ±2·SE.

        This component is REDUCED 2.4× compared to EV05 (P1-only 6H
        snapshot), and slightly better than EV06 (P1-only hourly) in
        the dry season.

        95% CI of VPD, per mangsa (EV07 GIDW P1+P2, 2015–2025, 11 yr):
          Kasa:    1.244 ± 0.168 kPa    Kapat:    1.646 ± 0.244 kPa
          Karo:    1.447 ± 0.146 kPa    Kalima:   1.408 ± 0.301 kPa
          Katiga:  1.645 ± 0.144 kPa    Kanem:    0.812 ± 0.198 kPa
          Kapitu:  0.563 ± 0.055 kPa    Kawolu:   0.478 ± 0.051 kPa
          Kasanga: 0.536 ± 0.059 kPa    Kasadasa: 0.604 ± 0.087 kPa
          Desta:   0.856 ± 0.129 kPa    Sada:     1.010 ± 0.158 kPa
        (EV06b IDW reference: Kasa 1.352±0.168, Katiga 1.690±0.160,
         Kapitu 0.467±0.045, Kasadasa 0.656±0.092)
         
        95% CI of VPD, per mangsa (EV09-HIST30 hybrid, 1995–2026, 31 yr):
          Kasa:    1.215 ± 0.101 kPa    Kapat:    1.509 ± 0.122 kPa
          Karo:    1.392 ± 0.095 kPa    Kalima:   1.046 ± 0.239 kPa
          Katiga:  1.570 ± 0.072 kPa    Kanem:    0.535 ± 0.185 kPa
          Kapitu:  0.421 ± 0.083 kPa    Kawolu:   0.404 ± 0.025 kPa
          Kasanga: 0.476 ± 0.029 kPa    Kasadasa: 0.584 ± 0.072 kPa
          Desta:   0.759 ± 0.093 kPa    Sada:     0.928 ± 0.079 kPa
        (σ dari M6H_VPD_SIGMA = max model-spread, SE_GIDW_31yr;
         interpretasi 1-σ, bukan 95% CI — kalikan 1.96 untuk CI)         

        95% CI of sun_h, per mangsa (EV07 GIDW P1+P2):
          Kasa:    10.78 h    Kapat:  11.00 h    Kapitu:   8.17 h
          Karo:    10.95 h    Kalima: 10.83 h    Kawolu:   8.19 h
          Katiga:  11.01 h    Kanem:   8.81 h    Kasanga:  8.85 h
          Kasadasa: 9.42 h    Desta:  10.19 h    Sada:    10.38 h

  II.B  Type B uncertainty — Period representation bias
        The 2015–2025 period is not fully representative of the R30
        climatological norm (1996–2025). Identified biases:
          · Air temperature maximum: +0.56 to +1.14°C (Kapitu to Kalima)
          · Relative humidity:       −1.8 to −5.1% (Kasanga to Karo)
        Estimated VPD correction if returned to the R30 baseline:
        −0.03 to −0.24 kPa. Correction is NOT applied because EV06b
        values are considered more representative of current climate
        conditions and short-term projections.

  II.C  Type C uncertainty — Temporal non-stationarity
        Linear regression of VPD against time (2015–2025) shows
        statistically significant trends in the following three
        mangsa:

          Kapitu (7):    +0.016 kPa/year  (p = 0.014, significant α=0.05)
          Kasanga (9):   +0.013 kPa/year  (p = 0.070, marginal α=0.10)
          Kasadasa (10): +0.024 kPa/year  (p = 0.097, marginal α=0.10)

        The presence of these trends indicates that the single mean
        value listed in METEO_MANGSA_6H for those three mangsa is
        non-stationary — the actual VPD at the end of the calibration
        period (2023–2025) is higher than the listed value. The
        confidence interval for these three mangsa should be widened
        by ≈20% to accommodate trend-induced uncertainty. For sun_h
        no significant trend was found in any mangsa (all p > 0.11),
        so sun_h values are treated as stationary.

        Physical interpretation: the VPD trend in Kapitu–Kasadasa
        (January–April) reflects Rendheng–Mareng warming consistent
        with regional East Java climate-warming projections.

  II.D  Diurnal sampling bias (EV05, fully eliminated from EV06)
        EV05 used 6H snapshots (00, 06, 12, 18 UTC+7) to estimate
        daily VPD and sun_h. Analysis against 1H data shows
        systematic biases:
          · VPD: underestimate −2.5 to −5.8% (nighttime hours
            received >50% weight)
          · sun_h: overestimate up to +4.66 h/day in Karo and Kasa
                   (sunshine_duration snapshot at noon multiplied ×6;
                    overestimation of clear periods between two
                    measurement points)
        Both biases are systematic and unidirectional across all
        mangsa. Since EV06, these biases are fully eliminated through
        the use of 1H data.

  III. ASTRONOMICAL CALIBRATION LIMITATIONS
       · Calibration covers 2020–2029; precision degrades outside
         this range due to accumulated ΔT uncertainty.
       · Orion Midnight Culmination (8 Dec): refers to midnight
         transit at 00:00 WIB. The tradition refers to dusk
         culmination (1 Mar) — a definitional difference, not
         precession.
       · Orion Acronychal Set (18 Jun, dopy=361.9) differs by 15 days
         from tradition (4 Jun, dopy=347) because tradition uses the
         dawn heliacal set definition. Precession over 170 years
         (1855→2025) contributes ≈2° (~±3 days).

  IV. IOD MODULE LIMITATIONS
      · IOD_DELTA was calibrated from 8 pIOD years (1961–2019, incl.
        pre-1979) and 7 nIOD years (1960–2024). These sample sizes
        are below the recommended minimum (n ≥ 10) for stable
        composite estimation.
      · IOD–ENSO co-occurrence ~60–67%: ENSO filtering was applied
        (|ASO Niño3.4| ≥ 0.50), but the non-linear IOD–ENSO
        interaction is not fully isolated.
      · IOD application weights (0.30 standalone, 0.50 ENSO–IOD
        synergy) are derived from the literature (Hendon et al. 2012;
        Abram et al. 2008), not empirically optimised from local data
        due to sample-size limitations.
      · The active IOD window is restricted to mangsa 3–5 (SON,
        September–November); lagged IOD effects on Kanem–Kapitu have
        not been modelled.
"""

from __future__ import annotations

# ── Section 0 · Standard library ──────────────────────────────────────────
import argparse
import os
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:                                    # pragma: no cover
    HAS_PANDAS = False

try:
    from scipy.stats import multivariate_normal as _mvn  # noqa: F401
    HAS_SCIPY = True
except ImportError:                                    # pragma: no cover
    HAS_SCIPY = False


# ══════════════════════════════════════════════════════════════════════════
# Section 1 · Presentation constants
# ══════════════════════════════════════════════════════════════════════════

W: int = 70                          # fixed frame width (columns)
IND: str = "  "

MONTH_SHORT: Dict[int, str] = {
    1: "Jan",  2: "Feb",  3: "Mar",  4: "Apr",  5: "Mei",  6: "Jun",
    7: "Jul",  8: "Agu",  9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
}
MONTH_FULL: Dict[int, str] = {
    1: "Januari",  2: "Februari", 3: "Maret",    4: "April",
    5: "Mei",      6: "Juni",     7: "Juli",      8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}


# ══════════════════════════════════════════════════════════════════════════
# Section 2 · Geometry & location constants
# ══════════════════════════════════════════════════════════════════════════

TARGET_LAT: float = -7.521951
TARGET_LON: float = 112.566089
STATION_P1: Tuple[float, float] = (-7.486819, 112.538210)
STATION_P2: Tuple[float, float] = (-7.5571175, 112.557350)
IDW_POWER: float = 2.0

# EV09 interpolation weights per field strategy:
# VPD/volatile fields → EV08 adaptive IDW weights
_IDW_W1_VPD: float  = 0.4154    # terrain_optimized (P1), humidity class
_IDW_W2_VPD: float  = 0.5846    # nearest (P2)
# Soil moisture → EV08 adaptive IDW weights (Q_terrain=1.35)
_IDW_W1_SOIL: float = 0.4996    # terrain_optimized (P1), soil_moisture class
_IDW_W2_SOIL: float = 0.5004    # nearest (P2)
# GIDW effective weights for live blending (from met_idw_blender.py)
_GIDW_W1: float     = 0.4417    # mean across variables
_GIDW_W2: float     = 0.5583    # nearest (P2)

ANCHOR_MONTH: int = 6
ANCHOR_DAY: int = 22          # traditional; precision anchor is 21 Jun

DEFAULT_DAILY_CSV_P1   = "open-meteo-7.49S112.54E28m.csv"
DEFAULT_DAILY_CSV_P2   = "open-meteo-7.56S112.56E28m.csv"
DEFAULT_6H_CSV_P1      = "open-meteo-7.49S112.54E28m_6hour10yr.csv"
DEFAULT_6H_CSV_P2      = "open-meteo-7.56S112.56E28m_6hour10yr.csv"
DEFAULT_HOURLY_CSV_P1  = "open-meteo-7.49S112.54E28m_hourly10yr.csv"
DEFAULT_HOURLY_CSV_P2  = "open-meteo-7.56S112.56E28m_hourly10yr.csv"
DEFAULT_ENSO_CSV       = "Sst_nino34_index.csv"
DEFAULT_MSLA_CSV       = "Msla_nino34_index.csv"
DEFAULT_IOD_MONTHLY    = "30yr_dmi_3rmean.txt"
DEFAULT_IOD_WEEKLY     = "iod_1.txt"


# ══════════════════════════════════════════════════════════════════════════
# Section 3 · Data attribution registry
# ══════════════════════════════════════════════════════════════════════════
#
# Full bibliographic metadata for every upstream product referenced by the
# model. Consumed by :func:`print_data_attribution`. Do not embed citations
# elsewhere; the registry is the single source of truth.

DATA_ATTRIBUTION: Dict[str, Dict[str, Optional[str]]] = {
    "era5": {
        "nama": "ERA5",
        "deskripsi": "Global reanalysis, 0.25° (~31 km), 1940–present",
        "institusi": "ECMWF / Copernicus Climate Change Service (C3S)",
        "sitasi": ("Hersbach, H., et al. (2020). The ERA5 global reanalysis. "
                   "Quarterly Journal of the Royal Meteorological Society, "
                   "146(730), 1999–2049."),
        "doi": "10.1002/qj.3803",
        "lisensi": "Copernicus Licence — CC-BY 4.0",
    },
    "era5_land": {
        "nama": "ERA5-Land",
        "deskripsi": "Land-surface reanalysis, 0.1° (~9 km), 1950–present",
        "institusi": "ECMWF / Copernicus Climate Change Service (C3S)",
        "sitasi": ("Muñoz-Sabater, J., et al. (2021). ERA5-Land: a "
                   "state-of-the-art global reanalysis dataset for land "
                   "applications. Earth System Science Data, 13(9), 4349–4383."),
        "doi": "10.5194/essd-13-4349-2021",
        "lisensi": "Copernicus Licence — CC-BY 4.0",
    },
    "ecmwf_ifs": {
        "nama": "ECMWF IFS (HRES)",
        "deskripsi": "Global NWP model, 9 km resolution, 2017–present",
        "institusi": "European Centre for Medium-Range Weather Forecasts (ECMWF)",
        "sitasi": "ECMWF. (2024). IFS Documentation CY49r1. ECMWF Technical Report.",
        "doi": None,
        "lisensi": "CC-BY 4.0",
        "catatan": ("Collected by Open-Meteo from IFS 0z/6z/12z/18z runs "
                    "since 2017."),
    },
    "open_meteo": {
        "nama": "Open-Meteo",
        "deskripsi": "Open meteorological data aggregation API",
        "institusi": "Open-Meteo (open-source, non-commercial)",
        "sitasi": "Zippenfenig, P. (2023). Open-Meteo.com Weather API.",
        "doi": "10.5281/ZENODO.7970649",
        "lisensi": "CC-BY 4.0 (attribution required)",
    },
    "aviso_duacs_sla": {
        "nama": "DUACS SLA Niño3.4 Index",
        "deskripsi": ("Filtered SLA index (annual, semi-annual and 60-day "
                      "components removed; 85-day rolling window; Niño3.4 "
                      "region 5°S–5°N, 190°E–240°E; weekly)."),
        "institusi": "CNES / CLS — AVISO+ / DUACS",
        "sitasi": ("AVISO/DUACS. (2025). El Niño Southern Oscillation Ocean "
                   "Indicator product (vDT2024) [Data set]. CNES."),
        "doi": "10.24400/527896/A01-2025.008",
        "input": ("Global Sea Level Anomalies 'all-satellite' daily "
                  "DUACS2024 DT and NRT from Copernicus Marine Service."),
        "referensi": "https://www.aviso.altimetry.fr/en/data/products/indicators/enso.html",
        "lisensi": "Copernicus Marine Licence",
    },
    "noaa_oisst_sst": {
        "nama": "NOAA OISST v2.1 SST Niño3.4 Index",
        "deskripsi": ("Filtered SST index (annual, semi-annual and trend "
                      "removed; 85-day rolling window; Niño3.4 region)."),
        "institusi": "NOAA NCEI / AVISO+ (ENSO Ocean Indicator product)",
        "sitasi": ("Huang, B., et al. (2021). Improvements of the Daily "
                   "Optimum Interpolation Sea Surface Temperature (DOISST) "
                   "Version 2.1. Journal of Climate, 34, 2923–2939."),
        "doi": "10.1175/JCLI-D-20-0166.1",
        "input": "NOAA 1/4° Daily Gridded OISST V2.1",
        "lisensi": "NOAA Open Data",
    },
    "jma_iod": {
        "nama": "JMA Dipole Mode Index (DMI)",
        "deskripsi": ("DMI = SST anomaly WIN (50–70°E, 10°S–10°N) − EIN "
                      "(90–110°E, 10°S–Eq). Threshold ±0.40 °C, 3-month "
                      "running mean, Jun–Nov."),
        "institusi": "Japan Meteorological Agency (JMA)",
        "sitasi": ("Saji, N. H., Goswami, B. N., Vinayachandran, P. N., & "
                   "Yamagata, T. (1999). A dipole mode in the tropical Indian "
                   "Ocean. Nature, 401, 360–363."),
        "doi": "10.1038/43854",
        "input": ("MGDSST (Kurihara et al. 2006) after Jun 2015; COBE-SST2 "
                  "(Hirahara et al. 2014) before May 2015."),
        "referensi": "https://ds.data.jma.go.jp/tcc/tcc/products/elnino/iodevents.html",
        "lisensi": "JMA Open Data",
    },
    "bom_iod": {
        "nama": "Bureau of Meteorology IOD Index",
        "deskripsi": ("IOD index from SST anomalies (ERSSTv5, HadISST), "
                      "threshold ±0.40 °C, 3 consecutive weeks."),
        "institusi": "Australian Bureau of Meteorology (BoM)",
        "sitasi": "Australian Bureau of Meteorology. (2025). Indian Ocean Dipole monitoring.",
        "doi": None,
        "referensi": "http://www.bom.gov.au/climate/iod/",
        "lisensi": "CC-BY 4.0 (BoM Open Data)",
    },
    "vsop87d": {
        "nama": "VSOP87D (Planetary Solution)",
        "deskripsi": ("Analytic planetary theory, version D: heliocentric "
                      "spherical variables, ecliptic of date. Position "
                      "accuracy ~1″ for 1800–2200."),
        "institusi": "IMCCE — Observatoire de Paris / Bureau des Longitudes",
        "sitasi": ("Bretagnon, P., & Francou, G. (1988). Planetary theories "
                   "in rectangular and spherical variables: VSOP87 solution. "
                   "Astronomy & Astrophysics, 202, 309–315."),
        "doi": None,
        "catatan": ("Version D chosen because it uses ecliptic of date — "
                    "appropriate for epoch-specific ephemerides."),
        "referensi": "https://cdsarc.cds.unistra.fr/viz-bin/cat/VI/81",
        "lisensi": "IMCCE Open Data",
    },
    "iers2010": {
        "nama": "IERS Conventions 2010",
        "deskripsi": ("IAU 2006/2000A precession-nutation: P03 precession "
                      "(Capitaine et al. 2003), IAU 2000A nutation "
                      "(Mathews et al. 2002), frame bias, dX/dY corrections."),
        "institusi": "International Earth Rotation and Reference Systems Service",
        "sitasi": ("Petit, G., & Luzum, B. (eds.). (2010). IERS Conventions "
                   "(2010). IERS Technical Note No. 36."),
        "doi": None,
        "referensi": "https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html",
        "lisensi": "IERS Open Access",
    },
    "iau2006_precession": {
        "nama": "IAU 2006 Precession (P03)",
        "deskripsi": "P03 precession model adopted by IAU 2006 Resolution.",
        "institusi": "IAU Working Group on Precession and the Ecliptic",
        "sitasi": ("Wallace, P. T., & Capitaine, N. (2006). Precession-"
                   "nutation procedures consistent with IAU 2006 resolutions. "
                   "Astronomy & Astrophysics, 459(3), 981–985."),
        "doi": "10.1051/0004-6361:20065897",
        "referensi": "https://www.aanda.org/articles/aa/abs/2006/45/aa5897-06/aa5897-06.html",
        "lisensi": "CC-BY 4.0 (A&A Open Access)",
    },
    "hmnao_deltat": {
        "nama": "HMNAO ΔT Polynomials",
        "deskripsi": ("ΔT (TT − UT1) table and polynomials for −720 to 2019, "
                      "with extrapolation to 2100."),
        "institusi": "HM Nautical Almanac Office (HMNAO), UK Hydrographic Office",
        "sitasi": ("HM Nautical Almanac Office. (2020). Polynomial "
                   "Coefficients for ΔT and Length of Day (LOD) for Years "
                   "−720 to 2019: Version 2020."),
        "doi": None,
        "referensi": "http://astro.ukho.gov.uk/nao/lvm/",
        "lisensi": "HMNAO Open Data",
    },
    "sofa": {
        "nama": "SOFA (Standards of Fundamental Astronomy)",
        "deskripsi": ("IAU reference library for precession, nutation, "
                      "Earth rotation, time scales and reference systems."),
        "institusi": "IAU SOFA Center — Rutherford Appleton Laboratory",
        "sitasi": ("Hohenkerk, C. Y. (2011). Standards of Fundamental "
                   "Astronomy. Scholarpedia, 6(1), 11404."),
        "doi": "10.4249/scholarpedia.11404",
        "referensi": "https://www.iausofa.org/",
        "lisensi": "SOFA Licence (non-commercial)",
    },
}


# ══════════════════════════════════════════════════════════════════════════
# Section 4 · Traditional Pranata Mangsa dataset
# ══════════════════════════════════════════════════════════════════════════
#
# Fixed mangsa durations as formalised by Paku Buwana VII (1855). Leap-year
# adjustment applies only to Mangsa 8 (Kawolu), by +1 day.

@dataclass(frozen=True)
class MangsaSpec:
    """Immutable specification of one traditional mangsa."""
    no: int
    nama: str
    start_month: int
    start_day: int
    duration: int


MANGSAS: Tuple[MangsaSpec, ...] = (
    MangsaSpec( 1, "Kasa",     6, 22, 41),
    MangsaSpec( 2, "Karo",     8,  2, 23),
    MangsaSpec( 3, "Katiga",   8, 25, 24),
    MangsaSpec( 4, "Kapat",    9, 18, 25),
    MangsaSpec( 5, "Kalima",  10, 13, 27),
    MangsaSpec( 6, "Kanem",   11,  9, 43),
    MangsaSpec( 7, "Kapitu",  12, 22, 43),
    MangsaSpec( 8, "Kawolu",   2,  3, 26),
    MangsaSpec( 9, "Kasanga",  3,  1, 25),
    MangsaSpec(10, "Kasadasa", 3, 26, 24),
    MangsaSpec(11, "Desta",    4, 19, 23),
    MangsaSpec(12, "Sada",     5, 12, 41),
)

# Wet-season grouping (Katiga, Labuh, Rendheng, Mareng).
MUSIM_MEMBERS: Dict[str, Tuple[int, ...]] = {
    "Katiga":   (1, 2, 3),
    "Labuh":    (4, 5, 6),
    "Rendheng": (7, 8, 9),
    "Mareng":  (10, 11, 12),
}
MUSIM_DESKRIPSI: Dict[str, str] = {
    "Katiga":   "Kemarau Puncak",
    "Labuh":    "Peralihan → Hujan",
    "Rendheng": "Musim Hujan Puncak",
    "Mareng":   "Peralihan → Kemarau",
}
MUSIM_ORDER: Tuple[str, ...] = ("Katiga", "Labuh", "Rendheng", "Mareng")

# Traditional (Indonesian) phenological descriptions.
CIRI_TRADISIONAL: Dict[int, str] = {
    1: ("Solstis Juni 21 Jun (λ☉=90°, dopy≈−0.8). Weluku/Orion terbit fajar "
        "~25 Jun (dopy≈3.1, 3 hr setelah solstis). Awal tahun pertanian; "
        "membersihkan lahan, tanah kering maksimum."),
    2: "Pohon randu/kapuk mulai berdaun. Tanah retak. Pengolahan lahan kering.",
    3: "Puncak kemarau, sumur mengering. Panen palawija (jagung, kacang).",
    4: ("Burung gelatik di sawah, manyar membuat sarang. Angin mulai berubah "
        "ke barat. Ekuinoks September (23 Sep, dopy≈92.9) jatuh di akhir Kapat."),
    5: ("Zenith Matahari I: 12 Okt (δ☉=−7.52°, dopy≈112.4, 1 hr lebih awal "
        "dari tradisional). Awal hujan. Pleiades terlihat di senja. Embun beracun."),
    6: ("Weluku/Orion Acronychal Rise (pertama terlihat di senja): ~5 Des "
        "(dopy≈166.2). Kulminasi tengah malam Orion: ~8 Des (dopy≈168.9). "
        "Hujan lebat. Menabur benih padi. "
        "Solstis Desember 21 Des (dopy≈182.7) juga jatuh di Kanem, "
        "bukan di Kapitu — karena batas musim R30/R10 menempatkan Kapitu "
        "baru mulai setelah dopy≈196–208."),
    7: ("Solstis Desember (21 Des, dopy≈182.7) secara astronomis berada di "
        "Mangsa-6 Kanem, bukan Kapitu. Tradisi menaruh Solstis di Kapitu "
        "karena batas lama (22 Des). Pleiades setinggi pecat sawad (~50°). "
        "Memindah bibit padi ke sawah."),
    8: ("Transplantasi selesai. Pleiades kulminasi di senja. Padi tumbuh. "
        "Zenith Matahari II (1 Mar, dopy≈252.5) dan Orion Kulminasi "
        "Senja (~1 Mar) jatuh di Kawolu untuk skenario R30/R10."),
    9: ("Zenith Matahari II (dopy≈252.5) & Orion Evening Heliacal "
        "Culmination (~26 Feb–1 Mar) secara astronomis berada di Mangsa-8 "
        "Kawolu untuk R30/R10; hanya pada skenario TRAD jatuh di Kasanga. "
        "Ekuinoks Maret 20 Mar (dopy≈271.8) di akhir Kasanga (R30). "
        "Jangkrik berbunyi. Padi berbulir."),
    10: "Hujan reda, angin timur. Panen raya mulai.",
    11: ("Orion terbalik di barat (terbenam awal). Kapuk mekar. "
         "Hutang dilunasi."),
    12: ("Orion terakhir terlihat senja: ~18 Jun (dopy≈361.9, acronychal "
         "set). Perkiraan tradisional 4 Jun (heliacal set fajar, dopy≈347) "
         "berbeda definisi (+15 hr). Panen selesai. Masa bera (Apit Lemah)."),
}

# Javanese candra (poetic verse) — preserved verbatim.
CIRI_JAWA: Dict[int, str] = {
    1: ("Sotya murca ing êmbanan, punika candranipun măngsa kasa = I "
        "mangsanipun gêgodhongan sami gogrog, kêkajêngan sami paruthul, "
        "têgêsipun: sotya murca ing êmbanan = sêsotya coplok saking ing "
        "êmbanan, gêgodhongan kaupamèkakên: sêsotya, uwit kaupamèkakên: "
        "êmbananipun."),
    2: ("Bantala rêngka, candranipun măngsa kalih = II têgêsipun: bantala "
        "rêngka = siti bênthèt, bantala = siti, rêngka = bênthèt, punika "
        "mangsanipun siti nêla."),
    3: ("Suta manut ing bapa, candranipun măngsa katiga = III têgêsipun: "
        "anak manut ing bapa, punika mangsanipun lung-lungan nurut lanjaran."),
    4: ("Waspa kumêmbêng jroning kalbu, candranipun măngsa sakawan = IV, "
        "têgêsipun: êluh kumêmbêng salêbêting manah, punika mangsanipun "
        "sumbêr pêpêt (= pêpêt sumbêr) êluh kadamêl upami: toya, manah: "
        "kadamêl upami: sumbêr."),
    5: ("Pancuran êmas sumawur ing jagad, candranipun măngsa gangsal = V, "
        "pancuran: kadamêl upami: jawah, sumawur: dhawahipun ing jawah."),
    6: ("Rasa mulya kasucian, candranipun măngsa kanêm = VI, mangsanipun "
        "wowohan nêdhêng."),
    7: ("Wisa kentar ing maruta, candranipun măngsa kapitu = VII, têgêsipun: "
        "wisa larut dening angin, punika mangsanipun kathah sêsakit."),
    8: ("Anjrah jroning kayun, candranipun măngsa kawolu = VIII, punika "
        "mangsanipun kucing gandhik."),
    9: ("Wêdharing wacana mulya, candranipun măngsa kasanga = IX, têgêsipun "
        "wêdaling wicantên linakung, punika mangsanipun gangsir sami "
        "ngênthir, garèng sami ngêrèng."),
    10: ("Gêdhong minêb jroning kalbu, candranipun măngsa sadasa = X, "
         "punika mangsanipun sato kewan sami mêtêng."),
    11: ("Sotya sinarawèdi, candranipun măngsa dhêstha = XI, punika "
         "mangsanipun pêksi sami ngloloh, têgêsipun: sêsotya, kadamêl "
         "upami: anaking pêksi, sinarawèdi = pinulasara, punika "
         "ngibaratipun dipun loloh."),
    12: ("Tirta sah saking sasana, candranipun măngsa sadha = XII, "
         "têgêsipun: toya pisah saking panggenan, punika măngsa badhidhing, "
         "tirta punika ngibarat kringêt, sasana ngibarat badan, dados "
         "awis-awis tiyang kringêtên, amargi saking asrêpipun."),
}

# Short ecological cues used by the scenario builder.
CIRI_BASE: Dict[int, str] = {
    1:  "Awal tahun pertanian; membersihkan lahan, tanah mengering.",
    2:  "Pohon randu/kapuk mulai merekah. Tanah retak.",
    3:  "Puncak kemarau, sumur mengering. Panen palawija.",
    4:  "Burung gelatik di sawah, manyar membuat sarang. Angin ke barat.",
    5:  "Awal hujan. Pleiades terlihat di senja. Embun beracun.",
    6:  "Hujan lebat. Menabur benih padi.",
    7:  "Pleiades setinggi pecat sawad (~50°). Memindah bibit padi.",
    8:  "Transplantasi selesai. Pleiades kulminasi di senja.",
    9:  "Jangkrik berbunyi. Padi berbulir.",
    10: "Hujan reda, angin timur. Panen raya mulai.",
    11: "Orion terbalik di barat. Kapuk mekar. Hutang dilunasi.",
    12: "Panen selesai. Masa bera (Apit Lemah).",
}


def is_leap_year(year: int) -> bool:
    """Return True for Gregorian leap years."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


@lru_cache(maxsize=1)
def _orig_dopy_table() -> Dict[int, int]:
    """Cumulative day-of-pranata-year offset per traditional mangsa."""
    table, cum = {}, 0
    for spec in MANGSAS:
        table[spec.no] = cum
        cum += spec.duration
    return table


ORIG_DOPY: Dict[int, int] = _orig_dopy_table()
ORIG_MUSIM_START: Dict[str, int] = {
    mu: ORIG_DOPY[members[0]] for mu, members in MUSIM_MEMBERS.items()
}
ORIG_MUSIM_START_NEXT: Dict[str, int] = {
    "Katiga":   ORIG_MUSIM_START["Labuh"],
    "Labuh":    ORIG_MUSIM_START["Rendheng"],
    "Rendheng": ORIG_MUSIM_START["Mareng"],
    "Mareng":   365 + ORIG_MUSIM_START["Katiga"],
}


# ══════════════════════════════════════════════════════════════════════════
# Section 5 · Astronomical calibration
# ══════════════════════════════════════════════════════════════════════════
#
# Mean dopy and dispersion (2020–2029) for each reference event, computed
# with JRC_Ephemeris v5.0 (VSOP87D + IERS 2010 + HMNAO ΔT) at
# (−7.521951°S, 112.566089°E, 28 m). The `trad_dopy` field is the
# traditional Pranata Mangsa dopy for the *equivalent* event. Where the
# traditional reference is a different event definition (e.g. heliacal
# set vs acronychal set), the flag `same_event=False` is set.

@dataclass(frozen=True)
class AstroEvent:
    key: str
    label: str
    mean_dopy: float
    std_dopy: float
    mean_month: int
    mean_day: int
    trad_dopy: int
    delta: float
    same_event: bool = True
    catatan: str = ""


ASTRO_CALIB: Dict[str, AstroEvent] = {
    "solstis_juni": AstroEvent(
        "solstis_juni", "Solstis Juni (λ☉=90°)",
        -0.81, 0.27, 6, 21, 0, -0.81,
        catatan=("Solstis Juni 21 Jun ~11:00 WIB. Jangkar tradisional 22 Jun "
                 "terlambat ~20 jam."),
    ),
    "solstis_des": AstroEvent(
        "solstis_des", "Solstis Desember (λ☉=270°)",
        182.71, 0.28, 12, 21, 184, -1.29,
        catatan=("Secara astronomis jatuh di Mangsa-6 Kanem untuk semua "
                 "skenario modern, bukan Kapitu seperti tradisi."),
    ),
    "equinox_maret": AstroEvent(
        "equinox_maret", "Ekuinoks Maret (λ☉=0°)",
        271.75, 0.30, 3, 20, 273, -1.25,
        catatan="Ekuinoks Maret 20 Mar ~11:00 WIB. Bukan penanda tradisional.",
    ),
    "equinox_sept": AstroEvent(
        "equinox_sept", "Ekuinoks September (λ☉=180°)",
        92.85, 0.27, 9, 23, 92, +0.85,
        catatan=("Ekuinoks September 23 Sep ~07:00 WIB. Jatuh di Mangsa-4 "
                 "Kapat pada skenario TRAD/R30."),
    ),
    "zenith_I_okt": AstroEvent(
        "zenith_I_okt", "Zenith Matahari I (δ☉=−7.52°)",
        112.37, 0.27, 10, 12, 113, -0.63,
        catatan=("Zenith I 12 Okt ~09:00 WIB, 0.6 hr lebih awal dari "
                 "tradisional 13 Okt. Penanda awal Kalima."),
    ),
    "zenith_II_mar": AstroEvent(
        "zenith_II_mar", "Zenith Matahari II (δ☉=−7.52°)",
        252.46, 0.27, 3, 1, 253, -0.54,
        catatan=("Zenith II 1 Mar ~10:00 WIB. Jatuh di Mangsa-8 Kawolu untuk "
                 "R30/R10, bukan Kasanga seperti tradisi."),
    ),
    "orion_helrise": AstroEvent(
        "orion_helrise", "Orion Heliacal Rise (terbit fajar)",
        3.11, 0.40, 6, 25, 0, +3.11,
        catatan="Orion heliacal rise 25 Jun — 3 hr setelah solstis.",
    ),
    "orion_evening_rise": AstroEvent(
        "orion_evening_rise", "Orion Acronychal Rise (terbit senja)",
        166.16, 0.46, 12, 5, 167, -0.84,
        catatan="Orion acronychal rise 5 Des (~18:30 WIB). Konsisten +−1 hr.",
    ),
    "orion_evening_culm": AstroEvent(
        "orion_evening_culm", "Orion Kulminasi Senja",
        252.50, 0.40, 3, 1, 253, -0.50,
        catatan=("Ammarell (1991) Tbl.3: epoch 1850 = 26 Feb, kini ≈1 Mar. "
                 "Jatuh di Mangsa-8 Kawolu untuk R30/R10."),
    ),
    "orion_midnight_culm": AstroEvent(
        "orion_midnight_culm", "Orion Kulminasi Tengah Malam",
        168.91, 0.40, 12, 8, 252, -83.09, same_event=False,
        catatan=("Kulminasi tengah malam ~8 Des (00:00 WIB). Berbeda dari "
                 "evening heliacal culmination (1 Mar) — perbedaan definisi, "
                 "bukan presesi."),
    ),
    "orion_acron_set": AstroEvent(
        "orion_acron_set", "Orion Acronychal Set (terbenam senja)",
        361.93, 0.50, 6, 18, 347, +14.93, same_event=False,
        catatan=("Acronychal set 18 Jun (dopy 361.9). Tradisional 4 Jun "
                 "(dopy 347) memakai definisi heliacal set fajar."),
    ),
}


def astro_event_date(key: str, year: int) -> Optional[date]:
    """Return the calibrated calendar date for the astro event in a year."""
    ev = ASTRO_CALIB.get(key)
    if ev is None:
        return None
    actual_year = year if ev.mean_month >= 6 else year + 1
    try:
        return date(actual_year, ev.mean_month, ev.mean_day)
    except ValueError:
        return date(actual_year, ev.mean_month, min(ev.mean_day, 28))


def astro_delta_str(key: str) -> str:
    """Human-readable comparison against the traditional dopy."""
    ev = ASTRO_CALIB.get(key)
    if ev is None:
        return ""
    if not ev.same_event:
        return f"Δ={ev.delta:+.1f} hari (definisi berbeda)"
    if abs(ev.delta) < 0.5:
        return f"Δ={ev.delta:+.1f} hari (konsisten tradisional)"
    direction = "lebih awal" if ev.delta < 0 else "lebih lambat"
    return f"Δ={ev.delta:+.1f} hari ({abs(ev.delta):.1f} hari {direction})"


@lru_cache(maxsize=128)
def astro_events_in_range(dopy_start: float, dopy_end: float) -> Tuple[str, ...]:
    """Astro event keys whose mean dopy falls within [start, end]. Cached."""
    out: List[str] = []
    s, e = dopy_start % 365, dopy_end % 365
    for key, ev in ASTRO_CALIB.items():
        d = ev.mean_dopy % 365
        if (s <= e and s <= d <= e) or (s > e and (d >= s or d <= e)):
            out.append(key)
    return tuple(sorted(out, key=lambda k: ASTRO_CALIB[k].mean_dopy))


def build_ciri(mangsa_no: int, dopy_start: float, dopy_end: float) -> str:
    """Base phenology + inline astro markers for a mangsa span."""
    base = CIRI_BASE.get(mangsa_no, "")
    events = astro_events_in_range(dopy_start, dopy_end)
    if not events:
        return base
    parts = []
    for key in events:
        ev = ASTRO_CALIB[key]
        tgl = f"{ev.mean_day:02d} {MONTH_SHORT[ev.mean_month]}"
        parts.append(f"{ev.label} {tgl} (dopy≈{ev.mean_dopy:.1f})")
    return base + "  |  " + "  |  ".join(parts)


# ══════════════════════════════════════════════════════════════════════════
# Section 6 · Calendar scenarios
# ══════════════════════════════════════════════════════════════════════════
#
# Each scenario provides the day-of-pranata-year (dopy) at which each wet-
# season category begins. Interior mangsa boundaries are linearly interpolated
# within each wet-season category so that traditional *relative* durations are
# preserved (only the category-level spans change).

@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    musim_start: Dict[str, int]
    catatan: str
    enso_phase: str = "NETRAL"          # ELNINO | LANINA | NETRAL
    iod_phase: str = "NETRAL"           # pIOD | nIOD | NETRAL


CALIB_SCENARIOS: Dict[str, Scenario] = {
    "R30": Scenario(
        "R30", "Normal Iklim Terkini (1996–2025, 30 th)",
        {"Katiga": 19, "Labuh": 94, "Rendheng": 208, "Mareng": 286},
        ("Skenario UTAMA yang direkomendasikan untuk pemakaian sehari-hari "
         "saat ini."),
    ),
    "ALL": Scenario(
        "ALL", "Rata-rata Seluruh Data (1950–2025, 76 th)",
        {"Katiga": 32, "Labuh": 91, "Rendheng": 187, "Mareng": 286},
        ("Baseline jangka panjang — menunjukkan pergeseran vs. kondisi "
         "terkini."),
    ),
    "R10": Scenario(
        "R10", "10 Tahun Terakhir (2016–2025)",
        {"Katiga": 12, "Labuh": 131, "Rendheng": 185, "Mareng": 305},
        ("Basis 10 tahun terakhir; lebih responsif terhadap tren iklim, "
         "namun sampel kecil sehingga uncertainty lebih besar dari R30."),
    ),
    "ELNINO": Scenario(
        "ELNINO", "Tahun El Niño (ASO Niño3.4 ≥ +0.5)",
        {"Katiga": 2, "Labuh": 133, "Rendheng": 217, "Mareng": 288},
        ("Katiga jauh lebih panjang & lambat berakhir (rata-rata 131 hr vs "
         "88 hr tradisional)."),
        enso_phase="ELNINO", iod_phase="pIOD",
    ),
    "LANINA": Scenario(
        "LANINA", "Tahun La Niña (ASO Niño3.4 ≤ −0.5)",
        {"Katiga": 35, "Labuh": 79, "Rendheng": 210, "Mareng": 284},
        ("Katiga jauh lebih pendek (44 hr); musim hujan datang lebih awal."),
        enso_phase="LANINA", iod_phase="nIOD",
    ),
    "NETRAL": Scenario(
        "NETRAL", "Tahun ENSO Netral",
        {"Katiga": 11, "Labuh": 102, "Rendheng": 189, "Mareng": 288},
        "Paling mendekati pola ALL — kondisi tanpa pengaruh ENSO kuat.",
    ),
}
DEFAULT_SCENARIO: str = "R30"


@lru_cache(maxsize=16)
def build_calibrated_mangsa(scenario_key: str) -> Dict[int, float]:
    """Interpolate mangsa start dopy for a given scenario. Cached."""
    scenario = CALIB_SCENARIOS[scenario_key]
    starts = scenario.musim_start
    starts_next = {
        "Katiga":   starts["Labuh"],
        "Labuh":    starts["Rendheng"],
        "Rendheng": starts["Mareng"],
        "Mareng":   365 + starts["Katiga"],
    }
    out: Dict[int, float] = {}
    for musim, members in MUSIM_MEMBERS.items():
        o_start = ORIG_MUSIM_START[musim]
        o_len   = ORIG_MUSIM_START_NEXT[musim] - o_start
        n_start = starts[musim]
        n_len   = starts_next[musim] - n_start
        for mno in members:
            frac = (ORIG_DOPY[mno] - o_start) / o_len
            out[mno] = n_start + frac * n_len
    return out


# ══════════════════════════════════════════════════════════════════════════
# Section 7 · Meteorological climatology
# ══════════════════════════════════════════════════════════════════════════
#
# Daily fields  (METEO_MANGSA, METEO_MUSIM):
#   (hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad)
#     hj      total rainfall        [mm / mangsa]
#     hj_d    daily rainfall rate   [mm / day]
#     hhr     wet days              [days]
#     et0     FAO-56 ET0            [mm / day]
#     wb      water balance P − ET0 [mm / day]
#     sm      surface soil moisture [m³/m³]
#     rh      mean relative humidity[%]
#     tx, tn  mean T_max, T_min     [°C]
#     angin   max wind              [km/h]
#     rad     global radiation      [MJ/m²]
#
# 6-hour derived fields (METEO_MANGSA_6H, METEO_MUSIM_6H):
#   (vpd, tcwv, cloud, cloud_aft, sun_h, sm_sh, sm_dp, sT_sh, sT_dp)
#     vpd       24-h averaged VPD                [kPa]
#     tcwv      24-h averaged column water       [kg/m²]
#     cloud     24-h averaged cloud cover        [%]
#     cloud_aft 12–18 h WIB cloud cover          [%]
#     sun_h     daily sunshine duration          [h / day]
#     sm_sh     soil moisture 0–7 cm             [m³/m³]
#     sm_dp     soil moisture 28–100 cm          [m³/m³]
#     sT_sh     soil temperature 0–7 cm          [°C]
#     sT_dp     soil temperature 100–255 cm      [°C]

METEO_MANGSA: Dict[int, Tuple] = {
     1: (  23,  0.6,  5, 4.40, -3.75, 0.180, 67.1, 32.2, 21.5, 10.1, 19.9),
     2: (   9,  0.5,  2, 4.98, -4.51, 0.150, 63.7, 33.2, 21.7, 10.7, 22.1),
     3: (  17,  0.8,  3, 5.36, -4.51, 0.147, 62.3, 34.0, 22.3, 11.1, 23.3),
     4: (  85,  2.8,  9, 5.31, -2.49, 0.183, 64.3, 34.3, 23.1, 10.8, 23.0),
     5: ( 244,  7.4, 21, 4.51,  2.88, 0.273, 72.5, 32.9, 23.7,  9.4, 20.4),
     6: ( 628, 12.7, 43, 3.61,  9.12, 0.369, 81.8, 30.6, 23.3,  9.6, 17.3),
     7: ( 559, 15.5, 35, 3.41, 12.12, 0.394, 84.4, 29.7, 23.1, 11.4, 16.8),
     8: ( 344, 15.6, 21, 3.55, 12.07, 0.398, 84.6, 29.9, 23.0, 10.0, 17.6),
     9: ( 238, 11.9, 18, 3.72,  8.16, 0.389, 83.5, 30.3, 23.0,  8.8, 18.3),
    10: ( 209,  7.8, 20, 3.75,  4.01, 0.364, 81.4, 30.6, 23.0,  8.2, 18.3),
    11: (  97,  3.7, 12, 3.84, -0.10, 0.309, 77.0, 31.2, 23.0,  8.6, 18.2),
    12: (  83,  1.9, 14, 3.87, -1.99, 0.249, 72.8, 31.4, 22.2,  9.0, 18.0),
}

METEO_MUSIM: Dict[str, Tuple] = {
    "Katiga":   (  75,   60,  0.8, 4.64, -3.84, 0.180, 66.1, 32.6, 21.8, 10.3, 20.8),
    "Labuh":    ( 114,  978,  8.6, 4.32,  4.26, 0.290, 74.5, 32.3, 23.3,  9.9, 19.7),
    "Rendheng": (  78, 1140, 14.6, 3.53, 11.09, 0.390, 84.2, 29.9, 23.0, 10.3, 17.4),
    "Mareng":   (  98,  453,  4.6, 3.79,  0.82, 0.310, 77.6, 31.1, 22.9,  8.5, 18.1),
}

METEO_BULANAN: Dict[int, Tuple] = {
     1: ( 441, 14.2, 3.47, 10.75, 0.390, 83.5, 30.0, 23.1, 10.8, 16.9),
     2: ( 457, 16.2, 3.46, 12.72, 0.400, 84.7, 29.7, 23.0, 11.3, 17.1),
     3: ( 407, 13.1, 3.67,  9.44, 0.390, 83.9, 30.2, 22.9,  9.2, 18.1),
     4: ( 241,  8.1, 3.73,  4.32, 0.370, 81.6, 30.6, 23.0,  8.2, 18.2),
     5: ( 113,  3.7, 3.83, -0.18, 0.300, 76.7, 31.2, 22.9,  8.6, 18.2),
     6: (  55,  1.8, 3.83, -2.00, 0.250, 73.3, 31.4, 22.3,  9.0, 17.9),
     7: (  30,  1.0, 4.19, -3.21, 0.200, 68.8, 31.8, 21.6,  9.7, 19.2),
     8: (  14,  0.4, 4.78, -4.34, 0.160, 64.6, 32.8, 21.5, 10.4, 21.4),
     9: (  29,  1.0, 5.36, -4.40, 0.150, 62.4, 34.0, 22.3, 11.1, 23.3),
    10: ( 110,  3.5, 5.19, -1.65, 0.200, 65.8, 34.1, 23.3, 10.7, 22.6),
    11: ( 261,  8.7, 4.28,  4.41, 0.300, 74.6, 32.5, 23.7,  9.0, 19.7),
    12: ( 402, 13.0, 3.60,  9.35, 0.370, 81.7, 30.7, 23.3,  9.4, 17.2),
}

# EV09-HIST30: volatile ← EV08 adaptive IDW; consensus ← avg(EV08, EV08b).
# Source: P1 & P2 hourly 1995–2026, ~277.800 timestep · N = 31 pranata-tahun.
# Weighted combination: R31 (1995–2025) ∘ R11 (2015–2025) → 1995–2026.
# Tuple: (vpd, tcwv, cloud, cloud_aft, sun_h, sm_sh, sm_dp, sT_sh, sT_dp)
METEO_MANGSA_6H: Dict[int, Tuple] = {
     1: (1.215, 34.4, 50, 57, 10.80, 0.177, 0.230, 27.4, 27.1),  # Kasa       σ=0.1010  Δvpd=-0.130 Δsun=-0.06
     2: (1.392, 32.9, 50, 57, 10.47, 0.143, 0.205, 28.0, 27.2),  # Karo       σ=0.0950  Δvpd=-0.150 Δsun=-0.54
     3: (1.570, 33.8, 53, 58, 10.82, 0.138, 0.190, 29.0, 27.3),  # Katiga     σ=0.0720  Δvpd=-0.122 Δsun=-0.22
     4: (1.509, 37.4, 62, 64, 11.09, 0.172, 0.181, 29.4, 27.7),  # Kapat      σ=0.1220  Δvpd=-0.093 Δsun=+0.15
     5: (1.046, 45.2, 77, 79, 10.06, 0.259, 0.203, 28.8, 28.1),  # Kalima     σ=0.2390⚠ Δvpd=-0.123 Δsun=+0.00
     6: (0.535, 51.0, 90, 91,  8.37, 0.354, 0.304, 27.2, 28.0),  # Kanem      σ=0.1850⚠ Δvpd=-0.092 Δsun=-0.14
     7: (0.421, 52.5, 92, 93,  7.93, 0.377, 0.358, 26.4, 27.4),  # Kapitu     σ=0.0830  Δvpd=-0.059 Δsun=+0.13
     8: (0.404, 51.9, 89, 91,  7.94, 0.381, 0.372, 26.3, 27.0),  # Kawolu     σ=0.0250  Δvpd=-0.087 Δsun=-0.59
     9: (0.476, 50.8, 83, 86,  9.01, 0.373, 0.366, 26.7, 26.8),  # Kasanga    σ=0.0290  Δvpd=-0.071 Δsun=-0.18
    10: (0.584, 48.1, 76, 78,  9.53, 0.353, 0.352, 26.9, 26.8),  # Kasadasa   σ=0.0720  Δvpd=-0.092 Δsun=-0.11
    11: (0.759, 44.5, 63, 68,  9.76, 0.302, 0.312, 27.2, 26.9),  # Desta      σ=0.0930  Δvpd=-0.190 Δsun=-0.58
    12: (0.928, 40.7, 58, 63, 10.42, 0.248, 0.270, 27.2, 27.1),  # Sada       σ=0.0790  Δvpd=-0.094 Δsun=-0.00
}

# σ = max(|EV08−EV08b| model spread, SE_GIDW_31yr).
# M8 dan M9 turun sedikit karena SE sampling berkurang (n 11→31).
# Semua field lain masih didominasi model spread — tidak berubah.
M6H_VPD_SIGMA: Dict[int, float] = {
     1: 0.1010,   2: 0.0950,   3: 0.0720,   4: 0.1220,
     5: 0.2390,   6: 0.1850,   7: 0.0830,   8: 0.0250,
     9: 0.0290,  10: 0.0720,  11: 0.0930,  12: 0.0790,
}

# EV09-HIST30: duration-weighted dari METEO_MANGSA_6H di atas.
METEO_MUSIM_6H: Dict[str, Tuple] = {
    "Katiga":   (1.358, 33.8, 51, 10.72),  # EV09→: Δvpd=-0.133 Δsun=-0.23
    "Labuh":    (0.936, 45.8, 79,  9.57),  # EV09→: Δvpd=-0.102 Δsun=-0.02
    "Rendheng": (0.431, 51.9, 89,  8.22),  # EV09→: Δvpd=-0.070 Δsun=-0.15
    "Mareng":   (0.790, 43.7, 64, 10.00),  # EV09→: Δvpd=-0.119 Δsun=-0.19
}

# Extreme absolute temperatures (R30 1996–2025): (T_max_abs, T_min_abs).
METEO_MANGSA_EXTREME: Dict[int, Tuple[float, float]] = {
     1: (36.4, 16.3),  2: (36.7, 17.5),  3: (37.2, 17.3),
     4: (38.5, 18.5),  5: (39.3, 19.9),  6: (37.7, 20.3),
     7: (35.1, 20.1),  8: (33.6, 19.9),  9: (33.8, 18.2),
    10: (33.9, 19.4), 11: (34.9, 18.0), 12: (35.3, 17.1),
}

# R30 dopy spans per mangsa (single source of truth used by the interpolation
# engine, the extreme-temp aggregator, and the ENSO/IOD overlap weighting).
R30_DOPY_RANGES: Dict[int, Tuple[float, float]] = {
     1: ( 19.00,  53.94),  2: ( 53.94,  73.55),  3: ( 73.55,  94.00),
     4: ( 94.00, 124.00),  5: (124.00, 156.40),  6: (156.40, 208.00),
     7: (208.00, 243.68),  8: (243.68, 265.26),  9: (265.26, 286.00),
    10: (286.00, 312.73), 11: (312.73, 338.34), 12: (338.34, 384.00),
}

# R30 dopy span per *wet-season category* — derived, never hard-coded.
R30_MUSIM_DOPY: Dict[str, Tuple[float, float]] = {
    mu: (R30_DOPY_RANGES[members[0]][0],
         R30_DOPY_RANGES[members[-1]][1] - 1)
    for mu, members in MUSIM_MEMBERS.items()
}


def _extreme_for_dopy_range(
    dopy_s: float, dopy_e: float
) -> Optional[Tuple[float, float]]:
    """Worst-case (T_max_abs, T_min_abs) across mangsa overlapping a span.

    Uses max/min aggregation over the overlapping R30 mangsa set. Because
    both operators are monotone, the result is exact for the union of
    overlapping mangsa, regardless of the new dopy span's length.
    """
    tx_max, tn_min = -np.inf, +np.inf
    found = False
    for no, (rs, re) in R30_DOPY_RANGES.items():
        if min(dopy_e, re) - max(dopy_s, rs) > 0:
            tx, tn = METEO_MANGSA_EXTREME[no]
            tx_max = max(tx_max, tx)
            tn_min = min(tn_min, tn)
            found = True
    return (tx_max, tn_min) if found else None


def _fmt_suhu(
    tx: float, tn: float,
    dopy_s: Optional[float] = None,
    dopy_e: Optional[float] = None,
) -> str:
    """Format mean ± extreme temperature line."""
    if dopy_s is not None and dopy_e is not None:
        ext = _extreme_for_dopy_range(dopy_s, dopy_e)
        if ext is not None:
            tx_a, tn_a = ext
            return (f"Tx̄ {tx:.1f}°C ({tx_a:.1f}°C) · "
                    f"Tn̄ {tn:.1f}°C ({tn_a:.1f}°C)")
    return f"Tx̄ {tx:.1f}°C · Tn̄ {tn:.1f}°C"


# ══════════════════════════════════════════════════════════════════════════
# Section 8 · ENSO and IOD perturbation models
# ══════════════════════════════════════════════════════════════════════════
#
# Empirical delta composites (daily IDW-merged ERA5/ERA5-Land at P1+P2).
# Per-mangsa tuple: (Δtx, Δtn, Δhj_d, Δet0, Δrad, Δrh).
#
# ENSO classification from ASO Niño3.4 MSLA (Aug–Sep–Oct mean):
#   El Niño years (8) : 1997, 2002, 2004, 2006, 2009, 2015, 2018, 2023
#   La Niña  years (11): 1998, 1999, 2007, 2008, 2010, 2011, 2016, 2017,
#                        2020, 2024, 2025
#
# IOD classification from SON DMI (BOM, ±0.40 °C threshold),
# ENSO-filtered by |ASO Niño3.4| < 0.50:
#   pIOD (8)  : 1961, 1963, 1967, 1972, 1982, 2012, 2018, 2019
#   nIOD (7)  : 1960, 1974, 1975, 1984, 1996, 2005, 2024
#
# IOD corrections are only active during mangsa 3–5 (SON overlap ≥ 15 d).
# Weighting: standalone 0.30; ENSO-synergistic (El Niño + pIOD, La Niña +
# nIOD) 0.50.

ENSO_DELTA: Dict[str, Dict[int, Tuple[float, ...]]] = {
    "ELNINO": {
         1: ( +0.19, -0.40, -0.014, +0.084, +0.24, -2.0),
         2: ( -0.04, -0.62, -0.018, +0.031, +0.22, -1.5),
         3: ( +0.13, -0.58, -0.029, +0.168, +0.66, -1.8),
         4: ( +0.82, -0.57, -0.080, +0.584, +1.94, -5.6),
         5: ( +2.14, +0.38, -0.134, +0.835, +2.65, -8.7),
         6: ( +0.42, +0.21, -0.026, +0.173, +0.75, -1.1),
         7: ( -0.31, -0.12, +0.002, -0.108, -0.51, +0.2),
         8: ( -0.14, -0.22, -0.008, -0.004, +0.06, -0.1),
         9: ( +0.01, -0.12, -0.040, +0.078, +0.42, -0.7),
        10: ( +0.18, -0.13, -0.059, +0.140, +0.59, -1.5),
        11: ( +0.02, -0.24, -0.009, +0.055, +0.16, -0.9),
        12: ( +0.40, -0.27, -0.027, +0.261, +0.88, -3.2),
    },
    "LANINA": {
         1: ( -0.24, +0.35, +0.004, -0.108, -0.34, +2.0),
         2: ( -0.06, +0.38, +0.017, +0.010, -0.06, +1.0),
         3: ( -0.15, +0.38, +0.033, -0.110, -0.45, +1.8),
         4: ( -0.45, +0.38, +0.037, -0.243, -0.92, +3.0),
         5: ( -1.06, -0.14, +0.058, -0.456, -1.54, +4.7),
         6: ( -0.03, +0.09, -0.007, -0.003, -0.04, -0.1),
         7: ( +0.46, +0.25, -0.021, +0.144, +0.60, -0.6),
         8: ( +0.20, +0.23, +0.057, -0.022, -0.16, +0.3),
         9: ( +0.04, +0.25, +0.060, -0.157, -0.86, +0.7),
        10: ( -0.14, +0.27, +0.050, -0.176, -0.78, +1.6),
        11: ( -0.00, +0.23, +0.026, -0.072, -0.29, +1.0),
        12: ( -0.09, +0.24, +0.010, -0.110, -0.31, +1.4),
    },
    "NETRAL": {no: (0.,) * 6 for no in range(1, 13)},
}

IOD_DELTA: Dict[str, Dict[int, Tuple[float, ...]]] = {
    "pIOD": {
        no: (0.,) * 6 for no in range(1, 13)
    } | {
        3: (+0.534, -0.617, -0.943, +0.476, +1.175,  -4.860),
        4: (+1.278, -0.316, -2.224, +0.730, +1.690,  -7.271),
        5: (+2.345, +0.244, -4.980, +0.879, +2.461, -10.023),
    },
    "nIOD": {
        no: (0.,) * 6 for no in range(1, 13)
    } | {
        3: (-0.841, +0.468, +2.365, -0.423, -1.459, +5.183),
        4: (-0.831, +0.217, +2.437, -0.383, -1.149, +4.998),
        5: (-0.487, -0.064, +1.359, -0.112, -0.319, +1.964),
    },
    "NETRAL": {no: (0.,) * 6 for no in range(1, 13)},
}

IOD_STANDALONE_WEIGHT: float = 0.30
IOD_SYNERGY_WEIGHT:    float = 0.50
IOD_MIN_OVERLAP_DAYS:  float = 15.0     # SON-overlap gate


def _overlap_weights(
    dopy_s: float, dopy_e: float
) -> Dict[int, float]:
    """Normalised overlap fractions of [dopy_s, dopy_e] with R30 mangsa."""
    weights: Dict[int, float] = {}
    for no, (rs, re) in R30_DOPY_RANGES.items():
        ovl = max(0.0, min(dopy_e, re) - max(dopy_s, rs))
        if ovl > 0:
            weights[no] = ovl
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()} if total else {}


def _enso_delta_for_dopy_range(
    dopy_s: float, dopy_e: float, enso_phase: str
) -> Tuple[float, ...]:
    """Dopy-weighted ENSO delta vector for an arbitrary mangsa span.

    The composite delta is expressed per R30 mangsa; for a shifted span we
    take the overlap-weighted mean. Physically this is 'dopy-anchored ENSO':
    the correction follows the *calendar position*, not the mangsa label.
    """
    if enso_phase not in ENSO_DELTA or enso_phase == "NETRAL":
        return (0.,) * 6
    wn = _overlap_weights(dopy_s, dopy_e)
    if not wn:
        return (0.,) * 6
    table = ENSO_DELTA[enso_phase]
    return tuple(
        sum(wn[no] * table[no][fi] for no in wn) for fi in range(6)
    )


def _iod_delta_for_dopy_range(
    dopy_s: float, dopy_e: float, iod_phase: str, enso_phase: str = "NETRAL"
) -> Tuple[float, ...]:
    """Dopy-weighted IOD delta vector, gated to SON-overlap ≥ 15 days.

    Mangsa whose IOD composite is identically zero are excluded *before*
    re-normalisation so that the pIOD/nIOD signal is not diluted by
    overlap with the inactive window (mangsa 6–12).
    """
    if iod_phase not in IOD_DELTA or iod_phase == "NETRAL":
        return (0.,) * 6

    weights = _overlap_weights(dopy_s, dopy_e)
    if not weights:
        return (0.,) * 6

    table = IOD_DELTA[iod_phase]
    # Keep only contributing mangsa (any nonzero component) and require the
    # residual overlap with those mangsa to reach the SON gate.
    contributing = {
        no: w for no, w in weights.items()
        if any(abs(x) > 1e-9 for x in table[no])
    }
    residual_days = sum(contributing.values()) * (dopy_e - dopy_s)
    if residual_days < IOD_MIN_OVERLAP_DAYS or not contributing:
        return (0.,) * 6

    total = sum(contributing.values())
    wn = {no: w / total for no, w in contributing.items()}

    synergistic = (
        (enso_phase == "ELNINO" and iod_phase == "pIOD") or
        (enso_phase == "LANINA" and iod_phase == "nIOD")
    )
    weight = IOD_SYNERGY_WEIGHT if synergistic else IOD_STANDALONE_WEIGHT

    raw = tuple(sum(wn[no] * table[no][fi] for no in wn) for fi in range(6))
    return tuple(weight * x for x in raw)


# ══════════════════════════════════════════════════════════════════════════
# Section 9 · Climate interpolation engine
# ══════════════════════════════════════════════════════════════════════════
#
# Single point of truth for scenario climatology. Do NOT compare scenario
# mangsa N against R30 mangsa N — the dopy spans differ. Always invoke
# meteo_for_dopy_range(dopy_s, dopy_e, ...) with the actual calendar span.
#
# Physical parameterisations (applied to the 6-hour derived fields):
#
#   ΔVPD    = 0.075 · ΔT_mean − 0.030 · ΔRH             [kPa]
#   ΔTCWV   = −1.75 · ΔT_mean                           [kg/m²]
#   Δsun_h  =  0.20 · Δrad                              [h/day]
#
# The VPD coefficients empirically calibrated against P1 hourly data
# at T ≈ 30 °C, RH ≈ 70 %; the TCWV sign is the Maritime-Continent signature
# of ENSO (Walker-cell displacement lowers local column water even as T
# rises). Calibrated against 30 years of P1 hourly data.

_HHR_SCALE_EXPONENT: float = 0.6      # wet-day partial scaling exponent
_DVPD_DT: float = 0.075                # kPa/K
_DVPD_DRH: float = -0.030              # kPa per %RH
_DTCWV_DT: float = -1.75               # kg/m² per K
_DSUN_DRAD: float = 0.20               # h/day per MJ/m²
_DCLOUD_DRAD: float = -5.0             # % per MJ/m²  — IOD only
# Cloud correction hanya untuk IOD (Walker-cell displacement mengubah
# tutupan awan secara lebih langsung via perubahan SST lokal dan
# konveksi regional). ENSO tidak dikoreksi di sini karena sinyal cloud
# ENSO sudah terserap di sun_h via _DSUN_DRAD.
# Konstanta −5.0 diambil dari JS (meteoForDopyRange, IOD block):
#   m6h[2] -= 5.0 * dRadI  (cloud)
#   m6h[3] -= 5.0 * dRadI  (cloud_aft)
# Berlaku untuk pIOD maupun nIOD (tanda mengikuti dRad).

@lru_cache(maxsize=512)
def meteo_for_dopy_range(
    dopy_s: float, dopy_e: float,
    enso_phase: str = "NETRAL",
    iod_phase: str = "NETRAL",
) -> Tuple[Optional[Tuple], Optional[Tuple]]:
    """Interpolated climatology for an arbitrary dopy span. Cached.

    See module-level section 9 header for the physical model. Returns
    (daily_tuple, six_hour_tuple); either may be None if the span does not
    overlap any R30 mangsa.
    """
    weights = _overlap_weights(dopy_s, dopy_e)
    if not weights:
        return None, None
    dur = max(dopy_e - dopy_s, 1.0)

    # ── Daily fields: rate interpolation + partial scaling of wet days ──
    rate_idx = (1, 3, 4, 5, 6, 7, 8, 9, 10)
    seed_no = next(iter(weights))
    vals = list(METEO_MANGSA[seed_no])

    wetday_frac = sum(
        w * METEO_MANGSA[no][2]
          / (R30_DOPY_RANGES[no][1] - R30_DOPY_RANGES[no][0])
        for no, w in weights.items()
    )
    vals[2] = round(wetday_frac * dur)

    for fi in rate_idx:
        vals[fi] = sum(w * METEO_MANGSA[no][fi] for no, w in weights.items())
    vals[0] = round(vals[1] * dur)

    hj_d_base, hhr_base = vals[1], vals[2]
    enso_delta = iod_delta = None

    # ── ENSO correction (daily) ─────────────────────────────────────────
    if enso_phase in ("ELNINO", "LANINA"):
        enso_delta = _enso_delta_for_dopy_range(dopy_s, dopy_e, enso_phase)
        d_tx, d_tn, d_hjd, d_et0, d_rad, d_rh = enso_delta

        hj_d_new = hj_d_base + d_hjd
        vals[1], vals[0] = hj_d_new, round(hj_d_new * dur)

        if hj_d_base > 0.05:
            scale = hj_d_new / hj_d_base
            vals[2] = max(0, round(hhr_base * (scale ** _HHR_SCALE_EXPONENT)))
        vals[3] += d_et0
        vals[6] += d_rh
        vals[7] += d_tx
        vals[8] += d_tn
        vals[10] += d_rad
        vals[4] = vals[1] - vals[3]

    m_tuple = tuple(vals)

    # ── IOD correction (daily) ──────────────────────────────────────────
    if iod_phase in ("pIOD", "nIOD"):
        iod_delta = _iod_delta_for_dopy_range(
            dopy_s, dopy_e, iod_phase, enso_phase
        )
        if any(abs(x) > 1e-9 for x in iod_delta):
            v = list(m_tuple)
            hj_d_pre, hhr_pre = v[1], v[2]
            d_tx_i, d_tn_i, d_hjd_i, d_et0_i, d_rad_i, d_rh_i = iod_delta
            hj_d_new = hj_d_pre + d_hjd_i
            v[1], v[0] = hj_d_new, round(hj_d_new * dur)
            if hj_d_pre > 0.05:
                scale = hj_d_new / hj_d_pre
                v[2] = max(0, round(hhr_pre * (scale ** _HHR_SCALE_EXPONENT)))
            v[3] += d_et0_i
            v[4] = v[1] - v[3]
            v[6] += d_rh_i
            v[7] += d_tx_i
            v[8] += d_tn_i
            v[10] += d_rad_i
            m_tuple = tuple(v)

    # ── 6-hour derived: direct field interpolation + physical deltas ────
    m6h_vals = [
        sum(w * METEO_MANGSA_6H[no][fi] for no, w in weights.items())
        for fi in range(9)
    ]

    for delta, phase in ((enso_delta, enso_phase), (iod_delta, iod_phase)):
        if delta is None or phase == "NETRAL":
            continue
        d_tx, d_tn, _, _, d_rad, d_rh = delta
        d_tmean = 0.5 * (d_tx + d_tn)
        m6h_vals[0] = max(0.0, m6h_vals[0] + _DVPD_DT  * d_tmean
                                            + _DVPD_DRH * d_rh)
        m6h_vals[1] = max(0.0, m6h_vals[1] + _DTCWV_DT * d_tmean)
        m6h_vals[4] = min(13.0, max(6.0,
                          m6h_vals[4] + _DSUN_DRAD * d_rad))
        # Cloud correction: hanya aktif untuk IOD (ENSO diabaikan — lihat
        # komentar di _DCLOUD_DRAD). Sebelumnya ada di JS tapi tidak di Python.
        if phase in ("pIOD", "nIOD"):
            m6h_vals[2] = min(100.0, max(0.0,
                              m6h_vals[2] + _DCLOUD_DRAD * d_rad))
            m6h_vals[3] = min(100.0, max(0.0,
                              m6h_vals[3] + _DCLOUD_DRAD * d_rad))

    return m_tuple, tuple(m6h_vals)


# ══════════════════════════════════════════════════════════════════════════
# Section 10 · Hidden Markov Model parameters
# ══════════════════════════════════════════════════════════════════════════
#
# 4-D legacy model: [rain_30d, wb_30d, sm_30d, rh_30d].
# 8-D EV06b model : [rain_30d, wb_30d, sm_30d, rh_30d,
#                    tcwv_30d, dtr_30d, cloud_30d, smd_30d].

HMM_T_pi    = [0.0, 1.0, 0.0, 0.0]
HMM_T_A     = [
    [0.9425, 0.0575, 0.0000, 0.0000],
    [0.0529, 0.8871, 0.0000, 0.0600],
    [0.0000, 0.0000, 0.9543, 0.0457],
    [0.0000, 0.0574, 0.0516, 0.8910],
]
HMM_T_means = [
    [-1.0662, -1.1139, -1.4893, -1.4005],
    [-0.7011, -0.6798, -0.4381, -0.4862],
    [ 1.2559,  1.2481,  0.9896,  1.0313],
    [ 0.1795,  0.2094,  0.5963,  0.5180],
]
HMM_T_covs = [
    [[0.00333, 0.00337, 0.00666, 0.00613],
     [0.00337, 0.01149, 0.02119, 0.04043],
     [0.00666, 0.02119, 0.06652, 0.08894],
     [0.00613, 0.04043, 0.08894, 0.19196]],
    [[0.08677, 0.07744, 0.02992, 0.02422],
     [0.07744, 0.07613, 0.05928, 0.05991],
     [0.02992, 0.05928, 0.25335, 0.23600],
     [0.02422, 0.05991, 0.23600, 0.26591]],
    [[0.26552, 0.25858, 0.02309, 0.05224],
     [0.25858, 0.25298, 0.02295, 0.05313],
     [0.02309, 0.02295, 0.00357, 0.00743],
     [0.05224, 0.05313, 0.00743, 0.02512]],
    [[0.29796, 0.27850, 0.04217, 0.03377],
     [0.27850, 0.26355, 0.04823, 0.04586],
     [0.04217, 0.04823, 0.07873, 0.07706],
     [0.03377, 0.04586, 0.07706, 0.10589]],
]
HMM_T_mu = [218.561, 96.474, 0.29663, 75.725]
HMM_T_sd = [193.949, 210.002, 0.09978, 8.9105]

HMM_T_STATE = {
    0: "Katiga      — kering (kemarau puncak)",
    1: "Labuh/Mareng — transisi kering → sedang",
    2: "Rendheng    — hujan puncak (basah)",
    3: "Labuh/Mareng — transisi sedang → basah",
}

HMM_T8_pi    = [0.0, 1.0, 0.0, 0.0]
HMM_T8_mu    = [218.50968, 94.95218, 0.27494, 75.28310,
                44.07459,  7.80143, 71.16249, 0.27615]
HMM_T8_sd    = [196.21025, 213.10715, 0.10689, 9.14500,
                 8.20608,   2.05462, 17.96527, 0.09706]
HMM_T8_means = [
    [-0.99199, -0.96909, -0.98870, -0.93154, -1.12689,  1.09432, -1.08972, -0.58020],
    [ 0.01315, -0.04637, -0.21487, -0.34309, -0.06776,  0.11755,  0.13064, -0.53510],
    [ 1.22106,  1.20684,  0.92099,  0.97957,  0.94877, -0.93550,  1.05342,  0.86449],
    [-0.22744, -0.16457,  0.27292,  0.33157,  0.18566, -0.22910, -0.15607,  0.37753],
]
HMM_T8_covs = [
    [[ 0.03054,  0.03668,  0.08960,  0.08275,  0.07756, -0.08183,  0.04637,  0.05648],
     [ 0.03668,  0.04814,  0.12625,  0.11997,  0.09626, -0.10651,  0.06110,  0.09406],
     [ 0.08960,  0.12625,  0.44146,  0.38006,  0.22655, -0.25419,  0.17190,  0.40982],
     [ 0.08275,  0.11997,  0.38006,  0.37334,  0.24233, -0.27635,  0.15879,  0.36183],
     [ 0.07756,  0.09626,  0.22655,  0.24233,  0.33738, -0.32056,  0.13814,  0.10726],
     [-0.08183, -0.10651, -0.25419, -0.27635, -0.32056,  0.37360, -0.13584, -0.13805],
     [ 0.04637,  0.06110,  0.17190,  0.15879,  0.13814, -0.13584,  0.21501,  0.13741],
     [ 0.05648,  0.09406,  0.40982,  0.36183,  0.10726, -0.13805,  0.13741,  0.52406]],
    [[ 0.84378,  0.88919,  0.85516,  0.92098,  0.78767, -0.89999,  0.76891,  0.62175],
     [ 0.88919,  0.93970,  0.91392,  0.98682,  0.83864, -0.95997,  0.81964,  0.66598],
     [ 0.85516,  0.91392,  1.03046,  1.05695,  0.81745, -0.99372,  0.81979,  0.81700],
     [ 0.92098,  0.98682,  1.05695,  1.14499,  0.94168, -1.08900,  0.91625,  0.78475],
     [ 0.78767,  0.83864,  0.81745,  0.94168,  0.99774, -1.00594,  0.88420,  0.42368],
     [-0.89999, -0.95997, -0.99372, -1.08900, -1.00594,  1.15089, -0.93833, -0.62722],
     [ 0.76891,  0.81964,  0.81979,  0.91625,  0.88420, -0.93833,  0.91116,  0.49956],
     [ 0.62175,  0.66598,  0.81700,  0.78475,  0.42368, -0.62722,  0.49956,  0.98265]],
    [[ 0.29130,  0.28385,  0.10930,  0.09243,  0.03951, -0.02144,  0.07098,  0.17482],
     [ 0.28385,  0.27805,  0.10946,  0.09354,  0.04045, -0.02818,  0.07384,  0.17654],
     [ 0.10930,  0.10946,  0.11171,  0.06105, -0.02207,  0.00894,  0.00656,  0.19937],
     [ 0.09243,  0.09354,  0.06105,  0.05042,  0.01226, -0.01845,  0.02233,  0.10996],
     [ 0.03951,  0.04045, -0.02207,  0.01226,  0.09004, -0.05524,  0.04682, -0.03493],
     [-0.02144, -0.02818,  0.00894, -0.01845, -0.05524,  0.09147, -0.04639,  0.00206],
     [ 0.07098,  0.07384,  0.00656,  0.02233,  0.04682, -0.04639,  0.09373,  0.00445],
     [ 0.17482,  0.17654,  0.19937,  0.10996, -0.03493,  0.00206,  0.00445,  0.39624]],
    [[ 0.49767,  0.48123,  0.37605,  0.36813,  0.37565, -0.28695,  0.47199,  0.32410],
     [ 0.48123,  0.46752,  0.37697,  0.36632,  0.36476, -0.27978,  0.45925,  0.32669],
     [ 0.37605,  0.37697,  0.54927,  0.43013,  0.27650, -0.20948,  0.38532,  0.51309],
     [ 0.36813,  0.36632,  0.43013,  0.39387,  0.33140, -0.26910,  0.39826,  0.38236],
     [ 0.37565,  0.36476,  0.27650,  0.33140,  0.50766, -0.37421,  0.47227,  0.19054],
     [-0.28695, -0.27978, -0.20948, -0.26910, -0.37421,  0.34751, -0.36659, -0.13466],
     [ 0.47199,  0.45925,  0.38532,  0.39826,  0.47227, -0.36659,  0.59074,  0.29875],
     [ 0.32410,  0.32669,  0.51309,  0.38236,  0.19054, -0.13466,  0.29875,  0.53854]],
]
HMM_T8_A = [
    [0.98667, 0.01333, 0.00000, 0.00000],
    [0.00000, 0.99123, 0.00877, 0.00000],
    [0.00000, 0.00000, 0.98718, 0.01282],
    [0.01018, 0.00000, 0.00000, 0.98982],
]


# ══════════════════════════════════════════════════════════════════════════
# Section 11 · Domain model & calendar builders
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MangsaEntry:
    """A single mangsa instance placed on the Gregorian calendar."""
    no: int
    nama: str
    musim: str
    mulai: date
    akhir: date
    durasi: int
    ciri: str
    dopy_start: float
    dopy_end: float
    candra: str = ""


def fmt(d: date) -> str:
    return f"{d.day:02d} {MONTH_SHORT[d.month]} {d.year}"


def get_pranatamangsa_year_and_dopy(d: date) -> Tuple[int, int]:
    """Return (pranatamangsa_year, day-of-pranata-year) for a date."""
    anchor = date(d.year, ANCHOR_MONTH, ANCHOR_DAY)
    if d >= anchor:
        return d.year, (d - anchor).days
    anchor = date(d.year - 1, ANCHOR_MONTH, ANCHOR_DAY)
    return d.year - 1, (d - anchor).days


def dopy_to_date(pyear: int, dopy: float) -> date:
    return (date(pyear, ANCHOR_MONTH, ANCHOR_DAY)
            + timedelta(days=int(round(dopy))))


def _musim_for_mangsa(no: int) -> str:
    for musim, members in MUSIM_MEMBERS.items():
        if no in members:
            return musim
    raise ValueError(f"Mangsa {no} not assigned to any wet-season category.")


def build_calendar_tradisional(pyear: int) -> List[MangsaEntry]:
    """Traditional Paku Buwana VII calendar for one pranatamangsa year."""
    cal: List[MangsaEntry] = []
    for spec in MANGSAS:
        cy = (pyear if (spec.start_month > ANCHOR_MONTH or
              (spec.start_month == ANCHOR_MONTH and spec.start_day >= ANCHOR_DAY))
              else pyear + 1)
        start = date(cy, spec.start_month, spec.start_day)
        dur = spec.duration + (1 if spec.no == 8 and is_leap_year(cy) else 0)
        end = start + timedelta(days=dur - 1)
        cal.append(MangsaEntry(
            no=spec.no, nama=spec.nama, musim=_musim_for_mangsa(spec.no),
            mulai=start, akhir=end, durasi=dur,
            ciri=CIRI_TRADISIONAL.get(spec.no, ""),
            dopy_start=float(ORIG_DOPY[spec.no]),
            dopy_end=float(ORIG_DOPY[spec.no] + dur - 1),
            candra=CIRI_JAWA.get(spec.no, ""),
        ))
    return cal


def build_calendar_terkalibrasi(
    pyear: int, scenario_key: str = DEFAULT_SCENARIO
) -> List[MangsaEntry]:
    """Calibrated calendar for one pranatamangsa year."""
    new_dopy = build_calibrated_mangsa(scenario_key)
    sorted_nos = sorted(new_dopy.keys())
    cal: List[MangsaEntry] = []
    for i, no in enumerate(sorted_nos):
        spec = next(x for x in MANGSAS if x.no == no)
        start = dopy_to_date(pyear, new_dopy[no])
        nxt_no = sorted_nos[(i + 1) % 12]
        if nxt_no != 1:
            nxt_dp = new_dopy[nxt_no]
            end = dopy_to_date(pyear, nxt_dp) - timedelta(days=1)
        else:
            nxt_dp = 365 + new_dopy[1]      
            end = dopy_to_date(pyear + 1, new_dopy[1]) - timedelta(days=1)
        cal.append(MangsaEntry(
            no=no, nama=spec.nama, musim=_musim_for_mangsa(no),
            mulai=start, akhir=end, durasi=(end - start).days + 1,
            ciri=build_ciri(no, new_dopy[no], nxt_dp - 1),
            dopy_start=new_dopy[no], dopy_end=nxt_dp - 1,
        ))
    return cal


def get_mangsa_by_date(
    tanggal: date, mode: str = "tradisional",
    scenario_key: str = DEFAULT_SCENARIO,
) -> Optional[MangsaEntry]:
    """Locate the mangsa containing `tanggal` under the selected mode."""
    pyear, _ = get_pranatamangsa_year_and_dopy(tanggal)
    # Only pyear and pyear-1 can contain the date (anchor is 22 Jun).
    for py in (pyear, pyear - 1):
        cal = (build_calendar_tradisional(py) if mode == "tradisional"
               else build_calendar_terkalibrasi(py, scenario_key))
        for entry in cal:
            if entry.mulai <= tanggal <= entry.akhir:
                return entry
    return None


# ══════════════════════════════════════════════════════════════════════════
# Section 12 · Nowcast pipeline
# ══════════════════════════════════════════════════════════════════════════

def find_data_file(filename: str) -> Optional[str]:
    """Search cwd and script directory for a data file."""
    if not filename:
        return None
    candidates = [filename, filename.replace("_", ".")]
    for folder in (".", os.path.dirname(os.path.abspath(__file__))):
        for cand in candidates:
            p = os.path.join(folder, cand)
            if os.path.exists(p):
                return p
    return None


def _idw_weights(
    lat_t: float, lon_t: float,
    coords: Sequence[Tuple[float, float]],
    power: float = IDW_POWER,
    var_class: str = "volatile",          # "volatile" | "soil"
) -> List[float]:
    """
    GIDW-aware interpolation coefficients (normalised).

    For the standard 2-station (P1, P2) configuration, returns the
    pre-computed mean GIDW effective weights derived from the full
    variable-specific calibration (met_idw_blender.py).  The `var_class`
    argument selects which weight set to use:
      · "volatile" (default): VPD/TCWV/cloud/sunshine class
                              (_IDW_W1_VPD, _IDW_W2_VPD)
      · "soil"              : soil-moisture/temperature class
                              (_IDW_W1_SOIL, _IDW_W2_SOIL)
    For other configurations, falls back to Haversine-based IDW (power p).

    Haversine replaces the legacy Euclidean degree-distance (EV06b):
      Euclidean: d ≈ √(Δlat² + Δlon²) [degrees, ignores cos(lat)]
      Haversine: proper great-circle km — reduces distance error ~5% at
      −7.5°S and eliminates the lon-compression artefact.
    """
    import math as _math
    _R = 6371.0088

    def _hav(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        p1, l1 = _math.radians(lat1), _math.radians(lon1)
        p2, l2 = _math.radians(lat2), _math.radians(lon2)
        a = (_math.sin((p2 - p1) / 2) ** 2
             + _math.cos(p1) * _math.cos(p2) * _math.sin((l2 - l1) / 2) ** 2)
        return 2.0 * _R * _math.asin(_math.sqrt(max(0.0, min(1.0, a))))

    # Fast path: standard 2-station P1+P2 → use EV09 hybrid weights
    if (len(coords) == 2
            and coords[0] == STATION_P1
            and coords[1] == STATION_P2):
        if var_class == "soil":
            return [_IDW_W1_SOIL, _IDW_W2_SOIL]
        return [_IDW_W1_VPD, _IDW_W2_VPD]

    dists = [_hav(c[0], lat_t, c[1], lon_t) for c in coords]
    for i, d in enumerate(dists):
        if d < 1e-6:
            return [1.0 if j == i else 0.0 for j in range(len(coords))]
    raw = [1.0 / (d ** power) for d in dists]
    s   = sum(raw)
    return [x / s for x in raw]


def _read_openmeteo_csv(path: str) -> "pd.DataFrame":
    """Read an Open-Meteo CSV, auto-detecting the header row.

    Open-Meteo prepends 2–3 metadata lines; header detection via the
    'time,...' first-column signature is robust to version changes.
    """
    with open(path, "r", encoding="utf-8") as fh:
        skip = 0
        for i, line in enumerate(fh):
            if line.lstrip().startswith("time,"):
                skip = i
                break
    df = pd.read_csv(path, skiprows=skip)
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").reset_index(drop=True)


def _idw_merge(
    df1: "pd.DataFrame", df2: "pd.DataFrame",
    w1: float, w2: float, index_col: str = "time",
) -> "pd.DataFrame":
    """IDW-merge two dataframes column-by-column with graceful fallback."""
    d1 = df1.set_index(index_col)
    d2 = df2.set_index(index_col)
    shared = [c for c in d1.columns if c in d2.columns]
    idx = d1.index.union(d2.index)
    out = pd.DataFrame(index=idx)
    for col in shared:
        v1 = d1[col].reindex(idx)
        v2 = d2[col].reindex(idx)
        both = v1.notna() & v2.notna()
        only1 = v1.notna() & ~v2.notna()
        only2 = ~v1.notna() & v2.notna()
        out.loc[both, col] = w1 * v1[both] + w2 * v2[both]
        out.loc[only1, col] = v1[only1]
        out.loc[only2, col] = v2[only2]
    for col in [c for c in d2.columns if c not in shared]:
        out[col] = d2[col].reindex(idx)
    return out.reset_index().rename(columns={"index": index_col})


def _aggregate_to_daily(
    m: "pd.DataFrame",
    aft_slots: Sequence[int],
    sec_per_slot: int,
) -> "pd.DataFrame":
    """Vectorised sub-hourly → daily aggregation (EV07 revision).

    Replaces the earlier `.groupby("_date").apply()` pattern (≈7,300 Python
    iterations across two stations) with C-level groupby reducers. All
    numerical outputs are identical to the previous version; only execution
    path changes.

    Output columns: tcwv, dtr, cloud_mean, cloud_aft, sm28_100, sm_sh,
    sT_sh, sT_dp, sunshine_h, sw_rad_MJ, vpd.
    """
    m = m.copy()
    m["_date"] = pd.to_datetime(m["time"]).dt.normalize()
    m["_hour"] = pd.to_datetime(m["time"]).dt.hour
    g = m.groupby("_date")

    agg: Dict[str, "pd.Series"] = {}
    for out_name, src in {
        "tcwv":       "total_column_integrated_water_vapour (kg/m²)",
        "cloud_mean": "cloud_cover (%)",
        "sm28_100":   "soil_moisture_28_to_100cm (m³/m³)",
        "sm_sh":      "soil_moisture_0_to_7cm (m³/m³)",
        "sT_sh":      "soil_temperature_0_to_7cm (°C)",
        "sT_dp":      "soil_temperature_100_to_255cm (°C)",
        "vpd":        "vapour_pressure_deficit (kPa)",
    }.items():
        if src in m.columns:
            agg[out_name] = g[src].mean()

    if "temperature_2m (°C)" in m.columns:
        agg["dtr"] = (g["temperature_2m (°C)"].max()
                      - g["temperature_2m (°C)"].min())
    if "cloud_cover (%)" in m.columns:
        agg["cloud_aft"] = (m[m["_hour"].isin(aft_slots)]
                             .groupby("_date")["cloud_cover (%)"].mean())
    if "sunshine_duration (s)" in m.columns:
        agg["sunshine_h"] = g["sunshine_duration (s)"].sum() / 3600.0
    if "shortwave_radiation (W/m²)" in m.columns:
        agg["sw_rad_MJ"] = (g["shortwave_radiation (W/m²)"].sum()
                            * sec_per_slot / 1e6)

    return (pd.DataFrame(agg).reset_index()
              .rename(columns={"_date": "time"}))


def load_interpolated_meteo(
    csv1: str = DEFAULT_DAILY_CSV_P1,
    csv2: str = DEFAULT_DAILY_CSV_P2,
    lat_t: float = TARGET_LAT, lon_t: float = TARGET_LON,
) -> Optional["pd.DataFrame"]:
    """Load daily P1+P2, IDW-merged onto the target point."""
    if not HAS_PANDAS:
        return None
    p1, p2 = find_data_file(csv1), find_data_file(csv2)
    if p1 is None and p2 is None:
        return None
    w1, w2 = _idw_weights(lat_t, lon_t, [STATION_P1, STATION_P2])
    if p1 is None:
        return _read_openmeteo_csv(p2)
    if p2 is None:
        return _read_openmeteo_csv(p1)
    return _idw_merge(_read_openmeteo_csv(p1),
                      _read_openmeteo_csv(p2), w1, w2).reset_index(drop=True)


def load_interpolated_6h(
    csv_6h_p1: str = DEFAULT_6H_CSV_P1,
    csv_6h_p2: str = DEFAULT_6H_CSV_P2,
    hourly_p1: str = DEFAULT_HOURLY_CSV_P1,
    hourly_p2: str = DEFAULT_HOURLY_CSV_P2,
    lat_t: float = TARGET_LAT, lon_t: float = TARGET_LON,
) -> Optional["pd.DataFrame"]:
    """Load hourly (preferred) or 6-hourly inputs, aggregate to daily, IDW-merge."""
    if not HAS_PANDAS:
        return None

    def _per_station(hourly_path, six_path):
        p_hourly = find_data_file(hourly_path)
        p_six = find_data_file(six_path)
        if p_hourly is not None:
            return _aggregate_to_daily(_read_openmeteo_csv(p_hourly),
                                        aft_slots=tuple(range(12, 18)),
                                        sec_per_slot=3600)
        if p_six is not None:
            return _aggregate_to_daily(_read_openmeteo_csv(p_six),
                                        aft_slots=(12, 18),
                                        sec_per_slot=21600)
        return None

    agg1 = _per_station(hourly_p1, csv_6h_p1)
    agg2 = _per_station(hourly_p2, csv_6h_p2)
    if agg1 is None and agg2 is None:
        return None
    if agg1 is None:
        return agg2
    if agg2 is None:
        return agg1
    w1, w2 = _idw_weights(lat_t, lon_t, [STATION_P1, STATION_P2])
    return _idw_merge(agg1, agg2, w1, w2).reset_index(drop=True)


def _log_mvn(X: np.ndarray, mean, cov) -> np.ndarray:
    """Log-density of multivariate normal with Tikhonov regularisation."""
    cov = np.asarray(cov) + 1e-6 * np.eye(len(mean))
    if HAS_SCIPY:
        try:
            from scipy.stats._multivariate import multivariate_normal_gen
            return multivariate_normal_gen().logpdf(X, mean=mean, cov=cov)
        except Exception:
            pass
    diff = X - np.array(mean)
    inv = np.linalg.inv(cov)
    _, logdet = np.linalg.slogdet(cov)
    d = len(mean)
    if diff.ndim == 2:
        quad = np.einsum("ij,jk,ik->i", diff, inv, diff)
    else:
        quad = diff @ inv @ diff
    return -0.5 * (d * np.log(2 * np.pi) + logdet + quad)


def hmm_causal_filter(
    Xz: np.ndarray,
    pi=None, A=None, means=None, covs=None,
) -> np.ndarray:
    """Forward-only (causal) HMM filter — no look-ahead."""
    pi_arr = np.array(pi if pi is not None else HMM_T_pi) + 1e-12
    pi_arr /= pi_arr.sum()
    A_arr = np.array(A if A is not None else HMM_T_A)
    mu_arr = means if means is not None else HMM_T_means
    cv_arr = covs if covs is not None else HMM_T_covs

    n, K = len(Xz), len(mu_arr)
    logB = np.column_stack([_log_mvn(Xz, mu_arr[k], cv_arr[k])
                             for k in range(K)])
    alpha = pi_arr * np.exp(logB[0] - logB[0].max())
    alpha /= alpha.sum()
    probs = [alpha]
    for t in range(1, n):
        pred = alpha @ A_arr
        w = np.exp(logB[t] - logB[t].max())
        alpha = pred * w
        alpha /= alpha.sum()
        probs.append(alpha)
    return np.array(probs)


class _ARCH1:
    """ARCH(1) conditional variance with hard floor."""

    def __init__(self, omega: float = 5.0, alpha: float = 0.3,
                 r_min: float = 1.0) -> None:
        self.omega, self.alpha, self.r_min = omega, alpha, r_min

    def update(self, innov: float) -> float:
        return max(self.r_min, self.omega + self.alpha * innov ** 2)


def sr_kf_local_trend(
    y: np.ndarray, q_level: float = 0.8, q_trend: float = 0.02,
    r_init: float = 400.0, arch_omega: float = 5.0, arch_alpha: float = 0.3,
) -> Tuple[float, float]:
    """Square-root Kalman filter for a local-linear-trend on y.

    Uses QR-based state covariance factorisation (S) for numerical stability
    and an ARCH(1) measurement noise term to track heteroscedasticity.
    """
    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    H = np.array([[1.0, 0.0]])
    Q_sqrt = np.diag([np.sqrt(q_level), np.sqrt(q_trend)])
    x = np.array([y[0], 0.0])
    S = np.eye(2) * np.sqrt(r_init)
    arch = _ARCH1(arch_omega, arch_alpha)

    for t in range(len(y)):
        x = F @ x
        compound = np.vstack((S.T @ F.T, Q_sqrt))
        _, R_qr = np.linalg.qr(compound, mode="reduced")
        S = R_qr[:2, :2].T
        y_pred = (H @ x).item()
        innov = y[t] - y_pred
        R_t = arch.update(innov)
        f = S.T @ H.T
        S_s = np.sqrt((f.T @ f).item() + R_t)
        K = (S @ f).flatten() / S_s
        x = x + K * (innov / S_s)
        alpha = 1.0 / (S_s * (S_s + np.sqrt(R_t)))
        S = np.tril(S - alpha * (S @ f @ f.T))
    return float(x[0]), float(x[1])


def _prep_8d_from_daily(df: "pd.DataFrame") -> Optional["pd.DataFrame"]:
    """Construct the 8-D feature matrix used by the EV06b HMM."""
    df = df.sort_values("time").reset_index(drop=True).copy()
    df["wb"] = (df["precipitation_sum (mm)"]
                - df["et0_fao_evapotranspiration (mm)"])
    df["rh_mean"] = ((df["relative_humidity_2m_max (%)"]
                      + df["relative_humidity_2m_min (%)"]) / 2)
    win = 30
    df["rain_30d"]  = df["precipitation_sum (mm)"].rolling(win, min_periods=15).sum()
    df["wb_30d"]    = df["wb"].rolling(win, min_periods=15).sum()
    df["sm_30d"]    = (df["soil_moisture_0_to_7cm_mean (m³/m³)"]
                        .ffill().rolling(win, min_periods=15).mean())
    df["rh_30d"]    = df["rh_mean"].rolling(win, min_periods=15).mean()
    df["tcwv_30d"]  = df["tcwv"].ffill().rolling(win, min_periods=15).mean()
    df["dtr_30d"]   = df["dtr"].ffill().rolling(win, min_periods=15).mean()
    df["cloud_30d"] = df["cloud_mean"].ffill().rolling(win, min_periods=15).mean()
    df["smd_30d"]   = df["sm28_100"].ffill().rolling(win, min_periods=15).mean()
    need = ["rain_30d", "wb_30d", "sm_30d", "rh_30d",
            "tcwv_30d", "dtr_30d", "cloud_30d", "smd_30d"]
    df = df.dropna(subset=need).reset_index(drop=True)
    return df if len(df) else None


def classify_enso_phase(aso_mean: float) -> str:
    if aso_mean >= 0.5:
        return "El Niño"
    if aso_mean <= -0.5:
        return "La Niña"
    return "Netral"


SCENARIO_FOR_PHASE: Dict[str, str] = {
    "El Niño": "ELNINO", "La Niña": "LANINA", "Netral": "NETRAL",
}


def live_nowcast(
    meteo_csv: str = DEFAULT_DAILY_CSV_P1,
    meteo_csv2: str = DEFAULT_DAILY_CSV_P2,
    meteo_6h: str = DEFAULT_6H_CSV_P1,
    meteo_6h2: str = DEFAULT_6H_CSV_P2,
    meteo_hourly: str = DEFAULT_HOURLY_CSV_P1,
    meteo_hourly2: str = DEFAULT_HOURLY_CSV_P2,
    enso_csv: str = DEFAULT_ENSO_CSV,
    msla_csv: str = DEFAULT_MSLA_CSV,
) -> Optional[Dict]:
    """Execute the full nowcast pipeline; returns a dict or None on failure."""
    if not HAS_PANDAS:
        print("  [!] pandas not available — nowcast skipped.")
        return None

    df = load_interpolated_meteo(meteo_csv, meteo_csv2)
    if df is None:
        print("  [!] No daily meteorology file found — nowcast skipped.")
        return None

    p1_ok = find_data_file(meteo_csv) is not None
    p2_ok = find_data_file(meteo_csv2) is not None
    interp_mode = ("GIDW 2 stasiun (EV07)" if (p1_ok and p2_ok)
                   else ("stasiun P1 saja" if p1_ok else "stasiun P2 saja"))

    df6 = load_interpolated_6h(meteo_6h, meteo_6h2,
                                hourly_p1=meteo_hourly,
                                hourly_p2=meteo_hourly2)
    has_6h = df6 is not None and len(df6) > 0
    if has_6h:
        df = df.merge(df6, on="time", how="left")
    df = df.sort_values("time").reset_index(drop=True)

    df["wb"] = (df["precipitation_sum (mm)"]
                - df["et0_fao_evapotranspiration (mm)"])
    df["rh_mean"] = ((df["relative_humidity_2m_max (%)"]
                      + df["relative_humidity_2m_min (%)"]) / 2)
    win = 30
    df["rain_30d"] = df["precipitation_sum (mm)"].rolling(win, min_periods=15).sum()
    df["wb_30d"]   = df["wb"].rolling(win, min_periods=15).sum()
    df["sm_30d"]   = (df["soil_moisture_0_to_7cm_mean (m³/m³)"]
                       .ffill().rolling(win, min_periods=15).mean())
    df["rh_30d"]   = df["rh_mean"].rolling(win, min_periods=15).mean()

    # ── HMM filter: 8-D if we have 6-hour data, otherwise 4-D ───────────
    df_8d = _prep_8d_from_daily(df) if has_6h else None
    if df_8d is not None and len(df_8d) >= 60:
        tail = df_8d.tail(400).reset_index(drop=True)
        X = tail[["rain_30d", "wb_30d", "sm_30d", "rh_30d",
                  "tcwv_30d", "dtr_30d", "cloud_30d", "smd_30d"]].values
        Xz = (X - np.array(HMM_T8_mu)) / np.array(HMM_T8_sd)
        probs = hmm_causal_filter(Xz, pi=HMM_T8_pi, A=HMM_T8_A,
                                   means=HMM_T8_means, covs=HMM_T8_covs)
        hmm_mode = "8-D (EV06b: +TCWV+DTR+cloud+SM-dalam)"
        df_trend = df_8d
    else:
        df4 = df.dropna(subset=["rain_30d", "wb_30d", "sm_30d", "rh_30d"]
                         ).reset_index(drop=True)
        tail = df4.tail(400).reset_index(drop=True)
        X = tail[["rain_30d", "wb_30d", "sm_30d", "rh_30d"]].values
        Xz = (X - np.array(HMM_T_mu)) / np.array(HMM_T_sd)
        probs = hmm_causal_filter(Xz)
        hmm_mode = "4-D (legacy)"
        df_trend = df4

    last_probs = probs[-1]
    last_date = tail["time"].iloc[-1].date()

    y = (df_trend["wb_30d"].values[-730:]
         if len(df_trend) > 730 else df_trend["wb_30d"].values)
    level, trend = sr_kf_local_trend(y)

    out: Dict = {
        "last_date":          last_date,
        "state_probs":        last_probs,
        "dominant_state":     int(np.argmax(last_probs)),
        "level_wb30":         level,
        "trend_wb30_per_day": trend,
        "interp_mode":        interp_mode,
        "lat_target":         TARGET_LAT,
        "lon_target":         TARGET_LON,
        "data_start":         df["time"].iloc[0].date() if len(df) else None,
        "hmm_mode":           hmm_mode,
        "has_6h":             has_6h,
    }

    # ── ENSO SST index ──────────────────────────────────────────────────
    epath = find_data_file(enso_csv)
    if epath is not None:
        edf = pd.read_csv(epath)
        base = datetime(1978, 1, 1, 12, 0, 0)
        edf["date"] = edf["time"].apply(
            lambda d: base + timedelta(days=float(d)))
        edf["year"] = edf["date"].dt.year
        edf["month"] = edf["date"].dt.month
        latest_year = int(edf["year"].max())
        aso = edf[(edf["year"] == latest_year)
                  & edf["month"].isin([8, 9, 10])]["enso"]
        if len(aso):
            aso_mean = float(aso.mean())
            out["enso_year"] = latest_year
            out["enso_aso_mean_sofar"] = aso_mean
            out["enso_phase_sofar"] = classify_enso_phase(aso_mean)
        edf_sorted = edf.sort_values("date")
        out["enso_latest_value"] = float(edf_sorted["enso"].iloc[-1])
        out["enso_latest_date"] = edf_sorted["date"].iloc[-1].date()

    # ── MSLA SLA index (epoch 1950-01-01) + ARX 6-week forecast ─────────
    mpath = find_data_file(msla_csv)
    if mpath is not None:
        mdf = pd.read_csv(mpath)
        mbase = datetime(1950, 1, 1, 0, 0, 0)
        mdf["date"] = mdf["time"].apply(
            lambda d: mbase + timedelta(days=float(d)))
        mdf["year"] = mdf["date"].dt.year
        mdf["month"] = mdf["date"].dt.month
        mdf = mdf.sort_values("date").reset_index(drop=True)

        out["enso_sla_latest_value"] = float(mdf["enso"].iloc[-1])
        out["enso_sla_latest_date"] = mdf["date"].iloc[-1].date()
        out["enso_sla_phase"] = classify_enso_phase(out["enso_sla_latest_value"])

        latest_sla_year = int(mdf["year"].max())
        sla_aso = mdf[(mdf["year"] == latest_sla_year)
                      & mdf["month"].isin([8, 9, 10])]["enso"]
        if len(sla_aso):
            out["enso_sla_aso_mean"] = float(sla_aso.mean())
            out["enso_sla_year"] = latest_sla_year

        if epath is not None:
            merged = (edf[["date", "enso"]].rename(columns={"enso": "sst"})
                        .merge(mdf[["date", "enso"]].rename(columns={"enso": "sla"}),
                               on="date", how="inner")
                        .sort_values("date").reset_index(drop=True))
            if len(merged) > 30:
                s_arr = merged["sst"].values.astype(float)
                m_arr = merged["sla"].values.astype(float)
                lag_h, lag_f = 4, 6
                X_list, y_list = [], []
                for i in range(lag_h, len(merged) - lag_f):
                    feats = np.concatenate([s_arr[i - lag_h:i + 1],
                                            m_arr[i - lag_h:i + 1], [1.0]])
                    X_list.append(feats)
                    y_list.append(m_arr[i + lag_f])
                beta, *_ = np.linalg.lstsq(np.array(X_list),
                                            np.array(y_list), rcond=None)
                latest_feats = np.concatenate([s_arr[-(lag_h + 1):],
                                               m_arr[-(lag_h + 1):], [1.0]])
                pred = float(np.dot(latest_feats, beta))
                out["enso_sla_arx_6wk"] = pred
                out["enso_sla_arx_6wk_phase"] = classify_enso_phase(pred)

    # ── IOD: weekly preferred, monthly fallback ─────────────────────────
    iw = find_data_file(DEFAULT_IOD_WEEKLY)
    if iw is not None:
        rows: List[Tuple[date, float]] = []
        with open(iw, encoding="utf-8") as f:
            for ln in f:
                parts = ln.strip().split(",")
                if len(parts) < 3:
                    continue
                try:
                    d2 = datetime.strptime(parts[1], "%Y%m%d").date()
                    rows.append((d2, float(parts[2])))
                except ValueError:
                    continue
        if rows:
            rows.sort()
            rec = rows[-8:]
            v = sum(x[1] for x in rec) / len(rec)
            out["iod_value"] = v
            out["iod_phase"] = ("pIOD" if v >= 0.40 else
                                "nIOD" if v <= -0.40 else "NETRAL")
            out["iod_src"] = f"{len(rec)} pekan s.d. {rec[-1][0]}"

    if "iod_phase" not in out:
        im = find_data_file(DEFAULT_IOD_MONTHLY)
        if im is not None:
            with open(im, encoding="utf-8") as f:
                lines = [ln.split() for ln in f if ln.strip()]
            for p in reversed(lines[1:]):
                if len(p) < 13:
                    continue
                try:
                    vals = [float(x) for x in p[1:13]]
                except ValueError:
                    continue
                son = [x for x in (vals[8], vals[9], vals[10])
                       if abs(x - 99.90) > 1e-6]
                if len(son) < 2:
                    continue
                v = sum(son) / len(son)
                out["iod_value"] = v
                out["iod_phase"] = ("pIOD" if v >= 0.40 else
                                    "nIOD" if v <= -0.40 else "NETRAL")
                out["iod_src"] = f"SON {p[0]} (n={len(son)}/3)"
                break

    return out
    
    
# ══════════════════════════════════════════════════════════════════════════
# Section 13 · Presentation primitives
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
    """Render one or more wrapped lines inside the frame."""
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

def hbar(ch: str = "─") -> str:
    return ch * W

def thin_hbar(indent: int = 2) -> str:
    return " " * indent + "─" * (W - indent)

def sec_header(label: str, sub: str = "", dopy_range: str = "") -> None:
    right = f"[dopy: {dopy_range}]" if dopy_range else ""
    title = f"▌▌ {label.upper()}"
    if sub:
        title += f" — {sub}"
    gap = W - len(title) - len(right)
    print()
    if gap >= 1 or not right:
        print(title + (" " * max(1, gap)) + right if right else title)
    else:
        print(title[:W]); print(right.rjust(W))
    print(thin_hbar(0))

def wline(label: str, value: str, lw: int = 12, indent: int = 6) -> str:
    pre = " " * indent + f"{label:<{lw}}: "
    sub = " " * (indent + lw + 2)
    return textwrap.fill(value, width=W, initial_indent=pre, subsequent_indent=sub)

def wprint(label: str, value: str, lw: int = 12, indent: int = 6) -> None:
    print(wline(label, value, lw, indent))

def _wrap_ciri_line(raw: str, width: int) -> List[str]:
    """Wrap a CIRI line with hanging indent.

    Bullet lines (leading `•`) render as `• content…` on the first line
    and align continuation lines under the bullet content. Plain lines
    preserve leading whitespace as indent.
    """
    if not raw:
        return [""]
    stripped = raw.lstrip()
    if not stripped:
        return [""]
    leading = len(raw) - len(stripped)
    if stripped.startswith("•"):
        prefix = " " * leading + "• "
        content = stripped[1:].strip()
        return textwrap.wrap(
            content, width=width,
            initial_indent=prefix,
            subsequent_indent=" " * len(prefix),
        ) or [prefix.rstrip()]
    prefix = " " * leading
    return textwrap.wrap(
        stripped, width=width,
        initial_indent=prefix,
        subsequent_indent=prefix,
    ) or [prefix.rstrip()]

def print_data_attribution(detail: str = "ringkas") -> None:
    """Print the source-attribution block. detail: 'ringkas' | 'lengkap'."""
    print()
    print(box_top("ATRIBUSI SUMBER DATA"))
    print(box_row("Sumber ilmiah untuk seluruh data meteorologi, oseanografi, "
                  "dan iklim"))
    print(box_mid())
    kategori = (
        ("METEOROLOGI",   ("era5", "era5_land", "ecmwf_ifs", "open_meteo")),
        ("ENSO (Niño3.4)", ("aviso_duacs_sla", "noaa_oisst_sst")),
        ("IOD",           ("jma_iod", "bom_iod")),
        ("ASTRONOMI",     ("vsop87d", "iers2010", "iau2006_precession",
                            "hmnao_deltat", "sofa")),
    )
    for label, keys in kategori:
        print(box_row(""))
        print(box_row(f"  ── {label} ─────────────────────────────────"))
        for k in keys:
            a = DATA_ATTRIBUTION[k]
            print(box_row(""))
            print(box_row(f"  ▸ {a['nama']}"))
            for ln in textwrap.wrap(a["deskripsi"], width=W - 8,
                                    initial_indent="    ",
                                    subsequent_indent="    "):
                print(box_row(ln))
            print(box_row(f"    Institusi : {a['institusi']}"))
            print(box_row(f"    Sitasi    : {a['sitasi']}"))
            if a.get("doi"):
                print(box_row(f"    DOI       : https://doi.org/{a['doi']}"))
            if detail == "lengkap":
                if a.get("input"):
                    for ln in textwrap.wrap(a["input"], width=W - 22,
                                            initial_indent="    Input     : ",
                                            subsequent_indent="                "):
                        print(box_row(ln))
                if a.get("catatan"):
                    for ln in textwrap.wrap(a["catatan"], width=W - 22,
                                            initial_indent="    Catatan   : ",
                                            subsequent_indent="                "):
                        print(box_row(ln))
                if a.get("referensi"):
                    print(box_row(f"    Referensi : {a['referensi']}"))
            print(box_row(f"    Lisensi   : {a['lisensi']}"))
    print(box_bot()); print()


# ══════════════════════════════════════════════════════════════════════════
# Section 14 · Climate blocks
# ══════════════════════════════════════════════════════════════════════════

def _print_mangsa_block(
    dopy_s: float, dopy_e: float,
    indent: int = 6,
    enso_phase: str = "NETRAL",
    iod_phase: str = "NETRAL",
) -> None:
    """Unified daily + 6H climatology printer for a dopy span."""
    m, m6h = meteo_for_dopy_range(dopy_s, dopy_e, enso_phase, iod_phase)
    if m is None:
        return
    hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad = m
    pad = " " * indent
    wb_str = f"{wb:+.2f} mm/hari ({'defisit' if wb < 0 else 'surplus'})"
    print(f"{pad}Curah hujan : {hj:>4} mm/musim · {hj_d:.1f} mm/hari · {hhr} hari hujan")
    print(f"{pad}Suhu udara  : {_fmt_suhu(tx, tn, dopy_s, dopy_e)}")
    print(f"{pad}Kelembaban  : RH {rh:.1f}% · SM {sm:.3f} m³/m³ · ET₀ {et0:.2f} mm/hari")
    print(f"{pad}Neraca air  : {wb_str}")
    print(f"{pad}Radiasi/Angin: {rad:.1f} MJ/m² · Angin maks {angin:.1f} km/j")
    if m6h is not None:
        vpd, tcwv, cld, cld_a, sun_h, sm_sh, sm_dp, sT_sh, sT_dp = m6h
        print(f"{pad}[6H] VPD {vpd:.2f} kPa · TCWV {tcwv:.1f} kg/m²")
        print(f"{pad}[6H] Cloud {cld:.0f}% (aft {cld_a:.0f}%) · Sun {sun_h:.1f} h/hari")
        print(f"{pad}[6H] SM 0-7cm {sm_sh:.3f} · SM 28-100cm {sm_dp:.3f} m³/m³")
        print(f"{pad}[6H] sT 0-7cm {sT_sh:.1f}°C · sT 100-255cm {sT_dp:.1f}°C")


def _print_musim_block(
    musim: str, dopy_s: float, dopy_e: float,
    indent: int = 2,
    enso_phase: str = "NETRAL", iod_phase: str = "NETRAL",
) -> None:
    """Unified wet-season climatology printer."""
    m, m6h = meteo_for_dopy_range(dopy_s, dopy_e, enso_phase, iod_phase)
    if m is None:
        return
    hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad = m
    dur = int(round(dopy_e - dopy_s + 1))
    pad = " " * indent
    wb_str = f"{wb:+.2f} mm/hari ({'defisit' if wb < 0 else 'surplus'})"
    print(f"{pad}Curah hujan : {hj:>5} mm/musim · {hj_d:.1f} mm/hari · ET₀ {et0:.2f} mm/hari")
    print(f"{pad}Neraca air  : {wb_str} · SM {sm:.3f} m³/m³")
    print(f"{pad}Suhu udara  : {_fmt_suhu(tx, tn, dopy_s, dopy_e)} · RH {rh:.1f}%")
    print(f"{pad}Rad./Angin  : {rad:.1f} MJ/m² · Angin {angin:.1f} km/j · Durasi {dur} hari")
    if m6h is not None:
        vpd, tcwv, cld, cld_a, sun_h = m6h[:5]
        print(f"{pad}[6H] VPD {vpd:.3f} kPa · TCWV {tcwv:.1f} kg/m²")
        print(f"{pad}[6H] Cloud {cld:.0f}% · Sun {sun_h:.1f} h/hari")


# ══════════════════════════════════════════════════════════════════════════
# Section 15 · Report generators
# ══════════════════════════════════════════════════════════════════════════

def print_astro_calib_table() -> None:
    print()
    print(box_top())
    print(box_row("KALIBRASI ASTRONOMIS — EV09"))
    print(box_row("JRC_Ephemeris · VSOP87D · IERS 2010 · ΔT HMNAO"))
    print(box_row("Lokasi: −7.5220°LS, 112.5661°BT, 28 m · Rata-rata 2020–2029"))
    print(box_mid())
    print(box_row("Peristiwa            Tgl    dopy  σ  Δ vs trad   Mangsa"))
    print(box_bot()); print()

    rows = (
        ("solstis_juni",       "Solstis Juni",             "1 Kasa"),
        ("solstis_des",        "Solstis Desember",          "6 Kanem†"),
        ("equinox_maret",      "Ekuinoks Maret",            "8/9 Kawolu†"),
        ("equinox_sept",       "Ekuinoks September",        "4 Kapat†"),
        ("zenith_I_okt",       "Zenith Matahari I",         "5 Kalima"),
        ("zenith_II_mar",      "Zenith Matahari II",        "8 Kawolu†"),
        ("orion_helrise",      "Orion Heliacal Rise",       "1 Kasa"),
        ("orion_evening_rise", "Orion Acronychal Rise",     "6 Kanem"),
        ("orion_evening_culm", "Orion Kulminasi Senja",     "8 Kawolu†"),
        ("orion_midnight_culm", "Orion Kulminasi Tngah Mlm", "6 Kanem"),
        ("orion_acron_set",    "Orion Acronychal Set",      "12 Sada"),
    )
    for key, label, mangsa in rows:
        ev = ASTRO_CALIB.get(key)
        if ev is None:
            continue
        tgl = f"{ev.mean_day:02d} {MONTH_SHORT[ev.mean_month]}"
        marker = "" if ev.same_event else "*"
        print(f"  {label:<22} {tgl:>6}  {ev.mean_dopy:>7.1f}  "
              f"{ev.std_dopy:.2f}  {ev.delta:>+6.1f}  {mangsa}{marker}"[:W])

    print()
    for ln in textwrap.wrap("† = berdasarkan skenario R30/R10. "
                            "* = definisi tradisional berbeda.",
                            width=W, initial_indent="  ",
                            subsequent_indent="    "):
        print(ln)
    print(); print(thin_hbar(2))
    print("  Catatan per peristiwa:"); print()
    for key, label, _ in rows:
        ev = ASTRO_CALIB.get(key)
        if ev is None or not ev.catatan:
            continue
        wprint(label[:20], ev.catatan, lw=22, indent=2); print()


def print_calendar(
    cal: Sequence[MangsaEntry], judul: str,
    scenario_key: str = DEFAULT_SCENARIO,
    show_meteo: bool = True, show_astro: bool = True,
) -> None:
    scenario = CALIB_SCENARIOS[scenario_key]

    print()
    print(box_top())
    print(box_row(judul))
    if show_meteo:
        print(box_row("ERA5/ERA5-Land (ECMWF/C3S) · IFS HRES 9km (ECMWF)"))
        print(box_row("−7.5220°LS, 112.5661°BT, 28 m · IDW 2 stasiun (P1+P2)"))
        print(box_row(f"Skenario musim: {scenario_key} — {scenario.label}"))
        clim_note = (
            f"Klimatologi: interpolasi dopy R30 + koreksi Δ{scenario_key}"
            if scenario.enso_phase != "NETRAL"
            else "Klimatologi: interpolasi dopy R30 (1996–2025)"
        )
        print(box_row(clim_note))
        if scenario.iod_phase in ("pIOD", "nIOD"):
            synergy = ("0.50 sinergi ENSO–IOD"
                       if scenario.enso_phase != "NETRAL"
                       else "0.30 standalone")
            print(box_row(f"Koreksi IOD: {scenario.iod_phase} "
                          f"(mangsa 3–5, bobot {synergy})"))
        print(box_row("Tx̄/Tn̄ = rata² T maks/min harian · (x) = ekstrem absolut"))
    if show_astro:
        print(box_row("Astro: VSOP87D+IERS2010 · JRC_Ephemeris · 2020–2029"))
    print(box_bot())

    if show_meteo:
        ms = scenario.musim_start
        ms_next = {
            "Katiga":   ms["Labuh"],
            "Labuh":    ms["Rendheng"],
            "Rendheng": ms["Mareng"],
            "Mareng":   365 + ms["Katiga"],
        }
    else:
        ms = ORIG_MUSIM_START
        ms_next = ORIG_MUSIM_START_NEXT

    for musim in MUSIM_ORDER:
        ds, de = float(ms[musim]), float(ms_next[musim] - 1)
        sec_header(f"MUSIM {musim}", MUSIM_DESKRIPSI[musim],
                   dopy_range=f"{ds:.0f}–{de:.0f}")

        if show_meteo:
            _print_musim_block(musim, ds, de, indent=2,
                               enso_phase=scenario.enso_phase,
                               iod_phase=scenario.iod_phase)
            print()

        hdr = (f"{'No':>3}  {'Nama':<10}  {'Mulai':<13} "
               f"{'Selesai':<13} {'Dur (hr)':>8}")
        print(f"  {hdr}")
        print(f"  {'─' * len(hdr)}")

        for m in cal:
            if m.musim != musim:
                continue
            print(f"  {m.no:>3}  {m.nama:<10}  {fmt(m.mulai):<13} "
                  f"{fmt(m.akhir):<13} {m.durasi:>8}")
            if show_meteo:
                _print_mangsa_block(m.dopy_start, m.dopy_end, indent=7,
                                    enso_phase=scenario.enso_phase,
                                    iod_phase=scenario.iod_phase)
            print(textwrap.fill(m.ciri, width=W,
                                initial_indent="       Ciri       : ",
                                subsequent_indent=" " * 19))
            if m.candra:
                print(textwrap.fill(m.candra, width=W,
                                    initial_indent="       Candra     : ",
                                    subsequent_indent=" " * 19))
            print()
    print()


def print_mangsa_today(
    tanggal: date, scenario_key: str = DEFAULT_SCENARIO
) -> None:
    pyear, dopy = get_pranatamangsa_year_and_dopy(tanggal)
    scenario = CALIB_SCENARIOS[scenario_key]
    print()
    print(box_top())
    print(box_row(f"MANGSA UNTUK TANGGAL: {fmt(tanggal)}"))
    print(box_row(f"Tahun-Pranata: {pyear}/{pyear + 1} · Hari ke-{dopy + 1} "
                  f"(dopy={dopy})"))
    print(box_mid())

    trad = get_mangsa_by_date(tanggal, "tradisional")
    kal  = get_mangsa_by_date(tanggal, "terkalibrasi", scenario_key)

    if trad is not None:
        print(box_row(""))
        print(box_row("[ TRADISIONAL — Reformasi Paku Buwana VII, 1855 ]"))
        print(box_row(f"  Mangsa ke-{trad.no}: {trad.nama.upper()} · "
                      f"Musim {trad.musim}"))
        print(box_row(f"  Periode: {fmt(trad.mulai)} — {fmt(trad.akhir)} "
                      f"({trad.durasi} hari)"))
        first = True
        for raw in trad.ciri.split("\n"):
            for ln in _wrap_ciri_line(raw, W - 14):
                print(box_row(f"  Ciri: {ln}" if first else f"        {ln}"))
                first = False
        if trad.candra:
            print(box_row(""))
            print(box_row("  Candraning Măngsa (tradisional):"))
            for ln in textwrap.wrap(trad.candra, width=W - 12,
                                    initial_indent="      ",
                                    subsequent_indent="      "):
                print(box_row(ln))

    print(box_mid())
    if kal is not None:
        print(box_row(""))
        print(box_row(f"[ TERKALIBRASI — {scenario.label} ]"))
        print(box_row(f"  Mangsa ke-{kal.no}: {kal.nama.upper()} · "
                      f"Musim {kal.musim}"))
        print(box_row(f"  Periode: {fmt(kal.mulai)} — {fmt(kal.akhir)} "
                      f"({kal.durasi} hari)"))
        if trad is not None and kal.no != trad.no:
            print(box_row(f"  >> BERBEDA dari tradisional (tradisional: "
                          f"mangsa {trad.no} {trad.nama})"))
        elif trad is not None:
            sel = (kal.mulai - trad.mulai).days
            sgn = "lebih awal" if sel < 0 else "lebih lambat"
            print(box_row(f"  Awal mangsa ini bergeser {sel:+d} hari "
                          f"({abs(sel)} hari {sgn}) vs. tradisional"))

        for ln in textwrap.wrap(kal.ciri, width=W - 12,
                                initial_indent="  Ciri: ",
                                subsequent_indent="        "):
            print(box_row(ln))

        print(box_mid()); print(box_row(""))
        src = f"R30 1996–2025 · skenario {scenario_key}"
        if scenario.iod_phase in ("pIOD", "nIOD"):
            src += f" · IOD {scenario.iod_phase}"
        print(box_row(f"  Klimatologi (sumber {src}):"))

        m, m6h = meteo_for_dopy_range(kal.dopy_start, kal.dopy_end,
                                       scenario.enso_phase, scenario.iod_phase)
        if m is not None:
            hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad = m
            wb_str = "defisit" if wb < 0 else "surplus"
            print(box_row(f"  Curah hujan : {hj} mm/musim · {hj_d:.1f} mm/hari "
                          f"· {hhr} hari hujan"))
            print(box_row(f"  Suhu udara  : {_fmt_suhu(tx, tn, kal.dopy_start, kal.dopy_end)}"))
            print(box_row(f"  Kelembaban  : RH {rh:.1f}% · SM {sm:.3f} m³/m³ · "
                          f"ET₀ {et0:.2f} mm/hari"))
            print(box_row(f"  Neraca air  : P−ET₀ {wb:+.2f} mm/hari ({wb_str}) "
                          f"· Rad {rad:.1f} MJ/m²"))
        if m6h is not None:
            vpd, tcwv, cld, cld_a, sun_h, sm_sh, sm_dp, sT_sh, sT_dp = m6h
            print(box_row(f"  [6H] VPD {vpd:.2f} kPa · TCWV {tcwv:.1f} kg/m²"))
            print(box_row(f"  [6H] Cloud {cld:.0f}% (aft {cld_a:.0f}%) · "
                          f"Sun {sun_h:.1f} h/hari"))
            print(box_row(f"  [6H] SM 0-7cm {sm_sh:.3f} · "
                          f"SM 28-100cm {sm_dp:.3f} m³/m³"))

        print(box_mid()); print(box_row(""))
        print(box_row("  Penanda Astronomis (VSOP87D, rata-rata 2020–2029):"))
        ev_keys = astro_events_in_range(kal.dopy_start, kal.dopy_end)
        if not ev_keys:
            print(box_row("  (tidak ada penanda astronomis khusus)"))
        for ev_key in ev_keys:
            ev = ASTRO_CALIB.get(ev_key)
            if ev is None:
                continue
            tgl_str = f"{ev.mean_day:02d} {MONTH_SHORT[ev.mean_month]}"
            print(box_row(f"  {ev.label}"))
            combined = f"→ Tgl rata-rata: {tgl_str} | {astro_delta_str(ev_key)}"
            for ln in textwrap.wrap(combined, width=W - 12,
                                    initial_indent="    ",
                                    subsequent_indent="      "):
                print(box_row(ln))

    print(box_bot()); print()


def print_perbandingan(pyear: int) -> None:
    trad_cal = build_calendar_tradisional(pyear)
    scn_keys = list(CALIB_SCENARIOS)
    print(); print(box_top())
    print(box_row(f"PERBANDINGAN SKENARIO — Tahun-Pranata {pyear}/{pyear + 1}"))
    print(box_row("Angka = selisih hari awal mangsa vs. Tradisional (– lebih awal)"))
    print(box_bot()); print()

    hdr = f"  {'No':>2}  {'Nama':<10} {'Tradisional':>12}"
    for k in scn_keys:
        hdr += f"  {k:>6}"
    print(hdr[:W]); print(thin_hbar(2))

    cal_by_scn = {k: build_calendar_terkalibrasi(pyear, k) for k in scn_keys}
    for td in trad_cal:
        row = f"  {td.no:>2}  {td.nama:<10} {fmt(td.mulai):>12}"
        for k in scn_keys:
            m_cal = next(x for x in cal_by_scn[k] if x.no == td.no)
            row += f"  {(m_cal.mulai - td.mulai).days:>+6}"
        print(row[:W])

    print(); print(thin_hbar(2))
    print("  Legenda skenario:")
    for k, v in CALIB_SCENARIOS.items():
        print(); print(f"  {k:<7}: {v.label}")
        wprint("Catatan", v.catatan, lw=7, indent=10)
    print()


def print_durasi_musim() -> None:
    print(); print(box_top())
    print(box_row("DURASI TIAP MUSIM (hari) — Tradisional vs Kalibrasi"))
    print(box_bot()); print()

    col_w = 11
    hdr = f"  {'Skenario':<13}" + "".join(f"{m:>{col_w}}" for m in MUSIM_ORDER) \
          + f"  {'Total':>6}"
    print(hdr[:W]); print(thin_hbar(2))

    o, on = ORIG_MUSIM_START, ORIG_MUSIM_START_NEXT
    durs = [on[mu] - o[mu] for mu in MUSIM_ORDER]
    print(f"  {'Tradisional':<13}" + "".join(f"{d:>{col_w}}" for d in durs)
          + f"  {sum(durs):>6}")

    for key, scn in CALIB_SCENARIOS.items():
        s = scn.musim_start
        sn = {"Katiga": s["Labuh"], "Labuh": s["Rendheng"],
              "Rendheng": s["Mareng"], "Mareng": 365 + s["Katiga"]}
        durs = [sn[mu] - s[mu] for mu in MUSIM_ORDER]
        print(f"  {key:<13}" + "".join(f"{d:>{col_w}}" for d in durs)
              + f"  {sum(durs):>6}")

    print(); print(thin_hbar(2)); print()
    print("  Klimatologi tiap musim — Normal Iklim R30 (1996–2025):")
    for mu in MUSIM_ORDER:
        print(f"\n  ▸ {mu.upper()} — {MUSIM_DESKRIPSI[mu]}")
        ds, de = R30_MUSIM_DOPY[mu]
        _print_musim_block(mu, ds, de, indent=4)
    print()


def print_klimatologi_bulanan() -> None:
    print(); print(box_top())
    print(box_row("KLIMATOLOGI BULANAN — Normal Iklim R30 (1996–2025)"))
    print(box_row("ERA5/Land-IFSHRES · −7.522°LS 112.566°BT · 28 m [IDW 2 stasiun]"))
    print(box_mid())
    print(box_row("Satuan: mm/bln = milimeter per bulan · mm/hr = mm/hari"))
    print(box_row("        MJ/m² = megajoule per meter² · km/j = km/jam"))
    print(box_row("Tx/Tn = rata² suhu maks/min harian"))
    print(box_bot()); print()

    params = (
        ("Hujan total (mm/bln)", 0, "{:>6.0f}"),
        ("Hujan (mm/hr)",        1, "{:>6.1f}"),
        ("ET₀ (mm/hr)",          2, "{:>6.2f}"),
        ("P−ET₀ (mm/hr)",        3, "{:>+6.1f}"),
        ("SM (m³/m³)",           4, "{:>6.3f}"),
        ("RH (%)",               5, "{:>6.1f}"),
        ("Tx (°C)",              6, "{:>6.1f}"),
        ("Tn (°C)",              7, "{:>6.1f}"),
        ("Angin (km/j)",         8, "{:>6.1f}"),
        ("Radiasi (MJ/m²)",      9, "{:>6.1f}"),
    )
    for _, bulan_list in ((1, range(1, 7)), (7, range(7, 13))):
        hdr = f"  {'Parameter':<20}" + "".join(f"{MONTH_SHORT[b]:>7}"
                                                for b in bulan_list)
        print(hdr[:W]); print(thin_hbar(2))
        for label, idx, fstr in params:
            row = f"  {label:<20}" + "".join(fstr.format(METEO_BULANAN[b][idx])
                                              for b in bulan_list)
            print(row[:W])
        print()

    print(thin_hbar(0)); print()
    print(f"  {'RINGKASAN PER MUSIM':^{W - 2}}")
    print(f"  {'(Normal Iklim R30 · rata-rata harian kecuali total)':^{W - 2}}")
    print()

    mus_params = (
        ("Hujan total (mm)", 1, "{:>10.0f}"),
        ("Hujan (mm/hr)",    2, "{:>10.1f}"),
        ("ET₀ (mm/hr)",      3, "{:>10.2f}"),
        ("P−ET₀ (mm/hr)",    4, "{:>+10.2f}"),
        ("SM (m³/m³)",       5, "{:>10.3f}"),
        ("RH (%)",           6, "{:>10.1f}"),
        ("Tx (°C)",          7, "{:>10.1f}"),
        ("Tn (°C)",          8, "{:>10.1f}"),
        ("Angin (km/j)",     9, "{:>10.1f}"),
        ("Radiasi (MJ/m²)", 10, "{:>10.1f}"),
        ("Durasi (hari)",    0, "{:>10.0f}"),
    )
    col_w = 10
    hdr = f"  {'Parameter':<20}" + "".join(f"{m:>{col_w}}" for m in MUSIM_ORDER)
    print(hdr[:W]); print(thin_hbar(2))
    for label, idx, fstr in mus_params:
        row = f"  {label:<20}" + "".join(fstr.format(METEO_MUSIM[mu][idx])
                                          for mu in MUSIM_ORDER)
        print(row[:W])
    print(); print(thin_hbar(0)); print()

    print(f"  {'RINGKASAN 6H PER MUSIM (EV09)':^{W - 2}}")
    print(f"  {'Nilai = rata-rata musiman (R30 1996–2025, IDW P1+P2)':^{W - 2}}")
    print()
    col_w = 11
    hdr = f"  {'Parameter':<22}" + "".join(f"{m:>{col_w}}" for m in MUSIM_ORDER)
    print(hdr[:W]); print(thin_hbar(2))
    for lbl, idx, fstr in (("VPD (kPa)", 0, "{:>11.3f}"),
                            ("TCWV (kg/m²)", 1, "{:>11.1f}"),
                            ("Cloud (%)", 2, "{:>11.0f}"),
                            ("Sunshine (h/d)", 3, "{:>11.1f}")):
        row = f"  {lbl:<22}" + "".join(fstr.format(METEO_MUSIM_6H[mu][idx])
                                        for mu in MUSIM_ORDER)
        print(row[:W])
    print(); print(thin_hbar(0)); print()


def print_live_nowcast() -> None:
    print(); print(box_top())
    print(box_row("NOWCAST LANGSUNG — Analisis Iklim Real-Time"))
    print(box_row("HMM 8-D (EV09) + SR-EKF Level/Tren (ARCH(1))"))
    print(box_bot())

    res = live_nowcast()
    if res is None:
        return

    print()
    print(f"  Titik target               : "
          f"{abs(res.get('lat_target', TARGET_LAT)):.4f}°LS, "
          f"{res.get('lon_target', TARGET_LON):.4f}°BT")
    print(f"  Mode data                  : {res.get('interp_mode', '-')}")
    print(f"  Mode HMM                   : {res.get('hmm_mode', '-')}")
    print(f"  Data 6-jam tersedia        : "
          f"{'Ya' if res.get('has_6h') else 'Tidak (fallback 4-D)'}")
    if res.get("data_start"):
        print(f"  Rentang data               : {res['data_start']} s.d. "
              f"{fmt(res['last_date'])}")
    else:
        print(f"  Data meteorologi terakhir  : {fmt(res['last_date'])}")
    print(); print(thin_hbar(2))
    print("  Probabilitas rejim iklim (HMM forward/causal, tanpa look-ahead):")
    print(thin_hbar(2))
    for k in range(4):
        p = res["state_probs"][k]
        print(f"  State {k}  {p * 100:5.1f}%  {'█' * int(round(p * 30)):<32}")
        print(f"           {HMM_T_STATE[k]}")
    dom = res["dominant_state"]
    print(); print(f"  >> Rejim dominan saat ini: State {dom} — "
                   f"{HMM_T_STATE[dom]}")

    print(); print(thin_hbar(2))
    print("  SR-EKF — Neraca air P−ET₀ 30-hari (level & tren ter-filter):")
    print(thin_hbar(2))
    wb, trnd = res["level_wb30"], res["trend_wb30_per_day"]
    arah = "→ menuju lebih basah" if trnd > 0 else "→ menuju lebih kering"
    print(f"  Level saat ini  : {wb:+.1f} mm / 30 hari")
    print(f"  Tren harian     : {trnd:+.3f} mm/hari {arah}")

    if "enso_phase_sofar" in res or "enso_sla_latest_value" in res:
        print(); print(thin_hbar(2))
        print(f"  Status ENSO — Niño3.4 (data s.d. {fmt(res['enso_latest_date'])}):")
        print(thin_hbar(2))
        if "enso_phase_sofar" in res:
            print(f"  [SST]  ASO {res['enso_year']}   : "
                  f"{res['enso_aso_mean_sofar']:+.2f}  →  "
                  f"{res['enso_phase_sofar']}")
            print(f"  [SST]  Terkini        : {res['enso_latest_value']:+.2f}")
        if "enso_sla_latest_value" in res:
            print()
            print(f"  [SLA]  Terkini        : "
                  f"{res['enso_sla_latest_value']:+.2f}  →  "
                  f"{res['enso_sla_phase']} "
                  f"(s.d. {fmt(res['enso_sla_latest_date'])})")
            if "enso_sla_aso_mean" in res:
                print(f"  [SLA]  ASO {res['enso_sla_year']}   : "
                      f"{res['enso_sla_aso_mean']:+.2f}")
            if "enso_sla_arx_6wk" in res:
                print(f"  [ARX]  Prakiraan +6 minggu : "
                      f"{res['enso_sla_arx_6wk']:+.2f}  →  "
                      f"{res['enso_sla_arx_6wk_phase']}")
        if ("enso_latest_value" in res and "enso_sla_latest_value" in res):
            sst_v = res["enso_latest_value"]
            sla_v = res["enso_sla_latest_value"]
            if classify_enso_phase(sst_v) != classify_enso_phase(sla_v):
                print()
                print(f"  ⚠ Divergensi SST ({classify_enso_phase(sst_v)}) ↔ "
                      f"SLA ({classify_enso_phase(sla_v)}) — pantau 4–6 minggu.")
        phase = res.get("enso_phase_sofar", res.get("enso_sla_phase", "Netral"))
        scn = SCENARIO_FOR_PHASE.get(phase)
        if scn:
            print(); print(f"  >> Rekomendasi skenario: '{scn}'")
            wprint("Catatan", CALIB_SCENARIOS[scn].catatan, lw=7, indent=5)

    if "iod_phase" in res:
        print(); print(thin_hbar(2))
        print("  Status IOD (Dipole Mode Index):")
        print(thin_hbar(2))
        print(f"  Fase   : {res['iod_phase']}  (DMI {res['iod_value']:+.2f})")
        print(f"  Sumber : {res['iod_src']}")
        enso_ph = res.get("enso_phase_sofar", res.get("enso_sla_phase", "Netral"))
        iod_ph = res["iod_phase"]
        if ((enso_ph == "El Niño" and iod_ph == "pIOD") or
                (enso_ph == "La Niña" and iod_ph == "nIOD")):
            print("  ⚑ Sinergi ENSO–IOD → bobot koreksi IOD 0.50")
        elif iod_ph in ("pIOD", "nIOD"):
            print("  · IOD standalone   → bobot koreksi IOD 0.30")

    print(); print(thin_hbar(2))
    print("  Sumber data:")
    print(thin_hbar(2))
    for ln in (
        "SLA  : AVISO/DUACS (CNES/CLS) — DOI 10.24400/527896/A01-2025.008",
        "SST  : NOAA OISST v2.1 — DOI 10.1175/JCLI-D-20-0166.1",
        "IOD  : JMA (DMI) — Saji et al. (1999), Nature 401:360",
        "Met  : ERA5/ERA5-Land (ECMWF/C3S) + IFS HRES 9km (ECMWF)",
        "Astro: VSOP87D (IMCCE) + IERS 2010 + HMNAO ΔT",
    ):
        print(f"  {ln}")
    print()


# ══════════════════════════════════════════════════════════════════════════
# Section 16 · CLI
# ══════════════════════════════════════════════════════════════════════════

MENU_ITEMS = (
    "  1 › Kalender Tradisional (Paku Buwana VII, 1855)",
    "  2 › Kalender Terkalibrasi (meteorologi + astro)",
    "  3 › Cek Mangsa Hari Ini / Tanggal Tertentu",
    "  4 › Tabel Perbandingan Skenario (selisih hari)",
    "  5 › Durasi Tiap Musim per Skenario",
    "  6 › Klimatologi Bulanan & Ringkasan Per-Musim",
    "  7 › Nowcast Langsung (HMM 8-D, real-time)",
    "  8 › Tabel Kalibrasi Astronomis",
    "  9 › Atribusi Sumber Data (sitasi ilmiah)",
    "  0 › Keluar",
)


def _ask_int(prompt: str, default: Optional[int] = None) -> Optional[int]:
    try:
        s = input(prompt).strip()
        return default if not s and default is not None else int(s)
    except (ValueError, EOFError):
        return default


def _ask_scenario() -> str:
    keys = ", ".join(CALIB_SCENARIOS)
    print(f"\n  Skenario tersedia: {keys}")
    s = input(f"  Pilih skenario [{DEFAULT_SCENARIO}]: ").strip().upper()
    return s if s in CALIB_SCENARIOS else DEFAULT_SCENARIO


def show_menu() -> None:
    print(); print(box_top("PRANATA MANGSA — EV09 GIDW+METEO(DAILY+6H)+ENSO+IOD+ASTRO"))
    print(box_row("−7.52S112.56E28m · ERA5/Land IFS HRES 1940–2026 · ENSO 1993–2026"))
    print(box_row("IOD: DMI 1950–2025 · mangsa 3–5 · bobot 0.30/0.50"))
    print(box_row("HMM 8-D (EV06b) · VSOP87D + IERS2010 · JRC_Ephemeris 2020–2029"))
    print(box_mid())
    for item in MENU_ITEMS:
        print(box_row(item))
    print(box_bot())


def laporan_singkat() -> None:
    today = date.today()
    print_mangsa_today(today, DEFAULT_SCENARIO)
    any_meteo = any(find_data_file(p) for p in (
        DEFAULT_DAILY_CSV_P1, DEFAULT_DAILY_CSV_P2,
        DEFAULT_6H_CSV_P1, DEFAULT_6H_CSV_P2,
        DEFAULT_HOURLY_CSV_P1, DEFAULT_HOURLY_CSV_P2,
    ))
    if any_meteo:
        print_live_nowcast()


def main_loop() -> None:
    while True:
        show_menu()
        pilihan = input("  Pilih menu (0–9): ").strip()

        if pilihan == "0":
            print(); print(box_top())
            print(box_row("Terima kasih. Sampai jumpa! — Pranata Mangsa EV09"))
            print(box_bot()); print()
            break

        elif pilihan == "1":
            tahun = _ask_int("  Tahun Gregorian (YYYY): ", date.today().year)
            if tahun is not None:
                print_calendar(build_calendar_tradisional(tahun),
                               f"KALENDER TRADISIONAL — TAHUN {tahun}",
                               show_meteo=False, show_astro=False)

        elif pilihan == "2":
            default_py = get_pranatamangsa_year_and_dopy(date.today())[0]
            tahun = _ask_int(f"  Tahun-pranata mulai (YYYY) [{default_py}]: ",
                             default_py)
            scn = _ask_scenario()
            if tahun is not None:
                print_calendar(
                    build_calendar_terkalibrasi(tahun, scn),
                    f"KALENDER TERKALIBRASI {tahun}/{tahun + 1}",
                    scenario_key=scn, show_meteo=True, show_astro=True,
                )

        elif pilihan == "3":
            s = input("  Tanggal (YYYY-MM-DD) [kosong = hari ini]: ").strip()
            try:
                tgl = date.today() if not s else date(*map(int, s.split("-")))
            except ValueError:
                print("  Format tanggal tidak valid.")
                continue
            print_mangsa_today(tgl, _ask_scenario())

        elif pilihan == "4":
            default_py = get_pranatamangsa_year_and_dopy(date.today())[0]
            tahun = _ask_int(f"  Tahun-pranata mulai (YYYY) [{default_py}]: ",
                             default_py)
            if tahun is not None:
                print_perbandingan(tahun)

        elif pilihan == "5":
            print_durasi_musim()
        elif pilihan == "6":
            print_klimatologi_bulanan()
        elif pilihan == "7":
            print_live_nowcast()
        elif pilihan == "8":
            print_astro_calib_table()
        elif pilihan == "9":
            print_data_attribution(detail="lengkap")
        else:
            print("\n  Pilihan tidak valid. Masukkan angka 0–9.")
            input("\n  Tekan Enter untuk melanjutkan...")
            continue

        input("\n  Tekan Enter untuk kembali ke menu...")


def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="pranatamangsa",
        description="Calibrated Pranata Mangsa calendar (EV09).",
    )
    ap.add_argument("--report", action="store_true",
                    help="Print today's mangsa and, if data available, nowcast.")
    ap.add_argument("--astro", action="store_true",
                    help="Print only the astronomical calibration table.")
    ap.add_argument("--attribution", action="store_true",
                    help="Print only the data attribution block.")
    ap.add_argument("--scenario", choices=list(CALIB_SCENARIOS),
                    default=DEFAULT_SCENARIO,
                    help=f"Scenario key (default: {DEFAULT_SCENARIO}).")
    ap.add_argument("--date", dest="iso_date", metavar="YYYY-MM-DD",
                    help="Query a specific date (implies --report-like output).")
    return ap


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_argparser().parse_args(argv)

    if args.iso_date:                  
        try:
            d = date.fromisoformat(args.iso_date)
        except ValueError:
            print(f"Invalid --date: {args.iso_date}", file=sys.stderr)
            return 2
        print_mangsa_today(d, args.scenario)
        return 0
    if args.report:
        laporan_singkat(); return 0
    if args.astro:
        print_astro_calib_table(); return 0
    if args.attribution:
        print_data_attribution(detail="lengkap"); return 0

    main_loop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Program dihentikan. Sampai jumpa!")
        sys.exit(0)    