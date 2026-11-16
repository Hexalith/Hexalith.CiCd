"""Prepare local pilot product commits after authenticated shared release.

No module remote ref is changed. Main pushes must wait for the independent
cleanup identity disposition, complete approved verification, and prompt adoption.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
RETIRE = {"tools/verify_nuget_release.py", "tools/test_verify_nuget_release.py",
          "tools/release-packages.json", "package.json", "package-lock.json"}
PRODUCT = {".github/actions/after-unit-tests/action.yml", "scripts/pack-release-packages.py",
           "scripts/validate-consumer-package-references.py"}
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
release = json.loads((HERE / "builds-released-pin.json").read_text())
assert release["result"] == "acceptable released shared behavior" and release["outcome"]["outcome"] == "published"
validation = json.loads((HERE / "product-commit-message-validation.json").read_text())
assert validation["result"] == "pass"
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)
report_path = HERE / "local-product-preparation.json"
assert not report_path.exists(), "Inspect existing local preparation instead of repeating commits"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "builds_tag": release["release"]["tag_name"],
          "released_source": release["source_sha"], "remote_push_performed": False,
          "full_approved_verification": "required before each eventual push",
          "main_push_gate": "pending Zot identity disposition; adoption must follow promptly",
          "modules": {}, "operations": []}
sys.path.insert(0, str(ROOT / "references/Hexalith.Builds/Github/lib"))
from expected_state import Git, tree_snapshot


def save():
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, repository, *, credential=False):
    result = subprocess.run(arguments, cwd=repository, env=environment if credential else None,
                            capture_output=True, text=True, timeout=120)
    report["operations"].append({"command": arguments, "cwd": str(repository), "exit": result.returncode,
                                  "stdout": result.stdout, "stderr": result.stderr})
    save()
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


for name in MODULES:
    source = ROOT / "references" / name
    run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], source, credential=True)
    base = run(["git", "rev-parse", "origin/main"], source)
    assert run(["git", "rev-parse", "HEAD"], source) == base
    record = validation["modules"][name]
    assert record["base"] == base
    for filename, key in (("commitlint.config.mjs", "owning_config_sha256"), ("package-lock.json", "owning_lock_sha256")):
        blob = subprocess.run(["git", "show", base + ":" + filename], cwd=source, capture_output=True, check=True).stdout
        assert hashlib.sha256(blob).hexdigest() == record[key]
    message = HERE / ("product-message-" + name + ".txt")
    assert hashlib.sha256(message.read_bytes()).hexdigest() == record["message_sha256"]
    staged = set(run(["git", "diff", "--cached", "--name-only"], source).splitlines())
    assert staged == (PRODUCT if name == MODULES[0] else set()), staged
    assert run(["git", "diff", "--name-only", "--ignore-submodules=all"], source) == ""
    assert run(["git", "ls-files", "--others", "--exclude-standard"], source) == ""
    branch = "cicd-pilot-preparation-" + ("commons" if name == MODULES[0] else "poly") + "-20261116"
    run(["git", "switch", "-c", branch, "origin/main"], source)
    run(["git", "rm", "--", *sorted(RETIRE)], source)
    run(["git", "commit", "--file", str(message)], source)
    head = run(["git", "rev-parse", "HEAD"], source)
    assert run(["git", "rev-parse", "HEAD^"], source) == base
    git = Git(source)
    before, candidate = (tree_snapshot(git, sha) for sha in (base, head))
    allowed = RETIRE | (PRODUCT if name == MODULES[0] else set())
    changed = sorted(path for path in set(before.items) | set(candidate.items)
                     if before.items.get(path) != candidate.items.get(path))
    assert set(changed) == allowed
    assert not RETIRE & set(candidate.items)
    unchanged = []
    for path in sorted((set(before.items) | set(candidate.items)) - allowed):
        assert before.items.get(path) is not None and before.items[path] == candidate.items.get(path), path
        item = before.items[path]
        row = {"path": path, "mode": item.mode, "oid": item.oid}
        if item.mode != "160000":
            assert before.read(path) == candidate.read(path), path
            row["sha256"] = hashlib.sha256(before.read(path)).hexdigest()
        unchanged.append(row)
    assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], source) == ""
    nested = source / "references/Hexalith.Builds"
    assert nested.is_dir() and not any(nested.iterdir())
    report["modules"][name] = {"branch": branch, "base": base, "head": head, "changed_paths": changed,
                               "unchanged_byte_mode_gitlink_records": unchanged,
                               "message_and_owning_policy_inputs_match_validated_hashes": True,
                               "original_nested_builds_uninitialized": True}
    save()
report["completed_at"] = datetime.now(timezone.utc).isoformat()
report["result"] = "exact local product candidates prepared; no remote main push"
save()
print(json.dumps({name: {key: report["modules"][name][key] for key in ("branch", "base", "head")}
                  for name in MODULES}, indent=2), flush=True)
