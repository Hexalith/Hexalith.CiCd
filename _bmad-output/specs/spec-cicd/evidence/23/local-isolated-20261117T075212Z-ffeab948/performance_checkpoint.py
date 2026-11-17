"""Read only the exported support-safe benchmark checkpoint, never private bulk."""
import json
from pathlib import Path
import re
import stat


PHASES = {'RunnerStarting', 'FixtureCreated', 'FixtureInitialization', 'DomainConfiguration',
          'HostStartup', 'FixtureReady', 'ExecutionGateWait', 'BenchmarkSetup', 'Seeding',
          'SeedingComplete', 'TargetDeactivation', 'TargetDeactivated', 'Rehydration',
          'RehydrationComplete', 'AssertionsPassed', 'FixtureTeardown', 'FixtureDisposed'}


def read_checkpoint(scratch):
    runtime = scratch / 'runner'
    output = runtime / 'output'
    if not output.exists():
        return None
    assert not output.is_symlink() and output.stat().st_size < 1024 * 1024
    rows = [line.split('=', 1)[1] for line in output.read_text().splitlines()
            if line.startswith('progress_path=')]
    if not rows:
        return None
    assert len(rows) == 1
    path = Path(rows[0])
    assert path.name == 'progress.json' and path.parent.parent == Path('/work/s23/runner')
    assert re.fullmatch(r'tenants-performance-progress-[A-Za-z0-9]{8}', path.parent.name)
    private = runtime / path.parent.name
    target = private / path.name
    assert private.resolve(strict=True) == private and not private.is_symlink()
    assert stat.S_IMODE(private.stat().st_mode) == 0o700
    assert not target.is_symlink() and stat.S_IMODE(target.stat().st_mode) == 0o600
    assert target.stat().st_size <= 16384
    data = json.loads(target.read_bytes())
    assert data['schemaVersion'] == 1 and data['phase'] in PHASES
    assert data['status'] in ('incomplete', 'failed', 'passed')
    allowed = {'schemaVersion', 'phase', 'status', 'failedPhase', 'benchmarkPassed',
               'fixtureDisposed', 'commandsAccepted', 'configurationWritesAccepted',
               'tenantsSeeded', 'elapsedSeconds', 'phaseElapsedSeconds', 'completedPhaseSeconds',
               'rehydrationSeconds', 'optionsSnapshotInterval', 'persistedPolicyResolverRegistered',
               'effectiveSnapshotInterval', 'snapshotIntervalSource', 'workload'}
    assert set(data) <= allowed
    assert data.get('failedPhase') is None or data['failedPhase'] in PHASES
    assert data.get('snapshotIntervalSource') in (None, 'Default', 'Domain', 'TenantDomain')
    for key in ('benchmarkPassed', 'fixtureDisposed', 'persistedPolicyResolverRegistered'):
        assert data.get(key) is None or type(data[key]) is bool
    for key, maximum in (('commandsAccepted', 500000), ('configurationWritesAccepted', 167000),
                         ('tenantsSeeded', 1000), ('optionsSnapshotInterval', 2147483647),
                         ('effectiveSnapshotInterval', 2147483647)):
        assert data.get(key) is None or type(data[key]) is int and 0 <= data[key] <= maximum
    for key in ('elapsedSeconds', 'phaseElapsedSeconds', 'rehydrationSeconds'):
        assert data.get(key) is None or type(data[key]) in (int, float) and 0 <= data[key] <= 86400
    for key, value in data.get('completedPhaseSeconds', {}).items():
        assert key in PHASES and type(value) in (int, float) and 0 <= value <= 86400
    if 'workload' in data:
        assert data['workload'] == {'tenants':1000, 'commandsPerTenant':500, 'configurationKeys':100,
                                    'concurrency':50, 'documentedSnapshotInterval':50, 'rehydrationLimitSeconds':30}
    return data
