"""Authorized, bounded AD-21 GitHub administration for Works story 13.

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
MODULE = "Hexalith.Works"
REPOSITORY_ID = 1264171182
PREFIX = "repos/Hexalith/" + MODULE
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("phase", choices=("cleanup", "rulesets", "environments", "settings-grants"))
arguments = parser.parse_args()
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh", GH_PROMPT_DISABLED="1")
for name in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)
path = HERE / ("provision-" + arguments.phase + ".json")
assert not path.exists(), "Assess retained partial operations before a retry"
report = {"started_at": datetime.now(timezone.utc).isoformat(),
          "phase": arguments.phase, "module": MODULE, "repository_id": REPOSITORY_ID,
          "administration_profile": environment["GH_CONFIG_DIR"],
          "default_profile": os.environ.get("GH_CONFIG_DIR"), "requests": []}
deadline = time.monotonic() + 1200


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")
    path.chmod(0o600)


def require_packet(name):
    packet = json.loads((HERE / name).read_text())
    assert packet.get("result") == "pass" or packet.get("verified") is True, name + " is incomplete"
    return packet


def result_ok(status):
    return status.startswith("HTTP/") and any(code in status for code in (" 200 ", " 201 ", " 204 "))


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


try:
    selection = require_packet("app-selection-verified.json")
    assert "Hexalith.Works" in selection["observation"]["selected"]
    assert selection["observation"]["only_selected"] and not selection["observation"]["save_enabled"]
    user, _ = api("GET", "user")
    assert user["login"] == "jpiquot" and user["id"] == 6775094
    metadata, _ = api("GET", PREFIX)
    assert metadata["full_name"] == "Hexalith/" + MODULE and metadata["id"] == REPOSITORY_ID
    assert metadata["default_branch"] == "main"

    if arguments.phase == "cleanup":
        for _ in range(500):
            analyses, status = api("GET", PREFIX + "/code-scanning/analyses?tool_name=CodeQL&per_page=100",
                                   allowed=(0, 1))
            if "404" in status and isinstance(analyses, dict) and analyses.get("message") == "no analysis found":
                analyses = []
            assert isinstance(analyses, list)
            if not analyses:
                break
            assert all(item["tool"]["name"] == "CodeQL"
                       and item["analysis_key"] == ".github/workflows/codeql.yml:analyze"
                       for item in analyses), "Unexpected CodeQL configuration; assess before deletion"
            heads = [item for item in analyses if item["deletable"] is True]
            assert heads, "No deletable CodeQL analysis in the bounded inventory"
            for item in heads:
                endpoint = PREFIX + "/code-scanning/analyses/" + str(item["id"]) + "?confirm_delete=true"
                for _ in range(1000):
                    value, status = api("DELETE", endpoint, allowed=(0, 1))
                    if "404" in status and isinstance(value, dict) and value.get("message", "").startswith("No analysis found"):
                        break
                    assert result_ok(status), status
                    next_url = value["confirm_delete_url"]
                    if next_url is None:
                        break
                    expected = "https://api.github.com/" + PREFIX + "/code-scanning/analyses/"
                    assert next_url.startswith(expected)
                    assert re.fullmatch(r"[0-9]+\?confirm_delete(?:=true)?", next_url[len(expected):])
                    endpoint = next_url.removeprefix("https://api.github.com/")
                else:
                    raise AssertionError("CodeQL chain bound exceeded")
        else:
            raise AssertionError("CodeQL inventory bound exceeded")
        releases, _ = api("GET", PREFIX + "/releases?per_page=100")
        assert isinstance(releases, list) and len(releases) < 100
        assert not any(item["draft"] for item in releases), "Unexpected draft requires assessment"
        assessed = json.loads((HERE / "legacy-tag-cleanup-assessment.json").read_text())["assessment"]
        candidates = [item for item in assessed
                      if item["disposition"].startswith("assessed incomplete")
                      and not item["published_packages"] and not item["github_release"]]
        published = {item["tag_name"] for item in releases if not item["draft"]}
        tags, _ = api("GET", PREFIX + "/git/matching-refs/tags/v")
        assert isinstance(tags, list) and len(tags) < 100
        before = {item["ref"].removeprefix("refs/tags/"): item["object"]["sha"] for item in tags}
        inventory, _ = api("GET", PREFIX + "/rulesets?includes_parents=true")
        assert not any(item["target"] == "tag" and item["enforcement"] == "active" for item in inventory), (
            "Tag rules changed; assess before cleanup")
        report["deleted_tags"] = []
        for item in candidates:
            name = item["tag"]
            assert name not in published
            reference, _ = api("GET", PREFIX + "/git/ref/tags/" + name)
            assert reference["ref"] == "refs/tags/" + name
            assert reference["object"]["sha"] == item["sha"] or before[name] == item["sha"]
            if reference["object"]["type"] == "commit":
                assert reference["object"]["sha"] == item["sha"]
            api("DELETE", PREFIX + "/git/refs/tags/" + name)
            report["deleted_tags"].append({"tag": name, "sha": item["sha"]})
            save()
        after_tags, _ = api("GET", PREFIX + "/git/matching-refs/tags/v")
        after = {item["ref"].removeprefix("refs/tags/") for item in after_tags}
        removed = {item["tag"] for item in candidates}
        assert not removed.intersection(after)
        assert published.issubset(after)
        report["stale_state_assessment"] = {
            "codeql": "legacy CodeQL analyses deleted or already absent",
            "unmarked_drafts": [], "orphan_version_tags": [item["tag"] for item in candidates],
            "cleanup_writes": len(report["deleted_tags"])}

    elif arguments.phase == "rulesets":
        require_packet("provision-cleanup.json")
        desired = [
            {"name": "Protect main", "target": "branch", "enforcement": "active", "bypass_actors": [],
             "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
             "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}]},
            {"name": "v tags", "target": "tag", "enforcement": "active", "bypass_actors": [],
             "conditions": {"ref_name": {"include": ["refs/tags/v*"], "exclude": []}},
             "rules": [{"type": "update"}, {"type": "deletion"}]},
        ]
        inventory, _ = api("GET", PREFIX + "/rulesets?includes_parents=true")
        assert isinstance(inventory, list)
        assert all(item["source"] == "Hexalith/" + MODULE for item in inventory), (
            "Existing protection needs assessment before changing it")
        names = {item["name"] for item in inventory}
        for definition in desired:
            matches = [item for item in inventory if item["name"] == definition["name"]]
            assert len(matches) <= 1
            if not matches:
                api("POST", PREFIX + "/rulesets", definition)
        actual, _ = api("GET", PREFIX + "/rulesets?includes_parents=true")
        assert {item["name"] for item in actual} == {item["name"] for item in desired}
        assert len(actual) == 2
        for item in actual:
            detail, _ = api("GET", PREFIX + "/rulesets/" + str(item["id"]))
            wanted = next(entry for entry in desired if entry["name"] == item["name"])
            assert all(detail.get(key) == value for key, value in wanted.items())
        report["exact_rulesets_verified"] = True
        report["ruleset_writes"] = 0 if names == {item["name"] for item in desired} else "created missing"

    elif arguments.phase == "environments":
        require_packet("provision-rulesets.json")
        environments, _ = api("GET", PREFIX + "/environments")
        foreign = [item["name"] for item in environments["environments"] if item["name"] != "hexalith-release"]
        if not any(item["name"] == "hexalith-release" for item in environments["environments"]):
            body = {"wait_timer": 0, "reviewers": [], "prevent_self_review": False,
                    "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True}}
            api("PUT", PREFIX + "/environments/hexalith-release", body)
        detail, _ = api("GET", PREFIX + "/environments/hexalith-release")
        assert detail["deployment_branch_policy"] == {
            "protected_branches": False, "custom_branch_policies": True}
        policies, status = api("GET", PREFIX + "/environments/hexalith-release/deployment-branch-policies")
        existing = policies.get("branch_policies", []) if isinstance(policies, dict) else []
        if not existing:
            api("POST", PREFIX + "/environments/hexalith-release/deployment-branch-policies",
                {"name": "main", "type": "branch"})
        policies, _ = api("GET", PREFIX + "/environments/hexalith-release/deployment-branch-policies")
        assert policies["total_count"] == 1
        assert policies["branch_policies"][0]["name"] == "main"
        assert policies["branch_policies"][0]["type"] == "branch"
        report.update(main_only_release_environment_verified=True,
                      foreign_environments=foreign, legacy_access_removed=False)

    else:
        require_packet("provision-registry.json")
        require_packet("nuget-policy-verification.json")
        setup, _ = api("GET", PREFIX + "/code-scanning/default-setup")
        assert setup["state"] == "not-configured"
        updates, _ = api("GET", PREFIX + "/automated-security-fixes", allowed=(0, 1))
        assert updates is not None and updates.get("enabled") is False
        variables, _ = api("GET", PREFIX + "/actions/variables")
        switches = [item for item in variables["variables"] if item["name"] == "HEXALITH_RELEASE_PUBLISH_ENABLED"]
        if not switches:
            api("POST", PREFIX + "/actions/variables",
                {"name": "HEXALITH_RELEASE_PUBLISH_ENABLED", "value": "true"})
        else:
            assert len(switches) == 1 and switches[0]["value"] == "true", (
                "Assess the existing publication switch before changing intent")
        switch, _ = api("GET", PREFIX + "/actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED")
        assert switch["value"] == "true"
        retention, _ = api("GET", PREFIX + "/actions/permissions/artifact-and-log-retention")
        assert retention["days"] == 90
        assert metadata["security_and_analysis"]["secret_scanning_push_protection"]["status"] == "enabled"
        for kind, names in (
                ("actions/secrets", ("HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD")),
                ("dependabot/secrets", ("HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD")),
                ("actions/variables", ("HEXALITH_NUGET_USER",)),
        ):
            for name in names:
                endpoint = f"orgs/Hexalith/{kind}/{name}"
                visibility, _ = api("GET", endpoint)
                assert visibility["visibility"] == "selected"
                before, _ = api("GET", endpoint + "/repositories")
                before_ids = {item["id"] for item in before["repositories"]}
                if REPOSITORY_ID not in before_ids:
                    api("PUT", endpoint + "/repositories/" + str(REPOSITORY_ID))
                after, _ = api("GET", endpoint + "/repositories")
                after_ids = {item["id"] for item in after["repositories"]}
                assert after_ids == before_ids | {REPOSITORY_ID}
        report.update(shared_grants_verified=True, legacy_access_removed=False)

    report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat())
    save()
    print(json.dumps({"phase": arguments.phase, "result": "pass"}, indent=2), flush=True)
except Exception:
    report.update(result="incomplete", stopped_at=datetime.now(timezone.utc).isoformat())
    save()
    raise
