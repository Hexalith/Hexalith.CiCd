"""Read-only scope qualification of the uncommitted Projects candidate."""
from pathlib import Path
import json
import os
import stat
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(root / 'tools'))
from scan import Detector
from scan_discovery import Discovery

class Source:
    def __init__(self, directory):
        self.directory = directory
    def blob(self, revision, path):
        source = self.directory / path
        return os.readlink(source).encode() if source.is_symlink() else source.read_bytes()
    def items(self, revision):
        result = {}
        data = subprocess.check_output(['git', '-C', str(self.directory), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'])
        for raw in data.split(b'\0'):
            if not raw:
                continue
            name = os.fsdecode(raw)
            path = self.directory / name
            if path.is_symlink():
                result[name] = ('120000', 'blob', '')
            elif path.is_file():
                result[name] = ('100755' if path.stat().st_mode & stat.S_IXUSR else '100644', 'blob', '')
            elif path.is_dir():
                result[name] = ('160000', 'commit', '')
        return result

with tempfile.TemporaryDirectory(prefix='projects-candidate-scope-') as temporary:
    detector = Detector(Source(root), 'working-candidate', Path(temporary))
    files, errors = Discovery(Source(root / 'references/Hexalith.Projects'), 'working-candidate',
                             javascript_parser=detector.javascript).discover()
    print(json.dumps({'result':'fail' if errors else 'pass', 'files':sorted(files), 'errors':errors}, indent=2))
    sys.exit(bool(errors))
