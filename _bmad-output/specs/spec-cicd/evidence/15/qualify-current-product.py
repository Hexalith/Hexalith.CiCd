"""Qualify the current McpCli product-preparation tree under the approved substitute.

Run with run-with-temp. Uses a standalone copy, a sibling Builds archive of the
module pin, and released v6.2.0 policy tools. Initializes no nested submodule.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULE = Path("/home/administrator/projects/hexalith/mcpcli-story-15-product")
PROTECTED = [
    ".github/workflows", ".github/dependabot.yml", ".github/hexalith-ci.json",
    ".releaserc.json", ".gitmodules", "references/Hexalith.Builds",
    "AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md",
    ".claude/settings.json", "commitlint.config.mjs",
]
ORDINARY = [
    "tests/Hexalith.McpCli.Abstractions.Tests/Hexalith.McpCli.Abstractions.Tests.csproj",
    "tests/Hexalith.McpCli.Analyzers.Tests/Hexalith.McpCli.Analyzers.Tests.csproj",
    "tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj",
    "tests/Hexalith.McpCli.Manifest.Tests/Hexalith.McpCli.Manifest.Tests.csproj",
    "tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj",
    "tests/Hexalith.McpCli.Mcp.Tests/Hexalith.McpCli.Mcp.Tests.csproj",
]
FLAGS = [
    "-p:UseHexalithProjectReferences=false", "-p:NuGetAudit=true",
    "-p:NuGetAuditMode=all", "-p:NuGetAuditLevel=low", "-warnaserror",
]
MESSAGE = """ci: migrate product checks onto registered actions

