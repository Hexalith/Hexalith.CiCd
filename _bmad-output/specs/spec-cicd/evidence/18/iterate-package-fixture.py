"""Retain one private local qualification clone; every child run still owns and awaits its complete teardown."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

helper = Path(__file__).with_name('local-package-build.py')
context = {'__file__': str(helper), '__name__': '__main__'}
sys.argv = [str(helper)]
try:
    exec(compile(helper.read_text(), str(helper), 'exec'), context)
except SystemExit as completed:
    if completed.code:
        print('INITIAL BUILD FAILED', completed.code, flush=True)

root = context['root']
flags = context['flags']
workspace = root / 'tests/e2e'
iteration = 0

def run(command, cwd=root):
    print('ITERATIVE RUN', *command, flush=True)
    completed = subprocess.run(command, cwd=cwd, check=False)
    print('ITERATIVE EXIT', completed.returncode, flush=True)
    return completed.returncode

def identity():
    global iteration
    iteration += 1
    state = {}
    for name in ('Projects', 'Folders', 'Builds', 'EventStore', 'Tenants', 'Platform'):
        repository = root if name == 'Projects' else root / 'references' / ('Hexalith.' + name)
        paths = subprocess.check_output(['git', '-C', str(repository), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'])
        digest = hashlib.sha256()
        for raw in sorted(set(paths.split(b'\0')) - {b''}):
            path = repository / os.fsdecode(raw)
            if path.is_file() and not path.is_symlink():
                digest.update(raw + b'\0' + hashlib.sha256(path.read_bytes()).digest())
        state[name] = {'revision': subprocess.check_output(['git', '-C', str(repository), 'rev-parse', 'HEAD'], text=True).strip(),
                       'candidate_sha256': digest.hexdigest()}
    print('ITERATION SOURCE', iteration, json.dumps(state, sort_keys=True), flush=True)

print('PRIVATE WORKSPACE', root, flush=True)
identity()
print('ITERATION READY: build, safety, npm, run, identity, quit', flush=True)
while True:
    selected = sys.stdin.readline().strip()
    if selected in ('', 'quit'):
        print('ITERATION CLEANUP', flush=True)
        break
    if selected == 'identity':
        identity()
    elif selected == 'build':
        identity()
        run(['dotnet', 'build', 'tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj',
             '--no-restore', '--disable-build-servers', *flags])
    elif selected == 'safety':
        run(['dotnet', 'tests/Hexalith.Projects.Integration.Tests/bin/Release/net11.0/Hexalith.Projects.Integration.Tests.dll',
             '-class', 'Hexalith.Projects.Integration.Tests.PackageFixtureSafetyTests',
             '-class', 'Hexalith.Projects.Integration.Tests.PackageCredentialMatrixTests',
             '-class', 'Hexalith.Projects.Integration.Tests.PackageOwnerMetadataTests', '-noColor', '-failSkips'])
    elif selected == 'npm':
        for command in (['npm', 'ci', '--ignore-scripts'], ['npm', 'audit', 'signatures'], ['npm', 'run', 'typecheck'],
                        ['node', 'node_modules/@playwright/test/cli.js', 'test', 'specs/browser-configuration.spec.ts', '--project', 'chromium', '--workers', '1', '--retries', '0'],
                        ['node', 'node_modules/@playwright/test/cli.js', 'install']):
            if run(command, workspace):
                break
    elif selected == 'run':
        identity()
        run(['npm', 'run', 'test:package'], workspace)
    else:
        print('UNKNOWN ITERATION COMMAND', flush=True)
    print('ITERATION READY', flush=True)
