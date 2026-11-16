from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import time

root=Path(os.environ['TMPDIR'])/'Hexalith.Projects'
source=Path('/home/administrator/projects/hexalith/cicd/references/Hexalith.Projects')
results=Path('/home/administrator/projects/hexalith/cicd/_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116/current-main')
updated={}
for name in ('PackageApplicationFactory.cs','PackageFixtureRun.cs'):
    relative='tests/Hexalith.Projects.PackageFixtures/'+name
    shutil.copyfile(source/relative,root/relative)
    updated[relative]=hashlib.sha256((root/relative).read_bytes()).hexdigest()
(results/'collector-update-inputs.json').write_text(json.dumps(updated,indent=2)+'\n')
flags=['--configuration','Release','--disable-build-servers','-noAutoResponse','-p:UseHexalithProjectReferences=false',
       '-p:ShouldUnsetParentConfigurationAndPlatform=false','-p:RestoreConfigFile='+str(root/'references/Hexalith.Builds/NuGet.ci.Config'),
       '-p:EnableNETAnalyzers=true','-p:RunAnalyzers=true','-p:RunAnalyzersDuringBuild=true','-p:UseSharedCompilation=false','-warnaserror','-m:1','-nr:false']
def run(command,name,cwd=root):
    with (results/name).open('w') as output:
        code=subprocess.run(command,cwd=cwd,stdout=output,stderr=subprocess.STDOUT).returncode
    print(name,'EXIT',code,flush=True)
    if code:raise SystemExit(code)
run(['dotnet','build','tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj',*flags],'integration-build.log')
run(['dotnet','tests/Hexalith.Projects.Integration.Tests/bin/Release/net11.0/Hexalith.Projects.Integration.Tests.dll',
     *[v for name in ('PackageFreshCutoverTests','PackageOwnerArtifactSelectionTests','PackageFixtureSafetyTests','PackageCredentialMatrixTests','PackageOwnerLoadContextTests','PackageOwnerMetadataTests')
       for v in ('-class','Hexalith.Projects.Integration.Tests.'+name)],'-noColor','-failSkips'],'focused-tests.log')
run(['npm','ci','--ignore-scripts'],'npm-setup.log',root/'tests/e2e')
run(['npm','audit','signatures'],'npm-signatures.log',root/'tests/e2e')
with (results/'package-fixture.log').open('w') as output:
    process=subprocess.Popen(['dotnet','tests/Hexalith.Projects.PackageFixtures/bin/Release/net11.0/Hexalith.Projects.PackageFixtures.dll','--root',str(root)],cwd=root,stdout=output,stderr=subprocess.STDOUT)
    try:
        while True:
            for directory in Path(os.environ['TMPDIR']).glob('projects-fixtures-*'):
                for parent,names in [(directory,('telemetry-receiver.json','projects-process.json')),
                     (directory/'native-evidence',('fresh-cutover-inventory-observations.jsonl','writer-protocol-cutover.json','bootstrap-delivery.json','read-progress.log','seed-delivery-readiness.jsonl','folder-seed-readiness.jsonl','projects-restart-process.json'))]:
                    for name in names:
                        report=parent/name
                        if report.is_file():
                            try:shutil.copyfile(report,results/(directory.name+'-'+name))
                            except FileNotFoundError:pass
            if process.poll() is not None:break
            time.sleep(0.2)
    finally:
        if process.poll() is None:process.terminate()
        code=process.wait()
print('package-fixture.log EXIT',code,flush=True)
raise SystemExit(code)
