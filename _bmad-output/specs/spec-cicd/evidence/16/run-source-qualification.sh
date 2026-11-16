#!/usr/bin/env bash
set -euo pipefail
: "${TMPDIR:?Run this script through run-with-temp}"
source_root=$(realpath "${1:?Builds source required}")
evidence_root=$(realpath "${2:?evidence directory required}")
export source_root
python3 - <<'PY'
import os, pathlib, subprocess, shutil
root=pathlib.Path(os.environ['source_root']); target=pathlib.Path(os.environ['TMPDIR'])/'source'
for name in subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).decode().split('\0'):
    if name and (root/name).is_file():
        dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,dest)
PY
cd "$TMPDIR/source"
flags=(-p:Version=6.1.0 -p:PackageVersion=6.1.0 -p:MinVerVersionOverride=6.1.0)
dotnet build test/Hexalith.Builds.Module.Tests/Hexalith.Builds.Module.Tests.csproj --configuration Release -m:1 "${flags[@]}" -p:UseHexalithProjectReferences=false -warnaserror > "$evidence_root/managed-producer-build.log" 2>&1
mkdir "$TMPDIR/feed"
dotnet pack src/libraries/Hexalith.Builds.Module.Cli/Hexalith.Builds.Module.Cli.csproj --no-build --no-restore --configuration Release "${flags[@]}" --output "$TMPDIR/feed" > "$evidence_root/source-package-qualification.log" 2>&1
cat > "$TMPDIR/NuGet.Config" <<XML
<configuration><packageSources><clear/><add key="private-source-qualification" value="$TMPDIR/feed"/></packageSources></configuration>
XML
dotnet tool install Hexalith.Builds.Module.Cli --version 6.1.0 --tool-path "$TMPDIR/tool" --configfile "$TMPDIR/NuGet.Config" >> "$evidence_root/source-package-qualification.log" 2>&1
export HEXALITH_MANAGED_SOURCE_PACKAGE_TOOL="$TMPDIR/tool/hexalith-module"
"$HEXALITH_MANAGED_SOURCE_PACKAGE_TOOL" --help >> "$evidence_root/source-package-qualification.log" 2>&1
dotnet test/Hexalith.Builds.Module.Tests/bin/Release/net11.0/Hexalith.Builds.Module.Tests.dll -class '*ManagedBuildPreparationTests' -class '*IsolatedBuildReferenceContractTests' -noLogo > "$evidence_root/managed-producer-tests.log" 2>&1

dotnet test/Hexalith.Builds.Module.Tests/bin/Release/net11.0/Hexalith.Builds.Module.Tests.dll -class 'Hexalith.Builds.ModuleTool.Tests.Workspace.BuildPreparationTests' -class '*PlatformIdentityTests' -class '*WorkspaceRootResolverTests' -noLogo > "$evidence_root/legacy-producer-regression.log" 2>&1

python3 "$evidence_root/qualify-adapter-source.py" "$TMPDIR/source" "$evidence_root/../../../../../references/Hexalith.Conversations" > "$evidence_root/managed-adapter-source-qualification.log" 2>&1
