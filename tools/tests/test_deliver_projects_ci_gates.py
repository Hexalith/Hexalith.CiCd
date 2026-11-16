#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Real-Git behavior of the separate, closed nine-file Projects repair."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import shlex
import sys
import tempfile
import unittest
from unittest import mock

from test_deliver_g6_catalog import CatalogWorkspace, delivery, rt
from delivery_support import ROOT, git
from test_delivery_workflow import Workflow
import yaml


class GateWorkspace(CatalogWorkspace):
    """Start with acquired catalog files, then review only nine gate prerequisites."""
    def __init__(self, root):
        super().__init__(root)
        git(self.projects, "commit", "--quiet", "-m", "test: previously delivered acquisition")
        existing = (delivery.GATES_PATHS[0], *delivery.GATES_PATHS[6:])
        for path in existing:
            target = self.projects / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"# existing prerequisite retained at the reviewed base\n")
        git(self.projects, "add", "--", *existing)
        git(self.projects, "commit", "--quiet", "-m", "test: source with existing renderer")
        self.base = git(self.projects, "rev-parse", "HEAD")
        self.base_tree = git(self.projects, "rev-parse", "HEAD^{tree}")
        self.before = self.items(self.projects, self.base)
        git(self.projects, "push", "--quiet", self.remote, "HEAD:main")
        for path in delivery.GATES_PATHS:
            target = self.projects / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'{"private":true}\n' if path.endswith(".json")
                               else b"raise RuntimeError('module code must never execute with the token')\n")
        git(self.projects, "add", "--", *delivery.GATES_PATHS)
        self.refresh_proposal()

    def refresh_proposal(self):
        self.patch = subprocess.run(["git", "-C", str(self.projects), "diff", "--cached", "--binary", self.base],
                                    capture_output=True, check=True).stdout
        self.result_tree = git(self.projects, "write-tree")
        self.after = self.items(self.projects, self.result_tree)
        self.value = {"schema": "hexalith.projects-ci-gates.v1", "repository": delivery.PROJECTS,
                      "pre_push_gate": "reviewed-tree-owner-authorized", "base_commit": self.base,
                      "base_tree": self.base_tree, "patch_sha256": delivery.digest(self.patch),
                      "result_tree": self.result_tree,
                      "before": {path: self.before.get(path) for path in delivery.GATES_PATHS},
                      "after": {path: self.after.get(path) for path in delivery.GATES_PATHS}}
        self.validation = {"schema": "hexalith.projects-ci-gates-validation.v1", "status": "passed",
                           **{field: self.value[field] for field in ("base_commit", "base_tree", "result_tree", "patch_sha256")},
                           "checks": {name: {"status": "passed", "log_sha256": "a" * 64}
                                      for name in delivery.GATES_CHECKS}}
        self.bind_validation(self.validation)

    def bind_validation(self, proof):
        self.validation_bytes = (json.dumps(proof) + "\n").encode()
        self.value["validation_sha256"] = delivery.digest(self.validation_bytes)
        self.save()

    def save(self):
        for path in delivery.GATES_SOURCES:
            target = self.owner / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if path == delivery.GATES_MANIFEST:
                target.write_text(json.dumps(self.value) + "\n")
            elif path == delivery.GATES_VALIDATION:
                target.write_bytes(self.validation_bytes)
            else:
                target.write_bytes(self.patch if path == delivery.GATES_PATCH else (ROOT / path).read_bytes())
        git(self.owner, "add", ".")
        git(self.owner, "commit", "--quiet", "-m", "test: reviewed gate prerequisites")
        self.sha = git(self.owner, "rev-parse", "HEAD")
        git(self.owner, "push", "--quiet", self.owner_remote, "HEAD:main")

    def context(self):
        return super().context() | {"G6_PROFILE": "ci-gates", "G6_BEHAVIORAL_RESULT": "success", "GITHUB_WORKFLOW_REF":
            "Hexalith/Hexalith.CiCd/" + delivery.GATES_WORKFLOW + "@refs/heads/main"}

    def run(self, operation="qualify", *, profile="ci-gates", **context):
        self.read_counts.clear()
        return delivery.execute(operation, self.context() | context, self.report_path, transport=self.transport,
                                token=self.token if operation == "deliver" else "", scratch=self.root,
                                local_root=self.owner, profile=profile)

    def cli_call(self, operation="qualify", *, script=None, args=None, cwd=None, **extra):
        configuration = self.root / "gate-config.json"
        configuration.write_text(json.dumps({"cicd": str(self.owner_remote),
            "modules": {delivery.PROJECTS: str(self.remote)}, "acquisitions": str(self.root / "cli-acquisitions.jsonl"),
            "push_fail": [], "races": {}}))
        output = self.root / "gate-output"
        output.unlink(missing_ok=True)
        environment = os.environ | self.context() | {"GITHUB_OUTPUT": str(output), "TMPDIR": str(self.root),
            "MODULE_TOKEN": self.token if operation == "deliver" else "", "CICD_TOKEN": ""}
        for key, value in extra.items():
            if value is None:
                environment.pop(key, None)
            else:
                environment[key] = value
        result = subprocess.run([sys.executable, "-I", str(ROOT / "tools/tests/delivery_support.py"), "driver",
            str(script or self.owner / "tools/deliver_g6_catalog.py"), str(configuration),
            *(args or [operation, "--profile", "ci-gates", "--report", str(self.report_path)])],
            capture_output=True, cwd=cwd, env=environment)
        return result, output.read_text() if output.exists() else ""

    def cli_qualify(self, **extra):
        return self.cli_call(**extra)



