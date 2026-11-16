"""Retire only regenerated pre-adoption CodeQL configuration analyses.

New shared ci.yml analyses and every other tool remain untouched. Each chained
deletion target is re-read and bound to the exact legacy analysis key first.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
adoption = json.loads((HERE / "authenticated-adoption.json").read_text())
assert adoption["result"] == "pass"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh", GH_PROMPT_DISABLED="1")
destination = HERE / "post-adoption-legacy-codeql-cleanup.json"
assert not destination.exists(), "Inspect saved partial configuration cleanup before retrying"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "candidate": adoption["candidate"],
          "target_analysis_key": ".github/workflows/codeql.yml:analyze", "requests": [], "modules": {}, "result": "pending"}


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def api(method, endpoint):
    value = subprocess.run(["gh", "api", "--method", method, endpoint], env=environment,
                           capture_output=True, text=True, timeout=60)
    data = json.loads(value.stdout) if value.stdout.strip() else None
    report["requests"].append({"at": datetime.now(timezone.utc).isoformat(), "method": method,
                                 "endpoint": endpoint, "exit": value.returncode, "data": data, "error": value.stderr})
    save()
    assert value.returncode == 0, value.stderr
    return data


for name in adoption["modules"]:
    prefix = "repos/Hexalith/" + name + "/code-scanning/analyses"
    deleted = []
    for _ in range(500):
        items = []
        for page in range(1, 101):
            rows = api("GET", prefix + "?tool_name=CodeQL&per_page=100&page=" + str(page))
            assert isinstance(rows, list)
            items.extend(rows)
            if len(rows) < 100:
                break
        else:
            raise AssertionError("CodeQL inventory bound exceeded")
        legacy = [item for item in items if item["analysis_key"] == report["target_analysis_key"]]
        if not legacy:
            report["modules"][name] = {"legacy_analysis_ids_deleted": deleted,
                "remaining_codeql_configurations": sorted({item["analysis_key"] for item in items}),
                "other_configuration_deletions": 0, "legacy_configuration_absent": True}
            save()
            break
        heads = [item for item in legacy if item["deletable"] is True]
        assert heads, "Legacy configuration has no deletable head; inspect exact API refusal"
        for first in heads:
            endpoint = prefix + "/" + str(first["id"])
            for _ in range(1000):
                detail = api("GET", endpoint)
                assert detail["tool"]["name"] == "CodeQL" and detail["analysis_key"] == report["target_analysis_key"]
                identity = detail["id"]
                result = api("DELETE", endpoint + "?confirm_delete=true")
                deleted.append(identity)
                next_url = result["confirm_delete_url"]
                if next_url is None:
                    break
                expected = "https://api.github.com/" + prefix + "/"
                assert next_url.startswith(expected)
                suffix = next_url[len(expected):]
                match = re.fullmatch(r"([0-9]+)\?confirm_delete(?:=true)?", suffix)
                assert match
                endpoint = prefix + "/" + match[1]
            else:
                raise AssertionError("Legacy-only deletion chain bound exceeded")
            # Re-inventory after one chain; concurrent API heads may now have
            # disappeared as part of the confirmed legacy chain.
            break
    else:
        raise AssertionError("Legacy configuration cleanup bound exceeded")
report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat())
save()
print(json.dumps(report["modules"], indent=2))
