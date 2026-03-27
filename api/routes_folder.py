import os, threading
from flask import Blueprint, request, jsonify
from core.file_scanner import scan_folder
import config

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
    data  = request.get_json(force=True)
    paths = data.get("paths", [])

    # Retrocompatibilità: supporta anche campo singolo "path"
    if not paths and data.get("path"):
        paths = [data["path"]]

    paths = [p.strip() for p in paths if p and p.strip()]
    invalid = [p for p in paths if not os.path.isdir(p)]
    if invalid:
        return jsonify({"error": f"Cartelle non trovate: {', '.join(invalid)}"}), 400

    files = []
    seen  = set()
    for p in paths:
        for f in scan_folder(p):
            key = f["path"].lower()
            if key not in seen:
                seen.add(key)
                files.append(f)

    _session["paths"] = paths
    _session["files"] = files

    return jsonify({
        "total":   len(files),
        "preview": [f["filename"] for f in files[:10]],
    })

@bp.route("/default", methods=["GET"])
def default_folder():
    return jsonify({"path": config.DOWNLOAD_FOLDER})

def get_files():
    return _session.get("files", [])
