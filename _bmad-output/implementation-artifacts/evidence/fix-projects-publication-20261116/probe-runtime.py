"""Locate the native timeout with bounded diagnostics; this is not publication proof."""
from pathlib import Path
import json
import os
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
integration = json.loads((HERE / "integration.json").read_text())
source = Path(integration["worktree"])
module = Path(os.environ["TMPDIR"]) / "Hexalith.Projects"
for relative in ("tests/Hexalith.Projects.PackageFixtures/FixtureDiagnostics.cs",
                 "tests/Hexalith.Projects.PackageFixtures/Program.cs"):
    shutil.copy2(source / relative, module / relative)
os.environ.update(GIT_PAGER="cat", PAGER="cat", NO_COLOR="1", TERM="dumb",
                  DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", DOTNET_CLI_USE_MSBUILD_SERVER="0", MSBUILDDISABLENODEREUSE="1")
config = module / "references/Hexalith.Builds/NuGet.ci.Config"
flags = ["-noAutoResponse", "-p:Configuration=Release", "-warnaserror", "-p:UseHexalithProjectReferences=false",
         "-p:ShouldUnsetParentConfigurationAndPlatform=false", "-p:RestoreConfigFile=" + str(config),
         "-p:EnableNETAnalyzers=true", "-p:RunAnalyzers=true", "-p:RunAnalyzersDuringBuild=true",
         "-p:UseSharedCompilation=false", "-nr:false", "-m:1"]
command = ["dotnet", "build", "tests/Hexalith.Projects.PackageFixtures.AppHost/Hexalith.Projects.PackageFixtures.AppHost.csproj",
           "--no-restore", "--disable-build-servers", *flags]
print("DIAGNOSTIC BUILD", json.dumps(command), flush=True)
result = subprocess.run(command, cwd=module)
if result.returncode:
    raise SystemExit(result.returncode)
print("DIAGNOSTIC RUN: unchanged complete product fixture; deadlines/assertions preserved", flush=True)
raise SystemExit(subprocess.run(["npm", "run", "test:package"], cwd=module / "tests/e2e").returncode)
