from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

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
