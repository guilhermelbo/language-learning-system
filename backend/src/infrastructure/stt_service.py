import httpx
import logging
from ..domain.interfaces import STTService

logger = logging.getLogger(__name__)

class FasterWhisperSTTService(STTService):
    def __init__(self, api_url: str = "http://localhost:8001"):
        self.api_url = api_url

    async def transcribe(self, audio_data: bytes) -> str:
        async with httpx.AsyncClient() as client:
            files = {'file': ('audio.webm', audio_data, 'audio/webm')}
            try:
                logger.debug(f"Sending {len(audio_data)} bytes to STT service at {self.api_url}")
                response = await client.post(f"{self.api_url}/transcribe", files=files, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                text = result.get("text", "")
                logger.debug(f"STT Service response: {text}")
                return text
            except httpx.RequestError as e:
                logger.error(f"STT Service Error: {e}")
                # Fallback or re-raise
                return ""
