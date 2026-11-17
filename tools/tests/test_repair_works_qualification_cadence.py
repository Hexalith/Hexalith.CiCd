"""Real-Git owner proposal refusal, complete-job preservation and local application."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "repair_works_qualification_cadence.py"
SPEC = importlib.util.spec_from_file_location("works_cadence_repair", SOURCE)
REPAIR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPAIR)
REAL_OWNER_IDENTITY = REPAIR.owner_identity


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


class OwnerCadenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="works-cadence-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.module = self.root / "module"
        self.module.mkdir()
        git(self.module, "init", "--quiet")
        git(self.module, "config", "user.name", "Synthetic fixture")
        git(self.module, "config", "user.email", "fixture@example.invalid")
        self.parity = (b"  platform-parity:\n    name: Complete parity\n    timeout-minutes: 180\n"
                       b"    steps:\n      - uses: owner/action@" + b"a" * 40 + b"\n"
                       b"      - run: bash scripts/verify-platform-parity-ci.sh\n\n")
        self.ci = (b"name: CI\non: [push, pull_request]\njobs:\n  platform-toolchain:\n"
                   b"    name: Preserve toolchain\n\n" + self.parity +
                   b"  ci:\n    uses: owner/build@" + b"b" * 40 + b"\n\n"
                   b"  scripts-lint:\n    name: Preserve unrelated job\n")
        self.release = (b"name: Release\non: workflow_dispatch\njobs:\n  verify-source:\n"
                        b"    steps:\n      - name: Require current main with successful exact-source push CI\n"
                        b"        run: bash scripts/validate-release-source.sh\n\n  release:\n"
                        b"    needs: verify-source\n    environment: production\n"
                        b"    permissions:\n      id-token: write\n    steps:\n"
                        b"      - uses: owner/publish@" + b"c" * 40 + b"\n")
        for path, raw in ((REPAIR.CI, self.ci), (REPAIR.RELEASE, self.release)):
            target = self.module / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        (self.module / "user.txt").write_text("foreign committed content\n")
        git(self.module, "add", ".")
        git(self.module, "commit", "--quiet", "-m", "test: synthetic Works source")
        git(self.module, "remote", "add", "origin", "https://github.com/Hexalith/Hexalith.Works.git")
        frozen = patch.object(REPAIR, "BASE", git(self.module, "rev-parse", "HEAD"))
        frozen.start()
        self.addCleanup(frozen.stop)
        authority = patch.object(REPAIR, "owner_identity", return_value={"owner_source": "f" * 40,
            "materializer_sha256": "0" * 64, "helper_sha256": "1" * 64})
        authority.start()
        self.addCleanup(authority.stop)
        self.directory = self.root / "proposal"
        self.directory.mkdir()

    def prepare(self):
        manifest, raw, changes = REPAIR.proposal(self.module)
        (self.directory / (REPAIR.STEM + ".json")).write_text(json.dumps(manifest))
        (self.directory / (REPAIR.STEM + ".patch")).write_bytes(raw)
        return manifest, raw, changes

    def contents(self):
        return {path: (self.module / path).read_bytes() for path in (REPAIR.CI, REPAIR.RELEASE)}

    def test_exact_apply_moves_the_entire_parity_job_and_preserves_foreign_edits_index_and_head(self):
        manifest, _, changes = self.prepare()
        self.assertEqual(changes[REPAIR.CI], self.ci.replace(self.parity, b""))
        self.assertIn(self.parity, changes[REPAIR.QUALIFICATION])
        self.assertIn(b"schedule:", changes[REPAIR.QUALIFICATION])
        self.assertIn(b"workflow_dispatch:", changes[REPAIR.QUALIFICATION])
        self.assertNotIn(b"pull_request", changes[REPAIR.QUALIFICATION])
        self.assertEqual(changes[REPAIR.RELEASE], self.release.replace(
            b"Require current main with successful exact-source push CI",
            b"Require current main with exact-source CI and complete qualification"))
        head, index = git(self.module, "rev-parse", "HEAD"), git(self.module, "write-tree")
        (self.module / "user.txt").write_text("foreign pending edit\n")
        (self.module / "new-user.txt").write_text("foreign untracked content\n")
        REPAIR.apply(self.module, self.directory)
        self.assertEqual(head, git(self.module, "rev-parse", "HEAD"))
        self.assertEqual(index, git(self.module, "write-tree"))
        self.assertEqual("foreign pending edit\n", (self.module / "user.txt").read_text())
        self.assertEqual("foreign untracked content\n", (self.module / "new-user.txt").read_text())
        for path, expected in changes.items():
            self.assertEqual(expected, (self.module / path).read_bytes())
        git(self.module, "add", "--", *changes)
        self.assertEqual(manifest["result_tree"], git(self.module, "write-tree"))
        self.assertTrue((self.directory / (REPAIR.STEM + "-applied.json")).is_file())

    def test_foreign_owner_origin_refuses_before_workflow_writes(self):
        owner = self.root / "owner"
        tools = owner / "tools"
        tools.mkdir(parents=True)
        materializer = tools / SOURCE.name
        materializer.write_bytes(SOURCE.read_bytes())
        helper = SOURCE.with_name("repair_works_package_metadata.py")
        (tools / helper.name).write_bytes(helper.read_bytes())
        git(owner, "init", "--quiet")
        git(owner, "config", "user.name", "Synthetic fixture")
        git(owner, "config", "user.email", "fixture@example.invalid")
        git(owner, "add", ".")
        git(owner, "commit", "--quiet", "-m", "test: synthetic CiCd owner")
        git(owner, "remote", "add", "origin", "https://github.com/Hexalith/Hexalith.CiCd.git")
        with patch.object(REPAIR, "owner_identity", REAL_OWNER_IDENTITY), \
                patch.object(REPAIR, "OWNER", owner), patch.object(REPAIR, "__file__", str(materializer)):
            self.prepare()
            git(owner, "remote", "set-url", "origin", "https://example.invalid/Hexalith.CiCd.git")
            before = self.contents()
            with self.assertRaisesRegex(ValueError, "official CiCd owner checkout"):
                REPAIR.apply(self.module, self.directory)
            self.assertEqual(before, self.contents())
            self.assertFalse((self.module / REPAIR.QUALIFICATION).exists())
            self.assertFalse((self.directory / (REPAIR.STEM + "-applied.json")).exists())

    def test_dirty_or_staged_workflow_refuses_before_writes(self):
        self.prepare()
        target = self.module / REPAIR.RELEASE
        target.write_bytes(target.read_bytes() + b"foreign edit\n")
        before = self.contents()
        with self.assertRaisesRegex(ValueError, "Preserve existing workflow edits"):
            REPAIR.apply(self.module, self.directory)
        self.assertEqual(before, self.contents())
        git(self.module, "add", REPAIR.RELEASE)
        with self.assertRaisesRegex(ValueError, "Preserve staged workflow edits"):
            REPAIR.apply(self.module, self.directory)
        self.assertFalse((self.module / REPAIR.QUALIFICATION).exists())

    def test_existing_untracked_qualification_is_preserved(self):
        self.prepare()
        before = self.contents()
        target = self.module / REPAIR.QUALIFICATION
        target.write_text("foreign qualification\n")
        with self.assertRaisesRegex(ValueError, "existing qualification"):
            REPAIR.apply(self.module, self.directory)
        self.assertEqual(before, self.contents())
        self.assertEqual("foreign qualification\n", target.read_text())

    def test_hard_link_and_executable_mode_refuse_without_writes(self):
        self.prepare()
        before = self.contents()
        target = self.module / REPAIR.RELEASE
        alias = self.module / "foreign-backup.txt"
        os.link(target, alias)
        with self.assertRaisesRegex(ValueError, "hard-linked"):
            REPAIR.apply(self.module, self.directory)
        self.assertEqual(before, self.contents())
        self.assertEqual(before[REPAIR.RELEASE], alias.read_bytes())
        alias.unlink()
        target.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "file modes"):
            REPAIR.apply(self.module, self.directory)
        self.assertEqual(before, self.contents())

    def test_symlink_target_refuses_without_writing_its_foreign_referent(self):
        self.prepare()
        target = self.module / REPAIR.RELEASE
        foreign = self.module / "foreign-release.yml"
        target.rename(foreign)
        target.symlink_to(foreign)
        before = foreign.read_bytes()
        with self.assertRaisesRegex(ValueError, "symbolic links"):
            REPAIR.apply(self.module, self.directory)
        self.assertEqual(before, foreign.read_bytes())
        self.assertFalse((self.module / REPAIR.QUALIFICATION).exists())

    def test_patch_or_owner_identity_drift_refuses(self):
        self.prepare()
        before = self.contents()
        with patch.object(REPAIR, "owner_identity", return_value={"owner_source": "e" * 40}):
            with self.assertRaisesRegex(ValueError, "identity changed"):
                REPAIR.apply(self.module, self.directory)
        (self.directory / (REPAIR.STEM + ".patch")).write_text("changed")
        with self.assertRaisesRegex(ValueError, "identity changed"):
            REPAIR.apply(self.module, self.directory)
        self.assertEqual(before, self.contents())

    def test_source_movement_after_prepare_requires_a_new_source_bound_proposal(self):
        self.prepare()
        (self.module / "user.txt").write_text("new committed content")
        git(self.module, "add", "user.txt")
        git(self.module, "commit", "--quiet", "-m", "test: advance source")
        with self.assertRaisesRegex(ValueError, "identity changed"):
            REPAIR.apply(self.module, self.directory)

    def test_unrelated_descendant_can_prepare_but_changed_owned_workflows_refuse(self):
        (self.module / "user.txt").write_text("unrelated committed content")
        git(self.module, "add", "user.txt")
        git(self.module, "commit", "--quiet", "-m", "test: unrelated descendant")
        manifest, _, _ = self.prepare()
        self.assertEqual(manifest["base_commit"], git(self.module, "rev-parse", "HEAD"))
        target = self.module / REPAIR.CI
        target.write_bytes(target.read_bytes() + b"foreign policy change\n")
        git(self.module, "add", REPAIR.CI)
        git(self.module, "commit", "--quiet", "-m", "test: changed policy")
        with self.assertRaisesRegex(ValueError, "approved Works baseline"):
            self.prepare()

    def test_adopted_or_foreign_repository_refuses(self):
        git(self.module, "remote", "set-url", "origin", "https://example.invalid/Works.git")
        with self.assertRaisesRegex(ValueError, "official Works"):
            self.prepare()
        git(self.module, "remote", "set-url", "origin", "https://github.com/Hexalith/Hexalith.Works.git")
        (self.module / ".github/hexalith-ci.json").write_text("{}")
        git(self.module, "add", ".github/hexalith-ci.json")
        git(self.module, "commit", "--quiet", "-m", "test: adopted source")
        with patch.object(REPAIR, "BASE", git(self.module, "rev-parse", "HEAD")):
            with self.assertRaisesRegex(ValueError, "normal delivered perimeter"):
                self.prepare()


if __name__ == "__main__":
    unittest.main()
