from pathlib import Path
import subprocess,os,json,hashlib
root=Path('/home/administrator/projects/hexalith');p=Path(__file__).resolve().parent;scratch=Path(os.environ['TMPDIR']);env=dict(os.environ,GH_CONFIG_DIR='/home/administrator/.config/gh-cicd-agent')
def run(cwd,*args):
 r=subprocess.run(args,cwd=cwd,env=env,capture_output=True,timeout=300)
 if r.returncode:raise RuntimeError(' '.join(args[:3])+': '+r.stderr.decode(errors='replace'))
 return r.stdout
state={};workspaces={}
for name,repo in [('cicd','Hexalith.CiCd'),('projects','Hexalith.Projects')]:
 original=root/name;idx=Path(run(original,'git','rev-parse','--path-format=absolute','--git-path','index').decode().strip());state[name]={'head':run(original,'git','rev-parse','HEAD').decode().strip(),'index_sha256':hashlib.sha256(idx.read_bytes()).hexdigest()}
 work=scratch/name;run(original,'git','clone','--quiet','--no-hardlinks','--no-checkout',str(original),str(work));run(work,'git','remote','set-url','origin','https://github.com/Hexalith/'+repo+'.git');run(work,'git','fetch','--no-tags','--no-recurse-submodules','origin','main');run(work,'git','-c','submodule.recurse=false','checkout','--quiet','--detach','origin/main');workspaces[name]=str(work);workspaces[name+'_source']=run(work,'git','rev-parse','HEAD').decode().strip()
assert workspaces['projects_source']=='146d0f7e9964c82da23d31b51e6ab62efdcfdda6','Projects advanced; inspect before repair'
(p/'workspace-before.json').write_text(json.dumps(state,indent=2)+'\n');(p/'workspaces.json').write_text(json.dumps(workspaces,indent=2)+'\n');print(json.dumps(workspaces,indent=2),flush=True)
