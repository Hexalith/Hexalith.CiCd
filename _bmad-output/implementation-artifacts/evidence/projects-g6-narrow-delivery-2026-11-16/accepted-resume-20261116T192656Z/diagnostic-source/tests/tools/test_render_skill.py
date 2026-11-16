"""Hermetic fixture tests for the shared BMAD skill renderer."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RENDERER_PATH = PROJECT_ROOT / "_bmad" / "scripts" / "render_skill.py"
CI_PATH = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


@dataclass(frozen=True)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _load_renderer_module() -> ModuleType:
    module_name = "fixture_render_skill"
    specification = importlib.util.spec_from_file_location(module_name, RENDERER_PATH)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Unable to load renderer module from {RENDERER_PATH}")
    module = importlib.util.module_from_spec(specification)
    scripts_root = str(RENDERER_PATH.parent)
    sys.path.insert(0, scripts_root)
    try:
        specification.loader.exec_module(module)
    finally:
        sys.path.remove(scripts_root)
    return module


class RenderSkillFixtureTests(unittest.TestCase):
    """Exercise the checked-in renderer with dependency-free temporary fixtures."""

    def make_fixture(
        self,
        root: Path,
        *,
        workflow: str = "Fixture workflow.\n",
        guide: str = "Fixture guide.\n",
        central_config: str = '[fixture]\nvalue = "base"\n',
        customization: str | None = None,
    ) -> RendererFixture:
        project_root = root / "project fixture with spaces"
        skill_root = root / "skill fixtures" / "fixture-skill"
        caller_root = root / "caller cwd with spaces"
        caller_root.mkdir(parents=True)
        _write_text(project_root / "_bmad" / "config.toml", central_config)
        _write_text(skill_root / "SKILL.md", "---\nname: fixture-skill\n---\n")
        _write_text(skill_root / "workflow.md", workflow)
        _write_text(skill_root / "guide.md", guide)
        if customization is not None:
            _write_text(skill_root / "customize.toml", customization)
        return RendererFixture(project_root, skill_root, caller_root)

    def run_renderer(
        self, fixture: RendererFixture
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [
                sys.executable,
                str(RENDERER_PATH),
                "--project-root",
                str(fixture.project_root),
                "--skill",
                str(fixture.skill_root),
            ],
            cwd=fixture.caller_root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=30,
        )

    def assert_success(
        self,
        completed: subprocess.CompletedProcess[str],
    ) -> Path:
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual("", completed.stderr)
        prefix = "read and follow "
        self.assertTrue(completed.stdout.startswith(prefix), completed.stdout)
        self.assertTrue(completed.stdout.endswith("\n"), completed.stdout)
        entry = Path(completed.stdout[len(prefix) :].rstrip("\n"))
        self.assertEqual(f"read and follow {entry}\n", completed.stdout)
        self.assertTrue(entry.is_file(), entry)
        return entry

    def assert_halt(
        self,
        completed: subprocess.CompletedProcess[str],
        expected_prefix: str,
    ) -> None:
        self.assertEqual(1, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual("", completed.stderr)
        self.assertTrue(
            completed.stdout.startswith(expected_prefix),
            f"Expected prefix {expected_prefix!r}, got {completed.stdout!r}",
        )
        self.assertTrue(completed.stdout.endswith("\n"), completed.stdout)
        self.assertEqual(1, completed.stdout.count("\n"), completed.stdout)

    def assert_manifest_integrity(
        self,
        fixture: RendererFixture,
        entry: Path,
        expected_outputs: set[str],
    ) -> dict[str, object]:
        destination = entry.parent
        manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(1, manifest["schema_version"])
        self.assertEqual(fixture.skill_root.name, manifest["skill"])
        self.assertEqual(str(fixture.project_root), manifest["project_root"])
        renderer = _load_renderer_module()
        self.assertEqual(
            renderer._project_slug(fixture.project_root), manifest["project_slug"]
        )

        root_hash = renderer._root_hash(fixture.project_root)
        self.assertEqual(root_hash, manifest["root_hash"])
        self.assertEqual(
            f"{manifest['project_slug']}-{root_hash}", destination.parent.name
        )
        self.assertEqual(fixture.skill_root.name, destination.parent.parent.name)

        inputs = manifest["inputs"]
        self.assertIsInstance(inputs, dict)
        generation_hash = renderer._generation_hash(inputs)
        self.assertEqual(generation_hash, manifest["generation_hash"])
        self.assertEqual(generation_hash, destination.name)
        self.assertEqual(str(fixture.project_root), inputs["project_root"])
        self.assertEqual(_sha256(RENDERER_PATH.read_bytes()), inputs["renderer_sha256"])

        sources = {
            path.relative_to(fixture.skill_root).as_posix(): _sha256(
                path.read_text(encoding="utf-8").encode("utf-8")
            )
            for path in fixture.skill_root.rglob("*.md")
            if path.name != "SKILL.md"
        }
        self.assertEqual(sources, inputs["source_sha256"])
        self.assertEqual(expected_outputs, set(manifest["outputs"]))
        self.assertEqual(
            expected_outputs | {"manifest.json"}, set(_tree_bytes(destination))
        )
        for name, expected_hash in manifest["outputs"].items():
            self.assertEqual(expected_hash, _sha256((destination / name).read_bytes()))
        return manifest

    def test_root_planning_context_excludes_sibling_contexts(self) -> None:
        for skill_name in ("bmad-spec", "bmad-sprint-planning"):
            with self.subTest(skill=skill_name), tempfile.TemporaryDirectory() as temporary:
                fixture = self.make_fixture(
                    Path(temporary),
                    workflow="Facts:\n{workflow.persistent_facts}\n",
                    customization='[workflow]\npersistent_facts = []\n',
                )
                skill_root = fixture.skill_root.with_name(skill_name)
                fixture.skill_root.rename(skill_root)
                fixture = RendererFixture(fixture.project_root, skill_root, fixture.caller_root)
                _write_text(
                    fixture.project_root / "_bmad" / "custom" / f"{skill_name}.toml",
                    (PROJECT_ROOT / "_bmad" / "custom" / f"{skill_name}.toml").read_text(encoding="utf-8"),
                )
                root_context = fixture.project_root / "_bmad-output" / "project-context.md"
                sibling_context = fixture.project_root / "references" / "Sibling" / "project-context.md"
                _write_text(root_context, "Root context.\n")
                _write_text(sibling_context, "Contradictory sibling context.\n")
                entry = self.assert_success(self.run_renderer(fixture))
                facts = [line.removeprefix("- file:") for line in entry.read_text().splitlines() if line.startswith("- file:")]
                matched = [path for fact in facts for path in fixture.project_root.glob(fact.removeprefix("{project-root}/"))]
                self.assertEqual([root_context], matched)

    def test_identity_helpers_preserve_fixed_vectors(self) -> None:
        renderer = _load_renderer_module()
        project = Path("Project Fixture With Spaces")
        self.assertEqual("project-fixture-with-spaces", renderer._project_slug(project))
        self.assertEqual("3d3bdc19974a", renderer._root_hash(project))
        self.assertEqual("project", renderer._project_slug(Path("---")))
        self.assertEqual("a" * 79, renderer._project_slug(Path("a" * 79 + " b")))
        self.assertEqual(
            "c5c0c21621d614e4d01d",
            renderer._generation_hash({"number": 1, "example": "雪"}),
        )

    def test_layer_precedence_lists_and_keyed_review_replacement(self) -> None:
        workflow = """Central winner: {{config.settings.winner}}
