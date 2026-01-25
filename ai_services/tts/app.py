from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import Response
import subprocess
import os
import io

app = FastAPI()

# Configuration
# Assuming we mount models to /models
# Default model: pt_BR-faber-medium.onnx
MODEL_PATH = os.environ.get("PIPER_MODEL_PATH", "/models/pt_BR-faber-medium.onnx")

@app.post("/synthesize")
async def synthesize(text: str = Body(..., embed=True)):
    # Invoke Piper CLI
    # echo "text" | piper --model model.onnx --output_file output.wav
    
    try:
        process = subprocess.Popen(
            ["piper", "--model", MODEL_PATH, "--output_file", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        wav_data, stderr = process.communicate(input=text.encode("utf-8"))
        
        if process.returncode != 0:
            print(f"Piper error: {stderr.decode()}")
            return Response(content=f"Error: {stderr.decode()}", status_code=500)
            
        return Response(content=wav_data, media_type="audio/wav")
        
    except Exception as e:
        return Response(content=str(e), status_code=500)
