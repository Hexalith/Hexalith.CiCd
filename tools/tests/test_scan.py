#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Real Git scope and pinned detector qualification; no matrix cases skip."""
from __future__ import annotations

import functools
import hashlib
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
import test_nightly_acceptance as acceptance_tests

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
        self.pins = {}

    def module(self, target, module):
        self.seen.append(module)
        target.run("fetch", "--quiet", "--depth=1", "--no-tags", "--no-recurse-submodules",
                   self.paths[module], "+refs/heads/main:refs/heads/main")
        return target.resolve("refs/heads/main^{commit}")

    def pinned_source(self, target, repository, revision):
        target.run("fetch", "--quiet", "--depth=1", "--no-tags", "--no-recurse-submodules",
                   self.pins[repository], revision)


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
    ("ps-else", [("pwsh", "if ($false) { Write-Host x } else { ./scripts/helper.ps1 }", "")], {"scripts/helper.ps1": COPY},
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
    ("python-dynamic-heredoc", [("bash", "python - <<EOF\nimport helper\nEOF", "")], {"helper.py": COPY},
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


class PowerShellDiscoveryTests(unittest.TestCase):
    def discover(self, source, files=None):
        temporary = tempfile.TemporaryDirectory(prefix="powershell-discovery-")
        self.addCleanup(temporary.cleanup)
        w = Workspace(Path(temporary.name) / "workspace", ("Hexalith.Alpha",))
        w.action("Hexalith.Alpha", "./scripts/start.ps1", shell="pwsh")
        for path, text in {"scripts/start.ps1": source, **(files or {})}.items():
            w.write("Hexalith.Alpha", path, text)
        revision = w.commit(w.paths["Hexalith.Alpha"])
        return sc.Discovery(rt.Git(w.paths["Hexalith.Alpha"]), revision).discover()

    def test_parameters_assignments_and_data_expressions_are_not_commands(self):
        files, errors = self.discover("""param([string]$Label = 'folders')
$ErrorActionPreference = 'Stop'
$values = @(1, 2)
$count = 0
$count++
$data = @{ Label = $Label; Values = $values }
foreach ($item in $values) { Write-Host "$($data.Label): $item" }
""")
        self.assertEqual(errors, [])
        self.assertEqual(set(files), {".github/actions/dormant/action.yml", "scripts/start.ps1"})

    def test_literal_calls_inside_functions_branches_and_assignment_rhs(self):
        files, errors = self.discover("""using module @{ModuleName='./scripts/library.psm1'; ModuleVersion='1.0.0'}
function Invoke-Checks {
    param([string]$Label = 'folders')
    if ($Label) { & "$PSScriptRoot/child.ps1" } else { . "$PSScriptRoot/library.psm1" }
}
Invoke-Checks -Label folders
$output = (python ./scripts/check.py)
try { ./scripts/direct.ps1 } catch { Write-Host 'failed' }
pwsh -Command:"& ./scripts/direct.ps1"
""", {"scripts/child.ps1": "Write-Host child\n", "scripts/library.psm1": "Write-Host library\n",
       "scripts/check.py": "print('checked')\n", "scripts/direct.ps1": "Write-Host direct\n"})
        self.assertEqual(errors, [])
        self.assertTrue({"scripts/child.ps1", "scripts/library.psm1", "scripts/check.py",
                         "scripts/direct.ps1"} <= set(files))

    def test_unresolved_execution_and_resolution_mutations_still_fail(self):
        probes = {
            "& $Command": "unresolved computed command",
            ". $Script": "unresolved computed command",
            "$output = (& $Command)": "unresolved computed command",
            'Write-Host "$(python $Script)"': "unresolved local-script target",
            'pwsh -File "$Script"': "unresolved local-script target",
            "Invoke-Expression $Code": "unresolved computed command",
            "Start-Process python -ArgumentList $Args": "PowerShell process invocation",
            "[System.Diagnostics.Process]::Start($Command)": "PowerShell method invocation",
            "[scriptblock]::Create($Code).Invoke()": "PowerShell method invocation",
            "Set-Location scripts": "working-directory command",
            "$env:PYTHONPATH = 'support'": "environment assignment",
            '$env:PATH = "$PWD/scripts;$env:PATH"': "PATH change",
            "Set-Item env:PSModulePath ./modules": "environment assignment",
            "unknown-launcher $Command": "computed operand of unknown command",
            "unknown-launcher @Arguments": "argument splatting",
            'pwsh -Command "$Code"': "unresolved computed command",
            'python -c ("exec(" + "input())")': "computed PowerShell command operand",
            'Invoke-Expression -Command:("./scripts/" + "hidden.ps1")': "computed PowerShell command operand",
            'Invoke-Expression -Command:$Code': "unresolved computed command",
            'unknown-launcher ("scripts/hid" + "den.ps1")': "computed PowerShell command operand",
            '$env:PYTHONPATH[0] = "s"': "environment assignment",
            '[Environment]::CurrentDirectory = "scripts"': "PowerShell assignment target",
            '$env:PYTHONPATH++': "environment assignment",
            '$env:PYTHONPATH ??= "support"': "environment assignment",
            '$env:PATH ??= "scripts"': "environment assignment",
            '--$env:PATH': "environment assignment",
            '$function:InvokeHidden = $Code': "assignment affecting command resolution",
            '$alias:InvokeHidden = $Command': "assignment affecting command resolution",
            '$global:PSDefaultParameterValues = @{}': "assignment affecting command resolution",
            '("./scripts/hid" + "den.ps1") | Invoke-Expression': "unresolved computed command",
            'Set-Alias run Invoke-Expression; run "& (\'./scripts/hid\' + \'den.ps1\')"': "alias mutation",
            'Set-Item alias:run Invoke-Expression': "provider mutation",
        }
        for source, diagnostic in probes.items():
            with self.subTest(source=source):
                _, errors = self.discover("param()\n" + source + "\n")
                self.assertTrue(any("scripts/start.ps1:2:" in error and diagnostic in error
                                    for error in errors), errors)

    def test_alias_and_provider_mutations_are_rejected(self):
        for command in ('Copy-Item alias:iex alias:run', 'cpi alias:iex alias:run',
                        'Move-Item alias:iex alias:run', 'Rename-Item alias:iex run',
                        'Import-Alias ./aliases.csv', 'New-PSDrive -Name commands -PSProvider Alias -Root ""'):
            with self.subTest(command=command):
                _, errors = self.discover(command + "\n")
                self.assertTrue(any("affecting command resolution" in error for error in errors), errors)

    def test_invalid_syntax_and_missing_parser_fail_closed(self):
        _, errors = self.discover("if ($true { Write-Host x }\n")
        self.assertTrue(any("invalid PowerShell syntax" in error for error in errors), errors)
        import scan_discovery as discovery
        discovery.powershell_ast.cache_clear()
        with mock.patch.object(discovery.subprocess, "run", side_effect=FileNotFoundError("pwsh")):
            with self.assertRaisesRegex(rt.DeliveryError, "PowerShell parser unavailable"):
                discovery.powershell_ast("param()\n# missing parser probe\n")

    def test_malformed_and_failed_parser_output_fail_closed(self):
        import scan_discovery as discovery
        for output in ("not JSON", '{"events":null}', '{"events":[{}]}',
                       '{"events":[{"line":1,"kind":"command","text":"x"}]}'):
            with self.subTest(output=output):
                result = discovery.subprocess.CompletedProcess([], 0, output, "")
                with mock.patch.object(discovery.subprocess, "run", return_value=result):
                    with self.assertRaisesRegex(rt.DeliveryError, "invalid PowerShell parser output"):
                        discovery.powershell_ast("# malformed output probe " + output)
        with mock.patch.object(discovery.subprocess, "run", return_value=discovery.subprocess.CompletedProcess(
                [], 1, "", "parser failure")):
            with self.assertRaisesRegex(rt.DeliveryError, "PowerShell parser failed"):
                discovery.powershell_ast("# failed parser probe")
        with mock.patch.object(discovery.subprocess, "run", side_effect=discovery.subprocess.TimeoutExpired("pwsh", 30)):
            with self.assertRaisesRegex(rt.DeliveryError, "PowerShell parser unavailable"):
                discovery.powershell_ast("# parser timeout probe")

    def test_data_array_literal_module_references_are_traversed(self):
        files, errors = self.discover("$arguments = @('python', '-m', 'helper')\n", {"helper.py": "print('helper')\n"})
        self.assertEqual(errors, [])
        self.assertIn("helper.py", files)

    def test_requires_literal_module_is_traversed(self):
        files, errors = self.discover("#requires -Modules ./scripts/helper.psm1\nWrite-Host ready\n",
                                      {"scripts/helper.psm1": "& $Command\n"})
        self.assertIn("scripts/helper.psm1", files)
        self.assertTrue(any("scripts/helper.psm1:1:" in error and "unresolved computed command" in error
                            for error in errors), errors)

    def test_source_is_never_executed(self):
        temporary = tempfile.TemporaryDirectory(prefix="powershell-inert-")
        self.addCleanup(temporary.cleanup)
        marker = Path(temporary.name) / "must-not-exist"
        _, errors = self.discover("Set-Content -Path '" + str(marker) + "' -Value executed\n")
        self.assertEqual(errors, [])
        self.assertFalse(marker.exists())
        import scan_discovery as discovery
        module = Path(temporary.name) / "must-not-load.psm1"
        module.write_text("Set-Content -Path '" + str(marker) + "' -Value loaded\n")
        for target in (module, module.with_name("does-not-exist.psm1")):
            events = discovery.powershell_ast("using module '" + str(target) + "'\n")
            self.assertFalse(any(event["kind"] == "error" for event in events), events)
            self.assertFalse(marker.exists())


class LauncherDiscoveryTests(unittest.TestCase):
    def discover(self, commands, files, *, action="dormant"):
        with tempfile.TemporaryDirectory(prefix="shell-discovery-") as temp:
            module = "Hexalith.Alpha"
            w = Workspace(Path(temp) / "workspace", (module,))
            w.write(module, f".github/actions/{action}/action.yml", steps(*commands))
            for path, source in files.items():
                w.write(module, path, source)
            revision = w.commit(w.paths[module])
            discovery = sc.Discovery(rt.Git(w.paths[module]), revision)
            selected, errors = discovery.discover()
            return selected, errors, discovery.visited

    def test_timeout_options_keep_the_child_in_scope(self):
        files = {"tools/helper.py": "import child\n", "tools/child.py": "print('child')\n"}
        commands = [("bash", "timeout --signal=TERM --kill-after=30s -- 1.5m python tools/helper.py", "")]
        selected, errors, _ = self.discover(commands, files)
        self.assertEqual(errors, [])
        self.assertIn("tools/child.py", selected)

    def test_stopped_container_operations_keep_literal_source_references(self):
        source = """import subprocess
subprocess.run(["docker", "pull", "--platform", "linux/amd64", image], timeout=300)
container = subprocess.check_output(["docker", "create", "--network", "none", image, "/bin/true"])
subprocess.run(["docker", "cp", container + ":/tool", "tools/helper.py"])
subprocess.run(["docker", "rm", container])
"""
        selected, errors, _ = self.discover([("bash", "python tools/bootstrap.py", "")],
                                            {"tools/bootstrap.py": source, "tools/helper.py": "import child\n",
                                             "tools/child.py": "pass\n"})
        self.assertEqual(errors, [])
        self.assertIn("tools/child.py", selected)

    def test_docker_data_operations_refuse_unproved_execution(self):
        for call, files, diagnostic in (
                ('["docker", "run", image]', {}, "unresolved computed Python script invocation"),
                ('["docker", operation, image]', {}, "unresolved computed Python script invocation"),
                ('["docker", "create", "--network", settings, image, "/bin/true"]', {},
                 "unresolved computed Python script invocation"),
                ('["docker", "rm", *containers]', {}, "unsafe or unresolved forwarding"),
                ('["docker", "rm", container], shell=True', {}, "unsupported shell execution"),
                ('["docker", "rm", container], preexec_fn=callback', {}, "unsupported subprocess pre-execution callback"),
                ('["docker", "rm", container], env={"PATH": "tools"}', {}, "environment affecting resolution"),
                ('["docker", "rm", container]', {"tools/subprocess.py": "pass\n"}, "unproved subprocess API"),
                ('["docker", "rm", container]', {"tools/docker": "#!/bin/bash\n:"}, "tracked Docker command")):
            with self.subTest(call=call, files=files):
                _, errors, _ = self.discover([("bash", "python tools/bootstrap.py", "")],
                                             files | {"tools/bootstrap.py": f"import subprocess\nsubprocess.run({call})\n"})
                self.assertEqual(len(errors), 1)
                self.assertIn(diagnostic, errors[0])
        _, errors, _ = self.discover([("bash", "python tools/bootstrap.py", "")], {
            "tools/bootstrap.py": 'import subprocess\nsubprocess.getoutput(["docker", "rm", container])\n',
        })
        self.assertEqual(len(errors), 1)
        self.assertIn("unsupported shell execution", errors[0])

    def test_native_hook_traverses_the_shared_prepared_python_target(self):
        command = ('timeout --signal=TERM --kill-after=30s 3600 '
                   '"${HEXALITH_CI_PYTHON:?Shared prepared Python is required}" tools/driver.py linux')
        version = "v6.8.1"
        checked_config = {"aspire": True, "hooks": ["after-unit-tests"], "buildsTag": version}
        workflow = ("on: [push]\njobs:\n  ci:\n"
                    f"    uses: Hexalith/Hexalith.Builds/.github/workflows/ci.yml@{version}\n"
                    "    with:\n      job-timeout-minutes: 360\n")
        files = {
            ".github/hexalith-ci.json": json.dumps(checked_config),
            ".github/workflows/ci.yml": workflow,
            "tools/driver.py": "import helper\n",
            "tools/helper.py": "pass\n",
        }
        selected, errors, _ = self.discover([("bash", command, "")], files, action="after-unit-tests")
        self.assertEqual(errors, [])
        self.assertIn("tools/helper.py", selected)
        for supported in ("v6.2.0", "v6.8.4", "v6.11.2"):
            with self.subTest(supported=supported):
                selected, errors, _ = self.discover([("bash", command, "")], files | {
                    ".github/workflows/ci.yml": workflow.replace(version, supported),
                    ".github/hexalith-ci.json": json.dumps(checked_config | {"buildsTag": supported}),
                }, action="after-unit-tests")
                self.assertEqual(errors, [])
                self.assertIn("tools/helper.py", selected)

        for changes, extra, diagnostic in (
            ({".github/hexalith-ci.json": json.dumps(checked_config | {"aspire": False})}, "",
             "requires the enabled native CI hook"),
            ({".github/workflows/ci.yml": workflow.replace(version, "v6.1.9"),
              ".github/hexalith-ci.json": json.dumps(checked_config | {"buildsTag": "v6.1.9"})}, "",
             "requires the committed managed CI workflow"),
            ({".github/workflows/ci.yml": workflow + "      module-root: alternate\n"}, "",
             "requires the committed managed CI workflow"),
            ({}, "      env:\n        HEXALITH_CI_PYTHON: ./elsewhere\n",
             "unsupported step environment affecting script resolution"),
        ):
            with self.subTest(diagnostic=diagnostic, changes=changes):
                _, errors, _ = self.discover([("bash", command, extra)], files | changes, action="after-unit-tests")
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(diagnostic, errors[0])
        for alternation in (command.replace('"$', '$').replace('}"', '}'), command + ' > "$OUTPUT"'):
            with self.subTest(alternation=alternation):
                _, errors, _ = self.discover([("bash", alternation, "")], files, action="after-unit-tests")
                self.assertEqual(len(errors), 1, errors)
                self.assertIn("unresolved computed command", errors[0])
        _, errors, _ = self.discover([
            ("bash", 'echo "HEXALITH_CI_PYTHON=/somewhere/python" >> "$GITHUB_ENV"', ""),
            ("bash", command, ""),
        ], files, action="after-unit-tests")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("unsupported $GITHUB_ENV write affecting script resolution", errors[0])
        _, errors, _ = self.discover([("bash", command, "")], files | {
            ".github/actions/wrapper/action.yml": (
                "name: wrapper\nruns:\n  using: composite\n  steps:\n"
                "    - uses: ./.github/actions/after-unit-tests\n"
                "      env:\n        HEXALITH_CI_PYTHON: ./elsewhere\n"
            ),
        }, action="after-unit-tests")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("unsupported step environment affecting script resolution", errors[0])

    def test_quoted_python_heredoc_traverses_imports_and_preserves_line_numbers(self):
        commands = [("bash", "cd checks\npython3 - \"$RECEIPT\" <<'PY'\n"
                    "import helper\nimport subprocess\nsubprocess.run([target])\nPY", "")]
        files = {"helper.py": "pass\n", "checks/helper.py": "pass\n"}
        selected, errors, _ = self.discover(commands, files)
        self.assertTrue(files.keys() <= selected.keys(), selected)
        self.assertEqual(errors, [".github/actions/dormant/action.yml:10: local-script discovery: "
                                  "unresolved computed Python script invocation"], errors)

    def test_quoted_python_heredoc_refuses_unproved_shell_forms(self):
        for command, diagnostic in (
            ('python3 - \"$(hidden)\" <<\'PY\'\nimport helper\nPY', "unsupported shell command substitution"),
            ("python3 - <<'PY' < \"$SOURCE\"\nimport helper\nPY", "unsupported heredoc-fed interpreter"),
            ("python3 - <<'PY'\nimport helper", "unsupported heredoc-fed interpreter"),
            ("python3 - <<'PY'\r\nimport helper\nPY", "unsupported heredoc-fed interpreter"),
            ("python3\\\n- <<'PY'\nimport helper\nPY", "unsupported heredoc-fed interpreter"),
        ):
            with self.subTest(command=command):
                selected, errors, _ = self.discover([("bash", command, "")], {"helper.py": "pass\n"})
                self.assertNotIn("helper.py", selected)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(diagnostic, errors[0])

    def test_literal_dotnet_build_operation_keeps_script_references(self):
        commands = [("bash", 'dotnet pack "$PROJECT" --output "${ARTIFACTS}" -p:Fixture=tools/check.py', "")]
        selected, errors, _ = self.discover(commands, {"tools/check.py": "pass\n"})
        self.assertEqual(errors, [])
        self.assertIn("tools/check.py", selected)

    def test_dotnet_build_operation_refuses_unproved_shell_forms(self):
        for command, diagnostic in (
            ('dotnet "$OPERATION" "$PROJECT"', "unresolved computed operand of unknown command"),
            ('dotnet build "$(hidden)"', "unsupported shell command substitution"),
            ('dotnet pack "${NAME@P}"', "unsupported .NET shell substitution"),
            ('dotnet tool run "$TOOL"', "unresolved computed operand of unknown command"),
        ):
            with self.subTest(command=command):
                _, errors, _ = self.discover([("bash", command, "")], {})
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(diagnostic, errors[0])

    def test_timeout_refuses_an_unresolved_option_or_duration(self):
        commands = [("bash", command, "") for command in (
            "timeout --unknown 60 python -m helper",
            "timeout --kill-after=$GRACE 60 python -m helper",
            "timeout $DURATION python -m helper",
            "timeout -- --signal=TERM 60 python -m helper",
        )]
        selected, errors, _ = self.discover(commands, {"helper.py": "print('helper')\n"})
        self.assertEqual(len(errors), len(commands), errors)
        self.assertTrue(all("timeout " in error for error in errors), errors)
        self.assertIn("helper.py", selected)

    def test_bounded_source_relative_launcher_preserves_child_cwd(self):
        launcher = """#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
exec timeout --signal=TERM --kill-after=30s 2280 python3 tools/live-topology/driver.py prepare
"""
        launcher_path = "tools/live-topology/start.sh"
        driver = "tools/live-topology/driver.py"
        files = {launcher_path: launcher, driver: "pass\n", "jobs/README.md": "Job launch directory.\n"}
        commands = [("bash", "bash ../tools/live-topology/start.sh", "      working-directory: jobs\n")]
        selected, errors, visited = self.discover(commands, files)
        self.assertEqual(errors, [])
        self.assertIn(driver, selected)
        self.assertEqual({cwd for path, cwd, *_ in visited if path == driver}, {"."})
        selected, errors, _ = self.discover(commands, files | {launcher_path: launcher.replace("/../..", "/../../..")})
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("source-relative launcher escapes", errors[0])
        self.assertIn(driver, selected)

    def test_source_relative_scratch_prologue_binds_the_later_working_directory(self):
        launcher = """#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
task_dir="$(mktemp -d)"
trap 'rm -rf "$task_dir"' EXIT
cd "$repo_root"
python3 -m check
"""
        launcher_path = "tools/checks/start.sh"
        files = {
            launcher_path: launcher, "check.py": "pass\n",
            "jobs/README.md": "Job cwd.", "alternate/README.md": "Changed cwd.",
        }
        steps = [("bash", "bash ../tools/checks/start.sh", "      working-directory: jobs\n")]
        selected, errors, visited = self.discover(steps, files)
        self.assertEqual(errors, [])
        self.assertIn("check.py", selected)
        self.assertIn(".", {cwd for path, cwd, *_ in visited if path == "check.py"})
        for altered, diagnostic in (
            (launcher.replace("/../..", "/../../.."), "source-relative launcher escapes"),
            (launcher.replace('cd "$repo_root"', 'cd "$fallback"'), "unsupported shell command substitution"),
            (launcher.replace("repo_root=", "unset BASH_SOURCE\nrepo_root=", 1), "unsupported shell command substitution"),
            (launcher.replace('repo_root=', 'cd "$GITHUB_WORKSPACE/alternate"\nrepo_root='),
             "unsupported shell command substitution"),
        ):
            with self.subTest(diagnostic=diagnostic):
                _, errors, _ = self.discover(steps, files | {launcher_path: altered})
                self.assertTrue(any(diagnostic in error for error in errors), errors)

    def test_source_relative_scratch_prologue_accepts_inert_option_validation(self):
        launcher = """#!/usr/bin/env bash
set -euo pipefail

configuration="${1-Debug}"
if (( $# > 1 )) || [[ "$configuration" != Debug && "$configuration" != Release ]]; then
    echo "Usage: bash tools/checks/start.sh [Debug|Release]" >&2
    exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
task_dir="$(mktemp -d)"
trap 'rm -rf "$task_dir"' EXIT
cd "$repo_root"
python3 -m check
"""
        path = "tools/checks/start.sh"
        files = {"check.py": "pass\n", "jobs/README.md": "Job cwd.", path: launcher}
        steps = [("bash", "bash ../tools/checks/start.sh", "      working-directory: jobs\n")]
        selected, errors, visited = self.discover(steps, files)
        self.assertEqual(errors, [])
        self.assertIn("check.py", selected)
        self.assertIn(".", {cwd for name, cwd, *_ in visited if name == "check.py"})
        for unsafe in (
            launcher.replace("exit 2", 'cd "$GITHUB_WORKSPACE/tools"\n    exit 2'),
            launcher.replace("$# > 1", "count = 1"),
            launcher.replace('start.sh [Debug|Release]', 'start.sh $(hidden)'),
        ):
            with self.subTest(unsafe=unsafe):
                _, errors, _ = self.discover(steps, files | {path: unsafe})
                self.assertTrue(any("unsupported shell command substitution" in error for error in errors), errors)

    def test_literal_bash_array_keeps_its_script_references(self):
        command = "vectors=(tools/input.json\n         tools/helper.py)\npython tools/next.py"
        files = {"tools/helper.py": "pass\n", "tools/next.py": "pass\n"}
        selected, errors, _ = self.discover([("bash", command, "")], files)
        self.assertEqual(errors, [])
        self.assertTrue(files.keys() <= selected.keys(), selected)
        for unsafe in (
            command.replace("tools/input.json", '$(python tools/hidden.py)'),
            command.replace("vectors", "BASH_ALIASES"),
            command.replace("tools/helper.py)", 'tools/helper.py); "$COMMAND"'),
            command.replace("tools/input.json", '[index]=tools/input.json'),
        ):
            with self.subTest(unsafe=unsafe):
                selected, errors, _ = self.discover([("bash", unsafe, "")], files)
                self.assertTrue(errors)
                self.assertIn("tools/next.py", selected)

    def test_grep_literal_pattern_and_simple_path_remain_data(self):
        command = """if ! grep -Eq '^[[:space:]]*1 Warning\\(s\\)$' "$directory/build.log"; then
  grep -q found tools/probe.py
fi"""
        files = {"tools/probe.py": "pass\n"}
        selected, errors, _ = self.discover([("bash", command, "")], files)
        self.assertEqual(errors, [])
        self.assertIn("tools/probe.py", selected)
        _, errors, _ = self.discover([("bash", 'grep -Eq pattern "$(hidden)"', "")], files)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("unsupported shell command substitution", errors[0])

    def test_early_python_search_path_keeps_its_source_root(self):
        source = ("import sys\nfrom pathlib import Path\n"
                  "ROOT = Path(__file__).resolve().parents[1]\n"
                  "sys.path.insert(0, str(ROOT / 'support'))\n"
                  "import helper\n"
                  "def later():\n    return type(ROOT), Path\n")
        command = [("bash", "python scripts/start.py", "")]
        files = {"scripts/start.py": source, "support/helper.py": "pass\n"}
        selected, errors, _ = self.discover(command, files)
        self.assertEqual(errors, [])
        self.assertIn("support/helper.py", selected)
        _, errors, _ = self.discover(command, files | {
            "scripts/start.py": source.replace("sys.path.insert", "modify(Path)\nsys.path.insert"),
        })
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("unsupported Python search-path mutation", errors[0])

    def test_unittest_discovers_package_sources_and_refuses_dynamic_selection(self):
        files = {
            "checks/test_suite.py": "import case_helper\n",
            "checks/case_helper.py": "print('helper')\n",
            "checks/nested/__init__.py": "from . import load\n",
            "checks/nested/load.py": "print('load_tests helper')\n",
            "checks/ignored.py": "raise RuntimeError('out of scope')\n",
        }
        commands = [("bash", "python -m unittest discover -v -s checks -p 'test_*.py'", "")]
        selected, errors, _ = self.discover(commands, files)
        self.assertEqual(errors, [])
        self.assertEqual({file for file in selected if file.startswith("checks/")},
                         set(files) - {"checks/ignored.py"})
        commands = [("bash", "python -m unittest discover -s checks -p \"$PATTERN\"", "")]
        _, errors, _ = self.discover(commands, files)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("unresolved unittest discovery filename pattern", errors[0])
        commands = [("bash", "python -m unittest discover -s checks", "")]
        _, errors, _ = self.discover(commands, files | {"checks/__pycache__/test_suite.cpython-312.pyc": "bytecode"})
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("unsafe unittest discovery source", errors[0])
        _, errors, _ = self.discover([("bash", "python -m unittest discover", "")], {})
        self.assertEqual(errors, [])

    def test_unittest_argv_keeps_wrapped_tests_in_scope(self):
        commands = [("bash", "python scripts/start.py", "")]
        source = ("from sys import executable as python\n"
                  "supervise([python, '-m', 'unittest', 'discover', '-s', 'checks', '-p', 'test_*.py'])\n")
        files = {"scripts/start.py": source, "checks/test_suite.py": "import helper\n",
                 "checks/helper.py": "pass\n", "ignored/test_hidden.py": "pass\n"}
        selected, errors, _ = self.discover(commands, files)
        self.assertEqual(errors, [])
        self.assertIn("checks/test_suite.py", selected)
        self.assertIn("checks/helper.py", selected)
        self.assertNotIn("ignored/test_hidden.py", selected)

        _, errors, _ = self.discover(commands, files | {"scripts/start.py": source.replace("'checks'", "directory")})
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("unresolved unittest discovery arguments", errors[0])

        direct = ("import subprocess, sys\n"
                  "subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'checks'], cwd='other')\n")
        shell = {"scripts/start.py": direct, "other/checks/test_specific.py": "pass\n"}
        selected, errors, _ = self.discover(commands, shell)
        self.assertEqual(errors, [])
        self.assertIn("other/checks/test_specific.py", selected)

    def test_git_can_read_the_superproject_directory(self):
        files = {"scripts/probe.py": "import subprocess\n"
                 "subprocess.check_output(['git', '-C', directory, 'rev-parse', '--show-superproject-working-tree'])\n"}
        selected, errors, _ = self.discover([("bash", "python scripts/probe.py", "")], files)
        self.assertEqual(errors, [])
        self.assertIn("scripts/probe.py", selected)


def discover_python(files, command="python3 entry.py"):
    """Discover one module directly, without the detector."""
    with tempfile.TemporaryDirectory(prefix="python-discovery-") as temp:
        module = "Hexalith.Alpha"
        w = Workspace(Path(temp) / "workspace", (module,))
        w.write(module, ".github/actions/dormant/action.yml", steps(("bash", command, "")))
        for path, source in files.items():
            w.write(module, path, source)
        revision = w.commit(w.paths[module])
        return sc.Discovery(rt.Git(w.paths[module]), revision).discover()


def discover_boundary(commands, files):
    """Discover one module directly; return its selection, errors and test boundary observations."""
    with tempfile.TemporaryDirectory(prefix="boundary-discovery-") as temp:
        module = "Hexalith.Alpha"
        w = Workspace(Path(temp) / "workspace", (module,))
        w.write(module, ".github/actions/dormant/action.yml", steps(*commands))
        for path, source in files.items():
            w.write(module, path, source)
        revision = w.commit(w.paths[module])
        discovery = sc.Discovery(rt.Git(w.paths[module]), revision)
        selected, errors = discovery.discover()
        observations = [f"{item['path']}:{item['line']}: {item['reason']}" for item in discovery.observations]
        return set(selected), errors, observations


def sites(diagnostics):
    """The path:line prefix of each diagnostic or observation."""
    return {":".join(entry.split(":", 2)[:2]) for entry in diagnostics}


class TestBoundaryTests(unittest.TestCase):
    """A test source reached only through unittest selection records its unresolved launches."""

    DISCOVER = ("bash", "python -m unittest discover -s tests -p 'test_*.py'", "")
    UNRESOLVED = "import subprocess\nsubprocess.run(command)\n"
    # Lines 2-10: computed argv, cwd and env, an unfollowed process API, exec
    # text, a computed import, a file loader, an oversized execution literal and
    # an unresolved command inside a literal inline shell program.
    LAUNCHES = ("import importlib, importlib.util, os, subprocess, sys\n"
                "subprocess.run(command)\n"
                "subprocess.run(['python', 'tools/helper.py'], cwd=directory)\n"
                "subprocess.run(['tool', '--check'], env=environment)\n"
                "os.execv(sys.executable, [sys.executable])\n"
                "exec(code)\n"
                "importlib.import_module(name)\n"
                "importlib.util.spec_from_file_location('fixture', location)\n"
                "PROGRAM = 'python3 -c pass  # " + "x" * 5000 + "'\n"
                "subprocess.run(['bash', '-c', 'set -e; \"$TOOL\" --check'])\n")
    LAUNCH_LINES = range(2, 11)

    def test_unresolved_launches_in_test_sources_are_observations(self):
        files = {"tests/test_launch.py": self.LAUNCHES + "subprocess.run([sys.executable, 'tools/runner.py'])\n"
                                         "import support\nimport test_peer\n",
                 "tests/test_peer.py": self.UNRESOLVED, "tests/support.py": self.UNRESOLVED,
                 "tools/helper.py": self.UNRESOLVED, "tools/runner.py": self.UNRESOLVED}
        selected, errors, observations = discover_boundary([self.DISCOVER], files)
        # Test sources stay selected; what they launch, name or import from
        # product code keeps full rules. Another test source keeps the boundary.
        self.assertTrue(set(files) <= selected, selected)
        self.assertEqual(sites(errors), {"tests/support.py:2", "tools/helper.py:2", "tools/runner.py:2"}, errors)
        self.assertEqual(sites(observations), {f"tests/test_launch.py:{line}" for line in self.LAUNCH_LINES}
                         | {"tests/test_peer.py:2"}, observations)
        self.assertTrue(all("local-script discovery: " in entry for entry in observations), observations)
        self.assertIn("tests/test_launch.py:3: local-script discovery: unresolved computed subprocess cwd", observations)
        self.assertIn("tests/test_launch.py:9: local-script discovery: execution literal coverage limit exceeded",
                      observations)

    def test_literal_unittest_names_select_test_sources(self):
        files = {"tests/test_named.py": self.UNRESOLVED, "tests/helper.py": "pass\n"}
        for command in ("python -m unittest tests.test_named", "python -m unittest -v tests.test_named.Case.test_x",
                        "python3 -m unittest --failfast --buffer tests.test_named json.tests"):
            with self.subTest(command=command):
                selected, errors, observations = discover_boundary([("bash", command, "")], files)
                self.assertEqual(errors, [])
                self.assertIn("tests/test_named.py", selected)
                self.assertNotIn("tests/helper.py", selected)
                self.assertEqual(sites(observations), {"tests/test_named.py:2"})

    def test_unmodeled_unittest_invocations_still_fail(self):
        files = {"tests/test_named.py": "pass\n", "tests/pkg/__init__.py": "pass\n"}
        for command in ("python -m unittest", "python -m unittest -v", "python -m unittest tests",
                        "python -m unittest tests.pkg.test_x", "python -m unittest tests.test_missing",
                        'python -m unittest "$NAME"', "python -m unittest -k fast tests.test_named",
                        "python -m unittest tests/test_missing.py", "python -m unittest ../outside/test_x.py"):
            with self.subTest(command=command):
                _, errors, observations = discover_boundary([("bash", command, "")], files)
                self.assertEqual(len(errors), 1, errors)
                self.assertTrue(".github/actions/dormant/action.yml:" in errors[0], errors)
                self.assertEqual(observations, [])

    def test_unittest_file_operand_is_also_a_literal_reference(self):
        # Rule 1 includes the operand from the action itself, a non-test path.
        selected, errors, observations = discover_boundary(
            [("bash", "python -m unittest tests/test_named.py", "")], {"tests/test_named.py": self.UNRESOLVED})
        self.assertIn("tests/test_named.py", selected)
        self.assertEqual(sites(errors), {"tests/test_named.py:2"}, errors)
        self.assertEqual(observations, [])

    def test_test_named_files_outside_the_selection_keep_full_rules(self):
        files = {"tests/check_entry.py": "import subprocess, sys\nimport test_unselected\n"
                                         "subprocess.run([sys.executable, 'tools/test_outside.py'])\n",
                 "tests/test_unselected.py": self.UNRESOLVED, "tools/test_outside.py": self.UNRESOLVED,
                 "elsewhere/test_unreached.py": self.UNRESOLVED}
        selected, errors, observations = discover_boundary(
            [("bash", "python -m unittest discover -s tests -p 'check_*.py'", "")], files)
        self.assertNotIn("elsewhere/test_unreached.py", selected)
        self.assertEqual(sites(errors), {"tests/test_unselected.py:2", "tools/test_outside.py:2"}, errors)
        self.assertEqual(observations, [])

    def test_product_imports_and_direct_runs_keep_full_rules_in_selected_tests(self):
        files = {"tests/test_shared.py": self.UNRESOLVED, "tests/test_direct.py": self.UNRESOLVED,
                 "tests/test_only.py": self.UNRESOLVED,
                 "tools/check.py": "from tests import test_shared\n"}
        selected, errors, observations = discover_boundary(
            [self.DISCOVER, ("bash", "python tools/check.py", ""), ("bash", "python tests/test_direct.py", "")], files)
        self.assertTrue(set(files) <= selected, selected)
        self.assertEqual(sites(errors), {"tests/test_shared.py:2", "tests/test_direct.py:2"}, errors)
        self.assertEqual(sites(observations), {"tests/test_only.py:2"}, observations)

    def test_nested_and_recursive_discovery_keep_full_rules_outside_tests(self):
        outer = ("import subprocess, sys\n"
                 "subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'])\n"
                 "subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'nested', '-p', 'test_*.py'])\n"
                 "subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', '.', '-p', 'test_*.py'])\n")
        files = {"tests/test_outer.py": outer, "nested/__init__.py": self.UNRESOLVED,
                 "nested/empty/__init__.py": self.UNRESOLVED,
                 "nested/test_inner.py": "import helper\n" + self.UNRESOLVED, "nested/helper.py": self.UNRESOLVED,
                 "tools/test_cli.py": self.UNRESOLVED}
        selected, errors, observations = discover_boundary(
            [self.DISCOVER, ("bash", "python tools/test_cli.py", "")], files)
        self.assertTrue(set(files) <= selected, selected)
        # Initializers, imported helpers and action-run files keep full rules.
        self.assertEqual(sites(errors), {"nested/__init__.py:2", "nested/empty/__init__.py:2", "nested/helper.py:2",
                                         "tools/test_cli.py:2"}, errors)
        self.assertEqual(sites(observations), {"nested/test_inner.py:3"}, observations)

    def test_wrapper_proofs_imported_only_by_tests_stay_observations(self):
        files = {"tests/test_wrapper.py": "import subprocess\ndef launch(argv):\n    subprocess.run(argv)\n"
                                          "launch(['tool', '--check'])\n",
                 "tests/test_user.py": "import test_wrapper\n", "tools/check.py": "from tests import test_wrapper\n"}
        message = "tests/test_wrapper.py:3: local-script discovery: unresolved forwarded wrapper: its source is imported by other code"
        _, errors, observations = discover_boundary([self.DISCOVER], files)
        self.assertEqual((errors, observations), ([], [message]))
        _, errors, observations = discover_boundary([self.DISCOVER, ("bash", "python tools/check.py", "")], files)
        self.assertEqual((errors, observations), ([message], []))

    def test_boundary_site_in_a_file_reached_both_ways_stays_an_error(self):
        files = {"tests/test_both.py": self.UNRESOLVED, "tests/test_peer.py": "import test_both\n" + self.UNRESOLVED,
                 "tools/check.py": "import subprocess, sys\nsubprocess.run([sys.executable, 'tests/test_both.py'])\n"}
        for command in ("python tools/check.py", "echo tests/test_both.py"):
            with self.subTest(command=command):
                _, errors, observations = discover_boundary([self.DISCOVER, ("bash", command, "")], files)
                self.assertEqual(sites(errors), {"tests/test_both.py:2"}, errors)
                self.assertEqual(sites(observations), {"tests/test_peer.py:3"}, observations)

    def test_unsafe_forms_in_product_code_still_fail(self):
        files = {"tools/check.py": self.LAUNCHES, "tests/test_launch.py": self.LAUNCHES}
        _, errors, observations = discover_boundary(
            [self.DISCOVER, ("bash", "python tools/check.py", ""), ("bash", "python tests/test_launch.py", "")], files)
        self.assertEqual(sites(errors), {f"{path}:{line}" for path in files for line in self.LAUNCH_LINES}, errors)
        self.assertEqual(observations, [])

    def test_other_test_source_rules_and_global_limits_still_fail(self):
        rules = ("import os, subprocess, sys\n"
                 "os.environ['PYTHONPATH'] = 'tools'\n"
                 "sys.path.append('tools')\n"
                 "open(os.environ['GITHUB_ENV'], 'a')\n"
                 "runner = getattr(subprocess, 'run')\n"
                 "os.chdir('tools')\n")
        _, errors, observations = discover_boundary([self.DISCOVER], {"tests/test_rules.py": rules})
        self.assertEqual(sites(errors), {f"tests/test_rules.py:{line}" for line in range(2, 7)}, errors)
        self.assertEqual(observations, [])
        files = {"tests/test_limit.py": self.UNRESOLVED + "print('tools/extra.py')\n", "tools/extra.py": "pass\n"}
        with mock.patch.object(sys.modules[sc.Discovery.__module__], "MAX_FILES", 2):
            _, errors, observations = discover_boundary([self.DISCOVER], files)
        self.assertEqual(sites(errors), {"tests/test_limit.py:2", "tests/test_limit.py:3"}, errors)
        self.assertIn("module selected-file limit exceeded", " ".join(errors))
        self.assertEqual(observations, [])

    PRODUCT = ("import os, subprocess\n"
               "def launch(argv):\n"
               "    subprocess.run(argv)\n"
               "ENVIRONMENT = os.environ.copy()\n"
               "ENVIRONMENT['MODE'] = 'x'\n"
               "launch(['python3', 'tools/leaf.py'])\n"
               "subprocess.run(['python3', 'tools/leaf.py'], env=ENVIRONMENT)\n")
    PROOFS = ["tools/run.py:3: local-script discovery: unresolved forwarded wrapper: its source is imported by other code",
              "tools/run.py:7: local-script discovery: unresolved module-level environment copy: its source is imported "
              "by other code"]

    def test_product_proofs_imported_only_by_test_sources_are_observations(self):
        files = {"tools/run.py": self.PRODUCT, "tools/leaf.py": "pass\n", "tests/test_run.py": "from tools import run\n"}
        product = ("bash", "python tools/run.py", "")
        selected, errors, observations = discover_boundary([self.DISCOVER, product], files)
        self.assertEqual((errors, observations), ([], self.PROOFS))
        self.assertTrue(set(files) <= selected, selected)
        cases = {
            "product_importer": ([self.DISCOVER, product, ("bash", "python tools/check.py", "")],
                                 {"tools/check.py": "from tools import run\n"}),
            "importer_run_by_product": ([self.DISCOVER, product, ("bash", "python tests/test_run.py", "")], {}),
            "importer_names_workflow_file": ([self.DISCOVER, product], {
                "tests/test_run.py": "from tools import run\nSUMMARY = 'echo done >> \"$GITHUB_STEP_SUMMARY\"'\n"}),
            "importer_not_test_named": ([("bash", "python -m unittest discover -s tests -p 'check_*.py'", ""), product],
                                        {"tests/test_run.py": "pass\n", "tests/check_run.py": "from tools import run\n"}),
        }
        for label, (commands, changes) in cases.items():
            with self.subTest(case=label):
                _, errors, observations = discover_boundary(commands, {**files, **changes})
                self.assertEqual((errors, observations), (self.PROOFS, []))
        limited = {**files, "tools/leaf.py": "print('tools/extra.py')\n", "tools/extra.py": "pass\n"}
        with mock.patch.object(sys.modules[sc.Discovery.__module__], "MAX_FILES", 4):
            _, errors, observations = discover_boundary([self.DISCOVER, product], limited)
        self.assertTrue(set(self.PROOFS) <= set(errors), errors)
        self.assertIn("module selected-file limit exceeded", " ".join(errors))
        self.assertEqual(observations, [])

    def test_boundary_sites_that_could_write_workflow_command_files_stay_errors(self):
        launch = "import os, subprocess, sys\nsubprocess.run(command)\n"
        _, errors, observations = discover_boundary([self.DISCOVER], {"tests/test_rules.py": launch})
        self.assertEqual((errors, sites(observations)), ([], {"tests/test_rules.py:2"}))
        refused = ("tests/test_rules.py:2: local-script discovery: unresolved computed Python script invocation; "
                   "unsafe or unresolved forwarding; no test boundary: the source names a GitHub workflow command file")
        texts = {
            "env_file": "TEXT = 'echo MODE=x >> \"$GITHUB_ENV\"'\n",
            "path_file": "TEXT = 'echo /opt/bin >> $github_path'\n",
            "output_file": "TEXT = 'print(1, file=open(os.environ[\"GITHUB_OUTPUT\"], \"a\"))'\n",
            "state_file": "TEXT = f'{value} >> $GITHUB_STATE'\n",
            "summary_file": "TEXT = b'Github_Step_Summary'\n",
            "set_env": "TEXT = 'echo \"::set-env name=MODE::x\"'\n",
            "add_path": "TEXT = '::ADD-PATH::/opt/bin'\n",
            "set_output": "TEXT = '::set-output name=mode::x'\n",
            "save_state": "TEXT = '::save-state name=mode::x'\n",
            "shell_program": "subprocess.run(['bash', '-c', 'echo x >> \"$GITHUB_OUTPUT\"'], env=environment)\n",
            "inline_program": "subprocess.run([sys.executable, '-c', 'import os\\nopen(os.environ[\"GITHUB_STATE\"])'],"
                              " cwd=directory)\n",
        }
        for label, text in texts.items():
            with self.subTest(case=label):
                _, errors, observations = discover_boundary([self.DISCOVER], {"tests/test_rules.py": launch + text})
                self.assertIn(refused, errors)
                self.assertTrue(all(error.endswith("names a GitHub workflow command file") for error in errors), errors)
                self.assertEqual(observations, [])

    def test_only_selected_test_named_sources_keep_the_boundary(self):
        files = {"tests/test_named.py": self.UNRESOLVED, "tests/helper_named.py": self.UNRESOLVED,
                 "tests/Test_upper.py": self.UNRESOLVED, "tests/check_named.py": self.UNRESOLVED}
        _, errors, observations = discover_boundary(
            [("bash", "python -m unittest discover -s tests -p '*.py'", "")], files)
        self.assertEqual(sites(errors), {"tests/helper_named.py:2", "tests/Test_upper.py:2", "tests/check_named.py:2"},
                         errors)
        self.assertEqual(sites(observations), {"tests/test_named.py:2"}, observations)
        for command, path in (("python -m unittest tests.check_named", "tests/check_named.py"),
                              ("python -m unittest tests.helper_named.Case", "tests/helper_named.py")):
            with self.subTest(command=command):
                _, errors, observations = discover_boundary([("bash", command, "")], files)
                self.assertEqual((sites(errors), observations), ({path + ":2"}, []))


class ComputedProcessContextTests(unittest.TestCase):
    """Computed directories, copied environments and wrapper parameters need explicit proofs."""

    def assert_refused(self, cases, files=None):
        for label, (source, diagnostic, *extra) in cases.items():
            with self.subTest(case=label):
                selected, errors = discover_python({**(files or {}), "entry.py": source, **(extra[0] if extra else {})})
                self.assertTrue(any(diagnostic in error for error in errors), (label, errors))

    DOTNET = (
        "import os, shutil, subprocess\n"
        "def build(directory, project):\n"
        "    dotnet = shutil.which('dotnet')\n"
        "    targets = [dotnet, 'msbuild', project, '-nologo', 'tools/leaf.py']\n"
        "    subprocess.run(targets, cwd=directory, env=os.environ.copy(), check=True)\n"
        "    environment = dict(os.environ, CustomAfterDirectoryBuildTargets=str(project))\n"
        "    subprocess.run(targets + ['-p:Extra=' + str(project)], cwd=directory, env=environment)\n"
        "    subprocess.run(['dotnet', 'build', project], cwd=directory)\n"
        "    subprocess.run([shutil.which('dotnet'), 'restore', project], cwd=directory, env=environment)\n"
        "def evaluate(directory, project):\n"
        "    import subprocess\n"
        "    subprocess.run(['dotnet', 'pack', project], cwd=directory, capture_output=True)\n"
        "build(root, project)\n"
    )
    INSTALLED_SDK = '{"sdk": {"version": "11.0.100", "rollForward": "latestPatch"}, "test": {"runner": "x"}}\n'

    def test_fixed_dotnet_operation_treats_computed_cwd_as_directory_data(self):
        selected, errors = discover_python({"entry.py": self.DOTNET, "tools/leaf.py": "pass\n",
                                            "global.json": self.INSTALLED_SDK, "src/global.json": "{}\n"})
        self.assertEqual(errors, [])
        self.assertIn("tools/leaf.py", selected)

    def test_fixed_dotnet_computed_cwd_refuses_host_sdk_and_process_indirection(self):
        call = "subprocess.run(['dotnet', 'build', project], cwd=directory)"
        base = "import os, shutil, subprocess\n" + call + "\n"
        lookup = "subprocess.run([shutil.which('dotnet'), 'build', project])"
        which = "import shutil, subprocess\n" + lookup + "\n"
        self.assertEqual(discover_python({"entry.py": which})[1], [])
        paths = '{"sdk": {"version": "11.0.100", "paths": [".dotnet", "$host$"]}}'
        cases = {
            "sdk_paths": (base, "global.json declares SDK search paths", {"global.json": paths}),
            "nested_sdk_paths": (base, "global.json declares SDK search paths", {"tests/fixture/global.json": paths}),
            "case_variant_name": (base, "global.json declares SDK search paths", {"tools/GLOBAL.JSON": paths}),
            "case_variant_key": (base, "global.json declares SDK search paths",
                                 {"global.json": '{"SDK": {"Paths": ["sdk"]}}'}),
            "duplicate_keys": (base, "unreadable global.json", {"global.json": '{"sdk": {}, "Sdk": {"paths": ["x"]}}'}),
            "commented": (base, "unreadable global.json", {"global.json": '// pinned\n{"sdk": {}}'}),
            "tracked_host": (base, "unproved .NET executable: tracked dotnet command", {"tools/dotnet": "#!/bin/sh\n"}),
            "tracked_windows_host": (base, "tracked dotnet command", {"tools/DotNet.cmd": "@echo off\n"}),
            "shell": (base.replace("cwd=directory)", "cwd=directory, shell=True)"), "shell execution"),
            "callback": (base.replace("cwd=directory)", "cwd=directory, preexec_fn=callback)"), "pre-execution callback"),
            "executable": (base.replace("cwd=directory)", "cwd=directory, executable=tool)"), "computed subprocess executable"),
            "replaced_api": (base.replace(call, "subprocess.run = replacement\n" + call), "unproved subprocess API for .NET"),
            "escaped_api": (base.replace(call, "register(subprocess)\n" + call), "unproved subprocess API for .NET"),
            "local_api": (base, "unproved subprocess API for .NET", {"subprocess.py": "pass\n"}),
            "tool_manifest": (base.replace("'build', project", "'tool', 'run', 'fixture'"), "computed subprocess cwd"),
            "other_operation": (base.replace("'build'", "'test'"), "computed subprocess cwd"),
            "computed_operation": (base.replace("'build'", "operation"), "computed subprocess cwd"),
            "computed_host": (base.replace("'dotnet'", "host"), "computed subprocess cwd"),
            "forwarded_data": (base.replace("project]", "*options]"), "computed subprocess cwd"),
            "host_environment": (base.replace("cwd=directory)", "cwd=directory, env=dict(os.environ, DOTNET_ROOT=root))"),
                                 "computed subprocess env"),
            "sdk_environment": (base.replace("cwd=directory)", "cwd=directory, env={**os.environ, 'MSBuildSDKsPath': 'sdk'})"),
                                "computed subprocess env"),
            "plugin_environment": (base.replace("cwd=directory)", "cwd=directory, env=dict(os.environ, NUGET_PLUGIN_PATHS=root))"),
                                   "computed subprocess env"),
            "literal_host_environment": (base.replace("cwd=directory)", "cwd=directory, env={'DOTNET_ROOT': 'sdk'})"),
                                         "environment affecting resolution"),
            "literal_path": (base.replace("cwd=directory)", "cwd=directory, env={'PATH': 'tools'})"),
                             "environment affecting resolution"),
            "which_tracked_host": (which, "tracked dotnet command", {"tools/dotnet.exe": "MZ\n"}),
            "which_path": (which.replace("'dotnet')", "'dotnet', path=root)"), "computed Python script invocation"),
            "which_tool": (which.replace("'dotnet')", "tool)"), "computed Python script invocation"),
            "which_replaced": (which.replace(lookup, "shutil.which = finder\n" + lookup), "computed Python script invocation"),
            "which_patched": (which.replace(lookup, "patch('shutil.which', finder)\n" + lookup),
                              "computed Python script invocation"),
            "which_escaped": (which.replace(lookup, "patch.object(shutil, 'which')\n" + lookup),
                              "computed Python script invocation"),
            "which_local": (which, "computed Python script invocation", {"shutil.py": "pass\n"}),
            "which_rebound": (which.replace(lookup, "dotnet = shutil.which('dotnet')\ndotnet = other\n"
                                            "subprocess.run([dotnet, 'build', project])"), "computed Python script invocation"),
        }
        listed = ("import subprocess\ndef build(directory, project):\n    targets = ['dotnet', 'build', project]\n"
                  "    MUTATION\n    subprocess.run(targets, cwd=directory)\n")
        for label, mutation in {"append": "targets.append(option)", "store": "targets[0] = host",
                                "alias": "alias = targets", "escape": "register(targets)", "rebound": "targets = other",
                                "extend": "targets += options"}.items():
            cases["list_" + label] = (listed.replace("MUTATION", mutation), "computed subprocess cwd")
        self.assert_refused(cases)

    ASSEMBLY = (
        "import os, shutil, subprocess\n"
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parent\n"
        "def run_suite(name, output, port):\n"
        "    env = os.environ.copy()\n"
        "    for key in tuple(env):\n"
        "        if key.startswith(('FIXTURE_', 'OTHER_')):\n"
        "            env.pop(key)\n"
        "    env['FIXTURE_HOME'] = str(output / 'home')\n"
        "    def command(arguments):\n"
        "        result = subprocess.run(arguments, env=env, capture_output=True)\n"
        "        record({'argv': list(arguments), 'exit': result.returncode})\n"
        "        return result\n"
        "    command(['dotnet', f'tests/{name}/bin/Release/{name}.dll', '-xml', str(output / 'x.xml')])\n"
        "    subprocess.run(['dotnet', str(ROOT / 'tests/fixture.dll'), output], check=True)\n"
        "    subprocess.run([shutil.which('dotnet'), f'{name}.dll', '--port', str(port)], cwd='tools')\n"
        "    subprocess.run(('dotnet', 'tests/literal.dll', name), env={'MODE': 'x'})\n"
        "    subprocess.run(['dotnet', f'{name}.dll', 'tools/leaf.py'])\n"
        "run_suite('Fixture', Path(out), 8080)\n"
    )

    def test_managed_assembly_launch_runs_an_application_dll_as_data(self):
        # hostfxr runs an existing first operand ending in .dll as an application.
        selected, errors = discover_python({"entry.py": self.ASSEMBLY, "tools/leaf.py": "pass\n",
                                            "global.json": self.INSTALLED_SDK, "docs/dotnet-notes.txt": "notes\n"})
        self.assertEqual(errors, [])
        self.assertIn("tools/leaf.py", selected)

    def test_managed_assembly_launch_refuses_other_operands_and_the_sdk_fallback(self):
        call = "subprocess.run(['dotnet', f'{name}.dll', '-xml', output])"
        base = "import os, shutil, subprocess\n" + call + "\n"
        self.assertEqual(discover_python({"entry.py": base})[1], [])
        computed = "computed Python script invocation"
        paths = '{"sdk": {"version": "11.0.100", "paths": [".dotnet", "$host$"]}}'
        custom = "class Fake:\n    def __truediv__(self, other):\n        return 'build'\n"
        cases = {
            "other_suffix": (base.replace("{name}.dll", "{name}.exe"), computed),
            "upper_suffix": (base.replace("{name}.dll", "{name}.DLL"), computed),
            "computed_suffix": (base.replace("{name}.dll", "{name}{suffix}"), computed),
            "trailing_value": (base.replace("{name}.dll", "{name}.dll{suffix}"), computed),
            "plain_value": (base.replace("f'{name}.dll'", "name"), computed),
            "concatenation": (base.replace("f'{name}.dll'", "name + '.dll'"), computed),
            "unproved_division": (base.replace("f'{name}.dll'", "root / 'fixture.dll'"), computed),
            "custom_division": (custom + base.replace("f'{name}.dll'", "Fake() / 'fixture.dll'"), computed),
            "exec_verb": (base.replace("'dotnet', ", "'dotnet', 'exec', "), computed),
            "computed_host": (base.replace("'dotnet'", "host"), computed),
            "which_path": (base.replace("'dotnet'", "shutil.which('dotnet', path=root)"), computed),
            "starred": (base.replace("output]", "*options]"), "unsafe or unresolved forwarding"),
            "computed_cwd": (base.replace("output])", "output], cwd=directory)"), "computed subprocess cwd"),
            "startup_hook": (base.replace("output])", "output], env=dict(os.environ, DOTNET_STARTUP_HOOKS=hook))"),
                             "computed subprocess env"),
            "host_trace": (base.replace("output])", "output], env={**os.environ, 'COREHOST_TRACE': '1'})"),
                           "computed subprocess env"),
            "msbuild": (base.replace("output])", "output], env=dict(os.environ, MSBuildExtensionsPath=root))"),
                        "computed subprocess env"),
            "profiler": (base.replace(call, "environment = os.environ.copy()\nenvironment['CORECLR_PROFILER'] = 'x'\n"
                                      + call.replace("output])", "output], env=environment)")), "computed subprocess env"),
            "literal_host_environment": (base.replace("output])", "output], env={'DOTNET_ROOT': 'sdk'})"),
                                         "environment affecting resolution"),
            "literal_loader_environment": (base.replace("output])", "output], env={'LD_PRELOAD': 'x.so'})"),
                                           "environment affecting resolution"),
            "shell": (base.replace("output])", "output], shell=True)"), "shell execution"),
            "callback": (base.replace("output])", "output], preexec_fn=callback)"), "pre-execution callback"),
            "executable": (base.replace("output])", "output], executable=tool)"), "computed subprocess executable"),
            "replaced_api": (base.replace(call, "subprocess.run = replacement\n" + call), "unproved subprocess API for .NET"),
            "local_api": (base, "unproved subprocess API for .NET", {"subprocess.py": "pass\n"}),
            "tracked_host": (base, "unproved .NET executable: tracked dotnet command", {"tools/dotnet": "#!/bin/sh\n"}),
            # A missing application .dll is routed to the SDK, which reads global.json
            # and resolves the operand as a dotnet-prefixed command or a local tool.
            "sdk_paths": (base, "global.json declares SDK search paths", {"global.json": paths}),
            "unreadable_global": (base, "unreadable global.json", {"tests/global.json": '// pinned\n{"sdk": {}}'}),
            "tracked_command": (base, "tracked dotnet-prefixed command: tools/dotnet-fixture.dll",
                                {"tools/dotnet-fixture.dll": "#!/bin/sh\n"}),
            "tracked_windows_command": (base, "tracked dotnet-prefixed command: bin/DotNet-Tests/fixture.DLL.CMD",
                                        {"bin/DotNet-Tests/fixture.DLL.CMD": "@echo off\n"}),
            "tool_manifest": (base, "tracked local tool manifest: .config/dotnet-tools.json",
                              {".config/dotnet-tools.json": "{}\n"}),
        }
        self.assert_refused(cases)

    TYPE_NAME = (
        "import subprocess\n"
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parent\n"
        "def main():\n"
        "    try:\n"
        "        subprocess.run(['python3', 'leaf.py'], cwd=ROOT / 'work', check=True)\n"
        "    except OSError as error:\n"
        "        print(f'{type(error).__name__}: {error}', type(error).__name__.lower())\n"
        "main()\n"
    )

    def test_type_name_reads_are_not_source_path_class_reflection(self):
        files = {"work/leaf.py": "pass\n"}
        selected, errors = discover_python({"entry.py": self.TYPE_NAME, **files})
        self.assertEqual(errors, [])
        self.assertIn("work/leaf.py", selected)
        read = "type(error).__name__.lower()"
        source = self.TYPE_NAME
        cases = {
            "class_object": source.replace(read, "type(error)"),
            "other_attribute": source.replace(read, "type(ROOT).__truediv__"),
            "name_store": source.replace("def main():\n", "def main():\n    type(ROOT).__name__ = 'Other'\n"),
            "method_store": source.replace("def main():\n", "def main():\n    type(ROOT).resolve = replacement\n"),
            "deletion": source.replace("def main():\n", "def main():\n    del type(ROOT).__name__\n"),
            "class_call": source.replace(read, "type(ROOT)('elsewhere')"),
            "class_creation": source.replace(read, "type('Fake', (), {}).__name__"),
            "starred": source.replace(read, "type(*values).__name__"),
            "keyword": source.replace(read, "type(error, extra=1).__name__"),
            "shadowed": source.replace("ROOT = ", "type = replacement\nROOT = "),
            "imported": source.replace("import subprocess\n", "import subprocess\nfrom fixture import type\n"),
            "dunder_class": source.replace(read, "error.__class__.__name__"),
        }
        for label, unsafe in cases.items():
            with self.subTest(case=label):
                _, errors = discover_python({"entry.py": unsafe, **files})
                self.assertTrue(any("computed subprocess cwd" in error for error in errors), (label, errors))

    COPIES = (
        "import os, subprocess\n"
        "from unittest.mock import patch\n"
        "def invoke(mode):\n"
        "    environment = os.environ.copy()\n"
        "    environment.pop('MODE', None)\n"
        "    if mode:\n"
        "        environment['MODE'] = str(mode)\n"
        "        environment['HOME'] = '/fixture/home'\n"
        "    for name in ('FIXTURE_A', 'FIXTURE_B'):\n"
        "        environment.pop(name, None)\n"
        "    for key in list(environment):\n"
        "        if key.startswith(('FIXTURE_', 'OTHER_')):\n"
        "            del environment[key]\n"
        "    if 'X' in environment and environment.get('Y') and os.environ['Z'] and 'Z' in os.environ:\n"
        "        print(environment['X'], len(environment))\n"
        "    subprocess.run(['python3', 'leaf.py'], env=environment)\n"
        "    subprocess.run(['python3', 'leaf.py'], env={**os.environ, 'MODE': f'{mode}-x'})\n"
        "    subprocess.run(['python3', 'leaf.py'], env=dict(os.environ, MODE=mode, ROOT=os.devnull))\n"
        "    with patch.dict(os.environ, {'FIXTURE_A': '1'}):\n"
        "        subprocess.run(['python3', 'leaf.py'], env=os.environ.copy())\n"
        "invoke('x')\n"
    )

    def test_copied_environments_accept_only_literal_safe_key_changes(self):
        selected, errors = discover_python({"entry.py": self.COPIES, "leaf.py": "pass\n"})
        self.assertEqual(errors, [])
        self.assertIn("leaf.py", selected)
        source = self.COPIES
        cases = {
            "resolution_store": source.replace("environment['MODE'] = str(mode)", "environment['PATH'] = str(mode)"),
            "python_store": source.replace("environment['MODE'] = str(mode)", "environment['PYTHONPATH'] = 'x'"),
            "resolution_removal": source.replace("environment.pop('MODE', None)", "environment.pop('PATH', None)"),
            "resolution_deletion": source.replace("environment.pop('MODE', None)", "del environment['PYTHONHOME']"),
            "loop_removal": source.replace("('FIXTURE_A', 'FIXTURE_B')", "('FIXTURE_A', 'PATH')"),
            "prefix_removal": source.replace("('FIXTURE_', 'OTHER_')", "('FIXTURE_', 'PYTH')"),
            "dict_resolution": source.replace("MODE=mode, ROOT", "PATH=mode, ROOT"),
            "display_resolution": source.replace("'MODE': f'{mode}-x'", "'NODE_OPTIONS': f'{mode}-x'"),
            "display_expansion": source.replace("'MODE': f'{mode}-x'", "**extra"),
            "dict_expansion": source.replace("MODE=mode, ROOT=os.devnull", "**extra"),
            "computed_key": source.replace("environment['MODE'] = str(mode)", "environment[mode] = 'x'"),
            "computed_update": source.replace("environment.pop('MODE', None)", "environment.update(extra)"),
            "unknown_value": source.replace("environment['MODE'] = str(mode)", "environment['MODE'] = unknown()"),
            "method_value": source.replace("environment['MODE'] = str(mode)", "environment['MODE'] = mode.strip()"),
            "computed_home": source.replace("environment['HOME'] = '/fixture/home'", "environment['HOME'] = mode"),
            "alias": source.replace("    environment.pop('MODE', None)", "    alias = environment"),
            "callback": source.replace("    environment.pop('MODE', None)", "    mutate(environment)"),
            "value_escape": source.replace("environment['MODE'] = str(mode)", "environment['MODE'] = str(environment)"),
            "clear": source.replace("environment.pop('MODE', None)", "environment.clear()"),
            "dunder": source.replace("environment.pop('MODE', None)", "environment.__setitem__('PATH', '.')"),
            "rebound": source.replace("    environment.pop('MODE', None)", "    environment = supplied"),
            "global": source.replace("def invoke(mode):\n", "def invoke(mode):\n    global environment\n"),
            "loop_rebinding": source.replace("        environment.pop(name, None)", "        name = 'PATH'\n        environment.pop(name, None)"),
            "replaced_source": source.replace("def invoke", "os.environ = {}\ndef invoke"),
            "source_alias": source.replace("def invoke", "mapping = os.environ\ndef invoke"),
            "source_clear": source.replace("def invoke", "os.environ.clear()\ndef invoke"),
            "source_store": source.replace("def invoke", "os.environ['MODE'] = 'x'\ndef invoke"),
            "module_escape": source.replace("def invoke", "patch.object(os, 'environ', {})\ndef invoke"),
            "unknown_patch": source.replace("from unittest.mock import patch", "from injected import patch"),
            "patched_patch": source.replace("def invoke", "patch.dict = replacement\ndef invoke"),
            "shadowed_dict": source.replace("def invoke", "def dict(*args, **kwargs):\n    return {'PATH': '.'}\ndef invoke"),
            "shadowed_str": source.replace("def invoke", "str = replacement\ndef invoke"),
            "shadowed_list": source.replace("def invoke", "from injected import list\ndef invoke"),
            "fake_consumer": source.replace("    subprocess.run(['python3', 'leaf.py'], env=environment)",
                                            "    fake.run(['python3', 'leaf.py'], env=environment)\n"
                                            "    subprocess.run(['python3', 'leaf.py'], env=environment)").replace(
                "import os, subprocess", "import os, subprocess, fixture as fake"),
            "local_api": source.replace("def invoke", "class subprocess:\n    pass\ndef invoke"),
        }
        for label, unsafe in cases.items():
            with self.subTest(case=label):
                _, errors = discover_python({"entry.py": unsafe, "leaf.py": "pass\n"})
                self.assertTrue(any("computed subprocess env" in error or "affecting resolution" in error
                                    for error in errors), (label, errors))

    INSTANCE = (
        "import os, subprocess, unittest\n"
        "class Fixture(unittest.TestCase):\n"
        "    def setUp(self):\n"
        "        self.env = os.environ.copy()\n"
        "        self.env.pop('MODE', None)\n"
        "    def invoke(self, mode):\n"
        "        self.env['MODE'] = mode\n"
        "        return subprocess.run(['python3', 'leaf.py'], env=self.env)\n"
    )

    def test_instance_environment_requires_every_assignment_and_reference_proved(self):
        for variant in (self.INSTANCE, self.INSTANCE.replace("(unittest.TestCase)", "(object)"),
                        self.INSTANCE.replace("(unittest.TestCase)", "(TestCase)").replace(
                            "import os, subprocess, unittest", "import os, subprocess\nfrom unittest import TestCase")):
            selected, errors = discover_python({"entry.py": variant, "leaf.py": "pass\n"})
            self.assertEqual(errors, [])
            self.assertIn("leaf.py", selected)
        source = self.INSTANCE
        cases = {
            "resolution_store": source.replace("self.env['MODE'] = mode", "self.env['PATH'] = mode"),
            "foreign_store": source + "def replace(other):\n    other.env = {'PATH': '.'}\n",
            "foreign_mutation": source + "def replace(other):\n    other.env['PATH'] = '.'\n",
            "class_default": source.replace("    def setUp", "    env = {'PATH': '.'}\n    def setUp"),
            "property": source.replace("    def setUp", "    def env(self):\n        return {}\n    def setUp"),
            "setattr": source + "setattr(Fixture, 'env', {})\n",
            "computed_getattr": source + "getattr(Fixture(), name)\n",
            "vars": source + "vars(Fixture())\n",
            "dict_access": source.replace("self.env.pop('MODE', None)", "self.__dict__.update(env={})"),
            "subclass_store": source + "class Child(Fixture):\n    def setUp(self):\n        self.env = os.environ.copy()\n",
            "unknown_base": source.replace("(unittest.TestCase)", "(Base)"),
            "rebound_unittest": source.replace("class Fixture", "unittest = fake\nclass Fixture"),
            "foreign_testcase": source.replace("(unittest.TestCase)", "(TestCase)").replace(
                "import os, subprocess, unittest", "import os, subprocess\nfrom fixtures import TestCase"),
            "shadowed_object": source.replace("(unittest.TestCase)", "(object)").replace("class Fixture", "object = Base\nclass Fixture"),
            "metaclass": source.replace("(unittest.TestCase)", "(unittest.TestCase, metaclass=Meta)"),
            "decorated": source.replace("class Fixture", "@decorate\nclass Fixture"),
            "not_a_copy": source.replace("os.environ.copy()", "dict(supplied)"),
            "escape": source.replace("self.env.pop('MODE', None)", "register(self.env)"),
            "static_receiver": source.replace("    def invoke", "    @staticmethod\n    def invoke"),
            "rebound_receiver": source.replace("        self.env['MODE'] = mode", "        self = other"),
        }
        for label, unsafe in cases.items():
            with self.subTest(case=label):
                _, errors = discover_python({"entry.py": unsafe, "leaf.py": "pass\n"})
                self.assertTrue(any("computed subprocess env" in error for error in errors), (label, errors))
        _, errors = discover_python({"entry.py": source, "leaf.py": "pass\n", "unittest/__init__.py": "pass\n"})
        self.assertTrue(any("computed subprocess env" in error for error in errors), errors)
        _, errors = discover_python({"entry.py": "import fixture\n", "fixture.py": source, "leaf.py": "pass\n"})
        self.assertIn("fixture.py:8: local-script discovery: unresolved instance environment copy: its source is "
                      "imported by other code", errors)

    WRAPPER = (
        "import os, subprocess\n"
        "def run(command, cwd=None, env=None):\n"
        "    print(' '.join(map(str, command)), len(command), command[0])\n"
        "    return subprocess.run(list(map(str, command)), cwd=cwd, env=env, check=True)\n"
        "def launch(command, overrides):\n"
        "    return run(command, 'work', overrides)\n"
        "environment = os.environ.copy()\n"
        "environment['MODE'] = 'x'\n"
        "run(['python3', 'leaf.py'], 'work', environment)\n"
        "run(['python3', 'other.py'])\n"
        "run(['git', 'status'], cwd=supplied)\n"
        "launch(['python3', 'deep.py'], os.environ.copy())\n"
    )

    def test_wrapper_parameters_are_proved_at_every_direct_call_site(self):
        files = {"leaf.py": "pass\n", "work/leaf.py": "import helper\n", "work/helper.py": "pass\n", "other.py": "pass\n",
                 "work/deep.py": "pass\n"}
        selected, errors = discover_python({"entry.py": self.WRAPPER, **files})
        self.assertEqual(errors, [])
        for path in ("work/leaf.py", "work/helper.py", "other.py", "work/deep.py"):
            self.assertIn(path, selected)
        source = self.WRAPPER
        cases = {
            "computed_argv": source.replace("run(['python3', 'other.py'])", "run([sys.executable, script])"),
            "computed_cwd": source.replace("run(['python3', 'other.py'])", "run(['python3', 'other.py'], directory)"),
            "resolution_env": source.replace("run(['python3', 'other.py'])", "run(['python3', 'other.py'], 'work', {'PATH': '.'})"),
            "unknown_env": source.replace("run(['python3', 'other.py'])", "run(['python3', 'other.py'], 'work', supplied)"),
            "caller_env_store": source.replace("environment['MODE'] = 'x'", "environment['PATH'] = 'x'"),
            "argv_mutation": source.replace("    print(", "    command.append('-c')\n    print("),
            "argv_escape": source.replace("    print(", "    register(command)\n    print("),
            "argv_rebound": source.replace("    print(", "    command = other\n    print("),
            "env_mutation": source.replace("    print(", "    env['PATH'] = '.'\n    print("),
            "alias": source + "alias = run\n",
            "callback": source + "register(run)\n",
            "keyword_expansion": source + "run(['python3', 'leaf.py'], **options)\n",
            "positional_expansion": source + "run(*arguments)\n",
            "recursion": source.replace("    return subprocess.run", "    run(command)\n    return subprocess.run"),
            "decorated": source.replace("def run(", "@decorate\ndef run("),
            "computed_default": source.replace("cwd=None", "cwd=DIRECTORY"),
            "missing_argument": source + "run()\n",
            "split_string": source + "run('python3 leaf.py')\n",
            "callers": source + "run(['python3', 'leaf.py'])\n" * 129,
            "depth": "import subprocess\ndef run0(command):\n    subprocess.run(command)\n" + "".join(
                f"def run{index}(command):\n    return run{index - 1}(command)\n" for index in range(1, 10))
                + "run9(['python3', 'leaf.py'])\n",
        }
        for label, unsafe in cases.items():
            with self.subTest(case=label):
                _, errors = discover_python({"entry.py": unsafe, **files})
                self.assertTrue(errors and all("entry.py:" in error for error in errors), (label, errors))
        # Callers and mutations in an importing source are not visible to the proof.
        _, errors = discover_python({"entry.py": "import tooling\n", "tooling.py": source, **files})
        self.assertIn("tooling.py:4: local-script discovery: unresolved forwarded wrapper: its source is imported by "
                      "other code", errors)
        self.assertTrue(any("module-level environment copy: its source is imported" in error for error in errors), errors)
        method = ("import subprocess\nclass Runner:\n    def run(self, command):\n        return subprocess.run(command)\n"
                  "Runner().run(['python3', 'leaf.py'])\n")
        _, errors = discover_python({"entry.py": method, **files})
        self.assertTrue(any("unresolved computed Python script invocation" in error for error in errors), errors)

    def test_finite_list_rows_reach_only_their_own_argv(self):
        loop = ("import subprocess\ndef main():\n    for arguments in (['python3', 'leaf.py'], ['python3', 'other.py']):\n"
                "        subprocess.run(arguments, check=True)\nmain()\n")
        selected, errors = discover_python({"entry.py": loop, "leaf.py": "pass\n", "other.py": "pass\n"})
        self.assertEqual(errors, [])
        self.assertTrue({"leaf.py", "other.py"} <= set(selected))
        for label, unsafe in {
            "append": loop.replace("        subprocess.run", "        arguments.append('-c')\n        subprocess.run"),
            "escape": loop.replace("        subprocess.run", "        register(arguments)\n        subprocess.run"),
            "nonlocal": loop.replace("def main():\n", "def main():\n    def swap():\n        nonlocal arguments\n"
                                     "        arguments = ['bash', 'hidden.sh']\n    arguments = None\n"),
            "global": loop + "def swap():\n    global arguments\n    arguments = ['bash', 'hidden.sh']\n",
        }.items():
            with self.subTest(case=label):
                _, errors = discover_python({"entry.py": unsafe, "leaf.py": "pass\n", "other.py": "pass\n"})
                self.assertTrue(any("unsafe or unresolved forwarding" in error for error in errors), (label, errors))


class ScanTests(acceptance_tests.Harness):
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
            ("import runtime from 'node:process'; runtime.getBuiltinModule('child_process').exec(process.env.CMD);", "reflective JavaScript execution"),
            ("import {default as runtime} from 'node:process'; runtime.getBuiltinModule('child_process').exec(process.env.CMD);", "reflective JavaScript execution"),
            ("import runtime = require('node:process'); runtime.getBuiltinModule('child_process').exec(process.env.CMD);", "reflective JavaScript execution"),
            ("import runtime from 'node:process'; function f(p) { p.getBuiltinModule('child_process').exec(process.env.CMD); } f(runtime);", "API escape"),
            ("process[process.env.API]('child_process').exec(process.env.CMD);", "reflective JavaScript process/import API"),

            ("import * as runtime from 'process'; runtime.getBuiltinModule('child_process').exec(process.env.CMD);", "reflective JavaScript execution"),
            ("import {getBuiltinModule as load} from 'node:process'; load('child_process').exec(process.env.CMD);", "reflective JavaScript execution"),
            ("const runtime = require('node:process'); runtime.getBuiltinModule('child_process').exec(process.env.CMD);", "reflective JavaScript execution"),
            ("function f(p) { p.getBuiltinModule('child_process').exec(process.env.CMD); } f(process);", "API escape"),
            ("function f(p) { p.getBuiltinModule('child_process').exec(process.env.CMD); } f(globalThis.process);", "API escape"),
            ("function f(p) { p.getBuiltinModule('child_process').exec(process.env.CMD); } f(globalThis['process']);", "API escape"),
            ("function f(p) { p.getBuiltinModule('child_process').exec(process.env.CMD); } f(global['process']);", "API escape"),
            ("const root = globalThis; root.process.getBuiltinModule('child_process').exec(process.env.CMD);", "reflective JavaScript execution"),
            ("const root = global; root.process.getBuiltinModule('child_process').exec(process.env.CMD);", "reflective JavaScript execution"),
            ("function f(root) { root.process.getBuiltinModule('child_process').exec(process.env.CMD); } f(globalThis);", "API escape"),
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

    def test_builtin_process_imports_preserve_ordinary_environment_and_argument_reads(self):
        for source in (
            "import runtime from 'node:process'; const mode = runtime.env.CI; const args = runtime.argv.slice(2);\n",
            "import {default as runtime} from 'node:process'; const mode = runtime.env.CI; const args = runtime.argv.slice(2);\n",
            "import * as runtime from 'process'; const mode = runtime.env.CI; const args = runtime.argv.slice(2);\n",
            "import {env, argv} from 'node:process'; const mode = env.CI; const args = argv.slice(2);\n",
            "const runtime = require('process'); const mode = runtime.env.CI; const args = runtime.argv.slice(2);\n",
            "const runtime = globalThis.process; const mode = runtime.env.CI; const args = runtime.argv.slice(2);\n",
            "const runtime = globalThis['process']; const mode = runtime.env.CI; const args = runtime.argv.slice(2);\n",
            "const root = globalThis; const mode = root.process.env.CI; const args = root.process.argv.slice(2);\n",
            "const root = global; const mode = root.process.env.CI; const args = root.process.argv.slice(2);\n",
        ):
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "node script.js", "")], {
                    "script.js": source + block("javascript", "process reads"),
                })
                self.assertTrue(all(not row["errors"] for row in report["modules"]), report)
                self.assertTrue(all("script.js" in {item["path"] for item in row["files"]} for row in report["modules"]), report)
                self.assert_coverage(report, "script.js", None)

    def test_data_only_mkdir_accepts_parameters_but_not_execution(self):
        report = self.coverage_case([("bash", 'mkdir -p "$REPORT_DIRECTORY"\npython3 leaf.py', "")], {"leaf.py": COPY})
        self.assert_coverage(report, "leaf.py", None)
        for command in ('mkdir -p "$(python3 hidden.py)"', 'mkdir -p "`python3 hidden.py`"',
                        'mkdir -p "${DIRECTORY:-$(python3 hidden.py)}"', '$DIRECTORY_TOOL -p "$REPORT_DIRECTORY"'):
            with self.subTest(command=command):
                report = self.coverage_case([("bash", command, "")], {"hidden.py": COPY})
                self.assertEqual(report["result"], "fail", report)
                self.assertTrue(all(row["errors"] for row in report["modules"]), report)

    def test_subprocess_environment_copy_preserves_source_resolution(self):
        source = (
            "import os, subprocess\n"
            "def invoke():\n"
            "    environment = os.environ.copy()\n"
            "    for key in tuple(environment):\n"
            "        if key.startswith('GIT_'):\n"
            "            environment.pop(key)\n"
            "    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_LAZY_FETCH='1')\n"
            "    subprocess.run(['python3', 'leaf.py'], env=environment)\n"
            "invoke()\n"
        )
        self.assert_coverage(self.coverage_case([("bash", "python3 entry.py", "")],
                                               {"entry.py": source, "leaf.py": COPY}), "leaf.py", None)
        cases = {
            "resolution_update": source.replace("GIT_CONFIG_NOSYSTEM='1'", "PATH='.'"),
            "python_prefix_update": source.replace("GIT_CONFIG_NOSYSTEM='1'", "PYTHONSAFEPATH='0'"),
            "lowercase_npm_update": source.replace("GIT_CONFIG_NOSYSTEM='1'", "npm_config_script_shell='python3'"),
            "node_update": source.replace("GIT_CONFIG_NOSYSTEM='1'", "NODE_OPTIONS='--require hidden.js'"),
            "powershell_update": source.replace("GIT_CONFIG_NOSYSTEM='1'", "PSModulePath='.'"),
            "resolution_delete": source.replace("key.startswith('GIT_')", "key.startswith('PATH')"),
            "computed_update": source.replace("environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_LAZY_FETCH='1')", "environment.update(mapping)"),
            "computed_value": source.replace("GIT_CONFIG_NOSYSTEM='1'", "GIT_CONFIG_NOSYSTEM=unknown()"),
            "alias_escape": source.replace("    for key", "    alias = environment\n    for key", 1),
            "imported_copy": source.replace("    subprocess.run", "    from injected import mapping as environment\n    subprocess.run"),
            "class_copy": source.replace("    subprocess.run", "    class environment:\n        pass\n    subprocess.run"),
            "callback_escape": source.replace("    for key", "    mutate(environment)\n    for key", 1),
            "shadowed_source": source.replace("def invoke():", "def invoke(os):"),
            "replaced_source": source.replace("def invoke():", "os.environ = replacement\ndef invoke():"),
            "source_alias_escape": source.replace("def invoke():", "mapping = os.environ\ndef invoke():"),
            "source_method_escape": source.replace("def invoke():", "mutate(os.environ.copy)\ndef invoke():"),
            "source_bound_mapping_escape": source.replace("def invoke():", "mutate(os.environ.copy.__self__)\ndef invoke():"),
            "source_clear": source.replace("def invoke():", "os.environ.clear()\ndef invoke():"),
            "shadowed_tuple": source.replace("def invoke():", "def tuple(mapping):\n    mapping['PATH'] = '.'\n    return []\ndef invoke():"),
            "imported_tuple": source.replace("def invoke():", "from collections import deque as tuple\ndef invoke():"),
            "rebound_loop_key": source.replace("            environment.pop(key)", "            key = 'PATH'\n            environment.pop(key)"),
        }
        for label, unsafe in cases.items():
            with self.subTest(case=label):
                report = self.coverage_case([("bash", "python3 entry.py", "")], {"entry.py": unsafe, "leaf.py": COPY})
                self.assertEqual(report["result"], "fail", report)
                self.assertTrue(all(any("computed subprocess env" in error for error in row["errors"])
                                    for row in report["modules"]), report)

    def test_bounded_forwarding_includes_direct_and_literal_loop_sources(self):
        for source in (
            "import subprocess\ndef launch(*parts):\n    return subprocess.run(parts)\nlaunch('python3', 'leaf.py')\n",
            "import subprocess\ndef launch(root, *parts):\n    return subprocess.run(['python3', *parts])\n"
            "def forward(*parts):\n    return launch('.', *parts)\n"
            "for parts in (('leaf.py',), ('leaf.py',)):\n    forward(*parts)\n",
            "import subprocess\nfor parts in (('python3', 'leaf.py'), ('python3', 'leaf.py')):\n    subprocess.run(parts)\n",
        ):
            with self.subTest(source=source):
                self.assert_coverage(self.coverage_case([("bash", "python3 entry.py", "")],
                                                       {"entry.py": source, "leaf.py": COPY}), "leaf.py", None)

    def test_source_relative_pathlib_cwd_discovers_actual_child(self):
        for declaration, root in (
                ("from pathlib import Path", "Path(__file__).resolve().parents[1]"),
                ("from pathlib import Path as FilePath", "FilePath(__file__).resolve().parent.parent"),
                ("import pathlib as paths", "paths.Path(__file__).resolve().parents[1]")):
            with self.subTest(declaration=declaration):
                source = (declaration + "\nimport subprocess\nROOT = " + root + "\n"
                          "CHILD = ROOT / 'nested'\n"
                          "def invoke():\n    subprocess.run(['python', 'leaf.py'], cwd=str(CHILD))\ninvoke()\n")
                report = self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": source, "nested/leaf.py": COPY,
                    "leaf.py": "print('root decoy')\n"})
                self.assert_coverage(report, "nested/leaf.py", None)

        source = ("from pathlib import Path\nimport subprocess\nROOT = Path(__file__).resolve().parents[1]\n"
                  "subprocess.run(['python', 'leaf.py'], cwd=ROOT / 'support')\n")
        report = self.coverage_case([("bash", "python $GITHUB_WORKSPACE/scripts/start.py",
                                      "      working-directory: nested\n")], {
            "scripts/start.py": source, "support/leaf.py": COPY, "nested/marker.txt": "directory\n",
            "nested/support/leaf.py": "print('cwd decoy')\n"})
        self.assert_coverage(report, "support/leaf.py", None)

    def test_source_relative_search_path_discovers_imports_in_all_scopes(self):
        source = ("from pathlib import Path\nimport sys\nROOT = Path(__file__).resolve().parents[1]\n"
                  "import helper\nif enabled:\n    sys.path.insert(0, str(ROOT / 'support'))\n"
                  "def invoke():\n    import helper\n    import package.child\n")
        report = self.coverage_case([("bash", "python scripts/start.py", "")], {
            "scripts/start.py": source, "support/helper.py": COPY,
            "support/package/__init__.py": COPY, "support/package/child.py": COPY})
        for target in ("support/helper.py", "support/package/__init__.py", "support/package/child.py"):
            self.assert_coverage(report, target, None)

    def test_composed_source_script_paths_include_unknown_consumers_and_processes(self):
        prefix = "from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n"
        for invocation in (
                "record(ROOT / 'support' / 'leaf.py')",
                "import subprocess, sys\nsubprocess.run([sys.executable, str(ROOT / 'support' / 'leaf.py')])",
                "import subprocess, sys\nsubprocess.run([sys.executable, '-B', ROOT / 'support' / 'leaf.py'], cwd=ROOT / 'nested')",
                "import runpy\nrunpy.run_path(str(ROOT / 'support' / 'leaf.py'))"):
            with self.subTest(invocation=invocation):
                report = self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": prefix + invocation + "\n", "support/leaf.py": COPY,
                    "nested/marker.txt": "directory\n"})
                self.assert_coverage(report, "support/leaf.py", None)

    def test_literal_importlib_dashed_module_keeps_package_and_child_scope(self):
        scripts = {
            "scripts/start.py": "import importlib\nimportlib.import_module('fixtures.run-check')\n",
            "scripts/fixtures/__init__.py": "from . import setup\n" + block("python", "package initializer"),
            "scripts/fixtures/setup.py": COPY,
            "scripts/fixtures/run-check.py": ("import importlib\nimportlib.import_module(target)\n"
                                              + block("python", "dashed module")),
        }
        report = self.coverage_case([("bash", "python scripts/start.py", "")], scripts)
        for target in ("scripts/fixtures/__init__.py", "scripts/fixtures/setup.py", "scripts/fixtures/run-check.py"):
            self.assert_coverage(report, target, "unresolved computed Python import")
        scripts["scripts/start.py"] = "import importlib\nimportlib.import_module('../fixtures/run-check')\n"
        report = self.coverage_case([("bash", "python scripts/start.py", "")], scripts)
        self.assert_coverage(report, None, "unresolved local Python module")

    def test_python_file_argv_follows_the_script_before_forwarding_data(self):
        scripts = {
            "scripts/start.py": ("from pathlib import Path\nimport subprocess, sys\n"
                                 "launch = Path(__file__).with_name('leaf.py')\n"
                                 "subprocess.run([sys.executable, '-B', '--', launch, value, *items])\n"),
            "scripts/leaf.py": "import helper\n",
            "scripts/helper.py": COPY,
        }
        report = self.coverage_case([("bash", "python scripts/start.py", "")], scripts)
        self.assert_coverage(report, "scripts/helper.py", None)

        scripts["scripts/start.py"] = ("import subprocess, sys\n"
                                       "subprocess.run([sys.executable, 'leaf.py', value, 'literal.py'], cwd='work')\n")
        scripts.update({"work/leaf.py": "import helper\n", "work/helper.py": COPY, "work/literal.py": COPY})
        report = self.coverage_case([("bash", "python scripts/start.py", "")], scripts)
        for child in ("work/helper.py", "work/literal.py"):
            self.assert_coverage(report, child, None)

    def test_python_file_argv_refuses_indirection_before_the_script(self):
        prefix = "from pathlib import Path\nimport subprocess, sys\n"
        for arguments, options, diagnostic in (
                ("sys.executable, *options, 'leaf.py', value", "", "unsafe or unresolved forwarding"),
                ("sys.executable, '-m', module, value", "", "unresolved computed Python script invocation"),
                ("sys.executable, '-X', flag, 'leaf.py', value", "", "unresolved computed Python script invocation"),
                ("sys.executable, Path(__file__).with_name(name), value", "", "unresolved computed Python script invocation"),
                ("sys.executable, Path(__file__).with_name('../leaf.py'), value", "", "unresolved computed Python script invocation"),
                ("sys.executable, 'leaf.py', value", ", shell=True", "unsupported shell or pre-execution callback"),
                ("sys.executable, 'leaf.py', value", ", preexec_fn=callback", "unsupported shell or pre-execution callback"),
                ("sys.executable, 'unknown.py', value", "", "missing or unsafe regular script")):
            with self.subTest(arguments=arguments, options=options):
                report = self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": prefix + f"subprocess.run([{arguments}]{options})\n", "scripts/leaf.py": COPY,
                })
                self.assert_coverage(report, None, diagnostic)

        scripts = {"scripts/start.py": prefix + "subprocess.run([sys.executable, 'leaf.py', value])\n",
                   "scripts/leaf.py": "import runpy, sys\nrunpy.run_path(sys.argv[1])\n"}
        report = self.coverage_case([("bash", "python scripts/start.py", "")], scripts)
        self.assert_coverage(report, None, "unresolved computed Python script invocation")

    def test_source_relative_path_proofs_refuse_shadowing_mutation_and_escape(self):
        source = ("from pathlib import Path\nimport subprocess\nROOT = Path(__file__).resolve().parents[1]\n"
                  "def invoke():\n    subprocess.run(['python', 'leaf.py'], cwd=ROOT / 'support')\ninvoke()\n")
        cases = {
            "rebound_root": source.replace("def invoke():", "ROOT = replacement\ndef invoke():"),
            "shadowed_root": source.replace("def invoke():", "def invoke(ROOT):"),
            "alternate_scope": source.replace("def invoke():", "def other():\n    ROOT = replacement\ndef invoke():"),
            "shadowed_path": source.replace("def invoke():", "def other(Path):\n    pass\ndef invoke():"),
            "path_class_escape": source.replace("def invoke():", "mutate(Path)\ndef invoke():"),
            "path_class_alias": source.replace("def invoke():", "Alias = Path\ndef invoke():"),
            "path_class_mutation": source.replace("def invoke():", "Path.__truediv__ = replacement\ndef invoke():"),
            "path_instance_class": source.replace("def invoke():", "ROOT.__class__.__truediv__ = replacement\ndef invoke():"),
            "path_type_escape": source.replace("def invoke():", "Class = type(ROOT)\nmutate(Class)\ndef invoke():"),
            "pathlib_replaced": source.replace("from pathlib import Path", "from untrusted import Path"),
            "file_rebound": source.replace("def invoke():", "__file__ = '/elsewhere/start.py'\ndef invoke():"),
            "reflection": source.replace("def invoke():", "globals()['ROOT'] = replacement\ndef invoke():"),
            "cwd_factory": source.replace("Path(__file__).resolve().parents[1]", "Path.cwd()"),
            "untrusted_str": source.replace("def invoke():", "def str(value):\n    return '.'\ndef invoke():").replace("cwd=ROOT / 'support'", "cwd=str(ROOT / 'support')"),
            "root_escape": source.replace("ROOT / 'support'", "ROOT / '../outside'"),
            "absolute_escape": source.replace("ROOT / 'support'", "ROOT / '/outside'"),
            "shell_anchor": source.replace("ROOT / 'support'", "ROOT / '$GITHUB_WORKSPACE/support'"),
            "backslash": source.replace("ROOT / 'support'", "ROOT / '..\\\\support'"),
            "over_parent": source.replace("parents[1]", "parents[2]"),
            "computed_component": source.replace("ROOT / 'support'", "ROOT / component"),
            "non_directory": source.replace("ROOT / 'support'", "ROOT / 'support/leaf.py'"),
            "path_alias_write": source.replace("def invoke():", "ROOT.name = replacement\ndef invoke():"),
            "path_alias_class": source.replace("def invoke():", "Alias = ROOT\nAlias.__class__.__truediv__ = replacement\ndef invoke():"),
        }
        for label, unsafe in cases.items():
            with self.subTest(case=label):
                report = self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": unsafe, "support/leaf.py": COPY})
                self.assertTrue(all(any("subprocess cwd" in error or "working directory" in error for error in row["errors"])
                                    for row in report["modules"]), report)

    def test_source_relative_paths_refuse_linked_prefixes_and_shadowed_stdlib(self):
        for kind in ("symlink", "gitlink", "stdlib"):
            with self.subTest(kind=kind):
                w = self.workspace()
                for module in w.paths:
                    w.action(module, "python scripts/start.py")
                    w.write(module, "scripts/start.py", "from pathlib import Path\nimport subprocess\n"
                            "ROOT = Path(__file__).resolve().parents[1]\n"
                            "subprocess.run(['python', 'leaf.py'], cwd=(ROOT / 'linked').resolve().parent / 'support')\n")
                    w.write(module, "support/leaf.py", block("python"))
                    if kind == "symlink":
                        (w.paths[module] / "linked").symlink_to("../outside")
                    elif kind == "gitlink":
                        w.commit(w.paths[module])
                        revision = git(w.paths[module], "rev-parse", "HEAD")
                        git(w.paths[module], "update-index", "--add", "--cacheinfo", "160000," + revision + ",linked")
                    else:
                        w.write(module, "scripts/pathlib.py", "def Path(value):\n    return value\n")
                        w.write(module, "linked/marker.txt", "directory\n")
                    if kind == "gitlink":
                        git(w.paths[module], "commit", "--quiet", "-m", "unsafe source path")
                    else:
                        w.commit(w.paths[module])
                report = w.scan(self.factory)
                self.assertTrue(all(any("subprocess cwd" in error for error in row["errors"])
                                    for row in report["modules"]), report)

    def test_source_relative_search_path_refuses_unknown_or_aliased_roots(self):
        source = ("from pathlib import Path\nimport sys\nROOT = Path(__file__).resolve().parents[1]\n"
                  "sys.path.insert(0, str(ROOT / 'support'))\nimport helper\n")
        cases = {
            "dynamic_root": source.replace("ROOT / 'support'", "ROOT / supplied"),
            "external_root": source.replace("ROOT / 'support'", "ROOT / '../outside'"),
            "file_root": source.replace("ROOT / 'support'", "ROOT / 'support/helper.py'"),
            "missing_root": source.replace("ROOT / 'support'", "ROOT / 'missing'"),
            "aliased_path": source.replace("sys.path.insert", "alias = sys.path\nalias.insert"),
            "mutated_sys": source.replace("sys.path.insert", "sys.path = replacement\nsys.path.insert"),
            "path_escape": source.replace("import helper", "mutate(sys.path)\nimport helper"),
            "bound_method_escape": source.replace("import helper", "mutate(sys.path.append)\nimport helper"),
            "path_alias_escape": source.replace("import helper", "alias = sys.path\nmutate(alias)\nimport helper"),
            "computed_index": source.replace("insert(0,", "insert(index,"),
            "remove": source.replace("insert(0,", "remove("),
        }
        for label, unsafe in cases.items():
            with self.subTest(case=label):
                report = self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": unsafe, "support/helper.py": COPY})
                self.assertTrue(all(any("search-path mutation" in error for error in row["errors"])
                                    for row in report["modules"]), report)

    def test_forwarded_indirection_and_process_options_fail_closed(self):
        base = "import os, subprocess\ndef launch(*parts):\n    return subprocess.run(['python3', *parts])\nlaunch('leaf.py')\n"
        cases = {
            "dynamic_executable": base.replace("['python3', *parts]", "parts").replace("launch('leaf.py')", "launch(os.environ['TOOL'], 'leaf.py')"),
            "dynamic_interpreter_options": base.replace("launch('leaf.py')", "launch('-c', os.environ['CODE'])"),
            "alias": base.replace("launch('leaf.py')", "alias = launch\nalias('leaf.py')"),
            "import": base.replace("launch('leaf.py')", "from collections import deque as launch\nlaunch('leaf.py')"),
            "class": base.replace("launch('leaf.py')", "class launch:\n    pass\nlaunch('leaf.py')"),
            "local_shadow": base.replace("launch('leaf.py')", "def invoke(launch):\n    launch('leaf.py')\nlaunch('leaf.py')"),
            "global_replacement": base.replace("launch('leaf.py')", "globals()['launch'] = replacement\nlaunch('leaf.py')"),
            "callable_code_replacement": base.replace("launch('leaf.py')", "launch.__code__ = replacement\nlaunch('leaf.py')"),
            "decorator": base.replace("def launch", "@replacement\ndef launch"),
            "rebound_tuple": base.replace("    return subprocess", "    parts = unknown()\n    return subprocess"),
            "imported_varargs": base.replace("    return subprocess", "    from injected import arguments as parts\n    return subprocess"),
            "keyword_expansion": base.replace("launch('leaf.py')", "launch('leaf.py', **options)"),
            "shell": base.replace("*parts])", "*parts], shell=True)"),
            "cwd": base.replace("*parts])", "*parts], cwd=os.environ['DIR'])"),
            "env": base.replace("*parts])", "*parts], env={'PATH': '.'})"),
            "executable": base.replace("*parts])", "*parts], executable='other-python')"),
            "subprocess_class": base.replace("launch('leaf.py')", "class subprocess:\n    pass\nlaunch('leaf.py')"),
            "subprocess_import": base.replace("launch('leaf.py')", "import collections as subprocess\nlaunch('leaf.py')"),
            "loop_rebinding": "import subprocess\nfor parts in (('python3','leaf.py'),):\n    parts = unknown()\n    subprocess.run(parts)\n",
            "computed_loop": "import subprocess\nfor parts in unknown():\n    subprocess.run(parts)\n",
            "mutable_loop_row": "import os, subprocess\nfor parts in (['python3', 'leaf.py'],):\n    parts[1] = os.environ['SCRIPT']\n    subprocess.run(parts)\n",
        }
        for label, source in cases.items():
            with self.subTest(case=label):
                report = self.coverage_case([("bash", "python3 entry.py", "")], {"entry.py": source, "leaf.py": COPY})
                self.assertTrue(all(row["errors"] for row in report["modules"]), report)

    @staticmethod
    def guarded_git_source():
        return (
            "import os, re, subprocess\n"
            "IDENTITY = re.compile('[0-9a-f]{40}')\n"
            "CATALOG = 'object.txt'\n"
            "def require(condition, message):\n"
            "    if not condition:\n"
            "        raise ValueError(message)\n"
            "def checked(values):\n"
            "    result = values[0]\n"
            "    require(IDENTITY.fullmatch(result), 'invalid identity')\n"
            "    return result\n"
            "def launch(root, *parts):\n"
            "    return subprocess.run(['git', '-c', 'submodule.recurse=false', '-C', str(root), *parts])\n"
            "def output(root, *parts):\n"
            "    return launch(root, *parts)\n"
            "identity = checked(supplied)\n"
            "output('.', 'show', identity + ':' + CATALOG)\n"
            "output('.', 'fetch', '--no-recurse-submodules', '--no-tags', '--depth=1', '--no-write-fetch-head', '--refmap=', '--no-auto-maintenance', 'origin', identity)\n"
        )

    def test_opaque_git_forwarding_refuses_unproved_value_provenance(self):
        source = self.guarded_git_source()
        literal = ("import subprocess\ndef launch(root, *parts):\n"
                   "    return subprocess.run(['git', '-C', str(root), *parts])\n"
                   "for parts in (('rev-parse', 'HEAD'), ('remote', 'get-url', 'origin')):\n"
                   "    launch('.', *parts)\n")
        self.assert_coverage(self.coverage_case([("bash", "python3 entry.py\npython3 leaf.py", "")],
                                               {"entry.py": literal, "leaf.py": COPY}), "leaf.py", None)
        cases = {
            "guarded_opaque_value": source,
            "changing_subscript": source.replace("    result = values[0]\n", "").replace("result", "values[0]"),
            "string_subclass": source.replace("identity = checked(supplied)",
                "class Identity(str):\n    def __add__(self, other):\n        return '--ext-diff'\n"
                "identity = checked([Identity('a' * 40)])"),
            "computed_subcommand": literal.replace("'rev-parse'", "unknown()"),
            "fake_module": source.replace("IDENTITY =", "re = replacement\nIDENTITY =", 1),
            "class_module": source.replace("IDENTITY =", "class re:\n    pass\nIDENTITY =", 1),
            "imported_module": source.replace("IDENTITY =", "import collections as re\nIDENTITY =", 1),
            "local_module": source.replace("def checked(values):", "def checked(values, re):"),
            "replaced_compile": source.replace("IDENTITY =", "re.compile = replacement\nIDENTITY =", 1),
            "replaced_pattern": source.replace("def require", "IDENTITY = replacement\ndef require", 1),
            "local_pattern": source.replace("def checked(values):", "def checked(values, IDENTITY):"),
            "replaced_fullmatch": source.replace("def require", "IDENTITY.fullmatch = replacement\ndef require", 1),
            "escaped_pattern": source.replace("def require", "mutate(IDENTITY)\ndef require", 1),
            "fake_guard": source.replace("    if not condition:\n        raise ValueError(message)", "    return True"),
            "imported_guard": source.replace("identity = checked", "from collections import deque as require\nidentity = checked"),
            "class_guard": source.replace("identity = checked", "class require:\n    pass\nidentity = checked"),
            "local_guard": source.replace("def checked(values):", "def checked(values, require):"),
            "global_guard": source.replace("identity = checked", "globals()['require'] = replacement\nidentity = checked"),
            "guard_code": source.replace("identity = checked", "require.__code__ = replacement\nidentity = checked"),
            "guard_alias": source.replace("identity = checked", "alias = require\nidentity = checked"),
            "side_effect_after_validation": source.replace("'invalid identity')", "mutate(values))"),
            "dynamic_suffix": source.replace("identity + ':' + CATALOG", "identity + os.environ['FLAGS']"),
            "rebound_suffix": source.replace("identity = checked", "CATALOG = os.environ['FLAGS']\nidentity = checked"),
            "config_editor": source.replace("'show', identity + ':' + CATALOG", "'config', '--edit'"),
            "custom_fetch_helper": source.replace("'origin', identity", "'ext::python3 hidden.py', identity"),
            "fetch_option_suffix": source.replace("'origin', identity", "'origin', identity + os.environ['FLAGS']"),
        }
        for label, unsafe in cases.items():
            with self.subTest(case=label):
                report = self.coverage_case([("bash", "python3 entry.py\npython3 leaf.py", "")],
                                            {"entry.py": unsafe, "leaf.py": COPY})
                self.assertTrue(all(row["errors"] for row in report["modules"]), report)
        for filename in ("re.py", "subprocess.py"):
            with self.subTest(local_module=filename):
                report = self.coverage_case([("bash", "python3 entry.py\npython3 leaf.py", "")],
                                            {"entry.py": source, "leaf.py": COPY, filename: "pass\n"})
                self.assertTrue(all(row["errors"] for row in report["modules"]), report)

    def test_literal_git_operations_follow_literal_references(self):
        source = (
            "import subprocess\n"
            "PATHS = ('input.txt',)\n"
            "subprocess.run(['git', '-C', root, 'rev-parse', '--verify', revision])\n"
            "subprocess.run(['git', '-C', '/outside/read-only', 'status'])\n"
            "subprocess.run(['git', 'ls-tree', '-r', revision, '--', path], cwd=root)\n"
            "subprocess.run(['git', 'ls-files', '-z', '--', path], cwd=root)\n"
            "subprocess.run(['git', 'status', '--porcelain'], cwd=root)\n"
            "subprocess.run(['git', 'cat-file', 'blob', oid], cwd=root)\n"
            "subprocess.run(['git', 'diff', '--exit-code', '--end-of-options', revision, '--', path], cwd=root)\n"
            "subprocess.run(['git', 'show', '--end-of-options', revision, '--', path], cwd=root)\n"
            "subprocess.run(['git', 'archive', '--format=tar', '--', revision, *PATHS], cwd=root)\n"
            "subprocess.run(['git', 'remote', 'get-url', remote], cwd=root)\n"
            "subprocess.run(['git', 'clone', '--no-checkout', '--', './origin', destination], cwd=root)\n"
            "subprocess.run(['git', 'fetch', '--no-auto-maintenance', '--no-recurse-submodules', '--', './origin', revision], cwd=root)\n"
            "subprocess.run(['git', 'checkout', '--detach', 'HEAD', '--'], cwd=root)\n"
            "def inspect(root):\n"
            "    def git(*arguments):\n"
            "        return subprocess.check_output(['git', '-C', root, *arguments],"
            " **({'env': {'LANG': 'C'}} if enabled else {}))\n"
            "    git('rev-parse', revision)\n"
            "    git('ls-tree', revision, '--', path)\n"
            "inspect(root)\n"
            "subprocess.run(['git', 'show', 'HEAD', '--', 'leaf.py'], cwd='cwd-only')\n"
            "subprocess.run(['git', '-C', 'first', '-C', 'second', 'show', 'HEAD', '--', 'other.py'])\n"
        )
        report = self.coverage_case([("bash", "python3 entry.py", "")],
                                    {"entry.py": source, "cwd-only/leaf.py": COPY,
                                     "first/second/other.py": "print('unique')\n"})
        self.assert_coverage(report, "cwd-only/leaf.py", None)
        self.assertTrue(all("first/second/other.py" in {file["path"] for file in row["files"]}
                            for row in report["modules"]), report)

    def test_git_invocations_reject_unproved_modes_options_and_environment(self):
        cases = (
            ("['git', operation, 'HEAD']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', '-c', 'submodule.recurse=false', 'rev-parse', 'HEAD']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'config', '--get', 'remote.origin.url']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'hook', 'run', 'pre-commit']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'submodule', 'foreach', supplied]", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'custom-alias']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'diff', '--ext-diff', '--', path]", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'diff', computed_option, 'HEAD', '--', path]", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'show', '--textconv', 'HEAD:leaf.py']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'show', '--format', '--end-of-options', revision]", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'archive', '--format=custom', 'HEAD']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'archive', '--prefix', '--', revision]", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'clone', '--no-checkout', './origin', destination]", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'clone', '--no-checkout', '--', source, destination]", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'fetch', dynamic_flag, '--', './origin', 'HEAD']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'checkout', '--detach', 'HEAD']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'checkout', '--detach', revision, '--']", "", "unsupported Git mode or unresolved Git options"),
            ("['git', 'status']", ", shell=True", "unsupported shell execution of a Git operation"),
            ("['git', 'status']", ", preexec_fn=callback", "unsupported subprocess pre-execution callback"),
            ("['git', 'status']", ", **({'executable': target} if enabled else {})", "unresolved subprocess positional/options expansion"),
            ("['git', 'status']", ", **({'env': {'PATH': '.'}} if enabled else {})", "unsupported subprocess environment affecting resolution"),
            ("['git', 'status']", ", env={'GIT_CONFIG_COUNT': '1'}", "unsupported subprocess environment affecting resolution"),
        )
        for argv, options, diagnostic in cases:
            with self.subTest(argv=argv, options=options):
                source = f"import subprocess\nsubprocess.run({argv}{options})\n"
                report = self.coverage_case([("bash", "python3 entry.py", "")], {"entry.py": source})
                self.assertTrue(all(f"entry.py:2: local-script discovery: {diagnostic}" in row["errors"]
                                    for row in report["modules"]), report)

    def test_git_operation_requires_standard_process_and_git_executables(self):
        entry = "subprocess.run(['git', 'status'], cwd=root)\n"
        for changed, files, diagnostic in (
            ("subprocess.run = replacement\n", {}, "unproved subprocess API for Git discovery"),
            ("", {"subprocess.py": "pass\n"}, "unproved subprocess API for Git discovery"),
            ("", {"support/git": "#!/bin/bash\necho shadow\n"}, "unproved Git executable: tracked Git command"),
        ):
            with self.subTest(changed=changed, files=files):
                report = self.coverage_case([("bash", "python3 entry.py", "")],
                                            {"entry.py": "import subprocess\n" + changed + entry, **files})
                self.assertTrue(all(any(diagnostic in error for error in row["errors"])
                                    for row in report["modules"]), report)

    def test_git_copied_environment_guards_git_and_loader_settings(self):
        for setting in ("GIT_CONFIG_COUNT", "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"):
            with self.subTest(setting=setting):
                source = ("import os, subprocess\n"
                          "env = os.environ.copy()\n"
                          f"env.update({setting}='1')\n"
                          "subprocess.run(['git', 'status'], env=env)\n")
                report = self.coverage_case([("bash", "python3 entry.py", "")], {"entry.py": source})
                self.assertTrue(all("entry.py:4: local-script discovery: unresolved computed subprocess env" in row["errors"]
                                    for row in report["modules"]), report)

    def test_git_literal_directory_rejects_committed_non_directory_components(self):
        for directory in ("linked", "linked/nested"):
            with self.subTest(directory=directory):
                workspace = self.workspace()
                for module in workspace.paths:
                    workspace.action(module, "python3 entry.py")
                    workspace.write(module, "entry.py", "import subprocess\n"
                                    f"subprocess.run(['git', '-C', {directory!r}, 'status'])\n")
                    workspace.write(module, "support/nested/leaf.py", block("python"))
                    (workspace.paths[module] / "linked").symlink_to("support", target_is_directory=True)
                    workspace.commit(workspace.paths[module])
                report = workspace.scan(self.factory)
                self.assertTrue(all(any(error.startswith("entry.py:2: local-script discovery: unsafe Git -C working directory:")
                                        for error in row["errors"]) for row in report["modules"]), report)

    def test_forwarding_recursion_and_expansion_are_bounded(self):
        cases = {
            "recursive": "import subprocess\ndef launch(*args):\n    subprocess.run(args)\n    launch(*args)\nlaunch('python3','leaf.py')\n",
            "callers": "import subprocess\ndef launch(*args):\n    subprocess.run(args)\n" + "launch('python3','leaf.py')\n" * 129,
            "tokens": "import subprocess\ndef launch(*args):\n    subprocess.run(args)\nlaunch(" + ",".join(repr("python3") for _ in range(257)) + ")\n",
            "loop": "import subprocess\nfor args in " + repr(tuple(("python3", "leaf.py") for _ in range(129))) + ":\n    subprocess.run(args)\n",
            "depth": "import subprocess\ndef launch0(*args):\n    subprocess.run(args)\n" + "".join(
                f"def launch{index}(*args):\n    return launch{index - 1}(*args)\n" for index in range(1, 11)) + "launch10('python3', 'leaf.py')\n",
            "cartesian": "import subprocess\ndef launch(*args):\n    subprocess.run([" + ",".join("*args" for _ in range(8))
                + "])\nlaunch('python3', 'leaf.py')\nlaunch('python3', 'leaf.py')\n",
        }
        for label, source in cases.items():
            with self.subTest(case=label):
                report = self.coverage_case([("bash", "python3 entry.py", "")], {"entry.py": source, "leaf.py": COPY})
                self.assertTrue(all(row["errors"] for row in report["modules"]), report)
                self.assertTrue(all(not any("invalid Python source" in message for message in row["errors"])
                                    for row in report["modules"]), report)

    def test_builtin_process_additional_aliases_preserve_ordinary_reads(self):
        for path, source in (
            ("script.js", "import runtime from 'node:process'; runtime.exit(0);"),
            ("script.js", "import {default as runtime} from 'process'; import * as namespace from 'node:process'; const mode = runtime.env.CI; const args = namespace.default.argv.slice(2);"),
            ("script.js", "import {env as environment, argv as arguments_} from 'node:process'; const mode = environment.CI; const args = arguments_.slice(2);"),
            ("script.js", "const original = require('process'); const runtime = original; const mode = runtime.env.CI; const args = runtime.argv.slice(2);"),
            ("script.js", "const {env, argv} = require('node:process'); const mode = env.CI; const args = argv.slice(2);"),
            ("script.ts", "import runtime = require('node:process'); const mode = runtime.env.CI; const args = runtime.argv.slice(2);"),
            ("script.ts", "import runtime = require('process'); const mode = runtime.env.CI; const args = runtime.argv.slice(2);"),
            ("script.js", "const mode = require('process').env.CI; const args = require('node:process')['argv'].slice(2); require('process').exit(0);"),
            ("script.js", "const environment = require('process').env; const mode = environment[process.argv[2]]; delete environment.MODE;"),
        ):
            with self.subTest(path=path, source=source):
                report = self.coverage_case([("bash", "node " + path, "")], {
                    path: source + "\n" + block(FORMATS[Path(path).suffix], "process reads"),
                })
                self.assert_coverage(report, path, None)

    def test_builtin_process_import_reflection_and_escapes_fail_closed(self):
        for source, diagnostic in (
            ("import runtime from 'node:process'; runtime.getBuiltinModule('child_process');", "reflective JavaScript execution"),
            ("import {default as runtime} from 'process'; runtime.getBuiltinModule('child_process');", "reflective JavaScript execution"),
            ("import * as runtime from 'node:process'; runtime.default.getBuiltinModule('child_process');", "reflective JavaScript execution"),
            ("import * as runtime from 'process'; runtime.chdir(process.env.DIRECTORY);", "reflective JavaScript execution"),
            ("import {getBuiltinModule as load} from 'node:process'; load('child_process');", "reflective JavaScript execution"),
            ("const runtime = require('node:process'); runtime.dlopen(module, process.env.LIBRARY);", "reflective JavaScript execution"),
            ("import runtime from 'process'; runtime.binding('spawn_sync');", "reflective JavaScript execution"),
            ("import {binding as load} from 'node:process'; load('spawn_sync');", "reflective JavaScript execution"),
            ("const {_linkedBinding: load} = require('process'); load(process.env.MODULE);", "reflective JavaScript execution"),
            ("import runtime from 'node:process'; runtime.getBuiltinModule.call(runtime, 'child_process');", "reflective JavaScript execution"),
            ("import runtime from 'node:process'; runtime.execve('/usr/bin/node', ['node', 'payload.js']);", "reflective JavaScript execution"),
            ("const runtime = require('process'); runtime.loadEnvFile('settings.env');", "reflective JavaScript execution"),
            ("import * as runtime from 'node:process'; runtime.mainModule.require(process.env.MODULE);", "reflective JavaScript execution"),
            ("import {execve as replace} from 'process'; replace(process.env.COMMAND, []);", "reflective JavaScript execution"),
            ("const runtime = require('process'); const load = runtime.mainModule.require; load(process.env.MODULE);", "reflective JavaScript execution"),
            ("process.getBuiltinModule[process.env.METHOD](null, 'child_process');", "reflective JavaScript process/import API"),
            ("import {getBuiltinModule as load} from 'process'; load[process.env.METHOD](null, 'child_process');", "reflective JavaScript process/import API"),
            ("const {getBuiltinModule: load} = require('node:process'); const alias = load; alias[process.env.METHOD](null, 'child_process');", "reflective JavaScript process/import API"),
            ("import runtime = require('node:process'); runtime.getBuiltinModule('child_process');", "reflective JavaScript execution"),
            ("import runtime from 'process'; const load = runtime.getBuiltinModule; load('child_process');", "reflective JavaScript execution"),
            ("import runtime from 'node:process'; runtime[process.env.API]('child_process');", "reflective JavaScript process/import API"),
            ("process[process.env.API]('child_process');", "reflective JavaScript process/import API"),
            ("import runtime from 'node:process'; consume(runtime);", "API escape"),
            ("import runtime = require('node:process'); const stored = [runtime];", "API escape"),
            ("consume(process);", "API escape"),
            ("consume(globalThis.process);", "API escape"),
            ("import runtime from 'process'; consume(runtime['getBuiltinModule']);", "API escape"),
            ("require('process').getBuiltinModule('child_process');", "reflective JavaScript execution"),
            ("import('process').then(runtime => consume(runtime));", "dynamic JavaScript process-module import"),
            ("export {getBuiltinModule} from 'node:process';", "process API re-export"),
        ):
            with self.subTest(source=source):
                self.assert_coverage(self.coverage_case([("bash", "node script.ts", "")], {
                    "script.ts": source + "\n",
                }), None, diagnostic)

    def test_builtin_process_environment_reexport_fails_closed_across_files(self):
        report = self.coverage_case([("bash", "node script.js", "")], {
            "script.js": "import {environment} from './process-data.js'; delete environment.NODE_PATH;\n",
            "process-data.js": "export {env as environment, argv} from 'process';\n" + block("javascript", "process re-export"),
        })
        self.assert_coverage(report, "process-data.js", "process API re-export")

    def test_builtin_process_environment_deletion_fails_closed(self):
        for source in (
            "const environment = require('process').env; delete environment.NODE_PATH;",
            "import {env as environment} from 'node:process'; delete environment.PATH;",
            "import runtime from 'node:process'; delete runtime.env;",
            "const runtime = globalThis.process; delete runtime['env'];",
            "const environment = require('node:process')['env']; delete environment[process.env.KEY];",
            "const runtime = require('process'); const environment = runtime.env; const alias = environment; delete alias['NODE_OPTIONS'];",
            "const {env: environment} = require('process'); delete environment[process.argv[2]];",
        ):
            with self.subTest(source=source):
                self.assert_coverage(self.coverage_case([("bash", "node script.js", "")], {
                    "script.js": source + "\n",
                }), None, "environment change affecting resolution")

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
            ("timeout --signal=TERM --kill-after=30s 1.5m ./scripts/helper.sh", "bash", "scripts/helper.sh"),
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

    def test_actions_reader_authenticates_real_historical_and_independent_scans(self):
        alpha, beta, gamma = acceptance_tests.MODULES
        w = self.workspace((alpha, beta))
        nightly_source = git(w.cicd, "rev-parse", "HEAD")

        def scan_members():
            report = w.scan(self.factory)
            members = {name: (w.output / name).read_bytes() for name in ("report.json", "summary.md")}
            self.assertEqual(json.loads(members["report.json"]), report)
            return report, members

        def nightly_world(heads):
            world = acceptance_tests.World(tuple(heads))
            world.run["head_sha"] = nightly_source
            world.nightly_overrides["identity"] = {
                "runId": world.run["id"], "attempt": world.run["run_attempt"], "source": nightly_source}
            for module, head in heads.items():
                world.rows[module].update(dispatchHead=head, deliveredSha=nightly_source)
                world.rows[module]["outcome"]["sha"] = head
            return world

        historical_report, historical_members = scan_members()
        historical_heads = {module: git(path, "rev-parse", "HEAD") for module, path in w.paths.items()}
        historical = nightly_world(historical_heads)
        historical.scan = historical_members["report.json"]
        historical.scan_summary = historical_members["summary.md"]
        code, report = self.judge(historical, alpha, beta)
        self.assertEqual(historical_report["result"], "pass")
        self.assertEqual(code, 0)
        self.assertEqual({item["scan"]["source"] for item in report["modules"].values()}, {"scan job"})

        w.module(gamma)
        scan_source = w.commit(w.cicd)
        self.assertNotEqual(scan_source, nightly_source)
        copied = ".github/actions/dormant/shared.py"
        for module in (alpha, beta):
            w.write(module, copied, block("python"))
        unsupported = w.action(gamma, 'bash "$SCRIPT"')
        heads = {module: w.commit(path) for module, path in w.paths.items()}
        failed_report, failed_members = scan_members()
        self.assertEqual(failed_report["result"], "fail")
        self.assertTrue(failed_report["findings"])
        self.assertIn(copied.encode(), failed_members["summary.md"])
        self.assertIn(b"action.yml:", failed_members["summary.md"])

        (w.paths[beta] / copied).unlink()
        unsupported.unlink()
        w.commit(w.paths[beta])
        w.commit(w.paths[gamma])
        clean_report, clean_members = scan_members()
        self.assertEqual(clean_report["result"], "pass")
        self.assertIn((alpha, heads[alpha]), {(row["module"], row["revision"]) for row in clean_report["modules"]})

        independent = nightly_world(heads)
        independent.run["conclusion"] = "success"
        independent.nightly_result = "pass"
        del independent.jobs["scan"]
        independent.omit.add("scan")

        def producer(run_id, hour, event, attempt, source, report, members):
            run = {"id": run_id, "path": ".github/workflows/scan.yml", "head_branch": "main",
                   "head_sha": source, "status": "completed", "run_attempt": attempt,
                   "conclusion": "success" if report["result"] == "pass" else "failure",
                   "event": event, "created_at": f"2026-11-18T{hour}:00:00Z",
                   "repository": {"full_name": "Hexalith/Hexalith.CiCd"}}
            return run, {"scan": members}

        stale = producer(60001, "09", "workflow_dispatch", 1, nightly_source, historical_report, historical_members)
        failed = producer(60002, "10", "schedule", 2, scan_source, failed_report, failed_members)
        clean = producer(60003, "11", "workflow_dispatch", 1, scan_source, clean_report, clean_members)
        independent.scan_producers = [stale]
        code, report = self.judge(independent, alpha, gamma)
        self.assertEqual(code, 1)
        for module in (alpha, gamma):
            self.assertIn("covers the dispatched head", self.reasons(report, module))
            self.assertIsNone(report["modules"][module]["scan"])

        independent.scan_producers = [stale, failed, clean]
        code, report = self.judge(independent, alpha, beta, gamma)
        self.assertEqual(code, 1)
        self.assertEqual(self.verdicts(report), dict.fromkeys(heads, "fail"))
        for module in (alpha, beta):
            self.assertIn("cross-module duplicate findings", self.reasons(report, module))
        self.assertIn("own scan row failed: .github/actions/dormant/action.yml:", self.reasons(report, gamma))
        self.assertEqual({item["scan"]["runId"] for item in report["modules"].values()}, {60002})
        self.assertFalse(any("runs/60003/artifacts" in call for call in self.github_calls))
        self.assertIn({"name": "hexalith-nightly-scan-2", "id": 15000000002,
                       "digest": "sha256:" + hashlib.sha256(acceptance_tests.zip_bytes(failed_members)).hexdigest()},
                      report["artifacts"])

        wrong_controller = producer(60004, "09", "workflow_dispatch", 1, nightly_source, failed_report, failed_members)
        independent.scan_producers = [wrong_controller, clean]
        code, report = self.judge(independent, alpha, gamma)
        self.assertEqual(code, 1)
        self.assertEqual(self.verdicts(report), {alpha: "pass", gamma: "fail"})
        self.assertIn("skipped scan.yml run 60004: scan report controller revision", self.reasons(report, gamma))
        self.assertEqual(report["modules"][alpha]["scan"], {"source": "scan.yml", "runId": 60003})

        independent.scan_producers = [failed]
        github = independent.github()
        github.routes[acceptance_tests.API + "actions/runs/60002/artifacts?per_page=100"]["artifacts"][0][
            "workflow_run"]["head_sha"] = nightly_source
        code, _ = self.judge(github, alpha)
        self.assertEqual(code, 2)
        self.assertIn(f"artifact hexalith-nightly-scan-2 is not bound to run 60002 at {scan_source}", self.stderr)

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

    def test_test_boundary_observations_pass_the_row_summary_and_acceptance(self):
        alpha = acceptance_tests.MODULES[0]
        w = self.workspace((alpha,))
        w.action(alpha, "python -m unittest discover -s tests -p 'test_*.py'")
        w.write(alpha, "tests/test_launch.py", "import subprocess\nsubprocess.run(command)\n")
        head = w.commit(w.paths[alpha])
        report = w.scan(self.factory)
        row = report["modules"][0]
        self.assertEqual((report["result"], row["result"], row["errors"]), ("pass", "pass", []), report)
        self.assertIn("tests/test_launch.py", {item["path"] for item in row["files"]})
        self.assertEqual([(item["path"], item["line"]) for item in row["observations"]], [("tests/test_launch.py", 2)])
        self.assertIn("local-script discovery: unresolved computed Python script invocation",
                      row["observations"][0]["reason"])
        summary = (w.output / "summary.md").read_text()
        self.assertIn("; 1 test boundary observation\n", summary)
        self.assertIn("  - boundary: tests/test_launch.py:2: local-script discovery: ", summary)
        source = git(w.cicd, "rev-parse", "HEAD")
        world = acceptance_tests.World((alpha,))
        world.run["head_sha"] = source
        world.nightly_overrides["identity"] = {"runId": world.run["id"], "attempt": world.run["run_attempt"],
                                               "source": source}
        world.rows[alpha].update(dispatchHead=head, deliveredSha=source)
        world.rows[alpha]["outcome"]["sha"] = head
        world.scan = (w.output / "report.json").read_bytes()
        world.scan_summary = summary.encode()
        code, verdicts = self.judge(world, alpha)
        self.assertEqual(code, 0, verdicts)
        self.assertEqual(self.verdicts(verdicts), {alpha: "pass"})

    def pinned_workspace(self, command, *, declaration=True, origin=None, duplicate=False, configured=True,
                         gitlink=True, symlink=False, check_source="import helper\n",
                         module="Hexalith.Alpha", repository="Hexalith.Dependency", dependency_files=None):
        path = "references/" + repository
        workspace = self.workspace((module,))
        dependency = workspace.root / repository
        dependency.mkdir()
        git(dependency, "init", "--quiet", "--initial-branch=main")
        (dependency / "eng").mkdir()
        (dependency / "eng/launcher.sh").write_text(
            '#!/usr/bin/env bash\nset -euo pipefail\nROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"\n'
            'exec python3 "$ROOT/eng/check.py" "$@"\n')
        check = dependency / "eng/check.py"
        (dependency / "eng/helper.py").write_text("print('pinned helper')\n")
        for name, text in (dependency_files or {}).items():
            (dependency / name).write_text(text)
        if symlink:
            check.symlink_to("helper.py")
        else:
            check.write_text(check_source)
        pin = workspace.commit(dependency)
        (dependency / "eng/helper.py").write_text("print('mutable branch replacement')\n")
        workspace.commit(dependency)
        workspace.transport.pins[repository] = dependency
        if configured:
            (workspace.cicd / ("setup/" + module + ".yml")).write_text(
                "solution: none\nsubmodules:\n  - " + path + "\n")
            workspace.commit(workspace.cicd)
        if declaration:
            url = origin or rt.Transport().remote(repository)
            section = f'\tpath = {path}\n\turl = {url}\n'
            workspace.write(module, ".gitmodules", f'[submodule "{repository}"]\n' + section
                            + ('[submodule "duplicate"]\n' + section if duplicate else ""))
        workspace.action(module, command)
        workspace.commit(workspace.paths[module])
        if gitlink:
            git(workspace.paths[module], "update-index", "--add", "--cacheinfo", "160000", pin, path)
            git(workspace.paths[module], "commit", "--quiet", "-m", "record dependency")
        return workspace, pin

    def test_pinned_source_launcher_and_import_follow_recorded_commit(self):
        path = "references/Hexalith.Dependency"
        workspace, pin = self.pinned_workspace("bash " + path + "/eng/launcher.sh")
        report = workspace.scan(self.factory)
        self.assertEqual("pass", report["result"], report)
        row = report["modules"][0]
        self.assertEqual(row["pinnedSources"], {path: {"repository": "Hexalith.Dependency", "revision": pin}})
        self.assertEqual({item["path"] for item in row["files"]}, {
            ".github/actions/dormant/action.yml", path + "/eng/launcher.sh", path + "/eng/check.py",
            path + "/eng/helper.py",
        })
        helper = next(item for item in row["files"] if item["path"].endswith("/helper.py"))
        self.assertEqual(hashlib.sha256(b"print('pinned helper')\n").hexdigest(), helper["sha256"])

    def test_pinned_source_unknown_and_substituted_execution_targets_fail(self):
        path = "references/Hexalith.Dependency"
        launcher = path + "/eng/launcher.sh"
        for command, options, diagnostic in (
            (f'bash "$UNKNOWN"/eng/launcher.sh', {}, "unresolved local-script target"),
            (f'bash {path}/eng/missing.sh', {}, "missing or unsafe regular script"),
            (f'bash {path}/../{launcher}', {}, "unsafe source path within pinned source"),
            (f'bash {launcher}', {"declaration": False}, "missing regular committed .gitmodules"),
            (f'bash {launcher}', {"duplicate": True}, "ambiguous committed submodule declaration"),
            (f'bash {launcher}', {"origin": "https://example.com/Substitute"}, "origin or path mismatch"),
            (f'bash {launcher}', {"configured": False}, "not authorized by committed setup"),
            (f'bash {launcher}', {"gitlink": False}, "missing or unsafe regular script"),
            (f'bash {launcher}', {"symlink": True}, "missing or unsafe regular script"),
        ):
            with self.subTest(command=command, options=options):
                workspace, _ = self.pinned_workspace(command, **options)
                report = workspace.scan(self.factory)
                self.assertEqual("fail", report["result"], report)
                self.assertTrue(any(diagnostic in error for error in report["modules"][0]["errors"]), report)

    def test_pinned_python_source_relative_parent_cannot_escape_dependency(self):
        launcher = "references/Hexalith.Dependency/eng/launcher.sh"
        workspace, _ = self.pinned_workspace("bash " + launcher, check_source=(
            "from pathlib import Path\nimport subprocess\n"
            "subprocess.run(['python3', Path(__file__).resolve().parents[3] / 'outside' / 'check.py'])\n"
        ))
        workspace.write("Hexalith.Alpha", "outside/check.py", "print('outside the dependency')\n")
        module = workspace.paths["Hexalith.Alpha"]
        git(module, "add", "outside/check.py")
        git(module, "commit", "--quiet", "-m", "record adjacent source")
        report = workspace.scan(self.factory)
        row = report["modules"][0]
        self.assertEqual("fail", row["result"], report)
        self.assertTrue(any("unresolved computed Python script invocation" in error for error in row["errors"]), report)
        self.assertNotIn("outside/check.py", {item["path"] for item in row["files"]})

    def test_computed_dotnet_directory_rechecks_sdk_selection_in_later_pinned_sources(self):
        launcher = "references/Hexalith.Dependency/eng/launcher.sh"
        workspace, _ = self.pinned_workspace("python3 entry.py", dependency_files={
            "global.json": '{"sdk": {"version": "11.0.100", "paths": ["eng"]}}\n'})
        # The .NET call is examined before the later process call acquires the pinned source.
        workspace.write("Hexalith.Alpha", "entry.py", "import subprocess\n"
                        "subprocess.run(['dotnet', 'build', project], cwd=directory)\n"
                        f"subprocess.run(['bash', {launcher!r}])\n")
        module = workspace.paths["Hexalith.Alpha"]
        git(module, "add", "entry.py")
        git(module, "commit", "--quiet", "-m", "record computed .NET directory")
        report = workspace.scan(self.factory)
        row = report["modules"][0]
        self.assertEqual("fail", row["result"], report)
        self.assertIn("entry.py:2: local-script discovery: unproved .NET SDK selection: global.json declares SDK search "
                      "paths: references/Hexalith.Dependency/global.json", row["errors"], report)

    def test_managed_assembly_launch_rechecks_command_lookup_in_later_pinned_sources(self):
        launcher = "references/Hexalith.Dependency/eng/launcher.sh"
        entry = ("import subprocess\nsubprocess.run(['dotnet', f'{name}.dll', '-xml', output])\n"
                 f"subprocess.run(['bash', {launcher!r}])\n")
        for files, expected in (({}, []), ({"eng/dotnet-fixture.dll": "#!/bin/sh\n"}, [
                "entry.py:2: local-script discovery: unproved .NET command lookup: tracked dotnet-prefixed command: "
                "references/Hexalith.Dependency/eng/dotnet-fixture.dll"])):
            with self.subTest(files=files):
                # The launch is examined before the later process call acquires the pinned source.
                workspace, _ = self.pinned_workspace("python3 entry.py", dependency_files=files)
                workspace.write("Hexalith.Alpha", "entry.py", entry)
                module = workspace.paths["Hexalith.Alpha"]
                git(module, "add", "entry.py")
                git(module, "commit", "--quiet", "-m", "record managed-assembly launch")
                report = workspace.scan(self.factory)
                self.assertEqual(report["modules"][0]["errors"], expected, report)

    def test_works_platform_boundary_follows_only_the_reviewed_inputs(self):
        import scan_discovery as discovery

        module = "Hexalith.Works"
        repository = "Hexalith.Platform"
        path = discovery.WORKS_PLATFORM_ROOT
        action = discovery.WORKS_PLATFORM_ACTION
        workflow = discovery.WORKS_PLATFORM_WORKFLOW
        coordinator = "scripts/coordinator.py"
        export = "eng/export.py"
        export_source = "import shutil\n\n\ndef create(origin, root):\n    shutil.copytree(origin, root)\n"
        workspace, pin = self.pinned_workspace("echo dormant", module=module, repository=repository,
                                               dependency_files={export: export_source})
        remote = workspace.paths[module]
        dependency = workspace.transport.pins[repository]
        script = workspace.write(module, coordinator,
                                 "import subprocess\n"
                                 "subprocess.run(['bash', sealed_export / 'eng/launcher.sh'])\n")
        action_source = workspace.write(module, action, steps(("bash", "python3 " + coordinator, "")))
        reviewed = ("jobs:\n  ci:\n    uses: \"Hexalith/Hexalith.Builds/.github/workflows/ci.yml@v6.8.1\"\n"
                    "  parity:\n    steps:\n    - uses: Hexalith/Hexalith.Builds/Github/prepare@v6.8.1\n"
                    "    - uses: Hexalith/Hexalith.Builds.Extra/prepare@v1.0.0\n"
                    "    - uses: OtherHexalith/Hexalith.Builds/Github/prepare@v1.0.0\n"
                    "    - uses: ./.github/actions/platform-parity\n    timeout-minutes: 180\n")
        workspace.write(module, workflow, reviewed)
        git(remote, "add", "--", action, coordinator, workflow)
        git(remote, "commit", "--quiet", "-m", "record parity entry point")
        base = git(remote, "rev-parse", "HEAD")
        # Like the production constant, the digest fingerprints the reviewed bytes.
        inputs = {workflow: discovery.works_fingerprint(workflow, reviewed.encode()),
                  action: hashlib.sha256(action_source.read_bytes()).hexdigest(),
                  coordinator: hashlib.sha256(script.read_bytes()).hexdigest()}
        exports = {export: hashlib.sha256(export_source.encode()).hexdigest()}
        entrypoint = (coordinator, 2, "subprocess.run")
        entries = {entrypoint: ("eng/launcher.sh", "bash")}

        def record(message, *changes, gitlink=None):
            git(remote, "reset", "--quiet", "--hard", base)
            for target, text in changes:
                workspace.write(module, target, text)
                git(remote, "add", "--", target)
            if gitlink is not None:
                git(remote, "update-index", "--cacheinfo", "160000", gitlink, path)
            git(remote, "commit", "--quiet", "--allow-empty", "-m", message)

        def platform(message, files, links=None):
            # A new Platform commit beyond the original pin; None deletes a file.
            git(dependency, "reset", "--quiet", "--hard", pin)
            for name, text in files.items():
                target = dependency / name
                if text is None:
                    target.unlink()
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text)
            for name, target in (links or {}).items():
                (dependency / name).symlink_to(target)
            git(dependency, "add", "--force", "--all")
            git(dependency, "commit", "--quiet", "-m", message)
            return git(dependency, "rev-parse", "HEAD")

        def unproved(row, diagnostic, *, revision=None):
            self.assertEqual("fail", row["result"], row)
            if revision is None:
                self.assertNotIn("pinnedSources", row)
            else:
                self.assertEqual(row["pinnedSources"], {path: {"repository": repository, "revision": revision}})
            self.assertIn(f"{action}:1: local-script discovery: {diagnostic}", row["errors"])

        with mock.patch.multiple(discovery, WORKS_PLATFORM_INPUTS=inputs, WORKS_PLATFORM_EXPORT=exports,
                                 WORKS_PLATFORM_ENTRIES=entries):
            report = workspace.scan(self.factory)
            row = report["modules"][0]
            self.assertEqual("pass", row["result"], report)
            self.assertEqual(row["pinnedSources"], {path: {"repository": repository, "revision": pin}})
            helper = next(item for item in row["files"] if item["path"] == path + "/eng/helper.py")
            self.assertEqual(hashlib.sha256(b"print('pinned helper')\n").hexdigest(), helper["sha256"])

            # Any Platform commit holding the reviewed export bytes is proved, and
            # the workflow may differ from its reviewed bytes only in immutable
            # Builds release tags. Traversal still follows the recorded commit.
            updated = platform("unrelated Platform update", {"eng/helper.py": "print('updated helper')\n"})
            record("advance Platform and Builds", (workflow, reviewed.replace("@v6.8.1", "@v6.8.3", 1)
                                                   .replace("@v6.8.1", "@v6.10.0")), gitlink=updated)
            row = workspace.scan(self.factory)["modules"][0]
            self.assertEqual("pass", row["result"], row)
            self.assertEqual(row["pinnedSources"], {path: {"repository": repository, "revision": updated}})
            helper = next(item for item in row["files"] if item["path"] == path + "/eng/helper.py")
            self.assertEqual(hashlib.sha256(b"print('updated helper')\n").hexdigest(), helper["sha256"])

            for label, text in (
                ("workflow outside the tags", reviewed.replace("timeout-minutes: 180", "timeout-minutes: 170")),
                ("mutable Builds branch", reviewed.replace("ci.yml@v6.8.1", "ci.yml@main")),
                ("Builds prerelease", reviewed.replace("prepare@v6.8.1", "prepare@v6.8.2-rc.1")),
                ("Builds tag-like branch", reviewed.replace("prepare@v6.8.1", "prepare@v6.8.1/next")),
                ("literal tag mask", reviewed.replace("prepare@v6.8.1", "prepare@vX.Y.Z")),
                ("lookalike repository tag", reviewed.replace("Extra/prepare@v1.0.0", "Extra/prepare@v1.0.1")),
                ("lookalike owner tag", reviewed.replace("OtherHexalith/Hexalith.Builds/Github/prepare@v1.0.0",
                                                         "OtherHexalith/Hexalith.Builds/Github/prepare@v1.0.1")),
            ):
                with self.subTest(case=label):
                    record("substitute workflow", (workflow, text))
                    unproved(workspace.scan(self.factory)["modules"][0],
                             "unproved computed Platform source: " + workflow)

            with self.subTest(case="action"):
                record("substitute action", (action, action_source.read_text() + "# changed\n"))
                unproved(workspace.scan(self.factory)["modules"][0], "unproved computed Platform source: " + action)

            with self.subTest(case="materializer"):
                record("substitute computed source", (coordinator, script.read_text().replace(
                    "eng/launcher.sh", "eng/unproved.sh")))
                row = workspace.scan(self.factory)["modules"][0]
                unproved(row, "unproved computed Platform source: " + coordinator)
                self.assertIn(f"{coordinator}:2: local-script discovery: unresolved computed Python script invocation",
                              row["errors"])

            with self.subTest(case="import shadow"):
                shadow = "scripts/subprocess.py"
                record("substitute interpreter namespace", (shadow, "# Shadow the checked interpreter namespace\n"))
                unproved(workspace.scan(self.factory)["modules"][0],
                         "unproved computed Platform import shadow: " + shadow)

            cache = "eng/__pycache__"
            bytecode = "export.cpython-312.pyc"
            for label, files, links, source in (
                    ("changed export", {export: export_source + "# changed\n"}, None, export),
                    ("missing export", {export: None}, None, export),
                    ("cached export bytecode", {cache + "/" + bytecode: "substituted\n"}, None, cache + "/" + bytecode),
                    ("linked bytecode cache", {"eng/bytecode/" + bytecode: "substituted\n"}, {cache: "bytecode"},
                     cache)):
                with self.subTest(case=label):
                    substituted = platform(label, files, links)
                    record("record " + label, gitlink=substituted)
                    unproved(workspace.scan(self.factory)["modules"][0],
                             "unproved computed Platform source: " + path + "/" + source, revision=substituted)

            blob = git(remote, "hash-object", "-w", "--stdin", data=b"not a commit\n")
            for label, arguments in (("missing gitlink", ("--force-remove", path)),
                                     ("blob gitlink", ("--cacheinfo", "100644", blob, path)),
                                     ("symlink gitlink", ("--cacheinfo", "120000", blob, path))):
                with self.subTest(case=label):
                    git(remote, "reset", "--quiet", "--hard", base)
                    git(remote, "update-index", *arguments)
                    git(remote, "commit", "--quiet", "-m", "substitute " + label)
                    unproved(workspace.scan(self.factory)["modules"][0],
                             "unproved Platform gitlink for computed checkout/export: " + path)

            git(remote, "reset", "--quiet", "--hard", base)
            with mock.patch.object(discovery, "WORKS_PLATFORM_ENTRIES",
                                   {entrypoint: ("eng/../eng/launcher.sh", "bash")}):
                row = workspace.scan(self.factory)["modules"][0]
            self.assertEqual("fail", row["result"], row)
            self.assertTrue(any("unsafe source path within pinned source" in error for error in row["errors"]), row)

            unresolved = platform("record unresolved descendant", {"eng/check.py": (
                "import subprocess\nimport os\nsubprocess.run([os.getenv('UNPROVED_PROGRAM')])\n")})
            record("record unresolved descendant", gitlink=unresolved)
            row = workspace.scan(self.factory)["modules"][0]
            self.assertEqual("fail", row["result"], row)
            self.assertEqual(row["pinnedSources"], {path: {"repository": repository, "revision": unresolved}})
            self.assertIn(f"{path}/eng/check.py:3: local-script discovery: unresolved computed Python script invocation",
                          row["errors"])
            self.assertFalse(any("unproved" in error for error in row["errors"]), row)

    def test_works_platform_production_export_is_a_loaded_entry_target(self):
        import scan_discovery as discovery

        targets = {target for target, _ in discovery.WORKS_PLATFORM_ENTRIES.values()}
        self.assertTrue(discovery.WORKS_PLATFORM_EXPORT)
        self.assertLessEqual(set(discovery.WORKS_PLATFORM_EXPORT), targets)

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
        # The scan artifact carries exactly these files; nightly_acceptance.py rejects any other set.
        self.assertEqual(sorted(path.name for path in w.output.iterdir()), ["report.json", "summary.md"])
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
            ("python -m unittest discover -s tests -p \"$PATTERN\"", {"tests/test_helper.py": "import helper\n"},
             "unresolved unittest discovery filename pattern"),
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

    def test_unittest_discovery_detects_duplicates_in_imported_helpers(self):
        report = self.coverage_case(
            [("bash", "python -m unittest discover -s tests", "")],
            {"tests/test_helper.py": "import helper\n", "helper.py": COPY},
        )
        self.assert_coverage(report, "helper.py", None)

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
                ("subprocess.run(['dotnet', 'tool', 'run', 'fixture'], cwd=directory)", "subprocess cwd"),
                ("subprocess.run(['dotnet', 'build', project], cwd=directory, preexec_fn=callback)", "pre-execution callback"),
                ("subprocess.run(['dotnet', 'build', project], env={'PATH':'scripts'})", "environment affecting resolution")):
            with self.subTest(command=command):
                self.assert_coverage(self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": "import subprocess\n" + command + "\n",
                }), None, diagnostic)

    def test_fixed_msbuild_property_tuple_preserves_discovery_boundary(self):
        prefix = "import subprocess\ndef invoke(source, project):\n"
        prepare = "    properties = (f'-p:RestoreSources={source}', '-p:RestoreFallbackFolders=')\n"
        command = "    subprocess.run(['dotnet', 'restore', project, 'scripts/leaf.py', *properties])\n"
        report = self.coverage_case([("bash", "python scripts/start.py", "")], {
            "scripts/start.py": prefix + prepare + command, "scripts/leaf.py": COPY,
        })
        self.assert_coverage(report, "scripts/leaf.py", None)

        diagnostics = (
            (prefix + "    properties = source\n" + command, "unsafe or unresolved forwarding"),
            (prefix + prepare.replace("RestoreSources", "{source}") + command, "unsafe or unresolved forwarding"),
            (prefix + prepare + "    properties = source\n" + command, "unsafe or unresolved forwarding"),
            (prefix + prepare + command.replace("'restore'", "operation"), "unsafe or unresolved forwarding"),
            (prefix + prepare + command.replace("*properties]", "*properties, 'x']"), "unsafe or unresolved forwarding"),
            (prefix + prepare + command.replace("*properties])", "*properties], shell=True)"), "shell execution"),
            (prefix + prepare + command.replace("*properties])", "*properties], preexec_fn=callback)"), "pre-execution callback"),
        )
        for source, diagnostic in diagnostics:
            with self.subTest(source=source):
                report = self.coverage_case([("bash", "python scripts/start.py", "")], {
                    "scripts/start.py": source, "scripts/leaf.py": COPY,
                })
                self.assert_coverage(report, None, diagnostic)

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
