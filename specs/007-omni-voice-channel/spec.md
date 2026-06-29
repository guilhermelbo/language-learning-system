# Feature Specification: Omni Voice Channel — Native Speech-to-Speech Tutoring

**Feature Branch**: `007-omni-voice-channel`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "quero que o projeto tenha suporte a utilização do modelo Qwen/Qwen2.5-Omni-7B que entende fala e consegue fazer speech to speech diretamente para conversas fluidas e em tempo real e para que o sistema consiga conversar com o usuário e entender a pronuncia dele, identificar erros e ensinar corretamente. atualmente estamos usando llm + tts + stt mas isso limita tutoria por vóz por não conseguir interpretar a pronuncia do usuário. não precisa substituir o que já temos, apenas criar uma nova via"

## Problem Statement

The current voice tutoring pipeline chains three separate services — speech recognition, language model, and speech synthesis — making it impossible for the system to analyze how the user actually pronounced words. The spoken audio is converted to text before any AI processing occurs, so pronunciation nuances, accent errors, and phonetic mistakes are permanently lost. This limits the tutoring experience: the system can correct grammar and vocabulary but cannot coach pronunciation. A new, parallel voice channel powered by a natively multimodal audio model would close this gap, enabling genuine pronunciation-aware tutoring without removing the existing pipeline.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Real-Time Voice Conversation via Omni Channel (Priority: P1)

A language learner switches to the "Voice Tutor (Advanced)" mode and speaks directly to the system. The system processes the spoken audio natively and responds with synthesized speech, creating a fluid back-and-forth conversation. The interaction feels like talking to a human tutor rather than using a voice-controlled text chatbot.

**Why this priority**: Core value proposition of the feature. Without end-to-end audio conversation, the pronunciation analysis capabilities in P2 and P3 are unreachable.

**Independent Test**: A user can start a conversation, speak a sentence in the target language, and receive a spoken response — without any intermediate text conversion step required by the user. The conversation can continue for multiple turns.

**Acceptance Scenarios**:

1. **Given** the user selects the Omni Voice Channel mode, **When** they speak a sentence in the target language, **Then** the system responds with spoken audio within 5 seconds.
2. **Given** an active omni voice session, **When** the user speaks a follow-up message, **Then** the system maintains conversation context and the response is coherent and pedagogically appropriate.
3. **Given** the user switches back to the standard text/voice mode, **Then** the existing behavior is completely unaffected.

---

### User Story 2 — Pronunciation Error Detection and Feedback (Priority: P2)

During an omni voice conversation, the user mispronounces a word or uses an incorrect intonation pattern. The system detects this from the raw audio and — rather than just responding to the semantic meaning — explicitly addresses the pronunciation mistake, explains what was wrong, and demonstrates the correct pronunciation in its response.

**Why this priority**: This is the primary pedagogical differentiator over the current pipeline. Without this, the omni channel offers no advantage over LLM+TTS+STT for learning outcomes.

**Independent Test**: A user deliberately mispronounces a word with a known, identifiable error (e.g., wrong vowel sound, misplaced stress). The system's spoken response includes explicit mention of the pronunciation issue and a correction — not just a semantic reply.

**Acceptance Scenarios**:

1. **Given** the user speaks a word with a clear pronunciation error, **When** the system processes the audio, **Then** the response explicitly identifies the mispronunciation and names the correct form.
2. **Given** a pronunciation correction in the system's response, **Then** the system itself pronounces the corrected form clearly so the user can hear the target pronunciation.
3. **Given** the user pronounces a word correctly, **Then** the system does NOT falsely report a pronunciation error (acceptable false-positive rate ≤ 10%).

---

### User Story 3 — Pronunciation Coaching with Guided Practice (Priority: P3)

After identifying a pronunciation error, the tutor guides the user through a short correction drill: the system articulates the correct form, prompts the user to repeat it, listens to the repetition, and confirms success or offers further guidance.

**Why this priority**: Closes the feedback loop; transforms detection into learning. Requires P1 and P2 to be functional first.

**Independent Test**: Following a detected error, the system initiates a repeat-after-me drill. The user's repetition is evaluated and the system confirms whether the pronunciation improved.

**Acceptance Scenarios**:

1. **Given** a pronunciation error was identified, **When** the system prompts the user to repeat the correct form, **Then** the user's spoken repetition is evaluated for pronunciation quality.
2. **Given** the user's repetition is correct, **Then** the system confirms success and continues the conversation naturally.
3. **Given** the user's repetition still has errors, **Then** the system provides a second, more targeted correction rather than looping indefinitely (maximum 2 correction attempts per word before moving on).

---

### User Story 4 — Graceful Fallback When Omni Channel Is Unavailable (Priority: P4)

