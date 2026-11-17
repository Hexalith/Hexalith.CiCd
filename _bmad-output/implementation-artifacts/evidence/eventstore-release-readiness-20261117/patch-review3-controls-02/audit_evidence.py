#!/usr/bin/env python3
"""Replay source/package/API receipts and aggregation; no producer test execution.

Run: run-with-temp python3 -O -B <packet>/audit_evidence.py --output <fresh-dir>
"""
import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sys
import zipfile

from verification_core import digest, require, owned_run, suite_complete, suite_passed, trx_inventory, archive_sha512, archive_matches_library, control_report_valid
from verify import SOURCE, BUILDS, validate_properties, FROZEN_SECURITY_EXCEPTIONS
from inspect_public_api import TOOL_VERSION, TOOL_SHA256, RID_SHA256, PACKAGES, MISSING, PRESENT

QUERY = 'patch-review3-query-api-01'
PUBLIC = 'patch-review3-public-api-01'
CONTROLS = 'patch-review3-controls-02'


from artifact_resolver import retained_artifact, resolve_artifact


def report_bytes_bound(path, record):
    return digest(path) == record.get("sha256")


def api_outcome(record, tool, scratch, version, typename, diagnostic):
    archive = str(Path(scratch) / f"hexalith.eventstore.contracts.{version}.nupkg")
    expected = tool["command_prefix"] + ["type",typename,"--package",archive,"--plaintext"]
    if record.get("command") != expected:
        return False
    if typename == MISSING:
        return record.get("native_exit") == 1 and f"Type '{MISSING}' not found." in diagnostic
    return (typename == PRESENT and record.get("native_exit") == 0 and
            diagnostic.splitlines()[0] == PRESENT and
            f"Package: hexalith.eventstore.contracts | Version: {version} |" in diagnostic)


def candidate_binding_inventory(bindings, version):
    expected = {"Owner.Contracts": {"Hexalith.EventStore.Contracts/" + version},
                "Probe.Consumer": {"Hexalith.EventStore." + name + "/" + version
                                   for name in ("Contracts","Client","RestApi.Generators")}}
    return set(bindings) == set(expected) and all(set(bindings[name]) == keys for name,keys in expected.items())


def load(path):
    return json.loads(path.read_text())


