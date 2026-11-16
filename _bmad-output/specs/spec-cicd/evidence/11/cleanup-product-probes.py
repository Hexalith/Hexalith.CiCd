"""Close the two owned probe PRs and compare-and-delete only four probe refs.

No PR merge or main write. Protected module token only. Remote branch deletion
uses an exact SHA lease; local refs use compare-and-delete expected identities.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
pre = json.loads((HERE / "pre-delivery-probes.json").read_text())
updated = json.loads((HERE / "post-delivery-update-branch.json").read_text())
fresh = json.loads((HERE / "post-adoption-fresh-branch-outcomes.json").read_text())
assert updated["result"].startswith("qualified actual server outcomes") and fresh["result"] == "pass"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")
destination = HERE / "product-probe-cleanup.json"
assert not destination.exists(), "Inspect exact partial cleanup before any repeat mutation"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "modules": {}, "operations": [], "result": "pending"}


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, source=ROOT, document=None):
    value = subprocess.run(arguments, cwd=source, env=environment, input=json.dumps(document) if document is not None else None,
                           capture_output=True, text=True, timeout=120)
    report["operations"].append({"command": arguments, "repository": str(source), "input": document,
                                  "exit": value.returncode, "stdout": value.stdout, "stderr": value.stderr})
    save()
    assert value.returncode == 0, value.stderr
    return value.stdout.strip()


def get(endpoint):
    return json.loads(run(["gh", "api", endpoint]))


for name, original in pre["modules"].items():
    source = ROOT / "references" / name
    result = updated["modules"][name]
    expected_pr_head = result.get("new_head", original["head"])
    prefix = "repos/Hexalith/" + name
    endpoint = prefix + "/pulls/" + str(original["pull_request_number"])
    pull = get(endpoint)
    assert pull["state"] == "open" and pull["merged"] is False and pull["head"]["sha"] == expected_pr_head
    run(["gh", "api", "--method", "PATCH", endpoint, "--input", "-"], document={"state": "closed"})
    closed = get(endpoint)
    assert closed["state"] == "closed" and closed["merged"] is False and closed["merged_at"] is None
    assert closed["head"]["sha"] == expected_pr_head
    row = {"pull_request": closed["number"], "state": "closed", "merged": False,
           "head": expected_pr_head, "remote_refs_deleted": [], "local_refs_deleted": []}
    report["modules"][name] = row
    save()
    refs = [(original["branch"], expected_pr_head, original["head"]),
            (fresh["modules"][name]["branch"], fresh["modules"][name]["head"], fresh["modules"][name]["head"])]
    for branch, remote_head, local_head in refs:
        reference = "refs/heads/" + branch
        assert get(prefix + "/git/ref/heads/" + branch)["object"]["sha"] == remote_head
        run(["git", "push", "--porcelain", "--force-with-lease=" + reference + ":" + remote_head,
             "origin", ":" + reference], source)
        assert run(["git", "ls-remote", "--heads", "origin", reference], source) == ""
        row["remote_refs_deleted"].append({"ref": reference, "expected_head": remote_head, "atomic_exact_sha_lease": True})
        save()
        assert run(["git", "rev-parse", reference], source) == local_head
        worktrees = run(["git", "worktree", "list", "--porcelain"], source)
        assert "branch " + reference + "\n" not in worktrees + "\n"
        run(["git", "update-ref", "-d", reference, local_head], source)
        assert subprocess.run(["git", "show-ref", "--verify", "--quiet", reference], cwd=source).returncode == 1
        row["local_refs_deleted"].append({"ref": reference, "expected_head": local_head, "compare_and_delete": True})
        save()
    row["main_after_cleanup"] = get(prefix + "/git/ref/heads/main")["object"]["sha"]
    assert row["main_after_cleanup"] == result["main"]
report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat(), no_pull_request_merged=True)
save()
print(json.dumps(report["modules"], indent=2))
