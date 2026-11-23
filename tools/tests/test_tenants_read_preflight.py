"""Offline qualification: no real gh/git subprocess is allowed by these tests."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'tenants_preflight', ROOT / 'tools/qualification/pre-adoption/tenants/read-preflight.py')
PREFLIGHT = importlib.util.module_from_spec(SPEC)
# A regression to import-time execution must also fail without contacting GitHub.
with mock.patch.object(subprocess, 'run', side_effect=AssertionError('unexpected external command during import')):
    SPEC.loader.exec_module(PREFLIGHT)


def response(data=None, *, status=200, headers=(), raw=None):
    body = json.dumps(data) if raw is None else raw
    lines = [f'HTTP/2.0 {status} status', 'X-Accepted-Github-Permissions: administration=read', *headers]
    return subprocess.CompletedProcess([], 0 if status < 400 else 1, '\r\n'.join(lines) + '\r\n\r\n' + body, '')


def link(endpoint, page=2):
    return 'Link: <https://api.github.com/' + PREFLIGHT.page_endpoint(endpoint, page) + '>; rel="next"'


class PreflightTests(unittest.TestCase):
    def test_default_root_resolves_to_the_cicd_repository(self):
        self.assertEqual(ROOT, PREFLIGHT.ROOT)

    def setUp(self):
        guard = mock.patch.object(subprocess, 'run', side_effect=AssertionError('unexpected external command'))
        guard.start()
        self.addCleanup(guard.stop)

    def reader(self, replies):
        replies = iter(replies)
        calls = []
        def transport(endpoint, environment):
            calls.append(endpoint)
            value = next(replies)
            if isinstance(value, Exception):
                raise value
            return value
        return PREFLIGHT.Inventory({'GH_CONFIG_DIR': PREFLIGHT.MAINTAINER_PROFILE}, transport=transport), calls

    def test_multi_page_success_keeps_filters_metadata_and_complete_inventory(self):
        endpoint = PREFLIGHT.PREFIX + '/rulesets?includes_parents=true'
        reader, calls = self.reader([
            response([{'id': 1}], headers=(link(endpoint), 'X-OAuth-Scopes: repo', 'Set-Cookie: private')),
            response([{'id': 2}]),
        ])
        result = reader.collection(endpoint)
        self.assertTrue(result['complete'])
        self.assertEqual([1, 2], [item['id'] for item in result['items']])
        self.assertEqual(2, result['successful_pages'])
        self.assertEqual(['1', '2'], [parse_qs(urlsplit(call).query)['page'][0] for call in calls])
        self.assertTrue(all(parse_qs(urlsplit(call).query)['includes_parents'] == ['true'] for call in calls))
        self.assertIn('X-OAuth-Scopes: repo', reader.report['requests'][0]['headers'])
        self.assertNotIn('Set-Cookie: private', json.dumps(reader.report))

    def test_later_refusal_retains_observed_items_and_exact_permission_failure(self):
        endpoint = 'orgs/Hexalith/actions/secrets'
        reader, _ = self.reader([
            response({'total_count': 2, 'secrets': [{'name': 'FIRST'}]}, headers=(link(endpoint),)),
            response({'message': 'Resource not accessible by personal access token'}, status=403),
        ])
        result = reader.collection(endpoint, 'secrets')
        self.assertFalse(result['complete'])
        self.assertEqual('partial', result['state'])
        self.assertEqual([{'name': 'FIRST'}], result['items'])
        denied = reader.report['requests'][-1]
        self.assertEqual((1, 403, 'refused'), (denied['exit'], denied['http_status'], denied['state']))
        self.assertIn('administration=read', denied['headers'][1])
        self.assertEqual('refused', result['failure']['reason'])

    def test_metadata_verified_codeql_numeric_alias_continues_all_pages(self):
        endpoint = PREFLIGHT.PREFIX + '/code-scanning/analyses'
        alias = 'repositories/1174267565/code-scanning/analyses'
        reader, calls = self.reader([
            response({'id': 1174267565, 'full_name': 'Hexalith/Hexalith.Tenants'}),
            response([{'id': 1}], headers=(link(alias),)),
            response([{'id': 2}], headers=(link(alias, 3),)),
            response([{'id': 3}]),
        ])
        reader.request(PREFLIGHT.PREFIX)
        result = reader.collection(endpoint)
        self.assertTrue(result['complete'])
        self.assertEqual(3, result['observed_count'])
        self.assertEqual([PREFLIGHT.PREFIX, PREFLIGHT.page_endpoint(endpoint),
                          PREFLIGHT.page_endpoint(alias, 2), PREFLIGHT.page_endpoint(alias, 3)], calls)
        self.assertEqual('ok', reader.report['requests'][-1]['state'])

    def test_codeql_numeric_alias_requires_successful_matching_repository_metadata(self):
        endpoint = PREFLIGHT.PREFIX + '/code-scanning/analyses'
        alias = 'repositories/1174267565/code-scanning/analyses'
        for metadata in (None, response({'message': 'Forbidden'}, status=403),
                         response({'id': 1174267566, 'full_name': 'Hexalith/Hexalith.Tenants'}),
                         response({'id': 1174267565, 'full_name': 'Hexalith/Other'})):
            with self.subTest(metadata=metadata):
                replies = [response([{'id': 1}], headers=(link(alias),))]
                if metadata is not None:
                    replies.insert(0, metadata)
                reader, calls = self.reader(replies)
                if metadata is not None:
                    reader.request(PREFLIGHT.PREFIX)
                result = reader.collection(endpoint)
                self.assertFalse(result['complete'])
                self.assertEqual(1, result['observed_count'])
                self.assertNotIn(PREFLIGHT.page_endpoint(alias, 2), calls)

    def test_verified_codeql_alias_keeps_repository_suffix_host_filter_and_page_boundaries(self):
        endpoint = PREFLIGHT.PREFIX + '/code-scanning/analyses'
        alias = 'repositories/1174267565/code-scanning/analyses'
        targets = (
            'https://api.github.com/repositories/1174267566/code-scanning/analyses?per_page=100&page=2',
            'https://api.github.com/repositories/1174267565/code-scanning/alerts?per_page=100&page=2',
            'https://example.invalid/' + alias + '?per_page=100&page=2',
            'https://api.github.com/' + alias + '?per_page=100&page=2&direction=asc',
            'https://api.github.com/' + alias + '?per_page=100&page=3',
        )
        for target in targets:
            with self.subTest(target=target):
                reader, calls = self.reader([
                    response({'id': 1174267565, 'full_name': 'Hexalith/Hexalith.Tenants'}),
                    response([{'id': 1}], headers=('Link: <' + target + '>; rel="next"',)),
                ])
                reader.request(PREFLIGHT.PREFIX)
                result = reader.collection(endpoint)
                self.assertFalse(result['complete'])
                self.assertEqual('partial', result['state'])
                self.assertEqual(2, len(calls))

    def test_empty_refused_and_inaccessible_collections_are_distinct(self):
        for reply, expected, complete in (
            (response([]), 'complete', True),
            (response({'message': 'Forbidden'}, status=403), 'refused', False),
            (response({'message': 'Not Found'}, status=404), 'not-found-or-inaccessible', False),
        ):
            with self.subTest(expected=expected):
                reader, _ = self.reader([reply])
                result = reader.collection('repos/Hexalith/Hexalith.Tenants/releases')
                self.assertEqual((expected, complete, []), (result['state'], result['complete'], result['items']))

    def test_partial_failure_after_successful_empty_page_is_still_partial(self):
        endpoint = 'orgs/Hexalith/installations'
        reader, _ = self.reader([
            response({'installations': []}, headers=(link(endpoint),)), response({}, status=403),
        ])
        result = reader.collection(endpoint, 'installations')
        self.assertEqual('partial', result['state'])
        self.assertEqual(1, result['successful_pages'])

    def test_malformed_later_page_timeout_and_transport_failure_preserve_partial_evidence(self):
        endpoint = PREFLIGHT.PREFIX + '/releases'
        failures = (response(raw='{'), response({'wrong': []}),
                    subprocess.TimeoutExpired('gh', 45, output='private partial stdout', stderr='private stderr'),
                    OSError('unavailable'))
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                reader, _ = self.reader([response([{'id': 1}], headers=(link(endpoint),)), failure])
                result = reader.collection(endpoint)
                self.assertEqual('partial', result['state'])
                self.assertEqual(1, result['observed_count'])
                self.assertFalse(result['complete'])
                self.assertNotIn('private', json.dumps(reader.report))

    def test_untrusted_or_inconsistent_pagination_never_certifies_completeness(self):
        endpoint = 'orgs/Hexalith/installations'
        bad_links = (
            'Link: <https://example.invalid/orgs/Hexalith/installations?per_page=100&page=2>; rel="next"',
            'Link: <https://api.github.com/orgs/Other/installations?per_page=100&page=2>; rel="next"',
            link(endpoint, 1), link(endpoint, 3),
            'Link: <https://api.github.com/orgs/Hexalith/installations?per_page=1&page=2>; rel="next"',
            'Link: malformed',
        )
        for header in bad_links:
            with self.subTest(header=header):
                reader, calls = self.reader([response({'installations': [{'id': 1}]}, headers=(header,))])
                result = reader.collection(endpoint, 'installations')
                self.assertFalse(result['complete'])
                self.assertEqual(1, len(calls))
                self.assertIn('failure', result)

    def test_missing_pages_changing_counts_and_duplicate_items_remain_unverified(self):
        endpoint = 'orgs/Hexalith/installations'
        for replies in (
            [response({'total_count': 2, 'installations': [{'id': 1}]})],
            [response({'total_count': 2, 'installations': [{'id': 1}]}, headers=(link(endpoint),)),
             response({'total_count': 3, 'installations': [{'id': 2}]})],
            [response({'total_count': 2, 'installations': [{'id': 1}]}, headers=(link(endpoint),)),
             response({'total_count': 2, 'installations': [{'id': 1}]})],
        ):
            reader, _ = self.reader(replies)
            result = reader.collection(endpoint, 'installations')
            self.assertFalse(result['complete'])
            self.assertIn('failure', result)

    def complete_transport(self, calls):
        def transport(endpoint, environment):
            calls.append(endpoint)
            path, query = urlsplit(endpoint).path, parse_qs(urlsplit(endpoint).query)
            if 'per_page' not in query:
                return response({'login': 'fixture', 'id': 99})
            self.assertEqual(['100'], query['per_page'])
            page = int(query['page'][0])
            self.assertIn(page, (1, 2))
            keys = {'environments': 'environments', 'variables': 'variables', 'repositories': 'repositories',
                    'secrets': 'secrets', 'installations': 'installations', 'deployment-branch-policies': 'branch_policies'}
            key = keys.get(path.rsplit('/', 1)[-1])
            item = {'id': page}
            if key == 'environments':
                item['name'] = 'production' if page == 1 else 'hexalith-release'
            if key in ('secrets', 'variables'):
                item.update(name='EXTRA_FIRST' if page == 1 else 'EXTRA_LATE', visibility='selected')
            data = {'total_count': 2, key: [item]} if key else [item]
            return response(data, headers=(link(endpoint),) if page == 1 else ())
        return transport

    def test_full_inventory_paginates_every_collection_and_discovers_late_details_and_grants(self):
        calls = []
        reader = PREFLIGHT.Inventory({'GH_CONFIG_DIR': PREFLIGHT.MAINTAINER_PROFILE}, transport=self.complete_transport(calls))
        report = reader.collect()
        self.assertTrue(report['collections'])
        self.assertTrue(all(item['complete'] and len(item['pages']) == 2 for item in report['collections']))
        self.assertIn(PREFLIGHT.PREFIX + '/rulesets/2', calls)
        self.assertIn(PREFLIGHT.PREFIX + '/environments/hexalith-release', calls)
        for kind in ('actions/secrets', 'dependabot/secrets', 'actions/variables'):
            self.assertIn(PREFLIGHT.page_endpoint('orgs/Hexalith/' + kind + '/EXTRA_LATE/repositories'), calls)
        self.assertIn(PREFLIGHT.page_endpoint('orgs/Hexalith/actions/secrets/HEXALITH_ZOT_API_KEY/repositories'), calls)
        self.assertNotIn('HEXALITH_ZOT_PASSWORD', json.dumps(calls))
        self.assertIn(PREFLIGHT.page_endpoint(PREFLIGHT.PREFIX + '/environments/hexalith-release/deployment-branch-policies'), calls)

    def test_cli_rejects_overrides_and_existing_evidence_before_requesting(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'historical.json'
            output.write_text('historical')
            for environment, exception in (({'GH_CONFIG_DIR': PREFLIGHT.MAINTAINER_PROFILE, 'GH_TOKEN': 'unused'}, SystemExit),
                                           ({'GH_CONFIG_DIR': PREFLIGHT.MAINTAINER_PROFILE}, FileExistsError)):
                with mock.patch.dict(os.environ, environment, clear=True), \
                        mock.patch.object(sys, 'argv', ['read-preflight.py', '--output', str(output)]), \
                        mock.patch.object(PREFLIGHT, 'Inventory') as reader, redirect_stdout(io.StringIO()), \
                        mock.patch.object(sys, 'stderr', io.StringIO()):
                    with self.assertRaises(exception):
                        PREFLIGHT.main()
                    reader.assert_not_called()
                    self.assertEqual('historical', output.read_text())

    def test_cli_saves_mocked_paginated_readbacks_without_changing_profile(self):
        calls = []
        reader = PREFLIGHT.Inventory({'GH_CONFIG_DIR': PREFLIGHT.MAINTAINER_PROFILE}, transport=self.complete_transport(calls))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'new.json'
            with mock.patch.dict(os.environ, {'GH_CONFIG_DIR': PREFLIGHT.MAINTAINER_PROFILE}, clear=True), \
                    mock.patch.object(sys, 'argv', ['read-preflight.py', '--output', str(output)]), \
                    mock.patch.object(PREFLIGHT, 'Inventory', return_value=reader), \
                    mock.patch.object(PREFLIGHT, 'local_metadata'), redirect_stdout(io.StringIO()):
                self.assertEqual(0, PREFLIGHT.main())
                saved = json.loads(output.read_text())
                self.assertTrue(all(row['complete'] for row in saved['collections']))
                self.assertEqual(PREFLIGHT.MAINTAINER_PROFILE, os.environ['GH_CONFIG_DIR'])
                self.assertFalse(saved['remote_mutations'])

    def test_redacts_module_credentials_and_removes_debug_environment(self):
        environments = []
        def transport(endpoint, environment):
            environments.append(environment)
            return response({'message': 'private-fixture-token'}, status=403,
                            headers=('X-GitHub-SSO: private-fixture-token',))
        reader = PREFLIGHT.Inventory({'GH_DEBUG': 'api', 'GIT_TRACE': '1'}, transport=transport)
        reader.request('user', label='module-agent', redact=('private-fixture-token',))
        self.assertNotIn('private-fixture-token', json.dumps(reader.report))
        self.assertNotIn('GH_DEBUG', environments[0])
        self.assertNotIn('GIT_TRACE', environments[0])


if __name__ == '__main__':
    unittest.main()
