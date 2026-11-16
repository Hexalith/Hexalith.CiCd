from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import time

source = Path('/home/administrator/projects/hexalith/cicd/references/Hexalith.Projects')
root = Path(os.environ['TMPDIR']) / 'Hexalith.Projects'
results = Path('/home/administrator/projects/hexalith/cicd/_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116')
paths = ['tests/Hexalith.Projects.Integration.Tests/' + name for name in ('PackageReadFixture.cs', 'PackageFreshCutoverTests.cs', 'PackageOwnerArtifactSelectionTests.cs', 'PackageCredentialMatrixTests.cs', 'PackageOwnerLoadContextTests.cs', 'PackageFixtureSafetyTests.cs')]
paths += ['tests/Hexalith.Projects.PackageFixtures.AppHost/' + name for name in ('PackageActualOwnerInfrastructure.cs', 'PackageActualOwnerComposition.cs', 'PackageOwnerLoadContext.cs')]
paths += ['tests/Hexalith.Projects.PackageFixtures/' + name for name in ('FixtureInputs.cs', 'FixtureDiagnostics.cs', 'Program.cs')]
inputs = {}
for relative in paths:
    target = root / relative
    shutil.copyfile(source / relative, target)
    inputs[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
(results / 'runtime-iteration-5-inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
flags = ['--configuration', 'Release', '--no-restore', '--disable-build-servers', '-noAutoResponse',
         '-p:UseHexalithProjectReferences=false', '-p:ShouldUnsetParentConfigurationAndPlatform=false',
         '-p:RestoreConfigFile=' + str(root / 'references/Hexalith.Builds/NuGet.ci.Config'),
         '-p:EnableNETAnalyzers=true', '-p:RunAnalyzers=true', '-p:RunAnalyzersDuringBuild=true',
         '-p:UseSharedCompilation=false', '-warnaserror', '-m:1', '-nr:false']
def run(command, name):
    with (results / name).open('w') as output:
        result = subprocess.run(command, cwd=root, stdout=output, stderr=subprocess.STDOUT)
    print(name, 'EXIT', result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
run(['dotnet', 'build', 'tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj', *flags], 'runtime-iteration-5-build.log')
run(['dotnet', 'tests/Hexalith.Projects.Integration.Tests/bin/Release/net11.0/Hexalith.Projects.Integration.Tests.dll',
     *[value for name in ('PackageFreshCutoverTests','PackageOwnerArtifactSelectionTests','PackageFixtureSafetyTests','PackageCredentialMatrixTests','PackageOwnerLoadContextTests')
       for value in ('-class', 'Hexalith.Projects.Integration.Tests.' + name)], '-noColor', '-failSkips'], 'runtime-iteration-5-tests.log')
