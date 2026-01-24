import wave
import io
import json
from ..domain.interfaces import TTSService

# Note: Ideally we would use the 'piper' python package directly if available and compatible.
# For this MVP, we will assume we can invoke it or use a simplified python wrapper.
# If 'piper-tts' package provides PiperVoice, we use it. 
# Else, we might need to use subprocess. 
# Here is a standard implementation using the `piper` package structure:

try:
    from piper import PiperVoice
except ImportError:
    PiperVoice = None

class PiperTTSService(TTSService):
    def __init__(self, model_path: str, config_path: str = None, use_cuda: bool = False):
        if PiperVoice is None:
            raise ImportError("piper package not found. Please install piper-tts.")
        
        # PiperVoice.load automatically looks for .json if config_path is None
        self.voice = PiperVoice.load(model_path, config_path=config_path, use_cuda=use_cuda)

    async def synthesize(self, text: str) -> bytes:
        # Piper synthesize writes to a wav file object
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wav_file:
             self.voice.synthesize(text, wav_file)
        
        return wav_io.getvalue()

    async def synthesize_to_file(self, text: str, output_path: str) -> str:
        with wave.open(output_path, "wb") as wav_file:
            self.voice.synthesize(text, wav_file)
        return output_path
