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
from threading import Barrier
import unittest
from unittest import mock
import urllib.error
from delivery_support import bootstrap_source


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures/validate"
sys.dont_write_bytecode = True

# Reuse the renderer's tagged Git workspace, not a second schema or
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
scope_check = load("_validate_change_scope", ROOT / "tools/change_scope.py")
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
          mock.patch.object(module, "check_app_inventory"),
          mock.patch.object(module, "lint_workflows") as lint,
          mock.patch.object(module, "check_bootstrap"),
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

    def responses(self):
        main = self.main.get("object", {}).get("sha") if isinstance(self.main.get("object"), dict) else None
        # Exact endpoints and argument order: a reversed or self-comparison
        # must not silently receive the acceptable compare document.
        responses = {f"releases/tags/{self.tag}": self.release, f"git/ref/tags/{self.tag}": self.ref,
                     "git/ref/heads/main": self.main,
                     f"compare/{self.commit}...{main}?per_page=1&page=2": self.compare}
        responses.update({f"git/tags/{sha}": document for sha, document in self.tags.items()})
        return responses

    def __call__(self, path):
        self.calls.append(path)
        responses = self.responses()
        if path not in responses:
            raise AssertionError(f"Unexpected API read: {path}")
        return copy.deepcopy(responses[path])


