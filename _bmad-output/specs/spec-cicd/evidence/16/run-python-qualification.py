#!/usr/bin/env python3
"""Run changed-contract/default/lifecycle groups sequentially and retain results."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[5]
builds = root / 'references/Hexalith.Builds'
module = root / 'references/Hexalith.Conversations'
evidence = Path(__file__).resolve().parent
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
python = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else sys.executable
label = subprocess.check_output([python, '-c', 'import sys; print(".".join(map(str,sys.version_info[:3])))'],text=True).strip()
groups = [('builds-'+name, builds, ['-m','unittest','discover','-s','Github/lib/tests','-p',name+'.py','-v']) for name in (
    'test_ci_config','test_ci_pipeline','test_ci_prepare','test_ci_environment','test_module_preparation',
    'test_windows_checkout','test_ci_dapr_scope','test_local_check','test_release_state','test_release_build')]
groups += [('fixture-protocol', root, ['-m','unittest','discover','-s','tools/tests','-p','test_conversations_fixture_results.py','-v']),
           ('candidate-qualification', root, ['-m','unittest','discover','-s','tools/tests','-p','test_conversations_qualification.py','-v']),
           ('module-package-products', module, ['-m','unittest','discover','-s','tests/tooling','-p','test_package_contract.py','-v'])]
result_file = evidence/f'python-{label}-results.json'
results = json.loads(result_file.read_text()) if result_file.is_file() else []
results = [item for item in results if item['group'] != 'module-fixture-overlay']
selected = next((value.split('=', 1)[1].split(',') for value in sys.argv if value.startswith('--groups=')), None)
if selected:
    groups = [group for group in groups if group[0] in selected]
if '--failed' in sys.argv:
    failed = {result['group'] for result in results if result['exitCode']}
    groups = [group for group in groups if group[0] in failed]
for name, cwd, arguments in groups:
    log=evidence/f'python-{label}-{name}.log'
    with log.open('w') as output:
        output.write('COMMAND: '+json.dumps([python,*arguments])+'\nCWD: '+str(cwd)+'\n')
        output.flush()
        result=subprocess.run([python,*arguments],cwd=cwd,stdout=output,stderr=subprocess.STDOUT,check=False,timeout=900)
    entry = {'group':name,'python':label,'exitCode':result.returncode,'log':log.name}
    results = [item for item in results if item['group'] != name] + [entry]
    print(json.dumps(entry),flush=True)
    (evidence/f'python-{label}-results.json').write_text(json.dumps(results,indent=2)+'\n')
if any(result['exitCode'] for result in results):
    raise SystemExit(1)
