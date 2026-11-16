"""Repeat story 14's local regressions without repository writes."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
SCRATCH = Path(os.environ["TMPDIR"])
REPORT = {"observedAt": datetime.now(timezone.utc).isoformat(),
          "scope": "local committed snapshots; no GitHub or administration operations", "commands": []}


def git(repository, *arguments):
    return subprocess.check_output(["git", "-C", str(repository), *arguments])


def save():
    (HERE / "regressions.json").write_text(json.dumps(REPORT, indent=2) + "\n")


def run(label, command, cwd):
    log = HERE / (label + ".log")
    with log.open("w") as output:
        result = subprocess.run(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "UV_OFFLINE": "1"})
    REPORT["commands"].append({"label": label, "command": command, "exitCode": result.returncode,
                               "log": log.name, "logSha256": hashlib.sha256(log.read_bytes()).hexdigest()})
    save()
    print(label + ": " + str(result.returncode), flush=True)


REPORT["controller"] = git(ROOT, "rev-parse", "HEAD").decode().strip()
REPORT["repositories"] = {}
for name in ("Hexalith.Builds", "Hexalith.Agents"):
    source = ROOT / "references" / name
    destination = SCRATCH / name
    revision = git(source, "rev-parse", "HEAD").decode().strip()
    subprocess.run(["git", "-c", "submodule.recurse=false", "clone", "--quiet", "--shared",
                    "--no-recurse-submodules", str(source), str(destination)], check=True)
    subprocess.run(["git", "-C", str(destination), "checkout", "--quiet", "--detach", revision], check=True)
    REPORT["repositories"][name] = {"revision": revision,
        "tree": git(source, "rev-parse", "HEAD^{tree}").decode().strip(),
        "sourceWorktreeChanges": git(source, "status", "--short").decode().splitlines()}
save()

for version in ("3.12", "3.14"):
    for group in ("ci_config", "ci_pipeline", "local_check"):
        run("builds-" + group + "-python" + version.replace(".", ""), [
            "uv", "run", "--offline", "--python", version, "--with", "jsonschema==4.26.0",
            "--with", "PyYAML==6.0.3", "python", "-B", "-m", "unittest", "discover",
            "-s", "Github/lib/tests", "-p", "test_" + group + ".py", "-v"], SCRATCH / "Hexalith.Builds")

for group in ("built_package_hook", "ui_consumer_assets", "nuget_package_validation", "ui_static_package",
              "publish_release_packages", "release_package_integrity", "package_pack",
              "recover_release_packages", "package_authority_exclusions"):
    run("agents-" + group, ["python3", "-B", "-m", "unittest", "discover", "-s", "tests/tooling",
        "-p", group + "_test.py", "-v"], SCRATCH / "Hexalith.Agents")

REPORT["result"] = "pass" if all(item["exitCode"] == 0 for item in REPORT["commands"]) else "fail"
save()
raise SystemExit(REPORT["result"] != "pass")
