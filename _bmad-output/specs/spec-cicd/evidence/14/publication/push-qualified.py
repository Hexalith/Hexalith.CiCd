"""Push a qualified exact commit by normal fast-forward with the intended profile."""
from pathlib import Path
import argparse
import json
import os
import subprocess

OUTPUT = Path(__file__).resolve().parent
ROOT = Path('/home/administrator/projects/hexalith/cicd-publish-story-14')
parser = argparse.ArgumentParser()
parser.add_argument('repository', choices=['Hexalith.Builds', 'Hexalith.Agents', 'Hexalith.CiCd'])
args = parser.parse_args()
name = args.repository
integration = json.loads((OUTPUT / 'integration.json').read_text())
directory = ROOT if name == 'Hexalith.CiCd' else ROOT / 'references' / name
profile = 'gh-module-agent' if name == 'Hexalith.Agents' else 'gh-cicd-agent'
environment = {**os.environ, 'GH_CONFIG_DIR': '/home/administrator/.config/' + profile,
               'GH_PROMPT_DISABLED': '1', 'GIT_TERMINAL_PROMPT': '0'}
assert not any(os.environ.get(key) for key in ['GH_TOKEN', 'GITHUB_TOKEN'])
if profile == 'gh-module-agent':
    environment['GH_TOKEN'] = Path('/home/administrator/.config/gh-module-agent/token').read_text().strip()


def git(*arguments):
    return subprocess.check_output(['git', '-c', 'submodule.recurse=false', *arguments],
                                   cwd=directory, env=environment, text=True).strip()


component = {'Hexalith.Builds': 'builds', 'Hexalith.Agents': 'agents', 'Hexalith.CiCd': 'root'}[name]
proof_file = 'root-publication-qualification.json' if name == 'Hexalith.CiCd' else component + '-qualification.json'
qualification = json.loads((OUTPUT / proof_file).read_text())
head = git('rev-parse', 'HEAD')
assert qualification['result'] == 'pass' and qualification['head'] == head
assert not git('status', '--porcelain', '--ignore-submodules=all')
for dependency in ['Hexalith.Builds', 'Hexalith.Agents'] if name == 'Hexalith.CiCd' else []:
    dependency_file = ('builds-audit-fix-push.json' if dependency == 'Hexalith.Builds'
                       and (OUTPUT / 'builds-audit-fix-push.json').exists() else dependency + '-push.json')
    previous = json.loads((OUTPUT / dependency_file).read_text())
    assert previous['confirmed']
    assert git('rev-parse', 'HEAD:references/' + dependency) == previous['head']
record = {'repository': name, 'profile': environment['GH_CONFIG_DIR'], 'head': head,
          'base': integration['repositories'][name]['base'], 'attempted': False, 'confirmed': False,
          'qualificationScope': qualification.get('scope', 'complete component qualification')}
path = OUTPUT / (name + '-push.json')
assert not path.exists(), 'Inspect an existing/uncertain publication before trying again.'
subprocess.run(['git', '-c', 'submodule.recurse=false', 'fetch', '--no-recurse-submodules',
                'origin', 'main'], cwd=directory, env=environment, check=True,
               stdout=subprocess.DEVNULL)
record['prePushMain'] = git('rev-parse', 'origin/main')
path.write_text(json.dumps(record, indent=2) + '\n')
assert record['prePushMain'] == record['base'], 'main advanced; reintegrate and qualify before pushing'
record['attempted'] = True
path.write_text(json.dumps(record, indent=2) + '\n')
result = subprocess.run(['git', '-c', 'submodule.recurse=false', 'push', '--porcelain',
                         'origin', head + ':refs/heads/main'], cwd=directory,
                        env=environment, text=True, capture_output=True)
(OUTPUT / (name + '-push.log')).write_text(result.stdout + result.stderr)
record.update(exitCode=result.returncode, diagnostics=result.stdout + result.stderr)
remote = git('ls-remote', '--heads', 'origin', 'refs/heads/main').split()[0]
record['readbackMain'] = remote
record['confirmed'] = remote == head
if not record['confirmed'] and result.returncode == 0:
    subprocess.run(['git', '-c', 'submodule.recurse=false', 'fetch', '--no-recurse-submodules',
                    'origin', 'main'], cwd=directory, env=environment, check=True)
    record['confirmed'] = subprocess.run(['git', 'merge-base', '--is-ancestor', head, 'origin/main'],
                                        cwd=directory).returncode == 0
path.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
raise SystemExit(0 if record['confirmed'] else result.returncode or 1)
