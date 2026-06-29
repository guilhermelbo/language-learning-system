# Quickstart & Validation Guide: Omni Voice Channel

**Feature**: 007-omni-voice-channel  
**Date**: 2026-06-27

---

## Prerequisites

1. **Model weights**: Download `Qwen/Qwen2.5-Omni-7B` from Hugging Face and place under `ai_services/omni/models/Qwen2.5-Omni-7B/`. The service will not start without weights present.

2. **Docker + Docker Compose**: Existing project dependency. All services run via `docker-compose up --build`.

3. **Enable the omni channel**: Copy `.env.example` (or create `.env`) and set:
   ```
   OMNI_ENABLED=true
   OMNI_API_URL=http://omni:8003
   ```

4. **Existing services**: STT (`lingo-stt`), TTS (`lingo-tts`), and Backend (`lingo-backend`) must be running. Standard mode must pass all existing tests before validating omni.

---

## Starting the Stack

```bash
# Start everything including the new omni service
docker-compose up --build

# Verify all services are healthy
curl http://localhost:8001/health    # STT
curl http://localhost:8002/health    # TTS
curl http://localhost:8003/health    # Omni (new)
curl http://localhost:8000/health    # Backend
```

Expected health response from omni service:
```json
{ "status": "ok", "model_loaded": true }
```

> Note: The omni service may take 2–5 minutes to load the model on first start. The `/health` endpoint returns `"model_loaded": false` while loading and `true` once ready.

---

## Scenario 1: Omni Channel Availability Check (FR-001, FR-008)

**Purpose**: Verify the mode toggle appears when omni is enabled and hides when disabled.

```bash
# With OMNI_ENABLED=true
curl http://localhost:8000/conversation/omni/status
```

**Expected**:
```json
{ "omni_enabled": true, "model_loaded": true, "omni_api_url": "http://omni:8003" }
```

**Browser check**: Open `http://localhost:3000`. Confirm a "Voice Tutor" mode selector is visible alongside the standard mode. Select it.

---

## Scenario 2: Basic Omni Voice Turn (FR-001, FR-002, FR-003)

**Purpose**: Verify audio-in / audio-out without intermediate text transcription required from user.

```bash
# Record or use a sample audio file (WebM or WAV, < 60 seconds)
curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@tests/fixtures/sample_hello.wav" \
  | python3 -c "
import sys, json, base64
r = json.load(sys.stdin)
print('User text (model-inferred):', r['user_text'])
print('AI text:', r['ai_text'])
print('Conversation ID:', r['conversation_id'])
print('Audio received:', len(base64.b64decode(r['audio_base64'])), 'bytes')
print('Pronunciation events:', len(r['pronunciation_events']))
"
```

**Expected**:
- `conversation_id` starts with `"omni-"`
- `user_text` is non-empty (model's transcription of the sample audio)
- `audio_base64` decodes to a valid WAV file > 0 bytes
- Response received within 10 seconds

---

## Scenario 3: Pronunciation Error Detection (FR-003, FR-004, SC-002)

**Purpose**: Verify the system identifies a known mispronunciation.

Use `tests/fixtures/mispronounced_hello.wav` (a recording with a short vowel error on "hello").

```bash
curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@tests/fixtures/mispronounced_hello.wav" \
  | python3 -c "
import sys, json
r = json.load(sys.stdin)
events = r['pronunciation_events']
print(f'Pronunciation events detected: {len(events)}')
for e in events:
    print(f'  Word: {e[\"word\"]}  |  Error: {e[\"error_type\"]}  |  Correct: {e[\"correct_pronunciation\"]}')
"
```

**Expected**:
- `pronunciation_events` contains at least one entry
- The entry for "hello" (or phonetically similar word) shows `error_type` in `["vowel", "stress"]`
- `ai_text` contains explicit mention of the correction

---

## Scenario 4: Multi-Turn Session Continuity (FR-006, SC-004)

**Purpose**: Verify conversation context is maintained across turns.

```bash
# Turn 1 — start session
CONV_ID=$(curl -s -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@tests/fixtures/sample_hello.wav" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['conversation_id'])")

echo "Session ID: $CONV_ID"

# Turn 2 — continue session
curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@tests/fixtures/sample_followup.wav" \
  -F "conversation_id=$CONV_ID" \
  | python3 -c "
import sys, json
r = json.load(sys.stdin)
print('AI response (should reference prior context):', r['ai_text'][:200])
"
```

**Expected**:
- Turn 2 uses the same `conversation_id` without error
- The AI response in turn 2 is contextually coherent with turn 1 (e.g., does not re-introduce itself)

---

## Scenario 5: Zero Regression on Standard Pipeline (SC-005)

**Purpose**: Confirm existing endpoints are completely unaffected.

```bash
# Run the existing test suite
cd /path/to/project
pytest tests/ -v

# Manually verify standard voice endpoint
curl -X POST http://localhost:8000/conversation/speech \
  -F "file=@tests/fixtures/sample_hello.wav"
```

**Expected**:
- All existing pytest tests pass
- Standard `/conversation/speech` and `/conversation/text` return the same response shape as before

---

## Scenario 6: Graceful Degradation (FR-009, SC-005)

**Purpose**: Verify standard mode continues when omni service is down.

```bash
# Stop only the omni service
docker-compose stop omni

# Attempt omni endpoint
curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@tests/fixtures/sample_hello.wav"
```

**Expected**:
```json
{ "detail": "omni_unavailable" }
```
HTTP status: `503 Service Unavailable`

```bash
# Confirm standard mode still works
curl -X POST http://localhost:8000/conversation/speech \
  -F "file=@tests/fixtures/sample_hello.wav"
```

**Expected**: Normal `200 OK` response with `audio_base64` and `ai_text`.

---

## Scenario 7: Audio Too Long (FR-010 boundary)

**Purpose**: Verify oversized audio is rejected cleanly.

```bash
# Use a test audio file longer than 60 seconds
curl -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@tests/fixtures/long_audio_70s.wav"
```

**Expected**:
```json
{ "detail": "audio_too_long" }
```
HTTP status: `400 Bad Request`

---

## Artifact References

- API contract: `contracts/omni-api-contract.md`
- Data model: `data-model.md`
- Acceptance scenarios: `spec.md` (User Stories 1–4)
- Test fixtures needed: `tests/fixtures/sample_hello.wav`, `tests/fixtures/mispronounced_hello.wav`, `tests/fixtures/sample_followup.wav`, `tests/fixtures/long_audio_70s.wav`
