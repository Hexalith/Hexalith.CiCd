"""Run complete CiCd publication gates on the committed candidate in private scratch."""
from pathlib import Path
import json
import os
import subprocess

OUTPUT = Path(__file__).resolve().parent
ROOT = Path('/home/administrator/projects/hexalith/cicd-publish-story-14')
scratch = Path(os.environ['TMPDIR'])
checkout = scratch / 'CiCd'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-recurse-submodules', str(ROOT), str(checkout)], check=True)
subprocess.run(['git', 'checkout', '--quiet', '--detach', head], cwd=checkout, check=True)
builds = checkout / 'references/Hexalith.Builds'
subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-recurse-submodules',
                str(ROOT / 'references/Hexalith.Builds'), str(builds)], check=True)
builds_head = subprocess.check_output(['git', 'rev-parse', 'HEAD:references/Hexalith.Builds'], cwd=checkout, text=True).strip()
subprocess.run(['git', 'checkout', '--quiet', '--detach', builds_head], cwd=builds, check=True)
environment = {**os.environ}
assert environment.get('GH_CONFIG_DIR') == '/home/administrator/.config/gh-cicd-agent'
assert not any(environment.get(key) for key in ['GH_TOKEN', 'GITHUB_TOKEN'])
credential = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True,
                             env=environment, check=True).stdout.strip()
assert credential
environment['GH_TOKEN'] = credential
report = {'head': head, 'commands': [], 'credentialSource': 'configured CiCd-agent profile; read operations only'}
for label, arguments in [
    ('root-render', ['uv', 'run', '--no-cache', '--locked', '--script', 'tools/render.py', '--check']),
    ('root-global', ['uv', 'run', '--no-cache', '--locked', '--script', 'tools/check_global.py']),
]:
    with (OUTPUT / (label + '.log')).open('w') as log:
        result = subprocess.run(arguments, cwd=checkout, env=environment,
                                stdout=log, stderr=subprocess.STDOUT)
    report['commands'].append({'label': label, 'exitCode': result.returncode})
    (OUTPUT / 'root-qualification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(label + ': ' + str(result.returncode), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
report['result'] = 'pass'
(OUTPUT / 'root-qualification.json').write_text(json.dumps(report, indent=2) + '\n')
