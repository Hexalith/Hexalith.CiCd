"""Authorized, bounded AD-21 GitHub administration for McpCli story 15.

Uses only the command-local maintainer profile. Does not read secret values,
modify module files, push product refs, adopt modules or remove legacy access.
Each API result is saved immediately so interrupted provisioning is auditable.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
MODULES = ("Hexalith.McpCli",)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("phase", choices=("cleanup", "rulesets", "environments", "settings-grants"))
arguments = parser.parse_args()
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh", GH_PROMPT_DISABLED="1")
for name in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)
path = HERE / ("provision-" + arguments.phase + ".json")
report = {"started_at": datetime.now(timezone.utc).isoformat(),
          "phase": arguments.phase, "administration_profile": environment["GH_CONFIG_DIR"],
          "default_profile": os.environ.get("GH_CONFIG_DIR"), "requests": []}
deadline = time.monotonic() + 1200


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")


def api(method, endpoint, body=None, *, allowed=(0,)):
    assert time.monotonic() < deadline, "Provisioning deadline exceeded"
    command = ["gh", "api", "--method", method, "--include", endpoint]
    if body is not None:
        command += ["--input", "-"]
    result = subprocess.run(command, input=json.dumps(body) if body is not None else None,
                            env=environment, capture_output=True, text=True, timeout=60)
    headers, _, data = result.stdout.partition("\n\n")
    value = json.loads(data) if data.strip() else None
    status = next((line for line in headers.splitlines() if line.startswith("HTTP/")), "")
    report["requests"].append({"recorded_at": datetime.now(timezone.utc).isoformat(),
        "method": method, "endpoint": endpoint, "input": body, "exit": result.returncode,
        "status": status, "data": value, "error": result.stderr.strip()})
    save()
    print(method, endpoint, status, flush=True)
    assert result.returncode in allowed, result.stderr
    return value, status


user, _ = api("GET", "user")
assert user["login"] == "jpiquot" and user["id"] == 6775094
for module in MODULES:
    prefix = "repos/Hexalith/" + module
    metadata, _ = api("GET", prefix)
    assert metadata["full_name"] == "Hexalith/" + module and metadata["default_branch"] == "main"
    if arguments.phase == "cleanup":
        analyses, status = api("GET", prefix + "/code-scanning/analyses?tool_name=CodeQL&per_page=100", allowed=(0, 1))
        assert analyses == [] or ("404" in status and analyses.get("message") == "no analysis found"), "Unexpected CodeQL inventory requires assessment"
        releases, _ = api("GET", prefix + "/releases?per_page=100")
        assert isinstance(releases, list) and len(releases) < 100
        assert not any(item["draft"] for item in releases), "Unexpected draft requires assessment"
        tags, _ = api("GET", prefix + "/git/matching-refs/tags/v")
        assert isinstance(tags, list) and len(tags) < 100
        release_tags = {item["tag_name"] for item in releases if not item["draft"]}
        assert all(item["ref"].removeprefix("refs/tags/") in release_tags for item in tags), "Unpublished version tag requires assessment"
        report["stale_state_assessment"] = {"codeql": "no analysis found; no deletion target", "unmarked_drafts": [], "orphan_version_tags": [], "cleanup_writes": 0}
    elif arguments.phase == "rulesets":
        inventory, _ = api("GET", prefix + "/rulesets?includes_parents=true")
        assert inventory == [], "Existing protection needs assessment before changing it"
        for name, target, include, types in (
                ("Protect main", "branch", "refs/heads/main", ("deletion", "non_fast_forward")),
                ("v tags", "tag", "refs/tags/v*", ("update", "deletion"))):
            body = {"name": name, "target": target, "enforcement": "active", "bypass_actors": [],
                    "conditions": {"ref_name": {"include": [include], "exclude": []}},
                    "rules": [{"type": kind} for kind in types]}
            rule, _ = api("POST", prefix + "/rulesets", body)
            detail, _ = api("GET", prefix + "/rulesets/" + str(rule["id"]))
            assert all(detail[key] == value for key, value in body.items())
    elif arguments.phase == "environments":
        environments, _ = api("GET", prefix + "/environments")
        assert not any(item["name"] == "hexalith-release" for item in environments["environments"])
        body = {"wait_timer": 0, "reviewers": [], "prevent_self_review": False,
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True}}
        api("PUT", prefix + "/environments/hexalith-release", body)
        api("POST", prefix + "/environments/hexalith-release/deployment-branch-policies",
            {"name": "main", "type": "branch"})
        policies, _ = api("GET", prefix + "/environments/hexalith-release/deployment-branch-policies")
        assert policies["total_count"] == 1
        assert policies["branch_policies"][0]["name"] == "main"
        assert policies["branch_policies"][0]["type"] == "branch"
    else:
        setup, _ = api("GET", prefix + "/code-scanning/default-setup")
        assert setup["state"] == "not-configured"
        updates, _ = api("GET", prefix + "/automated-security-fixes", allowed=(0, 1))
        assert updates is not None and updates.get("enabled") is False
        variables, _ = api("GET", prefix + "/actions/variables")
        switches = [item for item in variables["variables"] if item["name"] == "HEXALITH_RELEASE_PUBLISH_ENABLED"]
        if not switches:
            api("POST", prefix + "/actions/variables", {"name": "HEXALITH_RELEASE_PUBLISH_ENABLED", "value": "true"})
        else:
            assert len(switches) == 1 and switches[0]["value"] in ("true", "false")
        switch, _ = api("GET", prefix + "/actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED")
        assert switch["value"] in ("true", "false")
        retention, _ = api("GET", prefix + "/actions/permissions/artifact-and-log-retention")
        assert retention["days"] == 90
        assert metadata["security_and_analysis"]["secret_scanning_push_protection"]["status"] == "enabled"
        for namespace in ("actions", "dependabot"):
            for name in ("HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD"):
                endpoint = f"orgs/Hexalith/{namespace}/secrets/{name}/repositories"
                api("PUT", endpoint + "/" + str(metadata["id"]))
                repositories, _ = api("GET", endpoint)
                assert any(item["id"] == metadata["id"] for item in repositories["repositories"])
        endpoint = "orgs/Hexalith/actions/variables/HEXALITH_NUGET_USER/repositories"
        api("PUT", endpoint + "/" + str(metadata["id"]))
        repositories, _ = api("GET", endpoint)
        assert any(item["id"] == metadata["id"] for item in repositories["repositories"])
report["completed_at"] = datetime.now(timezone.utc).isoformat()
report["result"] = "pass"
save()
