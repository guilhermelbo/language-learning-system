# Implementation Plan: LLM Response Architecture Refactoring

*Feature*: [See spec.md](spec.md)
*Branch*: 1-llm-response-architecture
*Created*: 2026-01-25

---

## Technical Context

### Current State

The application uses a three-tier architecture with the following LLM response flow:

```
LLM Service (Ollama) → Use Case → API Endpoint → Frontend
```

**Current Issues Identified:**

1. **LLM Service** (`backend/src/infrastructure/llm_service.py`):
   - System prompt mixes content generation with JSON formatting requirements
   - LLM must generate valid JSON array with specific structure
   - Format compliance is fragile and prompt-dependent

2. **Use Cases** (`backend/src/application/use_cases.py`):
   - Duplicated JSON parsing logic in `ProcessUserSpeechUseCase` (lines 48-87) and `ProcessUserTextUseCase` (lines 167-206)
   - Inline error handling with hardcoded fallback messages
   - Segments are parsed but only joined text is returned to API
   - No separation between extraction, validation, and transformation

3. **API Layer** (`backend/src/main.py`):
   - `TextResponse` model only includes flattened `ai_text`, not structured segments
   - Segment data (language codes, individual texts) is lost

4. **Frontend** (`frontend/app/page.tsx`, `frontend/components/ChatInterface.tsx`):
   - `Message` interface only has `content: string`
   - No support for displaying bilingual segments
   - All responses rendered as simple text

### Target State

```
LLM Service → Content Extractor → Domain Response → Transformer → API Response → Frontend
     ↓              ↓                   ↓              ↓               ↓
  Raw text    Parse & validate    TextSegment[]    Format for API   Bilingual UI
```

**New Architecture Layers:**

1. **Domain Layer** - Pure entities representing LLM responses
2. **Content Extraction** - Parse raw LLM output to domain entities
3. **Transformation** - Convert domain entities to API/UI formats
4. **Presentation** - Display structured bilingual content

### Technology Stack

| Layer | Technology | Files |
|-------|------------|-------|
| Backend Domain | Python dataclasses | `backend/src/domain/` |
| Backend Application | Python services | `backend/src/application/` |
| Backend Infrastructure | FastAPI, Pydantic | `backend/src/main.py`, `backend/src/infrastructure/` |
| Frontend | Next.js 14, React, TypeScript | `frontend/app/`, `frontend/components/` |

### Dependencies

- Existing: `ollama`, `pydantic`, `fastapi`, Next.js
- No new dependencies required

### Unknowns / NEEDS CLARIFICATION

None. All design decisions are covered by the specification and constitution.

---

## Constitution Check

### Principles Evaluated

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| Clean Architecture | MUST separate layers | ✅ PASS | New extraction and transformation layers |
| Domain-Driven Design | MUST keep logic in domain | ✅ PASS | TextSegment and AssistantResponse in domain |
| Single Responsibility | MUST single responsibility | ✅ PASS | Extractor extracts, Transformer transforms |
| Testability | SHOULD test in isolation | ✅ PASS | All new services are stateless and mockable |
| API First | SHOULD clean APIs | ✅ PASS | New structured response contract |
| Error Handling | MUST graceful errors | ✅ PASS | Fallback responses for malformed LLM output |
| Security | MUST protect data | ✅ PASS | No security changes required |

### Compliance Status

**All MUST principles: PASS**
**All SHOULD principles: PASS**

### Justifications

No deviations from constitution required.

---

