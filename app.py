#!/usr/bin/env python3
from flask import Flask, jsonify, request
import subprocess, threading

app = Flask(__name__)

# Cache dei risultati: video_id -> {status, audio_url}
VIDEO_CACHE = {}

def generate_audio(video_id):
    """Genera e salva in cache il link audio super ottimizzato"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        res = subprocess.run(
            [
                "yt-dlp",
                "-f", "bestaudio",
                "--get-url",
                "--no-warnings",
                "--no-playlist",
                "--skip-download",
                "--quiet",
                url
            ],
            capture_output=True, text=True, check=True
        )
        audio_url = res.stdout.strip()
        VIDEO_CACHE[video_id] = {
            "status": "ready",
            "audio_url": audio_url
        }
    except subprocess.CalledProcessError:
        VIDEO_CACHE[video_id] = {"status": "error"}

@app.route("/api")
def api_audio():
    video_id = (request.args.get("id") or "").strip()
    if not video_id:
        return jsonify({"status": "error"}), 400

    # Se non è in cache o è in stato non valido → prepara
    if video_id not in VIDEO_CACHE or VIDEO_CACHE[video_id]["status"] in ["error", "preparing"]:
        if VIDEO_CACHE.get(video_id, {}).get("status") != "preparing":
            VIDEO_CACHE[video_id] = {"status": "preparing"}
            threading.Thread(target=generate_audio, args=(video_id,), daemon=True).start()
        return jsonify({"status": "preparing"})

    # Restituisce il risultato dalla cache
    return jsonify(VIDEO_CACHE[video_id])

if __name__ == "__main__":
    # Server in ascolto su tutte le interfacce, porta 8080
    app.run(host="0.0.0.0", port=8080)
