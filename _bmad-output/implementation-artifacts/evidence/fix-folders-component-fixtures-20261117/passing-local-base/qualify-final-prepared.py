#!/usr/bin/env python3
"""Finish exact-input qualification using the retained prepared provider/workspace."""
from pathlib import Path
import hashlib,json,os,signal,subprocess
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
MODULE=Path('/tmp/hexalith-job.vFOGqWVb/Hexalith.Folders')
REPORT={'scope':'local final candidate; no protected enrollment or publication','commands':[]}
COORDINATOR=json.loads((OUT/'retained-workspace-coordinator.json').read_text())['pid']

def save(): (OUT/'final-qualification.json').write_text(json.dumps(REPORT,indent=2)+'\n')
def job(label,args,timeout=1200):
    print(label+' running',flush=True)
    with (OUT/(label+'.log')).open('wb') as output:
        child=subprocess.Popen(args,cwd=MODULE,env=dict(os.environ,CI='true',DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER='1',MSBUILDDISABLENODEREUSE='1'),stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
        try: code=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL); code=child.wait()
        finally:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
    REPORT['commands'].append({'label':label,'argv':args,'exitCode':code});save();print(label+' exit '+str(code),flush=True);return code
try:
    project='tests/Hexalith.Folders.Server.Tests/Hexalith.Folders.Server.Tests.csproj'
    flags=['-p:NuGetAudit=true','-p:NuGetAuditMode=all','-p:NuGetAuditLevel=low','-warnaserror','-m:1','-p:UseSharedCompilation=false','-nr:false']
    code=job('final-release-build',['dotnet','build',project,'-c','Release','--disable-build-servers','-p:UseHexalithProjectReferences=false','-p:UseNuGetDeps=true',*flags])
    if not code:
        for relative,name in [('bin/Release/net11.0/sdk-binding.project.assets.json','release-bound-assets.json'),('bin/Release/net11.0/Hexalith.Folders.Server.Tests.deps.json','release-server.deps.json')]:
            (OUT/name).write_bytes((MODULE/'tests/Hexalith.Folders.Server.Tests'/relative).read_bytes())
        code=job('complete-server',['pwsh','-NoProfile','-File','tests/tools/run-complete-project-tests.ps1','-ProjectName','Hexalith.Folders.Server.Tests','-ComponentEvidenceFile',str(OUT/'complete-server-results.xml')])
    REPORT['releaseExitCode']=code
    source=job('final-debug-source-build',['dotnet','build',project,'-c','Debug','--disable-build-servers','-p:UseHexalithProjectReferences=true','-p:UseNuGetDeps=false',*flags])
    REPORT['sourceBuildExitCode']=source;REPORT['exitCode']=code or source;save()
finally:
    os.kill(COORDINATOR,signal.SIGCONT)
    print('Resumed retained coordinator for source fixture and cleanup.',flush=True)
raise SystemExit(REPORT['exitCode'])
