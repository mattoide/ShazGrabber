import os

AUDIO_EXTS = {".mp3", ".mp4", ".wav", ".aif", ".aiff", ".flac", ".ogg", ".m4a"}

def scan_folder(folder_path):
    """
    Scansiona ricorsivamente la cartella e restituisce
    lista di nomi file (senza estensione) per il fuzzy matching.
    """
    files = []
    for root, _, filenames in os.walk(folder_path):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in AUDIO_EXTS:
                name = os.path.splitext(fname)[0]
                files.append({"name": name, "filename": fname, "path": os.path.join(root, fname)})
    return files
