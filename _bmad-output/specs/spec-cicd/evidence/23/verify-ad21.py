"""Qualify retained post-provision Tenants readbacks without remote operations."""
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
PREFIX = 'repos/Hexalith/Hexalith.Tenants'
REPOSITORY_ID = 1174267565


def load(name):
    return json.loads((HERE / name).read_text())


current = load('maintainer-preflight-provisioned.json')
assert current['effective_GH_CONFIG_DIR'] == '/home/administrator/.config/gh'
assert not any(current['override_presence'].values())
requests = [x for x in current['requests'] if x['credential'] == 'maintainer-read-only']


def read(endpoint):
    row = next(x for x in requests if x['endpoint'] == endpoint)
    assert row['state'] == 'ok', endpoint + ' is unverified'
    return row['data']


def collection(path):
    matches = [x for x in current['collections'] if urlsplit(x['endpoint']).path == path]
    assert len(matches) == 1 and matches[0]['complete'], path + ' inventory is incomplete'
    return matches[0]['items']


assert read('user') == {'login': 'jpiquot', 'id': 6775094}
repository = read(PREFIX)
assert repository['id'] == REPOSITORY_ID and repository['full_name'] == 'Hexalith/Hexalith.Tenants'
assert repository['security_and_analysis']['secret_scanning_push_protection']['status'] == 'enabled'
app = load('app-selection-provisioned-readback.json')
assert app['verified'] is True and app['observation']['save_enabled'] is False
assert app['observation']['only_selected_repositories'] is True
assert 'Hexalith.Tenants' in app['observation']['selected']

packet_names = ('legacy-codeql-cleanup-verification.json', 'provision-cleanup-tags.json',
                'provision-rulesets.json', 'provision-environment.json', 'provision-registry.json',
                'nuget-policy-verification.json', 'provision-settings-grants-resumed.json')
packets = {name: load(name) for name in packet_names}
assert all(x['result'] == 'pass' for x in packets.values())

rulesets = collection(PREFIX + '/rulesets')
assert len(rulesets) == 2
expected_rules = {
    'branch': (['refs/heads/main'], {'deletion', 'non_fast_forward'}),
    'tag': (['refs/tags/v*'], {'update', 'deletion'}),
}
for item in rulesets:
    detail = read(PREFIX + '/rulesets/' + str(item['id']))
    refs, rules = expected_rules.pop(detail['target'])
    assert detail['enforcement'] == 'active' and detail['bypass_actors'] == []
    assert detail['conditions'] == {'ref_name': {'include': refs, 'exclude': []}}
    ordered_rules = ('deletion', 'non_fast_forward') if item['target'] == 'branch' else ('update', 'deletion')
    assert detail['rules'] == [{'type': kind} for kind in ordered_rules]
    assert {x['type'] for x in detail['rules']} == rules
assert not expected_rules

release_environment = read(PREFIX + '/environments/hexalith-release')
assert release_environment['deployment_branch_policy'] == {'protected_branches': False, 'custom_branch_policies': True}
assert all(x['type'] == 'branch_policy' for x in release_environment['protection_rules'])
policies = collection(PREFIX + '/environments/hexalith-release/deployment-branch-policies')
assert len(policies) == 1 and policies[0]['name'] == 'main' and policies[0]['type'] == 'branch'
secret_names = {x['name'] for x in collection(PREFIX + '/environments/hexalith-release/secrets')}
assert {'HEXALITH_REGISTRY_USERNAME', 'HEXALITH_REGISTRY_PASSWORD'} <= secret_names

registry = packets['provision-registry.json']
identity = registry['identities']['Hexalith.Tenants']
assert identity['username'] == 'hexalith-tenants-publish'
assert set(identity['repository_patterns']) == {'tenants', 'tenants/**', 'tenants-api', 'tenants-api/**'}
assert identity['actions'] == ['read', 'create', 'update'] and identity['admin_actions'] == []
assert registry['preservation']['old_htpasswd_rows_byte_identical']
assert registry['preservation']['existing_configuration_and_grants_unchanged']
assert not registry['preservation']['legacy_access_removed']
assert len(registry['authentication']) == 5
assert all(x['status'] == x['expected'] for x in registry['authentication'])

nuget = packets['nuget-policy-verification.json']
assert nuget['status'] == 'Active' and nuget['repository_id'] == REPOSITORY_ID
assert nuget['package_owner'] == 'Hexalith' and nuget['repository_owner_id'] == 80614290
assert nuget['workflow'] == 'release.yml' and nuget['environment'] == 'hexalith-release'
assert nuget['package_glob'] == 'Hexalith.Tenants*' and nuget['push_new_packages_and_versions']
assert not nuget['unlist'] and not nuget['stage']
assert nuget['legacy_policy_unchanged'] and nuget['all_existing_policy_ids_preserved']

assert read(PREFIX + '/code-scanning/default-setup')['state'] == 'not-configured'
assert read(PREFIX + '/automated-security-fixes')['enabled'] is False
assert read(PREFIX + '/actions/permissions/artifact-and-log-retention')['days'] == 90
variables = {x['name']: x['value'] for x in collection(PREFIX + '/actions/variables')}
assert variables['HEXALITH_RELEASE_PUBLISH_ENABLED'] == 'true'
assert variables['NUGET_USER'] == 'jpiquot'
for kind, names in (
    ('actions/secrets', ('HEXALITH_REGISTRY_PULL_USERNAME', 'HEXALITH_REGISTRY_PULL_PASSWORD')),
    ('dependabot/secrets', ('HEXALITH_REGISTRY_PULL_USERNAME', 'HEXALITH_REGISTRY_PULL_PASSWORD')),
    ('actions/variables', ('HEXALITH_NUGET_USER',)),
):
    for name in names:
        assert any(x['id'] == REPOSITORY_ID for x in collection('orgs/Hexalith/' + kind + '/' + name + '/repositories'))

# These remain raw failures. Independent, authenticated UI evidence supplies
# the App selection and post-deletion absence evidence; no 403/404 is made green.
expected_failures = {
    'user/installations/179966090/repositories': (403, None),
    PREFIX + '/code-scanning/analyses': (404, 'no analysis found'),
    'repos/Hexalith/Hexalith.CiCd/git/ref/heads/delivered/Hexalith.Tenants': (404, 'Not Found'),
}
observed_failures = []
for row in requests:
    if row['state'] == 'ok':
        continue
    expected_status, expected_message = expected_failures[urlsplit(row['endpoint']).path]
    assert row['http_status'] == expected_status
    if expected_message:
        assert row['data']['message'] == expected_message
    observed_failures.append({'endpoint': row['endpoint'], 'status': row['http_status'], 'state': row['state']})

report = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'result': 'pass',
          'scope': 'AD-21 per-repository provisioning before product preparation',
          'repository': 'Hexalith.Tenants', 'repository_id': REPOSITORY_ID,
          'github_readback': 'maintainer-preflight-provisioned.json',
          'app_selection_readback': 'app-selection-provisioned-readback.json',
          'provisioning_packets': list(packet_names), 'raw_failures_preserved': observed_failures,
          'product_preparation_allowed': True, 'adoption_ready': False,
          'remaining_adoption_gates': ['compatible published Builds release and pin',
                                      'Tenants product implementation and verification',
                                      'concrete legacy Zot publisher revocation plan',
                                      'committed candidate validation, App delivery and immediate cleanup',
                                      'green adopted CI and next genuine scheduled nightly outcome']}
(HERE / 'ad21-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
