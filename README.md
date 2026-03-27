# ShazGrabber

Applicazione web locale per sincronizzare la tua libreria Shazam con i file MP3 sul tuo computer.

Carica il CSV esportato da Shazam, confrontalo con la tua cartella musica, e scarica automaticamente le canzoni mancanti in MP3 alla massima qualità disponibile.

---

## Funzionalità

- **Importa libreria Shazam** — legge il CSV esportato direttamente dall'app
- **Scansione cartella locale** — rileva tutti i file audio già presenti (MP3, FLAC, WAV, M4A, ecc.)
- **Analisi fuzzy** — confronto intelligente tra titoli Shazam e nomi file locali, anche con nomi leggermente diversi
- **Download automatico** — scarica le canzoni mancanti da YouTube via yt-dlp in MP3 alla massima qualità (`bestaudio/best`, VBR 0)
- **Progresso in tempo reale** — interfaccia web con progress bar live tramite SSE (Server-Sent Events)
- **Ripresa automatica** — se interrotto, riprende da dove si era fermato

---

## Requisiti

### Python
```
flask>=3.0
flask-cors>=4.0
yt-dlp>=2024.1
rapidfuzz>=3.6
```

### Sistema
- **Python 3.10+**
- **ffmpeg** — necessario per la conversione audio
  ```
  winget install ffmpeg
  ```

---

## Installazione

```bash
# 1. Entra nella cartella del progetto
cd C:\Users\matto\Lavoro\Extra\ShazGrabber

# 2. Installa le dipendenze Python
pip install -r requirements.txt

# 3. Installa ffmpeg (se non già presente)
winget install ffmpeg
```

---

## Avvio

```bash
python app.py
```
Oppure doppio click su `start.bat`.

Apri il browser su: **http://localhost:5000**

---

## Utilizzo

### Step 1 — Esporta la libreria da Shazam
Nell'app Shazam: *Libreria → ··· → Esporta libreria*
Riceverai un file `.csv` via email.

### Step 2 — Carica il CSV
Trascina il file CSV nell'interfaccia o clicca per selezionarlo.

### Step 3 — Seleziona la cartella locale
Indica la cartella che contiene i tuoi MP3 già scaricati.
Clicca **Sfoglia** per aprire il dialog nativo del sistema operativo.

### Step 4 — Analisi
Regola la soglia di similarità (default 72%) e clicca **Esegui analisi**.
Il risultato mostra tre categorie:
- **Trovate** — già presenti in locale
- **Mancanti** — da scaricare
- **Incerte** — match parziale, da verificare manualmente

### Step 5 — Download
Seleziona le canzoni da scaricare e clicca **Scarica selezionate**.
Il download avviene in background con progresso in tempo reale.

---

## Struttura del progetto

```
ShazGrabber/
├── app.py                  # Entry point Flask
├── config.py               # Configurazione (ffmpeg, cartelle, soglia)
├── requirements.txt
├── start.bat               # Avvio rapido su Windows
│
├── core/
│   ├── csv_parser.py       # Parsing CSV Shazam
│   ├── file_scanner.py     # Scansione cartella audio locale
│   ├── fuzzy_matcher.py    # Confronto fuzzy (rapidfuzz)
│   └── downloader.py       # Wrapper yt-dlp con progress callback
│
├── api/
│   ├── routes_upload.py    # POST /api/upload/csv
│   ├── routes_folder.py    # GET /api/folder/browse, POST /api/folder/scan
│   ├── routes_match.py     # POST /api/match/run
│   └── routes_download.py  # POST /api/download/start, GET /api/download/stream (SSE)
│
├── static/
│   ├── css/style.css       # Dark theme
│   └── js/app.js           # Frontend vanilla JS
│
└── templates/
    └── index.html          # SPA a 4 step
```

---

## Note tecniche

- Il download usa sempre `-f bestaudio/best` per ottenere la sorgente audio migliore disponibile su YouTube (tipicamente 128–256 kbps opus/AAC), convertita poi in MP3 con encoder VBR qualità 0
- YouTube non offre audio oltre ~256 kbps, quindi quello è il massimo ottenibile
- Il fuzzy matching usa `rapidfuzz.fuzz.token_sort_ratio` con peso 65% titolo / 35% artista
- Il progresso live usa SSE (Server-Sent Events) con keep-alive ogni 20 secondi
