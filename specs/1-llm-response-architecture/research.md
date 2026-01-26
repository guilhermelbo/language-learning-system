# Research Document: LLM Response Architecture

*Created*: 2026-01-25
*Branch*: 1-llm-response-architecture

---

## Research Summary

This document captures research findings and design decisions made during the planning phase.

---

## R1: LLM Output Parsing Strategies

### Decision
Use a multi-strategy parser that attempts formats in order of likelihood.

### Rationale
LLMs may produce varied output formats even with the same prompt. A robust parser handles:
1. Clean JSON array (expected format)
2. Markdown-wrapped JSON (```json blocks)
3. Single object instead of array
4. Wrapped objects (e.g., `{"data": [...]}`)
5. Plain text fallback

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Strict JSON validation | Simpler code | Frequent failures with LLM variations |
| LLM retry on failure | Better output | Increased latency, cost |
| Structured output (Ollama format=json) | Guaranteed JSON | Already using, still produces variations |

### Implementation Notes
- Use `json.loads()` with try/catch
- Strip markdown code fences before parsing
- Check for wrapping keys: `data`, `segments`, `items`, `response`
- Wrap single objects in array
- Log parse failures for monitoring

---

## R2: Domain Entity Immutability

### Decision
Use Python `@dataclass(frozen=True)` for domain entities.

### Rationale
Immutable entities:
- Prevent accidental mutation during processing
- Are thread-safe for concurrent requests
- Align with functional programming principles
- Make debugging easier (state doesn't change)

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Regular dataclasses | Easier to modify | Risk of mutation bugs |
| Pydantic models | Validation built-in | Mixes domain with infrastructure |
| Named tuples | Very immutable | Less readable, no methods |

### Implementation Notes
- Use `tuple` instead of `list` for collections (immutable)
- Provide factory methods for creating instances
- Domain entities have no dependencies on Pydantic or serialization

---

## R3: Transformer Pattern

### Decision
Use a simple function-based transformer (not class-based).

### Rationale
For this feature:
- Only one transformer needed (API format)
- No complex state to maintain
- Function is easier to test and reason about

If multiple transformers are needed later, can introduce a Protocol.

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Abstract class + implementations | Clear extension point | Over-engineering for single use case |
| Protocol interface | Type-safe extensibility | Adds complexity |
| Simple function | Minimal, testable | May need refactor if more formats added |

### Implementation Notes
- Start with function: `transform_to_api_response(response: AssistantResponse) -> dict`
- Can introduce Protocol later if needed
- Keep transformer logic separate from extraction

---

## R4: API Backward Compatibility

### Decision
Use additive changes only. Keep existing fields, add new `segments` field.

### Rationale
- Frontend may not be updated simultaneously
- Existing integrations (if any) continue to work
- Gradual migration path

### API Response Evolution

**Before:**
```json
{
  "user_text": "...",
  "ai_text": "combined text here",
  "conversation_id": "...",
  "audio_base64": "..."
}
```

**After (additive):**
```json
{
  "user_text": "...",
  "ai_text": "combined text here",
  "segments": [
    {"text": "Portuguese text", "lang": "pt"},
    {"text": "English text", "lang": "en"}
  ],
  "conversation_id": "...",
  "audio_base64": "..."
}
```

### Implementation Notes
- `segments` is a new optional field
- `ai_text` remains as combined text
- Frontend checks for `segments` and falls back to `ai_text`

---

## R5: Frontend Bilingual Display

### Decision
Create a dedicated `BilingualMessage` component with clear visual separation.

### Rationale
- Single responsibility: one component for bilingual display
- Reusable across different message types
- Clear visual hierarchy between languages

### Design Approach

```
┌─────────────────────────────────────┐
│  Tutor IA                          │
│  ┌─────────────────────────────┐   │
│  │ 🇧🇷 Portuguese text here   │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 🇬🇧 English text here      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Side-by-side columns | Compact | Poor on mobile |
| Tabs | Clean, saves space | Extra click needed |
| Stacked with visual separation | Clear, mobile-friendly | Takes more vertical space |

### Implementation Notes
- Use subtle background colors to distinguish languages
- Add small flag icons or language labels
- Ensure accessibility (sufficient contrast)
- Graceful fallback to simple text display

---

## R6: LLM Prompt Strategy

### Decision
Simplify prompt to focus on content quality, with minimal format guidance.

### Current Prompt (problematic)
```
Valid JSON Output is MANDATORY.
Root element must be a JSON ARRAY.
[{"text": "...", "lang": "pt"}, {"text": "...", "lang": "en"}]
Do not output any markdown or conversational text outside the JSON.
```

### New Prompt (content-focused)
```
You are a bilingual language tutor helping users learn English from Portuguese.

When responding:
- Provide your response in both Portuguese and English
- First give the Portuguese version, then the English version
- Keep responses natural and conversational

Respond as a helpful, encouraging tutor.
```

### Rationale
- LLM generates better content when not constrained by format
- Parser handles extraction of languages from natural output
- Reduced prompt complexity improves response quality

### Implementation Notes
- Extractor must handle more varied output formats
- May need NLP-based language detection as fallback
- Monitor response quality after change

---

## Open Items

None. All research questions have been resolved.

---

## References

- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html)
- [Ollama API documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/)
