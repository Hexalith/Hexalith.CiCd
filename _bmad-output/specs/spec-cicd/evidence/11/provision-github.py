"""Authorized, bounded AD-21 GitHub administration for the two story 11 pilots.

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
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
TAGS = {
    "Hexalith.Commons": {"v2.30.2": "6646e37ed4abc380333f11c22908ac40a6b80abf"},
    "Hexalith.PolymorphicSerializations": {
        "v1.19.0": "5ef1b2773b651c264f1c1506ec4623d35e40e977",
        "v1.19.4": "98de6e013840ece9f0fa7c68ab7dcdf2bba3b375"},
}
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
        # AD-21 retires the old CodeQL configuration. Preserve other tools.
        for _ in range(500):
            analyses, _ = api("GET", prefix + "/code-scanning/analyses?tool_name=CodeQL&per_page=100")
            assert isinstance(analyses, list)
            if not analyses:
                break
            assert all(item["tool"]["name"] == "CodeQL"
                       and item["analysis_key"] == ".github/workflows/codeql.yml:analyze"
                       for item in analyses), "Unexpected CodeQL configuration; assess before deletion"
            heads = [item for item in analyses if item["deletable"] is True]
            assert heads, "No deletable CodeQL analysis in the bounded inventory"
            for item in heads:
                endpoint = prefix + "/code-scanning/analyses/" + str(item["id"]) + "?confirm_delete=true"
                for _ in range(1000):
                    value, _ = api("DELETE", endpoint)
                    next_url = value["confirm_delete_url"]
                    if next_url is None:
                        break
                    expected = "https://api.github.com/" + prefix + "/code-scanning/analyses/"
                    assert next_url.startswith(expected)
                    assert re.fullmatch(r"[0-9]+\?confirm_delete(?:=true)?", next_url[len(expected):])
                    endpoint = next_url.removeprefix("https://api.github.com/")
                else:
                    raise AssertionError("CodeQL chain bound exceeded")
        else:
            raise AssertionError("CodeQL inventory bound exceeded")
        releases, _ = api("GET", prefix + "/releases?per_page=100")
        assert isinstance(releases, list) and len(releases) < 100
        assert not any(item["draft"] for item in releases), "Unexpected draft needs assessment"
        for tag, sha in TAGS[module].items():
            assert not any(item["tag_name"] == tag for item in releases)
            reference, status = api("GET", prefix + "/git/ref/tags/" + tag, allowed=(0, 1))
            if "404" in status:
                continue
            assert "200" in status and reference["ref"] == "refs/tags/" + tag
            assert reference["object"] == {"sha": sha, "type": "commit",
                                          "url": "https://api.github.com/" + prefix + "/git/commits/" + sha}
            api("DELETE", prefix + "/git/refs/tags/" + tag)
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
        assert len(switches) == 1 and switches[0]["value"] in ("true", "false")
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
