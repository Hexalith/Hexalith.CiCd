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
project='tests/Hexalith.McpCli.AppHost/Hexalith.McpCli.AppHost.csproj'
run(['dotnet','restore',project,*flags],env=env)
run(['dotnet','build',project,'--no-restore','--configuration','Release',*flags],env=env)
print('AppHost source/API compile qualification passed; no lifecycle or live acceptance claimed.',flush=True)
