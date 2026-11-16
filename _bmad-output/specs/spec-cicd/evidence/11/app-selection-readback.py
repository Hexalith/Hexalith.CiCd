"""Read the active installed-App document, ignoring stale Confirm access nodes."""
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
[pscustomobject]@{document=$doc.Current.Name;url=$url;selected=@($selected | Sort-Object);save_enabled=$save.Current.IsEnabled;only_selected_repositories=$radio.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected} | ConvertTo-Json -Depth 4 -Compress
"""
result = subprocess.run([
    "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe", "-NoProfile",
    "-NonInteractive", "-EncodedCommand",
    base64.b64encode(code.encode("utf-16-le")).decode("ascii")],
    capture_output=True, timeout=45)
assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
observation = json.loads(result.stdout.decode("utf-8-sig"))
assert observation["only_selected_repositories"] and not observation["save_enabled"]
assert observation["selected"] == ["Hexalith.Builds", "Hexalith.CiCd", "Hexalith.Commons",
                                  "Hexalith.PolymorphicSerializations"]
report = {"recorded_at": datetime.now(timezone.utc).isoformat(),
          "interaction": "read-only UIAutomation after browser reload of installation settings",
          "result": observation}
Path(__file__).with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
