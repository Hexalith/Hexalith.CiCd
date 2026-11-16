#!/usr/bin/env python3
"""Check the uncommitted preparation in a disposable, local-only standalone clone.

Run with run-with-temp. This is preparation evidence, not the exact committed
pre-push/adoption qualification required by the approved migration decision.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile


EVIDENCE = Path(__file__).resolve().parent
WORKSPACE = EVIDENCE.parents[4]
MODULE = WORKSPACE / "references/Hexalith.Timesheets"


def git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


def main() -> int:
    scratch = Path(os.environ["TMPDIR"])
    clone = scratch / "Timesheets"
    subprocess.run(["git", "clone", "--shared", "--no-checkout", str(MODULE), str(clone)], check=True)
    head = git(MODULE, "rev-parse", "HEAD")
    subprocess.run(["git", "-C", str(clone), "checkout", "--detach", head], check=True)
    patch = subprocess.check_output(["git", "-C", str(MODULE), "diff", "--binary", "HEAD"])
    subprocess.run(["git", "-C", str(clone), "apply"], input=patch, check=True)
    additions = [
        "scripts/tests/test_product_packages.py",
        "tests/Hexalith.Timesheets.ArchitectureTests/FitnessTests/AppHostDependencyTests.cs",
        "tools/product-validation.json",
        *[path.relative_to(MODULE).as_posix() for path in sorted((MODULE / "tools/package-consumers").glob("*.cs"))],
    ]
    for relative in additions:
        (clone / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MODULE / relative, clone / relative)
    revisions = {"module": head, "local_origin_main": git(MODULE, "rev-parse", "origin/main")}
    for name in ("Builds", "EventStore", "Works"):
        relative = "references/Hexalith." + name
        revision = git(MODULE, "rev-parse", head + ":" + relative)
        revisions[relative] = revision
        archive = scratch / (name + ".tar")
        subprocess.run(["git", "-C", str(WORKSPACE / relative), "archive", "--output", str(archive), revision], check=True)
        target = clone / relative
        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as stream:
            stream.extractall(target, filter="data")
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", DOTNET_CLI_HOME=str(scratch / "dotnet-home"),
                       DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", MSBUILDDISABLENODEREUSE="1")
    jobs = [
        ("package-validator-tests", ["python3", "scripts/tests/test_product_packages.py", "-v"]),
        ("selected-index-tests", ["python3", "scripts/test_magic_link_index_selection.py", "-v"]),
        ("release-package-build", ["dotnet", "build", "Hexalith.Timesheets.slnx", "--configuration", "Release",
                                    "-p:UseHexalithProjectReferences=false", "-warnaserror", "-m:1", "/nr:false"]),
        ("architecture-build", ["dotnet", "build", "tests/Hexalith.Timesheets.ArchitectureTests/Hexalith.Timesheets.ArchitectureTests.csproj",
                                "--configuration", "Release", "-p:UseHexalithProjectReferences=false", "-warnaserror", "-m:1", "/nr:false"]),
    ]
    results = []
    for name, command in jobs:
        log = EVIDENCE / (name + ".log")
        with log.open("w") as stream:
            result = subprocess.run(command, cwd=clone, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=False)
        results.append({"job": name, "command": command, "exit_code": result.returncode, "log": log.name})
        print(name + ": " + str(result.returncode), flush=True)
    if results[-1]["exit_code"] == 0:
        name = "architecture-tests"
        command = ["dotnet", "test", "--project", "tests/Hexalith.Timesheets.ArchitectureTests/Hexalith.Timesheets.ArchitectureTests.csproj",
                   "--configuration", "Release", "--no-build", "--no-restore", "-p:UseHexalithProjectReferences=false"]
        log = EVIDENCE / (name + ".log")
        with log.open("w") as stream:
            result = subprocess.run(command, cwd=clone, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=False)
        results.append({"job": name, "command": command, "exit_code": result.returncode, "log": log.name})
        print(name + ": " + str(result.returncode), flush=True)
    output = {"qualification": "uncommitted local preparation only; no fetch, push, remote settings or adoption",
              "revisions": revisions, "patch_sha256": hashlib.sha256(patch).hexdigest(),
              "additions": {relative: hashlib.sha256((MODULE / relative).read_bytes()).hexdigest() for relative in additions},
              "results": results}
    (EVIDENCE / "local-preparation-check.json").write_text(json.dumps(output, indent=2) + "\n")
    return int(any(result["exit_code"] for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
