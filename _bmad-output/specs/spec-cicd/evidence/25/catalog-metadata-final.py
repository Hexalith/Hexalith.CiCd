#!/usr/bin/env python3
"""Check the final proposal's finite roles without changing the running catalog."""

import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


EVIDENCE = Path(__file__).resolve().parent
WORKSPACE = EVIDENCE.parents[4]
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("catalog_candidate", EVIDENCE / "catalog-candidate-check.py")
CANDIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CANDIDATE)


def main() -> int:
    final = json.loads((EVIDENCE / "catalog-final-check.json").read_text())
    live = (WORKSPACE / "references/Hexalith.Builds/Props/Directory.Packages.props").read_bytes()
    original = live
    if hashlib.sha256(original).hexdigest() != final["inputs"]["catalog_source_sha256"]:
        blob = subprocess.check_output(["git", "-C", str(WORKSPACE / "references/Hexalith.Builds"), "show",
                                        final["revisions"]["builds_source"] + ":Props/Directory.Packages.props"])
        variants = [blob, blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")]
        original = next(data for data in variants if hashlib.sha256(data).hexdigest() == final["inputs"]["catalog_source_sha256"])
    proposed = CANDIDATE.candidate(original)
    root = Path(os.environ["TMPDIR"])
    catalog = root / "Directory.Packages.props"
    catalog.write_bytes(proposed)
    (root / "global.json").write_text('{"sdk":{"version":"11.0.100","rollForward":"latestPatch"}}')
    (EVIDENCE / "catalog-candidate-final.patch").write_text("".join(difflib.unified_diff(
        original.decode().splitlines(keepends=True), proposed.decode().splitlines(keepends=True),
        fromfile="a/Props/Directory.Packages.props", tofile="b/Props/Directory.Packages.props")))
    properties = ["MSBuildProjectName", "HexalithTimesheetsNet10CatalogView", "HexalithEventStoreVersion",
                  "HexalithCommonsVersion", "HexalithPolymorphicSerializationsVersion", "HexalithTenantsVersion",
                  "HexalithMemoriesVersion", "HexalithMcpCliVersion", "HexalithAspNetCoreOpenApiVersion", "HexalithOpenApiVersion"]
    overrides = {name: "99." + str(number) + ".0" for number, name in enumerate(properties[2:], 1)}
    cases = [("Hexalith.Timesheets.Works", False, {}), ("Hexalith.Timesheets.Works.Tests", False, {}),
             ("Unrelated", False, {}), ("Hexalith.Works.Contracts", False, {}),
             ("Hexalith.Timesheets.Works", True, {}), ("Hexalith.Timesheets.Works", False, overrides)]
    results = []
    for name, source, selected_overrides in cases:
        project = root / (name + ".proj")
        document = ET.Element("Project")
        ET.SubElement(document, "Import", Project=str(catalog))
        ET.ElementTree(document).write(project, encoding="utf-8")
        command = ["dotnet", "msbuild", str(project), "-p:UseHexalithProjectReferences=" + str(source).lower(),
                   "-getProperty:" + ",".join(properties), "-getItem:PackageVersion",
                   *["-p:" + key + "=" + value for key, value in selected_overrides.items()]]
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=True)
        data = json.loads(result.stdout)
        actual = data["Properties"]
        packages = {item["Identity"]: item["Version"] for item in data["Items"]["PackageVersion"]}
        selected = name.startswith("Hexalith.Timesheets.")
        sdk42 = selected and not source
        expected = {"MSBuildProjectName": name, "HexalithTimesheetsNet10CatalogView": str(selected).lower(),
                    "HexalithEventStoreVersion": "4.2.0" if sdk42 else "5.1.1",
                    "HexalithCommonsVersion": "2.30.11" if selected else "3.0.0",
                    "HexalithPolymorphicSerializationsVersion": "1.19.9" if selected else "2.0.0",
                    "HexalithTenantsVersion": "7.0.7" if sdk42 else "8.0.0",
                    "HexalithMemoriesVersion": "3.0.27" if sdk42 else "4.0.0",
                    "HexalithMcpCliVersion": "2.0.1" if sdk42 else "3.0.0",
                    "HexalithAspNetCoreOpenApiVersion": "10.0.15" if sdk42 else "11.0.0",
                    "HexalithOpenApiVersion": "2.13.0" if sdk42 else "3.11.0"}
        expected.update(selected_overrides)
        assert actual == expected, {"role": name, "source_mode": source, "actual": actual, "expected": expected}
        selected_packages = {}
        for package in ("Microsoft.AspNetCore.Mvc.Testing", "Microsoft.AspNetCore.Authentication.JwtBearer", "Microsoft.AspNetCore.TestHost"):
            assert packages[package] == ("10.0.15" if selected else "11.0.0")
            selected_packages[package] = packages[package]
        for package, name in (("Microsoft.AspNetCore.OpenApi", "HexalithAspNetCoreOpenApiVersion"), ("Microsoft.OpenApi", "HexalithOpenApiVersion")):
            assert packages[package] == expected[name]
            selected_packages[package] = packages[package]
        results.append({"role": actual["MSBuildProjectName"], "source_mode": source,
                        "explicit_overrides": selected_overrides, "properties": actual, "selected_packages": selected_packages})
    report = {"scope": "metadata-only final proposal; no live catalog edits or production qualification",
              "frozen_full_run_candidate_sha256": final["inputs"]["catalog_candidate_sha256"],
              "proposal_sha256": hashlib.sha256(proposed).hexdigest(),
              "concurrent_live_catalog_sha256": hashlib.sha256(live).hexdigest(),
              "concurrent_live_catalog_matches_proposal": live == proposed,
              "delta_from_frozen_run": "Timesheets negative exclusion added to the initial Tenants 8 default; selected package mode now evaluates Tenants 7.0.7",
              "consumed_graph_affected": False,
              "graph_evidence": "All 16 frozen candidate project.assets.json files inspected while the candidate existed; none consumes Hexalith.Tenants, Hexalith.Memories or Hexalith.McpCli",
              "cases": results}
    (EVIDENCE / "catalog-metadata-final.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Six catalog package/source/unrelated/Works-owner/explicit-override cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
