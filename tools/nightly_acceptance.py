#!/usr/bin/env python3
"""Judge one nightly.yml run on CiCd main for selected modules; stdlib only.

Every GitHub read is ``gh api --method GET`` in the caller's unchanged
environment. Nothing is dispatched, rerun, minted or written remotely; ZIP
members are parsed in memory and the only local write is the optional
identity-only receipt.

The run must be a completed ``nightly.yml`` run on ``main``, scheduled or
dispatched, whose ``dispatch`` job ran (so ``qualify-bump`` was false). Each
selected module's verdict comes from its own rows only: its nightly row and
release run, its release CodeQL jobs, its scan row and, after a pushed Builds
bump, its delivery-wait row. Other targets, Builds and the night's aggregate
are reported and never change it. ``--checkpoint pilot`` also requires the bump
to report no change, or a pushed candidate with a green delivery-wait, and
keepalive to pass.

Exit 0 when every selected module (and the checkpoint) passes, 1 when any
fails, and 2 for a rejected run, a usage error or a transport error.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
from urllib.parse import quote
import zipfile
import zlib

OWNER = "Hexalith"
CICD = "Hexalith.CiCd"
BUILDS = "Hexalith.Builds"
NIGHTLY_WORKFLOW = ".github/workflows/nightly.yml"
SCAN_WORKFLOW = ".github/workflows/scan.yml"
EVENTS = ("schedule", "workflow_dispatch")
NIGHTLY_SCHEMA = "hexalith.nightly.v1"
OUTCOME_SCHEMA = "hexalith.release-outcome.v1"
PACKAGE_PUBLICATION = "hexalith-package-publication.v1.json"
PACKAGE_SCHEMA = "hexalith.package-publication.v1"
RELEASE_OUTCOME = "hexalith-release-outcome"
SCAN_SCHEMA = "hexalith.duplicate-scan.v1"
BUMP_SCHEMA = "hexalith.nightly-bump-report.v1"
PUSH_SCHEMA = "hexalith.nightly-bump-push.v1"
DELIVERY_SCHEMA = "hexalith.nightly-delivery-wait.v1"
KEEPALIVE_SCHEMA = "hexalith.nightly-keepalive.v1"
REPORT_SCHEMA = "hexalith.nightly-acceptance.v1"
RECEIPT_SCHEMA = "hexalith.nightly-acceptance-receipt.v1"

# Mirrored from tools/nightly_runtime.py (DIGEST, ROW_KEYS, STATE_KEYS and the
# allowed row values), not imported: this tool runs under ``python3 -I``.
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
ROW_KEYS = frozenset(("repository", "workflow", "deliveredSha", "dispatchHead", "runId", "runAttempt", "link",
                      "eligibility", "dispatch", "status", "conclusion", "outcome", "outcomeError", "publication",
                      "verdict", "reason"))
STATE_KEYS = frozenset(("schema", "phase", "identity", "registry", "builds", "targets", "errors", "wait", "result"))
ROW_VALUES = {"eligibility": {"pending", "eligible", "not-adopted", "failed"},
              "dispatch": {"pending", "dispatched", "failed", "skipped"},
              "publication": {"pending", "published", "failed", "skipped"},
              "verdict": {"pending", "pass", "fail", "skip"}}
OUTCOMES = frozenset(("published", "ready", "nothing", "disabled", "failed"))

SHA = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
PACKAGE_ID = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}\Z")
CONTAINER_NAME = re.compile(r"[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*(?:/[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*)*\Z")
RELEASE_MARKERS = ("hexalith-release", "hexalith-release-run", "hexalith-release-artifact",
                   "hexalith-release-packages", "hexalith-release-containers")
REPOSITORY = re.compile(r"Hexalith\.[A-Za-z0-9_.-]{1,91}\Z")
ENDPOINT = re.compile(r"repos/Hexalith/[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_./%=&?:+-]{1,1000}\Z")
STAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z\Z")
LANGUAGE = re.compile(r"[a-z][a-z-]{0,31}\Z")
CODEQL_JOB = re.compile(r"(?:.+ / )?Release CodeQL \((.+)\)\Z")
MAX_ZIP = 8 * 1024 * 1024
MAX_JSON = 2 * 1024 * 1024
MAX_RESPONSE = 16 * 1024 * 1024
MAX_MEMBER = {"report.json": 16 * 1024 * 1024, "summary.md": 16 * 1024 * 1024}
MAX_RECEIPT = 16 * 1024
MAX_REASON = 200
PAGE = 100

# Artifacts this tool reads: the nightly.yml job that uploads each, its name
# template and its exact ZIP members. After story 28-7, scan.yml must keep the
# scan name or update it here (test_nightly_workflow.py checks both).
ARTIFACTS = {
    "nightly": ("publish-ready", "hexalith-nightly-nightly-{attempt}", ("nightly.json",)),
    "scan": ("scan", "hexalith-nightly-scan-{attempt}", ("report.json", "summary.md")),
    "bump-report": ("bump", "hexalith-nightly-bump-report-{attempt}", ("bump.json",)),
    "bump-push": ("bump-push", "hexalith-nightly-bump-push-{attempt}", ("bump-push.json",)),
    "delivery-wait": ("delivery-wait", "hexalith-nightly-delivery-wait-{attempt}", ("report.json",)),
    "keepalive": ("keepalive", "hexalith-nightly-keepalive-{attempt}", ("keepalive.json",)),
}


class Rejected(Exception):
    """The run, or an artifact it relies on, cannot be judged at all."""


class TransportError(Exception):
    """A GitHub read failed; no verdict is possible."""


class NotFound(TransportError):
    """GitHub answered 404: the evidence does not exist (missing, not a transport fault)."""


class UsageError(Exception):
    """The command line names no judgeable selection."""


class Unproven(Exception):
    """Evidence owned by one module or by the checkpoint is missing or malformed."""


class ReceiptTooLarge(Exception):
    """The identity-only receipt would exceed 16 KiB."""


def clean(value, limit=MAX_REASON):
    text = "".join(c if 32 <= ord(c) < 127 else "?" for c in str(value))
    return text if len(text) <= limit else text[:limit - 3] + "..."


def same(left, right):
    """Exact JSON equality, so that true never equals 1."""
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def positive(value):
    return type(value) is int and value > 0


def timestamp(value):
    if not isinstance(value, str) or not STAMP.fullmatch(value):
        raise ValueError("timestamp is not canonical UTC")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def parse_json(data, limit=MAX_JSON):
    if len(data) > limit:
        raise ValueError("JSON exceeds its size limit")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("non-JSON constant")
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError) as error:
        raise ValueError("invalid JSON: " + clean(error)) from None


class GitHub:
    """The only network boundary: ``gh api --method GET`` with the caller's environment.

    No ``env`` is passed, so the caller's gh profile is used unchanged.
    """

    def __init__(self, run=subprocess.run, timeout=300):
        self._run, self.timeout = run, timeout

    def _get(self, endpoint, *, binary=False):
        if not isinstance(endpoint, str) or not ENDPOINT.fullmatch(endpoint):
            raise TransportError("refused a read outside the Hexalith repositories")
        try:
            headers = ["-H", "Accept: application/octet-stream"] if binary else []
            completed = self._run(["gh", "api", "--method", "GET", *headers, endpoint], stdin=subprocess.DEVNULL,
                                  capture_output=True, timeout=self.timeout, check=False)
        except (OSError, subprocess.SubprocessError) as error:
            raise TransportError(endpoint + ": " + clean(error)) from None
        if completed.returncode:
            message = completed.stderr.decode("utf-8", "replace").strip() or "gh exited " + str(completed.returncode)
            failure = NotFound if "(HTTP 404)" in message else TransportError
            raise failure(endpoint + ": " + clean(message))
        return completed.stdout

    def json(self, endpoint):
        try:
            return parse_json(self._get(endpoint), MAX_RESPONSE)
        except ValueError as error:
            raise TransportError(endpoint + ": " + clean(error)) from None

    def blob(self, endpoint, *, binary=False):
        return self._get(endpoint, binary=binary)


def listing(github, endpoint, field):
    """One page of at most 100 items; a missing, longer or inconsistent listing fails closed."""
    try:
        value = github.json(endpoint + ("&" if "?" in endpoint else "?") + "per_page=" + str(PAGE))
    except NotFound:
        raise Unproven(field + " listing is not found") from None
    if (not isinstance(value, dict) or type(value.get("total_count")) is not int
            or not isinstance(value.get(field), list)):
        raise Unproven(field + " listing is malformed")
    if value["total_count"] > PAGE:
        raise Unproven(field + " listing has " + str(value["total_count"]) + " items, over one page of 100")
    if len(value[field]) != value["total_count"] or not all(isinstance(item, dict) for item in value[field]):
        raise Unproven(field + " listing is incomplete")
    return value[field]


def jobs_by_name(github, endpoint):
    jobs = {}
    for job in listing(github, endpoint, "jobs"):
        name = job.get("name")
        if not isinstance(name, str) or name in jobs:
            raise Unproven("job listing has a missing or duplicate job name")
        jobs[name] = job
    return jobs


def authenticate_run(github, run_id):
    run = github.json(f"repos/{OWNER}/{CICD}/actions/runs/{run_id}")
    if not isinstance(run, dict) or not same(run.get("id"), run_id):
        raise Rejected(f"run {run_id} identity mismatch")
    repository = run.get("repository")
    if not isinstance(repository, dict) or repository.get("full_name") != OWNER + "/" + CICD:
        raise Rejected(f"run {run_id} is not a {CICD} run")
    if run.get("path") != NIGHTLY_WORKFLOW:
        raise Rejected(f"run {run_id} is {clean(run.get('path'))}, not {NIGHTLY_WORKFLOW}")
    if run.get("head_branch") != "main":
        raise Rejected(f"run {run_id} ran on {clean(run.get('head_branch'))}, not main")
    if run.get("event") not in EVENTS:
        raise Rejected(f"run {run_id} event {clean(run.get('event'))} is neither schedule nor workflow_dispatch")
    if run.get("status") != "completed":
        raise Rejected(f"run {run_id} is {clean(run.get('status'))}, not completed")
    if not positive(run.get("run_attempt")) or not SHA.fullmatch(str(run.get("head_sha"))):
        raise Rejected(f"run {run_id} attempt or head is malformed")
    try:
        timestamp(run.get("created_at"))
    except ValueError:
        raise Rejected(f"run {run_id} creation time is malformed") from None
    return run


def download(github, metadata, run, members, clock, *, repository=CICD):
    """Authenticate one listed artifact of ``run`` and return its exact members, or reject."""
    name = clean(metadata.get("name"))
    if metadata.get("expired") is not False:
        raise Rejected(f"artifact {name} is expired")
    try:
        expires = timestamp(metadata.get("expires_at")).timestamp()
    except ValueError:
        raise Rejected(f"artifact {name} expiry is malformed") from None
    if expires <= clock():
        raise Rejected(f"artifact {name} is expired")
    origin = metadata.get("workflow_run")
    if (not isinstance(origin, dict) or not same(origin.get("id"), run["id"])
            or origin.get("head_sha") != run["head_sha"] or origin.get("head_branch") != "main"):
        raise Rejected(f"artifact {name} is not bound to run {run['id']} at {run['head_sha']}")
    size, digest = metadata.get("size_in_bytes"), metadata.get("digest")
    if not positive(metadata.get("id")) or not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        raise Rejected(f"artifact {name} id or digest is malformed")
    if not positive(size) or size > MAX_ZIP:
        raise Rejected(f"artifact {name} size is malformed or over 8 MiB")
    payload = github.blob(f"repos/{OWNER}/{repository}/actions/artifacts/{metadata['id']}/zip")
    if len(payload) != size:
        raise Rejected(f"artifact {name} downloaded {len(payload)} bytes, API size is {size}")
    if "sha256:" + hashlib.sha256(payload).hexdigest() != digest:
        raise Rejected(f"artifact {name} downloaded bytes do not match its API digest")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            found = {item.filename: item for item in archive.infolist()}
            if len(found) != len(archive.infolist()) or set(found) != set(members):
                raise Rejected(f"artifact {name} members {sorted(found)} are not {sorted(members)}")
            documents = {}
            for member in members:
                item = found[member]
                limit = MAX_MEMBER.get(member, MAX_JSON)
                mode = item.external_attr >> 16
                if (item.flag_bits & 1 or item.is_dir() or not 1 <= item.file_size <= limit
                        or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                        or (mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG))):
                    raise Rejected(f"artifact {name} member {member} metadata is refused")
                with archive.open(item) as stream:
                    data = stream.read(limit + 1)
                if len(data) != item.file_size:
                    raise Rejected(f"artifact {name} member {member} size mismatch")
                documents[member] = data
    except (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, OSError, EOFError, RuntimeError,
            ValueError) as error:
        raise Rejected(f"artifact {name} is not a readable ZIP: " + clean(error)) from None
    return documents


class Artifacts:
    """The run's artifact listing; each artifact used is authenticated once and recorded."""

    def __init__(self, github, run, clock):
        self.github, self.run, self.clock = github, run, clock
        self.listed = listing(github, f"repos/{OWNER}/{CICD}/actions/runs/{run['id']}/artifacts", "artifacts")
        self.cache, self.used = {}, []

    def documents(self, kind):
        """Members of this attempt's ``kind`` artifact, or None when it was not uploaded."""
        if kind not in self.cache:
            _, template, members = ARTIFACTS[kind]
            name = template.format(attempt=self.run["run_attempt"])
            matches = [item for item in self.listed if item.get("name") == name]
            if len(matches) > 1:
                raise Rejected(f"artifact {name} is listed more than once")
            documents = None
            if matches:
                documents = download(self.github, matches[0], self.run, members, self.clock)
                self.used.append({"name": name, "id": matches[0]["id"], "digest": matches[0]["digest"]})
            self.cache[kind] = documents
        return self.cache[kind]

    def document(self, kind, member):
        documents = self.documents(kind)
        if documents is None:
            return None
        try:
            return parse_json(documents[member], MAX_MEMBER.get(member, MAX_JSON))
        except ValueError as error:
            # Authenticated bytes that are not JSON are malformed evidence of
            # whoever consumes them, not a transport or digest failure.
            raise Unproven(f"{ARTIFACTS[kind][1].format(attempt=self.run['run_attempt'])} {member} "
                           "is not JSON: " + str(error)) from None


