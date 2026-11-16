"""Push the exact qualified diagnostic fix once and bind its real delivery."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
candidate = json.loads((HERE / "nightly-diagnostics-candidate-5.json").read_text())
baseline = json.loads((HERE / "resume-nightly-baseline-after-main-advance.json").read_text())
assert candidate["result"] == "pass" and candidate["validation_exit"] == 0
assert candidate["verdict"] == {"global": True, "modules": ["Hexalith.Commons", "Hexalith.PolymorphicSerializations"]}
assert candidate["original_index_preserved"] and all(row["exit"] == 0 for row in candidate["worktree_cleanup"])
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
path = HERE / "nightly-diagnostics-push.json"
assert not path.exists(), "Inspect a partial or uncertain push instead of retrying it"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "head": candidate["head"],
          "base": candidate["base"], "operations": [], "push_attempted": False, "push_confirmed": False}


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments):
    value = subprocess.run(arguments, cwd=ROOT, text=True, capture_output=True, timeout=180)
    report["operations"].append({"arguments": arguments, "exit": value.returncode,
                                  "stdout": value.stdout, "stderr": value.stderr})
    save()
    assert value.returncode == 0, value.stderr
    return value.stdout.strip()


def get(endpoint):
    return json.loads(run(["gh", "api", endpoint]))


run(["git", "fetch", "--no-recurse-submodules", "origin", "main"])
assert run(["git", "rev-parse", "origin/main"]) == candidate["base"]
assert run(["git", "rev-parse", "refs/heads/" + candidate["branch"]]) == candidate["head"]
assert hashlib.sha256((HERE / "nightly-diagnostics-full-validation-5.log").read_bytes()).hexdigest() == candidate["validation_log_sha256"]
for source, expected in candidate["sources"].items():
    assert hashlib.sha256((ROOT / source).read_bytes()).hexdigest() == expected, source
assert hashlib.sha256(subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT)).hexdigest() == baseline["index_entries_sha256"]
assert get("repos/Hexalith/Hexalith.CiCd/git/ref/heads/main")["object"]["sha"] == candidate["base"]
report["push_attempted"] = True
save()
run(["git", "push", "--porcelain", "origin", candidate["head"] + ":refs/heads/main"])
assert get("repos/Hexalith/Hexalith.CiCd/git/ref/heads/main")["object"]["sha"] == candidate["head"]
report["push_confirmed"] = True
save()
deadline = time.monotonic() + 180
while time.monotonic() < deadline:
    inventory = get("repos/Hexalith/Hexalith.CiCd/actions/workflows/deliver.yml/runs?branch=main&event=push&head_sha="
                    + candidate["head"] + "&per_page=100")
    assert inventory["total_count"] < 100
    matches = [item for item in inventory["workflow_runs"] if item["head_sha"] == candidate["head"]
               and item["path"] == ".github/workflows/deliver.yml" and item["event"] == "push"
               and item["head_branch"] == "main"]
    assert len(matches) <= 1
    if matches:
        report["delivery_run"] = {key: matches[0].get(key) for key in (
            "id", "path", "event", "head_sha", "head_branch", "status", "conclusion",
            "run_attempt", "created_at", "html_url")}
        report["result"] = "exact qualified fix pushed; genuine push-created delivery bound"
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        save()
        print(json.dumps(report["delivery_run"], indent=2))
        break
    time.sleep(5)
else:
    raise RuntimeError("Confirmed push has no unique real delivery run; do not dispatch or repeat the push")
