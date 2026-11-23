"""Real Git/worktree write controls for the committed CiCd maintenance profile."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from copy import deepcopy

# The candidate supplies only blobs committed at its HEAD. Its remotes,
# branches and config never select the owner: the nightly bump's scratch
# checkout is `git init` with no remotes, and an Actions checkout has its own.
CANDIDATE = Path(__file__).resolve().parents[2]
# Only objects are read from the Builds reference: the frozen 4.44.x base and
# the registration base (a bare, remote-less repository in the bump scratch).
# The override lets a scratch copy of the candidate use another Builds clone.
SOURCE = Path(os.environ.get('MAINTENANCE_BUILDS_SOURCE', CANDIDATE / 'references/Hexalith.Builds')).resolve()
# An inherited GIT_DIR, GIT_INDEX_FILE, etc. (for example from a Git hook)
# would point the fixture and the tool at another repository.
GIT_LOCAL = subprocess.check_output(['git', 'rev-parse', '--local-env-vars'], text=True).split()
GIT_CONFIG_ENV = {'GIT_CONFIG', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT'}
# The actual sources may need caller-provided safe.directory configuration.
SOURCE_ENV = {key: value for key, value in os.environ.items() if key not in GIT_LOCAL or key in GIT_CONFIG_ENV}
spec = importlib.util.spec_from_file_location('maintenance', CANDIDATE / 'tools/maintenance.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
OWNER_ORIGIN = 'https://github.com/Hexalith/Hexalith.CiCd.git'
FOREIGN_ORIGIN = 'https://github.com/Other/Repo.git'
IDENTITY = {'GIT_AUTHOR_NAME': 'Maintenance fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
            'GIT_COMMITTER_NAME': 'Maintenance fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'}


def git(cwd, *arguments, data=None, env=None):
    result = subprocess.run(['git', *arguments], cwd=cwd, input=data, env=env, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(f"git {' '.join(arguments)} failed: {result.stderr.decode()}")
    return result.stdout


def committed(relative):
    return git(CANDIDATE, 'cat-file', 'blob', 'HEAD:' + relative, env=SOURCE_ENV)


POLICY_BYTES = committed(tool.POLICY)
POLICY = json.loads(POLICY_BYTES)
TEMPLATES = sorted({entry['template'] for profiles in POLICY['ownedOutputs'].values()
                    for profile in profiles.values() for entry in profile['files'].values()})
OWNED = {relative: committed(relative) for relative in ('tools/maintenance.py', tool.POLICY, *TEMPLATES)}
REPOSITORY = 'Hexalith/Hexalith.Builds'
BASE = POLICY['lanes'][REPOSITORY]['baseRevision']
CI_TEMPLATE = POLICY['ownedOutputs'][REPOSITORY]['maintenance']['files']['.github/workflows/ci.yml']['template']


def make_owner(directory, origin=OWNER_ORIGIN, changes=None):
    """Commit the candidate's owned inputs, plus any changes, into a new owner repository."""
    git(directory.parent, 'init', '--quiet', '--template=', '--object-format=sha1', '--initial-branch=main', str(directory))
    entries = []
    for relative, content in sorted({**OWNED, **(changes or {})}.items()):
        blob = git(directory, 'hash-object', '-w', '--stdin', data=content).decode().strip()
        entries.append(f'100644 {blob}\t{relative}\n')
    git(directory, 'update-index', '--add', '--index-info', data=''.join(entries).encode())
    tree = git(directory, 'write-tree').decode().strip()
    revision = git(directory, 'commit-tree', '--no-gpg-sign', '-m', 'maintenance owner fixture', tree).decode().strip()
    git(directory, 'update-ref', 'refs/heads/main', revision)
    git(directory, 'remote', 'add', 'origin', origin)
    return directory, revision


class MaintenanceWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        # The ceiling stops discovery at SOURCE: an uninitialized Builds
        # directory fails here instead of borrowing the candidate's objects.
        cls.objects = git(SOURCE, 'rev-parse', '--path-format=absolute', '--git-path', 'objects',
                          env={**SOURCE_ENV, 'GIT_CEILING_DIRECTORIES': str(SOURCE.parent)})
        # From here on, every Git call (including those in the renderer) is
        # against a disposable repository owned by the fixture.
        fixture_env = {key: value for key, value in SOURCE_ENV.items() if not key.startswith('GIT_')}
        fixture_env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', **IDENTITY)
        cls.enterClassContext(patch.dict(os.environ, fixture_env, clear=True))
        cls.owner = make_owner(Path(temporary.name) / 'owner')

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.target = self.root / 'target'
        self.output = self.root / 'output'
        # A clone without refs: the target borrows the Builds objects and
        # names only its own origin and branch.
        self.run_git('init', '--quiet', '--template=', '--object-format=sha1', str(self.target), cwd=self.root)
        alternates = self.target / '.git/objects/info/alternates'
        alternates.parent.mkdir(parents=True, exist_ok=True)
        alternates.write_bytes(self.objects)
        self.run_git('remote', 'add', 'origin', 'https://github.com/Hexalith/Hexalith.Builds.git')
        self.run_git('-c', 'submodule.recurse=false', 'checkout', '-b', '4.44.x', BASE)
        self.workflow = self.target / '.github/workflows/ci.yml'
        self.before = self.workflow.read_bytes()

    def run_git(self, *arguments, cwd=None):
        return git(cwd or self.target, *arguments)

    def execute(self, apply=True, role='maintenance', revision=BASE, owner=None):
        directory, owner_revision = owner or self.owner
        return tool.render(directory, owner_revision, self.target, revision, REPOSITORY, role, self.output, apply=apply)

    def snapshot(self):
        workflows = {str(path.relative_to(self.target)): path.read_bytes()
                     for path in (self.target / '.github/workflows').glob('*.yml') if not path.is_symlink()}
        outputs = None
        if self.output.exists():
            outputs = {str(path.relative_to(self.output)):
                       os.readlink(path) if path.is_symlink() else path.read_bytes() if path.is_file() else None
                       for path in self.output.rglob('*')}
        return workflows, outputs, self.run_git('ls-files', '--stage', '-v', '-z')

    def refused_without_overwrite(self, reason, **arguments):
        before = self.snapshot()
        with self.assertRaisesRegex(tool.MaintenanceError, re.escape(reason)):
            self.execute(**arguments)
        self.assertEqual(self.snapshot(), before)

    def test_exact_named_branch_applies_only_committed_owned_templates(self):
        receipt = self.execute()
        self.assertEqual(receipt['branch'], '4.44.x')
        self.assertEqual(receipt['ownerSource'], self.owner[1])
        self.assertEqual(receipt['ownerPolicySha256'], hashlib.sha256(POLICY_BYTES).hexdigest())
        self.assertEqual(receipt['intendedBranch'], '4.44.x')
        self.assertFalse(receipt['detachedProposal'])
        for relative, entry in POLICY['ownedOutputs'][REPOSITORY]['maintenance']['files'].items():
            self.assertEqual((self.target / relative).read_bytes(), OWNED[entry['template']])
        self.assertTrue((self.output / 'maintenance-delivery.json').is_file())

    def test_detached_render_is_labelled_and_cannot_apply(self):
        self.run_git('-c', 'submodule.recurse=false', 'checkout', '--detach', BASE)
        receipt = self.execute(apply=False)
        self.assertIsNone(receipt['branch'])
        self.assertTrue(receipt['detachedProposal'])
        self.refused_without_overwrite('maintenance apply requires the actual approved named branch')

    def test_another_named_branch_cannot_claim_the_maintenance_lane(self):
        self.run_git('checkout', '-b', 'other')
        self.refused_without_overwrite('maintenance apply requires the actual approved named branch')

    def test_staged_owned_content_is_preserved(self):
        self.workflow.write_bytes(self.before + b'\n# incoming staged edit\n')
        self.run_git('add', '.github/workflows/ci.yml')
        self.refused_without_overwrite('owned target paths have staged, unstaged, deleted or untracked changes')

    def test_unstaged_owned_content_is_preserved(self):
        self.workflow.write_bytes(self.before + b'\n# incoming worktree edit\n')
        self.refused_without_overwrite('owned target paths have staged, unstaged, deleted or untracked changes')

    def test_tracked_worktree_deletion_is_preserved(self):
        self.workflow.unlink()
        self.refused_without_overwrite('owned target paths have staged, unstaged, deleted or untracked changes')
        self.assertFalse(self.workflow.exists())

    def test_staged_deletion_is_preserved(self):
        self.run_git('rm', '.github/workflows/ci.yml')
        self.refused_without_overwrite('owned target paths have staged, unstaged, deleted or untracked changes')
        self.assertFalse(self.workflow.exists())

    def test_staged_mode_change_is_preserved(self):
        self.run_git('update-index', '--chmod=+x', '.github/workflows/ci.yml')
        self.refused_without_overwrite('owned target paths have staged, unstaged, deleted or untracked changes')

    def test_executable_worktree_mode_refuses_even_when_git_ignores_filemode(self):
        self.run_git('config', 'core.filemode', 'false')
        self.workflow.chmod(0o755)
        self.refused_without_overwrite('owned target path is untracked, nonregular or has a changed mode')
        self.assertTrue(self.workflow.stat().st_mode & 0o111)

    def test_empty_untracked_registration_workflow_is_preserved(self):
        revision = POLICY['ownedOutputs'][REPOSITORY]['registration']['baseRevision']
        self.run_git('-c', 'submodule.recurse=false', 'checkout', '--detach', revision)
        self.run_git('update-ref', 'refs/remotes/origin/main', revision)
        self.run_git('checkout', '-b', 'fix/registration-fixture')
        created = self.target / '.github/workflows/build-release.yml'
        self.assertFalse(created.exists())
        created.touch()
        self.refused_without_overwrite('owned target paths have staged, unstaged, deleted or untracked changes',
                                       role='registration', revision=revision)
        self.assertEqual(created.read_bytes(), b'')

    def test_foreign_target_origin_refuses_before_any_write(self):
        self.run_git('remote', 'set-url', 'origin', FOREIGN_ORIGIN)
        self.refused_without_overwrite('foreign owner or target origin')

    def test_foreign_owner_origin_refuses_before_any_write(self):
        owner = make_owner(self.root / 'foreign-owner', origin=FOREIGN_ORIGIN)
        self.refused_without_overwrite('foreign owner or target origin', owner=owner)

    def test_abbreviated_owner_and_target_revisions_refuse(self):
        directory, revision = self.owner
        for arguments in ({'owner': (directory, revision[:12])}, {'revision': BASE[:12]}):
            with self.subTest(arguments=arguments):
                self.refused_without_overwrite('full immutable Git revisions are required', **arguments)

    def test_target_head_differs_from_selected_revision(self):
        other = POLICY['ownedOutputs'][REPOSITORY]['registration']['baseRevision']
        self.refused_without_overwrite('target checkout differs from the selected source', revision=other)

    def test_registration_proposal_requires_current_main(self):
        revision = POLICY['ownedOutputs'][REPOSITORY]['registration']['baseRevision']
        self.run_git('-c', 'submodule.recurse=false', 'checkout', '--detach', revision)
        self.run_git('update-ref', 'refs/remotes/origin/main', BASE)
        self.refused_without_overwrite('registration delivery requires the freshly selected current main',
                                       role='registration', revision=revision, apply=False)

    def test_changed_incoming_workflow_requires_new_policy(self):
        self.workflow.write_bytes(self.before + b'\n# committed upstream change\n')
        self.run_git('add', '.github/workflows/ci.yml')
        self.run_git('commit', '-m', 'Changed incoming workflow')
        revision = self.run_git('rev-parse', 'HEAD').decode().strip()
        self.refused_without_overwrite('incoming owned workflow changed', revision=revision)

    def test_uncommitted_workflow_hidden_from_status_is_preserved(self):
        self.run_git('update-index', '--assume-unchanged', '.github/workflows/ci.yml')
        self.workflow.write_bytes(self.before + b'\n# local workflow edit\n')
        self.refused_without_overwrite('uncommitted target workflow would be overwritten')

    def test_unrelated_preparation_output_is_preserved(self):
        occupied = self.output / '.github/workflows/ci.yml'
        occupied.parent.mkdir(parents=True)
        occupied.write_bytes(b'unrelated preparation')
        self.refused_without_overwrite('an unrelated preparation output would be overwritten', apply=False)

    def test_unrelated_receipt_is_preserved_before_apply(self):
        self.output.mkdir()
        (self.output / 'maintenance-delivery.json').write_bytes(b'unrelated receipt')
        self.refused_without_overwrite('an unrelated delivery receipt would be overwritten')

    def test_policy_cannot_write_outside_its_workflow_scope(self):
        for name in ('other.yml', '.github/workflows/ci.txt'):
            with self.subTest(name=name):
                policy = deepcopy(POLICY)
                files = policy['ownedOutputs'][REPOSITORY]['maintenance']['files']
                files[name] = files.pop('.github/workflows/ci.yml')
                owner = make_owner(self.root / Path(name).stem, changes={tool.POLICY: json.dumps(policy).encode()})
                self.refused_without_overwrite('policy attempts to write outside its exact owned workflow scope', owner=owner)
                self.assertFalse((self.target / name).exists())

    def test_changed_executing_tool_refuses_before_any_write(self):
        changed = {'tools/maintenance.py': OWNED['tools/maintenance.py'] + b'\n# changed owner tool\n'}
        owner = make_owner(self.root / 'changed-tool', changes=changed)
        self.refused_without_overwrite('executing maintenance tool differs from its committed owner revision', owner=owner)

    def test_changed_policy_hash_refuses_before_any_write(self):
        policy = deepcopy(POLICY)
        policy['ownedOutputs'][REPOSITORY]['maintenance']['files']['.github/workflows/ci.yml']['sha256'] = '0' * 64
        cases = {'template': {CI_TEMPLATE: OWNED[CI_TEMPLATE] + b'\n# changed template\n'},
                 'recorded hash': {tool.POLICY: (json.dumps(policy, indent=2) + '\n').encode()}}
        for name, changes in cases.items():
            with self.subTest(name):
                owner = make_owner(self.root / ('changed-' + name.replace(' ', '-')), changes=changes)
                self.refused_without_overwrite('committed owned template differs from the policy hash', owner=owner)

    def test_late_output_symlink_does_not_allow_an_earlier_output_write(self):
        directory = self.output / '.github/workflows'
        directory.mkdir(parents=True)
        (directory / 'build-release.yml').symlink_to(self.workflow)
        self.refused_without_overwrite('owned paths cannot traverse symlinks', apply=False)
        self.assertFalse((directory / 'ci.yml').exists())

    def test_receipt_symlink_refuses_before_any_target_write(self):
        self.output.mkdir()
        marker = self.root / 'foreign-marker'; marker.write_bytes(b'unchanged')
        (self.output / 'maintenance-delivery.json').symlink_to(marker)
        self.refused_without_overwrite('owned paths cannot traverse symlinks')
        self.assertEqual(marker.read_bytes(), b'unchanged')

    def test_unrelated_dirty_content_is_preserved(self):
        unrelated = self.target / 'unrelated-task.txt'; unrelated.write_bytes(b'user changes')
        self.execute()
        self.assertEqual(unrelated.read_bytes(), b'user changes')


