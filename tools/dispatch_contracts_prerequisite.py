"""Dispatch only the two approved owner release profiles, with no automatic retry.

Committed source is read with the Contents API at a full commit identity and
verified against its Git blob identity. No target checkout, subprocess, module
code, configurable URL, or credential-bearing Git process is involved.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

_SPEC = importlib.util.spec_from_file_location(
    "_contracts_dispatch_runtime", Path(__file__).with_name("delivery_runtime.py"))
rt = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = rt
_SPEC.loader.exec_module(rt)

OWNERS = {"eventstore": "Hexalith.EventStore", "projects": "Hexalith.Projects"}
OPERATIONS = {"publish": "contracts-prerequisite", "verify": "contracts-prerequisite-verify"}
WORKFLOW = ".github/workflows/dispatch-contracts-prerequisites.yml"
RELEASE = ".github/workflows/release.yml"
SCHEMA = "hexalith.contracts-prerequisites-dispatch.v1"
OWNER_PREFIX = "/repos/Hexalith/Hexalith.CiCd"
MAX_RUNS = 1000
POLL_SECONDS = 60
POLICY_PROPOSAL = "docs/proposals/contracts-prerequisites/projects-prerequisite-policy.json"
POLICY_PATHS = {"tests/tools/run-ci-workflow-gates.ps1", "tests/tools/test_run_ci_workflow_gates.py"}
MISSING = object()


def require(condition, message):
    if not condition:
        raise rt.DeliveryError(message)


def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def proposal_path(owner):
    return "docs/proposals/contracts-prerequisites/" + owner + "-publisher.json"


def source_paths(owner):
    return ("tools/dispatch_contracts_prerequisite.py", "tools/delivery_runtime.py", WORKFLOW,
            "tools/tests/test_dispatch_contracts_prerequisite.py", proposal_path(owner))


class APIError(rt.DeliveryError):
    def __init__(self, message, details):
        super().__init__(message)
        self.details = details


class Interrupted(rt.DeliveryError):
    pass


class API:
    """One fixed API origin, no redirects/proxies/retries, bounded bodies/time."""
    def __init__(self, *, opener=None):
        self.opener = opener or build_opener(ProxyHandler({}), rt.NoRedirect())

    def request(self, method, path, token=None, *, payload=None, timeout=30, absent=False):
        # Every caller constructs paths from constants, closed choices and full
        # validated SHAs. This second boundary also forbids origin/path escapes.
        require(method in {"GET", "POST"} and isinstance(path, str)
                and path.startswith(("/repos/Hexalith/", "/installation/repositories?"))
                and not any(c in path for c in ("\r", "\n", "#", "\\", "%", ":"))
                and not any(p in {".", ".."} for p in path.split("?", 1)[0].split("/")),
                "noncanonical fixed GitHub API request")
        if method == "POST":
            require(path in {"/repos/Hexalith/" + repo + "/actions/workflows/release.yml/dispatches"
                             for repo in OWNERS.values()}
                    and payload in ({"ref": "main", "inputs": {"release-profile": profile}}
                                    for profile in OPERATIONS.values()) and token,
                    "write outside fixed release dispatch refused")
        else:
            require(payload is None, "GET payload refused")
        if absent:
            prefix = OWNER_PREFIX + "/contents/" + POLICY_PROPOSAL + "?ref="
            require(method == "GET" and path.startswith(prefix)
                    and rt.SHA.fullmatch(path.removeprefix(prefix)),
                    "absence is permitted only for the fixed exact-source policy proposal")
        require(0 < timeout <= 30, "invalid bounded API timeout")
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2026-03-10",
                   "User-Agent": "Hexalith-CiCd-contracts-prerequisite-dispatch"}
        if token is not None:
            require(token, "scoped owner App token unavailable")
            headers["Authorization"] = "Bearer " + token
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("ascii")
        if data is not None:
            headers["Content-Type"] = "application/json"
        details = {"method": method, "path": path.split("?", 1)[0], "status": None, "request_id": None}
        try:
            request = Request("https://api.github.com" + path, headers=headers, data=data, method=method)
            with self.opener.open(request, timeout=timeout) as response:
                details.update(status=response.status,
                               request_id=rt.clean(response.headers.get("X-GitHub-Request-Id", "")))
                body = response.read(rt.MAX_JSON + 1)
                require(len(body) <= rt.MAX_JSON, "GitHub API body exceeds 2 MiB limit")
                if method == "POST":
                    if response.status not in {200, 204}:
                        raise APIError("unexpected dispatch response status", details)
                    # Only 200 supplies a request-specific identity. A 204 can
                    # retain observations but cannot identify this operation.
                    return {"http": details, "body": rt.json_read(body) if body else None}
                require(response.status == 200, "unexpected GitHub API response status")
                return rt.json_read(body)
        except HTTPError as error:
            details.update(status=error.code,
                           request_id=rt.clean(error.headers.get("X-GitHub-Request-Id", "")))
            error.close()
            if absent and error.code == 404:
                return MISSING
            raise APIError("GitHub API HTTP failure", details) from None
        except (URLError, OSError, rt.http.client.HTTPException):
            raise APIError("GitHub API transport failed or timed out", details) from None


def main_sha(api, prefix, token=None):
    value = api.request("GET", prefix + "/git/ref/heads/main", token)
    require(isinstance(value, dict) and value.get("ref") == "refs/heads/main"
            and isinstance(value.get("object"), dict) and value["object"].get("type") == "commit",
            "fixed main ref identity mismatch")
    return rt.sha(value["object"].get("sha"))


def committed_blob(api, prefix, source, path, token=None, *, optional=False):
    """Read only an exact-commit file and verify the returned complete Git blob."""
    value = api.request("GET", prefix + "/contents/" + path + "?ref=" + rt.sha(source), token, absent=optional)
    if value is MISSING:
        return None
    require(isinstance(value, dict) and value.get("type") == "file" and value.get("path") == path
            and value.get("encoding") == "base64" and type(value.get("size")) is int
            and 0 <= value["size"] <= rt.MAX_JSON and isinstance(value.get("content"), str)
            and len(value["content"]) <= rt.MAX_JSON,
            "missing, nonregular or oversized exact committed blob")
    identity = rt.sha(value.get("sha"))
    try:
        data = base64.b64decode(value["content"].replace("\n", ""), validate=True)
    except ValueError:
        raise rt.DeliveryError("malformed exact committed blob encoding") from None
    require(len(data) == value["size"] and blob_sha(data) == identity,
            "exact committed Git blob identity mismatch")
    return identity, data


def manifest(raw, repository):
    value = rt.json_read(raw)
    require(isinstance(value, dict) and value.get("schema") == "hexalith.contracts-prerequisites.v1"
            and value.get("repository") == repository, "fixed publisher proposal identity mismatch")
    for key in ("base_commit", "base_tree", "result_tree"):
        rt.sha(value.get(key))
    require(isinstance(value.get("after"), dict) and set(value["after"]) == {RELEASE},
            "publisher proposal is not the one-path release workflow delivery")
    item = value["after"][RELEASE]
    require(isinstance(item, list) and len(item) == 3 and item[:2] == ["100644", "blob"],
            "publisher proposal release path is not a regular Git blob")
    rt.sha(item[2])
    return value


def policy_manifest(raw):
    """Only the committed two-path Projects prerequisite policy correction."""
    value = rt.json_read(raw)
    require(isinstance(value, dict) and value.get("schema") == "hexalith.contracts-prerequisites.v1"
            and value.get("repository") == OWNERS["projects"], "fixed Projects policy proposal identity mismatch")
    for key in ("base_commit", "base_tree", "result_tree"):
        rt.sha(value.get(key))
    for field in ("before", "after"):
        require(isinstance(value.get(field), dict) and set(value[field]) == POLICY_PATHS,
                "Projects policy proposal differs from the two fixed policy paths")
        for item in value[field].values():
            require(isinstance(item, list) and len(item) == 3 and item[:2] == ["100644", "blob"],
                    "Projects policy proposal requires regular Git blobs")
            rt.sha(item[2])
    return value


def local_blob(root, path, data):
    local = root / path
    require(local.is_file() and not local.is_symlink() and local.stat().st_size <= rt.MAX_JSON,
            "local trusted source missing, nonregular or oversized: " + path)
    with local.open("rb") as stream:
        require(stream.read(rt.MAX_JSON + 1) == data,
                "local payload differs from exact committed owner source: " + path)


def token_scope(api, prefix, repository, token, context):
    require(token and context.get("PREREQUISITE_TOKEN_RESULT") == "success",
            "existing App installation did not provide the scoped token")
    require(context.get("PREREQUISITE_INSTALLATION_ID") == "179966090"
            and context.get("PREREQUISITE_APP_SLUG") == "hexalith-cicd", "approved existing App identity mismatch")
    inventory = api.request("GET", "/installation/repositories?per_page=100&page=1", token)
    require(isinstance(inventory, dict) and type(inventory.get("total_count")) is int
            and inventory["total_count"] == 1 and isinstance(inventory.get("repositories"), list)
            and len(inventory["repositories"]) == 1 and isinstance(inventory["repositories"][0], dict)
            and inventory["repositories"][0].get("full_name") == "Hexalith/" + repository,
            "App token repository inventory is not exactly the chosen fixed owner")
    metadata = api.request("GET", prefix, token)
    require(isinstance(metadata, dict) and metadata.get("full_name") == "Hexalith/" + repository
            and metadata.get("default_branch") == "main", "fixed target repository/default main mismatch")


def inventory(api, prefix, source, token, *, deadline=None, clock=time.monotonic):
    runs, total = {}, None
    for page in range(1, MAX_RUNS // 100 + 1):
        timeout = 30 if deadline is None else min(30, deadline - clock())
        require(timeout > 0, "run correlation polling deadline reached")
        value = api.request("GET", prefix + "/actions/workflows/release.yml/runs"
                            + "?event=workflow_dispatch&branch=main&head_sha=" + rt.sha(source)
                            + "&per_page=100&page=" + str(page), token, timeout=timeout)
        require(isinstance(value, dict) and type(value.get("total_count")) is int
                and 0 <= value["total_count"] <= MAX_RUNS and isinstance(value.get("workflow_runs"), list)
                and len(value["workflow_runs"]) <= 100, "invalid or unbounded workflow run inventory")
        require(total is None or total == value["total_count"], "workflow run inventory changed during pagination")
        total = value["total_count"]
        for run in value["workflow_runs"]:
            require(isinstance(run, dict) and type(run.get("id")) is int and run["id"] > 0
                    and run["id"] not in runs, "malformed or duplicate workflow run identity")
            runs[run["id"]] = run
        if len(runs) == total:
            return runs
        require(len(runs) < total and len(value["workflow_runs"]) == 100,
                "incomplete workflow run inventory")
    raise rt.DeliveryError("workflow run inventory pagination limit exceeded")


def matching_run(run, repository, source, workflow_id):
    identity = run["id"]
    expected_url = "https://github.com/Hexalith/" + repository + "/actions/runs/" + str(identity)
    if (run.get("path") != RELEASE or type(run.get("workflow_id")) is not int or run["workflow_id"] != workflow_id
            or run.get("event") != "workflow_dispatch" or run.get("head_sha") != source
            or run.get("head_branch") != "main" or not isinstance(run.get("actor"), dict)
            or run["actor"].get("login") != "hexalith-cicd[bot]"
            or not isinstance(run.get("repository"), dict)
            or run["repository"].get("full_name") != "Hexalith/" + repository
            or run.get("html_url") != expected_url
            or type(run.get("run_attempt")) is not int or run["run_attempt"] < 1):
        return None
    return {"id": identity, "url": expected_url, "head_sha": source, "attempt": run["run_attempt"],
            "actor": "hexalith-cicd[bot]", "workflow": RELEASE}


def dispatch_identity(response, prefix, repository):
    require(isinstance(response, dict) and isinstance(response.get("http"), dict)
            and response["http"].get("status") == 200, "dispatch response has no direct 200 run identity")
    body = response.get("body")
    require(isinstance(body, dict) and type(body.get("workflow_run_id")) is int
            and body["workflow_run_id"] > 0, "malformed dispatch response run identity")
    identity = str(body["workflow_run_id"])
    require(body.get("run_url") == "https://api.github.com" + prefix + "/actions/runs/" + identity
            and body.get("html_url") == "https://github.com/Hexalith/" + repository
            + "/actions/runs/" + identity, "dispatch response URL identity mismatch")
    return body["workflow_run_id"]


def refused_dispatch(receipt):
    status = receipt.get("dispatch_http_error", {}).get("status")
    return type(status) is int and 400 <= status < 500


def correlate(api, prefix, token, receipt, *, clock, sleep):
    deadline = clock() + POLL_SECONDS
    correlation = {"status": "unresolved", "reason": "direct dispatch run identity unavailable; observations cannot identify the operation",
                   "polls": 0, "candidate_ids": [], "other_new_ids": []}
    receipt["correlation"] = correlation
    receipt.update(status="unresolved", run=None)
    if refused_dispatch(receipt):
        receipt["status"] = "failed"
        correlation.update(status="refused", reason=receipt["dispatch_error"])
        return
    try:
        direct_id = dispatch_identity(receipt.get("dispatch_response"), prefix, receipt["repository"])
    except rt.DeliveryError:
        direct_id = None
    before = set(receipt["pre_dispatch_run_ids"])
    if direct_id in before:
        correlation["reason"] = "returned dispatch run was already in the pre-dispatch inventory"
        return
    if direct_id is not None:
        correlation["reason"] = "returned dispatch run not observed and verified"
    while clock() < deadline:
        try:
            observed = inventory(api, prefix, receipt["target_sha"], token, deadline=deadline, clock=clock)
            correlation["polls"] += 1
            fresh = set(observed) - before
            matches = [matching_run(observed[identity], receipt["repository"], receipt["target_sha"],
                                    receipt["workflow_id"]) for identity in sorted(fresh)]
            matches = [match for match in matches if match is not None]
            correlation.update(candidate_ids=[match["id"] for match in matches],
                               other_new_ids=sorted(fresh - {match["id"] for match in matches}))
            if direct_id in fresh:
                selected = matching_run(observed[direct_id], receipt["repository"], receipt["target_sha"],
                                        receipt["workflow_id"])
                require(selected is not None, "returned dispatch run source/workflow/actor identity mismatch")
                receipt["run"] = selected
                receipt["status"] = "correlated"
                correlation.update(status="correlated", reason=None)
                return
        except Interrupted:
            raise
        except Exception as error:
            correlation["reason"] = safe_error(error)
            if isinstance(error, APIError):
                correlation["http_error"] = error.details
            return
        remaining = deadline - clock()
        if remaining > 0:
            sleep(min(5, remaining))


def safe_error(error):
    return rt.clean(error) if isinstance(error, rt.DeliveryError) else "controller failure: " + type(error).__name__


def checkpoint(path, receipt):
    rt.atomic(path, receipt)
    # Flush both the attempt contents and its atomic directory entry before POST.
    with path.open("rb") as stream:
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def execute(operation, owner, context, report, token, *, api, clock, sleep, local_root):
    receipt = {"schema": SCHEMA, "owner": owner, "operation": operation,
               "repository": OWNERS[owner], "release_profile": OPERATIONS[operation],
               "owner_source": None, "target_sha": None, "status": "failed", "reason": None,
               "failed_operation": "authorize fixed owner invocation", "dispatch_attempted": False,
               "pre_dispatch_run_ids": [], "run": None}
    receipt["invocation"] = {key: rt.clean(context.get(key, "")) for key in (
        "GITHUB_WORKFLOW_REF", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "PREREQUISITE_TOKEN_RESULT",
        "PREREQUISITE_INSTALLATION_ID", "PREREQUISITE_APP_SLUG", "PREREQUISITE_BEHAVIORAL_RESULT",
        "PREREQUISITE_WRITER_STATUS")}
    prefix = "/repos/Hexalith/" + OWNERS[owner]
    prior_attempt, unreadable_report = False, False
    try:
        if report.exists():
            unreadable_report = True
            previous = rt.read_state(report)
            unreadable_report = False
            prior_attempt = previous.get("dispatch_attempted") is True
            if prior_attempt:
                # Never discard an ambiguous prior attempt, even when this
                # invocation's identity or source fails authorization.
                receipt = previous
                receipt["recovery_only"] = True
                require(previous.get("schema") == SCHEMA and previous.get("owner") == owner
                        and previous.get("operation") == operation
                        and previous.get("repository") == OWNERS[owner]
                        and previous.get("release_profile") == OPERATIONS[operation],
                        "prior attempt binding differs; no additional dispatch is permitted")
        require(context.get("GITHUB_REPOSITORY") == "Hexalith/Hexalith.CiCd"
                and context.get("GITHUB_REF") == "refs/heads/main"
                and context.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
                and context.get("GITHUB_WORKFLOW_REF") == "Hexalith/Hexalith.CiCd/" + WORKFLOW + "@refs/heads/main"
                and context.get("PREREQUISITE_OWNER") == owner
                and context.get("PREREQUISITE_OPERATION") == operation, "ineligible fixed owner workflow invocation")
        source = rt.sha(context.get("PREREQUISITE_OWNER_SOURCE"))
        require(source == context.get("GITHUB_SHA") == context.get("GITHUB_WORKFLOW_SHA"),
                "owner dispatch/workflow/source identities differ")
        require(not prior_attempt or receipt.get("owner_source") == source,
                "prior attempted owner source differs; no additional dispatch is permitted")
        receipt["owner_source"] = source
        require(context.get("PREREQUISITE_BEHAVIORAL_RESULT") == "success"
                and context.get("PREREQUISITE_WRITER_STATUS") == "success",
                "secret-free behavioral qualification or writer failed, cancelled or was skipped")
        require(prior_attempt or context.get("GITHUB_RUN_ATTEMPT") == "1",
                "workflow rerun has no durable prior checkpoint; a fresh POST is forbidden")
        receipt["failed_operation"] = "verify current committed owner source"
        require(main_sha(api, OWNER_PREFIX) == source, "owner source is not current exact CiCd main")
        committed = {}
        for path in source_paths(owner):
            identity, data = committed_blob(api, OWNER_PREFIX, source, path)
            local_blob(local_root, path, data)
            committed[path] = data
        proposal = manifest(committed[proposal_path(owner)], OWNERS[owner])
        policy = None
        if owner == "projects":
            policy_blob = committed_blob(api, OWNER_PREFIX, source, POLICY_PROPOSAL, optional=True)
            if policy_blob is None:
                require(not (local_root / POLICY_PROPOSAL).exists() and not (local_root / POLICY_PROPOSAL).is_symlink(),
                        "local policy proposal is absent from exact committed owner source")
            else:
                local_blob(local_root, POLICY_PROPOSAL, policy_blob[1])
                policy = policy_manifest(policy_blob[1])
                receipt["policy_proposal_blob"] = policy_blob[0]
        receipt["failed_operation"] = "verify scoped existing App token"
        token_scope(api, prefix, OWNERS[owner], token, context)
        if prior_attempt:
            rt.sha(receipt.get("target_sha"))
            require(isinstance(receipt.get("pre_dispatch_run_ids"), list)
                    and len(receipt["pre_dispatch_run_ids"]) <= MAX_RUNS
                    and all(type(i) is int and i > 0 for i in receipt["pre_dispatch_run_ids"])
                    and type(receipt.get("workflow_id")) is int and receipt["workflow_id"] > 0,
                    "invalid prior attempt correlation checkpoint; no additional dispatch is permitted")
            receipt["failed_operation"] = "read-only recovery of prior attempted dispatch"
            correlate(api, prefix, token, receipt, clock=clock, sleep=sleep)
        else:
            receipt["failed_operation"] = "verify exact live target main and publisher delivery"
            live = main_sha(api, prefix, token)
            receipt["target_sha"] = live
            commit = api.request("GET", prefix + "/git/commits/" + live, token)
            require(isinstance(commit, dict) and commit.get("sha") == live
                    and isinstance(commit.get("tree"), dict), "target commit identity mismatch")
            tree = rt.sha(commit["tree"].get("sha"))
            receipt["target_tree"] = tree
            if operation == "publish":
                parents = commit.get("parents")
                bindings = [(owner + "-publisher", proposal)]
                if policy is not None:
                    bindings.append(("projects-prerequisite-policy", policy))
                eligible = [(profile, value) for profile, value in bindings
                            if tree == value["result_tree"] and isinstance(parents, list) and len(parents) == 1
                            and isinstance(parents[0], dict) and parents[0].get("sha") == value["base_commit"]]
                require(eligible,
                        "publish requires exact complete delivered tree and single reviewed direct parent")
                receipt["publish_binding"] = {"profile": eligible[0][0], "base_commit": eligible[0][1]["base_commit"],
                                              "result_tree": eligible[0][1]["result_tree"]}
            release_blob, _ = committed_blob(api, prefix, live, RELEASE, token)
            require(release_blob == proposal["after"][RELEASE][2], "live release workflow differs from approved publisher blob")
            receipt["release_blob"] = release_blob
            workflow = api.request("GET", prefix + "/actions/workflows/release.yml", token)
            require(isinstance(workflow, dict) and type(workflow.get("id")) is int and workflow["id"] > 0
                    and workflow.get("path") == RELEASE and workflow.get("state") == "active",
                    "fixed release workflow identity/state mismatch")
            receipt["workflow_id"] = workflow["id"]
            receipt["failed_operation"] = "inventory pre-dispatch release runs"
            receipt["pre_dispatch_run_ids"] = sorted(inventory(api, prefix, live, token, clock=clock))
            receipt["failed_operation"] = "reread owner and target main immediately before dispatch"
            require(main_sha(api, OWNER_PREFIX) == source, "CiCd main advanced before dispatch")
            require(main_sha(api, prefix, token) == live, "target main advanced before dispatch")
            receipt.update(failed_operation="single fixed release workflow POST", dispatch_attempted=True,
                           dispatch_outcome="attempted; acceptance unknown; automatic retry forbidden",
                           correlation={"status": "unresolved", "reason": "process may stop during POST"})
            checkpoint(report, receipt)
            try:
                response = api.request("POST", prefix + "/actions/workflows/release.yml/dispatches", token,
                                       payload={"ref": "main", "inputs": {"release-profile": OPERATIONS[operation]}})
                # Only fixed, validated response identities can enter artifacts.
                receipt["dispatch_response"] = {"http": response["http"], "body": None}
                dispatch_identity(response, prefix, OWNERS[owner])
                body = response["body"]
                body = {key: body[key] for key in ("workflow_run_id", "run_url", "html_url")}
                receipt["dispatch_response"] = {"http": response["http"], "body": body}
                receipt["dispatch_outcome"] = "accepted response; independent run correlation required"
            except Interrupted:
                raise
            except Exception as error:
                receipt["dispatch_error"] = safe_error(error)
                if isinstance(error, APIError):
                    receipt["dispatch_http_error"] = error.details
                receipt["dispatch_outcome"] = ("refused; automatic retry forbidden" if refused_dispatch(receipt)
                                               else "ambiguous response; automatic retry forbidden")
            checkpoint(report, receipt)
            receipt["failed_operation"] = "bounded read-only release run correlation"
            correlate(api, prefix, token, receipt, clock=clock, sleep=sleep)
        if receipt["status"] == "correlated":
            receipt.update(failed_operation=None, reason=None)
        elif receipt["status"] == "failed":
            receipt["reason"] = receipt["correlation"]["reason"]
        else:
            receipt.update(status="unresolved", reason=receipt["correlation"]["reason"])
    except (Exception, KeyboardInterrupt) as error:
        receipt["status"] = "unresolved" if receipt.get("dispatch_attempted") and not refused_dispatch(receipt) else "failed"
        receipt["reason"] = safe_error(error)
        if isinstance(error, (Interrupted, KeyboardInterrupt)):
            receipt["interrupted"] = True
        if isinstance(error, APIError):
            receipt["http_error"] = error.details
    # Preserve an unreadable checkpoint: replacing it would erase evidence of
    # a possible attempted POST and permit a later invocation to dispatch again.
    if not unreadable_report:
        checkpoint(report, receipt)
    return receipt


def main(argv=None, *, api=None, clock=time.monotonic, sleep=time.sleep, local_root=None):
    """The sole dependency-injection boundary; production has no URL/test flags."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=tuple(OPERATIONS))
    parser.add_argument("--owner", choices=tuple(OWNERS), required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    context = os.environ.copy()
    tokens = rt.sanitize()  # Remove all token-bearing ambient environment before work.
    token = tokens["MODULE_TOKEN"]
    previous_handlers = {}
    def interrupted(signum, frame):
        raise Interrupted("controller interrupted; attempted dispatch must never be retried")
    try:
        for signum in (signal.SIGTERM, signal.SIGINT):
            previous_handlers[signum] = signal.signal(signum, interrupted)
        result = execute(args.operation, args.owner, context, Path(args.report), token,
                         api=api or API(), clock=clock, sleep=sleep,
                         local_root=Path(local_root) if local_root else Path(__file__).resolve().parents[1])
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
    return 0 if result["status"] == "correlated" else 1


if __name__ == "__main__":
    raise SystemExit(main())
