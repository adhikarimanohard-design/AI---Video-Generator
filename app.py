#!/usr/bin/env python3
"""
AI Video Generation Pipeline - Web Application
Flask web interface for generating videos from topics
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
import time
from pathlib import Path
from video_pipeline import VideoGenerationPipeline
import logging

# ----------------------
# Setup
# ----------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-video-pipeline-secret-key'

logging.basicConfig(level=logging.INFO)

# Thread-safe generation status
status_lock = threading.Lock()
generation_status = {
    'status': 'idle',
    'message': 'Ready to generate videos',
    'progress': 0,
    'video_path': None,
    'error': None
}

# ----------------------
# Background video generation
# ----------------------
def generate_video_background(topic):
    """Generate video in background thread"""
    global generation_status

    try:
        with status_lock:
            generation_status = {
                'status': 'running',
                'message': 'Initializing pipeline...',
                'progress': 10,
                'video_path': None,
                'error': None
            }

        pipeline = VideoGenerationPipeline(output_dir="output")

        # Step 1: Generate script
        with status_lock:
            generation_status['message'] = '🎬 Generating AI script...'
            generation_status['progress'] = 25
        script_data = pipeline.step1_generate_script(topic)

        # Step 2: Generate voiceover
        with status_lock:
            generation_status['message'] = '🎙️ Creating voiceover...'
            generation_status['progress'] = 40
        audio_path = pipeline.step2_generate_voiceover(script_data)

        # Step 3: Fetch visuals
        with status_lock:
            generation_status['message'] = '🖼️ Fetching visuals...'
            generation_status['progress'] = 60
        visual_paths = pipeline.step3_fetch_visuals(script_data)

        # Step 4: Combine into video
        with status_lock:
            generation_status['message'] = '🎬 Assembling final video...'
            generation_status['progress'] = 80
        video_path = pipeline.step4_combine_into_video(script_data, audio_path, visual_paths)

        with status_lock:
            if video_path:
                generation_status = {
                    'status': 'completed',
                    'message': '✅ Video ready for download!',
                    'progress': 100,
                    'video_path': video_path,
                    'error': None
                }
            else:
                generation_status = {
                    'status': 'error',
                    'message': '❌ Video generation failed',
                    'progress': 0,
                    'video_path': None,
                    'error': 'Video pipeline returned None'
                }

    except Exception as e:
        with status_lock:
            generation_status = {
                'status': 'error',
                'message': f'❌ Error: {str(e)}',
                'progress': 0,
                'video_path': None,
                'error': str(e)
            }

# ----------------------
# Routes
# ----------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    global generation_status
    logging.info("Received generate request")

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
        generation_status = {
            'status': 'idle',
            'message': 'Ready to generate videos',
            'progress': 0,
            'video_path': None,
            'error': None
        }
    return jsonify({'message': 'Status reset'})

# ----------------------
# No app.run() needed for Render / Gunicorn
# ----------------------
# Just make sure 'output' directory exists
os.makedirs('output', exist_ok=True)