# Tasks: Omni Voice Channel — Native Speech-to-Speech Tutoring

**Input**: Design documents from `specs/007-omni-voice-channel/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/omni-api-contract.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory scaffolding and Docker foundation before any code is written.

- [x] T001 Create `ai_services/omni/` directory with `app/` and `models/` subdirectories
- [x] T002 [P] Create `tests/fixtures/` directory for audio test files used by quickstart.md scenarios
- [x] T003 [P] Add `ai_services/omni/models/.gitkeep` and `.gitignore` entry to exclude model weights from version control

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain types, interfaces, and config that all user stories depend on. Nothing in Phase 3+ can start until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Add `OmniVoiceSession`, `OmniAudioTurn`, `PronunciationEvent`, and `OmniVoiceResult` to `backend/src/domain/entities.py` (per data-model.md)
- [x] T005 [P] Add `OmniVoiceService` abstract base class to `backend/src/domain/interfaces.py` with method `async process_speech(audio: bytes, language: str, context: list) -> OmniVoiceResult`
- [x] T006 [P] Add `omni_api_url: str`, `omni_enabled: bool`, and `omni_timeout_seconds: int` settings to `backend/src/config.py` (env vars: `OMNI_API_URL`, `OMNI_ENABLED`, default `false`)
- [x] T007 Add `InMemoryOmniSessionRepository` to `backend/src/infrastructure/repositories.py` with `save(session)` and `get_by_id(id)` methods, following existing `InMemoryConversationRepository` pattern

**Checkpoint**: Domain model, interface contract, config, and repository are ready — user story implementation can begin.

---

## Phase 3: User Story 1 — Real-Time Voice Conversation via Omni Channel (Priority: P1) 🎯 MVP

**Goal**: A user can speak to the system and receive a spoken response through the native audio channel, end-to-end, with session continuity across turns.

**Independent Test**: `POST /conversation/omni/speech` with a valid WAV file returns `200 OK` with `audio_base64`, `user_text`, `ai_text`, and `conversation_id` prefixed with `"omni-"`. A second call with the returned `conversation_id` succeeds and maintains context.

### Implementation for User Story 1

- [x] T008 [US1] Create `ai_services/omni/requirements.txt` listing `fastapi`, `uvicorn`, `transformers`, `torch`, `accelerate`, and `pillow` (Qwen2.5-Omni inference dependencies)
- [x] T009 [US1] Create `ai_services/omni/Dockerfile` — Python 3.10 slim base, install requirements, expose port 8003, copy app/, set entrypoint to `uvicorn app.main:app`
- [x] T010 [US1] Implement `ai_services/omni/app/main.py`: FastAPI server with `GET /health` (returns `{status, model_loaded}`) and `POST /omni/speech` (accepts multipart audio + language + context, returns JSON per data-model.md internal contract)
- [x] T011 [US1] Implement model loading in `ai_services/omni/app/main.py`: load `Qwen/Qwen2.5-Omni-7B` from `./models/Qwen2.5-Omni-7B/` at startup using `transformers.AutoModelForCausalLM` with audio support; set `model_loaded = True` after successful load
- [x] T012 [US1] Implement system prompt in `ai_services/omni/app/main.py`: instruct model to (a) respond naturally in the target language, (b) detect pronunciation issues, (c) correct them in spoken response, (d) emit `pronunciation_events` JSON in text output channel
- [x] T013 [P] [US1] Implement `QwenOmniHttpService` in `backend/src/infrastructure/omni_service.py`: implements `OmniVoiceService` ABC, sends multipart POST to `OMNI_API_URL/omni/speech` via `httpx.AsyncClient`, deserialises response into `OmniVoiceResult`; raises `OmniServiceUnavailableError` on connection failure or non-200 status
- [x] T014 [P] [US1] Implement `ProcessOmniVoiceUseCase` in `backend/src/application/use_cases.py`: accepts audio bytes + session (or None for new), calls `OmniVoiceService.process_speech()`, saves `OmniAudioTurn` to session, persists session via repository, returns result dict with `conversation_id`, `user_text`, `ai_text`, `audio_base64`, `pronunciation_events`
- [x] T015 [US1] Add `POST /conversation/omni/speech` endpoint to `backend/src/main.py`: instantiate `QwenOmniHttpService` (only when `OMNI_ENABLED=true`), wire `ProcessOmniVoiceUseCase`, accept `UploadFile` + optional `conversation_id` + optional `language`, return `OmniTextResponse` model; raise `HTTP 503` with `{"detail": "omni_unavailable"}` when disabled or service unreachable
- [x] T016 [US1] Add `GET /conversation/omni/status` endpoint to `backend/src/main.py`: check `OMNI_ENABLED` config and probe `OMNI_API_URL/health`; return `{omni_enabled, model_loaded, omni_api_url}` (see contracts/omni-api-contract.md)
- [x] T017 [US1] Add `OmniTextResponse` Pydantic model to `backend/src/main.py` with fields: `conversation_id`, `user_text`, `ai_text`, `audio_base64 | None`, `pronunciation_events: list`
- [x] T018 [US1] Add `omni` service to `docker-compose.yml`: build from `./ai_services/omni`, container name `lingo-omni`, port `8003:8003`, mount `./ai_services/omni/models:/app/models:ro`, restart `unless-stopped`; no `depends_on` in backend (backend degrades gracefully)
- [x] T019 [US1] Update backend `docker-compose.yml` environment block to include `OMNI_ENABLED=${OMNI_ENABLED:-false}` and `OMNI_API_URL=http://omni:8003`
- [x] T020 [P] [US1] Add mode selector toggle ("Standard" / "Voice Tutor") to `frontend/components/ChatInterface.tsx`; call `GET /conversation/omni/status` on mount; hide Voice Tutor option if `omni_enabled: false`
- [x] T021 [P] [US1] Create `frontend/components/OmniStatusBadge.tsx`: visual indicator showing "Voice Tutor Active" when in omni mode, including a loading state while `model_loaded: false`
- [x] T022 [US1] Update `frontend/components/ChatInterface.tsx` to maintain separate `omniConversationId` state; route audio submissions to `POST /conversation/omni/speech` when in omni mode; carry returned `conversation_id` forward across turns
- [x] T023 [US1] Write `backend/tests/test_omni_use_case.py`: unit tests for `ProcessOmniVoiceUseCase` — new session creation, existing session lookup, turn appended to session, result dict shape; mock `OmniVoiceService`
- [x] T024 [P] [US1] Write `backend/tests/test_omni_service.py`: unit tests for `QwenOmniHttpService` — successful response deserialization, `OmniServiceUnavailableError` on connection error, timeout handling; mock `httpx.AsyncClient`