def document_or_error(artifacts, kind, member):
    """A consumer's document, or the Unproven error it owns when the member is not JSON."""
    try:
        return artifacts.document(kind, member)
    except Unproven as error:
        return error


def run_link(repository, run_id):
    return f"https://github.com/{OWNER}/{repository}/actions/runs/{run_id}"


def validate_nightly(value, run):
    """Run-level shape of nightly.json; per-row problems are judged per module."""
    if not isinstance(value, dict) or set(value) != STATE_KEYS:
        raise Rejected("nightly.json fields are not the nightly state contract")
    if value["schema"] != NIGHTLY_SCHEMA or value["phase"] != "nightly":
        raise Rejected("nightly.json is not a final hexalith.nightly.v1 nightly-phase state")
    if not same(value["identity"], {"runId": run["id"], "attempt": run["run_attempt"], "source": run["head_sha"]}):
        raise Rejected("nightly.json identity does not match run, attempt and head")
    registry = value["registry"]
    if registry == [] and isinstance(value["errors"], list) and value["errors"]:
        # publish-ready's conservative seed: the controller never produced a state.
        raise Rejected("nightly.json is publish-ready's seed: " + clean(value["errors"][0]))
    if (not isinstance(registry, list) or not all(isinstance(item, str) and REPOSITORY.fullmatch(item)
                                                  and item.casefold() != BUILDS.casefold() for item in registry)
            or registry != sorted(set(registry))):
        raise Rejected("nightly.json registry is malformed")
    targets = value["targets"]
    expected = [*registry, BUILDS]
    if (not isinstance(targets, list) or len(targets) != len(expected)
            or any(not isinstance(row, dict) or row.get("repository") != name for row, name in zip(targets, expected))):
        raise Rejected("nightly.json targets do not follow its registry and Builds")
    if value["result"] not in ("pending", "pass", "fail") or not isinstance(value["errors"], list):
        raise Rejected("nightly.json aggregate result or errors are malformed")
    return {row["repository"]: row for row in targets}


