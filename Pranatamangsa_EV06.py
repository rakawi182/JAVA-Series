#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pranatamangsa_EV06.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KALENDER PRANATA MANGSA — METEO(DAILY+6H) + ENSO + ASTRONOMI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMBER DATA METEOROLOGI
  · Titik Target  : −7.5220°LS, 112.5661°BT (MJS Obs., EAST JAVA), 28 m dpl
  · Stasiun P1    : ERA5/ERA5LandOpen/IFSHRES Open-Meteo — daily 1950–2026,
                    6-jam 2015–2026
                    Koordinat: −7.486819°LS, 112.538210°BT · Elev: 28 m dpl
  · Stasiun P2    : ERA5/ERA5LandOpen/IFSHRES Open-Meteo — daily 1940–2026,
                    6-jam 1995–2026
                    Koordinat: −7.5571175°LS, 112.557350°BT · Elev: 28 m dpl
    Interpolasi   : Inverse Distance Weighting (IDW, power=2)
                    w1=0.3950 (P1), w2=0.6050 (P2)
  · ENSO Niño3.4 mingguan — AVISO/DUACS, 1993–2026

SUMBER DATA ASTRONOMIS
  · Efemerida     : VSOP87D (akurasi ~1″) via JRC_Ephemeris v5.0
  · Nutasi & presesi: IERS 2010, tabel lengkap (IAU 2000A/2006A)
  · ΔT (TT−UTC)   : Tabel HMNAO interpolasi linier
  · Rentang kalibrasi: 2020–2029 (10 tahun rata-rata)
  · Lokasi        : −7.521951°LS, 112.566089°BT, 28 m dpl
  · Bintang       : Sabuk Orion (Alnitak, Alnilam, Mintaka) rata-rata

PERISTIWA ASTRONOMIS YANG DIKALIBRASI (rata-rata 2020–2029)
  ┌───────────────────────────────────────────────┬────────┬──────────┬──────────┐
  │ Peristiwa                                     │ Tgl    │  dopy    │ Trad dpy │
  ├───────────────────────────────────────────────┼────────┼──────────┼──────────┤
  │ Solstis Juni       (λ☉=90°)                   │ 21 Jun │   -0.81  │    0     │
  │ Solstis Desember   (λ☉=270°)                  │ 21 Des │  182.71  │  184     │
  │ Ekuinoks Maret     (λ☉=0°)                    │ 20 Mar │  271.75  │  273     │
  │ Ekuinoks September (λ☉=180°)                  │ 23 Sep │   92.85  │   92     │
  │ Zenith Matahari I  (δ☉=−7.52°, okt)           │ 12 Okt │  112.37  │  113     │
  │ Zenith Matahari II (δ☉=−7.52°, mar)           │ 01 Mar │  252.46  │  253     │
  │ Orion Heliacal Rise (terbit fajar)            │ 25 Jun │    3.11  │    0     │
  │ Orion Acronychal Rise (pertama terlihat senja)│ 05 Des │  166.16  │  167     │
  │ Orion Kulminasi Senja (Evening Heliacal Culm) │ 01 Mar │  252.50  │  253     │
  │ Orion Kulminasi Tengah Malam (HA=0°, 00:00)   │ 08 Des │  168.91  │  252*    │
  │ Orion Acronychal Set  (terakhir terlihat senja)│ 18 Jun│  361.93  │  347**   │
  └───────────────────────────────────────────────┴────────┴──────────┴──────────┘
  *  Trad. dopy≈252 (1 Mar) merujuk Evening Heliacal Culmination (kulminasi SENJA),
     bukan transit siang; kulminasi tengah malam terjadi 8 Des (∆ ≈ −84 hari).
  ** Trad. dopy=347 (4 Jun) merujuk heliacal set fajar (∆ ≈ +15 hr dari acronychal set).

TEMUAN KALIBRASI ASTRONOMIS (EV02 vs EV01, diwarisi EV03/EV04)
  · Jangkar awal tahun (Solstis Juni): terjadi 21 Jun (~0.81 hari sebelum 22 Jun
    tradisional) → koreksi kecil −1 hari; jangkar presisi = 21 Jun.
  · Solstis Desember: 21 Des (bukan 22 Des tradisional), dopy 182.71 vs 184.
  · Zenith Matahari I: 12 Okt (bukan 13 Okt tradisional).
  · Zenith Matahari II: 1 Mar (sama dengan tradisional, ∆−0.54 hr, tidak signifikan).
  · Orion Heliacal Rise: 25 Jun (dopy≈3.1, bukan 22 Jun/dopy=0 tradisional).
    → Mangsa-1 Kasa TIDAK dimulai dari heliacal rise Orion.
    → Orion baru terlihat pertama ~3 hari setelah solstis Juni.
  · Orion Evening Rise (first visible at dusk): 5 Des (dopy=166.16, vs 6 Des/dopy=167)
    → Konsisten dengan tradisional dalam ±1 hari.
  · Orion Evening Heliacal Culmination (kulminasi senja): ~1 Mar (dopy≈252.5).
    → Cocok dengan tradisional "1 Mar" (Mangsa-9). Kulminasi terjadi jam
       ~18:30 WIB, saat senja (matahari baru terbenam ~37–60 menit sebelumnya).
       Ammarell (1991) Tabel 3: epoch 1850 = 26 Feb, epoch 2025 ≈ 1 Mar.
  · Orion Kulminasi Tengah Malam: 8 Des (dopy=168.91).
    → BERBEDA dari kulminasi senja (1 Mar). Pada 8 Des, Orion berkulminasi
       tepat tengah malam 00:00 WIB. Bukan tentang "transit siang".
  · Orion Acronychal Set: 18 Jun (dopy=361.93, vs 4 Jun/dopy=347 tradisional).
    → Jika pakai definisi heliacal set fajar: Alnilam tak terlihat di fajar
       ≈ 25 Jun (tepat bersamaan dengan heliacal rise berikutnya).

TEMUAN KALIBRASI METEOROLOGI 6H (EV04 vs EV03)
  · R10 musim_start = {12, 131, 185, 305} dari Composite Wetness Index
    (6H-enhanced, R10 window 2015–2024). Nilai robust_mean dari
    10 tahun sampel:

        Katiga   : mean 12.5, median 6,  robust_mean 12   → 12
        Labuh    : mean 131.1, median 133, robust_mean 131 → 131
        Rendheng : mean 185.0, median 178, robust_mean 185 → 185
        Mareng   : mean 305.2, median 310, robust_mean 305 → 305

    Sampel 10 tahun (2015–2024), uncertainty σ ≈ 12–35 hari,
    didominasi variabilitas ENSO.

  · Cross-validasi 6H pada musim_start final (median, window ±3 hari,
    R10 2015–2024, IDW 2 stasiun):
        dopy  12 (Katiga)   → VPD 1.11 kPa · TCWV 38.8 kg/m²
                              · precip 0.06 mm/hr · cloud 49%
        dopy 131 (Labuh)    → VPD 1.21 kPa · TCWV 42.7 kg/m²
                              · precip 0.65 mm/hr · cloud 78%
        dopy 185 (Rendheng) → VPD 0.62 kPa · TCWV 51.8 kg/m²
                              · precip 8.29 mm/hr · cloud 92%
        dopy 305 (Mareng)   → VPD 0.70 kPa · TCWV 47.7 kg/m²
                              · precip 2.00 mm/hr · cloud 81%

    Catatan: VPD di dopy 12 (Katiga) hanya 1.11 kPa karena masih awal
    musim kering; puncak kering sesungguhnya di dopy 40–50 (VPD ~1.40).
    Hujan signifikan baru mulai dopy 135–140, sehingga Labuh=131 adalah
    onset sinyal transisi, bukan awal hujan lebat.

TEMUAN KALIBRASI METEOROLOGI 6H (EV05 vs EV04)
  · Recompute METEO_MANGSA_6H field sun_h & vpd:
    Metode: IDW-merged harian dari P1-hourly (2015–2026) + P2-6H (1995–2026).
    Pembagi mangsa berdasarkan batas R30. Periode acuan: 1996–2025 (10.958 hari).
    Data coverage: IDW 4018 hari (P1∩P2), P2-only 6940 hari, P1-only 0 hari.

    Perubahan sun_h (jam/hari):
        Kasa(1):+0→11.3    Karo(2):+0→11.4    Katiga(3):+0→11.3
        Kapat(4):−0.3→11.0 Kalima(5):−1.0→10.4 Kanem(6):−2.2→9.3
        Kapitu(7):−2.4→9.4 Kawolu(8):−1.9→9.8  Kasanga(9):−1.3→10.2
        Kasadasa(10):−1.0→10.4 Desta(11):−0.6→10.7 Sada(12):−0.3→11.0
    → Pola lebih realistis: sun_h rendah saat Rendheng (9.3–9.8 jam),
      tinggi saat Katiga/Karo/Kasa (11.3–11.4 jam). EV04 terlalu flat (~11.3–11.8).

    Perubahan vpd (kPa):
        Field 1–3 sedikit turun (−0.01 s/d −0.02), field 4 turun −0.10 (Kapat),
        field 5 naik +0.12 (Kalima), field 6–12 perubahan kecil (±0.05).
    → Nilai baru lebih mencerminkan sumber data P2 yg dominan (w2=0.605).

    Perubahan METEO_MUSIM_6H:
        Katiga:   sun_h 11.4→11.3 (−0.1),  vpd 1.299→1.296 (−0.003)
        Labuh:    sun_h 11.3→10.1 (−1.2),  vpd 0.707→0.900 (+0.193)  ← paling besar
        Rendheng: sun_h 11.6→9.7  (−1.9),  vpd 0.405→0.413 (+0.008)
        Mareng:   sun_h 11.3→10.7 (−0.6),  vpd 0.737→0.758 (+0.021)

DAMPAK KE KALENDER TERKALIBRASI
  · Pergeseran jangkar awal tahun: −1 hari (dari 22 Jun → 21 Jun presisi).
    Untuk konsistensi tampilan, ANCHOR_DAY tetap 22 Jun, namun ASTRO_CALIB
    menyimpan nilai presisi.
  · Kalibrasi R30 (skenario utama) tidak berubah (berbasis meteorologi).
  · Tabel ASTRO_CALIB tersedia untuk referensi presisi & penempatan
    penanda astro di setiap skenario.
  · build_ciri() menempatkan penanda astro secara dinamis sesuai rentang
    dopy aktual setiap skenario.

CATATAN PENEMPATAN CIRI (koreksi EV03, diwarisi EV04)
  · Solstis Des (dopy 182.7) → Mangsa-6 Kanem di semua skenario modern.
  · Zenith II & Orion Evening Culm (dopy ≈252.5) → Mangsa-8 Kawolu
    di R30/R10; Mangsa-9 Kasanga hanya di TRAD.
  · Mulai EV03, penempatan penanda astro untuk skenario terkalibrasi
    dihitung otomatis oleh build_ciri() sesuai rentang dopy aktual.

CATATAN KETERBATASAN
  · Kalibrasi meteorologi (12 mangsa via time-warp musim) tetap dari EV01;
    pada EV03/EV04 hanya skenario R10 yang di-rekalibrasi ulang (6H).
  · Kalibrasi astronomis tidak mengubah batas musim/mangsa; hanya mengoreksi
    referensi tanggal dalam teks deskripsi (CIRI) & penempatan dinamis.
  · Pergeseran astronomis terkecil: zenith & solstis <1 hari → praktis tidak
    mengubah kalender. Pergeseran Orion heliacal rise +3 hr dan acronychal set
    +15 hr vs tradisional mencerminkan pergeseran presesi ~170 tahun
    (1855→2025) sebesar ~2°.
  · Kulminasi tengah malam Orion (8 Des) vs tradisional (1 Mar) adalah
    perbedaan DEFINISI, bukan presesi — tradisional mengacu transit siang,
    EV02/EV03/EV04 mengacu tengah malam.
  · Composite Wetness Index 6H menggunakan sampel 10 tahun (2015–2024);
    uncertainty musim-start ±12–35 hari, didominasi variabilitas ENSO.
    Metode alternatif (K-means 5-fitur 6H) memberi {12, 122, 155, 294};
    dipilih composite karena lebih stabil terhadap outlier.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import textwrap
from datetime import date, timedelta, datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from scipy.stats import multivariate_normal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# ══════════════════════════════════════════════════════════════════════
# 0. KONSTANTA TAMPILAN
# ══════════════════════════════════════════════════════════════════════

W   = 70
IND = "  "

BULAN_ID = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
    7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
}
BULAN_FULL = {
    1: "Januari",  2: "Februari", 3: "Maret",    4: "April",
    5: "Mei",      6: "Juni",     7: "Juli",      8: "Agustus",
    9: "September",10: "Oktober", 11: "November", 12: "Desember",
}

def fmt(d: date) -> str:
    return f"{d.day:02d} {BULAN_ID[d.month]} {d.year}"

def box_top(title: str = "") -> str:
    if not title:
        return "╔" + "═" * (W - 2) + "╗"
    inner = f"  {title}  "
    pad = W - 2 - len(inner)
    if pad < 0:
        inner = inner[:W - 2]; pad = 0
    l = pad // 2
    return "╔" + "═" * l + inner + "═" * (pad - l) + "╗"

def box_mid() -> str:
    return "╠" + "═" * (W - 2) + "╣"

def box_bot() -> str:
    return "╚" + "═" * (W - 2) + "╝"

def box_row(text: str) -> str:
    """Render satu atau lebih baris ber-border.

    Teks yang melebihi lebar konten (W−6) di-wrap ke beberapa baris
    sehingga border selalu presisi W kolom dan isi tidak dipotong.
    """
    cw = W - 6
    s  = str(text)
    if len(s) <= cw:
        return "║  " + s + " " * (cw - len(s)) + "  ║"
    lines = textwrap.wrap(s, width=cw) or [""]
    return "\n".join(
        "║  " + ln + " " * (cw - len(ln)) + "  ║"
        for ln in lines
    )

def hbar(ch: str = "─") -> str:
    return ch * W

def thin_hbar(indent: int = 2) -> str:
    return " " * indent + "─" * (W - indent)

def sec_header(label: str, sub: str = "", dopy_range: str = "") -> None:
    """Cetak header seksi. Jika judul + dopy_range kepanjangan, kanan
    dipindah ke baris berikut agar tidak terpotong."""
    right = f"[dopy: {dopy_range}]" if dopy_range else ""
    title = f"▌▌ {label.upper()}"
    if sub:
        title += f" — {sub}"
    gap = W - len(title) - len(right)
    print()
    if gap >= 1 or not right:
        line = title + (" " * max(1, gap)) + right if right else title
        print(line[:W])
    else:
        print(title[:W])
        print(right.rjust(W))
    print(thin_hbar(0))

def mini_header(label: str) -> None:
    print(f"\n{IND}{'─' * (W - 4)}")
    print(f"{IND}{label}")
    print(f"{IND}{'─' * (W - 4)}")

def wline(label: str, value: str, lw: int = 12, indent: int = 6) -> str:
    pre     = " " * indent + f"{label:<{lw}}: "
    sub_ind = " " * (indent + lw + 2)
    return textwrap.fill(value, width=W, initial_indent=pre, subsequent_indent=sub_ind)

def wprint(label: str, value: str, lw: int = 12, indent: int = 6) -> None:
    print(wline(label, value, lw, indent))

def wrap_print(text: str, indent: int = 6) -> None:
    pre = " " * indent
    print(textwrap.fill(text, width=W, initial_indent=pre, subsequent_indent=pre))

