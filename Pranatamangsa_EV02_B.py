#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pranatamangsa_EV02.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KALENDER PRANATA MANGSA — TERKALIBRASI METEOROLOGI, ENSO & ASTRONOMIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EV02 = EV01 (kalibrasi meteorologi/ENSO) + kalibrasi astronomis presisi
menggunakan JRC_Ephemeris v5.0 (VSOP87D + IERS 2010 nutasi penuh + ΔT HMNAO).

SUMBER DATA METEOROLOGI (sama dengan EV01)
  · Titik Target  : −7.5220°LS, 112.5661°BT (MJS Obs., EAST JAVA)
  · Stasiun P1    : ERA5/ERA5LandOpen/IFSHRES Open-Meteo — 1950–2026
                    Koordinat: −7.487°LS, 112.538°BT · Elev: 28 m dpl
  · Stasiun P2    : ERA5/ERA5LandOpen/IFSHRES Open-Meteo — 1940–2026
                    Koordinat: −7.557°LS, 112.557°BT · Elev: 28 m dpl
    Interpolasi   : Inverse Distance Weighting (IDW, power=2)
  · ENSO Niño3.4 mingguan — AVISO/DUACS, 1993–2026

SUMBER DATA ASTRONOMIS (baru di EV02)
  · Efemerida     : VSOP87D (akurasi ~1″) via JRC_Ephemeris v5.0
  · Nutasi & presesi: IERS 2010, tabel lengkap (IAU 2000A/2006A)
  · ΔT (TT−UTC)   : Tabel HMNAO interpolasi linier
  · Rentang kalibrasi: 2020–2029 (10 tahun rata-rata)
  · Lokasi        : −7.521951°LS, 112.566089°BT, 28 m dpl
  · Bintang       : Sabuk Orion (Alnitak, Alnilam, Mintaka) rata-rata

PERISTIWA ASTRONOMIS YANG DIKALIBRASI (rata-rata 2020–2029)
  ┌─────────────────────────────────────────────┬──────────┬──────────┬──────────┐
  │ Peristiwa                                   │ Tgl rata │  dopy    │ Trad dpy │
  ├─────────────────────────────────────────────┼──────────┼──────────┼──────────┤
  │ Solstis Juni     (λ☉=90°)                   │ 21 Jun   │   -0.81  │    0     │
  │ Solstis Desember (λ☉=270°)                  │ 21 Des   │  182.71  │  184     │
  │ Ekuinoks Maret   (λ☉=0°)                    │ 20 Mar   │  271.75  │  273     │
  │ Ekuinoks September (λ☉=180°)                │ 23 Sep   │   92.85  │   92     │
  │ Zenith Matahari I   (δ☉=−7.52°, okt)        │ 12 Okt   │  112.37  │  113     │
  │ Zenith Matahari II  (δ☉=−7.52°, mar)        │ 01 Mar   │  252.46  │  253     │
  │ Orion Heliacal Rise (terbit fajar)           │ 25 Jun   │    3.11  │    0     │
  │ Orion Acronychal Rise (pertama terlihat senja) │ 05 Des   │  166.16  │  167     │
  │ Orion Kulminasi Senja (Evening Heliacal Culm) │ 01 Mar   │  252.50  │  253     │
  │ Orion Kulminasi Tengah Malam (HA=0° 00:00)  │ 08 Des   │  168.91  │  252*    │
  │ Orion Acronychal Set (terakhir terlihat senja)│ 18 Jun   │  361.93  │  347**   │
  └─────────────────────────────────────────────┴──────────┴──────────┴──────────┘
  *  Trad. dopy≈252 (1 Mar) merujuk Evening Heliacal Culmination (kulminasi SENJA),
     bukan transit siang; kulminasi tengah malam terjadi 8 Des (∆≈−84 hari).
  ** Trad. dopy=347 (4 Jun) merujuk heliacal set fajar (∆≈+15 hr dari acronychal set)

TEMUAN KALIBRASI ASTRONOMIS (EV02 vs EV01)
  · Jangkar awal tahun (Solstis Juni): terjadi 21 Jun (~0.81 hari sebelum 22 Jun tradisional)
    → Koreksi kecil −1 hari: jangkar presisi = 21 Jun.
  · Solstis Desember: 21 Des (bukan 22 Des tradisional), dopy 182.71 vs 184.
  · Zenith Matahari I: 12 Okt (bukan 13 Okt tradisional).
  · Zenith Matahari II: 1 Mar (sama dengan tradisional, ∆−0.54 hr, tidak signifikan).
  · Orion Heliacal Rise: 25 Jun (dopy ~3.1, bukan 22 Jun/dopy=0 tradisional).
    → Koreksi: Mangsa-1 Kasa TIDAK dimulai dari heliacal rise Orion.
    → Orion baru terlihat pertama kali ~3 hari setelah solstis juni.
  · Orion Evening Rise (first visible at dusk): 5 Des (dopy=166.16, vs 6 Des/dopy=167).
    → Konsisten dengan tradisional dalam ±1 hari.
  · Orion Evening Heliacal Culmination (kulminasi senja): ~1 Mar (dopy≈252.5).
    → Cocok dengan tradisional "1 Mar" (Mangsa-9). Kulminasi terjadi jam ~18:30 WIB,
       yakni saat senja (matahari baru terbenam ~37-60 menit sebelumnya).
       Ammarell (1991) Tabel 3: epoch 1850 = 26 Feb, epoch 2025 ≈ 1 Mar.
  · Orion Kulminasi Tengah Malam: 8 Des (dopy=168.91).
    → BERBEDA dari kulminasi senja (1 Mar). Pada 8 Des, Orion berkulminasi
       tepat tengah malam 00:00 WIB. Bukan tentang "transit siang".
  · Orion Acronychal Set: 18 Jun (dopy=361.93, vs 4 Jun/dopy=347 tradisional).
    → Jika pakai definisi heliacal set fajar: Alnilam tak terlihat di fajar ≈ 25 Jun
       (tepat bersamaan dengan heliacal rise berikutnya).

DAMPAK KE KALENDER TERKALIBRASI
  · Pergeseran jangkar awal tahun: −1 hari (dari 22 Jun → 21 Jun presisi).
    Untuk konsistensi tampilan, ANCHOR_DAY tetap 22 Jun, namun ASTRO_CALIB
    menyimpan nilai presisi.
  · Kalibrasi R30 (skenario utama) TIDAK diubah karena berbasis meteorologi.
  · Fungsi baru: tabel ASTRO_CALIB tersedia untuk referensi presisi dan
    untuk menentukan offset astronomi saat menampilkan ciri mangsa.
  · CIRI mangsa yang menyebut Orion diperbarui dengan tanggal astronomis presisi.

