import httpx
from ..domain.interfaces import TTSService

class PiperTTSService(TTSService):
    def __init__(self, api_url: str = "http://localhost:8002"):
        self.api_url = api_url

    async def synthesize(self, text: str) -> bytes:
        async with httpx.AsyncClient() as client:
            try:
                # Piper API expects plain text or JSON
                # Our wrapper expects {"text": "..."} inside Body, 
                # but let's check app.py: synthesize(text: str = Body(..., embed=True))
                # So JSON: {"text": "Hello"}
                
                response = await client.post(
                    f"{self.api_url}/synthesize", 
                    json={"text": text},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.content
            except Exception as e:
                print(f"TTS Service Error: {e}")
                return b""

    async def synthesize_to_file(self, text: str, output_path: str) -> str:
        audio_bytes = await self.synthesize(text)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path
