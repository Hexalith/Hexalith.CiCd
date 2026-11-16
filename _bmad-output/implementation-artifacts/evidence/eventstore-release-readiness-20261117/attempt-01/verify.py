#!/usr/bin/env python3
"""Verify the frozen EventStore producer; run only through run-with-temp.

No publication, submodule initialization, or shared checkout mutation occurs.
Every invocation requires a new output directory so failures remain preserved.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import xml.etree.ElementTree as ET

SOURCE = "3b2350e7c1fff640131f8101596c78a59e31a03f"
BUILDS = "16cf0db6f843eb4defdc87105804d42eded634d6"
PROJECTS = {
    "generators": "tests/Hexalith.EventStore.RestApi.Generators.Tests/Hexalith.EventStore.RestApi.Generators.Tests.csproj",
    "contracts": "tests/Hexalith.EventStore.Contracts.Tests/Hexalith.EventStore.Contracts.Tests.csproj",
    "gateway": "src/Hexalith.EventStore.Gateway/Hexalith.EventStore.Gateway.csproj",
}
INPUTS = [
    "AGENTS.md", "Directory.Build.props", "Directory.Build.targets",
    "Directory.Packages.props", ".editorconfig", ".gitattributes", "global.json",
    ".gitmodules", ".github/workflows/ci.yml", ".github/workflows/release.yml",
    "tests/Directory.Build.props", "scripts/verify-release-source.sh",
    "tools/release-packages.json",
    "src/Hexalith.EventStore.Contracts/Queries/QueryResultContractAttribute.cs",
    "tests/Hexalith.EventStore.RestApi.Generators.Tests/TypedGatewayQueryGenerationTests.cs",
    *PROJECTS.values(),
]


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tmp = Path(os.environ["TMPDIR"]).resolve()
    if os.environ.get("TMP") != str(tmp) or os.environ.get("TEMP") != str(tmp):
        parser.error("Invoke with run-with-temp so TMPDIR/TMP/TEMP identify private scratch.")
    output = args.output.resolve()
    if output == tmp or tmp in output.parents:
        parser.error("Evidence must survive scratch cleanup; output must be outside TMPDIR.")
    output.mkdir(parents=True, exist_ok=False)
    work = Path(tempfile.mkdtemp(prefix="eventstore-readiness-", dir=tmp))
    owner = work / "Hexalith.EventStore"
    env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "HEXALITH_BUILDS_SOURCE"):
        env.pop(name, None)
    env.update({
        "GIT_NO_REPLACE_OBJECTS": "1", "GIT_TERMINAL_PROMPT": "0",
        "NUGET_PACKAGES": str(work / "nuget-packages"),
        "NUGET_HTTP_CACHE_PATH": str(work / "nuget-http-cache"),
        "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1",
        "MSBUILDDISABLENODEREUSE": "1",
    })
    result = {
        "started_utc": utc(), "source": SOURCE, "builds": BUILDS,
        "helper_sha256": sha256(Path(__file__).resolve()),
        "scratch": str(work), "commands": [], "inputs": {}, "dependencies": {},
        "test_results": {}, "checks": {}, "complete_release_acceptance": False,
        "filters": [], "source_changes_authorized_only_on_demonstrated_product_failure": True,
    }

    def save():
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    def run(name, command, cwd=None, required=False):
        log = output / (name + ".log")
        record = {"name": name, "command": [str(x) for x in command],
                  "cwd": str(cwd or work), "started_utc": utc(), "log": log.name}
        result["commands"].append(record)
        save()
        print(f"{utc()} START {name}", flush=True)
        started = time.monotonic()
        with log.open("wb") as stream:
            process = subprocess.run(command, cwd=cwd or work, env=env,
                                     stdout=stream, stderr=subprocess.STDOUT, check=False)
        record.update(native_exit=process.returncode, elapsed_seconds=round(time.monotonic()-started, 3),
                      finished_utc=utc(), log_sha256=sha256(log))
        save()
        print(f"{utc()} EXIT {name}: {process.returncode}", flush=True)
        if required and process.returncode:
            raise RuntimeError(f"{name} failed: exit {process.returncode}; see {log.name}")
        return process.returncode, log.read_text(errors="replace")

    def git(root, *arguments):
        return subprocess.check_output(["git", "--no-replace-objects", "-C", str(root), *arguments],
                                       env=env, text=True).strip()

    def clone(name, commit, destination):
        store = args.workspace.resolve() / "references" / name
        if git(store, "cat-file", "-t", commit) != "commit":
            raise RuntimeError(f"Missing commit {name} {commit}")
        run("clone-" + name, ["git", "-c", "submodule.recurse=false", "clone", "--no-checkout",
                              "--no-hardlinks", str(store), str(destination)], required=True)
        run("checkout-" + name, ["git", "-c", "submodule.recurse=false", "checkout", "--detach", commit],
            cwd=destination, required=True)
        # Production identity is required by the existing repository-path tests.
        run("origin-" + name, ["git", "remote", "set-url", "origin",
                               f"https://github.com/Hexalith/{name}.git"], cwd=destination, required=True)
        assert git(destination, "rev-parse", "HEAD") == commit
        assert not git(destination, "status", "--porcelain")
        result["dependencies"][name] = {"commit": commit,
            "tree": git(destination, "rev-parse", "HEAD^{tree}"), "object_store": str(store),
            "nested_submodules_initialized": False}
        save()

    try:
        clone("Hexalith.EventStore", SOURCE, owner)
        # Whole Contracts tests read these repositories. Each comes from the
        # producer's actual gitlink, with no recursive submodule operation.
        for name in ("Hexalith.Builds", "Hexalith.AI.Tools", "Hexalith.Tenants"):
            relative = "references/" + name
            mode, kind, commit = git(owner, "ls-tree", SOURCE, relative).split("\t")[0].split()
            assert mode == "160000" and kind == "commit"
            if name == "Hexalith.Builds":
                assert commit == BUILDS
            clone(name, commit, owner / relative)
        for relative in INPUTS:
            raw = subprocess.check_output(["git", "--no-replace-objects", "-C", str(owner),
                                           "show", SOURCE + ":" + relative], env=env)
            target = output / "committed-inputs" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            result["inputs"][relative] = {"blob": git(owner, "rev-parse", SOURCE + ":" + relative),
                                          "sha256": sha256(target)}
        result["builds_catalog_sha256"] = sha256(owner / "references/Hexalith.Builds/Props/Directory.Packages.props")
        result["release_package_inventory"] = json.loads((owner / "tools/release-packages.json").read_text())
        assert len(result["release_package_inventory"]["packages"]) == 14
        run("dotnet-info", ["dotnet", "--info"], cwd=owner, required=True)
        flags = ["-p:UseHexalithProjectReferences=false", "-p:UseNuGetDeps=true"]
        ready = {}
        for name, project in PROJECTS.items():
            evaluation, text = run(name + "-properties", ["dotnet", "msbuild", project,
                "-p:Configuration=Release", *flags,
                "-getProperty:Configuration,UseHexalithProjectReferences,UseNuGetDeps,NuGetAudit,NuGetAuditMode,NuGetAuditLevel,TreatWarningsAsErrors,RunAnalyzers,RunAnalyzersDuringBuild,EnableNETAnalyzers,NoWarn,WarningsNotAsErrors"], cwd=owner)
            result["checks"][name + "-properties"] = evaluation
            restore, _ = run(name + "-restore", ["dotnet", "restore", project,
                "-p:Configuration=Release", *flags], cwd=owner)
            result["checks"][name + "-restore"] = restore
            if restore:
                ready[name] = False
                result["checks"][name + "-build"] = {"unrun": "restore failed"}
            else:
                build, _ = run(name + "-build", ["dotnet", "build", project, "--no-restore",
                    "--configuration", "Release", "-warnaserror", "-m:1", *flags], cwd=owner)
                result["checks"][name + "-build"] = build
                ready[name] = build == 0
        for name in ("generators", "contracts"):
            if not ready[name]:
                result["test_results"][name] = {"unrun": "restore/build failed", "native_exit": None}
                continue
            reports = work / "reports" / name
            code, _ = run(name + "-test", ["dotnet", "test", PROJECTS[name], "--no-build",
                "--configuration", "Release", "--results-directory", str(reports),
                "--report-xunit-trx", "--report-xunit-trx-filename", name + ".trx", *flags], cwd=owner)
            summary = {"native_exit": code, "reports": []}
            if reports.exists():
                shutil.copytree(reports, output / "test-results" / name)
                for trx in sorted((output / "test-results" / name).rglob("*.trx")):
                    root = ET.parse(trx).getroot()
                    ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
                    counters = root.find("t:ResultSummary/t:Counters", ns)
                    outcomes = root.findall("t:Results/t:UnitTestResult", ns)
                    summary["reports"].append({"path": str(trx.relative_to(output)),
                        "sha256": sha256(trx), "counters": counters.attrib if counters is not None else None,
                        "nonpassing": [dict(item.attrib) | {"detail": "".join(item.itertext()).strip()}
                                       for item in outcomes if item.get("outcome") != "Passed"],
                        "typed_query_compilation_tests": [dict(item.attrib) for item in outcomes
                            if "TypedGatewayQueryGenerationTests" in item.get("testName", "")]})
            result["test_results"][name] = summary
            result["checks"][name + "-test"] = code
            save()
        for name in result["dependencies"]:
            directory = owner if name == "Hexalith.EventStore" else owner / "references" / name
            code, text = run("final-source-" + name,
                             ["git", "diff", "--exit-code", "HEAD", "--"], cwd=directory)
            result["dependencies"][name]["tracked_source_unchanged"] = code == 0
            nested = []
            for line in git(directory, "ls-tree", "-r", "HEAD").splitlines():
                if line.startswith("160000 "):
                    relative = line.split("\t", 1)[1]
                    if name == "Hexalith.EventStore" and relative in {
                            "references/Hexalith.Builds", "references/Hexalith.AI.Tools", "references/Hexalith.Tenants"}:
                        continue
                    if (directory / relative / ".git").exists():
                        nested.append(relative)
            result["dependencies"][name]["unexpected_initialized_dependencies"] = nested
            assert code == 0 and not nested
        run("later-observed-main", ["git", "ls-remote", "--refs", "origin", "refs/heads/main"], cwd=owner)
        result["focused_checks_passed"] = (
            all(value == 0 for value in result["checks"].values()) and
            all(item.get("reports") and all(
                report.get("counters") and int(report["counters"].get("failed", "1")) == 0
                for report in item["reports"]) for item in result["test_results"].values()))
        result["completed_utc"] = utc()
        save()
        return 0 if result["focused_checks_passed"] else 1
    except Exception as error:
        result["fatal_error"] = str(error)
        result["completed_utc"] = utc()
        (output / "helper-error.log").write_text(traceback.format_exc())
        save()
        raise


if __name__ == "__main__":
    sys.exit(main())
