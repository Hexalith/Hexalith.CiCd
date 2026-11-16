#!/usr/bin/env python3
"""Summarize retained results and read-only preservation checks for handoff."""
from pathlib import Path
import datetime
import json
import re
import subprocess

root=Path(__file__).resolve().parents[5]
evidence=Path(__file__).resolve().parent
module=root/'references/Hexalith.Conversations'
builds=root/'references/Hexalith.Builds'
def git(repository,*args):return subprocess.check_output(['git',*args],cwd=repository,text=True)
def counts(name):
    text=(evidence/name).read_text()
    matches=list(re.finditer(r'Ran (\d+) tests? in ([0-9.]+)s\n\n(OK|FAILED[^\n]*)',text))
    assert matches,name
    match=matches[-1]
    return {'tests':int(match[1]),'seconds':float(match[2]),'passed':match[3]=='OK','log':name}
matrices={}
for version in ('3.12.13','3.14.4'):
    rows=json.loads((evidence/f'python-{version}-results.json').read_text())
    assert len(rows)==13 and all(row['exitCode']==0 for row in rows)
    matrices[version]=[{**row,**counts(row['log'])} for row in rows]
    assert all(row['passed'] for row in matrices[version]),matrices[version]
for repository in (root,builds,module):
    subprocess.run(['git','diff','--check'],cwd=repository,check=True)
preserved=['package.json','package-lock.json','.config/dotnet-tools.json','.gitmodules','global.json']
for name in preserved:
    assert subprocess.check_output(['git','show','HEAD:'+name],cwd=module)==(module/name).read_bytes(),name
