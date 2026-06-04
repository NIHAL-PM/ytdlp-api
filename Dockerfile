# Use a modern, stable Python image (Debian based)
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose Deno's installation path to the global system environment
ENV PATH="/root/.deno/bin:$PATH"

# Install critical system tools (FFmpeg for media processing, Curl/Unzip for Deno)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno (The lightweight sandboxed JS runtime required by yt-dlp to solve anti-bot scripts)
RUN curl -fsSL https://deno.land/install.sh | sh

# Set our work environment directory
WORKDIR /app

# Install optimized pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy over the updated main.py file
COPY . .

# Expose FastAPI's custom communication port
EXPOSE 1337

# Run our app asynchronously natively via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "1337"]
