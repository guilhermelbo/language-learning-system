# Feature Specification: Real-Time Voice Tutor Conversation

**Feature Branch**: `010-realtime-voice-tutor`

**Created**: 2026-06-30

**Status**: Draft

**Input**: User description: "quero que o modo voice tutor se torne uma conversa em tempo real entre o usuário e o tutor com streaming e que seja fluido tentando se aproximar de conversa natural. no frontend eu quero que quando o usuário entre no modo tutor então uma conversa ao vivo se inicie, o usuário vai falar, depois de um tempo configurável (pode iniciar em 2 segundos) que o usuário ficar em silencio o que foi dito será enviado para o backend e o backend deve responder em streaming, e o usuário fala novamente, e assim por diante. sem que o usuário precise clicar no botão de gravar o audio e clicar para parar. o foco é que seja realmente uma conversa em tempo real."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Hands-Free Voice Conversation (Priority: P1)

When a student switches to Voice Tutor mode, the microphone activates automatically and the conversation begins without any button presses. The student speaks naturally; after a brief silence (default: 2 seconds), what was said is sent to the tutor. The tutor responds and the student can speak again immediately. The cycle continues indefinitely until the student leaves the mode.

**Why this priority**: This is the core feature — eliminating the push-to-talk friction is what transforms the interaction from a tool into a natural conversation. Without this, no other story delivers value.

**Independent Test**: Open the app, switch to Voice Tutor mode, speak a sentence, stay silent for 2 seconds, and receive a spoken response — all without touching any button.

**Acceptance Scenarios**:

1. **Given** the user is in Voice Tutor mode, **When** the mode is activated, **Then** the microphone starts listening automatically with a visual indicator showing "listening" state.
2. **Given** the microphone is listening, **When** the user speaks and then goes silent for 2 seconds, **Then** the recorded audio is sent automatically and the tutor begins responding.
3. **Given** the tutor is responding, **When** the response finishes, **Then** the microphone reactivates automatically and the user can speak again without pressing anything.
4. **Given** the user has not spoken for more than 30 seconds, **When** that silence threshold is reached, **Then** the system shows a "Tap to continue" prompt rather than continually sending empty audio.

---

### User Story 2 — Streaming Tutor Response (Priority: P2)

The tutor's text response appears progressively on screen as it is generated, rather than appearing all at once after a delay. The audio response begins playing as soon as the first complete sentence is ready, while subsequent sentences are still being generated.

**Why this priority**: Streaming reduces perceived wait time and makes the interaction feel alive. A blank screen while waiting for the full response breaks conversational flow.

**Independent Test**: Send a voice message and observe the response text appearing word-by-word and the first sentence playing as audio before the full response is complete.

**Acceptance Scenarios**:

1. **Given** audio is sent to the tutor, **When** the tutor generates a response, **Then** response text appears progressively on screen within 1 second of the first token being generated.
2. **Given** the tutor's response contains multiple sentences, **When** the first sentence is complete, **Then** audio playback of that sentence begins before the remaining text arrives.
3. **Given** the tutor is streaming a response, **When** audio playback is in progress, **Then** the microphone remains muted so the user's ambient sound does not trigger a new turn.

---

### User Story 3 — Configurable Silence Threshold (Priority: P3)

The student can adjust how long the system waits after their voice goes silent before sending the recording. The default is 2 seconds; options allow shorter (1 second, for fast-paced practice) or longer (3–5 seconds, for students who need more thinking time).

**Why this priority**: Silence threshold is highly personal — fast speakers need a short gap, slower learners need more time to formulate sentences. One size does not fit all.

**Independent Test**: Change the silence threshold setting, speak a sentence, and confirm the system waits exactly the configured duration before sending.

**Acceptance Scenarios**:

1. **Given** the silence threshold is set to 1 second, **When** the user finishes speaking and pauses for 1 second, **Then** the recording is sent immediately at the 1-second mark.
2. **Given** the silence threshold is set to 4 seconds, **When** the user pauses mid-sentence to think, **Then** the system continues recording and does not send until 4 seconds of silence have elapsed.
3. **Given** the user changes the threshold, **When** they return to Voice Tutor mode, **Then** the new threshold is applied.

