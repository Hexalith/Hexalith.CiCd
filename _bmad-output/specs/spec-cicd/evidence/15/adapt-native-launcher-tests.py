from pathlib import Path
import ast
p=Path('/home/administrator/projects/hexalith/cicd-story-15/references/Hexalith.McpCli/tools/live-topology/test_ci.py');s=p.read_text();lines=s.splitlines(keepends=True)
replacements={
 'test_hosted_namespace_setup_reprobes_before_building_sources': '''    def test_hosted_product_probe_requires_prepared_namespaces_without_reconfiguring_host(self):
        self.env.update(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted')
        result = self.invoke('prepare-ci.sh', 'namespace-needs-setup')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('unshare --user', result.stderr)
        self.assert_no_build_or_live()
        self.assertFalse(any(call[0] == 'sudo' for call in self.calls()))
        self.assertFalse((self.root / 'namespace-enabled').exists())
''',
 'test_hosted_namespace_setup_and_reprobe_failures_stop_source_builds': '''    def test_prepared_hosted_namespaces_are_rechecked_before_private_source_builds(self):
        self.env.update(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted')
        (self.root / 'namespace-enabled').touch()
        self.prepare_result = self.prepare()
        calls = self.calls()
        probes = [index for index, call in enumerate(calls) if call[0] == 'unshare']
        build = next(index for index, call in enumerate(calls) if call[0] == 'dotnet' and call[2] == 'build')
        self.assertEqual(1, len(probes))
        self.assertLess(probes[0], build)
        self.assertFalse(any(call[0] == 'sudo' for call in calls))
''',
 'test_missing_bundle_is_provisioned_before_build_and_setup_failure_propagates': '''    def test_missing_shared_bundle_is_named_and_never_reinstalled_by_product_preparation(self):
        dashboard = Path(self.env['HOME']) / '.aspire/bundle/dashboard/Aspire.Dashboard'
        dashboard.unlink()
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Qualified Aspire bundle mismatch: dashboard/Aspire.Dashboard', result.stderr)
        self.assertFalse(dashboard.exists())
        self.assertFalse(any(call[0] == 'aspire' and call[2] == 'setup' for call in self.calls()))
        self.assert_no_build_or_live()
''',
 'test_missing_aspire_installs_only_a_digest_verified_release_archive': '''    def test_missing_shared_aspire_is_named_before_any_product_installation_or_build(self):
        (self.bin / 'aspire').unlink()
        for tool in ('python3', 'bash', 'dirname'):
            (self.bin / tool).symlink_to(shutil.which(tool))
        self.env['PATH'] = str(self.bin)
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Missing prerequisite: aspire', result.stderr)
        self.assertFalse(any(call[0] == 'curl' for call in self.calls()))
        self.assert_no_build_or_live()
''',
 'test_failed_preparation_retains_owned_private_location': '''    def test_failed_preparation_retains_owned_private_location(self):
        (Path(self.env['HOME']) / '.aspire/bundle/dashboard/Aspire.Dashboard').unlink()
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Qualified Aspire bundle mismatch', result.stderr)
        receipt = json.loads((self.evidence / 'preparation.json').read_text())
        self.assertEqual('failed', receipt['result'])
        self.assertTrue(Path(receipt['privateDirectory']).is_dir())
        self.assertFalse(Path(receipt['privateDirectory']).is_relative_to(self.evidence))
''',
 'test_hosted_runner_refreshes_complete_existing_bundle_before_hash_validation': '''    def test_hosted_product_preparation_rejects_stale_shared_bundle_without_repairing_it(self):
        self.env.update(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted')
        managed = Path(self.env['HOME']) / '.aspire/bundle/managed/aspire-managed'
        managed.write_text('older cached managed bundle')
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Qualified Aspire bundle mismatch: managed/aspire-managed', result.stderr)
        self.assertEqual('older cached managed bundle', managed.read_text())
        self.assertFalse(any(call[0] == 'aspire' and call[2] == 'setup' for call in self.calls()))
        self.assert_no_build_or_live()
''',
 'test_hosted_bundle_refresh_still_rejects_mismatched_managed_payload': '''    def test_shared_comparison_bundle_is_required_and_never_reconstructed_by_product(self):
        self.env.pop('HEXALITH_CI_ASPIRE_QUALIFIED_BUNDLE')
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('shared environment must supply its authenticated Aspire comparison bundle', result.stderr)
        self.assertFalse(any(call[0] == 'aspire' and call[2] == 'setup' for call in self.calls()))
        self.assert_no_build_or_live()
''',
}
nodes=[node for node in ast.walk(ast.parse(s)) if isinstance(node,ast.FunctionDef) and node.name in replacements]
assert len(nodes)==len(replacements)
for node in sorted(nodes,key=lambda x:x.lineno,reverse=True):lines[node.lineno-1:node.end_lineno]=[replacements[node.name]]
s=''.join(lines)
s=s.replace("        result = self.invoke('prepare-ci.sh', 'incomplete-bundle')", "        (Path(self.env['HEXALITH_CI_ASPIRE_QUALIFIED_BUNDLE']) / 'dcp/dcp').unlink()\n        result = self.invoke('prepare-ci.sh')",1)
s=s.replace("self.assertEqual(8, len(builds))", "self.assertEqual(5, len(builds))",1)
s=s.replace("        self.prepare()\n        builds = [call for call in self.calls() if call[0] == 'dotnet' and call[2] == 'build']\n        selected", "        prepared = self.prepare()\n        builds = [call for call in self.calls() if call[0] == 'dotnet' and call[2] == 'build']\n        selected",1)
s=s.replace("self.assertEqual(str(self.root / 'references/Hexalith.Parties'), selected[0][1])", "self.assertEqual(str(Path(prepared['sourceFixtureRoot']) / 'Hexalith.Parties'), selected[0][1])",1)
start=s.index('    def test_actual_domain_asset_version_and_project_mutations_refuse_prepare_and_execute')
end=s.index('\n    def ',start+5)
part=s[start:end]
part=part.replace("                        if phase == 'run': self.prepare()", "                        selected_asset = asset\n                        if phase == 'run':\n                            prepared = self.prepare()\n                            selected_asset = Path(prepared['sourceFixtureRoot']) / f'Hexalith.{module}/src/Hexalith.{module}/obj/project.assets.json'")
part=part.replace('                        asset.write_text(json.dumps(changed))','                        selected_asset.write_text(json.dumps(changed))').replace('                            asset.write_text(original)','                            selected_asset.write_text(original)')
part=part.replace("self.assertIn('restored assets must contain only the exact published EventStore package cohort', result.stderr)", "self.assertIn('restored assets must contain only the exact published EventStore package cohort' if phase == 'prepare' else 'source fixture bytes changed', result.stderr)")
s=s[:start]+part+s[end:]
p.write_text(s)
