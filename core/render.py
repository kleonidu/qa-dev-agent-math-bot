import os
import requests

RENDER_API = "https://api.render.com/v1"
TOKEN = os.getenv("RENDER_API_KEY")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
SERVICE_ID = os.getenv("RENDER_SERVICE_ID")

def trigger_deploy():
    if not (TOKEN and SERVICE_ID):
        return {"skipped": True, "reason": "no credentials"}
    r = requests.post(f"{RENDER_API}/services/{SERVICE_ID}/deploys", headers=HEADERS, json={})
    r.raise_for_status()
    return r.json()
