"""Qualify functional browser helpers with an exact disposable Node24 runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from urllib.request import urlopen

parser = argparse.ArgumentParser()
parser.add_argument('--attempt', required=True)
parser.add_argument('--audit-only', action='store_true')
args = parser.parse_args()
if not args.attempt.replace('-', '').isalnum(): raise ValueError('An immutable attempt identifier is required.')
source = Path('/home/administrator/projects/hexalith/tenants-story-23-product')
original = Path('/home/administrator/projects/hexalith/tenants')
temporary = Path(os.environ['TMPDIR'])
evidence = Path(__file__).resolve().parent
record = {'attempt': args.attempt, 'nodeVersion': '24.22.3', 'npmVersion': '11.19.1', 'commands': []}
filename = 'node-v24.22.3-linux-x64.tar.xz'
base = 'https://nodejs.org/dist/v24.22.3/'
with urlopen(base + 'SHASUMS256.txt', timeout=60) as response:
    sums = response.read().decode('utf-8')
rows = [line.split() for line in sums.splitlines() if line.split()[-1] == filename]
if len(rows) != 1 or len(rows[0][0]) != 64:
    raise ValueError('The official exact Node archive checksum is unavailable.')
with urlopen(base + filename, timeout=120) as response:
    archive = response.read()
record['archiveSha256'] = hashlib.sha256(archive).hexdigest()
if record['archiveSha256'] != rows[0][0]: raise ValueError('The exact Node runtime archive failed integrity verification.')
path = temporary / filename
path.write_bytes(archive)
with tarfile.open(path) as package:
    package.extractall(temporary, filter='data')
binary = temporary / filename.removesuffix('.tar.xz') / 'bin'
environment = {**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH'], 'PLAYWRIGHT_BROWSERS_PATH': str(temporary / 'browsers'), 'npm_config_cache': str(temporary / 'npm-cache')}
root = temporary / 'Hexalith.Tenants'
browser = root / 'tests/Hexalith.Tenants.UI.Tests/Browser'
browser.parent.mkdir(parents=True)
shutil.copytree(source / 'tests/Hexalith.Tenants.UI.Tests/Browser', browser)
focus = root / 'src/Hexalith.Tenants.UI/wwwroot/js/tenantsFocus.js'
focus.parent.mkdir(parents=True)
shutil.copy2(source / 'src/Hexalith.Tenants.UI/wwwroot/js/tenantsFocus.js', focus)
workspace = root / 'tests/performance/tenant-audit'
workspace.mkdir(parents=True)
for name in ('package.json', 'package-lock.json'):
    data = (source / 'tests/performance/tenant-audit' / name).read_bytes()
    if data != (original / 'tests/performance/tenant-audit' / name).read_bytes(): raise ValueError('The cached functional workspace is not the exact product lock.')
    (workspace / name).write_bytes(data)
(workspace / 'node_modules').symlink_to(original / 'tests/performance/tenant-audit/node_modules', target_is_directory=True)
record['functionalWorkspaceLockSha256'] = hashlib.sha256((workspace / 'package-lock.json').read_bytes()).hexdigest()
result = 0
try:
    commands = ([str(binary / 'node'), '--version'], [str(binary / 'npm'), '--version'],
                    [str(binary / 'node'), str(workspace / 'node_modules/playwright/cli.js'), 'install', 'chromium'],
                    [str(binary / 'node'), '--test', *[str(browser / name) for name in (
                        'authenticated-live-route-waits.test.mjs', 'authenticated-live-route-evidence.test.mjs', 'published-frontcomposer-evidence.test.mjs')]])
    if args.audit_only:
        commands = ([str(binary / 'node'), '--version'], [str(binary / 'npm'), '--version'],
                    [str(binary / 'npm'), 'audit', '--package-lock-only', '--ignore-scripts', '--json'])
    for command in commands:
        print('RUN', json.dumps(command), flush=True)
        completed = subprocess.run(command, cwd=workspace if args.audit_only else root, env=environment, check=False, timeout=600, text=True, capture_output=args.audit_only)
        if args.audit_only:
            print(completed.stdout, flush=True)
            print(completed.stderr, flush=True)
            if 'audit' in command:
                audit = json.loads(completed.stdout)
                record['audit'] = audit
                if audit.get('error') or any(audit.get('metadata', {}).get('vulnerabilities', {}).values()):
                    completed.returncode = completed.returncode or 1
        record['commands'].append({'arguments': command, 'exitCode': completed.returncode})
        result = result or completed.returncode
        if completed.returncode: break
except Exception as error:
    result = 1
    record['qualificationFailure'] = str(error)
    raise
finally:
    record['exitCode'] = result
    (evidence / ('product-node24-' + args.attempt + '.json')).open('x').write(json.dumps(record, indent=2) + '\n')
raise SystemExit(result)
