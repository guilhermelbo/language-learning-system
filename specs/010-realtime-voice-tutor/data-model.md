# Data Model: Real-Time Voice Tutor Conversation

## Entities

### VoiceTurnStream *(new — replaces single-shot response)*

A single real-time turn: from when the user stops speaking to when the tutor finishes responding.

| Field | Type | Description |
|-------|------|-------------|
| `turn_id` | UUID | Unique identifier for this exchange |
| `session_id` | UUID | Parent session (reuses existing OmniVoiceSession) |
| `audio_bytes` | bytes | User's recorded audio blob (received by backend) |
| `transcript_user` | str | Extracted USER_TRANSCRIPT from LLM response |
| `full_text` | str | Complete tutor response text (accumulated from stream) |
| `sentences` | list[SentenceChunk] | Ordered list of sentence-audio pairs |
| `pronunciation_events` | list[PronunciationEvent] | Reuses existing entity |
| `state` | TurnState | Current processing state |

### SentenceChunk *(new)*

A complete sentence extracted from the LLM stream, paired with its TTS audio.

| Field | Type | Description |
|-------|------|-------------|
| `index` | int | Position in response (0-based) |
| `text` | str | Clean sentence text |
| `audio_bytes` | bytes | WAV audio from Piper TTS |
| `tts_ok` | bool | False if TTS failed (degraded mode: no audio, text still shown) |

### SilenceConfig *(new — frontend only, not persisted)*

User-configurable silence detection settings.

| Field | Type | Default | Range |
|-------|------|---------|-------|
| `silence_threshold_ms` | int | 2000 | 1000–5000 |
| `min_speech_ms` | int | 500 | fixed |
| `rms_silence_level` | float | 30.0 | calibrated per session |

---

## State Machines

### ConversationLoopState (frontend)

```
IDLE
  │ (enter Voice Tutor mode)
  ▼
LISTENING ◄─────────────────────────────────────┐
  │ (RMS drops below threshold)                 │
  ▼                                             │
SILENCE_COUNTDOWN                               │
  │ (RMS rises — user continues)                │ (done event + queue empty)
  ├──────────────────────────────────────────────┤
  │ (countdown reaches 0)                        │
  ▼                                              │
SENDING                                         │
  │ (SSE stream starts)                          │
  ▼                                              │
TUTOR_RESPONDING                                │
  │ (first sentence_audio event)                 │
  ▼                                              │
PLAYING_AUDIO ───────────────────────────────────┘
```

Additional transitions:
- Any state → `IDLE`: user clicks "Exit Voice Tutor"
- `LISTENING` → `IDLE`: 30 seconds of no speech (inactivity guard, shows "Tap to continue")

### TurnState (backend — for tracking stream progress)

```
RECEIVED → CONVERTING → LLM_STREAMING → TTS_DISPATCHING → COMPLETE
                                                         └→ ERROR
```

---

## SSE Event Schema (backend → frontend)

All events are typed. The frontend switches on `event` field.

```
event: transcript
data: {"user_text": "<string>"}

event: text_delta
data: {"delta": "<string>"}

event: sentence_audio
data: {"index": 0, "text": "<sentence>", "audio_base64": "<base64 wav>", "tts_ok": true}

event: pronunciation_events
data: [{"word": "...", "error_type": "...", "user_pronunciation": "...", "correct_pronunciation": "...", "correction_attempted": false, "correction_succeeded": null}]

event: done
data: {"conversation_id": "omni-<uuid>"}

event: error
data: {"detail": "<string>"}
```

---

## Reused Entities (unchanged)

- **OmniVoiceSession**: Multi-turn session tracking. The streaming endpoint reuses the same session model. `session_id` is carried forward as `conversation_id` (prefixed `omni-`).
- **OmniAudioTurn**: Persisted after each turn completes (same as current non-streaming flow). The stream adds no new persistent entities.
- **PronunciationEvent**: Unchanged. Populated from the `<!-- PRONUNCIATION_EVENTS: [...] -->` block once the full response is assembled.

---

## Interface Changes

### `OmniVoiceService` (domain interface — `domain/interfaces.py`)

New method added alongside existing `process_speech`:

```
process_speech_stream(audio: bytes, language: str, context: list | None)
  → AsyncGenerator[dict, None]   # yields SSE event dicts
```

The existing `process_speech` method remains unchanged (used by the current non-streaming endpoint).

### `OpenAICompatibleVoiceService` (infrastructure)

Adds `_call_llm_stream()` private method (streaming variant of `_call_llm`) and implements `process_speech_stream()`.
