#!/usr/bin/env python3
from flask import Flask, request, render_template_string
import subprocess, json, re, os, mimetypes, time
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Cache in memoria: video_id -> {url, expire, title, views}
CACHE = {}

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{ title }}</title>
  <style>
    body{font-family:system-ui,Arial;margin:20px;max-width:700px}
    .meta{color:#555;margin-bottom:10px}
    .warn{color:#a00}
    a.link{word-break:break-all}
  </style>
  <script>
    function startCountdown(seconds) {
      function update() {
        if (seconds <= 0) {
          document.getElementById("countdown").innerText = "Scaduto";
          clearInterval(timer);
          return;
        }
        let h = Math.floor(seconds/3600);
        let m = Math.floor((seconds%3600)/60);
        let s = seconds % 60;
        document.getElementById("countdown").innerText = h+"h "+m+"m "+s+"s";
        seconds--;
      }
      update();
      let timer = setInterval(update, 1000);
    }
    window.onload = function() {
      startCountdown({{ seconds_left }});
    }
  </script>
</head>
<body>
  <h1>{{ title }}</h1>
  <div class="meta">
    Visualizzazioni: {{ views }} <br>
    Link valido ancora: <span id="countdown"></span>
  </div>

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
    <p class="warn">Impossibile ottenere un link diretto per questo video.</p>
  {% endif %}
</body>
</html>
"""

ID_RE = re.compile(r'^[A-Za-z0-9_\-]{4,}$')

def generate_url(video_id):
    """Usa yt-dlp per ottenere titolo, views e URL diretto."""
    url = f"https://www.youtube.com/watch?v={video_id}"

    # metadati
    res = subprocess.run(
        ["yt-dlp", "-j", "--no-warnings", "--skip-download", url],
        check=True, capture_output=True, text=True, timeout=30
    )
    data = json.loads(res.stdout)
    title = data.get("title", "Titolo non disponibile")
    views = data.get("view_count", 0)

    # link diretto
    g = subprocess.run(
        ["yt-dlp", "-f", "bestaudio", "-g", url],
        check=True, capture_output=True, text=True, timeout=30
    )
    lines = [l.strip() for l in g.stdout.splitlines() if l.strip()]
    direct_url = lines[0] if lines else None

    expire_ts = None
    if direct_url:
        qs = parse_qs(urlparse(direct_url).query)
        if "expire" in qs:
            expire_ts = int(qs["expire"][0])

    mime = None
    if direct_url:
        ext = os.path.splitext(urlparse(direct_url).path)[1]
        if ext:
            mime = mimetypes.guess_type("file" + ext)[0]

    return {
        "title": title,
        "views": views,
        "direct_url": direct_url,
        "expire": expire_ts,
        "mime": mime
    }

@app.route("/", methods=["GET"])
def yt_player():
    video_id = (request.args.get("id") or "").strip()
    if not video_id or not ID_RE.match(video_id):
        return "<p>Errore: parametro ?id= mancante o non valido</p>", 400

    # Controlla cache
    cached = CACHE.get(video_id)
    now = int(time.time())
    if cached and cached["expire"] and cached["expire"] > now + 30:
        # link ancora valido per almeno 30s → usa cache
        data = cached
    else:
        # genera nuovo link
        data = generate_url(video_id)
        CACHE[video_id] = data

    seconds_left = max(0, (data["expire"] or now) - now)

    return render_template_string(
        HTML_TEMPLATE,
        title=data["title"],
        views=data["views"],
        direct_url=data["direct_url"],
        mime=data["mime"],
        seconds_left=seconds_left
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
