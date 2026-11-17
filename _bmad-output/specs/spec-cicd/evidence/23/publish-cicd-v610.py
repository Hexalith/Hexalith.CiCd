"""Publish only the already-qualified isolated CiCd candidate, without force."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = Path('/home/administrator/projects/hexalith/cicd-story-23-v610')
BASE = '87de2b565d5896d7a24d31d065e02f033e5a4adf'
HEAD = 'f56dcbfb167b4701de5b1fc0a130971e6bca8e30'
TAG = 'a1e0c310b1f1a50d78e6132890fae6bcba769f6d'
REPO = 'Hexalith/Hexalith.CiCd'
URL = 'https://github.com/' + REPO + '.git'
PROFILE = '/home/administrator/.config/gh-cicd-agent'
report = HERE / 'cicd-v610-publication.json'
assert not report.exists()
assert not any(os.environ.get(name) for name in ('GH_TOKEN', 'GITHUB_TOKEN'))
environment = dict(os.environ, GH_CONFIG_DIR=PROFILE, GIT_TERMINAL_PROMPT='0')
token = subprocess.check_output(['gh', 'auth', 'token', '--hostname', 'github.com'],
                                env=environment, text=True).strip()
assert token
record = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'repository': REPO, 'profile': PROFILE, 'base': BASE, 'candidate': HEAD,
          'environmentTokenOverridesPresent': False, 'operations': [],
          'status': 'checking', 'forcePush': False, 'rootWorkspaceMutation': False}


def save():
    report.write_text(json.dumps(record, indent=2) + '\n')
    report.chmod(0o600)


def run(arguments):
    process = subprocess.run(arguments, cwd=ROOT, env=environment, capture_output=True,
                             text=True, timeout=240)
    return process


def api(path):
    result = run(['gh', 'api', path])
    if result.returncode:
        record['operations'].append({'read': path, 'exit': result.returncode,
                                     'failure': result.stderr.replace(token, '[redacted]')})
        raise RuntimeError('Read refused: ' + path)
    return json.loads(result.stdout)


def git(*arguments):
    result = run(['git', '-c', 'credential.helper=', '-c',
                  'credential.helper=!gh auth git-credential', *arguments])
    if result.returncode:
        record['operations'].append({'git': list(arguments), 'exit': result.returncode,
                                     'failure': result.stderr.replace(token, '[redacted]')})
        raise RuntimeError('Git operation refused')
    return result.stdout.strip()


save()
try:
    verification = json.loads((HERE / 'cicd-v610-validation-03.json').read_text())
    assert verification['source'] == HEAD and verification['status'] == 'passed'
    assert verification['exit'] == 0 and verification['candidatePreserved'] is True
    stdout_path = HERE / verification['stdout']['path']
    assert hashlib.sha256(stdout_path.read_bytes()).hexdigest() == verification['stdout']['sha256']
    verdict = json.loads(stdout_path.read_text())
    assert verdict['global'] is True
    assert verdict['modules'] == ['Hexalith.AI.Tools', 'Hexalith.Commons', 'Hexalith.PolymorphicSerializations']
    record['qualifiedVerdict'] = verdict
    account = api('user')
    assert (account['login'], account['id']) == ('jpiquot', 6775094)
    record['account'] = {'login': account['login'], 'id': account['id']}
    metadata = api('repos/' + REPO)
    assert metadata['full_name'] == REPO and metadata['id'] == 1379430755
    record['repositoryId'] = metadata['id']
    assert git('rev-parse', 'HEAD') == HEAD
    assert not git('status', '--porcelain')
    assert git('merge-base', BASE, HEAD) == BASE
    git('diff', '--check', BASE, HEAD)
    headers = run(['git', 'config', '--get-regexp', r'^http\..*extraheader$'])
    assert headers.returncode in (0, 1) and not headers.stdout.strip()
    live = api('repos/' + REPO + '/commits/main')['sha']
    record['liveMainBefore'] = live
    assert live == BASE, 'Live main advanced; reapply on a fresh branch before publication'
    release = api('repos/Hexalith/Hexalith.Builds/releases/tags/v6.1.0')
    assert release['draft'] is False and release['prerelease'] is False and release['immutable'] is True
    tag = api('repos/Hexalith/Hexalith.Builds/git/ref/tags/v6.1.0')['object']
    if tag['type'] == 'tag':
        tag = api('repos/Hexalith/Hexalith.Builds/git/tags/' + tag['sha'])['object']
    assert tag['type'] == 'commit' and tag['sha'] == TAG
    record['releasedBuilds'] = {'tag': 'v6.1.0', 'sha': TAG, 'immutable': True}
    assert git('ls-remote', URL, 'refs/heads/main').split()[0] == BASE
    record['status'] = 'publishing'
    save()
    result = run(['git', '-c', 'credential.helper=', '-c',
                  'credential.helper=!gh auth git-credential', 'push', '--porcelain',
                  URL, HEAD + ':refs/heads/main'])
    record['operations'].append({'git': 'ordinary fast-forward push to main', 'exit': result.returncode,
                                 'stdout': result.stdout.replace(token, '[redacted]'),
                                 'stderr': result.stderr.replace(token, '[redacted]')})
    assert result.returncode == 0, 'Publication refused; retain the intended profile and report the failure'
    after = api('repos/' + REPO + '/commits/main')['sha']
    record['liveMainAfter'] = after
    assert after == HEAD
    content = api('repos/' + REPO + '/contents/builds-version?ref=' + HEAD)
    import base64
    pin = base64.b64decode(content['content']).decode().strip()
    assert pin == 'v6.1.0'
    record['liveBuildsPin'] = pin
    record['candidatePreserved'] = git('rev-parse', 'HEAD') == HEAD and not git('status', '--porcelain')
    assert record['candidatePreserved']
    record['status'] = 'published'
except BaseException as error:
    record['status'] = 'failed'
    record['error'] = type(error).__name__ + ': ' + str(error).replace(token, '[redacted]')
    raise
finally:
    save()
    print(json.dumps({key: record.get(key) for key in ('repository', 'candidate', 'status', 'liveMainBefore', 'liveMainAfter', 'liveBuildsPin')}, indent=2))
