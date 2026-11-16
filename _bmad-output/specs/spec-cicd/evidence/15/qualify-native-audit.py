"""Exercise the private audit against real public packages; no module build outputs touched."""
import importlib.util,os,sys,json,subprocess
from pathlib import Path
root=Path.cwd();scratch=Path(os.environ['TMPDIR']);module=root/'references/Hexalith.McpCli'
sys.path.insert(0,str(module/'tools/live-topology'))
import native_audit,ci
policy=json.loads((module/'global.json').read_text())['sdk']
for case,package,version in [('transitive-clean','Microsoft.Extensions.Logging','11.0.0'),('known-vulnerable','Newtonsoft.Json','9.0.1')]:
 folder=scratch/case;folder.mkdir()
 (folder/'global.json').write_text(json.dumps({'sdk':policy}))
 project=folder/'original.csproj'
 project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net11.0</TargetFramework><NuGetAudit>false</NuGetAudit><RestoreEnablePackagePruning>false</RestoreEnablePackagePruning></PropertyGroup><ItemGroup><PackageReference Include="'+package+'" Version="['+version+']"/></ItemGroup></Project>')
 config=folder/'NuGet.Config';config.write_text('<configuration><packageSources><clear/><add key="nuget" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
 env=dict(os.environ,NUGET_PACKAGES=str(folder/'original-packages'),NUGET_HTTP_CACHE_PATH=str(folder/'original-http'))
 subprocess.run(['dotnet','restore',str(project),'--configfile',str(config),'-p:NuGetAudit=false'],cwd=folder,env=env,check=True)
 output=folder/'bin/Release/net11.0/original.dll';output.parent.mkdir(parents=True);output.write_bytes(b'unchanged module output sentinel')
 original=native_audit.output_snapshot(project)
 try:
  receipt=native_audit.audit_project(project,folder/'private-audit',folder/'audit-command',policy,ci.bounded)
 except RuntimeError as error:
  if case!='known-vulnerable':raise
  message=(folder/'audit-command.stderr.txt').read_text()+(folder/'audit-command.stdout.txt').read_text()
  assert 'NU1903' in message,message
  print('Known vulnerable package rejected at low-and-higher warning-as-error policy:',error,flush=True)
 else:
  assert case=='transitive-clean','Known vulnerable package accepted'
  assert len(receipt['packages'])>1,'Transitive probe did not cover multiple packages'
  assert set(receipt['advisories']['pages'])=={'index','base','update'}
  print('Complete clean transitive graph audited:',list(receipt['packages']),flush=True)
  (root/'_bmad-output/specs/spec-cicd/evidence/15/native-audit-real-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 assert original==native_audit.output_snapshot(project)
 print(case,'original assets/build outputs unchanged',flush=True)
