"""Publish the explicitly authorized, qualified AI.Tools product preparation."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
MODULE = Path('/home/administrator/projects/hexalith/ai-tools-story-12')
BASE = '736687b79c1e4fa8beabdab75c4675bb76c466b9'
HEAD = 'cfd1ebea92587cdea41b9aa2cff47358bf2f32f6'
assert os.environ.get('GH_CONFIG_DIR') == '/home/administrator/.config/gh-cicd-agent'
assert not any(key in os.environ for key in ('GH_TOKEN', 'GITHUB_TOKEN'))
environment = dict(os.environ,
    GH_TOKEN=Path('/home/administrator/.config/gh-module-agent/token').read_text().strip(),
    GH_PROMPT_DISABLED='1')
proof_path = HERE / 'preparation-proof.json'
proof = json.loads(proof_path.read_text())
assert proof['result'] == 'pass' and proof['base'] == BASE and proof['head'] == HEAD
assert proof['shared_commitlint'] == proof['prior_owning_commitlint'] == proof['audit_lint'] == 'pass'
assert proof['preserved_legacy_commitlint_config']['oid'] == '0616fb937bb77b75355c94334276f9aa337b7c1f'
path = HERE / 'preparation-publication.json'
assert not path.exists(), 'Inspect the existing publication record before any retry'
report = {'started_at': datetime.now(timezone.utc).isoformat(),
    'authorization': 'Human: push all changes to main', 'repository': 'Hexalith/Hexalith.AI.Tools',
    'credential': 'protected module-agent token; no credential switch',
    'base': BASE, 'head': HEAD, 'proof_sha256': hashlib.sha256(proof_path.read_bytes()).hexdigest(),
    'adoption_registration_published': False, 'operations': [], 'push_attempted': False}


def save():
    path.write_text(json.dumps(report, indent=2) + '\n')


def run(arguments):
    result = subprocess.run(arguments, cwd=MODULE, env=environment,
        capture_output=True, text=True, timeout=90)
    report['operations'].append({'command': arguments, 'exit': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr})
    save()
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


assert not run(['git', 'status', '--porcelain'])
assert run(['git', 'rev-parse', 'HEAD']) == HEAD
run(['git', '-c', 'submodule.recurse=false', 'fetch', '--no-recurse-submodules', 'origin', 'main'])
assert run(['git', 'rev-parse', 'origin/main']) == BASE
current = json.loads(run(['gh', 'api', 'repos/Hexalith/Hexalith.AI.Tools/git/ref/heads/main']))
assert current['object']['sha'] == BASE
assert run(['git', 'ls-tree', BASE, 'commitlint.config.mjs']) == run(['git', 'ls-tree', HEAD, 'commitlint.config.mjs'])
report['immediate_prepush_observed_at'] = datetime.now(timezone.utc).isoformat()
report['push_attempted'] = True
save()
run(['git', 'push', '--porcelain', 'origin', HEAD + ':refs/heads/main'])
current = json.loads(run(['gh', 'api', 'repos/Hexalith/Hexalith.AI.Tools/git/ref/heads/main']))
assert current['object']['sha'] == HEAD
report.update(push_confirmed=True, result='qualified product preparation published; no adoption',
    completed_at=datetime.now(timezone.utc).isoformat())
save()
print(json.dumps({'repository': report['repository'], 'main': HEAD,
    'push_confirmed': True, 'adoption_registration_published': False}))
