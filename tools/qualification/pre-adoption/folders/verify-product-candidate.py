#!/usr/bin/env python3
"""Verify the local Folders preparation without remote Git or nested submodules."""
from __future__ import annotations

import hashlib
import ctypes
import dataclasses
import re
import json
import os
from pathlib import Path
import shutil
import signal
import uuid
import subprocess
import sys
import time

CICD = Path(__file__).resolve().parents[4]
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
SOURCE = CICD / 'references/Hexalith.Folders'
BASE = 'a448d20873dc9e809623f85da206e8d8a13bb9ab'
SCRATCH = Path(os.environ['TMPDIR'])
OUTPUT = SCRATCH / 'folders-product-results'
OUTPUT.mkdir(parents=True, exist_ok=True)
ROOT = SCRATCH / 'Hexalith.Folders'
# Adopt and reap only our own orphaned subprocess descendants on Linux.
ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0)
COMMON = Path(subprocess.check_output(['git', '-C', str(CICD), 'rev-parse', '--path-format=absolute', '--git-common-dir'], text=True).strip()) / 'modules/references'
RESULT = {'status': 'running', 'base': BASE, 'cicd': subprocess.check_output(['git', '-C', str(CICD), 'rev-parse', 'HEAD'], text=True).strip(), 'inputs': {}, 'commands': [], 'limitations': []}


def save():
    (OUTPUT / 'product-verification.json').write_text(json.dumps(RESULT, indent=2) + '\n')


def job(label, arguments, *, cwd=ROOT, environment=None, timeout=1800):
    start = time.time()
    log = OUTPUT / (label + '.log')
    print(label, 'running', flush=True)
    env = os.environ.copy()
    env.update(CI='true', DOTNET_NOLOGO='1', DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_CLI_UI_LANGUAGE='en-US', MSBUILDDISABLENODEREUSE='1', UseSharedCompilation='false')
    if environment:
        env.update(environment)
    process = None
    try:
        with log.open('w') as output:
            process = subprocess.Popen(arguments, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                code = 124
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
    finally:
        if process is not None:
            # Only this job's private process group is eligible for cleanup.
            try:
                os.killpg(process.pid, signal.SIGTERM)
                time.sleep(0.2)
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            # The subreaper makes descendants waitable after their direct parent
            # exits. Reap this private process group before scratch cleanup.
            while True:
                try:
                    child, _ = os.waitpid(-process.pid, 0)
                    if child == 0:
                        break
                except ChildProcessError:
                    break
    summary = None
    proof_status = None
    if label.startswith('test-'):
        matches = re.findall(r'(?m)^\s*(\S+)\s+Total:\s*(\d+),\s*Errors:\s*(\d+),\s*Failed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Not Run:\s*(\d+)', log.read_text(errors='replace'))
        if len(matches) == 1:
            _, *values = matches[0]
            summary = dict(zip(['total', 'errors', 'failed', 'skipped', 'not_run'], map(int, values)))
            proof_status = 'failed' if code != 0 or summary['errors'] or summary['failed'] else ('incomplete' if summary['skipped'] or summary['not_run'] else 'complete')
        else:
            proof_status = 'not_verified'
    RESULT['commands'].append({'label': label, 'arguments': arguments, 'exit_code': code, 'seconds': round(time.time() - start, 2), 'log': log.name, **({'summary': summary, 'proof_status': proof_status} if proof_status else {})})
    save()
    print(label, 'exit', code, flush=True)
    return code


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-c', 'submodule.recurse=false', '-c', 'fetch.recurseSubmodules=false', '-C', str(cwd), *args], text=True).strip()


subprocess.run(['git', '-c', 'submodule.recurse=false', 'clone', '--shared', '--no-checkout', str(SOURCE), str(ROOT)], check=True, capture_output=True)
subprocess.run(['git', '-C', str(ROOT), '-c', 'submodule.recurse=false', 'checkout', '--detach', BASE], check=True, capture_output=True)
changed = subprocess.check_output(['git', '-C', str(SOURCE), 'diff', '--name-only', '-z', BASE]).decode().split('\0')
untracked = subprocess.check_output(['git', '-C', str(SOURCE), 'ls-files', '--others', '--exclude-standard', '-z']).decode().split('\0')
for relative in sorted(set(changed + untracked) - {''}):
    original, target = SOURCE / relative, ROOT / relative
    if original.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
    elif original.is_symlink():
        target.symlink_to(os.readlink(original))
    elif not original.exists() and target.is_file():
        target.unlink()
    else:
        raise RuntimeError('unsupported candidate path: ' + relative)
git('add', '--all')
patch = subprocess.check_output(['git', '-C', str(ROOT), 'diff', '--cached', '--binary', BASE])
(OUTPUT / 'folders-product-candidate.patch').write_bytes(patch)
RESULT['patch_sha256'] = hashlib.sha256(patch).hexdigest()
RESULT['tree'] = git('write-tree')
subprocess.run(['git', '-C', str(ROOT), '-c', 'user.name=Hexalith module agent', '-c', 'user.email=module-agent@hexalith.com', 'commit', '-m', 'build: prepare Folders central CI migration'], check=True, capture_output=True)
RESULT['candidate'] = git('rev-parse', 'HEAD')
# Before adoption, all whole files, partial-instruction carriers, Builds and
# .gitmodules retain their exact blob/mode/gitlink identities from the base.
owned = ['.github/workflows', '.github/dependabot.yml', '.github/hexalith-ci.json', 'references/Hexalith.Builds', '.gitmodules', 'AGENTS.md', 'CLAUDE.md', '.github/copilot-instructions.md', '.claude', 'commitlint.config.mjs', '.releaserc.json']
previous = git('ls-tree', '-r', BASE, '--', *owned)
current = git('ls-tree', '-r', 'HEAD', '--', *owned)
RESULT['owned_tree_preserved'] = previous == current
(OUTPUT / 'owned-tree-baseline.txt').write_text(previous + '\n')
(OUTPUT / 'owned-tree-candidate.txt').write_text(current + '\n')
if previous != current:
    raise RuntimeError('owned tree changed')
# Ordinary standalone copies at exact existing local objects: no submodule init.
for line in git('ls-tree', BASE, '--', 'references/Hexalith.Builds', 'references/Hexalith.McpCli', 'references/Hexalith.Memories', 'references/Hexalith.Platform', 'references/Hexalith.Tenants').splitlines():
    mode, kind, revision, relative = line.split()
    source = COMMON / Path(relative).name
    destination = ROOT / relative
    subprocess.run(['git', '-c', 'submodule.recurse=false', 'clone', '--shared', '--no-checkout', str(source), str(destination)], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(destination), '-c', 'submodule.recurse=false', 'checkout', '--detach', revision], check=True, capture_output=True)
    RESULT['inputs'][relative] = revision
