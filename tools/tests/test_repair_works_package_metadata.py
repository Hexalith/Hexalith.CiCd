"""Real-Git refusal and preservation checks for the bounded owner materializer."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "repair_works_package_metadata.py"
SPEC = importlib.util.spec_from_file_location("works_auth_repair", SOURCE)
REPAIR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPAIR)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


class OwnerRepairTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="works-auth-owner-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.builds, self.module = self.root / "builds", self.root / "module"
        for directory in (self.builds, self.module):
            directory.mkdir()
            git(directory, "init", "--quiet")
            git(directory, "config", "user.name", "Synthetic fixture")
            git(directory, "config", "user.email", "fixture@example.invalid")
        for path, count in REPAIR.BUILD_PATHS.items():
            target = self.builds / path
            target.parent.mkdir(parents=True, exist_ok=True)
            indent = "          " if path.startswith(".github/") else "        "
            target.write_text((indent + "PACKAGE_PREPARE_SCRIPT: ${{ inputs.package-prepare-script }}\n") * count)
        git(self.builds, "add", ".")
        git(self.builds, "commit", "--quiet", "-m", "test: frozen synthetic source")
        base = git(self.builds, "rev-parse", "HEAD")
        self.base_patch = patch.object(REPAIR, "BASE", base)
        self.base_patch.start()
        self.addCleanup(self.base_patch.stop)
        owner_patch = patch.object(REPAIR, "owner_identity", return_value={"owner_source": "f" * 40,
            "materializer_sha256": "0" * 64})
        owner_patch.start()
        self.addCleanup(owner_patch.stop)
        for path in REPAIR.BUILD_PATHS:
            target = self.builds / path
            indent = "          " if path.startswith(".github/") else "        "
            target.write_text(target.read_text().replace("\n", "\n" + indent + "GH_TOKEN: ${{ github.token }}\n"))
        git(self.builds, "add", ".")
        git(self.builds, "commit", "--quiet", "-m", "fix: synthetic compatibility source")
        self.revision = git(self.builds, "rev-parse", "HEAD")
        for path, count in REPAIR.WORKS_PATHS.items():
            target = self.module / path
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = ("execution=" + base + "\n") * count
            if path.endswith("/ci.yml"):
                raw += ("      - name: Prepare verified published Builds artifacts\n"
                        "        run: bash scripts/prepare-platform-builds.sh\n")
            target.write_text(raw)
        (self.module / "user.txt").write_text("foreign committed content\n")
        git(self.module, "add", ".")
        git(self.module, "commit", "--quiet", "-m", "test: synthetic Works source")
        git(self.module, "remote", "add", "origin", "https://github.com/Hexalith/Hexalith.Works.git")
        self.directory = self.root / "proposal"
        self.directory.mkdir()

    def prepare(self):
        manifest, raw, changes = REPAIR.proposal(self.module, self.builds, self.revision)
        (self.directory / "works-package-metadata-auth.json").write_text(json.dumps(manifest))
        (self.directory / "works-package-metadata-auth.patch").write_bytes(raw)
        return manifest, raw, changes

    def test_exact_application_preserves_foreign_edits_index_and_head(self):
        manifest, _, changes = self.prepare()
        head = git(self.module, "rev-parse", "HEAD")
        index = git(self.module, "write-tree")
        (self.module / "user.txt").write_text("foreign pending edit\n")
        (self.module / "new-user.txt").write_text("foreign untracked content\n")
        REPAIR.apply(self.module, self.builds, self.revision, self.directory)
        self.assertEqual(head, git(self.module, "rev-parse", "HEAD"))
        self.assertEqual(index, git(self.module, "write-tree"))
        self.assertEqual("foreign pending edit\n", (self.module / "user.txt").read_text())
        self.assertEqual("foreign untracked content\n", (self.module / "new-user.txt").read_text())
        for path, expected in changes.items():
            self.assertEqual(expected, (self.module / path).read_bytes())
        git(self.module, "add", "--", *changes)
        self.assertEqual(manifest["result_tree"], git(self.module, "write-tree"))

    def test_dirty_workflow_refuses_before_any_target_write(self):
        self.prepare()
        path = self.module / ".github/workflows/release.yml"
        path.write_text(path.read_text() + "foreign edit\n")
        before = {p: (self.module / p).read_bytes() for p in REPAIR.WORKS_PATHS}
        with self.assertRaisesRegex(ValueError, "Preserve existing workflow edits"):
            REPAIR.apply(self.module, self.builds, self.revision, self.directory)
        self.assertEqual(before, {p: (self.module / p).read_bytes() for p in before})

    def test_tampered_patch_refuses(self):
        self.prepare()
        (self.directory / "works-package-metadata-auth.patch").write_text("changed")
        with self.assertRaisesRegex(ValueError, "patch identity changed"):
            REPAIR.apply(self.module, self.builds, self.revision, self.directory)

    def test_new_module_head_requires_new_proposal(self):
        self.prepare()
        (self.module / "user.txt").write_text("new committed content")
        git(self.module, "add", "user.txt")
        git(self.module, "commit", "--quiet", "-m", "test: advanced source")
        with self.assertRaisesRegex(ValueError, "exact source or patch identity changed"):
            REPAIR.apply(self.module, self.builds, self.revision, self.directory)

    def test_unreviewed_builds_source_refuses(self):
        (self.builds / "extra.txt").write_text("unrelated change")
        git(self.builds, "add", "extra.txt")
        git(self.builds, "commit", "--quiet", "-m", "test: changed source")
        with self.assertRaisesRegex(ValueError, "single compatibility commit"):
            REPAIR.proposal(self.module, self.builds, git(self.builds, "rev-parse", "HEAD"))

    def test_adopted_module_refuses(self):
        (self.module / ".github/hexalith-ci.json").write_text("{}")
        git(self.module, "add", ".github/hexalith-ci.json")
        git(self.module, "commit", "--quiet", "-m", "test: adopted source")
        with self.assertRaisesRegex(ValueError, "normal delivered perimeter"):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
