from pathlib import Path
import hashlib
import json
import os
import subprocess

root = Path('/home/administrator/projects/hexalith/cicd')
source = root / '_bmad-output/specs/spec-cicd/evidence/18/local-package-build.py'
text = source.read_text().split("root = scratch / 'Hexalith.Projects'")[0]
needle = "    names = (subprocess.check_output"
insertion = """    if module not in ('Projects', 'Folders'):
        entry = subprocess.check_output(['git', '-C', str(source / 'references/Hexalith.Projects'), 'ls-tree', 'HEAD', 'references/' + name], text=True).split()
        if not entry or entry[0] != '160000':
            raise RuntimeError('Missing committed direct dependency: ' + name)
        subprocess.run(['git', '-C', str(target), 'checkout', '--quiet', '--detach', entry[2]], check=True)
        print('EXACT COMMITTED DEPENDENCY', name, entry[2], flush=True)
        continue
"""
assert needle in text
text = text.replace(needle, insertion + needle, 1)
exec(compile(text, str(source), 'exec'), {'__name__':'__snapshot__','__file__':str(source)})
job = Path(os.environ['TMPDIR']) / 'Hexalith.Projects'
report = {'scope':'Local product qualification; unpublished Folder owner changes are explicit candidate inputs, not pre-push or adoption acceptance.', 'modules':{}}
for name, repository in [('Projects',job),('Folders',job/'references/Hexalith.Folders')]:
    entries = set((subprocess.check_output(['git','-C',str(repository),'ls-files','-z']) + subprocess.check_output(['git','-C',str(repository),'ls-files','--others','--exclude-standard','-z'])).split(b'\0'))
    rows = {}
    for value in sorted(entries-{b''}):
        p = repository / os.fsdecode(value)
        if p.is_file() and not p.is_symlink():
            rows[os.fsdecode(value)] = {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mode':oct(p.stat().st_mode & 0o777)}
    report['modules'][name] = {'head':subprocess.check_output(['git','-C',str(repository),'rev-parse','HEAD'],text=True).strip(),'files':rows}
(root/'_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116/snapshot.json').write_text(json.dumps(report,indent=2)+'\n')
print('Prepared frozen Projects/Folder candidate with per-file hashes', flush=True)
