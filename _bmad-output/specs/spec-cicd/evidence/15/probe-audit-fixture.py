import os,subprocess,json
from pathlib import Path
p=Path(os.environ['TMPDIR']);d=p/'fixture';d.mkdir()
(d/'global.json').write_text('{"sdk":{"version":"11.0.100","rollForward":"latestPatch"}}')
(d/'audit.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net11.0</TargetFramework><NuGetAudit>true</NuGetAudit><NuGetAuditMode>all</NuGetAuditMode><NuGetAuditLevel>low</NuGetAuditLevel><RestoreEnablePackagePruning>false</RestoreEnablePackagePruning><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup><ItemGroup><PackageReference Include="Newtonsoft.Json" Version="[13.0.4]" /></ItemGroup></Project>''')
(d/'NuGet.Config').write_text('''<configuration><packageSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources><auditSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></auditSources></configuration>''')
e=dict(os.environ,NUGET_PACKAGES=str(p/'packages'),NUGET_HTTP_CACHE_PATH=str(p/'http'))
subprocess.run(['dotnet','restore','audit.csproj','--configfile','NuGet.Config','--verbosity','normal','--force','-warnaserror'],cwd=d,env=e,check=True)
for f in sorted((p/'http').rglob('*')):
 if f.is_file():
  print('CACHE:',f.relative_to(p/'http'),f.stat().st_size)
  if 'vuln' in f.name:print(f.read_text()[:700])
print(json.dumps(json.load(open(d/'obj/project.assets.json'))['project']['restore'],indent=2))
