"""Active inputs stay outside historical evidence and mutable live registries."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import repository_inputs as inputs


class RepositoryInputsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="repository-inputs-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)

    def tracked(self, relative, body):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body if isinstance(body, bytes) else body.encode())
        subprocess.run(["git", "-C", str(self.root), "add", "--", relative], check=True)
        return path

    def evidence_failures(self):
        return inputs.evidence_dependencies(self.root, inputs.tracked_paths(self.root))

    def suite(self, body, relative="tools/tests/test_candidate.py"):
        self.tracked(relative, "from pathlib import Path\nROOT = Path(__file__).resolve().parents[2]\n" + body)
        return inputs.registry_dependencies(self.root, inputs.tracked_paths(self.root))

    def test_tracked_active_repository_inputs_have_no_evidence_dependency(self):
        failures = inputs.evidence_dependencies(ROOT, inputs.tracked_paths(ROOT))
        self.assertEqual([], failures, "\n".join(failures))

    def test_tracked_suites_do_not_read_the_real_setup_or_rendered_registry(self):
        failures = inputs.registry_dependencies(ROOT, inputs.tracked_paths(ROOT))
        self.assertEqual([], failures, "\n".join(failures))

    def test_tracked_unlisted_suites_do_not_read_the_builds_pin(self):
        failures = inputs.pin_dependencies(ROOT, inputs.tracked_paths(ROOT))
        self.assertEqual([], failures, "\n".join(failures))

    def test_pin_boundary_reports_direct_and_shared_helper_reads_per_suite(self):
        helper = "tools/tests/read_pin.py"
        self.tracked(helper, "from pathlib import Path\n"
                     "ROOT = Path(__file__).resolve().parents[2]\n"
                     "PIN = (ROOT / 'builds-version').read_text()\n"
                     "def read(root):\n"
                     "    return (root / 'builds-version').read_bytes()\n")
        first, second = "tools/tests/test_candidate.py", "tools/tests/test_other.py"
        self.suite("from read_pin import read\nread(ROOT)\nopen('builds-version')\n", first)
        self.suite("import read_pin\n", second)
        self.assertEqual([
            f"{helper}:3: {first} reads repository-root builds-version",
            f"{helper}:3: {second} reads repository-root builds-version",
            f"{helper}:5: {first} reads repository-root builds-version",
            f"{first}:5: {first} reads repository-root builds-version",
        ], inputs.pin_dependencies(self.root, inputs.tracked_paths(self.root)))

    def test_pin_boundary_allows_selected_suites_and_disposable_inputs(self):
        self.tracked("tools/read_pin.py", "def read(root):\n    return (root / 'builds-version').read_text()\n")
        self.suite("from read_pin import read\nread(ROOT / 'fixture')\n"
                   "open(ROOT / 'tools/tests/fixtures/builds-version')\n")
        self.suite("open(ROOT / 'builds-version')\n", f"tools/tests/{inputs.PIN_SUITES[0]}")
        self.assertEqual([], inputs.pin_dependencies(self.root, inputs.tracked_paths(self.root)))

    def test_pin_boundary_tracks_subprocess_paths_and_git_revision_reads(self):
        helper = "tools/tests/read_pin_process.py"
        self.tracked(helper, "import subprocess\n"
                     "def git(root, *args):\n"
                     "    return subprocess.run(['git', '-C', str(root), *map(str, args)])\n")
        suite = "tools/tests/test_candidate.py"
        operations = (
            ("subprocess.run(['cat', 'builds-version'], cwd={root})", suite, 5),
            ("subprocess.run(['cat', Path('builds-version')], cwd={root})", suite, 5),
            ("subprocess.check_output(['git', 'show', 'HEAD:builds-version'], cwd={root})", suite, 5),
            ("subprocess.run(['git', '-C', str({root}), 'show', 'HEAD:builds-version'])", suite, 5),
            ("git({root}, 'show', 'HEAD:builds-version')", helper, 3),
        )
        for operation, source, line in operations:
            for root, expected in (("ROOT", [f"{source}:{line}: {suite} reads repository-root builds-version"]),
                                   ("ROOT / 'fixture'", [])):
                with self.subTest(operation=operation, root=root):
                    self.suite("import subprocess\nfrom read_pin_process import git\n" + operation.format(root=root) + "\n")
                    self.assertEqual(expected, inputs.pin_dependencies(self.root, inputs.tracked_paths(self.root)))
        self.suite("import subprocess\nsubprocess.run(['cat', 'builds-version'])\n")
        self.assertEqual([f"{suite}:4: {suite} reads repository-root builds-version"],
                         inputs.pin_dependencies(self.root, inputs.tracked_paths(self.root)))

    def test_pin_boundary_tracks_runpy_packages_and_imported_test_classes(self):
        suite = "tools/tests/test_candidate.py"
        fixtures = (
            ("tools/tests/read_pin_path.py", "import runpy\nrunpy.run_path(ROOT / 'tools/tests/read_pin_path.py')\n",
             "PIN = (ROOT / 'builds-version').read_text()\n", 3, 2),
            ("tools/tests/read_pin_package/__init__.py", "import read_pin_package\n",
             "PIN = (ROOT / 'builds-version').read_text()\n", 3, 3),
            ("tools/tests/read_pin_cases.py", "from read_pin_cases import TestPublication\n",
             "import unittest\nclass TestPublication(unittest.TestCase):\n"
             "    def setUp(self):\n        self.root = ROOT\n"
             "    def test_read(self):\n        (self.root / 'builds-version').read_text()\n", 8, 2),
        )
        for helper, body, contents, line, depth in fixtures:
            self.suite(body)
            for root, expected in (("checkout", [f"{helper}:{line}: {suite} reads repository-root builds-version"]),
                                   ("checkout / 'fixture'", [])):
                with self.subTest(helper=helper, root=root):
                    self.tracked(helper, "from pathlib import Path\n"
                                 f"checkout = Path(__file__).resolve().parents[{depth}]; ROOT = {root}\n"
                                 + contents)
                    self.assertEqual(expected, inputs.pin_dependencies(self.root, inputs.tracked_paths(self.root)))

    def test_pin_boundary_tracks_concrete_path_transforms_and_globs(self):
        suite = "tools/tests/test_candidate.py"
        reads = ("({root} / 'builds-version.txt').with_suffix('').read_text()",
                 "({root} / 'other').with_stem('builds-version').read_bytes()",
                 "list({root}.glob('builds-*'))",
                 "list({root}.rglob('builds-*'))")
        for read in reads:
            for root, expected in (("ROOT", [f"{suite}:3: {suite} reads repository-root builds-version"]),
                                   ("(ROOT / 'fixture')", [])):
                with self.subTest(read=read, root=root):
                    self.suite(read.format(root=root) + "\n")
                    self.assertEqual(expected, inputs.pin_dependencies(self.root, inputs.tracked_paths(self.root)))

    def test_executable_and_shared_data_mutations_fail_with_path_and_line(self):
        historical = inputs.EVIDENCE_ROOT + "/specs/spec-cicd/evidence/18/runner.py"
        for relative, body in (("tools/new_runner.py", f"source = {historical!r}\n"),
                               ("tools/fixture.json", '{"source": "' + historical + '"}\n'),
                               ("tools/receipt.txt", historical + "\n"),
                               ("tools/build.log", historical + "\n")):
            with self.subTest(relative=relative):
                self.tracked(relative, body)
                self.assertIn(relative + ":1: active input references evidence", self.evidence_failures())

    def test_all_historical_output_subdirectories_are_protected(self):
        self.tracked("tools/input.json", '{"path":"' + inputs.EVIDENCE_ROOT + '/implementation-artifacts/input.json"}')
        self.assertEqual(["tools/input.json:1: active input references evidence"], self.evidence_failures())

    def test_reconstructed_evidence_reads_in_production_tools_are_rejected(self):
        self.tracked("tools/reader.py", "from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n"
                     "(ROOT / ('_bmad-' + 'output') / 'input.json').read_text()\n")
        self.assertEqual(["tools/reader.py:3: active Python path reads evidence"], self.evidence_failures())
        self.tracked("tools/reader.py", "from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n"
                     "(ROOT / 'setup/Fixture.yml').read_text()\n")
        self.assertEqual([], self.evidence_failures())
        self.assertEqual([], inputs.registry_dependencies(self.root, inputs.tracked_paths(self.root)))

    def test_reconstructed_evidence_paths_are_rejected_at_load_execute_and_copy_sinks(self):
        marker = "ROOT / ('_bmad-' + 'output') / 'runner.py'"
        for call in (f"runpy.run_path(str({marker}))",
                     f"importlib.util.spec_from_file_location('runner', {marker})",
                     f"subprocess.run(['python3', str({marker})])",
                     f"shutil.copy({marker}, 'copy.py')"):
            with self.subTest(call=call):
                self.tracked("tools/runner_loader.py", "from pathlib import Path\nimport importlib.util, runpy, shutil, subprocess\n"
                             "ROOT = Path(__file__).resolve().parents[1]\n" + call + "\n")
                self.assertEqual(["tools/runner_loader.py:4: active Python path reads evidence"], self.evidence_failures())

    def test_prose_and_comments_are_not_active_path_reads(self):
        historical = inputs.EVIDENCE_ROOT + "/specs/spec-cicd/evidence/18/runner.py"
        self.tracked("docs/history.md", f"The former runner was `{historical}`.\n")
        self.tracked("tools/example.py", "# Former source: " + historical + "\nvalue = 1\n")
        self.tracked(inputs.EVIDENCE_ROOT + "/specs/spec-cicd/evidence/18/historical.py", historical)
        self.assertEqual([], self.evidence_failures())
        executable = self.tracked("tools/disguised.md", "#!/bin/sh\npython3 " + historical + "\n")
        executable.chmod(0o755)
        self.assertEqual(["tools/disguised.md:2: active input references evidence"], self.evidence_failures())

    def test_provenance_exception_is_exact_path_and_immutable_bytes(self):
        relative = "docs/contracts-prerequisites/approval.json"
        original = (ROOT / relative).read_bytes()
        self.assertEqual(inputs.PROVENANCE[relative], hashlib.sha256(original).hexdigest())
        path = self.tracked(relative, original)
        self.assertEqual([], self.evidence_failures())
        path.write_bytes(original + b"\n")
        self.assertEqual([relative + ":1: historical provenance identity changed"], self.evidence_failures())
        path.write_bytes(original)
        self.tracked("docs/contracts-prerequisites/copied.json", original)
        self.assertTrue(any(value.startswith("docs/contracts-prerequisites/copied.json:") for value in self.evidence_failures()))

    def test_exact_prose_classes_do_not_exempt_shared_markdown_fixtures(self):
        historical = inputs.EVIDENCE_ROOT + '/fixture.json'
        for relative in ('README.md', 'AGENTS.md', 'setup/README.md', 'docs/history.md',
                         '_bmad/core/config.yaml', '.agents/skills/example/SKILL.md'):
            self.tracked(relative, historical)
        self.assertEqual([], self.evidence_failures())
        for relative in ('tools/fixture.md', 'docs/proposals/fixture.md',
                         'docs/contracts-prerequisites/fixture.md', 'docs/nested/fixture.rst'):
            self.tracked(relative, '# source: ' + historical)
            self.assertIn(relative + ':1: active input references evidence', self.evidence_failures())

    def test_direct_and_aliased_root_reads_are_rejected(self):
        for directory in ("setup", "rendered"):
            with self.subTest(directory=directory):
                failures = self.suite(f"alias = ROOT\nregistry = alias / {directory!r}\n(registry / 'Fixture.yml').read_bytes()\n")
                self.assertEqual([f"tools/tests/test_candidate.py:5: suite reads repository-root {directory}/"], failures)

    def test_relative_reads_resolve_from_the_suite_working_directory(self):
        for body in ("open('setup/Fixture.yml')\n", "Path('rendered/Fixture.json').read_text()\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)
        self.assertEqual([], self.suite("open('tools/tests/fixtures/Fixture.yml')\n"))

    def test_path_constructor_folds_every_component(self):
        self.assertEqual(["tools/tests/test_candidate.py:3: suite reads repository-root setup/"],
                         self.suite("Path(ROOT, 'setup', 'Fixture.yml').read_text()\n"))

    def test_standard_library_path_and_reader_aliases_keep_callable_identity(self):
        for body in ("import pathlib as paths\npaths.Path(ROOT, 'setup/Fixture.yml').read_text()\n",
                     "from pathlib import Path as P\nP(ROOT, 'setup/Fixture.yml').read_text()\n",
                     "import io as streams\nstreams.open(ROOT / 'rendered/Fixture.json')\n",
                     "from io import open as read\nread(ROOT / 'setup/Fixture.yml')\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)

    def test_conditional_bindings_reach_subsequent_reads(self):
        for body in ("if condition:\n    registry = ROOT / 'setup'\nregistry.read_text()\n",
                     "if condition:\n    registry = ROOT / 'tools'\nelse:\n    registry = ROOT / 'rendered'\nregistry.read_text()\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)

    def test_unittest_setup_instance_and_class_paths_reach_test_reads(self):
        for body in ("class Suite:\n    def setUp(self):\n        self.root = ROOT\n        self.registry = self.root / 'setup'\n"
                     "    def test_read(self):\n        self.registry.read_text()\n",
                     "class Suite:\n    @classmethod\n    def setUpClass(cls):\n        cls.registry = ROOT / 'rendered'\n"
                     "    def test_read(self):\n        self.registry.read_text()\n",
                     "class Suite:\n    registry = ROOT / 'setup'\n    def test_read(self):\n        self.registry.read_text()\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)

    def test_unpacked_and_dictionary_paths_keep_their_identity(self):
        for body in ("registry, other = ROOT / 'setup', ROOT / 'tools'\nregistry.read_text()\n",
                     "paths = {'registry': ROOT / 'rendered', 'other': ROOT / 'tools'}\npaths['registry'].read_bytes()\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)

    def test_comprehensions_bind_their_generators_before_reads(self):
        for body in ("[path.read_text() for path in [ROOT / 'setup/Fixture.yml']]\n",
                     "{name: path.read_bytes() for name, path in [('registry', ROOT / 'rendered/Fixture.json')]}\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)

    def test_glob_patterns_are_checked_and_their_returned_paths_are_preserved(self):
        failures = self.suite("paths = ROOT.glob('setup/*.yml')\nfor path in paths:\n    path.read_text()\n")
        self.assertEqual(["tools/tests/test_candidate.py:3: suite reads repository-root setup/",
                          "tools/tests/test_candidate.py:5: suite reads repository-root setup/"], failures)

    def test_positional_only_helper_parameters_keep_path_identity(self):
        self.assertTrue(self.suite("def read(root, /):\n    return (root / 'setup/Fixture.yml').read_text()\nread(ROOT)\n"))

    def test_helper_reads_and_returned_paths_keep_the_real_root_identity(self):
        for body in ("def read(root):\n    return (root / 'setup/Fixture.yml').read_text()\nread(ROOT)\n",
                     "def registry(root):\n    return root / 'rendered'\nalias = registry\nregistry_path = alias(ROOT)\nlist(registry_path.glob('*'))\n",
                     "class Suite:\n    def read(self, root):\n        return (root / 'setup/Fixture.yml').open()\n    def test_read(self):\n        self.read(ROOT)\n"):
            with self.subTest(body=body):
                failures = self.suite(body)
                self.assertTrue(failures, body)
                self.assertTrue(all("suite reads repository-root" in value for value in failures))

    def test_imported_helper_reads_and_path_builders_are_rejected(self):
        self.tracked("tools/reader.py", "def registry(root):\n    return root / 'setup'\ndef load(root):\n    return (registry(root) / 'Fixture.yml').read_bytes()\n")
        failures = self.suite("from reader import load as helper\nhelper(ROOT)\n")
        self.assertEqual(["tools/reader.py:4: suite reads repository-root setup/"], failures)
        self.tracked("tools/reader.py", "def safe_path(root, relative):\n    return root / relative\ndef load(root):\n    return safe_path(root, 'rendered').glob('*')\n")
        failures = self.suite("import reader as helper\nhelper.load(ROOT)\n")
        self.assertEqual(["tools/reader.py:4: suite reads repository-root rendered/"], failures)

    def test_dynamically_loaded_helper_is_followed(self):
        self.tracked("tools/reader.py", "def read(root):\n    return (root / 'setup/Fixture.yml').read_bytes()\n")
        failures = self.suite("reader = load_module('reader', ROOT / 'tools/reader.py')\nreader.read(ROOT)\n")
        self.assertEqual(["tools/reader.py:2: suite reads repository-root setup/"], failures)

    def test_imported_root_constants_and_os_path_helpers_keep_identity(self):
        self.tracked("tools/reader.py", "from pathlib import Path\nROOT = Path(__file__).resolve().parent.parent\n")
        failures = self.suite("from reader import ROOT as checkout\n(checkout / 'setup/Fixture.yml').read_bytes()\n")
        self.assertEqual(["tools/tests/test_candidate.py:4: suite reads repository-root setup/"], failures)
        failures = self.suite("import os\nregistry = os.path.join(str(ROOT), 'rendered', 'Fixture.json')\nopen(registry)\n")
        self.assertEqual(["tools/tests/test_candidate.py:5: suite reads repository-root rendered/"], failures)

    def test_relocated_and_nested_test_suites_cannot_bypass_the_boundary(self):
        for relative in ("tools/qualification/pre-adoption/module/test_runner.py", "tools/new/tests/helpers.py"):
            with self.subTest(relative=relative):
                depth = len(Path(relative).parts) - 1
                self.tracked(relative, "from pathlib import Path\n"
                             f"checkout = Path(__file__).resolve().parents[{depth}]\n"
                             "(checkout / 'setup/Fixture.yml').read_bytes()\n")
                failures = inputs.registry_dependencies(self.root, inputs.tracked_paths(self.root))
                self.assertIn(relative + ":3: suite reads repository-root setup/", failures)

    def test_nested_suite_local_helper_is_resolved_before_tools_helpers(self):
        relative = "tools/nested/tests/test_candidate.py"
        self.tracked("tools/nested/tests/reader.py", "def read(root):\n    return (root / 'rendered/Fixture.json').read_bytes()\n")
        self.tracked(relative, "from pathlib import Path\nfrom reader import read as helper\n"
                     "checkout = Path(__file__).resolve().parents[3]\nhelper(checkout)\n")
        failures = inputs.registry_dependencies(self.root, inputs.tracked_paths(self.root))
        self.assertEqual(["tools/nested/tests/reader.py:2: suite reads repository-root rendered/"], failures)

    def test_helper_default_parameters_do_not_hide_checkout_reads(self):
        for body in ("def registry(root=ROOT):\n    return (root / 'setup/Fixture.yml').read_text()\nregistry()\n",
                     "def registry(*, root=ROOT):\n    return (root / 'rendered/Fixture.json').read_bytes()\nregistry()\n"):
            with self.subTest(body=body):
                failures = self.suite(body)
                self.assertTrue(failures, body)

    def test_registry_copies_existence_checks_and_child_process_paths_are_rejected(self):
        for body in ("import shutil\nshutil.copytree(ROOT / 'rendered', 'workspace')\n",
                     "from shutil import copyfile\ncopyfile(ROOT / 'setup/Fixture.yml', 'Fixture.yml')\n",
                     "import os\nos.path.exists(ROOT / 'setup')\n",
                     "import subprocess, sys\nsubprocess.run([sys.executable, 'render.py', str(ROOT / 'setup')])\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)

    def test_unknown_and_path_components_keep_the_known_registry_prefix(self):
        for body in ("name = compute()\n(ROOT / 'setup' / name).read_text()\n",
                     "for name in names():\n    (ROOT / 'setup' / (name + '.yml')).read_text()\n",
                     "Path(ROOT, 'rendered', compute()).read_text()\n",
                     "(ROOT / Path('setup/Fixture.yml')).read_text()\n",
                     "(ROOT / 'setup' / 'Fixture').with_suffix('.yml').read_text()\n",
                     "open(file=ROOT / 'setup/Fixture.yml')\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)

    def test_nested_helpers_are_analyzed_and_callable(self):
        for body in ("def test_read():\n    def read():\n        return (ROOT / 'setup/Fixture.yml').read_text()\n    read()\n",
                     "def test_read():\n    def read(root):\n        return (root / 'rendered/Fixture.json').read_bytes()\n    read(ROOT)\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)

    def test_inherited_fixture_state_reaches_subclass_tests(self):
        for body in ("import unittest\nclass Base(unittest.TestCase):\n    def setUp(self):\n        self.registry = ROOT / 'setup'\n"
                     "class Suite(Base):\n    def test_read(self):\n        (self.registry / 'Fixture.yml').read_text()\n",
                     "class Base:\n    registry = ROOT / 'rendered'\nclass Suite(Base):\n    def test_read(self):\n        self.registry.read_text()\n"):
            with self.subTest(body=body):
                self.assertTrue(self.suite(body), body)

    def test_spec_loaded_helper_modules_are_followed(self):
        self.tracked("tools/tests/helper.py", "def read(root):\n    return (root / 'setup/Fixture.yml').read_bytes()\n")
        failures = self.suite("import importlib.util\nSPEC = importlib.util.spec_from_file_location('helper', Path(__file__).with_name('helper.py'))\n"
                              "HELPER = importlib.util.module_from_spec(SPEC)\nSPEC.loader.exec_module(HELPER)\nHELPER.read(ROOT)\n")
        self.assertEqual(["tools/tests/helper.py:2: suite reads repository-root setup/"], failures)

    def test_disposable_copies_child_processes_and_nested_helpers_remain_valid(self):
        disposable = self.root / "registry-fixture"
        failures = self.suite("import shutil, subprocess\nfixture = Path(" + repr(str(disposable)) + ")\n"
                              "shutil.copytree(fixture / 'setup', fixture / 'copy')\n"
                              "subprocess.run(['git', 'ls-files', 'setup', 'rendered'], cwd=fixture)\n"
                              "def test_read():\n    def read(root):\n        return (root / 'setup/Fixture.yml').read_text()\n    read(fixture)\n")
        self.assertEqual([], failures)

    def test_disposable_registry_reads_and_nonregistry_checkout_inputs_remain_valid(self):
        self.tracked("tools/reader.py", "def read(root):\n    return (root / 'setup/Fixture.yml').read_bytes()\n")
        disposable = self.root / "registry-fixture"
        failures = self.suite("import reader\nfixture = Path(" + repr(str(disposable)) + ")\n"
                              "alias = fixture\nreader.read(alias)\n(alias / 'rendered/Fixture.json').read_text()\n"
                              "(ROOT / 'tools/tests/fixtures/schema.json').read_bytes()\n"
                              "(ROOT / 'templates/workflow.yml.j2').read_text()\n")
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
