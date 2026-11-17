from pathlib import Path
import os,urllib.request,tarfile,hashlib,subprocess,json
p=Path(os.environ['TMPDIR']); archive=p/'aspire.tar.gz'
with urllib.request.urlopen('https://github.com/microsoft/aspire/releases/download/v13.6.5/aspire-cli-linux-x64-13.6.5.tar.gz',timeout=120) as r:archive.write_bytes(r.read())
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='6e22bd4daaa62d09320638246e57bfaf56ed147a3a87cdd5eafec277726ca978'
with tarfile.open(archive) as z:z.extractall(p/'cli',filter='data')
binary=p/'cli/aspire';assert hashlib.sha256(binary.read_bytes()).hexdigest()=='7a9d1c1e264c645d7d78e2891ef53a865fa51d96adf2d827fed1e9cc3cb1e253'
env=dict(os.environ,ASPIRE_CLI_TELEMETRY_OPTOUT='1',DOTNET_CLI_TELEMETRY_OPTOUT='1')
for name in ('qualified','installed'):
 target=p/name
 environment=dict(env,ASPIRE_LAYOUT_PATH=str(target))
 result=subprocess.run(['timeout','--signal=TERM','--kill-after=30s','180',str(binary),'setup','--install-path',str(target),'--force','--non-interactive'],env=environment,text=True,capture_output=True)
 print(name,'exit',result.returncode,result.stdout,result.stderr,flush=True)
 assert result.returncode==0,'A failed installer is never accepted from extracted files alone'
import sys
sys.path.insert(0,str(Path.cwd()/'references/Hexalith.Builds/Github/lib'))
import ci_environment
ci_environment.verify_aspire_bundle(p/'qualified/bundle',p/'installed/bundle')
files={str(path.relative_to(p/'qualified/bundle')):hashlib.sha256(path.read_bytes()).hexdigest() for path in (p/'qualified/bundle').rglob('*') if path.is_file()}
print('Verified complete authenticated private bundle manifests:',len(files),'files.',flush=True)
print('DCP:',files['dcp/dcp'],'Dashboard:',files['dashboard/Aspire.Dashboard'],flush=True)
