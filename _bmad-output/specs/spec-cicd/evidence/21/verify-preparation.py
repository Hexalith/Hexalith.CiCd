#!/usr/bin/env python3
"""Qualify local preparation in a standalone clone using only local Git objects.

Run under run-with-temp. No Git network operations, submodule initialization,
commits, or remote mutations are performed. Package restore may access NuGet.
"""
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone
import uuid
import os
import shutil
import subprocess
import time

CICD = Path(__file__).resolve().parents[5]
PARTIES = CICD / 'references/Hexalith.Parties'
LOCAL = Path('/home/administrator/projects/hexalith/cicd/references')
EVIDENCE = Path(__file__).resolve().parent
RESULTS = EVIDENCE / 'runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
RESULTS.mkdir(parents=True)
print('Evidence:', RESULTS, flush=True)
WORK = Path(os.environ['TMPDIR'])
MODULE = WORK / 'Hexalith.Parties'
RECORD = {'commands': [], 'git_network': False, 'submodule_initialization': False}


def command(args, *, cwd=None, log=None, check=True, input=None):
    started = time.monotonic()
    if log:
        with (RESULTS/log).open('wb') as output:
            result = subprocess.run(args, cwd=cwd, input=input, stdout=output,
                                    stderr=subprocess.STDOUT, timeout=1800)
        result.stdout = (RESULTS/log).read_bytes()
    else:
        result = subprocess.run(args, cwd=cwd, input=input, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=1800)
    RECORD['commands'].append({'command': list(map(str,args)), 'cwd': str(cwd or Path.cwd()),
                               'elapsed_seconds': round(time.monotonic()-started,3),
                               'exit_code': result.returncode, 'log': log})
    if result.returncode and check:
        print(result.stdout.decode(errors='replace')[-12000:])
        raise RuntimeError(f'Command failed ({result.returncode}): {args}')
    return result


def clone(source, destination, revision):
    command(['git', 'clone', '--quiet', '--local', '--shared', '--no-checkout',
             '--no-recurse-submodules', str(source), str(destination)])
    command(['git', 'checkout', '--quiet', '--detach', revision], cwd=destination)


