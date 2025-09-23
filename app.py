from flask import Flask, request, render_template_string
import subprocess
import json

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Mini Lettore YouTube</title>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>Visualizzazioni: {{ views }}</p>
    <audio controls>
        <source src="{{ direct_url }}" type="audio/mp4">
        Il tuo browser non supporta l'audio.
    </audio>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def yt_player():
    video_id = request.args.get("id")
    if not video_id:
        return "<p>Errore: manca parametro ?id=</p>", 400

    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        # Prende i metadati del video in JSON
        result = subprocess.check_output(["yt-dlp", "-j", url], text=True)
        data = json.loads(result)

        direct_url = data.get("url")
        title = data.get("title", "Titolo non disponibile")
        views = data.get("view_count", 0)

        return render_template_string(
            HTML_TEMPLATE,
            direct_url=direct_url,
            title=title,
            views=views
        )

    except subprocess.CalledProcessError as e:
        return f"<p>Errore durante il recupero del video: {e}</p>", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