def row_problems(row):
    """The nightly row contract of tools/nightly_runtime.py validate_state."""
    if set(row) != ROW_KEYS:
        return ["row fields are not the nightly row contract"]
    problems = []
    caller = ".github/workflows/" + ("builds-release.yml" if row["repository"] == BUILDS else "release.yml")
    if row["workflow"] != caller:
        problems.append("row caller is not " + caller)
    for field in ("deliveredSha", "dispatchHead"):
        if row[field] != "" and not (isinstance(row[field], str) and SHA.fullmatch(row[field])):
            problems.append(field + " is malformed")
    for field in ("runId", "runAttempt"):
        if type(row[field]) is not int or row[field] < 0:
            problems.append(field + " is malformed")
    if not problems and row["link"] != (run_link(row["repository"], row["runId"]) if row["runId"] else ""):
        problems.append("run link does not match runId")
    for field, allowed in ROW_VALUES.items():
        if not isinstance(row[field], str) or row[field] not in allowed:
            problems.append(field + " is malformed")
    for field in ("status", "conclusion"):
        if not isinstance(row[field], str) or not re.fullmatch(r"[a-z_]{0,32}", row[field]):
            problems.append(field + " is malformed")
    for field in ("outcomeError", "reason"):
        if not isinstance(row[field], str):
            problems.append(field + " is malformed")
    if row["outcome"] is not None and not isinstance(row["outcome"], dict):
        problems.append("outcome is neither an object nor null")
    if not problems and row["dispatch"] == "dispatched" and (
            not row["runId"] or not row["dispatchHead"] or row["runAttempt"] < 1):
        problems.append("dispatched row has an incomplete run identity")
    return problems


def release_problems(row):
    """D2: eligible, dispatched, success, and published/nothing or a ready row published by this run."""
    problems = []
    if row["eligibility"] != "eligible":
        problems.append(f"release eligibility is {row['eligibility']}: {clean(row['reason'], 120)}")
    if row["dispatch"] != "dispatched":
        problems.append(f"release dispatch is {row['dispatch']}")
        return problems
    if row["status"] != "completed":
        problems.append(f"release run is {row['status'] or 'unobserved'}, not completed")
    elif row["conclusion"] != "success":
        problems.append(f"release run concluded {row['conclusion'] or 'without a conclusion'}")
    if row["outcomeError"]:
        problems.append("release outcome unreadable: " + clean(row["outcomeError"], 150))
    outcome = row["outcome"]
    if (not isinstance(outcome, dict) or outcome.get("schema") != OUTCOME_SCHEMA
            or outcome.get("outcome") not in OUTCOMES):
        problems.append("release outcome is missing or malformed")
        return problems
    if not isinstance(outcome.get("sha"), str) or not SHA.fullmatch(outcome["sha"]):
        problems.append("release outcome source is malformed")
    elif outcome["sha"] != row["dispatchHead"] and outcome["outcome"] not in {"ready", "published"}:
        problems.append("release outcome source is not the dispatched head")
    result = outcome["outcome"]
    if result == "ready" and row["publication"] != "published":
        problems.append(f"ready release was not published by this run (publication {row['publication']})")
    elif result == "disabled":
        problems.append("release publishing is disabled")
    elif result == "failed":
        problems.append("release outcome is failed")
    return problems


