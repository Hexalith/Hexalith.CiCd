#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Offline validation qualification with real Git trees and external I/O doubles."""

from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
import copy
import http.client
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
import urllib.error


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures/validate"
sys.dont_write_bytecode = True

# Reuse the renderer's synthetic tagged Git workspace, not a second schema or
# hand-written stand-in for the released readers.
import importlib.util


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


render_tests = load("_validate_render_fixtures", ROOT / "tools/tests/test_render.py")
global_check = load("_validate_global_checks", ROOT / "tools/check_global.py")
validator = load("_validate_orchestrator", ROOT / "tools/validate.py")
renderer = global_check.renderer
git = render_tests.git
run = render_tests.run


class Workspace(render_tests.Workspace):
    def __init__(self, root):
        super().__init__(root)
        git(root, "init", "--quiet", "--initial-branch=main")
        (root / ".gitmodules").write_text("")
        self.remotes = {}
        self.cloned = []

    def module(self, name="Hexalith.Fixture", actions=(), *, setup=None):
        remote = self.root.parent / (name + ".git-source")
        remote.mkdir()
        git(remote, "init", "--quiet", "--initial-branch=main")
        (remote / "README.md").write_text("Live main fixture.\n")
        for action in actions:
            path = remote / f".github/actions/{action}/action.yml"
            path.parent.mkdir(parents=True)
            shutil.copyfile(FIXTURES / "action.yml", path)
        git(remote, "add", ".")
        git(remote, "commit", "--quiet", "-m", "Live main fixture")
        revision = git(remote, "rev-parse", "HEAD").decode().strip()
        self.remotes[name] = remote
        with (self.root / ".gitmodules").open("a") as document:
            document.write(f'[submodule "references/{name}"]\n'
                           f'\tpath = references/{name}\n'
                           f'\turl = https://github.com/Hexalith/{name}.git\n')
        git(self.root, "update-index", "--add", "--cacheinfo", "160000", revision, f"references/{name}")
        self.document(setup or {"solution": "none"}, name)
        return remote

    def commit(self):
        renderer.render(self.root, check=False)
        git(self.root, "add", "setup", "templates", "rendered", "builds-version", ".gitmodules")
        git(self.root, "commit", "--quiet", "-m", "Candidate render")

    def clone(self, repository, destination):
        self.cloned.append(repository)
        run(["git", "-c", "core.hooksPath=/dev/null", "clone", "--quiet", "--no-checkout",
             "--depth=1", "--single-branch", "--branch=main", "--no-recurse-submodules",
             self.remotes[repository].as_uri(), destination])
        # No action checkout or nested submodule initialization is necessary.
        assert not (Path(destination) / ".github").exists()
        assert not (Path(destination) / ".git/modules").exists()

    def config(self, name="Hexalith.Fixture", **changes):
        path = self.output(".github/hexalith-ci.json", name)
        document = json.loads(path.read_bytes())
        document.update(changes)
        path.write_text(json.dumps(document) + "\n")


@contextmanager
def workspace():
    with tempfile.TemporaryDirectory(prefix="hexalith-validate-fixture-") as directory:
        yield Workspace(Path(directory) / "candidate")


@contextmanager
def external_global_checks(module=global_check):
    """The child suites are always stubbed: exercising this runner cannot recurse."""
    with (mock.patch.object(module, "run_tool_tests") as tests,
          mock.patch.object(module, "lint_workflows") as lint,
          mock.patch.object(module, "check_release") as release):
        yield tests, lint, release


class Api:
    def __init__(self, fixture, contract):
        self.tag = contract.tag
        self.commit = contract.revision
        self.raw = git(fixture.builds, "rev-parse", f"refs/tags/{self.tag}").decode().strip()
        self.release = json.loads((FIXTURES / "release.json").read_bytes())
        self.release["tag_name"] = self.tag
        kind = git(fixture.builds, "cat-file", "-t", self.raw).decode().strip()
        self.ref = {"ref": f"refs/tags/{self.tag}", "object": {"type": kind, "sha": self.raw}}
        # Live main is a later commit: the production case is "ahead".
        self.main = {"ref": "refs/heads/main", "object": {"type": "commit", "sha": "c" * 40}}
        self.compare = {"status": "ahead", "base_commit": {"sha": self.commit},
                        "merge_base_commit": {"sha": self.commit}, "ahead_by": 3, "behind_by": 0}
        self.tags = {}
        if kind == "tag":
            self.tags[self.raw] = {"sha": self.raw, "tag": self.tag,
                                   "object": {"type": "commit", "sha": self.commit}}
        self.calls = []

    def __call__(self, path):
        self.calls.append(path)
        main = self.main.get("object", {}).get("sha") if isinstance(self.main.get("object"), dict) else None
        # Exact endpoints and argument order: a reversed or self-comparison
        # must not silently receive the acceptable compare document.
        responses = {f"releases/tags/{self.tag}": self.release, f"git/ref/tags/{self.tag}": self.ref,
                     "git/ref/heads/main": self.main,
                     f"compare/{self.commit}...{main}?per_page=1&page=2": self.compare}
        responses.update({f"git/tags/{sha}": document for sha, document in self.tags.items()})
        if path not in responses:
            raise AssertionError(f"Unexpected API read: {path}")
        return copy.deepcopy(responses[path])


