"""Read visible NuGet API-key metadata in a new tab; never read key values."""
import base64
import argparse
import datetime
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--attempt', type=int, default=1)
arguments = parser.parse_args()
report = HERE / ('nuget-legacy-key-fresh-ui-' + str(arguments.attempt).zfill(2) + '.json')
assert not report.exists()
code = r'''[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::RootElement
$scope=[System.Windows.Automation.TreeScope]::Descendants
$tabCondition=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::TabItem)
function Identity($element){return (($element.GetRuntimeId()|ForEach-Object{[string]$_}) -join ',')}
function Sanitize([string]$value){return [regex]::Replace($value,'[A-Za-z0-9_+/=-]{32,}','[redacted-opaque]')}
$before=@{};foreach($tab in $root.FindAll($scope,$tabCondition)){$before[(Identity $tab)]=$true}
$result=[ordered]@{metadataOnly=$true;keyValuesRead=$false;cookiesOrStorageRead=$false;accountChanges=$false;ownTabClosed=$false}
$ownTab=$null
try{
 Start-Process 'https://www.nuget.org/account/apikeys?forceApiKeys=true'
 $deadline=[DateTime]::UtcNow.AddSeconds(25)
 do{
  $matches=@($root.FindAll($scope,$tabCondition)|Where-Object{(-not $before.ContainsKey((Identity $_))) -and $_.Current.Name -like 'NuGet Gallery*'})
  $unique=@{};foreach($tab in $matches){$unique[(Identity $tab)]=$tab}
  if($unique.Count -eq 1){$ownTab=@($unique.Values)[0];break}
  Start-Sleep -Milliseconds 250
 }while([DateTime]::UtcNow -lt $deadline)
 if($null -eq $ownTab){throw 'New NuGet tab could not be identified uniquely'}
 $walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker;$window=$ownTab
 while($window.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window){$window=$walker.GetParent($window)}
 $doc=$null;$verified=$false;$path=$null
 do{
  $nodes=$window.FindAll($scope,[System.Windows.Automation.Condition]::TrueCondition)
  foreach($node in $nodes){if($node.Current.Name -in @('Address and search bar',"Barre d'adresse et de recherche")){
   $value=$node.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
   if($value -match '^(https://)?(www\.)?nuget\.org/account/apikeys\?forceApiKeys=true$'){$verified=$true;$path='/account/apikeys?forceApiKeys=true'}
  }}
  $doc=$window.FindFirst($scope,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,'NuGet Gallery | API Keys')))
  if($verified -and $null -ne $doc){break}
  Start-Sleep -Milliseconds 250
 }while([DateTime]::UtcNow -lt $deadline)
 $result.originVerified=$verified;$result.path=$path
 if(-not $verified -or $null -eq $doc){throw 'Authenticated NuGet API Keys document unavailable; inventory remains unverified'}
 $rows=@();$editIds=@();$regenerateCount=0;$deleteCount=0
 foreach($node in $doc.FindAll($scope,[System.Windows.Automation.Condition]::TrueCondition)){
  $type=$node.Current.ControlType
  if($type -in @([System.Windows.Automation.ControlType]::Text,[System.Windows.Automation.ControlType]::Button,[System.Windows.Automation.ControlType]::Hyperlink)){
   $name=$node.Current.Name;$id=$node.Current.AutomationId
   if($id -match '^start-edit-([0-9]+)$'){$editIds+=$Matches[1]}
   if($name -eq 'Regenerate'){$regenerateCount++}
   if($name -eq 'Delete'){$deleteCount++}
   if($name -or $id){$rows+=[pscustomobject]@{type=$type.ProgrammaticName;name=(Sanitize $name);id=(Sanitize $id)}}
  }
 }
 $result.document=$doc.Current.Name;$result.editKeyIds=$editIds;$result.regenerateCount=$regenerateCount;$result.deleteCount=$deleteCount
 $result.rows=$rows;$result.status='read'
}catch{$result.status='unverified';$result.failure=(Sanitize $_.Exception.Message)}
finally{
 if($null -ne $ownTab){
  try{
   $close=@($ownTab.FindAll($scope,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)))|Where-Object{$_.Current.Name -match '^(Close|Fermer)'})
   if($close.Count -eq 1){$close[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke();$result.ownTabClosed=$true}
   else{$result.closeFailure='Exact new-tab close control unavailable'}
  }catch{$result.closeFailure=(Sanitize $_.Exception.Message)}
 }
}
[pscustomobject]$result|ConvertTo-Json -Depth 5 -Compress
'''
process = subprocess.run([
    '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-NonInteractive',
    '-EncodedCommand', base64.b64encode(code.encode('utf-16-le')).decode()], capture_output=True, timeout=45)
record = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'operation': 'fresh attended NuGet API-key metadata read',
          'exit': process.returncode}
if process.returncode == 0:
    record['observation'] = json.loads(process.stdout.decode('utf-8-sig'))
else:
    record['failure'] = process.stderr.decode('utf-8', 'replace')
report.write_text(json.dumps(record, indent=2) + '\n')
report.chmod(0o600)
observation = record.get('observation', {})
print(json.dumps({key: observation.get(key) for key in ('status', 'originVerified', 'editKeyIds', 'regenerateCount', 'deleteCount',
                                                       'ownTabClosed', 'failure', 'closeFailure')}, indent=2))