def release_run_problems(run, name, row):
    if not isinstance(run, dict):
        return ["release run is unreadable"]
    expected = {"id": row["runId"], "path": row["workflow"], "event": "workflow_dispatch", "head_branch": "main",
                "head_sha": row["dispatchHead"], "run_attempt": row["runAttempt"], "status": "completed",
                "conclusion": row["conclusion"]}
    problems = [f"release run {key} is {clean(run.get(key), 60)}, the row says {clean(value, 60)}"
                for key, value in expected.items() if not same(run.get(key), value)]
    repository = run.get("repository")
    if not isinstance(repository, dict) or repository.get("full_name") != OWNER + "/" + name:
        problems.append("release run belongs to another repository")
    return problems


def remote_release(github, name, row, artifacts, *, check_publication):
    """The linked release run must be the row's run, attempt, head and conclusion."""
    endpoint = f"repos/{OWNER}/{name}/actions/runs/{row['runId']}"
    try:
        run = github.json(endpoint)
    except NotFound:
        return ["release run is not found"], {}
    problems = release_run_problems(run, name, row)
    if not isinstance(run, dict):
        return problems, {}
    detail = {"runId": row["runId"], "attempt": row["runAttempt"], "link": row["link"],
              "conclusion": run.get("conclusion")}
    if not problems and check_publication:
        try:
            proof = publication_proof(github, name, row, run, artifacts.clock)
            current = github.json(endpoint)
            if release_run_problems(current, name, row) or current.get("run_started_at") != run["run_started_at"]:
                raise Unproven("correlated completion attempt changed during publication verification")
            detail["publicationProof"] = proof
            artifacts.used.append(proof["outcomeArtifact"])
        except (Unproven, Rejected, NotFound, ValueError) as error:
            problems.append("release source is unproven: " + clean(error))
    return problems, detail


def published_trailers(release, source):
    """Require the five draft trailers, with no case or indentation aliases."""
    body = release.get("body")
    if not isinstance(body, str) or len(body) > 120000:
        raise Unproven("immutable release is missing its original draft markers")
    markers = "|".join(RELEASE_MARKERS)
    if len(re.findall(r"^[ \t]*(?:" + markers + r")[ \t]*:", body, re.I | re.M)) != len(RELEASE_MARKERS):
        raise Unproven("immutable release has missing or conflicting draft markers")
    values = [re.findall(r"^" + marker + r":[ \t]*(.*?)\r?$", body, re.M) for marker in RELEASE_MARKERS]
    if any(len(matches) != 1 for matches in values):
        raise Unproven("immutable release has missing or conflicting draft markers")
    sha, producer, artifact, packages, containers = (matches[0] for matches in values)
    match = re.fullmatch(r"([1-9][0-9]*) (sha256:[0-9a-f]{64})", artifact)
    package_ids = packages.split(",") if packages else []
    container_names = containers.split(",") if containers else []
    if (sha != source or not re.fullmatch(r"[1-9][0-9]*", producer) or match is None
            or any(not PACKAGE_ID.fullmatch(package) for package in package_ids)
            or len({package.casefold() for package in package_ids}) != len(package_ids)
            or any(not CONTAINER_NAME.fullmatch(container) for container in container_names)
            or len(set(container_names)) != len(container_names)):
        raise Unproven("immutable release has invalid original source, artifact or inventory markers")
    return int(producer), int(match[1]), match[2], sorted(package_ids)


def peeled_tag(github, prefix, tag):
    reference = github.json(prefix + "/git/ref/tags/" + tag)
    if not isinstance(reference, dict) or reference.get("ref") != "refs/tags/" + tag:
        raise Unproven("version tag identity mismatch")
    target = reference.get("object")
    seen = set()
    for _ in range(16):
        identity = target.get("sha") if isinstance(target, dict) else None
        if not isinstance(identity, str) or not SHA.fullmatch(identity):
            break
        if target.get("type") == "commit":
            return identity
        if target.get("type") != "tag" or identity in seen:
            break
        seen.add(identity)
        annotated = github.json(prefix + "/git/tags/" + identity)
        if not isinstance(annotated, dict) or annotated.get("sha") != identity:
            break
        target = annotated.get("object")
    raise Unproven("version tag could not be peeled to a commit")


def package_publication_record(package):
    """Mirror the tagged Builds v1 validator's package and payload-map contract."""
    if (not isinstance(package, dict) or set(package) != {"id", "archiveSha256", "files"}
            or not isinstance(package["id"], str) or not PACKAGE_ID.fullmatch(package["id"])
            or not isinstance(package["archiveSha256"], str) or not SHA256.fullmatch(package["archiveSha256"])
            or not isinstance(package["files"], dict) or not package["files"]):
        return False
    paths = set()
    for path, digest in package["files"].items():
        if (not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or ":" in path
                or any(part in ("", ".", "..") for part in path.split("/"))
                or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in path)
                or path == ".signature.p7s" or path.casefold() in paths
                or not isinstance(digest, str) or not SHA256.fullmatch(digest)):
            return False
        paths.add(path.casefold())
    return True


def authenticate_publication_asset(github, prefix, release, expected, package_ids):
    assets = release.get("assets")
    if not isinstance(assets, list) or any(not isinstance(asset, dict) for asset in assets):
        raise Unproven("immutable release assets are unreadable")
    matches = [asset for asset in assets if asset.get("name") == PACKAGE_PUBLICATION]
    if len(matches) != 1:
        raise Unproven("immutable release must have exactly one package publication asset")
    asset = matches[0]
    identity, size, digest = (asset.get(key) for key in ("id", "size", "digest"))
    if (not positive(identity) or not positive(size) or size > MAX_JSON or asset.get("state") != "uploaded"
            or not isinstance(digest, str) or not DIGEST.fullmatch(digest)):
        raise Unproven("package publication asset metadata is malformed")
    content = github.blob(prefix + f"/releases/assets/{identity}", binary=True)
    if len(content) != size or "sha256:" + hashlib.sha256(content).hexdigest() != digest:
        raise Unproven("package publication asset size or digest mismatch")
    document = parse_json(content)
    if (not isinstance(document, dict) or set(document) != {*expected, "packages"}
            or any(not same(document[key], value) for key, value in expected.items())
            or not isinstance(document["packages"], list)
            or any(not package_publication_record(package) for package in document["packages"])
            or [package["id"] for package in document["packages"]] != package_ids):
        raise Unproven("package publication asset conflicts with the original draft and build identity")
    return {"id": identity, "digest": digest}


