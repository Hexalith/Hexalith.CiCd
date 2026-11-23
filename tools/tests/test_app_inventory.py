#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Run the real offline inventory checker on parent source and disposable drift."""
from __future__ import annotations

from contextlib import contextmanager, nullcontext, redirect_stderr
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools/check_app_inventory.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


inventory = load("_test_app_inventory", CHECKER)
global_check = load("_test_app_inventory_global", ROOT / "tools/check_global.py")
POLICY = inventory.policy_document(ROOT)
DELIVER = ".github/workflows/deliver.yml"
CONTRACTS = ".github/workflows/deliver-contracts-prerequisites.yml"
QUALIFY = ".github/workflows/qualify-package-owner-access.yml"
NIGHTLY = ".github/workflows/nightly.yml"


@contextmanager
def workspace():
    with tempfile.TemporaryDirectory(prefix="app-inventory-") as directory:
        root = Path(directory)
        paths = {inventory.POLICY, *POLICY["selector_sources"]}
        paths.update(path.relative_to(ROOT).as_posix() for path in (ROOT / ".github/workflows").iterdir()
                     if path.suffix in (".yml", ".yaml"))
        for relative in paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        yield root


def document(root, path):
    return inventory.renderer.yaml_document((root / path).read_bytes(), path)


def write(root, path, value):
    (root / path).write_text(json.dumps(value, indent=2) + "\n")


def token(value, job="deliver", identity="g6_token"):
    return next(step for step in value["jobs"][job]["steps"] if step.get("id") == identity)


@contextmanager
def offline_environment():
    with tempfile.TemporaryDirectory(prefix="app-inventory-credentials-") as directory:
        # No inherited tokens, gh/Git configuration, credential homes or NO_PROXY
        # exception. The private home/config directories start completely empty.
        root = Path(directory)
        for name in ("home", "gh", "config"):
            (root / name).mkdir()
        environment = {"PATH": os.defpath, "HOME": str(root / "home"),
                       "GH_CONFIG_DIR": str(root / "gh"), "XDG_CONFIG_HOME": str(root / "config"),
                       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                       "HTTPS_PROXY": "http://127.0.0.1:1", "HTTP_PROXY": "http://127.0.0.1:1"}
        environment.update({key: os.environ[key] for key in ("TMPDIR", "TMP", "TEMP") if key in os.environ})
        yield environment


