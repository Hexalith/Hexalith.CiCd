"""Read-only story 11 checkpoint audit; no tests, pushes or settings writes."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)


def git(repository, *arguments):
    return subprocess.run(["git", *arguments], cwd=repository, capture_output=True, text=True,
                          check=True, timeout=60).stdout.strip()


def get(endpoint):
    result = subprocess.run(["gh", "api", endpoint], cwd=ROOT, env=environment,
                            capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def save(name, document):
    (HERE / name).write_text(json.dumps(document, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec_path = ROOT / "_bmad-output/implementation-artifacts/spec-11-pilot-migration-commons-and-polymorphicserializations.md"
relative = str(spec_path.relative_to(ROOT))
baseline = "37e73a99dfe82c3b7741554d6f4ff2207711644b"
original = subprocess.run(["git", "show", baseline + ":" + relative], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout
current = spec_path.read_text()
approved = json.loads((HERE / "approved-intent-audit.json").read_text())["approved_paragraph"]
frozen = lambda text: re.search(r"(?s)<frozen-after-approval[^>]*>.*?</frozen-after-approval>", text).group()
old_block, new_block = frozen(original), frozen(current)
assert new_block.count(approved) == 1
assert new_block.replace(approved + "\n\n", "", 1) == old_block
assert "baseline_commit: '" + baseline + "'" in current
intent = {"observed_at": datetime.now(timezone.utc).isoformat(), "baseline_commit": baseline,
          "original_frozen_sha256": hashlib.sha256(old_block.encode()).hexdigest(),
          "current_frozen_sha256": hashlib.sha256(new_block.encode()).hexdigest(),
          "entire_frozen_block_byte_identical_to_baseline": False,
          "approved_delta_only": True, "approved_paragraph": approved,
          "all_other_frozen_bytes_identical": True, "historical_audits_preserved": True, "result": "pass"}
save("checkpoint-intent-audit.json", intent)

proof_sets = {}
for prefix in ("pre-adoption-probe-verification", "pre-adoption-verification"):
    document = json.loads((HERE / (prefix + ".json")).read_text())
    assert document["result"] == "pass" and document["builds_tag"] == "v6.0.6"
    log = (HERE / (prefix + ".log")).read_text()
    tests, selected = [], None
    for line in log.splitlines():
        if line.startswith("Unit tests: "):
            selected = line.removeprefix("Unit tests: ")
        match = re.fullmatch(r"  succeeded: ([0-9]+)", line)
        if match:
            assert selected
            tests.append({"project": selected, "passed": int(match[1])})
    skipped = [int(value) for value in re.findall(r"(?m)^  skipped: ([0-9]+)$", log)]
    assert len(tests) == len(skipped) == 9 and sum(skipped) == 0
    assert sum(test["passed"] for test in tests) == 372
    assert sum(test["passed"] for test in tests if "Commons" in test["project"]) == 357
    assert "Validated 12 Hexalith.Commons packages at version 0.0.0." in log
    assert "Validated isolated package-only consumer build." in log
    proof_sets[document["purpose"]] = {"report_sha256": digest(HERE / (prefix + ".json")),
        "full_log_sha256": digest(HERE / (prefix + ".log")), "test_projects": tests,
        "total_passed": 372, "total_skipped": 0, "payload_symbol_package_pairs": 12,
        "isolated_package_only_consumer": "pass", "result": "pass"}
save("pre-adoption-proof-summary.json", {"observed_at": datetime.now(timezone.utc).isoformat(), "sets": proof_sets})

preparation = json.loads((HERE / "local-product-preparation.json").read_text())
probes = json.loads((HERE / "pre-delivery-probes.json").read_text())
registration = json.loads((HERE / "local-registration-preparation.json").read_text())
status = {"observed_at": datetime.now(timezone.utc).isoformat(), "story_status": "in-progress",
          "shared_release": {"tag": "v6.0.6", "source": "fdda17c0a4538b0f7c99f813c20ca24b49006530",
                             "ci_run": 43834424445, "release_run": 43838534329, "outcome": "published"},
          "modules": {}, "local_registration": "render/contract/published-pin checks pass; no candidate commit/push",
          "full_committed_live_candidate_verdict": "not performed",
          "pending_identity_question": "Identify any remaining legacy Zot automation principal and its pilot scope, or attest that jpiquot and jpiquot@itaneo.com are maintainer-only and no legacy pilot publisher remains.",
          "preparation_main_push_performed": False, "actual_adoption_performed": False,
          "immediate_legacy_cleanup_performed": False, "post_delivery_probe_outcomes": "not performed",
          "real_scheduled_nightly_checkpoint": "not performed"}
for name in MODULES:
    source = ROOT / "references" / name
    module, probe = preparation["modules"][name], probes["modules"][name]
    assert git(source, "rev-parse", "HEAD") == module["head"]
    assert git(source, "status", "--porcelain", "--ignore-submodules=all") == ""
    assert git(source, "show", module["base"] + ":global.json") == (source / "global.json").read_text().strip()
    main = get("repos/Hexalith/" + name + "/git/ref/heads/main")
    assert main["object"]["sha"] == module["base"]
    pull = get("repos/Hexalith/" + name + "/pulls/" + str(probe["pull_request_number"]))
    assert pull["state"] == "open" and pull["merged_at"] is None and pull["head"]["sha"] == probe["head"]
    checks = get("repos/Hexalith/" + name + "/commits/" + probe["head"] + "/check-runs?per_page=100")
    assert checks["total_count"] < 100
    nested = source / "references/Hexalith.Builds"
    assert nested.is_dir() and not any(nested.iterdir())
    status["modules"][name] = {"remote_main": main["object"]["sha"], "local_preparation_head": module["head"],
        "local_preparation_branch": module["branch"], "probe_branch": probe["branch"], "probe_head": probe["head"],
        "probe_pr": pull["number"], "probe_pr_url": pull["html_url"], "probe_state": pull["state"], "probe_merged": False,
        "original_nested_builds_empty": True, "worktrees": git(source, "worktree", "list", "--porcelain"),
        "legacy_probe_checks": [{key: check.get(key) for key in ("id", "name", "status", "conclusion", "html_url")}
                                for check in checks["check_runs"]]}
save("checkpoint-status.json", status)

for name in ("Hexalith.Builds", *MODULES):
    repository = ROOT / "references" / name
    git(repository, "diff", "--check")
    git(repository, "diff", "--cached", "--check")
git(ROOT, "diff", "--check")
git(ROOT, "diff", "--cached", "--check")
staging = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                         capture_output=True, check=True).stdout
assert hashlib.sha256(staging).hexdigest() == registration["original_staging_before_sha256"]
scripts = sorted(HERE.glob("*.py"))
for script in scripts:
    ast.parse(script.read_text(), filename=str(script))

patterns = {"github_credential": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})"),
            "private_key": re.compile(rb"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"),
            "bcrypt_credential_hash": re.compile(rb"\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}"),
            "generated_registry_password": re.compile(rb"(?<![A-Fa-f0-9])[A-Fa-f0-9]{48}(?![A-Fa-f0-9])")}
hits = []
files = sorted(path for path in HERE.rglob("*") if path.is_file())
for path in files:
    payload = path.read_bytes()
    for label, pattern in patterns.items():
        if pattern.search(payload):
            hits.append({"file": str(path.relative_to(ROOT)), "kind": label})
    if environment["GH_TOKEN"].encode() in payload:
        hits.append({"file": str(path.relative_to(ROOT)), "kind": "protected_module_token_value"})
assert not hits, hits
active = []
names = {"observe-builds.py", "pre-adoption-verify.py", "verify-and-publish-probes.py", "prepare-probes.py",
         "prepare-retirement.py", "prepare-local-registration.py", "post-adoption-check.py"}
for process in Path("/proc").iterdir():
    if process.name.isdigit() and int(process.name) != os.getpid():
        try:
            arguments = (process / "cmdline").read_bytes().split(b"\0")
        except (OSError, PermissionError):
            continue
        selected = [Path(value.decode(errors="replace")).name for value in arguments if value and b"\n" not in value]
        matches = names.intersection(selected)
        if matches:
            active.append({"pid": int(process.name), "job_names": sorted(matches)})
assert not active, active
save("checkpoint-checks.json", {"observed_at": datetime.now(timezone.utc).isoformat(), "result": "pass",
     "frozen_intent": "exact approved paragraph only; every other byte preserved", "proof_sets": proof_sets,
     "whitespace": "working and staged diffs pass in root and all three touched direct repositories",
     "original_root_staging_preserved": True, "evidence_python_syntax_count": len(scripts),
     "evidence_files_scanned": len(files), "credential_scan_hits": hits, "active_local_job_processes": active,
     "default_profile": os.environ["GH_CONFIG_DIR"], "inherited_token_overrides_present": False})
print(json.dumps({"result": "pass", "proof_sets": {key: value["total_passed"] for key, value in proof_sets.items()},
                  "credential_hits": len(hits), "active_local_jobs": active, "original_root_staging_preserved": True}, indent=2))
