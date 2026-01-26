# Data Model: LLM Response Architecture

*Created*: 2026-01-25
*Branch*: 1-llm-response-architecture

---

## Domain Entities

### TextSegment

Represents a piece of text in a specific language.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | Yes | The text content |
| language | string | Yes | Language code (e.g., "pt", "en") |
| order | int | Yes | Position in the response sequence |

**Invariants:**
- `text` must not be empty (after trimming whitespace)
- `language` must be a valid ISO 639-1 code
- `order` must be >= 0

**Python Definition:**
```python
@dataclass(frozen=True)
class TextSegment:
    text: str
    language: str
    order: int

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("text cannot be empty")
        if self.order < 0:
            raise ValueError("order must be non-negative")
```

---

### AssistantResponse

Represents a complete response from the AI assistant.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| segments | tuple[TextSegment, ...] | Yes | Collection of text segments |
| raw_content | string | Yes | Original LLM output (for debugging) |
| created_at | datetime | Yes | When the response was created |

**Invariants:**
- `segments` must contain at least one segment
- Segments must be ordered by their `order` field

**Computed Properties:**
- `combined_text`: All segment texts joined with space
- `portuguese_text`: Text from segments where language="pt"
- `english_text`: Text from segments where language="en"

**Python Definition:**
```python
@dataclass(frozen=True)
class AssistantResponse:
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
        """Create a fallback response when LLM parsing fails."""
        segment = TextSegment(text=message, language=language, order=0)
        return cls(segments=(segment,), raw_content=message)
```

---

## API Data Transfer Objects (DTOs)

### SegmentDTO

API representation of a text segment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | Yes | The text content |
| lang | string | Yes | Language code (short form) |

**Pydantic Definition:**
```python
class SegmentDTO(BaseModel):
    text: str
    lang: str
```

---

### StructuredTextResponse

API response including structured segment data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_text | string | Yes | User's input text |
| ai_text | string | Yes | Combined AI response text |
| segments | list[SegmentDTO] | Yes | Structured bilingual segments |
| conversation_id | string | Yes | UUID of the conversation |
| audio_base64 | string | No | Base64-encoded AI audio |
| user_audio_base64 | string | No | Base64-encoded user audio |

**Pydantic Definition:**
```python
class StructuredTextResponse(BaseModel):
    user_text: str
    ai_text: str
    segments: list[SegmentDTO]
    conversation_id: str
    audio_base64: Optional[str] = None
    user_audio_base64: Optional[str] = None
```

---

## Frontend Types

### Segment (TypeScript)

```typescript
interface Segment {
  text: string;
  lang: string;
}
```

### Message (TypeScript) - Updated

```typescript
interface Message {
  role: 'user' | 'assistant';
  content: string;
  id: string;
  segments?: Segment[];  // NEW: Optional structured segments
}
```

### APIResponse (TypeScript)

```typescript
interface APIResponse {
  user_text: string;
  ai_text: string;
  segments: Segment[];
  conversation_id: string;
  audio_base64?: string;
  user_audio_base64?: string;
}
```

---

## Entity Relationships

```
┌─────────────────────┐
│  AssistantResponse  │
├─────────────────────┤
│ - raw_content       │
│ - created_at        │
└─────────┬───────────┘
          │ 1
          │
          │ contains
          │
          │ *
┌─────────▼───────────┐
│    TextSegment      │
├─────────────────────┤
│ - text              │
│ - language          │
│ - order             │
└─────────────────────┘
```

---

## Data Flow Transformations

### LLM Output → Domain

```
Raw LLM String
     │
     ▼ (Content Extractor)
     │
AssistantResponse
  └─ TextSegment[]
```

### Domain → API

```
AssistantResponse
     │
     ▼ (Response Transformer)
     │
StructuredTextResponse
  └─ SegmentDTO[]
```

### API → Frontend

```
StructuredTextResponse (JSON)
     │
     ▼ (HTTP Response)
     │
APIResponse (TypeScript)
     │
     ▼ (State Update)
     │
Message (with segments)
```

---

## Validation Rules

| Entity | Field | Rule |
|--------|-------|------|
| TextSegment | text | Non-empty after trim |
| TextSegment | language | Valid ISO 639-1 code |
| TextSegment | order | Non-negative integer |
| AssistantResponse | segments | At least one segment |
| SegmentDTO | text | Non-empty |
| SegmentDTO | lang | Non-empty |

---

## Migration Notes

### Existing Data

No data migration required. This feature only affects runtime response structure.

### Backward Compatibility

- `ai_text` field preserved for old frontend versions
- New `segments` field is additive
- Frontend checks `segments` existence before using
