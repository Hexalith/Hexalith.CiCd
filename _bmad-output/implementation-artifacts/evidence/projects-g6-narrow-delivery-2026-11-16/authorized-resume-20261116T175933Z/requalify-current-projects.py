"""Bind the unchanged owner correction to current reviewed Projects source."""
import hashlib,importlib.util,json,os,subprocess
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/cicd');e=Path(__file__).parent
spec=importlib.util.spec_from_file_location('proof_runtime',root/'tools/delivery_runtime.py');rt=importlib.util.module_from_spec(spec);spec.loader.exec_module(rt)
manifest=json.loads((root/'docs/proposals/projects-g6-catalog.json').read_bytes());old=manifest['base_commit'];expected='49f0a9e31482891fe8c1376d2ccdb1637f1f20dd';assert old=='981ceef13a1abc88219925e73c51a23eb9ac50c2'
transport=rt.Transport();git=rt.Git(Path(os.environ['TMPDIR'])/'projects.git',index=Path(os.environ['TMPDIR'])/'index');git.init();current=transport.module(git,'Hexalith.Projects');assert current==expected,'Projects advanced; inspect new source first'
git.run('fetch','--depth=1','--no-recurse-submodules','--no-tags',transport.remote('Hexalith.Projects'),old)
before=git.items(current);previous=git.items(old);paths=set(manifest['after'])
assert {p:v for p,v in before.items() if v[0]=='160000'}=={p:v for p,v in previous.items() if v[0]=='160000'}
assert before['.gitmodules']==previous['.gitmodules']
for path,entry in manifest['before'].items():assert before.get(path)==(tuple(entry) if entry else None),path
probe_path='Directory.Packages.props';probe_oid=before[probe_path][2]
def available(oid):
 r=subprocess.run(['git','-C',str(git.root),'cat-file','--batch-check=%(objectname) %(objecttype)'],input=(oid+'\n').encode(),env=git.env|{'GIT_NO_LAZY_FETCH':'1'},capture_output=True,check=True);return r.stdout.decode().strip()
probe_before=available(probe_oid);patch=(root/'docs/proposals/projects-g6-catalog.patch').read_bytes();assert hashlib.sha256(patch).hexdigest()==manifest['patch_sha256']
git.run('read-tree',current);git.run('apply','--cached','--whitespace=nowarn',data=patch);tree=git.resolve(git.run('write-tree','--missing-ok').decode().strip());after=git.items(tree)
for path,entry in manifest['after'].items():assert after[path]==tuple(entry),path
changed=sorted(p for p in before.keys()|after.keys() if before.get(p)!=after.get(p));assert set(changed)==paths
assert {p:v for p,v in before.items() if p not in paths}=={p:v for p,v in after.items() if p not in paths}
for path in paths- {'.github/workflows/ci.yml'}:assert git.blob(tree,path)==(root/path).read_bytes()
probe_after=available(probe_oid)
if probe_before.endswith(' missing'):assert probe_after==probe_before,'Unrelated promised blob was fetched'
assert git.run('ls-remote','--heads',transport.remote('Hexalith.Projects'),'refs/heads/main').decode().split()[0]==current
receipt={'old_base':old,'reviewed_base':current,'base_tree':git.resolve(current+'^{tree}'),'result_tree':tree,'proposal_sha256':manifest['patch_sha256'],'changed_paths':changed,'before':{p:before.get(p) for p in sorted(paths)},'after':{p:after[p] for p in sorted(paths)},'all_other_entries_preserved':True,'all_gitlinks_preserved':True,'gitmodules_preserved':True,'builds_gitlink':before['references/Hexalith.Builds'][2],'platform_gitlink':before['references/Hexalith.Platform'][2],'promised_blob_probe':{'path':probe_path,'before':probe_before,'after':probe_after},'concurrent_product_changes':[p for p in sorted(previous.keys()|before.keys()) if previous.get(p)!=before.get(p)]}
(e/'projects-source-requalification.json').write_text(json.dumps(receipt,indent=2)+'\n')
manifest.update(base_commit=current,base_tree=receipt['base_tree'],result_tree=tree)
(root/'docs/proposals/projects-g6-catalog.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(receipt,indent=2))
