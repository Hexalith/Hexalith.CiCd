"""Local-only preparation perimeter controls using real disposable Git history."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('eventstore_bootstrap', Path(__file__).with_name('pre-adoption-verify.py'))
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def process(arguments, cwd, **_):
    env = os.environ.copy()
    if arguments[0] == 'git':
        # These commands only create and inspect the disposable history.
        env = {key: value for key, value in env.items() if not key.startswith('GIT_')}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
        arguments = ['git', '-c', 'core.hooksPath=' + os.devnull, *arguments[1:]]
    return subprocess.run(arguments, cwd=cwd, env=env, text=True, capture_output=True, check=True)


def git(repository, *arguments, **authentication):
    return verifier.git_read(process, repository, *arguments, **authentication)


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'repository'
        self.root.mkdir()
        git(self.root, 'init', '-b', 'main')
        git(self.root, 'config', 'user.name', 'Local test fixture')
        git(self.root, 'config', 'user.email', 'fixture@invalid.example')
        self.write('.github/workflows/ci.yml', 'owned baseline\n')
        self.write('scripts/ci-product-checks.py', 'product baseline\n')
        self.base = self.commit('test: establish fixture')

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message):
        git(self.root, 'add', '-A')
        git(self.root, 'commit', '-m', message)
        return git(self.root, 'rev-parse', 'HEAD')

    def test_literal_scope_refuses_unreviewed_publication_and_new_test_paths(self):
        for name in ('scripts/publish.py', 'scripts/verify-process-packages.py', 'tools/release.py',
                     'tests/new-test.cs', '.github/workflows/ci.yml', 'package-lock.json'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'protected paths'):
                verifier.require_preparation_paths([name])
        verifier.require_preparation_paths(['scripts/ci-product-checks.py'])

    def test_product_history_is_accepted(self):
        self.write('scripts/ci-product-checks.py', 'reviewed product change\n')
        head = self.commit('test: change product')
        self.assertEqual(1, len(verifier.verify_preparation_history(git, self.root, self.base, head)))

    def test_owned_edit_and_revert_with_equal_endpoint_is_rejected(self):
        self.write('.github/workflows/ci.yml', 'owned forbidden edit\n')
        changed = self.commit('test: alter protected fixture')
        git(self.root, 'revert', '--no-edit', changed)
        head = git(self.root, 'rev-parse', 'HEAD')
        self.assertEqual('', git(self.root, 'diff', '--name-only', self.base, head))
        with self.assertRaisesRegex(ValueError, '.github/workflows/ci.yml'):
            verifier.verify_preparation_history(git, self.root, self.base, head)

    def test_leading_newline_add_and_delete_cannot_alias_reviewed_path(self):
        name = '\nscripts/ci-product-checks.py'
        self.write(name, 'unreviewed disguised file\n')
        self.commit('test: add disguised path')
        (self.root / name).unlink()
        head = self.commit('test: remove disguised path')
        self.assertEqual('', git(self.root, 'diff', '--name-only', self.base, head))
        with self.assertRaisesRegex(ValueError, 'protected paths'):
            verifier.verify_preparation_history(git, self.root, self.base, head)

    def test_merge_second_parent_edge_is_checked(self):
        git(self.root, 'branch', 'product')
        self.write('.github/workflows/ci.yml', 'fresh main owned baseline\n')
        base = self.commit('test: advance main baseline')
        git(self.root, 'checkout', 'product')
        self.write('scripts/ci-product-checks.py', 'side product change\n')
        self.commit('test: change side product')
        git(self.root, 'checkout', 'main')
        git(self.root, 'merge', '--no-ff', 'product', '-m', 'test: merge product')
        with self.assertRaisesRegex(ValueError, '.github/workflows/ci.yml'):
            verifier.verify_preparation_history(git, self.root, base, git(self.root, 'rev-parse', 'HEAD'))

    def test_explicit_fetch_refreshes_main_with_custom_remote_mapping(self):
        remote = Path(self.temporary.name) / 'remote.git'
        git(self.root, 'clone', '--bare', str(self.root), str(remote))
        git(self.root, 'remote', 'add', 'origin', str(remote))
        git(self.root, 'fetch', 'origin')
        self.assertEqual(self.base, git(self.root, 'rev-parse', 'origin/main'))
        git(self.root, 'config', 'remote.origin.fetch', '+refs/heads/main:refs/remotes/origin/custom-main')
        self.write('scripts/ci-product-checks.py', 'new upstream main\n')
        upstream = self.commit('test: advance upstream')
        git(self.root, 'push', 'origin', 'main')  # Local bare fixture only.
        self.assertEqual(self.base, git(self.root, 'rev-parse', 'origin/main'))
        self.assertEqual(upstream, verifier.refresh_module_main(git, self.root))


class AdoptionTests(unittest.TestCase):
    def invoke(self, *, failure_at=None, body=None, stderr='gh: Not Found (HTTP 404)', actor=None, adopted=False):
        calls = []
        responses = [actor or verifier.EXPECTED_CI_ACCOUNT,
                     {'full_name': 'Hexalith/Hexalith.CiCd', 'default_branch': 'main'},
                     {'ref': 'refs/heads/main', 'object': {'sha': 'a' * 40, 'type': 'commit'}},
                     body or {'message': 'Not Found', 'status': '404', 'documentation_url': 'https://docs.github.com/rest/git/refs#get-a-reference'}]
        def command(arguments, *, profile, check=True):
            self.assertEqual(verifier.CI_PROFILE, profile)
            index = len(calls); calls.append(arguments)
            if index == failure_at:
                raise RuntimeError('Known access HTTP 404/403 is unverified')
            return subprocess.CompletedProcess(arguments, 0 if index < 3 or adopted else 1,
                                               json.dumps(responses[index]), '' if index < 3 or adopted else stderr)
        try:
            verifier.require_unadopted(command)
        finally:
            self.calls = calls

    def test_precise_ref_absence_requires_actor_repository_and_main_success(self):
        self.invoke()
        self.assertEqual(4, len(self.calls))
        self.assertEqual('user', self.calls[0][-1])
        self.assertTrue(self.calls[2][-1].endswith('/heads/main'))

    def test_unknown_account_and_known_access_failures_never_establish_absence(self):
        for position in range(3):
            with self.subTest(position=position), self.assertRaises(RuntimeError):
                self.invoke(failure_at=position)
            self.assertEqual(position + 1, len(self.calls))
        with self.assertRaisesRegex(ValueError, 'account is unverified'):
            self.invoke(actor={'login': 'other', 'id': 1})

    def test_other_404_authentication_errors_and_adopted_ref_fail_closed(self):
        for body, stderr in (({'message': 'Bad credentials', 'status': '401'}, 'gh: HTTP 404'),
                             ({'message': 'Not Found', 'status': '404'}, 'gh: Not Found (HTTP 404)'),
                             (None, 'unrelated HTTP 404 while reading configuration')):
            with self.subTest(body=body), self.assertRaisesRegex(ValueError, 'absence is unverified'):
                self.invoke(body=body, stderr=stderr)
        with self.assertRaisesRegex(ValueError, 'exception has expired'):
            self.invoke(adopted=True)


class CompletePreparationUnitsTests(unittest.TestCase):
    class PipelineError(Exception):
        def __init__(self, message, returncode=1):
            super().__init__(message)
            self.returncode = returncode

    def fixture(self, failures):
        from types import SimpleNamespace
        self.projects = ('tests/A.Tests/A.Tests.csproj', 'tests/B.Tests/B.Tests.csproj', 'tests/C.Tests/C.Tests.csproj')
        self.classified = SimpleNamespace(unit=self.projects)
        self.prepared = SimpleNamespace(root=Path('controlled-root'))
        self.executed = []
        def execute(root, projects, *, runner):
            self.assertEqual(self.prepared.root, root)
            self.assertEqual('controlled released runner', runner)
            self.assertEqual(1, len(projects))
            project = projects[0]
            self.executed.append(project)
            if project in failures:
                raise failures[project]
        api = SimpleNamespace(PipelineError=self.PipelineError,
                              classified_projects=mock.Mock(return_value=self.classified),
                              test_runner=mock.Mock(return_value='controlled released runner'),
                              execute_unit_projects=execute)
        return api

    def test_failed_projects_do_not_hide_later_results_and_unit_stage_still_raises(self):
        api = self.fixture({'tests/A.Tests/A.Tests.csproj': self.PipelineError('first failure', 7),
                            'tests/C.Tests/C.Tests.csproj': self.PipelineError('later failure', 9)})
        results = []
        with self.assertRaises(self.PipelineError) as failure:
            verifier.run_preparation_unit_projects(api, self.prepared, results)
        self.assertEqual(list(self.projects), self.executed)
        self.assertEqual(['failed', 'passed', 'failed'], [value['result'] for value in results])
        self.assertEqual(7, failure.exception.returncode)
        self.assertIn('first failure', str(failure.exception))
        self.assertIn('later failure', str(failure.exception))
        api.classified_projects.assert_called_once_with(self.prepared, repository='Hexalith/Hexalith.EventStore')
        api.test_runner.assert_called_once_with(self.prepared.root)

    def test_all_passing_projects_return_the_released_classification(self):
        api = self.fixture({})
        results = []
        self.assertIs(self.classified, verifier.run_preparation_unit_projects(api, self.prepared, results))
        self.assertEqual(list(self.projects), self.executed)
        self.assertEqual(['passed'] * 3, [value['result'] for value in results])

    def test_unexpected_errors_are_not_collected_or_suppressed(self):
        api = self.fixture({'tests/A.Tests/A.Tests.csproj': RuntimeError('unexpected infrastructure failure')})
        with self.assertRaisesRegex(RuntimeError, 'unexpected infrastructure failure'):
            verifier.run_preparation_unit_projects(api, self.prepared, [])
        self.assertEqual([self.projects[0]], self.executed)


class ReleasedPreparationConfigurationTests(unittest.TestCase):
    RELEASE_SHA = 'fdda17c0a4538b0f7c99f813c20ca24b49006530'

    @classmethod
    def setUpClass(cls):
        # Only the loader and schema from the immutable release are needed.
        cls.temporary = tempfile.TemporaryDirectory(prefix='eventstore-v606-contract-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.release = Path(cls.temporary.name) / 'release'
        cls.release.mkdir()
        source = verifier.ROOT / 'references/Hexalith.Builds'
        # Preserve protected safe.directory config for the real checkout while
        # ignoring repository/index overrides inherited from a hook.
        local = set(subprocess.check_output(['git', 'rev-parse', '--local-env-vars'], text=True).split())
        local -= {'GIT_CONFIG', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT'}
        env = {key: value for key, value in os.environ.items() if key not in local}
        env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1', GIT_CEILING_DIRECTORIES=str(source.parent))
        for name in ('Github/lib/ci_config.py', 'schemas/hexalith.ci.v1.json'):
            body = subprocess.check_output(['git', 'cat-file', 'blob', cls.RELEASE_SHA + ':' + name],
                                           cwd=source, env=env, timeout=30)
            destination = cls.release / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)
        spec = importlib.util.spec_from_file_location('eventstore_released_v606_config', cls.release / 'Github/lib/ci_config.py')
        cls.loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.loader)
        import jsonschema
        cls.schema_validator = jsonschema.Draft202012Validator(json.loads((cls.release / 'schemas/hexalith.ci.v1.json').read_text()))
        cls.schema_validator.check_schema(cls.schema_validator.schema)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='eventstore-stage-projection-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.plan = json.loads((Path(__file__).parent / 'fixtures/planned-configuration.json').read_text())
        self.sdk_output = '10.0.404 [/fixture/sdk]\n11.0.100 [/fixture/sdk]\n'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.calls = self.root / 'sdk-command.json'

    def project(self, plan=None):
        sdk = self.bin / 'dotnet'
        sdk.write_text(f'#!{sys.executable}\nimport json,pathlib,sys\n'
                       + f'pathlib.Path({str(self.calls)!r}).write_text(json.dumps(sys.argv[1:]))\n'
                       + f'print({self.sdk_output!r}, end="")\n')
        sdk.chmod(0o755)
        with mock.patch.dict(os.environ, {'PATH': str(self.bin) + os.pathsep + os.environ['PATH']}):
            return verifier.preparation_stage_configuration(self.plan if plan is None else plan, 'v6.0.6', process, self.root)

    def materialize_and_validate(self, configuration):
        path = self.root / 'eventstore-preparation-stages-1-3.json'
        path.write_text(json.dumps(configuration))
        loaded = self.loader.load_config(path, repository='Hexalith/Hexalith.EventStore')
        self.schema_validator.validate(json.loads(path.read_text()))
        return loaded

    def test_released_loader_and_schema_accept_materialized_projection_preserving_routes(self):
        self.plan['tests']['integration'] = ['tests/First.Integration.Tests/First.Integration.Tests.csproj',
                                             'tests/Second.Integration.Tests/Second.Integration.Tests.csproj']
        self.plan['tests']['exclude']['tests/Other.Tests/Other.Tests.csproj'] = 'after-integration-tests'
        original = deepcopy(self.plan)
        with self.assertRaises(self.loader.ConfigError):
            self.materialize_and_validate(dict(self.plan, schema='hexalith.ci.v1', buildsTag='v6.0.6'))
        configuration, report = self.project()
        self.assertEqual(configuration, self.materialize_and_validate(configuration))
        self.assertEqual(original, self.plan)
        expected = deepcopy(original['tests'])
        del expected['minimumExpectedTests'], expected['failSkips']
        expected['exclude'][verifier.AZURE_LIVE_PROJECT] = 'after-unit-tests'
        self.assertEqual(expected, configuration['tests'])
        self.assertEqual({}, configuration['jobs'])
        for key in ('solution', 'dapr', 'browsers', 'registry', 'codeql', 'hooks', 'submodules'):
            self.assertEqual(original[key], configuration[key])
        self.assertEqual(['--list-sdks'], json.loads(self.calls.read_text()))
        self.assertEqual('10.0.404', report['additional_sdk_check']['required'])
        self.assertIn('not an adoption configuration', report['scope'])
        self.assertIn('Unexecuted and authority-owned', report['azure_service_cases'])

    def test_missing_required_sdk_is_refused_using_actual_subprocess_control_output(self):
        for output in ('10.0.403 [/fixture/sdk]\n11.0.100 [/fixture/sdk]\n', 'SDK 10.0.404 is mentioned but not installed\n'):
            with self.subTest(output=output):
                self.sdk_output = output
                with self.assertRaisesRegex(ValueError, 'Required additional .NET SDK is not installed: 10.0.404'):
                    self.project()
                self.assertEqual(['--list-sdks'], json.loads(self.calls.read_text()))
        for value in (None, '', '10.0.404\nunsafe'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'exact additional SDK version'):
                self.project(dict(self.plan, additionalSdkVersion=value))

    def test_enabled_or_nondefault_unsupported_policy_is_never_dropped(self):
        for key, value in (('npmWorkspaces', ['web']), ('dotnetTools', True), ('dotnetTools', 0),
                           ('moduleManifest', 'module.json'), ('windowsCheckout', {'mode': 'sparse'})):
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, 'unsupported enabled policy'):
                self.project(dict(self.plan, **{key: value}))
        for key, value in (('minimumExpectedTests', {'tests/Some.Tests/Some.Tests.csproj': 1}),
                           ('minimumExpectedTests', []), ('failSkips', True), ('failSkips', 0)):
            plan = deepcopy(self.plan)
            plan['tests'][key] = value
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, 'unsupported enabled policy'):
                self.project(plan)

    def test_unknown_policy_is_refused_by_the_actual_released_contract(self):
        for location, key, value in (('root', 'unreviewedPreparation', False), ('root', 'aspire', True),
                                    ('tests', 'unreviewedPolicy', False)):
            plan = deepcopy(self.plan)
            (plan if location == 'root' else plan['tests'])[key] = value
            configuration, _ = self.project(plan)
            with self.subTest(key=key), self.assertRaisesRegex(self.loader.ConfigError, 'unknown keys'):
                self.materialize_and_validate(configuration)

    def test_only_exact_known_azure_job_project_and_hook_are_projected(self):
        mutations = [
            lambda plan: plan['jobs']['payload-azure'].update(preparation='setup'),
            lambda plan: plan['jobs']['payload-azure']['runner'].update(group='other-worker'),
            lambda plan: plan['jobs'].pop('payload-azure'),
            lambda plan: plan['tests']['exclude'].update({verifier.AZURE_LIVE_PROJECT: 'after-integration-tests'}),
            lambda plan: plan['tests']['exclude'].update({'tests/Other.LiveTests/Other.LiveTests.csproj': 'payload-azure'}),
            lambda plan: plan['hooks'].remove('after-unit-tests'),
        ]
        for mutation in mutations:
            plan = deepcopy(self.plan)
            mutation(plan)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'exact Azure live project'):
                self.project(plan)
        plan = deepcopy(self.plan)
        plan['jobs']['unknown-manual'] = deepcopy(plan['jobs']['payload-azure'])
        with self.assertRaisesRegex(ValueError, 'exact Azure live project'):
            self.project(plan)
        plan = deepcopy(self.plan)
        plan['jobs']['legacy-windows'] = {'runner': 'windows-latest'}
        plan['tests']['exclude']['tests/Ordinary.Tests/Ordinary.Tests.csproj'] = 'legacy-windows'
        with self.assertRaisesRegex(ValueError, 'exact Azure live project'):
            self.project(plan)


if __name__ == '__main__':
    unittest.main()
