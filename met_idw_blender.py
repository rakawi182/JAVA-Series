#!/usr/bin/env python3
"""
met_idw_blender.py
==================
Advanced Gradient-Enhanced IDW Meteorological Blending Module
Jolotundo Research Observatory • ASTERID Project

Tujuan
------
Memadukan (blend) dua sel grid Open-Meteo ke satu titik target menggunakan
Gradient-Enhanced Inverse Distance Weighting (GIDW) dengan:

  • Jarak 3-D efektif  : Haversine horizontal + koreksi elevasi terbobot
  • Koreksi lapse rate : Suhu, titik embun, tekanan udara per variabel
  • Bobot kualitas     : terrain_optimized vs nearest (per variabel)
  • GIDW               : blend antara linear gradient dan IDW murni
  • Kalibrasi p        : estimasi eksponen IDW dari variogram empiris
  • Koreksi mutual     : inter-station difference D(t) mengonstrain gradien
                         spasial sehingga kedua stasiun saling mengoreksi
  • Ketidakpastian     : propagasi σ dari perbedaan antar stasiun

Mutual Correction
-----------------
Kunci algoritma: Selisih D(t) = V₁(t) − V₂(t) memperkirakan gradien
spasial lokal ∇V ≈ (V₂ − V₁) / d₁₂. Gradien ini digunakan oleh GIDW
untuk mengoreksi interpolasi ke titik target T melebihi kemampuan IDW
biasa. Tiap stasiun "menginformasikan" estimasi yang dihasilkan stasiun
lain — itulah mekanisme saling koreksi.

Referensi
---------
  Shepard (1968) Two-dimensional interpolation function for
    irregularly spaced data. ACM '68.
  Liston & Elder (2006) A meteorological distribution system for
    high-resolution terrestrial modeling (MicroMet). J. Hydrometeor.
  ECMWF IFS Documentation CY47R3 (2021).

Penggunaan (CLI)
----------------
  python met_idw_blender.py file1.csv file2.csv \\
      --lat -7.521951 --lon 112.566089 --alt 27.07 \\
      --outdir ./output

Penggunaan (Python API)
-----------------------
  from met_idw_blender import MetIDWBlender, StationConfig, GeoPoint

  blender = MetIDWBlender(
      station1 = StationConfig("s1.csv", "terrain_optimized", "S1"),
      station2 = StationConfig("s2.csv", "nearest",           "S2"),
      target   = GeoPoint(-7.521951, 112.566089, 27.07, "Jolotundo"),
  )
  blender.run()
  blender.print_report()
  blender.export("./output")
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__  = "ASTERID / Jolotundo Research Observatory"

# ─── Standard library ─────────────────────────────────────────────────────────
import re
import sys
import json
import math
import warnings
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

# ─── Scientific stack ─────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from scipy import stats

# ─────────────────────────────────────────────────────────────────────────────
#  PHYSICAL CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

EARTH_RADIUS_KM: float = 6371.0088     # IUGG mean Earth radius (km)
RAD: float = math.pi / 180.0          # Degrees → radians conversion

# Atmospheric lapse rates (K m⁻¹; positive = colder with altitude)
LAPSE_TEMPERATURE: float = 6.5e-3     # ICAO standard environmental lapse rate
LAPSE_DEWPOINT:    float = 0.5e-3     # Approximate dew-point lapse rate
LAPSE_SOIL_0_7:    float = 5.0e-3     # Near-surface soil temperature
LAPSE_SOIL_7_28:   float = 4.0e-3
LAPSE_SOIL_28_100: float = 3.0e-3
LAPSE_SOIL_100_255:float = 2.0e-3

# Barometric altitude correction
GRAVITY: float   = 9.80665           # m s⁻²
Rd: float        = 287.053           # Gas constant dry air (J kg⁻¹ K⁻¹)

# Vertical-to-horizontal distance scaling for 3D IDW.
# Atmospheric fields are ~100–500× more correlated horizontally than
# vertically at near-surface scales.  1 m elevation ≈ 0.005 km horizontal.
VERT_SCALE: float = 5e-3             # km per metre elevation difference


# ─────────────────────────────────────────────────────────────────────────────
#  DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GeoPoint:
    """Immutable geographic point (WGS-84)."""
    lat: float    # Decimal degrees North (negative = South)
    lon: float    # Decimal degrees East  (negative = West)
    alt: float    # Metres above MSL
    label: str = ""

    @property
    def lat_rad(self) -> float:
        return self.lat * RAD

    @property
    def lon_rad(self) -> float:
        return self.lon * RAD


@dataclass
class StationConfig:
    """Open-Meteo source grid-cell descriptor."""
    filepath: Union[str, Path]
    cell_selection: str          # 'terrain_optimized' | 'nearest'
    label: str = ""
    # Populated after load():
    point: Optional[GeoPoint] = field(default=None, repr=False)
    data:  Optional[pd.DataFrame] = field(default=None, repr=False)


@dataclass
class VariableSpec:
    """
    Physical and spatial profile for one meteorological variable.

    Parameters
    ----------
    key            : canonical column name (no unit suffix)
    unit           : display unit string
    lapse_rate     : atmospheric lapse rate (K m⁻¹), 0 = no vertical correction
    terrain_quality: quality multiplier for terrain_optimized relative to nearest
                     (> 1 favours terrain cell; < 1 disfavours it for this var)
    idw_power      : default IDW power p (overridden by variogram estimate)
    decorr_km      : spatial decorrelation length scale (km) — controls GIDW α
    circular       : True for directional variables (wind direction) → circular mean
    categorical    : True for WMO codes → winner-takes-all
    pressure_type  : True for pressure variables → hypsometric correction
    """
    key:             str
    unit:            str
    lapse_rate:      float
    terrain_quality: float
    idw_power:       float
    decorr_km:       float
    circular:        bool  = False
    categorical:     bool  = False
    pressure_type:   bool  = False


# ─────────────────────────────────────────────────────────────────────────────
#  VARIABLE REGISTRY
#  Sources: ECMWF IFS Doc. CY47R3; Liston & Elder (2006) MicroMet Table 1;
#           Shepard (1968) spatial correlation analysis.
# ─────────────────────────────────────────────────────────────────────────────

REGISTRY: Dict[str, VariableSpec] = {
    # ── Near-surface temperature (terrain-optimized strongly preferred) ──────
    "temperature_2m":              VariableSpec("temperature_2m",             "°C",       LAPSE_TEMPERATURE, 1.20, 2.0,  50.0),
    "apparent_temperature":        VariableSpec("apparent_temperature",       "°C",       LAPSE_TEMPERATURE, 1.15, 2.0,  50.0),
    "dew_point_2m":                VariableSpec("dew_point_2m",               "°C",       LAPSE_DEWPOINT,    1.15, 2.0,  40.0),
    # ── Soil temperature (terrain-optimized; lapse decreases with depth) ─────
    "soil_temperature_0_to_7cm":   VariableSpec("soil_temperature_0_to_7cm",  "°C",       LAPSE_SOIL_0_7,    1.25, 2.0,  20.0),
    "soil_temperature_7_to_28cm":  VariableSpec("soil_temperature_7_to_28cm", "°C",       LAPSE_SOIL_7_28,   1.20, 2.0,  20.0),
    "soil_temperature_28_to_100cm":VariableSpec("soil_temperature_28_to_100cm","°C",      LAPSE_SOIL_28_100, 1.15, 2.5,  30.0),
    "soil_temperature_100_to_255cm":VariableSpec("soil_temperature_100_to_255cm","°C",    LAPSE_SOIL_100_255,1.10, 2.5,  40.0),
    # ── Humidity ──────────────────────────────────────────────────────────────
    "relative_humidity_2m":        VariableSpec("relative_humidity_2m",       "%",        0.0,               1.15, 2.0,  40.0),
    "vapour_pressure_deficit":     VariableSpec("vapour_pressure_deficit",    "kPa",      0.0,               1.10, 2.0,  40.0),
    "total_column_integrated_water_vapour":
                                   VariableSpec("total_column_integrated_water_vapour","kg/m²", 0.0,         1.05, 2.0,  80.0),
    # ── Pressure (hypsometric correction) ────────────────────────────────────
    "surface_pressure":            VariableSpec("surface_pressure",           "hPa",      0.0,               1.05, 2.0, 100.0, pressure_type=True),
    "pressure_msl":                VariableSpec("pressure_msl",               "hPa",      0.0,               1.00, 2.0, 200.0, pressure_type=True),
    # ── Precipitation (nearest unbiased; terrain may over-represent ridges) ──
    "precipitation":               VariableSpec("precipitation",              "mm",       0.0,               0.95, 1.5,  15.0),
    "rain":                        VariableSpec("rain",                       "mm",       0.0,               0.95, 1.5,  15.0),
    "snowfall":                    VariableSpec("snowfall",                   "cm",       0.0,               1.00, 1.5,  15.0),
    "snow_depth":                  VariableSpec("snow_depth",                 "m",        0.0,               1.05, 2.0,  15.0),
    # ── Wind ─────────────────────────────────────────────────────────────────
    "wind_speed_10m":              VariableSpec("wind_speed_10m",             "km/h",     0.0,               1.05, 1.5,  30.0),
    "wind_direction_10m":          VariableSpec("wind_direction_10m",         "°",        0.0,               1.05, 1.5,  30.0, circular=True),
    "wind_gusts_10m":              VariableSpec("wind_gusts_10m",             "km/h",     0.0,               1.05, 1.5,  25.0),
    "wind_speed_100m":             VariableSpec("wind_speed_100m",            "km/h",     0.0,               1.00, 1.5,  50.0),
    "wind_direction_100m":         VariableSpec("wind_direction_100m",        "°",        0.0,               1.00, 1.5,  50.0, circular=True),
    # ── Solar radiation (independent of cell selection at these scales) ───────
    "shortwave_radiation":         VariableSpec("shortwave_radiation",        "W/m²",     0.0,               1.00, 2.0, 100.0),
    "direct_radiation":            VariableSpec("direct_radiation",           "W/m²",     0.0,               1.00, 2.0, 100.0),
    "diffuse_radiation":           VariableSpec("diffuse_radiation",          "W/m²",     0.0,               1.00, 2.0, 100.0),
    "direct_normal_irradiance":    VariableSpec("direct_normal_irradiance",   "W/m²",     0.0,               1.00, 2.0, 100.0),
    "terrestrial_radiation":       VariableSpec("terrestrial_radiation",      "W/m²",     0.0,               1.00, 2.0, 100.0),
    "sunshine_duration":           VariableSpec("sunshine_duration",          "s",        0.0,               1.00, 2.0,  50.0),
    # ── Cloud cover ───────────────────────────────────────────────────────────
    "cloud_cover":                 VariableSpec("cloud_cover",                "%",        0.0,               1.00, 1.5,  80.0),
    "cloud_cover_low":             VariableSpec("cloud_cover_low",            "%",        0.0,               1.05, 1.5,  60.0),
    "cloud_cover_mid":             VariableSpec("cloud_cover_mid",            "%",        0.0,               1.00, 1.5,  80.0),
    "cloud_cover_high":            VariableSpec("cloud_cover_high",           "%",        0.0,               1.00, 1.5, 100.0),
    # ── Evapotranspiration (surface-property sensitive → terrain preferred) ───
    "et0_fao_evapotranspiration":  VariableSpec("et0_fao_evapotranspiration", "mm",       0.0,               1.20, 2.0,  30.0),
    # ── Soil moisture (terrain-optimized critical for land surface type) ──────
    "soil_moisture_0_to_7cm":      VariableSpec("soil_moisture_0_to_7cm",     "m³/m³",   0.0,               1.25, 2.0,  20.0),
    "soil_moisture_7_to_28cm":     VariableSpec("soil_moisture_7_to_28cm",    "m³/m³",   0.0,               1.20, 2.0,  20.0),
    "soil_moisture_28_to_100cm":   VariableSpec("soil_moisture_28_to_100cm",  "m³/m³",   0.0,               1.15, 2.5,  30.0),
    "soil_moisture_100_to_255cm":  VariableSpec("soil_moisture_100_to_255cm", "m³/m³",   0.0,               1.10, 2.5,  40.0),
    # ── WMO code (categorical: winner-takes-all) ──────────────────────────────
    "weather_code":                VariableSpec("weather_code",               "wmo",      0.0,               1.00, 0.0,  20.0, categorical=True),
}

_DEFAULT_SPEC = VariableSpec("_default", "", 0.0, 1.00, 2.0, 50.0)


def get_spec(var: str) -> VariableSpec:
    """Retrieve VariableSpec; fall back to default for unlisted variables."""
    if var in REGISTRY:
        return REGISTRY[var]
    for key, spec in REGISTRY.items():
        if var.startswith(key) or key.startswith(var):
            return spec
    return _DEFAULT_SPEC


# ─────────────────────────────────────────────────────────────────────────────
#  GEOMETRY
# ─────────────────────────────────────────────────────────────────────────────

def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    """
    Great-circle distance between two points in kilometres.
    Uses the Haversine formula (numerically stable for all distances).
    """
    dφ = b.lat_rad - a.lat_rad
    dλ = b.lon_rad - a.lon_rad
    h = (math.sin(dφ / 2) ** 2
         + math.cos(a.lat_rad) * math.cos(b.lat_rad) * math.sin(dλ / 2) ** 2)
    return 2.0 * EARTH_RADIUS_KM * math.asin(math.sqrt(max(0.0, min(1.0, h))))


def dist3d_km(source: GeoPoint, target: GeoPoint) -> float:
    """
    3D effective distance combining horizontal Haversine and scaled elevation.

    d₃D = √(d_h² + (VERT_SCALE × |Δz|)²)

    VERT_SCALE = 0.005 km m⁻¹ reflects the strong horizontal anisotropy of
    near-surface atmospheric fields (typical horizontal decorrelation length
    ~50 km vs. ~250 m vertical → ratio 1:200 → scale ≈ 0.005 km/m).
    """
    d_h = haversine_km(source, target)
    d_v = abs(source.alt - target.alt) * VERT_SCALE
    return math.hypot(d_h, d_v)


def local_cartesian_km(ref: GeoPoint, p: GeoPoint) -> Tuple[float, float]:
    """
    East (X) and North (Y) offsets from ref to p, in kilometres.
    Spherical flat-Earth approximation; valid for separations < 200 km.
    """
    cos_lat = math.cos(ref.lat_rad)
    x = (p.lon - ref.lon) * RAD * EARTH_RADIUS_KM * cos_lat
    y = (p.lat - ref.lat) * RAD * EARTH_RADIUS_KM
    return float(x), float(y)


# ─────────────────────────────────────────────────────────────────────────────
#  BASELINE GEOMETRY  (heart of the GIDW algorithm)
# ─────────────────────────────────────────────────────────────────────────────

class BaselineGeometry:
    """
    Precomputes the complete spatial geometry for blending two source
    stations (S1, S2) to a target point T.

    Key geometric quantities
    ────────────────────────
    d1_km      : 3D distance  S1 → T
    d2_km      : 3D distance  S2 → T
    d12_km     : 3D distance  S1 → S2 (baseline length)
    along_frac : parametric position of T on the S1→S2 baseline
                 (0 = at S1, 1 = at S2)
                 Defines the linear gradient weights:
                   W₁_lin = 1 − along_frac
                   W₂_lin = along_frac
    d_perp_km  : perpendicular distance from T to the S1–S2 baseline

    Mutual Correction Principle
    ───────────────────────────
    The inter-station difference D(t) = V₁(t) − V₂(t) constrains the
    local spatial gradient ∇V ≈ (V₂ − V₁) / d₁₂  along the baseline.
    By projecting T onto this baseline we obtain a gradient-corrected
    estimate that is exact for spatially linear fields.  This is superior
    to plain IDW which only uses distance but not the gradient direction.

    The blend between linear-gradient and IDW interpolation is controlled
    by α (alpha), which depends on how far T lies off the S1–S2 axis:
        α = exp(−d_perp / λ_perp)   where  λ_perp = decorr_km / 4
    When d_perp → 0 (T on the baseline): α → 1 (pure gradient).
    When d_perp >> λ_perp:               α → 0 (pure IDW).
    """

    def __init__(self, s1: GeoPoint, s2: GeoPoint, target: GeoPoint):
        self.s1     = s1
        self.s2     = s2
        self.target = target

        # 3D distances
        self.d1_km  = dist3d_km(s1, target)
        self.d2_km  = dist3d_km(s2, target)
        self.d12_km = dist3d_km(s1, s2)

        # Local Cartesian: target as origin
        x1, y1 = local_cartesian_km(target, s1)
        x2, y2 = local_cartesian_km(target, s2)

        # Horizontal baseline length (used for projection; avoids elevation distortion)
        bx, by = x2 - x1, y2 - y1
        d12_h = math.hypot(bx, by)

        if d12_h < 1e-9:
            # Degenerate: stations at identical location
            self.along_frac  = 0.5
            self.d_perp_km   = 0.0
            self._W_lin      = (0.5, 0.5)
            self._ux, self._uy = 1.0, 0.0
            return

        ux, uy = bx / d12_h, by / d12_h   # unit vector S1→S2
        self._ux, self._uy = ux, uy

        # Vector S1 → T  (T is origin, S1 is at x1,y1 → so T−S1 = −x1,−y1)
        tx, ty = -x1, -y1

        # Scalar projection of (S1→T) onto the baseline
        along = tx * ux + ty * uy
        # Perpendicular distance (unsigned)
        perp  = abs(tx * (-uy) + ty * ux)

        # Clamp to [0, d12_h] — do not extrapolate beyond the stations
        along_c = max(0.0, min(along, d12_h))

        self.along_frac = float(along_c / d12_h)
        self.d_perp_km  = float(perp)
        self._W_lin     = (1.0 - self.along_frac, self.along_frac)

    # ── Per-variable computed properties ──────────────────────────────────────

    def alpha(self, spec: VariableSpec) -> float:
        """
        GIDW gradient reliability factor α ∈ [0, 1].
        Higher α → gradient interpolation dominates.
        Higher decorr_km (smoother variable) → higher α at same d_perp.
        """
        lambda_perp = max(spec.decorr_km / 4.0, 0.1)
        return float(math.exp(-self.d_perp_km / lambda_perp))

    def quality_factor(self, spec: VariableSpec, cell_selection: str) -> float:
        """
        Quality multiplier Q(variable, cell_selection).
        terrain_optimized → spec.terrain_quality  (may be > or < 1)
        nearest           → 1.0  (baseline reference)
        """
        if cell_selection == "terrain_optimized":
            return float(spec.terrain_quality)
        return 1.0

    def idw_weights(
        self, spec: VariableSpec, q1: float, q2: float
    ) -> Tuple[float, float]:
        """
        Quality-adjusted IDW weights.
          wᵢ = Qᵢ / dᵢ^p    (p = spec.idw_power)
        Normalised to sum to 1.
        """
        p = spec.idw_power
        if p <= 0 or self.d1_km < 1e-9 or self.d2_km < 1e-9:
            return (0.5, 0.5)
        w1 = q1 / (self.d1_km ** p)
        w2 = q2 / (self.d2_km ** p)
        s  = w1 + w2
        return (w1 / s, w2 / s) if s > 0 else (0.5, 0.5)

    def gidw_weights(
        self, spec: VariableSpec, q1: float, q2: float
    ) -> Tuple[float, float]:
        """
        Gradient-Enhanced IDW (GIDW) final normalised weights.

            W_final = α · W_linear + (1−α) · W_IDW

        Where:
          W_linear = (along_frac-based) gradient interpolation weights
          W_IDW    = quality-adjusted inverse-distance weights
          α        = gradient reliability factor (depends on d_perp, decorr_km)

        Both component weight pairs sum to 1, so W_final also sums to 1.
        The GIDW estimate for value V is then:
            V̂_T = W1_final · V₁ + W2_final · V₂
        """
        a   = self.alpha(spec)
        W_l = self._W_lin
        W_i = self.idw_weights(spec, q1, q2)
        w1  = a * W_l[0] + (1.0 - a) * W_i[0]
        w2  = a * W_l[1] + (1.0 - a) * W_i[1]
        return (float(w1), float(w2))


# ─────────────────────────────────────────────────────────────────────────────
#  ATMOSPHERIC CORRECTIONS
# ─────────────────────────────────────────────────────────────────────────────

def lapse_correction(
    series: pd.Series, spec: VariableSpec, dz_m: float
) -> pd.Series:
    """
    Shift a temperature-family variable from source elevation to target elevation.

    V_target ≈ V_source − lapse_rate × Δz

    Δz = target_alt − source_alt  (positive → target is higher → colder)
    For temperature: correction ≈ −6.5e-3 × Δz °C
    For dew-point:   correction ≈ −0.5e-3 × Δz °C
    """
    if abs(spec.lapse_rate) < 1e-12 or abs(dz_m) < 0.01:
        return series
    return series + (-spec.lapse_rate * dz_m)


def pressure_hypsometric(
    series: pd.Series, dz_m: float, T_mean_K: float = 298.0
) -> pd.Series:
    """
    Hypsometric (barometric) altitude correction for pressure variables.

        P_target ≈ P_source × [1 − g·Δz / (Rd·T_mean)]

    Uses a linearised form of the full hypsometric equation; accurate
    for |Δz| < 500 m.  T_mean estimated from companion temperature column
    or defaults to 298 K (typical tropical surface temperature).
    """
    if abs(dz_m) < 0.01:
        return series
    factor = 1.0 + (-GRAVITY * dz_m) / (Rd * T_mean_K)
    return series * factor


# ─────────────────────────────────────────────────────────────────────────────
#  CIRCULAR BLENDING  (for wind direction)
# ─────────────────────────────────────────────────────────────────────────────

def circular_blend_series(
    θ1_deg: pd.Series, θ2_deg: pd.Series, w1: float, w2: float
) -> pd.Series:
    """
    Weighted circular mean of two angular time series (degrees).

    Converts to unit vectors, computes weighted vector sum, returns resultant
    angle in [0°, 360°).  Correctly handles the 0°/360° discontinuity.

    Uncertainty is returned as the circular spread (see InterStationAnalyzer).
    """
    θ1 = np.deg2rad(θ1_deg.values)
    θ2 = np.deg2rad(θ2_deg.values)
    x  = w1 * np.cos(θ1) + w2 * np.cos(θ2)
    y  = w1 * np.sin(θ1) + w2 * np.sin(θ2)
    θ  = np.rad2deg(np.arctan2(y, x)) % 360.0
    return pd.Series(θ, index=θ1_deg.index, name=θ1_deg.name)


# ─────────────────────────────────────────────────────────────────────────────
#  INTER-STATION TEMPORAL ANALYZER
# ─────────────────────────────────────────────────────────────────────────────

class InterStationAnalyzer:
    """
    Analyses the temporal structure of the inter-station difference series
    D(t) = V₁(t) − V₂(t) to:

      1. Quantify systematic bias (terrain effect, elevation offset)
      2. Estimate random interpolation uncertainty
      3. Assess temporal consistency (data quality proxy)
      4. Estimate optimal IDW power p via variogram analysis

    Mutual Correction Role
    ─────────────────────
    D(t) is the empirical realization of the spatial gradient along the
    S1→S2 baseline.  Its temporal statistics tell us:
      • mean(D)  → permanent terrain/location offset → bias of blend
      • std(D)   → random component → interpolation uncertainty σ
      • ρ(V₁,V₂) → if ρ ≈ 1: both stations see same weather (good blend)
                    if ρ << 1: localised phenomena (blend less reliable)
    """

    def __init__(self, s1: pd.Series, s2: pd.Series):
        mask     = s1.notna() & s2.notna()
        self.D   = (s1 - s2)[mask]
        self.V1  = s1[mask]
        self.V2  = s2[mask]
        self._n  = int(mask.sum())

    # ── Scalar statistics ──────────────────────────────────────────────────────

    def mean_bias(self) -> float:
        """Mean inter-station difference E[V₁ − V₂].
        Positive → S1 (terrain) systematically higher than S2 (nearest)."""
        return float(self.D.mean()) if self._n > 0 else 0.0

    def std_diff(self) -> float:
        """Standard deviation of D; proxy for random interpolation error."""
        return float(self.D.std(ddof=1)) if self._n > 1 else 0.0

    def rmsd(self) -> float:
        """Root-mean-square inter-station difference."""
        return float(np.sqrt((self.D ** 2).mean())) if self._n > 0 else 0.0

    def mae(self) -> float:
        """Mean absolute inter-station difference."""
        return float(self.D.abs().mean()) if self._n > 0 else 0.0

    def pearson_r(self) -> float:
        """Pearson cross-correlation ρ(V₁, V₂)."""
        if self._n < 10:
            return float("nan")
        r, _ = stats.pearsonr(self.V1.values, self.V2.values)
        return float(r)

    def consistency_score(self) -> float:
        """
        Normalized consistency score ∈ [0, 1].

            score = exp(−RMSD² / (½ (σ₁² + σ₂²)))

        Derived from normalized RMSD relative to joint variance.
        score ≈ 1 → perfect agreement (blend highly reliable).
        score ≈ 0 → no correlation (blend less reliable).
        """
        joint_var = 0.5 * (float(self.V1.var()) + float(self.V2.var()))
        if joint_var < 1e-30:
            return 1.0
        return float(np.exp(-(self.rmsd() ** 2) / joint_var))

    # ── Variogram-based IDW power estimator ───────────────────────────────────

    def estimate_idw_power(self, d12_km: float, spec: VariableSpec) -> float:
        """
        Estimate optimal IDW power p from the variogram at lag d₁₂.

        Theory (Shepard 1968; Cressie 1993 §2.4):
        ────────────────────────────────────────────────────
        The empirical semivariance at lag h₁₂:
            γ(h₁₂) = ½ · Var(D) = ½ · Var(V₁ − V₂)

        The variogram sill (total field variance):
            C₀ ≈ ½ (Var₁ + Var₂)

        Normalized:
            γ_rel = γ(h₁₂) / C₀  ∈ (0, 1)

        For a power variogram model  γ(h) ∝ (h/range)^β:
            γ_rel ≈ (h₁₂ / range)^β
            ⟹ β = log(γ_rel) / log(h₁₂ / decorr_km)

        Empirical IDW relationship (Shepard 1968):
            p_opt ≈ β / 2      clamped to [0.5, 3.0]

        When β cannot be estimated reliably, the registry default is used.
        """
        if self._n < 48:                         # Need at least 2 days hourly
            return spec.idw_power

        gamma_h  = 0.5 * float(self.D.var(ddof=1))
        sill     = 0.5 * (float(self.V1.var()) + float(self.V2.var()))

        if sill < 1e-12 or gamma_h < 1e-12:
            return spec.idw_power

        gamma_rel = min(gamma_h / sill, 0.999)
        h_norm    = max(1e-3, min(d12_km / max(spec.decorr_km, 0.1), 0.999))

        try:
            beta  = math.log(gamma_rel) / math.log(h_norm)
            p_opt = float(np.clip(beta / 2.0, 0.5, 3.0))
        except (ValueError, ZeroDivisionError, OverflowError):
            p_opt = spec.idw_power

        return p_opt

    # ── Temporal breakdowns ───────────────────────────────────────────────────

    def monthly_bias(self) -> pd.Series:
        """Month-of-year mean bias (Jan=1 … Dec=12)."""
        return self.D.groupby(self.D.index.month).mean()

    def diurnal_bias(self) -> pd.Series:
        """Hour-of-day mean bias (0 … 23 local time)."""
        return self.D.groupby(self.D.index.hour).mean()

    def bias_amplitude(self) -> float:
        """Peak-to-peak amplitude of the diurnal bias cycle."""
        db = self.diurnal_bias()
        return float(db.max() - db.min()) if len(db) > 1 else 0.0

    def to_dict(self) -> dict:
        return {
            "n_valid":             self._n,
            "mean_bias_V1_V2":     round(self.mean_bias(), 6),
            "std_diff":            round(self.std_diff(), 6),
            "mae":                 round(self.mae(), 6),
            "rmsd":                round(self.rmsd(), 6),
            "pearson_r":           round(self.pearson_r(), 6),
            "consistency_score":   round(self.consistency_score(), 4),
            "diurnal_bias_ampl":   round(self.bias_amplitude(), 6),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  CSV PARSER  (Open-Meteo format)
# ─────────────────────────────────────────────────────────────────────────────

_UNIT_RE = re.compile(r"\s*\([^)]*\)\s*$")


def _strip_units(name: str) -> str:
    """'temperature_2m (°C)' → 'temperature_2m'"""
    return _UNIT_RE.sub("", name).strip()


def parse_open_meteo_csv(
    filepath: Union[str, Path],
) -> Tuple[pd.DataFrame, GeoPoint]:
    """
    Parse an Open-Meteo historical CSV export.

    File layout
    ───────────
    Row 0 : 'latitude,longitude,elevation,utc_offset_seconds,timezone,...'
    Row 1 : '-7.49,112.54,28.0,25200,Asia/Jakarta,GMT+7'
    Row 2 : (blank)
    Row 3 : 'time,temperature_2m (°C),...'  ← column header
    Row 4+: data

    Returns
    ───────
    df    : DatetimeIndex DataFrame with unit-stripped column names,
            sorted by time, float64 dtype.
    point : GeoPoint extracted from CSV metadata row.
    """
    filepath = Path(filepath)

    with filepath.open(encoding="utf-8") as fh:
        meta_keys = fh.readline().strip().split(",")
        meta_vals = fh.readline().strip().split(",")
    meta  = dict(zip(meta_keys, meta_vals))
    point = GeoPoint(
        lat   = float(meta.get("latitude",  0)),
        lon   = float(meta.get("longitude", 0)),
        alt   = float(meta.get("elevation", 0)),
        label = meta.get("timezone_abbreviation", ""),
    )

    df = pd.read_csv(
        filepath,
        skiprows=[0, 1, 2],            # skip metadata rows + blank
        parse_dates=["time"],
        index_col="time",
        na_values=["", "NaN", "nan"],
        low_memory=False,
    )
    # Force numeric, strip units from column names
    df.columns = [_strip_units(c) for c in df.columns]
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    df.index.name = "time"

    return df, point


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN BLENDER
# ─────────────────────────────────────────────────────────────────────────────

class MetIDWBlender:
    """
    Advanced Gradient-Enhanced IDW Meteorological Blender.

    Combines two Open-Meteo grid cells (terrain_optimized + nearest) into a
    single blended time series at the specified target point.

    Quick start
    ───────────
    blender = MetIDWBlender(sta1, sta2, target)
    blender.run()
    blender.print_report()
    blender.export("./output")

    Full pipeline
    ─────────────
    blender.load()            → parse CSVs, align timestamps, precompute geometry
    blender.compute_weights() → per-variable GIDW weights + diagnostics
    blender.blend()           → produce blended time series + σ uncertainty
    """

    def __init__(
        self,
        station1:        StationConfig,
        station2:        StationConfig,
        target:          GeoPoint,
        use_variogram_p: bool = True,
    ):
        """
        Parameters
        ----------
        station1         : StationConfig for terrain_optimized cell (S1)
        station2         : StationConfig for nearest cell (S2)
        target           : GeoPoint for the blend destination
        use_variogram_p  : if True, estimate IDW power p from data variogram
                           for each variable (overrides registry default).
                           Recommended for best accuracy.
        """
        self.sta1          = station1
        self.sta2          = station2
        self.target        = target
        self.use_variogram_p = use_variogram_p

        # Internal state (populated by load / compute_weights / blend)
        self._geo:       Optional[BaselineGeometry] = None
        self._vars:      List[str]                   = []
        self._q1:        Dict[str, float]            = {}
        self._q2:        Dict[str, float]            = {}
        self._weights:   Dict[str, Tuple[float, float]] = {}
        self._opt_p:     Dict[str, float]            = {}
        self._blended:   Optional[pd.DataFrame]      = None
        self._sigma:     Optional[pd.DataFrame]      = None
        self._diag:      Dict[str, dict]             = {}

    # ─── Loading ──────────────────────────────────────────────────────────────

    def load(self) -> "MetIDWBlender":
        """
        Parse both CSV files, align timestamps (inner join), precompute geometry.
        """
        df1, p1 = parse_open_meteo_csv(self.sta1.filepath)
        df2, p2 = parse_open_meteo_csv(self.sta2.filepath)

        self.sta1.point, self.sta1.data = p1, df1
        self.sta2.point, self.sta2.data = p2, df2

        # Align timestamps
        idx = df1.index.intersection(df2.index)
        if len(idx) < len(df1) or len(idx) < len(df2):
            n_drop = max(len(df1), len(df2)) - len(idx)
            warnings.warn(
                f"Timestamp alignment: {len(idx):,} common rows "
                f"({n_drop:,} rows discarded from longer file)."
            )
        self.sta1.data = df1.loc[idx].copy()
        self.sta2.data = df2.loc[idx].copy()

        # Common variables
        self._vars = sorted(
            set(self.sta1.data.columns) & set(self.sta2.data.columns)
        )
        only_s1 = sorted(set(df1.columns) - set(df2.columns))
        only_s2 = sorted(set(df2.columns) - set(df1.columns))
        if only_s1 or only_s2:
            warnings.warn(
                f"Station-only columns (excluded from blend): "
                f"S1={only_s1}  S2={only_s2}"
            )

        # Baseline geometry
        self._geo = BaselineGeometry(p1, p2, self.target)

        # Per-variable quality factors
        for v in self._vars:
            spec       = get_spec(v)
            self._q1[v] = self._geo.quality_factor(spec, self.sta1.cell_selection)
            self._q2[v] = self._geo.quality_factor(spec, self.sta2.cell_selection)

        return self

    # ─── Weight computation ───────────────────────────────────────────────────

    def compute_weights(self) -> "MetIDWBlender":
        """
        Compute per-variable GIDW weights and populate diagnostics table.

        For each variable:
          1. Apply lapse-rate/pressure corrections to both series
          2. Run InterStationAnalyzer on the corrected pair
          3. Optionally estimate optimal IDW power p via variogram
          4. Compute GIDW weights = α·W_linear + (1−α)·W_IDW
        """
        if self._geo is None:
            raise RuntimeError("Call .load() before .compute_weights()")

        geo = self._geo

        for v in self._vars:
            spec  = get_spec(v)
            s1_c  = self._corrected(self.sta1, v, spec)
            s2_c  = self._corrected(self.sta2, v, spec)
            ana   = InterStationAnalyzer(s1_c, s2_c)

            # Variogram-based power refinement
            p_opt = spec.idw_power
            if self.use_variogram_p and not spec.categorical and not spec.circular:
                p_opt = ana.estimate_idw_power(geo.d12_km, spec)
                spec  = VariableSpec(
                    spec.key, spec.unit, spec.lapse_rate,
                    spec.terrain_quality, p_opt, spec.decorr_km,
                    spec.circular, spec.categorical, spec.pressure_type,
                )
            self._opt_p[v] = p_opt

            # GIDW weights
            q1, q2           = self._q1[v], self._q2[v]
            w1, w2           = geo.gidw_weights(spec, q1, q2)
            self._weights[v] = (w1, w2)

            # Diagnostic record
            self._diag[v] = {
                "variable":          v,
                "unit":              get_spec(v).unit,
                "d1_km":             round(geo.d1_km,  4),
                "d2_km":             round(geo.d2_km,  4),
                "d12_km":            round(geo.d12_km, 4),
                "d_perp_km":         round(geo.d_perp_km, 4),
                "along_frac":        round(geo.along_frac, 4),
                "W1_linear_%":       round((1 - geo.along_frac) * 100, 3),
                "W2_linear_%":       round(geo.along_frac * 100, 3),
                "alpha_gidw":        round(geo.alpha(get_spec(v)), 4),
                "idw_power_p":       round(p_opt, 4),
                "Q1_terrain":        round(q1, 4),
                "Q2_nearest":        round(q2, 4),
                "W1_final_%":        round(w1 * 100, 3),
                "W2_final_%":        round(w2 * 100, 3),
                **ana.to_dict(),
            }

        return self

    # ─── Blending ─────────────────────────────────────────────────────────────

    def blend(self) -> "MetIDWBlender":
        """
        Produce the blended time-series and per-variable 1-σ uncertainty.

        Blending rules per variable class:
          • Continuous scalars  → weighted sum  V̂ = w₁V₁ + w₂V₂
          • Circular (wind dir) → weighted circular mean
          • Categorical (codes) → value from the dominant-weight station

        Uncertainty (σ)
          For continuous variables:
            σ = |V₁ − V₂| · √(w₁² + w₂²)
          This propagates the inter-station spread through the weights.
          When the stations strongly agree, σ → 0.
          When they disagree, σ captures the spatial interpolation uncertainty.
        """
        if not self._weights:
            raise RuntimeError("Call .compute_weights() before .blend()")

        blended: Dict[str, pd.Series] = {}
        sigma:   Dict[str, pd.Series] = {}

        for v in self._vars:
            spec   = get_spec(v)
            s1_c   = self._corrected(self.sta1, v, spec)
            s2_c   = self._corrected(self.sta2, v, spec)
            w1, w2 = self._weights[v]

            if spec.categorical:
                # Winner-takes-all
                dominant     = s1_c if w1 >= w2 else s2_c
                blended[v]   = dominant
                sigma[v]     = pd.Series(np.nan, index=s1_c.index, dtype=float)

            elif spec.circular:
                blended[v] = circular_blend_series(s1_c, s2_c, w1, w2)
                # Angular spread as uncertainty
                θ1 = np.deg2rad(s1_c.values)
                θ2 = np.deg2rad(s2_c.values)
                Rx = w1 * np.cos(θ1) + w2 * np.cos(θ2)
                Ry = w1 * np.sin(θ1) + w2 * np.sin(θ2)
                R  = np.hypot(Rx, Ry)
                sigma[v] = pd.Series(
                    np.rad2deg(np.arccos(np.clip(R, 0.0, 1.0))),
                    index=s1_c.index, dtype=float
                )

            else:
                blend_s    = w1 * s1_c + w2 * s2_c
                blended[v] = blend_s
                sigma[v]   = (s1_c - s2_c).abs() * math.sqrt(w1**2 + w2**2)

        idx = self.sta1.data.index
        self._blended = pd.DataFrame(blended, index=idx)
        self._sigma   = pd.DataFrame(sigma,   index=idx)
        return self

    # ─── Internal helpers ─────────────────────────────────────────────────────

    def _corrected(
        self, station: StationConfig, var: str, spec: VariableSpec
    ) -> pd.Series:
        """
        Retrieve `var` from `station` and apply vertical atmospheric correction
        to the target elevation (Δz = target.alt − station.alt).
        """
        s  = station.data[var].copy()
        dz = self.target.alt - station.point.alt

        if spec.pressure_type:
            t_col  = "temperature_2m"
            T_mean = (
                float(station.data[t_col].mean()) + 273.15
                if t_col in station.data.columns else 298.0
            )
            return pressure_hypsometric(s, dz, T_mean)

        return lapse_correction(s, spec, dz)

    # ─── Public accessors ─────────────────────────────────────────────────────

    def get_blended(self) -> pd.DataFrame:
        """Blended time-series DataFrame (index: DatetimeIndex)."""
        if self._blended is None:
            raise RuntimeError("Call .blend() first.")
        return self._blended.copy()

    def get_sigma(self) -> pd.DataFrame:
        """Per-variable 1-σ uncertainty DataFrame (same shape as blended)."""
        if self._sigma is None:
            raise RuntimeError("Call .blend() first.")
        return self._sigma.copy()

    def get_weights(self) -> pd.DataFrame:
        """
        Per-variable weight summary as DataFrame.

        Columns
        ───────
        unit, W1_terrain_%, W2_nearest_%, idw_power_p, alpha_gidw,
        Q1_terrain, W1_linear_%, W2_linear_%
        """
        if not self._weights:
            raise RuntimeError("Call .compute_weights() first.")
        rows = []
        geo  = self._geo
        for v, (w1, w2) in self._weights.items():
            spec = get_spec(v)
            rows.append({
                "variable":     v,
                "unit":         spec.unit,
                "W1_terrain_%": round(w1 * 100, 3),
                "W2_nearest_%": round(w2 * 100, 3),
                "idw_power_p":  round(self._opt_p.get(v, spec.idw_power), 3),
                "alpha_gidw":   round(geo.alpha(spec), 4),
                "Q1_terrain":   round(self._q1.get(v, 1.0), 3),
                "Q2_nearest":   round(self._q2.get(v, 1.0), 3),
                "W1_linear_%":  round((1 - geo.along_frac) * 100, 3),
                "W2_linear_%":  round(geo.along_frac * 100, 3),
            })
        return pd.DataFrame(rows).set_index("variable")

    def get_diagnostics(self) -> pd.DataFrame:
        """Full per-variable diagnostics table (includes geometry + statistics)."""
        if not self._diag:
            raise RuntimeError("Call .compute_weights() first.")
        return pd.DataFrame(list(self._diag.values())).set_index("variable")

    def get_geometry(self) -> dict:
        """Summary of spatial geometry."""
        geo = self._geo
        return {
            "target":          {"lat": self.target.lat, "lon": self.target.lon, "alt_m": self.target.alt},
            "source1_terrain": {"lat": self.sta1.point.lat, "lon": self.sta1.point.lon, "alt_m": self.sta1.point.alt},
            "source2_nearest": {"lat": self.sta2.point.lat, "lon": self.sta2.point.lon, "alt_m": self.sta2.point.alt},
            "d1_km":            round(geo.d1_km,  4),
            "d2_km":            round(geo.d2_km,  4),
            "d12_km":           round(geo.d12_km, 4),
            "along_frac":       round(geo.along_frac, 4),
            "d_perp_km":        round(geo.d_perp_km, 4),
            "W1_linear":        round(1 - geo.along_frac, 4),
            "W2_linear":        round(geo.along_frac, 4),
        }

    def run(self) -> "MetIDWBlender":
        """Convenience: load → compute_weights → blend in one call."""
        return self.load().compute_weights().blend()

    # ─── Export ───────────────────────────────────────────────────────────────

    def export(
        self,
        out_dir:  Union[str, Path] = ".",
        prefix:   str               = "blended",
        formats:  Tuple[str, ...]   = ("csv", "json"),
    ) -> Dict[str, Path]:
        """
        Write results to disk.

        Output files (with default prefix='blended')
        ─────────────────────────────────────────────
        blended_timeseries.csv   : main blended time-series
        blended_sigma.csv        : per-timestamp, per-variable σ uncertainty
        blended_weights.csv      : per-variable weight summary
        blended_diagnostics.csv  : full diagnostics table
        blended_summary.json     : human-readable JSON summary

        Returns mapping {output_name → Path}.
        """
        if self._blended is None:
            raise RuntimeError("Call .blend() first.")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        paths: Dict[str, Path] = {}

        if "csv" in formats:
            p = out_dir / f"{prefix}_timeseries.csv"
            self._blended.to_csv(p)
            paths["timeseries_csv"] = p

            p = out_dir / f"{prefix}_sigma.csv"
            self._sigma.to_csv(p)
            paths["sigma_csv"] = p

            p = out_dir / f"{prefix}_weights.csv"
            self.get_weights().to_csv(p)
            paths["weights_csv"] = p

            p = out_dir / f"{prefix}_diagnostics.csv"
            self.get_diagnostics().to_csv(p)
            paths["diagnostics_csv"] = p

        if "json" in formats:
            p = out_dir / f"{prefix}_summary.json"
            p.write_text(
                json.dumps(self._build_summary(), indent=2, default=str),
                encoding="utf-8",
            )
            paths["summary_json"] = p

        return paths

    def _build_summary(self) -> dict:
        return {
            "version":             __version__,
            "algorithm":           "Gradient-Enhanced IDW (GIDW)",
            "geometry":            self.get_geometry(),
            "n_timestamps":        len(self._blended),
            "time_start":          str(self._blended.index.min()),
            "time_end":            str(self._blended.index.max()),
            "n_variables_blended": len(self._vars),
            "variables":           self._diag,
        }

    # ─── Pretty Report ────────────────────────────────────────────────────────

    def print_report(self) -> None:
        """
        Print a formatted console report of the blending configuration,
        geometry, per-variable weights and diagnostics.
        """
        if not self._weights:
            raise RuntimeError("Call .compute_weights() first.")

        geo = self._geo
        W   = "═" * 78
        w   = "─" * 78

        print(f"\n{W}")
        print(f"  GIDW METEOROLOGICAL BLENDING — ASTERID / Jolotundo Observatory")
        print(f"  Algorithm: Gradient-Enhanced Inverse Distance Weighting v{__version__}")
        print(W)

        # ── Target & sources
        T  = self.target
        P1 = self.sta1.point
        P2 = self.sta2.point
        print(f"\n  TARGET   : {T.lat:+.6f}°  {T.lon:+.6f}°  z = {T.alt:.2f} m  "
              f"[{T.label}]")
        print()
        print(f"  Source 1 ({self.sta1.cell_selection}):  [{self.sta1.label}]")
        print(f"    {P1.lat:+.6f}°  {P1.lon:+.6f}°  z = {P1.alt:.1f} m")
        print(f"    3D dist to target: {geo.d1_km:.4f} km")
        print()
        print(f"  Source 2 ({self.sta2.cell_selection}):  [{self.sta2.label}]")
        print(f"    {P2.lat:+.6f}°  {P2.lon:+.6f}°  z = {P2.alt:.1f} m")
        print(f"    3D dist to target: {geo.d2_km:.4f} km")

        # ── Geometry summary
        print(f"\n{w}")
        print(f"  SPATIAL GEOMETRY")
        print(w)
        print(f"  Baseline S1→S2      : {geo.d12_km:.4f} km")
        print(f"  Target on baseline  : {geo.along_frac*100:.2f}%  "
              f"(W_lin₁ = {(1-geo.along_frac)*100:.2f}%  "
              f"W_lin₂ = {geo.along_frac*100:.2f}%)")
        print(f"  Target off-axis     : {geo.d_perp_km:.4f} km  "
              f"(perpendicular distance to S1–S2 line)")
        print(f"\n  Note: Target lies {geo.along_frac*100:.1f}% of the way from S1 to S2.")
        print(f"  Off-axis distance {geo.d_perp_km:.2f} km limits gradient reliability (α).")

        # ── Mutual correction explanation
        print(f"\n{w}")
        print(f"  MUTUAL CORRECTION PRINCIPLE (GIDW)")
        print(w)
        print(f"  D(t) = V₁(t) − V₂(t)  constrains the local spatial gradient:")
        print(f"    ∇V ≈ (V₂ − V₁) / d₁₂  [{geo.d12_km:.2f} km baseline]")
        print(f"  This gradient is used to linearly interpolate to target T,")
        print(f"  correcting the IDW estimate via α-weighted combination:")
        print(f"    W_final = α·W_linear + (1−α)·W_IDW")
        print(f"  α varies by variable decorrelation length (see table below).")

        # ── Per-variable weights table
        print(f"\n{w}")
        hdr = f"  {'Variable':<38s} {'Unit':>6s}  {'W₁-T%':>7s} {'W₂-N%':>7s}"
        hdr += f" {'p':>5s} {'α':>6s} {'r':>6s} {'σ_D':>8s}"
        print(hdr)
        print(f"  {'(terrain opt.)':>46s} {'(nearest)':>7s}")
        print(f"  {w}")

        for v in sorted(self._weights.keys()):
            w1, w2 = self._weights[v]
            spec   = get_spec(v)
            d      = self._diag[v]
            if spec.categorical:
                dom = "S1" if w1 >= w2 else "S2"
                print(f"  {v[:38]:<38s} {spec.unit:>6s}  "
                      f"  winner → {dom}")
                continue
            p_str  = f"{d['idw_power_p']:.2f}"
            a_str  = f"{d['alpha_gidw']:.3f}"
            r_str  = f"{d['pearson_r']:.3f}"
            sd_str = f"{d['std_diff']:.4f}"
            print(
                f"  {v[:38]:<38s} {spec.unit:>6s}  "
                f"{w1*100:>7.3f} {w2*100:>7.3f}"
                f" {p_str:>5s} {a_str:>6s} {r_str:>6s} {sd_str:>8s}"
            )

        print(w)
        print("  p  = IDW power (variogram-estimated per variable)")
        print("  α  = GIDW gradient weight (α→1: gradient dominates; α→0: pure IDW)")
        print("  r  = Pearson correlation V₁ vs V₂ (consistency proxy)")
        print("  σ_D= Std of inter-station difference (spatial uncertainty proxy)")
        print("  W₁-T% = terrain_optimized weight  |  W₂-N% = nearest weight")

        # ── Time series stats
        if self._blended is not None:
            print(f"\n{w}")
            print(f"  BLENDED TIME SERIES")
            print(w)
            print(f"  Period      : {self._blended.index.min()}  →  "
                  f"{self._blended.index.max()}")
            print(f"  Timestamps  : {len(self._blended):,}  (hourly)")
            print(f"  Variables   : {len(self._vars):,}")

        print(f"\n{W}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  COMMAND-LINE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="met_idw_blender",
        description=(
            "Gradient-Enhanced IDW blend of two Open-Meteo grid cells "
            "to a target geographic point.\n\n"
            "Source 1 must be the terrain_optimized cell.\n"
            "Source 2 must be the nearest cell."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("file1",   help="CSV for terrain-optimized cell (S1)")
    p.add_argument("file2",   help="CSV for nearest cell (S2)")
    p.add_argument("--lat",   type=float, required=True, help="Target latitude  (°, negative = South)")
    p.add_argument("--lon",   type=float, required=True, help="Target longitude (°, negative = West)")
    p.add_argument("--alt",   type=float, required=True, help="Target altitude  (m MSL, Copernicus DEM)")
    p.add_argument("--outdir",  default=".",          help="Output directory (default: current dir)")
    p.add_argument("--prefix",  default="blended",   help="Output filename prefix (default: blended)")
    p.add_argument("--no-variogram-p", action="store_true",
                   help="Use registry default IDW power p (skip variogram estimation)")
    p.add_argument("--formats", default="csv,json",
                   help="Comma-separated output formats: csv, json (default: csv,json)")
    p.add_argument("--quiet",   action="store_true", help="Suppress console report")
    return p


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    target = GeoPoint(
        lat   = args.lat,
        lon   = args.lon,
        alt   = args.alt,
        label = "target",
    )
    sta1 = StationConfig(
        filepath       = Path(args.file1),
        cell_selection = "terrain_optimized",
        label          = "S1-terrain",
    )
    sta2 = StationConfig(
        filepath       = Path(args.file2),
        cell_selection = "nearest",
        label          = "S2-nearest",
    )

    blender = MetIDWBlender(
        station1        = sta1,
        station2        = sta2,
        target          = target,
        use_variogram_p = not args.no_variogram_p,
    )

    print("Loading and aligning data …", file=sys.stderr)
    blender.load()
    print("Computing per-variable GIDW weights …", file=sys.stderr)
    blender.compute_weights()
    print("Blending time series …", file=sys.stderr)
    blender.blend()

    if not args.quiet:
        blender.print_report()

    fmts  = tuple(f.strip() for f in args.formats.split(","))
    paths = blender.export(out_dir=args.outdir, prefix=args.prefix, formats=fmts)
    print("\nOutput files:")
    for name, path in paths.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
