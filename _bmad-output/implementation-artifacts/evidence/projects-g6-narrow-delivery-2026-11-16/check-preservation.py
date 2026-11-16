"""Read-only state comparison; distinguish concurrent user edits from task-owned source."""
import hashlib,json,os,subprocess
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/cicd');e=Path(__file__).parent
before=json.loads((e/'before.json').read_bytes());results={}
own={'tools/deliver_g6_catalog.py','docs/proposals/projects-g6-catalog.json','tools/tests/test_deliver_g6_catalog.py','tools/tests/test_deliver_g6_catalog.py.lock','.github/workflows/deliver.yml','docs/projects-g6-catalog-acquisition.md','tools/tests/test_delivery_workflow.py','_bmad-output/implementation-artifacts/spec-projects-g6-narrow-delivery.md'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,item in before.items():
 r=Path(name)
 def git(*args):return subprocess.check_output(['git','-C',name,*args],env=os.environ|{'GIT_OPTIONAL_LOCKS':'0'})
 index=Path(git('rev-parse','--path-format=absolute','--git-path','index').decode().strip())
 current=git('diff','--name-only','-z','HEAD').decode().split('\0')
 changed={p:{'before':item['tracked'][p],'now':sha(r/p) if (r/p).is_file() else None} for p in current if p in item['tracked'] and (r/p).is_file() and sha(r/p)!=item['tracked'][p] and not (r==root and p in own)}
 results[name]={'head_before':item['head'],'head_now':git('rev-parse','HEAD').decode().strip(),'index_preserved':sha(index)==item['index_sha256'],'staged_entries_preserved':hashlib.sha256(git('ls-files','--stage','-z')).hexdigest()==item['entries_sha256'],'gitlinks_preserved':[x for x in git('ls-tree','-r','HEAD').decode().splitlines() if x.startswith('160000')]==item['gitlinks'],'concurrent_working_file_changes':changed}
 if r.name=='folders':
  protected={p:h for p,h in item['tracked'].items() if p.endswith(('sprint-status.yaml','sprint-status.yml')) or (p.startswith('_bmad-output/implementation-artifacts/') and '1-17' in p and '/evidence/' not in p)}
  results[name]['story_tracking_preserved']=all((r/p).is_file() and sha(r/p)==h for p,h in protected.items());results[name]['protected_tracking_files']=len(protected)
 if r==root:
  unchanged=['tools/delivery_runtime.py','tools/deliver.py','.github/actions/prepare-g6-catalog/action.yml','.github/actions/prepare-g6-catalog/prepare.py','tools/tests/test_prepare_g6_catalog.py','docs/proposals/projects-g6-catalog.patch','builds-version']
  results[name]['protected_owner_sources']={p:sha(r/p)==item['tracked'][p] for p in unchanged}
(e/'preservation-final.json').write_text(json.dumps(results,indent=2)+'\n')
for name,result in results.items():
 assert result['index_preserved'] and result['staged_entries_preserved'] and result['gitlinks_preserved'],name
 assert result['head_before']==result['head_now'],name
 if 'story_tracking_preserved' in result:assert result['story_tracking_preserved']
 if 'protected_owner_sources' in result:assert all(result['protected_owner_sources'].values())
 print(name, 'HEAD/index/gitlinks preserved; concurrent file changes:',len(result['concurrent_working_file_changes']))
