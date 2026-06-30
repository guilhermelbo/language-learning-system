# Tasks: llamacpp Voice Provider (Native Audio)

**Input**: Design documents from `specs/009-llamacpp-voice-provider/`

**Scope**: 1 new file, 3 modified files, 1 new test file. No domain changes, no API shape changes, no frontend changes.

**Pipeline**: Audio → base64 → `POST /v1/chat/completions` (input_audio) → parse USER_TRANSCRIPT + PRONUNCIATION_EVENTS → Piper TTS → audio response. No STT step.

**Tests**: Included per constitution (Section VI: "Tests are REQUIRED for all new features").

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the new config field that all feature tasks depend on.

- [X] T001 Add `voice_model_name: str = Field(default="", alias="VOICE_MODEL_NAME")` to `Settings` class in `backend/src/config.py` (after `voice_api_url` field)

**Checkpoint**: Config field available.

---

## Phase 3: User Story 1 — Student Holds a Spoken Conversation (Priority: P1) 🎯 MVP

**Goal**: Implement `OpenAICompatibleVoiceService` that sends audio directly to Gemma 4 via `input_audio` content type, parses transcript + pronunciation events from the response, and synthesizes audio via Piper TTS.

**Independent Test**: `pytest tests/test_llm_voice_service.py -v` — all tests pass.

### Tests for User Story 1

- [X] T002 [P] [US1] Create `backend/tests/test_llm_voice_service.py` with imports and helper `_make_response(status, body, binary)` — skeleton only
- [X] T003 [P] [US1] Add `test_extract_pronunciation_events_with_events` in `backend/tests/test_llm_voice_service.py` — verifies `_extract_pronunciation_events` parses block and strips it from text
- [X] T004 [P] [US1] Add `test_extract_pronunciation_events_no_block` in `backend/tests/test_llm_voice_service.py` — verifies returns full text and empty list when no block
- [X] T005 [P] [US1] Add `test_extract_user_transcript_present` in `backend/tests/test_llm_voice_service.py` — verifies `_extract_user_transcript` extracts content of USER_TRANSCRIPT block
- [X] T006 [P] [US1] Add `test_extract_user_transcript_absent` in `backend/tests/test_llm_voice_service.py` — verifies returns empty string when no block
- [X] T007 [P] [US1] Add `test_process_speech_success` in `backend/tests/test_llm_voice_service.py` — mocks LLM response with USER_TRANSCRIPT + PRONUNCIATION_EVENTS and TTS returning WAV bytes; asserts all `OmniVoiceResult` fields
- [X] T008 [P] [US1] Add `test_process_speech_llm_failure` in `backend/tests/test_llm_voice_service.py` — mocks LLM returning non-2xx; asserts `VoiceServiceUnavailableError` raised
- [X] T009 [P] [US1] Add `test_process_speech_tts_failure` in `backend/tests/test_llm_voice_service.py` — mocks LLM success, TTS non-2xx; asserts result has `audio_bytes=b""` and no exception propagated
- [X] T010 [P] [US1] Add `test_process_speech_with_context` in `backend/tests/test_llm_voice_service.py` — verifies prior-turn context messages appear as text in the messages array before the current `input_audio` message
- [X] T011 [P] [US1] Add `test_audio_base64_in_request` in `backend/tests/test_llm_voice_service.py` — verifies that `input_audio.data` in the LLM request is base64(audio bytes) and `format` is "wav"
- [X] T012 [P] [US1] Add `test_reasoning_content_none_handled` in `backend/tests/test_llm_voice_service.py` — mocks LLM response with `content=None` and `reasoning_content="..."` (thinking truncated); asserts `VoiceServiceUnavailableError` or graceful empty-content handling

### Implementation for User Story 1

- [X] T013 [US1] Create `backend/src/infrastructure/llm_voice_service.py` with module-level constants `TUTOR_SYSTEM_PROMPT` (from `ai_services/omni/app/main.py`, updated to include `<!-- USER_TRANSCRIPT: ... -->` block instruction) and `DRILL_CONTEXT_PROMPT` (from same file)
- [X] T014 [US1] Add helpers `_extract_pronunciation_events(text: str) -> tuple[str, list]` and `_extract_user_transcript(text: str) -> str` to `backend/src/infrastructure/llm_voice_service.py` — regex parsers for embedded blocks
- [X] T015 [US1] Add `_build_system_prompt(context: list | None) -> str` helper to `backend/src/infrastructure/llm_voice_service.py` — builds full system prompt with optional DRILL_CONTEXT_PROMPT addendum for open corrections
- [X] T016 [US1] Add `OpenAICompatibleVoiceService` class to `backend/src/infrastructure/llm_voice_service.py` — constructor accepts `base_url: str`, `model: str`, `api_key: str | None`, `tts_api_url: str`, `timeout: int`
- [X] T017 [US1] Implement `_call_llm(self, audio: bytes, language: str, context: list | None) -> str` private method in `backend/src/infrastructure/llm_voice_service.py`:
  - base64-encode `audio`
  - Build `messages` list: system message + prior turns (text only, from context) + current user message with `[{type: "input_audio", input_audio: {data: b64, format: "wav"}}, {type: "text", text: "..."}]`
  - `POST {base_url}/chat/completions` with `model`, `messages`, `max_tokens=1024`; add `Authorization: Bearer` header if `api_key` is set
  - Extract `payload["choices"][0]["message"].get("content") or ""`; raise `VoiceServiceUnavailableError` if empty/None
  - Raise `VoiceServiceUnavailableError` on `ConnectError`, `TimeoutException`, or non-2xx
