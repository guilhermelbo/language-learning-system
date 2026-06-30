# Feature Specification: llamacpp Voice Provider

**Feature Branch**: `009-llamacpp-voice-provider`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: "Canal Voice Tutor usando APIs de áudio OpenAI-compatible do llamacpp. O servidor llamacpp (porta 8080) já expõe /v1/audio/transcriptions (STT) e /v1/audio/speech (TTS). Criar um novo provider 'openai_compatible' no canal de voz que orquestra: (1) STT via llamacpp → texto transcrito, (2) Gemma-4 via /v1/chat/completions com system prompt de tutor de pronúncia → texto com PRONUNCIATION_EVENTS, (3) TTS via llamacpp → áudio de resposta. O objetivo é conversa de voz contínua sem depender de servidor de voz externo separado — tudo passa pelo mesmo llamacpp já em uso para texto."

## Problem Statement

The voice tutoring channel currently requires a dedicated native audio model server (speech-to-speech) running separately. The language inference server already in use for text conversations also exposes speech transcription and speech synthesis endpoints in the same OpenAI-compatible format. Running a second, separate server solely for the voice channel is unnecessary overhead when all the required audio capabilities are already available in the existing server. This feature adds a voice provider mode that uses those capabilities — transcription, language model, and speech synthesis — as a single unified pipeline through the already-running server.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Student holds a spoken conversation with the language tutor (Priority: P1)

A student activates the Voice Tutor mode and speaks a sentence in the target language. The system transcribes what was said, the tutor responds naturally with coaching and pronunciation feedback, and the student hears the tutor's voice. The exchange continues as a back-and-forth dialogue — the student speaks again and the cycle repeats — without leaving the tutoring session.

**Why this priority**: This is the core user-facing experience. Everything else supports this flow.

**Independent Test**: Record a short audio clip, send it to the voice tutoring endpoint, and verify that an audio response is returned along with a text transcript and at least a valid (possibly empty) pronunciation feedback list. No separate voice server should be required.

**Acceptance Scenarios**:

1. **Given** the student is in Voice Tutor mode and speaks a sentence, **When** the recording is submitted, **Then** the student hears a spoken response from the tutor within a reasonable time, and the tutor's reply is coherent and pedagogically appropriate.
2. **Given** the student mispronounces a word, **When** the tutor processes the turn, **Then** the response addresses the pronunciation error by name, demonstrates the correct form, and the feedback list identifies the word and error type.
3. **Given** the student has had several conversation turns, **When** they speak again, **Then** the tutor's response is contextually aware of prior turns in the session (not starting fresh each time).
4. **Given** the student speaks correctly with no errors, **When** the tutor processes the turn, **Then** the response is encouraging, the conversation continues naturally, and the pronunciation feedback list is empty.

---

### User Story 2 — Developer enables the voice channel with zero new services (Priority: P2)

A developer wants to enable the Voice Tutor feature on an instance that already runs the language inference server. They set two or three environment variables and restart the backend. No new Docker services are added, no additional models are downloaded, and voice tutoring becomes available immediately.

**Why this priority**: Validates that the feature delivers its core operational promise — unified infrastructure, no extra moving parts.

**Independent Test**: Start the backend with the environment variables pointing to the existing inference server. Call the voice status endpoint and verify it reports the voice channel as enabled and the model as loaded. No other service should be running or required.

**Acceptance Scenarios**:

1. **Given** the inference server is already running and handling text conversations, **When** the developer sets the voice provider to the unified mode and restarts the backend, **Then** voice tutoring is available without starting any additional service.
2. **Given** the voice channel is configured incorrectly (wrong server address), **When** the backend starts and a voice request is made, **Then** a clear error is returned identifying that the voice server is unreachable — the text pipeline is unaffected.
3. **Given** the voice channel is enabled, **When** the developer queries the voice status endpoint, **Then** the response confirms the channel is active and reports the model as ready.

---

### User Story 3 — Conversation feels continuous and uninterrupted (Priority: P3)

After the tutor delivers an audio response, the interface immediately becomes ready for the student's next utterance without requiring a manual reset or page action. The conversation flows like a natural dialogue — listen, then speak, then listen again.

**Why this priority**: The quality of the learning experience depends on this flow feeling natural. Without it, the feature works but feels clunky.

**Independent Test**: Complete three consecutive conversation turns (send audio → receive audio → send audio again using the same session ID) and verify that each turn is aware of the previous ones and that no manual session reset is needed between turns.

**Acceptance Scenarios**:

1. **Given** the tutor has just finished responding, **When** the student is ready to speak again, **Then** the interface is immediately in a listening state without the student having to press a restart button.
2. **Given** multiple consecutive turns in the same session, **When** the student's third or fourth utterance references something from an earlier turn, **Then** the tutor's response reflects that context (session continuity is preserved).

