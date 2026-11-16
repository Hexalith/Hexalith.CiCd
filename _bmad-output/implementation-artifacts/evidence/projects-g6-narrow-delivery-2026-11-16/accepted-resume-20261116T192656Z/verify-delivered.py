"""Independently verify the hosted owner receipt against complete GitHub trees."""
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,os,subprocess
p=Path(__file__).resolve().parent
owner=json.loads((p/'source-preflight.json').read_text())
receipt=json.loads((p/'Hexalith.CiCd-43939511545-projects-g6-delivery.json').read_text())
assert receipt['owner_source']==owner['owner_source']
assert receipt['status'] in ('delivered','unchanged') and receipt['failed_operation'] is None
assert receipt['delivered_tree']==owner['result_tree']
sha=receipt['delivered_sha'];assert len(sha)==40
env=dict(os.environ,GH_CONFIG_DIR='/home/administrator/.config/gh-cicd-agent')
def api(path):return json.loads(subprocess.check_output(['gh','api',path],env=env,stderr=subprocess.PIPE,timeout=60))
repo='repos/Hexalith/Hexalith.Projects/'
commit=api(repo+'git/commits/'+sha)
assert commit['sha']==sha and [v['sha'] for v in commit['parents']]==[owner['projects_source']]
assert commit['tree']['sha']==owner['result_tree']
(p/'delivered-commit.json').write_text(json.dumps(commit,indent=2)+'\n')
trees={}
for label,tree in [('before',owner['input_tree']),('after',owner['result_tree'])]:
 data=api(repo+'git/trees/'+tree+'?recursive=1')
 assert data['sha']==tree and data['truncated'] is False
 (p/('projects-tree-'+label+'.json')).write_text(json.dumps(data,indent=2)+'\n')
 trees[label]={x['path']:[x['mode'],x['type'],x['sha']] for x in data['tree'] if x['type']!='tree'}
manifest_path=Path('/home/administrator/projects/hexalith/cicd/docs/proposals/projects-g6-catalog.json')
manifest_bytes=manifest_path.read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest()==owner['verified_files']['docs/proposals/projects-g6-catalog.json']['sha256']
manifest=json.loads(manifest_bytes)
changed={path:{'before':trees['before'].get(path),'after':trees['after'].get(path)} for path in sorted(set(trees['before'])|set(trees['after'])) if trees['before'].get(path)!=trees['after'].get(path)}
assert set(changed)==set(manifest['after'])
for path,values in changed.items():
 assert values['before']==manifest['before'][path] and values['after']==manifest['after'][path]
 actual=api(repo+'contents/'+path+'?ref='+sha)
 assert actual['type']=='file' and actual['sha']==values['after'][2]
 data=base64.b64decode(actual['content'])
 out=p/'delivered-source'/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
 if path.startswith('.github/actions/'):
  assert hashlib.sha256(data).hexdigest()==owner['verified_files'][path]['sha256']
workflow=(p/'delivered-source/.github/workflows/ci.yml').read_text()
assert workflow.index('uses: ./.github/actions/prepare-g6-catalog')<workflow.index('prepare-build')
before_pins={k:v for k,v in trees['before'].items() if v[1]=='commit'}
after_pins={k:v for k,v in trees['after'].items() if v[1]=='commit'}
assert before_pins==after_pins
current=api(repo+'git/ref/heads/main')['object']['sha']
assert current==sha,'Projects main advanced after delivery; inspect before claiming current-source acceptance'
proof={'verified_at':datetime.now(timezone.utc).isoformat(),'owner_source':owner['owner_source'],'delivered_sha':sha,'single_parent':owner['projects_source'],'input_tree':owner['input_tree'],'result_tree':owner['result_tree'],'changed':changed,'unchanged_entries':len(trees['before'])-1,'gitlinks_preserved':True,'gitlinks':before_pins,'other_workflows_and_gates_unchanged':True,'acquisition_payload_unchanged':True,'invocation_before_prepare_build':True,'current_main':current,'scope':'Read-only exact-source delivery proof; no module execution or runtime acceptance.'}
(p/'delivered-source-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({k:proof[k] for k in ('delivered_sha','single_parent','result_tree','unchanged_entries','gitlinks_preserved','invocation_before_prepare_build','current_main')},indent=2))
