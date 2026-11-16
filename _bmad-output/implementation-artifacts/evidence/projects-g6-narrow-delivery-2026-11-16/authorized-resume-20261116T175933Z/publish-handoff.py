"""Commit only the reviewed owner handoff; preserve the active workspace index/branch."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/cicd');e=Path(__file__).parent;snapshot=json.loads((e/'handoff-source-snapshot.json').read_bytes());scratch=Path(os.environ['TMPDIR']);env=os.environ|{'GH_CONFIG_DIR':'/home/administrator/.config/gh-cicd-agent','GIT_OPTIONAL_LOCKS':'0'}
def run(at,*args,check=True):
 r=subprocess.run(args,cwd=at,env=env,capture_output=True)
 if check and r.returncode:raise RuntimeError(' '.join(args[:3])+': '+r.stderr.decode(errors='replace'))
 return r
before={}
for name in ('cicd','projects','folders'):
 r=root.parent/name;idx=Path(run(r,'git','rev-parse','--path-format=absolute','--git-path','index').stdout.decode().strip());before[name]={'head':run(r,'git','rev-parse','HEAD').stdout.decode().strip(),'index_sha256':hashlib.sha256(idx.read_bytes()).hexdigest()}
(e/'handoff-before.json').write_text(json.dumps(before,indent=2)+'\n')
# Use the existing immutable released commitlint policy, never module-owned config.
prior=json.loads((e.parent/'commitlint.json').read_bytes());tool_sha=prior['tool_source'];builds=root/'references/Hexalith.Builds';export=scratch/'tools-source';export.mkdir()
archive=subprocess.Popen(['git','-C',str(builds),'archive',tool_sha,'Github/lib','Github/guard'],stdout=subprocess.PIPE);subprocess.run(['tar','-x','-C',str(export)],stdin=archive.stdout,check=True);archive.stdout.close();assert archive.wait()==0
sys.path.insert(0,str(export/'Github/lib'));from guard_tools import Tools
lintdir=scratch/'commitlint';lintdir.mkdir();tools=Tools(lintdir);run(lintdir,'git','init','--quiet');message='docs(cicd): record Projects G-6 delivery qualification\n';message_file=scratch/'commit-message';message_file.write_text(message)
validation=subprocess.run(['node',str(lintdir/'node_modules/@commitlint/cli/cli.js'),'--config',str(export/'Github/guard/commitlint.config.mjs'),'--color=false','--edit',str(message_file)],cwd=lintdir,env=tools.environment,capture_output=True);(e/'handoff-commitlint.log').write_bytes(validation.stdout+validation.stderr);assert validation.returncode==0
work=scratch/'owner';run(root,'git','clone','--quiet','--no-hardlinks','--no-checkout',str(root),str(work));run(work,'git','remote','set-url','origin','https://github.com/Hexalith/Hexalith.CiCd.git');run(work,'git','fetch','--no-recurse-submodules','origin','main');run(work,'git','-c','submodule.recurse=false','checkout','--quiet','--detach','origin/main');parent=run(work,'git','rev-parse','HEAD').stdout.decode().strip()
for p,h in snapshot['observed_shared_docs'].items():assert hashlib.sha256(run(work,'git','show','HEAD:'+p).stdout).hexdigest()==h,'Concurrent published documentation edit: '+p
for p,item in snapshot['files'].items():
 data=item['text'].encode();assert hashlib.sha256(data).hexdigest()==item['sha256'];f=work/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
paths=list(snapshot['files']);run(work,'git','add','--',*paths);run(work,'git','diff','--cached','--check');changed=run(work,'git','diff','--cached','--name-only').stdout.decode().splitlines();assert set(changed)<=set(paths) and changed;run(work,'git','commit','--file',str(message_file));commit=run(work,'git','rev-parse','HEAD').stdout.decode().strip();run(work,'git','fetch','--no-recurse-submodules','origin','main');assert run(work,'git','rev-parse','origin/main').stdout.decode().strip()==parent,'Owner main advanced before handoff push'
push=run(work,'git','push','--porcelain','origin',commit+':refs/heads/main',check=False);receipt={'parent':parent,'commit':commit,'message':message,'paths':changed,'push_exit':push.returncode,'stdout':push.stdout.decode(),'stderr':push.stderr.decode(),'commitlint_exit':validation.returncode,'commitlint_source':tool_sha};(e/'handoff-publication.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if push.returncode:raise SystemExit(push.returncode)
# Reflect only our three documentation files when nobody changed them since capture.
for p,h in snapshot['observed_shared_docs'].items():
 f=root/p
 if hashlib.sha256(f.read_bytes()).hexdigest()==h:f.write_text(snapshot['files'][p]['text'])
after={}
for name,previous in before.items():
 r=root.parent/name;idx=Path(run(r,'git','rev-parse','--path-format=absolute','--git-path','index').stdout.decode().strip());after[name]={'head':run(r,'git','rev-parse','HEAD').stdout.decode().strip(),'index_sha256':hashlib.sha256(idx.read_bytes()).hexdigest()};assert after[name]==previous,'Concurrent state change while publishing: '+name
(e/'handoff-workspace-preservation.json').write_text(json.dumps({'before':before,'after':after,'preserved':True},indent=2)+'\n')
