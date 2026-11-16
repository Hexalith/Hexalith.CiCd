#!/usr/bin/env python3
"""Source-only Git fixture qualification; never a released module/adoption receipt."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

builds_source = Path(sys.argv[1]).resolve()
conversations_source = Path(sys.argv[2]).resolve()
scratch = Path(os.environ['TMPDIR']) / 'adapter-source-fixture'
scratch.mkdir()


def git(root, *arguments):
    return subprocess.check_output(['git', '-c', 'user.name=Source Qualification', '-c', 'user.email=source@example.invalid', *arguments], cwd=root, text=True).rstrip('\r\n')


def initialize(root):
    root.mkdir(parents=True, exist_ok=True)
    git(root, 'init', '-q', '-b', 'main')


def commit(root):
    git(root, 'add', '-A')
    git(root, 'commit', '-q', '-m', 'source qualification fixture')
    return git(root, 'rev-parse', 'HEAD')


# Source package identity is private to this fixture and is not a publication claim.
builds = scratch / 'active-builds'
shutil.copytree(builds_source, builds, ignore=shutil.ignore_patterns('bin', 'obj', 'artifacts', '.git'))
initialize(builds)
active = commit(builds)
git(builds, 'tag', 'v6.1.0')
old_catalog = '39973bfccb26ae98a3d25856a8f85950fecdf02a'
platform = scratch / 'platform'
initialize(platform)
(platform / 'hexalith-platform.json').write_text(json.dumps({'schemaVersion': 1, 'toolVersionRange': '[6.0.0,7.0.0)'}))
git(platform, 'add', 'hexalith-platform.json')
git(platform, 'update-index', '--add', '--cacheinfo', f'160000,{old_catalog},references/Hexalith.Builds')
git(platform, 'commit', '-q', '-m', 'source fixture Platform provenance')
platform_head = git(platform, 'rev-parse', 'HEAD')
git(platform, 'tag', 'v1.0.0')
module = scratch / 'module'
initialize(module)
for name in subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=conversations_source).decode().split('\0'):
    if name and (conversations_source / name).is_file():
        target = module / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(conversations_source / name, target)
shutil.copy2(conversations_source / 'module/hexalith.module-manifest.v2.json', module / 'module.json')
(module / '.config').mkdir(exist_ok=True)
(module / '.config/dotnet-tools.json').write_text(json.dumps({'version': 1, 'isRoot': True, 'tools': {'hexalith.builds.module.cli': {'version': '6.1.0', 'commands': ['hexalith-module'], 'rollForward': False}}}))
(module / 'references').mkdir(exist_ok=True)
subprocess.run(['git', 'clone', '-q', str(platform), str(module / 'references/Hexalith.Platform')], check=True)
git(module, 'add', '.')
for line in git(conversations_source, 'ls-tree', '-r', 'HEAD', '--', 'references').splitlines():
    metadata, path = line.split('\t')
    mode, kind, oid = metadata.split()
    if mode == '160000' and path != 'references/Hexalith.Platform':
        git(module, 'update-index', '--add', '--cacheinfo', f'160000,{oid},{path}')
git(module, "commit", "-q", "-m", "source fixture module")
head = git(module, "rev-parse", "HEAD")
git(module, 'remote', 'add', 'origin', 'https://github.com/Example/Fixture')
git(module, 'update-ref', 'refs/remotes/origin/main', head)
ci = scratch / 'candidate'
initialize(ci)
config_path = 'rendered/Fixture/.github/hexalith-ci.json'
config = json.dumps({'schema': 'hexalith.ci.v1', 'buildsTag': 'v6.1.0', 'moduleManifest': 'module.json'}).encode()
(ci / config_path).parent.mkdir(parents=True)
(ci / config_path).write_bytes(config)
git(ci, 'add', 'rendered')
git(ci, 'update-index', '--add', '--cacheinfo', f'160000,{head},references/Fixture')
git(ci, "commit", "-q", "-m", "source fixture candidate")
candidate = git(ci, "rev-parse", "HEAD")
source_digest = hashlib.sha256(git(module, 'ls-tree', '-r', 'HEAD').encode()).hexdigest()
authority = dict(schema='hexalith.managed-build.v1', kind='candidate-qualification', repository='Example/Fixture', moduleRoot=str(module), moduleHead=head, originalBuildsGitlink=old_catalog, buildsTag='v6.1.0', buildsCommit=active, buildsRoot=str(builds), deliveredSha=None, configurationDigest=hashlib.sha256(config).hexdigest(), perimeterDigest=None, platformCommit=platform_head, platformCatalogCommit=old_catalog, platformReleaseTag='v1.0.0', producerPin='6.1.0', qualification=dict(baselineHead=head, ownedBaselineDigest=source_digest, ownedProductDigest=source_digest, productDiffDigest=source_digest, ciCdRoot=str(ci), ciCdCandidate=candidate, candidateTree=git(ci, 'rev-parse', 'HEAD^{tree}'), renderedConfigPath=config_path, renderedConfigBlob=git(ci, 'rev-parse', f'HEAD:{config_path}'), producerSourceCommit=active))
receipt = scratch / 'authority.json'
receipt.write_text(json.dumps(authority))
command = [os.environ['HEXALITH_MANAGED_SOURCE_PACKAGE_TOOL'], 'prepare-qualified-build', '--manifest', str(module / 'module.json'), '--authority', str(receipt), '--workspace', str(scratch / 'producer'), '--output', 'json']
result = subprocess.run(command, cwd=module, capture_output=True, text=True, timeout=180)
print(result.stdout, result.stderr, flush=True)
result.check_returncode()
prepared = json.loads(result.stdout)
assert 'runId' not in prepared
values = prepared['buildPreparation']['environment']
assert len(values) == 7, values
print('Actual installed source package produced all seven runtime-free exports.', flush=True)
environment = os.environ.copy()
environment.update(values)
spec = importlib.util.spec_from_file_location('release_build', builds / 'Github/lib/release_build.py')
release = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = release
spec.loader.exec_module(release)
flags = release.release_flags('1.0.0', head, 'Example/Fixture')
project = 'tests/compatibility/MinimalModule/Hexalith.Conversations.MinimalModule.Compatibility.csproj'
for arguments in [['restore', project, *flags], ['msbuild', project, '-getItem:ProjectReference', '-getProperty:IsTestProject,IsPackable,IsPublishable,EnableDefaultCompileItems,TargetFramework,HexalithBuildsRoot,CustomAfterMicrosoftCommonTargets', *flags], ['build', project, '--no-restore', *flags]]:
    print('RUN dotnet', *arguments, flush=True)
    subprocess.run(['dotnet', *arguments], cwd=module, env=environment, check=True)
subprocess.run([sys.executable, str(module / 'tests/compatibility/MinimalModule/run_compatibility.py')], cwd=module, env=environment, check=True)
print('PRODUCT OVERLAY CHECKS: all three retained assertions under the actual producer-selected catalog.', flush=True)
subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/tooling', '-p', 'test_minimal_module_compatibility_overlay.py', '-v'], cwd=module, env=environment, check=True, timeout=120)
# These are disposable source-fixture mutations, never module bypass flags.
fixture_project = module / 'tests/fixtures/Hexalith.Conversations.MinimalModule/tests/Hexalith.Conversations.MinimalModule.Tests'
generated = fixture_project / 'obj/Hexalith.Conversations.MinimalModule.Tests.csproj.nuget.g.props'
original = generated.read_bytes()
generated.write_bytes(original.replace(b'</Project>', b'<PropertyGroup><NuGetAudit>false</NuGetAudit></PropertyGroup></Project>'))
refused = subprocess.run(['dotnet', 'build', project, '--no-restore', *flags], cwd=module, env=environment, capture_output=True, text=True, timeout=180)
print(refused.stdout, refused.stderr, flush=True)
assert refused.returncode != 0 and 'Generated NuGet import bytes differ' in refused.stdout
print('Altered generated NuGet policy import refused.', flush=True)
generated.write_bytes(original)
assets = fixture_project / 'obj/project.assets.json'
original_assets = assets.read_bytes()
changed = json.loads(original_assets)
next(iter(changed['libraries'].values()))['sha512'] = 'tampered-source-fixture'
assets.write_text(json.dumps(changed))
refused = subprocess.run(['dotnet', 'build', project, '--no-restore', *flags], cwd=module, env=environment, capture_output=True, text=True, timeout=180)
print(refused.stdout, refused.stderr, flush=True)
assert refused.returncode != 0 and 'restored assets graph differs' in refused.stdout
print('Altered restored library graph refused.', flush=True)
assets.write_bytes(original_assets)
for product in ['Hexalith.Conversations.Conformance.Tests', 'Hexalith.Conversations.Conformance.Portable.Tests', 'Hexalith.Conversations.TestSupport.Tests']:
    target = f'tests/{product}/{product}.csproj'
    print('STRICT PRODUCT SOURCE BUILD:', target, flush=True)
    subprocess.run(['dotnet', 'build', target, '-m:1', '-warnaserror', *flags], cwd=module, env=environment, check=True, timeout=300)
for suite, classes in [
    ('Hexalith.Conversations.Conformance.Tests', ['*DerivedProjectionKeyConformanceTest']),
    ('Hexalith.Conversations.Conformance.Portable.Tests', ['*ClientPublicApiConformanceTest', '*ReleaseBaselineValidationTest', '*ReleaseConformanceArtifactGenerationTest', '*NoInModuleSharedFakeDuplicateConformanceTest']),
]:
    command = ['dotnet', str(module / f'tests/{suite}/bin/Release/net11.0/{suite}.dll'), '-automated', 'sync', '-failSkips', '-noAutoReporters']
    for name in classes:
        command += ['-class', name]
    print('EXTRACTED PRODUCT SOURCE ASSERTIONS:', classes, flush=True)
    subprocess.run(command, cwd=module, env=environment, check=True, timeout=180)
print('SOURCE PACKAGE PRODUCTS: pack built outputs, five payload/symbol pairs, independent consumers.', flush=True)
subprocess.run([sys.executable, 'scripts/validate-built-packages.py'], cwd=module, env=environment, check=True, timeout=300)
subprocess.run([sys.executable, str(Path(__file__).with_name('qualify-testsupport-windows.py')), str(module / 'tests/Hexalith.Conversations.TestSupport.Tests/bin/Release/net11.0'), str(Path(__file__).with_name('testsupport-native-windows-source.log'))], check=True, timeout=260)
print('Strict Conformance, Portable and TestSupport product source compilation passed.', flush=True)
print('SOURCE QUALIFICATION ONLY: real managed adapter restore/build and exact seven fixture assertions passed; no released-tool or module adoption claim.', flush=True)
