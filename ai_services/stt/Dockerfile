FROM python:3.10-slim

# Install system dependencies (needed for soundfile/librosa usually used by whisper)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install faster-whisper fastapi uvicorn python-multipart

COPY app.py /app/app.py
WORKDIR /app

# Run the API
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
