"""
KALENDER JAWA MODERN (ANNO JAVANICO)
=====================================
Implementasi ilmiah berdasarkan naskah "Primbon Aji Saka – Almanak Pawukon 1000 Tahun"
karya R. Tanojo (Penerbit Trimurti, Surabaya).

Sistem ini merupakan akulturasi dari:
- Kalender Saka (Hindu, solar)
- Kalender Hijriah (Arab, lunar)
- Sistem Pawukon asli Jawa (wuku, masa-wuku, paringkelan)

Epoch: 1 Muharam 1555 Alip = 8 Juli 1633 M (Jumat Legi)

Referensi utama (halaman dalam naskah):
- Halaman 14-16 : Churuf/Kurup dan Sesebutaning Taun
- Halaman 17   : Panjang tahun dan bulan (wastu/wuntu, pemendekan)
- Halaman 21   : Windu, Wuku, Masa-Wuku, Tumbuk
- Halaman 22-23: Masa-Wuku dan Dapur Wuku
- Halaman 24-25: Paringkelan
- Halaman 26   : Lapan (Salapan) Anggara Kasih
- Halaman 28   : Bulan tanpa Anggara Kasih (Bulan Suwung)
- Halaman 37-52: Lambang Wuku pada awal setiap Windu
"""

import datetime
from typing import Tuple, Optional, Dict, Any, List


