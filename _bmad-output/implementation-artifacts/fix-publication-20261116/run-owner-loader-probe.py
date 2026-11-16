"""Compile the exact loader in a BCL-only regression harness under wrapper TMPDIR."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

packet = Path(__file__).resolve().parent
root = packet.parents[2]
source = root / "references/Hexalith.Projects/tests/Hexalith.Projects.PackageFixtures.AppHost/PackageOwnerLoadContext.cs"
scratch = Path(os.environ["TMPDIR"]) / "probe"
scratch.mkdir()
shutil.copyfile(source, scratch / source.name)
shutil.copyfile(root / "references/Hexalith.Projects/global.json", scratch / "global.json")
shutil.copyfile(packet / "owner-loader-probe.cs", scratch / "Program.cs")
(scratch / "LoaderProbe.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net11.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup></Project>')
environment = dict(os.environ, DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", DOTNET_CLI_USE_MSBUILD_SERVER="0", MSBUILDDISABLENODEREUSE="1")
report = {"source_sha256": hashlib.sha256((scratch / source.name).read_bytes()).hexdigest(), "commands": []}
for command in (["dotnet", "build", "LoaderProbe.csproj", "--configuration", "Release", "--disable-build-servers", "-noAutoResponse", "-p:UseSharedCompilation=false", "-warnaserror"],
                ["dotnet", str(scratch / "bin/Release/net11.0/LoaderProbe.dll")]):
    result = subprocess.run(command, cwd=scratch, env=environment, capture_output=True, text=True, timeout=120)
    print(result.stdout + result.stderr, flush=True)
    report["commands"].append({"command": command, "exit_code": result.returncode, "output": result.stdout + result.stderr})
    (packet / "owner-loader-probe.json").write_text(json.dumps(report, indent=2) + "\n")
    if result.returncode: raise SystemExit(result.returncode)
