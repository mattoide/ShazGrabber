# ShazGrabber — Contesto per Claude

## Cos'è
App web Flask (Python) per sincronizzare la libreria Shazam con i file MP3 locali.
Carica il CSV esportato da Shazam, confronta con una cartella locale, scarica le canzoni mancanti da YouTube in MP3 alla massima qualità.

## Stack
- **Backend**: Flask + flask-cors, Python 3.10+
- **Matching**: rapidfuzz (fuzzy match titoli/artisti)
- **Download**: yt-dlp con ffmpeg (`bestaudio/best`, VBR 0)
- **Frontend**: HTML/CSS/JS vanilla, dark theme, SSE per progresso real-time

## Struttura
```
ShazGrabber/
├── app.py                  # Entry point Flask (porta 5000)
├── config.py               # FFMPEG_PATH (auto-detect), cartelle default, soglia fuzzy
├── core/
│   ├── csv_parser.py       # parse_shazam_csv(path) → lista {title, artist, date, url}
│   ├── file_scanner.py     # scan_folder(path) → lista file audio locali
│   ├── fuzzy_matcher.py    # match_library(songs, files, threshold) → matched/missing/ambiguous
│   └── downloader.py       # download_song(artist, title, out_dir, ffmpeg, cb) → (bool, str)
├── api/
│   ├── routes_upload.py    # POST /api/upload/csv
│   ├── routes_folder.py    # GET /api/folder/browse (tkinter dialog), POST /api/folder/scan
│   ├── routes_match.py     # POST /api/match/run
│   └── routes_download.py  # POST /api/download/start, GET /api/download/stream (SSE)
├── static/css/style.css
├── static/js/app.js        # SPA vanilla JS, gestisce i 4 step e SSE
└── templates/index.html
```

## Regole importanti

### Download
- Usare **sempre** `core/downloader.py` per qualsiasi download MP3 — non duplicare la logica yt-dlp altrove.
- Il comando usa `-f bestaudio/best` + `-x --audio-format mp3 --audio-quality 0`.
- YouTube offre al massimo ~256 kbps; il VBR 0 è già il massimo ottenibile.

### Fuzzy matching
- Soglia default: **72%**
- Peso: 65% titolo, 35% artista (`fuzz.partial_ratio`)
- Tre categorie: `matched` (≥72%), `ambiguous` (57–71%), `missing` (<57%)

### CSV Shazam
- Encoding: UTF-8 BOM (`utf-8-sig`)
- Colonne: `Index, TagTime, Title, Artist, URL, TrackKey`
- Il parser deduplica per `(title.lower(), artist.lower())`

### SSE
- Il worker di download gira su un thread separato e manda eventi in una `queue.Queue`
- L'endpoint SSE (`/api/download/stream/<session_id>`) drena la queue
- Keep-alive ogni 20s con `: ping`

## Avvio rapido
```bash
pip install -r requirements.txt
# ffmpeg: winget install ffmpeg
python app.py
# → http://localhost:5000
```

## File collegati fuori dal progetto
- `C:\Users\matto\Scripts\shazam_download.py` — script CLI che importa da questo progetto
- `C:\Users\matto\Videos\shazamlibrary.csv` — CSV Shazam dell'utente
- `C:\Users\matto\Videos\Shazam_Download\` — cartella download default
- `C:\Users\matto\Videos\aTubeCatcher\` — libreria MP3 locale principale dell'utente
