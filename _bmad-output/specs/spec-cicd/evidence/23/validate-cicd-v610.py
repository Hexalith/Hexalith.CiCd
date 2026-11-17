"""Run unchanged committed candidate validation with private, redacted transport.

Invoke under run-with-temp after the sequential product job has closed.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tarfile
import time
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
ROOT = Path('/home/administrator/projects/hexalith/cicd-story-23-v610')
SCRATCH = Path(os.environ['TMPDIR']).resolve(strict=True)
REVISION = 'd37a20a3318daba15066faa28f651730a7e9939e'
environment = dict(os.environ, GH_CONFIG_DIR='/home/administrator/.config/gh-cicd-agent')
assert not any(environment.get(name) for name in ('GH_TOKEN', 'GITHUB_TOKEN', 'ZIZMOR_GITHUB_TOKEN'))
assert SCRATCH.name.startswith('hexalith-job.') and SCRATCH.stat().st_uid == os.getuid()
assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip() == REVISION
assert not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain'], text=True).strip()
account = json.loads(subprocess.check_output(['gh', 'api', 'user'], env=environment, text=True))
assert (account['login'], account['id']) == ('jpiquot', 6775094)
token = subprocess.check_output(['gh', 'auth', 'token', '--hostname', 'github.com'], env=environment, text=True).strip()
assert token
archive_name = 'node-v24.22.3-linux-x64.tar.xz'
with urlopen('https://nodejs.org/dist/v24.22.3/' + archive_name, timeout=120) as response:
    archive_bytes = response.read()
archive_hash = hashlib.sha256(archive_bytes).hexdigest()
assert archive_hash == '4f2b175a6d53a5c617a80dba2676238a0688cef28c6da4eba35c7d844e66fcfb'
archive = SCRATCH / archive_name
archive.write_bytes(archive_bytes)
with tarfile.open(archive) as package:
    package.extractall(SCRATCH, filter='data')
binary = SCRATCH / archive_name.removesuffix('.tar.xz') / 'bin'
environment.update(GH_TOKEN=token, UV_CACHE_DIR=str(SCRATCH / 'uv-cache'), PYTHONDONTWRITEBYTECODE='1',
                   NPM_CONFIG_CACHE=str(SCRATCH / 'npm-cache'),
                   PATH=str(binary) + os.pathsep + environment['PATH'])
versions = [subprocess.check_output([str(binary / name), '--version'], env=environment, text=True).strip()
            for name in ('node', 'npm')]
assert versions == ['v24.22.3', '11.19.1']
command = ['uv', 'run', '--locked', '--script', '--python', '/usr/bin/python3.14',
           str(ROOT / 'tools/validate.py'), '--project-root', str(ROOT)]
record = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source': REVISION,
          'workspace': str(ROOT), 'command': command, 'profile': environment['GH_CONFIG_DIR'],
          'account': {'login': account['login'], 'id': account['id']},
          'node': {'versions': versions, 'archiveSha256': archive_hash},
          'credentialHandling': 'profile token in memory/child environment only; retained logs redact exact token',
          'remoteMutations': False, 'status': 'running', 'elapsedSeconds': 0}
report = HERE / 'cicd-v610-validation-01.json'
assert not report.exists()


def save():
    temporary = report.with_suffix('.new')
    temporary.write_text(json.dumps(record, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(report)


started = time.monotonic()
save()
with (SCRATCH / 'stdout').open('wb') as stdout, (SCRATCH / 'stderr').open('wb') as stderr:
    process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr,
                               start_new_session=True)
    try:
        while process.poll() is None:
            if time.monotonic() - started > 3600:
                raise TimeoutError('Unchanged candidate validation exceeded one hour')
            record['elapsedSeconds'] = time.monotonic() - started
            text = (SCRATCH / 'stderr').read_text(errors='replace')
            record['passedGlobalChecks'] = re.findall(r'^global ([a-z ]+): passed$', text, re.MULTILINE)
            record['finishedToolSuites'] = len(re.findall(r'^Ran [0-9]+ tests? in ', text, re.MULTILINE))
            save()
            time.sleep(5)
    except BaseException as error:
        record['controllerFailure'] = type(error).__name__
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
    record['exit'] = process.wait()
for name in ('stdout', 'stderr'):
    text = (SCRATCH / name).read_text(errors='replace').replace(token, '[redacted-profile-token]')
    path = HERE / ('cicd-v610-validation-01.' + name + '.log')
    path.open('x').write(text)
    path.chmod(0o600)
    record[name] = {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
record['elapsedSeconds'] = time.monotonic() - started
record['status'] = 'passed' if record['exit'] == 0 and 'controllerFailure' not in record else 'failed'
record['candidatePreserved'] = (subprocess.check_output(
    ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip() == REVISION
    and not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain'], text=True).strip())
if not record['candidatePreserved']:
    record['status'] = 'failed'
save()
print(json.dumps({key: record[key] for key in ('source', 'status', 'exit', 'elapsedSeconds')}, indent=2))
raise SystemExit(0 if record['status'] == 'passed' else 1)
