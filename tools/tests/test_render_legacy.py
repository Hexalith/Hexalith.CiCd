#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Historical renderer contract variants; shared cases run in test_render.py."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures/render"
LEGACY_RELEASE = json.loads((FIXTURES.parent / "builds-releases.json").read_bytes())["renderer"]
MANUAL_JOB = {
    "trigger": "manual", "runner": {"group": "private-ephemeral", "labels": ["self-hosted", "linux", "x64"]},
    "environment": "owner-approval", "secrets": ["AUTHORITY_JSON", "CUSTODY_JSON"],
    "preparation": "build-only", "timeoutMinutes": 45,
}
sys.dont_write_bytecode = True


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


renderer = load_module("_cicd_renderer", ROOT / "tools/render.py")
# Rendering and global qualification share the effective permission-union rule.
global_checks = load_module("_cicd_render_global_checks", ROOT / "tools/check_global.py")


def run(arguments, *, cwd=None, input=None, env=None, check=True):
    environment = os.environ.copy()
    environment.update({
        "GIT_AUTHOR_NAME": "Renderer fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "Renderer fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_CONFIG_NOSYSTEM": "1", "PYTHONDONTWRITEBYTECODE": "1",
    })
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_PREFIX"):
        environment.pop(key, None)
    if env:
        environment.update(env)
    result = subprocess.run(list(map(str, arguments)), cwd=cwd, input=input,
                            capture_output=True, env=environment, check=False)
    if check and result.returncode:
        raise AssertionError(f"{arguments[0]} failed ({result.returncode}):\n"
                             f"{result.stdout.decode(errors='replace')}\n{result.stderr.decode(errors='replace')}")
    return result


def git(root, *arguments, **kwargs):
    return run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                "-C", root, *arguments], **kwargs).stdout


def file_bytes(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file() and ".git" not in path.relative_to(root).parts}


class Workspace:
    def __init__(self, root: Path, *, tag=None):
        self.root = root
        self.builds = root / "references/Hexalith.Builds"
        # Legacy refusals/defaults belong to this authentic released contract,
        # independently of the production pin. Selected-release coverage below
        # exercises the actual pin without rewriting historical expectations.
        self.tag = tag or LEGACY_RELEASE["tag"]
        self.builds.parent.mkdir(parents=True)
        run(["git", "clone", "--quiet", "--shared", "--no-checkout",
             ROOT / "references/Hexalith.Builds", self.builds])
        if self.tag == LEGACY_RELEASE["tag"]:
            revision = git(self.builds, "rev-parse", f"refs/tags/{self.tag}^{{commit}}").decode().strip()
            if revision != LEGACY_RELEASE["commit"]:
                raise AssertionError("Legacy renderer fixture must use the authentic released commit")
        shutil.copytree(ROOT / "templates", root / "templates")
        (root / "setup").mkdir()
        (root / "setup/README.md").write_text("Fixture registry only.\n")
        (root / "builds-version").write_text(self.tag + "\n")
        (root / "rendered").mkdir()
        (root / "rendered/.gitkeep").write_bytes(b"")

    def setup(self, fixture="minimal", name="Hexalith.Fixture"):
        path = self.root / f"setup/{name}.yml"
        shutil.copyfile(FIXTURES / f"{fixture}.yml", path)
        return path

    def document(self, document, name="Hexalith.Fixture"):
        path = self.root / f"setup/{name}.yml"
        path.write_text(json.dumps(document, ensure_ascii=True) + "\n", encoding="utf-8")
        return path

    def cli(self, *arguments, check=True, cwd=None, env=None, script=None):
        return run([sys.executable, "-I", script or ROOT / "tools/render.py",
                    "--project-root", self.root, *arguments], cwd=cwd, env=env, check=check)

    def output(self, relative, name="Hexalith.Fixture"):
        return self.root / "rendered" / name / relative

    def json(self, relative=".github/hexalith-ci.json", name="Hexalith.Fixture"):
        return json.loads(self.output(relative, name).read_bytes())

    def yaml(self, relative, name="Hexalith.Fixture"):
        return renderer.yaml_document(self.output(relative, name).read_bytes(), relative)

    def change_tag(self, changes: dict[str, bytes | None], *, move_tag=True):
        """Create local Git-object fixtures without reading or changing a checkout."""
        with tempfile.TemporaryDirectory(prefix="render-index-") as directory:
            index = Path(directory) / "index"
            environment = {"GIT_INDEX_FILE": str(index)}
            git(self.builds, "read-tree", self.tag, env=environment)
            for path, data in changes.items():
                if data is None:
                    git(self.builds, "update-index", "--force-remove", "--", path, env=environment)
                else:
                    oid = git(self.builds, "hash-object", "-w", "--stdin", input=data).decode().strip()
                    git(self.builds, "update-index", "--add", "--cacheinfo", "100644", oid, path, env=environment)
            tree = git(self.builds, "write-tree", env=environment).decode().strip()
            commit = git(self.builds, "commit-tree", tree, "-p", self.tag,
                         input=b"Synthetic contract fixture\n").decode().strip()
            git(self.builds, "update-ref", "refs/heads/fixture", commit)
            git(self.builds, "symbolic-ref", "HEAD", "refs/heads/fixture")
            if move_tag:
                git(self.builds, "update-ref", f"refs/tags/{self.tag}", commit)
            return commit

    def qualification_contract(self):
        """Synthetic tagged candidate: production's release selector stays untouched."""
        paths = ("schemas/hexalith.ci.v1.json", "Github/lib/ci_config.py", ".github/workflows/ci.yml",
                 "Github/prepare/action.yml")
        with renderer.pinned_contract(ROOT) as contract:
            changes = {path: (contract.root / path).read_bytes() for path in paths}
        self.change_tag(changes)


