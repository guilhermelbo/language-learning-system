# Tasks: Real-Time Voice Tutor Conversation

**Input**: Design documents from `specs/010-realtime-voice-tutor/`

**Scope**: 2 new backend files, 5 modified backend files, 3 new frontend files, 1 modified frontend file.

**Pipeline**: Browser mic → Web Audio VAD (silence detection) → WebM blob → SSE POST → backend converts to WAV → llamacpp stream → sentence split → Piper TTS per sentence → SSE events (text_delta, sentence_audio, done) → frontend progressive display + queued audio → mic re-enabled.

---

## Phase 1: Setup

**Purpose**: Add the only new backend dependency.

- [X] T001 Add `sse-starlette` to `backend/requirements.txt` (new line after `responses`)

**Checkpoint**: Dependency declared.

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Extend the domain interface so all story phases can implement against it.

- [X] T002 Add abstract method `process_speech_stream(self, audio: bytes, language: str, context: list | None) -> AsyncGenerator[dict, None]` to `OmniVoiceService` in `backend/src/domain/interfaces.py` — import `AsyncGenerator` from `typing`, add method with `...` body; add `from __future__ import annotations` if needed for forward ref

**Checkpoint**: Domain interface updated. US1 backend and frontend work can begin in parallel.

---

## Phase 3: User Story 1 — Hands-Free Voice Conversation (Priority: P1) 🎯 MVP

**Goal**: User enters Voice Tutor mode → mic activates automatically → speaks → silence detected → audio sent → tutor responds → mic re-enables. Zero button presses.

**Independent Test**: `cd backend && docker compose up --build -d backend` then `curl -X POST http://localhost:8000/conversation/omni/speech/stream -F "file=@/tmp/test.wav" -H "Accept: text/event-stream"` returns SSE stream with `transcript`, `sentence_audio`, `done` events. In browser: switch to Voice Tutor, speak, wait 2s, receive response without pressing any button.

### Backend — US1

- [X] T003 [US1] Add `_sentence_buffer_splitter(tokens: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]` async generator helper to `backend/src/infrastructure/llm_voice_service.py` — buffers incoming tokens, yields complete sentences when `[.!?…]\s` boundary detected; flushes remaining buffer on exhaustion; place after `_build_system_prompt`
- [X] T004 [US1] Implement `_call_llm_stream(self, audio: bytes, language: str, context: list | None) -> AsyncGenerator[str, None]` private async generator in `backend/src/infrastructure/llm_voice_service.py` — identical payload to `_call_llm` but adds `"stream": True`; uses `async with httpx.AsyncClient().stream("POST", ...)` and `async for line in resp.aiter_lines()`; skips `data: [DONE]`; extracts `json.loads(line[6:])["choices"][0]["delta"].get("content") or ""`; yields non-empty strings; raises `VoiceServiceUnavailableError` on ConnectError/TimeoutException/non-2xx
- [X] T005 [US1] Implement `process_speech_stream(self, audio: bytes, language: str, context: list | None) -> AsyncGenerator[dict, None]` in `backend/src/infrastructure/llm_voice_service.py` — orchestration: (1) convert audio to WAV via `_to_wav` if needed, (2) stream tokens via `_call_llm_stream`, (3) extract and yield `{"event": "transcript", "data": json.dumps({"user_text": transcript})}` when `USER_TRANSCRIPT` block detected in accumulated text, (4) yield `{"event": "text_delta", "data": json.dumps({"delta": token})}` per token, (5) for each sentence from `_sentence_buffer_splitter` call `_synthesize` and yield `{"event": "sentence_audio", "data": json.dumps({"index": i, "text": sentence, "audio_base64": b64, "tts_ok": True})}`, (6) yield `{"event": "pronunciation_events", "data": json.dumps(events)}`, (7) yield `{"event": "done", "data": json.dumps({"conversation_id": ""})}` — conversation_id filled by use case; wrap entire body in try/except to yield `{"event": "error", "data": json.dumps({"detail": str(exc)})}` on VoiceServiceUnavailableError
- [X] T006 [P] [US1] Add `ProcessOmniVoiceStreamUseCase` class to `backend/src/application/use_cases.py` — constructor same as `ProcessOmniVoiceUseCase` (omni_service, session_repo); implement `async def execute_stream(self, audio_data: bytes, session: OmniVoiceSession | None, language: str) -> AsyncGenerator[dict, None]`: builds context same way as `ProcessOmniVoiceUseCase.execute`, calls `self.omni.process_speech_stream(audio, language, context)`, yields all events through; on `done` event: updates `conversation_id` field in event data with `session.omni_id`, saves session to repo (accumulate transcript and ai_text from prior events into an `OmniAudioTurn` and call `session.add_turn` + `session_repo.save`)
- [X] T007 [US1] Instantiate `ProcessOmniVoiceStreamUseCase` in `backend/src/main.py` — import it, add `omni_stream_use_case: ProcessOmniVoiceStreamUseCase | None = None` module-level variable, instantiate inside the `if settings.voice_enabled:` block alongside `omni_use_case`
- [X] T008 [US1] Add `POST /conversation/omni/speech/stream` endpoint to `backend/src/main.py` — import `EventSourceResponse` from `sse_starlette.sse`; endpoint accepts `file: UploadFile`, `conversation_id: Optional[str] = Form(default=None)`, `language: str = Form(default="en-US")`; validates `voice_enabled` + `omni_stream_use_case`, enforces audio size limit; resolves session same as `/conversation/omni/speech`; defines `async def event_generator()` that calls `omni_stream_use_case.execute_stream(...)` and yields each dict; returns `EventSourceResponse(event_generator())`; catches `VoiceServiceUnavailableError` inside generator and yields error event

