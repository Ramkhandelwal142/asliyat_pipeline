from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import run

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint — shows environment info."""
    import subprocess
    try:
        pw_ver = subprocess.check_output(
            ["python", "-c", "import playwright; print(playwright.__version__)"],
            stderr=subprocess.STDOUT, text=True
        ).strip()
    except Exception as e:
        pw_ver = f"error: {e}"

    groq_key = os.environ.get("GROQ_API_KEY", "NOT SET")
    groq_masked = groq_key[:8] + "..." if len(groq_key) > 8 else groq_key

    return jsonify({
        "status": "ok",
        "playwright_version": pw_ver,
        "groq_api_key_set": groq_key != "NOT SET",
        "groq_key_preview": groq_masked,
        "output_dir_exists": os.path.exists("output"),
        "cwd": os.getcwd(),
    })

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    topic = data.get('topic', '')
    if not topic.strip():
        topic = None
    no_research = data.get('fast_mode', True)

    try:
        result = run(topic=topic, no_research=no_research)
        if result and result.get('output'):
            abs_path = os.path.abspath(result['output'])
            return jsonify({
                "status": "success",
                "meme_path": abs_path,
                "topic": result.get('topic'),
                "score": result.get('qa', {}).get('engagement_score', '?'),
                "expectation": result.get('meme', {}).get('expectation_text'),
                "reality": result.get('meme', {}).get('reality_text'),
                "time": result.get('time_seconds')
            })
        else:
            return jsonify({"status": "error", "message": "Pipeline returned no output image."}), 500
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ERROR] /generate failed:\n{tb}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": tb
        }), 500

@app.route('/image')
def serve_image():
    path = request.args.get('path')
    if path and os.path.exists(path):
        return send_file(path, mimetype='image/jpeg')
    return "Image not found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"\n  🚀 STARTING CREATOR STUDIO ON PORT {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

