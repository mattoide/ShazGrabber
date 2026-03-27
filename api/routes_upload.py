import os
from flask import Blueprint, request, jsonify, current_app
from core.csv_parser import parse_shazam_csv

bp = Blueprint("upload", __name__, url_prefix="/api/upload")
_session = {}  # {csv_path, songs}

@bp.route("/csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "Nessun file inviato"}), 400

    f = request.files["file"]
    if not f.filename.endswith(".csv"):
        return jsonify({"error": "Il file deve essere un .csv"}), 400

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, "shazam_library.csv")
    f.save(path)

    try:
        songs = parse_shazam_csv(path)
    except Exception as e:
        return jsonify({"error": f"Errore parsing CSV: {e}"}), 400

    _session["csv_path"] = path
    _session["songs"]    = songs

    return jsonify({
        "total":   len(songs),
        "preview": songs[:8],
    })

@bp.route("/csv", methods=["DELETE"])
def delete_csv():
    _session.clear()
    return jsonify({"ok": True})

def get_songs():
    return _session.get("songs", [])