class ValidateTests(unittest.TestCase):
    def verdict(self, fixture, *, global_ok=True):
        with (mock.patch.object(validator, "global_checks", return_value=global_ok) as global_call,
              mock.patch.object(validator, "clone_module", side_effect=fixture.clone),
              redirect_stderr(io.StringIO()) as diagnostic):
            verdict, status = validator.validate(fixture.root)
        global_call.assert_called_once_with(fixture.root)
        return verdict, status, diagnostic.getvalue()

    def test_empty_registry_is_valid(self):
        with workspace() as fixture:
            fixture.commit()
            (fixture.root / "setup/NotRegistered.yaml").write_text(": [ invalid")
            with external_global_checks() as (tests, lint, release), redirect_stderr(io.StringIO()):
                self.assertTrue(global_check.run(fixture.root))
            tests.assert_called_once()
            lint.assert_called_once()
            release.assert_called_once()
            self.assertEqual(self.verdict(fixture)[:2], ({"global": True, "modules": []}, 0))

    def test_sorted_passing_modules_include_no_hook_clone(self):
        with workspace() as fixture:
            fixture.module("Hexalith.Zeta", ("after-unit-tests",),
                           setup={"solution": "src/Zeta.slnx", "hooks": ["after-unit-tests"]})
            fixture.module("Hexalith.Alpha")
            fixture.commit()
            self.assertEqual(self.verdict(fixture)[:2],
                             ({"global": True, "modules": ["Hexalith.Alpha", "Hexalith.Zeta"]}, 0))
            self.assertEqual(fixture.cloned, ["Hexalith.Alpha", "Hexalith.Zeta"])

    def test_enabled_windows_job_action_availability_controls_only_its_module(self):
        for present in (True, False):
            with self.subTest(present=present), workspace() as fixture:
                fixture.module("Hexalith.Alpha")
                fixture.module("Hexalith.Windows", actions=("windows-tests",) if present else (),
                               setup={"solution": "src/Windows.slnx",
                                      "jobs": {"windows-tests": {"runner": "windows-latest"}}})
                fixture.commit()
                for global_ok in (True, False):
                    verdict, status, diagnostic = self.verdict(fixture, global_ok=global_ok)
                    expected = ["Hexalith.Alpha", "Hexalith.Windows"] if present else ["Hexalith.Alpha"]
                    self.assertEqual(verdict, {"global": global_ok, "modules": expected})
                    self.assertEqual(status, int(not (global_ok and present)))
                    if not present:
                        self.assertIn("windows-tests/action.yml", diagnostic)

    def test_global_and_module_failures_remain_independent(self):
        with workspace() as fixture:
            fixture.module("Hexalith.Alpha")
            fixture.module("Hexalith.Bad", setup={"solution": "src/Bad.slnx", "hooks": ["nightly"]})
            fixture.module("Hexalith.Zeta")
            fixture.commit()
            for global_ok in (True, False):
                with self.subTest(global_ok=global_ok):
                    verdict, status, diagnostic = self.verdict(fixture, global_ok=global_ok)
                    self.assertEqual(verdict, {"global": global_ok, "modules": ["Hexalith.Alpha", "Hexalith.Zeta"]})
                    self.assertEqual(status, 1)
                    self.assertIn("Hexalith.Bad", diagnostic)
                    self.assertIn("nightly", diagnostic)

    def test_cli_emits_identical_verdict_before_nonzero_exit(self):
        with workspace() as fixture:
            fixture.module("Hexalith.Alpha")
            fixture.module("Hexalith.Bad", setup={"solution": "src/Bad.slnx", "hooks": ["nightly"]})
            fixture.commit()
            output = fixture.root / "github-output"
            harness = fixture.root.parent / "cli.py"
            harness.write_text(
                "import importlib.util, pathlib, subprocess, sys\n"
                f"spec=importlib.util.spec_from_file_location('validator_cli', {str(ROOT / 'tools/validate.py')!r})\n"
                "module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)\n"
                "module.global_checks=lambda project: False\n"
                f"remotes={dict((name, str(path)) for name, path in fixture.remotes.items())!r}\n"
                "def clone(name, destination):\n"
                " subprocess.run(['git','-c','core.hooksPath=/dev/null','clone','--quiet','--no-checkout','--depth=1','--branch=main','--no-recurse-submodules',pathlib.Path(remotes[name]).as_uri(),str(destination)],check=True)\n"
                "module.clone_module=clone\n"
                "raise SystemExit(module.main())\n")
            result = run([sys.executable, "-I", harness, "--project-root", fixture.root],
                         env={"GITHUB_OUTPUT": str(output)}, check=False)
            expected = b'{"global":false,"modules":["Hexalith.Alpha"]}'
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, expected + b"\n")
            self.assertEqual(output.read_bytes(), b"verdict=" + expected + b"\n")
            self.assertIn(b"Hexalith.Bad", result.stderr)
            self.assertNotIn(b"Traceback", result.stderr)

    def test_local_checkout_is_never_action_source(self):
        with workspace() as fixture:
            remote = fixture.module(actions=("after-unit-tests",),
                                    setup={"solution": "src/F.slnx", "hooks": ["after-unit-tests"]})
            (remote / ".gitmodules").write_text('[submodule "nested"]\n\tpath = references/Nested\n\turl = https://example.invalid/never-clone.git\n')
            revision = git(remote, "rev-parse", "HEAD").decode().strip()
            git(remote, "update-index", "--add", "--cacheinfo", "160000", revision, "references/Nested")
            git(remote, "add", ".gitmodules")
            git(remote, "commit", "--quiet", "-m", "Nested submodule must remain uninitialized")
            fixture.commit()
            local = fixture.root / "references/Hexalith.Fixture"
            local.mkdir()
            (local / "untracked-secret").write_text("untouched")
            before = render_tests.file_bytes(local)
            self.assertEqual(self.verdict(fixture)[1], 0)
            self.assertEqual(render_tests.file_bytes(local), before)
            git(remote, "rm", "--quiet", ".github/actions/after-unit-tests/action.yml")
            git(remote, "commit", "--quiet", "-m", "Remove action on live main")
            action = local / ".github/actions/after-unit-tests/action.yml"
            action.parent.mkdir(parents=True)
            shutil.copyfile(FIXTURES / "action.yml", action)
            before = render_tests.file_bytes(local)
            self.assertEqual(self.verdict(fixture)[1], 1)
            self.assertEqual(render_tests.file_bytes(local), before)

    def test_action_yaml_or_symlink_does_not_satisfy_committed_action_yml(self):
        for failure in ("yaml-only", "symlink"):
            with self.subTest(failure=failure), workspace() as fixture:
                remote = fixture.module(actions=("nightly",), setup={"solution": "src/F.slnx", "hooks": ["nightly"]})
                action = remote / ".github/actions/nightly/action.yml"
                if failure == "yaml-only":
                    action.rename(action.with_suffix(".yaml"))
                else:
                    action.unlink()
                    action.symlink_to("../../../README.md")
                git(remote, "add", ".github")
                git(remote, "commit", "--quiet", "-m", "Invalid action tree")
                fixture.commit()
                verdict, status, diagnostic = self.verdict(fixture)
                self.assertEqual(verdict, {"global": True, "modules": []})
                self.assertEqual(status, 1)
                self.assertIn("nightly/action.yml", diagnostic)

    def test_clone_failure_does_not_drop_other_modules(self):
        with workspace() as fixture:
            fixture.module("Hexalith.Alpha")
            fixture.module("Hexalith.Broken")
            fixture.commit()
            def clone(repository, destination):
                if repository == "Hexalith.Broken":
                    raise OSError("anonymous clone failed")
                fixture.clone(repository, destination)
            with (mock.patch.object(validator, "global_checks", return_value=True),
                  mock.patch.object(validator, "clone_module", side_effect=clone),
                  redirect_stderr(io.StringIO()) as diagnostic):
                verdict, status = validator.validate(fixture.root)
            self.assertEqual(verdict, {"global": True, "modules": ["Hexalith.Alpha"]})
            self.assertEqual(status, 1)
            self.assertIn("Hexalith.Broken", diagnostic.getvalue())

    def test_invalid_candidate_configuration_is_module_and_global_failure(self):
        cases = {
            "malformed": b'{"schema":',
            "unsupported": {"schema": "hexalith.ci.v999"},
            "missing-key": {"tests": None},
            "overlapping-hook-job": {"solution": "src/F.slnx", "hooks": ["nightly"], "jobs": {"nightly": {"runner": "windows-latest"}}},
            "disabled-exclusion": {"solution": "src/F.slnx", "tests": {"integration": [], "exclude": {"test/F.csproj": "nightly"}}},
            "stale-builds-tag": {"buildsTag": "v0.0.0"},
        }
        for case, changes in cases.items():
            with self.subTest(case=case), workspace() as fixture:
                fixture.module()
                fixture.commit()
                path = fixture.output(".github/hexalith-ci.json")
                if isinstance(changes, bytes):
                    path.write_bytes(changes)
                else:
                    fixture.config(**changes)
                self.assertEqual(self.verdict(fixture, global_ok=False)[:2], ({"global": False, "modules": []}, 1))
                with external_global_checks(), redirect_stderr(io.StringIO()):
                    self.assertFalse(global_check.run(fixture.root))

    def test_missing_configuration_fails_only_affected_module(self):
        with workspace() as fixture:
            fixture.module("Hexalith.Alpha")
            fixture.module("Hexalith.Bad")
            fixture.commit()
            fixture.output(".github/hexalith-ci.json", "Hexalith.Bad").unlink()
            self.assertEqual(self.verdict(fixture, global_ok=False)[:2],
                             ({"global": False, "modules": ["Hexalith.Alpha"]}, 1))

    def test_registration_requires_declaration_and_committed_gitlink(self):
        for failure in ("missing-declaration", "regular-file", "wrong-path"):
            with self.subTest(failure=failure), workspace() as fixture:
                fixture.module()
                fixture.commit()
                if failure == "missing-declaration":
                    (fixture.root / ".gitmodules").write_text("")
                    git(fixture.root, "add", ".gitmodules")
                elif failure == "wrong-path":
                    path = fixture.root / ".gitmodules"
                    path.write_text(path.read_text().replace("path = references/", "path = elsewhere/"))
                    git(fixture.root, "add", ".gitmodules")
                else:
                    oid = git(fixture.root, "hash-object", "-w", "--stdin", input=b"not a gitlink\n").decode().strip()
                    git(fixture.root, "update-index", "--add", "--cacheinfo", "100644", oid, "references/Hexalith.Fixture")
                git(fixture.root, "commit", "--quiet", "-m", "Invalid declaration")
                self.assertEqual(self.verdict(fixture)[1], 1)

    def test_submodule_declaration_comes_from_head_not_restored_worktree(self):
        with workspace() as fixture:
            fixture.module("Hexalith.Alpha")
            fixture.module("Hexalith.Bad")
            fixture.commit()
            path = fixture.root / ".gitmodules"
            original = path.read_bytes()
            path.write_text("")
            self.assertEqual(self.verdict(fixture)[:2],
                             ({"global": True, "modules": ["Hexalith.Alpha", "Hexalith.Bad"]}, 0))
            path.write_bytes(original)
            git(fixture.root, "config", "--file", path, "--remove-section", "submodule.references/Hexalith.Bad")
            git(fixture.root, "add", ".gitmodules")
            git(fixture.root, "commit", "--quiet", "-m", "Remove candidate declaration")
            path.write_bytes(original)
            verdict, status, diagnostic = self.verdict(fixture)
            self.assertEqual(verdict, {"global": True, "modules": ["Hexalith.Alpha"]})
            self.assertEqual(status, 1)
            self.assertIn("Hexalith.Bad", diagnostic)

    def test_submodule_declaration_requires_url_without_restricting_spelling(self):
        for url in (None, "", "   ", "../different-public-name.git"):
            with self.subTest(url=url), workspace() as fixture:
                fixture.module()
                fixture.commit()
                path = fixture.root / ".gitmodules"
                key = "submodule.references/Hexalith.Fixture.url"
                if url is None:
                    git(fixture.root, "config", "--file", path, "--unset", key)
                else:
                    git(fixture.root, "config", "--file", path, key, url)
                git(fixture.root, "add", ".gitmodules")
                git(fixture.root, "commit", "--quiet", "-m", "URL fixture")
                verdict, status, _ = self.verdict(fixture)
                valid = bool(url and url.strip())
                self.assertEqual(verdict, {"global": True, "modules": ["Hexalith.Fixture"] if valid else []})
                self.assertEqual(status, int(not valid))

    def test_tag_named_main_cannot_replace_live_main_branch(self):
        with workspace() as fixture:
            fixture.module("Hexalith.Alpha")
            remote = fixture.module("Hexalith.TagOnly", actions=("nightly",),
                                    setup={"solution": "src/Tag.slnx", "hooks": ["nightly"]})
            git(remote, "tag", "main")
            git(remote, "branch", "--move", "archive")
            missing = run(["git", "-C", remote, "show-ref", "--verify", "refs/heads/main"], check=False)
            self.assertNotEqual(missing.returncode, 0)
            fixture.commit()
            verdict, status, diagnostic = self.verdict(fixture)
            self.assertEqual(verdict, {"global": True, "modules": ["Hexalith.Alpha"]})
            self.assertEqual(status, 1)
            self.assertIn("Hexalith.TagOnly", diagnostic)

    def test_cloned_main_must_match_fetched_origin_main(self):
        with workspace() as fixture:
            fixture.module()
            fixture.commit()
            def clone(repository, destination):
                fixture.clone(repository, destination)
                tree = git(destination, "rev-parse", "HEAD^{tree}").decode().strip()
                other = git(destination, "commit-tree", tree, input=b"Different fetched main\n").decode().strip()
                git(destination, "update-ref", "refs/remotes/origin/main", other)
            with (mock.patch.object(validator, "global_checks", return_value=True),
                  mock.patch.object(validator, "clone_module", side_effect=clone),
                  redirect_stderr(io.StringIO()) as diagnostic):
                verdict, status = validator.validate(fixture.root)
            self.assertEqual(verdict, {"global": True, "modules": []})
            self.assertEqual(status, 1)
            self.assertIn("fetched origin/main", diagnostic.getvalue())

    def test_unusable_registry_and_missing_contract_are_conservative(self):
        for failure in ("reserved", "symlink", "missing-tag"):
            with self.subTest(failure=failure), workspace() as fixture:
                fixture.module()
                fixture.commit()
                if failure == "reserved":
                    fixture.document({"solution": "none"}, "Hexalith.Builds")
                elif failure == "symlink":
                    path = fixture.root / "setup/Hexalith.Fixture.yml"
                    path.unlink()
                    path.symlink_to(fixture.root / "setup/README.md")
                else:
                    (fixture.root / "builds-version").write_text("v999.0.0\n")
                self.assertEqual(self.verdict(fixture)[:2], ({"global": False, "modules": []}, 1))

    def test_old_or_incomplete_pin_fails_prerequisite_without_head_fallback(self):
        for missing in ("schemas/hexalith.perimeter.v1.json", "Github/lib/perimeter.py", "Github/lib/perimeter_config.py"):
            with self.subTest(missing=missing), workspace() as fixture:
                original = git(fixture.builds, "rev-parse", fixture.tag).decode().strip()
                incomplete = fixture.change_tag({missing: None})
                # A newer HEAD does contain the prerequisite; only the selected
                # older/incomplete release must decide this result.
                git(fixture.builds, "update-ref", "refs/heads/fixture", original)
                git(fixture.builds, "update-ref", "refs/tags/v4.0.0", incomplete)
                (fixture.root / "builds-version").write_text("v4.0.0\n")
                with self.assertRaisesRegex(ValueError, "(?i)perimeter.*prerequisite|prerequisite.*perimeter"):
                    with global_check.selected_contract(fixture.root):
                        self.fail("Incomplete selected tag was loaded")

    def test_tagged_contract_does_not_read_mutable_builds_head(self):
        with workspace() as fixture:
            fixture.module()
            fixture.commit()
            fixture.change_tag({"Github/lib/ci_config.py": b"raise RuntimeError('HEAD must never execute')\n"}, move_tag=False)
            with global_check.selected_contract(fixture.root) as contract:
                self.assertNotIn(b"HEAD must never execute", (contract.root / "Github/lib/ci_config.py").read_bytes())
                global_check.check_documents(fixture.root, renderer.registry(fixture.root), contract)
            self.assertEqual(self.verdict(fixture)[1], 0)


