"""Simple Tkinter-based interface for yt-dlp downloads.

Run with ``python yt_dlp_gui.py`` and ensure yt-dlp is installed.
"""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from yt_dlp import YoutubeDL


class YTDLPDownloader(tk.Tk):
    """A small GUI wrapper around :mod:`yt_dlp`."""

    def __init__(self) -> None:
        super().__init__()
        self.title("yt-dlp helper")
        self.geometry("640x360")
        self.resizable(True, True)

        self.url_var = tk.StringVar()
        self.format_var = tk.StringVar(value="best")
        self.output_var = tk.StringVar(value=str(Path.cwd() / "downloads"))

        self._create_widgets()
        self._ensure_output_dir()

    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Видео/плейлист URL:").grid(row=0, column=0, sticky="w")
        url_entry = ttk.Entry(main, textvariable=self.url_var)
        url_entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        ttk.Label(main, text="Формат загрузки:").grid(row=2, column=0, sticky="w")
        format_box = ttk.Combobox(
            main,
            textvariable=self.format_var,
            values=("best", "bestvideo+bestaudio", "bestaudio"),
            state="readonly",
        )
        format_box.grid(row=3, column=0, sticky="w")

        ttk.Label(main, text="Папка сохранения:").grid(row=2, column=1, sticky="w")
        output_entry = ttk.Entry(main, textvariable=self.output_var)
        output_entry.grid(row=3, column=1, sticky="ew", padx=(10, 0))
        ttk.Button(main, text="Выбрать…", command=self._choose_dir).grid(row=3, column=2, padx=(10, 0))

        self.download_button = ttk.Button(main, text="Скачать", command=self._start_download)
        self.download_button.grid(row=4, column=0, pady=10)

        self.progress = ttk.Progressbar(main, mode="determinate", maximum=100)
        self.progress.grid(row=4, column=1, columnspan=2, sticky="ew")

        self.log_box = tk.Text(main, height=10, state="disabled")
        self.log_box.grid(row=5, column=0, columnspan=3, pady=(10, 0), sticky="nsew")

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=0)
        main.rowconfigure(5, weight=1)

    # ------------------------------------------------------------------
    def _ensure_output_dir(self) -> None:
        Path(self.output_var.get()).mkdir(parents=True, exist_ok=True)

    def _choose_dir(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.output_var.get())
        if directory:
            self.output_var.set(directory)
            self._ensure_output_dir()

    def _start_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Ошибка", "Введите ссылку на видео или плейлист")
            return

        self.download_button.config(state="disabled")
        self.progress.config(value=0)
        self._log("Начинаю загрузку...")

        thread = threading.Thread(target=self._download, args=(url,), daemon=True)
        thread.start()

    def _download(self, url: str) -> None:
        try:
            output_dir = Path(self.output_var.get())
            self._ensure_output_dir()

            ydl_opts = {
                "outtmpl": str(output_dir / "%(title)s [%(id)s].%(ext)s"),
                "noplaylist": False,
                "progress_hooks": [self._progress_hook],
                "quiet": True,
                "no_warnings": True,
            }

            format_choice = self.format_var.get()
            if format_choice == "bestvideo+bestaudio":
                ydl_opts["format"] = "bestvideo+bestaudio/best"
            elif format_choice == "bestaudio":
                ydl_opts["format"] = "bestaudio/best"
            else:
                ydl_opts["format"] = "best"

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self._log("Загрузка завершена")
        except Exception as exc:  # noqa: BLE001 - show message box
            self._log(f"Ошибка: {exc}")
            messagebox.showerror("Ошибка", str(exc))
        finally:
            self.download_button.config(state="normal")
            self.progress.config(value=0)

    def _progress_hook(self, d: dict) -> None:
        status = d.get("status")
        if status == "downloading":
            percent = d.get("_percent_str", "0.0%").strip()
            if percent.endswith("%"):
                try:
                    value = float(percent[:-1])
                except ValueError:
                    value = 0.0
                self.progress.config(value=value)
            speed = d.get("_speed_str", "?")
            eta = d.get("_eta_str", "?")
            self._log(f"Скачивание: {percent} | {speed} | ETA {eta}", replace_last=True)
        elif status == "finished":
            filename = d.get("filename", "")
            self._log(f"Файл сохранён: {filename}")
            self.progress.config(value=100)

    def _log(self, message: str, replace_last: bool = False) -> None:
        self.log_box.configure(state="normal")
        if replace_last:
            self.log_box.delete("end-2l", "end-1l")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")


def main() -> None:
    app = YTDLPDownloader()
    app.mainloop()


if __name__ == "__main__":
    main()
