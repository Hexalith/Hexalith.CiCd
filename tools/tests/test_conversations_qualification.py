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

    def test_real_historical_fixture_acquisition_preserves_selected_release_and_missing_refs_fail(self):
        declarations = json.loads((ROOT / "tools/tests/fixtures/builds-releases.json").read_bytes())
        with tempfile.TemporaryDirectory(prefix="qualification-release-fixtures-") as temporary:
            root = Path(temporary)
            owner = root / "owner"
            manifest = owner / "tools/tests/fixtures/builds-releases.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps(declarations))
            remote = root / "remote.git"
            remote.mkdir()
            QUALIFY.git(remote, "init", "--bare", "--template=")
            source = ROOT / "references/Hexalith.Builds"
            selected = (ROOT / "builds-version").read_text().strip()
            QUALIFY.git(remote, "fetch", "--no-tags", "--no-recurse-submodules", str(source),
                        f"refs/tags/{selected}:refs/tags/{selected}")
            builds = root / "builds"
            builds.mkdir()
            QUALIFY.git(builds, "init", "--template=")
            QUALIFY.git(builds, "remote", "add", "origin", str(remote))
            QUALIFY.git(builds, "fetch", "--no-tags", "--no-recurse-submodules", "origin",
                        f"refs/tags/{selected}:refs/tags/{selected}")
            QUALIFY.git(builds, "checkout", "--detach", f"refs/tags/{selected}")
            head = QUALIFY.git(builds, "rev-parse", "HEAD")
            with self.assertRaises(QUALIFY.delivery.DeliveryError):
                QUALIFY.acquire_fixture_releases(owner, builds)
            historical = {key: declarations[key] for key in ("delivery", "renderer")}
            for expected in (historical, declarations):
                with self.subTest(fixtures=list(expected)):
                    manifest.write_text(json.dumps(expected))
                    for entry in expected.values():
                        tag = entry["tag"]
                        QUALIFY.git(remote, "fetch", "--no-tags", "--no-recurse-submodules", str(source),
                                    f"refs/tags/{tag}:refs/tags/{tag}")
                    self.assertEqual(expected, QUALIFY.acquire_fixture_releases(owner, builds))
                    self.assertEqual(head, QUALIFY.git(builds, "rev-parse", "HEAD"))
                    self.assertEqual(b"", QUALIFY.git(builds, "status", "--porcelain"))
                    for entry in expected.values():
                        self.assertEqual(entry["commit"], QUALIFY.git(builds, "rev-parse",
                            "refs/tags/" + entry["tag"] + "^{commit}").decode().strip())
            declarations["renderer"]["commit"] = "1" * 40
            manifest.write_text(json.dumps(declarations))
            with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "fixture release identity"):
                QUALIFY.acquire_fixture_releases(owner, builds)
            self.assertEqual(head, QUALIFY.git(builds, "rev-parse", "HEAD"))

    def test_fixture_release_manifest_refuses_unbounded_or_nonliteral_inputs_before_git(self):
        valid = json.loads((ROOT / "tools/tests/fixtures/builds-releases.json").read_bytes())
        with tempfile.TemporaryDirectory(prefix="qualification-release-manifest-") as temporary:
            root = Path(temporary)
            manifest = root / "tools/tests/fixtures/builds-releases.json"
            manifest.parent.mkdir(parents=True)
            invalid = [[], {}, {"delivery": valid["delivery"]},
                {**valid, "unknown": valid["renderer"]},
                {**valid, "renderer": {**valid["renderer"], "tag": "main"}},
                {**valid, "renderer": {**valid["renderer"], "commit": "not-a-sha"}},
                {**valid, "renderer": {**valid["renderer"], "unexpected": True}}]
            for document in invalid:
                with self.subTest(document=document):
                    manifest.write_text(json.dumps(document))
                    with mock.patch.object(QUALIFY, "git") as command, self.assertRaises(QUALIFY.delivery.DeliveryError):
                        QUALIFY.acquire_fixture_releases(root, root / "builds")
                    command.assert_not_called()
            manifest.write_bytes(b" " * 4097)
            with mock.patch.object(QUALIFY, "git") as command, self.assertRaises(QUALIFY.delivery.DeliveryError):
                QUALIFY.acquire_fixture_releases(root, root / "builds")
            command.assert_not_called()

    def test_canonical_owned_mask_preserves_partial_npm_and_instruction_files(self):
        # A nightly bump leases released Git objects without a Builds checkout.
        # Keep the real pinned library export alive for this complete control.
        contract = self.enterContext(QUALIFY.renderer.pinned_contract(ROOT))
        spec = importlib.util.spec_from_file_location(
            "_qualification_fixture_perimeter", contract.root / "Github/lib/perimeter.py")
        perimeter = importlib.util.module_from_spec(spec)
        self.enterContext(mock.patch.dict(sys.modules, {spec.name: perimeter}))
        spec.loader.exec_module(perimeter)
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

    def test_approved_artifact_inventory_pins_only_the_two_user_approved_v4_bytes(self):
        self.assertEqual({
            "docs/release-evidence/public-contract-shape-bounded-read-v4.json":
                "4de710b386ff63a2316c603e40556bc78b0f61bbf1635a419cf0d436a1353d74",
            "docs/release-evidence/public-contract-shape-bounded-read-v4-review.json":
                "f90f69acda2e858b99980ae8b59ee00b936ff2fb91276215f4a1c71aa5716227",
        }, QUALIFY.APPROVED_ARTIFACT_ADDITIONS)
        self.assertFalse(any(prefix.startswith("docs/") for prefix in QUALIFY.PRODUCT_PATHS))

    def test_product_diff_accepts_exact_approved_regular_artifact_additions(self):
        # Supply a small test approval for the same literal paths, then exercise
        # the production digest/mode/addition guard without a module checkout.
        payloads = {path: ("100644", ("approved fixture " + path).encode())
                    for path in QUALIFY.APPROVED_ARTIFACT_ADDITIONS}
        pins = {path: QUALIFY.digest(data) for path, (_, data) in payloads.items()}
        before = {"src/Product.cs": ("100644", b"old")}
        after = {"src/Product.cs": ("100644", b"new"), **payloads}
        with mock.patch.dict(QUALIFY.APPROVED_ARTIFACT_ADDITIONS, pins, clear=True):
            result = QUALIFY.product_difference(snapshot(before), snapshot(after))
        additions = {row["path"]: row for row in result if row["path"] in payloads}
        self.assertEqual(set(payloads), set(additions))
        for path, row in additions.items():
            self.assertIsNone(row["before"])
            self.assertEqual({"mode": "100644", "oid": QUALIFY.digest(payloads[path][1])}, row["after"])

    def test_product_diff_refuses_wrong_bytes_modes_and_existing_artifact_changes(self):
        for path in tuple(QUALIFY.APPROVED_ARTIFACT_ADDITIONS):
            approved = b"exact approved test artifact"
            pins = {path: QUALIFY.digest(approved)}
            cases = {
                "wrong-bytes": ({}, {path: ("100644", approved + b"changed")}),
                "executable": ({}, {path: ("100755", approved)}),
                "symlink": ({}, {path: ("120000", approved)}),
                "gitlink": ({}, {path: ("160000", approved)}),
                "modify-existing": ({path: ("100644", b"previous")}, {path: ("100644", approved)}),
                "remove-existing": ({path: ("100644", approved)}, {}),
                "change-existing-mode": ({path: ("100644", approved)}, {path: ("100755", approved)}),
            }
            for fault, (before, after) in cases.items():
                with self.subTest(path=path, fault=fault), \
                        mock.patch.dict(QUALIFY.APPROVED_ARTIFACT_ADDITIONS, pins, clear=True), \
                        self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "exact approved append-only"):
                    QUALIFY.product_difference(snapshot(before), snapshot(after))

    def test_product_diff_does_not_let_valid_additions_admit_an_unapproved_frozen_change(self):
        payloads = {path: ("100644", ("approved fixture " + path).encode())
                    for path in QUALIFY.APPROVED_ARTIFACT_ADDITIONS}
        pins = {path: QUALIFY.digest(data) for path, (_, data) in payloads.items()}
        frozen = "docs/release-evidence/public-contract-shape-story-6.4-v3.json"
        with mock.patch.dict(QUALIFY.APPROVED_ARTIFACT_ADDITIONS, pins, clear=True), \
                self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "outside the approved central product inventory"):
            QUALIFY.product_difference(snapshot({frozen: ("100644", b"original")}),
                snapshot({**payloads, frozen: ("100644", b"changed")}))

    def test_product_diff_keeps_unchanged_approved_artifacts_without_retiring_immutability(self):
        path = next(iter(QUALIFY.APPROVED_ARTIFACT_ADDITIONS))
        retained = {path: ("100644", b"already published unchanged artifact")}
        before = snapshot({**retained, "src/Product.cs": ("100644", b"old")})
        after = snapshot({**retained, "src/Product.cs": ("100644", b"new")})
        self.assertEqual(["src/Product.cs"], [row["path"] for row in QUALIFY.product_difference(before, after)])

    def test_product_diff_refuses_all_unapproved_docs_and_frozen_api_changes(self):
        approved_path = next(iter(QUALIFY.APPROVED_ARTIFACT_ADDITIONS))
        paths = (
            "docs/release-evidence/public-contract-shape-baseline-v1.json",
            "docs/release-evidence/public-contract-shape-story-9.2-v2.json",
            "docs/release-evidence/public-contract-shape-story-6.4-v3.json",
            "docs/release-evidence/public-contract-shape-story-6.4-v3-review.json",
            "docs/release-evidence/unapproved.json", "docs/README.md",
            approved_path + ".bak", approved_path + "/child.json", approved_path.upper(),
        )
        for path in paths:
            for operation, before, after in (
                ("add", {}, {path: ("100644", b"new")}),
                ("modify", {path: ("100644", b"old")}, {path: ("100644", b"new")}),
                ("remove", {path: ("100644", b"old")}, {}),
            ):
                with self.subTest(path=path, operation=operation), \
                        self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "outside the approved central product inventory"):
                    QUALIFY.product_difference(snapshot(before), snapshot(after))

    def direct_runtime_fixture(self, directory):
        work = directory / "work"
        private = work / "dapr-qualification-control"
        runtime, shims, verified = private / "runtime", private / "bin", private / "verified-cli"
        runtime_bin = runtime / ".dapr/bin"
        decoy = directory / "decoy"
        for path in (runtime_bin, shims, verified, decoy):
            path.mkdir(parents=True)
        private.chmod(0o700)
        for path, marker in ((runtime_bin / "daprd", "selected-runtime"), (verified / "dapr", "verified-cli"),
                (shims / "dapr", "selected-cli-shim"), (shims / "docker", "selected-docker-shim"),
                (decoy / "daprd", "decoy-runtime"), (decoy / "dapr", "decoy-cli"), (decoy / "docker", "decoy-docker")):
            path.write_text("#!/bin/sh\nprintf '%s\\n' '" + marker + "'\n")
            path.chmod(0o755)
        return SimpleNamespace(work=work, private=private, runtime=runtime, runtime_bin=runtime_bin,
            shims=shims, decoy=decoy,
            selected={"runtimePath": str(runtime), "cli": str(verified / "dapr")})

    def test_direct_dapr_uses_actual_selected_executable_and_preserves_cli_docker_shims_and_home(self):
        with tempfile.TemporaryDirectory(prefix="qualification-direct-dapr-") as temporary:
            fixture = self.direct_runtime_fixture(Path(temporary))
            # Neither a flat binary nor a guessed runtime/bin is the CLI layout.
            for directory in (fixture.runtime, fixture.runtime / "bin"):
                directory.mkdir(exist_ok=True)
                alternate = directory / "daprd"
                alternate.write_text("#!/bin/sh\nprintf 'wrong-runtime-layout'\n")
                alternate.chmod(0o755)
            original = str(fixture.shims) + os.pathsep + str(fixture.decoy) + os.pathsep + os.environ["PATH"]
            with mock.patch.dict(os.environ, PATH=original, HOME=str(fixture.decoy)):
                self.assertEqual("decoy-runtime", subprocess.check_output(["daprd"], text=True).strip())
                with QUALIFY.direct_dapr_runtime(fixture.work, fixture.selected):
                    self.assertEqual(str(fixture.runtime_bin / "daprd"), shutil.which("daprd"))
                    self.assertEqual("selected-runtime", subprocess.check_output(["daprd", "--version"], text=True).strip())
                    self.assertEqual("selected-cli-shim", subprocess.check_output(["dapr"], text=True).strip())
                    self.assertEqual("selected-docker-shim", subprocess.check_output(["docker"], text=True).strip())
                    self.assertEqual([str(fixture.shims), str(fixture.runtime_bin)], os.environ["PATH"].split(os.pathsep)[:2])
                    self.assertEqual(str(fixture.decoy), os.environ["HOME"])
                self.assertEqual(original, os.environ["PATH"])
                self.assertEqual(str(fixture.decoy), os.environ["HOME"])
                self.assertEqual("decoy-runtime", subprocess.check_output(["daprd"], text=True).strip())

    def test_direct_dapr_restores_exact_path_on_child_failure_or_environment_mutation(self):
        with tempfile.TemporaryDirectory(prefix="qualification-direct-dapr-restore-") as temporary:
            fixture = self.direct_runtime_fixture(Path(temporary))
            for original in (str(fixture.shims), str(fixture.shims) + os.pathsep,
                             str(fixture.shims) + os.pathsep + str(fixture.decoy)):
                with self.subTest(original=original), mock.patch.dict(os.environ, PATH=original):
                    with self.assertRaisesRegex(RuntimeError, "child failed"):
                        with QUALIFY.direct_dapr_runtime(fixture.work, fixture.selected):
                            os.environ.pop("PATH")
                            raise RuntimeError("child failed")
                    self.assertEqual(original, os.environ["PATH"])

    def test_direct_dapr_refuses_none_or_malformed_selection_before_exposing_any_runtime(self):
        with tempfile.TemporaryDirectory(prefix="qualification-direct-dapr-selection-") as temporary:
            fixture = self.direct_runtime_fixture(Path(temporary))
            original = str(fixture.shims) + os.pathsep + str(fixture.decoy)
            selections = [None, [], "runtime", {}, {"runtimePath": str(fixture.runtime)},
                {**fixture.selected, "runtimePath": None}, {**fixture.selected, "runtimePath": fixture.runtime},
                {**fixture.selected, "runtimePath": "relative/runtime"}, {**fixture.selected, "runtimePath": "bad\0path"},
                {**fixture.selected, "cli": str(fixture.decoy / "dapr")}]
            for selected in selections:
                with self.subTest(selectedType=type(selected).__name__), mock.patch.dict(os.environ, PATH=original):
                    with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "invalid selected Dapr runtime"):
                        with QUALIFY.direct_dapr_runtime(fixture.work, selected):
                            self.fail("invalid selection entered its child scope")
                    self.assertEqual(original, os.environ["PATH"])
                    self.assertEqual(str(fixture.decoy / "daprd"), shutil.which("daprd"))

    def test_direct_dapr_refuses_absent_empty_or_reordered_shim_path_without_mutation(self):
        with tempfile.TemporaryDirectory(prefix="qualification-direct-dapr-shims-") as temporary:
            fixture = self.direct_runtime_fixture(Path(temporary))
            for original in (None, "", str(fixture.decoy) + os.pathsep + str(fixture.shims)):
                environment = dict(os.environ)
                if original is None:
                    environment.pop("PATH", None)
                else:
                    environment["PATH"] = original
                with self.subTest(path=original), mock.patch.dict(os.environ, environment, clear=True):
                    with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "invalid selected Dapr runtime"):
                        with QUALIFY.direct_dapr_runtime(fixture.work, fixture.selected):
                            self.fail("missing/reordered shim scope was accepted")
                    self.assertEqual(original, os.environ.get("PATH"))

    def test_direct_dapr_refuses_escape_links_missing_nonexecutable_and_foreign_owned_inputs(self):
        faults = ("escape", "dotdot", "product-path", "missing", "directory", "nonexecutable", "binary-link",
                  "runtime-link", "runtime-home-link", "runtime-bin-link", "shim-link", "cli-link",
                  "flat-runtime", "foreign-owner", "malformed-work")
        for fault in faults:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix="qualification-direct-dapr-path-") as temporary:
                root = Path(temporary)
                fixture = self.direct_runtime_fixture(root)
                selected = dict(fixture.selected)
                work = fixture.work
                if fault == "escape":
                    selected["runtimePath"] = str(root / "dapr-qualification-foreign/runtime")
                elif fault == "dotdot":
                    selected["runtimePath"] = str(fixture.private / ".." / fixture.private.name / "runtime")
                elif fault == "product-path":
                    selected["runtimePath"] = str(work / "module/runtime")
                elif fault in ("missing", "directory", "nonexecutable", "binary-link"):
                    executable = fixture.runtime_bin / "daprd"
                    if fault == "nonexecutable":
                        executable.chmod(0o644)
                    else:
                        executable.unlink()
                        if fault == "directory": executable.mkdir()
                        elif fault == "binary-link": executable.symlink_to(fixture.decoy / "daprd")
                elif fault in ("runtime-link", "runtime-home-link", "runtime-bin-link", "shim-link"):
                    directory = {"runtime-link": fixture.runtime, "runtime-home-link": fixture.runtime_bin.parent,
                                 "runtime-bin-link": fixture.runtime_bin, "shim-link": fixture.shims}[fault]
                    directory.rename(root / "foreign-directory")
                    directory.symlink_to(root / "foreign-directory", target_is_directory=True)
                elif fault == "flat-runtime":
                    (fixture.runtime_bin / "daprd").rename(fixture.runtime / "daprd")
                elif fault == "cli-link":
                    cli = Path(selected["cli"])
                    cli.unlink(); cli.symlink_to(fixture.decoy / "dapr")
                elif fault == "malformed-work":
                    work = None
                original = str(fixture.shims) + os.pathsep + str(fixture.decoy)
                with mock.patch.dict(os.environ, PATH=original), \
                        mock.patch.object(QUALIFY.os, "getuid", return_value=os.getuid() + (1 if fault == "foreign-owner" else 0)):
                    with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "invalid selected Dapr runtime"):
                        with QUALIFY.direct_dapr_runtime(work, selected):
                            self.fail("unsafe selected runtime entered child scope")
                    self.assertEqual(original, os.environ["PATH"])

    def test_direct_dapr_never_shadows_an_unexpected_first_shim_runtime(self):
        with tempfile.TemporaryDirectory(prefix="qualification-direct-dapr-precedence-") as temporary:
            fixture = self.direct_runtime_fixture(Path(temporary))
            collision = fixture.shims / "daprd"
            collision.write_text("#!/bin/sh\nprintf 'unexpected-first-shim'\n"); collision.chmod(0o755)
            original = str(fixture.shims) + os.pathsep + str(fixture.decoy)
            with mock.patch.dict(os.environ, PATH=original):
                with self.assertRaisesRegex(QUALIFY.delivery.DeliveryError, "invalid selected Dapr runtime"):
                    with QUALIFY.direct_dapr_runtime(fixture.work, fixture.selected):
                        self.fail("a first-shim collision was silently shadowed")
                self.assertEqual(original, os.environ["PATH"])

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
