"""Read and retain exact-source hosted metadata, receipts, archives and job logs."""
import argparse,hashlib,json,os,re,subprocess,zipfile
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('operation',choices=('observe','artifacts','joblogs'));p.add_argument('--repo',required=True,choices=('Hexalith.CiCd','Hexalith.Projects'));p.add_argument('--run',required=True,type=int);p.add_argument('--source',required=True);p.add_argument('--artifact-prefix');p.add_argument('--job',type=int);a=p.parse_args();assert a.run>0 and re.fullmatch('[0-9a-f]{40}',a.source)
root=Path(__file__).parent;env=os.environ|{'GH_CONFIG_DIR':'/home/administrator/.config/gh-cicd-agent'};prefix='repos/Hexalith/'+a.repo;stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
def api(path):return json.loads(subprocess.check_output(['gh','api',path],env=env,stderr=subprocess.PIPE,timeout=60))
def pages(path,field):
 rows=[];total=None
 for page in range(1,21):
  d=api(path+('?' if '?' not in path else '&')+f'per_page=100&page={page}');total=d['total_count'];items=d[field];rows+=items
  if len(items)<100:break
 assert total==len(rows),'Incomplete hosted inventory'
 return rows
run=api(prefix+'/actions/runs/'+str(a.run));assert run['head_sha']==a.source,'Unexpected hosted source';jobs=pages(prefix+'/actions/runs/'+str(a.run)+'/jobs','jobs');label=a.repo+'-'+str(a.run)
observation={'observed_at':datetime.now(timezone.utc).isoformat(),'run':run,'jobs':jobs};(root/(label+'-observation-'+stamp+'.json')).write_text(json.dumps(observation,indent=2)+'\n')
if a.operation=='observe':
 print(json.dumps({'run':a.run,'source':a.source,'status':run['status'],'conclusion':run['conclusion'],'jobs':[{'id':j['id'],'name':j['name'],'status':j['status'],'conclusion':j['conclusion'],'active':[s['name'] for s in j['steps'] if s['status']=='in_progress'],'failed':[s['name'] for s in j['steps'] if s.get('conclusion')=='failure']} for j in jobs]},indent=2));raise SystemExit(0)
if a.operation=='joblogs':
 assert a.job and any(j['id']==a.job for j in jobs)
 file=root/(label+'-job-'+str(a.job)+'.log')
 with file.open('wb') as stream:r=subprocess.run(['gh','api',prefix+'/actions/jobs/'+str(a.job)+'/logs'],env=env,stdout=stream,stderr=subprocess.PIPE,timeout=300)
 (root/(file.name+'.receipt.json')).write_text(json.dumps({'job':a.job,'run':a.run,'source':a.source,'exit':r.returncode,'stderr':r.stderr.decode(),'sha256':hashlib.file_digest(file.open('rb'),'sha256').hexdigest()},indent=2)+'\n');print(file);raise SystemExit(r.returncode)
artifacts=pages(prefix+'/actions/runs/'+str(a.run)+'/artifacts','artifacts');(root/(label+'-artifacts.json')).write_text(json.dumps(artifacts,indent=2)+'\n');selected=[x for x in artifacts if not a.artifact_prefix or x['name'].startswith(a.artifact_prefix)];assert selected,'Expected hosted artifact missing'
for artifact in selected:
 assert not artifact['expired'];zip_path=root/(label+'-artifact-'+str(artifact['id'])+'.zip')
 with zip_path.open('wb') as stream:r=subprocess.run(['gh','api',prefix+'/actions/artifacts/'+str(artifact['id'])+'/zip'],env=env,stdout=stream,stderr=subprocess.PIPE,timeout=600)
 receipt={'artifact':artifact,'run':a.run,'source':a.source,'exit':r.returncode,'stderr':r.stderr.decode()}
 if r.returncode:
  (root/(zip_path.name+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n');raise SystemExit(r.returncode)
 with zip_path.open('rb') as stream:receipt['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
 with zipfile.ZipFile(zip_path) as archive:
  receipt['members']=[{'name':i.filename,'bytes':i.file_size} for i in archive.infolist()]
  wanted=('g6-qualification.json','projects-g6-delivery.json','catalog-acquisition.json','projects-ci-gates-qualification.json','projects-ci-gates-delivery.json')
  for name in wanted:
   matches=[i for i in archive.infolist() if Path(i.filename).name==name and not i.is_dir()];assert len(matches)<=1,'Duplicate expected receipt'
   if matches:
    item=matches[0];assert item.file_size<=2*1024*1024;data=archive.read(item);value=json.loads(data)
    if name!='catalog-acquisition.json':assert value['owner_source']==a.source
    if name=='catalog-acquisition.json' and value.get('status')=='prepared':assert value.get('source_revision')==a.source
    out=root/(label+'-'+name);out.write_bytes(data);print(json.dumps({'receipt':str(out),'status':value.get('status'),'delivered_sha':value.get('delivered_sha'),'delivered_tree':value.get('delivered_tree'),'reason':value.get('reason')},indent=2))
 (root/(zip_path.name+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n');print('retained',zip_path,'bytes',zip_path.stat().st_size)
