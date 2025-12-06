import ollama
from ai.backend.llm_base import LLMBackend


class OllamaBackend(LLMBackend):
    def __init__(self, model: str = "gemma3"):
        self.model = model

    def chat(self, prompt: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]

    def generate(self, prompt: str) -> str:
        client = ollama.Client()
        response = client.generate(
            model=self.model,
            prompt=prompt,
        )
        return response["response"]
