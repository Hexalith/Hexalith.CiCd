"""Observe or add only AI.Tools through the authenticated installation settings UI.

Each action is bounded and records visible controls only. Never reads cookies,
tokens, hidden controls, or credential stores. Save requires an exact additive
comparison against the refreshed baseline, with selected-only scope preserved.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=("observe", "reload", "open", "search", "choose", "save"))
args = parser.parse_args()
here = Path(__file__).resolve().parent
baseline = here / "app-selection-baseline.json"
expected = None
if args.action == "save":
    previous = json.loads(baseline.read_text())["observation"]
    assert previous["only_selected"] and not previous["save_enabled"]
    expected = sorted(set(previous["selected"]) | {"Hexalith.AI.Tools"})

code = r"""[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class AppSelectionWindow {
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int s);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
}
'@
$action='ACTION'
$root=[System.Windows.Automation.AutomationElement]::RootElement
$doc=$root.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,'Installed GitHub App - Hexalith CiCd')))
if($null -eq $doc -or $doc.Current.IsOffscreen){throw 'Active installation document unavailable'}
$walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
$window=$doc
while($window.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window){$window=$walker.GetParent($window)}
$url=$null
$windowNodes=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
foreach($n in $windowNodes){if($n.Current.Name -in @('Address and search bar',"Barre d'adresse et de recherche")){
 $v=$n.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
 if($v -match '^(https://)?github\.com/organizations/Hexalith/settings/installations/179966090/?$'){$url=$v}
}}
if($null -eq $url){throw 'Installation URL not verified'}
function Nodes {return $doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)}
function Named($name,$type){return @((Nodes) | Where-Object {$_.Current.Name -eq $name -and $_.Current.ControlType -eq $type})}
function State {
 $selected=@((Nodes) | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -like 'Remove Hexalith.*'} | ForEach-Object {$_.Current.Name.Substring(7)} | Sort-Object -Unique)
 $s=@((Nodes) | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq 'Save'})
 $r=@((Nodes) | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::RadioButton -and $_.Current.Name -eq 'Only select repositories'})
 if($s.Count -ne 1 -or $r.Count -ne 1){throw 'Exact save/radio controls unavailable'}
 return [pscustomobject]@{selected=$selected;save_enabled=$s[0].Current.IsEnabled;only_selected=$r[0].GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected}
}
$before=State
if(-not $before.only_selected){throw 'Selected-only installation scope is required'}
if($action -eq 'reload'){
 if($before.save_enabled){throw 'Refusing reload over pending unsaved settings'}
 $reload=@($windowNodes | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -in @('Actualiser','Reload')})
 if($reload.Count -ne 1){throw 'Exact reload control unavailable'}
 $reload[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
 [pscustomobject]@{action=$action;url=$url;reload_invoked=$true} | ConvertTo-Json -Compress
 exit
}
if($action -in @('open','search')){
 [void][AppSelectionWindow]::ShowWindow([IntPtr]$window.Current.NativeWindowHandle,9)
 [void][AppSelectionWindow]::SetForegroundWindow([IntPtr]$window.Current.NativeWindowHandle)
 $search=Named 'Search for a repository' ([System.Windows.Automation.ControlType]::Edit)
 if($search.Count -eq 0){
  $select=Named 'Select repositories' ([System.Windows.Automation.ControlType]::Button)
  if($select.Count -ne 1){throw ('Exact selector unavailable: '+$select.Count)}
  $scroll=$null
  if($select[0].TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$scroll)){$scroll.ScrollIntoView();Start-Sleep -Milliseconds 300}
  $select[0].SetFocus()
  $select[0].GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Expand()
 }
 for($i=0;$i -lt 40;$i++){$search=Named 'Search for a repository' ([System.Windows.Automation.ControlType]::Edit);if($search.Count -eq 1){break};Start-Sleep -Milliseconds 200}
 if($search.Count -ne 1){throw 'Repository search did not appear'}
 if($action -eq 'search'){
  $search[0].SetFocus()
  $search[0].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue('Hexalith.AI.Tools')
  Start-Sleep -Milliseconds 2000
 }
}
if($action -eq 'choose'){
 $matches=@((Nodes) | Where-Object {($_.Current.Name -in @('Hexalith.AI.Tools','Hexalith/Hexalith.AI.Tools') -or $_.Current.Name -clike 'Hexalith/Hexalith.AI.Tools *') -and -not $_.Current.IsOffscreen -and $_.Current.ControlType -in @([System.Windows.Automation.ControlType]::CheckBox,[System.Windows.Automation.ControlType]::ListItem,[System.Windows.Automation.ControlType]::MenuItem)})
 if($matches.Count -ne 1){throw ('Exact AI.Tools choice unavailable: '+$matches.Count)}
 $choice=$matches[0];$p=$null
 if($choice.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$p)){$p.Select()}
 elseif($choice.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern,[ref]$p)){if($p.Current.ToggleState -eq [System.Windows.Automation.ToggleState]::Off){$p.Toggle()}}
 elseif($choice.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$p)){$p.Invoke()}
 else{throw 'Repository choice has no supported selection pattern'}
 Start-Sleep -Milliseconds 500
}
if($action -eq 'save'){
 $expected=EXPECTED_JSON | ConvertFrom-Json
 if(-not $before.save_enabled -or @($before.selected).Count -ne @($expected).Count -or (Compare-Object @($before.selected) @($expected))){throw 'Pending settings are not the exact authorized repository addition'}
 $save=@((Nodes) | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq 'Save'})
 $save[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
 Start-Sleep -Milliseconds 1000
}
$state=State
$controls=@((Nodes) | Where-Object {(-not $_.Current.IsOffscreen) -and ($_.Current.Name -like '*AI.Tools*' -or $_.Current.Name -eq 'Search for a repository' -or $_.Current.ControlType -in @([System.Windows.Automation.ControlType]::CheckBox,[System.Windows.Automation.ControlType]::MenuItem))} | ForEach-Object {[pscustomobject]@{name=$_.Current.Name;type=$_.Current.ControlType.ProgrammaticName;enabled=$_.Current.IsEnabled;patterns=@($_.GetSupportedPatterns() | ForEach-Object {$_.ProgrammaticName})}})
[pscustomobject]@{action=$action;url=$url;before=$before;selected=$state.selected;save_enabled=$state.save_enabled;only_selected=$state.only_selected;controls=$controls;save_invoked=($action -eq 'save')} | ConvertTo-Json -Depth 6 -Compress
""".replace("'ACTION'", repr(args.action)).replace("EXPECTED_JSON", "'" + json.dumps(expected) + "'")

r = subprocess.run(["/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "-NoProfile", "-NonInteractive", "-EncodedCommand",
                    base64.b64encode(code.encode("utf-16-le")).decode()],
                   capture_output=True, timeout=45)
report = {"observed_at": datetime.now(timezone.utc).isoformat(), "action": args.action,
          "exit_code": r.returncode,
          "observation": json.loads(r.stdout.decode("utf-8-sig")) if r.returncode == 0 else None,
          "error": r.stderr.decode("utf-8", "replace")}
path = here / ("app-selection-" + args.action + "-" + datetime.now(timezone.utc).strftime("%H%M%S") + ".json")
path.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
raise SystemExit(r.returncode)
