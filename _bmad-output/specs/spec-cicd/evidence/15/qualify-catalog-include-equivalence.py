"""Compare actual MSBuild evaluation before applying a canonical Include representation."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

REPOSITORY = Path('/home/administrator/projects/hexalith/cicd-story-15/references/Hexalith.Builds')
OUTPUT = Path(__file__).with_name('catalog-include-equivalence.json')
SELECTIONS = {
    'Microsoft.AspNetCore.Authentication.JwtBearer': 'HexalithAspNetCoreJwtBearerVersion',
    'Microsoft.AspNetCore.Mvc.Testing': 'HexalithAspNetCoreMvcTestingVersion',
    'Microsoft.AspNetCore.TestHost': 'HexalithAspNetCoreTestHostVersion',
}


def canonical(data):
    text = data.decode('utf-8')
    newline = '\r\n' if '\r\n' in text else '\n'
    rows = []
    for package, variable in SELECTIONS.items():
        old = (f'    <PackageVersion Include="{package}" Version="11.0.0" Condition="\'$(HexalithTimesheetsNet10CatalogView)\' != \'true\'" />' + newline
               + f'    <PackageVersion Include="{package}" Version="10.0.15" Condition="\'$(HexalithTimesheetsNet10CatalogView)\' == \'true\'" />')
        new = f'    <PackageVersion Include="{package}" Version="$({variable})" />'
        assert text.count(old) == 1, package
        text = text.replace(old, new)
        rows.extend([f'    <{variable}>11.0.0</{variable}>',
                     f'    <{variable} Condition="\'$(HexalithTimesheetsNet10CatalogView)\' == \'true\'">10.0.15</{variable}>'])
    anchor = '    <HexalithAspNetCoreOpenIdConnectVersion>11.0.0</HexalithAspNetCoreOpenIdConnectVersion>'
    assert text.count(anchor) == 1
    text = text.replace(anchor, newline.join(rows) + newline + anchor)
    result = text.encode('utf-8')
    items = ET.fromstring(result).findall('.//PackageVersion')
    assert all(sum(item.get('Include') == package for item in items) == 1 for package in SELECTIONS)
    return result


def main():
    before = (REPOSITORY / 'Props/Directory.Packages.props').read_bytes()
    after = canonical(before)
    view = ET.fromstring(before).findall('.//HexalithTimesheetsNet10CatalogView')[1].get('Condition')
    roles = re.findall(r"MSBuildProjectName.Equals\('([^']+)'\)", view)
    assert len(roles) == 16 and len(set(roles)) == 16
    cases = [{'name': name, 'framework': 'net10.0', 'properties': {}, 'kind': 'finite-timesheets'} for name in roles]
    cases += [{'name': name, 'framework': 'net11.0', 'properties': {}, 'kind': 'default-or-nonmatching'} for name in
              ('CatalogProbe', 'Hexalith.McpCli', 'Hexalith.Tenants', 'Hexalith.Timesheets.Works.Future', 'hexalith.timesheets', 'Hexalith.TimesheetsExtra')]
    cases += [
        {'name': 'Hexalith.Timesheets', 'framework': 'net10.0', 'properties': {
            'HexalithCommonsVersion': '3.0.0', 'HexalithPolymorphicSerializationsVersion': '2.0.0',
            'HexalithEventStoreVersion': '5.1.1', 'HexalithTenantsVersion': '8.0.0', 'HexalithMemoriesVersion': '4.0.0'}, 'kind': 'explicit-cohort'},
        {'name': 'Hexalith.Timesheets', 'framework': 'net11.0', 'properties': {'UseHexalithProjectReferences': 'true'}, 'kind': 'explicit-source-framework'},
        {'name': 'Hexalith.Timesheets', 'framework': 'net10.0', 'properties': {'HexalithTimesheetsNet10CatalogView': 'false'}, 'kind': 'explicit-view-off'},
        {'name': 'Unrelated', 'framework': 'net11.0', 'properties': {'HexalithTimesheetsNet10CatalogView': 'true'}, 'kind': 'explicit-view-on'},
    ]
    environment = {**os.environ, 'DOTNET_PROCESSOR_COUNT': '2', 'MSBUILDDISABLENODEREUSE': '1'}
    with tempfile.TemporaryDirectory(prefix='catalog-equivalence-') as temporary:
        root = Path(temporary); catalogs = [root / 'before.props', root / 'after.props']
        catalogs[0].write_bytes(before); catalogs[1].write_bytes(after)
        def evaluate(case):
            directory = root / str(cases.index(case)); directory.mkdir()
            project = directory / (case['name'] + '.proj')
            results = []
            for catalog in catalogs:
                document = ET.Element('Project'); ET.SubElement(document, 'Import', Project=str(catalog));ET.ElementTree(document).write(project, encoding='utf-8')
                command = ['dotnet', 'msbuild', str(project), '-nologo', '-noAutoResponse', '-nr:false',
                           '-p:TargetFramework=' + case['framework'], '-getProperty:HexalithTimesheetsNet10CatalogView', '-getItem:PackageVersion']
                command += ['-p:' + key + '=' + value for key, value in case['properties'].items()]
                process = subprocess.run(command, cwd=REPOSITORY, env=environment, capture_output=True, text=True, check=True, timeout=60)
                evaluated = json.loads(process.stdout)
                items = evaluated['Items']['PackageVersion']; versions = {item['Identity']: item['Version'] for item in items}
                assert len(items) == len(versions), 'evaluated duplicate ID'
                results.append((evaluated['Properties']['HexalithTimesheetsNet10CatalogView'], versions))
            assert results[0] == results[1], case
            flag, versions = results[0]
            expected = '10.0.15' if flag == 'true' else '11.0.0'
            assert all(versions[package] == expected for package in SELECTIONS)
            return {**case, 'selected_packages': len(versions), 'timesheets_view': flag,
                    'complete_selection_sha256': hashlib.sha256(json.dumps(versions,sort_keys=True).encode()).hexdigest(),
                    'three_versions': {package: versions[package] for package in SELECTIONS}, 'equivalent': True}
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(evaluate, cases))
    output = {'source_commit': subprocess.check_output(['git','-C',str(REPOSITORY),'rev-parse','HEAD'],text=True).strip(),
              'before_sha256':hashlib.sha256(before).hexdigest(),'candidate_sha256':hashlib.sha256(after).hexdigest(),
              'scope':'Actual MSBuild complete package/version selections; no restore/build or module source edits.',
              'process_limit':'DOTNET_PROCESSOR_COUNT=2 for this evaluation-only probe; frozen native suite environment unchanged',
              'cases':results,'passed':len(results)}
    OUTPUT.write_text(json.dumps(output,indent=2)+'\n');print('Equivalent actual MSBuild selections in',len(results),'cases.')

if __name__ == '__main__': main()