Base only: {{config.settings.base_only}}
User only: {{config.settings.user_only}}
Team only: {{config.settings.team_only}}
Final only: {{config.settings.final_only}}
Artifact root: {{.artifact_root}}
Headline: {workflow.headline}
Prepend:
{workflow.prepend_steps}
Append:
{workflow.append_steps}
Review:
{workflow.review_layers}
"""
        defaults = """[workflow]
headline = "default headline"
prepend_steps = ["default prepend"]
append_steps = ["default append"]

[[workflow.review_layers]]
id = "security"
name = "Default Security"
instruction = "default security instruction"
when = "always"

[[workflow.review_layers]]
id = "structure"
name = "Default Structure"
instruction = "default structure instruction"
"""
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            fixture = self.make_fixture(
                Path(directory),
                workflow=workflow,
                central_config="""[settings]
winner = "base"
base_only = "base value"
artifact_root = "{project-root}/artifacts"
""",
                customization=defaults,
            )
            custom_root = fixture.project_root / "_bmad" / "custom"
            _write_text(
                fixture.project_root / "_bmad" / "config.user.toml",
                '[settings]\nwinner = "central user"\nuser_only = "user value"\n',
            )
            _write_text(
                custom_root / "config.toml",
                '[settings]\nwinner = "team"\nteam_only = "team value"\n',
            )
            _write_text(
                custom_root / "config.user.toml",
                '[settings]\nwinner = "custom user"\nfinal_only = "final value"\n',
            )
            _write_text(
                custom_root / f"{fixture.skill_root.name}.toml",
                """[workflow]
headline = "team headline"
prepend_steps = ["team prepend"]
append_steps = ["team append"]

[[workflow.review_layers]]
id = "security"
instruction = "team security instruction"

[[workflow.review_layers]]
id = "performance"
name = "Team Performance"
instruction = "team performance instruction"
""",
            )
            _write_text(
                custom_root / f"{fixture.skill_root.name}.user.toml",
                """[workflow]
headline = "user headline"
prepend_steps = ["user prepend"]
append_steps = ["user append"]

[[workflow.review_layers]]
id = "performance"
name = "User Performance"
instruction = ""