CATATAN KETERBATASAN
  · Kalibrasi meteorologi (12 mangsa via time-warp musim) tetap dari EV01.
  · Kalibrasi astronomis tidak mengubah batas musim/mangsa; hanya mengkoreksi
    referensi tanggal dalam teks deskripsi (CIRI).
  · Pergeseran astronomis terkecil: zenith & solstis <1 hari → praktis tidak
    mengubah kalender. Pergeseran Orion heliacal rise +3 hr dan acronychal set
    +15 hr vs tradisional — ini mencerminkan pergeseran precession ~170 tahun
    (1855→2025) sebesar ~2°.
  · Kulminasi tengah malam Orion (8 Des) vs tradisional (1 Mar) adalah perbedaan
    DEFINISI bukan presesi — tradisional mengacu transit siang, EV02 mengacu
    tengah malam.
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

W   = 70        # Lebar konsol (karakter)
IND = "  "      # Indentasi standar (2 spasi)

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

# ── Box / border helpers ──────────────────────────────────────────────

def box_top(title: str = "") -> str:
    if not title:
        return "╔" + "═" * (W - 2) + "╗"
    inner = f"  {title}  "
    pad = W - 2 - len(inner)
    if pad < 0:
        inner = inner[:W - 2]
        pad = 0
    l = pad // 2
    return "╔" + "═" * l + inner + "═" * (pad - l) + "╗"

def box_mid() -> str:
    return "╠" + "═" * (W - 2) + "╣"

def box_bot() -> str:
    return "╚" + "═" * (W - 2) + "╝"

def box_row(text: str) -> str:
    safe = str(text)[: W - 4]
    return "║  " + safe + " " * (W - 4 - len(safe)) + "  ║"

def hbar(ch: str = "─") -> str:
    return ch * W

def thin_hbar(indent: int = 2) -> str:
    return " " * indent + "─" * (W - indent)

# ── Section headers ───────────────────────────────────────────────────

def sec_header(label: str, sub: str = "", dopy_range: str = "") -> None:
    right = f"[dopy: {dopy_range}]" if dopy_range else ""
    title = f"▌▌ {label.upper()}"
    if sub:
        title += f" — {sub}"
    gap = W - len(title) - len(right)
    line = title + (" " * max(1, gap)) + right if right else title
    print()
    print(line[:W])
    print(thin_hbar(0))

def mini_header(label: str) -> None:
    print(f"\n{IND}{'─' * (W - 4)}")
    print(f"{IND}{label}")
    print(f"{IND}{'─' * (W - 4)}")

# ── Text wrapping ─────────────────────────────────────────────────────

def wline(label: str, value: str, lw: int = 12, indent: int = 6) -> str:
    pre     = " " * indent + f"{label:<{lw}}: "
    sub_ind = " " * (indent + lw + 2)
    return textwrap.fill(
        value,
        width=W,
        initial_indent=pre,
        subsequent_indent=sub_ind,
    )

def wprint(label: str, value: str, lw: int = 12, indent: int = 6) -> None:
    print(wline(label, value, lw, indent))

def wrap_print(text: str, indent: int = 6) -> None:
    pre = " " * indent
    print(textwrap.fill(text, width=W, initial_indent=pre,
                        subsequent_indent=pre))


# ══════════════════════════════════════════════════════════════════════
# 1. DATA DASAR PRANATA MANGSA TRADISIONAL  (tidak diubah — referensi)
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

# ── CIRI mangsa (diperbarui EV02 dengan tanggal astronomis presisi) ──
CIRI = {
    1:  ("Solstis Juni 21 Jun (λ☉=90°, dopy≈−0.8). Weluku/Orion terbit fajar "
         "~25 Jun (dopy≈3.1, 3 hr setelah solstis). "
         "Awal tahun pertanian; membersihkan lahan, tanah kering maksimum."),
    2:  ("Pohon randu/kapuk mulai berdaun. Tanah retak. "
         "Pengolahan lahan kering."),
    3:  "Puncak kemarau, sumur mengering. Panen palawija (jagung, kacang).",
    4:  ("Burung gelatik di sawah, manyar membuat sarang. "
         "Angin mulai berubah ke barat."),
    5:  ("Zenith Matahari I: 12 Okt (δ☉=−7.52°, dopy≈112.4, "
         "1 hr lebih awal dari tradisional). "
         "Awal hujan. Pleiades terlihat di senja. Embun beracun."),
    6:  ("Weluku/Orion Acronychal Rise (pertama terlihat di senja): ~5 Des "
         "(dopy≈166.2, 1 hr lebih awal dari tradisional 6 Des). "
         "Kulminasi tengah malam Orion: ~8 Des (dopy≈168.9). "
         "Hujan lebat. Menabur benih padi."),
    7:  ("Solstis Desember: 21 Des (dopy≈182.7, 1.3 hr lebih awal dari "
         "tradisional 22 Des). "
         "Pleiades setinggi pecat sawad (~50°). Memindah bibit padi ke sawah."),
    8:  "Transplantasi selesai. Pleiades kulminasi di senja. Padi tumbuh.",
    9:  ("Zenith Matahari II: 1 Mar (δ☉=−7.52°, dopy≈252.5, konsisten tradisional). "
         "Orion berkulminasi (transit meridian, alt≈84°) waktu senja ~18:30 WIB "
         "(Evening Heliacal Culmination, ~26 Feb/1 Mar — Ammarell 1991 Tbl.3: "
         "epoch 1850 = 26 Feb, epoch kini ≈1 Mar). "
         "Jangkrik berbunyi. Padi berbulir."),
    10: "Hujan reda, angin timur. Panen raya mulai.",
    11: ("Orion terbalik di barat (terbenam awal). "
         "Kapuk mekar. Hutang dilunasi."),
    12: ("Orion terakhir terlihat senja: ~18 Jun (dopy≈361.9, acronychal set). "
         "Perkiraan tradisional 4 Jun (heliacal set fajar, dopy≈347) berbeda "
         "definisi (+15 hr). Panen selesai. Masa bera (Apit Lemah)."),
}

ANCHOR_MONTH, ANCHOR_DAY = 6, 22   # Jangkar tampilan tetap 22 Jun


