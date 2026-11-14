#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Execute actual job/step conditions and mappings with isolated controllers."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import unittest

import yaml
from delivery_support import ROOT, load
from test_delivery_workflow import Workflow as Expressions
from nightly_support import Workspace, metadata, zip_document

controller = load(ROOT / "tools/nightly.py", "_nightly_workflow_controller")
TOKENS = ("CICD_TOKEN", "TARGET_TOKEN", "POLL_TOKEN", "HANDOFF_TOKEN", "MODULE_TOKEN", "NIGHTLY_MINT_EPOCH")


class Workflow(Expressions):
    lookup = Expressions.lookup
    def expression(self, value):
        value = value.strip()
        if value.startswith("${{"):
            value = value[3:-2].strip()
        tokens = re.findall(r"'(?:[^']|'')*'|[A-Za-z_][A-Za-z0-9_.-]*|&&|\|\||==|!=|!|\(|\)|,", value)
        result = []
        for token in tokens:
            if token.startswith("'"): result.append(repr(token[1:-1]))
            elif token in {"&&", "||", "!"}: result.append({"&&": "and", "||": "or", "!": "not"}[token])
            elif token in {"==", "!=", "(", ")", ","}: result.append(token)
            elif token in {"always", "success", "failure", "cancelled", "format"}: result.append(token)
            elif token in {"true", "false"}: result.append("True" if token == "true" else "False")
            else: result.append(repr(self.lookup(token)))
        return eval(" ".join(result), {"__builtins__": {}}, {"always": lambda: True,
            "success": lambda: not self.failed and not self.cancelled, "failure": lambda: self.failed,
            "cancelled": lambda: self.cancelled, "format": lambda pattern, value: pattern.format(value)})

    def expand(self, value):
        if not isinstance(value, str): return value
        def replace(match):
            result = self.expression(match.group(1))
            return str(result).lower() if isinstance(result, bool) else str(result)
        return re.sub(r"\$\{\{(.*?)\}\}", replace, value)

    def __init__(self, workspace, *, event="workflow_dispatch", ref="refs/heads/main", mint_fail=(),
                 cancel_after=None, lost_artifact=None, pending=(), fail_checkout=None):
        self.w = workspace
        self.document = yaml.safe_load((ROOT / ".github/workflows/nightly.yml").read_bytes())
        self.context = {"github": {"ref": ref, "sha": workspace.sha, "repository": "Hexalith/Hexalith.CiCd",
            "workspace": str(workspace.candidate), "run_id": "101", "run_attempt": "1", "event_name": event,
            "token": "inert-handoff-token"}, "needs": {}, "steps": {}, "runner": {"temp": str(workspace.root)},
            "secrets": {"HEXALITH_CICD_APP_PRIVATE_KEY": "inert-private-key"},
            "vars": {"HEXALITH_CICD_APP_CLIENT_ID": "inert-client-id"}}
        self.mint_fail, self.cancel_after = set(mint_fail), cancel_after
        self.lost_artifact, self.fail_checkout = lost_artifact, fail_checkout
        self.w.config["pending"] = list(pending)
        self.failed, self.cancelled = False, False
        self.mints, self.uploads, self.commands, self.results, self.post_actions = [], [], [], {}, []
        self.tokens, self.elapsed = {}, {}
        # Only the job's own GITHUB_TOKEN exists before a mint; it reads CiCd handoffs.
        self.w.config["token_scopes"] = {"inert-handoff-token": ["Hexalith.CiCd"]}

    def execute(self):
        triggers = self.document.get("on", self.document.get(True))
        if self.context["github"]["event_name"] not in triggers:
            return "not-triggered"
        self.concurrency_group = self.expand(self.document["concurrency"]["group"])
        self.cancel_in_progress = self.document["concurrency"]["cancel-in-progress"]
        for phase, job in self.document["jobs"].items():
            self.failed = False
            self.context["steps"] = {}
            if not self.expression(job["if"]):
                self.results[phase] = "skipped"
                self.context["needs"][phase] = {"result": "skipped", "outputs": {}}
                continue
            if job["environment"] != "cicd-app" or not 0 < job["timeout-minutes"] < 360:
                raise AssertionError("App job environment or timeout is unsafe")
            # Dispatch downloads no handoff; later jobs read their predecessor's artifact.
            if job["permissions"] != ({"contents": "read"} if phase == "dispatch" else {"contents": "read", "actions": "read"}):
                raise AssertionError("job token grants excessive permissions")
            started = self.w.clock()
            base = {key: value for key, value in self.w.env().items() if key not in TOKENS}
            base.update({"GITHUB_" + key.upper(): str(value) for key, value in self.context["github"].items() if key != "token"})
            base.update({key: self.expand(value) for key, value in job.get("env", {}).items()})
            self.context["env"] = base
            self.w.directory = Path(base["NIGHTLY_DIRECTORY"])
            for ordinal, step in enumerate(job["steps"]):
                self.context["job"] = {"status": "cancelled" if self.cancelled else "failure" if self.failed else "success"}
                identifier = step.get("id", f"step_{ordinal}")
                if not self.expression(step.get("if", "success()")):
                    self.context["steps"][identifier] = {"outcome": "skipped", "outputs": {}}
                    continue
                outputs, outcome = {}, "success"
                if "uses" in step:
                    action, pin = step["uses"].split("@")
                    if len(pin) != 40 or not all(c in "0123456789abcdef" for c in pin):
                        raise AssertionError("external action is not pinned")
                    inputs = {key: self.expand(value) for key, value in step.get("with", {}).items()}
                    if action == "actions/checkout":
                        if inputs.get("submodules") is not False or inputs.get("persist-credentials") is not False:
                            raise AssertionError("unsafe checkout")
                        if phase == self.fail_checkout:
                            outcome = "failure"
                    elif action == "actions/create-github-app-token":
                        if self.cancelled:
                            raise AssertionError("mint action executed after cancellation")
                        repositories = inputs.get("repositories", "").split(",")
                        allowed = {*self.w.modules, "Hexalith.Builds", "Hexalith.CiCd"}
                        if (inputs.get("owner") != "Hexalith" or not repositories or "" in repositories
                                or not set(repositories) <= allowed or inputs.get("skip-token-revoke") is not True):
                            raise AssertionError("implicit scope or aged post-job revocation")
                        # The action ignores empty permission inputs.
                        permissions = {key: value for key, value in inputs.items() if key.startswith("permission-") and value}
                        if phase == "wait":
                            if permissions != {"permission-actions": "read"}:
                                raise AssertionError("wait token is not read-only")
                        elif phase == "publish-ready":
                            if len(repositories) != 1 or permissions != {
                                    "permission-contents": "write", "permission-workflows": "write", "permission-actions": "read"}:
                                raise AssertionError("publication permission mismatch")
                        elif repositories == ["Hexalith.CiCd"]:
                            if identifier != "barrier_token" or permissions != {"permission-actions": "read"}:
                                raise AssertionError("delivery barrier token is not read-only")
                        elif len(repositories) != 1 or permissions != ({"permission-actions": "write"} if repositories == ["Hexalith.Builds"]
                                else {"permission-actions": "write", "permission-administration": "read"}):
                            raise AssertionError("dispatch permission mismatch")
                        self.mints.append((phase, identifier, self.w.clock(), inputs))
                        self.w.advance(1)  # the action consumes time after the recorded boundary
                        if identifier in self.mint_fail or phase + ":" + identifier in self.mint_fail or any(repo in self.mint_fail for repo in repositories):
                            outcome = "failure"
                        else:
                            # A distinct credential per mint exposes any cross-slot or stale mapping.
                            token = f"inert-{phase}-{identifier}"
                            outputs["token"] = token
                            self.tokens[token] = len(self.mints) - 1
                            self.w.config["token_scopes"][token] = repositories
                        self.post_actions.append({"skip": inputs["skip-token-revoke"], "minted": self.w.clock()})
                    elif action == "actions/upload-artifact":
                        path = Path(inputs["path"])
                        if not path.exists():
                            outcome = "failure"
                        else:
                            data = path.read_bytes()
                            if any(token in data for token in (b"inert-", b"Bearer", b"private-key")):
                                raise AssertionError("artifact leaked a credential")
                            artifact = 7001 + len(self.uploads)
                            payload = zip_document(path.name, json.loads(data))
                            archive = self.w.root / (str(artifact) + ".zip")
                            archive.write_bytes(payload)
                            self.w.config["handoffs"][str(artifact)] = {"path": str(archive), "metadata": metadata(
                                artifact, inputs["name"], payload, 101, self.w.sha)}
                            self.uploads.append((phase, json.loads(data)))
                            if phase != self.lost_artifact:
                                outputs["artifact-id"] = str(artifact)
                    else:
                        raise AssertionError("unexpected action: " + action)
                else:
                    command = shlex.split(step["run"])
                    if command[:3] == ["python3", "-I", "-c"]:
                        if "${{" in step["run"]:
                            raise AssertionError("expression interpolated in fallback shell code")
                        result = subprocess.run([sys.executable, *command[1:]], env=base, capture_output=True)
                        if result.stdout or result.stderr:
                            raise AssertionError("seed/fallback emitted unexpected output")
                        outcome = "failure" if result.returncode else "success"
                        self.context["steps"][identifier] = {"outcome": outcome, "outputs": {}}
                        if outcome == "failure" and not step.get("continue-on-error", False):
                            self.failed = True
                        continue
                    if command[:3] != ["python3", "-I", "tools/nightly.py"] or "${{" in step["run"]:
                        raise AssertionError("App command is not an isolated controller")
                    operation = command[3]
                    env = base | {key: str(self.expand(value)).lower() if isinstance(self.expand(value), bool) else self.expand(value)
                                  for key, value in step.get("env", {}).items()}
                    self.w.outputs.unlink(missing_ok=True)
                    args = command[4:]
                    slot = int(args[args.index("--slot") + 1]) if "--slot" in args else None
                    self.commands.append((phase, operation, slot, self.w.clock(), env.get("NIGHTLY_MINT_EPOCH"), env.get("POLL_TOKEN", "")))
                    for name in ("CICD_TOKEN", "TARGET_TOKEN", "POLL_TOKEN"):
                        if env.get(name):
                            # Each controller receives the latest mint of its own job,
                            # with that mint's own recorded boundary.
                            index = self.tokens.get(env[name])
                            if index is None or index != len(self.mints) - 1 or self.mints[index][0] != phase:
                                raise AssertionError("controller received another or stale mint's token")
                            if float(env.get("NIGHTLY_MINT_EPOCH", "nan")) != self.mints[index][2]:
                                raise AssertionError("controller mint epoch is not its own mint boundary")
                    if phase == self.fail_checkout:
                        outcome = "failure"
                    elif self.w.call(operation, phase=phase, slot=slot, env=env):
                        outcome = "failure"
                    if self.w.outputs.exists():
                        outputs = dict(line.split("=", 1) for line in self.w.outputs.read_text().splitlines())
                self.context["steps"][identifier] = {"outcome": outcome, "outputs": outputs}
                if outcome == "failure" and not step.get("continue-on-error", False):
                    self.failed = True
                if self.cancel_after == (phase, identifier):
                    self.cancelled = True
            self.results[phase] = "failure" if self.failed else "success"
            self.elapsed[phase] = self.w.clock() - started
            self.context["needs"][phase] = {"result": self.results[phase], "outputs": {
                key: self.expand(value) for key, value in job.get("outputs", {}).items()}}
        return "failure" if "failure" in self.results.values() else "success"


