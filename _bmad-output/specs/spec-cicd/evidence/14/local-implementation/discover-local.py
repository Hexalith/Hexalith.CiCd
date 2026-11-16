"""Use the unchanged production discovery engine on exact local candidate bytes."""
from pathlib import Path
import hashlib,json,stat,subprocess,sys
ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'tools'))
from scan_discovery import Discovery
MODULE=ROOT/'references/Hexalith.Agents'
class LocalCandidate:
    def __init__(self):
        self.sources={}
        names=subprocess.check_output(['git','-C',str(MODULE),'ls-files','-z']).split(b'\0')
        names+=subprocess.check_output(['git','-C',str(MODULE),'ls-files','--others','--exclude-standard','-z']).split(b'\0')
        for raw in names:
            if not raw:continue
            name=raw.decode();path=MODULE/name
            if path.is_file() and not path.is_symlink():
                data=path.read_bytes();mode='100755' if path.stat().st_mode & stat.S_IXUSR else '100644'
                self.sources[name]=((mode,'blob',hashlib.sha256(data).hexdigest()),data)
    def items(self,revision):return {name:item[0] for name,item in self.sources.items()}
    def blob(self,revision,path):return self.sources[path][1]
selected,errors=Discovery(LocalCandidate(),'local-candidate').discover()
report={'scope':'uncommitted local candidate; production discovery engine unchanged','files':sorted(selected),'errors':errors,'result':'fail' if errors else 'pass'}
Path(__file__).with_name('hook-discovery.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(bool(errors))