def publication_proof(github, name, row, run, clock):
    """Bind a successful completion attempt to its original draft, build and immutable release."""
    outcome = row["outcome"]
    source, version, draft, last_tag = (outcome.get(key) for key in ("sha", "version", "draftId", "lastTag"))
    if (set(outcome) != {"schema", "outcome", "sha", "version", "draftId", "lastTag"}
            or not VERSION.fullmatch(str(version)) or not positive(draft) or not isinstance(last_tag, str)
            or (last_tag and (not last_tag.startswith("v") or not VERSION.fullmatch(last_tag[1:])))):
        raise Unproven("outcome source is not the dispatched head or lacks a valid completion draft identity")
    repository = f"{OWNER}/{name}"
    prefix = "repos/" + repository
    started = timestamp(run.get("run_started_at"))
    listed = listing(github, prefix + f"/actions/runs/{row['runId']}/artifacts", "artifacts")
    matches = [item for item in listed if item.get("name") == RELEASE_OUTCOME
               and timestamp(item.get("created_at")) >= started]
    if len(matches) != 1:
        raise Unproven("completion attempt must have exactly one release outcome artifact")
    metadata = matches[0]
    document = download(github, metadata, run, ("outcome.json",), clock, repository=name)
    if not same(parse_json(document["outcome.json"]), outcome):
        raise Unproven("completion attempt outcome differs from the central nightly row")
    # GitHub returns comparison totals on every page and large patch
    # data only on the first page.
    comparison = github.json(prefix + f"/compare/{source}...{row['dispatchHead']}?per_page=1&page=2")
    if (not isinstance(comparison, dict) or comparison.get("status") != "ahead"
            or not same(comparison.get("behind_by"), 0) or not positive(comparison.get("ahead_by"))
            or any(not isinstance(comparison.get(key), dict) or comparison[key].get("sha") != source
                   for key in ("base_commit", "merge_base_commit"))):
        raise Unproven("original source is not a proven ancestor of the exact dispatch head")
    tag = "v" + version
    release = github.json(prefix + f"/releases/{draft}")
    expected_release = {"id": draft, "immutable": True, "draft": False, "prerelease": False,
                        "tag_name": tag, "target_commitish": source}
    if (not isinstance(release, dict) or any(not same(release.get(key), value)
                                            for key, value in expected_release.items())
            or not isinstance(release.get("author"), dict) or release["author"].get("login") != "github-actions[bot]"):
        raise Unproven("immutable release does not match the original bot-marked draft, version or source")
    producer_id, artifact_id, digest, package_ids = published_trailers(release, source)
    origin = github.json(prefix + f"/actions/runs/{producer_id}")
    producer_run = {"id": producer_id, "path": row["workflow"], "event": "workflow_dispatch",
                    "head_branch": "main", "head_sha": source}
    if (not isinstance(origin, dict) or any(not same(origin.get(key), value) for key, value in producer_run.items())
            or not isinstance(origin.get("repository"), dict) or origin["repository"].get("full_name") != repository):
        raise Unproven("original producer run does not match the module release workflow, repository or source")
    build = github.json(prefix + f"/actions/artifacts/{artifact_id}")
    expected_build = {"id": artifact_id, "name": "release", "digest": digest}
    if (not isinstance(build, dict) or any(not same(build.get(key), value) for key, value in expected_build.items())
            or not isinstance(build.get("workflow_run"), dict)
            or not same(build["workflow_run"].get("id"), producer_id)
            or build["workflow_run"].get("head_sha") != source):
        raise Unproven("original build artifact does not match the producer, source or digest")
    asset = authenticate_publication_asset(github, prefix, release, {
        "schema": PACKAGE_SCHEMA, "repository": repository, "sha": source, "version": version,
        "artifactRun": producer_id, "artifactId": artifact_id, "artifactDigest": digest}, package_ids)
    if peeled_tag(github, prefix, tag) != source:
        raise Unproven("peeled version tag does not identify the original source")
    return {"source": source, "dispatchHead": row["dispatchHead"], "completionRun": row["runId"],
            "completionAttempt": row["runAttempt"], "draftId": draft, "tag": tag, "artifactRun": producer_id,
            "artifactId": artifact_id, "artifactDigest": digest, "publicationAsset": asset,
            "outcomeArtifact": {key: metadata[key] for key in ("name", "id", "digest")}}


def codeql_languages(github, name, delivered):
    """The codeql list of the hexalith-ci.json rendered at the delivered CiCd commit."""
    if not delivered:
        raise Unproven("no delivered CiCd revision to read its CodeQL languages from")
    path = f"rendered/{name}/.github/hexalith-ci.json"
    try:
        value = github.json(f"repos/{OWNER}/{CICD}/contents/{quote(path)}?ref={delivered}")
    except NotFound:
        raise Unproven("rendered hexalith-ci.json is not found at the delivered revision") from None
    if (not isinstance(value, dict) or value.get("type") != "file" or value.get("path") != path
            or value.get("encoding") != "base64" or not isinstance(value.get("content"), str)):
        raise Unproven("rendered hexalith-ci.json contents response is malformed")
    try:
        data = base64.b64decode("".join(value["content"].split()), validate=True)
    except ValueError:
        raise Unproven("rendered hexalith-ci.json content is not base64") from None
    blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
    if not same(value.get("size"), len(data)) or value.get("sha") != blob:
        raise Unproven("rendered hexalith-ci.json size or blob id does not match its content")
    try:
        config = parse_json(data)
    except ValueError as error:
        raise Unproven("rendered hexalith-ci.json: " + str(error)) from None
    languages = config.get("codeql") if isinstance(config, dict) else None
    if (not isinstance(languages, list) or len(set(map(str, languages))) != len(languages)
            or not all(isinstance(item, str) and LANGUAGE.fullmatch(item) for item in languages)):
        raise Unproven("rendered hexalith-ci.json codeql is malformed")
    return languages


