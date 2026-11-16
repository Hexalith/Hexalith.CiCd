"""Qualify AI.Tools registration in the isolated resume worktree.

Run through run-with-temp and the renderer's locked requirements. This reads
local repositories only; it neither fetches current remote state nor establishes
adoption, a global verdict, or acceptance. Historical worktrees remain untouched.
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
PREPARED = SOURCE
BUILDS = SOURCE.parent / "cicd-story-12/references/Hexalith.Builds"
MODULE = PREPARED.parent / "ai-tools-story-12"
MODULE_HEAD = "cfd1ebea92587cdea41b9aa2cff47358bf2f32f6"
ADDITIONS = (
    "setup/Hexalith.AI.Tools.yml",
    "rendered/Hexalith.AI.Tools.perimeter.json",
    "rendered/Hexalith.AI.Tools/.github/dependabot.yml",
    "rendered/Hexalith.AI.Tools/.github/hexalith-ci.json",
    "rendered/Hexalith.AI.Tools/.github/workflows/ci.yml",
    "rendered/Hexalith.AI.Tools/.github/workflows/release.yml",
)
scratch = Path(os.environ["TMPDIR"]).resolve()
candidate = scratch / "cicd-registration"
report = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "scope": "offline isolated-worktree committed-source registration qualification",
    "repository_remote_operations": False,
    "tool_downloads": "released integrity-locked tools; permitted by execution.md",
    "push_performed": False,
    "adoption_performed": False,
    "story_accepted": False,
    "checks": {},
}


def command(arguments, cwd=SOURCE):
    result = subprocess.run(list(map(str, arguments)), cwd=cwd, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace"))
    return result.stdout


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


try:
    base = command(["git", "rev-parse", "HEAD"]).decode().strip()
    report["source_worktree"] = str(SOURCE)
    report["source_worktree_head"] = base
    report["observed_local_main"] = command(["git", "rev-parse", "main"]).decode().strip()
    report["observed_local_origin_main"] = command(["git", "rev-parse", "origin/main"]).decode().strip()
    report["unrelated_source_worktree_changes_included"] = False
    report["uncommitted_registration_inputs"] = list(ADDITIONS)
    command(["git", "clone", "--quiet", "--no-hardlinks", "--no-recurse-submodules", SOURCE, candidate])
    command(["git", "checkout", "--quiet", "--detach", base], candidate)
    for relative in ADDITIONS:
        target = candidate / relative
        assert not target.exists(), relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PREPARED / relative, target)
    builds = candidate / "references/Hexalith.Builds"
    command(["git", "clone", "--quiet", "--no-hardlinks", "--no-recurse-submodules",
             BUILDS, builds])
    tag = (candidate / "builds-version").read_text().strip()
    command(["git", "checkout", "--quiet", "--detach", tag], builds)
    report["builds_tag"] = tag
    report["builds_source"] = command(["git", "rev-parse", "HEAD"], builds).decode().strip()
    sys.path.insert(0, str(builds / "Github/lib"))
    from guard_tools import Tools

    tooling = scratch / "message-tools"
    tooling.mkdir()
    message = "build(cicd): prepare AI.Tools registration\n"
    Tools(tooling).lint_message(message, "exact disposable registration candidate")
    message_path = scratch / "candidate-message.txt"
    message_path.write_text(message)
    report["candidate_message"] = message
    report["checks"]["exact_candidate_message"] = "pass"
    command(["git", "add", "--", *ADDITIONS], candidate)
    command(["git", "-c", "user.name=Local qualification", "-c", "user.email=local@example.invalid",
             "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "commit", "--quiet",
             "--file", message_path], candidate)
    changes = command(["git", "diff", "--name-only", base, "HEAD"], candidate).decode().splitlines()
    assert set(changes) == set(ADDITIONS), changes
    command(["git", "diff", "--check", base, "HEAD"], candidate)
    report["checks"]["six_registration_additions_only"] = "pass"
    report["checks"]["all_existing_registered_content_preserved"] = "pass"
    checks = load("_story12_resume_global", candidate / "tools/check_global.py")
    checks.check_committed_inputs(candidate)
    report["checks"]["committed_render_inputs"] = "pass"
    checks.check_committed_render(candidate)
    report["checks"]["committed_render"] = "pass"
    with checks.selected_contract(candidate) as contract:
        checks.check_render(candidate, contract)
        report["checks"]["render_reproducibility"] = "pass"
        checks.check_documents(candidate, checks.renderer.registry(candidate), contract)
        report["checks"]["schemas_and_caller_interfaces"] = "pass"
    validator = load("_story12_resume_validator", candidate / "tools/validate.py")
    validator.check_submodule(candidate, "Hexalith.AI.Tools")
    link = command(["git", "ls-tree", "HEAD", "references/Hexalith.AI.Tools"], candidate).decode().strip()
    assert link == "160000 commit " + MODULE_HEAD + "\treferences/Hexalith.AI.Tools", link
    assert command(["git", "rev-parse", "HEAD"], MODULE).decode().strip() == MODULE_HEAD
    assert not command(["git", "status", "--porcelain"], MODULE).strip()
    publication = json.loads(command(["git", "show",
        base + ":_bmad-output/specs/spec-cicd/evidence/12/preparation-publication.json"]))
    assert publication["push_confirmed"] and publication["head"] == MODULE_HEAD
    report["checks"]["recorded_published_module_gitlink"] = "pass; historical publication readback, not a fresh remote read"
    config = json.loads((candidate / ADDITIONS[3]).read_text())
    assert config["solution"] == "none" and config["buildsTag"] == tag
    assert config["hooks"] == config["submodules"] == config["codeql"] == []
    assert config["jobs"] == {} and config["tests"] == {"exclude": {}, "integration": []}
    assert not any(config[key] for key in ("browsers", "dapr", "registry"))
    report["checks"]["explicit_no_solution_empty_inventory_configuration"] = "pass"
    owned = command(["git", "ls-tree", MODULE_HEAD, "commitlint.config.mjs"], MODULE)
    assert owned == command(["git", "ls-tree", MODULE_HEAD + "^", "commitlint.config.mjs"], MODULE)
    assert not command(["git", "ls-tree", MODULE_HEAD, "package.json", "package-lock.json"], MODULE)
    report["checks"]["published_preparation_owned_config_and_package_retirement"] = "pass"
    for suite in ("render", "validate"):
        arguments = ["uv", "run", "--locked", "--script", "--python", sys.executable,
                     candidate / f"tools/tests/test_{suite}.py"]
        result = subprocess.run(arguments, cwd=candidate, capture_output=True, timeout=600)
        output = result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")
        log = HERE / f"isolated-resume-{suite}.txt"
        log.write_text(output)
        report["checks"][f"existing_{suite}_suite"] = {
            "exit": result.returncode,
            "tests": int(re.search(r"Ran (\d+) tests?", output).group(1)),
            "log": log.name,
        }
        assert result.returncode == 0, output
    report.update(
        result="pass",
        disposable_candidate=command(["git", "rev-parse", "HEAD"], candidate).decode().strip(),
        candidate_tree=command(["git", "rev-parse", "HEAD^{tree}"], candidate).decode().strip(),
        recorded_module_gitlink=link,
        registration_paths={relative: {
            "sha256": hashlib.sha256((candidate / relative).read_bytes()).hexdigest(),
            "git_mode": command(["git", "ls-tree", "HEAD", relative], candidate).decode().split()[0],
        } for relative in ADDITIONS},
        pending=["fresh authenticated remote-main and immutable-release readbacks",
                 "story 11 genuine 2026-11-17T02:17:00Z scheduled night and acceptance",
                 "ordered AD-21 live preconditions and registration publication",
                 "full committed/global/live-module tools/validate.py verdict",
                 "authenticated App adoption, normal checker and green CI",
                 "next genuine adopted-module scheduled release/scan/delivery outcomes"],
    )
except Exception as error:
    report.update(result="failed", error=str(error))
    raise
finally:
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    (HERE / "isolated-resume-check.json").write_text(json.dumps(report, indent=2) + "\n")

print("Isolated registration candidate passes offline qualification; adoption remains gated.")
