#!/usr/bin/env bash

# Install system dependencies
apt-get update
apt-get install -y ffmpeg

# Upgrade pip
pip install --upgrade pip

# Install Python packages
pip install Flask gunicorn groq requests edge-tts
pip install Pillow==9.5.0
pip install moviepy==1.0.3