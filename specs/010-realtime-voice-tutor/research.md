# Research: Real-Time Voice Tutor Conversation

## Decision 1: Voice Activity Detection (VAD) — Browser Side

**Decision**: Web Audio API `AnalyserNode` + `MediaRecorder`, no external library.

**Approach**:
- `getUserMedia` → `AudioContext` → `AnalyserNode` for continuous RMS sampling (every 100ms)
- Simultaneously feed stream to `MediaRecorder` for blob accumulation
- RMS silence threshold: < 30 on a 0–255 scale (from `getByteFrequencyData`); requires >= 0.5s of speech above threshold before a turn is considered valid
- When RMS stays below threshold for the configured duration (default: 2s), stop `MediaRecorder` and send the blob
- Use `AudioWorklet` (not deprecated `ScriptProcessorNode`) for off-thread processing

**Rationale**: Zero dependencies, works in all modern browsers, integrates naturally with `MediaRecorder` for blob capture. External libraries (e.g., `@ricky0123/vad-web`) add bundle weight and WASM complexity for marginal gain.

**Alternatives considered**:
- `@ricky0123/vad-web` (Silero VAD): More accurate, but requires WASM bundle (~2MB) and is overkill for silence detection. Could be a future upgrade.
- WebRTC `RTCPeerConnection`: Not applicable — no peer needed; overkill.

---

## Decision 2: Streaming Protocol — Server to Client

**Decision**: SSE (Server-Sent Events) via `sse-starlette` package, `EventSourceResponse` on a POST endpoint.

**Package**: `sse-starlette` (adds `EventSourceResponse` with proper `data: …\n\n` framing).

**Pattern**:
```python
from sse_starlette.sse import EventSourceResponse

@app.post("/conversation/omni/speech/stream")
async def stream_omni(file: UploadFile, ...):
    async def generate():
        async for event in use_case.execute_stream(...):
            yield event   # dict with "event" and "data" keys
    return EventSourceResponse(generate())
```

**Rationale**: Unidirectional (server→client), HTTP/1.1 compatible, no persistent connection management. Simpler than WebSocket for this use case where the client sends audio once and receives a stream of events back.

**Alternatives considered**:
- WebSocket: Bidirectional capability unused here; adds connection lifecycle complexity.
- Plain `StreamingResponse`: Works but requires manual SSE framing (`data: …\n\n`) with no event typing.

---

## Decision 3: LLM Response Streaming from llamacpp

**Decision**: `httpx` async streaming with `client.stream()`, consuming newline-delimited JSON from llamacpp's `stream: true` mode.

**Pattern in `_call_llm_stream`**:
```python
async with httpx.AsyncClient(timeout=self._timeout) as client:
    async with client.stream("POST", f"{self._base_url}/chat/completions", json={**payload, "stream": True}) as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                delta = json.loads(line[6:])["choices"][0]["delta"].get("content") or ""
                if delta:
                    yield delta
```

**Note**: llamacpp supports `stream: true` with `input_audio` (multimodal) in the same `/v1/chat/completions` endpoint. The payload is identical to the non-streaming call except `"stream": True` is added.

**Rationale**: Already using `httpx` in `llm_voice_service.py`. The `AsyncOpenAI` client also supports streaming but requires replacing the existing httpx-based implementation. Staying with httpx is the minimal change.

**Alternatives considered**:
- `AsyncOpenAI` with `stream=True`: Clean API but requires migrating `_call_llm` to use the OpenAI SDK. Deferred to future refactor.

---

## Decision 4: Sentence Boundary Detection for Progressive TTS

**Decision**: Regex-based buffer — accumulate tokens until a sentence-ending punctuation followed by whitespace or end-of-stream is detected.

**Pattern**:
```python
SENTENCE_END = re.compile(r'(?<=[.!?…])\s+|(?<=[.!?…])$')

buffer = ""
async for token in llm_stream:
    buffer += token
    sentences = SENTENCE_END.split(buffer)
    while len(sentences) > 1:
        yield sentences.pop(0)   # complete sentence → send to TTS
        buffer = " ".join(sentences)  # remaining fragments
```

On stream end, flush any remaining buffer as the final sentence.

**Rationale**: No dependencies. Handles ~95% of natural sentences. Avoids splitting on abbreviations like "Dr." is an acceptable edge case for this use case.

**Alternatives considered**:
- NLTK `sent_tokenize`: More accurate but adds a large dependency and is synchronous. Out of scope for v1.

---

## Decision 5: SSE Event Schema

Five event types streamed from backend to frontend per turn:

| Event | Payload | Purpose |
|-------|---------|---------|
| `transcript` | `{"user_text": "..."}` | Extracted USER_TRANSCRIPT block |
| `text_delta` | `{"delta": "..."}` | Progressive LLM text tokens |
| `sentence_audio` | `{"text": "...", "audio_base64": "..."}` | Complete sentence + WAV audio |
| `pronunciation_events` | `[{...}]` | Pronunciation feedback events |
| `done` | `{"conversation_id": "omni-..."}` | Turn complete, mic can re-enable |
| `error` | `{"detail": "..."}` | Fatal error for this turn |

**Rationale**: Typed events allow the frontend to handle each independently — update transcript immediately, play audio as sentences arrive, show pronunciation cards on `done`.

---

## Decision 6: Frontend Audio Queuing

**Decision**: Web Audio API `AudioBuffer` queue played sequentially via `AudioBufferSourceNode.onended` chaining.

**Pattern**:
```
sentence_audio event received
  → decode base64 WAV → AudioBuffer
  → if nothing playing: play immediately
  → else: enqueue, play after current ends
  → all sentences done (done event): re-enable mic
```

**Rationale**: Guarantees sentence order. `AudioBufferSourceNode` is fire-and-forget; chaining via `onended` is the standard Web Audio API pattern for audio queues.

---

## Decision 7: State Machine for Conversation Loop

**States**: `idle` → `listening` → `silence_countdown` → `sending` → `tutor_responding` → `playing_audio` → `listening`

**Transitions**:
- `idle` → `listening`: User enters Voice Tutor mode
- `listening` → `silence_countdown`: Voice activity drops below RMS threshold
- `silence_countdown` → `listening`: Voice activity resumes (user continues speaking)
- `silence_countdown` → `sending`: Silence duration exceeds configured threshold
- `sending` → `tutor_responding`: SSE stream starts (`transcript` or `text_delta` received)
- `tutor_responding` → `playing_audio`: First `sentence_audio` event triggers audio playback
- `playing_audio` → `listening`: `done` event received + audio queue drained
- any → `idle`: User exits Voice Tutor mode

**Inactivity guard**: After 30 seconds in `listening` state with no speech detected (no RMS spike), transition to `idle` and show "Tap to continue" prompt.

---

## Constitution Compliance

| Principle | Status | Notes |
|-----------|--------|-------|
| Docker-First | ✅ Pass | New package (`sse-starlette`) added to requirements.txt; no new containers |
| LLM Independence | ✅ Pass | LLM call still via env-configured URL; streaming is just `stream: true` |
| Clean Architecture | ✅ Pass | `process_speech_stream` added to domain interface; implementation in infrastructure |
| Type Safety & Async | ✅ Pass | All new async generators typed; `httpx` streaming used |
| JSON Contract | ⚠️ Note | Voice Tutor SSE events do not use the `[{text, lang}]` JSON contract — intentional, different channel |
| Testing | ✅ Pass | Unit tests required for stream event generation and VAD logic |
