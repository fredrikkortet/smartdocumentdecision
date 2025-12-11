try:
    import ollama

    OLLAMA_AVAILABLE = True
except Exception:
    ollama = None
    OLLAMA_AVAILABLE = False

from ai.backend.llm_base import LLMBackend


class OllamaBackend(LLMBackend):
    def __init__(self, model: str = "gemma3"):
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama SDK not installed; install `ollama` or use another backend.")
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
