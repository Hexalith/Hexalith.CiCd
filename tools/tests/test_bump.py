#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Actual producer/Git selection, stable UTC nights and failure boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from bump_support import br, rt, IDENTITY, Workspace, FixtureGit, git


class BumpTests(unittest.TestCase):
    def workspace(self):
        temporary = tempfile.TemporaryDirectory(prefix="bump-test-")
        self.addCleanup(temporary.cleanup)
        return Workspace(temporary.name)

    def test_numeric_newest_same_major_excludes_skip(self):
        w = self.workspace()
        w.release("v5.9.0")
        selected = w.release("v5.10.0", annotated=True)
        w.release("v6.0.0")
        report = w.produce()
        self.assertEqual(report["result"], "candidate", report)
        self.assertEqual(w.value()["new"], selected)
        self.assertEqual(git(w.cicd, "rev-parse", "HEAD"), w.base)

    def test_live_main_newer_than_scheduler_and_committed_gate(self):
        w = self.workspace()
        old = w.base
        (w.cicd / "product.txt").write_text("new live tip\n")
        live = w.commit()
        seen = []
        def gate(project):
            seen.append(git(project, "show", "HEAD:builds-version"))
            self.assertEqual(git(project, "rev-parse", "HEAD^"), live)
            self.assertEqual(git(project, "show", "HEAD:product.txt"), "new live tip")
            return True
        report = w.produce(check=gate)
        self.assertEqual(report["result"], "candidate", report)
        self.assertEqual(report["base"], live)
        self.assertNotEqual(old, live)
        self.assertEqual(seen, ["v5.2.0"])

    def test_failed_gate_never_exposes_candidate(self):
        w = self.workspace()
        report = w.produce(check=lambda project: False)
        self.assertEqual(report["result"], "failed")
        self.assertFalse((w.directory / "candidate.json").exists())
        self.assertEqual(report["candidate"], "")

    def test_skip_rollback_no_change_and_invalid_line(self):
        w = self.workspace()
        (w.cicd / "builds-skip").write_text("v5.2.0\n")
        w.commit()
        report = w.produce()
        self.assertEqual(report["result"], "no-change", report)
        self.assertFalse((w.directory / "candidate.json").exists())
        (w.cicd / "builds-skip").write_text("\nv5.2\n")
        w.commit()
        report = w.produce()
        self.assertEqual(report["result"], "failed")
        self.assertIn("builds-skip:2", report["reason"])

    def test_historical_missing_skip_is_empty(self):
        w = self.workspace()
        (w.cicd / "builds-skip").unlink()
        w.commit()
        self.assertEqual(w.produce()["result"], "candidate")

    def test_same_night_rerun_and_next_night(self):
        w = self.workspace()
        self.assertEqual(w.produce()["result"], "candidate")
        pushed = w.push()
        self.assertEqual(pushed["result"], "pushed", pushed)
        # Synchronize the disposable worktree with the pushed branch only.
        git(w.cicd, "reset", "--hard", "HEAD")
        w.release("v5.3.0")
        rerun = deepcopy(IDENTITY)
        rerun["attempt"] = 2
        self.assertEqual(w.produce(identity=rerun)["result"], "no-change")
        next_night = deepcopy(IDENTITY)
        next_night["night"] = "2026-11-15"
        report = w.produce(identity=next_night)
        self.assertEqual(report["result"], "candidate", report)
        self.assertEqual(w.value()["new"]["tag"], "v5.3.0")

    def test_no_acceptable_release_and_unreadable_listing_fail(self):
        w = self.workspace()
        for row in w.releases:
            row["immutable"] = False
        self.assertEqual(w.produce()["result"], "failed")
        with mock.patch.object(w.transport.api, "pages", side_effect=rt.NightlyError("incomplete inventory")):
            self.assertIn("incomplete inventory", w.produce()["reason"])

    def test_remote_local_tag_mismatch_fails(self):
        w = self.workspace()
        original = w.transport.api.get
        def mismatch(path, token=None):
            value = original(path, token)
            if path.endswith("tags/v5.2.0"):
                value["object"]["sha"] = w.old["object"]
            return value
        with mock.patch.object(w.transport.api, "get", side_effect=mismatch):
            self.assertIn("remote/local", w.produce()["reason"])

    def test_night_identity_uses_creation_date_across_midnight(self):
        env = {"GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd", "GITHUB_REF": "refs/heads/main",
               "GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "101", "GITHUB_RUN_ATTEMPT": "2"}
        document = {"id": 101, "run_attempt": 2, "head_sha": "a" * 40, "head_branch": "main",
                    "path": ".github/workflows/nightly.yml", "event": "schedule",
                    "repository": {"full_name": "Hexalith/Hexalith.CiCd"}, "created_at": "2026-11-14T23:59:59Z"}
        api = mock.Mock()
        api.get.return_value = document
        self.assertEqual(br.identity(env, api)["night"], "2026-11-14")


if __name__ == "__main__":
    unittest.main()
