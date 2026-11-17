"""Run one disposable Docker-isolated product workload, never the host backend.

Invoke with run-with-temp. Raw logs/credentials remain scratch. Full mode
qualifies released routines locally; no delivered baseline or hosted result is created.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
SOURCE = Path('/home/administrator/projects/hexalith/tenants-story-23-current')
OBJECTS = Path('/home/administrator/projects/hexalith/tenants/references')
SCRATCH = Path(os.environ['TMPDIR']).resolve(strict=True)
if (SCRATCH.parent != Path('/tmp') or not SCRATCH.name.startswith('hexalith-job.')
        or SCRATCH.stat().st_uid != os.getuid() or stat.S_IMODE(SCRATCH.stat().st_mode) != 0o700):
    raise ValueError('Use the current private run-with-temp workspace')
REVISION = 'd25495a753fd02ce2ddac129809c6d3107ec6c6d'
TREE = 'cbca49fae5f1107b2e8c27886f66c7a9794f3939'
PRODUCT_BASE = 'ac7b6ba9edd88c197701fa1d1503cf2743ee022a'
BUILDS = 'a1e0c310b1f1a50d78e6132890fae6bcba769f6d'
SDK = 'mcr.microsoft.com/dotnet/sdk@sha256:65f3c7c6a25a239ab3e6719f2896147e7b68242ff2d8818dd70498bde6ef8bea'
DIND = 'docker.io/library/docker@sha256:9d337aaf171682751be04d67c15d880d6a95c6fd44cb8e12043f605012e5e654'
NONCE = uuid.uuid4().hex
MODE = os.environ.get('S23_MODE', 'full')
if MODE not in ('full', 'unit-ui', 'prerequisites', 'cold-integration', 'cold-rest', 'tool-tests', 'unit-hook'):
    raise ValueError('Unsupported local workload scope')
CONTAINER_ROOT = Path('/work/s23')
PACKET = HERE / ('local-isolated-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + NONCE[:8])
PACKET.mkdir(mode=0o700)
record = {'schema': 'tenants.local-isolated-job.v1', 'nonce': NONCE, 'source': REVISION,
          'tree': TREE, 'productBase': PRODUCT_BASE, 'sharedSource': BUILDS, 'sdkImage': SDK, 'daemonImage': DIND,
          'sharedPublicationReceipt': 'shared-v610-publication-verification.json',
          'deliveredBaselineVerified': False, 'hostedCi': False, 'scheduledNightly': False,
          'remoteRepositoryMutations': False, 'containers': [], 'startedAt': time.time(),
          'events': [], 'cleanup': [], 'privateScratchPath': str(SCRATCH), 'scope': MODE,
          'containerScratchPath': str(CONTAINER_ROOT),
          'limits': {'workerCpus': 4, 'workerMemory': '24g', 'daemonCpus': 2, 'daemonMemory': '8g'}}
active_process = None


def save():
    target = PACKET / 'result.json'
    target.write_text(json.dumps(record, indent=2) + '\n')
    target.chmod(0o600)


def note(value):
    record['events'].append({'at': time.time(), 'message': value})
    save()
    print('[S23-isolated] ' + value, flush=True)


def command(arguments, *, timeout=120, check=True):
    process = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
    if check and process.returncode:
        # No raw Docker/SUT output is copied into a public exception.
        raise RuntimeError('Command failed: ' + arguments[0] + '/' + str(process.returncode))
    return process


def git(repository, *arguments):
    return command(['git', '-C', str(repository), *arguments]).stdout.strip()


def project(repository, destination, revision):
    command(['git', 'clone', '--quiet', '--local', '--no-hardlinks', '--no-recurse-submodules',
             '--no-checkout', str(repository), str(destination)], timeout=600)
    command(['git', '-C', str(destination), 'checkout', '--quiet', '--detach', revision])
    alternate = destination / '.git/objects/info/alternates'
    if alternate.exists():
        command(['git', '-C', str(destination), 'repack', '-a', '-d'], timeout=600)
        alternate.unlink()
    if git(destination, 'rev-parse', 'HEAD') != revision:
        raise ValueError('Source projection identity differs')
    # Pure local verification cannot publish back to a host repository.
    command(['git', '-C', str(destination), 'config', 'remote.origin.pushurl', 'no-push://local-qualification'])


def host_backend():
    process = command(['docker', 'inspect', '--format',
                       '{{json .Id}} {{json .Created}} {{json .State.StartedAt}} {{json .State.Running}}',
                       'dapr_redis'], check=False)
    return {'exit': process.returncode, 'metadata': process.stdout.strip() if not process.returncode else None}


DCP_PROBE = r'''import hashlib,json,os
from pathlib import Path
found=[]
for process in Path('/proc').glob('[0-9]*'):
    try:
        name=(process/'comm').read_text().strip()
        if name not in ('dcp','dcpctrl'):
            continue
        executable=(process/'exe').resolve(strict=True)
        found.append((name!='dcp',int(process.name),name,executable,process/'exe'))
    except (OSError,ValueError):
        continue
rows=[]
for _,pid,name,executable,handle in sorted(found)[:1]:
    with handle.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    # Observe the running binary without executing a second native DCP process.
    # This exact hash was queried successfully in the earlier retained packet.
    known=digest=='1fb8f6c741b89fe39f73f491f5b06729dd187515bbfe37cf46d7bdefd7bd67f8'
    relative=str(executable)
    prefix='/work/s23/home/.nuget/packages/'
    rows.append({'processName':name,'pid':pid,'binarySha256':digest,
        'packagePath':relative.removeprefix(prefix) if relative.startswith(prefix) else executable.name,
        'versions':['0.26.6'] if known else [],'versionCommandExecuted':False,
        'versionSource':'prior-native-query-matching-binary-sha256' if known else 'unknown',
        'priorVersionReceipt':'local-isolated-20261117T003405Z-a33aa406/result.json' if known else None})
print(json.dumps(rows))
'''


def observe_dcp(worker):
    if record.get('executedDcp') or record.get('dcpObservationError') or worker is None:
        return
    try:
        probe=command(['docker','exec','--user','1000:1000',
            '--env','HOME=/work/s23/home','--env','TMPDIR=/work/s23/runner',
            '--env','TMP=/work/s23/runner','--env','TEMP=/work/s23/runner',
            worker,'python3','-B','-c',DCP_PROBE],timeout=15,check=False)
        if probe.returncode==0:
            rows=json.loads(probe.stdout)
            if rows:
                record['executedDcp']=rows
                save()
    except (OSError,ValueError,subprocess.TimeoutExpired) as error:
        # Optional metadata must never interrupt the product's complete tests.
        record['dcpObservationError']=type(error).__name__
        save()


def register_container(kind, cidfile, *, lookup=False):
    identifier = cidfile.read_text().strip() if cidfile.is_file() else ''
    if lookup and re.fullmatch(r'[0-9a-f]{64}', identifier) is None:
        name = 'tenants-s23-' + ('dind' if kind == 'daemon' else 'worker') + '-' + NONCE[:12]
        inspected = command(['docker', 'container', 'inspect', '--format',
                             '{"id":{{json .Id}},"labels":{{json .Config.Labels}}}', name], check=False)
        if inspected.returncode:
            if re.search(r'No such (?:object|container)', inspected.stderr, re.IGNORECASE):
                return None
            raise RuntimeError('Task container identity read refused')
        data = json.loads(inspected.stdout)
        if (data.get('labels') or {}).get('hexalith.local-qualification') != NONCE:
            raise ValueError('Task container lookup ownership differs')
        identifier = data['id']
    if not identifier:
        return None
    if re.fullmatch(r'[0-9a-f]{64}', identifier) is None:
        raise ValueError('Task container identity is malformed')
    row = {'kind': kind, 'id': identifier}
    if row not in record['containers']:
        record['containers'].append(row)
        save()
    return identifier


def remove_container(row):
    inspected = command(['docker', 'container', 'inspect', '--format', '{{json .Config.Labels}}', row['id']], check=False)
    if inspected.returncode:
        if re.search(r'No such (?:object|container)', inspected.stderr, re.IGNORECASE):
            record['cleanup'].append({'container': row, 'state': 'already-removed'})
            return
        raise RuntimeError('Task container removal remains unverified')
    labels = json.loads(inspected.stdout)
    if labels.get('hexalith.local-qualification') != NONCE:
        raise ValueError('Task container label changed; removal refused')
    command(['docker', 'rm', '--force', '--volumes', row['id']], timeout=90)
    record['cleanup'].append({'container': row, 'state': 'removed'})


def safe_results(raw):
    masks = {line.partition('::add-mask::')[2].strip() for line in raw.splitlines() if '::add-mask::' in line}
    masks.discard('')
    record['maskValuesDiscarded'] = len(masks)
    clean = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', raw)
    record['toolSuiteCounters'] = {
        'python': re.findall(r'^Ran (\d+) tests? in ([0-9.]+)s$', clean, re.MULTILINE),
        'node': re.findall(r'^(?:#|ℹ️?) (?:tests|pass|fail|skipped) \d+$', clean, re.MULTILINE),
        'pythonFailures': re.findall(r'^FAILED \([a-z0-9=, ]+\)$', clean, re.MULTILINE)}

    def scrub(value):
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items()}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, str):
            for secret in masks:
                value = value.replace(secret, '[redacted]')
            return re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '[redacted-token]', value)
        return value

    # Keep counters and fixed phase markers, never raw topology/exception logs.
    selected = []
    for line in re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', raw).splitlines():
        text = line.strip()
        if (text.startswith('[S23] ') or text in ('Build succeeded.', 'Build FAILED.', 'Test run summary: Passed!')
                or re.fullmatch(r'(?:total|failed|succeeded|skipped|duration): [0-9A-Za-z .:]+', text)
                or re.fullmatch(r'E: [A-Za-z0-9 .:+/()_-]+', text)
                or re.fullmatch(r'- (?:Overall line coverage \(publishable packages\)|Isolation/auth branch coverage): [0-9.% /()]+', text)):
            selected.append(scrub(text))
    (PACKET / 'progress.log').write_text('\n'.join(selected) + '\n')
    result = SCRATCH / 'worker-result.json'
    if result.is_file() and not result.is_symlink():
        record['worker'] = scrub(json.loads(result.read_text()))
    failed = [row['name'] for row in record.get('worker', {}).get('phases', []) if row['status'] == 'failed']
    if failed and failed[-1] in ('after-unit-tests-hook', 'focused-product-script-tools'):
        # These stages run before the native owner profiles and have no mounted
        # publishing credentials. Retain bounded failure context, still redacting
        # masks, PEM material, credential assignments and long opaque values.
        section = raw.rsplit('[S23] START ' + failed[-1], 1)[-1]
        record['toolFailureHeaders'] = re.findall(
            r'^(?:FAIL|ERROR): ([A-Za-z_][A-Za-z0-9_]*) \(([A-Za-z0-9_.]+)\)', section, re.MULTILINE)
        diagnostic = scrub('\n'.join(section.splitlines()[-240:]))
        diagnostic = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', diagnostic)
        diagnostic = re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----',
                            '[redacted-private-key]', diagnostic, flags=re.DOTALL)
        diagnostic = re.sub(r'(?im)\b(password|token|secret|api[_-]?key)\s*[:=]\s*[^\n,}]+',
                            r'\1=[redacted]', diagnostic)
        diagnostic = re.sub(r'[A-Za-z0-9+/=_-]{24,}', '[redacted-opaque]', diagnostic)
        target = PACKET / 'tool-failure-redacted.log'
        target.write_text(diagnostic[-24000:] + '\n')
        target.chmod(0o600)
        record['toolFailureDiagnostic'] = target.name
    outputs = []
    runtime = SCRATCH / 'runner'
    patterns = ('hexalith-dapr-initialization.json', 'tenants-product-profiles/*.json',
                'tenants-bootstrap-diagnostics/*.json', 'tenants-dapr-*.json', 'tenants-product-catalog-consumer.json')
    destination = PACKET / 'support-safe'
    destination.mkdir(mode=0o700, exist_ok=True)
    for pattern in patterns:
        for path in sorted(runtime.glob(pattern)):
            if path.is_file() and not path.is_symlink() and path.stat().st_size <= 4 * 1024 * 1024:
                data = scrub(json.loads(path.read_text()))
                name = path.parent.name + '-' + path.name
                target = destination / name
                target.write_text(json.dumps(data, indent=2) + '\n')
                target.chmod(0o600)
                outputs.append(name)
    record['supportSafeArtifacts'] = outputs
    summaries = []
    for path in (SCRATCH / 'Hexalith.Tenants/TestResults').rglob('*.trx'):
        if path.is_symlink():
            continue
        document = ET.parse(path)
        counters = document.find('.//{*}Counters')
        failures = []
        for item in document.findall('.//{*}UnitTestResult'):
            if item.get('outcome') == 'Passed':
                continue
            message = item.findtext('.//{*}Message', default='')
            stack = item.findtext('.//{*}StackTrace', default='')
            error_type = re.match(r'\s*([A-Za-z0-9_.]+(?:Exception|Error))\b', message)
            failures.append({'method': item.get('testName', '').partition('(')[0][:300],
                             'outcome': item.get('outcome'),
                             'errorType': error_type[1] if error_type else None,
                             'messageSha256': hashlib.sha256(message.encode()).hexdigest(),
                             'testFrames': scrub([line.strip() for line in stack.splitlines()
                                                  if 'Hexalith.Tenants.' in line and ('.cs:line' in line or line.strip().startswith('at '))])})
            relative_report = path.relative_to(SCRATCH / 'Hexalith.Tenants/TestResults').as_posix()
            if MODE == 'unit-ui' or MODE == 'full' and relative_report.startswith('shared-ci/unit-'):
                # Unit reports are produced before any cold owner material.
                # Strip token/PEM/opaque key-like values while retaining numeric
                # assertions and static UI markup needed to explain a failure.
                summary = scrub(message)
                summary = re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----',
                                 '[redacted-private-key]', summary, flags=re.DOTALL)
                summary = re.sub(r'[A-Za-z0-9+/=_-]{24,}', '[redacted-opaque]', summary)
                failures[-1]['unitMessageSummary'] = summary[:4000]
        summaries.append({'path': str(path.relative_to(SCRATCH)),
                          'counters': dict(counters.attrib) if counters is not None else None,
                          'nonpassingMethods': scrub(failures)})
    record['trxSummaries'] = summaries


def terminate(signum, frame):
    raise InterruptedError('Local qualification interrupted')


for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, terminate)

daemon_cid = SCRATCH / 'daemon.cid'
worker_cid = SCRATCH / 'worker.cid'
raw_path = SCRATCH / 'worker-private.log'
try:
    assert git(SOURCE, 'rev-parse', 'HEAD') == REVISION
    assert git(SOURCE, 'rev-parse', 'HEAD^{tree}') == TREE
    assert not git(SOURCE, 'status', '--porcelain')
    command(['git', '-C', str(SOURCE), 'merge-base', '--is-ancestor', PRODUCT_BASE, REVISION])
    record['hostBackendBefore'] = host_backend()
    record['outerDaemonId'] = command(['docker', 'info', '--format', '{{json .ID}}']).stdout.strip()
    project(SOURCE, SCRATCH / 'Hexalith.Tenants', REVISION)
    record['directPins'] = {}
    for module in ('Builds', 'EventStore', 'Platform', 'Memories'):
        name = 'Hexalith.' + module
        pin = git(SOURCE, 'rev-parse', 'HEAD:references/' + name)
        record['directPins'][name] = pin
        project(OBJECTS / name, SCRATCH / 'Hexalith.Tenants/references' / name, pin)
    project(HERE.parents[4] / 'references/Hexalith.Builds', SCRATCH / 'shared-builds', BUILDS)
    shutil.copyfile(HERE / 'product-routing-proposal.json', SCRATCH / 'proposal.json')
    shutil.copyfile(HERE / 'run-isolated-product-worker.py', SCRATCH / 'worker.py')
    record['workerSha256'] = hashlib.sha256((SCRATCH / 'worker.py').read_bytes()).hexdigest()
    record['orchestratorSha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    shutil.copyfile(Path(__file__), PACKET / 'run-isolated-product.py')
    shutil.copyfile(SCRATCH / 'worker.py', PACKET / 'run-isolated-product-worker.py')
    note('Exact source projections ready; no nested submodules initialized')
    command(['docker', 'pull', DIND], timeout=600)
    note('Exact official DinD image available')
    socket = SCRATCH / 'daemon-socket'
    socket.mkdir(mode=0o700)
    name = 'tenants-s23-dind-' + NONCE[:12]
    started = command(['docker', 'run', '--detach', '--privileged', '--name', name,
                       '--cpus', '2', '--memory', '8g',
                       '--cidfile', str(daemon_cid), '--label', 'hexalith.story=23',
                       '--label', 'hexalith.local-qualification=' + NONCE,
                       '--env', 'DOCKER_TLS_CERTDIR=', '--mount', f'type=bind,src={SCRATCH},dst={CONTAINER_ROOT}',
                       DIND, 'dockerd', '--host=unix://' + str(CONTAINER_ROOT / 'daemon-socket/docker.sock'),
                       '--data-root=' + str(CONTAINER_ROOT / 'daemon-data'), '--storage-driver=vfs'], timeout=90, check=False)
    identifier = register_container('daemon', daemon_cid)
    if started.returncode or identifier is None:
        raise RuntimeError('Private daemon did not start')
    inner = ['docker', 'exec', identifier, 'docker', '--host=unix://' + str(CONTAINER_ROOT / 'daemon-socket/docker.sock')]
    deadline = time.monotonic() + 90
    while True:
        response = command([*inner, 'info', '--format', '{{json .ID}}'], timeout=10, check=False)
        if not response.returncode:
            break
        record['lastDaemonReadiness'] = {'exit': response.returncode, 'stderr': response.stderr[:2000]}
        state = command(['docker', 'container', 'inspect', '--format',
                         '{"running":{{json .State.Running}},"exit":{{.State.ExitCode}},"oom":{{json .State.OOMKilled}},"error":{{json .State.Error}}}',
                         identifier], check=False)
        if not state.returncode:
            record['daemonStartupState'] = json.loads(state.stdout)
            if not record['daemonStartupState']['running']:
                logs = command(['docker', 'logs', '--tail', '100', identifier], check=False)
                # The SDK worker has not started and no owner material exists.
                diagnostic = logs.stdout + logs.stderr
                diagnostic = re.sub(r'(https?://)[^/@\s]+@', r'\1[redacted]@', diagnostic)
                (PACKET / 'daemon-startup.log').write_text(diagnostic)
                raise RuntimeError('Private daemon exited before workload startup')
        if time.monotonic() >= deadline:
            raise TimeoutError('Private daemon readiness deadline')
        time.sleep(1)
    record['innerDaemonId'] = response.stdout.strip()
    if record['innerDaemonId'] == record['outerDaemonId']:
        raise ValueError('Daemon isolation failed')
    if command([*inner, 'ps', '--all', '--quiet']).stdout.strip() or command([*inner, 'volume', 'ls', '--quiet']).stdout.strip():
        raise ValueError('Private daemon was not initially empty')
    note('Fresh private daemon ready with no preexisting containers or volumes')
    bootstrap = '''set -euo pipefail
if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then
  sed -i -e 's|http://archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g' -e 's|http://security.ubuntu.com/ubuntu|https://security.ubuntu.com/ubuntu|g' /etc/apt/sources.list.d/ubuntu.sources
fi
apt-get -o Acquire::Retries=2 -o Acquire::http::Timeout=45 update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-yaml sudo jq procps unzip
exec python3 -B "$1"
'''
    run_id = str(time.time_ns())
    arguments = ['docker', 'run', '--rm', '--init', '--name', 'tenants-s23-worker-' + NONCE[:12],
                 '--cpus', '4', '--memory', '24g', '--pids-limit', '4096',
                 '--cidfile', str(worker_cid), '--network', 'container:' + identifier,
                 '--label', 'hexalith.story=23', '--label', 'hexalith.local-qualification=' + NONCE,
                 '--mount', f'type=bind,src={SCRATCH},dst={CONTAINER_ROOT}',
                 '--mount', 'type=bind,src=/usr/bin/docker,dst=/usr/local/bin/docker,readonly',
                 '--workdir', str(CONTAINER_ROOT / 'Hexalith.Tenants')]
    environment = {'S23_SCRATCH': str(CONTAINER_ROOT), 'S23_BUILDS_REVISION': BUILDS, 'S23_MODE': MODE,
                   'S23_PRODUCT_BASE': PRODUCT_BASE,
                   'DOCKER_HOST': 'unix://' + str(CONTAINER_ROOT / 'daemon-socket/docker.sock'),
                   'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'Hexalith/Hexalith.Tenants',
                   'GITHUB_RUN_ID': run_id, 'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_JOB': 'local_s23_qualification',
                   'GITHUB_SHA': REVISION}
    for key, value in environment.items():
        arguments.extend(('--env', key + '=' + value))
    arguments.extend((SDK, 'bash', '-c', bootstrap, 'tenants-local-bootstrap', str(CONTAINER_ROOT / 'worker.py')))
    descriptor = os.open(raw_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as raw:
        active_process = subprocess.Popen(arguments, stdout=raw, stderr=subprocess.STDOUT)
        started_at = time.monotonic()
        last_phase = None
        while active_process.poll() is None:
            worker_identifier = register_container('worker', worker_cid)
            result = SCRATCH / 'worker-result.json'
            if result.is_file():
                status = json.loads(result.read_text())
                if status['phases']:
                    current = (status['phases'][-1]['name'], status['phases'][-1]['status'])
                    if current != last_phase:
                        note('Worker phase: ' + '/'.join(current))
                        last_phase = current
                    if current[0] in ('selected-cold-rest-profile', 'complete-hook-owned-integration-project', 'after-integration-step-2') and current[1] == 'running':
                        observe_dcp(worker_identifier)
            if time.monotonic() - started_at > 21600:
                raise TimeoutError('Local workload exceeded the provisional 360-minute bound')
            time.sleep(2)
        record['workerContainerExit'] = active_process.returncode
        active_process = None
    safe_results(raw_path.read_text(errors='replace'))
    record['status'] = 'passed' if record.get('worker', {}).get('status') == 'passed' and not record['workerContainerExit'] else 'failed'
except BaseException as error:
    record.update(status='failed', exceptionType=type(error).__name__)
    if raw_path.is_file():
        try:
            safe_results(raw_path.read_text(errors='replace'))
        except Exception as collector_error:
            record['collectorError'] = type(collector_error).__name__
finally:
    if active_process is not None:
        active_process.terminate()
        try:
            active_process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            active_process.kill()
            active_process.wait()
    for kind, path in (('worker', worker_cid), ('daemon', daemon_cid)):
        try:
            register_container(kind, path, lookup=True)
        except Exception as identity_error:
            record['cleanup'].append({'kind': kind, 'state': 'identity-unverified', 'error': type(identity_error).__name__})
            record['status'] = 'failed'
    for row in sorted(record['containers'], key=lambda item: item['kind'] == 'daemon'):
        try:
            remove_container(row)
        except Exception as cleanup_error:
            record['cleanup'].append({'container': row, 'state': 'failed', 'error': type(cleanup_error).__name__})
            record['status'] = 'failed'
    try:
        record['hostBackendAfter'] = host_backend()
        record['hostBackendUnchanged'] = record.get('hostBackendBefore') == record['hostBackendAfter']
        record['sourceStillExact'] = git(SOURCE, 'rev-parse', 'HEAD') == REVISION and not git(SOURCE, 'status', '--porcelain')
        if not record['hostBackendUnchanged'] or not record['sourceStillExact']:
            raise ValueError('Final host backend or source preservation check failed')
    except Exception as verification_error:
        record['finalVerificationError'] = type(verification_error).__name__
        record['status'] = 'failed'
    record['finishedAt'] = time.time()
    record['elapsedSeconds'] = record['finishedAt'] - record['startedAt']
    record['releasedRoutineBootstrapQualified'] = (MODE == 'full' and record['status'] == 'passed'
        and record.get('worker', {}).get('releasedRoutineBootstrapQualified') is True)
    save()
    # Docker's private data files can be root-owned. Restrict cleanup to this
    # wrapper's canonical scratch tree; never follow links out of it.
    try:
        command(['sudo', '-n', 'chown', '-R', '-P', '--no-dereference',
                 str(os.getuid()) + ':' + str(os.getgid()), str(SCRATCH)], timeout=120)
        record['scratchCleanupOwnership'] = 'restored to wrapper user'
    except Exception as ownership_error:
        record['scratchCleanupOwnership'] = type(ownership_error).__name__
        record['status'] = 'failed'
        record['releasedRoutineBootstrapQualified'] = False
    save()
    print(json.dumps({'packet': str(PACKET), 'scope': MODE, 'status': record['status'],
                      'worker': record.get('worker', {}).get('status'),
                      'hostBackendUnchanged': record.get('hostBackendUnchanged'),
                      'sourceStillExact': record.get('sourceStillExact')}, indent=2), flush=True)
raise SystemExit(0 if record['status'] == 'passed' else 1)
