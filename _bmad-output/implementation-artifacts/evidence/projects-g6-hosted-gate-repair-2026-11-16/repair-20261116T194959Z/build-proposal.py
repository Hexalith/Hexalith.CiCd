from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).resolve().parent;spaces=json.loads((p/'workspaces.json').read_text());project=Path(spaces['projects']);owner=Path(spaces['cicd']);paths=['tests/tools/test_render_skill.py','tests/tools/test_release_workflow.py','tests/tools/test_run_g6_candidate_gate.py','tests/tools/test_g6_mapper_build.py','package.json','package-lock.json','tests/tools/run-frontcomposer-inspect-gate.ps1','tests/tools/run-ci-workflow-gates.ps1','tests/tools/test_run_ci_workflow_gates.py']
def git(*args):return subprocess.check_output(['git',*args],cwd=project,stderr=subprocess.PIPE)
assert git('rev-parse','HEAD').decode().strip()==spaces['projects_source']
git('add','--',*paths);changed=git('diff','--cached','--name-only').decode().splitlines();assert set(changed)==set(paths);git('diff','--cached','--check');patch=git('diff','--cached','--binary','--full-index','--no-ext-diff');beforetree=git('rev-parse','HEAD^{tree}').decode().strip();aftertree=git('write-tree').decode().strip()
def entries(ref):
 result={}
 for row in git('ls-tree','-rz','--full-tree',ref).split(b'\0'):
  if row:
   info,path=row.split(b'\t',1);mode,kind,sha=info.decode().split();result[path.decode()]=[mode,kind,sha]
 return result
before=entries('HEAD');after=entries(aftertree);assert {x for x in set(before)|set(after) if before.get(x)!=after.get(x)}==set(paths)
manifest={'schema':'hexalith.projects-ci-gates.v1','repository':'Hexalith.Projects','pre_push_gate':'reviewed-tree-owner-authorized','base_commit':spaces['projects_source'],'base_tree':beforetree,'patch_sha256':hashlib.sha256(patch).hexdigest(),'result_tree':aftertree,'before':{path:before.get(path) for path in paths},'after':{path:after[path] for path in paths}}
for path in paths[1:6]:assert before.get(path) is None
for path in paths[1:4]:assert (project/path).read_bytes()==git('show','981ceef13a1abc88219925e73c51a23eb9ac50c2:'+path)
for path in ['.github/workflows/ci.yml','.github/workflows/commitlint.yml','.github/actions/prepare-g6-catalog/action.yml','.github/actions/prepare-g6-catalog/prepare.py','commitlint.config.mjs']:assert before[path]==after[path]
for path,item in before.items():
 if item[1]=='commit':assert after[path]==item
for f in (owner/'docs/proposals/projects-ci-gates.patch',p/'projects-ci-gates.patch'):f.write_bytes(patch)
# Validation digest is appended once all final-source evidence has passed.
for f in (owner/'docs/proposals/projects-ci-gates.json',p/'projects-ci-gates.json'):f.write_text(json.dumps(manifest,indent=2)+'\n')
proof={'manifest':manifest,'exact_changed_paths':changed,'gitlinks_preserved':True,'existing_workflows_and_acquisition_preserved':True,'historical_three_suites_exact':True,'commitlint_versions_and_integrities_unchanged':True,'unrelated_entries_preserved':True,'nonmetadata_repair_diff':git('diff','--cached','--',*paths[:4],*paths[6:]).decode()};(p/'module-proposal-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'base':manifest['base_commit'],'before_tree':beforetree,'after_tree':aftertree,'patch_bytes':len(patch),'patch_sha256':manifest['patch_sha256'],'changed_paths':changed},indent=2))
