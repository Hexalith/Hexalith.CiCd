#!/usr/bin/env python3
"""Run the blocking product prerequisite on the exact fresh-main candidate."""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import signal
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SCRATCH = Path(os.environ['TMPDIR'])
assert SCRATCH != Path('/tmp') and SCRATCH.is_dir(), 'Use run-with-temp'
ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0)
policy = json.loads((OUT / 'qualification.json').read_text())
source = ROOT / 'references/Hexalith.Folders'
input_record = policy['modules']['Folders']
module = SCRATCH / 'Hexalith.Folders'
REPORT = {'candidateTree': input_record['candidateTree'],
          'freshMain': input_record['freshMain'], 'commands': [],
          'scope': 'Focused prerequisite for required strict Server hook; no complete qualification claimed',
          'commitsCreated': False, 'pushesAttempted': False, 'dependencies': {}}


def git(path, *args):
    return subprocess.check_output(['git', '-c', 'submodule.recurse=false', '-C', str(path), *args], stderr=subprocess.STDOUT)


def clone(origin, target, revision):
    git(ROOT, 'clone', '--quiet', '--shared', '--no-checkout', '--no-recurse-submodules', str(origin), str(target))
    git(target, 'checkout', '--quiet', '--detach', revision)


def save():
    (OUT / 'Folders-product-qualification.json').write_text(json.dumps(REPORT, indent=2) + '\n')


def job(label, command, timeout=900):
    log = OUT / (label + '.txt')
    env = dict(os.environ, CI='true', DOTNET_CLI_TELEMETRY_OPTOUT='1',
               DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER='1', MSBUILDDISABLENODEREUSE='1')
    print(label + ' running', flush=True)
    with log.open('wb') as output:
        child = subprocess.Popen(command, cwd=module, env=env, stdout=output,
                                 stderr=subprocess.STDOUT, start_new_session=True)
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
    REPORT['commands'].append({'label': label, 'argv': command, 'exitCode': code, 'log': log.name})
    save()
    print(label + ' exit ' + str(code), flush=True)
    return code


try:
    clone(source, module, input_record['freshMain'])
    patch = OUT / 'Folders-candidate.patch'
    subprocess.run(['git', 'apply', '--index', '--binary', str(patch)], cwd=module, check=True)
    assert git(module, 'write-tree').decode().strip() == REPORT['candidateTree']
    for line in git(module, 'ls-files', '--stage', 'references').decode().splitlines():
        metadata, relative = line.split('\t', 1)
        mode, revision, stage = metadata.split()
        if mode != '160000':
            continue
        origin = ROOT / 'references' / Path(relative).name
        if not (origin / '.git').exists():
            raise RuntimeError('Unavailable root-declared dependency: ' + relative)
        clone(origin, module / relative, revision)
        REPORT['dependencies'][relative] = revision
    REPORT['candidatePatchSha256'] = hashlib.sha256(patch.read_bytes()).hexdigest()
    REPORT['componentFixtureSupplied'] = bool(os.environ.get('HEXALITH_WORKLOAD_COMPONENT_FILE'))
    save()
    flags = ['-p:Configuration=Release', '-p:UseHexalithProjectReferences=false', '-p:UseNuGetDeps=true',
             '-p:NuGetAudit=true', '-p:NuGetAuditMode=all', '-p:NuGetAuditLevel=low',
             '-warnaserror', '-m:1', '-p:UseSharedCompilation=false', '-nr:false']
    project = 'tests/Hexalith.Folders.Server.Tests/Hexalith.Folders.Server.Tests.csproj'
    code = job('Folders-server-package-build', ['dotnet', 'build', project, '--configuration', 'Release', '--disable-build-servers', *flags])
    if not code:
        code = job('Folders-explicit-component-prerequisite', [
            'dotnet', 'tests/Hexalith.Folders.Server.Tests/bin/Release/net11.0/Hexalith.Folders.Server.Tests.dll',
            '-class', 'Hexalith.Folders.Server.Tests.EnrolledWorkloadSourceBoundaryTests',
            '-explicit', 'on', '-noLogo', '-noColor', '-failSkips'])
    REPORT['exitCode'] = code
    REPORT['status'] = 'failed required product prerequisite' if code else 'focused prerequisite passed; complete approved checks still required'
except Exception as error:
    REPORT['status'] = 'qualification setup failed'
    REPORT['error'] = str(error)
    raise
finally:
    save()
print(json.dumps(REPORT), flush=True)
raise SystemExit(REPORT['exitCode'])
