import io
from faster_whisper import WhisperModel
from ..domain.interfaces import STTService

class FasterWhisperSTTService(STTService):
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        print(f"Loading Faster Whisper model: {model_size} on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Faster Whisper model loaded.")

    async def transcribe(self, audio_data: bytes) -> str:
        # faster-whisper accepts a file-like object
        audio_file = io.BytesIO(audio_data)
        
        segments, info = self.model.transcribe(audio_file, beam_size=5)
        
        text = ""
        for segment in segments:
            text += segment.text
            
        return text.strip()
