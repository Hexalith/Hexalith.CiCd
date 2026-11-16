#!/usr/bin/env python3
"""Regenerate artifacts from canonical inputs; preserve precise provenance changes."""
import difflib
import hashlib
import json
import os
import signal
import ctypes
from pathlib import Path
import shutil
import subprocess

EVIDENCE = Path(__file__).resolve().parent
CICD = EVIDENCE.parents[4]
SOURCE = CICD / 'references/Hexalith.Folders'
ROOT = Path(os.environ['TMPDIR']) / 'folders-generation'
ROOT.mkdir()
ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0)
paths = subprocess.check_output(['git', '-C', str(SOURCE), 'ls-files', '-z', '--', 'src/Hexalith.Folders.Client', 'src/Hexalith.Folders.Contracts']).decode().split('\0')
paths += ['Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', 'nuget.config']
for relative in set(paths) - {''}:
    path = SOURCE / relative
    if path.is_file():
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
shutil.copytree(CICD / 'references/Hexalith.Builds/Props', ROOT / 'references/Hexalith.Builds/Props')
project = 'src/Hexalith.Folders.Client/Hexalith.Folders.Client.csproj'
artifacts = ['HexalithFoldersClient.g.cs', 'HexalithFoldersIdempotencyHelpers.g.cs', 'HexalithFoldersNativeClient.g.cs']
folder = Path(project).parent / 'Generated'
for name in artifacts:
    (ROOT / folder / name).unlink()
commands = []
flags = ['-p:Configuration=Release', '-p:UseHexalithProjectReferences=false', '-p:NuGetAudit=true', '-p:NuGetAuditMode=all', '-p:NuGetAuditLevel=low', '-warnaserror', '-m:1']
for label, command in [('restore', ['dotnet', 'restore', project, *flags]), ('generate', ['dotnet', 'msbuild', project, '-t:GenerateHexalithFoldersIdempotencyHelpers;GenerateHexalithFoldersNativeClient;VerifyHexalithFoldersNativeClient', *flags])]:
    with (EVIDENCE / ('runtime-regeneration-' + label + '.log')).open('w') as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            while True:
                try:
                    os.waitpid(-process.pid, 0)
                except ChildProcessError:
                    break
    commands.append({'label': label, 'arguments': command, 'exit_code': process.returncode})
    if process.returncode:
        (EVIDENCE / 'runtime-regeneration.json').write_text(json.dumps({'commands': commands, 'status': 'failed'}, indent=2) + '\n')
        raise SystemExit(process.returncode)
changes = {}
for name in artifacts:
    old = subprocess.check_output(['git', '-C', str(SOURCE), 'show', 'a448d20873dc9e809623f85da206e8d8a13bb9ab:' + str(folder / name)])
    new = (ROOT / folder / name).read_bytes()
    changes[name] = {'before_sha256': hashlib.sha256(old).hexdigest(), 'after_sha256': hashlib.sha256(new).hexdigest(), 'byte_identical': old == new}
    if old != new:
        changes[name]['diff'] = ''.join(difflib.unified_diff(old.decode().splitlines(keepends=True), new.decode().splitlines(keepends=True), fromfile=name + ':before', tofile=name + ':after'))
        # Only the real helper generator's canonical configuration digest may
        # differ. Public generated clients retain their exact existing bytes.
        changed_lines = [line for line in changes[name]['diff'].splitlines() if line.startswith(('+', '-')) and not line.startswith(('+++', '---'))]
        if name == 'HexalithFoldersNativeClient.g.cs':
            allowed = all('Generated using the NSwag toolchain' in line or 'System.CodeDom.Compiler.GeneratedCode(' in line for line in changed_lines)
            changes[name]['change_class'] = 'Existing stale generator-version metadata refreshed; public declarations and method bodies are unchanged.'
        elif name == 'HexalithFoldersIdempotencyHelpers.g.cs':
            allowed = all('GenerationConfigurationSha256' in line or 'GeneratedHelpersSha256' in line for line in changed_lines)
            changes[name]['change_class'] = 'Canonical configuration digest and dependent self-hash only.'
        else:
            allowed = False
        if not allowed:
            (EVIDENCE / ('runtime-regeneration-' + name + '.diff')).write_text(changes[name]['diff'])
            raise RuntimeError('Unexpected generated behavior diff: ' + name)
        shutil.copy2(ROOT / folder / name, SOURCE / folder / name)
(EVIDENCE / 'runtime-regeneration.json').write_text(json.dumps({'status': 'passed', 'commands': commands, 'canonical_configuration': {name: hashlib.sha256((SOURCE / Path(project).parent / name).read_bytes()).hexdigest() for name in ['nswag.json', 'nswag-native.json']}, 'changes': changes}, indent=2) + '\n')
print(json.dumps(changes, indent=2))
