"""Bounded stdlib GitHub/Git boundary for unattended nightly releases.

Only committed CiCd identities select repositories. No environment or handoff
can select a network origin, and downloaded ZIP members are never extracted.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
import hashlib
import http.client
import importlib
import io
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import delivery_runtime as delivery
from delivery_runtime import (BUILDS, CAPACITY, CICD, MAX_JSON, SHA, TAG, Git,
                              atomic, clean, environment, json_read, name, registry, sha, timestamp)

NightlyError = delivery.DeliveryError
MAX_ZIP = 8 * 1024 * 1024
MAX_CALLS = 4096
MAX_PAGES = 20
API_VERSION = "2026-03-10"
SCHEMA = "hexalith.nightly.v1"
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
TOKEN_NAMES = ("CICD_TOKEN", "TARGET_TOKEN", "POLL_TOKEN", "HANDOFF_TOKEN", "MODULE_TOKEN")


@contextmanager
def whole_operation(seconds, *, write=False):
    """Bound DNS, connection acquisition and dribbling reads on Ubuntu runners.

    urllib's timeout only bounds socket inactivity. A real-time process alarm
    also interrupts continuous slow reads, without leaving a background request
    able to finish an uncertain write after this controller has moved on.
    Preserve enclosing alarms and their remaining time, including nested uses.
    """
    seconds = number(seconds, positive=True)
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_delay, previous_interval = signal.getitimer(signal.ITIMER_REAL)
    started = time.monotonic()
    def expired(_signum, _frame):
        message = "GitHub API whole-operation deadline exceeded"
        if write:
            message += "; write result uncertain, not retried"
        raise NightlyError(message)
    try:
        signal.signal(signal.SIGALRM, expired)
    except ValueError:
        # Controllers execute on the main thread. Refuse an unbounded fallback
        # if a future caller invokes this transport from another thread.
        raise NightlyError("whole-operation deadline requires the main controller thread") from None
    try:
        signal.setitimer(signal.ITIMER_REAL, min(seconds, previous_delay) if previous_delay else seconds)
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_delay:
            remaining = previous_delay - (time.monotonic() - started)
            # An enclosing alarm that expired during this call still belongs
            # to its previous handler; deliver it promptly after restoration.
            signal.setitimer(signal.ITIMER_REAL, max(0.000001, remaining), previous_interval)


def sanitize():
    """Capture credentials for explicit calls and redact before clearing env."""
    tokens = {key: os.environ.get(key, "") for key in TOKEN_NAMES}
    delivery._SECRETS.extend(value for value in tokens.values() if value)
    os.environ.clear()
    os.environ.update(environment())
    sys.dont_write_bytecode = True
    return tokens


def number(value, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or (positive and value <= 0)):
        raise NightlyError("invalid nightly clock")
    return value


class Budget:
    """Conservative persisted wall-clock budget, including operation reserve.

    Mint epochs are captured before the action starts, never at script startup.
    A request timeout cannot extend past the job, slice, or 50-minute boundary.
    """
    def __init__(self, started=None, job_seconds=55 * 60, token_epoch=None,
                 deadline=None, *, clock=time.time):
        self.clock = clock
        self.started = number(clock() if started is None else started, positive=True)
        self.job_seconds = number(job_seconds, positive=True)
        self.token_epoch = None if token_epoch is None else number(token_epoch, positive=True)
        self.deadline = None if deadline is None else number(deadline, positive=True)

    def remaining(self, *, token=False):
        now = number(self.clock(), positive=True)
        if now < self.started or (self.token_epoch is not None and now < self.token_epoch):
            raise NightlyError("nightly clock moved backwards")
        ends = [self.started + self.job_seconds - 30]
        if self.deadline is not None:
            ends.append(self.deadline)
        if token:
            if self.token_epoch is None:
                raise NightlyError("token mint epoch unavailable")
            ends.append(self.token_epoch + 50 * 60 - 30)
        return min(ends) - now

    def check(self, *, token=False):
        if self.remaining(token=token) < 1:
            raise NightlyError("token or nightly operation budget exhausted")

    def timeout(self, *, token=False, max_seconds=120):
        self.check(token=token)
        return max(1, min(number(max_seconds, positive=True), self.remaining(token=token)))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def positive(value, message="invalid positive API identity"):
    if type(value) is not int or value < 1 or value > 2**63 - 1:
        raise NightlyError(message)
    return value


def run_link(repository, identity):
    return f"https://github.com/Hexalith/{name(repository, module=False)}/actions/runs/{positive(identity)}"


def dispatch_details(repository, value):
    """Authenticate the exact run returned by a successful workflow dispatch."""
    if not isinstance(value, dict):
        raise NightlyError("dispatch response uncertain: missing exact run identity")
    identity = positive(value.get("workflow_run_id"), "dispatch response uncertain: missing exact run identity")
    if (value.get("html_url") != run_link(repository, identity)
            or value.get("run_url") != f"https://api.github.com/repos/Hexalith/{repository}/actions/runs/{identity}"):
        raise NightlyError("dispatch response uncertain: run URL mismatch")
    return {"runId": identity, "link": value["html_url"]}


def run_identity(document, repository, workflow, identity):
    """Require exactly the dispatch-created caller, never a latest-run guess."""
    expected = "Hexalith/" + name(repository, module=False)
    if (not isinstance(document, dict) or document.get("id") != positive(identity)
            or type(document.get("id")) is not int or document.get("path") != workflow
            or document.get("event") != "workflow_dispatch" or document.get("head_branch") != "main"
            or not isinstance(document.get("repository"), dict)
            or document["repository"].get("full_name") != expected
            or document.get("html_url") != run_link(repository, identity)):
        raise NightlyError("correlated release run identity mismatch")
    sha(document.get("head_sha"))
    positive(document.get("run_attempt"))
    if document.get("status") not in {"queued", "in_progress", "completed", "waiting", "pending", "requested"}:
        raise NightlyError("correlated release run status is malformed")
    if document.get("conclusion") is not None and document.get("conclusion") not in {
            "success", "failure", "neutral", "cancelled", "skipped", "timed_out", "action_required",
            "stale", "startup_failure"}:
        raise NightlyError("correlated release run conclusion is malformed")
    return document


class API:
    def __init__(self, budget=None, repositories=(CICD, BUILDS), opener=None, *, sleep=time.sleep):
        self.budget = budget or Budget()
        self.repositories = frozenset(name(item, module=False) for item in repositories)
        if not self.repositories or len(self.repositories) > CAPACITY + 2:
            raise NightlyError("invalid API repository scope")
        self.opener = opener or build_opener(ProxyHandler({}), NoRedirect())
        self.sleep = sleep
        self.calls = 0

    def _path(self, path, method="GET"):
        if not isinstance(path, str) or len(path) > 1500 or any(ord(c) < 32 for c in path):
            raise NightlyError("noncanonical GitHub API path")
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc or parsed.fragment or "\\" in path or "%" in path:
            raise NightlyError("noncanonical GitHub API path")
        matched = re.fullmatch(r"/repos/Hexalith/([A-Za-z0-9_.-]+)/(.+)", parsed.path)
        if not matched or matched[1] not in self.repositories:
            raise NightlyError("GitHub API repository outside explicit scope")
        suffix = matched[2]
        workflow = "builds-release.yml" if matched[1] == BUILDS else "release.yml"
        get_patterns = (
            r"actions/runs/[1-9][0-9]*(?:/artifacts|/attempts/[1-9][0-9]*/jobs)?",
            r"actions/artifacts/[1-9][0-9]*(?:/zip)?",
            r"actions/workflows/(?:ci|deliver|nightly|release|builds-release)\.yml/runs",
            r"immutable-releases", r"releases(?:/[1-9][0-9]*|/tags/v[0-9]+\.[0-9]+\.[0-9]+)?",
            r"git/ref/(?:heads/main|tags/v[0-9]+\.[0-9]+\.[0-9]+)",
            r"git/matching-refs/tags/v[0-9]+\.[0-9]+\.[0-9]+",
            r"git/tags/[0-9a-f]{40}", r"compare/[0-9a-f]{40}\.\.\.[0-9a-f]{40}")
        if method == "GET":
            allowed = any(re.fullmatch(pattern, suffix) for pattern in get_patterns)
        elif method == "POST":
            allowed = suffix == f"actions/workflows/{workflow}/dispatches" or (
                matched[1] == CICD and suffix == "actions/workflows/deliver.yml/dispatches")
        elif method == "PUT":
            allowed = matched[1] == CICD and suffix in {
                "actions/workflows/nightly.yml/enable", "actions/workflows/deliver.yml/enable"}
        elif method == "PATCH":
            allowed = re.fullmatch(r"releases/[1-9][0-9]*", suffix) is not None
        else:
            allowed = False
        if not allowed:
            raise NightlyError("GitHub API operation outside nightly contract")
        query = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True) if parsed.query else []
        if len(query) != len(dict(query)):
            raise NightlyError("duplicate GitHub API query key")
        for key, value in query:
            if ((key == "page" and re.fullmatch(r"[1-9][0-9]?", value) and int(value) <= MAX_PAGES)
                    or (key == "per_page" and re.fullmatch(r"[1-9][0-9]*", value) and int(value) <= 100)
                    or (key == "branch" and value == "main")
                    or (key == "created" and re.fullmatch(r">=[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value)
                        and re.fullmatch(r"actions/workflows/(?:ci|deliver)\.yml/runs", suffix))
                    or (key == "status" and value in {"queued", "requested", "waiting", "pending", "in_progress"})
                    or (key == "event" and value == "workflow_dispatch")):
                continue
            raise NightlyError("GitHub API query outside nightly contract")
        if method != "GET" and query:
            raise NightlyError("write request cannot have query parameters")
        return parsed.path

    def _headers(self, token):
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": API_VERSION,
                   "User-Agent": "Hexalith-CiCd-nightly"}
        if token is not None:
            if not token:
                raise NightlyError("scoped App token unavailable")
            self.budget.check(token=True)
            delivery._SECRETS.append(token)
            headers["Authorization"] = "Bearer " + token
        return headers

    def _remaining(self, token, deadline):
        remaining = self.budget.remaining(token=token is not None)
        if deadline is not None:
            remaining = min(remaining, number(deadline, positive=True) - self.budget.clock())
        return remaining

    def _retry_delay(self, headers, attempt):
        """Honor service minimum delays without trusting an unbounded sleep."""
        delays = []
        values = {str(key).lower(): value for key, value in (headers or {}).items()}
        after = values.get("retry-after")
        if isinstance(after, str):
            after = after.strip()
            if re.fullmatch(r"[0-9]+", after):
                if len(after) > 20:
                    raise NightlyError("GitHub API retry delay exceeds operation budget")
                delays.append(int(after))
            else:
                try:
                    instant = parsedate_to_datetime(after)
                    if instant.tzinfo is not None:
                        delays.append(max(0, instant.timestamp() - self.budget.clock()))
                except (TypeError, ValueError, OverflowError):
                    pass
        reset = values.get("x-ratelimit-reset")
        if isinstance(reset, str):
            reset = reset.strip()
        if (str(values.get("x-ratelimit-remaining", "")).strip() == "0"
                and isinstance(reset, str) and re.fullmatch(r"[0-9]+", reset)):
            if len(reset) > 20:
                raise NightlyError("GitHub API retry delay exceeds operation budget")
            delays.append(max(0, int(reset) - self.budget.clock()))
        # A secondary throttle can leave primary quota available. In that case
        # its primary reset is irrelevant; GitHub requires at least one minute
        # when no usable retry delay was supplied, followed by backoff.
        return max(delays) if delays else 60 * (attempt + 1)

    @staticmethod
    def _limited(status, headers):
        # GitHub reports primary and secondary rate limits as 403 or 429.
        values = {str(key).lower(): value for key, value in (headers or {}).items()}
        return status == 429 or status == 403 and (
            values.get("retry-after") is not None or str(values.get("x-ratelimit-remaining", "")).strip() == "0")

    def _http_diagnostic(self, error, token, attempt, deadline):
        """Retain bounded response evidence without exposing credentials or URLs."""
        details = {"authentication": "anonymous" if token is None else "scoped",
                   "attempts": attempt + 1}
        headers = {str(key).lower(): value for key, value in (error.headers or {}).items()}
        for key in ("x-github-request-id", "x-ratelimit-limit", "x-ratelimit-remaining",
                    "x-ratelimit-reset", "retry-after", "x-accepted-github-permissions"):
            value = headers.get(key)
            if isinstance(value, str):
                details[key] = clean(value)[:80]
        # HTTPError owns a response stream. Bound both its size and total read
        # time; an unreadable error body must never obscure the original status.
        try:
            remaining = self._remaining(token, deadline)
            if remaining >= 1:
                with whole_operation(min(2, remaining)):
                    payload = error.read(4097)
                if len(payload) <= 4096:
                    value = json_read(payload)
                    if isinstance(value, dict) and isinstance(value.get("message"), str):
                        details["message"] = clean(value["message"])[:240]
        except (NightlyError, OSError, ValueError, http.client.HTTPException):
            pass
        # Keep the complete object below clean's 2,000-character ceiling even
        # when every allowed field contains escaped controls or astral Unicode.
        return clean(json.dumps(details, ensure_ascii=False, separators=(",", ":")))

    def _request(self, method, path, token=None, document=None, *, deadline=None):
        self._path(path, method)
        parsed = urlsplit(path)
        wire_path = parsed.path + ("?" + urlencode(parse_qsl(parsed.query)) if parsed.query else "")
        data = None if document is None else json.dumps(document, separators=(",", ":")).encode()
        if data is not None and len(data) > MAX_JSON:
            raise NightlyError("API request exceeds JSON limit")
        for attempt in range(3 if method == "GET" else 1):
            self.calls += 1
            if self.calls > MAX_CALLS:
                raise NightlyError("GitHub API call limit exceeded")
            timeout = self.budget.timeout(token=token is not None, max_seconds=30)
            if deadline is not None:
                remaining = number(deadline, positive=True) - self.budget.clock()
                if remaining < 1:
                    raise NightlyError("GitHub API request deadline exhausted")
                timeout = min(timeout, remaining)
            headers = self._headers(token)
            if data is not None:
                headers["Content-Type"] = "application/json"
            try:
                with whole_operation(timeout, write=method != "GET"):
                    with self.opener.open(Request("https://api.github.com" + wire_path, data=data,
                                                 headers=headers, method=method), timeout=timeout) as response:
                        empty = method == "PUT"
                        if empty and response.status == 204:
                            if response.read(1):
                                raise NightlyError("GitHub API expected empty HTTP 204")
                            return None
                        if empty:
                            raise NightlyError("GitHub API expected empty HTTP 204; write result uncertain, not retried")
                        if response.status != 200:
                            # A write the service accepted without the expected
                            # reply may have dispatched/published: never definite.
                            raise NightlyError("GitHub API unexpected response status" + (
                                "; write result uncertain, not retried" if method != "GET" else ""))
                        payload = response.read(MAX_JSON + 1)
                        try:
                            value = json_read(payload)
                        except NightlyError as error:
                            if method != "GET":
                                raise NightlyError("GitHub API malformed write response; write result uncertain, not retried: "
                                                   + clean(error)) from None
                            raise
                    if method == "GET":
                        # A received write response is never discarded by a
                        # later budget check: its created identity must survive.
                        self.budget.check(token=token is not None)
                        if deadline is not None and self.budget.clock() >= deadline:
                            raise NightlyError("GitHub API request deadline exhausted")
                return value
            except HTTPError as error:
                try:
                    status = error.code
                    response_headers = error.headers
                    limited = self._limited(status, response_headers)
                    if method == "GET" and (limited or status in {500, 502, 503, 504}) and attempt < 2:
                        try:
                            delay = self._retry_delay(response_headers, attempt) if limited else attempt + 1
                        except NightlyError as failure:
                            diagnostic = self._http_diagnostic(error, token, attempt, deadline)
                            raise NightlyError(f"{clean(failure)}: HTTP {status}; {diagnostic}") from None
                        if self._remaining(token, deadline) < delay + 2:
                            diagnostic = self._http_diagnostic(error, token, attempt, deadline)
                            raise NightlyError("GitHub API retry budget exhausted: "
                                               f"HTTP {status}; {diagnostic}") from None
                        # Close before sleeping, without changing the retry or
                        # credential policy for any read or uncertain write.
                        error.close()
                        self.sleep(delay)
                        continue
                    qualifier = "rejected" if method != "GET" and status in {400, 401, 403, 404, 409, 422} else "failed"
                    diagnostic = self._http_diagnostic(error, token, attempt, deadline)
                    raise NightlyError(f"GitHub API {method} {self._path(path, method)} {qualifier}: "
                                       f"HTTP {status}; {diagnostic}") from None
                finally:
                    error.close()
            except (URLError, OSError, http.client.HTTPException):
                # An idempotent read survives one transient reset or timeout.
                if method == "GET" and attempt < 2:
                    if self._remaining(token, deadline) < attempt + 3:
                        raise NightlyError("GitHub API retry budget exhausted") from None
                    self.sleep(attempt + 1)
                    continue
                # A lost write response may already have dispatched/published. Never retry it.
                raise NightlyError("GitHub API transport failed" +
                                   ("; write result uncertain, not retried" if method != "GET" else "")) from None
        raise NightlyError("GitHub API retry limit exceeded")

    def get(self, path, token=None, *, deadline=None):
        return self._request("GET", path, token, deadline=deadline)

    def enable(self, workflow, token):
        if workflow not in {"nightly.yml", "deliver.yml"}:
            raise NightlyError("workflow enable outside nightly contract")
        return self._request("PUT", f"/repos/Hexalith/{CICD}/actions/workflows/{workflow}/enable", token)

    def dispatch_delivery(self, token):
        value = self._request("POST", f"/repos/Hexalith/{CICD}/actions/workflows/deliver.yml/dispatches",
                              token, {"ref": "main"})
        return dispatch_details(CICD, value)

    def pages(self, path, token=None, *, field=None, deadline=None):
        result, total = [], None
        for page in range(1, MAX_PAGES + 1):
            value = self.get(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}", token,
                             deadline=deadline)
            if field is not None:
                if not isinstance(value, dict) or type(value.get("total_count")) is not int or value["total_count"] < 0:
                    raise NightlyError("malformed paginated GitHub object")
                if total is not None and value["total_count"] != total:
                    raise NightlyError("GitHub paginated inventory changed")
                total = value["total_count"]
                value = value.get(field)
            if not isinstance(value, list) or len(value) > 100:
                raise NightlyError("malformed paginated GitHub list")
            result.extend(value)
            if len(value) < 100:
                if total is not None and total != len(result):
                    raise NightlyError("incomplete paginated GitHub inventory")
                return result
        raise NightlyError("GitHub API pagination limit exceeded")

    def dispatch(self, repository, workflow, inputs, token):
        expected = "builds-release.yml" if repository == BUILDS else "release.yml"
        if workflow not in {expected, ".github/workflows/" + expected} or not isinstance(inputs, dict):
            raise NightlyError("invalid release dispatch caller")
        if repository == BUILDS:
            if inputs:
                raise NightlyError("Builds dispatch accepts no module inputs")
        elif set(inputs) != {"delivered-sha"} or sha(inputs["delivered-sha"]) != inputs["delivered-sha"]:
            raise NightlyError("module dispatch requires exact delivered commit")
        value = self._request("POST", f"/repos/Hexalith/{repository}/actions/workflows/{expected}/dispatches", token,
                              {"ref": "main", "inputs": inputs, "return_run_details": True})
        return dispatch_details(repository, value)

    def patch(self, path, document, token, *, deadline=None):
        if (not isinstance(document, dict) or set(document) != {"tag_name", "target_commitish", "draft"}
                or document["draft"] is not False or not isinstance(document["tag_name"], str)
                or not TAG.fullmatch(document["tag_name"])):
            raise NightlyError("invalid draft publication request")
        sha(document["target_commitish"])
        return self._request("PATCH", path, token, document, deadline=deadline)

    def publish_draft(self, repository, identity, document, token):
        return self.patch(f"/repos/Hexalith/{repository}/releases/{positive(identity)}", document, token)

    def _artifact_payload(self, path, token):
        """One authenticated download attempt: (payload, None) or (None, transient reason)."""
        self.calls += 1
        if self.calls > MAX_CALLS:
            raise NightlyError("GitHub API call limit exceeded")
        try:
            timeout = self.budget.timeout(token=True, max_seconds=30)
            with whole_operation(timeout):
                request = Request("https://api.github.com" + path, headers=self._headers(token))
                try:
                    response = self.opener.open(request, timeout=timeout)
                except HTTPError as redirect:
                    try:
                        if redirect.code != 302:
                            if self._limited(redirect.code, redirect.headers):
                                return None, f"artifact download returned HTTP {redirect.code}", redirect.headers or {}
                            if redirect.code in {500, 502, 503, 504}:
                                return None, f"artifact download returned HTTP {redirect.code}", None
                            raise NightlyError(f"artifact download returned HTTP {redirect.code}")
                        location = redirect.headers.get("Location", "")
                        parsed = urlsplit(location)
                        if (parsed.scheme != "https" or parsed.port not in {None, 443}
                                or parsed.username is not None or parsed.password is not None or parsed.fragment
                                or not parsed.hostname or len(location) > 8192
                                or not re.fullmatch(r"[a-z0-9-]+\.(?:blob\.core\.windows\.net|actions\.githubusercontent\.com)", parsed.hostname)
                                or any(ord(c) < 32 for c in location)):
                            raise NightlyError("artifact redirect destination refused")
                    finally:
                        redirect.close()
                    # The signed artifact URL gets no installation Authorization header.
                    self.budget.check(token=True)
                    response = self.opener.open(Request(location, headers={"User-Agent": "Hexalith-CiCd-nightly"}),
                                                timeout=self.budget.timeout(token=True, max_seconds=30))
                with response:
                    if response.status != 200:
                        raise NightlyError("artifact download returned unexpected status")
                    payload = response.read(MAX_ZIP + 1)
                self.budget.check(token=True)
                return payload, None, None
        except (HTTPError, URLError, OSError, http.client.HTTPException, ValueError) as error:
            if isinstance(error, NightlyError):
                raise
            return None, "artifact download transport failed", None

    def artifact_member(self, repository, metadata, member, token):
        if (not isinstance(metadata, dict) or metadata.get("expired") is not False
                or not isinstance(metadata.get("digest"), str) or not DIGEST.fullmatch(metadata["digest"])
                or type(metadata.get("size_in_bytes")) is not int or not 1 <= metadata["size_in_bytes"] <= MAX_ZIP):
            raise NightlyError("artifact metadata is malformed, expired, or oversized")
        expires = timestamp(metadata.get("expires_at"))
        if expires.timestamp() <= self.budget.clock():
            raise NightlyError("artifact expiry could not be validated")
        identity = positive(metadata.get("id"))
        if member not in {"dispatch.json", "wait.json", "nightly.json", "outcome.json", "candidate.json", "delivery.json"}:
            raise NightlyError("artifact member outside nightly contract")
        path = f"/repos/Hexalith/{repository}/actions/artifacts/{identity}/zip"
        self._path(path)
        # Downloads are idempotent GETs: a transient API/storage failure is
        # retried boundedly with a freshly signed redirect, never forever.
        for attempt in range(3):
            payload, transient, limited = self._artifact_payload(path, token)
            if transient is None:
                break
            # Rate limits keep the service-directed minimum used by API reads.
            delay = self._retry_delay(limited, attempt) if limited is not None else attempt + 1
            if attempt == 2 or self.budget.remaining(token=True) < delay + 2:
                raise NightlyError(transient)
            self.sleep(delay)
        if (len(payload) > MAX_ZIP or len(payload) != metadata["size_in_bytes"]
                or "sha256:" + hashlib.sha256(payload).hexdigest() != metadata["digest"]):
            raise NightlyError("artifact ZIP size or digest mismatch")
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                members = archive.infolist()
                if len(members) != 1 or members[0].filename != member:
                    raise NightlyError("artifact must contain exactly its expected JSON member")
                item = members[0]
                mode = item.external_attr >> 16
                if (item.flag_bits & 1 or item.is_dir() or item.file_size > MAX_JSON or item.file_size < 1
                        or item.compress_size > MAX_ZIP or item.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                        or (mode and stat.S_IFMT(mode) not in {0, stat.S_IFREG})):
                    raise NightlyError("artifact member metadata refused")
                with archive.open(item) as stream:
                    data = stream.read(MAX_JSON + 1)
                if len(data) != item.file_size:
                    raise NightlyError("artifact member size mismatch")
                return json_read(data)
        except (zipfile.BadZipFile, RuntimeError, OSError, NotImplementedError):
            raise NightlyError("artifact ZIP is unreadable") from None


class Transport(delivery.Transport):
    def __init__(self, budget=None, api=None):
        self.budget = budget or Budget()
        self.api = api or API(self.budget)

    def helpers(self, tag, destination):
        """Authenticate release/tag/source, then import only committed tagged helpers."""
        git, exported = self.builds(tag, destination)
        source = git.resolve("refs/tags/" + tag + "^{commit}")
        return self._helpers(git, source, exported)

    def cached_helpers(self, tag, source, destination):
        """Reuse this job's authenticated objects, never another anonymous lookup."""
        if not isinstance(tag, str) or not TAG.fullmatch(tag):
            raise NightlyError("cached Builds tag identity malformed")
        source = sha(source)
        git = Git(Path(destination) / "objects", self.budget)
        git.env["GIT_NO_LAZY_FETCH"] = "1"
        if git.resolve("refs/tags/" + tag + "^{commit}") != source:
            raise NightlyError("cached Builds tag/source identity mismatch")
        exported = Path(destination) / "source"
        # Restore the imported tree from the authenticated objects rather than
        # trusting exported working bytes left by an earlier script process.
        git.export(source, "Github/lib", exported)
        git.export(source, "schemas", exported)
        return self._helpers(git, source, exported)

    def _helpers(self, git, source, exported):
        required = {
            "release_outcome": {"validate_outcome"},
            "release_complete": {"selected_draft"},
            "release_draft": {"release_trailers", "artifact_metadata"},
            "release_publish": {"validate_source", "validate_release", "version_tag", "producer", "finalize_release"},
            "release_state": {"highest_reachable_stable_tag"}}
        for module, functions in required.items():
            data = git.blob(source, "Github/lib/" + module + ".py")
            try:
                tree = ast.parse(data)
            except (SyntaxError, ValueError):
                raise NightlyError("pinned Builds release capability source is invalid") from None
            present = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
            if not functions <= present:
                raise NightlyError("pinned Builds release capability missing: " + module)
        schema = json_read(git.blob(source, "schemas/hexalith.release-outcome.v1.json"))
        if (not isinstance(schema, dict) or schema.get("properties", {}).get("schema", {}).get("const")
                != "hexalith.release-outcome.v1" or schema.get("additionalProperties") is not False):
            raise NightlyError("pinned Builds release outcome schema unavailable")
        helpers = load_helpers(exported)
        helpers.source = source
        return helpers