Preserve payload, consumer, conformance and native launcher coverage while
removing YAML and semantic-release orchestration tests.
"""
PYTHON = "/home/administrator/.local/bin/python3.12"
scratch = Path(os.environ["TMPDIR"]).resolve()
report = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "module": str(MODULE),
    "approval": "Story 15 frozen human decision, 2026-11-16; pre-adoption package-mode substitute",
    "nested_submodules_initialized": False,
    "operations": [],
}
log_path = HERE / "qualify-current-product.log"
report_path = HERE / "qualify-current-product.json"


def save() -> None:
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def log(message: str) -> None:
    line = message.rstrip() + "\n"
    sys.stderr.write(line)
    sys.stderr.flush()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def run(arguments, *, cwd, env=None, timeout=1800, check=True):
    log("Running: " + " ".join(map(str, arguments)))
    result = subprocess.run(
        list(map(str, arguments)), cwd=cwd, env=env, capture_output=True,
        text=True, timeout=timeout)
    report["operations"].append({
        "command": list(map(str, arguments)), "cwd": str(cwd),
        "exit": result.returncode, "seconds_timeout": timeout,
        "stdout_tail": result.stdout[-4000:], "stderr_tail": result.stderr[-4000:],
    })
    save()
    if result.stdout:
        log(result.stdout[-2000:])
    if result.stderr:
        log(result.stderr[-2000:])
    if check and result.returncode:
        raise SystemExit(f"{arguments[0]} exited {result.returncode}")
    return result


def git(module, *arguments):
    return subprocess.check_output(["git", *arguments], cwd=module, text=True).strip()


try:
    log_path.write_text("")
    assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
    assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
    base = git(MODULE, "rev-parse", "HEAD")
    github_main = git(MODULE, "rev-parse", "github/main")
    assert base == github_main, (base, github_main)
    owned = git(MODULE, "diff", "--name-status", "HEAD", "--", *PROTECTED)
    assert not owned, owned
    nested = list((MODULE / "references").glob("*/.git"))
    assert not nested, nested
    report.update(base=base, github_main=github_main, owned_content_diff=owned)
    builds_pin = git(MODULE, "rev-parse", "HEAD:references/Hexalith.Builds")
    report["builds_pin"] = builds_pin

    copy = scratch / "module"
    run(["git", "clone", "--quiet", "--shared", "--no-checkout", str(MODULE), str(copy)], cwd=scratch)
    run(["git", "checkout", "-B", "candidate", base], cwd=copy)
    diff = subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=MODULE)
    apply = subprocess.run(["git", "apply", "--binary", "--index", "-"], cwd=copy, input=diff, check=True)
    report["candidate_diff_sha256"] = hashlib.sha256(diff).hexdigest()
    assert not git(copy, "diff", "--name-status", "HEAD", "--", *PROTECTED)
    assert not list((copy / "references").glob("*/.git"))

    builds_checkout = ROOT / "references/Hexalith.Builds"
    sibling = scratch / "Hexalith.Builds"
    sibling.mkdir()
    archive = subprocess.check_output(["git", "archive", builds_pin], cwd=builds_checkout)
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(sibling, filter="data")
    assert not (copy / "references/Hexalith.Builds/.git").exists()
    released = scratch / "builds-v6.2.0"
    released.mkdir()
    tag = "v6.2.0"
    released_sha = git(builds_checkout, "rev-parse", f"{tag}^{{commit}}")
    assert released_sha == "0ccd12af6576a3aac601340dec7dba53e86768c3"
    archive = subprocess.check_output(["git", "archive", released_sha], cwd=builds_checkout)
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(released, filter="data")
    report.update(builds_release_tag=tag, builds_release_sha=released_sha)

    sys.path.insert(0, str(released / "Github/lib"))
    import audit_lint
    import expected_state
    from guard_tools import Tools

    snapshot = expected_state.tree_snapshot(expected_state.Git(copy), git(copy, "write-tree"))
    audit_lint.lint(snapshot)
    report["released_audit_lint"] = "pass"
    tools_dir = scratch / "tools"
    tools_dir.mkdir()
    tools = Tools(tools_dir)
    message_path = HERE / "product-commit-message.txt"
    message_path.write_text(MESSAGE)
    tools.lint_message(MESSAGE, "shared commitlint")
    copied = scratch / "tools" / "module-commitlint.config.mjs"
    shutil.copyfile(MODULE / "commitlint.config.mjs", copied)
    module_lint = tools._process(
        ["node", str(scratch / "tools" / "node_modules/@commitlint/cli/cli.js"),
         "--config", str(copied), "--color=false", "--verbose"],
        "owning repository commitlint", MESSAGE)
    if module_lint.returncode:
        raise SystemExit(module_lint.stdout + module_lint.stderr)
    report.update(shared_commitlint="pass", owning_commitlint="pass",
                  commit_message=MESSAGE, commit_message_sha256=hashlib.sha256(MESSAGE.encode()).hexdigest(),
                  owning_commitlint_output=module_lint.stdout)

    env = dict(
        os.environ, NUGET_PACKAGES=str(scratch / "packages"),
        NUGET_HTTP_CACHE_PATH=str(scratch / "http"), DOTNET_NOLOGO="1",
        DOTNET_CLI_TELEMETRY_OPTOUT="1", MSBUILDDISABLENODEREUSE="1",
        DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", PYTHONDONTWRITEBYTECODE="1",
        NO_COLOR="1", TERM="dumb")
    for key in (
            "COLORTERM", "TERM_PROGRAM", "CLICOLOR", "CLICOLOR_FORCE", "FORCE_COLOR",
            "DOTNET_SYSTEM_CONSOLE_ALLOW_ANSI_COLOR_REDIRECTION"):
        env.pop(key, None)
    run(["dotnet", "restore", "Hexalith.McpCli.slnx", *FLAGS], cwd=copy, env=env, timeout=900)
    run(["dotnet", "build", "Hexalith.McpCli.slnx", "--no-restore", "--configuration", "Release",
         "-p:UseHexalithProjectReferences=false", "-warnaserror"], cwd=copy, env=env, timeout=900)
    for project in ORDINARY:
        run(["dotnet", "test", project, "--no-build", "--configuration", "Release"],
            cwd=copy, env=env, timeout=900)
    report["ordinary_tests"] = "pass"

    packable = []
    for item in ET.parse(copy / "Hexalith.McpCli.slnx").iter("Project"):
        path = item.attrib["Path"]
        result = run(
            ["dotnet", "msbuild", path, "-nologo", "-p:Configuration=Release",
             "-p:UseHexalithProjectReferences=false", "-getProperty:IsPackable,PackageId"],
            cwd=copy, env=env, timeout=120)
        properties = json.loads(result.stdout)["Properties"]
        if properties["IsPackable"] == "true":
            packable.append(properties["PackageId"])
    assert sorted(packable) == ["Hexalith.McpCli", "Hexalith.McpCli.Abstractions"], packable
    report["evaluated_pack_set"] = sorted(packable)

    venv = scratch / "py"
    run([PYTHON, "-m", "venv", str(venv)], cwd=copy, env=env, timeout=120)
    python = venv / "bin" / "python"
    run([python, "-m", "pip", "install", "--upgrade", "pip"], cwd=copy, env=env, timeout=180)
    run([python, "-m", "pip", "install", "-r", "tools/conformance-vectors/v1/requirements.txt"],
        cwd=copy, env=env, timeout=180)
    product = run([python, "-m", "unittest", "discover", "-v", "-s", "scripts/tests", "-p", "test_*.py"],
                  cwd=copy, env=env, timeout=600)
    report["product_script_tests"] = {"exit": product.returncode, "tail": product.stderr[-2000:]}
    conformance = run([python, "-m", "unittest", "discover", "-v", "-s", "tools/conformance-vectors/v1", "-p", "test_*.py"],
                      cwd=copy, env=env, timeout=900)
    report["conformance_tests"] = {"exit": conformance.returncode, "tail": conformance.stderr[-2000:]}
    native = run([python, "-m", "unittest", "discover", "-v", "-s", "tools/live-topology", "-p", "test_native_*.py"],
                 cwd=copy, env=env, timeout=600)
    report["native_helper_tests"] = {"exit": native.returncode, "tail": native.stderr[-2000:]}
    report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat())
    save()
    print(json.dumps({key: report[key] for key in (
        "result", "base", "builds_pin", "evaluated_pack_set", "ordinary_tests",
        "shared_commitlint", "owning_commitlint")}, indent=2))
except Exception as error:
    report.update(result="fail", error=str(error), completed_at=datetime.now(timezone.utc).isoformat())
    save()
    raise
