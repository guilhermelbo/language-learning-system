<!--
Sync Impact Report:
- Version change: 1.0.0 -> 1.1.0
- List of modified principles:
    - [NEW] SDD Article I: Library-First Principle
    - [NEW] SDD Article II: CLI Interface Mandate
    - [NEW] SDD Article III: Test-First Imperative
    - [NEW] SDD Article VII: Simplicity
    - [NEW] SDD Article VIII: Anti-Abstraction
    - [NEW] SDD Article IX: Integration-First Testing
    - [RENAMED] Privacy-First & Local AI -> Article IV
    - [RENAMED] Clean Architecture Compliance -> Article V
    - [RENAMED] High Performance & Low Latency -> Article VI
    - [RENAMED] Adaptive Learning & Memory -> Article X
- Templates requiring updates:
    - .specify/templates/plan-template.md (⚠ pending)
    - .specify/templates/spec-template.md (⚠ pending)
-->
# LingoAI Constitution

## Core Principles

### I. Library-First Principle (SDD)
Every feature in LingoAI MUST begin its existence as a standalone library.
No feature shall be implemented directly within application code without first being abstracted into a reusable library component.
Libraries must be self-contained, independently testable, and have clear purpose.

### II. CLI Interface Mandate (SDD)
Every library must expose its functionality through a command-line interface.
All CLI interfaces MUST:
- Accept text as input (via stdin, arguments, or files)
- Produce text as output (via stdout, errors via stderr)
- Support JSON format for structured data exchange

### III. Test-First Imperative (SDD - NON-NEGOTIABLE)
All implementation MUST follow strict Test-Driven Development.
No implementation code shall be written before:
1. Unit/Contract tests are written
2. Tests are validated and approved
3. Tests are confirmed to FAIL (Red phase)

### IV. Privacy-First & Local AI (LingoAI)
LingoAI utilizes local AI models (Ollama, Faster-Whisper, Piper) to ensure user data privacy and low latency. All sensitive processing (STT, LLM inference, TTS) must occur within the user's execution environment. No audio or transcript data shall be sent to external cloud APIs unless explicitly configured.

### V. Clean Architecture Compliance (LingoAI)
The project enforces strict separation of concerns following Clean Architecture and DDD principles.
 Dependencies must point inwards (Infrastructure -> Application -> Domain).
- **Domain**: Pure business logic/entities.
- **Application**: Use cases.
- **Infrastructure**: Implementations.
- **Interface**: Adapters.

### VI. High Performance & Low Latency (LingoAI)
Conversational flow must be natural.
- **STT**: < 500ms latency.
- **TTS**: < 200ms initial byte latency.
- **UI**: Premium, responsive glassmorphism.

### VII. Simplicity (SDD)
- Maximum 3 projects/modules for initial implementation of any feature.
- No "future-proofing" without immediate requirement justification.
- Start simple, YAGNI principles strictly enforced.

### VIII. Anti-Abstraction (SDD)
- Use framework features directly rather than wrapping them in custom layers.
- Avoid generic repository patterns unless strictly required by Clean Architecture for specific external adapters.
- Single model representation where possible.

### IX. Integration-First Testing (SDD)
Tests MUST use realistic environments where feasible:
- Prefer real databases over mocks for integration tests.
- Contract tests mandatory for all new library interfaces.

### X. Adaptive Learning & Memory (LingoAI)
The system tracks user progress, errors, and vocabulary mastery (Spaced Repetition).
All components share short-term and long-term memory contexts.

## Governance

### Amendment Procedure
This Constitution supersedes all other documentation. Amendments require a Pull Request with updated justification and must follow the Semantic Versioning policy.
- **MAJOR**: Fundamental change to a core principle.
- **MINOR**: Adding a new principle or significant subsection.
- **PATCH**: Clarifications and wording fixes.

### Compliance
All architectural decisions and Pull Requests must be verified against these principles. The "Constitution Check" in implementation plans is mandatory.

**Version**: 1.1.0 | **Ratified**: 2026-01-25 | **Last Amended**: 2026-01-25
