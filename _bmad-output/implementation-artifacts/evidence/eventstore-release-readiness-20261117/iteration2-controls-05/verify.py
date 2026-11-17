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

from verification_core import (clean_environment, owned_run, trx_inventory, suite_passed,
                               suite_complete, capture_graphs, repository_unchanged,
                               JobInterrupted, JobCleanupError, unexpected_inputs, file_manifest)

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
    *[f"src/Hexalith.EventStore.{name}/Hexalith.EventStore.{name}.csproj" for name in ("Contracts", "Client", "RestApi.Generators")],
]


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


# Committed Builds policy at the frozen producer pin, not a new exception.
FROZEN_SECURITY_EXCEPTIONS = {"NoWarn": set(), "WarningsNotAsErrors": {"NU1901", "NU1902"}}
POLICY_PROPERTIES = ("Configuration,UseHexalithProjectReferences,UseNuGetDeps,NuGetAudit,NuGetAuditMode,"
    "NuGetAuditLevel,TreatWarningsAsErrors,RunAnalyzers,RunAnalyzersDuringBuild,EnableNETAnalyzers,"
    "_SkipAnalyzers,_ImplicitlySkipAnalyzers,NoWarn,WarningsNotAsErrors,ProjectAssetsFile,"
    "MSBuildProjectFullPath,BaseIntermediateOutputPath,OutputPath")


def validate_properties(properties, security_exceptions=None):
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
    permitted = FROZEN_SECURITY_EXCEPTIONS if security_exceptions is None else security_exceptions
    for name in ("NoWarn", "WarningsNotAsErrors"):
        actual = {code.strip().upper() for code in properties.get(name, "").replace(",", ";").split(";")
                  if code.strip().upper().startswith("NU19")}
        if actual != set(permitted.get(name, ())):
            errors.append(f"{name} vulnerability exceptions differ from frozen policy: {sorted(actual)}")
    return errors


def test_passed(summary, frozen):
    return suite_passed(summary, frozen)


