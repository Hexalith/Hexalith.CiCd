#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Offline renderer CLI qualification; --lint adds explicit-path online audits."""

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
sys.dont_write_bytecode = True


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


renderer = load_module("_cicd_renderer", ROOT / "tools/render.py")


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
    def __init__(self, root: Path):
        self.root = root
        self.builds = root / "references/Hexalith.Builds"
        self.tag = (ROOT / "builds-version").read_text().strip()
        self.builds.parent.mkdir(parents=True)
        run(["git", "clone", "--quiet", "--shared", "--no-checkout",
             ROOT / "references/Hexalith.Builds", self.builds])
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


@contextmanager
def workspace():
    with tempfile.TemporaryDirectory(prefix="hexalith-render-fixture-") as directory:
        yield Workspace(Path(directory))


class RenderTests(unittest.TestCase):
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

    def test_empty_registry_and_exact_yml_enumeration(self):
        with workspace() as fixture:
            (fixture.root / "setup/NotRegistered.yaml").write_text("invalid yaml : [")
            fixture.cli()
            fixture.cli("--check")
            self.assertEqual(file_bytes(fixture.root / "rendered"), {".gitkeep": b""})

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

    def test_strict_yaml_keys_and_values(self):
        invalid = [
            "solution: none\nsolution: none\n", "tests:\n  exclude: {}\n  exclude: {}\n",
            "false: value\n", "1: value\n", "? [a, b]\n: value\n",
            "tests:\n  exclude:\n    1: nightly\n", "dapr: yes\n", "browsers: TRUE\n",
            "solution: 2026-11-13\n", "registry: .nan\n", "registry: .inf\n",
            "hooks: !!set {a: null}\n", "hooks: &a [*a]\n", "<<: {solution: none}\n",
            "hooks: !custom []\n", 'solution: "\\ud800"\n', "{}\n---\n{}\n",
        ]
        with workspace() as fixture:
            path = fixture.setup()
            fixture.cli()
            for document in invalid:
                with self.subTest(document=document):
                    path.write_text(document)
                    self.assert_failure_unchanged(fixture, contains="Hexalith.Fixture.yml")

    def test_names_collisions_and_symlinks_fail_before_writes(self):
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            for name in ("", "Hexalith.Builds", "hexalith.builds", ".", "..", "bad name", "bad\n::error::name"):
                with self.subTest(name=name):
                    path = fixture.document({}, name)
                    result = self.assert_failure_unchanged(fixture)
                    self.assertEqual(result.stderr.count(b"\n"), 1)
                    path.unlink()
            for name in ("hexalith.fixture", ".gitkeep", "Hexalith.Fixture.perimeter.json"):
                with self.subTest(collision=name):
                    path = fixture.document({}, name)
                    self.assert_failure_unchanged(fixture, contains="collision")
                    path.unlink()
            path = fixture.root / "setup/Linked.yml"
            path.symlink_to(fixture.root / "setup/Hexalith.Fixture.yml")
            self.assert_failure_unchanged(fixture, contains="symlink")

    def test_repository_name_length_boundaries(self):
        with workspace() as fixture:
            fixture.document({}, "A" * 100)
            fixture.cli()
            self.assertTrue((fixture.root / "rendered" / ("A" * 100)).is_dir())
            fixture.document({}, "B" * 101)
            self.assert_failure_unchanged(fixture, contains="invalid or reserved repository name")

    def test_output_and_template_symlinks_cannot_escape(self):
        with workspace() as fixture, tempfile.TemporaryDirectory(prefix="render-foreign-") as directory:
            foreign = Path(directory)
            (foreign / "keep").write_bytes(b"foreign bytes\n")
            fixture.setup()
            fixture.cli()
            link = fixture.root / "rendered/obsolete"
            link.symlink_to(foreign, target_is_directory=True)
            result = fixture.cli(check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr.decode())
            self.assertEqual((foreign / "keep").read_bytes(), b"foreign bytes\n")
            self.assertTrue(link.is_symlink())
            link.unlink()
            template = fixture.root / "templates/.github/workflows/ci.yml.j2"
            template.unlink()
            template.symlink_to(foreign / "keep")
            self.assert_failure_unchanged(fixture, contains="symlink")
            template.unlink()
            output = fixture.root / "rendered"
            shutil.rmtree(output)
            output.symlink_to(foreign, target_is_directory=True)
            result = fixture.cli(check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(file_bytes(foreign), {"keep": b"foreign bytes\n"})

    def test_template_errors_are_atomic_and_contextual(self):
        with workspace() as fixture:
            fixture.setup("full")
            fixture.cli()
            perimeter = "Hexalith.Fixture.yml -> perimeter.json"
            replacements = {
                ".github/hexalith-ci.json.j2": [
                    ('{"solution":', ".github/hexalith-ci.json"),
                    ('{"schema": "a", "schema": "b"}', ".github/hexalith-ci.json"),
                    ('[[ missing_value | tojson ]]', ".github/hexalith-ci.json.j2: 'missing_value' is undefined"),
                ],
                ".github/workflows/ci.yml.j2": [
                    (content, ".github/workflows/ci.yml")
                    for content in ('name: A\nname: B\n', 'name: [\n', 'false: a\n', '\ufeffname: A\n')
                ],
                "partials/deny-entries.json.j2": [('["a", "a"]\n', perimeter), ('{}\n', perimeter)],
                "perimeter.json.j2": [('{"schema": "unknown", "entries": []}\n', perimeter)],
            }
            for name, bad_templates in replacements.items():
                path = fixture.root / "templates" / name
                original = path.read_bytes()
                for content, contains in bad_templates:
                    with self.subTest(template=name, content=content):
                        path.write_text(content, encoding="utf-8")
                        self.assert_failure_unchanged(fixture, contains=contains)
                path.write_bytes(original)
            missing = fixture.root / "templates/.github/dependabot.yml.j2"
            missing.unlink()
            self.assert_failure_unchanged(fixture, contains="dependabot.yml.j2")

    def test_bad_module_keeps_all_previous_modules_unchanged(self):
        with workspace() as fixture:
            fixture.setup("full", "A.Valid")
            fixture.setup("partial", "Z.Invalid")
            fixture.cli()
            fixture.document({"solution": "Changed.slnx"}, "A.Valid")
            fixture.document({"registry": None}, "Z.Invalid")
            self.assert_failure_unchanged(fixture, contains="Z.Invalid.yml")

    def test_check_mode_sorted_paths_and_stale_tree_replacement(self):
        with workspace() as fixture:
            setup = fixture.setup("full")
            fixture.cli()
            fixture.output(".github/workflows/ci.yml").write_bytes(b"changed\n")
            fixture.output(".github/hexalith-ci.json").unlink()
            obsolete = fixture.root / "rendered/Z.Obsolete/file"
            obsolete.parent.mkdir()
            obsolete.write_bytes(b"obsolete\n")
            (fixture.root / "rendered/empty-obsolete").mkdir()
            (fixture.root / "rendered/stale\n::error::injected").write_bytes(b"stale\n")
            before = file_bytes(fixture.root / "rendered")
            result = fixture.cli("--check", check=False)
            paths = result.stdout.decode().splitlines()
            self.assertEqual(result.returncode, 1)
            self.assertEqual(paths, sorted(paths))
            self.assertIn("rendered/stale\\u000a::error::injected", paths)
            self.assertFalse([line for line in paths if line.startswith("::")])
            self.assertIn("rendered/Hexalith.Fixture/.github/hexalith-ci.json", paths)
            self.assertIn("rendered/Hexalith.Fixture/.github/workflows/ci.yml", paths)
            self.assertIn("rendered/Z.Obsolete/file", paths)
            self.assertIn("rendered/empty-obsolete", paths)
            self.assertEqual(file_bytes(fixture.root / "rendered"), before)
            fixture.document({"solution": "Fixture.slnx"})
            fixture.cli()
            self.assertEqual(set(fixture.yaml(".github/workflows/ci.yml")["jobs"]), {"ci"})
            self.assertFalse(obsolete.parent.exists())
            fixture.cli("--check")
            setup.rename(setup.with_name("Renamed.yml"))
            fixture.cli()
            self.assertFalse((fixture.root / "rendered/Hexalith.Fixture").exists())
            self.assertTrue((fixture.root / "rendered/Renamed.perimeter.json").is_file())
            (fixture.root / "setup/Renamed.yml").unlink()
            fixture.cli()
            self.assertEqual(file_bytes(fixture.root / "rendered"), {".gitkeep": b""})

    def test_missing_root_and_keep_check_do_not_write(self):
        with workspace() as fixture:
            shutil.rmtree(fixture.root / "rendered")
            result = fixture.cli("--check", check=False)
            self.assertEqual(result.returncode, 1)
            self.assertFalse((fixture.root / "rendered").exists())
            self.assertIn("rendered/.gitkeep", result.stdout.decode())
            fixture.cli()
            fixture.cli("--check")
            (fixture.root / "rendered/.gitkeep").write_bytes(b"reserved bytes\n")
            fixture.setup()
            fixture.cli()
            self.assertEqual((fixture.root / "rendered/.gitkeep").read_bytes(), b"reserved bytes\n")

    def test_publication_install_oserror_restores_complete_previous_tree(self):
        with tempfile.TemporaryDirectory(prefix="render-rollback-") as directory:
            root = Path(directory)
            output = root / "rendered"
            (output / "module/empty").mkdir(parents=True)
            (output / "module/owned.json").write_bytes(b"previous owned bytes\n")
            (output / ".gitkeep").write_bytes(b"reserved bytes\n")
            before = file_bytes(output)
            directories = {path.relative_to(output) for path in output.rglob("*") if path.is_dir()}
            rename = Path.rename
            failed = False

            def fail_install(path, target):
                nonlocal failed
                if path.name == "new" and Path(target) == output:
                    self.assertFalse(output.exists())
                    self.assertTrue((path.parent / "old").is_dir())
                    failed = True
                    raise OSError("injected staged-tree installation failure")
                return rename(path, target)

            with mock.patch.object(Path, "rename", fail_install):
                with self.assertRaisesRegex(OSError, "staged-tree installation"):
                    renderer.publish(output, {"module/new.json": b"replacement bytes\n"})
            self.assertTrue(failed)
            self.assertEqual(file_bytes(output), before)
            self.assertEqual({path.relative_to(output) for path in output.rglob("*") if path.is_dir()}, directories)
            self.assertEqual(list(root.iterdir()), [output])

    def test_publication_interrupts_at_rename_boundaries_restore_previous_tree(self):
        for boundary in ("before-backup", "after-backup", "before-install", "after-install"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory(prefix="render-interrupt-") as directory:
                root = Path(directory)
                output = root / "rendered"
                (output / "module/empty").mkdir(parents=True)
                (output / "module/owned.json").write_bytes(b"previous bytes\n")
                (output / ".gitkeep").write_bytes(b"reserved bytes\n")
                before = file_bytes(output)
                directories = {path.relative_to(output) for path in output.rglob("*") if path.is_dir()}
                rename = Path.rename
                interrupted = False

                def interrupt(path, target):
                    nonlocal interrupted
                    operation = "backup" if path == output and Path(target).name == "old" else (
                        "install" if path.name == "new" and Path(target) == output else "rollback")
                    if not interrupted and boundary == f"before-{operation}":
                        interrupted = True
                        raise KeyboardInterrupt
                    result = rename(path, target)
                    if not interrupted and boundary == f"after-{operation}":
                        interrupted = True
                        raise KeyboardInterrupt
                    return result

                with mock.patch.object(Path, "rename", interrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        renderer.publish(output, {"module/new.json": b"replacement bytes\n"})
                self.assertTrue(interrupted)
                self.assertEqual(file_bytes(output), before)
                self.assertEqual({path.relative_to(output) for path in output.rglob("*") if path.is_dir()}, directories)
                self.assertEqual(list(root.iterdir()), [output])

    def test_interrupted_first_publication_leaves_no_output(self):
        for boundary in ("before-install", "after-install"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory(prefix="render-first-") as directory:
                root = Path(directory)
                output = root / "rendered"
                rename = Path.rename
                interrupted = False

                def interrupt(path, target):
                    nonlocal interrupted
                    install = path.name == "new" and Path(target) == output
                    if install and not interrupted and boundary == "before-install":
                        interrupted = True
                        raise KeyboardInterrupt
                    result = rename(path, target)
                    if install and not interrupted and boundary == "after-install":
                        interrupted = True
                        raise KeyboardInterrupt
                    return result

                with mock.patch.object(Path, "rename", interrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        renderer.publish(output, {"module/new.json": b"replacement bytes\n"})
                self.assertTrue(interrupted)
                self.assertFalse(output.exists())
                self.assertEqual(list(root.iterdir()), [])

    def test_determinism_cwd_time_and_module_state(self):
        with workspace() as fixture:
            fixture.setup("full")
            fixture.cli()
            before = file_bytes(fixture.root / "rendered")
            foreign = fixture.root / "references/Unregistered/.github"
            foreign.mkdir(parents=True)
            (foreign / "hexalith-ci.json").write_text("invalid\n")
            fixture.cli(cwd="/", env={"TZ": "Pacific/Auckland", "SOURCE_DATE_EPOCH": "1"})
            self.assertEqual(file_bytes(fixture.root / "rendered"), before)
            fixture.cli("--check", cwd="/tmp")
            script = fixture.root / "tools/render.py"
            script.parent.mkdir()
            shutil.copyfile(ROOT / "tools/render.py", script)
            run([sys.executable, "-I", script, "--check"], cwd="/")
            # Inherited Git discovery variables, as in a superproject hook, are ignored.
            unrelated = fixture.root / "unrelated"
            run(["git", "init", "--quiet", unrelated])
            fixture.cli("--check", env={"GIT_DIR": str(unrelated / ".git"), "GIT_WORK_TREE": str(unrelated)})

    def test_uninitialized_builds_never_resolves_to_superproject(self):
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            shutil.rmtree(fixture.builds)
            fixture.builds.mkdir()
            git(fixture.root, "init", "--quiet")
            git(fixture.root, "commit", "--quiet", "--allow-empty", "-m", "Superproject fixture")
            git(fixture.root, "tag", fixture.tag)
            self.assert_failure_unchanged(fixture, contains="not a git repository")

    def test_tag_objects_win_over_head_and_worktree(self):
        with workspace() as fixture:
            fixture.setup("full")
            fixture.cli()
            before = file_bytes(fixture.root / "rendered")
            schema_path = "schemas/hexalith.ci.v1.json"
            fixture.change_tag({schema_path: b"invalid HEAD schema\n"}, move_tag=False)
            (fixture.builds / "schemas").mkdir()
            (fixture.builds / schema_path).write_text("invalid working schema\n")
            (fixture.builds / "Github/lib").mkdir(parents=True)
            (fixture.builds / "Github/lib/ci_config.py").write_text("raise RuntimeError('mutable loader')\n")
            attributes = fixture.builds / ".git/info/attributes"
            attributes.write_text("schemas/** export-ignore\nGithub/** export-ignore\n")
            # Local replace refs must not substitute the tagged schema blob.
            tagged = git(fixture.builds, "rev-parse", f"{fixture.tag}:{schema_path}").decode().strip()
            replacement = git(fixture.builds, "hash-object", "-w", "--stdin",
                              input=b"invalid replaced schema\n").decode().strip()
            git(fixture.builds, "replace", tagged, replacement)
            fixture.cli("--check")
            fixture.cli()
            self.assertEqual(file_bytes(fixture.root / "rendered"), before)

    def test_missing_tag_and_schemas_fail_without_writes(self):
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            pin = fixture.root / "builds-version"
            for value in ("main\n", "v05.1.0\n", "v5.1.0-rc.1\n", "v5.1.0\n\n", "v999.0.0\n"):
                with self.subTest(pin=value):
                    pin.write_text(value)
                    self.assert_failure_unchanged(fixture)
        for kind in ("ci", "perimeter"):
            for mode in ("missing", "ambiguous"):
                with workspace() as fixture, self.subTest(kind=kind, mode=mode):
                    fixture.setup()
                    fixture.cli()
                    name = f"schemas/hexalith.{kind}.v1.json"
                    data = git(fixture.builds, "show", f"{fixture.tag}:{name}")
                    fixture.change_tag({name: None} if mode == "missing" else
                                       {f"schemas/hexalith.{kind}.v2.json": data})
                    self.assert_failure_unchanged(fixture, contains=f"exactly one {kind} schema")

    def test_defaults_come_from_pinned_schema_and_missing_required_fails(self):
        with workspace() as fixture:
            fixture.document({"solution": "Fixture.slnx"})
            schema_path = "schemas/hexalith.ci.v1.json"
            schema = json.loads(git(fixture.builds, "show", f"{fixture.tag}:{schema_path}"))
            schema["properties"]["submodules"]["default"] = ["references/DefaultSibling"]
            schema["properties"]["tests"]["properties"]["integration"]["default"] = ["test/Default.csproj"]
            # An explicitly supplied empty object still receives nested defaults.
            fixture.document({"solution": "Fixture.slnx", "tests": {}})
            fixture.change_tag({schema_path: json.dumps(schema).encode()})
            fixture.cli()
            self.assertEqual(fixture.json()["submodules"], ["references/DefaultSibling"])
            self.assertEqual(fixture.json()["tests"]["integration"], ["test/Default.csproj"])
            del schema["properties"]["solution"]["default"]
            fixture.change_tag({schema_path: json.dumps(schema).encode()})
            fixture.document({})
            self.assert_failure_unchanged(fixture, contains="solution")

    def test_referenced_defaults_follow_tagged_schema_and_preserve_explicit_values(self):
        with workspace() as fixture:
            fixture.setup()
            schema_path = "schemas/hexalith.ci.v1.json"
            schema = json.loads(git(fixture.builds, "show", f"{fixture.tag}:{schema_path}"))
            source = schema["properties"]["submodules"]
            source["default"] = ["references/ReferencedDefault"]
            schema["$defs"]["submoduleKnob"] = source
            schema["properties"]["submodules"] = {"$ref": "#/$defs/submoduleKnob"}
            fixture.change_tag({schema_path: json.dumps(schema).encode()})
            fixture.cli()
            self.assertEqual(fixture.json()["submodules"], ["references/ReferencedDefault"])
            fixture.document({"submodules": []})
            fixture.cli()
            self.assertEqual(fixture.json()["submodules"], [])
            fixture.document({"submodules": ["references/Explicit"]})
            fixture.cli()
            self.assertEqual(fixture.json()["submodules"], ["references/Explicit"])
            fixture.document({"submodules": None})
            self.assert_failure_unchanged(fixture, contains="submodules")

    def test_schema_validation_and_strict_loader_both_run(self):
        with workspace() as fixture:
            fixture.setup("partial")
            fixture.cli()
            schema_path = "schemas/hexalith.ci.v1.json"
            schema = json.loads(git(fixture.builds, "show", f"{fixture.tag}:{schema_path}"))
            schema["properties"]["registry"]["const"] = True
            fixture.change_tag({schema_path: json.dumps(schema).encode()})
            self.assert_failure_unchanged(fixture, contains="True was expected")
        with workspace() as fixture:
            fixture.setup("partial")
            fixture.cli()
            loader = "Github/lib/ci_config.py"
            data = git(fixture.builds, "show", f"{fixture.tag}:{loader}")
            data = data.replace(b'    return document\n', b'    raise ConfigError("pinned reader qualification")\n')
            fixture.change_tag({loader: data})
            self.assert_failure_unchanged(fixture, contains="pinned reader qualification")
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            loader = "Github/lib/perimeter_config.py"
            data = git(fixture.builds, "show", f"{fixture.tag}:{loader}")
            data = data.replace(b'    return document\n', b'    raise ConfigError("pinned perimeter qualification")\n')
            fixture.change_tag({loader: data})
            self.assert_failure_unchanged(fixture, contains="pinned perimeter qualification")

    def test_remote_schema_refs_are_rejected_offline(self):
        for keyword in ("$ref", "$dynamicRef"):
            with self.subTest(keyword=keyword), workspace() as fixture:
                fixture.setup()
                fixture.cli()
                path = "schemas/hexalith.ci.v1.json"
                external = fixture.root / "external-schema.json"
                document = json.loads(git(fixture.builds, "show", f"{fixture.tag}:{path}"))
                document["properties"]["solution"] = {keyword: external.as_uri()}
                fixture.change_tag({path: json.dumps(document).encode()})
                for content in ('{"const": "none"}', '{"not": {}}', None):
                    if content is None:
                        external.unlink()
                    else:
                        external.write_text(content)
                    result = self.assert_failure_unchanged(fixture, contains=f"nonlocal schema reference {keyword}")
                    self.assertIn("hexalith.ci.v1.json", result.stderr.decode())
                document["properties"]["solution"] = {keyword: "https://example.invalid/schema"}
                fixture.change_tag({path: json.dumps(document).encode()})
                self.assert_failure_unchanged(fixture, contains=f"nonlocal schema reference {keyword}")

    def test_validator_itself_prohibits_external_retrieval(self):
        with tempfile.TemporaryDirectory(prefix="render-schema-retrieval-") as directory:
            root = Path(directory)
            external = root / "external.json"
            external.write_text("{}\n")
            for keyword in ("$ref", "$dynamicRef"):
                with self.subTest(keyword=keyword), mock.patch.object(
                    renderer, "deny_schema_retrieval", wraps=renderer.deny_schema_retrieval,
                ) as denied:
                    contract = renderer.Contract(root, "v1.0.0", "unused", {"ci": {keyword: external.as_uri()}})
                    with self.assertRaisesRegex(renderer.RenderError, "fixture.json: schema reference resolution failed"):
                        contract.validate("ci", b"{}", "fixture.json", "Hexalith.Fixture")
                    denied.assert_called_once_with(external.as_uri())

    def test_missing_promisor_blob_does_not_invoke_remote_helper(self):
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            data = f"# unique missing fixture blob {fixture.root}\n".encode()
            fixture.change_tag({"Github/lib/missing_fixture.py": data})
            oid = git(fixture.builds, "hash-object", "--stdin", input=data).decode().strip()
            (fixture.builds / ".git/objects" / oid[:2] / oid[2:]).unlink()
            git(fixture.builds, "config", "extensions.partialClone", "origin")
            git(fixture.builds, "config", "remote.origin.promisor", "true")
            git(fixture.builds, "config", "remote.origin.partialclonefilter", "blob:none")
            git(fixture.builds, "remote", "set-url", "origin", "fixture-missing::unavailable")
            helpers = fixture.root / "helpers"
            helpers.mkdir()
            helper = helpers / "git-remote-fixture-missing"
            helper.write_text('#!/bin/sh\nprintf attempted >> "$RENDER_REMOTE_PROBE"\nexit 1\n')
            helper.chmod(0o755)
            marker = fixture.root / "remote-invoked"
            environment = {"PATH": str(helpers) + os.pathsep + os.environ["PATH"],
                           "RENDER_REMOTE_PROBE": str(marker), "GIT_NO_LAZY_FETCH": "0"}
            before = file_bytes(fixture.root / "rendered")
            result = fixture.cli(check=False, env=environment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing local Git blob", result.stderr.decode())
            self.assertNotIn("Traceback", result.stderr.decode())
            self.assertEqual(file_bytes(fixture.root / "rendered"), before)
            self.assertFalse(marker.exists())
            # A control read proves this promisor fixture really would fetch.
            git(fixture.builds, "cat-file", "--batch", input=(oid + "\n").encode(), env=environment, check=False)
            self.assertTrue(marker.exists())

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

    def test_perimeter_all_nine_kinds_and_exact_interim_policy(self):
        with workspace() as fixture:
            fixture.setup()
            fixture.cli()
            perimeter = json.loads((fixture.root / "rendered/Hexalith.Fixture.perimeter.json").read_bytes())
            entries = perimeter["entries"]
            self.assertEqual({entry["kind"] for entry in entries}, {
                "whole", "whole-dir", "gitlink", "gitmodules-section", "json-superset",
                "marker-block", "absent-glob", "absent-json", "absent-line",
            })
            self.assertEqual(len(entries), 17)
            blocks = [entry for entry in entries if entry["kind"] == "marker-block"]
            self.assertEqual({entry["path"] for entry in blocks},
                             {"AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"})
            self.assertTrue(all(entry["text"] == "CI/CD ownership instruction placeholder; replaced by story 10-2.\n"
                                for entry in blocks))
            deny = next(entry for entry in entries if entry["kind"] == "json-superset")
            self.assertEqual(deny, {"kind": "json-superset", "path": ".claude/settings.json",
                                    "pointer": "/permissions/deny", "values": []})
            self.assertEqual(next(entry for entry in entries if entry["kind"] == "gitlink")["buildsTag"], fixture.tag)
            self.assertEqual({entry["pattern"] for entry in entries if entry["kind"] == "absent-glob"}, {
                ".releaserc*", "release.config.*", "commitlint.config.*", ".commitlintrc*",
                "**/Directory.Build.rsp", "**/bmad-testarch-ci/**",
            })
            selectors = next(entry for entry in entries if entry["kind"] == "absent-json")["selectors"]
            self.assertEqual(selectors, [["release"], ["commitlint"]] + [
                [group, package] for group in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")
                for package in ("semantic-release", "@semantic-release/*", "@commitlint/*")])
            self.assertEqual(next(entry for entry in entries if entry["kind"] == "absent-line"),
                             {"kind": "absent-line", "path": ".husky/commit-msg", "pattern": r"\bcommitlint\b"})

    def test_callers_match_pinned_workflow_and_composite_interfaces(self):
        with workspace() as fixture, renderer.pinned_contract(fixture.root) as contract:
            fixture.setup("full")
            fixture.cli()
            ci = fixture.yaml(".github/workflows/ci.yml")
            release = fixture.yaml(".github/workflows/release.yml")
            def tagged(path):
                return renderer.yaml_document((contract.root / path).read_bytes(), path)
            ci_api = tagged(".github/workflows/ci.yml")["on"]["workflow_call"]
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
            self.assertEqual(ci["jobs"]["ci"], {
                "uses": f"Hexalith/Hexalith.Builds/.github/workflows/ci.yml@{fixture.tag}",
                "permissions": {"contents": "read"}, "secrets": pull_secrets,
            })
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
            union = {}
            for shared_job in release_declaration["jobs"].values():
                for scope, permission in shared_job["permissions"].items():
                    if union.get(scope) != "write":
                        union[scope] = permission
            self.assertEqual(job["permissions"], union)
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

    def test_new_required_callable_arguments_are_detected(self):
        with workspace() as fixture, renderer.pinned_contract(fixture.root) as contract:
            fixture.setup("full")
            fixture.cli()
            ci = fixture.yaml(".github/workflows/ci.yml")["jobs"]
            release = fixture.yaml(".github/workflows/release.yml")["jobs"]
            def tagged(path):
                return renderer.yaml_document((contract.root / path).read_bytes(), path)
            ci_api = tagged(".github/workflows/ci.yml")["on"]["workflow_call"]
            release_api = tagged(".github/workflows/release.yml")["on"]["workflow_call"]
            cases = [
                ("ci-inputs", ci["ci"].get("with", {}), ci_api["inputs"]),
                ("ci-secrets", ci["ci"]["secrets"], ci_api["secrets"]),
                ("release-inputs", release["release"]["with"], release_api["inputs"]),
                ("release-secrets", release["release"]["secrets"], release_api["secrets"]),
                ("prepare-inputs", ci["windows-123-job"]["steps"][0]["with"], tagged("Github/prepare/action.yml")["inputs"]),
                ("publish-inputs", release["publish"]["steps"][0]["with"], tagged("Github/publish/action.yml")["inputs"]),
            ]
            for name, supplied, declarations in cases:
                with self.subTest(callable=name):
                    declarations = dict(declarations)
                    declarations["new-required-argument"] = {"required": True}
                    with self.assertRaisesRegex(AssertionError, "new-required-argument"):
                        self.assert_arguments_supplied(supplied, declarations)

    def test_tagged_perimeter_applies_only_index_and_preserves_foreign_content(self):
        with workspace() as fixture, renderer.pinned_contract(fixture.root) as contract:
            fixture.setup("full")
            fixture.cli()
            git(fixture.root, "init", "--quiet")
            git(fixture.root, "add", "rendered")
            git(fixture.root, "commit", "--quiet", "-m", "Fixture expected render")
            module = fixture.root / "module"
            module.mkdir()
            git(module, "init", "--quiet")
            files = {
                ".github/workflows/obsolete.yml": b"foreign obsolete workflow\n",
                ".github/hexalith-ci.json": b"malformed owned json\n",
                ".github/dependabot.yml": b"malformed owned yaml\n",
                ".github/actions/windows-tests/action.yml": b"module-owned product action\n",
                ".gitmodules": b'[submodule "other"]\n\tpath = references/Other\n\turl = https://example.invalid/Other.git\n',
                ".claude/settings.json": b'{"permissions":{"allow":["Read(**)"],"deny":["foreign-deny"]},"other":true}\n',
                "AGENTS.md": b"Foreign instructions before.\n<!-- hexalith-cicd:begin -->\nold\n<!-- hexalith-cicd:end -->\nForeign after.\n",
                "CLAUDE.md": b"Foreign Claude instructions.\n",
                ".github/copilot-instructions.md": b"Foreign Copilot instructions.\n",
                ".releaserc.json": b"{}\n", "release.config.cjs": b"obsolete\n",
                "commitlint.config.js": b"obsolete\n", ".commitlintrc.yml": b"obsolete\n",
                "Directory.Build.rsp": b"obsolete\n", "nested/Directory.Build.rsp": b"obsolete\n",
                ".agents/skills/bmad-testarch-ci/SKILL.md": b"obsolete\n",
                ".husky/commit-msg": b"#!/bin/sh\nnpx commitlint --edit\necho foreign\n",
                "product.txt": b"foreign product bytes\n",
            }
            package = {"name": "foreign-package", "release": {}, "commitlint": {},
                       "scripts": {"release": "foreign product script"}}
            for group in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                package[group] = {"semantic-release": "1", "@semantic-release/git": "1",
                                  "@commitlint/cli": "1", "foreign-product": "2"}
            files["package.json"] = (json.dumps(package) + "\n").encode()
            for relative, data in files.items():
                path = module / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            git(module, "add", ".")
            git(module, "commit", "--quiet", "-m", "Fixture owned drift and foreign content")
            before = file_bytes(module)
            library = load_module("_qualified_perimeter", contract.root / "Github/lib/perimeter.py")
            document = library.config.load_config(fixture.root / "rendered/Hexalith.Fixture.perimeter.json")
            repository = library.Git(module)
            expected = library.Git(fixture.root).snapshot()
            builds = library.Git(fixture.builds)
            options = {"expected": expected, "rendered_root": "rendered/Hexalith.Fixture", "builds": builds}
            self.assertTrue(library.compare(document, repository.snapshot(), **options))
            self.assertTrue(library.apply(document, repository, **options))
            actual = repository.snapshot("index")
            self.assertEqual(library.compare(document, actual, **options), [])
            self.assertEqual(file_bytes(module), before)
            self.assertEqual(actual.read("product.txt"), files["product.txt"])
            self.assertEqual(actual.read(".github/actions/windows-tests/action.yml"), files[".github/actions/windows-tests/action.yml"])
            self.assertEqual(json.loads(actual.read(".claude/settings.json")), json.loads(files[".claude/settings.json"]))
            for name, foreign in (("AGENTS.md", b"Foreign instructions before."), ("CLAUDE.md", b"Foreign Claude instructions."),
                                  (".github/copilot-instructions.md", b"Foreign Copilot instructions.")):
                self.assertIn(foreign, actual.read(name))
                self.assertIn(b"CI/CD ownership instruction placeholder; replaced by story 10-2.", actual.read(name))
            self.assertIn(b"Foreign after.", actual.read("AGENTS.md"))
            self.assertIn(b"references/Other", actual.read(".gitmodules"))
            self.assertIn(b"https://github.com/Hexalith/Hexalith.Builds.git", actual.read(".gitmodules"))
            self.assertEqual(actual.items["references/Hexalith.Builds"].mode, "160000")
            self.assertEqual(actual.items["references/Hexalith.Builds"].oid, contract.revision)
            repaired = json.loads(actual.read("package.json"))
            self.assertNotIn("release", repaired)
            self.assertNotIn("commitlint", repaired)
            self.assertEqual(repaired["scripts"], package["scripts"])
            for group in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                self.assertEqual(repaired[group], {"foreign-product": "2"})
            self.assertEqual(actual.read(".husky/commit-msg"), b"#!/bin/sh\necho foreign\n")
            for relative in (".github/workflows/obsolete.yml", ".releaserc.json", "release.config.cjs", "commitlint.config.js",
                             ".commitlintrc.yml", "Directory.Build.rsp", "nested/Directory.Build.rsp",
                             ".agents/skills/bmad-testarch-ci/SKILL.md"):
                self.assertNotIn(relative, actual.items)
            for relative in renderer.TEMPLATES:
                self.assertEqual(actual.read(relative), fixture.output(relative).read_bytes())
            index = repository.index_path().read_bytes()
            self.assertEqual(library.apply(document, repository, **options), [])
            self.assertEqual(repository.index_path().read_bytes(), index)
            self.assertEqual(file_bytes(module), before)


def lint_fixtures() -> None:
    """Use tagged pins/installer, but enumerate only our explicit fixture paths."""
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        raise ValueError("Pinned linter archives target Linux x86_64")
    if any(os.environ.get(key) for key in ("ZIZMOR_OFFLINE", "ZIZMOR_NO_ONLINE_AUDITS")):
        raise ValueError("Online zizmor audits are required; remove offline overrides")
    if not any(os.environ.get(key) for key in ("GH_TOKEN", "GITHUB_TOKEN", "ZIZMOR_GITHUB_TOKEN")):
        raise ValueError("Online audits require a read-only GH_TOKEN, GITHUB_TOKEN or ZIZMOR_GITHUB_TOKEN")
    with (workspace() as fixture, renderer.pinned_contract(fixture.root) as contract,
          tempfile.TemporaryDirectory(prefix="hexalith-lint-tools-") as tools_directory):
        for name in ("minimal", "partial", "full", "quoted"):
            fixture.setup(name, f"Hexalith.Fixture-{name}")
        fixture.cli()
        paths = sorted(path.relative_to(fixture.root).as_posix()
                       for path in (fixture.root / "rendered").glob("*/.github/workflows/*.yml"))
        if len(paths) != 8:
            raise ValueError("Expected eight nonempty representative caller paths")
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
        print(f"actionlint {pins['actionlint']['version']}: {len(paths)} explicit fixture workflows passed", flush=True)
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
        print(f"zizmor {pins['zizmor']['version']}: {len(paths)} explicit fixture workflows passed online audits", flush=True)


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
        except (OSError, ValueError, RuntimeError, KeyError, AssertionError) as error:
            print(f"Fixture lint failed: {renderer.diagnostic(error)}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
