from pathlib import Path
import os
import shutil
import subprocess

root=Path(os.environ['TMPDIR'])/'Hexalith.Projects'
results=Path('/home/administrator/projects/hexalith/cicd/_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116')
source=root/'tests/Hexalith.Projects.PackageFixtures/PackageFixtureRun.cs'
original=source.read_bytes()
text=original.decode()
needle='''                if (actualOwners && scenario != "browser")'''
insertion='''                Console.WriteLine("[restart-diagnostic] before-bootstrap-only-restart");
                using (JsonDocument receipt = JsonDocument.Parse(await File.ReadAllBytesAsync(scratch.File("projects-process.json"), timeout.Token).ConfigureAwait(false)))
                {
                    using var child = System.Diagnostics.Process.GetProcessById(receipt.RootElement.GetProperty("pid").GetInt32());
                    using var parent = System.Diagnostics.Process.GetProcessById(receipt.RootElement.GetProperty("launcherPid").GetInt32());
                    Console.WriteLine("[restart-diagnostic] child=" + child.ProcessName + " parent=" + parent.ProcessName);
                    File.Copy(scratch.File("projects-process.json"), "RESULTS/projects-before-restart.json", overwrite: true);
                }
                var restarted = await application.ResourceCommands.ExecuteCommandAsync("projects", global::Aspire.Hosting.ApplicationModel.KnownResourceCommands.RestartCommand, timeout.Token).ConfigureAwait(false);
                Console.WriteLine("[restart-diagnostic] success=" + restarted.Success + " canceled=" + restarted.Canceled);
                if (!restarted.Success) throw new InvalidOperationException("Bootstrap-only owned resource restart refused.");
                await application.ResourceNotifications.WaitForResourceHealthyAsync("projects", timeout.Token).ConfigureAwait(false);
                File.Copy(scratch.File("projects-process.json"), "RESULTS/projects-after-restart.json", overwrite: true);
                return;
'''.replace('RESULTS',str(results))
assert text.count(needle)==1
text=text.replace(needle,insertion+needle,1)
# Return from this diagnostic intentionally makes subsequent product matrix unreachable; do not treat as acceptance.
text=text.replace('                return;\n                if (actualOwners', '                if (Environment.GetEnvironmentVariable("HEXALITH_RESTART_DIAGNOSTIC") == "1") return;\n                if (actualOwners',1)
source.write_text(text)
shutil.copyfile(Path('/home/administrator/projects/hexalith/cicd/references/Hexalith.Projects/tests/Hexalith.Projects.Integration.Tests/PackageReadFixture.cs'),root/'tests/Hexalith.Projects.Integration.Tests/PackageReadFixture.cs')
try:
    flags=['--configuration','Release','--no-restore','--disable-build-servers','-noAutoResponse','-p:UseHexalithProjectReferences=false','-p:ShouldUnsetParentConfigurationAndPlatform=false','-p:RestoreConfigFile='+str(root/'references/Hexalith.Builds/NuGet.ci.Config'),'-p:EnableNETAnalyzers=true','-p:RunAnalyzers=true','-p:RunAnalyzersDuringBuild=true','-p:UseSharedCompilation=false','-warnaserror','-m:1','-nr:false']
    with (results/'restart-diagnostic-build.log').open('w') as output:
        code=subprocess.run(['dotnet','build','tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj',*flags],cwd=root,stdout=output,stderr=subprocess.STDOUT).returncode
    print('RESTART DIAGNOSTIC BUILD EXIT',code,flush=True)
    if code: raise SystemExit(code)
    environment=os.environ.copy();environment['HEXALITH_RESTART_DIAGNOSTIC']='1'
    with (results/'restart-diagnostic-fixture.log').open('w') as output:
        code=subprocess.run(['dotnet','tests/Hexalith.Projects.PackageFixtures/bin/Release/net11.0/Hexalith.Projects.PackageFixtures.dll','--root',str(root)],cwd=root,env=environment,stdout=output,stderr=subprocess.STDOUT).returncode
    print('RESTART DIAGNOSTIC FIXTURE EXIT',code,flush=True)
finally:
    source.write_bytes(original)
raise SystemExit(code)
