"""Exercise the exact fixture-only image handoff and host/runner UID access without printing key material."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import textwrap
import time

source = Path(sys.argv[1])
text = source.read_text()
script = textwrap.dedent(re.search(r'internal const string KeycloakStartupScript = """\n(.*?)\n        """;', text, re.S).group(1))
root = Path(os.environ['TMPDIR'])
public = root / 'public-origin'
public.mkdir(mode=0o755)
secret = root / 'private-key-proof'
secret.write_bytes(os.urandom(32))
secret.chmod(0o600)
label = 'keycloak-proof-' + os.urandom(8).hex()
image = 'quay.io/keycloak/keycloak:26.6'
passed = 0

def hostname(value):
    pending = public / 'pending'
    pending.write_text(value + '\n')
    pending.chmod(0o444)
    pending.replace(public / 'hostname')

def case(name, uid, command, expected, extra=(), timeout=30):
    global passed
    print('START', name, 'uid', uid, flush=True)
    started = time.monotonic()
    result = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--name', label + '-' + name,
        '--label', 'hexalith.keycloak-handoff-proof=' + label, '--user', uid, '--entrypoint', '/bin/bash',
        '--mount', 'type=bind,src=' + str(public) + ',target=/fixture-startup,readonly',
        *extra, image, '-c', command], capture_output=True, timeout=timeout, check=False)
    if result.returncode != expected:
        raise RuntimeError(name + ' exit=' + str(result.returncode) + ' expected=' + str(expected)
            + ' safe-output-sha256=' + hashlib.sha256(result.stdout + result.stderr).hexdigest())
    passed += 1
    print('PASS', name, 'exit', result.returncode, 'elapsed', round(time.monotonic() - started, 3), flush=True)

secret_mount = ('--mount', 'type=bind,src=' + str(secret) + ',target=/fixture-secret,readonly')
try:
    hostname('https://127.0.0.1:43190')
    case('different-uid-refused', '1001:0', 'test -r /fixture-secret', 1, secret_mount)
    case('assign-runner-owner', '0:0', 'chown 1001:0 /fixture-secret', 0,
        ('--mount', 'type=bind,src=' + str(secret) + ',target=/fixture-secret'))
    case('runner-uid-private-access', '1001:0', 'test "$EUID" -eq 1001 && test -r /fixture-secret && test -r /fixture-startup/hostname && test -w /opt/keycloak/data && test -w /opt/keycloak/lib/quarkus', 0, secret_mount)
    assert secret.stat().st_mode & 0o777 == 0o600
    for name, origin in (('foreign-origin-refused', 'https://example.invalid:43190'),
                         ('unassigned-origin-refused', 'https://127.0.0.1:0'),
                         ('outside-port-refused', 'https://127.0.0.1:65536')):
        hostname(origin)
        case(name, '1001:0', script, 125)
    (public / 'hostname').unlink()
    case('missing-handoff-bounded', '1001:0', script, 124, timeout=145)
finally:
    remaining = subprocess.check_output(['docker', 'ps', '--all', '--no-trunc', '--filter',
        'label=hexalith.keycloak-handoff-proof=' + label, '--format', '{{.ID}}'], text=True).split()
    for identity in remaining:
        custody = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .Config.Labels}}', identity]))
        if custody.get('hexalith.keycloak-handoff-proof') != label:
            raise RuntimeError('Image control custody changed')
        subprocess.run(['docker', 'rm', '--force', '--volumes', identity], check=True, capture_output=True)
    after = subprocess.check_output(['docker', 'ps', '--all', '--filter', 'label=hexalith.keycloak-handoff-proof=' + label,
        '--format', '{{.ID}}'], text=True).strip()
    if after:
        raise RuntimeError('Image control cleanup incomplete')
    print('CLEANUP complete', flush=True)
print('CONTROLS passed', passed, 'failed 0; source-sha256', hashlib.sha256(source.read_bytes()).hexdigest(),
      'script-sha256', hashlib.sha256(script.encode()).hexdigest(), flush=True)
