import os, threading
from flask import Blueprint, request, jsonify
from core.file_scanner import scan_folder

bp = Blueprint("folder", __name__, url_prefix="/api/folder")
_session = {}  # {path, files}

@bp.route("/browse", methods=["GET"])
def browse():
    """Apre un dialog nativo per scegliere la cartella."""
    result = {"path": None}
    done   = threading.Event()

    def _open():
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes("-topmost", True)
            path = filedialog.askdirectory(title="Seleziona cartella MP3")
            root.destroy()
            result["path"] = path
        except Exception as e:
            result["error"] = str(e)
        finally:
            done.set()

    t = threading.Thread(target=_open, daemon=True)
    t.start()
    done.wait(timeout=60)

    if result.get("error"):
        return jsonify({"error": result["error"]}), 500
    return jsonify({"path": result["path"] or ""})

@bp.route("/scan", methods=["POST"])
def scan():
    data = request.get_json(force=True)
    path = data.get("path", "").strip()

    if not path or not os.path.isdir(path):
        return jsonify({"error": "Cartella non valida o non trovata"}), 400

    files = scan_folder(path)
    _session["path"]  = path
    _session["files"] = files

    return jsonify({
        "total":   len(files),
        "preview": [f["filename"] for f in files[:10]],
    })

def get_files():
    return _session.get("files", [])
