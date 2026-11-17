"""Qualify current-main complete live provenance capture under run-with-temp."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import tarfile
import urllib.request
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('--attempt', required=True)
args = parser.parse_args()
if not args.attempt.replace('-', '').isalnum(): raise ValueError('An immutable attempt name is required.')
source = Path('/home/administrator/projects/hexalith/tenants-story-23-current')
evidence = Path(__file__).resolve().parent
root = Path(os.environ['TMPDIR']) / 'Tenants'
record = {'attempt': args.attempt, 'source': str(source), 'commands': [], 'startedAt': time.time(),
          'nativeAppHostLaunched': False, 'nestedSubmodulesInitialized': False}
def git(repository, *arguments):
    return subprocess.check_output(['git', '-C', str(repository), *arguments], text=True).strip()
def clone(repository, target, revision):
    subprocess.run(['git', 'clone', '--quiet', '--local', '--shared', '--no-recurse-submodules', '--no-checkout', str(repository), str(target)], check=True)
    subprocess.run(['git', '-C', str(target), 'checkout', '--quiet', '--detach', revision], check=True)
record['baseline'] = git(source, 'rev-parse', 'HEAD')
clone(source, root, record['baseline'])
changes = set(subprocess.check_output(['git', '-C', str(source), 'diff', '--name-only', 'HEAD', '-z']).split(b'\0')
    + subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others', '--exclude-standard', '-z']).split(b'\0')) - {b''}
for raw in changes:
    relative = os.fsdecode(raw)
    path, target = source / relative, root / relative
    if path.is_file() and not path.is_symlink():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    elif not path.exists() and target.is_file(): target.unlink()
subprocess.run(['git', '-C', str(root), '-c', 'core.safecrlf=false', 'add', '-A'], check=True)
record['candidateTree'] = git(root, 'write-tree')
record['changesAfterParentCommit'] = git(root, 'diff', '--cached', '--name-only', 'HEAD').splitlines()
record['normalizedInputs'] = {row.split('\t', 1)[1]: row.split()[1] for row in git(root, 'ls-files', '--stage').splitlines()}
subprocess.run(['git', '-C', str(root), '-c', 'core.autocrlf=false', 'checkout-index', '--force', '--all'], check=True)
manifest = {}
paths = set(subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z']).split(b'\0')
    + subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others', '--exclude-standard', '-z']).split(b'\0')) - {b''}
for raw in paths:
    relative = os.fsdecode(raw)
    path = source / relative
    if path.is_file() and not path.is_symlink(): manifest[relative] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'mode': oct(path.stat().st_mode & 0o777)}
(evidence / ('product-manifest-' + args.attempt + '.json')).open('x').write(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
patch = subprocess.check_output(['git', '-C', str(root), 'diff', '--cached', '--binary', '--no-ext-diff', 'HEAD'])
patch_path = evidence / ('product-candidate-' + args.attempt + '.patch')
patch_path.open('xb').write(patch)
record['candidatePatch'] = {'path': patch_path.name, 'sha256': hashlib.sha256(patch).hexdigest()}
record['nativeAppHostLaunched'] = False
record['nodeTestFile'] = 'tests/Hexalith.Tenants.UI.Tests/Browser/published-frontcomposer-evidence.test.mjs'
result = 0
try:
    version = '24.22.3'
    name = 'node-v' + version + '-linux-x64.tar.xz'
    archive = Path(os.environ['TMPDIR']) / name
    sums = urllib.request.urlopen('https://nodejs.org/dist/v' + version + '/SHASUMS256.txt', timeout=60).read().decode()
    expected = next(line.split()[0] for line in sums.splitlines() if line.split()[-1] == name)
    archive.write_bytes(urllib.request.urlopen('https://nodejs.org/dist/v' + version + '/' + name, timeout=90).read())
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected: raise ValueError('The exact Node archive digest differs.')
    with tarfile.open(archive) as package: package.extractall(Path(os.environ['TMPDIR']), filter='data')
    binary = Path(os.environ['TMPDIR']) / ('node-v' + version + '-linux-x64/bin/node')
    record['runtime'] = {'version': subprocess.check_output([str(binary), '--version'], text=True).strip(),
        'archive': name, 'archiveSha256': actual, 'binarySha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'officialDigestVerified': True}
    arguments = [str(binary), '--test', record['nodeTestFile']]
    print('RUN', json.dumps(arguments), flush=True)
    started = time.monotonic()
    completed = subprocess.run(arguments, cwd=root, env=os.environ, timeout=60, capture_output=True, text=True)
    print(completed.stdout, flush=True)
    print(completed.stderr, flush=True)
    counters = {}
    for line in completed.stdout.splitlines():
        if line.startswith('ℹ '):
            parts = line[2:].split()
            if len(parts) == 2 and parts[1].isdigit(): counters[parts[0]] = int(parts[1])
    record['testCounters'] = counters
    result = completed.returncode
    if not result and (counters.get('tests', 0) < 133 or counters.get('fail') != 0 or counters.get('skipped') != 0):
        raise ValueError('Complete no-skip Node counters are required.')
    record['commands'].append({'arguments': arguments, 'exitCode': completed.returncode, 'elapsedSeconds': time.monotonic() - started})
except BaseException as error:
    result = 1
    record['jobFailure'] = type(error).__name__
    raise
finally:
    record['exitCode'] = result
    record['finishedAt'] = time.time()
    (evidence / ('product-local-' + args.attempt + '.json')).open('x').write(json.dumps(record, indent=2) + '\n')
raise SystemExit(result)
