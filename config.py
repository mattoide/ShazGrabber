import os

BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER    = os.path.join(BASE_DIR, "uploads")
DOWNLOAD_FOLDER  = os.path.join(os.path.expanduser("~"), "Music")
FUZZY_THRESHOLD  = 72
MAX_CONTENT_MB   = 10

# File cookies opzionale (formato Netscape) per scaricare i video YouTube con
# restrizione d'età. Esportalo una volta dal browser e salvalo qui. Se non
# esiste, i download normali funzionano lo stesso, solo gli age-restricted no.
COOKIES_FILE     = os.path.join(os.path.expanduser("~"), "shazgrabber_cookies.txt")

# Cerca ffmpeg automaticamente
def find_ffmpeg():
    import shutil
    path = shutil.which("ffmpeg")
    if path:
        return os.path.dirname(path)
    winget_base = os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages")
    for root, _, files in os.walk(winget_base):
        if "ffmpeg.exe" in files:
            return root
    return None

FFMPEG_PATH = find_ffmpeg()
