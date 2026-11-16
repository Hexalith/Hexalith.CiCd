#!/usr/bin/env python3
"""Verify the real strict runner's failure propagation without repeating product cases."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess

EVIDENCE = Path(__file__).resolve().parent
SOURCE = EVIDENCE.parents[4] / 'references/Hexalith.Folders/tests/tools/run-complete-project-tests.ps1'
ROOT = Path(os.environ['TMPDIR']) / 'runner-proof'
(ROOT / 'tests/tools').mkdir(parents=True)
shutil.copyfile(SOURCE, ROOT / 'tests/tools/run-complete-project-tests.ps1')
project = 'Hexalith.Folders.Server.Tests'
assembly = ROOT / 'tests' / project / 'bin/Release/net11.0' / (project + '.dll')
assembly.parent.mkdir(parents=True)
assembly.write_bytes(b'only checks the runner boundary; dotnet is a controlled stand-in')
binaries = ROOT / 'bin'
binaries.mkdir()
(binaries / 'dotnet').write_text('''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
Path(os.environ['RUNNER_ARGUMENTS']).write_text(json.dumps(sys.argv[1:]))
print(os.environ['RUNNER_SUMMARY'])
sys.exit(int(os.environ['RUNNER_EXIT']))
''')
(binaries / 'dotnet').chmod(0o755)
clean = 'Hexalith.Folders.Server.Tests  Total: 2, Errors: 0, Failed: 0, Skipped: 0, Not Run: 0, Time: 0.001s'
cases = [('complete', clean, 0, 0), ('zero', clean.replace('Total: 2', 'Total: 0'), 0, 1), ('missing', 'no summary', 0, 1), ('ambiguous', clean + '\n' + clean, 0, 1)]
for counter in ['Errors', 'Failed', 'Skipped', 'Not Run']:
    cases.append((counter.lower().replace(' ', '-'), clean.replace(counter + ': 0', counter + ': 1'), 0, 1))
cases.append(('native-failure', clean, 37, 37))
real_dotnet = shutil.which('dotnet')
pwsh_targets = sorted((Path(shutil.which('pwsh')).parent / '.store/powershell').rglob('unix/pwsh.dll'))
if len(pwsh_targets) != 1:
    raise RuntimeError('Expected one existing installed PowerShell runtime target')
pwsh_dll = str(pwsh_targets[0])
results = []
for name, summary, native_exit, expected in cases:
    arguments_file = ROOT / ('arguments-' + name + '.json')
    env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH'], RUNNER_ARGUMENTS=str(arguments_file), RUNNER_SUMMARY=summary, RUNNER_EXIT=str(native_exit))
    result = subprocess.run([real_dotnet, pwsh_dll, '-NoLogo', '-NoProfile', '-File', str(ROOT / 'tests/tools/run-complete-project-tests.ps1'), '-ProjectName', project], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
    received = json.loads(arguments_file.read_text())
    flags = received[1:]
    correct_arguments = flags == ['-noLogo', '-noColor', '-explicit', 'on']
    passed = result.returncode == expected and correct_arguments
    results.append({'case': name, 'native_exit': native_exit, 'expected_exit': expected, 'actual_exit': result.returncode, 'complete_explicit_selection_without_subset': correct_arguments, 'passed': passed})
    if not passed:
        raise RuntimeError(json.dumps(dict(results[-1], received=received)))
(EVIDENCE / 'complete-project-runner-qualification.json').write_text(json.dumps({'script_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'status': 'passed', 'results': results}, indent=2) + '\n')
print('All nine real runner boundary checks passed: nonempty complete selection, explicit-on, all counters, and native exit propagation.')
