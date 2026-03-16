# Use lightweight Python image
FROM python:3.11-slim

# -------------------------
# System dependencies
# -------------------------
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libjpeg-dev \
    zlib1g-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Set app directory
# -------------------------
WORKDIR /app

# -------------------------
# Python dependencies
# -------------------------
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# -------------------------
# Copy source code
# -------------------------
COPY . .

# -------------------------
# Expose port (Render uses PORT env)
# -------------------------
ENV PORT=5000
EXPOSE 5000

# -------------------------
# Run Flask app with Gunicorn
# -------------------------
CMD gunicorn app:app --bind 0.0.0.0:${PORT} --workers 2 --threads 4