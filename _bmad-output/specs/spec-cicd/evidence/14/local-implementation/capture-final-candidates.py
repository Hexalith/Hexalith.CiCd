"""Capture reviewable canonical source trees without changing real indexes or HEADs."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[6]
EVIDENCE=Path(__file__).resolve().parent
report={}
for label,name in [('module','Hexalith.Agents'),('builds','Hexalith.Builds')]:
    repository=ROOT/'references'/name
    environment={**os.environ,'GIT_INDEX_FILE':str(Path(os.environ['TMPDIR'])/(label+'-index'))}
    def git(*args):return subprocess.check_output(['git','-C',str(repository),*args],env=environment)
    base=git('rev-parse','HEAD').decode().strip()
    git('read-tree','HEAD')
    git('add','--all')
    tree=git('write-tree').decode().strip()
    report[label]={'baseRevision':base,'candidateTree':tree,'changedPaths':git('diff','--cached','--name-only','HEAD').decode().splitlines()}
product=json.loads((EVIDENCE/'product-results.json').read_text())
report['qualificationLane']=product.get('lane')
report['matchesProductQualification']=all(report[label]['candidateTree']==product[label+'CandidateTree'] for label in ('module','builds'))
logs={}
for path in sorted(EVIDENCE.glob('*.log')):
    data=path.read_bytes();logs[path.name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
report['logs']=logs
(EVIDENCE/'final-candidates.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key!='logs'},indent=2))
raise SystemExit(not report['matchesProductQualification'])
