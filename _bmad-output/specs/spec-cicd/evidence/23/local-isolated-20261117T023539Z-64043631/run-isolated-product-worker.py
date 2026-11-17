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
          'productBase': os.environ['S23_PRODUCT_BASE'],
          'scope': os.environ.get('S23_MODE', 'full'),
          'localSyntheticIdentity': True, 'hostedCi': False, 'scheduledNightly': False,
          'deliveredBaselineVerified': False, 'deliveredConfigurationCreated': False,
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
        if record['scope'] == 'prerequisites':
            row['prerequisiteError'] = str(error)[:3000]
            if name == 'shared-tls-trust':
                diagnostic = subprocess.run(['dotnet', 'dev-certs', 'https', '--trust', '--verbose'],
                    cwd=root, capture_output=True, text=True, timeout=60)
                # This invocation only trusts a job-local certificate; it has no
                # export/key/password arguments and no publishing credentials.
                row['publicTrustDiagnostic'] = {
                    'exit': diagnostic.returncode,
                    'lines': (diagnostic.stdout + diagnostic.stderr).splitlines()[-100:]}
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


def released_product_policy():
    import shutil
    import guard_actions
    import guard_tools
    import perimeter
    directory = runtime / 'released-guard-tools'
    directory.mkdir(mode=0o700)
    tools = guard_tools.Tools(directory)
    snapshot = perimeter.Git(root).snapshot(record['source'])
    guard_actions.lint(snapshot, tools)
    tools.lint_message('build: migrate Tenants product checks\n', 'prospective product commit')
    module_config = directory / 'module-commitlint.config.mjs'
    shutil.copyfile(root / 'commitlint.config.mjs', module_config)
    revisions = subprocess.check_output(['git', 'rev-list',
        record['productBase']+'..HEAD'], cwd=root, text=True).splitlines()
    for revision in revisions:
        commit = subprocess.check_output(['git', 'cat-file', 'commit', revision], cwd=root)
        message = commit.split(b'\n\n', 1)[1].decode('utf-8')
        tools.lint_message(message, 'actual product commit')
        tools._run(['node', str(directory / 'node_modules/@commitlint/cli/cli.js'),
            '--config', str(module_config), '--color=false'], 'owning module commitlint', message)
    if not revisions:
        raise ValueError('No actual product commit policy scope was verified')
    version = json.loads((directory / 'node_modules/@commitlint/cli/package.json').read_text())['version']
    record['releasedPolicy'] = {'customActions':'passed', 'actualCommitMessages':revisions,
        'commitlintVersion':version, 'centralPolicy':'passed', 'modulePolicy':'passed',
        'lockedInstallAndSignatures':'passed'}
    save()


