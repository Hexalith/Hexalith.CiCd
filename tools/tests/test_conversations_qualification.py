#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Refusal and canonical-mask controls for the explicit local qualification path."""

from __future__ import annotations

import importlib.util
import hashlib
import io
import json
import os
import shutil
from pathlib import Path
import sys
import tempfile
import subprocess
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "references/Hexalith.Builds/Github/lib"))
import perimeter

SPEC = importlib.util.spec_from_file_location("qualify_conversations", ROOT / "tools/qualify_conversations.py")
QUALIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUALIFY)


def snapshot(values):
    return SimpleNamespace(items={path: SimpleNamespace(mode=mode, oid=QUALIFY.digest(data)) for path, (mode, data) in values.items()},
                           read=lambda path: values[path][1])


class QualificationTests(unittest.TestCase):
    def setUp(self):
        # Global owner checks legitimately carry a read token. These controls
        # exercise product isolation with inert credentials in their own scope.
        environment = {key: value for key, value in os.environ.items() if key not in QUALIFY.CREDENTIAL_KEYS}
        patch = mock.patch.dict(os.environ, environment, clear=True)
        patch.start()
        self.addCleanup(patch.stop)

    def test_canonical_owned_mask_preserves_partial_npm_and_instruction_files(self):
        document = {"entries": [{"kind": "whole-dir", "path": ".github/workflows"},
            {"kind": "gitlink", "path": "references/Hexalith.Builds"},
            {"kind": "marker-block", "path": "AGENTS.md"},
            {"kind": "absent-json", "path": "package.json"},
            {"kind": "absent-glob", "pattern": "commitlint.config.*"}]}
        values = {".github/workflows/ci.yml": ("100644", b"workflow"), "AGENTS.md": ("100644", b"foreign and owned"),
                  "references/Hexalith.Builds": ("160000", b"actual recorded pin"),
                  "package.json": ("100644", b"legacy selectors"), "commitlint.config.mjs": ("100644", b"legacy config"),
                  "src/Product.cs": ("100644", b"product")}
        baseline = QUALIFY.owned_inventory(snapshot(values), document, perimeter)
        for path in ("AGENTS.md", "package.json", ".github/workflows/ci.yml", "references/Hexalith.Builds"):
            changed = dict(values)
            del changed[path]
            self.assertNotEqual(baseline, QUALIFY.owned_inventory(snapshot(changed), document, perimeter))
        changed = dict(values, **{"src/Product.cs": ("100644", b"new product")})
        self.assertEqual(baseline, QUALIFY.owned_inventory(snapshot(changed), document, perimeter))

    def test_product_diff_cannot_authorize_workflows_or_npm_selector_retirement(self):
        before = snapshot({"src/Product.cs": ("100644", b"old")})
        for path in (".github/workflows/ci.yml", "package.json", "package-lock.json", ".gitmodules"):
            after = snapshot({"src/Product.cs": ("100644", b"old"), path: ("100644", b"new")})
            with self.subTest(path=path), self.assertRaises(QUALIFY.delivery.DeliveryError):
                QUALIFY.product_difference(before, after)
        after = snapshot({"src/Product.cs": ("100644", b"new"), ".github/actions/after-unit-tests/action.yml": ("100644", b"product action")})
        self.assertEqual(2, len(QUALIFY.product_difference(before, after)))

    def test_stale_candidate_records_failure_before_any_remote_sdk_or_source_command(self):
        with tempfile.TemporaryDirectory(prefix="qualification-controls-") as temporary:
            directory = Path(temporary)
            scratch = directory / "scratch"
            scratch.mkdir()
            output = directory / "receipt.json"
            with mock.patch.dict(os.environ, TMPDIR=str(scratch)), mock.patch.object(QUALIFY, "git", return_value=b"2" * 40), \
                    mock.patch.object(QUALIFY, "live_baseline") as remote, mock.patch.object(QUALIFY.subprocess, "run") as command:
                with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "exact committed CiCd"):
                    QUALIFY.qualify(directory / "project", candidate="1" * 40, product_head="3" * 40, baseline="4" * 40, output=output)
            remote.assert_not_called()
            command.assert_not_called()
            receipt = json.loads(output.read_text())
            self.assertEqual("failed", receipt["result"])
            self.assertIn("exact committed CiCd", receipt["reason"])

    def test_fixture_protocol_requires_the_actual_candidate_reader(self):
        with tempfile.TemporaryDirectory(prefix="qualification-protocol-") as temporary:
            root = Path(temporary)
            helper = root / "owner/tools/qualification/conversations_fixture_results.py"
            helper.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / "tools/qualification/conversations_fixture_results.py", helper)
            module = root / "candidate"
            fixture = module / "tests/compatibility/MinimalModule"
            fixture.mkdir(parents=True)
            with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "fixture result protocol failed"):
                QUALIFY.qualify_fixture_results(root / "owner", module)
            (fixture / "run_compatibility.py").write_text(
                "def expected_tests():\n    return {str(index) for index in range(7)}\n"
                "def verify_records(records):\n    pass\n")
            with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "fixture result protocol failed"):
                QUALIFY.qualify_fixture_results(root / "owner", module)

    def test_receipts_cannot_replace_product_or_existing_files(self):
        with tempfile.TemporaryDirectory(prefix="qualification-controls-") as temporary:
            root = Path(temporary)
            scratch = root / "scratch"
            scratch.mkdir()
            existing = root / "existing.json"
            existing.write_text("preserve")
            for target in (existing, scratch / "receipt.json", root / "references/Hexalith.Conversations/.github/hexalith-ci.json"):
                with self.subTest(target=target), mock.patch.dict(os.environ, TMPDIR=str(scratch)), \
                        self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "fresh non-product"):
                    QUALIFY.qualify(root, candidate="1" * 40, product_head="2" * 40, baseline="3" * 40, output=target)
            self.assertEqual("preserve", existing.read_text())

    def test_stdin_token_is_bounded_exact_and_never_echoed_on_refusal(self):
        token = "inert-owner-read-token-for-qualification-controls"
        stream = io.BytesIO(json.dumps({"ownerReadToken": token}).encode())
        self.assertEqual(token, QUALIFY.read_owner_token(stream))
        self.assertEqual(b"", stream.read())
        self.assertNotIn(token, QUALIFY.delivery.clean("failed with " + token))
        for payload in (b"", b"not JSON", b"[]", b'{}', b'{"ownerReadToken":null}',
                b'{"ownerReadToken":""}', b'{"ownerReadToken":"secret\\nvalue"}',
                b'{"ownerReadToken":"secret","extra":true}',
                b'{"ownerReadToken":"secret","ownerReadToken":"other"}', b"x" * 8193):
            with self.subTest(payload=payload[:50]), self.assertRaisesRegex(QUALIFY.delivery.DeliveryError,
                    "invalid owner read-token stdin envelope"):
                QUALIFY.read_owner_token(io.BytesIO(payload))

    def test_inherited_aliases_are_scrubbed_and_refused_before_any_child(self):
        tokens = {key: "inert-inherited-" + key for key in QUALIFY.CREDENTIAL_KEYS}
        with mock.patch.dict(os.environ, tokens), mock.patch.object(QUALIFY.subprocess, "run") as child:
            with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "token-free ancestors and stdin"):
                QUALIFY.qualify(ROOT, candidate="1" * 40, product_head="2" * 40, baseline="3" * 40,
                               output=Path("unused.json"))
            self.assertFalse(any(key in os.environ for key in tokens))
            for value in tokens.values():
                self.assertNotIn(value, QUALIFY.delivery.clean(value))
        child.assert_not_called()

    def test_native_receipt_sibling_cannot_replace_existing_inputs(self):
        with tempfile.TemporaryDirectory(prefix="qualification-native-existing-") as temporary:
            root = Path(temporary)
            scratch = root / "scratch"
            scratch.mkdir()
            output = root / "receipt.json"
            retained = root / "receipt.json.native-inputs"
            retained.mkdir()
            (retained / "keep").write_bytes(b"preserve")
            with mock.patch.dict(os.environ, TMPDIR=str(scratch)), mock.patch.object(QUALIFY, "git") as command, \
                    self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "fresh receipt sibling"):
                QUALIFY.qualify(root, candidate="1" * 40, product_head="2" * 40, baseline="3" * 40, output=output)
            command.assert_not_called()
            self.assertEqual(b"preserve", (retained / "keep").read_bytes())

    def test_only_real_global_child_receives_token_and_diagnostics_are_redacted(self):
        token = QUALIFY.read_owner_token(io.BytesIO(b'{"ownerReadToken":"inert-owner-child-token"}'))
        with tempfile.TemporaryDirectory(prefix="qualification-token-") as temporary:
            root = Path(temporary)
            (root / "tools").mkdir()
            (root / "tools/check_global.py").write_text(
                "import os,sys\n"
                "assert os.environ['GH_TOKEN'] == 'inert-owner-child-token'\n"
                "assert 'GITHUB_TOKEN' not in os.environ and 'ZIZMOR_GITHUB_TOKEN' not in os.environ\n"
                "assert not sys.stdin.buffer.read()\n"
                "print(os.environ['GH_TOKEN'])\n"
                "print(os.environ['GH_TOKEN'],file=sys.stderr)\n")
            with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout, \
                    mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
                QUALIFY.check_global(root, token)
            self.assertNotIn(token, stdout.getvalue() + stderr.getvalue())
            self.assertIn("[redacted]", stdout.getvalue())
            self.assertIn("[redacted]", stderr.getvalue())
            subprocess.run([sys.executable, "-I", "-c",
                "import os; assert not any(k in os.environ for k in " + repr(QUALIFY.CREDENTIAL_KEYS) + ")"], check=True)
            (root / "tools/check_global.py").write_text("raise SystemExit(7)\n")
            with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "mandatory global owner checks failed"):
                QUALIFY.check_global(root, token)
            with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "require --global-check-token-stdin"):
                QUALIFY.check_global(root, "")

    def test_actual_cli_accepts_stdin_and_refuses_inherited_token_without_exposure(self):
        with tempfile.TemporaryDirectory(prefix="qualification-cli-") as temporary:
            root = Path(temporary)
            scratch = root / "scratch"
            scratch.mkdir()
            arguments = [sys.executable, "-I", str(ROOT / "tools/qualify_conversations.py"),
                "--project-root", str(ROOT), "--candidate", "1" * 40, "--product-head", "2" * 40,
                "--baseline", "3" * 40, "--output", str(root / "receipt.json"), "--global-check-token-stdin"]
            token = "inert-real-cli-token"
            for inherited in (False, True):
                environment = dict(os.environ, TMPDIR=str(scratch))
                if inherited:
                    environment["GH_TOKEN"] = token
                result = subprocess.run(arguments, input=json.dumps({"ownerReadToken": token}),
                    env=environment, capture_output=True, text=True, timeout=60)
                self.assertEqual(1, result.returncode)
                self.assertNotIn(token, result.stdout + result.stderr)
                self.assertIn("inherited credential aliases" if inherited else "exact committed CiCd", result.stderr)

    def native_fixture(self, root):
        module, builds = root / "module", root / "builds"
        for directory in (module, builds):
            directory.mkdir()
            QUALIFY.git(directory, "init", "--template=")
        sources = {"global.json": b'{"sdk":{"version":"11.0.100"}}', "Hexalith.Conversations.slnx": b"solution",
            QUALIFY.NATIVE_PROJECT + "/BoundaryAssertionsTests.cs": b"original assertions",
            "docs/release-evidence/story-10.1-final-record-v2.json": b"signed record",
            "docs/release-evidence/success-metric-report-and-attestation-v1.json": b"signed attestation"}
        for name, content in sources.items():
            path = module / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        support = builds / "Github/lib/module_preparation.py"
        support.parent.mkdir(parents=True)
        support.write_text("# released library\n")
        for directory in (module, builds):
            QUALIFY.git(directory, "add", ".")
            QUALIFY.git(directory, "commit", "-m", "fixture")
        identities = {"candidate": "1" * 40, "productHead": QUALIFY.git(module, "rev-parse", "HEAD").decode().strip(),
            "buildsCommit": QUALIFY.git(builds, "rev-parse", "HEAD").decode().strip(),
            "producer": {"version": "6.0.99", "sourceCommit": "2" * 40, "sha256": "3" * 64}}
        binary = module / QUALIFY.NATIVE_PROJECT / "bin/Release/net11.0"
        binary.mkdir(parents=True)
        for suffix in (".dll", ".deps.json", ".runtimeconfig.json"):
            (binary / ("Hexalith.Conversations.TestSupport.Tests" + suffix)).write_bytes(b"actual built bytes" + suffix.encode())
        (binary / "nested").mkdir()
        (binary / "nested/dependency.dll").write_bytes(b"complete dependency bytes")
        (module / "unrelated-secret-cache").write_text("never retained")
        return module, builds, identities, binary

    def test_native_inputs_survive_workspace_removal_with_exact_hashes_and_no_machine_state(self):
        with tempfile.TemporaryDirectory(prefix="qualification-native-") as temporary:
            root = Path(temporary)
            work = root / "work"
            work.mkdir()
            module, builds, identities, binary = self.native_fixture(work)
            destination = root / "retained"
            with mock.patch.object(QUALIFY, "NATIVE_HISTORICAL_COMMIT", identities["productHead"]), \
                    mock.patch.object(QUALIFY.subprocess, "check_output", return_value="11.0.100\n"):
                receipt = QUALIFY.retain_native_inputs(module, builds, destination, identities=identities)
            shutil.rmtree(work)
            payload = (destination / "manifest.json").read_bytes()
            manifest = json.loads(payload)
            self.assertEqual(QUALIFY.digest(payload), receipt["manifestSha256"])
            self.assertEqual(identities, manifest["identities"])
            self.assertEqual("11.0.100", manifest["sdk"])
            self.assertIn("pending", manifest["nativeWindows"])
            self.assertTrue((destination / manifest["entrypoint"]).is_file())
            files = {row["path"]: row for row in manifest["files"]}
            actual = {path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file()}
            self.assertEqual(actual - {"manifest.json"}, set(files))
            self.assertEqual(receipt["files"], len(files))
            self.assertEqual(receipt["bytes"], sum(row["bytes"] for row in files.values()))
            for name, row in files.items():
                content = (destination / name).read_bytes()
                self.assertEqual(row["bytes"], len(content))
                self.assertEqual(row["sha256"], QUALIFY.digest(content))
                self.assertNotIn(".git", Path(name).parts)
                self.assertNotIn("unrelated-secret-cache", name)
            historical = (destination / "historical-commit.bin").read_bytes()
            self.assertEqual(identities["productHead"], hashlib.sha1(
                b"commit " + str(len(historical)).encode() + b"\0" + historical).hexdigest())
            (destination / manifest["entrypoint"]).write_bytes(b"tampered")
            self.assertNotEqual(files[manifest["entrypoint"]]["sha256"], QUALIFY.digest(
                (destination / manifest["entrypoint"]).read_bytes()))

    def test_native_retention_refuses_incomplete_mutated_linked_or_unbounded_inputs_and_cleans(self):
        for fault in ("missing", "source", "mode", "link", "ancestor", "size", "count", "total", "sdk", "product", "builds", "history", "collision",
                      "directory-case", "backslash", "device", "wildcard", "dot"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix="qualification-native-refusal-") as temporary:
                root = Path(temporary)
                module, builds, identities, binary = self.native_fixture(root)
                destination = root / "retained"
                if fault == "missing":
                    (binary / "Hexalith.Conversations.TestSupport.Tests.runtimeconfig.json").unlink()
                elif fault == "source":
                    (module / QUALIFY.NATIVE_PROJECT / "BoundaryAssertionsTests.cs").write_text("changed assertions")
                elif fault == "mode":
                    (module / QUALIFY.NATIVE_PROJECT / "BoundaryAssertionsTests.cs").chmod(0o755)
                elif fault == "link":
                    (binary / "external.dll").symlink_to(module / "global.json")
                elif fault == "ancestor":
                    binary.rename(root / "linked-output")
                    binary.symlink_to(root / "linked-output", target_is_directory=True)
                elif fault == "collision":
                    (binary / "HEXALITH.CONVERSATIONS.TESTSUPPORT.TESTS.DLL").write_bytes(b"case collision")
                elif fault == "directory-case":
                    (binary / "NESTED").mkdir()
                    (binary / "NESTED/other.dll").write_bytes(b"directory collision")
                elif fault in ("backslash", "device", "wildcard", "dot"):
                    (binary / {"backslash": "..\\escape.dll", "device": "CON.dll", "wildcard": "bad?.dll", "dot": "bad."}[fault]).write_bytes(b"unsafe")
                elif fault in ("product", "builds"):
                    identities["productHead" if fault == "product" else "buildsCommit"] = "f" * 40
                with mock.patch.object(QUALIFY, "NATIVE_HISTORICAL_COMMIT",
                        "f" * 40 if fault == "history" else QUALIFY.git(module, "rev-parse", "HEAD").decode().strip()), \
                        mock.patch.object(QUALIFY, "NATIVE_MAX_FILE_BYTES", 1 if fault == "size" else 128 * 1024 * 1024), \
                        mock.patch.object(QUALIFY, "NATIVE_MAX_FILES", 1 if fault == "count" else 10000), \
                        mock.patch.object(QUALIFY, "NATIVE_MAX_BYTES", 1 if fault == "total" else 1024 * 1024 * 1024), \
                        mock.patch.object(QUALIFY.subprocess, "check_output", return_value="10.0.100" if fault == "sdk" else "11.0.100"), \
                        self.assertRaises((QUALIFY.delivery.DeliveryError, FileNotFoundError)):
                    QUALIFY.retain_native_inputs(module, builds, destination, identities=identities)
                self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
