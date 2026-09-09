# pranatamangsa_interaktif.py
# Kalender Pranata Mangsa Konvensional (Statis)
# Berdasarkan reformasi Paku Buwana VII (1855)
# Data diambil dari: Ammarell, van den Bosch, & Sumani
# Versi Interaktif - 2025

from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
import sys

# ------------------------------------------------------------
# 1. DATA DASAR PRANATA MANGSA
# ------------------------------------------------------------

MANGSAS = [
    {"no": 1, "nama": "Kasa",      "lain": "Kasa",        "bulan": 6,  "tgl": 22, "durasi": 41},
    {"no": 2, "nama": "Karo",      "lain": "Kalih",       "bulan": 8,  "tgl": 2,  "durasi": 23},
    {"no": 3, "nama": "Katiga",    "lain": "Katelu",      "bulan": 8,  "tgl": 25, "durasi": 24},
    {"no": 4, "nama": "Kapat",     "lain": "Kasakawan",   "bulan": 9,  "tgl": 18, "durasi": 25},
    {"no": 5, "nama": "Kalima",    "lain": "Gangsal",     "bulan": 10, "tgl": 13, "durasi": 27},
    {"no": 6, "nama": "Kanem",     "lain": "Kanem",       "bulan": 11, "tgl": 9,  "durasi": 43},
    {"no": 7, "nama": "Kapitu",    "lain": "Kapitu",      "bulan": 12, "tgl": 22, "durasi": 43},
    {"no": 8, "nama": "Kawolu",    "lain": "Kawolu",      "bulan": 2,  "tgl": 3,  "durasi": 26},  # 27 di tahun kabisat
    {"no": 9, "nama": "Kasanga",   "lain": "Kasanga",     "bulan": 3,  "tgl": 1,  "durasi": 25},
    {"no": 10, "nama": "Kasadasa","lain": "Kasepuluh",    "bulan": 3,  "tgl": 26, "durasi": 24},
    {"no": 11, "nama": "Desta",    "lain": "Desta",       "bulan": 4,  "tgl": 19, "durasi": 23},
    {"no": 12, "nama": "Sada",     "lain": "Sada",        "bulan": 5,  "tgl": 12, "durasi": 41},
]

MUSIM = [
    ("Katiga",     "Kemarau",                 [1, 2, 3]),
    ("Labuh",      "Peralihan ke Hujan",      [4, 5, 6]),
    ("Rendheng",   "Musim Hujan",             [7, 8, 9]),
    ("Mareng",      "Peralihan ke Kemarau",    [10, 11, 12])
]

CIRI = {
    1: "Orion (Weluku) terbit tegak di timur saat fajar. Awal tahun pertanian, membersihkan lahan.",
    2: "Pohon randu/kapuk mulai berdaun. Tanah retak. Pengolahan lahan kering.",
    3: "Puncak kemarau, sumur mengering. Panen palawija (jagung, kacang).",
    4: "Burung gelatik di sawah, manyar membuat sarang. Angin mulai berubah ke barat.",
    5: "Zenith sun I (13 Okt). Awal hujan. Pleiades terlihat di senja. Embun beracun.",
    6: "Hujan lebat. Orion terbit tegak di senja (6 Des). Menabur benih padi.",
    7: "Solstis Des. Pleiades setinggi pecat sawad (50°). Memindah bibit padi ke sawah.",
    8: "Transplantasi selesai. Pleiades kulminasi di senja. Padi tumbuh.",
    9: "Zenith sun II (1 Mar). Orion kulminasi. Jangkrik berbunyi. Padi berbulir.",
    10: "Hujan reda, angin timur. Panen raya mulai.",
    11: "Puncak panen. Orion terbalik di barat. Kapuk mekar. Hutang dilunasi.",
    12: "Panen selesai. Orion menghilang (4 Jun). Masa bera (Apit Lemah).",
}

NAMA_INDONESIA_BULAN = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
    7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"
}


# ------------------------------------------------------------
# 2. FUNGSI BANTU
# ------------------------------------------------------------

def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def get_start_date(year: int, bulan: int, tgl: int) -> date:
    return date(year, bulan, tgl)

