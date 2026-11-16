"""Record the committed draft's pre-push prerequisites without a module push."""
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[5]
MODULE = ROOT / 'references/Hexalith.McpCli'
EVIDENCE = Path(__file__).parent


def git(*args):
    return subprocess.check_output(['git', *args], cwd=MODULE, text=True).strip()


head = git('rev-parse', 'HEAD')
base = git('rev-parse', 'origin/main')
protected = [
    '.github/workflows', '.github/dependabot.yml', '.github/hexalith-ci.json',
    '.releaserc.json', '.gitmodules', 'references/Hexalith.Builds',
    'AGENTS.md', 'CLAUDE.md', '.github/copilot-instructions.md', '.claude/settings.json',
]
differences = git('diff', '--name-status', base, head, '--', *protected)
assert not differences, differences
literal = subprocess.run(['python3', 'references/Hexalith.Builds/check.py'], cwd=MODULE,
                         capture_output=True, text=True, timeout=30)
(EVIDENCE / 'push-request-literal-check.log').write_text(literal.stdout + literal.stderr)

scratch = Path(os.environ['TMPDIR'])
copy = scratch / 'module'
pin = git('rev-parse', 'HEAD:references/Hexalith.Builds')
with (EVIDENCE / 'push-request-current-package-mode.log').open('w') as log:
    subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-recurse-submodules', str(MODULE), str(copy)],
                   check=True, stdout=log, stderr=subprocess.STDOUT)
    builds = scratch / 'Hexalith.Builds'
    builds.mkdir()
    archive = subprocess.check_output(['git', 'archive', pin], cwd=ROOT / 'references/Hexalith.Builds')
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(builds, filter='data')
    assert not (copy / 'references/Hexalith.Builds/.git').exists()
    environment = dict(os.environ, NUGET_PACKAGES=str(scratch / 'packages'),
                       NUGET_HTTP_CACHE_PATH=str(scratch / 'http'), DOTNET_NOLOGO='1',
                       DOTNET_CLI_TELEMETRY_OPTOUT='1', MSBUILDDISABLENODEREUSE='1',
                       DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER='1')
    command = ['dotnet', 'restore', 'tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj',
               '-p:UseHexalithProjectReferences=false', '-p:NuGetAudit=true', '-p:NuGetAuditMode=all',
               '-p:NuGetAuditLevel=low', '-warnaserror']
    result = subprocess.run(command, cwd=copy, env=environment, stdout=log,
                            stderr=subprocess.STDOUT, timeout=300)

report = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'commit': head, 'fresh_main': base,
          'builds_import': pin, 'protected_paths': protected, 'owned_content_diff': differences,
          'literal_checker_exit': literal.returncode, 'package_restore_exit': result.returncode,
          'package_restore_command': command, 'module_push_permitted': False,
          'note': 'This does not waive required package-mode build/test/consumer checks.',
          'nested_submodules_initialized': False}
(EVIDENCE / 'push-request-current-gate.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
