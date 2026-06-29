# Data Model: Voice Provider Abstraction

**Feature**: 008-voice-provider-abstraction  
**Date**: 2026-06-29

This feature is a **pure refactoring** — no new domain entities are introduced and no existing entities change. The changes are entirely in the configuration and infrastructure layers.

---

## Configuration Changes (Settings Entity)

The `Settings` class in `backend/src/config.py` gains one field and renames four.

### Fields renamed

| Old field | Old alias (env var) | New field | New alias (env var) |
|-----------|--------------------|-----------|--------------------|
| `omni_enabled` | `OMNI_ENABLED` | `voice_enabled` | `VOICE_ENABLED` |
| `omni_api_url` | `OMNI_API_URL` | `voice_api_url` | `VOICE_API_URL` |
| `omni_timeout_seconds` | `OMNI_TIMEOUT_SECONDS` | `voice_timeout_seconds` | `VOICE_TIMEOUT_SECONDS` |
| `omni_max_audio_seconds` | `OMNI_MAX_AUDIO_SECONDS` | `voice_max_audio_seconds` | `VOICE_MAX_AUDIO_SECONDS` |

### Field added

| New field | Alias (env var) | Type | Default | Valid values |
|-----------|----------------|------|---------|-------------|
| `voice_provider` | `VOICE_PROVIDER` | `str` | `"generic"` | `"generic"` (extensible) |

---

## New Infrastructure Components

### `GenericVoiceHttpService` (renamed from `QwenOmniHttpService`)

**File**: `backend/src/infrastructure/omni_service.py`  
No logic changes. Only the class name and exception name change.

| Before | After |
|--------|-------|
| `QwenOmniHttpService` | `GenericVoiceHttpService` |
| `OmniServiceUnavailableError` | `VoiceServiceUnavailableError` |

---

### `VoiceProviderFactory` (new)

**File**: `backend/src/infrastructure/voice_factory.py`

| Field | Value |
|-------|-------|
| Function name | `create_voice_service` |
| Input | `Settings` |
| Output | `OmniVoiceService` (domain interface, unchanged) |
| Providers supported | `"generic"` → `GenericVoiceHttpService` |
| Error on unknown | `ValueError` with message naming the invalid provider |

---

### `ModelBackend` ABC (new, in external server)

**File**: `ai_services/omni/app/backends/base.py`

| Method | Signature | Description |
|--------|-----------|-------------|
| `load()` | `() → None` | Load model weights at startup |
| `infer()` | `(audio: ndarray, sr: int, system_prompt: str, context: list) → tuple[ndarray, int, str]` | Run inference; returns (audio_out, sample_rate, text_out) |
| `is_loaded()` | `() → bool` | True when weights are fully loaded |
| `backend_name()` | `() → str` | Identifier string for health response |

---

### `QwenBackend` (extracted from main.py)

**File**: `ai_services/omni/app/backends/qwen.py`  
Contains: all code currently in `_load_model()` and `_run_inference()` in `main.py`.  
Env var read: `VOICE_MODEL_DIR` (default: `/app/models/Qwen2.5-Omni-7B`).

---

### `GemmaBackend` (stub)

**File**: `ai_services/omni/app/backends/gemma.py`  
Purpose: validate extensibility pattern only.

| Method | Behaviour |
|--------|-----------|
| `load()` | Raises `NotImplementedError("Gemma 4 backend not yet implemented")` |
| `infer()` | Raises `NotImplementedError` |
| `is_loaded()` | Returns `False` |
| `backend_name()` | Returns `"gemma4"` |

---

## Health Endpoint Schema Change (external server)

`GET /health` adds one field:

**Before**:
```json
{ "status": "ok", "model_loaded": true }
```

**After**:
```json
{ "status": "ok", "model_loaded": true, "backend": "qwen2.5-omni" }
```

The `backend` field names the active `VOICE_MODEL_BACKEND` value. The backend's `GET /conversation/omni/status` endpoint already proxies this health response, so the frontend will see `backend` in the status response too.

---

## What Does NOT Change

- `OmniVoiceService` ABC in `backend/src/domain/interfaces.py` — unchanged
- `OmniVoiceResult`, `PronunciationEvent`, `OmniVoiceSession`, `OmniAudioTurn` in `backend/src/domain/entities.py` — unchanged
- `ProcessOmniVoiceUseCase` in `backend/src/application/use_cases.py` — unchanged
- `InMemoryOmniSessionRepository` in `backend/src/infrastructure/repositories.py` — unchanged
- All public API endpoints (`/conversation/omni/speech`, `/conversation/omni/status`) — unchanged
- All response schemas (`OmniTextResponse`) — unchanged
- All frontend components — unchanged
- Internal voice server endpoint `/omni/speech` — unchanged (internal contract)
