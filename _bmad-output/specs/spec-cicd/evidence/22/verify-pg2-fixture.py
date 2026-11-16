"""Exercise changed disposable-source fixture setup without an approved profile.

Run with run-with-temp. This grants no telemetry authorization or gate credit.
"""

import importlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path("/home/administrator/projects/hexalith/memories-story-22")
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tests/tooling/access_telemetry_c1"))
module = importlib.import_module("pg2_runtime_control_plane_identity_test")
case = module.Pg2RuntimeControlPlaneIdentityTests()
try:
    case.setUp()
    fixture = case.temporary_repository()
    status = subprocess.check_output(["git", "status", "--short"], cwd=fixture, text=True)
    assert not status, status
    message = subprocess.check_output(["git", "log", "-1", "--format=%s"], cwd=fixture, text=True).strip()
    assert message == "test: establish disposable source fixture"
    for relative in module.SOURCE_PATHS:
        assert (fixture / relative).is_file(), relative
    assert not (fixture / "node_modules").exists()
    record = {"candidate": subprocess.check_output(["git", "rev-parse", "HEAD"],
        cwd=ROOT, text=True).strip(), "fixtureSetupPassed": True,
        "rootCommitlintDependencyRemoved": True, "fixtureGitStatus": status,
        "productGateOrAuthorizationCredit": False,
        "completeProfileDependentSuiteExecuted": False}
    (Path(__file__).resolve().parent / "pg2-fixture-verification.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record))
finally:
    case.doCleanups()
