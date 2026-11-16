#!/usr/bin/env python3
"""Probe real SDK version evaluation and strict unsigned-candidate refusal.

This synthetic package is not Timesheets acceptance. Run with run-with-temp;
the unsigned fixture must fail under the shared required-signature policy.
"""

import json
import os
from pathlib import Path
import subprocess


EVIDENCE = Path(__file__).resolve().parent
WORKSPACE = EVIDENCE.parents[4]


def main() -> int:
    root = Path(os.environ["TMPDIR"]) / "module"
    root.mkdir()
    (root / "global.json").write_text('{"sdk":{"version":"11.0.100","rollForward":"latestPatch"}}')
    project = root / "Fixture.Contracts.csproj"
    project.write_text('''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>
<TargetFramework>net10.0</TargetFramework><PackageId>Fixture.Contracts</PackageId>
<Version>2.3.4</Version><PackageVersion>2.3.4</PackageVersion>
<IncludeSymbols>true</IncludeSymbols><SymbolPackageFormat>snupkg</SymbolPackageFormat>
<NuGetAudit>true</NuGetAudit><NuGetAuditMode>all</NuGetAuditMode>
</PropertyGroup></Project>''')
    (root / "Product.cs").write_text('namespace Fixture; public static class Product { public const string Marker = "fixture"; }')
    # Keep consumer sources outside the product's default compile glob.
    (root / "consumer.cs.txt").write_text('if (Fixture.Product.Marker != "fixture") throw new System.Exception("product contract");')
    (root / "consumers").mkdir()
    (root / "consumers/Consumer.cs").write_text((root / "consumer.cs.txt").read_text())
    project.write_text(project.read_text().replace('</Project>', '<ItemGroup><Compile Remove="consumers/**/*.cs" /></ItemGroup></Project>'))
    (root / "validate.py").write_text('import pathlib, sys; assert len(list(pathlib.Path(sys.argv[1]).glob("*.nupkg"))) == 1')
    (root / "packages.json").write_text(json.dumps({"packages": [{"id": "Fixture.Contracts", "project": project.name}]}))
    (root / "contract.json").write_text(json.dumps({"schema": "hexalith.product-validation.v1", "manifest": "packages.json",
        "archiveValidator": "validate.py", "targetFramework": "net10.0", "consumers": {"Fixture.Contracts": "consumers/Consumer.cs"}}))
    environment = os.environ.copy()
    environment.update(DOTNET_CLI_HOME=str(Path(os.environ["TMPDIR"]) / "cli-home"),
                       MSBUILDDISABLENODEREUSE="1", DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1")
    commands = [
        ["dotnet", "build", project.name, "--configuration", "Release", "-warnaserror", "-m:1", "/nr:false"],
        ["python3", "-I", str(WORKSPACE / "references/Hexalith.Builds/Github/lib/product_validation.py"),
         "--workspace", str(root), "--contract", "contract.json"],
    ]
    results = []
    combined = ""
    for command in commands:
        result = subprocess.run(command, cwd=root, env=environment, text=True, capture_output=True, check=False)
        combined += "Command: " + json.dumps(command) + "\n" + result.stdout + result.stderr + "\n"
        results.append({"command": command, "exit_code": result.returncode})
        if len(results) == 1 and result.returncode:
            break
    (EVIDENCE / "runner-real-sdk-probe.log").write_text(combined)
    expected = (len(results) == 2 and results[0]["exit_code"] == 0 and results[1]["exit_code"] != 0
                and "NU3004" in combined)
    (EVIDENCE / "runner-real-sdk-probe.json").write_text(json.dumps({
        "scope": "synthetic SDK 11/net10 package only; not Timesheets acceptance",
        "expected_unsigned_candidate_refusal": expected, "results": results}, indent=2) + "\n")
    print("Expected strict unsigned-candidate refusal: " + str(expected))
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
