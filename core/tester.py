import re
import time
from pathlib import Path
import yaml
from .llm import ClaudeClient

class TestRunner:
    def __init__(self, bot_system_prompt_path: str):
        self.bot_system = Path(bot_system_prompt_path).read_text(encoding="utf-8")
        self.llm = ClaudeClient()

    def run_plan(self, plan_path: str) -> dict:
        plan = yaml.safe_load(Path(plan_path).read_text(encoding="utf-8"))
        steps = plan.get("steps", [])
        results = {"plan": plan.get("name"), "cases": [], "failed": 0, "passed": 0}
        history = []
        t0 = time.time()
        for i, step in enumerate(steps, 1):
            # эмулируем ответ бота, используя его же системный промпт
            reply = self.llm.chat(system=self.bot_system, messages=[{"role": "user", "content": step["user"]}])
            ok = True
            pat = step.get("expect_regex")
            if pat:
                ok = re.search(pat, reply, flags=re.IGNORECASE) is not None
            results["cases"].append({
                "idx": i,
                "user": step["user"],
                "reply": reply,
                "expect": pat,
                "ok": ok,
            })
            results["passed" if ok else "failed"] += 1
            history.append({"user": step["user"], "assistant": reply})
        results["elapsed_sec"] = round(time.time() - t0, 2)
        return results
