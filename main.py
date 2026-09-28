import os
import queue
import sys
import threading
import tkinter as tk
from io import BytesIO
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.request import Request, urlopen
from urllib.parse import urlparse

import yt_dlp
from PIL import Image, ImageTk


class YoutubeToMp3App:
    def __init__(self, root):
        self.root = root
        self.root.title("M3.con")
        self.root.geometry("720x520")
        self.root.minsize(620, 460)

        self.events = queue.Queue()
        self.is_downloading = False
        self.preview_request_id = 0
        self.preview_after_id = None
        self.preview_image = None
        self.url_var = tk.StringVar()
        self.destination_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.status_var = tk.StringVar(value="Pronto para baixar")
        self.progress_var = tk.DoubleVar(value=0)
        resource_dir = (
            Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
            / "assets"
            / "icons"
        )
        self.root.iconbitmap(str(resource_dir / "icone.ico"))
        self.history_icons = {
            "success": ImageTk.PhotoImage(
                Image.open(resource_dir / "Double-J-Design-Ravenna-3d-Accept.ico")
                .convert("RGBA").resize((20, 20))
            ),
            "error": ImageTk.PhotoImage(
                Image.open(resource_dir / "Double-J-Design-Ravenna-3d-Delete.ico")
                .convert("RGBA").resize((20, 20))
            ),
        }

        self._build_ui()
        self.url_var.trace_add("write", self._on_url_changed)
        self.root.after(100, self._process_events)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(7, weight=1)

        ttk.Label(main, text="YouTube -> MP3", font=("Segoe UI", 20, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 20)
        )

        ttk.Label(main, text="Link do vídeo:").grid(row=1, column=0, sticky="w", pady=6)
        url_entry = ttk.Entry(main, textvariable=self.url_var)
        url_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(12, 0), pady=6)
        url_entry.focus_set()

        self.preview_frame = ttk.Frame(main)
        self.preview_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 4))
        self.preview_thumbnail = tk.Canvas(
            self.preview_frame,
            width=160,
            height=90,
            background="#e5e5e5",
            highlightthickness=0,
        )
        self.preview_thumbnail.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 12))
        self.preview_image_item = self.preview_thumbnail.create_image(0, 0, anchor="nw")
        self.preview_placeholder_item = self.preview_thumbnail.create_text(
            80, 45, text="Sem informações", fill="#666666", width=145
        )
        self.preview_title_label = ttk.Label(
            self.preview_frame,
            text="Sem informações",
            font=("Segoe UI", 11, "bold"),
            wraplength=470,
            justify="left",
        )
        self.preview_title_label.grid(row=0, column=1, sticky="sw")
        self.preview_status_label = ttk.Label(
            self.preview_frame, text="Prévia do vídeo", foreground="#666666"
        )
        self.preview_status_label.grid(row=1, column=1, sticky="nw", pady=(4, 0))
        self.preview_frame.columnconfigure(1, weight=1)

        self.destination_frame = ttk.Frame(main)
        self.destination_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=6)
        self.destination_frame.columnconfigure(1, weight=1)
        ttk.Label(self.destination_frame, text="Pasta de destino:").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Entry(self.destination_frame, textvariable=self.destination_var).grid(
            row=0, column=1, sticky="ew", padx=(12, 8)
        )
        self.browse_button = ttk.Button(
            self.destination_frame, text="Escolher...", command=self._choose_destination
        )
        self.browse_button.grid(row=0, column=2, sticky="ew")

        self.download_button = ttk.Button(
            main, text="Baixar e converter", command=self._start_download
        )
        self.download_button.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 8))

        self.progress = ttk.Progressbar(
            main, variable=self.progress_var, maximum=100, mode="determinate"
        )
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(4, 4))
        self.progress.grid_remove()
        ttk.Label(main, textvariable=self.status_var).grid(
            row=6, column=0, columnspan=3, sticky="nw", pady=(4, 12)
        )

        history_frame = ttk.LabelFrame(main, text="Histórico", padding=8)
        history_frame.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(4, 0))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        self.history_canvas = tk.Canvas(
            history_frame, height=130, highlightthickness=0, borderwidth=0, background="white"
        )
        self.history_canvas.grid(row=0, column=0, sticky="nsew")
        self.history_content = ttk.Frame(self.history_canvas)
        self.history_window = self.history_canvas.create_window(
            (0, 0), window=self.history_content, anchor="nw"
        )
        self.history_content.columnconfigure(1, weight=1)
        self.history_content.bind("<Configure>", self._update_history_scrollregion)
        self.history_canvas.bind("<Configure>", self._resize_history_content)
        scrollbar = ttk.Scrollbar(
            history_frame, orient="vertical", command=self.history_canvas.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.history_canvas.configure(yscrollcommand=scrollbar.set)

        ttk.Label(
            main,
            text="© Arthur F. dos Santos 2026",
            foreground="#666666",
        ).grid(row=8, column=0, columnspan=3, sticky="w", pady=(12, 0))

    def _on_url_changed(self, *_):
        self.preview_request_id += 1
        request_id = self.preview_request_id
        if self.preview_after_id is not None:
            self.root.after_cancel(self.preview_after_id)
            self.preview_after_id = None

        if self.is_downloading:
            return

        self.progress.grid_remove()
        self.preview_image = None
        self.preview_thumbnail.itemconfigure(self.preview_image_item, image="")
        self.preview_thumbnail.itemconfigure(self.preview_placeholder_item, state="normal")
        self.preview_title_label.configure(text="Sem informações")
        self.preview_status_label.configure(text="Aguardando um link do YouTube.")

        url = self.url_var.get().strip()
        if not url:
            self.status_var.set("Cole um link do YouTube para ver a prévia.")
            return
        if not self._is_youtube_url(url):
            self.status_var.set("O link precisa ser de um vídeo do YouTube.")
            return

        self.status_var.set("Preparando prévia do vídeo...")
        self.preview_after_id = self.root.after(
            700, lambda: self._start_preview_request(url, request_id)
        )

    def _start_preview_request(self, url, request_id):
        self.preview_after_id = None
        if request_id != self.preview_request_id or self.is_downloading:
            return
        self.status_var.set("Buscando informações do vídeo...")
        threading.Thread(
            target=self._load_preview, args=(url, request_id), daemon=True
        ).start()

    def _load_preview(self, url, request_id):
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True}) as downloader:
                info = downloader.extract_info(url, download=False)
            if not info:
                raise ValueError("Nenhum vídeo foi encontrado.")

            title = info.get("title", "Vídeo do YouTube")
            thumbnail_url = info.get("thumbnail")
            thumbnail = None
            if thumbnail_url:
                try:
                    request = Request(thumbnail_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urlopen(request, timeout=15) as response:
                        image = Image.open(BytesIO(response.read())).convert("RGB")
                    image.thumbnail((160, 90), Image.Resampling.LANCZOS)
                    thumbnail = Image.new("RGB", (160, 90), "#e5e5e5")
                    thumbnail.paste(
                        image, ((160 - image.width) // 2, (90 - image.height) // 2)
                    )
                except Exception:
                    thumbnail = None
            self.events.put(("preview_success", request_id, title, thumbnail))
        except Exception as error:
            self.events.put(("preview_error", request_id, self._translate_error(error)))

    def _choose_destination(self):
        selected = filedialog.askdirectory(
            title="Escolha a pasta de destino", initialdir=self.destination_var.get()
        )
        if selected:
            self.destination_var.set(selected)

    def _start_download(self):
        if self.is_downloading:
            return

        url = self.url_var.get().strip()
        destination = Path(self.destination_var.get().strip()).expanduser()
        if not self._is_youtube_url(url):
            error_message = "Erro: link inválido. Cole um link válido do YouTube."
            self._add_history_item("error", error_message)
            messagebox.showwarning("Link inválido", "Cole um link válido do YouTube.")
            return
        if not destination.is_dir():
            error_message = "Erro: a pasta de destino não existe. Escolha uma pasta válida."
            self._add_history_item("error", error_message)
            messagebox.showwarning("Pasta inválida", "Escolha uma pasta de destino existente.")
            return

        self.is_downloading = True
        self.download_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.progress_var.set(0)
        self.progress.grid()
        self.status_var.set("Iniciando download...")
        threading.Thread(
            target=self._download, args=(url, destination), daemon=True
        ).start()

    def _download(self, url, destination):
        options = {
            "format": "bestaudio/best",
            "outtmpl": str(destination / "%(title)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "progress_hooks": [self._progress_hook],
        }
        ffmpeg_path = self._find_portable_ffmpeg()
        if ffmpeg_path:
            options["ffmpeg_location"] = str(ffmpeg_path)
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(url, download=True)
            title = info.get("title", "Áudio")
            self.events.put(("success", f"Concluído: {title}"))
        except Exception as error:
            self.events.put(("error", self._translate_error(error)))

    @staticmethod
    def _find_portable_ffmpeg():
        if getattr(sys, "frozen", False):
            app_directory = Path(sys.executable).resolve().parent
        else:
            app_directory = Path(__file__).resolve().parent
        ffmpeg_path = app_directory / "ffmpeg" / "bin" / "ffmpeg.exe"
        return ffmpeg_path if ffmpeg_path.is_file() else None

    def _progress_hook(self, data):
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes", 0)
            if total:
                percent = downloaded * 100 / total
                self.events.put(("progress", percent, f"Baixando... {percent:.1f}%"))
        elif data.get("status") == "finished":
            self.events.put(("progress", 100, "Convertendo para MP3..."))

    def _process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "progress":
                    self.progress_var.set(event[1])
                    self.status_var.set(event[2])
                elif kind == "preview_success":
                    if event[1] != self.preview_request_id:
                        continue
                    self.preview_image = (
                        ImageTk.PhotoImage(event[3]) if event[3] is not None else None
                    )
                    if self.preview_image:
                        self.preview_thumbnail.itemconfigure(
                            self.preview_image_item, image=self.preview_image
                        )
                        self.preview_thumbnail.itemconfigure(
                            self.preview_placeholder_item, state="hidden"
                        )
                    else:
                        self.preview_thumbnail.itemconfigure(
                            self.preview_placeholder_item,
                            text="Miniatura indisponível",
                            state="normal",
                        )
                    self.preview_title_label.configure(text=event[2])
                    self.progress.grid_remove()
                    self.status_var.set("Prévia carregada. Escolha a pasta e baixe.")
                elif kind == "preview_error":
                    if event[1] != self.preview_request_id:
                        continue
                    self.preview_title_label.configure(text="Sem informações")
                    self.preview_status_label.configure(text=event[2])
                    self.status_var.set(event[2])
                    self._add_history_item("error", f"Erro: {event[2]}")
                elif kind == "success":
                    self._finish_download()
                    self.status_var.set(event[1])
                    self._add_history_item("success", event[1])
                    messagebox.showinfo("Download concluído", event[1])
                elif kind == "error":
                    self._finish_download()
                    self.status_var.set("Não foi possível concluir o download.")
                    self._add_history_item("error", f"Erro: {event[1]}")
                    messagebox.showerror("Falha no download", event[1])
        except queue.Empty:
            pass
        self.root.after(100, self._process_events)

    def _add_history_item(self, kind, text):
        existing_rows = self.history_content.winfo_children()
        for existing_row in existing_rows:
            current_row = int(existing_row.grid_info()["row"])
            existing_row.grid_configure(row=current_row + 1)
        row = ttk.Frame(self.history_content)
        row.grid(row=0, column=0, sticky="ew", padx=(2, 4), pady=1)
        ttk.Label(row, image=self.history_icons[kind]).grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Label(row, text=text, anchor="w").grid(
            row=0, column=1, sticky="ew"
        )
        self.history_canvas.yview_moveto(0)

    def _update_history_scrollregion(self, _event):
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def _resize_history_content(self, event):
        self.history_canvas.itemconfigure(self.history_window, width=event.width)

    @staticmethod
    def _translate_error(error):
        message = str(error).casefold()
        if "this video is unavailable" in message or "video is unavailable" in message:
            return "Este vídeo não está disponível. Ele pode ter sido removido, estar privado ou bloqueado."
        if "private video" in message or "this is a private video" in message:
            return "Este vídeo é privado e não pode ser acessado."
        if "sign in to confirm" in message or "confirm you're not a bot" in message:
            return "O YouTube exige uma verificação para acessar este vídeo. Tente novamente mais tarde."
        if "http error 429" in message or "too many requests" in message:
            return "O YouTube limitou temporariamente os pedidos. Aguarde e tente novamente."
        if "http error 403" in message:
            return "O acesso ao vídeo foi recusado. Verifique se ele está disponível e tente novamente."
        if "ffmpeg" in message:
            return "O FFmpeg não foi encontrado ou não conseguiu converter o áudio. Verifique a instalação."
        if "unsupported url" in message:
            return "O link não é compatível. Confira se ele é de um vídeo do YouTube."
        return "Não foi possível baixar ou converter o vídeo. Verifique o link e a conexão com a internet e tente novamente."

    def _finish_download(self):
        self.is_downloading = False
        self.download_button.configure(state="normal")
        self.browse_button.configure(state="normal")

    @staticmethod
    def _is_youtube_url(value):
        try:
            parsed = urlparse(value)
            return parsed.scheme in {"http", "https"} and parsed.netloc.lower() in {
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
                "youtu.be",
                "www.youtu.be",
            }
        except ValueError:
            return False


def main():
    root = tk.Tk()
    YoutubeToMp3App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
