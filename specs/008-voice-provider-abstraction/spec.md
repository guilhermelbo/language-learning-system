# Feature Specification: Voice Provider Abstraction

**Feature Branch**: `008-voice-provider-abstraction`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: "Desacoplar o canal de voz (speech-to-speech) do modelo específico (Qwen2.5-Omni). Atualmente o backend hardcoda QwenOmniHttpService sem factory pattern, e o servidor externo (ai_services/omni/) importa diretamente classes do Qwen. Queremos aplicar o mesmo padrão já usado pelo LLM: env var VOICE_PROVIDER seleciona o provedor, um factory cria a implementação correta, e o servidor externo usa VOICE_MODEL_BACKEND para selecionar o backend de modelo — permitindo trocar para qualquer modelo (ex: Gemma 4) sem alterar código, apenas configuração."

## Problem Statement

The voice tutoring channel (speech-to-speech) was built with the specific Qwen2.5-Omni model hardcoded into the project. This means that switching to any other model — for example Google Gemma 4 — requires editing source code in two places: the backend service (which names and instantiates the Qwen-specific adapter directly) and the external model server (which imports Qwen's Python classes directly). The rest of the system — the LLM text pipeline — already solves this problem correctly: a single environment variable selects the provider, and a factory creates the right implementation at startup. This feature applies that same pattern to the voice channel, so that the model powering voice conversations becomes a configuration choice, not a code change.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Switch Voice Model via Configuration Only (Priority: P1)

A developer running the system decides to replace the speech-to-speech model (e.g., from Qwen2.5-Omni to Gemma 4). They update one or two environment variables, restart the services, and voice tutoring continues working with the new model. No source files are opened or edited.

**Why this priority**: Core value of the feature. Everything else is infrastructure to enable this outcome.

**Independent Test**: Set `VOICE_PROVIDER=generic` and `VOICE_API_URL` pointing to a test server. Change `VOICE_MODEL_BACKEND` on the external server. Restart. Voice tutoring endpoint returns valid responses. No code was modified.

**Acceptance Scenarios**:

1. **Given** the system is configured with Model A for voice, **When** a developer changes `VOICE_API_URL` (and `VOICE_MODEL_BACKEND` on the external server) and restarts, **Then** voice tutoring works with Model B — with zero source code changes.
2. **Given** an unsupported `VOICE_PROVIDER` value is set, **When** the backend starts, **Then** it fails with a clear error message naming the invalid provider, and does not start silently broken.
3. **Given** `VOICE_ENABLED=false`, **When** the backend starts, **Then** voice functionality is disabled regardless of other voice env vars, and the standard text+voice pipeline is unaffected.

---

### User Story 2 — Add a New Voice Provider Without Touching Existing Code (Priority: P2)

A developer wants to connect the voice channel directly to a cloud provider's API (e.g., Google Gemini Live or OpenAI Realtime) instead of running a local model server. They write one new provider implementation, register it in the factory, and the rest of the system — endpoints, use cases, frontend — works without modification.

**Why this priority**: Validates that the abstraction is genuinely extensible, not just renamed. Ensures the factory pattern is correct by testing the add-a-new-provider path.

**Independent Test**: Add a minimal stub provider implementation to the factory. Configure `VOICE_PROVIDER=stub`. Backend starts and the voice endpoint returns a response from the stub. No other files were modified.

**Acceptance Scenarios**:

1. **Given** a new provider implementation is added to the factory, **When** `VOICE_PROVIDER=<new-provider>` is set, **Then** the backend uses the new implementation without any change to endpoints, use cases, or frontend.
2. **Given** the new provider is active, **When** a voice request is processed, **Then** the response shape (audio, transcript, pronunciation events) is identical to any other provider.

---

### User Story 3 — External Voice Server Supports Multiple Model Backends (Priority: P3)

The external voice server (`ai_services/omni/`) can load different underlying models based on a single environment variable (`VOICE_MODEL_BACKEND`), without requiring code changes to the server itself. A developer switching from Qwen2.5-Omni to Gemma 4 only needs to install the new model's weights and set the env var.

**Why this priority**: Decouples the external server from any single model. Enables the user to run different models on different machines or contexts by changing configuration only.

**Independent Test**: Set `VOICE_MODEL_BACKEND=qwen2.5-omni`, verify voice server starts and `GET /health` returns `model_loaded: true`. Then set `VOICE_MODEL_BACKEND=gemma4` (with Gemma weights present), restart, verify same health response. No code was changed between the two runs.

**Acceptance Scenarios**:

1. **Given** `VOICE_MODEL_BACKEND=qwen2.5-omni` and Qwen weights present, **When** the voice server starts, **Then** `GET /health` returns `{ "status": "ok", "model_loaded": true, "backend": "qwen2.5-omni" }`.
2. **Given** `VOICE_MODEL_BACKEND=gemma4` and Gemma weights present, **When** the voice server starts, **Then** `GET /health` returns `{ "status": "ok", "model_loaded": true, "backend": "gemma4" }`.
3. **Given** an unsupported `VOICE_MODEL_BACKEND` value, **When** the voice server starts, **Then** it fails with a clear error message and `model_loaded: false` in the health check.

---

### User Story 4 — Zero Regression on Existing Functionality (Priority: P4)

After the refactor, all existing behaviour — standard text chat, standard voice (STT+LLM+TTS pipeline), and the voice tutoring channel when enabled — works identically to before. No endpoint paths, response shapes, or user-facing interactions change.

**Why this priority**: This is a pure internal refactoring. The user experience must not change at all.

**Independent Test**: Run the full existing test suite. All previously passing tests continue to pass. The voice tutoring endpoint `POST /conversation/speech/realtime` (or the existing path) returns the same response shape as before the refactor.

**Acceptance Scenarios**:

1. **Given** the refactor is applied, **When** the existing test suite runs, **Then** 100% of previously passing tests still pass.
2. **Given** `VOICE_ENABLED=false` (default), **When** the standard pipeline handles a request, **Then** behaviour is identical to pre-refactor.
3. **Given** `VOICE_ENABLED=true` with a compatible server, **When** a voice tutoring request is made, **Then** the response shape (audio, transcript, pronunciation events, conversation ID) is identical to pre-refactor.

---

### Edge Cases

- What happens if `VOICE_PROVIDER` is set but `VOICE_ENABLED=false`? (The provider setting should be ignored; only evaluated when enabled.)
- What happens if `VOICE_API_URL` is set to a reachable server that implements a different API contract (wrong response format)? (Should fail with a clear deserialization error, not silently return empty data.)
- What happens if the external voice server's `VOICE_MODEL_BACKEND` is unsupported but the backend still calls it? (Voice server should return a 503 or equivalent; backend should propagate it as service unavailable.)
- What happens if model weights for the selected `VOICE_MODEL_BACKEND` are missing? (Server starts but `model_loaded: false`; requests return 503 with a descriptive message.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST select the voice provider via a `VOICE_PROVIDER` environment variable, with no provider name appearing in application source code outside the factory.
- **FR-002**: The system MUST include a voice provider factory that maps `VOICE_PROVIDER` values to concrete provider implementations, following the same pattern as the existing LLM provider factory.
- **FR-003**: All environment variables controlling the voice channel MUST use the `VOICE_` prefix (e.g., `VOICE_ENABLED`, `VOICE_PROVIDER`, `VOICE_API_URL`), replacing any model-specific prefixes (e.g., `OMNI_*`).
- **FR-004**: The external voice server MUST select the underlying model via a `VOICE_MODEL_BACKEND` environment variable, with no model-specific class names in the server's main application file.
- **FR-005**: The external voice server MUST expose a `backend` field in its `GET /health` response indicating which model backend is currently loaded.
- **FR-006**: Adding a new voice provider to the backend MUST require changes only to the factory file and a new provider implementation file — no changes to endpoints, use cases, domain, or frontend.
- **FR-007**: Adding a new model backend to the external voice server MUST require changes only to a new backend file — no changes to the server's HTTP layer or pronunciation event extraction logic.
- **FR-008**: All existing API endpoint paths, request formats, and response shapes MUST remain unchanged after the refactor.
- **FR-009**: The system MUST produce a clear startup error if an unrecognised `VOICE_PROVIDER` or `VOICE_MODEL_BACKEND` value is configured, rather than silently failing at request time.
- **FR-010**: The default `VOICE_PROVIDER` value MUST be `"generic"`, pointing to the self-hosted voice server, consistent with how the LLM defaults to an OpenAI-compatible endpoint.

### Key Entities

- **VoiceProviderFactory**: Maps `VOICE_PROVIDER` configuration values to `VoiceService` implementations; the single place in the codebase that knows which providers exist.
- **VoiceProvider**: A concrete implementation of the voice service interface for one provider (e.g., `GenericVoiceHttpService` for a self-hosted server, future `GeminiVoiceService` for Google's API).
- **ModelBackend**: Within the external voice server, the component responsible for loading a specific model and running inference. One backend per model family (e.g., `QwenBackend`, `GemmaBackend`).
- **ModelBackendRegistry**: Within the external voice server, maps `VOICE_MODEL_BACKEND` values to `ModelBackend` implementations; the single place in the server that knows which model backends exist.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Switching from one voice model to another requires changing 0 source files — only environment variable values.
- **SC-002**: Adding a new voice provider to the backend requires touching at most 2 files: the factory file and one new provider implementation file.
- **SC-003**: Adding a new model backend to the external server requires touching at most 1 file: the new backend implementation.
- **SC-004**: 100% of previously passing backend tests continue to pass after the refactor.
- **SC-005**: The voice tutoring endpoint response shape is byte-for-byte identical to pre-refactor when using the same model and configuration.
- **SC-006**: An invalid `VOICE_PROVIDER` or `VOICE_MODEL_BACKEND` value causes a startup failure with an error message that names the invalid value within 5 seconds of service start.

## Assumptions

- The existing `OmniVoiceService` abstract interface in the domain layer is already model-agnostic and does not need to change.
- The existing `ProcessOmniVoiceUseCase` is already provider-agnostic (it accepts the interface, not a concrete class) and does not need to change.
- The external voice server (`ai_services/omni/`) currently has only one model backend (Qwen2.5-Omni); Gemma 4 backend is created as a stub/placeholder to validate the pattern, not as a production-ready implementation.
- The pronunciation event extraction logic (parsing the `<!-- PRONUNCIATION_EVENTS: -->` block) stays in the external server's HTTP layer, not in individual model backends — because it is part of the API contract between the server and the backend, not model-specific behaviour.
- The frontend and all existing API endpoint paths (`/conversation/omni/speech`, `/conversation/omni/status`) remain unchanged; this is a backend and server-internal refactoring only.
- Backward compatibility: `OMNI_*` env vars are removed (not kept as aliases), since this is an internal system with no external consumers that need a migration window.
