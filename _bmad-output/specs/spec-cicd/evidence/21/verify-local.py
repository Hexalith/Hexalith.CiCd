#!/usr/bin/env python3
"""Qualify the local preparation without changing module refs or owned files.

Invoke with run-with-temp. Copies and outputs stay inside its private TMPDIR;
the JSON report and full command log stay beside this script.
"""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = Path(__file__).resolve().parent
PARTIES = ROOT / "references/Hexalith.Parties"
GRAPH_ONLY = "--graph-only" in sys.argv
if GRAPH_ONLY:
    EVIDENCE = EVIDENCE / "graph-preservation"
    EVIDENCE.mkdir(exist_ok=True)


def git(repository: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(repository), *arguments], text=True).strip()


def main() -> int:
    scratch = Path(os.environ["TMPDIR"])
    if scratch == Path("/tmp") or not scratch.is_dir():
        raise ValueError("Invoke using run-with-temp and its private TMPDIR")
    module = scratch / "Hexalith.Parties"
    subprocess.run(["git", "clone", "--quiet", "--shared", "--no-recurse-submodules", str(PARTIES), str(module)], check=True)
    # Copy only tracked product files, preserving this session's working bytes.
    # Do not follow a nested submodule or initialize one.
    tracked = git(PARTIES, "ls-files", "-z").split("\0")
    snapshot = {}
    for relative in tracked:
        source = PARTIES / relative
        if not relative:
            continue
        target = module / relative
        if not source.is_file():
            if target.is_file():
                target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        snapshot[relative] = {"sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "executable": bool(source.stat().st_mode & 0o111)}
    for relative in git(PARTIES, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        source = PARTIES / relative
        if not relative or not source.is_file():
            continue
        target = module / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        snapshot[relative] = {"sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "executable": bool(source.stat().st_mode & 0o111)}
    pin = (ROOT / "builds-version").read_text().strip()
    dependencies: dict[str, str] = {}
    for name in ("Builds", "EventStore", "Tenants", "Memories", "Platform", "Commons", "FrontComposer", "McpCli", "PolymorphicSerializations", "AI.Tools"):
        repository = "Hexalith." + name
        source = ROOT / "references" / repository
        revision = git(source, "rev-parse", pin + "^{commit}") if name == "Builds" else git(PARTIES, "rev-parse", ":references/" + repository)
        destination = module / "references" / repository
        # Retained native provenance reads HEAD. A real local clone preserves the
        # exact identity and ordinary owner files, with no nested checkout.
        subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", "--no-recurse-submodules", str(source), str(destination)], check=True)
        subprocess.run(["git", "-C", str(destination), "checkout", "--quiet", "--detach", revision], check=True)
        dependencies[repository] = revision
    report: dict[str, object] = {
        "phase": "local-only preparation; no push, adoption or acceptance credit",
        "source": git(PARTIES, "rev-parse", "HEAD"),
        "sourceDiffSha256": hashlib.sha256(subprocess.check_output(["git", "-C", str(PARTIES), "diff", "HEAD", "--binary"])).hexdigest(),
        "sourceFilesSha256": hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest(),
        "buildsVersion": pin,
        "dependencies": dependencies,
        "commands": [],
    }
    (EVIDENCE / "local-source-inputs.json").write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    properties = ["-p:UseHexalithProjectReferences=false", "-p:UseNuGetDeps=true", "-p:NuGetAudit=true", "-p:NuGetAuditMode=all", "-p:NuGetAuditLevel=low", "-p:HexalithEventStoreVersion=5.1.1"]
    target = "tests/Hexalith.Parties.Tests/Hexalith.Parties.Tests.csproj" if GRAPH_ONLY else "Hexalith.Parties.Standalone.slnx"
    command = ["dotnet", "build", target, "--configuration", "Release", "--disable-build-servers", "-m:1", "-warnaserror", *properties]
    with (EVIDENCE / "local-build.log").open("w") as log:
        started = time.monotonic()
        result = subprocess.run(command, cwd=module, stdout=log, stderr=subprocess.STDOUT)
        report["commands"].append({"argv": command, "exitCode": result.returncode, "durationSeconds": round(time.monotonic() - started, 3)})
    if result.returncode == 0:
        # Changed, retained product assertions; actual native/browser scenarios
        # require live control channels and are never inferred from these tests.
        for project, classes in [
            ("Hexalith.Parties.Ci.Tests", ["BrowserProductTests", "ContainerProductTests", "ReleaseArtifactVerificationTests", "StandaloneSolutionTests"]),
            ("Hexalith.Parties.Tests", ["DependencyGraphTests", "RetiredLeafProjectFitnessTests"]),
        ]:
            if GRAPH_ONLY and project != "Hexalith.Parties.Tests":
                continue
            namespace = "Hexalith.Parties.Ci.Tests" if project.endswith("Ci.Tests") else "Hexalith.Parties.Tests.FitnessTests"
            command = ["dotnet", "test", "--project", f"tests/{project}/{project}.csproj", "--no-build", "--no-restore", "--configuration", "Release", *properties, "--minimum-expected-tests", "1", "--fail-skips", "on"]
            for name in classes:
                command.extend(["--filter-class", namespace + "." + name])
            with (EVIDENCE / ("local-" + project + ".log")).open("w") as log:
                started = time.monotonic()
                result = subprocess.run(command, cwd=module, stdout=log, stderr=subprocess.STDOUT)
                report["commands"].append({"argv": command, "exitCode": result.returncode, "durationSeconds": round(time.monotonic() - started, 3)})
            if result.returncode:
                break
    if result.returncode == 0 and not GRAPH_ONLY:
        for name, command in [
            ("declaration", ["python3", "scripts/render-platform-declaration.py", "--check"]),
            ("declaration-tests", ["python3", "-B", "-m", "unittest", "discover", "-s", "scripts", "-p", "test_platform_declaration.py", "-v"]),
            ("browser-install", ["npm", "ci", "--ignore-scripts"]),
            ("browser-config", ["npm", "run", "test:config"]),
            ("browser-types", ["npm", "run", "typecheck"]),
            ("chromium", ["npx", "--no-install", "playwright", "install", "chromium"]),
            ("browser-scenarios", ["npm", "run", "test:ui"]),
        ]:
            directory = module / "tests/e2e" if name.startswith("browser") or name == "chromium" else module
            environment = dict(os.environ, CI="true", BASE_URL="http://127.0.0.1:5072", PLAYWRIGHT_SKIP_WEBSERVER="", PLAYWRIGHT_BROWSERS_PATH=str(scratch / "browsers"))
            with (EVIDENCE / ("local-" + name + ".log")).open("w") as log:
                started = time.monotonic()
                result = subprocess.run(command, cwd=directory, env=environment, stdout=log, stderr=subprocess.STDOUT)
                report["commands"].append({"argv": command, "workingDirectory": str(directory.relative_to(module)), "exitCode": result.returncode, "durationSeconds": round(time.monotonic() - started, 3)})
            if result.returncode:
                break
    (EVIDENCE / "local-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
