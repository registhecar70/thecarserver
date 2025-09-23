#!/usr/bin/env python3
from flask import Flask, send_from_directory, request, jsonify
import subprocess, os, json, re, threading

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ID_RE = re.compile(r'^[A-Za-z0-9_\-]{4,}$')
# Stato dei video: video_id -> {"status": "preparing"/"ready", "filename": "...", "title": "...", "views": ...}
VIDEO_STATUS = {}

def download_video(video_id):
    """Scarica il video completo e aggiorna VIDEO_STATUS"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    filename = f"{video_id}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # Scarica solo se non esiste
    if not os.path.exists(filepath):
        VIDEO_STATUS[video_id] = {"status": "preparing"}
        try:
            subprocess.run([
                "yt-dlp",
                "-f", "best",
                "-o", filepath,
                url
            ], check=True)
        except subprocess.CalledProcessError:
            VIDEO_STATUS[video_id] = {"status": "error"}
            return
    # Aggiorna metadati
    res = subprocess.run(
        ["yt-dlp", "-j", "--no-warnings", "--skip-download", url],
        capture_output=True, text=True, check=True
    )
    data = json.loads(res.stdout)
    title = data.get("title", "Titolo non disponibile")
    views = data.get("view_count", 0)
    
    VIDEO_STATUS[video_id] = {
        "status": "ready",
        "filename": filename,
        "title": title,
        "views": views
    }

@app.route("/api")
def api_video():
    video_id = (request.args.get("id") or "").strip()
    if not video_id or not ID_RE.match(video_id):
        return jsonify({"error": "id mancante o non valido"}), 400

    # Se il video non è in status o è stato cancellato, avvia download in thread separato
    if video_id not in VIDEO_STATUS or VIDEO_STATUS[video_id].get("status") != "ready":
        if VIDEO_STATUS.get(video_id, {}).get("status") != "preparing":
            threading.Thread(target=download_video, args=(video_id,), daemon=True).start()
        return jsonify({"status": "preparing"})

    status = VIDEO_STATUS[video_id]
    return jsonify({
        "status": "ready",
        "video_url": f"/video/{status['filename']}",
        "title": status["title"],
        "views": status["views"]
    })

@app.route("/video/<filename>")
def serve_video(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