@contextmanager
def workspace(*, tag=None):
    with tempfile.TemporaryDirectory(prefix="hexalith-render-fixture-") as directory:
        yield Workspace(Path(directory), tag=tag)


class RenderTests(unittest.TestCase):
    def selected_workspace(self):
        return workspace(tag=(ROOT / "builds-version").read_text().strip())

    def test_selected_release_complete_defaults_and_numeric_timeout_interface(self):
        with self.selected_workspace() as fixture:
            self.assertEqual(git(ROOT / "references/Hexalith.Builds", "rev-parse", f"refs/tags/{fixture.tag}^{{commit}}").decode().strip(),
                             git(fixture.builds, "rev-parse", f"refs/tags/{fixture.tag}^{{commit}}").decode().strip())
            fixture.setup()
            fixture.cli()
            self.assertEqual(fixture.json(), {
                "schema": "hexalith.ci.v1", "buildsTag": fixture.tag, "solution": "none",
                "dapr": False, "browsers": False, "registry": False, "codeql": [],
                "tests": {"integration": [], "exclude": {}, "failSkips": False, "minimumExpectedTests": {}},
                "hooks": [], "jobs": {}, "submodules": [], "buildProjects": [], "publishedBuilds": None,
                "ciTimeoutMinutes": 30, "npmWorkspaces": [], "dotnetTools": False,
                "moduleManifest": None, "windowsCheckout": None, "docs": "warn",
            })
            self.assertEqual({"job-timeout-minutes": 30},
                             fixture.yaml(".github/workflows/ci.yml")["jobs"]["ci"]["with"])
            with renderer.pinned_contract(fixture.root) as contract:
                global_checks.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
            for invalid in (0, 361, True, "30", None):
                with self.subTest(invalid=invalid):
                    fixture.document({"ciTimeoutMinutes": invalid})
                    self.assert_failure_unchanged(fixture, contains="ciTimeoutMinutes")

    def test_selected_release_preserves_explicit_values_and_additive_windows_interface(self):
        with self.selected_workspace() as fixture:
            setup = fixture.setup("full")
            fixture.cli()
            supplied = renderer.yaml_document(setup.read_bytes(), str(setup))
            self.assertEqual(fixture.json(), {
                "schema": "hexalith.ci.v1", "buildsTag": fixture.tag, **supplied,
                "tests": {**supplied["tests"], "failSkips": False, "minimumExpectedTests": {}},
                "buildProjects": [], "publishedBuilds": None, "ciTimeoutMinutes": 30, "docs": "warn",
                "npmWorkspaces": [], "dotnetTools": False, "moduleManifest": None, "windowsCheckout": None,
            })
            names = ("solution", "submodules", "global-json", "module-manifest", "windows-checkout", "source-revision", "module-authority")
            windows = fixture.yaml(".github/workflows/ci.yml")["jobs"]["windows-windows-tests"]
            self.assertEqual({name: "${{ needs.ci.outputs." + name + " }}" for name in names}, windows["steps"][0]["with"])
            with renderer.pinned_contract(fixture.root) as contract:
                global_checks.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
            fixture.document({"solution": "Fixture.slnx", "tests": {"failSkips": True,
                "minimumExpectedTests": {"test/Fixture.csproj": 7}}, "ciTimeoutMinutes": 120})
            fixture.cli()
            self.assertEqual({"integration": [], "exclude": {}, "failSkips": True,
                              "minimumExpectedTests": {"test/Fixture.csproj": 7}}, fixture.json()["tests"])
            self.assertEqual({"job-timeout-minutes": 120},
                             fixture.yaml(".github/workflows/ci.yml")["jobs"]["ci"]["with"])
            for invalid in ({"failSkips": "true"}, {"minimumExpectedTests": {"test/Fixture.csproj": 0}}):
                fixture.document({"solution": "Fixture.slnx", "tests": invalid})
                self.assert_failure_unchanged(fixture)

    def test_selected_release_accepts_manual_runner_and_preserves_private_source_binding(self):
        with self.selected_workspace() as fixture:
            fixture.document({"solution": "Fixture.slnx", "jobs": {"azure": MANUAL_JOB}})
            fixture.cli()
            self.assertEqual(MANUAL_JOB, fixture.json()["jobs"]["azure"])
            qualification = fixture.yaml(".github/workflows/qualification.yml")
            job = qualification["jobs"]["custom-azure"]
            self.assertEqual(MANUAL_JOB["runner"], job["runs-on"])
            self.assertEqual("owner-approval", job["environment"])
            self.assertEqual(45, job["timeout-minutes"])
            self.assertNotIn("env", job)
            self.assertNotIn("secrets", job)
            with renderer.pinned_contract(fixture.root) as contract:
                global_checks.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
            fixture.cli("--check")

    def execution_config(self, jobs):
        return {"jobs": jobs, "buildsTag": "v9.8.7", "solution": "Fixture.slnx", "registry": False,
                "submodules": [], "tests": {}}

    def test_tagged_platform_prerequisite_schema_reader_and_defaults_round_trip(self):
        with workspace() as fixture:
            with renderer.pinned_contract(ROOT) as contract:
                changes = {path: (contract.root / path).read_bytes() for path in (
                    "schemas/hexalith.ci.v1.json", "Github/lib/ci_config.py")}
            fixture.change_tag(changes)
            fixture.document({"solution": "Fixture.slnx"})
            fixture.cli()
            self.assertIsNone(fixture.json()["publishedBuilds"])
            self.assertEqual([], fixture.json()["buildProjects"])
            declaration = {"id": "sdk-420", "project": "compat/Consumer.csproj",
                "versions": {"HexalithEventStoreVersion": "4.2.0"}}
            fixture.document({"solution": "Fixture.slnx", "publishedBuilds": "eng/tuple.json", "buildProjects": [declaration]})
            fixture.cli()
            self.assertEqual([declaration], fixture.json()["buildProjects"])
            self.assertEqual("eng/tuple.json", fixture.json()["publishedBuilds"])
            before = fixture.output(".github/hexalith-ci.json").read_bytes()
            fixture.document({"solution": "Fixture.slnx", "publishedBuilds": "eng/tuple.json", "buildProjects": [
                dict(declaration, versions={"NuGetAudit": "false"})]})
            self.assertNotEqual(0, fixture.cli(check=False).returncode)
            self.assertEqual(before, fixture.output(".github/hexalith-ci.json").read_bytes())







    def test_manual_qualification_preserves_secrets_runner_and_green_source(self):
        with workspace() as fixture:
            fixture.qualification_contract()
            fixture.document({"solution": "Fixture.slnx", "additionalSdkVersion": "11.0.100", "ciTimeoutMinutes": 180,
                              "jobs": {"azure": MANUAL_JOB,
                                       "windows-tests": {"runner": "windows-latest"}}})
            fixture.cli()
            ci = fixture.yaml(".github/workflows/ci.yml")
            workflow = fixture.yaml(".github/workflows/qualification.yml")
            expected_arguments = {"additional-sdk-version": "11.0.100", "job-timeout-minutes": 180}
            self.assertEqual(expected_arguments, ci["jobs"]["ci"]["with"])
            self.assertIsNone(ci["on"]["workflow_dispatch"])
            self.assertNotIn("custom-azure", ci["jobs"])
            dispatch = workflow["on"]["workflow_dispatch"]["inputs"]
            self.assertEqual(["nightly", "azure"], dispatch["job"]["options"])
            self.assertEqual("nightly", dispatch["job"]["default"])
            self.assertEqual("", dispatch["authority-sha256"]["default"])
            green = workflow["jobs"]["qualification-ci"]
            self.assertEqual(expected_arguments, green["with"])
            job = workflow["jobs"]["custom-azure"]
            self.assertEqual(["qualification-ci"], job["needs"])
            self.assertIn("github.ref == 'refs/heads/main'", job["if"])
            self.assertIn("needs.qualification-ci.result == 'success'", job["if"])
            self.assertIn("github.event_name == 'workflow_dispatch'", job["if"])
            self.assertIn("contains(fromJSON(", job["if"])
            self.assertIn('"azure"', job["if"])
            self.assertIn("inputs.job", job["if"])
            self.assertEqual(MANUAL_JOB["runner"], job["runs-on"])
            self.assertEqual("owner-approval", job["environment"])
            self.assertEqual("preserve", job["steps"][0]["with"]["environment"])
            self.assertEqual("${{ inputs.authority-sha256 }}", job["steps"][0]["with"]["authority-sha256"])
            self.assertEqual("${{ needs.qualification-ci.outputs.source-sha }}", job["steps"][0]["with"]["source-sha"])
            environment = job["steps"][1]["env"]
            for name in MANUAL_JOB["secrets"]:
                self.assertEqual("${{ secrets." + name + " }}", environment[name])
            self.assertEqual("${{ inputs.authority-sha256 }}", environment["HEXALITH_AUTHORITY_SHA256"])
            self.assertEqual("${{ needs.qualification-ci.outputs.source-sha }}", environment["HEXALITH_SOURCE_SHA"])
            self.assertNotIn("with", job["steps"][1])
            self.assertNotIn("env", job)
            self.assertNotIn("env", job["steps"][0])
            for caller in (ci["jobs"]["ci"], green):
                self.assertEqual({"registry-pull-username", "registry-pull-password"}, set(caller["secrets"]))
            with renderer.pinned_contract(fixture.root) as contract:
                global_checks.check_interfaces(fixture.root, "Hexalith.Fixture", contract)
            fixture.cli("--check")

    def test_old_release_rejects_manual_shape_without_replacing_accepted_render(self):
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            fixture.document({"solution": "Fixture.slnx", "jobs": {"azure": MANUAL_JOB}})
            self.assert_failure_unchanged(fixture)

    def assert_arguments_supplied(self, supplied, declarations):
        self.assertLessEqual(set(supplied), set(declarations))
        required = {name for name, options in declarations.items() if options.get("required") is True}
        missing = required - set(supplied)
        self.assertFalse(missing, f"missing required arguments: {', '.join(sorted(missing))}")

    def assert_failure_unchanged(self, fixture, *arguments, contains=None):
        before = file_bytes(fixture.root / "rendered")
        result = fixture.cli(*arguments, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(file_bytes(fixture.root / "rendered"), before)
        if contains:
            self.assertIn(contains, result.stderr.decode())
        self.assertNotIn("Traceback", result.stderr.decode())
        return result


    def test_minimal_complete_defaults_and_exact_output_tree(self):
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            self.assertEqual(fixture.json(), {
                "schema": "hexalith.ci.v1", "buildsTag": fixture.tag, "solution": "none",
                "dapr": False, "browsers": False, "registry": False, "codeql": [],
                "tests": {"integration": [], "exclude": {}}, "hooks": [], "jobs": {}, "submodules": [],
            })
            expected = {f"Hexalith.Fixture/{path}" for path in renderer.TEMPLATES}
            expected |= {".gitkeep", "Hexalith.Fixture.perimeter.json"}
            self.assertEqual(set(file_bytes(fixture.root / "rendered")), expected)
            fixture.cli("--check")
            for name, data in file_bytes(fixture.root / "rendered").items():
                if name == ".gitkeep":
                    continue
                self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
                self.assertNotIn(b"\r", data)
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))

    def test_nested_defaults_and_explicit_values_survive(self):
        with workspace() as fixture:
            fixture.setup("partial")
            fixture.cli()
            document = fixture.json()
            self.assertEqual(document["codeql"], ["csharp"])
            self.assertEqual(document["tests"], {
                "integration": ["test/Fixture.IntegrationTests.csproj"], "exclude": {},
            })
            fixture.document({"solution": "Fixture.slnx", "tests": {"exclude": {}},
                              "dapr": False, "registry": False, "codeql": [], "hooks": [], "jobs": {},
                              "submodules": []})
            fixture.cli()
            self.assertEqual(fixture.json()["tests"], {"integration": [], "exclude": {}})
            self.assertEqual(fixture.json()["codeql"], [])
            self.assertFalse(fixture.json()["dapr"])

    def timeout_contract(self, fixture):
        """Model the additive, complete contract at a future selected release."""
        schema_path, loader_path = "schemas/hexalith.ci.v1.json", "Github/lib/ci_config.py"
        schema = json.loads(git(fixture.builds, "show", f"{fixture.tag}:{schema_path}"))
        schema["required"].append("ciTimeoutMinutes")
        schema["properties"]["ciTimeoutMinutes"] = {
            "type": "integer", "minimum": 1, "maximum": 360, "default": 30,
        }
        schema["properties"]["job-timeout-minutes"] = {
            "type": "integer", "minimum": 1, "maximum": 360,
        }
        loader = git(fixture.builds, "show", f"{fixture.tag}:{loader_path}").decode()
        original = '"tests", "hooks", "jobs", "submodules"))'
        self.assertIn(original, loader)
        loader = loader.replace(original, '"tests", "hooks", "jobs", "submodules", "ciTimeoutMinutes"))')
        loader = loader.replace('frozenset(("buildsTag",))', 'frozenset(("buildsTag", "job-timeout-minutes"))')
        loader = loader.replace("    return document\n", """    if type(document["ciTimeoutMinutes"]) is not int or not 1 <= document["ciTimeoutMinutes"] <= 360:
        fail("$/ciTimeoutMinutes", "expected an integer from 1 to 360")
    return document
""", 1)
        fixture.change_tag({schema_path: json.dumps(schema).encode(), loader_path: loader.encode()})

    def test_timeout_materializes_and_forwards_only_from_the_selected_complete_contract(self):
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            self.assertNotIn("ciTimeoutMinutes", fixture.json())
            self.assertNotIn("with", fixture.yaml(".github/workflows/ci.yml")["jobs"]["ci"])
            fixture.document({"ciTimeoutMinutes": 120})
            self.assert_failure_unchanged(fixture, contains="ciTimeoutMinutes")
            self.timeout_contract(fixture)
            fixture.document({})
            fixture.cli()
            self.assertEqual(30, fixture.json()["ciTimeoutMinutes"])
            self.assertEqual({"job-timeout-minutes": 30},
                             fixture.yaml(".github/workflows/ci.yml")["jobs"]["ci"]["with"])
            for allowance in (1, 120, 360):
                fixture.document({"ciTimeoutMinutes": allowance})
                fixture.cli()
                self.assertEqual(allowance, fixture.json()["ciTimeoutMinutes"])
                self.assertEqual({"job-timeout-minutes": allowance},
                                 fixture.yaml(".github/workflows/ci.yml")["jobs"]["ci"]["with"])
                fixture.cli("--check")
            for invalid in (0, -1, 361, True, "60", 30.5, None):
                with self.subTest(invalid=invalid):
                    fixture.document({"ciTimeoutMinutes": invalid})
                    self.assert_failure_unchanged(fixture, contains="ciTimeoutMinutes")

    def test_timeout_requires_the_pinned_numeric_workflow_input(self):
        with workspace() as fixture:
            fixture.setup()
            self.timeout_contract(fixture)
            workflow_path = ".github/workflows/ci.yml"
            workflow = git(fixture.builds, "show", f"{fixture.tag}:{workflow_path}")
            declaration = renderer.yaml_document(workflow, workflow_path)
            declaration["on"]["workflow_call"]["inputs"]["job-timeout-minutes"]["type"] = "string"
            fixture.change_tag({workflow_path: json.dumps(declaration).encode()})
            self.assert_failure_unchanged(fixture, contains="numeric job-timeout-minutes input")

    def test_explicit_native_timeout_override_keeps_precedence(self):
        with workspace() as fixture:
            fixture.setup()
            self.timeout_contract(fixture)
            fixture.document({"ciTimeoutMinutes": 120, "job-timeout-minutes": 90})
            fixture.cli()
            self.assertEqual(120, fixture.json()["ciTimeoutMinutes"])
            self.assertEqual(90, fixture.yaml(".github/workflows/ci.yml")["jobs"]["ci"]["with"]["job-timeout-minutes"])
            for invalid in (0, 361, True, "90"):
                with self.subTest(invalid=invalid):
                    fixture.document({"job-timeout-minutes": invalid})
                    self.assert_failure_unchanged(fixture, contains="job-timeout-minutes")

    def test_valid_quotes_spaces_unicode_are_data(self):
        with workspace() as fixture:
            setup = fixture.setup("quoted")
            expected = renderer.yaml_document(setup.read_bytes(), str(setup))
            fixture.cli()
            for field in ("solution", "submodules", "codeql", "hooks", "tests"):
                self.assertEqual(fixture.json()[field], expected[field])
            workflow = fixture.yaml(".github/workflows/ci.yml")
            self.assertEqual(set(workflow["jobs"]), {"ci"})
            self.assertNotIn(expected["solution"], fixture.output(".github/workflows/ci.yml").read_text())

    def test_invalid_setup_matrix_does_not_mutate_output(self):
        documents = [
            ("root-null", None), ("root-array", []), ("root-string", "no"),
            ("schema", {"schema": "hexalith.ci.v1"}), ("buildsTag", {"buildsTag": "v5.1.0"}),
            ("unknown", {"unknown": True}), ("dapr-type", {"dapr": "false"}),
            ("none-dapr", {"dapr": True}), ("none-browsers", {"browsers": True}),
            ("none-hooks", {"hooks": ["nightly"]}),
            ("none-tests", {"tests": {"integration": ["test/A.csproj"]}}),
            ("none-jobs", {"jobs": {"windows": {"runner": "windows-latest"}}}),
            ("solution-extension", {"solution": "Fixture.sln"}),
            ("reserved-job", {"solution": "Fixture.slnx", "jobs": {"ci": {"runner": "windows-latest"}}}),
            ("reserved-hook-job", {"solution": "Fixture.slnx", "jobs": {"nightly": {"runner": "windows-latest"}}}),
            ("unsafe-job", {"solution": "Fixture.slnx", "jobs": {"x\njob": {"runner": "windows-latest"}}}),
            ("runner", {"solution": "Fixture.slnx", "jobs": {"windows": {"runner": "ubuntu-latest"}}}),
            ("runner-missing", {"solution": "Fixture.slnx", "jobs": {"windows": {}}}),
            ("job-extra", {"solution": "Fixture.slnx", "jobs": {"windows": {"runner": "windows-latest", "steps": []}}}),
            ("target", {"solution": "Fixture.slnx", "tests": {"exclude": {"test/A.csproj": "missing"}}}),
            ("language", {"codeql": ["actions"]}), ("duplicate", {"submodules": ["a", "a"]}),
            ("test-unknown", {"tests": {"unknown": []}}),
        ]
        documents += [(f"null-{key}", {key: None}) for key in
                      ("solution", "dapr", "browsers", "registry", "codeql", "tests", "hooks", "jobs", "submodules")]
        documents += [(f"null-tests-{key}", {"tests": {key: None}}) for key in ("integration", "exclude")]
        documents += [(f"unsafe-path-{index}", {"solution": value}) for index, value in enumerate([
            "/Fixture.slnx", "../Fixture.slnx", "a/../Fixture.slnx", "C:Fixture.slnx", "a\\Fixture.slnx",
            "a//Fixture.slnx", "a/./Fixture.slnx", "Fixture.slnx/", "a\nFixture.slnx", "a\x7fFixture.slnx",
            "${{ secrets.TOKEN }}.slnx",
        ])]
        with workspace() as fixture:
            fixture.setup(name="Hexalith.Valid")
            fixture.cli()
            for label, document in documents:
                with self.subTest(label=label):
                    fixture.document(document, "Hexalith.Invalid")
                    self.assert_failure_unchanged(fixture, contains="Hexalith.Invalid.yml")






















    def test_dependabot_exact_solution_policy(self):
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            self.assertEqual(fixture.yaml(".github/dependabot.yml"), {"version": 2, "updates": []})
            setup = fixture.setup("full")
            fixture.cli()
            # The full fixture supplies every knob: nothing is dropped, coerced or added.
            self.assertEqual(fixture.json(), {
                "schema": "hexalith.ci.v1", "buildsTag": fixture.tag,
                **renderer.yaml_document(setup.read_bytes(), str(setup)),
            })
            self.assertEqual(fixture.yaml(".github/dependabot.yml"), {
                "version": 2, "updates": [{
                    "package-ecosystem": "nuget", "directory": "/", "exclude-paths": ["references/**"],
                    "schedule": {"interval": "weekly", "day": "monday", "time": "06:00", "timezone": "Etc/UTC"},
                    "open-pull-requests-limit": 5, "commit-message": {"prefix": "build(deps)"},
                }],
            })
            self.assertEqual(set(fixture.yaml(".github/workflows/ci.yml")["jobs"]),
                             {"ci", "windows-123-job", "windows-alpha-windows", "windows-windows-123-job", "windows-windows-tests"})
            self.assertEqual(set(fixture.yaml(".github/workflows/release.yml")["jobs"]), {"release", "publish"})


    def test_additive_windows_outputs_require_a_contract_that_defines_the_fields(self):
        names = ("solution", "submodules", "global-json", "module-manifest", "windows-checkout", "source-revision", "module-authority")
        with workspace() as fixture:
            fixture.document({"solution": "Fixture.slnx", "jobs": {"product-tests": {"runner": "windows-latest"}}})
            fixture.cli()
            legacy = fixture.yaml(".github/workflows/ci.yml")
            self.assertEqual(set(names[:3]), set(legacy["jobs"]["windows-product-tests"]["steps"][0]["with"]))
            workflow_path = ".github/workflows/ci.yml"
            action_path = "Github/prepare/action.yml"
            producer = renderer.yaml_document(git(fixture.builds, "show", f"{fixture.tag}:{workflow_path}"), "tagged producer")
            prepare = renderer.yaml_document(git(fixture.builds, "show", f"{fixture.tag}:{action_path}"), "tagged prepare")
            for name in names[3:]:
                producer["on"]["workflow_call"]["outputs"][name] = {
                    "description": "Synthetic additive interface fixture.",
                    "value": "${{ jobs.ci.outputs." + name + " }}"}
                prepare["inputs"][name] = {"description": "Synthetic additive interface fixture.", "default": ""}
            fixture.change_tag({workflow_path: json.dumps(producer).encode(), action_path: json.dumps(prepare).encode()})
            fixture.cli()
            forwarded = fixture.yaml(".github/workflows/ci.yml")["jobs"]["windows-product-tests"]["steps"][0]["with"]
            self.assertEqual({name: "${{ needs.ci.outputs." + name + " }}" for name in names}, forwarded)
            with renderer.pinned_contract(fixture.root) as contract:
                global_checks.check_interfaces(fixture.root, "Hexalith.Fixture", contract)

    def test_callers_match_pinned_workflow_and_composite_interfaces(self):
        with workspace() as fixture, renderer.pinned_contract(fixture.root) as contract:
            fixture.setup("full")
            fixture.cli()
            ci = fixture.yaml(".github/workflows/ci.yml")
            release = fixture.yaml(".github/workflows/release.yml")
            def tagged(path):
                return renderer.yaml_document((contract.root / path).read_bytes(), path)
            ci_declaration = tagged(".github/workflows/ci.yml")
            ci_api = ci_declaration["on"]["workflow_call"]
            release_declaration = tagged(".github/workflows/release.yml")
            release_api = release_declaration["on"]["workflow_call"]
            prepare_api = tagged("Github/prepare/action.yml")["inputs"]
            publish_api = tagged("Github/publish/action.yml")["inputs"]
            pull_secrets = {
                "registry-pull-username": "${{ secrets.HEXALITH_REGISTRY_PULL_USERNAME }}",
                "registry-pull-password": "${{ secrets.HEXALITH_REGISTRY_PULL_PASSWORD }}",
            }
            self.assertEqual(ci["name"], "CI")
            self.assertEqual(ci["on"], {"push": {"branches": ["main"]},
                                       "pull_request": {"branches": ["main"]}, "workflow_dispatch": None})
            self.assertEqual(ci["permissions"], {})
            self.assertEqual(ci["concurrency"], {
                "group": "ci-${{ github.event_name }}-${{ github.event_name == 'pull_request' && github.ref || github.sha }}",
                "cancel-in-progress": "${{ github.event_name == 'pull_request' }}",
            })
            names = ("123-job", "alpha-windows", "windows-123-job", "windows-tests")
            self.assertEqual(list(ci["jobs"]), ["ci", *("windows-" + name for name in names)])
            # Qualify the real selected contract, including released restore
            # support, without deriving the expected union through the renderer.
            self.assertEqual(ci_declaration["jobs"]["ci"]["permissions"], {"contents": "read"})
            expected_ci_permissions = {"contents": "read"}
            if "restore" in ci_declaration["jobs"]:
                self.assertEqual(ci_declaration["jobs"]["restore"]["permissions"],
                                 {"contents": "write", "actions": "write"})
                expected_ci_permissions = {"contents": "write", "actions": "write"}
            self.assertEqual(ci["jobs"]["ci"], {
                "uses": f"Hexalith/Hexalith.Builds/.github/workflows/ci.yml@{fixture.tag}",
                "permissions": expected_ci_permissions, "secrets": pull_secrets,
            })
            self.assertEqual(ci["jobs"]["ci"]["permissions"], global_checks.permission_union(ci_declaration))
            self.assert_arguments_supplied(ci["jobs"]["ci"].get("with", {}), ci_api["inputs"])
            self.assert_arguments_supplied(pull_secrets, ci_api["secrets"])
            for name in names:
                job = ci["jobs"]["windows-" + name]
                self.assertEqual(job, {
                    "needs": "ci", "runs-on": "windows-latest", "permissions": {"contents": "read"},
                    "steps": [{
                        "uses": f"Hexalith/Hexalith.Builds/Github/prepare@{fixture.tag}",
                        "with": {key: "${{ needs.ci.outputs." + key + " }}"
                                 for key in ("solution", "submodules", "global-json")},
                    }, {"uses": f"./.github/actions/{name}"}],
                })
                self.assert_arguments_supplied(job["steps"][0]["with"], prepare_api)
                self.assertTrue(set(job["steps"][0]["with"]) <= ci_api["outputs"].keys())
            self.assertEqual(release["name"], "Release")
            self.assertEqual(release["on"], {"workflow_dispatch": {"inputs": {"delivered-sha": {
                "description": "Validated delivered-state commit", "type": "string", "required": False, "default": "",
            }}}})
            self.assertEqual(release["permissions"], {})
            self.assertEqual(release["cache-mode"], "none")
            self.assertEqual(release["concurrency"], {"group": "release", "cancel-in-progress": False})
            self.assertEqual(set(release["jobs"]), {"release", "publish"})
            job = release["jobs"]["release"]
            self.assertEqual(job, {
                "uses": f"Hexalith/Hexalith.Builds/.github/workflows/release.yml@{fixture.tag}",
                "with": {"delivered-sha": "${{ inputs.delivered-sha }}"}, "secrets": pull_secrets,
                "permissions": {"contents": "write", "actions": "read", "security-events": "write"},
            })
            self.assert_arguments_supplied(job["with"], release_api["inputs"])
            self.assert_arguments_supplied(pull_secrets, release_api["secrets"])
            self.assertEqual(job["permissions"], global_checks.permission_union(release_declaration))
            handoff = ("publish", "version", "sha", "last-tag", "draft-id", "artifact-id", "artifact-digest", "artifact-run")
            values = {key: "${{ needs.release.outputs." + key + " }}" for key in handoff}
            values.update({"nuget-user": "${{ vars.HEXALITH_NUGET_USER }}",
                           "registry-username": "${{ secrets.HEXALITH_REGISTRY_USERNAME }}",
                           "registry-password": "${{ secrets.HEXALITH_REGISTRY_PASSWORD }}"})
            self.assertEqual(release["jobs"]["publish"], {
                "needs": "release", "if": "needs.release.outputs.publish == 'true'", "runs-on": "ubuntu-latest",
                "environment": "hexalith-release", "permissions": {"contents": "write", "actions": "read", "id-token": "write"},
                "steps": [{"uses": f"Hexalith/Hexalith.Builds/Github/publish@{fixture.tag}", "with": values}],
            })
            self.assertEqual(set(values), set(publish_api))
            self.assert_arguments_supplied(values, publish_api)
            self.assertTrue(set(handoff) <= release_api["outputs"].keys())
            self.assertTrue(all(publish_api[key]["required"] for key in values))





