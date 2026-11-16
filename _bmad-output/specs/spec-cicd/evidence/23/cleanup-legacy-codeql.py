"""AD-21 cleanup restricted to Tenants' assessed legacy CodeQL configuration."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PREFIX = 'repos/Hexalith/Hexalith.Tenants'
ANALYSES = PREFIX + '/code-scanning/analyses'
LEGACY_KEY = '.github/workflows/codeql.yml:analyze'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=HERE / 'legacy-codeql-authorized-cleanup.json')
parser.add_argument('--resume-from', type=Path)
arguments = parser.parse_args()
OUTPUT = arguments.output
assert not OUTPUT.exists(), 'Assess retained cleanup state before resuming'
assert not any(key in os.environ for key in ('GH_TOKEN', 'GITHUB_TOKEN'))
selection = json.loads((HERE / 'app-selection-persisted-readback.json').read_text())
assert selection['verified'] is True
assert 'Hexalith.Tenants' in selection['observation']['selected']
assert selection['observation']['save_enabled'] is False
assert 0 <= (datetime.now(timezone.utc) - datetime.fromisoformat(selection['recorded_at'])).total_seconds() < 3600
environment = dict(os.environ, GH_CONFIG_DIR='/home/administrator/.config/gh', GH_PROMPT_DISABLED='1')
for key in ('GH_DEBUG', 'GIT_TRACE', 'GIT_TRACE_CURL', 'GIT_CURL_VERBOSE'):
    environment.pop(key, None)
report = {'started_at': datetime.now(timezone.utc).isoformat(),
          'administration_profile': environment['GH_CONFIG_DIR'],
          'override_presence': {key: key in os.environ for key in ('GH_TOKEN', 'GITHUB_TOKEN')},
          'target': PREFIX, 'legacy_analysis_key': LEGACY_KEY,
          'app_selection_evidence': 'app-selection-persisted-readback.json',
          'requests': [], 'deleted_ids': [], 'result': 'pending'}
(HERE / 'latest-codeql-cleanup.txt').write_text(OUTPUT.name + '\n')
if arguments.resume_from:
    prior = json.loads(arguments.resume_from.read_text())
    assert prior['target'] == PREFIX and prior['legacy_analysis_key'] == LEGACY_KEY
    report.update(resumed_from=str(arguments.resume_from),
                  prior_deleted_ids=[*prior.get('prior_deleted_ids', []), *prior['deleted_ids']])


class RemovedAnalysis(Exception):
    """A listed analysis disappeared; only a fresh inventory can choose another."""


def save():
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n')


def api(method, endpoint):
    result = subprocess.run(['gh', 'api', '--method', method, '--include', endpoint],
                            env=environment, capture_output=True, text=True, timeout=45)
    headers, _, body = result.stdout.replace('\r\n', '\n').partition('\n\n')
    data = json.loads(body) if body.strip() else None
    recorded = data
    if isinstance(data, list):
        recorded = {'count': len(data), 'analysis_keys': sorted({x.get('analysis_key', '') for x in data}),
                    'deletable_ids': [x['id'] for x in data if x.get('deletable') is True]}
    elif isinstance(data, dict) and endpoint == 'user':
        recorded = {key: data.get(key) for key in ('login', 'id')}
    elif isinstance(data, dict) and endpoint == PREFIX:
        recorded = {key: data.get(key) for key in ('id', 'full_name', 'permissions')}
    elif isinstance(data, dict) and result.returncode == 0 and method == 'GET' and '/analyses/' in endpoint:
        recorded = {key: data.get(key) for key in ('id', 'analysis_key', 'category', 'tool', 'deletable', 'ref', 'commit_sha')}
    report['requests'].append({'recorded_at': datetime.now(timezone.utc).isoformat(),
                               'method': method, 'endpoint': endpoint, 'exit': result.returncode,
                               'headers': [line for line in headers.splitlines() if line.lower().startswith(
                                   ('http/', 'x-oauth-scopes:', 'x-accepted-oauth-scopes:', 'x-accepted-github-permissions:'))],
                               'data': recorded, 'error': result.stderr.strip()})
    save()
    if result.returncode:
        analysis_endpoint = endpoint.split('?', 1)[0]
        if (method in ('GET', 'DELETE') and re.fullmatch(re.escape(ANALYSES) + r'/[0-9]+', analysis_endpoint)
                and headers.startswith('HTTP/') and ' 404 ' in headers.splitlines()[0]
                and isinstance(data, dict) and data.get('message') ==
                'No analysis found for analysis ID ' + analysis_endpoint.rsplit('/', 1)[1]):
            raise RemovedAnalysis(endpoint)
        raise RuntimeError(f'{method} {endpoint}: {result.stderr.strip()}')
    return data


try:
    account = api('GET', 'user')
    assert account['login'] == 'jpiquot' and account['id'] == 6775094
    repository = api('GET', PREFIX)
    assert repository['id'] == 1174267565 and repository['full_name'] == 'Hexalith/Hexalith.Tenants'
    for _ in range(2000):
        analyses = []
        for page in range(1, 101):
            items = api('GET', ANALYSES + '?tool_name=CodeQL&per_page=100&page=' + str(page))
            assert isinstance(items, list)
            analyses.extend(items)
            if any(x['analysis_key'] == LEGACY_KEY and x.get('deletable') is True for x in items):
                break  # Enough evidence to choose a verified head; final emptiness still requires every page.
            if len(items) < 100:
                break
        else:
            raise RuntimeError('CodeQL page bound exceeded; inventory remains incomplete')
        legacy = [x for x in analyses if x['analysis_key'] == LEGACY_KEY]
        if not legacy:
            report.update(result='pass', completed_at=datetime.now(timezone.utc).isoformat(),
                          remaining_codeql_analysis_keys=sorted({x['analysis_key'] for x in analyses}),
                          other_configuration_deletions=0)
            save()
            print(json.dumps({'result': 'pass', 'deleted': len(report['deleted_ids']),
                              'remaining_codeql_analysis_keys': report['remaining_codeql_analysis_keys']}), flush=True)
            break
        heads = [x for x in legacy if x.get('deletable') is True]
        assert heads, 'Legacy configuration has no deletable head'
        for head in heads:
            endpoint = ANALYSES + '/' + str(head['id'])
            for _ in range(2000):
                try:
                    detail = api('GET', endpoint)
                except RemovedAnalysis:
                    report.setdefault('disappeared_before_delete', []).append(endpoint)
                    save()
                    break  # A fresh detail read is required for every other head.
                assert detail['tool']['name'] == 'CodeQL' and detail['analysis_key'] == LEGACY_KEY
                if detail['deletable'] is not True:
                    report.setdefault('no_longer_deletable', []).append(endpoint)
                    save()
                    break  # Preserve it until a later inventory identifies its head.
                identity = detail['id']
                try:
                    result = api('DELETE', endpoint + '?confirm_delete=true')
                except RemovedAnalysis:
                    report.setdefault('disappeared_at_delete', []).append(endpoint)
                    save()
                    break  # A 404 is retained; only the final full inventory can certify cleanup.
                report['deleted_ids'].append(identity)
                save()
                if len(report['deleted_ids']) % 25 == 0:
                    print(json.dumps({'legacy_analyses_deleted': len(report['deleted_ids'])}), flush=True)
                following = result['confirm_delete_url']
                if following is None:
                    break
                match = re.fullmatch(
                    r'https://api\.github\.com/(?:repos/Hexalith/Hexalith\.Tenants|repositories/1174267565)'
                    r'/code-scanning/analyses/([0-9]+)\?confirm_delete(?:=true)?', following)
                assert match, 'Deletion chain left the verified Tenants analyses endpoint'
                endpoint = ANALYSES + '/' + match[1]
            else:
                raise RuntimeError('Legacy deletion chain bound exceeded')
    else:
        raise RuntimeError('Legacy configuration cleanup bound exceeded')
except Exception as error:
    report.update(result='incomplete', error=str(error), stopped_at=datetime.now(timezone.utc).isoformat())
    save()
    raise
