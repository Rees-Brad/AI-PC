import anthropic


def make_client(api_key: str | None = None) -> anthropic.Anthropic:
    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    return anthropic.Anthropic()
