"""Qualify retained owner proposal in a disposable committed Projects copy."""
import hashlib,json,os,subprocess
from pathlib import Path
owner=Path('/home/administrator/projects/hexalith/cicd')
projects=owner.parent/'projects'
evidence=owner/'_bmad-output/implementation-artifacts/evidence/projects-g6-narrow-delivery-2026-11-16'
root=Path(os.environ['TMPDIR'])/'projects'; root.mkdir()
env=os.environ.copy();env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_AUTHOR_NAME='Qualification',GIT_AUTHOR_EMAIL='qualification@example.invalid',GIT_COMMITTER_NAME='Qualification',GIT_COMMITTER_EMAIL='qualification@example.invalid',PYTHONDONTWRITEBYTECODE='1')
def git(at,*args,data=None):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null','-c','submodule.recurse=false','-C',str(at),*args],input=data,env=env,stderr=subprocess.PIPE)
base=git(projects,'rev-parse','refs/remotes/origin/main').decode().strip()
git(root,'init','--quiet');git(root,'fetch','--quiet','--no-tags','--no-recurse-submodules',str(projects),base);git(root,'checkout','--quiet','--detach',base)
patch=(owner/'docs/proposals/projects-g6-catalog.patch').read_bytes()
git(root,'apply','--check','--cached','-',data=patch);git(root,'apply','--cached','-',data=patch)
tree=git(root,'write-tree').decode().strip()
changes=git(root,'diff','--cached','--name-only',base).decode().splitlines()
assert sorted(changes)==sorted(['.github/workflows/ci.yml','.github/actions/prepare-g6-catalog/action.yml','.github/actions/prepare-g6-catalog/prepare.py'])
for p in changes:
 if p.startswith('.github/actions'):
  assert git(root,'show',':'+p)==(owner/p).read_bytes()
commit=git(root,'commit-tree',tree,'-p',base,data=b'build(cicd): qualify reviewed Projects G-6 catalog acquisition\n').decode().strip()
git(root,'checkout','--quiet','--detach',commit)
git(root,'checkout-index','--all','--force')
git(root,'remote','add','origin','https://github.com/Hexalith/Hexalith.Projects.git');git(root,'update-ref','refs/remotes/origin/main',base)
pin=git(root,'rev-parse','HEAD:references/Hexalith.Builds').decode().strip();builds=root/'references/Hexalith.Builds'
git(root,'clone','--quiet','--no-checkout','--no-hardlinks',str(projects/'references/Hexalith.Builds'),str(builds));git(builds,'checkout','--quiet','--detach',pin)
result=subprocess.run(['python3','references/Hexalith.Builds/check.py'],cwd=root,env=env,capture_output=True)
(evidence/'pinned-check.stdout.log').write_bytes(result.stdout);(evidence/'pinned-check.stderr.log').write_bytes(result.stderr)
receipt={'base':base,'base_tree':git(root,'rev-parse',base+'^{tree}').decode().strip(),'result_tree':tree,'qualification_commit':commit,'proposal_sha256':hashlib.sha256(patch).hexdigest(),'changes':changes,'builds_pin':pin,'checker_command':['python3','references/Hexalith.Builds/check.py'],'checker_exit':result.returncode,'before':{p:git(root,'ls-tree',base,'--',p).decode().strip() for p in changes},'after':{p:git(root,'ls-tree',commit,'--',p).decode().strip() for p in changes},'gitlinks_preserved':git(root,'ls-tree','-r',base).splitlines()==git(root,'ls-tree','-r',commit).splitlines()}
# Compare every immutable entry outside the closed patch, including gitlinks.
def entries(rev):return {r.split(b'\t',1)[1]:r for r in git(root,'ls-tree','-r','-z',rev).split(b'\0') if r and r.split(b'\t',1)[1].decode() not in changes}
assert entries(base)==entries(commit)
receipt['all_other_entries_preserved']=True
receipt['gitlinks_preserved']=all(v==entries(commit).get(k) for k,v in entries(base).items() if v.startswith(b'160000'))
(evidence/'proposal-qualification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2));print(result.stderr.decode())
