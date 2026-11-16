#!/usr/bin/env python3
"""Exercise previously unexecuted real controls without repeating unrelated suites."""
import ctypes
import json
import os
from pathlib import Path
import re
import signal
import subprocess

EVIDENCE = Path(__file__).resolve().parent
expected = json.loads((EVIDENCE / 'product-verification.json').read_text())['candidate']
match = re.search(r'(/\S+/Hexalith\.Folders)/src/', (EVIDENCE / 'package-restore.log').read_text())
if match is None:
    raise RuntimeError('The active disposable build workspace was not found')
root = Path(match[1])
actual = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
if actual != expected:
    raise RuntimeError('Disposable source identity changed')
ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0)
commands = [
    ('explicit-server-controls', 'Hexalith.Folders.Server.Tests', ['-explicit', 'only', '-class', 'Hexalith.Folders.Server.Tests.EnrolledWorkloadSourceBoundaryTests'], {}),
    ('explicit-apphost-controls', 'Hexalith.Folders.AppHost.Tests', ['-explicit', 'only', '-class', 'Hexalith.Folders.AppHost.Tests.WorkloadEnrollmentComponentTests'], {}),
    ('fr58-opted-in-product-proof', 'Hexalith.Folders.AppHost.Tests', ['-method', 'Hexalith.Folders.AppHost.Tests.Fr58PublicMutationSearchRoundTripTests.AuthenticatedPublicAddWorkspaceFileShouldConvergeOnPublicSearchAndStatus'], {'HEXALITH_FOLDERS_RUN_ASPIRE_INTEGRATION': 'true'}),
]
results = []
for label, project, selectors, additions in commands:
    assembly = root / 'tests' / project / 'bin/Release/net11.0' / (project + '.dll')
    env = dict(os.environ, **additions)
    with (EVIDENCE / (label + '.log')).open('w') as output:
        process = subprocess.Popen(['dotnet', str(assembly), '-noLogo', '-noColor', *selectors], cwd=root, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            code = 124
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            while True:
                try:
                    os.waitpid(-process.pid, 0)
                except ChildProcessError:
                    break
    text = (EVIDENCE / (label + '.log')).read_text(errors='replace')
    summary = re.findall(r'(?m)^\s*' + re.escape(project) + r'\s+Total:\s*(\d+),\s*Errors:\s*(\d+),\s*Failed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Not Run:\s*(\d+)', text)
    results.append({'label': label, 'candidate': actual, 'arguments': ['dotnet', str(assembly), '-noLogo', '-noColor', *selectors], 'environment_names_set': sorted(additions), 'exit_code': code, 'summary': dict(zip(['total', 'errors', 'failed', 'skipped', 'not_run'], map(int, summary[0]))) if len(summary)==1 else None, 'status': 'failed-prerequisite' if code else 'passed', 'log': label+'.log'})
    print(label, 'exit', code, results[-1]['summary'], flush=True)
(EVIDENCE / 'focused-product-prerequisites.json').write_text(json.dumps({'status': 'blocked-on-genuine-product-prerequisites', 'results': results, 'interpretation': 'These are real retained product controls, deliberately not exempted. Focused selectors apply only to local investigation; delivered hooks select complete projects without class/method filters.'}, indent=2)+'\n')
