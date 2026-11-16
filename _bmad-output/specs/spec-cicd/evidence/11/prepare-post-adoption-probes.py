"""Prepare product-only fresh-main heads after authenticated App adoption.

No pushes. Exact normal shared checks must succeed on these committed heads
before the separate fresh-ref publication operation. Never merge the probes.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
adoption = json.loads((HERE / "authenticated-adoption.json").read_text())
assert adoption["result"] == "pass"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
destination = HERE / "post-adoption-probe-preparation.json"
assert not destination.exists(), "Inspect saved exact local refs before retrying"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "candidate": adoption["candidate"],
          "purpose": "restricted-token fresh-main product branching after actual App delivery; never merge",
          "modules": {}, "operations": [], "result": "pending"}
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")
scratch = Path(os.environ["TMPDIR"]) / "fresh-main-pilot-probes"
scratch.mkdir()
worktrees = []


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, source, *, authenticated=False):
    value = subprocess.run(arguments, cwd=source, env=environment if authenticated else None,
                           capture_output=True, text=True, timeout=120)
    report["operations"].append({"command": arguments, "repository": str(source), "exit": value.returncode,
                                  "stdout": value.stdout, "stderr": value.stderr})
    save()
    assert value.returncode == 0, value.stderr
    return value.stdout.strip()


try:
    for name, accepted in adoption["modules"].items():
        source = ROOT / "references" / name
        run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], source, authenticated=True)
        base = run(["git", "rev-parse", "origin/main"], source)
        assert base == accepted["adoption_sha"]
        suffix = "commons" if name == "Hexalith.Commons" else "poly"
        branch = "cicd-pilot-fresh-" + suffix + "-20261116"
        assert subprocess.run(["git", "show-ref", "--verify", "--quiet", "refs/heads/" + branch], cwd=source).returncode == 1
        job = scratch / name
        run(["git", "worktree", "add", "-b", branch, str(job), base], source)
        worktrees.append((source, job))
        (job / "pilot-fresh-main-probe.md").write_text(
            "# Pilot fresh-main branch qualification\n\n"
            "Disposable product-only probe created after actual App delivery.\n"
            "Never merge; remove after recording protected-token behavior.\n")
        run(["git", "add", "--", "pilot-fresh-main-probe.md"], job)
        run(["git", "commit", "-m", "test(cicd): qualify fresh-main product branching"], job)
        head = run(["git", "rev-parse", "HEAD"], job)
        paths = run(["git", "diff", "--name-only", base, head], job).splitlines()
        assert paths == ["pilot-fresh-main-probe.md"]
        assert run(["git", "show", "-s", "--format=%P", head], job) == base
        report["modules"][name] = {"base": base, "head": head, "branch": branch,
                                    "changed_paths": paths, "owned_bytes_modes_gitlinks_preserved": True,
                                    "remote_push_performed": False}
        save()
    report["result"] = "prepared; exact normal checker still required before push"
finally:
    cleanup = []
    for source, job in reversed(worktrees):
        value = subprocess.run(["git", "worktree", "remove", "--force", str(job)], cwd=source,
                               capture_output=True, text=True, timeout=120)
        cleanup.append({"repository": str(source), "path": str(job), "exit": value.returncode, "stderr": value.stderr})
    report["worktree_cleanup"] = cleanup
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    assert all(value["exit"] == 0 for value in cleanup)
    for source, job in worktrees:
        assert "worktree " + str(job) + "\n" not in run(["git", "worktree", "list", "--porcelain"], source) + "\n"
    report["all_temporary_worktree_metadata_removed"] = True
    save()
print(json.dumps(report["modules"], indent=2))
