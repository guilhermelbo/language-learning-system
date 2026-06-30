"""
GenericVoiceHttpService — HTTP adapter for the ai_services/omni FastAPI service.

Implements OmniVoiceService from the domain layer.
"""
import logging
from typing import AsyncGenerator, Optional

import httpx

from ..domain.interfaces import OmniVoiceService
from ..domain.entities import OmniVoiceResult, PronunciationEvent

logger = logging.getLogger(__name__)


class VoiceServiceUnavailableError(Exception):
    """Raised when the voice model service is unreachable or returns a non-2xx status."""


class GenericVoiceHttpService(OmniVoiceService):
    def __init__(self, api_url: str, timeout: int = 30) -> None:
        self._api_url = api_url.rstrip("/")
        self._timeout = timeout

    async def process_speech(
        self,
        audio: bytes,
        language: str = "en-US",
        context: list | None = None,
    ) -> OmniVoiceResult:
        import json as _json

        context_json = _json.dumps(context) if context else None

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                files = {"file": ("audio.wav", audio, "audio/wav")}
                data: dict = {"language": language}
                if context_json is not None:
                    data["context"] = context_json

                response = await client.post(
                    f"{self._api_url}/omni/speech",
                    files=files,
                    data=data,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Omni service unreachable: %s", exc)
            raise VoiceServiceUnavailableError(str(exc)) from exc

        if response.status_code == 503:
            raise VoiceServiceUnavailableError(
                f"Omni service returned 503: {response.text}"
            )
        if not response.is_success:
            raise VoiceServiceUnavailableError(
                f"Omni service error {response.status_code}: {response.text}"
            )

        payload = response.json()

        import base64
        audio_bytes = base64.b64decode(payload.get("audio_base64", ""))

        raw_events: list[dict] = payload.get("pronunciation_events", [])
        pronunciation_events = [
            PronunciationEvent(
                word=ev.get("word", ""),
                error_type=ev.get("error_type", "other"),
                user_pronunciation=ev.get("user_pronunciation", ""),
                correct_pronunciation=ev.get("correct_pronunciation", ""),
                correction_attempted=ev.get("correction_attempted", False),
                correction_succeeded=ev.get("correction_succeeded", None),
            )
            for ev in raw_events
            if ev.get("word")
        ]

        return OmniVoiceResult(
            audio_bytes=audio_bytes,
            transcript_user=payload.get("transcript_user", ""),
            transcript_assistant=payload.get("transcript_assistant", ""),
            pronunciation_events=pronunciation_events,
        )

    async def process_speech_stream(
        self,
        audio: bytes,
        language: str = "en-US",
        context: list | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Not implemented for the generic HTTP provider — use OpenAICompatibleVoiceService."""
        yield {"event": "error", "data": '{"detail": "streaming not supported by generic provider"}'}
        return

    async def health_check(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self._api_url}/health")
            if response.is_success:
                return response.json()
        except Exception:
            pass
        return {"status": "unreachable", "model_loaded": False}
