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
TOKENS = ("CICD_TOKEN", "TARGET_TOKEN", "POLL_TOKEN", "HANDOFF_TOKEN", "MODULE_TOKEN", "NIGHTLY_MINT_EPOCH",
          "GITHUB_TOKEN", "GH_TOKEN", "NODE_AUTH_TOKEN", "NPM_TOKEN")


def artifact_path(inputs, workspace):
    """Model upload-artifact's path rejection before reading fixture bytes."""
    raw = inputs["path"]
    if not isinstance(raw, str) or not Path(raw).is_absolute() or any(part in {".", ".."} for part in raw.split("/")):
        raise AssertionError("artifact path is relative or contains '.'/'..' segments")
    path = Path(raw)
    checkout = Path(workspace)
    try:
        relative = path.relative_to(checkout.parent)
    except ValueError:
        raise AssertionError("nightly artifact path is outside the job's sibling directories") from None
    if not relative.parts or not relative.parts[0].startswith(checkout.name + "-nightly-"):
        raise AssertionError("nightly artifact path is inside checkout or outside its job directory prefix")
    if any(part.startswith(".") for part in relative.parts):
        raise AssertionError("artifact path would be excluded as hidden")
    return path


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
        # A job condition binds success() to its needs (see job_condition);
        # step conditions keep the job's own step status.
        return eval(" ".join(result), {"__builtins__": {}}, {"always": lambda: True,
            "success": lambda: getattr(self, "upstream", None) is not False and not self.failed and not self.cancelled,
            "failure": lambda: self.failed,
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
            "token": "inert-handoff-token"}, "needs": {}, "steps": {}, "runner": {"temp": str(workspace.root / "runner-temp")},
            "secrets": {"HEXALITH_CICD_APP_PRIVATE_KEY": "inert-private-key"},
            "vars": {"HEXALITH_CICD_APP_CLIENT_ID": "inert-client-id"}}
        self.mint_fail, self.cancel_after = set(mint_fail), cancel_after
        Path(self.context["runner"]["temp"]).mkdir(exist_ok=True)
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
        # These fixture I/O doubles exercise the pre-existing release contract.
        # PostReleaseWorkflow below executes the new graph with its independent
        # controller-result boundary, without silently dropping the new jobs.
        for phase, job in self.document["jobs"].items():
            if phase not in controller.SECONDS:
                continue
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
                        path = artifact_path(inputs, self.context["github"]["workspace"])
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


