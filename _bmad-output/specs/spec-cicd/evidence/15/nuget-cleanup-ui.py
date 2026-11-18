"""Inspect exact NuGet keep/delete controls; delete only policy 20113 after proven adoption.

Use the normal current authenticated UI. No cookies, hidden form values, keys
or credential values are read. Flattened accessibility cards are bound by the
unique Edit ID, complete preceding card metadata, and its immediate Delete
sibling. Never select the first global Delete button.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=("readiness", "begin-delete", "verify-cleanup"))
args = parser.parse_args()
if args.action != "readiness":
    adoption = json.loads((HERE / "authenticated-adoption.json").read_text())
    assert adoption["result"] == "pass"
    assert adoption["modules"]["Hexalith.McpCli"]["perimeter_match"] is True
destination = HERE / ("nuget-cleanup-" + args.action + ".json")
if args.action == "begin-delete":
    assert not destination.exists(), "Inspect actual partial deletion/modal state before any retry"
    destination.write_text(json.dumps({
        "attempted_at": datetime.now(timezone.utc).isoformat(),
        "policy": "20113",
        "action": args.action,
    }, indent=2) + "\n")
code = r'''[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
Add-Type -AssemblyName UIAutomationClient;Add-Type -AssemblyName UIAutomationTypes
$action='ACTION'
$root=[System.Windows.Automation.AutomationElement]::RootElement
$docs=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Document)))
$doc=$null;foreach($d in $docs){if($d.Current.Name -like 'NuGet Gallery*Trusted Publishing*' -and -not $d.Current.IsOffscreen){$doc=$d;break}}
if($null -eq $doc){throw 'Fresh authenticated Trusted Publishing document unavailable'}
$all=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
$expected=@{
 '20113'=@('Hexalith.McpCli','1379417482','production');
 '27180'=@('Hexalith.McpCli','1379417482','hexalith-release')}
$targetIds=if($action -eq 'verify-cleanup'){@('27180')}else{@('20113','27180')}
$rows=@();$deleteTarget=$null
foreach($id in $targetIds){
 $module,$repoId,$environment=$expected[$id]
 $title=if($environment -eq 'production'){$module}else{$module+' hexalith-release'}
 $edit=$null;$editIndex=-1;$start=-1
 for($i=0;$i -lt $all.Count;$i++){
  $n=$all[$i]
  if($n.Current.ControlType -eq [System.Windows.Automation.ControlType]::Text -and $n.Current.Name -eq $title){$start=$i}
  if($n.Current.AutomationId -eq ('__start-edit-'+$id)){$edit=$n;$editIndex=$i;break}
 }
 if($null -eq $edit -or $start -lt 0 -or $start -ge $editIndex){throw ('Exact policy card unavailable: '+$id)}
 $metadata=@();$editIds=@()
 for($i=$start;$i -le $editIndex;$i++){
  $n=$all[$i]
  if($n.Current.ControlType -in @([System.Windows.Automation.ControlType]::Text,[System.Windows.Automation.ControlType]::ListItem)){$metadata+=$n.Current.Name}
  if($n.Current.AutomationId -like '__start-edit-*'){$editIds+=$n.Current.AutomationId}
 }
 $joined=$metadata -join "`n"
 if($editIds.Count -ne 1 -or $editIds[0] -ne ('__start-edit-'+$id)){throw 'Ambiguous policy segment'}
 foreach($value in @(' Active','Hexalith','Repository Owner: Hexalith#80614290','Repository: '+$module+'#'+$repoId,'Workflow: release.yml','Environment: '+$environment)){
  if(-not $joined.Contains($value)){throw ('Policy binding mismatch: '+$id)}
 }
 if($environment -eq 'hexalith-release'){
  if(-not ($metadata -contains 'Push new packages and package versions') -or -not ($metadata -contains ($module+'*')) -or $joined -match 'Unlist|Stage package'){throw 'New keep policy scope mismatch'}
 }
 $delete=$walker.GetNextSibling($edit)
 if($null -eq $delete -or $delete.Current.ControlType -ne [System.Windows.Automation.ControlType]::Button -or $delete.Current.Name -ne 'Delete' -or -not $delete.Current.IsEnabled){throw ('Exact immediate Delete sibling unavailable: '+$id)}
 $rows+=[pscustomobject]@{id=$id;title=$title;repository_id=$repoId;environment=$environment;metadata=$metadata;edit_enabled=$edit.Current.IsEnabled;delete_enabled=$delete.Current.IsEnabled;delete_is_immediate_sibling_of_exact_edit=$true;delete_runtime_id=$delete.GetRuntimeId();disposition=$(if($environment -eq 'production'){'delete only after adoption'}else{'keep'})}
 if($id -eq '20113'){$deleteTarget=$delete}
}
$allIds=@();foreach($n in $all){if($n.Current.AutomationId -like '__start-edit-*'){$allIds+=$n.Current.AutomationId}}
$invoked=$false
if($action -eq 'begin-delete'){
 if($null -eq $deleteTarget){throw 'No reviewed legacy target'}
 $deleteTarget.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke();$invoked=$true
}
[pscustomobject]@{action=$action;policies=$rows;all_policy_edit_ids=$allIds;legacy_delete_control_invoked=$invoked;selected_legacy_id='20113';new_policy_mutated=$false}|ConvertTo-Json -Depth 8 -Compress
'''.replace("'ACTION'", repr(args.action))
result = subprocess.run(
    ["/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe", "-NoProfile",
     "-NonInteractive", "-EncodedCommand",
     base64.b64encode(code.encode("utf-16-le")).decode()],
    capture_output=True, timeout=45)
report = {"observed_at": datetime.now(timezone.utc).isoformat(),
          "action": args.action, "exit": result.returncode}
if result.returncode:
    report["error"] = result.stderr.decode("utf-8", errors="replace")
    report["stdout"] = result.stdout.decode("utf-8", errors="replace")[-4000:]
else:
    report["result"] = json.loads(result.stdout.decode("utf-8-sig"))
    if args.action == "verify-cleanup":
        before = json.loads((HERE / "nuget-cleanup-readiness.json").read_text())["result"]["all_policy_edit_ids"]
        after = report["result"]["all_policy_edit_ids"]
        assert set(before) - set(after) == {"__start-edit-20113"}
        assert not set(after) - set(before)
        assert "__start-edit-27180" in after
        report["all_other_policy_ids_preserved"] = True
        report["removed_exact_legacy_policy_ids"] = [20113]
        report["preserved_scoped_policy_id"] = 27180
destination.write_text(json.dumps(report, indent=2) + "\n")
assert result.returncode == 0, report.get("error")
print(json.dumps(report, indent=2))