## Architecture

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Domain entity immutability | Frozen dataclasses | Prevents accidental mutation, aligns with DDD |
| Extractor pattern | Function-based service | Stateless, easy to test, simple |
| Transformer pattern | Protocol-based interface | Allows multiple implementations, extensible |
| API versioning | Additive changes only | Backward compatible with existing frontend |
| Frontend segments | Optional field | Graceful degradation if backend changes first |

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 BACKEND                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────────┐     │
│  │ LLM Service │───▶│ Content Extractor │───▶│ Domain: AssistantResponse│     │
│  │  (Ollama)   │    │    (NEW)         │    │   TextSegment[]         │     │
│  └─────────────┘    └──────────────────┘    └────────────┬────────────┘     │
│                                                           │                  │
│                     ┌──────────────────┐                  │                  │
│                     │   Transformer    │◀─────────────────┘                  │
│                     │  (API Format)    │                                     │
│                     └────────┬─────────┘                                     │
│                              │                                               │
│  ┌───────────────────────────▼───────────────────────────────────────────┐  │
│  │                        Use Cases                                       │  │
│  │  ProcessUserSpeechUseCase / ProcessUserTextUseCase                    │  │
│  │  - Calls LLM, Extractor, Transformer                                  │  │
│  │  - Orchestrates TTS with segments                                     │  │
│  └───────────────────────────┬───────────────────────────────────────────┘  │
│                              │                                               │
│  ┌───────────────────────────▼───────────────────────────────────────────┐  │
│  │                      API Endpoints                                     │  │
│  │  /conversation/speech, /conversation/text                             │  │
│  │  Returns: StructuredTextResponse (with segments)                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                          page.tsx                                      │   │
│  │  - Receives StructuredTextResponse                                    │   │
│  │  - Passes segments to ChatInterface                                   │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                      │                                        │
│                                      ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                     ChatInterface.tsx (UPDATED)                        │   │
│  │  - Renders bilingual segments when available                          │   │
│  │  - Falls back to simple content display                               │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Request Flow:**
```
User Input → API → Use Case → LLM Service → Raw String
                                    ↓
                            Content Extractor
                                    ↓
                       AssistantResponse (Domain)
                                    ↓
                            Transformer
                                    ↓
                       StructuredTextResponse (API)
                                    ↓
                         Frontend (Bilingual UI)
```

**Domain Entity Structure:**
```python
@dataclass(frozen=True)
class TextSegment:
    text: str
    language: str  # "pt" or "en"
    order: int

@dataclass(frozen=True)
class AssistantResponse:
    segments: tuple[TextSegment, ...]
    raw_content: str  # Original LLM output for debugging
```

**API Response Structure:**
```python
class SegmentDTO(BaseModel):
    text: str
    lang: str

class StructuredTextResponse(BaseModel):
    user_text: str
    ai_text: str  # Combined text (backward compatible)
    segments: list[SegmentDTO]  # Structured bilingual data
    conversation_id: str
    audio_base64: Optional[str] = None
    user_audio_base64: Optional[str] = None
```

---

## Implementation Phases

### Phase 1: Domain Foundation

**Goal**: Create domain entities for LLM responses

**Files to Create:**
- `backend/src/domain/response_entities.py`

**Tasks:**
1. Create `TextSegment` dataclass (frozen, immutable)
2. Create `AssistantResponse` dataclass with segment collection
3. Add factory method for creating fallback responses
4. Add unit tests for domain entities

**Acceptance:**
- Entities are immutable
- Factory methods work correctly
- No dependencies on infrastructure

### Phase 2: Content Extraction Layer

**Goal**: Create service to parse raw LLM output into domain entities

**Files to Create:**
- `backend/src/application/response_extractor.py`
- `backend/tests/test_response_extractor.py`

**Tasks:**
1. Create `extract_response(raw_llm_output: str) -> AssistantResponse` function
2. Handle markdown code block removal
3. Handle JSON parsing with multiple fallback strategies
4. Handle wrapped responses (dict with `data`, `segments`, etc.)
5. Handle single object vs array responses
6. Return fallback response on parse failure (log error)
7. Write comprehensive unit tests with various LLM output formats

**Acceptance:**
- All existing LLM output variations are handled
- Parse failures return valid fallback response
- 100% test coverage on extractor logic

### Phase 3: Response Transformation

**Goal**: Create transformer to convert domain responses to API format

**Files to Create:**
- `backend/src/application/response_transformer.py`
- `backend/tests/test_response_transformer.py`

**Tasks:**
1. Create `ResponseTransformer` protocol/interface
2. Create `APIResponseTransformer` implementation
3. Transform `AssistantResponse` to `StructuredTextResponse` data
4. Preserve segment order and language codes
5. Generate combined `ai_text` from segments
6. Write unit tests

**Acceptance:**
- Transformer is independent of extraction logic
- New transformers can be added without modifying existing code

### Phase 4: API Contract Update

**Goal**: Update API to return structured responses

**Files to Modify:**
- `backend/src/main.py`

**Tasks:**
1. Create `SegmentDTO` Pydantic model
2. Update `TextResponse` to `StructuredTextResponse` (additive)
3. Add `segments` field to response
4. Maintain backward compatibility (ai_text still present)

**Acceptance:**
- Existing frontend continues to work
- New `segments` field is available

### Phase 5: Use Case Refactoring

**Goal**: Replace inline parsing with extractor and transformer

**Files to Modify:**
- `backend/src/application/use_cases.py`

