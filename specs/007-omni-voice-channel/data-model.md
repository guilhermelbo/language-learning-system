# Data Model: Omni Voice Channel

**Feature**: 007-omni-voice-channel  
**Date**: 2026-06-27

---

## Domain Entities

### OmniVoiceSession

Represents an active speech-to-speech tutoring session using the native audio channel. Stored in-memory alongside the standard `Conversation` but keyed separately.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | Primary key, auto-generated |
| `student_id` | `UUID` | Links to Student entity |
| `turns` | `List[OmniAudioTurn]` | Ordered list of conversation turns |
| `created_at` | `datetime` | Session creation timestamp |
| `status` | `str` | `"active"` \| `"ended"` |

**Rules**:
- A session has at minimum 1 turn before being persisted
- Session `id` is namespaced with prefix `omni-` when exposed to the frontend to avoid collisions with standard `Conversation` ids

---

### OmniAudioTurn

One exchange within an OmniVoiceSession. Captures both audio references and pedagogical metadata for that turn.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | Auto-generated |
| `session_id` | `UUID` | Parent session |
| `user_audio_ref` | `Optional[str]` | Filename of saved user audio (debug only) |
| `assistant_audio_bytes` | `bytes` | Raw WAV/PCM audio from model |
| `transcript_user` | `str` | Model-inferred transcription of user speech |
| `transcript_assistant` | `str` | Text of assistant response |
| `pronunciation_events` | `List[PronunciationEvent]` | Detected issues in this turn (may be empty) |
| `timestamp` | `datetime` | Turn creation time |

**Rules**:
- `assistant_audio_bytes` must be non-empty for a turn to be considered complete
- `pronunciation_events` is an empty list when no errors are detected (never null)

---

### PronunciationEvent

A single detected pronunciation deviation within one turn.

| Field | Type | Notes |
|-------|------|-------|
| `word` | `str` | The word or phrase that was mispronounced |
| `error_type` | `str` | `"vowel"` \| `"consonant"` \| `"stress"` \| `"intonation"` \| `"other"` |
| `user_pronunciation` | `str` | Approximate phonetic description of what the user said (IPA or plain text) |
| `correct_pronunciation` | `str` | Target pronunciation |
| `correction_attempted` | `bool` | Whether a correction drill was initiated in this turn |
| `correction_succeeded` | `Optional[bool]` | `True` if user repeated correctly; `None` if not yet evaluated |

**Rules**:
- `word` must be non-empty
- `error_type` must be one of the allowed enum values
- `correction_succeeded` is `None` until a repeat-after-me drill completes

---

### OmniChannelConfig

Runtime configuration for the omni voice channel, read from environment at startup.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `enabled` | `bool` | `False` | Master switch; when `False`, endpoint returns 503 |
| `api_url` | `str` | `"http://omni:8003"` | Base URL of the omni model service |
| `timeout_seconds` | `int` | `30` | Request timeout per turn |
| `max_audio_seconds` | `int` | `60` | Maximum user audio length accepted |

---

## Value Objects

### OmniVoiceResult

Returned by `OmniVoiceService.process_speech()`. Not persisted; passed between layers.

| Field | Type | Notes |
|-------|------|-------|
| `audio_bytes` | `bytes` | Assistant's spoken response (WAV) |
| `transcript_user` | `str` | What the model understood the user to have said |
| `transcript_assistant` | `str` | Text of the model's spoken response |
| `pronunciation_events` | `List[PronunciationEvent]` | Detected issues (may be empty) |

---

## Omni Service API Contract (internal)

The `ai_services/omni/` service exposes this internal API. It is **not** the public backend API.

### Request: `POST /omni/speech`

```
Content-Type: multipart/form-data

Fields:
  audio       (bytes, required)  — User's speech in WebM/WAV format
  language    (str, optional)    — Target language code, default "en-US"
  context     (str, optional)    — JSON-serialised prior turns for session continuity
```

### Response: `application/json`

```json
{
  "audio_base64": "<base64-encoded WAV>",
  "transcript_user": "The user said this",
  "transcript_assistant": "The assistant responded with this",
  "pronunciation_events": [
    {
      "word": "example",
      "error_type": "vowel",
      "user_pronunciation": "ɪɡˈzæmpəl (short i)",
      "correct_pronunciation": "ɪɡˈzɑːmpəl",
      "correction_attempted": false,
      "correction_succeeded": null
    }
  ]
}
```

### Response: `GET /health`

```json
{ "status": "ok", "model_loaded": true }
```

---

## Relationships

```
OmniVoiceSession ──< OmniAudioTurn ──< PronunciationEvent
                                    └── OmniVoiceResult (transient)
Student ──────────── OmniVoiceSession
```

---

## State Transitions: OmniVoiceSession

```
[created] ──► [active] ──► [ended]
                 │
                 └──► [active] (each new turn appended)
```

## State Transitions: PronunciationEvent.correction_succeeded

```
None (not yet drilled)
  │
  ├──► True  (user repeated correctly on first or second attempt)
  └──► False (user attempted twice but still incorrect → session moves on)
```
