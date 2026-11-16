"""Run the real package fixture after building its full integration dependency graph.

This is a focused diagnostic, not a complete publication qualification.
"""
from pathlib import Path
import ast
import hashlib
import sys

root = Path(__file__).resolve().parents[3]
driver = root / "_bmad-output/specs/spec-cicd/evidence/18/local-package-build.py"
source = driver.read_text()
parsed = ast.parse(source)
targets = [node for node in parsed.body if isinstance(node, ast.Assign)
           and any(isinstance(target, ast.Name) and target.id == "target" for target in node.targets)]
assert len(targets) == 1
target = targets[0]
lines = source.splitlines(keepends=True)
lines[target.lineno - 1:target.end_lineno] = ["target = 'tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj'\n"]
source = "".join(lines)
print("DIAGNOSTIC ONLY: existing driver with integration build target; actual full native/browser scenario loop unchanged", flush=True)
print("SOURCE DRIVER SHA256", hashlib.sha256(driver.read_bytes()).hexdigest(), flush=True)
sys.argv = [str(driver), "--nightly"]
exec(compile(source, str(driver), "exec"), {"__file__": str(driver), "__name__": "__main__"})
