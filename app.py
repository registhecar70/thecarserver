#!/usr/bin/env python3
from flask import Flask, jsonify, request
import subprocess, threading

app = Flask(__name__)

# Cache dei video: video_id -> {"status":..., "audio_url":...}
VIDEO_CACHE = {}

def generate_audio(video_id):
    """Genera il link audio per un video YouTube"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        # yt-dlp: solo link audio, massimo 128 kbps, senza scaricare
        res = subprocess.run(
            ["yt-dlp", "-f", "bestaudio[abr<=128]", "-g", "--no-warnings", url],
            capture_output=True, text=True, check=True
        )
        audio_url = res.stdout.strip().splitlines()[0]
        VIDEO_CACHE[video_id] = {"status": "ready", "audio_url": audio_url}
    except subprocess.CalledProcessError:
        VIDEO_CACHE[video_id] = {"status": "error"}

@app.route("/api")
def api_audio():
    video_id = (request.args.get("id") or "").strip()
    if not video_id:
        return jsonify({"status": "error"}), 400

    # Se il video non è pronto o non è in cache, avvia thread per generarlo
    if video_id not in VIDEO_CACHE or VIDEO_CACHE[video_id]["status"] in ["preparing", "error"]:
        if VIDEO_CACHE.get(video_id, {}).get("status") != "preparing":
            VIDEO_CACHE[video_id] = {"status": "preparing"}
            threading.Thread(target=generate_audio, args=(video_id,), daemon=True).start()
        return jsonify({"status": "preparing"})

    # Video pronto
    return jsonify(VIDEO_CACHE[video_id])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
