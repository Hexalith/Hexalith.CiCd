"""Refresh story 11 blockers using read-only APIs, UIAutomation and Git reads.

No credential value, browser secret, form submission or repository mutation is
needed. Run from the CiCd root; results are saved beside this script.
"""
from datetime import datetime, timezone
import base64
import json
import os
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PROFILE = "/home/administrator/.config/gh"
report = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "effective_GH_CONFIG_DIR": os.environ.get("GH_CONFIG_DIR"),
    "override_presence": {name: name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN")},
    "administration_profile": PROFILE,
    "requests": [],
}
assert not any(report["override_presence"].values()), "Unexpected inherited credential override"
environment = dict(os.environ, GH_CONFIG_DIR=PROFILE, GH_PROMPT_DISABLED="1")
for name in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)


def run(arguments, *, cwd=ROOT, env=None, timeout=60):
    return subprocess.run(arguments, cwd=cwd, env=env, text=True,
                          capture_output=True, timeout=timeout)


for endpoint in (
        "user", "repos/Hexalith/Hexalith.CiCd", "orgs/Hexalith/installations",
        "user/installations/179966090/repositories?per_page=100"):
    result = run(["gh", "api", "--method", "GET", "--include", endpoint], env=environment)
    headers, _, body = result.stdout.partition("\n\n")
    value = json.loads(body)
    if result.returncode == 0:
        if endpoint == "user":
            value = {name: value[name] for name in ("login", "id")}
        elif endpoint.startswith("repos/"):
            value = {name: value.get(name) for name in ("id", "full_name", "permissions")}
        elif endpoint == "orgs/Hexalith/installations":
            value = {"total_count": value["total_count"], "cicd_installations": [
                {name: item.get(name) for name in (
                    "id", "app_id", "app_slug", "repository_selection", "permissions")}
                for item in value["installations"] if item["id"] == 179966090]}
        else:
            value = {"total_count": value["total_count"], "repositories": [
                {name: item.get(name) for name in ("id", "full_name")}
                for item in value["repositories"]]}
    report["requests"].append({
        "endpoint": endpoint, "exit": result.returncode,
        "headers": [line for line in headers.splitlines() if line.startswith(
            ("HTTP/", "X-Oauth-Scopes:", "X-Accepted-Github-Permissions:"))],
        "data": value, "error": result.stderr.strip(),
    })

powershell = r"""[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::RootElement
$windows=$root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
$result=@()
foreach($window in $windows){
 if($window.Current.Name -eq 'Confirm access - Google Chrome'){
  $nodes=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  $names=@()
  $url=$null
  foreach($node in $nodes){
   if($node.Current.Name -in @('Confirm access','Use passkey or security key','Use GitHub Mobile','Use your authenticator app','Use your password','@jpiquot')){$names+=$node.Current.Name}
   if($node.Current.Name -in @('Address and search bar',"Barre d'adresse et de recherche")){
    $pattern=$null
    if($node.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)){
     $value=$pattern.Current.Value
     if($value -match '^(https://)?github\.com/organizations/Hexalith/settings/installations/179966090/?$'){$url=$value}
    }
   }
  }
  $result+=[pscustomobject]@{title=$window.Current.Name;url=$url;matched_names=@($names | Select-Object -Unique)}
 }
}
ConvertTo-Json -InputObject @($result) -Depth 5 -Compress
"""
browser = subprocess.run([
    "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe", "-NoProfile",
    "-NonInteractive", "-EncodedCommand",
    base64.b64encode(powershell.encode("utf-16-le")).decode("ascii")],
    capture_output=True, timeout=45)
report["browser"] = {
    "exit": browser.returncode,
    "interaction": "read-only UIAutomation; no form fill, submit or authentication control invocation",
    "windows": json.loads(browser.stdout.decode("utf-8-sig")) if browser.returncode == 0 else [],
    "error": browser.stderr.decode("utf-8", "replace") if browser.returncode else "",
}

builds = ROOT / "references/Hexalith.Builds"
report["modules"] = []
for name in ("Hexalith.Commons", "Hexalith.PolymorphicSerializations"):
    module = ROOT / "references" / name
    command = ["python3", "references/Hexalith.Builds/check.py"]
    result = run(command, cwd=module)
    tree = run(["git", "ls-tree", "HEAD", "references/Hexalith.Builds", ".github/hexalith-ci.json"], cwd=module)
    pin = tree.stdout.split()[2]
    pin_check = run(["git", "ls-tree", pin, "check.py", "Github/lib/local_check.py"], cwd=builds)
    revision = run(["git", "rev-parse", "HEAD"], cwd=module)
    report["modules"].append({
        "repository": name, "revision": revision.stdout.strip(), "cwd": str(module),
        "command": command, "exit": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr,
        "committed_inputs": {"exit": tree.returncode, "stdout": tree.stdout, "stderr": tree.stderr},
        "legacy_builds_pin": pin,
        "legacy_checker_files": {"command": ["git", "ls-tree", pin, "check.py", "Github/lib/local_check.py"],
                                 "exit": pin_check.returncode, "stdout": pin_check.stdout,
                                 "stderr": pin_check.stderr},
    })
report["authentication_after"] = {
    "effective_GH_CONFIG_DIR": os.environ.get("GH_CONFIG_DIR"),
    "override_presence": {name: name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN")},
}
report["nested_submodules_initialized"] = False
report["push_attempted"] = False
report["remote_mutations"] = False
report["completed_at"] = datetime.now(timezone.utc).isoformat()
(HERE / "resume-prerequisites.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"recorded_at": report["recorded_at"],
                  "app_selection_api_exit": report["requests"][-1]["exit"],
                  "confirm_access_windows": len(report["browser"]["windows"]),
                  "prepush_exits": {row["repository"]: row["exit"] for row in report["modules"]},
                  "remote_mutations": report["remote_mutations"]}, indent=2))