class GlobalTests(unittest.TestCase):
    def test_permission_union_uses_effective_mappings_and_maximum_access(self):
        for levels in (("read", "none"), ("none", "read"), ("write", "none", "read")):
            document = {"permissions": {}, "jobs": {
                str(index): {"permissions": {"contents": permission}}
                for index, permission in enumerate(levels)}}
            expected = "write" if "write" in levels else "read"
            self.assertEqual(global_check.permission_union(document), {"contents": expected})
        self.assertEqual(global_check.permission_union({"permissions": {}, "jobs": {"inherited": {}}}), {})
        self.assertEqual(global_check.permission_union({
            "permissions": {"contents": "read", "actions": "none"},
            "jobs": {"inherited": {}, "overridden": {"permissions": {"contents": "none"}}}}),
            {"contents": "read", "actions": "none"})

    def test_restore_enabled_tag_requires_exact_write_union_and_rejects_less_or_more_access(self):
        with workspace() as fixture:
            fixture.module()
            path = ".github/workflows/ci.yml"
            manifest = renderer.yaml_document(git(fixture.builds, "show", f"{fixture.tag}:{path}"), "tagged ci")
            manifest["jobs"]["restore"] = {
                "permissions": {"contents": "write", "actions": "write"},
                "runs-on": "ubuntu-latest", "steps": [{"uses": "$/Github/restore"}],
            }
            revision = fixture.change_tag({path: json.dumps(manifest).encode()}, move_tag=False)
            fixture.tag = "v5.2.0"
            git(fixture.builds, "update-ref", f"refs/tags/{fixture.tag}", revision)
            (fixture.root / "builds-version").write_text(fixture.tag + "\n")
            fixture.commit()
            with global_check.selected_contract(fixture.root) as contract:
                global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
                caller = fixture.output(path)
                document = renderer.yaml_document(caller.read_bytes(), "rendered caller")
                for permissions in ({"contents": "read"}, {"contents": "write"},
                        {"contents": "write", "actions": "read"},
                        {"contents": "write", "actions": "write", "id-token": "write"}):
                    with self.subTest(permissions=permissions):
                        document["jobs"]["ci"]["permissions"] = permissions
                        caller.write_text(json.dumps(document))
                        with self.assertRaisesRegex(ValueError, "permission union"):
                            global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)

    def test_callable_literal_types_preserve_expressions_and_untyped_composites(self):
        for declared, literal, invalid in (("string", "value", True), ("boolean", True, "true"),
                                           ("number", 2, True)):
            declarations = {"input": {"type": declared}}
            global_check.arguments_supplied({"input": literal}, declarations, "fixture")
            global_check.arguments_supplied({"input": "${{ inputs.dynamic }}"}, declarations, "fixture")
            with self.assertRaisesRegex(ValueError, "declared type"):
                global_check.arguments_supplied({"input": invalid}, declarations, "fixture")
        global_check.arguments_supplied({"input": True}, {"input": {"required": True}}, "composite")

    def test_actual_callers_reject_interface_permission_output_and_tag_drift(self):
        for case in ("unknown-input", "literal-input-type", "unknown-secret", "permission", "output", "workflow-tag", "action-tag", "missing-input"):
            with self.subTest(case=case), workspace() as fixture:
                fixture.document({"solution": "src/F.slnx", "jobs": {"windows-tests": {"runner": "windows-latest"}}})
                fixture.commit()
                path = fixture.output(".github/workflows/release.yml" if case == "missing-input" else ".github/workflows/ci.yml")
                document = renderer.yaml_document(path.read_bytes(), str(path))
                if case == "unknown-input":
                    document["jobs"]["ci"]["with"] = {"not-declared": "x"}
                elif case == "literal-input-type":
                    document["jobs"]["ci"]["with"] = {"module-root": True}
                elif case == "unknown-secret":
                    document["jobs"]["ci"]["secrets"]["not-declared"] = "x"
                elif case == "permission":
                    document["jobs"]["ci"]["permissions"] = {"contents": "write"}
                elif case == "output":
                    document["jobs"]["windows-windows-tests"]["steps"][0]["with"]["solution"] = "${{ needs.ci.outputs.not-declared }}"
                elif case == "workflow-tag":
                    document["jobs"]["ci"]["uses"] = document["jobs"]["ci"]["uses"].replace(fixture.tag, "v0.0.0")
                elif case == "action-tag":
                    step = document["jobs"]["windows-windows-tests"]["steps"][0]
                    step["uses"] = step["uses"].replace(fixture.tag, "v0.0.0")
                else:
                    del document["jobs"]["publish"]["steps"][0]["with"]["version"]
                path.write_text(json.dumps(document))
                with global_check.selected_contract(fixture.root) as contract:
                    with self.assertRaises(ValueError):
                        global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)

    def test_bracket_output_references_require_declared_outputs_and_needs(self):
        with workspace() as fixture:
            fixture.document({"solution": "src/F.slnx", "jobs": {"windows-tests": {"runner": "windows-latest"}}})
            fixture.commit()
            path = fixture.output(".github/workflows/ci.yml")
            original = renderer.yaml_document(path.read_bytes(), str(path))
            with global_check.selected_contract(fixture.root) as contract:
                for syntax in ("needs['ci'].outputs['%s']", 'needs["ci"].outputs["%s"]',
                               "needs.ci.outputs['%s']", "needs['ci'].outputs.%s",
                               "needs [ 'ci' ] . outputs [ '%s' ]"):
                    for output in ("solution", "not-declared"):
                        with self.subTest(syntax=syntax, output=output):
                            document = copy.deepcopy(original)
                            job = document["jobs"]["windows-windows-tests"]
                            job["steps"][0]["with"]["solution"] = "${{ " + syntax % output + " }}"
                            path.write_text(json.dumps(document))
                            if output == "solution":
                                global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
                            else:
                                with self.assertRaisesRegex(ValueError, "not-declared"):
                                    global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
                document = copy.deepcopy(original)
                job = document["jobs"]["windows-windows-tests"]
                job.pop("needs")
                job["steps"][0]["with"]["solution"] = "${{ needs['ci'].outputs['solution'] }}"
                path.write_text(json.dumps(document))
                with self.assertRaisesRegex(ValueError, "undeclared output reference"):
                    global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)

    def test_committed_render_cannot_use_an_untracked_restored_setup_cause(self):
        with workspace() as fixture:
            fixture.module()
            fixture.commit()
            git(fixture.root, "rm", "--cached", "setup/Hexalith.Fixture.yml")
            git(fixture.root, "commit", "--quiet", "-m", "Candidate omits setup cause")
            global_check.check_committed_render(fixture.root)
            with global_check.selected_contract(fixture.root) as contract:
                global_check.check_render(fixture.root, contract)
            with self.assertRaisesRegex(ValueError, "setup/Hexalith.Fixture.yml"):
                global_check.check_committed_inputs(fixture.root)
            with external_global_checks(), redirect_stderr(io.StringIO()) as diagnostic:
                self.assertFalse(global_check.run(fixture.root))
            self.assertIn("committed render inputs", diagnostic.getvalue())

    def run_global(self, fixture):
        with external_global_checks(), redirect_stderr(io.StringIO()) as diagnostic:
            passed = global_check.run(fixture.root)
        return passed, diagnostic.getvalue()

    def test_runner_fails_when_only_one_render_or_interface_check_fails(self):
        with self.subTest(case="stale committed render"), workspace() as fixture:
            fixture.module()
            fixture.commit()
            fixture.document({"solution": "src/Changed.slnx"})
            git(fixture.root, "add", "setup")
            git(fixture.root, "commit", "--quiet", "-m", "Setup committed without its render")
            passed, diagnostic = self.run_global(fixture)
            self.assertFalse(passed)
            self.assertIn("global render reproducibility: render differs", diagnostic)
            for label in ("committed render inputs", "committed render", "schemas and caller interfaces"):
                self.assertIn(f"global {label}: passed", diagnostic)
        with self.subTest(case="uncommitted fresh render"), workspace() as fixture:
            fixture.module()
            fixture.commit()
            fixture.document({"solution": "src/Changed.slnx"})
            git(fixture.root, "add", "setup")
            git(fixture.root, "commit", "--quiet", "-m", "Setup committed; render left in the working tree")
            renderer.render(fixture.root, check=False)
            passed, diagnostic = self.run_global(fixture)
            self.assertFalse(passed)
            self.assertIn("global committed render: uncommitted rendered paths", diagnostic)
            for label in ("committed render inputs", "render reproducibility", "schemas and caller interfaces"):
                self.assertIn(f"global {label}: passed", diagnostic)
        with self.subTest(case="new required tagged input"), workspace() as fixture:
            fixture.document({"solution": "none"})
            fixture.commit()
            manifest = renderer.yaml_document(git(fixture.builds, "show", f"{fixture.tag}:.github/workflows/ci.yml"), "tagged ci")
            manifest["on"]["workflow_call"]["inputs"]["new-required"] = {"type": "string", "required": True}
            fixture.change_tag({".github/workflows/ci.yml": json.dumps(manifest).encode()})
            passed, diagnostic = self.run_global(fixture)
            self.assertFalse(passed)
            self.assertIn("global schemas and caller interfaces:", diagnostic)
            self.assertIn("new-required", diagnostic)
            for label in ("committed render inputs", "committed render", "render reproducibility"):
                self.assertIn(f"global {label}: passed", diagnostic)

    def test_document_tags_must_match_builds_version(self):
        for case in ("ci", "perimeter"):
            with self.subTest(case=case), workspace() as fixture:
                fixture.module()
                fixture.commit()
                if case == "ci":
                    fixture.config(buildsTag="v0.0.0")
                    message = "buildsTag differs"
                else:
                    path = fixture.root / "rendered/Hexalith.Fixture.perimeter.json"
                    document = json.loads(path.read_bytes())
                    entry = next(item for item in document["entries"] if "buildsTag" in item)
                    entry["buildsTag"] = "v0.0.0"
                    path.write_text(json.dumps(document) + "\n")
                    message = "perimeter gitlink tag differs"
                with global_check.selected_contract(fixture.root) as contract:
                    with self.assertRaisesRegex(ValueError, message):
                        global_check.check_documents(fixture.root, renderer.registry(fixture.root), contract)

    def test_plain_job_outputs_are_declared_producers(self):
        with workspace() as fixture:
            fixture.document({"solution": "src/F.slnx", "jobs": {"windows-tests": {"runner": "windows-latest"}}})
            fixture.commit()
            path = fixture.output(".github/workflows/ci.yml")
            original = renderer.yaml_document(path.read_bytes(), str(path))
            with global_check.selected_contract(fixture.root) as contract:
                for output in ("value", "undeclared"):
                    with self.subTest(output=output):
                        document = copy.deepcopy(original)
                        document["jobs"]["producer"] = {"runs-on": "ubuntu-latest", "permissions": {},
                                                        "outputs": {"value": "${{ steps.value.outputs.value }}"},
                                                        "steps": [{"id": "value", "run": "echo value=1 >> \"$GITHUB_OUTPUT\""}]}
                        job = document["jobs"]["windows-windows-tests"]
                        job["needs"] = ["ci", "producer"]
                        job["steps"][0]["with"]["solution"] = "${{ needs.producer.outputs.%s }}" % output
                        path.write_text(json.dumps(document))
                        if output == "value":
                            global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
                        else:
                            with self.assertRaisesRegex(ValueError, "undeclared output reference"):
                                global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)

    def test_global_cli_exit_status_reflects_runner_verdict(self):
        for failing in (False, True):
            with self.subTest(failing=failing), workspace() as fixture:
                fixture.commit()
                if failing:
                    (fixture.root / "rendered/uncommitted").write_text("unexpected\n")
                harness = fixture.root.parent / "global_cli.py"
                harness.write_text(
                    "import importlib.util, sys\n"
                    "sys.dont_write_bytecode = True\n"
                    f"spec=importlib.util.spec_from_file_location('global_cli', {str(ROOT / 'tools/check_global.py')!r})\n"
                    "module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)\n"
                    "module.run_tool_tests = module.lint_workflows = module.check_release = lambda *arguments: None\n"
                    "raise SystemExit(module.main())\n")
                result = run([sys.executable, "-I", harness, "--project-root", fixture.root], check=False)
                self.assertEqual(result.returncode, int(failing))
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"global committed render: " + (b"uncommitted" if failing else b"passed"), result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)

    def test_unexpected_http_exception_is_collected_and_later_checks_run(self):
        with workspace() as fixture:
            fixture.commit()
            with external_global_checks() as (tests, lint, release), redirect_stderr(io.StringIO()) as diagnostic:
                release.side_effect = http.client.IncompleteRead(b"partial")
                self.assertFalse(global_check.run(fixture.root))
            lint.assert_called_once()
            tests.assert_called_once()
            self.assertIn("global acceptable Builds publication: IncompleteRead", diagnostic.getvalue())

    def test_committed_inputs_compare_pin_registry_and_used_templates_only(self):
        for cause in ("builds-version", "setup/Hexalith.Fixture.yml", "templates/perimeter.json.j2"):
            with self.subTest(cause=cause), workspace() as fixture:
                fixture.module()
                fixture.commit()
                path = fixture.root / cause
                path.write_bytes(path.read_bytes() + b" ")
                with self.assertRaisesRegex(ValueError, "uncommitted render inputs"):
                    global_check.check_committed_inputs(fixture.root)
        with workspace() as fixture:
            fixture.module()
            fixture.commit()
            (fixture.root / "setup/Hexalith.Fixture.yml").unlink()
            with self.assertRaisesRegex(ValueError, "setup/Hexalith.Fixture.yml"):
                global_check.check_committed_inputs(fixture.root)
        with workspace() as fixture:
            fixture.commit()
            for relative in ("planning/evidence.md", "tools/unrelated.py", "templates/unused.j2", "setup/README.md"):
                path = fixture.root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Unrelated change is allowed.\n")
            global_check.check_committed_inputs(fixture.root)

    def test_new_required_tagged_callable_argument_is_detected(self):
        with workspace() as fixture:
            fixture.document({"solution": "none"})
            fixture.commit()
            manifest = renderer.yaml_document(git(fixture.builds, "show", f"{fixture.tag}:.github/workflows/ci.yml"), "tagged ci")
            manifest["on"]["workflow_call"]["inputs"]["new-required"] = {"type": "string", "required": True}
            fixture.change_tag({".github/workflows/ci.yml": json.dumps(manifest).encode()})
            with global_check.selected_contract(fixture.root) as contract:
                with self.assertRaisesRegex(ValueError, "new-required"):
                    global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)

    def test_committed_render_detects_add_delete_bytes_and_modes_only_inside_output(self):
        cases = ("bytes", "added", "deleted", "executable", "symlink")
        for case in cases:
            with self.subTest(case=case), workspace() as fixture:
                fixture.module()
                fixture.commit()
                target = fixture.output(".github/hexalith-ci.json")
                if case == "bytes":
                    target.write_bytes(target.read_bytes() + b" ")
                elif case == "added":
                    (fixture.root / "rendered/uncommitted").write_text("unexpected")
                elif case == "deleted":
                    target.unlink()
                elif case == "executable":
                    target.chmod(0o755)
                else:
                    target.unlink()
                    target.symlink_to(fixture.root / "builds-version")
                with self.assertRaises((ValueError, OSError)):
                    global_check.check_committed_render(fixture.root)
        with workspace() as fixture:
            fixture.commit()
            (fixture.root / "unrelated-planning.md").write_text("Allowed dirty evidence.\n")
            fixture.change_tag({"unrelated-head": b"later Builds HEAD\n"}, move_tag=False)
            global_check.check_committed_render(fixture.root)

    def test_render_and_committed_comparisons_cover_both_directions(self):
        with workspace() as fixture:
            fixture.module()
            fixture.commit()
            fixture.document({"solution": "src/F.slnx"})
            renderer.render(fixture.root, check=False)
            with global_check.selected_contract(fixture.root) as contract:
                global_check.check_render(fixture.root, contract)
            with self.assertRaises(ValueError):
                global_check.check_committed_render(fixture.root)
            git(fixture.root, "checkout", "--", "rendered")
            global_check.check_committed_render(fixture.root)
            with global_check.selected_contract(fixture.root) as contract:
                with self.assertRaises(ValueError):
                    global_check.check_render(fixture.root, contract)

    def test_committed_generated_executable_or_symlink_modes_fail(self):
        for mode in ("100755", "120000"):
            with self.subTest(mode=mode), workspace() as fixture:
                fixture.module()
                fixture.commit()
                target = "rendered/Hexalith.Fixture/.github/hexalith-ci.json"
                oid = git(fixture.root, "rev-parse", "HEAD:" + target).decode().strip()
                git(fixture.root, "update-index", "--cacheinfo", mode, oid, target)
                git(fixture.root, "commit", "--quiet", "-m", "Invalid committed mode")
                with self.assertRaisesRegex(ValueError, "mode"):
                    global_check.check_committed_render(fixture.root)

    def test_global_runner_collects_test_lint_release_failures_without_recursion(self):
        with workspace() as fixture:
            fixture.commit()
            with external_global_checks() as (tests, lint, release), redirect_stderr(io.StringIO()) as diagnostic:
                tests.side_effect = ValueError("test suite failed")
                lint.side_effect = ValueError("lint failed")
                release.side_effect = ValueError("release unverified")
                self.assertFalse(global_check.run(fixture.root))
            tests.assert_called_once()
            lint.assert_called_once()
            release.assert_called_once()
            for message in ("test suite failed", "lint failed", "release unverified"):
                self.assertIn(message, diagnostic.getvalue())

    def test_tool_suite_runner_executes_each_locked_suite_once_without_lint(self):
        with workspace() as fixture:
            directory = fixture.root / "tools/tests"
            directory.mkdir(parents=True)
            for name in ("test_render.py", "test_validate.py"):
                (directory / name).write_text("# fixture suite\n")
            with mock.patch.object(global_check, "command", return_value=b"") as command:
                global_check.run_tool_tests(fixture.root)
            self.assertEqual(command.call_count, 2)
            for call in command.call_args_list:
                arguments = list(map(str, call.args[0]))
                self.assertIn("--locked", arguments)
                self.assertNotIn("--lint", arguments)
                self.assertGreater(call.kwargs["timeout"], 0)

    def test_workflow_lints_receive_actual_explicit_paths_and_reject_incomplete_results(self):
        with workspace() as fixture:
            fixture.module()
            fixture.commit()
            workflow = fixture.root / ".github/workflows/deliver.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: fixture\n")
            expected = [".github/workflows/deliver.yml",
                        "rendered/Hexalith.Fixture/.github/workflows/ci.yml",
                        "rendered/Hexalith.Fixture/.github/workflows/release.yml"]
            self.assertEqual(global_check.workflow_paths(fixture.root), expected)
            platform_patches = (mock.patch.object(global_check.platform, "system", return_value="Linux"),
                                mock.patch.object(global_check.platform, "machine", return_value="x86_64"))
            with global_check.selected_contract(fixture.root) as contract, platform_patches[0], platform_patches[1]:
                tokens = ("GITHUB_TOKEN", "GH_TOKEN", "ZIZMOR_GITHUB_TOKEN")
                for case, changes in (("offline", {"ZIZMOR_OFFLINE": "1"}), ("no-online", {"ZIZMOR_NO_ONLINE_AUDITS": "1"}),
                                      ("no-token", None)):
                    with self.subTest(guard=case):
                        installer = mock.Mock()
                        with (mock.patch.object(global_check, "load_module", return_value=installer),
                              mock.patch.object(global_check.subprocess, "run") as zizmor,
                              mock.patch.dict(os.environ, {"GITHUB_TOKEN": "fixture-token", "ZIZMOR_OFFLINE": "",
                                                           "ZIZMOR_NO_ONLINE_AUDITS": ""})):
                            if changes is None:
                                for key in tokens:
                                    os.environ.pop(key, None)
                            else:
                                os.environ.update(changes)
                            with self.assertRaisesRegex(ValueError, "(?i)online"):
                                global_check.lint_workflows(fixture.root, contract)
                        installer.install_tool.assert_not_called()
                        zizmor.assert_not_called()
                for code, output in ((0, b"[]"), (1, b"[]"), (11, b"[]"), (0, b"{}"),
                                     (0, b'[{}]'), (0, b'[{"ident":"rule","desc":"finding","ignored":false}]')):
                    with self.subTest(code=code, output=output):
                        installer = mock.Mock()
                        installer.install_tool.side_effect = lambda name, pin, cache: Path("/verified") / name
                        completed = subprocess.CompletedProcess([], code, stdout=output, stderr=b"")
                        with (mock.patch.object(global_check, "load_module", return_value=installer),
                              mock.patch.object(global_check, "command", return_value=b"") as actionlint,
                              mock.patch.object(global_check.subprocess, "run", return_value=completed) as zizmor,
                              mock.patch.dict(os.environ, {"GITHUB_TOKEN": "fixture-token", "ZIZMOR_OFFLINE": "", "ZIZMOR_NO_ONLINE_AUDITS": ""}),
                              redirect_stderr(io.StringIO())):
                            if code == 0 and output == b"[]":
                                global_check.lint_workflows(fixture.root, contract)
                            else:
                                with self.assertRaises(ValueError):
                                    global_check.lint_workflows(fixture.root, contract)
                        self.assertEqual(list(map(str, actionlint.call_args.args[0]))[-3:], expected)
                        self.assertEqual(zizmor.call_args.args[0][-3:], expected)
                        self.assertNotIn("--offline", zizmor.call_args.args[0])