assert not git(module,'diff','--','tests/fixtures/Hexalith.Conversations.MinimalModule')
assert not git(module,'diff','--','.github/workflows','.github/hexalith-ci.json')
assert not git(root,'diff','--','builds-version','setup/Hexalith.Conversations.yml','rendered')
spec=root/'_bmad-output/implementation-artifacts/spec-16-migrate-conversations.md'
before=subprocess.check_output(['git','show','HEAD:'+spec.relative_to(root).as_posix()],cwd=root).decode()
after=spec.read_text()
def frozen(text):return text[text.index('<frozen-after-approval'):text.index('</frozen-after-approval>')+len('</frozen-after-approval>')]
assert frozen(before)==frozen(after)
assert "baseline_commit: 'd04c9ab7a8fa43dc6dac1f15d34135aba8e79551'" in after
assert "status: 'in-progress'" in after
result={
    'schema':'story16.local-source-verification.v1',
    'recordedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status':'local-source-qualified; external acceptance pending',
    'worktree':str(root),
    'repositoryHeads':{label:git(path,'rev-parse','HEAD').strip() for label,path in [('CiCd',root),('Builds',builds),('Conversations',module)]},
    'commands':[
        'run-with-temp _bmad-output/specs/spec-cicd/evidence/16/run-source-qualification.sh references/Hexalith.Builds _bmad-output/specs/spec-cicd/evidence/16',
        'run-with-temp python3 _bmad-output/specs/spec-cicd/evidence/16/run-python-qualification.py /home/administrator/.local/bin/python3.12',
        'run-with-temp bash -euc \'UV_CACHE_DIR="$TMPDIR/uv-cache" uv run --no-project --python /home/administrator/.local/bin/python3.12 --with Jinja2==3.1.6 --with PyYAML==6.0.3 --with jsonschema==4.26.0 python _bmad-output/specs/spec-cicd/evidence/16/run-python-qualification.py --failed\'',
        'run-with-temp python3 _bmad-output/specs/spec-cicd/evidence/16/run-python-qualification.py /home/administrator/.local/bin/python3.12 --groups=builds-test_module_preparation',
        'run-with-temp python3 _bmad-output/specs/spec-cicd/evidence/16/run-python-qualification.py /home/administrator/.local/bin/python3.12 --groups=builds-test_windows_checkout',
        'run-with-temp python3 _bmad-output/specs/spec-cicd/evidence/16/run-python-qualification.py /home/administrator/.local/bin/python3.12 --groups=builds-test_ci_dapr_scope',
        'run-with-temp python3 _bmad-output/specs/spec-cicd/evidence/16/run-python-qualification.py',
        'run-with-temp uv run --locked --script tools/tests/test_render.py',
        'run-with-temp uv run --locked --script tools/tests/test_validate.py',
        'run-with-temp uv run --locked --script tools/render.py --check',
        'run-with-temp uv lock --offline --check --script tools/qualify_conversations.py'],
    'python':matrices,
    'dotnet':{
        'strictBuild':{'warnings':0,'errors':0,'log':'managed-producer-build.log'},
        'newContractTests':{'tests':12,'failed':0,'skipped':0,'log':'managed-producer-tests.log'},
        'legacyTests':{'tests':138,'failed':0,'skipped':0,'log':'legacy-producer-regression.log'},
        'privateToolPackage':{'version':'6.1.0','published':False,'exclusiveLocalFeed':True,'positiveInstalledQualifiedCommand':True,'log':'source-package-qualification.log'},
        'productSource':{'strictProjects':['Conformance','Portable','TestSupport'],'projectionKeyAssertions':1,'portableAssertions':20,'fixtureAssertions':7,'overlayAssertions':3,'packageSymbolPairs':5,'isolatedConsumers':['public','testing'],'tamperedGeneratedImportRefused':True,'tamperedAssetsGraphRefused':True,'log':'managed-adapter-source-qualification.log'}},
    'nativeWindows':{
        'protectedSparseIndex':'windows-implementation-qualification.json',
        'fullTestSupportDll':{'tests':44,'failed':0,'skipped':0,'notRun':0,'filtered':False,'runtime':'11.0.0','runtimeInstalledOnlyInPrivateScratch':True,'sha512VerifiedAgainstMicrosoftReleaseMetadata':True,'log':'testsupport-native-windows-source.log'},
        'physicalGitRootSpellingVerified':True,
        'fullModuleReleasedInputAcceptance':'pending'},
    'rootTools':{'renderer':counts('renderer-regressions.log'),'validator':counts('validator-regressions.log'),'renderCheck':{'exitCode':0,'log':'render-check.log'},'qualificationLockCheck':{'exitCode':0,'log':'qualification-lock-check.log'}},
    'preservation':{'moduleFilesByteIdenticalToHead':preserved,'frozenFixtureTreeUnchanged':True,'moduleOwnedWorkflowsConfigGitmodulesUnchanged':True,'productionBuildsPinRegistrationRenderedTreeUnchanged':True,'specFrozenBlockBaselineUnchanged':True,'specStatus':'in-progress','whitespaceChecks':['CiCd','Builds','Conversations']},
    'limitations':[
        'Private source package and synthetic local identity fixtures are not a published producer or production qualification receipt.',
        'Successor locks were qualified against the existing v6.0.6 catalog (EventStore 5.1.1); recheck the actual new release catalog before adoption.',
        'Broad Workspace suite did not pass: HXR021 failures, three contextual skips, terminated after twenty minutes; causality unverified. See broad-workspace-regression.log.',
        'Genuine local Dapr integration refused because all four existing user control-plane containers are present; their IDs/names were unchanged. See dapr-occupied-host-refusal.log.',
        'Full tools/validate.py live-module/online qualification was not run in this local/no-remote-operations implementation phase.'],
    'pendingExternal':[
        'AD-21 administrative preflight/provisioning and acceptable published Builds/CLI release.',
        'Real Conversations tool/Platform prerequisites, committed exact-input qualification and protected product-preparation push.',
        'Released pin plus registration/render; App delivery and authenticated preservation.',
        'Green genuine Linux/browser/Dapr/AppHost and full Windows module CI; adopted normal check.py.',
        'Immutable-release readback, legacy access retirement, scheduled nightly CodeQL/publication or authenticated nothing-to-release outcome.',
        'After adoption removes owned npm selectors: product npm cleanup after selector absence and normal checker success.'],
    'operations':{'commits':False,'pushes':False,'remoteAdministration':False,'allTaskWrapperJobsCompleted':True}}
assert result['rootTools']['renderer']['passed'] and result['rootTools']['validator']['passed']
(evidence/'verification-results.json').write_text(json.dumps(result,indent=2)+'\n')
inventory={}
for label,repository in [('CiCd',root),('Builds',builds),('Conversations',module)]:
    inventory[label]={'trackedChanges':git(repository,'diff','--name-status').splitlines(),'untrackedAdditions':git(repository,'ls-files','--others','--exclude-standard').splitlines()}
(evidence/'source-diff-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
print(json.dumps({'pythonTotals':{key:sum(row['tests'] for row in rows) for key,rows in matrices.items()},'renderer':result['rootTools']['renderer'],'validator':result['rootTools']['validator']}))
