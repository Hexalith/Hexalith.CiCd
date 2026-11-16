"""Local workload worker; no delivered configuration or hosted result is created."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
import tarfile
import time
from urllib.request import urlopen


scratch = Path(os.environ['S23_SCRATCH'])
root = scratch / 'Hexalith.Tenants'
result_path = scratch / 'worker-result.json'

if os.getuid() == 0:
    # This account/sudo rule exists only in the disposable SDK container.
    try:
        account = pwd.getpwuid(1000)
    except KeyError:
        subprocess.run(['useradd', '--uid', '1000', '--user-group', '--no-create-home',
                        '--home-dir', str(scratch / 'home'), 'qualification'], check=True)
        account = pwd.getpwuid(1000)
    home = scratch / 'home'
    home.mkdir(mode=0o700, exist_ok=True)
    os.chown(home, account.pw_uid, account.pw_gid)
    subprocess.run(['usermod', '--home', str(home), account.pw_name], check=True)
    rule = Path('/etc/sudoers.d/tenants-local-qualification')
    rule.write_text(account.pw_name + ' ALL=(ALL) NOPASSWD: ALL\n')
    rule.chmod(0o440)
    os.chown(scratch / 'daemon-socket/docker.sock', account.pw_uid, account.pw_gid)
    os.environ.update(HOME=str(home), USER=account.pw_name, LOGNAME=account.pw_name)
    os.setgroups([])
    os.setgid(account.pw_gid)
    os.setuid(account.pw_uid)
    os.execv(sys.executable, [sys.executable, '-B', __file__])

runtime = scratch / 'runner'
runtime.mkdir(mode=0o700)
os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
                  RUNNER_TEMP=str(runtime), NPM_CONFIG_CACHE=str(runtime / 'npm-cache'),
                  NUGET_PACKAGES=str(scratch / 'home/.nuget/packages'),
                  DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1',
                  GITHUB_ENV=str(runtime / 'environment'), GITHUB_PATH=str(runtime / 'path'),
                  GITHUB_OUTPUT=str(runtime / 'output'), GITHUB_STEP_SUMMARY=str(runtime / 'summary'),
                  PYTHONDONTWRITEBYTECODE='1')
for name in ('environment', 'path', 'output', 'summary'):
    descriptor = os.open(runtime / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(descriptor)

record = {'schema': 'tenants.local-workload.v1', 'source': os.environ['GITHUB_SHA'],
          'sharedSource': os.environ['S23_BUILDS_REVISION'], 'phases': [],
          'localSyntheticIdentity': True, 'hostedCi': False, 'scheduledNightly': False,
          'publishedContract': False, 'deliveredConfigurationCreated': False,
          'startedAt': time.time()}


def save():
    target = result_path.with_suffix('.new')
    target.write_text(json.dumps(record, indent=2) + '\n')
    target.chmod(0o600)
    target.replace(result_path)


def phase(name, operation):
    row = {'name': name, 'status': 'running', 'startedAt': time.time()}
    record['phases'].append(row)
    save()
    print('[S23] START ' + name, flush=True)
    try:
        value = operation()
    except BaseException as error:
        row.update(status='failed', exceptionType=type(error).__name__,
                   exitCode=getattr(error, 'returncode', 1))
        raise
    else:
        row['status'] = 'passed'
        return value
    finally:
        row['elapsedSeconds'] = time.time() - row['startedAt']
        save()
        print('[S23] ' + row['status'].upper() + ' ' + name, flush=True)


def run(arguments, timeout=3600):
    subprocess.run(arguments, cwd=root, check=True, timeout=timeout)


def node_runtime():
    filename = 'node-v24.22.3-linux-x64.tar.xz'
    with urlopen('https://nodejs.org/dist/v24.22.3/' + filename, timeout=120) as response:
        data = response.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != '4f2b175a6d53a5c617a80dba2676238a0688cef28c6da4eba35c7d844e66fcfb':
        raise ValueError('Exact Node archive integrity refused')
    archive = runtime / filename
    archive.write_bytes(data)
    with tarfile.open(archive) as package:
        package.extractall(runtime, filter='data')
    binary = runtime / filename.removesuffix('.tar.xz') / 'bin'
    os.environ['PATH'] = str(binary) + os.pathsep + os.environ['PATH']
    versions = [subprocess.check_output([str(binary / name), '--version'], text=True).strip()
                for name in ('node', 'npm')]
    if versions != ['v24.22.3', '11.19.1']:
        raise ValueError('Exact Node/npm pair refused')
    record['node'] = {'versions': versions, 'archiveSha256': digest}


try:
    if subprocess.check_output(['dotnet', '--version'], cwd=root, text=True).strip() != '11.0.100':
        raise ValueError('Exact SDK refused')
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() != record['source']:
        raise ValueError('Exact source refused')
    sys.path.insert(0, str(scratch / 'shared-builds/Github/lib'))
    import ci_pipeline
    import ci_environment
    proposal = json.loads((scratch / 'proposal.json').read_text())['proposedSetup']
    # This is a test plan for pure build/test helpers, not an accepted module
    # configuration. No fake Builds tag, identity exception or delivered file.
    prepared = ci_pipeline.PreparedConfig(root, root, {'solution': proposal['solution'], 'tests': {}},
                                          proposal['solution'], 'global.json', ())
    units = tuple('samples/Hexalith.Tenants.Sample.Tests/Hexalith.Tenants.Sample.Tests.csproj'
                  if name == 'Sample' else f'tests/Hexalith.Tenants.{name}.Tests/Hexalith.Tenants.{name}.Tests.csproj'
                  for name in ('Sample', 'Client', 'Contracts', 'Testing', 'UI'))
    integrations = tuple(f'tests/Hexalith.Tenants.{name}.Tests/Hexalith.Tenants.{name}.Tests.csproj'
                         for name in ('AppHost', 'Server'))
    owned = 'tests/Hexalith.Tenants.IntegrationTests/Hexalith.Tenants.IntegrationTests.csproj'
    minima = dict(zip((*units, *integrations), (40, 103, 761, 198, 8085, 66, 1911)))
    phase('exact-node-runtime', node_runtime)
    phase('one-release-package-build', lambda: ci_pipeline.restore_and_build(prepared))
    discovered = ci_pipeline.discover_test_projects(root, proposal['solution'])
    if set(discovered) != {*units, *integrations, owned}:
        raise ValueError('Complete project inventory differs from the inspected test plan')
    record['testProjects'] = {'unit': units, 'integration': integrations, 'hookOwned': owned}
    runner = ci_pipeline.test_runner(root)
    phase('complete-unit-projects', lambda: ci_pipeline.execute_test_projects(
        root, units, runner=runner, stage='Unit', minimum_expected_tests=minima, fail_skips=True))
    phase('one-shared-environment', lambda: ci_environment.setup_environment(
        root, solution=proposal['solution'], dapr=proposal['dapr'], browsers=proposal['browsers'],
        registry=proposal['registry'], npm_workspaces=proposal['npmWorkspaces'],
        prerequisites=proposal['prerequisites']))
    phase('after-unit-tests-hook', lambda: run(['bash', 'scripts/run-product-unit-checks.sh']))
    phase('complete-integration-projects', lambda: ci_pipeline.execute_test_projects(
        root, integrations, runner=runner, stage='Integration', minimum_expected_tests=minima, fail_skips=True))
    # Match the composite literally, including its exact coverage and mutation controls.
    action = root / '.github/actions/after-integration-tests/action.yml'
    # PyYAML is only an orchestration dependency in this disposable worker.
    import yaml
    for index, step in enumerate(yaml.safe_load(action.read_text())['runs']['steps']):
        if 'run' in step:
            phase('after-integration-step-' + str(index + 1),
                  lambda body=step['run']: run(['bash', '--noprofile', '--norc', '-e', '-o', 'pipefail', '-c', body], 14400))
    phase('nightly-product-workload-local-only', lambda: run(['bash', 'scripts/run-product-nightly.sh', 'daily']))
    audit = subprocess.run(['dotnet', 'package', 'list', '--project', proposal['solution'], '--vulnerable',
                            '--include-transitive', '--format', 'json', '--no-restore'],
                           cwd=root, capture_output=True, text=True, timeout=180)
    audit_json = json.loads(audit.stdout)
    findings = [package for project in audit_json.get('projects', []) for framework in project.get('frameworks', [])
                for group in ('topLevelPackages', 'transitivePackages') for package in framework.get(group, [])
                if package.get('vulnerabilities')]
    record['nugetAudit'] = {'exit': audit.returncode, 'findings': len(findings),
                            'errors': bool(audit_json.get('errors') or audit_json.get('error'))}
    if audit.returncode or findings or record['nugetAudit']['errors'] or not audit_json.get('projects'):
        raise ValueError('NuGet audit did not pass')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD'], cwd=root, capture_output=True, check=True)
    record['status'] = 'passed'
except BaseException as error:
    record.update(status='failed', exceptionType=type(error).__name__)
    # Raw exceptions/topology output are private scratch. Support-safe product
    # JSON and failure phase are the retained diagnostics.
finally:
    record['finishedAt'] = time.time()
    record['elapsedSeconds'] = record['finishedAt'] - record['startedAt']
    save()
    print('[S23] WORKER ' + record['status'].upper(), flush=True)
sys.exit(0 if record['status'] == 'passed' else 1)
