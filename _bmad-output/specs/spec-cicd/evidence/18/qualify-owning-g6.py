"""Run retained owning product assertions without historical workflow/evidence gates."""
from pathlib import Path
import json
import os
import signal
import socket
import subprocess
import uuid


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

    def container(role, image, port, arguments=(), published=0):
        name = namespace + '-' + role
        cidfile = scratch / (name + '.cid')
        try:
            subprocess.run(['docker', 'run', '--detach', '--cidfile', str(cidfile), '--name', name,
                            '--label', 'hexalith.story18-g6=' + namespace,
                            '-p', f'127.0.0.1:{published or ""}:{port}', image, *arguments], check=True)
        finally:
            if cidfile.exists():
                owned.append(cidfile.read_text().strip())
        binding = subprocess.check_output(['docker', 'port', owned[-1], str(port) + '/tcp'], text=True).strip()
        return name, int(binding.rsplit(':', 1)[1])

    cleanup = []
    try:
        placement, _ = container('placement', 'daprio/dapr:1.19.1', 50005, ['./placement', '--port', '50005'])
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            scheduler_port = listener.getsockname()[1]
        scheduler, _ = container('scheduler', 'daprio/dapr:1.19.1', 50006,
            ['./scheduler', '--port', '50006', '--etcd-data-dir', '/tmp/g6-scheduler',
             '--etcd-client-listen-address', '0.0.0.0', '--override-broadcast-host-port', f'127.0.0.1:{scheduler_port}'], scheduler_port)
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
        for identity in reversed(owned):
            labels = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .Config.Labels}}', identity], text=True))
            if labels.get('hexalith.story18-g6') != namespace:
                raise ValueError('Exact owning qualifier cleanup custody changed')
            subprocess.run(['docker', 'rm', '--force', '--volumes', identity], check=True)
            removed = subprocess.run(['docker', 'inspect', identity], stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL).returncode != 0
            cleanup.append({'id':identity, 'removed':removed})
        (results / 'owning-g6-cleanup.json').write_text(json.dumps(cleanup, indent=2))
        if not all(item['removed'] for item in cleanup):
            raise ValueError('Owning qualifier control plane cleanup failed')
