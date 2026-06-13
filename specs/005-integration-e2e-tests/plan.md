# Implementation Plan: Integration and E2E Testing Framework

**Branch**: `005-integration-e2e-tests` | **Date**: 2026-06-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-integration-e2e-tests/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

This feature implements a comprehensive testing framework for the LingoAI language learning system, covering three levels of testing: backend API integration tests, frontend E2E component tests, and full stack Docker E2E tests. The tests ensure the conversation flow works correctly across all services (STT, LLM, TTS) and provide CI/CD integration for automated quality assurance.

**Primary requirement**: Create test infrastructure that validates the complete application behavior without relying on external AI service costs, using mocks and lightweight containers.

## Technical Context

**Language/Version**: Python 3.10+ (backend tests), TypeScript 5.x (frontend tests)

**Primary Dependencies**: 
- Backend: `pytest`, `pytest-cov`, `httpx`, `httpx-mock`, `responses`
- Frontend: `@playwright/test`
- Utilities: `docker-py`, `testcontainers-python`

**Storage**: No persistent storage required (tests are stateless, run in-memory)

**Testing**: Backend uses `pytest`, Frontend uses `Playwright`

**Target Platform**: Linux CI/CD environment (GitHub Actions or similar), local development

**Project Type**: Testing infrastructure for web application

**Performance Goals**: 
- Backend integration tests complete within 5 minutes
- Frontend E2E tests achieve 90%+ pass rate when healthy
- Full stack tests runnable with single command

**Constraints**: 
- Mock external AI services to avoid costs
- Use synthetic test data only (no real user data)
- Tests must run in CI/CD without manual intervention
- Containerized test environment required

**Scale/Scope**: 
- ~20-30 backend integration test cases
- ~10-15 frontend E2E test scenarios
- 1 full stack Docker test suite

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I - Docker-First Deployment**: ✅ COMPLIANT - Tests designed to run in Docker containers with `docker-compose up --build`

**Principle II - LLM Independence**: ✅ COMPLIANT - Tests mock external LLM services, no dependency on actual LLM instance

**Principle III - Clean Architecture + DDD**: ✅ COMPLIANT - Tests organized by domain layers (domain, application, infrastructure)

**Principle IV - Type Safety & Async I/O**: ✅ COMPLIANT - All test code uses type hints and async/await

**Principle V - JSON Contract Compliance**: ✅ COMPLIANT - Tests validate JSON response format from LLM

**Principle VI - Testing Discipline**: ✅ COMPLIANT - This feature IS the testing infrastructure, directly implements constitution principle

**Status**: All gates PASSED - No violations

## Project Structure

### Documentation (this feature)

```text
specs/005-integration-e2e-tests/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
# Backend Tests (Phase 1 - P1)
backend/tests/
├── __init__.py
├── conftest.py          # Pytest fixtures, mock services
├── integration/
│   ├── __init__.py
│   ├── test_conversation_speech.py
│   ├── test_conversation_text.py
│   ├── test_error_handling.py
│   └── conftest.py
├── unit/
│   ├── __init__.py
│   ├── domain/
│   │   └── test_message.py
│   └── application/
│       └── test_use_cases.py
└── e2e/
    └── test_full_stack.py

# Frontend Tests (Phase 1 - P2)
frontend/
├── tests/
│   ├── __init__.py
│   ├── e2e/
│   │   ├── __init__.py
│   │   ├── test_voice_interaction.spec.ts
│   │   ├── test_text_interaction.spec.ts
│   │   └── test_audio_playback.spec.ts
│   └── fixtures/
│       └── mock_responses.ts
└── playwright.config.ts

# Test Infrastructure (Shared)
tests/
├── __init__.py
├── fixtures/
│   ├── __init__.py
│   ├── mock_services.py     # Mock STT/LLM/TTS services
│   └── test_data.py         # Synthetic test data
├── docker/
│   ├── __init__.py
│   └── test_containers.py   # Docker container fixtures
└── utils/
    ├── __init__.py
    └── audio_utils.py       # Test audio generation utilities
```

**Structure Decision**: Tests organized by priority (P1 backend first, then P2 frontend, then P3 full stack) with shared fixtures for reusability.

## Complexity Tracking

> **No complexity violations** - The test architecture follows standard industry practices and leverages well-established frameworks (pytest, Playwright) that are appropriate for the project scale. No alternative patterns rejected.
