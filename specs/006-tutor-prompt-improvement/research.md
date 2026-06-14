# Research: Professional Language Tutor System Prompt

**Feature**: 006-tutor-prompt-improvement
**Date**: 2026-06-14

---

## Decision 1: Pedagogical Framework

**Decision**: Communicative Language Teaching (CLT) with explicit grammar instruction

**Rationale**: CLT is the dominant evidence-based approach for conversational language tutoring. It prioritizes meaning-focused interaction while still allowing metalinguistic (grammar-rule) explanations when students make errors. This balances natural conversation with the explicit teaching moments the spec requires (FR-001 through FR-004).

**Alternatives considered**:
- Pure grammar-translation: rejected — produces translators, not communicators
- Total immersion (Portuguese-only): rejected — the bilingual JSON format is a constitutional requirement that presupposes English explanations for clarity
- Silent Way / Suggestopedia: too complex to encode in a single LLM prompt

---

## Decision 2: Error Correction Strategy

**Decision**: Recasting + explicit correction + metalinguistic feedback in sequence

**Rationale**: Research (Lyster & Ranta, 1997; Ellis 2009) shows that recasting alone has low noticeability by learners. For an automated tutor, the more effective approach is:
1. **Recast** (model the correct form naturally in the response)
2. **Explicit correction** (name the error and the correct form)
3. **Metalinguistic feedback** (briefly name the rule — e.g., "ser vs. estar: permanent vs. temporary states")

This is encodable in the JSON array by using English segments for rules and Portuguese segments for practice.

**Alternatives considered**:
- Recasting only: insufficient noticeability in text/voice
- Prompting only (asking the student to self-correct): valuable but needs to be secondary strategy

---

## Decision 3: Proficiency Level Inference

**Decision**: CEFR-based heuristic inference from vocabulary and sentence complexity

**Rationale**: The tutor cannot ask users to fill out a form or take a test in this voice-based system. It must infer level from signals in the conversation. CEFR (A1→C2) is the industry-standard framework. The prompt will instruct the LLM to:
- Start at B1 (intermediate) by default
- Downgrade to A1/A2 if the student uses only simple phrases or asks for very basic help
- Upgrade to B2/C1 if the student writes complex, idiomatic sentences

**Alternatives considered**:
- Asking the student their level explicitly at the first turn: viable but feels robotic in voice context — relegated to a secondary option ("you can also tell me your level")
- Fixed level: rejected — fails all learners outside that fixed level

---

## Decision 4: JSON Array Usage for Pedagogy

**Decision**: Use the multi-segment JSON array to separate language domains within a single tutor turn

**Rationale**: The existing JSON format `[{"text": "...", "lang": "pt"}, {"text": "...", "lang": "en"}]` is constitutionally required. Rather than fighting this constraint, the new system prompt weaponizes it:
- Portuguese segments: immersive practice, model sentences, conversation continuation
- English segments: grammar rule explanations, vocabulary notes, practice invitations

This allows the TTS pipeline to speak Portuguese naturally for immersion and switch to English for explanation — a natural pattern used by human bilingual tutors.

**Alternatives considered**:
- Mixing English and Portuguese within a single segment: rejected — breaks TTS lang selection
- Using only Portuguese for everything: rejected — reduces clarity of explanations for learners who need English support

---

## Decision 5: Session Continuity Without External Memory

**Decision**: Rely on in-context conversation history; prompt the LLM to reference prior turns explicitly

**Rationale**: The spec's Assumptions section confirms there is no database or cross-session memory store. The LLM's context window (messages array) is the only memory available. The system prompt will instruct the tutor to actively review earlier messages in the conversation and reference them explicitly. This is feasible because modern LLMs handle long context well, and conversations are typically 10-30 turns.

**Alternatives considered**:
- External memory store: out of scope for this feature
- Summarization agent: overkill for typical session length

---

## Decision 6: Prompt Length and Token Budget

**Decision**: Accept a longer prompt (~500–800 tokens) without token-count constraints

**Rationale**: The spec's Assumptions section explicitly states "the improved prompt may be longer; any token budget concern is an implementation decision." The current models configured (Qwen3, Mistral) handle prompts of this size without issues. Pedagogical richness is prioritized over brevity here.

**Alternatives considered**:
- Short prompt with few examples: produces inconsistent behavior — rejected
- External instruction file loaded at runtime: over-engineering for a single constant

---

## Decision 7: `/no_think` Prefix Handling

**Decision**: Preserve `/no_think` as the first line of the prompt; treat it as an implementation detail outside the spec's scope

**Rationale**: The `/no_think` prefix is a Qwen3/llama.cpp model-specific token that disables chain-of-thought reasoning. It reduces latency in real-time voice interaction. The spec explicitly states it is preserved. The new pedagogical content comes after this line.

---

## Summary of Prompt Architecture

The new system prompt will be structured in this order:
1. `/no_think` (model-specific, preserved)
2. **Role declaration** — professional bilingual tutor identity
3. **Output format constraint** — JSON array with text/lang (mandatory)
4. **Teaching principles** — CLT framework, vocabulary-in-context, practice invitations
5. **Grammar correction protocol** — recast → name error → explain rule → practice
6. **Level adaptation** — CEFR inference rules
7. **JSON segment strategy** — Portuguese for immersion, English for explanation
8. **Session continuity** — reference prior turns when relevant
9. **Tone and boundaries** — warm, encouraging, redirect off-topic gracefully
