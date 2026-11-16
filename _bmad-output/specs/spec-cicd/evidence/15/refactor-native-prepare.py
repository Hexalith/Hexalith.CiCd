from pathlib import Path
p=Path('/home/administrator/projects/hexalith/cicd-story-15/references/Hexalith.McpCli/tools/live-topology/ci.py');s=p.read_text()
s=s.replace("for tool in ('timeout', 'git', 'dotnet', 'docker', 'dapr', 'unshare', 'ip', 'curl', 'bash'):","for tool in ('timeout', 'git', 'dotnet', 'docker', 'dapr', 'aspire', 'unshare', 'ip', 'curl', 'bash'):")
start=s.index('        try:\n            bounded(namespace_probe,')
end=s.index('        temporary_root =',start)
s=s[:start]+"        bounded(namespace_probe, 30, evidence / 'namespace-probe')\n"+s[end:]
start=s.index("        if not shutil.which('aspire'):")
end=s.index("        tools['aspire'] =",start)
s=s[:start]+s[end:]
start=s.index("        fresh_bundle = private / 'qualified-aspire'")
end=s.index('        expected_bundle =',start)
s=s[:start]+"""        qualified = os.environ.get('HEXALITH_CI_ASPIRE_QUALIFIED_BUNDLE')
        if not qualified or not Path(qualified).is_dir():
            raise RuntimeError('The shared environment must supply its authenticated Aspire comparison bundle.')
        fresh_bundle = Path(qualified)
"""+s[end:]
s=s.replace("str(path.relative_to(fresh_bundle / 'bundle'))", "str(path.relative_to(fresh_bundle))")
s=s.replace("for path in (fresh_bundle / 'bundle').rglob('*') if path.is_file()", "for path in fresh_bundle.rglob('*') if path.is_file()")
s=s.replace("        save(evidence / 'aspire-bundle-hashes.json', expected_bundle)","        if any(path.is_symlink() for path in fresh_bundle.rglob('*')) or any(path.is_symlink() for path in (bundle / 'bundle').rglob('*')):\n            raise RuntimeError('The qualified Aspire bundle must not contain symbolic links.')\n        actual_bundle = {str(path.relative_to(bundle / 'bundle')): hashlib.sha256(path.read_bytes()).hexdigest()\n                         for path in (bundle / 'bundle').rglob('*') if path.is_file()}\n        if actual_bundle != expected_bundle:\n            raise RuntimeError('The installed Aspire bundle differs from the complete shared comparison tree.')\n        tools['aspireBundle'] = expected_bundle\n        save(evidence / 'aspire-bundle-hashes.json', expected_bundle)")
s=s.replace('        # Never restore an unpublished local candidate: all subprocesses share one new cache.', '        # Source fixtures have their own cache; the shared module assets and outputs remain untouched.')
s=s.replace("        os.environ['NUGET_PACKAGES'] = str(package_cache)\n",'')
s=s.replace("        os.environ['CustomAfterMicrosoftCommonTargets'] = str(overrides)\n", "        source_environment = dict(os.environ, NUGET_PACKAGES=str(package_cache), CustomAfterMicrosoftCommonTargets=str(overrides))\n")
s=s.replace("        receipt['sources'] = native_cohort.select_sources(ROOT, selection, evidence, bounded)\n", "        receipt['sources'] = native_cohort.select_sources(ROOT, selection, evidence, bounded)\n        fixture_root = private / 'source-fixtures'\n        source_proof = native_sources.create(ROOT, fixture_root, selection, evidence, bounded)\n        receipt['sourceFixtureRoot'] = str(fixture_root)\n")
s=s.replace("            if module == 'Hexalith.Platform':\n                continue\n            project = PACKAGE_GATEWAY if module == 'Hexalith.EventStore' else f'src/{module}/{module}.csproj'\n            working = ROOT if module == 'Hexalith.EventStore' else ROOT / 'references' / module", "            if module not in native_sources.MODULES:\n                continue\n            project = f'src/{module}/{module}.csproj'\n            working = fixture_root / module")
s=s.replace("30, evidence / (module + '-eventstore-version'), cwd=working)","30, evidence / (module + '-eventstore-version'), cwd=working, environment=source_environment)")
s=s.replace("bounded(command, 300, evidence / (module + '-build'), cwd=working)", "bounded(command, 300, evidence / (module + '-build'), cwd=working, environment=source_environment)")
s=s.replace("300, evidence / 'parties-adapter-build', cwd=working)", "300, evidence / 'parties-adapter-build', cwd=working, environment=source_environment)")
start=s.index('        # Rebuild the actual AppHost and tests')
end=s.index("        catalog_path = evidence / 'head-catalog.json'",start)
s=s[:start]+"""        # Audit the exact already-restored module graphs through distinct package-only fixtures.
        receipt['nativeAudits'] = {}
        for index, relative in enumerate(MODULE_AUDIT_PROJECTS):
            audit = native_audit.audit_project(ROOT / relative, private / ('module-audit-' + str(index)),
                                               evidence / ('module-audit-' + str(index)), tools['sdkPolicy'], bounded)
            receipt['nativeAudits'][relative] = audit
            # The isolated metadata reader has no external network. Seed its private cache
            # only from these freshly audited package bytes; never change the module cache.
            for package in (Path(audit['privateDirectory']) / 'packages').iterdir():
                if not package.is_dir():
                    continue
                for version in package.iterdir():
                    if not version.is_dir():
                        continue
                    target = package_cache / package.name / version.name
                    if target.exists():
                        for archive in version.glob('*.nupkg'):
                            if (target / archive.name).read_bytes() != archive.read_bytes():
                                raise ValueError('Private source/reader caches disagree on audited archive bytes.')
                    else:
                        shutil.copytree(version, target)
        source_path = evidence / 'native-source-fixtures.json'
        save(source_path, native_sources.seal(source_proof))
        receipt['sourceFixtures'] = {'path': str(source_path.resolve()), 'sha256': hashlib.sha256(source_path.read_bytes()).hexdigest()}
        receipt['gateway'] = gateway_package_provenance(fixture_root)
        audit_path = evidence / 'native-reader-audit.json'
        save(audit_path, reader_audit_provenance(receipt))
        receipt['readerAudit'] = {'path': str(audit_path.resolve()), 'sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest()}
        python = Path(os.environ.get('HEXALITH_CI_PYTHON', ''))
        if not python.is_file():
            raise RuntimeError('The shared environment must supply its prepared Python interpreter.')
        tools['python'] = bounded([str(python), '--version'], 30, evidence / 'python-version')
        tools['jsonschema'] = bounded([str(python), '-c', 'import importlib.metadata; print(importlib.metadata.version("jsonschema"))'],
                                     30, evidence / 'jsonschema-version')
        if tools['jsonschema'] != '4.26.0':
            raise RuntimeError('The native product lane requires prepared jsonschema 4.26.0.')
"""+s[end:]
s=s.replace("                           NUGET_PACKAGES=prepared['nugetPackages'],", "                           NUGET_PACKAGES=prepared['nugetPackages'],\n                           MCPCLI_NATIVE_SOURCE_FIXTURES=prepared['sourceFixtures']['path'],\n                           MCPCLI_NATIVE_SOURCE_FIXTURES_SHA256=prepared['sourceFixtures']['sha256'],")
p.write_text(s)