class BoundaryTests(unittest.TestCase):
    def test_anonymous_clone_scrubs_credentials_config_and_git_context(self):
        inherited = {"GH_TOKEN": "private-fixture", "GITHUB_TOKEN": "private-fixture", "GIT_DIR": "/invalid/git",
                     "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.extraHeader", "GIT_CONFIG_VALUE_0": "private-fixture",
                     "GIT_SSH_COMMAND": "false", "SSH_ASKPASS": "false", "SSH_AUTH_SOCK": "/invalid/socket"}
        with tempfile.TemporaryDirectory(prefix="hexalith-clone-boundary-") as directory:
            destination = Path(directory) / "module"
            with (mock.patch.dict(os.environ, inherited), mock.patch.object(validator.checks, "command", return_value=b"") as command):
                validator.clone_module("Hexalith.Fixture", destination)
            arguments = list(map(str, command.call_args.args[0]))
            environment = command.call_args.kwargs["env"]
            self.assertIn("https://github.com/Hexalith/Hexalith.Fixture.git", arguments)
            for argument in ("--no-checkout", "--depth=1", "--branch=main", "--filter=blob:none", "credential.helper=", "http.extraHeader=", "core.hooksPath=/dev/null", "submodule.recurse=false"):
                self.assertIn(argument, arguments)
            self.assertGreater(command.call_args.kwargs["timeout"], 0)
            for key in inherited:
                self.assertNotIn(key, environment)
            self.assertEqual(environment["GIT_CONFIG_GLOBAL"], os.devnull)
            self.assertEqual(environment["GIT_CONFIG_NOSYSTEM"], "1")
            self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")
            self.assertNotEqual(environment["HOME"], os.environ.get("HOME"))
            self.assertEqual(environment["XDG_CONFIG_HOME"], environment["HOME"])

    def test_http_reader_bounds_get_and_rejects_auth_errors_malformed_and_oversized_json(self):
        for payload in (b"{}", b"[]", b"{malformed", b"x" * (2 * 1024 * 1024 + 1)):
            with self.subTest(size=len(payload), prefix=payload[:10]):
                response = mock.MagicMock()
                response.__enter__.return_value = response
                response.read.return_value = payload
                opener = mock.Mock()
                opener.open.return_value = response
                with (mock.patch.dict(os.environ, {"GITHUB_TOKEN": "fixture-token"}),
                      mock.patch.object(global_check.urllib.request, "build_opener", return_value=opener) as build):
                    if payload == b"{}":
                        self.assertEqual(global_check.github_api("releases/tags/v5.1.0"), {})
                    else:
                        with self.assertRaises(ValueError):
                            global_check.github_api("releases/tags/v5.1.0")
                request = opener.open.call_args.args[0]
                self.assertEqual(request.get_method(), "GET")
                self.assertTrue(request.full_url.startswith("https://api.github.com/repos/Hexalith/Hexalith.Builds/"))
                self.assertGreater(opener.open.call_args.kwargs["timeout"], 0)
                self.assertLessEqual(response.read.call_args.args[0], 2 * 1024 * 1024 + 1)
                self.assertTrue(any(isinstance(handler, global_check.NoRedirect) for handler in build.call_args.args))
        with self.assertRaisesRegex(ValueError, "redirected.*unverified"):
            global_check.NoRedirect().redirect_request(request, None, 302, "Found", {}, "https://example.invalid/")
        for code in (403, 404, 500):
            opener = mock.Mock()
            error = urllib.error.HTTPError("https://api.github.com/", code, "fixture", {}, None)
            opener.open.side_effect = error
            with (self.subTest(code=code), mock.patch.dict(os.environ, {"GITHUB_TOKEN": "fixture-token"}),
                  mock.patch.object(global_check.urllib.request, "build_opener", return_value=opener),
                  self.assertRaisesRegex(ValueError, rf"HTTP {code}.*unverified")):
                global_check.github_api("releases/tags/v5.1.0")
            error.close()

    def test_global_child_logs_stay_off_stdout_and_failure_is_independent(self):
        with (mock.patch.object(validator.checks, "command", return_value=b"tool progress\n") as command,
              redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr):
            self.assertTrue(validator.global_checks(ROOT))
        command.assert_called_once()
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("tool progress", stderr.getvalue())
        with (mock.patch.object(validator.checks, "command", side_effect=ValueError("global child failed")),
              redirect_stderr(io.StringIO())):
            self.assertFalse(validator.global_checks(ROOT))

    def test_global_child_is_locked_shared_entry_point_for_given_project(self):
        with tempfile.TemporaryDirectory(prefix="hexalith-global-project-") as directory:
            project = Path(directory)
            with (mock.patch.object(validator.checks, "command", return_value=b"") as command,
                  redirect_stderr(io.StringIO())):
                self.assertTrue(validator.global_checks(project))
            arguments = list(map(str, command.call_args.args[0]))
            self.assertEqual(arguments[:4], ["uv", "run", "--locked", "--script"])
            self.assertIn(str(ROOT / "tools/check_global.py"), arguments)
            self.assertEqual(arguments[-2:], ["--project-root", str(project)])
            self.assertEqual(command.call_args.kwargs["cwd"], project)

    def test_cli_fallback_and_unwritable_output_fail_closed(self):
        environment = {key: value for key, value in os.environ.items() if key != "GITHUB_OUTPUT"}
        with (mock.patch.object(validator, "validate", side_effect=ValueError("internal failure")),
              mock.patch.object(sys, "argv", ["validate.py"]), mock.patch.dict(os.environ, environment, clear=True),
              redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr):
            self.assertEqual(validator.main(), 1)
        self.assertEqual(stdout.getvalue(), '{"global":false,"modules":[]}\n')
        self.assertIn("internal failure", stderr.getvalue())
        with tempfile.TemporaryDirectory(prefix="hexalith-output-directory-") as directory:
            with (mock.patch.object(validator, "validate", return_value=({"global": True, "modules": []}, 0)),
                  mock.patch.object(sys, "argv", ["validate.py"]), mock.patch.dict(os.environ, {"GITHUB_OUTPUT": directory}),
                  redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr):
                self.assertEqual(validator.main(), 1)
        self.assertEqual(stdout.getvalue(), '{"global":true,"modules":[]}\n')
        self.assertIn("verdict output", stderr.getvalue())

    def test_logs_escape_each_line_separately(self):
        with redirect_stderr(io.StringIO()) as stderr:
            global_check.log("first\nsecond\x1b[31m\r\nthird")
        self.assertEqual(stderr.getvalue(), "first\nsecond\\u001b[31m\nthird\n")


