import base64
import os
import time
from dataclasses import dataclass
from typing import Optional
import requests

API = "https://api.github.com"
REPO = os.environ["GITHUB_REPO"]
TOKEN = os.environ["GITHUB_TOKEN"]
DEFAULT_BRANCH = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

@dataclass
class FileSpec:
    path: str
    content: str
    sha: Optional[str] = None

class GitHub:
    def __init__(self):
        self.repo = REPO

    def _get(self, path):
        r = requests.get(f"{API}/repos/{self.repo}{path}", headers=HEADERS)
        r.raise_for_status(); return r.json()

    def _post(self, path, json):
        r = requests.post(f"{API}/repos/{self.repo}{path}", headers=HEADERS, json=json)
        r.raise_for_status(); return r.json()

    def _put(self, path, json):
        r = requests.put(f"{API}/repos/{self.repo}{path}", headers=HEADERS, json=json)
        r.raise_for_status(); return r.json()

    def default_branch_sha(self) -> str:
        repo = self._get("")
        branch = self._get(f"/branches/{DEFAULT_BRANCH}")
        return branch["commit"]["sha"]

    def create_branch(self, name: str) -> str:
        base_sha = self.default_branch_sha()
        ref = self._post("/git/refs", {"ref": f"refs/heads/{name}", "sha": base_sha})
        return ref["object"]["sha"]

    def get_file(self, path: str, ref: str = DEFAULT_BRANCH) -> FileSpec:
        data = self._get(f"/contents/{path}?ref={ref}")
        content = base64.b64decode(data["content"]).decode("utf-8") if data.get("content") else ""
        return FileSpec(path=path, content=content, sha=data.get("sha"))

    def put_file(self, path: str, content: str, branch: str, message: str):
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        return self._put(f"/contents/{path}", {
            "message": message,
            "content": encoded,
            "branch": branch,
        })

    def create_pr(self, branch: str, title: str, body: str, draft: bool = True):
        return self._post("/pulls", {
            "title": title,
            "head": branch,
            "base": DEFAULT_BRANCH,
            "body": body,
            "draft": draft,
        })
