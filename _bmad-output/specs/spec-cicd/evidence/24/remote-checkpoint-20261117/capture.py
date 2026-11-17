"""Capture stopped work as restorable archives, without publishing module refs."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,os,subprocess
DEST=Path("/home/administrator/projects/hexalith/cicd-story-24-checkpoint-20261117/_bmad-output/specs/spec-cicd/evidence/24/remote-checkpoint-20261117")
TMP=Path(os.environ["TMPDIR"])
ROOT=Path("/home/administrator/projects/hexalith/cicd-story-24")
def git(repo,*args,index=None,data=None):
    env=os.environ.copy()
    if index:env["GIT_INDEX_FILE"]=str(index)
    return subprocess.check_output(["git","-c","core.hooksPath=/dev/null","-c","gc.autoDetach=false","-c","maintenance.autoDetach=false","-C",str(repo),*args],env=env,input=data)
digest=lambda value:hashlib.sha256(value).hexdigest()
records=[]
for name,repo in [("cicd",ROOT),("builds",ROOT/"references/Hexalith.Builds"),("frontcomposer",ROOT/"references/Hexalith.FrontComposer")]:
    base=git(repo,"rev-parse","HEAD").decode().strip()
    idxpath=Path(git(repo,"rev-parse","--git-path","index").decode().strip())
    if not idxpath.is_absolute():idxpath=repo/idxpath
    original_index=digest(idxpath.read_bytes())
    index=TMP/(name+".index");restored=TMP/(name+"-restored.index")
    git(repo,"read-tree","HEAD",index=index)
    git(repo,"add","-A",index=index)
    tree=git(repo,"write-tree",index=index).decode().strip()
    patch=git(repo,"diff","--binary","--no-ext-diff","--no-textconv",base,tree,"--")
    git(repo,"read-tree",base,index=restored)
    git(repo,"apply","--cached","--binary","-",index=restored,data=patch)
    restored_tree=git(repo,"write-tree",index=restored).decode().strip()
    assert restored_tree==tree,(name,restored_tree,tree)
    assert digest(idxpath.read_bytes())==original_index,name
    assert git(repo,"rev-parse","HEAD").decode().strip()==base,name
    changed=git(repo,"diff","--name-only","-z",base,tree,"--").split(b"\0")
    filename=name+".patch.gz"
    packed=gzip.compress(patch,mtime=0)
    (DEST/filename).write_bytes(packed)
    (DEST/(name+"-status.txt")).write_bytes(git(repo,"status","--short","--untracked-files=all"))
    gitlinks=[]
    for item in git(repo,"ls-tree","-r","-z",tree).split(b"\0"):
        if item.startswith(b"160000 "):
            header,path=item.split(b"\t",1);gitlinks.append({"path":path.decode(),"commit":header.decode().split()[2]})
    records.append({"name":name,"repository":str(repo),"baseline_commit":base,"snapshot_tree":tree,
        "restored_tree":restored_tree,"archive":filename,"archive_bytes":len(packed),"archive_sha256":digest(packed),
        "patch_bytes":len(patch),"patch_sha256":digest(patch),"changed_paths":[p.decode() for p in changed if p],
        "gitlinks":gitlinks,"real_index_unchanged_during_capture":True})
report={"captured_at":datetime.now(timezone.utc).isoformat(),"purpose":"User-requested remote checkpoint of all saved story-24 working changes.",
    "publication":"CiCd archival branch only; module refs/pins are not published or advanced.",
    "implementation_complete":False,"current_candidate_fully_verified":False,
    "normal_git_ignored_outputs_included":False,"records":records,
    "existing_main_checkpoint":"a46a061c02f3865296cc3e98231f92abb8e36987"}
(DEST/"manifest.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"records":[{k:v for k,v in r.items() if k not in ("changed_paths","gitlinks")} for r in records]},indent=2))
