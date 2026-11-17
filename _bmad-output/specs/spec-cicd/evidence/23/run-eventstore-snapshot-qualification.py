"""Run the complete approved prerequisite check with private disposable tooling."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time
from urllib.request import urlopen
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
SCRATCH = Path(os.environ['TMPDIR'])
head = sys.argv[1]
assert re.fullmatch('[0-9a-f]{40}', head)
attempt = sys.argv[2]
assert re.fullmatch('[0-9]{2}', attempt)
report_path = HERE / ('eventstore-snapshot-complete-qualification' + attempt + '.json')
assert not report_path.exists()
record = {'at': datetime.now(timezone.utc).isoformat(), 'head': head, 'attempt': attempt,
          'scratch': str(SCRATCH), 'publicRelease': False, 'adoptionBaseline': False,
          'azureExecuted': False, 'remoteWrites': False}
environment = dict(os.environ)
for name in ('HOME', 'DOTNET_CLI_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME'):
    location = SCRATCH / name.lower()
    location.mkdir(mode=0o700)
    environment[name] = str(location)
for name in list(environment):
    if name.startswith(('PAYLOAD_AZURE_', 'HEXALITH_PP_')) or name in ('GH_TOKEN', 'GITHUB_TOKEN', 'NODE_AUTH_TOKEN', 'NPM_TOKEN'):
        environment.pop(name)
environment.update(npm_config_cache=str(SCRATCH / 'npm-cache'), HUSKY='0',
                   PYTHONDONTWRITEBYTECODE='1', DOTNET_NOLOGO='1',
                   DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER='1', DOTNET_CLI_USE_MSBUILD_SERVER='0',
                   MSBUILDDISABLENODEREUSE='1')
archive_name = 'node-v24.22.3-linux-x64.tar.xz'
with urlopen('https://nodejs.org/dist/v24.22.3/' + archive_name, timeout=60) as response:
    data = response.read()
digest = hashlib.sha256(data).hexdigest()
assert digest == '4f2b175a6d53a5c617a80dba2676238a0688cef28c6da4eba35c7d844e66fcfb'
archive = SCRATCH / archive_name
archive.write_bytes(data)
with tarfile.open(archive) as package:
    package.extractall(SCRATCH, filter='data')
binary = SCRATCH / archive_name.removesuffix('.tar.xz') / 'bin'
environment['PATH'] = str(binary) + os.pathsep + environment['PATH']
record['node'] = {name: subprocess.check_output([name, '--version'], env=environment, text=True).strip() for name in ('node', 'npm')}
assert record['node'] == {'node': 'v24.22.3', 'npm': '11.19.1'}
record['nodeArchiveSha256'] = digest
command = [sys.executable, '-B', str(HERE / 'qualify-eventstore-snapshot-candidate.py'),
           '392a7e4e9daade785ee9f1ae5f40e25931002735', head, 'v6.1.0',
           'a1e0c310b1f1a50d78e6132890fae6bcba769f6d',
           '--module', '/home/administrator/projects/hexalith/eventstore-story-23-snapshot-recovered',
           '--report', str(report_path)]
record['command'] = command
log = SCRATCH / 'qualification.log'
started = time.monotonic()
with log.open('w') as output:
    process = subprocess.Popen(command, env=environment, stdout=output, stderr=subprocess.STDOUT)
    while True:
        try:
            code = process.wait(timeout=30)
            break
        except subprocess.TimeoutExpired:
            print(json.dumps({'running': True, 'elapsedSeconds': round(time.monotonic() - started)}), flush=True)
record.update(exit=code, elapsedSeconds=time.monotonic() - started,
              rawLogSha256=hashlib.sha256(log.read_bytes()).hexdigest())
record['trx'] = []
for path in sorted(SCRATCH.rglob('*.trx')):
    try:
        document = ET.parse(path)
        counters = document.find('.//{*}Counters')
        if counters is not None:
            record['trx'].append({'path': str(path.relative_to(SCRATCH)), 'counters': counters.attrib,
                                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                  'nonPassing': [{'name': item.get('testName'), 'outcome': item.get('outcome')}
                                                 for item in document.findall('.//{*}UnitTestResult') if item.get('outcome') != 'Passed']})
    except ET.ParseError:
        record.setdefault('incompleteTrx', []).append(str(path.relative_to(SCRATCH)))
(HERE / ('eventstore-snapshot-complete-qualification-driver' + attempt + '.json')).open('x').write(json.dumps(record, indent=2) + '\n')
if code:
    print('Qualification failure context from a credential-free disposable product job:', flush=True)
    print('\n'.join(log.read_text(errors='replace').splitlines()[-45:]), flush=True)
print(json.dumps({'exit': code, 'elapsedSeconds': record['elapsedSeconds'], 'trxFiles': len(record['trx'])}), flush=True)
raise SystemExit(code)
