"""Read-only story-23 inventory; imports never contact GitHub.

Run only during an authorized remote phase, with --output naming a new file.
Collections follow Link headers; refused/malformed pages remain incomplete.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qsl, urlencode, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFIX = 'repos/Hexalith/Hexalith.Tenants'
TENANTS_REPOSITORY_ID = 1174267565
MAINTAINER_PROFILE = '/home/administrator/.config/gh'
CICD_PROFILE = '/home/administrator/.config/gh-cicd-agent'
PERMISSION_HEADERS = ('x-oauth-scopes:', 'x-accepted-oauth-scopes:',
                      'x-accepted-github-permissions:', 'x-github-sso:',
                      'x-ratelimit-', 'retry-after:', 'link:')
MAX_PAGES = 1000


def gh_get(endpoint, environment):
    return subprocess.run(['gh', 'api', '--method', 'GET', '--include', endpoint],
                          env=environment, capture_output=True, text=True, timeout=45)


def summarize(endpoint, data):
    path = urlsplit(endpoint).path
    if path.endswith('/releases') and isinstance(data, list):
        fields = ('id', 'tag_name', 'draft', 'immutable', 'target_commitish', 'published_at')
    elif path.endswith('/code-scanning/analyses') and isinstance(data, list):
        fields = ('id', 'ref', 'category', 'commit_sha', 'created_at')
    else:
        fields = None
    if fields:
        return [{key: item.get(key) for key in fields} if isinstance(item, dict) else item for item in data]
    if path.endswith('/repositories') and isinstance(data, dict) and isinstance(data.get('repositories'), list):
        return {**data, 'repositories': [
            {key: item.get(key) for key in ('id', 'full_name')}
            if isinstance(item, dict) else item for item in data['repositories']]}
    if path == 'user' and isinstance(data, dict):
        return {key: data.get(key) for key in ('login', 'id')}
    if path == PREFIX and isinstance(data, dict):
        return {key: data.get(key) for key in
                ('id', 'full_name', 'default_branch', 'permissions', 'security_and_analysis')}
    return data


def page_endpoint(endpoint, page=1):
    parts = urlsplit(endpoint)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(per_page='100', page=str(page))
    return parts.path + '?' + urlencode(query)


def next_page(endpoint, headers, repository_id=None):
    links = [line.partition(':')[2].strip() for line in headers if line.lower().startswith('link:')]
    targets = []
    for value in links:
        for part in value.split(','):
            match = re.fullmatch(r'\s*<([^>]+)>\s*;\s*rel="([^"]+)"\s*', part)
            if match is None:
                raise ValueError('malformed pagination Link header')
            if 'next' in match[2].split():
                targets.append(match[1])
    if not targets:
        return None
    if len(targets) != 1:
        raise ValueError('multiple next-page links')
    current, following = urlsplit(endpoint), urlsplit(targets[0])
    allowed_paths = {current.path.lstrip('/')}
    codeql_paths = {PREFIX + '/code-scanning/analyses',
                    f'repositories/{TENANTS_REPOSITORY_ID}/code-scanning/analyses'}
    # GitHub's CodeQL Link header uses the numeric repository route. Only a
    # successful metadata read binding this exact ID/name authorizes that alias.
    if repository_id == TENANTS_REPOSITORY_ID and current.path.lstrip('/') in codeql_paths:
        allowed_paths = codeql_paths
    if (following.scheme not in ('', 'https') or following.netloc not in ('', 'api.github.com')
            or following.fragment or following.path.lstrip('/') not in allowed_paths):
        raise ValueError('pagination left the requested GitHub collection')
    before, after = parse_qsl(current.query, keep_blank_values=True), parse_qsl(following.query, keep_blank_values=True)
    if (len(after) != len(dict(after))
            or sorted((key, value) for key, value in before if key != 'page')
            != sorted((key, value) for key, value in after if key != 'page')
            or dict(after).get('page') != str(int(dict(before)['page']) + 1)):
        raise ValueError('pagination changed filters or skipped/repeated a page')
    return following.path.lstrip('/') + '?' + urlencode(after)


class Inventory:
    def __init__(self, environment, *, transport=gh_get):
        self.environment = dict(environment, GH_PROMPT_DISABLED='1')
        for key in ('GH_DEBUG', 'GIT_TRACE', 'GIT_TRACE_CURL', 'GIT_CURL_VERBOSE'):
            self.environment.pop(key, None)
        self.transport = transport
        self.repository_id = None
        self.label = ('maintainer-read-only' if environment.get('GH_CONFIG_DIR') == MAINTAINER_PROFILE else 'cicd-agent')
        self.report = {
            'recorded_at': datetime.now(timezone.utc).isoformat(),
            'effective_GH_CONFIG_DIR': environment.get('GH_CONFIG_DIR'),
            'override_presence': {key: key in environment for key in ('GH_TOKEN', 'GITHUB_TOKEN')},
            'requests': [], 'collections': [], 'remote_mutations': False,
            'inventory_scope': 'Paginated readbacks, not AD-21 approval; incomplete reads remain unverified.',
        }

    def request(self, endpoint, *, label=None, environment=None, redact=()):
        row = {'credential': label or self.label, 'endpoint': endpoint, 'exit': None,
               'http_status': None, 'headers': [], 'data': None, 'stderr': ''}
        try:
            result = self.transport(endpoint, environment or self.environment)
        except (OSError, subprocess.TimeoutExpired):
            # Timeout objects may carry partial output; never publish it.
            row['state'] = 'transport-error'
        else:
            row.update(exit=result.returncode, stderr=result.stderr.strip())
            header, separator, body = result.stdout.replace('\r\n', '\n').partition('\n\n')
            status = re.match(r'HTTP/\S+ ([0-9]{3})(?:\s|$)', header)
            if status and separator:
                row['http_status'] = int(status[1])
                row['headers'] = [line for line in header.splitlines()
                                  if line.lower().startswith(('http/', *PERMISSION_HEADERS))]
            try:
                data = json.loads(body) if body.strip() else None
                valid_json = bool(body.strip()) or row['http_status'] == 204
            except (ValueError, RecursionError):
                data, valid_json = None, False
            row['data'] = summarize(endpoint, data)
            code = row['http_status']
            if code in (401, 403):
                row['state'] = 'refused'
            elif code == 404:
                row['state'] = 'not-found-or-inaccessible'
            elif code is None or not valid_json:
                row['state'] = 'invalid-response'
            elif result.returncode or not 200 <= code < 300:
                row['state'] = 'failed'
            else:
                row['state'] = 'ok'
        serialized = json.dumps(row)
        for value in redact:
            if value:
                serialized = serialized.replace(value, '<redacted>')
        row = json.loads(serialized)
        self.report['requests'].append(row)
        if endpoint == PREFIX and row['state'] == 'ok' and isinstance(row['data'], dict):
            if (type(row['data'].get('id')) is int and row['data']['id'] == TENANTS_REPOSITORY_ID
                    and row['data'].get('full_name') == PREFIX.removeprefix('repos/')):
                self.repository_id = TENANTS_REPOSITORY_ID
        return row

    def collection(self, endpoint, key=None):
        endpoint = page_endpoint(endpoint)
        collection = {'credential': self.label, 'endpoint': endpoint, 'item_key': key,
                      'pages': [], 'successful_pages': 0, 'items': [], 'complete': False, 'state': 'unavailable'}
        self.report['collections'].append(collection)
        identities = set()
        for _ in range(MAX_PAGES):
            row = self.request(endpoint)
            collection['pages'].append(endpoint)
            if row['state'] != 'ok':
                collection.update(state='partial' if collection['successful_pages'] else row['state'],
                                  failure={'endpoint': endpoint, 'reason': row['state']})
                break
            data = row['data']
            items = data.get(key) if key is not None and isinstance(data, dict) else data if key is None else None
            if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
                collection['failure'] = {'endpoint': endpoint, 'reason': 'malformed collection body'}
                break
            collection['successful_pages'] += 1
            collection['items'].extend(items)
            try:
                for item in items:
                    identity = item.get('id', item.get('name', item.get('full_name')))
                    if not isinstance(identity, (int, str)) or isinstance(identity, bool) or identity in identities:
                        raise ValueError('missing or repeated item identity')
                    identities.add(identity)
                if isinstance(data, dict) and 'total_count' in data:
                    count = data['total_count']
                    if type(count) is not int or count < 0:
                        raise ValueError('invalid total_count')
                    if 'total_count' in collection and collection['total_count'] != count:
                        raise ValueError('total_count changed during pagination')
                    collection['total_count'] = count
                following = next_page(endpoint, row['headers'], self.repository_id)
                if following is None:
                    if collection.get('total_count', len(collection['items'])) != len(collection['items']):
                        raise ValueError('total_count does not match observed items')
                    collection.update(complete=True, state='complete')
                    break
                endpoint = following
            except ValueError as error:
                collection['failure'] = {'endpoint': row['endpoint'], 'reason': str(error)}
                break
        else:
            collection['failure'] = {'endpoint': endpoint, 'reason': 'pagination page limit reached'}
        if not collection['complete'] and collection['state'] == 'unavailable':
            collection['state'] = 'partial' if collection['successful_pages'] else 'invalid-response'
        collection['observed_count'] = len(collection['items'])
        return collection

    def collect(self):
        self.request('user')
        self.request(PREFIX)
        for suffix in ('/git/ref/heads/main', '/actions/permissions/artifact-and-log-retention',
                       '/code-scanning/default-setup', '/automated-security-fixes', '/immutable-releases'):
            self.request(PREFIX + suffix)
        rules = self.collection(PREFIX + '/rulesets?includes_parents=true')
        environments = self.collection(PREFIX + '/environments', 'environments')
        self.collection(PREFIX + '/actions/variables', 'variables')
        self.collection(PREFIX + '/releases')
        self.request('repos/Hexalith/Hexalith.CiCd/git/ref/heads/delivered/Hexalith.Tenants')
        for item in rules['items']:
            if type(item.get('id')) is int:
                self.request(PREFIX + '/rulesets/' + str(item['id']))
        if any(item.get('name') == 'hexalith-release' for item in environments['items']):
            self.request(PREFIX + '/environments/hexalith-release')
            self.collection(PREFIX + '/environments/hexalith-release/secrets', 'secrets')
            self.collection(PREFIX + '/environments/hexalith-release/deployment-branch-policies', 'branch_policies')
        if self.label == 'maintainer-read-only':
            self.collection('orgs/Hexalith/installations', 'installations')
            self.collection('user/installations/179966090/repositories', 'repositories')
            self.collection(PREFIX + '/code-scanning/analyses')
            for kind, key in (('actions/secrets', 'secrets'), ('dependabot/secrets', 'secrets'),
                              ('actions/variables', 'variables')):
                observed = self.collection('orgs/Hexalith/' + kind, key)
                # Include unanticipated selected legacy grants, as well as the
                # known prerequisites, without recording secret values.
                names = {item['name'] for item in observed['items']
                         if isinstance(item.get('name'), str) and item.get('visibility') == 'selected'}
                names.update({'actions/secrets': (
                    'HEXALITH_REGISTRY_PULL_USERNAME', 'HEXALITH_REGISTRY_PULL_PASSWORD',
                    'NUGET_API_KEY', 'HEXALITH_ZOT_USERNAME', 'HEXALITH_ZOT_API_KEY'),
                    'dependabot/secrets': ('HEXALITH_REGISTRY_PULL_USERNAME', 'HEXALITH_REGISTRY_PULL_PASSWORD'),
                    'actions/variables': ('HEXALITH_NUGET_USER',)}[kind])
                for name in sorted(names):
                    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
                        self.collection('orgs/Hexalith/' + kind + '/' + name + '/repositories', 'repositories')
        return self.report


def local_metadata(inventory, root=ROOT, credential=Path('/home/administrator/.config/gh-module-agent/token')):
    """Record local provenance; product verification is a separate operation."""
    report = inventory.report
    report['module_credential_file'] = {'path': str(credential), 'exists': credential.is_file(), 'symlink': credential.is_symlink()}
    if credential.is_file() and not credential.is_symlink():
        info = credential.stat()
        report['module_credential_file'].update(mode=oct(info.st_mode & 0o777), owned_by_current_user=info.st_uid == os.getuid())
        if info.st_uid == os.getuid() and info.st_mode & 0o777 == 0o600:
            token = credential.read_text().strip()
            if token:
                environment = dict(inventory.environment, GH_TOKEN=token)
                environment.pop('GITHUB_TOKEN', None)
                for endpoint in ('user', PREFIX):
                    inventory.request(endpoint, label='module-agent', environment=environment, redact=(token,))
    module = root / 'references/Hexalith.Tenants'
    report['git'] = {}
    for name, arguments, cwd in (
        ('cicd_head', ['rev-parse', 'HEAD'], root),
        ('tenants_head', ['rev-parse', 'HEAD'], module),
        ('tenants_main', ['rev-parse', 'origin/main'], module),
        ('tenants_committed_inputs', ['ls-tree', 'HEAD', 'references/Hexalith.Builds', '.github/hexalith-ci.json'], module),
    ):
        try:
            result = subprocess.run(['git', *arguments], cwd=cwd, env=inventory.environment,
                                    capture_output=True, text=True, timeout=45)
            report['git'][name] = {'command': ['git', *arguments], 'cwd': str(cwd), 'exit': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr}
        except (OSError, subprocess.TimeoutExpired):
            report['git'][name] = {'state': 'unavailable', 'cwd': str(cwd)}
    report['checker'] = {'state': 'not-run', 'reason': 'Configuration inventory does not verify a product revision.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new evidence file; existing files are never overwritten')
    arguments = parser.parse_args()
    if any(key in os.environ for key in ('GH_TOKEN', 'GITHUB_TOKEN')):
        parser.error('inherited GH_TOKEN/GITHUB_TOKEN overrides must be absent')
    if os.environ.get('GH_CONFIG_DIR') not in (MAINTAINER_PROFILE, CICD_PROFILE):
        parser.error('set command-local GH_CONFIG_DIR to the intended existing maintainer or CiCd-agent profile')
    # Reserve the evidence destination before any request; retain historical files.
    with arguments.output.open('x', encoding='utf-8') as output:
        inventory = Inventory(os.environ)
        inventory.collect()
        local_metadata(inventory)
        report = inventory.report
        report['authentication_after'] = {
            'effective_GH_CONFIG_DIR': os.environ.get('GH_CONFIG_DIR'),
            'override_presence': {key: key in os.environ for key in ('GH_TOKEN', 'GITHUB_TOKEN')},
        }
        output.write(json.dumps(report, indent=2) + '\n')
    failures = sum(row['state'] != 'ok' for row in report['requests'])
    incomplete = sum(not row['complete'] for row in report['collections'])
    print(json.dumps({'output': str(arguments.output), 'failed_requests': failures,
                      'incomplete_collections': incomplete, 'remote_mutations': False}, indent=2))
    return 2 if failures or incomplete else 0


if __name__ == '__main__':
    raise SystemExit(main())
