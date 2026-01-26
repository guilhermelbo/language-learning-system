# Feature Specification: LLM Response Architecture Refactoring

*Status: Draft*
*Created: 2026-01-25*
*Branch: 1-llm-response-architecture*

---

## Overview

Refactor the LLM response handling system to separate concerns using clean architecture and domain-driven design (DDD) principles. Currently, the LLM prompt mixes content generation responsibilities with output formatting concerns, resulting in inconsistent and fragile responses. This refactoring will establish clear boundaries between content generation, response transformation, and presentation formatting.

## Problem Statement

The current system tightly couples the LLM's content generation with format-specific requirements:

1. **Prompt Overload**: The LLM prompt instructs the model to both generate language learning content AND format it as specific JSON structures, leading to format compliance failures
2. **Duplicated Logic**: Response parsing and transformation code is duplicated across multiple use cases with no shared abstraction
3. **Lost Context**: Language segment information (bilingual text pairs) is discarded when responses are flattened for the frontend
4. **Fragile Error Handling**: JSON parsing failures cascade into user-facing errors rather than being gracefully handled
5. **No Validation Layer**: The system trusts LLM output format without proper validation

## Goals

- Separate LLM content generation from output formatting concerns
- Create a dedicated response transformation layer with clear responsibilities
- Enable rich frontend display of bilingual content (currently lost in transformation)
- Improve system reliability through proper validation and error handling
- Make the response pipeline testable at each layer

## User Stories

### Language Learner

- As a language learner, I want to see both the original language and translation clearly displayed so that I can learn vocabulary in context
- As a language learner, I want the assistant to respond reliably without format errors so that my learning session is not interrupted
- As a language learner, I want responses to load quickly so that conversation feels natural

### Developer

- As a developer, I want to modify response formatting without changing LLM prompts so that I can iterate on the UI independently
- As a developer, I want response processing to be testable so that I can verify transformations work correctly
- As a developer, I want clear error messages when LLM responses are malformed so that I can debug issues quickly

## Functional Requirements

### FR-1: Domain Response Model

**Description**: Create domain entities that represent LLM responses independent of format concerns.

**Acceptance Criteria**:
- [ ] A domain entity exists for representing bilingual text segments (text content + language identifier)
- [ ] A domain entity exists for representing complete assistant responses (collection of segments)
- [ ] Domain entities contain no serialization logic or format-specific code
- [ ] Domain entities are immutable after creation

### FR-2: LLM Content Extraction Service

**Description**: Create a service responsible for extracting content from raw LLM output.

**Acceptance Criteria**:
- [ ] Service accepts raw LLM string output and returns domain response entities
- [ ] Service handles common LLM output variations (markdown wrappers, nested objects, arrays)
- [ ] Service validates extracted content against expected structure
- [ ] Invalid or unparseable responses produce a default fallback response rather than errors
- [ ] Service is stateless and can be unit tested with mock LLM outputs

### FR-3: Response Transformation Layer

**Description**: Create transformation services that convert domain responses to format-specific outputs.

**Acceptance Criteria**:
- [ ] A transformer exists for API response format (structured JSON for frontend consumption)
- [ ] Transformers preserve bilingual segment information for rich display
- [ ] Transformers are independent of domain logic and LLM implementation
- [ ] New output formats can be added without modifying existing code

### FR-4: Frontend Response Contract

**Description**: Define a clear API contract for LLM responses that supports rich content display.

**Acceptance Criteria**:
- [ ] API response includes structured segment data (not just flattened text)
- [ ] Each segment includes text content and language identifier
- [ ] Response includes combined text for simple display scenarios
- [ ] Response structure is documented and versioned

### FR-5: Frontend Bilingual Display

**Description**: Update the frontend to display bilingual content from structured responses.

**Acceptance Criteria**:
- [ ] Chat interface displays both language versions of assistant responses
- [ ] User can visually distinguish between original and translated text
- [ ] Display gracefully falls back to simple text if segment data is unavailable
- [ ] Layout adapts to different response lengths

### FR-6: LLM Prompt Simplification

**Description**: Simplify the LLM system prompt to focus on content generation.

**Acceptance Criteria**:
- [ ] LLM prompt focuses on what to generate (bilingual learning content), not how to format it
- [ ] Format instructions are minimal and focused on semantic structure, not serialization
- [ ] Prompt changes do not break backward compatibility with existing conversations

## Non-Functional Requirements

### Performance

- Response transformation adds less than 50ms to total response time
- Frontend renders structured responses without visible delay compared to current simple text

### Maintainability

- Each layer (LLM service, extraction, transformation, API) can be modified independently
- New response formats can be added by implementing a transformer interface
- All business logic is testable without external service dependencies

### Reliability

- System produces user-friendly responses even when LLM output is malformed
- Transformation failures are logged with context for debugging
- No unhandled exceptions reach the user from response processing

## User Scenarios & Testing

### Scenario 1: Successful Bilingual Response

**Given**: A user sends a message in Portuguese
**When**: The LLM generates a bilingual response
**Then**: The frontend displays both Portuguese and English versions clearly separated

### Scenario 2: Malformed LLM Output

**Given**: The LLM returns output that doesn't match expected structure
**When**: The extraction service processes the response
**Then**: A fallback response is returned and the error is logged without user disruption

### Scenario 3: Simple Text Fallback

**Given**: The API returns response without segment details (backward compatibility)
**When**: The frontend receives the response
**Then**: The combined text is displayed in traditional single-message format

### Scenario 4: Developer Adds New Format

**Given**: A developer needs to add a new output format (e.g., for a mobile app)
**When**: They implement a new transformer
**Then**: The new format is available without modifying extraction or LLM code

## Edge Cases

- LLM returns empty response → System provides default "I couldn't generate a response" message
- LLM returns single language only → System displays available content, logs missing translation
- LLM returns deeply nested structure → Extraction service unwraps to find content
- Network timeout during LLM call → Error handling outside this scope (existing behavior preserved)
- Frontend receives response during audio playback → Display updates without interrupting audio

## Key Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| TextSegment | A piece of text in a specific language | text (string), language (code), order (number) |
| AssistantResponse | Complete response from the assistant | segments (list), timestamp, conversationId |
| TransformationResult | Output of a transformer | format (type), data (format-specific), metadata |

## Success Criteria

- [ ] 100% of assistant responses display bilingual content when available
- [ ] Response processing errors visible to users decrease by 90%
- [ ] New transformer implementations require no changes to existing code
- [ ] All response transformation logic has unit test coverage
- [ ] Frontend displays structured responses within 100ms of receiving API response

## Assumptions

- The existing LLM (Ollama with Mistral) will continue to be used
- Bilingual output (Portuguese/English) remains the primary use case
- The frontend framework (Next.js/React) will not change
- Audio synthesis remains separate from this refactoring (TTS receives text segments)
- Conversation storage mechanism remains in-memory for now

## Dependencies

- Current LLM service must continue functioning during incremental refactoring
- Frontend changes can be deployed independently of backend changes
- No external API changes required

## Out of Scope

- Streaming response support (future enhancement)
- Persistent conversation storage (separate feature)
- Additional language support beyond Portuguese/English
- Audio synthesis optimization
- LLM model changes or fine-tuning
- Authentication or user management
