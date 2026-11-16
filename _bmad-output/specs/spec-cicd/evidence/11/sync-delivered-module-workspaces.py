"""Conditionally fast-forward the two clean original checkouts after redelivery.

This intentional materialization of authenticated App commits is separate from
earlier preservation proofs. No reset, owned-file authoring, nested dependency
initialization, force update or original CiCd index change is permitted.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
adoption = json.loads((HERE / "authenticated-policy-redelivery.json").read_text())
assert adoption["result"] == "pass" and adoption["candidate"] == "3427f041c5f686c460c1fa027cf6f835791209c1"
preparation = json.loads((HERE / "local-product-preparation.json").read_text())
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")
destination = HERE / "original-module-workspace-sync.json"
assert not destination.exists(), "Inspect exact intentional sync status before retrying"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "candidate": adoption["candidate"],
          "operation": "ordinary checkout and fast-forward of clean task preparation/main workspaces only",
          "earlier_preservation_proofs_retained": True, "operations": [], "modules": {}, "result": "pending"}


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, source=ROOT, *, authenticated=False, allowed=(0,)):
    value = subprocess.run(arguments, cwd=source, env=environment if authenticated else None,
                           capture_output=True, text=True, timeout=120)
    report["operations"].append({"command": arguments, "repository": str(source), "exit": value.returncode,
                                  "stdout": value.stdout, "stderr": value.stderr})
    save()
    assert value.returncode in allowed, value.stderr
    return value.stdout.strip(), value.returncode


def git(source, *arguments):
    return run(["git", *arguments], source)[0]


staging = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                         capture_output=True, check=True).stdout
root_head = git(ROOT, "rev-parse", "HEAD")
report["original_cicd_head_before"] = root_head
report["original_cicd_staging_sha256"] = hashlib.sha256(staging).hexdigest()
try:
    for name, receipt in adoption["modules"].items():
        source = ROOT / "references" / name
        prior = preparation["modules"][name]
        head = git(source, "rev-parse", "HEAD")
        branch, _ = run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], source, allowed=(0, 1))
        status = git(source, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=all")
        nested = source / "references/Hexalith.Builds"
        contents = "symlink preserved" if nested.is_symlink() else sorted(path.name for path in nested.iterdir()) if nested.is_dir() else None
        row = {"before_head": head, "before_branch": branch, "target": receipt["application_sha"],
               "nested_builds_contents_before": contents, "result": "pending"}
        report["modules"][name] = row
        save()
        if status or nested.is_symlink() or contents not in (None, []):
            row.update(result="preserved without sync", reason="user changes or populated nested dependency; no overwrite")
            save()
            continue
        if branch not in {"main", prior["branch"]}:
            row.update(result="preserved without sync", reason="clean user-selected branch outside task preparation/main")
            save()
            continue
        current = json.loads(run(["gh", "api", "repos/Hexalith/" + name + "/git/ref/heads/main"], authenticated=True)[0])
        if current["object"]["sha"] != row["target"]:
            row.update(result="preserved without sync", reason="remote main advanced beyond authenticated redelivery")
            save()
            continue
        run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], source, authenticated=True)
        assert git(source, "rev-parse", "origin/main") == row["target"]
        ancestor_checks = {}
        for label, revision in (("preparation", prior["head"]), ("current_head", head), ("local_main", "refs/heads/main")):
            _, exit_status = run(["git", "merge-base", "--is-ancestor", revision, row["target"]], source, allowed=(0, 1))
            ancestor_checks[label] = exit_status == 0
        row["ancestor_checks"] = ancestor_checks
        if not all(ancestor_checks.values()):
            row.update(result="preserved without sync", reason="local work is not fully ancestral to authenticated main")
            save()
            continue
        assert git(source, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=all") == ""
        options = ["git", "-c", "core.hooksPath=/dev/null", "-c", "submodule.recurse=false"]
        run(options + ["checkout", "--no-recurse-submodules", "main"], source)
        run(options + ["merge", "--ff-only", "origin/main"], source)
        assert git(source, "rev-parse", "HEAD") == row["target"]
        assert git(source, "symbolic-ref", "--short", "HEAD") == "main"
        assert git(source, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=all") == ""
        after_contents = sorted(path.name for path in nested.iterdir()) if nested.is_dir() else None
        assert after_contents in (None, [])
        row.update(result="synced", after_head=row["target"], after_branch="main", clean_after=True,
                   nested_builds_contents_after=after_contents, no_nested_initialization=True)
        save()
    report["result"] = "pass" if all(row["result"] == "synced" for row in report["modules"].values()) else "user state preserved; conditional sync incomplete"
finally:
    after = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                           capture_output=True, check=True).stdout
    report["original_cicd_staging_preserved"] = after == staging
    report["original_cicd_head_after"] = git(ROOT, "rev-parse", "HEAD")
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    assert after == staging and report["original_cicd_head_after"] == root_head
print(json.dumps(report["modules"], indent=2))
