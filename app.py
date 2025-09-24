#!/usr/bin/env python3
from flask import Flask, jsonify, request
import subprocess, threading

app = Flask(__name__)

# Cache: video_id -> {"status":..., "audio_url":...}
VIDEO_CACHE = {}

def generate_audio(video_id):
    """Genera il link audio per un singolo video"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        res = subprocess.run(
            ["yt-dlp", "-f", "bestaudio", "--get-url", "--no-warnings",
             "--no-playlist", "--skip-download", "--quiet", url],
            capture_output=True, text=True, check=True
        )
        audio_url = res.stdout.strip()
        VIDEO_CACHE[video_id] = {"status": "ready", "audio_url": audio_url}
    except subprocess.CalledProcessError:
        VIDEO_CACHE[video_id] = {"status": "error"}

@app.route("/api")
def api_audio():
    video_id = (request.args.get("id") or "").strip()
    if not video_id:
        return jsonify({"status": "error"}), 400

    # Caso: già in cache e pronto
    if video_id in VIDEO_CACHE:
        if VIDEO_CACHE[video_id]["status"] == "ready":
            return jsonify(VIDEO_CACHE[video_id])
        elif VIDEO_CACHE[video_id]["status"] == "preparing":
            return jsonify({"status": "preparing"})
        elif VIDEO_CACHE[video_id]["status"] == "error":
            return jsonify({"status": "error"})

    # Caso nuovo: genera subito in background
    VIDEO_CACHE[video_id] = {"status": "preparing"}
    threading.Thread(target=generate_audio, args=(video_id,), daemon=True).start()
    return jsonify({"status": "preparing"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
