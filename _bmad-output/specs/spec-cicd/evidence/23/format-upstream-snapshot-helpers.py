"""Format private helper copies, verify content preservation, then apply only whitespace."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

source = Path('/home/administrator/projects/hexalith/eventstore-story-23-snapshot-recovered')
scratch = Path(os.environ['TMPDIR'])
root = scratch / 'format'
root.mkdir()
names = ['src/Hexalith.EventStore.Client/Handlers/FoldedSnapshotProcessor.cs',
         'src/Hexalith.EventStore.Server/Configuration/FoldedSnapshotActorConfigurationExtensions.cs']
# The standalone formatter treats the severity suffix as part of this whitespace
# option. Supply its supported spelling for the repository's unchanged Allman intent.
(root / '.editorconfig').write_text((source / '.editorconfig').read_text().replace(
    'csharp_new_line_before_open_brace = all:warning', 'csharp_new_line_before_open_brace = all'))
for name in names:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((source / name).read_bytes())
environment = {**os.environ, 'DOTNET_CLI_HOME': str(scratch / 'dotnet-home'), 'HOME': str(scratch / 'home'),
    'XDG_CONFIG_HOME': str(scratch / 'config'), 'XDG_DATA_HOME': str(scratch / 'data'), 'XDG_CACHE_HOME': str(scratch / 'cache')}
command = ['dotnet', 'format', 'whitespace', str(root), '--folder', '--include', *names, '--verbosity', 'quiet']
subprocess.run(command, cwd=root, env=environment, timeout=120, check=True)
facts = []
for name in names:
    before, after = (source / name).read_text(), (root / name).read_text()
    assert re.sub(r'\s+', '', before) == re.sub(r'\s+', '', after)
    assert re.findall(r'"(?:\\.|[^"\\])*"', before) == re.findall(r'"(?:\\.|[^"\\])*"', after)
    (source / name).write_text(after)
    facts.append({'path': name, 'whitespaceOnly': True, 'literalsUnchanged': True,
                  'sha256': hashlib.sha256(after.encode()).hexdigest()})
print(json.dumps({'command': command, 'results': facts}, indent=2))
