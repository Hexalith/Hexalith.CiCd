#!/usr/bin/env python3
"""Execute the four real legacy preparation commands with synthetic metadata authority."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def qualify(builds):
    documents = [yaml.safe_load((builds / ".github/workflows/domain-ci.yml").read_text()),
                 yaml.safe_load((builds / "Github/prepare-domain-release/action.yml").read_text())]
    steps = [step for job in documents[0]["jobs"].values() for step in job.get("steps", [])]
    steps += documents[1]["runs"]["steps"]
    prepared = [step for step in steps if step.get("name") == "Prepare package dependencies"]
    if len(prepared) != 4:
        raise ValueError("The reviewed legacy entry points must execute four preparation commands")
    results = []
    for index, step in enumerate(prepared):
        with tempfile.TemporaryDirectory(prefix="works-package-auth-") as temporary:
            root = Path(temporary)
            script = root / "prepare.sh"
            script.write_text("#!/bin/bash\nset -eu\n"
                "test \"${GH_TOKEN:-}\" = synthetic-read-metadata-authority\n"
                "printf authenticated > observed\n")
            environment = {key: value for key, value in os.environ.items()
                           if key not in ("GH_TOKEN", "GITHUB_TOKEN")}
            replacements = {"${{ inputs.package-prepare-script }}": "prepare.sh",
                            "${{ github.token }}": "synthetic-read-metadata-authority"}
            environment.update({key: replacements.get(value, value) for key, value in step.get("env", {}).items()})
            result = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
                                    cwd=root, env=environment, capture_output=True, text=True)
            if result.returncode or (root / "observed").read_text() != "authenticated":
                raise ValueError("Real preparation command did not receive scoped metadata authority")
            # Removing the step token must fail the same child; parent credentials cannot mask this control.
            environment.pop("GH_TOKEN", None)
            (root / "observed").unlink()
            negative = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
                                      cwd=root, env=environment, capture_output=True, text=True)
            if negative.returncode == 0 or (root / "observed").exists():
                raise ValueError("Missing metadata authority unexpectedly passed preparation")
            results.append({"entry": index + 1, "authenticated": True, "missing_token_refused": True})
    return {"status": "passed", "steps": results, "real_credentials_used": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--builds", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    result = qualify(args.builds.resolve())
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
