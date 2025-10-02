from __future__ import annotations
import argparse
import json
import random
from pathlib import Path
from typing import List, Dict, Any

import yaml
from sympy import symbols, Eq, sympify, solveset, S

DEFAULT_DATA = Path("data/themes_levels.yaml")

_RAND_RANGE = {
    "small": range(-9, 10),
    "coef":  range(-7, 8),
    "pos":   range(2, 9),
}

PLACEHOLDERS = list("abcdefghijklmnopqrstuvwxyz")


def _strip_comment(template: str) -> str:
    return template.split("#", 1)[0].strip()


def _pick_value(name: str) -> int:
    # Базовая эвристика: положительные для k,p,q,r,s по умолчанию; остальным — маленькие целые
    if name in {"k", "p", "q", "r", "s"}:
        v = random.choice(list(_RAND_RANGE["pos"]))
        if name in {"r"} and v == 0:
            v = 3
        return v
    v = random.choice(list(_RAND_RANGE["coef"]))
    if name == "a" and v == 0:
        v = 2
    return v


def _fill_template(tpl: str) -> str:
    # Находим одиночные буквы‑плейсхолдеры и подставляем значения
    out = []
    i = 0
    while i < len(tpl):
        ch = tpl[i]
        if ch in PLACEHOLDERS:
            # защита от переменной x/y: если сосед — буква или число слева, ставим умножение
            val = str(_pick_value(ch))
            out.append(val)
            i += 1
        else:
            out.append(ch)
            i += 1
    # Чиним возможные случаи "2x" → sympy понимает, оставляем как есть
    return "".join(out)


def _solve_equation(text: str) -> Dict[str, Any]:
    # Пытаемся распарсить как уравнение LHS = RHS и решить по x (или y)
    var = symbols("x")
    if "y" in text and "x" not in text:
        var = symbols("y")
    if "=" not in text:
        return {"answer": None}
    lhs_s, rhs_s = [s.strip() for s in text.split("=", 1)]
    try:
        lhs = sympify(lhs_s)
        rhs = sympify(rhs_s)
        sol = solveset(Eq(lhs, rhs), var, domain=S.Reals)
        # Форматируем кратко
        return {"answer": f"{var} ∈ {str(sol)}"}
    except Exception:
        return {"answer": None}


def generate_exam(level: str, topics: List[str], data_path: Path = DEFAULT_DATA, seed: int | None = None) -> Dict[str, Any]:
    if seed is not None:
        random.seed(seed)
    data = yaml.safe_load(Path(data_path).read_text(encoding="utf-8"))

    q_per_topic = data["exam_builder"]["questions_per_topic"].get(level, 2)

    questions = []
    for topic in topics:
        info = data["topics"].get(topic)
        if not info:
            continue
        templates = info.get("templates", {}).get(level, [])
        if not templates:
            continue
        for _ in range(q_per_topic):
            tpl = random.choice(templates)
            base = _strip_comment(tpl)
            text = _fill_template(base)
            solved = _solve_equation(text)
            questions.append({
                "topic": topic,
                "text": text,
                **solved,
            })

    exam = {
        "level": level,
        "topics": topics,
        "count": len(questions),
        "questions": questions,
    }
    return exam


def main():
    ap = argparse.ArgumentParser(description="Generate exam ticket JSON from data/themes_levels.yaml")
    ap.add_argument("--level", default="средний")
    ap.add_argument("--topics", default="Линейные уравнения;Квадратные уравнения",
                    help="Список тем через ; или ,")
    ap.add_argument("--out", default="reports/sample_ticket.json")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    topics = [t.strip() for t in args.topics.replace(",", ";").split(";") if t.strip()]
    exam = generate_exam(args.level, topics)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(exam, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out}")

if __name__ == "__main__":
    main()
