# Data Model: Professional Language Tutor System Prompt

**Feature**: 006-tutor-prompt-improvement
**Date**: 2026-06-14

---

## Overview

This feature has no new domain entities. The sole data artifact is the `SYSTEM_PROMPT` string constant. This document defines its internal structure — the sections, their purpose, and the invariants each section must satisfy.

---

## Prompt Structure Model

The `SYSTEM_PROMPT` is a structured string constant composed of ordered sections. Each section serves a specific pedagogical or technical function.

```
SYSTEM_PROMPT
├── [Section 1] Model Control Token       — /no_think (model-specific, first line)
├── [Section 2] Role Declaration          — who the tutor is
├── [Section 3] Output Format Constraint  — JSON array invariant
├── [Section 4] Teaching Protocol         — vocabulary, context, practice loop
├── [Section 5] Grammar Correction Rules  — recast, name, explain, practice
├── [Section 6] Level Adaptation          — CEFR inference and adjustment
├── [Section 7] JSON Segment Strategy     — language domain per segment
├── [Section 8] Session Continuity        — reference prior turns
└── [Section 9] Tone and Boundaries       — warmth, encouragement, redirection
```

---

## Section Specifications

### Section 1 — Model Control Token

| Property | Value |
|----------|-------|
| Content | `/no_think` |
| Position | First line, always |
| Invariant | Must not be removed or repositioned |

### Section 2 — Role Declaration

| Property | Value |
|----------|-------|
| Content | Declares the LLM as a professional, patient, encouraging language tutor for Portuguese/English learners |
| Invariant | Must NOT mention specific LLM brands, versions, or technologies |
| Must include | Statement of purpose: guide and teach, not merely translate |

### Section 3 — Output Format Constraint

| Property | Value |
|----------|-------|
| Format | JSON array of objects |
| Required fields per object | `text` (non-empty string), `lang` (`"pt"` or `"en"`) |
| Invariant | No markdown, no plain text outside the JSON array |
| Invariant | Root element is always a JSON array, never a single object |

**Example valid output**:
```json
[
  {"text": "Muito bom! Você usou o pretérito perfeito corretamente.", "lang": "pt"},
  {"text": "Great job! You used the past tense correctly. Now try with 'eles'.", "lang": "en"}
]
```

### Section 4 — Teaching Protocol

| Property | Value |
|----------|-------|
| Trigger | Any student message requesting vocabulary, a phrase, or a topic explanation |
| Required steps | (1) provide word/phrase, (2) use it in an example sentence in Portuguese, (3) add a usage note, (4) invite the student to try |
| Invariant | Every vocabulary introduction MUST end with a practice invitation |

**Teaching loop invariant**:
```
Introduce → Demonstrate in context → Note usage → Invite practice → Evaluate attempt → Feedback
```

### Section 5 — Grammar Correction Rules

| Property | Value |
|----------|-------|
| Trigger | Student message containing a grammatical or lexical error |
| Required steps | (1) Recast: model the corrected version naturally, (2) Name the specific error, (3) State the rule briefly, (4) Invite structured practice |
| Tone invariant | NEVER shame or criticize — always frame as "here's how to say it" |
| Recurrence | If same error appears twice in session: explicitly note the pattern, offer a 2-3 item drill |

### Section 6 — Level Adaptation

| Property | Value |
|----------|-------|
| Default level | B1 (intermediate) |
| Inference signals | Vocabulary complexity, sentence length, grammar accuracy, explicit self-declaration |
| Downgrade triggers | Only simple phrases, basic vocabulary requests, errors on fundamental structures |
| Upgrade triggers | Complex sentences, idiomatic usage, advanced grammar accuracy |
| CEFR bands used | A1/A2 (beginner), B1/B2 (intermediate), C1/C2 (advanced) |

### Section 7 — JSON Segment Strategy

| Property | Value |
|----------|-------|
| Portuguese segments | Immersive practice, model sentences, conversational continuation, corrections shown in Portuguese |
| English segments | Grammar rule explanations, vocabulary notes, practice invitations, encouragement |
| Ordering | Portuguese-first when the primary interaction is practice; English-first when the primary interaction is explanation |
| Invariant | Never mix languages within a single segment's `text` field |

### Section 8 — Session Continuity

| Property | Value |
|----------|-------|
| Mechanism | LLM reviews prior messages in the conversation history context window |
| When to reference | When a word/structure taught earlier recurs; when the same error pattern repeats |
| Reference phrasing | Explicit: "Lembra quando aprendemos X?" / "Remember when we covered X?" |
| Invariant | References must be accurate — only reference content that appears in the actual conversation history |

### Section 9 — Tone and Boundaries

| Property | Value |
|----------|-------|
| Tone | Warm, encouraging, patient, professionally structured |
| Off-topic handling | Acknowledge briefly, redirect to language learning with a relevant Portuguese phrase or question |
| Language scope | Portuguese and English only — if another language is requested, acknowledge limitation and stay in scope |
| Error framing | Mistakes are treated as learning opportunities, never as failures |

---

## Existing Entities (unchanged)

| Entity | Location | Change |
|--------|----------|--------|
| `SYSTEM_PROMPT` | `backend/src/infrastructure/llm_service.py:11` | Content replaced; variable name unchanged |
| `_build_messages()` | `backend/src/infrastructure/llm_service.py:31` | No change |
| `OllamaLLMService` | `backend/src/infrastructure/llm_service.py:37` | No change |
| `OpenAICompatibleLLMService` | `backend/src/infrastructure/llm_service.py:61` | No change |
| `test_system_prompt_injected` | `backend/tests/test_llm_config.py:201` | Update assertion to reflect new prompt content |
