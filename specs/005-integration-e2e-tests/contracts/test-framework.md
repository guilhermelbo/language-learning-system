# Contract: Test Framework Interface

**Created**: 2026-06-12
**Feature**: [spec.md](spec.md)

---

## Overview

This contract defines the interface for the test framework used across the LingoAI project. It ensures consistency in test execution, reporting, and integration with CI/CD pipelines.

---

## Test Framework API Contract

### 1. Test Discovery

**Interface**: Tests follow standard pytest/Playwright naming conventions.

**Format**:
- Python tests: `test_<name>.py` or `<name>_test.py`
- Test functions: `test_<description>()`
- Test classes: `Test<Description>`
- E2E tests: `*.spec.ts` (Playwright)

**Example**:
```python
def test_conversation_speech_endpoint():
    """Test backend conversation endpoint"""
    pass

class TestAudioPlayback:
    """Test audio playback functionality"""
    def test_playback_success(self):
        pass
```

```typescript
// Playwright E2E test
test('voice interaction flow', async ({ page }) => {
  // Test logic
});
```

---

### 2. Test Fixture Protocol

**Interface**: Pytest fixtures must follow this pattern.

**Requirements**:
- All fixtures MUST use `@pytest.fixture` decorator
- Global fixtures (module/session) MUST be clearly documented
- Dependencies between fixtures MUST be explicit in fixture signatures

---

### 3. Test Result Report Format

**Interface**: Tests must produce structured output for CI/CD integration.

**Format (JSON)**:
```json
{
  "test_id": "unique-id-123",
  "test_name": "test_conversation_endpoint",
  "status": "passed",
  "duration_ms": 150,
  "timestamp": "2026-06-12T10:30:00Z",
  "coverage_percentage": 85.5,
  "tags": ["integration", "backend", "p1"]
}
```

**Status Values**:
- `passed`: Test completed successfully
- `failed`: Test assertion failed
- `skipped`: Test was skipped (reason in metadata)
- `error`: Test crashed or encountered unexpected error

**Requirements**:
- All test runners MUST produce valid JSON output
- `test_id` MUST be unique across the test run
- `duration_ms` MUST be positive integer

---

### 4. Mock Service Contract

**Interface**: Mock services must respond with predictable data.

**Error Response Format**:
```json
{
  "status": 500,
  "body": {
    "error": "Service unavailable",
    "message": "STT service is down",
    "code": "SERVICE_ERROR"
  }
}
```

**Requirements**:
- Mock responses MUST include proper HTTP status codes
- Error responses MUST follow the error format above
- Delay simulation MUST support milliseconds (not seconds)

---

### 5. Test Data Contract

**Interface**: Synthetic test data must follow these schemas.

**Audio File Schema**:
```json
{
  "audio_id": "audio-001",
  "language": "pt",
  "duration_seconds": 3.5,
  "format": "wav",
  "content_type": "audio/wav",
  "sample_rate_hz": 16000
}
```

**Conversation Turn Schema**:
```json
{
  "turn_id": "turn-001",
  "user_input": "Olá, como vai?",
  "user_input_type": "text",
  "user_language": "pt",
  "llm_response": null,
  "status": "pending"
}
```

**Requirements**:
- All test data MUST be synthetic (no real user data)
- Audio files MUST use standard sample rates (16000 Hz)
- Language codes MUST use ISO 639-1 (pt, en)

---

### 6. CI/CD Pipeline Contract

**Interface**: GitHub Actions workflow must follow this structure.

**Requirements**:
- Pipeline MUST run on all push/PR events to main branches
- Coverage reports MUST be uploaded to coverage service
- Tests MUST have a 30-minute timeout
- All tests MUST pass before PR merge

---

### 7. Test Execution Contract

**Interface**: Test commands must be reproducible and deterministic.

**Commands**:
```bash
# Backend integration tests (fastest, no Docker)
pytest backend/tests/integration/ -v --cov=backend/src

# Frontend E2E tests
npm run test:e2e

# Full stack Docker tests
docker-compose up --build && pytest tests/e2e/
```

**Exit Codes**:
- `0`: All tests passed
- `1`: One or more tests failed
- `2`: Test collection error
- `128`: General error

**Requirements**:
- Test commands MUST be documented in README
- Exit codes MUST follow Unix conventions
- Test output MUST be human-readable with verbose flag

---

## Notes

- All contracts are enforced by the test infrastructure itself
- Violations will cause test collection or execution to fail
- Contracts are versioned with the project (v1.0.0)
- Breaking changes require major version bump
