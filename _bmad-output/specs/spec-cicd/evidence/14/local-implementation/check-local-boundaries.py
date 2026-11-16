"""Check unchanged owned bytes/modes/gitlinks and use the released audit lint on local product bytes."""
from pathlib import Path
import hashlib,json,stat,subprocess,sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[6]
MODULE=ROOT/'references/Hexalith.Agents'
BUILDS=ROOT/'references/Hexalith.Builds'
sys.path.insert(0,str(BUILDS/'Github/lib'))
import audit_lint

def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args])
base=git(MODULE,'rev-parse','HEAD').decode().strip()
changes=git(MODULE,'diff','--name-only','HEAD').decode().splitlines()
fixed=['.gitmodules','AGENTS.md','CLAUDE.md','.github/copilot-instructions.md','.claude/settings.json','references/Hexalith.Builds']
fixed+=git(MODULE,'ls-files','.github/workflows/*','.github/dependabot*','*commitlint*','*releaserc*').decode().splitlines()
owned=[]
for name in sorted(set(fixed)):
    row=git(MODULE,'ls-tree',base,'--',name).decode().strip()
    if not row:continue
    metadata,path=row.split('\t',1);mode,kind,oid=metadata.split()
    exact=name not in changes
    if kind=='blob':
        candidate=MODULE/name
        exact=exact and candidate.is_file() and git(MODULE,'show',base+':'+name)==candidate.read_bytes()
        actual_mode='100755' if candidate.stat().st_mode & stat.S_IXUSR else '100644'
        exact=exact and actual_mode==mode
    owned.append({'path':name,'mode':mode,'gitObject':oid,'unchanged':exact})
class Snapshot:
    def __init__(self):
        self.items={};self.data={}
        for raw in git(MODULE,'ls-files','-z') .split(b'\0'):
            if not raw:continue
            name=raw.decode();path=MODULE/name
            if path.is_file():
                data=path.read_bytes();self.data[name]=data
                self.items[name]=SimpleNamespace(mode='100755' if path.stat().st_mode & stat.S_IXUSR else '100644')
    def read(self,path):return self.data[path]
try:audit_lint.lint(Snapshot());audit={'result':'pass'}
except Exception as error:audit={'result':'fail','diagnostic':str(error)}
report={'moduleBase':base,'freshMainFetch':'pending; this run authorizes no remote operations','owned':owned,'ownedResult':'pass' if all(row['unchanged'] for row in owned) else 'fail','audit':audit,'auditSourceUnchangedFromRelease':git(BUILDS,'show','fdda17c0a4538b0f7c99f813c20ca24b49006530:Github/lib/audit_lint.py')==(BUILDS/'Github/lib/audit_lint.py').read_bytes()}
Path(__file__).with_name('local-boundaries.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(report['ownedResult']!='pass' or audit['result']!='pass')
