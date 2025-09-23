#!/usr/bin/env python3
from flask import Flask, send_from_directory, request, render_template_string
import subprocess, os, json, re

app = Flask(__name__)

# Cartella dove salvare i video scaricati
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Template HTML con video player e link
HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{{ title }}</title>
<style>
body{font-family:system-ui,Arial;margin:20px;max-width:700px;}
.meta{color:#555;margin-bottom:10px;}
a.link{word-break:break-all;}
</style>
</head>
<body>
<h1>{{ title }}</h1>
<p class="meta">Visualizzazioni: {{ views }}</p>

<p>Link diretto al video: <a class="link" href="{{ video_url }}" target="_blank">{{ video_url }}</a></p>

<video controls width="640">
  <source src="{{ video_url }}" type="video/mp4">
  Il tuo browser non supporta il video.
</video>

</body>
</html>
"""

# Validazione semplice dell'ID YouTube
ID_RE = re.compile(r'^[A-Za-z0-9_\-]{4,}$')

def download_video(video_id):
    """Scarica il video completo (audio+video) se non esiste già"""
    # Cerca un file esistente nella cartella
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.startswith(video_id):
            return filename  # già presente

    # Se non esiste, scarica
    url = f"https://www.youtube.com/watch?v={video_id}"
    # Salva in formato mp4 con nome VIDEOID.mp4
    output_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    subprocess.run([
        "yt-dlp",
        "-f", "best",
        "-o", output_path,
        url
    ], check=True)
    return f"{video_id}.mp4"

def get_video_metadata(video_id):
    """Recupera titolo e visualizzazioni tramite yt-dlp"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    res = subprocess.run(
        ["yt-dlp", "-j", "--no-warnings", "--skip-download", url],
        capture_output=True, text=True, check=True
    )
    data = json.loads(res.stdout)
    title = data.get("title", "Titolo non disponibile")
    views = data.get("view_count", 0)
    return title, views

@app.route("/")
def yt_page():
    video_id = (request.args.get("id") or "").strip()
    if not video_id or not ID_RE.match(video_id):
        return "Parametro ?id= mancante o non valido", 400

    try:
        # Scarica il video se necessario
        filename = download_video(video_id)
        # Recupera metadati
        title, views = get_video_metadata(video_id)
    except subprocess.CalledProcessError as e:
        return f"Errore durante download/metadati: {e}", 500

    video_url = f"/video/{filename}"
    return render_template_string(
        HTML_TEMPLATE,
        title=title,
        views=views,
        video_url=video_url
    )

@app.route("/video/<filename>")
def serve_video(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
