"""Prepare fresh-main publication trees without changing shared indexes or refs."""
from pathlib import Path
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SCRATCH = Path(os.environ['TMPDIR'])
POLICY = 'fdda17c0a4538b0f7c99f813c20ca24b49006530'
OWNED = ['.github/workflows', '.github/dependabot.yml', '.github/hexalith-ci.json',
         'references/Hexalith.Builds', '.gitmodules', 'AGENTS.md', 'CLAUDE.md',
         '.github/copilot-instructions.md', '.claude', 'commitlint.config.mjs', '.releaserc.json']
RESULT = {'policyTag': 'v6.0.6', 'policyCommit': POLICY, 'repositories': {}}

def git(path, *args, env=None, payload=None, check=True):
    r = subprocess.run(['git', '-c', 'submodule.recurse=false', '-C', str(path), *args],
                       env=env, input=payload, capture_output=True, check=check)
    return r.stdout if check else r

def save():
    (OUT / 'prepared-candidates.json').write_text(json.dumps(RESULT, indent=2) + '\n')

archive = git(ROOT / 'references/Hexalith.Builds', 'archive', POLICY, 'Github/guard', 'Github/lib')
policy = SCRATCH / 'released-policy'
policy.mkdir()
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    tar.extractall(policy, filter='data')
sys.dont_write_bytecode = True
sys.path.insert(0, str(policy / 'Github/lib'))
import audit_lint
import expected_state
import guard_actions
from guard_tools import Tools

tools_path = SCRATCH / 'tools'
tools_path.mkdir()
tools = Tools(tools_path)
RESULT['lockedToolInstallation'] = 'passed'
RESULT['toolSignatures'] = 'passed'
RESULT['toolLockSha256'] = hashlib.sha256((policy / 'Github/guard/package-lock.json').read_bytes()).hexdigest()
RESULT['nodeVersion'] = subprocess.check_output(['node', '--version'], text=True).strip()
save()

messages = {
    'Hexalith.Platform': 'fix(test): manage complete component fixture lifetime\n',
    'Hexalith.Folders': 'fix(test): qualify package-bound component fixtures\n',
    'Hexalith.CiCd': 'build(cicd): record publication preparation and verification\n',
}
for name, message in messages.items():
    source = ROOT if name == 'Hexalith.CiCd' else ROOT / 'references' / name
    head = git(source, 'rev-parse', 'HEAD').decode().strip()
    base = git(source, 'rev-parse', 'origin/main').decode().strip()
    index = SCRATCH / (name + '.index')
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    git(source, 'read-tree', head, env=env)
    git(source, 'add', '--all', env=env)
    captured_tree = git(source, 'write-tree', env=env).decode().strip()
    patch = git(source, 'diff', '--binary', head, captured_tree)
    candidate = SCRATCH / name
    git(ROOT, 'clone', '--quiet', '--shared', '--no-checkout', '--no-recurse-submodules', str(source), str(candidate))
    git(candidate, 'checkout', '--quiet', '--detach', base)
    row = {'sourceHead': head, 'freshBase': base, 'capturedSourceTree': captured_tree,
           'sourceHeadUnchangedAfterCapture': head == git(source, 'rev-parse', 'HEAD').decode().strip()}
    RESULT['repositories'][name] = row
    applied = git(candidate, 'apply', '--3way', '--index', '-', payload=patch, check=False)
    row['applyExit'] = applied.returncode
    if applied.returncode:
        row['applyDiagnostics'] = applied.stderr.decode(errors='replace')
        save()
        continue
    tree = git(candidate, 'write-tree').decode().strip()
    row['candidateTree'] = tree
    row['changedPaths'] = git(candidate, 'diff', '--name-only', base, tree).decode().splitlines()
    row['ownedTreePreserved'] = git(candidate, 'ls-tree', '-r', base, '--', *OWNED) == git(candidate, 'ls-tree', '-r', tree, '--', *OWNED)
    proposed_patch = git(candidate, 'diff', '--binary', base, tree)
    (OUT / (name + '.patch')).write_bytes(proposed_patch)
    row['patchSha256'] = hashlib.sha256(proposed_patch).hexdigest()
    (OUT / (name + '-message.txt')).write_text(message)
    tools.lint_message(message, name + ' proposed commit')
    row['exactMessageCommitlint'] = 'passed'
    snapshot = expected_state.tree_snapshot(expected_state.Git(candidate), tree)
    for label, operation in [('releasedAudit', lambda: audit_lint.lint(snapshot)),
                             ('releasedActionLint', lambda: guard_actions.lint(snapshot, tools))]:
        try:
            operation()
            row[label] = 'passed'
        except Exception as error:
            row[label] = str(error)
    save()
    print(json.dumps({'repository': name, **row}), flush=True)
