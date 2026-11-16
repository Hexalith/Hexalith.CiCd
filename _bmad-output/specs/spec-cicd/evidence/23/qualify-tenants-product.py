"""Qualify the exact local Tenants candidate and direct pinned source projections.

Run under run-with-temp. No nested submodule operation or remote write occurs.
"""
import argparse
import datetime
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
parser.add_argument('--phase', choices=('build', 'contracts', 'unit', 'python', 'audit', 'metadata', 'released', 'focused'), default='build')
parser.add_argument('--attempt', default=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
args = parser.parse_args()
if not args.attempt.replace('-', '').isalnum(): raise ValueError('An immutable attempt identifier is required.')
source = args.source
root = Path(os.environ['TMPDIR']) / 'Hexalith.Tenants'
original = Path('/home/administrator/projects/hexalith/tenants')
evidence = Path(__file__).resolve().parent
record = {'attempt': args.attempt, 'phase': args.phase, 'source': str(source), 'startedAt': time.time(), 'commands': [], 'directPins': {}}

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
subprocess.run(['git', '-C', str(root), '-c', 'core.safecrlf=false', 'add', '-A'], check=True)
record['candidateTree'] = git(root, 'write-tree')
subprocess.run(['git', '-C', str(root), '-c', 'core.autocrlf=false', 'checkout-index', '--force', '--all'], check=True)
record['materialization'] = 'normalized Git index/tree, preserving explicit tracked eol attributes'
manifest = {}
for raw in subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z']).split(b'\0') + subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others', '--exclude-standard', '-z']).split(b'\0'):
    if not raw: continue
    relative = os.fsdecode(raw)
    path = source / relative
    if path.is_file() and not path.is_symlink():
        manifest[relative] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'mode': oct(path.stat().st_mode & 0o777)}
