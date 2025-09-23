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
        # Metadati + URL audio in un'unica chiamata
        res = subprocess.run(
            ["yt-dlp", "-j", "-f", "bestaudio", "-g", "--no-warnings", url],
            capture_output=True, text=True, check=True
        )

        # yt-dlp -j restituisce JSON con metadata
        data = json.loads(res.stdout)
        title = data.get("title", "Titolo non disponibile")
        views = data.get("view_count", 0)

        # URL diretto audio
        audio_url = data.get("url") or res.stdout.strip().splitlines()[-1]

        # Expire stimato dal link
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

    except subprocess.CalledProcessError:
        return jsonify({"status":"error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
