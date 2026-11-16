"""Run affected fixture tests with the existing standalone package/Release driver."""
from pathlib import Path
import hashlib
import sys

root = Path(__file__).resolve().parents[3]
driver = root / "_bmad-output/specs/spec-cicd/evidence/18/local-package-build.py"
source = driver.read_text()
needle = "'-class', 'Hexalith.Projects.Integration.Tests.PackageFixtureSafetyTests',"
assert source.count(needle) == 1
source = source.replace(needle, needle + "\n               '-class', 'Hexalith.Projects.Integration.Tests.PackageOwnerLoadContextTests',")
print("SOURCE DRIVER SHA256", hashlib.sha256(driver.read_bytes()).hexdigest(), flush=True)
sys.argv = [str(driver), "--credential-preflight"]
exec(compile(source, str(driver), "exec"), {"__file__": str(driver), "__name__": "__main__"})