class AppInventoryTests(unittest.TestCase):
    def invoke(self, root, expected=0, boundary=None):
        with offline_environment() as environment:
            result = subprocess.run([sys.executable, "-I", CHECKER, "--project-root", root],
                                    env=environment, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        if boundary:
            self.assertIn(boundary, result.stderr)
        return result

    def test_real_parent_source_is_seven_workflows_ten_jobs_76_mints_without_secrets(self):
        result = self.invoke(ROOT)
        self.assertIn("7 workflows, 10 jobs, 76 tokens", result.stdout)
        self.assertIn("hosted state unverified", result.stdout)
        with (offline_environment() as environment,
              mock.patch.dict(os.environ, environment, clear=True),
              mock.patch("socket.socket", side_effect=AssertionError("socket access forbidden")) as socket,
              mock.patch("socket.create_connection", side_effect=AssertionError("network access forbidden")) as connect,
              mock.patch("socket.getaddrinfo", side_effect=AssertionError("DNS access forbidden")) as lookup):
            self.assertEqual(inventory.check(ROOT), {"workflows": 7, "jobs": 10, "tokens": 76})
        socket.assert_not_called()
        connect.assert_not_called()
        lookup.assert_not_called()

    def test_computed_secret_indices_fail_for_unknown_workflows_and_jobs(self):
        expressions = ("${{ secrets[format('HEXALITH_CICD_APP_{0}', 'PRIVATE_KEY')] }}",
                       "${{ secrets[inputs.secret_name] }}")
        for expression in expressions:
            for unknown_workflow in (True, False):
                with self.subTest(expression=expression, workflow=unknown_workflow), workspace() as root:
                    path = ".github/workflows/unreviewed.yaml" if unknown_workflow else DELIVER
                    value = {"on": "workflow_dispatch", "jobs": {}} if unknown_workflow else document(root, path)
                    value["jobs"]["unknown"] = {"runs-on": "ubuntu-latest",
                                               "steps": [{"run": "true", "env": {"APP": expression}}]}
                    write(root, path, value)
                    self.invoke(root, 1, path if unknown_workflow else path + "/unknown")

    def test_unreviewed_reusable_calls_fail_with_or_without_inherited_secrets(self):
        for inherited in (True, False):
            for unknown_workflow in (True, False):
                with self.subTest(inherited=inherited, workflow=unknown_workflow), workspace() as root:
                    path = ".github/workflows/unreviewed.yaml" if unknown_workflow else DELIVER
                    value = {"on": "workflow_dispatch", "jobs": {}} if unknown_workflow else document(root, path)
                    job = {"uses": "Hexalith/Hexalith.CiCd/.github/workflows/hidden.yml@" + "a" * 40}
                    if inherited:
                        job["secrets"] = "inherit"
                    value["jobs"]["unknown"] = job
                    write(root, path, value)
                    result = self.invoke(root, 1, path + "/unknown")
                    self.assertIn("unreviewed reusable workflow call", result.stderr)

    def test_unrelated_environment_names_urls_and_literal_secrets_are_harmless(self):
        for environment in ("cicd-app-preview", "CiCd-ApP-preview",
                            {"name": "development", "url": "https://example.test/cicd-app"},
                            {"name": "development", "url": "${{ steps.cicd-app.outputs.url }}"}):
            with self.subTest(environment=environment), workspace() as root:
                path = ".github/workflows/unrelated.yaml"
                write(root, path, {"on": "workflow_dispatch", "jobs": {"harmless": {
                    "runs-on": "ubuntu-latest", "environment": environment,
                    "steps": [{"run": "true", "env": {"FIRST": "${{ secrets.OTHER_SECRET }}",
                                                         "SECOND": "${{ secrets['OTHER_SECRET'] }}"}}]}}})
                self.invoke(root)

    def test_workspace_ignores_nonworkflow_directories(self):
        with workspace() as source:
            (source / ".github/workflows/notes").mkdir()
            with mock.patch.object(sys.modules[__name__], "ROOT", source), workspace() as root:
                self.assertFalse((root / ".github/workflows/notes").exists())
                self.invoke(root)

    def test_unknown_workflow_each_discovery_signal_independently(self):
        for signal in ("environment", "key", "mixed-environment", "mixed-key", "dynamic-environment"):
            with self.subTest(signal=signal), workspace() as root:
                job = {"runs-on": "ubuntu-latest", "steps": [{"run": "true"}]}
                if signal == "environment":
                    job["environment"] = {"name": "cicd-app"}
                elif signal == "mixed-environment":
                    job["environment"] = {"name": "CiCd-ApP"}
                elif signal == "dynamic-environment":
                    job["environment"] = "${{ inputs.target }}"
                else:
                    secret = "hexalith_cicd_app_private_key" if signal == "mixed-key" else "HEXALITH_CICD_APP_PRIVATE_KEY"
                    job["steps"][0]["env"] = {"APP": "${{ secrets." + secret + " }}"}
                path = ".github/workflows/unreviewed.yaml"
                write(root, path, {"on": "workflow_dispatch", "jobs": {"unknown": job}})
                self.invoke(root, 1, path)

    def test_case_variant_workflow_extensions_reach_inventory_and_lint(self):
        for extension in (".YML", ".YaMl"):
            with self.subTest(extension=extension), workspace() as root:
                path = ".github/workflows/unreviewed" + extension
                write(root, path, {"on": "workflow_dispatch", "jobs": {"unreviewed": {
                    "runs-on": "ubuntu-latest", "environment": "cicd-app", "steps": [{"run": "true"}],
                }}})
                rendered = "rendered/Hexalith.Fixture/" + path
                (root / rendered).parent.mkdir(parents=True)
                shutil.copyfile(root / path, root / rendered)
                paths = global_check.workflow_paths(root)
                self.assertIn(path, paths)
                self.assertIn(rendered, paths)
                self.assertIn("unreviewed App consumer workflow", self.invoke(root, 1, path).stderr)
                with (mock.patch.dict(os.environ, {"GITHUB_TOKEN": "fixture"}, clear=True),
                      mock.patch.object(global_check.platform, "system", return_value="Linux"),
                      mock.patch.object(global_check.platform, "machine", return_value="x86_64"),
                      self.assertRaises(global_check.CheckError) as refusal):
                    global_check.lint_workflows(root, None)
                self.assertIn("requires lowercase", str(refusal.exception))
                self.assertIn(path, str(refusal.exception))
                self.assertIn(rendered, str(refusal.exception))

    def test_unknown_job_each_discovery_signal_independently(self):
        for job in ({"environment": "cicd-app", "steps": [{"run": "true"}]},
                    {"environment": "CiCd-ApP", "steps": [{"run": "true"}]},
                    {"steps": [{"env": {"KEY": "${{ secrets.hexalith_cicd_app_private_key }}"}, "run": "true"}]},
                    {"steps": [{"env": {"KEY": "${{ secrets.HEXALITH_CICD_APP_PRIVATE_KEY }}"}, "run": "true"}]}):
            with self.subTest(job=job), workspace() as root:
                value = document(root, DELIVER)
                value["jobs"]["unreviewed"] = job
                write(root, DELIVER, value)
                self.invoke(root, 1, DELIVER + "/unreviewed")

    def test_missing_environment_or_key_still_discovers_known_consumer(self):
        for field in ("environment", "private-key"):
            with self.subTest(field=field), workspace() as root:
                value = document(root, QUALIFY)
                if field == "environment":
                    value["jobs"]["qualify"].pop(field)
                else:
                    token(value, "qualify", "token")["with"].pop(field)
                write(root, QUALIFY, value)
                self.invoke(root, 1, QUALIFY + "/qualify/" + ("token/with/" if field == "private-key" else "") + field)

    def test_top_level_key_reference_and_removed_consumer_fail(self):
        with workspace() as root:
            value = document(root, DELIVER)
            value["env"] = {"APP": "${{ secrets.HEXALITH_CICD_APP_PRIVATE_KEY }}"}
            write(root, DELIVER, value)
            self.invoke(root, 1, "outside a reviewed job")
        with workspace() as root:
            path = ".github/workflows/unreviewed.yaml"
            write(root, path, {"on": "workflow_dispatch",
                               "env": {"APP": "${{ secrets[format('HEXALITH_CICD_APP_{0}', 'PRIVATE_KEY')] }}"},
                               "jobs": {"ordinary": {"runs-on": "ubuntu-latest", "steps": [{"run": "true"}]}}})
            self.invoke(root, 1, path + ": App key reference or computed secret index outside a reviewed job")
        with workspace() as root:
            (root / QUALIFY).unlink()
            self.invoke(root, 1, "workflow inventory")

    def test_token_boundaries_reject_every_input_and_identity_change(self):
        changes = (
            ("repository", lambda step: step["with"].update(repositories="Hexalith.Projects,Hexalith.EventStore"), "/with/repositories"),
            ("owner", lambda step: step["with"].update(owner="another-owner"), "/with/owner"),
            ("permission", lambda step: step["with"].update({"permission-administration": "write"}), "/with/permission-administration"),
            ("permission-value", lambda step: step["with"].update({"permission-workflows": "admin"}), "/with/permission-workflows"),
            ("permission-omitted", lambda step: step["with"].pop("permission-contents"), "/with/permission-contents"),
            ("new-selector", lambda step: step["with"].update({"repository-ids": "1,2"}), "/with/repository-ids"),
            ("client", lambda step: step["with"].update({"client-id": "${{ vars.OTHER_APP }}"}), "/with/client-id"),
            ("identity", lambda step: step.update(id="another-token"), "/id"),
            ("condition", lambda step: step.pop("if"), "/if"),
            ("action", lambda step: step.update(uses="actions/create-github-app-token@main"), "/uses"),
        )
        for name, change, boundary in changes:
            with self.subTest(change=name), workspace() as root:
                value = document(root, DELIVER)
                change(token(value))
                write(root, DELIVER, value)
                self.invoke(root, 1, DELIVER + "/deliver/g6_token" + boundary)

    def test_dynamic_permission_and_repository_expressions_are_bound(self):
        for field, replacement in (("repositories", "${{ inputs.repository }}"),
                                   ("permission-administration", "write")):
            with self.subTest(field=field), workspace() as root:
                value = document(root, DELIVER)
                token(value, identity="module_01_token")["with"][field] = replacement
                write(root, DELIVER, value)
                self.invoke(root, 1, f"{DELIVER}/deliver/module_01_token/with/{field}")

    def test_job_condition_environment_dependency_and_matrix_are_bound(self):
        changes = (
            ("if", lambda job: job.update({"if": "${{ true }}"})),
            ("environment", lambda job: job.update(environment="another-environment")),
            ("strategy", lambda job: job["strategy"]["matrix"]["repository"].append("Hexalith.Builds")),
            ("strategy", lambda job: job["strategy"]["matrix"].update(include=[{"repository": "Hexalith.CiCd"}])),
            ("permissions", lambda job: job["permissions"].update(contents="write")),
        )
        for boundary, change in changes:
            with self.subTest(boundary=boundary), workspace() as root:
                value = document(root, QUALIFY)
                change(value["jobs"]["qualify"])
                write(root, QUALIFY, value)
                self.invoke(root, 1, QUALIFY + "/qualify/" + boundary)
        with workspace() as root:
            value = document(root, DELIVER)
            value["jobs"]["deliver"].pop("needs")
            write(root, DELIVER, value)
            self.invoke(root, 1, DELIVER + "/deliver/needs")

    def test_manual_profile_owner_operation_and_catalog_options_are_closed(self):
        for path, name in ((CONTRACTS, "profile"), (DELIVER, "delivery"),
                           (".github/workflows/dispatch-contracts-prerequisites.yml", "owner"),
                           (".github/workflows/dispatch-contracts-prerequisites.yml", "operation")):
            with self.subTest(path=path, name=name), workspace() as root:
                value = document(root, path)
                value["on"]["workflow_dispatch"]["inputs"][name]["options"].append("unreviewed")
                write(root, path, value)
                self.invoke(root, 1, path + "/context/on/workflow_dispatch/inputs/" + name + "/options")
        with workspace() as root:
            value = document(root, CONTRACTS)
            token(value, identity="publisher-token")["if"] = "${{ true }}"
            write(root, CONTRACTS, value)
            self.invoke(root, 1, CONTRACTS + "/deliver/publisher-token/if")

    def test_selector_steps_dependency_jobs_and_controller_code_are_bound(self):
        with workspace() as root:
            value = document(root, NIGHTLY)
            next(step for step in value["jobs"]["dispatch"]["steps"] if step.get("id") == "select")["run"] = "echo slot_01=Hexalith.Other >> $GITHUB_OUTPUT"
            write(root, NIGHTLY, value)
            self.invoke(root, 1, NIGHTLY + "/dispatch/select")
        with workspace() as root:
            value = document(root, CONTRACTS)
            value["jobs"]["validate"]["steps"].append({"run": "true"})
            write(root, CONTRACTS, value)
            self.invoke(root, 1, CONTRACTS + "/validate")
        for name in ("delivery_bootstrap.py", "nightly.py", "nightly_runtime.py", "deliver_contracts_prerequisites.py"):
            with self.subTest(name=name), workspace() as root:
                path = root / "tools" / name
                path.write_bytes(path.read_bytes() + b"\n# changed selector\n")
                self.invoke(root, 1, "tools/" + name)

    def test_unbound_transitive_dependency_job_fails(self):
        for path, name in ((NIGHTLY, "bump-push"), (NIGHTLY, "scan"), (DELIVER, "validate")):
            with self.subTest(path=path, name=name), workspace() as root:
                policy = json.loads((root / inventory.POLICY).read_bytes())
                policy["workflows"][path]["context_jobs"].pop(name)
                write(root, inventory.POLICY, policy)
                self.invoke(root, 1, f"{path}/{name}: dependency of an App consumer is not bound")
        with workspace() as root:
            # A renewal that approves a new needs entry must also bind the new job.
            value = document(root, DELIVER)
            value["jobs"]["helper"] = {"runs-on": "ubuntu-latest", "steps": [{"run": "true"}]}
            policy = json.loads((root / inventory.POLICY).read_bytes())
            for boundary in (value["jobs"]["deliver"], policy["workflows"][DELIVER]["jobs"]["deliver"]["boundary"]):
                needs = boundary["needs"]
                boundary["needs"] = ([needs] if isinstance(needs, str) else list(needs)) + ["helper"]
            write(root, DELIVER, value)
            write(root, inventory.POLICY, policy)
            self.invoke(root, 1, DELIVER + "/helper: dependency of an App consumer is not bound")

    def test_policy_token_entries_require_explicit_owner_key_action_and_permissions(self):
        def drop_permissions(step):
            for key in [key for key in step["with"] if key.startswith("permission-")]:
                del step["with"][key]

        changes = (
            ("owner", lambda step: step["with"].update(owner="another-owner")),
            ("permissions", drop_permissions),
            ("action", lambda step: step.update(uses="actions/other-token-action@" + "a" * 40)),
            ("key", lambda step: step["with"].update({"private-key": "${{ secrets.OTHER_KEY }}"})),
        )
        for name, change in changes:
            with self.subTest(change=name), workspace() as root:
                # Change source and policy identically: only the policy rule can refuse.
                value = document(root, QUALIFY)
                change(token(value, "qualify", "token"))
                write(root, QUALIFY, value)
                policy = json.loads((root / inventory.POLICY).read_bytes())
                entry = next(item for item in policy["workflows"][QUALIFY]["jobs"]["qualify"]["tokens"]
                             if item["step"]["id"] == "token")
                change(entry["step"])
                write(root, inventory.POLICY, policy)
                self.invoke(root, 1, "token must have explicit owner, repositories, key and permissions")
        with workspace() as root:
            policy = json.loads((root / inventory.POLICY).read_bytes())
            policy["workflows"][QUALIFY]["jobs"]["qualify"]["boundary"]["environment"] = "another-environment"
            write(root, inventory.POLICY, policy)
            self.invoke(root, 1, "expected cicd-app job boundary")

    def test_missing_added_or_duplicate_token_step_fails(self):
        for mode in ("missing", "added", "duplicate-id"):
            with self.subTest(mode=mode), workspace() as root:
                value = document(root, DELIVER)
                steps = value["jobs"]["deliver"]["steps"]
                if mode == "missing":
                    steps.remove(token(value))
                elif mode == "added":
                    steps.append(copy.deepcopy(token(value)))
                else:
                    token(value)["id"] = "cicd_token"
                write(root, DELIVER, value)
                self.invoke(root, 1, DELIVER + "/deliver")

    def test_malformed_yaml_json_policy_and_nonregular_inputs_fail_cleanly(self):
        cases = (
            (QUALIFY, b"jobs:\n  x: {}\n  x: {}\n"),
            (QUALIFY, b"jobs: [invalid]\n"),
            (QUALIFY, b"jobs: {x: null}\n"),
            (QUALIFY, b"jobs: &loop {x: *loop}\n"),
            (QUALIFY, b"jobs: [\xff"),
            (inventory.POLICY, b'{"schema":1,"schema":2}'),
            (inventory.POLICY, b"[]"),
        )
        for path, data in cases:
            with self.subTest(data=data), workspace() as root:
                (root / path).write_bytes(data)
                self.invoke(root, 1, path)
        with workspace() as root:
            path = root / QUALIFY
            path.unlink()
            path.symlink_to(ROOT / QUALIFY)
            self.invoke(root, 1, QUALIFY)
        with workspace() as root:
            value = json.loads((root / inventory.POLICY).read_bytes())
            value["workflows"][DELIVER]["jobs"]["deliver"]["tokens"][0]["index"] = -1
            write(root, inventory.POLICY, value)
            self.invoke(root, 1, "step indices")
        with workspace() as root:
            value = json.loads((root / inventory.POLICY).read_bytes())
            value["selector_sources"]["tools/../../outside.py"] = copy.deepcopy(next(iter(value["selector_sources"].values())))
            write(root, inventory.POLICY, value)
            self.invoke(root, 1, "canonical repository-relative path")

    def test_secret_free_global_gate_preserves_failure_collection(self):
        # Run the real integration at its normal position; keep unrelated global
        # work outside this focused fixture and prove later suites still run.
        with workspace() as root:
            with (mock.patch.object(global_check, "check_committed_inputs"),
                  mock.patch.object(global_check, "check_committed_render"),
                  mock.patch.object(global_check, "check_bootstrap"),
                  mock.patch.object(global_check, "selected_contract", return_value=nullcontext(object())),
                  mock.patch.object(global_check, "check_render"),
                  mock.patch.object(global_check, "check_documents"),
                  mock.patch.object(global_check.renderer, "registry", return_value=[]),
                  mock.patch.object(global_check, "check_release"),
                  mock.patch.object(global_check, "lint_workflows"),
                  mock.patch.object(global_check, "run_tool_tests") as suites,
                  redirect_stderr(io.StringIO()) as diagnostic):
                self.assertTrue(global_check.run(root))
                value = document(root, QUALIFY)
                token(value, "qualify", "token")["with"]["owner"] = "unreviewed"
                write(root, QUALIFY, value)
                self.assertFalse(global_check.run(root))
            self.assertEqual(suites.call_args_list, [mock.call(root.resolve()), mock.call(root.resolve())])
            self.assertIn("global App workflow inventory: passed", diagnostic.getvalue())
            self.assertIn(QUALIFY + "/qualify/token/with/owner", diagnostic.getvalue())
            self.assertNotIn("global selected contract/prerequisite:", diagnostic.getvalue())
        global_check.check_app_inventory(ROOT)


if __name__ == "__main__":
    unittest.main()
