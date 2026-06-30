# Research: llamacpp Voice Provider

**Feature**: 009-llamacpp-voice-provider
**Date**: 2026-06-29
**Status**: Complete — updated with native audio findings

---

## 1. Native Audio Input via llamacpp `/v1/chat/completions` ✅ WORKING

### Capability Confirmation

```bash
curl -s http://localhost:8080/props | python3 -c "import sys,json; p=json.load(sys.stdin); print('audio:', p['total_slots'][0]['audio'])"
# audio: True
```

Gemma 4 12B is loaded with `mmproj-gemma-4-12B-it-bf16.gguf` (354MB), enabling multimodal audio + vision.

### Request Format

```json
{
  "model": "gemma-4-12B-it-Q5_K_M.gguf",
  "messages": [{
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
        "text": "Please respond as the language tutor."
      }
    ]
  }],
  "max_tokens": 1024
}
```

**Important**: `max_tokens` must be >= 1024. Thinking mode is active — the model generates `reasoning_content` (internal reasoning) first, then `content` (the actual response). Low `max_tokens` truncates before content is generated.

### Response Format

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "reasoning_content": "...(internal reasoning)...",
      "content": "...(actual tutor response)..."
    }
  }]
}
```

**Extraction**: `payload["choices"][0]["message"].get("content") or ""`

`reasoning_content` may or may not be present; use `.get()` and guard against `None`.

### Validated Performance

| Audio | Input tokens | Latency | Result |
|-------|-------------|---------|--------|
| Tom 440Hz (3s) | 117 | 2.8s | "high-pitched electronic beep" ✅ |
| Fala humana real | ~120 | 2.4–5.7s | Resposta coerente ✅ |
| Sons sintéticos | 88–103 | 4–5s | Alucinações ⚠️ (esperado — treinado em fala natural) |

**Conclusion**: Works correctly with real human speech. Ideal for language tutoring. Synthetic test tones cause hallucinations (expected).

### Audio Format

- Ideal: WAV 16kHz mono
- Max duration: 30 seconds
- Data: raw bytes → base64 encoded → sent in `input_audio.data` field
- Format field: `"wav"` (even for browser-recorded audio; llamacpp accepts various formats)

---

## 2. TTS — Piper (existing service at port 8002)

**Request**: `POST /` with `Content-Type: application/json`
```json
{"text": "Hello, how are you?", "lang": "en"}
```

**Response**: WAV bytes (PCM 16-bit, binary response body)

**Language mapping** from voice request `language` param:
- `"en-US"` or `"en"` → `"en"`
- `"pt-BR"` or `"pt"` → `"pt"`
- Default: `"en"`

---

## 3. STT — NOT USED in this provider

llamacpp `/v1/audio/transcriptions` exists but is NOT needed because the LLM processes audio natively. Transcript of user speech is requested from the model via the system prompt (USER_TRANSCRIPT block).

llamacpp `/v1/audio/speech` returns 404 (no TTS model loaded) — use Piper instead.

---

## 4. Existing Code Patterns to Reuse

### Pattern: `GenericVoiceHttpService` (`infrastructure/omni_service.py`)
- Uses `httpx.AsyncClient(timeout=self._timeout)` for all requests
- Raises `VoiceServiceUnavailableError` on `ConnectError`, `TimeoutException`, and non-2xx

### Pattern: `voice_factory.py`
```python
if provider == "generic":
    return GenericVoiceHttpService(api_url=..., timeout=...)
```
Add:
```python
if provider == "openai_compatible":
    return OpenAICompatibleVoiceService(
        base_url=settings.voice_api_url,
        model=settings.voice_model_name,
        api_key=settings.llm_api_key,
        tts_api_url=settings.tts_api_url,
        timeout=settings.voice_timeout_seconds,
    )
```

### Pattern: `TUTOR_SYSTEM_PROMPT` and `_extract_pronunciation_events`
Source: `ai_services/omni/app/main.py`

Duplicated into `llm_voice_service.py` — backend and ai_services/ are separate deployment units.

System prompt is updated to also request a `<!-- USER_TRANSCRIPT: ... -->` block so the transcript of what the student said is parseable from the response.

`_extract_pronunciation_events(text)`:
```python
pattern = r"<!--\s*PRONUNCIATION_EVENTS:\s*(\[.*?\])\s*-->"
match = re.search(pattern, text, re.DOTALL)
if not match:
    return text.strip(), []
clean_text = text[: match.start()].strip()
events = json.loads(match.group(1))
return clean_text, events if isinstance(events, list) else []
```

`_extract_user_transcript(text)`:
```python
pattern = r"<!--\s*USER_TRANSCRIPT:\s*(.*?)\s*-->"
match = re.search(pattern, text, re.DOTALL)
return match.group(1).strip() if match else ""
```

---

## 5. New Config Fields

`backend/src/config.py` — add to `Settings`:
```python
voice_model_name: str = Field(default="", alias="VOICE_MODEL_NAME")
```

Empty default means: use whatever model is loaded on the server. The `tts_api_url` field already exists.

---

## 6. docker-compose.yml Changes

```yaml
- VOICE_ENABLED=true
- VOICE_PROVIDER=openai_compatible
- VOICE_API_URL=http://host.docker.internal:8080/v1
- VOICE_MODEL_NAME=gemma-4-12B-it-Q5_K_M.gguf
# TTS_API_URL already set to http://tts:8002
```
