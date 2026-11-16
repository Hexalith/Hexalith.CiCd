"""Record the qualified renderer fixture correction in the isolated candidate."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
path = HERE / "adoption-candidate.json"
old = json.loads(path.read_text())
backup = HERE / "adoption-candidate-1.json"
assert not backup.exists()
failed = json.loads((HERE / "preparation-publication-and-candidate-validation.json").read_text())
assert failed["candidate"] == old["head"] and failed["verdict"]["global"] is False
source = "tools/tests/test_render.py"
qualification = {"source_sha256": hashlib.sha256((ROOT / source).read_bytes()).hexdigest(), "interpreters": {}}
for version in ("312", "314"):
    log = HERE / ("render-permission-fixture-python" + version + ".log")
    text = log.read_text()
    assert "Ran 32 tests" in text and text.rstrip().endswith("OK")
    qualification["interpreters"][version] = {"tests": 32, "result": "pass", "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()}
(HERE / "render-permission-fixture-qualification.json").write_text(json.dumps(qualification, indent=2) + "\n")
scratch = Path(os.environ["TMPDIR"]) / "candidate-fixture-correction"
scratch.mkdir()
job = scratch / "cicd"
operations = []


def run(arguments, repository):
    result = subprocess.run(arguments, cwd=repository, capture_output=True, text=True, timeout=180)
    operations.append({"command": arguments, "cwd": str(repository), "exit": result.returncode,
                       "stdout": result.stdout, "stderr": result.stderr})
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


staging = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                         capture_output=True, check=True).stdout
assert hashlib.sha256(staging).hexdigest() == old["original_staging_sha256"]
run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], ROOT)
assert run(["git", "rev-parse", "origin/main"], ROOT) == old["base"]
assert run(["git", "rev-parse", "refs/heads/" + old["branch"]], ROOT) == old["head"]
run(["git", "worktree", "add", "--detach", str(job), old["head"]], ROOT)
try:
    shutil.copyfile(ROOT / source, job / source)
    run(["git", "add", "--", source], job)
    sys.path.insert(0, str(ROOT / "references/Hexalith.Builds/Github/lib"))
    from guard_tools import Tools
    from expected_state import Git
    import guard_commitlint
    directory = scratch / "guard-tools"
    directory.mkdir()
    tools = Tools(directory)
    message = "test(render): make permission contract fixtures explicit\n\nQualify real tagged restore permissions and select a synthetic read-only baseline for the transition check.\n"
    tools.lint_message(message, "renderer fixture correction")
    message_path = scratch / "message.txt"
    message_path.write_text(message)
    run(["git", "commit", "--file", str(message_path)], job)
    head = run(["git", "rev-parse", "HEAD"], job)
    assert run(["git", "rev-parse", "HEAD^"], job) == old["head"]
    assert run(["git", "diff", "--name-only", old["head"], head], job).splitlines() == [source]
    assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], job) == ""
    guard_commitlint.lint(Git(job), tools, event_name="push", event={}, frozen_head=head, commit_range=(old["base"], head))
    run(["git", "update-ref", "refs/heads/" + old["branch"], head, old["head"]], ROOT)
    shutil.copyfile(path, backup)
    revised = dict(old)
    revised.update(head=head, revised_at=datetime.now(timezone.utc).isoformat(), parent_candidate=old["head"],
                   prior_failed_verdict="preparation-publication-and-candidate-validation.json",
                   full_live_candidate_verdict="pending revised full gate",
                   result="fixture-only revised candidate ready")
    revised["source_file_sha256"] = dict(old["source_file_sha256"], **{source: qualification["source_sha256"]})
    revised["changed_paths"] = run(["git", "diff", "--name-only", old["base"], head], job).splitlines()
    revised["fixture_correction"] = {"changed_path": source, "qualification": qualification,
                                     "production_renderer_validator_unchanged": True, "operations": operations}
    path.write_text(json.dumps(revised, indent=2) + "\n")
finally:
    run(["git", "worktree", "remove", "--force", str(job)], ROOT)
    assert "worktree " + str(job) + "\n" not in run(["git", "worktree", "list", "--porcelain"], ROOT) + "\n"
    after = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                           capture_output=True, check=True).stdout
    assert after == staging
revised = json.loads(path.read_text())
revised["revision_original_staging_preserved"] = True
revised["revision_temporary_worktree_metadata_removed"] = True
path.write_text(json.dumps(revised, indent=2) + "\n")
print(json.dumps({key: revised[key] for key in ("base", "parent_candidate", "head", "result", "revision_original_staging_preserved")}, indent=2))