def codeql_problems(github, name, row, languages):
    """Each declared language needs a successful Release CodeQL job; no Release CodeQL job may fail."""
    try:
        jobs = listing(github, f"repos/{OWNER}/{name}/actions/runs/{row['runId']}/attempts/{row['runAttempt']}/jobs",
                       "jobs")
    except Unproven as error:
        return ["release " + str(error)], []
    selected = [job for job in jobs if "Release CodeQL" in str(job.get("name"))]
    detail = [{"name": clean(job.get("name"), 80), "conclusion": clean(job.get("conclusion"), 20)} for job in selected]
    if not languages:
        return [], detail
    problems = []
    for language in languages:
        if not any((match := CODEQL_JOB.fullmatch(str(job.get("name")))) and match.group(1) == language
                   and job.get("status") == "completed" and job.get("conclusion") == "success" for job in selected):
            problems.append(f"no successful Release CodeQL ({language}) job")
    for job in selected:
        if job.get("status") != "completed" or job.get("conclusion") != "success":
            problems.append(f"{clean(job.get('name'), 80)} concluded {clean(job.get('conclusion'), 20)}")
    return problems, detail


def scan_report_problems(report, producer):
    if not isinstance(report, dict) or report.get("schema") != SCAN_SCHEMA:
        return ["scan report is not hexalith.duplicate-scan.v1"]
    if report.get("controllerRevision") != producer["head_sha"]:
        return ["scan report controller revision is not its run's head"]
    modules, findings, errors = report.get("modules"), report.get("findings"), report.get("errors")
    if (not isinstance(modules, list) or not isinstance(findings, list) or not isinstance(errors, list)
            or not all(isinstance(row, dict) and isinstance(row.get("module"), str) for row in modules)):
        return ["scan report modules, findings or errors are malformed"]
    return []


def scan_row_problems(report, name, head):
    rows = [row for row in report["modules"] if row["module"] == name]
    if len(rows) != 1:
        return ["scan report has " + ("no row" if not rows else "duplicate rows") + " for the module"]
    row, problems = rows[0], []
    if row.get("revision") != head:
        problems.append(f"scan row revision {clean(row.get('revision'), 40)} is not the dispatched head {head}")
    errors = row.get("errors")
    if row.get("result") != "pass" or not isinstance(errors, list) or errors:
        first = errors[0] if isinstance(errors, list) and errors else row.get("result")
        problems.append("own scan row failed: " + clean(first, 150))
    if report["errors"]:
        problems.append("scan report has run-level errors: " + clean(report["errors"][0], 150))
    involved = [item for item in report["findings"] if not isinstance(item, dict) or name in (
        endpoint.get("module") if isinstance(endpoint, dict) else name
        for endpoint in (item.get("first"), item.get("second")))]
    if involved:
        problems.append(f"{len(involved)} cross-module duplicate findings involve the module")
    return problems


class ScanSource:
    """The attempt's scan job artifact, or after 28-7 the first scan.yml run covering the dispatched head."""

    def __init__(self, github, run, jobs, artifacts, clock):
        self.github, self.run, self.artifacts, self.clock = github, run, artifacts, clock
        self.in_run = "scan" in jobs
        self.runs, self.reports = None, {}

    def problems(self, name, head):
        if not head:
            return ["no dispatched head to match a scan row"], None
        if self.in_run:
            report = document_or_error(self.artifacts, "scan", "report.json")
            if isinstance(report, Unproven):
                return [str(report)], None
            if report is None:
                return ["the attempt's scan artifact is missing"], None
            problems = scan_report_problems(report, self.run) or scan_row_problems(report, name, head)
            return problems, {"source": "scan job", "runId": self.run["id"]}
        skipped = []
        try:
            for producer in self.scan_runs():
                # Only a run whose row covers the dispatched head decides; a run
                # without a readable, well-formed report has no row to decide.
                report = self.report(producer)
                if report is None:
                    continue
                if isinstance(report, Unproven):
                    skipped.append(str(report))
                    continue
                problems = scan_report_problems(report, producer)
                if problems:
                    skipped.append(f"scan.yml run {producer['id']}: " + problems[0])
                    continue
                if any(row["module"] == name and row.get("revision") == head for row in report["modules"]):
                    return scan_row_problems(report, name, head), {"source": "scan.yml", "runId": producer["id"]}
        except Unproven as error:
            return ["scan.yml " + str(error)], None
        notes = ["skipped " + note for note in skipped[:3]]
        if len(skipped) > 3:
            notes.append(f"skipped {len(skipped) - 3} more unreadable scan.yml runs")
        return ["no completed scan.yml run on main after the nightly covers the dispatched head", *notes], None

    def scan_runs(self):
        if self.runs is None:
            created = self.run["created_at"]
            listed = listing(self.github, f"repos/{OWNER}/{CICD}/actions/workflows/scan.yml/runs?branch=main"
                             f"&status=completed&created={quote('>=' + created, safe='')}", "workflow_runs")
            start = timestamp(created)
            def eligible(item):
                try:
                    return (positive(item.get("id")) and positive(item.get("run_attempt"))
                            and item.get("path") == SCAN_WORKFLOW and item.get("head_branch") == "main"
                            and item.get("event") in EVENTS
                            and item.get("status") == "completed" and SHA.fullmatch(str(item.get("head_sha")))
                            and isinstance(item.get("repository"), dict)
                            and item["repository"].get("full_name") == OWNER + "/" + CICD
                            and timestamp(item.get("created_at")) >= start)
                except ValueError:
                    return False
            self.runs = sorted(filter(eligible, listed), key=lambda item: (timestamp(item["created_at"]), item["id"]))
        return self.runs

    def report(self, producer):
        """The run's report, None without one, or the Unproven naming the run; read once."""
        if producer["id"] not in self.reports:
            artifacts = Artifacts(self.github, producer, self.clock)
            try:
                self.reports[producer["id"]] = artifacts.document("scan", "report.json")
            except Unproven as error:
                self.reports[producer["id"]] = Unproven(f"scan.yml run {producer['id']}: {error}")
            finally:
                self.artifacts.used.extend(artifacts.used)
        return self.reports[producer["id"]]


def bump_identity(run):
    return {"runId": run["id"], "attempt": run["run_attempt"], "source": run["head_sha"],
            "night": timestamp(run["created_at"]).date().isoformat()}


