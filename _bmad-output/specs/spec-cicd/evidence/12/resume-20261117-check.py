"""Qualify committed AI.Tools registration and the local adopted snapshot.

Run through run-with-temp and the renderer's locked requirements. This reads
local Git objects only: no fetch, push, settings change, App selection,
dispatch or nested initialization in the persistent checkouts. It does not
authenticate current remote main or accept the story.
"""

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[4]
MODULE = SOURCE / "references/Hexalith.AI.Tools"
SIBLING_MODULE = SOURCE.parent / "conversations/references/Hexalith.AI.Tools"
PREP_HEAD = "cfd1ebea92587cdea41b9aa2cff47358bf2f32f6"
SCAN_HEAD = "3a4a78d91b36849c4700e8bc9aae74a1b91f2fba"
REGISTRATION = (
    "setup/Hexalith.AI.Tools.yml",
    "rendered/Hexalith.AI.Tools.perimeter.json",
    "rendered/Hexalith.AI.Tools/.github/dependabot.yml",
    "rendered/Hexalith.AI.Tools/.github/hexalith-ci.json",
    "rendered/Hexalith.AI.Tools/.github/workflows/ci.yml",
    "rendered/Hexalith.AI.Tools/.github/workflows/release.yml",
)
SIBLINGS = (
    "setup/Hexalith.Commons.yml",
    "setup/Hexalith.PolymorphicSerializations.yml",
    "setup/Hexalith.Conversations.yml",
)
CONCURRENT_UNTRACKED = (
    "_bmad-output/specs/spec-cicd/evidence/11/authenticate-scheduled-20261118.py",
)
scratch = Path(os.environ["TMPDIR"]).resolve()
candidate = scratch / "cicd-committed"
report = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "scope": "offline committed-current-main registration and local adopted-snapshot checker",
    "repository_remote_operations": False,
    "tool_downloads": "released integrity-locked tools; permitted by execution.md",
    "push_performed": False,
    "adoption_claimed": False,
    "story_accepted": False,
    "checks": {},
}


