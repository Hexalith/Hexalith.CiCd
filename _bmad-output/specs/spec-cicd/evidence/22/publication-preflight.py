"""Read current module metadata and reproduce the required checker in scratch.

Run with run-with-temp. The module-agent credential is a child-process input
only; no token value is recorded. This script never pushes or modifies settings.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
MODULE = Path('/home/administrator/projects/hexalith/memories-story-22')
REPOSITORY = 'Hexalith/Hexalith.Memories'
environment = dict(os.environ, GH_PROMPT_DISABLED='1', GIT_TERMINAL_PROMPT='0')
assert not any(environment.get(key) for key in ('GH_TOKEN', 'GITHUB_TOKEN'))
environment.pop('GH_DEBUG', None)
environment.pop('GIT_CURL_VERBOSE', None)
environment['GH_TOKEN'] = Path('/home/administrator/.config/gh-module-agent/token').read_text().strip()
report = {'recordedAt': datetime.now(timezone.utc).isoformat(),
          'repository': REPOSITORY, 'defaultProfile': os.environ.get('GH_CONFIG_DIR'),
          'inheritedCredentialOverridePresent': False,
          'moduleAuthentication': 'protected module-agent token in child environment',
          'requests': [], 'pushPerformed': False}

for endpoint in ('user', 'repos/' + REPOSITORY, 'repos/' + REPOSITORY + '/commits/main'):
    result = subprocess.run(['gh', 'api', '--include', endpoint], env=environment,
                            capture_output=True, text=True, timeout=45)
    headers, _, body = result.stdout.partition('\n\n')
    row = {'endpoint': endpoint, 'exitCode': result.returncode,
           'headers': [line for line in headers.splitlines() if line.lower().startswith(
               ('http/', 'x-oauth-scopes:', 'x-accepted-github-permissions:'))]}
    value = json.loads(body)
    if result.returncode:
        row['error'] = value
    elif endpoint == 'user':
        row['data'] = {key: value.get(key) for key in ('login', 'id')}
    elif endpoint.endswith('/commits/main'):
        row['data'] = {'sha': value['sha']}
        report['currentRemoteMain'] = value['sha']
    else:
        row['data'] = {key: value.get(key) for key in ('full_name', 'default_branch', 'permissions')}
    report['requests'].append(row)

scratch = Path(os.environ['TMPDIR']) / 'memories-prepush'
subprocess.run(['git', 'clone', '--local', '--shared', '--no-checkout', str(MODULE), str(scratch)],
               check=True, capture_output=True)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=MODULE, text=True).strip()
subprocess.run(['git', 'checkout', '--detach', head], cwd=scratch, check=True, capture_output=True)
subprocess.run(['git', 'remote', 'set-url', 'origin', 'https://github.com/' + REPOSITORY + '.git'],
               cwd=scratch, check=True)
pin = subprocess.check_output(['git', 'rev-parse', head + ':references/Hexalith.Builds'],
                              cwd=MODULE, text=True).strip()
builds = scratch / 'references/Hexalith.Builds'
subprocess.run(['git', 'clone', '--local', '--shared', '--no-checkout',
                str(MODULE / 'references/Hexalith.Builds'), str(builds)], check=True, capture_output=True)
subprocess.run(['git', 'checkout', '--detach', pin], cwd=builds, check=True, capture_output=True)
result = subprocess.run(['python3', 'references/Hexalith.Builds/check.py'], cwd=scratch,
                        capture_output=True, text=True, timeout=45)
(HERE / 'publication-checker.log').write_text(result.stdout + result.stderr)
report['candidate'] = head
report['buildsGitlink'] = pin
report['requiredChecker'] = {'command': 'python3 references/Hexalith.Builds/check.py',
                             'exitCode': result.returncode, 'output': result.stdout + result.stderr}
report['approvedExceptionComplete'] = False
report['remainingExceptionRequirements'] = [
    'Released shared source/composition, browser, coverage, SQL and rollout support',
    'Complete applicable runtime/product and package-consumer verification',
    'Resolution of the unchanged C1 approval/input mismatch and dependent suite verification',
    'AD-21 maintainer preconditions and exact current-main product reapplication as needed']
(HERE / 'publication-preflight.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
