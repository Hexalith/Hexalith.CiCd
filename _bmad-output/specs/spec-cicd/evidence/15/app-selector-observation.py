"""Read the exact installation selector through existing authenticated UIAutomation.
No authentication control, credential read or settings save is performed.
"""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

code = r"""[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::RootElement
$doc=$root.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,'Installed GitHub App - Hexalith CiCd')))
if($null -eq $doc -or $doc.Current.IsOffscreen){throw 'Active installation document unavailable'}
$nodes=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$selected=@();$save=$null;$radio=$null
foreach($node in $nodes){
 if($node.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $node.Current.Name -like 'Remove Hexalith.*'){$selected+=$node.Current.Name.Substring(7)}
 if($node.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $node.Current.Name -eq 'Save'){$save=$node}
 if($node.Current.ControlType -eq [System.Windows.Automation.ControlType]::RadioButton -and $node.Current.Name -eq 'Only select repositories'){$radio=$node}
}
$walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
$window=$doc
while($window.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window){$window=$walker.GetParent($window)}
$windowNodes=$window.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$url=$null
foreach($node in $windowNodes){
 if($node.Current.Name -in @('Address and search bar',"Barre d'adresse et de recherche")){
  $value=$node.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
  if($value -match '^(https://)?github\.com/organizations/Hexalith/settings/installations/179966090/?$'){$url=$value}
 }
}
if($null -eq $url){throw 'Installation URL not verified'}
$select=@($nodes | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and $_.Current.Name -eq 'Select repositories'})
$pattern=$null
$before='Menu already exposed'
if($select.Count -eq 1){
 $pattern=$select[0].GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
 $before=$pattern.Current.ExpandCollapseState.ToString()
 if($before -eq 'Collapsed'){$pattern.Expand();Start-Sleep -Milliseconds 500}
}
$nodes=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$search=@($nodes | Where-Object {$_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Edit -and $_.Current.Name -eq 'Search for a repository'})
$searched=$false
if($search.Count -eq 1){$search[0].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue('Hexalith.McpCli');$searched=$true;Start-Sleep -Milliseconds 1500}
$nodes=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$controls=@($nodes | Where-Object {$_.Current.ControlType -in @([System.Windows.Automation.ControlType]::Edit,[System.Windows.Automation.ControlType]::ComboBox,[System.Windows.Automation.ControlType]::CheckBox,[System.Windows.Automation.ControlType]::Menu,[System.Windows.Automation.ControlType]::MenuItem) -or $_.Current.Name -like '*search*' -or $_.Current.Name -like '*McpCli*' -or $_.Current.Name -eq 'Select repositories'} | ForEach-Object {[pscustomobject]@{name=$_.Current.Name;id=$_.Current.AutomationId;type=$_.Current.ControlType.ProgrammaticName;enabled=$_.Current.IsEnabled;offscreen=$_.Current.IsOffscreen;patterns=@($_.GetSupportedPatterns() | ForEach-Object {$_.ProgrammaticName})}})
[pscustomobject]@{document=$doc.Current.Name;url=$url;selected=@($selected | Sort-Object);save_enabled=$save.Current.IsEnabled;selector_before=$before;selector_after=$(if($null -ne $pattern){$pattern.Current.ExpandCollapseState.ToString()}else{'Menu already exposed'});controls=$controls;repository_search_attempted=$searched;search_text='Hexalith.McpCli';search_reason='Search only; no repository choice or Save invoked';page_reloaded=$false;remote_settings_changed=$false} | ConvertTo-Json -Depth 6 -Compress"""

r = subprocess.run(["/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", base64.b64encode(code.encode("utf-16-le")).decode()], capture_output=True, timeout=45)
report = {"recorded_at": datetime.now(timezone.utc).isoformat(), "exit_code": r.returncode, "observation": json.loads(r.stdout.decode("utf-8-sig")) if r.returncode == 0 else None, "stderr": r.stderr.decode("utf-8", "replace")}
Path(__file__).with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
