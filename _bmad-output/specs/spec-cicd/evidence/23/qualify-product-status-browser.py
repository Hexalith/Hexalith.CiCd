"""Qualify current-main package-backed status-label browser controls under run-with-temp."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import tarfile
import urllib.request
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('--attempt', required=True)
args = parser.parse_args()
if not args.attempt.replace('-', '').isalnum(): raise ValueError('An immutable attempt name is required.')
source = Path('/home/administrator/projects/hexalith/tenants-story-23-current')
evidence = Path(__file__).resolve().parent
root = Path(os.environ['TMPDIR']) / 'Tenants'
record = {'attempt': args.attempt, 'source': str(source), 'commands': [], 'startedAt': time.time(),
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
pin = git(source, 'rev-parse', 'HEAD:references/Hexalith.Builds')
clone(Path('/home/administrator/projects/hexalith/tenants/references/Hexalith.Builds'), root / 'references/Hexalith.Builds', pin)
record['materializedDirectDependency'] = {'Hexalith.Builds': pin}
environment = {**os.environ, 'DOTNET_CLI_HOME': str(Path(os.environ['TMPDIR']) / 'dotnet-home'),
    'NUGET_PACKAGES': str(Path(os.environ['TMPDIR']) / 'packages'), 'DOTNET_NOLOGO': '1',
    'DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER': '1', 'DOTNET_CLI_USE_MSBUILD_SERVER': '0', 'MSBUILDDISABLENODEREUSE': '1'}
target = 'tests/Hexalith.Tenants.UI.Tests/Hexalith.Tenants.UI.Tests.csproj'
flags = ['-noAutoResponse', '-p:Configuration=Release', '-warnaserror', '-p:UseHexalithProjectReferences=false', '-p:UseNuGetDeps=true',
    '-p:HexalithFrontComposerFromSource=false', '-p:HexalithMemoriesFromSource=false', '-p:EnableNETAnalyzers=true',
    '-p:RunAnalyzers=true', '-p:RunAnalyzersDuringBuild=true', '-p:UseSharedCompilation=false', '-nr:false', '-m:1',
    '-p:RestoreConfigFile=' + str(root / 'references/Hexalith.Builds/NuGet.ci.Config')]
def run(arguments, *, capture=False):
    print('RUN', json.dumps(arguments), flush=True)
    started = time.monotonic()
    completed = subprocess.run(arguments, cwd=root, env=environment, timeout=300, check=False, text=True, capture_output=capture)
    if capture:
        print(completed.stdout, flush=True)
        print(completed.stderr, flush=True)
        if completed.returncode == 0:
            report = json.loads(completed.stdout.strip().splitlines()[-1])
            record['browserReport'] = report
    result = {'arguments': arguments, 'exitCode': completed.returncode, 'elapsedSeconds': time.monotonic() - started}
    record['commands'].append(result)
    print('RESULT', json.dumps(result), flush=True)
    return completed.returncode
result = 0
try:
    result = run(['dotnet', 'restore', target, '--disable-build-servers', *flags])
    if not result:
        assets = json.loads((root / 'tests/Hexalith.Tenants.UI.Tests/obj/project.assets.json').read_text())
        record['selectedPackages'] = {key: value for key, value in assets['libraries'].items()
            if key.startswith(('Microsoft.FluentUI.', 'bunit/', 'Hexalith.FrontComposer.'))}
        result = run(['dotnet', 'build', target, '--no-restore', '--disable-build-servers', *flags])
    if not result:
        for name, class_name, minimum in (('status-label', 'StatusFilterLabelRenderingTests', '16'),
                                          ('list-surface', 'TenantListSurfaceTests', '84')):
            command = ['dotnet', 'test', '--project', target, '--no-build', '--no-restore', '--configuration', 'Release',
                '--filter-class', 'Hexalith.Tenants.UI.Tests.Components.' + class_name,
                '--minimum-expected-tests', minimum, '--fail-skips', 'on', '--report-xunit-trx',
                '--report-xunit-trx-filename', name + '.trx', '--results-directory', str(Path(os.environ['TMPDIR']) / name)]
            result = run(command) or result
            reports = list((Path(os.environ['TMPDIR']) / name).rglob('*.trx'))
            if len(reports) != 1: raise ValueError('One complete focused TRX report is required.')
            tree = ET.parse(reports[0])
            record.setdefault('testSuites', {})[name] = {'counters': tree.find('.//{*}Counters').attrib,
                'cases': [{'name': item.get('testName'), 'outcome': item.get('outcome')} for item in tree.findall('.//{*}UnitTestResult')]}
    if not result:
        node_version = '24.22.3'
        archive_name = 'node-v' + node_version + '-linux-x64.tar.xz'
        archive = Path(os.environ['TMPDIR']) / archive_name
        checksums = urllib.request.urlopen('https://nodejs.org/dist/v' + node_version + '/SHASUMS256.txt', timeout=60).read().decode()
        expected = next(row.split()[0] for row in checksums.splitlines() if row.split()[-1] == archive_name)
        archive.write_bytes(urllib.request.urlopen('https://nodejs.org/dist/v' + node_version + '/' + archive_name, timeout=90).read())
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual != expected: raise ValueError('The exact Node runtime archive digest differs.')
        with tarfile.open(archive) as package: package.extractall(Path(os.environ['TMPDIR']), filter='data')
        node_bin = Path(os.environ['TMPDIR']) / ('node-v' + node_version + '-linux-x64/bin')
        environment.update(PATH=str(node_bin) + os.pathsep + environment['PATH'],
            npm_config_cache=str(Path(os.environ['TMPDIR']) / 'npm-cache'),
            PLAYWRIGHT_BROWSERS_PATH=str(Path(os.environ['TMPDIR']) / 'browsers'))
        record['nodeRuntime'] = {'version': subprocess.check_output([str(node_bin / 'node'), '--version'], text=True).strip(),
            'npm': subprocess.check_output([str(node_bin / 'npm'), '--version'], env=environment, text=True).strip(),
            'archive': archive_name, 'sha256': actual, 'officialDigestVerified': True}
        if record['nodeRuntime']['version'] != 'v24.22.3' or record['nodeRuntime']['npm'] != '11.19.1':
            raise ValueError('The exact paired Node/npm runtime differs.')
        functional = root / 'tests/performance/tenant-audit'
        result = run([str(node_bin / 'npm'), 'ci', '--prefix', str(functional)])
        if not result:
            manifest_path = functional / 'node_modules/playwright-core/browsers.json'
            manifest = json.loads(manifest_path.read_text())
            chromium = next(item for item in manifest['browsers'] if item['name'] == 'chromium')
            record['playwrightBrowserManifest'] = {'packageVersion': json.loads((functional / 'node_modules/playwright-core/package.json').read_text())['version'],
                'chromium': chromium, 'sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
            result = run([str(node_bin / 'node'), str(functional / 'node_modules/playwright/cli.js'), 'install', 'chromium', '--no-shell'])
        if not result:
            browser = subprocess.check_output([str(node_bin / 'node'), '-e', "console.log(require('@playwright/test').chromium.executablePath())"],
                cwd=functional, env=environment, text=True).strip()
            version = subprocess.check_output([browser, '--version'], text=True).strip()
            if chromium['browserVersion'] not in version: raise ValueError('The selected Chromium version differs from its locked manifest.')
            record['chromium'] = {'version': version, 'sha256': hashlib.sha256(Path(browser).read_bytes()).hexdigest(),
                'playwrightRevision': chromium['revision']}
            result = run([str(node_bin / 'node'), 'tests/Hexalith.Tenants.UI.Tests/Browser/validate-status-filter-label-browser.mjs',
                          'Release', browser, '30'], capture=True)
except BaseException as error:
    result = 1
    record['jobFailure'] = type(error).__name__
    raise
finally:
    record['exitCode'] = result
    record['finishedAt'] = time.time()
    (evidence / ('product-local-' + args.attempt + '.json')).open('x').write(json.dumps(record, indent=2) + '\n')
raise SystemExit(result)
