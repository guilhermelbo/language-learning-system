from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4


# ---------------------------------------------------------------------------
# Omni Voice Channel entities
# ---------------------------------------------------------------------------

@dataclass
class PronunciationEvent:
    word: str
    error_type: str  # "vowel" | "consonant" | "stress" | "intonation" | "other"
    user_pronunciation: str
    correct_pronunciation: str
    correction_attempted: bool = False
    correction_succeeded: Optional[bool] = None  # None until drill completes


@dataclass
class OmniVoiceResult:
    """Transient value object returned by OmniVoiceService — not persisted."""
    audio_bytes: bytes
    transcript_user: str
    transcript_assistant: str
    pronunciation_events: List[PronunciationEvent] = field(default_factory=list)


@dataclass
class OmniAudioTurn:
    session_id: UUID
    assistant_audio_bytes: bytes
    transcript_user: str
    transcript_assistant: str
    pronunciation_events: List[PronunciationEvent] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    user_audio_ref: Optional[str] = None


@dataclass
class OmniVoiceSession:
    id: UUID = field(default_factory=uuid4)
    student_id: UUID = field(default_factory=uuid4)
    turns: List[OmniAudioTurn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"
    # drill_state tracks correction attempts per word: word -> attempt_count
    drill_state: dict = field(default_factory=dict)

    def add_turn(self, turn: OmniAudioTurn) -> None:
        self.turns.append(turn)

    @property
    def omni_id(self) -> str:
        """Frontend-safe ID prefixed with 'omni-' to avoid collisions."""
        return f"omni-{self.id}"


# ---------------------------------------------------------------------------
# Standard conversation entities (unchanged)
# ---------------------------------------------------------------------------

@dataclass
class Student:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    native_language: str = "pt-BR"
    target_language: str = "en-US"
    proficiency_level: str = "beginner"
    # Future: vocabulary_dominance, preferences, etc.

@dataclass
class Message:
    content: str
    role: str  # 'user' or 'assistant'
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    audio_path: Optional[str] = None
    
@dataclass
class Conversation:
    id: UUID = field(default_factory=uuid4)
    student_id: UUID = field(default_factory=uuid4)
    messages: List[Message] = field(default_factory=list)
    
    def add_message(self, message: Message):
        self.messages.append(message)
