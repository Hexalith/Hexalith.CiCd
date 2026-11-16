#!/usr/bin/env python3
"""Record local source inputs and unchanged owned bytes/modes/gitlinks."""
from pathlib import Path
import hashlib
import json
import stat
import subprocess

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[4] / 'references/Hexalith.Parties'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


paths = ['.github/workflows','.github/hexalith-ci.json','.github/dependabot.yml',
         '.gitmodules','AGENTS.md','CLAUDE.md','.github/copilot-instructions.md',
         '.claude/settings.json']
owned = []
for entry in git('ls-tree','-rz','HEAD','--',*paths).split(b'\0'):
    if not entry:
        continue
    metadata, rawpath = entry.split(b'\t',1)
    mode, kind, objectid = metadata.decode().split()
    path = rawpath.decode()
    expected = git('cat-file','blob',objectid)
    actual = (ROOT/path).read_bytes()
    actual_mode = '100755' if (ROOT/path).stat().st_mode & stat.S_IXUSR else '100644'
    owned.append({'path':path,'mode':mode,'working_mode':actual_mode,
                  'baseline_sha256':digest(expected),'working_sha256':digest(actual),
                  'unchanged':expected==actual and mode==actual_mode})
patch = git('diff','--binary','HEAD')
(EVIDENCE/'current-preparation.patch').write_bytes(patch)
newfiles = []
for entry in git('ls-files','--others','--exclude-standard','-z').split(b'\0'):
    if entry:
        path = entry.decode()
        file = ROOT/path
        newfiles.append({'path':path,'sha256':digest(file.read_bytes()),
                         'mode':oct(file.stat().st_mode & 0o777)})
base_pin = git('ls-tree','HEAD','references/Hexalith.Builds').decode().strip()
index_pin = git('ls-files','--stage','references/Hexalith.Builds').decode().strip()
result = {'base':git('rev-parse','HEAD').decode().strip(),
          'patch_sha256':digest(patch),'untracked_inputs':newfiles,
          'owned_files':owned,'owned_files_unchanged':all(x['unchanged'] for x in owned),
          'owned_diff':git('diff','--name-only','HEAD','--',*paths,'references/Hexalith.Builds').decode(),
          'builds_base_gitlink':base_pin,'builds_index_gitlink':index_pin,
          'nested_submodule_status':git('submodule','status').decode(),
          'remote_mutations':False,'pushes':False,
          'accidental_git_network_read_attempt':'Interrupted direct EventStore initial clone from submodule update --init --no-fetch (exit 130); no remote mutation, no completed initialization.'}
(EVIDENCE/'current-preparation-state.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['owned_files_unchanged'] and not result['owned_diff']
assert base_pin.split()[0] == index_pin.split()[0] and base_pin.split()[2] == index_pin.split()[1]
assert all(line.startswith('-') for line in result['nested_submodule_status'].splitlines())
print(json.dumps({'patch_sha256':result['patch_sha256'],'owned_file_count':len(owned),'owned_unchanged':True,'nested_initialized':False}))
