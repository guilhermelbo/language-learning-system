from typing import Dict, Optional
from uuid import UUID
from ..domain.entities import Conversation

class InMemoryConversationRepository:
    def __init__(self):
        self._conversations: Dict[UUID, Conversation] = {}

    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    async def save(self, conversation: Conversation):
        self._conversations[conversation.id] = conversation
