"""Fresh visible App/policy metadata in a separate tab; no form submission."""
import argparse
import base64
import datetime
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('target', choices=('app', 'policy'))
parser.add_argument('--attempt', type=int, required=True)
args = parser.parse_args()
destination = Path(__file__).resolve().parent / f'attended-{args.target}-refresh-{args.attempt:02}.json'
assert not destination.exists()
url = ('https://github.com/organizations/Hexalith/settings/installations/179966090' if args.target == 'app'
       else 'https://www.nuget.org/account/TrustedPublishing')
code = r'''[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::RootElement
$scope=[System.Windows.Automation.TreeScope]::Descendants
$tabCondition=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::TabItem)
function Identity($e){return (($e.GetRuntimeId()|ForEach-Object{[string]$_}) -join ',')}
$before=@{};foreach($t in $root.FindAll($scope,$tabCondition)){$before[(Identity $t)]=$true}
$result=[ordered]@{target='TARGET';url='URL';remoteConfigurationChanges=$false;ownTabClosed=$false}
$own=$null
try{
 Start-Process 'URL'
 $deadline=[DateTime]::UtcNow.AddSeconds(25)
 do{
  $unique=@{}
  foreach($t in $root.FindAll($scope,$tabCondition)){
   if(-not $before.ContainsKey((Identity $t)) -and (($result.target -eq 'app' -and $t.Current.Name -like 'Installed GitHub App*') -or ($result.target -eq 'policy' -and $t.Current.Name -like 'NuGet Gallery*'))){$unique[(Identity $t)]=$t}
  }
  if($unique.Count -eq 1){$own=@($unique.Values)[0];break}
  Start-Sleep -Milliseconds 250
 }while([DateTime]::UtcNow -lt $deadline)
 if($null -eq $own){throw 'Exact new settings tab unavailable'}
 $window=$own;$walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
 while($window.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window){$window=$walker.GetParent($window)}
 $verified=$false;$doc=$null
 do{
  foreach($node in $window.FindAll($scope,[System.Windows.Automation.Condition]::TrueCondition)){
   if($node.Current.Name -in @('Address and search bar',"Barre d'adresse et de recherche")){
    $address=$node.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
    if(($result.target -eq 'app' -and $address -match '^(https://)?github\.com/organizations/Hexalith/settings/installations/179966090/?$') -or ($result.target -eq 'policy' -and $address -match '^(https://)?(www\.)?nuget\.org/account/TrustedPublishing/?$')){$verified=$true}
   }
   if($node.Current.ControlType -eq [System.Windows.Automation.ControlType]::Document -and (($result.target -eq 'app' -and $node.Current.Name -like 'Installed GitHub App*') -or ($result.target -eq 'policy' -and $node.Current.Name -like 'NuGet Gallery*Trusted Publishing*'))){$doc=$node}
  }
  if($verified -and $null -ne $doc){break}
  Start-Sleep -Milliseconds 250
 }while([DateTime]::UtcNow -lt $deadline)
 $result.originVerified=$verified
 if(-not $verified -or $null -eq $doc){throw 'Intended settings origin/document unverified'}
 if($result.target -eq 'policy'){
  $manage=$doc.FindFirst($scope,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::AutomationIdProperty,'show-manage-container')))
  if($null -ne $manage){$p=$manage.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern);if($p.Current.ExpandCollapseState -eq [System.Windows.Automation.ExpandCollapseState]::Collapsed){$p.Expand()}}
 }
 Start-Sleep -Seconds 2
 $rows=@()
 foreach($node in $doc.FindAll($scope,[System.Windows.Automation.Condition]::TrueCondition)){
  $type=$node.Current.ControlType;$name=$node.Current.Name;$id=$node.Current.AutomationId
  if($type -in @([System.Windows.Automation.ControlType]::Text,[System.Windows.Automation.ControlType]::Button,[System.Windows.Automation.ControlType]::Hyperlink,[System.Windows.Automation.ControlType]::RadioButton)){
   if($result.target -eq 'policy' -or $name -match 'Hexalith|[Rr]emove|[Ss]ave|Only select|All repositories'){
    $row=[ordered]@{type=$type.ProgrammaticName;name=$name;id=$id;enabled=$node.Current.IsEnabled}
    if($type -eq [System.Windows.Automation.ControlType]::RadioButton){$row.selected=$node.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected}
    $rows+=[pscustomobject]$row
   }
  }
 }
 $result.rows=$rows;$result.status='read'
}catch{$result.status='unverified';$result.failure=$_.Exception.Message}
finally{
 if($null -ne $own){try{
  $close=@($own.FindAll($scope,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)))|Where-Object{$_.Current.Name -match '^(Close|Fermer)'})
  if($close.Count -eq 1){$close[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke();$result.ownTabClosed=$true}
 }catch{$result.closeFailure='Own tab close unavailable'}}
}
[pscustomobject]$result|ConvertTo-Json -Depth 6 -Compress
'''.replace("'TARGET'", repr(args.target)).replace("'URL'", repr(url))
process = subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
    '-NoProfile', '-NonInteractive', '-EncodedCommand', base64.b64encode(code.encode('utf-16-le')).decode()],
    capture_output=True, timeout=45)
report = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exit':process.returncode}
if process.returncode == 0:
    report['observation'] = json.loads(process.stdout.decode('utf-8-sig'))
else:
    report['status'] = 'unverified'
destination.write_text(json.dumps(report, indent=2) + '\n')
destination.chmod(0o600)
print(json.dumps({**{k:v for k,v in report.items() if k != 'observation'},
                  'observation':{k:v for k,v in report.get('observation',{}).items() if k != 'rows'}}))
