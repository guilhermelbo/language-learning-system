"""Unit tests for OpenAICompatibleVoiceService (native audio via input_audio)."""
import base64
import json
import pytest
from unittest.mock import AsyncMock, patch

import httpx

from src.infrastructure.llm_voice_service import (
    OpenAICompatibleVoiceService,
    _extract_pronunciation_events,
    _extract_user_transcript,
)
from src.infrastructure.omni_service import VoiceServiceUnavailableError
from src.domain.entities import OmniVoiceResult


SAMPLE_AUDIO = b"RIFF\x24\x00\x00\x00WAVEfmt "
SAMPLE_WAV = b"RIFF\x28\x00\x00\x00WAVEfmt \x10\x00\x00\x00"


def _llm_response(content: str, status: int = 200) -> httpx.Response:
    body = {"choices": [{"message": {"role": "assistant", "content": content}}]}
    return httpx.Response(
        status_code=status,
        content=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )


def _error_response(status: int, detail: str = "error") -> httpx.Response:
    return httpx.Response(
        status_code=status,
        content=json.dumps({"error": detail}).encode(),
        headers={"content-type": "application/json"},
    )


def _tts_response(wav: bytes = SAMPLE_WAV, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status,
        content=wav,
        headers={"content-type": "audio/wav"},
    )


@pytest.fixture
def service():
    return OpenAICompatibleVoiceService(
        base_url="http://fake-llamacpp:8080/v1",
        model="gemma-test.gguf",
        api_key=None,
        tts_api_url="http://fake-tts:8002",
        timeout=5,
    )


# ---------------------------------------------------------------------------
# Helpers: _extract_pronunciation_events
# ---------------------------------------------------------------------------

def test_extract_pronunciation_events_with_events():
    text = (
        "Your pronunciation was mostly good! "
        "<!-- PRONUNCIATION_EVENTS: ["
        '{"word": "world", "error_type": "vowel", '
        '"user_pronunciation": "wurld", "correct_pronunciation": "wɜːrld"}'
        "] -->"
    )
    clean, events = _extract_pronunciation_events(text)
    assert clean == "Your pronunciation was mostly good!"
    assert len(events) == 1
    assert events[0]["word"] == "world"
    assert events[0]["error_type"] == "vowel"


def test_extract_pronunciation_events_no_block():
    text = "Great job! Keep practicing."
    clean, events = _extract_pronunciation_events(text)
    assert clean == text
    assert events == []


def test_extract_pronunciation_events_empty_array():
    text = "Perfect! <!-- PRONUNCIATION_EVENTS: [] -->"
    clean, events = _extract_pronunciation_events(text)
    assert clean == "Perfect!"
    assert events == []


# ---------------------------------------------------------------------------
# Helpers: _extract_user_transcript
# ---------------------------------------------------------------------------

def test_extract_user_transcript_present():
    text = "Nice try! <!-- USER_TRANSCRIPT: hello world --> <!-- PRONUNCIATION_EVENTS: [] -->"
    assert _extract_user_transcript(text) == "hello world"


def test_extract_user_transcript_absent():
    text = "Nice try! <!-- PRONUNCIATION_EVENTS: [] -->"
    assert _extract_user_transcript(text) == ""


# ---------------------------------------------------------------------------
# process_speech: happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_speech_success(service):
    llm_content = (
        "Great pronunciation! "
        "<!-- USER_TRANSCRIPT: hello world --> "
        "<!-- PRONUNCIATION_EVENTS: [] -->"
    )
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=[_llm_response(llm_content), _tts_response()],
    ):
        result = await service.process_speech(audio=SAMPLE_AUDIO, language="en-US", context=None)

    assert isinstance(result, OmniVoiceResult)
    assert result.transcript_user == "hello world"
    assert result.transcript_assistant == "Great pronunciation!"
    assert result.audio_bytes == SAMPLE_WAV
    assert result.pronunciation_events == []


@pytest.mark.asyncio
async def test_process_speech_with_pronunciation_events(service):
    llm_content = (
        "Watch your vowel on 'world'. "
        "<!-- USER_TRANSCRIPT: I live in the wurld --> "
        "<!-- PRONUNCIATION_EVENTS: ["
        '{"word": "world", "error_type": "vowel", '
        '"user_pronunciation": "wurld", "correct_pronunciation": "wɜːrld"}'
        "] -->"
    )
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=[_llm_response(llm_content), _tts_response()],
    ):
        result = await service.process_speech(audio=SAMPLE_AUDIO, language="en-US", context=None)

    assert result.transcript_user == "I live in the wurld"
    assert len(result.pronunciation_events) == 1
    assert result.pronunciation_events[0].word == "world"
    assert result.pronunciation_events[0].error_type == "vowel"


