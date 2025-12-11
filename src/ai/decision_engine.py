class DecisionEngine:
    def __init__(self, context_rules=None):
        """
        context_rules: output of context.md parser
        Example:
        {
            "priority_topics": [...],
            "ignore_topics": [...],
            "sensitivity": 0.7
        }
        """
        self.context = context_rules or {}

    def combine_responses(self, chunk_summaries, metadata):
        """
        chunk_summaries: list of dicts from the LLM
        metadata: basic file metadata (size, type, OCR-used, etc.)

        Return combined document-level semantic info.
        """
        return {
            "combined_topics": self._collect_topics(chunk_summaries),
            "combined_summary": self._combine_text(chunk_summaries),
            "metadata": metadata,
        }

    def compute_read_worthiness(self, combined):
        """Produces a score 0.0–1.0 indicating how valuable the document is.

        Implementation notes:
        - If any priority topics are present, increase score.
        - Use sensitivity from context to boost or dampen the effective score.
        - For the simple heuristic: base score = fraction of topics that match priority_topics.
        """
        """
        Produces a score 0.0–1.0 indicating how valuable the document is.

        You will refine the scoring algorithm later.
        """
        topics = combined["combined_topics"]
        sensitivity = self.context.get("sensitivity", 0.5)

        score = 0.0

        # If there are no topics identified, default to a low score
        if not topics:
            base = 0.0
        else:
            # compute fraction of topics that are priority topics
            priority = [x.lower() for x in self.context.get("priority_topics", [])]
            ignored = [x.lower() for x in self.context.get("ignore_topics", [])]
            match_count = sum(1 for t in topics if t.lower() in priority)
            base = match_count / max(1, len(topics))

        # Use sensitivity to increase weight of matched topics
        score = base * (0.5 + sensitivity)

        # Reduce score if ignored topics present
        for t in topics:
            if t.lower() in ignored:
                score -= 0.3

        # Clamp
        score = max(0.0, min(score, 1.0))
        return score

    def compute_confidence(self, chunk_summaries, metadata):
        """
        Quick confidence estimation.
        """
        confidence = 1.0

        if metadata.get("ocr_used"):
            confidence -= 0.2  # OCR lowers confidence

        if len(chunk_summaries) < 2:
            confidence -= 0.1  # small docs less reliable

        return max(0.0, min(confidence, 1.0))

    def final_recommendation(self, score):
        if score > 0.65:
            return "Full Read Recommended"
        if score > 0.30:
            return "Key Info Enough"
        return "Not Relevant"

    # ---------------------------
    # Internals
    # ---------------------------

    def _collect_topics(self, summaries):
        topics = []
        for s in summaries:
            topics.extend(s.get("topics", []))
        return list(set(topics))

    def _combine_text(self, summaries):
        return "\n".join(s.get("summary", "") for s in summaries)