class FixtureConfigurationTests(unittest.TestCase):
    def test_render_with_global_url_rewrite_and_crlf_conversion(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / 'gitconfig'
            for key, value in (('safe.directory', str(CANDIDATE)), ('safe.directory', str(SOURCE)),
                               ('url.ssh://fixture.invalid/.insteadOf', 'https://github.com/'),
                               ('core.autocrlf', 'true')):
                git(CANDIDATE, 'config', '--file', str(config), '--add', key, value, env=SOURCE_ENV)
            env = dict(SOURCE_ENV, GIT_CONFIG_GLOBAL=str(config), GIT_TEST_ASSUME_DIFFERENT_OWNER='1')
            case = 'MaintenanceWriteTests.test_exact_named_branch_applies_only_committed_owned_templates'
            result = subprocess.run([sys.executable, '-B', __file__, case], env=env,
                                    text=True, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)


class ProductionEnvironmentTests(unittest.TestCase):
    """The environment addition reads only the committed policy and a mocked API."""

    def test_environment_addition_is_one_exact_branch_with_reviewers_unchanged(self):
        environment = {'protection_rules': [{'type': 'required_reviewers', 'reviewers': [{'type': 'User', 'id': 1}]}],
                       'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True},
                       'can_admins_bypass': False}
        existing = {'id': 1, 'name': 'main', 'type': 'branch'}
        created = {'id': 2, 'name': '4.44.x', 'type': 'branch'}
        calls = []
        def api(method, endpoint, payload=None):
            calls.append((method, endpoint, payload))
            if method == 'POST':
                self.assertEqual(payload, {'name': '4.44.x', 'type': 'branch'})
                return deepcopy(created)
            if endpoint.endswith('/production'):
                return deepcopy(environment)
            policies = [existing, created] if any(call[0] == 'POST' for call in calls) else [existing]
            return {'total_count': len(policies), 'branch_policies': deepcopy(policies)}
        receipt = tool.production_branch(api, POLICY, apply=True)
        self.assertTrue(receipt['applied'])
        self.assertTrue(receipt['reviewersUnchanged'])
        self.assertEqual(len([call for call in calls if call[0] == 'POST']), 1)

    def test_missing_required_reviewers_cannot_be_repaired_by_environment_mutation(self):
        calls = []
        def api(method, endpoint, payload=None):
            calls.append(method)
            return {'protection_rules': [], 'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True}}
        with self.assertRaisesRegex(tool.MaintenanceError, 'the existing production reviewer/branch policy must remain enabled'):
            tool.production_branch(api, POLICY, apply=True)
        self.assertEqual(calls, ['GET'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
