<div align="center">

# 🎵 Audio Converter Pro

**Konverter audio batch dengan GUI modern, ringan, dan mudah dipakai.**
Ditulis dengan Python + Tkinter, ditenagai FFmpeg.

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![FFmpeg](https://img.shields.io/badge/Powered%20by-FFmpeg-007808?logo=ffmpeg&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-Tkinter-4f46e5)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## ✨ Kenapa Audio Converter Pro?

Tidak perlu hafal perintah FFmpeg. Cukup **tambah file → pilih format → klik Konversi**.
Tanpa library pihak ketiga yang wajib dipasang, hanya Python dan FFmpeg.

## 📸 Tampilan

> Letakkan screenshot aplikasi di folder `screenshots/` lalu aktifkan baris di bawah.

<!-- ![Screenshot](screenshots/main.png) -->

## 🚀 Fitur Utama

| Fitur | Keterangan |
|-------|------------|
| 📂 **Konversi batch** | Tambah banyak file sekaligus, atau satu folder lengkap dengan subfoldernya |
| 🎚️ **8 format output** | MP3, WAV, FLAC, AAC (M4A), OGG, OPUS, WMA, AIFF |
| 🎬 **Ekstrak audio dari video** | MP4, MKV, AVI, MOV, FLV, 3GP, dan lainnya |
| ⚙️ **Pengaturan lengkap** | Bitrate, sample rate, channel (mono/stereo), normalisasi volume |
| 📊 **Progress real-time** | Status per file di tabel + progress bar keseluruhan |
| ⏹️ **Bisa dibatalkan** | Tombol Batal menghentikan proses dan membersihkan file yang belum selesai |
| 🖱️ **Drag & drop** | Seret file atau folder langsung ke daftar (opsional) |
| 🛡️ **Aman** | File asli tidak pernah tertimpa kecuali Anda mengizinkannya |
| 📜 **Log detail** | Lihat perintah FFmpeg dan pesan error jika ada konversi yang gagal |
| 📜 **Scrollable** | Seluruh jendela bisa digulir, nyaman di layar kecil |
| 🔍 **Deteksi FFmpeg otomatis** | Atau pilih lokasi `ffmpeg` secara manual lewat tombol **Atur FFmpeg** |

## 🎧 Format yang Didukung

**Output**

| Format | Ekstensi | Tipe | Catatan |
|--------|----------|------|---------|
| MP3 | `.mp3` | Lossy | Paling kompatibel di semua perangkat |
| AAC (M4A) | `.m4a` | Lossy | Efisien, standar Apple dan banyak ponsel |
| OGG Vorbis | `.ogg` | Lossy | Open source, kualitas bagus |
| OPUS | `.opus` | Lossy | Sangat efisien, bagus untuk suara/podcast |
| WMA | `.wma` | Lossy | Format Windows Media |
| FLAC | `.flac` | Lossless | Kualitas asli, ukuran lebih kecil dari WAV |
| WAV | `.wav` | Lossless | Tanpa kompresi (PCM 16-bit) |
| AIFF | `.aiff` | Lossless | Tanpa kompresi, umum di ekosistem Apple |

**Input:** `mp3 wav flac aac m4a ogg opus wma aiff aif amr ac3 mka ape wv webm mp4 mkv avi mov flv 3gp`

## 📦 Instalasi

### 1. Siapkan Python

Butuh **Python 3.8 atau lebih baru**. Unduh di [python.org](https://www.python.org/downloads/).
Tkinter sudah termasuk di instalasi Python standar.

### 2. Pasang FFmpeg

| Sistem | Perintah |
|--------|----------|
| **Windows** | `winget install Gyan.FFmpeg` atau `choco install ffmpeg` |
| **macOS** | `brew install ffmpeg` |
| **Ubuntu / Debian** | `sudo apt install ffmpeg python3-tk` |

> 💡 **Windows manual:** unduh build dari [ffmpeg.org](https://ffmpeg.org/download.html), lalu tambahkan folder `bin` ke `PATH`.
> Atau cukup taruh `ffmpeg.exe` dan `ffprobe.exe` **di folder yang sama dengan skrip**.

Aplikasi mencari FFmpeg secara berurutan di: folder skrip → `ffmpeg/` → `ffmpeg/bin/` → `PATH`.

### 3. Unduh proyek

```bash
git clone https://github.com/muhdi15/AudConv.git
cd AudConv
```

### 4. (Opsional) Aktifkan drag & drop

```bash
pip install tkinterdnd2
```

## ▶️ Cara Menjalankan

```bash
python audio_converter.py
```

## 📖 Cara Pakai

1. **Tambahkan file**: klik **＋ Tambah File** atau **📁 Tambah Folder**, atau seret file ke daftar.
2. **Pilih format tujuan** (misalnya MP3) dan atur kualitas sesuai kebutuhan.
3. **Tentukan folder tujuan**: sama dengan file asli, atau pilih folder lain.
4. Klik **▶ Konversi Sekarang** dan pantau progress-nya.
5. Selesai! Folder hasil akan terbuka otomatis (bisa dimatikan).

> ⌨️ **Tips:** tekan tombol `Delete` untuk menghapus file terpilih dari daftar.

## 🎛️ Penjelasan Pengaturan

| Pengaturan | Fungsi |
|------------|--------|
| **Format tujuan** | Format hasil konversi |
| **Kualitas (bitrate)** | Hanya untuk format lossy. Makin tinggi, makin bagus dan makin besar ukuran file |
| **Sample rate** | `Asli` mempertahankan aslinya. Pilihan: 8000 sampai 96000 Hz |
| **Channel** | `Asli`, `Mono` (1 channel), atau `Stereo` (2 channel) |
| **Normalisasi volume** | Menyamakan kenyaringan memakai filter `loudnorm` FFmpeg |
| **Timpa file yang sudah ada** | Jika mati, file baru diberi nama `lagu (1).mp3` agar tidak menimpa |
| **Buka folder setelah selesai** | Membuka folder hasil otomatis |

### 🎯 Panduan memilih bitrate

| Bitrate | Cocok untuk |
|---------|-------------|
| 64k – 96k | Rekaman suara, podcast, audiobook |
| 128k | Musik dengan kualitas standar, hemat ruang |
| 192k | Keseimbangan terbaik antara kualitas dan ukuran |
| 256k – 320k | Kualitas tinggi untuk musik |

> Butuh kualitas tanpa kehilangan sama sekali? Pilih **FLAC**.

## 🧱 Dibuat Menjadi Aplikasi `.exe` (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AudioConverterPro audio_converter.py
```

Hasilnya ada di folder `dist/`. Supaya FFmpeg ikut tertanam di dalam `.exe`:

```bash
pyinstaller --onefile --windowed --name AudioConverterPro ^
  --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." audio_converter.py
```

Tanpa opsi `--add-binary`, pengguna tetap harus memasang FFmpeg sendiri di `PATH`.

## 🛠️ Pemecahan Masalah

<details>
<summary><b>"FFmpeg tidak ditemukan"</b></summary>

Pastikan FFmpeg terpasang dan bisa dijalankan dengan mengetik `ffmpeg -version` di terminal.
Jika belum ada di `PATH`, klik tombol **Atur FFmpeg** di aplikasi lalu pilih file `ffmpeg` secara manual.
</details>

<details>
<summary><b>Muncul error <code>No module named tkinter</code> (Linux)</b></summary>

```bash
sudo apt install python3-tk
```
</details>

<details>
<summary><b>Drag & drop tidak berfungsi</b></summary>

Fitur ini opsional. Pasang dengan `pip install tkinterdnd2`, lalu jalankan ulang aplikasi.
Tanpa library itu, gunakan tombol **Tambah File** / **Tambah Folder**.
</details>

<details>
<summary><b>Sebuah file berstatus "Gagal ✗"</b></summary>

Klik **Lihat Log** untuk melihat pesan error dari FFmpeg. Penyebab umum: file rusak,
file tidak memiliki aliran audio, atau codec tidak tersedia di build FFmpeg Anda.
</details>

<details>
<summary><b>Durasi tampil "-"</b></summary>

Durasi dibaca memakai `ffprobe`. Pastikan `ffprobe` berada satu folder dengan `ffmpeg`.
Konversi tetap berjalan, hanya persentase per file yang tidak akurat.
</details>

## 🗂️ Struktur Proyek

```
AudConv/
├── audio_converter.py   # Aplikasi utama (GUI + logika konversi)
├── README.md
└── screenshots/         # (opsional) tangkapan layar untuk README
```

## 🧠 Cara Kerja Singkat

- GUI dibangun dengan **Tkinter / ttk** dan tema `clam` yang dikustomisasi.
- Konversi berjalan di **thread terpisah**, sehingga jendela tidak membeku.
- Progress dibaca dari keluaran `ffmpeg -progress pipe:1` dan dihitung terhadap durasi dari `ffprobe`.
- Komunikasi antar-thread memakai `queue.Queue` yang dibaca berkala oleh UI.

## 🗺️ Rencana Pengembangan

- [ ] Potong/trim audio
- [ ] Edit metadata (judul, artis, album, cover)
- [ ] Mode gelap (dark mode)
- [ ] Preset kualitas (Podcast, Musik, Arsip)
- [ ] Konversi paralel untuk beberapa file sekaligus
- [ ] Simpan pengaturan terakhir

## 🤝 Berkontribusi

Kontribusi sangat diterima!

1. Fork repository ini
2. Buat branch fitur: `git checkout -b fitur-baru`
3. Commit perubahan: `git commit -m "Tambah fitur baru"`
4. Push ke branch: `git push origin fitur-baru`
5. Buka Pull Request

Punya ide atau menemukan bug? Silakan buat [Issue](https://github.com/muhdi15/AudConv/issues).

## 📄 Lisensi

Dirilis di bawah lisensi **MIT**. Lihat berkas `LICENSE` untuk detailnya.

## 🙏 Terima Kasih

- [FFmpeg](https://ffmpeg.org/) untuk mesin konversi yang luar biasa
- [tkinterdnd2](https://github.com/Eliav2/tkinterdnd2) untuk dukungan drag & drop

---

<div align="center">

Dibuat dengan ❤️ oleh [@muhdi15](https://github.com/muhdi15)

⭐ Jika proyek ini membantu, jangan lupa beri bintang di GitHub!

</div>
