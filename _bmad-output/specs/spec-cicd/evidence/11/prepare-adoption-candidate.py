"""Commit one isolated pilot adoption candidate without changing original staging.

Run under run-with-temp. The candidate branch survives; all disposable worktree
metadata is removed. No module-main or delivery-triggering push occurs here.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BRANCH = "cicd-pilot-adoption-20261116"
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
SOURCE = ("tools/deliver.py", "tools/delivery_runtime.py", "tools/tests/test_deliver.py", "tools/tests/test_delivery_runtime.py")
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
report_path = HERE / "adoption-candidate.json"
assert not report_path.exists(), "Inspect existing candidate instead of repeating preparation"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "branch": BRANCH,
          "builds_tag": "v6.0.6", "push_performed": False, "operations": []}
scratch = Path(os.environ["TMPDIR"]) / "adoption-candidate-preparation"
scratch.mkdir()
job = scratch / "cicd"
builds = ROOT / "references/Hexalith.Builds"
worktrees = []


def save():
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, repository):
    result = subprocess.run(arguments, cwd=repository, capture_output=True, text=True, timeout=180)
    report["operations"].append({"command": arguments, "cwd": str(repository), "exit": result.returncode,
                                  "stdout": result.stdout, "stderr": result.stderr})
    save()
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


staging = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                         capture_output=True, check=True).stdout
report["original_staging_sha256"] = hashlib.sha256(staging).hexdigest()
run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], ROOT)
base = run(["git", "rev-parse", "origin/main"], ROOT)
assert base == run(["git", "rev-parse", "HEAD"], ROOT), "Reconcile upstream source before copying selected changes"
report["base"] = base
preparation = json.loads((HERE / "local-product-preparation.json").read_text())
proof = json.loads((HERE / "pre-adoption-verification.json").read_text())
assert proof["result"] == "pass" and proof["builds_tag"] == "v6.0.6"
links = {"Hexalith.Builds": "fdda17c0a4538b0f7c99f813c20ca24b49006530"}
for name in MODULES:
    assert proof["modules"][name]["head"] == preparation["modules"][name]["head"]
    links[name] = preparation["modules"][name]["head"]
assert run(["git", "rev-parse", "v6.0.6^{commit}"], builds) == links["Hexalith.Builds"]
assert run(["git", "rev-parse", "HEAD"], builds) == links["Hexalith.Builds"]
assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], builds) == ""
try:
    run(["git", "worktree", "add", "-b", BRANCH, str(job), base], ROOT)
    worktrees.append((ROOT, job))
    direct = job / "references/Hexalith.Builds"
    assert direct.is_dir() and not any(direct.iterdir())
    direct.rmdir()
    run(["git", "worktree", "add", "--detach", str(direct), links["Hexalith.Builds"]], builds)
    worktrees.append((builds, direct))
    paths = ["builds-version", *SOURCE, *("setup/" + name + ".yml" for name in MODULES)]
    paths += [str(path.relative_to(ROOT)) for path in (ROOT / "rendered").rglob("*") if path.is_file() and path.name != ".gitkeep"]
    for relative in paths:
        source, target = ROOT / relative, job / relative
        assert source.is_file() and not source.is_symlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(source.stat().st_mode & 0o777)
    run(["git", "add", "--", *paths], job)
    for name, sha in links.items():
        run(["git", "update-index", "--add", "--cacheinfo", "160000", sha, "references/" + name], job)
    sys.path.insert(0, str(builds / "Github/lib"))
    from guard_tools import Tools
    tools_path = scratch / "guard-tools"
    tools_path.mkdir()
    tools = Tools(tools_path)
    message = ("build(cicd): adopt Commons and PolymorphicSerializations\n\n"
               "Preserve package and consumer checks through Commons' product hook.\n"
               "Pin released publication verification and deliver both pilots' owned perimeter.\n")
    tools.lint_message(message, "CiCd adoption candidate")
    message_path = scratch / "message.txt"
    message_path.write_text(message)
    run(["git", "commit", "--file", str(message_path)], job)
    head = run(["git", "rev-parse", "HEAD"], job)
    from expected_state import Git
    import guard_commitlint
    guard_commitlint.lint(Git(job), tools, event_name="push", event={}, frozen_head=head, commit_range=(base, head))
    assert run(["git", "diff", base, head, "--", ".gitmodules"], job) == ""
    assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], job) == ""
    run(["uv", "run", "--locked", "--script", "tools/render.py", "--check"], job)
    # Reuse the production committed-input/render/contract checks with the
    # production locked dependency header, without rerunning the full verdict.
    driver = scratch / "committed-check.py"
    header = re.search(r"(?ms)^# /// script\n.*?^# ///\n", (job / "tools/check_global.py").read_text()).group()
    driver.write_text(header + "\nimport pathlib,sys\nsys.dont_write_bytecode=True\np=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(p/'tools'))\nimport check_global as c\nc.check_committed_inputs(p)\nc.check_committed_render(p)\nwith c.selected_contract(p) as contract:\n c.check_render(p,contract)\n c.check_documents(p,c.renderer.registry(p),contract)\nprint('Committed inputs/render and tagged schema/caller contracts: pass')\n")
    shutil.copyfile(job / "tools/check_global.py.lock", driver.with_suffix(".py.lock"))
    run(["uv", "run", "--locked", "--script", str(driver), str(job)], job)
    changed = run(["git", "diff", "--name-only", base, head], job).splitlines()
    assert set(changed) == set(paths) | {"references/" + name for name in links}
    report.update(head=head, direct_gitlinks=links, changed_paths=changed,
                  committed_render_input_contract_checks="pass", commit_and_range_policy="pass",
                  source_file_sha256={path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCE},
                  full_live_candidate_verdict="pending live preparation mains", result="committed local candidate ready")
    save()
finally:
    cleanup = []
    for source, worktree in reversed(worktrees):
        result = subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=source,
                                capture_output=True, text=True, timeout=120)
        cleanup.append({"repository": str(source), "path": str(worktree), "exit": result.returncode, "stderr": result.stderr})
    report["temporary_worktree_cleanup"] = cleanup
    after = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                           capture_output=True, check=True).stdout
    report["original_staging_preserved"] = after == staging
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    assert all(row["exit"] == 0 for row in cleanup) and after == staging
    for source, worktree in worktrees:
        assert "worktree " + str(worktree) + "\n" not in run(["git", "worktree", "list", "--porcelain"], source) + "\n"
    report["all_temporary_worktree_metadata_removed"] = True
    save()
print(json.dumps({key: report[key] for key in ("branch", "base", "head", "result", "original_staging_preserved")}, indent=2))
