from transformers import pipeline
from ai.backend.llm_base import LLMBackend


class HFBackend(LLMBackend):
    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        self.pipe = pipeline(task="text-generation", model=model_name, max_new_tokens=512)

    def chat(self, prompt: str) -> str:
        output = self.pipe(prompt)[0]["generated_text"]
        return output
