#!/usr/bin/env python3
"""Run existing provider controls in a private workspace owned by the tested UID."""
import os
from pathlib import Path
import subprocess
import tarfile

root = Path(__file__).resolve().parents[4]
source = root / 'references/Hexalith.Platform/infrastructure/keycloak-workload-binding'
jar = Path(os.environ['FIXTURE_PROVIDER_JAR'])
assert jar.is_file()
caller = 1001
args = ['sudo', '-n', 'setpriv', '--reuid=' + str(caller), '--regid=' + str(caller), '--groups=' + str(Path('/var/run/docker.sock').stat().st_gid), '--',
        'env', '-u', 'TMPDIR', '-u', 'TMP', '-u', 'TEMP', 'bash', '-c', Path('/home/administrator/.local/bin/run-with-temp').read_text(), 'run-with-temp', 'bash', '-c',
        'set -euo pipefail\ntar -xf - -C "$TMPDIR"\ncd "$TMPDIR/fixture"\npython3 -B -m unittest discover -s "$TMPDIR/fixture" -p "test_*.py" -v']
with (Path(__file__).parent / 'platform-private-non1000-tests.log').open('wb') as output:
    child = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=output, stderr=subprocess.STDOUT)
    try:
        with tarfile.open(fileobj=child.stdin, mode='w|') as archive:
            for file in source.glob('*.py'):
                archive.add(file, arcname='fixture/' + file.name)
            archive.add(jar, arcname='fixture/target/' + jar.name)
    finally:
        try: child.stdin.close()
        except BrokenPipeError: pass
        code = child.wait(timeout=600)
print('Private non-1000 provider suite exit', code)
raise SystemExit(code)
