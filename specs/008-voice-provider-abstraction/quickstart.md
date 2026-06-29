# Quickstart & Validation Guide: Voice Provider Abstraction

**Feature**: 008-voice-provider-abstraction  
**Date**: 2026-06-29

This is a backend refactoring. All validation is done via configuration changes, test runs, and grep checks — no new UI or model weights are needed.

---

## Prerequisites

- Python 3.10+ with project dependencies installed
- Project running or backend importable from project root
- Voice server not needed for most validation scenarios (tests mock it)

---

## Scenario 1: No OMNI_* References Remain in Backend Code

**Purpose**: Prove FR-001, FR-003 — model name has been removed from all source files.

```bash
# Should return 0 matches (empty output)
grep -rn "OMNI_\|QwenOmni\|OmniServiceUnavailable" \
    backend/src/ docker-compose.yml .env.example

# Should return 0 matches
grep -rn "QwenOmniHttpService\|OmniServiceUnavailableError" backend/src/
```

**Expected**: No output from either command.

---

## Scenario 2: Factory Is the Only Instantiation Point (FR-002, SC-002)

**Purpose**: Verify `GenericVoiceHttpService` is instantiated only inside the factory.

```bash
# Should appear ONLY in voice_factory.py
grep -rn "GenericVoiceHttpService" backend/src/

# Should appear in main.py as a function call, not a class reference
grep -n "create_voice_service\|GenericVoiceHttpService" backend/src/main.py
```

**Expected**:
- `GenericVoiceHttpService` appears only in `backend/src/infrastructure/omni_service.py` (definition) and `backend/src/infrastructure/voice_factory.py` (instantiation)
- `backend/src/main.py` contains `create_voice_service` — not `GenericVoiceHttpService`

---

## Scenario 3: All Tests Still Pass (FR-008, SC-004)

**Purpose**: Zero regression validation.

```bash
python3 -m pytest backend/tests/ --ignore=backend/tests/integration \
    --override-ini="addopts=" -v
```

**Expected**: Same pass/fail count as before the refactoring. The 2 pre-existing failures (`test_settings_defaults`, `test_openai_compatible_generate_response`) may still fail — that is acceptable and pre-existing. All other tests pass.

---

## Scenario 4: Unknown VOICE_PROVIDER Fails at Startup (FR-009, SC-006)

**Purpose**: Verify startup error on invalid provider.

```bash
VOICE_ENABLED=true VOICE_PROVIDER=invalid_provider \
    python3 -c "
from backend.src.config import Settings
from backend.src.infrastructure.voice_factory import create_voice_service
s = Settings()
try:
    create_voice_service(s)
    print('FAIL: No error raised')
except ValueError as e:
    print(f'PASS: Got expected error: {e}')
"
```

**Expected**: Prints `PASS: Got expected error: Unknown VOICE_PROVIDER 'invalid_provider'. ...`

---

## Scenario 5: Adding a New Provider Touches Only 2 Files (SC-002)

**Purpose**: Validate extensibility claim.

```bash
# Verify adding a stub provider only requires:
# 1. A new file: backend/src/infrastructure/gemini_service.py
# 2. One entry in: backend/src/infrastructure/voice_factory.py
# No other files need changing.

# Check that main.py does NOT reference provider class names directly
grep -n "GenericVoice\|GeminiVoice" backend/src/main.py
```

**Expected**: No output — `main.py` only references `create_voice_service`, not any provider class.

---

## Scenario 6: External Server Selects Backend via Env Var (FR-004, US3)

**Purpose**: Verify `VOICE_MODEL_BACKEND` controls model selection in the voice server.

```bash
# Check the registry in main.py of the voice server
grep -n "VOICE_MODEL_BACKEND\|_BACKENDS\|QwenBackend\|GemmaBackend" \
    ai_services/omni/app/main.py
```

**Expected**:
- `VOICE_MODEL_BACKEND` appears as the env var being read
- A registry dict maps backend names to classes
- No direct `Qwen2_5Omni*` imports in `main.py` (only in `backends/qwen.py`)

```bash
# Qwen-specific imports should be ONLY in the backend file
grep -n "Qwen2_5Omni" ai_services/omni/app/main.py         # should return empty
grep -n "Qwen2_5Omni" ai_services/omni/app/backends/qwen.py  # should return matches
```

---

## Scenario 7: Health Endpoint Returns backend Field (FR-005)

**Purpose**: Verify the voice server reports which model backend is active.

If the voice server is running:
```bash
curl http://localhost:8003/health
```

**Expected**:
```json
{ "status": "ok", "model_loaded": true, "backend": "qwen2.5-omni" }
```

If not running (offline check via code):
```bash
grep -n "backend_name\|\"backend\"" ai_services/omni/app/main.py
```

**Expected**: `main.py` includes `"backend": backend.backend_name()` in the health response.

---

## Artifact References

- Configuration contract: `contracts/voice-config-contract.md`
- Data model changes: `data-model.md`
- Research decisions: `research.md`
