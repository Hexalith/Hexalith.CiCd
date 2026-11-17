#!/usr/bin/env python3
"""Verify the frozen EventStore producer; run only through run-with-temp.

No publication, submodule initialization, or shared checkout mutation occurs.
Every invocation requires a new output directory so failures remain preserved.
"""

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
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
    "tools/pack-release-packages.py", "tools/release_package_contract.py",
    "scripts/validate-consumer-package-references.py",
    "scripts/validate-eventstore-package-authority.ps1",
    "src/Hexalith.EventStore.Contracts/Queries/QueryResultContractAttribute.cs",
    "tests/Hexalith.EventStore.RestApi.Generators.Tests/TypedGatewayQueryGenerationTests.cs",
    *PROJECTS.values(),
]


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_properties(properties):
    expected = {
        "Configuration": "Release", "UseHexalithProjectReferences": "false",
        "UseNuGetDeps": "true", "NuGetAudit": "true", "NuGetAuditMode": "all",
        "NuGetAuditLevel": "low", "TreatWarningsAsErrors": "true", "EnableNETAnalyzers": "true",
    }
    errors = [f"{name}: expected {value!r}, evaluated {properties.get(name)!r}"
              for name, value in expected.items() if properties.get(name) != value]
    # _ComputeSkipAnalyzers is executed by the query. Blank public RunAnalyzers
    # properties use the SDK default; actual computed skips must remain off.
    for name in ("_SkipAnalyzers", "_ImplicitlySkipAnalyzers"):
        if properties.get(name) not in ("", "false"):
            errors.append(f"{name} must be off, evaluated {properties.get(name)!r}")
    for name in ("RunAnalyzers", "RunAnalyzersDuringBuild"):
        if properties.get(name) not in ("", "true"):
            errors.append(f"{name} disables or invalidates analyzers: {properties.get(name)!r}")
    return errors


def test_passed(summary):
    if summary.get("native_exit") != 0 or not summary.get("reports"):
        return False
    for report in summary["reports"]:
        counters = report.get("counters") or {}
        try:
            total, passed, executed = (int(counters[name]) for name in ("total", "passed", "executed"))
            if total <= 0 or passed <= 0 or total != passed or total != executed:
                return False
            if any(int(value) != 0 for name, value in counters.items()
                   if name not in {"total", "passed", "executed", "completed"}):
                return False
        except (ValueError, KeyError):
            return False
        if report.get("nonpassing") or report.get("result_rows") != total:
            return False
    return True


