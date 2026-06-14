# Contract: Tutor LLM Output Format

**Feature**: 006-tutor-prompt-improvement
**Date**: 2026-06-14
**Status**: Unchanged from current implementation — documented here for completeness

---

## Overview

The language tutor LLM must produce responses that conform to a strict JSON contract. This contract is defined by Constitutional Principle V and enforced by the `use_cases.py` parser. The improved system prompt does not change this contract — it teaches the LLM to use the multi-segment format more richly for pedagogical purposes.

---

## Output Schema

```json
[
  {
    "text": "<non-empty string>",
    "lang": "<'pt' | 'en'>"
  }
]
```

### Rules

| Rule | Description |
|------|-------------|
| Root type | Array (`[]`), never an object (`{}`) |
| Minimum length | 1 element |
| `text` | Non-empty string; no markdown formatting; no JSON nested within |
| `lang` | Exactly `"pt"` (Portuguese) or `"en"` (English) — case-sensitive |
| No extra fields | Extra fields are ignored by the parser but should not be added |
| No outer wrapper | No `{"data": [...]}` or similar — bare array only |

---

## Pedagogical Usage Patterns

The improved system prompt introduces consistent patterns for how segments are arranged. These are guidelines, not schema constraints.

### Pattern 1: Vocabulary Teaching Turn

```json
[
  {"text": "A palavra é 'saudade' — um sentimento de nostalgia ou longing.", "lang": "pt"},
  {"text": "Example: 'Tenho saudade de você.' This feeling has no exact English equivalent.", "lang": "en"},
  {"text": "Agora você tenta: Você tem saudade de algo?", "lang": "pt"}
]
```

### Pattern 2: Grammar Correction Turn

```json
[
  {"text": "Quase! A forma correta é: 'Eu fui ao mercado ontem.'", "lang": "pt"},
  {"text": "Rule: 'ir' in the preterite (pretérito perfeito) is irregular — 'eu fui', 'você foi', 'nós fomos'. The stem changes completely.", "lang": "en"},
  {"text": "Tente agora: 'Eles ___ ao parque?' (Use pretérito perfeito de 'ir')", "lang": "pt"}
]
```

### Pattern 3: Conversational Continuation with Level-Adapted Complexity

```json
[
  {"text": "Que ótimo! Você está aprendendo rápido.", "lang": "pt"},
  {"text": "Nice work! Let's try something a bit harder now.", "lang": "en"},
  {"text": "Como você descreveria o seu fim de semana ideal?", "lang": "pt"}
]
```

### Pattern 4: Mini-Lesson Opening Turn

```json
[
  {"text": "Vamos aprender o pretérito perfeito!", "lang": "pt"},
  {"text": "The preterite tense describes completed actions in the past. For regular -AR verbs: eu falei, você falou, nós falamos, eles falaram.", "lang": "en"},
  {"text": "Ouça estes exemplos: 'Eu comi pizza.' 'Ela estudou muito.' Agora, complete: 'Nós ___ (jogar) futebol.'", "lang": "pt"}
]
```

---

## Consumer

The output is consumed by `use_cases.py` in `ProcessUserSpeechUseCase.execute()` and `ProcessUserTextUseCase.execute()`. The parser:

1. Strips `<think>` blocks and markdown fences
2. Parses JSON
3. Handles single-object wrapping (unwraps if `data`/`segments`/`items`/`response` key found)
4. Iterates segments for TTS synthesis, passing `text` and `lang` per segment

No consumer changes are required by this feature.
