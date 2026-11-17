"""Authorized story-12 live refresh. Read-only GitHub GETs and local observer status.

Never prints or stores credential values. Does not mutate repository settings,
push, dispatch, adopt, or touch the story 11 observer.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PREFIX = "repos/Hexalith/Hexalith.AI.Tools"
CICD = "repos/Hexalith/Hexalith.CiCd"
BUILDS = "repos/Hexalith/Hexalith.Builds"
MAINTAINER = "/home/administrator/.config/gh"
CICD_PROFILE = "/home/administrator/.config/gh-cicd-agent"
MODULE_PROFILE = "/home/administrator/.config/gh-module-agent"
assert os.environ.get("GH_CONFIG_DIR") == CICD_PROFILE
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))


def environment(profile):
    env = dict(os.environ, GH_CONFIG_DIR=profile, GH_PROMPT_DISABLED="1")
    for key in ("GH_DEBUG", "GIT_TRACE", "GIT_TRACE_CURL", "GIT_CURL_VERBOSE"):
        env.pop(key, None)
    return env


def get(endpoint, profile):
    process = subprocess.run(
        ["gh", "api", "--method", "GET", "--include", endpoint],
        capture_output=True, text=True, timeout=45, env=environment(profile))
    headers, separator, body = process.stdout.partition("\n\n")
    if not separator:
        headers, body = "", process.stdout
    try:
        value = json.loads(body) if body.strip() else None
    except json.JSONDecodeError:
        value = {"unparsed_response": True}
    permission_headers = {}
    for line in headers.splitlines():
        name, _, data = line.partition(":")
        if name.lower() in (
                "x-accepted-github-permissions", "x-oauth-scopes",
                "x-accepted-oauth-scopes"):
            permission_headers[name.lower()] = data.strip()
    status = next((line for line in headers.splitlines() if line.startswith("HTTP/")),
                  "unavailable")
    return {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "method": "GET",
        "endpoint": endpoint,
        "exit_code": process.returncode,
        "status": status,
        "permission_headers": permission_headers,
        "data": select(endpoint, value),
        "stderr": process.stderr.strip(),
    }


def select(endpoint, value):
    if not isinstance(value, dict) or "message" in value:
        if endpoint.endswith("/releases") and isinstance(value, list):
            return [{"id": item.get("id"), "tag_name": item.get("tag_name"),
                     "draft": item.get("draft"), "immutable": item.get("immutable"),
                     "target_commitish": item.get("target_commitish")}
                    for item in value]
        if endpoint.endswith("/tags") and isinstance(value, list):
            return [{"name": item.get("name"),
                     "commit": (item.get("commit") or {}).get("sha")}
                    for item in value]
        if endpoint.endswith("/analyses") and isinstance(value, list):
            return [{"id": item.get("id"), "tool": (item.get("tool") or {}).get("name"),
                     "ref": item.get("ref"), "commit_sha": item.get("commit_sha")}
                    for item in value]
        return value
    if endpoint == "user":
        return {key: value.get(key) for key in ("login", "id")}
    if endpoint in (PREFIX, CICD, BUILDS):
        return {key: value.get(key) for key in
                ("id", "full_name", "default_branch", "permissions",
                 "security_and_analysis")}
    if "/actions/runs" in endpoint:
        return {"total_count": value.get("total_count"), "runs": [
            {key: run.get(key) for key in
             ("id", "head_sha", "event", "status", "conclusion", "path",
              "html_url", "created_at")}
            for run in value.get("workflow_runs", [])]}
    if endpoint.endswith("/actions/workflows"):
        return {"total_count": value.get("total_count"), "workflows": [
            {key: item.get(key) for key in ("id", "name", "path", "state")}
            for item in value.get("workflows", [])]}
    if endpoint.startswith("user/installations/"):
        return {"total_count": value.get("total_count"), "repositories": [
            item.get("full_name") for item in value.get("repositories", [])]}
    if endpoint.endswith("/environments"):
        return {"total_count": value.get("total_count"), "environments": [
            {key: item.get(key) for key in
             ("name", "protection_rules", "deployment_branch_policy")}
            for item in value.get("environments", [])]}
    if endpoint.endswith("/actions/variables"):
        return {"total_count": value.get("total_count"), "variables": [
            {key: item.get(key) for key in ("name", "value")}
            for item in value.get("variables", [])]}
    if "/repositories" in endpoint and isinstance(value.get("repositories"), list):
        return {"total_count": value.get("total_count"), "repositories": [
            {key: item.get(key) for key in ("id", "full_name")}
            for item in value["repositories"]]}
    if endpoint.endswith("/releases/tags/v6.2.0"):
        return {key: value.get(key) for key in
                ("id", "tag_name", "draft", "prerelease", "immutable",
                 "author", "published_at", "target_commitish")}
    return value


observer = json.loads(
    (HERE.parent / "11" / "nightly-continuation-20261118-observation.json").read_text())
local = {
    "cicd_head": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "cicd_origin_main": subprocess.check_output(
        ["git", "rev-parse", "refs/remotes/origin/main"], cwd=ROOT, text=True).strip(),
    "ai_tools_gitlink": subprocess.check_output(
        ["git", "ls-tree", "HEAD", "references/Hexalith.AI.Tools"],
        cwd=ROOT, text=True).strip(),
    "story11_observer": {
        "result": observer.get("result"),
        "night_start": observer.get("night_start"),
        "sleeping_until": observer.get("sleeping_until"),
        "heartbeat_at": observer.get("heartbeat_at"),
        "manual_dispatch_or_rerun": observer.get("manual_dispatch_or_rerun"),
    },
}

requests = []
for endpoint, profile in (
        ("user", MAINTAINER),
        (PREFIX, MAINTAINER),
        (PREFIX + "/git/ref/heads/main", MODULE_PROFILE),
        (PREFIX + "/rulesets?includes_parents=true", MAINTAINER),
        (PREFIX + "/environments", MAINTAINER),
        (PREFIX + "/actions/variables", MAINTAINER),
        (PREFIX + "/actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED", MAINTAINER),
        (PREFIX + "/actions/permissions/artifact-and-log-retention", MAINTAINER),
        (PREFIX + "/code-scanning/default-setup", MAINTAINER),
        (PREFIX + "/automated-security-fixes", MAINTAINER),
        (PREFIX + "/immutable-releases", MAINTAINER),
        (PREFIX + "/releases?per_page=100", MAINTAINER),
        (PREFIX + "/tags?per_page=100", MAINTAINER),
        (PREFIX + "/actions/workflows", MAINTAINER),
        (PREFIX + "/actions/runs?per_page=100", MAINTAINER),
        (PREFIX + "/code-scanning/analyses?tool_name=CodeQL&per_page=100", MAINTAINER),
        ("user/installations/179966090/repositories?per_page=100", MAINTAINER),
        (CICD + "/git/ref/heads/main", CICD_PROFILE),
        (CICD + "/git/ref/heads/delivered/Hexalith.AI.Tools", CICD_PROFILE),
        (BUILDS + "/releases/tags/v6.2.0", CICD_PROFILE),
        (BUILDS + "/git/ref/tags/v6.2.0", CICD_PROFILE),
):
    requests.append(get(endpoint, profile))

metadata = next(item for item in requests if item["endpoint"] == PREFIX)
repository_id = (metadata.get("data") or {}).get("id")
if repository_id:
    for kind, names in (
            ("actions/secrets", ("HEXALITH_REGISTRY_PULL_USERNAME",
                                 "HEXALITH_REGISTRY_PULL_PASSWORD")),
            ("dependabot/secrets", ("HEXALITH_REGISTRY_PULL_USERNAME",
                                    "HEXALITH_REGISTRY_PULL_PASSWORD")),
            ("actions/variables", ("HEXALITH_NUGET_USER",)),
    ):
        for name in names:
            requests.append(get(
                f"orgs/Hexalith/{kind}/{name}/repositories", MAINTAINER))
    requests.append(get(PREFIX + "/environments/hexalith-release", MAINTAINER))
    requests.append(get(
        PREFIX + "/environments/hexalith-release/deployment-branch-policies",
        MAINTAINER))
    requests.append(get(PREFIX + "/environments/hexalith-release/secrets", MAINTAINER))

report = {
    "observed_at": datetime.now(timezone.utc).isoformat(),
    "phase": "authorized live refresh; no mutations",
    "default_profile": os.environ["GH_CONFIG_DIR"],
    "administration_profile": MAINTAINER,
    "module_profile": MODULE_PROFILE,
    "token_overrides": {key: key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN")},
    "local": local,
    "repository_id": repository_id,
    "requests": requests,
}
(HERE / "live-refresh-20261117.json").write_text(json.dumps(report, indent=2) + "\n")
for item in requests:
    print(item["status"], item["endpoint"])
