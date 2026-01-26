# Tasks: LLM Response Architecture Refactoring

*Feature*: LLM Response Architecture Refactoring
*Branch*: 1-llm-response-architecture
*Generated*: 2026-01-25

---

## User Story Mapping

| Story ID | User Story | Priority | Functional Requirements |
|----------|------------|----------|------------------------|
| US1 | As a developer, I want response processing to be testable so that I can verify transformations work correctly | P1 | FR-1, FR-2, FR-3 |
| US2 | As a language learner, I want the assistant to respond reliably without format errors so that my learning session is not interrupted | P2 | FR-2, FR-6 |
| US3 | As a language learner, I want to see both the original language and translation clearly displayed so that I can learn vocabulary in context | P3 | FR-4, FR-5 |

---

## Phase 1: Setup

**Goal**: Ensure project structure supports new architecture

- [x] T001 Verify backend test infrastructure exists in `backend/tests/`
- [x] T002 Verify frontend can import new components in `frontend/components/`

---

## Phase 2: Foundational (Domain Layer)

**Goal**: Create domain entities that all user stories depend on

### Domain Entities

- [x] T003 [P] Create `TextSegment` frozen dataclass with text, language, order fields in `backend/src/domain/response_entities.py`
- [x] T004 [P] Add `__post_init__` validation to TextSegment (non-empty text, non-negative order) in `backend/src/domain/response_entities.py`
- [x] T005 Create `AssistantResponse` frozen dataclass with segments tuple and raw_content in `backend/src/domain/response_entities.py`
- [x] T006 Add computed properties (`combined_text`, `portuguese_text`, `english_text`) to AssistantResponse in `backend/src/domain/response_entities.py`
- [x] T007 Add `fallback()` factory method to AssistantResponse for creating error responses in `backend/src/domain/response_entities.py`
- [x] T008 Create unit tests for TextSegment validation in `backend/tests/test_response_entities.py`
- [x] T009 Create unit tests for AssistantResponse computed properties in `backend/tests/test_response_entities.py`

**Acceptance Criteria**:
- Domain entities are immutable (frozen dataclasses)
- Validation raises ValueError for invalid inputs
- All tests pass

---

## Phase 3: US1 - Testable Response Processing

**Goal**: Create extraction and transformation layers that can be unit tested

**Story**: As a developer, I want response processing to be testable so that I can verify transformations work correctly

### Content Extractor (FR-2)

- [x] T010 [US1] Create `extract_response()` function signature accepting raw string, returning AssistantResponse in `backend/src/application/response_extractor.py`
- [x] T011 [US1] Implement markdown code block removal (`\`\`\`json` stripping) in `backend/src/application/response_extractor.py`
- [x] T012 [US1] Implement JSON parsing with try/except handling in `backend/src/application/response_extractor.py`
- [x] T013 [US1] Implement `_normalize_to_list()` helper for handling dict vs array responses in `backend/src/application/response_extractor.py`
- [x] T014 [US1] Implement wrapped object detection (check for `data`, `segments`, `items`, `response` keys) in `backend/src/application/response_extractor.py`
- [x] T015 [US1] Implement `_create_segments()` helper to convert dicts to TextSegment instances in `backend/src/application/response_extractor.py`
- [x] T016 [US1] Implement fallback response creation on parse failure with logging in `backend/src/application/response_extractor.py`
- [x] T017 [P] [US1] Create test for valid JSON array extraction in `backend/tests/test_response_extractor.py`
- [x] T018 [P] [US1] Create test for markdown-wrapped JSON extraction in `backend/tests/test_response_extractor.py`
- [x] T019 [P] [US1] Create test for single object normalization in `backend/tests/test_response_extractor.py`
- [x] T020 [P] [US1] Create test for wrapped object extraction (`{"data": [...]}`) in `backend/tests/test_response_extractor.py`
- [x] T021 [P] [US1] Create test for empty input fallback in `backend/tests/test_response_extractor.py`
- [x] T022 [P] [US1] Create test for malformed JSON fallback in `backend/tests/test_response_extractor.py`

### Response Transformer (FR-3)

