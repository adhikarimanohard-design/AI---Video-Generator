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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-video-pipeline-secret-key'

# Global variable for tracking generation status
generation_status = {
    'status': 'idle',
    'message': 'Ready to generate videos',
    'progress': 0,
    'video_path': None,
    'error': None
}

def generate_video_background(topic):
    """Generate video in background thread"""
    global generation_status
    
    try:
        generation_status = {
            'status': 'running',
            'message': 'Initializing pipeline...',
            'progress': 10,
            'video_path': None,
            'error': None
        }
        
        pipeline = VideoGenerationPipeline(output_dir="output")
        
        # Step 1: Generate script
        generation_status['message'] = '🎬 Generating AI script...'
        generation_status['progress'] = 25
        script_data = pipeline.step1_generate_script(topic)
        
        # Step 2: Generate voiceover
        generation_status['message'] = '🎙️ Creating voiceover...'
        generation_status['progress'] = 40
        audio_path = pipeline.step2_generate_voiceover(script_data)
        
        # Step 3: Fetch visuals
        generation_status['message'] = '🖼️ Fetching visuals...'
        generation_status['progress'] = 60
        visual_paths = pipeline.step3_fetch_visuals(script_data)
        
        # Step 4: Combine into video
        generation_status['message'] = '🎬 Assembling final video...'
        generation_status['progress'] = 80
        video_path = pipeline.step4_combine_into_video(
            script_data, 
            audio_path, 
            visual_paths
        )
        
        if video_path:
            generation_status = {
                'status': 'completed',
                'message': '✅ Video ready for download!',
                'progress': 100,
                'video_path': video_path,
                'error': None
            }
        else:
            raise Exception("Video generation failed")
            
    except Exception as e:
        generation_status = {
            'status': 'error',
            'message': f'❌ Error: {str(e)}',
            'progress': 0,
            'video_path': None,
            'error': str(e)
        }

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Start video generation"""
    global generation_status
    
    # Check if already generating
    if generation_status['status'] == 'running':
        return jsonify({'error': 'Video generation already in progress'}), 400
    
    # Get topic from request
    data = request.get_json()
    topic = data.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'Please provide a topic'}), 400
    
    # Start generation in background thread
    thread = threading.Thread(target=generate_video_background, args=(topic,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Video generation started', 'status': 'running'})

@app.route('/status')
def status():
    """Get current generation status"""
    return jsonify(generation_status)

@app.route('/download')
def download():
    """Download the generated video"""
    if generation_status['video_path'] and os.path.exists(generation_status['video_path']):
        return send_file(
            generation_status['video_path'],
            as_attachment=True,
            download_name='ai_generated_video.mp4'
        )
    else:
        return jsonify({'error': 'No video available'}), 404

@app.route('/reset')
def reset():
    """Reset generation status"""
    global generation_status
    generation_status = {
        'status': 'idle',
        'message': 'Ready to generate videos',
        'progress': 0,
        'video_path': None,
        'error': None
    }
    return jsonify({'message': 'Status reset'})

if __name__ == '__main__':
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    print("""
╔══════════════════════════════════════════════════════════╗
║    AI VIDEO GENERATION PIPELINE - WEB SERVER             ║
╚══════════════════════════════════════════════════════════╝

🌐 Server starting on LOCALHOST...
📡 Open your browser and go to:

    http://localhost:5000
    
    or
    
    http://127.0.0.1:5000

Press Ctrl+C to stop the server
""")
    
    # Run on localhost only
    port = int(os.environ.get('PORT', 5000))
app.run(debug=False, host='0.0.0.0', port=port)