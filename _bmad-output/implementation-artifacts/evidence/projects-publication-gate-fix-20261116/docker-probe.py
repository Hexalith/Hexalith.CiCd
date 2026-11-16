from pathlib import Path
import hashlib
import json
import os
import re
import runpy
import socket
import subprocess
import time
import uuid

root = Path('/home/administrator/projects/hexalith/cicd')
source = root / '_bmad-output/specs/spec-cicd/evidence/18/qualify-owning-g6.py'
g6 = runpy.run_path(str(source))
job = Path(os.environ['TMPDIR']) / 'docker-port-probe'
job.mkdir(exist_ok=True)
namespace = 'g6-portfix-' + uuid.uuid4().hex
owned, cleaned = [], []
report = {'namespace': namespace, 'helper_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'excluded_ranges': g6['_windows_excluded_ports'](), 'probe_complete': False}

def remove():
    while owned:
        cleaned.append(g6['_remove_owned_container'](owned[-1], namespace))
        owned.pop()

def create(port, attempt):
    name = namespace + '-' + str(attempt)
    cid = job / (name + '.cid')
    command = ['docker', 'run', '--detach', '--cidfile', str(cid), '--name', name,
               '--label', 'hexalith.story18-g6=' + namespace, '-p', f'127.0.0.1:{port}:50006',
               'daprio/dapr:1.19.1', './scheduler', '--port', '50006', '--etcd-data-dir', '/tmp/g6-scheduler',
               '--etcd-client-listen-address', '0.0.0.0', '--override-broadcast-host-port', f'127.0.0.1:{port}']
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if cid.exists():
        identity = cid.read_text().strip()
        assert re.fullmatch('[0-9a-f]{64}', identity)
        owned.append(identity)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
    binding = subprocess.check_output(['docker', 'port', owned[-1], '50006/tcp'], text=True, timeout=30).strip()
    assert binding == f'127.0.0.1:{port}', binding
    return name, port

try:
    if any(first <= 51825 <= last for first, last in report['excluded_ranges']):
        try:
            create(51825, 0)
        except subprocess.CalledProcessError as error:
            report['original_port_refusal_exit'] = error.returncode
            report['original_port_refusal'] = error.stderr
            assert error.returncode == 125 and 'ports are not available' in error.stderr.lower()
        else:
            raise AssertionError('Windows excluded port unexpectedly admitted')
        finally:
            remove()
    name, port = g6['_start_scheduler'](create, remove)
    until = time.monotonic() + 30
    while True:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                break
        except OSError:
            if time.monotonic() >= until:
                raise
            time.sleep(.2)
    assert subprocess.check_output(['docker', 'inspect', '--format', '{{.State.Running}}', owned[-1]],
                                   text=True, timeout=30).strip() == 'true'
    report.update(selected_port=port, loopback_endpoint_reachable=True, scheduler_running=True, probe_complete=True)
finally:
    remove()
    report['cleanup'] = cleaned
    (root / '_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116/docker-probe.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
