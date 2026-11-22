#!/usr/bin/env python3
"""Freeze the final local product candidate, verify policy, and rerun full Client."""
import ctypes
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
CICD = Path(__file__).resolve().parents[4]
SOURCE = CICD / 'references/Hexalith.Folders'
BASE = 'a448d20873dc9e809623f85da206e8d8a13bb9ab'
SCRATCH = Path(os.environ['TMPDIR'])
OUTPUT = SCRATCH / 'folders-final-results'
OUTPUT.mkdir(parents=True, exist_ok=True)
ROOT = SCRATCH / 'Hexalith.Folders'
RESULT = {'status': 'running', 'base': BASE, 'commands': [], 'publication': 'not attempted; local-only boundary'}
ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0)

def save():
    (OUTPUT / 'final-candidate.json').write_text(json.dumps(RESULT, indent=2)+'\n')

def git(*args, root=ROOT):
    return subprocess.check_output(['git', '-c', 'submodule.recurse=false', '-C', str(root), *args], text=True).strip()

def job(label, command, *, timeout=600):
    log = OUTPUT / (label+'.log')
    env = dict(os.environ, CI='true', DOTNET_NOLOGO='1', DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_CLI_UI_LANGUAGE='en-US', MSBUILDDISABLENODEREUSE='1', UseSharedCompilation='false')
    print(label, 'running', flush=True)
    with log.open('w') as output:
        child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            code = 124
        finally:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            while True:
                try:
                    os.waitpid(-child.pid, 0)
                except ChildProcessError:
                    break
    RESULT['commands'].append({'label':label, 'arguments':command, 'exit_code':code, 'log':log.name})
    save()
    print(label, 'exit', code, flush=True)
    return code

subprocess.run(['git','-c','submodule.recurse=false','clone','--shared','--no-checkout',str(SOURCE),str(ROOT)],check=True,capture_output=True)
subprocess.run(['git','-C',str(ROOT),'-c','submodule.recurse=false','checkout','--detach',BASE],check=True,capture_output=True)
changed=subprocess.check_output(['git','-C',str(SOURCE),'diff','--name-only','-z',BASE]).decode().split('\0')
untracked=subprocess.check_output(['git','-C',str(SOURCE),'ls-files','--others','--exclude-standard','-z']).decode().split('\0')
for relative in sorted(set(changed+untracked)-{''}):
    source,target=SOURCE/relative,ROOT/relative
    if source.is_file():
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    elif not source.exists() and target.is_file():target.unlink()
    else:raise RuntimeError('Unsupported candidate path: '+relative)