- [x] T023 [US1] Create `transform_to_api_response()` function accepting AssistantResponse, returning dict in `backend/src/application/response_transformer.py`
- [x] T024 [US1] Implement segment-to-dict conversion preserving text and language in `backend/src/application/response_transformer.py`
- [x] T025 [US1] Ensure transformer generates `ai_text` from combined segments in `backend/src/application/response_transformer.py`
- [x] T026 [P] [US1] Create test for transformer output structure in `backend/tests/test_response_transformer.py`
- [x] T027 [P] [US1] Create test for segment preservation in transformer in `backend/tests/test_response_transformer.py`

**Independent Test Criteria for US1**:
- All extractor tests pass with mocked LLM outputs
- All transformer tests pass with mocked domain entities
- No external dependencies required for testing

---

## Phase 4: US2 - Reliable Response Processing

**Goal**: Integrate extraction layer into use cases for reliable error-free responses

**Story**: As a language learner, I want the assistant to respond reliably without format errors so that my learning session is not interrupted

### Use Case Integration (FR-2)

- [x] T028 [US2] Import response_extractor and response_transformer in `backend/src/application/use_cases.py`
- [x] T029 [US2] Replace inline JSON parsing in ProcessUserSpeechUseCase with extract_response() call in `backend/src/application/use_cases.py`
- [x] T030 [US2] Replace inline JSON parsing in ProcessUserTextUseCase with extract_response() call in `backend/src/application/use_cases.py`
- [x] T031 [US2] Update use case return dict to include segments from transformer in `backend/src/application/use_cases.py`
- [x] T032 [US2] Remove duplicated `_merge_wavs` method from ProcessUserTextUseCase (keep in ProcessUserSpeechUseCase or extract to shared utility) in `backend/src/application/use_cases.py`
- [x] T033 [US2] Update TTS synthesis loop to use segments directly from AssistantResponse in `backend/src/application/use_cases.py`

### LLM Prompt Simplification (FR-6)

- [x] T034 [US2] Update system prompt to focus on bilingual content generation (remove strict JSON requirements) in `backend/src/infrastructure/llm_service.py`
- [x] T035 [US2] Keep minimal format guidance (Portuguese first, then English) in `backend/src/infrastructure/llm_service.py`
- [x] T036 [US2] Add logging for raw LLM output before extraction in `backend/src/infrastructure/llm_service.py`

**Independent Test Criteria for US2**:
- ProcessUserSpeechUseCase returns valid response with segments
- ProcessUserTextUseCase returns valid response with segments
- Malformed LLM output results in fallback response (not error)
- Backend can run and respond without frontend changes

---

## Phase 5: US3 - Bilingual Display

**Goal**: Update API and frontend to display bilingual content

**Story**: As a language learner, I want to see both the original language and translation clearly displayed so that I can learn vocabulary in context

### API Contract Update (FR-4)

- [x] T037 [US3] Create `SegmentDTO` Pydantic model with text and lang fields in `backend/src/main.py`
- [x] T038 [US3] Create `StructuredTextResponse` model extending TextResponse with segments field in `backend/src/main.py`
- [x] T039 [US3] Update `/conversation/speech` endpoint to return StructuredTextResponse in `backend/src/main.py`
- [x] T040 [US3] Update `/conversation/text` endpoint to return StructuredTextResponse in `backend/src/main.py`
- [x] T041 [US3] Ensure `ai_text` field is preserved for backward compatibility in `backend/src/main.py`

### Frontend Types

- [x] T042 [P] [US3] Create `Segment` TypeScript interface with text and lang fields in `frontend/app/page.tsx`
- [x] T043 [P] [US3] Update `Message` interface to include optional `segments` array in `frontend/app/page.tsx`
- [x] T044 [P] [US3] Create `APIResponse` TypeScript interface matching StructuredTextResponse in `frontend/app/page.tsx`

### Bilingual Message Component (FR-5)

- [x] T045 [US3] Create `BilingualMessage.tsx` component file in `frontend/components/BilingualMessage.tsx`
- [x] T046 [US3] Implement props interface accepting segments array in `frontend/components/BilingualMessage.tsx`
- [x] T047 [US3] Implement Portuguese segment display with 🇧🇷 label and blue background in `frontend/components/BilingualMessage.tsx`
- [x] T048 [US3] Implement English segment display with 🇬🇧 label and green background in `frontend/components/BilingualMessage.tsx`
- [x] T049 [US3] Add responsive layout styling (stacked vertically) in `frontend/components/BilingualMessage.tsx`