class ReleaseTests(unittest.TestCase):
    def test_published_lightweight_and_annotated_tags_pass(self):
        for annotated in (False, True):
            with self.subTest(annotated=annotated), workspace() as fixture:
                if annotated:
                    revision = git(fixture.builds, "rev-parse", f"{fixture.tag}^{{commit}}").decode().strip()
                    git(fixture.builds, "tag", "--delete", fixture.tag)
                    git(fixture.builds, "tag", "--annotate", fixture.tag, revision, "-m", "Annotated release fixture")
                with global_check.selected_contract(fixture.root) as contract:
                    api = Api(fixture, contract)
                    global_check.check_release(contract, api=api)
                    self.assertTrue(any(path.startswith("compare/") for path in api.calls))
                    if annotated:
                        self.assertTrue(any(path.startswith("git/tags/") for path in api.calls))
                    api = Api(fixture, contract)
                    api.main["object"]["sha"] = contract.revision
                    api.compare.update({"status": "identical", "ahead_by": 0})
                    global_check.check_release(contract, api=api)

    def test_release_metadata_predicates_fail_closed(self):
        cases = ({"draft": True}, {"draft": "false"}, {"immutable": False}, {"immutable": None},
                 {"author": {"login": "maintainer"}}, {"author": None},
                 {"published_at": None}, {"published_at": "not-a-timestamp"}, {"tag_name": "v0.0.0"})
        with workspace() as fixture, global_check.selected_contract(fixture.root) as contract:
            for changes in cases:
                with self.subTest(changes=changes):
                    api = Api(fixture, contract)
                    api.release.update(changes)
                    with self.assertRaises((ValueError, KeyError, TypeError)):
                        global_check.check_release(contract, api=api)

    def test_remote_local_tag_and_ancestry_mismatches_fail(self):
        with workspace() as fixture, global_check.selected_contract(fixture.root) as contract:
            for case in ("remote-commit", "ref-name", "bad-oid", "nonancestor", "merge-base", "main-kind"):
                with self.subTest(case=case):
                    api = Api(fixture, contract)
                    if case == "remote-commit":
                        api.ref["object"]["sha"] = "a" * 40
                    elif case == "ref-name":
                        api.ref["ref"] = "refs/tags/v0.0.0"
                    elif case == "bad-oid":
                        api.ref["object"]["sha"] = "not-a-commit"
                    elif case == "nonancestor":
                        api.compare["status"] = "diverged"
                    elif case == "merge-base":
                        api.compare["merge_base_commit"]["sha"] = "b" * 40
                    else:
                        api.main["object"]["type"] = "tree"
                    with self.assertRaises((ValueError, KeyError, TypeError)):
                        global_check.check_release(contract, api=api)

    def test_annotated_tag_object_mismatch_and_cycle_fail(self):
        with workspace() as fixture:
            revision = git(fixture.builds, "rev-parse", f"{fixture.tag}^{{commit}}").decode().strip()
            git(fixture.builds, "tag", "--delete", fixture.tag)
            git(fixture.builds, "tag", "--annotate", fixture.tag, revision, "-m", "Annotated release fixture")
            with global_check.selected_contract(fixture.root) as contract:
                for case in ("tag-object-oid", "peeled-commit", "cycle"):
                    with self.subTest(case=case):
                        api = Api(fixture, contract)
                        if case == "tag-object-oid":
                            api.tags[api.raw]["sha"] = "a" * 40
                        elif case == "peeled-commit":
                            api.tags[api.raw]["object"]["sha"] = "b" * 40
                        else:
                            api.tags[api.raw]["object"] = {"type": "tag", "sha": api.raw}
                        with self.assertRaises((ValueError, KeyError, TypeError)):
                            global_check.check_release(contract, api=api)

    def test_unavailable_missing_and_malformed_api_never_certify_release(self):
        with workspace() as fixture, global_check.selected_contract(fixture.root) as contract:
            for error in (urllib.error.HTTPError("https://api.github.com/", 403, "Forbidden", {}, None),
                          urllib.error.HTTPError("https://api.github.com/", 404, "Not Found", {}, None),
                          TimeoutError("API timed out"), ValueError("malformed API JSON")):
                with self.subTest(error=type(error).__name__), self.assertRaises((OSError, ValueError)):
                    global_check.check_release(contract, api=mock.Mock(side_effect=error))
                if isinstance(error, urllib.error.HTTPError):
                    error.close()
            for response in (None, [], {}, {"message": "API error"}):
                with self.subTest(response=response), self.assertRaises(ValueError):
                    global_check.check_release(contract, api=lambda path: response)

    def test_malformed_nested_api_objects_fail_as_validation_errors(self):
        with workspace() as fixture, global_check.selected_contract(fixture.root) as contract:
            for case in ("tag-object", "main-object", "compare-base", "compare-merge-base"):
                with self.subTest(case=case):
                    api = Api(fixture, contract)
                    if case == "tag-object":
                        api.ref["object"] = None
                    elif case == "main-object":
                        api.main["object"] = []
                    elif case == "compare-base":
                        api.compare["base_commit"] = None
                    else:
                        api.compare["merge_base_commit"] = []
                    with self.assertRaises(ValueError):
                        global_check.check_release(contract, api=api)


if __name__ == "__main__":
    unittest.main()