save()
# Discovery is the actual existing CiCd model, run on a committed candidate.
sys.path.insert(0, str(CICD / 'tools'))
import delivery_runtime
from scan_discovery import Discovery
files, errors = Discovery(delivery_runtime.Git(ROOT), RESULT['candidate']).discover()
(OUTPUT / 'action-discovery.json').write_text(json.dumps({'candidate': RESULT['candidate'], 'paths': sorted(files), 'errors': errors}, indent=2) + '\n')
RESULT['action_discovery'] = {'files': len(files), 'error_count': len(errors), 'diagnostic_samples': errors[:5], 'diagnostics': 'action-discovery.json'}
save()
# Released audit/action/commit policy, without delivered-state substitution.
sys.path.insert(0, str(ROOT / 'references/Hexalith.Builds/Github/lib'))
import audit_lint
import expected_state
import guard_actions
import guard_commitlint
from guard_tools import Tools
snapshot = expected_state.tree_snapshot(expected_state.Git(ROOT), RESULT['candidate'])
try:
    audit_lint.lint(snapshot)
    RESULT['audit_lint'] = 'passed'
except Exception as error:
    RESULT['audit_lint'] = str(error)
save()
try:
    tool_root = SCRATCH / 'guard-tools'
    tool_root.mkdir()
    tools = Tools(tool_root)
    tools.lint_message('build: prepare Folders central CI migration\n', 'candidate message')
    guard_actions.lint(snapshot, tools)
    guard_commitlint.lint(expected_state.Git(ROOT), tools, event_name='workflow_dispatch', event={}, frozen_head=RESULT['candidate'])
    RESULT['released_action_commit_policy'] = 'passed'
except Exception as error:
    RESULT['released_action_commit_policy'] = str(error)
save()
job('package-checks', ['python3', '-m', 'scripts.tests.test_release_packages'])
job('nightly-classification', ['pwsh', '-NoLogo', '-NoProfile', '-File', 'tests/tools/run-nightly-drift-gates.ps1', '-ProviderProfile', 'pinned-snapshots'])
# A private host without any .NET 10 runtime proves generator execution does
# not accidentally depend on the workstation's side-by-side runtime.
dotnet_source = Path(shutil.which('dotnet')).resolve().parent
host = SCRATCH / 'dotnet11'
host.mkdir()
shutil.copy2(dotnet_source / 'dotnet', host / 'dotnet')
for name in ['host', 'sdk', 'sdk-manifests', 'packs', 'templates', 'metadata']:
    if (dotnet_source / name).exists():
        (host / name).symlink_to(dotnet_source / name, target_is_directory=True)