### Frontend Integration

- [x] T050 [US3] Import BilingualMessage component in `frontend/components/ChatInterface.tsx`
- [x] T051 [US3] Update ChatInterface to check for segments in assistant messages in `frontend/components/ChatInterface.tsx`
- [x] T052 [US3] Render BilingualMessage for assistant messages with segments in `frontend/components/ChatInterface.tsx`
- [x] T053 [US3] Implement fallback to simple content display when segments unavailable in `frontend/components/ChatInterface.tsx`
- [x] T054 [US3] Update page.tsx to pass segments when adding assistant messages to state in `frontend/app/page.tsx`
- [x] T055 [US3] Update speech response handler to extract segments from API response in `frontend/app/page.tsx`
- [x] T056 [US3] Update text response handler to extract segments from API response in `frontend/app/page.tsx`

**Independent Test Criteria for US3**:
- API returns segments field in response
- Frontend displays bilingual content when segments present
- Frontend falls back to ai_text when segments absent
- Responsive design works on mobile viewport

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Final integration testing and cleanup

- [x] T057 Run full integration test: speech input → bilingual display
- [x] T058 Run full integration test: text input → bilingual display
- [x] T059 Test backward compatibility: old frontend with new backend (ai_text still works)
- [x] T060 Verify error logging captures extraction failures with context
- [x] T061 Remove any commented-out old parsing code from use_cases.py
- [x] T062 Update type hints/docstrings for new functions in `backend/src/application/`

---

## Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Domain) ──────────────────┐
    │                               │
    ▼                               │
Phase 3 (US1: Testable)            │
    │                               │
    ▼                               │
Phase 4 (US2: Reliable) ◄──────────┘
    │
    ▼
Phase 5 (US3: Bilingual)
    │
    ▼
Phase 6 (Polish)
```

**Key Dependencies:**
- US1 depends on: Phase 2 (Domain entities)
- US2 depends on: US1 (Extractor/Transformer must exist)
- US3 depends on: US2 (Use cases must return segments)

---

## Parallel Execution Opportunities

### Within Phase 2 (Domain):
```
T003 + T004 can run in parallel (both create TextSegment)
T008 + T009 can run in parallel (both are tests)
```

### Within Phase 3 (US1):
```
Extractor tests (T017-T022) can all run in parallel
Transformer tests (T026-T027) can run in parallel
```

### Within Phase 5 (US3):
```
Frontend types (T042-T044) can all run in parallel
Backend API (T037-T041) can run in parallel with Frontend types
BilingualMessage (T045-T049) depends on T042 but then can proceed independently
```

---

## Implementation Strategy

### MVP Scope (Recommended)
Complete **Phase 2 + Phase 3 (US1)** first:
- Creates testable extraction and transformation logic
- Enables development of US2 and US3 with confidence
- All tests can run without external services

### Incremental Delivery
1. **Iteration 1**: Domain entities + Extractor tests (T003-T022)
2. **Iteration 2**: Transformer + Use case integration (T023-T036)
3. **Iteration 3**: API contract + Frontend types (T037-T044)
4. **Iteration 4**: BilingualMessage component (T045-T056)
5. **Iteration 5**: Polish and integration testing (T057-T062)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 62 |
| **Phase 1 (Setup)** | 2 tasks |
| **Phase 2 (Domain)** | 7 tasks |
| **Phase 3 (US1)** | 18 tasks |
| **Phase 4 (US2)** | 9 tasks |
| **Phase 5 (US3)** | 20 tasks |
| **Phase 6 (Polish)** | 6 tasks |
| **Parallelizable Tasks** | 16 (marked with [P]) |
| **New Files** | 5 |
| **Modified Files** | 5 |

### Files Created
- `backend/src/domain/response_entities.py`
- `backend/src/application/response_extractor.py`
- `backend/src/application/response_transformer.py`
- `backend/tests/test_response_extractor.py`
- `backend/tests/test_response_transformer.py`
- `frontend/components/BilingualMessage.tsx`

### Files Modified
- `backend/src/main.py`
- `backend/src/application/use_cases.py`
- `backend/src/infrastructure/llm_service.py`
- `frontend/app/page.tsx`
- `frontend/components/ChatInterface.tsx`
