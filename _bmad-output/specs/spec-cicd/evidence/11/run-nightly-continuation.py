"""Observe only the genuine scheduled event, then resume authorized BMAD work."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PROFILE = "/home/administrator/.config/gh-cicd-agent"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
assert os.environ.get("GH_CONFIG_DIR") == PROFILE
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
assert (HERE / "nightly-continuation-prompt.md").is_file()
environment = dict(os.environ, GH_CONFIG_DIR=PROFILE, GH_PROMPT_DISABLED="1")


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
                      "token_overrides_present": False, "remote_mutation": False}))
    raise SystemExit(0)

path = HERE / "nightly-continuation-observation.json"
assert not path.exists(), "Inspect the existing run binding rather than launching duplicate observation"
report = {"started_at": now(), "expected_event": "schedule", "expected_date_utc": "2026-11-17",
          "expected_cron_utc": "17 2 * * *", "profile": PROFILE, "login": identity["login"],
          "observations": [], "errors": [], "result": "waiting; not accepted"}


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")


save()
deadline = time.monotonic() + 18 * 3600
selected = None
previous = None
while time.monotonic() < deadline:
    try:
        if selected is None:
            inventory = get("repos/Hexalith/Hexalith.CiCd/actions/workflows/nightly.yml/runs"
                            "?event=schedule&branch=main&created=2026-11-17&per_page=100")
            assert inventory["total_count"] <= 100, "Paginated selection requires explicit inspection"
            matches = [run for run in inventory["workflow_runs"]
                       if "2026-11-17T02:17:00Z" <= run["created_at"] < "2026-11-18T00:00:00Z"
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
    except (RuntimeError, AssertionError, ValueError, subprocess.SubprocessError) as failure:
        error = str(failure)[:2000]
        if not report["errors"] or report["errors"][-1]["error"] != error:
            report["errors"].append({"observed_at": now(), "error": error})
            save()
    time.sleep(60)
else:
    report["result"] = "observation deadline reached; genuine scheduled checkpoint unverified"
report["observation_completed_at"] = now()
save()

prompt = (HERE / "nightly-continuation-prompt.md").read_text()
log = HERE / "nightly-continuation-agent.jsonl"
with log.open("w") as output:
    process = subprocess.Popen(["/home/administrator/.local/bin/codex", "exec", "--json",
        "--sandbox", "danger-full-access", "-c", 'approval_policy="never"', "--cd", str(ROOT),
        "--output-last-message", str(HERE / "nightly-continuation-final.md"), "-"],
        cwd=ROOT, env=environment, stdin=subprocess.PIPE, stdout=output,
        stderr=subprocess.STDOUT, text=True, start_new_session=True)
    report["agent_started_at"] = now()
    report["agent_pid"] = process.pid
    save()
    try:
        process.communicate(prompt, timeout=4 * 3600)
        report["agent_exit"] = process.returncode
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        report["agent_completed_at"] = now()
        report["agent_exit"] = process.returncode
        save()
raise SystemExit(process.returncode)