[[workflow.review_layers]]
id = "final"
name = "User Final"
instruction = "user final instruction"
""",
            )

            entry = self.assert_success(self.run_renderer(fixture))
            rendered = entry.read_text(encoding="utf-8")
            expected_scalars = (
                "Central winner: custom user",
                "Base only: base value",
                "User only: user value",
                "Team only: team value",
                "Final only: final value",
                f"Artifact root: {fixture.project_root}/artifacts",
                "Headline: user headline",
            )
            for expected in expected_scalars:
                self.assertIn(expected, rendered)
            self.assertIn(
                "Prepend:\n- default prepend\n- team prepend\n- user prepend",
                rendered,
            )
            self.assertIn(
                "Append:\n- default append\n- team append\n- user append",
                rendered,
            )
            self.assertIn("#### security (`security`)", rendered)
            self.assertIn("team security instruction", rendered)
            self.assertIn("#### Default Structure (`structure`)", rendered)
            self.assertIn("#### User Final (`final`)", rendered)
            self.assertNotIn("Default Security", rendered)
            self.assertNotIn("Run only when: always", rendered)
            self.assertNotIn("Performance", rendered)
            self.assertLess(rendered.index("(`security`)"), rendered.index("(`structure`)"))
            self.assertLess(rendered.index("(`structure`)"), rendered.index("(`final`)"))

            manifest = self.assert_manifest_integrity(
                fixture, entry, {"workflow.md", "guide.md"}
            )
            resolved = manifest["inputs"]["resolved_values"]
            self.assertEqual(
                ["default prepend", "team prepend", "user prepend"],
                resolved["customization.workflow.prepend_steps"],
            )
            review_layers = resolved["customization.workflow.review_layers"]
            self.assertEqual(
                ["security", "structure", "performance", "final"],
                [layer["id"] for layer in review_layers],
            )
            self.assertEqual(
                {
                    "id": "security",
                    "name": "security",
                    "instruction": "team security instruction",
                },
                review_layers[0],
            )

    def test_surviving_review_layer_renders_its_condition(self) -> None:
        defaults = """[workflow]
[[workflow.review_layers]]
id = "security"
name = "Security"
instruction = "Check authorization."
when = "authorization changes"
"""
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            fixture = self.make_fixture(
                Path(directory),
                workflow="Review:\n{workflow.review_layers}\n",
                customization=defaults,
            )
            entry = self.assert_success(self.run_renderer(fixture))
            self.assertEqual(
                "Review:\n#### Security (`security`)\n\n"
                "Run only when: authorization changes\n\nCheck authorization.\n",
                entry.read_text(encoding="utf-8"),
            )
            manifest = self.assert_manifest_integrity(
                fixture, entry, {"workflow.md", "guide.md"}
            )
            self.assertEqual(
                "authorization changes",
                manifest["inputs"]["resolved_values"][
                    "customization.workflow.review_layers"
                ][0]["when"],
            )

    def test_empty_open_spec_override_preserves_the_named_exception(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            fixture = self.make_fixture(
                Path(directory),
                workflow="Before\n{workflow.open_spec}\nAfter\n",
                customization='[workflow]\nopen_spec = "Open the spec."\n',
            )
            original_entry = self.assert_success(self.run_renderer(fixture))
            original_bytes = _tree_bytes(original_entry.parent)
            self.assertEqual(
                "Before\nOpen the spec.\nAfter\n",
                original_entry.read_text(encoding="utf-8"),
            )
            _write_text(
                fixture.project_root / "_bmad" / "custom"
                / f"{fixture.skill_root.name}.user.toml",
                '[workflow]\nopen_spec = ""\n',
            )
            entry = self.assert_success(self.run_renderer(fixture))
            self.assertNotEqual(original_entry, entry)
            self.assertEqual("Before\n\nAfter\n", entry.read_text(encoding="utf-8"))
            manifest = self.assert_manifest_integrity(
                fixture, entry, {"workflow.md", "guide.md"}
            )
            self.assertEqual(
                "", manifest["inputs"]["resolved_values"]["customization.workflow.open_spec"]
            )
            self.assertEqual(original_bytes, _tree_bytes(original_entry.parent))

    def test_other_nonempty_string_defaults_reject_empty_overrides(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            fixture = self.make_fixture(
                Path(directory),
                workflow="{workflow.headline}\n",
                customization='[workflow]\nheadline = "Required headline"\n',
            )
            _write_text(
                fixture.project_root / "_bmad" / "custom"
                / f"{fixture.skill_root.name}.user.toml",
                '[workflow]\nheadline = ""\n',
            )
            self.assert_halt(
                self.run_renderer(fixture),
                "HALT: customization.workflow.headline must not be empty",
            )
            self.assertFalse((fixture.project_root / "_bmad" / "render").exists())

    def test_external_source_link_halts_without_publication(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            root = Path(directory)
            fixture = self.make_fixture(root)
            external = root / "external.md"
            _write_text(external, "External source.\n")
            source = fixture.skill_root / "guide.md"
            source.unlink()
            source.symlink_to(external)
            self.assert_halt(
                self.run_renderer(fixture),
                "HALT: render source escapes skill directory: guide.md",
            )
            self.assertEqual(b"External source.\n", external.read_bytes())
            self.assertTrue(source.is_symlink())
            self.assertFalse((fixture.project_root / "_bmad" / "render").exists())

    def test_internal_source_link_remains_supported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            fixture = self.make_fixture(Path(directory))
            alias = fixture.skill_root / "alias.md"
            alias.symlink_to("guide.md")
            entry = self.assert_success(self.run_renderer(fixture))
            self.assertEqual(
                b"Fixture guide.\n", (entry.parent / "alias.md").read_bytes()
            )
            self.assertFalse((entry.parent / "alias.md").is_symlink())
            self.assert_manifest_integrity(
                fixture, entry, {"workflow.md", "guide.md", "alias.md"}
            )

    def test_inserted_tokens_are_opaque_and_source_snapshots_bind_to_generation(self) -> None:
        opaque = (
            "config={{config.fixture.value}}; short={{.value}}; "
            "workflow={workflow.other}; runtime={project-root}; "
            "snapshot=[[bmad-snapshot:missing.md]]; skill={skill-root}/guide.md"
        )
        workflow = """Opaque: {workflow.opaque}
