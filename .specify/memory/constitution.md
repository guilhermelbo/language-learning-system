# LingoAI Constitution

<!-- Core governance document for LingoAI - AI-powered language learning system -->

## Core Principles

### I. Docker-First Deployment

Every service MUST be containerized and orchestrated via Docker Compose. The primary deployment method is a single-command `docker-compose up --build`. External infrastructure containers (llamacpp, hindsight, searxng) are shared and MUST NEVER be modified, stopped, or removed by agent actions.

**Rationale**: User requirement for single-command deployment. The project must be ready to use immediately after running docker compose, independent of specific LLM implementation.

### II. LLM Independence

The backend MUST connect to external LLM services via environment variables only (LLM_PROVIDER, LLM_MODEL_NAME, LLM_BASE_URL). The backend depends ONLY on STT and TTS services - no `depends_on` for LLM in docker-compose. Manual model installation is required; the application MUST NOT bundle or manage model binaries.

**Rationale**: Flexibility for remote/local LLM instances. The user explicitly rejected Ollama/llama.cpp containers in docker-compose to enable easy API swapping without modifying the stack.

### III. Clean Architecture + DDD

The backend MUST follow Clean Architecture with Domain-Driven Design. Core entities (Student, Message, Conversation) and service interfaces (STTService, LLMService, TTSService) live in `domain/`. Use cases orchestrate business logic in `application/`. External integrations live in `infrastructure/`. This separation is NON-NEGOTIABLE.

**Rationale**: Clear boundaries enable testability, service swapping, and maintainability. All external services MUST implement domain interfaces.

### IV. Type Safety & Async I/O

All Python function signatures MUST include type hints (PEP 604 union types preferred). All external service calls MUST use `async/await` with `httpx.AsyncClient`. Graceful degradation: log errors and return empty strings/blobs on service failures.

**Rationale**: Static typing reduces runtime errors. Async I/O is essential for handling multiple external service calls without blocking.

### V. JSON Contract Compliance

LLM responses MUST be strict JSON arrays with `text` and `lang` fields. Frontend-to-backend communication uses FormData (multipart) for speech and JSON body for text. These contracts are MANDATORY and MUST NOT be violated.

**Rationale**: Bilingual conversation flow requires predictable, machine-parseable responses. The frontend TTS pipeline depends on exact field names.

### VI. Testing Discipline

Backend tests run via `pytest tests/ -v`. Frontend linting runs via `npm run lint`. Tests are REQUIRED for all new features. Error handling MUST show user-friendly messages. Manual QA checklist items MUST pass before deployment.

**Rationale**: No formal test framework mandates exist, but pytest and ESLint are established conventions. Testing ensures quality without formal gates.

## Technology Stack Requirements

**Backend**: Python 3.10+ with FastAPI and uvicorn
**Frontend**: Next.js with Node.js 18+ (App Router)
**AI Services**: STT (Faster-Whisper), TTS (Piper), LLM (external via config)
**Containerization**: Docker with Python 3.10 slim images
**Package Managers**: pip (Python), npm (Node.js)

**Rationale**: Technology choices are fixed in docker-compose and Dockerfiles. Deviations require constitutional amendment.

## Security & Privacy

All AI models run locally. No external telemetry or data collection. User conversations remain in-memory only (no database in v1). External LLM connections use HTTP; no authentication is implemented.

**Rationale**: Privacy is a core feature. Local execution enables low latency and user trust.

## Governance

**Amendment Procedure**: This constitution MAY be amended by updating `.specify/memory/constitution.md` with a new version number. Changes that add/remove principles require explicit justification.

**Versioning**: Semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Backward incompatible principle removals or redefinitions
- **MINOR**: New principle added or materially expanded guidance
- **PATCH**: Clarifications, wording, typo fixes, non-semantic refinements

**Compliance Review**: All PRs/reviews MUST verify constitution compliance. Complexity MUST be justified in the Implementation Plan under "Complexity Tracking". Use runtime guidance files for development decisions.

**Version**: 1.0.0 | **Ratified**: 2026-06-12 | **Last Amended**: 2026-06-12
