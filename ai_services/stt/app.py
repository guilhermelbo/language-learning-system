from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import os
import shutil

app = FastAPI()

# Load model on startup
MODEL_SIZE = os.environ.get("WHISPER_MODEL", "small")
DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE", "int8")

print(f"Loading Whisper model: {MODEL_SIZE} on {DEVICE}...")
model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
print("Model loaded.")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        segments, info = model.transcribe(temp_filename, beam_size=5)
        text = "".join([segment.text for segment in segments])
        return {"text": text.strip(), "language": info.language}
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
