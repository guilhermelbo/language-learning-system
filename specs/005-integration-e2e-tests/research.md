# Research: Integration and E2E Testing Framework

**Created**: 2026-06-12
**Feature**: [spec.md](spec.md)

---

## Research Findings

### 1. Pytest Best Practices for Backend Integration Tests

**Decision**: Use `pytest` with `pytest-cov` for coverage, `httpx-mock` for mocking external HTTP calls, and `responses` library for additional HTTP mocking flexibility.

**Rationale**: 
- `pytest` is the established testing framework in the project (per AGENTS.md)
- `httpx-mock` integrates seamlessly with the async `httpx` client used by backend services
- `responses` provides additional mock HTTP server capabilities for complex scenarios
- `pytest-cov` ensures test coverage remains high

**Alternatives considered**:
- `unittest.mock` - Not needed, `httpx-mock` is more appropriate for HTTP
- `pytest-asyncio` - `httpx` already handles async natively
- `factory-boy` - Not required for simple test data fixtures

**References**:
- Pytest documentation: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- httpx-mock: https://pypi.org/project/pytest-httpx/

---

### 2. Playwright for Frontend E2E Testing

**Decision**: Use `@playwright/test` for frontend E2E testing.

**Rationale**:
- Playwright is actively maintained and supports both Chromium, Firefox, and WebKit
- Better browser automation than Selenium for modern web applications
- Supports TypeScript natively with excellent type inference
- Already indicated in `.gitignore` with `.playwright-mcp`
- Provides built-in test runners and codegen tools

**Alternatives considered**:
- `cypress` - Also excellent, but Playwright has better multi-browser support
- `selenium` - Too verbose and slower than Playwright
- `puppeteer` - Only supports Chromium, less flexible

**References**:
- Playwright documentation: https://playwright.dev/
- Playwright TypeScript: https://playwright.dev/docs/test-typescript

---

### 3. Mocking External AI Services

**Decision**: Create dedicated mock services for STT, LLM, and TTS that return synthetic test responses.

**Rationale**:
- Avoids API costs for external services
- Ensures test stability and reproducibility
- Enables testing of error conditions (timeouts, invalid JSON, service failures)
- Allows testing with synthetic data only (privacy compliance)

**Implementation approach**:
- Use `httpx-mock` to intercept HTTP calls to external service URLs
- Create fixtures in `tests/fixtures/mock_services.py`
- Define JSON schemas for expected responses
- Support configurable delays for timeout testing

**Alternatives considered**:
- Testcontainers with real services - Too slow for unit tests
- External mock services (WireMock) - Adds deployment complexity
- Manual mocking per test - Error-prone, not scalable

---

### 4. Docker Test Infrastructure

**Decision**: Use `testcontainers-python` for running test services in Docker containers.

**Rationale**:
- Simplifies Docker container management in tests
- Provides automatic lifecycle management (start/stop)
- Supports both real services and custom containers
- Integrates well with pytest fixtures

**Alternatives considered**:
- `docker-py` directly - More verbose, requires manual container management
- `docker-compose` for tests - Good for full stack, but testcontainers better for unit-level isolation
- Manual Docker commands - Too fragile and error-prone

**References**:
- Testcontainers Python: https://testcontainers-python.readthedocs.io/

---

### 5. Test Data Generation

**Decision**: Create synthetic test data generators in `tests/fixtures/test_data.py`.

**Rationale**:
- Ensures all test data is synthetic (no real user data)
- Provides consistent data across test runs
- Enables edge case testing with controlled inputs
- Supports multilingual test scenarios (Portuguese/English)

**Key data points**:
- Test audio files (short .wav files for STT)
- Bilingual text samples (simple Portuguese/English phrases)
- Error scenario payloads (malformed JSON, empty requests)

---

### 6. CI/CD Integration

**Decision**: Create GitHub Actions workflow for automated test execution.

**Rationale**:
- Provides automated testing on every PR
- Catches regressions before merge
- Supports parallel test execution for faster feedback
- Generates coverage reports

**Workflow structure**:
- `test.yml` - Runs on push/PR to main branches
- Matrix strategy for different Python versions
- Coverage upload to coverage service (codecov.io)
- E2E tests run in separate job with browser support

**References**:
- GitHub Actions documentation: https://docs.github.com/en/actions

---

### 7. Test Execution Strategy

**Decision**: Organize tests by priority and dependency:
- **P1**: Backend integration tests (run first, no Docker required)
- **P2**: Frontend E2E tests (run after backend tests pass)
- **P3**: Full stack Docker tests (run last, requires full container stack)

**Rationale**:
- Faster feedback from lightweight tests first
- P1 tests can run locally without Docker
- P3 tests validate full integration but are slower
- Parallel execution where possible (P1 and P2 independent)

---

### 8. Error Handling in Tests

**Decision**: Create comprehensive error test scenarios covering:
- Service timeouts (STT/LLM/TTS)
- Invalid JSON responses
- Empty/malformed requests
- Network failures
- Resource exhaustion (disk space, memory)

**Rationale**:
- Ensures graceful degradation as per Constitution Principle IV
- Tests error handling paths not covered by happy path
- Validates user-friendly error messages

---

**All NEEDS CLARIFICATION resolved**. The research confirms the technical approach aligns with project conventions and best practices.
