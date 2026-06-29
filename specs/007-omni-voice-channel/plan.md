# Implementation Plan: Omni Voice Channel — Native Speech-to-Speech Tutoring

**Branch**: `007-omni-voice-channel` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-omni-voice-channel/spec.md`

---

## Summary

Add a parallel voice tutoring channel powered by Qwen2.5-Omni-7B — a natively multimodal audio model that processes raw speech input and generates spoken responses without converting audio to text first. This enables pronunciation-aware tutoring: the model hears how the user speaks, detects phonetic errors, and corrects them in its spoken reply. The new channel runs as a new Docker service (`lingo-omni`) and integrates into the existing Clean Architecture as a new domain interface + infrastructure adapter + use case, leaving the current LLM+STT+TTS pipeline entirely untouched.

---

## Technical Context

**Language/Version**: Python 3.10+ (backend + omni service), TypeScript / Next.js (frontend)

**Primary Dependencies**: FastAPI, httpx (async), transformers (omni service), torch (omni service), React (frontend)

**Storage**: In-memory only — `OmniVoiceSession` stored in a new `InMemoryOmniSessionRepository`, same pattern as existing `InMemoryConversationRepository`

**Testing**: pytest (backend), npm run lint (frontend)

**Target Platform**: Linux server (Docker, Python 3.10 slim + CUDA or CPU)

**Project Type**: Web service (new service + backend extension + frontend extension)

**Performance Goals**: Omni turn response ≤ 5 seconds for audio inputs ≤ 15 seconds (matches SC-001)

**Constraints**:
- Model weights must be user-supplied; service must not bundle or auto-download them
- `OMNI_ENABLED=false` by default — zero impact on existing deployments
- Existing test suite must pass 100% (SC-005)
- No changes to existing API endpoints or response shapes

**Scale/Scope**: Single-user local deployment; no horizontal scaling in v1

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Docker-First Deployment | ✅ PASS | New `lingo-omni` service added to `docker-compose.yml`; stack still starts with single command |
| II. LLM Independence | ✅ PASS | Omni service URL configured via `OMNI_API_URL` env var; backend has no direct model dependency |
| III. Clean Architecture + DDD | ✅ PASS | `OmniVoiceService` ABC in `domain/`; `QwenOmniHttpService` in `infrastructure/`; use case in `application/` |
| IV. Type Safety & Async I/O | ✅ PASS | All new service calls use `async/await` + `httpx.AsyncClient`; all signatures typed |
| V. JSON Contract Compliance | ✅ PASS | New endpoint uses a new response model (`OmniTextResponse`) — existing JSON contract unchanged |
| VI. Testing Discipline | ✅ PASS | New use case and service adapter covered by pytest; new endpoint added to integration tests |

No violations. Complexity Tracking section not required.

---

## Project Structure

### Documentation (this feature)

```text
specs/007-omni-voice-channel/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Entities and internal API contract
├── quickstart.md        # Validation scenarios
├── contracts/
│   └── omni-api-contract.md    # Public backend API contract
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
ai_services/
├── stt/                            # (unchanged)
├── tts/                            # (unchanged)
└── omni/                           # NEW — Qwen2.5-Omni model service
    ├── Dockerfile
    ├── requirements.txt
    ├── app/
    │   └── main.py                 # FastAPI server: POST /omni/speech, GET /health
    └── models/                     # User-supplied model weights (gitignored)
        └── Qwen2.5-Omni-7B/        # Hugging Face model directory

backend/
├── src/
│   ├── domain/
│   │   ├── entities.py             # ADD: OmniVoiceSession, OmniAudioTurn, PronunciationEvent, OmniVoiceResult
│   │   └── interfaces.py           # ADD: OmniVoiceService ABC
│   ├── infrastructure/
│   │   ├── omni_service.py         # NEW: QwenOmniHttpService (implements OmniVoiceService)
│   │   └── repositories.py         # ADD: InMemoryOmniSessionRepository
│   ├── application/
│   │   └── use_cases.py            # ADD: ProcessOmniVoiceUseCase
│   ├── config.py                   # ADD: omni_api_url, omni_enabled settings
│   └── main.py                     # ADD: /conversation/omni/speech + /conversation/omni/status
└── tests/
    ├── test_omni_service.py         # NEW: unit tests for QwenOmniHttpService
    └── test_omni_use_case.py        # NEW: unit tests for ProcessOmniVoiceUseCase

frontend/
├── app/
│   └── page.tsx                    # MODIFY: pass omniEnabled flag to ChatInterface
└── components/
    ├── ChatInterface.tsx            # MODIFY: add mode selector + omni session state
    ├── VoiceButton.tsx              # (unchanged — reused in both modes)
    └── OmniStatusBadge.tsx         # NEW: visual indicator for omni mode / availability
    └── PronunciationEventCard.tsx   # NEW: displays detected pronunciation errors

docker-compose.yml                  # ADD: omni service definition (optional, no depends_on)

tests/
└── fixtures/
    ├── sample_hello.wav            # NEW: test audio fixture
    ├── mispronounced_hello.wav     # NEW: test audio fixture
    ├── sample_followup.wav         # NEW: test audio fixture
    └── long_audio_70s.wav          # NEW: test audio fixture (duration > 60s)
```

---

## Complexity Tracking

No constitution violations. This section is intentionally blank.
