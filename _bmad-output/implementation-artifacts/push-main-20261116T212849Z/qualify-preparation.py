#!/usr/bin/env python3
"""Inspect exact preparation candidates without changing the shared worktrees."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SCRATCH = Path(os.environ['TMPDIR'])
assert SCRATCH.is_dir() and SCRATCH != Path('/tmp'), 'Use run-with-temp'
REPORT = {'status': 'running', 'commitsCreated': False, 'pushesAttempted': False,
          'modules': {}, 'releasedPolicy': {}}


def run(argv, cwd=ROOT, *, env=None, payload=None):
    return subprocess.run(argv, cwd=cwd, env=env, input=payload,
                          capture_output=True, check=False)


def git(repository, *args, env=None):
    r = run(['git', '-c', 'submodule.recurse=false', *args], repository, env=env)
    if r.returncode:
        raise RuntimeError(r.stderr.decode(errors='replace'))
    return r.stdout


def save():
    (OUT / 'qualification.json').write_text(json.dumps(REPORT, indent=2) + '\n')


def clone(source, destination, revision):
    git(ROOT, 'clone', '--quiet', '--shared', '--no-checkout',
        '--no-recurse-submodules', str(source), str(destination))
    git(destination, 'checkout', '--quiet', '--detach', revision)


def candidate(name):
    source = ROOT / 'references' / ('Hexalith.' + name)
    head = git(source, 'rev-parse', 'HEAD').decode().strip()
    base = git(source, 'rev-parse', 'origin/main').decode().strip()
    environment = dict(os.environ, GIT_INDEX_FILE=str(SCRATCH / (name + '.index')))
    git(source, 'read-tree', head, env=environment)
    git(source, 'add', '--all', env=environment)
    patch = git(source, 'diff', '--cached', '--binary', head, env=environment)
    (OUT / (name + '-pending.patch')).write_bytes(patch)
    target = SCRATCH / ('Hexalith.' + name)
    clone(source, target, base)
    item = REPORT['modules'][name] = {
        'sourceHead': head, 'freshMain': base,
        'pendingPatchSha256': hashlib.sha256(patch).hexdigest(),
        'sourceStatus': git(source, 'status', '--porcelain=v1', '--untracked-files=all').decode(),
        'normalCheckerApplicable': False, 'approvedPreparationSubstitute': True,
        'sourceIndexPreserved': True, 'checks': {},
    }
    r = run(['git', 'apply', '--3way', '--index', '--binary', '-'], target, payload=patch)
    (OUT / (name + '-fresh-main-apply.txt')).write_bytes(r.stdout + r.stderr)
    if r.returncode:
        item['checks']['freshMainApplication'] = {'exitCode': r.returncode,
                                                  'log': name + '-fresh-main-apply.txt'}
        return None, item
    item['checks']['freshMainApplication'] = 'pass'
    tree = git(target, 'write-tree').decode().strip()
    item['candidateTree'] = tree
    (OUT / (name + '-candidate.patch')).write_bytes(git(target, 'diff', '--cached', '--binary', base))
    owned = ['.github/workflows', '.github/dependabot.yml', '.github/hexalith-ci.json',
             'references/Hexalith.Builds', '.gitmodules', 'AGENTS.md', 'CLAUDE.md',
             '.github/copilot-instructions.md', '.claude', 'commitlint.config.mjs', '.releaserc.json']
    before = git(target, 'ls-tree', '-r', base, '--', *owned)
    after = git(target, 'ls-tree', '-r', tree, '--', *owned)
    item['checks']['ownedContentPreserved'] = before == after
    (OUT / (name + '-owned-before.txt')).write_bytes(before)
    (OUT / (name + '-owned-after.txt')).write_bytes(after)
    return target, item


try:
    builds = ROOT / 'references/Hexalith.Builds'
    policy_revision = git(builds, 'rev-parse', 'refs/tags/v6.0.6^{commit}').decode().strip()
    policy = SCRATCH / 'released-Builds'
    clone(builds, policy, policy_revision)
    environment = dict(os.environ, GH_CONFIG_DIR='/home/administrator/.config/gh-cicd-agent')
    r = run(['gh', 'api', 'repos/Hexalith/Hexalith.Builds/releases/tags/v6.0.6',
             '--jq', '{tag_name,immutable,draft,prerelease,published_at,html_url}'], env=environment)
    (OUT / 'released-policy-proof.json').write_bytes(r.stdout)
    proof = json.loads(r.stdout) if not r.returncode else {}
    REPORT['releasedPolicy'] = {'tag': 'v6.0.6', 'revision': policy_revision,
                                'releaseReadExitCode': r.returncode, 'release': proof}
    if r.returncode or proof.get('draft') or proof.get('prerelease'):
        raise RuntimeError('Acceptable released-policy proof unavailable')
    sys.path.insert(0, str(policy / 'Github/lib'))
    import audit_lint
    import expected_state
    import guard_actions
    from guard_tools import Tools, SOURCE
    REPORT['releasedPolicy']['toolLockSha256'] = hashlib.sha256((SOURCE / 'package-lock.json').read_bytes()).hexdigest()
    tools = None
    for name in ('Folders', 'Projects'):
        target, item = candidate(name)
        save()
        if target is None:
            continue
        snapshot = expected_state.tree_snapshot(expected_state.Git(target), item['candidateTree'])
        try:
            audit_lint.lint(snapshot)
            item['checks']['releasedAudit'] = 'pass'
        except Exception as error:
            item['checks']['releasedAudit'] = {'error': str(error)}
        try:
            if tools is None:
                tools_root = SCRATCH / 'guard-tools'
                tools_root.mkdir()
                tools = Tools(tools_root)
                REPORT['releasedPolicy']['lockedToolsAndSignatureVerification'] = 'pass'
            guard_actions.lint(snapshot, tools)
            item['checks']['releasedActions'] = 'pass'
        except Exception as error:
            item['checks']['releasedActions'] = {'error': str(error)}
        item['status'] = 'policy-preflight-only; complete product qualification still required'
        save()
        print(json.dumps({'module': name, 'tree': item['candidateTree'], 'checks': item['checks']}), flush=True)
    REPORT['status'] = 'preflight finished; not publication approval'
except Exception as error:
    REPORT['status'] = 'preflight failed'
    REPORT['error'] = str(error)
    raise
finally:
    save()
