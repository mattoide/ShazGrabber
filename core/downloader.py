import os, re, sys, subprocess


def _classify_error(last_error):
    """Traduce l'ultima riga di ERROR di yt-dlp in un messaggio leggibile."""
    low = last_error.lower()
    if "confirm your age" in low:
        return "Video con restrizione d'età — serve un file cookies YouTube (vedi config.COOKIES_FILE)"
    if "confirm you" in low and "bot" in low:
        return "YouTube chiede verifica anti-bot — serve un file cookies"
    if "not available" in low or "video unavailable" in low:
        return "Nessun risultato disponibile su YouTube"
    if "private video" in low:
        return "Video privato"
    return last_error or "Download non riuscito"


def download_song(artist, title, output_folder, ffmpeg_path, progress_cb=None, cookies_file=None):
    """
    Scarica una canzone da YouTube come MP3 massima qualità.
    progress_cb(dict) viene chiamato con aggiornamenti di stato.
    Restituisce (success: bool, message: str).
    """
    # ytsearch3: se il primo risultato è morto/protetto, -i salta al successivo;
    # --max-downloads 1 ferma appena uno va a buon fine.
    query = f"ytsearch3:{artist} - {title}"
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', f"{artist} - {title}")
    out_tmpl = os.path.join(output_folder, f"{safe_name}.%(ext)s")
    out_mp3  = os.path.join(output_folder, f"{safe_name}.mp3")

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--ffmpeg-location", ffmpeg_path,
        "-f", "bestaudio/best",   # forza sorgente audio migliore
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",   # VBR massima qualità encoder
        "-i",                     # ignora i risultati falliti e prova il successivo
        "--max-downloads", "1",   # scarica solo il primo che funziona
        "-o", out_tmpl,
        "--add-metadata",
        "--newline",
        "--no-warnings",
    ]
    # Cookies opzionali per i video con restrizione d'età
    if cookies_file and os.path.exists(cookies_file):
        cmd += ["--cookies", cookies_file]
    cmd.append(query)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        last_error = ""
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            if "ERROR" in line:
                last_error = line
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
        # Successo = il file mp3 esiste e non è vuoto. Non ci si può basare sul
        # return code: --max-downloads 1 esce con codice 101 anche quando va bene.
        success = os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 0
        return (True, "") if success else (False, _classify_error(last_error))

    except FileNotFoundError:
        return False, "yt-dlp non trovato. Esegui: pip install yt-dlp"
    except Exception as e:
        return False, str(e)
