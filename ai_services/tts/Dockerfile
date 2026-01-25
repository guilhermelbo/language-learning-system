FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Download Piper (2023.11.14-2)
RUN curl -L -o piper.tar.gz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz && \
    tar -xvf piper.tar.gz && \
    rm piper.tar.gz

# Install Python API dependencies
RUN pip install fastapi uvicorn

COPY app.py /app/app.py

# Models directory
RUN mkdir /models && \
    curl -L -o /models/pt_BR-faber-medium.onnx https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx && \
    curl -L -o /models/pt_BR-faber-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json && \
    curl -L -o /models/en_US-lessac-medium.onnx https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    curl -L -o /models/en_US-lessac-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Add piper to path locally or call it directly. 
# In app.py we call "piper", so let's add to PATH
ENV PATH="/app/piper:${PATH}"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
