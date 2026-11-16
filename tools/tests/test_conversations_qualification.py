"""Refusal and canonical-mask controls for the explicit local qualification path."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
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


if __name__ == "__main__":
    unittest.main()
