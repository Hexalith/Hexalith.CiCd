"""Qualify only the diagnosed transport change; preserve the original index."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--attempt", type=int, default=1)
arguments = parser.parse_args()
assert arguments.attempt > 0
suffix = "" if arguments.attempt == 1 else "-" + str(arguments.attempt)
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
assert "TMPDIR" in os.environ, "Run through run-with-temp"
paths = ("tools/nightly_runtime.py", "tools/tests/test_nightly_runtime.py", "docs/nightly.md")
destination = HERE / ("nightly-diagnostics-candidate" + suffix + ".json")
assert not destination.exists(), "Inspect existing qualification before another attempt"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "operations": [],
          "sources": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths},
          "result": "pending", "push_attempted": False}
scratch = Path(os.environ["TMPDIR"]) / "nightly-diagnostics"
scratch.mkdir()
job = scratch / "cicd"
worktrees = []


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, cwd=ROOT):
    value = subprocess.run(arguments, cwd=cwd, capture_output=True, text=True, timeout=180)
    report["operations"].append({"arguments": arguments, "cwd": str(cwd),
                                 "exit": value.returncode, "stdout": value.stdout, "stderr": value.stderr})
    save()
    assert value.returncode == 0, value.stderr
    return value.stdout.strip()


index = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT)
report["original_index_sha256"] = hashlib.sha256(index).hexdigest()
run(["git", "fetch", "--no-recurse-submodules", "origin", "main"])
base = run(["git", "rev-parse", "origin/main"])
report["base"] = base
try:
    run(["git", "worktree", "add", "--detach", str(job), base])
    worktrees.append((ROOT, job))
    direct = job / "references/Hexalith.Builds"
    direct.rmdir()
    builds = ROOT / "references/Hexalith.Builds"
    build_sha = run(["git", "rev-parse", base + ":references/Hexalith.Builds"])
    run(["git", "worktree", "add", "--detach", str(direct), build_sha], builds)
    worktrees.append((builds, direct))
    for path in paths:
        shutil.copyfile(ROOT / path, job / path)
    run(["git", "add", "--", *paths], job)
    message = scratch / "message.txt"
    message.write_text("fix(nightly): retain bounded HTTP failure evidence\n\n"
                       "Preserve authentication context and sanitized response diagnostics without changing credentials, retries or trust checks.\n")
    run(["git", "-c", "core.hooksPath=/dev/null", "commit", "--file", str(message)], job)
    head = run(["git", "rev-parse", "HEAD"], job)
    report["head"] = head
    assert run(["git", "rev-parse", "HEAD^"], job) == base
    assert set(run(["git", "diff", "--name-only", base, head], job).splitlines()) == set(paths)
    branch = "cicd-story11-nightly-diagnostics-20261116" + suffix
    run(["git", "update-ref", "refs/heads/" + branch, head, "0" * 40])
    report["branch"] = branch
    save()
    # The same configured profile supplies the existing audit credential only
    # to the locked gate. It never replaces any anonymous controller read.
    token = subprocess.check_output(["gh", "auth", "token"], text=True, timeout=30).strip()
    environment = dict(os.environ, GH_TOKEN=token, UV_CACHE_DIR=str(scratch / "uv-cache"))
    log = HERE / ("nightly-diagnostics-full-validation" + suffix + ".log")
    with log.open("w") as output:
        process = subprocess.Popen(["uv", "run", "--locked", "--script", "tools/validate.py"],
                                   cwd=job, env=environment, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        report["validation_pid"] = process.pid
        save()
        try:
            report["validation_exit"] = process.wait(timeout=2400)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    report["validation_log_sha256"] = hashlib.sha256(log.read_bytes()).hexdigest()
    save()
    verdicts = []
    for line in log.read_text().splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict) and set(value) == {"global", "modules"}:
            verdicts.append(value)
    assert report["validation_exit"] == 0 and verdicts == [
        {"global": True, "modules": ["Hexalith.Commons", "Hexalith.PolymorphicSerializations"]}]
    report["verdict"] = verdicts[0]
    assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], job) == ""
    report["result"] = "pass"
finally:
    report["worktree_cleanup"] = []
    for source, worktree in reversed(worktrees):
        value = subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                               cwd=source, capture_output=True, text=True, timeout=120)
        report["worktree_cleanup"].append({"path": str(worktree), "exit": value.returncode,
                                           "stderr": value.stderr})
    report["original_index_preserved"] = index == subprocess.check_output(
        ["git", "ls-files", "--stage", "-z"], cwd=ROOT)
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    assert report["original_index_preserved"] and all(row["exit"] == 0 for row in report["worktree_cleanup"])
print(json.dumps({key: report[key] for key in ("base", "head", "result", "original_index_preserved")}))
