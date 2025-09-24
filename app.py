#!/usr/bin/env python3
from flask import Flask, jsonify, request
import subprocess, threading, time

app = Flask(__name__)

# Cache: video_id -> {"status":..., "audio_url":...}
VIDEO_CACHE = {}
# Coda preload
PRELOAD_QUEUE = []
# Lock per accesso thread-safe
LOCK = threading.Lock()

def generate_audio(video_id):
    """Genera il link audio per un singolo video"""
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
        VIDEO_CACHE[video_id] = {"status": "ready", "audio_url": audio_url}
    except subprocess.CalledProcessError:
        VIDEO_CACHE[video_id] = {"status": "error"}

def generate_batch(video_ids):
    """Genera i link audio in batch"""
    urls = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
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
            ] + urls,
            capture_output=True, text=True, check=True
        )
        lines = res.stdout.strip().splitlines()
        for vid, line in zip(video_ids, lines):
            VIDEO_CACHE[vid] = {"status": "ready", "audio_url": line.strip()}
    except subprocess.CalledProcessError:
        for vid in video_ids:
            VIDEO_CACHE[vid] = {"status": "error"}

def check_queue():
    """Controlla la coda e processa batch da 20"""
    while True:
        time.sleep(1)
        with LOCK:
            if len(PRELOAD_QUEUE) >= 20:
                batch = PRELOAD_QUEUE[:20]
                del PRELOAD_QUEUE[:20]
                threading.Thread(target=generate_batch, args=(batch,), daemon=True).start()

@app.route("/api")
def api_audio():
    video_id = (request.args.get("id") or "").strip()
    urgent = request.args.get("u") == "1"

    if not video_id:
        return jsonify({"status": "error"}), 400

    # Caso: già in cache
    if video_id in VIDEO_CACHE and VIDEO_CACHE[video_id]["status"] == "ready":
        return jsonify(VIDEO_CACHE[video_id])

    # Caso urgente → genera subito
    if urgent:
        VIDEO_CACHE[video_id] = {"status": "preparing"}
        threading.Thread(target=generate_audio, args=(video_id,), daemon=True).start()
        return jsonify({"status": "preparing"})

    # Caso preload → accoda
    with LOCK:
        if video_id not in PRELOAD_QUEUE and (
            video_id not in VIDEO_CACHE or VIDEO_CACHE[video_id]["status"] != "preparing"
        ):
            PRELOAD_QUEUE.append(video_id)
            VIDEO_CACHE[video_id] = {"status": "preparing"}
    return jsonify({"status": "preparing"})

if __name__ == "__main__":
    # Thread che gestisce la coda
    threading.Thread(target=check_queue, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
