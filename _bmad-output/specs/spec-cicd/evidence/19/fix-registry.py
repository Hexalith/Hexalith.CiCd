"""Provision only ChatBot's isolated Zot identity and environment secrets.

Credentials remain in memory and pass to GitHub/Kubernetes through stdin.
Existing htpasswd rows, grants and configuration are preserved. This is the
authorized AD-21 additive provisioning step, not post-adoption revocation.
"""
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import urllib.error
import urllib.request

import bcrypt

HERE = Path(__file__).resolve().parent
KUBE = ["kubectl", "--context", "jpiquot@local", "-n", "registry-distribution"]
MODULES = {
    "Hexalith.ChatBot": ("hexalith-chatbot-publish", ["hexalith-chatbot-server", "hexalith-chatbot-ui"]),
}
selection = json.loads((HERE / "app-selection-verification.json").read_text())
assert selection["installation_id"] == 179966090
assert "Hexalith.ChatBot" in selection["selected_repositories"] and selection["saved"] is True

assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh", GH_PROMPT_DISABLED="1")
for name in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)
report = {"started_at": datetime.now(timezone.utc).isoformat(),
          "context": "jpiquot@local", "namespace": "registry-distribution",
          "administration_profile": environment["GH_CONFIG_DIR"], "operations": []}
path = HERE / "fix-registry.json"


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")


def command(arguments, *, payload=None, env=None, label=None, timeout=60):
    result = subprocess.run(arguments, input=payload, env=env, capture_output=True, timeout=timeout)
    # Never persist stdout/stderr from operations that carry secret data.
    report["operations"].append({"recorded_at": datetime.now(timezone.utc).isoformat(),
                                 "operation": label or " ".join(arguments), "exit": result.returncode})
    save()
    assert result.returncode == 0, (label or arguments[0]) + " failed; inspect authorized metadata without credentials"
    print(label or " ".join(arguments), "exit", result.returncode, flush=True)
    return result.stdout


def get(kind, name):
    return json.loads(command(KUBE + ["get", kind, name, "-o", "json"]))


def patch(kind, name, value):
    return command(KUBE + ["patch", kind, name, "--type=json", "--patch-file", "/dev/stdin"],
                   payload=json.dumps(value).encode(), label="patch " + kind + " " + name)


account = json.loads(command(["gh", "api", "user"], env=environment, label="verify maintainer account"))
assert account["login"] == "jpiquot" and account["id"] == 6775094
configmap = get("configmap", "distribution-registry-config")
secret = get("secret", "distribution-registry-htpasswd")
deployment = get("deployment", "distribution-registry")
original = json.loads(configmap["data"]["config.json"])
original_passwords = base64.b64decode(secret["data"]["htpasswd"])
names = [row.split(b":", 1)[0].decode() for row in original_passwords.splitlines() if row]
assert original_passwords.endswith(b"\n"), "Assess unexpected htpasswd format before changing it"
assert deployment["spec"]["replicas"] == 1 and deployment["spec"]["strategy"]["type"] == "Recreate"
updated = copy.deepcopy(original)
acl = updated["http"]["accessControl"]
base_policy = copy.deepcopy(acl["repositories"]["**"])
assert not any(username in names for username, _ in MODULES.values()), "Existing module identity needs separate assessment"
assert not any(username in policy.get("users", [])
               for username, _ in MODULES.values()
               for scope in acl["repositories"].values() for policy in scope.get("policies", []))
credentials = {}
new_passwords = original_passwords
for module, (username, scopes) in MODULES.items():
    password = secrets.token_hex(24)
    credentials[module] = (username, password, scopes)
    for scope in scopes:
        assert scope not in acl["repositories"], "Existing namespace ACL needs separate assessment"
        policy = copy.deepcopy(base_policy)
        policy["policies"].append({"users": [username], "actions": ["read", "create", "update"]})
        acl["repositories"][scope] = policy
    new_passwords += username.encode() + b":" + bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)) + b"\n"
    for key, value in (("HEXALITH_REGISTRY_USERNAME", username), ("HEXALITH_REGISTRY_PASSWORD", password)):
        command(["gh", "secret", "set", key, "--repo", "Hexalith/" + module, "--env", "hexalith-release"],
                payload=value.encode(), env=environment,
                label="set " + module + " hexalith-release " + key)
    report.setdefault("identities", {})[module] = {
        "username": username, "repository_patterns": scopes,
        "actions": ["read", "create", "update"], "admin_actions": [], "bcrypt_cost": 12,
        "secret_values_persisted_locally": False,
    }
    save()

