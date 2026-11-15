# Read-only closeout reproduction

Run from the CiCd root. This audits the saved evidence, repeats the recorded
GET requests and independently lists remote heads. It issues no push, dispatch
or PR operation and does not requalify current write restrictions. Later
external changes may differ from the saved snapshot; record them separately.
The credential source, account and expiration do not establish token-byte
continuity or unchanged grants since the historical probes. Story 10-2 has
populated the canonical policy template; no module delivery is proved here.

```bash
run-with-temp python3 - <<'PY'
import hashlib, json, os, pathlib, stat, subprocess

root = pathlib.Path.cwd()
folder = root / '_bmad-output/specs/spec-cicd/evidence/10-1'
saved = json.loads((folder / 'closeout-verification.json').read_text())
for name, digest in saved['retained_evidence_sha256'].items():
    assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
for prefix, suffix in [('owned-local', '.json'), ('commons-main-tree', '.txt')]:
    assert (folder / (prefix + '-before' + suffix)).read_bytes() == (
        folder / (prefix + '-after' + suffix)).read_bytes()

def local_snapshot():
    module = root / 'references/Hexalith.Commons'
    values = {}
    for path in saved['closeout_local_owned_snapshot_after']:
        if path.startswith('gitlink:') or path in ('local_HEAD', 'status_porcelain'):
            continue
        source = module / path
        values[path] = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
    for key, args in [
        ('gitlink:references/Hexalith.Builds', ['rev-parse', 'HEAD:references/Hexalith.Builds']),
        ('local_HEAD', ['rev-parse', 'HEAD']),
        ('status_porcelain', ['status', '--porcelain=v1']),
    ]:
        value = subprocess.check_output(['git', *args], cwd=module, text=True)
        values[key] = value if key == 'status_porcelain' else value.strip()
    return values

before = local_snapshot()
source = pathlib.Path(saved['credential_source'])
info = source.lstat()
assert stat.S_ISREG(info.st_mode) and not source.is_symlink()
assert info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600
secret = source.read_text().strip()
assert secret.startswith('github_pat_')
env = os.environ.copy()
assert env.get('GH_CONFIG_DIR') == saved['effective_GH_CONFIG_DIR']
for key in list(env):
    if key in ('GITHUB_TOKEN', 'GH_DEBUG', 'GIT_CURL_VERBOSE', 'GIT_CONFIG_PARAMETERS') or key.startswith('GIT_TRACE'):
        env.pop(key, None)
env.update(GH_TOKEN=secret, GH_PROMPT_DISABLED='1', GIT_TERMINAL_PROMPT='0',
           GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_COUNT='0')
for request in saved['read_only_responses']:
    assert request['method'] == 'GET'
    result = subprocess.run(['gh', 'api', '--method', 'GET', '--include', request['endpoint']],
                            cwd=os.environ['TMPDIR'], env=env, text=True, capture_output=True)
    assert secret not in result.stdout + result.stderr
    assert result.returncode == 0
    body = json.loads(result.stdout.split('\n\n', 1)[1])
    endpoint = request['endpoint']
    if endpoint == 'user':
        assert body['login'] == saved['authenticated_account']['login']
    elif '/git/matching-refs/' in endpoint:
        assert not any('cicd-token-qualification-20261115-1752' in row['ref'] for row in body)
    elif '/pulls?' in endpoint:
        assert body == []
    elif '/runs?' in endpoint:
        assert body['total_count'] == 0 and body['workflow_runs'] == []
    print('GET', endpoint, 'exit=0')
result = subprocess.run(saved['independent_git_ls_remote_result']['command'],
                        cwd=os.environ['TMPDIR'], env=env, text=True, capture_output=True)
assert secret not in result.stdout + result.stderr
assert result.returncode == 0
assert 'cicd-token-qualification-20261115-1752' not in result.stdout
print(result.stdout, end='')
assert before == local_snapshot()
print('Retained evidence hashes match; cleanup confirmed; local owned state unchanged.')
PY
```

The original three live outcomes remain in `first-probes.json` and the numbered
server transcripts. The closeout JSON records their assertions, exact GET
endpoints, selected response headers, independent Git command/result,
before/after local hashes and authentication observations. Its provenance map
identifies the planning documents used for the compiled epic context.
