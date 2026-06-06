"""Tests for dynamic LLM configuration."""
import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Provide a stub for the optional 'ollama' package so tests don't need it installed.
_ollama_stub = types.ModuleType("ollama")
_ollama_stub.AsyncClient = MagicMock  # replaced per-test anyway
sys.modules.setdefault("ollama", _ollama_stub)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def _make_settings(**kwargs):
    """Create a Settings instance with env isolation."""
    from src.config import Settings
    return Settings(**{k.upper(): v for k, v in kwargs.items()})


def test_settings_defaults():
    from src.config import Settings
    s = Settings()
    assert s.llm_provider == "ollama"
    assert s.llm_model_name == "mistral"
    assert s.llm_base_url == "http://localhost:11434/v1"
    assert s.llm_api_key == "ollama"
    assert s.llm_temperature == 0.7
    assert s.llm_max_tokens == 1024


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_MODEL_NAME", "qwen2.5:7b")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("LLM_API_KEY", "ollama")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.3")
    monkeypatch.setenv("LLM_MAX_TOKENS", "512")

    from src.config import Settings
    s = Settings()
    assert s.llm_provider == "openai_compatible"
    assert s.llm_model_name == "qwen2.5:7b"
    assert s.llm_temperature == 0.3
    assert s.llm_max_tokens == 512


def test_settings_get_settings_singleton(monkeypatch):
    import src.config as cfg_module
    monkeypatch.setattr(cfg_module, "_settings", None)
    s1 = cfg_module.get_settings()
    s2 = cfg_module.get_settings()
    assert s1 is s2


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def test_factory_returns_ollama_service(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_MODEL_NAME", "mistral")

    from src.config import Settings
    from src.infrastructure.llm_factory import create_llm_service
    from src.infrastructure.llm_service import OllamaLLMService

    s = Settings()
    service = create_llm_service(s)
    assert isinstance(service, OllamaLLMService)
    assert service.model == "mistral"


def test_factory_returns_openai_compatible_service(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_MODEL_NAME", "qwen2.5:7b")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("LLM_API_KEY", "ollama")

    from src.config import Settings
    from src.infrastructure.llm_factory import create_llm_service
    from src.infrastructure.llm_service import OpenAICompatibleLLMService

    s = Settings()
    service = create_llm_service(s)
    assert isinstance(service, OpenAICompatibleLLMService)
    assert service.model == "qwen2.5:7b"


def test_factory_raises_on_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown_provider")

    from src.config import Settings
    from src.infrastructure.llm_factory import create_llm_service

    s = Settings()
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        create_llm_service(s)


# ---------------------------------------------------------------------------
# OllamaLLMService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ollama_generate_response():
    from src.infrastructure.llm_service import OllamaLLMService
    from src.domain.entities import Message

    mock_response = {"message": {"content": '[{"text": "Olá", "lang": "pt"}]'}}

    service = OllamaLLMService(model="mistral")
    service.client = MagicMock()
    service.client.chat = AsyncMock(return_value=mock_response)

    history = [Message(content="Hello", role="user")]
    result = await service.generate_response(history)

    assert result == '[{"text": "Olá", "lang": "pt"}]'
    service.client.chat.assert_called_once()
    call_kwargs = service.client.chat.call_args
    assert call_kwargs.kwargs["model"] == "mistral"
    assert call_kwargs.kwargs["format"] == "json"


# ---------------------------------------------------------------------------
# OpenAICompatibleLLMService
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_openai_compatible_generate_response():
    from src.infrastructure.llm_service import OpenAICompatibleLLMService
    from src.domain.entities import Message

    service = OpenAICompatibleLLMService(
        model="qwen2.5:7b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

    # Mock the async OpenAI client
    mock_message = MagicMock()
    mock_message.content = '[{"text": "Olá", "lang": "pt"}]'
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    service.client = MagicMock()
    service.client.chat = MagicMock()
    service.client.chat.completions = MagicMock()
    service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    history = [Message(content="Translate 'hello'", role="user")]
    result = await service.generate_response(history)

    assert result == '[{"text": "Olá", "lang": "pt"}]'
    service.client.chat.completions.create.assert_called_once()
    call_kwargs = service.client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "qwen2.5:7b"
    assert call_kwargs.get("stream") is not True  # not a streaming call


@pytest.mark.asyncio
async def test_openai_compatible_generate_response_stream():
    from src.infrastructure.llm_service import OpenAICompatibleLLMService
    from src.domain.entities import Message

    service = OpenAICompatibleLLMService(
        model="qwen2.5:7b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

    async def _fake_stream():
        chunks = ['[{"text"', ': "Olá"', ', "lang": "pt"}]']
        for text in chunks:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = text
            yield chunk

    service.client = MagicMock()
    service.client.chat = MagicMock()
    service.client.chat.completions = MagicMock()
    # create() is called with stream=True; the service iterates the result with async for
    service.client.chat.completions.create = AsyncMock(return_value=_fake_stream())

    history = [Message(content="Hello", role="user")]
    parts = [part async for part in service.generate_response_stream(history)]

    assert "".join(parts) == '[{"text": "Olá", "lang": "pt"}]'


# ---------------------------------------------------------------------------
# System prompt is included
# ---------------------------------------------------------------------------

def test_system_prompt_injected():
    from src.infrastructure.llm_service import _build_messages, SYSTEM_PROMPT
    from src.domain.entities import Message

    history = [Message(content="hi", role="user")]
    messages = _build_messages(history)

    assert messages[0]["role"] == "system"
    assert "JSON" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "hi"