def expected_aggregation(packet):
    original = load(packet / 'attempt-01/result.json')
    query = load(packet / QUERY / 'result.json')
    public = load(packet / PUBLIC / 'result.json')
    controls = load(packet / CONTROLS / 'result.json')
    local = load(packet / 'attempt-03-local-packages/result.json')
    authority = load(packet / 'attempt-04-authority/result.json')
    authority_command = next(item for item in authority['commands'] if item['name']=='package-authority-direct')
    observed = next(item for item in query['commands'] if item['name']=='later-observed-main')
    authority_count = int(re.search(r'passed for (\d+) projects', (packet/'attempt-04-authority'/authority_command['log']).read_text()).group(1))
    reference_names = ('attempt-01', 'attempt-02-local-packages', 'attempt-03-local-packages',
                       'attempt-04-authority', QUERY, PUBLIC, CONTROLS)
    return {
        'source': SOURCE, 'builds': BUILDS,
        'source_tree': query['dependencies']['Hexalith.EventStore']['tree'],
        'dependencies': {name:item['commit'] for name,item in query['dependencies'].items()},
        'complete_release_acceptance': False, 'publication_authorized_by_packet': False,
        'baseline_whole_suite_green': False,
        'whole_test_projects': {name:{'native_exit':value['native_exit'],
            'counters':value['reports'][0]['counters'], 'nonpassing':value['reports'][0]['nonpassing']}
            for name,value in original['test_results'].items()},
        'ordinary_release_package_checks': original['checks'],
        'explicit_original_package_skips': 2,
        'existing_audit_warning_exceptions': sorted(FROZEN_SECURITY_EXCEPTIONS['WarningsNotAsErrors']),
        'unpublished_local_packages': {'attempt':'attempt-03-local-packages','source':local['source'],
            'version':local['local_candidate_packages']['version'],'published':False,
            'archive_count':len(local['local_candidate_packages']['archives']),
            'archive_hashes':local['local_candidate_packages']['archives'], 'checks':local['checks'],
            'full_validator_library_consumers':13,'full_validator_tool_consumers':1,'reminder_subset_consumers':3,
            'passed':local['package_probes_passed']},
        'package_authority_reproduction': {'attempt':'attempt-04-authority',
            'native_exit':authority_command['native_exit'],'timeout_seconds':authority_command['timeout_seconds'],
            'timed_out':authority_command['timed_out'],'elapsed_seconds':authority_command['elapsed_seconds'],
            'projects':authority_count,'exclusions':[],'process_tree_fully_waited':None,
            'original_whole_suite_timeout_preserved':True,
            'original_group_receipt_claimed_fully_waited':authority_command['process_tree_fully_waited'],
            'custody_limit':'Historical process-group receipt; session-escape custody was not established for this original attempt.'},
        'later_observed_remote_main': {'observed_utc':observed['finished_utc'],
            'value':(packet/QUERY/observed['log']).read_text().strip()},
        'iteration2_jobs_fully_waited_and_scratch_removed': all(not Path(item['scratch']).exists() for item in (query,public,controls)) and all(item['process_tree_fully_waited'] and item['custodian_waited'] for item in query['commands']+public['commands']),
        'iteration2_no_broad_producer_or_unrelated_consumer_reruns':not query['test_results'] and query['scope']=='query-api-package-probe',
        'iteration2_original_failures_and_snapshots_preserved':True,
        'verified_query_contract_api_in_frozen_source': True,
        'verified_query_contract_api_in_synthetic_package_consumer': query['query_api_package_probe']['passed'],
        'product_source_correction': None,
        'query_api_package_probe': {'attempt':QUERY, **query['query_api_package_probe'],
                                   'resolved_package_graphs':query['resolved_package_graphs']},
        'public_api_inspection': {'attempt':PUBLIC, 'helper':'inspect_public_api.py',
            'tool':public['tool'], 'packages':public['packages'], 'passed':public['passed'],
            'original_logs_unchanged':True},
        'iteration2_verification': {'controls':CONTROLS + '/result.json', 'controls_passed':controls['passed'],
            'controls_count':len(controls['checks']), 'python_optimization':controls['python_optimization'],
            'query_attempt':QUERY, 'public_attempt':PUBLIC,
            'receipt_bindings':{name + '/result.json':digest(packet/name/'result.json') for name in reference_names}},
        'resolved_dependency_graph_provenance': {
            'original_attempts':'unavailable: original disposable graphs were removed; no reconstruction claimed',
            'attempt_05_capture':'flawed historical capture: 11 files included 6 committed Windows history assets and 5 active Linux assets; original capture preserved',
            'new_query_probe':'5 explicitly evaluated active Linux ProjectAssetsFile paths with targets, dependency/framework/asset selections, exact candidate archive content hashes and pre/post sanitized restore policy',
            'previous_iteration2_capture':'inventory-only package libraries/content hashes; dependency edges, target asset selections and pre-execution effective restore policy were not retained'
},
    }


