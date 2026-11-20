#!/usr/bin/env python3
"""Write the reviewed pre-adoption FrontComposer workflow patch to stdout."""
import argparse
import difflib
from pathlib import Path
import re
import subprocess
import sys

BASE = "c1aea1732d3ce2dca299f1d9aa5ce709958ba87d"
BUILDS = "fe68718b6c074a6b500a7191e3554a1d39e17688"
TAG = "v6.4.4"
ROUTER_ACTION = ".github/actions/test-source-router/action.yml"
ROUTER_BLOB = "61ef38bd3288bdd099d9ddf55067435a8bf6e588"
INITIALIZE = "Github/initialize-build"
WORKFLOWS = {
    "codeql": (".github/workflows/codeql.yml", 1),
    "commitlint": (".github/workflows/commitlint.yml", 1),
    "dependency-review": (".github/workflows/dependency-review.yml", 1),
    "flaky-test-governance": (INITIALIZE, 1),
    "mutation-property-nightly": (INITIALIZE, 3),
    "nightly": (INITIALIZE, 1),
    "quality": (INITIALIZE, 2),
    "quarantine-governance-nightly": (INITIALIZE, 1),
}


def git(repository, *args):
    return subprocess.check_output(["git", "-C", str(repository), *args]).decode("utf-8")


def patch(module, builds, revision):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Supply a full lower-case module commit SHA")
    if git(module, "rev-parse", revision + "^{commit}").strip() != revision:
        raise ValueError("The selected module object must be a commit")
    if (Path(__file__).resolve().parents[1] / "builds-version").read_text().strip() != TAG:
        raise ValueError("CiCd's Builds selection changed; requalify this proposal")
    if git(builds, "rev-parse", f"refs/tags/{TAG}^{{commit}}").strip() != BUILDS:
        raise ValueError("The selected Builds tag has an unexpected commit")
    if revision != BASE:
        subprocess.run(["git", "-C", str(module), "merge-base", "--is-ancestor", BASE, revision], check=True)
        if git(module, "rev-parse", f"{revision}:{ROUTER_ACTION}").strip() != ROUTER_BLOB:
            raise ValueError("Selected product commit is missing the reviewed router action")
        test_path = "tests/Hexalith.FrontComposer.Shell.Tests/Governance/CiGovernanceTests.cs"
        if "Hexalith.Builds/.github/workflows/commitlint.yml@main" in git(module, "show", f"{revision}:{test_path}"):
            raise ValueError("Selected product commit still requires the moving commitlint reference")

    output = []
    for name, (target, expected_count) in WORKFLOWS.items():
        path = f".github/workflows/{name}.yml"
        old = git(module, "show", f"{BASE}:{path}")
        if old != git(module, "show", f"{revision}:{path}"):
            raise ValueError(f"{path} changed since review; requalify the owner patch")
        implementation = "Github/initialize-build/action.yml" if target == INITIALIZE else target
        git(builds, "cat-file", "-e", f"{BUILDS}:{implementation}")
        reference = f"uses: Hexalith/Hexalith.Builds/{target}@"
        before = reference + "main\n"
        if old.count(before) != expected_count:
            raise ValueError(f"Unexpected number of floating references in {path}")
        new = old.replace(before, f"{reference}{BUILDS} # {TAG}\n")
        if name == "quality":
            marker = "      - name: Typecheck Epic 9 browser proof\n"
            if new.count(marker) != 1:
                raise ValueError("Cannot identify the prepared source-mode job")
            new = new.replace(marker, "      - name: Test the combined UI router\n"
                              "        uses: ./.github/actions/test-source-router\n\n" + marker)
        output.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                          fromfile="a/" + path, tofile="b/" + path))
    return "".join(output).encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, type=Path, help="local FrontComposer repository")
    parser.add_argument("--builds", required=True, type=Path, help="local Builds repository with release tags")
    parser.add_argument("--revision", default=BASE, help="exact product commit, defaults to the audited baseline")
    args = parser.parse_args()
    try:
        sys.stdout.buffer.write(patch(args.module, args.builds, args.revision))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
