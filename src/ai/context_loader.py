import os


class ContextLoader:
    def __init__(self, path="context.md"):
        self.path = path

    def load(self):
        """Return the raw content of context.md as a string.

        This method preserves the existing behavior used by DocumentReasoner
        (for injecting context notes into prompts).
        """
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def load_parsed(self):
        """Parse the context.md contents and return a dictionary of rules.

        Supported keys (examples):
          - sensitivity: high|medium|low or 0.0-1.0
          - focus: comma separated topics -> mapped to priority_topics
          - ignore: comma separated topics -> mapped to ignore_topics
          - custom_priority: comma separated list -> mapped to priority_topics

        The returned dict is suitable to pass into DecisionEngine.
        """
        raw = self.load()
        if not raw:
            return {}

        parsed = {"priority_topics": [], "ignore_topics": [], "raw": raw}
        for ln in raw.splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            if "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            k = k.strip().lower()
            v = v.strip()
            if k == "sensitivity":
                # Accept numeric or descriptive sensitivity
                try:
                    parsed["sensitivity"] = float(v)
                except ValueError:
                    v_lower = v.lower()
                    if v_lower in ("high", "h", "1", "0.8"):
                        parsed["sensitivity"] = 0.8
                    elif v_lower in ("medium", "med", "m"):
                        parsed["sensitivity"] = 0.5
                    elif v_lower in ("low", "l"):
                        parsed["sensitivity"] = 0.3
                    else:
                        parsed["sensitivity"] = 0.5
            elif k in ("focus", "priority", "priority_topics"):
                topics = [t.strip() for t in v.split(",") if t.strip()]
                parsed["priority_topics"].extend(topics)
            elif k in ("ignore", "ignore_topics"):
                topics = [t.strip() for t in v.split(",") if t.strip()]
                parsed["ignore_topics"].extend(topics)
            elif k in ("custom_priority",):
                topics = [t.strip() for t in v.split(",") if t.strip()]
                parsed["priority_topics"].extend(topics)
            else:
                # generic passthrough
                parsed[k] = v

        # normalize unique lists
        parsed["priority_topics"] = list({t for t in parsed.get("priority_topics", [])})
        parsed["ignore_topics"] = list({t for t in parsed.get("ignore_topics", [])})
        # ensure numeric sensitivity
        if "sensitivity" not in parsed:
            parsed["sensitivity"] = 0.5
        return parsed
