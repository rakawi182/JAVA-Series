import textwrap

# ============================================================
# DICTIONARY
# ============================================================

hari = {
    "Minggu": 5,
    "Senin": 4,
    "Selasa": 3,
    "Rabu": 7,
    "Kamis": 8,
    "Jum'at": 6,
    "Sabtu": 9
}

pasaran = {
    "Kliwon": 8,
    "Legi": 5,
    "Pahing": 9,
    "Pon": 7,
    "Wage": 4
}

data_kelompok = {
    0: [
        ("Minggu", "Pon", 12),
        ("Minggu", "Wage", 9),
        ("Senin", "Kliwon", 12),
        ("Senin", "Legi", 9),
        ("Selasa", "Pahing", 12),
        ("Rabu", "Kliwon", 15),
        ("Rabu", "Legi", 12),
        ("Kamis", "Pon", 15),
        ("Kamis", "Wage", 12),
        ("Jum'at", "Pahing", 15),
        ("Sabtu", "Pahing", 18),
    ],
    1: [
        ("Minggu", "Kliwon", 13),
        ("Minggu", "Legi", 10),
        ("Senin", "Pahing", 13),
        ("Selasa", "Pon", 10),
        ("Selasa", "Wage", 7),
        ("Rabu", "Pahing", 16),
        ("Kamis", "Kliwon", 16),
        ("Kamis", "Legi", 13),
        ("Jum'at", "Pon", 13),
        ("Jum'at", "Wage", 10),
        ("Sabtu", "Pon", 16),
        ("Sabtu", "Wage", 13),
    ],
    2: [
        ("Minggu", "Pahing", 14),
        ("Senin", "Pon", 11),
        ("Senin", "Wage", 8),
        ("Selasa", "Kliwon", 11),
        ("Selasa", "Legi", 8),
        ("Rabu", "Pon", 14),
        ("Rabu", "Wage", 11),
        ("Kamis", "Pahing", 17),
        ("Jum'at", "Kliwon", 14),
        ("Jum'at", "Legi", 11),
        ("Sabtu", "Kliwon", 17),
        ("Sabtu", "Legi", 14),
    ]
}

hari_pandawa = {
    "Aboge": [
        ("Selasa", "Wage"),
        ("Rabu", "Legi"),
        ("Kamis", "Pon"),
        ("Sabtu", "Kliwon"),
        ("Minggu", "Pahing")
    ],
    "Asapon": [
        ("Senin", "Pon"),
        ("Selasa", "Kliwon"),
        ("Rabu", "Pahing"),
        ("Jum'at", "Wage"),
        ("Sabtu", "Legi")
    ]
}

taliwangke = {
    "Sela": "Senin Kliwon",
    "Jumadilawal": "Senin Kliwon",
    "Besar": "Selasa Legi",
    "Jumadilakir": "Selasa Legi",
    "Sura": "Rabu Pahing",
    "Rejeb": "Rabu Pahing",
    "Sapar": "Kamis Pon",
    "Ruwah": "Kamis Pon",
    "Mulud": "Jum'at Wage",
    "Pasa": "Jum'at Wage",
    "Ba'da Mulud": "Sabtu Kliwon",
    "Sawal": "Sabtu Kliwon"
}

aturan_bulan = {
    "Sura": "larangan",
    "Sapar": "boleh",
    "Mulud": "larangan",
    "Ba'da Mulud": "boleh",
    "Jumadilawal": "boleh",
    "Jumadilakir": "baik",
    "Rejeb": "baik",
    "Ruwah": "baik",
    "Pasa": "larangan",
    "Sawal": "boleh",
    "Sela": "larangan",
    "Besar": "baik"
}

# ============================================================
# FUNGSI
# ============================================================

pasangan_pandawa = set()
for kelompok in hari_pandawa.values():
    for h, p in kelompok:
        pasangan_pandawa.add((h, p))

def normalize_input(text):
    text = text.replace("'", "'").replace("’", "'").replace("‘", "'")
    return ' '.join(text.lower().split())

def get_hari_baik(laki_laki, perempuan):
    total_laki = hari[laki_laki[0]] + pasaran[laki_laki[1]]
    total_perempuan = hari[perempuan[0]] + pasaran[perempuan[1]]
    total = total_laki + total_perempuan
    sisa = total % 3
    key = 2 if sisa == 0 else (1 if sisa == 1 else 0)
    daftar = data_kelompok[key]
    return [item for item in daftar if (item[0], item[1]) not in pasangan_pandawa]

def get_bulan_baik(hanya_baik=True):
    return [b for b, s in aturan_bulan.items() if s == "baik" or (s == "boleh" and not hanya_baik)]

def filter_kematian(daftar, kematian):
    set_k = set(kematian)
    return [item for item in daftar if (item[0], item[1]) not in set_k]

# ============================================================
# FUNGSI CETAK DENGAN WRAP
# ============================================================

