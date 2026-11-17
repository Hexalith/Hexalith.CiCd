"""Validate the exact checkpoint message with released, locked Builds tooling."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
R=Path("/home/administrator/projects/hexalith/cicd/references/Hexalith.Builds")
E=Path("/home/administrator/projects/hexalith/cicd-story-24-checkpoint-20261117/_bmad-output/specs/spec-cicd/evidence/24/remote-checkpoint-20261117")
TMP=Path(os.environ["TMPDIR"]);SOURCE=TMP/"released";SOURCE.mkdir()
TAG="v6.2.0";SHA="0ccd12af6576a3aac601340dec7dba53e86768c3"
MESSAGE="build(cicd): save unfinished story 24 checkpoint\n"
def git(*args):return subprocess.check_output(["git","-C",str(R),*args])
assert git("rev-parse",TAG+"^{commit}").decode().strip()==SHA
release=json.loads(subprocess.check_output(["gh","release","view",TAG,"--repo","Hexalith/Hexalith.Builds","--json","tagName,isDraft,isPrerelease,publishedAt,targetCommitish,url"]))
assert not release["isDraft"] and not release["isPrerelease"] and release["targetCommitish"]==SHA
paths=git("ls-tree","-r","--name-only",SHA,"--","Github/lib","Github/guard").decode().splitlines()
inputs={}
for name in paths:
    if (name.startswith("Github/lib/") and name.count("/")==2 and name.endswith(".py")) or name in (
        "Github/guard/package.json","Github/guard/package-lock.json","Github/guard/commitlint.config.mjs","Github/guard/commitlint_bridge.mjs"):
        dest=SOURCE/name;dest.parent.mkdir(parents=True,exist_ok=True)
        payload=git("show",SHA+":"+name);dest.write_bytes(payload);inputs[name]=hashlib.sha256(payload).hexdigest()
binary=Path("/home/administrator/.nvm/versions/node/v24.22.1/bin")
assert (binary/"node").is_file()
os.environ["PATH"]=str(binary)+os.pathsep+os.environ["PATH"]
sys.path.insert(0,str(SOURCE/"Github/lib"))
from guard_tools import Tools
tools_dir=TMP/"message-tools";tools_dir.mkdir()
record={"at":datetime.now(timezone.utc).isoformat(),"release":release,"policy_commit":SHA,"policy_input_sha256":inputs,"commands":[],
    "message":MESSAGE,"message_sha256":hashlib.sha256(MESSAGE.encode()).hexdigest(),"scope":"Message validation only. No product qualification or source execution."}
class RecordedTools(Tools):
    def _process(self,arguments,operation,payload=None,**kwargs):
        r=super()._process(arguments,operation,payload,**kwargs)
        record["commands"].append({"arguments":arguments,"operation":operation,"returncode":r.returncode,"stdout":r.stdout,"stderr":r.stderr})
        return r
message_file=TMP/"candidate-message.txt";message_file.write_text(MESSAGE)
try:
    tools=RecordedTools(tools_dir)
    tools.lint_message(message_file.read_text(),"checkpoint commit")
    package=json.loads((tools_dir/"node_modules/@commitlint/cli/package.json").read_text())
    assert package["version"]=="21.2.4"
    record["versions"]={"commitlint":package["version"],"node":subprocess.check_output(["node","--version"],text=True).strip(),"npm":subprocess.check_output(["npm","--version"],text=True).strip()}
    record["pass"]=True
    (E/"commit-message.txt").write_bytes(message_file.read_bytes())
finally:
    (E/"commit-message-validation.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps({"pass":record["pass"],"versions":record["versions"],"validated_commands":len(record["commands"])}))
