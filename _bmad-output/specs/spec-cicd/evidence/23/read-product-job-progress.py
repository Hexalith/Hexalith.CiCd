"""Read only safe counters/phase metadata from one active local packet."""
import json
from pathlib import Path
import re
import stat
import sys
import time
import xml.etree.ElementTree as ET
from performance_checkpoint import read_checkpoint


packet = Path(__file__).resolve().parent / sys.argv[1]
assert packet.parent == Path(__file__).resolve().parent
record = json.loads((packet / 'result.json').read_text())
scratch = Path(record['privateScratchPath'])
output = {'packet': packet.name, 'status': record.get('status', 'running'),
          'elapsedSeconds': round(time.time() - record['startedAt']),
          'lastEvent': record['events'][-1] if record['events'] else None}
if scratch.exists():
    assert scratch.resolve() == scratch and scratch.parent == Path('/tmp')
    assert scratch.name.startswith('hexalith-job.') and stat.S_IMODE(scratch.stat().st_mode) == 0o700
    progress = scratch / 'worker-result.json'
    if progress.is_file():
        worker = json.loads(progress.read_text())
        assert worker['source'] == record['source']
        output['phases'] = [{key: row.get(key) for key in ('name', 'status', 'elapsedSeconds')}
                            for row in worker['phases']]
    reports = []
    for path in (scratch / 'Hexalith.Tenants/TestResults').rglob('*.trx'):
        try:
            counters = ET.parse(path).getroot().find('.//{*}Counters')
            if counters is not None:
                reports.append({key: int(counters.get(key, '0'))
                                for key in ('total', 'executed', 'passed', 'failed', 'notExecuted')})
        except (OSError, ET.ParseError):
            pass
    output['completedTrx'] = reports
    checkpoint = read_checkpoint(scratch)
    if checkpoint is not None:
        output['performanceCheckpoint'] = checkpoint
    raw_path = scratch / 'worker-private.log'
    if raw_path.is_file():
        raw = raw_path.read_text(errors='replace')
        raw = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', raw)
        output['pythonSuiteCounters'] = re.findall(r'^Ran (\d+) tests? in ([0-9.]+)s$', raw, re.MULTILINE)
        output['nodeTestCounters'] = re.findall(r'^(?:#|ℹ️?) (?:tests|pass|fail|skipped) \d+$', raw, re.MULTILINE)
        output['failureSummaries'] = re.findall(r'^FAILED \([a-z0-9=, ]+\)$', raw, re.MULTILINE)
        output['coldProfileStarts'] = re.findall(
            r'^Cold product profile: (rest|persisted|anonymous-ui|authenticated-ui|catalog-owner)$', raw, re.MULTILINE)
    receipt_path = scratch / 'runner/tenants-product-profiles/authenticated-ui.json'
    if receipt_path.is_file():
        try:
            receipt = json.loads(receipt_path.read_text())
            relative = Path(receipt['privateDirectory']).relative_to('/work/s23')
            private = scratch / relative
            assert private.parent == scratch / 'runner' and private.name.startswith('tenants-source-catalog-')
            assert not private.is_symlink()
            rows = []
            for path in private.glob('tenants-live-routes-*/result.json'):
                if path.is_symlink() or path.parent.is_symlink():
                    continue
                report = json.loads(path.read_text())
                phase = report.get('progress', {}).get('phase', '')
                rows.append({'passed': report.get('passed') is True,
                             'completedCases': len(report.get('cases', [])),
                             'phase': phase if re.fullmatch(r'[A-Za-z0-9._-]{1,120}', phase) else None})
            output['authenticatedBrowserProgress'] = rows
        except (OSError, ValueError):
            pass
print(json.dumps(output))
