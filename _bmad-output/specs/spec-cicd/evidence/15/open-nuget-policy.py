"""Open a new Chrome window at NuGet Trusted Publishing and leave it open."""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
URL = "https://www.nuget.org/account/TrustedPublishing"
code = r"""[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::RootElement
$scope=[System.Windows.Automation.TreeScope]::Descendants
$tabCondition=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::TabItem)
function Identity($e){return (($e.GetRuntimeId()|ForEach-Object{[string]$_}) -join ',')}
$before=@{};foreach($t in $root.FindAll($scope,$tabCondition)){$before[(Identity $t)]=$true}
$browser=Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'
if(-not(Test-Path -LiteralPath $browser)){throw 'Known attended browser executable unavailable'}
Start-Process $browser -ArgumentList @('--new-window','URL')
$deadline=[DateTime]::UtcNow.AddSeconds(30)
$own=$null
do{
 $unique=@{}
 foreach($t in $root.FindAll($scope,$tabCondition)){
  if(-not $before.ContainsKey((Identity $t))){$unique[(Identity $t)]=$t}
 }
 if($unique.Count -eq 1){$own=@($unique.Values)[0];break}
 Start-Sleep -Milliseconds 250
}while([DateTime]::UtcNow -lt $deadline)
if($null -eq $own){throw 'Exact new browser tab unavailable'}
$window=$own;$walker=[System.Windows.Automation.TreeWalker]::ControlViewWalker
while($window.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window){$window=$walker.GetParent($window)}
$address=$null;$doc=$null
do{
 foreach($node in $window.FindAll($scope,[System.Windows.Automation.Condition]::TrueCondition)){
  if($node.Current.Name -in @('Address and search bar',"Barre d'adresse et de recherche")){
   $address=$node.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
  }
  if($node.Current.ControlType -eq [System.Windows.Automation.ControlType]::Document -and -not $node.Current.IsOffscreen){$doc=$node.Current.Name}
 }
 if($null -ne $address -and $null -ne $doc){break}
 Start-Sleep -Milliseconds 250
}while([DateTime]::UtcNow -lt $deadline)
[pscustomobject]@{tab=$own.Current.Name;address=$address;document=$doc;left_open=$true} | ConvertTo-Json -Compress
""".replace("'URL'", repr(URL))
r = subprocess.run(["/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "-NoProfile", "-NonInteractive", "-EncodedCommand",
                    base64.b64encode(code.encode("utf-16-le")).decode()],
                   capture_output=True, timeout=45)
report = {"observed_at": datetime.now(timezone.utc).isoformat(), "exit_code": r.returncode,
          "observation": json.loads(r.stdout.decode("utf-8-sig")) if r.returncode == 0 and r.stdout.strip() else None,
          "error": r.stderr.decode("utf-8", "replace")}
path = HERE / "open-nuget-policy.json"
assert not path.exists(), "Inspect the existing navigation record before any retry"
path.write_text(json.dumps(report, indent=2) + "\n")
path.chmod(0o600)
print(json.dumps(report, indent=2)[:4000])
raise SystemExit(r.returncode)
