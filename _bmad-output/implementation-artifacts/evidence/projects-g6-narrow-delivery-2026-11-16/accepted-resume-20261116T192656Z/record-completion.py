"""Record a compact local handoff without changing shared branches or indices."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/cicd');p=Path(__file__).resolve().parent;snapshot=json.loads((p/'completion-source-snapshot.json').read_text());scratch=Path(os.environ['TMPDIR']);env=dict(os.environ,GH_CONFIG_DIR='/home/administrator/.config/gh-cicd-agent',GIT_OPTIONAL_LOCKS='0')
def run(at,*args,check=True):
 r=subprocess.run(args,cwd=at,env=env,capture_output=True,timeout=300)
 if check and r.returncode:raise RuntimeError(' '.join(args[:3])+': '+r.stderr.decode(errors='replace'))
 return r
before={}
for name in ('cicd','projects','folders'):
 repo=root.parent/name;idx=Path(run(repo,'git','rev-parse','--path-format=absolute','--git-path','index').stdout.decode().strip());before[name]={'head':run(repo,'git','rev-parse','HEAD').stdout.decode().strip(),'index_sha256':hashlib.sha256(idx.read_bytes()).hexdigest()}
(p/'completion-workspace-before.json').write_text(json.dumps(before,indent=2)+'\n')
# Export only the already qualified immutable released commit validator.
tool_sha=json.loads((p.parent/'commitlint.json').read_text())['tool_source'];export=scratch/'released-tools';export.mkdir()
archive=subprocess.Popen(['git','-C',str(root/'references/Hexalith.Builds'),'archive',tool_sha,'Github/lib','Github/guard'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
extract=subprocess.run(['tar','-x','-C',str(export)],stdin=archive.stdout,capture_output=True);archive.stdout.close();archive.wait();assert extract.returncode==0 and archive.returncode==0
sys.path.insert(0,str(export/'Github/lib'));from guard_tools import Tools
lintdir=scratch/'commitlint';lintdir.mkdir();tools=Tools(lintdir);run(lintdir,'git','init','--quiet')
message='docs(cicd): retain Projects catalog delivery outcome\n';message_file=scratch/'commit-message';message_file.write_text(message)
lint=subprocess.run(['node',str(lintdir/'node_modules/@commitlint/cli/cli.js'),'--config',str(export/'Github/guard/commitlint.config.mjs'),'--color=false','--edit',str(message_file)],cwd=lintdir,env=tools.environment,capture_output=True,timeout=120);(p/'completion-commitlint.log').write_bytes(lint.stdout+lint.stderr);assert lint.returncode==0
work=scratch/'owner';run(root,'git','clone','--quiet','--no-hardlinks','--no-checkout',str(root),str(work));run(work,'git','remote','set-url','origin','https://github.com/Hexalith/Hexalith.CiCd.git');run(work,'git','fetch','--no-tags','--no-recurse-submodules','origin',snapshot['parent']);assert run(work,'git','rev-parse','FETCH_HEAD').stdout.decode().strip()==snapshot['parent'],'Exact local handoff base unavailable';run(work,'git','-c','submodule.recurse=false','checkout','--quiet','--detach',snapshot['parent'])
for path,digest in snapshot['observed_shared_docs'].items():assert hashlib.sha256(run(work,'git','show','HEAD:'+path).stdout).hexdigest()==digest,'Published/shared documentation differs: '+path
for path,item in snapshot['files'].items():
 data=item['text'].encode();assert hashlib.sha256(data).hexdigest()==item['sha256'];f=work/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
paths=list(snapshot['files']);run(work,'git','add','--',*paths);run(work,'git','diff','--cached','--check');changed=run(work,'git','diff','--cached','--name-only').stdout.decode().splitlines();assert set(changed)==set(paths)
run(work,'git','commit','--file',str(message_file));commit=run(work,'git','rev-parse','HEAD').stdout.decode().strip()
bundle=p/'completion.bundle';run(work,'git','bundle','create',str(bundle),snapshot['parent']+'..HEAD');run(work,'git','bundle','verify',str(bundle))
# Import objects only: no branch/ref, FETCH_HEAD, shared index or checkout change.
run(root,'git','fetch','--no-write-fetch-head','--no-tags',str(bundle),'HEAD')
for path,digest in snapshot['observed_shared_docs'].items():
 f=root/path;assert hashlib.sha256(f.read_bytes()).hexdigest()==digest,'Concurrent shared documentation change: '+path
for path in snapshot['observed_shared_docs']:(root/path).write_text(snapshot['files'][path]['text'])
after={}
for name,previous in before.items():
 repo=root.parent/name;idx=Path(run(repo,'git','rev-parse','--path-format=absolute','--git-path','index').stdout.decode().strip());after[name]={'head':run(repo,'git','rev-parse','HEAD').stdout.decode().strip(),'index_sha256':hashlib.sha256(idx.read_bytes()).hexdigest()};assert after[name]==previous,'Concurrent shared Git state change: '+name
tracking=json.loads((p/'protected-tracking-before.json').read_text());assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in tracking.items())
receipt={'commit':commit,'parent':snapshot['parent'],'message':message,'paths':changed,'commitlint_source':tool_sha,'commitlint_exit':0,'published':False,'bundle':str(bundle),'bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'bundle_bytes':bundle.stat().st_size,'shared_heads_and_indices_preserved':True,'protected_tracking_preserved':True,'bulk_evidence_excluded':True}
(p/'completion-commit.json').write_text(json.dumps(receipt,indent=2)+'\n');(p/'completion-preservation.json').write_text(json.dumps({'before':before,'after':after,'preserved':True,'story_tracking_unchanged':True},indent=2)+'\n');print(json.dumps(receipt,indent=2))
