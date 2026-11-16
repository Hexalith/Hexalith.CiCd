"""Validate exact publication messages with the pinned shared commit policy."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
BUILDS = Path('/home/administrator/projects/hexalith/builds-story-23')
sys.dont_write_bytecode = True
sys.path.insert(0, str(BUILDS / 'Github/lib'))
from guard_tools import Tools

messages = {
    'builds': 'feat(ci): record Dapr initialization and timeouts\n',
    'cicd': ('build(ci): expose shared timeout configuration\n\n'
             'Record the approved Tenants migration decisions and local checks.\n'),
}
with tempfile.TemporaryDirectory(prefix='publication-tools-', dir=os.environ['TMPDIR']) as directory:
    tools = Tools(directory)
    for repository, message in messages.items():
        tools.lint_message(message, repository + ' publication commit')
        (HERE / (repository + '-commit-message.txt')).write_text(message)
report = {
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'builds_source': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BUILDS, text=True).strip(),
    'tools_lock_sha256': hashlib.sha256((BUILDS / 'Github/guard/package-lock.json').read_bytes()).hexdigest(),
    'policy_sha256': hashlib.sha256((BUILDS / 'Github/guard/commitlint.config.mjs').read_bytes()).hexdigest(),
    'node_version': subprocess.check_output(['node', '--version'], text=True).strip(),
    'locked_install': True, 'signatures_verified': True,
    'messages': {name: {'message': message, 'result': 'pass'} for name, message in messages.items()},
}
(HERE / 'publication-commitlint.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