---

### Edge Cases

- What happens if the transcription returns an empty string (silence or inaudible audio)? The tutor should prompt the student to speak again rather than generating a confusing response.
- What happens if the speech synthesis step fails after the text response is already generated? The text transcript should still be returned; the audio field may be empty with a degraded-mode indicator.
- What happens if the student's audio is too long? The system should reject it with a clear message before attempting transcription.
- What happens if the inference server goes down mid-conversation? The endpoint should return a service-unavailable response without crashing the backend; the student's session is preserved for the next attempt.
- What happens if the language parameter is not supported by the transcription engine? The system should fall back to auto-detection rather than failing.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support a voice provider mode that performs transcription, conversation, and speech synthesis through a single external server without requiring a dedicated speech-to-speech model server.
- **FR-002**: The system MUST transcribe the student's audio before passing it to the language model for tutoring response generation.
- **FR-003**: The language model MUST receive a tutoring-specific system prompt that instructs it to act as a pronunciation coach and emit structured pronunciation feedback in a machine-parseable format at the end of each response.
- **FR-004**: The system MUST synthesize the tutor's text response into audio and return it to the student alongside the text transcript and structured pronunciation feedback.
- **FR-005**: The pronunciation feedback MUST follow the established format used by the existing voice tutoring channel — same fields, same structure — so the frontend renders it identically regardless of which voice provider is active.
- **FR-006**: The voice provider MUST be selectable via environment variable, consistent with how the text LLM provider is selected; no code changes should be needed to switch between voice provider modes.
- **FR-007**: The system MUST maintain per-session conversation history across multiple turns so the tutor has context from prior exchanges when generating each new response.
- **FR-008**: The system MUST track pronunciation correction attempts within a session — if the tutor corrected a word in a prior turn, subsequent responses should acknowledge whether the student improved.
- **FR-009**: If the voice server is unreachable or returns an error, the voice endpoint MUST return a clear service-unavailable response; the text conversation pipeline MUST remain unaffected.
- **FR-010**: The student's audio input MUST be validated for maximum duration before being processed; audio exceeding the configured limit MUST be rejected with a descriptive error.

### Key Entities

- **VoiceTurn**: A single exchange in the conversation — the student's audio input, the tutor's audio response, the transcripts of both, and any pronunciation events detected in that turn.
- **VoiceSession**: The persistent context of a tutoring conversation — an ordered sequence of turns, the student identifier, and the accumulated state of pronunciation corrections being tracked across turns.
- **PronunciationEvent**: A detected pronunciation issue in a single turn — the word mispronounced, the type of error (vowel, consonant, stress, intonation, or other), the student's actual pronunciation, and the correct form.
- **VoiceProviderConfig**: The set of environment-driven parameters that define which voice pipeline to use and how to reach the underlying server.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A student can complete a full voice tutoring exchange — speak, receive audio response, speak again — using only the inference server already running for text conversations; no additional service is required.
- **SC-002**: Voice tutoring activates within the normal backend startup time when the correct environment variables are set; no manual steps beyond configuration are needed.
- **SC-003**: The tutor correctly identifies and names pronunciation errors in at least the majority of turns where clear mispronunciations occur, as verified through manual test scenarios with known errors.
- **SC-004**: All previously passing backend tests continue to pass after the new voice provider is added; the text pipeline and existing voice provider mode are unaffected.
- **SC-005**: A conversation of at least five consecutive turns can be completed within a single session, with the tutor demonstrating awareness of prior turns (references to earlier corrections or context).
- **SC-006**: An invalid or unreachable voice server configuration causes a clear error response on voice requests without disrupting the text pipeline.

---

## Assumptions

- The inference server is already running and handling text conversations before the voice channel is activated; the backend does not manage the inference server lifecycle.
- The inference server's transcription capability supports the audio formats the frontend records (WebM or WAV); no audio conversion beyond resampling is needed.
- The inference server's speech synthesis produces audio in a format (WAV or MP3) that the frontend can play directly.
- Pronunciation analysis is based on the transcribed text, not the raw audio signal; the model infers likely errors from what it reads, not from acoustic features. This is an accepted limitation of the unified pipeline approach.
- The voice tutoring system prompt (instructions to the language model) is the same whether using a native audio model or a text-based pipeline; only the input medium differs.
- Session persistence is in-memory (no database); sessions are lost on backend restart. This matches the existing behaviour of all other conversation channels.
- The frontend already supports the voice tutoring turn-by-turn flow and the pronunciation event display; only backend changes are required for this feature.
- The student's language target (e.g., English, Portuguese) is passed as a parameter per request; the system does not infer it from the session.
