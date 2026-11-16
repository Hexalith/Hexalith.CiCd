from pathlib import Path
import hashlib
import json
import os
import subprocess

root=Path(os.environ['TMPDIR'])/'Hexalith.Projects'
results=Path('/home/administrator/projects/hexalith/cicd/_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116')
program=root/'tests/Hexalith.Projects.PackageFixtures/Program.cs'
original=program.read_bytes()
text=original.decode()
needle='Console.Error.WriteLine("Package fixture failure: " + failure.GetType().Name + ": " + failure.Message);'
assert text.count(needle)==1
text=text.replace(needle, needle+'\n        Console.Error.WriteLine(failure.StackTrace);')
program.write_text(text)
(results/'runtime-diagnostic-input.json').write_text(json.dumps({'scope':'Diagnostic stack reporting only; not exact-tree publication qualification', 'originalProgramSha256':hashlib.sha256(original).hexdigest(),'diagnosticProgramSha256':hashlib.sha256(program.read_bytes()).hexdigest()},indent=2)+'\n')
try:
    with (results/'runtime-diagnostic-build.log').open('w') as output:
        code=subprocess.run(['dotnet','build','tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj','--configuration','Release','--no-restore','--disable-build-servers','-noAutoResponse','-p:UseHexalithProjectReferences=false','-p:ShouldUnsetParentConfigurationAndPlatform=false','-p:RestoreConfigFile='+str(root/'references/Hexalith.Builds/NuGet.ci.Config'),'-p:EnableNETAnalyzers=true','-p:RunAnalyzers=true','-p:RunAnalyzersDuringBuild=true','-p:UseSharedCompilation=false','-warnaserror','-m:1','-nr:false'],cwd=root,stdout=output,stderr=subprocess.STDOUT).returncode
    print('DIAGNOSTIC BUILD EXIT',code,flush=True)
    if code: raise SystemExit(code)
    with (results/'runtime-diagnostic-fixture.log').open('w') as output:
        code=subprocess.run(['dotnet','tests/Hexalith.Projects.PackageFixtures/bin/Release/net11.0/Hexalith.Projects.PackageFixtures.dll','--root',str(root)],cwd=root,stdout=output,stderr=subprocess.STDOUT).returncode
    print('DIAGNOSTIC FIXTURE EXIT',code,flush=True)
finally:
    program.write_bytes(original)
raise SystemExit(code)
