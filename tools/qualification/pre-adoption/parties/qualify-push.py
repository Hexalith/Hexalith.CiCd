#!/usr/bin/env python3
"""Qualify the exact Parties preparation tree and commit messages before push."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FIXTURES = HERE / 'fixtures'
OUTPUT = Path(os.environ['TMPDIR']) / 'parties-publication-results'
OUTPUT.mkdir(parents=True, exist_ok=True)
MODULE = ROOT / 'references/Hexalith.Parties'
BUILDS = ROOT / 'references/Hexalith.Builds'
BASE = 'a575021fc97a8eda664711089270b60f5e570ded'


def git(*args, environment=None):
    return subprocess.check_output(['git', *args], cwd=MODULE, env=environment)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


record = {'module_base': BASE, 'result': 'failed'}
try:
    require(git('rev-parse', 'HEAD').decode().strip() == BASE, 'module HEAD differs from the frozen base')
    require(git('rev-parse', 'origin/main').decode().strip() == BASE, 'origin/main differs from the frozen base')
    require(not git('diff', '--name-only'), 'module has unstaged changes')
    state = json.loads((FIXTURES / 'current-preparation-state.json').read_text())
    accepted = json.loads((FIXTURES / 'accepted-local-verification.json').read_text())
    require(state['patch_sha256'] == accepted['final_patch_sha256'], 'preparation patch differs from accepted digest')
    patch = (FIXTURES / 'current-preparation.patch').read_bytes()
    require(sha(patch) == state['patch_sha256'], 'current-preparation.patch digest mismatch')
    normalization = json.loads((FIXTURES / 'whitespace-normalization.json').read_text())
    with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as temporary:
        temporary = Path(temporary)
        environment = dict(os.environ, GIT_INDEX_FILE=str(temporary / 'expected.index'))
        git('read-tree', BASE, environment=environment)
        subprocess.run(['git', 'apply', '--cached', '--binary', '-'], input=patch,
                       cwd=MODULE, env=environment, check=True, capture_output=True)
        unit = json.loads((FIXTURES / accepted['unit_run'] / 'unit-only-preparation.json').read_text())
        for name, revision in unit['dependencies'].items():
            path = 'references/' + name
            actual_pin = git('ls-files', '--stage', '--', path).decode().split()
            require(actual_pin[:2] == ['160000', revision], f'dependency pin mismatch: {path}')
            git('update-index', '--cacheinfo', '160000', revision, path, environment=environment)
        record['verified_dependency_revisions'] = unit['dependencies']
        for item in state['untracked_inputs']:
            path = MODULE / item['path']
            body = path.read_bytes()
            if item['path'] == normalization['path']:
                require(item['sha256'] == normalization['before_sha256'], 'normalization input digest mismatch')
                require(sha(body) == normalization['after_sha256'], 'normalized source digest mismatch')
            else:
                require(sha(body) == item['sha256'], item['path'])
            require(oct(path.stat().st_mode & 0o777) == item['mode'], f"source mode mismatch: {item['path']}")
            blob = subprocess.check_output(['git', 'hash-object', '-w', '--stdin'],
                                           cwd=MODULE, input=body).decode().strip()
            mode = '100755' if path.stat().st_mode & 0o100 else '100644'
            git('update-index', '--add', '--cacheinfo', mode, blob, item['path'], environment=environment)
        expected_tree = git('write-tree', environment=environment).decode().strip()
        tree = git('write-tree').decode().strip()
        require(tree == expected_tree, f'staged tree {tree} differs from expected {expected_tree}')
        record.update(tree=tree, exact_verified_inputs=True, whitespace_only_adjustment=normalization)

        sys.path.insert(0, str(BUILDS / 'Github/lib'))
        import audit_lint
        import expected_state
        import guard_actions
        from guard_tools import Tools, SOURCE

        snapshot = expected_state.tree_snapshot(expected_state.Git(MODULE), tree)
        audit_lint.lint(snapshot)
        record['released_audit_lint'] = 'pass'
        tools_dir = temporary / 'tools'
        tools_dir.mkdir()
        tools = Tools(tools_dir)
        guard_actions.lint(snapshot, tools)
        record['released_action_lint'] = 'pass'
        record['builds_revision'] = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=BUILDS).decode().strip()
        record['tools_lock_sha256'] = sha((SOURCE / 'package-lock.json').read_bytes())
        module_config = MODULE / 'commitlint.config.mjs'
        copied_config = tools_dir / 'module-commitlint.config.mjs'
        shutil.copyfile(module_config, copied_config)
        messages = {
            'parties': 'build(cicd): prepare Parties shared pipeline migration\n',
            'cicd': 'build(cicd): record Parties migration preparation\n',
        }
        record['messages'] = {}
        for name, message in messages.items():
            path = OUTPUT / (name + '-commit-message.txt')
            path.write_text(message)
            tools.lint_message(message, name)
            if name == 'parties':
                result = tools._process([
                    'node', str(tools_dir / 'node_modules/@commitlint/cli/cli.js'),
                    '--config', str(copied_config), '--color=false'],
                    'owning repository commitlint', message)
                require(result.returncode == 0, result.stdout + result.stderr)
            record['messages'][name] = {'message': message, 'result': 'pass'}
        record.update(result='pass', locked_install=True, signatures_verified=True,
                      existing_product_test_evidence=str(FIXTURES / 'accepted-local-verification.json'),
                      owned_files_unchanged=state['owned_files_unchanged'])
except Exception as error:
    record['error'] = str(error)
    raise
finally:
    (OUTPUT / 'pre-push-qualification.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