# ---------------------------------------------------------------------------
# process_speech: audio sent as base64 input_audio
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audio_base64_in_request(service):
    """Verify LLM request contains base64 audio in input_audio content block."""
    llm_content = "Good job! <!-- USER_TRANSCRIPT: hi --> <!-- PRONUNCIATION_EVENTS: [] -->"
    captured = []

    async def fake_post(url, **kwargs):
        captured.append((url, kwargs))
        if "chat" in url:
            return _llm_response(llm_content)
        return _tts_response()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=fake_post):
        await service.process_speech(audio=SAMPLE_AUDIO, language="en-US", context=None)

    llm_call = next(c for c in captured if "chat/completions" in c[0])
    messages = llm_call[1]["json"]["messages"]

    # Last user message should have input_audio content block
    user_msg = messages[-1]
    assert user_msg["role"] == "user"
    assert isinstance(user_msg["content"], list)

    audio_block = next(b for b in user_msg["content"] if b["type"] == "input_audio")
    expected_b64 = base64.b64encode(SAMPLE_AUDIO).decode("utf-8")
    assert audio_block["input_audio"]["data"] == expected_b64
    assert audio_block["input_audio"]["format"] == "wav"


# ---------------------------------------------------------------------------
# process_speech: context (multi-turn)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_speech_with_context(service):
    """Prior-turn context appears as text messages before the current audio message."""
    context = [
        {"role": "user", "content": "Hello teacher"},
        {"role": "assistant", "content": "Hello! Great to meet you."},
    ]
    llm_content = "I'm well! <!-- USER_TRANSCRIPT: how are you --> <!-- PRONUNCIATION_EVENTS: [] -->"
    captured = []

    async def fake_post(url, **kwargs):
        captured.append((url, kwargs))
        if "chat" in url:
            return _llm_response(llm_content)
        return _tts_response()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=fake_post):
        await service.process_speech(audio=SAMPLE_AUDIO, language="en-US", context=context)

    llm_call = next(c for c in captured if "chat/completions" in c[0])
    messages = llm_call[1]["json"]["messages"]

    assert messages[0]["role"] == "system"
    # Prior turns as text
    assert any(
        m.get("role") == "user" and m.get("content") == "Hello teacher"
        for m in messages
    )
    assert any(
        m.get("role") == "assistant" and m.get("content") == "Hello! Great to meet you."
        for m in messages
    )
    # Current turn is last and multimodal
    assert messages[-1]["role"] == "user"
    assert isinstance(messages[-1]["content"], list)


# ---------------------------------------------------------------------------
# process_speech: error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_speech_llm_failure_non2xx(service):
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=_error_response(503),
    ):
        with pytest.raises(VoiceServiceUnavailableError):
            await service.process_speech(audio=SAMPLE_AUDIO, language="en-US", context=None)


@pytest.mark.asyncio
async def test_process_speech_llm_connect_error(service):
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("refused"),
    ):
        with pytest.raises(VoiceServiceUnavailableError):
            await service.process_speech(audio=SAMPLE_AUDIO, language="en-US", context=None)


@pytest.mark.asyncio
async def test_process_speech_tts_failure(service):
    """TTS failure returns degraded result (empty audio) without raising."""
    llm_content = "Good job! <!-- USER_TRANSCRIPT: nice --> <!-- PRONUNCIATION_EVENTS: [] -->"
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=[_llm_response(llm_content), _error_response(500)],
    ):
        result = await service.process_speech(audio=SAMPLE_AUDIO, language="en-US", context=None)

    assert result.audio_bytes == b""
    assert result.transcript_assistant == "Good job!"


@pytest.mark.asyncio
async def test_reasoning_content_empty_content_raises(service):
    """If content is None/empty (truncated by thinking mode), raise VoiceServiceUnavailableError."""
    body = {"choices": [{"message": {"role": "assistant", "reasoning_content": "...", "content": None}}]}
    resp = httpx.Response(
        status_code=200,
        content=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=resp):
        with pytest.raises(VoiceServiceUnavailableError, match="empty content"):
            await service.process_speech(audio=SAMPLE_AUDIO, language="en-US", context=None)


# ---------------------------------------------------------------------------
# Language mapping
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_language_mapping_pt_br(service):
    """Verify pt-BR maps to 'pt' for Piper TTS."""
    llm_content = "Olá! <!-- USER_TRANSCRIPT: olá --> <!-- PRONUNCIATION_EVENTS: [] -->"
    captured = []

    async def fake_post(url, **kwargs):
        captured.append((url, kwargs))
        if "chat" in url:
            return _llm_response(llm_content)
        return _tts_response()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=fake_post):
        await service.process_speech(audio=SAMPLE_AUDIO, language="pt-BR", context=None)

    tts_call = next(c for c in captured if "chat" not in c[0])
    assert tts_call[1]["json"]["lang"] == "pt"


@pytest.mark.asyncio
async def test_language_mapping_en_us(service):
    """Verify en-US maps to 'en' for Piper TTS."""
    llm_content = "Nice! <!-- USER_TRANSCRIPT: hi --> <!-- PRONUNCIATION_EVENTS: [] -->"
    captured = []

    async def fake_post(url, **kwargs):
        captured.append((url, kwargs))
        if "chat" in url:
            return _llm_response(llm_content)
        return _tts_response()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=fake_post):
        await service.process_speech(audio=SAMPLE_AUDIO, language="en-US", context=None)

    tts_call = next(c for c in captured if "chat" not in c[0])
    assert tts_call[1]["json"]["lang"] == "en"