**Checkpoint**: End-to-end audio conversation via omni channel works. User can speak, get spoken response, and continue across multiple turns. Frontend shows mode selector and routes correctly.

---

## Phase 4: User Story 2 — Pronunciation Error Detection and Feedback (Priority: P2)

**Goal**: When the user mispronounces a word, the system's response explicitly addresses it and `pronunciation_events` in the API response contains structured error data.

**Independent Test**: POST a WAV with a deliberate mispronunciation (use `tests/fixtures/mispronounced_hello.wav`). Response `pronunciation_events` must contain ≥ 1 entry with non-empty `word`, `error_type`, `user_pronunciation`, and `correct_pronunciation`. `ai_text` must contain explicit mention of the correction.

### Implementation for User Story 2

- [x] T025 [US2] Extend omni service system prompt in `ai_services/omni/app/main.py` to require structured pronunciation metadata in the model's text output: format as `<!-- PRONUNCIATION_EVENTS: [...] -->` comment block after the spoken response text, parseable as JSON array of `PronunciationEvent` objects
- [x] T026 [US2] Implement pronunciation event extraction in `ai_services/omni/app/main.py`: parse the `<!-- PRONUNCIATION_EVENTS: [...] -->` block from the model's text output; populate `pronunciation_events` in the JSON response; fall back to empty list if block is absent or malformed
- [x] T027 [US2] Extend `QwenOmniHttpService` in `backend/src/infrastructure/omni_service.py` to deserialise `pronunciation_events` array from the omni service response into `List[PronunciationEvent]` and include in returned `OmniVoiceResult`
- [x] T028 [P] [US2] Create `frontend/components/PronunciationEventCard.tsx`: renders a single `PronunciationEvent` as a card showing the mispronounced word, error type badge, user form vs. correct form; accessible colour coding (not colour-only)
- [x] T029 [US2] Update `frontend/components/ChatInterface.tsx` to render `PronunciationEventCard` list below the audio player after each omni turn; cards appear only when `pronunciation_events.length > 0`

