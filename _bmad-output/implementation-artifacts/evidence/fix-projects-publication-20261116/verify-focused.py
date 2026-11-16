"""Focused repair checks against retained binaries; never publication proof."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
source = Path(json.loads((HERE / "integration.json").read_text())["worktree"])
module = Path(os.environ["TMPDIR"]) / "Hexalith.Projects"
paths = ["tests/Hexalith.Projects.PackageFixtures/FixtureDiagnostics.cs",
         "tests/Hexalith.Projects.PackageFixtures/FixtureInputs.cs",
         "tests/Hexalith.Projects.PackageFixtures.AppHost/PackageActualOwnerComposition.cs",
         "tests/Hexalith.Projects.PackageFixtures.AppHost/PackageOwnerLoadContext.cs",
         "tests/Hexalith.Projects.PackageFixtures.AppHost/PackageActualOwnerInfrastructure.cs",
         "tests/Hexalith.Projects.PackageFixtures.AppHost/Hexalith.Projects.PackageFixtures.AppHost.csproj",
         "tests/Hexalith.Projects.Integration.Tests/PackageFixtureSafetyTests.cs",
         "tests/Hexalith.Projects.Integration.Tests/PackageOwnerLoadContextTests.cs",
         "tests/Hexalith.Projects.Integration.Tests/PackageOwnerMetadataTests.cs"]
hashes = {}
for relative in paths:
    shutil.copy2(source / relative, module / relative)
    hashes[relative] = hashlib.sha256((source / relative).read_bytes()).hexdigest()
(HERE / "focused-inputs.json").write_text(json.dumps({"scope": "current repair source with retained old product binaries; diagnostic only", "files": hashes}, indent=2) + "\n")
os.environ.update(DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", DOTNET_CLI_USE_MSBUILD_SERVER="0", MSBUILDDISABLENODEREUSE="1")
flags = ["--no-restore", "--disable-build-servers", "-noAutoResponse", "-p:Configuration=Release", "-warnaserror",
         "-p:UseHexalithProjectReferences=false", "-p:BuildProjectReferences=false",
         "-p:ShouldUnsetParentConfigurationAndPlatform=false", "-p:RestoreConfigFile=" + str(module / "references/Hexalith.Builds/NuGet.ci.Config"),
         "-p:EnableNETAnalyzers=true", "-p:RunAnalyzers=true", "-p:RunAnalyzersDuringBuild=true",
         "-p:UseSharedCompilation=false", "-nr:false", "-m:1"]
results = []
def run(label, command, cwd=module):
    print(label, json.dumps(command), flush=True)
    result = subprocess.run(command, cwd=cwd)
    results.append({"check": label, "command": command, "exitCode": result.returncode})
    (HERE / "focused-results.json").write_text(json.dumps(results, indent=2) + "\n")
    if result.returncode:
        raise SystemExit(result.returncode)
for name in ("Hexalith.Projects.PackageFixtures", "Hexalith.Projects.PackageFixtures.AppHost", "Hexalith.Projects.Integration.Tests"):
    run("diagnostic-build-" + name, ["dotnet", "build", "tests/" + name + "/" + name + ".csproj", *flags])
run("focused-repair-tests", ["dotnet", "tests/Hexalith.Projects.Integration.Tests/bin/Release/net11.0/Hexalith.Projects.Integration.Tests.dll",
    "-class", "Hexalith.Projects.Integration.Tests.PackageOwnerLoadContextTests",
    "-class", "Hexalith.Projects.Integration.Tests.PackageOwnerMetadataTests",
    "-class", "Hexalith.Projects.Integration.Tests.PackageFixtureSafetyTests",
    "-class", "Hexalith.Projects.Integration.Tests.PackageCredentialMatrixTests", "-noColor", "-failSkips"])
