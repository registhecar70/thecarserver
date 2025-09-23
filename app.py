from flask import Flask, request, jsonify, render_template_string
from yt_dlp import YoutubeDL

app = Flask(__name__)

ydl_opts = {
    "quiet": True,
    "skip_download": True,
    "format": "bestaudio/best",
}

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mini YouTube Player</title>
</head>
<body>
    <h2>Mini YouTube Player</h2>
    <form method="get" action="/">
        YouTube URL: <input type="text" name="url" style="width:400px" required>
        <input type="submit" value="Play">
    </form>
    {% if audio_url %}
        <p>Riproduzione:</p>
        <audio controls autoplay style="width: 400px;">
            <source src="{{ audio_url }}">
            Il tuo browser non supporta l'audio HTML5.
        </audio>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    url = request.args.get("url")
    audio_url = None
    if url:
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info["url"]
        except Exception as e:
            audio_url = None
    return render_template_string(HTML_PAGE, audio_url=audio_url)

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
    print("🚀 Mini server Flask con lettore web avviato su http://0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080, debug=True)


