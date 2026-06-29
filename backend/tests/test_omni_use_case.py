"""Unit tests for ProcessOmniVoiceUseCase."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.entities import (
    OmniVoiceSession,
    OmniVoiceResult,
    PronunciationEvent,
)
from src.infrastructure.repositories import InMemoryOmniSessionRepository
from src.application.use_cases import ProcessOmniVoiceUseCase


def _make_result(
    audio: bytes = b"RIFF\x00\x00\x00\x00WAVEfmt ",
    transcript_user: str = "hello",
    transcript_assistant: str = "Hello! Good job.",
    pronunciation_events: list | None = None,
) -> OmniVoiceResult:
    return OmniVoiceResult(
        audio_bytes=audio,
        transcript_user=transcript_user,
        transcript_assistant=transcript_assistant,
        pronunciation_events=pronunciation_events or [],
    )


@pytest.fixture
def omni_service():
    svc = AsyncMock()
    svc.process_speech = AsyncMock(return_value=_make_result())
    return svc


@pytest.fixture
def repo():
    return InMemoryOmniSessionRepository()


@pytest.fixture
def use_case(omni_service, repo):
    return ProcessOmniVoiceUseCase(omni_service, repo)


@pytest.mark.asyncio
async def test_creates_new_session_when_none_provided(use_case, repo):
    result = await use_case.execute(audio_data=b"fake_audio", session=None)

    assert result["conversation_id"].startswith("omni-")
    assert result["user_text"] == "hello"
    assert result["ai_text"] == "Hello! Good job."
    assert isinstance(result["pronunciation_events"], list)


@pytest.mark.asyncio
async def test_appends_turn_to_existing_session(use_case, repo):
    # First call — creates session
    result1 = await use_case.execute(audio_data=b"audio1", session=None)
    conv_id = result1["conversation_id"]
    raw_id = conv_id[len("omni-"):]

    from uuid import UUID
    session = await repo.get_by_id(UUID(raw_id))
    assert session is not None
    assert len(session.turns) == 1

    # Second call — continues session
    result2 = await use_case.execute(audio_data=b"audio2", session=session)
    assert result2["conversation_id"] == conv_id

    session_after = await repo.get_by_id(UUID(raw_id))
    assert len(session_after.turns) == 2


@pytest.mark.asyncio
async def test_result_dict_has_correct_shape(use_case):
    result = await use_case.execute(audio_data=b"audio", session=None)

    assert "conversation_id" in result
    assert "user_text" in result
    assert "ai_text" in result
    assert "audio_base64" in result
    assert "pronunciation_events" in result


@pytest.mark.asyncio
async def test_pronunciation_events_included_in_result(omni_service, repo):
    event = PronunciationEvent(
        word="hello",
        error_type="vowel",
        user_pronunciation="hɛlo",
        correct_pronunciation="həˈloʊ",
    )
    omni_service.process_speech = AsyncMock(
        return_value=_make_result(pronunciation_events=[event])
    )
    uc = ProcessOmniVoiceUseCase(omni_service, repo)
    result = await uc.execute(audio_data=b"audio", session=None)

    assert len(result["pronunciation_events"]) == 1
    ev = result["pronunciation_events"][0]
    assert ev["word"] == "hello"
    assert ev["error_type"] == "vowel"
    assert ev["correct_pronunciation"] == "həˈloʊ"


@pytest.mark.asyncio
async def test_audio_base64_is_none_when_empty(omni_service, repo):
    omni_service.process_speech = AsyncMock(
        return_value=_make_result(audio=b"")
    )
    uc = ProcessOmniVoiceUseCase(omni_service, repo)
    result = await uc.execute(audio_data=b"audio", session=None)

    assert result["audio_base64"] is None


@pytest.mark.asyncio
async def test_session_persisted_after_execute(use_case, repo):
    result = await use_case.execute(audio_data=b"audio", session=None)
    raw_id = result["conversation_id"][len("omni-"):]

    from uuid import UUID
    session = await repo.get_by_id(UUID(raw_id))
    assert session is not None
    assert len(session.turns) == 1
    assert session.turns[0].transcript_user == "hello"
