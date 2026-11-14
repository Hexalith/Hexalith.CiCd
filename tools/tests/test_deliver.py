#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Executed controller tests with released perimeter code and real remotes."""
from pathlib import Path
import json
import tempfile
import unittest

from delivery_support import Workspace, git, RELEASE


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ws = Workspace(Path(self.temp.name) / "workspace", ("Hexalith.Alpha", "Hexalith.Beta"))

    def test_all_entry_kinds_foreign_content_modes_and_idempotence(self):
        w = self.ws
        self.assertEqual(w.deliver(), 0, w.report())
        for row in w.report()["modules"]:
            self.assertEqual(row["advancement"], "advanced")
            self.assertEqual(row["application"], "pushed")
            remote = Path(w.remotes[row["repository"]])
            self.assertEqual(git(w.remote, "rev-parse", "refs/heads/delivered/" + row["repository"]), w.sha)
            self.assertEqual(git(remote, "show", "main:product.txt"), "foreign product")
            self.assertIn("foreign instructions", git(remote, "show", "main:AGENTS.md"))
            self.assertIn("owned instructions", git(remote, "show", "main:AGENTS.md"))
            settings = json.loads(git(remote, "show", "main:.claude/settings.json"))
            self.assertEqual(settings["permissions"]["deny"], ["foreign", "owned"])
            self.assertEqual(settings["permissions"]["allow"], ["foreign"])
            self.assertEqual(git(remote, "show", "main:.husky/commit-msg"), "keep foreign")
            package = json.loads(git(remote, "show", "main:package.json"))
            self.assertEqual(package["scripts"], {"keep": "echo ok"})
            self.assertEqual(package["devDependencies"], {"foreign": "2"})
            self.assertIn('submodule "foreign"', git(remote, "show", "main:.gitmodules"))
            self.assertEqual(git(remote, "ls-tree", "main", "references/Hexalith.Builds").split()[2], RELEASE)
            self.assertTrue(git(remote, "ls-tree", "main", ".github/workflows/ci.yml").startswith("100755"))
            for removed in (".releaserc.json", "Directory.Build.rsp", ".github/workflows/old.yml"):
                self.assertEqual(git(remote, "ls-tree", "main", removed), "")
            self.assertEqual(git(remote, "rev-list", "--count", "main"), "2")
        before = {r: git(Path(p), "rev-parse", "main") for r, p in w.remotes.items()}
        self.assertEqual(w.deliver(), 0, w.report())
        self.assertEqual([r["application"] for r in w.report()["modules"]], ["unchanged", "unchanged"])
        self.assertEqual(before, {r: git(Path(p), "rev-parse", "main") for r, p in w.remotes.items()})
        report = (w.directory / "report/delivery.json").read_bytes()
        self.assertNotIn(b"inert-", report)
        self.assertNotIn(b"inert-", (w.directory / "state.json").read_bytes())

    def test_rejected_module_repairs_old_render_healthy_sibling_advances(self):
        w = self.ws
        w.ref("Hexalith.Alpha")
        (w.candidate / "rendered/Hexalith.Alpha/.github/hexalith-ci.json").write_text('{"rejected":true}\n')
        w.commit()
        w.config["fail_app"] = ["Hexalith.Alpha"]
        self.assertEqual(w.deliver(), 1)
        alpha, beta = w.report()["modules"]
        self.assertEqual(alpha["advancement"], "skipped")
        self.assertEqual(alpha["application"], "pushed")
        self.assertEqual(git(w.remote, "rev-parse", "refs/heads/delivered/Hexalith.Alpha"), w.accepted)
        self.assertEqual(git(Path(w.remotes["Hexalith.Alpha"]), "show", "main:.github/hexalith-ci.json"), '{"accepted":true}')
        self.assertEqual(beta["advancement"], "advanced")

    def test_failed_global_repairs_removed_setup_and_no_candidate_execution(self):
        w = self.ws
        w.ref("Hexalith.Alpha")
        (w.candidate / "setup/Hexalith.Alpha.yml").unlink()
        marker = w.root / "EXECUTED"
        (w.candidate / "tools/deliver.py").write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
        w.commit()
        w.select({"global": False, "modules": []})
        self.assertEqual(w.report()["tools_source_sha"], w.accepted)
        self.assertEqual(w.operation("initialize"), 0)
        for slot in (1, 2):
            self.assertEqual(w.operation("module", slot), 0)
        self.assertEqual(w.operation("finalize"), 1)
        self.assertFalse(marker.exists())
        self.assertEqual(w.report()["modules"][0]["application"], "pushed")
        self.assertEqual(w.report()["modules"][1]["application"], "no-ref")

    def test_race_retry_parentage_and_exhaustion(self):
        w = self.ws
        w.config["races"] = {"Hexalith.Alpha": 1, "Hexalith.Beta": 4}
        self.assertEqual(w.deliver(), 1)
        alpha, beta = w.report()["modules"]
        self.assertEqual((alpha["application"], alpha["retries"]), ("pushed", 1))
        remote = Path(w.remotes["Hexalith.Alpha"])
        self.assertEqual(git(remote, "show", "-s", "--format=%s", "main^"), "Concurrent product 0")
        self.assertEqual((beta["application"], beta["retries"]), ("failed", 3))
        self.assertEqual(git(Path(w.remotes["Hexalith.Beta"]), "show", "-s", "--format=%s", "main"), "Concurrent product 3")

    def test_mint_and_transport_failure_continue_siblings(self):
        w = self.ws
        w.select()
        w.operation("initialize", CICD_TOKEN="")
        w.operation("module", 1, MODULE_TOKEN="")
        w.operation("module", 2, CICD_TOKEN="")
        self.assertEqual(w.operation("finalize"), 1)
        alpha, beta = w.report()["modules"]
        self.assertEqual(alpha["application"], "failed")
        self.assertEqual(beta["advancement"], "failed")
        self.assertEqual(beta["application"], "no-ref")
        self.assertEqual(git(w.remote, "for-each-ref", "refs/heads/delivered/"), "")

    def test_bad_release_retains_ref_and_fails_before_module_write(self):
        w = self.ws
        w.ref("Hexalith.Alpha")
        w.config["bad_release"] = True
        self.assertEqual(w.deliver(), 1)
        self.assertEqual(git(w.remote, "rev-parse", "refs/heads/delivered/Hexalith.Alpha"), w.accepted)
        for remote in w.remotes.values():
            self.assertEqual(git(Path(remote), "rev-list", "--count", "main"), "1")

    def test_stale_candidate_and_ref_race_keep_newer_accepted_state(self):
        w = self.ws
        candidate = w.sha
        (w.candidate / "rendered/Hexalith.Alpha/.github/hexalith-ci.json").write_text('{"newer":true}\n')
        newer = w.commit()
        w.ref("Hexalith.Alpha", newer)
        w.sha = candidate
        w.config["ref_races"] = {"Hexalith.Beta": newer}
        self.assertEqual(w.deliver(), 0, w.report())
        for row in w.report()["modules"]:
            self.assertEqual(row["advancement"], "superseded")
            self.assertEqual(row["accepted_sha"], newer)
            self.assertIn("superseded by " + newer, row["reasons"])
        self.assertEqual(git(Path(w.remotes["Hexalith.Alpha"]), "show", "main:.github/hexalith-ci.json"), '{"newer":true}')

    def test_malformed_partial_is_repaired_and_transport_failure_is_not_retried(self):
        w = self.ws
        source = w.root / "Hexalith.Alpha-source"
        (source / ".claude/settings.json").write_text("{malformed partial\n")
        git(source, "add", ".")
        git(source, "commit", "--quiet", "-m", "Malformed partial")
        git(source, "push", "--quiet", w.remotes["Hexalith.Alpha"], "main")
        w.config["push_fail"] = ["Hexalith.Beta"]
        self.assertEqual(w.deliver(), 1)
        alpha, beta = w.report()["modules"]
        self.assertEqual(alpha["application"], "pushed")
        settings = json.loads(git(Path(w.remotes["Hexalith.Alpha"]), "show", "main:.claude/settings.json"))
        self.assertEqual(settings, {"permissions": {"deny": ["owned"]}})
        self.assertEqual((beta["application"], beta["retries"]), ("failed", 0))

    def test_hourly_history_error_and_staleness_still_repair(self):
        w = self.ws
        for module in w.modules:
            w.ref(module)
        prefix = "/repos/Hexalith/Hexalith.CiCd/actions/"
        w.config["api"][prefix + "workflows"] = {"error": "HTTP 403 inert-cicd-token"}
        self.assertEqual(w.deliver({"global": False, "modules": []}, GITHUB_EVENT_NAME="schedule"), 1)
        self.assertEqual(w.report()["freshness"]["status"], "failed")
        self.assertEqual([r["application"] for r in w.report()["modules"]], ["pushed", "pushed"])
        self.assertNotIn("inert-cicd-token", (w.directory / "report/delivery.json").read_text())
        w.config["api"][prefix + "workflows"] = [{"path": ".github/workflows/nightly.yml", "id": 1}]
        w.config["api"][prefix + "workflows/1/runs?branch=main&per_page=1&page=1"] = {
            "total_count": 1, "workflow_runs": [{"path": ".github/workflows/nightly.yml", "id": 2,
                "head_branch": "main", "created_at": "2020-01-01T00:00:00Z", "conclusion": "cancelled"}]}
        self.assertEqual(w.deliver({"global": False, "modules": []}, GITHUB_EVENT_NAME="schedule"), 1)
        self.assertEqual(w.report()["freshness"]["status"], "stale")
        self.assertEqual([r["application"] for r in w.report()["modules"]], ["unchanged", "unchanged"])

    def test_tag_source_mismatch_executes_nothing_and_writes_nothing(self):
        w = self.ws
        w.config["release"] = "f" * 40
        self.assertEqual(w.deliver(), 1)
        for remote in w.remotes.values():
            self.assertEqual(git(Path(remote), "rev-list", "--count", "main"), "1")
        self.assertEqual(git(w.remote, "for-each-ref", "refs/heads/delivered/"), "")

    def test_missing_perimeter_capability_rejects_before_tag_code_executes(self):
        w = self.ws
        marker = w.root / "EXECUTED"
        source = w.root / "incomplete-builds"
        source.mkdir()
        git(source, "init", "--quiet", "--initial-branch=main")
        (source / "Github/lib").mkdir(parents=True)
        (source / "Github/lib/perimeter.py").write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
        git(source, "add", ".")
        git(source, "commit", "--quiet", "-m", "Incomplete capability")
        revision = git(source, "rev-parse", "HEAD")
        git(source, "tag", "v5.1.0")
        remote = w.root / "incomplete-builds.git"
        git(w.root, "clone", "--quiet", "--bare", source, remote)
        w.config.update(builds=str(remote), release=revision)
        self.assertEqual(w.deliver(), 1)
        self.assertFalse(marker.exists())
        self.assertEqual(git(w.remote, "for-each-ref", "refs/heads/delivered/"), "")


if __name__ == "__main__":
    unittest.main()
