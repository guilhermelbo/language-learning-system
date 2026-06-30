# Quickstart: Real-Time Voice Tutor Validation

## Prerequisites

- Docker Compose stack running: `docker compose up -d`
- llamacpp running on host port 8080 with Gemma 4 loaded
- Browser with microphone access (Chrome or Firefox recommended)
- `curl` and `jq` for backend validation

---

## Backend Validation

### 1. Verify streaming endpoint exists

```bash
curl -s -X POST http://localhost:8000/conversation/omni/speech/stream \
  -F "file=@/tmp/test.wav" \
  -F "language=en-US" \
  -H "Accept: text/event-stream"
```

**Expected**: SSE stream with events in order: `transcript`, `text_delta` (multiple), `sentence_audio` (one or more), `pronunciation_events`, `done`. HTTP 200 before any events arrive.

### 2. Verify sentence-by-sentence audio

```bash
curl -s -X POST http://localhost:8000/conversation/omni/speech/stream \
  -F "file=@/tmp/test.wav" \
  -F "language=en-US" \
  -H "Accept: text/event-stream" | grep "^event:"
```

**Expected output** (order):
```
event: transcript
event: text_delta
event: text_delta
... (multiple)
event: sentence_audio
event: text_delta
... (more tokens for next sentence)
event: sentence_audio
event: pronunciation_events
event: done
```

### 3. Verify conversation continuity (multi-turn)

```bash
# Turn 1
CONV_ID=$(curl -s -X POST http://localhost:8000/conversation/omni/speech/stream \
  -F "file=@/tmp/test.wav" \
  -H "Accept: text/event-stream" | grep "^data:" | tail -1 | jq -r '.conversation_id')

echo "Got conversation ID: $CONV_ID"

# Turn 2 — send with same conversation_id
curl -s -X POST http://localhost:8000/conversation/omni/speech/stream \
  -F "file=@/tmp/test.wav" \
  -F "conversation_id=$CONV_ID" \
  -H "Accept: text/event-stream"
```

**Expected**: Second turn references prior context (greeting not repeated, tutor builds on Turn 1).

### 4. Verify backward compatibility

```bash
# Old non-streaming endpoint must still work
curl -s -X POST http://localhost:8000/conversation/omni/speech \
  -F "file=@/tmp/test.wav" \
  -F "language=en-US"
```

**Expected**: JSON response `{"conversation_id": "omni-...", "user_text": "...", "ai_text": "...", "audio_base64": "..."}` — unchanged behavior.

---

## Frontend Validation

### 5. Voice Tutor mode activates mic automatically

1. Open `http://localhost:3000`
2. Ensure the mode selector shows — switch to "Voice Tutor"
3. **Expected**: Microphone activates immediately, mic icon animates, "Listening…" indicator visible
4. **Expected**: No button press required

### 6. Silence detection triggers send

1. In Voice Tutor mode, speak a sentence ("Hello, how are you?")
2. Stop speaking
3. **Expected**: After 2 seconds of silence, a send indicator appears ("Thinking…" or spinner)
4. **Expected**: Tutor response text starts appearing progressively within ~3 seconds of silence

### 7. Audio plays sentence by sentence

1. Ask the tutor a question that produces a multi-sentence response
2. **Expected**: First sentence audio starts playing before the full response text is complete on screen
3. **Expected**: Text continues appearing while first sentence plays
4. **Expected**: Sentences play in order, no overlap

### 8. Microphone re-enables automatically

1. After tutor finishes speaking (audio queue drains)
2. **Expected**: Mic icon reactivates, "Listening…" indicator returns
3. **Expected**: No button press needed — user can speak again immediately

### 9. Configurable silence threshold

1. Find the silence threshold control (should be visible in Voice Tutor mode)
2. Change from 2s to 4s
3. Speak a sentence, pause
4. **Expected**: System waits the full 4 seconds before sending

### 10. Exit Voice Tutor mode stops everything

1. While in Voice Tutor mode with tutor speaking, switch to "Padrão" mode
2. **Expected**: Audio stops immediately, mic indicator disappears, no further SSE connections made

---

## Error Scenarios

### 11. Backend unavailable

1. Stop the backend container: `docker compose stop backend`
2. In Voice Tutor mode, speak and wait for silence
3. **Expected**: Error message appears within a few seconds, system does NOT crash
4. **Expected**: User can still switch to standard mode

### 12. Microphone permission denied

1. Revoke mic permission in browser settings
2. Enter Voice Tutor mode
3. **Expected**: Clear error message: "Microphone access required. Please enable it in your browser settings."
4. **Expected**: Mode switches back to standard automatically

---

## Reference

- SSE event schema: [contracts/streaming-endpoint-contract.md](contracts/streaming-endpoint-contract.md)
- VAD state machine: [contracts/frontend-vad-contract.md](contracts/frontend-vad-contract.md)
- Technical decisions: [research.md](research.md)
