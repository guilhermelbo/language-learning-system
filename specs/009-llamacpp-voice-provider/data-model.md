# Data Model: llamacpp Voice Provider

**Feature**: 009-llamacpp-voice-provider
**Date**: 2026-06-29

This feature is a **pure infrastructure extension** — no new domain entities, no schema changes, no new repositories.

---

## Configuration Changes (Settings Entity)

One field added to `backend/src/config.py`:

| New field | Alias (env var) | Type | Default | Description |
|-----------|----------------|------|---------|-------------|
| `voice_model_name` | `VOICE_MODEL_NAME` | `str` | `""` | Model name passed to llamacpp chat completions. Empty = server default. |

All other `voice_*` fields already exist (from feature 008).

---

## New Infrastructure Component

### `OpenAICompatibleVoiceService`

**File**: `backend/src/infrastructure/llm_voice_service.py`

| Field | Value |
|-------|-------|
| Class name | `OpenAICompatibleVoiceService` |
| Implements | `OmniVoiceService` (domain interface — unchanged) |
| Input | `process_speech(audio: bytes, language: str, context: list | None)` |
| Output | `OmniVoiceResult` (domain entity — unchanged) |
| LLM call | `POST {base_url}/chat/completions` (JSON, `input_audio` multimodal format) |
| TTS call | `POST {tts_api_url}/` (JSON, Piper format) |
| STT call | **None** — audio is processed natively by the LLM |
| Error type raised | `VoiceServiceUnavailableError` (from `omni_service.py`, unchanged) |

**Constructor parameters**:
```
base_url: str          — llamacpp base URL (e.g., http://host.docker.internal:8080/v1)
model: str             — model name for the LLM call (e.g., "gemma-4-12B-it-Q5_K_M.gguf")
api_key: str | None    — optional auth header (passed as Bearer token if set)
tts_api_url: str       — Piper TTS base URL (e.g., http://tts:8002)
timeout: int           — per-request timeout in seconds
```

**Pipeline** (two HTTP calls, not three):
```
audio bytes (WAV)
    ↓ base64 encode
POST {base_url}/chat/completions
  messages[0].content = [
    {type: "input_audio", input_audio: {data: "<b64>", format: "wav"}},
    {type: "text", text: "Respond as the tutor."}
  ]
    ↓ choices[0].message.content (with PRONUNCIATION_EVENTS + USER_TRANSCRIPT blocks)
parse USER_TRANSCRIPT → transcript_user
parse PRONUNCIATION_EVENTS → events
strip blocks → clean_text
    ↓
POST {tts_api_url}/
  {"text": clean_text, "lang": "en"|"pt"}
    ↓ WAV bytes
OmniVoiceResult(audio_bytes, transcript_user, clean_text, events)
```

---

## What Does NOT Change

- `OmniVoiceService` ABC in `backend/src/domain/interfaces.py` — unchanged
- `OmniVoiceResult`, `PronunciationEvent`, `OmniVoiceSession`, `OmniAudioTurn` — unchanged
- `ProcessOmniVoiceUseCase` — unchanged
- `GenericVoiceHttpService` — unchanged
- All public API endpoints — unchanged
- All response schemas (`OmniTextResponse`) — unchanged
- All frontend components — unchanged
- `InMemoryOmniSessionRepository` — unchanged
