#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Real Git scope and pinned detector qualification; no matrix cases skip."""
from __future__ import annotations

import functools
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from delivery_support import ROOT, git, load

sys.path.insert(0, str(ROOT / "tools"))
sc = load(ROOT / "tools/scan.py", "_scan_tests")
rt = sc.rt


class FixtureGit(rt.Git):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        index = int(self.env["GIT_CONFIG_COUNT"])
        self.env.update({"GIT_CONFIG_COUNT": str(index + 1), f"GIT_CONFIG_KEY_{index}": "protocol.file.allow",
                         f"GIT_CONFIG_VALUE_{index}": "always"})


class Remotes:
    def __init__(self, paths):
        self.paths, self.seen = paths, []

    def module(self, target, module):
        self.seen.append(module)
        target.run("fetch", "--quiet", "--depth=1", "--no-tags", "--no-recurse-submodules",
                   self.paths[module], "+refs/heads/main:refs/heads/main")
        return target.resolve("refs/heads/main^{commit}")


class Workspace:
    def __init__(self, path, modules=("Hexalith.Alpha", "Hexalith.Beta")):
        self.root = Path(path)
        self.root.mkdir(parents=True)
        self.cicd = self.root / "cicd"
        self.cicd.mkdir()
        git(self.cicd, "init", "--quiet", "--initial-branch=main")
        (self.cicd / "setup").mkdir()
        (self.cicd / "tools/jscpd").mkdir(parents=True)
        shutil.copy(ROOT / ".jscpd.json", self.cicd)
        for name in ("package.json", "package-lock.json"):
            shutil.copy(ROOT / "tools/jscpd" / name, self.cicd / "tools/jscpd")
        self.paths = {}
        for module in modules:
            self.module(module)
        self.commit(self.cicd)
        self.transport = Remotes(self.paths)
        self.output = self.root / "report"

    def module(self, module):
        (self.cicd / "setup" / (module + ".yml")).write_text("solution: none\n")
        path = self.root / module
        path.mkdir()
        git(path, "init", "--quiet", "--initial-branch=main")
        (path / "product.txt").write_text("unrelated\n")
        self.commit(path)
        self.paths[module] = path
        return path

    def write(self, module, path, text):
        target = self.paths[module] / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target

    def action(self, module, command="python scripts/check.py", *, shell="bash", extra=""):
        return self.write(module, ".github/actions/dormant/action.yml", "name: Dormant\nruns:\n  using: composite\n  steps:\n"
                          "    - shell: " + shell + "\n" + extra + "      run: " + json.dumps(command) + "\n")

    @staticmethod
    def commit(path):
        git(path, "add", "--force", "--all")
        git(path, "commit", "--quiet", "--allow-empty", "-m", "fixture")
        return git(path, "rev-parse", "HEAD")

    def scan(self, detector):
        return sc.scan(self.cicd, self.output, transport=self.transport, git_factory=FixtureGit,
                       detector_factory=detector)


def block(fmt, label="shared", count=18):
    if fmt == "python":
        return "".join(f'print("{label} operation {i:02d}", {i}, {i + 1})\n' for i in range(count))
    if fmt == "bash":
        return "".join(f"printf '%s\\n' '{label} operation {i:02d}'\n" for i in range(count))
    if fmt == "powershell":
        return "".join(f'Write-Output "{label} operation {i:02d}"\n' for i in range(count))
    return "".join(f"- name: {label} step {i:02d}\n  run: echo operation-{i:02d}\n" for i in range(count))


class ScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="scan-real-detector-")
        root = Path(cls.temporary.name)
        w = Workspace(root / "bootstrap", ())
        cls.detector = sc.Detector(rt.Git(w.cicd), git(w.cicd, "rev-parse", "HEAD"), root)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def workspace(self, modules=("Hexalith.Alpha", "Hexalith.Beta")):
        temporary = tempfile.TemporaryDirectory(prefix="scan-test-")
        self.addCleanup(temporary.cleanup)
        return Workspace(Path(temporary.name) / "workspace", modules)

    def factory(self, *args):
        return self.detector

    def both(self, w, path, text, command=None):
        for module in w.paths:
            w.write(module, path, text)
            if not path.startswith(".github/actions/"):
                w.action(module, command or "python " + path)
            w.commit(w.paths[module])

    def test_all_four_languages_use_actual_pinned_detector(self):
        for fmt, suffix in (("yaml", "yml"), ("bash", "sh"), ("powershell", "ps1"), ("python", "py")):
            with self.subTest(format=fmt):
                w = self.workspace()
                path = ".github/actions/dormant/shared." + suffix
                self.both(w, path, block(fmt))
                detected, original = {}, self.detector.detect
                def capture(roots):
                    value = original(roots)
                    detected.update(value["statistics"])
                    return value
                with mock.patch.object(self.detector, "detect", capture):
                    report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                self.assertFalse(report["errors"], report)
                self.assertTrue(report["findings"], report)
                finding = report["findings"][0]
                self.assertEqual(finding["format"], fmt)
                self.assertEqual(finding["first"]["path"], path)
                self.assertEqual({finding[k]["module"] for k in ("first", "second")}, set(w.paths))
                self.assertIn("operation", finding["fragment"])
                self.assertIn(path + ":", (w.output / "summary.md").read_text())
                print(f"CALIBRATION {fmt}: {finding['lines']} lines, {finding['tokens']} tokens; detected", file=sys.stderr)
                self.assertEqual(detected["total"]["sources"], 2)

    def test_extensionless_scripts_wrappers_and_windows_paths(self):
        w = self.workspace()
        for module in w.paths:
            w.action(module, "cd $GITHUB_WORKSPACE; env MODE=fixture bash -e -o pipefail scripts/start.sh",
                     extra="      working-directory: ${{ github.workspace }}\n")
            w.write(module, "scripts/start.sh", "exec ./scripts/helper\nuv run --locked --script scripts/extra.py\n")
            w.write(module, "scripts/helper", "#!/usr/bin/env python3\n" + block("python"))
            w.write(module, "scripts/helper.py", "# distinct source with colliding suffix\n")
            w.write(module, "scripts/extra.py", "from subprocess import run as launch\nlaunch(['pwsh', '-File', 'scripts/windows.ps1'])\n")
            w.write(module, "scripts/windows.ps1", '. "$PSScriptRoot\\leaf.ps1"\n')
            w.write(module, "scripts/leaf.ps1", block("powershell"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertEqual([row["errors"] for row in report["modules"]], [[], []], report)
        selected = {item["path"] for item in report["modules"][0]["files"]}
        self.assertIn("scripts/helper", selected)
        self.assertIn("scripts/leaf.ps1", selected)
        self.assertTrue(report["findings"], report)

    def test_three_modules_same_module_repetition_and_trivial_boilerplate(self):
        w = self.workspace(("Hexalith.Alpha", "Hexalith.Beta", "Hexalith.Gamma"))
        for module in w.paths:
            self.assertNotEqual(module, rt.BUILDS)
            for index in range(2 if module == "Hexalith.Alpha" else 1):
                w.write(module, f".github/actions/dormant/repeat{index}.py", block("python"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        implicated = {row[key]["module"] for row in report["findings"] for key in ("first", "second")}
        self.assertEqual(implicated, set(w.paths))
        self.assertTrue(all(row["first"]["module"] != row["second"]["module"] for row in report["findings"]))
        alone = self.workspace(("Hexalith.Alpha",))
        for suffix in ("a", "b"):
            alone.write("Hexalith.Alpha", ".github/actions/repeat/" + suffix + ".py", block("python"))
        alone.commit(alone.paths["Hexalith.Alpha"])
        self.assertEqual(alone.scan(self.factory)["result"], "pass")
        for fmt, suffix in (("yaml", "yml"), ("bash", "sh"), ("powershell", "ps1"), ("python", "py")):
            short = self.workspace()
            self.both(short, ".github/actions/short/file." + suffix, block(fmt, count=3))
            self.assertEqual(short.scan(self.factory)["result"], "pass")

    def test_transitive_calls_local_python_imports_and_data_arguments(self):
        w = self.workspace()
        for module in w.paths:
            w.action(module, 'bash "${{ github.action_path }}/wrapper.sh"')
            w.write(module, ".github/actions/dormant/wrapper.sh", "source ./scripts/entry.sh\n")
            w.write(module, "scripts/entry.sh", 'python -I scripts/start.py --data not-a-script.py\n')
            w.write(module, "scripts/start.py", "import local_package.worker\nfrom local_package import leaf\n")
            w.write(module, "scripts/local_package/__init__.py", "# initializer\n")
            w.write(module, "scripts/local_package/worker.py", "from . import leaf\n")
            w.write(module, "scripts/local_package/leaf.py", block("python"))
            w.write(module, "unrelated.py", block("python", "unrelated"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertFalse(report["errors"], report)
        for row in report["modules"]:
            self.assertEqual(row["errors"], [], row)
            selected = {item["path"] for item in row["files"]}
            self.assertIn("scripts/local_package/leaf.py", selected)
            self.assertIn("scripts/local_package/__init__.py", selected)
            self.assertNotIn("unrelated.py", selected)
        self.assertTrue(any(row["first"]["path"].endswith("leaf.py") for row in report["findings"]))

    def test_workspace_working_directory_module_invocation_and_powershell(self):
        w = self.workspace()
        for module in w.paths:
            w.action(module, 'python -m package.entry', extra="      working-directory: ${{ github.workspace }}/scripts\n")
            w.write(module, "scripts/package/__init__.py", "# package\n")
            w.write(module, "scripts/package/entry.py", "import subprocess\nsubprocess.run(['pwsh', '-File', 'scripts/wrapper.ps1'])\n")
            # Scripts retain the literal invocation cwd. PSScriptRoot anchors
            # the second call independently of that cwd.
            w.write(module, "scripts/scripts/wrapper.ps1", '& "$PSScriptRoot/leaf.ps1"\n')
            w.write(module, "scripts/scripts/leaf.ps1", block("powershell"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertEqual([row["errors"] for row in report["modules"]], [[], []], report)
        self.assertTrue(report["findings"], report)

    def test_subprocess_cwd_follows_actual_nested_helper_with_root_decoy(self):
        for cwd, working_directory, target in (("scripts", None, "scripts/helper.py"),
                                               ("nested", "scripts", "scripts/nested/helper.py"),
                                               (None, "scripts", "scripts/helper.py")):
            with self.subTest(cwd=cwd, working_directory=working_directory):
                w = self.workspace()
                for module in w.paths:
                    command = "python " + ("start.py" if working_directory else "scripts/start.py")
                    extra = "      working-directory: scripts\n" if working_directory else ""
                    w.action(module, command, extra=extra)
                    w.write(module, "scripts/start.py", "import subprocess\n"
                            "subprocess.run(['python', 'helper.py'], cwd=" + repr(cwd) + ")\n")
                    w.write(module, "helper.py", "# inactive repository-root decoy\n")
                    w.write(module, target, block("python"))
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                self.assertFalse(report["errors"], report)
                for row in report["modules"]:
                    self.assertEqual(row["errors"], [], row)
                    selected = {item["path"] for item in row["files"]}
                    self.assertIn(target, selected)
                    self.assertNotIn("helper.py", selected)
                self.assertTrue(any(row["first"]["path"] == target and row["second"]["path"] == target
                                    for row in report["findings"]), report)

    def test_unresolved_subprocess_resolution_options_fail_with_source_diagnostic(self):
        for options in ("cwd=directory", "cwd='../outside'", "cwd='helper.py'", "cwd='missing'", "cwd='linked/../scripts'",
                        "**options", "executable='scripts/alternate.py'", "shell=dynamic", "-1, None"):
            with self.subTest(options=options):
                w = self.workspace(("Hexalith.Alpha",))
                w.action("Hexalith.Alpha", "python scripts/start.py")
                w.write("Hexalith.Alpha", "scripts/start.py", "import subprocess\n"
                        "subprocess.run(['python', 'helper.py'], " + options + ")\n")
                w.write("Hexalith.Alpha", "helper.py", "# root decoy cannot establish coverage\n")
                (w.paths["Hexalith.Alpha"] / "linked").symlink_to("scripts")
                w.commit(w.paths["Hexalith.Alpha"])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                row = report["modules"][0]
                self.assertEqual(row["result"], "fail", row)
                self.assertTrue(any("scripts/start.py:2:" in error and "subprocess" in error for error in row["errors"]), row)
                self.assertNotIn("helper.py", {item["path"] for item in row["files"]})

    def test_nested_python_aliases_retain_actual_helper_findings(self):
        cases = (
            "def main():\n    import subprocess as sp\n    sp.run(['python', 'scripts/helper.py'])\nmain()\n",
            "def main():\n    from subprocess import check_call as launch\n    launch(['python', 'scripts/helper.py'])\nmain()\n",
            "def main():\n    import importlib as loader\n    loader.import_module('helper')\nmain()\n",
            "def main():\n    from importlib import import_module as load\n    load('helper')\nmain()\n",
            "def main():\n    import runpy as rp\n    rp.run_path('scripts/helper.py')\nmain()\n",
            "def main():\n    from runpy import run_path as execute\n    execute('scripts/helper.py')\nmain()\n",
            # Reusing a name in another scope must not erase the earlier edge.
            "def first():\n    import subprocess as invoke\n    invoke.run(['python', 'scripts/helper.py'])\n"
            "def second():\n    import importlib as invoke\n    invoke.import_module('helper')\nfirst()\nsecond()\n",
            "def main():\n    import subprocess as sp\n    launch = sp.run\n    launch(['python', 'scripts/helper.py'])\nmain()\n",
        )
        for source in cases:
            with self.subTest(source=source):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, "python scripts/start.py")
                    w.write(module, "scripts/start.py", source)
                    w.write(module, "scripts/helper.py", block("python"))
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                self.assertFalse(report["errors"], report)
                for row in report["modules"]:
                    self.assertEqual(row["errors"], [], row)
                    self.assertIn("scripts/helper.py", {item["path"] for item in row["files"]})
                self.assertTrue(any(row["first"]["path"] == "scripts/helper.py" and
                                    row["second"]["path"] == "scripts/helper.py" for row in report["findings"]), report)

    def test_python_search_path_changes_fail_coverage_even_with_clean_import_decoy(self):
        cases = (
            "import sys\nsys.path.insert(0, 'support')\nimport helper\n",
            "def main():\n    import sys as runtime\n    runtime.path.append('support')\n    import helper\nmain()\n",
            "from sys import path as import_paths\nimport_paths.extend(['support'])\nimport helper\n",
            "import sys\nsys.path[:0] = ['support']\nimport helper\n",
            "import sys\npaths = sys.path\npaths.insert(0, 'support')\nimport helper\n",
            "import sys\nsys.path = ['support']\nimport helper\n",
            "import sys\nsys.path += ['support']\nimport helper\n",
            "import site as sites\nsites.addsitedir('support')\nimport helper\n",
        )
        for source in cases:
            with self.subTest(source=source):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, "python scripts/start.py")
                    w.write(module, "scripts/start.py", source)
                    w.write(module, "helper.py", "# clean root import decoy\n")
                    w.write(module, "support/helper.py", block("python"))
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                for row in report["modules"]:
                    self.assertEqual(row["result"], "fail", row)
                    self.assertTrue(any("scripts/start.py:" in error and "Python search-path mutation" in error
                                        for error in row["errors"]), row)

    def test_unsupported_shell_execution_forms_report_incomplete_coverage(self):
        cases = (
            ('echo "$(python scripts/helper.py)"', "bash", "substitution"),
            ('result="$(python scripts/helper.py)"', "bash", "substitution"),
            ('f() { python scripts/helper.py; }; f', "bash", "compound/subshell"),
            ('& { python scripts/helper.py }', "pwsh", "compound/subshell"),
            ('pushd scripts; python helper.py', "bash", "working-directory"),
            ('Set-Location scripts; python helper.py', "pwsh", "working-directory"),
            ('CD scripts; python helper.py', "pwsh", "working-directory"),
            ('cd scripts; python helper.py', "pwsh", "working-directory"),
            ('CHDIR scripts; python helper.py', "pwsh", "working-directory"),
            ('SL scripts; python helper.py', "pwsh", "working-directory"),
            ('Push-Location scripts; python helper.py', "pwsh", "working-directory"),
            ('Pop-Location; python helper.py', "pwsh", "working-directory"),
            ('PUSHD scripts; python helper.py', "pwsh", "working-directory"),
            ('POPD; python helper.py', "pwsh", "working-directory"),
            ('(cd scripts; python helper.py); python other.py', "bash", "compound/subshell"),
            ('env -i python scripts/helper.py', "bash", "wrapper options"),
            ('env -u MODE python scripts/helper.py', "bash", "wrapper options"),
            ('command -- python scripts/helper.py', "bash", "wrapper options"),
            ('exec -a custom python scripts/helper.py', "bash", "wrapper options"),
            ('Start-Process python -ArgumentList scripts/helper.py -Wait', "pwsh", "process invocation"),
            ('uv run --directory scripts helper.py', "bash", "uv working-directory"),
            ('uv run --directory scripts python helper.py', "bash", "uv working-directory"),
        )
        for command, shell, diagnostic in cases:
            with self.subTest(command=command):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, command, shell=shell)
                    w.write(module, "helper.py", "# clean root decoy\n")
                    w.write(module, "scripts/helper.py", block("python"))
                    w.write(module, "other.py", block("python", "actual root target"))
                    w.write(module, "scripts/other.py", "# clean subdirectory decoy\n")
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                for row in report["modules"]:
                    self.assertEqual(row["result"], "fail", row)
                    self.assertTrue(any("action.yml:" in error and diagnostic in error for error in row["errors"]), row)

    def test_literal_data_arguments_do_not_become_unsupported_execution_forms(self):
        for shell in ("bash", "pwsh"):
            w = self.workspace(("Hexalith.Alpha",))
            w.action("Hexalith.Alpha", "echo '$(python scripts/missing.py)' '(cd scripts)' 'Start-Process python' '{ literal data }'", shell=shell)
            w.commit(w.paths["Hexalith.Alpha"])
            report = w.scan(self.factory)
            self.assertEqual(report["result"], "pass", report)

    def test_condition_calls_powershell_named_modules_and_source_cwd(self):
        for prefix in ("while", "until", "elif"):
            w = self.workspace()
            for module in w.paths:
                command = ("if false; then true; elif ./scripts/helper.sh; then true; fi" if prefix == "elif"
                           else prefix + " ./scripts/helper.sh; do true; done")
                w.action(module, command)
                w.write(module, "scripts/helper.sh", block("bash"))
                w.commit(w.paths[module])
            report = w.scan(self.factory)
            self.assertFalse(report["errors"], report)
            self.assertTrue(report["findings"], report)
            self.assertEqual([row["errors"] for row in report["modules"]], [[], []])
        w = self.workspace()
        for module in w.paths:
            w.action(module, "Import-Module -Name ./scripts/helper.psm1", shell="pwsh")
            w.write(module, "scripts/helper.psm1", block("powershell"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertTrue(report["findings"], report)
        self.assertEqual([row["errors"] for row in report["modules"]], [[], []])
        w = self.workspace()
        for module in w.paths:
            w.action(module, "source scripts/change.sh; python helper.py")
            w.write(module, "scripts/change.sh", "cd scripts\n")
            w.write(module, "helper.py", "# clean root decoy\n")
            w.write(module, "scripts/helper.py", block("python"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertEqual(report["result"], "fail", report)
        self.assertTrue(all(any("scripts/change.sh:1:" in error and "sourced script" in error
                                for error in row["errors"]) for row in report["modules"]), report)

    def test_python_invocation_roots_namespace_imports_and_package_entrypoints(self):
        cases = (
            ("python scripts/start.py", {"scripts/start.py": "from pkg import helper\n"},
             "scripts/pkg/helper.py", "pkg/helper.py"),
            ("python -m scripts.start", {"scripts/start.py": "import helper\n"},
             "helper.py", "scripts/helper.py"),
            ("python -c 'import helper'", {}, "helper.py", ".github/actions/dormant/helper.py"),
            ("python scripts/start.py", {"scripts/start.py": "import package.worker\n",
                                        "scripts/package/__init__.py": "# package\n",
                                        "scripts/package/worker.py": "import helper\n"},
             "scripts/helper.py", "scripts/package/helper.py"),
            ("python -m package", {"package/__init__.py": "# package\n"},
             "package/__main__.py", "scripts/package/__main__.py"),
            ("python -m package", {}, "package/__main__.py", "scripts/package/__main__.py"),
        )
        for command, sources, target, decoy in cases:
            with self.subTest(command=command, target=target, sources=sources):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, command)
                    for path, text in sources.items():
                        w.write(module, path, text)
                    w.write(module, target, block("python"))
                    w.write(module, decoy, "# inactive clean import decoy\n")
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertFalse(report["errors"], report)
                for row in report["modules"]:
                    self.assertEqual(row["errors"], [], row)
                    self.assertIn(target, {item["path"] for item in row["files"]})
                    for source in sources:
                        if source.endswith("/__init__.py"):
                            self.assertIn(source, {item["path"] for item in row["files"]})
                    # Files initially seeded beneath actions remain in scope.
                    if not decoy.startswith(".github/actions/"):
                        self.assertNotIn(decoy, {item["path"] for item in row["files"]})
                self.assertTrue(any(row["first"]["path"] == target and row["second"]["path"] == target
                                    for row in report["findings"]), report)

    def test_subprocess_environment_import_overrides_cannot_certify_root_decoy(self):
        for environment in ("{'PYTHONPATH': 'support'}", "{'PATH': 'support'}", "environment"):
            w = self.workspace()
            for module in w.paths:
                w.action(module, "python scripts/start.py")
                w.write(module, "scripts/start.py", "import subprocess\n"
                        "subprocess.run(['python', '-m', 'helper'], env=" + environment + ")\n")
                w.write(module, "helper.py", "# root decoy\n")
                w.write(module, "support/helper.py", block("python"))
                w.commit(w.paths[module])
            report = w.scan(self.factory)
            self.assertEqual(report["result"], "fail", report)
            self.assertTrue(all(any("scripts/start.py:2:" in error and "env" in error for error in row["errors"])
                                for row in report["modules"]), report)

    def test_actual_detector_original_offsets_source_slices_and_summary_ranges(self):
        w = self.workspace()
        target = ".github/actions/dormant/code.py"
        copied = block("python", "original-offset-calibration")
        prefixes = {"Hexalith.Alpha": "import decimal\n\n", "Hexalith.Beta": "from fractions import Fraction\n\n\n\n\n"}
        expected = {"Hexalith.Alpha": (3, 20), "Hexalith.Beta": (6, 23)}
        for module in w.paths:
            w.write(module, target, prefixes[module] + copied)
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertEqual(report["result"], "fail", report)
        self.assertFalse(report["errors"], report)
        self.assertEqual(len(report["findings"]), 1, report)
        finding = report["findings"][0]
        self.assertEqual(finding["fragment"], copied.rstrip("\n"))
        summary = (w.output / "summary.md").read_text()
        for key in ("first", "second"):
            endpoint = finding[key]
            module = endpoint["module"]
            self.assertEqual(endpoint["path"], target)
            self.assertEqual((endpoint["start"], endpoint["end"]), expected[module])
            source = (w.paths[module] / target).read_text().splitlines()
            self.assertEqual("\n".join(source[endpoint["start"] - 1:endpoint["end"]]), copied.rstrip("\n"))
            self.assertIn(f"{module}/{target}:{expected[module][0]}-{expected[module][1]}", summary)

    def test_live_main_is_authoritative_committed_registry_and_reproducibility(self):
        w = self.workspace()
        # Stale/unregistered superproject checkouts cannot select scan bytes.
        local = w.cicd / "references/Hexalith.Alpha"
        local.mkdir(parents=True)
        (local / "stale.py").write_text(block("python", "stale"))
        w.module("Hexalith.Unregistered")
        # Do not commit its registration.
        for module in w.paths:
            w.write(module, ".github/actions/dormant/code.py", block("python"))
            w.commit(w.paths[module])
        first = w.scan(self.factory)
        self.assertEqual(w.transport.seen, ["Hexalith.Alpha", "Hexalith.Beta"])
        self.assertTrue(all(row["revision"] == git(w.paths[row["module"]], "rev-parse", "HEAD") for row in first["modules"]))
        self.assertEqual(first, w.scan(self.factory))

    def test_module_policy_ignores_and_source_directives_cannot_hide_clones(self):
        w = self.workspace()
        text = "# jscpd:ignore-start\n" + block("python") + "# jscpd:ignore-end\n"
        for module in w.paths:
            w.write(module, ".jscpd.json", '{"ignore":["**"],"minTokens":999999}\n')
            w.write(module, ".ignore", "**\n")
            w.write(module, ".gitignore", "ignored.py\n")
        self.both(w, ".github/actions/dormant/ignored.py", text)
        report = w.scan(self.factory)
        self.assertTrue(report["findings"], report)
        self.assertIn("print", report["findings"][0]["fragment"])

    def test_empty_registry_and_modules_without_actions_are_explicit_success(self):
        for modules in ((), ("Hexalith.Alpha",)):
            w = self.workspace(modules)
            report = w.scan(self.factory)
            self.assertEqual(report["result"], "pass", report)
            self.assertFalse(report["findings"])
            self.assertIn("successful zero scope", (w.output / "summary.md").read_text())

    def test_registry_invalid_collision_builds_symlink_and_capacity_fail(self):
        for names in (("Hexalith.Builds",), ("Alpha", "alpha"), tuple("Module" + str(i) for i in range(18)), ("bad name",)):
            w = self.workspace(())
            for name in names:
                (w.cicd / "setup" / (name + ".yml")).write_text("{}\n")
            w.commit(w.cicd)
            report = w.scan(self.factory)
            self.assertEqual(report["result"], "fail", report)
            self.assertTrue(report["errors"])
            self.assertFalse(w.transport.seen)
        w = self.workspace(())
        (w.cicd / "setup/Link.yml").symlink_to("../.jscpd.json")
        w.commit(w.cicd)
        self.assertEqual(w.scan(self.factory)["result"], "fail")

    def test_unreadable_module_is_isolated_healthy_sibling_findings_survive(self):
        w = self.workspace(("Hexalith.Alpha", "Hexalith.Beta", "Hexalith.Broken"))
        self.both(w, ".github/actions/copy/code.py", block("python"))
        shutil.rmtree(w.paths["Hexalith.Broken"])
        report = w.scan(self.factory)
        self.assertEqual(report["result"], "fail")
        self.assertTrue(report["findings"], report)
        self.assertEqual([row["result"] for row in report["modules"]], ["pass", "pass", "fail"])
        self.assertEqual(report["modules"][-1]["revision"], "")

    def test_invalid_actions_unsafe_sources_and_oversized_blobs_fail_per_module(self):
        cases = ("invalid", "symlink", "root-symlink", "gitlink", "oversized", "nul", "unsafe-name")
        for case in cases:
            with self.subTest(case=case):
                w = self.workspace()
                module = "Hexalith.Alpha"
                path = ".github/actions/broken/action.yml"
                if case == "invalid":
                    w.write(module, path, "runs: [broken\n")
                elif case == "symlink":
                    target = w.write(module, path, "placeholder")
                    target.unlink()
                    target.symlink_to("../../../product.txt")
                elif case == "root-symlink":
                    (w.paths[module] / ".github").mkdir()
                    (w.paths[module] / ".github/actions").symlink_to("../product.txt")
                elif case == "gitlink":
                    git(w.paths[module], "update-index", "--add", "--cacheinfo", "160000",
                        git(w.paths[module], "rev-parse", "HEAD"), ".github/actions/submodule")
                    git(w.paths[module], "commit", "--quiet", "-m", "gitlink")
                elif case == "oversized":
                    w.write(module, ".github/actions/broken/big.py", "#" * (rt.MAX_JSON + 1))
                elif case == "nul":
                    w.write(module, ".github/actions/broken/code.py", "\0")
                else:
                    w.write(module, ".github/actions/broken/bad\nname.py", "pass\n")
                if case != "gitlink":
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                self.assertEqual(report["modules"][0]["result"], "fail", report)
                self.assertTrue(report["modules"][0]["errors"], report)
                self.assertEqual(report["modules"][1]["result"], "pass")

    def test_missing_dynamic_and_outside_calls_report_source_diagnostics(self):
        for command in ("python missing.py", 'bash "$SCRIPT"', "pwsh -File ../../outside.ps1", "./missing.sh"):
            w = self.workspace(("Hexalith.Alpha",))
            w.action("Hexalith.Alpha", command)
            w.commit(w.paths["Hexalith.Alpha"])
            report = w.scan(self.factory)
            self.assertEqual(report["result"], "fail", report)
            error = report["modules"][0]["errors"][0]
            self.assertIn("action.yml:", error)
            self.assertIn("local-script", error)

    def test_nonexecuting_git_and_anonymous_transport_environment(self):
        w = self.workspace(("Hexalith.Alpha",))
        marker = w.root / "MODULE-CODE-WAS-EXECUTED"
        w.action("Hexalith.Alpha", "bash scripts/call.sh")
        w.write("Hexalith.Alpha", "scripts/call.sh", "touch " + str(marker) + "\n")
        w.write("Hexalith.Alpha", ".gitattributes", "* filter=poison\n")
        git(w.paths["Hexalith.Alpha"], "config", "filter.poison.smudge", "touch " + str(marker))
        w.commit(w.paths["Hexalith.Alpha"])
        with mock.patch.dict(os.environ, {"GH_TOKEN": "sensitive-inert-value", "GITHUB_TOKEN": "sensitive-inert-value",
                                          "GIT_CONFIG_GLOBAL": str(w.root / "poison")}, clear=False):
            report = w.scan(self.factory)
        self.assertEqual(report["result"], "pass", report)
        self.assertFalse(marker.exists())
        self.assertNotIn("sensitive-inert-value", (w.output / "report.json").read_text())
        env = rt.environment()
        self.assertNotIn("GH_TOKEN", env)
        self.assertNotIn("GITHUB_TOKEN", self.detector.env)
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(rt.Transport().remote("Hexalith.Alpha"), "https://github.com/Hexalith/Hexalith.Alpha.git")

    def test_install_signature_version_and_detector_failures_remain_visible(self):
        w = self.workspace()
        self.both(w, ".github/actions/copy/code.py", block("python"))
        for operation in ("npm locked install", "npm signature verification", "detector version verification"):
            original = sc.Detector.run
            def fail(detector, command, name, timeout):
                if name == operation:
                    raise rt.DeliveryError(operation + " failed")
                return original(detector, command, name, timeout)
            with mock.patch.object(sc.Detector, "run", fail):
                report = w.scan(sc.Detector)
            self.assertEqual(report["result"], "fail", report)
            self.assertIn(operation, report["errors"][0])
            self.assertTrue(report["modules"][0]["files"])
        with mock.patch.object(self.detector, "detect", side_effect=rt.DeliveryError("duplicate detector failed")):
            report = w.scan(self.factory)
        self.assertEqual(report["result"], "fail")
        self.assertIn("duplicate detector failed", report["errors"])

    def test_invalid_and_outside_detector_reports_fail_closed(self):
        w = self.workspace()
        self.both(w, ".github/actions/copy/code.py", block("python"))
        original = self.detector.detect
        def mutated(roots):
            value = original(roots)
            return mutation(value)
        def endpoint(value):
            value["duplicates"][0]["firstFile"]["name"] = "/outside/module.py"
            return value
        def range_error(value):
            value["duplicates"][0]["secondFile"]["end"] = 99999
            return value
        def format_error(value):
            value["duplicates"][0]["format"] = "javascript"
            return value
        def location_error(value):
            del value["duplicates"][0]["firstFile"]["startLoc"]
            return value
        for mutation in (lambda value: {}, lambda value: {"duplicates": []},
                         lambda value: value | {"statistics": {"formats": {}, "total": {}}}, endpoint, range_error,
                         format_error, location_error, lambda value: value | {"duplicates": [None]}):
            with mock.patch.object(self.detector, "detect", mutated):
                report = w.scan(self.factory)
            self.assertEqual(report["result"], "fail", report)
            self.assertTrue(report["errors"], report)
        for raw in (b'{"duplicates":[],"duplicates":[]}', b'{"bad":NaN}', b'invalid', b'"' + b'a' * sc.MAX_REPORT):
            with self.assertRaises(rt.DeliveryError):
                sc.read_json(raw)

    def test_central_policy_failure_and_bounded_export_report(self):
        w = self.workspace()
        self.both(w, ".github/actions/copy/code.py", block("python"))
        (w.cicd / ".jscpd.json").write_text('{"format":["python"],"ignore":["**"]}\n')
        w.commit(w.cicd)
        report = w.scan(sc.Detector)
        self.assertIn("invalid central detector policy", report["errors"])
        with mock.patch.object(sc, "MAX_EXPORT", 1):
            report = w.scan(self.factory)
        self.assertEqual(report["result"], "fail")
        self.assertTrue(all(row["errors"] for row in report["modules"]))

    def test_wrong_version_missing_config_integrity_and_report_failure(self):
        w = self.workspace(())
        run = sc.Detector.run
        def wrong_version(detector, command, operation, timeout):
            if operation == "detector version verification":
                return b"jscpd 0.0.0\n"
            return run(detector, command, operation, timeout)
        with mock.patch.object(sc.Detector, "run", wrong_version):
            report = w.scan(sc.Detector)
        self.assertIn("detector reported unexpected version", report["errors"])
        lock_path = w.cicd / "tools/jscpd/package-lock.json"
        lock = json.loads(lock_path.read_bytes())
        del lock["packages"]["node_modules/jscpd"]["integrity"]
        lock_path.write_text(json.dumps(lock))
        w.commit(w.cicd)
        self.assertIn("detector dependency lacks registry integrity pin", w.scan(sc.Detector)["errors"])
        (w.cicd / ".jscpd.json").unlink()
        w.commit(w.cicd)
        self.assertEqual(w.scan(sc.Detector)["result"], "fail")
        persist = sc.persist
        injected = []
        def fail_report(directory, value):
            if value["result"] == "pass" and not injected:
                injected.append(True)
                raise rt.DeliveryError("injected report write failure")
            persist(directory, value)
        with mock.patch.object(sc, "persist", fail_report):
            report = w.scan(self.factory)
        self.assertEqual(report["result"], "fail")
        self.assertIn("report generation failed", report["errors"][-1])
        self.assertEqual(json.loads((w.output / "report.json").read_bytes())["result"], "fail")
        self.assertIn("incomplete", (w.output / "summary.md").read_text())

    def test_production_entrypoint_return_codes_and_retained_reports(self):
        w = self.workspace(())
        actual = sc.scan
        injected = functools.partial(actual, transport=w.transport, git_factory=FixtureGit, detector_factory=self.factory)
        with mock.patch.object(sc, "scan", injected), mock.patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(sc.main(["--project-root", str(w.cicd), "--output", str(w.output)]), 0)
            (w.cicd / "setup/Hexalith.Builds.yml").write_text("{}\n")
            w.commit(w.cicd)
            self.assertEqual(sc.main(["--project-root", str(w.cicd), "--output", str(w.output)]), 1)
        self.assertEqual(json.loads((w.output / "report.json").read_bytes())["result"], "fail")
        self.assertIn("FAIL", (w.output / "summary.md").read_text())


if __name__ == "__main__":
    unittest.main()