class NightlyWorkflowTests(unittest.TestCase):
    def fixture(self, modules=("Hexalith.Alpha", "Hexalith.Beta")):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        workspace = Workspace(Path(temporary.name) / "workspace", modules)
        for repository in modules:
            workspace.ref(repository)
        return workspace

    def test_main_schedule_manual_and_no_push_pr_or_nonmain_app_jobs(self):
        for event, ref, result in (("schedule", "refs/heads/main", "success"),
                ("workflow_dispatch", "refs/heads/main", "success"), ("push", "refs/heads/main", "not-triggered"),
                ("pull_request", "refs/pull/1/merge", "not-triggered"), ("workflow_dispatch", "refs/heads/other", "success")):
            with self.subTest(event=event, ref=ref):
                workflow = Workflow(self.fixture(()), event=event, ref=ref)
                self.assertEqual(workflow.execute(), result)
                if result != "not-triggered":
                    # A skipped non-main dispatch cannot replace main's pending run.
                    self.assertEqual(workflow.concurrency_group,
                                     "nightly" if ref == "refs/heads/main" else "nightly-skipped-" + ref)
                if ref != "refs/heads/main": self.assertFalse(workflow.mints)
                elif result == "success":
                    self.assertEqual(list(workflow.results), ["dispatch", "wait", "publish-ready"])
                    self.assertEqual(workflow.uploads[-1][1]["result"], "pass")

    def test_all_17_modules_and_builds_keep_slot_scopes_and_inputs(self):
        workspace = self.fixture(tuple(f"Hexalith.Module{index:02d}" for index in range(1, 18)))
        repositories = [*workspace.modules, "Hexalith.Builds"]
        for index, repository in enumerate(repositories, 1):
            workspace.ready(repository, release_id=80000 + index, producer_id=50000 + index, artifact_id=90000 + index)
        workflow = Workflow(workspace)
        self.assertEqual(workflow.execute(), "success")
        report = workflow.uploads[-1][1]
        self.assertEqual(len(report["targets"]), 18)
        self.assertTrue(all(row["verdict"] == "pass" for row in report["targets"]))
        self.assertEqual(workflow.concurrency_group, "nightly")
        self.assertFalse(workflow.cancel_in_progress)
        requests = [json.loads(line) for line in Path(workspace.config["requests"]).read_text().splitlines()]
        targets = [inputs["repositories"] for phase, _, _, inputs in workflow.mints if phase == "dispatch" and inputs["repositories"] != "Hexalith.CiCd"]
        self.assertEqual(targets, [*workspace.modules, "Hexalith.Builds"])
        permissions = [(identifier, inputs["repositories"], inputs["permission-actions"], inputs.get("permission-administration"))
                       for phase, identifier, _, inputs in workflow.mints if phase == "dispatch"]
        self.assertEqual(permissions, [("barrier_token", "Hexalith.CiCd", "read", None)] + [
            (f"target_{index:02d}_token", repository, "write", "" if repository == "Hexalith.Builds" else "read")
            for index, repository in enumerate(repositories, 1)])
        # Each dispatch and publication process authenticated with its own slot's mint.
        used = {(item["path"].split("/")[3], item["authorization"]) for item in requests
                if item["authorization"] and item["path"].split("/")[3] != "Hexalith.CiCd"}
        for index, repository in enumerate(repositories, 1):
            for phase in ("dispatch", "publish-ready"):
                self.assertIn((repository, f"Bearer inert-{phase}-target_{index:02d}_token"), used)
        self.assertLess(workflow.elapsed["dispatch"] + 7 * 60, 55 * 60)
        self.assertLess(workflow.elapsed["publish-ready"] + 7 * 60, 55 * 60)
        writes = [json.loads(line) for line in Path(workspace.config["dispatches"]).read_text().splitlines()]
        self.assertEqual(len(writes), 18)
        self.assertTrue(all(write["document"]["inputs"] == {"delivered-sha": workspace.accepted} for write in writes[:-1]))
        self.assertEqual(writes[-1]["document"]["inputs"], {})
        published = [json.loads(line) for line in Path(workspace.config["publications"]).read_text().splitlines()]
        self.assertEqual([(item["repository"], item["release_id"]) for item in published],
                         [(repository, 80000 + index) for index, repository in enumerate(repositories, 1)])
        self.assertEqual([(item[1], item[3]["repositories"]) for item in workflow.mints if item[0] == "publish-ready"],
                         [(f"target_{index:02d}_token", repository) for index, repository in enumerate(repositories, 1)])
        self.assertEqual([item[2] for item in workflow.commands if item[0:2] == ("publish-ready", "publish")], list(range(1, 19)))
        self.assertTrue(all(item["publication"] == "published" for item in report["targets"]))
        # Every job authenticates the immutable release/tag/source once. None
        # of the 18 publication slots or polling slices reacquires it.
        anonymous = [item for item in requests if item["authorization"] is None]
        self.assertEqual(len(anonymous), 12)
        self.assertEqual(sum(item["path"].endswith("/releases/tags/v5.1.0") for item in anonymous), 3)

    def test_mint_failure_and_failed_upstream_still_collect_and_finalize(self):
        workflow = Workflow(self.fixture(), mint_fail=("Hexalith.Alpha",))
        self.assertEqual(workflow.execute(), "failure")
        self.assertEqual(len(workflow.uploads), 3)
        report = workflow.uploads[-1][1]
        self.assertEqual([row["verdict"] for row in report["targets"]], ["fail", "pass", "pass"])
        self.assertEqual(workflow.results["dispatch"], "failure")
        self.assertEqual(workflow.results["publish-ready"], "failure")

    def test_ready_publication_uses_target_slots_and_isolates_mint_failure(self):
        for failed in (False, True):
            with self.subTest(failed=failed):
                workspace = self.fixture()
                workspace.ready("Hexalith.Alpha")
                workspace.ready("Hexalith.Beta", release_id=881, producer_id=11, artifact_id=21)
                workflow = Workflow(workspace, mint_fail=("publish-ready:target_01_token",) if failed else ())
                self.assertEqual(workflow.execute(), "failure" if failed else "success")
                report = workflow.uploads[-1][1]
                self.assertEqual([item["verdict"] for item in report["targets"]],
                                 ["fail" if failed else "pass", "pass", "pass"])
                publication_mints = [item[3]["repositories"] for item in workflow.mints if item[0] == "publish-ready"]
                self.assertEqual(publication_mints, ["Hexalith.Alpha", "Hexalith.Beta"])
                writes = [json.loads(line) for line in Path(workspace.config["publications"]).read_text().splitlines()]
                self.assertEqual(len(writes), 1 if failed else 2)

    def test_missing_artifact_and_checkout_failure_synthesize_red_state(self):
        for configuration in ({"lost_artifact": "dispatch"}, {"fail_checkout": "dispatch"}):
            with self.subTest(configuration=configuration):
                workflow = Workflow(self.fixture(), **configuration)
                self.assertEqual(workflow.execute(), "failure")
                report = workflow.uploads[-1][1]
                self.assertEqual(report["result"], "fail")
                self.assertEqual(len(report["targets"]), 3)
                self.assertTrue(report["errors"])

    def test_actual_wait_renews_before_50_minutes_and_keeps_aggregate_deadline(self):
        workspace = self.fixture(())
        workflow = Workflow(workspace, pending=("Hexalith.Builds",), mint_fail=("poll_02_token",))
        self.assertEqual(workflow.execute(), "failure")
        report = workflow.uploads[-1][1]
        self.assertEqual(report["wait"]["deadline"] - report["wait"]["started"], 18000)
        polls = [item for item in workflow.commands if item[0] == "wait" and item[1] == "poll"]
        self.assertGreaterEqual(len(polls), 8)
        self.assertTrue(all(started - float(epoch) < 3000 for _, _, _, started, epoch, _ in polls))
        self.assertEqual(polls[1][-1], "")
        self.assertTrue(all(action["skip"] for action in workflow.post_actions))
        self.assertGreater(workspace.clock() - workflow.post_actions[0]["minted"], 3000)
        # Over five fake hours of polling still leaves checkout/mint/upload reserve.
        self.assertGreaterEqual(workflow.elapsed["wait"], 300 * 60)
        self.assertLess(workflow.elapsed["wait"] + 7 * 60, 330 * 60)

    def test_job_timeouts_cover_controller_budgets_and_unmetered_step_limits(self):
        for phase, job in yaml.safe_load((ROOT / ".github/workflows/nightly.yml").read_bytes())["jobs"].items():
            with self.subTest(phase=phase):
                limits = {step["uses"].split("@")[0]: step["timeout-minutes"] for step in job["steps"] if "uses" in step}
                reserve = (limits["actions/checkout"] + limits["actions/create-github-app-token"]
                           + limits["actions/upload-artifact"] + 1) * 60
                self.assertLess(controller.SECONDS[phase] + reserve, job["timeout-minutes"] * 60)

    def test_cancel_stops_new_mints_dispatches_and_publication_but_uploads(self):
        for after in ("select", "target_01_budget", "target_01_token"):
            with self.subTest(after=after):
                workflow = Workflow(self.fixture(), cancel_after=("dispatch", after))
                workflow.execute()
                self.assertTrue(workflow.cancelled)
                self.assertEqual(workflow.results["wait"], "skipped")
                self.assertEqual(workflow.results["publish-ready"], "skipped")
                self.assertEqual(len(workflow.uploads), 1)
                self.assertTrue(workflow.uploads[0][1]["errors"])
                self.assertFalse(Path(workflow.w.config["dispatches"]).exists())

    def test_cancel_in_wait_or_publish_ready_stops_later_mints_and_publication_but_uploads(self):
        for phase, after, uploads in (("wait", "poll_01_budget", 2), ("publish-ready", "target_01_token", 3)):
            with self.subTest(phase=phase, after=after):
                workspace = self.fixture()
                workspace.ready("Hexalith.Alpha")
                workspace.ready("Hexalith.Beta", release_id=881, producer_id=11, artifact_id=21)
                workflow = Workflow(workspace, cancel_after=(phase, after))
                workflow.execute()
                self.assertTrue(workflow.cancelled)
                self.assertFalse(Path(workspace.config["publications"]).exists())
                # The harness refuses any mint action after cancellation.
                self.assertEqual([item[1] for item in workflow.mints if item[0] == phase],
                                 [] if phase == "wait" else ["target_01_token"])
                self.assertEqual([item[0] for item in workflow.uploads], ["dispatch", "wait", "publish-ready"][:uploads])
                final = workflow.uploads[-1][1]
                self.assertIn("nightly orchestration was cancelled", final["errors"])
                if phase == "wait":
                    self.assertEqual(workflow.results["publish-ready"], "skipped")
                    self.assertTrue(all(row["runId"] for row in final["targets"]))
                else:
                    self.assertEqual(final["result"], "fail")
                    self.assertTrue(all(row["publication"] != "published" for row in final["targets"]))


if __name__ == "__main__":
    unittest.main()
