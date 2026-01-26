# Quickstart: LLM Response Architecture Implementation

*Branch*: 1-llm-response-architecture
*Created*: 2026-01-25

---

## Overview

This guide provides step-by-step instructions for implementing the LLM response architecture refactoring.

## Prerequisites

- Python 3.10+ with FastAPI backend running
- Node.js 18+ with Next.js frontend running
- Ollama with Mistral model available
- Existing codebase on branch `1-llm-response-architecture`

---

## Phase 1: Domain Entities

### Create Response Entities

**File**: `backend/src/domain/response_entities.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class TextSegment:
    """Represents a piece of text in a specific language."""
    text: str
    language: str
    order: int

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("text cannot be empty")
        if self.order < 0:
            raise ValueError("order must be non-negative")

@dataclass(frozen=True)
class AssistantResponse:
    """Represents a complete AI assistant response."""
    segments: tuple[TextSegment, ...]
    raw_content: str
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def combined_text(self) -> str:
        return " ".join(seg.text for seg in self.segments)

    @property
    def portuguese_text(self) -> str:
        return " ".join(seg.text for seg in self.segments if seg.language == "pt")

    @property
    def english_text(self) -> str:
        return " ".join(seg.text for seg in self.segments if seg.language == "en")

    @classmethod
    def fallback(cls, message: str, language: str = "pt") -> "AssistantResponse":
        segment = TextSegment(text=message, language=language, order=0)
        return cls(segments=(segment,), raw_content=message)
```

### Verify

```bash
cd backend
python -c "from src.domain.response_entities import TextSegment, AssistantResponse; print('OK')"
```

---

## Phase 2: Content Extractor

### Create Response Extractor

**File**: `backend/src/application/response_extractor.py`

```python
import json
import re
import logging
from typing import Optional
from ..domain.response_entities import TextSegment, AssistantResponse

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE_PT = "Desculpe, não consegui gerar uma resposta para isso."
FALLBACK_MESSAGE_EN = "Sorry, I couldn't generate a response for that."

def extract_response(raw_llm_output: str) -> AssistantResponse:
    """
    Extract structured response from raw LLM output.

    Handles various LLM output formats:
    - Clean JSON array
    - Markdown-wrapped JSON
    - Single object
    - Wrapped objects (e.g., {"data": [...]})
    - Plain text fallback
    """
    if not raw_llm_output or not raw_llm_output.strip():
        logger.warning("Empty LLM output, returning fallback")
        return AssistantResponse.fallback(FALLBACK_MESSAGE_PT)

    try:
        # Step 1: Clean markdown code blocks
        cleaned = _remove_markdown_blocks(raw_llm_output)

        # Step 2: Parse JSON
        parsed = json.loads(cleaned)

        # Step 3: Normalize to list
        segments_data = _normalize_to_list(parsed)

        # Step 4: Create domain entities
        segments = _create_segments(segments_data)

        if not segments:
            logger.warning("No valid segments extracted, returning fallback")
            return AssistantResponse.fallback(FALLBACK_MESSAGE_PT)

        return AssistantResponse(
            segments=tuple(segments),
            raw_content=raw_llm_output
        )

    except Exception as e:
        logger.error(f"Failed to parse LLM output: {e}. Raw: {raw_llm_output[:200]}")
        # Use raw output as fallback if it has content
        if raw_llm_output.strip():
            return AssistantResponse.fallback(raw_llm_output.strip())
        return AssistantResponse.fallback(FALLBACK_MESSAGE_PT)

def _remove_markdown_blocks(text: str) -> str:
    """Remove markdown code block markers."""
    return re.sub(r'```(?:json)?', '', text).strip()

def _normalize_to_list(parsed) -> list:
    """Normalize parsed JSON to a list of segment dictionaries."""
    if isinstance(parsed, list):
        return parsed

    if isinstance(parsed, dict):
        # Check for common wrapping keys
        for key in ['data', 'segments', 'items', 'response']:
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        # Single object, wrap in list
        return [parsed]

    raise ValueError(f"Unexpected JSON structure: {type(parsed)}")

def _create_segments(segments_data: list) -> list[TextSegment]:
    """Create TextSegment instances from segment dictionaries."""
    segments = []
    for i, seg in enumerate(segments_data):
        text = seg.get("text", "").strip()
        lang = seg.get("lang", "pt")

        if not text:
            continue

        segments.append(TextSegment(text=text, language=lang, order=i))

    return segments