def push_state(run, jobs, artifacts):
    """Whether this attempt pushed a Builds bump, as bump-push.json says."""
    job = jobs.get("bump-push")
    if job is None:
        return {"state": "unknown", "reason": "the attempt has no bump-push job"}
    if job.get("conclusion") == "skipped":
        return {"state": "not-run"}
    report = document_or_error(artifacts, "bump-push", "bump-push.json")
    if isinstance(report, Unproven):
        return {"state": "unknown", "reason": str(report)}
    if report is None:
        return {"state": "unknown", "reason": "bump-push ran but its report is missing"}
    if not isinstance(report, dict) or report.get("schema") != PUSH_SCHEMA or not isinstance(report.get("result"), str):
        return {"state": "unknown", "reason": "bump-push report is malformed"}
    if report["result"] == "failed":
        return {"state": "failed"}
    if report["result"] != "pushed":
        return {"state": "unknown", "reason": "bump-push result is " + clean(report["result"], 20)}
    if not same(report.get("identity"), bump_identity(run)) or not SHA.fullmatch(str(report.get("candidate"))):
        return {"state": "unknown", "reason": "pushed bump report identity or candidate is malformed"}
    return {"state": "pushed", "candidate": report["candidate"]}


def delivery_report(run, artifacts, push):
    """The delivery-wait report bound to this attempt and the pushed candidate."""
    report = artifacts.document("delivery-wait", "report.json")
    if report is None:
        raise Unproven("delivery-wait report is missing after pushed bump " + push["candidate"])
    if (not isinstance(report, dict) or report.get("schema") != DELIVERY_SCHEMA
            or not same(report.get("identity"), {"runId": run["id"], "attempt": run["run_attempt"],
                                                 "source": run["head_sha"]})
            or report.get("bump") != push["candidate"] or not isinstance(report.get("modules"), list)
            or not all(isinstance(row, dict) for row in report["modules"])):
        raise Unproven("delivery-wait report identity, candidate or rows are malformed")
    return report


def delivery_problems(name, push, delivery):
    if push["state"] == "unknown":
        return ["bump push result unproven: " + push["reason"]]
    if push["state"] != "pushed":
        return []
    if isinstance(delivery, Unproven):
        return [str(delivery)]
    rows = [row for row in delivery["modules"] if row.get("repository") == name]
    if len(rows) != 1:
        return ["no delivery-wait row after pushed bump " + push["candidate"]]
    row = rows[0]
    if not positive(row.get("runId")) or row.get("conclusion") != "success":
        return [f"delivery-wait first CI is {clean(row.get('conclusion') or 'missing', 20)} after pushed bump"]
    return []


def judge_module(github, name, row, scan, push, delivery, artifacts):
    verdict = {"verdict": "fail", "reasons": []}
    if row is None:
        verdict["reasons"].append("not a target of this run's committed registry")
        return verdict
    problems = row_problems(row)
    if problems:
        verdict["reasons"].extend("nightly row: " + problem for problem in problems)
        return verdict
    reasons = release_problems(row)
    outcome = row["outcome"] if isinstance(row["outcome"], dict) else {}
    verdict["release"] = {"outcome": clean(outcome.get("outcome", ""), 20),
                          "version": clean(outcome.get("version", ""), 40),
                          "publication": row["publication"], "dispatchHead": row["dispatchHead"]}
    if row["dispatch"] == "dispatched":
        check_publication = not reasons and outcome.get("sha") != row["dispatchHead"]
        problems, detail = remote_release(github, name, row, artifacts, check_publication=check_publication)
        reasons.extend(problems)
        verdict["release"].update(detail)
        try:
            languages = codeql_languages(github, name, row["deliveredSha"])
        except Unproven as error:
            reasons.append("CodeQL languages unproven: " + str(error))
        else:
            problems, detail = codeql_problems(github, name, row, languages)
            reasons.extend(problems)
            verdict["codeql"] = {"languages": languages, "jobs": detail}
        problems, detail = scan.problems(name, row["dispatchHead"])
        reasons.extend(problems)
        verdict["scan"] = detail
        reasons.extend(delivery_problems(name, push, delivery))
    verdict["reasons"] = [clean(reason) for reason in reasons]
    verdict["verdict"] = "fail" if reasons else "pass"
    return verdict


def judge_pilot(run, artifacts, push, delivery):
    """Story 11's shared machinery: the bump and keepalive."""
    reasons, bump_detail = [], {}
    bump = document_or_error(artifacts, "bump-report", "bump.json")
    if isinstance(bump, Unproven):
        reasons.append(str(bump))
    elif bump is None:
        reasons.append("bump report is missing")
    elif not isinstance(bump, dict) or bump.get("schema") != BUMP_SCHEMA or not isinstance(bump.get("result"), str):
        reasons.append("bump report is malformed")
    else:
        result, tag = bump["result"], clean(bump.get("tag") or "an unselected tag", 40)
        bump_detail = {"result": clean(result, 20), "tag": clean(bump.get("tag", ""), 40),
                       "candidate": clean(bump.get("candidate", ""), 40)}
        # The producer's early-failure paths omit the identity; every other report carries it.
        if "identity" in bump or result != "failed":
            if not same(bump.get("identity"), bump_identity(run)):
                reasons.append("bump report identity does not match run, attempt, head and night")
        if result == "failed":
            reasons.append(f"Builds bump to {tag} failed: " + clean(bump.get("reason"), 150))
        elif result == "candidate":
            if push["state"] != "pushed" or push["candidate"] != bump.get("candidate"):
                reasons.append(f"bump candidate for {tag} was not pushed (bump-push {push['state']})")
            elif isinstance(delivery, Unproven):
                reasons.append(str(delivery))
            elif delivery.get("result") != "pass":
                reasons.append(f"delivery-wait after the {tag} bump is {clean(delivery.get('result'), 20)}")
        elif result != "no-change":
            reasons.append("bump result is " + clean(result, 20))
    keepalive = document_or_error(artifacts, "keepalive", "keepalive.json")
    if isinstance(keepalive, Unproven):
        reasons.append(str(keepalive))
    elif keepalive is None:
        reasons.append("keepalive report is missing")
    elif not isinstance(keepalive, dict) or keepalive.get("schema") != KEEPALIVE_SCHEMA:
        reasons.append("keepalive report is malformed")
    elif keepalive.get("result") != "pass":
        errors = keepalive.get("errors") if isinstance(keepalive.get("errors"), list) else []
        reasons.append(f"keepalive is {clean(keepalive.get('result'), 20)}"
                       + (": " + clean(errors[0], 150) if errors else ""))
    reasons = [clean(reason) for reason in reasons]
    return {"name": "pilot", "verdict": "fail" if reasons else "pass", "reasons": reasons, "bump": bump_detail,
            "keepalive": clean(keepalive.get("result"), 20) if isinstance(keepalive, dict) else "missing"}


