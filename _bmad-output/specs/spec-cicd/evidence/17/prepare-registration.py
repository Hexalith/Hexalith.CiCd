#!/usr/bin/env python3
"""Render the proposed registration without activating or publishing it."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

EVIDENCE = Path(__file__).resolve().parent
CICD = EVIDENCE.parents[4]
ROOT = Path(os.environ['TMPDIR']) / 'cicd'
source = CICD / 'references/Hexalith.Builds'
subprocess.run(['git', '-c', 'submodule.recurse=false', 'clone', '--shared', str(CICD), str(ROOT)], check=True, capture_output=True)
subprocess.run(['git', '-c', 'submodule.recurse=false', 'clone', '--shared', str(source), str(ROOT / 'references/Hexalith.Builds')], check=True, capture_output=True)
shutil.copyfile(EVIDENCE / 'Hexalith.Folders.setup-candidate.yml', ROOT / 'setup/Hexalith.Folders.yml')
results = []
for label, arguments in [('candidate-render', []), ('candidate-render-check', ['--check'])]:
    with (EVIDENCE / (label + '.log')).open('w') as output:
        process = subprocess.run(['uv', 'run', '--locked', '--script', 'tools/render.py', *arguments], cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
    results.append({'label': label, 'exit_code': process.returncode})
    if process.returncode:
        raise SystemExit(process.returncode)
output = EVIDENCE / 'registration-candidate'
output.mkdir(exist_ok=True)
shutil.copytree(ROOT / 'rendered/Hexalith.Folders', output / 'rendered/Hexalith.Folders', dirs_exist_ok=True)
shutil.copyfile(ROOT / 'rendered/Hexalith.Folders.perimeter.json', output / 'rendered/Hexalith.Folders.perimeter.json')
shutil.copytree(ROOT / 'setup', output / 'setup', dirs_exist_ok=True)
manifest = {'cicd_base': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(), 'results': results, 'files': {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.rglob('*')) if path.is_file()}, 'status': 'rendered-local-only', 'activation_requires': ['Successful exact product-preparation proof including released audit/action/commit checks and complete retained coverage.', 'Predecessor acceptance and ordered AD-21 provisioning.', 'Protected module-agent publication and freshly revalidated remote preparation commit.', 'Setup, reproducible render and remotely available gitlink committed together.']}
(EVIDENCE / 'registration-candidate.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Candidate registration rendered and checked; production setup and gitlink were not changed.')
