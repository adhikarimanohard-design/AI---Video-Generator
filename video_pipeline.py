#!/usr/bin/env python3
"""
AI Video Generation Pipeline - CORRECTED VERSION
Creates YouTube-ready videos from a single topic input

Pipeline steps:
1. AI generates script (Gemini/Groq/Grok free tier)
2. AI voiceover from script (ElevenLabs free/Edge TTS)
3. Fetch/generate visuals (Pexels API/AI images)
4. Combine into .mp4 (FFmpeg/MoviePy)

FIXES:
- Audio now properly attached to video with set_audio()
- Better error handling and debugging
- Duration matching improved
- Audio verification added
"""

import os
import requests
import json
from pathlib import Path
from typing import List, Dict
import subprocess
import time
import sys

# Third-party imports
try:
    from groq import Groq
except ImportError:
    print("Installing required packages...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "groq", "moviepy", "requests", "edge-tts", 
        "--break-system-packages"
    ], check=True)
    from groq import Groq

from PIL import Image

# Pillow >=10 compatibility: MoviePy uses ANTIALIAS internally
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from moviepy.editor import (
    VideoFileClip, AudioFileClip, ImageClip, 
    concatenate_videoclips, CompositeVideoClip
)


class VideoGenerationPipeline:
    """Main pipeline for generating AI videos from topics"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # API keys (set via environment variables)
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.pexels_api_key = os.getenv("PEXELS_API_KEY", "")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
        
        print("\n🔑 API Keys Status:")
        print(f"   Groq: {'✅ Set' if self.groq_api_key else '❌ Not set (will use fallback)'}")
        print(f"   Pexels: {'✅ Set' if self.pexels_api_key else '❌ Not set (will use colored backgrounds)'}")
        print(f"   ElevenLabs: {'✅ Set' if self.elevenlabs_api_key else '❌ Not set (will use Edge TTS)'}")
        
    def step1_generate_script(self, topic: str) -> Dict[str, any]:
        """
        Generate video script using Groq (free tier)
        Returns: dict with script text and scene descriptions
        """
        print(f"\n🎬 Step 1: Generating script for topic: '{topic}'")
        
        if not self.groq_api_key:
            print("⚠️  GROQ_API_KEY not set. Using fallback script.")
            return self._generate_fallback_script(topic)
        
        try:
            client = Groq(api_key=self.groq_api_key)
            
            prompt = f"""Create a 45-60 second video script about: {topic}

Format your response as JSON with this structure:
{{
    "title": "Video Title",
    "script": "Full narration script...",
    "scenes": [
        {{"duration": 8, "description": "Scene description", "text": "Narration for this scene"}},
        {{"duration": 8, "description": "Scene description", "text": "Narration for this scene"}}
    ]
}}

