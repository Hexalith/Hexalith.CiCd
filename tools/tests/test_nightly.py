#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Exercise real isolated nightly controllers and tagged release helpers."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from nightly_support import ROOT, Workspace, git, load, STAMP
from nightly_publish_cases import TestNightlyPublication

controller = load(ROOT / "tools/nightly.py", "_nightly_controller_tests")


class NightlyControllerTests(unittest.TestCase):
    def fixture(self, modules=("Hexalith.Alpha", "Hexalith.Beta")):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        workspace = Workspace(Path(temporary.name) / "workspace", modules)
        for repository in modules:
            workspace.ref(repository)
        self.assertEqual(workspace.call("initialize"), 0)
        return workspace

    def dispatch(self, workspace):
        self.assertEqual(workspace.call("barrier"), 0)
        self.assertEqual(workspace.call("select"), 0)
        for index, item in enumerate(workspace.state()["targets"], 1):
            if item["eligibility"] == "eligible":
                code = workspace.call("dispatch", slot=index)
                # A failed target step exits nonzero; continue-on-error isolates it.
                self.assertEqual(code, 0 if workspace.state()["targets"][index - 1]["dispatch"] == "dispatched" else 1)
        workspace.call("finalize")
        return workspace.state()

    def test_empty_registry_still_dispatches_only_builds(self):
        workspace = self.fixture(())
        state = self.dispatch(workspace)
        self.assertEqual([item["repository"] for item in state["targets"]], ["Hexalith.Builds"])
        self.assertEqual(state["targets"][0]["dispatch"], "dispatched")
        writes = [json.loads(line) for line in Path(workspace.config["dispatches"]).read_text().splitlines()]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0]["document"]["inputs"], {})

    def test_missing_ref_is_skip_and_failed_caller_does_not_suppress_builds(self):
        workspace = self.fixture()
        git(workspace.remote, "update-ref", "-d", "refs/heads/delivered/Hexalith.Alpha")
        source = workspace.root / "Hexalith.Beta-source"
        (source / ".github/workflows/release.yml").write_text("drift\n")
        git(source, "add", ".")
        git(source, "commit", "--quiet", "-m", "Drift")
        git(source, "push", "--quiet", workspace.remotes["Hexalith.Beta"], "HEAD:main")
        state = self.dispatch(workspace)
        self.assertEqual([item["eligibility"] for item in state["targets"]], ["not-adopted", "failed", "eligible"])
        self.assertEqual(state["targets"][-1]["dispatch"], "dispatched")

    def test_missing_config_symlink_mode_and_immutable_read_failure_fail_closed(self):
        for failure in ("config", "mode", "immutable"):
            with self.subTest(failure=failure):
                workspace = self.fixture(("Hexalith.Alpha",))
                source = workspace.root / "Hexalith.Alpha-source"
                if failure == "config":
                    (source / ".github/hexalith-ci.json").unlink()
                elif failure == "mode":
                    (source / ".github/workflows/release.yml").chmod(0o755)
                else:
                    workspace.config["responses"]["/repos/Hexalith/Hexalith.Alpha/immutable-releases"] = {"status": 403, "body": {}}
                if failure != "immutable":
                    git(source, "add", ".")
                    git(source, "commit", "--quiet", "-m", "Bad adoption")
                    git(source, "push", "--quiet", workspace.remotes["Hexalith.Alpha"], "HEAD:main")
                state = self.dispatch(workspace)
                self.assertEqual(state["targets"][0]["dispatch"], "failed")
                self.assertEqual(state["targets"][0]["eligibility"], "failed")
                self.assertIn("eligibility failed", state["targets"][0]["reason"])
                self.assertEqual(state["targets"][-1]["dispatch"], "dispatched")
                if failure == "immutable":
                    self.assertFalse(Path(workspace.config["dispatches"]).read_text().count("Hexalith.Alpha"))

    def test_delivery_busy_waits_then_clears_and_deadline_dispatches_nothing(self):
        for clears in (True, False):
            with self.subTest(clears=clears):
                workspace = self.fixture(())
                busy = {"id": 123, "head_branch": "main", "path": ".github/workflows/deliver.yml", "status": "pending"}
                idle = deepcopy(busy)
                idle["status"] = "completed"
                endpoint = "/repos/Hexalith/Hexalith.CiCd/actions/workflows/deliver.yml/runs?branch=main&status=pending&per_page=100&page=1"
                workspace.config["responses"][endpoint] = ([{"total_count": 1, "workflow_runs": [busy]},
                    {"total_count": 1, "workflow_runs": [idle]}] if clears else {"total_count": 1, "workflow_runs": [busy]})
                started = workspace.clock()
                code = workspace.call("barrier")
                self.assertEqual(code, 0 if clears else 1)
                self.assertGreaterEqual(workspace.clock() - started, 60)
                self.assertLessEqual(workspace.clock() - started, 1800)
                self.assertEqual(workspace.call("select"), 0 if clears else 1)
                if not clears:
                    self.assertFalse(Path(workspace.config["dispatches"]).exists())

    def test_target_mint_failure_and_uncertain_dispatch_preserve_siblings(self):
        workspace = self.fixture()
        workspace.config["dispatch_fail"] = ["Hexalith.Beta"]
        workspace.call("barrier")
        workspace.call("select")
        workspace.call("dispatch", slot=1, TARGET_TOKEN="")
        workspace.call("dispatch", slot=2)
        workspace.call("dispatch", slot=3)
        state = workspace.state()
        self.assertEqual([item["dispatch"] for item in state["targets"]], ["failed", "failed", "dispatched"])
        self.assertIn("not retried", state["targets"][1]["reason"])

    def test_dispatch_rejects_changed_eligibility_head_but_keeps_exact_created_run(self):
        workspace = self.fixture(("Hexalith.Alpha",))
        workspace.call("barrier")
        workspace.call("select")
        frozen = workspace.state()["targets"][0]["dispatchHead"]
        source = workspace.root / "Hexalith.Alpha-source"
        (source / "product.txt").write_text("concurrent main change\n")
        git(source, "add", ".")
        git(source, "commit", "--quiet", "-m", "Concurrent push")
        git(source, "push", "--quiet", workspace.remotes["Hexalith.Alpha"], "HEAD:main")
        workspace.call("dispatch", slot=1)
        workspace.call("dispatch", slot=2)
        item, builds = workspace.state()["targets"]
        self.assertEqual(item["dispatch"], "failed")
        self.assertEqual(item["dispatchHead"], frozen)
        self.assertEqual(item["runId"], 1001)
        self.assertEqual(item["link"], "https://github.com/Hexalith/Hexalith.Alpha/actions/runs/1001")
        self.assertIn("source changed", item["reason"])
        self.assertEqual(builds["dispatch"], "dispatched")
        workspace.call("finalize")
        # The readable but irreconcilable run is final target data: wait does
        # not poll it to the five-hour deadline or report an unreadable status.
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        started = workspace.clock()
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        state = workspace.state("wait")
        self.assertLess(workspace.clock() - started, 120)
        self.assertFalse(state["errors"])
        self.assertIn("cannot be accepted", state["targets"][0]["outcomeError"])
        self.assertEqual(state["targets"][0]["dispatchHead"], frozen)
        workspace.outputs.unlink(missing_ok=True)
        workspace.call("permit", phase="wait")
        self.assertIn("active=false", workspace.outputs.read_text().splitlines())

    def test_barrier_observes_queued_to_running_transition_and_rejects_late_idle(self):
        workspace = self.fixture(())
        workspace.config["barrier_transition"] = True
        started = workspace.clock()
        self.assertEqual(workspace.call("barrier"), 0)
        self.assertEqual(workspace.clock() - started, 120)
        requests = [json.loads(line)["path"] for line in Path(workspace.config["requests"]).read_text().splitlines()]
        scans = [path for path in requests if "/deliver.yml/runs?" in path]
        self.assertLess(next(index for index, path in enumerate(scans) if "status=queued" in path),
                        next(index for index, path in enumerate(scans) if "status=in_progress" in path))
        workspace = self.fixture(())
        path = "/repos/Hexalith/Hexalith.CiCd/actions/workflows/deliver.yml/runs?branch=main&status=requested&per_page=100&page=1"
        workspace.config["delays"] = {"GET " + path: 1801}
        self.assertEqual(workspace.call("barrier"), 1)
        self.assertFalse((workspace.directory / "barrier-cleared").exists())
        self.assertEqual(workspace.call("select"), 1)
        self.assertFalse(Path(workspace.config["dispatches"]).exists())

    def test_slow_dispatch_and_publication_slots_leave_healthy_siblings_time(self):
        workspace = self.fixture()
        workspace.call("barrier")
        workspace.call("select")
        workspace.config["delays"] = {"GET /repos/Hexalith/Hexalith.Alpha/immutable-releases": 90}
        workspace.call("dispatch", slot=1)
        workspace.call("dispatch", slot=2)
        workspace.call("dispatch", slot=3)
        self.assertEqual([item["dispatch"] for item in workspace.state()["targets"]], ["failed", "dispatched", "dispatched"])
        workspace = self.fixture()
        workspace.ready("Hexalith.Alpha")
        workspace.ready("Hexalith.Beta", release_id=881, producer_id=11, artifact_id=21)
        self.dispatch(workspace)
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        workspace.call("finalize", phase="wait")
        workspace.next_phase("publish-ready", workspace.artifact("wait"))
        workspace.config["delays"] = {"GET /repos/Hexalith/Hexalith.Alpha/releases?per_page=100&page=1": 90}
        # A failed publication slot step is red in Actions; a published one is green.
        self.assertEqual(workspace.call("publish", phase="publish-ready", slot=1), 1)
        self.assertEqual(workspace.call("publish", phase="publish-ready", slot=2), 0)
        first, second, _ = workspace.state("publish-ready")["targets"]
        self.assertEqual(first["publication"], "failed")
        self.assertEqual(second["publication"], "published")
        writes = [json.loads(line) for line in Path(workspace.config["publications"]).read_text().splitlines()]
        self.assertEqual([item["repository"] for item in writes], ["Hexalith.Beta"])

    def test_known_created_run_recovers_observations_after_first_read_failure(self):
        workspace = self.fixture(("Hexalith.Alpha",))
        workspace.config["status_fail"] = ["Hexalith.Alpha"]
        self.dispatch(workspace)
        original = workspace.state()["targets"][0]
        self.assertEqual(original["dispatch"], "failed")
        self.assertEqual(original["runId"], 1001)
        workspace.config["status_fail"] = []
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        workspace.call("permit", phase="wait")
        self.assertIn("Hexalith.Alpha", workspace.outputs.read_text())
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        recovered = workspace.state("wait")["targets"][0]
        self.assertEqual(recovered["dispatch"], "failed")
        self.assertEqual(recovered["reason"], original["reason"])
        self.assertEqual(recovered["outcome"]["outcome"], "nothing")
        self.assertEqual((recovered["status"], recovered["runAttempt"]), ("completed", 1))
        workspace.call("finalize", phase="wait")
        workspace.next_phase("publish-ready", workspace.artifact("wait"))
        self.assertEqual(workspace.call("finalize", phase="publish-ready"), 1)
        self.assertEqual([item["verdict"] for item in workspace.state("publish-ready")["targets"]], ["fail", "pass"])
        writes = [json.loads(line) for line in Path(workspace.config["dispatches"]).read_text().splitlines()]
        self.assertEqual(sum(item["repository"] == "Hexalith.Alpha" for item in writes), 1)

    def test_recovered_failed_dispatch_ready_result_gets_no_publication_slot_or_write_mint(self):
        workspace = self.fixture(("Hexalith.Alpha",))
        workspace.ready("Hexalith.Alpha")
        workspace.config["status_fail"] = ["Hexalith.Alpha"]
        self.dispatch(workspace)
        reason = workspace.state()["targets"][0]["reason"]
        workspace.config["status_fail"] = []
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        self.assertEqual(workspace.state("wait")["targets"][0]["outcome"]["outcome"], "ready")
        workspace.call("finalize", phase="wait")
        workspace.outputs.unlink(missing_ok=True)
        workspace.next_phase("publish-ready", workspace.artifact("wait"))
        self.assertEqual(workspace.outputs.read_text(), "")
        workspace.call("permit", phase="publish-ready", slot=1)
        self.assertEqual(workspace.outputs.read_text(), "active=false\n")
        self.assertEqual(workspace.call("finalize", phase="publish-ready"), 1)
        item = workspace.state("publish-ready")["targets"][0]
        self.assertEqual((item["verdict"], item["reason"]), ("fail", reason))
        self.assertFalse(Path(workspace.config["publications"]).exists())

    def test_wait_polls_pending_runs_at_60_second_intervals(self):
        workspace = self.fixture(())
        self.dispatch(workspace)
        workspace.config["pending"] = ["Hexalith.Builds"]
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        times = [item["at"] for item in map(json.loads, Path(workspace.config["requests"]).read_text().splitlines())
                 if item["path"] == "/repos/Hexalith/Hexalith.Builds/actions/runs/1001" and item["authorization"] == "Bearer inert-poll-token"]
        self.assertGreaterEqual(len(times), 39)
        self.assertEqual({later - earlier for earlier, later in zip(times, times[1:])}, {60})

    def test_slice_edge_outcome_read_stays_pollable_for_the_next_slice(self):
        workspace = self.fixture(())
        self.dispatch(workspace)
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        listing = "GET /repos/Hexalith/Hexalith.Builds/actions/runs/1001/artifacts?per_page=100&page=1"
        workspace.config["delays"] = {listing: 2400}
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        item = workspace.state("wait")["targets"][0]
        self.assertEqual((item["status"], item["outcome"], item["outcomeError"]), ("completed", None, ""))
        self.assertFalse(workspace.state("wait")["errors"])
        workspace.config["delays"] = {}
        workspace.outputs.unlink(missing_ok=True)
        workspace.call("permit", phase="wait")
        self.assertIn("active=true", workspace.outputs.read_text().splitlines())
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        self.assertEqual(workspace.state("wait")["targets"][0]["outcome"]["outcome"], "nothing")

    def test_slice_edge_stops_before_the_next_target_without_an_orchestration_error(self):
        workspace = self.fixture(("Hexalith.Alpha",))
        self.dispatch(workspace)
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        alpha, builds = workspace.state("wait")["targets"]
        workspace.config["delays"] = {
            f"GET /repos/Hexalith/Hexalith.Alpha/actions/runs/{alpha['runId']}/artifacts?per_page=100&page=1": 2399.5}
        Path(workspace.config["requests"]).unlink(missing_ok=True)
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        state = workspace.state("wait")
        self.assertEqual(state["errors"], [])
        self.assertEqual([(item["outcome"], item["outcomeError"]) for item in state["targets"]], [(None, ""), (None, "")])
        paths = [item["path"] for item in map(json.loads, Path(workspace.config["requests"]).read_text().splitlines())]
        self.assertNotIn(f"/repos/Hexalith/Hexalith.Builds/actions/runs/{builds['runId']}", paths)
        workspace.config["delays"] = {}
        workspace.call("permit", phase="wait")
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        self.assertEqual([item["outcome"]["outcome"] for item in workspace.state("wait")["targets"]], ["nothing", "nothing"])

    def test_slice_edge_recheck_failure_stays_pollable_without_an_orchestration_error(self):
        workspace = self.fixture(())
        self.dispatch(workspace)
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        workspace.config["delays"] = {"GET /repos/Hexalith/Hexalith.Builds/actions/runs/1001": 1199.6}
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        state = workspace.state("wait")
        self.assertEqual(state["errors"], [])
        item = state["targets"][0]
        self.assertEqual((item["status"], item["outcome"], item["outcomeError"]), ("completed", None, ""))
        workspace.config["delays"] = {}
        workspace.call("permit", phase="wait")
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        self.assertEqual(workspace.state("wait")["targets"][0]["outcome"]["outcome"], "nothing")

    def test_failed_publish_ready_initialization_withholds_every_write_slot(self):
        workspace = self.fixture(("Hexalith.Alpha",))
        workspace.ready("Hexalith.Alpha")
        self.dispatch(workspace)
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        self.assertEqual(workspace.state("wait")["targets"][0]["outcome"]["outcome"], "ready")
        workspace.call("finalize", phase="wait")
        workspace.outputs.unlink(missing_ok=True)
        workspace.config["bad_release"] = True
        workspace.next_phase("publish-ready", workspace.artifact("wait"))
        self.assertNotIn("slot_", workspace.outputs.read_text() if workspace.outputs.exists() else "")
        workspace.outputs.unlink(missing_ok=True)
        workspace.call("permit", phase="publish-ready", slot=1)
        self.assertEqual(workspace.outputs.read_text(), "active=false\n")
        self.assertEqual(workspace.call("finalize", phase="publish-ready"), 1)
        self.assertTrue(all(item["verdict"] == "fail" for item in workspace.state("publish-ready")["targets"]))
        self.assertFalse(Path(workspace.config["publications"]).exists())

    def test_complete_mode_outcome_may_name_an_older_release_sha(self):
        workspace = self.fixture(("Hexalith.Alpha",))
        state = self.dispatch(workspace)
        older = git(workspace.remotes["Hexalith.Alpha"], "rev-parse", "refs/heads/main~1")
        self.assertNotEqual(older, state["targets"][0]["dispatchHead"])
        workspace.config["outcomes"]["Hexalith.Alpha"] = {"schema": "hexalith.release-outcome.v1", "sha": older,
                                                         "outcome": "published", "version": "1.0.0"}
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        self.assertEqual(workspace.call("poll", phase="wait"), 0)
        item = workspace.state("wait")["targets"][0]
        self.assertEqual((item["outcome"]["sha"], item["outcomeError"]), (older, ""))
        workspace.call("finalize", phase="wait")
        workspace.next_phase("publish-ready", workspace.artifact("wait"))
        self.assertEqual(workspace.call("finalize", phase="publish-ready"), 0)
        self.assertEqual([row["verdict"] for row in workspace.state("publish-ready")["targets"]], ["pass", "pass"])

    def test_stalled_module_selection_cannot_spend_sibling_or_builds_time(self):
        workspace = self.fixture()
        workspace.config["slow_modules"] = {"Hexalith.Alpha": 25}
        self.assertEqual(workspace.call("barrier"), 0)
        self.assertEqual(workspace.call("select"), 0)
        state = workspace.state()
        self.assertEqual([item["eligibility"] for item in state["targets"]], ["failed", "eligible", "eligible"])
        self.assertIn("eligibility failed", state["targets"][0]["reason"])
        self.assertEqual(workspace.outputs.read_text().splitlines(), ["slot_02=Hexalith.Beta", "slot_03=Hexalith.Builds"])

    def test_unreadable_delivered_refs_fail_eligibility_and_never_mean_not_adopted(self):
        workspace = self.fixture()
        self.assertEqual(workspace.call("barrier"), 0)
        workspace.remote.rename(workspace.root / "cicd-unreadable.git")
        self.assertEqual(workspace.call("select"), 0)
        state = workspace.state()
        self.assertEqual([item["eligibility"] for item in state["targets"]], ["failed", "failed", "eligible"])
        self.assertTrue(all("eligibility failed" in item["reason"] for item in state["targets"][:2]))

    def test_orchestration_errors_stay_within_the_closed_state_bound(self):
        state = {"errors": []}
        for index in range(150):
            controller.fail(state, "distinct failure " + str(index))
        self.assertEqual(len(state["errors"]), 100)
        self.assertEqual(state["errors"][-1], controller.SUPPRESSED)
        self.assertEqual(state["errors"][98], "distinct failure 98")
        workspace = self.fixture(("Hexalith.Alpha",))
        self.dispatch(workspace)
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        path = workspace.directory / "wait.json"
        value = json.loads(path.read_bytes())
        for index in range(150):
            controller.fail(value, "run status read failed for Hexalith.Alpha: variant " + str(index))
        path.write_text(json.dumps(value))
        self.assertEqual(workspace.call("finalize", phase="wait"), 1)
        persisted = workspace.state("wait")
        self.assertEqual(persisted["targets"][0]["runId"], 1001)
        self.assertNotIn("local state unavailable", " ".join(persisted["errors"]))

    def test_outcome_download_rerun_rechecks_every_terminal_result_and_status_failure(self):
        for result in ("nothing", "disabled", "published", "unreadable"):
            with self.subTest(result=result):
                workspace = self.fixture(("Hexalith.Alpha",))
                self.dispatch(workspace)
                source = workspace.state()["targets"][0]["dispatchHead"]
                workspace.config["outcomes"]["Hexalith.Alpha"] = {"schema": "hexalith.release-outcome.v1", "sha": source,
                    "outcome": "nothing" if result == "unreadable" else result, "version": "1.0.0"}
                workspace.config["rerun_on_download"] = {"Hexalith.Alpha": "unreadable" if result == "unreadable" else "running"}
                workspace.next_phase("wait", workspace.artifact("dispatch"))
                self.assertEqual(workspace.call("poll", phase="wait"), 1 if result == "unreadable" else 0)
                state = workspace.state("wait")
                item = state["targets"][0]
                self.assertIsNone(item["outcome"])
                self.assertTrue(item["outcomeError"])
                if result != "unreadable":
                    self.assertEqual((item["status"], item["runAttempt"]), ("in_progress", 2))
                self.assertEqual(bool(state["errors"]), result == "unreadable")
                self.assertEqual(state["targets"][-1]["outcome"]["outcome"], "nothing")

    def test_handoffs_are_bound_to_current_run_attempt_and_closed_registry(self):
        for mutation in ("attempt", "source", "repository", "phase", "missing"):
            with self.subTest(mutation=mutation):
                workspace = self.fixture(())
                self.dispatch(workspace)
                path = workspace.directory / "dispatch.json"
                value = json.loads(path.read_bytes())
                if mutation == "attempt": value["identity"]["attempt"] = 2
                elif mutation == "source": value["identity"]["source"] = "f" * 40
                elif mutation == "repository": value["targets"][0]["repository"] = "Arbitrary"
                elif mutation == "phase": value["phase"] = "wait"
                path.write_text(json.dumps(value))
                artifact = workspace.artifact("dispatch")
                if mutation == "missing": artifact = ""
                self.assertEqual(workspace.next_phase("wait", artifact), 0)
                state = workspace.state("wait")
                self.assertTrue(state["errors"])
                self.assertEqual(state["targets"][0]["runId"], 0)

    def test_success_and_outcome_failures_are_data_and_status_read_failure_fails_wait(self):
        for mode in ("success", "outcome", "status"):
            with self.subTest(mode=mode):
                workspace = self.fixture(("Hexalith.Alpha",))
                self.dispatch(workspace)
                if mode == "outcome": workspace.config["outcomes"]["Hexalith.Alpha"] = {"outcome": "published"}
                if mode == "status": workspace.config["status_fail"] = ["Hexalith.Alpha"]
                self.assertEqual(workspace.next_phase("wait", workspace.artifact("dispatch")), 0)
                code = workspace.call("poll", phase="wait")
                state = workspace.state("wait")
                self.assertEqual(code, 1 if mode == "status" else 0)
                self.assertEqual(state["targets"][-1]["conclusion"], "success")
                if mode == "outcome": self.assertTrue(state["targets"][0]["outcomeError"])
                self.assertEqual(bool(state["errors"]), mode == "status")

    def test_exact_run_identity_and_previous_attempt_outcome_are_rejected(self):
        for mode in ("identity", "attempt"):
            with self.subTest(mode=mode):
                workspace = self.fixture(())
                self.dispatch(workspace)
                if mode == "identity":
                    workspace.config["responses"]["/repos/Hexalith/Hexalith.Builds/actions/runs/1001"] = {
                        "id": 999, "status": "completed"}
                else:
                    workspace.config["run_started"]["Hexalith.Builds"] = "2026-11-15T00:00:00Z"
                    workspace.config["run_attempts"]["Hexalith.Builds"] = 2
                workspace.next_phase("wait", workspace.artifact("dispatch"))
                code = workspace.call("poll", phase="wait")
                item = workspace.state("wait")["targets"][0]
                if mode == "identity": self.assertEqual(code, 1)
                else: self.assertIn("attempt", item["outcomeError"])

    def test_wait_deadline_survives_all_slices_and_timeout_is_a_failed_verdict(self):
        workspace = self.fixture(())
        self.dispatch(workspace)
        workspace.config["pending"] = ["Hexalith.Builds"]
        workspace.next_phase("wait", workspace.artifact("dispatch"))
        deadline = workspace.state("wait")["wait"]["deadline"]
        for _ in range(8):
            workspace.call("permit", phase="wait")
            values = dict(line.split("=", 1) for line in workspace.outputs.read_text().splitlines())
            if values["active"] == "true":
                self.assertEqual(workspace.call("poll", phase="wait"), 0)
        self.assertEqual(workspace.state("wait")["wait"]["deadline"], deadline)
        self.assertEqual(workspace.clock(), deadline)
        self.assertEqual(workspace.call("finalize", phase="wait"), 0)
        artifact = workspace.artifact("wait")
        workspace.next_phase("publish-ready", artifact)
        self.assertEqual(workspace.call("finalize", phase="publish-ready"), 1)
        self.assertEqual(workspace.state("publish-ready")["result"], "fail")

    def test_missing_local_state_finalizes_failed_report_and_summary(self):
        workspace = self.fixture(())
        (workspace.directory / "dispatch.json").unlink()
        self.assertEqual(workspace.call("finalize"), 1)
        self.assertTrue(workspace.state()["errors"])
        workspace.next_phase("publish-ready", "")
        self.assertEqual(workspace.call("finalize", phase="publish-ready"), 1)
        self.assertIn("Nightly releases: FAIL", (workspace.root / "summary.md").read_text())


if __name__ == "__main__":
    unittest.main()
