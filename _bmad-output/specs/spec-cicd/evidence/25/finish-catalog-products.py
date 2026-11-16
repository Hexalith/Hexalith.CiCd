#!/usr/bin/env python3
"""Finish retained checks using relocated existing outputs; never rebuild the module."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET


EVIDENCE = Path(__file__).resolve().parent
WORKSPACE = EVIDENCE.parents[4]


def main() -> int:
    root = CANDIDATE_WORKSPACE
    original = CANDIDATE_ORIGINAL_WORKSPACE
    six = json.loads((EVIDENCE / "catalog-candidate-check.json").read_text())
    if not six["results"] or six["results"][0]["exit_code"]:
        raise RuntimeError("a successful full build is required for the retained checks")
    diagnostics = EVIDENCE / "catalog-remaining-suite-diagnostics.json"
    while not diagnostics.is_file() or not json.loads(diagnostics.read_text()).get("complete"):
        time.sleep(5)
    compiled = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (root / "src").rglob("*") if path.suffix in {".dll", ".pdb"} and "bin" in path.parts}
    relocated = []
    for path in root.rglob("*"):
        if path.is_file() and "obj" in path.parts and path.suffix in {".json", ".props", ".targets"}:
            data = path.read_text(encoding="utf-8")
            replaced = data.replace(str(original), str(root))
            if replaced != data:
                path.write_text(replaced, encoding="utf-8")
                relocated.append(path.relative_to(root).as_posix())
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", DOTNET_CLI_HOME=str(Path(os.environ["TMPDIR"]) / "cli-home"),
                       MSBUILDDISABLENODEREUSE="1", DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1",
                       TIMESHEETS_TEST_CONFIGURATION="Release")
    metadata = Path(os.environ["TMPDIR"]) / "metadata"
    metadata.mkdir()
    shutil.copy2(root / "global.json", metadata / "global.json")
    results, matrix = [], []
    roles = [("Hexalith.Timesheets.Works", False), ("Hexalith.Timesheets.Works.Tests", False),
             ("Unrelated", False), ("Hexalith.Works.Contracts", False), ("Hexalith.Timesheets.Works", True)]
    for name, source in roles:
        project = metadata / (name + ".proj")
        document = ET.Element("Project")
        ET.SubElement(document, "Import", Project=str(root / "references/Hexalith.Builds/Props/Directory.Packages.props"))
        ET.ElementTree(document).write(project, encoding="utf-8")
        command = ["dotnet", "msbuild", str(project), "-p:UseHexalithProjectReferences=" + str(source).lower(),
                   "-getProperty:MSBuildProjectName,HexalithEventStoreVersion,HexalithCommonsVersion,HexalithPolymorphicSerializationsVersion,HexalithTimesheetsNet10CatalogView",
                   "-getItem:PackageVersion"]
        result = subprocess.run(command, cwd=metadata, env=environment, text=True, capture_output=True, check=True)
        values = json.loads(result.stdout)
        properties = values["Properties"]
        packages = {item["Identity"]: item["Version"] for item in values["Items"]["PackageVersion"]}
        selected = name.startswith("Hexalith.Timesheets.")
        assert properties["MSBuildProjectName"] == name
        assert properties["HexalithTimesheetsNet10CatalogView"] == str(selected).lower()
        assert properties["HexalithEventStoreVersion"] == ("4.2.0" if selected and not source else "5.1.1")
        assert properties["HexalithCommonsVersion"] == ("2.30.11" if selected else "3.0.0")
        assert properties["HexalithPolymorphicSerializationsVersion"] == ("1.19.9" if selected else "2.0.0")
        for package in ("Microsoft.AspNetCore.Mvc.Testing", "Microsoft.AspNetCore.Authentication.JwtBearer", "Microsoft.AspNetCore.TestHost"):
            assert packages[package] == ("10.0.15" if selected else "11.0.0")
        matrix.append({"role": name, "source_mode": source, "properties": properties,
                       "selected_packages": {package: packages[package] for package in (
                           "Microsoft.AspNetCore.Mvc.Testing", "Microsoft.AspNetCore.Authentication.JwtBearer", "Microsoft.AspNetCore.TestHost")}})
    (EVIDENCE / "catalog-metadata-check.json").write_text(json.dumps(matrix, indent=2) + "\n")
    print("Catalog metadata: five package/source/unrelated/Works-owner cases passed.", flush=True)
    for name in ("product_validation.py",):
        shutil.copy2(WORKSPACE / "references/Hexalith.Builds/Github/lib" / name,
                     root / "references/Hexalith.Builds/Github/lib" / name)
    assembly = "tests/Hexalith.Timesheets.Projections.Tests/bin/Release/net10.0/Hexalith.Timesheets.Projections.Tests.dll"
    baseline_command = ["dotnet", assembly, "-method",
                        "Hexalith.Timesheets.Projections.Tests.MagicLinkBootstrapLatencyTests.DelayedCombinedInventoryPersistsV7WithinGatewayAttemptBudget",
                        "-xml", str(EVIDENCE / "bootstrap-latency-before-fix.xml")]
    with (EVIDENCE / "bootstrap-latency-before-fix.log").open("w") as stream:
        baseline = subprocess.run(baseline_command, cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=False)
    results.append({"job": "bootstrap-latency-before-fix", "command": baseline_command,
                    "exit_code": baseline.returncode, "log": "bootstrap-latency-before-fix.log"})
    print("Focused original bootstrap latency: " + str(baseline.returncode), flush=True)
    changes = ["src/Hexalith.Timesheets.Projections/MagicLinks/MagicLinkTokenHashCapabilityIndexProjectionHandler.cs",
               "tests/Hexalith.Timesheets.Projections.Tests/MagicLinkGlobalIndexEpochTests.cs"]
    for relative in changes:
        shutil.copy2(WORKSPACE / "references/Hexalith.Timesheets" / relative, root / relative)
    rebuild = ["dotnet", "build", "Hexalith.Timesheets.slnx", "--configuration", "Release", "--no-restore",
               "-p:UseHexalithProjectReferences=false", "-warnaserror", "-m:1", "/nr:false"]
    with (EVIDENCE / "catalog-product-fix-build.log").open("w") as stream:
        result = subprocess.run(rebuild, cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=False)
    results.append({"job": "catalog-product-fix-build", "command": rebuild, "exit_code": result.returncode,
                    "log": "catalog-product-fix-build.log"})
    print("Product-fix Release/package rebuild: " + str(result.returncode), flush=True)
    if result.returncode:
        (EVIDENCE / "catalog-retained-products.json").write_text(json.dumps({"results": results}, indent=2) + "\n")
        return 1
    compiled = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (root / "src").rglob("*") if path.suffix in {".dll", ".pdb"} and "bin" in path.parts}
    jobs = []
    for label, method in [("bootstrap-latency-after-fix", "MagicLinkBootstrapLatencyTests.DelayedCombinedInventoryPersistsV7WithinGatewayAttemptBudget"),
                          ("bootstrap-reservation-regressions", "MagicLinkGlobalIndexEpochTests.StreamedBootstrapRefusesReservationChangesDuringSelectedInventory")]:
        jobs.append((label, ["dotnet", assembly, "-method", "Hexalith.Timesheets.Projections.Tests." + method,
                             "-xml", str(EVIDENCE / (label + ".xml"))]))
    projects = sorted(node.attrib["Path"] for node in ET.parse(root / "Hexalith.Timesheets.slnx").findall(".//Project") if node.attrib["Path"].startswith("tests/"))
    projects.sort(key=lambda path: ("IntegrationTests" in path, path))
    jobs += [("fixed-" + Path(project).stem, ["dotnet", "test", "--project", project, "--configuration", "Release",
                                              "--no-build", "--no-restore", "-p:UseHexalithProjectReferences=false"]) for project in projects]
    jobs += [
        ("catalog-apphost-configuration", ["python3", "scripts/check_magic_link_apphost_guards.py", "--configuration-only",
                                          "--configuration", "Release", "--log-directory", str(EVIDENCE / "apphost-configuration")]),
        ("catalog-fixture-privacy-tests", ["python3", "scripts/test_isolated_magic_link_dapr.py", "-v"]),
        ("catalog-real-package-validation", ["python3", "-I", "references/Hexalith.Builds/Github/lib/product_validation.py",
                                             "--workspace", str(root), "--contract", "tools/product-validation.json"]),
    ]
    for name, command in jobs:
        log = EVIDENCE / (name + ".log")
        with log.open("w") as stream:
            result = subprocess.run(command, cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=False)
        results.append({"job": name, "command": command, "exit_code": result.returncode, "log": log.name})
        print(name + ": " + str(result.returncode), flush=True)
    unchanged = all(hashlib.sha256((root / path).read_bytes()).hexdigest() == digest for path, digest in compiled.items())
    assert unchanged, "retained checks changed an existing compiled product output"
    output = {"scope": "retained checks using the already-built unreleased catalog candidate; no main rebuild",
              "compiled_outputs_unchanged": unchanged, "compiled_output_sha256": compiled,
              "relocated_generated_path_metadata": relocated, "results": results}
    (EVIDENCE / "catalog-retained-products.json").write_text(json.dumps(output, indent=2) + "\n")
    return int(any(item["exit_code"] for item in results))


if __name__ == "__main__":
    raise SystemExit(main())
