import httpx
import logging
from ..domain.interfaces import TTSService

logger = logging.getLogger(__name__)

class PiperTTSService(TTSService):
    def __init__(self, api_url: str = "http://localhost:8002"):
        self.api_url = api_url

    async def synthesize(self, text: str, lang: str = "pt") -> bytes:
        async with httpx.AsyncClient() as client:
            try:
                # Piper API expects plain text or JSON
                # Our wrapper expects {"text": "..."} inside Body, 
                # but let's check app.py: synthesize(text: str = Body(..., embed=True))
                # So JSON: {"text": "Hello"}
                
                logger.debug(f"Synthesizing audio for text: '{text[:20]}...' at {self.api_url} with lang {lang}")
                response = await client.post(
                    f"{self.api_url}/synthesize", 
                    json={"text": text},
                    params={"lang": lang},
                    timeout=30.0
                )
                response.raise_for_status()
                logger.debug(f"TTS synthesis successful, received {len(response.content)} bytes")
                return response.content
            except Exception as e:
                logger.error(f"TTS Service Error: {e}")
                return b""

    async def synthesize_to_file(self, text: str, output_path: str) -> str:
        audio_bytes = await self.synthesize(text)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path
