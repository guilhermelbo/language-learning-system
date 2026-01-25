import ollama
import logging
from typing import AsyncGenerator
from ..domain.interfaces import LLMService
from ..domain.entities import Message

logger = logging.getLogger(__name__)

class OllamaLLMService(LLMService):
    def __init__(self, model: str = "mistral"):
        self.model = model
        self.client = ollama.AsyncClient()

    def _convert_history(self, history: list[Message]) -> list[dict]:
        system_prompt = """
        You are a helpful bilingual language tutor (Portuguese/English).
        Valid JSON Output is MANDATORY.
        Root element must be a JSON ARRAY.
        
        Instructions:
        - If the user asks for a phrase, generate a creative one.
        - If the user asks for a translation, provide the translation.
        - If the user asks for the same phrase in both languages, provide two segments.
        
        Output Format:
        [
            {"text": "Portuguese text here", "lang": "pt"},
            {"text": "English text here", "lang": "en"}
        ]
        
        Do not output any markdown or conversational text outside the JSON.
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend([{"role": msg.role, "content": msg.content} for msg in history])
        return messages

    async def generate_response(self, conversation_history: list[Message]) -> str:
        messages = self._convert_history(conversation_history)
        logger.debug(f"Generating response with model {self.model} for {len(messages)} messages")
        response = await self.client.chat(model=self.model, messages=messages, format="json")
        content = response['message']['content']
        logger.debug(f"LLM Response length: {len(content)}")
        return content

    async def generate_response_stream(self, conversation_history: list[Message]) -> AsyncGenerator[str, None]:
        messages = self._convert_history(conversation_history)
        async for part in await self.client.chat(model=self.model, messages=messages, stream=True):
             yield part['message']['content']
