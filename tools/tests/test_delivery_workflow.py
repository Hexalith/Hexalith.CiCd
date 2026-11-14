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
from pathlib import Path
import re
import shlex
import tempfile
import unittest
from unittest import mock

import yaml
from delivery_support import ROOT, Workspace, bootstrap_source, git


class Workflow:
    def __init__(self, workspace, *, ref="refs/heads/main", event="push", validation="success", verdict=None,
                 mint_fail=(), cancel_after=None):
        self.w = workspace
        self.document = yaml.safe_load((ROOT / ".github/workflows/deliver.yml").read_bytes())
        self.job = self.document["jobs"]["deliver"]
        self.context = {"github": {"ref": ref, "sha": workspace.sha, "repository": "Hexalith/Hexalith.CiCd",
            "workspace": str(workspace.root), "run_id": "101", "run_attempt": "1", "event_name": event, "token": "inert-checkout-token"},
            "needs": {"validate": {"result": validation, "outputs": {"verdict": json.dumps(verdict) if verdict is not None else ""}}},
            "steps": {}, "runner": {"temp": str(workspace.root)},
            "secrets": {"HEXALITH_CICD_APP_PRIVATE_KEY": "inert-no-private-key"},
            "vars": {"HEXALITH_CICD_APP_CLIENT_ID": "inert-client-id"}}
        # Model validation at its I/O boundary, then evaluate the real job's
        # output mapping even when that job's result is failure.
        self.context["steps"] = {"validate": {"outputs": self.context["needs"]["validate"]["outputs"]}}
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
                result.append(repr(token[1:-1]))
            elif token in {"&&", "||", "!"}:
                result.append({"&&": "and", "||": "or", "!": "not"}[token])
            elif token in {"==", "!=", "(", ")", ","}:
                result.append(token)
            elif token in {"always", "success", "failure", "cancelled", "format"}:
                result.append(token)
            elif token in {"true", "false"}:
                result.append("True" if token == "true" else "False")
            else:
                result.append(repr(self.lookup(token)))
        return eval(" ".join(result), {"__builtins__": {}}, {"always": lambda: True,
            "success": lambda: not self.failed and not self.cancelled, "failure": lambda: self.failed, "cancelled": lambda: self.cancelled,
            "format": lambda pattern, value: pattern.format(value)})

    def expand(self, value):
        if not isinstance(value, str):
            return value
        return re.sub(r"\$\{\{(.*?)\}\}", lambda m: str(self.expression(m.group(1))), value)

    def execute(self):
        triggers = self.document.get("on", self.document.get(True))
        event, ref = self.context["github"]["event_name"], self.context["github"]["ref"]
        if event not in triggers or (event == "push" and ref.removeprefix("refs/heads/") not in triggers["push"]["branches"]):
            return "not-triggered"
        concurrency = self.document["concurrency"]
        self.concurrency_group = self.expression(concurrency["group"])
        self.cancel_in_progress = self.expression(concurrency["cancel-in-progress"])
        self.validation_entered = True
        if not self.expression(self.job["if"]):
            return "skipped"
        base = self.w.env()
        base.update({"GITHUB_" + key.upper(): str(value) for key, value in self.context["github"].items() if key != "token"})
        base.update({key: self.expand(value) for key, value in self.job.get("env", {}).items()})
        self.context["env"] = base
        for ordinal, step in enumerate(self.job["steps"]):
            identifier = step.get("id", f"step_{ordinal}")
            if not self.expression(step.get("if", "success()")):
                self.context["steps"][identifier] = {"outcome": "skipped", "outputs": {}}
                continue
            outputs, outcome = {}, "success"
            if "uses" in step:
                inputs = {key: self.expand(value) for key, value in step.get("with", {}).items()}
                self.actions.append((step["uses"], inputs))
                action = step["uses"].split("@", 1)[0]
                if action == "actions/checkout":
                    source = inputs.get("ref", "")
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
                    if not artifact.is_file():
                        raise AssertionError("upload did not receive actual report bytes")
                    self.uploads.append((inputs["name"], artifact.read_bytes()))
                else:
                    raise AssertionError("unhandled external action " + action)
            elif "run" in step:
                command = shlex.split(step["run"])
                if command[:2] != ["python3", "-I"] or "${{" in step["run"]:
                    raise AssertionError("privileged command is not isolated Python")
                self.commands.append(command)
                self.w.outputs.unlink(missing_ok=True)
                env = base | {key: self.expand(value) for key, value in step.get("env", {}).items()}
                if command[3:4] == ["module"]:
                    self.processes.append({"name": step["name"], "slot": int(command[command.index("--slot") + 1]),
                                           "token": env.get("MODULE_TOKEN", "")})
                result = self.w.call(str(self.w.root / command[2]), command[3:], env=env)
                if result:
                    outcome = "failure"
                if self.w.outputs.exists():
                    outputs = dict(line.split("=", 1) for line in self.w.outputs.read_text().splitlines())
            else:
                raise AssertionError("step has neither action nor command")
            self.context["steps"][identifier] = {"outcome": outcome, "outputs": outputs}
            if outcome == "failure" and not step.get("continue-on-error", False):
                self.failed = True
            if self.cancel_after is not None and self.cancel_after in (identifier, step.get("name")):
                self.cancelled = True
        return "failure" if self.failed else "success"


class WorkflowTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
