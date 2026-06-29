# Research: Omni Voice Channel — Native Speech-to-Speech Tutoring

**Feature**: 007-omni-voice-channel  
**Date**: 2026-06-27  
**Status**: Complete — all unknowns resolved

---

## 1. How Qwen2.5-Omni Processes Audio

**Decision**: Treat Qwen2.5-Omni-7B as a black-box service, accessed via a dedicated HTTP API that the backend calls like it calls STT, TTS, or LLM today.

**Rationale**: Qwen2.5-Omni-7B uses a "Thinker-Talker" architecture: the Thinker component processes multimodal input (including raw audio PCM or WAV bytes encoded in the request), understands speech semantics and phonetics, then the Talker generates audio tokens that are decoded to waveform output. Because the model operates on raw audio—not a transcription—it preserves pronunciation nuances that are stripped away by a conventional STT step. Serving this via a thin Python FastAPI wrapper inside Docker matches exactly the pattern used by the STT service (Faster-Whisper) and TTS service (Piper).

**Alternatives considered**:
- vLLM with audio support: viable for high throughput, but heavy operational overhead and audio-output support is still experimental as of mid-2025. Not chosen for v1.
- llamacpp with audio: no mature support for Qwen2.5-Omni audio output. Rejected.
- Direct integration in the backend service: violates LLM Independence principle and conflates ML runtime with business logic. Rejected.

---

## 2. Service Interface Pattern

**Decision**: Add a new `OmniVoiceService` abstract base class to `domain/interfaces.py`; implement it as `QwenOmniHttpService` in `infrastructure/`.

**Rationale**: The existing pattern is ABC in domain, HTTP-based concrete class in infrastructure, injected into use cases. This is exactly what the constitution mandates (Clean Architecture + DDD, Principle III). The new interface takes `bytes` (audio) and returns `OmniVoiceResult` (audio bytes + pronunciation events). This keeps the domain layer technology-agnostic.

**Alternatives considered**:
- Reusing `STTService` + `LLMService` + `TTSService` in a new use case: defeats the purpose; loses the pronunciation signal by going through text. Rejected.
- Adding audio-in/audio-out method to LLMService: wrong abstraction; LLMService is text-to-text. Rejected.

---

## 3. Docker Service Layout

**Decision**: New service `ai_services/omni/` with a Python FastAPI server that loads and wraps Qwen2.5-Omni-7B. Runs as `lingo-omni` container on port `8003`. Added to `docker-compose.yml` as an optional service (no `depends_on` from backend — backend degrades gracefully if omni is absent).

**Rationale**: Mirrors `ai_services/stt/` and `ai_services/tts/` exactly. Model weights must be mounted or pre-downloaded by the user (consistent with LLM Independence principle). The service exposes two endpoints: `POST /omni/speech` (audio in, audio + metadata out) and `GET /health`.

**Alternatives considered**:
- Running the model from within the backend container: increases backend image size from ~200MB to 15GB+; breaks service isolation. Rejected.
- External vLLM server pointed to via env var: feasible future path but no standardized audio I/O contract yet. Deferred.

---

## 4. Pronunciation Feedback Mechanism

**Decision**: The omni service returns a JSON envelope: `{ "audio_base64": "...", "pronunciation_events": [...], "transcript": "..." }`. The backend passes `pronunciation_events` to the frontend alongside the audio.

**Rationale**: The Qwen2.5-Omni model naturally generates a text explanation of pronunciation errors when prompted correctly (as part of its response). The omni service prompts the model to always include a structured list of detected errors (word, error type, correction) in a metadata field separate from the spoken response. This separates "what was said" (audio) from "what the tutor noticed" (pronunciation events), enabling the frontend to show visual feedback alongside audio playback.

**Alternatives considered**:
- Encode pronunciation metadata only in the spoken audio response: no structured data for the frontend to parse. Rejected.
- Separate second LLM call for pronunciation analysis: reintroduces the text-only limitation. Rejected.

---

## 5. Frontend Mode Toggle

**Decision**: Add a mode selector (Standard / Voice Tutor) to the existing `ChatInterface.tsx`. Standard mode uses the existing `/conversation/speech` + `/conversation/text` flow. Voice Tutor mode uses the new `/conversation/omni/speech` endpoint. No new page; same component with conditional rendering.

**Rationale**: Minimal surface area change. Keeps the existing UX intact. The omni session uses a separate `conversation_id` namespace (prefixed `omni-`) so history doesn't bleed between modes.

**Alternatives considered**:
- Separate page/route for omni mode: clean separation but doubles navigation complexity. Deferred to future enhancement.
- Same endpoint that auto-detects mode: opaque behavior; breaks graceful degradation. Rejected.

---

## 6. Graceful Degradation

**Decision**: If the omni service is unreachable or returns an error, the backend returns HTTP 503 with `{"detail": "omni_unavailable"}`. The frontend detects this code and shows a non-blocking toast message; standard mode remains active.

**Rationale**: The constitution requires zero regression (Principle I). The backend must not crash or degrade the standard pipeline if the omni container is down. The frontend must not block the user from standard mode. A 503 is the correct HTTP semantics for a dependency being temporarily unavailable.

**Alternatives considered**:
- Automatic fallback to standard pipeline on 503: hides the mode switch from the user and may confuse pronunciation feedback expectations. Rejected.

---

## 7. Configuration

**Decision**: New env vars `OMNI_API_URL` (default: `http://omni:8003`) and `OMNI_ENABLED` (default: `false`). Backend reads these in `config.py`; the omni use case is only instantiated when `OMNI_ENABLED=true`.

**Rationale**: Matches the existing env-var pattern for `STT_API_URL`, `TTS_API_URL`, and `LLM_BASE_URL`. Keeping it disabled by default ensures zero impact on existing deployments that haven't installed the model.

---

## 8. System Prompt for Pronunciation Tutoring

**Decision**: The omni service sends a structured system prompt instructing the model to: (a) respond naturally in the target language, (b) identify any mispronunciations in the user's audio, (c) include corrections in its spoken response, and (d) emit a JSON metadata block in its text response listing pronunciation events.

**Rationale**: The model's text output channel carries structured metadata while the audio channel carries the tutoring response. This dual-output approach leverages Qwen2.5-Omni's native ability to generate both modalities simultaneously.
