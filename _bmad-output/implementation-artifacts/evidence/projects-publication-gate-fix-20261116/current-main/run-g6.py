from pathlib import Path
import os
import runpy
import shutil

source = Path('/home/administrator/projects/hexalith/cicd/_bmad-output/specs/spec-cicd/evidence/18/qualify-owning-g6.py')
results = Path('/home/administrator/projects/hexalith/cicd/_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116/current-main/g6')
results.mkdir(parents=True,exist_ok=True)
scratch = Path(os.environ['TMPDIR'])
private = scratch / 'owning-g6-current-check'
private.mkdir(exist_ok=True)
helper = private / 'qualify-owning-g6.py'
shutil.copyfile(source, helper)
try:
    runpy.run_path(str(helper))['run'](scratch / 'Hexalith.Projects', scratch)
finally:
    for report in private.glob('*.json'):
        shutil.copyfile(report, results / report.name)

fixture_report = scratch / 'owning-fixture-cleanup.json'
if fixture_report.exists():
    shutil.copyfile(fixture_report, results / fixture_report.name)
