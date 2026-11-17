"""Qualify the current Agents preparation tree before a module-agent push."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent
SOURCE = Path("/home/administrator/projects/hexalith/agents-story-14-prepare-20261117b")
BUILDS_SOURCE = Path("/home/administrator/projects/hexalith/cicd/references/Hexalith.Builds")
RELEASE = "0ccd12af6576a3aac601340dec7dba53e86768c3"
SCRATCH = Path(os.environ["TMPDIR"])
PROTECTED = (
    ".gitmodules",
    "AGENTS.md",
    "CLAUDE.md",
    ".claude/settings.json",
    ".github/copilot-instructions.md",
    ".github/dependabot.yml",
    ".github/workflows",
    "references/Hexalith.Builds",
)
FLOORS = (
    ("Contracts", "Hexalith.Agents.Contracts.Tests", 529),
    ("Client", "Hexalith.Agents.Client.Tests", 6),
    ("Domain", "Hexalith.Agents.Tests", 787),
    ("Server", "Hexalith.Agents.Server.Tests", 549),
    ("UI", "Hexalith.Agents.UI.Tests", 1073),
)
REPORT = {
    "observedAt": datetime.now(timezone.utc).isoformat(),
    "scope": "Agents preparation push; approved pre-adoption proof; no adoption",
    "releasedPolicy": json.loads((HERE / "released-policy-proof.json").read_text()),
    "commands": [],
}


def git(repository, *arguments):
    return subprocess.check_output(["git", "-C", str(repository), *arguments])


def save():
    (HERE / "qualification.json").write_text(json.dumps(REPORT, indent=2) + "\n")


def run(label, command, cwd, *, expected=None, environment=None):
    log = HERE / (label + ".log")
    env = environment or {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "DOTNET_CLI_HOME": str(SCRATCH / "dotnet-home"),
        "NUGET_PACKAGES": str(SCRATCH / "nuget-packages"),
        "NUGET_HTTP_CACHE_PATH": str(SCRATCH / "nuget-http"),
        "NUGET_PLUGINS_CACHE_PATH": str(SCRATCH / "nuget-plugins"),
        "DOTNET_CLI_UI_LANGUAGE": "en-US",
        "DOTNET_NOLOGO": "1",
        "DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER": "1",
        "MSBUILDDISABLENODEREUSE": "1",
        "MinVerVersionOverride": "0.0.0",
    }
    with log.open("w") as output:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
    REPORT["commands"].append({
        "label": label,
        "command": command,
        "exitCode": result.returncode,
        "log": log.name,
        "logSha256": hashlib.sha256(log.read_bytes()).hexdigest(),
    })
    save()
    print(label + ": " + str(result.returncode), flush=True)
    if expected is None:
        if result.returncode:
            REPORT["result"] = "fail"
            save()
            raise SystemExit(result.returncode)
        return result
    expected(result.returncode, log.read_text())
    return result


def snapshot(source, destination):
    subprocess.run(
        ["git", "-c", "submodule.recurse=false", "clone", "--quiet", "--shared",
         "--no-recurse-submodules", str(source), str(destination)],
        check=True,
    )
    revision = git(source, "rev-parse", "HEAD").decode().strip()
    subprocess.run(["git", "-C", str(destination), "checkout", "--quiet", "--detach", revision], check=True)
    names = git(source, "diff", "--name-only", "-z", "HEAD").split(b"\0")
    names += git(source, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    for raw in names:
        if not raw:
            continue
        name = raw.decode()
        src = source / name
        dst = destination / name
        if src.is_dir():
            continue
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif dst.exists():
            dst.unlink()
    subprocess.run(["git", "-C", str(destination), "add", "--all"], check=True)
    return {
        "revision": revision,
        "candidateTree": git(destination, "write-tree").decode().strip(),
        "sourceWorktreeChanges": git(source, "status", "--short").decode().splitlines(),
        "changedPaths": [path.decode() for path in names if path],
    }


module = SCRATCH / "Agents"
builds = module / "references/Hexalith.Builds"
REPORT["agents"] = snapshot(SOURCE, module)
pinned = git(SOURCE, "rev-parse", "HEAD:references/Hexalith.Builds").decode().strip()
REPORT["recordedBuildsGitlink"] = pinned
subprocess.run(
    ["git", "-c", "submodule.recurse=false", "clone", "--quiet", "--shared",
     "--no-recurse-submodules", str(BUILDS_SOURCE), str(builds)],
    check=True,
)
subprocess.run(["git", "-C", str(builds), "checkout", "--quiet", "--detach", pinned], check=True)
assert git(builds, "rev-parse", "HEAD").decode().strip() == pinned
REPORT["attachedBuilds"] = pinned
remotes = git(module, "remote").decode().split()
if "origin" in remotes:
    subprocess.run(
        ["git", "-C", str(module), "remote", "set-url", "origin",
         "https://github.com/Hexalith/Hexalith.Agents.git"],
        check=True,
    )
else:
    subprocess.run(
        ["git", "-C", str(module), "remote", "add", "origin",
         "https://github.com/Hexalith/Hexalith.Agents.git"],
        check=True,
    )
subprocess.run(
    ["git", "-C", str(module), "update-ref", "refs/remotes/origin/main",
     REPORT["agents"]["revision"]],
    check=True,
)
REPORT["origin"] = "https://github.com/Hexalith/Hexalith.Agents.git"
save()

base = git(SOURCE, "rev-parse", "origin/main").decode().strip()
REPORT["freshMainBase"] = base
changed = {
    path for path in git(module, "diff", "--name-only", base, "HEAD").decode().splitlines() if path
}
REPORT["pushRangePaths"] = sorted(changed)
if changed != {
    "eng/consumer-executable-assets.json",
    "test/Hexalith.Agents.Server.Tests/BuildContractConformanceTests.cs",
}:
    raise RuntimeError("unexpected candidate paths: " + str(sorted(changed)))
owned = git(module, "diff", "--name-only", base, "HEAD", "--", *PROTECTED).decode().splitlines()
if owned:
    raise RuntimeError("owned perimeter changed: " + str(owned))
REPORT["ownedPerimeterUnchanged"] = True
missing_config = subprocess.run(
    ["git", "-C", str(module), "cat-file", "-e", "HEAD:.github/hexalith-ci.json"],
    capture_output=True,
)
REPORT["adoptedConfigPresent"] = missing_config.returncode == 0
if REPORT["adoptedConfigPresent"]:
    raise RuntimeError("Agents main now has hexalith-ci.json; the preparation exception has ended")
save()

message_file = HERE / "Hexalith.Agents-message.txt"
file_message = message_file.read_text()
message = git(SOURCE, "log", "-1", "--format=%B").decode()
if message.strip() != file_message.strip():
    raise RuntimeError("HEAD message does not match the validated candidate file")
REPORT["head"] = git(SOURCE, "rev-parse", "HEAD").decode().strip()
released = SCRATCH / "released"
released.mkdir()
archive = subprocess.check_output(
    ["git", "archive", RELEASE, "Github/lib", "Github/guard", "schemas"],
    cwd=BUILDS_SOURCE,
)
with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
    contents.extractall(released, filter="data")
sys.path.insert(0, str(released / "Github/lib"))
from guard_tools import Tools, SOURCE as GUARD_SOURCE
from expected_state import Git, tree_snapshot
import audit_lint

tools_dir = SCRATCH / "guard-tools"
tools_dir.mkdir()
tools = Tools(tools_dir)
REPORT["guardLockSha256"] = hashlib.sha256((GUARD_SOURCE / "package-lock.json").read_bytes()).hexdigest()
tools.lint_message(message, "shared released policy")
owning = SOURCE / "commitlint.config.mjs"
copied = tools_dir / "agents-commitlint.config.mjs"
copied.write_bytes(owning.read_bytes())
message_file = HERE / "Hexalith.Agents-message.txt"
verbose = tools._process(
    ["node", str(tools_dir / "node_modules/@commitlint/cli/cli.js"),
     "--config", str(copied), "--cwd", str(SOURCE), "--edit", str(message_file),
     "--verbose", "--color=false"],
    "Agents owning commit policy",
)
(HERE / "commitlint.log").write_text(verbose.stdout + verbose.stderr)
if verbose.returncode:
    raise RuntimeError("owning commitlint failed:\n" + verbose.stdout + verbose.stderr)
REPORT["commitlint"] = {
    "sharedReleasedPolicy": "passed",
    "owningPolicy": "passed",
    "releasedValidatorCommit": RELEASE,
    "configSha256": hashlib.sha256(owning.read_bytes()).hexdigest(),
    "messageSha256": hashlib.sha256(message.encode()).hexdigest(),
}
save()

audit_lint.lint(tree_snapshot(Git(module)))
REPORT["releasedAuditLint"] = "passed"
save()


def bootstrap(code, text):
    if code != 1 or ".github/hexalith-ci.json" not in text:
        raise RuntimeError("Unexpected checker result; do not extend the approved bootstrap exception")
    REPORT["normalChecker"] = "Refused missing pre-adoption config; approved preparation proof follows."


run("agents-normal-checker", ["python3", "references/Hexalith.Builds/check.py"], module, expected=bootstrap)
run(
    "agents-restore",
    ["dotnet", "restore", "Hexalith.Agents.slnx", "-p:Configuration=Release",
     "-p:UseHexalithProjectReferences=false", "/m:1", "/nr:false"],
    module,
)
run(
    "agents-build",
    ["dotnet", "build", "Hexalith.Agents.slnx", "-c", "Release", "--no-restore",
     "-warnaserror", "-p:UseHexalithProjectReferences=false", "/m:1", "/nr:false"],
    module,
)
for label, project, floor in FLOORS:
    run(
        "agents-tests-" + label,
        ["dotnet", "test", "--project", f"test/{project}/{project}.csproj",
         "-c", "Release", "--no-build", "--no-restore",
         "-p:UseHexalithProjectReferences=false", "--stop-on-fail", "off",
         "--minimum-expected-tests", str(floor), "--fail-skips", "on"],
        module,
    )
run("agents-package-hook", ["python3", "scripts/check-built-packages.py"], module)
if (module / "artifacts/cicd-agents-package-check").exists():
    raise RuntimeError("package hook retained scratch data")
run(
    "agents-exact-exclusions",
    ["python3", "-B", "-m", "unittest", "discover", "-s", "tests/tooling",
     "-p", "package_authority_exclusions_test.py", "-v"],
    module,
)
dirty = git(module, "status", "--porcelain", "--ignore-submodules=all").decode()
if dirty:
    raise RuntimeError("proof dirtied the candidate:\n" + dirty)
REPORT["moduleProductTreeUnchangedDuringProof"] = True
REPORT["result"] = "pass"
save()
print("qualification: pass", flush=True)