for family in (dotnet_source / 'shared').iterdir():
    for runtime in family.iterdir():
        if runtime.name.startswith('11.'):
            target = host / 'shared' / family.name / runtime.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(runtime, target_is_directory=True)
restricted = {'DOTNET_ROOT': str(host), 'PATH': str(host) + os.pathsep + os.environ['PATH']}
job('dotnet11-runtimes', [str(host / 'dotnet'), '--list-runtimes'], environment=restricted)
flags = ['-p:Configuration=Release', '-p:UseHexalithProjectReferences=false', '-p:NuGetAudit=true', '-p:NuGetAuditMode=all', '-p:NuGetAuditLevel=low', '-warnaserror', '-m:1']
restored = job('package-restore', ['dotnet', 'restore', 'Hexalith.Folders.CI.slnx', *flags])
built = job('package-build', ['dotnet', 'build', 'Hexalith.Folders.CI.slnx', '--no-restore', *flags])
# Fresh generation is isolated from the candidate whose built suites follow.
generation_root = SCRATCH / 'generation-only'
generation_root.mkdir()
paths = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z', '--', 'src/Hexalith.Folders.Client', 'src/Hexalith.Folders.Contracts']).decode().split('\0')
paths += ['Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', 'nuget.config']
for relative in set(paths) - {''}:
    source = ROOT / relative
    if source.is_file():
        destination = generation_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
shutil.copytree(ROOT / 'references/Hexalith.Builds/Props', generation_root / 'references/Hexalith.Builds/Props')
client = 'src/Hexalith.Folders.Client/Hexalith.Folders.Client.csproj'
for relative in ['Generated/HexalithFoldersClient.g.cs', 'Generated/HexalithFoldersIdempotencyHelpers.g.cs']:
    (generation_root / Path(client).parent / relative).unlink()
job('generator-restore-dotnet11-only', [str(host / 'dotnet'), 'restore', client, *flags], cwd=generation_root, environment=restricted)
job('generator-dotnet11-only', [str(host / 'dotnet'), 'msbuild', client, '-t:GenerateHexalithFoldersIdempotencyHelpers', *flags], cwd=generation_root, environment=restricted)
job('native-generator-dotnet11-only', [str(host / 'dotnet'), 'msbuild', client, '-t:VerifyHexalithFoldersNativeClient', *flags], cwd=generation_root, environment=restricted)
RESULT['generated_diff'] = [name for name in ['HexalithFoldersClient.g.cs', 'HexalithFoldersIdempotencyHelpers.g.cs'] if not (generation_root / Path(client).parent / 'Generated' / name).is_file() or (ROOT / Path(client).parent / 'Generated' / name).read_bytes() != (generation_root / Path(client).parent / 'Generated' / name).read_bytes()]
save()
job('source-whitespace', ['dotnet', 'format', 'whitespace', 'Hexalith.Folders.CI.slnx', '--verify-no-changes', '--no-restore', '--include', './src/', './tests/', './samples/'])
job('source-analyzers', ['dotnet', 'format', 'analyzers', 'Hexalith.Folders.CI.slnx', '--verify-no-changes', '--no-restore', '--severity', 'warn', '--include', './src/', './tests/', './samples/', '--exclude-diagnostics', 'CA1822', 'CA2007'])
# Installed Dapr is already shared with other active workspace jobs. Verify its
# exact pinned runtime without reinitializing or stopping those resources.
job('dapr-prerequisite', ['dapr', '--version'])
job('docker-prerequisite', ['docker', 'version', '--format', '{{.Server.Version}}'])
try:
    from ci_environment import dapr_versions, playwright_tools
    RESULT['trusted_dapr_versions'] = dapr_versions()
    RESULT['shared_playwright_tools'] = [str(script.relative_to(ROOT)) for script in playwright_tools(ROOT, 'Hexalith.Folders.CI.slnx')]
except Exception as error:
    RESULT['shared_environment_error'] = str(error)
