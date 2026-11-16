"""Validate exact publication messages with released tools and owning policies."""
from pathlib import Path
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile

OUTPUT = Path(__file__).resolve().parent
ROOT = Path('/home/administrator/projects/hexalith/cicd-publish-story-14')
RELEASE = 'fdda17c0a4538b0f7c99f813c20ca24b49006530'
scratch = Path(os.environ['TMPDIR'])
released = scratch / 'released'
released.mkdir()
archive = subprocess.check_output([
    'git', 'archive', RELEASE, 'Github/lib', 'Github/guard', 'schemas',
], cwd=ROOT / 'references/Hexalith.Builds')
with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
    contents.extractall(released, filter='data')
sys.path.insert(0, str(released / 'Github/lib'))
from guard_tools import Tools

directory = scratch / 'tools'
directory.mkdir()
tools = Tools(directory)
messages = {
    'Hexalith.Builds': 'feat(ci): enforce project test floors and skipped tests\n',
    'Hexalith.Agents': 'build(cicd): prepare Agents product checks for shared pipelines\n',
    'Hexalith.CiCd': 'build(cicd): publish Agents preparation and shared test policy\n',
}
results = {'releasedValidatorCommit': RELEASE, 'messages': {}}
for name, message in messages.items():
    message_file = scratch / (name + '-message.txt')
    message_file.write_text(message)
    tools.lint_message(message_file.read_text(), name)
    owning_config = ROOT / 'references' / name / 'commitlint.config.mjs'
    record = {'sharedReleasedPolicy': 'passed'}
    if owning_config.is_file():
        destination = directory / (name + '-commitlint.config.mjs')
        destination.write_bytes(owning_config.read_bytes())
        if name == 'Hexalith.Builds':
            for relative in ['Github/guard/commitlint_bridge.mjs', 'Github/lib/commit_policy.py']:
                target = directory / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(released / relative, target)
        result = tools._process([
            'node', str(directory / 'node_modules/@commitlint/cli/cli.js'),
            '--config', str(destination), '--cwd', str(owning_config.parent),
            '--edit', str(message_file), '--verbose', '--color=false',
        ], name + ' owning commit policy')
        (OUTPUT / (name + '-commitlint.log')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(name + ': owning commit policy failed; inspect the saved log')
        record.update(owningPolicy='passed', configSha256=hashlib.sha256(owning_config.read_bytes()).hexdigest())
    shutil.copy2(message_file, OUTPUT / message_file.name)
    record.update(message=message, sha256=hashlib.sha256(message.encode()).hexdigest())
    results['messages'][name] = record
    print(name + ': exact message validated', flush=True)
(OUTPUT / 'message-validation.json').write_text(json.dumps(results, indent=2) + '\n')