### Frontend — US1

- [X] T009 [P] [US1] Create `frontend/hooks/useVoiceActivityDetection.ts` — exports `useVoiceActivityDetection(onSendAudio: (blob: Blob) => Promise<void>, config?: Partial<SilenceConfig>): UseVADResult` hook; implements full state machine (`idle|listening|silence_countdown|sending|tutor_responding|playing_audio`); uses `AudioContext` + `AnalyserNode` (FFT 2048) for RMS VAD every 100ms (silence = RMS < 30/255); uses `MediaRecorder` concurrently for blob accumulation; on silence trigger: stops recorder, calls `onSendAudio(blob)`; exposes `state`, `start()`, `stop()`, `config`, `setConfig()`; `start()` calls `getUserMedia` and activates loop; `stop()` tears down AudioContext and MediaRecorder; `start()` transitions `idle → listening`; silence detected transitions `listening → silence_countdown`; countdown elapsed (minSpeechMs met) transitions `silence_countdown → sending`; external state setters `setTutorResponding()`, `setPlayingAudio()`, `setListening()` to allow parent component to advance state after SSE events
- [X] T010 [US1] Create `frontend/components/VoiceTutorLive.tsx` — uses `useVoiceActivityDetection`; on state enter `sending`: opens SSE connection to `POST /conversation/omni/speech/stream` (using `fetch` with `ReadableStream` body reader); accumulates `user_text` from `transcript` event; accumulates `ai_text` from `text_delta` events; queues `sentence_audio` events into `AudioBuffer` array; on `done` event: adds message pair to conversation list, starts sequential audio playback via `AudioBufferSourceNode` queue, calls `setListening()` after queue drains; shows state indicator badge (`listening` / `thinking` / `speaking`); renders conversation history with `Message` components; wraps `useVoiceActivityDetection` and wires `onSendAudio`
- [X] T011 [US1] Modify `frontend/app/page.tsx` — when `voiceMode === "omni"`: render `<VoiceTutorLive conversationId={omniConversationId} onConversationIdChange={setOmniConversationId} language="en-US" />` in the footer area instead of the current `VoiceButton` + `handleOmniRecordingComplete` path; keep `VoiceButton` only for `voiceMode === "standard"`; keep all standard mode logic unchanged

**Checkpoint**: Hands-free loop works. No button presses. Direct curl test and browser test both pass per `quickstart.md` scenarios 1–8.

---

## Phase 4: User Story 2 — Streaming Tutor Response (Priority: P2)

**Goal**: Response text appears progressively token by token. First sentence plays as audio before full response arrives.

**Independent Test**: In Voice Tutor mode, ask a question requiring 2+ sentences. Observe text appearing word-by-word AND first sentence audio playing before second sentence text appears.

- [X] T012 [US2] Upgrade `frontend/hooks/useVoiceActivityDetection.ts` — add `streamingText: string` to `UseVADResult`; expose setter internally; in the SSE consumer: on each `text_delta` event append delta to `streamingText` state; on each `sentence_audio` event: decode base64 WAV, create `AudioBuffer`, enqueue and start playback immediately if queue was empty (not waiting for `done`); clear `streamingText` when transitioning back to `listening`
- [X] T013 [US2] Upgrade `frontend/components/VoiceTutorLive.tsx` — during `tutor_responding` state: render an in-progress message bubble showing `streamingText` from hook with a blinking cursor; when `done` event arrives replace the streaming bubble with the final committed message; do not wait for audio to finish before showing committed text

