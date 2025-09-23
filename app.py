from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL

app = Flask(__name__)
ydl_opts = {"quiet": True, "skip_download": True, "format": "best"}

@app.route("/yt", methods=["GET"])
def yt():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Manca parametro ?url="}), 400
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({"direct_url": info["url"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