**Checkpoint**: Pronunciation errors are detected from audio, structured data is returned in the API, and the frontend displays them visually alongside the audio response.

---

## Phase 5: User Story 3 — Pronunciation Coaching with Guided Practice Drill (Priority: P3)

**Goal**: After an error is identified, the system prompts the user to repeat the correct form, evaluates the repetition, and confirms success or offers a second correction attempt (max 2 per word).

**Independent Test**: After receiving a response with a pronunciation event, the user speaks the same word again. The next `pronunciation_events` entry for that word should have `correction_attempted: true` and `correction_succeeded: true | false`. The `ai_text` should confirm success or offer a second correction. A third attempt is not made — the session moves on naturally.

### Implementation for User Story 3

- [x] T030 [US3] Add `drill_state` tracking to `OmniVoiceSession` entity in `backend/src/domain/entities.py`: dict mapping `word → attempt_count` (max 2); reset when session moves to a new topic
- [x] T031 [US3] Update `ProcessOmniVoiceUseCase` in `backend/src/application/use_cases.py` to inject `drill_state` context into the omni service call when the previous turn had open `PronunciationEvent`s with `correction_attempted: false`; cap drill attempts at 2 per word and mark `correction_succeeded` based on whether the event reappears in the follow-up turn
- [x] T032 [US3] Extend omni service prompt in `ai_services/omni/app/main.py` to handle drill context: when `context` includes an open correction, instruct model to (a) acknowledge whether the user's pronunciation improved, (b) confirm success if correct, (c) offer one more specific tip if still incorrect, (d) move on naturally after second attempt regardless
- [x] T033 [US3] Update `frontend/components/PronunciationEventCard.tsx` to show drill status: "Awaiting your repetition" (correction_attempted: false), "Correct!" (correction_succeeded: true), "Keep practising" (correction_succeeded: false)

**Checkpoint**: Full pronunciation correction drill works — detection, prompted repetition, evaluation, and natural continuation are all functional.

---

## Phase 6: User Story 4 — Graceful Fallback When Omni Channel Is Unavailable (Priority: P4)

**Goal**: When the omni service is offline or errors mid-session, the user receives a clear message, standard mode continues unaffected, and no crashes or audio artifacts occur.

**Independent Test**: Stop the `lingo-omni` container. `POST /conversation/omni/speech` returns `503` with `{"detail": "omni_unavailable"}`. `POST /conversation/speech` (standard) returns `200 OK`. `GET /conversation/omni/status` returns `{"omni_enabled": false, ...}`. Frontend shows a toast and reverts to standard mode.

### Implementation for User Story 4

- [x] T034 [US4] Add `OmniServiceUnavailableError` exception class in `backend/src/infrastructure/omni_service.py`; catch `httpx.ConnectError`, `httpx.TimeoutException`, and non-2xx responses; raise `OmniServiceUnavailableError` in all cases
- [x] T035 [US4] Update `POST /conversation/omni/speech` handler in `backend/src/main.py` to catch `OmniServiceUnavailableError` and return `HTTPException(status_code=503, detail="omni_unavailable")`; ensure no exception propagates to the existing standard endpoints
- [x] T036 [US4] Update `GET /conversation/omni/status` in `backend/src/main.py` to catch connection errors to `OMNI_API_URL/health` and return `{"omni_enabled": false, "model_loaded": false, "omni_api_url": null}` rather than raising an exception
- [x] T037 [P] [US4] Add frontend toast notification in `frontend/components/ChatInterface.tsx`: on `503` response from omni endpoint, show non-blocking toast "Voice Tutor mode is currently unavailable. Standard mode is still active." and switch mode selector back to Standard
- [x] T038 [P] [US4] Add mid-session error recovery in `frontend/components/ChatInterface.tsx`: if an omni request fails after at least one successful turn, stop spinner, show toast, preserve prior transcript display; do not clear `omniConversationId` (allows retry if service recovers)

**Checkpoint**: Omni channel failure is fully isolated. Standard pipeline is provably unaffected. Frontend handles unavailability gracefully at all stages.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Test fixtures, documentation, and final regression verification.