assert new_passwords.startswith(original_passwords)
patch("secret", "distribution-registry-htpasswd", [
    {"op": "test", "path": "/metadata/resourceVersion", "value": secret["metadata"]["resourceVersion"]},
    {"op": "replace", "path": "/data/htpasswd", "value": base64.b64encode(new_passwords).decode()}])
rendered = json.dumps(updated, indent=2) + "\n"
patch("configmap", "distribution-registry-config", [
    {"op": "test", "path": "/metadata/resourceVersion", "value": configmap["metadata"]["resourceVersion"]},
    {"op": "replace", "path": "/data/config.json", "value": rendered}])
digest = hashlib.sha256(rendered.encode()).hexdigest()
annotations = dict(deployment["spec"]["template"]["metadata"].get("annotations", {}))
annotations["hexalith.com/story-19-chatbot-config-sha256"] = digest
patch("deployment", "distribution-registry", [
    {"op": "test", "path": "/metadata/resourceVersion", "value": deployment["metadata"]["resourceVersion"]},
    {"op": "add", "path": "/spec/template/metadata/annotations", "value": annotations}])
command(KUBE + ["rollout", "status", "deployment/distribution-registry", "--timeout=150s"], timeout=160)
current_configmap = get("configmap", "distribution-registry-config")
current_secret = get("secret", "distribution-registry-htpasswd")
current_deployment = get("deployment", "distribution-registry")
assert json.loads(current_configmap["data"]["config.json"]) == updated
assert base64.b64decode(current_secret["data"]["htpasswd"]) == new_passwords
assert current_deployment["status"].get("availableReplicas") == 1
old_configuration = copy.deepcopy(updated)
for _, scopes in MODULES.values():
    for scope in scopes:
        del old_configuration["http"]["accessControl"]["repositories"][scope]
assert old_configuration == original
report["preservation"] = {"old_htpasswd_rows_byte_identical": True,
                          "existing_configuration_and_grants_unchanged": True,
                          "legacy_access_removed": False,
                          "configuration_sha256": digest}
report["resourceVersions"] = {
    "secret_before": secret["metadata"]["resourceVersion"],
    "secret_after": current_secret["metadata"]["resourceVersion"],
    "configmap_before": configmap["metadata"]["resourceVersion"],
    "configmap_after": current_configmap["metadata"]["resourceVersion"],
    "deployment_before": deployment["metadata"]["resourceVersion"],
    "deployment_after": current_deployment["metadata"]["resourceVersion"],
}
report["authentication"] = []
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for module, (username, password, scopes) in credentials.items():
    authorization = "Basic " + base64.b64encode((username + ":" + password).encode()).decode()
    other = "commons"
    for method, endpoint, expected in (
            ("GET", "/v2/", 200),
            ("POST", "/v2/" + other + "/blobs/uploads/", 403),
            ("POST", "/v2/story-19-unrelated/blobs/uploads/", 403)):
        request = urllib.request.Request("https://registry.hexalith.com" + endpoint,
                                         headers={"Authorization": authorization}, method=method)
        try:
            with opener.open(request, timeout=30) as response:
                status = response.status
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
        report["authentication"].append({"repository": module, "username": username,
                                          "method": method, "endpoint": endpoint,
                                          "status": status, "expected": expected})
        save()
        assert status == expected, "Unexpected registry authentication/foreign-write response"
    metadata = json.loads(command(["gh", "api", "repos/Hexalith/" + module
                                    + "/environments/hexalith-release/secrets"], env=environment,
                                  label="read " + module + " environment secret metadata"))
    names = sorted(item["name"] for item in metadata["secrets"])
    assert names == ["HEXALITH_REGISTRY_PASSWORD", "HEXALITH_REGISTRY_USERNAME"]
    report["identities"][module]["environment_secret_names"] = names
report["verification_limits"] = [
    "Authenticated registry access and foreign-write refusals are real server results.",
    "Own namespace read/create/update grants are verified from preserved live ACL and restarted workload; no package/image or upload was created.",
    "No legacy registry identity or credential was revoked before adoption."]
report["completed_at"] = datetime.now(timezone.utc).isoformat()
report["result"] = "pass"
save()
print("ChatBot Zot identity and environment-secret provisioning passed.", flush=True)
