"""Run each pilot's exact normal checker in a disposable standalone module job.

Usage under run-with-temp: python3 post-adoption-check.py TAG COMMONS_BASE
COMMONS_HEAD POLY_BASE POLY_HEAD. Save stdout/stderr alongside the report.
The original CiCd checkouts' nested Builds paths must remain empty. Each
standalone module is the job root; a separate worktree of CiCd's already
root-declared Builds repository supplies that job's direct dependency.
"""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("builds_tag")
parser.add_argument("commons_base")
parser.add_argument("commons_head")
parser.add_argument("poly_base")
parser.add_argument("poly_head")
args = parser.parse_args()
assert re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", args.builds_tag)
revisions = {MODULES[0]: (args.commons_base, args.commons_head),
             MODULES[1]: (args.poly_base, args.poly_head)}
assert all(re.fullmatch(r"[a-f0-9]{40}", sha) for pair in revisions.values() for sha in pair)
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
scratch = Path(os.environ["TMPDIR"]).resolve() / "standalone-pilot-checks"
scratch.mkdir()
report_path = HERE / "post-adoption-check.json"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "builds_tag": args.builds_tag,
          "layout": "standalone module job root with direct Builds worktree from root-declared repository",
          "product_output_log": "post-adoption-check.log", "modules": {}, "operations": [],
          "nested_submodule_initialization": False}
environment = dict(os.environ, NUGET_PACKAGES=str(scratch / ".nuget/packages"),
                   NUGET_HTTP_CACHE_PATH=str(scratch / ".nuget/http"),
                   NUGET_PLUGINS_CACHE_PATH=str(scratch / ".nuget/plugins"),
                   DOTNET_CLI_HOME=str(scratch / ".dotnet"), UV_CACHE_DIR=str(scratch / "uv-cache"))
fetch_environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                         GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    fetch_environment.pop(name, None)


def save():
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, repository, *, env=None):
    result = subprocess.run(arguments, cwd=repository, env=env, text=True, capture_output=True, timeout=120)
    report["operations"].append({"command": arguments, "cwd": str(repository), "exit": result.returncode,
                                  "stdout": result.stdout, "stderr": result.stderr})
    save()
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def original_nested_state():
    result = {}
    for name in MODULES:
        path = ROOT / "references" / name / "references/Hexalith.Builds"
        assert not path.is_symlink()
        contents = sorted(entry.name for entry in path.iterdir()) if path.is_dir() else None
        assert contents in (None, []), "Original nested Builds path must remain uninitialized"
        result[name] = {"path": str(path), "exists": path.exists(), "contents": contents}
    return result


original = original_nested_state()
report["original_nested_paths_before"] = original
builds_source = ROOT / "references/Hexalith.Builds"
tag_sha = run(["git", "rev-parse", args.builds_tag + "^{commit}"], builds_source)
report["builds_sha"] = tag_sha
worktrees = []
try:
    for name, (base, head) in revisions.items():
        source = ROOT / "references" / name
        run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], source, env=fetch_environment)
        assert run(["git", "rev-parse", "origin/main"], source) == base
        assert run(["git", "rev-parse", head + "^{commit}"], source) == head
        job = scratch / name
        run(["git", "worktree", "add", "--detach", str(job), head], source)
        worktrees.append((source, job))
        config = json.loads((job / ".github/hexalith-ci.json").read_text())
        assert config["buildsTag"] == args.builds_tag and config["submodules"] == []
        gitlink = run(["git", "ls-tree", head, "references/Hexalith.Builds"], source)
        assert gitlink == "160000 commit " + tag_sha + "\treferences/Hexalith.Builds"
        direct = job / "references/Hexalith.Builds"
        assert direct.is_dir() and not any(direct.iterdir())
        direct.rmdir()
        run(["git", "worktree", "add", "--detach", str(direct), tag_sha], builds_source)
        worktrees.append((builds_source, direct))
        report["modules"][name] = {"base": base, "head": head, "job_root": str(job),
                                   "builds_direct_dependency": str(direct), "builds_sha": tag_sha}
        save()
        print("Exact normal checker for " + name + " at " + head, flush=True)
        # No injected transport, configuration or checker override is used.
        command = ["python3", "references/Hexalith.Builds/check.py"]
        report["modules"][name]["checker_command"] = command
        process = subprocess.Popen(command, cwd=job, env=environment, start_new_session=True)
        try:
            status = process.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            report["modules"][name]["checker_outer_timeout"] = True
            raise
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        report["modules"][name]["checker_exit"] = status
        save()
        assert status == 0, "Normal shared checker failed"
    for name, (base, head) in revisions.items():
        source = ROOT / "references" / name
        run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], source, env=fetch_environment)
        assert run(["git", "rev-parse", "origin/main"], source) == base, "Main advanced during checking"
        report["modules"][name]["final_all_module_freshness"] = "pass"
    report["result"] = "pass"
finally:
    cleanup = []
    for source, worktree in reversed(worktrees):
        result = subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                                cwd=source, capture_output=True, text=True, timeout=120)
        cleanup.append({"repository": str(source), "path": str(worktree), "exit": result.returncode,
                        "stderr": result.stderr})
    report["worktree_cleanup"] = cleanup
    report["original_nested_paths_after"] = original_nested_state()
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    assert all(item["exit"] == 0 for item in cleanup), "Temporary worktree cleanup failed"
    assert report["original_nested_paths_after"] == original
    for source, worktree in worktrees:
        registered = run(["git", "worktree", "list", "--porcelain"], source)
        assert "worktree " + str(worktree) + "\n" not in registered + "\n"
    report["all_temporary_worktree_metadata_removed"] = True
    save()
