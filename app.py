from flask import Flask, request, jsonify
import subprocess, threading

app = Flask(__name__)
VIDEO_CACHE = {}

def generate_audio(video_id):
    try:
        cmd = [
            "java", "-jar", "extractor-v0.24.8-all.jar",
            "--youtube", f"https://www.youtube.com/watch?v={video_id}"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        audio_url = res.stdout.strip().splitlines()[0]
        VIDEO_CACHE[video_id] = {"status":"ready","audio_url":audio_url}
    except subprocess.CalledProcessError:
        VIDEO_CACHE[video_id] = {"status":"error"}

@app.route("/api")
def api_audio():
    video_id = (request.args.get("id") or "").strip()
    urgent = request.args.get("u") == "1"

    if not video_id:
        return jsonify({"status":"error"}), 400

    if video_id in VIDEO_CACHE:
        if VIDEO_CACHE[video_id]["status"]=="ready":
            return jsonify(VIDEO_CACHE[video_id])
        elif VIDEO_CACHE[video_id]["status"]=="preparing":
            return jsonify({"status":"preparing"})
        elif VIDEO_CACHE[video_id]["status"]=="error":
            return jsonify({"status":"error"})

    VIDEO_CACHE[video_id] = {"status":"preparing"}
    threading.Thread(target=generate_audio, args=(video_id,), daemon=True).start()
    return jsonify({"status":"preparing"})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=8080)

