"""Publish the exact authorized gate decision without changing active workspace state."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/cicd');e=Path(__file__).parent;base='b836159cea272e5211333296936106cf82833a27'
env=os.environ|{'GH_CONFIG_DIR':'/home/administrator/.config/gh-cicd-agent'}
def run(at,*args,check=True):
 r=subprocess.run(args,cwd=at,env=env,capture_output=True)
 if check and r.returncode:raise RuntimeError(' '.join(args[:3])+': '+r.stderr.decode(errors='replace'))
 return r
scratch=Path(os.environ['TMPDIR']);tools_source=scratch/'builds';tools_source.mkdir()
builds=root/'references/Hexalith.Builds';tag=(root/'builds-version').read_text().strip();tool_sha=run(root,'git','-C',str(builds),'rev-parse',tag+'^{commit}').stdout.decode().strip()
archive=subprocess.Popen(['git','-C',str(builds),'archive',tool_sha,'Github/lib','Github/guard'],stdout=subprocess.PIPE)
subprocess.run(['tar','-x','-C',str(tools_source)],stdin=archive.stdout,check=True);archive.stdout.close();assert archive.wait()==0
sys.path.insert(0,str(tools_source/'Github/lib'));from guard_tools import Tools
lintdir=scratch/'commitlint';lintdir.mkdir();tools=Tools(lintdir);run(lintdir,'git','init','--quiet')
message='build(cicd): authorize reviewed Projects G-6 delivery\n';message_file=scratch/'commit-message';message_file.write_text(message)
validation=subprocess.run(['node',str(lintdir/'node_modules/@commitlint/cli/cli.js'),'--config',str(tools_source/'Github/guard/commitlint.config.mjs'),'--color=false','--edit',str(message_file)],cwd=lintdir,env=tools.environment,capture_output=True)
(e/'commitlint.log').write_bytes(validation.stdout+validation.stderr);assert validation.returncode==0
(e/'commitlint.json').write_text(json.dumps({'message':message,'exit':validation.returncode,'tool_source':tool_sha,'tag':tag},indent=2)+'\n')
paths=['docs/proposals/projects-g6-catalog.json','tools/tests/test_deliver_g6_catalog.py','docs/projects-g6-catalog-acquisition.md','_bmad-output/implementation-artifacts/spec-projects-g6-narrow-delivery.md'];work=scratch/'owner'
run(root,'git','clone','--quiet','--no-hardlinks','--no-checkout',str(root),str(work));run(work,'git','remote','set-url','origin','https://github.com/Hexalith/Hexalith.CiCd.git');run(work,'git','fetch','--no-recurse-submodules','origin','main');run(work,'git','checkout','--quiet','--detach','origin/main')
parent=run(work,'git','rev-parse','HEAD').stdout.decode().strip();assert parent==base,'Owner main advanced: recheck exact source'
for p in paths:
 assert run(work,'git','show','HEAD:'+p).stdout==run(root,'git','show',base+':'+p).stdout,p
 dest=work/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((root/p).read_bytes())
old=json.loads(run(work,'git','show','HEAD:docs/proposals/projects-g6-catalog.json').stdout);new=json.loads((work/paths[0]).read_bytes());assert old.pop('pre_push_gate')=='pending-owner-decision';assert new.pop('pre_push_gate')=='reviewed-tree-owner-authorized';assert old==new
run(work,'git','add','--',*paths);run(work,'git','diff','--cached','--check');diff=run(work,'git','diff','--cached','--binary').stdout;(e/'authorization.diff').write_bytes(diff)
assert sorted(run(work,'git','diff','--cached','--name-only').stdout.decode().splitlines())==sorted(paths)
run(work,'git','commit','--file',str(message_file));commit=run(work,'git','rev-parse','HEAD').stdout.decode().strip();run(work,'git','fetch','--no-recurse-submodules','origin','main');assert run(work,'git','rev-parse','origin/main').stdout.decode().strip()==parent
result=run(work,'git','push','--porcelain','origin',commit+':refs/heads/main',check=False)
receipt={'parent':parent,'commit':commit,'message':message,'paths':paths,'sources':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},'push_exit':result.returncode,'push_stdout':result.stdout.decode(),'push_stderr':result.stderr.decode()};(e/'owner-publication.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if result.returncode:raise SystemExit(result.returncode)
dispatch=run(work,'gh','workflow','run','deliver.yml','--repo','Hexalith/Hexalith.CiCd','--ref','main','-f','delivery=projects-g6-catalog',check=False)
(e/'dispatch.json').write_text(json.dumps({'owner_source':commit,'command':['gh','workflow','run','deliver.yml','--repo','Hexalith/Hexalith.CiCd','--ref','main','-f','delivery=projects-g6-catalog'],'exit_code':dispatch.returncode,'stdout':dispatch.stdout.decode(),'stderr':dispatch.stderr.decode()},indent=2)+'\n')
print('owner narrow dispatch exit:',dispatch.returncode);print(dispatch.stdout.decode());print(dispatch.stderr.decode());raise SystemExit(dispatch.returncode)
