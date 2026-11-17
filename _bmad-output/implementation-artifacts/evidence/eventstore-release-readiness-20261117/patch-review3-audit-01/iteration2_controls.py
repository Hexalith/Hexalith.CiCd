#!/usr/bin/env python3
"""Focused iteration-2 controls. No producer suite or broad consumer execution."""
import argparse
import copy
import ctypes
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
from unittest.mock import patch

import verification_core as core
from verify import validate_properties, FROZEN_SECURITY_EXCEPTIONS
import inspect_public_api
import verify
from audit_evidence import report_bytes_bound, api_outcome, candidate_binding_inventory
from artifact_resolver import resolve_artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    scratch = Path(os.environ['TMPDIR']).resolve()
    core.require(os.environ.get('TMP') == str(scratch) == os.environ.get('TEMP'), 'Use run-with-temp')
    output = args.output.resolve()
    core.require(not output.is_relative_to(scratch), 'Keep results outside scratch')
    output.mkdir(parents=True, exist_ok=False)
    packet = Path(__file__).resolve().parent
    names = ('iteration2_controls.py', 'verification_core.py', 'verify.py', 'query_package_probe.py', 'inspect_public_api.py', 'audit_evidence.py', 'artifact_resolver.py', 'control-inventory.json')
    for name in names:
        shutil.copy2(packet / name, output / name)
    checks, receipts = {}, {}
    completed = False
    # This test harness owns foreign fixtures explicitly. The production helper
    # never enables subreaping in its caller; each job gets a dedicated child.
    core.require(ctypes.CDLL(None).prctl(36, 1, 0, 0, 0) == 0, 'Fixture subreaper unavailable')
    caller_pid = os.getpid()
    original_processes = core._processes

    def child_only_processes():
        core.require(os.getpid() != caller_pid, 'Caller must never classify/adopt child trees')
        return original_processes()

    def check(name, value):
        checks[name] = bool(value)
        core.require(value, name)

    def wait_path(path):
        deadline = time.monotonic() + 5
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(.005)
        core.require(path.exists(), f'Fixture not ready: {path}')

    def run(name, command, bound=None, job_env=None):
        log = output / (name + '.log')
        record = {'command':command,'log':log.name}
        receipts[name] = record
        try:
            with log.open('wb') as stream:
                record.update(core.owned_run(command, scratch, job_env if job_env is not None else os.environ.copy(), stream, bound))
        except (core.JobInterrupted, core.JobCleanupError) as error:
            record.update(error.receipt)
            raise
        finally:
            record['log_sha256'] = core.digest(log)
        return record

    def escaped(path, stay):
        sleeper = f"import os,time;from pathlib import Path;Path({str(path)!r}).write_text(str(os.getpid()));time.sleep(60)"
        code = ('import os,sys,time\n'
                'if os.fork():\n    ' + ('time.sleep(60)' if stay else 'os._exit(0)') + '\n'
                'else:\n    os.setsid()\n    if os.fork(): os._exit(0)\n'
                f'    os.execve(sys.executable,[sys.executable,"-c",{sleeper!r}],{{}})\n')
        return [sys.executable, '-c', code]

    try:
        with patch.object(core, '_processes', child_only_processes):
            for code in (0, 7):
                receipt = run(f'native-{code}', [sys.executable, '-c', f'raise SystemExit({code})'])
                check(f'native-{code}-preserved', receipt['native_exit'] == code and receipt['custodian_waited'] and receipt['timeout_seconds'] is None)
            for label, stay, bound in (('escape-normal', False, None), ('escape-timeout', True, .3)):
                path = scratch / (label + '.pid')
                receipt = run(label, escaped(path, stay), bound)
                wait_path(path)
                pid = int(path.read_text())
                check(label, pid in receipt['owned_pids'] and not Path(f'/proc/{pid}').exists() and receipt['process_tree_fully_waited'])
                check(label + '-bound', receipt['timeout_seconds'] == bound and receipt['timed_out'] == stay)
                if stay:
                    check('timeout-native-term-preserved', receipt['native_exit'] == -signal.SIGTERM)
            # Exact reproduced race: foreign parent exists before job creation,
            # then double-forks after that boundary and exits. Its surviving
            # descendant is adopted by this outer harness, never the custodian.
            for index in range(3):
                trigger = scratch / f'foreign-trigger-{index}'
                pidfile = scratch / f'foreign-orphan-{index}.pid'
                source = ('import os,time\nfrom pathlib import Path\n'
                    f'while not Path({str(trigger)!r}).exists(): time.sleep(.002)\n'
                    'if os.fork(): os._exit(0)\n'
                    'os.setsid()\nif os.fork(): os._exit(0)\n'
                    f'Path({str(pidfile)!r}).write_text(str(os.getpid()))\ntime.sleep(60)\n')
                foreign = subprocess.Popen([sys.executable, '-c', source], start_new_session=True)
                foreign_pid = None
                try:
                    job = f"import time;from pathlib import Path;Path({str(trigger)!r}).touch();time.sleep(60)"
                    receipt = run(f'foreign-orphan-race-{index}', [sys.executable, '-c', job], .3)
                    wait_path(pidfile)
                    foreign_pid = int(pidfile.read_text())
                    foreign.wait(timeout=5)
                    check(f'foreign-orphan-survives-{index}', Path(f'/proc/{foreign_pid}').exists() and foreign_pid not in receipt['owned_pids'] and foreign.pid not in receipt['owned_pids'])
                    check(f'foreign-orphan-not-reaped-{index}', os.waitpid(foreign_pid, os.WNOHANG) == (0, 0))
                finally:
                    if foreign.poll() is None:
                        foreign.terminate()
                        foreign.wait(timeout=5)
                    if foreign_pid is not None:
                        os.kill(foreign_pid, signal.SIGTERM)
                        os.waitpid(foreign_pid, 0)
                    # Reap the fixture's intermediate fork, whose identity is
                    # tracked by ancestry only in this fixture-owning harness.
                    while True:
                        try:
                            pid, _ = os.waitpid(-1, os.WNOHANG)
                        except ChildProcessError:
                            break
                        if not pid:
                            break
            for signum in (signal.SIGINT, signal.SIGTERM):
                path = scratch / f'active-cancel-{signum}.pid'
                timer = threading.Timer(.3, os.kill, args=(os.getpid(), signum))
                timer.start()
                try:
                    try:
                        run(f'active-cancel-{signum}', escaped(path, True))
                        raise RuntimeError('Cancellation ignored')
                    except core.JobInterrupted as error:
                        wait_path(path)
                        check(f'active-cancel-{signum}', error.receipt['cancelled'] and error.receipt['cancellation_signal'] == signum and error.receipt['custodian_waited'] and not Path('/proc/' + path.read_text()).exists())
                finally:
                    timer.join()
            original_signal = signal.signal
            injected = False
            def during_setup(signum, handler):
                nonlocal injected
                previous = original_signal(signum, handler)
                if signum == signal.SIGTERM and callable(handler) and not injected:
                    injected = True
                    os.kill(os.getpid(), signal.SIGINT)
                return previous
            with patch.object(core.signal, 'signal', during_setup):
                try:
                    run('early-cancel', [sys.executable, '-c', 'raise SystemExit(0)'])
                    raise RuntimeError('Early cancellation ignored')
                except core.JobInterrupted as error:
                    check('early-cancel-no-job', not error.receipt['process_started'] and error.receipt['native_exit'] is None and error.receipt['process_tree_fully_waited'])
            original_fork = os.fork
            def cancel_after_fork():
                pid = original_fork()
                if pid:
                    os.kill(os.getpid(), signal.SIGINT)
                return pid
            with patch.object(core.os, 'fork', cancel_after_fork):
                try:
                    run('fork-startup-cancel', [sys.executable, '-c', 'import time;time.sleep(60)'])
                    raise RuntimeError('Fork startup cancellation ignored')
                except core.JobInterrupted as error:
                    check('fork-startup-cancel-custody', error.receipt['cancelled'] and error.receipt['custodian_waited'] and error.receipt['process_tree_fully_waited'])
        check('caller-never-scanned', True)  # enforced for every lifecycle run above
        poisoned = dict(os.environ, GIT_CONFIG_GLOBAL='/foreign/config', GIT_CONFIG_SYSTEM='/foreign/system',
            GIT_TEMPLATE_DIR='/foreign/template', GIT_INDEX_FILE=str(scratch / 'sentinel-index'),
            EVENTSTORE_PACKAGE_CONTRACT_DIR='/foreign/packages', NoWarn='NU1904', RunAnalyzers='false')
        cleaned, removed = core.clean_environment(poisoned)
        check('git-policy-selector-quarantine', all(name not in cleaned for name in ('GIT_CONFIG_GLOBAL', 'GIT_CONFIG_SYSTEM', 'GIT_TEMPLATE_DIR', 'GIT_INDEX_FILE', 'EVENTSTORE_PACKAGE_CONTRACT_DIR', 'NoWarn', 'RunAnalyzers')))
        check('credential-selection-preserved', all(cleaned.get(key) == poisoned.get(key) for key in ('GH_CONFIG_DIR', 'GH_TOKEN', 'GITHUB_TOKEN', 'GIT_SSH_COMMAND')))
        props = {'Configuration':'Release','UseHexalithProjectReferences':'false','UseNuGetDeps':'true',
            'TargetFramework':'net11.0','AnalysisMode':'','AnalysisLevel':'latest','EffectiveAnalysisLevel':'11.0',
            '_GlobalAnalyzerConfigAnalysisMode_MicrosoftCodeAnalysisNetAnalyzers':'Default','NuGetAudit':'true','NuGetAuditMode':'all','NuGetAuditLevel':'low','TreatWarningsAsErrors':'true','EnableNETAnalyzers':'true',
            'WarningsNotAsErrors':';NU1901;NU1902', 'RunAnalyzers':'', 'RunAnalyzersDuringBuild':'', '_SkipAnalyzers':'', '_ImplicitlySkipAnalyzers':''}
        check('exact-frozen-security-exceptions', not validate_properties(props))
        for name in ('NoWarn', 'WarningsNotAsErrors'):
            for code in ('NU1903', 'NU1904'):
                bad = dict(props, **{name: props.get(name, '') + ';' + code})
                check('reject-added-' + name + '-' + code, bool(validate_properties(bad)))
        check('reject-analyzer-disable', bool(validate_properties(dict(props, RunAnalyzers='false'))))
        check('synthetic-has-no-security-exceptions', not validate_properties(dict(props, WarningsNotAsErrors=''), {'NoWarn':set(), 'WarningsNotAsErrors':set()}))
        # An evaluated Linux graph is selected explicitly; committed Windows
        # history remains on disk and must never enter active aggregation.
        graphroot = scratch / 'graph-fixture'
        project = graphroot / 'src/P.csproj'
        project.parent.mkdir(parents=True)
        project.write_text('<Project />')
        active = graphroot / 'obj/project.assets.json'
        active.parent.mkdir()
        active.write_text(json.dumps({'project':{'restore':{'projectPath':str(project),'sources':{'https://user:secret@example.com/feed?token=secret':{}}}},'libraries':{'P/1':{'type':'package','sha512':'content'}},'targets':{'net11.0':{'P/1':{'dependencies':{'D':'1'},'compile':{'lib/P.dll':{}},'runtime':{'lib/P.dll':{}}}}},'projectFileDependencyGroups':{'net11.0':['P >= 1']}}))
        history = graphroot / 'history/project.assets.json'
        history.parent.mkdir()
        history.write_text('not even valid JSON; inactive tracked history')
        metadata = core.capture_graphs(graphroot, output, [{'assets_path':str(active),'project_path':str(project),'evaluation_command':'active-project-evaluation'}])
        graphs = json.loads((output / metadata['path']).read_text())
        check('only-evaluated-active-graph', metadata['project_count'] == 1 and graphs[0]['path'] == 'obj/project.assets.json')
        check('effective-source-sanitized', graphs[0]['sources'] == ['https://example.com/feed'])
        graph_data = active.read_text()
        active.write_text('invalid')
        try:
            core.capture_graphs(graphroot, output, [{'assets_path':str(active),'project_path':str(project),'evaluation_command':'bad'}])
            raise RuntimeError('Invalid graph accepted')
        except json.JSONDecodeError:
            check('graph-error-is-explicit', True)
        active.write_text(graph_data)
        inputs = scratch / 'input-fixture'
        inputs.mkdir()
        (inputs / 'source.cs').write_text('frozen')
        (inputs / 'obj').mkdir()
        (inputs / 'obj/generated.cs').write_text('output')
        check('designated-output-accepted', not core.unexpected_inputs(inputs, ['source.cs'], ['obj']))
        (inputs / 'extra.props').write_text('untracked input')
        check('unexpected-build-input-rejected', core.unexpected_inputs(inputs, ['source.cs'], ['obj']) == ['extra.props'])
        manifest = core.file_manifest(inputs)
        check('input-manifest-replayed', core.verify_manifest(inputs, manifest))
        (inputs / 'source.cs').write_text('changed')
        check('input-manifest-mutation-rejected', not core.verify_manifest(inputs, manifest))
        interrupted_result = {'commands':[]}
        cancellation = {'native_exit':-2,'cancelled':True,'process_tree_fully_waited':True,'custodian_waited':True,'remaining_owned_after_cleanup':[]}
        with patch.object(inspect_public_api, 'owned_run', side_effect=core.JobInterrupted(cancellation)):
            try:
                inspect_public_api.execute(interrupted_result, output, scratch, {}, 'inspection-cancellation', ['inspector','type','Control'])
                raise RuntimeError('Inspection did not interrupt')
            except core.JobInterrupted:
                check('interrupted-inspection-records-command', len(interrupted_result['commands']) == 1 and interrupted_result['commands'][0]['command'] == ['inspector','type','Control'])
                check('interrupted-inspection-records-cleanup', interrupted_result['commands'][0]['custodian_waited'] and 'log_sha256' in interrupted_result['commands'][0])
        (output / 'interrupted-inspection-receipt.json').write_text(json.dumps(interrupted_result, indent=2) + '\n')
        failed_output = output / 'primary-failure-control'
        failure_receipt = {'native_exit':7, 'process_tree_fully_waited':True, 'custodian_waited':True,
            'timed_out':False, 'remaining_owned_after_cleanup':[], 'owned_pids':[]}
        with patch.object(sys, 'argv', ['verify.py', '--output', str(failed_output)]), \
             patch.object(verify, 'owned_run', return_value=failure_receipt), \
             patch.object(verify, 'capture_graphs', side_effect=OSError('secondary graph failure')):
            try:
                verify.main()
                raise RuntimeError('Primary command failure was ignored')
            except RuntimeError as error:
                check('primary-error-propagated', 'git-read-0 failed: exit 7' in str(error))
        failed = json.loads((failed_output / 'result.json').read_text())
        check('primary-error-survives-graph-capture', 'git-read-0 failed: exit 7' in failed['fatal_error'] and 'secondary graph failure' in failed['graph_capture_error'] and bool(failed['completed_utc']))
        check('primary-failed-command-receipt-preserved', failed['commands'][0]['native_exit'] == 7 and failed['commands'][0]['custodian_waited'] and bool(failed['commands'][0]['log_sha256']))
        for label,error_type,fully_waited in (('interruption',core.JobInterrupted,True),('cleanup-error',core.JobCleanupError,False)):
            target=output/('verify-main-'+label)
            injected={'native_exit':-2 if fully_waited else -9,'cancelled':fully_waited,
                'process_tree_fully_waited':fully_waited,'custodian_waited':True,
                'remaining_owned_after_cleanup':[] if fully_waited else [999999999], 'owned_pids':[]}
            with patch.object(sys,'argv',['verify.py','--output',str(target)]), \
                 patch.object(verify,'owned_run',side_effect=error_type(injected)):
                try:
                    verify.main()
                    raise RuntimeError('verify.main lifecycle error was ignored')
                except error_type:
                    pass
            actual=json.loads((target/'result.json').read_text())
            record=actual['commands'][0]
            record['log']=str((target/record['log']).relative_to(output))
            receipts['verify-main-'+label]=record
            check('verify-main-'+label+'-receipt',actual['primary_error_type']==error_type.__name__ and record['native_exit']==injected['native_exit'] and record['process_tree_fully_waited']==fully_waited and record['custodian_waited'] and core.digest(output/record['log'])==record['log_sha256'])
        poisoned=dict(os.environ,GIT_EXTERNAL_DIFF='/bin/true',GIT_EXTERNAL_DIFF_TRUST_EXIT_CODE='1',AnalysisMode='None',AnalysisLevel='none')
        safe,_=core.clean_environment(poisoned)
        check('external-diff-selectors-quarantined',all(key not in safe for key in ('GIT_EXTERNAL_DIFF','GIT_EXTERNAL_DIFF_TRUST_EXIT_CODE')))
        check('analyzer-mode-level-selectors-quarantined',all(key not in safe for key in ('AnalysisMode','AnalysisLevel')))
        for label,key in (('analysis-mode','AnalysisMode'),('analysis-level','AnalysisLevel'),('effective-mode','_GlobalAnalyzerConfigAnalysisMode_MicrosoftCodeAnalysisNetAnalyzers')):
            check('reject-'+label+'-none',bool(validate_properties(dict(props,**{key:'None'}))))
        repository=scratch/'diff-fixture';repository.mkdir()
        (repository/'data.txt').write_text('original')
        run('diff-fixture-init',['git','init','--initial-branch=main',str(repository)],job_env=safe)
        run('diff-fixture-add',['git','-C',str(repository),'add','data.txt'],job_env=safe)
        run('diff-fixture-commit',['git','-C',str(repository),'-c','core.hooksPath=/dev/null','-c','user.name=Verification Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture'],job_env=safe)
        (repository/'data.txt').write_text('changed')
        hidden=run('external-diff-false-clean',['git','-C',str(repository),'diff','--exit-code','HEAD','--'],job_env=poisoned)
        guarded=run('internal-diff-changed',['git','-C',str(repository),'diff','--no-ext-diff','--no-textconv','--exit-code','HEAD','--'],job_env=safe)
        check('external-diff-reproduces-false-clean',hidden['native_exit']==0)
        check('internal-diff-detects-tracked-change',guarded['native_exit']==1)
        archive=scratch/'candidate.nupkg';archive.write_bytes(b'original candidate archive')
        library={'type':'package','sha512':core.archive_sha512(archive)}
        check('archive-content-sha512-matches',core.archive_matches_library(archive,library))
        archive.write_bytes(b'substituted candidate archive')
        check('archive-content-sha512-substitution-rejected',not core.archive_matches_library(archive,library))
        original=json.loads((packet/'attempt-01/result.json').read_text())
        report=original['test_results']['generators']['reports'][0]
        trx=scratch/'original.trx';shutil.copy2(packet/'attempt-01/test-results/generators/generators.trx',trx)
        check('trx-byte-hash-control',report_bytes_bound(trx,report))
        trx.write_bytes(trx.read_bytes()+b'\n')
        check('trx-changed-bytes-rejected',not report_bytes_bound(trx,report))
        public=json.loads((packet/'iteration2-public-api-02/result.json').read_text())
        case=next(item for item in public['commands'] if item['name']=='contracts-5.2.0-missing-query-result')
        diagnostic=(packet/'iteration2-public-api-02'/case['log']).read_text()
        check('api-outcome-native-control',api_outcome(case,public['tool'],public['scratch'],'5.2.0',inspect_public_api.MISSING,diagnostic))
        wrong=copy.deepcopy(case);wrong['command'][2]=inspect_public_api.PRESENT
        check('api-outcome-wrong-type-rejected',not api_outcome(wrong,public['tool'],public['scratch'],'5.2.0',inspect_public_api.MISSING,diagnostic))
        wrong=copy.deepcopy(case);wrong['command'][4]=wrong['command'][4].replace('5.2.0','5.1.1')
        check('api-outcome-wrong-version-rejected',not api_outcome(wrong,public['tool'],public['scratch'],'5.2.0',inspect_public_api.MISSING,diagnostic))
        check('api-outcome-native-exit-rejected',not api_outcome(dict(case,native_exit=0),public['tool'],public['scratch'],'5.2.0',inspect_public_api.MISSING,diagnostic))
        check('api-outcome-diagnostic-rejected',not api_outcome(case,public['tool'],public['scratch'],'5.2.0',inspect_public_api.MISSING,'different type not found'))
        inventory=json.loads((packet/'control-inventory.json').read_text())
        fixture={'passed':True,'checks':dict.fromkeys(inventory['controls'],True),'lifecycle_receipts':dict.fromkeys(inventory['receipts'],{})}
        check('empty-control-report-rejected',not core.control_report_valid({'passed':True,'checks':{},'lifecycle_receipts':{}},inventory))
        changed=copy.deepcopy(fixture);changed['checks'].pop(next(iter(changed['checks'])))
        check('truncated-controls-rejected',not core.control_report_valid(changed,inventory))
        changed=copy.deepcopy(fixture);changed['lifecycle_receipts'].pop(next(iter(changed['lifecycle_receipts'])))
        check('truncated-receipts-rejected',not core.control_report_valid(changed,inventory))
        config=scratch/'private.config'
        config.write_text('<configuration><packageSources><clear/><add key="feed" value="https://user:password@example.com/feed?token=do-not-retain"/></packageSources><packageSourceCredentials><feed><add key="ClearTextPassword" value="do-not-retain"/></feed></packageSourceCredentials><apikeys><add key="feed" value="do-not-retain"/></apikeys><config><add key="http_proxy" value="http://user:password@proxy.example.com"/></config></configuration>')
        policies=core.capture_restore_policy([config],output,'secret-control')
        sanitized=(output/policies[0]['path']).read_text()
        check('restore-policy-secrets-removed',all(value not in sanitized for value in ('do-not-retain','password','user:','http_proxy')) and 'https://example.com/feed' in sanitized)
        core.verify_restore_policy(policies,output)
        check('restore-policy-replayed',True)
        config.write_text(config.read_text().replace('example.com/feed','example.com/different'))
        try:
            core.verify_restore_policy(policies,output)
            raise RuntimeError('Restore policy mutation accepted')
        except RuntimeError as error:
            check('restore-policy-mutation-rejected','Effective restore policy changed' in str(error))
        check('graph-target-framework-edges-retained',graphs[0]['targets']['net11.0']['P/1']['dependencies']=={'D':'1'} and 'compile' in graphs[0]['targets']['net11.0']['P/1'] and graphs[0]['projectFileDependencyGroups']=={'net11.0':['P >= 1']})
        check('tool-artifact-not-in-packet',not list(packet.rglob('dotnet-inspect*.nupkg')))
        external=json.loads((packet/'external-artifacts.json').read_text())
        check('tool-artifact-sidecar-bound',bool(external['historical_paths']) and all(core.digest(resolve_artifact(item,scratch))==item['sha256'] for item in external['historical_paths'].values()))
        version='5.2.1-local-readiness.'+verify.SOURCE[:8]
        binding_fixture={'Owner.Contracts':{'Hexalith.EventStore.Contracts/'+version:'hash'},
            'Probe.Consumer':{'Hexalith.EventStore.'+name+'/'+version:'hash' for name in ('Contracts','Client','RestApi.Generators')}}
        check('archive-binding-inventory-required',candidate_binding_inventory(binding_fixture,version))
        check('archive-binding-empty-rejected',not candidate_binding_inventory({},version))
        binding_fixture['Probe.Consumer'].pop('Hexalith.EventStore.Client/'+version)
        check('archive-binding-truncated-rejected',not candidate_binding_inventory(binding_fixture,version))
        help_receipt=run('original-cli-help',[sys.executable,str(packet/'verify.py'),'--help'])
        help_text=(output/'original-cli-help.log').read_text()
        check('original-cli-compatible',help_receipt['native_exit']==0 and all(option in help_text for option in ('--workspace','--local-package-probes','--authority-probe','--query-api-package-probe')))
        check('authority-bound-unchanged', 'timeout_seconds=480' in (packet / 'verify.py').read_text())
        completed = True
        return 0
    finally:
        result = {'passed':completed and all(checks.values()),'checks':checks,'lifecycle_receipts':receipts,
            'source_sha256':{name:core.digest(output/name) for name in names},'python_optimization':sys.flags.optimize,
            'inventory_sha256':core.digest(packet/'control-inventory.json'),
            'scratch':str(scratch),'complete_release_acceptance':False,
            'invocation':'run-with-temp python3 -O -B ' + str(Path(__file__).resolve()) + ' --output ' + str(output)}
        if result['passed']:
            result['passed']=core.control_report_valid(result,json.loads((packet/'control-inventory.json').read_text()))
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'passed':result['passed'],'checks':len(checks),'output':str(output)}))

if __name__ == '__main__':
    sys.exit(main())
