"""Publish a task-only CiCd commit from current remote main without touching workspace indices."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true');args=parser.parse_args()
root=Path('/home/administrator/projects/hexalith/cicd');out=Path(__file__).parent
paths=['tools/deliver_g6_catalog.py','docs/proposals/projects-g6-catalog.json','tools/tests/test_deliver_g6_catalog.py','tools/tests/test_deliver_g6_catalog.py.lock','tools/tests/test_delivery_workflow.py','.github/workflows/deliver.yml','docs/projects-g6-catalog-acquisition.md','_bmad-output/implementation-artifacts/spec-projects-g6-narrow-delivery.md']
base='eba7514e02904c741f6a0a80930d85eb358d385c';work=Path(os.environ['TMPDIR'])/'owner'
env=os.environ.copy();env['GH_CONFIG_DIR']='/home/administrator/.config/gh-cicd-agent'
def run(cwd,*cmd,check=True):
 r=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True)
 if check and r.returncode:raise RuntimeError(' '.join(cmd[:3])+': '+r.stderr.decode(errors='replace'))
 return r
run(root,'git','clone','--quiet','--no-hardlinks','--no-checkout',str(root),str(work))
run(work,'git','remote','set-url','origin','https://github.com/Hexalith/Hexalith.CiCd.git');run(work,'git','fetch','--no-recurse-submodules','origin','main');run(work,'git','checkout','--quiet','--detach','origin/main')
parent=run(work,'git','rev-parse','HEAD').stdout.decode().strip()
for p in paths:
 previous=run(root,'git','show',base+':'+p,check=False)
 current=run(work,'git','show','HEAD:'+p,check=False)
 assert previous.returncode==current.returncode and previous.stdout==current.stdout,'Concurrent source change requires reconciliation: '+p
 source=root/p;assert source.is_file() and not source.is_symlink(),p
 dest=work/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
run(work,'git','add','--',*paths)
changed=run(work,'git','diff','--cached','--name-only').stdout.decode().splitlines();assert sorted(changed)==sorted(paths),changed
message='build(cicd): add exact-source Projects G-6 delivery\n'
validated=json.loads((out/'commitlint.json').read_bytes())['validated_messages'];assert message.strip() in validated
# Conventional Commit was checked with the pinned Builds commitlint policy.
msg=Path(os.environ['TMPDIR'])/'owner-commit-message';msg.write_text(message)
run(work,'git','commit','--file',str(msg))
commit=run(work,'git','rev-parse','HEAD').stdout.decode().strip()
receipt={'parent':parent,'commit':commit,'message':message,'paths':changed,'sources':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},'push_requested':args.publish}
if args.publish:
 run(work,'git','fetch','--no-recurse-submodules','origin','main')
 assert run(work,'git','rev-parse','origin/main').stdout.decode().strip()==parent,'Remote main advanced before push; requalify on fresh source'
 result=run(work,'git','push','--porcelain','origin',commit+':refs/heads/main',check=False)
 receipt.update(push_exit=result.returncode,push_stdout=result.stdout.decode(),push_stderr=result.stderr.decode())
 (out/'owner-publication.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));raise SystemExit(result.returncode)
(out/'owner-candidate.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
