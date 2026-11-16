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
# Keep the already frozen candidate; the diagnostic wrappers restored their source changes.
inputs = {}
for relative in ('tests/Hexalith.Projects.PackageFixtures/PackageFixtureRun.cs', 'tests/Hexalith.Projects.Integration.Tests/PackageReadFixture.cs'):
    inputs[relative] = hashlib.sha256((root / relative).read_bytes()).hexdigest()
(results / 'full-fixture-inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
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
run(['dotnet', 'build', 'tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj', *flags], 'full-fixture-build.log')
run(['dotnet', 'tests/Hexalith.Projects.Integration.Tests/bin/Release/net11.0/Hexalith.Projects.Integration.Tests.dll',
     *[value for name in ('PackageFreshCutoverTests','PackageOwnerArtifactSelectionTests','PackageFixtureSafetyTests','PackageCredentialMatrixTests','PackageOwnerLoadContextTests')
       for value in ('-class', 'Hexalith.Projects.Integration.Tests.' + name)], '-noColor', '-failSkips'], 'full-fixture-tests.log')
with (results / 'full-fixture-fixture.log').open('w') as output:
    process = subprocess.Popen(['dotnet', 'tests/Hexalith.Projects.PackageFixtures/bin/Release/net11.0/Hexalith.Projects.PackageFixtures.dll', '--root', str(root)],
                               cwd=root, stdout=output, stderr=subprocess.STDOUT)
    try:
        while True:
            # Only retain known sanitized receipts; never copy credentials, raw state, RDBs or browser sessions.
            for directory in Path(os.environ['TMPDIR']).glob('projects-fixtures-*/native-evidence'):
                for name in ('fresh-cutover-inventory-observations.jsonl', 'writer-protocol-cutover.json', 'bootstrap-delivery.json', 'read-progress.log', 'seed-delivery-readiness.jsonl', 'folder-seed-readiness.jsonl', 'organization-seed-readiness.jsonl', 'seed-project-projection-outcomes.jsonl', 'projects-restart-process.json', 'query-denial-timing.jsonl'):
                    report = directory / name
                    if report.is_file():
                        try:
                            shutil.copyfile(report, results / ('full-fixture-' + directory.parent.name + '-' + name))
                        except FileNotFoundError:
                            pass
            if process.poll() is not None:
                break
            time.sleep(0.2)
    finally:
        if process.poll() is None:
            process.terminate()
        code = process.wait()
print('full-fixture-fixture.log EXIT', code, flush=True)
raise SystemExit(code)
