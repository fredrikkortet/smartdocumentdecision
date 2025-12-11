from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str


class LLMBackend:
    """
    Abstract interface for any LLM backend.

    This base exposes both `chat` and `generate` to accomodate
    differing client APIs. Implementations SHOULD implement `chat`.
    If a backend provides `generate`, it should behave like `chat`.
    """

    def chat(self, prompt: str) -> str:
        raise NotImplementedError

    def generate(self, prompt: str) -> str:
        # default to chat for backward compatibility
        return self.chat(prompt)
