# Implementation Plan: Professional Language Tutor System Prompt

**Branch**: `006-tutor-prompt-improvement` | **Date**: 2026-06-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-tutor-prompt-improvement/spec.md`

---

## Summary

Replace the minimal 10-line `SYSTEM_PROMPT` constant in `backend/src/infrastructure/llm_service.py` with a structured, pedagogically-rich prompt that transforms the LLM from a simple translator into a professional language tutor. The prompt implements Communicative Language Teaching (CLT) with explicit grammar instruction, CEFR-adaptive complexity, structured vocabulary teaching loops, grammar correction protocol, and session continuity through in-context references. The existing JSON array output contract (`[{"text": ..., "lang": ...}]`) is preserved unchanged.

---

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: FastAPI, OpenAI Python SDK (async), Ollama client (optional lazy import)

**Storage**: N/A — prompt is a string constant; no persistence layer involved

**Testing**: pytest (`backend/tests/test_llm_config.py`)

**Target Platform**: Linux server (Docker container, Python 3.10 slim)

**Project Type**: Web service (backend API)

**Performance Goals**: Prompt token count should stay under 1000 tokens to avoid excessive latency in real-time voice interaction

**Constraints**: Output format must remain strict JSON array (Constitutional Principle V). `/no_think` prefix must be preserved as the first line.

**Scale/Scope**: Single-file change — one constant in one file, one test assertion update

---

## Constitution Check

*GATE: Must pass before implementation. Re-check after design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Docker-First Deployment | ✅ PASS | No deployment changes; string constant update only |
| II. LLM Independence | ✅ PASS | Prompt is model-agnostic text; env-var configuration unchanged |
| III. Clean Architecture + DDD | ✅ PASS | `SYSTEM_PROMPT` lives in `infrastructure/` — correct layer |
| IV. Type Safety & Async I/O | ✅ PASS | No function signatures changed |
| V. JSON Contract Compliance | ✅ PASS | New prompt reinforces and explains the JSON contract more explicitly |
| VI. Testing Discipline | ✅ PASS | Existing test updated; new behavioral assertions added |

No violations. Complexity Tracking section not required.

---

## Project Structure

### Documentation (this feature)

```text
specs/006-tutor-prompt-improvement/
├── spec.md                              # Feature specification
├── plan.md                              # This file
├── research.md                          # Pedagogical framework decisions (Phase 0)
├── data-model.md                        # Prompt section structure (Phase 1)
├── quickstart.md                        # Manual validation scenarios (Phase 1)
├── contracts/
│   └── tutor-output-contract.md         # JSON output contract with usage patterns (Phase 1)
├── checklists/
│   └── requirements.md                  # Spec quality checklist
└── tasks.md                             # Task breakdown (Phase 2 — /speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── infrastructure/
│       └── llm_service.py               # SYSTEM_PROMPT constant → content replaced
└── tests/
    └── test_llm_config.py               # test_system_prompt_injected → assertion updated
```

**Structure Decision**: Single-file change in the infrastructure layer. Matches Clean Architecture (Constitutional Principle III). No new files in source tree.

---

## Implementation Steps

### Step 1 — Draft the New SYSTEM_PROMPT

Replace the content of `SYSTEM_PROMPT` in `backend/src/infrastructure/llm_service.py` (lines 11-28) with a structured multi-section prompt. The prompt must follow the section order defined in `data-model.md`:

```
/no_think
[Role Declaration]
[Output Format Constraint]
[Teaching Protocol]
[Grammar Correction Rules]
[Level Adaptation]
[JSON Segment Strategy]
[Session Continuity]
[Tone and Boundaries]
```

See `data-model.md` for the invariants each section must satisfy and `contracts/tutor-output-contract.md` for usage pattern examples to embed in the prompt.

**Key content requirements**:
- Role: "You are a professional, patient, and encouraging bilingual language tutor for Portuguese (Brazilian) and English learners."
- Every vocabulary introduction ends with a practice invitation (FR-003, FR-004)
- Grammar corrections follow: recast → name error → explain rule → practice (FR-002)
- CEFR default B1, infer up/down from student messages (FR-005)
- Portuguese segments for immersion, English segments for explanations (FR-007)
- Reference prior conversation turns when relevant (FR-008)
- Warm, encouraging tone; redirect off-topic gracefully (FR-009, FR-010)
- Define mini-lesson structure inline: intro → examples → practice → feedback (FR-011)

### Step 2 — Update the Test Assertion

In `backend/tests/test_llm_config.py`, function `test_system_prompt_injected` (line 201), update the assertion to match the new prompt's actual content markers:

**Current assertion** (line 209):
```python
assert "JSON" in messages[0]["content"]
```

This assertion remains valid as-is since the new prompt still references JSON. However, add a more meaningful assertion to verify the pedagogical content is present:

```python
assert "JSON" in messages[0]["content"]
assert "tutor" in messages[0]["content"].lower()  # role declaration present
```

### Step 3 — Add Behavioral Prompt Tests

Add a new test in `backend/tests/test_llm_config.py` to verify the prompt contains all required pedagogical sections:

```python
def test_system_prompt_pedagogical_content():
    from src.infrastructure.llm_service import SYSTEM_PROMPT
    prompt_lower = SYSTEM_PROMPT.lower()
    
    # Role declaration
    assert "tutor" in prompt_lower
    # Output format
    assert "json" in prompt_lower
    assert '"lang"' in SYSTEM_PROMPT
    # Teaching protocol
    assert "example" in prompt_lower or "exemplo" in prompt_lower
    # Grammar correction
    assert "correct" in prompt_lower or "correction" in prompt_lower
    # Level adaptation
    assert any(level in SYSTEM_PROMPT for level in ["A1", "A2", "B1", "B2", "C1", "C2", "CEFR"])
    # Tone
    assert "encourage" in prompt_lower or "patient" in prompt_lower
```

### Step 4 — Manual Validation

Run through the 7 scenarios defined in `quickstart.md` with the running backend to confirm behavioral quality. Pay particular attention to Scenarios 2 (grammar correction) and 3/4 (level adaptation) as these are the most impactful quality gates.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Model ignores complex prompt instructions | Medium | Keep instructions imperative and numbered; test with multiple prompt-input pairs |
| Token count exceeds model's comfort zone for voice latency | Low | Target <1000 tokens; measure with `tiktoken` or equivalent |
| `/no_think` prefix breaks on non-Qwen3 models | Low | Already present in current prompt; behavior unchanged |
| JSON format failures increase with more complex prompt | Low | Existing `format="json"` parameter in Ollama call enforces JSON; parser fallback handles edge cases |
| `test_system_prompt_injected` fails after content change | Very low | Update assertion in Step 2 before running tests |

---

## Complexity Tracking

> No constitution violations. This section is empty per governance rules.
