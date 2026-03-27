from flask import Blueprint, request, jsonify
from core.fuzzy_matcher import match_library
from api.routes_upload import get_songs
from api.routes_folder import get_files

bp = Blueprint("match", __name__, url_prefix="/api/match")
_results = {}

@bp.route("/run", methods=["POST"])
def run():
    data      = request.get_json(force=True) or {}
    threshold = int(data.get("threshold", 72))

    songs = get_songs()
    files = get_files()

    if not songs:
        return jsonify({"error": "Carica prima il CSV Shazam"}), 400
    if not files:
        return jsonify({"error": "Scansiona prima la cartella locale"}), 400

    matched, missing, ambiguous = match_library(songs, files, threshold)

    _results["matched"]   = matched
    _results["missing"]   = missing
    _results["ambiguous"] = ambiguous

    def slim(lst):
        return [{"title": s["title"], "artist": s["artist"],
                 "score": s.get("score"), "match": s["match"]["filename"] if s.get("match") else None}
                for s in lst]

    return jsonify({
        "matched":   slim(matched),
        "missing":   slim(missing),
        "ambiguous": slim(ambiguous),
        "stats": {
            "total":     len(songs),
            "matched":   len(matched),
            "missing":   len(missing),
            "ambiguous": len(ambiguous),
        }
    })

def get_missing():
    return _results.get("missing", [])
