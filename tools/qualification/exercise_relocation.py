#!/usr/bin/env python3
"""Exercise relocated qualifiers with disposable source and controlled boundaries.

Run with run-with-temp. This checks relocation behavior, never module readiness
or publication authority. Git, GitHub, released policy modules, Docker and SDK
processes are controlled in process; runner code, frozen fixture reads, source
file operations, report writes, result checks and refusal checks execute normally.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tarfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
BASE = 'a' * 40
HEAD = 'b' * 40
BUILDS_SHA = 'fdda17c0a4538b0f7c99f813c20ca24b49006530'
FOLDERS_BASE = 'a448d20873dc9e809623f85da206e8d8a13bb9ab'
PARTIES_BASE = 'a575021fc97a8eda664711089270b60f5e570ded'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root):
    return {str(path.relative_to(root)): digest(path) for path in sorted(root.rglob('*'))
            if path.is_file() and '__pycache__' not in path.parts}


@dataclass
class Classified:
    unit: tuple = ('tests/Controlled.Tests/Controlled.Tests.csproj',)
    integration: tuple = ()
    excluded: tuple = ()


@dataclass(frozen=True)
class Item:
    mode: str
    oid: str


class Snapshot:
    def __init__(self, candidate=False):
        self.bodies = {
            'AGENTS.md': b'Controlled foreign instructions\n',
            'package-lock.json': json.dumps({'packages': {
                'node_modules/' + name: {'version': '21.2.4'}
                for name in ('@commitlint/cli', '@commitlint/config-conventional')}}).encode(),
            'commitlint.config.mjs': b'export default {};\n',
            'docs/ci.md': b'candidate\n' if candidate else b'base\n',
        }
        self.items = {name: Item('100644', hashlib.sha1(body).hexdigest())
                      for name, body in self.bodies.items()}
        self.items.update({'references/' + name: Item('160000', BUILDS_SHA)
                           for name in ('Hexalith.Builds', 'Hexalith.Tenants', 'Hexalith.Platform', 'Hexalith.FrontComposer')})

    def read(self, path):
        return self.bodies[path]


class Boundaries:
    """A bounded external-tool model. Unknown operations fail the exercise."""
    def __init__(self, layout, scratch, kind, *, refuse_policy=False, parties_case="source"):
        self.layout, self.scratch, self.kind = layout, scratch, kind
        self.refuse_policy = refuse_policy
        self.parties_case = parties_case
        self.calls, self.policy_calls, self.reads = [], [], []
        self.containers = {}
        self.original_open = Path.open
        self.dependencies = {}
        if kind == 'parties':
            fixture = layout / 'tools/qualification/pre-adoption/parties/fixtures'
            accepted = json.loads((fixture / 'accepted-local-verification.json').read_text())
            self.dependencies = json.loads((fixture / accepted['unit_run'] / 'unit-only-preparation.json').read_text())['dependencies']

    def record_open(self, path, mode='r', *args, **kwargs):
        path = Path(path)
        if 'r' in mode:
            self.reads.append(path.resolve())
        return self.original_open(path, mode, *args, **kwargs)

    def output(self, arguments, cwd=None, **kwargs):
        arguments = list(map(str, arguments))
        self.calls.append(arguments)
        tool = Path(arguments[0]).name
        stdout, stderr, code = '', '', 0
        if tool == 'git':
            args = arguments[1:]
            cwd = Path(cwd or self.layout)
            cleaned = []
            index = 0
            while index < len(args):
                if args[index] == '-C':
                    cwd = Path(args[index + 1]); index += 2
                elif args[index] == '-c':
                    index += 2
                else:
                    cleaned.append(args[index]); index += 1
            args = cleaned
            operation = args[0]
            if operation == 'rev-parse':
                option = args[-1]
                if option == '--is-shallow-repository': stdout = 'false\n'
                elif option == '--show-toplevel': stdout = str(cwd) + '\n'
                elif option == '--git-common-dir':
                    # Real Git prints a relative common directory unless absolute paths are requested.
                    stdout = (str(self.layout / '.git') if '--path-format=absolute' in args else '.git') + '\n'
                elif option.endswith('^{commit}'): stdout = BUILDS_SHA + '\n'
                elif self.kind == 'parties': stdout = PARTIES_BASE + '\n'
                elif self.kind == 'eventstore': stdout = (BASE if option == 'origin/main' else HEAD) + '\n'
                elif self.kind.startswith('folders'): stdout = ('c' * 40 if cwd == self.layout else FOLDERS_BASE) + '\n'
                else: stdout = 'c' * 40 + '\n'
            elif operation == 'config':
                stdout = 'https://github.com/Hexalith/' + cwd.name + '\n'
            elif operation in ('status', 'fetch', 'checkout', 'add', 'commit', 'merge-base', 'remote', 'read-tree', 'update-index', 'apply'):
                pass
            elif operation == 'clone':
                source, destination = map(Path, args[-2:])
                shutil.copytree(source, destination, dirs_exist_ok=True)
            elif operation == 'diff':
                if '--name-only' in args:
                    stdout = 'docs/ci.md\0' if self.kind == 'eventstore' else ''
                else: stdout = 'controlled product delta\n'
            elif operation == 'ls-files':
                if '--stage' in args:
                    name = Path(args[-1]).name
                    pin = '0' * 40 if self.parties_case == 'pin' else self.dependencies[name]
                    stdout = '160000 ' + pin + ' 0\t' + args[-1] + '\n'
                elif '--others' in args:
                    pass
                else:
                    prefix = 'src/' if self.kind.startswith('folders') else ''
                    stdout = '\0'.join(str(path.relative_to(cwd)) for path in sorted(cwd.rglob('*'))
                                       if path.is_file() and (not prefix or str(path.relative_to(cwd)).startswith(prefix))) + '\0'
            elif operation == 'ls-tree':
                if '-r' in args:
                    stdout = '100644 blob ' + '1' * 40 + '\tAGENTS.md\n'
                else:
                    stdout = '\n'.join('160000 commit ' + BUILDS_SHA + '\treferences/' + name
                                       for name in ('Hexalith.Builds', 'Hexalith.McpCli', 'Hexalith.Memories', 'Hexalith.Platform', 'Hexalith.Tenants'))
            elif operation == 'write-tree':
                wrong_tree = self.parties_case == 'tree' and not (kwargs.get('env') or {}).get('GIT_INDEX_FILE')
                stdout = ('c' if wrong_tree else 'd') * 40 + '\n'
            elif operation == 'hash-object': stdout = 'e' * 40 + '\n'
            elif operation == 'cat-file': stdout = 'tree ' + 'd' * 40 + '\n'
            elif operation == 'bundle': Path(args[2]).write_bytes(b'controlled bundle\n')
            elif operation == 'rev-list': stdout = HEAD + (' ' + BASE if '--parents' in args else '') + '\n'
            elif operation == 'archive':
                with tarfile.open(fileobj=kwargs['stdout'], mode='w') as payload:
                    item = tarfile.TarInfo('Github/lib/.controlled-boundary')
                    body = b'Controlled released modules are supplied in process.\n'
                    item.size = len(body); payload.addfile(item, io.BytesIO(body))
            else: raise AssertionError('Uncontrolled Git operation: ' + repr(args))
        elif tool == 'netsh.exe':
            stdout = ''
        elif tool == 'gh':
            endpoint = arguments[-1]
            if endpoint == 'user': value = {'login': 'jpiquot'}
            elif endpoint == 'repos/Hexalith/Hexalith.CiCd': value = {'full_name': 'Hexalith/Hexalith.CiCd', 'default_branch': 'main'}
            elif endpoint.endswith('/heads/main'): value = {'ref': 'refs/heads/main', 'object': {'sha': BASE, 'type': 'commit'}}
            elif '/heads/delivered/' in endpoint:
                value = {'message': 'Not Found', 'status': '404', 'documentation_url': 'https://docs.github.com/rest/git/refs#get-a-reference'}
                code, stderr = 1, 'gh: Not Found (HTTP 404)'
            elif '/releases/tags/' in endpoint:
                value = {'tag_name': 'v6.0.6', 'draft': False, 'immutable': True, 'prerelease': False, 'author': {'login': 'github-actions[bot]'}}
            else: raise AssertionError('Uncontrolled GitHub operation: ' + endpoint)
            stdout = json.dumps(value)
        elif tool == 'docker':
            args = arguments[1:]
            if args[0] == 'run':
                identity = format(len(self.containers) + 1, '064x')
                name = args[args.index('--name') + 1]
                label = args[args.index('--label') + 1].split('=', 1)[1]
                port = args[args.index('-p') + 1].split(':')[1]
                self.containers[identity] = {'name': name, 'label': label, 'port': int(port) if port else 43123, 'removed': False}
                Path(args[args.index('--cidfile') + 1]).write_text(identity)
                stdout = identity + '\n'
            elif args[0] == 'port': stdout = '127.0.0.1:' + str(self.containers[args[1]]['port']) + '\n'
            elif args[0] == 'inspect': stdout = json.dumps({'hexalith.story18-g6': self.containers[args[-1]]['label']})
            elif args[0] == 'container':
                if args[-1].startswith('id='):
                    identity = args[-1].removeprefix('id=')
                    stdout = '' if self.containers[identity]['removed'] else identity + '\n'
                else: raise AssertionError('Unexpected custody recovery; cidfiles must exist')
            elif args[0] == 'rm' and args[-1] in self.containers: self.containers[args[-1]]['removed'] = True
            elif args[0] in ('image', 'pull', 'rm', 'network', 'version'): pass
            else: raise AssertionError('Uncontrolled Docker operation: ' + repr(args))
        elif tool in ('dotnet', 'pwsh', 'dapr', 'npm', 'node', 'python3', Path(sys.executable).name):
            if '--list-sdks' in arguments: stdout = '10.0.404 [/controlled/sdk]\n11.0.100 [/controlled/sdk]\n'
            elif '-result-ctrf' in arguments:
                result = Path(arguments[arguments.index('-result-ctrf') + 1])
                result.write_text(json.dumps({'results': {'summary': {'passed': 1, 'skipped': 0, 'failed': 0}}}))
            else: stdout = 'Passed Total: 1, Errors: 0, Failed: 0, Skipped: 0, Not Run: 0\n'
            if 'msbuild' in arguments:
                generated = Path(cwd) / 'src/Hexalith.Folders.Client/Generated'
                generated.mkdir(parents=True, exist_ok=True)
                for name in ('HexalithFoldersClient.g.cs', 'HexalithFoldersIdempotencyHelpers.g.cs'):
                    (generated / name).write_text('// controlled generated product\n')
        else: raise AssertionError('Uncontrolled external tool: ' + tool)
        return stdout, stderr, code

    def run(self, arguments, **kwargs):
        stdout, stderr, code = self.output(arguments, **kwargs)
        stream = kwargs.get('stdout')
        if stream is not None and stream not in (subprocess.PIPE, subprocess.DEVNULL) and Path(str(arguments[0])).name != 'git':
            stream.write(stdout); stream.flush()
        if kwargs.get('check') and code:
            raise subprocess.CalledProcessError(code, arguments, stdout, stderr)
        text = kwargs.get('text') or kwargs.get('encoding')
        return subprocess.CompletedProcess(arguments, code, stdout if text else stdout.encode(), stderr if text else stderr.encode())

    def check_output(self, arguments, **kwargs):
        return self.run(arguments, check=True, **kwargs).stdout

    def popen(self, arguments, **kwargs):
        result = self.run(arguments, **kwargs)
        return SimpleNamespace(pid=987654321, wait=lambda timeout=None: result.returncode)

    def modules(self):
        values = {}
        def module(name, **attributes):
            value = ModuleType(name)
            value.__dict__.update(attributes)
            values[name] = value
            return value
        def checked(name):
            def call(*args, **kwargs):
                self.policy_calls.append(name)
                if self.refuse_policy and name == 'audit_lint':
                    raise ValueError('controlled released audit refusal')
            return call
        class Tools:
            def __init__(self, root): self.environment = dict(os.environ)
            lint_message = lambda *args: self.policy_calls.append('lint_message')
            def _process(_tools, arguments, operation, message):
                self.policy_calls.append(operation)
                if self.parties_case == 'commitlint':
                    return subprocess.CompletedProcess(arguments, 1, '', 'controlled commitlint rejection')
                return subprocess.CompletedProcess(arguments, 0, '', '')
        class PipelineError(Exception):
            def __init__(self, message, returncode=1): super().__init__(message); self.returncode = returncode
        @dataclass
        class PreparedConfig:
            root: Path
            source: Path
            configuration: dict
            solution: str
            global_json: str
            dependencies: tuple
        module('audit_lint', lint=checked('audit_lint'))
        module('guard_actions', lint=checked('guard_actions'))
        module('guard_commitlint', lint=checked('guard_commitlint'), message=lambda *args: 'build: controlled product\n')
        module('expected_state', Git=lambda root: root, tree_snapshot=lambda root, revision: Snapshot(revision == HEAD))
        module('guard_tools', Tools=Tools, SOURCE=self.layout / 'controlled-tools')
        module('delivery_runtime', Git=lambda root: root)
        class Discovery:
            def __init__(self, *args): pass
            def discover(self): return {'scripts/product.py'}, []
        module('scan_discovery', Discovery=Discovery)
        module('ci_environment', dapr_versions=lambda: ('1.19.1',), playwright_tools=lambda *args: [])
        module('ci_pipeline', PipelineError=PipelineError, PreparedConfig=PreparedConfig,
               classify_projects=lambda *args, **kwargs: Classified(), discover_test_projects=lambda *args: Classified().unit,
               classified_projects=lambda *args, **kwargs: Classified(), test_runner=lambda *args: 'controlled runner',
               execute_test_projects=checked('execute_test_projects'), execute_unit_projects=checked('execute_unit_projects'),
               restore_and_build=checked('restore_and_build'), validate_config=checked('validate_config'))
        return values


def write(path, body='controlled disposable product\n'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def source_layout(layout):
    for name in ('Projects', 'Builds', 'EventStore', 'Tenants', 'Folders', 'Platform', 'FrontComposer', 'McpCli', 'Memories'):
        root = layout / 'references' / ('Hexalith.' + name)
        root.mkdir(parents=True)
        write(root / 'README.md')
        if name == 'Builds':
            write(root / 'NuGet.ci.Config'); write(root / 'Props/controlled.props')
    folders = layout / 'references/Hexalith.Folders'
    for name in ('HexalithFoldersClient.g.cs', 'HexalithFoldersIdempotencyHelpers.g.cs'):
        write(folders / 'src/Hexalith.Folders.Client/Generated' / name, '// controlled generated product\n')
    write(folders / 'src/Hexalith.Folders.Contracts/Controlled.cs')
    write(folders / 'tests/tools/run-complete-project-tests.ps1')
    write(folders / 'tests/Controlled.Tests/bin/Release/net11.0/Controlled.Tests.dll')
    projects = layout / 'references/Hexalith.EventStore'
    for name in ('Hexalith.EventStore.Server.LiveSidecar.Tests', 'Hexalith.EventStore.Server.Tests'):
        write(projects / 'tests' / name / (name + '.csproj'))
        write(projects / 'tests' / name / 'bin/Release/net11.0' / (name + '.dll'))
    for name in ('Hexalith.Builds', 'Hexalith.McpCli', 'Hexalith.Memories', 'Hexalith.Platform', 'Hexalith.Tenants'):
        source = layout / 'references' / name
        shutil.copytree(source, layout / '.git/modules/references' / name)
    write(layout / 'controlled-tools/package-lock.json', '{}\n')
    host = layout / 'controlled-sdk'
    write(host / 'dotnet', '#!/bin/sh\nexit 0\n')
    (host / 'dotnet').chmod(0o755)
    for name in ('host', 'sdk', 'shared/Microsoft.NETCore.App/11.0.100'):
        (host / name).mkdir(parents=True)


def parties_success_inputs(layout):
    """Create synthetic proof/source pairs only in a private success layout."""
    fixture = layout / 'tools/qualification/pre-adoption/parties/fixtures'
    module = layout / 'references/Hexalith.Parties'
    patch_body = b'controlled disposable preparation patch\n'
    (fixture / 'current-preparation.patch').write_bytes(patch_body)
    normalization = {'path': 'scripts/controlled-normalized.py',
                     'before_sha256': hashlib.sha256(b'controlled product\n\n').hexdigest(),
                     'after_sha256': hashlib.sha256(b'controlled product\n').hexdigest()}
    inputs = []
    for name in ('scripts/controlled-product.py', normalization['path']):
        path = module / name
        write(path, 'controlled product\n')
        path.chmod(0o644)
        inputs.append({'path': name, 'mode': '0o644',
                       'sha256': normalization['before_sha256'] if name == normalization['path'] else digest(path)})
    patch_sha = hashlib.sha256(patch_body).hexdigest()
    values = {
        'current-preparation-state.json': {'patch_sha256': patch_sha, 'untracked_inputs': inputs,
                                           'owned_files_unchanged': True},
        'accepted-local-verification.json': {'final_patch_sha256': patch_sha, 'unit_run': 'controlled-run'},
        'whitespace-normalization.json': normalization,
        'controlled-run/unit-only-preparation.json': {'dependencies': {'Hexalith.Builds': BUILDS_SHA}},
    }
    for name, value in values.items():
        write(fixture / name, json.dumps(value) + '\n')
    write(module / 'commitlint.config.mjs', 'export default {};\n')


def exercise(checkout, workspace, kind, *, refuse_policy=False, parties_case='source'):
    layout = workspace / kind
    shutil.copytree(checkout / 'tools/qualification', layout / 'tools/qualification',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    source_layout(layout)
    if kind == 'parties' and parties_case != 'source':
        parties_success_inputs(layout)
    scratch = layout / 'scratch'
    scratch.mkdir()
    boundaries = Boundaries(layout, scratch, kind, refuse_policy=refuse_policy, parties_case=parties_case)
    code = layout / 'tools/qualification'
    before = manifest(code)
    qualifier = {
        'folders-product': 'pre-adoption/folders/verify-product-candidate.py',
        'folders-final': 'pre-adoption/folders/verify-final-candidate.py',
        'projects': 'pre-adoption/projects/local-package-build.py',
        'g6': 'qualify-owning-g6.py',
        'eventstore': 'pre-adoption/eventstore/pre-adoption-verify.py',
        'parties': 'pre-adoption/parties/qualify-push.py',
    }[kind]
    runner = code / qualifier
    log = layout / 'execution.log'
    def recorded_open(path, mode='r', *args, **kwargs):
        return boundaries.record_open(path, mode, *args, **kwargs)
    def child_reaped(*args): raise ChildProcessError()
    environment = {'PATH': str(layout / 'controlled-sdk'), 'TMPDIR': str(scratch),
                   'TMP': str(scratch), 'TEMP': str(scratch)}
    if kind == 'parties' and parties_case == 'source':
        # All immutable proof fixtures and every dependency pin are checked first.
        # A real file with deliberately wrong bytes tests the preserved exact-input
        # refusal; the unavailable historical untracked bodies are never simulated.
        state = json.loads((runner.parent / 'fixtures/current-preparation-state.json').read_text())
        write(layout / 'references/Hexalith.Parties' / state['untracked_inputs'][0]['path'], 'deliberate exact-input mismatch\n')
    argv = [str(runner)]
    if kind == 'projects': argv += ['--test', '--fixture-safety', '--folder-product', '--hooks', '--nightly', '--g6', '--tools']
    namespace, exit_code, refusal = None, 0, None
    with log.open('w') as output, ExitStack() as stack:
        stack.enter_context(redirect_stdout(output)); stack.enter_context(redirect_stderr(output))
        stack.enter_context(patch.dict(os.environ, environment, clear=True))
        stack.enter_context(patch.dict(sys.modules, boundaries.modules()))
        stack.enter_context(patch.object(sys, 'argv', argv))
        stack.enter_context(patch.object(Path, 'open', recorded_open))
        stack.enter_context(patch.object(subprocess, 'run', boundaries.run))
        stack.enter_context(patch.object(subprocess, 'check_output', boundaries.check_output))
        stack.enter_context(patch.object(subprocess, 'Popen', boundaries.popen))
        stack.enter_context(patch('os.killpg', lambda *args: None))
        stack.enter_context(patch('os.waitpid', child_reaped))
        stack.enter_context(patch('time.sleep', lambda *args: None))
        stack.enter_context(patch('shutil.which', lambda name: str(layout / 'controlled-sdk/dotnet') if name == 'dotnet' else None))
        try:
            namespace = runpy.run_path(str(runner), run_name='__exercise__')
            if kind == 'g6':
                runtime = scratch / 'runtime'
                shutil.copytree(layout / 'references', runtime / 'references')
                namespace['run'](runtime, scratch)
            elif kind == 'eventstore':
                token = layout / 'controlled-module-token'
                token.write_text('relocation-exercise-placeholder')
                namespace['main'].__globals__['MODULE_TOKEN_FILE'] = token
                report = layout / 'eventstore-result.json'
                sys.argv = [str(runner), BASE, HEAD, 'v6.0.6', BUILDS_SHA,
                            '--module', str(layout / 'references/Hexalith.EventStore'), '--report', str(report)]
                exit_code = namespace['main']()
        except SystemExit as error:
            exit_code = int(error.code or 0)
        except ValueError as error:
            if kind != 'parties' or parties_case == 'success': raise
            refusal = str(error)
    assert manifest(code) == before, kind + ' modified qualifier code or fixtures'
    fixture_reads = sorted({str(path.relative_to(code)) for path in boundaries.reads
                            if path.is_relative_to(code) and 'fixtures' in path.relative_to(code).parts})
    assert fixture_reads, kind + ' did not read relocated fixtures'
    result = {'runner': 'tools/qualification/' + qualifier,
              'controlled_external_calls': len(boundaries.calls), 'policy_calls': boundaries.policy_calls,
              'fixture_reads': fixture_reads, 'log_sha256': digest(log), 'code_and_fixtures_unchanged': True}
    if kind == 'parties':
        result['qualification_error'] = refusal
        if parties_case != 'success' and refusal is None:
            raise AssertionError(f'Parties qualifier returned normally for {parties_case}')
        if parties_case in ('pin', 'tree', 'commitlint'):
            return result
    if kind.startswith('folders'):
        name = 'product-verification.json' if kind == 'folders-product' else 'final-candidate.json'
        report = next(scratch.rglob(name))
        record = json.loads(report.read_text())
        expected = 'failed' if kind == 'folders-product' else 'blocked'
        assert record['status'] == expected, (kind, record['status'])
        assert not record.get('generated_diff'), 'Controlled generation changed bytes'
        if kind == 'folders-product':
            assert any(value.get('status') == 'reused' and value.get('proof_status') == 'incomplete'
                       for value in record['commands']), 'Historical incomplete result was lost'
            assert all(value['exit_code'] == 0 for value in record['commands']
                       if value.get('status') != 'reused'), 'Controlled product command failed'
            store = (layout / '.git/modules/references').resolve()
            sources = [call[-2] for call in boundaries.calls if Path(call[0]).name == 'git'
                       and 'clone' in call and Path(call[-1]).parent.name == 'references']
            assert len(sources) == 5 and all(Path(value).is_absolute() and Path(value).resolve().is_relative_to(store)
                                             for value in sources), ('Dependency clones left the CiCd module store', sources)
        assert 'audit_lint' in boundaries.policy_calls and 'guard_actions' in boundaries.policy_calls
        if refuse_policy: assert record['audit_lint'] == 'controlled released audit refusal'
        result['preserved_result'] = record['status']
    elif kind in ('g6', 'projects'):
        assert exit_code == 0, (kind, exit_code)
        cleanup = json.loads((scratch / 'owning-g6-cleanup.json').read_text())
        assert len(cleanup) == 3 and all(value['removed'] for value in cleanup)
        assert len(boundaries.containers) == 3 and all(item['removed'] for item in boundaries.containers.values())
        # The controlled SDK writes compact CTRF; only the runner's retained copy is indented.
        for name in ('owning-support-ctrf.json', 'owning-postgresql-ctrf.json'):
            retained = (scratch / name).read_text()
            assert retained == json.dumps(json.loads(retained), indent=2), name + ' was not retained by the runner'
        if kind == 'projects': assert 'execute_test_projects' in boundaries.policy_calls
        result['preserved_result'] = 'controlled product commands and G-6 result/cleanup checks completed'
    elif kind == 'eventstore':
        record = json.loads((layout / 'eventstore-result.json').read_text())
        assert exit_code == 0 and record['result'] == 'passed', record
        assert len(record['unit_project_results']) == 1
        assert record['push_performed'] is False and record['azure_executed'] is False
        assert 'execute_unit_projects' in boundaries.policy_calls
        result['preserved_result'] = 'controlled full preparation body completed'
    elif parties_case == 'success':
        output_directory = scratch / 'parties-publication-results'
        record = json.loads((output_directory / 'pre-push-qualification.json').read_text())
        assert refusal is None and record['result'] == 'pass', record
        assert record['exact_verified_inputs'] is True
        assert record['verified_dependency_revisions'] == boundaries.dependencies
        expected_messages = {
            'parties': 'build(cicd): prepare Parties shared pipeline migration\n',
            'cicd': 'build(cicd): record Parties migration preparation\n',
        }
        result['messages'] = {}
        for name, message in expected_messages.items():
            path = output_directory / (name + '-commit-message.txt')
            assert path.resolve().is_relative_to(scratch.resolve())
            assert path.read_text() == message
            assert record['messages'][name] == {'message': message, 'result': 'pass'}
            result['messages'][name] = {'path': str(path.relative_to(scratch)), 'contents': message}
        assert boundaries.policy_calls.count('lint_message') == 2
        assert record['released_audit_lint'] == record['released_action_lint'] == 'pass'
        result['fixture_basis'] = 'controlled disposable receipts and source; no historical acceptance'
        result['preserved_result'] = 'controlled success body completed; both commit messages written in scratch'
    else:
        record = json.loads((scratch / 'parties-publication-results/pre-push-qualification.json').read_text())
        assert refusal == record['error'] and record['result'] == 'failed', record
        # The exact-byte refusal names its input; other checks and boundary faults do not.
        assert record['error'] == state['untracked_inputs'][0]['path'], 'Refusal was not the exact-byte check: ' + record['error']
        assert record['verified_dependency_revisions'] == boundaries.dependencies
        mismatch = layout / 'references/Hexalith.Parties' / state['untracked_inputs'][0]['path']
        assert mismatch.resolve() in boundaries.reads, 'Expected exact-input check was not reached'
        assert digest(mismatch) != state['untracked_inputs'][0]['sha256']
        result['refusal_input'] = {'path': state['untracked_inputs'][0]['path'],
                                   'expected_sha256': state['untracked_inputs'][0]['sha256'],
                                   'observed_sha256': digest(mismatch)}
        for name in ('current-preparation-state.json', 'accepted-local-verification.json', 'current-preparation.patch', 'whitespace-normalization.json'):
            assert any(Path(path).name == name for path in fixture_reads), name
        assert any(Path(path).name == 'unit-only-preparation.json' for path in fixture_reads)
        result['preserved_result'] = 'exact-input refusal after immutable proof and dependency checks; report written in scratch'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, default=ROOT)
    parser.add_argument('--report', type=Path, help='Optional compact durable report; raw execution stays in TMPDIR.')
    parser.add_argument('--allow-dirty', action='store_true', help='Development only; records that clean-checkout acceptance was not established.')
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    source = lambda *arguments: subprocess.check_output(['git', '-C', str(checkout), *arguments], text=True).strip()
    clean = not source('status', '--porcelain', '--untracked-files=all')
    if not clean and not args.allow_dirty:
        parser.error('The qualification checkout must be clean (use --allow-dirty only for development).')
    scratch = Path(os.environ['TMPDIR']).resolve()
    workspace = scratch / 'relocation-exercise'
    workspace.mkdir()
    report = {'scope': 'Relocation and preserved behavior only; controlled tools do not establish fresh module readiness or publication acceptance.',
              'source_commit': source('rev-parse', 'HEAD'), 'source_tree': source('rev-parse', 'HEAD^{tree}'),
              'clean_checkout': clean, 'exercises': {}}
    for kind in ('folders-product', 'folders-final', 'projects', 'g6', 'eventstore', 'parties'):
        report['exercises'][kind] = exercise(checkout, workspace, kind)
    report['exercises']['parties-success'] = exercise(checkout, workspace / 'controlled-success', 'parties', parties_case='success')
    report['exercises']['released-policy-refusal'] = exercise(checkout, workspace / 'negative', 'folders-product', refuse_policy=True)
    report['limits'] = ['No network, credentials, module publication or real SDK/container product qualification is used.',
                        'Parties preserves exact-byte refusal for an intentionally mismatched disposable source file after all frozen fixtures and dependency pins are checked.',
                        'The separate Parties success case uses synthetic disposable receipts and source to check message outputs; it establishes no historical input or product acceptance.',
                        'Folders product retains failed status from immutable incomplete receipts; Folders final retains its unconditional historical blocked result.']
    payload = json.dumps(report, indent=2) + '\n'
    if args.report:
        args.report.resolve().write_text(payload)
    print(payload, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
