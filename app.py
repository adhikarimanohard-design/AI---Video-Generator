#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
from video_pipeline import VideoGenerationPipeline
import logging
import queue
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-video-pipeline-secret-key'

logging.basicConfig(level=logging.INFO)

# Ensure output folder exists
os.makedirs('output', exist_ok=True)

# Thread-safe generation status with a queue for updates
status_lock = threading.Lock()
generation_status = {
    'status': 'idle',
    'message': 'Ready to generate videos',
    'progress': 0,
    'video_path': None,
    'error': None
}

# Queue to communicate progress updates safely
progress_queue = queue.Queue()

# ----------------------
# Auto delete generated video
# ----------------------
def delete_file_later(file_path, delay=120):
    def delete():
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"🗑 Deleted file: {file_path}")
        except Exception as e:
            logging.error(f"Delete error: {e}")

    timer = threading.Timer(delay, delete)
    timer.daemon = True
    timer.start()

# ----------------------
# Background video generation
# ----------------------
def generate_video_background(topic):
    global generation_status

    try:
        with status_lock:
            generation_status.update({
                'status': 'running',
                'message': 'Initializing pipeline...',
                'progress': 5,
                'video_path': None,
                'error': None
            })

        pipeline = VideoGenerationPipeline(output_dir="output")

        # Step 1: Script
        with status_lock:
            generation_status.update({'message': '🎬 Generating AI script...', 'progress': 10})
        script_data = pipeline.step1_generate_script(topic)

        # Step 2: Voiceover
        with status_lock:
            generation_status.update({'message': '🎙️ Creating voiceover...', 'progress': 35})
        audio_path = pipeline.step2_generate_voiceover(script_data)

        # Step 3: Visuals
        with status_lock:
            generation_status.update({'message': '🖼️ Fetching visuals...', 'progress': 60})
        visual_paths = pipeline.step3_fetch_visuals(script_data)

        # Step 4: Combine video
        with status_lock:
            generation_status.update({'message': '🎬 Assembling final video...', 'progress': 80})
        video_path = pipeline.step4_combine_into_video(script_data, audio_path, visual_paths)

        with status_lock:
            if video_path:
                generation_status.update({
                    'status': 'completed',
                    'message': '✅ Video ready for download!',
                    'progress': 100,
                    'video_path': video_path,
                    'error': None
                })
                delete_file_later(video_path, 120)
            else:
                generation_status.update({
                    'status': 'error',
                    'message': '❌ Video generation failed',
                    'progress': 0,
                    'video_path': None,
                    'error': 'Video pipeline returned None'
                })

    except Exception as e:
        with status_lock:
            generation_status.update({
                'status': 'error',
                'message': f'❌ Error: {str(e)}',
                'progress': 0,
                'video_path': None,
                'error': str(e)
            })

# ----------------------
# Routes
# ----------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    global generation_status

    with status_lock:
        if generation_status['status'] == 'running':
            return jsonify({'error': 'Video generation already in progress'}), 400

    data = request.get_json()
    topic = data.get('topic', '').strip()

    if not topic:
        return jsonify({'error': 'Please provide a topic'}), 400

    thread = threading.Thread(target=generate_video_background, args=(topic,))
    thread.daemon = True
    thread.start()

    return jsonify({'message': 'Video generation started', 'status': 'running'})


@app.route('/status')
def status():
    try:
        with status_lock:
            return jsonify(generation_status)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/download')
def download():
    with status_lock:
        video_path = generation_status.get('video_path')

    if video_path and os.path.exists(video_path):
        return send_file(video_path, as_attachment=True, download_name='ai_generated_video.mp4')
    else:
        return jsonify({'error': 'No video available'}), 404


@app.route('/reset')
def reset():
    global generation_status
    with status_lock:
        generation_status.update({
            'status': 'idle',
            'message': 'Ready to generate videos',
            'progress': 0,
            'video_path': None,
            'error': None
        })
    return jsonify({'message': 'Status reset'})


# ----------------------
# Run server (Render compatible)
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)