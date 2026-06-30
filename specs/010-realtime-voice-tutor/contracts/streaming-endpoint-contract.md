# Contract: Streaming Voice Tutor Endpoint

## Endpoint

```
POST /conversation/omni/speech/stream
Content-Type: multipart/form-data
Accept: text/event-stream
```

## Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary (audio) | Yes | User audio blob (WAV or WebM — backend converts to WAV) |
| `conversation_id` | string | No | Prior session ID (`omni-<uuid>`) for multi-turn continuity |
| `language` | string | No | Target language tag (default: `en-US`) |

## Response: SSE Event Stream

The response is an SSE stream (`Content-Type: text/event-stream`). Events arrive in this order:

### 1. `transcript` — User's speech as heard by the model
```
event: transcript
data: {"user_text": "Hello, how are you today?"}
```
Arrives as soon as the LLM response is parsed. May arrive before or interleaved with `text_delta`.

### 2. `text_delta` — Progressive LLM text tokens
```
event: text_delta
data: {"delta": "Great "}
```
One event per token batch. Frontend accumulates these to show the full response progressively.

### 3. `sentence_audio` — Complete sentence with synthesized audio
```
event: sentence_audio
data: {"index": 0, "text": "Great to meet you!", "audio_base64": "<base64 wav>", "tts_ok": true}
```
Emitted as each sentence boundary is detected and TTS completes. `tts_ok: false` means TTS failed but text is still valid (degraded mode — show text, skip audio for this sentence).

### 4. `pronunciation_events` — Pronunciation feedback
```
event: pronunciation_events
data: [{"word": "hello", "error_type": "vowel", "user_pronunciation": "hɛlo", "correct_pronunciation": "həˈloʊ", "correction_attempted": false, "correction_succeeded": null}]
```
Emitted once, after all sentences have been processed (empty array if no errors).

### 5. `done` — Turn complete
```
event: done
data: {"conversation_id": "omni-550e8400-e29b-41d4-a716-446655440000"}
```
Signals the stream is complete. Frontend should re-enable the microphone after audio queue drains.

### 6. `error` — Fatal error (replaces `done`)
```
event: error
data: {"detail": "omni_unavailable"}
```
Emitted if the backend cannot process the turn. The stream closes after this event.

---

## Status Codes

| Code | Condition |
|------|-----------|
| 200 | Stream started successfully (even if LLM later errors — check `error` event) |
| 400 | Invalid request (audio too long, malformed conversation_id) |
| 503 | Voice service not enabled |

---

## Ordering Guarantee

Events within a turn are emitted in this order:
1. `transcript` (when available)
2. N × (`text_delta`*, `sentence_audio`) — interleaved, sentence_audio may lag text_delta
3. `pronunciation_events`
4. `done` OR `error`

*`text_delta` events are not guaranteed to align perfectly with sentence boundaries. Frontend must accumulate them independently.

---

## Backward Compatibility

The existing non-streaming endpoint `POST /conversation/omni/speech` is **unchanged**. The new streaming endpoint is additive.
