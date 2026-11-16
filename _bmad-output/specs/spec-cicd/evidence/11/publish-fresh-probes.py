"""Publish only exact normal-checker-qualified product heads with module token."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
prepared = json.loads((HERE / "post-adoption-probe-preparation.json").read_text())
proof = json.loads((HERE / "post-adoption-check.json").read_text())
assert proof["result"] == "pass" and proof["all_temporary_worktree_metadata_removed"] is True
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")
destination = HERE / "post-adoption-fresh-branch-outcomes.json"
assert not destination.exists(), "Inspect exact partial remote results before any retry"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "modules": {}, "operations": [], "result": "pending"}


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, repository):
    value = subprocess.run(arguments, cwd=repository, env=environment, capture_output=True, text=True, timeout=120)
    report["operations"].append({"command": arguments, "repository": str(repository), "exit": value.returncode,
                                  "stdout": value.stdout, "stderr": value.stderr})
    save()
    assert value.returncode == 0, value.stderr
    return value.stdout.strip()


for name, item in prepared["modules"].items():
    assert all(proof["modules"][name][key] == item[key] for key in ("base", "head"))
    assert proof["modules"][name]["checker_exit"] == 0
# Refresh each base/head after BOTH complete check jobs; repeat immediately at
# each push so an earlier Commons check cannot silently outlive Poly checking.
for name, item in prepared["modules"].items():
    source = ROOT / "references" / name
    run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], source)
    assert run(["git", "rev-parse", "origin/main"], source) == item["base"]
    assert run(["git", "rev-parse", "refs/heads/" + item["branch"]], source) == item["head"]
for name, item in prepared["modules"].items():
    source = ROOT / "references" / name
    run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], source)
    assert run(["git", "rev-parse", "origin/main"], source) == item["base"]
    assert run(["git", "rev-parse", "refs/heads/" + item["branch"]], source) == item["head"]
    assert run(["git", "ls-remote", "--heads", "origin", "refs/heads/" + item["branch"]], source) == "", "Probe destination already exists; preserve and inspect"
    report["modules"][name] = {**item, "immediate_prepush_freshness_at": datetime.now(timezone.utc).isoformat(),
                                "remote_destination_absent_before_push": True, "push_attempted": True}
    save()
    run(["git", "push", "--porcelain", "origin", item["head"] + ":refs/heads/" + item["branch"]], source)
    actual = json.loads(run(["gh", "api", "repos/Hexalith/" + name + "/git/ref/heads/" + item["branch"]], ROOT))
    assert actual["object"]["sha"] == item["head"]
    report["modules"][name]["push_confirmed"] = True
    save()
report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat())
save()
print(json.dumps(report["modules"], indent=2))
