# Contract: Voice Pipeline — openai_compatible Provider

**Feature**: 009-llamacpp-voice-provider
**Date**: 2026-06-29

This contract describes the two HTTP calls made internally by `OpenAICompatibleVoiceService.process_speech()`. No STT call is needed — audio is processed natively by the LLM. These are not public API changes — the public endpoint (`POST /conversation/omni/speech`) is unchanged.

---

## 1. LLM — Chat Completions with Native Audio Input

**Request**

```
POST {VOICE_API_URL}/chat/completions
Content-Type: application/json
Authorization: Bearer {VOICE_API_KEY}   (omitted if api_key is None)
```

```json
{
  "model": "<VOICE_MODEL_NAME>",
  "max_tokens": 1024,
  "messages": [
    {
      "role": "system",
      "content": "<TUTOR_SYSTEM_PROMPT>"
    },
    {
      "role": "user",
      "content": "<prior turn user text>"
    },
    {
      "role": "assistant",
      "content": "<prior turn assistant text>"
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_audio",
          "input_audio": {
            "data": "<base64_wav>",
            "format": "wav"
          }
        },
        {
          "type": "text",
          "text": "Please respond as the language tutor to what you hear."
        }
      ]
    }
  ]
}
```

Notes:
- Prior turns (context) are sent as plain text `{"role": ..., "content": "..."}` messages
- Only the current turn has the multimodal `input_audio` content block
- `max_tokens=1024` is required — thinking mode generates internal reasoning before the actual response

**Response** (HTTP 200)

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "reasoning_content": "...(internal reasoning, may be null)...",
      "content": "<tutor response text + embedded blocks>"
    }
  }]
}
```

**Extraction**: `payload["choices"][0]["message"].get("content") or ""`

**Embedded blocks in content** (parsed after extraction):

```
<tutor response text>
<!-- USER_TRANSCRIPT: what I heard the student say -->
<!-- PRONUNCIATION_EVENTS: [{"word": "world", "error_type": "vowel", "user_pronunciation": "wurld", "correct_pronunciation": "wɜːrld"}] -->
```

Parsing:
- `USER_TRANSCRIPT`: `r"<!--\s*USER_TRANSCRIPT:\s*(.*?)\s*-->"` with `re.DOTALL`
- `PRONUNCIATION_EVENTS`: `r"<!--\s*PRONUNCIATION_EVENTS:\s*(\[.*?\])\s*-->"` with `re.DOTALL`
- `clean_text`: text before the first `<!--` block

**Error handling**: `ConnectError`, `TimeoutException`, or non-2xx → raise `VoiceServiceUnavailableError`

---

## 2. TTS — Text-to-Speech (Piper)

**Request**

```
POST {TTS_API_URL}/
Content-Type: application/json
```

```json
{"text": "<clean_text>", "lang": "<mapped_lang>"}
```

Language mapping:

| Input `language` | Piper `lang` |
|-----------------|--------------|
| `"en-US"`, `"en"` | `"en"` |
| `"pt-BR"`, `"pt"` | `"pt"` |
| anything else | `"en"` |

**Response** (HTTP 200): WAV bytes (binary body, PCM 16-bit)

**Error handling**: `ConnectError`, `TimeoutException`, or non-2xx → degraded mode: `audio_bytes=b""`, no exception propagated.

---

## 3. Public Endpoint (Unchanged)

`POST /conversation/omni/speech` — contract unchanged from feature 008.

**Response schema** (`OmniTextResponse`):

```json
{
  "conversation_id": "omni-<uuid>",
  "user_text": "<what the model heard — from USER_TRANSCRIPT block>",
  "ai_text": "<clean tutor response>",
  "audio_base64": "<base64 WAV>",
  "pronunciation_events": [
    {"word": "...", "error_type": "...", "user_said": "...", "correct": "..."}
  ]
}
```

`pronunciation_events` is always an array (empty when no errors detected).
`user_text` is always a string (empty string if USER_TRANSCRIPT block not present in model response).
