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
FORMATS = sc.FORMATS


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
        for name in ("package.json", "package-lock.json", "discover.cjs"):
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
    if fmt in {"javascript", "typescript"}:
        return "".join(f'console.log("{label} operation {i:02d}", {i}, {i+1});\n' for i in range(count))
    if fmt == "bash":
        return "".join(f"printf '%s\\n' '{label} operation {i:02d}'\n" for i in range(count))
    if fmt == "powershell":
        return "".join(f'Write-Output "{label} operation {i:02d}"\n' for i in range(count))
    return "".join(f"- name: {label} step {i:02d}\n  run: echo operation-{i:02d}\n" for i in range(count))


def steps(*items):
    """A composite action whose steps are (shell, run, extra) tuples."""
    text = "name: Dormant\nruns:\n  using: composite\n  steps:\n"
    for shell, run, extra in items:
        text += "    - shell: " + shell + "\n" + extra + "      run: " + json.dumps(run) + "\n"
    return text


def python_source(label="shared"):
    return block("python", label)


# Review pass 3 (A1) reproductions. Each is (label, steps, files, target, diagnostic):
# the copied target is a cross-module finding, the diagnostic names the coverage
# failure, or both. "COPY" marks the substantial copied source.
COPY = object()
A1 = (
    ("env-abs", [("bash", "/usr/bin/env python3 scripts/helper.py", "")], {"scripts/helper.py": COPY},
     "scripts/helper.py", None),
    ("timeout-abs", [("bash", "/usr/bin/timeout 60 ./scripts/helper.sh", "")], {"scripts/helper.sh": COPY},
     "scripts/helper.sh", None),
    ("abs-uv", [("bash", "/home/runner/.local/bin/uv run scripts/helper.py", "")], {"scripts/helper.py": COPY},
     "scripts/helper.py", None),
    ("then-brace", [("bash", "if true; then { ./scripts/helper.sh; }; fi", "")], {"scripts/helper.sh": COPY},
     "scripts/helper.sh", None),
    ("do-brace", [("bash", "while true; do { ./scripts/helper.sh; break; }; done", "")],
     {"scripts/helper.sh": COPY}, "scripts/helper.sh", None),
    ("func-midline", [("bash", "true; function f { ./scripts/helper.sh; }; f", "")], {"scripts/helper.sh": COPY},
     "scripts/helper.sh", "unsupported shell compound/subshell execution"),
    ("ps-try", [("pwsh", "try { ./scripts/helper.ps1 } catch { exit 1 }", "")], {"scripts/helper.ps1": COPY},
     "scripts/helper.ps1", None),
    ("ps-else", [("pwsh", "} else { ./scripts/helper.ps1 }", "")], {"scripts/helper.ps1": COPY},
     "scripts/helper.ps1", None),
    ("builtin-source", [("bash", "builtin source ./scripts/helper.sh", "")], {"scripts/helper.sh": COPY},
     "scripts/helper.sh", None),
    ("coproc", [("bash", "coproc ./scripts/helper.sh", "")], {"scripts/helper.sh": COPY}, "scripts/helper.sh", None),
    ("redirect-first", [("bash", ">out.log ./scripts/helper.sh", "")], {"scripts/helper.sh": COPY},
     "scripts/helper.sh", None),
    ("trap-dashdash", [("bash", "trap -- './scripts/helper.sh' EXIT", "")], {"scripts/helper.sh": COPY},
     "scripts/helper.sh", None),
    ("uv-p", [("bash", "uv run -p 3.12 scripts/helper.py", "")], {"scripts/helper.py": COPY},
     "scripts/helper.py", None),
    ("uv-extra", [("bash", "uv run --extra dev scripts/helper.py", "")], {"scripts/helper.py": COPY},
     "scripts/helper.py", None),
    ("uv-envfile", [("bash", "uv run --env-file .env python -m helper", "")],
     {".env": "PYTHONPATH=support\n", "support/helper.py": COPY, "helper.py": "# root decoy\n"},
     None, "unsupported uv env file affecting script resolution"),
    ("prefix-append", [("bash", "MODE+=x ./scripts/helper.sh", "")], {"scripts/helper.sh": COPY},
     "scripts/helper.sh", None),
    ("prefix-append-env", [("bash", "env MODE+=x ./scripts/helper.sh", "")], {"scripts/helper.sh": COPY},
     "scripts/helper.sh", None),
    ("export-append", [("bash", "export PYTHONPATH+=:support; python -m helper", "")],
     {"support/helper.py": COPY, "helper.py": "# root decoy\n"},
     None, "unsupported environment assignment affecting script resolution"),
    ("github-env", [("bash", 'echo "PYTHONPATH=support" >> "$GITHUB_ENV"', ""), ("bash", "python -m helper", "")],
     {"support/helper.py": COPY, "helper.py": "# root decoy\n"},
     None, "unsupported $GITHUB_ENV write affecting script resolution"),
    ("non-mapping-step-env", [("bash", "python -m helper", "      env: ${{ fromJSON(inputs.environment) }}\n")],
     {"support/helper.py": COPY, "helper.py": "# root decoy\n"},
     None, "unsupported computed step environment affecting script resolution"),
    ("path-export", [("bash", 'export PATH="$PWD/scripts:$PATH"; helper.sh', "")],
     {"scripts/helper.sh": COPY, "helper.sh": "# root decoy\n"},
     None, "unsupported PATH change affecting script resolution"),
    ("cond-cd", [("bash", 'if [ -n "$X" ]; then cd scripts; fi\npython helper.py', "")],
     {"helper.py": COPY, "scripts/helper.py": "# conditional decoy\n"}, "helper.py", None),
    ("py-eval", [("bash", "python scripts/start.py", "")],
     {"scripts/start.py": "eval(\"__import__('helper')\")\n", "scripts/helper.py": COPY},
     None, "unsupported Python process/import API: eval"),
    ("py-attr-alias", [("bash", "python scripts/start.py", "")],
     {"scripts/start.py": "import subprocess\nclass R:\n    def __init__(self):\n        self.launch = subprocess.run\n"
                          "R().launch(['python', 'scripts/helper.py'])\n", "scripts/helper.py": COPY},
     "scripts/helper.py", "scripts/start.py:4: local-script discovery: unsupported reflective use"),
    ("py-arg-pass", [("bash", "python scripts/start.py", "")],
     {"scripts/start.py": "import subprocess\ndef call(f, *a):\n    return f(*a)\n"
                          "call(subprocess.run, ['python', 'scripts/helper.py'])\n", "scripts/helper.py": COPY},
     "scripts/helper.py", "unsupported reflective use of a process/import API"),
    ("py-getattr", [("bash", "python scripts/start.py", "")],
     {"scripts/start.py": "import subprocess\ngetattr(subprocess, 'run')(['python', 'scripts/helper.py'])\n",
      "scripts/helper.py": COPY}, "scripts/helper.py", "unsupported reflective getattr"),
    ("py-tuple", [("bash", "python scripts/start.py", "")],
     {"scripts/start.py": "import subprocess, os\na, b = subprocess.run, os.system\n"
                          "a(['python', 'scripts/helper.py'])\n", "scripts/helper.py": COPY},
     "scripts/helper.py", "unsupported reflective use of a process/import API"),
    ("py-walrus", [("bash", "python scripts/start.py", "")],
     {"scripts/start.py": "import subprocess\nif (r := subprocess.run):\n    r(['python', '-m', 'helper'])\n",
      "helper.py": COPY}, None, "unsupported reflective use of a process/import API"),
    ("py-default-arg", [("bash", "python scripts/start.py", "")],
     {"scripts/start.py": "import subprocess\ndef f(run=subprocess.run):\n    run(['python', '-m', 'helper'])\nf()\n",
      "helper.py": COPY}, None, "unsupported reflective use of a process/import API"),
    ("pwsh-stdin", [("pwsh", "Get-Content scripts/x.ps1 | pwsh -Command -", "")], {"scripts/x.ps1": COPY},
     "scripts/x.ps1", "unsupported stdin-fed interpreter"),
    ("bash-heredoc", [("bash", "bash <<EOF\n./scripts/x.sh\nEOF", "")], {"scripts/x.sh": COPY},
     "scripts/x.sh", "unsupported heredoc-fed interpreter"),
    ("python-heredoc", [("bash", "python - <<'EOF'\nimport helper\nEOF", "")], {"helper.py": COPY},
     None, "unsupported heredoc-fed interpreter"),
    ("make-recipe", [("bash", "make lint", "")], {"Makefile": "lint:\n\tpython -m helper\n", "helper.py": COPY},
     None, "unsupported task runner with tracked module recipes: make"),
    ("just-recipe", [("bash", "just lint", "")], {"justfile": "lint:\n    python -m helper\n", "helper.py": COPY},
     None, "unsupported task runner with tracked module recipes: just"),
    ("npm-recipe", [("bash", "npm run lint", "")],
     {"package.json": '{"scripts": {"lint": "python -m helper"}}\n', "helper.py": COPY},
     None, "missing or unsafe npm/config input: package-lock.json"),
    ("poetry-recipe", [("bash", "poetry run lint", "")],
     {"pyproject.toml": "[tool.poetry.scripts]\nlint = 'helper:main'\n", "helper.py": COPY},
     None, "unsupported task runner with tracked module recipes: poetry"),
    ("pdm-recipe", [("bash", "pdm run lint", "")],
     {"pyproject.toml": "[tool.pdm.scripts]\nlint = 'python -m helper'\n", "helper.py": COPY},
     None, "unsupported task runner with tracked module recipes: pdm"),
    ("uv-entry-point", [("bash", "uv run lint", "")],
     {"pyproject.toml": "[project]\nname = 'x'\n[project.scripts]\nlint = 'helper:main'\n", "helper.py": COPY},
     None, "unsupported task runner with tracked module recipes: uv"),
)


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

    def test_npm_recipe_covers_complete_workspace_aliases_and_cross_language_calls(self):
        files = {
            "tests/e2e/package.json": json.dumps({"scripts":{"test:package":"playwright test --project=chromium"}}),
            "tests/e2e/package-lock.json": '{"lockfileVersion":3,"packages":{}}',
            "tests/e2e/tsconfig.json": json.dumps({"compilerOptions":{"baseUrl":".","paths":{"@helpers/*":["../shared/*"]}}}),
            "tests/e2e/playwright.config.ts": "export default {globalSetup:'./setup.ts'};\n",
            "tests/e2e/setup.ts": "import '@helpers/copied.js';\n",
            "tests/e2e/specs/only-npm.spec.ts": block("typescript", "npm-only"),
            "tests/shared/copied.ts": block("typescript", "aliased-only"),
            "tests/e2e/process.ts": "import {execFileSync as run} from 'node:child_process'; run('python3',['../../scripts/helper.py']);\n",
            "scripts/helper.py": block("python", "javascript-process-only"),
        }
        report = self.coverage_case([("bash", "npm --prefix tests/e2e run test:package", "")], files)
        self.assert_coverage(report, "tests/shared/copied.ts", None)
        self.assert_coverage(report, "tests/e2e/specs/only-npm.spec.ts", None)
        self.assert_coverage(report, "scripts/helper.py", None)
        self.assertTrue(all(not row["errors"] for row in report["modules"]), report)

    def test_javascript_computed_import_process_and_config_fail_closed(self):
        for source, diagnostic in (
            ("import(process.env.TARGET);", "computed JavaScript import"),
            ("import {runInNewContext} from 'node:vm'; runInNewContext(process.env.CODE);", "VM/config execution"),
            ("import('node:child_process').then(cp => cp.exec(process.env.CMD));", "dynamic JavaScript process-module import"),
            ("require('node:child_process').spawn(process.env.TOOL, []);", "inline JavaScript process-module require"),
            ("let execute; execute = require('node:child_process').exec; execute(process.env.CMD);", "inline JavaScript process-module require"),
            ("globalThis.require('node:child_process').exec(process.env.CMD);", "inline JavaScript process-module require"),
            ("globalThis.process.getBuiltinModule('child_process').spawn(process.env.TOOL, []);", "reflective JavaScript execution"),
            ("const runtime = globalThis.process; runtime.getBuiltinModule('child_process').exec(process.env.CMD);", "reflective JavaScript execution"),
            ("import {exec} from 'node:child_process'; setTimeout(exec, 0, process.env.CMD);", "API escape"),
            ("import {spawn} from 'node:child_process'; spawn(process.env.TOOL, []);", "computed JavaScript process"),
            ("export default {globalSetup:process.env.SETUP};", "computed JavaScript test configuration"),
            ("export default {reporter:process.env.REPORTER};", "computed JavaScript reporter"),
            ("export default {webServer:{command:process.env.CMD}};", "computed JavaScript webServer command"),
            ("import '../outside.js';", "source path escapes module"),
            ("const cp=require('node:child_process'); cp[process.env.API]('python');", "reflective JavaScript process"),
        ):
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "node script.js", "")], {"script.js":source})
                self.assertEqual("fail", report["result"])
                self.assertTrue(all(any(diagnostic in message for message in row["errors"]) for row in report["modules"]), report)

    def test_npm_later_flags_cannot_enable_unscanned_lifecycle_scripts(self):
        for command in ("npm ci --ignore-scripts --ignore-scripts=false",
                        "npm --ignore-scripts ci --ignore-scripts=0"):
            with self.subTest(command=command):
                report = self.coverage_case([("bash", command, "")], {})
                self.assertEqual("fail", report["result"])
                self.assertTrue(all(any("lifecycle-enabling option" in message for message in row["errors"])
                                    for row in report["modules"]), report)

    def test_all_six_languages_use_actual_pinned_detector(self):
        for fmt, suffix in (("yaml", "yml"), ("bash", "sh"), ("powershell", "ps1"), ("python", "py"),
                            ("javascript", "js"), ("typescript", "ts")):
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
            w.write(module, "scripts/start.sh", "exec ./scripts/helper\nuv run --locked --script scripts/extra.py\n"
                    "python scripts/helper.py --check\n")
            w.write(module, "scripts/helper", "#!/usr/bin/env python3\n" + block("python"))
            # Selected beside scripts/helper: path-based staging would overwrite one.
            w.write(module, "scripts/helper.py", "# distinct source with colliding suffix\n")
            w.write(module, "scripts/extra.py", "from subprocess import run as launch\nlaunch(['pwsh', '-File', 'scripts/windows.ps1'])\n")
            w.write(module, "scripts/windows.ps1", '. "$PSScriptRoot\\leaf.ps1"\n')
            w.write(module, "scripts/leaf.ps1", block("powershell"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertEqual([row["errors"] for row in report["modules"]], [[], []], report)
        for row in report["modules"]:
            selected = {item["path"] for item in row["files"]}
            self.assertLessEqual({"scripts/helper", "scripts/helper.py", "scripts/leaf.ps1"}, selected)
        # The Python finding stays at the extensionless source in both modules.
        self.assertTrue(any(row["format"] == "python" and row["first"]["path"] == "scripts/helper"
                            and row["second"]["path"] == "scripts/helper"
                            and row["first"]["module"] != row["second"]["module"] for row in report["findings"]), report)

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
                    # Coverage model rule 1: the literal 'helper.py' also names
                    # the root decoy from the workspace base, so it is included.
                    self.assertIn("helper.py", selected)
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
                # The decoy is included as a data literal; it never certifies coverage.
                self.assertIn("helper.py", {item["path"] for item in row["files"]})

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
            ('nice -n 5 python scripts/helper.py', "bash", "wrapper options"),
            ('PYTHONPATH=scripts python -m helper', "bash", "environment"),
            ('env PYTHONPATH=scripts python -m helper', "bash", "environment"),
            ('export PYTHONPATH=scripts; python -m helper', "bash", "environment"),
            ('eval "cd scripts"; python helper.py', "bash", "working directory"),
            ('find . -execdir python helper.py \\;', "bash", "execdir"),
            ('find scripts -name "*.py" -exec {} \\;', "bash", "find -exec"),
            ('Invoke-Command -FilePath scripts/helper.ps1', "pwsh", "Invoke-Command"),
            ('pwsh -WorkingDirectory scripts -File helper.ps1', "pwsh", "working-directory"),
            ('pwsh -EncodedCommand ZQBjAGgAbwA=', "pwsh", "encoded"),
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
                    w.write(module, "scripts/tool.js", "console.log('unsupported language');\n")
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                for row in report["modules"]:
                    self.assertEqual(row["result"], "fail", row)
                    self.assertTrue(any("action.yml:" in error and diagnostic in error for error in row["errors"]), row)

    def test_wrapped_option_positioned_and_spelled_interpreter_calls_reach_actual_scripts(self):
        cases = (
            ("timeout 60 ./scripts/helper.sh", "bash", "scripts/helper.sh"),
            ("nohup ./scripts/helper.sh", "bash", "scripts/helper.sh"),
            ("time ./scripts/helper.sh", "bash", "scripts/helper.sh"),
            ("sudo ./scripts/helper.sh", "bash", "scripts/helper.sh"),
            ("nice ./scripts/helper.sh", "bash", "scripts/helper.sh"),
            ("eval ./scripts/helper.sh", "bash", "scripts/helper.sh"),
            ("trap './scripts/helper.sh' EXIT", "bash", "scripts/helper.sh"),
            ("find . -name '*.txt' -exec ./scripts/helper.sh {} \\;", "bash", "scripts/helper.sh"),
            ("if [ $# -lt 1 ]; then ./scripts/helper.sh; fi  # trailing comment", "bash", "scripts/helper.sh"),
            ("python scripts/helper.py -c config.yml -m fast", "bash", "scripts/helper.py"),
            ("python -u -X dev scripts/helper.py", "bash", "scripts/helper.py"),
            ("python3.11 scripts/helper.py", "bash", "scripts/helper.py"),
            ("python.exe scripts/helper.py", "bash", "scripts/helper.py"),
            ("bash scripts/helper.sh -c Release", "bash", "scripts/helper.sh"),
            ("pwsh -NoProfile -executionpolicy Bypass -File scripts/helper.ps1 -config release", "pwsh", "scripts/helper.ps1"),
            ("pwsh.exe -File scripts/helper.ps1", "pwsh", "scripts/helper.ps1"),
            ("Invoke-Expression './scripts/helper.ps1'", "pwsh", "scripts/helper.ps1"),
            ("using module ./scripts/helper.psm1", "pwsh", "scripts/helper.psm1"),
        )
        formats = {".sh": "bash", ".py": "python", ".ps1": "powershell", ".psm1": "powershell"}
        for command, shell, target in cases:
            with self.subTest(command=command):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, command, shell=shell)
                    w.write(module, target, block(formats[Path(target).suffix]))
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual([row["errors"] for row in report["modules"]], [[], []], report)
                for row in report["modules"]:
                    self.assertIn(target, {item["path"] for item in row["files"]})
                self.assertTrue(any(row["first"]["path"] == target and row["second"]["path"] == target
                                    for row in report["findings"]), report)

    def test_python_process_apis_are_followed_or_fail_explicitly(self):
        for source in ("import os\nos.popen('python scripts/helper.py')\n",
                       "import subprocess\nsubprocess.getoutput('python scripts/helper.py')\n"):
            with self.subTest(source=source):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, "python scripts/start.py")
                    w.write(module, "scripts/start.py", source)
                    w.write(module, "scripts/helper.py", block("python"))
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual([row["errors"] for row in report["modules"]], [[], []], report)
                self.assertTrue(any(row["first"]["path"] == "scripts/helper.py" for row in report["findings"]), report)
        failing = (
            ("import os\nos.execv('/usr/bin/python3', ['python3', 'scripts/helper.py'])\n", "process/import API"),
            ("from subprocess import *\nrun(['python', 'scripts/helper.py'])\n", "star import"),
            ("import importlib.util\nimportlib.util.spec_from_file_location('h', 'scripts/helper.py')\n", "process/import API"),
            ("exec(open('scripts/helper.py').read())\n", "process/import API"),
            ("import asyncio\nasyncio.create_subprocess_exec('python', 'scripts/helper.py')\n", "process/import API"),
            ("import functools, subprocess\nfunctools.partial(subprocess.run, cwd='support')(['python', 'helper.py'])\n",
             "partial"),
            ("import os, subprocess\nos.environ['PYTHONPATH'] = 'support'\nsubprocess.run(['python', '-m', 'helper'])\n",
             "environment"),
            ("import os, subprocess\nos.environ.update(PYTHONPATH='support')\nsubprocess.run(['python', '-m', 'helper'])\n",
             "environment"),
            ("import contextlib, subprocess\nwith contextlib.chdir('support'):\n    subprocess.run(['python', 'helper.py'])\n",
             "working-directory"),
        )
        for source, diagnostic in failing:
            with self.subTest(source=source):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, "python scripts/start.py")
                    w.write(module, "scripts/start.py", source)
                    w.write(module, "helper.py", "# clean root decoy\n")
                    w.write(module, "support/helper.py", block("python"))
                    w.write(module, "scripts/helper.py", block("python", "script helper"))
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                for row in report["modules"]:
                    self.assertEqual(row["result"], "fail", row)
                    self.assertTrue(any("scripts/start.py:" in error and diagnostic in error for error in row["errors"]), row)

    def test_comments_bom_installed_tools_and_attribute_imports_keep_actual_scope(self):
        w = self.workspace()
        for module in w.paths:
            w.action(module, "python -m pip --version\npython scripts/start.py\npwsh -File scripts/help.ps1\n"
                     "pwsh -File scripts/bom.ps1\npython scripts/bom.py")
            w.write(module, "scripts/start.py", "from os import path\n")
            w.write(module, "scripts/path.py", "# unrelated name of a non-local module attribute\n")
            w.write(module, "scripts/help.ps1", "<#\n.SYNOPSIS\nGets the module's version.\n.EXAMPLE\n"
                    "./scripts/missing.ps1\n#>\n. ./scripts/leaf.ps1\n")
            w.write(module, "scripts/leaf.ps1", block("powershell"))
            w.write(module, "scripts/bom.ps1", "﻿. ./scripts/bomleaf.ps1\n")
            w.write(module, "scripts/bomleaf.ps1", block("powershell", "bom"))
            w.write(module, "scripts/bom.py", "﻿import bomhelper\n")
            w.write(module, "scripts/bomhelper.py", block("python", "bom"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertEqual([row["errors"] for row in report["modules"]], [[], []], report)
        for row in report["modules"]:
            selected = {item["path"] for item in row["files"]}
            self.assertLessEqual({"scripts/leaf.ps1", "scripts/bomleaf.ps1", "scripts/bomhelper.py"}, selected)
            self.assertNotIn("scripts/path.py", selected)
        self.assertTrue(any(row["first"]["path"] == "scripts/bomleaf.ps1" for row in report["findings"]), report)

    def test_composite_uses_follow_local_actions_and_require_pinned_remote_targets(self):
        w = self.workspace()
        for module in w.paths:
            w.write(module, ".github/actions/outer/action.yml", "name: Outer\nruns:\n  using: composite\n  steps:\n"
                    "    - uses: ./.github/actions/inner\n    - uses: actions/checkout@" + "a" * 40 + "\n")
            w.write(module, ".github/actions/inner/action.yaml", "name: Inner\nruns:\n  using: composite\n  steps:\n"
                    "    - shell: bash\n      run: python scripts/helper.py\n")
            w.write(module, "scripts/helper.py", block("python"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertEqual([row["errors"] for row in report["modules"]], [[], []], report)
        self.assertTrue(any(row["first"]["path"] == "scripts/helper.py" for row in report["findings"]), report)
        for target, diagnostic in (("actions/checkout@v4", "unpinned action target"),
                                   ("./.github/actions/missing", "missing/ambiguous local action"),
                                   ("./elsewhere", "missing/ambiguous local action")):
            with self.subTest(target=target):
                w = self.workspace(("Hexalith.Alpha",))
                w.write("Hexalith.Alpha", ".github/actions/outer/action.yml", "name: Outer\nruns:\n  using: composite\n"
                        "  steps:\n    - uses: " + target + "\n")
                w.write("Hexalith.Alpha", "elsewhere/action.yml", "name: Elsewhere\nruns:\n  using: composite\n  steps: []\n")
                w.commit(w.paths["Hexalith.Alpha"])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "fail", report)
                self.assertTrue(any(".github/actions/outer/action.yml:" in error and diagnostic in error
                                    for error in report["modules"][0]["errors"]), report)

    def test_inline_python_action_shell_starts_from_working_directory(self):
        # Imports resolve from every candidate root, including the workspace
        # root, so the root decoy is included beside a working-directory target.
        for extra, target, decoy, included in (("", "helper.py", "scripts/helper.py", False),
                                               ("      working-directory: scripts\n", "scripts/helper.py", "helper.py", True)):
            with self.subTest(working_directory=bool(extra)):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, "import helper", shell="python", extra=extra)
                    w.write(module, target, block("python"))
                    w.write(module, decoy, "# inactive clean import decoy\n")
                    w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertEqual([row["errors"] for row in report["modules"]], [[], []], report)
                for row in report["modules"]:
                    selected = {item["path"] for item in row["files"]}
                    self.assertIn(target, selected)
                    self.assertEqual(decoy in selected, included)
                self.assertTrue(any(row["first"]["path"] == target for row in report["findings"]), report)

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
        # The last field is whether the decoy is a candidate root match. Imports
        # resolve from the invocation roots, the importer's directory, the
        # working directory and the workspace root, and every match counts.
        cases = (
            ("python scripts/start.py", {"scripts/start.py": "from pkg import helper\n"},
             "scripts/pkg/helper.py", "pkg/helper.py", True),
            ("python -m scripts.start", {"scripts/start.py": "import helper\n"},
             "helper.py", "scripts/helper.py", True),
            ("python -c 'import helper'", {}, "helper.py", ".github/actions/dormant/helper.py", True),
            ("python scripts/start.py", {"scripts/start.py": "import package.worker\n",
                                        "scripts/package/__init__.py": "# package\n",
                                        "scripts/package/worker.py": "import helper\n"},
             "scripts/helper.py", "scripts/package/helper.py", True),
            ("python -m package", {"package/__init__.py": "# package\n"},
             "package/__main__.py", "scripts/package/__main__.py", False),
            ("python -m package", {}, "package/__main__.py", "scripts/package/__main__.py", False),
        )
        for command, sources, target, decoy, included in cases:
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
                    self.assertEqual(decoy in {item["path"] for item in row["files"]}, included)
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
        w = self.workspace()
        for module in w.paths:
            w.action(module, "python -m helper", extra="      env:\n        PYTHONPATH: support\n")
            w.write(module, "helper.py", "# root decoy\n")
            w.write(module, "support/helper.py", block("python"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assertEqual(report["result"], "fail", report)
        self.assertTrue(all(any("action.yml:" in error and "step environment" in error for error in row["errors"])
                            for row in report["modules"]), report)

    def test_actual_detector_original_offsets_source_slices_and_summary_ranges(self):
        w = self.workspace()
        target = ".github/actions/dormant/code.py"
        copied = block("python", "original-offset-calibration")
        # A form feed is not a detector line break; it must not shift the slice.
        prefixes = {"Hexalith.Alpha": "import decimal  # \f page\n\n", "Hexalith.Beta": "from fractions import Fraction\n\n\n\n\n"}
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
            source = (w.paths[module] / target).read_text().split("\n")
            self.assertEqual("\n".join(source[endpoint["start"] - 1:endpoint["end"]]), copied.rstrip("\n"))
            self.assertIn(f"{module}/{target}:{expected[module][0]}-{expected[module][1]}", summary)
        # The copied code itself is in an inert top-level fence.
        self.assertIn("\n```python\n" + copied.rstrip("\n") + "\n```\n", summary)
        endpoint = {"module": "Hexalith.Alpha", "path": "a.sh", "start": 1, "end": 2}
        rendered = sc.summary({"result": "fail", "modules": [], "errors": [], "findings": [
            {"format": "bash", "first": endpoint, "second": endpoint | {"module": "Hexalith.Beta"},
             "fragment": "echo ```\n    <b>[link](https://example.invalid)</b>"}]})
        self.assertIn("\n````bash\necho ```\n    <b>[link](https://example.invalid)</b>\n````\n", rendered)

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
            self.assertIn("  - " + error + "\n", (w.output / "summary.md").read_text())

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
        # A real nonzero child exit fails the named boundary without its stderr.
        with self.assertRaises(rt.DeliveryError) as raised:
            self.detector.run([sys.executable, "-c", "import sys; sys.stderr.write('inert-secret'); sys.exit(3)"],
                              "npm signature verification", 20)
        self.assertEqual(str(raised.exception), "npm signature verification failed (exit 3)")

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
        # An empty registry with a tooling failure names the actual cause.
        summary = (w.output / "summary.md").read_text()
        self.assertIn("No registered module was scanned.", summary)
        self.assertIn("- ERROR: detector reported unexpected version", summary)
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
        # An empty SCAN_DIRECTORY is missing output, never the current directory.
        with mock.patch.dict(os.environ, {"SCAN_DIRECTORY": ""}), mock.patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as raised:
                sc.main(["--project-root", str(w.cicd)])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("FAIL", (w.output / "summary.md").read_text())


    def coverage_case(self, items, files, modules=("Hexalith.Alpha", "Hexalith.Beta")):
        w = self.workspace(modules)
        for module in w.paths:
            w.write(module, ".github/actions/dormant/action.yml", steps(*items))
            for path, text in files.items():
                fmt = FORMATS.get(Path(path).suffix, "python")
                w.write(module, path, block(fmt, "copied " + path) if text is COPY else text)
            w.commit(w.paths[module])
        return w.scan(self.factory)

    def assert_coverage(self, report, target, diagnostic):
        """Never pass while copied code sits outside the scanned scope."""
        self.assertEqual(report["result"], "fail", report)
        for row in report["modules"]:
            if diagnostic is None:
                self.assertEqual(row["errors"], [], row)
            else:
                self.assertEqual(row["result"], "fail", row)
                self.assertTrue(any(diagnostic in error for error in row["errors"]), row)
            if target:
                self.assertIn(target, {item["path"] for item in row["files"]}, row)
        if target:
            self.assertTrue(any(row["first"]["path"] == target and row["second"]["path"] == target
                                and row["first"]["module"] != row["second"]["module"]
                                for row in report["findings"]), report)

    def test_review3_reproductions_yield_cross_module_finding_or_named_failure(self):
        for label, items, files, target, diagnostic in A1:
            with self.subTest(case=label):
                self.assert_coverage(self.coverage_case(items, files), target, diagnostic)

    def test_literal_references_include_data_arguments_and_heredoc_bodies(self):
        # A data argument or heredoc body that names a tracked script includes it.
        for command, target in (("chmod +x scripts/x.sh && cat scripts/y.py", "scripts/y.py"),
                                ("chmod +x scripts/x.sh && cat scripts/y.py", "scripts/x.sh"),
                                ("cat > notes.md <<EOF\nRun ./scripts/x.sh manually\nEOF", "scripts/x.sh"),
                                ("echo 'see scripts/y.py' > /dev/null", "scripts/y.py")):
            with self.subTest(command=command, target=target):
                report = self.coverage_case([("bash", command, "")], {"scripts/x.sh": COPY, "scripts/y.py": COPY})
                self.assert_coverage(report, target, None)
        # Literal data naming no tracked script, including heredoc prose, passes.
        for command in ("cat > notes.md <<'EOF'\nDon't run ./scripts/missing.sh manually\nEOF\necho done",
                        "echo 'MODE=fast' >> \"$GITHUB_ENV\"",
                        'export PATH="$HOME/.local/bin:$PATH"',
                        'echo "$HOME/.local/bin" >> "$GITHUB_PATH"',
                        "poetry run pytest -q"):
            with self.subTest(command=command):
                w = self.workspace(("Hexalith.Alpha",))
                w.action("Hexalith.Alpha", command)
                w.write("Hexalith.Alpha", "pyproject.toml", "[tool.poetry.scripts]\nlint = 'helper:main'\n")
                w.commit(w.paths["Hexalith.Alpha"])
                report = w.scan(self.factory)
                self.assertEqual(report["result"], "pass", report)

    def test_unmodeled_environment_and_path_writes_fail(self):
        cases = (
            ('echo "$NAME=support" >> "$GITHUB_ENV"', "bash", "computed environment name"),
            ('echo "PATH=$GITHUB_WORKSPACE/scripts:$PATH" >> "$GITHUB_ENV"', "bash", "$GITHUB_ENV PATH write"),
            ('echo "$GITHUB_WORKSPACE/scripts" >> "$GITHUB_PATH"', "bash", "$GITHUB_PATH change"),
            ('echo "${{ github.action_path }}/bin" >> "$GITHUB_PATH"', "bash", "$GITHUB_PATH change"),
            ("PATH=scripts:$PATH helper.sh", "bash", "PATH change"),
            ("env PATH=./scripts:$PATH helper.sh", "bash", "PATH change"),
            ("export UV_ENV_FILE=.env", "bash", "environment assignment"),
            ("$env:PYTHONPATH = 'support'; python -m helper", "pwsh", "environment assignment"),
            ('$env:PATH = "$PWD/scripts;$env:PATH"', "pwsh", "PATH change"),
            ("Set-Item -Path env:PYTHONPATH -Value support", "pwsh", "environment assignment"),
        )
        for command, shell, diagnostic in cases:
            with self.subTest(command=command):
                report = self.coverage_case([(shell, command, "")], {"support/helper.py": COPY,
                                                                     "scripts/helper.sh": COPY})
                self.assert_coverage(report, None, diagnostic)
        python = (
            ("import os\nwith open(os.environ['GITHUB_ENV'], 'a') as f:\n    f.write('PYTHONPATH=support\\n')\n",
             "access to GITHUB_ENV"),
            ("import os\nos.environ['PATH'] = 'support:' + os.environ['PATH']\n", "environment mutation"),
            ("from dotenv import load_dotenv\nload_dotenv()\n", "env file"),
        )
        for source, diagnostic in python:
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "python scripts/start.py\npython -m helper", "")],
                                            {"scripts/start.py": source, "support/helper.py": COPY})
                self.assert_coverage(report, None, diagnostic)
        report = self.coverage_case([("bash", "python -m helper", "      env:\n        PATH: ${{ github.workspace }}/support\n")],
                                    {"support/helper.py": COPY})
        self.assert_coverage(report, None, "step PATH environment")

    def test_dormant_action_subfolder_uses_owning_action_path(self):
        # C1: the dormant seed's context is the nearest ancestor holding an action.
        report = self.coverage_case([("bash", 'bash "$GITHUB_ACTION_PATH/scripts/run.sh"', "")], {
            ".github/actions/dormant/scripts/run.sh": 'source "$GITHUB_ACTION_PATH/scripts/lib.sh"\n',
            ".github/actions/dormant/scripts/lib.sh": COPY})
        self.assert_coverage(report, ".github/actions/dormant/scripts/lib.sh", None)

    def test_continuations_keep_physical_lines_and_split_only_on_lf(self):
        # C2: backslash continues shell, backtick continues PowerShell, and a
        # logical line keeps its first physical line number.
        for name, source in (("run.sh", "echo a \\\n  b \\\n  c\nfoo\npython missing.py\npython \\\n  other.py\n"),
                             ("run.ps1", "Write-Output a `\n  b `\n  c\nfoo\npython missing.py\npython `\n  other.py\n")):
            with self.subTest(name=name):
                w = self.workspace(("Hexalith.Alpha",))
                w.write("Hexalith.Alpha", ".github/actions/dormant/" + name, source)
                w.commit(w.paths["Hexalith.Alpha"])
                errors = w.scan(self.factory)["modules"][0]["errors"]
                prefix = ".github/actions/dormant/" + name + ":"
                self.assertEqual([error.split(": ", 1)[0] for error in errors], [prefix + "5", prefix + "6"], errors)
                self.assertIn("missing.py", errors[0])
                self.assertIn("other.py", errors[1])
        # Only the shell's own continuation joins lines; C7: only LF splits, a
        # trailing CR is dropped and other separators stay inside the line.
        for name, source in (("cross.ps1", "Write-Output a \\\npython -m helper\n"),
                             ("cross.sh", "echo a\\`\npython -m helper\n"),
                             ("crlf.sh", "echo a\r\npython -m helper\r\n"),
                             ("u2028.sh", "echo x \u2028# ; python -m helper\n"),
                             ("cr.sh", "echo x\r# ; python -m helper\n"),
                             ("ff.sh", "echo x \f# ; python -m helper\n")):
            with self.subTest(name=name):
                report = self.coverage_case([("bash", "true", "")], {".github/actions/dormant/" + name: source,
                                                                     "helper.py": COPY})
                self.assert_coverage(report, "helper.py", None)

    def test_each_composite_step_is_discovered_independently(self):
        # C3: an invalid step is anchored at its own line; later steps continue.
        w = self.workspace()
        for module in w.paths:
            w.write(module, ".github/actions/dormant/action.yml", "name: Steps\nruns:\n  using: composite\n  steps:\n"
                    "    - uses: actions/checkout@v4\n    - shell: bash\n      run: python -m helper\n")
            w.write(module, "helper.py", block("python", "later step"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assert_coverage(report, "helper.py", ".github/actions/dormant/action.yml:5: invalid action/discovery: "
                             "unresolved or unpinned action target")

    def test_powershell_block_comments_are_removed_anywhere(self):
        # C8: inline and multi-line <# ... #> comments keep the line count.
        report = self.coverage_case([("pwsh", "Write-Output x <# note #> ; python -m helper", "")], {"helper.py": COPY})
        self.assert_coverage(report, "helper.py", None)
        w = self.workspace(("Hexalith.Alpha",))
        w.write("Hexalith.Alpha", ".github/actions/dormant/run.ps1",
                "Write-Output x <# a\nb #> ; Write-Output y\npython missing.py\n")
        w.commit(w.paths["Hexalith.Alpha"])
        errors = w.scan(self.factory)["modules"][0]["errors"]
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(errors[0].startswith(".github/actions/dormant/run.ps1:3: "), errors)

    def test_command_lookup_probe_and_sys_executable_interpreter(self):
        # C9: command -v/-V is a non-executing probe. C10: sys.executable, and
        # any alias of it, as argv[0] is the Python interpreter.
        for command in ("if command -v jq >/dev/null; then python -m helper; fi",
                        "command -V jq && python -m helper"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {"helper.py": COPY}), "helper.py", None)
        for source in ("import subprocess, sys\nsubprocess.run([sys.executable, '-m', 'helper'])\n",
                       "import subprocess, sys\npy = sys.executable\nsubprocess.check_call((py, '-m', 'helper'))\n",
                       "import subprocess\nfrom sys import executable as python\nsubprocess.run([python, '-m', 'helper'])\n"):
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "python scripts/start.py", "")],
                                            {"scripts/start.py": source, "helper.py": COPY})
                self.assert_coverage(report, "helper.py", None)

    def test_followed_wrapper_and_recursive_interpreter_forms(self):
        # C11: module-form children are reachable only through the recognized layer.
        for command, shell in (("echo x | xargs python -m helper", "bash"),
                               ("flock /tmp/scan.lock python -m helper", "bash"),
                               ("bash -c 'python -m helper'", "bash"),
                               ("pwsh -Command 'python -m helper'", "bash"),
                               ("pwsh -Command python -m helper", "pwsh"),
                               ("uv run --with requests python -m helper", "bash")):
            with self.subTest(command=command):
                report = self.coverage_case([(shell, command, "")], {"helper.py": COPY})
                self.assert_coverage(report, "helper.py", None)

    def test_followed_python_process_and_import_apis(self):
        # C12: each recognized API reaches a module that no path literal names.
        for source in ("import os\nos.system('python -m helper')\n",
                       "import subprocess\nsubprocess.Popen(['python', '-m', 'helper']).wait()\n",
                       "import subprocess\nsubprocess.call(['python', '-m', 'helper'])\n",
                       "import subprocess\nsubprocess.check_output(['python', '-m', 'helper'])\n",
                       "import subprocess\nsubprocess.getstatusoutput('python -m helper')\n",
                       "import runpy\nrunpy.run_module('helper')\n",
                       "__import__('helper')\n"):
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "python scripts/start.py", "")],
                                            {"scripts/start.py": source, "helper.py": COPY})
                self.assert_coverage(report, "helper.py", None)

    def test_python_resolution_and_execution_apis_fail(self):
        # C13: each failure is pinned by its own diagnostic.
        cases = (
            ("import os\nos.chdir('scripts')\n", "working-directory mutation"),
            ("import os\nos.putenv('PYTHONPATH', 'support')\n", "environment mutation"),
            ("import os\nos.environ.setdefault('PYTHONPATH', 'support')\n", "environment mutation"),
            ("import os\nos.spawnl(os.P_WAIT, '/usr/bin/python3', 'python3', '-m', 'helper')\n",
             "process/import API: os.spawnl"),
            ("import os\nos.posix_spawn('/usr/bin/python3', ['python3', '-m', 'helper'], {})\n",
             "process/import API: os.posix_spawn"),
            ("from importlib.machinery import SourceFileLoader\nSourceFileLoader('h', 'support/helper.py').load_module()\n",
             "process/import API: importlib.machinery.SourceFileLoader"),
            ("exec(compile(open('support/helper.py').read(), 'h', 'exec'))\n", "process/import API: compile"),
        )
        for source, diagnostic in cases:
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "python scripts/start.py", "")],
                                            {"scripts/start.py": source, "support/helper.py": COPY})
                self.assert_coverage(report, None, diagnostic)
                for row in report["modules"]:
                    self.assertTrue(any(error.startswith("scripts/start.py:") and diagnostic in error
                                        for error in row["errors"]), row)
        report = self.coverage_case([("bash", "python -m pkg.missing", "")], {"pkg/__init__.py": COPY})
        self.assert_coverage(report, None, "missing local Python module: pkg.missing")

    def test_extensionless_shebang_action_source_is_scanned(self):
        # C14: an extensionless file directly beneath .github/actions/** with a
        # supported shebang is an initial source.
        w = self.workspace()
        for module in w.paths:
            w.write(module, ".github/actions/dormant/tool", "#!/usr/bin/env bash\n" + block("bash", "shebang"))
            w.commit(w.paths[module])
        report = w.scan(self.factory)
        self.assert_coverage(report, ".github/actions/dormant/tool", None)
        self.assertTrue(all(row["format"] == "bash" for row in report["findings"]), report)

    def test_namespace_package_inside_regular_package_runs_ancestor_initializer(self):
        # C6: every ancestor __init__.py of an imported namespace package runs.
        for source, child in (("from pkg.ns import helper\n", True), ("import pkg.ns\n", False)):
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": source, "scripts/pkg/__init__.py": COPY,
                    "scripts/pkg/ns/helper.py": "# namespace child\n"})
                self.assert_coverage(report, "scripts/pkg/__init__.py", None)
                for row in report["modules"]:
                    self.assertEqual("scripts/pkg/ns/helper.py" in {item["path"] for item in row["files"]}, child)

    def test_module_operands_behind_unrecognized_consumers_are_included(self):
        # Rule 1 for module names: a literal -m operand, or a module that a
        # literal -c operand imports, is included whatever consumes it.
        shell = (
            ("bash", "xvfb-run python -m helper", "helper.py"),
            ("bash", "retry --times 3 -- bash -c 'python -m helper'", "helper.py"),
            ("bash", "xvfb-run python -c 'import helper'", "helper.py"),
            ("bash", "xvfb-run python -m pkg", "pkg/__main__.py"),
            ("bash", "cat <<EOF | parallel\npython -m helper\nEOF", "helper.py"),
            ("bash", "python -m cProfile -m helper", "helper.py"),
            ("pwsh", "Start-Job { python -m helper } | Wait-Job", "helper.py"),
            ("pwsh", "1..2 | ForEach-Object { python -m helper }", "helper.py"),
        )
        for command_shell, command, target in shell:
            with self.subTest(command=command):
                report = self.coverage_case([(command_shell, command, "")], {
                    "helper.py": COPY, "pkg/__init__.py": "# package\n", "pkg/__main__.py": COPY})
                self.assert_coverage(report, target, None)
                for row in report["modules"]:
                    if target.startswith("pkg/"):
                        self.assertIn("pkg/__init__.py", {item["path"] for item in row["files"]})
        python = (
            "import sys\nsys.modules['subprocess'].run(['python', '-m', 'helper'])\n",
            "__import__('subprocess').run(['python', '-m', 'helper'])\n",
            "import importlib\nimportlib.import_module('subprocess').call('python -m helper', shell=True)\n",
            "import sh\nsh.python('-m', 'helper')\n",
            "import subprocess\nsubprocess.run(['xvfb-run', 'python', '-c', 'import helper'])\n",
            "import os\nos.system(\"xvfb-run python -c 'from helper import main; main()'\")\n",
        )
        for source in python:
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "python scripts/start.py", "")],
                                            {"scripts/start.py": source, "helper.py": COPY})
                self.assert_coverage(report, "helper.py", None)

    def test_cross_language_execution_positions_fail(self):
        # From an execution position, a tracked script in another language fails.
        tool = "#!/usr/bin/env python3\n" + block("python", "copied tool")
        mixed = "#!/usr/bin/env python3\n" + block("bash", "copied mixed")
        cases = (
            ("bash", "bash scripts/helper.py", "scripts/helper.py", "cross-language script invocation: scripts/helper.py"),
            ("bash", "python scripts/helper.sh", "scripts/helper.sh", "cross-language script invocation: scripts/helper.sh"),
            ("bash", "pwsh -File scripts/helper.sh", "scripts/helper.sh", "cross-language script invocation"),
            ("bash", "source scripts/helper.py", "scripts/helper.py", "cross-language script invocation"),
            ("bash", ". ./scripts/helper.ps1", "scripts/helper.ps1", "cross-language script invocation"),
            ("pwsh", ". ./scripts/helper.sh", "scripts/helper.sh", "cross-language script invocation"),
            ("bash", "uv run --script scripts/helper.sh", "scripts/helper.sh", "cross-language script invocation"),
            ("bash", "bash scripts/tool", "scripts/tool", "cross-language script invocation: scripts/tool"),
            ("bash", "./scripts/mixed.sh", "scripts/mixed.sh", "ambiguous script language: scripts/mixed.sh"),
        )
        for shell, command, target, diagnostic in cases:
            with self.subTest(command=command):
                report = self.coverage_case([(shell, command, "")], {
                    "scripts/helper.py": COPY, "scripts/helper.sh": COPY, "scripts/helper.ps1": COPY,
                    "scripts/tool": tool, "scripts/mixed.sh": mixed})
                self.assert_coverage(report, target, diagnostic)
        report = self.coverage_case([("bash", "python scripts/start.py", "")], {
            "scripts/start.py": "import runpy\nrunpy.run_path('scripts/helper.sh')\n", "scripts/helper.sh": COPY})
        self.assert_coverage(report, "scripts/helper.sh", "scripts/start.py:2: local-script discovery: unsupported "
                             "cross-language script invocation")
        # uv run --script runs its target as Python, so an extensionless PEP 723
        # script without a shebang is reached through the recognized call.
        report = self.coverage_case([("bash", "uv run --script scripts/inline", "")], {
            "scripts/inline": "# /// script\n# ///\n" + block("python", "copied inline")})
        self.assert_coverage(report, "scripts/inline", None)
        self.assertTrue(all(row["format"] == "python" for row in report["findings"]), report)

    def test_python_environment_mapping_writes_fail(self):
        for source in ("import os\nos.environ |= {'PYTHONPATH': 'support'}\n",
                       "import os\nos.environ = {'PYTHONPATH': 'support'}\n",
                       "from os import environ\nenviron |= {'PYTHONPATH': 'support'}\n",
                       "import os\nos.environb[b'PYTHONPATH'] = b'support'\n",
                       "import os\nos.environb.update({b'PYTHONPATH': b'support'})\n"):
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "python scripts/start.py\npython -m helper", "")], {
                    "scripts/start.py": source, "support/helper.py": COPY, "helper.py": "# root decoy\n"})
                self.assert_coverage(report, None, "scripts/start.py:2: local-script discovery: unsupported Python "
                                     "environment mutation affecting resolution")
        # Rebinding a plain alias and reading the mapping change no environment.
        w = self.workspace(("Hexalith.Alpha",))
        w.action("Hexalith.Alpha", "python scripts/start.py")
        w.write("Hexalith.Alpha", "scripts/start.py", "from os import environ\nenviron = dict(environ, MODE='x')\n")
        w.commit(w.paths["Hexalith.Alpha"])
        self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_runners_with_tracked_recipes_or_tests_fail(self):
        config = "repos:\n- repo: local\n  hooks:\n  - id: helper\n    entry: python helper.py\n    language: system\n"
        cases = (
            ("pre-commit run --all-files", {".pre-commit-config.yaml": config},
             "unsupported task runner with tracked module recipes: pre-commit"),
            ("python -m pre_commit run", {".pre-commit-config.yaml": config},
             "unsupported task runner with tracked module recipes: pre-commit"),
            ("python -m tox -c ci.ini", {"ci.ini": "[testenv]\ncommands = python helper.py\n"},
             "unsupported task runner recipe location: tox"),
            ("pytest tests", {"tests/test_helper.py": "import helper\n"},
             "unsupported test runner with tracked module tests: pytest"),
            ("python -m pytest -q", {"tests/conftest.py": "import helper\n"},
             "unsupported test runner with tracked module tests: pytest"),
            ("uv run pytest", {"helper_test.py": "import helper\n"},
             "unsupported test runner with tracked module tests: pytest"),
            ("python -m unittest discover -s tests", {"tests/test_helper.py": "import helper\n"},
             "unsupported test runner with tracked module tests: unittest"),
        )
        for command, files, diagnostic in cases:
            with self.subTest(command=command):
                report = self.coverage_case([("bash", command, "")], files | {"helper.py": COPY})
                self.assert_coverage(report, None, diagnostic)
        # Without tracked recipes or tests these runners execute no module file.
        for command in ("pytest --version", "python -m pytest --version", "pre-commit --version"):
            with self.subTest(command=command):
                w = self.workspace(("Hexalith.Alpha",))
                w.action("Hexalith.Alpha", command)
                w.commit(w.paths["Hexalith.Alpha"])
                self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_module_user_and_directory_search_paths_fail(self):
        # PSModulePath, PYTHONUSERBASE and CDPATH redirect name-based lookup.
        cases = (
            ("bash", "export PSModulePath=./modules; pwsh -Command 'Import-Module helper'", "",
             "environment assignment affecting script resolution"),
            ("pwsh", '$env:PSModulePath = "./modules;" + $env:PSModulePath; Import-Module helper', "",
             "environment assignment affecting script resolution"),
            ("bash", "pwsh -Command 'Import-Module helper'", "      env:\n        PSModulePath: ./modules\n",
             "step environment affecting script resolution"),
            ("bash", "export PYTHONUSERBASE=./local; python -m helper", "",
             "environment assignment affecting script resolution"),
            ("bash", "CDPATH=scripts; cd sub && python helper.py", "",
             "environment assignment affecting script resolution"),
        )
        for shell, command, extra, diagnostic in cases:
            with self.subTest(command=command):
                report = self.coverage_case([(shell, command, extra)], {
                    "modules/helper/helper.psm1": COPY, "local/lib/python3.12/site-packages/helper.py": COPY,
                    "scripts/sub/helper.py": COPY})
                self.assert_coverage(report, None, diagnostic)

    def test_review4_children_retain_all_working_directory_contexts(self):
        # D1: selection alone is insufficient; even previously selected children
        # must be traversed under every established invocation cwd.
        cases = (
            ("cd support; xvfb-run python ../scripts/start.py", {
                "scripts/start.py": "import subprocess\nsubprocess.run(['python', '-m', 'helper'])\n",
                "support/helper.py": COPY}, "support/helper.py"),
            ("cd work; xvfb-run ../scripts/start.sh", {
                "scripts/start.sh": "python -m helper\n", "work/helper.py": COPY}, "work/helper.py"),
            ("cat scripts/start.py\ncd support; xvfb-run python ../scripts/start.py", {
                "scripts/start.py": "import subprocess\nsubprocess.run(['python', '-m', 'helper'])\n",
                "support/helper.py": COPY}, "support/helper.py"),
        )
        for command, files, target in cases:
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], files), target, None)

    def test_review4_successive_conditional_directories_extend_every_candidate(self):
        # D2: b and a/b are both possible after the second literal cd.
        report = self.coverage_case([("bash", "if false; then cd a; fi\ncd b; python -m helper", "")], {
            "b/helper.py": COPY, "a/b/helper.py": "# conditional decoy\n"})
        self.assert_coverage(report, "b/helper.py", None)

    def test_review4_quoted_powershell_comment_delimiters_are_data(self):
        # D3: only unquoted delimiters remove comments; physical lines survive.
        for command in ("Write-Output '<#'; python -m helper; Write-Output '#>'",
                        'Write-Output "<#"; python -m helper; Write-Output "#>"',
                        "Write-Output '<#'; <# actual\ncomment #> python -m helper; Write-Output '#>'",
                        'Write-Output @"\nliteral " <#\n"@\npython -m helper'):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("pwsh", command, "")], {"helper.py": COPY}),
                                     "helper.py", None)
        report = self.coverage_case([("pwsh", "Write-Output '<#'\n<# actual\ncomment #>\npython missing.py", "")],
                                    {"helper.py": COPY})
        self.assert_coverage(report, None, "action.yml:9: local-script discovery: missing or unsafe")

    def test_review4_hidden_computed_interpreter_operands_fail(self):
        # D4: an unknown outer consumer does not erase an execution position.
        for command in ('xvfb-run python "${{ inputs.script }}"', 'xvfb-run python -m "$MODULE"',
                        'xvfb-run env python "${{ inputs.script }}"'):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {"helper.py": COPY}),
                                     None, "unresolved local")
        for command in ('xvfb-run "$COMMAND"', 'xvfb-run env "$COMMAND"'):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {"helper.py": COPY}),
                                     None, "unresolved computed")
        for command in ('echo "python $DATA"', 'printf "%s" "python ${INPUT}"',
                        'cat "$INPUT"'):
            with self.subTest(data=command):
                w = self.workspace(("Hexalith.Alpha",))
                w.action("Hexalith.Alpha", command)
                w.commit(w.paths["Hexalith.Alpha"])
                self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_review4_reflected_builtin_and_imported_namespaces_fail(self):
        # D5/D6: retain namespace identity, including modules returned by imports.
        sources = (
            "import builtins\nbuiltins.__dict__['__import__']('helper')\n",
            "import builtins as b\nb.__dict__['__import__']('helper')\n",
            "__builtins__['__import__']('helper')\n",
            "import sys\ngetattr(__import__('subprocess'), 'run')(['python', '-m', sys.argv[1]])\n",
            "import importlib, sys\ngetattr(importlib.import_module('subprocess'), 'run')"
            "(['python', '-m', sys.argv[1]])\n",
        )
        for source in sources:
            with self.subTest(source=source):
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": source, "scripts/helper.py": COPY}), None, "unsupported reflective")
        self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py", "")], {
            "scripts/start.py": "import builtins\nbuiltins.__import__('helper')\n", "scripts/helper.py": COPY}),
            "scripts/helper.py", None)

    def test_review4_complete_environment_output_is_validated(self):
        # D7: another literal key cannot certify computed emitted output.
        for command in ('printf "X=1\\n%s" "$CONFIG" >> "$GITHUB_ENV"',
                        'printf \'%s\\n\' MODE=fast "$NAME=support" >> "$GITHUB_ENV"'):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {"support/helper.py": COPY}),
                                     None, "computed environment name or output")
        w = self.workspace(("Hexalith.Alpha",))
        w.action("Hexalith.Alpha", 'printf \'%s\\n\' MODE=fast X=1 >> "$GITHUB_ENV"')
        w.commit(w.paths["Hexalith.Alpha"])
        self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_review4_ignore_scripts_does_not_suppress_named_npm_scripts(self):
        # D8: --ignore-scripts suppresses lifecycle hooks, not npm run's target.
        for command in ("npm run go --ignore-scripts", "npm --ignore-scripts run lint"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "package.json": '{"scripts":{"go":"python -m helper","lint":"python -m helper"}}',
                    "helper.py": COPY}), None, "missing or unsafe npm/config input: package-lock.json")
        for command in ("npm --ignore-scripts --version", "npm view jscpd version", "npm ci --ignore-scripts"):
            with self.subTest(probe=command):
                w = self.workspace(("Hexalith.Alpha",))
                w.action("Hexalith.Alpha", command)
                w.write("Hexalith.Alpha", "package.json", '{"scripts":{"lint":"python -m helper"}}')
                w.commit(w.paths["Hexalith.Alpha"])
                self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_review4_project_build_backends_fail_without_execution(self):
        # D9: build backends are executable tracked project code.
        for command in ("uv build", "poetry build", "pdm build", "hatch build"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "pyproject.toml": '[build-system]\nrequires=[]\nbuild-backend="backend"\nbackend-path=["support"]\n',
                    "support/backend.py": COPY}), None, "unsupported project runner with tracked module build/recipes")

    def test_review4_inline_namespace_import_includes_regular_ancestors(self):
        # D10: a namespace itself has no initializer, but its regular parent does.
        self.assert_coverage(self.coverage_case([("bash", 'xvfb-run python -c "import pkg.ns"', "")], {
            "pkg/__init__.py": COPY, "pkg/ns/leaf.py": "# namespace member\n"}), "pkg/__init__.py", None)

    def test_review4_expanding_heredocs_cannot_hide_execution(self):
        # D11: unquoted heredocs expand even though their bodies are not commands.
        for body in ("$(cd support; python -m helper)", '$(python -m "$MODULE")', "`python -m helper`"):
            with self.subTest(body=body):
                self.assert_coverage(self.coverage_case([("bash", "cat > notes.md <<EOF\n" + body + "\nEOF", "")],
                                                       {"support/helper.py": COPY}),
                                     None, "action.yml:7: local-script discovery: unsupported expanding heredoc execution")
        # A quoted delimiter suppresses expansion while retaining literal references.
        self.assert_coverage(self.coverage_case([("bash", "cat <<'EOF'\n$(python scripts/helper.py)\nEOF", "")],
                                               {"scripts/helper.py": COPY}), "scripts/helper.py", None)

    def test_review4_read_cannot_mutate_resolution_names(self):
        # D12: builtin input assignment changes resolution just like an export.
        for command in ("read -r PATH <<<support; helper", "read PYTHONPATH", 'read -r "$NAME"',
                        "read -aPATH <<<support; helper", "read -raPATH <<<support; helper"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "support/helper": "#!/usr/bin/env python3\n" + block("python")}),
                    None, "unsupported read environment mutation")
        w = self.workspace(("Hexalith.Alpha",))
        w.action("Hexalith.Alpha", "read -r MODE <<<fast")
        w.commit(w.paths["Hexalith.Alpha"])
        self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_review4_over_limit_inline_execution_fails_visibly(self):
        # D13: never silently discard a bounded execution-bearing literal.
        command = "xvfb-run python -c '" + "x=0;" * 1100 + "import helper'"
        self.assert_coverage(self.coverage_case([("bash", command, "")], {"helper.py": COPY}),
                             None, "execution literal coverage limit exceeded")

    def test_review4_module_form_project_runners_apply_recipe_guard(self):
        # D14: installed -m entrypoints have the same recipe guard as CLI tools.
        for command in ("python -m poetry run lint", "python -m pdm run lint", "python -m hatch run lint"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "pyproject.toml": '[project.scripts]\nlint="helper:main"\n', "helper.py": COPY}),
                    None, "unsupported task runner with tracked module recipes")

    def test_review4_shell_startup_sources_fail_explicitly(self):
        # D15: an interactive shell startup file is an executing source.
        for option in ("--rcfile", "--init-file"):
            with self.subTest(option=option):
                self.assert_coverage(self.coverage_case([("bash", "bash " + option + " setup.rc -ic true", "")], {
                    "setup.rc": "python -m helper\n", "helper.py": COPY}),
                    None, "unsupported shell startup source option")

    def test_review4_unsafe_imports_fail_instead_of_disappearing(self):
        # D16: a found symlink or gitlink import is unsafe, not a non-local module.
        for kind in ("symlink", "gitlink"):
            with self.subTest(kind=kind):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, "python scripts/start.py")
                    w.write(module, "scripts/start.py", "import helper\n")
                    w.write(module, "support/helper.py", block("python"))
                    if kind == "symlink":
                        (w.paths[module] / "scripts/helper.py").symlink_to("../support/helper.py")
                        w.commit(w.paths[module])
                    else:
                        w.commit(w.paths[module])
                        revision = git(w.paths[module], "rev-parse", "HEAD")
                        git(w.paths[module], "update-index", "--add", "--cacheinfo", "160000," + revision + ",scripts/helper.py")
                        git(w.paths[module], "commit", "--quiet", "-m", "unsafe import")
                self.assert_coverage(w.scan(self.factory), None, "missing or unsafe regular script/action: scripts/helper.py")

    def test_review4_uv_project_recipe_root_changes_fail(self):
        # D17: do not search the caller's recipes after discarding --project.
        for command in ("uv run --project tools lint", "uv --project=tools run lint"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "tools/pyproject.toml": '[project.scripts]\nlint="helper:main"\n', "tools/helper.py": COPY}),
                    None, "unsupported uv project recipe-root option")

    def test_review4_action_input_default_and_step_with_scalars_include_copied_scripts(self):
        # D18: these YAML scalars are the sole references to the copied helper.
        for field in ("input-default", "step-with"):
            with self.subTest(field=field):
                w = self.workspace()
                for module in w.paths:
                    action = "name: Dormant\n"
                    if field == "input-default":
                        action += "inputs:\n  script:\n    default: scripts/helper.py\n"
                    action += "runs:\n  using: composite\n  steps:\n"
                    if field == "step-with":
                        action += ("    - uses: owner/action@" + "a" * 40 +
                                   "\n      with:\n        script: scripts/helper.py\n")
                    else:
                        action += "    - shell: bash\n      run: echo ready\n"
                    w.write(module, ".github/actions/dormant/action.yml", action)
                    w.write(module, "scripts/helper.py", block("python"))
                    w.commit(w.paths[module])
                self.assert_coverage(w.scan(self.factory), "scripts/helper.py", None)

    def test_review6_returned_process_namespaces_fail_even_as_attribute_receivers(self):
        # R1: a namespace returned by an import retains execution identity even
        # when the receiver is an Attribute rather than getattr or an assignment.
        for expression in ("__import__('subprocess')", "importlib.import_module('subprocess')"):
            with self.subTest(expression=expression):
                source = "import sys, importlib\n" + expression + ".run(['python3', '-m', sys.argv[1]])\n"
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py support.helper", "")], {
                    "scripts/start.py": source, "support/helper.py": COPY}), None,
                    "scripts/start.py:2: local-script discovery: unresolved computed Python script invocation")
        for namespace in ("sys.modules['subprocess']", "s.modules['subprocess']"):
            with self.subTest(namespace=namespace):
                source = ("import sys\nimport sys as s\n" + namespace +
                          ".run(['python', '-m', sys.argv[1]])\n")
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py helper", "")], {
                    "scripts/start.py": source, "helper.py": COPY}), None,
                    "scripts/start.py:3: local-script discovery: unresolved computed Python script invocation")

    def test_review6_nested_builtin_namespace_reflection_fails(self):
        # R11: do not exempt a namespace because another Attribute follows it.
        for expression in ("builtins.__dict__.get('__import__')('helper')",
                           "builtins.__dict__.__getitem__('__import__')('helper')",
                           "__builtins__.__dict__.get('__import__')('helper')"):
            with self.subTest(expression=expression):
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": "import builtins\n" + expression + "\n", "scripts/helper.py": COPY}),
                    None, "scripts/start.py:2: local-script discovery: unsupported reflective")

    def unsafe_import_case(self, kind, unsafe, source, *, child=False):
        w = self.workspace()
        for module in w.paths:
            w.action(module, "python scripts/start.py")
            w.write(module, "scripts/start.py", source)
            w.write(module, "support/helper.py", block("python"))
            if child:
                w.write(module, "scripts/pkg/helper.py", "# regular imported child\n")
            target = w.paths[module] / unsafe
            target.parent.mkdir(parents=True, exist_ok=True)
            if kind == "symlink":
                target.symlink_to("../support" if unsafe == "scripts/pkg" else (
                    "../support/helper.py" if unsafe == "scripts/helper.py" else "../../support/helper.py"))
                w.commit(w.paths[module])
            else:
                w.commit(w.paths[module])
                revision = git(w.paths[module], "rev-parse", "HEAD")
                git(w.paths[module], "update-index", "--add", "--cacheinfo", "160000," + revision + "," + unsafe)
                git(w.paths[module], "commit", "--quiet", "-m", "unsafe import")
        return w.scan(self.factory)

    def test_review6_intermediate_unsafe_import_paths_fail(self):
        # R2: final-path absence cannot turn a tracked symlink/gitlink ancestor
        # into an installed non-local module.
        for kind in ("symlink", "gitlink"):
            with self.subTest(kind=kind):
                self.assert_coverage(self.unsafe_import_case(kind, "scripts/pkg", "import pkg.helper\n"), None,
                                     "scripts/start.py:1: local-script discovery: unsafe non-directory Python import")

    def test_review6_literal_import_fallback_validates_unsafe_paths(self):
        # R3: unknown process consumers still validate every literal import,
        # including its leaf, intermediate directories and initializers.
        for kind in ("symlink", "gitlink"):
            for unsafe, module, child in (("scripts/helper.py", "helper", False),
                                           ("scripts/pkg", "pkg.helper", False),
                                           ("scripts/pkg/__init__.py", "pkg.helper", True)):
                for consumer in ("sys.modules['subprocess']", "runner"):
                    with self.subTest(kind=kind, unsafe=unsafe, consumer=consumer):
                        source = ("import sys, subprocess\n" + consumer + ".run(['python3', '-c', "
                                  + repr("import " + module) + "], cwd='scripts')\n")
                        diagnostic = "unsafe non-directory Python import" if unsafe == "scripts/pkg" else (
                            "missing or unsafe regular script/action: " + unsafe)
                        self.assert_coverage(self.unsafe_import_case(kind, unsafe, source, child=child), None,
                                             "scripts/start.py:2: local-script discovery: " + diagnostic)

    def test_review6_unsafe_ancestor_initializers_fail_for_regular_children(self):
        # R16: changing add_module's ancestor membership check to regular(init)
        # must not let the regular child certify its unsafe initializer.
        for kind in ("symlink", "gitlink"):
            with self.subTest(kind=kind):
                self.assert_coverage(self.unsafe_import_case(kind, "scripts/pkg/__init__.py",
                                                            "import pkg.helper\n", child=True), None,
                                     "scripts/start.py:1: local-script discovery: missing or unsafe regular "
                                     "script/action: scripts/pkg/__init__.py")

    def test_review6_project_preparation_fails_before_a_harmless_child(self):
        # R4: uv may build the local project before running python -c pass.
        project = ('[project]\nname="probe"\nversion="1.0"\n[build-system]\nrequires=[]\n'
                   'build-backend="backend"\nbackend-path=["support"]\n')
        for command in ("uv run --offline python -c pass", "python -m uv run --offline python -c pass",
                        "uv run python -c pass --no-sync", "uv run python -c pass --no-project",
                        "poetry run python -c pass", "pdm run python -c pass", "hatch run python -c pass"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "pyproject.toml": project, "support/backend.py": COPY}), None,
                    "unsupported local project preparation with tracked build backend")
        for command in ("uv --version", "uv run --no-project python -c pass", "uv run --no-sync python -c pass"):
            with self.subTest(probe=command):
                w = self.workspace(("Hexalith.Alpha",))
                w.action("Hexalith.Alpha", command)
                w.write("Hexalith.Alpha", "pyproject.toml", project)
                w.write("Hexalith.Alpha", "support/backend.py", block("python"))
                w.commit(w.paths["Hexalith.Alpha"])
                self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_review6_runner_locations_are_checked_before_option_values(self):
        # R5/R14: selector values such as info cannot masquerade as safe probes.
        for command in ("npm --prefix info run lint", "npm --prefix=info run lint", "pnpm --dir info run lint",
                        "yarn --cwd info run lint", "python -m poetry --directory tools run lint",
                        "poetry --directory tools run lint", "pdm --project tools run lint"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "info/package.json": '{"scripts":{"lint":"python3 -m helper"}}', "info/helper.py": COPY,
                    "tools/pyproject.toml": '[tool.poetry.scripts]\nlint="helper:main"\n',
                    "tools/helper.py": COPY}), None, "missing or unsafe npm/config input: info/package-lock.json" if command.startswith("npm")
                                     else "unsupported task runner recipe location")
        for command in ("npm info jscpd", "npm --version", "npm audit signatures"):
            with self.subTest(probe=command):
                w = self.workspace(("Hexalith.Alpha",))
                w.action("Hexalith.Alpha", command)
                w.write("Hexalith.Alpha", "package.json", '{"scripts":{"lint":"python -m helper"}}')
                w.commit(w.paths["Hexalith.Alpha"])
                self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_review6_environment_marker_output_is_not_a_destination(self):
        # R6: only the actual redirect destination is exempt from output checks.
        for value in ("$CONFIG$GITHUB_ENV", "GITHUB_ENV$CONFIG", "${GITHUB_ENV}$CONFIG"):
            with self.subTest(value=value):
                command = 'printf "MODE=fast\\n%s" "' + value + '" >> "$GITHUB_ENV"'
                self.assert_coverage(self.coverage_case([("bash", command, ""), ("bash", "python -m helper", "")],
                                                       {"support/helper.py": COPY}), None,
                                     "computed environment name or output")

    def test_review6_environment_heredoc_output_cannot_use_a_prefix_assignment(self):
        # R7: MODE belongs to cat's environment, not its emitted heredoc body.
        command = 'MODE=fast cat >> "$GITHUB_ENV" <<EOF\nPYTHONPATH=support\nEOF\npython3 -m helper'
        self.assert_coverage(self.coverage_case([("bash", command, "")], {"support/helper.py": COPY}), None,
                             "action.yml:6: local-script discovery: unsupported $GITHUB_ENV write output producer")

    def test_review6_formatted_environment_output_cannot_hide_keys(self):
        # R8: exact octal and %b/hex review fixtures must fail without execution.
        for command in ("printf 'MODE=fast\\n\\120YTHONPATH=support\\n' >> \"$GITHUB_ENV\"",
                        "printf '%b' 'MODE=fast\\x0aPYTHONPATH=support\\x0a' >> \"$GITHUB_ENV\"",
                        "printf '%s\\n' MODE=fast PYTHONPATH=support >> \"$GITHUB_ENV\""):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, ""), ("bash", "python -m helper", "")],
                                                       {"support/helper.py": COPY}), None, "$GITHUB_ENV")
        for command in ("printf 'MODE=fast\\n' >> \"$GITHUB_ENV\"",
                        "printf '%s\\n' MODE=fast X=1 >> \"$GITHUB_ENV\"",
                        "echo MODE=fast >> \"$GITHUB_ENV\""):
            with self.subTest(literal=command):
                w = self.workspace(("Hexalith.Alpha",))
                w.action("Hexalith.Alpha", command)
                w.commit(w.paths["Hexalith.Alpha"])
                self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_review6_expanding_heredoc_continuations_preserve_execution_diagnostics(self):
        # R9: fold backslash-newline before recognizing the resulting $(...).
        for target in ("helper", '"$MODULE"'):
            with self.subTest(target=target):
                command = "cat <<EOF\n$\\\n(cd support; python3 -m " + target + ")\nEOF"
                self.assert_coverage(self.coverage_case([("bash", command, "")], {"support/helper.py": COPY}), None,
                                     "action.yml:7: local-script discovery: unsupported expanding heredoc execution")
        # Quoted heredocs preserve the backslash and remain literal data.
        w = self.workspace(("Hexalith.Alpha",))
        w.action("Hexalith.Alpha", "cat <<'EOF'\n$\\\n(python -m \"$MODULE\")\nEOF")
        w.commit(w.paths["Hexalith.Alpha"])
        self.assertEqual(w.scan(self.factory)["result"], "pass")

    def test_review6_double_quoted_powershell_here_strings_expand(self):
        # R10: double-quoted here strings execute subexpressions; single quotes
        # retain data and literal script references without execution parsing.
        command = 'Write-Output @"\n$(Set-Location support; python3 -m helper)\n"@'
        self.assert_coverage(self.coverage_case([("pwsh", command, "")], {"support/helper.py": COPY}), None,
                             "action.yml:7: local-script discovery: unsupported expanding heredoc execution")
        self.assert_coverage(self.coverage_case([("pwsh", "Write-Output @'\n$(python scripts/helper.py)\n'@", "")],
                                               {"scripts/helper.py": COPY}), "scripts/helper.py", None)

    def test_review6_indexed_read_destinations_fail(self):
        # R12: an array subscript does not change the resolution-variable name.
        for command in ("read PATH[0]", "read -r 'PATH[0]' <<<support; helper", "read PYTHONPATH[1]",
                        "read -a 'PATH[0]' <<<support", 'read "${NAME}[0]"'):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "support/helper": "#!/usr/bin/env python3\n" + block("python")}), None,
                    "unsupported read environment mutation")

    def test_review6_literal_fallback_limits_fail_at_the_source(self):
        # R13: both known namespaces and unknown consumers reach the sequence bound.
        for consumer, operands in (("sys.modules['subprocess']", ["python", "-c", "x=0;" * 1100 + "import helper"]),
                                   ("runner", ["python", "-c", "x=0;" * 1100 + "import helper"]),
                                   ("runner", ["python", "-c" + "x=0;" * 1100 + "import helper"])):
            with self.subTest(consumer=consumer, joined=len(operands) == 2):
                source = "import sys, subprocess\n" + consumer + ".run(" + repr(operands) + ")\n"
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": source, "helper.py": COPY}), None,
                    "scripts/start.py:2: local-script discovery: execution literal coverage limit exceeded")

    def test_review6_mixed_quoted_heredoc_delimiter_preserves_later_execution(self):
        # R15: E'OF' is the complete quote-removed EOF delimiter, not E.
        for delimiter in ("E'OF'", 'E"OF"', "E\\OF"):
            with self.subTest(delimiter=delimiter):
                command = 'cat <<' + delimiter + '\ndata\nEOF\npython "$SCRIPT"'
                self.assert_coverage(self.coverage_case([("bash", command, "")], {"support/helper.py": COPY}), None,
                                     "action.yml:9: local-script discovery: unresolved local-script target")

    def test_review7_sys_modules_get_retains_process_identity(self):
        for namespace in ("sys.modules.get('subprocess')", "s.modules.get('subprocess')"):
            with self.subTest(namespace=namespace):
                source = ("import sys\nimport sys as s\n" + namespace +
                          ".run(['python3','-m',sys.argv[1]])\n")
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py helper", "")], {
                    "scripts/start.py": source, "helper.py": COPY}), None,
                    "unresolved computed Python script invocation")
                source = "import sys\nimport sys as s\n" + namespace + ".run(['python3','-m','helper'])\n"
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": source, "helper.py": COPY}), "helper.py", None)
        source = ("import sys, subprocess\nsp = sys.modules.get('subprocess')\n"
                  "sp.run(['python','-m',sys.argv[1]])\n")
        self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py helper", "")], {
            "scripts/start.py": source, "helper.py": COPY}), None,
            "scripts/start.py:2: local-script discovery: unsupported reflective use of an imported process/import namespace")

    def test_review7_qualified_asyncio_subprocess_apis_fail(self):
        for source in (
                "import asyncio, sys\nasyncio.run(asyncio.subprocess.create_subprocess_exec"
                "('python3','-m',sys.argv[1]))\n",
                "import asyncio, sys\nfrom asyncio.subprocess import create_subprocess_exec as launch\n"
                "asyncio.run(launch('python3','-m',sys.argv[1]))\n",
                "import asyncio, sys\nimport asyncio.subprocess as child\n"
                "asyncio.run(child.create_subprocess_exec('python3','-m',sys.argv[1]))\n"):
            with self.subTest(source=source):
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py helper", "")], {
                    "scripts/start.py": source, "helper.py": COPY}), None,
                    "unsupported Python process/import API: asyncio.subprocess.create_subprocess_exec")

    def test_review7_from_import_checks_unsafe_child_directories(self):
        for kind in ("symlink", "gitlink"):
            with self.subTest(kind=kind):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, "python scripts/start.py")
                    w.write(module, "scripts/start.py", "from pkg import ns\n")
                    w.write(module, "scripts/pkg/__init__.py", "# regular package\n")
                    w.write(module, "support/__init__.py", block("python"))
                    if kind == "symlink":
                        (w.paths[module] / "scripts/pkg/ns").symlink_to("../../support")
                        w.commit(w.paths[module])
                    else:
                        w.commit(w.paths[module])
                        revision = git(w.paths[module], "rev-parse", "HEAD")
                        git(w.paths[module], "update-index", "--add", "--cacheinfo",
                            "160000," + revision + ",scripts/pkg/ns")
                        git(w.paths[module], "commit", "--quiet", "-m", "unsafe child directory")
                self.assert_coverage(w.scan(self.factory), None,
                                     "unsafe non-directory Python import path component: scripts/pkg/ns")

    def test_review7_printf_variable_resolution_writes_fail(self):
        for command in ("printf -v PATH '%s' support; helper", "printf -vPATH '%s' support; helper",
                        "printf -v 'PATH[0]' '%s' support; helper", 'printf -v "$NAME" %s support',
                        "printf -v PYTHONPATH %s support", "printf -v 'MODE[PATH=1]' %s support"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "support/helper": "#!/usr/bin/env python3\n" + block("python")}), None,
                    "unsupported printf variable write affecting script resolution")
        self.assertEqual(self.coverage_case([("bash", "printf -v MODE '%s' fast", "")], {},
                                            modules=("Hexalith.Alpha",))["result"], "pass")

    def test_review7_unmodeled_nameref_declarations_fail(self):
        for declaration in ("declare -n indirect=PATH", "declare -gn indirect=PATH", "typeset -n indirect=PATH"):
            with self.subTest(declaration=declaration):
                self.assert_coverage(self.coverage_case([("bash", declaration + "; read indirect <<<support", "")], {
                    "support/helper": "#!/usr/bin/env python3\n" + block("python")}), None,
                    "unsupported shell nameref declaration")
        self.assertEqual(self.coverage_case([("bash", "declare MODE=fast; read MODE <<<fast", "")], {},
                                            modules=("Hexalith.Alpha",))["result"], "pass")

    def test_review7_path_file_validates_complete_emitted_output(self):
        for command in ('echo /usr/bin "$CONFIG$GITHUB_PATH" >> "$GITHUB_PATH"',
                        'echo /usr/bin "GITHUB_PATH$CONFIG" >> "$GITHUB_PATH"',
                        'printf "%b" "/usr/bin\\nsupport" >> "$GITHUB_PATH"'):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], {"support/helper.py": COPY}), None,
                                     "unsupported $GITHUB_PATH change affecting script resolution")
        for command in ('echo "$HOME/.local/bin" >> "$GITHUB_PATH"',
                        'printf \'%s\\n\' "$HOME/bin" /usr/bin >> "$GITHUB_PATH"'):
            with self.subTest(safe=command):
                self.assertEqual(self.coverage_case([("bash", command, "")], {},
                                                    modules=("Hexalith.Alpha",))["result"], "pass")

    def test_review7_project_build_system_preparation_fails_without_backend_path(self):
        project = ('[project]\nname="probe"\nversion="1.0"\n[build-system]\nrequires=["setuptools"]\n'
                   'build-backend="setuptools.build_meta"\n')
        files = {"pyproject.toml": project, "setup.py": COPY}
        self.assert_coverage(self.coverage_case([("bash", "uv run --no-build-isolation --offline python -c pass", "")],
                                               files), None,
                             "unsupported local project preparation with tracked build backend")
        for command in ("uv --version", "uv run --no-sync python -c pass", "uv run --no-project python -c pass"):
            with self.subTest(probe=command):
                self.assertEqual(self.coverage_case([("bash", command, "")], files,
                                                    modules=("Hexalith.Alpha",))["result"], "pass")

    def test_review7_path_file_cr_records_are_validated_individually(self):
        for separator in (r"\r", r"\r\n", r"\n"):
            with self.subTest(separator=separator):
                command = "printf '/usr/bin" + separator + "support" + separator + "' >> \"$GITHUB_PATH\""
                self.assert_coverage(self.coverage_case([("bash", command, "")], {
                    "support/helper": "#!/usr/bin/env python3\n" + block("python")}), None,
                    "unsupported $GITHUB_PATH change affecting script resolution")

    def test_review7_explicit_local_dependencies_precede_preparation_exemptions(self):
        project = ('[project]\nname="probe"\nversion="1.0"\n[build-system]\nrequires=[]\n'
                   'build-backend="backend"\nbackend-path=["support"]\n')
        files = {"pyproject.toml": project, "support/backend.py": COPY}
        for command in ("uv run --offline --no-project --with . python -c pass",
                        "uv run --no-sync --with=. python -c pass", "uv run --no-project --with-editable . python -c pass"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], files), None,
                                     "unsupported local dependency preparation")
        for command in ("uv run --no-project --with packaging python -c pass",
                        "uv run --no-sync --with 'packaging>=24' python -c pass"):
            with self.subTest(public=command):
                self.assertEqual(self.coverage_case([("bash", command, "")], files,
                                                    modules=("Hexalith.Alpha",))["result"], "pass")
        self.assert_coverage(self.coverage_case([("bash", "uv run python -c pass --no-project --with .", "")], files),
                             None, "unsupported local project preparation with tracked build backend")

    def test_review7_mutating_npm_audit_is_not_a_safe_probe(self):
        files = {"package.json": '{"dependencies":{"hook":"file:./hooks"}}',
                 "hooks/package.json": '{"name":"hook","scripts":{"install":"python3 -m helper"}}',
                 "hooks/helper.py": COPY}
        self.assert_coverage(self.coverage_case([("bash", "npm audit fix --offline --foreground-scripts", "")], files),
                             None, "unsupported mutating npm audit operation")
        for command in ("npm audit signatures", "npm audit --json"):
            with self.subTest(probe=command):
                self.assertEqual(self.coverage_case([("bash", command, "")], files,
                                                    modules=("Hexalith.Alpha",))["result"], "pass")

    def test_review7_project_recipes_shadow_interpreter_and_shell_names(self):
        for name in ("python", "bash"):
            with self.subTest(name=name):
                self.assert_coverage(self.coverage_case([("bash", "poetry run " + name + " -c pass", "")], {
                    "pyproject.toml": '[tool.poetry.scripts]\n' + name + '="helper:main"\n', "helper.py": COPY}), None,
                    "unsupported task runner with tracked module recipes: poetry")

    def test_review7_powershell_environment_output_uses_separate_lines(self):
        command = 'Write-Output "MODE=fast" "PYTHONPATH=support" >> $env:GITHUB_ENV'
        self.assert_coverage(self.coverage_case([("pwsh", command, "")], {"support/helper.py": COPY}), None,
                             "unsupported $GITHUB_ENV write affecting script resolution")
        # Bash echo emits one harmless MODE value containing the second word.
        self.assertEqual(self.coverage_case([("bash", 'echo "MODE=fast" "PYTHONPATH=support" >> "$GITHUB_ENV"', "")], {},
                                            modules=("Hexalith.Alpha",))["result"], "pass")

    def test_review7_node_workspace_and_unmodeled_leading_value_options_fail(self):
        files = {"package.json": '{"workspaces":["info"]}',
                 "info/package.json": '{"name":"info","scripts":{"lint":"python3 -m helper"}}',
                 "info/helper.py": COPY}
        for command in ("npm --workspace info run lint", "npm --workspace=info run lint", "npm -w info run lint"):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", command, "")], files), None,
                                     "missing or unsafe npm/config input: info/package-lock.json")
        self.assert_coverage(self.coverage_case([("bash", "npm --registry info run lint", "")], files), None,
                             "unsupported task runner leading option")
        for command in ("npm info jscpd", "npm --ignore-scripts --version", "npm audit signatures"):
            with self.subTest(probe=command):
                self.assertEqual(self.coverage_case([("bash", command, "")], files,
                                                    modules=("Hexalith.Alpha",))["result"], "pass")

    def test_review7_outer_execution_string_limit_fails_for_unknown_python_consumer(self):
        for command in ("python -c '" + "x=0;" * 1100 + " import helper'",
                        "true;" * 1100 + "python -c 'import helper'"):
            with self.subTest(command_suffix=command[-40:]):
                source = "import runner\nrunner.run(" + repr(command) + ")\n"
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": source, "helper.py": COPY}), None,
                    "scripts/start.py:2: local-script discovery: execution literal coverage limit exceeded")
        # A large literal without an execution-bearing command remains data.
        for value in ("ordinary data " * 400, "notpython -c data " * 400):
            with self.subTest(data_prefix=value[:20]):
                self.assertEqual(self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": "value = " + repr(value) + "\n"},
                    modules=("Hexalith.Alpha",))["result"], "pass")

    def test_review7_nested_process_dunder_invocation_fails(self):
        for receiver in ("subprocess.run", "launch"):
            with self.subTest(receiver=receiver):
                source = ("import subprocess, sys\nlaunch = subprocess.run\n" + receiver +
                          ".__call__(['python3','-m',sys.argv[1]])\n")
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py helper", "")], {
                    "scripts/start.py": source, "helper.py": COPY}), None,
                    "unsupported reflective use of a process/import API")

    def test_review7_unsupported_heredoc_quoting_fails_without_hiding_later_commands(self):
        for delimiter in ("$'EOF'", '$"EOF"'):
            with self.subTest(delimiter=delimiter):
                command = 'cat <<' + delimiter + '\ndata\nEOF\npython3 "$SCRIPT"'
                self.assert_coverage(self.coverage_case([("bash", command, "")], {"support/helper.py": COPY}), None,
                                     "unsupported heredoc delimiter syntax: ANSI/locale quoting")

    def test_unknown_python_consumer_preserves_literal_child_cwd(self):
        source = "import runner\nrunner.run(['bash','../scripts/start.sh'], cwd='work')\n"
        report = self.coverage_case([("bash", "python scripts/start.py", "")], {
            "scripts/start.py": source, "scripts/start.sh": "python -m helper\n", "work/helper.py": COPY})
        self.assert_coverage(report, "work/helper.py", None)

    def test_fixed_compiler_operands_preserve_literal_scope_and_reject_execution_indirection(self):
        report = self.coverage_case([("bash", "python scripts/start.py", "")], {
            "scripts/start.py": "import subprocess\nsubprocess.run(['dotnet', 'build', project, '--no-restore', 'scripts/payload.py'])\n",
            "scripts/payload.py": COPY,
        })
        self.assert_coverage(report, "scripts/payload.py", None)
        for command, diagnostic in (
                ("subprocess.run(['dotnet', operation, project])", "computed Python script invocation"),
                ("subprocess.run([executable, 'build', project])", "computed Python script invocation"),
                ("subprocess.run(['dotnet', 'build', project], shell=True)", "shell execution"),
                ("subprocess.run(['dotnet', 'build', project], cwd=directory)", "subprocess cwd"),
                ("subprocess.run(['dotnet', 'build', project], env={'PATH':'scripts'})", "environment affecting resolution")):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": "import subprocess\n" + command + "\n",
                }), None, diagnostic)

    def test_each_central_policy_rule_fails_alone(self):
        # C16: one single-violation subtest per central-policy rule.
        policy = json.loads((ROOT / ".jscpd.json").read_bytes())
        mutations = {"not-an-object": [], "format": policy | {"format": ["python"]},
                     "format-missing": {k: v for k, v in policy.items() if k != "format"},
                     "skipLocal": policy | {"skipLocal": False}, "noGitignore": policy | {"noGitignore": False},
                     "absolute": policy | {"absolute": False}, "reporters": policy | {"reporters": ["json", "console"]},
                     "ignore": policy | {"ignore": ["**"]}, "ignorePattern": policy | {"ignorePattern": ["x"]},
                     "threshold": policy | {"threshold": 0}, "baseline": policy | {"baseline": "x"},
                     "pattern": policy | {"pattern": "**"}}
        w = self.workspace(())
        for rule, value in mutations.items():
            with self.subTest(rule=rule):
                (w.cicd / ".jscpd.json").write_text(json.dumps(value))
                revision = w.commit(w.cicd)
                with tempfile.TemporaryDirectory() as scratch, self.assertRaises(rt.DeliveryError) as raised:
                    sc.Detector(rt.Git(w.cicd), revision, scratch)
                self.assertEqual(str(raised.exception), "invalid central detector policy")
        (w.cicd / ".jscpd.json").write_text(json.dumps(policy))
        revision = w.commit(w.cicd)
        # The unchanged committed policy is accepted by the same validation.
        self.assertEqual(rt.json_read(rt.Git(w.cicd).blob(revision, ".jscpd.json")), policy)

if __name__ == "__main__":
    unittest.main()
