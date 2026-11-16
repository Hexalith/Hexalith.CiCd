#!/usr/bin/env python3
"""Qualify a finite Timesheets net10 catalog candidate without changing module pins.

This deliberately tests unreleased Builds source in a disposable standalone
workspace. It is prerequisite research, never registration/pre-push acceptance.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET


EVIDENCE = Path(__file__).resolve().parent
WORKSPACE = EVIDENCE.parents[4]
MODULE = WORKSPACE / "references/Hexalith.Timesheets"
BUILDS = WORKSPACE / "references/Hexalith.Builds"


def git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


def candidate(content: bytes) -> bytes:
    text = content.decode().replace("\r\n", "\n")
    projects = sorted(Path(node.attrib["Path"]).stem for node in ET.parse(MODULE / "Hexalith.Timesheets.slnx").findall(".//Project"))
    selector = "\n        or ".join("$(MSBuildProjectName.Equals('" + project + "'))" for project in projects)
    view = ('    <!-- Preserve the measured net10 product/consumer contract for these exact Timesheets identities. -->\n'
            '    <HexalithTimesheetsNet10CatalogView>false</HexalithTimesheetsNet10CatalogView>\n'
            '    <HexalithTimesheetsNet10CatalogView Condition="' + selector + '">true</HexalithTimesheetsNet10CatalogView>\n')
    for name, version in (("HexalithCommonsVersion", "2.30.11"), ("HexalithPolymorphicSerializationsVersion", "1.19.9")):
        view += f'    <{name} Condition="\'$(HexalithTimesheetsNet10CatalogView)\' == \'true\' and \'$({name})\' == \'\'">{version}</{name}>\n'
    needle = '    <HexalithCommonsVersion Condition="'
    assert text.count(needle) == 1
    text = text.replace(needle, view + needle, 1)
    # Reuse the existing retained SDK4.2/OpenAPI2 family condition; source mode
    # retains the existing SDK-current behavior and caller-supplied versions.
    selected = "'$(HexalithBuildsPackagedHostSdk42CatalogView)' == 'true')"
    assert text.count(selected) >= 3
    text = text.replace(selected, "'$(HexalithBuildsPackagedHostSdk42CatalogView)' == 'true' or '$(HexalithTimesheetsNet10CatalogView)' == 'true')")
    excluded = "'$(HexalithBuildsPackagedHostSdk42CatalogView)' != 'true'))"
    assert text.count(excluded) == 1
    text = text.replace(excluded, "'$(HexalithBuildsPackagedHostSdk42CatalogView)' != 'true' and '$(HexalithTimesheetsNet10CatalogView)' != 'true'))")
    for package in ("Microsoft.AspNetCore.Mvc.Testing", "Microsoft.AspNetCore.Authentication.JwtBearer", "Microsoft.AspNetCore.TestHost"):
        old = f'    <PackageVersion Include="{package}" Version="11.0.0" />'
        assert text.count(old) == 1, package
        new = (f'    <PackageVersion Include="{package}" Version="11.0.0" Condition="\'$(HexalithTimesheetsNet10CatalogView)\' != \'true\'" />\n'
               f'    <PackageVersion Include="{package}" Version="10.0.15" Condition="\'$(HexalithTimesheetsNet10CatalogView)\' == \'true\'" />')
        text = text.replace(old, new)
    return text.replace("\n", "\r\n").encode() if b"\r\n" in content else text.encode()


def main() -> int:
    original = (BUILDS / "Props/Directory.Packages.props").read_bytes()
    followup = os.environ.get("TIMESHEETS_SCOPED_FOLLOWUP") == "1"
    frozen = json.loads((EVIDENCE / "catalog-final-check.json").read_text()) if followup else None
    if followup:
        blob = subprocess.check_output(["git", "-C", str(BUILDS), "show",
                                        frozen["revisions"]["builds_source"] + ":Props/Directory.Packages.props"])
        original = next(data for data in (blob, blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
                        if hashlib.sha256(data).hexdigest() == frozen["inputs"]["catalog_source_sha256"])
    proposed = candidate(original)
    source = frozen["revisions"]["builds_source"] if followup else git(BUILDS, "rev-parse", "HEAD")
    scratch = Path(os.environ["TMPDIR"])
    clone = scratch / "Timesheets"
    subprocess.run(["git", "clone", "--shared", "--no-checkout", str(MODULE), str(clone)], check=True)
    head = git(MODULE, "rev-parse", "HEAD")
    subprocess.run(["git", "-C", str(clone), "checkout", "--detach", head], check=True)
    patch = subprocess.check_output(["git", "-C", str(MODULE), "diff", "--binary", "HEAD"])
    if patch:
        subprocess.run(["git", "-C", str(clone), "apply"], input=patch, check=True)
    additions = ["scripts/tests/test_product_packages.py", "tests/Hexalith.Timesheets.ArchitectureTests/FitnessTests/AppHostDependencyTests.cs",
                 "tools/product-validation.json", *[path.relative_to(MODULE).as_posix() for path in sorted((MODULE / "tools/package-consumers").glob("*.cs"))]]
    for relative in additions:
        (clone / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MODULE / relative, clone / relative)
    revisions = {"module": head, "builds_source": source}
    for name in ("Builds", "EventStore", "Works"):
        relative = "references/Hexalith." + name
        revision = source if name == "Builds" else git(MODULE, "rev-parse", head + ":" + relative)
        revisions[relative] = revision
        archive = scratch / (name + ".tar")
        subprocess.run(["git", "-C", str(WORKSPACE / relative), "archive", "--output", str(archive), revision], check=True)
        target = clone / relative
        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as stream:
            stream.extractall(target, filter="data")
    (clone / "references/Hexalith.Builds/Props/Directory.Packages.props").write_bytes(proposed)
    (EVIDENCE / "catalog-candidate.patch").write_text("".join(difflib.unified_diff(
        original.decode().splitlines(keepends=True), proposed.decode().splitlines(keepends=True),
        fromfile="a/Props/Directory.Packages.props", tofile="b/Props/Directory.Packages.props")))
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", DOTNET_CLI_HOME=str(scratch / "dotnet-home"),
                       DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", MSBUILDDISABLENODEREUSE="1",
                       TIMESHEETS_TEST_CONFIGURATION="Release")
    runner = clone / "references/Hexalith.Builds/Github/lib/product_validation.py"
    shutil.copy2(BUILDS / "Github/lib/product_validation.py", runner)
    results = []
    if followup:
        script = clone / "scripts/run_isolated_magic_link_dapr.py"
        fixed = script.read_bytes()
        try:
            script.write_bytes(fixed.replace(b"except (FileNotFoundError, ProcessLookupError):", b"except FileNotFoundError:", 1))
            command = ["python3", "-B", "scripts/test_isolated_magic_link_dapr.py", "-v",
                       "IsolatedFixtureTests.test_process_group_scan_ignores_only_disappearing_processes"]
            log = EVIDENCE / "fixture-esrch-red-regression.log"
            with log.open("w") as stream:
                red = subprocess.run(command, cwd=clone, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=False)
            assert red.returncode and "ProcessLookupError" in log.read_text(), "old helper must expose the injected ESRCH race"
            results.append({"job": "fixture-esrch-red-regression", "command": command, "exit_code": red.returncode,
                            "expected_failure": True, "log": log.name})
        finally:
            script.write_bytes(fixed)
    commands = [("final-catalog-candidate-build", ["dotnet", "build", "Hexalith.Timesheets.slnx", "--configuration", "Release",
                                           "-p:UseHexalithProjectReferences=false", "-warnaserror", "-m:1", "/nr:false"])]
    assembly = "tests/Hexalith.Timesheets.Projections.Tests/bin/Release/net10.0/Hexalith.Timesheets.Projections.Tests.dll"
    for label, method in [("bootstrap-latency-after-fix", "MagicLinkBootstrapLatencyTests.DelayedCombinedInventoryPersistsV7WithinGatewayAttemptBudget"),
                          ("bootstrap-reservation-regressions", "MagicLinkGlobalIndexEpochTests.StreamedBootstrapRefusesReservationChangesDuringSelectedInventory")]:
        commands.append((label, ["dotnet", assembly, "-method", "Hexalith.Timesheets.Projections.Tests." + method,
                                "-xml", str(EVIDENCE / (label + ".xml"))]))
    projects = sorted(node.attrib["Path"] for node in ET.parse(clone / "Hexalith.Timesheets.slnx").findall(".//Project") if node.attrib["Path"].startswith("tests/"))
    projects.sort(key=lambda path: ("IntegrationTests" in path, path))
    commands += [("final-" + Path(project).stem, ["dotnet", "test", "--project", project, "--configuration", "Release",
                                     "--no-build", "--no-restore", "-p:UseHexalithProjectReferences=false"]) for project in projects]
    commands += [
        ("final-apphost-configuration", ["python3", "scripts/check_magic_link_apphost_guards.py", "--configuration-only",
                                        "--configuration", "Release", "--log-directory", str(EVIDENCE / "apphost-configuration")]),
        ("final-fixture-privacy-tests", ["python3", "scripts/test_isolated_magic_link_dapr.py", "-v"]),
        ("final-real-package-validation", ["python3", "-I", str(runner), "--workspace", str(clone),
                                           "--contract", "tools/product-validation.json"]),
    ]
    if followup:
        server = "tests/Hexalith.Timesheets.Server.Tests/bin/Release/net10.0/Hexalith.Timesheets.Server.Tests.dll"
        commands = [
            ("scoped-followup-build", ["dotnet", "build", "Hexalith.Timesheets.slnx", "--configuration", "Release",
                                       "-p:UseHexalithProjectReferences=false", "-warnaserror", "-m:1", "/nr:false"]),
            ("fixture-esrch-focused", ["python3", "-B", "scripts/test_isolated_magic_link_dapr.py", "-v",
                                      "IsolatedFixtureTests.test_process_group_scan_ignores_only_disappearing_processes",
                                      "IsolatedFixtureTests.test_process_group_scan_preserves_permission_and_malformed_stat_refusals",
                                      "IsolatedFixtureTests.test_vanished_proc_entry_during_timeout_still_kills_and_reaps_descendants",
                                      "IsolatedFixtureTests.test_real_journey_interruption_terminates_and_reaps_descendants"]),
            ("fixture-privacy-followup", ["python3", "-B", "scripts/test_isolated_magic_link_dapr.py", "-v"]),
            ("server-polling-source-complete", ["dotnet", server, "-method",
                                                "Hexalith.Timesheets.Server.Tests.MagicLinkDurableSubmissionServiceTests.ProcessingStatusIsPolledToTheConfiguredDeadlineAndDenied",
                                                "-xml", str(EVIDENCE / "server-polling-source-complete.xml")]),
            ("server-suite-source-complete", ["dotnet", "test", "--project", "tests/Hexalith.Timesheets.Server.Tests/Hexalith.Timesheets.Server.Tests.csproj",
                                              "--configuration", "Release", "--no-build", "--no-restore", "-p:UseHexalithProjectReferences=false"]),
            ("current-runner-real-packages", ["python3", "-B", "-I", str(runner), "--workspace", str(clone),
                                              "--contract", "tools/product-validation.json"]),
        ]
    status = EVIDENCE / ("catalog-scoped-followup.json" if followup else "catalog-final-check.json")
    inputs = {"module_patch_sha256": hashlib.sha256(patch).hexdigest(),
              "runner_sha256": hashlib.sha256(runner.read_bytes()).hexdigest(),
              "catalog_source_sha256": hashlib.sha256(original).hexdigest(),
              "catalog_candidate_sha256": hashlib.sha256(proposed).hexdigest()}
    for name, command in commands:
        log = EVIDENCE / (name + ".log")
        with log.open("w") as stream:
            result = subprocess.run(command, cwd=clone, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=False)
        results.append({"job": name, "command": command, "exit_code": result.returncode, "log": log.name})
        status.write_text(json.dumps({"scope": "fresh non-relocated unreleased candidate; sequential local checks only",
                                      "complete": False, "revisions": revisions, "inputs": inputs, "results": results}, indent=2) + "\n")
        print(name + ": " + str(result.returncode), flush=True)
        if result.returncode and name in ("final-catalog-candidate-build", "scoped-followup-build"):
            break
    output = {"scope": "unreleased source catalog qualification only; no owned module edits, registration or pre-push acceptance",
              "revisions": revisions, "catalog_source_sha256": hashlib.sha256(original).hexdigest(),
              "catalog_candidate_sha256": hashlib.sha256(proposed).hexdigest(), "results": results,
              "live_catalog_still_matches_source": (BUILDS / "Props/Directory.Packages.props").read_bytes() == original}
    output.update(complete=True, inputs=inputs)
    status.write_text(json.dumps(output, indent=2) + "\n")
    return int(any(result["exit_code"] for result in results if not result.get("expected_failure")))


if __name__ == "__main__":
    raise SystemExit(main())
