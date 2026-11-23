#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Execute real workflow mappings; replace external actions and I/O boundaries.

The controller and immutable bootstrap commands execute in isolated Python
children. Git fixtures use real remotes and the released v5.1.0 library; this
harness does not replace scripts with expected reports or a perimeter stand-in.
"""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
import io
from types import SimpleNamespace
import unittest
from unittest import mock
from datetime import datetime, timezone

import yaml
from delivery_support import ROOT, Workspace, bootstrap_source, git, load

scope_checks = load(ROOT / "tools/change_scope.py", "_workflow_change_scope")


class GithubString(str):
    """GitHub expression equality ignores string case; outputs preserve it."""
    def __eq__(self, other):
        return self.casefold() == other.casefold() if isinstance(other, str) else super().__eq__(other)

    def __ne__(self, other):
        return not self == other


class Workflow:
    def __init__(self, workspace, *, ref="refs/heads/main", event="push", validation="success", verdict=None,
                 mint_fail=(), cancel_after=None, delivery="full", g6_plan=None, job="deliver",
                 suite_result="success", checkout_fail=False, scope=None, classification="full",
                 builds_checkout_fail=False, scope_fail=False):
        self.w = workspace
        self.document = yaml.safe_load((ROOT / ".github/workflows/deliver.yml").read_bytes())
        self.job = self.document["jobs"][job]
        self.job_name = job
        self.suite_result = suite_result
        self.checkout_fail = checkout_fail
        self.classification = classification
        self.builds_checkout_fail = builds_checkout_fail
        self.scope_fail = scope_fail
        self.context = {"github": {"ref": ref, "sha": workspace.sha, "repository": "Hexalith/Hexalith.CiCd",
            "workspace": str(workspace.root), "run_id": "101", "run_attempt": "1", "event_name": event, "token": "inert-checkout-token"},
            "needs": {"validate": {"result": validation, "outputs": {"verdict": json.dumps(verdict) if verdict is not None else ""}}},
            "steps": {}, "inputs": {"delivery": delivery}, "runner": {"temp": str(workspace.root)},
            "secrets": {"HEXALITH_CICD_APP_PRIVATE_KEY": "inert-no-private-key"},
            "vars": {"HEXALITH_CICD_APP_CLIENT_ID": "inert-client-id"}}
        # Model validation at its I/O boundary, then evaluate the real job's
        # output mapping even when that job's result is failure.
        self.context["steps"] = {"validate": {"outputs": self.context["needs"]["validate"]["outputs"]},
                                 "scope": {"outputs": {"scope": scope or "", "skip_checks": str(scope_checks.skip_checks(scope, event))}},
                                 "g6_qualify": {"outputs": {"plan": json.dumps(g6_plan) if g6_plan else ""}}}
        self.context["needs"]["validate"]["outputs"] = {
            key: self.expand(value) for key, value in self.document["jobs"]["validate"].get("outputs", {}).items()}
        self.context["steps"] = {}
        self.mint_fail = set(mint_fail)
        self.actions, self.commands, self.uploads = [], [], []
        self.failed = False
        self.cancelled = validation == "cancelled"
        self.cancel_after = cancel_after
        self.mints, self.processes, self.checkouts = [], [], []

    def lookup(self, path):
        value = self.context
        for part in path.split("."):
            value = value.get(part, "") if isinstance(value, dict) else ""
        return value

    def expression(self, value):
        value = value.strip()
        if value.startswith("${{"):
            value = value[3:-2].strip()
        tokens = re.findall(r"'(?:[^']|'')*'|[A-Za-z_][A-Za-z0-9_.]*|&&|\|\||==|!=|!|\(|\)|,", value)
        result = []
        for token in tokens:
            if token.startswith("'"):
                result.append("string(" + repr(token[1:-1].replace("''", "'")) + ")")
            elif token in {"&&", "||", "!"}:
                result.append({"&&": "and", "||": "or", "!": "not"}[token])
            elif token in {"==", "!=", "(", ")", ","}:
                result.append(token)
            elif token in {"always", "success", "failure", "cancelled", "format"}:
                result.append(token)
            elif token in {"true", "false"}:
                result.append("True" if token == "true" else "False")
            else:
                actual = self.lookup(token)
                result.append("string(" + repr(actual) + ")" if isinstance(actual, str) else repr(actual))
        return eval(" ".join(result), {"__builtins__": {}}, {"always": lambda: True,
            "success": lambda: not self.failed and not self.cancelled, "failure": lambda: self.failed, "cancelled": lambda: self.cancelled,
            "format": lambda pattern, value: pattern.format(value), "string": GithubString})

    def expand(self, value):
        if not isinstance(value, str):
            return value
        return re.sub(r"\$\{\{(.*?)\}\}", lambda m: str(self.expression(m.group(1))), value)

    def condition(self, value):
        # GitHub inserts success() unless an explicit status function occurs.
        if not re.search(r"\b(?:always|cancelled|failure|success)\s*\(", value):
            if self.failed or self.cancelled:
                return False
        return self.expression(value)

    def finish_step(self, identifier, step, outcome, outputs):
        self.context["steps"][identifier] = {"outcome": outcome, "outputs": outputs}
        if outcome == "failure" and not step.get("continue-on-error", False):
            self.failed = True
        if self.cancel_after is not None and self.cancel_after in (identifier, step.get("name")):
            self.cancelled = True

    def execute(self):
        triggers = self.document.get("on", self.document.get(True))
        event, ref = self.context["github"]["event_name"], self.context["github"]["ref"]
        if event not in triggers or (event == "push" and ref.removeprefix("refs/heads/") not in triggers["push"]["branches"]):
            return "not-triggered"
        concurrency = self.document["concurrency"]
        self.concurrency_group = self.expression(concurrency["group"])
        self.cancel_in_progress = self.expression(concurrency["cancel-in-progress"])
        writer = self.job.get("concurrency")
        self.writer_concurrency_group = self.expand(writer["group"]) if writer else None
        self.writer_cancel_in_progress = self.expand(writer["cancel-in-progress"]) if writer else None
        self.validation_entered = True
        if not self.condition(self.job.get("if", "success()")):
            return "skipped"
        base = self.w.env()
        if self.job_name == "validate":
            base.pop("MODULE_TOKEN", None)
            base.pop("CICD_TOKEN", None)
        base.update({"GITHUB_" + key.upper(): str(value) for key, value in self.context["github"].items() if key != "token"})
        base.update({key: self.expand(value) for key, value in self.job.get("env", {}).items()})
        self.context["env"] = base
        for ordinal, step in enumerate(self.job["steps"]):
            identifier = step.get("id", f"step_{ordinal}")
            if not self.condition(step.get("if", "success()")):
                self.context["steps"][identifier] = {"outcome": "skipped", "outputs": {}}
                continue
            outputs, outcome = {}, "success"
            if "uses" in step:
                inputs = {key: self.expand(value) for key, value in step.get("with", {}).items()}
                self.actions.append((step["uses"], inputs))
                action = step["uses"].split("@", 1)[0]
                if action == "actions/checkout":
                    source = inputs.get("ref", "")
                    if self.job_name == "validate":
                        # Candidate bytes already exist in this real Git fixture;
                        # only the external checkout action is substituted.
                        if step.get("id") == "cicd" and self.checkout_fail:
                            outcome = "failure"
                        if inputs.get("repository") == "Hexalith/Hexalith.Builds" and self.builds_checkout_fail:
                            outcome = "failure"
                        self.checkouts.append(inputs)
                        self.finish_step(identifier, step, outcome, outputs)
                        continue
                    if inputs.get("path") == ".g6-owner":
                        if self.checkout_fail:
                            self.finish_step(identifier, step, "failure", outputs)
                            continue
                        if source != self.w.sha or inputs.get("persist-credentials") is not False or inputs.get("submodules") is not False:
                            raise AssertionError("narrow checkout changed qualified source/credentials")
                        destination = self.w.root / inputs["path"]
                        paths = git(self.w.candidate, "ls-tree", "-r", "--name-only", source).splitlines()
                        selected = [path for path in paths if any(path == prefix or path.startswith(prefix + "/")
                                    for prefix in inputs["sparse-checkout"].splitlines())]
                        for path in selected:
                            target = destination / path
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(subprocess.run(["git", "-C", str(self.w.candidate), "show",
                                                source + ":" + path], check=True, capture_output=True).stdout)
                        self.checkouts.append(sorted(selected))
                        self.finish_step(identifier, step, outcome, outputs)
                        continue
                    anchor = json.loads((ROOT / "tools/tests/fixtures/delivery-bootstrap.json").read_bytes())
                    if not re.fullmatch(r"[0-9a-f]{40}", source) or source != anchor["source_sha"]:
                        raise AssertionError("selector checkout is not immutable")
                    if inputs.get("persist-credentials") is not False or inputs.get("submodules") is not False:
                        raise AssertionError("unsafe checkout")
                    destination = self.w.root / inputs["path"]
                    for path in inputs.get("sparse-checkout", "").splitlines():
                        if not path or path.startswith("/") or ".." in Path(path).parts:
                            raise AssertionError("noncanonical sparse path")
                        data = bootstrap_source(source, path)
                        if hashlib.sha256(data).hexdigest() != anchor["files"][path]:
                            raise AssertionError("bootstrap bytes do not match immutable source manifest")
                        target = destination / path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(data)
                    self.checkouts.append(sorted(p.relative_to(destination).as_posix()
                                                 for p in destination.rglob("*") if p.is_file()))
                elif action == "actions/create-github-app-token":
                    repository = inputs.get("repositories")
                    self.mints.append((identifier, inputs.copy()))
                    if inputs.get("owner") != "Hexalith" or not repository or "," in repository or "\n" in repository:
                        raise AssertionError("mint broadened beyond one explicit repository")
                    if inputs.get("permission-contents") != "write" or inputs.get("permission-workflows") != "write":
                        raise AssertionError("mint lacks required Contents/Workflows write permissions")
                    if repository == "Hexalith.CiCd" and inputs.get("permission-actions") != "read":
                        raise AssertionError("CiCd mint lacks Actions read permission")
                    if repository in self.mint_fail:
                        outcome = "failure"
                    else:
                        outputs["token"] = "inert-token-" + repository
                elif action == "actions/upload-artifact":
                    artifact = Path(inputs["path"])
                    if not artifact.is_absolute():
                        artifact = self.w.root / artifact
                    if not artifact.is_file():
                        self.finish_step(identifier, step, "failure", outputs)
                        continue
                    self.uploads.append((inputs["name"], artifact.read_bytes()))
                elif action == "astral-sh/setup-uv" and self.job_name == "validate":
                    pass
                else:
                    raise AssertionError("unhandled external action " + action)
            elif "run" in step:
                env = base | {key: self.expand(value) for key, value in step.get("env", {}).items()}
                if identifier == "scope" and self.job_name == "validate":
                    self.commands.append(shlex.split(step["run"]))
                    outputs = {} if self.scope_fail else {"scope": self.classification,
                        "skip_checks": str(scope_checks.skip_checks(self.classification, env.get("CHANGE_SCOPE_EVENT", "")))}
                    self.finish_step(identifier, step, "failure" if self.scope_fail else "success", outputs)
                    continue
                if identifier == "validate" and self.job_name == "validate":
                    command = shlex.split(step["run"])
                    self.assert_validation_command(command)
                    self.commands.append(command)
                    outputs = {"verdict": json.dumps({"global": True, "modules": []})}
                    self.finish_step(identifier, step, "success", outputs)
                    continue
                if identifier == "g6_tests" and self.job_name == "validate":
                    self.finish_step(identifier, step, self.suite_result, outputs)
                    continue
                command = shlex.split(step["run"])
                if command[2:3] in ([".g6-owner/tools/deliver_g6_catalog.py"], ["tools/deliver_g6_catalog.py"]):
                    command[command.index("--report") + 1] = str(self.w.root / command[command.index("--report") + 1])
                if command[:2] != ["python3", "-I"] or "${{" in step["run"]:
                    raise AssertionError("privileged command is not isolated Python")
                self.commands.append(command)
                self.w.outputs.unlink(missing_ok=True)
                if command[3:4] == ["module"]:
                    self.processes.append({"name": step["name"], "slot": int(command[command.index("--slot") + 1]),
                                           "token": env.get("MODULE_TOKEN", "")})
                source = self.w.candidate / command[2] if self.job_name == "validate" else self.w.root / command[2]
                result = self.w.call(str(source), command[3:], env=env) if source.is_file() else 1
                if result:
                    outcome = "failure"
                if self.w.outputs.exists():
                    outputs = dict(line.split("=", 1) for line in self.w.outputs.read_text().splitlines())
            else:
                raise AssertionError("step has neither action nor command")
            self.finish_step(identifier, step, outcome, outputs)
        return "failure" if self.failed else "success"

    @staticmethod
    def assert_validation_command(command):
        if command != ["uv", "run", "--locked", "--script", "tools/validate.py", "--scope", "$CICD_CHANGE_SCOPE"]:
            raise AssertionError("validation must pass scope through a quoted environment variable")


class WorkflowTests(unittest.TestCase):
    def test_explicit_push_none_skips_writer_tokens_and_ref_changes(self):
        w = self.fixture()
        w.ref("Hexalith.Alpha")
        before = git(w.remote, "for-each-ref", "refs/heads/delivered/")
        workflow = Workflow(w, scope="none", verdict={"global": True, "modules": []})
        self.assertEqual("skipped", workflow.execute())
        self.assertEqual([], workflow.commands + workflow.actions + workflow.mints + workflow.uploads)
        self.assertEqual(before, git(w.remote, "for-each-ref", "refs/heads/delivered/"))

    def test_failed_validation_keeps_repair_regardless_of_scope(self):
        for scope in (None, "", "unknown", "NONE", "none"):
            with self.subTest(scope=scope):
                w = self.fixture()
                w.ref("Hexalith.Alpha")
                workflow, report = self.run_workflow(w, scope=scope, validation="failure")
                self.assertTrue(report["failed"])
                self.assertEqual("pushed", report["modules"][0]["application"])
                self.assertTrue(workflow.mints)

    def test_scheduled_none_keeps_delivery_freshness_and_accepted_repairs(self):
        w = self.fixture()
        for name in w.modules:
            w.ref(name)
        (w.candidate / "README.md").write_text("Prose candidate only.\n")
        w.commit()
        prefix = "/repos/Hexalith/Hexalith.CiCd/actions/"
        w.config["api"][prefix + "workflows"] = [{"path": ".github/workflows/nightly.yml", "id": 1}]
        w.config["api"][prefix + "workflows/1/runs?branch=main&per_page=1&page=1"] = {
            "total_count": 1, "workflow_runs": [{
                "path": ".github/workflows/nightly.yml", "id": 2, "head_branch": "main",
                "created_at": datetime.now(timezone.utc).isoformat(), "conclusion": "success",
            }],
        }
        workflow, report = self.run_workflow(w, scope="none", event="schedule",
                                             verdict={"global": True, "modules": w.modules})
        self.assertFalse(report["failed"], report)
        self.assertEqual("fresh", report["freshness"]["status"])
        for row in report["modules"]:
            self.assertEqual(("advanced", "pushed", w.sha),
                             (row["advancement"], row["application"], row["accepted_sha"]))
            module = row["repository"]
            self.assertEqual(git(w.candidate, "show", f"{w.accepted}:rendered/{module}/.github/workflows/ci.yml"),
                             git(w.remotes[module], "show", "main:.github/workflows/ci.yml"))
        self.assertEqual(["Hexalith.CiCd", *w.modules], [inputs["repositories"] for _, inputs in workflow.mints])

    def test_validation_classifies_before_builds_and_only_pr_push_none_omit_it(self):
        for event, scope in (("push", "none"), ("pull_request", "none"), ("schedule", "none"),
                             ("push", "module"), ("push", "full"), ("push", ""), ("push", "unknown"), ("push", "NONE")):
            with self.subTest(event=event, scope=scope):
                workflow = Workflow(self.fixture(()), event=event, job="validate", classification=scope)
                self.assertEqual("success", workflow.execute())
                self.assertEqual(["python3", "-I", "tools/change_scope.py"], workflow.commands[0])
                self.assertEqual(scope, workflow.lookup("steps.scope.outputs.scope"))
                builds = [checkout for checkout in workflow.checkouts if checkout.get("repository") == "Hexalith/Hexalith.Builds"]
                self.assertEqual(0 if scope == "none" and event in ("push", "pull_request") else 1, len(builds))
                self.assertEqual("success", workflow.lookup("steps.validate.outcome"))
                self.assertEqual([], workflow.mints)

    def test_expression_equality_matches_github_case_insensitive_strings(self):
        workflow = Workflow(self.fixture(()), scope="NONE")
        self.assertTrue(workflow.expression("'NONE' == 'none'"))
        self.assertFalse(workflow.expression("needs.validate.outputs.scope != 'none'"))
        self.assertTrue(workflow.expression("needs.validate.outputs.skip_checks != '1'"))

    def test_classifier_or_builds_failure_retains_conservative_validation(self):
        for options in ({"scope_fail": True}, {"builds_checkout_fail": True}):
            with self.subTest(options=options):
                workflow = Workflow(self.fixture(()), job="validate", **options)
                self.assertEqual("failure", workflow.execute())
                self.assertEqual("success", workflow.lookup("steps.validate.outcome"))
                if options.get("scope_fail"):
                    self.assertEqual("", workflow.lookup("steps.scope.outputs.scope"))

    def test_shallow_checkout_uses_frozen_pinned_bootstrap_bytes(self):
        import delivery_support
        original = delivery_support.subprocess.run
        def shallow(command, *args, **kwargs):
            if command[:4] == ["git", "-C", str(ROOT), "show"]:
                return type("MissingObject", (), {"returncode": 128})()
            return original(command, *args, **kwargs)
        w = self.fixture(())
        with mock.patch.object(delivery_support.subprocess, "run", side_effect=shallow):
            _, report = self.run_workflow(w, verdict={"global": True, "modules": []})
        self.assertFalse(report["failed"])

    def fixture(self, modules=("Hexalith.Alpha", "Hexalith.Beta")):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return Workspace(Path(temporary.name) / "workspace", modules)

    def run_workflow(self, w, **kwargs):
        workflow = Workflow(w, **kwargs)
        outcome = workflow.execute()
        self.assertEqual(len(workflow.uploads), 1)
        self.assertEqual(workflow.uploads[0][0], "hexalith-delivery")
        report = json.loads(workflow.uploads[0][1])
        self.assertEqual(report["failed"], outcome == "failure")
        self.assertNotIn(b"inert-", workflow.uploads[0][1])
        return workflow, report

    def test_main_after_validation_success_and_failure_with_valid_global(self):
        for validation in ("success", "failure"):
            with self.subTest(validation=validation):
                w = self.fixture()
                workflow, report = self.run_workflow(w, validation=validation,
                    verdict={"global": True, "modules": w.modules})
                self.assertFalse(report["failed"], report)
                self.assertEqual([r["application"] for r in report["modules"]], ["pushed", "pushed"])
                self.assertTrue(all(r["advancement"] == "advanced" for r in report["modules"]))
                module_mints = [inputs for _, inputs in workflow.mints if inputs["repositories"] != "Hexalith.CiCd"]
                self.assertEqual([inputs["permission-administration"] for inputs in module_mints], ["read", "read"])
                self.assertEqual(workflow.checkouts, [["tools/delivery_bootstrap.py", "tools/delivery_runtime.py"]])

    def test_missing_validation_uses_accepted_tools_and_repairs(self):
        w = self.fixture()
        w.ref("Hexalith.Alpha")
        workflow, report = self.run_workflow(w, validation="failure")
        self.assertTrue(report["failed"])
        self.assertFalse(report["global"])
        self.assertEqual(report["modules"][0]["application"], "pushed")
        for action, inputs in workflow.actions:
            if action.startswith("actions/create-github-app-token") and inputs["repositories"] != "Hexalith.CiCd":
                self.assertEqual(inputs["permission-administration"], "")

    def test_pr_excludes_privileged_job(self):
        workflow = Workflow(self.fixture(), ref="refs/pull/1/merge", event="pull_request")
        self.assertEqual(workflow.execute(), "skipped")
        self.assertEqual(workflow.commands + workflow.actions + workflow.uploads, [])
        self.assertTrue(workflow.validation_entered)
        self.assertEqual(workflow.concurrency_group, "deliver-validate-refs/pull/1/merge")
        self.assertTrue(workflow.cancel_in_progress)

    def test_individual_mint_and_cicd_mint_failures_do_not_suppress_slots(self):
        w = self.fixture()
        w.ref("Hexalith.Beta")
        workflow, report = self.run_workflow(w, mint_fail=("Hexalith.Alpha", "Hexalith.CiCd"),
            verdict={"global": True, "modules": w.modules})
        self.assertEqual(report["modules"][0]["application"], "failed")
        self.assertEqual(report["modules"][1]["application"], "pushed")
        self.assertIn("Hexalith.Beta", [i["repositories"] for a, i in workflow.actions if a.startswith("actions/create-github-app-token")])

    def test_actual_controller_crash_isolated_and_artifact_still_uploaded(self):
        w = self.fixture()
        path = w.candidate / "tools/deliver.py"
        path.write_text(path.read_text().replace("args = parser.parse_args(argv)",
            'args = parser.parse_args(argv)\n    if args.operation == "module" and args.slot == 1:\n        raise RuntimeError("fixture controller failure")'))
        w.commit()
        workflow, report = self.run_workflow(w, verdict={"global": True, "modules": w.modules})
        self.assertEqual(report["modules"][0]["application"], "failed")
        self.assertEqual(report["modules"][1]["application"], "pushed")

    def test_empty_slots_no_module_mint_and_all_main_events(self):
        for event in ("push", "schedule", "workflow_dispatch"):
            with self.subTest(event=event):
                w = self.fixture(())
                workflow, report = self.run_workflow(w, event=event, verdict={"global": True, "modules": []})
                self.assertFalse(report["failed"], report)
                self.assertEqual(workflow.concurrency_group, "deliver")
                self.assertFalse(workflow.cancel_in_progress)
                minted = [i["repositories"] for a, i in workflow.actions if a.startswith("actions/create-github-app-token")]
                self.assertEqual(minted, ["Hexalith.CiCd"])
                self.assertEqual(git(w.remote, "for-each-ref", "refs/heads/delivered/"), "")

    def test_full_capacity_keeps_each_repository_token_and_slot_together(self):
        w = self.fixture(tuple(f"Hexalith.Module{index:02d}" for index in range(1, 18)))
        workflow, report = self.run_workflow(w, verdict={"global": True, "modules": w.modules})
        self.assertEqual(len(report["modules"]), 17)
        self.assertTrue(all(row["processed"] and row["application"] == "pushed" for row in report["modules"]))
        module_mints = [(identifier, inputs) for identifier, inputs in workflow.mints
                        if inputs["repositories"] != "Hexalith.CiCd"]
        self.assertEqual(len(module_mints), 17)
        self.assertEqual(len(workflow.processes), 17)
        for slot, ((identifier, inputs), process) in enumerate(zip(module_mints, workflow.processes), 1):
            repository = workflow.lookup(f"steps.select.outputs.slot_{slot:02d}")
            self.assertEqual(identifier, f"module_{slot:02d}_token")
            self.assertEqual(inputs["repositories"], repository)
            self.assertEqual(inputs["permission-administration"], "read")
            self.assertEqual(process["slot"], slot)
            self.assertEqual(process["token"], "inert-token-" + repository)

    def test_cancel_stops_later_mints_and_writes_but_finalizes_and_uploads(self):
        for after, processed in (("select", 0), ("cicd_token", 0), ("module_01_budget", 0), ("Process module slot 01", 1)):
            with self.subTest(after=after):
                w = self.fixture()
                before = {r: git(Path(p), "rev-parse", "main") for r, p in w.remotes.items()}
                workflow, report = self.run_workflow(w, cancel_after=after,
                    verdict={"global": True, "modules": w.modules})
                self.assertTrue(workflow.cancelled)
                self.assertTrue(report["failed"])
                if after == "module_01_budget":
                    self.assertEqual(workflow.lookup("steps.module_01_budget.outputs.active"), "true")
                self.assertEqual(len(workflow.processes), processed)
                module_mints = [i for _, i in workflow.mints if i["repositories"] != "Hexalith.CiCd"]
                self.assertEqual(len(module_mints), processed)
                for row in report["modules"][processed:]:
                    self.assertEqual(row["application"], "failed")
                    self.assertIn("module slot did not complete", row["reasons"])
                    self.assertEqual(git(Path(w.remotes[row["repository"]]), "rev-parse", "main"), before[row["repository"]])
                    self.assertEqual(git(w.remote, "for-each-ref", "refs/heads/delivered/" + row["repository"]), "")
        workflow = Workflow(self.fixture(), validation="cancelled")
        self.assertEqual(workflow.execute(), "skipped")
        self.assertEqual(workflow.actions, [])

    def test_overflow_and_source_failure_upload_failed_report_without_mints(self):
        w = self.fixture(())
        for index in range(18):
            (w.candidate / "setup" / f"Fixture{index}.yml").write_text("{}\n")
        w.commit()
        workflow, report = self.run_workflow(w, verdict={"global": True, "modules": []})
        self.assertTrue(report["failed"])
        self.assertEqual([a for a, _ in workflow.actions if a.startswith("actions/create-github-app-token")], [])
        self.assertIn("exceeds 17", " ".join(report["failures"]))
        w = self.fixture(())
        workflow, report = self.run_workflow(w, validation="failure")
        self.assertTrue(report["failed"])
        self.assertIsNone(report["tools_source_sha"])


class WorkflowBoundaryTests(unittest.TestCase):
    def test_actual_workflow_env_and_arguments_reach_classifier_and_validator(self):
        # Reuse the validator's existing exact dependency lock in disposable
        # scratch; this workflow suite keeps its own PyYAML-only environment.
        with tempfile.TemporaryDirectory(prefix="workflow-scope-cli-") as directory:
            driver = Path(directory) / "boundary.py"
            metadata = re.search(r"(?ms)^# /// script\n.*?^# ///\n", (ROOT / "tools/validate.py").read_text()).group()
            driver.write_text(metadata + "import sys\n"
                + f"sys.path.insert(0, {str(Path(__file__).parent)!r})\n"
                + "from test_delivery_workflow import WorkflowBoundaryTests\n"
                + "WorkflowBoundaryTests().assert_cli_boundary()\n")
            shutil.copyfile(ROOT / "tools/validate.py.lock", Path(str(driver) + ".lock"))
            result = subprocess.run(["uv", "run", "--locked", "--script", "--python", "3.12", str(driver)],
                                    capture_output=True, timeout=180)
            self.assertEqual(0, result.returncode, (result.stdout + result.stderr).decode(errors="replace"))

    def assert_cli_boundary(self):
        # Only network Git transport, anonymous live-module clones and the
        # global child process are substituted. Both real CLIs, Git trees,
        # schema readers, module loop and verdict output execute unchanged.
        import test_validate as fixtures
        with fixtures.workspace() as fixture:
            fixture.module("Hexalith.Alpha")
            fixture.module("Hexalith.Beta")
            fixture.commit()
            baseline = git(fixture.root, "rev-parse", "HEAD")
            accepted_input = fixture.root / "tools/accepted.py"
            accepted_input.parent.mkdir(exist_ok=True)
            accepted_input.write_text("# Only the accepted branch has this shared input.\n")
            git(fixture.root, "add", "--", str(accepted_input))
            git(fixture.root, "commit", "--quiet", "-m", "Different accepted baseline")
            different_accepted = git(fixture.root, "rev-parse", "HEAD")
            cases = (("pull_request", "README.md", "none", "complete"),
                     ("push", "README.md", "none", "complete"),
                     ("push", "setup/Hexalith.Alpha.yml", "module", "complete"),
                     ("push", "tools/shared.py", "full", "complete"),
                     ("schedule", "README.md", "none", "complete"),
                     ("workflow_dispatch", "README.md", "full", "complete"),
                     ("push", "README.md", "full", "missing"),
                     ("push", "README.md", "full", "missing-skip"))
            for event, path, expected, output_shape in cases:
                with self.subTest(event=event, path=path, output_shape=output_shape):
                    git(fixture.root, "reset", "--hard", baseline)
                    changed = fixture.root / path
                    changed.parent.mkdir(parents=True, exist_ok=True)
                    changed.write_text((changed.read_text() if changed.exists() else "") + "\n# candidate\n")
                    git(fixture.root, "add", "--", path)
                    git(fixture.root, "commit", "--quiet", "-m", "Boundary candidate")
                    candidate = git(fixture.root, "rev-parse", "HEAD")
                    workflow = Workflow(SimpleNamespace(root=fixture.root, sha=candidate), event=event, job="validate")
                    workflow.context["github"]["event"] = {"pull_request": {"base": {"sha": baseline}}}
                    steps = {step.get("id"): step for step in workflow.job["steps"] if "id" in step}
                    environment = {key: value for key, value in os.environ.items()
                                   if not key.startswith("CHANGE_SCOPE_") and key not in ("CICD_CHANGE_SCOPE", "GITHUB_OUTPUT")}
                    environment["GITHUB_EVENT_NAME"] = event
                    output = fixture.root.parent / "scope-output"
                    output.unlink(missing_ok=True)
                    scope_env = environment | {key: workflow.expand(value) for key, value in steps["scope"]["env"].items()}
                    scope_env["GITHUB_OUTPUT"] = str(output)
                    command = shlex.split(steps["scope"]["run"])
                    self.assertEqual(["python3", "-I"], command[:2])
                    classifier = load(ROOT / command[2], "_boundary_scope")
                    original_git = classifier.git
                    baseline_calls = []

                    def anonymous(project, *arguments):
                        if arguments[0] == "ls-remote":
                            baseline_calls.append(("ls-remote",))
                            discovered = different_accepted if event == "pull_request" else baseline
                            return f"{discovered}\trefs/heads/delivered/Hexalith.Alpha\n".encode()
                        if arguments[0] == "fetch":
                            baseline_calls.append(("fetch", arguments[-1]))
                            return fixtures.git(project, "fetch", "--quiet", "--no-tags", "--depth=1", str(fixture.root), arguments[-1])
                        return original_git(project, *arguments)
                    with (mock.patch.object(classifier, "git", side_effect=anonymous),
                          mock.patch.dict(os.environ, scope_env, clear=True), redirect_stdout(io.StringIO()) as stdout,
                          redirect_stderr(io.StringIO())):
                        self.assertEqual(0, classifier.main([*command[3:], "--project-root", str(fixture.root)]))
                    classify_expected = expected if output_shape == "complete" else "none"
                    self.assertEqual(classify_expected + "\n", stdout.getvalue())
                    if event == "pull_request":
                        self.assertEqual([("fetch", baseline)], baseline_calls)
                    outputs = dict(line.split("=", 1) for line in output.read_text().splitlines())
                    self.assertEqual(str(int(classify_expected == "none" and event in ("push", "pull_request"))),
                                     outputs["skip_checks"])
                    if output_shape == "missing":
                        outputs = {}
                    elif output_shape == "missing-skip":
                        del outputs["skip_checks"]
                    workflow.context["steps"]["scope"] = {
                        "outputs": outputs, "outcome": "failure" if output_shape == "missing" else "success",
                    }
                    validate_env = environment | {key: workflow.expand(value) for key, value in steps["validate"]["env"].items()}
                    # Let a real shell expand the actual quoted CLI argument,
                    # including the empty-string behavior when wiring is lost.
                    expanded = subprocess.run(["bash", "-c", 'set -- ' + steps["validate"]["run"] + '\nprintf "%s\\0" "$@"'],
                                              env=validate_env, capture_output=True, check=True).stdout
                    arguments = [item.decode() for item in expanded.split(b"\0")[:-1]]
                    self.assertEqual(["uv", "run", "--locked", "--script", "tools/validate.py"], arguments[:5])
                    validator = fixtures.validator
                    original_command = validator.checks.command
                    global_calls = []
                    def external_child(arguments, **options):
                        if arguments[0] == "uv":
                            global_calls.append(list(map(str, arguments)))
                            return b""
                        return original_command(arguments, **options)
                    fixture.cloned.clear()
                    with (mock.patch.object(validator.checks, "command", side_effect=external_child),
                          mock.patch.object(validator, "clone_module", side_effect=fixture.clone),
                          mock.patch.dict(os.environ, validate_env, clear=True),
                          mock.patch.object(sys, "argv", [arguments[4], *arguments[5:], "--project-root", str(fixture.root)]),
                          redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO())):
                        self.assertEqual(0, validator.main())
                    fast = expected == "none" and event in ("push", "pull_request")
                    modules = [] if fast else ["Hexalith.Alpha", "Hexalith.Beta"]
                    self.assertEqual({"global": True, "modules": modules}, json.loads(stdout.getvalue()))
                    self.assertEqual(modules, fixture.cloned)
                    self.assertEqual(0 if fast else 1, len(global_calls))
                    if not fast:
                        if expected in ("none", "module"):
                            self.assertEqual(["--scope", expected], global_calls[0][-2:])
                        else:
                            self.assertNotIn("--scope", global_calls[0])


class EvidenceWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = yaml.safe_load((ROOT / ".github/workflows/evidence.yml").read_bytes())
        cls.evidence = cls.document["jobs"]["evidence"]

    def test_evidence_runs_only_on_pull_requests_and_main_pushes_with_exact_event_inputs(self):
        self.assertEqual({"push": {"branches": ["main"]}, "pull_request": None},
                         self.document.get("on", self.document.get(True)))
        fixture = SimpleNamespace(root=ROOT, sha="a" * 40)
        for event, ref in (("pull_request", "refs/pull/1/merge"), ("push", "refs/heads/main")):
            with self.subTest(event=event):
                workflow = Workflow(fixture, event=event, ref=ref)
                pr_base = "b" * 40 if event == "pull_request" else ""
                push_before = "c" * 40 if event == "push" else ""
                workflow.context["github"]["event"] = {"pull_request": {"base": {"sha": pr_base}},
                                                          "before": push_before}
                step = self.evidence["steps"][1]
                self.assertEqual({"EVIDENCE_PR_BASE": pr_base, "EVIDENCE_PUSH_BEFORE": push_before},
                                 {key: workflow.expand(value) for key, value in step["env"].items()})
                self.assertEqual(["python3", "-I", "tools/check_evidence.py"], shlex.split(step["run"]))

    def test_evidence_read_only_checkout_and_independence_from_the_writer(self):
        workflow = Workflow(SimpleNamespace(root=ROOT, sha="a" * 40))
        self.assertEqual({"evidence"}, set(self.document["jobs"]))
        self.assertEqual({}, self.document["permissions"])
        self.assertNotIn("concurrency", self.document)
        self.assertEqual({"contents": "read"}, self.evidence["permissions"])
        self.assertEqual({"runs-on", "timeout-minutes", "permissions", "steps"}, set(self.evidence))
        checkout, check = self.evidence["steps"]
        self.assertEqual({"name", "uses", "with"}, set(checkout))
        self.assertEqual(workflow.document["jobs"]["validate"]["steps"][0]["uses"], checkout["uses"])
        self.assertEqual({"fetch-depth": 1, "fetch-tags": False, "sparse-checkout": "/tools/check_evidence.py",
                          "sparse-checkout-cone-mode": False, "submodules": False, "persist-credentials": False},
                         checkout["with"])
        self.assertEqual({"name", "env", "run"}, set(check))
        self.assertEqual({"validate", "deliver"}, set(workflow.document["jobs"]))
        self.assertEqual("validate", workflow.document["jobs"]["deliver"]["needs"])
        self.assertNotIn("needs", workflow.document["jobs"]["validate"])


class NarrowWorkflowTests(unittest.TestCase):
    def fixture(self):
        from test_deliver_g6_catalog import CatalogWorkspace, delivery
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        w = Workspace(Path(temporary.name) / "workspace", (delivery.PROJECTS,))
        (w.candidate / "setup" / (delivery.PROJECTS + ".yml")).unlink()
        (w.candidate / "setup/Hexalith.Unrelated.yml").write_text("{}\n")
        catalog = CatalogWorkspace(w.root / "catalog")
        for path in delivery.SOURCES:
            target = w.candidate / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(catalog.owner / path, target)
        w.config["modules"][delivery.PROJECTS] = str(catalog.remote)
        w.commit()
        w.ref("Hexalith.Unrelated", w.sha)
        report = w.root / "qualified.json"
        w.outputs.unlink(missing_ok=True)
        code = w.call(str(w.candidate / "tools/deliver_g6_catalog.py"), ["qualify", "--report", str(report)],
                      env=w.env(GITHUB_EVENT_NAME="workflow_dispatch", G6_OWNER_SOURCE=w.sha,
                                MODULE_TOKEN="", CICD_TOKEN=""))
        self.assertEqual(code, 0)
        published = dict(line.split("=", 1) for line in w.outputs.read_text().splitlines())
        self.assertEqual(set(published), {"plan"})
        binding = json.loads(published["plan"])
        self.assertEqual(binding, json.loads(report.read_bytes())["plan"])
        return w, catalog, binding

    def test_narrow_branch_executes_only_qualified_owner_writer_and_projects_mint(self):
        w, catalog, binding = self.fixture()
        workflow = Workflow(w, event="workflow_dispatch", delivery="projects-g6-catalog", g6_plan=binding)
        self.assertEqual(workflow.execute(), "success")
        self.assertEqual(workflow.concurrency_group, "deliver-projects-g6-catalog")
        self.assertFalse(workflow.cancel_in_progress)
        self.assertEqual(workflow.writer_concurrency_group, "deliver-owned-writes")
        self.assertFalse(workflow.writer_cancel_in_progress)
        self.assertEqual([inputs["repositories"] for _, inputs in workflow.mints], ["Hexalith.Projects"])
        self.assertEqual(set(workflow.mints[0][1]), {"client-id", "private-key", "owner", "repositories",
                                                   "permission-contents", "permission-workflows"})
        self.assertEqual(len(workflow.commands), 1)
        self.assertIn("deliver_g6_catalog.py", workflow.commands[0][2])
        self.assertEqual(workflow.processes, [])
        self.assertEqual([name for name, _ in workflow.uploads], ["projects-g6-delivery"])
        result = json.loads(workflow.uploads[0][1])
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(result["owner_source"], w.sha)
        self.assertEqual(result["delivered_tree"], catalog.result_tree)
        self.assertEqual(git(w.remote, "for-each-ref", "--format=%(refname)", "refs/heads/delivered/"), "refs/heads/delivered/Hexalith.Unrelated")
        self.assertEqual(git(w.remote, "ls-tree", "-r", "--name-only", w.sha, "--", "setup"), "setup/Hexalith.Unrelated.yml")
        self.assertTrue(all(proof["registry_count"] == 1 and proof["accepted_ref_count"] == 1
                            for proof in result["full_writer_exclusion"]))

    def test_concurrency_keeps_normal_default_and_pr_groups(self):
        w, _, binding = self.fixture()
        scenarios = (
            ({"event": "workflow_dispatch", "delivery": "projects-g6-catalog"}, "deliver-projects-g6-catalog", False),
            ({"event": "workflow_dispatch", "delivery": "full"}, "deliver", False),
            ({"event": "workflow_dispatch", "delivery": ""}, "deliver", False),
            ({"event": "push", "delivery": "projects-g6-catalog"}, "deliver", False),
            ({"event": "schedule", "delivery": ""}, "deliver", False),
            ({"event": "pull_request", "ref": "refs/pull/1/merge", "delivery": "projects-g6-catalog"},
             "deliver-validate-refs/pull/1/merge", True),
            ({"event": "workflow_dispatch", "ref": "refs/heads/feature", "delivery": "projects-g6-catalog"},
             "deliver-validate-refs/heads/feature", True),
        )
        for options, group, cancel in scenarios:
            with self.subTest(options=options):
                workflow = Workflow(w, validation="cancelled", g6_plan=binding, **options)
                self.assertEqual(workflow.execute(), "skipped")
                self.assertEqual(workflow.concurrency_group, group)
                self.assertEqual(workflow.cancel_in_progress, cancel)
                self.assertEqual(workflow.mints, [])
                self.assertEqual(workflow.writer_concurrency_group, "deliver-owned-writes")
                self.assertFalse(workflow.writer_cancel_in_progress)

    def test_independent_validation_lanes_share_only_the_existing_write_job_mutex(self):
        w, _, binding = self.fixture()
        groups = []
        for mode in ("full", "projects-g6-catalog"):
            writer = Workflow(w, event="workflow_dispatch", delivery=mode, validation="cancelled", g6_plan=binding)
            self.assertEqual(writer.execute(), "skipped")
            self.assertEqual(writer.writer_concurrency_group, "deliver-owned-writes")
            self.assertFalse(writer.writer_cancel_in_progress)
            self.assertNotEqual(writer.writer_concurrency_group, writer.concurrency_group)
            validation = Workflow(w, event="workflow_dispatch", delivery=mode, validation="cancelled", job="validate")
            self.assertEqual(validation.execute(), "skipped")
            self.assertIsNone(validation.writer_concurrency_group)
            groups.append(validation.concurrency_group)
        self.assertEqual(groups, ["deliver", "deliver-projects-g6-catalog"])

    def test_narrow_qualification_failure_missing_plan_or_wrong_ref_mints_nothing(self):
        for options in ({"validation": "failure"}, {"g6_plan": None}, {"ref": "refs/heads/feature"},
                        {"event": "push"}):
            with self.subTest(options=options):
                w, catalog, binding = self.fixture()
                args = {"event": "workflow_dispatch", "delivery": "projects-g6-catalog", "g6_plan": binding} | options
                workflow = Workflow(w, **args)
                self.assertEqual(workflow.execute(), "skipped")
                self.assertEqual(workflow.mints, [])
                self.assertEqual(workflow.commands, [])
                self.assertEqual(git(catalog.remote, "rev-parse", "main"), catalog.base)

    def test_narrow_mint_refusal_uploads_failed_receipt_without_other_mints(self):
        w, catalog, binding = self.fixture()
        workflow = Workflow(w, event="workflow_dispatch", delivery="projects-g6-catalog", g6_plan=binding,
                            mint_fail=("Hexalith.Projects",))
        self.assertEqual(workflow.execute(), "failure")
        self.assertEqual(len(workflow.mints), 1)
        result = json.loads(workflow.uploads[0][1])
        self.assertEqual(result["status"], "failed")
        self.assertIn("App token unavailable", result["reason"])
        self.assertFalse(result["push_attempted"])
        self.assertEqual(git(catalog.remote, "rev-parse", "main"), catalog.base)

    def test_behavioral_suite_failure_still_uploads_failed_qualification_without_plan_or_mint(self):
        w, catalog, _ = self.fixture()
        validation = Workflow(w, event="workflow_dispatch", delivery="projects-g6-catalog", job="validate", suite_result="failure")
        self.assertEqual(validation.execute(), "failure")
        self.assertEqual(validation.lookup("steps.g6_tests.outcome"), "failure")
        self.assertEqual(validation.lookup("steps.g6_qualify.outcome"), "failure")
        self.assertEqual(validation.lookup("steps.g6_qualify.outputs.plan"), "")
        self.assertEqual([name for name, _ in validation.uploads], ["projects-g6-qualification"])
        receipt = json.loads(validation.uploads[0][1])
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["failed_operation"], "verify secret-free behavioral suites")
        self.assertIsNone(receipt["plan"])
        writer = Workflow(w, event="workflow_dispatch", delivery="projects-g6-catalog", validation="failure")
        self.assertEqual(writer.execute(), "skipped")
        self.assertEqual(writer.mints, [])
        checkouts = [item for item in validation.checkouts if isinstance(item, dict) and item.get("repository") == "Hexalith/Hexalith.Builds"]
        self.assertEqual(len(checkouts), 1)
        self.assertEqual(checkouts[0]["ref"], "refs/tags/v5.1.0")
        self.assertEqual(checkouts[0]["fetch-depth"], 1)
        self.assertFalse(checkouts[0]["fetch-tags"])
        self.assertFalse(checkouts[0]["submodules"])
        self.assertEqual(git(catalog.remote, "rev-parse", "main"), catalog.base)

    def test_implicit_success_prevents_mint_after_checkout_failure_or_cancellation(self):
        for options in ({"checkout_fail": True}, {"cancel_after": "Checkout exact qualified narrow owner source"}):
            with self.subTest(options=options):
                w, catalog, binding = self.fixture()
                workflow = Workflow(w, event="workflow_dispatch", delivery="projects-g6-catalog", g6_plan=binding, **options)
                workflow.execute()
                self.assertEqual(workflow.lookup("steps.g6_token.outcome"), "skipped")
                self.assertEqual(workflow.mints, [])
                self.assertEqual(git(catalog.remote, "rev-parse", "main"), catalog.base)


if __name__ == "__main__":
    unittest.main()
