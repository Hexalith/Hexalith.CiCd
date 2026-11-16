"""Ordered, Tenants-only AD-21 GitHub administration with retained readbacks."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PREFIX = 'repos/Hexalith/Hexalith.Tenants'
REPOSITORY_ID = 1174267565
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('phase', choices=('cleanup-tags', 'rulesets', 'environment', 'settings-grants'))
parser.add_argument('--output', type=Path)
parser.add_argument('--resume-from', type=Path)
arguments = parser.parse_args()
output = arguments.output or HERE / ('provision-' + arguments.phase + '.json')
assert not output.exists(), 'Assess retained partial operations before a retry'
assert not any(key in os.environ for key in ('GH_TOKEN', 'GITHUB_TOKEN'))
environment = dict(os.environ, GH_CONFIG_DIR='/home/administrator/.config/gh', GH_PROMPT_DISABLED='1')
for key in ('GH_DEBUG', 'GIT_TRACE', 'GIT_TRACE_CURL', 'GIT_CURL_VERBOSE'):
    environment.pop(key, None)
spec = importlib.util.spec_from_file_location('tenants_preflight', HERE / 'read-preflight.py')
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)
reader = preflight.Inventory(environment)
report = {'started_at': datetime.now(timezone.utc).isoformat(), 'phase': arguments.phase,
          'administration_profile': environment['GH_CONFIG_DIR'],
          'override_presence': {key: key in os.environ for key in ('GH_TOKEN', 'GITHUB_TOKEN')},
          'requests': [], 'readbacks': reader.report, 'result': 'pending'}
if arguments.resume_from:
    prior = json.loads(arguments.resume_from.read_text())
    assert prior['phase'] == arguments.phase and prior['result'] == 'incomplete'
    report.update(resumed_from=str(arguments.resume_from), prior_mutation_count=len(prior['requests']))


def save():
    output.write_text(json.dumps(report, indent=2) + '\n')


def require_packet(name):
    packet = json.loads((HERE / name).read_text())
    assert packet.get('result') == 'pass', name + ' is incomplete'
    return packet


def read(endpoint):
    row = reader.request(endpoint)
    save()
    assert row['state'] == 'ok', endpoint + ': ' + row['stderr']
    return row['data']


def collection(endpoint, key=None):
    data = reader.collection(endpoint, key)
    save()
    assert data['complete'], endpoint + ': incomplete inventory'
    return data['items']


def mutate(method, endpoint, value=None):
    command = ['gh', 'api', '--method', method, '--include', endpoint]
    if value is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(value) if value is not None else None,
                            env=environment, capture_output=True, text=True, timeout=45)
    headers, _, body = result.stdout.replace('\r\n', '\n').partition('\n\n')
    data = json.loads(body) if body.strip() else None
    report['requests'].append({'recorded_at': datetime.now(timezone.utc).isoformat(),
                               'method': method, 'endpoint': endpoint, 'input': value,
                               'exit': result.returncode, 'data': data, 'error': result.stderr.strip(),
                               'headers': [line for line in headers.splitlines() if line.lower().startswith(
                                   ('http/', 'x-oauth-scopes:', 'x-accepted-oauth-scopes:', 'x-accepted-github-permissions:'))]})
    save()
    assert result.returncode == 0, method + ' ' + endpoint + ': ' + result.stderr.strip()
    return data


try:
    selection = json.loads((HERE / 'app-selection-persisted-readback.json').read_text())
    assert selection['verified'] and 'Hexalith.Tenants' in selection['observation']['selected']
    account = read('user')
    assert account == {'login': 'jpiquot', 'id': 6775094}
    repository = read(PREFIX)
    assert repository['id'] == REPOSITORY_ID and repository['full_name'] == 'Hexalith/Hexalith.Tenants'

    if arguments.phase == 'cleanup-tags':
        require_packet((HERE / 'latest-codeql-cleanup.txt').read_text().strip())
        assessed = json.loads((HERE / 'legacy-tag-cleanup-assessment.json').read_text())['assessment']
        candidates = [x for x in assessed if not x['published_packages'] and not x['published_containers']]
        releases = collection(PREFIX + '/releases')
        assert not any(x['draft'] for x in releases), 'Assess unexpected drafts before cleanup'
        published = {x['tag_name'] for x in releases}
        tags = collection(PREFIX + '/tags')
        before = {x['name']: x['commit']['sha'] for x in tags}
        rules = collection(PREFIX + '/rulesets?includes_parents=true')
        assert not any(x['target'] == 'tag' and x['enforcement'] == 'active' for x in rules), 'Tag rules changed; assess before cleanup'
        report.update(deleted_tags=[], already_absent_tags=[])
        for item in candidates:
            name = item['tag']
            assert name not in published
            if name not in before:
                report['already_absent_tags'].append(name)
                save()
                continue
            reference = read(PREFIX + '/git/ref/tags/' + name)
            assert reference['object']['sha'] == item['sha'] == before[name], 'Assessed tag changed'
            mutate('DELETE', PREFIX + '/git/refs/tags/' + name)
            report['deleted_tags'].append({'tag': name, 'sha': item['sha']})
            save()
        after = {x['name']: x['commit']['sha'] for x in collection(PREFIX + '/tags')}
        removed = {x['tag'] for x in candidates}
        assert not removed.intersection(after)
        assert all(after.get(name) == sha for name, sha in before.items() if name not in removed)
        report.update(published_and_unrelated_tags_preserved=True, published_release_count=len(published))

    elif arguments.phase == 'rulesets':
        require_packet('provision-cleanup-tags.json')
        desired = [
            {'name': 'Protect main', 'target': 'branch', 'enforcement': 'active', 'bypass_actors': [],
             'conditions': {'ref_name': {'include': ['refs/heads/main'], 'exclude': []}},
             'rules': [{'type': 'deletion'}, {'type': 'non_fast_forward'}]},
            {'name': 'v tags', 'target': 'tag', 'enforcement': 'active', 'bypass_actors': [],
             'conditions': {'ref_name': {'include': ['refs/tags/v*'], 'exclude': []}},
             'rules': [{'type': 'update'}, {'type': 'deletion'}]},
        ]
        existing = collection(PREFIX + '/rulesets?includes_parents=true')
        assert all(x['name'] in {d['name'] for d in desired} and x['source'] == 'Hexalith/Hexalith.Tenants' for x in existing), 'Assess foreign rulesets before changes'
        for definition in desired:
            matches = [x for x in existing if x['name'] == definition['name']]
            assert len(matches) <= 1
            if not matches:
                mutate('POST', PREFIX + '/rulesets', definition)
        actual = collection(PREFIX + '/rulesets?includes_parents=true')
        assert len(actual) == 2
        for item in actual:
            detail = read(PREFIX + '/rulesets/' + str(item['id']))
            wanted = next(x for x in desired if x['name'] == item['name'])
            assert all(detail.get(key) == value for key, value in wanted.items())
        report['exact_rulesets_verified'] = True

    elif arguments.phase == 'environment':
        require_packet('provision-rulesets.json')
        existing = collection(PREFIX + '/environments', 'environments')
        foreign = {x['name']: read(PREFIX + '/environments/' + x['name']) for x in existing if x['name'] != 'hexalith-release'}
        if not any(x['name'] == 'hexalith-release' for x in existing):
            mutate('PUT', PREFIX + '/environments/hexalith-release',
                   {'wait_timer': 0, 'reviewers': [], 'prevent_self_review': False,
                    'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True}})
        detail = read(PREFIX + '/environments/hexalith-release')
        assert detail['deployment_branch_policy'] == {'protected_branches': False, 'custom_branch_policies': True}
        assert all(x['type'] == 'branch_policy' for x in detail['protection_rules']), 'Assess unexpected release protections'
        policies = collection(PREFIX + '/environments/hexalith-release/deployment-branch-policies', 'branch_policies')
        if not policies:
            mutate('POST', PREFIX + '/environments/hexalith-release/deployment-branch-policies', {'name': 'main', 'type': 'branch'})
        policies = collection(PREFIX + '/environments/hexalith-release/deployment-branch-policies', 'branch_policies')
        assert len(policies) == 1 and policies[0]['name'] == 'main' and policies[0]['type'] == 'branch'
        assert all(read(PREFIX + '/environments/' + name) == value for name, value in foreign.items())
        report.update(main_only_release_environment_verified=True, foreign_environments_preserved=True)

    else:
        require_packet('provision-registry.json')
        require_packet('nuget-policy-verification.json')
        assert read(PREFIX + '/code-scanning/default-setup')['state'] == 'not-configured'
        assert read(PREFIX + '/automated-security-fixes')['enabled'] is False
        variables = collection(PREFIX + '/actions/variables', 'variables')
        switch = next((x for x in variables if x['name'] == 'HEXALITH_RELEASE_PUBLISH_ENABLED'), None)
        if switch is None:
            mutate('POST', PREFIX + '/actions/variables', {'name': 'HEXALITH_RELEASE_PUBLISH_ENABLED', 'value': 'true'})
        else:
            assert switch['value'] == 'true', 'Assess the existing publication switch before changing intent'
        assert read(PREFIX + '/actions/permissions/artifact-and-log-retention')['days'] == 90
        for kind, names in (
            ('actions/secrets', ('HEXALITH_REGISTRY_PULL_USERNAME', 'HEXALITH_REGISTRY_PULL_PASSWORD')),
            ('dependabot/secrets', ('HEXALITH_REGISTRY_PULL_USERNAME', 'HEXALITH_REGISTRY_PULL_PASSWORD')),
            ('actions/variables', ('HEXALITH_NUGET_USER',)),
        ):
            for name in names:
                endpoint = 'orgs/Hexalith/' + kind + '/' + name
                assert read(endpoint)['visibility'] == 'selected'
                before = {x['id'] for x in collection(endpoint + '/repositories', 'repositories')}
                if REPOSITORY_ID not in before:
                    mutate('PUT', endpoint + '/repositories/' + str(REPOSITORY_ID))
                after = {x['id'] for x in collection(endpoint + '/repositories', 'repositories')}
                assert after == before | {REPOSITORY_ID}
        variables = collection(PREFIX + '/actions/variables', 'variables')
        assert any(x['name'] == 'HEXALITH_RELEASE_PUBLISH_ENABLED' and x['value'] == 'true' for x in variables)
        report.update(shared_grants_verified=True, legacy_access_removed=False)
    report.update(result='pass', completed_at=datetime.now(timezone.utc).isoformat())
    save()
    print(json.dumps({'phase': arguments.phase, 'result': 'pass', 'mutations': len(report['requests'])}), flush=True)
except Exception as error:
    report.update(result='incomplete', error=str(error), stopped_at=datetime.now(timezone.utc).isoformat())
    save()
    raise
