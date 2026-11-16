#!/usr/bin/env python3
"""Recheck the delivered correction without changing shared repositories."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
OWNER = Path('/home/administrator/projects/hexalith/cicd')
SOURCE = '4db3776e444f0ec6e5f97d1ff089a0d83f990082'


def command(args, cwd, **kwargs):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, **kwargs)


def main():
    result = {'recorded_at': datetime.now(timezone.utc).isoformat(),
              'owner_source': SOURCE, 'checks': [], 'scope': 'local behavioral qualification only'}
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith('GIT_') or name in {'GH_TOKEN', 'GITHUB_TOKEN', 'MODULE_TOKEN', 'CICD_TOKEN'}:
            environment.pop(name)
    environment.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1',
                       GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')
    with tempfile.TemporaryDirectory(prefix='g6-recheck-', dir=os.environ['TMPDIR']) as directory:
        root = Path(directory) / 'owner'
        command(['git', '-c', 'submodule.recurse=false', 'clone', '--shared', '--no-checkout',
                 '--no-recurse-submodules', str(OWNER), str(root)], OWNER, env=environment)
        command(['git', 'sparse-checkout', 'init', '--no-cone'], root, env=environment)
        command(['git', 'sparse-checkout', 'set', '/tools/', '/.github/', '/docs/proposals/',
                 '/builds-version'], root, env=environment)
        command(['git', '-c', 'submodule.recurse=false', 'checkout', '--detach', SOURCE], root, env=environment)
        builds = root / 'references/Hexalith.Builds'
        builds.mkdir(parents=True)
        command(['git', 'init', '--bare', '--quiet', str(builds)], root, env=environment)
        command(['git', '-C', str(builds), 'fetch', '--quiet', '--no-recurse-submodules', '--no-tags',
                 '--depth=1', str(OWNER / 'references/Hexalith.Builds'),
                 'refs/tags/v5.1.0:refs/tags/v5.1.0'], root, env=environment)
        result['fixture_release'] = command(['git', '-C', str(builds), 'rev-parse',
                                            'refs/tags/v5.1.0^{commit}'], root, env=environment).stdout.decode().strip()
        for suite in ('test_prepare_g6_catalog.py', 'test_deliver_g6_catalog.py', 'test_delivery_workflow.py'):
            args = ['uv', 'run', '--locked', '--script', '--python', '3.12', 'tools/tests/' + suite]
            log = HERE / (suite + '.log')
            with log.open('xb') as stream:
                check = subprocess.run(args, cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT)
            result['checks'].append({'command': args, 'exit_code': check.returncode,
                                     'log': log.name, 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
            print(suite, check.returncode, flush=True)
        result['status'] = 'passed' if all(x['exit_code'] == 0 for x in result['checks']) else 'failed'
    (HERE / 'local-qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