def cetak_label_nilai(label, nilai, lebar_label=15, lebar_maks=72):
    """
    Mencetak label dan nilai dengan titik dua sejajar.
    Jika nilai panjang, di-wrap dengan indentasi yang sama dengan posisi setelah titik dua.
    """
    label_str = f"{label:<{lebar_label}}"
    baris_pertama = f"{label_str} : {nilai}"
    if len(baris_pertama) <= lebar_maks:
        print(baris_pertama)
    else:
        indentasi = lebar_label + 3  # 3 = spasi + titik dua + spasi
        wrapper = textwrap.TextWrapper(width=lebar_maks, subsequent_indent=' ' * indentasi)
        nilai_wrap = wrapper.fill(nilai)
        print(f"{label_str} : {nilai_wrap}")

# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    print("\n" + "=" * 50)
    print("     PROGRAM HARI BAIK PERNIKAHAN")
    print("=" * 50 + "\n")

    hari_lower = {k.lower(): k for k in hari}
    pasaran_lower = {k.lower(): k for k in pasaran}

    while True:
        # Input laki-laki
        while True:
            raw = input("Laki-laki (hari pasaran): ").strip()
            norm = normalize_input(raw)
            parts = norm.split()
            if len(parts) == 2:
                h_norm, p_norm = parts
                if h_norm in hari_lower and p_norm in pasaran_lower:
                    h_laki = hari_lower[h_norm]
                    p_laki = pasaran_lower[p_norm]
                    break
            print("  ! Input salah, coba lagi.")

        # Input perempuan
        while True:
            raw = input("Perempuan (hari pasaran): ").strip()
            norm = normalize_input(raw)
            parts = norm.split()
            if len(parts) == 2:
                h_norm, p_norm = parts
                if h_norm in hari_lower and p_norm in pasaran_lower:
                    h_perempuan = hari_lower[h_norm]
                    p_perempuan = pasaran_lower[p_norm]
                    break
            print("  ! Input salah, coba lagi.")

        # Hitung
        laki_laki = (h_laki, p_laki)
        perempuan = (h_perempuan, p_perempuan)
        hasil_hari = get_hari_baik(laki_laki, perempuan)

        total_laki = hari[h_laki] + pasaran[p_laki]
        total_perempuan = hari[h_perempuan] + pasaran[p_perempuan]
        total = total_laki + total_perempuan
        sisa = total % 3

        # TAMPILAN DENGAN TITIK DUA SEJAJAR
        print("\n--- PERHITUNGAN ---")
        print(f"{'Laki-laki':<15} : {h_laki} + {p_laki} = {total_laki}")
        print(f"{'Perempuan':<15} : {h_perempuan} + {p_perempuan} = {total_perempuan}")
        print(f"{'Total':<15} : {total}, sisa {sisa}")

        if not hasil_hari:
            print("\nTidak ada hari baik (semua terkena pandawa).")
        else:
            print("\nHari baik (sebelum filter kematian):")
            for i, (h, p, j) in enumerate(hasil_hari, 1):
                print(f"  {i:2}. {h} + {p} = {j}")

            print("\n--- INPUT KEMATIAN (max 4, Enter selesai) ---")
            kematian = []
            for i in range(4):
                raw = input(f"  Kematian {i+1}: ").strip()
                if not raw:
                    break
                norm = normalize_input(raw)
                parts = norm.split()
                if len(parts) == 2:
                    h_norm, p_norm = parts
                    if h_norm in hari_lower and p_norm in pasaran_lower:
                        h = hari_lower[h_norm]
                        p = pasaran_lower[p_norm]
                        if (h, p) not in kematian:
                            kematian.append((h, p))
                        else:
                            print("    (sudah ada, abaikan)")
                    else:
                        print("    (input salah, lewati)")
                else:
                    print("    (input salah, lewati)")

            if kematian:
                hasil_hari = filter_kematian(hasil_hari, kematian)
                print("\nHari baik setelah eliminasi kematian:")
                if not hasil_hari:
                    print("  (Tidak ada tersisa)")
                else:
                    for i, (h, p, j) in enumerate(hasil_hari, 1):
                        print(f"  {i:2}. {h} + {p} = {j}")
            else:
                print("\n(Tidak ada filter kematian)")

        # ============================================================
        # REKOMENDASI BULAN
        # ============================================================
        print("\n--- BULAN BAIK ---")
        baik = ", ".join(get_bulan_baik(hanya_baik=True))
        boleh = ", ".join(get_bulan_baik(hanya_baik=False))

        cetak_label_nilai("Kategori baik", baik)
        cetak_label_nilai("Kategori boleh", boleh)

        # Ulangi?
        lagi = input("\nHitung lagi? (y/n): ").strip().lower()
        if lagi != 'y':
            print("\nTerima kasih, sampai jumpa!")
            break

if __name__ == "__main__":
    main()