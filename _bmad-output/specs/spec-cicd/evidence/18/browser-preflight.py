"""Qualify TypeScript and all browser-selection controls before AppHost allocation."""
from pathlib import Path
import os
import shutil
import subprocess

source = Path(__file__).resolve().parents[5] / 'references/Hexalith.Projects'
target = Path(os.environ['TMPDIR']) / 'browser-workspace'
target.mkdir()
names = subprocess.check_output(['git', '-C', str(source), 'ls-files', '--cached', '--others', '--exclude-standard', '-z', '--', 'tests/e2e'])
for raw in names.split(b'\0'):
    if raw:
        path = source / os.fsdecode(raw)
        if path.is_file() and not path.is_symlink():
            output = target / path.relative_to(source / 'tests/e2e')
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, output)
environment = {**os.environ, 'CI':'true', 'E2E_LIVE_APPHOST':'0', 'E2E_PACKAGE_FIXTURES':'1',
               'E2E_PACKAGE_OUTPUT':str(target / 'private-output')}
for command in (['npm', 'ci', '--ignore-scripts'], ['npm', 'audit', 'signatures'],
                ['node', 'node_modules/typescript/bin/tsc', '--noEmit'],
                ['node', 'node_modules/@playwright/test/cli.js', 'test', 'specs/browser-configuration.spec.ts', '--project', 'chromium']):
    print('PREFLIGHT', *command, flush=True)
    subprocess.run(command, cwd=target, env=environment, check=True)
