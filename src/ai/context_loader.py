import os


class ContextLoader:
    def __init__(self, path="context.md"):
        self.path = path

    def load(self):
        """Return the content of context.md if it exists, else empty string."""
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""
