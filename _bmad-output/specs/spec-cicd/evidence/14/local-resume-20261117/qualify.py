"""Qualify the restored Agents audit-policy assertion without remote operations."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
SCRATCH = Path(os.environ["TMPDIR"])
REPORT = {
    "observedAt": datetime.now(timezone.utc).isoformat(),
    "scope": "local snapshots plus uncommitted Agents audit-policy restoration; no GitHub operations",
    "commands": [],
}


def git(repository, *arguments):
    return subprocess.check_output(["git", "-C", str(repository), *arguments])


def save():
    (HERE / "qualification.json").write_text(json.dumps(REPORT, indent=2) + "\n")


def run(label, command, cwd):
    log = HERE / (label + ".log")
    with log.open("w") as output:
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=output,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "UV_OFFLINE": "1"},
        )
    REPORT["commands"].append({
        "label": label,
        "command": command,
        "exitCode": result.returncode,
        "log": log.name,
        "logSha256": hashlib.sha256(log.read_bytes()).hexdigest(),
    })
    save()
    print(label + ": " + str(result.returncode), flush=True)
    if result.returncode:
        REPORT["result"] = "fail"
        save()
        raise SystemExit(result.returncode)


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
    }


module = SCRATCH / "Agents"
builds = module / "references/Hexalith.Builds"
REPORT["agents"] = snapshot(ROOT / "references/Hexalith.Agents", module)
REPORT["builds"] = snapshot(ROOT / "references/Hexalith.Builds", builds)
REPORT["buildsVersion"] = (ROOT / "builds-version").read_text().strip()
REPORT["v620"] = git(ROOT / "references/Hexalith.Builds", "rev-parse", "v6.2.0").decode().strip()
save()

for version in ("3.12", "3.14"):
    for group in ("ci_config", "ci_pipeline", "local_check"):
        run(
            "builds-" + group + "-python" + version.replace(".", ""),
            [
                "uv", "run", "--offline", "--python", version, "--with", "jsonschema==4.26.0",
                "--with", "PyYAML==6.0.3", "python", "-B", "-m", "unittest", "discover",
                "-s", "Github/lib/tests", "-p", "test_" + group + ".py", "-v",
            ],
            builds,
        )

for group in (
    "built_package_hook",
    "ui_consumer_assets",
    "nuget_package_validation",
    "ui_static_package",
    "publish_release_packages",
    "release_package_integrity",
    "package_pack",
    "recover_release_packages",
    "package_authority_exclusions",
):
    run(
        "agents-" + group.replace("_", "-"),
        ["python3", "-B", "-m", "unittest", "discover", "-s", "tests/tooling",
         "-p", group + "_test.py", "-v"],
        module,
    )

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
run(
    "agents-audit-policy",
    [
        "dotnet", "test",
        "--project", "test/Hexalith.Agents.Server.Tests/Hexalith.Agents.Server.Tests.csproj",
        "-c", "Release", "--no-build", "--no-restore",
        "-p:UseHexalithProjectReferences=false",
        "--filter", "FullyQualifiedName~OrdinaryReleaseShouldEvaluateTheHighAndCriticalAuditPolicy"
                    "|FullyQualifiedName~RootBuildPropsShouldEnforceLanguageAndBuildContract",
        "--stop-on-fail", "off", "--fail-skips", "on",
    ],
    module,
)
run("agents-check-built-packages", ["python3", "scripts/check-built-packages.py"], module)
if (module / "artifacts/cicd-agents-package-check").exists():
    raise RuntimeError("package hook retained scratch data")

REPORT["result"] = "pass"
save()
