"""Bounded stack sample of the running disposable seeding phase; raw trace stays private."""
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys

from performance_checkpoint import read_checkpoint

here = Path(__file__).resolve().parent
packet = here / sys.argv[1]
assert packet.parent == here
record = json.loads((packet / 'result.json').read_text())
scratch = Path(record['privateScratchPath'])
before = read_checkpoint(scratch)
assert before['phase'] == 'Seeding' and before['status'] == 'incomplete'
worker = next(row for row in record['containers'] if row['kind'] == 'worker')
labels = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .Config.Labels}}', worker['id']]))
assert labels['hexalith.local-qualification'] == record['nonce']
code = r'''
import json,os,pathlib,subprocess
root=pathlib.Path('/work/s23');private=root/'runner/diagnostics-tools';private.mkdir(mode=0o700)
environment=dict(os.environ,HOME=str(root/'home'),TMPDIR=str(root),TMP=str(root),TEMP=str(root),
                 DOTNET_ROLL_FORWARD='LatestMajor',NUGET_PACKAGES=str(root/'home/.nuget/packages'))
targets=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  if pathlib.Path(os.readlink(p/'exe')).name=='Hexalith.Tenants.IntegrationTests':targets.append(p.name)
 except OSError:pass
assert len(targets)==1
log=private/'private.log'
with log.open('wb') as stream:
 subprocess.run(['dotnet','tool','install','dotnet-trace','--version','10.0.750501','--tool-path',str(private)],
                env=environment,cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=180,check=True)
 trace=private/'seeding.nettrace'
 subprocess.run([str(private/'dotnet-trace'),'collect','--process-id',targets[0],
                 '--providers','Microsoft-DotNETCore-SampleProfiler','--duration','00:00:00:20',
                 '--output',str(trace)],env=environment,cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=60,check=True)
 result=subprocess.run([str(private/'dotnet-trace'),'report',str(trace),'topN','--number','30','--inclusive'],
                       env=environment,cwd=root,capture_output=True,text=True,timeout=30)
 print(json.dumps({'exit':result.returncode,'report':result.stdout,'rawTraceRetainedOutsideScratch':False}))
'''
process = subprocess.run(['docker','exec','--user','1000',worker['id'],'python3','-B','-c',code],
                         capture_output=True,text=True,timeout=285)
result = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'packet':packet.name,
          'source':record['source'],'before':before,'tool':'dotnet-trace/10.0.750501',
          'provider':'Microsoft-DotNETCore-SampleProfiler','sampleSeconds':20,
          'scope':'Diagnostic instrumentation during seeding; not performance acceptance',
          'exit':process.returncode,'rawTraceRetainedOutsideScratch':False}
if process.returncode == 0:
    data = json.loads(process.stdout)
    result['reportExit'] = data['exit']
    # Keep only static source/framework method lines and numeric report headers.
    lines = []
    for line in data['report'].splitlines():
        if re.search(r'\b(?:System|Microsoft|Hexalith|Dapr)\.[A-Za-z]',line):
            assert not re.search(r'https?://|zak_|eyJ|BEGIN |password|secret',line,re.I)
            lines.append(line[:1500])
        elif re.fullmatch(r'[A-Za-z0-9% ():._=-]*',line):
            lines.append(line)
    result['staticMethodReport'] = lines
else:
    result['failure'] = 'Diagnostic tool install/sample/report unavailable; private output discarded'
result['after'] = read_checkpoint(scratch)
target = here / 'performance-seeding-stack-observation-01.json'
assert not target.exists()
target.write_text(json.dumps(result,indent=2)+'\n')
target.chmod(0o600)
print(json.dumps(result,indent=2))