def bounded_run(command, cwd, env, stream, bound):
    """Run one Linux process tree with a bound, then reap its entire group."""
    # Become a subreaper so orphaned grandchildren can be waited for here.
    libc = ctypes.CDLL(None, use_errno=True)
    require(libc.prctl(36, 1, 0, 0, 0) == 0, "Could not enable child-subreaper custody")
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream,
                               stderr=subprocess.STDOUT, start_new_session=True)
    timed_out = False

    def members():
        group = []
        for entry in Path("/proc").iterdir():
            if entry.name.isdigit():
                try:
                    if os.getpgid(int(entry.name)) == process.pid:
                        group.append(int(entry.name))
                except ProcessLookupError:
                    pass
        return group

    def send(sig):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass

    def reap():
        while True:
            try:
                pid, _ = os.waitpid(-process.pid, os.WNOHANG)
            except ChildProcessError:
                return
            if pid == 0:
                return

    try:
        process.wait(timeout=bound)
    except subprocess.TimeoutExpired:
        timed_out = True
        send(signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            send(signal.SIGKILL)
            process.wait()
    # The direct native exit is now collected. Clean up and wait for any
    # remaining descendants even if the top-level process already exited.
    remaining_before_cleanup = members()
    if remaining_before_cleanup:
        send(signal.SIGTERM)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            reap()
            if not members():
                break
            time.sleep(0.05)
        if members():
            send(signal.SIGKILL)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            reap()
            if not members():
                break
            time.sleep(0.05)
    reap()
    remaining = members()
    require(not remaining, f"Bounded command tree cleanup incomplete: {remaining}")
    return {"native_exit": process.returncode, "timeout_seconds": bound, "timed_out": timed_out,
            "remaining_group_before_cleanup": remaining_before_cleanup, "remaining_group_after_cleanup": remaining,
            "process_tree_fully_waited": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output", type=Path, required=True)
    probes = parser.add_mutually_exclusive_group()
    probes.add_argument("--local-package-probes", action="store_true",
                        help="Supplement the baseline with real unpublished manifest packages and the skipped package probe bodies.")
    probes.add_argument("--authority-probe", action="store_true",
                        help="Reproduce the package-authority scan once with its original eight-minute bound.")
    args = parser.parse_args()
    tmp = Path(os.environ["TMPDIR"]).resolve()
    if os.environ.get("TMP") != str(tmp) or os.environ.get("TEMP") != str(tmp):
        parser.error("Invoke with run-with-temp so TMPDIR/TMP/TEMP identify private scratch.")
    output = args.output.resolve()
    if output == tmp or tmp in output.parents:
        parser.error("Evidence must survive scratch cleanup; output must be outside TMPDIR.")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(Path(__file__).resolve(), output / "verify.py")
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
        "scope": "local-package-probes" if args.local_package_probes else "authority-probe" if args.authority_probe else "baseline",
    }

    def save():
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    def run(name, command, cwd=None, required=False, timeout_seconds=None):
        log = output / (name + ".log")
        record = {"name": name, "command": [str(x) for x in command],
                  "cwd": str(cwd or work), "started_utc": utc(), "log": log.name}
        result["commands"].append(record)
        save()
        print(f"{utc()} START {name}", flush=True)
        started = time.monotonic()
        with log.open("wb") as stream:
            if timeout_seconds is None:
                process = subprocess.run(command, cwd=cwd or work, env=env,
                                         stdout=stream, stderr=subprocess.STDOUT, check=False)
                record["native_exit"] = process.returncode
            else:
                record.update(bounded_run(command, cwd or work, env, stream, timeout_seconds))
        record.update(elapsed_seconds=round(time.monotonic()-started, 3),
                      finished_utc=utc(), log_sha256=sha256(log))
        save()
        print(f"{utc()} EXIT {name}: {record['native_exit']}; timeout={record.get('timed_out', False)}", flush=True)
        if required and (record["native_exit"] or record.get("timed_out")):
            raise RuntimeError(f"{name} failed: exit {record['native_exit']}; see {log.name}")
        return record["native_exit"], log.read_text(errors="replace")

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
        require(git(destination, "rev-parse", "HEAD") == commit, f"Wrong checkout identity for {name}")
        require(not git(destination, "status", "--porcelain"), f"Dirty initial checkout for {name}")
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
            require(mode == "160000" and kind == "commit", f"{relative} must be a committed gitlink")
            if name == "Hexalith.Builds":
                require(commit == BUILDS, "Producer Builds gitlink differs from the frozen pin")
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
        require(len(result["release_package_inventory"]["packages"]) == 14, "Release inventory must contain fourteen packages")
        run("dotnet-info", ["dotnet", "--info"], cwd=owner, required=True)
        flags = ["-p:UseHexalithProjectReferences=false", "-p:UseNuGetDeps=true"]
        ready = {}
        selected_projects = {} if args.local_package_probes or args.authority_probe else PROJECTS
        for name, project in selected_projects.items():
            evaluation, text = run(name + "-properties", ["dotnet", "msbuild", project,
                "-p:Configuration=Release", *flags,
                "-target:_ComputeSkipAnalyzers",
                "-getProperty:Configuration,UseHexalithProjectReferences,UseNuGetDeps,NuGetAudit,NuGetAuditMode,NuGetAuditLevel,TreatWarningsAsErrors,RunAnalyzers,RunAnalyzersDuringBuild,EnableNETAnalyzers,_SkipAnalyzers,_ImplicitlySkipAnalyzers,NoWarn,WarningsNotAsErrors"], cwd=owner)
            properties = json.loads(text)["Properties"] if evaluation == 0 else {}
            errors = validate_properties(properties)
            result.setdefault("evaluated_properties", {})[name] = {"values": properties, "validation_errors": errors}
            result["checks"][name + "-properties"] = evaluation or int(bool(errors))
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
        if args.local_package_probes:
            packages = work / "local-candidate-packages"
            # A local-only prerelease above the current published cohort keeps
            # genuine transitive minimums (Tenants >= Contracts 5.1.1) intact.
            # This is no release selection and is never sent to a publisher.
            version = "5.2.1-local-readiness.3b2350e7"
            result["local_candidate_packages"] = {"version": version, "published": False, "archives": []}
            packed, _ = run("pack-manifest-local-candidate", ["python3", "tools/pack-release-packages.py",
                                                             str(packages), version], cwd=owner)
            result["checks"]["pack-manifest-local-candidate"] = packed
            for archive in sorted(packages.glob("*.nupkg")):
                result["local_candidate_packages"]["archives"].append({"name": archive.name,
                                                                       "sha256": sha256(archive)})
            if packed == 0:
                require(len(result["local_candidate_packages"]["archives"]) == 14,
                        "Local candidate must contain all fourteen real package archives")
                env["EVENTSTORE_PACKAGE_CONTRACT_DIR"] = str(packages)
                full_probe, _ = run("all-package-consumer-probes", ["python3",
                    "scripts/validate-consumer-package-references.py", str(packages)], cwd=owner)
                result["checks"]["all-package-consumer-probes"] = full_probe
                reminder_probe, reminder_text = run("reminder-package-consumer-probes", ["python3",
                    "scripts/validate-consumer-package-references.py", str(packages),
                    "--package", "Hexalith.EventStore.Contracts", "--package", "Hexalith.EventStore.Client",
                    "--package", "Hexalith.EventStore.DomainService"], cwd=owner)
                result["checks"]["reminder-package-consumer-probes"] = reminder_probe
                reminder_summary = "Validated 3 isolated package-only consumers" in reminder_text
                result["checks"]["reminder-three-consumer-summary"] = 0 if reminder_summary else 1
            else:
                result["package_input_blocker"] = "Manifest packing failed; original package skips remain unresolved."
        for name in (key for key in selected_projects if key != "gateway"):
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
                        "result_rows": len(outcomes),
                        "nonpassing": [dict(item.attrib) | {"detail": "".join(item.itertext()).strip()}
                                       for item in outcomes if item.get("outcome") != "Passed"],
                        "typed_query_compilation_tests": [dict(item.attrib) for item in outcomes
                            if "TypedGatewayQueryGenerationTests" in item.get("testName", "")]})
            result["test_results"][name] = summary
            result["checks"][name + "-test"] = code
            save()
        if args.authority_probe:
            catalog = owner / "references/Hexalith.Builds/Props/Directory.Packages.props"
            result["authority_inputs"] = {relative: sha256(owner / "references/Hexalith.Builds" / relative)
                for relative in ("Tools/validate-consumer-package-authority.ps1", "Tools/validate-central-package-versions.ps1")}
            code, _ = run("package-authority-direct", ["pwsh", "-NoProfile", "-File",
                "scripts/validate-eventstore-package-authority.ps1", "-RepositoryRoot", str(owner),
                "-CatalogPath", str(catalog)], cwd=owner, timeout_seconds=480)
            result["checks"]["package-authority-direct"] = 124 if result["commands"][-1].get("timed_out") else code
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
            require(code == 0 and not nested, f"Source changed or nested dependency initialized in {name}")
        run("later-observed-main", ["git", "ls-remote", "--refs", "origin", "refs/heads/main"], cwd=owner)
        result["focused_checks_passed"] = (not args.local_package_probes and not args.authority_probe and
            all(value == 0 for value in result["checks"].values()) and
            all(test_passed(item) for item in result["test_results"].values()))
        result["package_probes_passed"] = (args.local_package_probes and
            all(value == 0 for value in result["checks"].values()) and
            len(result.get("local_candidate_packages", {}).get("archives", [])) == 14)
        result["authority_probe_passed"] = (args.authority_probe and
            result["checks"].get("package-authority-direct") == 0)
        result["completed_utc"] = utc()
        save()
        return 0 if result["focused_checks_passed"] or result["package_probes_passed"] or result["authority_probe_passed"] else 1
    except Exception as error:
        result["fatal_error"] = str(error)
        result["completed_utc"] = utc()
        (output / "helper-error.log").write_text(traceback.format_exc())
        save()
        raise


if __name__ == "__main__":
    sys.exit(main())