def load_helpers(root):
    """Import the exported trusted release helper tree (acquisition is separate)."""
    exported = Path(root).resolve()
    required = {
        "release_outcome": {"validate_outcome"},
        "release_complete": {"selected_draft"},
        "release_draft": {"release_trailers", "artifact_metadata"},
        "release_publish": {"validate_source", "validate_release", "version_tag", "producer", "finalize_release"},
        "release_state": {"highest_reachable_stable_tag"}}
    for module, functions in required.items():
        try:
            data = (exported / "Github/lib" / (module + ".py")).read_bytes()
            tree = ast.parse(data)
        except (OSError, SyntaxError, ValueError):
            raise NightlyError("pinned Builds release capability source unavailable") from None
        if not functions <= {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}:
            raise NightlyError("pinned Builds release capability missing: " + module)
    schema = json_read((exported / "schemas/hexalith.release-outcome.v1.json").read_bytes())
    if (not isinstance(schema, dict) or schema.get("properties", {}).get("schema", {}).get("const")
            != "hexalith.release-outcome.v1" or schema.get("additionalProperties") is not False):
        raise NightlyError("pinned Builds release outcome schema unavailable")
    library = exported / "Github/lib"
    names = {path.stem for path in library.glob("*.py")}
    # Helpers use sibling absolute imports. No mutable checkout is on sys.path.
    for module in names:
        sys.modules.pop(module, None)
    sys.path.insert(0, str(library))
    modules = {}
    try:
        for module in required:
            modules[module] = importlib.import_module(module)
        for module, functions in required.items():
            if any(not callable(getattr(modules[module], function, None)) for function in functions):
                raise NightlyError("pinned Builds release callable capability unavailable")
    except Exception as error:
        raise NightlyError("pinned Builds release import failed: " + clean(error)) from None
    finally:
        # Tagged helpers insert their own directory; remove every occurrence.
        sys.path[:] = [path for path in sys.path if path != str(library)]
    aliases = {key.removeprefix("release_"): value for key, value in modules.items()}
    return SimpleNamespace(root=exported, **modules, **aliases)

