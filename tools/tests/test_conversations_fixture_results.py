"""Qualify the product fixture's native result reader outside module automation."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "references/Hexalith.Conversations/tests/compatibility/MinimalModule"
sys.path.insert(0, str(FIXTURE))
SPEC = importlib.util.spec_from_file_location("conversations_compatibility_runner", FIXTURE / "run_compatibility.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def successful_records():
    result = [{"$type": "discovery-complete", "TestCasesToRun": 7},
              {"$type": "test-assembly-starting", "AssemblyUniqueID": "assembly"}]
    for index, name in enumerate(sorted(RUNNER.expected_tests())):
        common = {"AssemblyUniqueID": "assembly", "TestUniqueID": str(index)}
        result.extend(({"$type": "test-starting", "TestDisplayName": name, **common},
                       {"$type": "test-passed", **common}, {"$type": "test-finished", **common}))
    result.append({"$type": "test-assembly-finished", "AssemblyUniqueID": "assembly", "TestsTotal": 7,
                   "TestsFailed": 0, "TestsSkipped": 0, "TestsNotRun": 0})
    return result


class NativeResultsTests(unittest.TestCase):
    def test_exact_seven_distinct_passes(self):
        RUNNER.verify_records(successful_records())

    def test_missing_duplicate_and_unexpected_results_are_rejected(self):
        original = successful_records()
        candidates = [original[:3] + original[6:], original[:4] + [original[3]] + original[4:]]
        unexpected = copy.deepcopy(original)
        unexpected[2]["TestDisplayName"] = "Unexpected.Test"
        candidates.append(unexpected)
        for records in candidates:
            with self.subTest(records=records), self.assertRaises(ValueError):
                RUNNER.verify_records(records)

    def test_failed_skipped_not_run_and_cleanup_errors_are_rejected(self):
        for kind in ("test-failed", "test-skipped", "test-not-run", "error", "fatal-error", "test-assembly-cleanup-failure"):
            records = successful_records()
            records.insert(4, {"$type": kind})
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                RUNNER.verify_records(records)

    def test_discovery_and_assembly_counters_are_bound(self):
        for key, value in (("TestsTotal", 6), ("TestsFailed", 1), ("TestsSkipped", 1), ("TestsNotRun", 1), ("TestsTotal", True)):
            records = successful_records()
            records[-1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                RUNNER.verify_records(records)
        for index in (0, 1, -1):
            records = successful_records()
            del records[index]
            with self.subTest(index=index), self.assertRaises(ValueError):
                RUNNER.verify_records(records)


if __name__ == "__main__":
    unittest.main()