class JavaneseCalendar:
    """
    Kalender Jawa Modern (Anno Javanico).

    Kelas ini menyediakan konversi dari tanggal Gregorian ke seluruh elemen
    kalender Jawa berdasarkan naskah Primbon Aji Saka.

    Semua perhitungan berbasis pada jumlah hari sejak epoch (8 Juli 1633 M)
    dan mengikuti aturan-aturan yang didefinisikan dalam naskah.

    Properti utama yang dihitung:
    - Tahun Jawa (nomor dan nama dalam windu)
    - Bulan (Arab dan Jawa)
    - Tanggal
    - Hari (Saptawara) + Pasaran (Pancawara) + Paringkelan (Sadwara)
    - Wuku (nomor dan nama, serta Lambang Wuku untuk awal windu)
    - Masa-Wuku
    - Windu (nomor dan nama)
    - Kurup (Churuf) dengan nomor
    - Sesebutaning Taun (nama tahun berdasarkan hari 1 Sura)
    - Salapan (Lapan) dengan progress bar siklus Windu
    - Bulan tanpa Anggara Kasih (Selasa Kliwon)

    Metode:
        format() -> str : Tampilan output lengkap dengan progress bar
        to_dict() -> Dict[str, Any] : Seluruh properti dalam dictionary
    """

    # ========================================================================
    # 1. KONSTANTA DASAR
    # ========================================================================

    # Saptawara (7 hari) – halaman 14-16
    DAYS = ['Ahad', 'Senèn', 'Selasa', 'Rebo', 'Kemis', 'Jum\'at', 'Sabtu']

    # Pancawara (5 hari pasaran) – halaman 14-16
    PASARAN = ['Legi', 'Paing', 'Pon', 'Wagé', 'Kliwon']

    # Paringkelan (6 hari) – halaman 24-25
    PARINGKELAN = ['Tunglé', 'Arjang', 'Wurukung', 'Paningron', 'Uwas', 'Mawulu']

    # Nama tahun dalam 1 Windu (8 tahun) – halaman 14
    YEAR_NAMES = ['Alip', 'Ehé', 'Djimawal', 'Djé', 'Dal', 'Bé', 'Wawu', 'Djimächir']

    # Panjang hari tiap tahun dalam windu (wastu/wuntu) – halaman 17
    YEAR_LENGTHS = [354, 355, 354, 354, 355, 354, 354, 355]

    # Status tahun wastu/wuntu – halaman 17
    # Wastu = 354 hari, Wuntu = 355 hari
    YEAR_STATUS = {
        'Alip': 'wastu',
        'Ehé': 'wuntu',
        'Djimawal': 'wastu',
        'Djé': 'wastu',
        'Dal': 'wuntu',
        'Bé': 'wastu',
        'Wawu': 'wastu',
        'Djimächir': 'wuntu'
    }

    # Panjang hari berdasarkan status – halaman 17
    YEAR_LENGTH_BY_STATUS = {
        'wastu': 354,
        'wuntu': 355
    }

    # Nama bulan – Arab (halaman 7) dan Jawa (halaman 8-9)
    MONTHS = [
        'Muharam', 'Shafar', 'Rabiulawal', 'Rabiulakhir',
        'Djumadilawal', 'Djumadilakhir', 'Radjab', 'Sja\'ban',
        'Ramadhan', 'Sjawal', 'Zulkaédah', 'Zulhidjdjah'
    ]
    MONTHS_JAWA = [
        'Sura', 'Sapar', 'Mulud', 'Bakda Mulud',
        'Jumadilawal', 'Jumadilakhir', 'Rejeb', 'Ruwah',
        'Pasa', 'Sawal', 'Sela', 'Besar'
    ]

    # Panjang bulan untuk tahun wastu (354) dan wuntu (355) – halaman 17
    MONTH_LEN_WASTU = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]
    MONTH_LEN_WUNTU = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 30]

    # 30 Wuku (siklus 7 harian) – halaman 21
    WUKU = [
        'Sinta', 'Landep', 'Wukir', 'Kurantil', 'Tolu', 'Gumbreg',
        'Warigalit', 'Warigagung', 'Djulungwangi', 'Sungsang',
        'Galungan', 'Kuningan', 'Langkir', 'Mandasija', 'Djulungpudjud',
        'Pahang', 'Kuruwelut', 'Marakèh', 'Tambir', 'Medangkungan',
        'Maktal', 'Wujé', 'Manahil', 'Prangbakat', 'Bala', 'Wugu',
        'Wajang', 'Kulawu', 'Dukut', 'Watugunung'
    ]

    # 12 Masa-Wuku (siklus 35 harian) – halaman 22
    MASA_WUKU = [
        'I Kasa', 'II Karo', 'III Katelu', 'IV Kapat',
        'V Kalima', 'VI Kanem', 'VII Kapitu', 'VIII Kawolu',
        'IX Kasanga', 'X Kasapuluh', 'XI Desta', 'XII Saddha'
    ]

    # Masa-Wuku dan Wuku pada Anggara Kasih (Selasa Kliwon) – halaman 22
    ANGGARA_KASIH_WUKU_MAP = {
        'I Kasa': 'Mandasija',
        'II Karo': 'Tambir',
        'III Katelu': 'Prangbakat',
        'IV Kapat': 'Dukut',
        'V Kalima': 'Kurantil',
        'VI Kanem': 'Djulungwangi',
        'VII Kapitu': 'Mandasija',
        'VIII Kawolu': 'Tambir',
        'IX Kasanga': 'Prangbakat',
        'X Kasapuluh': 'Dukut',
        'XI Desta': 'Kurantil',
        'XII Saddha': 'Djulungwangi'
    }

    # 4 Windu Besar (siklus 32 tahun) – halaman 21
    MACRO_WINDUS = ['Adi', 'Kuntara', 'Sangara', 'Sentjaja']

    # ========================================================================
    # 2. SESEBUTANING TAUN & CHURUF (KURUP) – halaman 14-16
    # ========================================================================

    # Churuf (Kurup): periode 120 tahun dengan hari dan pasaran awal tahun Alip
    CHURUF_DATA = [
        (1555, 1674, "Djam'ijah Legi", 1),
        (1675, 1748, "Kamsijah Kliwon", 2),
        (1749, 1866, "Arba'ijah Wagé", 3),
        (1867, 1986, "Salasijah Pon", 4),
        (1987, 2106, "Isnainijah Paing", 5),
        (2107, 2226, "Ahadijah Legi", 6),
        (2227, 2346, "Sabtijah Kliwon", 7),
        (2347, 2466, "Djam'ijah Wagé", 8),
        (2467, 2586, "Kamsijah Pon", 9)
    ]

    # Sesebutaning Taun: matriks [kurup-1][year_index] – halaman 14-16
    SESEBUTAN_MATRIX = [
        # Kurup 1 (Djam'ijah Legi)
        ['Sukra Mangkara', 'Anggara Rekata', 'Ditê Kenaba', 'Respati Mintuna',
         'Soma Wretjita', 'Tumpak Mênda', 'Buddha Maêsa', 'Ditê Kenaba'],
        # Kurup 2 (Kamsijah Kliwon)
        ['Respati Mintuna', 'Soma Wretjita', 'Tumpak Mênda', 'Buddha Maêsa',
         'Ditê Kenaba', 'Sukra Mangkara', 'Anggara Rekata', 'Tumpak Mênda'],
        # Kurup 3 (Arba'ijah Wagé) ABOGE
        ['Buddha Maêsa', 'Ditê Kenaba', 'Sukra Mangkara', 'Anggara Rekata',
         'Tumpak Mênda', 'Respati Mintuna', 'Soma Wretjita', 'Sukra Mangkara'],
        # Kurup 4 (Salasijah Pon) ASAPON
        ['Anggara Rekata', 'Tumpak Mênda', 'Respati Mintuna', 'Soma Wretjita',
         'Sukra Mangkara', 'Buddha Maêsa', 'Ditê Kenaba', 'Respati Mintuna'],
        # Kurup 5 (Isnainijah Paing)
        ['Soma Wretjita', 'Sukra Mangkara', 'Buddha Maêsa', 'Ditê Kenaba',
         'Respati Mintuna', 'Anggara Rekata', 'Tumpak Mênda', 'Sukra Mangkara'],
        # Kurup 6 (Ahadijah Legi)
        ['Ditê Kenaba', 'Respati Mintuna', 'Anggara Rekata', 'Tumpak Mênda',
         'Buddha Maêsa', 'Soma Wretjita', 'Sukra Mangkara', 'Anggara Rekata'],
        # Kurup 7 (Sabtijah Kliwon)
        ['Tumpak Mênda', 'Buddha Maêsa', 'Soma Wretjita', 'Sukra Mangkara',
         'Anggara Rekata', 'Ditê Kenaba', 'Respati Mintuna', 'Soma Wretjita'],
        # Kurup 8 (Djam'ijah Wagé)
        ['Sukra Mangkara', 'Anggara Rekata', 'Ditê Kenaba', 'Respati Mintuna',
         'Soma Wretjita', 'Tumpak Mênda', 'Buddha Maêsa', 'Ditê Kenaba'],
        # Kurup 9 (Kamsijah Pon)
        ['Respati Mintuna', 'Soma Wretjita', 'Tumpak Mênda', 'Buddha Maêsa',
         'Ditê Kenaba', 'Sukra Mangkara', 'Anggara Rekata', 'Tumpak Mênda']
    ]

    # ========================================================================
    # 3. LAMBANG WUKU (Awal Windu) – halaman 37-52 (tabel)
    # ========================================================================

    LAMBANG_WUKU_MAP = {
        'Adi': 'Langkir',
        'Kuntara': 'Kulawu',
        'Sangara': 'Langkir',
        'Sentjaja': 'Kulawu'
    }

    # ========================================================================
    # 4. ATURAN KHUSUS
    # ========================================================================

    # Tahun-tahun yang dipendekkan (1 hari di Zulhidjdjah) – halaman 17
    SHORTENED_YEARS = {1674, 1748, 1866, 1986, 2106, 2226, 2346, 2466}

    # Epoch: 1 Muharam 1555 Alip = 8 Juli 1633 M (Jumat Legi)
    EPOCH = datetime.date(1633, 7, 8)

    # ========================================================================
    # 5. INISIALISASI
    # ========================================================================

    def __init__(self, greg_date: datetime.date):
        """
        Konstruktor: menghitung seluruh elemen kalender Jawa dari tanggal Gregorian.

        Algoritma perhitungan berdasarkan naskah Primbon Aji Saka:

        1. **Tahun Jawa (5A)**:
           - Mulai dari tahun 1555.
           - Akumulasi hari per tahun (sesuai YEAR_LENGTHS) hingga melewati `days_since_epoch`.
           - Tahun yang termasuk SHORTENED_YEARS dikurangi 1 hari (pemendekan churuf, hal. 17).
           - Formula: `cum_days = sum_{y=1555}^{year-1} length(y)`, dengan `length(y) = YEAR_LENGTHS[(y-1555)%8] - (1 if y in SHORTENED_YEARS else 0)`.
           - Hasil: `self.javanese_year`, `self.year_name`, `self.year_index`.

        2. **Bulan & Tanggal (5B)**:
           - Ambil panjang bulan berdasarkan tahun (wastu/wuntu), lalu kurangi 1 hari pada Zulhidjdjah jika tahun dipendekkan.
           - Kurangi `remaining_days` dengan panjang bulan secara berurutan hingga ditemukan bulan yang sesuai.
           - Hasil: `self.month_index`, `self.month_name_arab`, `self.month_name_jawa`, `self.day_of_month`.

        3. **Dina, Pasaran, Paringkelan (5C)**:
           - Epoch adalah Jumat Legi, sehingga:
             - `day_index = (5 + days_since_epoch) % 7`  (Jumat=5)
             - `pasaran_index = days_since_epoch % 5`      (Legi=0)
           - Paringkelan (siklus 6 hari) dengan offset 2 agar hari 0 = Wurukung (indeks 2).
             - `paringkelan_index = (days_since_epoch + 2) % 6`
           - Hasil: `day_name`, `pasaran_name`, `paringkelan_name`.

        4. **Wuku (5D)**:
           - Wuku berganti setiap 7 hari, dimulai dari hari Minggu.
           - Epoch (Jumat) berada pada Wuku Kulawu (indeks 27). Hari Minggu berikutnya (2 hari kemudian) adalah indeks 28.
           - Formula: `wuku_index = floor((days_since_epoch + 194) / 7) % 30`, dengan 194 = (28*7 - 2) untuk menyelaraskan.
           - Hasil: `wuku_number` (1-based), `wuku_name`.

        5. **Masa-Wuku (5E)**:
           - Masa-Wuku berganti setiap 35 hari, dimulai dari Anggara Kasih (Selasa Kliwon).
           - Epoch (Jumat) berada pada Masa-Wuku IX Kasanga (indeks 8). Offset = 8*35 = 280.
           - Formula: `masa_wuku_index = floor((days_since_epoch + 280) / 35) % 12`.
           - Hasil: `masa_wuku_name`.

        6. **Windu Besar (5F)**:
           - 1 Windu Besar = 4 Windu kecil = 32 tahun.
           - Indeks = `floor((tahun - 1555 + 7) / 8) % 4` (ceil pembagian 8).
           - Hasil: `macro_windu_name`, `macro_windu_number` (1-based).

        7. **Lambang Wuku (5G)**:
           - Berdasarkan tabel halaman 37-52: Adi & Sangara → Langkir; Kuntara & Sentjaja → Kulawu.
           - Hasil: `lambang_wuku`.

        8. **Churuf / Kurup (5H)**:
           - Mencari churuf berdasarkan rentang tahun dari CHURUF_DATA.
           - Hasil: `churuf_name`, `kurup_number`.

        9. **Sesebutaning Taun (5I)**:
           - Mengambil dari SESEBUTAN_MATRIX berdasarkan kurup dan year_index.
           - Hasil: `sesebutaning_taun`.

        10. **1 Sura (5J)**:
            - Menghitung hari dan pasaran pada 1 Muharam tahun tersebut.
            - `first_day_idx = (5 + cum_days_to_1_sura) % 7`.
            - `first_pasaran_idx = cum_days_to_1_sura % 5`.
            - Hasil: `first_day_1_sura`, `first_pasaran_1_sura`.

        11. **Salapan & Progress Windu (5K)**:
            - 1 Salapan (Lapan) = 35 hari.
            - 1 Windu = 8 tahun = 2835 hari (atau 2834 jika ada tahun pendek).
            - Total Salapan dalam 1 Windu = 2835 // 35 = 81.
            - Hitung hari yang sudah dilalui dalam Windu saat ini (`days_since_windu_start`).
            - `lapan_index = floor(days_since_windu_start / 35) % 81`.
            - `lapan_number = lapan_index + 1`.
            - Hasil: `lapan_number`, `lapan_total`, `lapan_start_date`, `windu_progress_percent`.

        12. **Dapur Wuku (5L)**:
            - 1 Dapur Wuku = 210 hari.
            - `dapur_wuku_count = floor(days_since_epoch / 210)`.

        13. **Bulan tanpa Anggara Kasih (5M)**:
            - Mendeteksi bulan-bulan yang tidak memiliki Selasa Kliwon (Anggara Kasih) dengan iterasi harian per bulan.
            - Hasil: `bulan_tanpa_anggara_kasih` (list nama bulan Jawa).
        """
        self.greg_date = greg_date
        self.days_since_epoch = (greg_date - self.EPOCH).days

        # --------------------------------------------------------------------
        # 5A. TAHUN JAWA – halaman 17-18
        # --------------------------------------------------------------------
        year = 1555
        cum_days = 0
        while True:
            idx = (year - 1555) % 8
            length = self.YEAR_LENGTHS[idx]
            if year in self.SHORTENED_YEARS:
                length -= 1
            if cum_days + length > self.days_since_epoch:
                break
            cum_days += length
            year += 1

        self.javanese_year = year
        self.cum_days_to_1_sura = cum_days
        self.remaining_days = self.days_since_epoch - cum_days
        self.year_index = (year - 1555) % 8
        self.year_name = self.YEAR_NAMES[self.year_index]

        # --------------------------------------------------------------------
        # 5B. BULAN & TANGGAL – halaman 17
        # --------------------------------------------------------------------
        is_wuntu = (self.YEAR_LENGTHS[self.year_index] == 355)
        month_lengths = self.MONTH_LEN_WUNTU.copy() if is_wuntu else self.MONTH_LEN_WASTU.copy()
        if year in self.SHORTENED_YEARS:
            month_lengths[-1] -= 1

        month = 0
        for i, length in enumerate(month_lengths):
            if self.remaining_days >= length:
                self.remaining_days -= length
                month += 1
            else:
                break

        self.month_index = month
        self.month_name_arab = self.MONTHS[month]
        self.month_name_jawa = self.MONTHS_JAWA[month]
        self.day_of_month = self.remaining_days + 1

        # --------------------------------------------------------------------
        # 5C. DINA, PASARAN, PARINGKELAN – halaman 24-25
        # --------------------------------------------------------------------
        self.day_index = (5 + self.days_since_epoch) % 7
        self.day_name = self.DAYS[self.day_index]

        self.pasaran_index = self.days_since_epoch % 5
        self.pasaran_name = self.PASARAN[self.pasaran_index]

        self.paringkelan_index = (self.days_since_epoch + 2) % 6
        self.paringkelan_name = self.PARINGKELAN[self.paringkelan_index]

        # --------------------------------------------------------------------
        # 5D. WUKU – halaman 21
        # --------------------------------------------------------------------
        self.wuku_index = ((self.days_since_epoch + 194) // 7) % 30
        self.wuku_number = self.wuku_index + 1
        self.wuku_name = self.WUKU[self.wuku_index]

        # --------------------------------------------------------------------
        # 5E. MASA-WUKU – halaman 22-23
        # --------------------------------------------------------------------
        self.masa_wuku_index = ((self.days_since_epoch + 311) // 35) % 12
        self.masa_wuku_name = self.MASA_WUKU[self.masa_wuku_index]

        # Wuku pada Anggara Kasih (Selasa Kliwon) – halaman 22
        self.anggara_kasih_wuku = self.ANGGARA_KASIH_WUKU_MAP.get(self.masa_wuku_name, '—')

        # --------------------------------------------------------------------
        # 5F. WINDU BESAR – halaman 21
        # --------------------------------------------------------------------
        self.macro_windu_index = ((self.javanese_year - 1555 + 7) // 8) % 4
        self.macro_windu_name = self.MACRO_WINDUS[self.macro_windu_index]
        self.macro_windu_number = self.macro_windu_index + 1

        # --------------------------------------------------------------------
        # 5G. LAMBANG WUKU – halaman 37-52
        # --------------------------------------------------------------------
        self.lambang_wuku = self.LAMBANG_WUKU_MAP.get(self.macro_windu_name, '—')

        # --------------------------------------------------------------------
        # 5H. CHURUF (KURUP) – halaman 14-16
        # --------------------------------------------------------------------
        churuf_name, kurup_number = self._get_churuf(self.javanese_year)
        self.churuf_name = churuf_name
        self.kurup_number = kurup_number

        # --------------------------------------------------------------------
        # 5I. SESEBUTANING TAUN – halaman 14-16
        # --------------------------------------------------------------------
        if self.kurup_number is not None:
            self.sesebutaning_taun = self.SESEBUTAN_MATRIX[self.kurup_number - 1][self.year_index]
        else:
            self.sesebutaning_taun = None

        # --------------------------------------------------------------------
        # 5J. 1 SURA – halaman 14-16
        # --------------------------------------------------------------------
        first_day_idx = (5 + self.cum_days_to_1_sura) % 7
        first_pasaran_idx = self.cum_days_to_1_sura % 5
        self.first_day_1_sura = self.DAYS[first_day_idx]
        self.first_pasaran_1_sura = self.PASARAN[first_pasaran_idx]
        self.sesebutan_keterangan = (
            f"1 Sura tahun {self.javanese_year} {self.year_name} "
            f"({self.first_day_1_sura} {self.first_pasaran_1_sura})."
        )

        # --------------------------------------------------------------------
        # 5K. SALAPAN & PROGRESS WINDU – halaman 26
        # --------------------------------------------------------------------
        windu_start_year = 1555 + ((self.javanese_year - 1555) // 8) * 8
        windu_end_year = windu_start_year + 7
        windu_days = 0
        for y in range(windu_start_year, windu_end_year + 1):
            idx = (y - 1555) % 8
            length = self.YEAR_LENGTHS[idx]
            if y in self.SHORTENED_YEARS:
                length -= 1
            windu_days += length

        temp_year = 1555
        temp_cum = 0
        while temp_year < windu_start_year:
            idx = (temp_year - 1555) % 8
            length = self.YEAR_LENGTHS[idx]
            if temp_year in self.SHORTENED_YEARS:
                length -= 1
            temp_cum += length
            temp_year += 1

        total_days_since_epoch = self.days_since_epoch
        days_since_windu_start = total_days_since_epoch - temp_cum

        self.windu_start_year = windu_start_year
        self.windu_total_days = windu_days
        self.days_since_windu_start = days_since_windu_start
        self.windu_progress_percent = (days_since_windu_start / windu_days) * 100

        self.lapan_index = (days_since_windu_start // 35) % 81
        self.lapan_number = self.lapan_index + 1
        self.lapan_total = 81
        days_to_lapan_start = (35 - (days_since_windu_start % 35)) % 35
        self.lapan_start_date = self.greg_date + datetime.timedelta(days=days_to_lapan_start)

        # --------------------------------------------------------------------
        # 5N. HARI SEJAK ANGGARA KASIH TERAKHIR
        # --------------------------------------------------------------------
        # Anggara Kasih = Selasa Kliwon = hari ke-4 dari epoch (Jumat Legi)
        # 1 Masa-Wuku = 35 hari, selalu dimulai pada Anggara Kasih
        first_AK = 4  # hari ke-4 adalah Selasa Kliwon pertama
        if self.days_since_epoch >= first_AK:
            last_AK_offset = first_AK + 35 * ((self.days_since_epoch - first_AK) // 35)
            self.days_since_last_AK = self.days_since_epoch - last_AK_offset
        else:
            self.days_since_last_AK = 0

        # --------------------------------------------------------------------
        # 5L. DAPUR WUKU – halaman 23
        # --------------------------------------------------------------------
        self.dapur_wuku_count = self.days_since_epoch // 210

        # --------------------------------------------------------------------
        # 5M. BULAN TANPA ANGGARA KASIH – halaman 28
        # --------------------------------------------------------------------
        self.bulan_tanpa_anggara_kasih = self._get_bulan_tanpa_anggara_kasih(self.javanese_year)

    def _get_churuf(self, year: int) -> Tuple[Optional[str], Optional[int]]:
        """
        Mencari churuf (kurup) berdasarkan tahun Jawa.

        Referensi: halaman 14-16.
        Churuf berganti setiap 120 tahun karena selisih 1 hari antara
        perhitungan Jawa dan Hijriah (lihat halaman 13).
        """
        for start, end, name, number in self.CHURUF_DATA:
            if start <= year <= end:
                return name, number
        return None, None

    def get_year_info(self) -> Dict[str, Any]:
        """
        Mengembalikan informasi status dan panjang tahun saat ini.

        Referensi: halaman 17.
        """
        status = self.YEAR_STATUS.get(self.year_name, 'unknown')
        length = self.YEAR_LENGTH_BY_STATUS.get(status, 0)
        return {
            'year_name': self.year_name,
            'status': status,
            'length_days': length,
            'is_wuntu': status == 'wuntu'
        }

    def _get_month_lengths_for_year(self, year: int) -> List[int]:
        """
        Mengembalikan daftar panjang bulan untuk tahun tertentu (dengan pemendekan).

        Referensi: halaman 17.
        Jika tahun termasuk SHORTENED_YEARS, Zulhidjdjah (bulan ke-12) dikurangi 1 hari.
        """
        idx = (year - 1555) % 8
        is_wuntu = (self.YEAR_LENGTHS[idx] == 355)
        month_lengths = self.MONTH_LEN_WUNTU.copy() if is_wuntu else self.MONTH_LEN_WASTU.copy()
        if year in self.SHORTENED_YEARS:
            month_lengths[-1] -= 1
        return month_lengths

    def _get_bulan_tanpa_anggara_kasih(self, year: int) -> List[str]:
        """
        Mendeteksi bulan-bulan yang tidak memiliki Selasa Kliwon (Anggara Kasih)
        dalam satu tahun Jawa. Disebut 'bulan suwung' dalam primbon.

        Algoritma:
        1. Hitung hari ke-0 dari 1 Sura tahun tersebut (cum_days dari epoch).
        2. Untuk setiap bulan, iterasi setiap harinya dan cek apakah ada hari
           dengan day_index==2 (Selasa) dan pasaran_index==4 (Kliwon).
        3. Jika tidak ditemukan, tambahkan nama bulan Jawa ke daftar.

        Referensi: halaman 28.
        """
        month_lengths = self._get_month_lengths_for_year(year)

        # Hitung cum_days dari epoch ke 1 Sura tahun ini
        temp_year = 1555
        temp_cum = 0
        while temp_year < year:
            idx = (temp_year - 1555) % 8
            length = self.YEAR_LENGTHS[idx]
            if temp_year in self.SHORTENED_YEARS:
                length -= 1
            temp_cum += length
            temp_year += 1
        start_days = temp_cum

        suwung_months = []
        for i, length in enumerate(month_lengths):
            found = False
            for d in range(length):
                day_idx = (5 + start_days + d) % 7
                pas_idx = (start_days + d) % 5
                if day_idx == 2 and pas_idx == 4:  # Selasa Kliwon
                    found = True
                    break
            if not found:
                suwung_months.append(self.MONTHS_JAWA[i])
            start_days += length
        return suwung_months

    def format(self) -> str:
        """
        Menampilkan informasi kalender Jawa secara lengkap dengan progress bar.

        Format output:
        - Gregorian: tanggal Masehi
        - Jawa: tahun dan nama tahun
        - Bulan: nama Jawa dan tanggal
        - Dina: hari + pasaran + paringkelan
        - Wuku: nomor dan nama
        - Masa-Wuku: nama
        - Windu: nomor dan nama
        - Kurup: nomor dan nama
        - Sesebutan: nama tradisional
        - Lambang Wuku: nama wuku awal windu
        - Salapan: nomor/81 dengan progress bar, persentase, dan hari dalam windu
        - Bulan tanpa Anggara Kasih: daftar bulan
        """
        bar_length = 14
        filled = int(bar_length * self.windu_progress_percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        progress_line = (
            f"📌 Salapan   : {self.lapan_number}/81 [{bar}] "
            f"{self.windu_progress_percent:.1f}% ({int(self.days_since_windu_start)}/{self.windu_total_days} hari)"
        )
        suwung_str = ', '.join(self.bulan_tanpa_anggara_kasih) if self.bulan_tanpa_anggara_kasih else "Tidak ada"

        # Ambil informasi tahun
        year_info = self.get_year_info()
        year_status_line = f"📌 Status    : {year_info['status']} ({year_info['length_days']} hari)"

        return (
            f"📅 Gregorian : {self.greg_date.strftime('%Y-%m-%d')}\n"
            f"🗓️ Jawa      : AJ {self.javanese_year} {self.year_name}\n"
            f"📌 1 Sura    : {self.sesebutan_keterangan}\n"
            f"🏷️ Sesebutan : {self.sesebutaning_taun}\n"
            f"{year_status_line}\n"
            f"📆 Bulan     : {self.month_name_jawa} {self.day_of_month}\n"
            f"📌 Dina      : {self.day_name} {self.pasaran_name} {self.paringkelan_name}\n"
            f"🌀 Wuku      : {self.wuku_number}. {self.wuku_name}\n"
            f"⏳ Masa-Wuku : {self.masa_wuku_name} ({self.days_since_last_AK} hari sejak Anggara Kasih wuku {self.anggara_kasih_wuku})\n"        
            f"🔁 Windu     : {self.macro_windu_number}. {self.macro_windu_name}\n"
            f"🔰 Kurup     : {self.kurup_number}. {self.churuf_name}\n"
            f"🏷️ Lambang   : {self.lambang_wuku}\n"
            f"{progress_line}\n"
            f"📌 Bulan tanpa Anggara Kasih : {suwung_str}"
        )            


    def to_dict(self) -> Dict[str, Any]:
        """
        Mengembalikan seluruh properti sebagai dictionary untuk keperluan
        serialisasi atau integrasi dengan aplikasi lain.
        """
        year_info = self.get_year_info()  # Ambil sekali
        return {
            'gregorian_date': self.greg_date.isoformat(),
            'javanese_year': self.javanese_year,
            'year_name': self.year_name,
            'year_status': year_info['status'],
            'year_length_days': year_info['length_days'],
            'month_name_arab': self.month_name_arab,
            'month_name_jawa': self.month_name_jawa,
            'month_number': self.month_index + 1,
            'day_of_month': self.day_of_month,
            'day_name': self.day_name,
            'pasaran': self.pasaran_name,
            'paringkelan': self.paringkelan_name,
            'wuku_number': self.wuku_number,
            'wuku_name': self.wuku_name,
            'masa_wuku': self.masa_wuku_name,
            'masa_wuku': self.masa_wuku_name,
            'anggara_kasih_wuku': self.anggara_kasih_wuku,            
            'macro_windu_name': self.macro_windu_name,
            'macro_windu_number': self.macro_windu_number,
            'lambang_wuku': self.lambang_wuku,
            'kurup_number': self.kurup_number,
            'churuf_name': self.churuf_name,
            'sesebutaning_taun': self.sesebutaning_taun,
            'first_day_1_sura': self.first_day_1_sura,
            'first_pasaran_1_sura': self.first_pasaran_1_sura,
            'sesebutan_keterangan': self.sesebutan_keterangan,
            'lapan_number': self.lapan_number,
            'lapan_total': self.lapan_total,
            'lapan_start_date': self.lapan_start_date.isoformat(),
            'days_since_last_AK': self.days_since_last_AK,
            'windu_start_year': self.windu_start_year,
            'windu_total_days': self.windu_total_days,
            'days_since_windu_start': int(self.days_since_windu_start),
            'windu_progress_percent': self.windu_progress_percent,
            'bulan_tanpa_anggara_kasih': self.bulan_tanpa_anggara_kasih,
            'dapur_wuku_count': self.dapur_wuku_count,
            'days_since_epoch': self.days_since_epoch
        }


# ============================================================================
# FUNGSI KONVERSI BALIK (JAWA -> MASEHI)
# ============================================================================

def from_javanese(year: int, month_name: str, day: int) -> Optional[datetime.date]:
    """
    Mengonversi tanggal Jawa (tahun, bulan Jawa, tanggal) ke tanggal Masehi.

    Algoritma:
    1. Normalisasi nama bulan Jawa dan cari indeksnya.
    2. Hitung jumlah hari dari epoch ke 1 Sura tahun yang diminta.
    3. Dapatkan panjang bulan untuk tahun tersebut.
    4. Validasi tanggal (1..panjang bulan).
    5. Hitung offset hari dalam tahun: sum(panjang bulan sebelum bulan target) + (day - 1).
    6. Total hari = cum_days + offset.
    7. Kembalikan tanggal Masehi = EPOCH + total_hari.

    Referensi: halaman 17 (panjang bulan) dan perhitungan cum_days.
    """
    # Normalisasi nama bulan
    month_name = month_name.strip().lower()
    month_map = {m.lower(): i for i, m in enumerate(JavaneseCalendar.MONTHS_JAWA)}
    if month_name not in month_map:
        return None
    month_index = month_map[month_name]

    # Hitung cum_days ke 1 Sura tahun tersebut
    temp_year = 1555
    temp_cum = 0
    while temp_year < year:
        idx = (temp_year - 1555) % 8
        length = JavaneseCalendar.YEAR_LENGTHS[idx]
        if temp_year in JavaneseCalendar.SHORTENED_YEARS:
            length -= 1
        temp_cum += length
        temp_year += 1

    # Dapatkan panjang bulan untuk tahun tersebut
    idx = (year - 1555) % 8
    is_wuntu = (JavaneseCalendar.YEAR_LENGTHS[idx] == 355)
    month_lengths = JavaneseCalendar.MONTH_LEN_WUNTU.copy() if is_wuntu else JavaneseCalendar.MONTH_LEN_WASTU.copy()
    if year in JavaneseCalendar.SHORTENED_YEARS:
        month_lengths[-1] -= 1

    # Validasi tanggal
    if day < 1 or day > month_lengths[month_index]:
        return None

    # Offset hari dalam tahun
    target_day_offset = sum(month_lengths[:month_index]) + (day - 1)
    total_days = temp_cum + target_day_offset

    epoch = JavaneseCalendar.EPOCH
    target_date = epoch + datetime.timedelta(days=total_days)
    return target_date


# ============================================================================
# FUNGSI-FUNGSI MENU (INTERAKTIF)
# ============================================================================

def print_header(title: str):
    """Mencetak header menu dengan garis pemisah."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def menu_realtime():
    """Menu 1: Menampilkan informasi kalender Jawa untuk hari ini."""
    today = datetime.date.today()
    kal = JavaneseCalendar(today)
    print_header("INFO REALTIME")
    print(kal.format())
    input("\nTekan Enter untuk kembali...")


def menu_input_tanggal():
    """Menu 2: Konversi dari tanggal Masehi yang diinput user."""
    try:
        date_str = input("Masukkan tanggal (YYYY-MM-DD): ").strip()
        year, month, day = map(int, date_str.split('-'))
        greg_date = datetime.date(year, month, day)
        kal = JavaneseCalendar(greg_date)
        print_header("HASIL KONVERSI")
        print(kal.format())
    except Exception as e:
        print(f"❌ Error: {e}. Format harus YYYY-MM-DD.")
    input("\nTekan Enter untuk kembali...")


def menu_konversi():
    """Menu 3: Konversi dari tanggal Jawa (tahun, bulan, tanggal) ke Masehi."""
    try:
        year = int(input("Masukkan tahun Jawa (contoh: 1960): ").strip())
        print("Nama bulan Jawa yang tersedia:")
        print(", ".join(JavaneseCalendar.MONTHS_JAWA))
        month_name = input("Masukkan nama bulan Jawa: ").strip()
        day = int(input("Masukkan tanggal (1-30): ").strip())

        result_date = from_javanese(year, month_name, day)
        if result_date:
            print_header("HASIL KONVERSI")
            print(f"📅 Masehi : {result_date.strftime('%Y-%m-%d')}")
            # Tampilkan info lengkap untuk tanggal tersebut
            kal = JavaneseCalendar(result_date)
            print(kal.format())
        else:
            print("❌ Nama bulan atau tanggal tidak valid. Periksa input Anda.")
    except ValueError:
        print("❌ Input harus berupa angka untuk tahun dan tanggal.")
    except Exception as e:
        print(f"❌ Error: {e}")
    input("\nTekan Enter untuk kembali...")


def menu_bulan_suwung():
    """Menu 4: Mencari bulan tanpa Anggara Kasih (Selasa Kliwon) dalam tahun tertentu."""
    try:
        year = int(input("Masukkan tahun Jawa (contoh: 1960): ").strip())
        # Ambil contoh tanggal di tahun tersebut untuk inisialisasi objek
        # Cari tanggal 1 Sura tahun tersebut
        temp_year = 1555
        temp_cum = 0
        while temp_year < year:
            idx = (temp_year - 1555) % 8
            length = JavaneseCalendar.YEAR_LENGTHS[idx]
            if temp_year in JavaneseCalendar.SHORTENED_YEARS:
                length -= 1
            temp_cum += length
            temp_year += 1
        epoch = JavaneseCalendar.EPOCH
        sample_date = epoch + datetime.timedelta(days=temp_cum)
        kal = JavaneseCalendar(sample_date)

        suwung_list = kal.bulan_tanpa_anggara_kasih
        print_header(f"BULAN TANPA ANGGARA KASIH DI TAHUN {year} {kal.year_name}")
        if suwung_list:
            print("Bulan-bulan yang tidak memiliki Selasa Kliwon:")
            for bulan in suwung_list:
                print(f"  - {bulan}")
        else:
            print("Tidak ada bulan tanpa Anggara Kasih di tahun ini.")
    except Exception as e:
        print(f"❌ Error: {e}")
    input("\nTekan Enter untuk kembali...")


# ============================================================================
# MENU UTAMA
# ============================================================================

def main():
    """Menu interaktif untuk mengakses semua fitur kalender Jawa."""
    while True:
        print("\n" + "=" * 80)
        print(" KALENDER JAWA-MODERN AJ (ANNO JAVANICO)")
        print("=" * 80)
        print("1. Realtime (hari ini)")
        print("2. Input tanggal Masehi")
        print("3. Konversi (tanggal Jawa → Masehi)")
        print("4. Bulan tanpa Anggara Kasih")
        print("5. Keluar")
        print("=" * 80)

        pilihan = input("Pilih menu (1-5): ").strip()
        if pilihan == '1':
            menu_realtime()
        elif pilihan == '2':
            menu_input_tanggal()
        elif pilihan == '3':
            menu_konversi()
        elif pilihan == '4':
            menu_bulan_suwung()
        elif pilihan == '5':
            print("Terima kasih telah menggunakan Kalender Jawa Modern.")
            break
        else:
            print("❌ Pilihan tidak valid. Silakan coba lagi.")
            input("Tekan Enter untuk melanjutkan...")


if __name__ == "__main__":
    main()