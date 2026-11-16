"""Observe one exact authorized Builds CI/release run; no dispatch or mutation."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("kind", choices=("ci", "release"))
parser.add_argument("run_id", type=int)
parser.add_argument("sha")
arguments = parser.parse_args()
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
expected = ".github/workflows/builds-" + arguments.kind + ".yml"
endpoint = "repos/Hexalith/Hexalith.Builds/actions/runs/" + str(arguments.run_id)
path = Path(__file__).parent / ("builds-" + arguments.kind + "-observation-" + str(arguments.run_id) + ".json")
report = {"started_at": datetime.now(timezone.utc).isoformat(), "run_id": arguments.run_id,
          "expected_sha": arguments.sha, "workflow": expected, "observations": []}
deadline = time.monotonic() + 7200
previous = None


def get(suffix=""):
    result = subprocess.run(["gh", "api", "--method", "GET", endpoint + suffix],
                            text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


while time.monotonic() < deadline:
    run = get()
    assert run["id"] == arguments.run_id and run["head_sha"] == arguments.sha
    assert run["head_branch"] == "main" and run["path"] == expected
    assert run["event"] == ("push" if arguments.kind == "ci" else "workflow_dispatch")
    state = (run["status"], run["conclusion"], run["run_attempt"])
    if state != previous:
        observation = {name: run.get(name) for name in (
            "id", "head_sha", "head_branch", "path", "event", "status", "conclusion",
            "run_attempt", "created_at", "updated_at", "html_url")}
        observation["observed_at"] = datetime.now(timezone.utc).isoformat()
        jobs = get("/jobs?per_page=100")
        assert jobs["total_count"] < 100
        observation["jobs"] = [{name: job.get(name) for name in (
            "id", "name", "status", "conclusion", "started_at", "completed_at", "steps")}
            for job in jobs["jobs"]]
        report["observations"].append(observation)
        path.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"observed_at": observation["observed_at"], "run_id": arguments.run_id,
                          "status": run["status"], "conclusion": run["conclusion"]}), flush=True)
        previous = state
    if run["status"] == "completed":
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        report["result"] = "pass" if run["conclusion"] == "success" else "fail"
        path.write_text(json.dumps(report, indent=2) + "\n")
        raise SystemExit(0 if run["conclusion"] == "success" else 1)
    time.sleep(30)
raise SystemExit("Observation deadline exceeded; exact run remains unverified")
