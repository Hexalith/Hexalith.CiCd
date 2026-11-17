"""Observe only the genuine 2026-11-18 scheduled nightly. No dispatch or rerun."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PROFILE = "/home/administrator/.config/gh-cicd-agent"
NIGHT_START = "2026-11-18T02:17:00Z"
NIGHT_END = "2026-11-19T00:00:00Z"
WAKE_AT = datetime(2026, 11, 18, 2, 16, tzinfo=timezone.utc)
DEADLINE_AT = datetime(2026, 11, 18, 20, 17, tzinfo=timezone.utc)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
assert os.environ.get("GH_CONFIG_DIR") == PROFILE
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR=PROFILE, GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)


def now():
    return datetime.now(timezone.utc).isoformat()


def get(endpoint):
    result = subprocess.run(["gh", "api", "--include", "--method", "GET", endpoint],
                            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=60)
    header, body = result.stdout.split("\n\n", 1)
    value = json.loads(body)
    if result.returncode:
        message = value.get("message", "unreadable response") if isinstance(value, dict) else "invalid response"
        safe = {key.lower(): text.strip() for line in header.splitlines()[1:] if ":" in line
                for key, text in [line.split(":", 1)] if key.lower() in {
                    "x-github-request-id", "x-accepted-github-permissions", "retry-after",
                    "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset"}}
        raise RuntimeError(json.dumps({"status": header.splitlines()[0], "headers": safe,
            "message": re.sub(r"https?://[^\s]+", "[URL omitted]", str(message))[:240]}))
    return value


identity = get("user")
assert identity["login"] == "jpiquot" and identity["id"] == 6775094
if args.check:
    print(json.dumps({"ready": True, "profile": PROFILE, "login": identity["login"],
                      "token_overrides_present": False, "remote_mutation": False,
                      "manual_dispatch_or_rerun": False}))
    raise SystemExit(0)

path = HERE / "nightly-continuation-20261118-observation.json"
if path.exists():
    report = json.loads(path.read_text())
    if str(report.get("result", "")).startswith("terminal parent observed"):
        print(json.dumps({"result": report["result"], "selected_run_id": report.get("selected_run_id")}))
        raise SystemExit(0)
else:
    report = {"started_at": now(), "expected_event": "schedule", "expected_date_utc": "2026-11-18",
              "expected_cron_utc": "17 2 * * *", "night_start": NIGHT_START, "night_end": NIGHT_END,
              "profile": PROFILE, "login": identity["login"], "manual_dispatch_or_rerun": False,
              "observations": [], "errors": [], "result": "waiting; not accepted"}


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")


save()
while datetime.now(timezone.utc) < WAKE_AT:
    remaining = (WAKE_AT - datetime.now(timezone.utc)).total_seconds()
    report["sleeping_until"] = WAKE_AT.isoformat().replace("+00:00", "Z")
    report["heartbeat_at"] = now()
    save()
    print(json.dumps({"heartbeat_at": report["heartbeat_at"], "sleeping_until": report["sleeping_until"]}),
          flush=True)
    time.sleep(min(60, max(1, remaining)))

report["awake_at"] = now()
save()
selected = report.get("selected_run_id")
previous = None
if report.get("observations"):
    last = report["observations"][-1]
    previous = (last.get("status"), last.get("conclusion"), last.get("run_attempt"))
while datetime.now(timezone.utc) < DEADLINE_AT:
    try:
        if selected is None:
            inventory = get("repos/Hexalith/Hexalith.CiCd/actions/workflows/nightly.yml/runs"
                            "?event=schedule&branch=main&created=2026-11-18&per_page=100")
            assert inventory["total_count"] <= 100, "Paginated selection requires explicit inspection"
            matches = [run for run in inventory["workflow_runs"]
                       if NIGHT_START <= run["created_at"] < NIGHT_END
                       and run["event"] == "schedule" and run["head_branch"] == "main"
                       and run["path"] == ".github/workflows/nightly.yml"]
            if matches:
                selected = min(matches, key=lambda run: (run["created_at"], run["id"]))["id"]
        if selected is not None:
            run = get("repos/Hexalith/Hexalith.CiCd/actions/runs/" + str(selected))
            assert run["id"] == selected and run["event"] == "schedule" and run["head_branch"] == "main"
            assert run["path"] == ".github/workflows/nightly.yml"
            state = (run["status"], run["conclusion"], run["run_attempt"])
            if state != previous:
                report["observations"].append({"observed_at": now(), **{key: run.get(key) for key in (
                    "id", "event", "path", "head_branch", "head_sha", "created_at", "updated_at",
                    "status", "conclusion", "run_attempt", "html_url")}})
                report["selected_run_id"] = selected
                save()
                print(json.dumps(report["observations"][-1]), flush=True)
                previous = state
            if run["status"] == "completed":
                report["result"] = "terminal parent observed; semantic acceptance not yet verified"
                break
    except (RuntimeError, AssertionError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as failure:
        error = str(failure)[:2000]
        if not report["errors"] or report["errors"][-1]["error"] != error:
            report["errors"].append({"observed_at": now(), "error": error})
            save()
    report["heartbeat_at"] = now()
    save()
    time.sleep(60)
else:
    report["result"] = "observation deadline reached; genuine scheduled checkpoint unverified"
report["observation_completed_at"] = now()
save()
print(json.dumps({"result": report["result"], "selected_run_id": report.get("selected_run_id")}), flush=True)
raise SystemExit(0 if str(report["result"]).startswith("terminal parent observed") else 1)