- [x] T039 [P] Create `tests/fixtures/sample_hello.wav` — short clean pronunciation of "hello" (≥ 1s, ≤ 5s WAV); used by quickstart Scenario 2 and backend unit tests
- [x] T040 [P] Create `tests/fixtures/mispronounced_hello.wav` — recording with deliberate short-vowel error on "hello"; used by quickstart Scenario 3
- [x] T041 [P] Create `tests/fixtures/sample_followup.wav` — contextual follow-up utterance ("How do you say 'world'?"); used by quickstart Scenario 4
- [x] T042 [P] Create `tests/fixtures/long_audio_70s.wav` — silent or minimal WAV exceeding 60 seconds; used by quickstart Scenario 7
- [x] T043 Add `OMNI_ENABLED` and `OMNI_API_URL` entries to `.env.example` (or create it if absent) with comments explaining model weight installation path
- [x] T044 Update `ai_services/omni/README.md` (create if absent) with: model download instructions, hardware requirements (VRAM estimate), `docker-compose up omni` quickstart, and reference to `specs/007-omni-voice-channel/quickstart.md`
- [x] T045 Run full pytest suite (`pytest tests/ -v`) and confirm all pre-existing tests still pass; fix any regressions before marking done
- [x] T046 Run quickstart.md Scenarios 1–7 manually and confirm all pass; document any observed deviations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — first story; can start once foundation is ready
- **US2 (Phase 4)**: Depends on Phase 3 checkpoint — pronunciation events are built on top of the working audio channel
- **US3 (Phase 5)**: Depends on Phase 4 checkpoint — drill requires pronunciation detection to be working
- **US4 (Phase 6)**: Can start after Phase 2 — error paths are independent of pronunciation logic; can be developed in parallel with US2/US3
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

| Story | Depends On | Can Parallel |
|-------|-----------|-------------|
| US1 (P1) | Phase 2 | — |
| US2 (P2) | US1 checkpoint | — |
| US3 (P3) | US2 checkpoint | — |
| US4 (P4) | Phase 2 | US2, US3 |

### Within Each User Story

- Backend service/infrastructure tasks → before use case tasks → before endpoint tasks
- Frontend tasks marked [P] → can run alongside backend tasks (different files)
- Omni service (`ai_services/omni/`) tasks → before backend integration tasks that call it

---

## Parallel Opportunities

### Phase 2 (Foundational) — run together

```
T004 (entities) + T005 (interface) + T006 (config) → then T007 (repository, depends on T004)
```

### Phase 3 (US1) — parallel groups

```
Group A (service layer):
  T013 QwenOmniHttpService   |  T014 ProcessOmniVoiceUseCase

Group B (omni service):
  T008 requirements.txt   |  T009 Dockerfile

Group C (frontend):
  T020 mode selector   |  T021 OmniStatusBadge

Group D (tests):
  T023 test_omni_use_case.py   |  T024 test_omni_service.py
```

### Phase 6 (US4) — parallel

```
T037 frontend toast   |  T038 mid-session recovery
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks everything)
3. Complete Phase 3: US1 (T008–T024)
4. **STOP and VALIDATE**: Run quickstart Scenarios 1–2 and confirm end-to-end audio works
5. Demo: user speaks → system responds with audio → session continues across turns

### Incremental Delivery

1. Setup + Foundational → domain model ready
2. US1 → working audio channel (MVP) ✅
3. US2 → pronunciation error display ✅
4. US3 → correction drills ✅
5. US4 → graceful degradation (can be interleaved with US2/US3) ✅
6. Polish → fixtures, docs, regression pass ✅

### Parallel Team Strategy

With two developers after Phase 2:
- **Dev A**: US1 backend (T008–T019) + US4 backend (T034–T036)
- **Dev B**: US1 frontend (T020–T022) + US2/US3 frontend (T028–T029, T033)

---

## Notes

- [P] tasks = independent files, no intra-phase ordering required
- [Story] label maps each task to a spec.md user story for traceability
- Model weights for `ai_services/omni/` must be user-supplied; document clearly in T044
- `OMNI_ENABLED=false` by default — existing deployments are unaffected until user opts in
- Commit after each checkpoint to keep rollback points clean
- Standard endpoints (`/conversation/speech`, `/conversation/text`, `/health`) must not be touched
