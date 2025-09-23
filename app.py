from flask import Flask, request, render_template_string
import subprocess
import json

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; }
        h1 { font-size: 22px; }
        p { margin: 5px 0; }
        .url-box { 
            background: #f0f0f0; 
            padding: 10px; 
            border-radius: 8px; 
            word-break: break-all;
        }
        audio { margin-top: 15px; width: 100%; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p><b>Views:</b> {{ views }}</p>
    <p><b>Direct URL:</b></p>
    <div class="url-box">{{ direct_url }}</div>
    <audio controls>
        <source src="{{ direct_url }}" type="audio/mp4">
        Your browser does not support audio playback.
    </audio>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def yt_player():
    video_id = request.args.get("id")
    if not video_id:
        return "<p>Error: missing ?id=</p>", 400

    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        # Get video metadata in JSON via yt-dlp
        result = subprocess.check_output(["yt-dlp", "-j", url], text=True)
        data = json.loads(result)

        direct_url = data.get("url")
        title = data.get("title", "No title")
        views = data.get("view_count", 0)

        return render_template_string(
            HTML_TEMPLATE,
            direct_url=direct_url,
            title=title,
            views=views
        )

    except subprocess.CalledProcessError as e:
        return f"<p>Error running yt-dlp: {e}</p>", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
