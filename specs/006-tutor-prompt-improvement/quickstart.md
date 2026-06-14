# Quickstart Validation Guide: Professional Language Tutor System Prompt

**Feature**: 006-tutor-prompt-improvement
**Date**: 2026-06-14

---

## Prerequisites

- Docker Compose stack running (`docker-compose up --build`)
- Backend accessible at `http://localhost:8000`
- OR: Python environment set up with `pip install -r backend/requirements.txt`

---

## Automated Test Validation

Run the existing test suite to confirm the prompt change doesn't break infrastructure:

```bash
cd backend
pytest tests/test_llm_config.py -v
```

**Expected**: All tests pass, including `test_system_prompt_injected` (which checks for "JSON" in the prompt content — the new prompt still contains this word).

> **Note**: The assertion `assert "JSON" in messages[0]["content"]` in `test_system_prompt_injected` remains valid since the new prompt explicitly references JSON output requirements.

---

## Manual Validation Scenarios

These scenarios validate the pedagogical behavior of the improved prompt. Run them via the text endpoint for repeatability.

### Setup

```bash
# Start the backend (or use the running Docker stack)
cd backend
uvicorn src.main:app --reload
```

Send requests to `POST http://localhost:8000/text` with body:
```json
{"text": "<your message>", "conversation_id": null}
```

---

### Scenario 1: Vocabulary Teaching Loop (FR-001, FR-002, FR-003)

**Turn 1 — Request a word**:
```json
{"text": "How do I say 'forgiveness' in Portuguese?"}
```

**Expected response characteristics**:
- Provides the word "perdão" or "forgiveness → perdão"
- Contains an example sentence in Portuguese using the word
- Ends with an invitation to practice (e.g., "Tente usar a palavra numa frase!")
- Output is valid JSON array with `pt` and `en` segments

**Validation check**:
```python
import json, requests
r = requests.post("http://localhost:8000/text", json={"text": "How do I say 'forgiveness' in Portuguese?"})
data = r.json()
segments = json.loads(data["ai_text"])  # if returned as raw — check actual endpoint shape
# Verify: at least one segment contains "perdão"
# Verify: at least one segment with lang="pt" contains an example sentence
# Verify: at least one segment contains a practice invitation
```

---

### Scenario 2: Grammar Correction (FR-002, FR-004)

**Turn 1 — Make a grammar mistake**:
```json
{"text": "Ontem eu vai ao mercado e compriei muitas coisas."}
```

**Expected response characteristics**:
- Acknowledges what the student meant (communicates understanding)
- Provides corrected form: "Ontem eu fui ao mercado e comprei muitas coisas."
- Names the rule: preterite form of "ir" (fui) and "-ar" verbs in preterite (comprei)
- Offers a follow-up practice item
- Tone is warm and encouraging

---

### Scenario 3: Level Adaptation — Beginner Signals (FR-005)

**Turn 1**:
```json
{"text": "Hello. I want learn Portuguese. I am beginner."}
```

**Expected response characteristics**:
- Tutor uses simple vocabulary in Portuguese segments
- English explanations are comprehensive and foundational
- Does not introduce idiomatic expressions or complex grammar
- Greets the student warmly and introduces a very simple first concept

**Turn 2 (same conversation)**:
```json
{"text": "Como se diz 'I am happy' em português?"}
```

**Expected**: Tutor remains at A1/A2 complexity — provides "Eu estou feliz" with simple explanation of "estar" for emotional states.

---

### Scenario 4: Level Adaptation — Advanced Signals (FR-005)

**Turn 1**:
```json
{"text": "Queria praticar o uso do subjuntivo em orações condicionais hipotéticas. Podemos explorar isso?"}
```

**Expected response characteristics**:
- Tutor recognizes B2/C1 proficiency from the message
- Introduces the subjuntivo directly without explaining basic grammar
- Uses more idiomatic Portuguese in the pt segments
- English explanation is concise and targeted at grammar nuance

---

### Scenario 5: Mini-Lesson (FR-010, FR-011)

**Turn 1**:
```json
{"text": "Can you teach me about ser vs estar?"}
```

**Expected response structure (4-phase lesson)**:
1. **Introduction** — concept statement about ser (permanent) vs estar (temporary)
2. **Examples** — 2 contrasting sentences in Portuguese
3. **Practice prompt** — "Agora complete: 'Ela ___ professora.' (ser ou estar?)"
4. Subsequent turn evaluates the student's answer and gives feedback

---

### Scenario 6: JSON Format Compliance (FR-006, SC-004)

For any of the above scenarios, validate the output JSON:

```python
import json
# Take the raw LLM response from logs or debug endpoint
response = '[{"text": "...", "lang": "pt"}, {"text": "...", "lang": "en"}]'
segments = json.loads(response)
assert isinstance(segments, list), "Root must be array"
for seg in segments:
    assert "text" in seg and "lang" in seg, "Missing required fields"
    assert seg["lang"] in ("pt", "en"), f"Invalid lang: {seg['lang']}"
    assert seg["text"].strip(), "Empty text segment"
print("JSON contract: PASS")
```

---

### Scenario 7: Off-Topic Redirection (Edge Case)

**Turn 1**:
```json
{"text": "What's a good recipe for carbonara?"}
```

**Expected**: Tutor briefly acknowledges, then redirects with something like:
- English: "I'm your Portuguese/English tutor! Let's stick to language learning."
- Portuguese: "Mas posso ensinar como dizer 'massa carbonara' em português! Quer tentar?"

---

## Checklist

After running the scenarios above:

- [ ] All automated tests pass
- [ ] Scenario 1: vocabulary teaching with example + practice invitation ✓
- [ ] Scenario 2: grammar correction with rule + warm tone ✓
- [ ] Scenario 3: beginner adaptation — simpler vocabulary ✓
- [ ] Scenario 4: advanced adaptation — no basic explanations ✓
- [ ] Scenario 5: mini-lesson 4-phase structure ✓
- [ ] Scenario 6: JSON format valid across all responses ✓
- [ ] Scenario 7: off-topic gracefully redirected ✓