Make it engaging, educational, and suitable for YouTube. Each scene should be 6-10 seconds.
Total duration should be 45-60 seconds. Include 5-8 scenes."""

            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a professional YouTube script writer. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-70b-versatile",
                temperature=0.7,
                max_tokens=1500
            )
            
            script_data = json.loads(response.choices[0].message.content)
            print(f"✅ Script generated: {script_data['title']}")
            print(f"   Scenes: {len(script_data['scenes'])}")
            
            # Calculate total duration
            total_duration = sum(scene['duration'] for scene in script_data['scenes'])
            print(f"   Total duration: {total_duration} seconds")
            
            return script_data
            
        except Exception as e:
            print(f"❌ Error generating script: {e}")
            return self._generate_fallback_script(topic)
    
    def _generate_fallback_script(self, topic: str) -> Dict:
        """Fallback script if API fails"""
        return {
            "title": f"Everything About {topic}",
            "script": f"Welcome to our video about {topic}. This is a fascinating subject that many people want to learn about. {topic} has a rich history and many interesting aspects. Let's explore the key concepts together. Understanding {topic} can open up new possibilities. Thank you for watching this video about {topic}.",
            "scenes": [
                {"duration": 10, "description": f"intro to {topic}", "text": f"Welcome to our video about {topic}."},
                {"duration": 10, "description": f"{topic} history", "text": f"This is a fascinating subject that many people want to learn about. {topic} has a rich history."},
                {"duration": 10, "description": f"{topic} concepts", "text": "Let's explore the key concepts together."},
                {"duration": 10, "description": f"{topic} applications", "text": f"Understanding {topic} can open up new possibilities."},
                {"duration": 10, "description": f"{topic} conclusion", "text": f"Thank you for watching this video about {topic}."}
            ]
        }
    
    def step2_generate_voiceover(self, script_data: Dict, output_path: str = None) -> str:
        """
        Generate voiceover using Edge TTS (free) or ElevenLabs
        Returns: path to audio file
        """
        print("\n🎙️  Step 2: Generating voiceover")
        
        if output_path is None:
            output_path = self.output_dir / "voiceover.mp3"
        
        full_script = script_data["script"]
        print(f"   Script length: {len(full_script)} characters")
        
        # Try ElevenLabs if API key is available
        if self.elevenlabs_api_key:
            try:
                result = self._generate_elevenlabs_audio(full_script, output_path)
                if result:
                    return result
            except Exception as e:
                print(f"⚠️  ElevenLabs failed: {e}. Falling back to Edge TTS.")
        
        # Use Edge TTS as free alternative
        return self._generate_edge_tts_audio(full_script, output_path)
    
    def _generate_edge_tts_audio(self, text: str, output_path: str) -> str:
        """Generate audio using Microsoft Edge TTS (free)"""
        try:
            import asyncio
            import edge_tts
            
            print("   Using Edge TTS (free)...")
            
            async def generate():
                # Available voices: en-US-GuyNeural (male), en-US-JennyNeural (female)
                communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
                await communicate.save(str(output_path))
            
            asyncio.run(generate())
            
            # Verify audio file was created and has content
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ Voiceover generated: {output_path}")
                print(f"   File size: {file_size:,} bytes")
                
                if file_size < 1000:
                    print("⚠️  Warning: Audio file is very small, may be empty")
                    raise Exception("Audio file too small")
                
                # Get audio duration using ffprobe
                try:
                    result = subprocess.run(
                        ['ffprobe', '-v', 'error', '-show_entries', 
                         'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                         str(output_path)],
                        capture_output=True,
                        text=True
                    )
                    duration = float(result.stdout.strip())
                    print(f"   Audio duration: {duration:.2f} seconds")
                except:
                    print("   Could not determine audio duration (ffprobe not available)")
                
                return str(output_path)
            else:
                raise Exception("Audio file was not created")
            
        except Exception as e:
            print(f"❌ Edge TTS error: {e}")
            # Create silent audio as fallback
            print("   Creating silent audio fallback...")
            return self._create_silent_audio(output_path, duration=45)
    
    def _generate_elevenlabs_audio(self, text: str, output_path: str) -> str:
        """Generate audio using ElevenLabs API"""
        print("   Using ElevenLabs API...")
        
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(output_path)
            print(f"✅ ElevenLabs voiceover generated: {output_path}")
            print(f"   File size: {file_size:,} bytes")
            return str(output_path)
        else:
            raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")
    
    def _create_silent_audio(self, output_path: str, duration: int = 45) -> str:
        """Create silent audio file as fallback"""
        print(f"   Creating {duration}s silent audio...")
        try:
            cmd = [
                "ffmpeg", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
                "-t", str(duration), "-q:a", "9", "-acodec", "libmp3lame",
                str(output_path), "-y"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Silent audio created: {output_path}")
                return str(output_path)
            else:
                print(f"❌ FFmpeg error: {result.stderr}")
                raise Exception("Failed to create silent audio")
        except Exception as e:
            print(f"❌ Could not create silent audio: {e}")
            raise
    
    def step3_fetch_visuals(self, script_data: Dict) -> List[str]:
        """
        Fetch visuals from Pexels API or generate with AI
        Returns: list of video/image file paths
        """
        print("\n🖼️  Step 3: Fetching visuals")
        
        visual_paths = []
        
        for i, scene in enumerate(script_data["scenes"]):
            search_query = scene["description"]
            visual_path = self.output_dir / f"visual_{i}.mp4"
            
            # Try Pexels first
            if self.pexels_api_key:
                try:
                    video_url = self._search_pexels_video(search_query)
                    if video_url:
                        self._download_file(video_url, visual_path)
                        visual_paths.append(str(visual_path))
                        print(f"✅ Downloaded visual {i+1}/{len(script_data['scenes'])}: {search_query}")
                        time.sleep(0.5)  # Rate limiting
                        continue
                except Exception as e:
                    print(f"⚠️  Pexels failed for scene {i}: {e}")
            
            # Fallback: create colored background
            self._create_colored_background(visual_path, scene["text"], i)
            visual_paths.append(str(visual_path))
            print(f"✅ Created fallback visual {i+1}/{len(script_data['scenes'])}")
        
        return visual_paths
    
    def _search_pexels_video(self, query: str) -> str:
        """Search Pexels for video"""
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": self.pexels_api_key}
        params = {"query": query, "per_page": 1, "size": "medium", "orientation": "landscape"}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("videos"):
                video_files = data["videos"][0]["video_files"]
                # Get best quality video that's not too large
                for vf in video_files:
                    if vf["quality"] in ["hd", "sd"] and vf["width"] >= 1280:
                        return vf["link"]
        
        return None
    
    def _download_file(self, url: str, output_path: str):
        """Download file from URL"""
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    
    def _create_colored_background(self, output_path: str, text: str, index: int):
        """Create a simple colored background video with text"""
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", "#F38181", "#AA96DA"]
        color = colors[index % len(colors)]
        
        # Clean text for ffmpeg (escape special characters)
        clean_text = text.replace("'", "").replace('"', '').replace(':', ' ')[:80]
        
        # Create 8-second video with colored background
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c={color}:s=1920x1080:d=8",
                "-vf", f"drawtext=text='{clean_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "-pix_fmt", "yuv420p", "-r", "24",
                str(output_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                # If text drawing fails, create simple colored background
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i", f"color=c={color}:s=1920x1080:d=8",
                    "-pix_fmt", "yuv420p", "-r", "24",
                    str(output_path)
                ]
                subprocess.run(cmd, capture_output=True, check=True)
        except Exception as e:
            print(f"⚠️  Error creating colored background: {e}")
    
    def step4_combine_into_video(
        self, 
        script_data: Dict, 
        audio_path: str, 
        visual_paths: List[str],
        output_path: str = None
    ) -> str:
        """
        Combine audio and visuals into final MP4
        Returns: path to final video
        """
        print("\n🎬 Step 4: Combining into final video")
        
        if output_path is None:
            timestamp = int(time.time())
            output_path = self.output_dir / f"final_video_{timestamp}.mp4"
        
        try:
            # Load audio
            print("   Loading audio...")
            audio = AudioFileClip(audio_path)
            audio_duration = audio.duration
            print(f"   📊 Audio duration: {audio_duration:.2f} seconds")
            
            if audio_duration < 5:
                print("⚠️  Warning: Audio is very short. This may indicate a problem.")
            
            # Load and resize visual clips
            print("   Loading visual clips...")
            clips = []
            cumulative_duration = 0
            
            for i, visual_path in enumerate(visual_paths):
                try:
                    print(f"      Loading visual {i+1}/{len(visual_paths)}...")
                    clip = VideoFileClip(visual_path)
                    
                    # Get scene duration from script
                    scene_duration = script_data["scenes"][i]["duration"]
                    
                    # Trim or loop clip to match scene duration
                    if clip.duration > scene_duration:
                        clip = clip.subclip(0, scene_duration)
                    elif clip.duration < scene_duration:
                        # Loop the clip
                        loops_needed = int(scene_duration / clip.duration) + 1
                        clip = concatenate_videoclips([clip] * loops_needed).subclip(0, scene_duration)
                    
                    # Resize to 1080p maintaining aspect ratio
                    clip = clip.resize(height=1080)
                    
                    clips.append(clip)
                    cumulative_duration += clip.duration
                    print(f"      ✓ Visual {i+1} loaded: {clip.duration:.2f}s")
                    
                except Exception as e:
                    print(f"      ⚠️  Error loading visual {i}: {e}")
                    continue
            
            if not clips:
                print("❌ No valid video clips found")
                audio.close()
                return None
            
            print(f"   📊 Total video clips duration: {cumulative_duration:.2f} seconds")
            
            # Concatenate all clips
            print("   Concatenating video clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            print(f"   📊 Concatenated video duration: {final_video.duration:.2f} seconds")
            
            # Match video duration to audio
            if final_video.duration < audio_duration:
                print(f"   ⚙️  Video shorter than audio. Looping video...")
                # Loop video to match audio
                loops_needed = int(audio_duration / final_video.duration) + 1
                final_video = concatenate_videoclips([final_video] * loops_needed)
                final_video = final_video.subclip(0, audio_duration)
            elif final_video.duration > audio_duration:
                print(f"   ⚙️  Video longer than audio. Trimming video...")
                final_video = final_video.subclip(0, audio_duration)
            
            print(f"   📊 Final video duration (before audio): {final_video.duration:.2f} seconds")
            
            # **CRITICAL FIX: Set audio on the video clip**
            print("   🔊 Attaching audio to video...")
            final_video = final_video.set_audio(audio)
            
            print(f"   📊 Final video duration (with audio): {final_video.duration:.2f} seconds")
            print(f"   📊 Audio track duration: {final_video.audio.duration:.2f} seconds")
            
            # Write final video with audio
            print(f"   💾 Writing final video to: {output_path}")
            print("   ⏳ This may take a few minutes...")
            
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=24,
                preset='medium',
                audio_bitrate='192k',
                bitrate='5000k',
                threads=4
            )
            
            # Verify output file
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"\n✅ Final video created successfully!")
                print(f"   Path: {output_path}")
                print(f"   Size: {file_size / (1024*1024):.2f} MB")
                
                # Verify audio in output
                try:
                    result = subprocess.run(
                        ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                         '-show_entries', 'stream=codec_name', '-of', 
                         'default=noprint_wrappers=1:nokey=1', str(output_path)],
                        capture_output=True,
                        text=True
                    )
                    if result.stdout.strip():
                        print(f"   Audio codec: {result.stdout.strip()}")
                        print("   ✅ Audio track verified in output video!")
                    else:
                        print("   ⚠️  Warning: No audio track detected in output")
                except:
                    pass
            
            # Clean up
            print("   🧹 Cleaning up resources...")
            audio.close()
            final_video.close()
            for clip in clips:
                clip.close()
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error combining video: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to clean up
            try:
                if 'audio' in locals():
                    audio.close()
                if 'final_video' in locals():
                    final_video.close()
                if 'clips' in locals():
                    for clip in clips:
                        clip.close()
            except:
                pass
            
            return None
    
    def generate_video(self, topic: str) -> str:
        """
        Main function: Generate complete video from topic
        Returns: path to final video
        """
        print(f"\n{'='*60}")
        print(f"🚀 AI VIDEO GENERATION PIPELINE")
        print(f"{'='*60}")
        print(f"Topic: {topic}")
        
        try:
            # Step 1: Generate script
            script_data = self.step1_generate_script(topic)
            
            # Save script to file
            script_path = self.output_dir / "script.json"
            with open(script_path, 'w') as f:
                json.dump(script_data, f, indent=2)
            print(f"📝 Script saved to: {script_path}")
            
            # Step 2: Generate voiceover
            audio_path = self.step2_generate_voiceover(script_data)
            
            # Step 3: Fetch visuals
            visual_paths = self.step3_fetch_visuals(script_data)
            
            # Step 4: Combine into final video
            final_video_path = self.step4_combine_into_video(
                script_data, 
                audio_path, 
                visual_paths
            )
            
            if final_video_path:
                print(f"\n{'='*60}")
                print(f"🎉 SUCCESS! Video generated!")
                print(f"{'='*60}")
                print(f"📹 Video: {final_video_path}")
                print(f"📝 Script: {script_path}")
                print(f"{'='*60}\n")
                
                # Bonus: Generate metadata
                self._generate_metadata(script_data, final_video_path)
                
                return final_video_path
            else:
                print("\n❌ Video generation failed in final step")
                return None
                
        except Exception as e:
            print(f"\n❌ Fatal error in video generation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_metadata(self, script_data: Dict, video_path: str):
        """Bonus: Generate YouTube metadata"""
        metadata = {
            "title": script_data["title"],
            "description": script_data["script"],
            "tags": ["AI Generated", "Educational", "Tutorial", "Automated Video"],
            "category": "Education",
            "thumbnail_suggestion": "Create custom thumbnail with title text",
            "video_path": video_path,
            "duration_seconds": sum(scene['duration'] for scene in script_data['scenes']),
            "scenes": len(script_data['scenes'])
        }
        
        metadata_path = self.output_dir / "youtube_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📊 YouTube metadata saved to: {metadata_path}")


def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    missing = []
    
    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        if result.returncode == 0:
            print("   ✅ FFmpeg installed")
        else:
            missing.append("FFmpeg")
    except FileNotFoundError:
        missing.append("FFmpeg")
        print("   ❌ FFmpeg not found")
    
    # Check Python packages
    packages = ['groq', 'moviepy', 'requests', 'edge_tts', 'PIL']
    for package in packages:
        try:
            if package == 'PIL':
                import PIL
            else:
                __import__(package)
            print(f"   ✅ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"   ❌ {package} not found")
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("   Run: pip install groq moviepy requests edge-tts pillow --break-system-packages")
        if 'FFmpeg' in missing:
            print("   Install FFmpeg: sudo apt install ffmpeg")
        return False
    
    print("   ✅ All dependencies installed!")
    return True


def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════╗
║      AI VIDEO GENERATION PIPELINE v2.0                   ║
║      Build YouTube-Ready Videos from Topics              ║
║      🔊 AUDIO FIXED VERSION 🔊                           ║
╚══════════════════════════════════════════════════════════╝

Setup Instructions:
1. Set environment variables (optional but recommended):
   export GROQ_API_KEY="your_groq_api_key"
   export PEXELS_API_KEY="your_pexels_api_key"
   export ELEVENLABS_API_KEY="your_elevenlabs_api_key"

2. Get free API keys:
   - Groq: https://console.groq.com/
   - Pexels: https://www.pexels.com/api/
   - ElevenLabs: https://elevenlabs.io/ (optional)

3. Install FFmpeg: 
   - Ubuntu/Debian: sudo apt install ffmpeg
   - Mac: brew install ffmpeg
   - Windows: Download from ffmpeg.org
""")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first!")
        return
    
    # Example usage
    print("\n" + "="*60)
    topic = input("🎬 Enter your video topic: ").strip()
    
    if not topic:
        topic = "The History of Artificial Intelligence"
        print(f"Using default topic: {topic}")
    
    print("="*60)
    
    try:
        pipeline = VideoGenerationPipeline()
        video_path = pipeline.generate_video(topic)
        
        if video_path:
            print(f"\n{'='*60}")
            print("🎉 VIDEO GENERATION COMPLETE!")
            print(f"{'='*60}")
            print(f"Your video is ready at: {video_path}")
            print("\nNext steps:")
            print("1. Review the video")
            print("2. Create a custom thumbnail")
            print("3. Check youtube_metadata.json for upload details")
            print("4. Upload to YouTube!")
            print(f"{'='*60}\n")
        else:
            print("\n❌ Video generation failed. Check the errors above.")
            print("Common issues:")
            print("- Missing FFmpeg installation")
            print("- Invalid API keys")
            print("- Insufficient disk space")
            print("- Network connectivity issues")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