**Checkpoint**: Text streams progressively. First sentence audio plays before full response is on screen.

---

## Phase 5: User Story 3 — Configurable Silence Threshold (Priority: P3)

**Goal**: User can adjust silence detection duration (1–5 seconds) without reloading.

**Independent Test**: Set threshold to 4s, speak a sentence, wait — system does not send until after 4 full seconds of silence.

- [X] T014 [P] [US3] Create `frontend/components/SilenceThresholdControl.tsx` — renders a horizontal range `<input>` (min=1, max=5, step=0.5), labeled "Silence threshold: Xs"; accepts `value: number`, `onChange: (seconds: number) => void` props; default displayed value 2
- [X] T015 [US3] Integrate `SilenceThresholdControl` in `frontend/components/VoiceTutorLive.tsx` — add `thresholdSeconds` state (default 2); render `<SilenceThresholdControl>` below the state badge when in `idle` or `listening` state; pass `thresholdSeconds * 1000` as `config.silenceThresholdMs` to `useVoiceActivityDetection`

**Checkpoint**: Slider visible in Voice Tutor mode. Changing it affects next turn.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T016 [P] Add 30-second inactivity guard to `frontend/hooks/useVoiceActivityDetection.ts` — if state remains `listening` for 30s without any RMS spike above threshold, call `stop()` and expose `inactive: boolean` flag in `UseVADResult`; reset on next `start()` call
- [X] T017 [P] Add microphone permission error handling to `frontend/hooks/useVoiceActivityDetection.ts` — wrap `getUserMedia` in try/catch; on `NotAllowedError` or `NotFoundError`, expose `micError: string | null` in `UseVADResult` with human-readable message; do not transition to `listening` state
- [X] T018 Add `micError` and `inactive` display to `frontend/components/VoiceTutorLive.tsx` — when `micError` is non-null show error card with message and a "Switch to Standard Mode" button; when `inactive` is true show "Tap to continue" pill that calls `start()` on click
- [X] T019 Rebuild backend and run quickstart validation: `docker compose up --build -d backend` then execute curl scenarios 1–4 from `specs/010-realtime-voice-tutor/quickstart.md` and verify expected SSE event sequences

---

## Dependencies & Execution Order

- **Phase 1** (T001): Start immediately
- **Phase 2** (T002): Depends on Phase 1
- **Phase 3** (T003–T011): Depends on Phase 2 (T002 interface must exist)
  - Backend sequential: T003 → T004 → T005 → T007 → T008 (T006 can run parallel with T003–T005)
  - Frontend runs fully in parallel with backend: T009 → T010 → T011
- **Phase 4** (T012–T013): Depends on Phase 3 complete
- **Phase 5** (T014–T015): Depends on Phase 3 complete; can run in parallel with Phase 4
- **Phase 6** (T016–T019): Depends on Phases 4 and 5

---

## Parallel Opportunities Per Phase

```
# After T002 completes, start these simultaneously:
Backend stream:   T003 → T004 → T005
                  T006 (parallel with T003/T004/T005 — different logical section of use_cases.py)
Frontend stream:  T009 → T010 → T011 (completely different files)

# After Phase 3 completes, start simultaneously:
US2 stream upgrades: T012 → T013
US3 threshold:       T014 → T015
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. T001 (dependency) → T002 (interface) → T003–T008 (backend) || T009–T011 (frontend)
2. **STOP and VALIDATE**: curl test + browser hands-free conversation
3. Ship: hands-free Voice Tutor with response text shown on `done`, audio queued from `sentence_audio`

### Full Feature

1. MVP complete → T012–T013 (streaming text + progressive audio)
2. T014–T015 (threshold slider)
3. T016–T019 (polish + validation)

---

## Notes

- `process_speech_stream` in `OpenAICompatibleVoiceService` must handle the case where llamacpp does NOT support `stream: true` with `input_audio`. Risk mitigation: if streaming fails (non-200, or stream yields nothing), fall back to non-streaming `_call_llm`, then split result into sentences and yield the same SSE events. Add this fallback inside T005.
- The `done` event from `process_speech_stream` yields `conversation_id: ""` — `ProcessOmniVoiceStreamUseCase` must overwrite this with the actual `session.omni_id` before forwarding to the frontend.
- Frontend SSE consumption uses `fetch` with `ReadableStream` reader (not `EventSource`) because `EventSource` does not support POST requests. Parse lines manually: skip empty lines, `data: ` prefix → `JSON.parse(line.slice(6))`.
