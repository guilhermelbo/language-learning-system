# Quickstart: llamacpp Voice Provider Validation

**Feature**: 009-llamacpp-voice-provider
**Date**: 2026-06-29

---

## Prerequisites

- llamacpp running at `http://host.docker.internal:8080` with a model loaded (e.g., Gemma-4 12B)
- Piper TTS running at `http://tts:8002` (or `http://localhost:8002` from host)
- Backend rebuilt with feature 009 changes

## Environment Variables

```env
VOICE_ENABLED=true
VOICE_PROVIDER=openai_compatible
VOICE_API_URL=http://host.docker.internal:8080/v1
VOICE_MODEL_NAME=gemma-4-12B-it-Q5_K_M.gguf
# TTS_API_URL already set to http://tts:8002
```

---

## Scenario 1 — Voice Status (SC-002, US2/AC3)

```bash
curl http://localhost:8000/conversation/omni/status
```

**Expected**:
```json
{"omni_enabled": true, "model_loaded": true}
```

---

## Scenario 2 — Single Voice Turn (SC-001, US1/AC1)

Record or download a short English audio clip (WAV or WebM):

```bash
curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@/tmp/hello.wav" \
  -F "language=en-US"
```

**Expected**:
```json
{
  "conversation_id": "omni-<uuid>",
  "user_text": "<transcribed text>",
  "ai_text": "<tutor response>",
  "audio_base64": "<non-empty base64 string>",
  "pronunciation_events": []
}
```

Validate:
- `user_text` is a non-empty transcript of the audio
- `ai_text` is a coherent tutor response
- `audio_base64` decodes to valid WAV bytes
- `pronunciation_events` is a list (may be empty for correct speech)

---

## Scenario 3 — Pronunciation Error Detection (SC-003, US1/AC2)

Record audio with a deliberate mispronunciation (e.g., say "wurld" instead of "world"):

```bash
curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@/tmp/mispronounced.wav" \
  -F "language=en-US"
```

**Expected**:
```json
{
  "pronunciation_events": [
    {"word": "world", "error_type": "vowel", "user_said": "...", "correct": "..."}
  ]
}
```

Validate: `pronunciation_events` contains at least one entry identifying the mispronounced word.

---

## Scenario 4 — Session Continuity (SC-005, US3)

Perform three consecutive turns with the same `conversation_id`:

```bash
# Turn 1 — get conversation_id
RESP=$(curl -s -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@/tmp/turn1.wav" -F "language=en-US")
CONV_ID=$(echo $RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['conversation_id'])")

# Turn 2
curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@/tmp/turn2.wav" \
  -F "language=en-US" \
  -F "conversation_id=$CONV_ID"

# Turn 3 — ask the tutor to repeat what the student said in the first turn
curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@/tmp/turn3_reference_first.wav" \
  -F "language=en-US" \
  -F "conversation_id=$CONV_ID"
```

**Expected**: Turn 3 response references context from Turn 1 or 2 (session continuity preserved).

---

## Scenario 5 — Unreachable Server (SC-006, US2/AC2)

```bash
# Temporarily set wrong URL
VOICE_API_URL=http://host.docker.internal:9999/v1 \
  curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@/tmp/hello.wav" -F "language=en-US"
```

**Expected**: HTTP 503 with error body. Text pipeline unaffected (test a text conversation concurrently).

---

## Scenario 6 — Regression: Text Pipeline Unaffected (SC-004)

```bash
curl -X POST http://localhost:8000/conversation/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "language": "en"}'
```

**Expected**: Normal text response — no degradation from feature 009 changes.

---

## Unit Test Validation

```bash
cd backend
pytest tests/test_llm_voice_service.py -v
```

**Expected**: All tests pass. Tests cover:
- STT response parsing (extract `payload["text"]`)
- LLM response parsing (extract from `choices[0].message.content`)
- `_extract_pronunciation_events()` with and without PRONUNCIATION_EVENTS block
- TTS success (WAV bytes returned)
- TTS failure (returns empty bytes, no exception propagated)
- `VoiceServiceUnavailableError` raised on connect error and non-2xx

## All Backend Tests (SC-004)

```bash
cd backend
pytest
```

**Expected**: All previously passing tests still pass.
