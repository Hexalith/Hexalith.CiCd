"""Read attended NuGet API-key metadata only; never read values or invoke key actions."""
import argparse,base64,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('action',choices=['navigate','readback','reload']);a=p.parse_args()
code=r'''[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$action='ACTION'
if($action -eq 'navigate'){
 Start-Process chrome.exe -ArgumentList 'https://www.nuget.org/account/apikeys'
 [pscustomobject]@{action='navigate';url='https://www.nuget.org/account/apikeys'}|ConvertTo-Json -Compress
 exit
}
$root=[System.Windows.Automation.AutomationElement]::RootElement
$docs=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Document)))
$doc=$null
foreach($candidate in $docs){if($candidate.Current.Name -eq 'NuGet Gallery | API Keys' -and -not $candidate.Current.IsOffscreen){$doc=$candidate;break}}
if($null -eq $doc){
 $confirmation=$null
 foreach($candidate in $docs){if($candidate.Current.Name -eq 'Confirm access' -and -not $candidate.Current.IsOffscreen){$confirmation=$candidate;break}}
 if($null -eq $confirmation){throw 'Existing attended NuGet API Keys document unavailable'}
 $rows=@()
 $nodes=$confirmation.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
 foreach($node in $nodes){if($node.Current.ControlType -in @([System.Windows.Automation.ControlType]::Text,[System.Windows.Automation.ControlType]::Button,[System.Windows.Automation.ControlType]::Hyperlink)){if($node.Current.Name){$rows+=[pscustomobject]@{type=$node.Current.ControlType.ProgrammaticName;name=$node.Current.Name;id=$node.Current.AutomationId}}}}
 [pscustomobject]@{document='Confirm access';status='reauthentication_required';rows=@($rows)}|ConvertTo-Json -Depth 4 -Compress
 exit
}
if($action -eq 'reload'){
 $window=$doc;$walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 while($window.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window){$window=$walker.GetParent($window)}
 $reload=$window.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,'Actualiser')))
 if($null -eq $reload){throw 'Observed browser Reload control unavailable'}
 $reload.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
 [pscustomobject]@{action='reload';reload_invoked=$true}|ConvertTo-Json -Compress
 exit
}
$nodes=$doc.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$rows=@()
foreach($node in $nodes){
 # Names of displayed metadata only; never read Edit/ValuePattern contents.
 if($node.Current.ControlType -in @([System.Windows.Automation.ControlType]::Text,[System.Windows.Automation.ControlType]::Button,[System.Windows.Automation.ControlType]::ListItem)){
  if($node.Current.Name){$rows+=[pscustomobject]@{type=$node.Current.ControlType.ProgrammaticName;name=$node.Current.Name;id=$node.Current.AutomationId}}
 }
}
[pscustomobject]@{document=$doc.Current.Name;rows=@($rows)}|ConvertTo-Json -Depth 4 -Compress
'''.replace("'ACTION'",repr(a.action))
r=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(code.encode('utf-16-le')).decode()],capture_output=True,timeout=45)
assert r.returncode==0,r.stderr.decode('utf-8','replace')
x={'recorded_at':datetime.now(timezone.utc).isoformat(),'action':a.action,'interaction':'Read-only API-key names/status/package scopes; no values read or key actions invoked','observation':json.loads(r.stdout.decode('utf-8-sig'))}
Path(__file__).with_name('nuget-api-keys-'+a.action+'.json').write_text(json.dumps(x,indent=2)+'\n')
print(json.dumps(x,indent=2))
