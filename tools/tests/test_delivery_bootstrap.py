#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Selector entrypoint qualification against disposable committed objects."""
from pathlib import Path
import json
import tempfile
import unittest

from delivery_support import Workspace, git


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.w = Workspace(Path(temporary.name) / "workspace")

    def test_valid_candidate_selects_exact_tools_and_outputs_only_registry(self):
        w = self.w
        self.assertEqual(w.select(), 0)
        state = json.loads((w.directory / "state.json").read_bytes())
        self.assertTrue(state["ready"])
        self.assertEqual(state["source"], w.sha)
        self.assertEqual(state["slots"], ["Hexalith.Alpha"])
        self.assertEqual((w.directory / "selected/tools/deliver.py").read_bytes(), (w.candidate / "tools/deliver.py").read_bytes())
        self.assertIn("slot_01=Hexalith.Alpha\n", w.outputs.read_text())
        self.assertIn("slot_02=\n", w.outputs.read_text())

    def test_missing_malformed_and_duplicate_verdict_fail_closed(self):
        w = self.w
        w.ref("Hexalith.Alpha")
        for raw in ("", "{", '{"global":true,"global":false,"modules":[]}',
                    '{"global":1,"modules":[]}', '{"global":true,"modules":[1]}',
                    '{"global":true,"modules":[],"unknown":1}'):
            with self.subTest(raw=raw):
                self.assertEqual(w.select(DELIVERY_VERDICT=raw), 0)
                self.assertFalse(w.report()["global"])
                self.assertEqual(w.report()["tools_source_sha"], w.accepted)
                self.assertTrue(w.report()["failed"])

    def test_no_accepted_source_never_falls_back_to_candidate(self):
        w = self.w
        w.select({"global": False, "modules": []})
        self.assertIsNone(w.report()["tools_source_sha"])
        self.assertFalse((w.directory / "selected").exists())
        result = w.call("delivery_bootstrap.py", ["finalize"])
        self.assertEqual(result, 1)
        self.assertIn("trusted controller unavailable", w.report()["failures"])

    def test_missing_accepted_controller_keeps_zero_write_failure_report(self):
        w = self.w
        (w.candidate / "tools/deliver.py").unlink()
        w.commit()
        w.ref("Hexalith.Alpha", w.sha)
        w.select({"global": False, "modules": []})
        self.assertFalse(json.loads((w.directory / "state.json").read_bytes())["ready"])
        self.assertEqual(w.call("delivery_bootstrap.py", ["finalize"]), 1)
        self.assertIn("missing regular committed source", " ".join(w.report()["failures"]))

    def test_nonancestor_ref_is_reported_and_excluded(self):
        w = self.w
        tree = git(w.remote, "rev-parse", "main^{tree}")
        unrelated = git(w.remote, "commit-tree", tree, data=b"Not on main\n")
        w.ref("Hexalith.Alpha", unrelated)
        w.select({"global": False, "modules": []})
        row = w.report()["modules"][0]
        self.assertEqual(row["application"], "failed")
        self.assertIn(unrelated, " ".join(row["reasons"]))
        self.assertIsNone(w.report()["tools_source_sha"])

    def test_newest_accepted_target_selected_by_main_topology(self):
        w = self.w
        w.ref("Hexalith.Alpha")
        (w.candidate / "README.fixture").write_text("next\n")
        w.commit()
        git(w.remote, "update-ref", "refs/heads/delivered/Hexalith.Beta", w.sha)
        w.select({"global": False, "modules": []})
        self.assertEqual(w.report()["tools_source_sha"], w.sha)
        self.assertEqual(json.loads((w.directory / "state.json").read_bytes())["slots"], ["Hexalith.Alpha", "Hexalith.Beta"])

    def test_overflow_fails_before_slots_or_writes(self):
        w = self.w
        for index in range(18):
            (w.candidate / "setup" / f"Fixture{index}.yml").write_text("{}\n")
        w.commit()
        w.select({"global": True, "modules": []})
        self.assertIn("exceeds 17", " ".join(w.report()["failures"]))
        self.assertEqual(json.loads((w.directory / "state.json").read_bytes())["slots"], [])
        self.assertEqual(git(w.remote, "for-each-ref", "refs/heads/delivered/"), "")

    def test_outside_registry_names_and_builds_are_rejected(self):
        for value in ("Outside", "Hexalith.Builds"):
            self.w.select({"global": True, "modules": [value]})
            self.assertTrue(self.w.report()["failed"])
            self.assertEqual(json.loads((self.w.directory / "state.json").read_bytes())["slots"], [])

    def test_mint_permit_reserves_a_minute_before_soft_deadline(self):
        w = self.w
        w.select()
        self.assertEqual(w.call("delivery_bootstrap.py", ["permit", "--slot", "1"]), 0)
        self.assertTrue(w.outputs.read_text().endswith("active=true\n"))
        state_path = w.directory / "state.json"
        state = json.loads(state_path.read_bytes())
        state["started"] -= 35 * 60
        state_path.write_text(json.dumps(state))
        self.assertEqual(w.call("delivery_bootstrap.py", ["permit", "--slot", "1"]), 0)
        self.assertTrue(w.outputs.read_text().endswith("active=false\n"))


if __name__ == "__main__":
    unittest.main()
