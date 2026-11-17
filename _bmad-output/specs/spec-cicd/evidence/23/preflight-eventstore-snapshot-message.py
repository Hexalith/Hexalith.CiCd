"""Validate the exact upstream message using its locked owning-repository policy."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
SOURCE = Path('/home/administrator/projects/hexalith/eventstore-story-23-snapshot-recovered')
SCRATCH = Path(os.environ['TMPDIR'])
MESSAGE = 'feat(snapshots): support qualified aggregate capture and actor configuration\n'
record = {'at': datetime.now(timezone.utc).isoformat(), 'commands': [], 'remoteWrites': False}
env = dict(os.environ)
for name in ('HOME', 'DOTNET_CLI_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME'):
    path = SCRATCH / name.lower()
    path.mkdir(mode=0o700)
    env[name] = str(path)
for name in ('GH_TOKEN', 'GITHUB_TOKEN', 'NODE_AUTH_TOKEN', 'NPM_TOKEN'):
    env.pop(name, None)
env.update(npm_config_cache=str(SCRATCH / 'npm-cache'), HUSKY='0')
root = SCRATCH / 'message-policy'
root.mkdir()
for name in ('package.json', 'package-lock.json', 'commitlint.config.js'):
    if not (SOURCE / name).is_file() and name == 'commitlint.config.js':
        name = 'commitlint.config.mjs'
    shutil.copyfile(SOURCE / name, root / name)
record['policyInputs'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
assert json.loads((root / 'package-lock.json').read_text())['packages']['node_modules/@commitlint/cli']['version'] == '21.2.4'
filename = 'node-v24.22.3-linux-x64.tar.xz'
with urlopen('https://nodejs.org/dist/v24.22.3/' + filename, timeout=60) as response:
    data = response.read()
digest = hashlib.sha256(data).hexdigest()
assert digest == '4f2b175a6d53a5c617a80dba2676238a0688cef28c6da4eba35c7d844e66fcfb'
archive = SCRATCH / filename
archive.write_bytes(data)
with tarfile.open(archive) as package:
    package.extractall(SCRATCH, filter='data')
binary = SCRATCH / filename.removesuffix('.tar.xz') / 'bin'
env['PATH'] = str(binary) + os.pathsep + env['PATH']
record['nodeArchiveSha256'] = digest
record['versions'] = {name: subprocess.check_output([name, '--version'], env=env, text=True).strip() for name in ('node', 'npm')}
assert record['versions'] == {'node': 'v24.22.3', 'npm': '11.19.1'}
message = root / 'candidate-message.txt'
message.write_text(MESSAGE)
try:
    for command in ([str(binary / 'npm'), 'ci', '--ignore-scripts'],
                    [str(binary / 'npm'), 'audit', 'signatures'],
                    [str(root / 'node_modules/.bin/commitlint'), '--config', str(root / 'commitlint.config.mjs'), '--color=false']):
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=180,
                                input=MESSAGE if command[0].endswith('/commitlint') else None)
        record['commands'].append({'arguments': command, 'exit': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr})
        if result.returncode:
            raise RuntimeError('Owning commit-message preflight failed')
    record['passed'] = True
    record['exactMessage'] = MESSAGE
    record['messageSha256'] = hashlib.sha256(message.read_bytes()).hexdigest()
    (HERE / 'eventstore-snapshot-commit-message.txt').open('x').write(MESSAGE)
finally:
    (HERE / 'eventstore-snapshot-message-preflight02.json').open('x').write(json.dumps(record, indent=2) + '\n')
print(json.dumps({'passed': record['passed'], 'policyInputs': record['policyInputs'], 'versions': record['versions']}))