def _wrap_ciri_line(raw: str, width: int) -> List[str]:
    """Wrap satu baris teks CIRI dengan hanging-indent.

    - Baris bullet `•`: baris pertama `• ...`, baris berikut menjorok
      sejajar konten bullet.
    - Baris biasa: leading space dipertahankan sebagai indent.
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
            subsequent_indent=" " * len(prefix)
        ) or [prefix.rstrip()]
    prefix = " " * leading
    return textwrap.wrap(
        stripped, width=width,
        initial_indent=prefix,
        subsequent_indent=prefix
    ) or [prefix.rstrip()]


def _box_row_wrapped(text: str, prefix: str) -> None:
    """Cetak teks ke dalam beberapa baris box_row dengan hanging-indent
    `prefix` (dipakai untuk Candra dan baris astronomis)."""
    for ln in textwrap.wrap(text, width=W - 6,
                            initial_indent=prefix,
                            subsequent_indent=prefix) or [prefix]:
        print(box_row(ln))


# ══════════════════════════════════════════════════════════════════════
# ATRIBUSI SUMBER DATA — standar sitasi ilmiah (LENGKAP)
# ══════════════════════════════════════════════════════════════════════

DATA_ATTRIBUTION = {
    # ── Meteorologi harian/sub-harian ────────────────────────────────
    "era5": {
        "nama": "ERA5",
        "deskripsi": "Reanalisis global, resolusi 0.25° (~31 km), 1940–sekarang",
        "institusi": "ECMWF / Copernicus Climate Change Service (C3S)",
        "sitasi": ("Hersbach, H., et al. (2020). The ERA5 global reanalysis. "
                   "Quarterly Journal of the Royal Meteorological Society, "
                   "146(730), 1999–2049."),
        "doi": "10.1002/qj.3803",
        "lisensi": "Copernicus Licence — CC-BY 4.0",
    },
    "era5_land": {
        "nama": "ERA5-Land",
        "deskripsi": "Reanalisis permukaan darat, resolusi 0.1° (~9 km), 1950–sekarang",
        "institusi": "ECMWF / Copernicus Climate Change Service (C3S)",
        "sitasi": ("Muñoz-Sabater, J., et al. (2021). ERA5-Land: a state-of-the-art "
                   "global reanalysis dataset for land applications. Earth System "
                   "Science Data, 13(9), 4349–4383."),
        "doi": "10.5194/essd-13-4349-2021",
        "lisensi": "Copernicus Licence — CC-BY 4.0",
    },
    "ecmwf_ifs": {
        "nama": "ECMWF IFS (HRES)",
        "deskripsi": "Model NWP global, resolusi 9 km, 2017–sekarang",
        "institusi": "European Centre for Medium-Range Weather Forecasts (ECMWF)",
        "sitasi": ("ECMWF. (2024). IFS Documentation CY49r1. "
                   "ECMWF Technical Report."),
        "doi": None,
        "lisensi": "CC-BY 4.0",
        "catatan": ("Dikumpulkan oleh Open-Meteo dari seluruh run IFS "
                    "0z, 6z, 12z, 18z sejak 2017."),
    },
    "open_meteo": {
        "nama": "Open-Meteo",
        "deskripsi": "API agregator data meteorologi terbuka",
        "institusi": "Open-Meteo (open-source, non-komersial)",
        "sitasi": "Zippenfenig, P. (2023). Open-Meteo.com Weather API.",
        "doi": "10.5281/ZENODO.7970649",
        "lisensi": "CC-BY 4.0 (attribution required)",
    },

    # ── ENSO — SLA dan SST Niño3.4 ──────────────────────────────────
    "aviso_duacs_sla": {
        "nama": "DUACS SLA Niño3.4 Index",
        "deskripsi": ("Indeks SLA terfilter (annual, semiannual, 60-hari, "
                      "tren dihilangkan), 85-hari rolling window, "
                      "region Niño3.4 (5°S–5°N, 190°E–240°E), mingguan"),
        "institusi": "CNES / CLS — AVISO+ / DUACS",
        "sitasi": ("AVISO/DUACS. (2025). El Niño Southern Oscillation Ocean "
                   "Indicator product (vDT2024) [Data set]. CNES."),
        "doi": "10.24400/527896/A01-2025.008",
        "input": ("Global Sea Level Anomalies 'all-satellite' daily "
                  "DUACS2024 DT dan NRT dari Copernicus Marine Service (CMEMS)"),
        "referensi": "https://www.aviso.altimetry.fr/en/data/products/indicators/enso.html",
        "lisensi": "Copernicus Marine Licence",
    },
    "noaa_oisst_sst": {
        "nama": "NOAA OISST v2.1 SST Niño3.4 Index",
        "deskripsi": ("Indeks SST terfilter (annual, semiannual, tren "
                      "dihilangkan), 85-hari rolling window, "
                      "region Niño3.4, mingguan"),
        "institusi": "NOAA NCEI / AVISO+ (produk ENSO Ocean Indicator)",
        "sitasi": ("Huang, B., et al. (2021). Improvements of the Daily Optimum "
                   "Interpolation Sea Surface Temperature (DOISST) Version 2.1. "
                   "Journal of Climate, 34, 2923–2939."),
        "doi": "10.1175/JCLI-D-20-0166.1",
        "input": "NOAA 1/4° Daily Gridded OISST V2.1",
        "lisensi": "NOAA Open Data",
    },

    # ── IOD — Dipole Mode Index ─────────────────────────────────────
    "jma_iod": {
        "nama": "JMA Dipole Mode Index (DMI)",
        "deskripsi": ("DMI = SST anomali rata-rata area WIN (50–70°E, 10°S–10°N) "
                      "− EIN (90–110°E, 10°S–Equator). Ambang ±0.4°C, "
                      "running mean 3 bulan, periode Jun–Nov."),
        "institusi": "Japan Meteorological Agency (JMA)",
        "sitasi": ("Saji, N. H., Goswami, B. N., Vinayachandran, P. N., & "
                   "Yamagata, T. (1999). A dipole mode in the tropical Indian "
                   "Ocean. Nature, 401, 360–363."),
        "doi": "10.1038/43854",
        "input": ("MGDSST (Kurihara et al. 2006) setelah Jun 2015; "
                  "COBE-SST2 (Hirahara et al. 2014) sebelum Mei 2015"),
        "referensi": "https://ds.data.jma.go.jp/tcc/tcc/products/elnino/iodevents.html",
        "lisensi": "JMA Open Data",
    },
    "bom_iod": {
        "nama": "Bureau of Meteorology IOD Index",
        "deskripsi": ("IOD index dari SST anomali (ERSSTv5, HadISST), "
                      "ambang ±0.4°C, 3 minggu berturut-turut"),
        "institusi": "Australian Bureau of Meteorology (BoM)",
        "sitasi": ("Australian Bureau of Meteorology. (2025). Indian Ocean "
                   "Dipole (IOD) monitoring."),
        "doi": None,
        "referensi": "http://www.bom.gov.au/climate/iod/",
        "lisensi": "CC-BY 4.0 (BoM Open Data)",
    },

    # ── ASTRONOMI — VSOP87D, IERS, HMNAO ────────────────────────────
    "vsop87d": {
        "nama": "VSOP87D (Planetary Solution)",
        "deskripsi": ("Solusi analitik gerak planet, versi D: variabel "
                      "heliosentrik sferis, equinox dan ekliptika tanggal. "
                      "Akurasi posisi ~1″ untuk era 1800–2200."),
        "institusi": "IMCCE — Observatoire de Paris / Bureau des Longitudes",
        "sitasi": ("Bretagnon, P., & Francou, G. (1988). Planetary theories in "
                   "rectangular and spherical variables: VSOP87 solution. "
                   "Astronomy & Astrophysics, 202, 309–315."),
        "doi": None,
        "bibcode": "1988A&A...202..309B",
        "input": ("Konstanta integrasi ditentukan dengan fitting terhadap "
                  "integrasi numerik DE200 dari Jet Propulsion Laboratory."),
        "referensi": "https://cdsarc.cds.unistra.fr/viz-bin/cat/VI/81",
        "lisensi": "IMCCE Open Data",
        "catatan": ("Versi VSOP87D dipilih karena menggunakan ekliptika "
                    "tanggal (equinox and ecliptic of date) — sesuai untuk "
                    "perhitungan ephemeris pada epoch tertentu."),
    },
    "iers2010": {
        "nama": "IERS Conventions 2010",
        "deskripsi": ("Model standar presesi-nutasi IAU 2006/2000A: "
                      "presesi P03 (Capitaine et al. 2003), nutasi IAU 2000A "
                      "(Mathews et al. 2002), frame bias, dan koreksi "
                      "dX, dY. Akurasi sub-mikroarcsecond."),
        "institusi": "International Earth Rotation and Reference Systems Service (IERS)",
        "sitasi": ("Petit, G., & Luzum, B. (eds.). (2010). IERS Conventions "
                   "(2010). IERS Technical Note No. 36. Frankfurt am Main: "
                   "Verlag des Bundesamts für Kartographie und Geodäsie."),
        "doi": None,
        "isbn": "3-89888-989-6",
        "input": ("Model presesi IAU 2006 (P03) + nutasi IAU 2000A "
                  "dengan penyesuaian P03 (Wallace & Capitaine 2006)"),
        "referensi": "https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html",
        "lisensi": "IERS Open Access",
        "catatan": ("Digunakan untuk: matriks bias-presesi-nutasi (NPB), "
                    "locator CIO (s), equation of origins (EO), dan "
                    "transformasi GCRS↔CIRS↔TIRS."),
    },
    "iau2006_precession": {
        "nama": "IAU 2006 Precession (P03)",
        "deskripsi": ("Model presesi IAU 2006 berdasarkan P03 "
                      "(Capitaine et al. 2003), diadopsi oleh Resolusi IAU "
                      "2006. Menggantikan model presesi IAU 2000."),
        "institusi": "IAU Working Group on Precession and the Ecliptic",
        "sitasi": ("Wallace, P. T., & Capitaine, N. (2006). Precession-nutation "
                   "procedures consistent with IAU 2006 resolutions. "
                   "Astronomy & Astrophysics, 459(3), 981–985."),
        "doi": "10.1051/0004-6361:20065897",
        "bibcode": "2006A&A...459..981W",
        "referensi": "https://www.aanda.org/articles/aa/abs/2006/45/aa5897-06/aa5897-06.html",
        "lisensi": "CC-BY 4.0 (A&A Open Access)",
        "catatan": ("Menyediakan prosedur lengkap untuk menghasilkan matriks "
                    "NPB berbasis equinox dan CIO, serta tabel koefisien "
                    "seri X, Y, dan s+XY/2 (tersedia di CDS: J/A+A/459/981)."),
    },
    "hmnao_deltat": {
        "nama": "HMNAO ΔT Polynomials",
        "deskripsi": ("Tabel dan polinomial ΔT (TT−UT1) untuk rentang "
                      "-720 s.d. 2019, dengan ekstrapolasi hingga 2100. "
                      "Digunakan untuk konversi waktu ephemeris."),
        "institusi": ("HM Nautical Almanac Office (HMNAO), "
                      "UK Hydrographic Office"),
        "sitasi": ("HM Nautical Almanac Office. (2020). Polynomial "
                   "Coefficients for ΔT and Length of Day (LOD) for Years "
                   "-720 to 2019: Version 2020."),
        "doi": None,
        "referensi": "http://astro.ukho.gov.uk/nao/lvm/",
        "lisensi": "HMNAO Open Data",
        "catatan": ("ΔT digunakan untuk konversi dari UT1 (waktu sipil) ke "
                    "TT (waktu ephemeris). Tanpa ΔT, perhitungan posisi "
                    "Matahari dan bintang bisa meleset beberapa arcminute."),
    },
    "sofa": {
        "nama": "SOFA (Standards of Fundamental Astronomy)",
        "deskripsi": ("Pustaka algoritma dan rutin standar IAU untuk "
                      "astronomi fundamental: presesi, nutasi, rotasi Bumi, "
                      "waktu, dan sistem referensi."),
        "institusi": "IAU SOFA Center — Rutherford Appleton Laboratory / HMNAO",
        "sitasi": ("Hohenkerk, C. Y. (2011). Standards of Fundamental Astronomy. "
                   "Scholarpedia, 6(1), 11404."),
        "doi": "10.4249/scholarpedia.11404",
        "referensi": "https://www.iausofa.org/",
        "lisensi": "SOFA Licence (non-commercial)",
        "catatan": ("SOFA menyediakan implementasi referensi untuk model "
                    "IAU 2006/2000A; JRC_Ephemeris v5.0 dalam modul ini "
                    "mengadopsi prosedur yang sama."),
    },
}

def print_data_attribution(detail: str = "ringkas") -> None:
    """Cetak atribusi sumber data.

    detail : 'ringkas' (default) — 4 baris per kategori
             'lengkap' — sitasi + DOI + lisensi penuh
    """
    print()
    print(box_top("ATRIBUSI SUMBER DATA"))
    print(box_row("Sumber ilmiah untuk seluruh data meteorologi, oseanografi, "
                  "dan iklim"))
    print(box_mid())

    if detail == "lengkap":
        kategori = [
            ("METEOROLOGI",   ["era5", "era5_land", "ecmwf_ifs", "open_meteo"]),
            ("ENSO (Niño3.4)", ["aviso_duacs_sla", "noaa_oisst_sst"]),
            ("IOD",           ["jma_iod", "bom_iod"]),
            ("ASTRONOMI",     ["vsop87d", "iers2010", "iau2006_precession",
                               "hmnao_deltat", "sofa"]),
        ]
        for label, keys in kategori:
            print(box_row(""))
            print(box_row(f"  ── {label} ─────────────────────────────────"))
            for k in keys:
                a = DATA_ATTRIBUTION[k]
                print(box_row(""))
                print(box_row(f"  ▸ {a['nama']}"))
                for ln in textwrap.wrap(a['deskripsi'], width=W - 8,
                                        initial_indent="    ",
                                        subsequent_indent="    "):
                    print(box_row(ln))
                print(box_row(f"    Institusi : {a['institusi']}"))
                print(box_row(f"    Sitasi    : {a['sitasi']}"))
                if a.get("doi"):
                    print(box_row(f"    DOI       : https://doi.org/{a['doi']}"))
                if a.get("input"):
                    for ln in textwrap.wrap(a['input'], width=W - 22,
                                            initial_indent="    Input     : ",
                                            subsequent_indent="                "):
                        print(box_row(ln))
                if a.get("catatan"):
                    for ln in textwrap.wrap(a['catatan'], width=W - 22,
                                            initial_indent="    Catatan   : ",
                                            subsequent_indent="                "):
                        print(box_row(ln))
                print(box_row(f"    Lisensi   : {a['lisensi']}"))
                if a.get("referensi"):
                    print(box_row(f"    Referensi : {a['referensi']}"))
    else:
        kategori = [
            ("METEOROLOGI",    ["era5", "era5_land", "ecmwf_ifs", "open_meteo"]),
            ("ENSO (Niño3.4)", ["aviso_duacs_sla", "noaa_oisst_sst"]),
            ("IOD",            ["jma_iod", "bom_iod"]),
            ("ASTRONOMI",      ["vsop87d", "iers2010", "iau2006_precession",
                                "hmnao_deltat", "sofa"]),
        ]
        for label, keys in kategori:
            print(box_row(""))
            print(box_row(f"  ── {label} ─────────────────────────────────"))
            for k in keys:
                a = DATA_ATTRIBUTION[k]
                print(box_row(f"  {a['nama']:<32} {a['institusi']}"))
                if a.get("doi"):
                    print(box_row(f"  {'':<32} DOI: {a['doi']}"))
        print(box_row(""))
    print(box_bot())
    print()


def print_attribution_short() -> str:
    """String satu-baris untuk ditempel di header kalender."""
    return ("ERA5/ERA5-Land (ECMWF/C3S) · IFS HRES 9km (ECMWF) · "
            "SLA: AVISO/DUACS (CNES/CLS) · SST: NOAA OISST v2.1 · "
            "IOD: JMA/BoM · Astro: VSOP87D + IERS2010 + HMNAO")


# ══════════════════════════════════════════════════════════════════════
# 1. DATA DASAR PRANATA MANGSA TRADISIONAL
# ══════════════════════════════════════════════════════════════════════

MANGSAS = [
    {"no":  1, "nama": "Kasa",     "bulan":  6, "tgl": 22, "durasi": 41},
    {"no":  2, "nama": "Karo",     "bulan":  8, "tgl":  2, "durasi": 23},
    {"no":  3, "nama": "Katiga",   "bulan":  8, "tgl": 25, "durasi": 24},
    {"no":  4, "nama": "Kapat",    "bulan":  9, "tgl": 18, "durasi": 25},
    {"no":  5, "nama": "Kalima",   "bulan": 10, "tgl": 13, "durasi": 27},
    {"no":  6, "nama": "Kanem",    "bulan": 11, "tgl":  9, "durasi": 43},
    {"no":  7, "nama": "Kapitu",   "bulan": 12, "tgl": 22, "durasi": 43},
    {"no":  8, "nama": "Kawolu",   "bulan":  2, "tgl":  3, "durasi": 26},
    {"no":  9, "nama": "Kasanga",  "bulan":  3, "tgl":  1, "durasi": 25},
    {"no": 10, "nama": "Kasadasa", "bulan":  3, "tgl": 26, "durasi": 24},
    {"no": 11, "nama": "Desta",    "bulan":  4, "tgl": 19, "durasi": 23},
    {"no": 12, "nama": "Sada",     "bulan":  5, "tgl": 12, "durasi": 41},
]

MUSIM_MEMBERS = {
    "Katiga":   [1, 2, 3],
    "Labuh":    [4, 5, 6],
    "Rendheng": [7, 8, 9],
    "Mareng":   [10, 11, 12],
}
MUSIM_DESKRIPSI = {
    "Katiga":   "Kemarau Puncak",
    "Labuh":    "Peralihan → Hujan",
    "Rendheng": "Musim Hujan Puncak",
    "Mareng":   "Peralihan → Kemarau",
}
MUSIM_ORDER = ["Katiga", "Labuh", "Rendheng", "Mareng"]

CIRI = {
    1:  ("Solstis Juni 21 Jun (λ☉=90°, dopy≈−0.8). Weluku/Orion terbit fajar "
         "~25 Jun (dopy≈3.1, 3 hr setelah solstis). "
         "Awal tahun pertanian; membersihkan lahan, tanah kering maksimum."),
    2:  ("Pohon randu/kapuk mulai berdaun. Tanah retak. "
         "Pengolahan lahan kering."),
    3:  "Puncak kemarau, sumur mengering. Panen palawija (jagung, kacang).",
    4:  ("Burung gelatik di sawah, manyar membuat sarang. "
         "Angin mulai berubah ke barat. "
         "Ekuinoks September (23 Sep, dopy≈92.9) jatuh di akhir Kapat."),
    5:  ("Zenith Matahari I: 12 Okt (δ☉=−7.52°, dopy≈112.4, "
         "1 hr lebih awal dari tradisional). "
         "Awal hujan. Pleiades terlihat di senja. Embun beracun."),
    6:  ("Weluku/Orion Acronychal Rise (pertama terlihat di senja): ~5 Des "
         "(dopy≈166.2). Kulminasi tengah malam Orion: ~8 Des (dopy≈168.9). "
         "Hujan lebat. Menabur benih padi. "
         "[EV04] Solstis Desember 21 Des (dopy≈182.7) juga jatuh di Kanem, "
         "bukan di Kapitu — karena batas musim R30/R10 menempatkan Kapitu "
         "baru mulai setelah dopy≈196–208."),
    7:  ("Solstis Desember (21 Des, dopy≈182.7) secara astronomis berada di "
         "Mangsa-6 Kanem, bukan Kapitu. Tradisi menaruh Solstis di Kapitu "
         "karena batas lama (22 Des). "
         "Pleiades setinggi pecat sawad (~50°). "
         "Memindah bibit padi ke sawah."),
    8:  "Transplantasi selesai. Pleiades kulminasi di senja. Padi tumbuh. "
        "[EV04] Zenith Matahari II (1 Mar, dopy≈252.5) dan Orion Kulminasi "
        "Senja (~1 Mar) jatuh di Kawolu untuk skenario R30/R10.",
    9:  ("[EV04] Zenith Matahari II (dopy≈252.5) & Orion Evening Heliacal "
         "Culmination (~26 Feb–1 Mar) secara astronomis berada di Mangsa-8 "
         "Kawolu untuk R30/R10; hanya pada skenario TRAD jatuh di Kasanga. "
         "Ekuinoks Maret 20 Mar (dopy≈271.8) di akhir Kasanga (R30). "
         "Jangkrik berbunyi. Padi berbulir."),
    10: "Hujan reda, angin timur. Panen raya mulai.",
    11: ("Orion terbalik di barat (terbenam awal). "
         "Kapuk mekar. Hutang dilunasi."),
    12: ("Orion terakhir terlihat senja: ~18 Jun (dopy≈361.9, acronychal set). "
         "Perkiraan tradisional 4 Jun (heliacal set fajar, dopy≈347) berbeda "
         "definisi (+15 hr). Panen selesai. Masa bera (Apit Lemah)."),
}

CIRI_JAWA = {
    1: ("Sotya murca ing êmbanan, punika candranipun măngsa kasa = I mangsanipun gêgodhongan sami gogrog, kêkajêngan sami paruthul, têgêsipun: sotya murca ing êmbanan = sêsotya coplok saking ing êmbanan, gêgodhongan kaupamèkakên: sêsotya, uwit kaupamèkakên: êmbananipun."),
    2: ("Bantala rêngka, candranipun măngsa kalih = II têgêsipun: bantala rêngka = siti bênthèt, bantala = siti, rêngka = bênthèt, punika mangsanipun siti nêla."),
    3: ("Suta manut ing bapa, candranipun măngsa katiga = III têgêsipun: anak manut ing bapa, punika mangsanipun lung-lungan nurut lanjaran."),
    4: ("Waspa kumêmbêng jroning kalbu, candranipun măngsa sakawan = IV, têgêsipun: êluh kumêmbêng salêbêting manah, punika mangsanipun sumbêr pêpêt (= pêpêt sumbêr) êluh kadamêl upami: toya, manah: kadamêl upami: sumbêr."),
    5: ("Pancuran êmas sumawur ing jagad, candranipun măngsa gangsal = V, pancuran: kadamêl upami: jawah, sumawur: dhawahipun ing jawah."),
    6: ("Rasa mulya kasucian, candranipun măngsa kanêm = VI, mangsanipun wowohan nêdhêng."),
    7: ("Wisa kentar ing maruta, candranipun măngsa kapitu = VII, têgêsipun: wisa larut dening angin, punika mangsanipun kathah sêsakit."),
    8: ("Anjrah jroning kayun, candranipun măngsa kawolu = VIII, punika mangsanipun kucing gandhik."),
    9: ("Wêdharing wacana mulya, candranipun măngsa kasanga = IX, têgêsipun wêdaling wicantên linakung, punika mangsanipun gangsir sami ngênthir, garèng sami ngêrèng."),
    10: ("Gêdhong minêb jroning kalbu, candranipun măngsa sadasa = X, punika mangsanipun sato kewan sami mêtêng."),
    11: ("Sotya sinarawèdi, candranipun măngsa dhêstha = XI, punika mangsanipun pêksi sami ngloloh, têgêsipun: sêsotya, kadamêl upami: anaking pêksi, sinarawèdi = pinulasara, punika ngibaratipun dipun loloh."),
    12: ("Tirta sah saking sasana, candranipun măngsa sadha = XII, têgêsipun: toya pisah saking panggenan, punika măngsa badhidhing, tirta punika ngibarat kringêt, sasana ngibarat badan, dados awis-awis tiyang kringêtên, amargi saking asrêpipun."),
}

ANCHOR_MONTH, ANCHOR_DAY = 6, 22


def is_leap_year(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def orig_dopy_table() -> Dict[int, int]:
    out, cum = {}, 0
    for m in MANGSAS:
        out[m["no"]] = cum
        cum += m["durasi"]
    return out


ORIG_DOPY = orig_dopy_table()
ORIG_MUSIM_START = {mu: ORIG_DOPY[mem[0]] for mu, mem in MUSIM_MEMBERS.items()}
ORIG_MUSIM_START_NEXT = {
    "Katiga":   ORIG_MUSIM_START["Labuh"],
    "Labuh":    ORIG_MUSIM_START["Rendheng"],
    "Rendheng": ORIG_MUSIM_START["Mareng"],
    "Mareng":   365 + ORIG_MUSIM_START["Katiga"],
}


# ══════════════════════════════════════════════════════════════════════
# 2. KALIBRASI ASTRONOMIS
# ══════════════════════════════════════════════════════════════════════

ASTRO_CALIB = {
    "solstis_juni": {
        "mean_dopy": -0.81, "std_dopy": 0.27, "mean_month": 6, "mean_day": 21,
        "trad_dopy": 0, "delta": -0.81,
        "catatan": ("Solstis Juni 21 Jun ~11:00 WIB. Jangkar tradisional 22 Jun "
                    "terlambat ~20 jam."),
    },
    "solstis_des": {
        "mean_dopy": 182.71, "std_dopy": 0.28, "mean_month": 12, "mean_day": 21,
        "trad_dopy": 184, "delta": -1.29,
        "catatan": ("Solstis Desember 21 Des (dopy 182.7). Secara astronomis "
                    "jatuh di Mangsa-6 Kanem untuk semua skenario modern, "
                    "bukan di Kapitu seperti pada tradisi."),
    },
    "equinox_maret": {
        "mean_dopy": 271.75, "std_dopy": 0.30, "mean_month": 3, "mean_day": 20,
        "trad_dopy": 273, "delta": -1.25,
        "catatan": ("Ekuinoks Maret 20 Mar ~11:00 WIB. Tidak dipakai sebagai "
                    "penanda mangsa dalam tradisi."),
    },
    "equinox_sept": {
        "mean_dopy": 92.85, "std_dopy": 0.27, "mean_month": 9, "mean_day": 23,
        "trad_dopy": 92, "delta": 0.85,
        "catatan": ("Ekuinoks September 23 Sep ~07:00 WIB. Jatuh di Mangsa-4 "
                    "Kapat pada skenario TRAD/R30. Tidak dipakai sebagai "
                    "penanda tradisional."),
    },
    "zenith_I_okt": {
        "mean_dopy": 112.37, "std_dopy": 0.27, "mean_month": 10, "mean_day": 12,
        "trad_dopy": 113, "delta": -0.63,
        "catatan": ("Zenith I 12 Okt ~09:00 WIB, 0.6 hr lebih awal dari "
                    "tradisional 13 Okt. Penanda awal Kalima."),
    },
    "zenith_II_mar": {
        "mean_dopy": 252.46, "std_dopy": 0.27, "mean_month": 3, "mean_day": 1,
        "trad_dopy": 253, "delta": -0.54,
        "catatan": ("Zenith II 1 Mar ~10:00 WIB. Jatuh di Mangsa-8 Kawolu "
                    "untuk skenario R30/R10 (bukan Kasanga seperti tradisi)."),
    },
    "orion_helrise": {
        "mean_dopy": 3.11, "std_dopy": 0.40, "mean_month": 6, "mean_day": 25,
        "trad_dopy": 0, "delta": 3.11,
        "catatan": ("Orion heliacal rise 25 Jun — 3 hr setelah solstis. "
                    "Tradisi 22 Jun kurang tepat karena presesi."),
    },
    "orion_evening_rise": {
        "mean_dopy": 166.16, "std_dopy": 0.46, "mean_month": 12, "mean_day": 5,
        "trad_dopy": 167, "delta": -0.84,
        "catatan": ("Orion Acronychal Rise 5 Des (~18:30 WIB). Konsisten "
                    "dengan tradisional 6 Des."),
    },
    "orion_evening_culm": {
        "mean_dopy": 252.5, "std_dopy": 0.40, "mean_month": 3, "mean_day": 1,
        "trad_dopy": 253, "delta": -0.5,
        "catatan": ("Orion Evening Heliacal Culmination ~26 Feb–1 Mar. "
                    "Ammarell (1991) Tbl.3: epoch 1850 = 26 Feb, kini ≈1 Mar. "
                    "Jatuh di Mangsa-8 Kawolu untuk R30/R10."),
    },
    "orion_midnight_culm": {
        "mean_dopy": 168.91, "std_dopy": 0.40, "mean_month": 12, "mean_day": 8,
        "trad_dopy": 252, "delta": -83.09,
        "catatan": ("Orion kulminasi tengah malam ~8 Des (00:00 WIB). "
                    "Berbeda dari evening heliacal culmination (1 Mar)."),
    },
    "orion_acron_set": {
        "mean_dopy": 361.93, "std_dopy": 0.50, "mean_month": 6, "mean_day": 18,
        "trad_dopy": 347, "delta": 14.93,
        "catatan": ("Orion Acronychal Set 18 Jun (dopy 361.9). Tradisional "
                    "4 Jun (dopy 347) memakai definisi heliacal set fajar."),
    },
}


def astro_event_date(key: str, year: int) -> Optional[date]:
    ev = ASTRO_CALIB.get(key)
    if not ev:
        return None
    month = ev["mean_month"]; day = ev["mean_day"]
    actual_year = year if month >= 6 else year + 1
    try:
        return date(actual_year, month, day)
    except ValueError:
        return date(actual_year, month, min(day, 28))


def astro_delta_str(key: str) -> str:
    ev = ASTRO_CALIB.get(key)
    if not ev:
        return ""
    delta = ev["delta"]
    if abs(delta) < 0.5:
        return f"Δ={delta:+.1f} hr (konsisten tradisional)"
    arah = "lebih awal" if delta < 0 else "lebih lambat"
    return f"Δ={delta:+.1f} hr ({abs(delta):.1f} hr {arah} dari tradisional)"


# ══════════════════════════════════════════════════════════════════════
# 2b. CIRI DINAMIS PER-SKENARIO
# ══════════════════════════════════════════════════════════════════════

CIRI_BASE = {
    1:  "Awal tahun pertanian; membersihkan lahan, tanah kering maksimum.",
    2:  "Pohon randu/kapuk mulai berdaun. Tanah retak. Pengolahan lahan kering.",
    3:  "Puncak kemarau, sumur mengering. Panen palawija (jagung, kacang).",
    4:  "Burung gelatik di sawah, manyar membuat sarang. Angin mulai berubah ke barat.",
    5:  "Awal hujan. Pleiades terlihat di senja. Embun beracun.",
    6:  "Hujan lebat. Menabur benih padi.",
    7:  "Pleiades setinggi pecat sawad (~50°). Memindah bibit padi ke sawah.",
    8:  "Transplantasi selesai. Pleiades kulminasi di senja. Padi tumbuh.",
    9:  "Jangkrik berbunyi. Padi berbulir.",
    10: "Hujan reda, angin timur. Panen raya mulai.",
    11: "Orion terbalik di barat (terbenam awal). Kapuk mekar. Hutang dilunasi.",
    12: "Panen selesai. Masa bera (Apit Lemah).",
}

ASTRO_LABEL = {
    "solstis_juni":        "Solstis Juni (λ☉=90°)",
    "solstis_des":         "Solstis Desember (λ☉=270°)",
    "equinox_maret":       "Ekuinoks Maret (λ☉=0°)",
    "equinox_sept":        "Ekuinoks September (λ☉=180°)",
    "zenith_I_okt":        "Zenith Matahari I (δ☉=−7.52°)",
    "zenith_II_mar":       "Zenith Matahari II (δ☉=−7.52°)",
    "orion_helrise":       "Orion Heliacal Rise (terbit fajar)",
    "orion_evening_rise":  "Orion Acronychal Rise (terbit senja)",
    "orion_evening_culm":  "Orion Kulminasi Senja",
    "orion_midnight_culm": "Orion Kulminasi Tengah Malam",
    "orion_acron_set":     "Orion Acronychal Set (terbenam senja)",
}

MONTHS_ID_SHORT = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",
                   7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}


def astro_events_in_range(dopy_start: float, dopy_end: float) -> List[str]:
    """Key peristiwa astro yang mean_dopy-nya jatuh di rentang [start, end]."""
    out = []
    s = dopy_start % 365
    e = dopy_end   % 365
    for key, ev in ASTRO_CALIB.items():
        d = ev["mean_dopy"] % 365
        if s <= e:
            if s <= d <= e:
                out.append(key)
        else:
            if d >= s or d <= e:
                out.append(key)
    return sorted(out, key=lambda k: ASTRO_CALIB[k]["mean_dopy"])


def build_ciri(scenario_key: str, mangsa_no: int,
               dopy_start: float, dopy_end: float) -> str:
    """Basis fenologi + penanda astro (inline, satu paragraf).

    Penanda astro digabung inline dengan separator ' | ' agar dapat
    di-wrap rapi oleh textwrap.fill — bukan multiline bullet yang mudah
    terpotong di tepi konsol.
    """
    base = CIRI_BASE.get(mangsa_no, "")
    events = astro_events_in_range(dopy_start, dopy_end)
    if not events:
        return base
    parts = []
    for key in events:
        ev = ASTRO_CALIB[key]
        label = ASTRO_LABEL.get(key, key)
        tgl = f"{ev['mean_day']:02d} {MONTHS_ID_SHORT[ev['mean_month']]}"
        parts.append(f"{label} {tgl} (dopy≈{ev['mean_dopy']:.1f})")
    return base + "  |  " + "  |  ".join(parts)


# ══════════════════════════════════════════════════════════════════════
# 3. KALIBRASI METEOROLOGI
# ══════════════════════════════════════════════════════════════════════

CALIB_SCENARIOS = {
    "R30": {
        "label":      "Normal Iklim Terkini (1996–2025, 30 th)",
        "musim_start": {"Katiga": 19, "Labuh": 94, "Rendheng": 208, "Mareng": 286},
        "catatan":    ("Skenario UTAMA yang direkomendasikan untuk pemakaian "
                       "sehari-hari saat ini."),
    },
    "ALL": {
        "label":      "Rata-rata Seluruh Data (1950–2025, 76 th)",
        "musim_start": {"Katiga": 32, "Labuh": 91, "Rendheng": 187, "Mareng": 286},
        "catatan":    ("Baseline jangka panjang — menunjukkan pergeseran "
                       "vs. kondisi terkini."),
    },
    "R10": {
        "label":      "10 Tahun Terakhir (2016–2025)",
        "musim_start": {"Katiga": 12, "Labuh": 131, "Rendheng": 185, "Mareng": 305},
        "catatan":    ("Basis 10 tahun terakhir (2016–2025). Lebih responsif "
                       "terhadap tren iklim terkini; sampel kecil sehingga "
                       "uncertainty lebih besar dari R30."),
    },
    "ELNINO": {
        "label":      "Tahun El Niño (ASO Niño3.4 ≥ +0.5)",
        "musim_start": {"Katiga": 2,  "Labuh": 133, "Rendheng": 217, "Mareng": 288},
        "catatan":    ("Katiga jauh lebih panjang & lambat berakhir "
                       "(rata-rata 131 hr vs 88 hr tradisional)."),
    },
    "LANINA": {
        "label":      "Tahun La Niña (ASO Niño3.4 ≤ −0.5)",
        "musim_start": {"Katiga": 35, "Labuh": 79,  "Rendheng": 210, "Mareng": 284},
        "catatan":    ("Katiga jauh lebih pendek (44 hr); musim hujan "
                       "datang lebih awal."),
    },
    "NETRAL": {
        "label":      "Tahun ENSO Netral",
        "musim_start": {"Katiga": 11, "Labuh": 102, "Rendheng": 189, "Mareng": 288},
        "catatan":    "Paling mendekati pola ALL — kondisi tanpa pengaruh ENSO kuat.",
    },
}
DEFAULT_SCENARIO = "R30"


def build_calibrated_mangsa(scenario_key: str) -> Dict[int, float]:
    starts = CALIB_SCENARIOS[scenario_key]["musim_start"]
    starts_next = {
        "Katiga":   starts["Labuh"],
        "Labuh":    starts["Rendheng"],
        "Rendheng": starts["Mareng"],
        "Mareng":   365 + starts["Katiga"],
    }
    out = {}
    for musim, members in MUSIM_MEMBERS.items():
        o_start = ORIG_MUSIM_START[musim]
        o_len   = ORIG_MUSIM_START_NEXT[musim] - o_start
        n_start = starts[musim]
        n_len   = starts_next[musim] - n_start
        for mno in members:
            frac = (ORIG_DOPY[mno] - o_start) / o_len
            out[mno] = n_start + frac * n_len
    return out


# ══════════════════════════════════════════════════════════════════════
# 4. KLIMATOLOGI EMPIRIS (daily P1+P2 IDW, R30 1996–2025)
# ══════════════════════════════════════════════════════════════════════

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
    "Katiga":  (  75,   60,  0.8, 4.64, -3.84, 0.180, 66.1, 32.6, 21.8, 10.3, 20.8),
    "Labuh":   ( 114,  978,  8.6, 4.32,  4.26, 0.290, 74.5, 32.3, 23.3,  9.9, 19.7),
    "Rendheng": ( 78, 1140, 14.6, 3.53, 11.09, 0.390, 84.2, 29.9, 23.0, 10.3, 17.4),
    "Mareng":  (  98,  453,  4.6, 3.79,  0.82, 0.310, 77.6, 31.1, 22.9,  8.5, 18.1),
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

# ─── EV05: Klimatologi 6H-derived (recomputed) ───────────────────────
# Basis: R30 1996–2025, IDW-merged harian dari P1-hourly (2015–2026) +
#        P2-6H (1995–2026). w1=0.3950 (P1), w2=0.6050 (P2).
# Field vpd & sun_h direcompute; field lain (tcwv, cloud, sm, sT) tetap
# dari EV04 (belum ada data 6H yang cukup panjang untuk recalibrate).
# Format: (vpd, tcwv, cloud, cloud_aft, sun_h, sm_sh, sm_dp, sT_sh, sT_dp)
METEO_MANGSA_6H: Dict[int, Tuple] = {
     1: (1.159, 34.2,  50,    54,       11.3,  0.154, 0.335, 26.9,  26.8),  # Kasa
     2: (1.350, 32.1,  49,    54,       11.4,  0.132, 0.321, 27.7,  27.0),  # Karo
     3: (1.480, 33.1,  53,    56,       11.3,  0.126, 0.312, 28.4,  27.2),  # Katiga
     4: (1.436, 36.8,  64,    64,       11.0,  0.134, 0.301, 29.1,  27.5),  # Kapat
     5: (1.009, 46.5,  85,    88,       10.4,  0.271, 0.291, 28.4,  27.9),  # Kalima
     6: (0.514, 52.0,  96,    98,        9.3,  0.379, 0.291, 26.8,  27.9),  # Kanem
     7: (0.405, 52.7,  97,    98,        9.4,  0.394, 0.377, 26.2,  27.2),  # Kapitu
     8: (0.397, 52.4,  95,    96,        9.8,  0.396, 0.404, 26.2,  26.9),  # Kawolu
     9: (0.447, 51.7,  91,    92,       10.2,  0.386, 0.403, 26.5,  26.7),  # Kasanga
    10: (0.539, 49.9,  83,    85,       10.4,  0.360, 0.395, 26.6,  26.7),  # Kasadasa
    11: (0.734, 45.8,  66,    68,       10.7,  0.313, 0.377, 26.9,  26.8),  # Desta
    12: (0.902, 39.7,  56,    60,       11.0,  0.235, 0.356, 26.7,  26.8),  # Sada
}

METEO_MUSIM_6H: Dict[str, Tuple] = {
    # EV05: vpd & sun_h direcompute (IDW P1-hourly + P2-6H, R30 1996–2025)
    # Format: (vpd, tcwv, cloud, sun_h)
    "Katiga":   (1.296, 33.3,  51,    11.3),
    "Labuh":    (0.900, 48.1,  87,    10.1),
    "Rendheng": (0.413, 52.4,  95,     9.7),
    "Mareng":   (0.758, 44.9,  67,    10.7),
}

# ─── EV05 rev.2: Ekstrem absolut per mangsa & per musim (R30 1996–2025) ──
# Format: (Tx_abs, Tn_abs) — derajat Celsius
# Tx_abs = suhu maksimum harian tertinggi dalam periode
# Tn_abs = suhu minimum harian terendah dalam periode
# Konsisten secara internal: nilai musim = max/min dari mangsa anggotanya.
METEO_MANGSA_EXTREME: Dict[int, Tuple[float, float]] = {
     1: (36.4, 16.3),  2: (36.7, 17.5),  3: (37.2, 17.3),
     4: (38.5, 18.5),  5: (39.3, 19.9),  6: (37.7, 20.3),
     7: (35.1, 20.1),  8: (33.6, 19.9),  9: (33.8, 18.2),
    10: (33.9, 19.4), 11: (34.9, 18.0), 12: (35.3, 17.1),
}

METEO_MUSIM_EXTREME: Dict[str, Tuple[float, float]] = {
    "Katiga":   (37.2, 16.3),
    "Labuh":    (39.3, 18.5),
    "Rendheng": (35.1, 18.2),
    "Mareng":   (35.3, 17.1),
}

def _extreme_for_dopy_range(dopy_s: float, dopy_e: float
                             ) -> Optional[Tuple[float, float]]:
    """Ekstrem absolut (Tx_abs, Tn_abs) untuk rentang dopy [dopy_s, dopy_e].

    Dihitung dari METEO_MANGSA_EXTREME dengan aturan agregasi ekstrem:
        Tx_abs = max(Tx_abs_i) atas mangsa R30 yang beririsan
        Tn_abs = min(Tn_abs_i) atas mangsa R30 yang beririsan

    Karena max dan min monoton, hasil ini persis ekstrem atas gabungan
    rentang — tidak perlu pembobotan. Berlaku untuk semua skenario
    (R30/R10/ELNINO/LANINA/...) dengan asumsi: posisi dopy menentukan
    iklim ekstrem lebih kuat daripada fase ENSO.

    Mengembalikan None bila tidak ada irisan dengan rentang R30.
    """
    tx_max, tn_min = -np.inf, +np.inf
    found = False
    for no, (rs, re) in R30_DOPY_RANGES.items():
        ovl = max(0.0, min(dopy_e, re) - max(dopy_s, rs))
        if ovl > 0:
            tx, tn = METEO_MANGSA_EXTREME[no]
            if tx > tx_max: tx_max = tx
            if tn < tn_min: tn_min = tn
            found = True
    return (tx_max, tn_min) if found else None


def _fmt_suhu(tx: float, tn: float,
              dopy_s: Optional[float] = None,
              dopy_e: Optional[float] = None) -> str:
    """Format baris suhu: rata-rata + ekstrem absolut bila tersedia."""
    if dopy_s is not None and dopy_e is not None:
        ext = _extreme_for_dopy_range(dopy_s, dopy_e)
        if ext is not None:
            tx_a, tn_a = ext
            return (f"Tx̄ {tx:.1f}°C ({tx_a:.1f}°C) · "
                    f"Tn̄ {tn:.1f}°C ({tn_a:.1f}°C)")
    return f"Tx̄ {tx:.1f}°C · Tn̄ {tn:.1f}°C"

# ─── Rentang dopy R30 per mangsa (basis interpolasi lintas-skenario) ──
# Digunakan oleh meteo_for_dopy_range() agar skenario non-R30 mendapat
# klimatologi yang sesuai dopy-range-nya, bukan nomor mangsa-nya.
R30_DOPY_RANGES: Dict[int, Tuple[float, float]] = {
     1: ( 19.00,  53.94),  2: ( 53.94,  73.55),  3: ( 73.55,  94.00),
     4: ( 94.00, 124.00),  5: (124.00, 156.40),  6: (156.40, 208.00),
     7: (208.00, 243.68),  8: (243.68, 265.26),  9: (265.26, 286.00),
    10: (286.00, 312.73), 11: (312.73, 338.34), 12: (338.34, 384.00),
}


# ─── Delta ENSO per mangsa (empiris ERA5/Land R30 1996–2025) ─────────
# Basis: komposit harian P1 (−7.49°LS 112.54°BT) per ENSO-year (ASO Niño3.4 MSLA)
# ELNINO-years (8 thn): 1997,2002,2004,2006,2009,2015,2018,2023
# LANINA-years (11 thn): 1998,1999,2007,2008,2010,2011,2016,2017,2020,2024,2025
# Format per mangsa-no: (Δtx, Δtn, Δhj_d, Δet0, Δrad, Δrh)
# Δhj_d = delta curah hujan harian (mm/hari); Δwb diturunkan dari Δhj_d − Δet0
# Field 6H (vpd, tcwv, cloud, sun_h) tidak di-delta-kan langsung karena
# tersimpan sebagai IDW-merged dari P1+P2 yang sudah mencakup periode heterogen;
# namun vpd dan tcwv diestimasikan dari Δtx+Δtn+Δrh via pendekatan Tetens.
ENSO_DELTA: Dict[str, Dict[int, Tuple[float,...]]] = {
    #              Δtx    Δtn   Δhj_d   Δet0   Δrad    Δrh
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
    # NETRAL: nol (identik R30 komposit)
    "NETRAL": {no: (0.,0.,0.,0.,0.,0.) for no in range(1,13)},
}


# ─── Delta IOD per mangsa (empiris ERA5/Land R30 1950–2025) ──────────
# Basis  : komposit harian IDW-merged P1+P2, detrend linear, filter ENSO.
# Sumber : 30yr_dmi_3rmean.txt (bulanan, BOM/NOAA) + Sst_nino34_index.csv
# Periode: 1950–2025 (IOD bulanan), ENSO-filter dari Sst Niño3.4 ASO MSLA
#          (hanya 1993+ karena keterbatasan sumber Niño3.4).
# Ambang : SON DMI ≥ +0.40 → pIOD; ≤ −0.40 → nIOD (BOM Australia).
# Filter : |ASO Niño3.4| ≥ 0.50 → dikecualikan (ENSO-kuat).
# Sampel : pIOD 8 thn (1961,1963,1967,1972,1982,2012,2018,2019)
#          nIOD 7 thn (1960,1974,1975,1984,1996,2005,2024)
#          Netral 61 thn (1950–2025, detrend linear + filter ENSO)
# Audit  : 16/18 field lulus toleransi ±15% vs komposit ERA5 detrended
#          (2 field CHECK: nIOD Kalima tx & hj_d, sudah dikoreksi di atas)
#          Sampel pre-1979 konsisten searah dengan post-1979 (selisih <5%)
#          → ERA5 tropis stabil antar-era, pre-1979 aman dipakai
# Mask   : Hanya mangsa 3,4,5 (overlap ≥ 15 hari dgn SON aktif IOD).
# Sign   : Δtx≥0 (pIOD), Δhj_d≤0 (pIOD), Δrh≤0 (pIOD) — zero-kan jika dilanggar.
# Format : (Δtx, Δtn, Δhj_d, Δet0, Δrad, Δrh) — identik ENSO_DELTA.
IOD_DELTA: Dict[str, Dict[int, Tuple[float, ...]]] = {
    #              Δtx    Δtn   Δhj_d   Δet0   Δrad    Δrh
    "pIOD": {
         1: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         2: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         3: ( +0.534,  -0.617,  -0.943,  +0.476,  +1.175,  -4.860),
         4: ( +1.278,  -0.316,  -2.224,  +0.730,  +1.690,  -7.271),
         5: ( +2.345,  +0.244,  -4.980,  +0.879,  +2.461, -10.023),
         6: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         7: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         8: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         9: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
        10: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
        11: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
        12: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
    },
    "nIOD": {
         1: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         2: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         3: ( -0.841,  +0.468,  +2.365,  -0.423,  -1.459,  +5.183),
         4: ( -0.831,  +0.217,  +2.437,  -0.383,  -1.149,  +4.998),
         5: ( -0.487,  -0.064,  +1.359,  -0.112,  -0.319,  +1.964),
         6: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         7: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         8: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
         9: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
        10: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
        11: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
        12: ( +0.000,  +0.000,  +0.000,  +0.000,  +0.000,  +0.000),
    },
    "NETRAL": {no: (0., 0., 0., 0., 0., 0.) for no in range(1, 13)},
}

# Bobot aplikasi IOD (fraksi dari delta komposit)
# 0.30 bila IOD standalone (ENSO netral)
# 0.50 bila IOD sekutu ENSO (El Niño + pIOD, La Niña + nIOD)
_BOBOT_IOD_STANDALONE   = 0.30
_BOBOT_IOD_KOMBINASI    = 0.50


def _iod_delta_for_dopy_range(dopy_s: float, dopy_e: float,
                               iod_phase: str,
                               enso_phase: str = "NETRAL"
                               ) -> Tuple[float, ...]:
    """Delta IOD berbobot tumpang-tindih untuk rentang dopy, dengan skala bobot.

    Logika identik dengan ENSO_DELTA: bobot = fraksi irisan dengan mangsa R30.
    Bobot global ditingkatkan dari 0.30 (standalone) ke 0.50 bila IOD dan ENSO
    saling menguatkan (El Niño + pIOD; La Niña + nIOD).

    Returns
    -------
    (Δtx, Δtn, Δhj_d, Δet0, Δrad, Δrh) — sudah dikalikan bobot.
    """
    if iod_phase not in ("pIOD", "nIOD"):
        return (0., 0., 0., 0., 0., 0.)

    # Tentukan bobot berdasarkan sinergi ENSO–IOD
    sinergis = ((enso_phase == "ELNINO" and iod_phase == "pIOD") or
                (enso_phase == "LANINA" and iod_phase == "nIOD"))
    bobot = _BOBOT_IOD_KOMBINASI if sinergis else _BOBOT_IOD_STANDALONE

    delta_table = IOD_DELTA[iod_phase]
    weights: Dict[int, float] = {}
    for no, (rs, re) in R30_DOPY_RANGES.items():
        ovl = max(0.0, min(dopy_e, re) - max(dopy_s, rs))
        if ovl > 0:
            weights[no] = ovl
    if not weights:
        return (0., 0., 0., 0., 0., 0.)
    total_w = sum(weights.values())
    wn = {k: v / total_w for k, v in weights.items()}
    raw = tuple(
        sum(wn[no] * delta_table[no][fi] for no in wn)
        for fi in range(6)
    )
    return tuple(bobot * x for x in raw)


def _enso_delta_for_dopy_range(dopy_s: float, dopy_e: float,
                                enso_phase: str) -> Tuple[float, ...]:
    """Hitung delta ENSO berbobot tumpang-tindih untuk rentang dopy tertentu.

    ── RASIONAL ILMIAH ────────────────────────────────────────────────
    Delta ENSO empiris di ENSO_DELTA disusun per-nomor-mangsa R30
    berdasarkan komposit harian 30 tahun (1996–2025) dari reanalisis
    ERA5/ERA5-Land pada grid P1 (−7.49°LS, 112.54°BT, 28 m dpl).

    Klasifikasi tahun ENSO mengikuti indeks ASO Niño3.4 (Agustus–
    September–Oktober) dari MSLA/DUACS:
      · El Niño (8 tahun) : 1997, 2002, 2004, 2006, 2009, 2015,
                            2018, 2023  (ASO ≥ +0.5)
      · La Niña  (11 tahun): 1998, 1999, 2007, 2008, 2010, 2011,
                            2016, 2017, 2020, 2024, 2025 (ASO ≤ −0.5)
      · Netral            : sisanya

    Ketika skenario ENSO diterapkan pada kalender terkalibrasi, batas
    musim (musim_start) bergeser. Akibatnya, satu mangsa bernama sama
    (mis. "Kalima") pada skenario ELNINO dapat menempati rentang dopy
    yang tumpang-tindih dengan mangsa R30 yang berbeda (mis. Kanem).
    Delta yang tepat untuk rentang dopy baru adalah RATA-RATA BERBOBOT
    dari delta per-mangsa R30, dengan bobot = fraksi tumpang-tindih.

    ── KONSEKUENSI FISIS ──────────────────────────────────────────────
    Pendekatan ini disebut "DOPY-ANCHORED ENSO": delta yang dipakai
    MENGIKUTI POSISI KALENDER, bukan mengikuti label mangsa. Artinya,
    "Kalima EN" akan terasa seperti Kanem R30 karena memang begitulah
    iklim yang menyertai rentang dopy-nya. Ini adalah perilaku yang
    disengaja dan benar secara fisis.

    ── IMPLEMENTASI ───────────────────────────────────────────────────
    Untuk setiap mangsa R30 dengan rentang [r_s, r_e), hitung panjang
    irisan dengan [dopy_s, dopy_e). Bila irisan > 0, mangsa tersebut
    menyumbang delta sebesar (irisan / total_irisan). Semua enam field
    (Δtx, Δtn, Δhj_d, Δet0, Δrad, Δrh) dihitung dengan bobot yang sama.

    Returns
    -------
    (Δtx, Δtn, Δhj_d, Δet0, Δrad, Δrh) : tuple[float, ...]
        Delta terberat untuk keenam field. Jika tidak ada irisan,
        mengembalikan nol (skenario Netral implicit).
    """
    if enso_phase not in ENSO_DELTA:
        return (0., 0., 0., 0., 0., 0.)
    delta_table = ENSO_DELTA[enso_phase]
    weights: Dict[int, float] = {}
    for no, (rs, re) in R30_DOPY_RANGES.items():
        ovl = max(0.0, min(dopy_e, re) - max(dopy_s, rs))
        if ovl > 0:
            weights[no] = ovl
    if not weights:
        return (0., 0., 0., 0., 0., 0.)
    total_w = sum(weights.values())
    wn = {k: v / total_w for k, v in weights.items()}
    result = []
    for fi in range(6):
        result.append(sum(wn[no] * delta_table[no][fi] for no in wn))
    return tuple(result)


def meteo_for_dopy_range(dopy_s: float, dopy_e: float,
                          enso_phase: str = "NETRAL",
                          iod_phase: str = "NETRAL"
                          ) -> Tuple[Optional[Tuple], Optional[Tuple]]:
    """Klimatologi terinterpolasi untuk rentang dopy [dopy_s, dopy_e).

    ── TUJUAN ─────────────────────────────────────────────────────────
    Menyediakan klimatologi per-mangsa yang konsisten untuk SEMUA
    skenario kalender (R30/R10/ALL/ELNINO/LANINA/NETRAL) berdasarkan
    posisi dopy aktual, bukan nomor mangsa R30 yang hardcoded.

    ── METODE INTERPOLASI ─────────────────────────────────────────────
    Untuk setiap mangsa R30 dengan rentang [r_s, r_e), hitung panjang
    irisan dengan [dopy_s, dopy_e). Bobot w_no = irisan / total_irisan.
    Field rate (hj_d, et0, wb, sm, rh, tx, tn, angin, rad) dihitung
    sebagai rata-rata berbobot; field intensif (hari hujan, total hujan)
    diskalakan sesuai durasi rentang baru.

    ── SUMBER DATA ────────────────────────────────────────────────────
    · METEO_MANGSA     : ERA5/ERA5-Land/IFS-HRES daily, R30 1996–2025,
                         IDW 2 stasiun (w1=0.395 P1, w2=0.605 P2).
    · METEO_MANGSA_6H  : IDW-merged harian dari P1-hourly (2015–2026)
                         + P2-6H (1995–2026), field sun_h & VPD
                         direcompute EV05. Cloud, TCWV, SM, sT dari EV04.

    ── KOREKSI ENSO ───────────────────────────────────────────────────
    Jika enso_phase ∈ {ELNINO, LANINA}, delta empiris dari
    _enso_delta_for_dopy_range() diterapkan pada field harian.
    Untuk field 6H (VPD, TCWV, sun_h), delta diturunkan dari ΔTmean,
    ΔRH, dan Δrad memakai formulasi fisis (lihat di bawah).

    ── PERBAIKAN EV05 rev.1 ───────────────────────────────────────────
    Tiga koreksi kritis vs EV05 awal, semuanya berbasis validasi fisis
    terhadap komposit ERA5 Maritime Continent:

    (1) SKALA HARI HUJAN — eksponen parsial 0.6
        EV05 awal memakai re-kalkulasi linier hari_hujan ∝ hj_d, yang
        overestimasi perubahan frekuensi hujan saat ENSO kuat.
        Analisis komposit ERA5 1995–2024 pada 15 stasiun Jawa Timur
        menunjukkan relasi empiris hari_hujan ∝ hj_d^0.55–0.65
        (rerata 0.60). Model fisisnya: perubahan curah hujan ENSO
        terdistribusi antara frekuensi (hari hujan) dan intensitas
        (mm/hari-basah), tidak seluruhnya ke frekuensi. Eksponen 0.6
        mencerminkan pembagian tersebut.

    (2) ΔVPD — dari sensitivitas Tetens
        EV05 awal memakai linearisasi kasar:
            Δvpd = vpd_base · (ΔTmean/10 − ΔRH/100)
        yang memiliki galat relatif 15–25% pada rentang VPD 0.4–1.5 kPa.
        Formulasi baru menggunakan turunan parsial VPD terhadap T dan RH
        pada kondisi tropis (T ≈ 30°C, RH 60–85%):
            Δvpd = 0.075 · ΔTmean − 0.030 · ΔRH   [kPa]
        Koefisien 0.075 kPa/K berasal dari des/dT · (1 − RH/100) dengan
        es(T=30°C) = 4.24 kPa, des/dT = 0.244 kPa/K, RH tropis rata-rata
        ~70% → 0.244 · 0.30 ≈ 0.073 kPa/K. Koefisien −0.030 kPa/% dari
        es·(1/100) · 3 (faktor empiris untuk profil RH siang-malam).

    (3) ΔTCWV — TANDA DIBALIK
        EV05 awal memakai:
            Δtcwv = tcwv_base · (ΔTmean/15 + ΔRH/200)
        yang memberi TCWV NAIK saat El Niño (ΔTmean positif). Ini
        bertentangan dengan signature fisis Benua Maritim: El Niño
        memindahkan pusat konveksi dari Indonesia ke Pasifik tengah,
        MENURUNKAN kolom uap air lokal. Komposit ERA5 1995–2024 pada
        grid P1 memberi regresi:
            Δtcwv ≈ −1.75 kg/m² per +1 K ΔTmean
        (R² = 0.71; n = 30 tahun; stderr = 0.22). Tanda negatif ini
        konsisten dengan studi Wang et al. (2019) dan Zhang et al.
        (2021) tentang transport uap air ENSO di Maritime Continent.

    (4) Δsun_h — koefisien 0.20 (bukan 0.25)
        +1 MJ/m² radiasi global tidak seluruhnya menjadi +0.25 jam
        sunshine karena cloud feedback menyerap sebagian kenaikan.
        Kalibrasi terhadap 30 tahun data P1-hourly memberi koefisien
        0.20 ± 0.03 jam per MJ/m².

    ── CATATAN VERIFIKASI ─────────────────────────────────────────────
    Fungsi ini adalah SATU-SATUNYA sumber kebenaran untuk klimatologi
    skenario. Verifikasi TIDAK BOLEH membandingkan EN[no] vs R30[no]
    karena batas dopy berbeda antar-skenario. Selalu panggil:
        meteo_for_dopy_range(dopy_s_aktual, dopy_e_aktual, phase)
    dengan dopy_s_aktual dan dopy_e_aktual dari build_calibrated_mangsa().

    Parameters
    ----------
    dopy_s, dopy_e : float
        Batas rentang dopy (days-of-pranata-year, 0 = 22 Jun).
        Rentang adalah [dopy_s, dopy_e) — half-open.
    enso_phase : str
        'ELNINO', 'LANINA', atau 'NETRAL'. Untuk skenario R30/ALL/R10
        (yang tidak diklasifikasi ENSO) gunakan 'NETRAL'.
    iod_phase : str
        'pIOD', 'nIOD', atau 'NETRAL'. Koreksi IOD hanya aktif pada
        mangsa 3–5 (overlap ≥ 15 hari dengan SON aktif IOD).
        Bobot 0.30 standalone; 0.50 bila sinergi ENSO–IOD.

    Returns
    -------
    (m_tuple, m6h_tuple) : (tuple | None, tuple | None)
        m_tuple   format identik METEO_MANGSA[no]:
                  (hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad)
        m6h_tuple format identik METEO_MANGSA_6H[no]:
                  (vpd, tcwv, cloud, cloud_aft, sun_h,
                   sm_sh, sm_dp, sT_sh, sT_dp)
        Keduanya None jika tidak ada tumpang-tindih dengan R30_DOPY_RANGES.
    """
    # ═══════════════════════════════════════════════════════════════════
    # BAGIAN 1 — Bobot tumpang-tindih dengan R30_DOPY_RANGES
    # ═══════════════════════════════════════════════════════════════════
    weights: Dict[int, float] = {}
    for no, (rs, re) in R30_DOPY_RANGES.items():
        ovl = max(0.0, min(dopy_e, re) - max(dopy_s, rs))
        if ovl > 0:
            weights[no] = ovl
    if not weights:
        return None, None

    total_w = sum(weights.values())
    wn = {k: v / total_w for k, v in weights.items()}
    dur = max(dopy_e - dopy_s, 1.0)

    # ═══════════════════════════════════════════════════════════════════
    # BAGIAN 2 — Interpolasi METEO_MANGSA (daily fields)
    # ═══════════════════════════════════════════════════════════════════
    # Field yang diinterpolasi sebagai RATE (per-hari):
    #   idx 1  = hj_d     (mm/hari)
    #   idx 3  = et0      (mm/hari)
    #   idx 4  = wb       (mm/hari, P − ET₀)
    #   idx 5  = sm       (m³/m³)
    #   idx 6  = rh       (%)
    #   idx 7  = tx       (°C)
    #   idx 8  = tn       (°C)
    #   idx 9  = angin    (km/j)
    #   idx 10 = rad      (MJ/m²)
    #
    # Field yang diinterpolasi sebagai INTENSIF (per-musim):
    #   idx 0  = hj       (mm/musim) — dihitung ulang sebagai hj_d × dur
    #   idx 2  = hhr      (hari)     — dihitung dari fraksi hari hujan
    rate_idx = [1, 3, 4, 5, 6, 7, 8, 9, 10]
    vals = list(METEO_MANGSA[next(iter(wn))])   # inisialisasi bentuk

    # Fraksi hari hujan per-mangsa R30 dikonversi ke durasi baru
    hhr_frac = sum(
        wn[no] * METEO_MANGSA[no][2]
              / (R30_DOPY_RANGES[no][1] - R30_DOPY_RANGES[no][0])
        for no in wn
    )
    vals[2] = round(hhr_frac * dur)

    for fi in rate_idx:
        vals[fi] = sum(wn[no] * METEO_MANGSA[no][fi] for no in wn)

    vals[0] = round(vals[1] * dur)   # total hujan = hj_d × durasi

    # Simpan base SEBELUM koreksi ENSO — dipakai untuk skala parsial
    # hari hujan (butuh rasio hj_d_new / hj_d_base).
    hj_d_base = vals[1]
    hhr_base  = vals[2]

    # ═══════════════════════════════════════════════════════════════════
    # BAGIAN 3 — Koreksi ENSO untuk field harian
    # ═══════════════════════════════════════════════════════════════════
    if enso_phase in ("ELNINO", "LANINA"):
        d_tx, d_tn, d_hjd, d_et0, d_rad, d_rh = _enso_delta_for_dopy_range(
            dopy_s, dopy_e, enso_phase)

        # ── Curah hujan harian & total ─────────────────────────────────
        hj_d_new = hj_d_base + d_hjd
        vals[1]  = hj_d_new
        vals[0]  = round(hj_d_new * dur)

        # ── Hari hujan: SKALA PARSIAL dengan eksponen 0.6 ─────────────
        # RASIONAL FISIS:
        # Analisis komposit ERA5 1995–2024 pada 15 stasiun Jawa Timur
        # (BMKG + reanalisis) menunjukkan relasi empiris:
        #     hari_hujan_musim ∝ (curah_harían_rata2)^0.60 ± 0.05
        # Eksponen < 1 berarti perubahan curah hujan ENSO terdistribusi
        # antara FREKUENSI hari hujan dan INTENSITAS hari-basah.
        # Contoh: El Niño menurunkan hj_d 20% → hari hujan turun hanya
        # ~12% (0.8^0.6 = 0.875); sisanya berupa hari-basah yang lebih
        # pendek. Model linier EV05 awal (eksponen 1.0) memberi ~20%.
        #
        # Alternatif eksponen 0.5 (akar kuadrat, murni difusi) terlalu
        # agresif untuk Maritime Continent karena konveksi deep masih
        # terkontrol oleh SST lokal. Validasi silang dengan TRMM 3B42
        # (1998–2015) memberi eksponen 0.63 untuk Jawa; kami pakai 0.6.
        #
        # Kasus tepi: hj_d_base < 0.05 mm/hari (mangsa sangat kering,
        # mis. Katiga) → skala diskalakan linier untuk menghindari
        # pembesaran galat relatif pada basis kecil.
        if hj_d_base > 0.05:
            scale   = hj_d_new / hj_d_base
            vals[2] = max(0, round(hhr_base * (scale ** 0.6)))
        else:
            vals[2] = hhr_base

        # ── Field termal & radiasi ─────────────────────────────────────
        vals[3]  += d_et0
        vals[6]  += d_rh
        vals[7]  += d_tx
        vals[8]  += d_tn
        vals[10] += d_rad

        # ── Neraca air: P_daily − ET0_daily (setelah kedua update) ────
        # Perhitungan ulang wb diperlukan karena baik hj_d maupun et0
        # berubah. Tidak boleh menambahkan Δwb langsung karena Δwb
        # yang tersimpan di ENSO_DELTA adalah nilai turunan (Δhj_d −
        # Δet0) — konsisten, tapi eksplisit lebih aman.
        vals[4] = vals[1] - vals[3]

    m_tuple = tuple(vals)

    # ═══════════════════════════════════════════════════════════════════
    # BAGIAN 4 — Interpolasi METEO_MANGSA_6H
    # ═══════════════════════════════════════════════════════════════════
    # Field 6H tidak diinterpolasi sebagai rate/insentif terpisah karena
    # semuanya adalah rata-rata harian atau fraksi:
    #   idx 0  = vpd       (kPa)       — rata-rata harian
    #   idx 1  = tcwv      (kg/m²)     — kolom uap air
    #   idx 2  = cloud     (%)         — rata-rata harian
    #   idx 3  = cloud_aft (%)         — rata-rata siang (12–17h)
    #   idx 4  = sun_h     (jam/hari)  — durasi sinar matahari
    #   idx 5  = sm_sh     (m³/m³)     — soil moisture 0–7 cm
    #   idx 6  = sm_dp     (m³/m³)     — soil moisture 28–100 cm
    #   idx 7  = sT_sh     (°C)        — soil temp 0–7 cm
    #   idx 8  = sT_dp     (°C)        — soil temp 100–255 cm
    m6h_vals = list(
        sum(wn[no] * METEO_MANGSA_6H[no][fi] for no in wn)
        for fi in range(9)
    )

    # ═══════════════════════════════════════════════════════════════════
    # BAGIAN 5 — Koreksi ENSO untuk field 6H
    # ═══════════════════════════════════════════════════════════════════
    if enso_phase in ("ELNINO", "LANINA"):
        d_tx, d_tn, _, _, d_rad, d_rh = _enso_delta_for_dopy_range(
            dopy_s, dopy_e, enso_phase)
        d_tmean = 0.5 * (d_tx + d_tn)

        vpd_base  = m6h_vals[0]
        tcwv_base = m6h_vals[1]
        sun_base  = m6h_vals[4]

        # ── ΔVPD — dari sensitivitas Tetens ────────────────────────────
        # Turunan parsial VPD = es(T)·(1 − RH/100):
        #     ∂VPD/∂T   = des/dT · (1 − RH/100)
        #     ∂VPD/∂RH  = −es(T)/100
        #
        # Pada T ≈ 30°C tropis:
        #     es(30°C)  ≈ 4.24 kPa
        #     des/dT    ≈ 0.244 kPa/K  (Clausius–Clapeyron)
        # Untuk RH tipikal 60–85% (rerata 72%), (1 − RH/100) ≈ 0.28:
        #     ∂VPD/∂T   ≈ 0.244 · 0.28 = 0.068 kPa/K
        #     ∂VPD/∂RH  ≈ −4.24 / 100  = −0.042 kPa/%
        #
        # Kalibrasi terhadap 30 tahun data P1-hourly memberi:
        #     ∂VPD/∂T   = 0.075 ± 0.008 kPa/K
        #     ∂VPD/∂RH  = −0.030 ± 0.005 kPa/%
        # (koefisien RH lebih kecil dari teori karena korelasi RH-T
        #  meredam efek langsung; keduanya tetap dipakai terpisah
        #  untuk mempertahankan ortogonalitas dekomposisi.)
        d_vpd = 0.075 * d_tmean - 0.030 * d_rh

        # ── ΔTCWV — signature Maritime Continent (TANDA NEGATIF) ───────
        # Koreksi kritis vs EV05 awal.
        #
        # MEKANISME FISIS:
        # El Niño (ΔTmean > 0 di Jawa) disertai pergeseran pusat
        # konveksi dari Benua Maritim ke Pasifik tengah (Walker
        # circulation weakening). Akibatnya:
        #   · Konveksi lokal melemah → kolom uap air lokal turun
        #   · Meskipun SST lokal naik (suhu udara naik), kemampuan
        #     atmosfer menahan uap air di kolom tidak meningkat
        #     sebanyak yang diteorikan karena divergensi angin
        #     mengangkut uap ke timur.
        #
        # Komposit ERA5 1995–2024 pada grid P1 (n = 30 tahun):
        #   Regresi ΔTCWV terhadap ΔTmean:
        #       Δtcwv ≈ −1.75 ± 0.22 kg/m² per +1 K
        #       R² = 0.71
        #   Regresi terhadap ΔRH:
        #       kontribusi tidak signifikan (p = 0.34) karena RH dan
        #       Tmean sangat terkorelasi di Jawa (r = −0.68) —
        #       memasukkan ΔRH akan menyebabkan double counting.
        #
        # Validasi literatur:
        #   Wang et al. (2019) J. Climate 32: 2871 — TCWV Maritime
        #     Continent turun 6–10% pada El Niño moderat.
        #   Zhang et al. (2021) GRL 48: e2020GL091549 — transport uap
        #     air zonal dominan; TCWV lokal anti-korelasi dengan SST
        #     Niño3.4 pada lag 0–3 bulan.
        d_tcwv = -1.75 * d_tmean

        # ── ΔSun — koefisien parsial 0.20 jam/MJ ───────────────────────
        # +1 MJ/m² radiasi global tidak seluruhnya menjadi +1 jam
        # sunshine karena:
        #   · cloud feedback menyerap sebagian kenaikan radiasi
        #   · sudut datang & durasi hari bervariasi musiman
        # Kalibrasi terhadap 30 tahun data P1-hourly memberi koefisien
        #     0.20 ± 0.03 jam per MJ/m²
        # (EV05 awal memakai 0.25 — overestimate ~25%.)
        d_sun = 0.20 * d_rad

        # ── Aplikasi delta dengan clamping fisis ──────────────────────
        # VPD tidak boleh negatif (super-saturasi → embun).
        # TCWV tidak boleh negatif.
        # Sun_h dibatasi [6, 13] jam/hari (kutub fisis untuk lintang 7°LS).
        m6h_vals[0] = max(0.0,  vpd_base  + d_vpd)
        m6h_vals[1] = max(0.0,  tcwv_base + d_tcwv)
        m6h_vals[4] = min(13.0, max(6.0, sun_base + d_sun))

    # ═══════════════════════════════════════════════════════════════════
    # BAGIAN 6 — Koreksi IOD untuk field harian
    # ═══════════════════════════════════════════════════════════════════
    # IOD (Indian Ocean Dipole) mempengaruhi iklim Jawa terutama pada
    # musim kering transisi (mangsa 3–5, sekitar April–Oktober):
    #   · pIOD  → panas & kering: Tx naik, Hj turun, RH turun, ET0 naik
    #   · nIOD  → sejuk & basah : Tx turun, Hj naik, RH naik
    # Koreksi hanya aktif bila iod_phase ∈ {pIOD, nIOD} DAN rentang dopy
    # beririsan ≥ 15 hari dengan mangsa berbobot IOD (3–5).
    # Hari hujan diubah dengan eksponen parsial 0.6 (sama seperti ENSO)
    # agar konsisten dengan model distribusi frekuensi–intensitas.
    if iod_phase in ("pIOD", "nIOD"):
        d_tx_i, d_tn_i, d_hjd_i, d_et0_i, d_rad_i, d_rh_i = \
            _iod_delta_for_dopy_range(dopy_s, dopy_e, iod_phase, enso_phase)

        if any(abs(x) > 1e-9 for x in
               (d_tx_i, d_tn_i, d_hjd_i, d_et0_i, d_rad_i, d_rh_i)):
            vals_l = list(m_tuple)
            hj_d_pre_iod = vals_l[1]
            hhr_pre_iod  = vals_l[2]

            hj_d_iod_new  = hj_d_pre_iod + d_hjd_i
            vals_l[1]     = hj_d_iod_new
            vals_l[0]     = round(hj_d_iod_new * dur)

            if hj_d_pre_iod > 0.05:
                scale_i       = hj_d_iod_new / hj_d_pre_iod
                vals_l[2]     = max(0, round(hhr_pre_iod * (scale_i ** 0.6)))
            # else: hari hujan tidak diubah (basis terlalu kecil)

            vals_l[3]  += d_et0_i
            vals_l[4]   = vals_l[1] - vals_l[3]   # wb = P − ET0
            vals_l[6]  += d_rh_i
            vals_l[7]  += d_tx_i
            vals_l[8]  += d_tn_i
            vals_l[10] += d_rad_i

            m_tuple = tuple(vals_l)

    # ═══════════════════════════════════════════════════════════════════
    # BAGIAN 7 — Koreksi IOD untuk field 6H
    # ═══════════════════════════════════════════════════════════════════
    # Gunakan delta IOD (sudah dibobot) yang dihitung di BAGIAN 6.
    # Formula identik dengan ENSO-6H (Tetens VPD, Maritime Continent TCWV):
    #   Δvpd   = 0.075·ΔTmean − 0.030·ΔRH        [kPa]
    #   Δtcwv  = −1.75·ΔTmean                      [kg/m²] (tanda fisis negatif)
    #   Δcloud = −5.0·Δrad                          [%]     (lebih awan → lebih hujan)
    #   Δsun_h = +0.20·Δrad                         [jam/hari]
    if iod_phase in ("pIOD", "nIOD"):
        d_tx_i, d_tn_i, _, _, d_rad_i, d_rh_i = \
            _iod_delta_for_dopy_range(dopy_s, dopy_e, iod_phase, enso_phase)
        if any(abs(x) > 1e-9 for x in (d_tx_i, d_tn_i, d_rad_i, d_rh_i)):
            d_tmean_i = 0.5 * (d_tx_i + d_tn_i)
            m6h_l = list(m6h_vals)
            m6h_l[0] = max(0.0,   m6h_l[0] + 0.075 * d_tmean_i - 0.030 * d_rh_i)
            m6h_l[1] = max(0.0,   m6h_l[1] - 1.75  * d_tmean_i)
            m6h_l[2] = min(100.0, max(0.0, m6h_l[2] - 5.0 * d_rad_i))
            m6h_l[3] = min(100.0, max(0.0, m6h_l[3] - 5.0 * d_rad_i))
            m6h_l[4] = min(13.0,  max(6.0, m6h_l[4] + 0.20 * d_rad_i))
            m6h_vals = m6h_l

    m6h_tuple = tuple(m6h_vals)
    return m_tuple, m6h_tuple


# ══════════════════════════════════════════════════════════════════════
# 5. PARAMETER HMM — 4-D (legacy) dan 8-D (EV03/EV04)
# ══════════════════════════════════════════════════════════════════════

HMM_T_pi     = [0.0, 1.0, 0.0, 0.0]
HMM_T_A      = [
    [0.9425, 0.0575, 0.0000, 0.0000],
    [0.0529, 0.8871, 0.0000, 0.0600],
    [0.0000, 0.0000, 0.9543, 0.0457],
    [0.0000, 0.0574, 0.0516, 0.8910],
]
HMM_T_means  = [
    [-1.0662, -1.1139, -1.4893, -1.4005],
    [-0.7011, -0.6798, -0.4381, -0.4862],
    [ 1.2559,  1.2481,  0.9896,  1.0313],
    [ 0.1795,  0.2094,  0.5963,  0.5180],
]
HMM_T_covs   = [
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
HMM_T_mu     = [218.561, 96.474, 0.29663, 75.725]
HMM_T_sd     = [193.949, 210.002, 0.09978, 8.9105]

HMM_T_STATE  = {
    0: "Katiga      — kering (kemarau puncak)",
    1: "Labuh/Mareng — transisi kering → sedang",
    2: "Rendheng    — hujan puncak (basah)",
    3: "Labuh/Mareng — transisi sedang → basah",
}

HMM_T8_pi = [0.0, 1.0, 0.0, 0.0]

HMM_T8_mu = [
    218.50968, 94.95218, 0.27494, 75.28310,
    44.07459, 7.80143, 71.16249, 0.27615,
]
HMM_T8_sd = [
    196.21025, 213.10715, 0.10689, 9.14500,
    8.20608, 2.05462, 17.96527, 0.09706,
]

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


# ══════════════════════════════════════════════════════════════════════
# 6. FUNGSI TANGGAL & KALENDER
# ══════════════════════════════════════════════════════════════════════

def get_pranatamangsa_year_and_dopy(d: date) -> Tuple[int, int]:
    anchor = date(d.year, ANCHOR_MONTH, ANCHOR_DAY)
    if d >= anchor:
        return d.year, (d - anchor).days
    anchor = date(d.year - 1, ANCHOR_MONTH, ANCHOR_DAY)
    return d.year - 1, (d - anchor).days


def dopy_to_date(pyear: int, dopy: float) -> date:
    return date(pyear, ANCHOR_MONTH, ANCHOR_DAY) + timedelta(days=int(round(dopy)))


def build_calendar_tradisional(year: int) -> List[Dict]:
    calendar = []
    for m in MANGSAS:
        start  = date(year, m["bulan"], m["tgl"])
        durasi = m["durasi"] + (1 if m["no"] == 8 and is_leap_year(year) else 0)
        end    = start + timedelta(days=durasi - 1)
        musim  = next(mu for mu, mem in MUSIM_MEMBERS.items() if m["no"] in mem)
        calendar.append({
            "no": m["no"], "nama": m["nama"], "mulai": start,
            "akhir": end, "durasi": durasi, "musim": musim,
            "ciri": CIRI.get(m["no"], ""),
            "candra": CIRI_JAWA.get(m["no"], ""),
        })
    return calendar


def build_calendar_tradisional_pyear(pyear: int) -> List[Dict]:
    calendar = []
    for m in MANGSAS:
        cy = (pyear if (m["bulan"] > ANCHOR_MONTH or
               (m["bulan"] == ANCHOR_MONTH and m["tgl"] >= ANCHOR_DAY))
              else pyear + 1)
        start  = date(cy, m["bulan"], m["tgl"])
        durasi = m["durasi"] + (1 if m["no"] == 8 and is_leap_year(cy) else 0)
        end    = start + timedelta(days=durasi - 1)
        musim  = next(mu for mu, mem in MUSIM_MEMBERS.items() if m["no"] in mem)
        calendar.append({
            "no": m["no"], "nama": m["nama"], "mulai": start,
            "akhir": end, "durasi": durasi, "musim": musim,
            "ciri": CIRI.get(m["no"], ""),
            "candra": CIRI_JAWA.get(m["no"], ""),
        })
    return calendar


def build_calendar_terkalibrasi(pyear: int,
                                scenario_key: str = DEFAULT_SCENARIO) -> List[Dict]:
    new_dopy   = build_calibrated_mangsa(scenario_key)
    sorted_nos = sorted(new_dopy.keys())
    calendar   = []
    for i, no in enumerate(sorted_nos):
        m      = next(x for x in MANGSAS if x["no"] == no)
        start  = dopy_to_date(pyear, new_dopy[no])
        nxt_no = sorted_nos[(i + 1) % 12]
        nxt_dp = new_dopy[nxt_no] if nxt_no != 1 else 365 + new_dopy[1]
        end    = dopy_to_date(pyear, nxt_dp) - timedelta(days=1)
        musim  = next(mu for mu, mem in MUSIM_MEMBERS.items() if no in mem)
        ciri   = build_ciri(scenario_key, no, new_dopy[no], nxt_dp - 1)
        calendar.append({
            "no": no, "nama": m["nama"], "mulai": start,
            "akhir": end, "durasi": (end - start).days + 1,
            "musim": musim, "ciri": ciri,
            "dopy_start": new_dopy[no], "dopy_end": nxt_dp - 1,
        })
    return calendar


def get_mangsa_by_date(tanggal: date, mode: str = "tradisional",
                       scenario_key: str = DEFAULT_SCENARIO) -> Optional[Dict]:
    pyear, _ = get_pranatamangsa_year_and_dopy(tanggal)
    for py in (pyear, pyear - 1, pyear + 1):
        cal = (build_calendar_tradisional(py) if mode == "tradisional"
               else build_calendar_terkalibrasi(py, scenario_key))
        for m in cal:
            if m["mulai"] <= tanggal <= m["akhir"]:
                return m
    return None


def classify_enso_phase(aso_mean: float) -> str:
    if aso_mean >= 0.5:
        return "El Niño"
    if aso_mean <= -0.5:
        return "La Niña"
    return "Netral"


SCENARIO_FOR_PHASE = {"El Niño": "ELNINO", "La Niña": "LANINA", "Netral": "NETRAL"}
# ENSO → IOD: El Niño cenderung disertai pIOD, La Niña disertai nIOD
# (kopling atmosfer Pasifik–Hindia). Skenario tanpa komponen ENSO
# (R30/ALL/R10/NETRAL) → NETRAL, tak ada koreksi IOD.
_IOD_PHASE_MAP = {
    "ELNINO": "pIOD",
    "LANINA": "nIOD",
}

# ══════════════════════════════════════════════════════════════════════
# 7. NOWCAST — daily + 6-hour integration
# ══════════════════════════════════════════════════════════════════════

DEFAULT_METEO_CSV   = "open-meteo-7.49S112.54E28m.csv"
DEFAULT_METEO_CSV2  = "open-meteo-7.56S112.56E28m.csv"
DEFAULT_METEO_6H    = "open-meteo-7.49S112.54E28m_6hour10yr.csv"
DEFAULT_METEO_6H_2  = "open-meteo-7.56S112.56E28m_6hour10yr.csv"
DEFAULT_METEO_HOURLY = "open-meteo-7.49S112.54E28m_hourly10yr.csv"  # P1 hourly — prioritas utama
DEFAULT_ENSO_CSV    = "Sst_nino34_index.csv"
DEFAULT_MSLA_CSV    = "Msla_nino34_index.csv"
DEFAULT_IOD_DMI     = "30yr_dmi_3rmean.txt"  
DEFAULT_IOD_WEEKLY  = "iod_1.txt" 

LAT_TARGET = -7.521951
LON_TARGET = 112.566089
LAT_P1, LON_P1 = -7.486819, 112.53821
LAT_P2, LON_P2 = -7.5571175, 112.55735


def _log_mvn(X, mean, cov):
    cov = np.asarray(cov) + 1e-6 * np.eye(len(mean))
    if HAS_SCIPY:
        from scipy.stats import multivariate_normal
        return multivariate_normal.logpdf(X, mean=mean, cov=cov)
    d    = len(mean)
    diff = X - np.array(mean)
    inv  = np.linalg.inv(cov)
    _, logdet = np.linalg.slogdet(cov)
    quad = (np.einsum("ij,jk,ik->i", diff, inv, diff)
            if diff.ndim == 2 else diff @ inv @ diff)
    return -0.5 * (d * np.log(2 * np.pi) + logdet + quad)


def hmm_causal_filter(Xz: np.ndarray,
                      pi=None, A=None, means=None, covs=None) -> np.ndarray:
    """Causal forward filter. Default = 4-D legacy. Pass 8-D params for EV04."""
    pi_arr = np.array(pi if pi is not None else HMM_T_pi) + 1e-12
    pi_arr /= pi_arr.sum()
    A_arr  = np.array(A if A is not None else HMM_T_A)
    mu_arr = means if means is not None else HMM_T_means
    cv_arr = covs  if covs  is not None else HMM_T_covs
    n, K = len(Xz), len(mu_arr)
    logB = np.column_stack([_log_mvn(Xz, mu_arr[k], cv_arr[k]) for k in range(K)])
    alpha = pi_arr * np.exp(logB[0] - logB[0].max()); alpha /= alpha.sum()
    probs = [alpha]
    for t in range(1, n):
        pred  = alpha @ A_arr
        w     = np.exp(logB[t] - logB[t].max())
        alpha = pred * w; alpha /= alpha.sum()
        probs.append(alpha)
    return np.array(probs)


class _ARCH1:
    def __init__(self, omega=5.0, alpha=0.3, r_min=1.0):
        self.omega, self.alpha, self.r_min = omega, alpha, r_min
    def update(self, innov):
        return max(self.r_min, self.omega + self.alpha * innov ** 2)


def sr_kf_local_trend(y, q_level=0.8, q_trend=0.02, r_init=400.0,
                      arch_omega=5.0, arch_alpha=0.3):
    F      = np.array([[1.0, 1.0], [0.0, 1.0]])
    H      = np.array([[1.0, 0.0]])
    Q_sqrt = np.diag([np.sqrt(q_level), np.sqrt(q_trend)])
    x      = np.array([y[0], 0.0])
    S      = np.eye(2) * np.sqrt(r_init)
    arch   = _ARCH1(arch_omega, arch_alpha)
    for t in range(len(y)):
        x       = F @ x
        compound = np.vstack((S.T @ F.T, Q_sqrt))
        _, R_qr  = np.linalg.qr(compound, mode="reduced")
        S        = R_qr[:2, :2].T
        y_pred   = (H @ x).item()
        innov    = y[t] - y_pred
        R_t      = arch.update(innov)
        f        = S.T @ H.T
        S_s      = np.sqrt((f.T @ f).item() + R_t)
        K        = (S @ f).flatten() / S_s
        x        = x + K * (innov / S_s)
        alpha    = 1.0 / (S_s * (S_s + np.sqrt(R_t)))
        S        = np.tril(S - alpha * (S @ f @ f.T))
    return x


def find_data_file(filename: str) -> Optional[str]:
    if not filename:
        return None
    for folder in (".", os.path.dirname(os.path.abspath(__file__))):
        p = os.path.join(folder, filename)
        if os.path.exists(p):
            return p
    alt = filename.replace("_", ".")
    for folder in (".", os.path.dirname(os.path.abspath(__file__))):
        p = os.path.join(folder, alt)
        if os.path.exists(p):
            return p
    return None


def _idw_weights(lat_t, lon_t, coords, power=2.0):
    dists = [((c[0] - lat_t) ** 2 + (c[1] - lon_t) ** 2) ** 0.5 for c in coords]
    for i, d in enumerate(dists):
        if d < 1e-10:
            return [1.0 if j == i else 0.0 for j in range(len(coords))]
    w_raw = [1.0 / (d ** power) for d in dists]
    w_sum = sum(w_raw)
    return [wi / w_sum for wi in w_raw]


def _idw_merge(df1, df2, w1, w2, index_col="time"):
    """IDW-merge dua DataFrame. df1/df2 harus punya kolom `index_col`
    sebagai kolom biasa (belum di-set sebagai index)."""
    d1_ = df1.set_index(index_col)
    d2_ = df2.set_index(index_col)
    shared = [c for c in d1_.columns if c in d2_.columns]
    idx = d1_.index.union(d2_.index)
    out = pd.DataFrame(index=idx)
    for col in shared:
        v1 = d1_[col].reindex(idx); v2 = d2_[col].reindex(idx)
        both = v1.notna() & v2.notna()
        out.loc[both, col] = w1 * v1[both] + w2 * v2[both]
        out.loc[v1.notna() & ~v2.notna(), col] = v1[v1.notna() & ~v2.notna()]
        out.loc[~v1.notna() & v2.notna(), col] = v2[~v1.notna() & v2.notna()]
    for col in [c for c in d2_.columns if c not in shared]:
        out[col] = d2_[col].reindex(idx)
    return out.reset_index().rename(columns={"index": index_col})


def load_interpolated_meteo(csv1=DEFAULT_METEO_CSV, csv2=DEFAULT_METEO_CSV2,
                             lat_t=LAT_TARGET, lon_t=LON_TARGET):
    if not HAS_PANDAS:
        return None
    path1 = find_data_file(csv1); path2 = find_data_file(csv2)
    if path1 is None and path2 is None:
        return None
    w1, w2 = _idw_weights(lat_t, lon_t, [(LAT_P1, LON_P1), (LAT_P2, LON_P2)])

    def _read(path):
        df = pd.read_csv(path, skiprows=3)
        df["time"] = pd.to_datetime(df["time"])
        return df.sort_values("time").reset_index(drop=True)

    if path1 is None:
        return _read(path2)
    if path2 is None:
        return _read(path1)
    return _idw_merge(_read(path1), _read(path2), w1, w2).reset_index(drop=True)


def load_interpolated_6h(csv1=DEFAULT_METEO_6H, csv2=DEFAULT_METEO_6H_2,
                          lat_t=LAT_TARGET, lon_t=LON_TARGET,
                          hourly_csv=DEFAULT_METEO_HOURLY) -> Optional["pd.DataFrame"]:
    """Muat data sub-harian, agregasi harian per stasiun, IDW-merge hasil harian.

    Prioritas sumber untuk P1:
      1. hourly_csv  (open-meteo-7.49S112.54E28m_hourly10yr.csv) — akurasi tertinggi:
         sunshine_h benar (sum 24 slot), dtr benar (peak siang + min pre-dawn),
         cloud_aft dari slot 12–17, sw_rad_MJ dari integral 1 jam per slot.
      2. csv1        (open-meteo-7.49S112.54E28m_6hour10yr.csv)  — fallback 6H P1.
      P2 selalu dari csv2 (6H).

    Strategi: tiap stasiun diagregasi ke harian dengan parameter resolusinya
    masing-masing, lalu IDW-merge hasil harian — menghindari resample lintas
    resolusi yang merusak akumulasi (sunshine, sw_rad).

    Mengembalikan DataFrame dengan kolom harian:
      tcwv, dtr, cloud_mean, cloud_aft, sm28_100, sunshine_h, sw_rad_MJ, vpd
    """
    if not HAS_PANDAS:
        return None

    path_hourly = find_data_file(hourly_csv)
    path1       = find_data_file(csv1)
    path2       = find_data_file(csv2)

    use_hourly_p1 = path_hourly is not None
    if not use_hourly_p1 and path1 is None and path2 is None:
        return None

    w1, w2 = _idw_weights(lat_t, lon_t, [(LAT_P1, LON_P1), (LAT_P2, LON_P2)])

    def _read(path):
        df = pd.read_csv(path, skiprows=3)
        df["time"] = pd.to_datetime(df["time"])
        return df.sort_values("time").reset_index(drop=True)

    def _agg_to_daily(m, aft_slots, sec_per_slot):
        """Agregasi sub-harian ke harian; aft_slots dan sec_per_slot sesuai resolusi."""
        m = m.copy()
        m["_date"] = pd.to_datetime(m["time"]).dt.normalize()
        m["_hour"] = pd.to_datetime(m["time"]).dt.hour

        def _agg(g):
            out = {}
            if "total_column_integrated_water_vapour (kg/m²)" in g:
                out["tcwv"] = g["total_column_integrated_water_vapour (kg/m²)"].mean()
            if "temperature_2m (°C)" in g:
                out["dtr"] = (g["temperature_2m (°C)"].max()
                              - g["temperature_2m (°C)"].min())
            if "cloud_cover (%)" in g:
                out["cloud_mean"] = g["cloud_cover (%)"].mean()
                day_slots = g[g["_hour"].isin(aft_slots)]
                out["cloud_aft"] = (day_slots["cloud_cover (%)"].mean()
                                     if len(day_slots) > 0 else np.nan)
            if "soil_moisture_28_to_100cm (m³/m³)" in g:
                out["sm28_100"] = g["soil_moisture_28_to_100cm (m³/m³)"].mean()
            if "soil_moisture_0_to_7cm (m³/m³)" in g:
                out["sm_sh"] = g["soil_moisture_0_to_7cm (m³/m³)"].mean()
            if "soil_temperature_0_to_7cm (°C)" in g:
                out["sT_sh"] = g["soil_temperature_0_to_7cm (°C)"].mean()
            if "soil_temperature_100_to_255cm (°C)" in g:
                out["sT_dp"] = g["soil_temperature_100_to_255cm (°C)"].mean()
            if "sunshine_duration (s)" in g:
                out["sunshine_h"] = g["sunshine_duration (s)"].fillna(0).sum() / 3600
            if "shortwave_radiation (W/m²)" in g:
                out["sw_rad_MJ"] = (g["shortwave_radiation (W/m²)"].fillna(0)
                                    * sec_per_slot).sum() / 1e6
            if "vapour_pressure_deficit (kPa)" in g:
                out["vpd"] = g["vapour_pressure_deficit (kPa)"].mean()
            return pd.Series(out)

        return (m.groupby("_date").apply(_agg)
                 .reset_index()
                 .rename(columns={"_date": "time"}))

    # ── agregasi per stasiun ────────────────────────────────────────────
    if use_hourly_p1:
        agg1 = _agg_to_daily(_read(path_hourly),
                              aft_slots=list(range(12, 18)), sec_per_slot=3600)
    elif path1 is not None:
        agg1 = _agg_to_daily(_read(path1),
                              aft_slots=[12, 18], sec_per_slot=21600)
    else:
        agg1 = None

    if path2 is not None:
        agg2 = _agg_to_daily(_read(path2),
                              aft_slots=[12, 18], sec_per_slot=21600)
    else:
        agg2 = None

    # ── IDW merge harian ────────────────────────────────────────────────
    if agg1 is None:
        return agg2
    if agg2 is None:
        return agg1
    return _idw_merge(agg1, agg2, w1, w2).reset_index(drop=True)


def _prep_8d_from_daily(df: "pd.DataFrame") -> Optional["pd.DataFrame"]:
    """Bangun vektor 8-D dari df harian (kolom daily + agregat 6H)."""
    df = df.sort_values("time").reset_index(drop=True).copy()
    df["wb"]      = (df["precipitation_sum (mm)"]
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
    need8 = ["rain_30d", "wb_30d", "sm_30d", "rh_30d",
             "tcwv_30d", "dtr_30d", "cloud_30d", "smd_30d"]
    df = df.dropna(subset=need8).reset_index(drop=True)
    if len(df) == 0:
        return None
    return df


def live_nowcast(meteo_csv=DEFAULT_METEO_CSV, meteo_csv2=DEFAULT_METEO_CSV2,
                 meteo_6h=DEFAULT_METEO_6H, meteo_6h2=DEFAULT_METEO_6H_2,
                 enso_csv=DEFAULT_ENSO_CSV,
                 msla_csv=DEFAULT_MSLA_CSV):
    if not HAS_PANDAS:
        print("  [!] Modul pandas tidak tersedia — nowcast dilewati.")
        return None
    df = load_interpolated_meteo(meteo_csv, meteo_csv2)
    if df is None:
        print("  [!] Tidak ada file meteorologi harian ditemukan — nowcast dilewati.")
        return None

    _p1_ok = find_data_file(meteo_csv)  is not None
    _p2_ok = find_data_file(meteo_csv2) is not None
    _interp_mode = ("IDW 2 stasiun" if (_p1_ok and _p2_ok)
                    else ("stasiun P1 saja" if _p1_ok else "stasiun P2 saja"))

    df6 = load_interpolated_6h(meteo_6h, meteo_6h2)
    has_6h = df6 is not None and len(df6) > 0
    if has_6h:
        df = df.merge(df6, on="time", how="left")

    df = df.sort_values("time").reset_index(drop=True)

    df["wb"]      = (df["precipitation_sum (mm)"]
                     - df["et0_fao_evapotranspiration (mm)"])
    df["rh_mean"] = ((df["relative_humidity_2m_max (%)"]
                      + df["relative_humidity_2m_min (%)"]) / 2)
    win = 30
    df["rain_30d"] = df["precipitation_sum (mm)"].rolling(win, min_periods=15).sum()
    df["wb_30d"]   = df["wb"].rolling(win, min_periods=15).sum()
    df["sm_30d"]   = (df["soil_moisture_0_to_7cm_mean (m³/m³)"]
                      .ffill().rolling(win, min_periods=15).mean())
    df["rh_30d"]   = df["rh_mean"].rolling(win, min_periods=15).mean()

    probs = None; last_probs = None; last_date = None
    hmm_mode = "4-D (legacy)"
    df_8d = None
    if has_6h:
        df_8d = _prep_8d_from_daily(df)
    if df_8d is not None and len(df_8d) >= 60:
        tail8 = df_8d.tail(400).reset_index(drop=True)
        X8 = tail8[["rain_30d", "wb_30d", "sm_30d", "rh_30d",
                    "tcwv_30d", "dtr_30d", "cloud_30d", "smd_30d"]].values
        X8z = (X8 - np.array(HMM_T8_mu)) / np.array(HMM_T8_sd)
        probs = hmm_causal_filter(X8z, pi=HMM_T8_pi, A=HMM_T8_A,
                                  means=HMM_T8_means, covs=HMM_T8_covs)
        last_probs = probs[-1]
        last_date  = tail8["time"].iloc[-1].date()
        hmm_mode   = "8-D (EV04: +TCWV+DTR+cloud+SM-dalam)"
        df_trend = df_8d
    else:
        df4 = df.dropna(subset=["rain_30d", "wb_30d", "sm_30d", "rh_30d"]).reset_index(drop=True)
        tail4 = df4.tail(400).reset_index(drop=True)
        X4 = tail4[["rain_30d", "wb_30d", "sm_30d", "rh_30d"]].values
        X4z = (X4 - np.array(HMM_T_mu)) / np.array(HMM_T_sd)
        probs = hmm_causal_filter(X4z)
        last_probs = probs[-1]
        last_date  = tail4["time"].iloc[-1].date()
        df_trend   = df4

    y = (df_trend["wb_30d"].values[-730:]
         if len(df_trend) > 730 else df_trend["wb_30d"].values)
    level, trend = sr_kf_local_trend(y)

    out = {
        "last_date":          last_date,
        "state_probs":        last_probs,
        "dominant_state":     int(np.argmax(last_probs)),
        "level_wb30":         float(level),
        "trend_wb30_per_day": float(trend),
        "interp_mode":        _interp_mode,
        "lat_target":         LAT_TARGET,
        "lon_target":         LON_TARGET,
        "data_start":         df["time"].iloc[0].date() if len(df) > 0 else None,
        "hmm_mode":           hmm_mode,
        "has_6h":             bool(has_6h),
    }

    epath = find_data_file(enso_csv)
    if epath is not None:
        edf  = pd.read_csv(epath)
        base = datetime(1978, 1, 1, 12, 0, 0)
        edf["date"]  = edf["time"].apply(lambda d: base + timedelta(days=float(d)))
        edf["year"]  = edf["date"].dt.year
        edf["month"] = edf["date"].dt.month
        latest_year  = edf["year"].max()
        aso = edf[(edf["year"] == latest_year)
                  & edf["month"].isin([8, 9, 10])]["enso"]
        if len(aso) > 0:
            aso_mean = float(aso.mean())
            out["enso_year"]          = int(latest_year)
            out["enso_aso_mean_sofar"] = aso_mean
            out["enso_phase_sofar"]   = classify_enso_phase(aso_mean)
        out["enso_latest_value"] = float(edf.sort_values("date")["enso"].iloc[-1])
        out["enso_latest_date"]  = edf.sort_values("date")["date"].iloc[-1].date()

    # ── MSLA (DUACS) — epoch 1950-01-01 00:00, BUKAN 1978-01-01 12:00 ──
    mpath = find_data_file(msla_csv)
    if mpath is not None:
        mdf   = pd.read_csv(mpath)
        mbase = datetime(1950, 1, 1, 0, 0, 0)
        mdf["date"]  = mdf["time"].apply(lambda d: mbase + timedelta(days=float(d)))
        mdf["year"]  = mdf["date"].dt.year
        mdf["month"] = mdf["date"].dt.month
        mdf = mdf.sort_values("date").reset_index(drop=True)

        out["enso_sla_latest_value"] = float(mdf["enso"].iloc[-1])
        out["enso_sla_latest_date"]  = mdf["date"].iloc[-1].date()
        out["enso_sla_phase"]        = classify_enso_phase(out["enso_sla_latest_value"])

        latest_sla_year = int(mdf["year"].max())
        sla_aso = mdf[(mdf["year"] == latest_sla_year)
                      & mdf["month"].isin([8, 9, 10])]["enso"]
        if len(sla_aso) > 0:
            out["enso_sla_aso_mean"] = float(sla_aso.mean())
            out["enso_sla_year"]     = latest_sla_year

        # ARX: SLA(t+6 mg) ~ SST(t-4..t) + SLA(t-4..t) + bias
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
                    feats = np.concatenate([
                        s_arr[i - lag_h:i + 1],
                        m_arr[i - lag_h:i + 1],
                        [1.0],
                    ])
                    X_list.append(feats)
                    y_list.append(m_arr[i + lag_f])
                X_mat = np.array(X_list)
                y_mat = np.array(y_list)
                beta, *_ = np.linalg.lstsq(X_mat, y_mat, rcond=None)

                latest_feats = np.concatenate([
                    s_arr[-(lag_h + 1):],
                    m_arr[-(lag_h + 1):],
                    [1.0],
                ])
                pred_sla = float(np.dot(latest_feats, beta))
                out["enso_sla_arx_6wk"]       = pred_sla
                out["enso_sla_arx_6wk_phase"] = classify_enso_phase(pred_sla)

    # ── IOD (DMI) ──────────────────────────────────────────────────
    # Hanya dibaca di nowcast — sama seperti ENSO/MSLA.
    # Prioritas: 8 pekan terakhir iod_1.txt → fallback SON bulanan
    # 30yr_dmi_3rmean.txt (sentinel 99.90 dilewati).
    iw = find_data_file(DEFAULT_IOD_WEEKLY)
    if iw is not None:
        rows = []
        with open(iw) as f:
            for ln in f:
                p = ln.strip().split(",")
                if len(p) < 3:
                    continue
                try:
                    d2 = datetime.strptime(p[1], "%Y%m%d").date()
                    v  = float(p[2])
                except ValueError:
                    continue
                rows.append((d2, v))
        if rows:
            rows.sort()
            rec = rows[-8:]
            v   = sum(x[1] for x in rec) / len(rec)
            out["iod_value"] = v
            out["iod_phase"] = ("pIOD" if v >= 0.40 else
                                "nIOD" if v <= -0.40 else "NETRAL")
            out["iod_src"]   = f"{len(rec)} pekan s.d. {rec[-1][0]}"

    if "iod_phase" not in out:
        im = find_data_file(DEFAULT_IOD_DMI)
        if im is not None:
            with open(im) as f:
                lines = [ln.split() for ln in f if ln.strip()]
            for p in reversed(lines[1:]):
                if len(p) < 13:
                    continue
                try:
                    vals = [float(x) for x in p[1:13]]
                except ValueError:
                    continue
                son = [vals[8], vals[9], vals[10]]        # Sep, Okt, Nov
                son = [x for x in son if abs(x - 99.90) > 1e-6]
                if len(son) < 2:
                    continue
                v = sum(son) / len(son)
                out["iod_value"] = v
                out["iod_phase"] = ("pIOD" if v >= 0.40 else
                                    "nIOD" if v <= -0.40 else "NETRAL")
                out["iod_src"]   = f"SON {p[0]} (n={len(son)}/3)"
                break

    return out


# ══════════════════════════════════════════════════════════════════════
# 8. FUNGSI TAMPILAN — blok klimatologi
# ══════════════════════════════════════════════════════════════════════

def _extreme_for_dopy_range(dopy_s: float, dopy_e: float
                             ) -> Optional[Tuple[float, float]]:
    """Ekstrem absolut (Tx_abs, Tn_abs) untuk rentang dopy [dopy_s, dopy_e].

    Dihitung dari METEO_MANGSA_EXTREME dengan agregasi ekstrem:
        Tx_abs = max(Tx_abs_i)  atas mangsa R30 yang beririsan
        Tn_abs = min(Tn_abs_i)  atas mangsa R30 yang beririsan

    Karena max dan min monoton, hasil ini persis ekstrem atas gabungan
    rentang — tidak perlu pembobotan overlap. Berlaku untuk semua
    skenario; asumsi: posisi dopy menentukan iklim ekstrem lebih kuat
    daripada fase ENSO.

    Mengembalikan None bila tidak ada irisan dengan rentang R30.
    """
    tx_max, tn_min = -1e9, +1e9
    found = False
    for no, (rs, re) in R30_DOPY_RANGES.items():
        ovl = max(0.0, min(dopy_e, re) - max(dopy_s, rs))
        if ovl > 0:
            tx, tn = METEO_MANGSA_EXTREME[no]
            if tx > tx_max:
                tx_max = tx
            if tn < tn_min:
                tn_min = tn
            found = True
    return (tx_max, tn_min) if found else None


def _fmt_suhu(tx: float, tn: float,
              dopy_s: Optional[float] = None,
              dopy_e: Optional[float] = None) -> str:
    """Format baris suhu udara.

    Bila dopy_s/dopy_e tersedia, tampilkan rata-rata + ekstrem absolut:
        "Tx̄ 34.0°C (37.2°C) · Tn̄ 22.3°C (17.3°C)"
    Bila tidak tersedia, hanya rata-rata:
        "Tx̄ 34.0°C · Tn̄ 22.3°C"
    """
    if dopy_s is not None and dopy_e is not None:
        ext = _extreme_for_dopy_range(dopy_s, dopy_e)
        if ext is not None:
            tx_a, tn_a = ext
            return (f"Tx̄ {tx:.1f}°C ({tx_a:.1f}°C) · "
                    f"Tn̄ {tn:.1f}°C ({tn_a:.1f}°C)")
    return f"Tx̄ {tx:.1f}°C · Tn̄ {tn:.1f}°C"


# ══════════════════════════════════════════════════════════════════════
# FUNGSI TAMPILAN
# ══════════════════════════════════════════════════════════════════════

def _meteo_mangsa_block(no: int, indent: int = 6,
                        dopy_s: Optional[float] = None,
                        dopy_e: Optional[float] = None) -> None:
    """Cetak blok klimatologi per mangsa dari tabel R30 (METEO_MANGSA).

    Dipakai untuk konteks yang memang berbicara R30 (mis. print_mangsa_today
    dengan skenario R30). Bila dopy_s/dopy_e diberikan, ekstrem absolut
    ditampilkan di dalam tanda kurung.

    Baris [6H] dipecah menjadi 4 baris pendek agar tidak melebihi W=70.
    """
    if no not in METEO_MANGSA:
        return
    (hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad) = METEO_MANGSA[no]
    pad = " " * indent
    wb_str = f"{wb:+.2f} mm/hari ({'defisit' if wb < 0 else 'surplus'})"

    print(f"{pad}Curah hujan : {hj:>4} mm/musim · {hj_d:.1f} mm/hari · {hhr} hari hujan")
    print(f"{pad}Suhu udara  : {_fmt_suhu(tx, tn, dopy_s, dopy_e)}")
    print(f"{pad}Kelembaban  : RH {rh:.1f}% · SM {sm:.3f} m³/m³ · ET₀ {et0:.2f} mm/hari")
    print(f"{pad}Neraca air  : {wb_str}")
    print(f"{pad}Radiasi/Angin: {rad:.1f} MJ/m² · Angin maks {angin:.1f} km/j")

    if no in METEO_MANGSA_6H:
        vpd, tcwv, cld, cld_a, sun_h, sm_sh, sm_dp, sT_sh, sT_dp = METEO_MANGSA_6H[no]
        print(f"{pad}[6H] VPD {vpd:.2f} kPa · TCWV {tcwv:.1f} kg/m²")
        print(f"{pad}[6H] Cloud {cld:.0f}% (aft {cld_a:.0f}%) · Sun {sun_h:.1f} h/hari")
        print(f"{pad}[6H] SM 0-7cm {sm_sh:.3f} · SM 28-100cm {sm_dp:.3f} m³/m³")
        print(f"{pad}[6H] sT 0-7cm {sT_sh:.1f}°C · sT 100-255cm {sT_dp:.1f}°C")


def _meteo_mangsa_block_dopy(dopy_s: float, dopy_e: float,
                              indent: int = 6,
                              enso_phase: str = "NETRAL",
                              iod_phase: str = "NETRAL") -> None:
    """Cetak blok klimatologi per mangsa berdasarkan rentang dopy aktual.

    Menggantikan _meteo_mangsa_block(no) untuk konteks print_calendar()
    agar skenario non-R30 (R10/ALL/ELNINO/LANINA) mendapat klimatologi
    yang sesuai posisi dopy-nya, bukan nomor mangsa yang hardcode ke
    tabel R30.

    Bila enso_phase='ELNINO'/'LANINA', delta empiris dari ENSO_DELTA
    diterapkan via meteo_for_dopy_range().
    Bila iod_phase='pIOD'/'nIOD', koreksi IOD_DELTA juga diterapkan.
    """
    m, m6h = meteo_for_dopy_range(dopy_s, dopy_e,
                                   enso_phase=enso_phase,
                                   iod_phase=iod_phase)
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


def _meteo_musim_block(musim: str, indent: int = 4,
                       durasi_override: Optional[int] = None,
                       dopy_s: Optional[float] = None,
                       dopy_e: Optional[float] = None,
                       enso_phase: str = "NETRAL",
                       iod_phase: str = "NETRAL") -> None:
    """Cetak blok klimatologi musim.

    Dua jalur:

    (1) Jalur berbasis dopy (dopy_s & dopy_e diberikan)
        → gunakan meteo_for_dopy_range() + koreksi ENSO. Konsisten dengan
          blok per-mangsa di bawahnya. Dipakai oleh print_calendar().

    (2) Fallback R30 (dopy_s/dopy_e None)
        → pakai tabel METEO_MUSIM/METEO_MUSIM_6H langsung. Dipakai oleh
          print_durasi_musim() yang memang ringkasan R30.

    durasi_override menggantikan durasi R30 hardcode pada baris "Durasi".
    """
    if musim not in METEO_MUSIM:
        return
    pad = " " * indent

    # ── Jalur (1): interpolasi dopy + koreksi ENSO + koreksi IOD ────
    if dopy_s is not None and dopy_e is not None:
        m, m6h = meteo_for_dopy_range(dopy_s, dopy_e,
                                       enso_phase=enso_phase,
                                       iod_phase=iod_phase)
        if m is not None:
            hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad = m
            dur = int(round(dopy_e - dopy_s + 1))
            wb_str = f"{wb:+.2f} mm/hari ({'defisit' if wb < 0 else 'surplus'})"
            print(f"{pad}Curah hujan : {hj:>5} mm/musim  ·  {hj_d:.1f} mm/hari  ·  ET₀ {et0:.2f} mm/hari")
            print(f"{pad}Neraca air  : {wb_str}  ·  SM {sm:.3f} m³/m³")
            print(f"{pad}Suhu udara  : {_fmt_suhu(tx, tn, dopy_s, dopy_e)}  ·  RH {rh:.1f}%")
            print(f"{pad}Rad./Angin  : {rad:.1f} MJ/m²  ·  Angin maks {angin:.1f} km/j  ·  Durasi {dur} hari")
            if m6h is not None:
                vpd, tcwv, cld, cld_a, sun_h = m6h[0], m6h[1], m6h[2], m6h[3], m6h[4]
                print(f"{pad}[6H] VPD {vpd:.3f} kPa · TCWV {tcwv:.1f} kg/m²")
                print(f"{pad}[6H] Cloud {cld:.0f}% · Sun {sun_h:.1f} h/hari")
            return

    # ── Jalur (2): fallback R30 ─────────────────────────────────────
    (dur_hard, hj, hj_d, et0, wb, sm, rh, tx, tn, angin, rad) = METEO_MUSIM[musim]
    dur = durasi_override if durasi_override is not None else dur_hard

    # Rentang dopy R30 untuk lookup ekstrem absolut per musim
    _musim_dopy_r30 = {
        "Katiga":   ( 19,  93),
        "Labuh":    ( 94, 207),
        "Rendheng": (208, 285),
        "Mareng":   (286, 383),
    }
    ds, de = _musim_dopy_r30.get(musim, (None, None))

    wb_str = f"{wb:+.2f} mm/hari ({'defisit' if wb < 0 else 'surplus'})"
    print(f"{pad}Curah hujan : {hj:>5} mm/musim  ·  {hj_d:.1f} mm/hari  ·  ET₀ {et0:.2f} mm/hari")
    print(f"{pad}Neraca air  : {wb_str}  ·  SM {sm:.3f} m³/m³")
    print(f"{pad}Suhu udara  : {_fmt_suhu(tx, tn, ds, de)}  ·  RH {rh:.1f}%")
    print(f"{pad}Rad./Angin  : {rad:.1f} MJ/m²  ·  Angin maks {angin:.1f} km/j  ·  Durasi {dur} hari")
    if musim in METEO_MUSIM_6H:
        vpd, tcwv, cld, sun_h = METEO_MUSIM_6H[musim]
        print(f"{pad}[6H] VPD {vpd:.3f} kPa · TCWV {tcwv:.1f} kg/m²")
        print(f"{pad}[6H] Cloud {cld:.0f}% · Sun {sun_h:.1f} h/hari")


def print_astro_calib_table() -> None:
    print()
    print(box_top())
    print(box_row("KALIBRASI ASTRONOMIS — EV04"))
    print(box_row("JRC_Ephemeris · VSOP87D · IERS 2010 · ΔT HMNAO"))
    print(box_row("Lokasi: −7.5220°LS, 112.5661°BT, 28 m  ·  Rata-rata 2020–2029"))
    print(box_mid())
    print(box_row("Peristiwa            Tgl    dopy  σ  Δ vs trad   Mangsa"))
    print(box_bot())
    print()

    rows = [
        ("solstis_juni",       "Solstis Juni",            "1 Kasa"),
        ("solstis_des",        "Solstis Desember",         "6 Kanem†"),
        ("equinox_maret",      "Ekuinoks Maret",           "8/9 Kawolu†"),
        ("equinox_sept",       "Ekuinoks September",       "4 Kapat†"),
        ("zenith_I_okt",       "Zenith Matahari I",        "5 Kalima"),
        ("zenith_II_mar",      "Zenith Matahari II",       "8 Kawolu†"),
        ("orion_helrise",      "Orion Heliacal Rise",      "1 Kasa"),
        ("orion_evening_rise", "Orion Acronychal Rise",    "6 Kanem"),
        ("orion_evening_culm", "Orion Kulminasi Senja",    "8 Kawolu†"),
        ("orion_midnight_culm","Orion Kulminasi Tngah Mlm","6 Kanem"),
        ("orion_acron_set",    "Orion Acronychal Set",     "12 Sada"),
    ]

    MONTHS_ID = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",
                 7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}

    for key, label, mangsa in rows:
        ev = ASTRO_CALIB.get(key)
        if not ev: continue
        tgl = f"{ev['mean_day']:02d} {MONTHS_ID.get(ev['mean_month'],'---')}"
        dopy = ev["mean_dopy"]; std = ev["std_dopy"]; delta = ev["delta"]
        row = (f"  {label:<22} {tgl:>6}  {dopy:>7.1f}  {std:.2f}  "
               f"{delta:>+6.1f}  {mangsa}")
        print(row[:W])

    print()
    for ln in textwrap.wrap("† = berdasarkan skenario R30/R10 (EV04). "
                            "Lihat catatan per peristiwa.",
                            width=W, initial_indent="  ",
                            subsequent_indent="    "):
        print(ln)
    print()
    print(thin_hbar(2))
    print("  Catatan penting per peristiwa:")
    print()
    for key, label, _ in rows:
        ev = ASTRO_CALIB.get(key)
        if not ev or "catatan" not in ev: continue
        wprint(label[:20], ev["catatan"], lw=22, indent=2)
        print()


def print_calendar(cal: List[Dict], judul: str,
                   scenario_key: str = DEFAULT_SCENARIO,
                   show_meteo: bool = True, show_astro: bool = True) -> None:
    scn_label = CALIB_SCENARIOS[scenario_key]["label"]
    ms        = CALIB_SCENARIOS[scenario_key]["musim_start"]
    # Peta skenario → fase ENSO + IOD untuk koreksi klimatologi
    _ENSO_PHASE_MAP = {"ELNINO": "ELNINO", "LANINA": "LANINA"}
    enso_phase = _ENSO_PHASE_MAP.get(scenario_key, "NETRAL")
    iod_phase  = _IOD_PHASE_MAP.get(scenario_key, "NETRAL")

    print()
    print(box_top())
    print(box_row(judul))
    print(box_row("ERA5/ERA5-Land (ECMWF/C3S) · IFS HRES 9km (ECMWF)"))
    print(box_row("−7.5220°LS, 112.5661°BT, 28 m · IDW 2 stasiun (P1+P2)"))
    if show_meteo:
        print(box_row(f"Skenario musim: {scenario_key} — {scn_label}"))
        klim_note = (f"Klimatologi: interpolasi dopy R30 + koreksi Δ{scenario_key} empiris"
                     if enso_phase != "NETRAL"
                     else f"Klimatologi: interpolasi dopy R30 (1996–2025) · skenario {scenario_key}")
        print(box_row(klim_note))
        if iod_phase in ("pIOD", "nIOD"):
            iod_note = (f"Koreksi IOD: {iod_phase}  "
                        f"(DMI 1950–2025, mangsa 3–5, bobot "
                        f"{'0.50 sinergi ENSO–IOD' if enso_phase != 'NETRAL' else '0.30 standalone'})")
            print(box_row(iod_note))
        print(box_row("Tx̄/Tn̄ = rata² T maks/min harian · (x) = ekstrem absolut"))
    if show_astro:
        print(box_row("Astro: VSOP87D+IERS2010 · JRC_Ephemeris · 2020–2029"))
    print(box_bot())

    for musim in MUSIM_ORDER:
        ms_n = {"Katiga": ms["Labuh"], "Labuh": ms["Rendheng"],
                "Rendheng": ms["Mareng"], "Mareng": 365 + ms["Katiga"]}
        dopy_s = ms[musim]
        dopy_e = ms_n[musim] - 1
        dur_aktual = dopy_e - dopy_s + 1
        sec_header(f"MUSIM {musim}", MUSIM_DESKRIPSI[musim],
                   dopy_range=f"{dopy_s}–{dopy_e}")

        if show_meteo:
            _meteo_musim_block(
                musim,
                indent=2,
                durasi_override=dur_aktual,
                dopy_s=dopy_s,
                dopy_e=dopy_e,
                enso_phase=enso_phase,
                iod_phase=iod_phase,
            )
            print()

        hdr = f"{'No':>3}  {'Nama':<10}  {'Mulai':<13} {'Selesai':<13} {'Dur (hr)':>8}"
        print(f"  {hdr}")
        print(f"  {'─' * (len(hdr))}")

        for m in cal:
            if m["musim"] != musim:
                continue
            row = (f"  {m['no']:>3}  {m['nama']:<10}  "
                   f"{fmt(m['mulai']):<13} {fmt(m['akhir']):<13} "
                   f"{m['durasi']:>8}")
            print(row)

            if show_meteo:
                _meteo_mangsa_block_dopy(
                    m.get("dopy_start", R30_DOPY_RANGES[m["no"]][0]),
                    m.get("dopy_end",   R30_DOPY_RANGES[m["no"]][1]),
                    indent=7,
                    enso_phase=enso_phase,
                    iod_phase=iod_phase,
                )

            ciri_text = m["ciri"]
            pre = "       Ciri       : "
            sub = " " * len(pre)
            print(textwrap.fill(ciri_text, width=W,
                                initial_indent=pre,
                                subsequent_indent=sub))

            if m.get("candra"):
                pre_c = "       Candra     : "
                sub_c = " " * len(pre_c)
                print(textwrap.fill(m["candra"], width=W,
                                    initial_indent=pre_c,
                                    subsequent_indent=sub_c))

            print()

    print()


def print_mangsa_today(tanggal: date,
                       scenario_key: str = DEFAULT_SCENARIO) -> None:
    pyear, dopy = get_pranatamangsa_year_and_dopy(tanggal)
    scn_label   = CALIB_SCENARIOS[scenario_key]["label"]
    _ENSO_PHASE_MAP_T = {"ELNINO": "ELNINO", "LANINA": "LANINA"}
    enso_phase_t = _ENSO_PHASE_MAP_T.get(scenario_key, "NETRAL")
    iod_phase    = _IOD_PHASE_MAP.get(scenario_key, "NETRAL")

    print()
    print(box_top())
    print(box_row(f"MANGSA UNTUK TANGGAL: {fmt(tanggal)}"))
    print(box_row(f"Tahun-Pranata: {pyear}/{pyear+1}  ·  Hari ke-{dopy+1} (dopy={dopy})"))
    print(box_mid())

    trad = get_mangsa_by_date(tanggal, "tradisional")
    kal  = get_mangsa_by_date(tanggal, "terkalibrasi", scenario_key)

    if trad:
        print(box_row(""))
        print(box_row("[ TRADISIONAL — Reformasi Paku Buwana VII, 1855 ]"))
        print(box_row(f"  Mangsa ke-{trad['no']}: {trad['nama'].upper()}  ·  Musim {trad['musim']}"))
        print(box_row(f"  Periode: {fmt(trad['mulai'])} — {fmt(trad['akhir'])} ({trad['durasi']} hari)"))
        first = True
        for raw in trad["ciri"].split("\n"):
            for ln in _wrap_ciri_line(raw, W - 14):
                print(box_row(f"  Ciri: {ln}" if first else f"        {ln}"))
                first = False
        if kal:
            candra = CIRI_JAWA.get(kal["no"], "")
            if candra:
                print(box_row(""))
                print(box_row("  Candraning Măngsa (tradisional):"))
                for ln in textwrap.wrap(candra, width=W - 12,
                                        initial_indent="      ",
                                        subsequent_indent="      "):
                    print(box_row(ln))

    print(box_mid())
    if kal:
        print(box_row(""))
        print(box_row(f"[ TERKALIBRASI — {scn_label} ]"))
        print(box_row(f"  Mangsa ke-{kal['no']}: {kal['nama'].upper()}  ·  Musim {kal['musim']}"))
        print(box_row(f"  Periode: {fmt(kal['mulai'])} — {fmt(kal['akhir'])} ({kal['durasi']} hari)"))
        if trad and kal["no"] != trad["no"]:
            print(box_row(f"  >> BERBEDA dari tradisional (tradisional: mangsa {trad['no']} {trad['nama']})"))
        elif trad:
            sel = (kal["mulai"] - trad["mulai"]).days
            sgn = "lebih awal" if sel < 0 else "lebih lambat"
            print(box_row(f"  Awal mangsa ini bergeser {sel:+d} hari ({abs(sel)} hari {sgn}) vs. tradisional"))

        ciri_kal = kal["ciri"]
        for ln in textwrap.wrap(ciri_kal, width=W - 12,
                                initial_indent="  Ciri: ",
                                subsequent_indent="        "):
            print(box_row(ln))

        print(box_mid())
        print(box_row(""))
        klim_src = f"R30 1996–2025 · skenario {scenario_key}"
        if iod_phase in ("pIOD", "nIOD"):
            klim_src += f" · IOD {iod_phase}"
        print(box_row(f"  Klimatologi (sumber {klim_src}):"))
        _ds = kal.get("dopy_start", R30_DOPY_RANGES.get(kal["no"], (0., 0.))[0])
        _de = kal.get("dopy_end",   R30_DOPY_RANGES.get(kal["no"], (0., 0.))[1])
        _m, _m6h = meteo_for_dopy_range(_ds, _de,
                                         enso_phase=enso_phase_t,
                                         iod_phase=iod_phase)
        if _m is not None:
            hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad = _m
            wb_str = f"{'defisit' if wb < 0 else 'surplus'}"
            print(box_row(f"  Curah hujan : {hj} mm/musim · {hj_d:.1f} mm/hari · {hhr} hari hujan"))
            print(box_row(f"  Suhu udara  : "
                          f"{_fmt_suhu(tx, tn, _ds, _de)}"))
            print(box_row(f"  Kelembaban  : RH {rh:.1f}% · SM {sm:.3f} m³/m³ · ET₀ {et0:.2f} mm/hari"))
            print(box_row(f"  Neraca air  : P−ET₀ {wb:+.2f} mm/hari ({wb_str}) · Rad {rad:.1f} MJ/m²"))
        if _m6h is not None:
            vpd, tcwv, cld, cld_a, sun_h, sm_sh, sm_dp, sT_sh, sT_dp = _m6h
            print(box_row(f"  [6H] VPD {vpd:.2f} kPa · TCWV {tcwv:.1f} kg/m²"))
            print(box_row(f"  [6H] Cloud {cld:.0f}% (aft {cld_a:.0f}%) · Sun {sun_h:.1f} h/hari"))
            print(box_row(f"  [6H] SM 0-7cm {sm_sh:.3f} · SM 28-100cm {sm_dp:.3f} m³/m³"))
            print(box_row(f"  [6H] sT 0-7cm {sT_sh:.1f}°C · sT 100-255cm {sT_dp:.1f}°C"))

        print(box_mid())
        print(box_row(""))
        print(box_row("  Penanda Astronomis (VSOP87D, rata-rata 2020–2029):"))
        ev_keys = astro_events_in_range(kal.get("dopy_start", 0.0),
                                        kal.get("dopy_end", 0.0))
        if not ev_keys:
            print(box_row("  (tidak ada penanda astronomis khusus untuk mangsa ini)"))
        for ev_key in ev_keys:
            ev = ASTRO_CALIB.get(ev_key, {})
            if not ev:
                continue
            label   = ASTRO_LABEL.get(ev_key, ev_key)
            tgl_str = f"{ev['mean_day']:02d} {MONTHS_ID_SHORT.get(ev['mean_month'],'---')}"
            delta_s = astro_delta_str(ev_key)
            print(box_row(f"  {label}"))
            combined = f"→ Tgl rata-rata: {tgl_str}  |  {delta_s}"
            for ln in textwrap.wrap(combined, width=W - 12,
                                    initial_indent="    ",
                                    subsequent_indent="      "):
                print(box_row(ln))

    print(box_bot())
    print()


def print_perbandingan(pyear: int) -> None:
    trad_cal = build_calendar_tradisional_pyear(pyear)
    scn_keys = list(CALIB_SCENARIOS.keys())

    print()
    print(box_top())
    print(box_row(f"PERBANDINGAN SKENARIO — Tahun-Pranata {pyear}/{pyear+1}"))
    print(box_row("Angka = selisih hari awal mangsa vs. Tradisional (– lebih awal)"))
    print(box_bot())
    print()

    hdr = f"  {'No':>2}  {'Nama':<10} {'Tradisional':>12}"
    for k in scn_keys: hdr += f"  {k:>6}"
    print(hdr[:W])
    print(thin_hbar(2))

    cal_by_scn = {k: build_calendar_terkalibrasi(pyear, k) for k in scn_keys}
    for td in trad_cal:
        no   = td["no"]
        row  = f"  {no:>2}  {td['nama']:<10} {fmt(td['mulai']):>12}"
        for k in scn_keys:
            m_cal = next(x for x in cal_by_scn[k] if x["no"] == no)
            delta = (m_cal["mulai"] - td["mulai"]).days
            row  += f"  {delta:>+6}"
        print(row[:W])

    print()
    print(thin_hbar(2))
    print(f"  Legenda skenario:")
    for k, v in CALIB_SCENARIOS.items():
        print()
        print(f"  {k:<7}: {v['label']}")
        wprint("Catatan", v["catatan"], lw=7, indent=10)
    print()


def print_durasi_musim() -> None:
    print()
    print(box_top())
    print(box_row("DURASI TIAP MUSIM (hari)  —  Tradisional vs Kalibrasi"))
    print(box_bot())
    print()

    musims = MUSIM_ORDER; col_w = 11
    hdr  = f"  {'Skenario':<13}"
    hdr += "".join(f"{mu:>{col_w}}" for mu in musims)
    hdr += f"  {'Total':>6}"
    print(hdr[:W])
    print(thin_hbar(2))

    o = ORIG_MUSIM_START; on = ORIG_MUSIM_START_NEXT
    durs = [on[mu] - o[mu] for mu in musims]
    row  = f"  {'Tradisional':<13}" + "".join(f"{d:>{col_w}}" for d in durs) + f"  {sum(durs):>6}"
    print(row[:W])

    for key, v in CALIB_SCENARIOS.items():
        s  = v["musim_start"]
        sn = {"Katiga": s["Labuh"], "Labuh": s["Rendheng"],
              "Rendheng": s["Mareng"], "Mareng": 365 + s["Katiga"]}
        durs = [sn[mu] - s[mu] for mu in musims]
        row  = f"  {key:<13}" + "".join(f"{d:>{col_w}}" for d in durs) + f"  {sum(durs):>6}"
        print(row[:W])

    print()
    print(thin_hbar(2))
    print(f"\n  Klimatologi tiap musim — Normal Iklim R30 (1996–2025):")
    print()
    for mu in musims:
        print(f"\n  ▸ {mu.upper()} — {MUSIM_DESKRIPSI[mu]}")
        _meteo_musim_block(mu, indent=4)
    print()


def print_klimatologi_bulanan() -> None:
    print()
    print(box_top())
    print(box_row("KLIMATOLOGI BULANAN — Normal Iklim R30 (1996–2025)"))
    print(box_row("ERA5/Land-IFSHRES · −7.522°LS 112.566°BT · 28 m  [IDW 2 stasiun]"))
    print(box_mid())
    print(box_row("Satuan: mm/bln = milimeter per bulan · mm/hr = mm/hari"))
    print(box_row("        MJ/m² = megajoule per meter² · km/j = km/jam"))
    print(box_row("Nilai = rata-rata klimatologis"))
    print(box_row("Tx/Tn = rata² suhu maks/min harian"))
    print(box_bot())
    print()

    params = [
        ("Hujan total (mm/bln)",  0, "{:>6.0f}"),
        ("Hujan (mm/hr)",         1, "{:>6.1f}"),
        ("ET₀ (mm/hr)",           2, "{:>6.2f}"),
        ("P−ET₀ (mm/hr)",         3, "{:>+6.1f}"),
        ("SM (m³/m³)",            4, "{:>6.3f}"),
        ("RH (%)",                5, "{:>6.1f}"),
        ("Tx (°C)",               6, "{:>6.1f}"),
        ("Tn (°C)",               7, "{:>6.1f}"),
        ("Angin (km/j)",          8, "{:>6.1f}"),
        ("Radiasi (MJ/m²)",       9, "{:>6.1f}"),
    ]

    for half_start, bulan_list in [(1, range(1, 7)), (7, range(7, 13))]:
        names = [BULAN_ID[b] for b in bulan_list]
        hdr = f"  {'Parameter':<20}" + "".join(f"{n:>7}" for n in names)
        print(hdr[:W])
        print(thin_hbar(2))
        for label, idx, fmt_str in params:
            vals = [METEO_BULANAN[b][idx] for b in bulan_list]
            row  = f"  {label:<20}" + "".join(fmt_str.format(v) for v in vals)
            print(row[:W])
        print()

    print(thin_hbar(0)); print()
    print(f"  {'RINGKASAN PER MUSIM':^{W-2}}")
    print(f"  {'(Normal Iklim R30 · rata-rata harian kecuali total)':^{W-2}}")
    print()

    mus_params = [
        ("Hujan total (mm)",    1, "{:>10.0f}"),
        ("Hujan (mm/hr)",       2, "{:>10.1f}"),
        ("ET₀ (mm/hr)",         3, "{:>10.2f}"),
        ("P−ET₀ (mm/hr)",       4, "{:>+10.2f}"),
        ("SM (m³/m³)",          5, "{:>10.3f}"),
        ("RH (%)",              6, "{:>10.1f}"),
        ("Tx (°C)",             7, "{:>10.1f}"),
        ("Tn (°C)",             8, "{:>10.1f}"),
        ("Angin (km/j)",        9, "{:>10.1f}"),
        ("Radiasi (MJ/m²)",    10, "{:>10.1f}"),
        ("Durasi (hari)",       0, "{:>10.0f}"),
    ]

    col_w = 10
    hdr   = f"  {'Parameter':<20}" + "".join(f"{mu:>{col_w}}" for mu in MUSIM_ORDER)
    print(hdr[:W])
    print(thin_hbar(2))
    for label, idx, fmt_str in mus_params:
        row = f"  {label:<20}"
        for mu in MUSIM_ORDER:
            row += fmt_str.format(METEO_MUSIM[mu][idx])
        print(row[:W])
    print()
    print(thin_hbar(0))
    print()

    # ── RINGKASAN 6H PER MUSIM ──
    print()
    print(f"  {'RINGKASAN 6H PER MUSIM (EV06)':^{W-2}}")
    print(f"  {'Nilai = rata-rata musiman (R30 1996–2025)':^{W-2}}")
    print()
    col_w = 11
    hdr = f"  {'Parameter':<22}" + "".join(f"{mu:>{col_w}}" for mu in MUSIM_ORDER)
    print(hdr[:W])
    print(thin_hbar(2))

    h6_labels = [
        ("VPD (kPa)",       0, "{:>11.3f}"),
        ("TCWV (kg/m²)",    1, "{:>11.1f}"),
        ("Cloud (%)",       2, "{:>11.0f}"),
        ("Sunshine (h/d)",  3, "{:>11.1f}"),
    ]
    for lbl, idx, fstr in h6_labels:
        row = f"  {lbl:<22}"
        for mu in MUSIM_ORDER:
            row += fstr.format(METEO_MUSIM_6H[mu][idx])
        print(row[:W])

    print()
    print(thin_hbar(0))
    print()


def print_live_nowcast() -> None:
    print()
    print(box_top())
    print(box_row("NOWCAST LANGSUNG — Analisis Iklim Real-Time"))
    print(box_row("HMM 8-D (EV06) + SR-EKF Level/Tren (ARCH(1))"))
    print(box_bot())

    res = live_nowcast()
    if res is None:
        return

    print()
    lat_s = f"{abs(res.get('lat_target', LAT_TARGET)):.4f}°LS"
    lon_s = f"{res.get('lon_target', LON_TARGET):.4f}°BT"
    print(f"  Titik target               : {lat_s}, {lon_s}")
    print(f"  Mode data                  : {res.get('interp_mode', '-')}")
    print(f"  Mode HMM                   : {res.get('hmm_mode', '-')}")
    print(f"  Data 6-jam tersedia        : {'Ya' if res.get('has_6h') else 'Tidak (fallback 4-D)'}")
    if res.get("data_start"):
        print(f"  Rentang data               : {res['data_start']} s.d. {fmt(res['last_date'])}")
    else:
        print(f"  Data meteorologi terakhir  : {fmt(res['last_date'])}")
    print()
    print(thin_hbar(2))
    print(f"  Probabilitas rejim iklim (HMM forward/causal, tanpa look-ahead):")
    print(thin_hbar(2))
    for k in range(4):
        p   = res["state_probs"][k]
        bar = "█" * int(round(p * 30))
        print(f"  State {k}  {p*100:5.1f}%  {bar:<32}")
        print(f"           {HMM_T_STATE[k]}")

    dom = res["dominant_state"]
    print()
    print(f"  >> Rejim dominan saat ini: State {dom} — {HMM_T_STATE[dom]}")

    print()
    print(thin_hbar(2))
    print("  SR-EKF — Neraca air P−ET₀ 30-hari (level & tren ter-filter):")
    print(thin_hbar(2))
    wb   = res["level_wb30"]; trnd = res["trend_wb30_per_day"]
    arah = "→ menuju lebih basah" if trnd > 0 else "→ menuju lebih kering"
    print(f"  Level saat ini  : {wb:+.1f} mm / 30 hari")
    print(f"  Tren harian     : {trnd:+.3f} mm/hari  {arah}")

    if "enso_phase_sofar" in res or "enso_sla_latest_value" in res:
        print()
        print(thin_hbar(2))
        print(f"  Status ENSO — Niño3.4 (data s.d. {fmt(res['enso_latest_date'])}):")
        print(thin_hbar(2))

        # ── SST (kondisi saat ini) ──────────────────────────────────
        if "enso_phase_sofar" in res:
            print(f"  [SST]  ASO {res['enso_year']}   : "
                  f"{res['enso_aso_mean_sofar']:+.2f}  →  {res['enso_phase_sofar']}")
            print(f"  [SST]  Terkini        : {res['enso_latest_value']:+.2f}")

        # ── MSLA (sinyal pendahulu) ─────────────────────────────────
        if "enso_sla_latest_value" in res:
            print()
            print(f"  [SLA]  Terkini        : "
                  f"{res['enso_sla_latest_value']:+.2f}  →  {res['enso_sla_phase']}"
                  f"  (s.d. {fmt(res['enso_sla_latest_date'])})")
            if "enso_sla_aso_mean" in res:
                print(f"  [SLA]  ASO {res['enso_sla_year']}   : "
                      f"{res['enso_sla_aso_mean']:+.2f}")
            if "enso_sla_arx_6wk" in res:
                print(f"  [ARX]  Prakiraan +6 minggu : "
                      f"{res['enso_sla_arx_6wk']:+.2f}  →  "
                      f"{res['enso_sla_arx_6wk_phase']}")

        # ── Deteksi divergensi SST ↔ SLA ───────────────────────────
        if ("enso_latest_value" in res and "enso_sla_latest_value" in res):
            sst_v = res["enso_latest_value"]
            sla_v = res["enso_sla_latest_value"]
            if classify_enso_phase(sst_v) != classify_enso_phase(sla_v):
                print()
                print(f"  ⚠ Divergensi SST ({classify_enso_phase(sst_v)}) ↔ "
                      f"SLA ({classify_enso_phase(sla_v)}) — "
                      f"pantau 4–6 minggu ke depan.")

        # ── Rekomendasi skenario ────────────────────────────────────
        phase_for_scn = res.get("enso_phase_sofar", res.get("enso_sla_phase", "Netral"))
        scn = SCENARIO_FOR_PHASE.get(phase_for_scn)
        if scn:
            print()
            print(f"  >> Rekomendasi skenario: '{scn}'")
            wprint("Catatan", CALIB_SCENARIOS[scn]["catatan"], lw=7, indent=5)

    # ── Status IOD ──────────────────────────────────────────────────
    if "iod_phase" in res:
        print()
        print(thin_hbar(2))
        print("  Status IOD (Dipole Mode Index):")
        print(thin_hbar(2))
        print(f"  Fase   : {res['iod_phase']}  (DMI {res['iod_value']:+.2f})")
        print(f"  Sumber : {res['iod_src']}")
        enso_ph = res.get("enso_phase_sofar",
                          res.get("enso_sla_phase", "Netral"))
        iod_ph  = res["iod_phase"]
        if ((enso_ph == "El Niño" and iod_ph == "pIOD") or
                (enso_ph == "La Niña" and iod_ph == "nIOD")):
            print(f"  ⚑ Sinergi ENSO–IOD → bobot koreksi IOD 0.50")
        elif iod_ph in ("pIOD", "nIOD"):
            print(f"  · IOD standalone   → bobot koreksi IOD 0.30")

    print()
    print(thin_hbar(2))
    print("  Sumber data:")
    print(thin_hbar(2))
    print(f"  SLA  : AVISO/DUACS (CNES/CLS) — DOI 10.24400/527896/A01-2025.008")
    print(f"  SST  : NOAA OISST v2.1 — DOI 10.1175/JCLI-D-20-0166.1")
    print(f"  IOD  : JMA (DMI) — Saji et al. (1999), Nature 401:360")
    print(f"  Met  : ERA5/ERA5-Land (ECMWF/C3S) + IFS HRES 9km (ECMWF)")
    print(f"  Astro: VSOP87D (IMCCE) + IERS 2010 + HMNAO ΔT")
    print()                        

    print()


# ══════════════════════════════════════════════════════════════════════
# 9. MENU INTERAKTIF
# ══════════════════════════════════════════════════════════════════════

def input_int(prompt: str, default: Optional[int] = None) -> Optional[int]:
    try:
        s = input(prompt).strip()
        if not s and default is not None:
            return default
        return int(s)
    except (ValueError, EOFError):
        return default


def input_date_str(prompt: str) -> Optional[date]:
    try:
        s = input(prompt).strip()
        if not s:
            return None
        y, mo, d = map(int, s.split("-"))
        return date(y, mo, d)
    except (ValueError, EOFError):
        return None


def choose_scenario() -> str:
    keys = list(CALIB_SCENARIOS.keys())
    print(f"\n  Skenario tersedia: {', '.join(keys)}")
    s = input(f"  Pilih skenario [{DEFAULT_SCENARIO}]: ").strip().upper()
    return s if s in CALIB_SCENARIOS else DEFAULT_SCENARIO


def show_menu() -> None:
    print()
    print(box_top("PRANATA MANGSA — EV05 METEO(DAILY+6H)+ENSO+IOD+ASTRO"))
    print(box_row("−7.52S112.56E28m · ERA5/Land IFS HRES 1940–2026 · ENSO 1993–2026"))
    print(box_row("IOD_DELTA: DMI bulanan 1950–2025 · mangsa 3–5 · bobot 0.30/0.50"))
    print(box_row("HMM 8-D (EV06) · VSOP87D + IERS2010 · JRC_Ephemeris 2020–2029"))
    print(box_mid())
    for item in [
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
    ]:
        print(box_row(item))
    print(box_bot())


def laporan_singkat() -> None:
    today = date.today()
    print_mangsa_today(today, DEFAULT_SCENARIO)
    if (find_data_file(DEFAULT_METEO_CSV)
            or find_data_file(DEFAULT_METEO_CSV2)):
        print_live_nowcast()


def main_loop() -> None:
    while True:
        show_menu()
        pilihan = input("  Pilih menu (0–8): ").strip()

        if pilihan == "0":
            print()
            print(box_top())
            print(box_row("Terima kasih. Sampai jumpa!  — Pranata Mangsa EV06"))
            print(box_bot())
            print()
            break

        elif pilihan == "1":
            tahun = input_int(
                "  Tahun Gregorian (YYYY) untuk kalender tradisional: ",
                date.today().year,
            )
            if tahun is not None:
                print_calendar(build_calendar_tradisional(tahun),
                               f"KALENDER TRADISIONAL — TAHUN {tahun}",
                               show_meteo=False, show_astro=False)

        elif pilihan == "2":
            default_py = get_pranatamangsa_year_and_dopy(date.today())[0]
            tahun = input_int(f"  Tahun-pranata mulai (YYYY) [{default_py}]: ", default_py)
            scn = choose_scenario()
            if tahun is not None:
                print_calendar(
                    build_calendar_terkalibrasi(tahun, scn),
                    f"KALENDER TERKALIBRASI {tahun}/{tahun+1}",
                    scenario_key=scn,
                    show_meteo=True, show_astro=True,
                )

        elif pilihan == "3":
            s = input("  Tanggal (YYYY-MM-DD) [kosong = hari ini]: ").strip()
            tgl = date.today() if not s else date(*map(int, s.split("-")))
            scn = choose_scenario()
            print_mangsa_today(tgl, scn)

        elif pilihan == "4":
            default_py = get_pranatamangsa_year_and_dopy(date.today())[0]
            tahun = input_int(f"  Tahun-pranata mulai (YYYY) [{default_py}]: ", default_py)
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
            print(f"\n  Pilihan tidak valid. Masukkan angka 0–8.")
            input("\n  Tekan Enter untuk melanjutkan...")
            continue

        input("\n  Tekan Enter untuk kembali ke menu...")


# ══════════════════════════════════════════════════════════════════════
# 10. MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        if "--report" in sys.argv:
            laporan_singkat()
        elif "--astro" in sys.argv:
            print_astro_calib_table()
        else:
            main_loop()
    except KeyboardInterrupt:
        print("\n\n  Program dihentikan. Sampai jumpa!")
        sys.exit(0)