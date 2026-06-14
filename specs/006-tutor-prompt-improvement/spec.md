# Feature Specification: Professional Language Tutor System Prompt

**Feature Branch**: `006-tutor-prompt-improvement`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "quero melhorar muito o system prompt do tutor de linguas para que ele realmente guie e ensine o aluno de forma profissional"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Guided Vocabulary and Phrase Introduction (Priority: P1)

A student asks to learn a new word or phrase in Portuguese. The tutor does not simply translate — it teaches the word in context, explains usage, gives an example sentence, and invites the student to practice by creating their own sentence.

**Why this priority**: This is the core learning loop. Without active teaching and guided practice, the tutor is just a translator. P1 because it defines the product's value.

**Independent Test**: Send "Como digo 'forgiveness' em português?" and verify that the tutor (a) provides the word with pronunciation guidance, (b) places it in an example sentence, (c) explains a nuance or common usage mistake, and (d) prompts the student to try using the word themselves.

**Acceptance Scenarios**:

1. **Given** a student asks for a word translation, **When** the tutor responds, **Then** the response includes the translation AND an example sentence AND an invitation to practice.
2. **Given** a student asks for a phrase, **When** the tutor responds, **Then** the response demonstrates the phrase in two different contexts and explains the register (formal vs. informal).
3. **Given** the tutor has just taught a new word, **When** the student replies, **Then** the tutor evaluates the student's attempt and gives specific constructive feedback.

---

### User Story 2 - Real-Time Grammar Correction with Explanation (Priority: P1)

A student makes a grammatical mistake during conversation. The tutor acknowledges the student's intent, gently corrects the error, explains the underlying rule, and continues the conversation naturally without making the student feel discouraged.

**Why this priority**: Grammar correction with explanation is the distinguishing mark of professional tutoring. Equally P1 as vocabulary introduction.

**Independent Test**: Send a message with a deliberate grammar mistake (e.g., wrong verb conjugation, wrong gender agreement) and verify the tutor: (a) rephrases the correct version, (b) identifies the specific rule violated, (c) provides a brief explanation, (d) continues the conversational flow.

**Acceptance Scenarios**:

1. **Given** a student writes with incorrect verb conjugation, **When** the tutor responds, **Then** the response contains the corrected form highlighted and a one-sentence rule explanation.
2. **Given** a student writes with incorrect noun gender agreement, **When** the tutor responds, **Then** the tutor explains the gender rule and offers two more example words that follow the same pattern.
3. **Given** a student repeats the same mistake twice in a session, **When** the tutor responds the second time, **Then** the tutor explicitly notes the pattern ("Notei que essa é uma dificuldade recorrente...") and provides a mini-drill (2-3 quick practice items).

---

### User Story 3 - Adaptive Level Assessment and Progression (Priority: P2)

At the start of a session (or when the tutor detects a mismatch), the tutor assesses the student's proficiency level from the conversation and adjusts vocabulary complexity, grammar corrections depth, and pace accordingly.

**Why this priority**: Without adaptation, the tutor treats a beginner the same as an advanced student, failing both. P2 because the core teaching loop must exist first.

**Independent Test**: Begin two separate sessions — one with very simple messages and one with complex messages — and verify that the tutor's vocabulary and grammar explanations are noticeably simpler/more complex in each case.

**Acceptance Scenarios**:

1. **Given** a student sends only simple sentences for the first 3 turns, **When** the tutor responds, **Then** the tutor uses vocabulary within A2-B1 CEFR range and provides fuller sentence scaffolding.
2. **Given** a student demonstrates B2+ proficiency through complex sentences, **When** the tutor responds, **Then** the tutor introduces idiomatic expressions and discusses nuanced grammatical distinctions.
3. **Given** a student explicitly states their level ("Sou iniciante"), **When** the tutor acknowledges it, **Then** all subsequent responses adjust phrasing complexity and correction depth to match.

---

### User Story 4 - Structured Mini-Lesson Delivery (Priority: P2)

The student requests a mini-lesson on a specific topic (e.g., "teach me the past tense in Portuguese"). The tutor delivers a structured, progressive lesson: introduction → examples → student practice → feedback.

**Why this priority**: Structured lessons address intentional study, complementing conversational practice.

**Independent Test**: Ask "Pode me ensinar o pretérito perfeito?" and verify the tutor delivers a 4-phase lesson: concept introduction → 2 example sentences → student practice prompt → feedback loop.

**Acceptance Scenarios**:

1. **Given** a student requests a grammar topic lesson, **When** the tutor responds, **Then** the response opens with a clear concept statement, followed by two illustrative examples, and ends with a practice invitation.
2. **Given** the student attempts the practice, **When** the tutor evaluates it, **Then** the tutor provides specific feedback and a follow-up challenge one complexity level higher.
3. **Given** a student asks for vocabulary by theme (e.g., "palavras sobre alimentação"), **When** the tutor responds, **Then** it introduces 4-6 words with usage examples and a memory tip.

---

### User Story 5 - Session Continuity and Progress Acknowledgment (Priority: P3)

Within a single conversation session, the tutor remembers vocabulary and grammar topics already covered and references them in later turns, reinforcing learning through spaced repetition cues.

**Why this priority**: Reinforcement and continuity distinguish a tutor from a chatbot, but it depends on P1/P2 stories being in place.

