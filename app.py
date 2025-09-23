from flask import Flask, request, render_template_string
from yt_dlp import YoutubeDL
import time
from urllib.parse import urlparse, parse_qs

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
        Video ID: <input type="text" name="id" required>
        <input type="submit" value="Play">
    </form>
    {% if audio_url %}
        <p>Riproduzione:</p>
        <audio controls autoplay style="width: 400px;">
            <source src="{{ audio_url }}" type="audio/mp4">
            Il tuo browser non supporta l'audio HTML5.
        </audio>
        <p>URL scade tra <span id="timer">{{ ttl_formatted }}</span></p>
        <script>
            function secondsToHMS(seconds) {
                let h = Math.floor(seconds / 3600);
                let m = Math.floor((seconds % 3600) / 60);
                let s = seconds % 60;
                return [h, m, s].map(v => v.toString().padStart(2, '0')).join(':');
            }

            let seconds = {{ ttl }};
            let timerEl = document.getElementById("timer");
            setInterval(() => {
                if(seconds > 0){
                    seconds -= 1;
                    timerEl.innerText = secondsToHMS(seconds);
                } else {
                    timerEl.innerText = "SCADUTO";
                }
            }, 1000);
        </script>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    video_id = request.args.get("id")
    audio_url = None
    ttl = 0
    ttl_formatted = "00:00:00"
    if video_id:
        try:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                audio_url = info["url"]
                # Calcola TTL dall'URL
                query = parse_qs(urlparse(audio_url).query)
                expire_ts = int(query.get("expire", [0])[0])
                ttl = max(0, expire_ts - int(time.time()))
                h = ttl // 3600
                m = (ttl % 3600) // 60
                s = ttl % 60
                ttl_formatted = f"{h:02d}:{m:02d}:{s:02d}"
        except Exception as e:
            audio_url = None
            ttl = 0
            ttl_formatted = "00:00:00"
    return render_template_string(HTML_PAGE, audio_url=audio_url, ttl=ttl, ttl_formatted=ttl_formatted)

if __name__ == "__main__":
    print("🚀 Mini server Flask con lettore e timer HH:MM:SS avviato su http://0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080, debug=True)
