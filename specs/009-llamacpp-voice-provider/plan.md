# Implementation Plan: llamacpp Voice Provider

**Branch**: `009-llamacpp-voice-provider` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-llamacpp-voice-provider/spec.md`

---

## Summary

Pure backend addition — no domain changes, no API shape changes, no frontend changes. Adds an `openai_compatible` voice provider that drives the voice tutoring channel through the llamacpp server already running for text. Pipeline: Gemma 4 native audio input (chat completions with `input_audio` content type) → PRONUNCIATION_EVENTS + USER_TRANSCRIPT parsing → Piper TTS. No STT server required. Switching to this provider requires only two environment variable changes.

---

## Technical Context

**Language/Version**: Python 3.10+ (backend)

**Primary Dependencies**: httpx (already used), pydantic-settings, FastAPI — no new dependencies

**Storage**: N/A — no persistence changes; in-memory sessions unchanged

**Testing**: pytest (`backend/tests/`)

**Target Platform**: Linux server (Docker), same as current

**Project Type**: Web service (backend extension — new infrastructure class only)

**Performance Goals**: 2.4–5.7s latency per turn (validated); same I/O budget as existing pipeline

**Constraints**:
- Zero public API changes (endpoint paths, request/response shapes unchanged)
- Zero frontend changes
- Zero domain layer changes
- No STT server required — LLM processes audio natively via `input_audio` content type
- llamacpp TTS (`/v1/audio/speech`) returns 404 — use existing Piper TTS instead
- Reuse `TUTOR_SYSTEM_PROMPT` and `_extract_pronunciation_events` logic from `ai_services/omni/app/main.py`
- `max_tokens` must be >= 1024 — thinking mode generates `reasoning_content` first, then `content`

**Scale/Scope**: 1 new file, 3 files modified

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Docker-First Deployment | ✅ PASS | No new Docker services; only env var changes in docker-compose |
| II. LLM Independence | ✅ PASS | New provider reads `VOICE_API_URL` and `VOICE_MODEL_NAME` from env vars |
| III. Clean Architecture + DDD | ✅ PASS | New class lives in `infrastructure/`; domain layer untouched |
| IV. Type Safety & Async I/O | ✅ PASS | New service uses `async/await` with `httpx.AsyncClient` |
| V. JSON Contract Compliance | ✅ PASS | No response shape changes |
| VI. Testing Discipline | ✅ PASS | New test file for `OpenAICompatibleVoiceService` |

No violations.

---

## Research Decisions

### Decision 1 — TTS: Piper (existing) instead of llamacpp TTS
**Finding**: `POST localhost:8080/v1/audio/speech` returns 404 for all voice names. llamacpp at port 8080 has no TTS model loaded.
**Decision**: Use Piper TTS at `settings.tts_api_url` (port 8002, already running in Docker).

### Decision 2 — STT: NOT USED (native audio processing)
**Finding**: Gemma 4 12B loaded with mmproj (vision/audio projector). `POST /v1/chat/completions` with `input_audio` content type returns HTTP 200 and correctly describes audio content. Audio is processed by the multimodal encoder — no separate STT call needed.
**Decision**: Skip STT entirely. Audio bytes are base64-encoded and sent directly as `input_audio` in the messages array.

### Decision 3 — System Prompt and Pronunciation Parsing
**Finding**: `TUTOR_SYSTEM_PROMPT` and `_extract_pronunciation_events()` regex logic exist in `ai_services/omni/app/main.py`.
**Decision**: Duplicate into `llm_voice_service.py`. Add `<!-- USER_TRANSCRIPT: ... -->` block instruction to system prompt so the model also provides a parseable transcript of what it heard.

### Decision 4 — LLM call format: `input_audio` multimodal
**Finding**: llamacpp accepts multimodal messages with `type: "input_audio"` content blocks. Audio is base64-encoded WAV. Thinking mode is active, so response has `reasoning_content` (internal) + `content` (actual response).
**Decision**: Build messages with two content blocks: `input_audio` (the audio) + `text` (tutor instruction). Extract `content` from response (not `reasoning_content`). Guard against `None` content.

### Decision 5 — Piper TTS request format
**Finding**: Piper TTS at port 8002 accepts `POST /` with JSON body `{"text": "...", "lang": "..."}` and returns WAV bytes directly.
**Decision**: Map `language` parameter to Piper's lang field. Default "en".

### Decision 6 — max_tokens
**Finding**: Thinking mode generates `reasoning_content` before `content`. Low `max_tokens` truncates before content is generated, returning empty `content`.
**Decision**: Set `max_tokens=1024` in the LLM call. This is a hard-coded value in the service (not from config — voice config has no token field).

---

## Project Structure

### Documentation (this feature)

```text
specs/009-llamacpp-voice-provider/
├── spec.md
├── plan.md              # This file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── voice-pipeline-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code Changes

```text
backend/
├── src/
│   ├── config.py                                MODIFY — add voice_model_name
│   ├── infrastructure/
│   │   ├── llm_voice_service.py                 CREATE — OpenAICompatibleVoiceService
│   │   └── voice_factory.py                     MODIFY — add openai_compatible case
└── tests/
    └── test_llm_voice_service.py                CREATE — unit tests

docker-compose.yml                               MODIFY — VOICE_PROVIDER, VOICE_API_URL, VOICE_MODEL_NAME
```

---

## Complexity Tracking

No constitution violations. Section intentionally blank.
