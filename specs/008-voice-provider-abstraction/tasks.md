# Tasks: Voice Provider Abstraction

**Input**: Design documents from `specs/008-voice-provider-abstraction/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Spec does not explicitly request TDD. Test-related tasks are limited to updating existing test files that reference renamed classes.

**Organization**: Tasks are grouped by user story. This is a pure refactoring — no new dependencies, no schema migrations, no API shape changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: Verify no new dependencies are needed. This refactoring touches existing files only (plus 4 new files). No package installs required.

- [X] T001 Verify existing tests pass before any changes: run `python3 -m pytest backend/tests/ --ignore=backend/tests/integration --override-ini="addopts=" -v` and record pass/fail baseline

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Rename config fields and the service class/exception. Every other task depends on these names being stable.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete — factory and main.py both reference the renamed config fields and the renamed class.

- [X] T002 Rename `omni_*` config fields to `voice_*` and add `voice_provider` field in `backend/src/config.py`: rename `omni_enabled→voice_enabled`, `omni_api_url→voice_api_url`, `omni_timeout_seconds→voice_timeout_seconds`, `omni_max_audio_seconds→voice_max_audio_seconds`; add `voice_provider: str = Field(default="generic", alias="VOICE_PROVIDER")`
- [X] T003 Rename class and exception in `backend/src/infrastructure/omni_service.py`: `QwenOmniHttpService` → `GenericVoiceHttpService`, `OmniServiceUnavailableError` → `VoiceServiceUnavailableError`; update all internal references within that file
- [X] T004 [P] Rename `OMNI_*` env vars to `VOICE_*` in `docker-compose.yml`: `OMNI_ENABLED→VOICE_ENABLED`, `OMNI_API_URL→VOICE_API_URL`, `OMNI_TIMEOUT_SECONDS→VOICE_TIMEOUT_SECONDS`, `OMNI_MAX_AUDIO_SECONDS→VOICE_MAX_AUDIO_SECONDS`
- [X] T005 [P] Rename `OMNI_*` env vars to `VOICE_*` in `.env.example`: same renames as T004, add `VOICE_PROVIDER=generic` entry

**Checkpoint**: `grep -rn "omni_enabled\|omni_api_url\|QwenOmniHttpService\|OmniServiceUnavailableError" backend/src/` returns zero matches

---

## Phase 3: User Story 1 — Switch Voice Model via Configuration Only (Priority: P1) 🎯 MVP

**Goal**: Voice model can be swapped by changing env vars only — no source code edits. Factory is the single instantiation point for the voice service.

**Independent Test**: `grep -rn "GenericVoiceHttpService" backend/src/main.py` returns zero matches; `grep -n "create_voice_service" backend/src/main.py` returns a match.

### Implementation for User Story 1

- [X] T006 [US1] Create `backend/src/infrastructure/voice_factory.py`: implement `create_voice_service(settings: Settings) -> OmniVoiceService` mapping `"generic"` → `GenericVoiceHttpService(api_url=settings.voice_api_url, timeout=settings.voice_timeout_seconds)`; raise `ValueError(f"Unknown VOICE_PROVIDER '{settings.voice_provider}'. Supported: ['generic']")` for any other value; import `Settings` from `..config`, `OmniVoiceService` from `..domain.interfaces`, `GenericVoiceHttpService` from `.omni_service`
- [X] T007 [US1] Update `backend/src/main.py` to use the factory: add `from .infrastructure.voice_factory import create_voice_service`; replace direct `QwenOmniHttpService(...)` instantiation with `create_voice_service(settings)`; rename all `settings.omni_enabled` → `settings.voice_enabled`, `settings.omni_max_audio_seconds` → `settings.voice_max_audio_seconds`, `settings.omni_api_url` → `settings.voice_api_url` references; remove the `QwenOmniHttpService` import; remove `OmniServiceUnavailableError` import and replace with `VoiceServiceUnavailableError`

**Checkpoint**: Backend starts with `VOICE_ENABLED=false` (default) without errors. With `VOICE_PROVIDER=invalid_provider VOICE_ENABLED=true`, startup raises `ValueError` naming the invalid value.

---

## Phase 4: User Story 2 — Add a New Voice Provider Without Touching Existing Code (Priority: P2)

**Goal**: The factory pattern is genuinely extensible — adding a new provider requires only 2 files (factory + new implementation). No endpoints, use cases, domain, or frontend changes needed.

**Independent Test**: `grep -n "GenericVoice\|VoiceService" backend/src/main.py` returns zero class references (only `create_voice_service` call); `grep -rn "create_voice_service" backend/src/` returns matches only in `voice_factory.py` and `main.py`.

### Implementation for User Story 2

This story has no additional implementation tasks — the factory structure created in US1 (T006) already satisfies this story's acceptance criteria. The factory pattern is correct if:
- `main.py` only references `create_voice_service`, not any concrete class
- Adding a new provider requires creating one new file + one new `elif` in `voice_factory.py`

- [X] T008 [US2] Validate extensibility by grep: confirm `backend/src/main.py` contains `create_voice_service` and no direct `GenericVoiceHttpService` reference; confirm `backend/src/infrastructure/voice_factory.py` is the only file that maps provider names to implementations

**Checkpoint**: US2 acceptance criteria satisfied — extensibility pattern is in place from T006.

---

## Phase 5: User Story 3 — External Voice Server Multiple Backends (Priority: P3)

**Goal**: The external voice server selects its model via `VOICE_MODEL_BACKEND` env var. No Qwen-specific class names appear in `ai_services/omni/app/main.py`. `GET /health` returns a `backend` field.

**Independent Test**: `grep -n "Qwen2_5Omni" ai_services/omni/app/main.py` returns zero matches; `grep -n "Qwen2_5Omni" ai_services/omni/app/backends/qwen.py` returns matches; `grep -n "\"backend\"" ai_services/omni/app/main.py` returns a match.

### Implementation for User Story 3

- [X] T009 [US3] Create `ai_services/omni/app/backends/__init__.py` as an empty file to make `backends/` a Python package
- [X] T010 [US3] Create `ai_services/omni/app/backends/base.py` with the `ModelBackend` ABC: abstract methods `load(self) -> None`, `infer(self, audio: np.ndarray, sample_rate: int, system_prompt: str, context: list) -> tuple[np.ndarray, int, str]`, `is_loaded(self) -> bool`, `backend_name(self) -> str`; import `ABC`, `abstractmethod` from `abc` and `numpy as np`
- [X] T011 [US3] Create `ai_services/omni/app/backends/qwen.py` with `QwenBackend(ModelBackend)`: move all code from `_load_model()` and `_run_inference()` in `ai_services/omni/app/main.py` into this class; `load()` → model loading code (imports `Qwen2_5OmniForConditionalGeneration`, `Qwen2_5OmniProcessor`); `infer(audio, sample_rate, system_prompt, context) -> tuple[np.ndarray, int, str]` → inference code returning `(audio_array, SAMPLE_RATE, text_output)`; `is_loaded()` → returns `True` if model and processor are set; `backend_name()` → returns `"qwen2.5-omni"`; read `VOICE_MODEL_DIR` env var (default: `/app/models/Qwen2.5-Omni-7B`)
- [X] T012 [US3] Create `ai_services/omni/app/backends/gemma.py` with `GemmaBackend(ModelBackend)` stub: `load()` raises `NotImplementedError("Gemma 4 backend not yet implemented")`; `infer(...)` raises `NotImplementedError`; `is_loaded()` returns `False`; `backend_name()` returns `"gemma4"`
- [X] T013 [US3] Refactor `ai_services/omni/app/main.py` to use the backend registry: add `_BACKENDS = {"qwen2.5-omni": lambda: QwenBackend(), "gemma4": lambda: GemmaBackend()}`; read `VOICE_MODEL_BACKEND = os.environ.get("VOICE_MODEL_BACKEND", "qwen2.5-omni")`; on startup, instantiate the backend from `_BACKENDS[VOICE_MODEL_BACKEND]` (raise `ValueError` if key not found); replace calls to `_load_model()` with `backend.load()` and `_run_inference(...)` with `backend.infer(...)`; remove `_load_model()` and `_run_inference()` functions from `main.py`; rename `OMNI_MODEL_DIR` reference to use `VOICE_MODEL_DIR` (now in `QwenBackend`); update `GET /health` to include `"backend": backend.backend_name()` in the response dict; import `QwenBackend` from `.backends.qwen` and `GemmaBackend` from `.backends.gemma`

**Checkpoint**: `grep -n "Qwen2_5Omni" ai_services/omni/app/main.py` returns empty; health response includes `"backend"` field.

---

## Phase 6: User Story 4 — Zero Regression (Priority: P4)

**Goal**: All previously passing tests continue to pass. No endpoint paths, response shapes, or user-facing behaviour changed.

**Independent Test**: `python3 -m pytest backend/tests/ --ignore=backend/tests/integration --override-ini="addopts=" -v` passes the same tests that passed in the T001 baseline.

### Implementation for User Story 4

- [X] T014 [US4] Update `backend/tests/test_omni_service.py`: replace `QwenOmniHttpService` → `GenericVoiceHttpService` and `OmniServiceUnavailableError` → `VoiceServiceUnavailableError` in all imports and test function bodies
- [X] T015 [US4] Run full backend test suite and confirm zero regressions: `python3 -m pytest backend/tests/ --ignore=backend/tests/integration --override-ini="addopts=" -v`; the 2 pre-existing failures (`test_settings_defaults`, `test_openai_compatible_generate_response`) may still fail — all others must pass

**Checkpoint**: Test suite result matches T001 baseline — same pass/fail count.

---

## Phase 7: Polish & Validation

**Purpose**: Run quickstart.md validation scenarios to confirm all spec requirements are met.

- [X] T016 [P] Run Scenario 1 from quickstart.md: `grep -rn "OMNI_\|QwenOmni\|OmniServiceUnavailable" backend/src/ docker-compose.yml .env.example` — must return zero matches
- [X] T017 [P] Run Scenario 2 from quickstart.md: confirm `GenericVoiceHttpService` appears only in `omni_service.py` (definition) and `voice_factory.py` (instantiation), not in `main.py`
- [X] T018 [P] Run Scenario 4 from quickstart.md: `VOICE_ENABLED=true VOICE_PROVIDER=invalid_provider python3 -c "from backend.src.config import Settings; from backend.src.infrastructure.voice_factory import create_voice_service; s = Settings(); create_voice_service(s)"` — must raise `ValueError` naming `"invalid_provider"`
- [X] T019 [P] Run Scenario 6 from quickstart.md: `grep -n "VOICE_MODEL_BACKEND\|_BACKENDS\|QwenBackend\|GemmaBackend" ai_services/omni/app/main.py` — all four terms must appear

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — baseline only
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 (renamed fields must exist before factory uses them)
- **US2 (Phase 4)**: Depends on Phase 3 (factory must exist to validate its extensibility)
- **US3 (Phase 5)**: Depends on Phase 2 (can run in parallel with US1/US2 once config is renamed)
- **US4 (Phase 6)**: Depends on Phase 3 (class names renamed in T003 affect test imports)
- **Polish (Phase 7)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2)
- **US2 (P2)**: Depends on US1 (validates the factory created in US1)
- **US3 (P3)**: Depends on Foundational (Phase 2) — can run in parallel with US1
- **US4 (P4)**: Depends on US1 (class rename in T003 affects test file)

### Within Each Phase

- T002 (config) before T006 (factory reads config) and T007 (main.py reads config)
- T003 (class rename) before T006 (factory imports renamed class) and T014 (tests import renamed class)
- T006 (factory created) before T007 (main.py imports factory)
- T009/T010 (backends ABC) before T011/T012 (concrete backends implement ABC)
- T011/T012 (concrete backends) before T013 (main.py imports backends)

### Parallel Opportunities

- T004 and T005 (docker-compose + .env.example) can run in parallel with each other
- T009, T010, T011, T012 (backend files in ai_services) can run in parallel once T003 is done
- T016, T017, T018, T019 (validation scenarios) can all run in parallel

---

## Parallel Example: Phase 5 (US3)

```bash
# After T010 (base.py) is done, launch in parallel:
Task T011: "Create QwenBackend in ai_services/omni/app/backends/qwen.py"
Task T012: "Create GemmaBackend stub in ai_services/omni/app/backends/gemma.py"
# Then T013 depends on both T011 and T012 completing
```

---

## Implementation Strategy

### MVP (US1 Only — Phases 1–3)

1. Complete Phase 1: Baseline snapshot
2. Complete Phase 2: Config + class renames (foundation)
3. Complete Phase 3: Factory + main.py wired up
4. **STOP and VALIDATE**: Backend starts; factory rejects invalid provider; `grep` confirms no OMNI_* in source

### Full Delivery (All Stories)

1. MVP (above)
2. Phase 4: Confirm extensibility (no new implementation, validation only)
3. Phase 5: External server backend extraction
4. Phase 6: Test suite update + regression check
5. Phase 7: Quickstart validation scenarios

---

## Notes

- This is a **pure refactoring** — no domain changes, no API changes, no frontend changes
- The 2 pre-existing test failures (`test_settings_defaults`, `test_openai_compatible_generate_response`) are not caused by this feature; they existed before and remain acceptable
- `backend/tests/test_omni_use_case.py` requires **no changes** — it already mocks the `OmniVoiceService` interface, not the concrete class
- `backend/src/domain/` and `backend/src/application/` require **no changes**
- All frontend components require **no changes**
- All public API endpoint paths require **no changes**