If the omni voice service is not running, misconfigured, or encounters an error, the user is informed clearly and the existing standard voice mode remains fully available. No part of the existing pipeline is degraded.

**Why this priority**: Ensures zero regression on existing functionality. Must be validated before any production use.

**Independent Test**: Stop the omni service and attempt to use the omni channel. The UI shows a clear unavailability message and the standard mode continues working normally.

**Acceptance Scenarios**:

1. **Given** the omni voice service is offline, **When** the user tries to select the omni channel, **Then** the system displays a human-readable message explaining unavailability.
2. **Given** the omni service fails mid-conversation, **Then** the session ends gracefully with an error message; no audio artifacts or hanging states occur.
3. **Given** the omni service is unavailable, **Then** the standard LLM+TTS+STT pipeline continues operating without any impact.

---

### Edge Cases

- What happens when the user speaks in a mix of languages (code-switching) mid-sentence?
- What happens when background noise makes the audio unintelligible?
- How does the system handle very short utterances (single words, hesitations, filler sounds)?
- What happens if the user's microphone produces silence or extremely low volume?
- How does the system behave when the audio response generation exceeds the expected latency threshold?
- What happens when the user speaks in an accent variant that differs significantly from standard pronunciation models?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a distinct, selectable voice channel that uses native audio-to-audio processing, separate from the existing LLM+TTS+STT pipeline.
- **FR-002**: The omni voice channel MUST accept spoken user input as raw audio and produce spoken audio responses without requiring an intermediate text representation visible to the user.
- **FR-003**: The system MUST analyze pronunciation from the audio signal itself, not from a prior transcription step.
- **FR-004**: The system MUST identify mispronounced words or incorrect intonation patterns and include explicit pronunciation feedback in its spoken response when errors are detected.
- **FR-005**: The system MUST demonstrate the correct pronunciation of flagged words within its spoken response.
- **FR-006**: The system MUST support multi-turn conversation context across an omni voice session so pedagogical continuity is maintained.
- **FR-007**: The omni channel MUST operate without modifying, replacing, or degrading the existing standard voice pipeline (LLM+TTS+STT).
- **FR-008**: The system MUST be configurable to enable or disable the omni voice channel independently of other services via environment configuration.
- **FR-009**: The system MUST display a clear, user-friendly message when the omni voice channel is unavailable or encounters an error.
- **FR-010**: The system MUST support the same target languages currently supported by the language learning system.

### Key Entities

- **OmniVoiceSession**: Represents a single audio tutoring session using the native speech-to-speech channel; tracks conversation turns, detected pronunciation events, and session state.
- **PronunciationEvent**: A detected pronunciation deviation within a session turn — includes the word/phrase involved, the nature of the error, and whether a correction drill was initiated.
- **OmniAudioTurn**: One exchange within an OmniVoiceSession; contains the user's audio input reference and the system's audio response reference, along with any pedagogical metadata.
- **OmniChannelConfig**: Configuration for the omni voice service endpoint, enabling/disabling the channel, and any behavioral parameters (e.g., pronunciation sensitivity threshold).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive a spoken response from the omni channel within 5 seconds of finishing their utterance for inputs under 15 seconds in length.
- **SC-002**: The system correctly identifies and explicitly addresses pronunciation errors in at least 80% of test cases where a clear, standard mispronunciation is present.
- **SC-003**: The false-positive rate for pronunciation error detection (reporting an error when pronunciation was correct) is at or below 10%.
- **SC-004**: Users can sustain a multi-turn omni voice conversation of at least 10 exchanges without session degradation or loss of context.
- **SC-005**: 100% of existing standard voice pipeline tests continue passing after the omni channel is introduced (zero regression).
- **SC-006**: Users can switch between standard and omni voice modes without restarting the application.
- **SC-007**: The omni channel mode is discoverable — at least 80% of users in usability testing can locate and activate it without assistance.

## Assumptions

- The Qwen2.5-Omni-7B model (or equivalent natively multimodal audio model) must be manually installed by the user; the system will not bundle or auto-download model weights, consistent with the project's LLM Independence principle.
- The omni voice service is configured via environment variables, following the same pattern as the existing LLM, TTS, and STT services.
- The omni channel is a separate service endpoint — it does not modify or wrap the existing LLM, TTS, or STT services.
- Initial scope covers the web-based frontend only; mobile or native client support is out of scope for this feature.
- Conversation history from standard sessions and omni sessions is kept separate; cross-mode context continuity is out of scope for v1.
- The pronunciation detection capability depends on the underlying model's inherent audio understanding; no additional phoneme-level analysis library is introduced.
- Users are assumed to have a functioning microphone and a browser that supports the required audio capture APIs.
- The target language set for the omni channel matches what is already configured for the system; adding new language support is out of scope.
- Audio data processed by the omni channel stays local (no external telemetry), consistent with the project's privacy principles.