def aggregation_errors(actual, expected):
    return [name for name,value in expected.items() if actual.get(name) != value]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    packet = Path(__file__).resolve().parent
    scratch = Path(os.environ['TMPDIR']).resolve()
    require(os.environ.get('TMP') == str(scratch) == os.environ.get('TEMP'), 'Use run-with-temp')
    output = args.output.resolve()
    require(not output.is_relative_to(scratch), 'Evidence must survive scratch cleanup')
    output.mkdir(parents=True, exist_ok=False)
    names = ('audit_evidence.py','verify.py','verification_core.py','query_package_probe.py',
             'inspect_public_api.py','iteration2_controls.py','frozen-suite-inventories.json','artifact_resolver.py','control-inventory.json')
    for name in names:
        shutil.copy2(packet/name, output/name)
    checks, evidence, receipts = {}, {}, {}
    complete = False

    def check(name, value):
        checks[name] = bool(value)
        require(value, name)

    def replay_commands(name, directory, result, custody=False):
        for index,record in enumerate(result['commands']):
            check(f'{name}-log-{index}-{record["name"]}', digest(directory/record['log']) == record['log_sha256'])
            if custody:
                check(f'{name}-custody-{index}', record['process_tree_fully_waited'] and record['custodian_waited'] and not record['remaining_owned_after_cleanup'] and record['custody'].startswith('dedicated per-job'))
        check(name + '-scratch-removed', not Path(result['scratch']).exists())

    def replay_inputs(name, directory, result):
        for relative,item in result.get('inputs',{}).items():
            path = directory/item.get('retained_path','committed-inputs/'+relative)
            if not path.exists():
                alias=load(packet/'retained-input-aliases.json')['aliases'][str(path.relative_to(packet))]
                path=packet/alias
            raw = path.read_bytes()
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            check(name + '-input-' + relative, digest(path) == item['sha256'] and blob == item['blob'])

    def run_job(name, command, env):
        log = output / (name + '.log')
        record = {'command':command, 'log':log.name}
        receipts[name] = record
        progress = output / 'lifecycle-progress.json'
        progress.write_text(json.dumps(receipts,indent=2)+'\n')
        try:
            with log.open('wb') as stream:
                record.update(owned_run(command,scratch,env,stream))
        except BaseException as error:
            record.update(getattr(error,'receipt',{}))
            record['lifecycle_exception'] = repr(error)
            raise
        finally:
            record['log_sha256'] = digest(log)
            progress.write_text(json.dumps(receipts,indent=2)+'\n')
        return record

    try:
        historical = load(packet/'integrity.json')['attempts']
        for name in ('attempt-01','attempt-02-local-packages','attempt-03-local-packages','attempt-04-authority'):
            directory = packet/name
            result = load(directory/'result.json')
            check(name + '-immutable-original-result', digest(directory/'result.json') == historical[name]['result_sha256'])
            check(name + '-identities', result['source'] == SOURCE and result['builds'] == BUILDS)
            check(name + '-helper', digest(directory/'verify.py') == result['helper_sha256'])
            replay_commands(name,directory,result)
            replay_inputs(name,directory,result)
            evidence[name] = {'result_sha256':digest(directory/'result.json'),
                'historical_graphs':'unavailable; not reconstructed',
                'custody':'historical limitations preserved; no retroactive dedicated-custodian claim'}
        frozen = load(packet/'frozen-suite-inventories.json')['suites']
        original = load(packet/'attempt-01/result.json')
        for name in frozen:
            report_path = packet/f'attempt-01/test-results/{name}/{name}.trx'
            check(name+'-original-trx-sha256',report_bytes_bound(report_path,original['test_results'][name]['reports'][0]))
            report = trx_inventory(report_path)
            summary = {'native_exit':original['test_results'][name]['native_exit'],'reports':[report]}
            check(name + '-frozen-inventory', suite_complete(summary,frozen[name]))
            check(name + '-original-counters', report['counters'] == original['test_results'][name]['reports'][0]['counters'])
            check(name + '-native-outcome', suite_passed(summary,frozen[name]) == (name == 'generators'))
            if name == 'contracts':
                check('contracts-exit-2-1805-pass-two-fail-two-skip', summary['native_exit'] == 2 and report['counters']['passed'] == '1805' and report['counters']['failed'] == '2' and report['counters']['notExecuted'] == '2')
            else:
                for label,mutate in {
                    'missing-name':lambda item:item['reports'][0]['names'].pop(),
                    'substituted-name':lambda item:item['reports'][0]['names'].__setitem__(0,'Foreign.Test'),
                    'missing-required-typed-compilation':lambda item:item['reports'][0]['typed_query_compilation_tests'].pop(),
                    'failed-required-typed-compilation':lambda item:item['reports'][0]['typed_query_compilation_tests'][0].update(outcome='Failed'),
                    'positive-incomplete-count':lambda item:item['reports'][0].update(result_rows=202),
                }.items():
                    changed=copy.deepcopy(summary);mutate(changed)
                    check('reject-suite-' + label, not suite_passed(changed,frozen[name]))
        # Replay old query/API results with explicit historical limitations.
        for name in ('attempt-05-query-api-packages','public-api-recheck-02'):
            directory=packet/name;result=load(directory/'result.json')
            replay_commands(name,directory,result)
            evidence[name]={'result_sha256':digest(directory/'result.json'),
                'custody':'prior nonce implementation; no complete cleared-environment or foreign-orphan proof',
                'input_provenance':'historical query project/nuspec hashes were not captured before execution; no reconstruction claimed'}
        query=load(packet/QUERY/'result.json');directory=packet/QUERY
        replay_commands(QUERY,directory,query,True);replay_inputs(QUERY,directory,query)
        check('query-frozen-identities', query['source']==SOURCE and query['builds']==BUILDS)
        check('query-helper', digest(directory/'verify.py')==query['helper_sha256'])
        for name,expected in query['supporting_sha256'].items():
            check('query-supporting-'+name,digest(directory/name)==expected)
        check('query-scope-and-acceptance',query['scope']=='query-api-package-probe' and query['complete_release_acceptance'] is False and not query['test_results'])
        for command in query['commands']:
            if command['name'].startswith('final-source-'):
                check('query-internal-diff-'+command['name'],'--no-ext-diff' in command['command'] and '--no-textconv' in command['command'])
        for name,item in query['dependencies'].items():
            check('query-final-inputs-'+name,item['final_head']==item['commit'] and item['final_head_matches_recorded_commit'] and item['tracked_source_unchanged'] and item['unexpected_inputs_initial']==[] and item['unexpected_inputs_final']==[] and item['unexpected_initialized_dependencies']==[])
        graphmeta=query['resolved_package_graphs'];graphs=load(directory/graphmeta['path'])
        check('query-active-graph-manifest',digest(directory/graphmeta['path'])==graphmeta['sha256'] and graphmeta['project_count']==5==len(graphs)==len(query['active_assets']))
        commands={item['name']:item for item in query['commands']}
        for item in query['active_assets']:
            relative=str(Path(item['assets_path']).relative_to(Path(query['scratch'])))
            selected=[g for g in graphs if g['path']==relative and g['evaluation_command']==item['evaluation_command']]
            check('query-active-graph-'+item['evaluation_command'],len(selected)==1 and selected[0]['project_path']==str(Path(item['project_path']).relative_to(Path(query['scratch']))) and selected[0]['libraries'] and all('\\' not in g['path'] for g in selected))
        for graph in graphs:
            check('query-target-framework-edges-'+graph['evaluation_command'],bool(graph['targets']) and bool(graph['project_frameworks']) and bool(graph['projectFileDependencyGroups']) and bool(graph['restore_policy']))
            check('query-restore-configs-'+graph['evaluation_command'],set(graph['config_files'])=={p['source_path'] for p in graph['restore_policy']})
        check('query-policy-inventory',len(query['evaluated_properties'])==5)
        for name,item in query['evaluated_properties'].items():
            command=commands[item['command']]
            captured=load(directory/command['log'])['Properties']
            exceptions={'NoWarn':set(),'WarningsNotAsErrors':set()} if name.startswith('query-synthetic-') else FROZEN_SECURITY_EXCEPTIONS
            policies=item['restore_policy']
            check('query-restore-policy-inventory-'+name,bool(policies))
            for policy in policies:
                path=directory/policy['path']
                check('query-restore-policy-'+name+'-'+policy['path'],digest(path)==policy['sanitized_sha256'])
            check('query-evaluated-policy-'+name,item['values']==captured and not validate_properties(captured,exceptions) and item['validation_errors']==[] and item['permitted_security_exceptions']=={k:sorted(v) for k,v in exceptions.items()})
        probe=query['query_api_package_probe']
        check('query-actual-boundary-success',probe['passed'] and not probe['published'] and probe['source']==SOURCE and query['checks']['query-api-package-probe']==0 and all(commands[name]['native_exit']==0 for name in ('query-pack-Contracts','query-pack-Client','query-pack-RestApi.Generators','query-consumer-restore','query-consumer-build')))
        actual_manifest={str(path.relative_to(directory)):digest(path)
            for folder in (directory/'synthetic-consumer-inputs',directory/'package-metadata',directory/'candidate-packages')
            for path in sorted(folder.rglob('*')) if path.is_file()}
        actual_manifest[probe['generated_binding']['path']]=digest(directory/probe['generated_binding']['path'])
        check('query-retained-input-inventory-exact',actual_manifest==probe['retained_manifest'])
        check('query-pre-execution-inventory-exact',probe['pre_execution_manifest']=={k:v for k,v in actual_manifest.items() if k!=probe['generated_binding']['path']})
        for relative,expected in probe['retained_manifest'].items():
            check('query-retained-'+relative,digest(directory/relative)==expected)
        for relative,expected in probe['pre_execution_manifest'].items():
            check('query-pre-execution-'+relative,probe['retained_manifest'][relative]==expected and digest(directory/relative)==expected)
        for relative,expected in probe['synthetic_input_manifest'].items():
            check('query-synthetic-'+relative,digest(directory/'synthetic-consumer-inputs'/relative)==expected)
        candidate_version='5.2.1-local-readiness.'+SOURCE[:8]
        check('query-exact-archive-inventory',len(probe['archives'])==3 and
              {item['id'] for item in probe['archives']}=={'Hexalith.EventStore.'+name for name in ('Contracts','Client','RestApi.Generators')} and
              all(item['version']==candidate_version for item in probe['archives']))
        check('query-mandatory-content-bindings',candidate_binding_inventory(probe['archive_content_bindings'],candidate_version))
        for archive in probe['archives']:
            path=directory/'candidate-packages'/archive['name']
            check('query-archive-'+archive['id'],digest(path)==archive['sha256'] and archive_sha512(path)==archive['sha512_base64'])
            for project_name,bindings in probe['archive_content_bindings'].items():
                key=archive['id']+'/'+archive['version']
                if key in bindings:
                    project_graph=next(g for g in graphs if g['project_path'].endswith('/'+project_name+'/'+project_name+'.csproj'))
                    check('query-archive-content-'+project_name+'-'+archive['id'],bindings[key]==archive['sha512_base64'] and archive_matches_library(path,project_graph['libraries'][key]))
            with zipfile.ZipFile(path) as opened:
                nuspec=next(name for name in opened.namelist() if name.endswith('.nuspec'))
                check('query-nuspec-'+archive['id'],opened.read(nuspec)==(directory/archive['nuspec']['path']).read_bytes() and digest(directory/archive['nuspec']['path'])==archive['nuspec']['sha256'])
                if archive['id'].endswith('RestApi.Generators'):
                    check('query-packaged-analyzer',f'analyzers/dotnet/cs/{archive["id"]}.dll' in opened.namelist())
        binding=directory/probe['generated_binding']['path']
        check('query-generated-binding',digest(binding)==probe['generated_binding']['sha256'] and 'SubmitQueryAsync<global::Owner.Result>' in binding.read_text() and '"Owner.Queries.Read.v1"' in binding.read_text())
        # Recheck the frozen security exceptions against committed bytes; no
        # build or repository mutation is needed for this owner-policy proof.
        policylog=output/'frozen-builds-security-policy.log'
        command=['git','--no-replace-objects','-C',str(packet.parents[3]/'references/Hexalith.Builds'),'show',BUILDS+':Props/Directory.Packages.props']
        from verification_core import clean_environment
        env,_=clean_environment(os.environ)
        receipts['frozen-policy']=run_job('frozen-builds-security-policy',command,env)
        check('frozen-policy-native-success',receipts['frozen-policy']['native_exit']==0)
        attributes=output/'frozen-builds-gitattributes.log'
        receipts['frozen-attributes']=run_job('frozen-builds-gitattributes',command[:-1]+[BUILDS+':.gitattributes'],env)
        check('frozen-policy-checkout-transform',receipts['frozen-attributes']['native_exit']==0 and 'Props/Directory.Packages.props text eol=crlf' in attributes.read_text())
        checkout_sha=hashlib.sha256(policylog.read_bytes().replace(b'\n',b'\r\n')).hexdigest()
        check('frozen-policy-content-bound',checkout_sha==query['builds_catalog_sha256'] and '<WarningsNotAsErrors>$(WarningsNotAsErrors);NU1901;NU1902</WarningsNotAsErrors>' in policylog.read_text() and 'NU1903' not in policylog.read_text() and 'NU1904' not in policylog.read_text())
        public=load(packet/PUBLIC/'result.json');directory=packet/PUBLIC
        replay_commands(PUBLIC,directory,public,True)
        check('public-helper',digest(directory/'inspect_public_api.py')==public['helper_sha256'])
        for relative,expected in public['retained_manifest'].items():
            check('public-retained-'+relative,digest(directory/relative)==expected)
        tool=public['tool'];runtime=tool['runtime_archive']
        captured=resolve_artifact(tool['archive_artifact'],scratch)
        runtime_path=resolve_artifact(runtime['artifact'],scratch)
        check('public-tool-exact-archives',tool['version']==TOOL_VERSION and digest(captured)==TOOL_SHA256==tool['nupkg_sha256'] and digest(runtime_path)==RID_SHA256==runtime['sha256'])
        with zipfile.ZipFile(runtime_path) as opened:
            for relative,item in tool['installed_payload'].items():
                check('public-installed-payload-'+relative,hashlib.sha256(opened.read(relative)).hexdigest()==item['sha256'] and item['installed_relative_path'].endswith(relative))
            selected=[item for relative,item in tool['installed_payload'].items() if item['installed_relative_path']==tool['executed_payload']['relative_path']]
            check('public-executed-payload-bound',len(selected)==1 and selected[0]['sha256']==tool['executed_payload']['sha256'])
        for record in public['commands'][1:]:
            check('public-exact-executed-command-'+record['name'],record['command'][0]==tool['command_prefix'][0] and record['command'][0].endswith(tool['executed_payload']['relative_path']))
        check('public-two-controlled-versions',public['passed'] and len(public['packages'])==2)
        for item in public['packages']:
            version=item['version']
            for typename,label in ((MISSING,'missing-query-result'),(PRESENT,'known-present-submit-query')):
                matches=[r for r in public['commands'] if r['name']==f'contracts-{version}-{label}']
                check('public-derived-'+version+'-'+label,len(matches)==1 and api_outcome(matches[0],tool,public['scratch'],version,typename,(directory/matches[0]['log']).read_text()))
            check('public-types-'+version,item['sha256']==PACKAGES[version] and item['missing_type']=={'name':MISSING,'native_exit':1,'absent':True} and item['known_present_control']=={'name':PRESENT,'native_exit':0,'present':True})
        for policy in public['restore_policy']:
            check('public-restore-policy-'+policy['path'],digest(directory/policy['path'])==policy['sanitized_sha256'])
        for path,metadata in load(packet/'external-artifacts.json')['historical_paths'].items():
            check('historical-external-artifact-'+path,digest(retained_artifact(packet, path,metadata['sha256'],scratch,packet))==metadata['sha256'])
        controls=load(packet/CONTROLS/'result.json')
        inventory=load(packet/'control-inventory.json')
        check('focused-controls-pass',controls['python_optimization']==1 and control_report_valid(controls,inventory))
        check('focused-control-inventory-bound',controls['inventory_sha256']==digest(packet/'control-inventory.json')==digest(packet/CONTROLS/'control-inventory.json'))
        check('focused-controls-scratch-removed',not Path(controls['scratch']).exists())
        for name,item in controls['lifecycle_receipts'].items():
            check('focused-control-log-'+name,digest(packet/CONTROLS/item['log'])==item['log_sha256'])
            expected_custody = name != 'verify-main-cleanup-error'
            check('focused-control-custody-'+name,item['custodian_waited'] and item['process_tree_fully_waited'] == expected_custody and (not expected_custody or not item['remaining_owned_after_cleanup']))
        for name,expected in controls['source_sha256'].items():
            check('focused-controls-source-'+name,digest(packet/CONTROLS/name)==expected and digest(packet/name)==expected)
        expected=expected_aggregation(packet)
        readiness=load(packet/'readiness.json')
        check('readiness-bound-to-receipts',not aggregation_errors(readiness,expected))
        for key in ('source','source_tree','builds','dependencies','complete_release_acceptance','publication_authorized_by_packet','baseline_whole_suite_green','whole_test_projects','query_api_package_probe','public_api_inspection','iteration2_verification'):
            changed=copy.deepcopy(readiness);changed[key]='substituted'
            check('reject-aggregation-drift-'+key,bool(aggregation_errors(changed,expected)))
        evidence[QUERY]={'result_sha256':digest(packet/QUERY/'result.json'),'active_graphs':5,'passed':True}
        evidence[PUBLIC]={'result_sha256':digest(packet/PUBLIC/'result.json'),'payload_bound':True,'passed':True}
        complete=True
        return 0
    finally:
        result={'passed':complete and all(checks.values()),'checks':checks,'evidence':evidence,'lifecycle_receipts':receipts,
            'source_sha256':{name:digest(output/name) for name in names},'python_optimization':sys.flags.optimize,
            'scratch':str(scratch),'complete_release_acceptance':False,
            'invocation':'run-with-temp python3 -O -B '+str(Path(__file__).resolve())+' --output '+str(output)}
        (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'passed':result['passed'],'checks':len(checks),'output':str(output)}))

if __name__=='__main__':
    sys.exit(main())
