import anthropic

from ai_pc.config import Settings


def make_client(settings: Settings) -> anthropic.Anthropic:
    if settings.anthropic_api_key:
        return anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return anthropic.Anthropic()
