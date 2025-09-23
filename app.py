from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route("/yt", methods=["GET"])
def yt():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Manca parametro ?url="}), 400

    try:
        # Chiede a yt-dlp di restituire tutti i metadati in JSON
        result = subprocess.check_output(
            ["yt-dlp", "-j", url],
            text=True
        )
        data = json.loads(result)

        # Recupera URL diretto, titolo e visualizzazioni
        direct_url = data.get("url")
        title = data.get("title")
        views = data.get("view_count")

        return jsonify({
            "direct_url": direct_url,
            "title": title,
            "views": views
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
