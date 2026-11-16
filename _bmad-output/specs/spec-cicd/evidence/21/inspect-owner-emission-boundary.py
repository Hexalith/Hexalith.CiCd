"""Inspect the pinned foreign owner without restoring/building ordinary source libraries."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

EVIDENCE = Path(__file__).resolve().parent
CICD = Path(__file__).resolve().parents[5]
LOCAL = Path('/home/administrator/projects/hexalith/cicd/references')
ROOT = Path(os.environ['TMPDIR'])/'owner-inspection'
ROOT.mkdir()
commands = []

def run(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=90)
    commands.append(dict(command=list(map(str,args)), cwd=str(cwd or Path.cwd()), exit_code=result.returncode,
                         stdout=result.stdout, stderr=result.stderr))
    result.check_returncode()
    return result.stdout

def clone(name, revision):
    path=ROOT/'references'/name
    run(['git','clone','--quiet','--local','--shared','--no-checkout','--no-recurse-submodules',str(LOCAL/name),str(path)])
    run(['git','checkout','--quiet','--detach',revision],path)
    return path

revision=run(['git','ls-files','--stage','references/Hexalith.EventStore'], CICD/'references/Hexalith.Parties').split()[1]
owner=clone('Hexalith.EventStore',revision)
selected=run(['git','rev-parse','v6.0.6^{commit}'],CICD/'references/Hexalith.Builds').strip()
clone('Hexalith.Builds',selected)
record=dict(eventstore=revision, builds=selected, source_files={}, evaluated={}, commands=commands,
            git_network=False, submodule_initialization=False, source_build=False)
try:
    for name in ['Hexalith.EventStore.AppHost','Hexalith.EventStore.Aspire','Hexalith.EventStore']:
        path=owner/'src'/name/(name+'.csproj')
        record['source_files'][name]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),text=path.read_text())
        output=run(['dotnet','msbuild',str(path),'-nologo','-nr:false','-m:1',
                    '-p:Configuration=Release','-p:UseHexalithProjectReferences=false','-p:UseNuGetDeps=true',
                    '-p:HexalithUsePublishedSdkForHostedTests=true','-p:HexalithEventStoreVersion=5.1.1',
                    '-getProperty:IsPackable','-getItem:ProjectReference,PackageReference'],ROOT)
        record['evaluated'][name]=json.loads(output)
finally:
    (EVIDENCE/'owner-emission-boundary.json').write_text(json.dumps(record,indent=2)+'\n')
