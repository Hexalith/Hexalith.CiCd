"""Install the one-shot observer only after exact-source qualification/push."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
candidate = json.loads((HERE / "nightly-diagnostics-candidate-5.json").read_text())
push = json.loads((HERE / "nightly-diagnostics-push.json").read_text())
assert candidate["result"] == "pass" and candidate["validation_exit"] == 0
assert candidate["original_index_preserved"] and push["push_confirmed"]
assert push["head"] == candidate["head"]
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
unit = "hexalith-cicd-story11-20261117"
directory = Path("/home/administrator/.config/systemd/user")
directory.mkdir(parents=True, exist_ok=True)
service = directory / (unit + ".service")
timer = directory / (unit + ".timer")
assert not service.exists() and not timer.exists(), "Inspect an existing continuation before changing it"
task_path = os.environ["PATH"]
assert not any(char in task_path for char in ("\n", "\r", '"', "\\", "%"))
service.write_text("[Unit]\nDescription=Validate the genuine 17 November story 11 Nightly\n\n"
    "[Service]\nType=exec\nWorkingDirectory=" + str(ROOT) + "\n"
    "Environment=GH_CONFIG_DIR=/home/administrator/.config/gh-cicd-agent\n"
    'Environment="PATH=' + task_path + '"\n'
    "UnsetEnvironment=GH_TOKEN GITHUB_TOKEN\n"
    "ExecStart=/home/administrator/.local/bin/run-with-temp /usr/bin/python3 "
    + str(HERE / "run-nightly-continuation.py") + "\n"
    "RuntimeMaxSec=23h\nKillMode=control-group\nTimeoutStopSec=15s\n"
    "StandardOutput=append:" + str(HERE / "nightly-continuation-service.log") + "\nStandardError=inherit\n")
timer.write_text("[Unit]\nDescription=Observe story 11 after the genuine 03:17 Paris Nightly\n\n"
    "[Timer]\nOnCalendar=2026-11-17 02:20:00 UTC\nAccuracySec=1s\n"
    "RandomizedDelaySec=0\nPersistent=true\nUnit=" + unit + ".service\n\n"
    "[Install]\nWantedBy=timers.target\n")
subprocess.run(["systemd-analyze", "--user", "verify", str(service), str(timer)], check=True)
subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
subprocess.run(["systemctl", "--user", "enable", "--now", unit + ".timer"], check=True)
result = subprocess.run(["systemctl", "--user", "show", unit + ".timer", "--property=ActiveState",
    "--property=NextElapseUSecRealtime", "--property=LastTriggerUSec", "--property=Unit"],
    check=True, capture_output=True, text=True)
assert "ActiveState=active" in result.stdout
assert "2026-11-17" in result.stdout, result.stdout
report = {"installed_at": datetime.now(timezone.utc).isoformat(), "unit": unit,
          "service_path": str(service), "timer_path": str(timer), "source": push["head"],
          "genuine_nightly_expected_utc": "2026-11-17T02:17:00Z",
          "observer_starts_utc": "2026-11-17T02:20:00Z",
          "observer_starts_europe_paris": "2026-11-17T03:20:00+01:00",
          "profile": "/home/administrator/.config/gh-cicd-agent",
          "manual_workflow_dispatch": False, "scope": "read-only scheduled-event watcher then authorized BMAD verification/review",
          "readback": result.stdout, "result": "active; future scheduled outcome remains unverified"}
(HERE / "nightly-continuation-schedule.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