```

### Verify

```bash
python -c "
from src.application.response_extractor import extract_response
result = extract_response('[{\"text\": \"Olá\", \"lang\": \"pt\"}]')
print(f'Segments: {len(result.segments)}, Text: {result.combined_text}')
"
```

---

## Phase 3: Response Transformer

### Create Response Transformer

**File**: `backend/src/application/response_transformer.py`

```python
from ..domain.response_entities import AssistantResponse

def transform_to_api_response(response: AssistantResponse) -> dict:
    """
    Transform domain AssistantResponse to API response format.

    Returns a dictionary ready for API serialization.
    """
    segments = [
        {"text": seg.text, "lang": seg.language}
        for seg in response.segments
    ]

    return {
        "ai_text": response.combined_text,
        "segments": segments
    }
```

---

## Phase 4: API Contract Update

### Update main.py

Add new models and update response:

```python
# Add to imports section
from .application.response_extractor import extract_response
from .application.response_transformer import transform_to_api_response

# Add new Pydantic models
class SegmentDTO(BaseModel):
    text: str
    lang: str

class StructuredTextResponse(BaseModel):
    user_text: str
    ai_text: str
    segments: list[SegmentDTO]
    conversation_id: str
    audio_base64: Optional[str] = None
    user_audio_base64: Optional[str] = None
```

---

## Phase 5: Use Case Refactoring

### Update ProcessUserSpeechUseCase

Replace inline JSON parsing with extractor/transformer:

```python
# In execute() method, after LLM call:

from ..application.response_extractor import extract_response
from ..application.response_transformer import transform_to_api_response

# Replace the try/except JSON parsing block with:
response = extract_response(raw_response)
transformed = transform_to_api_response(response)
ai_text = transformed["ai_text"]
segments = transformed["segments"]

# Use segments for TTS
for seg in segments:
    # ... TTS synthesis
```

---

## Phase 6: Frontend Update

### Update Message Interface

**File**: `frontend/app/page.tsx`

```typescript
interface Segment {
  text: string;
  lang: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  id: string;
  segments?: Segment[];
}
```

### Create BilingualMessage Component

**File**: `frontend/components/BilingualMessage.tsx`

```typescript
"use client";

import React from 'react';

interface Segment {
  text: string;
  lang: string;
}

interface BilingualMessageProps {
  segments: Segment[];
}

export const BilingualMessage: React.FC<BilingualMessageProps> = ({ segments }) => {
  const ptSegments = segments.filter(s => s.lang === 'pt');
  const enSegments = segments.filter(s => s.lang === 'en');

  return (
    <div className="space-y-2">
      {ptSegments.length > 0 && (
        <div className="bg-blue-500/10 rounded-lg p-3">
          <span className="text-xs text-blue-400 font-medium">🇧🇷 Português</span>
          <p className="text-gray-100 mt-1">
            {ptSegments.map(s => s.text).join(' ')}
          </p>
        </div>
      )}
      {enSegments.length > 0 && (
        <div className="bg-green-500/10 rounded-lg p-3">
          <span className="text-xs text-green-400 font-medium">🇬🇧 English</span>
          <p className="text-gray-100 mt-1">
            {enSegments.map(s => s.text).join(' ')}
          </p>
        </div>
      )}
    </div>
  );
};
```

---

## Testing

### Run Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Run Frontend

```bash
cd frontend
npm run dev
```

### Manual Testing

1. Send a text message in Portuguese
2. Verify response shows both Portuguese and English sections
3. Verify audio plays correctly
4. Test with malformed input (should show fallback)

---

## Rollback

If issues arise, revert to previous behavior:

1. In use cases, restore inline JSON parsing
2. In main.py, use `TextResponse` instead of `StructuredTextResponse`
3. In frontend, ignore `segments` field

---

## Success Criteria Checklist

- [ ] Domain entities created and tested
- [ ] Extractor handles all LLM output variations
- [ ] Transformer produces correct API format
- [ ] API returns `segments` field
- [ ] Frontend displays bilingual content
- [ ] Fallback works for malformed responses
- [ ] All existing functionality preserved
