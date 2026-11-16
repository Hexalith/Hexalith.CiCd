#!/usr/bin/env python3
"""Minimal current-policy repro, without changing the scanner or module gates."""
import json
import os
from pathlib import Path
import subprocess
import sys

EVIDENCE = Path(__file__).resolve().parent
CICD = EVIDENCE.parents[4]
ROOT = Path(os.environ['TMPDIR']) / 'discovery-repro'
(ROOT / '.github/actions/example').mkdir(parents=True)
(ROOT / 'tests/tools').mkdir(parents=True)
(ROOT / '.github/actions/example/action.yml').write_text('''name: Literal PowerShell invocation\ndescription: A literal script with no child execution.\nruns:\n  using: composite\n  steps:\n    - shell: pwsh\n      run: ./tests/tools/verify.ps1\n''')
(ROOT / 'tests/tools/verify.ps1').write_text('''param([string]$Label = 'folders')\n$ErrorActionPreference = 'Stop'\nWrite-Host $Label\n''')
subprocess.run(['git', 'init', '--quiet', str(ROOT)], check=True)
subprocess.run(['git', '-C', str(ROOT), 'add', '.'], check=True)
subprocess.run(['git', '-C', str(ROOT), '-c', 'user.name=Repro', '-c', 'user.email=repro@localhost', 'commit', '--quiet', '-m', 'test: reproduce literal PowerShell discovery'], check=True)
sys.path.insert(0, str(CICD / 'tools'))
from delivery_runtime import Git
from scan_discovery import Discovery
revision = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
files, errors = Discovery(Git(ROOT), revision).discover()
result = {'revision': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(), 'cicd_source': subprocess.check_output(['git', '-C', str(CICD), 'rev-parse', 'HEAD'], text=True).strip(), 'intended_literal_callees': {'.github/actions/example/action.yml': ['tests/tools/verify.ps1'], 'tests/tools/verify.ps1': []}, 'script': (ROOT / 'tests/tools/verify.ps1').read_text(), 'selected': sorted(files), 'errors': errors, 'classification': 'False positives on ordinary PowerShell parameter/variable syntax; the script invokes no child script or process.'}
(EVIDENCE / 'action-discovery-minimal.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
