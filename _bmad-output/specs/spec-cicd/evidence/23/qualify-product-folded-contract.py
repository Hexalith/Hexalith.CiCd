"""Qualify current-main package-backed folded snapshot contract observation under run-with-temp."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('--attempt', required=True)
args = parser.parse_args()
if not args.attempt.replace('-', '').isalnum(): raise ValueError('An immutable attempt name is required.')
source = Path('/home/administrator/projects/hexalith/tenants-story-23-current')
evidence = Path(__file__).resolve().parent
root = Path(os.environ['TMPDIR']) / 'Tenants'
record = {'qualification': 'scratch-only capability gap diagnosis; no product changes, enrollment, parity or performance pass', 'attempt': args.attempt, 'source': str(source), 'commands': [], 'startedAt': time.time(),
          'nativeAppHostLaunched': False, 'nestedSubmodulesInitialized': False}
def git(repository, *arguments):
    return subprocess.check_output(['git', '-C', str(repository), *arguments], text=True).strip()
def clone(repository, target, revision):
    subprocess.run(['git', 'clone', '--quiet', '--local', '--shared', '--no-recurse-submodules', '--no-checkout', str(repository), str(target)], check=True)
    subprocess.run(['git', '-C', str(target), 'checkout', '--quiet', '--detach', revision], check=True)
record['baseline'] = git(source, 'rev-parse', 'HEAD')
clone(source, root, record['baseline'])
changes = set(subprocess.check_output(['git', '-C', str(source), 'diff', '--name-only', 'HEAD', '-z']).split(b'\0')
    + subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others', '--exclude-standard', '-z']).split(b'\0')) - {b''}
for raw in changes:
    relative = os.fsdecode(raw)
    path, target = source / relative, root / relative
    if path.is_file() and not path.is_symlink():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    elif not path.exists() and target.is_file(): target.unlink()
subprocess.run(['git', '-C', str(root), '-c', 'core.safecrlf=false', 'add', '-A'], check=True)
record['candidateTree'] = git(root, 'write-tree')
record['changesAfterParentCommit'] = git(root, 'diff', '--cached', '--name-only', 'HEAD').splitlines()
record['normalizedInputs'] = {row.split('\t', 1)[1]: row.split()[1] for row in git(root, 'ls-files', '--stage').splitlines()}
subprocess.run(['git', '-C', str(root), '-c', 'core.autocrlf=false', 'checkout-index', '--force', '--all'], check=True)
manifest = {}
paths = set(subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z']).split(b'\0')
    + subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others', '--exclude-standard', '-z']).split(b'\0')) - {b''}
for raw in paths:
    relative = os.fsdecode(raw)
    path = source / relative
    if path.is_file() and not path.is_symlink(): manifest[relative] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'mode': oct(path.stat().st_mode & 0o777)}
(evidence / ('product-manifest-' + args.attempt + '.json')).open('x').write(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
patch = subprocess.check_output(['git', '-C', str(root), 'diff', '--cached', '--binary', '--no-ext-diff', 'HEAD'])
patch_path = evidence / ('product-candidate-' + args.attempt + '.patch')
patch_path.open('xb').write(patch)
record['candidatePatch'] = {'path': patch_path.name, 'sha256': hashlib.sha256(patch).hexdigest()}
record['materializedDirectDependencies'] = {}
for name in ('Builds',):
    module = 'Hexalith.' + name
    pin = git(source, 'rev-parse', 'HEAD:references/' + module)
    clone(Path('/home/administrator/projects/hexalith/tenants/references') / module, root / 'references' / module, pin)
    record['materializedDirectDependencies'][module] = pin
environment = {**os.environ, 'DOTNET_CLI_HOME': str(Path(os.environ['TMPDIR']) / 'dotnet-home'),
    'NUGET_PACKAGES': str(Path(os.environ['TMPDIR']) / 'packages'), 'DOTNET_NOLOGO': '1',
    'DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER': '1', 'DOTNET_CLI_USE_MSBUILD_SERVER': '0', 'MSBUILDDISABLENODEREUSE': '1'}
record['sdkVersion'] = subprocess.check_output(['dotnet', '--version'], cwd=root, env=environment, text=True).strip()
probe = root / 'contract-probe'
probe.mkdir()
probe_source = evidence / 'FoldedSnapshotContractProbe.cs'
shutil.copyfile(probe_source, probe / 'Program.cs')
project = '<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup><OutputType>Exe</OutputType><IsPackable>false</IsPackable><IsTestProject>false</IsTestProject></PropertyGroup>\n  <ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App" /></ItemGroup>\n  <ItemGroup><ProjectReference Include="../src/Hexalith.Tenants.Server/Hexalith.Tenants.Server.csproj" /></ItemGroup>\n  <ItemGroup><PackageReference Include="Hexalith.EventStore.DomainService" /></ItemGroup>\n</Project>\n'
(probe / 'ContractProbe.csproj').write_text(project)
record['probe'] = {'sourceSha256': hashlib.sha256(probe_source.read_bytes()).hexdigest(),
                   'project': project, 'scratchOnly': True}
target = 'contract-probe/ContractProbe.csproj'
flags = ['-noAutoResponse', '-p:Configuration=Release', '-warnaserror', '-p:UseHexalithProjectReferences=false', '-p:UseNuGetDeps=true',
    '-p:HexalithFrontComposerFromSource=false', '-p:HexalithMemoriesFromSource=false', '-p:EnableNETAnalyzers=true',
    '-p:ShouldUnsetParentConfigurationAndPlatform=false', '-p:RunAnalyzers=true', '-p:RunAnalyzersDuringBuild=true', '-p:UseSharedCompilation=false', '-nr:false', '-m:1',
    '-p:RestoreConfigFile=' + str(root / 'references/Hexalith.Builds/NuGet.ci.Config')]
def run(arguments):
    print('RUN', json.dumps(arguments), flush=True)
    started = time.monotonic()
    completed = subprocess.run(arguments, cwd=root, env=environment, timeout=180, check=False)
    result = {'arguments': arguments, 'exitCode': completed.returncode, 'elapsedSeconds': time.monotonic() - started}
    record['commands'].append(result)
    print('RESULT', json.dumps(result), flush=True)
    return completed.returncode
result = 0
try:
    result = run(['dotnet', 'restore', target, '--disable-build-servers', *flags])
    if not result:
        assets = json.loads((probe / 'obj/project.assets.json').read_text())
        record['selectedPackages'] = {name: value for name, value in assets['libraries'].items()
            if name.startswith('Hexalith.EventStore.')}
        import xml.etree.ElementTree as ET
        record['packageRepositoryMetadata'] = {}
        for package in ('client', 'contracts', 'domainservice', 'server'):
            nuspec = Path(environment['NUGET_PACKAGES']) / ('hexalith.eventstore.' + package) / '5.1.1' / ('hexalith.eventstore.' + package + '.nuspec')
            document = ET.parse(nuspec)
            repository = document.find('.//{*}repository')
            record['packageRepositoryMetadata'][package] = repository.attrib
        result = run(['dotnet', 'build', target, '--no-restore', '--disable-build-servers', *flags])
    if not result:
        arguments = ['dotnet', str(probe / 'bin/Release/net11.0/ContractProbe.dll')]
        started = time.monotonic()
        completed = subprocess.run(arguments, cwd=root, env=environment, timeout=60, text=True, capture_output=True)
        print(completed.stdout, flush=True)
        print(completed.stderr, flush=True)
        result = completed.returncode
        record['commands'].append({'arguments': arguments, 'exitCode': result, 'elapsedSeconds': time.monotonic() - started})
        if not result:
            record['capabilityObservation'] = json.loads(completed.stdout)
except BaseException as error:
    result = 1
    record['jobFailure'] = type(error).__name__
    raise
finally:
    record['exitCode'] = result
    record['finishedAt'] = time.time()
    (evidence / ('product-local-' + args.attempt + '.json')).open('x').write(json.dumps(record, indent=2) + '\n')
raise SystemExit(result)
