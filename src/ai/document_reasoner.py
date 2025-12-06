import json
import re
from ai.prompts.document_prompts import combine_chunks_prompt
from ai.context_loader import ContextLoader


class DocumentReasoner:
    def __init__(self, ai_client, context_path="context.md"):
        self.ai_client = ai_client
        self.context_loader = ContextLoader(context_path)

    def combine(self, chunk_results):
        chunk_summaries = [c.summary for c in chunk_results]
        chunk_key_info = [c.key_info for c in chunk_results]

        context_notes = self.context_loader.load()

        prompt = combine_chunks_prompt(
            chunk_summaries="\n\n".join(chunk_summaries),
            chunk_key_info=json.dumps(chunk_key_info, indent=2),
            context_notes=context_notes,
        )

        llm_output = self.ai_client.generate(prompt)
        llm_output = self.safe_parse_llm_output(llm_output)

        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return {"summary": llm_output, "insights": [], "uncertainties": [], "confidence": 0.3}

    def decide_need_full_read(self, combined_result):
        # summary = combined_result.get("summary", "")
        uncertainties = combined_result.get("uncertainties", [])
        insights = combined_result.get("insights", [])
        confidence = combined_result.get("confidence", 0.5)

        # Basic rule-based logic
        reasons = []

        if len(uncertainties) > 0:
            reasons.append("Document contains uncertainties.")
        if confidence < 0.4:
            reasons.append("Low AI confidence.")
        if len(insights) < 3:
            reasons.append("Not enough insights extracted.")

        need_full_read = len(reasons) > 0

        return {"need_full_read": need_full_read, "reasons": reasons}

    def safe_parse_llm_output(self, text):
        # 0. Remove ```json ... ``` wrappers if present
        cleaned = re.sub(r"```json\s*|\s*```", "", text, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        return  cleaned
