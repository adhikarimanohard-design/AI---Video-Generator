🎬 AI Video Generator – Topic to YouTube-Ready Video

Generate a complete YouTube-ready video from a single topic prompt using AI and free tools.

One input → One automated video pipeline

This project demonstrates how AI, text-to-speech, media APIs, and video processing can be orchestrated into a single end-to-end workflow.

🎥 Demo
📺 YouTube Demo-: https://youtu.be/yKICsgxbH8k?si=_AHyQa-MOHljFuWI


🚀 What This Project Does

You provide a TOPIC, and the system automatically:

Generates a script using AI
Converts the script into a voiceover

Fetches relevant visuals
Combines everything into a final .mp4 video

✅ Output is ready for YouTube / Shorts / Reels

🧠 Pipeline Overview
Copy code

TOPIC
  ↓
AI Script Generation
  ↓
AI Voiceover
  ↓
Visual Fetching
  ↓
Video Assembly (.mp4)

🔧 Pipeline Steps
1️⃣ AI Script Generation

Uses free-tier LLMs (Groq / Gemini )

Generates a structured narration script based on the topic

2️⃣ AI Voiceover
Converts script → speech
Uses:

ElevenLabs (free tier)
Edge-TTS (free)

3️⃣ Visual Generation / Fetching

Fetches relevant stock visuals

4️⃣ Video Assembly
Combines:

Voiceover
Visuals
Transitions

Uses:
MoviePy
FFmpeg
Outputs final .mp4 video

⚡ Trigger Mechanism
One trigger = One video

Trigger options:

Web UI (Flask)

API request
Automation tools like n8n

🛠 Tech Stack-:

Backend: Python, Flask

AI / LLM: Groq / Gemini

Text-to-Speech:

 ElevenLabs, Edge-TTS

Media Processing: MoviePy, FFmpeg

APIs: Pexels
Automation (optional): n8n

Due to free hosting limitations for long-running video generation and FFmpeg, the complete pipeline is demonstrated via video.

⚠️ Hosting Note

This application performs compute-heavy video processing using FFmpeg and MoviePy.

Most free hosting platforms restrict:

background jobs
execution time
media binaries

Therefore:
The app runs fully locally

A full demo video is provided instead of an unstable live deployment


🎯 Use Cases

YouTube automation
Short-form video generation

Educational content creation

AI media pipelines
Workflow automation demos

👨‍💻 Author

Built to demonstrate end-to-end AI automation, media processing, and backend orchestration using free and open tools.