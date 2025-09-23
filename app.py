#!/usr/bin/env python3
from flask import Flask, jsonify, request
import subprocess, json, re, time
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

ID_RE = re.compile(r'^[A-Za-z0-9_\-]{4,}$')

@app.route("/api")
def api_audio():
    video_id = (request.args.get("id") or "").strip()
    if not video_id or not ID_RE.match(video_id):
        return jsonify({"status":"error", "error":"id mancante o non valido"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        # 1. Ottieni metadati JSON
        res_meta = subprocess.run(
            ["yt-dlp", "-j", "--no-warnings", "--skip-download", url],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res_meta.stdout)
        title = data.get("title", "Titolo non disponibile")
        views = data.get("view_count", 0)

        # 2. Ottieni link diretto audio
        res_url = subprocess.run(
            ["yt-dlp", "-f", "bestaudio", "-g", "--no-warnings", url],
            capture_output=True, text=True, check=True
        )
        audio_url = res_url.stdout.strip().splitlines()[0]

        # 3. Expire stimato
        expire_ts = None
        qs = parse_qs(urlparse(audio_url).query)
        if "expire" in qs:
            try:
                expire_ts = int(qs["expire"][0])
            except:
                expire_ts = None

        seconds_left = max(0, expire_ts - int(time.time())) if expire_ts else None

        return jsonify({
            "status": "ready",
            "audio_url": audio_url,
            "title": title,
            "views": views,
            "expire_seconds": seconds_left
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"status":"error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
