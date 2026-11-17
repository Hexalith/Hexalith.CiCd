"""Qualify and land the Commons package-hook discovery fix from current main.

Run under run-with-temp. Uses the protected module token only for Commons
fetch/push. Does not initialize nested submodules in the original checkout.
After App adoption, the exact command is python3 references/Hexalith.Builds/check.py
on a standalone module job root whose Builds gitlink is a direct worktree of
the committed v6.2.0 pin. Manual dispatch/rerun is not used.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
COMMONS = ROOT / "references/Hexalith.Commons"
BUILDS = ROOT / "references/Hexalith.Builds"
NIGHT_MAIN = "aa694ae3d43f1645f741ae0844987ca2e7e0d347"
BUILDS_TAG = "v6.2.0"
BUILDS_SHA = "0ccd12af6576a3aac601340dec7dba53e86768c3"
BRANCH = "fix/commons-package-hook-discovery"
ALLOWED = (
    ".github/actions/after-unit-tests/action.yml",
    "scripts/pack-release-packages.py",
    "scripts/validate-consumer-package-references.py",
)
EXPECTED_FILES = [
    ".github/actions/after-unit-tests/action.yml",
    "scripts/pack-release-packages.py",
    "scripts/validate-consumer-package-references.py",
    "scripts/validate-nuget-packages.py",
]
EXPECTED_BASE_ERRORS = [
    ".github/actions/after-unit-tests/action.yml:10: local-script discovery: unresolved computed operand of unknown command: rm",
    ".github/actions/after-unit-tests/action.yml:9: local-script discovery: unsupported shell command substitution",
    "scripts/pack-release-packages.py:47: local-script discovery: unresolved computed subprocess env",
    "scripts/validate-consumer-package-references.py:159: local-script discovery: unresolved computed subprocess cwd",
]
MESSAGE = (
    "fix: make package-hook scripts statically discoverable\n"
    "\n"
    "Replace mktemp/rm command substitution and computed subprocess env/cwd\n"
    "so the nightly local-script scan can certify the package hook without\n"
    "changing the twelve-package pack, payload/symbol checks, or isolated\n"
    "consumer caches.\n"
)
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
assert "TMPDIR" in os.environ
scratch = Path(os.environ["TMPDIR"]).resolve() / "commons-scan-fix"
scratch.mkdir()
report_path = HERE / "land-commons-scan-fix.json"
assert not report_path.exists(), "Inspect exact partial remote results before any retry"
log_path = HERE / "land-commons-scan-fix.log"
commitlint_log = HERE / "land-commons-scan-fix-commitlint.log"
message_path = HERE / "land-commons-scan-fix.commitmsg"
message_path.write_text(MESSAGE)
report = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "profile": os.environ["GH_CONFIG_DIR"],
    "module_token_override_present": False,
    "manual_dispatch_or_rerun": False,
    "nested_submodule_initialization": False,
    "builds_tag": BUILDS_TAG,
    "builds_sha": BUILDS_SHA,
    "branch": BRANCH,
    "allowed_paths": list(ALLOWED),
    "operations": [],
    "push_attempted": False,
    "result": "pending",
}
module_environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                          GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    module_environment.pop(name, None)
check_environment = dict(os.environ, NUGET_PACKAGES=str(scratch / ".nuget/packages"),
                         NUGET_HTTP_CACHE_PATH=str(scratch / ".nuget/http"),
                         NUGET_PLUGINS_CACHE_PATH=str(scratch / ".nuget/plugins"),
                         DOTNET_CLI_HOME=str(scratch / ".dotnet"),
                         UV_CACHE_DIR=str(scratch / "uv-cache"),
                         RUNNER_TEMP=str(scratch / "runner-temp"))
for name in ("GH_TOKEN", "GITHUB_TOKEN"):
    check_environment.pop(name, None)
(scratch / "runner-temp").mkdir()
sys.path.insert(0, str(ROOT / "tools"))
from delivery_runtime import Git as ScanGit
from scan_discovery import Discovery

worktrees = []


def save():
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, repository, *, env=None, data=None, timeout=180):
    result = subprocess.run(arguments, cwd=repository, env=env, input=data, text=True,
                            capture_output=True, timeout=timeout)
    report["operations"].append({"command": arguments, "cwd": str(repository), "exit": result.returncode,
                                  "stdout": result.stdout[-8000:], "stderr": result.stderr[-8000:]})
    save()
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()


def original_nested_state():
    path = COMMONS / "references/Hexalith.Builds"
    assert not path.is_symlink()
    contents = sorted(entry.name for entry in path.iterdir()) if path.is_dir() else None
    assert contents in (None, []), "Original nested Builds path must remain uninitialized"
    return {"path": str(path), "exists": path.exists(), "contents": contents}


def discover(revision):
    files, errors = Discovery(ScanGit(COMMONS), revision).discover()
    return {"errors": errors, "files": sorted(files)}


def digest(repository, revision, path):
    blob = subprocess.check_output(["git", "show", revision + ":" + path], cwd=repository)
    return {"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}


report["original_nested_paths_before"] = original_nested_state()
save()
try:
    run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], COMMONS, env=module_environment)
    base = run(["git", "rev-parse", "origin/main"], COMMONS)
    assert base == NIGHT_MAIN, "Commons origin/main is no longer the recorded night head; reapply from current main"
    assert run(["git", "rev-parse", BUILDS_TAG + "^{commit}"], BUILDS) == BUILDS_SHA
    gitlink = run(["git", "ls-tree", base, "references/Hexalith.Builds"], COMMONS)
    assert gitlink == "160000 commit " + BUILDS_SHA + "\treferences/Hexalith.Builds"
    config = json.loads(subprocess.check_output(["git", "show", base + ":.github/hexalith-ci.json"], cwd=COMMONS, text=True))
    assert config["buildsTag"] == BUILDS_TAG and config["hooks"] == ["after-unit-tests"]
    report["base"] = base
    report["base_hexalith_ci"] = {"buildsTag": config["buildsTag"], "hooks": config["hooks"]}
    report["base_file_digests"] = {path: digest(COMMONS, base, path) for path in EXPECTED_FILES}
    report["base_discovery"] = discover(base)
    save()
    assert report["base_discovery"]["errors"] == EXPECTED_BASE_ERRORS
    assert report["base_discovery"]["files"] == EXPECTED_FILES

    existing = subprocess.run(["git", "show-ref", "--verify", "refs/heads/" + BRANCH],
                              cwd=COMMONS, capture_output=True, text=True)
    assert existing.returncode != 0, "Inspect existing product branch before recreating it"
    product = scratch / "product"
    run(["git", "worktree", "add", "-b", BRANCH, str(product), base], COMMONS)
    worktrees.append((COMMONS, product))
    apply = subprocess.run(["git", "apply", str(HERE / "scheduled-20261117-commons-scan-fix.diff")],
                           cwd=product, capture_output=True, text=True, timeout=60)
    report["operations"].append({"command": ["git", "apply", "scheduled-20261117-commons-scan-fix.diff"],
                                  "cwd": str(product), "exit": apply.returncode,
                                  "stdout": apply.stdout, "stderr": apply.stderr})
    save()
    assert apply.returncode == 0, apply.stderr
    changed = [path for path in run(["git", "diff", "--name-only", "-z"], product).split("\0") if path]
    assert set(changed) == set(ALLOWED), changed
    run(["git", "add", "--", *ALLOWED], product)
    staged = [path for path in run(["git", "diff", "--cached", "--name-only"], product).splitlines() if path]
    assert set(staged) == set(ALLOWED), staged

    tools_root = scratch / "builds-tools"
    run(["git", "worktree", "add", "--detach", str(tools_root), BUILDS_SHA], BUILDS)
    worktrees.append((BUILDS, tools_root))
    sys.path.insert(0, str(tools_root / "Github/lib"))
    from guard_tools import Tools
    tools_dir = scratch / "guard-tools"
    tools_dir.mkdir()
    tools = Tools(tools_dir)
    tools.lint_message(MESSAGE, "candidate message")
    verbose = subprocess.run(
        ["node", str(tools_dir / "node_modules/@commitlint/cli/cli.js"),
         "--config", str(tools_root / "Github/guard/commitlint.config.mjs"),
         "--edit", str(message_path), "--verbose", "--color=false"],
        cwd=product, env=tools.environment, capture_output=True, text=True, timeout=120)
    commitlint_log.write_text(verbose.stdout + verbose.stderr)
    report["commitlint"] = {"exit": verbose.returncode, "log": commitlint_log.name,
                            "config": str(tools_root / "Github/guard/commitlint.config.mjs"),
                            "cli": "@commitlint/cli from released v6.2.0 guard tools"}
    save()
    assert verbose.returncode == 0, verbose.stdout + verbose.stderr
    run(["git", "commit", "--file", str(message_path)], product)
    head = run(["git", "rev-parse", "HEAD"], product)
    assert run(["git", "rev-parse", "HEAD^"], product) == base
    assert run(["git", "log", "-1", "--format=%B"], product) == MESSAGE.rstrip("\n")
    report["head"] = head
    report["head_file_digests"] = {path: digest(COMMONS, head, path) for path in EXPECTED_FILES}
    report["changed_raw"] = run(["git", "diff", "--raw", base, head], product)
    report["unchanged_owned_proof"] = run(
        ["git", "diff", "--name-only", base, head, "--",
         ".github/workflows", ".github/hexalith-ci.json", ".github/dependabot.yml",
         "AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md",
         ".claude/settings.json", ".gitmodules", "references/Hexalith.Builds"],
        product)
    assert report["unchanged_owned_proof"] == ""
    report["head_discovery"] = discover(head)
    save()
    assert report["head_discovery"]["errors"] == []
    assert report["head_discovery"]["files"] == EXPECTED_FILES

    job = scratch / "Hexalith.Commons"
    run(["git", "worktree", "add", "--detach", str(job), head], COMMONS)
    worktrees.append((COMMONS, job))
    direct = job / "references/Hexalith.Builds"
    assert direct.is_dir() and not any(direct.iterdir())
    direct.rmdir()
    run(["git", "worktree", "add", "--detach", str(direct), BUILDS_SHA], BUILDS)
    worktrees.append((BUILDS, direct))
    assert run(["git", "rev-parse", "HEAD"], direct) == BUILDS_SHA
    assert run(["git", "rev-parse", BUILDS_TAG + "^{commit}"], direct) == BUILDS_SHA
    report["checker"] = {"job_root": str(job), "builds_direct_dependency": str(direct),
                         "command": ["python3", "references/Hexalith.Builds/check.py"]}
    save()
    print("Exact normal checker for Hexalith.Commons at " + head, flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(["python3", "references/Hexalith.Builds/check.py"],
                                   cwd=job, env=check_environment, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            status = process.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            report["checker"]["outer_timeout"] = True
            save()
            raise
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    report["checker"]["exit"] = status
    save()
    assert status == 0, "Normal shared checker failed"

    packages = scratch / "runner-temp" / "commons-packages"
    packages.mkdir()
    print("Retained package/consumer scripts at " + head, flush=True)
    for command in (
            ["python3", "scripts/pack-release-packages.py", str(packages), "0.0.0"],
            ["python3", "scripts/validate-nuget-packages.py", str(packages)],
            ["python3", "scripts/validate-consumer-package-references.py", str(packages)]):
        with log_path.open("a", encoding="utf-8") as log:
            log.write("\n+ " + " ".join(command) + "\n")
            log.flush()
            result = subprocess.run(command, cwd=job, env=check_environment, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=600)
        report["operations"].append({"command": command, "cwd": str(job), "exit": result.returncode,
                                      "stdout": "", "stderr": ""})
        save()
        assert result.returncode == 0, "product package/consumer script failed: " + command[1]
    nupkg = sorted(path.name for path in packages.glob("*.nupkg") if not path.name.endswith(".symbols.nupkg"))
    snupkg = sorted(path.name for path in packages.glob("*.snupkg"))
    report["package_consumer"] = {"nupkg": nupkg, "snupkg": snupkg, "nupkg_count": len(nupkg),
                                   "snupkg_count": len(snupkg), "log": log_path.name}
    save()
    assert len(nupkg) == 12 and len(snupkg) == 12

    run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], COMMONS, env=module_environment)
    assert run(["git", "rev-parse", "origin/main"], COMMONS) == base, "Main advanced during checking"
    assert run(["git", "rev-parse", "refs/heads/" + BRANCH], COMMONS) == head
    report["immediate_prepush_freshness_at"] = datetime.now(timezone.utc).isoformat()
    report["push_attempted"] = True
    save()
    run(["git", "push", "--porcelain", "origin", head + ":refs/heads/main"], COMMONS, env=module_environment)
    actual = json.loads(run(["gh", "api", "repos/Hexalith/Hexalith.Commons/git/ref/heads/main"], ROOT,
                            env=module_environment))
    assert actual["object"]["sha"] == head
    report["push_confirmed"] = True
    report["remote_main"] = actual["object"]["sha"]
    save()

    original_head = run(["git", "rev-parse", "HEAD"], COMMONS)
    report["original_checkout_before_ff"] = original_head
    run(["git", "-c", "core.hooksPath=/dev/null", "merge", "--ff-only", "origin/main"], COMMONS)
    assert run(["git", "rev-parse", "HEAD"], COMMONS) == head
    assert run(["git", "status", "--porcelain"], COMMONS) == ""
    report["original_checkout_after_ff"] = head
    report["result"] = "pass"
    save()
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
    assert report["original_nested_paths_after"] == report["original_nested_paths_before"]
    for source, worktree in worktrees:
        registered = subprocess.check_output(["git", "worktree", "list", "--porcelain"], cwd=source, text=True)
        assert "worktree " + str(worktree) + "\n" not in registered + "\n"
    report["all_temporary_worktree_metadata_removed"] = True
    save()
print(json.dumps({"result": report.get("result"), "base": report.get("base"), "head": report.get("head"),
                  "push_confirmed": report.get("push_confirmed"), "checker_exit": report.get("checker", {}).get("exit")},
                 indent=2))
