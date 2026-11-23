#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Real writer reconstruction and rejection of adversarial candidates/races."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from bump_support import br, rt, writer, IDENTITY, Workspace, FixtureGit, git


class PushTests(unittest.TestCase):
    def workspace(self):
        temporary = tempfile.TemporaryDirectory(prefix="bump-writer-test-")
        self.addCleanup(temporary.cleanup)
        w = Workspace(temporary.name)
        report = w.produce()
        self.assertEqual(report["result"], "candidate", report)
        return w

    def assert_refused(self, w, value, reason):
        before = git(w.cicd, "rev-parse", "HEAD")
        report = w.push(value)
        self.assertEqual(report["result"], "failed", report)
        self.assertIn(reason, report["reason"])
        self.assertEqual(git(w.cicd, "rev-parse", "HEAD"), before)
        self.assertEqual(w.transport.api.dispatched, 0)

    def test_exact_candidate_push_and_explicit_delivery_dispatch(self):
        w = self.workspace()
        value = w.value()
        report = w.push()
        self.assertEqual(report["result"], "pushed", report)
        self.assertEqual(git(w.cicd, "rev-parse", "HEAD"), value["candidate"])
        self.assertEqual(git(w.cicd, "show", "HEAD^:product.txt"), "preserved")
        self.assertEqual(w.transport.api.dispatched, 1)
        self.assertIn("hexalith-nightly-bump: 2026-11-14", git(w.cicd, "show", "-s", "--format=%B", "HEAD"))

    def test_isolated_producer_and_writer_entrypoints_keep_tokens_out_of_handoffs(self):
        w = self.workspace()
        config = w.root / "fixture.json"
        config.write_text(json.dumps(w.config()))
        env = os.environ | {"BUMP_DIRECTORY": str(w.directory), "GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd",
                            "GITHUB_OUTPUT": str(w.root / "outputs"), "GITHUB_STEP_SUMMARY": str(w.root / "summary"),
                            "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": "a" * 40,
                            "GITHUB_RUN_ID": "101", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_EVENT_NAME": "schedule",
                            "GITHUB_TOKEN": "inert-read-only-job-token", "CICD_TOKEN": "inert-write-job-token",
                            "BUMP_ARTIFACT_ID": "9", "BUMP_ARTIFACT_DIGEST": "a" * 64}
        driver = Path(__file__).with_name("bump_support.py")
        for operation in ("produce", "push"):
            result = subprocess.run([sys.executable, "-I", str(driver), str(config), operation],
                                    env=env, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn(b"inert-read-only-job-token", result.stdout + result.stderr)
            self.assertNotIn(b"inert-write-job-token", result.stdout + result.stderr)
        for path in w.directory.glob("*.json"):
            self.assertNotIn(b"job-token", path.read_bytes())
        self.assertEqual(git(w.cicd, "rev-parse", "HEAD"), w.value()["candidate"])

    def test_app_fallback_uses_same_checks_without_dispatch(self):
        w = self.workspace()
        report = w.push(mode="app")
        self.assertEqual(report["result"], "pushed", report)
        self.assertEqual(w.transport.api.dispatched, 0)

    def test_dispatch_failure_preserves_confirmed_push_for_observer(self):
        w = self.workspace()
        with mock.patch.object(w.transport.api, "dispatch_delivery", side_effect=rt.NightlyError("dispatch result uncertain")):
            report = w.push()
        self.assertEqual(report["result"], "pushed", report)
        self.assertEqual(report["candidate"], w.value()["candidate"])
        self.assertTrue(report["failed"])
        self.assertIn("uncertain", report["reason"])

    def test_corrupt_object_and_attempt_identity_rejected(self):
        w = self.workspace()
        value = w.value()
        value["objects"][0]["data"] = "Y29ycnVwdA=="
        self.assert_refused(w, value, "hash mismatch")
        value = w.value()
        value["identity"]["attempt"] += 1
        self.assert_refused(w, value, "identity mismatch")

    def test_duplicate_and_unsorted_git_tree_entries_refused(self):
        entry = b"100644 same\0" + b"a" * 20
        for data in (entry + entry, b"100644 z\0" + b"a" * 20 + b"100644 a\0" + b"b" * 20):
            with self.assertRaisesRegex(rt.NightlyError, "tree"):
                br.canonical_tree(data)

    def test_wrong_parent_and_subject_rejected(self):
        w = self.workspace()
        value = w.value()
        value["base"] = w.old["commit"]
        self.assert_refused(w, value, "captured candidate parent")
        value = w.value()
        value["identity"]["night"] = "2026-11-15"
        self.assert_refused(w, value, "identity mismatch")

    def test_extra_path_and_mode_mutations_rejected(self):
        for kind in ("extra", "mode", "remove", "unrelated"):
            with self.subTest(kind=kind):
                w = self.workspace()
                def change(store):
                    path = "rendered/Hexalith.Alpha/.github/workflows/ci.yml"
                    oid = store.run("hash-object", "-w", "--stdin", data=b"arbitrary\n").decode().strip()
                    if kind == "extra":
                        store.run("update-index", "--add", "--cacheinfo", "100644", oid, "rendered/new.txt")
                    elif kind == "remove":
                        store.run("update-index", "--index-info", data=("0 " + "0" * 40 + "\t" + path + "\n").encode())
                    elif kind == "mode":
                        store.run("update-index", "--cacheinfo", "100755", oid, path)
                    else:
                        store.run("update-index", "--cacheinfo", "100644", oid, "product.txt")
                value = w.mutate(w.value(), change)
                self.assert_refused(w, value, "adds or removes" if kind in {"extra", "remove"} else "mode" if kind == "mode" else "outside")

    def test_arbitrary_rendered_edits_rejected(self):
        w = self.workspace()
        def change(store):
            oid = store.run("hash-object", "-w", "--stdin", data=b"runs: arbitrary code\n").decode().strip()
            store.run("update-index", "--cacheinfo", "100644", oid, "rendered/Hexalith.Alpha/.github/workflows/ci.yml")
        self.assert_refused(w, w.mutate(w.value(), change), "bytes differ")

    def test_unchanged_old_render_cannot_hide_behind_pin_only_bump(self):
        w = self.workspace()
        def change(store):
            path = "rendered/Hexalith.Alpha/.github/workflows/ci.yml"
            original = store.items(w.base)[path][2]
            store.run("update-index", "--cacheinfo", "100644", original, path)
        self.assert_refused(w, w.mutate(w.value(), change), "bytes differ")

    def test_new_main_and_new_release_races(self):
        w = self.workspace()
        (w.cicd / "product.txt").write_text("racing main\n")
        w.commit()
        self.assert_refused(w, w.value(), "main advanced")
        w = self.workspace()
        w.release("v5.3.0")
        self.assert_refused(w, w.value(), "newest acceptable")

    def test_pre_push_main_race_never_rebases(self):
        w = self.workspace()
        # Producer observes main once; writer verification then final check.
        def race():
            (w.cicd / "product.txt").write_text("race immediately before push\n")
            w.commit()
        w.main_hooks[w.transport.main_calls + 2] = race
        report = w.push()
        self.assertEqual(report["result"], "failed", report)
        self.assertIn("raced before", report["reason"])
        self.assertNotEqual(git(w.cicd, "rev-parse", "HEAD"), w.value()["candidate"])

    def test_nested_defaults_local_refs_conditionals_and_wrong_defaults(self):
        for wrong in (False, True):
            with self.subTest(wrong=wrong):
                temporary = tempfile.TemporaryDirectory(prefix="bump-defaults-test-")
                self.addCleanup(temporary.cleanup)
                w = Workspace(temporary.name)
                schema = {"properties": {"tests": {"properties": {"nested": {"$ref": "#/$defs/new"}}}},
                          "$defs": {"new": {"default": {}, "properties": {"enabled": {"default": False}}}},
                          "allOf": [{"if": {"properties": {"buildsTag": {"const": "v5.3.0"}}, "required": ["buildsTag"]},
                                     "then": {"properties": {"extra": {"default": []}}}}]}
                w.release("v5.3.0", schema=schema)
                def render(project):
                    w.render(project)
                    path = project / "rendered/Hexalith.Alpha/.github/hexalith-ci.json"
                    value = json.loads(path.read_bytes())
                    value["tests"]["nested"] = {"enabled": wrong}
                    value["extra"] = []
                    path.write_text(json.dumps(value) + "\n")
                report = w.produce(render=render)
                if wrong:
                    self.assertEqual(report["result"], "failed", report)
                    self.assertIn("defaults", report["reason"])
                else:
                    self.assertEqual(report["result"], "candidate", report)
                    report = w.push()
                    self.assertEqual(report["result"], "pushed", report)

    def test_unsupported_schema_condition_fails_closed(self):
        schema = {"properties": {"new": {"default": 1}}, "if": {"minProperties": 1},
                  "then": {"properties": {"other": {"default": 2}}}}
        with self.assertRaisesRegex(rt.NightlyError, "unsupported schema default condition"):
            br.add_defaults({}, schema, schema)
        self.assertFalse(br.condition({"nested": False}, {"const": {"nested": 0}}, {}))
        self.assertTrue(br.condition({"nested": 1.0}, {"const": {"nested": 1}}, {}))

    def test_min_items_selects_defaults_only_by_array_length(self):
        schema = {"if": {"properties": {"projects": {"minItems": 1}}, "required": ["projects"]},
                  "then": {"properties": {"mode": {"default": "with-projects"}}},
                  "else": {"properties": {"mode": {"default": "empty"}}}}
        for value, expected in (({}, "empty"), ({"projects": []}, "empty"),
                                ({"projects": ["one"]}, "with-projects"),
                                ({"projects": ["one", "two"]}, "with-projects"), ({"projects": None}, "with-projects")):
            with self.subTest(value=value):
                self.assertEqual(br.add_defaults(value, schema, schema)["mode"], expected)
        self.assertTrue(br.condition([], {"minItems": 0}, {}))
        self.assertTrue(br.condition(["one"], {"minItems": 1.0}, {}))
        for invalid in (-1, True, "1", 1.5, None, float("inf"), float("nan")):
            with self.subTest(minimum=invalid), self.assertRaisesRegex(rt.NightlyError, "minItems"):
                br.condition([], {"minItems": invalid}, {})

    def test_writer_rejects_unverified_conditional_additions(self):
        for predicate, reason in (({"minItems": 1}, "differ from tagged schema defaults"),
                                  ({"maxItems": 0}, "unsupported schema default condition")):
            with self.subTest(predicate=predicate), tempfile.TemporaryDirectory() as directory:
                w = Workspace(directory)
                w.release("v5.3.0", schema={"if": {"properties": {"tests": {"properties": {"integration": predicate}}}},
                                            "else": {"properties": {"enabled": {"default": False}}}})
                self.assertEqual(w.produce()["result"], "candidate")
                candidate = w.value()
                def change(store):
                    path = "rendered/Hexalith.Alpha/.github/hexalith-ci.json"
                    config = json.loads(store.blob(candidate["candidate"], path))
                    config["enabled"] = 0
                    oid = store.run("hash-object", "-w", "--stdin", data=json.dumps(config).encode()).decode().strip()
                    store.run("update-index", "--cacheinfo", "100644", oid, path)
                self.assert_refused(w, w.mutate(candidate, change), reason)

    def test_artifact_id_name_digest_run_and_attempt_binding(self):
        w = self.workspace()
        api = mock.Mock()
        digest = "sha256:" + "a" * 64
        metadata = {"id": 9, "name": "hexalith-nightly-bump-1", "digest": digest,
                    "workflow_run": {"id": 101, "head_sha": "a" * 40}}
        api.pages.return_value = [metadata]
        api.artifact_member.return_value = w.value()
        self.assertEqual(writer.artifact(api, IDENTITY, "9", digest, "inert"), w.value())
        for mutate in (lambda item: item.update(id=10), lambda item: item.update(name="hexalith-nightly-bump-2"),
                       lambda item: item.update(digest="sha256:" + "b" * 64),
                       lambda item: item["workflow_run"].update(id=102),
                       lambda item: item["workflow_run"].update(head_sha="b" * 40)):
            item = deepcopy(metadata)
            mutate(item)
            api.pages.return_value = [item]
            with self.assertRaises(rt.NightlyError):
                writer.artifact(api, IDENTITY, "9", digest, "inert")
        api.pages.return_value = [metadata, metadata]
        with self.assertRaisesRegex(rt.NightlyError, "duplicated"):
            writer.artifact(api, IDENTITY, "9", digest, "inert")

    def test_qualification_inert_ref_remote_tree_and_cleanup(self):
        w = self.workspace()
        before = git(w.cicd, "rev-parse", "HEAD")
        with mock.patch.object(rt, "Git", FixtureGit):
            report = writer.qualify(w.transport, w.directory, IDENTITY, "inert")
        self.assertEqual(report["result"], "qualified", report)
        self.assertEqual(report["candidate"], report["remoteSha"])
        self.assertEqual(report["tree"], report["remoteTree"])
        self.assertTrue(report["cleaned"])
        self.assertEqual(git(w.cicd, "rev-parse", "HEAD"), before)
        self.assertEqual(git(w.cicd, "for-each-ref", "--format=%(refname)", "refs/heads/nightly-bump-probe-"), "")
        self.assertEqual(w.transport.api.dispatched, 0)

    def test_generic_auth_failure_is_not_workflow_permission_rejection(self):
        self.assertFalse(writer.re_permission_rejection("HTTP 403 Resource not accessible by integration"))
        self.assertFalse(writer.re_permission_rejection("transport timeout"))
        self.assertTrue(writer.re_permission_rejection("refusing to allow a GitHub App to create or update workflow without workflows permission"))


if __name__ == "__main__":
    unittest.main()
