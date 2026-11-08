#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Converter Pro
===================
Aplikasi konverter audio lengkap dengan GUI (Tkinter) dan mesin FFmpeg.

Fitur:
  - Konversi banyak file sekaligus (batch)
  - Format: MP3, WAV, FLAC, AAC/M4A, OGG, OPUS, WMA, AIFF
  - Bisa ekstrak audio dari video (MP4, MKV, AVI, dll)
  - Pengaturan bitrate, sample rate, channel, normalisasi volume
  - Progress bar per file dan keseluruhan, tombol batal
  - Drag & drop (opsional, jika tkinterdnd2 terpasang)
  - Deteksi FFmpeg otomatis atau pilih manual

Kebutuhan:
  - Python 3.8+
  - FFmpeg (https://ffmpeg.org/download.html) ada di PATH,
    atau letakkan ffmpeg(.exe) di folder yang sama dengan skrip ini.
  - Opsional: pip install tkinterdnd2   (untuk drag & drop)
"""

import os
import sys
import shutil
import queue
import platform
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES  # type: ignore
    BaseTk = TkinterDnD.Tk
    HAS_DND = True
except Exception:
    BaseTk = tk.Tk
    HAS_DND = False

APP_TITLE = "Audio Converter Pro"
IS_WINDOWS = platform.system() == "Windows"

# ---------------------------------------------------------------- Konfigurasi
FORMATS = {
    "MP3":       {"ext": ".mp3",  "codec": "libmp3lame", "lossy": True},
    "WAV":       {"ext": ".wav",  "codec": "pcm_s16le",  "lossy": False},
    "FLAC":      {"ext": ".flac", "codec": "flac",       "lossy": False},
    "AAC (M4A)": {"ext": ".m4a",  "codec": "aac",        "lossy": True},
    "OGG":       {"ext": ".ogg",  "codec": "libvorbis",  "lossy": True},
    "OPUS":      {"ext": ".opus", "codec": "libopus",    "lossy": True},
    "WMA":       {"ext": ".wma",  "codec": "wmav2",      "lossy": True},
    "AIFF":      {"ext": ".aiff", "codec": "pcm_s16be",  "lossy": False},
}

INPUT_EXT = {
    ".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".opus", ".wma", ".aiff",
    ".aif", ".amr", ".ac3", ".mka", ".ape", ".wv", ".webm",
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".3gp",
}

BITRATES = ["64k", "96k", "128k", "160k", "192k", "256k", "320k"]
SAMPLE_RATES = ["Asli", "8000", "16000", "22050", "32000", "44100", "48000", "96000"]
CHANNELS = ["Asli", "Mono", "Stereo"]

# Warna tema
C_BG = "#f4f6fb"
C_CARD = "#ffffff"
C_PRIMARY = "#4f46e5"
C_PRIMARY_DARK = "#4338ca"
C_DANGER = "#dc2626"
C_TEXT = "#1f2937"
C_MUTED = "#6b7280"
C_BORDER = "#e5e7eb"
C_OK = "#16a34a"


# ---------------------------------------------------------------- Utilitas
def find_tool(name):
    """Cari ffmpeg/ffprobe: folder skrip, subfolder ffmpeg, lalu PATH."""
    exe = name + (".exe" if IS_WINDOWS else "")
    here = Path(__file__).resolve().parent
    for p in (here / exe, here / "ffmpeg" / exe, here / "ffmpeg" / "bin" / exe):
        if p.is_file():
            return str(p)
    return shutil.which(name)


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def human_time(sec):
    if sec is None:
        return "-"
    sec = int(sec)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    i = 1
    while True:
        cand = path.with_name(f"{path.stem} ({i}){path.suffix}")
        if not cand.exists():
            return cand
        i += 1


def open_folder(path):
    try:
        if IS_WINDOWS:
            os.startfile(path)  # type: ignore
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def popen_kwargs():
    kw = {}
    if IS_WINDOWS:
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW  # sembunyikan console
    return kw


# ---------------------------------------------------------------- Frame scrollable
class ScrollableFrame(ttk.Frame):
    """Frame yang bisa di-scroll vertikal (scrollbar + mouse wheel).
    Letakkan widget di dalam `self.content`."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=C_BG, highlightthickness=0, borderwidth=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel hanya aktif saat kursor berada di area ini
        self.bind("<Enter>", self._bind_wheel)
        self.bind("<Leave>", self._unbind_wheel)

    def _on_content_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._toggle_scrollbar()

    def _on_canvas_configure(self, event):
        # Lebar konten mengikuti lebar canvas; tinggi minimal = tinggi canvas
        self.canvas.itemconfigure(self._win, width=event.width)
        self._toggle_scrollbar()

    def _needs_scroll(self):
        return self.content.winfo_reqheight() > self.canvas.winfo_height()

    def _toggle_scrollbar(self):
        if self._needs_scroll():
            if not self.vsb.winfo_ismapped():
                self.vsb.pack(side="right", fill="y", before=self.canvas)
        else:
            if self.vsb.winfo_ismapped():
                self.vsb.pack_forget()
            self.canvas.yview_moveto(0)

    def _bind_wheel(self, _event=None):
        self.bind_all("<MouseWheel>", self._on_wheel)
        self.bind_all("<Button-4>", self._on_wheel)   # Linux scroll up
        self.bind_all("<Button-5>", self._on_wheel)   # Linux scroll down

    def _unbind_wheel(self, _event=None):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def _on_wheel(self, event):
        if not self._needs_scroll():
            return
        # Jika kursor di atas tabel file, biarkan tabel yang scroll sendiri
        try:
            w = self.winfo_containing(event.x_root, event.y_root)
        except (KeyError, tk.TclError):
            w = None
        if isinstance(w, ttk.Treeview):
            return

        if event.num == 4:
            step = -1
        elif event.num == 5:
            step = 1
        elif platform.system() == "Darwin":
            step = -int(event.delta)
        else:
            step = -int(event.delta / 120)
        if step:
            self.canvas.yview_scroll(step, "units")


# ---------------------------------------------------------------- Aplikasi
class AudioConverterApp(BaseTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("920x720")
        self.minsize(640, 400)
        self.configure(bg=C_BG)

        self.ffmpeg = find_tool("ffmpeg")
        self.ffprobe = find_tool("ffprobe")

        self.items = {}          # iid -> {"path": Path, "duration": float|None}
        self.paths = set()
        self.counter = 0
        self.msg_q = queue.Queue()
        self.cancel_event = threading.Event()
        self.proc = None
        self.worker = None
        self.converting = False

        self._setup_style()
        self._build_ui()
        self._refresh_quality_state()
        self._check_ffmpeg(initial=True)
        self.after(100, self._poll_queue)

    # ------------------------------------------------------------ Style
    def _setup_style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        default_font = ("Segoe UI", 10) if IS_WINDOWS else ("Helvetica", 11)
        self.option_add("*Font", default_font)

        s.configure(".", background=C_BG, foreground=C_TEXT)
        s.configure("TFrame", background=C_BG)
        s.configure("Card.TFrame", background=C_CARD)
        s.configure("TLabel", background=C_BG, foreground=C_TEXT)
        s.configure("Card.TLabel", background=C_CARD, foreground=C_TEXT)
        s.configure("Muted.TLabel", background=C_BG, foreground=C_MUTED)
        s.configure("CardMuted.TLabel", background=C_CARD, foreground=C_MUTED)
        s.configure("Title.TLabel", background=C_BG, foreground=C_TEXT,
                    font=(default_font[0], 20, "bold"))
        s.configure("Section.TLabel", background=C_CARD, foreground=C_TEXT,
                    font=(default_font[0], 11, "bold"))

        s.configure("TButton", padding=(12, 7), relief="flat", background="#e5e7eb",
                    foreground=C_TEXT, borderwidth=0)
        s.map("TButton", background=[("active", "#d1d5db"), ("disabled", "#f3f4f6")])

        s.configure("Primary.TButton", background=C_PRIMARY, foreground="white",
                    font=(default_font[0], 11, "bold"), padding=(20, 10))
        s.map("Primary.TButton",
              background=[("active", C_PRIMARY_DARK), ("disabled", "#a5b4fc")],
              foreground=[("disabled", "white")])

        s.configure("Danger.TButton", background=C_DANGER, foreground="white",
                    font=(default_font[0], 11, "bold"), padding=(20, 10))
        s.map("Danger.TButton",
              background=[("active", "#b91c1c"), ("disabled", "#fca5a5")],
              foreground=[("disabled", "white")])

        s.configure("TCheckbutton", background=C_CARD, foreground=C_TEXT)
        s.configure("TRadiobutton", background=C_CARD, foreground=C_TEXT)
        s.configure("TCombobox", padding=5, fieldbackground="white")
        s.configure("TEntry", padding=6)

        s.configure("Treeview", background="white", fieldbackground="white",
                    foreground=C_TEXT, rowheight=28, borderwidth=0)
        s.configure("Treeview.Heading", background="#eef0f6", foreground=C_TEXT,
                    font=(default_font[0], 10, "bold"), padding=6, relief="flat")
        s.map("Treeview", background=[("selected", "#e0e7ff")],
              foreground=[("selected", C_TEXT)])

        s.configure("Horizontal.TProgressbar", troughcolor="#e5e7eb",
                    background=C_PRIMARY, thickness=14, borderwidth=0)

    # ------------------------------------------------------------ UI
    def _card(self, parent, title=None):
        outer = tk.Frame(parent, bg=C_CARD, highlightbackground=C_BORDER,
                         highlightthickness=1)
        inner = ttk.Frame(outer, style="Card.TFrame", padding=14)
        inner.pack(fill="both", expand=True)
        if title:
            ttk.Label(inner, text=title, style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        return outer, inner

    def _build_ui(self):
        # Seluruh isi jendela ditaruh di dalam area yang bisa di-scroll
        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True)
        root = ttk.Frame(self.scroll.content, padding=(18, 14))
        root.pack(fill="both", expand=True)

        # Cegah combobox berubah nilai saat mouse wheel dipakai untuk scroll halaman
        self.unbind_class("TCombobox", "<MouseWheel>")
        self.unbind_class("TCombobox", "<Button-4>")
        self.unbind_class("TCombobox", "<Button-5>")

        # Header
        head = ttk.Frame(root)
        head.pack(fill="x")
        ttk.Label(head, text="🎵 " + APP_TITLE, style="Title.TLabel").pack(side="left")
        self.ffmpeg_label = ttk.Label(head, text="", style="Muted.TLabel")
        self.ffmpeg_label.pack(side="right")
        ttk.Button(head, text="Atur FFmpeg", command=self._choose_ffmpeg).pack(side="right", padx=8)

        hint = "Tambahkan file audio/video, pilih format tujuan, lalu klik Konversi."
        if HAS_DND:
            hint += "  Anda juga bisa drag & drop file ke daftar."
        ttk.Label(root, text=hint, style="Muted.TLabel").pack(anchor="w", pady=(0, 10))

        # ---- Daftar file
        card1, c1 = self._card(root, "File yang akan dikonversi")
        card1.pack(fill="both", expand=True)

        bar = ttk.Frame(c1, style="Card.TFrame")
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="＋ Tambah File", command=self.add_files).pack(side="left")
        ttk.Button(bar, text="📁 Tambah Folder", command=self.add_folder).pack(side="left", padx=6)
        ttk.Button(bar, text="Hapus Terpilih", command=self.remove_selected).pack(side="left")
        ttk.Button(bar, text="Kosongkan", command=self.clear_all).pack(side="left", padx=6)
        self.count_label = ttk.Label(bar, text="0 file", style="CardMuted.TLabel")
        self.count_label.pack(side="right")

        tree_wrap = ttk.Frame(c1, style="Card.TFrame")
        tree_wrap.pack(fill="both", expand=True)
        cols = ("nama", "tipe", "durasi", "ukuran", "status")
        self.tree = ttk.Treeview(tree_wrap, columns=cols, show="headings", selectmode="extended", height=8)
        for col, text, w, anc in (
            ("nama", "Nama File", 340, "w"),
            ("tipe", "Tipe", 60, "center"),
            ("durasi", "Durasi", 70, "center"),
            ("ukuran", "Ukuran", 80, "center"),
            ("status", "Status", 150, "center"),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor=anc, stretch=(col == "nama"))
        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.tag_configure("ok", foreground=C_OK)
        self.tree.tag_configure("err", foreground=C_DANGER)
        self.tree.bind("<Delete>", lambda e: self.remove_selected())

        if HAS_DND:
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind("<<Drop>>", self._on_drop)

        # ---- Pengaturan
        card2, c2 = self._card(root, "Pengaturan konversi")
        card2.pack(fill="x", pady=10)

        grid = ttk.Frame(c2, style="Card.TFrame")
        grid.pack(fill="x")
        for i in range(4):
            grid.columnconfigure(i, weight=1, uniform="g")

        self.var_format = tk.StringVar(value="MP3")
        self.var_bitrate = tk.StringVar(value="192k")
        self.var_sr = tk.StringVar(value="Asli")
        self.var_ch = tk.StringVar(value="Asli")

        def field(col, label, var, values, cmd=None):
            f = ttk.Frame(grid, style="Card.TFrame")
            f.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0))
            ttk.Label(f, text=label, style="CardMuted.TLabel").pack(anchor="w")
            cb = ttk.Combobox(f, textvariable=var, values=values, state="readonly")
            cb.pack(fill="x", pady=(2, 0))
            if cmd:
                cb.bind("<<ComboboxSelected>>", cmd)
            return cb

        field(0, "Format tujuan", self.var_format, list(FORMATS.keys()),
              lambda e: self._refresh_quality_state())
        self.cb_bitrate = field(1, "Kualitas (bitrate)", self.var_bitrate, BITRATES)
        field(2, "Sample rate (Hz)", self.var_sr, SAMPLE_RATES)
        field(3, "Channel", self.var_ch, CHANNELS)

        opts = ttk.Frame(c2, style="Card.TFrame")
        opts.pack(fill="x", pady=(10, 0))
        self.var_norm = tk.BooleanVar(value=False)
        self.var_overwrite = tk.BooleanVar(value=False)
        self.var_open = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Normalisasi volume", variable=self.var_norm).pack(side="left")
        ttk.Checkbutton(opts, text="Timpa file yang sudah ada", variable=self.var_overwrite).pack(side="left", padx=16)
        ttk.Checkbutton(opts, text="Buka folder setelah selesai", variable=self.var_open).pack(side="left")

        self.quality_note = ttk.Label(c2, text="", style="CardMuted.TLabel")
        self.quality_note.pack(anchor="w", pady=(6, 0))

        # ---- Output
        card3, c3 = self._card(root, "Folder tujuan")
        card3.pack(fill="x")
        self.var_outmode = tk.StringVar(value="same")
        self.var_outdir = tk.StringVar(value=str(Path.home() / "Music" / "Converted"))
        r1 = ttk.Frame(c3, style="Card.TFrame")
        r1.pack(fill="x")
        ttk.Radiobutton(r1, text="Sama dengan file asli", variable=self.var_outmode,
                        value="same", command=self._refresh_out_state).pack(side="left")
        ttk.Radiobutton(r1, text="Folder lain:", variable=self.var_outmode,
                        value="custom", command=self._refresh_out_state).pack(side="left", padx=(16, 6))
        self.ent_out = ttk.Entry(r1, textvariable=self.var_outdir)
        self.ent_out.pack(side="left", fill="x", expand=True)
        self.btn_out = ttk.Button(r1, text="Pilih…", command=self.choose_outdir)
        self.btn_out.pack(side="left", padx=(6, 0))
        self._refresh_out_state()

        # ---- Progress & aksi
        bottom = ttk.Frame(root)
        bottom.pack(fill="x", pady=(12, 0))

        pf = ttk.Frame(bottom)
        pf.pack(fill="x")
        self.progress = ttk.Progressbar(pf, mode="determinate", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True)
        self.pct_label = ttk.Label(pf, text="0%", width=6, anchor="e")
        self.pct_label.pack(side="left", padx=(8, 0))

        self.status_label = ttk.Label(bottom, text="Siap.", style="Muted.TLabel")
        self.status_label.pack(anchor="w", pady=(4, 8))

        btns = ttk.Frame(bottom)
        btns.pack(fill="x")
        self.btn_convert = ttk.Button(btns, text="▶  Konversi Sekarang",
                                      style="Primary.TButton", command=self.start_conversion)
        self.btn_convert.pack(side="left")
        self.btn_cancel = ttk.Button(btns, text="■  Batal", style="Danger.TButton",
                                     command=self.cancel_conversion, state="disabled")
        self.btn_cancel.pack(side="left", padx=8)
        ttk.Button(btns, text="Lihat Log", command=self.show_log).pack(side="right")

        self.log_lines = []

    # ------------------------------------------------------------ Status UI
    def _refresh_quality_state(self):
        fmt = FORMATS[self.var_format.get()]
        if fmt["lossy"]:
            self.cb_bitrate.configure(state="readonly")
            self.quality_note.configure(text="Format lossy: semakin tinggi bitrate, semakin bagus kualitasnya (dan file lebih besar).")
        else:
            self.cb_bitrate.configure(state="disabled")
            self.quality_note.configure(text="Format lossless: tidak memakai bitrate, kualitas audio dipertahankan penuh.")

    def _refresh_out_state(self):
        st = "normal" if self.var_outmode.get() == "custom" else "disabled"
        self.ent_out.configure(state=st)
        self.btn_out.configure(state=st)

    def _check_ffmpeg(self, initial=False):
        if self.ffmpeg:
            self.ffmpeg_label.configure(text="FFmpeg ✓ terdeteksi", foreground=C_OK)
        else:
            self.ffmpeg_label.configure(text="FFmpeg ✗ tidak ditemukan", foreground=C_DANGER)
            if initial:
                self.after(300, lambda: messagebox.showwarning(
                    "FFmpeg tidak ditemukan",
                    "Aplikasi membutuhkan FFmpeg untuk mengonversi audio.\n\n"
                    "• Windows: unduh dari ffmpeg.org lalu tambahkan ke PATH, atau klik "
                    "'Atur FFmpeg' dan pilih ffmpeg.exe.\n"
                    "• macOS: brew install ffmpeg\n"
                    "• Linux: sudo apt install ffmpeg"))

    def _choose_ffmpeg(self):
        path = filedialog.askopenfilename(title="Pilih ffmpeg",
                                          filetypes=[("FFmpeg", "ffmpeg*"), ("Semua file", "*.*")])
        if path:
            self.ffmpeg = path
            probe = Path(path).with_name("ffprobe" + (".exe" if IS_WINDOWS else ""))
            self.ffprobe = str(probe) if probe.is_file() else find_tool("ffprobe")
            self._check_ffmpeg()

    def _set_status(self, text):
        self.status_label.configure(text=text)

    # ------------------------------------------------------------ Daftar file
    def add_files(self):
        exts = " ".join("*" + e for e in sorted(INPUT_EXT))
        files = filedialog.askopenfilenames(
            title="Pilih file audio / video",
            filetypes=[("Audio & Video", exts), ("Semua file", "*.*")])
        self._add_paths(files)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Pilih folder berisi audio")
        if not folder:
            return
        found = [str(p) for p in Path(folder).rglob("*") if p.suffix.lower() in INPUT_EXT]
        if not found:
            messagebox.showinfo("Folder kosong", "Tidak ada file audio/video di folder tersebut.")
            return
        self._add_paths(found)

    def _on_drop(self, event):
        paths = self.tk.splitlist(event.data)
        expanded = []
        for p in paths:
            pp = Path(p)
            if pp.is_dir():
                expanded += [str(x) for x in pp.rglob("*") if x.suffix.lower() in INPUT_EXT]
            else:
                expanded.append(p)
        self._add_paths(expanded)

    def _add_paths(self, paths):
        new_items = []
        for p in paths:
            path = Path(p)
            if not path.is_file() or str(path) in self.paths:
                continue
            self.counter += 1
            iid = str(self.counter)
            try:
                size = human_size(path.stat().st_size)
            except OSError:
                size = "-"
            self.tree.insert("", "end", iid=iid,
                             values=(path.name, path.suffix.lstrip(".").upper(), "…", size, "Menunggu"))
            self.items[iid] = {"path": path, "duration": None}
            self.paths.add(str(path))
            new_items.append(iid)
        self._update_count()
        if new_items:
            threading.Thread(target=self._probe_worker, args=(new_items,), daemon=True).start()

    def _probe_worker(self, iids):
        for iid in iids:
            dur = self._probe_duration(self.items[iid]["path"]) if iid in self.items else None
            self.msg_q.put(("probe", iid, dur))

    def _probe_duration(self, path):
        if not self.ffprobe:
            return None
        try:
            out = subprocess.run(
                [self.ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", str(path)],
                capture_output=True, text=True, timeout=30, **popen_kwargs())
            return float(out.stdout.strip())
        except Exception:
            return None

    def remove_selected(self):
        if self.converting:
            return
        for iid in self.tree.selection():
            info = self.items.pop(iid, None)
            if info:
                self.paths.discard(str(info["path"]))
            self.tree.delete(iid)
        self._update_count()

    def clear_all(self):
        if self.converting:
            return
        self.tree.delete(*self.tree.get_children())
        self.items.clear()
        self.paths.clear()
        self._update_count()
        self._set_progress(0)
        self._set_status("Siap.")

    def _update_count(self):
        self.count_label.configure(text=f"{len(self.items)} file")

    def choose_outdir(self):
        d = filedialog.askdirectory(title="Pilih folder tujuan")
        if d:
            self.var_outdir.set(d)

    # ------------------------------------------------------------ Konversi
    def start_conversion(self):
        if self.converting:
            return
        if not self.ffmpeg:
            messagebox.showerror("FFmpeg tidak ada", "Klik 'Atur FFmpeg' untuk memilih lokasi ffmpeg.")
            return
        if not self.items:
            messagebox.showinfo("Belum ada file", "Tambahkan minimal satu file terlebih dahulu.")
            return

        outdir = None
        if self.var_outmode.get() == "custom":
            outdir = Path(self.var_outdir.get().strip())
            try:
                outdir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Folder tujuan tidak valid", str(e))
                return

        settings = {
            "fmt": self.var_format.get(),
            "bitrate": self.var_bitrate.get(),
            "sr": self.var_sr.get(),
            "ch": self.var_ch.get(),
            "norm": self.var_norm.get(),
            "overwrite": self.var_overwrite.get(),
            "outdir": outdir,
        }
        jobs = [(iid, self.items[iid]["path"], self.items[iid]["duration"])
                for iid in self.tree.get_children()]

        for iid, _, _ in jobs:
            self.tree.set(iid, "status", "Menunggu")
            self.tree.item(iid, tags=())

        self.cancel_event.clear()
        self.converting = True
        self.log_lines.clear()
        self._set_progress(0)
        self.btn_convert.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self._set_status("Memulai konversi…")

        self.worker = threading.Thread(target=self._convert_worker, args=(jobs, settings), daemon=True)
        self.worker.start()

    def cancel_conversion(self):
        if not self.converting:
            return
        self.cancel_event.set()
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self._set_status("Membatalkan…")

    def _build_cmd(self, src, dst, s):
        f = FORMATS[s["fmt"]]
        cmd = [self.ffmpeg, "-hide_banner", "-y", "-i", str(src),
               "-vn", "-map", "0:a:0", "-map_metadata", "0", "-c:a", f["codec"]]
        if f["lossy"]:
            cmd += ["-b:a", s["bitrate"]]
        if s["sr"] != "Asli":
            cmd += ["-ar", s["sr"]]
        if s["ch"] == "Mono":
            cmd += ["-ac", "1"]
        elif s["ch"] == "Stereo":
            cmd += ["-ac", "2"]
        if s["norm"]:
            cmd += ["-af", "loudnorm"]
        cmd += ["-progress", "pipe:1", "-nostats", str(dst)]
        return cmd

    def _convert_worker(self, jobs, s):
        total = len(jobs)
        ok = fail = 0
        out_dirs = set()
        ext = FORMATS[s["fmt"]]["ext"]

        for idx, (iid, src, dur) in enumerate(jobs):
            if self.cancel_event.is_set():
                self.msg_q.put(("status", iid, "Dibatalkan", None))
                continue

            folder = s["outdir"] or src.parent
            dst = folder / (src.stem + ext)
            if dst.resolve() == src.resolve():
                dst = unique_path(folder / (src.stem + "_converted" + ext))
            elif not s["overwrite"]:
                dst = unique_path(dst)
            out_dirs.add(str(folder))

            self.msg_q.put(("status", iid, "Memproses 0%", None))
            self.msg_q.put(("info", f"[{idx + 1}/{total}] {src.name}  →  {dst.name}"))
            self.msg_q.put(("overall", (idx) / total))

            cmd = self._build_cmd(src, dst, s)
            self.msg_q.put(("log", "$ " + " ".join(f'"{c}"' if " " in c else c for c in cmd)))
            tail = []
            try:
                self.proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", **popen_kwargs())
                for line in self.proc.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith(("out_time_us=", "out_time_ms=")):
                        try:
                            us = int(line.split("=", 1)[1])
                            if dur and dur > 0 and us >= 0:
                                frac = min(us / 1_000_000 / dur, 1.0)
                                self.msg_q.put(("status", iid, f"Memproses {int(frac * 100)}%", None))
                                self.msg_q.put(("overall", (idx + frac) / total))
                        except ValueError:
                            pass
                    elif "=" in line and line.split("=", 1)[0].replace("_", "").isalnum():
                        continue  # baris progress lain (bitrate=, speed=, dll)
                    else:
                        tail.append(line)
                        tail = tail[-15:]
                self.proc.wait()
                code = self.proc.returncode
            except Exception as e:
                code = -1
                tail.append(str(e))

            if self.cancel_event.is_set():
                try:
                    if dst.exists():
                        dst.unlink()
                except Exception:
                    pass
                self.msg_q.put(("status", iid, "Dibatalkan", "err"))
            elif code == 0:
                ok += 1
                self.msg_q.put(("status", iid, "Selesai ✓", "ok"))
            else:
                fail += 1
                self.msg_q.put(("status", iid, "Gagal ✗", "err"))
                self.msg_q.put(("log", "\n".join(tail)))
                try:
                    if dst.exists():
                        dst.unlink()
                except Exception:
                    pass

        self.proc = None
        self.msg_q.put(("done", ok, fail, total, sorted(out_dirs), self.cancel_event.is_set()))

    # ------------------------------------------------------------ Antrian pesan
    def _poll_queue(self):
        try:
            while True:
                msg = self.msg_q.get_nowait()
                kind = msg[0]
                if kind == "probe":
                    _, iid, dur = msg
                    if iid in self.items:
                        self.items[iid]["duration"] = dur
                        self.tree.set(iid, "durasi", human_time(dur))
                elif kind == "status":
                    _, iid, text, tag = msg
                    if self.tree.exists(iid):
                        self.tree.set(iid, "status", text)
                        if tag:
                            self.tree.item(iid, tags=(tag,))
                elif kind == "overall":
                    self._set_progress(msg[1] * 100)
                elif kind == "info":
                    self._set_status(msg[1])
                    self.log_lines.append(msg[1])
                elif kind == "log":
                    self.log_lines.append(msg[1])
                elif kind == "done":
                    self._on_done(*msg[1:])
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _set_progress(self, pct):
        self.progress["value"] = pct
        self.pct_label.configure(text=f"{int(pct)}%")

    def _on_done(self, ok, fail, total, out_dirs, cancelled):
        self.converting = False
        self.btn_convert.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        if cancelled:
            self._set_status(f"Dibatalkan. Berhasil: {ok}, gagal: {fail}.")
            return
        self._set_progress(100)
        self._set_status(f"Selesai! Berhasil: {ok}, gagal: {fail} dari {total} file.")
        if fail:
            messagebox.showwarning("Selesai dengan masalah",
                                   f"{ok} berhasil, {fail} gagal.\nKlik 'Lihat Log' untuk detail.")
        else:
            messagebox.showinfo("Selesai", f"Semua {ok} file berhasil dikonversi 🎉")
        if self.var_open.get() and ok and out_dirs:
            open_folder(out_dirs[0])

    # ------------------------------------------------------------ Log
    def show_log(self):
        win = tk.Toplevel(self)
        win.title("Log konversi")
        win.geometry("760x420")
        txt = tk.Text(win, wrap="word", font=("Consolas" if IS_WINDOWS else "Courier", 9))
        sb = ttk.Scrollbar(win, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", "\n".join(self.log_lines) or "(log kosong)")
        txt.configure(state="disabled")

    # ------------------------------------------------------------ Tutup
    def destroy(self):
        if self.converting:
            if not messagebox.askyesno("Keluar?", "Konversi sedang berjalan. Yakin ingin keluar?"):
                return
            self.cancel_event.set()
            if self.proc and self.proc.poll() is None:
                try:
                    self.proc.terminate()
                except Exception:
                    pass
        super().destroy()


if __name__ == "__main__":
    app = AudioConverterApp()
    app.mainloop()
