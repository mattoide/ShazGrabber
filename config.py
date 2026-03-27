import os

BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER    = os.path.join(BASE_DIR, "uploads")
DOWNLOAD_FOLDER  = os.path.join(BASE_DIR, "downloads")
FUZZY_THRESHOLD  = 72
MAX_CONTENT_MB   = 10

# Cerca ffmpeg automaticamente
def find_ffmpeg():
    import shutil
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    winget_base = os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages")
    for root, _, files in os.walk(winget_base):
        if "ffmpeg.exe" in files:
            return os.path.join(root, "ffmpeg.exe")
    return None

FFMPEG_PATH = find_ffmpeg()
