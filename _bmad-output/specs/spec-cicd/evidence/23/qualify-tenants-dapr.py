"""Run the retained native Dapr read controls; never initializes host Dapr."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

root = Path('/home/administrator/projects/hexalith/tenants-story-23-product')
evidence = Path(__file__).resolve().parent
record = {'runtime': '1.19.1', 'hostDaprInitialized': False, 'profilesLaunched': False, 'commands': []}
result = 0
for mutation in (False, True):
    label = 'mutation' if mutation else 'normal'
    report = evidence / ('product-dapr-read-' + label + '-01.json')
    log_path = evidence / ('product-dapr-read-' + label + '-01.log')
    if report.exists(): raise FileExistsError(report)
    command = ['python3', 'tests/integration/qualify-dapr-read-retries.py', '--daprd',
               '/home/administrator/.dapr/bin/daprd', '--output', str(report)]
    if mutation: command.append('--mutate-retries')
    started = time.monotonic()
    with log_path.open('x') as log:
        process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            status = process.wait(timeout=360)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGINT)
            try: status = process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                status = 124
    value = {'arguments': command, 'exitCode': status, 'elapsedSeconds': time.monotonic() - started}
    if report.is_file():
        data = json.loads(report.read_text())
        value['reportSha256'] = hashlib.sha256(report.read_bytes()).hexdigest()
        controls = data.get('results', [])
        failures = [item for item in controls if not item.get('pass')]
        value['controls'] = len(controls)
        value['failures'] = failures
        if mutation:
            value['passed'] = status != 0 and len(controls) == 13 and len(failures) == 1 and failures[0].get('case') == 'no retry on 503' and failures[0].get('backendCalls') == 4
        else:
            value['passed'] = status == 0 and len(controls) == 15 and not failures
    else:
        value['passed'] = False
        value['failure'] = 'No completed runtime report; inspect retained bounded refusal log.'
    result = result or int(not value['passed'])
    record['commands'].append(value)
record['exitCode'] = result
(evidence / 'product-dapr-qualification-01.json').open('x').write(json.dumps(record, indent=2) + '\n')
raise SystemExit(result)
