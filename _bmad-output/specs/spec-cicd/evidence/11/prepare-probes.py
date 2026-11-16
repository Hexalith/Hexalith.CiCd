"""Create local-only pilot probe commits from fresh main, retaining legacy tooling.

Run under run-with-temp. These branches must receive the complete approved
pre-adoption verification before any remote push; this script never pushes.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
PRODUCT = (".github/actions/after-unit-tests/action.yml", "scripts/pack-release-packages.py",
           "scripts/validate-consumer-package-references.py")
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
workspace = Path(os.environ["TMPDIR"]) / "local-probe-preparation"
workspace.mkdir()
sys.path.insert(0, str(ROOT / "references/Hexalith.Builds/Github/lib"))
from guard_tools import Tools
from expected_state import Git, tree_snapshot
tools_directory = workspace / "guard-tools"
tools_directory.mkdir()
tools = Tools(tools_directory)
fetch_environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                         GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    fetch_environment.pop(name, None)
report_path = HERE / "local-probe-preparation.json"
assert not report_path.exists(), "Inspect existing local probe evidence instead of repeating preparation"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "purpose": "pre-delivery Update branch qualification",
          "remote_push_performed": False, "pull_request_created": False,
          "full_approved_product_verification": "required before each eventual push",
          "modules": {}, "operations": []}


def save():
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, repository, *, env=None, data=None):
    result = subprocess.run(arguments, cwd=repository, env=env, input=data, text=True, capture_output=True, timeout=120)
    report["operations"].append({"command": arguments, "cwd": str(repository), "exit": result.returncode,
                                  "stdout": result.stdout, "stderr": result.stderr})
    save()
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


for name in MODULES:
    source = ROOT / "references" / name
    run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], source, env=fetch_environment)
    base = run(["git", "rev-parse", "origin/main"], source)
    branch = "cicd-pilot-update-" + ("commons" if name == MODULES[0] else "poly") + "-20261116"
    assert not subprocess.run(["git", "show-ref", "--verify", "refs/heads/" + branch],
                              cwd=source, capture_output=True).returncode == 0
    message = "test(cicd): prepare pilot branch qualification\n\nKeep this disposable product probe unmerged for the real delivery Update branch check.\n"
    tools.lint_message(message, name)
    config = tools_directory / (name + ".commitlint.config.mjs")
    config.write_bytes(subprocess.run(["git", "show", base + ":commitlint.config.mjs"], cwd=source,
                                     capture_output=True, check=True).stdout)
    lock_bytes = subprocess.run(["git", "show", base + ":package-lock.json"], cwd=source,
                                capture_output=True, check=True).stdout
    lock = json.loads(lock_bytes)
    assert all(lock["packages"]["node_modules/" + package]["version"] == "21.2.4"
               for package in ("@commitlint/cli", "@commitlint/config-conventional"))
    result = subprocess.run(["node", str(tools_directory / "node_modules/@commitlint/cli/cli.js"),
                             "--config", str(config), "--color=false"], cwd=tools_directory,
                            env=tools.environment, input=message, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    job = workspace / name
    run(["git", "worktree", "add", "-b", branch, str(job), base], source)
    try:
        allowed = {"pilot-ci-probe.md"}
        if name == MODULES[0]:
            for path in PRODUCT:
                destination = job / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((source / path).read_bytes())
            allowed.update(PRODUCT)
        (job / "pilot-ci-probe.md").write_text("# CI/CD pilot probe\n\nDisposable product branch for " + name + ".\nDo not merge this pull request.\n")
        run(["git", "add", "--", *sorted(allowed)], job)
        run(["git", "commit", "--file", "-"], job, data=message)
        head = run(["git", "rev-parse", "HEAD"], job)
        assert run(["git", "rev-parse", "HEAD^"], job) == base
        git = Git(job)
        before, candidate = (tree_snapshot(git, sha) for sha in (base, head))
        changed = sorted(path for path in set(before.items) | set(candidate.items)
                         if before.items.get(path) != candidate.items.get(path))
        assert changed and set(changed).issubset(allowed)
        assert "pilot-ci-probe.md" in changed
        unchanged = []
        for path in sorted((set(before.items) | set(candidate.items)) - allowed):
            assert before.items.get(path) is not None and before.items[path] == candidate.items.get(path), path
            item = before.items[path]
            record = {"path": path, "mode": item.mode, "oid": item.oid}
            if item.mode != "160000":
                assert before.read(path) == candidate.read(path), path
                record["sha256"] = hashlib.sha256(before.read(path)).hexdigest()
            unchanged.append(record)
        assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], job) == ""
        report["modules"][name] = {"branch": branch, "base": base, "head": head,
                                   "allowed_changed_paths": sorted(allowed), "changed_paths": changed,
                                   "unchanged_byte_mode_gitlink_records": unchanged,
                                   "owning_and_shared_commit_policy": "pass",
                                   "legacy_tooling_retained": True}
        save()
    finally:
        run(["git", "worktree", "remove", "--force", str(job)], source)
        assert "worktree " + str(job) + "\n" not in run(["git", "worktree", "list", "--porcelain"], source) + "\n"
        report["modules"].setdefault(name, {})["temporary_worktree_metadata_removed"] = True
        save()
report["completed_at"] = datetime.now(timezone.utc).isoformat()
report["result"] = "local candidates prepared; full verification and remote operations still pending"
save()
print(json.dumps({name: {key: report["modules"][name][key] for key in ("branch", "base", "head")}
                  for name in MODULES}, indent=2), flush=True)