Source config: {{config.fixture.value}}
Source snapshot: [[bmad-snapshot:guide.md]]
"""
        customization = f'[workflow]\nopaque = "{opaque}"\n'
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            fixture = self.make_fixture(
                Path(directory), workflow=workflow, customization=customization
            )
            nested_source = fixture.skill_root / "nested" / "details.md"
            nested_target = fixture.skill_root / "nested" / "target.md"
            _write_text(
                nested_source,
                """Nested opaque: {workflow.opaque}
Nested config: {{config.fixture.value}}
Nested snapshot: [[bmad-snapshot:nested/target.md]]
""",
            )
            _write_text(nested_target, "Nested target.\n")
            entry = self.assert_success(self.run_renderer(fixture))
            destination = entry.parent
            expected = (
                f"Opaque: {opaque.replace('{skill-root}', str(destination))}\n"
                "Source config: base\n"
                f"Source snapshot: {destination / 'guide.md'}\n"
            )
            self.assertEqual(expected, entry.read_text(encoding="utf-8"))
            expected_nested = (
                f"Nested opaque: {opaque.replace('{skill-root}', str(destination))}\n"
                "Nested config: base\n"
                f"Nested snapshot: {destination / 'nested' / 'target.md'}\n"
            )
            self.assertEqual(
                expected_nested,
                (destination / "nested" / "details.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "Nested target.\n",
                (destination / "nested" / "target.md").read_text(encoding="utf-8"),
            )
            self.assert_manifest_integrity(
                fixture,
                entry,
                {
                    "workflow.md",
                    "guide.md",
                    "nested/details.md",
                    "nested/target.md",
                },
            )

    def test_identical_render_reuses_bytes_and_changed_input_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            fixture = self.make_fixture(
                Path(directory), workflow="Value: {{config.fixture.value}}\n"
            )
            first_entry = self.assert_success(self.run_renderer(fixture))
            first_destination = first_entry.parent
            first_tree = _tree_bytes(first_destination)
            sentinel = 1_600_000_000_000_000_000
            for path in first_destination.rglob("*"):
                if path.is_file():
                    os.utime(path, ns=(sentinel, sentinel))
            preserved_mtimes = {
                path.relative_to(first_destination).as_posix(): path.stat().st_mtime_ns
                for path in first_destination.rglob("*")
                if path.is_file()
            }

            second_entry = self.assert_success(self.run_renderer(fixture))
            self.assertEqual(first_entry, second_entry)
            self.assertEqual(
                preserved_mtimes,
                {
                    path.relative_to(first_destination).as_posix(): path.stat().st_mtime_ns
                    for path in first_destination.rglob("*")
                    if path.is_file()
                },
            )
            self.assertEqual(first_tree, _tree_bytes(first_destination))

            _write_text(
                fixture.project_root / "_bmad" / "config.user.toml",
                '[fixture]\nvalue = "changed"\n',
            )
            third_entry = self.assert_success(self.run_renderer(fixture))
            self.assertNotEqual(first_entry, third_entry)
            self.assertEqual("Value: changed\n", third_entry.read_text(encoding="utf-8"))
            self.assertEqual(first_tree, _tree_bytes(first_destination))
            generations = {
                path.parent
                for path in (fixture.project_root / "_bmad" / "render").rglob(
                    "manifest.json"
                )
            }
            self.assertEqual({first_destination, third_entry.parent}, generations)

    def test_rename_failure_removes_populated_staging_and_destination(self) -> None:
        renderer = _load_renderer_module()
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            parent = Path(directory) / "publication with spaces"
            destination = parent / "generation"
            outputs = {"nested/workflow.md": b"fixture output\n"}
            manifest = {
                "outputs": {"nested/workflow.md": _sha256(outputs["nested/workflow.md"])}
            }

            def fail_rename(source: str, target: str, **kwargs) -> None:
                staging = parent / source
                self.assertEqual(destination.name, target)
                self.assertEqual(kwargs["src_dir_fd"], kwargs["dst_dir_fd"])
                self.assertEqual(
                    outputs["nested/workflow.md"],
                    (staging / "nested" / "workflow.md").read_bytes(),
                )
                self.assertTrue((staging / "manifest.json").is_file())
                raise OSError("forced rename failure")

            with mock.patch.object(renderer.os, "rename", side_effect=fail_rename):
                with self.assertRaisesRegex(OSError, "forced rename failure"):
                    renderer._publish(destination, outputs, manifest, trusted_root=Path(directory))

            self.assertFalse(destination.exists())
            self.assertEqual([], list(parent.glob(".staging-*")))

    def test_rename_collision_with_dangling_link_halts_and_cleans_staging(self) -> None:
        renderer = _load_renderer_module()
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            parent = Path(directory) / "publication with spaces"
            destination = parent / "generation"
            missing = parent / "missing generation"
            outputs = {"workflow.md": b"fixture output\n"}
            manifest = {"outputs": {"workflow.md": _sha256(outputs["workflow.md"])}}

            def competing_link(source: str, target: str, **kwargs) -> None:
                self.assertEqual(destination.name, target)
                self.assertEqual(kwargs["src_dir_fd"], kwargs["dst_dir_fd"])
                self.assertTrue((parent / source / "manifest.json").is_file())
                destination.symlink_to(missing, target_is_directory=True)
                raise OSError("competing publisher installed a dangling link")

            with mock.patch.object(renderer.os, "rename", side_effect=competing_link):
                with self.assertRaisesRegex(
                    renderer.RenderError, "generation is not an unlinked directory:"
                ):
                    renderer._publish(destination, outputs, manifest, trusted_root=Path(directory))

            self.assertTrue(destination.is_symlink())
            self.assertEqual(missing, destination.readlink())
            self.assertFalse(missing.exists())
            self.assertEqual([], list(parent.glob(".staging-*")))

    def test_render_ancestors_refuse_links_for_reuse_and_new_publication(self) -> None:
        for ancestor in ("_bmad", "render", "skill", "workspace"):
            for new_generation in (False, True):
                with self.subTest(ancestor=ancestor, new=new_generation), tempfile.TemporaryDirectory() as temporary:
                    fixture = self.make_fixture(Path(temporary), workflow="Value: {{config.fixture.value}}\n")
                    entry = self.assert_success(self.run_renderer(fixture))
                    selected = {"_bmad": fixture.project_root / "_bmad",
                                "render": fixture.project_root / "_bmad/render",
                                "skill": entry.parent.parent.parent,
                                "workspace": entry.parent.parent}[ancestor]
                    outside = Path(temporary) / "outside"
                    selected.rename(outside)
                    selected.symlink_to(outside, target_is_directory=True)
                    if new_generation:
                        _write_text(fixture.project_root / "_bmad/config.user.toml", '[fixture]\nvalue = "changed"\n')
                    before = _tree_bytes(outside)
                    self.assert_halt(self.run_renderer(fixture), "HALT: render ancestor is not an unlinked directory:")
                    self.assertEqual(before, _tree_bytes(outside))
                    self.assertTrue(selected.is_symlink())

    def test_concurrent_snapshot_links_are_rejected_without_reading_external_files(self) -> None:
        for selected in ("guide.md", "manifest.json", "nested", "details.md"):
            with self.subTest(selected=selected), tempfile.TemporaryDirectory() as temporary:
                fixture = self.make_fixture(Path(temporary))
                _write_text(fixture.skill_root / "nested/details.md", "Nested.\n")
                entry = self.assert_success(self.run_renderer(fixture))
                renderer = _load_renderer_module()
                relative = "nested/details.md" if selected == "details.md" else selected
                target = entry.parent / relative
                outside = Path(temporary) / "outside"
                real_open = os.open
                swapped = False

                def substitute(name, flags, *args, **kwargs):
                    nonlocal swapped
                    if name == selected and kwargs.get("dir_fd") is not None and not swapped:
                        swapped = True
                        directory = target.is_dir()
                        target.rename(outside)
                        target.symlink_to(outside, target_is_directory=directory)
                    return real_open(name, flags, *args, **kwargs)

                expected = _tree_bytes(target) if target.is_dir() else target.read_bytes()
                with mock.patch.object(renderer.os, "open", side_effect=substitute):
                    with self.assertRaises((renderer.RenderError, OSError)):
                        renderer.render(fixture.project_root, fixture.skill_root)
                self.assertTrue(swapped)
                self.assertTrue(target.is_symlink())
                self.assertEqual(expected, _tree_bytes(outside) if outside.is_dir() else outside.read_bytes())

    def test_substitution_after_an_output_read_is_still_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(Path(temporary))
            entry = self.assert_success(self.run_renderer(fixture))
            renderer = _load_renderer_module()
            target = entry.parent / "guide.md"
            outside = Path(temporary) / "outside"
            original = target.read_bytes()
            real_open = os.open
            swapped = False

            def substitute(name, flags, *args, **kwargs):
                nonlocal swapped
                if name == "manifest.json" and kwargs.get("dir_fd") is not None and not swapped:
                    swapped = True
                    target.rename(outside)
                    target.symlink_to(outside)
                return real_open(name, flags, *args, **kwargs)

            real_listdir = os.listdir
            def manifest_last(directory):
                return sorted(real_listdir(directory), key=lambda name: (name == "manifest.json", name))

            with (mock.patch.object(renderer.os, "open", side_effect=substitute),
                  mock.patch.object(renderer.os, "listdir", side_effect=manifest_last)):
                with self.assertRaisesRegex(renderer.RenderError, "generation changed during verification"):
                    renderer.render(fixture.project_root, fixture.skill_root)
            self.assertTrue(swapped)
            self.assertEqual(original, outside.read_bytes())

    def test_unsupported_descriptor_platform_halts_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(Path(temporary))
            renderer = _load_renderer_module()
            with mock.patch.object(renderer, "_DESCRIPTOR_IO", False):
                with self.assertRaisesRegex(renderer.RenderError, "requires no-follow directory descriptor support"):
                    renderer.render(fixture.project_root, fixture.skill_root)
            self.assertFalse((fixture.project_root / "_bmad/render").exists())

    def test_staging_name_swap_cannot_publish_a_link(self) -> None:
        renderer = _load_renderer_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "renders/generation"
            outside = root / "outside"
            _write_text(outside / "sentinel", "External.\n")
            before = _tree_bytes(outside)
            outputs = {"workflow.md": b"Fixture.\n"}
            manifest = {"outputs": {"workflow.md": _sha256(outputs["workflow.md"])}}
            real_rename = os.rename

            def substitute(source, target, **kwargs):
                real_rename(source, "displaced", **kwargs)
                os.symlink(str(outside), source, dir_fd=kwargs["src_dir_fd"], target_is_directory=True)
                return real_rename(source, target, **kwargs)

            with mock.patch.object(renderer.os, "rename", side_effect=substitute):
                with self.assertRaisesRegex(renderer.RenderError, "published generation differs"):
                    renderer._publish(destination, outputs, manifest, trusted_root=root)
            self.assertTrue(destination.is_symlink())
            self.assertEqual(before, _tree_bytes(outside))
            self.assertEqual(outputs["workflow.md"], (destination.parent / "displaced/workflow.md").read_bytes())

    def test_staging_output_substitution_is_verified_before_publication(self) -> None:
        renderer = _load_renderer_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "renders/generation"
            outside = root / "outside.md"
            outside.write_bytes(b"Fixture.\n")
            outputs = {"workflow.md": outside.read_bytes()}
            manifest = {"outputs": {"workflow.md": _sha256(outputs["workflow.md"])}}
            real_open = os.open
            substituted = False

            def substitute(name, flags, *args, **kwargs):
                nonlocal substituted
                if name == "manifest.json" and flags & os.O_CREAT:
                    substituted = True
                    os.unlink("workflow.md", dir_fd=kwargs["dir_fd"])
                    os.symlink(str(outside), "workflow.md", dir_fd=kwargs["dir_fd"])
                return real_open(name, flags, *args, **kwargs)

            with mock.patch.object(renderer.os, "open", side_effect=substitute):
                with self.assertRaisesRegex(renderer.RenderError, "linked or nonregular entry"):
                    renderer._publish(destination, outputs, manifest, trusted_root=root)
            self.assertTrue(substituted)
            self.assertFalse(destination.exists())
            self.assertEqual(b"Fixture.\n", outside.read_bytes())
            self.assertEqual([], list(destination.parent.glob(".staging-*")))

    def test_cleanup_preserves_foreign_trees_at_vacated_or_replaced_staging_names(self) -> None:
        for replaced in (False, True):
            with self.subTest(replaced=replaced), tempfile.TemporaryDirectory() as temporary:
                renderer = _load_renderer_module()
                root = Path(temporary)
                destination = root / "renders/generation"
                foreign = root / "foreign"
                _write_text(foreign / "sentinel", "Foreign bytes.\n")
                outputs = {"workflow.md": b"Fixture.\n"}
                manifest = {"outputs": {"workflow.md": _sha256(outputs["workflow.md"])}}
                real_rename = os.rename
                occupied = None

                def substitute(source, target, **kwargs):
                    nonlocal occupied
                    occupied = destination.parent / source
                    if replaced:
                        real_rename(source, "displaced", **kwargs)
                    else:
                        real_rename(source, target, **kwargs)
                    real_rename(foreign, occupied)
                    if replaced:
                        raise OSError("injected renamed staging failure")

                with mock.patch.object(renderer.os, "rename", side_effect=substitute):
                    if replaced:
                        with self.assertRaisesRegex(OSError, "injected renamed staging failure"):
                            renderer._publish(destination, outputs, manifest, trusted_root=root)
                    else:
                        renderer._publish(destination, outputs, manifest, trusted_root=root)
                self.assertIsNotNone(occupied)
                self.assertEqual({"sentinel": b"Foreign bytes.\n"}, _tree_bytes(occupied))
                self.assertEqual(not replaced, destination.exists())

    def test_cleanup_name_substitution_cannot_redirect_recursive_deletion(self) -> None:
        renderer = _load_renderer_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "renders/generation"
            foreign = root / "foreign"
            _write_text(foreign / "nested/sentinel", "Foreign bytes.\n")
            outputs = {"nested/workflow.md": b"Fixture.\n"}
            manifest = {"outputs": {"nested/workflow.md": _sha256(outputs["nested/workflow.md"])}}
            real_rename = os.rename
            real_clear = renderer._clear_owned_directory
            replaced = False
            occupied = None
            displaced = destination.parent / "displaced"

            def substitute(directory):
                nonlocal replaced, occupied
                if not replaced:
                    replaced = True
                    occupied = next(destination.parent.glob(".staging-*"))
                    real_rename(occupied, displaced)
                    real_rename(foreign, occupied)
                    self.assertEqual(displaced.stat().st_ino, os.fstat(directory).st_ino)
                return real_clear(directory)

            with (mock.patch.object(renderer.os, "rename", side_effect=OSError("injected publication failure")),
                  mock.patch.object(renderer, "_clear_owned_directory", side_effect=substitute),
                  mock.patch.object(shutil, "rmtree", side_effect=AssertionError("pathname cleanup is forbidden"))):
                with self.assertRaisesRegex(OSError, "injected publication failure"):
                    renderer._publish(destination, outputs, manifest, trusted_root=root)
            self.assertTrue(replaced)
            self.assertEqual({"nested/sentinel": b"Foreign bytes.\n"}, _tree_bytes(occupied))
            self.assertEqual({}, _tree_bytes(displaced))
            self.assertFalse(destination.exists())

    def test_reuse_rechecks_identity_after_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(Path(temporary))
            entry = self.assert_success(self.run_renderer(fixture))
            renderer = _load_renderer_module()
            manifest = json.loads((entry.parent / "manifest.json").read_text())
            target = entry.parent / "guide.md"
            outside = Path(temporary) / "outside"
            original = target.read_bytes()
            real_hash = renderer._hash_bytes
            substituted = False

            def substitute(content):
                nonlocal substituted
                if content == original and not substituted:
                    substituted = True
                    target.rename(outside)
                    target.symlink_to(outside)
                return real_hash(content)

            parent = os.open(entry.parent.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with mock.patch.object(renderer, "_hash_bytes", side_effect=substitute):
                    with self.assertRaisesRegex(renderer.RenderError, "generation changed during verification"):
                        renderer._verify_existing(entry.parent, manifest, parent)
            finally:
                os.close(parent)
            self.assertTrue(substituted)
            self.assertEqual(original, outside.read_bytes())

    def test_ancestor_movement_during_open_halts_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(Path(temporary), workflow="Value: {{config.fixture.value}}\n")
            entry = self.assert_success(self.run_renderer(fixture))
            _write_text(fixture.project_root / "_bmad/config.user.toml", '[fixture]\nvalue = "changed"\n')
            renderer = _load_renderer_module()
            ancestor = entry.parent.parent
            outside = Path(temporary) / "outside"
            before = _tree_bytes(ancestor)
            real_open = os.open
            substituted = False

            def substitute(name, flags, *args, **kwargs):
                nonlocal substituted
                descriptor = real_open(name, flags, *args, **kwargs)
                if name == ancestor.name and not substituted:
                    substituted = True
                    ancestor.rename(outside)
                    ancestor.symlink_to(outside, target_is_directory=True)
                return descriptor

            with mock.patch.object(renderer.os, "open", side_effect=substitute):
                with self.assertRaisesRegex(renderer.RenderError, "directory changed during rendering"):
                    renderer.render(fixture.project_root, fixture.skill_root)
            self.assertTrue(substituted)
            self.assertEqual(before, _tree_bytes(outside))

    @unittest.skipUnless(os.name == "posix", "POSIX descriptor-limit fixture")
    def test_many_outputs_publish_and_reuse_under_a_reduced_descriptor_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self.make_fixture(Path(temporary))
            for index in range(70):
                _write_text(fixture.skill_root / f"section-{index}/details.md", f"Section {index}.\n")
            arguments = [str(RENDERER_PATH), "--project-root", str(fixture.project_root), "--skill", str(fixture.skill_root)]
            code = ("import resource, runpy, sys; resource.setrlimit(resource.RLIMIT_NOFILE, (48, 48)); "
                    + "sys.path.insert(0, " + repr(str(RENDERER_PATH.parent)) + "); sys.argv = "
                    + repr(arguments) + "; runpy.run_path(sys.argv[0], run_name='__main__')")
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            entries = []
            for _ in range(2):
                completed = subprocess.run([sys.executable, "-c", code], env=environment,
                                           capture_output=True, text=True, timeout=30)
                entries.append(self.assert_success(completed))
            self.assertEqual(entries[0], entries[1])

    def test_invalid_inputs_halt_and_publish_nothing(self) -> None:
        valid_customization = '[workflow]\nmessage = "configured"\n'
        duplicate_reviews = """[workflow]