class ValidateTests(unittest.TestCase):
    def test_manual_qualification_requires_live_action_and_exact_isolation(self):
        for present in (True, False):
            with self.subTest(present=present), workspace() as fixture:
                fixture.module(actions=("azure",) if present else (),
                               setup={"solution": "Fixture.slnx", "jobs": {"azure": render_tests.MANUAL_JOB}})
                fixture.commit()
                verdict, status, diagnostic = self.verdict(fixture)
                self.assertEqual(0 if present else 1, status)
                if not present:
                    self.assertIn("live main is missing enabled action", diagnostic)
                with renderer.pinned_contract(fixture.root) as contract:
                    global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
                    path = fixture.output(".github/workflows/qualification.yml")
                    accepted = path.read_text()
                    for before, after in (("environment: preserve", "environment: setup"),
                                          ("secrets.AUTHORITY_JSON", "secrets.WRONG_JSON"),
                                          ("github.event_name == 'workflow_dispatch'", "github.event_name != 'workflow_dispatch'")):
                        with self.subTest(corruption=before):
                            path.write_text(accepted.replace(before, after))
                            with self.assertRaises(global_check.CheckError):
                                global_check.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
                    path.write_text(accepted)

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

    def test_enabled_preparation_requires_live_committed_regular_inputs(self):
        inputs = ("tests/e2e/package.json", "tests/e2e/package-lock.json", ".config/dotnet-tools.json")
        for changed in inputs:
            for failure in (None, "missing", "symlink"):
                with self.subTest(changed=changed, failure=failure), workspace() as fixture:
                    remote = fixture.module(setup={"solution": "src/F.slnx"})
                    for name in inputs:
                        target = remote / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text("{}\n")
                    if failure:
                        (remote / changed).unlink()
                        if failure == "symlink":
                            (remote / changed).symlink_to("../../README.md" if changed.startswith("tests/") else "../README.md")
                    git(remote, "add", ".")
                    git(remote, "commit", "--quiet", "-m", "Preparation inputs")
                    fixture.commit()
                    # The active released tag deliberately lacks the additive
                    # fields. Exercise the preparation-input boundary after an
                    # upgraded tagged reader has returned its complete document.
                    config = fixture.json() | {"npmWorkspaces": ["tests/e2e"], "dotnetTools": True}
                    contract = mock.Mock(tag=config["buildsTag"])
                    contract.validate.return_value = config
                    with mock.patch.object(validator, "clone_module", side_effect=fixture.clone):
                        if failure:
                            with self.assertRaises(validator.checks.CheckError) as raised:
                                validator.check_module(fixture.root, "Hexalith.Fixture", contract)
                            self.assertIn(changed, str(raised.exception))
                        else:
                            validator.check_module(fixture.root, "Hexalith.Fixture", contract)

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

    def test_platform_prerequisite_uses_the_same_tagged_schema_and_reader(self):
        with workspace() as fixture:
            with renderer.pinned_contract(ROOT) as contract:
                changes = {path: (contract.root / path).read_bytes() for path in (
                    "schemas/hexalith.ci.v1.json", "Github/lib/ci_config.py")}
            fixture.change_tag(changes)
            declaration = {"id": "sdk-420", "project": "compat/Consumer.csproj", "versions": {"HexalithEventStoreVersion": "4.2.0"}}
            fixture.module(setup={"solution": "Fixture.slnx", "publishedBuilds": "eng/tuple.json", "buildProjects": [declaration]})
            fixture.commit()
            self.assertEqual(self.verdict(fixture)[:2], ({"global": True, "modules": ["Hexalith.Fixture"]}, 0))
            fixture.config(publishedBuilds=None)
            self.assertEqual(self.verdict(fixture, global_ok=False)[:2], ({"global": False, "modules": []}, 1))

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
    def test_bootstrap_digest_failure_fails_actual_global_runner(self):
        with (workspace() as fixture,
              mock.patch.object(global_check, "run_tool_tests"),
              mock.patch.object(global_check, "check_app_inventory"),
              mock.patch.object(global_check, "lint_workflows"),
              mock.patch.object(global_check, "check_release"),
              mock.patch.object(global_check, "github_api", return_value={"encoding": "base64", "content": "dGFtcGVyZWQ="}),
              redirect_stderr(io.StringIO()) as diagnostic):
            fixture.module()
            fixture.commit()
            manifest = fixture.root / "tools/tests/fixtures/delivery-bootstrap.json"
            manifest.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / "tools/tests/fixtures/delivery-bootstrap.json", manifest)
            self.assertFalse(global_check.run(fixture.root))
        self.assertIn("global immutable delivery bootstrap:", diagnostic.getvalue())
        self.assertIn("source digest mismatch", diagnostic.getvalue())

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
                    "module.lint_workflows = module.check_release = module.check_bootstrap = module.check_app_inventory = lambda *arguments: None\n"
                    "def fail_suite(*arguments):\n"
                    "    raise module.CheckError('sentinel suite ran')\n"
                    "module.run_tool_tests = fail_suite\n"
                    "raise SystemExit(module.main())\n")
                for arguments, suites in (([], True), (["--suites", "all"], True), (["--suites", "pin"], True),
                                          (["--scope", "unknown"], True),
                                          (["--scope", "module"], False), (["--scope", "none"], False)):
                    with self.subTest(arguments=arguments):
                        result = run([sys.executable, "-I", harness, "--project-root", fixture.root, *arguments], check=False)
                        self.assertEqual(result.returncode, int(failing or suites))
                        self.assertEqual(result.stdout, b"")
                        self.assertIn(b"global committed render: " + (b"uncommitted" if failing else b"passed"), result.stderr)
                        self.assertEqual(suites, b"sentinel suite ran" in result.stderr)
                        self.assertNotIn(b"Traceback", result.stderr)
                result = run([sys.executable, "-I", harness, "--project-root", fixture.root,
                              "--scope", "none", "--suites", "unknown"], check=False)
                self.assertEqual(2, result.returncode)
                self.assertIn(b"argument --suites: invalid choice", result.stderr)
                self.assertNotIn(b"global committed render", result.stderr)

    def test_unexpected_http_exception_is_collected_and_later_checks_run(self):
        with workspace() as fixture:
            fixture.commit()
            with external_global_checks() as (tests, lint, release), redirect_stderr(io.StringIO()) as diagnostic:
                release.side_effect = http.client.IncompleteRead(b"partial")
                self.assertFalse(global_check.run(fixture.root))
            lint.assert_called_once()
            tests.assert_called_once()
            self.assertIn("global acceptable Builds publication: IncompleteRead", diagnostic.getvalue())

    def test_global_cli_pin_checks_release_and_excludes_independent_failure(self):
        with workspace() as fixture:
            fixture.commit()
            with global_check.selected_contract(fixture.root) as contract:
                api = Api(fixture, contract)
            responses = fixture.root.parent / "release-responses.json"
            responses.write_text(json.dumps(api.responses()))
            tests = fixture.root / "tools/tests"
            tests.mkdir(parents=True)
            for name in global_check.inputs.PIN_SUITES:
                (tests / name).touch()
            (tests / "test_maintenance.py").write_text("raise SystemExit('independent suite failure')\n")
            eventstore = fixture.root / "tools/qualification/pre-adoption/eventstore/test_pre_adoption_verify.py"
            eventstore.parent.mkdir(parents=True)
            eventstore.write_text("print('relocated suite ran')\n")
            harness = fixture.root.parent / "global_cli.py"
            harness.write_text(
                "import importlib.util, json, os, pathlib, sys\n"
                f"spec=importlib.util.spec_from_file_location('global_cli', {str(ROOT / 'tools/check_global.py')!r})\n"
                "gate=importlib.util.module_from_spec(spec); sys.modules[spec.name]=gate; spec.loader.exec_module(gate)\n"
                "gate.lint_workflows = gate.check_bootstrap = gate.check_app_inventory = lambda *arguments: None\n"
                f"responses = json.loads(pathlib.Path({str(responses)!r}).read_text())\n"
                "if os.environ['CICD_TEST_TAG_MISMATCH'] == '1':\n"
                f"    responses[{f'git/ref/tags/{api.tag}'!r}]['object']['sha'] = {'0' * 40!r}\n"
                "gate.github_api = responses.__getitem__\n"
                "raise SystemExit(gate.main())\n")
            cases = (
                (["--suites", "pin"], False, "pin", 0),
                ([], False, "all", 1),
                (["--scope", "unknown", "--suites", "pin"], False, "all", 1),
                (["--suites", "pin"], True, "pin", 1),
            )
            pin_labels = ", ".join(f"tools/tests/{name}" for name in global_check.inputs.PIN_SUITES)
            for arguments, mismatch, selection, status in cases:
                with self.subTest(arguments=arguments, mismatch=mismatch):
                    result = run([sys.executable, "-I", harness, "--project-root", fixture.root, *arguments],
                                 env={"CICD_TEST_TAG_MISMATCH": str(int(mismatch))}, check=False)
                    diagnostic = result.stderr.decode()
                    self.assertEqual(status, result.returncode, diagnostic)
                    if selection == "pin":
                        self.assertIn(f"tool suite selection: pin [{pin_labels}]", diagnostic)
                        self.assertNotIn("test_maintenance.py", diagnostic)
                        self.assertNotIn("relocated suite ran", diagnostic)
                    else:
                        self.assertIn("tool suite selection: all [", diagnostic)
                        self.assertIn("test_maintenance.py: uv exited 1", diagnostic)
                        self.assertIn("independent suite failure", diagnostic)
                        self.assertIn("relocated suite ran", diagnostic)
                    if mismatch:
                        self.assertIn("remote/local tag-object mismatch", diagnostic)
                        self.assertIn("global tool suites: passed", diagnostic)
                    else:
                        self.assertIn("global acceptable Builds publication: passed", diagnostic)

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
            eventstore = fixture.root / "tools/qualification/pre-adoption/eventstore/test_pre_adoption_verify.py"
            eventstore.parent.mkdir(parents=True)
            eventstore.write_text("# relocated fixture suite\n")
            expected = [
                ["uv", "run", "--locked", "--script", "--python", sys.executable, directory / name]
                for name in ("test_render.py", "test_validate.py")
            ] + [[sys.executable, "-B", eventstore]]
            with mock.patch.object(global_check, "command", return_value=b"") as command:
                global_check.run_tool_tests(fixture.root)
            self.assertCountEqual(expected, [call.args[0] for call in command.call_args_list])
            for call in command.call_args_list:
                self.assertEqual(call.kwargs["cwd"], fixture.root)
                self.assertEqual(call.kwargs["timeout"], 600)

    def test_independent_tool_suites_can_run_concurrently(self):
        with workspace() as fixture:
            directory = fixture.root / "tools/tests"
            directory.mkdir(parents=True)
            for name in ("test_render.py", "test_validate.py"):
                (directory / name).touch()
            ready = Barrier(2)

            def run_suite(arguments, **kwargs):
                if arguments[0] == "uv":
                    ready.wait(timeout=10)
                return b""

            with mock.patch.object(global_check, "command", side_effect=run_suite):
                global_check.run_tool_tests(fixture.root)

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
    def test_bootstrap_manifest_is_verified_against_pinned_remote_contents(self):
        import base64
        manifest = json.loads((ROOT / "tools/tests/fixtures/delivery-bootstrap.json").read_bytes())
        calls = []
        def api(path, *, repository):
            calls.append((path, repository))
            source = path.removeprefix("contents/").split("?", 1)[0]
            data = bootstrap_source(manifest["source_sha"], source)
            return {"encoding": "base64", "content": base64.b64encode(data).decode()}
        global_check.check_bootstrap(ROOT, api=api)
        self.assertEqual(calls, [(f"contents/{path}?ref={manifest['source_sha']}", "Hexalith.CiCd")
                                 for path in sorted(manifest["files"])])
        for response, reason in (({"encoding": "base64", "content": "dGFtcGVyZWQ="}, "digest mismatch"),
                                 ({"encoding": "base64", "content": "!"}, "invalid base64"),
                                 ({"encoding": "none"}, "malformed contents")):
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                global_check.check_bootstrap(ROOT, api=lambda *args, **kwargs: response)
        with self.assertRaisesRegex(ValueError, "HTTP 403"):
            global_check.check_bootstrap(ROOT, api=mock.Mock(side_effect=ValueError("HTTP 403")))

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


class ScopeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="hexalith-scope-fixture-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        git(self.root, "init", "--quiet", "--initial-branch=main")
        self.write("README.md")
        self.write("setup/Hexalith.Alpha.yml")
        self.write("rendered/Hexalith.Alpha/file.yml")
        self.write(".gitmodules")
        self.base = self.commit()

    def write(self, path, content="initial\n"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return target

    def commit(self):
        git(self.root, "add", "--all")
        git(self.root, "commit", "--quiet", "--allow-empty", "-m", "Scope fixture")
        return git(self.root, "rev-parse", "HEAD").decode().strip()

    def comparison(self, base=None):
        return scope_check.compare(scope_check.tree(self.root, self.commit()),
                                   scope_check.tree(self.root, base or self.base))

    def external_git(self, baselines, *, discovery=None, failed_fetch=None):
        original = scope_check.git
        self.external_calls = []
        def call(project, *arguments):
            if arguments[0] == "ls-remote":
                self.assertNotEqual(self.root, project)
                self.assertEqual(b"true", git(project, "rev-parse", "--is-bare-repository").strip())
                self.external_calls.append(arguments)
                if isinstance(discovery, Exception):
                    raise discovery
                if discovery is not None:
                    return discovery
                return b"".join(f"{sha}\trefs/heads/delivered/Hexalith.Module{index}\n".encode()
                                for index, sha in enumerate(baselines))
            if arguments[0] == "fetch":
                self.external_calls.append(arguments)
                self.assertEqual(arguments[1:-1], ("--quiet", "--no-tags", "--depth=1", "--filter=blob:none", scope_check.REMOTE))
                if arguments[-1] == failed_fetch:
                    raise OSError("fetch refused")
                # Substitute only GitHub transport; every fetched object and
                # commit/tree read still comes from a real Git repository.
                return git(project, "fetch", "--quiet", "--no-tags", "--depth=1", str(self.root), arguments[-1])
            return original(project, *arguments)
        return mock.patch.object(scope_check, "git", side_effect=call)

    def test_approved_prose_paths_include_additions_deletions_and_unusual_names(self):
        paths = [*scope_check.inputs.PROSE_FILES,
                 *(prefix + "fixture" for prefix in scope_check.inputs.PROSE_DIRECTORIES),
                 scope_check.inputs.EVIDENCE_ROOT + "/receipt.json", "docs/note.md", "docs/tab\tand\nline.md"]
        for path in paths:
            self.write(path, "changed\n")
        self.assertEqual("none", self.comparison())
        self.assertEqual("none", scope_check.compare(scope_check.tree(self.root, self.base),
                                                     scope_check.tree(self.root, self.commit())))

    def test_module_setup_render_execution_and_perimeter_inputs(self):
        for path in ("setup/Hexalith.Alpha.yml", "rendered/Hexalith.Alpha/file.yml",
                     "rendered/Hexalith.Alpha-execution/file.yml", "rendered/Hexalith.Alpha.perimeter.json"):
            with self.subTest(path=path):
                git(self.root, "reset", "--hard", self.base)
                self.write(path, "changed\n")
                self.assertEqual("module", self.comparison())
                self.assertEqual("module", scope_check.compare(scope_check.tree(self.root, self.base),
                                                               scope_check.tree(self.root, self.commit())))

    def test_shared_and_unknown_paths_are_full(self):
        for path in ("builds-version", "templates/shared.j2", "tools/test.py", "docs/proposals/fixture.md",
                     "docs/contracts-prerequisites/input.md", "unknown", "setup/Alpha.yaml",
                     "rendered/Hexalith.Unknown/file", ".gitmodules"):
            with self.subTest(path=path):
                git(self.root, "reset", "--hard", self.base)
                self.write(path, "changed\n")
                self.assertEqual("full", self.comparison())

    def test_renames_consider_both_paths_and_modes_are_not_lost(self):
        self.write("tools/shared.py")
        base = self.commit()
        (self.root / "docs").mkdir()
        git(self.root, "mv", "tools/shared.py", "docs/moved.md")
        self.assertEqual("full", self.comparison(base))
        git(self.root, "reset", "--hard", self.base)
        (self.root / "docs").mkdir(exist_ok=True)
        git(self.root, "mv", "README.md", "docs/renamed.md")
        self.assertEqual("none", self.comparison())
        git(self.root, "reset", "--hard", self.base)
        (self.root / "README.md").chmod(0o755)
        self.assertEqual("full", self.comparison())
        git(self.root, "reset", "--hard", self.base)
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to("setup/Hexalith.Alpha.yml")
        self.assertEqual("full", self.comparison())

    def test_only_existing_direct_gitlink_values_are_prose(self):
        path = "references/Hexalith.Alpha"
        (self.root / path).mkdir(parents=True)
        git(self.root, "update-index", "--add", "--cacheinfo", "160000", self.base, path)
        git(self.root, "commit", "--quiet", "-m", "Existing gitlink")
        base = git(self.root, "rev-parse", "HEAD").decode().strip()
        git(self.root, "update-index", "--cacheinfo", "160000", base, path)
        self.assertEqual("none", self.comparison(base))
        self.write(".gitmodules", "changed\n")
        self.assertEqual("full", self.comparison(base))
        git(self.root, "reset", "--hard", base)
        git(self.root, "update-index", "--force-remove", path)
        self.assertEqual("full", self.comparison(base))
        git(self.root, "reset", "--hard", self.base)
        (self.root / "references/New").mkdir(parents=True)
        git(self.root, "update-index", "--add", "--cacheinfo", "160000", self.base, "references/New")
        self.assertEqual("full", self.comparison())

    def test_committed_inputs_ignore_worktree_and_module_checkouts(self):
        self.write("README.md", "committed\n")
        self.commit()
        self.write("templates/uncommitted.j2")
        self.write("references/Hexalith.Alpha/never-read", "untracked module\n")
        with self.external_git([self.base]):
            self.assertEqual("none", scope_check.classify(self.root, "push"))
        self.assertEqual(["ls-remote", "fetch"], [call[0] for call in self.external_calls])
        self.assertTrue(all(scope_check.REMOTE in call for call in self.external_calls))

    def test_failed_or_cancelled_tools_predecessor_cannot_hide_behind_prose(self):
        for predecessor in ("red", "cancelled"):
            with self.subTest(predecessor=predecessor):
                git(self.root, "reset", "--hard", self.base)
                self.write("tools/changed.py", predecessor)
                self.commit()
                self.write("README.md", "later prose\n")
                self.commit()
                with self.external_git([self.base]):
                    self.assertEqual("full", scope_check.classify(self.root, "push"))

    def test_distinct_accepted_baselines_choose_narrowest_after_all_are_read(self):
        self.write("tools/changed.py")
        accepted = self.commit()
        self.write("README.md", "prose\n")
        self.commit()
        for event in ("push", "schedule"):
            with self.subTest(event=event), self.external_git([self.base, accepted, accepted]):
                self.assertEqual("none", scope_check.classify(self.root, event))
                self.assertEqual(2, sum(call[0] == "fetch" for call in self.external_calls))
        unreadable = "f" * 40
        with self.external_git([accepted, unreadable], failed_fetch=unreadable), redirect_stderr(io.StringIO()):
            self.assertEqual("full", scope_check.classify(self.root, "push"))
        self.assertEqual([accepted, unreadable], [call[-1] for call in self.external_calls if call[0] == "fetch"])

    def test_explicit_empty_tree_is_a_shared_change(self):
        entries = git(self.root, "ls-tree", self.base)
        empty = git(self.root, "mktree", input=b"").strip()
        record = b"040000 tree " + empty + b"\tunknown\n"
        candidate_tree = git(self.root, "mktree", input=entries + record).decode().strip()
        candidate = git(self.root, "commit-tree", candidate_tree, "-p", self.base, "-m", "Empty subtree").decode().strip()
        self.assertEqual("full", scope_check.compare(scope_check.tree(self.root, candidate),
                                                    scope_check.tree(self.root, self.base)))

    def test_pr_uses_exact_base_without_accepted_ref_discovery(self):
        self.write("README.md", "prose\n")
        self.commit()
        with self.external_git([]):
            self.assertEqual("none", scope_check.classify(self.root, "pull_request", self.base))
        self.assertEqual(["fetch"], [call[0] for call in self.external_calls])
        with self.external_git([]), redirect_stderr(io.StringIO()):
            self.assertEqual("full", scope_check.classify(self.root, "pull_request", "main"))
        with mock.patch.object(scope_check, "git") as external:
            self.assertEqual("full", scope_check.classify(self.root, "workflow_dispatch"))
            self.assertEqual("full", scope_check.classify(self.root, ""))
            external.assert_not_called()

    def test_missing_malformed_unreadable_discovery_and_fetch_take_full_path(self):
        def refs(*names):
            return b"".join(f"{self.base}\trefs/heads/delivered/{name}\n".encode() for name in names)

        for discovery in (b"", b"malformed\n", b"bad\trefs/heads/delivered/Alpha\n",
                          refs("Hexalith.Builds"), refs("Hexalith.Alpha", "hexalith.alpha"),
                          (self.base + "\trefs/heads/other/Alpha\n").encode(), OSError("discovery refused")):
            with self.subTest(discovery=discovery), self.external_git([], discovery=discovery), redirect_stderr(io.StringIO()):
                self.assertEqual("full", scope_check.classify(self.root, "push"))
        with self.external_git(["f" * 40], failed_fetch="f" * 40), redirect_stderr(io.StringIO()):
            self.assertEqual("full", scope_check.classify(self.root, "schedule"))

    def test_anonymous_git_removes_credentials_context_and_user_configuration(self):
        with (mock.patch.dict(os.environ, {"GH_TOKEN": "inert", "GITHUB_TOKEN": "inert",
                                          "GIT_DIR": "inert", "SSH_AUTH_SOCK": "inert"}),
              mock.patch.object(scope_check.subprocess, "run", return_value=mock.Mock(stdout=b"")) as process):
            scope_check.git(self.root, "ls-remote", "--refs", scope_check.REMOTE, "refs/heads/delivered/*")
        environment = process.call_args.kwargs["env"]
        self.assertTrue(all(key not in environment for key in ("GH_TOKEN", "GITHUB_TOKEN", "GIT_DIR", "SSH_AUTH_SOCK")))
        self.assertEqual(environment["GIT_CONFIG_GLOBAL"], os.devnull)
        self.assertFalse(Path(environment["HOME"]).exists())
        for option in ("credential.helper=", "http.extraHeader=", "http.followRedirects=false", "submodule.recurse=false"):
            self.assertIn(option, process.call_args.args[0])

    def test_nested_and_nonrepository_candidate_roots_cannot_use_enclosing_git(self):
        nested = self.root / "child"
        nested.mkdir()
        with tempfile.TemporaryDirectory(prefix="hexalith-not-a-repository-") as directory:
            for project in (nested, Path(directory)):
                with self.subTest(project=project), self.external_git([self.base]), redirect_stderr(io.StringIO()) as diagnostic:
                    self.assertEqual("full", scope_check.classify(project, "push"))
                    self.assertEqual([], self.external_calls)
                    self.assertIn("fallback=candidate root unverified", diagnostic.getvalue())

    def test_diagnostics_bind_candidate_baseline_and_class_without_raw_errors(self):
        self.write("README.md", "prose\n")
        candidate = self.commit()
        with self.external_git([self.base]), redirect_stderr(io.StringIO()) as diagnostic:
            self.assertEqual("none", scope_check.classify(self.root, "push"))
        self.assertEqual([f"change scope: candidate={candidate}", f"change scope: baseline={self.base} class=none"],
                         diagnostic.getvalue().splitlines())
        secret = "inert-credential\n::error::" + "x" * 1000
        with self.external_git([], discovery=OSError(secret)), redirect_stderr(io.StringIO()) as diagnostic:
            self.assertEqual("full", scope_check.classify(self.root, "push"))
        self.assertNotIn(secret, diagnostic.getvalue())
        self.assertIn("fallback=accepted refs unreadable", diagnostic.getvalue())
        self.assertLess(len(diagnostic.getvalue()), 200)
        with self.external_git([self.base], failed_fetch=self.base), redirect_stderr(io.StringIO()) as diagnostic:
            self.assertEqual("full", scope_check.classify(self.root, "push"))
        self.assertIn(f"baseline={self.base} class=full fallback=baseline fetch failed", diagnostic.getvalue())

    def test_cli_emits_separate_scope_output(self):
        output = self.root / "github-output"
        with (mock.patch.object(scope_check, "classify", return_value="none") as classify,
              mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(output), "CHANGE_SCOPE_EVENT": "pull_request",
                                           "CHANGE_SCOPE_PR_BASE": self.base}), redirect_stdout(io.StringIO())):
            self.assertEqual(0, scope_check.main(["--project-root", str(self.root)]))
        classify.assert_called_once_with(self.root, "pull_request", self.base)
        self.assertEqual("scope=none\nskip_checks=1\n", output.read_text())

    def test_internal_skip_decision_requires_exact_scope_and_pr_or_push(self):
        for scope in ("none", "NONE", "None", "", None, "unknown", "module", "full"):
            for event in ("pull_request", "push", "schedule", "workflow_dispatch", ""):
                with self.subTest(scope=scope, event=event):
                    self.assertEqual(int(scope == "none" and event in ("pull_request", "push")),
                                     scope_check.skip_checks(scope, event))


class ScopeSelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="hexalith-scope-selection-")
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)

    def test_prose_pr_and_push_have_no_builds_module_or_suite_reads(self):
        for event in ("pull_request", "push"):
            with (self.subTest(event=event), mock.patch.object(validator, "global_checks") as checks,
                  mock.patch.object(validator.renderer, "registry") as registry,
                  mock.patch.object(validator.checks, "selected_contract") as builds):
                self.assertEqual(({"global": True, "modules": []}, 0), validator.validate(self.project, "none", event))
                checks.assert_not_called()
                registry.assert_not_called()
                builds.assert_not_called()

    def test_module_and_schedule_keep_every_module_and_independent_verdict(self):
        with workspace() as fixture:
            fixture.module("Hexalith.Alpha")
            fixture.module("Hexalith.Beta")
            fixture.commit()
            for scope, event in (("module", "push"), ("none", "schedule")):
                with (self.subTest(scope=scope), mock.patch.object(validator, "global_checks", return_value=False) as checks,
                      mock.patch.object(validator, "clone_module", side_effect=fixture.clone), redirect_stderr(io.StringIO())):
                    self.assertEqual(({"global": False, "modules": ["Hexalith.Alpha", "Hexalith.Beta"]}, 1),
                                     validator.validate(fixture.root, scope, event))
                    checks.assert_called_once_with(fixture.root, scope)
            self.assertEqual(["Hexalith.Alpha", "Hexalith.Beta"] * 2, fixture.cloned)

    def test_missing_unknown_malformed_or_manual_scope_uses_full_global_child(self):
        for scope, event in ((None, "push"), ("", "push"), ("unknown", "push"), ({}, "push"),
                             ("none", "workflow_dispatch"), ("module", "workflow_dispatch")):
            with (self.subTest(scope=scope, event=event), mock.patch.object(validator, "global_checks", return_value=True) as checks,
                  mock.patch.object(validator.renderer, "registry", return_value=[]),
                  mock.patch.object(validator.checks, "selected_contract")):
                self.assertEqual(0, validator.validate(self.project, scope, event)[1])
                checks.assert_called_once_with(self.project)

    def test_validator_can_fall_back_when_classifier_cannot_be_loaded(self):
        locate = importlib.util.spec_from_file_location

        def without_classifier(name, path):
            if Path(path).name == "change_scope.py":
                raise FileNotFoundError(path)
            return locate(name, path)

        with mock.patch.object(importlib.util, "spec_from_file_location", side_effect=without_classifier):
            isolated = load("_validate_without_classifier", ROOT / "tools/validate.py")
        with (mock.patch.object(isolated, "global_checks", return_value=True) as checks,
              mock.patch.object(isolated.renderer, "registry", return_value=[]),
              mock.patch.object(isolated.checks, "selected_contract")):
            self.assertEqual(({"global": True, "modules": []}, 0), isolated.validate(self.project, "", "push"))
        checks.assert_called_once_with(self.project)

    def test_only_suites_depend_on_scope_and_online_proofs_remain(self):
        callbacks = ("check_app_inventory", "check_committed_inputs", "check_committed_render", "check_bootstrap",
                     "check_render", "check_documents", "check_release", "lint_workflows", "run_tool_tests")
        from contextlib import ExitStack
        for scope in ("none", "module", "full", None, "", "bad", {}):
            with self.subTest(scope=scope), ExitStack() as stack:
                calls = {name: stack.enter_context(mock.patch.object(global_check, name)) for name in callbacks}
                stack.enter_context(mock.patch.object(global_check, "selected_contract"))
                stack.enter_context(mock.patch.object(global_check.renderer, "registry", return_value=[]))
                stack.enter_context(redirect_stderr(io.StringIO()))
                self.assertTrue(global_check.run(self.project, scope))
                for name, callback in calls.items():
                    self.assertEqual(0 if name == "run_tool_tests" and scope in ("none", "module") else 1,
                                     callback.call_count, name)

    def test_global_suite_selection_uses_locked_commands_and_reports_independent_failure(self):
        names = ("test_conversations_qualification.py", "test_delivery_workflow.py", "test_render.py",
                 "test_render_legacy.py", "test_validate.py")
        tests = self.project / "tools/tests"
        tests.mkdir(parents=True)
        independent = tests / "test_maintenance.py"
        for path in [*(tests / name for name in names), independent]:
            path.touch()
        eventstore = self.project / "tools/qualification/pre-adoption/eventstore/test_pre_adoption_verify.py"
        visited = []

        def suite(arguments, *, cwd, timeout):
            path = arguments[-1]
            visited.append(path)
            self.assertEqual(self.project, cwd)
            self.assertEqual(600, timeout)
            if path == eventstore:
                self.assertEqual([sys.executable, "-B", path], arguments)
            else:
                self.assertEqual(["uv", "run", "--locked", "--script", "--python", sys.executable, path], arguments)
            if path == independent:
                raise global_check.CheckError("injected independent failure")
            return b""

        with (mock.patch.object(global_check, "command", side_effect=suite),
              redirect_stderr(io.StringIO()) as diagnostic):
            global_check.run_tool_tests(self.project, "pin")
            self.assertCountEqual([tests / name for name in names], visited)
            self.assertIn("tool suite selection: pin", diagnostic.getvalue())
            self.assertNotIn(independent.name, diagnostic.getvalue())
            visited.clear()
            for arguments in ((), ("all",)):
                with self.subTest(arguments=arguments):
                    with self.assertRaisesRegex(global_check.CheckError,
                                                "tools/tests/test_maintenance.py: injected independent failure"):
                        global_check.run_tool_tests(self.project, *arguments)
                    self.assertCountEqual([*(tests / name for name in names), independent, eventstore], visited)
                    visited.clear()
            (tests / names[0]).unlink()
            with self.assertRaisesRegex(global_check.CheckError, f"missing pin suites: {names[0]}"):
                global_check.run_tool_tests(self.project, "pin")
            self.assertEqual([], visited)

    def test_scope_reaches_locked_child_and_default_remains_full(self):
        for scope in ("none", "module", "bad", None):
            with mock.patch.object(validator.checks, "command", return_value=b"") as command:
                self.assertTrue(validator.global_checks(self.project, scope))
            arguments = command.call_args.args[0]
            if scope in ("none", "module"):
                self.assertEqual(["--scope", scope], arguments[-2:])
            else:
                self.assertNotIn("--scope", arguments)


if __name__ == "__main__":
    unittest.main()
