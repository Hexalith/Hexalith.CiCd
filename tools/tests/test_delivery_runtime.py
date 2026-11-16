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
from unittest import mock
from urllib.error import HTTPError

from delivery_support import ROOT, Workspace, TAG, RELEASE, filtered_remote, fixture_transport, load, git

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


class GitExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="delivery-export-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        git(self.source, "init", "--quiet", "--initial-branch=main")
        filtered_remote(self.source)

    def write(self, path, data):
        target = self.source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def acquire(self, *, partial=False):
        git(self.source, "add", "--all")
        git(self.source, "commit", "--quiet", "-m", "fixture")
        revision = git(self.source, "rev-parse", "HEAD")
        store = rt.Git(self.root / "objects")
        index = int(store.env["GIT_CONFIG_COUNT"])
        store.env.update(GIT_CONFIG_COUNT=str(index + 1))
        store.env[f"GIT_CONFIG_KEY_{index}"] = "protocol.file.allow"
        store.env[f"GIT_CONFIG_VALUE_{index}"] = "always"
        store.init()
        store.run("config", "remote.origin.url", self.source.as_uri())
        if partial:
            store.run("config", "remote.origin.promisor", "true")
            store.run("config", "remote.origin.partialclonefilter", "blob:none")
        store.run("fetch", "--quiet", "--no-tags", "--no-recurse-submodules",
                  *(["--filter=blob:none"] if partial else []), "origin", "+refs/heads/main:refs/heads/main")
        return store, revision

    def test_partial_export_bulk_fetches_selected_exact_bytes_without_checkout(self):
        expected = {f"selected/file-{i:03d}": bytes([i]) + b"\0\n\xff" for i in range(140)}
        expected["selected/empty"] = b""
        expected["selected/line\nbreak"] = b"binary\0body\n"
        for path, data in expected.items():
            self.write(path, data)
        (self.source / "selected/file-000").chmod(0o755)
        self.write("unselected", b"outside selected prefix")
        store, revision = self.acquire(partial=True)
        before = git(store.root, "rev-list", "--objects", "--all", "--missing=print")
        self.assertEqual(sum(row.startswith("?") for row in before.splitlines()), len(expected) + 1)
        destination = self.root / "exported"
        with mock.patch.object(store, "run", wraps=store.run) as run:
            store.export(revision, "selected", destination)
        self.assertEqual({str(path.relative_to(destination)): path.read_bytes()
                          for path in destination.rglob("*") if path.is_file()}, expected)
        calls = [call.args for call in run.call_args_list]
        self.assertEqual(sum(args[0] == "ls-tree" for args in calls), 1)
        fetches = [call for call in run.call_args_list if "fetch" in call.args]
        self.assertEqual(len(fetches), 2)
        self.assertTrue(all(len(call.kwargs["data"].splitlines()) <= 128 for call in fetches))
        self.assertLess(len(calls), 30)
        self.assertFalse((store.root / "index").exists())
        missing = git(store.root, "rev-list", "--objects", "--all", "--missing=print")
        self.assertEqual(sum(row.startswith("?") for row in missing.splitlines()), 1)

    def test_batch_bodies_stay_within_command_bound_at_blob_size_limit(self):
        for index in range(9):
            self.write(f"selected/{index}", bytes([index]) * rt.MAX_JSON)
        store, revision = self.acquire()
        with mock.patch.object(store, "run", wraps=store.run) as run:
            store.export(revision, "selected", self.root / "exported")
        bodies = [call for call in run.call_args_list if call.args == ("cat-file", "--batch")]
        self.assertEqual(len(bodies), 2)
        self.assertTrue(all(len(call.kwargs["data"].splitlines()) <= 7 for call in bodies))
        for index in range(9):
            self.assertEqual((self.root / f"exported/selected/{index}").read_bytes(), bytes([index]) * rt.MAX_JSON)

    def assert_capacity_failure(self, count, size, diagnostic):
        for index in range(count):
            self.write(f"selected/{index}", b"x" * size)
        store, revision = self.acquire(partial=True)
        with mock.patch.object(store, "run", wraps=store.run) as run:
            with self.assertRaisesRegex(rt.DeliveryError, diagnostic):
                store.export(revision, "selected", self.root / "exported")
        self.assertFalse((self.root / "exported").exists())
        self.assertFalse(any(call.args == ("cat-file", "--batch") for call in run.call_args_list))

    def test_oversized_blob_fails_before_body_materialization(self):
        self.assert_capacity_failure(1, rt.MAX_JSON + 1, "2 MiB")

    def test_oversized_aggregate_fails_before_body_materialization(self):
        self.assert_capacity_failure(33, rt.MAX_JSON, "export limit")

    def test_nonregular_and_unsafe_entries_fail_before_fetch(self):
        self.write("selected/regular", b"safe")
        store, revision = self.acquire()
        oid = store.items(revision)["selected/regular"][2]
        for path, mode, kind in (("selected/link", "120000", "blob"), ("selected/submodule", "160000", "commit"),
                                 ("/absolute", "100644", "blob"), ("selected/../escape", "100644", "blob"),
                                 ("selected/./alias", "100644", "blob"), ("selected/.git/config", "100644", "blob")):
            with self.subTest(path=path), mock.patch.object(store, "items", return_value={path: (mode, kind, oid)}):
                with mock.patch.object(store, "run", wraps=store.run) as run:
                    with self.assertRaisesRegex(rt.DeliveryError, "regular blob"):
                        store.export(revision, "selected", self.root / "exported")
                    run.assert_not_called()

    def test_missing_malformed_and_truncated_batch_objects_fail_closed(self):
        self.write("selected/file", b"exact\0bytes")
        store, revision = self.acquire()
        oid = store.items(revision)["selected/file"][2]
        original = store.run
        header = f"{oid} blob 11\n".encode()
        cases = (("--batch-check", (oid + " missing\n").encode()),
                 ("--batch-check", ("f" * 40 + " blob 11\n").encode()),
                 ("--batch-check", (oid + " tree 11\n").encode()),
                 ("--batch-check", (oid + " blob -1\n").encode()),
                 ("--batch-check", b""),
                 ("--batch", b"wrong header\n"),
                 ("--batch", header + b"short\n"),
                 ("--batch", header + b"exact\0bytes\ntrailing"))
        for operation, output in cases:
            with self.subTest(operation=operation, output=output):
                def malformed(*args, **kwargs):
                    return output if args == ("cat-file", operation) else original(*args, **kwargs)
                with mock.patch.object(store, "run", side_effect=malformed):
                    with self.assertRaises(rt.DeliveryError):
                        store.export(revision, "selected", self.root / "exported")

    def test_export_preserves_deadline_cancellation_and_git_output_bound(self):
        self.write("selected/file", b"body")
        store, revision = self.acquire()
        store.budget = rt.Budget(0, clock=lambda: 2161)
        with self.assertRaisesRegex(rt.DeliveryError, "deadline"):
            store.export(revision, "selected", self.root / "exported")
        store.budget = rt.Budget()
        def overrun(*args, **kwargs):
            kwargs["stdout"].write(b"x" * (rt.MAX_GIT + 1))
            return mock.Mock(returncode=0)
        with mock.patch.object(rt.subprocess, "run", side_effect=overrun):
            with self.assertRaisesRegex(rt.DeliveryError, "16 MiB"):
                store.run("cat-file", "--batch")


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
        with self.assertRaisesRegex(rt.DeliveryError, "null response"):
            rt.API(opener=Opener(b"null")).get(
                "/repos/Hexalith/Fixture/automated-security-fixes", "inert", absent=True)
        with self.assertRaises(rt.DeliveryError):
            rt.NoRedirect().redirect_request(None, None, None, None, None, None)
        with self.assertRaises(rt.DeliveryError):
            rt.API(opener=Opener({})).get("https://evil.invalid")
        for path in ("/repos/Hexalith/x/../y", "/repos/Hexalith/x/./y"):
            with self.assertRaises(rt.DeliveryError):
                rt.API(opener=Opener({})).get(path)
        opener = Opener({"ok": True})
        self.assertEqual(rt.API(opener=opener).get("/repos/Hexalith/Fixture/test", "inert"), {"ok": True})
        self.assertEqual(opener.requests[0][0].full_url, "https://api.github.com/repos/Hexalith/Fixture/test")
        self.assertEqual(opener.requests[0][0].get_header("Authorization"), "Bearer inert")
        self.assertLessEqual(opener.requests[0][1], 30)
        self.assertEqual(rt.API(opener=Opener({})).get("/repos/Hexalith/Hexalith.Builds/compare/" +
                         "a" * 40 + "..." + "b" * 40 + "?per_page=1&page=2"), {})

    def test_git_authentication_header_and_fixed_production_remote(self):
        import base64
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(rt.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
                rt.Git(directory).run("push", "https://github.com/Hexalith/Fixture.git", token="inert")
            env = run.call_args.kwargs["env"]
            config = {env[f"GIT_CONFIG_KEY_{i}"]: env[f"GIT_CONFIG_VALUE_{i}"]
                      for i in range(int(env["GIT_CONFIG_COUNT"]))}
            headers = {key: value for key, value in config.items() if key.lower().endswith(".extraheader")}
            self.assertEqual(headers, {"http.extraHeader": "", "http.https://github.com/.extraheader":
                "AUTHORIZATION: basic " + base64.b64encode(b"x-access-token:inert").decode()})
            self.assertNotIn("inert", " ".join(run.call_args.args[0]))
        self.assertEqual(rt.Transport().remote("Hexalith.Fixture"), "https://github.com/Hexalith/Hexalith.Fixture.git")

    def test_pagination_bounds_and_types(self):
        with self.assertRaises(rt.DeliveryError):
            rt.API(opener=Opener([{}] * 100)).pages("/repos/Hexalith/Fixture/rulesets")
        with self.assertRaises(rt.DeliveryError):
            rt.API(opener=Opener({"total_count": True, "repositories": []})).pages("/installation/repositories", field="repositories")

    def test_successful_paging_finds_required_repository_after_page_one(self):
        with tempfile.TemporaryDirectory() as directory:
            w = Workspace(Path(directory) / "workspace")
            w.config["api"]["/installation/repositories"] = [
                {"full_name": f"Hexalith/Other{index}"} for index in range(100)] + [{"full_name": "Hexalith/Hexalith.Alpha"}]
            transport = fixture_transport(rt, w.config)()
            repositories = transport.api.pages("/installation/repositories", "inert-token-Hexalith.Alpha", field="repositories")
            self.assertEqual(len(repositories), 101)
            self.assertEqual(repositories[-1]["full_name"], "Hexalith/Hexalith.Alpha")
            controller.app_checks(transport, "Hexalith.Alpha", "inert-token-Hexalith.Alpha")
            requests = [json.loads(line) for line in Path(w.config["requests"]).read_text().splitlines()]
            self.assertTrue(any(r["path"] == "/installation/repositories?per_page=100&page=2" for r in requests))

    def test_fixture_http_rejects_missing_and_wrong_repository_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            w = Workspace(Path(directory) / "workspace", ("Hexalith.Alpha", "Hexalith.Beta"))
            api = fixture_transport(rt, w.config)().api
            for path, token in (("/repos/Hexalith/Hexalith.Alpha", None),
                                ("/repos/Hexalith/Hexalith.Alpha", "inert-token-Hexalith.Beta"),
                                ("/repos/Hexalith/Hexalith.Alpha", "inert-cicd-token"),
                                ("/repos/Hexalith/Hexalith.CiCd/actions/workflows", "inert-token-Hexalith.Alpha"),
                                ("/installation/repositories", None)):
                with self.subTest(path=path, token=token), self.assertRaisesRegex(rt.DeliveryError, "HTTP 403"):
                    api.get(path, token)
            self.assertEqual(api.get("/repos/Hexalith/Hexalith.Alpha", "inert-token-Hexalith.Alpha")["default_branch"], "main")
            self.assertEqual(api.get("/repos/Hexalith/Hexalith.Builds/releases/tags/" + TAG)["tag_name"], TAG)

    def test_malformed_workflow_inventory_is_not_absence(self):
        with tempfile.TemporaryDirectory() as directory:
            w = Workspace(Path(directory) / "workspace", ())
            transport = fixture_transport(rt, w.config)()
            for item in ({}, None, {"path": 1, "id": 1}, {"path": "", "id": 1},
                         {"path": "other.yml", "id": "1"}, {"path": "other.yml", "id": True},
                         {"path": "other.yml", "id": 0}):
                with self.subTest(item=item):
                    w.config["api"]["/repos/Hexalith/Hexalith.CiCd/actions/workflows"] = [item]
                    with self.assertRaisesRegex(controller.rt.DeliveryError, "malformed nightly workflow inventory"):
                        controller.nightly(transport, "inert-cicd-token")

    def test_ancestry_rejections_name_returned_identities_before_acquisition(self):
        with tempfile.TemporaryDirectory() as directory:
            w = Workspace(Path(directory) / "workspace", ())
            transport = fixture_transport(rt, w.config)()
            main = "e" * 40
            w.config["api"]["/repos/Hexalith/Hexalith.Builds/git/ref/heads/main"] = {
                "ref": "refs/heads/main", "object": {"type": "commit", "sha": main}}
            path = f"/repos/Hexalith/Hexalith.Builds/compare/{RELEASE}...{main}?per_page=1&page=2"
            valid = {"status": "ahead", "base_commit": {"sha": RELEASE}, "merge_base_commit": {"sha": RELEASE}}
            cases = [valid | {"status": "diverged", "merge_base_commit": {"sha": "a" * 40}},
                     valid | {"base_commit": {"sha": "b" * 40}},
                     valid | {"merge_base_commit": {"sha": "c" * 40}},
                     valid | {"base_commit": {"sha": "bad\nbase"}, "merge_base_commit": {"sha": "c" * 40}},
                     valid | {"base_commit": None}, valid | {"merge_base_commit": "malformed"},
                     None, [], "malformed", {}]
            for index, comparison in enumerate(cases):
                with self.subTest(comparison=comparison):
                    w.config["api"][path] = {"status": 200, "body": comparison}
                    destination = w.root / f"rejected-{index}"
                    with mock.patch.object(rt, "Git") as acquisition:
                        with self.assertRaises(rt.DeliveryError) as rejected:
                            transport.builds(TAG, destination)
                        acquisition.assert_not_called()
                    reason = str(rejected.exception)
                    self.assertIn(TAG, reason)
                    self.assertIn(f"release {RELEASE}", reason)
                    self.assertIn(f"live main {main}", reason)
                    for key in ("base_commit", "merge_base_commit"):
                        value = comparison.get(key) if isinstance(comparison, dict) else None
                        value = value.get("sha") if isinstance(value, dict) else value
                        self.assertIn(f"{key} {rt.clean(value)}", reason)
                    self.assertNotIn("\n", reason)
                    self.assertFalse(destination.exists())

    def test_real_annotated_release_acquisition_and_tag_object_identity_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            w = Workspace(Path(directory) / "workspace", ())
            git(w.builds, "tag", "-f", "-a", TAG, RELEASE, "-m", "Released annotation")
            annotated = git(w.builds, "rev-parse", "refs/tags/" + TAG)
            prefix = "/repos/Hexalith/Hexalith.Builds/"
            w.config["api"][prefix + "git/ref/tags/" + TAG] = {
                "ref": "refs/tags/" + TAG, "object": {"type": "tag", "sha": annotated}}
            tag_path = prefix + "git/tags/" + annotated
            w.config["api"][tag_path] = {"sha": annotated, "object": {"type": "commit", "sha": RELEASE}}
            transport = fixture_transport(rt, w.config)()
            original_environment = rt.environment
            def file_environment():
                env = original_environment()
                index = int(env["GIT_CONFIG_COUNT"])
                env.update(GIT_CONFIG_COUNT=str(index + 1))
                env[f"GIT_CONFIG_KEY_{index}"] = "protocol.file.allow"
                env[f"GIT_CONFIG_VALUE_{index}"] = "always"
                return env
            with mock.patch.object(rt, "environment", side_effect=file_environment):
                acquired, exported = transport.builds(TAG, w.root / "accepted")
            self.assertEqual(acquired.resolve("refs/tags/" + TAG), annotated)
            self.assertEqual(acquired.resolve("refs/tags/" + TAG + "^{commit}"), RELEASE)
            self.assertEqual((exported / "Github/lib/perimeter.py").read_bytes(),
                             subprocess.run(["git", "-C", str(w.builds), "show", RELEASE + ":Github/lib/perimeter.py"],
                                            capture_output=True, check=True).stdout)
            w.config["api"][tag_path] = {"sha": "d" * 40, "object": {"type": "commit", "sha": RELEASE}}
            with mock.patch.object(rt, "Git") as acquisition:
                with self.assertRaises(rt.DeliveryError) as rejected:
                    transport.builds(TAG, w.root / "rejected")
                acquisition.assert_not_called()
            for identity in (TAG, annotated, "d" * 40):
                self.assertIn(identity, str(rejected.exception))
            self.assertFalse((w.root / "rejected").exists())

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

    def test_nightly_absence_and_age_boundary(self):
        now = datetime(2026, 11, 14, tzinfo=timezone.utc)
        class API:
            present = True
            age = 26 * 3600
            empty = False
            def pages(self, path, token, field=None):
                if not path.endswith("workflows"):
                    raise AssertionError("repository-wide run fallback is forbidden")
                if path.endswith("workflows"):
                    return [{"path": ".github/workflows/nightly.yml", "id": 1}] if self.present else []
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
        self.assertEqual(controller.nightly(transport, "inert", now=now)["status"], "not-activated")
        transport.api.present = True
        transport.api.empty = True
        self.assertEqual(controller.nightly(transport, "inert", now=now)["status"], "not-activated")


if __name__ == "__main__":
    unittest.main()
