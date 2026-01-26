from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from uuid import UUID
from .entities import Message, Conversation

class STTService(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribes audio data to text."""
        pass

class LLMService(ABC):
    @abstractmethod
    async def generate_response(self, conversation_history: list[Message]) -> str:
        """Generates a text response based on conversation history."""
        pass
    
    @abstractmethod
    async def generate_response_stream(self, conversation_history: list[Message]) -> AsyncGenerator[str, None]:
        """Generates a streaming text response."""
        pass

class TTSService(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Synthesizes text to audio bytes."""
        pass
    
    @abstractmethod
    async def synthesize_to_file(self, text: str, output_path: str, lang: str = "pt") -> str:
        """Synthesizes text to an audio file and returns the path."""
        pass

class ConversationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """Retrieves a conversation by its unique ID."""
        pass

    @abstractmethod
    async def save(self, conversation: Conversation):
        """Saves a conversation."""
        pass
