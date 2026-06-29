from typing import Dict, Optional
from uuid import UUID
from ..domain.entities import Conversation, OmniVoiceSession


class InMemoryConversationRepository:
    def __init__(self):
        self._conversations: Dict[UUID, Conversation] = {}

    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    async def save(self, conversation: Conversation):
        self._conversations[conversation.id] = conversation


class InMemoryOmniSessionRepository:
    def __init__(self):
        self._sessions: Dict[UUID, OmniVoiceSession] = {}

    async def get_by_id(self, session_id: UUID) -> Optional[OmniVoiceSession]:
        return self._sessions.get(session_id)

    async def save(self, session: OmniVoiceSession) -> None:
        self._sessions[session.id] = session
