"""Qualify exact normalized local Python inputs; run only under run-with-temp."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--attempt', required=True)
parser.add_argument('--python312-image')
parser.add_argument('--replay-red', action='store_true')
args = parser.parse_args()
if not args.attempt.replace('-', '').isalnum(): raise ValueError('A unique attempt identifier is required.')
source = Path('/home/administrator/projects/hexalith/tenants-story-23-product')
evidence = Path(__file__).resolve().parent
root = Path(os.environ['TMPDIR']) / 'Tenants'
record = {'attempt': args.attempt, 'source': str(source), 'commands': [], 'startedAt': time.time(),
          'nativeAppHostLaunched': False, 'nestedSubmodulesInitialized': False}
if args.python312_image and not args.python312_image.startswith('python@sha256:'):
    raise ValueError('The alternate runtime must be an exact official Python image digest.')
def git(repository, *arguments):
    return subprocess.check_output(['git', '-C', str(repository), *arguments], text=True).strip()
record['baseline'] = git(source, 'rev-parse', 'HEAD')
subprocess.run(['git', 'clone', '--quiet', '--local', '--shared', '--no-checkout', '--no-recurse-submodules', str(source), str(root)], check=True)
subprocess.run(['git', '-C', str(root), 'checkout', '--quiet', '--detach', record['baseline']], check=True)
changes = set(subprocess.check_output(['git', '-C', str(source), 'diff', '--name-only', 'HEAD', '-z']).split(b'\0')
              + subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others', '--exclude-standard', '-z']).split(b'\0')) - {b''}
if args.replay_red:
    replay = evidence / 'product-candidate-natural-red-01.patch'
    record['replayedPatch'] = {'path': replay.name, 'sha256': hashlib.sha256(replay.read_bytes()).hexdigest()}
    subprocess.run(['git', '-C', str(root), 'apply', '--binary', '-'], input=replay.read_bytes(), check=True)
else:
    for raw in changes:
        relative = os.fsdecode(raw)
        actual, target = source / relative, root / relative
        if actual.is_file() and not actual.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(actual, target)
        elif not actual.exists() and target.is_file(): target.unlink()
subprocess.run(['git', '-C', str(root), '-c', 'core.safecrlf=false', 'add', '-A'], check=True)
record['candidateTree'] = git(root, 'write-tree')
subprocess.run(['git', '-C', str(root), '-c', 'core.autocrlf=false', 'checkout-index', '--force', '--all'], check=True)
record['changesAfterParentCommit'] = git(root, 'diff', '--cached', '--name-only', 'HEAD').splitlines()
record['normalizedInputs'] = {row.split('\t', 1)[1]: row.split()[1] for row in git(root, 'ls-files', '--stage').splitlines()}
manifest = {}
manifest_source = root if args.replay_red else source
record['manifestBasis'] = 'materialized red replay' if args.replay_red else 'working source byte/mode inputs'
files = set(subprocess.check_output(['git', '-C', str(manifest_source), 'ls-files', '-z']).split(b'\0')
            + subprocess.check_output(['git', '-C', str(manifest_source), 'ls-files', '--others', '--exclude-standard', '-z']).split(b'\0')) - {b''}
for raw in files:
    relative = os.fsdecode(raw)
    path = manifest_source / relative
    if path.is_file() and not path.is_symlink():
        manifest[relative] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'mode': oct(path.stat().st_mode & 0o777)}
manifest_path = evidence / ('product-manifest-' + args.attempt + '.json')
manifest_path.open('x').write(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
record['manifest'] = {'path': manifest_path.name, 'sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
patch = subprocess.check_output(['git', '-C', str(root), 'diff', '--cached', '--binary', '--no-ext-diff', 'HEAD'])
patch_path = evidence / ('product-candidate-' + args.attempt + '.patch')
patch_path.open('xb').write(patch)
record['candidatePatch'] = {'path': patch_path.name, 'sha256': hashlib.sha256(patch).hexdigest()}
result = 0
try:
    for interpreter in ('python3.12', 'python3.14'):
        prefix = [interpreter]
        if interpreter == 'python3.12' and args.python312_image:
            scratch = Path(os.environ['TMPDIR']) / 'python312-scratch'
            scratch.mkdir(mode=0o700, exist_ok=True)
            prefix = ['docker', 'run', '--rm', '--name', 'tenants-s23-python-' + args.attempt,
                '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--pids-limit', '128', '--user', str(os.getuid()) + ':' + str(os.getgid()), '--workdir', '/work',
                '--mount', 'type=bind,source=' + str(root) + ',target=/work,readonly',
                '--mount', 'type=bind,source=' + str(scratch) + ',target=/scratch',
                '--env', 'TMPDIR=/scratch', '--env', 'TMP=/scratch', '--env', 'TEMP=/scratch',
                '--env', 'PYTHONDONTWRITEBYTECODE=1', '--entrypoint', 'python3', args.python312_image]
        facts = subprocess.check_output([*prefix, '-c',
            'import os,signal,sys,json;print(json.dumps(dict(executable=sys.executable,version=sys.version,pidfd_open=hasattr(os,"pidfd_open"),pidfd_send_signal=hasattr(signal,"pidfd_send_signal"))))'], text=True)
        record.setdefault('runtimes', {})[interpreter] = {**json.loads(facts), 'image': args.python312_image if interpreter == 'python3.12' else None}
        print('RUNTIME', interpreter, facts.strip(), flush=True)
        for suite in ('test_product_integration.py', 'test_source_catalog_profile.py'):
            arguments = [*prefix, '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-p', suite, '-v']
            print('RUN', json.dumps(arguments), flush=True)
            started = time.monotonic()
            completed = subprocess.run(arguments, cwd=root, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=90)
            value = {'arguments': arguments, 'exitCode': completed.returncode, 'elapsedSeconds': time.monotonic() - started}
            record['commands'].append(value)
            print('RESULT', json.dumps(value), flush=True)
            result = result or completed.returncode
finally:
    record['exitCode'] = result
    record['finishedAt'] = time.time()
    (evidence / ('product-local-' + args.attempt + '.json')).open('x').write(json.dumps(record, indent=2) + '\n')
raise SystemExit(result)