def get_mangsa_by_date(tanggal: date) -> Optional[Tuple[int, str, date, date]]:
    """
    Mencari mangsa yang sedang berlangsung pada tanggal tertentu.
    Return: (no_mangsa, nama_mangsa, tanggal_mulai, tanggal_akhir)
    """
    year = tanggal.year
    
    # Coba di tahun yang sama dan tahun sebelumnya (untuk mangsa yang melintasi tahun)
    for tahun_cek in (year, year - 1):
        for m in MANGSAS:
            start = get_start_date(tahun_cek, m["bulan"], m["tgl"])
            durasi = m["durasi"]
            if m["no"] == 8 and is_leap_year(tahun_cek):
                durasi = 27
            end = start + timedelta(days=durasi - 1)
            if start <= tanggal <= end:
                return (m["no"], m["nama"], start, end)
    
    return None


def build_calendar(year: int) -> List[Dict]:
    calendar = []
    for m in MANGSAS:
        start = get_start_date(year, m["bulan"], m["tgl"])
        durasi = m["durasi"]
        if m["no"] == 8 and is_leap_year(year):
            durasi = 27
        end = start + timedelta(days=durasi - 1)
        
        musim = ""
        for nama_musim, _, daftar_no in MUSIM:
            if m["no"] in daftar_no:
                musim = nama_musim
                break
        
        calendar.append({
            "no": m["no"],
            "nama": m["nama"],
            "lain": m["lain"],
            "mulai": start,
            "akhir": end,
            "durasi": durasi,
            "musim": musim,
            "ciri": CIRI.get(m["no"], ""),
        })
    return calendar


# ------------------------------------------------------------
# 3. FUNGSI TAMPILAN
# ------------------------------------------------------------

def print_header(year: int):
    print(f"\n{'='*100}")
    print(f"  KALENDER PRANATA MANGSA KONVENSIONAL - TAHUN {year}")
    print(f"  (Berdasarkan reformasi Paku Buwana VII, 1855)")
    print(f"{'='*100}\n")

def print_calendar(year: int):
    cal = build_calendar(year)
    print_header(year)
    
    for musim, deskripsi, daftar_no in MUSIM:
        print(f"\n  ██ MUSIM {musim.upper()} ({deskripsi})")
        print(f"  {'-'*95}")
        print(f"  {'No':<4} {'Nama':<12} {'Mulai':<14} {'Selesai':<14} {'Durasi':<8} {'Ciri-ciri'}")
        print(f"  {'-'*95}")
        
        for m in cal:
            if m["no"] in daftar_no:
                start_str = m["mulai"].strftime("%d %b %Y")
                end_str   = m["akhir"].strftime("%d %b %Y")
                durasi_str = f"{m['durasi']} hari"
                ciri_short = m["ciri"][:55] + "..." if len(m["ciri"]) > 55 else m["ciri"]
                print(f"  {m['no']:<4} {m['nama']:<12} {start_str:<14} {end_str:<14} {durasi_str:<8} {ciri_short}")
        
        print(f"  {'-'*95}")
    
    print("\n")

def print_mangsa_info(tanggal: date):
    result = get_mangsa_by_date(tanggal)
    if result:
        no, nama, start, end = result
        print(f"\n📅 Tanggal: {tanggal.strftime('%d %b %Y')}")
        print(f"   Mangsa ke-{no}: {nama.upper()}")
        print(f"   Periode: {start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')}")
        ciri = CIRI.get(no, "")
        if ciri:
            print(f"   Ciri: {ciri}")
    else:
        print(f"\n❌ Tidak ditemukan mangsa untuk tanggal {tanggal.strftime('%d %b %Y')}.")


# ------------------------------------------------------------
# 4. FUNGSI INPUT
# ------------------------------------------------------------