def bounded_run(command, cwd, env, stream, bound=None):
    return owned_run(command, cwd, env, stream, bound)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output", type=Path, required=True)
    probes = parser.add_mutually_exclusive_group()
    probes.add_argument("--local-package-probes", action="store_true",
                        help="Supplement the baseline with real unpublished manifest packages and the skipped package probe bodies.")
    probes.add_argument("--authority-probe", action="store_true",
                        help="Reproduce the package-authority scan once with its original eight-minute bound.")
    probes.add_argument("--query-api-package-probe", action="store_true",
                        help="Pack only the real Contracts/Client/generator archives and compile a synthetic query consumer.")
    args = parser.parse_args()
    tmp = Path(os.environ["TMPDIR"]).resolve()
    if os.environ.get("TMP") != str(tmp) or os.environ.get("TEMP") != str(tmp):
        parser.error("Invoke with run-with-temp so TMPDIR/TMP/TEMP identify private scratch.")
    output = args.output.resolve()
    if output == tmp or tmp in output.parents:
        parser.error("Evidence must survive scratch cleanup; output must be outside TMPDIR.")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(Path(__file__).resolve(), output / "verify.py")
    for supporting in ("verification_core.py", "query_package_probe.py", "frozen-suite-inventories.json"):
        shutil.copy2(Path(__file__).resolve().parent / supporting, output / supporting)
    work = Path(tempfile.mkdtemp(prefix="eventstore-readiness-", dir=tmp))
    owner = work / "Hexalith.EventStore"
    env, quarantined = clean_environment(os.environ)
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
        "supporting_sha256": {name: sha256(output / name) for name in
                               ("verification_core.py", "query_package_probe.py", "frozen-suite-inventories.json")},
        "effective_inputs": {"quarantined_selector_names": quarantined,
                             "package_contract_directory": None,
                             "credential_profile_selection_preserved": True,
                             "GH_CONFIG_DIR": env.get("GH_CONFIG_DIR"),
                             "token_override_present": {name: name in env for name in ("GH_TOKEN", "GITHUB_TOKEN")}},
        "scratch": str(work), "commands": [], "inputs": {}, "dependencies": {},
        "test_results": {}, "checks": {}, "complete_release_acceptance": False,
        "filters": [], "source_changes_authorized_only_on_demonstrated_product_failure": True,
        "scope": "query-api-package-probe" if args.query_api_package_probe else "local-package-probes" if args.local_package_probes else "authority-probe" if args.authority_probe else "baseline",
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
        try:
            with log.open("wb") as stream:
                record.update(owned_run(command, cwd or work, env, stream, timeout_seconds))
        except (JobInterrupted, JobCleanupError, unexpected_inputs, file_manifest) as error:
            record.update(error.receipt)
            record.update(elapsed_seconds=round(time.monotonic()-started, 3),
                          finished_utc=utc(), log_sha256=sha256(log))
            save()
            raise
        record.update(elapsed_seconds=round(time.monotonic()-started, 3),
                      finished_utc=utc(), log_sha256=sha256(log))
        save()
        print(f"{utc()} EXIT {name}: {record['native_exit']}; timeout={record.get('timed_out', False)}", flush=True)
        if required and (record["native_exit"] or record.get("timed_out")):
            raise RuntimeError(f"{name} failed: exit {record['native_exit']}; see {log.name}")
        return record["native_exit"], log.read_text(errors="replace")

    def git(root, *arguments):
        name = "git-read-" + str(len(result["commands"]))
        _, text = run(name, ["git", "--no-replace-objects", "-C", str(root), *arguments], required=True)
        return text.strip()

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

    active_assets = []
    designated_outputs = {}

    def evaluate(name, project, cwd, flags=(), synthetic=False):
        command_name = name + "-properties"
        code, text = run(command_name, ["dotnet", "msbuild", str(project),
            "-p:Configuration=Release", *flags, "-target:_ComputeSkipAnalyzers",
            "-getProperty:" + POLICY_PROPERTIES], cwd=cwd, required=True)
        properties = json.loads(text)["Properties"]
        exceptions = {"NoWarn": set(), "WarningsNotAsErrors": set()} if synthetic else FROZEN_SECURITY_EXCEPTIONS
        errors = validate_properties(properties, exceptions)
        result.setdefault("evaluated_properties", {})[name] = {"values": properties,
            "validation_errors": errors, "command": command_name,
            "permitted_security_exceptions": {key: sorted(value) for key, value in exceptions.items()}}
        save()
        require(not errors, f"{name}: {errors}")
        project_path = Path(properties["MSBuildProjectFullPath"]).resolve()
        require(project_path == (Path(cwd) / project).resolve(), "Evaluated another project")
        asset_path = Path(properties["ProjectAssetsFile"].replace("\\", "/"))
        if not asset_path.is_absolute():
            asset_path = project_path.parent / asset_path
        active_assets.append({"assets_path": str(asset_path.resolve()),
                              "project_path": str(project_path), "evaluation_command": command_name})
        for key in ("BaseIntermediateOutputPath", "OutputPath"):
            path = (project_path.parent / properties[key].replace("\\", "/")).resolve()
            require(path.is_relative_to(work), "Build output escaped private scratch")
            designated_outputs[str(path)] = command_name
        result["active_assets"] = active_assets
        result["designated_build_outputs"] = designated_outputs
        save()
        return properties

    def validate_input_tree(name, directory, initial=False):
        recorded = result["dependencies"][name]["commit"]
        tracked = git(directory, "ls-tree", "-r", "--name-only", recorded).splitlines()
        dependencies = ("references/Hexalith.Builds", "references/Hexalith.AI.Tools", "references/Hexalith.Tenants") if name == "Hexalith.EventStore" else ()
        outputs = [str(Path(path).relative_to(directory)) for path in designated_outputs
                   if Path(path).is_relative_to(directory)]
        extra = unexpected_inputs(directory, tracked, outputs, dependencies)
        result["dependencies"][name]["unexpected_inputs_initial" if initial else "unexpected_inputs_final"] = extra
        save()
        require(not extra, f"Unexpected source/build inputs in {name}: {extra}")

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
        for name in result["dependencies"]:
            validate_input_tree(name, owner if name == "Hexalith.EventStore" else owner / "references" / name, initial=True)
        # Preserve the original broad CLI modes without treating ordinary SDK
        # outputs from referenced frozen projects as injected inputs. Query mode
        # uses only its narrower explicitly evaluated output directories.
        if not args.query_api_package_probe:
            for name in result["dependencies"]:
                directory = owner if name == "Hexalith.EventStore" else owner / "references" / name
                tracked = git(directory, "ls-tree", "-r", "--name-only", result["dependencies"][name]["commit"]).splitlines()
                for relative in tracked:
                    if relative.endswith(".csproj"):
                        for leaf in ("bin", "obj"):
                            path = (directory / relative).parent / leaf
                            designated_outputs[str(path)] = "SDK output for frozen tracked project " + relative
            result["designated_build_outputs"] = designated_outputs
            save()
        for relative in INPUTS:
            _, _ = run("input-" + str(len(result["inputs"])),
                       ["git", "--no-replace-objects", "-C", str(owner), "show", SOURCE + ":" + relative], required=True)
            raw = (output / result["commands"][-1]["log"]).read_bytes()
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
        selected_projects = {} if args.local_package_probes or args.authority_probe or args.query_api_package_probe else PROJECTS
        for name, project in selected_projects.items():
            evaluate(name, project, owner, flags)
            result["checks"][name + "-properties"] = 0
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
                result["effective_inputs"]["package_contract_directory"] = str(packages)
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
                    report = trx_inventory(trx)
                    report["path"] = str(trx.relative_to(output))
                    summary["reports"].append(report)
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
        if args.query_api_package_probe:
            from query_package_probe import probe
            result["query_api_package_probe"] = probe(owner, work, output, env, run, SOURCE, evaluate, save, result)
            result["checks"]["query-api-package-probe"] = 0 if result["query_api_package_probe"]["passed"] else 1
        result["resolved_package_graphs"] = capture_graphs(work, output, active_assets)
        for name in result["dependencies"]:
            directory = owner if name == "Hexalith.EventStore" else owner / "references" / name
            validate_input_tree(name, directory)
            recorded = result["dependencies"][name]["commit"]
            final_head = git(directory, "rev-parse", "HEAD")
            result["dependencies"][name]["final_head"] = final_head
            result["dependencies"][name]["final_head_matches_recorded_commit"] = final_head == recorded
            code, text = run("final-source-" + name,
                             ["git", "diff", "--exit-code", recorded, "--"], cwd=directory)
            result["dependencies"][name]["tracked_source_unchanged"] = code == 0
            nested = []
            for line in git(directory, "ls-tree", "-r", recorded).splitlines():
                if line.startswith("160000 "):
                    relative = line.split("\t", 1)[1]
                    if name == "Hexalith.EventStore" and relative in {
                            "references/Hexalith.Builds", "references/Hexalith.AI.Tools", "references/Hexalith.Tenants"}:
                        continue
                    if (directory / relative / ".git").exists():
                        nested.append(relative)
            result["dependencies"][name]["unexpected_initialized_dependencies"] = nested
            require(repository_unchanged(recorded, final_head, code, nested),
                    f"Source changed or nested dependency initialized in {name}")
        run("later-observed-main", ["git", "ls-remote", "--refs", "origin", "refs/heads/main"], cwd=owner)
        frozen = json.loads((output / "frozen-suite-inventories.json").read_text())["suites"]
        result["suite_inventories_complete"] = (set(result["test_results"]) == set(frozen) and
            all(suite_complete(item, frozen[name]) for name, item in result["test_results"].items()))
        result["focused_checks_passed"] = (not args.local_package_probes and not args.authority_probe and
            not args.query_api_package_probe and result["suite_inventories_complete"] and
            all(value == 0 for value in result["checks"].values()) and
            all(test_passed(item, frozen[name]) for name, item in result["test_results"].items()))
        result["package_probes_passed"] = (args.local_package_probes and
            all(value == 0 for value in result["checks"].values()) and
            len(result.get("local_candidate_packages", {}).get("archives", [])) == 14)
        result["authority_probe_passed"] = (args.authority_probe and
            result["checks"].get("package-authority-direct") == 0)
        result["completed_utc"] = utc()
        save()
        return 0 if (result["focused_checks_passed"] or result["package_probes_passed"] or
                     result["authority_probe_passed"] or result.get("query_api_package_probe", {}).get("passed")) else 1
    except BaseException as error:
        result["fatal_error"] = str(error)
        result["primary_error_type"] = type(error).__name__
        result["completed_utc"] = utc()
        (output / "helper-error.log").write_text(traceback.format_exc())
        save()  # Preserve primary error before any best-effort capture.
        try:
            result["resolved_package_graphs"] = capture_graphs(work, output, active_assets)
        except BaseException as capture_error:
            result["graph_capture_error"] = repr(capture_error)
        save()
        raise


if __name__ == "__main__":
    sys.exit(main())
