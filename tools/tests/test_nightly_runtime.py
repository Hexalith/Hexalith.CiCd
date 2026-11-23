#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Bounded clocks, fixed endpoints, authenticated snapshots and hostile handoffs."""
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import tempfile
import time
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError
import zipfile

import nightly_support
from nightly_support import (ROOT, TAG, RELEASE, Clock, Opener, Workspace, fixture_transport,
                             git, load, metadata, zip_document)

rt = load(ROOT / "tools/nightly_runtime.py", "_nightly_runtime_tests")


def state(modules=("Hexalith.Alpha",)):
    rows = []
    for repository in [*modules, rt.BUILDS]:
        rows.append({"repository": repository, "workflow": ".github/workflows/" + (
            "builds-release.yml" if repository == rt.BUILDS else "release.yml"), "deliveredSha": "", "dispatchHead": "",
            "runId": 0, "runAttempt": 0, "link": "", "eligibility": "pending", "dispatch": "pending", "status": "",
            "conclusion": "", "outcome": None, "outcomeError": "", "publication": "pending", "verdict": "pending", "reason": ""})
    return {"schema": rt.SCHEMA, "phase": "dispatch", "identity": {"runId": 101, "attempt": 1, "source": "a" * 40},
            "registry": list(modules), "builds": {"tag": TAG, "sha": RELEASE}, "targets": rows, "errors": [],
            "wait": None, "result": "pending"}


