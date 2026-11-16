#!/usr/bin/env python3
"""Fresh SDK 11/net10 Release build and all six signed consumers in scratch."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile


EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[4]
MODULE = ROOT / "references/Hexalith.Timesheets"
BUILDS = ROOT / "references/Hexalith.Builds"


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    scratch = Path(os.environ["TMPDIR"])
    target = scratch / "Timesheets"
    subprocess.run(["git", "clone", "--quiet", "--shared", "--no-recurse-submodules", str(MODULE), str(target)], check=True)
    # Freeze the actual local module tree without changing any live build output.
    patch = subprocess.check_output(["git", "-C", str(MODULE), "diff", "--binary", "HEAD"])
    if patch:
        subprocess.run(["git", "-C", str(target), "apply"], input=patch, check=True)
    revisions = {"module": git(MODULE, "rev-parse", "HEAD"), "builds": git(BUILDS, "rev-parse", "HEAD")}
    for name in ("Builds", "EventStore", "Works"):
        relative = "references/Hexalith." + name
        source = ROOT / relative
        revision = revisions["builds"] if name == "Builds" else git(MODULE, "rev-parse", "HEAD:" + relative)
        revisions[relative] = revision
        archive = scratch / (name + ".tar")
        subprocess.run(["git", "-C", str(source), "archive", "--output", str(archive), revision], check=True)
        destination = target / relative
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as payload:
            payload.extractall(destination, filter="data")
    inputs = {}
    for relative in ("Props/Directory.Packages.props", "NuGet.ci.Config", "Github/lib/product_validation.py"):
        source = BUILDS / relative
        inputs[relative] = sha(source)
        shutil.copyfile(source, target / "references/Hexalith.Builds" / relative)
    runner = target / "references/Hexalith.Builds/Github/lib/product_validation.py"
    commands = [
        ["dotnet", "build", "Hexalith.Timesheets.slnx", "--configuration", "Release", "-noAutoResponse",
         "-p:UseHexalithProjectReferences=false", "-warnaserror", "-m:1", "/nr:false",
         "-p:RestoreConfigFile=" + str(target / "references/Hexalith.Builds/NuGet.ci.Config")],
        ["python3", "-B", "-I", str(runner), "--workspace", str(target), "--contract", "tools/product-validation.json"],
    ]
    environment = dict(os.environ, DOTNET_CLI_HOME=str(scratch / "cli-home"),
                       DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", MSBUILDDISABLENODEREUSE="1")
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "revisions": revisions,
              "builds_inputs_sha256": inputs, "module_patch_sha256": hashlib.sha256(patch).hexdigest(),
              "results": [], "publication": False, "adoption": False, "remote_operations": False}
    result_path = EVIDENCE / "candidate-signing-timesheets-check.json"
    log_path = EVIDENCE / "candidate-signing-timesheets-check.log"
    with log_path.open("w") as log:
        for command in commands:
            print("RUN", *command, flush=True)
            log.write("RUN " + json.dumps(command) + "\n")
            log.flush()
            outcome = subprocess.run(command, cwd=target, env=environment, stdout=log, stderr=subprocess.STDOUT)
            report["results"].append({"command": command, "exit": outcome.returncode})
            result_path.write_text(json.dumps(report, indent=2) + "\n")
            if outcome.returncode:
                print("\n".join(log_path.read_text(errors="replace").splitlines()[-50:]))
                return outcome.returncode
            if len(report["results"]) == 1:
                rows = json.loads((target / "tools/release-packages.json").read_text())["packages"]
                outputs = [path for row in rows for path in
                           (target / Path(row["project"]).parent / "bin/Release/net10.0").glob(row["id"] + ".*")
                           if path.suffix in (".dll", ".pdb")]
                report["release_outputs_before"] = {str(path.relative_to(target)): sha(path) for path in outputs}
                report["informational_version_inputs"] = {
                    row["id"]: (target / Path(row["project"]).parent / "obj/Release/net10.0" /
                                (row["id"] + ".AssemblyInfo.cs")).read_text()
                    for row in rows}
                report["contract_sha256"] = sha(target / "tools/product-validation.json")
                report["consumer_source_sha256"] = {str(path.relative_to(target)): sha(path)
                                                    for path in (target / "tools/package-consumers").glob("*.cs")}
                result_path.write_text(json.dumps(report, indent=2) + "\n")
    report["release_outputs_unchanged"] = all(sha(target / path) == expected
                                               for path, expected in report["release_outputs_before"].items())
    report["passed_consumers"] = [line for line in log_path.read_text().splitlines() if ": isolated consumer passed" in line]
    report["signer_workspaces_removed"] = not list(scratch.glob("hexalith-product-validation-*"))
    report["complete"] = (len(report["passed_consumers"]) == 6 and report["release_outputs_unchanged"]
                          and report["signer_workspaces_removed"])
    result_path.write_text(json.dumps(report, indent=2) + "\n")
    print("\n".join(log_path.read_text(errors="replace").splitlines()[-30:]))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