[[workflow.review_layers]]
id = "duplicate"
instruction = "first"
[[workflow.review_layers]]
id = "duplicate"
instruction = "second"
"""
        cases = (
            ("missing workflow", "Fixture.\n", None, "missing-workflow"),
            ("malformed source", "Fixture.\n", None, "malformed-source"),
            ("missing central config", "Fixture.\n", None, "missing-central"),
            ("malformed central config", "Fixture.\n", None, "malformed-central"),
            (
                "missing customization",
                "Configured: {workflow.message}\n",
                valid_customization,
                "missing-customization",
            ),
            (
                "malformed customization",
                "Configured: {workflow.message}\n",
                valid_customization,
                "malformed-customization",
            ),
            (
                "invalid review layers",
                "{workflow.review_layers}\n",
                duplicate_reviews,
                "invalid-reviews",
            ),
            (
                "undeclared snapshot",
                "[[bmad-snapshot:missing.md]]\n",
                None,
                "undeclared-snapshot",
            ),
        )
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            root = Path(directory)
            for index, (name, workflow, customization, mutation) in enumerate(cases):
                with self.subTest(name=name):
                    fixture = self.make_fixture(
                        root / f"case {index} with spaces",
                        workflow=workflow,
                        customization=customization,
                    )
                    central_path = fixture.project_root / "_bmad" / "config.toml"
                    customization_path = fixture.skill_root / "customize.toml"
                    workflow_path = fixture.skill_root / "workflow.md"
                    if mutation == "missing-workflow":
                        workflow_path.unlink()
                        expected = f"HALT: render entry is missing: {workflow_path}"
                    elif mutation == "malformed-source":
                        workflow_path.write_bytes(b"\xff")
                        expected = f"HALT: failed to read render source {workflow_path}:"
                    elif mutation == "missing-central":
                        central_path.unlink()
                        expected = f"HALT: required TOML file not found: {central_path}"
                    elif mutation == "malformed-central":
                        central_path.write_text("[invalid", encoding="utf-8")
                        expected = f"HALT: failed to parse {central_path}:"
                    elif mutation == "missing-customization":
                        customization_path.unlink()
                        expected = f"HALT: required TOML file not found: {customization_path}"
                    elif mutation == "malformed-customization":
                        customization_path.write_text("[invalid", encoding="utf-8")
                        expected = f"HALT: failed to parse {customization_path}:"
                    elif mutation == "invalid-reviews":
                        expected = "HALT: duplicate review layer id `duplicate`"
                    else:
                        expected = "HALT: snapshot reference targets undeclared source: missing.md"

                    self.assert_halt(self.run_renderer(fixture), expected)
                    render_root = fixture.project_root / "_bmad" / "render"
                    self.assertEqual(
                        [], list(render_root.rglob("*")) if render_root.exists() else []
                    )

    def test_missing_bmad_directory_halts_before_publishing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            fixture = self.make_fixture(Path(directory))
            shutil.rmtree(fixture.project_root / "_bmad")
            expected = f"HALT: project root does not contain _bmad/: {fixture.project_root}"
            self.assert_halt(self.run_renderer(fixture), expected)
            self.assertFalse((fixture.project_root / "_bmad").exists())

    def test_corrupt_existing_generations_halt_without_repair(self) -> None:
        def corrupt_manifest(destination: Path) -> str:
            (destination / "manifest.json").write_text("{", encoding="utf-8")
            return "HALT: corrupt existing generation"

        def collide_manifest(destination: Path) -> str:
            path = destination / "manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["skill"] = "colliding-skill"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            return "HALT: generation collision or corruption at"

        def damage_output(destination: Path) -> str:
            (destination / "workflow.md").write_text("damaged\n", encoding="utf-8")
            return "HALT: generation output hash mismatch:"

        def remove_output(destination: Path) -> str:
            (destination / "guide.md").unlink()
            return "HALT: generation contains unexpected or missing files:"

        def add_output(destination: Path) -> str:
            (destination / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
            return "HALT: generation contains unexpected or missing files:"

        cases = (
            ("manifest syntax", corrupt_manifest),
            ("manifest collision", collide_manifest),
            ("output hash", damage_output),
            ("missing file", remove_output),
            ("unexpected file", add_output),
        )
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            root = Path(directory)
            for index, (name, corrupt) in enumerate(cases):
                with self.subTest(name=name):
                    fixture = self.make_fixture(root / f"case {index} with spaces")
                    entry = self.assert_success(self.run_renderer(fixture))
                    destination = entry.parent
                    expected = corrupt(destination)
                    damaged_evidence = _tree_bytes(destination)

                    self.assert_halt(self.run_renderer(fixture), expected)
                    self.assertEqual(damaged_evidence, _tree_bytes(destination))
                    self.assertEqual([], list(destination.parent.glob(".staging-*")))

    def test_linked_generations_halt_without_changing_links_or_targets(self) -> None:
        cases = (
            "workflow.md", "manifest.json", "nested/details.md", "nested",
            "generation", "dangling-generation", "unexpected-link",
        )
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            root = Path(directory)
            for index, case in enumerate(cases):
                with self.subTest(case=case):
                    case_root = root / f"case {index}"
                    fixture = self.make_fixture(case_root)
                    _write_text(fixture.skill_root / "nested" / "details.md", "Nested.\n")
                    entry = self.assert_success(self.run_renderer(fixture))
                    destination = entry.parent
                    external = case_root / "external target"
                    if case in ("generation", "dangling-generation"):
                        link = destination
                        link.rename(external)
                        target = (
                            case_root / "missing generation"
                            if case == "dangling-generation" else external
                        )
                        link.symlink_to(target, target_is_directory=True)
                        expected = "HALT: generation is not an unlinked directory:"
                    elif case == "unexpected-link":
                        link = destination / "unexpected.md"
                        target = case_root / "missing file"
                        _write_text(external, "External sentinel.\n")
                        link.symlink_to(target)
                        expected = "HALT: generation contains linked or nonregular entry:"
                    else:
                        link = destination / case
                        is_directory = link.is_dir()
                        link.rename(external)
                        target = external
                        link.symlink_to(target, target_is_directory=is_directory)
                        expected = "HALT: generation contains linked or nonregular entry:"
                    external_before = (
                        _tree_bytes(external) if external.is_dir() else external.read_bytes()
                    )

                    self.assert_halt(self.run_renderer(fixture), expected)

                    self.assertTrue(link.is_symlink())
                    self.assertEqual(target, link.readlink())
                    self.assertEqual(
                        external_before,
                        _tree_bytes(external) if external.is_dir() else external.read_bytes(),
                    )
                    if case in ("dangling-generation", "unexpected-link"):
                        self.assertFalse(target.exists())
                    self.assertEqual([], list(destination.parent.glob(".staging-*")))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO fixture")
    def test_nonregular_entries_halt_before_manifest_or_output_reads(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render skill fixtures ") as directory:
            for name in ("guide.md", "manifest.json"):
                with self.subTest(name=name):
                    fixture = self.make_fixture(Path(directory) / name)
                    entry = self.assert_success(self.run_renderer(fixture))
                    fifo = entry.parent / name
                    fifo.unlink()
                    os.mkfifo(fifo)
                    before = fifo.lstat()
                    self.assert_halt(
                        self.run_renderer(fixture),
                        "HALT: generation contains linked or nonregular entry:",
                    )
                    self.assertEqual(before, fifo.lstat())
                    self.assertEqual([], list(entry.parent.parent.glob(".staging-*")))



if __name__ == "__main__":
    unittest.main()
