"""Validate publication messages using each repository's pinned policy bytes."""
from pathlib import Path
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
BUILDS = ROOT / 'references/Hexalith.Builds'
PIN = '66fc4855a6d3746fbfc8ad02db27d4ecd44dd8c9'
ROOT_PIN = '8d89eb81bb114fb7e57cce4f5e1718367de86d68'
PATHS = ['Github/guard', 'Github/lib/guard_tools.py', 'Github/lib/commit_policy.py']
subprocess.run(['git', '-C', str(BUILDS), 'diff', '--exit-code', PIN, ROOT_PIN, '--', *PATHS], check=True)
archive = subprocess.check_output(['git', '-C', str(BUILDS), 'archive', PIN, 'Github/guard', 'Github/lib'])
policy = Path(os.environ['TMPDIR']) / 'pinned-policy'
policy.mkdir()
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    tar.extractall(policy, filter='data')
sys.dont_write_bytecode = True
sys.path.insert(0, str(policy / 'Github/lib'))
from guard_tools import Tools

tools_dir = Path(os.environ['TMPDIR']) / 'guard-tools'
tools_dir.mkdir()
tools = Tools(tools_dir)
messages = {
    'Hexalith.Platform': 'fix(test): manage complete component fixture lifetime\n',
    'Hexalith.Folders': 'fix(test): qualify package-bound component fixtures\n',
    'Hexalith.CiCd': 'build(cicd): publish pending module preparation and evidence\n',
    'Hexalith.CiCd-verification': 'docs(cicd): record main publication verification\n',
}
results = {}
for name, message in messages.items():
    tools.lint_message(message, name + ' publication')
    (OUT / (name + '-message.txt')).write_text(message)
    results[name] = {'message': message, 'result': 'passed'}
report = {'modulePolicyPin': PIN, 'rootPolicyPin': ROOT_PIN,
          'pinnedCommitValidationBytesIdentical': True, 'lockedInstallation': 'passed',
          'signatureVerification': 'passed',
          'lockSha256': hashlib.sha256((policy / 'Github/guard/package-lock.json').read_bytes()).hexdigest(),
          'node': subprocess.check_output(['node', '--version'], text=True).strip(), 'messages': results}
(OUT / 'commitlint.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
