from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL

app = Flask(__name__)

# Opzioni di yt-dlp: niente download, silenzioso, formato migliore
ydl_opts = {
    "quiet": True,
    "skip_download": True,
    "format": "best",
}

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

if __name__ == "__main__":
    print("🚀 Server Flask avviato su http://0.0.0.0:8080")
    print("Puoi testare: curl http://127.0.0.1:8080/yt?url=URL_VIDEO")
    app.run(host="0.0.0.0", port=8080, debug=True)
