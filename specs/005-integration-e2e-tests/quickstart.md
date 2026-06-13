# Quickstart Guide: Integration and E2E Testing Framework

**Created**: 2026-06-12
**Feature**: [spec.md](spec.md)

---

## Prerequisites

1. **Docker** - For full stack tests (optional for backend tests)
2. **Python 3.10+** - For backend tests
3. **Node.js 18+** - For frontend E2E tests
4. **Git** - For repository access

---

## Validation Scenarios

### Scenario 1: Backend Integration Tests (P1 - MVP)

**Goal**: Verify all backend API endpoints work correctly with mocked external services.

**Setup**:
```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov httpx-mock responses
```

**Test Command**:
```bash
pytest tests/integration/ -v --cov=backend/src --cov-report=html
```

**Expected Outcome**:
- All integration tests pass
- Coverage report shows >80% coverage
- Test duration < 5 minutes

**Validation Steps**:
1. Run `pytest tests/integration/` and verify exit code is 0
2. Check coverage report shows required files are covered
3. Verify test results include all user stories (US1, US2, US3)

**Reference**: [Test Framework Contract](contracts/test-framework.md)

---

### Scenario 2: Frontend E2E Tests (P2)

**Goal**: Verify frontend handles user interactions correctly.

**Setup**:
```bash
cd frontend
npm install
npm install -D @playwright/test
npx playwright install
```

**Test Command**:
```bash
npx playwright test
```

**Expected Outcome**:
- All E2E tests pass
- Tests execute in < 10 minutes total
- No flaky tests (>90% pass rate)

**Validation Steps**:
1. Run `npx playwright test` and verify exit code is 0
2. Check test reports show all user stories covered
3. Verify screenshots/videos are generated for failures

**Reference**: [spec.md - User Story 2](spec.md)

---

### Scenario 3: Full Stack Docker Tests (P3)

**Goal**: Verify entire application stack works together.

**Setup**:
```bash
docker-compose up -d
```

**Test Command**:
```bash
pytest tests/e2e/ -v --cov=backend/src --cov=frontend/src
```

**Expected Outcome**:
- All containers start successfully
- Full stack tests pass with all services healthy
- Graceful degradation when services fail

**Validation Steps**:
1. Start containers with `docker-compose up -d`
2. Verify all services are healthy: `docker-compose ps`
3. Run full stack tests: `pytest tests/e2e/ -v`
4. Verify test results show all three user stories validated

**Reference**: [spec.md - User Story 3](spec.md)

---

## Error Handling Validation

### Test 1: Service Timeout

**Setup**: Configure mock to return delay of 30000ms (30 seconds)

**Expected**: Backend times out gracefully with user-friendly error message

**Command**:
```bash
pytest tests/integration/test_error_handling.py::test_service_timeout -v
```

### Test 2: Invalid JSON Response

**Setup**: Configure mock to return malformed JSON

**Expected**: Backend handles JSON parsing error and returns error response

**Command**:
```bash
pytest tests/integration/test_error_handling.py::test_invalid_json -v
```

### Test 3: Empty Request

**Setup**: Send empty audio file or empty text

**Expected**: Backend validates input and returns appropriate error

**Command**:
```bash
pytest tests/integration/test_error_handling.py::test_empty_request -v
```

---

## CI/CD Integration

### GitHub Actions Workflow

**File**: `.github/workflows/test.yml`

**Validation Steps**:
1. Create PR to `main` branch
2. Verify test workflow runs automatically
3. Check all test jobs pass (backend, frontend, full-stack)
4. Verify coverage report is uploaded

**Expected Outcome**:
- Tests run on every PR to main
- Coverage threshold enforced (>80%)
- All tests must pass before merge

---

## Quick Reference

### Test Commands

| Command | Description | Priority |
|---------|-------------|----------|
| `pytest tests/integration/ -v` | Backend integration tests | P1 |
| `pytest tests/integration/ --cov=backend/src` | Backend with coverage | P1 |
| `npx playwright test` | Frontend E2E tests | P2 |
| `docker-compose up -d && pytest tests/e2e/` | Full stack tests | P3 |
| `pytest tests/integration/test_error_handling.py` | Error handling tests | All |

### Test File Locations

| Location | Tests |
|----------|-------|
| `backend/tests/integration/` | Backend integration |
| `frontend/tests/e2e/` | Frontend E2E |
| `tests/e2e/` | Full stack Docker |
| `tests/fixtures/` | Shared fixtures |

### Key Files to Verify

| File | Purpose |
|------|---------|
| `specs/005-integration-e2e-tests/contracts/test-framework.md` | Test contract |
| `specs/005-integration-e2e-tests/data-model.md` | Test data schemas |
| `backend/tests/conftest.py` | Pytest fixtures |
| `frontend/playwright.config.ts` | Playwright config |

---

## Troubleshooting

### Issue 1: Tests fail locally but pass in CI

**Cause**: Local environment differs from CI (Python version, dependencies)

**Solution**: Use Docker for test execution or match CI environment exactly

### Issue 2: Slow test execution

**Cause**: Full stack tests include Docker startup time

**Solution**: Run backend/frontend tests separately for faster feedback

### Issue 3: Mock services not working

**Cause**: Mock interception not configured correctly

**Solution**: Verify `httpx-mock` fixture is applied and mocks are registered

---

## Notes

- This guide validates the testing framework, not the application itself
- All validation scenarios are independent and can run in any order
- Pass rate must be >90% for tests to be considered stable
- Documentation references link to contracts and data models for implementation details