def input_tanggal(prompt: str = "Masukkan tanggal (YYYY-MM-DD): ") -> Optional[date]:
    while True:
        try:
            input_str = input(prompt).strip()
            if not input_str:
                return None
            tahun, bulan, tgl = map(int, input_str.split('-'))
            return date(tahun, bulan, tgl)
        except ValueError:
            print("  ❌ Format salah. Gunakan YYYY-MM-DD (contoh: 2025-06-22).")
        except KeyboardInterrupt:
            print("\n  Dibatalakan.")
            return None

def input_tahun(prompt: str = "Masukkan tahun (YYYY): ") -> Optional[int]:
    while True:
        try:
            input_str = input(prompt).strip()
            if not input_str:
                return None
            tahun = int(input_str)
            if tahun < 1 or tahun > 9999:
                print("  ❌ Tahun harus antara 1 - 9999.")
                continue
            return tahun
        except ValueError:
            print("  ❌ Format salah. Masukkan angka tahun (contoh: 2025).")
        except KeyboardInterrupt:
            print("\n  Dibatalakan.")
            return None


# ------------------------------------------------------------
# 5. MENU INTERAKTIF
# ------------------------------------------------------------

def clear_screen():
    print("\n" * 2)

def show_menu():
    print("\n" + "="*60)
    print("  🌾 PRANATA MANGSA - KALENDER PERTANIAN JAWA")
    print("="*60)
    print("  1. Tampilkan Kalender untuk Tahun Tertentu")
    print("  2. Cek Mangsa Hari Ini")
    print("  3. Cek Mangsa untuk Tanggal Tertentu")
    print("  4. Cek Mangsa untuk Tanggal Sekarang + Info Lengkap")
    print("  0. Keluar")
    print("-"*60)

def main_loop():
    while True:
        show_menu()
        pilihan = input("  Pilih menu (0-4): ").strip()
        
        if pilihan == "0":
            print("\n  Terima kasih telah menggunakan Kalender Pranata Mangsa. Sampai jumpa! 🌾")
            break
        
        elif pilihan == "1":
            print("\n  📅 Tampilkan Kalender")
            tahun = input_tahun("  Masukkan tahun (YYYY): ")
            if tahun is not None:
                print_calendar(tahun)
            else:
                print("  ⏹️  Dibatalkan.")
            input("\n  Tekan Enter untuk kembali ke menu...")
        
        elif pilihan == "2":
            print("\n  🌤️ Cek Mangsa Hari Ini")
            today = date.today()
            print_mangsa_info(today)
            input("\n  Tekan Enter untuk kembali ke menu...")
        
        elif pilihan == "3":
            print("\n  🔍 Cek Mangsa untuk Tanggal Tertentu")
            tgl = input_tanggal("  Masukkan tanggal (YYYY-MM-DD): ")
            if tgl is not None:
                print_mangsa_info(tgl)
            else:
                print("  ⏹️  Dibatalkan.")
            input("\n  Tekan Enter untuk kembali ke menu...")
        
        elif pilihan == "4":
            print("\n  📌 Cek Mangsa Hari Ini + Info Lengkap")
            today = date.today()
            print_mangsa_info(today)
            
            # Tampilkan informasi tambahan
            result = get_mangsa_by_date(today)
            if result:
                no, nama, start, end = result
                cal = build_calendar(today.year)
                for m in cal:
                    if m["no"] == no:
                        print(f"\n  📋 Rincian Mangsa {nama.upper()}:")
                        print(f"     Nama lain  : {m['lain']}")
                        print(f"     Musim      : {m['musim']}")
                        print(f"     Durasi     : {m['durasi']} hari")
                        print(f"     Mulai      : {m['mulai'].strftime('%d %b %Y')}")
                        print(f"     Selesai    : {m['akhir'].strftime('%d %b %Y')}")
                        print(f"     Ciri-ciri  : {m['ciri']}")
                        break
            input("\n  Tekan Enter untuk kembali ke menu...")
        
        else:
            print("  ❌ Pilihan tidak valid. Silakan pilih 0-4.")
            input("\n  Tekan Enter untuk melanjutkan...")
        
        clear_screen()


# ------------------------------------------------------------
# 6. MAIN
# ------------------------------------------------------------

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n\n  Program dihentikan oleh pengguna. Sampai jumpa! 🌾")
        sys.exit(0)