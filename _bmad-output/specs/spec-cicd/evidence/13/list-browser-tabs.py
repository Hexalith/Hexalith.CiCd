"""List visible browser window and tab names. No form, cookie, or credential reads."""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

code = r"""[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::RootElement
$scope=[System.Windows.Automation.TreeScope]::Descendants
$windows=@()
foreach($w in $root.FindAll([System.Windows.Automation.TreeScope]::Children,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Window)))){
 $tabs=@()
 foreach($t in $w.FindAll($scope,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::TabItem)))){
  $tabs+=[pscustomobject]@{name=$t.Current.Name;offscreen=$t.Current.IsOffscreen}
 }
 $docs=@()
 foreach($d in $w.FindAll($scope,(New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Document)))){
  if(-not $d.Current.IsOffscreen){$docs+=$d.Current.Name}
 }
 $addresses=@()
 foreach($n in $w.FindAll($scope,[System.Windows.Automation.Condition]::TrueCondition)){
  if($n.Current.Name -in @('Address and search bar',"Barre d'adresse et de recherche")){
   $addresses+=$n.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
  }
 }
 $windows+=[pscustomobject]@{name=$w.Current.Name;class=$w.Current.ClassName;tabs=$tabs;documents=$docs;addresses=$addresses}
}
$chrome=Get-Process chrome -ErrorAction SilentlyContinue | Select-Object -First 5 Id,ProcessName,MainWindowTitle
[pscustomobject]@{windows=$windows;chrome=@($chrome)} | ConvertTo-Json -Depth 6 -Compress
"""
r = subprocess.run(["/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "-NoProfile", "-NonInteractive", "-EncodedCommand",
                    base64.b64encode(code.encode("utf-16-le")).decode()],
                   capture_output=True, timeout=45)
report = {"observed_at": datetime.now(timezone.utc).isoformat(), "exit_code": r.returncode,
          "observation": json.loads(r.stdout.decode("utf-8-sig")) if r.returncode == 0 and r.stdout.strip() else None,
          "error": r.stderr.decode("utf-8", "replace")}
path = Path(__file__).resolve().parent / "list-browser-tabs.json"
path.write_text(json.dumps(report, indent=2) + "\n")
path.chmod(0o600)
print(json.dumps(report, indent=2)[:8000])
raise SystemExit(r.returncode)
