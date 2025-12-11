from ai.backend.llm_base import LLMBackend


class StubBackend(LLMBackend):
    def __init__(self, responses=None):
        self.responses = responses or {}

    def chat(self, prompt: str) -> str:
        # Return canned response based on simple matching
        for k, v in self.responses.items():
            if k in prompt:
                return v
        # default: echo minimal structured response
        return '{"summary":"Stub summary","insights":["insight1"],"uncertainties":[],"confidence":0.9}'

    def generate(self, prompt: str) -> str:
        return self.chat(prompt)
