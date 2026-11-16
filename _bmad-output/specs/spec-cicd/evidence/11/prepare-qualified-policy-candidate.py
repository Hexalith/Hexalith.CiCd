"""Commit and fully qualify the factual post-probe CiCd policy in isolation.

Only canonical policy, its renderer assertions/output, and authenticated direct
module gitlinks enter this candidate. Historical/tracking/evidence edits stay
reviewable in the original workspace, whose index is preserved byte-for-byte.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
initial = json.loads((HERE / "adoption-candidate.json").read_text())
adoption = json.loads((HERE / "authenticated-adoption.json").read_text())
cleanup = json.loads((HERE / "product-probe-cleanup.json").read_text())
updates = json.loads((HERE / "post-delivery-update-branch.json").read_text())
assert adoption["result"] == cleanup["result"] == "pass"
assert all(item["http_status"] == "HTTP/2.0 202 Accepted" and item["all_adopted_workflow_and_other_owned_bytes_modes_gitlinks_imported_exactly"]
           for item in updates["modules"].values())
destination = HERE / "qualified-policy-candidate.json"
assert not destination.exists(), "Inspect existing exact candidate verdict; do not duplicate validation"
sources = ("AGENTS.md", "templates/partials/ownership-block.txt.j2", "tools/tests/test_render.py",
           "rendered/Hexalith.Commons.perimeter.json", "rendered/Hexalith.PolymorphicSerializations.perimeter.json")
report = {"started_at": datetime.now(timezone.utc).isoformat(), "base": initial["head"],
          "branch": "cicd-pilot-qualified-policy-20261116", "source_file_sha256": {
              name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
          "direct_gitlinks": {"Hexalith.Builds": initial["direct_gitlinks"]["Hexalith.Builds"],
                              **{name: item["adoption_sha"] for name, item in adoption["modules"].items()}},
          "operations": [], "phase": "prepare", "result": "pending", "push_performed": False}
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")
scratch = Path(os.environ["TMPDIR"]) / "qualified-policy-candidate"
scratch.mkdir()
job = scratch / "cicd"
builds_source = ROOT / "references/Hexalith.Builds"
worktrees = []


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, source=ROOT, *, module=False):
    value = subprocess.run(arguments, cwd=source, env=environment if module else None,
                           capture_output=True, text=True, timeout=180)
    report["operations"].append({"command": arguments, "repository": str(source), "exit": value.returncode,
                                  "stdout": value.stdout, "stderr": value.stderr})
    save()
    assert value.returncode == 0, value.stderr
    return value.stdout.strip()


def get(endpoint, *, module=False):
    return json.loads(run(["gh", "api", endpoint], module=module))


staging = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                         capture_output=True, check=True).stdout
report["original_staging_sha256"] = hashlib.sha256(staging).hexdigest()
assert report["original_staging_sha256"] == initial["original_staging_sha256"]
run(["git", "fetch", "--no-recurse-submodules", "origin", "main"])
assert run(["git", "rev-parse", "origin/main"]) == report["base"]
assert run(["git", "rev-parse", "HEAD"], builds_source) == report["direct_gitlinks"]["Hexalith.Builds"]
assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], builds_source) == ""
for name, item in adoption["modules"].items():
    assert get("repos/Hexalith/" + name + "/git/ref/heads/main", module=True)["object"]["sha"] == item["adoption_sha"]
    assert get("repos/Hexalith/Hexalith.CiCd/git/ref/heads/delivered/" + name)["object"]["sha"] == report["base"]
try:
    run(["git", "worktree", "add", "--detach", str(job), report["base"]])
    worktrees.append((ROOT, job))
    direct = job / "references/Hexalith.Builds"
    assert direct.is_dir() and not any(direct.iterdir())
    direct.rmdir()
    run(["git", "worktree", "add", "--detach", str(direct), report["direct_gitlinks"]["Hexalith.Builds"]], builds_source)
    worktrees.append((builds_source, direct))
    for name in sources:
        shutil.copyfile(ROOT / name, job / name)
    run(["git", "add", "--", *sources], job)
    for name, item in adoption["modules"].items():
        run(["git", "update-index", "--add", "--cacheinfo", "160000," + item["adoption_sha"] + ",references/" + name], job)
    sys.path.insert(0, str(direct / "Github/lib"))
    from expected_state import Git
    from guard_tools import Tools
    import guard_commitlint
    directory = scratch / "guard-tools"
    directory.mkdir()
    tools = Tools(directory)
    message = ("docs(cicd): document verified Update branch ownership boundary\n\n"
               "Record the allowed server behavior and require product-only reapplication from current main when owned changes would be imported.\n")
    tools.lint_message(message, "qualified pilot policy")
    message_path = scratch / "message.txt"
    message_path.write_text(message)
    run(["git", "commit", "--file", str(message_path)], job)
    head = run(["git", "rev-parse", "HEAD"], job)
    assert run(["git", "rev-parse", "HEAD^"], job) == report["base"]
    paths = run(["git", "diff", "--name-only", report["base"], head], job).splitlines()
    assert set(paths) == set(sources) | {"references/" + name for name in adoption["modules"]}
    guard_commitlint.lint(Git(job), tools, event_name="push", event={}, frozen_head=head,
                         commit_range=(report["base"], head))
    assert subprocess.run(["git", "show-ref", "--verify", "--quiet", "refs/heads/" + report["branch"]], cwd=ROOT).returncode == 1
    run(["git", "update-ref", "refs/heads/" + report["branch"], head])
    report.update(head=head, changed_paths=paths, phase="full locked committed/live candidate validation",
                  validation_started_at=datetime.now(timezone.utc).isoformat())
    save()
    credential = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True, timeout=30).stdout.strip()
    validation_environment = dict(os.environ, GH_TOKEN=credential, GH_PROMPT_DISABLED="1", UV_CACHE_DIR=str(scratch / "uv-cache"))
    output_path = HERE / "qualified-policy-full-validation.log"
    with output_path.open("w") as output:
        process = subprocess.Popen(["uv", "run", "--locked", "--script", "tools/validate.py"], cwd=job,
                                   env=validation_environment, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        report["validation_pid"] = process.pid
        save()
        try:
            status = process.wait(timeout=2400)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            report["validation_outer_timeout"] = True
            raise
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    report.update(validation_exit=status, validation_log_sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),
                  validation_completed_at=datetime.now(timezone.utc).isoformat())
    verdicts = []
    for line in output_path.read_text().splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict) and set(value) == {"global", "modules"}:
            verdicts.append(value)
    assert len(verdicts) == 1
    report["verdict"] = verdicts[0]
    save()
    assert status == 0 and verdicts[0] == {"global": True, "modules": list(adoption["modules"])}
    for name, item in adoption["modules"].items():
        assert get("repos/Hexalith/" + name + "/git/ref/heads/main", module=True)["object"]["sha"] == item["adoption_sha"]
    assert run(["git", "rev-parse", "HEAD"], job) == head
    assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], job) == ""
    report.update(phase="complete", result="exact qualified-policy candidate passed full locked gate")
    save()
finally:
    cleanup_rows = []
    for source, worktree in reversed(worktrees):
        value = subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=source,
                               capture_output=True, text=True, timeout=120)
        cleanup_rows.append({"repository": str(source), "path": str(worktree), "exit": value.returncode, "stderr": value.stderr})
    report["worktree_cleanup"] = cleanup_rows
    after = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                           capture_output=True, check=True).stdout
    report["original_staging_preserved"] = after == staging
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    assert all(item["exit"] == 0 for item in cleanup_rows) and after == staging
    for source, worktree in worktrees:
        assert "worktree " + str(worktree) + "\n" not in run(["git", "worktree", "list", "--porcelain"], source) + "\n"
    report["all_temporary_worktree_metadata_removed"] = True
    save()
print(json.dumps({key: report[key] for key in ("base", "head", "verdict", "result", "original_staging_preserved")}, indent=2))
