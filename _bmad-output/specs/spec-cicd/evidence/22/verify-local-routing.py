"""Behaviorally verify local Memories project routing without running .NET tests.

Run with run-with-temp after other verification finishes. This exercises the
real Bash and PowerShell entrypoints with a controlled dotnet executable.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


SOURCE = Path("/home/administrator/projects/hexalith/memories-story-22")
ROOT = Path(os.environ["TMPDIR"]) / "routing"
TOOLS = ROOT / "tools"
TOOLS.mkdir(parents=True)
BIN = ROOT / "bin"
BIN.mkdir()
for path in (SOURCE / "tools").glob("test*"):
    if path.is_file():
        shutil.copyfile(path, TOOLS / path.name)

DOTNET = BIN / "dotnet"
DOTNET.write_text(f"#!{sys.executable}\n" + """import json, os, sys
if sys.argv[1:2] != ['test']:
    os.execv(os.environ['ROUTING_REAL_DOTNET'], [os.environ['ROUTING_REAL_DOTNET'], *sys.argv[1:]])
with open(os.environ['ROUTING_COMMANDS'], 'a') as stream:
    stream.write(json.dumps(sys.argv[1:]) + '\\n')
sys.exit(int(os.environ.get('ROUTING_EXIT', '0')))
""")
DOTNET.chmod(0o755)


def inventory(name):
    return [line.strip() for line in (TOOLS / ("test-projects." + name + ".txt")).read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


unit = inventory("unit-contract")
fast = inventory("integration-fast")
nightly = inventory("integration-slow")
benchmark = inventory("benchmark")
assert len(unit) == 9 and len(fast) == len(nightly) == len(benchmark) == 1
assert any("DerivedStores" in project for project in unit)
CASES = [("Category!=Integration", unit), ("Category=Integration", fast + nightly),
         ("Category=IntegrationSlow", nightly), ("Category=Performance", nightly),
         ("Category=Integration&Category!=IntegrationSlow&Category!=Performance", fast),
         ("Category=Benchmark", benchmark), ("", unit + fast + nightly + benchmark)]
records = []
for shell in ("bash", "pwsh"):
    for selection, expected in CASES:
        output = ROOT / "commands.jsonl"
        output.write_text("")
        env = dict(os.environ, PATH=str(BIN) + os.pathsep + os.environ["PATH"],
                   ROUTING_COMMANDS=str(output), ROUTING_REAL_DOTNET=shutil.which("dotnet"))
        command = (["bash", str(TOOLS / "test.sh"), "--configuration", "Release", "--no-build"]
                   if shell == "bash" else ["pwsh", "-NoLogo", "-NoProfile", "-File",
                       str(TOOLS / "test.ps1"), "-Configuration", "Release", "-NoBuild"])
        if selection:
            command.extend(["--filter" if shell == "bash" else "-Filter", selection])
        result = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        arguments = [json.loads(line) for line in output.read_text().splitlines()]
        projects = [args[args.index("--project") + 1] for args in arguments]
        assert projects == expected, (shell, selection, projects, expected)
        assert all(args[0] == "test" and "--no-build" in args for args in arguments)
        records.append({"shell": shell, "selector": selection,
                        "selectedProjects": projects, "passed": True})
    failed = subprocess.run(command, env=dict(env, ROUTING_EXIT="27"),
                            capture_output=True, text=True, check=False)
    assert failed.returncode != 0, (shell, "lost child failure")

coverage = json.loads((SOURCE / "tests/tooling/coverage_gate/line-coverage-gate.json").read_text())
assert coverage["minimumLineCoveragePercent"] == 76.5
assert coverage["requiredReportProjects"] == [Path(project).stem for project in unit]
document = {"candidate": subprocess.check_output(["git", "rev-parse", "HEAD"],
    cwd=SOURCE, text=True).strip(), "controlledDotnetOnly": True,
    "executedProductTests": False, "cases": records,
    "childFailuresPropagated": True, "coverageThreshold": 76.5,
    "requiredReportProjects": coverage["requiredReportProjects"]}
(Path(__file__).resolve().parent / "local-routing.json").write_text(json.dumps(document, indent=2) + "\n")
print(f"PASS: {len(records)} Bash/PowerShell project routing cases; child failures propagated; nine reports at 76.5%.")
