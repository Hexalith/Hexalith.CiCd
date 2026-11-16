"""Qualify local candidate snapshots; never fetch, push, provision or initialize submodules."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[6]
EVIDENCE=Path(__file__).resolve().parent
SUMMARY={"scope":"local unreleased candidate only", "commands":[]}

def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args])

def run(label,args,cwd):
    path=EVIDENCE/(label+'.log')
    with path.open('w') as out:
        result=subprocess.run(args,cwd=cwd,stdout=out,stderr=subprocess.STDOUT)
    SUMMARY['commands'].append({'label':label,'arguments':args,'exitCode':result.returncode,'log':path.name})
    (EVIDENCE/'product-results.json').write_text(json.dumps(SUMMARY,indent=2)+'\n')
    print(label+': '+str(result.returncode),flush=True)
    if result.returncode:raise SystemExit(result.returncode)

def snapshot(source,destination):
    subprocess.run(['git','clone','--quiet','--shared','--no-recurse-submodules',str(source),str(destination)],check=True)
    revision=git(source,'rev-parse','HEAD').decode().strip()
    subprocess.run(['git','-C',str(destination),'checkout','--quiet','--detach',revision],check=True)
    names=git(source,'diff','--name-only','-z','HEAD').split(b'\0')
    names+=git(source,'ls-files','--others','--exclude-standard','-z').split(b'\0')
    for raw in names:
        if not raw:continue
        name=raw.decode();src=source/name;dst=destination/name
        if src.is_dir():continue
        if src.is_file():
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        elif dst.exists():dst.unlink()
    return revision

parser=argparse.ArgumentParser()
parser.add_argument("--lane", choices=("full", "independent"), default="full")
args=parser.parse_args()
SUMMARY["lane"]=args.lane
scratch=Path(os.environ['TMPDIR'])
module=scratch/'Agents';builds=module/'references/Hexalith.Builds'
SUMMARY['moduleBase']=snapshot(ROOT/'references/Hexalith.Agents',module)
SUMMARY['buildsBase']=snapshot(ROOT/'references/Hexalith.Builds',builds)
for label,candidate in [('module',module),('builds',builds)]:
    subprocess.run(['git','-C',str(candidate),'add','--all'],check=True)
    SUMMARY[label+'CandidateTree']=git(candidate,'write-tree').decode().strip()
SUMMARY['moduleCandidateDiffSha256']=hashlib.sha256(git(module,'diff','HEAD')).hexdigest()
SUMMARY['buildsCandidateDiffSha256']=hashlib.sha256(git(builds,'diff','HEAD')).hexdigest()
# Candidate floor/project changes are product files; nested gitlinks remain uninitialized.
run('agents-restore',['dotnet','restore','Hexalith.Agents.slnx','-p:Configuration=Release','-p:UseHexalithProjectReferences=false','/m:1','/nr:false'],module)
run('agents-build',['dotnet','build','Hexalith.Agents.slnx','-c','Release','--no-restore','-warnaserror','-p:UseHexalithProjectReferences=false','/m:1','/nr:false'],module)
if args.lane == 'full':
    for project,minimum in [('Contracts',529),('Client',6),('',787),('Server',549),('UI',1073)]:
        name='Hexalith.Agents'+('.'+project if project else '')+'.Tests'
        run('agents-tests-'+(project or 'Domain'),['dotnet','test','--project',f'test/{name}/{name}.csproj','-c','Release','--no-build','--no-restore','-p:UseHexalithProjectReferences=false','--stop-on-fail','off','--minimum-expected-tests',str(minimum),'--fail-skips','on'],module)
else:
    SUMMARY['scope']='Independent UI and package-hook qualification; does not replace the failed whole-repository authority suite'
    run('agents-tests-UI', ['dotnet','test','--project','test/Hexalith.Agents.UI.Tests/Hexalith.Agents.UI.Tests.csproj','-c','Release','--no-build','--no-restore','-p:UseHexalithProjectReferences=false','--stop-on-fail','off','--minimum-expected-tests','1073','--fail-skips','on'], module)
run('agents-built-package-hook',['python3','scripts/check-built-packages.py'],module)
if (module/'artifacts/cicd-agents-package-check').exists():
    raise RuntimeError('package hook retained scratch data')
SUMMARY['result']='pass'
(EVIDENCE/'product-results.json').write_text(json.dumps(SUMMARY,indent=2)+'\n')
