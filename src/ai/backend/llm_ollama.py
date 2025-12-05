import ollama
from ai.backend.llm_base import LLMBackend

class OllamaBackend(LLMBackend):
    def __init__(self, model: str = "mistral"):
        self.model = model
    
    def chat(self, prompt: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["messages"]["content"]
