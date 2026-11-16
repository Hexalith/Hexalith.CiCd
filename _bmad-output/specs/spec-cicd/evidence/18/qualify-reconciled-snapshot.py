"""Qualify one immutable, standalone local snapshot; run beneath run-with-temp."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

source = Path(__file__).resolve().parents[5]
evidence = Path(__file__).resolve().parent
scratch = Path(os.environ['TMPDIR'])
result_path = evidence / 'matrix-reconciled-qualification.json'
state = {'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'modules': {}, 'commands': [], 'complete': False}


def save():
    result_path.write_text(json.dumps(state, indent=2) + '\n')


def git(repository, *args, env=None):
    return subprocess.check_output(['git', '-C', str(repository), *args], env=env).decode().strip()


def run(label, command, cwd):
    print('QUALIFICATION RUN', label, flush=True)
    started = time.monotonic()
    completed = subprocess.run(command, cwd=cwd, check=False)
    state['commands'].append({'label': label, 'argv': command,
                              'exit': completed.returncode,
                              'seconds': round(time.monotonic() - started, 3)})
    save()
    print('QUALIFICATION RESULT', label, completed.returncode, flush=True)
    return completed.returncode


os.environ.update(DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER='1', DOTNET_CLI_USE_MSBUILD_SERVER='0',
                  MSBUILDDISABLENODEREUSE='1')
root = scratch / 'Hexalith.Projects'
for module in ('Projects', 'Builds', 'EventStore', 'Tenants', 'Folders', 'Platform'):
    name = 'Hexalith.' + module
    repository = source / 'references' / name
    target = root if module == 'Projects' else root / 'references' / name
    env = os.environ.copy()
    env['GIT_INDEX_FILE'] = str(scratch / (name + '.index'))
    before = git(repository, 'rev-parse', 'HEAD')
    git(repository, 'read-tree', before, env=env)
    git(repository, 'add', '-A', '--', '.', env=env)
    tree = git(repository, 'write-tree', env=env)
    subprocess.run(['git', 'clone', '--quiet', '--local', '--shared', '--no-checkout',
                    '--no-recurse-submodules', str(repository), str(target)], check=True)
    git(target, 'read-tree', tree)
    git(target, 'checkout-index', '--all', '--force')
    state['modules'][name] = {'head_before_capture': before, 'snapshot_tree': tree,
                              'head_after_capture': git(repository, 'rev-parse', 'HEAD')}
    save()
    print('QUALIFICATION SNAPSHOT', name, tree, flush=True)

config = root / 'references/Hexalith.Builds/NuGet.ci.Config'
flags = ['-noAutoResponse', '-p:Configuration=Release', '-warnaserror',
         '-p:UseHexalithProjectReferences=false', '-p:ShouldUnsetParentConfigurationAndPlatform=false',
         f'-p:RestoreConfigFile={config}', '-p:EnableNETAnalyzers=true', '-p:RunAnalyzers=true',
         '-p:RunAnalyzersDuringBuild=true', '-p:UseSharedCompilation=false', '-nr:false', '-m:1']
for mode, extra in (('restore', []), ('build', ['--no-restore'])):
    if run(mode, ['dotnet', mode, 'Hexalith.Projects.CI.slnx', *extra,
                  '--disable-build-servers', *flags], root):
        sys.exit(1)

sys.path.insert(0, str(root / 'references/Hexalith.Builds/Github/lib'))
import ci_pipeline
try:
    started = time.monotonic()
    tests = ci_pipeline.discover_test_projects(root, 'Hexalith.Projects.CI.slnx')
    ci_pipeline.execute_test_projects(root, tests, runner=ci_pipeline.test_runner(root), stage='Preserved product')
    state['commands'].append({'label': 'preserved-product', 'exit': 0,
                              'seconds': round(time.monotonic() - started, 3)})
except Exception:
    state['commands'].append({'label': 'preserved-product', 'exit': 1})
    save()
    raise
save()

failures = []
for label, command in (
    ('tool-restore', ['dotnet', 'tool', 'restore', '--tool-manifest', '.config/dotnet-tools.json',
                      '--configfile', str(config)]),
    ('frontcomposer', ['python3', 'scripts/check-frontcomposer-output.py']),
    ('packages', ['python3', 'scripts/check-package-dependencies.py']),
    ('package-tool-controls', ['python3', '-B', '-m', 'unittest', 'discover', '-s', 'tests/tools',
                               '-p', 'test_release_package_tools.py', '-v']),
):
    if run(label, command, root):
        failures.append(label)

workspace = root / 'tests/e2e'
for label, command in (
    ('npm-ci', ['npm', 'ci', '--ignore-scripts']),
    ('npm-signatures', ['npm', 'audit', 'signatures']),
    ('browser-types', ['npm', 'run', 'typecheck']),
    ('browser-selection', ['node', 'node_modules/@playwright/test/cli.js', 'test',
                           'specs/browser-configuration.spec.ts', '--project', 'chromium',
                           '--workers', '1', '--retries', '0']),
    ('browser-install', ['node', 'node_modules/@playwright/test/cli.js', 'install']),
    ('complete-package-runtime', ['npm', 'run', 'test:package']),
):
    if run(label, command, workspace):
        failures.append(label)
        break

state['complete'] = True
state['failures'] = failures
save()
print('QUALIFICATION FAILURES', json.dumps(failures), flush=True)
sys.exit(bool(failures))