save()
# Attempt every retained project once when its complete assembly was built.
# Missing assemblies remain explicit failures, never exemptions.
from ci_pipeline import discover_test_projects, classify_projects
config = json.loads((FIXTURES / 'registration-candidate/rendered/Hexalith.Folders/.github/hexalith-ci.json').read_text())
discovered = discover_test_projects(ROOT, 'Hexalith.Folders.CI.slnx')
classified = classify_projects(discovered, config, repository='Hexalith/Hexalith.Folders')
RESULT['shared_classification'] = dataclasses.asdict(classified)
(OUTPUT / 'shared-classification.json').write_text(json.dumps(RESULT['shared_classification'], indent=2) + '\n')
projects = [(path, Path(path).stem) for path in (*classified.unit, *classified.integration)]
prior = json.loads((FIXTURES / 'attempt-1/product-verification.json').read_text())
reusable = {'Hexalith.Folders.Sample.Tests', 'Hexalith.Folders.Cli.Tests', 'Hexalith.Folders.EventStore.Tests', 'Hexalith.Folders.IntegrationTests', 'Hexalith.Folders.LoadTests.Tests', 'Hexalith.Folders.Mcp.Tests', 'Hexalith.Folders.Server.Tests', 'Hexalith.Folders.Testing.Tests', 'Hexalith.Folders.UI.Tests', 'Hexalith.Folders.Workers.Tests', 'Hexalith.Folders.UI.E2E.Tests'}
RESULT['reuse_basis'] = 'Attempt-1 immutable candidate ' + prior['candidate'] + '; unchanged test/source C# inputs and package/dependency revisions. Zero-exit/incomplete counters remain incomplete. Changed Contracts, Client and core provider suites are rerun.'
for command in prior['commands']:
    if command['label'].removeprefix('test-') in reusable:
        reused = dict(command, status='reused', source_candidate=prior['candidate'], log='attempt-1/' + command['log'])
        RESULT['commands'].append(reused)
second = json.loads((FIXTURES / 'attempt-2/product-verification.json').read_text())
for command in second['commands']:
    if command['label'] == 'test-Hexalith.Folders.Tests':
        RESULT['commands'].append(dict(command, status='reused', source_candidate=second['candidate'], log='attempt-2/' + command['log']))
        reusable.add('Hexalith.Folders.Tests')
save()
for project, name in sorted(projects):
    if name in reusable:
        continue
    if name in {'Hexalith.Folders.Contracts.Tests', 'Hexalith.Folders.Client.Tests', 'Hexalith.Folders.UI.E2E.Tests'}:
        continue
    assembly = ROOT / Path(project).parent / 'bin/Release/net11.0' / (name + '.dll')
    if assembly.is_file():
        job('test-' + name, ['dotnet', str(assembly), '-noLogo', '-noColor'], environment=({'HEXALITH_FOLDERS_RUN_ASPIRE_INTEGRATION': 'true'} if name == 'Hexalith.Folders.AppHost.Tests' else None))
    else:
        RESULT['commands'].append({'label': 'test-' + name, 'exit_code': None, 'status': 'not_run', 'reason': 'complete Release assembly unavailable after product build failure'})
        save()
for name in ['Hexalith.Folders.Contracts.Tests', 'Hexalith.Folders.Client.Tests']:
    job('test-' + name, ['pwsh', '-NoLogo', '-NoProfile', '-File', 'tests/tools/run-complete-project-tests.ps1', '-ProjectName', name])
job('capacity-smoke', ['pwsh', '-NoLogo', '-NoProfile', '-File', 'tests/tools/run-capacity-smoke-ci-gates.ps1'])
job('capacity-calibration', ['pwsh', '-NoLogo', '-NoProfile', '-File', 'tests/tools/run-capacity-calibration-gates.ps1'])
smoke_id = uuid.uuid4().hex
try:
    job('forgejo-alpine-smoke', ['pwsh', '-NoLogo', '-NoProfile', '-File', 'tests/tools/run-forgejo-smart-http-alpine-smoke.ps1', '-RunId', smoke_id])
finally:
    for version in ['16.0.3', '15.0.7']:
        subprocess.run(['docker', 'rm', '--force', 'hxf-forgejo-smoke-' + version + '-' + smoke_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    subprocess.run(['docker', 'network', 'rm', 'hxf-forgejo-smoke-' + smoke_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
RESULT['status'] = 'passed' if not errors and not RESULT.get('generated_diff') and not RESULT.get('shared_environment_error') and RESULT.get('audit_lint') == 'passed' and RESULT.get('released_action_commit_policy') == 'passed' and all(command.get('exit_code') == 0 and command.get('proof_status', 'complete') == 'complete' for command in RESULT['commands']) else 'failed'
RESULT['limitations'] += ['No live AD-21 administration, remote Git, adoption, delivery authentication or genuine scheduled nightly is authorized in this local handoff.', 'The candidate commit exists only in a disposable verification repository; it is not a published preparation commit.']
save()
print('verification', RESULT['status'], flush=True)
