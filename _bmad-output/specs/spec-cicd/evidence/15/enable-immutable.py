"""Enable McpCli immutable releases immediately after authenticated App adoption."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
MODULE = "Hexalith.McpCli"
REPOSITORY_ID = 1379417482
assert os.environ.get("GH_CONFIG_DIR") != "/home/administrator/.config/gh"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
adoption = json.loads((HERE / "authenticated-adoption.json").read_text())
assert adoption["result"] == "pass"
assert adoption["modules"][MODULE]["perimeter_match"] is True
ADOPTED = adoption["modules"][MODULE]["adoption_sha"]
environment = dict(
    os.environ,
    GH_CONFIG_DIR="/home/administrator/.config/gh",
    GH_PROMPT_DISABLED="1",
)
for key in ("GH_DEBUG", "GIT_CURL_VERBOSE", "GITHUB_TOKEN"):
    environment.pop(key, None)
path = HERE / "post-adoption-github-cleanup.json"
assert not path.exists(), "Inspect saved cleanup status before any repeated write"
report = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "administration_profile": environment["GH_CONFIG_DIR"],
    "module": MODULE,
    "repository_id": REPOSITORY_ID,
    "current_main": ADOPTED,
    "candidate": adoption["candidate"],
    "requests": [],
    "result": "pending",
}


def save() -> None:
    path.write_text(json.dumps(report, indent=2) + "\n")


def api(method, endpoint, *, allowed=(0,)):
    value = subprocess.run(
        ["gh", "api", "--method", method, "--include", endpoint],
        env=environment, capture_output=True, text=True, timeout=60)
    headers, _, body = value.stdout.partition("\n\n")
    status = next((line for line in headers.splitlines() if line.startswith("HTTP/")), "")
    document = json.loads(body) if body.strip() else None
    report["requests"].append({
        "at": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "endpoint": endpoint,
        "status": status,
        "exit": value.returncode,
        "data": document,
        "error": value.stderr.strip(),
    })
    save()
    print(method, endpoint, status, flush=True)
    assert value.returncode in allowed, value.stderr
    return document, status


save()
user, _ = api("GET", "user")
assert (user["login"], user["id"]) == ("jpiquot", 6775094)
prefix = "repos/Hexalith/" + MODULE
assert api("GET", prefix)[0]["id"] == REPOSITORY_ID
assert api("GET", prefix + "/git/ref/heads/main")[0]["object"]["sha"] == ADOPTED
_, status = api("PUT", prefix + "/immutable-releases")
assert "204" in status
assert api("GET", prefix + "/immutable-releases")[0]["enabled"] is True
report["immutable_releases"] = True
report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat())
save()
print(json.dumps({"result": "pass", "immutable_releases": True, "main": ADOPTED}, indent=2))
