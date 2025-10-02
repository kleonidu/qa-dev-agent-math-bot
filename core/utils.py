from pathlib import Path
import json
import yaml

def load_yaml(path: str):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))

def save_json(path: str, obj: dict):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def save_text(path: str, text: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")
