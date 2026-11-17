#!/usr/bin/env python3
"""Local isolated qualification; no remote operations or repository mutations."""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SCRATCH = Path(os.environ['TMPDIR'])
assert SCRATCH.is_dir() and SCRATCH != Path('/tmp')
report = {'scope': 'local origin/main qualification; no protected enrollment or publication', 'foldersDestinationBase': '3ff01eeab6f6dfe7cff83e4ef3e1ff403c50c245', 'foldersSourcePatchBase': 'e5760ca105652f4d89c4f240e0ca455723c9a473', 'repositories': {}, 'dependencies': {}, 'commands': []}

def git(path, *args):
    return subprocess.check_output(['git', '-c', 'submodule.recurse=false', '-C', str(path), *args])

def clone(source, destination, revision='HEAD', changes=False):
    git(ROOT, 'clone', '--quiet', '--shared', '--no-checkout', '--no-recurse-submodules', str(source), str(destination))
    git(destination, 'checkout', '--quiet', '--detach', revision)
    if changes:
        patch = git(source, 'diff', '--binary', 'HEAD')
        subprocess.run(['git', 'apply', '--binary', '-'], input=patch, cwd=destination, check=True)
        for relative in git(source, 'ls-files', '--others', '--exclude-standard').decode().splitlines():
            if relative.endswith(('.py', '.cs', '.md')):
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((source / relative).read_bytes())
        paths = set(git(source, 'diff', '--name-only', 'HEAD').decode().splitlines()) | set(git(source, 'ls-files', '--others', '--exclude-standard').decode().splitlines())
        report['repositories'][source.name] = {'sourcePatchBase': git(source, 'rev-parse', 'HEAD').decode().strip(), 'destinationBase': git(destination, 'rev-parse', 'HEAD').decode().strip(), 'patchSha256': hashlib.sha256(patch).hexdigest(), 'files': {path: hashlib.sha256((source / path).read_bytes()).hexdigest() for path in sorted(paths) if (source / path).is_file()}}

def save():
    (OUT / 'qualification.json').write_text(json.dumps(report, indent=2) + '\n')

def job(label, command, cwd, env=None, timeout=1200):
    environment = dict(os.environ, CI='true', DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER='1', MSBUILDDISABLENODEREUSE='1')
    if env: environment.update(env)
    print(label + ' running', flush=True)
    with (OUT / (label + '.log')).open('wb') as output:
        child = subprocess.Popen(command, cwd=cwd, env=environment, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try: code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            code = child.wait()
        finally:
            try: os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError: pass
    report['commands'].append({'label': label, 'argv': command, 'exitCode': code})
    save()
    print(label + ' exit ' + str(code), flush=True)
    return code

module = SCRATCH / 'Hexalith.Folders'
assert git(ROOT / 'references/Hexalith.Folders', 'rev-parse', 'HEAD').decode().strip() == report['foldersSourcePatchBase']
assert git(ROOT / 'references/Hexalith.Folders', 'rev-parse', 'origin/main').decode().strip() == report['foldersDestinationBase']
clone(ROOT / 'references/Hexalith.Folders', module, report['foldersDestinationBase'], changes=True)
for line in git(module, 'ls-files', '--stage', 'references').decode().splitlines():
    metadata, relative = line.split('\t', 1)
    mode, revision, stage = metadata.split()
    if mode != '160000': continue
    source = ROOT / 'references' / Path(relative).name
    clone(source, module / relative, revision, changes=source.name == 'Hexalith.Platform')
    report['dependencies'][relative] = {'recorded': revision, 'qualifiedBase': git(module / relative, 'rev-parse', 'HEAD').decode().strip()}
platform = module / 'references/Hexalith.Platform/infrastructure/keycloak-workload-binding'
project = 'tests/Hexalith.Folders.Server.Tests/Hexalith.Folders.Server.Tests.csproj'
flags = ['-p:UseHexalithProjectReferences=false', '-p:UseNuGetDeps=true', '-p:NuGetAudit=true', '-p:NuGetAuditMode=all', '-p:NuGetAuditLevel=low', '-warnaserror', '-m:1', '-p:UseSharedCompilation=false', '-nr:false']
code = job('release-build', ['dotnet', 'build', project, '--configuration', 'Release', '--disable-build-servers', *flags], module)
if not code:
    assets = json.loads((module / 'tests/Hexalith.Folders.Server.Tests/obj/project.assets.json').read_text())
    deps = json.loads((module / 'tests/Hexalith.Folders.Server.Tests/bin/Release/net11.0/Hexalith.Folders.Server.Tests.deps.json').read_text())
    for relative, destination in [('obj/project.assets.json', 'release-project.assets.json'), ('bin/Release/net11.0/Hexalith.Folders.Server.Tests.deps.json', 'release-server.deps.json'), ('bin/Release/net11.0/sdk-binding.project.assets.json', 'release-bound-assets.json')]:
        (OUT / destination).write_bytes((module / 'tests/Hexalith.Folders.Server.Tests' / relative).read_bytes())
    (OUT / 'identity-inputs.json').write_text(json.dumps({'runtimeTarget': deps['runtimeTarget'], 'restoreFrameworks': assets['project'], 'sdkLibraries': {key: value for key, value in deps['libraries'].items() if key.startswith('Hexalith.EventStore.')}}, indent=2) + '\n')
    code = job('provider-build' , ['mvn', '--batch-mode', '--no-transfer-progress', 'package'], platform)
if not code:
    code = job('platform-fixture-tests', ['python3', '-B', '-m', 'unittest', 'discover', '-s', str(platform), '-p', 'test_component_fixture.py', '-v'], platform)
if not code:
    code = job('complete-server', ['pwsh', '-NoProfile', '-File', 'tests/tools/run-complete-project-tests.ps1', '-ProjectName', 'Hexalith.Folders.Server.Tests', '-ComponentEvidenceFile', str(OUT / 'complete-server-results.xml')], module)
report['releaseExitCode'] = code
source_flags = ['-p:UseHexalithProjectReferences=true', '-p:UseNuGetDeps=false', '-p:NuGetAudit=true', '-p:NuGetAuditMode=all', '-p:NuGetAuditLevel=low', '-warnaserror', '-m:1', '-p:UseSharedCompilation=false', '-nr:false']
source_code = job('debug-source-build', ['dotnet', 'build', project, '--configuration', 'Debug', '--disable-build-servers', *source_flags], module, env={'CI': 'false'})
if not source_code:
    source_code = job('source-component', ['python3', '-B', str(platform / 'verify_component.py'), '--sdk-assembly', str(module / 'tests/Hexalith.Folders.Server.Tests/bin/Debug/net11.0/Hexalith.Folders.Server.Tests.dll'), '--evidence-file', str(OUT / 'source-component-results.xml')], module)
report['sourceExitCode'] = source_code
report['exitCode'] = code or source_code
save()
raise SystemExit(report['exitCode'])
