import os
import json
import threading
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox
from yt_dlp import YoutubeDL
import simpleaudio as sa
import tempfile
import subprocess

# -------------------- Setup -------------------- #
DOWNLOAD_DIR = str(Path.home() / "Downloads")
HISTORY_FILE = Path("history.json")

if not HISTORY_FILE.exists():
    HISTORY_FILE.write_text("[]")

# -------------------- App Class -------------------- #
class AudioDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Audio Downloader")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self.audio_format = StringVar(value="mp3")
        self.current_play = None
        self.temp_wav = None

        self.setup_ui()

    def setup_ui(self):
        tab_control = ttk.Notebook(self.root)
        self.download_tab = Frame(tab_control)
        self.history_tab = Frame(tab_control)

        tab_control.add(self.download_tab, text="Downloader")
        tab_control.add(self.history_tab, text="History")
        tab_control.pack(expand=1, fill="both")

        self.build_downloader_tab()
        self.build_history_tab()

    # -------------------- Downloader Tab -------------------- #
    def build_downloader_tab(self):
        Label(self.download_tab, text="Paste YouTube Video URL:").pack(pady=10)
        self.url_entry = Entry(self.download_tab, width=60)
        self.url_entry.pack(pady=5)

        format_frame = Frame(self.download_tab)
        format_frame.pack(pady=10)
        for fmt in ["mp3", "m4a", "wav"]:
            Radiobutton(format_frame, text=fmt.upper(), variable=self.audio_format, value=fmt).pack(side=LEFT, padx=10)

        Button(self.download_tab, text="Download Audio", command=self.download_audio).pack(pady=10)
        self.status = Label(self.download_tab, text="")
        self.status.pack()

    def download_audio(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Needed", "Please enter a YouTube URL.")
            return

        fmt = self.audio_format.get()
        self.status.config(text="Downloading... Please wait.")

        def run():
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': fmt,
                        'preferredquality': '192',
                    }],
                    'quiet': True,
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get("title", "Unknown")
                    out_file = os.path.join(DOWNLOAD_DIR, f"{title}.{fmt}")
                    self.update_history(title, out_file, fmt)
                    self.status.config(text=f"✅ Downloaded: {title}")
                    self.url_entry.delete(0, END)
                    self.load_history()
            except Exception as e:
                self.status.config(text=f"❌ Failed: {e}")

        threading.Thread(target=run).start()

    # -------------------- History Tab -------------------- #
    def build_history_tab(self):
        self.history_frame = Frame(self.history_tab)
        self.history_frame.pack(fill=BOTH, expand=True)

        self.clear_btn = Button(self.history_tab, text="Clear History", command=self.clear_history)
        self.clear_btn.pack(pady=5)

        self.load_history()

    def load_history(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        try:
            data = json.loads(HISTORY_FILE.read_text())
        except:
            data = []

        for entry in reversed(data):
            frame = Frame(self.history_frame)
            frame.pack(pady=5, fill=X, padx=10)
            Label(frame, text=entry['title'], anchor="w", width=40).pack(side=LEFT)
            Label(frame, text=entry['format']).pack(side=LEFT)
            Button(frame, text="▶ Play", command=lambda p=entry['path']: self.play_audio(p)).pack(side=LEFT, padx=5)
            Button(frame, text="⏹ Stop", command=self.stop_audio).pack(side=LEFT)

    def update_history(self, title, path, fmt):
        try:
            data = json.loads(HISTORY_FILE.read_text())
        except:
            data = []
        data.append({"title": title, "path": path, "format": fmt})
        HISTORY_FILE.write_text(json.dumps(data, indent=2))

    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure?"):
            HISTORY_FILE.write_text("[]")
            self.load_history()

    def play_audio(self, path):
        self.stop_audio()

        # Convert to .wav if not already
        if not path.endswith(".wav"):
            self.temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            cmd = ["ffmpeg", "-y", "-i", path, self.temp_wav.name]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            path = self.temp_wav.name

        self.current_play = sa.WaveObject.from_wave_file(path).play()

    def stop_audio(self):
        if self.current_play:
            self.current_play.stop()
            self.current_play = None
        if self.temp_wav:
            try:
                os.remove(self.temp_wav.name)
            except:
                pass
            self.temp_wav = None

# -------------------- Main -------------------- #
if __name__ == "__main__":
    root = Tk()
    app = AudioDownloaderApp(root)
    root.mainloop()
