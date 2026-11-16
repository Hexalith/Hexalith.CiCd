"""Apply the human-approved verification to exact pilot preparation/probe commits.

Run under run-with-temp from CiCd after the shared verifier is released. This
does not commit or push, author owned module files or initialize submodules.
Product builds use direct-repository exports and an in-memory CI configuration.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
COMMON = {"tools/verify_nuget_release.py", "tools/test_verify_nuget_release.py",
          "tools/release-packages.json", "package.json", "package-lock.json"}
COMMONS_PRODUCT = {"scripts/pack-release-packages.py", "scripts/validate-consumer-package-references.py",
                   ".github/actions/after-unit-tests/action.yml"}
ALLOWED = {name: set(COMMON) for name in MODULES}
ALLOWED["Hexalith.Commons"].update(COMMONS_PRODUCT)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("builds_tag")
parser.add_argument("commons_base")
parser.add_argument("commons_head")
parser.add_argument("poly_base")
parser.add_argument("poly_head")
parser.add_argument("--purpose", choices=("preparation", "probe"), default="preparation")
parser.add_argument("--commons-repository", type=Path, default=ROOT / "references/Hexalith.Commons")
parser.add_argument("--poly-repository", type=Path, default=ROOT / "references/Hexalith.PolymorphicSerializations")
arguments = parser.parse_args()
assert re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", arguments.builds_tag)
revisions = {MODULES[0]: (arguments.commons_base, arguments.commons_head),
             MODULES[1]: (arguments.poly_base, arguments.poly_head)}
repositories = {MODULES[0]: arguments.commons_repository.resolve(), MODULES[1]: arguments.poly_repository.resolve()}
assert all(re.fullmatch(r"[a-f0-9]{40}", sha) for pair in revisions.values() for sha in pair)
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
if arguments.purpose == "probe":
    assert all(path.is_relative_to(Path(os.environ["TMPDIR"]).resolve()) for path in repositories.values())
    ALLOWED = {MODULES[0]: COMMONS_PRODUCT | {"pilot-ci-probe.md"}, MODULES[1]: {"pilot-ci-probe.md"}}
workspace = Path(os.environ["TMPDIR"]) / ("pilot-prepush-" + arguments.purpose)
(workspace / "references").mkdir(parents=True)
report = {"started_at": datetime.now(timezone.utc).isoformat(), "builds_tag": arguments.builds_tag,
          "purpose": arguments.purpose,
          "approval": "2026-11-16 human decision recorded in story 11 frozen constraints",
          "product_output_log": "pre-adoption-" + ("probe-" if arguments.purpose == "probe" else "") + "verification.log",
          "modules": {}, "operations": []}
report_path = HERE / ("pre-adoption-" + ("probe-" if arguments.purpose == "probe" else "") + "verification.json")


def save():
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def command(command, repository, *, env=None):
    result = subprocess.run(command, cwd=repository, env=env, text=True, capture_output=True, timeout=120)
    report["operations"].append({"command": command, "cwd": str(repository),
                                  "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    save()
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def export(repository, revision, destination):
    destination.mkdir()
    archive = workspace / (destination.name + ".tar")
    with archive.open("wb") as output:
        subprocess.run(["git", "archive", revision], cwd=repository, stdout=output, check=True)
    with tarfile.open(archive) as payload:
        payload.extractall(destination, filter="data")
    archive.unlink()


builds = ROOT / "references/Hexalith.Builds"
release = json.loads(command(["gh", "api", "repos/Hexalith/Hexalith.Builds/releases/tags/" + arguments.builds_tag], ROOT))
assert release["tag_name"] == arguments.builds_tag and release["draft"] is False
assert release["prerelease"] is False and isinstance(release["published_at"], str)
assert release["immutable"] is True and release["author"]["login"] == "github-actions[bot]"
command(["git", "fetch", "--no-recurse-submodules", "origin", "tag", arguments.builds_tag], builds)
builds_sha = command(["git", "rev-parse", arguments.builds_tag + "^{commit}"], builds)
command(["git", "merge-base", "--is-ancestor", "65fd22f37b9fad64b595841923cdbe050563ab99", builds_sha], builds)
command(["git", "fetch", "--no-recurse-submodules", "origin", "main"], builds)
command(["git", "merge-base", "--is-ancestor", builds_sha, "origin/main"], builds)
report["builds_sha"] = builds_sha
report["release"] = {key: release.get(key) for key in ("id", "tag_name", "immutable", "published_at", "html_url")}
trusted = workspace / "references/Hexalith.Builds"
export(builds, builds_sha, trusted)
assert b"verify_packages(values)" in (trusted / "Github/lib/release_publish.py").read_bytes()
sys.path.insert(0, str(trusted / "Github/lib"))
import audit_lint
import ci_pipeline
import expected_state
import guard_actions
import guard_commitlint
from guard_tools import Tools

tool_directory = workspace / "guard-tools"
tool_directory.mkdir()
tools = Tools(tool_directory)
token_environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                         GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    token_environment.pop(name, None)
for name, (base, head) in revisions.items():
    repository = repositories[name]
    command(["git", "fetch", "--no-recurse-submodules", "origin", "main"], repository, env=token_environment)
    assert command(["git", "rev-parse", "origin/main"], repository) == base
    assert command(["git", "rev-parse", "HEAD"], repository) == head
    assert command(["git", "status", "--porcelain", "--ignore-submodules=all"], repository) == ""
    git = expected_state.Git(repository)
    before, candidate = (expected_state.tree_snapshot(git, sha) for sha in (base, head))
    changed = sorted(path for path in set(before.items) | set(candidate.items)
                     if before.items.get(path) != candidate.items.get(path))
    assert changed and set(changed).issubset(ALLOWED[name]), changed
    if arguments.purpose == "probe":
        assert "pilot-ci-probe.md" in changed and "pilot-ci-probe.md" not in before.items
        assert candidate.items["pilot-ci-probe.md"].mode == "100644"
        expected_probe = "# CI/CD pilot probe\n\nDisposable product branch for " + name + ".\nDo not merge this pull request.\n"
        assert candidate.read("pilot-ci-probe.md") == expected_probe.encode()
    # This comparison covers the entire remaining tree, including every owned
    # blob, mode, instruction/settings portion, .gitmodules and Git gitlink.
    unchanged = []
    for path in sorted((set(before.items) | set(candidate.items)) - ALLOWED[name]):
        old, new = before.items.get(path), candidate.items.get(path)
        assert old is not None and old == new, path
        record = {"path": path, "mode": old.mode, "oid": old.oid}
        if old.mode != "160000":
            old_bytes, new_bytes = before.read(path), candidate.read(path)
            assert old_bytes == new_bytes, path
            record["sha256"] = hashlib.sha256(old_bytes).hexdigest()
        unchanged.append(record)
    canonical = json.dumps(unchanged, sort_keys=True, separators=(",", ":")).encode()
    audit_lint.lint(candidate)
    guard_actions.lint(candidate, tools)
    guard_commitlint.lint(git, tools, event_name="push", event={}, frozen_head=head, commit_range=(base, head))
    # Check the legacy owning policy too; its pinned commitlint matches the
    # integrity-locked shared CLI used above, even when npm files are retired.
    lock = json.loads(before.read("package-lock.json"))
    assert lock["packages"]["node_modules/@commitlint/cli"]["version"] == "21.2.4"
    assert lock["packages"]["node_modules/@commitlint/config-conventional"]["version"] == "21.2.4"
    config = tool_directory / (name + ".commitlint.config.mjs")
    config.write_bytes(before.read("commitlint.config.mjs"))
    for sha in command(["git", "rev-list", "--reverse", base + ".." + head], repository).splitlines():
        result = subprocess.run(["node", str(tool_directory / "node_modules/@commitlint/cli/cli.js"),
                                 "--config", str(config), "--color=false"],
                                cwd=tool_directory, env=tools.environment,
                                input=guard_commitlint.message(git, sha), text=True, capture_output=True, timeout=120)
        assert result.returncode == 0, result.stdout + result.stderr
    report["modules"][name] = {"base": base, "head": head, "repository": str(repository),
        "allowed_changed_paths": sorted(ALLOWED[name]), "changed_paths": changed,
        "unchanged_byte_mode_gitlink_records": unchanged,
        "unchanged_records_sha256": hashlib.sha256(canonical).hexdigest(),
        "policy_and_commit_validation": "pass", "owning_commitlint_version": "21.2.4"}
    export(repository, head, workspace / "references" / name)
    save()

os.environ.update(NUGET_PACKAGES=str(workspace / ".nuget/packages"),
    NUGET_HTTP_CACHE_PATH=str(workspace / ".nuget/http"), NUGET_PLUGINS_CACHE_PATH=str(workspace / ".nuget/plugins"),
    DOTNET_CLI_HOME=str(workspace / ".dotnet"), MinVerVersionOverride="0.0.0")
for name, (base, head) in revisions.items():
    module = workspace / "references" / name
    document = {"schema": "hexalith.ci.v1", "buildsTag": arguments.builds_tag,
        "solution": name + ".slnx", "dapr": False, "browsers": False, "registry": False,
        "codeql": ["csharp"], "tests": {"integration": [], "exclude": {}},
        "hooks": ["after-unit-tests"] if name == "Hexalith.Commons" else [], "jobs": {}, "submodules": []}
    ci_pipeline.validate_config(document, repository="Hexalith/" + name)
    prepared = ci_pipeline.PreparedConfig(workspace, module, document, document["solution"], "global.json", ())
    ci_pipeline.restore_and_build(prepared)
    classified = ci_pipeline.run_unit_tests(prepared, repository="Hexalith/" + name)
    assert len(classified.unit) == (8 if name == "Hexalith.Commons" else 1)
    if name == "Hexalith.Commons":
        packages = workspace / "commons-packages"
        for script, tail in (("pack-release-packages.py", [str(packages), "0.0.0", "--nuget-config", str(trusted / "NuGet.ci.Config")]),
                             ("validate-nuget-packages.py", [str(packages)]),
                             ("validate-consumer-package-references.py", [str(packages)])):
            subprocess.run([sys.executable, "scripts/" + script, *tail], cwd=module, check=True)
        report["modules"][name]["payload_symbol_consumer_checks"] = "pass"
    report["modules"][name]["product_build_and_all_unit_projects"] = "pass"
    report["modules"][name]["unit_projects"] = list(classified.unit)
    save()
    repository = repositories[name]
    command(["git", "fetch", "--no-recurse-submodules", "origin", "main"], repository, env=token_environment)
    assert command(["git", "rev-parse", "origin/main"], repository) == base, "Main advanced during checking"
    assert command(["git", "rev-parse", "HEAD"], repository) == head
    assert command(["git", "status", "--porcelain", "--ignore-submodules=all"], repository) == ""
for name, (base, head) in revisions.items():
    # Revisit Commons after Poly's verification as well. A separate immediate
    # fetch/base/head check remains required at each actual push boundary.
    repository = repositories[name]
    command(["git", "fetch", "--no-recurse-submodules", "origin", "main"], repository, env=token_environment)
    assert command(["git", "rev-parse", "origin/main"], repository) == base, "Main advanced during checking"
    assert command(["git", "rev-parse", "HEAD"], repository) == head
    assert command(["git", "status", "--porcelain", "--ignore-submodules=all"], repository) == ""
    report["modules"][name]["final_all_module_freshness"] = "pass"
    save()
report["completed_at"] = datetime.now(timezone.utc).isoformat()
report["result"] = "pass"
report["push_performed"] = False
report["nested_submodule_initialization"] = False
save()
print("Approved pre-adoption verification passed for both exact " + arguments.purpose + " commits.", flush=True)
