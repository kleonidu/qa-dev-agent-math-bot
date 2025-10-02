from pathlib import Path
import textwrap
from .llm import ClaudeClient

AGENT_PROMPT = Path("prompts/agent_system.md").read_text(encoding="utf-8")

class SuggestionEngine:
    def __init__(self):
        self.llm = ClaudeClient()

    def build_summary(self, test_report: dict) -> str:
        failed = [c for c in test_report["cases"] if not c["ok"]]
        body = [f"Итоги плана: {test_report['plan']} — passed={test_report['passed']} failed={test_report['failed']} time={test_report['elapsed_sec']}s\n"]
        if failed:
            body.append("## Провальные кейсы:\n")
            for c in failed:
                body.append(textwrap.dedent(f"""
                **#{c['idx']}**
                **user:** {c['user']}
                **expect:** `{c.get('expect')}`
                **reply:**
                {c['reply']}
                """))
        else:
            body.append("Все тесты пройдены.\n")
        return "\n".join(body)

    def propose_changes(self, test_report: dict, allowlist: list[str]) -> dict:
        """Возвращает dict с ключами: summary_md, patches (map filepath->new_content)"""
        summary_md = self.build_summary(test_report)
        # Просим LLM предложить точечные правки в рамках allowlist
        user_msg = f"""
        Ниже отчёт по тестам. Предложи минимальные правки для прохождения фейлов.
        Разрешено менять ТОЛЬКО файлы из списка: {allowlist}.
        Если нужны иные изменения — опиши их словами (без правок кода), мы добавим `suggestions.md`.

        Требования к ответу:
        1) Сначала краткое резюме (3-5 пунктов) по-русски.
        2) Затем, если уместно, предоставь **файлы целиком** (не diff), готовые к замене: формат JSON
           {{"patches": {{"relative/path.ext": "<новое содержимое файла>"}}}}
        3) Не включай файлы вне allowlist в patches.
        4) В конце короткий список рисков.
        Отчёт:
        {summary_md}
        """
        text = self.llm.chat(system=AGENT_PROMPT, messages=[{"role":"user","content":user_msg}])
        patches = {}
        # Наивный парсинг блока JSON с патчами
        import json, re
        m = re.search(r"\{\s*\"patches\"\s*:\s*\{[\s\S]*?\}\s*\}", text)
        if m:
            try:
                obj = json.loads(m.group(0))
                if "patches" in obj and isinstance(obj["patches"], dict):
                    for path, content in obj["patches"].items():
                        if path in allowlist:
                            patches[path] = content
            except Exception:
                pass
        return {"summary_md": summary_md, "llm_proposal":
