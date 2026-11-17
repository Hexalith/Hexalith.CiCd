"""Read-only download of digest-matched hexalith-delivery artifacts for AI.Tools.

Uses the committed nightly parser. Saves delivery.json only; never stores tokens.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
sys.path.insert(0, str(ROOT / "tools"))
import nightly_runtime as rt

RUNS = (
    ("initial-adoption", 44040325762, 14309624943),
    ("apply-2a5fd36-failed-run", 44068630104, 14322448269),
    ("later-success", 44070907422, 14323719147),
    ("current-main", 44088282587, 14332956568),
)
environment = dict(os.environ, GH_PROMPT_DISABLED="1")
for name in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)
report = {"started_at": datetime.now(timezone.utc).isoformat(), "runs": {}, "result": "pending"}


def gh(endpoint):
    value = subprocess.run(["gh", "api", endpoint], env=environment,
                           capture_output=True, text=True, timeout=60)
    assert value.returncode == 0, value.stderr
    return json.loads(value.stdout)


token = subprocess.run(["gh", "auth", "token"], env=environment, capture_output=True,
                       text=True, check=True, timeout=30).stdout.strip()
api = rt.API(rt.Budget(token_epoch=time.time()))
try:
    for label, run_id, artifact_id in RUNS:
        selected = gh(f"repos/Hexalith/Hexalith.CiCd/actions/runs/{run_id}")
        inventory = gh(f"repos/Hexalith/Hexalith.CiCd/actions/runs/{run_id}/artifacts?per_page=100")
        artifacts = [item for item in inventory["artifacts"] if item["id"] == artifact_id]
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact["name"] == "hexalith-delivery" and artifact["expired"] is False
        document = api.artifact_member("Hexalith.CiCd", artifact, "delivery.json", token)
        (HERE / f"delivery-{label}.json").write_text(json.dumps(document, indent=2) + "\n")
        tools = [item for item in document.get("modules", []) if item.get("repository") == "Hexalith.AI.Tools"]
        report["runs"][label] = {
            "run_id": run_id,
            "head_sha": selected["head_sha"],
            "event": selected["event"],
            "conclusion": selected["conclusion"],
            "html_url": selected["html_url"],
            "artifact": {key: artifact[key] for key in
                         ("id", "name", "size_in_bytes", "digest", "expired", "expires_at")},
            "ai_tools": tools,
            "delivery_sha256": hashlib.sha256(
                json.dumps(document, sort_keys=True).encode()).hexdigest(),
        }
finally:
    token = None
report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat())
(HERE / "delivery-reports.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({label: {"conclusion": row["conclusion"], "head": row["head_sha"],
                          "ai_tools": row["ai_tools"]}
                  for label, row in report["runs"].items()}, indent=2))
