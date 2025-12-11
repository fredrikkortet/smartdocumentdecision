# Hugging Face Inference Client backend with graceful absence of transformers.
try:
    from transformers import pipeline
    HF_AVAILABLE = True
except Exception:
    pipeline = None
    HF_AVAILABLE = False

from ai.backend.llm_base import LLMBackend


class HFBackend(LLMBackend):
    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        if not HF_AVAILABLE:
            raise RuntimeError("transformers not installed; HFBackend unavailable")
        self.pipe = pipeline(task="text-generation", model=model_name, max_new_tokens=512)

    def chat(self, prompt: str) -> str:
        output = self.pipe(prompt)[0]["generated_text"]
        return output

    def generate(self, prompt: str) -> str:
        # Provide a generate alias for compatibility with backends that call generate()
        return self.chat(prompt)