def selected_rest_profile():
    import importlib.util
    spec = importlib.util.spec_from_file_location('local_product_integration', root / 'scripts/run-product-integration.py')
    integration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(integration)
    temporary = Path(os.environ['RUNNER_TEMP']).resolve(strict=True)
    output = temporary / 'tenants-product-profiles'
    output.mkdir(mode=0o700)
    source = integration.PROFILE.command('git', 'rev-parse', 'HEAD:references/Hexalith.EventStore')
    producer = integration.PROFILE.command('dotnet', 'msbuild', 'src/Hexalith.Tenants/Hexalith.Tenants.csproj', '-nologo',
        '-getProperty:HexalithEventStoreVersion', '-p:Configuration=Release', '-p:UseHexalithProjectReferences=false',
        '-p:UseNuGetDeps=true', '-p:HexalithEventStoreFromSource=false')
    if producer != '5.1.1' or integration.PROFILES[0][0] != 'rest':
        raise ValueError('The selected actual product REST profile differs')
    original_finish = integration.PROFILE.finish
    def capture_refusal(path, temporary, error):
        reasons = {
            'Private topology consumers did not exit before the shutdown deadline.': 'native-exit-deadline',
            'The active catalog profile identity changed.': 'active-profile-identity',
            'The topology did not complete its awaited shutdown.': 'shutdown-proof',
            'The private component set changed during qualification.': 'component-set-changed',
            'The previous profile still has running component consumers.': 'private-process-survivors',
            'The previous profile still has private-custody container resources.': 'private-container-survivors',
            'Catalog receipts require private current-user custody.': 'receipt-custody',
            'Catalog cleanup requires private current-user directory custody.': 'directory-custody',
        }
        diagnostic = {'exceptionType': type(error).__name__,
            'refusal': reasons.get(str(error), 'unclassified-refusal')}
        try:
            from collections import Counter
            receipt = integration.PROFILE.document(path, temporary)
            private = integration.PROFILE.private_directory(receipt['privateDirectory'], temporary)
            processes = integration.PROFILE.active_processes(private)
            names = Counter()
            known = {'dotnet','MSBuild','VBCSCompiler','dcp','dcpctrl','daprd','sentry','node','bash','sh','python3'}
            facts = []
            for pid in processes:
                try:
                    proc = Path('/proc/' + str(pid))
                    name = (proc / 'comm').read_text().strip()
                    names[name if name in known else 'other'] += 1
                    status = dict(line.split(':', 1) for line in (proc / 'status').read_text().splitlines() if ':' in line)
                    arguments = (proc / 'cmdline').read_bytes()
                    environment = (proc / 'environ').read_bytes()
                    executable = proc / 'exe'
                    with executable.open('rb') as stream:
                        executable_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
                    facts.append({'pid':pid,'parentPid':int(status['PPid'].strip()),
                        'state':status['State'].strip().split()[0],
                        'name':name if name in known else 'other',
                        'nameSha256':hashlib.sha256(name.encode()).hexdigest(),
                        'executableSha256':executable_hash,
                        'privateCommandMatch':os.fsencode(private) in arguments,
                        'privateTemporaryEnvironmentMatch':b'TMPDIR='+os.fsencode(private)+b'\0' in environment,
                        'commandKind':next((value for value in ('version','--version','start','run')
                            if value.encode() in arguments.split(b'\0')[1:]),'other')})
                except OSError:
                    names['already-exited'] += 1
            diagnostic.update(privateProcessCount=len(processes), processKinds=dict(names),
                privateContainerCount=len(integration.PROFILE.private_containers(private)),
                shutdownFilePresent=(private / 'shutdown.json').is_file(),
                changedComponentCount=sum(integration.PROFILE.digest(private / 'components' / name) != digest
                    for name, digest in receipt['components'].items()))
            diagnostic['processFacts'] = facts
        except Exception as observation_error:
            diagnostic['observationError'] = type(observation_error).__name__
        record['cleanupRefusalDiagnostic'] = diagnostic
        save()

    def observed_finish(path, temporary, identity):
        try:
            return original_finish(path, temporary, identity)
        except BaseException as error:
            capture_refusal(path, temporary, error)
            raise
    original_wait = integration.wait_for_private_consumers
    def observed_wait(private):
        started = time.monotonic()
        completed = False
        try:
            result = original_wait(private)
            completed = True
            return result
        except BaseException as error:
            capture_refusal(output / 'rest.json', temporary, error)
            raise
        finally:
            record['naturalExitWait'] = {'elapsedSeconds':time.monotonic()-started,
                'completed':completed, 'forcedTermination':False}
            save()
    integration.wait_for_private_consumers = observed_wait
    integration.PROFILE.finish = observed_finish
    try:
        integration.run_profile(*integration.PROFILES[0], temporary=temporary, output=output, producer=producer, source=source)
    finally:
        integration.PROFILE.finish = original_finish
        integration.wait_for_private_consumers = original_wait


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
    if record['scope'] == 'full':
        import ci_config
        if record['sharedSource'] != 'a1e0c310b1f1a50d78e6132890fae6bcba769f6d':
            raise ValueError('Exact verified published v6.1.0 contract is required')
        document = {**proposal, 'schema':ci_config.schema_identity(), 'buildsTag':'v6.1.0',
            'codeql':['csharp'], 'jobs':{}, 'dotnetTools':False,
            'tests':{**proposal['tests'], 'minimumExpectedTests':minima, 'reports':{'trx':True}}}
        ci_config.validate_config(document, repository='Hexalith/Hexalith.Tenants')
        prepared = ci_pipeline.PreparedConfig(root, root, document, proposal['solution'], 'global.json', ())
        record['releasedContract'] = {'tag':'v6.1.0', 'revision':record['sharedSource'],
            'inMemoryTestRoutingOnly':document, 'deliveredStateFabricated':False,
            'publicationReceipt':'shared-v610-publication-verification.json'}
        phase('released-custom-actions-and-actual-commit-policy', released_product_policy)
    if record['scope'] == 'prerequisites':
        phase('exact-prerequisite-runtime-check', lambda: ci_environment.require_node_versions(
            root, proposal['prerequisites'], npm_required=True))
        phase('shared-apt-preparation', lambda: ci_environment.setup_apt(root))
        phase('shared-tls-trust', lambda: ci_environment.setup_tls_trust(root))
        record['status'] = 'passed'
    elif record['scope'] in ('cold-integration', 'cold-rest'):
        record['diagnosticOmittedStages'] = ['shared-unit-projects', 'after-unit-tests-hook',
            'shared-integration-projects', 'coverage-gate', 'Dapr-retry-controls', 'nightly-workload']
        phase('one-release-package-build', lambda: ci_pipeline.restore_and_build(prepared))
        phase('one-shared-environment', lambda: ci_environment.setup_environment(
            root, solution=proposal['solution'], dapr=proposal['dapr'], browsers=proposal['browsers'],
            registry=proposal['registry'], npm_workspaces=proposal['npmWorkspaces'],
            prerequisites=proposal['prerequisites']))
        if record['scope'] == 'cold-rest':
            record['diagnosticOmittedStages'].extend(['ordinary-integration-tier', 'other-four-cold-profiles'])
            phase('selected-cold-rest-profile', selected_rest_profile)
        else:
            phase('complete-hook-owned-integration-project', lambda: run(['python3', 'scripts/run-product-integration.py'], 14400))
        record['status'] = 'passed'
    else:
        phase('one-release-package-build', lambda: ci_pipeline.restore_and_build(prepared))
        discovered = ci_pipeline.discover_test_projects(root, proposal['solution'])
        if set(discovered) != {*units, *integrations, owned}:
            raise ValueError('Complete project inventory differs from the inspected test plan')
        record['testProjects'] = {'unit': units, 'integration': integrations, 'hookOwned': owned}
        runner = ci_pipeline.test_runner(root)
        if record['scope'] == 'full':
            classified = phase('released-complete-unit-projects', lambda: ci_pipeline.run_unit_tests(
                prepared, repository='Hexalith/Hexalith.Tenants'))
            if (set(classified.unit) != set(units) or set(classified.integration) != set(integrations)
                    or set(classified.excluded) != {owned}):
                raise ValueError('Released test classification differs from the complete inspected inventory')
            record['releasedClassification'] = {name:list(getattr(classified,name))
                for name in ('unit','integration','excluded')}
            unit_state = ci_pipeline.stage_state(prepared, classified)
        else:
            selected_units = (units[-1],) if record['scope'] == 'unit-ui' else units
            phase('focused-ui-project' if record['scope'] == 'unit-ui' else 'complete-unit-projects',
                  lambda: ci_pipeline.execute_test_projects(
                      root, selected_units, runner=runner, stage='Unit', minimum_expected_tests=minima,
                      fail_skips=True, reports={'trx': True}))
        if record['scope'] == 'full':
            phase('one-shared-environment', lambda: ci_environment.setup_environment(
                root, solution=proposal['solution'], dapr=proposal['dapr'], browsers=proposal['browsers'],
                registry=proposal['registry'], npm_workspaces=proposal['npmWorkspaces'],
                prerequisites=proposal['prerequisites']))
            phase('after-unit-tests-hook', lambda: run(['bash', 'scripts/run-product-unit-checks.sh']))
            phase('released-complete-integration-projects', lambda: ci_pipeline.run_integration_tests(
                prepared, repository='Hexalith/Hexalith.Tenants', expected_state=unit_state))
            # Match the composite literally, including exact coverage/mutation controls.
            action = root / '.github/actions/after-integration-tests/action.yml'
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
    record['releasedRoutineBootstrapQualified'] = (record['scope'] == 'full' and record['status'] == 'passed')
    record['finishedAt'] = time.time()
    record['elapsedSeconds'] = record['finishedAt'] - record['startedAt']
    save()
    print('[S23] WORKER ' + record['status'].upper(), flush=True)
sys.exit(0 if record['status'] == 'passed' else 1)