def judge(run_id, modules, checkpoint=None, *, github, clock=time.time):
    """Authenticate run ``run_id`` and return the report; raise Rejected or TransportError."""
    run = authenticate_run(github, run_id)
    attempt = run["run_attempt"]
    try:
        jobs = jobs_by_name(github, f"repos/{OWNER}/{CICD}/actions/runs/{run_id}/attempts/{attempt}/jobs")
    except Unproven as error:
        raise Rejected(f"run {run_id} {error}") from None
    dispatch = jobs.get("dispatch")
    if dispatch is None or dispatch.get("conclusion") in (None, "skipped"):
        raise Rejected(f"run {run_id} attempt {attempt} did not run its dispatch job (a qualify-bump run)")
    try:
        artifacts = Artifacts(github, run, clock)
    except Unproven as error:
        raise Rejected(f"run {run_id} artifact {error}") from None
    try:
        nightly = artifacts.document("nightly", "nightly.json")
    except Unproven as error:
        raise Rejected(f"run {run_id} artifact {error}") from None
    if nightly is None:
        raise Rejected(f"run {run_id} attempt {attempt} has no nightly.json artifact")
    targets = validate_nightly(nightly, run)
    push = push_state(run, jobs, artifacts)
    delivery = None
    if push["state"] == "pushed":
        try:
            delivery = delivery_report(run, artifacts, push)
        except Unproven as error:
            delivery = error
    scan = ScanSource(github, run, jobs, artifacts, clock)
    verdicts = {name: judge_module(github, name, targets.get(name), scan, push, delivery, artifacts) for name in modules}
    others = {name: {"verdict": clean(row.get("verdict"), 20), "reason": clean(row.get("reason"))}
              for name, row in targets.items() if name not in verdicts}
    report = {
        "schema": REPORT_SCHEMA,
        "run": {"id": run_id, "attempt": attempt, "event": run["event"], "head": run["head_sha"],
                "createdAt": run["created_at"], "conclusion": clean(run.get("conclusion"), 20),
                "link": run_link(CICD, run_id)},
        "night": {"result": nightly["result"], "errors": [clean(error) for error in nightly["errors"][:20]]},
        "modules": verdicts,
        "others": others,
        "push": push,
        "checkpoint": judge_pilot(run, artifacts, push, delivery) if checkpoint == "pilot" else None,
    }
    report["artifacts"] = list(artifacts.used)
    failed = any(item["verdict"] != "pass" for item in verdicts.values()) or (
        report["checkpoint"] is not None and report["checkpoint"]["verdict"] != "pass")
    report["verdict"] = "fail" if failed else "pass"
    return report


def receipt(report):
    """Identities only: run, artifacts, per-module verdicts and reasons; at most 16 KiB."""
    checkpoint = report["checkpoint"]
    value = {"schema": RECEIPT_SCHEMA,
             "run": {key: report["run"][key] for key in ("id", "attempt", "event", "head")},
             "artifacts": [{key: item[key] for key in ("name", "id", "digest")} for item in report["artifacts"]],
             "modules": {name: {"verdict": item["verdict"], "reasons": [clean(reason) for reason in item["reasons"]]}
                         for name, item in report["modules"].items()},
             "checkpoint": None if checkpoint is None else {
                 "name": checkpoint["name"], "verdict": checkpoint["verdict"],
                 "reasons": [clean(reason) for reason in checkpoint["reasons"]]}}
    for name, item in report["modules"].items():
        proof = item.get("release", {}).get("publicationProof")
        if proof is not None:
            value["modules"][name]["publicationProof"] = proof
    data = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()
    if len(data) > MAX_RECEIPT:
        raise ReceiptTooLarge(f"receipt would be {len(data)} bytes, over the 16 KiB limit")
    return data


def write_receipt(path, data):
    path = Path(path)
    temporary = path.with_name(path.name + ".writing")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    except OSError:
        with contextlib.suppress(OSError):
            temporary.unlink(missing_ok=True)
        raise


def arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--run", required=True, help="nightly.yml run id on Hexalith.CiCd")
    parser.add_argument("--module", action="append", required=True, help="module repository to judge (repeatable)")
    parser.add_argument("--checkpoint", choices=("pilot",), help="also judge story 11's shared bump and keepalive")
    parser.add_argument("--receipt", help="write the identity-only receipt here (at most 16 KiB)")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[1-9][0-9]{0,19}", args.run):
        raise UsageError("--run must be a positive run id")
    modules = []
    for name in args.module:
        if name.casefold() == BUILDS.casefold():
            raise UsageError("Hexalith.Builds is reported, never judged as a module")
        if not REPOSITORY.fullmatch(name):
            raise UsageError("--module must be a Hexalith module repository: " + clean(name))
        if name not in modules:
            modules.append(name)
    return int(args.run), modules, args.checkpoint, args.receipt


def main(argv=None, *, github=None, clock=time.time, stdout=None, stderr=None):
    stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
    try:
        run_id, modules, checkpoint, receipt_path = arguments(argv)
    except UsageError as error:
        print("nightly acceptance: usage: " + str(error), file=stderr)
        return 2
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 2
    try:
        report = judge(run_id, modules, checkpoint, github=github or GitHub(), clock=clock)
        data = receipt(report) if receipt_path else None
        if data is not None:
            write_receipt(receipt_path, data)
    except Rejected as error:
        print("nightly acceptance: rejected: " + str(error), file=stderr)
        return 2
    except TransportError as error:
        print("nightly acceptance: transport: " + str(error), file=stderr)
        return 2
    except (ReceiptTooLarge, OSError) as error:
        print("nightly acceptance: receipt not written: " + clean(error), file=stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True), file=stdout)
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    try:
        raise SystemExit(main())
    except Exception as error:  # an internal defect never reads as a verdict
        print("nightly acceptance: internal error: " + clean(error), file=sys.stderr)
        raise SystemExit(2) from None