(evidence / ('product-manifest-' + args.phase + '-' + args.attempt + '.json')).open('x').write(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
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
    is_audit = arguments[:3] == ['dotnet', 'package', 'list'] and '--vulnerable' in arguments
    result = subprocess.run(arguments, cwd=root, env=environment, check=False, text=True, capture_output=is_audit)
    value = {'arguments': arguments, 'exitCode': result.returncode, 'elapsedSeconds': time.monotonic() - started}
    semantic_exit = result.returncode
    if is_audit:
        print(result.stdout, flush=True)
        print(result.stderr, file=sys.stderr, flush=True)
        (evidence / ('product-audit-' + args.attempt + '.json')).open('x').write(result.stdout)
        try:
            report = json.loads(result.stdout)
            vulnerabilities = []
            for project in report.get('projects', []):
                for framework in project.get('frameworks', []):
                    for group in ('topLevelPackages', 'transitivePackages'):
                        for package in framework.get(group, []):
                            for advisory in package.get('vulnerabilities', []):
                                vulnerabilities.append({'project': project.get('path'), 'framework': framework.get('framework'),
                                    'package': package.get('id'), 'resolvedVersion': package.get('resolvedVersion'), **advisory})
            record['auditFindings'] = vulnerabilities
            record['auditErrors'] = report.get('errors', [])
            value['vulnerabilityCount'] = len(vulnerabilities)
            if vulnerabilities or record['auditErrors']: semantic_exit = 1
            record['auditResult'] = 'passed' if not semantic_exit else 'failed'
        except (ValueError, TypeError, KeyError) as error:
            semantic_exit = 1
            record['auditResult'] = 'unverified: output was not a complete machine-readable report'
        value['semanticExitCode'] = semantic_exit
    record['commands'].append(value)
    print('RESULT', json.dumps(value), flush=True)
    return semantic_exit

result = 0
try:
    print('INPUTS', json.dumps({key: value for key, value in record.items() if key != 'commands'}, sort_keys=True), flush=True)
    if args.phase == 'released':
        released = Path(os.environ['TMPDIR']) / 'released-builds'
        revision = git(original / 'references/Hexalith.Builds', 'rev-parse', 'v6.0.6^{commit}')
        if revision != 'fdda17c0a4538b0f7c99f813c20ca24b49006530': raise ValueError('The verified released contract changed.')
        clone(original / 'references/Hexalith.Builds', released, revision)
        sys.path.insert(0, str(released / 'Github/lib'))
        import ci_pipeline, ci_config, guard_actions, guard_tools, perimeter
        document = {'schema': ci_config.schema_identity(), 'buildsTag': 'v6.0.6', 'solution': 'Hexalith.Tenants.slnx',
                    'dapr': True, 'browsers': True, 'registry': False, 'codeql': ['csharp'],
                    'hooks': ['after-unit-tests', 'after-integration-tests', 'nightly'], 'jobs': {},
                    'submodules': ['references/Hexalith.EventStore', 'references/Hexalith.Platform', 'references/Hexalith.Memories'],
                    'tests': {'integration': ['tests/Hexalith.Tenants.Server.Tests/Hexalith.Tenants.Server.Tests.csproj'],
                              'exclude': {'tests/Hexalith.Tenants.IntegrationTests/Hexalith.Tenants.IntegrationTests.csproj': 'after-integration-tests'}}}
        ci_config.validate_config(document, repository='Hexalith/Hexalith.Tenants')
        prepared = ci_pipeline.PreparedConfig(root, root, document, document['solution'], 'global.json', ())
        record['releasedContract'] = {'tag': 'v6.0.6', 'revision': revision, 'inMemoryTestRoutingOnly': document, 'deliveredStateFabricated': False}
        subprocess.run(['git', '-C', str(root), 'add', '-A'], check=True)
        tree = git(root, 'write-tree')
        record['candidateTree'] = tree
        snapshot = perimeter.Git(root).snapshot(tree)
        tools_directory = Path(os.environ['TMPDIR']) / 'guard-tools'; tools_directory.mkdir()
        tools = guard_tools.Tools(tools_directory)
        guard_actions.lint(snapshot, tools)
        record['customActionPolicy'] = 'passed released guard_actions.lint on exact candidate tree'
        message = 'build: migrate Tenants product checks\n'
        tools.lint_message(message, 'prospective product commit')
        shutil.copyfile(root / 'commitlint.config.mjs', tools_directory / 'module-commitlint.config.mjs')
        tools._run(['node', str(tools_directory / 'node_modules/@commitlint/cli/cli.js'), '--config', str(tools_directory / 'module-commitlint.config.mjs'), '--color=false'], 'owning module commitlint', message)
        record['commitlint'] = {'version': '21.2.4', 'message': message, 'releasedPolicy': 'passed', 'owningModulePolicy': 'passed'}
        try:
            print('RELEASED API restore_and_build v6.0.6', flush=True)
            ci_pipeline.restore_and_build(prepared)
            record['releasedBuild'] = 'passed'
            print('RELEASED API run_unit_tests v6.0.6', flush=True)
            classified = ci_pipeline.run_unit_tests(prepared, repository='Hexalith/Hexalith.Tenants')
            record['releasedUnits'] = 'passed'
            record['classification'] = {key: list(getattr(classified, key)) for key in ('unit', 'integration', 'excluded')}
            print('RELEASED API run_integration_tests v6.0.6 (model/server projects)', flush=True)
            ci_pipeline.run_integration_tests(prepared, repository='Hexalith/Hexalith.Tenants')
            record['releasedIntegrationProjects'] = 'passed'
            result = run(['dotnet', 'test', '--project', 'tests/Hexalith.Tenants.IntegrationTests/Hexalith.Tenants.IntegrationTests.csproj', '--configuration', 'Release', '--no-build', '--no-restore', '--filter-class', 'Hexalith.Tenants.IntegrationTests.CatalogRedisBackendTests', '--minimum-expected-tests', '13', '--fail-skips', 'on'])
            record['databaseReaderChecks'] = 'passed' if not result else 'failed'
            coverage = run(['python3', 'scripts/validate-coverage.py', '--coverage-root', 'TestResults', '--minimum-line-coverage', '80', '--required-branch-coverage', '100',
                '--line-scope', 'src/Hexalith.Tenants.Contracts/', '--line-scope', 'src/Hexalith.Tenants.Client/',
                '--line-scope', 'src/Hexalith.Tenants.Server/', '--line-scope', 'src/Hexalith.Tenants.Testing/',
                '--isolation-auth-target', 'src/Hexalith.Tenants.Server/Aggregates/TenantAggregate.cs',
                '--isolation-auth-target', 'src/Hexalith.Tenants.Server/Aggregates/GlobalAdministratorsAggregate.cs',
                '--isolation-auth-target', 'src/Hexalith.Tenants.Server/Validators/ChangeUserRoleValidator.cs',
                '--isolation-auth-target', 'src/Hexalith.Tenants.Server/Projections/TenantAuditOwnership.cs'])
            record['coverage'] = 'passed' if not coverage else 'failed'
            result = result or coverage
        except Exception as error:
            result = getattr(error, 'returncode', 1)
            record['releasedRoutineFailure'] = str(error)
            print('RELEASED ROUTINE FAILURE', str(error), flush=True)
        audit = run(['dotnet', 'package', 'list', '--project', 'Hexalith.Tenants.slnx', '--vulnerable', '--include-transitive', '--format', 'json', '--no-restore'])
        record['auditCommandExitCode'] = audit
        result = result or audit
    elif args.phase == 'focused':
        target = 'tests/Hexalith.Tenants.IntegrationTests/Hexalith.Tenants.IntegrationTests.csproj'
        result = run(['dotnet', 'restore', target, '--disable-build-servers', *flags])
        if not result:
            result = run(['dotnet', 'build', target, '--no-restore', '--disable-build-servers', *flags])
        record['aspireRestoredAssets'] = {}
        for project_directory in ('src/Hexalith.Tenants.AppHost', 'tests/Hexalith.Tenants.IntegrationTests'):
            assets = root / project_directory / 'obj/project.assets.json'
            if assets.is_file():
                resolved = json.loads(assets.read_text())
                record['aspireRestoredAssets'][project_directory] = {
                    name: {'sha512': package.get('sha512'), 'type': package.get('type')}
                    for name, package in resolved['libraries'].items() if name.lower().startswith(('aspire.', 'microsoft.developercontrolplane.'))}
        record['nativeAspireCliInvoked'] = False
        if not result:
            result = run(['dotnet', 'test', '--project', target, '--no-build', '--no-restore', '--configuration', 'Release',
                          '--filter-class', 'Hexalith.Tenants.IntegrationTests.CatalogRedisBackendTests', '--minimum-expected-tests', '13', '--fail-skips', 'on'])
        if not result:
            record['liveClassDiscovery'] = {}
            for class_name in ('AuthenticatedTenantsRouteTests', 'AspireTopologyTests', 'TenantsUiRouteSmokeTests',
                               'AuthenticatedTenantsUiRouteTests', 'SourceCatalogOwnerProfileTests'):
                command = ['dotnet', 'test', '--project', target, '--no-build', '--no-restore', '--configuration', 'Release',
                           '--list-tests', 'text', '--filter-class', 'Hexalith.Tenants.IntegrationTests.' + class_name]
                discovered = subprocess.run(command, cwd=root, env=environment, text=True, capture_output=True, timeout=120)
                print(discovered.stdout, flush=True)
                print(discovered.stderr, file=sys.stderr, flush=True)
                record['liveClassDiscovery'][class_name] = {'exitCode': discovered.returncode, 'output': discovered.stdout}
                record['commands'].append({'arguments': command, 'exitCode': discovered.returncode})
                result = result or discovered.returncode
            record['ownerCohortDiscovered'] = 'ActualOwnerCohortCommitsCompleteV2AndPreservesOwnedBootstrapAndRestEffects' in record['liveClassDiscovery']['SourceCatalogOwnerProfileTests']['output']
            if not record['ownerCohortDiscovered']: result = 1
        for name in ('test_source_catalog_profile.py', 'test_product_integration.py'):
            result = run([sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-p', name, '-v']) or result
        patch = subprocess.check_output(['git', '-C', str(root), 'diff', '--cached', '--binary', '--no-ext-diff', 'HEAD'])
        patch_path = evidence / ('product-candidate-' + args.attempt + '.patch')
        patch_path.open('xb').write(patch)
        record['candidatePatch'] = {'path': patch_path.name, 'sha256': hashlib.sha256(patch).hexdigest()}
        final_inputs = {row.split('\t', 1)[1]: row.split()[1] for row in git(root, 'ls-files', '--stage').splitlines()}
        prior_inputs = json.loads((evidence / 'product-normalized-inputs-released-03.json').read_text())
        record['changesAfterReleased03'] = [entry['path'] for entry in prior_inputs['checks']
            if final_inputs.get(entry['path']) != entry.get('testedBlob')]
        record['normalizedInputs'] = final_inputs
    elif args.phase in ('build', 'contracts', 'unit', 'audit'):
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
        result = run([sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-p', 'test_*.py', '-v'])
        for name in ('test_bootstrap_handoff.py', 'test_catalog_artifact_guards.py', 'test_catalog_package_consumer.py',
                     'test_dapr_read_policy_evidence.py', 'test_hosted_package_profile.py', 'test_release_validation_context.py',
                     'test_tenant_audit_source_provenance.py'):
            code = run([sys.executable, 'tests/scripts/' + name])
            result = result or code
    else:
        for project in ('src/Hexalith.Tenants.AppHost/Hexalith.Tenants.AppHost.csproj',
                        'src/Hexalith.Tenants.UI/Hexalith.Tenants.UI.csproj',
                        'tests/Hexalith.Tenants.UI.Tests/Hexalith.Tenants.UI.Tests.csproj'):
            code = run(['dotnet', 'msbuild', project, '-nologo', *flags,
                        '-getProperty:HexalithFrontComposerFromSource,HexalithMemoriesFromSource,HexalithEventStoreFromSource,HexalithEventStoreVersion',
                        '-getItem:ProjectReference,PackageReference'])
            result = result or code
except Exception as error:
    result = getattr(error, 'returncode', 1)
    record['qualificationFailure'] = str(error)
    print('QUALIFICATION FAILURE', str(error), flush=True)
finally:
    record['finishedAt'] = time.time()
    record['exitCode'] = result
    (evidence / ('product-local-' + args.phase + '-' + args.attempt + '.json')).open('x').write(json.dumps(record, indent=2) + '\n')
sys.exit(result)