ROW_KEYS = frozenset(("repository", "workflow", "deliveredSha", "dispatchHead", "runId", "runAttempt", "link",
                     "eligibility", "dispatch", "status", "conclusion", "outcome", "outcomeError", "publication",
                     "verdict", "reason"))
STATE_KEYS = frozenset(("schema", "phase", "identity", "registry", "builds", "targets", "errors", "wait", "result"))


def _text(value):
    if not isinstance(value, str) or clean(value) != value:
        raise NightlyError("state diagnostic is malformed or exceeds bounds")


def validate_state(value, modules, identity=None, phase=None):
    """Closed handoff contract bound to this run and committed module registry."""
    if not isinstance(value, dict) or set(value) != STATE_KEYS or value["schema"] != SCHEMA:
        raise NightlyError("unsupported or malformed nightly state")
    if value["phase"] not in {"dispatch", "wait", "nightly"} or (phase is not None and value["phase"] != phase):
        raise NightlyError("nightly state phase mismatch")
    expected = sorted(name(module) for module in modules)
    if (len(expected) > CAPACITY or len({module.casefold() for module in expected}) != len(expected)
            or value["registry"] != expected):
        raise NightlyError("nightly state committed registry mismatch")
    if not isinstance(value["result"], str) or value["result"] not in {"pending", "pass", "fail"}:
        raise NightlyError("nightly aggregate result malformed")
    if value["phase"] != "nightly" and value["result"] != "pending":
        raise NightlyError("prepublication state cannot authorize an aggregate verdict")
    actual = value["identity"]
    if not isinstance(actual, dict) or set(actual) != {"runId", "attempt", "source"}:
        raise NightlyError("nightly state run identity malformed")
    positive(actual["runId"])
    positive(actual["attempt"])
    sha(actual["source"])
    if identity is not None and actual != identity:
        raise NightlyError("nightly state run/attempt/source identity mismatch")
    builds = value["builds"]
    if (not isinstance(builds, dict) or set(builds) != {"tag", "sha"}
            or not isinstance(builds["tag"], str)
            or not (TAG.fullmatch(builds["tag"]) or builds["tag"] == "" and value["errors"])):
        raise NightlyError("nightly state Builds identity malformed")
    if builds["sha"] != "":
        sha(builds["sha"])
    rows = value["targets"]
    if not isinstance(rows, list) or len(rows) != len(expected) + 1:
        raise NightlyError("nightly state target inventory mismatch")
    for row, repository in zip(rows, [*expected, BUILDS], strict=True):
        if not isinstance(row, dict) or set(row) != ROW_KEYS or row["repository"] != repository:
            raise NightlyError("nightly state target identity/fields mismatch")
        caller = ".github/workflows/" + ("builds-release.yml" if repository == BUILDS else "release.yml")
        if row["workflow"] != caller:
            raise NightlyError("nightly state target caller mismatch")
        for field in ("deliveredSha", "dispatchHead"):
            if row[field] != "":
                sha(row[field])
        for field in ("runId", "runAttempt"):
            if row[field] != 0:
                positive(row[field])
            elif type(row[field]) is not int:
                raise NightlyError("nightly state run identity malformed")
        if row["link"] != (run_link(repository, row["runId"]) if row["runId"] else ""):
            raise NightlyError("nightly state run link mismatch")
        for field, allowed in {
                "eligibility": {"pending", "eligible", "not-adopted", "failed"},
                "dispatch": {"pending", "dispatched", "failed", "skipped"},
                "publication": {"pending", "published", "failed", "skipped"},
                "verdict": {"pending", "pass", "fail", "skip"}}.items():
            if not isinstance(row[field], str) or row[field] not in allowed:
                raise NightlyError("nightly state verdict/state malformed")
        if value["phase"] != "nightly" and (row["publication"] != "pending" or row["verdict"] != "pending"):
            raise NightlyError("prepublication state cannot authorize verified publication")
        for field in ("status", "conclusion"):
            if not isinstance(row[field], str) or not re.fullmatch(r"[a-z_]{0,32}", row[field]):
                raise NightlyError("nightly state observation malformed")
        for field in ("outcomeError", "reason"):
            _text(row[field])
        if row["outcome"] is not None and not isinstance(row["outcome"], dict):
            raise NightlyError("nightly state outcome must be an object or null")
        if row["dispatch"] == "dispatched" and (not row["runId"] or not row["dispatchHead"] or row["runAttempt"] < 1):
            raise NightlyError("nightly state dispatched target has incomplete run identity")
    if not isinstance(value["errors"], list) or len(value["errors"]) > 100:
        raise NightlyError("nightly state errors exceed bounds")
    for error in value["errors"]:
        _text(error)
    wait = value["wait"]
    if wait is not None:
        if not isinstance(wait, dict) or set(wait) != {"started", "deadline"}:
            raise NightlyError("nightly wait clock malformed")
        number(wait["started"], positive=True)
        number(wait["deadline"], positive=True)
        if wait["deadline"] != wait["started"] + 300 * 60:
            raise NightlyError("nightly aggregate wait deadline mismatch")
    if value["phase"] == "dispatch" and wait is not None:
        raise NightlyError("dispatch state cannot contain a wait deadline")
    if value["phase"] in {"wait", "nightly"} and wait is None and (not value["errors"] or any(
            row["dispatch"] == "dispatched" or row["status"] or row["outcome"] is not None for row in rows)):
        raise NightlyError("observed nightly state requires its aggregate wait clock")
    return value


def read_state(path, modules, identity=None, phase=None):
    return validate_state(delivery.read_state(Path(path)), modules, identity=identity, phase=phase)