**Tasks:**
1. Inject extractor and transformer into use cases
2. Remove duplicated JSON parsing code from both use cases
3. Use extractor to get `AssistantResponse`
4. Use transformer to get API response data
5. Pass segments to TTS (instead of re-parsing)
6. Update return values to include segments

**Acceptance:**
- No duplicated parsing logic
- Use cases orchestrate services, don't contain business logic
- TTS receives segments directly

### Phase 6: LLM Prompt Simplification

**Goal**: Simplify LLM prompt to focus on content, not format

**Files to Modify:**
- `backend/src/infrastructure/llm_service.py`

**Tasks:**
1. Update system prompt to focus on bilingual content generation
2. Remove strict JSON formatting requirements
3. Keep minimal structure guidance (semantic, not syntactic)
4. Test with live LLM to ensure quality responses

**Acceptance:**
- LLM generates quality bilingual content
- Extractor handles new output format
- No regression in response quality

### Phase 7: Frontend Update

**Goal**: Display bilingual content in chat interface

**Files to Modify:**
- `frontend/app/page.tsx`
- `frontend/components/ChatInterface.tsx`

**Files to Create:**
- `frontend/components/BilingualMessage.tsx`

**Tasks:**
1. Update `Message` interface to include optional `segments` array
2. Create `BilingualMessage` component for structured display
3. Update `ChatInterface` to use `BilingualMessage` for assistant messages
4. Implement fallback to simple text if no segments
5. Style bilingual display (PT and EN clearly distinguished)
6. Test responsive layout

**Acceptance:**
- Bilingual content displays correctly
- Graceful fallback when segments unavailable
- Responsive design works

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM output becomes inconsistent after prompt change | Medium | High | Extensive testing with real LLM, rollback plan |
| Breaking change to API | Low | High | Additive changes only, backward compatible |
| Frontend-backend sync issues | Medium | Medium | Deploy backend first, frontend gracefully handles missing segments |
| Performance regression | Low | Medium | Transformation is O(n) on segments, minimal overhead |

### Mitigation Strategies

1. **Incremental Deployment**: Deploy backend changes before frontend
2. **Feature Flag**: Can disable segments in response if issues arise
3. **Logging**: Add comprehensive logging in extractor for debugging
4. **Rollback**: Each phase can be reverted independently

---

## Testing Strategy

### Unit Tests

| Component | Test Cases |
|-----------|------------|
| `TextSegment` | Creation, immutability, equality |
| `AssistantResponse` | Creation with segments, combined text generation |
| `ContentExtractor` | Valid JSON, markdown wrapped, nested objects, arrays, single objects, empty, malformed |
| `ResponseTransformer` | Domain to DTO conversion, segment preservation |

### Integration Tests

| Flow | Test Cases |
|------|------------|
| LLM → Extractor | Real LLM output parsing |
| Use Case E2E | Full flow with mocked LLM |
| API Response | Correct structure in HTTP response |

### End-to-End Tests

| Scenario | Test Cases |
|----------|------------|
| Speech Flow | Record → Process → Display bilingual |
| Text Flow | Type → Process → Display bilingual |
| Error Flow | Malformed LLM → Fallback display |
| Backward Compat | Old frontend with new backend |

---

## File Summary

### New Files

| Path | Purpose |
|------|---------|
| `backend/src/domain/response_entities.py` | Domain entities |
| `backend/src/application/response_extractor.py` | LLM output parsing |
| `backend/src/application/response_transformer.py` | Domain to DTO conversion |
| `backend/tests/test_response_extractor.py` | Extractor tests |
| `backend/tests/test_response_transformer.py` | Transformer tests |
| `frontend/components/BilingualMessage.tsx` | Bilingual display component |

### Modified Files

| Path | Changes |
|------|---------|
| `backend/src/main.py` | New response models, segments in response |
| `backend/src/application/use_cases.py` | Use extractor/transformer, remove duplication |
| `backend/src/infrastructure/llm_service.py` | Simplified prompt |
| `frontend/app/page.tsx` | Handle segments in response |
| `frontend/components/ChatInterface.tsx` | Use BilingualMessage |

---

## Estimated Complexity

| Phase | Complexity | LOC (est.) |
|-------|------------|------------|
| Phase 1: Domain | Low | ~50 |
| Phase 2: Extractor | Medium | ~100 |
| Phase 3: Transformer | Low | ~50 |
| Phase 4: API Contract | Low | ~30 |
| Phase 5: Use Cases | Medium | ~100 (refactor) |
| Phase 6: LLM Prompt | Low | ~20 |
| Phase 7: Frontend | Medium | ~150 |
| **Total** | | **~500 LOC** |
