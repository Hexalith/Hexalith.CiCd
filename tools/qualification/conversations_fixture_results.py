#!/usr/bin/env python3
"""Qualify the exact cloned product fixture's native result reader."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


def successful_records(runner):
    result = [{"$type": "discovery-complete", "TestCasesToRun": 7},
              {"$type": "test-assembly-starting", "AssemblyUniqueID": "assembly"}]
    for index, name in enumerate(sorted(runner.expected_tests())):
        common = {"AssemblyUniqueID": "assembly", "TestUniqueID": str(index)}
        result.extend(({"$type": "test-starting", "TestDisplayName": name, **common},
                       {"$type": "test-passed", **common}, {"$type": "test-finished", **common}))
    result.append({"$type": "test-assembly-finished", "AssemblyUniqueID": "assembly", "TestsTotal": 7,
                   "TestsFailed": 0, "TestsSkipped": 0, "TestsNotRun": 0})
    return result


class NativeResultsTests(unittest.TestCase):
    def test_exact_seven_distinct_passes(self):
        self.runner.verify_records(successful_records(self.runner))

    def test_missing_duplicate_and_unexpected_results_are_rejected(self):
        original = successful_records(self.runner)
        candidates = [original[:3] + original[6:], original[:4] + [original[3]] + original[4:]]
        unexpected = copy.deepcopy(original)
        unexpected[2]["TestDisplayName"] = "Unexpected.Test"
        candidates.append(unexpected)
        for records in candidates:
            with self.subTest(records=records), self.assertRaises(ValueError):
                self.runner.verify_records(records)

    def test_failed_skipped_not_run_and_cleanup_errors_are_rejected(self):
        for kind in ("test-failed", "test-skipped", "test-not-run", "error", "fatal-error", "test-assembly-cleanup-failure"):
            records = successful_records(self.runner)
            records.insert(4, {"$type": kind})
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.runner.verify_records(records)

    def test_discovery_and_assembly_counters_are_bound(self):
        for key, value in (("TestsTotal", 6), ("TestsFailed", 1), ("TestsSkipped", 1), ("TestsNotRun", 1), ("TestsTotal", True)):
            records = successful_records(self.runner)
            records[-1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.runner.verify_records(records)
        for index in (0, 1, -1):
            records = successful_records(self.runner)
            del records[index]
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.runner.verify_records(records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-root", type=Path, required=True)
    args = parser.parse_args()
    fixture = args.module_root.resolve(strict=True) / "tests/compatibility/MinimalModule"
    sys.path.insert(0, str(fixture))
    spec = importlib.util.spec_from_file_location("conversations_compatibility_runner", fixture / "run_compatibility.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    NativeResultsTests.runner = runner
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeResultsTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped or result.testsRun != 4:
        return 1
    print(json.dumps({"result": "passed", "checks": result.testsRun}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
