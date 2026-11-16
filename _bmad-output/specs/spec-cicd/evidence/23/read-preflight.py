"""Read-only story-23 configuration and authentication inventory."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULE = Path('/home/administrator/projects/hexalith/cicd/references/Hexalith.Tenants')
PREFIX = 'repos/Hexalith/Hexalith.Tenants'
BASE_ENV = dict(os.environ, GH_PROMPT_DISABLED='1')
PROFILE_LABEL = ('maintainer-read-only' if os.environ.get('GH_CONFIG_DIR') ==
                 '/home/administrator/.config/gh' else 'cicd-agent')
for key in ('GH_DEBUG', 'GIT_TRACE', 'GIT_TRACE_CURL', 'GIT_CURL_VERBOSE'):
    BASE_ENV.pop(key, None)
report = {
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'effective_GH_CONFIG_DIR': os.environ.get('GH_CONFIG_DIR'),
    'override_presence': {key: key in os.environ for key in ('GH_TOKEN', 'GITHUB_TOKEN')},
    'requests': [], 'remote_mutations': False,
    'inventory_scope': 'Initial read-only pages; paginate and refresh before any mutation.',
}
assert not any(report['override_presence'].values())


def summarize(endpoint, data):
    if endpoint.endswith('/releases?per_page=100') and isinstance(data, list):
        return [{key: item.get(key) for key in
                 ('id', 'tag_name', 'draft', 'immutable', 'target_commitish', 'published_at')}
                for item in data]
    if endpoint.endswith('/code-scanning/analyses?per_page=100') and isinstance(data, list):
        return [{key: item.get(key) for key in ('id', 'ref', 'category', 'commit_sha', 'created_at')}
                for item in data]
    if '/repositories?' in endpoint and isinstance(data, dict) and 'repositories' in data:
        return {'total_count': data.get('total_count'),
                'repositories': [{key: item.get(key) for key in ('id', 'full_name')}
                                 for item in data['repositories']]}
    return data


def request(endpoint, label=PROFILE_LABEL, env=BASE_ENV, redact=()):
    result = subprocess.run(['gh', 'api', '--method', 'GET', '--include', endpoint],
                            env=env, capture_output=True, text=True, timeout=45)
    headers, _, body = result.stdout.partition('\n\n')
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = {'unparsed_body': body[:500]}
    if result.returncode == 0 and endpoint == 'user':
        data = {key: data.get(key) for key in ('login', 'id')}
    elif result.returncode == 0 and endpoint == PREFIX:
        data = {key: data.get(key) for key in ('id', 'full_name', 'default_branch', 'permissions', 'security_and_analysis')}
    if result.returncode == 0:
        data = summarize(endpoint, data)
    row = {'credential': label, 'endpoint': endpoint, 'exit': result.returncode,
           'headers': [line for line in headers.splitlines() if line.lower().startswith(
               ('http/', 'x-oauth-scopes:', 'x-accepted-github-permissions:'))],
           'data': data, 'stderr': result.stderr.strip()}
    serialized = json.dumps(row)
    for value in redact:
        assert value not in serialized, 'Credential unexpectedly present in response'
    report['requests'].append(row)
    return row


request('user')
request(PREFIX)
for endpoint in (
    PREFIX + '/git/ref/heads/main',
    PREFIX + '/rulesets?includes_parents=true',
    PREFIX + '/environments',
    PREFIX + '/actions/variables',
    PREFIX + '/actions/permissions/artifact-and-log-retention',
    PREFIX + '/code-scanning/default-setup',
    PREFIX + '/automated-security-fixes',
    PREFIX + '/immutable-releases',
    PREFIX + '/releases?per_page=100',
    'repos/Hexalith/Hexalith.CiCd/git/ref/heads/delivered/Hexalith.Tenants',
):
    request(endpoint)
rules = next(row for row in report['requests'] if '/rulesets?' in row['endpoint'])
if rules['exit'] == 0 and isinstance(rules['data'], list):
    for item in rules['data']:
        request(PREFIX + '/rulesets/' + str(item['id']))
environment_row = next(row for row in report['requests'] if row['endpoint'].endswith('/environments'))
if environment_row['exit'] == 0:
    for item in environment_row['data'].get('environments', []):
        if item['name'] == 'hexalith-release':
            request(PREFIX + '/environments/hexalith-release')
            request(PREFIX + '/environments/hexalith-release/secrets')

if PROFILE_LABEL == 'maintainer-read-only':
    request('orgs/Hexalith/installations')
    request('user/installations/179966090/repositories?per_page=100')
    request(PREFIX + '/code-scanning/analyses?per_page=100')
    request('orgs/Hexalith/actions/secrets?per_page=100')
    request('orgs/Hexalith/dependabot/secrets?per_page=100')
    request('orgs/Hexalith/actions/variables?per_page=100')
    for kind, names in (
        ('actions/secrets', ('HEXALITH_REGISTRY_PULL_USERNAME', 'HEXALITH_REGISTRY_PULL_PASSWORD', 'NUGET_API_KEY', 'HEXALITH_ZOT_USERNAME', 'HEXALITH_ZOT_PASSWORD')),
        ('dependabot/secrets', ('HEXALITH_REGISTRY_PULL_USERNAME', 'HEXALITH_REGISTRY_PULL_PASSWORD')),
        ('actions/variables', ('HEXALITH_NUGET_USER',)),
    ):
        for name in names:
            request('orgs/Hexalith/' + kind + '/' + name + '/repositories?per_page=100')

source = Path('/home/administrator/.config/gh-module-agent/token')
report['module_credential_file'] = {
    'path': str(source), 'exists': source.is_file(),
    'symlink': source.is_symlink(),
}
if source.is_file() and not source.is_symlink():
    info = source.stat()
    report['module_credential_file'].update(mode=oct(info.st_mode & 0o777), owned_by_current_user=info.st_uid == os.getuid())
    if info.st_uid == os.getuid() and info.st_mode & 0o777 == 0o600:
        token = source.read_text().strip()
        child_env = dict(BASE_ENV, GH_TOKEN=token)
        child_env.pop('GITHUB_TOKEN', None)
        request('user', 'module-agent', child_env, (token,))
        request(PREFIX, 'module-agent', child_env, (token,))

report['git'] = {}
for name, command, cwd in (
    ('cicd_head', ['git', 'rev-parse', 'HEAD'], ROOT),
    ('tenants_head', ['git', 'rev-parse', 'HEAD'], MODULE),
    ('tenants_main', ['git', 'rev-parse', 'origin/main'], MODULE),
    ('tenants_committed_inputs', ['git', 'ls-tree', 'HEAD', 'references/Hexalith.Builds', '.github/hexalith-ci.json'], MODULE),
    ('checker_command', ['run-with-temp', 'python3', 'references/Hexalith.Builds/check.py'], MODULE),
):
    result = subprocess.run(command, cwd=cwd, env=BASE_ENV, capture_output=True, text=True, timeout=45)
    report['git'][name] = {'command': command, 'cwd': str(cwd), 'exit': result.returncode,
                           'stdout': result.stdout, 'stderr': result.stderr}
report['authentication_after'] = {
    'effective_GH_CONFIG_DIR': os.environ.get('GH_CONFIG_DIR'),
    'override_presence': {key: key in os.environ for key in ('GH_TOKEN', 'GITHUB_TOKEN')},
}
(HERE / ('maintainer-preflight.json' if PROFILE_LABEL == 'maintainer-read-only'
         else 'preflight.json')).write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'requests': [{'credential': row['credential'], 'endpoint': row['endpoint'],
                                'exit': row['exit']} for row in report['requests']],
                  'checker_exit': report['git']['checker_command']['exit'],
                  'remote_mutations': False}, indent=2))