git('add','--all')
patch=subprocess.check_output(['git','-C',str(ROOT),'diff','--cached','--binary',BASE])
(OUTPUT/'folders-product-candidate.patch').write_bytes(patch)
RESULT['patch_sha256']=hashlib.sha256(patch).hexdigest()
RESULT['tree']=git('write-tree')
subprocess.run(['git','-C',str(ROOT),'-c','user.name=Hexalith module agent','-c','user.email=module-agent@hexalith.com','commit','-m','build: prepare Folders central CI migration'],check=True,capture_output=True)
RESULT['candidate']=git('rev-parse','HEAD')
RESULT['changed_paths']=git('diff','--name-only',BASE,'HEAD').splitlines()
(OUTPUT/'candidate-commit.txt').write_text(git('cat-file','commit','HEAD')+'\n')
git('bundle','create',str(OUTPUT/'folders-product-candidate.bundle'),'HEAD','^'+BASE)
owned=['.github/workflows','.github/dependabot.yml','.github/hexalith-ci.json','references/Hexalith.Builds','.gitmodules','AGENTS.md','CLAUDE.md','.github/copilot-instructions.md','.claude','commitlint.config.mjs','.releaserc.json']
before,after=git('ls-tree','-r',BASE,'--',*owned),git('ls-tree','-r','HEAD','--',*owned)
RESULT['owned_tree_preserved']=before==after
(OUTPUT/'owned-tree-baseline.txt').write_text(before+'\n');(OUTPUT/'owned-tree-candidate.txt').write_text(after+'\n')
if before!=after:raise RuntimeError('Owned tree changed')
builds=ROOT/'references/Hexalith.Builds'
subprocess.run(['git','-c','submodule.recurse=false','clone','--shared','--no-checkout',str(CICD/'references/Hexalith.Builds'),str(builds)],check=True,capture_output=True)
subprocess.run(['git','-C',str(builds),'-c','submodule.recurse=false','checkout','--detach','fdda17c0a4538b0f7c99f813c20ca24b49006530'],check=True,capture_output=True)
RESULT['builds']='fdda17c0a4538b0f7c99f813c20ca24b49006530'
config_path=FIXTURES/'registration-candidate/rendered/Hexalith.Folders/.github/hexalith-ci.json'
RESULT['candidate_configuration_sha256']=hashlib.sha256(config_path.read_bytes()).hexdigest()
config=json.loads(config_path.read_text())
sys.path.insert(0,str(CICD/'tools'))
from delivery_runtime import Git
from scan_discovery import Discovery
files,errors=Discovery(Git(ROOT),RESULT['candidate']).discover()
(OUTPUT/'action-discovery.json').write_text(json.dumps({'candidate':RESULT['candidate'],'paths':sorted(files),'errors':errors},indent=2)+'\n')
RESULT['action_discovery']={'files':len(files),'error_count':len(errors),'samples':errors[:4],'diagnostics':'action-discovery.json','python_errors':[e for e in errors if e.startswith('scripts/')]}
sys.path.insert(0,str(builds/'Github/lib'))
import audit_lint,expected_state,guard_actions,guard_commitlint
from guard_tools import Tools
from ci_pipeline import classify_projects
snapshot=expected_state.tree_snapshot(expected_state.Git(ROOT),RESULT['candidate'])
try:
    audit_lint.lint(snapshot);RESULT['audit_lint']='passed'
except Exception as error:RESULT['audit_lint']=str(error)
try:
    tools_root=SCRATCH/'guard-tools';tools_root.mkdir();tools=Tools(tools_root)
    guard_actions.lint(snapshot,tools)
    guard_commitlint.lint(expected_state.Git(ROOT),tools,event_name='workflow_dispatch',event={},frozen_head=RESULT['candidate'])
    RESULT['released_action_commit_policy']='passed'
except Exception as error:RESULT['released_action_commit_policy']=str(error)
prior=json.loads((FIXTURES/'attempt-3/product-verification.json').read_text())
projects=tuple(sorted({path for group in prior['shared_classification'].values() for path in group}))
classified=classify_projects(projects,config,repository='Hexalith/Hexalith.Folders')
RESULT['shared_classification']=dataclasses.asdict(classified)
RESULT['classification_basis']='Released evaluated IsTestProject inventory from attempt 3; project definitions, source dependency pins and SDK/package settings are unchanged. Final explicit exclusions now bind all six complete-project owners.'
save()
project='tests/Hexalith.Folders.Client.Tests/Hexalith.Folders.Client.Tests.csproj'
flags=['-p:Configuration=Release','-p:UseHexalithProjectReferences=false','-p:NuGetAudit=true','-p:NuGetAuditMode=all','-p:NuGetAuditLevel=low','-warnaserror','-m:1']
job('final-client-restore',['dotnet','restore',project,*flags])
job('final-client-build',['dotnet','build',project,'--no-restore',*flags])
job('final-client-complete',['pwsh','-NoLogo','-NoProfile','-File','tests/tools/run-complete-project-tests.ps1','-ProjectName','Hexalith.Folders.Client.Tests'])
RESULT['strict_runner_sha256']=hashlib.sha256((ROOT/'tests/tools/run-complete-project-tests.ps1').read_bytes()).hexdigest()
RESULT['status']='blocked'
RESULT['blockers']=['Released audit lint rejects eight unchanged historical evidence auditSources declarations.','Current CiCd action discovery rejects ordinary PowerShell syntax; the minimal literal-callee repro is saved separately.','Retained real product prerequisites and frozen FR58 implementation are incomplete; strict delegated hooks remain red, with no skip/exemption.','Predecessor acceptance, AD-21 administration, protected-token publication, adoption and genuine scheduled release remain outside this local-only handoff.']
save()
print('Final local candidate frozen; strict Client result and honest blockers recorded.',flush=True)
