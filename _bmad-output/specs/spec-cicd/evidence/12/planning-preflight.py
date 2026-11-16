"""Read-only story 12 planning; record metadata, never credential values."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROFILE = "/home/administrator/.config/gh"
PREFIX = "repos/Hexalith/Hexalith.AI.Tools"
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
ENV = dict(os.environ, GH_CONFIG_DIR=PROFILE, GH_PROMPT_DISABLED="1")
for key in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    ENV.pop(key, None)


def select(endpoint, value):
    if not isinstance(value, dict) or "message" in value:
        return value
    if endpoint == "user":
        return {key: value.get(key) for key in ("login", "id")}
    if endpoint == PREFIX:
        return {key: value.get(key) for key in
                ("id", "full_name", "default_branch", "permissions", "security_and_analysis")}
    if endpoint.endswith("/actions/runs?per_page=100"):
        return {"total_count": value["total_count"], "runs": [
            {key: run.get(key) for key in
             ("id", "head_sha", "event", "status", "conclusion", "path", "html_url")}
            for run in value["workflow_runs"]]}
    if endpoint.endswith("/actions/workflows"):
        return {"total_count": value["total_count"], "workflows": [
            {key: item.get(key) for key in ("id", "name", "path", "state")}
            for item in value["workflows"]]}
    if endpoint.startswith("user/installations/"):
        return {"total_count": value["total_count"], "repositories": [
            item["full_name"] for item in value["repositories"]]}
    if endpoint.endswith("/git/ref/heads/main"):
        return {"ref": value["ref"], "object": value["object"]}
    if endpoint.endswith("/environments"):
        return {"total_count": value["total_count"], "environments": [
            {key: item.get(key) for key in
             ("name", "protection_rules", "deployment_branch_policy")}
            for item in value["environments"]]}
    return value


def get(endpoint):
    process = subprocess.run(
        ["gh", "api", "--method", "GET", "--include", endpoint],
        capture_output=True, text=True, timeout=30, env=ENV)
    headers, separator, body = process.stdout.partition("\n\n")
    if not separator:
        headers, body = "", process.stdout
    try:
        value = json.loads(body) if body.strip() else None
    except json.JSONDecodeError:
        value = {"unparsed_response": True}
    permission_headers = {}
    for line in headers.splitlines():
        name, separator, data = line.partition(":")
        if separator and name.lower() in (
                "x-accepted-github-permissions", "x-oauth-scopes", "x-accepted-oauth-scopes"):
            permission_headers[name.lower()] = data.strip()
    return {"observed_at": datetime.now(timezone.utc).isoformat(),
            "method": "GET", "endpoint": endpoint, "exit_code": process.returncode,
            "status": next((line for line in headers.splitlines()
                            if line.startswith("HTTP/")), "unavailable"),
            "permission_headers": permission_headers,
            "data": select(endpoint, value), "stderr": process.stderr.strip()}


endpoints = [
    "user", PREFIX, PREFIX + "/git/ref/heads/main",
    PREFIX + "/rulesets?includes_parents=true", PREFIX + "/environments",
    PREFIX + "/actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED",
    PREFIX + "/actions/permissions/artifact-and-log-retention",
    PREFIX + "/code-scanning/default-setup", PREFIX + "/automated-security-fixes",
    PREFIX + "/immutable-releases", PREFIX + "/releases?per_page=100",
    PREFIX + "/tags?per_page=100", PREFIX + "/actions/workflows",
    PREFIX + "/actions/runs?per_page=100",
    "user/installations/179966090/repositories?per_page=100",
]
with ThreadPoolExecutor(max_workers=5) as pool:
    results = list(pool.map(get, endpoints))
report = {"observed_at": datetime.now(timezone.utc).isoformat(),
          "phase": "planning only; no remote mutations",
          "default_profile": os.environ["GH_CONFIG_DIR"],
          "administration_profile": PROFILE,
          "token_overrides": {key: key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN")},
          "requests": results}
(HERE / "planning-preflight.json").write_text(json.dumps(report, indent=2) + "\n")
for item in results:
    print(item["status"], item["endpoint"], item["stderr"])
