"""Verify AI.Tools' narrowly approved preparation without remote operations.

Run with run-with-temp. --message-only validates the saved exact candidate before
the local commit; the default checks the committed base/head in a standalone
local clone. This proof neither pushes nor establishes adoption or live freshness.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = "736687b79c1e4fa8beabdab75c4675bb76c466b9"
ALLOWED = {"AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", "README.md",
           "hexalith-git-instructions.md", "hexalith-llm-instructions.md",
           "package.json", "package-lock.json"}
ENTRYPOINTS = ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--module", type=Path,
                    default=ROOT.parent / "ai-tools-story-12")
parser.add_argument("--message-only", action="store_true")
args = parser.parse_args()
scratch = Path(os.environ["TMPDIR"]).resolve() / "ai-tools-preparation"
scratch.mkdir()
report = {"started_at": datetime.now(timezone.utc).isoformat(),
          "approval": "AI.Tools only; story 12 frozen human decision, 2026-11-16",
          "phase": "local preparation; no remote operations", "base": BASE,
          "module": str(args.module.resolve()), "operations": [],
          "remote_freshness": "pending immediately before any future push",
          "normal_checker_passed": False, "push_performed": False,
          "nested_submodules_initialized": False}
report_path = HERE / ("message-validation.json" if args.message_only else "preparation-proof.json")


def save():
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def command(arguments, cwd, **kwargs):
    result = subprocess.run(list(map(str, arguments)), cwd=cwd,
                            capture_output=True, timeout=180, **kwargs)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


try:
    builds = ROOT / "references/Hexalith.Builds"
    tag = (ROOT / "builds-version").read_text().strip()
    released = json.loads((HERE.parent / "11/builds-released-pin.json").read_text())
    source = command(["git", "rev-parse", tag + "^{commit}"], builds).decode().strip()
    assert tag == released["release"]["tag_name"] and source == released["source_sha"]
    assert released["release"]["immutable"] and released["release_author"] == "github-actions[bot]"
    report.update(builds_tag=tag, builds_source=source,
                  publication_observation="../11/builds-released-pin.json; live revalidation pending")
    trusted = scratch / "builds"
    trusted.mkdir()
    archive = scratch / "builds.tar"
    with archive.open("wb") as output:
        subprocess.run(["git", "archive", source], cwd=builds, stdout=output, check=True)
    with tarfile.open(archive) as payload:
        payload.extractall(trusted, filter="data")
    sys.path.insert(0, str(trusted / "Github/lib"))
    import audit_lint
    import expected_state
    import guard_commitlint
    from guard_tools import Tools

    tooling = scratch / "tools"
    tooling.mkdir()
    tools = Tools(tooling)
    original = expected_state.Git(args.module.resolve())
    before = expected_state.tree_snapshot(original, BASE)
    lock = json.loads(before.read("package-lock.json"))
    shared_lock = json.loads((trusted / "Github/guard/package-lock.json").read_bytes())
    for package in ("@commitlint/cli", "@commitlint/config-conventional"):
        key = "node_modules/" + package
        assert lock["packages"][key]["version"] == shared_lock["packages"][key]["version"]
    legacy_config = tooling / "legacy.commitlint.config.mjs"
    legacy_config.write_bytes(before.read("commitlint.config.mjs"))
    message_path = HERE / "product-commit-message.txt"
    message = message_path.read_text()
    tools.lint_message(message, "exact candidate")
    result = subprocess.run(["node", str(tooling / "node_modules/@commitlint/cli/cli.js"),
                             "--config", str(legacy_config), "--color=false"],
                            cwd=tooling, env=tools.environment, input=message, text=True,
                            capture_output=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    report.update(exact_message=message, exact_message_sha256=hashlib.sha256(message.encode()).hexdigest(),
                  shared_commitlint="pass", prior_owning_commitlint="pass",
                  commitlint_version=lock["packages"]["node_modules/@commitlint/cli"]["version"])
    if not args.message_only:
        assert not command(["git", "status", "--porcelain"], args.module).strip()
        head = command(["git", "rev-parse", "HEAD"], args.module).decode().strip()
        assert command(["git", "rev-parse", "origin/main"], args.module).decode().strip() == BASE
        clone = scratch / "module"
        command(["git", "clone", "--quiet", "--no-hardlinks", "--no-recurse-submodules",
                 str(args.module.resolve()), str(clone)], scratch)
        git = expected_state.Git(clone)
        assert guard_commitlint.message(git, head) == message
        assert git.run("rev-parse", head + "^").decode().strip() == BASE
        candidate = expected_state.tree_snapshot(git, head)
        changed = sorted(path for path in set(before.items) | set(candidate.items)
                         if before.items.get(path) != candidate.items.get(path))
        assert set(changed) == ALLOWED, changed
        unchanged = []
        for path in sorted((set(before.items) | set(candidate.items)) - ALLOWED):
            old, new = before.items.get(path), candidate.items.get(path)
            assert old is not None and old == new, path
            record = {"path": path, "mode": old.mode, "oid": old.oid}
            if old.mode != "160000":
                assert before.read(path) == candidate.read(path), path
                record["sha256"] = hashlib.sha256(before.read(path)).hexdigest()
            unchanged.append(record)
        assert json.loads(before.read("package.json"))["devDependencies"] == {
            "@commitlint/cli": "21.2.4", "@commitlint/config-conventional": "21.2.4"}
        for path in ("package.json", "package-lock.json"):
            assert path not in candidate.items
        legacy = "commitlint.config.mjs"
        assert before.items[legacy] == candidate.items[legacy]
        assert before.read(legacy) == candidate.read(legacy)
        for snapshot in (before, candidate):
            assert not any(path.startswith(".github/workflows/") for path in snapshot.items)
            for path in (".github/hexalith-ci.json", ".github/dependabot.yml", ".gitmodules",
                         ".claude/settings.json", "references/Hexalith.Builds"):
                assert path not in snapshot.items, path
            assert not any(item.mode == "160000" for item in snapshot.items.values())
            for path in ENTRYPOINTS:
                assert b"<!-- hexalith-cicd:" not in snapshot.read(path)
        entries = [candidate.read(path) for path in ENTRYPOINTS]
        assert len(set(entries)) == 1
        assert len({data.decode().replace("\r\n", "\n") for data in entries}) == 1
        docs = b"\n".join(candidate.read(path) for path in ALLOWED if path in candidate.items)
        for stale in (b"npm ci", b"npx --no", b"pinned commitlint CLI", b"until the CiCd pilot"):
            assert stale not in docs, stale
        assert b"python3 references/Hexalith.Builds/check.py" in candidate.read("README.md")
        assert b"Do not use it to import" in candidate.read("hexalith-llm-instructions.md")
        assert not any(path.endswith((".slnx", ".csproj", ".fsproj", ".vbproj"))
                       for path in candidate.items)
        audit_lint.lint(candidate)
        guard_commitlint.lint(git, tools, event_name="push", event={}, frozen_head=head,
                              commit_range=(BASE, head))
        command(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check", BASE, head], clone)
        normal = subprocess.run([sys.executable, "references/Hexalith.Builds/check.py"],
                                cwd=clone, capture_output=True, text=True)
        assert normal.returncode == 2 and not (clone / "references").exists()
        report.update(head=head, head_tree=git.run("rev-parse", head + "^{tree}").decode().strip(),
                      changed_paths=changed, unchanged_byte_mode_gitlink_records=unchanged,
                      owned_state="pre-existing commitlint.config.mjs preserved exactly for delivery-owned deletion; other protected paths and delivered blocks remain absent",
                      preserved_legacy_commitlint_config={"path": legacy, "mode": candidate.items[legacy].mode,
                          "oid": candidate.items[legacy].oid, "sha256": hashlib.sha256(candidate.read(legacy)).hexdigest(),
                          "disposition": "awaiting deletion by delivery through absent-glob ownership"},
                      entrypoints="identical bytes and normalized text", audit_lint="pass",
                      documentation_removal_consistency="pass", exact_committed_messages="pass",
                      normal_checker={"command": [sys.executable, "references/Hexalith.Builds/check.py"],
                                      "exit": normal.returncode,
                                      "result": "unavailable before adoption; not a successful normal check"})
    report["result"] = "pass"
except Exception as error:
    report.update(result="failed", error=str(error))
    raise
finally:
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()

print("Exact message validation passed." if args.message_only else "Approved local preparation proof passed.")