def command(arguments, cwd, timeout=180):
    result = subprocess.run(list(map(str, arguments)), cwd=cwd, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace"))
    return result.stdout


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def nested_builds_state(root=MODULE):
    path = root / "references/Hexalith.Builds"
    contents = sorted(entry.name for entry in path.iterdir()) if path.is_dir() else None
    return {"path": str(path), "exists": path.exists(), "contents": contents}


def run_checker(source, head, log_name, origin_note):
    job = scratch / ("ai-tools-" + log_name)
    if job.exists():
        shutil.rmtree(job)
    command(["git", "clone", "--quiet", "--no-hardlinks", "--no-recurse-submodules", source, job], SOURCE)
    command(["git", "checkout", "--quiet", "--detach", head], job)
    command(["git", "remote", "set-url", "origin", "https://github.com/Hexalith/Hexalith.AI.Tools.git"], job)
    command(["git", "update-ref", "refs/remotes/origin/main", head], job)
    config = json.loads((job / ".github/hexalith-ci.json").read_text())
    gitlink = command(["git", "ls-tree", "HEAD", "references/Hexalith.Builds"], job).decode().strip()
    builds_sha = gitlink.split()[2]
    direct = job / "references/Hexalith.Builds"
    if direct.exists():
        shutil.rmtree(direct)
    command(["git", "clone", "--quiet", "--no-hardlinks", "--no-recurse-submodules",
             SOURCE / "references/Hexalith.Builds", direct], SOURCE)
    command(["git", "checkout", "--quiet", "--detach", builds_sha], direct)
    tagged = command(["git", "rev-parse", config["buildsTag"] + "^{commit}"], direct).decode().strip()
    assert tagged == builds_sha, (tagged, builds_sha)
    log = HERE / log_name
    result = subprocess.run(["python3", "references/Hexalith.Builds/check.py"], cwd=job,
                            capture_output=True, timeout=1800)
    log.write_text(result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace"))
    return {
        "exit": result.returncode,
        "log": log.name,
        "job_head": head,
        "builds_tag": config["buildsTag"],
        "builds_sha": builds_sha,
        "origin_main": origin_note,
    }


try:
    assert "TMPDIR" in os.environ
    assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
    report["source_worktree"] = str(SOURCE)
    report["source_worktree_head"] = command(["git", "rev-parse", "HEAD"], SOURCE).decode().strip()
    report["observed_local_main"] = command(["git", "rev-parse", "main"], SOURCE).decode().strip()
    report["observed_local_origin_main"] = command(["git", "rev-parse", "origin/main"], SOURCE).decode().strip()
    report["original_nested_builds_before"] = nested_builds_state()
    assert report["original_nested_builds_before"]["contents"] in (None, [])
    report["sibling_nested_builds_before"] = nested_builds_state(SIBLING_MODULE)
    assert report["sibling_nested_builds_before"]["contents"] in (None, [])
    command(["git", "clone", "--quiet", "--no-hardlinks", "--no-recurse-submodules", SOURCE, candidate], SOURCE)
    command(["git", "checkout", "--quiet", "--detach", report["source_worktree_head"]], candidate)
    for relative in CONCURRENT_UNTRACKED:
        assert not (candidate / relative).exists(), relative
    report["checks"]["concurrent_untracked_story11_files_excluded"] = "pass"
    builds = candidate / "references/Hexalith.Builds"
    if builds.exists():
        shutil.rmtree(builds)
    command(["git", "clone", "--quiet", "--no-hardlinks", "--no-recurse-submodules",
             SOURCE / "references/Hexalith.Builds", builds], SOURCE)
    tag = (candidate / "builds-version").read_text().strip()
    command(["git", "checkout", "--quiet", "--detach", tag], builds)
    report["builds_tag"] = tag
    report["builds_source"] = command(["git", "rev-parse", "HEAD"], builds).decode().strip()
    report["builds_tagged"] = command(["git", "rev-parse", tag + "^{commit}"], builds).decode().strip()
    assert report["builds_source"] == report["builds_tagged"]
    checks = load("_story12_current_global", candidate / "tools/check_global.py")
    checks.check_committed_inputs(candidate)
    report["checks"]["committed_render_inputs"] = "pass"
    checks.check_committed_render(candidate)
    report["checks"]["committed_render"] = "pass"
    with checks.selected_contract(candidate) as contract:
        checks.check_render(candidate, contract)
        report["checks"]["render_reproducibility"] = "pass"
        registrations = checks.renderer.registry(candidate)
        checks.check_documents(candidate, registrations, contract)
        report["checks"]["schemas_and_caller_interfaces"] = "pass"
    names = [name for name, _ in registrations]
    report["registration_names"] = names
    assert "Hexalith.AI.Tools" in names
    for sibling in ("Hexalith.Commons", "Hexalith.PolymorphicSerializations", "Hexalith.Conversations"):
        assert sibling in names, sibling
        assert (candidate / f"setup/{sibling}.yml").is_file()
    report["checks"]["sibling_registrations_preserved"] = "pass"
    validator = load("_story12_current_validator", candidate / "tools/validate.py")
    validator.check_submodule(candidate, "Hexalith.AI.Tools")
    report["checks"]["direct_submodule_declaration"] = "pass"
    link = command(["git", "ls-tree", "HEAD", "references/Hexalith.AI.Tools"], candidate).decode().strip()
    report["recorded_module_gitlink"] = link
    module_head = link.split()[2]
    assert link.startswith("160000 commit ") and link.endswith("\treferences/Hexalith.AI.Tools")
    config = json.loads((candidate / REGISTRATION[3]).read_text())
    assert config["solution"] == "none" and config["buildsTag"] == tag
    assert config["hooks"] == config["submodules"] == config["codeql"] == []
    assert config["jobs"] == {} and config["tests"]["integration"] == [] and config["tests"]["exclude"] == {}
    assert not any(config[key] for key in ("browsers", "dapr", "registry"))
    dependabot = (candidate / REGISTRATION[2]).read_text()
    assert dependabot == "version: 2\nupdates: []\n"
    setup = (candidate / REGISTRATION[0]).read_text()
    assert setup == "solution: none\n"
    report["checks"]["explicit_no_solution_empty_inventory_configuration"] = "pass"
    local_head = command(["git", "rev-parse", "HEAD"], MODULE).decode().strip()
    report["local_module_head"] = local_head
    report["local_module_origin_main"] = command(
        ["git", "rev-parse", "refs/remotes/origin/main"], MODULE).decode().strip()
    report["local_origin_main_is_authenticated_remote"] = False
    assert command(["git", "merge-base", "--is-ancestor", PREP_HEAD, local_head], MODULE) == b""
    assert not command(["git", "ls-tree", PREP_HEAD, "package.json", "package-lock.json"], MODULE)
    assert command(["git", "ls-tree", PREP_HEAD, "commitlint.config.mjs"], MODULE)
    assert not command(["git", "ls-tree", local_head, "package.json", "package-lock.json",
                        "commitlint.config.mjs"], MODULE)
    for path in ("hexalith-git-instructions.md", "hexalith-llm-instructions.md", "README.md"):
        prepared = command(["git", "rev-parse", PREP_HEAD + ":" + path], MODULE)
        adopted = command(["git", "rev-parse", local_head + ":" + path], MODULE)
        assert prepared == adopted, path
    entrypoints = []
    for path in ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"):
        entrypoints.append(command(["git", "rev-parse", local_head + ":" + path], MODULE))
    assert len(set(entrypoints)) == 1
    module_config = json.loads(command(["git", "show", local_head + ":.github/hexalith-ci.json"], MODULE))
    module_builds = command(["git", "ls-tree", local_head, "references/Hexalith.Builds"], MODULE).decode().strip()
    report["local_module_builds_tag"] = module_config["buildsTag"]
    report["local_module_builds_gitlink"] = module_builds
    report["rendered_versus_local_module_pin"] = {
        "rendered_builds_tag": tag,
        "local_module_builds_tag": module_config["buildsTag"],
        "classification": "local snapshot observation; not a fresh remote delivery readback",
    }
    report["checks"]["published_preparation_and_delivery_owned_deletion"] = "pass"
    report["cicd_gitlink_head"] = module_head
    report["sibling_module_source"] = str(SIBLING_MODULE)
    assert command(["git", "rev-parse", SCAN_HEAD + "^{commit}"], SIBLING_MODULE).decode().strip() == SCAN_HEAD
    assert command(["git", "merge-base", "--is-ancestor", local_head, SCAN_HEAD], SIBLING_MODULE) == b""
    scan_config = json.loads(command(["git", "show", SCAN_HEAD + ":.github/hexalith-ci.json"], SIBLING_MODULE))
    scan_builds = command(["git", "ls-tree", SCAN_HEAD, "references/Hexalith.Builds"], SIBLING_MODULE).decode().strip()
    report["sibling_scan_head"] = SCAN_HEAD
    report["sibling_scan_builds_tag"] = scan_config["buildsTag"]
    report["sibling_scan_builds_gitlink"] = scan_builds
    assert scan_config["solution"] == "none" and scan_config["buildsTag"] == tag
    assert not command(["git", "ls-tree", SCAN_HEAD, "package.json", "package-lock.json",
                        "commitlint.config.mjs"], SIBLING_MODULE)
    for path in ("hexalith-git-instructions.md", "hexalith-llm-instructions.md", "README.md"):
        assert command(["git", "rev-parse", PREP_HEAD + ":" + path], SIBLING_MODULE) == command(
            ["git", "rev-parse", SCAN_HEAD + ":" + path], SIBLING_MODULE)
    report["checks"]["sibling_local_scan_head_matches_current_render_pin"] = "pass"
    stale = run_checker(
        MODULE, local_head, "resume-20261117-checker-stale-gitlink.txt",
        "CiCd gitlink snapshot HEAD; not a fresh remote readback")
    report["checks"]["standalone_checker_committed_gitlink_snapshot"] = stale
    assert stale["exit"] == 1, stale
    current = run_checker(
        SIBLING_MODULE, SCAN_HEAD, "resume-20261117-checker.txt",
        "sibling local origin/main object; not a fresh authenticated fetch")
    report["checks"]["standalone_normal_checker"] = current
    assert current["exit"] == 0, (HERE / current["log"]).read_text()[-4000:]
    report["checks"]["committed_gitlink_lags_sibling_local_scan_head"] = "recorded; gitlink not updated without authenticated fetch"
    for suite in ("render", "validate"):
        arguments = ["uv", "run", "--locked", "--script", "--python", sys.executable,
                     candidate / f"tools/tests/test_{suite}.py"]
        result = subprocess.run(arguments, cwd=candidate, capture_output=True, timeout=900)
        output = result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")
        log = HERE / f"resume-20261117-{suite}.txt"
        log.write_text(output)
        report["checks"][f"existing_{suite}_suite"] = {
            "exit": result.returncode,
            "tests": int(re.search(r"Ran (\d+) tests?", output).group(1)),
            "log": log.name,
        }
        assert result.returncode == 0, output[-4000:]
    builds_tests = (
        "test_release_build.BuildTests.test_none_payload_does_not_execute_sdk_or_submodules",
        "test_release_version.ReleaseVersionTests.test_no_version_tagless_or_at_base_has_explicit_noop",
        "test_release_version.ReleaseVersionTests.test_first_release_analyzes_full_history_and_is_exactly_one",
        "test_guard.GuardTests.test_solution_none_has_the_same_guard_enforcement",
    )
    builds_result = subprocess.run(
        [sys.executable, "-m", "unittest", *builds_tests],
        cwd=builds / "Github/lib/tests", capture_output=True, timeout=900)
    builds_output = builds_result.stdout.decode(errors="replace") + builds_result.stderr.decode(errors="replace")
    builds_log = HERE / "resume-20261117-builds-matrix.txt"
    builds_log.write_text(builds_output)
    report["checks"]["released_builds_empty_inventory_and_no_release_tests"] = {
        "exit": builds_result.returncode,
        "tests": builds_tests,
        "log": builds_log.name,
    }
    assert builds_result.returncode == 0, builds_output[-4000:]
    report.update(
        result="pass",
        candidate_head=command(["git", "rev-parse", "HEAD"], candidate).decode().strip(),
        registration_paths={relative: {
            "sha256": hashlib.sha256((candidate / relative).read_bytes()).hexdigest(),
            "git_mode": command(["git", "ls-tree", "HEAD", relative], candidate).decode().split()[0],
        } for relative in REGISTRATION},
        pending=["fresh authenticated remote-main and immutable-release readbacks",
                 "story 11 genuine scheduled-night checkpoint and acceptance",
                 "ordered AD-21 live preconditions including main/v* rulesets",
                 "full committed/global/live-module tools/validate.py verdict",
                 "authenticated App adoption commit, owned/foreign tree and green hosted CI",
                 "next genuine adopted-module scheduled release/scan/delivery outcomes"],
    )
except Exception as error:
    report.update(result="failed", error=str(error)[-8000:])
    raise
finally:
    after = nested_builds_state()
    sibling_after = nested_builds_state(SIBLING_MODULE)
    report["original_nested_builds_after"] = after
    report["sibling_nested_builds_after"] = sibling_after
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    (HERE / "resume-20261117-check.json").write_text(json.dumps(report, indent=2) + "\n")
    before = report.get("original_nested_builds_before")
    sibling_before = report.get("sibling_nested_builds_before")
    if before is not None and after != before:
        raise RuntimeError("umbrella nested Builds path changed: " + json.dumps({"before": before, "after": after}))
    if sibling_before is not None and sibling_after != sibling_before:
        raise RuntimeError("sibling nested Builds path changed: " + json.dumps(
            {"before": sibling_before, "after": sibling_after}))

print("Committed registration and local adopted-snapshot checker finished; live acceptance remains gated.")
