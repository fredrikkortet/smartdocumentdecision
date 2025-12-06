from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str


class LLMBackend:
    """
    Abstract intergace fo any LLM backend.
    """

    def chat(self, prompt: str) -> str:
        raise NotImplementedError
