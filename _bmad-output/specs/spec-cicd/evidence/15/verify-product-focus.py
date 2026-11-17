"""Qualify current product changes in a private standalone snapshot; no pushes."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,xml.etree.ElementTree as ET
root=Path.cwd(); source=root/'references/Hexalith.McpCli'; scratch=Path(os.environ['TMPDIR'])/'module'
def run(args,cwd=scratch,env=None):
 print('Running:',*map(str,args),flush=True)
 subprocess.run(list(map(str,args)),cwd=cwd,env=env,check=True)
run(['git','clone','--shared','--quiet',source,scratch],cwd=root)
patch=subprocess.run(['git','diff','--binary','HEAD'],cwd=source,capture_output=True,check=True).stdout
subprocess.run(['git','apply','--binary','-'],cwd=scratch,input=patch,check=True)
for name in subprocess.run(['git','ls-files','--others','--exclude-standard'],cwd=source,capture_output=True,text=True,check=True).stdout.splitlines():
 src=source/name;target=scratch/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
builds_sha=subprocess.run(['git','rev-parse','HEAD:references/Hexalith.Builds'],cwd=source,capture_output=True,text=True,check=True).stdout.strip()
# Materialize the exact recorded import tree as a sibling archive. The
# module's nested references remain uninitialized.
builds=scratch.parent/'Hexalith.Builds'
builds.mkdir()
archive=subprocess.run(['git','archive',builds_sha],cwd=root/'references/Hexalith.Builds',capture_output=True,check=True).stdout
import io,tarfile
with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:bundle.extractall(builds,filter='data')
assert not (scratch/'references/Hexalith.Builds/.git').exists()
env=dict(os.environ,NUGET_PACKAGES=str(Path(os.environ['TMPDIR'])/'packages'),NUGET_HTTP_CACHE_PATH=str(Path(os.environ['TMPDIR'])/'http'),PYTHONDONTWRITEBYTECODE='1',DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
flags=['-p:UseHexalithProjectReferences=false','-p:NuGetAudit=true','-p:NuGetAuditMode=all','-p:NuGetAuditLevel=low','-warnaserror']
project='tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj'
# The full Core lane remains dependent on the genuinely published Projects contract.
# Qualify the independent Abstractions production/test graph without substituting it.
project='tests/Hexalith.McpCli.Abstractions.Tests/Hexalith.McpCli.Abstractions.Tests.csproj'
run(['dotnet','restore',project,*flags],env=env)
run(['dotnet','build',project,'--no-restore','--configuration','Release',*flags],env=env)
run(['dotnet','tests/Hexalith.McpCli.Abstractions.Tests/bin/Release/net11.0/Hexalith.McpCli.Abstractions.Tests.dll'],env=env)
packable=[]
for item in ET.parse(scratch/'Hexalith.McpCli.slnx').iter('Project'):
 path=item.attrib['Path']
 result=subprocess.run(['dotnet','msbuild',path,'-nologo','-p:Configuration=Release','-p:UseHexalithProjectReferences=false','-getProperty:IsPackable,PackageId'],cwd=scratch,env=env,capture_output=True,text=True,check=True)
 properties=json.loads(result.stdout)['Properties']
 if properties['IsPackable']=='true':packable.append(properties['PackageId'])
assert sorted(packable)==['Hexalith.McpCli','Hexalith.McpCli.Abstractions'],packable
print('Evaluated complete solution pack set:',packable,flush=True)
print('Input revision:',subprocess.run(['git','rev-parse','HEAD'],cwd=source,capture_output=True,text=True,check=True).stdout.strip(),'Builds:',builds_sha,'tracked patch SHA256:',hashlib.sha256(patch).hexdigest(),flush=True)