- [X] T018 [US1] Implement `_synthesize(self, text: str, language: str) -> bytes` private method in `backend/src/infrastructure/llm_voice_service.py`:
  - Map language: `"en-US"`/`"en"` → `"en"`, `"pt-BR"`/`"pt"` → `"pt"`, else `"en"`
  - `POST {tts_api_url}/` with JSON `{"text": text, "lang": mapped_lang}`
  - Return response bytes; return `b""` on any error (degraded mode, no exception)
- [X] T019 [US1] Implement `process_speech(self, audio: bytes, language: str, context: list | None) -> OmniVoiceResult` public method in `backend/src/infrastructure/llm_voice_service.py`:
  - Call `_call_llm` → full response text
  - Extract `_extract_user_transcript(text)` → `transcript_user`
  - Extract `_extract_pronunciation_events(text)` → `(clean_text, raw_events)`
  - Strip USER_TRANSCRIPT block from `clean_text` if present
  - Convert `raw_events` dicts to `PronunciationEvent` dataclass instances
  - Call `_synthesize(clean_text, language)` → `audio_bytes`
  - Return `OmniVoiceResult(audio_bytes=audio_bytes, transcript_user=transcript_user, transcript_assistant=clean_text, pronunciation_events=pronunciation_events)`
- [X] T020 [US1] Implement `health_check(self) -> dict` in `backend/src/infrastructure/llm_voice_service.py`:
  - `GET {base_url}/health` (or `/models` as fallback); return `{"status": "ok", "model_loaded": True}` on success
  - Return `{"status": "unreachable", "model_loaded": False}` on any error
- [X] T021 [US1] Run tests: `cd backend && pytest tests/test_llm_voice_service.py -v` — all must pass

**Checkpoint**: `OpenAICompatibleVoiceService` implemented and all unit tests pass.

---

## Phase 4: User Story 2 — Developer Enables Voice Channel with Zero New Services (Priority: P2)

**Goal**: Wire service into factory and configure docker-compose.

**Independent Test**: Set `VOICE_PROVIDER=openai_compatible` and call `GET /conversation/omni/status` → `{"omni_enabled": true, "model_loaded": true}`.

- [X] T022 [US2] Add `openai_compatible` case to `create_voice_service()` in `backend/src/infrastructure/voice_factory.py`:
  - Import `OpenAICompatibleVoiceService`
  - When `provider == "openai_compatible"` return `OpenAICompatibleVoiceService(base_url=settings.voice_api_url, model=settings.voice_model_name, api_key=settings.llm_api_key, tts_api_url=settings.tts_api_url, timeout=settings.voice_timeout_seconds)`
  - Update error message to list `"openai_compatible"` as supported value
- [X] T023 [US2] Update `docker-compose.yml` backend env vars: set `VOICE_PROVIDER=openai_compatible`, `VOICE_API_URL=http://host.docker.internal:8080/v1`, add `VOICE_MODEL_NAME=gemma-4-12B-it-Q5_K_M.gguf`

**Checkpoint**: Backend starts with `VOICE_PROVIDER=openai_compatible`. US2 complete.

---

## Phase 5: User Story 3 — Session Continuity (Priority: P3)

**Goal**: Confirm multi-turn context is passed correctly (no new code — validate wire-up).

- [X] T024 [US3] Verify `_call_llm` builds messages correctly from context: prior turns as text-only messages, current turn as multimodal `input_audio` — confirm context items with `role`/`content` are included and correction dicts are used only for `_build_system_prompt` DRILL_CONTEXT_PROMPT
- [X] T025 [US3] Run full backend test suite: `cd backend && pytest -v`

**Checkpoint**: All existing tests pass + new tests pass. Full feature complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Verify all public and private methods in `backend/src/infrastructure/llm_voice_service.py` have type hints (constitution Section IV)
- [X] T027 [P] Verify `backend/src/infrastructure/voice_factory.py` has no unused imports
- [ ] T028 Rebuild backend container: `docker compose up --build -d backend` and verify `/conversation/omni/status` returns `omni_enabled: true`

---

## Dependencies & Execution Order

- **Phase 2** (T001): Start immediately
- **Phase 3** (T002–T021): Depends on Phase 2
  - Tests (T002–T012): write in parallel after T002 skeleton exists
  - Implementation (T013–T020): sequential — constants → helpers → class constructor → methods → process_speech → health_check
- **Phase 4** (T022–T023): Depends on Phase 3 complete (T016 must exist before T022 imports it)
- **Phase 5** (T024–T025): Depends on Phase 4
- **Phase 6** (T026–T028): Depends on all story phases

---

## Implementation Strategy

### MVP

1. T001 (config) → T002–T012 (write tests) → T013–T020 (implement) → T021 (run tests)
2. At this point, the full pipeline is implemented and unit-tested
3. T022–T023 to wire up and deploy

### Notes

- `reasoning_content` in LLM response: guard with `.get("content") or ""` — if None/empty, raise VoiceServiceUnavailableError (response was truncated)
- Context items from `ProcessOmniVoiceUseCase` include both `{"role": ..., "content": ...}` messages AND correction dicts (no `role` key). Filter: only items with `role` key go into messages array; items without `role` go into `_build_system_prompt` for DRILL_CONTEXT_PROMPT
- TUTOR_SYSTEM_PROMPT must include instruction to emit `<!-- USER_TRANSCRIPT: ... -->` block