try:
    baseline = command(['git','rev-parse','HEAD'],cwd=PARTIES).stdout.decode().strip()
    RECORD['parties_base'] = baseline
    clone(PARTIES, MODULE, baseline)
    patch = command(['git','diff','--binary','HEAD'],cwd=PARTIES).stdout
    (RESULTS/'preparation.patch').write_bytes(patch)
    RECORD['patch_sha256'] = hashlib.sha256(patch).hexdigest()
    RECORD['untracked_inputs'] = []
    command(['git','apply','--binary','-'],cwd=MODULE,input=patch)
    untracked = command(['git','ls-files','--others','--exclude-standard','-z'],cwd=PARTIES).stdout
    for raw in untracked.split(b'\0'):
        if raw:
            relative = Path(os.fsdecode(raw))
            destination = MODULE/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(PARTIES/relative,destination)
            saved = RESULTS/'inputs'/relative
            saved.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(PARTIES/relative,saved)
            RECORD['untracked_inputs'].append({'path':relative.as_posix(),
                'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                'mode':oct(destination.stat().st_mode & 0o777)})
    RECORD['dependencies'] = {}
    for name in ['Hexalith.Builds','Hexalith.EventStore','Hexalith.Tenants','Hexalith.Memories',
                 'Hexalith.Commons','Hexalith.FrontComposer','Hexalith.Platform',
                 'Hexalith.McpCli','Hexalith.PolymorphicSerializations','Hexalith.AI.Tools']:
        tree = command(['git','ls-files','--stage',f'references/{name}'],cwd=PARTIES).stdout.decode()
        revision = tree.split()[1]
        source = CICD/'references'/name
        if not (source/'.git').exists():
            source = LOCAL/name
        command(['git','cat-file','-e',revision+'^{commit}'],cwd=source)
        clone(source,MODULE/'references'/name,revision)
        command(['git','update-index','--cacheinfo','160000,'+revision+',references/'+name],cwd=MODULE)
        RECORD['dependencies'][name] = revision
    selected = command(['git','rev-parse','v6.0.6^{commit}'],cwd=CICD/'references/Hexalith.Builds').stdout.decode().strip()
    selected_builds = WORK/'selected-builds'
    clone(CICD/'references/Hexalith.Builds',selected_builds,selected)
    RECORD['selected_builds'] = selected
    flags = ['--configuration','Release','--disable-build-servers','-m:1','-warnaserror',
             '-p:UseHexalithProjectReferences=false','-p:UseNuGetDeps=true',
             '-p:HexalithBuildsRoot='+str(selected_builds)]
    if os.environ.get('PARTIES_VERIFY_UNIT_ONLY') == 'true':
        RECORD['scope'] = 'Complete environment-free general unit assembly; standalone project build, not another complete solution verdict.'
        command(['dotnet','build','tests/Hexalith.Parties.Tests/Hexalith.Parties.Tests.csproj',*flags],
                cwd=MODULE,log='general-unit-project-build.log')
        command(['dotnet','tests/Hexalith.Parties.Tests/bin/Release/net11.0/Hexalith.Parties.Tests.dll',
                 '-failSkips'],cwd=MODULE,log='complete-general-unit-tests.log',check=False)
    elif os.environ.get('PARTIES_VERIFY_RUNTIME_CHILD_ONLY') == 'true':
        command(['dotnet','build','tests/Hexalith.Parties.Runtime.IntegrationTests/Hexalith.Parties.Runtime.IntegrationTests.csproj',*flags],
                cwd=MODULE,log='runtime-child-build.log')
    elif os.environ.get('PARTIES_VERIFY_GRAPH_ONLY') == 'true':
        fixture = '<Solution><Project Path="tests/Hexalith.Parties.RuntimeArtifacts/Hexalith.Parties.RuntimeArtifacts.csproj" /><Project Path="tests/Hexalith.Parties.EventStoreAdminUI.TestHost/Hexalith.Parties.EventStoreAdminUI.TestHost.csproj" /></Solution>\n'
        (MODULE/'RuntimeQualification.slnx').write_text(fixture)
        RECORD['fixture_solution'] = fixture
        RECORD['scope'] = 'Runtime graph and private Admin UI only; not a complete solution verdict'
        command(['dotnet','build','RuntimeQualification.slnx',*flags],cwd=MODULE,log='runtime-graph-only-build.log')
    elif os.environ.get('PARTIES_VERIFY_FOCUSED') == 'true':
        command(['dotnet','build','tests/Hexalith.Parties.Ci.Tests/Hexalith.Parties.Ci.Tests.csproj',*flags],
                cwd=MODULE,log='retained-product-tests-build.log')
        for group in ['ContainerProductTests','BrowserProductTests','StandaloneSolutionTests','PackagePublicationProductTests']:
            command(['dotnet','tests/Hexalith.Parties.Ci.Tests/bin/Release/net11.0/Hexalith.Parties.Ci.Tests.dll',
                     '-class','Hexalith.Parties.Ci.Tests.'+group],cwd=MODULE,log='retained-'+group+'.log')
    else:
        command(['dotnet','build','Hexalith.Parties.Standalone.slnx',*flags],cwd=MODULE,
                log='standalone-package-build.log')
        if os.environ.get('PARTIES_VERIFY_RUNTIME_GRAPH') == 'true':
            command(['bash','scripts/prepare-ci-package-dependencies.sh'],cwd=MODULE,
                    log='declared-aspire-assets.log')
            command(['bash','scripts/prepare-aspire-runtime-hosts.sh','--reuse-build','true',
                     '--include-memory-qualification','true'],cwd=MODULE,
                    log='runtime-build-reuse.log')
        command(['dotnet','tests/Hexalith.Parties.Ci.Tests/bin/Release/net11.0/Hexalith.Parties.Ci.Tests.dll',
                 '-parallelMode','none','-failSkips'],cwd=MODULE,log='complete-retained-ci-product-tests.log',check=False)
        command(['dotnet','tests/Hexalith.Parties.Tests/bin/Release/net11.0/Hexalith.Parties.Tests.dll',
                 '-failSkips'],cwd=MODULE,log='complete-general-unit-tests.log',check=False)
        command(['dotnet','tests/Hexalith.Parties.IntegrationTests/bin/Release/net11.0/Hexalith.Parties.IntegrationTests.dll',
                 '-class','Hexalith.Parties.IntegrationTests.Topology.MemoryRuntimeIdentityTests','-failSkips'],
                cwd=MODULE,log='runtime-child-identity-tests.log',check=False)
        command(['dotnet','tests/Hexalith.Parties.Runtime.IntegrationTests/bin/Release/net11.0/Hexalith.Parties.Runtime.IntegrationTests.dll',
                 '-method','Hexalith.Parties.Tests.Search.PartyMemoryRuntimeTests.DeletionTerminalWaitObservesCompletedAfterRunning',
                 '-method','Hexalith.Parties.Tests.Search.PartyMemoryRuntimeTests.DeletionTerminalWaitRejectsFailedOrTerminatedWorkflows',
                 '-method','Hexalith.Parties.Tests.Search.PartyMemoryRuntimeTests.DeletionTerminalWaitIsBoundedAndHonorsCancellation',
                 '-method','Hexalith.Parties.Tests.Search.PartyMemoryRuntimeTests.PrivateTeardownRetainsExactKeysAndErasesOnlyAfterSafeTerminalCleanup',
                 '-method','Hexalith.Parties.Tests.Search.PartyMemoryRuntimeTests.AuthorityReceiptFailureStillTearsDownPrimaryAndSurvivor',
                 '-method','Hexalith.Parties.Tests.Search.PartyMemoryRuntimeTests.AuthorityFinalizationRunsBothTeardownsAndPreservesTheOwningFailure',
                 '-failSkips'],cwd=MODULE,log='runtime-deterministic-teardown-tests.log',check=False)

finally:
    name = ('unit-only-preparation.json' if os.environ.get('PARTIES_VERIFY_UNIT_ONLY') == 'true' else 'runtime-child-preparation.json' if os.environ.get('PARTIES_VERIFY_RUNTIME_CHILD_ONLY') == 'true' else 'graph-only-preparation.json' if os.environ.get('PARTIES_VERIFY_GRAPH_ONLY') == 'true' else 'focused-preparation.json' if os.environ.get('PARTIES_VERIFY_FOCUSED') == 'true' else 'standalone-preparation.json')
    RECORD['evidence_directory'] = str(RESULTS)
    (RESULTS/name).write_text(json.dumps(RECORD,indent=2)+'\n')
    (EVIDENCE/('latest-'+name)).write_text(json.dumps({'result':str(RESULTS/name)},indent=2)+'\n')
