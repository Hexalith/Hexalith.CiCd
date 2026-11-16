"""Retain pinned owner commitlint and workflow lint qualification."""
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/cicd');evidence=Path(__file__).parent
builds=root/'references/Hexalith.Builds'
# Export the exact current released Builds tooling into the private job workspace.
tag=(root/'builds-version').read_text().strip(); revision=subprocess.check_output(['git','-C',str(builds),'rev-parse',tag+'^{commit}']).decode().strip()
export=Path(os.environ['TMPDIR'])/'builds';export.mkdir()
archive=subprocess.Popen(['git','-C',str(builds),'archive',revision,'Github/lib','Github/guard','Tools/ci'],stdout=subprocess.PIPE)
subprocess.run(['tar','-x','-C',str(export)],stdin=archive.stdout,check=True);archive.stdout.close();assert archive.wait()==0
if '--lint-only' not in sys.argv:
 sys.path.insert(0,str(export/'Github/lib'))
 from guard_tools import Tools
 scratch=Path(os.environ['TMPDIR'])/'commitlint';scratch.mkdir()
 messages=['build(cicd): add exact-source Projects G-6 delivery','build(cicd): apply reviewed Projects G-6 catalog acquisition','build(cicd): acquire reviewed Projects G-6 catalog','docs(cicd): record Projects G-6 delivery qualification']
 with (evidence/'commitlint.log').open('w') as log:
  tools=Tools(scratch)
  subprocess.run(["git","init","--quiet",str(scratch)],env=tools.environment,check=True)
  for i,message in enumerate(messages):
   text=message+'\n'; path=Path(os.environ['TMPDIR'])/('commit-message-'+str(i));path.write_text(text)
   # lint the exact message file with the pinned normal policy.
   command=['node',str(scratch/'node_modules/@commitlint/cli/cli.js'),'--config',str(export/'Github/guard/commitlint.config.mjs'),'--color=false','--edit',str(path)]
   result=subprocess.run(command,cwd=scratch,env=tools.environment,capture_output=True)
   log.write(text+result.stdout.decode()+result.stderr.decode()+f'exit={result.returncode}\n');log.flush()
   assert result.returncode==0
 receipt={'tag':tag,'tool_source':revision,'validated_messages':messages}
 (evidence/'commitlint.json').write_text(json.dumps(receipt,indent=2)+'\n')
 if '--messages-only' in sys.argv:raise SystemExit(0)
spec=importlib.util.spec_from_file_location('lint',export/'Tools/ci/lint_workflows.py');lint=importlib.util.module_from_spec(spec);spec.loader.exec_module(lint)
pins=json.loads((export/'Tools/ci/tools.json').read_bytes());binroot=Path(os.environ['TMPDIR'])/'lint'
paths=['.github/workflows/deliver.yml']
results={}
for name in ('actionlint','zizmor'):
 executable=lint.install_tool(name,pins[name],binroot)
 command=[str(executable)]
 if name=='actionlint':command+=['-shellcheck=','-pyflakes=','-config-file','tools/actionlint.yaml',*paths]
 else:command+=['--strict-collection','--no-progress','--format=json','--config','tools/zizmor.yml',*paths]
 env=os.environ.copy()
 if name=='zizmor':env['GH_TOKEN']=subprocess.check_output(['gh','auth','token'],env=os.environ|{'GH_CONFIG_DIR':'/home/administrator/.config/gh-cicd-agent'}).decode().strip()
 result=subprocess.run(command,cwd=root,env=env,capture_output=True)
 (evidence/(name+'.stdout.log')).write_bytes(result.stdout);(evidence/(name+'.stderr.log')).write_bytes(result.stderr)
 results[name]={'pin':pins[name],'exit':result.returncode,'workflow_sha256':hashlib.sha256((root/paths[0]).read_bytes()).hexdigest()}
(evidence/'lint.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
raise SystemExit(any(v['exit'] for v in results.values()))
