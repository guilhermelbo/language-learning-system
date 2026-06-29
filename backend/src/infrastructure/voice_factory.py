from ..config import Settings
from ..domain.interfaces import OmniVoiceService
from .omni_service import GenericVoiceHttpService


def create_voice_service(settings: Settings) -> OmniVoiceService:
    """Instantiate the correct voice backend from settings.

    VOICE_PROVIDER=generic → GenericVoiceHttpService (self-hosted voice server)
    """
    provider = settings.voice_provider.lower()

    if provider == "generic":
        return GenericVoiceHttpService(
            api_url=settings.voice_api_url,
            timeout=settings.voice_timeout_seconds,
        )

    raise ValueError(
        f"Unknown VOICE_PROVIDER '{settings.voice_provider}'. "
        "Supported values: 'generic'."
    )
