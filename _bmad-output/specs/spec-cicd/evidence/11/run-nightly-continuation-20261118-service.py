"""Systemd backup: observe the genuine 18 Nov night, then authenticate.

Holds the continuation flock. No dispatch, rerun, or extra BMAD agent.
Exits 0 if authentication already exists. Observer may resume.
"""
from pathlib import Path
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROFILE = "/home/administrator/.config/gh-cicd-agent"
assert os.environ.get("GH_CONFIG_DIR") == PROFILE
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
assert "TMPDIR" in os.environ
auth = HERE / "scheduled-20261118-authentication.json"
if auth.is_file():
    print("authentication already recorded; not repeating")
    raise SystemExit(0)
observer = subprocess.run([sys.executable, str(HERE / "run-nightly-continuation-20261118.py")],
                          check=False)
if observer.returncode:
    raise SystemExit(observer.returncode)
raise SystemExit(subprocess.run(
    [sys.executable, str(HERE / "authenticate-scheduled-20261118.py")]).returncode)
