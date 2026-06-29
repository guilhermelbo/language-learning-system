"""Unit tests for GenericVoiceHttpService."""
import base64
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from src.infrastructure.omni_service import GenericVoiceHttpService, VoiceServiceUnavailableError
from src.domain.entities import OmniVoiceResult, PronunciationEvent


SAMPLE_AUDIO = b"RIFF\x24\x00\x00\x00WAVEfmt "
SAMPLE_RESPONSE = {
    "audio_base64": base64.b64encode(SAMPLE_AUDIO).decode(),
    "transcript_user": "Hello world",
    "transcript_assistant": "Great pronunciation!",
    "pronunciation_events": [],
}


def _make_http_response(status: int, body: dict) -> httpx.Response:
    return httpx.Response(
        status_code=status,
        content=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )


@pytest.fixture
def service():
    return GenericVoiceHttpService(api_url="http://fake-omni:8003", timeout=5)


@pytest.mark.asyncio
async def test_successful_response_deserialization(service):
    mock_response = _make_http_response(200, SAMPLE_RESPONSE)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await service.process_speech(audio=SAMPLE_AUDIO)

    assert isinstance(result, OmniVoiceResult)
    assert result.transcript_user == "Hello world"
    assert result.transcript_assistant == "Great pronunciation!"
    assert result.pronunciation_events == []
    assert result.audio_bytes == SAMPLE_AUDIO


@pytest.mark.asyncio
async def test_pronunciation_events_deserialised(service):
    body = {
        **SAMPLE_RESPONSE,
        "pronunciation_events": [
            {
                "word": "hello",
                "error_type": "vowel",
                "user_pronunciation": "hɛlo",
                "correct_pronunciation": "həˈloʊ",
                "correction_attempted": False,
                "correction_succeeded": None,
            }
        ],
    }
    mock_response = _make_http_response(200, body)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await service.process_speech(audio=SAMPLE_AUDIO)

    assert len(result.pronunciation_events) == 1
    ev = result.pronunciation_events[0]
    assert isinstance(ev, PronunciationEvent)
    assert ev.word == "hello"
    assert ev.error_type == "vowel"
    assert ev.correction_attempted is False
    assert ev.correction_succeeded is None


@pytest.mark.asyncio
async def test_raises_unavailable_on_connect_error(service):
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("refused"),
    ):
        with pytest.raises(VoiceServiceUnavailableError):
            await service.process_speech(audio=SAMPLE_AUDIO)


@pytest.mark.asyncio
async def test_raises_unavailable_on_timeout(service):
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=httpx.TimeoutException("timeout"),
    ):
        with pytest.raises(VoiceServiceUnavailableError):
            await service.process_speech(audio=SAMPLE_AUDIO)


@pytest.mark.asyncio
async def test_raises_unavailable_on_503(service):
    mock_response = _make_http_response(503, {"detail": "model not loaded"})
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(VoiceServiceUnavailableError):
            await service.process_speech(audio=SAMPLE_AUDIO)


@pytest.mark.asyncio
async def test_raises_unavailable_on_500(service):
    mock_response = _make_http_response(500, {"detail": "internal error"})
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(VoiceServiceUnavailableError):
            await service.process_speech(audio=SAMPLE_AUDIO)


@pytest.mark.asyncio
async def test_health_check_returns_unreachable_on_connection_error(service):
    with patch(
        "httpx.AsyncClient.get",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("refused"),
    ):
        result = await service.health_check()

    assert result["model_loaded"] is False
    assert result["status"] == "unreachable"


@pytest.mark.asyncio
async def test_health_check_returns_model_status(service):
    mock_response = _make_http_response(200, {"status": "ok", "model_loaded": True})
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        result = await service.health_check()

    assert result["model_loaded"] is True
    assert result["status"] == "ok"
