"""Qualify the exact local Tenants candidate and direct pinned source projections.

Run under run-with-temp. No nested submodule operation or remote write occurs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=Path('/home/administrator/projects/hexalith/tenants-story-23-product'))
parser.add_argument('--phase', choices=('build', 'contracts', 'unit', 'python', 'audit', 'metadata'), default='build')
args = parser.parse_args()
source = args.source
root = Path(os.environ['TMPDIR']) / 'Hexalith.Tenants'
original = Path('/home/administrator/projects/hexalith/tenants')
evidence = Path(__file__).resolve().parent
record = {'phase': args.phase, 'source': str(source), 'startedAt': time.time(), 'commands': [], 'directPins': {}}

def git(repository, *arguments):
    return subprocess.check_output(['git', '-C', str(repository), *arguments], text=True).strip()

def clone(repository, target, revision):
    subprocess.run(['git', 'clone', '--quiet', '--local', '--shared', '--no-recurse-submodules', '--no-checkout', str(repository), str(target)], check=True)
    subprocess.run(['git', '-C', str(target), 'checkout', '--quiet', '--detach', revision], check=True)

record['baseline'] = git(source, 'rev-parse', 'HEAD')
clone(source, root, record['baseline'])
changes = (subprocess.check_output(['git', '-C', str(source), 'diff', '--name-only', '--no-ext-diff', 'HEAD', '-z'])
           + subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others', '--exclude-standard', '-z'])).split(b'\0')
for raw in set(changes) - {b''}:
    relative = os.fsdecode(raw)
    path, target = source / relative, root / relative
    if path.is_file() and not path.is_symlink():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    elif not path.exists() and target.is_file():
        target.unlink()
for name in ('Builds', 'EventStore', 'Platform', 'Memories'):
    module = 'Hexalith.' + name
    revision = git(source, 'rev-parse', 'HEAD:references/' + module)
    record['directPins'][module] = revision
    clone(original / 'references' / module, root / 'references' / module, revision)
manifest = {}
for raw in subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z']).split(b'\0') + subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others', '--exclude-standard', '-z']).split(b'\0'):
    if not raw: continue
    relative = os.fsdecode(raw)
    path = source / relative
    if path.is_file() and not path.is_symlink():
        manifest[relative] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'mode': oct(path.stat().st_mode & 0o777)}
record['candidateManifestSha256'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
record['nestedSubmodulesInitialized'] = False
flags = ['-noAutoResponse', '-p:Configuration=Release', '-warnaserror', '-p:UseHexalithProjectReferences=false',
         '-p:UseNuGetDeps=true', '-p:HexalithFrontComposerFromSource=false', '-p:HexalithMemoriesFromSource=false',
         '-p:ShouldUnsetParentConfigurationAndPlatform=false', '-p:EnableNETAnalyzers=true', '-p:RunAnalyzers=true',
         '-p:RunAnalyzersDuringBuild=true', '-p:UseSharedCompilation=false', '-nr:false', '-m:1',
         '-p:RestoreConfigFile=' + str(root / 'references/Hexalith.Builds/NuGet.ci.Config')]
environment = {**os.environ, 'DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER': '1', 'DOTNET_CLI_USE_MSBUILD_SERVER': '0',
               'MSBUILDDISABLENODEREUSE': '1', 'PYTHONDONTWRITEBYTECODE': '1'}

def run(arguments):
    print('RUN', json.dumps(arguments), flush=True)
    started = time.monotonic()
    result = subprocess.run(arguments, cwd=root, env=environment, check=False)
    value = {'arguments': arguments, 'exitCode': result.returncode, 'elapsedSeconds': time.monotonic() - started}
    record['commands'].append(value)
    print('RESULT', json.dumps(value), flush=True)
    return result.returncode

result = 0
try:
    print('INPUTS', json.dumps({key: value for key, value in record.items() if key != 'commands'}, sort_keys=True), flush=True)
    if args.phase in ('build', 'contracts', 'unit', 'audit'):
        target = 'tests/Hexalith.Tenants.Contracts.Tests/Hexalith.Tenants.Contracts.Tests.csproj' if args.phase == 'contracts' else 'Hexalith.Tenants.slnx'
        result = run(['dotnet', 'restore', target, '--disable-build-servers', *flags])
        if args.phase == 'audit':
            audit = run(['dotnet', 'package', 'list', '--project', target, '--vulnerable', '--include-transitive', '--format', 'json', '--no-restore'])
            result = result or audit
        elif not result:
            result = run(['dotnet', 'build', target, '--no-restore', '--disable-build-servers', *flags])
        if not result and args.phase == 'contracts':
            result = run(['dotnet', 'test', '--project', target, '--no-build', '--no-restore', '--configuration', 'Release',
                          '--stop-on-fail', 'off', '--fail-skips', 'on'])
        if not result and args.phase == 'unit':
            for project in ('Contracts', 'Client', 'Testing', 'UI'):
                target = f'tests/Hexalith.Tenants.{project}.Tests/Hexalith.Tenants.{project}.Tests.csproj'
                result = run(['dotnet', 'test', '--project', target, '--no-build', '--no-restore', '--configuration', 'Release',
                              '--stop-on-fail', 'off', '--fail-skips', 'on'])
                if result: break
            if not result:
                result = run(['dotnet', 'test', '--project', 'samples/Hexalith.Tenants.Sample.Tests/Hexalith.Tenants.Sample.Tests.csproj',
                              '--no-build', '--no-restore', '--configuration', 'Release', '--stop-on-fail', 'off', '--fail-skips', 'on'])
    elif args.phase == 'python':
        for directory, pattern in (('scripts/tests', 'test_*.py'), ('tests/scripts', 'test_*.py')):
            code = run([sys.executable, '-m', 'unittest', 'discover', '-s', directory, '-p', pattern, '-v'])
            result = result or code
    else:
        for project in ('src/Hexalith.Tenants.AppHost/Hexalith.Tenants.AppHost.csproj',
                        'src/Hexalith.Tenants.UI/Hexalith.Tenants.UI.csproj',
                        'tests/Hexalith.Tenants.UI.Tests/Hexalith.Tenants.UI.Tests.csproj'):
            code = run(['dotnet', 'msbuild', project, '-nologo', *flags,
                        '-getProperty:HexalithFrontComposerFromSource,HexalithMemoriesFromSource,HexalithEventStoreFromSource,HexalithEventStoreVersion',
                        '-getItem:ProjectReference,PackageReference'])
            result = result or code
finally:
    record['finishedAt'] = time.time()
    record['exitCode'] = result
    (evidence / ('product-local-' + args.phase + '.json')).write_text(json.dumps(record, indent=2) + '\n')
sys.exit(result)
