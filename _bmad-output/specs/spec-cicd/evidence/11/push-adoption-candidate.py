"""Push only the fully qualified exact candidate and bind its push delivery run."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
candidate = json.loads((HERE / "adoption-candidate.json").read_text())
validation = json.loads((HERE / "candidate-validation-2.json").read_text())
assert candidate["head"] == validation["candidate"] == "f002539f6fbaddaa9b621a9cbf75a1263eee5dea"
assert validation["validation_exit"] == 0 and validation["verdict"] == {
    "global": True, "modules": ["Hexalith.Commons", "Hexalith.PolymorphicSerializations"]}
assert validation["result"] == "both preparation mains published and exact committed/live candidate passed"
assert validation["all_temporary_worktree_metadata_removed"] is True
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
readiness = json.loads((HERE / "nuget-cleanup-readiness.json").read_text())
age = (datetime.now(timezone.utc) - datetime.fromisoformat(readiness["observed_at"])).total_seconds()
assert 0 <= age < 180, "Refresh authenticated NuGet cleanup controls immediately before pushing"
assert readiness["exit"] == 0 and readiness["result"]["legacy_delete_control_invoked"] is False
assert {value["id"] for value in readiness["result"]["policies"]} == {"20233", "20232", "27048", "27049"}
destination = HERE / "cicd-candidate-push.json"
assert not destination.exists(), "Inspect exact partial push/run outcome; do not repeat blindly"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "head": candidate["head"], "base": candidate["base"],
          "validation_report_sha256": hashlib.sha256((HERE / "candidate-validation-2.json").read_bytes()).hexdigest(),
          "nuget_cleanup_readiness_sha256": hashlib.sha256((HERE / "nuget-cleanup-readiness.json").read_bytes()).hexdigest(),
          "operations": [], "push_attempted": False}
module_environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                          GH_PROMPT_DISABLED="1")


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, *, module=False):
    result = subprocess.run(arguments, cwd=ROOT, env=module_environment if module else None,
                            capture_output=True, text=True, timeout=180)
    report["operations"].append({"command": arguments, "exit": result.returncode,
                                  "stdout": result.stdout, "stderr": result.stderr})
    save()
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def get(endpoint, *, module=False):
    return json.loads(run(["gh", "api", endpoint], module=module))


run(["git", "fetch", "--no-recurse-submodules", "origin", "main"])
assert run(["git", "rev-parse", "origin/main"]) == candidate["base"]
assert run(["git", "rev-parse", "refs/heads/" + candidate["branch"]]) == candidate["head"]
for path, value in candidate["source_file_sha256"].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == value
preparation = json.loads((HERE / "local-product-preparation.json").read_text())
for name, value in preparation["modules"].items():
    current = get("repos/Hexalith/" + name + "/git/ref/heads/main", module=True)
    assert current["object"]["sha"] == value["head"], "Main advanced after validation"
release = get("repos/Hexalith/Hexalith.Builds/releases/tags/v6.0.6")
assert release["immutable"] is True and release["draft"] is False and release["author"]["login"] == "github-actions[bot]"
accepted = get("repos/Hexalith/Hexalith.CiCd/git/matching-refs/heads/delivered/")
assert accepted == [], "Reassess pre-existing accepted targets before first pilot adoption"
report["immediate_prepush_freshness_at"] = datetime.now(timezone.utc).isoformat()
report["push_attempted"] = True
save()
run(["git", "push", "--porcelain", "origin", candidate["head"] + ":refs/heads/main"])
current = get("repos/Hexalith/Hexalith.CiCd/git/ref/heads/main")
assert current["object"]["sha"] == candidate["head"]
report["push_confirmed"] = True
save()
deadline = time.monotonic() + 180
while time.monotonic() < deadline:
    value = get("repos/Hexalith/Hexalith.CiCd/actions/workflows/deliver.yml/runs?branch=main&event=push&head_sha=" + candidate["head"] + "&per_page=100")
    assert value["total_count"] < 100
    matches = [row for row in value["workflow_runs"] if row["head_sha"] == candidate["head"]
               and row["head_branch"] == "main" and row["event"] == "push" and row["path"] == ".github/workflows/deliver.yml"]
    assert len(matches) <= 1, "Ambiguous exact-source push run"
    if matches:
        selected = matches[0]
        report["delivery_run"] = {key: selected.get(key) for key in (
            "id", "head_sha", "head_branch", "path", "event", "run_attempt", "status", "conclusion", "html_url", "created_at")}
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        report["result"] = "exact candidate pushed and delivery run bound"
        save()
        print(json.dumps(report["delivery_run"], indent=2))
        break
    time.sleep(5)
else:
    raise AssertionError("Push confirmed but delivery run not correlated; do not redispatch")
