"""Verify final publication inputs and the suites affected by concurrent upstream changes."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess

out = Path(__file__).resolve().parent
root = Path('/home/administrator/projects/hexalith/cicd-publish-story-14')
scratch = Path(os.environ['TMPDIR'])
checkout = scratch / 'CiCd'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-recurse-submodules', str(root), str(checkout)], check=True)
subprocess.run(['git', 'checkout', '--quiet', '--detach', head], cwd=checkout, check=True)
builds = checkout / 'references/Hexalith.Builds'
subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-recurse-submodules',
                str(root / 'references/Hexalith.Builds'), str(builds)], check=True)
builds_head = subprocess.check_output(['git', 'rev-parse', 'HEAD:references/Hexalith.Builds'], cwd=checkout, text=True).strip()
subprocess.run(['git', 'checkout', '--quiet', '--detach', builds_head], cwd=builds, check=True)
env = {**os.environ}
assert env.get('GH_CONFIG_DIR') == '/home/administrator/.config/gh-cicd-agent'
assert not any(env.get(k) for k in ('GH_TOKEN', 'GITHUB_TOKEN'))
env['GH_TOKEN'] = subprocess.check_output(['gh', 'auth', 'token'], env=env, text=True).strip()
report = {'head': head, 'builds': builds_head, 'commands': [],
          'scope': 'final publication: render, all core global checks, Projects delivery, renderer and validator suites',
          'broaderRun': 'root-qualification.json; independent result retained without claiming a complete global pass'}
runner = scratch / 'core-checks.py'
runner.write_text('''# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path.cwd() / "tools"))
import check_global as c
root = Path.cwd()
c.check_committed_inputs(root)
print("global committed render inputs: passed", flush=True)
c.check_committed_render(root)
print("global committed render: passed", flush=True)
c.check_bootstrap(root)
print("global immutable delivery bootstrap: passed", flush=True)
with c.selected_contract(root) as contract:
    c.check_render(root, contract)
    print("global render reproducibility: passed", flush=True)
    c.check_documents(root, c.renderer.registry(root), contract)
    print("global schemas and caller interfaces: passed", flush=True)
    c.check_release(contract)
    print("global acceptable Builds publication: passed", flush=True)
    c.lint_workflows(root, contract)
    print("global workflow lints: passed", flush=True)
''')
runner.with_suffix('.py.lock').write_bytes((checkout / 'tools/check_global.py.lock').read_bytes())


def run(label, arguments):
    private = scratch / label
    private.mkdir()
    child_env = {**env, 'TMPDIR': str(private), 'TMP': str(private), 'TEMP': str(private)}
    with (out / (label + '.log')).open('w') as log:
        result = subprocess.run(arguments, cwd=checkout, env=child_env, stdout=log, stderr=subprocess.STDOUT)
    record = {'label': label, 'command': arguments, 'exitCode': result.returncode}
    print(label + ': ' + str(result.returncode), flush=True)
    return record


commands = [
    ('root-final-render', ['uv', 'run', '--no-cache', '--locked', '--script', 'tools/render.py', '--check']),
    ('root-final-core', ['uv', 'run', '--no-cache', '--locked', '--script', str(runner)]),
    *[(name.removesuffix('.py') + '-final', ['uv', 'run', '--no-cache', '--locked', '--script', 'tools/tests/' + name])
      for name in ('test_deliver_g6_catalog.py', 'test_render.py', 'test_validate.py')],
]
with ThreadPoolExecutor(max_workers=3) as executor:
    for future in as_completed([executor.submit(run, label, args) for label, args in commands]):
        report['commands'].append(future.result())
        (out / 'root-publication-qualification.json').write_text(json.dumps(report, indent=2) + '\n')
report['result'] = 'pass' if all(c['exitCode'] == 0 for c in report['commands']) else 'fail'
(out / 'root-publication-qualification.json').write_text(json.dumps(report, indent=2) + '\n')
raise SystemExit(0 if report['result'] == 'pass' else 1)