---

### Edge Cases

- What happens when the user speaks while the tutor's audio is still playing? — The system should ignore microphone input until the tutor finishes speaking, then re-enable listening automatically.
- What happens if no speech is detected at all (background noise triggers silence detection)? — A minimum audio duration threshold (e.g., 0.5 seconds of detected speech) prevents empty or noise-only clips from being sent.
- What happens if the network is slow and the tutor response takes longer than expected? — A "Tutor is thinking…" indicator appears; the microphone stays muted until the response completes.
- What happens if the user switches away from Voice Tutor mode mid-conversation? — The microphone stops immediately, audio playback stops, and no further requests are sent.
- What happens if microphone permission is denied? — A clear error message explains that microphone access is required and guides the user to enable it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST automatically activate the microphone when the user enters Voice Tutor mode, without requiring any button press.
- **FR-002**: The system MUST detect when the user stops speaking and automatically send the recording after a configurable silence period (default: 2 seconds).
- **FR-003**: The system MUST display a real-time visual indicator distinguishing between: listening, silence detected (countdown), processing, tutor speaking.
- **FR-004**: The system MUST stream the tutor's text response to the screen progressively as it is generated.
- **FR-005**: The system MUST begin audio playback of the tutor's response sentence-by-sentence as each sentence is ready, without waiting for the full response.
- **FR-006**: The system MUST mute the microphone while the tutor's audio is playing to prevent feedback loops.
- **FR-007**: The system MUST automatically re-enable listening after the tutor's audio finishes, without user interaction.
- **FR-008**: The system MUST allow the user to configure the silence detection threshold between 1 and 5 seconds.
- **FR-009**: The system MUST require a minimum of 0.5 seconds of detected voice activity before treating audio as a valid turn, preventing silence-only or noise-only clips from being sent.
- **FR-010**: The system MUST stop all audio capture and playback immediately when the user exits Voice Tutor mode.
- **FR-011**: The system MUST show a "Tap to continue" prompt after 30 seconds of total inactivity (no speech from user), pausing auto-listening to avoid wasting resources.

### Key Entities

- **VoiceTurn**: A single exchange unit — the user's speech segment, its transcript, the tutor's streamed text response, and the synthesized audio response.
- **ConversationState**: The current phase of the interaction loop — idle, listening, silence-countdown, processing, tutor-speaking.
- **SilenceConfig**: User-configurable settings — silence threshold in seconds (1–5), minimum speech duration in seconds.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The first word of the tutor's text response appears on screen within 2 seconds of the user's silence threshold being reached, under normal network conditions.
- **SC-002**: The tutor's first audio sentence begins playing within 4 seconds of the user's silence threshold being reached.
- **SC-003**: The microphone reactivates within 500 milliseconds after the tutor's audio finishes, so the user can speak again immediately.
- **SC-004**: Users complete a 5-turn conversation without pressing any button, in 90% of test sessions.
- **SC-005**: Empty or noise-only audio clips are sent to the backend in fewer than 5% of turns across test sessions.
- **SC-006**: Switching out of Voice Tutor mode stops all audio activity within 200 milliseconds.

## Assumptions

- The user's browser supports the Web Audio API and MediaRecorder API, which are required for continuous audio capture and silence detection.
- Microphone permission has been granted or the system will prompt for it; the feature does not function without microphone access.
- The existing Voice Tutor backend pipeline (audio → tutor response text + pronunciation events + audio) remains the foundation; this feature adds streaming and auto-loop on top of it.
- Sentence-by-sentence audio is synthesized serially on the backend; true parallel synthesis is out of scope for this iteration.
- Mobile browser support is a secondary concern; the primary target is desktop Chrome/Firefox.
- The silence detection threshold setting persists for the browser session only (no server-side user profile storage in v1).
