"""Qualify exact publication commits in disposable, isolated checkouts."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

OUTPUT = Path(__file__).resolve().parent
ROOT = Path('/home/administrator/projects/hexalith/cicd-publish-story-14')
SCRATCH = Path(os.environ['TMPDIR'])
parser = argparse.ArgumentParser()
parser.add_argument('component', choices=['builds', 'agents'])
args = parser.parse_args()
report = {'component': args.component, 'commands': []}
result_file = OUTPUT / (args.component + '-qualification.json')


def git(root, *arguments):
    return subprocess.check_output(['git', *arguments], cwd=root)


def run(label, command, cwd, *, expected=None):
    log = OUTPUT / (label + '.log')
    environment = {**os.environ, 'npm_config_cache': str(SCRATCH / 'npm-cache')}
    with log.open('w') as output:
        result = subprocess.run(command, cwd=cwd, env=environment,
                                stdout=output, stderr=subprocess.STDOUT)
    report['commands'].append({'label': label, 'command': command,
                               'exitCode': result.returncode, 'log': log.name})
    result_file.write_text(json.dumps(report, indent=2) + '\n')
    print(label + ': ' + str(result.returncode), flush=True)
    if expected is None and result.returncode:
        raise SystemExit(result.returncode)
    if expected is not None:
        expected(result.returncode, log.read_text())


def clone(source, destination):
    revision = git(source, 'rev-parse', 'HEAD').decode().strip()
    subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-recurse-submodules',
                    str(source), str(destination)], check=True)
    subprocess.run(['git', 'checkout', '--quiet', '--detach', revision], cwd=destination, check=True)
    return revision


if args.component == 'builds':
    checkout = SCRATCH / 'Builds'
    report['head'] = clone(ROOT / 'references/Hexalith.Builds', checkout)
    run('builds-node-install', ['npm', 'ci', '--ignore-scripts'], checkout)
    run('builds-node-signatures', ['npm', 'audit', 'signatures'], checkout)
    for version in ['3.12', '3.14']:
        run('builds-library-python' + version.replace('.', ''), [
            'uv', 'run', '--no-cache', '--python', version,
            '--with', 'jsonschema==4.26.0', '--with', 'PyYAML==6.0.3',
            'python', '-B', '-m', 'unittest', 'discover', '-s', 'Github/lib/tests', '-v',
        ], checkout)
else:
    module = SCRATCH / 'Agents'
    report['head'] = clone(ROOT / 'references/Hexalith.Agents', module)
    integration = json.loads((OUTPUT / 'integration.json').read_text())
    base = integration['repositories']['Hexalith.Agents']['base']
    report['freshMainBase'] = base
    subprocess.run(['git', 'remote', 'set-url', 'origin',
                    'https://github.com/Hexalith/Hexalith.Agents.git'], cwd=module, check=True)
    subprocess.run(['git', 'update-ref', 'refs/remotes/origin/main', base], cwd=module, check=True)
    builds = module / 'references/Hexalith.Builds'
    shared = clone(ROOT / 'references/Hexalith.Builds', builds)
    pinned = git(module, 'rev-parse', 'HEAD:references/Hexalith.Builds').decode().strip()
    subprocess.run(['git', 'checkout', '--quiet', '--detach', pinned], cwd=builds, check=True)
    report.update(recordedBuildsGitlink=pinned, qualifiedSharedCandidate=shared)

    def bootstrap(code, text):
        if code != 1 or '.github/hexalith-ci.json' not in text:
            raise RuntimeError('Unexpected checker result; do not extend the approved bootstrap exception')
        report['normalChecker'] = 'Refused missing pre-adoption config; approved preparation proof follows.'

    run('agents-normal-checker', ['python3', 'references/Hexalith.Builds/check.py'],
        module, expected=bootstrap)
    # The approved preparation proof qualifies the planned shared source without
    # changing the module's committed owned perimeter or pretending adoption.
    patch = git(builds, 'diff', '--binary', pinned, shared)
    subprocess.run(['git', 'apply', '--index', '--binary', '-'], cwd=builds, input=patch, check=True)
    report['qualifiedSharedTree'] = git(builds, 'write-tree').decode().strip()
    assert report['qualifiedSharedTree'] == git(builds, 'rev-parse', shared + '^{tree}').decode().strip()
    assert git(builds, 'rev-parse', 'HEAD').decode().strip() == pinned
    protected = ['.gitmodules', 'AGENTS.md', 'CLAUDE.md', '.claude/settings.json',
                 '.github/copilot-instructions.md', '.github/dependabot.yml',
                 '.github/workflows', 'references/Hexalith.Builds']
    assert not git(module, 'diff', '--raw', base, 'HEAD', '--', *protected)
    report['ownedPerimeterMatchesFreshMain'] = True
    report['releasedAuditSourceUnchanged'] = (
        git(builds, 'show', pinned + ':Github/lib/audit_lint.py') == (builds / 'Github/lib/audit_lint.py').read_bytes())
    assert report['releasedAuditSourceUnchanged']
    sys.path.insert(0, str(builds / 'Github/lib'))
    import audit_lint
    from expected_state import Git, tree_snapshot
    audit_lint.lint(tree_snapshot(Git(module)))
    report['releasedAuditLint'] = 'passed'
    run('agents-restore', ['dotnet', 'restore', 'Hexalith.Agents.slnx',
        '-p:Configuration=Release', '-p:UseHexalithProjectReferences=false', '/m:1', '/nr:false'], module)
    run('agents-build', ['dotnet', 'build', 'Hexalith.Agents.slnx', '-c', 'Release',
        '--no-restore', '-warnaserror', '-p:UseHexalithProjectReferences=false', '/m:1', '/nr:false'], module)
    for project, floor in [('Contracts', 529), ('Client', 6), ('', 787), ('Server', 549), ('UI', 1073)]:
        name = 'Hexalith.Agents' + ('.' + project if project else '') + '.Tests'
        run('agents-tests-' + (project or 'Domain'), ['dotnet', 'test', '--project',
            f'test/{name}/{name}.csproj', '-c', 'Release', '--no-build', '--no-restore',
            '-p:UseHexalithProjectReferences=false', '--stop-on-fail', 'off',
            '--minimum-expected-tests', str(floor), '--fail-skips', 'on'], module)
    run('agents-package-hook', ['python3', 'scripts/check-built-packages.py'], module)
    assert not (module / 'artifacts/cicd-agents-package-check').exists()
    run('agents-exact-exclusions', ['python3', '-B', '-m', 'unittest', 'discover',
        '-s', 'tests/tooling', '-p', 'package_authority_exclusions_test.py', '-v'], module)
    assert not git(module, 'status', '--porcelain', '--ignore-submodules=all')
    report['moduleProductTreeUnchangedDuringProof'] = True
report['result'] = 'pass'
result_file.write_text(json.dumps(report, indent=2) + '\n')
