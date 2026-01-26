"""
Domain entities for LLM response handling.

These entities represent the structured response from the LLM,
independent of serialization or infrastructure concerns.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class TextSegment:
    """
    Represents a piece of text in a specific language.

    Attributes:
        text: The text content
        language: Language code (e.g., "pt", "en")
        order: Position in the response sequence (0-indexed)
    """
    text: str
    language: str
    order: int

    def __post_init__(self):
        """Validate segment data on creation."""
        if not self.text or not self.text.strip():
            raise ValueError("text cannot be empty")
        if self.order < 0:
            raise ValueError("order must be non-negative")


@dataclass(frozen=True)
class AssistantResponse:
    """
    Represents a complete response from the AI assistant.

    Attributes:
        segments: Tuple of text segments (immutable)
        raw_content: Original LLM output for debugging
        created_at: Timestamp when response was created
    """
    segments: tuple[TextSegment, ...]
    raw_content: str
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def combined_text(self) -> str:
        """Combine all segment texts with space separator."""
        return " ".join(seg.text for seg in self.segments)

    @property
    def portuguese_text(self) -> str:
        """Get combined text from Portuguese segments only."""
        return " ".join(seg.text for seg in self.segments if seg.language == "pt")

    @property
    def english_text(self) -> str:
        """Get combined text from English segments only."""
        return " ".join(seg.text for seg in self.segments if seg.language == "en")

    @classmethod
    def fallback(cls, message: str, language: str = "pt") -> "AssistantResponse":
        """
        Create a fallback response when LLM parsing fails.

        Args:
            message: The fallback message text
            language: Language code for the fallback message

        Returns:
            An AssistantResponse with a single segment
        """
        segment = TextSegment(text=message, language=language, order=0)
        return cls(segments=(segment,), raw_content=message)
