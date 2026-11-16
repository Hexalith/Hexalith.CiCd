#!/usr/bin/env python3
"""Run complete changed/helper classes natively; this is source qualification only."""
import json
import inspect
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

def install_runtime(root):
    import hashlib
    import io
    import json
    from pathlib import PurePosixPath
    from urllib.request import urlopen
    import zipfile
    metadata_url = 'https://builds.dotnet.microsoft.com/dotnet/release-metadata/11.0/releases.json'
    with urlopen(metadata_url, timeout=60) as response:
        metadata = json.load(response)
    release = next(item for item in metadata['releases'] if item['release-version'] == '11.0.0')
    archive = next(item for item in release['runtime']['files'] if item['name'] == 'dotnet-runtime-win-x64.zip' and item['rid'] == 'win-x64')
    assert archive['url'] == 'https://builds.dotnet.microsoft.com/dotnet/Runtime/11.0.0/dotnet-runtime-11.0.0-win-x64.zip'
    with urlopen(archive['url'], timeout=120) as response:
        payload = response.read(128 * 1024 * 1024)
    assert hashlib.sha512(payload).hexdigest().lower() == archive['hash'].lower()
    with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
        for item in bundle.infolist():
            path = PurePosixPath(item.filename)
            assert not path.is_absolute() and '..' not in path.parts and ':' not in item.filename
            assert item.external_attr >> 16 & 0o170000 != 0o120000
        bundle.extractall(root / 'runtime')
    print(json.dumps({'sourceQualificationRuntime': '11.0.0', 'metadata': metadata_url, 'archive': archive, 'bytes': len(payload)}), flush=True)


builds = Path(__file__).resolve().parents[5] / 'references/Hexalith.Builds'
conversations = builds.parent / 'Hexalith.Conversations'
source = Path(sys.argv[1]).resolve()
log = Path(sys.argv[2]).resolve()
if not Path('/mnt/c/Python314/python.exe').is_file():
    raise SystemExit('Native Windows Python prerequisite unavailable; source qualification incomplete')
# This nested wrapper owns and cleans its own NTFS scratch. Build artifacts stay
# private and cannot be treated as released producer/module acceptance evidence.
script = r'''
import os,pathlib,subprocess,sys
private=pathlib.Path(__file__).parent
root=private/'checkout'
temporary=private/'temp'
temporary.mkdir()
os.environ['TEMP']=str(temporary)
os.environ['TMP']=str(temporary)
os.environ['PATH']=str(private/'runtime')+r';C:\Python314;C:\Program Files\Git\cmd;'+os.environ['PATH']
os.environ['DOTNET_ROOT']=str(private/'runtime')
subprocess.run(['git','init','--quiet',str(root)],check=True)
commit=(private/'historical-commit.bin').read_bytes()
actual=subprocess.check_output(['git','-C',str(root),'hash-object','-t','commit','-w','--stdin'],input=commit).decode().strip()
assert actual == '79f4b126ca66d419a584855936ce56a1266cce67'
print('Imported the authentic historical commit object required by the retained signed-root assertion: '+actual)
sys.path.insert(0,str(private/'support/Github/lib'))
import module_preparation
reported=subprocess.check_output(['git','-C',str(root),'rev-parse','--show-toplevel'],text=True).strip()
assert module_preparation._same_git_root(root,reported)
other=root/'different-root'
other.mkdir()
assert not module_preparation._same_git_root(root,str(other))
print('Native Git forward-slash root normalizes to the same physical Windows root; a different root refuses.')
subprocess.run([str(private/'runtime/dotnet.exe'),str(root/'built/Hexalith.Conversations.TestSupport.Tests.dll'),'-automated','sync','-failSkips','-noAutoReporters'],cwd=root,check=True,timeout=180)
print('SOURCE QUALIFICATION ONLY: the full unfiltered TestSupport DLL executed on native Windows; full module Windows acceptance remains pending.')
'''
bootstrap = 'import pathlib,shutil,os,subprocess\n' + inspect.getsource(install_runtime) + '\nroot=pathlib.Path(os.environ["TMPDIR"])\ninstall_runtime(root)\nshutil.copytree(' + repr(str(source)) + ',root/"checkout/built")\nshutil.copytree(' + repr(str(builds / 'Github/lib')) + ',root/"support/Github/lib")\nshutil.copytree(' + repr(str(builds / 'Github/prepare-module-build')) + ',root/"support/Github/prepare-module-build")\n'
for name in ['Hexalith.Conversations.slnx', 'tests/Hexalith.Conversations.TestSupport.Tests/BoundaryAssertionsTests.cs', 'docs/release-evidence/story-10.1-final-record-v2.json', 'docs/release-evidence/success-metric-report-and-attestation-v1.json']:
    bootstrap += 'target=root/"checkout"/'+repr(name)+'\ntarget.parent.mkdir(parents=True,exist_ok=True)\nshutil.copy2('+repr(str(conversations/name))+',target)\n'
bootstrap += '(root/"historical-commit.bin").write_bytes(subprocess.check_output(["git","cat-file","commit","79f4b126ca66d419a584855936ce56a1266cce67"],cwd='+repr(str(conversations))+'))\n(root/"run.py").write_text(' + repr(script) + ')\ntarget=subprocess.check_output(["wslpath","-w",str(root/"run.py")],text=True).strip()\nsubprocess.run(["/mnt/c/Python314/python.exe",target],check=True)'

environment = os.environ.copy()
environment['TMPDIR']='/mnt/c/Users/Public'
with log.open('w') as output:
    result = subprocess.run(['run-with-temp', sys.executable, '-c', bootstrap], env=environment, stdout=output, stderr=subprocess.STDOUT, check=False, timeout=240)
raise SystemExit(result.returncode)