def is_leap_year(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def orig_dopy_table() -> Dict[int, int]:
    out, cum = {}, 0
    for m in MANGSAS:
        out[m["no"]] = cum
        cum += m["durasi"]
    return out


ORIG_DOPY = orig_dopy_table()
ORIG_MUSIM_START = {
    mu: ORIG_DOPY[mem[0]] for mu, mem in MUSIM_MEMBERS.items()
}
ORIG_MUSIM_START_NEXT = {
    "Katiga":   ORIG_MUSIM_START["Labuh"],
    "Labuh":    ORIG_MUSIM_START["Rendheng"],
    "Rendheng": ORIG_MUSIM_START["Mareng"],
    "Mareng":   365 + ORIG_MUSIM_START["Katiga"],
}


# ══════════════════════════════════════════════════════════════════════
# 2. KALIBRASI ASTRONOMIS (BARU DI EV02)
#    Dihitung oleh astro_calibration_extractor.py menggunakan
#    JRC_Ephemeris v5.0 — VSOP87D + IERS 2010 + ΔT HMNAO
#    Rata-rata 2020–2029 dari −7.521951°LS, 112.566089°BT, 28 m dpl
# ══════════════════════════════════════════════════════════════════════

ASTRO_CALIB = {
    # ─── Solstis & Ekuinoks ───────────────────────────────────────────
    "solstis_juni": {
        # Terjadi 21 Jun; 0.81 hari SEBELUM jangkar tradisional 22 Jun
        # Signifikansi: awal tahun-pranata sesungguhnya = 21 Jun
        "mean_dopy":   -0.81,   # hari ke-x dari 22 Jun (negatif = sebelum)
        "std_dopy":     0.27,   # σ antar-tahun
        "mean_month":   6,
        "mean_day":    21,
        "trad_dopy":    0,      # tradisional menganggap = hari ke-0 (22 Jun)
        "delta":       -0.81,   # koreksi vs tradisional (hari)
        "catatan": ("Solstis Juni terjadi rata-rata 21 Jun ~11:00 WIB. "
                    "Jangkar tradisional 22 Jun terlambat ~20 jam dari solstis "
                    "sesungguhnya. Koreksi kecil; kalender tetap memakai 22 Jun "
                    "sebagai jangkar tampilan."),
    },
    "solstis_des": {
        # Terjadi 21 Des (bukan 22 Des tradisional untuk Kapitu)
        "mean_dopy":  182.71,
        "std_dopy":    0.28,
        "mean_month":  12,
        "mean_day":   21,
        "trad_dopy":  184,
        "delta":       -1.29,
        "catatan": ("Solstis Desember terjadi rata-rata 21 Des, 1.3 hari lebih "
                    "awal dari asumsi tradisional Mangsa-7 (22 Des/dopy=184). "
                    "Mangsa Kapitu secara astronomis dimulai ~21 Des."),
    },
    "equinox_maret": {
        "mean_dopy":  271.75,
        "std_dopy":    0.30,
        "mean_month":   3,
        "mean_day":   20,
        "trad_dopy":  273,      # dihitung dari 22 Jun tahun sebelumnya
        "delta":       -1.25,
        "catatan": ("Ekuinoks Maret terjadi rata-rata 20 Mar (~11:00 WIB), dopy≈271.8. "
                    "Jatuh di dalam Mangsa-9 (Kasanga, dopy 252–276). "
                    "Ekuinoks tidak dikenal sebagai penanda mangsa dalam tradisi "
                    "Pranata Mangsa; dicantumkan sebagai titik referensi astronomis. "
                    "Posisinya ~19 hari setelah awal Kasanga (1 Mar)."),
    },
    "equinox_sept": {
        "mean_dopy":   92.85,
        "std_dopy":    0.27,
        "mean_month":   9,
        "mean_day":   23,
        "trad_dopy":   92,
        "delta":       +0.85,
        "catatan": ("Ekuinoks September terjadi rata-rata 23 Sep (~07:00 WIB), dopy≈92.9. "
                    "Jatuh di dalam Mangsa-4 (Kapat, dopy 88–112), tepat 5 hari setelah "
                    "awal Kapat (18 Sep). Ekuinoks tidak digunakan sebagai penanda mangsa "
                    "dalam tradisi Pranata Mangsa; dicantumkan sebagai referensi astronomis."),
    },
    # ─── Zenith Matahari (Titik Kulminasi Matahari) ───────────────────
    "zenith_I_okt": {
        # Matahari melintas deklinasi −7.52° (lintang MJS) bergerak ke selatan
        "mean_dopy":  112.37,
        "std_dopy":    0.27,
        "mean_month":  10,
        "mean_day":   12,
        "trad_dopy":  113,      # tradisional: 13 Okt (Mangsa-5)
        "delta":       -0.63,
        "catatan": ("Zenith passage I (matahari tepat di atas kepala) terjadi "
                    "rata-rata 12 Okt (~09:00 WIB), 0.6 hari lebih awal dari "
                    "tradisional 13 Okt. Penanda awal Mangsa-5 (Kalima)."),
    },
    "zenith_II_mar": {
        # Matahari melintas deklinasi −7.52° bergerak ke utara
        "mean_dopy":  252.46,
        "std_dopy":    0.27,
        "mean_month":   3,
        "mean_day":    1,
        "trad_dopy":  253,      # tradisional: 1 Mar (Mangsa-9)
        "delta":       -0.54,
        "catatan": ("Zenith passage II terjadi 1 Mar (~10:00 WIB), konsisten "
                    "dengan tradisional (∆ < 1 hari). Penanda tengah Mangsa-9 "
                    "(Kasanga)."),
    },
    # ─── Peristiwa Orion (Sabuk: Alnitak, Alnilam, Mintaka) ──────────
    "orion_helrise": {
        # Hari pertama sabuk Orion terlihat di langit fajar
        # Kriteria: bintang terbit saat matahari ≥ 12° di bawah horizon
        "mean_dopy":    3.11,
        "std_dopy":     0.40,
        "mean_month":   6,
        "mean_day":    25,
        "trad_dopy":    0,      # tradisional: 22 Jun = bersamaan solstis
        "delta":       +3.11,
        "catatan": ("Heliacal rise Weluku/Orion terjadi rata-rata 25 Jun "
                    "(3.1 hari setelah solstis). Karena presesi sejak 1855, "
                    "Orion kini terbit ~3 hari setelah solstis, bukan bersamaan. "
                    "Ini menjelaskan mengapa tradisi 22 Jun untuk Orion kini "
                    "sedikit tidak tepat."),
    },
    "orion_evening_rise": {
        # Hari pertama sabuk Orion terlihat di langit senja (timur) = Acronychal Rise
        # Kriteria: saat senja nautical (sun_alt=−8°), Orion sudah di atas horizon timur
        # Disebut juga 'Acronychal Rise': bintang terbit di timur tepat saat matahari terbenam
        "mean_dopy":  166.16,
        "std_dopy":    0.46,
        "mean_month":  12,
        "mean_day":    5,
        "trad_dopy":  167,      # tradisional: 6 Des (Mangsa-6)
        "delta":       -0.84,
        "catatan": ("Weluku/Orion pertama terlihat di langit senja (Acronychal Rise): "
                    "rata-rata 5 Des (~18:30 WIB). Pada saat ini Orion baru terbit di "
                    "cakrawala timur tepat saat matahari terbenam. Konsisten dengan "
                    "tradisional 6 Des (∆ = −0.8 hari). Penanda awal Mangsa-6 (Kanem). "
                    "Dalam literatur Jawa: 'Wluku erscheint am östlichen Abendhimmel' "
                    "(Van den Bosch 1980)."),
    },
    "orion_evening_culm": {
        # Hari ketika Orion (Alnilam) pertama kali berkulminasi (transit meridian)
        # tepat saat senja (matahari baru terbenam, bintang baru mulai terlihat)
        # = Evening Heliacal Culmination (Ammarell 1991, Tabel 3)
        # Epoch 1850: 26 Feb; epoch 2020-2029: ~1 Mar
        "mean_dopy":  252.5,
        "std_dopy":    0.40,
        "mean_month":   3,
        "mean_day":    1,
        "trad_dopy":  253,      # tradisional: 1 Mar (Mangsa-9)
        "delta":       -0.5,
        "catatan": ("Evening Heliacal Culmination Orion (kulminasi senja): "
                    "Orion transit meridian (alt≈84°) tepat saat senja ~18:30 WIB, "
                    "terjadi rata-rata ~26 Feb–1 Mar (dopy≈252). "
                    "Ammarell (1991) Tabel 3 mencatat epoch 1850 = 26 Feb, "
                    "altitude 84°; epoch kini bergeser ~2–3 hari akibat presesi. "
                    "Inilah penanda astronomis Mangsa-9 (Kasanga) yang sesungguhnya. "
                    "Jangan disamakan dengan kulminasi tengah malam (8 Des)."),
    },
    "orion_midnight_culm": {
        # Hari ketika Alnilam berkulminasi (HA=0°) tepat tengah malam WIB (00:00)
        # Berbeda dari evening heliacal culmination (~1 Mar/dopy≈252)
        "mean_dopy":  168.91,
        "std_dopy":    0.40,
        "mean_month":  12,
        "mean_day":    8,
        "trad_dopy":  252,      # tradisional: ~26 Feb/1 Mar = evening heliacal culmination
        "delta":      -83.09,
        "catatan": ("Kulminasi TENGAH MALAM Orion: ~8 Des (dopy≈168.9, ~00:00 WIB). "
                    "Ini BERBEDA dari 'evening heliacal culmination' (~26 Feb/1 Mar/dopy≈252) "
                    "yang terjadi waktu senja. "
                    "Pada 1 Mar, Orion berkulminasi sekitar 18:30 WIB (senja hari), "
                    "bukan siang hari. Pada 8 Des, Orion tepat di meridian saat tengah malam. "
                    "Perbedaan ~84 hari antara kulminasi tengah malam (8 Des) dan "
                    "kulminasi senja (1 Mar) mencerminkan pergeseran sidereal ~12 jam."),
    },
    "orion_acron_set": {
        # Hari terakhir Orion masih di atas horizon saat matahari terbenam
        # (Orion terakhir terlihat di langit barat senja)
        "mean_dopy":  361.93,
        "std_dopy":    0.50,
        "mean_month":   6,
        "mean_day":   18,
        "trad_dopy":  347,      # tradisional: 4 Jun (heliacal set fajar)
        "delta":      +14.93,
        "catatan": ("Acronychal set (Orion terakhir di atas horizon saat sunset): "
                    "rata-rata 18 Jun (dopy≈361.9). "
                    "Tradisional 4 Jun (dopy=347) menggunakan definisi heliacal "
                    "set fajar yang berbeda (+15 hari lebih awal). "
                    "Perbedaan ini mencerminkan presesi ~2° sejak 1855."),
    },
}

# ── Fungsi bantu akses ASTRO_CALIB ────────────────────────────────────

def astro_event_date(key: str, year: int) -> Optional[date]:
    """Kembalikan tanggal perkiraan peristiwa astronomis untuk tahun tertentu."""
    ev = ASTRO_CALIB.get(key)
    if not ev:
        return None
    # Tentukan tahun berdasarkan bulan (untuk peristiwa melintas batas tahun)
    month = ev["mean_month"]
    day   = ev["mean_day"]
    # Peristiwa Jun-Des: di tahun pranata (pyear)
    # Peristiwa Jan-Mei: di tahun berikutnya (pyear+1)
    actual_year = year if month >= 6 else year + 1
    try:
        return date(actual_year, month, day)
    except ValueError:
        return date(actual_year, month, min(day, 28))

def astro_delta_str(key: str) -> str:
    """Ringkasan singkat koreksi astronomis vs tradisional."""
    ev = ASTRO_CALIB.get(key)
    if not ev:
        return ""
    delta = ev["delta"]
    if abs(delta) < 0.5:
        return f"Δ={delta:+.1f} hr (konsisten tradisional)"
    arah = "lebih awal" if delta < 0 else "lebih lambat"
    return f"Δ={delta:+.1f} hr ({abs(delta):.1f} hr {arah} dari tradisional)"


# ══════════════════════════════════════════════════════════════════════
# 3. HASIL KALIBRASI METEOROLOGI (dari EV01 — tidak berubah)
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
        "musim_start": {"Katiga": 9,  "Labuh": 93, "Rendheng": 231, "Mareng": 265},
        "catatan":    ("Paling responsif thd tren terbaru; sampel kecil & "
                       "dipengaruhi ENSO 2023–24 yang kuat."),
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
# 4. KLIMATOLOGI EMPIRIS TERSEMAT (identik EV01)
# ══════════════════════════════════════════════════════════════════════

METEO_MANGSA: Dict[int, Tuple] = {
    #         hjan  h/hr hhr  et0    wb    sm     rh    Tx   Tn  angin rad
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
    #              dur hjan  h/hr  et0    wb    sm     rh    Tx   Tn  angin rad
    "Katiga":  (  75,   60,  0.8, 4.64, -3.84, 0.180, 66.1, 32.6, 21.8, 10.3, 20.8),
    "Labuh":   ( 114,  978,  8.6, 4.32,  4.26, 0.290, 74.5, 32.3, 23.3,  9.9, 19.7),
    "Rendheng": ( 78, 1140, 14.6, 3.53, 11.09, 0.390, 84.2, 29.9, 23.0, 10.3, 17.4),
    "Mareng":  (  98,  453,  4.6, 3.79,  0.82, 0.310, 77.6, 31.1, 22.9,  8.5, 18.1),
}

METEO_BULANAN: Dict[int, Tuple] = {
    #       hjan_bln h/hr  et0    wb     sm     rh    Tx   Tn  angin  rad
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


# ══════════════════════════════════════════════════════════════════════
# 5. PARAMETER HMM TRAILING/CAUSAL (identik EV01)
# ══════════════════════════════════════════════════════════════════════

HMM_T_pi     = [0.0, 1.0, 0.0, 0.0]
HMM_T_A      = [
    [0.9425, 0.0575, 0.0000, 0.0000],
    [0.0529, 0.8872, 0.0000, 0.0600],
    [0.0000, 0.0000, 0.9543, 0.0457],
    [0.0000, 0.0574, 0.0516, 0.8909],
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


# ══════════════════════════════════════════════════════════════════════
# 6. FUNGSI TANGGAL & KALENDER (identik EV01)
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
        })
    return calendar


def build_calendar_terkalibrasi(pyear: int, scenario_key: str = DEFAULT_SCENARIO) -> List[Dict]:
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
        calendar.append({
            "no": no, "nama": m["nama"], "mulai": start,
            "akhir": end, "durasi": (end - start).days + 1,
            "musim": musim, "ciri": CIRI.get(no, ""),
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


# ══════════════════════════════════════════════════════════════════════
# 7. NOWCAST (identik EV01)
# ══════════════════════════════════════════════════════════════════════

DEFAULT_METEO_CSV  = "open-meteo-7.49S112.54E28m.csv"
DEFAULT_METEO_CSV2 = "open-meteo-7.56S112.56E28m.csv"
DEFAULT_ENSO_CSV   = "Sst_nino34_index.csv"

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


def hmm_causal_filter(Xz: np.ndarray) -> np.ndarray:
    pi   = np.array(HMM_T_pi) + 1e-12;  pi /= pi.sum()
    A    = np.array(HMM_T_A)
    n, K = len(Xz), 4
    logB = np.column_stack(
        [_log_mvn(Xz, HMM_T_means[k], HMM_T_covs[k]) for k in range(K)]
    )
    alpha  = pi * np.exp(logB[0] - logB[0].max());  alpha /= alpha.sum()
    probs  = [alpha]
    for t in range(1, n):
        pred  = alpha @ A
        w     = np.exp(logB[t] - logB[t].max())
        alpha = pred * w;  alpha /= alpha.sum()
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
    for folder in (".", os.path.dirname(os.path.abspath(__file__))):
        p = os.path.join(folder, filename)
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


def load_interpolated_meteo(csv1=DEFAULT_METEO_CSV, csv2=DEFAULT_METEO_CSV2,
                             lat_t=LAT_TARGET, lon_t=LON_TARGET):
    if not HAS_PANDAS:
        return None
    path1 = find_data_file(csv1)
    path2 = find_data_file(csv2)
    if path1 is None and path2 is None:
        return None

    w1, w2 = _idw_weights(lat_t, lon_t, [(LAT_P1, LON_P1), (LAT_P2, LON_P2)])

    def _read(path):
        df = pd.read_csv(path, skiprows=3)
        df["time"] = pd.to_datetime(df["time"])
        return df.sort_values("time").set_index("time")

    if path1 is None:
        return _read(path2).reset_index()
    if path2 is None:
        return _read(path1).reset_index()

    df1 = _read(path1)
    df2 = _read(path2)
    shared_cols = [c for c in df1.columns if c in df2.columns]
    extra_cols  = [c for c in df2.columns if c not in df1.columns]
    all_dates   = df1.index.union(df2.index)
    out = pd.DataFrame(index=all_dates)
    out.index.name = "time"
    for col in shared_cols:
        v1 = df1[col].reindex(all_dates)
        v2 = df2[col].reindex(all_dates)
        both  = v1.notna() & v2.notna()
        only1 = v1.notna() & ~v2.notna()
        only2 = ~v1.notna() & v2.notna()
        out[col] = np.nan
        out.loc[both,  col] = w1 * v1[both] + w2 * v2[both]
        out.loc[only1, col] = v1[only1]
        out.loc[only2, col] = v2[only2]
    for col in extra_cols:
        out[col] = df2[col].reindex(all_dates)
    return out.reset_index()


def live_nowcast(meteo_csv=DEFAULT_METEO_CSV, meteo_csv2=DEFAULT_METEO_CSV2,
                 enso_csv=DEFAULT_ENSO_CSV):
    if not HAS_PANDAS:
        print("  [!] Modul pandas tidak tersedia — nowcast dilewati.")
        return None
    df = load_interpolated_meteo(meteo_csv, meteo_csv2)
    if df is None:
        print("  [!] Tidak ada file meteorologi ditemukan — nowcast dilewati.")
        return None

    _p1_ok = find_data_file(meteo_csv)  is not None
    _p2_ok = find_data_file(meteo_csv2) is not None
    _interp_mode = ("IDW 2 stasiun" if (_p1_ok and _p2_ok)
                    else ("stasiun P1 saja" if _p1_ok else "stasiun P2 saja"))

    df = df.sort_values("time").reset_index(drop=True)
    df["wb"]      = (df["precipitation_sum (mm)"]
                     - df["et0_fao_evapotranspiration (mm)"])
    df["rh_mean"] = ((df["relative_humidity_2m_max (%)"]
                      + df["relative_humidity_2m_min (%)"]) / 2)
    win = 30
    df["rain_30d"] = df["precipitation_sum (mm)"].rolling(win, min_periods=15).sum()
    df["wb_30d"]   = df["wb"].rolling(win, min_periods=15).sum()
    df["sm_30d"]   = (df["soil_moisture_0_to_7cm_mean (m³/m³)"]
                      .rolling(win, min_periods=15).mean())
    df["rh_30d"]   = df["rh_mean"].rolling(win, min_periods=15).mean()
    df = df.dropna(subset=["rain_30d","wb_30d","sm_30d","rh_30d"]).reset_index(drop=True)

    tail  = df.tail(400).reset_index(drop=True)
    X     = tail[["rain_30d","wb_30d","sm_30d","rh_30d"]].values
    Xz    = (X - np.array(HMM_T_mu)) / np.array(HMM_T_sd)
    probs = hmm_causal_filter(Xz)
    last_probs = probs[-1]
    last_date  = tail["time"].iloc[-1].date()

    y = tail["wb_30d"].values[-730:] if len(tail) > 730 else tail["wb_30d"].values
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
    }

    epath = find_data_file(enso_csv)
    if epath is not None:
        edf  = pd.read_csv(epath)
        base = datetime(1978, 1, 1, 12, 0, 0)
        edf["date"]  = edf["time"].apply(
            lambda d: base + timedelta(days=float(d)))
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
        out["enso_latest_value"] = float(
            edf.sort_values("date")["enso"].iloc[-1])
        out["enso_latest_date"]  = (
            edf.sort_values("date")["date"].iloc[-1].date())
    return out


# ══════════════════════════════════════════════════════════════════════
# 8. FUNGSI TAMPILAN — DITAMBAH BLOK ASTRO (baru di EV02)
# ══════════════════════════════════════════════════════════════════════

def _meteo_mangsa_block(no: int, indent: int = 6) -> None:
    if no not in METEO_MANGSA:
        return
    (hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad) = METEO_MANGSA[no]
    tx_m = (tx + tn) / 2
    pad  = " " * indent
    wb_str = (f"{wb:+.2f} mm/hari ({'defisit' if wb < 0 else 'surplus'})")
    print(f"{pad}Curah hujan : {hj:>4} mm/musim · {hj_d:.1f} mm/hari"
          f" · {hhr} hari hujan")
    print(f"{pad}Suhu udara  : maks {tx:.1f}°C · min {tn:.1f}°C"
          f" · rata-rata {tx_m:.1f}°C")
    print(f"{pad}Kelembaban  : RH {rh:.1f}% · SM {sm:.3f} m³/m³"
          f" · ET₀ {et0:.2f} mm/hari")
    print(f"{pad}Neraca air  : {wb_str}")
    print(f"{pad}Radiasi/Angin: {rad:.1f} MJ/m² · Angin maks {angin:.1f} km/j")


def _meteo_musim_block(musim: str, indent: int = 4) -> None:
    if musim not in METEO_MUSIM:
        return
    (dur, hj, hj_d, et0, wb, sm, rh, tx, tn, angin, rad) = METEO_MUSIM[musim]
    pad = " " * indent
    wb_str = f"{wb:+.2f} mm/hari ({'defisit' if wb < 0 else 'surplus'})"
    print(f"{pad}Curah hujan : {hj:>5} mm/musim  ·  {hj_d:.1f} mm/hari"
          f"  ·  ET₀ {et0:.2f} mm/hari")
    print(f"{pad}Neraca air  : {wb_str}"
          f"  ·  SM {sm:.3f} m³/m³")
    print(f"{pad}Suhu udara  : maks {tx:.1f}°C · min {tn:.1f}°C"
          f"  ·  RH {rh:.1f}%")
    print(f"{pad}Rad./Angin  : {rad:.1f} MJ/m²"
          f"  ·  Angin maks {angin:.1f} km/j"
          f"  ·  Durasi {dur} hari")


def print_astro_calib_table() -> None:
    """Cetak tabel kalibrasi astronomis lengkap (baru di EV02)."""
    print()
    print(box_top())
    print(box_row("KALIBRASI ASTRONOMIS — EV02"))
    print(box_row("JRC_Ephemeris · VSOP87D · IERS 2010 · ΔT HMNAO"))
    print(box_row("Lokasi: −7.5220°LS, 112.5661°BT, 28 m  ·  Rata-rata 2020–2029"))
    print(box_mid())
    print(box_row("Peristiwa             Tgl rata   dopy  σ  Δ vs trad  Mangsa"))
    print(box_bot())
    print()

    rows = [
        ("solstis_juni",       "Solstis Juni",            "1 (Kasa)"),
        ("solstis_des",        "Solstis Desember",         "7 (Kapitu)"),
        ("equinox_maret",      "Ekuinoks Maret",           "9 (Kasanga)†"),
        ("equinox_sept",       "Ekuinoks September",       "4 (Kapat)†"),
        ("zenith_I_okt",       "Zenith Matahari I",        "5 (Kalima)"),
        ("zenith_II_mar",      "Zenith Matahari II",       "9 (Kasanga)"),
        ("orion_helrise",      "Orion Heliacal Rise",      "1 (Kasa)"),
        ("orion_evening_rise", "Orion Acronychal Rise",    "6 (Kanem)"),
        ("orion_evening_culm", "Orion Kulminasi Senja",    "9 (Kasanga)"),
        ("orion_midnight_culm","Orion Kulminasi Tngah Mlm","6 (Kanem)"),
        ("orion_acron_set",    "Orion Acronychal Set",     "12 (Sada)"),
    ]

    for key, label, mangsa in rows:
        ev = ASTRO_CALIB.get(key)
        if not ev:
            continue
        MONTHS_ID = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",
                     7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}
        tgl = f"{ev['mean_day']:02d} {MONTHS_ID.get(ev['mean_month'],'---')}"
        dopy = ev["mean_dopy"]
        std  = ev["std_dopy"]
        delta = ev["delta"]
        row = (f"  {label:<26} {tgl:>7}  {dopy:>7.1f}  {std:.2f}  "
               f"{delta:>+6.1f}  {mangsa}")
        print(row[:W])

    print()
    print("  † = Ekuinoks jatuh di dalam mangsa tsb, namun BUKAN jangkar/penanda")
    print("      awal mangsa dalam tradisi Pranata Mangsa. Dicantumkan sebagai")
    print("      titik referensi astronomis saja.")
    print()
    print(thin_hbar(2))
    print("  Catatan penting per peristiwa:")
    print()
    for key, label, _ in rows:
        ev = ASTRO_CALIB.get(key)
        if not ev or "catatan" not in ev:
            continue
        wprint(label[:20], ev["catatan"], lw=22, indent=2)
        print()


def print_calendar(cal: List[Dict], judul: str, show_meteo: bool = True,
                   show_astro: bool = True) -> None:
    print()
    print(box_top())
    print(box_row(judul))
    print(box_row("ERA5/Land-IFS HRES · −7.522°LS 112.566°BT · 28 m  [IDW 2 stasiun]"))
    if show_meteo:
        print(box_row("Klimatologi: Normal Iklim R30 (1996–2025)"))
    if show_astro:
        print(box_row("Astro: VSOP87D+IERS2010 · JRC_Ephemeris · 2020–2029"))
    print(box_bot())

    for musim in MUSIM_ORDER:
        ms   = CALIB_SCENARIOS[DEFAULT_SCENARIO]["musim_start"]
        ms_n = {"Katiga": ms["Labuh"], "Labuh": ms["Rendheng"],
                "Rendheng": ms["Mareng"], "Mareng": 365 + ms["Katiga"]}
        dopy_s = ms[musim];  dopy_e = ms_n[musim] - 1
        sec_header(
            f"MUSIM {musim}",
            MUSIM_DESKRIPSI[musim],
            dopy_range=f"{dopy_s}–{dopy_e}",
        )
        if show_meteo:
            _meteo_musim_block(musim, indent=2)
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
                _meteo_mangsa_block(m["no"], indent=7)
            ciri_text = m["ciri"]
            label = "Ciri       "
            pre   = "       " + label + ": "
            sub   = " " * len(pre)
            print(textwrap.fill(ciri_text, width=W,
                                initial_indent=pre,
                                subsequent_indent=sub))
            print()

    print()


def print_mangsa_today(tanggal: date, scenario_key: str = DEFAULT_SCENARIO) -> None:
    pyear, dopy = get_pranatamangsa_year_and_dopy(tanggal)
    scn_label   = CALIB_SCENARIOS[scenario_key]["label"]

    print()
    print(box_top())
    print(box_row(f"MANGSA UNTUK TANGGAL: {fmt(tanggal)}"))
    print(box_row(f"Tahun-Pranata: {pyear}/{pyear+1}  ·  Hari ke-{dopy+1}"
                  f" (dopy={dopy})"))
    print(box_mid())

    trad = get_mangsa_by_date(tanggal, "tradisional")
    if trad:
        print(box_row(""))
        print(box_row("[ TRADISIONAL — Reformasi Paku Buwana VII, 1855 ]"))
        print(box_row(
            f"  Mangsa ke-{trad['no']}: {trad['nama'].upper()}"
            f"  ·  Musim {trad['musim']}"
        ))
        print(box_row(
            f"  Periode: {fmt(trad['mulai'])} — {fmt(trad['akhir'])}"
            f"  ({trad['durasi']} hari)"
        ))
        ciri_lines = textwrap.wrap(trad["ciri"], width=W - 6)
        for ln in ciri_lines:
            print(box_row(f"  Ciri: {ln}" if ln == ciri_lines[0] else f"        {ln}"))

    print(box_mid())
    kal = get_mangsa_by_date(tanggal, "terkalibrasi", scenario_key)
    if kal:
        print(box_row(""))
        print(box_row(f"[ TERKALIBRASI — {scn_label} ]"))
        print(box_row(
            f"  Mangsa ke-{kal['no']}: {kal['nama'].upper()}"
            f"  ·  Musim {kal['musim']}"
        ))
        print(box_row(
            f"  Periode: {fmt(kal['mulai'])} — {fmt(kal['akhir'])}"
            f"  ({kal['durasi']} hari)"
        ))
        if trad and kal["no"] != trad["no"]:
            print(box_row(
                f"  >> BERBEDA dari tradisional "
                f"(tradisional: mangsa {trad['no']} {trad['nama']})"
            ))
        elif trad:
            sel = (kal["mulai"] - trad["mulai"]).days
            sgn = "lebih awal" if sel < 0 else "lebih lambat"
            print(box_row(
                f"  Awal mangsa ini bergeser {sel:+d} hari "
                f"({abs(sel)} hari {sgn}) vs. tradisional"
            ))
        print(box_mid())
        print(box_row(""))
        print(box_row("  Klimatologi periode ini (Normal Iklim R30, 1996–2025):"))
        if kal["no"] in METEO_MANGSA:
            (hj, hj_d, hhr, et0, wb, sm, rh, tx, tn, angin, rad) = METEO_MANGSA[kal["no"]]
            wb_str = f"{'defisit' if wb < 0 else 'surplus'}"
            print(box_row(
                f"  Curah hujan : {hj} mm/musim · {hj_d:.1f} mm/hari"
                f" · {hhr} hari hujan"))
            print(box_row(
                f"  Suhu udara  : maks {tx:.1f}°C · min {tn:.1f}°C"
                f" · rata {(tx+tn)/2:.1f}°C"))
            print(box_row(
                f"  Kelembaban  : RH {rh:.1f}% · SM {sm:.3f} m³/m³"
                f" · ET₀ {et0:.2f} mm/hari"))
            print(box_row(
                f"  Neraca air  : P−ET₀ {wb:+.2f} mm/hari ({wb_str})"
                f" · Rad {rad:.1f} MJ/m²"))

        # ── Blok Astro (baru di EV02) ─────────────────────────────────
        print(box_mid())
        print(box_row(""))
        print(box_row("  Penanda Astronomis (VSOP87D, rata-rata 2020–2029):"))
        ASTRO_MANGSA = {
            1:  [("orion_helrise",      "Weluku/Orion Heliacal Rise")],
            4:  [("equinox_sept",       "Ekuinoks September (λ☉=180°)†")],
            5:  [("zenith_I_okt",       "Zenith Matahari I (δ☉=−7.52°)")],
            6:  [("orion_evening_rise", "Weluku/Orion Acronychal Rise"),
                 ("orion_midnight_culm","Weluku/Orion Kulminasi Tngah Mlm")],
            7:  [("solstis_des",        "Solstis Desember (λ☉=270°)")],
            9:  [("zenith_II_mar",      "Zenith Matahari II (δ☉=−7.52°)"),
                 ("orion_evening_culm", "Weluku/Orion Kulminasi Senja"),
                 ("equinox_maret",      "Ekuinoks Maret (λ☉=0°)†")],
            12: [("orion_acron_set",    "Weluku/Orion Acronychal Set")],
        }
        events = ASTRO_MANGSA.get(kal["no"], [])
        if not events:
            print(box_row("  (tidak ada penanda astronomis khusus untuk mangsa ini)"))
        for ev_key, ev_label in events:
            ev = ASTRO_CALIB.get(ev_key, {})
            if ev:
                MONTHS_ID = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",
                             7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}
                tgl_str = f"{ev['mean_day']:02d} {MONTHS_ID.get(ev['mean_month'],'---')}"
                delta_s = astro_delta_str(ev_key)
                print(box_row(f"  {ev_label}"))
                print(box_row(f"    → Tgl rata-rata: {tgl_str}  |  {delta_s}"))

    print(box_bot())
    print()


