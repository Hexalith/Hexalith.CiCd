"""Push the fully qualified exact policy candidate and bind its push run."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
candidate = json.loads((HERE / "qualified-policy-candidate.json").read_text())
adoption = json.loads((HERE / "authenticated-adoption.json").read_text())
assert candidate["head"] == "3427f041c5f686c460c1fa027cf6f835791209c1"
assert candidate["validation_exit"] == 0 and candidate["verdict"] == {"global": True, "modules": list(adoption["modules"])}
assert candidate["result"] == "exact qualified-policy candidate passed full locked gate"
assert candidate["all_temporary_worktree_metadata_removed"] is True
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
assert json.loads((HERE / "product-probe-cleanup.json").read_text())["result"] == "pass"
assert json.loads((HERE / "post-adoption-github-cleanup.json").read_text())["result"] == "pass"
assert json.loads((HERE / "nuget-cleanup-verify-cleanup.json").read_text())["all_other_policy_ids_preserved"] is True
destination = HERE / "qualified-policy-push.json"
assert not destination.exists(), "Inspect actual partial push/run binding before any retry"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "head": candidate["head"], "base": candidate["base"],
          "full_candidate_report_sha256": hashlib.sha256((HERE / "qualified-policy-candidate.json").read_bytes()).hexdigest(),
          "operations": [], "push_attempted": False}
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, *, module=False):
    value = subprocess.run(arguments, cwd=ROOT, env=environment if module else None,
                           capture_output=True, text=True, timeout=180)
    report["operations"].append({"command": arguments, "exit": value.returncode,
                                  "stdout": value.stdout, "stderr": value.stderr})
    save()
    assert value.returncode == 0, value.stderr
    return value.stdout.strip()


def get(endpoint, *, module=False):
    return json.loads(run(["gh", "api", endpoint], module=module))


run(["git", "fetch", "--no-recurse-submodules", "origin", "main"])
assert run(["git", "rev-parse", "origin/main"]) == candidate["base"]
assert run(["git", "rev-parse", "refs/heads/" + candidate["branch"]]) == candidate["head"]
for path, value in candidate["source_file_sha256"].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == value
for name, item in adoption["modules"].items():
    assert get("repos/Hexalith/" + name + "/git/ref/heads/main", module=True)["object"]["sha"] == item["adoption_sha"]
    assert get("repos/Hexalith/Hexalith.CiCd/git/ref/heads/delivered/" + name)["object"]["sha"] == candidate["base"]
release = get("repos/Hexalith/Hexalith.Builds/releases/tags/v6.0.6")
assert release["immutable"] is True and release["draft"] is False and release["author"]["login"] == "github-actions[bot]"
staging = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                         capture_output=True, check=True).stdout
assert hashlib.sha256(staging).hexdigest() == candidate["original_staging_sha256"]
report.update(immediate_prepush_freshness_at=datetime.now(timezone.utc).isoformat(), push_attempted=True)
save()
run(["git", "push", "--porcelain", "origin", candidate["head"] + ":refs/heads/main"])
assert get("repos/Hexalith/Hexalith.CiCd/git/ref/heads/main")["object"]["sha"] == candidate["head"]
report["push_confirmed"] = True
save()
deadline = time.monotonic() + 180
while time.monotonic() < deadline:
    runs = get("repos/Hexalith/Hexalith.CiCd/actions/workflows/deliver.yml/runs?branch=main&event=push&head_sha=" + candidate["head"] + "&per_page=100")
    assert runs["total_count"] < 100
    matches = [item for item in runs["workflow_runs"] if item["head_sha"] == candidate["head"]
               and item["path"] == ".github/workflows/deliver.yml" and item["event"] == "push" and item["head_branch"] == "main"]
    assert len(matches) <= 1
    if matches:
        report["delivery_run"] = {key: matches[0].get(key) for key in (
            "id", "head_sha", "head_branch", "path", "event", "run_attempt", "status", "conclusion", "html_url", "created_at")}
        report.update(result="exact qualified policy pushed and actual delivery run bound", completed_at=datetime.now(timezone.utc).isoformat())
        save()
        print(json.dumps(report["delivery_run"], indent=2))
        break
    time.sleep(5)
else:
    raise AssertionError("Confirmed push has no uniquely correlated delivery run; do not dispatch/retry")