def lint_fixtures(*, tag=None) -> None:
    """Use tagged pins/installer, but enumerate only our explicit fixture paths."""
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        raise ValueError("Pinned linter archives target Linux x86_64")
    if any(os.environ.get(key) for key in ("ZIZMOR_OFFLINE", "ZIZMOR_NO_ONLINE_AUDITS")):
        raise ValueError("Online zizmor audits are required; remove offline overrides")
    if not any(os.environ.get(key) for key in ("GH_TOKEN", "GITHUB_TOKEN", "ZIZMOR_GITHUB_TOKEN")):
        raise ValueError("Online audits require a read-only GH_TOKEN, GITHUB_TOKEN or ZIZMOR_GITHUB_TOKEN")
    with (workspace(tag=tag) as fixture, renderer.pinned_contract(fixture.root) as contract,
          tempfile.TemporaryDirectory(prefix="hexalith-lint-tools-") as tools_directory):
        for name in ("minimal", "partial", "full", "quoted"):
            fixture.setup(name, f"Hexalith.Fixture-{name}")
        fixture.cli()
        paths = sorted(path.relative_to(fixture.root).as_posix()
                       for path in (fixture.root / "rendered").glob("*/.github/workflows/*.yml"))
        if len(paths) != 8:
            raise ValueError("Expected eight nonempty representative caller paths")
        # Syntax/security fixture for the future execution API. This does not
        # assert that the currently published tag implements that API.
        execution = RenderTests().execution_config({
            "segments": {"runner": "ubuntu-24.04", "trigger": "nightly", "timeoutMinutes": 360,
                         "matrix": {"include": [{"id": "happy-path"}, {"id": "error-handling"}]}},
            "azure-map": {"runner": {"group": "private-ephemeral", "labels": ["self-hosted", "linux", "x64"]},
                          "trigger": "manual", "environment": "approval",
                          "secrets": {"AUTHORITY_JSON": "PAYLOAD_AZURE_AUTHORITY_JSON"}},
            "azure-array": {"runner": {"group": "private-ephemeral", "labels": ["self-hosted", "linux", "x64"]},
                            "trigger": "manual", "environment": "approval", "preparation": "build-only",
                            "timeoutMinutes": 180, "secrets": ["AUTHORITY_JSON"]}})
        execution["buildsTag"] = contract.tag
        _, _, jobs = renderer.execution_jobs(execution, {})
        jobs["qualification-ci"]["permissions"] = renderer.permission_union(renderer.yaml_document(
            (contract.root / ".github/workflows/ci.yml").read_bytes(), "selected CI"))
        relative = "rendered/Hexalith.Fixture-execution/.github/workflows/qualification.yml"
        destination = fixture.root / relative
        destination.parent.mkdir(parents=True)
        destination.write_bytes(renderer.rendered_bytes(renderer.templates(ROOT), renderer.QUALIFICATION, {
            "qualification_jobs": jobs, "qualification_choices": ["nightly", "azure-array", "azure-map"]}))
        paths.append(relative)
        installer = load_module("_tagged_linter_installer", contract.root / "Tools/ci/lint_workflows.py")
        pins = json.loads((contract.root / "Tools/ci/tools.json").read_bytes())
        # A private per-run cache: no other local user can swap a binary that
        # receives the audit token.
        cache = Path(tools_directory)
        binaries = {name: installer.install_tool(name, pins[name], cache) for name in ("actionlint", "zizmor")}
        result = run([binaries["actionlint"], "-shellcheck=", "-pyflakes=", "-config-file",
                      ROOT / "tools/actionlint.yaml", *paths], cwd=fixture.root, check=False)
        if result.returncode:
            raise ValueError(f"actionlint failed ({result.returncode}): "
                             f"{result.stdout.decode()}{result.stderr.decode()}")
        print(f"Builds {contract.tag}: actionlint {pins['actionlint']['version']}: {len(paths)} explicit fixture workflows passed", flush=True)
        result = run([binaries["zizmor"], "--strict-collection", "--no-progress", "--format=json",
                      "--config", ROOT / "tools/zizmor.yml", *paths], cwd=fixture.root, check=False)
        print(result.stderr.decode(), end="", file=sys.stderr)
        if result.returncode not in (0, 11, 12, 13, 14):
            raise ValueError(f"zizmor failed/incomplete scan (exit {result.returncode})")
        findings = json.loads(result.stdout)
        if not isinstance(findings, list):
            raise ValueError("zizmor did not return a complete JSON finding list")
        failures = [finding for finding in findings if not finding["ignored"]]
        if failures:
            for finding in failures:
                print(f"zizmor {finding['ident']}: {finding['desc']}", file=sys.stderr)
            raise ValueError(f"zizmor reported {len(failures)} findings")
        if result.returncode:
            raise ValueError(f"zizmor nonzero exit {result.returncode}, even though no findings were returned")
        print(f"Builds {contract.tag}: zizmor {pins['zizmor']['version']}: {len(paths)} explicit fixture workflows passed online audits", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lint", action="store_true", help="Also install pinned linters and run online fixture audits")
    args, remaining = parser.parse_known_args()
    result = unittest.main(argv=[sys.argv[0], *remaining], exit=False).result
    if not result.wasSuccessful():
        return 1
    if args.lint:
        try:
            lint_fixtures()
            selected = (ROOT / "builds-version").read_text().strip()
            if selected != LEGACY_RELEASE["tag"]:
                lint_fixtures(tag=selected)
        except (OSError, ValueError, RuntimeError, KeyError, AssertionError) as error:
            print(f"Fixture lint failed: {renderer.diagnostic(error)}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