def print_perbandingan(pyear: int) -> None:
    trad_cal = build_calendar_tradisional_pyear(pyear)
    scn_keys = list(CALIB_SCENARIOS.keys())

    print()
    print(box_top())
    print(box_row(
        f"PERBANDINGAN SKENARIO — Tahun-Pranata {pyear}/{pyear+1}"))
    print(box_row(
        "Angka = selisih hari awal mangsa vs. Tradisional (– lebih awal)"))
    print(box_bot())
    print()

    hdr = f"  {'No':>2}  {'Nama':<10} {'Tradisional':>12}"
    for k in scn_keys:
        hdr += f"  {k:>6}"
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

    musims  = MUSIM_ORDER
    col_w   = 11

    hdr  = f"  {'Skenario':<13}"
    hdr += "".join(f"{mu:>{col_w}}" for mu in musims)
    hdr += f"  {'Total':>6}"
    print(hdr[:W])
    print(thin_hbar(2))

    o    = ORIG_MUSIM_START
    on   = ORIG_MUSIM_START_NEXT
    durs = [on[mu] - o[mu] for mu in musims]
    row  = f"  {'Tradisional':<13}"
    row += "".join(f"{d:>{col_w}}" for d in durs)
    row += f"  {sum(durs):>6}"
    print(row[:W])

    for key, v in CALIB_SCENARIOS.items():
        s  = v["musim_start"]
        sn = {"Katiga": s["Labuh"], "Labuh": s["Rendheng"],
              "Rendheng": s["Mareng"], "Mareng": 365 + s["Katiga"]}
        durs = [sn[mu] - s[mu] for mu in musims]
        row  = f"  {key:<13}"
        row += "".join(f"{d:>{col_w}}" for d in durs)
        row += f"  {sum(durs):>6}"
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
    print(box_row("Satuan: mm/bln = milimeter per bulan  mm/hr = mm/hari"))
    print(box_row("        MJ/m² = megajoule per meter²  km/j = kilometer per jam"))
    print(box_bot())
    print()

    params = [
        ("Hujan (mm/bln)",   0, "{:>6.0f}"),
        ("Hujan (mm/hari)",  1, "{:>6.1f}"),
        ("ET₀  (mm/hari)",   2, "{:>6.2f}"),
        ("P−ET₀ (mm/hr)",    3, "{:>+6.1f}"),
        ("SM   (m³/m³)",     4, "{:>6.3f}"),
        ("RH   (%)",         5, "{:>6.1f}"),
        ("T maks (°C)",      6, "{:>6.1f}"),
        ("T min  (°C)",      7, "{:>6.1f}"),
        ("Angin (km/j)",     8, "{:>6.1f}"),
        ("Radiasi (MJ/m²)",  9, "{:>6.1f}"),
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

    print(thin_hbar(0))
    print()
    print(f"  {'RINGKASAN PER MUSIM':^{W-2}}")
    print(f"  {'(Normal Iklim R30, skenario terkalibrasi)':^{W-2}}")
    print()

    mus_params = [
        ("Hujan total (mm)",  1, "{:>10.0f}"),
        ("Hujan  (mm/hari)",  2, "{:>10.1f}"),
        ("ET₀    (mm/hari)",  3, "{:>10.2f}"),
        ("P−ET₀  (mm/hari)", 4, "{:>+10.2f}"),
        ("SM     (m³/m³)",   5, "{:>10.3f}"),
        ("RH     (%)",       6, "{:>10.1f}"),
        ("T maks (°C)",      7, "{:>10.1f}"),
        ("T min  (°C)",      8, "{:>10.1f}"),
        ("Angin  (km/j)",    9, "{:>10.1f}"),
        ("Radiasi(MJ/m²)",  10, "{:>10.1f}"),
        ("Durasi (hari)",    0, "{:>10.0f}"),
    ]

    col_w   = 10
    hdr     = f"  {'Parameter':<18}"
    hdr    += "".join(f"{mu:>{col_w}}" for mu in MUSIM_ORDER)
    print(hdr[:W])
    print(thin_hbar(2))
    for label, idx, fmt_str in mus_params:
        row = f"  {label:<18}"
        for mu in MUSIM_ORDER:
            row += fmt_str.format(METEO_MUSIM[mu][idx])
        print(row[:W])
    print()
    print(thin_hbar(0))
    print()


def print_live_nowcast() -> None:
    print()
    print(box_top())
    print(box_row("NOWCAST LANGSUNG — Analisis Iklim Real-Time"))
    print(box_row("HMM Causal Filter + SR-EKF Level/Tren (ARCH(1))"))
    print(box_bot())

    res = live_nowcast()
    if res is None:
        return

    print()
    lat_s = f"{abs(res.get('lat_target', LAT_TARGET)):.4f}°LS"
    lon_s = f"{res.get('lon_target', LON_TARGET):.4f}°BT"
    print(f"  Titik target               : {lat_s}, {lon_s}")
    print(f"  Mode data                  : {res.get('interp_mode', '-')}")
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
        print(f"  State {k}  {p*100:5.1f}%  {bar:<32}"
              f"  {HMM_T_STATE[k][:28]}")

    dom = res["dominant_state"]
    print()
    print(f"  >> Rejim dominan saat ini: State {dom} — {HMM_T_STATE[dom]}")

    print()
    print(thin_hbar(2))
    print("  SR-EKF — Neraca air P−ET₀ 30-hari (level & tren ter-filter):")
    print(thin_hbar(2))
    wb   = res["level_wb30"]
    trnd = res["trend_wb30_per_day"]
    arah = "→ menuju lebih basah" if trnd > 0 else "→ menuju lebih kering"
    print(f"  Level saat ini  : {wb:+.1f} mm / 30 hari")
    print(f"  Tren harian     : {trnd:+.3f} mm/hari  {arah}")

    if "enso_phase_sofar" in res:
        print()
        print(thin_hbar(2))
        print(f"  Status ENSO ({res['enso_year']} — rata-rata ASO Niño3.4"
              f", data s.d. {fmt(res['enso_latest_date'])}):")
        print(thin_hbar(2))
        print(f"  Indeks Niño3.4 ASO : {res['enso_aso_mean_sofar']:+.2f}"
              f"  →  Fase: {res['enso_phase_sofar']}")
        print(f"  Nilai mingguan terakhir: {res['enso_latest_value']:+.2f}")
        scn = SCENARIO_FOR_PHASE.get(res["enso_phase_sofar"])
        if scn:
            print()
            print(f"  >> Rekomendasi skenario: '{scn}'")
            wprint("Catatan", CALIB_SCENARIOS[scn]["catatan"], lw=7, indent=5)
    print()


# ══════════════════════════════════════════════════════════════════════
# 9. MENU INTERAKTIF (ditambah opsi 8: Kalibrasi Astronomis)
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
    print(box_top("PRANATA MANGSA — EV02 METEO+ASTRO"))
    print(box_row("−7.52S112.56E28m · ERA5/Land IFS HRES 1940–2026 · ENSO 1993–2026"))
    print(box_row("Kalibrasi Astro: VSOP87D + IERS2010 · JRC_Ephemeris · 2020–2029"))
    print(box_mid())
    for item in [
        "  1 › Kalender Tradisional (Paku Buwana VII, 1855)",
        "  2 › Kalender Terkalibrasi (meteorologi + astro)",
        "  3 › Cek Mangsa Hari Ini / Tanggal Tertentu",
        "  4 › Tabel Perbandingan Skenario (selisih hari)",
        "  5 › Durasi Tiap Musim per Skenario",
        "  6 › Klimatologi Bulanan & Ringkasan Per-Musim",
        "  7 › Nowcast Langsung (real-time dari data terbaru)",
        "  8 › Tabel Kalibrasi Astronomis",
        "  0 › Keluar",
    ]:
        print(box_row(item))
    print(box_bot())


def laporan_singkat() -> None:
    today = date.today()
    print_mangsa_today(today, DEFAULT_SCENARIO)
    if find_data_file(DEFAULT_METEO_CSV) or find_data_file(DEFAULT_METEO_CSV2):
        print_live_nowcast()


def main_loop() -> None:
    while True:
        show_menu()
        pilihan = input("  Pilih menu (0–8): ").strip()

        if pilihan == "0":
            print()
            print(box_top())
            print(box_row("Terima kasih. Sampai jumpa!  — Pranata Mangsa EV02-METEO+ASTRO"))
            print(box_bot())
            print()
            break

        elif pilihan == "1":
            tahun = input_int(
                "  Tahun Gregorian (YYYY) untuk kalender tradisional: ",
                date.today().year,
            )
            if tahun is not None:
                print_calendar(
                    build_calendar_tradisional(tahun),
                    f"KALENDER TRADISIONAL — TAHUN {tahun}",
                    show_meteo=False, show_astro=False,
                )

        elif pilihan == "2":
            default_py = get_pranatamangsa_year_and_dopy(date.today())[0]
            tahun = input_int(
                f"  Tahun-pranata mulai (YYYY) [{default_py}]: ",
                default_py,
            )
            scn = choose_scenario()
            if tahun is not None:
                print_calendar(
                    build_calendar_terkalibrasi(tahun, scn),
                    (f"KALENDER TERKALIBRASI [{CALIB_SCENARIOS[scn]['label']}]"
                     f" — {tahun}/{tahun+1}"),
                    show_meteo=True, show_astro=True,
                )

        elif pilihan == "3":
            s = input(
                "  Tanggal (YYYY-MM-DD) [kosong = hari ini]: "
            ).strip()
            tgl = date.today() if not s else date(*map(int, s.split("-")))
            scn = choose_scenario()
            print_mangsa_today(tgl, scn)

        elif pilihan == "4":
            default_py = get_pranatamangsa_year_and_dopy(date.today())[0]
            tahun = input_int(
                f"  Tahun-pranata mulai (YYYY) [{default_py}]: ",
                default_py,
            )
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
