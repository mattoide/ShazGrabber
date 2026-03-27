import json, os, queue, threading, uuid
from flask import Blueprint, request, jsonify, Response, stream_with_context
from core.downloader import download_song
import config

bp = Blueprint("download", __name__, url_prefix="/api/download")

# Sessioni di download attive: {session_id: {queue, stop_event, status}}
_sessions = {}

def _worker(session_id, songs, output_folder):
    sess  = _sessions[session_id]
    q     = sess["queue"]
    stop  = sess["stop_event"]
    total = len(songs)

    sess["status"]["total"]   = total
    sess["status"]["current"] = 0
    sess["status"]["ok"]      = 0
    sess["status"]["err"]     = 0

    os.makedirs(output_folder, exist_ok=True)

    for i, song in enumerate(songs):
        if stop.is_set():
            q.put({"event": "cancelled", "data": {}})
            break

        label = f"{song['artist']} - {song['title']}"
        sess["status"]["current"] = i + 1
        sess["status"]["song"]    = label

        q.put({"event": "song_start", "data": {"song": label, "index": i + 1, "total": total}})

        def cb(info, lbl=label):
            if info["type"] == "progress":
                q.put({"event": "progress", "data": {"song": lbl, "percent": info["percent"]}})

        ffmpeg = config.FFMPEG_PATH or "ffmpeg"
        success, err_msg = download_song(song["artist"], song["title"], output_folder, ffmpeg, cb)

        if success:
            sess["status"]["ok"] += 1
            q.put({"event": "song_ok", "data": {"song": label}})
        else:
            sess["status"]["err"] += 1
            q.put({"event": "song_err", "data": {"song": label, "error": err_msg}})

    q.put({"event": "done", "data": {
        "total": total,
        "ok":    sess["status"]["ok"],
        "err":   sess["status"]["err"],
    }})
    q.put(None)  # sentinel


@bp.route("/start", methods=["POST"])
def start():
    data   = request.get_json(force=True) or {}
    songs  = data.get("songs", [])
    folder = data.get("folder", config.DOWNLOAD_FOLDER)

    if not songs:
        return jsonify({"error": "Nessuna canzone selezionata"}), 400
    if not config.FFMPEG_PATH:
        return jsonify({"error": "ffmpeg non trovato. Installa con: winget install ffmpeg"}), 400

    sid  = str(uuid.uuid4())
    sess = {
        "queue":      queue.Queue(),
        "stop_event": threading.Event(),
        "status":     {"running": True},
    }
    _sessions[sid] = sess

    t = threading.Thread(target=_worker, args=(sid, songs, folder), daemon=True)
    t.start()

    return jsonify({"session_id": sid})


@bp.route("/stream/<session_id>")
def stream(session_id):
    if session_id not in _sessions:
        return jsonify({"error": "Sessione non trovata"}), 404

    def generate():
        q = _sessions[session_id]["queue"]
        yield ": ping\n\n"
        while True:
            try:
                item = q.get(timeout=20)
            except queue.Empty:
                yield ": ping\n\n"
                continue

            if item is None:
                break

            yield f"event: {item['event']}\ndata: {json.dumps(item['data'])}\n\n"

        yield "event: stream_end\ndata: {}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@bp.route("/cancel/<session_id>", methods=["POST"])
def cancel(session_id):
    if session_id in _sessions:
        _sessions[session_id]["stop_event"].set()
    return jsonify({"ok": True})


@bp.route("/status/<session_id>")
def status(session_id):
    if session_id not in _sessions:
        return jsonify({"error": "Sessione non trovata"}), 404
    return jsonify(_sessions[session_id]["status"])