class GateWorkflow(Workflow):
    """Run the actual owner job mapping; substitute only actions and suite outcome."""
    def __init__(self, workspace, *, job="validate", plan=None, validation="success", suite_result="success",
                 mint_fail=False, ref="refs/heads/main", event="workflow_dispatch"):
        super().__init__(workspace, job=job, event=event, ref=ref, validation=validation, suite_result=suite_result)
        self.document = yaml.safe_load((ROOT / delivery.GATES_WORKFLOW).read_bytes())
        self.job = self.document["jobs"][job]
        self.context["github"]["workflow_ref"] = "Hexalith/Hexalith.CiCd/" + delivery.GATES_WORKFLOW + "@refs/heads/main"
        self.context["needs"]["validate"]["outputs"] = {"plan": json.dumps(plan) if plan else ""}
        self.mint_fails = mint_fail
        self.outputs = {}

    def execute(self):
        triggers = self.document.get("on", self.document.get(True))
        if self.context["github"]["event_name"] not in triggers:
            return "not-triggered"
        self.concurrency_group = self.expand(self.document["concurrency"]["group"])
        mutex = self.job.get("concurrency", {})
        self.writer_concurrency_group = mutex.get("group")
        self.writer_cancel_in_progress = mutex.get("cancel-in-progress")
        if not self.condition(self.job.get("if", "success()")):
            return "skipped"
        base = self.w.context() | {"MODULE_TOKEN": "", "CICD_TOKEN": ""}
        base.update({"GITHUB_" + key.upper(): str(value) for key, value in self.context["github"].items() if key != "token"})
        working = self.w.owner if self.job_name == "validate" else self.w.root
        for ordinal, step in enumerate(self.job["steps"]):
            identifier = step.get("id", f"step_{ordinal}")
            if not self.condition(step.get("if", "success()")):
                self.finish_step(identifier, step, "skipped", {})
                continue
            outputs, outcome = {}, "success"
            if "uses" in step:
                inputs = {key: self.expand(value) for key, value in step.get("with", {}).items()}
                self.actions.append((step["uses"], inputs))
                action = step["uses"].split("@", 1)[0]
                if action == "actions/checkout":
                    if inputs.get("submodules") is not False or inputs.get("persist-credentials") is not False:
                        raise AssertionError("unsafe owner checkout")
                    if self.job_name == "deliver":
                        if inputs.get("ref") != self.w.sha:
                            raise AssertionError("checkout is not the exact qualified owner")
                        destination = working / inputs["path"]
                        for path in inputs["sparse-checkout"].splitlines():
                            target = destination / path
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(subprocess.run(["git", "-C", str(self.w.owner), "show",
                                self.w.sha + ":" + path], check=True, capture_output=True).stdout)
                    self.checkouts.append(inputs)
                elif action == "astral-sh/setup-uv":
                    pass
                elif action == "actions/create-github-app-token":
                    self.mints.append(inputs)
                    if inputs.get("owner") != "Hexalith" or inputs.get("repositories") != delivery.PROJECTS or \
                            inputs.get("permission-contents") != "write" or any(
                                key.startswith("permission-") and key != "permission-contents" for key in inputs):
                        raise AssertionError("gate repair token exceeds Projects Contents write")
                    if self.mint_fails:
                        outcome = "failure"
                    else:
                        outputs["token"] = self.w.token
                elif action == "actions/upload-artifact":
                    artifact = working / inputs["path"]
                    if artifact.is_file():
                        self.uploads.append((inputs["name"], artifact.read_bytes()))
                    elif inputs.get("if-no-files-found") == "error":
                        outcome = "failure"
                else:
                    raise AssertionError("unhandled external action " + action)
            elif identifier == "tests":
                # The suite I/O is replaced; its actual outcome feeds the real qualifier.
                outcome = self.suite_result
            else:
                command = shlex.split(step["run"])
                if command[:2] != ["python3", "-I"]:
                    raise AssertionError("writer command is not isolated Python")
                environment = base | {key: self.expand(value) for key, value in step.get("env", {}).items()}
                process, output = self.w.cli_call(command[3], script=working / command[2], args=command[3:],
                                                cwd=working, **environment)
                self.commands.append(command)
                self.processes.append(process)
                outcome = "success" if process.returncode == 0 else "failure"
                outputs = dict(row.split("=", 1) for row in output.splitlines())
            self.finish_step(identifier, step, outcome, outputs)
        if self.job_name == "validate":
            self.outputs = {key: self.expand(value) for key, value in self.job.get("outputs", {}).items()}
        return "failure" if self.failed else "success"


class GateDeliveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(temporary.cleanup)
        self.w = GateWorkspace(Path(temporary.name) / "workspace")
        original = rt.environment
        def file_transport():
            result = original()
            i = int(result["GIT_CONFIG_COUNT"])
            result.update(GIT_CONFIG_COUNT=str(i + 1))
            result[f"GIT_CONFIG_KEY_{i}"] = "protocol.file.allow"
            result[f"GIT_CONFIG_VALUE_{i}"] = "always"
            return result
        self.environment_patch = mock.patch.object(rt, "environment", side_effect=file_transport)
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)

    def refused(self, result, reason):
        self.assertEqual(result["status"], "failed")
        self.assertIn(reason, result["reason"])
        self.assertEqual(self.w.pushes, [])
        self.assertEqual(git(self.w.remote, "rev-parse", "main"), self.w.base)

    def test_cli_qualification_output_feeds_writer_and_preserves_catalog_and_gitlink(self):
        w = self.w
        code, output = w.cli_qualify()
        self.assertEqual(code.returncode, 0, code.stderr)
        actual_plan = json.loads(dict(row.split("=", 1) for row in output.splitlines())["plan"])
        qualified = json.loads(w.report_path.read_bytes())
        self.assertEqual(qualified["plan"], actual_plan)
        self.assertEqual(actual_plan["schema"], "hexalith.projects-ci-gates-plan.v1")
        self.assertEqual(actual_plan["profile"], "ci-gates")
        self.assertEqual(actual_plan["module_validation_sha256"], w.value["validation_sha256"])
        result = w.run("deliver", G6_QUALIFICATION="success", G6_PLAN=json.dumps(actual_plan))
        self.assertEqual(result["status"], "delivered", result)
        self.assertEqual(result["schema"], "hexalith.projects-ci-gates-delivery.v1")
        self.assertEqual(git(w.remote, "rev-parse", result["delivered_sha"] + "^"), w.base)
        self.assertEqual(w.items(w.remote, result["delivered_sha"]), w.after)
        for path, entry in w.before.items():
            if path not in delivery.GATES_PATHS:
                self.assertEqual(w.after[path], entry)
        self.assertEqual(git(w.remote, "show", "main", "--format=%B", "--no-patch"),
                         "build(cicd): restore reviewed Projects gate prerequisites")

    def test_unknown_profile_mismatched_context_and_wrong_workflow_refuse_before_writing(self):
        cases = (("unreviewed", {}, "unknown closed"),
                 ("catalog", {}, "profile differs"),
                 ("ci-gates", {"G6_PROFILE": "catalog"}, "profile differs"),
                 ("ci-gates", {"G6_PROFILE": None}, "profile differs"),
                 ("ci-gates", {"GITHUB_WORKFLOW_REF": "other-owner-workflow"}, "ineligible gate-repair"))
        for profile, context, reason in cases:
            with self.subTest(profile=profile, context=context):
                self.refused(self.w.run(profile=profile, **context), reason)

    def test_missing_or_other_profile_plan_never_reaches_push(self):
        original = self.w.run()["plan"]
        for change in ({"schema": "hexalith.projects-g6-catalog-plan.v1"}, {"profile": "catalog"},
                       {"profile": None}, {"owner_source": "f" * 40}):
            with self.subTest(change=change):
                supplied = original | change
                self.refused(self.w.run("deliver", G6_QUALIFICATION="success", G6_PLAN=json.dumps(supplied)),
                             "binding mismatch")

    def test_failed_suite_cli_emits_no_plan_and_delivery_requires_success(self):
        code, output = self.w.cli_qualify(G6_BEHAVIORAL_RESULT="failure")
        self.assertEqual(code.returncode, 1)
        self.assertEqual(output, "")
        self.refused(json.loads(self.w.report_path.read_bytes()), "behavioral qualification failed")
        self.refused(self.w.run("deliver", G6_QUALIFICATION="failure", G6_PLAN="{}"), "qualification did not succeed")

    def test_schemas_and_exact_nine_path_whitelist_cannot_be_crossed(self):
        for mutation in ("schema", "extra", "catalog", "existing-new", "existing-mode"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.w.value)
                if mutation == "schema":
                    changed["schema"] = "hexalith.projects-g6-catalog.v1"
                elif mutation == "extra":
                    changed["after"]["foreign.txt"] = ["100644", "blob", "a" * 40]
                elif mutation == "catalog":
                    changed["after"].pop(delivery.GATES_PATHS[-1])
                    changed["after"][delivery.WORKFLOW] = ["100644", "blob", "a" * 40]
                elif mutation == "existing-new":
                    changed["before"]["package-lock.json"] = ["100644", "blob", "a" * 40]
                else:
                    changed["before"][delivery.GATES_PATHS[6]][0] = "120000"
                with self.assertRaises(rt.DeliveryError):
                    delivery.manifest(json.dumps(changed), "ci-gates")

    def test_extra_workflow_change_is_rejected_even_with_bound_patch_and_complete_tree(self):
        w = self.w
        (w.projects / delivery.WORKFLOW).write_text("name: Unauthorized workflow change\n")
        git(w.projects, "add", "--", delivery.WORKFLOW)
        w.refresh_proposal()
        self.refused(w.run(), "outside the closed nine-path")

    def test_wrong_reviewed_source_or_complete_result_refuses(self):
        w = self.w
        original = copy.deepcopy(w.value)
        for field in ("base_commit", "base_tree", "result_tree"):
            with self.subTest(field=field):
                w.value = original | {field: "f" * 40}
                proof = copy.deepcopy(w.validation)
                proof[field] = w.value[field]
                w.bind_validation(proof)
                self.refused(w.run(), "reviewed" if field == "base_commit" else "mismatch")
        w.value = original
        w.bind_validation(w.validation)
        self.refused(w.run(G6_OWNER_SOURCE="f" * 40), "dispatch source")

    def test_gate_repair_is_idempotent_and_preserves_existing_acquisition(self):
        first = self.w.deliver()
        self.assertEqual(first["status"], "delivered", first)
        self.w.pushes.clear()
        again = self.w.deliver()
        self.assertEqual(again["status"], "unchanged", again)
        self.assertEqual(again["delivered_sha"], first["delivered_sha"])
        self.assertEqual(self.w.pushes, [])

    def test_production_profile_binds_reviewed_actual_module_validation(self):
        value = delivery.manifest((ROOT / delivery.GATES_MANIFEST).read_bytes(), "ci-gates")
        proof = delivery.module_validation((ROOT / delivery.GATES_VALIDATION).read_bytes(), value)
        self.assertEqual(value["patch_sha256"], delivery.digest((ROOT / delivery.GATES_PATCH).read_bytes()))
        self.assertEqual(proof["result_tree"], value["result_tree"])
        self.assertEqual(set(proof["checks"]), delivery.GATES_CHECKS)

    def test_qualification_requires_explicit_success_including_missing_result(self):
        for state in (None, "", "skipped", "cancelled", "failure"):
            with self.subTest(state=state):
                code, output = self.w.cli_qualify(G6_BEHAVIORAL_RESULT=state)
                self.assertEqual(code.returncode, 1)
                self.assertEqual(output, "")
                self.refused(json.loads(self.w.report_path.read_bytes()), "behavioral qualification failed")

    def test_missing_failed_or_stale_module_validation_cannot_qualify(self):
        w = self.w
        original = copy.deepcopy(w.validation)
        for mutation in ("failed", "missing-check", "failed-check", "stale-base", "stale-result", "stale-patch", "bad-log", "extra"):
            with self.subTest(mutation=mutation):
                proof = copy.deepcopy(original)
                if mutation == "failed":
                    proof["status"] = "failed"
                elif mutation == "missing-check":
                    proof["checks"].pop("workflow_gates")
                elif mutation == "failed-check":
                    proof["checks"]["npm_vulnerabilities"]["status"] = "failed"
                elif mutation in ("stale-base", "stale-result", "stale-patch"):
                    proof[{"stale-base": "base_commit", "stale-result": "result_tree", "stale-patch": "patch_sha256"}[mutation]] = "f" * (64 if mutation == "stale-patch" else 40)
                elif mutation == "bad-log":
                    proof["checks"]["npm_signatures"]["log_sha256"] = "invalid"
                else:
                    proof["owner_source"] = "f" * 40
                w.bind_validation(proof)
                self.refused(w.run(), "module validation")
        w.bind_validation(original)
        (w.owner / delivery.GATES_VALIDATION).unlink()
        self.refused(w.run(), "local owner payload differs")

    def test_validation_digest_and_qualified_validation_binding_cannot_change(self):
        w = self.w
        original = w.validation_bytes
        w.validation_bytes += b" "
        w.save()
        self.refused(w.run(), "validation SHA256 mismatch")
        w.validation_bytes = original
        w.save()
        plan = w.run()["plan"] | {"module_validation_sha256": "f" * 64}
        self.refused(w.run("deliver", G6_QUALIFICATION="success", G6_PLAN=json.dumps(plan)), "binding mismatch")

    def test_credentialed_cli_sanitizes_poisoned_environment_and_retains_indices(self):
        w = self.w
        snapshots = {str(path): (path / ".git/index").read_bytes() for path in (w.owner, w.projects)}
        poison = {"GIT_DIR": str(w.root / "poison.git"), "GIT_WORK_TREE": str(w.root / "poison-tree"),
                  "GIT_INDEX_FILE": str(w.root / "poison-index"), "GIT_CONFIG_COUNT": "1",
                  "GIT_CONFIG_KEY_0": "core.hooksPath", "GIT_CONFIG_VALUE_0": str(w.root / "poison-hooks"),
                  "PYTHONPATH": str(w.root / "poison-python"), "NODE_OPTIONS": "--require nonexistent-poison"}
        code, _ = w.cli_qualify(**poison)
        self.assertEqual(code.returncode, 0, code.stderr)
        plan = json.loads(w.report_path.read_bytes())["plan"]
        code, output = w.cli_call("deliver", G6_QUALIFICATION="success", G6_PLAN=json.dumps(plan), **poison)
        self.assertEqual(code.returncode, 0, code.stderr)
        result = json.loads(w.report_path.read_bytes())
        self.assertEqual(result["status"], "delivered")
        self.assertTrue(result["push_attempted"])
        self.assertEqual(output, "")
        self.assertNotIn(w.token.encode(), w.report_path.read_bytes())
        self.assertFalse((w.root / "poison-index").exists())
        for path, index in snapshots.items():
            self.assertEqual((Path(path) / ".git/index").read_bytes(), index)

    def test_new_profile_refuses_final_source_and_accepted_ref_races(self):
        w = self.w
        for race in (rt.CICD, delivery.PROJECTS, "accepted-ref"):
            with self.subTest(race=race):
                qualified = w.run()
                w.final_race = race if race != "accepted-ref" else None
                w.final_accepted_ref = delivery.PROJECTS if race == "accepted-ref" else None
                result = w.deliver(qualified)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(w.pushes, [])
                self.assertTrue(result["failed_operation"])
                git(w.owner_remote, "update-ref", "refs/heads/main", w.sha)
                git(w.remote, "update-ref", "refs/heads/main", w.base)
                if race == "accepted-ref":
                    git(w.owner_remote, "update-ref", "-d", "refs/heads/delivered/" + delivery.PROJECTS)
                w.final_race = w.final_accepted_ref = None

    def test_new_profile_rejected_and_ambiguous_push_never_retry(self):
        w = self.w
        for outcome in ("race", "error", "timeout"):
            with self.subTest(outcome=outcome):
                w.race = "before" if outcome == "race" else None
                w.push_outcome = None if outcome == "race" else outcome
                result = w.deliver()
                self.assertEqual(result["status"], "failed")
                self.assertEqual(len(w.pushes), 1)
                self.assertEqual(result["candidate_sha"], w.pushes[0])
                self.assertEqual(result["reconciliation"]["status"], "observed")
                self.assertEqual(result["delivered_sha"], None if outcome == "race" else result["candidate_sha"])
                git(w.remote, "update-ref", "refs/heads/main", w.base)
                w.pushes.clear()
                w.race = w.push_outcome = None

    def test_actual_owner_workflow_routes_real_plan_to_contents_only_serialized_writer(self):
        validate = GateWorkflow(self.w)
        self.assertEqual(validate.execute(), "success", [p.stderr for p in validate.processes])
        actual = json.loads(validate.outputs["plan"])
        self.assertEqual(actual["module_validation_sha256"], self.w.value["validation_sha256"])
        writer = GateWorkflow(self.w, job="deliver", plan=actual)
        self.assertEqual(writer.execute(), "success", [p.stderr for p in writer.processes])
        self.assertEqual(len(writer.mints), 1)
        self.assertEqual(writer.writer_concurrency_group, "deliver-owned-writes")
        self.assertIs(writer.writer_cancel_in_progress, False)
        self.assertEqual(writer.job["environment"], "cicd-app")
        self.assertEqual(validate.job["timeout-minutes"], 40)
        self.assertEqual(writer.job["timeout-minutes"], 40)
        self.assertEqual(json.loads(writer.uploads[-1][1])["status"], "delivered")

    def test_actual_owner_workflow_failed_suite_prevents_mint_and_keeps_failed_receipt(self):
        validate = GateWorkflow(self.w, suite_result="failure")
        self.assertEqual(validate.execute(), "failure")
        self.assertEqual(validate.outputs["plan"], "")
        self.assertEqual(json.loads(validate.uploads[-1][1])["status"], "failed")
        writer = GateWorkflow(self.w, job="deliver", validation="failure")
        self.assertEqual(writer.execute(), "skipped")
        self.assertEqual(writer.mints, [])

    def test_actual_owner_workflow_missing_token_keeps_failure_without_push(self):
        validate = GateWorkflow(self.w)
        self.assertEqual(validate.execute(), "success")
        writer = GateWorkflow(self.w, job="deliver", plan=json.loads(validate.outputs["plan"]), mint_fail=True)
        self.assertEqual(writer.execute(), "failure")
        receipt = json.loads(writer.uploads[-1][1])
        self.assertEqual(receipt["failed_operation"], "require scoped Projects App token")
        self.assertFalse(receipt["push_attempted"])
        self.assertEqual(self.w.pushes, [])


if __name__ == "__main__":
    unittest.main()
