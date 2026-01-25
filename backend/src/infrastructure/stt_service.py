import httpx
from ..domain.interfaces import STTService

class FasterWhisperSTTService(STTService):
    def __init__(self, api_url: str = "http://localhost:8001"):
        self.api_url = api_url

    async def transcribe(self, audio_data: bytes) -> str:
        async with httpx.AsyncClient() as client:
            files = {'file': ('audio.webm', audio_data, 'audio/webm')}
            try:
                response = await client.post(f"{self.api_url}/transcribe", files=files, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                return result.get("text", "")
            except httpx.RequestError as e:
                print(f"STT Service Error: {e}")
                # Fallback or re-raise
                return ""
