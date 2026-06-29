# Implementation Plan: Voice Provider Abstraction

**Branch**: `008-voice-provider-abstraction` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-voice-provider-abstraction/spec.md`

---

## Summary

Pure refactoring — no new features, no API changes, no domain changes. Applies the same provider factory pattern already used by the LLM text pipeline to the voice (speech-to-speech) channel. The result: switching voice models requires only environment variable changes, zero code edits. Three concrete changes: (1) rename `OMNI_*` config to `VOICE_*` + add `VOICE_PROVIDER`, (2) create `voice_factory.py` mirroring `llm_factory.py`, (3) extract Qwen inference code from the external server's `main.py` into a swappable backend module.

---

## Technical Context

**Language/Version**: Python 3.10+ (backend + voice server), TypeScript/Next.js (frontend — untouched)

**Primary Dependencies**: FastAPI, httpx, pydantic-settings (backend); transformers, torch (voice server)

**Storage**: N/A — no persistence changes

**Testing**: pytest (`backend/tests/`)

**Target Platform**: Linux server (Docker), same as current

**Project Type**: Web service (backend refactoring + external server restructuring)

**Performance Goals**: Identical to pre-refactor — this change adds no I/O paths

**Constraints**:
- Zero public API changes (endpoint paths, request/response shapes unchanged)
- Zero frontend changes
- Zero domain layer changes
- `OMNI_*` env vars removed (no aliases — internal system)

**Scale/Scope**: ~8 files modified, 4 new files created (factory + 3 backend files)

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Docker-First Deployment | ✅ PASS | No new Docker services; env var renames only in docker-compose |
| II. LLM Independence | ✅ PASS | This feature extends the same independence principle to the voice channel |
| III. Clean Architecture + DDD | ✅ PASS | Factory lives in `infrastructure/`; domain layer untouched |
| IV. Type Safety & Async I/O | ✅ PASS | No signature changes; factory function is typed |
| V. JSON Contract Compliance | ✅ PASS | No response shape changes |
| VI. Testing Discipline | ✅ PASS | Test file updated to match renamed classes; no test logic changes |

No violations. Complexity Tracking not required.

---

## Project Structure

### Documentation (this feature)

```text
specs/008-voice-provider-abstraction/
├── spec.md
├── plan.md              # This file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── voice-config-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks output
```

### Source Code Changes

```text
backend/
├── src/
│   ├── config.py                          MODIFY — rename omni_* → voice_*, add voice_provider
│   ├── infrastructure/
│   │   ├── omni_service.py                MODIFY — rename class + exception
│   │   └── voice_factory.py               CREATE — mirrors llm_factory.py
│   └── main.py                            MODIFY — use factory, rename setting refs
└── tests/
    └── test_omni_service.py               MODIFY — update class/exception names

ai_services/omni/
├── app/
│   ├── main.py                            MODIFY — extract model code, add backend registry
│   └── backends/
│       ├── __init__.py                    CREATE (empty)
│       ├── base.py                        CREATE — ModelBackend ABC
│       ├── qwen.py                        CREATE — QwenBackend (code extracted from main.py)
│       └── gemma.py                       CREATE — GemmaBackend (stub, raises NotImplementedError)

docker-compose.yml                         MODIFY — OMNI_* → VOICE_*
.env.example                               MODIFY — OMNI_* → VOICE_*
```

---

## Complexity Tracking

No constitution violations. Section intentionally blank.
