#!/usr/bin/env python3
from flask import Flask, request, render_template_string
import subprocess, json, re, os, mimetypes
from urllib.parse import urlparse
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Mini Lettore YouTube</title>
  <style>
    body{font-family:system-ui,Arial;margin:20px;max-width:700px}
    .meta{color:#555;margin-bottom:10px}
    .warn{color:#a00}
    a.link{word-break:break-all}
  </style>
</head>
<body>
  <h1>{{ title }}</h1>
  <div class="meta">Visualizzazioni: {{ views }} &nbsp;|&nbsp; Link generato: {{ generated_at }}</div>

  {% if direct_url %}
    <p>Link diretto: <a class="link" href="{{ direct_url }}" target="_blank">{{ direct_url }}</a></p>
    <audio controls preload="metadata" style="width:100%">
      {% if mime %}
        <source src="{{ direct_url }}" type="{{ mime }}">
      {% else %}
        <source src="{{ direct_url }}">
      {% endif %}
      Il tuo browser non supporta l'audio.
    </audio>
  {% else %}
    <p class="warn">Impossibile ottenere un link diretto per questo video (yt-dlp non ha restituito un URL).</p>
    <p>Prova a ricaricare la pagina (lo script genera un nuovo link ogni richiesta).</p>
  {% endif %}
</body>
</html>
"""

# semplice validazione dell'ID (tipico YouTube ID)
ID_RE = re.compile(r'^[A-Za-z0-9_\-]{4,}$')

@app.route("/", methods=["GET"])
def yt_player():
    video_id = (request.args.get("id") or "").strip()
    if not video_id or not ID_RE.match(video_id):
        return "<p>Errore: parametro ?id= mancante o non valido</p>", 400

    url = f"https://www.youtube.com/watch?v={video_id}"

    # 1) prende i metadati (titolo, view_count)
    try:
        res = subprocess.run(
            ["yt-dlp", "-j", "--no-warnings", "--skip-download", url],
            check=True, capture_output=True, text=True, timeout=30
        )
        data = json.loads(res.stdout)
        title = data.get("title", "Titolo non disponibile")
        views = data.get("view_count", 0)
    except subprocess.CalledProcessError as e:
        return f"<p>Errore durante recupero metadati: {e}</p>", 500
    except json.JSONDecodeError:
        return "<p>Errore: risposta metadati non valida</p>", 500

    # 2) ottiene un URL diretto per l'audio usando -g (bestaudio)
    direct_url = None
    try:
        g = subprocess.run(
            ["yt-dlp", "-f", "bestaudio", "-g", url],
            check=True, capture_output=True, text=True, timeout=30
        )
        lines = [l.strip() for l in g.stdout.splitlines() if l.strip()]
        if lines:
            direct_url = lines[0]  # di solito l'audio (primo link)
    except subprocess.CalledProcessError:
        direct_url = None

    # tenta dedurre tipo MIME dall'estensione (se presente)
    mime = None
    if direct_url:
        parsed = urlparse(direct_url)
        ext = os.path.splitext(parsed.path)[1]
        if ext:
            mime = mimetypes.guess_type("file" + ext)[0]

    generated_at = datetime.utcnow().isoformat() + "Z"
    return render_template_string(
        HTML_TEMPLATE,
        title=title,
        views=views,
        direct_url=direct_url,
        mime=mime,
        generated_at=generated_at
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
