#!/usr/bin/env python3
from flask import Flask, jsonify, request
import subprocess, threading, time, re, json
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

ID_RE = re.compile(r'^[A-Za-z0-9_\-]{4,}$')

# Stato dei video: video_id -> {"status": "preparing"/"ready"/"error", "audio_url":..., "title":..., "views":..., "expire_seconds":...}
VIDEO_CACHE = {}

def generate_audio_link(video_id):
    """Genera link audio e aggiorna VIDEO_CACHE"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        # Metadati
        res_meta = subprocess.run(
            ["yt-dlp", "-j", "--no-warnings", "--skip-download", url],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res_meta.stdout)
        title = data.get("title", "Titolo non disponibile")
        views = data.get("view_count", 0)

        # Link audio
        res_url = subprocess.run(
            ["yt-dlp", "-f", "bestaudio", "-g", "--no-warnings", url],
            capture_output=True, text=True, check=True
        )
        audio_url = res_url.stdout.strip().splitlines()[0]

        # Expire stimato
        expire_ts = None
        qs = parse_qs(urlparse(audio_url).query)
        if "expire" in qs:
            try:
                expire_ts = int(qs["expire"][0])
            except:
                expire_ts = None
        seconds_left = max(0, expire_ts - int(time.time())) if expire_ts else None

        VIDEO_CACHE[video_id] = {
            "status": "ready",
            "audio_url": audio_url,
            "title": title,
            "views": views,
            "expire_seconds": seconds_left
        }

    except subprocess.CalledProcessError:
        VIDEO_CACHE[video_id] = {"status": "error"}

@app.route("/api")
def api_audio():
    video_id = (request.args.get("id") or "").strip()
    if not video_id or not ID_RE.match(video_id):
        return jsonify({"status":"error","error":"id mancante o non valido"}), 400

    # Se video non in cache o non pronto, avvia thread
    if video_id not in VIDEO_CACHE or VIDEO_CACHE[video_id]["status"] in ["preparing", "error"]:
        if VIDEO_CACHE.get(video_id, {}).get("status") != "preparing":
            VIDEO_CACHE[video_id] = {"status": "preparing"}
            threading.Thread(target=generate_audio_link, args=(video_id,), daemon=True).start()
        return jsonify({"status": "preparing"})

    # Video pronto
    return jsonify(VIDEO_CACHE[video_id])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
