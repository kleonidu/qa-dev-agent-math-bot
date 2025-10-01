import argparse
import os
from datetime import datetime
from pathlib import Path
from core.tester import TestRunner
from core.pr_suggester import SuggestionEngine
from core.github import GitHub
from core.utils import load_yaml, save_json, save_text
from core.render import trigger_deploy

DEFAULT_PLAN = "tests/plan_smoke.yaml"

parser = argparse.ArgumentParser(description="QA+Dev Agent for @your_make_math_bot")
parser.add_argument("--plan", default=DEFAULT_PLAN)
parser.add_argument("--apply", action="store_true", help="apply allowlisted patches to a new branch")
parser.add_argument("--autodeploy", action="store_true", help="trigger Render deploy after PR created")

def main():
    args = parser.parse_args()

    cfg = load_yaml("config.yaml")
    allowlist = [p.strip() for p in cfg.get("patch_allowlist", [])]

    # 1) Run tests
    runner = TestRunner(bot_system_prompt_path=os.environ.get("BOT_SYSTEM_PROMPT_PATH", "prompts/bot_system.md"))
    report = runner.run_plan(args.plan)

    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    save_json(f"reports/{ts}.json", report)

    # 2) Propose changes
    sugg = SuggestionEngine()
    proposal = sugg.propose_changes(report, allowlist)

    # 3) Prepare PR content
    pr_body = [
        f"Автоотчёт QA ({args.plan})\n",
        "\n### Краткая сводка тестов\n",
        f"- passed: {report['passed']}\n- failed: {report['failed']}\n- elapsed: {report['elapsed_sec']}s\n",
        "\n---\n",
        "### Предложение LLM\n",
        "\n````md\n",
        proposal["llm_proposal"],
        "\n````\n",
    ]
    pr_body = "".join(pr_body)

    gh = GitHub()

    # 4) Create branch
    branch = os.getenv("GITHUB_BRANCH_OVERRIDE") or (os.getenv("BRANCH_PREFIX", "qa/dev-agent/") + ts)
    gh.create_branch(branch)

    # 5) Always add suggestions.md
    save_text("reports/suggestions.md", proposal["llm_proposal"])
    gh.put_file("reports/suggestions.md", proposal["llm_proposal"], branch, "chore(qaa): add suggestions")

    # 6) Apply allowlisted patches (optional)
    if args.apply:
        for path, content in proposal["patches"].items():
            gh.put_file(path, content, branch, f"fix(qaa): apply patch for {path}")

    # 7) Create Draft PR
    pr = gh.create_pr(branch=branch, title=f"QA: {Path(args.plan).stem}", body=pr_body, draft=True)

    # 8) Optional Render deploy
    if args.autodeploy:
        trigger_deploy()

    print(f"Created PR: {pr.get('html_url')}")

if __name__ == "__main__":
    main()
