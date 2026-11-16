"""Run retained owning product assertions without historical workflow/evidence gates."""
from pathlib import Path
import json
import os
import platform
import re
import signal
import shutil
import socket
import subprocess
import sys
import uuid


def _windows_excluded_ports():
    """WSL sockets do not see exclusions on the Windows Docker Desktop host."""
    command = shutil.which('netsh.exe')
    if command is None and 'microsoft' in platform.release().lower():
        fallback = Path('/mnt/c/Windows/System32/netsh.exe')
        if fallback.is_file():
            command = str(fallback)
    if command is None:
        return ()
    result = subprocess.run([command, 'interface', 'ipv4', 'show', 'excludedportrange', 'protocol=tcp'],
                            check=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    ranges = []
    for line in result.stdout.splitlines():
        match = re.fullmatch(r'\s*(\d+)\s+(\d+)\s*\*?\s*', line)
        if match is None and re.match(r'\s*\d', line):
            raise ValueError('Unrecognized Windows host excluded-port row')
        if match:
            first, last = map(int, match.groups())
            if not 1 <= first <= last <= 65535:
                raise ValueError('Invalid Windows host excluded-port range')
            ranges.append((first, last))
    return tuple(ranges)


def _scheduler_host_port(*, allocate=None, attempts=64):
    excluded = _windows_excluded_ports()
    for _ in range(attempts):
        if allocate is None:
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                port = listener.getsockname()[1]
        else:
            port = allocate()
        if not 1 <= port <= 65535:
            raise ValueError('Invalid scheduler host port')
        if not any(first <= port <= last for first, last in excluded):
            return port
    raise RuntimeError('No eligible scheduler host port within the bounded allocation attempts')


def _start_scheduler(create, discard, *, allocate=None, attempts=3):
    """Retry only host-port publication failures; never retry image/auth/runtime errors."""
    allocate = allocate or _scheduler_host_port
    for attempt in range(1, attempts + 1):
        port = allocate()
        try:
            name, published = create(port, attempt)
        except subprocess.CalledProcessError as error:
            diagnostic = error.stderr or ''
            if isinstance(diagnostic, bytes):
                diagnostic = diagnostic.decode('utf-8', errors='replace')
            publication_errors = ('ports are not available', 'port is already allocated', 'bind: address already in use')
            if error.returncode != 125 or not any(message in diagnostic.lower() for message in publication_errors):
                raise
            discard()
            if attempt == attempts:
                raise
        else:
            if published != port:
                raise ValueError('Scheduler advertised port differs from its Docker publication')
            return name, published
    raise ValueError('Scheduler publication requires at least one attempt')


def _remove_owned_container(identity, namespace, *, removed=None):
    removed = removed if removed is not None else set()
    if identity not in removed:
        labels = json.loads(subprocess.check_output(
            ['docker', 'inspect', '--format', '{{json .Config.Labels}}', identity], text=True, timeout=30))
        if labels.get('hexalith.story18-g6') != namespace:
            raise ValueError('Exact owning qualifier cleanup custody changed')
        subprocess.run(['docker', 'rm', '--force', '--volumes', identity], check=True, timeout=60)
        removed.add(identity)
    remaining = subprocess.check_output(
        ['docker', 'container', 'ls', '--all', '--quiet', '--no-trunc', '--filter', 'id=' + identity],
        text=True, timeout=30)
    if remaining.strip():
        raise ValueError('Owning qualifier container removal could not be verified')
    return {'id': identity, 'removed': True}


def _record_container_custody(cidfile, name, namespace, owned):
    identity = cidfile.read_text().strip() if cidfile.exists() else ''
    if not re.fullmatch('[0-9a-f]{64}', identity):
        # A timed-out client may not have received the daemon's successful create response.
        candidates = subprocess.check_output(['docker', 'container', 'ls', '--all', '--quiet', '--no-trunc',
            '--filter', 'name=^/' + name + '$', '--filter', 'label=hexalith.story18-g6=' + namespace],
            text=True, timeout=30).split()
        if len(candidates) > 1 or any(not re.fullmatch('[0-9a-f]{64}', value) for value in candidates):
            raise ValueError('Ambiguous owning qualifier container custody')
        identity = candidates[0] if candidates else ''
    if identity and identity not in owned:
        owned.append(identity)
    return identity


def _cleanup_owned_containers(owned, namespace, removed, cleanup, report, *, pending=None):
    failures = []
    for name, cidfile in (pending or {}).items():
        try:
            if not _record_container_custody(cidfile, name, namespace, owned):
                raise ValueError('Uncertain container create custody remains unresolved')
        except Exception as error:
            cleanup.append({'name': name, 'namespace': namespace, 'removed': False,
                            'custody_unresolved': True, 'error_type': type(error).__name__})
            failures.append(error)
    for identity in reversed(owned):
        try:
            cleanup.append(_remove_owned_container(identity, namespace, removed=removed))
        except Exception as error:
            cleanup.append({'id': identity, 'removed': False, 'remove_command_succeeded': identity in removed,
                            'error_type': type(error).__name__})
            failures.append(error)
    report.write_text(json.dumps(cleanup, indent=2))
    if failures:
        raise ExceptionGroup('Owning qualifier control plane cleanup failed', failures)


def run(root, scratch):
    owner = root / 'references/Hexalith.EventStore'
    config = root / 'references/Hexalith.Builds/NuGet.ci.Config'
    flags = ['-noAutoResponse', '-p:Configuration=Release', '-warnaserror',
             '-p:UseHexalithProjectReferences=false', '-p:ShouldUnsetParentConfigurationAndPlatform=false',
             f'-p:RestoreConfigFile={config}', '-p:EnableNETAnalyzers=true', '-p:RunAnalyzers=true',
             '-p:RunAnalyzersDuringBuild=true', '-m:1']
    assemblies = {}
    for name in ('Hexalith.EventStore.Server.LiveSidecar.Tests', 'Hexalith.EventStore.Server.Tests'):
        project = owner / 'tests' / name / (name + '.csproj')
        subprocess.run(['dotnet', 'build', str(project), *flags], cwd=owner, check=True)
        assemblies[name] = next((project.parent / 'bin/Release').glob('*/' + name + '.dll'))
    historical = root / '_bmad-output/implementation-artifacts/qualification-evidence/g-6-runtime-toolchain-20261001/attempt-16/capture/deterministic-support.json'
    selectors = json.loads(historical.read_text())['selectors']
    if len(selectors) != 21 or len(set(selectors)) != 21:
        raise ValueError('Expected the exact retained 21 owning support methods')
    results = Path(__file__).resolve().parent
    support = scratch / 'owning-support-ctrf.json'
    command = ['dotnet', str(assemblies['Hexalith.EventStore.Server.Tests'])]
    command += [argument for method in selectors for argument in ('-method', method)]
    subprocess.run([*command, '-noColor', '-result-ctrf', str(support)], cwd=owner, check=True)
    support_report = json.loads(support.read_text())
    if support_report['results']['summary']['skipped'] or support_report['results']['summary']['failed']:
        raise ValueError('Retained owning support methods must pass without skips')
    (results / 'owning-support-ctrf.json').write_text(json.dumps(support_report, indent=2))
    suffix = uuid.uuid4().hex
    namespace = 'g6-oq8-' + suffix
    owned = []
    pending = {}

    def container(role, image, port, arguments=(), published=0):
        name = namespace + '-' + role
        cidfile = scratch / (name + '.cid')
        pending[name] = cidfile
        try:
            result = subprocess.run(['docker', 'run', '--detach', '--cidfile', str(cidfile), '--name', name,
                            '--label', 'hexalith.story18-g6=' + namespace,
                            '-p', f'127.0.0.1:{published or ""}:{port}', image, *arguments],
                            capture_output=True, text=True, timeout=180)
            if result.returncode:
                print(result.stderr, end='', file=sys.stderr)
                raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
        finally:
            identity = _record_container_custody(cidfile, name, namespace, owned)
            if identity:
                pending.pop(name)
        if not identity:
            raise ValueError('Owning qualifier container custody is unproven')
        binding = subprocess.check_output(['docker', 'port', identity, str(port) + '/tcp'], text=True).strip()
        return name, int(binding.rsplit(':', 1)[1])

    cleanup = []
    removed = set()
    try:
        placement, _ = container('placement', 'daprio/dapr:1.19.1', 50005, ['./placement', '--port', '50005'])
        before_scheduler = len(owned)

        def create_scheduler(port, attempt):
            return container('scheduler-' + str(attempt), 'daprio/dapr:1.19.1', 50006,
                ['./scheduler', '--port', '50006', '--etcd-data-dir', '/tmp/g6-scheduler',
                 '--etcd-client-listen-address', '0.0.0.0', '--override-broadcast-host-port', f'127.0.0.1:{port}'], port)

        def discard_scheduler():
            while len(owned) > before_scheduler:
                cleanup.append(_remove_owned_container(owned[-1], namespace, removed=removed))
                owned.pop()

        scheduler, _ = _start_scheduler(create_scheduler, discard_scheduler)
        _, redis = container('redis', 'redis:7.4', 6379)
        postgres = 'postgres@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636'
        if subprocess.run(['docker', 'image', 'inspect', postgres], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode:
            subprocess.run(['docker', 'pull', postgres], check=True)
        environment = os.environ.copy()
        environment.update(HEXALITH_OQ8_DAPRD_PATH=str(Path.home() / '.dapr/bin/daprd'),
            HEXALITH_OQ8_CONFIGURATION='Release', HEXALITH_OQ8_PLACEMENT_CONTAINER=placement,
            HEXALITH_OQ8_SCHEDULER_CONTAINER=scheduler, HEXALITH_OQ8_REDIS_ENDPOINT=f'127.0.0.1:{redis}',
            HEXALITH_OQ8_NAMESPACE=namespace, HEXALITH_OQ8_CLEANUP_PATH=str(scratch / 'owning-fixture-cleanup.json'))
        result = scratch / 'owning-postgresql-ctrf.json'
        method = 'Hexalith.EventStore.Server.LiveSidecar.Tests.Actors.IdempotencyAdmissionOq8PostgresqlTests.ProductionMatrix_IndependentProcessesPreserveAuthorityReplayExpiryAndLeakageInvariants'
        process = subprocess.Popen(['dotnet', str(assemblies['Hexalith.EventStore.Server.LiveSidecar.Tests']),
            '-method', method, '-noColor', '-result-ctrf', str(result)], cwd=owner, env=environment,
            start_new_session=True)
        try:
            code = process.wait(timeout=900)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
        if result.exists():
            report = json.loads(result.read_text())
            (results / 'owning-postgresql-ctrf.json').write_text(json.dumps(report, indent=2))
        if code:
            raise subprocess.CalledProcessError(code, 'owning PostgreSQL qualifier')
        if report['results']['summary']['passed'] != 1 or report['results']['summary']['skipped']:
            raise ValueError('The owning PostgreSQL test must pass exactly once without skips')
    finally:
        _cleanup_owned_containers(owned, namespace, removed, cleanup, results / 'owning-g6-cleanup.json', pending=pending)
