"""Read-only Parties onboarding observations; never record credential values."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PROFILE = "/home/administrator/.config/gh"
PREFIX = "repos/Hexalith/Hexalith.Parties"
if any(os.environ.get(name) for name in ("GH_TOKEN", "GITHUB_TOKEN")):
    raise SystemExit("Unexpected token override present; inspect intended profile first")
ENV = dict(os.environ, GH_CONFIG_DIR=PROFILE, GH_PROMPT_DISABLED="1")
for name in ("GH_DEBUG", "GIT_CURL_VERBOSE", "GIT_TRACE", "GIT_TRACE_CURL"):
    ENV.pop(name, None)


def select(endpoint, value):
    if "/releases?" in endpoint and isinstance(value, list):
        return [{key: item.get(key) for key in (
            "id", "tag_name", "target_commitish", "draft", "prerelease",
            "immutable", "created_at", "published_at", "html_url")}
            for item in value]
    if "/tags?" in endpoint and isinstance(value, list):
        return [{key: item.get(key) for key in ("name", "commit")} for item in value]
    if not isinstance(value, dict) or "message" in value:
        return value
    if "/releases/tags/" in endpoint:
        return {key: value.get(key) for key in (
            "id", "tag_name", "target_commitish", "draft", "prerelease",
            "immutable", "created_at", "published_at", "html_url")}
    if endpoint == "user":
        return {key: value.get(key) for key in ("login", "id")}
    if endpoint == PREFIX:
        return {key: value.get(key) for key in (
            "id", "full_name", "default_branch", "permissions", "security_and_analysis")}
    if "actions/runs?" in endpoint:
        return {"total_count": value["total_count"], "runs": [
            {key: run.get(key) for key in (
                "id", "head_sha", "event", "status", "conclusion", "path",
                "created_at", "updated_at", "html_url")}
            for run in value["workflow_runs"]]}
    if endpoint.endswith("/actions/workflows"):
        return {"total_count": value["total_count"], "workflows": [
            {key: item.get(key) for key in ("id", "name", "path", "state")}
            for item in value["workflows"]]}
    if endpoint.startswith("user/installations/"):
        return {"total_count": value["total_count"],
                "repositories": [item["full_name"] for item in value["repositories"]]}
    if endpoint.endswith("/environments"):
        return {"total_count": value["total_count"], "environments": [
            {key: item.get(key) for key in (
                "name", "protection_rules", "deployment_branch_policy")}
            for item in value["environments"]]}
    return value


def get(endpoint):
    process = subprocess.run(
        ["gh", "api", "--method", "GET", "--include", endpoint],
        capture_output=True, text=True, timeout=40, env=ENV)
    headers, separator, body = process.stdout.partition("\n\n")
    if not separator:
        headers, body = "", process.stdout
    try:
        value = json.loads(body) if body.strip() else None
    except json.JSONDecodeError:
        value = {"unparsed_response": True}
    permissions = {}
    for line in headers.splitlines():
        name, separator, data = line.partition(":")
        if separator and name.lower() in (
                "x-accepted-github-permissions", "x-oauth-scopes", "x-accepted-oauth-scopes"):
            permissions[name.lower()] = data.strip()
    return {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "profile": PROFILE, "method": "GET", "endpoint": endpoint,
        "exit_code": process.returncode,
        "status": next((line for line in headers.splitlines()
                        if line.startswith("HTTP/")), "unavailable"),
        "permission_headers": permissions,
        "data": select(endpoint, value), "stderr": process.stderr.strip(),
    }


def revision(path):
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


identity = [get("user"), get(PREFIX)]
endpoints = [
    PREFIX + "/git/ref/heads/main",
    PREFIX + "/rulesets?includes_parents=true",
    PREFIX + "/environments",
    PREFIX + "/environments/hexalith-release/deployment-branch-policies",
    PREFIX + "/environments/hexalith-release/secrets",
    PREFIX + "/actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED",
    PREFIX + "/actions/permissions/artifact-and-log-retention",
    PREFIX + "/code-scanning/default-setup",
    PREFIX + "/automated-security-fixes",
    PREFIX + "/immutable-releases",
    PREFIX + "/releases?per_page=100",
    PREFIX + "/tags?per_page=100",
    PREFIX + "/actions/workflows",
    PREFIX + "/actions/runs?branch=main&per_page=20",
    "user/installations/179966090/repositories?per_page=100",
    "repos/Hexalith/Hexalith.CiCd/actions/runs?event=schedule&per_page=10",
    "repos/Hexalith/Hexalith.Builds/releases/tags/" + (ROOT / "builds-version").read_text().strip(),
]
with ThreadPoolExecutor(max_workers=5) as pool:
    results = identity + list(pool.map(get, endpoints))
report = {
    "observed_at": datetime.now(timezone.utc).isoformat(),
    "phase": "planning only; GET requests; no remote mutations",
    "default_profile": os.environ.get("GH_CONFIG_DIR", "unset"),
    "administration_profile": PROFILE,
    "token_overrides_present": {name: bool(os.environ.get(name))
                                for name in ("GH_TOKEN", "GITHUB_TOKEN")},
    "worktree": str(ROOT), "cicd_revision": revision(ROOT),
    "parties_revision": revision(ROOT / "references/Hexalith.Parties"),
    "builds_revision": revision(ROOT / "references/Hexalith.Builds"),
    "builds_version": (ROOT / "builds-version").read_text().strip(),
    "requests": results,
}
(HERE / "planning-preflight.json").write_text(json.dumps(report, indent=2) + "\n")
for result in results:
    print(result["status"], result["endpoint"], result["stderr"])
