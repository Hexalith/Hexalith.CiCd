"""Read only public/grant metadata; never fetch credential values."""
from datetime import datetime, timezone
import json, os, subprocess
from pathlib import Path
here=Path(__file__).resolve().parent
assert not any(key in os.environ for key in ('GH_TOKEN','GITHUB_TOKEN'))
env=dict(os.environ,GH_CONFIG_DIR='/home/administrator/.config/gh',GH_PROMPT_DISABLED='1')
report={'recorded_at':datetime.now(timezone.utc).isoformat(),'profile':env['GH_CONFIG_DIR'],'token_overrides_present':False,'requests':[]}
def get(endpoint):
 result=subprocess.run(['gh','api',endpoint],env=env,capture_output=True,text=True,timeout=60)
 row={'endpoint':endpoint,'exit':result.returncode}
 report['requests'].append(row)
 if result.returncode:row['error']=result.stderr;return None
 return json.loads(result.stdout)
user=get('user');assert user['login']=='jpiquot'
repo=get('repos/Hexalith/Hexalith.McpCli');assert repo['id']==1379417482
report['repository']={key:repo[key] for key in ('id','full_name','default_branch')}
report['repository_secrets']=get('repos/Hexalith/Hexalith.McpCli/actions/secrets?per_page=100')
report['environments']=get('repos/Hexalith/Hexalith.McpCli/environments?per_page=100')
report['environment_secrets']={}
for item in report['environments']['environments']:
 report['environment_secrets'][item['name']]=get('repos/Hexalith/Hexalith.McpCli/environments/'+item['name']+'/secrets?per_page=100')
report['organization_selected_grants']={}
for scope in ('actions','dependabot'):
 inventory=get('orgs/Hexalith/'+scope+'/secrets?per_page=100')
 assert inventory['total_count']<100
 grants=[]
 for secret in inventory['secrets']:
  if secret['visibility']=='all':
   grants.append({'name':secret['name'],'visibility':'all','module_has_access':True})
  elif secret['visibility']=='selected':
   selected=get('orgs/Hexalith/'+scope+'/secrets/'+secret['name']+'/repositories?per_page=100')
   assert selected['total_count']<100
   if any(item['id']==repo['id'] for item in selected['repositories']):
    grants.append({'name':secret['name'],'visibility':'selected','module_has_access':True,'repository_ids':[item['id'] for item in selected['repositories']]})
 report['organization_selected_grants'][scope]=grants
assert all(item['exit']==0 for item in report['requests'])
(here/'legacy-access-inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'repository_secrets':[item['name'] for item in report['repository_secrets']['secrets']], 'environment_secrets':{key:[item['name'] for item in value['secrets']] for key,value in report['environment_secrets'].items()},'organization_grants':report['organization_selected_grants']},indent=2))
