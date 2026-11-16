"""Observe the exact push-created pilot delivery run without mutation."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--qualified-policy", action="store_true")
args = parser.parse_args()
binding = json.loads((HERE / ("qualified-policy-push.json" if args.qualified_policy else "cicd-candidate-push.json")).read_text())
PREFIX = "qualified-policy-delivery-observation" if args.qualified_policy else "pilot-delivery-observation"
identity = binding["delivery_run"]["id"]
head = binding["head"]
assert head == ("3427f041c5f686c460c1fa027cf6f835791209c1" if args.qualified_policy else "f002539f6fbaddaa9b621a9cbf75a1263eee5dea")
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
endpoint = "repos/Hexalith/Hexalith.CiCd/actions/runs/" + str(identity)
report = {"started_at": datetime.now(timezone.utc).isoformat(), "run_id": identity, "candidate": head, "observations": []}
previous = None
deadline = time.monotonic() + 7200


def get(path):
    value = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True, timeout=60)
    return json.loads(value.stdout)


while time.monotonic() < deadline:
    run = get(endpoint)
    assert run["id"] == identity and run["head_sha"] == head and run["head_branch"] == "main"
    assert run["event"] == "push" and run["path"] == ".github/workflows/deliver.yml"
    jobs = get(endpoint + "/jobs?per_page=100")
    assert jobs["total_count"] < 100
    rows = [{"id": job["id"], "name": job["name"], "status": job["status"], "conclusion": job["conclusion"],
             "started_at": job["started_at"], "completed_at": job["completed_at"],
             "active_steps": [step["name"] for step in job.get("steps", []) if step["status"] == "in_progress"]}
            for job in jobs["jobs"]]
    state = (run["status"], run["conclusion"], run["run_attempt"], json.dumps(rows, sort_keys=True))
    if state != previous:
        observation = {"observed_at": datetime.now(timezone.utc).isoformat(),
                       **{key: run.get(key) for key in ("id", "head_sha", "path", "event", "status", "conclusion", "run_attempt", "html_url")},
                       "jobs": rows}
        report["observations"].append(observation)
        (HERE / (PREFIX + ".json")).write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(observation), flush=True)
        previous = state
    if run["status"] == "completed":
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        report["result"] = "pass" if run["conclusion"] == "success" else "fail"
        (HERE / (PREFIX + ".json")).write_text(json.dumps(report, indent=2) + "\n")
        raise SystemExit(0 if run["conclusion"] == "success" else 1)
    time.sleep(30)
raise SystemExit("Bounded delivery observation expired; no adoption inferred")
