#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Bounded HTTP, clock, credentials and nonexecuting Git qualification."""
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError

from delivery_support import ROOT, Workspace, load, git

rt = load(ROOT / "tools/delivery_runtime.py", "_runtime_test")
controller = load(ROOT / "tools/deliver.py", "_runtime_controller_test")


class Response(io.BytesIO):
    status = 200


class Opener:
    def __init__(self, data=None, status=200):
        self.data, self.status = data, status
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if self.status != 200:
            raise HTTPError(request.full_url, self.status, "fixture", {}, io.BytesIO(b"private body"))
        return Response(self.data if isinstance(self.data, bytes) else json.dumps(self.data).encode())


class RuntimeTests(unittest.TestCase):
    def test_strict_json_limits_and_duplicates(self):
        for data in (b'{"a":1,"a":2}', b'{"a":NaN}', b'\xff', b" " * (rt.MAX_JSON + 1)):
            with self.assertRaises(rt.DeliveryError):
                rt.json_read(data)

    def test_http_caps_redirects_errors_and_canonical_url(self):
        for status in (301, 302, 403, 404, 500):
            with self.assertRaises(rt.DeliveryError):
                rt.API(opener=Opener({}, status)).get("/repos/Hexalith/Fixture/test", "inert")
        self.assertIsNone(rt.API(opener=Opener({}, 404)).get("/repos/Hexalith/Fixture/automated-security-fixes", "inert", absent=True))
        for body in (b"x" * (rt.MAX_JSON + 1), b'{"x":1,"x":2}'):
            with self.assertRaises(rt.DeliveryError):
                rt.API(opener=Opener(body)).get("/repos/Hexalith/Fixture/test")
        with self.assertRaises(rt.DeliveryError):
            rt.NoRedirect().redirect_request(None, None, None, None, None, None)
        with self.assertRaises(rt.DeliveryError):
            rt.API(opener=Opener({})).get("https://evil.invalid")
        opener = Opener({"ok": True})
        self.assertEqual(rt.API(opener=opener).get("/repos/Hexalith/Fixture/test"), {"ok": True})
        self.assertEqual(opener.requests[0][0].full_url, "https://api.github.com/repos/Hexalith/Fixture/test")
        self.assertLessEqual(opener.requests[0][1], 30)

    def test_pagination_bounds_and_types(self):
        with self.assertRaises(rt.DeliveryError):
            rt.API(opener=Opener([{}] * 100)).pages("/repos/Hexalith/Fixture/rulesets")
        with self.assertRaises(rt.DeliveryError):
            rt.API(opener=Opener({"total_count": True, "repositories": []})).pages("/installation/repositories", field="repositories")

    def test_conservative_token_age_and_soft_deadline(self):
        for age, token in ((3001, True), (2161, False), (-1, True)):
            with self.assertRaises(rt.DeliveryError):
                rt.Budget(100, clock=lambda: 100 + age).check(token=token)
        rt.Budget(100, clock=lambda: 3100).check(token=True)

    def test_poisoned_git_python_environment_cannot_execute_hooks_or_filters(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "EXECUTED"
            config = root / "evil.gitconfig"
            config.write_text(f'[core]\n hooksPath = {root}\n[filter "poison"]\n clean = touch {marker}\n required = true\n')
            (root / "sitecustomize.py").write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
            hook = root / "post-checkout"
            hook.write_text(f'#!/bin/sh\ntouch {marker}\n')
            hook.chmod(0o755)
            w = Workspace(root / "workspace")
            self.assertEqual(w.deliver(GIT_CONFIG_GLOBAL=str(config), PYTHONPATH=str(root), GIT_CONFIG_COUNT="1",
                GIT_CONFIG_KEY_0="filter.poison.clean", GIT_CONFIG_VALUE_0=f"touch {marker}",
                GIT_DIR=str(root / "evil"), GIT_WORK_TREE=str(root)), 0, w.report())
            self.assertFalse(marker.exists())
            self.assertNotIn("inert-", (w.directory / "report/delivery.json").read_text())

    def test_nightly_absence_boundary_and_deleted_workflow_history(self):
        now = datetime(2026, 11, 14, tzinfo=timezone.utc)
        class API:
            present = True
            age = 26 * 3600
            empty = False
            def pages(self, path, token, field=None):
                if path.endswith("workflows"):
                    return [{"path": ".github/workflows/nightly.yml", "id": 1}] if self.present else []
                return [] if self.empty else [self.run()]
            def run(self):
                return {"path": ".github/workflows/nightly.yml", "id": 2, "head_branch": "main", "conclusion": "failure",
                        "created_at": (now - timedelta(seconds=self.age)).isoformat()}
            def get(self, path, token):
                return {"total_count": 0 if self.empty else 1, "workflow_runs": [] if self.empty else [self.run()]}
        transport = type("Transport", (), {"api": API()})()
        self.assertEqual(controller.nightly(transport, "inert", now=now)["status"], "fresh")
        transport.api.age += 1
        self.assertEqual(controller.nightly(transport, "inert", now=now)["status"], "stale")
        transport.api.present = False
        self.assertEqual(controller.nightly(transport, "inert", now=now)["status"], "stale")
        transport.api.empty = True
        self.assertEqual(controller.nightly(transport, "inert", now=now)["status"], "not-activated")


if __name__ == "__main__":
    unittest.main()
