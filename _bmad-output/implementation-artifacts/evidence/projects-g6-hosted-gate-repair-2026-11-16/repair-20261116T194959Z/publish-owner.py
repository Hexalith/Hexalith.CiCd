from pathlib import Path
import json,hashlib,os,subprocess
p=Path(__file__).resolve().parent;spaces=json.loads((p/'workspaces.json').read_text());work=Path(spaces['cicd']);root=Path('/home/administrator/projects/hexalith/cicd');env=dict(os.environ,GH_CONFIG_DIR='/home/administrator/.config/gh-cicd-agent');paths=['tools/deliver_g6_catalog.py','tools/tests/test_deliver_projects_ci_gates.py','tools/tests/test_deliver_projects_ci_gates.py.lock','.github/workflows/deliver-projects-ci-gates.yml','docs/proposals/projects-ci-gates.json','docs/proposals/projects-ci-gates.patch','docs/proposals/projects-ci-gates-validation.json','docs/projects-ci-gates-repair.md'];spec='_bmad-output/implementation-artifacts/spec-projects-g6-hosted-gate-repair.md';(work/spec).write_bytes((root/spec).read_bytes());paths.append(spec)
def run(*args,check=True):
 r=subprocess.run(args,cwd=work,env=env,text=True,capture_output=True,timeout=180)
 if check and r.returncode:raise RuntimeError(' '.join(args[:3])+': '+r.stderr)
 return r
lint=json.loads((p/'owner-commitlint.json').read_text());assert lint['exit']==0;message=lint['message'];message_file=p/'owner-commit-message.txt';message_file.write_text(message)
run('git','fetch','--no-tags','--no-recurse-submodules','origin','main');parent=run('git','rev-parse','HEAD').stdout.strip();assert parent==spaces['cicd_source'];assert run('git','rev-parse','origin/main').stdout.strip()==parent,'Owner main advanced; inspect overlap before publishing'
module_main=json.loads(run('gh','api','repos/Hexalith/Hexalith.Projects/git/ref/heads/main').stdout)['object']['sha'];manifest=json.loads((work/'docs/proposals/projects-ci-gates.json').read_text());assert module_main==manifest['base_commit'],'Projects advanced before source publication'
run('git','add','--',*paths);run('git','diff','--cached','--check');changed=run('git','diff','--cached','--name-only').stdout.splitlines();assert set(changed)==set(paths)
snapshot={path:{'text':(work/path).read_text(),'sha256':hashlib.sha256((work/path).read_bytes()).hexdigest()} for path in paths};(p/'owner-publication-snapshot.json').write_text(json.dumps({'parent':parent,'files':snapshot},indent=2)+'\n')
run('git','commit','--file',str(message_file));commit=run('git','rev-parse','HEAD').stdout.strip();bundle=p/'owner-source.bundle';run('git','bundle','create',str(bundle),parent+'..HEAD');run('git','bundle','verify',str(bundle));push=run('git','push','--porcelain','origin',commit+':refs/heads/main',check=False);receipt={'parent':parent,'commit':commit,'message':message,'paths':changed,'commitlint_exit':0,'push_exit':push.returncode,'stdout':push.stdout,'stderr':push.stderr,'bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'bundle_bytes':bundle.stat().st_size};(p/'owner-publication.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2),flush=True);assert push.returncode==0,'Owner source push rejected; no credential fallback'
# Import only task commit objects. Shared HEAD, branch and index are untouched.
r=subprocess.run(['git','fetch','--no-write-fetch-head','--no-tags','--no-recurse-submodules',str(bundle),'HEAD'],cwd=root,env=env,capture_output=True,text=True,timeout=120);assert r.returncode==0,r.stderr
reflected=[];concurrent=[]
for path,item in snapshot.items():
 if path==spec:continue
 f=root/path;previous=run('git','show',parent+':'+path,check=False)
 if not f.exists() or f.read_bytes()==item['text'].encode() or (previous.returncode==0 and f.read_bytes()==previous.stdout.encode()):f.parent.mkdir(parents=True,exist_ok=True);f.write_text(item['text']);reflected.append(path)
 else:concurrent.append(path)
(p/'owner-workspace-reflection.json').write_text(json.dumps({'reflected_task_paths':reflected,'concurrent_paths_preserved':concurrent,'branch_or_index_writes':False},indent=2)+'\n')