**Independent Test**: In a multi-turn session, teach a word in turn 3, then in turn 7 use that same word and verify the tutor references it ("Lembra quando aprendemos essa palavra?").

**Acceptance Scenarios**:

1. **Given** a word was taught earlier in the session, **When** the tutor uses it again, **Then** the tutor explicitly ties it to the earlier teaching moment.
2. **Given** a grammar rule was corrected earlier, **When** a similar structure arises, **Then** the tutor proactively applies the rule as a reminder before the student makes the mistake.

---

### Edge Cases

- What happens when the student sends a completely off-topic message (e.g., asking for a recipe)? Tutor should gently redirect to language learning goals while being helpful.
- How does the tutor handle a student who consistently avoids speaking in the target language? It should encourage with increasing specificity.
- What if the student asks for help in a language other than English or Portuguese? Tutor acknowledges the limitation and stays within its configured language pair.
- What if the LLM produces a response that contains grammar explanations too long to fit naturally in the bilingual JSON format? The explanation must still be split into appropriately sized `text`/`lang` segments within the JSON array.
- What if the student writes nothing meaningful (e.g., "ok", "hmm")? Tutor uses it as an opportunity to introduce a new teaching moment rather than producing a trivial response.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system prompt MUST instruct the LLM to act as a professional, encouraging language tutor who guides students through structured learning — not merely as a translator or question-answering assistant.
- **FR-002**: The system prompt MUST include explicit instructions for grammar correction: acknowledge the intent, provide the correction, name the rule, and continue the conversation.
- **FR-003**: The system prompt MUST instruct the tutor to introduce new vocabulary in context with at least one example sentence per new word/phrase taught.
- **FR-004**: The system prompt MUST direct the tutor to invite the student to practice after every teaching moment (example production, fill-in-the-blank, or question-and-answer).
- **FR-005**: The system prompt MUST include a proficiency adaptation directive — the tutor adjusts vocabulary complexity and explanation depth based on signals from the student's messages.
- **FR-006**: The system prompt MUST preserve the existing output format constraint: all output is a strict JSON array where each element has `text` (string) and `lang` (either `"pt"` or `"en"`) fields, with no markdown or plain text outside the JSON.
- **FR-007**: The system prompt MUST guide the tutor to use both languages strategically: Portuguese for immersive practice, English for explanations when clarity requires it.
- **FR-008**: The system prompt MUST instruct the tutor to reference previously covered content within the session when contextually appropriate (reinforcement).
- **FR-009**: The system prompt MUST define the tutor's tone: warm, encouraging, never condescending, patient with mistakes, and professionally structured.
- **FR-010**: The system prompt MUST include a directive to redirect off-topic conversations back to language learning in a friendly, engaging manner.
- **FR-011**: The system prompt MUST define structured mini-lesson format: introduction → examples → student practice prompt → feedback, usable on demand.
- **FR-012**: The system prompt MUST include specific CEFR-level indicators so the tutor can calibrate complexity (A1-A2 beginner, B1-B2 intermediate, C1-C2 advanced).

### Key Entities

- **System Prompt**: The text instruction set passed to the LLM as the `system` role message. This is the sole output of this feature — no new code entities are created, only the content of the existing `SYSTEM_PROMPT` constant is replaced.
- **Teaching Moment**: Any tutor response that introduces new language content (vocabulary, grammar, idiom) paired with an example and a practice invitation.
- **Correction Event**: A tutor response that identifies and explains a student error, triggered when the student's message contains grammatical or lexical mistakes.
- **Mini-Lesson**: A structured 4-phase pedagogical sequence (concept → examples → practice → feedback) delivered within one or more conversation turns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a session of 5 or more turns, 90% of tutor responses that respond to a student error include both a correction and a rule explanation, verifiable by manual review of conversation logs.
- **SC-002**: 100% of tutor responses that introduce new vocabulary also include an example sentence in context and end with an invitation to practice.
- **SC-003**: The tutor's language complexity visibly adjusts within 3 turns of a student demonstrating a consistent proficiency level (manual A/B comparison between beginner and advanced seed messages).
- **SC-004**: 95% of tutor responses maintain valid JSON array format with `text` and `lang` fields, as measured by automated JSON parsing in existing tests.
- **SC-005**: In a structured mini-lesson scenario, the tutor delivers all 4 phases (introduction, examples, practice prompt, feedback) within a 3-turn exchange.
- **SC-006**: Users who interact with the improved tutor for 10+ minutes report feeling guided and taught (not just answered), as measured by subjective evaluation with at least 3 test users.

## Assumptions

- The existing bilingual JSON output format (`[{"text": "...", "lang": "pt"}, {"text": "...", "lang": "en"}]`) is preserved — this is constitutionally mandated and cannot be relaxed.
- The language pair is fixed to Portuguese (Brazilian variety assumed) and English for v1; expansion to other language pairs is out of scope.
- The system prompt is a single static string passed per session; there is no per-user profile storage or database for cross-session learning tracking.
- The tutor will rely on in-context conversation history (the messages array) for within-session continuity; no external memory store is required for this feature.
- The LLM model in use is capable of following complex multi-instruction prompts reliably (assumed given the project's existing model configuration).
- The `/no_think` prefix used in the current prompt for Qwen3-style models is preserved in the implementation if needed — this spec concerns only the pedagogical content, not the model-specific flags.
- The improved prompt may be longer than the current one; any token budget concern is an implementation decision and does not constrain this specification.
