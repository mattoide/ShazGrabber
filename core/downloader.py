import os, sys, subprocess

def download_song(artist, title, output_folder, ffmpeg_path, progress_cb=None):
    """
    Scarica una canzone da YouTube come MP3 massima qualità.
    progress_cb(dict) viene chiamato con aggiornamenti di stato.
    Restituisce (success: bool, message: str).
    """
    query = f"ytsearch1:{artist} - {title}"
    out_tmpl = os.path.join(output_folder, "%(title)s.%(ext)s")

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--ffmpeg-location", ffmpeg_path,
        "-f", "bestaudio/best",   # forza sorgente audio migliore
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",   # VBR massima qualità encoder
        "--no-playlist",
        "-o", out_tmpl,
        "--add-metadata",
        "--newline",
        "--no-warnings",
        query,
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            if progress_cb:
                progress_cb({"raw": line, "type": "log"})
            # Parsing progresso: [download]  45.2% of ...
            if line.startswith("[download]") and "%" in line:
                try:
                    pct = float(line.split("%")[0].split()[-1])
                    progress_cb({"type": "progress", "percent": pct, "raw": line})
                except Exception:
                    pass

        proc.wait()
        success = proc.returncode == 0
        return success, "" if success else "yt-dlp returned non-zero exit code"

    except FileNotFoundError:
        return False, "yt-dlp non trovato. Esegui: pip install yt-dlp"
    except Exception as e:
        return False, str(e)
