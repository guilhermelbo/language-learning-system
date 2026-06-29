# API Contract: Omni Voice Channel

**Feature**: 007-omni-voice-channel  
**Date**: 2026-06-27  
**Base URL**: `http://localhost:8000` (backend service)

This document defines the public-facing backend API endpoints exposed by the omni voice channel. The internal `ai_services/omni/` service API is documented in `data-model.md`.

---

## Endpoints

### POST `/conversation/omni/speech`

Start or continue an omni voice session. Accepts raw audio from the user and returns the assistant's spoken response alongside pronunciation metadata.

**Request**

```
Content-Type: multipart/form-data

Fields:
  file              (UploadFile, required) — User's audio recording (WebM/WAV, max 60s)
  conversation_id   (str, optional)        — Existing omni session ID; omit to start new
  language          (str, optional)        — Target language code (default: "en-US")
```

**Response `200 OK`**

```json
{
  "conversation_id":        "omni-a1b2c3d4-...",
  "user_text":              "Hello, how are you?",
  "ai_text":                "I'm doing well! By the way, you said 'hello' with a short vowel — let's work on that.",
  "audio_base64":           "<base64-encoded WAV>",
  "pronunciation_events": [
    {
      "word":                   "hello",
      "error_type":             "vowel",
      "user_pronunciation":     "hɛlo",
      "correct_pronunciation":  "həˈloʊ",
      "correction_attempted":   false,
      "correction_succeeded":   null
    }
  ]
}
```

**Response `503 Service Unavailable`**

```json
{
  "detail": "omni_unavailable"
}
```

Returned when `OMNI_ENABLED=false` or the omni model service is unreachable.

**Response `400 Bad Request`**

```json
{
  "detail": "audio_too_long"
}
```

Returned when submitted audio exceeds the configured maximum duration (default 60 seconds).

**Response `404 Not Found`**

```json
{
  "detail": "Conversation not found"
}
```

Returned when a `conversation_id` is provided but the session does not exist.

---

### GET `/conversation/omni/status`

Check whether the omni channel is available and the model is loaded.

**Response `200 OK`**

```json
{
  "omni_enabled":   true,
  "model_loaded":   true,
  "omni_api_url":   "http://omni:8003"
}
```

**Response `200 OK` (disabled)**

```json
{
  "omni_enabled":   false,
  "model_loaded":   false,
  "omni_api_url":   null
}
```

The frontend calls this on page load to determine whether to show the omni mode selector.

---

## Response Model: `OmniTextResponse`

| Field | Type | Always present | Notes |
|-------|------|----------------|-------|
| `conversation_id` | `string` | Yes | Prefixed with `"omni-"` |
| `user_text` | `string` | Yes | Model's transcription of user speech |
| `ai_text` | `string` | Yes | Text of assistant response |
| `audio_base64` | `string \| null` | Yes | Base64-encoded WAV; null if synthesis failed |
| `pronunciation_events` | `array` | Yes | Empty array if no errors detected |

### `PronunciationEvent` object

| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| `word` | `string` | No | The mispronounced word or phrase |
| `error_type` | `string` | No | `"vowel"`, `"consonant"`, `"stress"`, `"intonation"`, `"other"` |
| `user_pronunciation` | `string` | No | Approximate phonetic form of what user said |
| `correct_pronunciation` | `string` | No | Target pronunciation |
| `correction_attempted` | `boolean` | No | Whether a drill was initiated |
| `correction_succeeded` | `boolean \| null` | Yes | `null` until drill completes |

---

## Backward Compatibility

- All existing endpoints (`/conversation/speech`, `/conversation/text`, `/health`) are **unchanged**.
- The omni endpoints are additive — they share no state with standard conversation sessions.
- Omni `conversation_id` values are always prefixed with `"omni-"` and are **not** interchangeable with standard conversation IDs.

---

## Frontend Integration Notes

1. On mount, call `GET /conversation/omni/status`. If `omni_enabled: false`, hide the omni mode selector.
2. For each omni turn, `POST /conversation/omni/speech` with the audio blob and carry the returned `conversation_id` forward.
3. Render `pronunciation_events` as visual annotations alongside the audio player (e.g., highlighted word chips).
4. On `503`, display a non-blocking toast: *"Voice Tutor mode is currently unavailable. Standard mode is still active."*
