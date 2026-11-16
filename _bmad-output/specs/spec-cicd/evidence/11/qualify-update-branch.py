"""Exercise real server Update branch on the pre-delivery PRs; never merge.

Only the protected module credential is used. An explicit server refusal is a
qualification result, not a reason to switch credentials or weaken policy.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
adoption = json.loads((HERE / "authenticated-adoption.json").read_text())
assert adoption["result"] == "pass"
fresh = json.loads((HERE / "post-adoption-fresh-branch-outcomes.json").read_text())
assert fresh["result"] == "pass"
probes = json.loads((HERE / "pre-delivery-probes.json").read_text())
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")
for key in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(key, None)
destination = HERE / "post-delivery-update-branch.json"
assert not destination.exists(), "Inspect actual partial server outcome before any retry"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "candidate": adoption["candidate"],
          "default_profile": os.environ.get("GH_CONFIG_DIR"), "module_token_override_present": True,
          "genuine_pre_delivery_heads": True, "modules": {}, "requests": [], "result": "pending"}


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def api(method, endpoint, document=None):
    command = ["gh", "api", "--include", "--method", method, endpoint]
    if document is not None:
        command += ["--input", "-"]
    value = subprocess.run(command, input=json.dumps(document) if document is not None else None,
                           env=environment, capture_output=True, text=True, timeout=60)
    headers, _, body = value.stdout.partition("\n\n")
    status = next(line for line in headers.splitlines() if line.startswith("HTTP/"))
    data = json.loads(body) if body.strip() else None
    report["requests"].append({"at": datetime.now(timezone.utc).isoformat(), "method": method, "endpoint": endpoint,
                                 "input": document, "status": status, "exit": value.returncode,
                                 "data": data, "error": value.stderr})
    save()
    return data, status, value.returncode


def get(endpoint):
    data, _, status = api("GET", endpoint)
    assert status == 0
    return data


report["account"] = {key: value for key, value in get("user").items() if key in {"login", "id"}}
for name, prior in probes["modules"].items():
    prefix = "repos/Hexalith/" + name
    metadata = get(prefix)
    number = prior["pull_request_number"]
    pr_endpoint = prefix + "/pulls/" + str(number)
    pull = get(pr_endpoint)
    main = get(prefix + "/git/ref/heads/main")["object"]["sha"]
    assert main == adoption["modules"][name]["adoption_sha"]
    assert pull["state"] == "open" and pull["merged"] is False
    assert pull["head"]["sha"] == prior["head"] and pull["head"]["ref"] == prior["branch"]
    assert pull["base"]["ref"] == "main"
    source = ROOT / "references" / name
    changed = subprocess.run(["git", "diff", "--name-only", prior["head"], main, "--", ".github/workflows"],
                             cwd=source, capture_output=True, text=True, check=True).stdout.splitlines()
    assert changed, "Update branch must cross the actual delivered workflow difference"
    row = {"pull_request_number": number, "url": pull["html_url"], "old_head": prior["head"], "main": main,
           "workflow_paths_differing_before_operation": changed, "permissions_metadata": metadata.get("permissions"),
           "attempted_at": datetime.now(timezone.utc).isoformat(), "operation": "PUT pull update-branch with expected_head_sha",
           "merged": False}
    report["modules"][name] = row
    save()
    data, status, exit_status = api("PUT", pr_endpoint + "/update-branch", {"expected_head_sha": prior["head"]})
    row.update(http_status=status, response=data, exit=exit_status)
    save()
    if "403" in status:
        assert exit_status != 0
        row["outcome"] = "server refused meaningful workflow-different Update branch with protected module token"
        current = get(pr_endpoint)
        assert current["head"]["sha"] == prior["head"] and current["merged"] is False
        row["head_unchanged_after_refusal"] = True
    elif "202" in status:
        assert exit_status == 0
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            current = get(pr_endpoint)
            assert current["merged"] is False
            if current["head"]["sha"] != prior["head"]:
                row.update(outcome="server accepted meaningful workflow-different Update branch with protected module token",
                           new_head=current["head"]["sha"])
                fetch = subprocess.run(["git", "fetch", "--no-recurse-submodules", "origin", "refs/heads/" + prior["branch"]],
                                       cwd=source, env=environment, capture_output=True, text=True, check=True, timeout=120)
                row["updated_head_fetch"] = {"exit": fetch.returncode, "stderr": fetch.stderr}
                parents = subprocess.run(["git", "show", "-s", "--format=%P", row["new_head"]], cwd=source,
                                         capture_output=True, text=True, check=True).stdout.strip().split()
                assert parents == [prior["head"], main]
                row["updated_head_parents"] = parents
                delta = subprocess.run(["git", "diff", "--name-only", main, row["new_head"]], cwd=source,
                                      capture_output=True, text=True, check=True).stdout.splitlines()
                assert delta == ["pilot-ci-probe.md"], "Inspect unexpected server merge content before policy qualification"
                row["updated_head_vs_adopted_main_paths"] = delta
                row["all_adopted_workflow_and_other_owned_bytes_modes_gitlinks_imported_exactly"] = True
                break
            time.sleep(5)
        else:
            raise AssertionError("Server accepted request but changed PR head remains unverified; do not retry")
    else:
        row["outcome"] = "unclassified server response; permission qualification remains unresolved"
        save()
        raise AssertionError("Unexpected Update branch response: " + status)
    save()
report.update(result="qualified actual server outcomes; canonical policy confirmation/correction still required",
              completed_at=datetime.now(timezone.utc).isoformat())
save()
print(json.dumps(report["modules"], indent=2))
