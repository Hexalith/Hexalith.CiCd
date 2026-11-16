"""Use the existing attended NuGet UI for additive, scoped pilot policies.

No cookies, browser storage, hidden form values or credentials are read. The
prepare action fills a reviewable form; submit checks every field and scope.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=("prepare", "submit", "readback"))
parser.add_argument("module", choices=("Commons", "PolymorphicSerializations"))
parser.add_argument("--attempt", type=int, default=2)
arguments = parser.parse_args()
module = "Hexalith." + arguments.module
code = r"""[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class NugetWindow {
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr handle,int show);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr handle);
}
'@
$action='ACTION';$module='MODULE'
$root=[System.Windows.Automation.AutomationElement]::RootElement
$docs=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Document)))
$doc=$null
foreach($candidate in $docs){if($candidate.Current.Name -like 'NuGet Gallery*Trusted Publishing*' -and -not $candidate.Current.IsOffscreen){$doc=$candidate;break}}
if($null -eq $doc){throw 'Existing authenticated Trusted Publishing document unavailable'}
function Control($id){return $doc.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::AutomationIdProperty,$id)))}
$expected=@{'__policy-name-0'=($module+' hexalith-release');'__package-owner-0'='Hexalith';'__provider-0'='GitHub Actions';'__github-repository-owner-0'='Hexalith';'__github-repository-0'=$module;'__github-workflow-file-0'='release.yml';'__github-environment-0'='hexalith-release';'__scope-subjects-input-0'=($module+'*')}
if($action -eq 'prepare'){
 $window=$doc;$walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 while($window.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window){$window=$walker.GetParent($window)}
 [void][NugetWindow]::ShowWindow([IntPtr]$window.Current.NativeWindowHandle,9)
 [void][NugetWindow]::SetForegroundWindow([IntPtr]$window.Current.NativeWindowHandle)
 if($null -eq (Control '__policy-name-0')){
  $create=Control 'show-create-container'
  $create.SetFocus()
  [System.Windows.Forms.SendKeys]::SendWait(' ')
  for($i=0;$i -lt 100 -and $null -eq (Control '__policy-name-0');$i++){Start-Sleep -Milliseconds 100}
 }
 if($null -eq (Control '__policy-name-0')){throw 'New policy form did not open'}
 $owner=Control '__package-owner-0'
 $owner.SetFocus()
 [System.Windows.Forms.SendKeys]::SendWait('{HOME}h{ENTER}')
 for($i=0;$i -lt 100 -and $owner.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -ne 'Hexalith';$i++){Start-Sleep -Milliseconds 100}
 if($owner.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -ne 'Hexalith'){throw 'Package owner selection failed'}
 foreach($id in $expected.Keys){if($id -notin @('__package-owner-0','__provider-0')){(Control $id).GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($expected[$id])}}
 foreach($id in @('__push-scope-checked-0','__unlist-scope-checked-0','__stage-scope-checked-0')){
  $pattern=(Control $id).GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
  $desired=if($id -eq '__push-scope-checked-0'){[System.Windows.Automation.ToggleState]::On}else{[System.Windows.Automation.ToggleState]::Off}
  if($pattern.Current.ToggleState -ne $desired){$pattern.Toggle()}
 }
 (Control '__package-push-scope-0').GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
 (Control '__github-environment-0').SetFocus()
}
if($action -in @('prepare','submit')){
 foreach($id in $expected.Keys){if((Control $id).GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -ne $expected[$id]){throw ('Policy field mismatch: '+$id)}}
 foreach($id in @('__push-scope-checked-0','__unlist-scope-checked-0','__stage-scope-checked-0')){
  $actual=(Control $id).GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern).Current.ToggleState
  $desired=if($id -eq '__push-scope-checked-0'){[System.Windows.Automation.ToggleState]::On}else{[System.Windows.Automation.ToggleState]::Off}
  if($actual -ne $desired){throw 'Policy scope mismatch'}
 }
 if(-not (Control '__package-push-scope-0').GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected){throw 'Push scope mismatch'}
 if($action -eq 'submit'){
  $submit=$null
  $buttons=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)))
  foreach($button in $buttons){if($button.Current.Name -eq 'Create' -and $button.Current.AutomationId -eq ''){$submit=$button;break}}
  if($null -eq $submit -or -not $submit.Current.IsEnabled){throw 'Policy submit unavailable'}
  $submit.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
 }
 [pscustomobject]@{action=$action;module=$module;expected_fields=$expected;push=$true;push_new_packages=$true;unlist=$false;stage=$false;legacy_policies_removed=$false} | ConvertTo-Json -Depth 4 -Compress
}else{
 $nodes=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
 $rows=@()
 foreach($node in $nodes){if($node.Current.Name){$rows+=[pscustomobject]@{type=$node.Current.ControlType.ProgrammaticName;name=$node.Current.Name;id=$node.Current.AutomationId}}}
 ConvertTo-Json -InputObject @($rows) -Depth 4 -Compress
}
""".replace("'ACTION'", repr(arguments.action)).replace("'MODULE'", repr(module))
result = subprocess.run([
    "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe", "-NoProfile",
    "-NonInteractive", "-EncodedCommand",
    base64.b64encode(code.encode("utf-16-le")).decode("ascii")], capture_output=True, timeout=45)
assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
observation = json.loads(result.stdout.decode("utf-8-sig"))
report = {"recorded_at": datetime.now(timezone.utc).isoformat(), "action": arguments.action,
          "module": module, "attempt": arguments.attempt}
if arguments.action == "readback":
    rows, policies = observation, []
    names = {name for pilot in ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
             for name in (pilot, pilot + " hexalith-release")}
    for index, row in enumerate(rows):
        if row["type"] == "ControlType.Text" and row["name"] in names:
            segment = []
            for item in rows[index:index + 50]:
                segment.append(item)
                if item["type"] == "ControlType.Button" and item["name"] == "Delete":
                    break
            policies.append(segment)
    report["policies"] = policies
    report["all_policy_edit_ids"] = [row["id"] for row in rows if row["id"].startswith("__start-edit-")]
    report["messages"] = [row for row in rows if any(value in row["name"].lower() for value in (
        "successfully created", "policy has been", "is required", "error occurred", "already exists"))]
else:
    report["result"] = observation
destination = Path(__file__).parent / ("nuget-" + arguments.module.lower() + "-"
                                      + arguments.action + "-" + str(arguments.attempt) + ".json")
destination.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