class ArtifactPathWorkflowTests(unittest.TestCase):
    def test_every_job_upload_expands_to_a_nonhidden_canonical_sibling(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        workflow = Workflow(Workspace(Path(temporary.name) / "workspace", ()))
        checkout = workflow.context["github"]["workspace"]
        uploads = []
        for phase, job in workflow.document["jobs"].items():
            base = {key: workflow.expand(value) for key, value in job.get("env", {}).items()}
            workflow.context["env"] = base
            for step in job["steps"]:
                if not step.get("uses", "").startswith("actions/upload-artifact@"):
                    continue
                inputs = {key: workflow.expand(value) for key, value in step["with"].items()}
                path = artifact_path(inputs, checkout)
                self.assertEqual(path.suffix, "" if phase == "scan" else ".json")
                self.assertNotIn("include-hidden-files", inputs)
                uploads.append((phase, path))
        self.assertEqual({phase for phase, _ in uploads}, set(workflow.document["jobs"]))
        self.assertEqual(len(uploads), 9)
        self.assertEqual(len({path for _, path in uploads}), 9)

    def test_upload_boundary_rejects_parent_current_hidden_and_relative_paths(self):
        checkout = "/runner/work/Repo/Repo"
        for path in (checkout + "/../.nightly/report.json", checkout + "-nightly/./report.json",
                     checkout + "-nightly-101-1/.report.json", "nightly/report.json",
                     "/workspace/nightly/report.json", checkout + "/report.json"):
            with self.subTest(path=path), self.assertRaises(AssertionError):
                artifact_path({"path": path}, checkout)
        self.assertEqual(artifact_path({"path": checkout + "-nightly-101-1/report.json"}, checkout),
                         Path(checkout + "-nightly-101-1/report.json"))


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
            if phase not in controller.SECONDS:
                continue
            with self.subTest(phase=phase):
                limits = {step["uses"].split("@")[0]: step["timeout-minutes"] for step in job["steps"] if "uses" in step}
                reserve = (limits["actions/checkout"] + limits["actions/create-github-app-token"]
                           + limits["actions/upload-artifact"] + 1) * 60
                self.assertLess(controller.SECONDS[phase] + reserve, job["timeout-minutes"] * 60)

    def test_bump_job_timeouts_cover_controller_budgets_and_metered_step_limits(self):
        jobs = yaml.safe_load((ROOT / ".github/workflows/nightly.yml").read_bytes())["jobs"]
        observer = load(ROOT / "tools/nightly_delivery_wait.py", "_timeout_delivery_wait")
        budgets = {
            "bump": load(ROOT / "tools/bump.py", "_timeout_bump").JOB_SECONDS,
            "bump-push": load(ROOT / "tools/bump_push.py", "_timeout_bump_push").JOB_SECONDS,
            # The persisted aggregate deadline bounds every observer operation.
            "delivery-wait": min(observer.JOB_SECONDS, observer.WAIT_SECONDS),
            "keepalive": load(ROOT / "tools/nightly_keepalive.py", "_timeout_keepalive").JOB_SECONDS,
        }
        for phase, budget in budgets.items():
            with self.subTest(phase=phase):
                steps = sum(step.get("timeout-minutes", 0) for step in jobs[phase]["steps"]) * 60
                # One further minute covers job setup and unmetered seed/report steps.
                self.assertLessEqual(budget + steps + 60, jobs[phase]["timeout-minutes"] * 60)

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


class PostReleaseWorkflow(Workflow):
    """Execute the real new graph with controller results at the I/O boundary.

    Producer, verifier and observers have separate real Git/controller suites.
    Here the boundary substitutes their outcomes so every workflow path, token
    mapping, cancellation condition and artifact upload can be exercised without
    a live Actions service. Inline failure seeds execute in isolated children.
    """
    def __init__(self, workspace, *, publication="success", producer="candidate", push="pushed",
                 propagation="success", keepalive="success", qualify=False, ref="refs/heads/main",
                 mint_fail=(), cancel_after=None, fail_checkout=None, scan="pass", fail_tool=None):
        super().__init__(workspace, ref=ref, mint_fail=mint_fail, cancel_after=cancel_after,
                         fail_checkout=fail_checkout)
        self.context["inputs"] = {"qualify-bump": qualify}
        self.context["needs"] = {"publish-ready": {"result": publication, "outputs": {}}}
        self.producer, self.push, self.propagation, self.keepalive = producer, push, propagation, keepalive
        self.extension_calls = []
        self.current_directory = None
        self.deadline, self.observation_failed = None, False
        self.scan, self.fail_tool = scan, fail_tool
        self.scan_summaries = []

    def controller_call(self, phase, command, env):
        self.extension_calls.append((phase, tuple(command), env.copy(), self.w.clock()))
        outputs, failed = {}, False
        if phase == "scan":
            if command != ["uv", "run", "--locked", "tools/scan.py"]:
                raise AssertionError("scan did not run the locked controller")
            if any(env.get(name) for name in TOKENS):
                raise AssertionError("scan received a credential")
            if self.scan != "missing":
                result = "pass" if self.scan == "pass" else "fail"
                directory = Path(env["SCAN_DIRECTORY"])
                (directory / "report.json").write_text(json.dumps({"schema": "hexalith.duplicate-scan.v1",
                    "result": result, "modules": [], "findings": [], "errors": []}))
                (directory / "summary.md").write_text("Duplicate scan: " + result.upper() + "\n")
                failed = self.scan == "failure"
        elif phase == "bump":
            if command != ["uv", "run", "--locked", "tools/bump.py"]:
                raise AssertionError("unexpected producer command")
            if env.get("GITHUB_TOKEN") != self.context["github"]["token"]:
                raise AssertionError("producer lacks its read-only job token")
            if self.producer == "candidate":
                path = Path(env["BUMP_DIRECTORY"]) / "candidate.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"candidate": "b" * 40, "base": self.w.sha}))
                outputs = {"result": "candidate", "candidate": "b" * 40, "base": self.w.sha}
            elif self.producer == "no-change":
                outputs = {"result": "no-change", "base": self.w.sha}
            elif self.producer == "missing":
                outputs = {}
            else:
                failed = True
            Path(env["BUMP_DIRECTORY"], "bump.json").write_text(json.dumps({"result": self.producer}))
        elif phase == "bump-push":
            if command[:3] != ["python3", "-I", "tools/bump_push.py"]:
                raise AssertionError("writer did not isolate its stdlib controller")
            if env.get("CICD_TOKEN") != self.context["github"]["token"]:
                raise AssertionError("writer does not use its own job token")
            if self.context["inputs"]["qualify-bump"]:
                if command[3:] != ["qualify"] or env.get("BUMP_ARTIFACT_ID"):
                    raise AssertionError("qualification entered production writer")
                result = "qualified"
            else:
                if command[3:] or not env.get("BUMP_ARTIFACT_ID") or not env.get("BUMP_ARTIFACT_DIGEST"):
                    raise AssertionError("writer lost candidate artifact binding")
                if env.get("BUMP_TRANSPORT") != "github-token":
                    raise AssertionError("unqualified fallback selected")
                failed = self.push in {"failure", "dispatch-failure"}
                result = "pushed" if self.push == "dispatch-failure" else "fail" if failed else self.push
                if result == "pushed":
                    outputs = {"result": "pushed", "candidate": "b" * 40, "base": self.w.sha}
            Path(env["BUMP_DIRECTORY"], "bump-push.json").write_text(json.dumps({"result": result}))
        elif phase == "delivery-wait":
            if command[:3] != ["python3", "-I", "tools/nightly_delivery_wait.py"]:
                raise AssertionError("App job executed an unexpected command")
            if env.get("BUMP_SHA") != "b" * 40 or env.get("BUMP_PUSH_RESULT") != "pushed":
                raise AssertionError("observer lost confirmed pushed identity")
            operation = command[3]
            if operation == "initialize":
                self.deadline = self.w.clock() + 90 * 60
                outputs = {"active": "true", "repositories": ",".join(["Hexalith.CiCd", *self.w.modules])}
            elif operation == "permit":
                outputs = {"active": str(self.w.clock() < self.deadline).lower(),
                           "mint_epoch": str(self.w.clock())}
            elif operation == "poll":
                token = env.get("POLL_TOKEN", "")
                if token:
                    if token not in self.tokens or self.tokens[token] != len(self.mints) - 1:
                        raise AssertionError("observer reused an earlier or cross-job token")
                    mint = self.mints[self.tokens[token]]
                    if mint[0] != phase or float(env["NIGHTLY_MINT_EPOCH"]) != mint[2]:
                        raise AssertionError("observer uses a different mint's boundary")
                    if self.w.clock() - mint[2] >= 50 * 60:
                        raise AssertionError("observer exceeded token age boundary")
                    self.w.advance(min(40 * 60, self.deadline - self.w.clock()))
                else:
                    self.observation_failed = True
                    failed = True
            elif operation == "finalize":
                failed = self.propagation == "failure" or self.observation_failed or self.cancelled
            else:
                raise AssertionError("unexpected observer operation")
            path = Path(env["NIGHTLY_DIRECTORY"]) / "delivery-wait/report.json"
            path.write_text(json.dumps({"result": "fail" if failed else "pass", "deadline": self.deadline}))
        elif phase == "keepalive":
            if command != ["python3", "-I", "tools/nightly_keepalive.py"]:
                raise AssertionError("keepalive did not isolate its stdlib controller")
            if env.get("CICD_TOKEN") != self.context["github"]["token"]:
                raise AssertionError("keepalive borrowed another job's token")
            failed = self.keepalive == "failure"
            Path(env["NIGHTLY_DIRECTORY"], "keepalive.json").write_text(json.dumps({"result": "fail" if failed else "pass"}))
        else:
            raise AssertionError("unrecognized post-release phase")
        return failed, outputs

    def ordered_jobs(self):
        """Schedule by real dependencies, preferring reverse declaration order.

        This makes a missing scan dependency observable: bump would start first.
        Conditions still decide eligibility after failed or skipped dependencies.
        """
        pending = {}
        for phase, job in self.document["jobs"].items():
            if phase in controller.SECONDS:
                # Qualify mode must skip every prior release phase as well.
                if self.context["inputs"]["qualify-bump"] and self.expression(job["if"]):
                    raise AssertionError("qualification allowed release orchestration")
                continue
            pending[phase] = job
        while pending:
            for phase in reversed(pending):
                job = pending[phase]
                needed = job.get("needs", [])
                needed = [needed] if isinstance(needed, str) else needed
                if all(name in self.context["needs"] for name in needed):
                    del pending[phase]
                    yield phase, job
                    break
            else:
                raise AssertionError("post-release graph has an unresolved dependency")

    def job_condition(self, phase, job):
        """Evaluate a job `if` with GitHub's job-level status semantics.

        Without a status function the condition is implicitly `success() && ...`.
        success() requires every transitive need to have succeeded; failure()
        is true when any of them failed. Removing `!cancelled()` is observable.
        """
        text = job.get("if", "").strip()
        if text.startswith("${{"):
            text = text[3:-2].strip()
        if not re.search(r"\b(?:success|failure|cancelled|always)\s*\(", text):
            text = "success() && (" + (text or "true") + ")"
        ancestors, pending = set(), [phase]
        while pending:
            needed = self.document["jobs"].get(pending.pop(), {}).get("needs", [])
            for name in [needed] if isinstance(needed, str) else needed:
                if name not in ancestors:
                    ancestors.add(name)
                    pending.append(name)
        results = [self.context["needs"][name]["result"] for name in ancestors if name in self.context["needs"]]
        self.failed, self.upstream = "failure" in results, all(result == "success" for result in results)
        try:
            return self.expression(text)
        finally:
            self.failed, self.upstream = False, None

    def execute(self):
        for phase, job in self.ordered_jobs():
            self.failed, self.context["steps"] = False, {}
            if not self.job_condition(phase, job):
                self.results[phase] = "skipped"
                self.context["needs"][phase] = {"result": "skipped", "outputs": {}}
                continue
            if not 0 < job["timeout-minutes"] < 360:
                raise AssertionError("unbounded job timeout")
            expected = ({"contents": "read"} if phase == "scan" else
                {"contents": "read", "actions": "read"} if phase in {"bump", "delivery-wait"} else
                {"contents": "write", "actions": "write"})
            if job["permissions"] != expected:
                raise AssertionError("post-release job token permission mismatch")
            if (job.get("environment") == "cicd-app") != (phase == "delivery-wait"):
                raise AssertionError("App environment escaped observer")
            base = {key: value for key, value in self.w.env().items() if key not in TOKENS}
            base.update({"GITHUB_" + key.upper(): str(value) for key, value in self.context["github"].items() if key != "token"})
            base.update({key: self.expand(value) for key, value in job.get("env", {}).items()})
            self.context["env"] = base
            for ordinal, step in enumerate(job["steps"]):
                self.context["job"] = {"status": "cancelled" if self.cancelled else "failure" if self.failed else "success"}
                identifier = step.get("id", f"step_{ordinal}")
                if not self.expression(step.get("if", "success()")):
                    self.context["steps"][identifier] = {"outcome": "skipped", "outputs": {}}
                    continue
                outputs, failed = {}, False
                env = base | {key: self.expand(value) for key, value in step.get("env", {}).items()}
                if "uses" in step:
                    action, pin = step["uses"].split("@")
                    if not re.fullmatch(r"[0-9a-f]{40}", pin):
                        raise AssertionError("unpinned action")
                    inputs = {key: self.expand(value) for key, value in step.get("with", {}).items()}
                    if action == "actions/checkout":
                        if inputs.get("persist-credentials") is not False or inputs.get("submodules") is not False:
                            raise AssertionError("unsafe controller checkout")
                        failed = phase == self.fail_checkout
                    elif action == "astral-sh/setup-uv":
                        if phase not in {"bump", "scan"} or inputs.get("enable-cache") is not False or inputs.get("version") != "0.13.7":
                            raise AssertionError("uv or cache enabled in App job")
                        failed = self.fail_tool == (phase, identifier)
                    elif action == "actions/setup-node":
                        if phase != "scan" or inputs.get("node-version") != "24" or inputs.get("package-manager-cache") is not False or "cache" in inputs:
                            raise AssertionError("unsafe detector runtime or package cache")
                        failed = self.fail_tool == (phase, identifier)
                    elif action == "actions/create-github-app-token":
                        scopes = inputs.get("repositories", "").split(",")
                        if self.cancelled or phase != "delivery-wait" or scopes != ["Hexalith.CiCd", *self.w.modules]:
                            raise AssertionError("invalid observer mint target or cancellation")
                        if inputs.get("skip-token-revoke") is not True or inputs.get("permission-actions") != "read":
                            raise AssertionError("invalid observer token lifecycle/permissions")
                        if any(k.startswith("permission-") and k != "permission-actions" for k in inputs):
                            raise AssertionError("observer token gained write access")
                        self.mints.append((phase, identifier, self.w.clock(), inputs))
                        self.w.advance(1)
                        failed = identifier in self.mint_fail
                        if not failed:
                            token = "inert-" + identifier
                            self.tokens[token] = len(self.mints) - 1
                            outputs["token"] = token
                    elif action == "actions/upload-artifact":
                        path = artifact_path(inputs, self.context["github"]["workspace"])
                        failed = not path.exists()
                        if not failed:
                            if phase == "scan":
                                if not path.is_dir() or {item.name for item in path.iterdir()} != {"report.json", "summary.md"}:
                                    raise AssertionError("scan artifact lost its report or summary")
                                summary = (path / "summary.md").read_text()
                                if "inert-" in summary:
                                    raise AssertionError("token leaked in scan summary")
                                self.scan_summaries.append(summary)
                                data = json.loads((path / "report.json").read_bytes())
                            else:
                                data = json.loads(path.read_bytes())
                            if "inert-" in json.dumps(data):
                                raise AssertionError("token leaked in artifact")
                            self.uploads.append((phase, data))
                            outputs = {"artifact-id": str(7001 + len(self.uploads)), "artifact-digest": "a" * 64}
                    else:
                        raise AssertionError("unexpected action " + action)
                else:
                    command = shlex.split(step["run"])
                    if "${{" in step["run"]:
                        raise AssertionError("expression interpolation inside shell")
                    if command[:3] == ["python3", "-I", "-c"]:
                        self.w.outputs.unlink(missing_ok=True)
                        result = subprocess.run([sys.executable, *command[1:]], env=env, capture_output=True)
                        if result.stdout or result.stderr:
                            raise AssertionError("inline controller leaked output")
                        failed = result.returncode != 0
                        if identifier == "boundary" and not failed:
                            # The real inline command is wall-clock based; represent
                            # the action boundary on this fixture's fake clock.
                            outputs["mint_epoch"] = str(self.w.clock())
                    elif phase == self.fail_checkout:
                        failed = True
                    else:
                        failed, outputs = self.controller_call(phase, command, env)
                outcome = "failure" if failed else "success"
                self.context["steps"][identifier] = {"outcome": outcome, "outputs": outputs}
                if failed and not step.get("continue-on-error", False):
                    self.failed = True
                if self.cancel_after == (phase, identifier):
                    self.cancelled = True
            self.results[phase] = "failure" if self.failed else "success"
            self.context["needs"][phase] = {"result": self.results[phase], "outputs": {
                key: self.expand(value) for key, value in job.get("outputs", {}).items()}}
        failed_upstream = self.context["needs"]["publish-ready"]["result"] == "failure"
        return "failure" if failed_upstream or "failure" in self.results.values() else "success"


class PostReleaseWorkflowTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return Workspace(Path(temporary.name) / "workspace", ("Hexalith.Alpha", "Hexalith.Beta"))

    def test_success_and_failed_publication_both_reach_bump_and_keepalive(self):
        for publication in ("success", "failure"):
            workflow = PostReleaseWorkflow(self.fixture(), publication=publication)
            self.assertEqual(workflow.execute(), "failure" if publication == "failure" else "success")
            self.assertEqual(workflow.results, {"scan": "success", "bump": "success", "bump-push": "success",
                                               "delivery-wait": "success", "keepalive": "success"})
            self.assertEqual(workflow.context["needs"]["bump-push"]["outputs"]["candidate"], "b" * 40)
            self.assertEqual([phase for phase, _ in workflow.uploads], ["scan", "bump", "bump", "bump-push", "delivery-wait", "keepalive"])
            self.assertEqual([phase for phase, _, _, _ in workflow.extension_calls][:2], ["scan", "bump"])
            # The failed release job remains an independent red verdict in Actions.
            self.assertEqual(workflow.context["needs"]["publish-ready"]["result"], publication)

    def test_explicit_nochange_skips_push_and_observation_but_keeps_alive(self):
        workflow = PostReleaseWorkflow(self.fixture(), producer="no-change")
        self.assertEqual(workflow.execute(), "success")
        self.assertEqual(workflow.results, {"scan": "success", "bump": "success", "bump-push": "skipped",
                                           "delivery-wait": "skipped", "keepalive": "success"})
        self.assertEqual([phase for phase, _ in workflow.uploads], ["scan", "bump", "keepalive"])
        self.assertFalse(workflow.mints)

    def test_failed_and_missing_candidate_never_reach_writer_and_keepalive_continues(self):
        for producer in ("failure", "missing"):
            workflow = PostReleaseWorkflow(self.fixture(), producer=producer)
            workflow.execute()
            self.assertEqual(workflow.results["bump-push"], "skipped")
            self.assertEqual(workflow.results["delivery-wait"], "skipped")
            self.assertEqual(workflow.results["keepalive"], "success")
            self.assertEqual([value["result"] for phase, value in workflow.uploads if phase == "bump"], [producer])
            self.assertNotEqual(workflow.context["needs"]["bump"]["outputs"]["result"], "no-change")
            self.assertEqual(workflow.results["bump"], "failure")

    def test_unavailable_controllers_preserve_failed_reports_and_keepalive_independence(self):
        for phase in ("scan", "bump", "bump-push", "delivery-wait", "keepalive"):
            with self.subTest(phase=phase):
                workflow = PostReleaseWorkflow(self.fixture(), fail_checkout=phase)
                self.assertEqual(workflow.execute(), "failure")
                self.assertEqual(workflow.results[phase], "failure")
                self.assertIn(phase, [name for name, _ in workflow.uploads])
                if phase != "keepalive":
                    self.assertEqual(workflow.results["keepalive"], "success")

    def test_scan_failure_and_missing_report_stay_red_while_bump_continues(self):
        for scan in ("failure", "missing"):
            with self.subTest(scan=scan):
                workflow = PostReleaseWorkflow(self.fixture(), publication="failure", scan=scan)
                self.assertEqual(workflow.execute(), "failure")
                self.assertEqual(workflow.results["scan"], "failure")
                self.assertEqual(workflow.results["bump"], "success")
                self.assertEqual(workflow.results["keepalive"], "success")
                report = next(value for phase, value in workflow.uploads if phase == "scan")
                self.assertEqual(report["result"], "fail")
                self.assertTrue(workflow.scan_summaries)
                summary = (workflow.w.root / "summary.md").read_text()
                self.assertIn(workflow.scan_summaries[0], summary)

    def test_scan_tooling_failures_preserve_seed_and_summary(self):
        for tool in ("node", "uv"):
            with self.subTest(tool=tool):
                workflow = PostReleaseWorkflow(self.fixture(), fail_tool=("scan", tool))
                self.assertEqual(workflow.execute(), "failure")
                self.assertEqual(workflow.results["scan"], "failure")
                self.assertEqual(workflow.results["bump"], "success")
                self.assertEqual(workflow.results["keepalive"], "success")
                self.assertFalse(any(phase == "scan" for phase, _, _, _ in workflow.extension_calls))
                report = next(value for phase, value in workflow.uploads if phase == "scan")
                self.assertEqual(report["result"], "fail")
                # The seed carries the documented report shape, with no observations.
                self.assertEqual((report["schema"], report["modules"], report["findings"]),
                                 ("hexalith.duplicate-scan.v1", [], []))
                self.assertIn("coverage is unverified", workflow.scan_summaries[0])
                self.assertIn(workflow.scan_summaries[0], (workflow.w.root / "summary.md").read_text())

    def test_job_conditions_follow_github_needs_status_semantics(self):
        # Without !cancelled(), GitHub's implicit success() skips a job after a
        # failed need. The model observes both continuation guards.
        for job, configuration in (("scan", {"publication": "failure"}), ("bump", {"scan": "failure"})):
            with self.subTest(job=job):
                workflow = PostReleaseWorkflow(self.fixture(), **configuration)
                condition = workflow.document["jobs"][job]["if"]
                workflow.document["jobs"][job]["if"] = condition.replace("!cancelled() && ", "")
                workflow.execute()
                self.assertEqual(workflow.results[job], "skipped")
                self.assertEqual(workflow.results["keepalive"], "success")
        workflow = PostReleaseWorkflow(self.fixture(), publication="failure", scan="failure")
        self.assertEqual(workflow.execute(), "failure")
        self.assertEqual((workflow.results["scan"], workflow.results["bump"]), ("failure", "success"))

    def test_nonmain_and_cancelled_scan_skip_production_controller(self):
        workflow = PostReleaseWorkflow(self.fixture(), ref="refs/heads/other")
        workflow.execute()
        self.assertEqual(workflow.results["scan"], "skipped")
        self.assertFalse(workflow.extension_calls)
        workflow = PostReleaseWorkflow(self.fixture(), cancel_after=("scan", "checkout"))
        workflow.execute()
        self.assertFalse(any(phase == "scan" for phase, _, _, _ in workflow.extension_calls))
        self.assertEqual(workflow.results["bump"], "skipped")
        self.assertEqual(workflow.results["keepalive"], "skipped")
        self.assertIn("scan", [phase for phase, _ in workflow.uploads])

    def test_failed_push_or_propagation_remains_red_and_keeps_alive(self):
        for configuration in ({"push": "failure"}, {"propagation": "failure"}):
            workflow = PostReleaseWorkflow(self.fixture(), **configuration)
            self.assertEqual(workflow.execute(), "failure")
            self.assertEqual(workflow.results["keepalive"], "success")
            if "push" in configuration:
                self.assertEqual(workflow.results["delivery-wait"], "skipped")

    def test_confirmed_push_still_observes_when_explicit_dispatch_failed(self):
        workflow = PostReleaseWorkflow(self.fixture(), push="dispatch-failure")
        self.assertEqual(workflow.execute(), "failure")
        self.assertEqual(workflow.results["bump-push"], "failure")
        self.assertEqual(workflow.results["delivery-wait"], "success")
        self.assertTrue(workflow.mints)
        self.assertEqual(workflow.results["keepalive"], "success")

    def test_failed_mint_has_no_stale_fallback_four_slices_share_deadline(self):
        workflow = PostReleaseWorkflow(self.fixture(), mint_fail=("propagation_02_token",))
        self.assertEqual(workflow.execute(), "failure")
        polls = [call for call in workflow.extension_calls if call[0] == "delivery-wait" and call[1][-1] == "poll"]
        self.assertEqual(len(polls), 4)
        self.assertEqual(polls[1][2]["POLL_TOKEN"], "")
        self.assertEqual([mint[1] for mint in workflow.mints], [f"propagation_{i:02d}_token" for i in range(1, 5)])
        start = next(call[3] for call in workflow.extension_calls if call[0] == "delivery-wait" and call[1][-1] == "initialize")
        self.assertEqual(workflow.deadline - start, 90 * 60)
        self.assertEqual(workflow.w.clock(), workflow.deadline)
        self.assertEqual(workflow.results["keepalive"], "success")

    def test_qualification_is_main_only_and_bypasses_all_production_paths(self):
        for ref in ("refs/heads/main", "refs/heads/other"):
            workflow = PostReleaseWorkflow(self.fixture(), qualify=True, ref=ref)
            workflow.execute()
            self.assertFalse(workflow.mints)
            calls = [(phase, command) for phase, command, _, _ in workflow.extension_calls]
            self.assertEqual(calls, [("bump-push", ("python3", "-I", "tools/bump_push.py", "qualify"))]
                             if ref == "refs/heads/main" else [])
            self.assertEqual(workflow.results["scan"], "skipped")
            self.assertEqual(workflow.results["keepalive"], "skipped")

    def test_cancellation_stops_new_mints_and_writes_but_retains_reports(self):
        workflow = PostReleaseWorkflow(self.fixture(), cancel_after=("delivery-wait", "propagation_01_budget"))
        workflow.execute()
        self.assertFalse(workflow.mints)
        self.assertEqual(workflow.results["keepalive"], "skipped")
        self.assertIn("delivery-wait", [phase for phase, _ in workflow.uploads])
        self.assertFalse(any(call[1][-1] == "poll" for call in workflow.extension_calls))

    def test_exact_job_timeouts_and_controller_surface(self):
        document = yaml.safe_load((ROOT / ".github/workflows/nightly.yml").read_bytes())
        expected = {"dispatch": 55, "wait": 330, "publish-ready": 55,
                    "scan": 55, "bump": 55, "bump-push": 55, "delivery-wait": 105, "keepalive": 15}
        self.assertEqual({phase: job["timeout-minutes"] for phase, job in document["jobs"].items()}, expected)
        observer = document["jobs"]["delivery-wait"]
        self.assertEqual(len([step for step in observer["steps"] if "uses" in step
                              and step["uses"].startswith("actions/create-github-app-token@")]), 4)
        for step in observer["steps"]:
            if "run" in step:
                self.assertTrue(step["run"].startswith("python3 -I "))
                self.assertNotIn("uv run", step["run"])


if __name__ == "__main__":
    unittest.main()
