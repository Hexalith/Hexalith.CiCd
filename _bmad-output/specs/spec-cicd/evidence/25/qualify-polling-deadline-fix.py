"""Verify the real polling/deadline tests against isolated current source inputs.

Run through run-with-temp. This is local product verification, not adoption or
an exact committed preparation-push attestation.
"""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import subprocess
import tarfile


EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[4]
MODULE = ROOT / "references/Hexalith.Timesheets"


def git(root, *arguments):
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


def main():
    scratch = Path(os.environ["TMPDIR"])
    target = scratch / "Timesheets"
    subprocess.run(["git", "clone", "--quiet", "--shared", "--no-recurse-submodules",
                    str(MODULE), str(target)], check=True)
    patch = subprocess.check_output(["git", "-C", str(MODULE), "diff", "--binary", "HEAD"])
    subprocess.run(["git", "-C", str(target), "apply"], input=patch, check=True)
    untracked = subprocess.check_output(["git", "-C", str(MODULE), "ls-files", "--others",
                                         "--exclude-standard", "-z"]).split(b"\0")
    additions = {}
    for raw in untracked:
        if not raw:
            continue
        relative = os.fsdecode(raw)
        source = MODULE / relative
        if source.is_file() and not source.is_symlink():
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            additions[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
    revisions = {"module": git(MODULE, "rev-parse", "HEAD")}
    for name in ("Builds", "EventStore", "Works"):
        relative = "references/Hexalith." + name
        source = ROOT / relative
        revision = git(source, "rev-parse", "HEAD") if name == "Builds" else git(MODULE, "rev-parse", "HEAD:" + relative)
        revisions[relative] = revision
        archive = scratch / (name + ".tar")
        subprocess.run(["git", "-C", str(source), "archive", "--output", str(archive), revision], check=True)
        destination = target / relative
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as payload:
            payload.extractall(destination, filter="data")
    catalog = ROOT / "references/Hexalith.Builds/Props/Directory.Packages.props"
    (target / "references/Hexalith.Builds/Props/Directory.Packages.props").write_bytes(catalog.read_bytes())
    project = "tests/Hexalith.Timesheets.Server.Tests/Hexalith.Timesheets.Server.Tests.csproj"
    commands = [
        ["dotnet", "build", project, "--configuration", "Release", "-noAutoResponse",
         "-p:UseHexalithProjectReferences=false", "-warnaserror", "-m:1", "/nr:false",
         "-p:RestoreConfigFile=" + str(target / "references/Hexalith.Builds/NuGet.ci.Config")],
        ["dotnet", "tests/Hexalith.Timesheets.Server.Tests/bin/Release/net10.0/Hexalith.Timesheets.Server.Tests.dll",
         "-class", "Hexalith.Timesheets.Server.Tests.MagicLinkDurableSubmissionServiceTests", "-noColor"],
        ["dotnet", "test", "--project", project, "--configuration", "Release", "--no-build", "--no-restore",
         "-p:UseHexalithProjectReferences=false"],
    ]
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "revisions": revisions,
              "module_patch_sha256": hashlib.sha256(patch).hexdigest(), "additions": additions,
              "catalog_sha256": hashlib.sha256(catalog.read_bytes()).hexdigest(), "results": [],
              "remote_operations": False, "adoption": False}
    result_path = EVIDENCE / "polling-deadline-fix.json"
    log_path = EVIDENCE / "polling-deadline-fix.log"
    environment = dict(os.environ, DOTNET_CLI_HOME=str(scratch / "dotnet-home"),
                       DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", MSBUILDDISABLENODEREUSE="1")
    with log_path.open("w") as log:
        for command in commands:
            print("RUN", *command, flush=True)
            outcome = subprocess.run(command, cwd=target, env=environment, stdout=log, stderr=subprocess.STDOUT)
            report["results"].append({"command": command, "exit": outcome.returncode})
            result_path.write_text(json.dumps(report, indent=2) + "\n")
            if outcome.returncode:
                print("\n".join(log_path.read_text(errors="replace").splitlines()[-45:]))
                return outcome.returncode
    report["complete"] = True
    result_path.write_text(json.dumps(report, indent=2) + "\n")
    print("\n".join(log_path.read_text(errors="replace").splitlines()[-15:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
