from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route("/geturl", methods=["GET"])
def get_url():
    video_url = request.args.get("video")
    if not video_url:
        return jsonify({"error": "Nessun URL fornito"}), 400

    try:
        ydl_opts = {
            "format": "best",
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify({
                "title": info.get("title"),
                "url": info.get("url"),
                "duration": info.get("duration"),
                "ext": info.get("ext"),
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
