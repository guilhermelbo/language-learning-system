from ..config import Settings
from ..domain.interfaces import OmniVoiceService
from .omni_service import GenericVoiceHttpService
from .llm_voice_service import OpenAICompatibleVoiceService


def create_voice_service(settings: Settings) -> OmniVoiceService:
    """Instantiate the correct voice backend from settings.

    VOICE_PROVIDER=generic           → GenericVoiceHttpService (self-hosted voice server)
    VOICE_PROVIDER=openai_compatible → OpenAICompatibleVoiceService (llamacpp native audio)
    """
    provider = settings.voice_provider.lower()

    if provider == "generic":
        return GenericVoiceHttpService(
            api_url=settings.voice_api_url,
            timeout=settings.voice_timeout_seconds,
        )

    if provider == "openai_compatible":
        return OpenAICompatibleVoiceService(
            base_url=settings.voice_api_url,
            model=settings.voice_model_name,
            api_key=settings.llm_api_key,
            tts_api_url=settings.tts_api_url,
            timeout=settings.voice_timeout_seconds,
        )

    raise ValueError(
        f"Unknown VOICE_PROVIDER '{settings.voice_provider}'. "
        "Supported values: 'generic', 'openai_compatible'."
    )
