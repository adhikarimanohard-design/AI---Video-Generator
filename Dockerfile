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
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# App directory
# -------------------------
WORKDIR /app

# -------------------------
# Python dependencies
# -------------------------
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# -------------------------
# Copy app source
# -------------------------
COPY . .

# -------------------------
# Render / Fly use PORT env var
# -------------------------
CMD sh -c "gunicorn app:app --bind 0.0.0.0:${PORT}"