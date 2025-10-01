import os
from anthropic import Anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))

class ClaudeClient:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])    

    def chat(self, system: str, messages: list[dict]):
        """messages: [{"role":"user"|"assistant", "content": str}]"""
        resp = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
        )
        # Anthropic SDK returns objects; normalize to str
        parts = []
        for block in resp.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts).strip()
