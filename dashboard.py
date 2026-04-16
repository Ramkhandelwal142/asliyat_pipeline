from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
from pathlib import Path
import threading

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import run

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    topic = data.get('topic', '')
    if not topic.strip():
        topic = None
    no_research = data.get('fast_mode', True)
    
    try:
        # Run the pipeline
        result = run(topic=topic, no_research=no_research)
        if result and result.get('output'):
            # Convert to absolute path so flask can serve it
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
            return jsonify({"status": "error", "message": "Pipeline failed to output an image."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