class RuntimeTests(unittest.TestCase):
    def api(self, responses, *, clock=None, repositories=(rt.CICD, rt.BUILDS, "Hexalith.Alpha")):
        clock = clock or Clock()
        opener = Opener(responses)
        api = rt.API(rt.Budget(clock(), token_epoch=clock(), clock=clock), repositories=repositories,
                     opener=opener, sleep=clock.sleep)
        return api, opener, clock

    def test_strict_json_and_token_redaction(self):
        for payload in (b'{"a":1,"a":2}', b'{"a":Infinity}', b'\xff', b" " * (rt.MAX_JSON + 1)):
            with self.assertRaises(rt.NightlyError):
                rt.json_read(payload)
        with mock.patch.dict(os.environ, {key: "secret-" + key for key in rt.TOKEN_NAMES}, clear=True):
            tokens = rt.sanitize()
            for key in rt.TOKEN_NAMES:
                self.assertEqual(tokens[key], "secret-" + key)
                self.assertNotIn("secret-" + key, rt.clean("error " + tokens[key]))
                self.assertNotIn(key, os.environ)
            self.assertEqual(os.environ["GIT_TERMINAL_PROMPT"], "0")

    def test_bump_delivery_ci_endpoints_and_exact_empty_enable(self):
        identity = 43643156668
        reply = {"workflow_run_id": identity, "run_url": f"https://api.github.com/repos/Hexalith/{rt.CICD}/actions/runs/{identity}",
                 "html_url": rt.run_link(rt.CICD, identity)}
        api, opener, _ = self.api([(204, b""), (204, b""), reply, {}, {}, {}])
        self.assertIsNone(api.enable("nightly.yml", "inert"))
        self.assertIsNone(api.enable("deliver.yml", "inert"))
        self.assertEqual(api.dispatch_delivery("inert"), {"runId": identity, "link": reply["html_url"]})
        api.get("/repos/Hexalith/Hexalith.Alpha/actions/workflows/ci.yml/runs?branch=main", "inert")
        api.get("/repos/Hexalith/Hexalith.CiCd/actions/runs/123/attempts/2/jobs?per_page=100&page=1", "inert")
        api.get("/repos/Hexalith/Hexalith.Builds/releases?per_page=100&page=1")
        self.assertEqual([request.get_method() for request, _ in opener.requests], ["PUT", "PUT", "POST", "GET", "GET", "GET"])
        for responses in ([(200, {})], [(204, b"unexpected")], [(403, {})], [URLError("reset")]):
            api, opener, _ = self.api(responses)
            with self.assertRaises(rt.NightlyError):
                api.enable("nightly.yml", "inert")
            self.assertEqual(len(opener.requests), 1)
        api, opener, _ = self.api([])
        for workflow in ("ci.yml", "release.yml", "../nightly.yml"):
            with self.assertRaises(rt.NightlyError):
                api.enable(workflow, "inert")
        with self.assertRaises(rt.NightlyError):
            api._request("PUT", "/repos/Hexalith/Hexalith.Alpha/actions/workflows/nightly.yml/enable", "inert")
        with self.assertRaises(rt.NightlyError):
            api._request("POST", "/repos/Hexalith/Hexalith.Alpha/actions/workflows/deliver.yml/dispatches", "inert")
        self.assertFalse(opener.requests)
        self.assertEqual(api._path("/repos/Hexalith/Hexalith.CiCd/actions/workflows/deliver.yml/runs?branch=main&created=>=2026-11-14T02:17:00Z"),
                         "/repos/Hexalith/Hexalith.CiCd/actions/workflows/deliver.yml/runs")
        with self.assertRaises(rt.NightlyError):
            api._path("/repos/Hexalith/Hexalith.Builds/releases?created=>=2026-11-14T02:17:00Z")
        api, opener, _ = self.api([{}])
        api.get("/repos/Hexalith/Hexalith.CiCd/actions/workflows/deliver.yml/runs?branch=main&created=>=2026-11-14T02:17:00Z", "inert")
        self.assertIn("created=%3E%3D2026-11-14T02%3A17%3A00Z", opener.requests[0][0].full_url)

    def test_delivery_dispatch_requires_current_200_exact_run_details_without_retries(self):
        identity = 43643156668
        reply = {"workflow_run_id": identity, "run_url": f"https://api.github.com/repos/Hexalith/{rt.CICD}/actions/runs/{identity}",
                 "html_url": rt.run_link(rt.CICD, identity)}
        api, opener, clock = self.api([reply])
        self.assertEqual(api.dispatch_delivery("inert"), {"runId": identity, "link": reply["html_url"]})
        request, _ = opener.requests[0]
        self.assertEqual(request.full_url, f"https://api.github.com/repos/Hexalith/{rt.CICD}/actions/workflows/deliver.yml/dispatches")
        self.assertEqual((request.get_method(), json.loads(request.data)), ("POST", {"ref": "main"}))
        self.assertEqual(request.get_header("X-github-api-version"), "2026-03-10")
        self.assertEqual((len(opener.requests), clock.sleeps), (1, []))
        malformed = (None, [], {}, reply | {"workflow_run_id": True}, reply | {"workflow_run_id": "43643156668"},
                     reply | {"workflow_run_id": 0}, reply | {"html_url": "https://evil.invalid/run"},
                     reply | {"html_url": rt.run_link("Hexalith.Other", identity)},
                     reply | {"html_url": rt.run_link(rt.CICD, identity + 1)},
                     reply | {"run_url": f"https://api.github.com/repos/Hexalith/Other/actions/runs/{identity}"},
                     reply | {"run_url": f"https://api.github.com/repos/Hexalith/{rt.CICD}/actions/runs/{identity + 1}"},
                     b'{"workflow_run_id":1,"workflow_run_id":2}', b'{', (204, b""), (204, b"unexpected"))
        for response in malformed:
            with self.subTest(response=response):
                api, opener, clock = self.api([response, reply])
                with self.assertRaisesRegex(rt.NightlyError, "uncertain"):
                    api.dispatch_delivery("inert")
                self.assertEqual((len(opener.requests), clock.sleeps), (1, []))
        for response in ((403, {}), (503, {}), URLError("lost dispatch response")):
            with self.subTest(response=response):
                api, opener, clock = self.api([response, reply])
                with self.assertRaises(rt.NightlyError):
                    api.dispatch_delivery("inert")
                self.assertEqual((len(opener.requests), clock.sleeps), (1, []))

    def test_exact_new_json_artifact_members_are_bounded_and_duplicate_rejecting(self):
        for member in ("candidate.json", "delivery.json"):
            for value in ({"schema": "fixture"}, b'{"same":1,"same":2}'):
                if isinstance(value, bytes):
                    stream = io.BytesIO()
                    with zipfile.ZipFile(stream, "w") as archive:
                        archive.writestr(member, value)
                    payload = stream.getvalue()
                else:
                    payload = zip_document(member, value)
                api, _, _ = self.api([payload])
                info = metadata(8, "fixture", payload, 101, "a" * 40)
                if isinstance(value, bytes):
                    with self.assertRaisesRegex(rt.NightlyError, "duplicate JSON"):
                        api.artifact_member(rt.CICD, info, member, "inert")
                else:
                    self.assertEqual(api.artifact_member(rt.CICD, info, member, "inert"), value)

    def test_conservative_epochs_and_operation_timeouts(self):
        clock = Clock()
        budget = rt.Budget(clock(), job_seconds=330 * 60, token_epoch=clock(), clock=clock)
        clock.sleep(49 * 60)
        self.assertEqual(budget.timeout(token=True), 30)
        clock.sleep(30)
        with self.assertRaises(rt.NightlyError):
            budget.check(token=True)
        budget.token_epoch = clock()
        budget.check(token=True)
        with self.assertRaises(rt.NightlyError):
            rt.Budget(clock(), token_epoch=None, clock=clock).check(token=True)
        budget = rt.Budget(clock(), deadline=clock() + 7, token_epoch=clock(), clock=clock)
        self.assertEqual(budget.timeout(token=True), 7)
        clock.value -= 1
        with self.assertRaises(rt.NightlyError):
            budget.check()

    def test_fixed_origins_repository_scope_and_narrow_operations(self):
        api, opener, _ = self.api([{}] * 20)
        for path in ("https://evil.invalid", "/repos/Evil/Hexalith.Alpha/releases", "/repos/Hexalith/Other/releases",
                     "/repos/Hexalith/Hexalith.Alpha/../releases", "/repos/Hexalith/Hexalith.Alpha/secrets",
                     "/repos/Hexalith/Hexalith.Alpha/releases#x", "/repos/Hexalith/Hexalith.Alpha/releases?url=evil",
                     "/repos/Hexalith/Hexalith.Alpha/releases?page=1&page=2", "/repos/Hexalith/Hexalith.Alpha/releases?page=21"):
            with self.subTest(path=path), self.assertRaises(rt.NightlyError):
                api.get(path, "inert")
        self.assertEqual(opener.requests, [])
        api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert")
        request, timeout = opener.requests[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer inert")
        self.assertEqual(request.get_header("X-github-api-version"), "2026-03-10")
        self.assertLessEqual(timeout, 30)

    def test_retry_get_and_do_not_retry_uncertain_writes(self):
        api, opener, clock = self.api([(503, {}), (429, {}), {"enabled": True}])
        self.assertEqual(api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert"), {"enabled": True})
        self.assertEqual(clock.sleeps, [1, 120])
        self.assertEqual(len(opener.requests), 3)
        api, opener, _ = self.api([URLError("token-bearing transport body"), {}])
        with self.assertRaisesRegex(rt.NightlyError, "uncertain, not retried"):
            api.dispatch(rt.BUILDS, "builds-release.yml", {}, "inert")
        self.assertEqual(len(opener.requests), 1)
        api, opener, _ = self.api([(403, {})])
        with self.assertRaisesRegex(rt.NightlyError, "rejected: HTTP 403"):
            api.dispatch(rt.BUILDS, "builds-release.yml", {}, "inert")
        self.assertEqual(len(opener.requests), 1)

    def test_rate_limit_headers_set_the_retry_minimum(self):
        for headers, delay in (({"Retry-After": "9"}, 9),
                ({"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(Clock()() + 13))}, 13),
                ({"Retry-After": format_datetime(datetime.fromtimestamp(Clock()() + 7, timezone.utc), usegmt=True)}, 7),
                ({"Retry-After": "9", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(Clock()() + 13))}, 13),
                ({"Retry-After": "9", "X-RateLimit-Remaining": "10", "X-RateLimit-Reset": str(int(Clock()() + 300))}, 9),
                ({"X-RateLimit-Remaining": "10", "X-RateLimit-Reset": str(int(Clock()() + 300))}, 60),
                ({"Retry-After": "malformed"}, 60), ({}, 60)):
            with self.subTest(headers=headers):
                api, opener, clock = self.api([(429, {}, headers), {"enabled": True}])
                self.assertEqual(api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert"), {"enabled": True})
                self.assertEqual(clock.sleeps, [delay])
                self.assertEqual(len(opener.requests), 2)

    def test_rate_limited_403_is_retried_but_permission_403_is_not(self):
        for headers, delay in (({"Retry-After": "9"}, 9),
                ({"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(Clock()() + 13))}, 13)):
            with self.subTest(headers=headers):
                api, opener, clock = self.api([(403, {}, headers), {"enabled": True}])
                self.assertEqual(api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert"), {"enabled": True})
                self.assertEqual((clock.sleeps, len(opener.requests)), ([delay], 2))
        api, opener, clock = self.api([(403, {}, {"X-RateLimit-Remaining": "10"}), {"enabled": True}])
        with self.assertRaisesRegex(rt.NightlyError, "failed: HTTP 403"):
            api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert")
        self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))
        api, opener, _ = self.api([(403, {}, {"Retry-After": "1"})])
        with self.assertRaisesRegex(rt.NightlyError, "rejected: HTTP 403"):
            api.dispatch(rt.BUILDS, "builds-release.yml", {}, "inert")
        self.assertEqual(len(opener.requests), 1)

    def test_terminal_403_retains_actual_response_and_authentication_context(self):
        path = "/repos/Hexalith/Hexalith.Builds/releases/tags/" + TAG
        headers = {"X-RateLimit-Limit": "60", "X-RateLimit-Remaining": "0",
                   "X-RateLimit-Reset": str(int(Clock()() + 9)), "X-GitHub-Request-Id": "ABCD:1234"}
        errors = [HTTPError("https://api.github.com" + path, 403, "Forbidden", headers,
                            io.BytesIO(b'{"message":"API rate limit exceeded"}')) for _ in range(3)]
        api, opener, clock = self.api(errors)
        with self.assertRaises(rt.NightlyError) as failure:
            api.get(path)
        diagnostic = json.loads(str(failure.exception).split("; ", 1)[1])
        self.assertEqual(diagnostic, {"authentication": "anonymous", "attempts": 3, "body_status": "message",
            "x-ratelimit-limit": "60", "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": headers["X-RateLimit-Reset"], "x-github-request-id": "ABCD:1234",
            "message": "API rate limit exceeded"})
        self.assertEqual((clock.sleeps, len(opener.requests)), ([9, 0], 3))
        self.assertTrue(all(request.get_header("Authorization") is None for request, _ in opener.requests))
        self.assertTrue(all(error.closed for error in errors))

        error = HTTPError("https://api.github.com" + path, 403, "Forbidden",
            {"X-RateLimit-Remaining": "4999", "X-Accepted-GitHub-Permissions": "contents=read"},
            io.BytesIO(b'{"message":"Resource not accessible by integration"}'))
        api, opener, clock = self.api([error, {}])
        with self.assertRaises(rt.NightlyError) as failure:
            api.get(path, "inert")
        diagnostic = json.loads(str(failure.exception).split("; ", 1)[1])
        self.assertEqual(diagnostic, {"authentication": "scoped", "attempts": 1, "body_status": "message",
            "x-ratelimit-remaining": "4999", "x-accepted-github-permissions": "contents=read",
            "message": "Resource not accessible by integration"})
        self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))

    def test_error_diagnostics_are_bounded_redacted_and_do_not_retry_writes(self):
        secret = "diagnostic-test-token"
        other_secret = "diagnostic-poll-token"
        rt.delivery._SECRETS.append(other_secret)
        self.addCleanup(rt.delivery._SECRETS.remove, other_secret)
        error = HTTPError("https://api.github.com/?secret=" + secret, 403, secret,
            {"X-GitHub-Request-Id": secret + "\nrequest", "Location": "https://example.com/" + secret},
            io.BytesIO(json.dumps({"message": secret + " " + other_secret + " https://example.com/?sig=unfamiliar-secret\n" + "x" * 500,
                                   "other": secret}).encode()))
        api, opener, clock = self.api([error, {}])
        with self.assertRaises(rt.NightlyError) as failure:
            api.dispatch(rt.BUILDS, "builds-release.yml", {}, secret)
        message = str(failure.exception)
        self.assertNotIn(secret, message)
        self.assertNotIn(other_secret, message)
        self.assertNotIn("Location", message)
        self.assertNotIn("example.com", message)
        self.assertNotIn("unfamiliar-secret", message)
        self.assertNotIn("\n", message)
        diagnostic = json.loads(message.split("; ", 1)[1])
        self.assertLessEqual(len(diagnostic["message"]), 240)
        self.assertIn("[redacted]", diagnostic["message"])
        self.assertIn("[URL omitted]", diagnostic["message"])
        self.assertTrue(diagnostic["message"].endswith("...[truncated]"))
        self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))
        self.assertTrue(error.closed)

    def test_unreadable_error_body_preserves_http_failure_and_retry_budget(self):
        class Unreadable(io.BytesIO):
            def read(self, size):
                raise OSError("private response failure")

        for payload, expected_status in ((b"not JSON", "invalid-json"), (b"x" * 4097, "oversized"),
                                         (b'{"message":null}', "no-message"), (Unreadable(), "unreadable")):
            with self.subTest(payload=type(payload).__name__):
                stream = io.BytesIO(payload) if isinstance(payload, bytes) else payload
                error = HTTPError("https://api.github.com/private", 403, "Forbidden", {}, stream)
                api, opener, clock = self.api([error])
                with self.assertRaisesRegex(rt.NightlyError, "failed: HTTP 403") as failure:
                    api.get("/repos/Hexalith/Hexalith.Builds/releases/tags/" + TAG)
                diagnostic = json.loads(str(failure.exception).split("; ", 1)[1])
                self.assertNotIn("message", diagnostic)
                self.assertEqual(diagnostic["body_status"], expected_status)
                self.assertEqual(len(opener.requests), 1)
                self.assertTrue(error.closed)

        for method, path in (("PUT", "/repos/Hexalith/Hexalith.CiCd/actions/workflows/nightly.yml/enable"),
                             ("PATCH", "/repos/Hexalith/Hexalith.Builds/releases/123")):
            error = HTTPError("https://api.github.com/private", 403, "Forbidden", {}, Unreadable())
            api, opener, clock = self.api([error, {}])
            with self.assertRaisesRegex(rt.NightlyError, "rejected: HTTP 403") as failure:
                api._request(method, path, "inert")
            self.assertIn('"body_status":"unreadable"', str(failure.exception))
            self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))
        api, opener, clock = self.api([(403, {}, {"Retry-After": "600"})])
        api.budget.job_seconds = 300
        with self.assertRaisesRegex(rt.NightlyError, "retry budget exhausted: HTTP 403") as failure:
            api.get("/repos/Hexalith/Hexalith.Builds/releases/tags/" + TAG)
        self.assertIn('"retry-after":"600"', str(failure.exception))
        self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))

    def test_error_body_cannot_extend_the_whole_operation_deadline(self):
        class Slow(io.BytesIO):
            def read(self, size):
                time.sleep(10)
                raise AssertionError("diagnostic read exceeded its deadline")

        error = HTTPError("https://api.github.com/private", 403, "Forbidden", {}, Slow())
        api, opener, _ = self.api([error])
        started = time.monotonic()
        with self.assertRaisesRegex(rt.NightlyError, "failed: HTTP 403"):
            api.get("/repos/Hexalith/Hexalith.Builds/releases/tags/" + TAG)
        self.assertLess(time.monotonic() - started, 4)
        self.assertEqual(len(opener.requests), 1)
        self.assertTrue(error.closed)

    def test_unicode_and_malformed_retry_headers_retain_complete_diagnostics(self):
        headers = {key: "\U0001f600\n" * 100 for key in (
            "X-GitHub-Request-Id", "X-RateLimit-Limit", "X-RateLimit-Remaining",
            "X-RateLimit-Reset", "Retry-After", "X-Accepted-GitHub-Permissions")}
        for replacement in ({}, {"Retry-After": "9" * 21},
                            {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "9" * 21}):
            with self.subTest(replacement=replacement):
                error = HTTPError("https://api.github.com/private", 403, "Forbidden", headers | replacement,
                    io.BytesIO(json.dumps({"message": "\U0001f600" * 240}).encode()))
                api, opener, clock = self.api([error])
                # A budget refusal or an invalid delay must retain evidence
                # rather than sleeping or silently discarding the response.
                api.budget.job_seconds = 60
                with self.assertRaisesRegex(rt.NightlyError, "HTTP 403") as failure:
                    api.get("/repos/Hexalith/Hexalith.Builds/releases/tags/" + TAG)
                diagnostic = json.loads(str(failure.exception).split("; ", 1)[1])
                self.assertEqual(diagnostic["message"], "\U0001f600" * 240)
                self.assertEqual(diagnostic["authentication"], "anonymous")
                self.assertEqual(diagnostic["attempts"], 1)
                self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))
                self.assertTrue(error.closed)

    def test_retry_refusals_identify_only_the_validated_endpoint(self):
        path = "/repos/Hexalith/Hexalith.Builds/releases"
        query = "?per_page=100&page=2"
        token = "scoped-retry-test-token"
        for delay, reason in (("9" * 21, "retry delay exceeds"), ("300", "retry budget exhausted")):
            with self.subTest(reason=reason):
                error = HTTPError("https://api.github.com" + path + query, 429, token,
                    {"Retry-After": delay, "X-GitHub-Request-Id": "fixture"},
                    io.BytesIO(json.dumps({"message": token + " https://example.invalid/private?sig=secret"}).encode()))
                api, opener, clock = self.api([error])
                api.budget.job_seconds = 60
                with self.assertRaises(rt.NightlyError) as failure:
                    api.get(path + query, token)
                message, evidence = str(failure.exception).split("; ", 1)
                self.assertIn("GET " + path, message)
                self.assertIn(reason, message)
                self.assertIn("HTTP 429", message)
                self.assertNotIn("?", str(failure.exception))
                self.assertNotIn(token, str(failure.exception))
                details = json.loads(evidence)
                self.assertEqual(details["message"], "[redacted] [URL omitted]")
                self.assertEqual((details["x-github-request-id"], details["attempts"]), ("fixture", 1))
                self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))
                self.assertTrue(error.closed)

        api, opener, clock = self.api([URLError("private transport error")])
        with self.assertRaises(rt.NightlyError) as failure:
            api.get(path + query, deadline=clock() + 2)
        self.assertEqual(str(failure.exception), f"GitHub API GET {path} retry budget exhausted")
        self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))

    def test_diagnostic_read_respects_short_job_token_and_caller_budgets(self):
        class Slow(io.BytesIO):
            def read(self, size):
                time.sleep(10)
                raise AssertionError("read escaped its enclosing budget")

        for limit in ("job", "token", "caller"):
            with self.subTest(limit=limit):
                error = HTTPError("https://api.github.com/private", 403, "Forbidden", {}, Slow())
                api, opener, _ = self.api([error])
                now = time.time()
                api.budget = rt.Budget(now, token_epoch=now)
                deadline = None
                if limit == "job":
                    api.budget.job_seconds = 31.1
                elif limit == "token":
                    api.budget.token_epoch = now - (50 * 60 - 30 - 1.1)
                else:
                    deadline = now + 1.1
                started = time.monotonic()
                with self.assertRaisesRegex(rt.NightlyError, "failed: HTTP 403"):
                    api.get("/repos/Hexalith/Hexalith.Builds/releases/tags/" + TAG, "inert", deadline=deadline)
                self.assertLess(time.monotonic() - started, 2)
                self.assertEqual(len(opener.requests), 1)
                self.assertTrue(error.closed)
        error = HTTPError("https://api.github.com/private", 403, "Forbidden", {}, Slow())
        api, _, clock = self.api([])
        diagnostic = json.loads(api._http_diagnostic(error, None, 0, clock() - 1))
        self.assertEqual(diagnostic["body_status"], "budget-exhausted")
        self.assertEqual(error.tell(), 0)
        error.close()

    def test_terminal_429_and_5xx_keep_final_response_evidence(self):
        for status in (429, 503):
            errors = [HTTPError("https://api.github.com/private", status, "error", {"X-GitHub-Request-Id": str(i)},
                                io.BytesIO(b'{"message":"final response"}')) for i in range(3)]
            api, opener, clock = self.api(errors)
            with self.assertRaisesRegex(rt.NightlyError, "HTTP " + str(status)) as failure:
                api.get("/repos/Hexalith/Hexalith.Builds/releases/tags/" + TAG)
            diagnostic = json.loads(str(failure.exception).split("; ", 1)[1])
            self.assertEqual((diagnostic["attempts"], diagnostic["x-github-request-id"]), (3, "2"))
            self.assertEqual(clock.sleeps, [60, 120] if status == 429 else [1, 2])
            self.assertEqual(len(opener.requests), 3)
            self.assertTrue(all(error.closed for error in errors))

    def test_transient_artifact_download_failures_retry_with_a_fresh_redirect(self):
        payload = zip_document("outcome.json", {"ok": True})
        info = metadata(8, "x", payload, 9, "a" * 40)
        location = {"Location": "https://productionresultssa1.blob.core.windows.net/a?sig=secret"}
        api, opener, clock = self.api([(502, {}), (302, {}, location), URLError("storage reset"),
                                       (302, {}, location), payload])
        self.assertEqual(api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert"), {"ok": True})
        self.assertEqual(clock.sleeps, [1, 2])
        self.assertEqual([request.get_header("Authorization") for request, _ in opener.requests],
                         ["Bearer inert", "Bearer inert", None, "Bearer inert", None])
        api, opener, _ = self.api([(503, {}), (503, {}), (503, {})])
        with self.assertRaisesRegex(rt.NightlyError, "HTTP 503"):
            api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert")
        self.assertEqual(len(opener.requests), 3)
        api, opener, _ = self.api([(404, {})])
        with self.assertRaisesRegex(rt.NightlyError, "HTTP 404"):
            api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert")
        self.assertEqual(len(opener.requests), 1)

    def test_transport_reset_retries_reads_but_never_writes(self):
        api, opener, clock = self.api([URLError("connection reset"), TimeoutError("read timeout"), {"enabled": True}])
        self.assertEqual(api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert"), {"enabled": True})
        self.assertEqual((clock.sleeps, len(opener.requests)), ([1, 2], 3))
        api, opener, _ = self.api([URLError("reset")] * 3)
        with self.assertRaisesRegex(rt.NightlyError, "transport failed$"):
            api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert")
        self.assertEqual(len(opener.requests), 3)
        api, opener, clock = self.api([URLError("reset"), {"enabled": True}])
        with self.assertRaisesRegex(rt.NightlyError, "retry budget"):
            api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert", deadline=clock() + 2)
        self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))

    def test_received_write_reply_is_never_a_definite_failure(self):
        repository, identity = "Hexalith.Alpha", 987
        reply = {"workflow_run_id": identity, "run_url": f"https://api.github.com/repos/Hexalith/{repository}/actions/runs/{identity}",
                 "html_url": rt.run_link(repository, identity)}
        class Wire(Opener):
            def __init__(self, response, clock, elapsed=0):
                super().__init__([])
                self.response, self.clock, self.elapsed = response, clock, elapsed
            def open(self, request, timeout):
                self.requests.append((request, timeout))
                self.clock.value += self.elapsed
                return self.response
        clock = Clock()
        wire = Wire(nightly_support.Response(b"", status=204), clock)
        api = rt.API(rt.Budget(clock(), token_epoch=clock(), clock=clock), repositories=(rt.BUILDS, repository),
                     opener=wire, sleep=clock.sleep)
        with self.assertRaisesRegex(rt.NightlyError, "unexpected response status; write result uncertain, not retried"):
            api.dispatch(repository, "release.yml", {"delivered-sha": "b" * 40}, "inert")
        self.assertEqual(len(wire.requests), 1)
        # A created run returned at the request's deadline keeps its exact identity.
        clock = Clock()
        wire = Wire(nightly_support.Response(reply), clock, elapsed=50 * 60)
        api = rt.API(rt.Budget(clock(), job_seconds=50 * 60, token_epoch=clock(), clock=clock),
                     repositories=(rt.BUILDS, repository), opener=wire, sleep=clock.sleep)
        self.assertEqual(api.dispatch(repository, "release.yml", {"delivered-sha": "b" * 40}, "inert"),
                         {"runId": identity, "link": reply["html_url"]})
        wire = Wire(nightly_support.Response({"enabled": True}), clock)
        api.opener = wire
        with self.assertRaises(rt.NightlyError):
            api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert")

    def test_rate_limited_artifact_downloads_wait_the_service_minimum(self):
        payload = zip_document("outcome.json", {"ok": True})
        info = metadata(8, "x", payload, 9, "a" * 40)
        location = {"Location": "https://productionresultssa1.blob.core.windows.net/a?sig=secret"}
        for status, headers, delay in ((429, {"Retry-After": "60"}, 60), (403, {"Retry-After": "45"}, 45),
                                       (403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(Clock()() + 70))}, 70),
                                       (429, {}, 60)):
            with self.subTest(status=status, headers=headers):
                api, opener, clock = self.api([(status, {}, headers), (302, {}, location), payload])
                self.assertEqual(api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert"), {"ok": True})
                self.assertEqual((clock.sleeps, len(opener.requests)), ([delay], 3))
        api, opener, clock = self.api([(403, {}, {"X-RateLimit-Remaining": "10"})])
        with self.assertRaisesRegex(rt.NightlyError, "HTTP 403"):
            api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert")
        self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))
        api, opener, clock = self.api([(429, {}, {"Retry-After": "600"})])
        api.budget.job_seconds = 300
        with self.assertRaisesRegex(rt.NightlyError, "HTTP 429"):
            api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert")
        self.assertEqual((clock.sleeps, len(opener.requests)), ([], 1))

    def test_rate_limit_delay_must_fit_operation_token_and_job_windows(self):
        for limit in ("operation", "token", "job"):
            with self.subTest(limit=limit):
                api, opener, clock = self.api([(429, {}, {"Retry-After": "10"}), {"enabled": True}])
                deadline = clock() + 10 if limit == "operation" else None
                if limit == "token":
                    api.budget.token_epoch = clock() - (50 * 60 - 40)
                if limit == "job":
                    api.budget.job_seconds = 40
                with self.assertRaisesRegex(rt.NightlyError, "retry budget"):
                    api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert", deadline=deadline)
                self.assertEqual(len(opener.requests), 1)
                self.assertFalse(clock.sleeps)

    def test_paginated_deadline_includes_prior_pages_reads_and_retries(self):
        clock = Clock()
        base = Opener([(503, {}), {"total_count": 101, "artifacts": [{}] * 100},
                       {"total_count": 101, "artifacts": [{}]}])
        class ElapsedOpener:
            def open(self, request, timeout):
                clock.value += 9
                return base.open(request, timeout)
        api = rt.API(rt.Budget(clock(), token_epoch=clock(), clock=clock), repositories=("Hexalith.Alpha",),
                     opener=ElapsedOpener(), sleep=clock.sleep)
        started = clock()
        with self.assertRaisesRegex(rt.NightlyError, "request deadline"):
            api.pages("/repos/Hexalith/Hexalith.Alpha/actions/runs/9/artifacts", "inert", field="artifacts",
                      deadline=started + 25)
        self.assertEqual(len(base.requests), 3)
        self.assertEqual(clock.sleeps, [1])
        self.assertEqual([timeout for _, timeout in base.requests], [25, 15, 6])

    def test_whole_operation_deadline_interrupts_acquisition_and_dribbling_reads(self):
        class ShortBudget(rt.Budget):
            def timeout(self, **kwargs):
                return min(0.02, super().timeout(**kwargs))
        class SlowResponse(io.BytesIO):
            status = 200
            def read(self, limit):
                # Every individual piece arrives before the socket inactivity
                # timeout; only the whole-operation alarm bounds the sequence.
                for _ in range(100):
                    time.sleep(0.005)
                return super().read(limit)
        for stage in ("acquisition", "read"):
            for method in ("GET", "POST"):
                with self.subTest(stage=stage, method=method):
                    responses = []
                    class SlowOpener:
                        calls = 0
                        def open(self, request, timeout):
                            self.calls += 1
                            if stage == "acquisition":
                                time.sleep(0.5)
                            response = SlowResponse(b"{}")
                            responses.append(response)
                            return response
                    opener = SlowOpener()
                    api = rt.API(ShortBudget(token_epoch=time.time()), opener=opener)
                    started = time.monotonic()
                    with self.assertRaisesRegex(rt.NightlyError, "whole-operation deadline") as raised:
                        if method == "GET":
                            api.get("/repos/Hexalith/Hexalith.Builds/releases", "inert")
                        else:
                            api.dispatch(rt.BUILDS, "builds-release.yml", {}, "inert")
                    self.assertLess(time.monotonic() - started, 0.4)
                    self.assertEqual(opener.calls, 1)
                    if responses:
                        self.assertTrue(responses[0].closed)
                    if method == "POST":
                        self.assertIn("write result uncertain, not retried", str(raised.exception))

    def test_artifact_redirect_and_download_share_one_whole_operation_deadline(self):
        class ShortBudget(rt.Budget):
            def timeout(self, **kwargs):
                return min(0.02, super().timeout(**kwargs))
        payload = zip_document("outcome.json", {})
        info = metadata(8, "x", payload, 9, "a" * 40)
        requests = []
        class SlowResponse(io.BytesIO):
            status = 200
            def read(self, limit):
                for _ in range(100):
                    time.sleep(0.005)
                return super().read(limit)
        class SlowOpener:
            def open(self, request, timeout):
                requests.append(request)
                if len(requests) == 1:
                    raise HTTPError(request.full_url, 302, "fixture", {
                        "Location": "https://productionresultssa1.blob.core.windows.net/a?sig=secret"}, io.BytesIO())
                return SlowResponse(payload)
        api = rt.API(ShortBudget(token_epoch=time.time()), repositories=("Hexalith.Alpha",), opener=SlowOpener())
        started = time.monotonic()
        with self.assertRaisesRegex(rt.NightlyError, "whole-operation deadline"):
            api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert")
        self.assertLess(time.monotonic() - started, 0.4)
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].get_header("Authorization"), "Bearer inert")
        self.assertIsNone(requests[1].get_header("Authorization"))

    def test_whole_operation_restores_existing_alarm_handler_and_remaining_timer(self):
        previous_handler = signal.getsignal(signal.SIGALRM)
        previous_timer = signal.getitimer(signal.ITIMER_REAL)
        def existing_handler(_signum, _frame):
            raise AssertionError("existing alarm should not expire")
        try:
            signal.signal(signal.SIGALRM, existing_handler)
            signal.setitimer(signal.ITIMER_REAL, 5, 2)
            with rt.whole_operation(1):
                time.sleep(0.01)
            self.assertIs(signal.getsignal(signal.SIGALRM), existing_handler)
            remaining, interval = signal.getitimer(signal.ITIMER_REAL)
            self.assertGreater(remaining, 4)
            self.assertLess(remaining, 5)
            self.assertEqual(interval, 2)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)
            if previous_timer[0]:
                signal.setitimer(signal.ITIMER_REAL, *previous_timer)

    def test_exact_dispatch_details_and_inputs(self):
        repository, identity = "Hexalith.Alpha", 987
        reply = {"workflow_run_id": identity, "run_url": f"https://api.github.com/repos/Hexalith/{repository}/actions/runs/{identity}",
                 "html_url": rt.run_link(repository, identity)}
        api, opener, _ = self.api([reply])
        self.assertEqual(api.dispatch(repository, "release.yml", {"delivered-sha": "b" * 40}, "inert"),
                         {"runId": identity, "link": reply["html_url"]})
        self.assertEqual(json.loads(opener.requests[0][0].data), {"ref": "main", "inputs": {"delivered-sha": "b" * 40},
                                                               "return_run_details": True})
        for changed in ({}, reply | {"workflow_run_id": True}, reply | {"html_url": "https://evil.invalid"},
                        reply | {"run_url": "https://api.github.com/repos/Hexalith/Other/actions/runs/987"}):
            api, opener, _ = self.api([changed])
            with self.assertRaises(rt.NightlyError):
                api.dispatch(repository, "release.yml", {"delivered-sha": "b" * 40}, "inert")
            self.assertEqual(len(opener.requests), 1)
        for repository, workflow, inputs in ((rt.BUILDS, "release.yml", {}), (rt.BUILDS, "builds-release.yml", {"x": "y"}),
                                               ("Hexalith.Alpha", "release.yml", {})):
            api, opener, _ = self.api([])
            with self.assertRaises(rt.NightlyError):
                api.dispatch(repository, workflow, inputs, "inert")
            self.assertFalse(opener.requests)

    def test_run_identity_refuses_substitution(self):
        run = {"id": 9, "path": ".github/workflows/release.yml", "event": "workflow_dispatch", "head_branch": "main",
               "repository": {"full_name": "Hexalith/Hexalith.Alpha"}, "html_url": rt.run_link("Hexalith.Alpha", 9),
               "head_sha": "a" * 40, "run_attempt": 2, "status": "completed", "conclusion": "success"}
        self.assertEqual(rt.run_identity(run, "Hexalith.Alpha", ".github/workflows/release.yml", 9), run)
        for change in ({"id": 10}, {"path": ".github/workflows/ci.yml"}, {"event": "push"}, {"head_branch": "other"},
                       {"repository": {"full_name": "Hexalith/Other"}}, {"run_attempt": True}):
            with self.subTest(change=change), self.assertRaises(rt.NightlyError):
                rt.run_identity(run | change, "Hexalith.Alpha", ".github/workflows/release.yml", 9)

    def test_publication_is_single_narrow_patch(self):
        value = {"tag_name": "v1.0.0", "target_commitish": "a" * 40, "draft": False}
        api, opener, _ = self.api([{}])
        api.publish_draft("Hexalith.Alpha", 8, value, "inert")
        self.assertEqual(opener.requests[0][0].get_method(), "PATCH")
        self.assertEqual(json.loads(opener.requests[0][0].data), value)
        for changed in (value | {"body": "new"}, value | {"draft": True}, value | {"tag_name": "latest"}):
            api, opener, _ = self.api([])
            with self.assertRaises(rt.NightlyError):
                api.patch("/repos/Hexalith/Hexalith.Alpha/releases/8", changed, "inert")
            self.assertFalse(opener.requests)

    def test_pagination_and_call_limits(self):
        api, _, _ = self.api([{"total_count": 101, "artifacts": [{}] * 100}, {"total_count": 101, "artifacts": [{}]}])
        self.assertEqual(len(api.pages("/repos/Hexalith/Hexalith.Alpha/actions/runs/9/artifacts", "inert", field="artifacts")), 101)
        api, _, _ = self.api([{"total_count": 1, "artifacts": []}])
        with self.assertRaisesRegex(rt.NightlyError, "incomplete"):
            api.pages("/repos/Hexalith/Hexalith.Alpha/actions/runs/9/artifacts", "inert", field="artifacts")
        api, opener, _ = self.api([{}])
        api.calls = rt.MAX_CALLS
        with self.assertRaisesRegex(rt.NightlyError, "call limit"):
            api.get("/repos/Hexalith/Hexalith.Alpha/immutable-releases", "inert")
        self.assertFalse(opener.requests)

    def test_pagination_changes_are_typed_refusals_and_malformed_pages_remain_fatal(self):
        for replies in ([{"total_count": 1, "artifacts": []}],
                        [{"total_count": 101, "artifacts": [{}] * 100}, {"total_count": 102, "artifacts": [{}]}]):
            with self.subTest(replies=replies):
                api, _, _ = self.api(replies)
                with self.assertRaises(rt.InventoryChanged):
                    api.pages("/repos/Hexalith/Hexalith.Alpha/actions/runs/9/artifacts", "inert", field="artifacts")
        for replies in ([{"total_count": True, "artifacts": []}], [{"total_count": 0, "artifacts": {}}],
                        [{"total_count": 101, "artifacts": [{}] * 100}, {"total_count": 102, "artifacts": None}]):
            with self.subTest(replies=replies):
                api, _, _ = self.api(replies)
                with self.assertRaises(rt.NightlyError) as failure:
                    api.pages("/repos/Hexalith/Hexalith.Alpha/actions/runs/9/artifacts", "inert", field="artifacts")
                self.assertNotIsInstance(failure.exception, rt.InventoryChanged)

    def test_fixture_artifact_bytes_survive_wall_clock_timestamp_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Workspace(Path(temporary) / "workspace", ("Hexalith.Alpha",))
            workspace.ready("Hexalith.Alpha")
            clock = Clock()
            api = fixture_transport(rt, workspace.config)(
                rt.Budget(clock(), token_epoch=clock(), clock=clock)).api
            before = time.struct_time((2026, 11, 17, 1, 0, 0, 1, 321, 0))
            after = time.struct_time((2026, 11, 17, 1, 0, 2, 1, 321, 0))
            with mock.patch.object(nightly_support.zipfile.time, "localtime", return_value=before):
                info, = api.pages("/repos/Hexalith/Hexalith.Alpha/actions/runs/1001/artifacts",
                                  "inert-poll-token", field="artifacts")
            payloads = []
            original = api.opener.open
            def capture(*args, **kwargs):
                response = original(*args, **kwargs)
                payloads.append(response.getvalue())
                return response
            with mock.patch.object(nightly_support.zipfile.time, "localtime", return_value=after), \
                    mock.patch.object(api.opener, "open", side_effect=capture):
                value = api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert-poll-token")
            self.assertEqual(value, workspace.config["outcomes"]["Hexalith.Alpha"])
            self.assertEqual(info["digest"], "sha256:" + hashlib.sha256(payloads[0]).hexdigest())
            self.assertEqual(info["size_in_bytes"], len(payloads[0]))
            with zipfile.ZipFile(io.BytesIO(payloads[0])) as archive:
                member, = archive.infolist()
                self.assertEqual(member.filename, "outcome.json")
                self.assertEqual(member.compress_type, zipfile.ZIP_DEFLATED)
                self.assertEqual(member.external_attr, 0o600 << 16)
                self.assertFalse(member.is_dir())
            with self.assertRaisesRegex(rt.NightlyError, "digest mismatch"):
                api.artifact_member("Hexalith.Alpha", info | {"digest": "sha256:" + "0" * 64},
                                    "outcome.json", "inert-poll-token")

    def test_fixture_artifact_identity_survives_listing_download_clock_boundary(self):
        value = {"schema": "hexalith.release-outcome.v1", "sha": "a" * 40, "outcome": "ready",
                 "version": "1.0.0", "draftId": 880, "lastTag": ""}
        with mock.patch("nightly_support.zipfile.time.localtime", return_value=(2026, 11, 14, 2, 17, 0)):
            listed = zip_document("outcome.json", value)
        info = metadata(8, "hexalith-release-outcome", listed, 9, "a" * 40)
        # The fake HTTP endpoint reconstructs this same immutable artifact on
        # each request. ZIP timestamps must not alter its authenticated bytes.
        with mock.patch("nightly_support.zipfile.time.localtime", return_value=(2026, 11, 14, 2, 17, 2)):
            downloaded = zip_document("outcome.json", value)
        api, _, _ = self.api([downloaded])
        self.assertEqual(api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert"), value)

    def test_artifact_digest_exact_member_and_json(self):
        payload = zip_document("outcome.json", {"ok": True})
        info = metadata(8, "hexalith-release-outcome", payload, 9, "a" * 40)
        api, _, _ = self.api([payload])
        self.assertEqual(api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert"), {"ok": True})
        for changed in (info | {"digest": "sha256:" + "a" * 64}, info | {"size_in_bytes": len(payload) + 1},
                        info | {"expired": True}, info | {"expires_at": "2000-01-01T00:00:00Z"},
                        info | {"size_in_bytes": rt.MAX_ZIP + 1}):
            api, _, _ = self.api([payload])
            with self.assertRaises(rt.NightlyError):
                api.artifact_member("Hexalith.Alpha", changed, "outcome.json", "inert")
        for member, document in (("../outcome.json", {}), ("x/outcome.json", {}), ("outcome.json", b'{"a":1,"a":2}')):
            payload = zip_document(member, document)
            api, _, _ = self.api([payload])
            with self.assertRaises(rt.NightlyError):
                api.artifact_member("Hexalith.Alpha", metadata(8, "x", payload, 9, "a" * 40), "outcome.json", "inert")

    def test_zip_duplicate_symlink_and_expansion_bounds(self):
        for kind in ("symlink", "large", "two"):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                if kind == "symlink":
                    item = zipfile.ZipInfo("outcome.json")
                    item.create_system = 3
                    item.external_attr = (stat.S_IFLNK | 0o777) << 16
                    archive.writestr(item, "elsewhere")
                else:
                    archive.writestr("outcome.json", "x" * (rt.MAX_JSON + 1) if kind == "large" else "{}")
                    if kind == "two":
                        archive.writestr("other.json", "{}")
            payload = stream.getvalue()
            api, _, _ = self.api([payload])
            with self.subTest(kind=kind), self.assertRaises(rt.NightlyError):
                api.artifact_member("Hexalith.Alpha", metadata(8, "x", payload, 9, "a" * 40), "outcome.json", "inert")

    def test_artifact_redirect_never_forwards_authorization(self):
        payload = zip_document("outcome.json", {})
        info = metadata(8, "x", payload, 9, "a" * 40)
        api, opener, _ = self.api([(302, {}, {"Location": "https://productionresultssa1.blob.core.windows.net/a?sig=secret"}), payload])
        api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert")
        self.assertEqual(opener.requests[0][0].get_header("Authorization"), "Bearer inert")
        self.assertIsNone(opener.requests[1][0].get_header("Authorization"))
        for destination in ("http://productionresultssa1.blob.core.windows.net/a", "https://evil.invalid/a",
                            "https://productionresultssa1.blob.core.windows.net.evil.invalid/a",
                            "https://user@productionresultssa1.blob.core.windows.net/a", "https://productionresultssa1.blob.core.windows.net:444/a"):
            api, opener, _ = self.api([(302, {}, {"Location": destination})])
            with self.subTest(destination=destination), self.assertRaises(rt.NightlyError):
                api.artifact_member("Hexalith.Alpha", info, "outcome.json", "inert")
            self.assertEqual(len(opener.requests), 1)

    def test_closed_state_is_bound_to_registry_run_attempt_source_and_phase(self):
        original = state()
        self.assertEqual(rt.validate_state(original, original["registry"], identity=original["identity"], phase="dispatch"), original)
        changes = [("schema", "unknown"), ("registry", ["Other"]), ("phase", "wait"), ("extra", True)]
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(rt.NightlyError):
                rt.validate_state(original | {key: value}, original["registry"], identity=original["identity"], phase="dispatch")
        for identity in (original["identity"] | {"attempt": 2}, original["identity"] | {"runId": 102}, original["identity"] | {"source": "b" * 40}):
            with self.assertRaises(rt.NightlyError):
                rt.validate_state(original, original["registry"], identity=identity)
        for field, value in (("repository", "Other"), ("workflow", "ci.yml"), ("publication", "published"), ("verdict", "pass"),
                             ("runId", True), ("link", "https://evil.invalid")):
            changed = deepcopy(original)
            changed["targets"][0][field] = value
            with self.subTest(field=field), self.assertRaises(rt.NightlyError):
                rt.validate_state(changed, original["registry"])
        changed = deepcopy(original)
        changed.update(phase="wait", wait={"started": 1000, "deadline": 19000})
        rt.validate_state(changed, original["registry"])
        changed["wait"]["deadline"] += 1
        with self.assertRaises(rt.NightlyError):
            rt.validate_state(changed, original["registry"])

    def test_wait_handoff_requires_clock_and_complete_dispatched_identities(self):
        value = state()
        value.update(phase="wait", wait={"started": 1000, "deadline": 19000})
        row = value["targets"][0]
        row.update(eligibility="eligible", dispatch="dispatched", dispatchHead="b" * 40,
                   runId=9, runAttempt=1, link=rt.run_link("Hexalith.Alpha", 9), status="completed",
                   conclusion="success", outcome={"schema": "hexalith.release-outcome.v1",
                   "sha": "b" * 40, "outcome": "nothing"})
        rt.validate_state(value, value["registry"])
        for field, replacement in (("wait", None), ("dispatchHead", ""), ("runAttempt", 0)):
            changed = deepcopy(value)
            if field == "wait": changed[field] = replacement
            else: changed["targets"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(rt.NightlyError):
                rt.validate_state(changed, changed["registry"])
        seed = state()
        seed.update(phase="wait", errors=["checkout or initialization did not complete"])
        rt.validate_state(seed, seed["registry"])
        seed.update(phase="nightly", result="fail")
        rt.validate_state(seed, seed["registry"])
        created = state()
        created["targets"][0].update(dispatch="failed", runId=9,
            link=rt.run_link("Hexalith.Alpha", 9), reason="first status read failed")
        rt.validate_state(created, created["registry"])

    def test_cached_helpers_reuse_authenticated_objects_without_rest_or_fetch(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Workspace(Path(temporary) / "work")
            base = rt.delivery.environment
            def environment():
                result = base()
                i = int(result["GIT_CONFIG_COUNT"])
                result.update(GIT_CONFIG_COUNT=str(i + 1))
                result[f"GIT_CONFIG_KEY_{i}"] = "protocol.file.allow"
                result[f"GIT_CONFIG_VALUE_{i}"] = "always"
                return result
            destination = Path(temporary) / "trusted"
            with mock.patch.object(rt.delivery, "environment", environment):
                transport = fixture_transport(rt, work.config)(rt.Budget(token_epoch=time.time()))
                acquired = transport.helpers(TAG, destination, token="inert-builds-read-token")
                calls = transport.api.calls
                # Mutable exported bytes are replaced by committed objects.
                (acquired.root / "Github/lib/release_outcome.py").write_text("raise RuntimeError('mutable export')\n")
                original_run = rt.Git.run
                def local_only(instance, *args, **kwargs):
                    if args[0] in {"fetch", "ls-remote"}:
                        raise AssertionError("cached helper tried remote Git acquisition")
                    return original_run(instance, *args, **kwargs)
                with mock.patch.object(transport.api, "get", side_effect=AssertionError("cached helper tried REST acquisition")), \
                        mock.patch.object(rt.Git, "run", local_only):
                    for _ in range(18):
                        cached = transport.cached_helpers(TAG, RELEASE, destination)
                        self.assertEqual(cached.source, RELEASE)
                    self.assertEqual(transport.api.calls, calls)
                    with self.assertRaisesRegex(rt.NightlyError, "tag/source identity"):
                        transport.cached_helpers(TAG, "a" * 40, destination)

    def test_trusted_acquisition_uses_real_release_objects_and_rejects_unacceptable_tag(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Workspace(Path(temporary) / "work")
            base = rt.delivery.environment
            def environment():
                result = base()
                i = int(result["GIT_CONFIG_COUNT"])
                result.update(GIT_CONFIG_COUNT=str(i + 1))
                result[f"GIT_CONFIG_KEY_{i}"] = "protocol.file.allow"
                result[f"GIT_CONFIG_VALUE_{i}"] = "always"
                return result
            with mock.patch.object(rt.delivery, "environment", environment):
                transport = fixture_transport(rt, work.config)(rt.Budget(token_epoch=time.time()))
                original_run = rt.Git.run

                def credential_free(instance, *args, **kwargs):
                    self.assertFalse(kwargs.get("token"))
                    return original_run(instance, *args, **kwargs)

                with mock.patch.object(rt.Git, "run", credential_free):
                    helpers = transport.helpers(TAG, Path(temporary) / "trusted", token="inert-builds-read-token")
                requests = [json.loads(line) for line in Path(work.config["requests"]).read_text().splitlines()]
                self.assertEqual(len(requests), 4)
                for request in requests:
                    self.assertEqual(request["method"], "GET")
                    self.assertTrue(request["path"].startswith("/repos/Hexalith/Hexalith.Builds/"))
                    self.assertEqual(request["authorization"], "Bearer inert-builds-read-token")
                self.assertFalse(hasattr(transport, "builds_token"))
                self.assertEqual(helpers.source, RELEASE)
                self.assertTrue(str(helpers.outcome.__file__).startswith(str(Path(temporary) / "trusted")))
                self.assertEqual(helpers.outcome.validate_outcome({"schema": "hexalith.release-outcome.v1", "sha": "a" * 40,
                                                                  "outcome": "disabled"})["outcome"], "disabled")
                work.config["bad_release"] = True
                with self.assertRaisesRegex(rt.NightlyError, "immutable"):
                    transport.helpers(TAG, Path(temporary) / "refused", token="inert-builds-read-token")
                self.assertFalse((Path(temporary) / "refused/source").exists())
                # Missing release capabilities fail before any imported top-level code.
                root = Path(temporary) / "incomplete"
                shutil.copytree(helpers.root, root)
                marker = Path(temporary) / "executed"
                (root / "Github/lib/release_outcome.py").write_text(f"open({str(marker)!r}, 'w').write('bad')\n")
                with self.assertRaisesRegex(rt.NightlyError, "capability"):
                    rt.load_helpers(root)
                self.assertFalse(marker.exists())

    def test_trusted_acquisition_never_falls_back_to_anonymous_reads(self):
        api, opener, _ = self.api([(403, {})])
        transport = rt.Transport(api.budget, api)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "builds"
            with self.assertRaisesRegex(rt.NightlyError, "job token unavailable"):
                transport.helpers(TAG, destination, token="")
            self.assertEqual([], opener.requests)
            with self.assertRaisesRegex(rt.NightlyError, "HTTP 403"):
                transport.helpers(TAG, destination, token="inert-builds-read-token")
            self.assertFalse(destination.exists())
        self.assertEqual(1, len(opener.requests))
        self.assertEqual(opener.requests[0][0].get_header("Authorization"), "Bearer inert-builds-read-token")
        self.assertFalse(hasattr(transport, "builds_token"))


if __name__ == "__main__":
    unittest.main()
