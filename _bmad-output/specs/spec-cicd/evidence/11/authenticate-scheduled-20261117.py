"""Authenticate the genuine 2026-11-17 scheduled nightly checkpoint.

Read-only CiCd-agent observations. No dispatch, rerun, owned-file edit, nested
initialization, credential switch or manufactured success. ZIP members are
parsed in memory. Job-log archives stay under TMPDIR; excerpts are saved.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PROFILE = "/home/administrator/.config/gh-cicd-agent"
REQUIRED_FIX = "d04c9ab7a8fa43dc6dac1f15d34135aba8e79551"
REQUIRED_POLICY = "3427f041c5f686c460c1fa027cf6f835791209c1"
PILOTS = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
OBSERVER_ID = 44067556763
DIAGNOSTIC_DELIVERY = 43889937298
CODEQL_GATE = "release CodeQL security gate passed; checked "
SARIF_HINTS = (
    "Code scanning results successfully uploaded",
    "Successfully uploaded SARIF",
    "Uploading SARIF results",
    "Waiting for processing to complete",
    "SARIF upload",
    "processing is complete",
    "Analysis uploaded",
)
assert os.environ.get("GH_CONFIG_DIR") == PROFILE
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR=PROFILE, GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)
path = HERE / "scheduled-20261117-authentication.json"
assert not path.exists(), "Preserve previous authentication; inspect before resuming"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "profile": PROFILE,
          "manual_dispatch_or_rerun": False, "credential_switch": False,
          "result": "pending", "errors": [], "criteria": {}}


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def note(error):
    text = str(error)[:2000]
    report["errors"].append({"observed_at": now(), "error": text})
    save()


def git(*arguments, cwd=ROOT):
    value = subprocess.run(["git", *arguments], cwd=cwd, env=environment,
                           capture_output=True, timeout=60)
    if value.returncode:
        raise RuntimeError(value.stderr.decode()[:1000] or value.stdout.decode()[:1000])
    return value.stdout.decode().strip()


def gh(endpoint, *, include=True, timeout=120):
    command = ["gh", "api", "--method", "GET", endpoint]
    if include:
        command.insert(2, "--include")
    value = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=timeout)
    stdout = value.stdout
    if include:
        text = stdout.decode()
        parts = re.split(r"\r?\n\r?\n", text, maxsplit=1)
        header = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        status = header.splitlines()[0] if header else ""
        headers = {}
        for line in header.splitlines()[1:]:
            if ":" not in line:
                continue
            key, text_value = line.split(":", 1)
            if key.lower() in {
                "x-github-request-id", "x-accepted-github-permissions", "retry-after",
                "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset",
                "content-type", "location"}:
                headers[key.lower()] = text_value.strip()
        try:
            parsed = json.loads(body) if body.strip() else None
        except json.JSONDecodeError:
            parsed = {"unparsed": True, "body_prefix": body[:240]}
        if value.returncode:
            message = parsed.get("message", "unreadable response") if isinstance(parsed, dict) else "invalid response"
            raise RuntimeError(json.dumps({
                "endpoint": endpoint, "status": status, "headers": headers,
                "message": re.sub(r"https?://[^\s]+", "[URL omitted]", str(message))[:240]}))
        return parsed, {"status": status, "headers": headers}
    if value.returncode:
        raise RuntimeError(endpoint + " failed: " + value.stderr.decode()[:500])
    return stdout, {}


def gh_file(endpoint, destination, timeout=180):
    with destination.open("wb") as stream:
        value = subprocess.run(["gh", "api", "--method", "GET", endpoint], cwd=ROOT, env=environment,
                               stdout=stream, stderr=subprocess.PIPE, timeout=timeout)
    if value.returncode:
        raise RuntimeError(endpoint + " failed: " + value.stderr.decode()[:500])
    return destination.stat().st_size


def write_json(name, value):
    target = HERE / name
    target.write_text(json.dumps(value, indent=2) + "\n")
    return str(target)


identity, identity_meta = gh("user")
assert identity["login"] == "jpiquot" and identity["id"] == 6775094
report["authentication_context"] = {
    "GH_CONFIG_DIR": PROFILE, "GH_TOKEN_present": False, "GITHUB_TOKEN_present": False,
    "user": {"id": identity["id"], "login": identity["login"]},
    "identity_headers": identity_meta["headers"]}
save()

inventory, inventory_meta = gh(
    "repos/Hexalith/Hexalith.CiCd/actions/workflows/nightly.yml/runs"
    "?event=schedule&branch=main&created=2026-11-17&per_page=100")
assert inventory["total_count"] <= 100
matches = [run for run in inventory["workflow_runs"]
           if "2026-11-17T02:17:00Z" <= run["created_at"] < "2026-11-18T00:00:00Z"
           and run["event"] == "schedule" and run["head_branch"] == "main"
           and run["path"] == ".github/workflows/nightly.yml"]
assert matches, "no genuine 2026-11-17 scheduled nightly was found"
selected_id = min(matches, key=lambda run: (run["created_at"], run["id"]))["id"]
assert selected_id == OBSERVER_ID, f"independent selection {selected_id} != observer {OBSERVER_ID}"
run, run_meta = gh(f"repos/Hexalith/Hexalith.CiCd/actions/runs/{selected_id}")
assert run["id"] == selected_id and run["event"] == "schedule" and run["head_branch"] == "main"
assert run["path"] == ".github/workflows/nightly.yml" and run["run_attempt"] == 1
source = run["head_sha"]
assert re.fullmatch(r"[0-9a-f]{40}", source)
assert git("merge-base", "--is-ancestor", REQUIRED_FIX, source) == ""
assert git("merge-base", "--is-ancestor", REQUIRED_POLICY, source) == ""
write_json("scheduled-20261117-run.json", run)
report["run"] = {key: run.get(key) for key in (
    "id", "event", "path", "head_branch", "head_sha", "created_at", "updated_at",
    "status", "conclusion", "run_attempt", "html_url", "display_title", "run_number")}
report["run"]["inventory_headers"] = inventory_meta["headers"]
report["run"]["run_headers"] = run_meta["headers"]
report["run"]["later_same_day_schedule_runs"] = [
    item["id"] for item in sorted(matches, key=lambda row: (row["created_at"], row["id"]))[1:]]
report["ancestry"] = {"required_fix": REQUIRED_FIX, "required_policy": REQUIRED_POLICY,
                      "source": source, "fix_ancestor": True, "policy_ancestor": True}
save()

jobs_page, jobs_meta = gh(
    f"repos/Hexalith/Hexalith.CiCd/actions/runs/{selected_id}/attempts/1/jobs?per_page=100")
assert jobs_page["total_count"] <= 100
jobs = jobs_page["jobs"]
write_json("scheduled-20261117-jobs.json", jobs_page)
report["jobs"] = [{"id": job["id"], "name": job["name"], "status": job["status"],
                   "conclusion": job["conclusion"], "started_at": job.get("started_at"),
                   "completed_at": job.get("completed_at"),
                   "steps": [{"name": step["name"], "conclusion": step.get("conclusion"),
                              "number": step.get("number")} for step in job.get("steps") or []]}
                  for job in jobs]
report["jobs_headers"] = jobs_meta["headers"]
save()

artifacts_page, artifacts_meta = gh(
    f"repos/Hexalith/Hexalith.CiCd/actions/runs/{selected_id}/artifacts?per_page=100")
assert artifacts_page["total_count"] <= 100
write_json("scheduled-20261117-artifact-metadata.json", artifacts_page)
report["artifacts"] = [{key: item.get(key) for key in (
    "id", "name", "size_in_bytes", "digest", "expired", "expires_at", "created_at",
    "updated_at", "workflow_run")} for item in artifacts_page["artifacts"]]
report["artifacts_headers"] = artifacts_meta["headers"]
save()

trusted = {}
for relative in ("tools/nightly_runtime.py", "tools/delivery_runtime.py", "tools/scan.py"):
    blob = subprocess.run(["git", "show", f"{source}:{relative}"], cwd=ROOT,
                          capture_output=True, check=True, timeout=30).stdout
    current = (ROOT / relative).read_bytes()
    trusted[relative] = {"source_sha256": hashlib.sha256(blob).hexdigest(),
                         "working_tree_sha256": hashlib.sha256(current).hexdigest(),
                         "working_tree_matches_source": blob == current}
report["trusted_production_parser_source_sha256"] = trusted
save()
sys.path.insert(0, str(ROOT / "tools"))
import nightly_runtime as rt
builds_pin = git("show", f"{source}:builds-version")
builds_sha = git("rev-parse", f"{builds_pin}^{{commit}}", cwd=ROOT / "references/Hexalith.Builds")
outcome_source = subprocess.run(
    ["git", "show", f"{builds_pin}:Github/lib/release_outcome.py"],
    cwd=ROOT / "references/Hexalith.Builds", capture_output=True, check=True, timeout=30).stdout
scratch = Path(os.environ["TMPDIR"]) / "trusted-builds"
scratch.mkdir()
(scratch / "release_outcome.py").write_bytes(outcome_source)
ci_config = subprocess.run(
    ["git", "show", f"{builds_pin}:Github/lib/ci_config.py"],
    cwd=ROOT / "references/Hexalith.Builds", capture_output=True, check=True, timeout=30).stdout
(scratch / "ci_config.py").write_bytes(ci_config)
sys.path.insert(0, str(scratch))
import release_outcome
report["builds_pin"] = {"tag": builds_pin, "sha": builds_sha,
                        "release_outcome_sha256": hashlib.sha256(outcome_source).hexdigest()}
save()

token = subprocess.run(["gh", "auth", "token"], cwd=ROOT, env=environment,
                       capture_output=True, text=True, check=True, timeout=30).stdout.strip()
rt.delivery._SECRETS.append(token)
api = rt.API(rt.Budget(token_epoch=time.time()),
             repositories=(rt.CICD, rt.BUILDS, *PILOTS, "Hexalith.AI.Tools", "Hexalith.Conversations"))
CONTRACT_MEMBERS = {
    "hexalith-nightly-dispatch-1": ("dispatch.json",),
    "hexalith-nightly-wait-1": ("wait.json",),
    "hexalith-nightly-nightly-1": ("nightly.json",),
    "hexalith-nightly-scan-1": ("report.json", "summary.md"),
    "hexalith-nightly-bump-report-1": ("bump.json",),
    "hexalith-nightly-bump-1": ("candidate.json",),
    "hexalith-nightly-bump-push-1": ("bump-push.json",),
    "hexalith-nightly-delivery-wait-1": ("report.json",),
    "hexalith-nightly-keepalive-1": ("keepalive.json",),
}


def artifact_zip(metadata):
    if (not isinstance(metadata, dict) or metadata.get("expired") is not False
            or not isinstance(metadata.get("digest"), str) or not rt.DIGEST.fullmatch(metadata["digest"])
            or type(metadata.get("size_in_bytes")) is not int or not 1 <= metadata["size_in_bytes"] <= rt.MAX_ZIP):
        raise rt.NightlyError("artifact metadata is malformed, expired, or oversized")
    expires = rt.timestamp(metadata.get("expires_at"))
    if expires.timestamp() <= api.budget.clock():
        raise rt.NightlyError("artifact expiry could not be validated")
    origin = metadata.get("workflow_run") or {}
    if (origin.get("id") != selected_id or origin.get("head_sha") != source
            or origin.get("head_branch") != "main"):
        raise rt.NightlyError("artifact is not bound to the selected scheduled run")
    identity_id = rt.positive(metadata.get("id"))
    path_name = f"/repos/Hexalith/Hexalith.CiCd/actions/artifacts/{identity_id}/zip"
    api._path(path_name)
    payload = None
    for attempt in range(3):
        payload, transient, limited = api._artifact_payload(path_name, token)
        if transient is None:
            break
        delay = api._retry_delay(limited, attempt) if limited is not None else attempt + 1
        if attempt == 2 or api.budget.remaining(token=True) < delay + 2:
            raise rt.NightlyError(transient)
        time.sleep(delay)
    if (len(payload) > rt.MAX_ZIP or len(payload) != metadata["size_in_bytes"]
            or "sha256:" + hashlib.sha256(payload).hexdigest() != metadata["digest"]):
        raise rt.NightlyError("artifact ZIP size or digest mismatch")
    return payload


def extract_members(metadata, names):
    payload = artifact_zip(metadata)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = archive.infolist()
        found = {item.filename: item for item in members}
        if set(found) != set(names):
            raise rt.NightlyError("artifact members " + ",".join(sorted(found)) + " != " + ",".join(names))
        documents = {}
        for name in names:
            item = found[name]
            mode = item.external_attr >> 16
            limit = 16 * 1024 * 1024 if name in {"report.json", "summary.md"} else rt.MAX_JSON
            if (item.flag_bits & 1 or item.is_dir() or item.file_size > limit or item.file_size < 1
                    or item.compress_size > rt.MAX_ZIP
                    or item.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                    or (mode and stat.S_IFMT(mode) not in {0, stat.S_IFREG})):
                raise rt.NightlyError("artifact member metadata refused: " + name)
            with archive.open(item) as stream:
                data = stream.read(limit + 1)
            if len(data) != item.file_size:
                raise rt.NightlyError("artifact member size mismatch: " + name)
            documents[name] = data
        return documents


extracted = {}
for artifact in artifacts_page["artifacts"]:
    name = artifact["name"]
    expected = CONTRACT_MEMBERS.get(name)
    if expected is None:
        report.setdefault("unexpected_artifacts", []).append(name)
        continue
    try:
        documents = extract_members(artifact, expected)
        saved = {}
        for member, data in documents.items():
            slug = f"scheduled-20261117-{name}-{member}"
            (HERE / slug).write_bytes(data)
            if member.endswith(".json"):
                parsed = rt.json_read(data) if member != "report.json" else json.loads(data)
                write_json(slug, parsed)
                saved[member] = parsed
            else:
                saved[member] = {"path": slug, "sha256": hashlib.sha256(data).hexdigest(),
                                 "bytes": len(data)}
        extracted[name] = {"id": artifact["id"], "digest": artifact["digest"],
                           "size_in_bytes": artifact["size_in_bytes"], "members": saved}
    except Exception as error:
        note(name + ": " + str(error))
        extracted[name] = {"id": artifact["id"], "error": str(error)[:500]}
report["extracted"] = {name: {key: value[key] for key in value if key != "members"} | (
    {"member_names": list(value.get("members", {}))} if "members" in value else {})
    for name, value in extracted.items()}
save()

nightly = (extracted.get("hexalith-nightly-nightly-1") or {}).get("members", {}).get("nightly.json")
dispatch = (extracted.get("hexalith-nightly-dispatch-1") or {}).get("members", {}).get("dispatch.json")
wait = (extracted.get("hexalith-nightly-wait-1") or {}).get("members", {}).get("wait.json")
scan = (extracted.get("hexalith-nightly-scan-1") or {}).get("members", {}).get("report.json")
bump = (extracted.get("hexalith-nightly-bump-report-1") or {}).get("members", {}).get("bump.json")
keepalive = (extracted.get("hexalith-nightly-keepalive-1") or {}).get("members", {}).get("keepalive.json")
targets = {}
if isinstance(nightly, dict):
    report["nightly_document"] = {
        "schema": nightly.get("schema"), "phase": nightly.get("phase"),
        "result": nightly.get("result"), "errors": nightly.get("errors"),
        "identity": nightly.get("identity"), "builds": nightly.get("builds"),
        "registry": nightly.get("registry")}
    if nightly.get("schema") != rt.SCHEMA:
        note("nightly schema " + str(nightly.get("schema")))
    identity_doc = nightly.get("identity") or {}
    if identity_doc.get("runId") != selected_id or identity_doc.get("source") != source:
        note("nightly identity does not match selected run")
    if identity_doc.get("attempt") != 1:
        note("nightly identity attempt is not 1")
    for item in nightly.get("targets") or []:
        targets[item.get("repository")] = item
save()

pilot_targets = {}
for module in PILOTS:
    item = targets.get(module)
    row = {"present": item is not None}
    if item is None:
        note("registered pilot missing from nightly targets: " + module)
        pilot_targets[module] = row
        continue
    row.update({key: item.get(key) for key in (
        "eligibility", "dispatch", "deliveredSha", "dispatchHead", "runId", "runAttempt",
        "status", "conclusion", "outcome", "outcomeError", "publication", "reason",
        "verdict", "workflow", "link")})
    try:
        if item.get("runId"):
            remote, remote_meta = gh(f"repos/Hexalith/{module}/actions/runs/{item['runId']}")
            row["remote_run"] = {key: remote.get(key) for key in (
                "id", "event", "path", "head_branch", "head_sha", "status", "conclusion",
                "run_attempt", "html_url", "created_at")}
            row["remote_headers"] = remote_meta["headers"]
            if remote.get("event") != "workflow_dispatch":
                note(module + " correlated run event is " + str(remote.get("event")))
            if remote.get("path") != ".github/workflows/release.yml":
                note(module + " correlated run path is " + str(remote.get("path")))
            if remote.get("head_branch") != "main":
                note(module + " correlated run branch is " + str(remote.get("head_branch")))
            if remote.get("run_attempt") != 1:
                note(module + " correlated run attempt is " + str(remote.get("run_attempt")))
            artifacts, _ = gh(f"repos/Hexalith/{module}/actions/runs/{item['runId']}/artifacts?per_page=100")
            matches = [value for value in artifacts.get("artifacts") or []
                       if value.get("name") == "hexalith-release-outcome"]
            row["outcome_artifact_count"] = len(matches)
            if len(matches) == 1:
                metadata = matches[0]
                producer = metadata.get("workflow_run") or {}
                if (metadata.get("expired") is not False and producer.get("id") == item["runId"]
                        and producer.get("head_sha") == item.get("dispatchHead")):
                    document = api.artifact_member(module, metadata, "outcome.json", token)
                    validated = release_outcome.validate_outcome(document)
                    write_json(f"scheduled-20261117-{module}-outcome.json", validated)
                    row["validated_outcome"] = validated
                    row["outcome_artifact"] = {key: metadata.get(key) for key in (
                        "id", "name", "digest", "size_in_bytes", "expired", "expires_at")}
                else:
                    note(module + " outcome artifact identity/expiry mismatch")
            jobs_doc, _ = gh(
                f"repos/Hexalith/{module}/actions/runs/{item['runId']}/attempts/"
                f"{remote.get('run_attempt') or 1}/jobs?per_page=100")
            codeql_jobs = [job for job in jobs_doc.get("jobs") or [] if "CodeQL" in (job.get("name") or "")]
            row["codeql_jobs"] = []
            for job in codeql_jobs:
                proof = {
                    "id": job["id"], "name": job["name"], "conclusion": job.get("conclusion"),
                    "status": job.get("status"),
                    "steps": [{"name": step.get("name"), "conclusion": step.get("conclusion")}
                              for step in job.get("steps") or []]}
                log_path = Path(os.environ["TMPDIR"]) / f"codeql-{module}-{job['id']}.zip"
                try:
                    gh_file(f"repos/Hexalith/{module}/actions/jobs/{job['id']}/logs", log_path)
                    hints, gate = [], []
                    with zipfile.ZipFile(log_path) as archive:
                        for info in archive.infolist():
                            if info.file_size > 8 * 1024 * 1024:
                                continue
                            text = archive.read(info).decode("utf-8", "replace")
                            if any(hint.lower() in text.lower() for hint in SARIF_HINTS) or CODEQL_GATE in text:
                                excerpt = [line for line in text.splitlines()
                                           if any(hint.lower() in line.lower() for hint in SARIF_HINTS)
                                           or CODEQL_GATE in line
                                           or "SARIF" in line or "processing" in line.lower()]
                                saved_log = HERE / f"scheduled-20261117-{module}-codeql-{job['id']}-{Path(info.filename).name}"
                                saved_log.write_text("\n".join(excerpt[:80]) + "\n")
                                hints.extend(excerpt[:40])
                                gate.extend(line for line in excerpt if CODEQL_GATE in line)
                    proof["log_hints"] = hints[:40]
                    proof["security_gate_lines"] = gate[:10]
                    proof["upload_or_processing_evidence"] = bool(hints)
                    proof["processed_findings_gate"] = bool(gate) and job.get("conclusion") == "success"
                except Exception as error:
                    proof["log_error"] = str(error)[:500]
                    note(module + " CodeQL logs: " + str(error))
                row["codeql_jobs"].append(proof)
            write_json(f"scheduled-20261117-{module}-release-jobs.json", jobs_doc)
    except Exception as error:
        row["error"] = str(error)[:800]
        note(module + ": " + str(error))
    pilot_targets[module] = row
report["pilots"] = pilot_targets
save()

builds_target = targets.get("Hexalith.Builds")
if builds_target:
    row = {key: builds_target.get(key) for key in (
        "eligibility", "dispatch", "dispatchHead", "runId", "status", "conclusion",
        "outcome", "outcomeError", "publication", "reason", "verdict", "workflow", "link")}
    try:
        if builds_target.get("runId"):
            remote, _ = gh(f"repos/Hexalith/Hexalith.Builds/actions/runs/{builds_target['runId']}")
            row["remote_run"] = {key: remote.get(key) for key in (
                "id", "event", "path", "head_branch", "head_sha", "status", "conclusion",
                "run_attempt", "html_url")}
            artifacts, _ = gh(
                f"repos/Hexalith/Hexalith.Builds/actions/runs/{builds_target['runId']}/artifacts?per_page=100")
            matches = [value for value in artifacts.get("artifacts") or []
                       if value.get("name") == "hexalith-release-outcome"]
            if len(matches) == 1:
                document = api.artifact_member("Hexalith.Builds", matches[0], "outcome.json", token)
                row["validated_outcome"] = release_outcome.validate_outcome(document)
                write_json("scheduled-20261117-Hexalith.Builds-outcome.json", row["validated_outcome"])
    except Exception as error:
        row["error"] = str(error)[:800]
        note("Builds: " + str(error))
    report["builds_target"] = row
else:
    note("Builds target missing from nightly document")
    report["builds_target"] = None
save()

scan_row = {"present": isinstance(scan, dict)}
if isinstance(scan, dict):
    scan_row.update({"schema": scan.get("schema"), "result": scan.get("result"),
                     "errors": scan.get("errors"), "findings": scan.get("findings"),
                     "detector": scan.get("detector"), "controllerRevision": scan.get("controllerRevision")})
    modules = {item.get("module"): item for item in scan.get("modules") or [] if isinstance(item, dict)}
    scan_row["modules"] = {}
    for module in PILOTS:
        item = modules.get(module)
        scan_row["modules"][module] = item
        if item is None:
            note("scan did not include pilot " + module)
        elif item.get("result") != "pass":
            note("scan pilot result is not pass: " + module)
        elif not re.fullmatch(r"[0-9a-f]{40}", str(item.get("revision") or "")):
            note("scan pilot revision missing: " + module)
    extra = sorted(name for name in modules if name not in PILOTS)
    scan_row["other_modules"] = extra
    scan_row["unresolved_findings"] = bool(scan.get("findings"))
    scan_row["covers_both_pilots"] = all(modules.get(name) for name in PILOTS)
report["scan"] = scan_row
save()

bump_row = {"present": isinstance(bump, dict)}
if isinstance(bump, dict):
    bump_row.update(bump)
    if bump.get("schema") != "hexalith.nightly-bump-report.v1":
        note("bump schema mismatch")
    identity_doc = bump.get("identity") or {}
    if identity_doc.get("runId") != selected_id or identity_doc.get("night") != "2026-11-17":
        note("bump identity does not match selected UTC night")
report["bump"] = bump_row
save()

keepalive_row = {"present": isinstance(keepalive, dict)}
if isinstance(keepalive, dict):
    keepalive_row.update({key: keepalive.get(key) for key in (
        "schema", "result", "enabled", "errors", "commit", "ageSeconds")})
report["keepalive"] = keepalive_row
save()

inventory_refusals = []
for module in PILOTS:
    try:
        gh(f"repos/Hexalith/{module}/code-scanning/analyses?ref=refs/heads/main&per_page=100")
        inventory_refusals.append({"repository": module, "unexpected": "read succeeded; not inferred previously"})
    except RuntimeError as error:
        inventory_refusals.append(json.loads(str(error)))
write_json("scheduled-20261117-codeql-inventory.json", inventory_refusals)
report["direct_codeql_inventory"] = inventory_refusals
save()

immutable = {}
for module in PILOTS:
    try:
        value, meta = gh(f"repos/Hexalith/{module}/immutable-releases")
        immutable[module] = {"value": value, "headers": meta["headers"]}
    except Exception as error:
        immutable[module] = {"error": str(error)[:500]}
        note(module + " immutable-releases: " + str(error))
report["immutable_releases"] = immutable
save()

diagnostic, diagnostic_meta = gh(f"repos/Hexalith/Hexalith.CiCd/actions/runs/{DIAGNOSTIC_DELIVERY}")
diag = {key: diagnostic.get(key) for key in (
    "id", "event", "path", "head_branch", "head_sha", "status", "conclusion",
    "run_attempt", "html_url", "created_at", "updated_at")}
diag["headers"] = diagnostic_meta["headers"]
if diagnostic.get("conclusion") == "success" and diagnostic.get("path") == ".github/workflows/deliver.yml":
    artifacts, _ = gh(
        f"repos/Hexalith/Hexalith.CiCd/actions/runs/{DIAGNOSTIC_DELIVERY}/artifacts?per_page=100")
    matches = [item for item in artifacts.get("artifacts") or [] if item.get("name") == "hexalith-delivery"]
    diag["delivery_artifact_count"] = len(matches)
    if len(matches) == 1:
        try:
            document = api.artifact_member("Hexalith.CiCd", matches[0], "delivery.json", token)
            write_json("scheduled-20261117-diagnostic-delivery-report.json", document)
            diag["artifact"] = {key: matches[0].get(key) for key in (
                "id", "name", "digest", "size_in_bytes", "expired", "expires_at")}
            diag["tools_source_sha"] = document.get("tools_source_sha")
            diag["modules"] = document.get("modules")
        except Exception as error:
            diag["artifact_error"] = str(error)[:500]
            note("diagnostic delivery artifact: " + str(error))
write_json("scheduled-20261117-diagnostic-delivery.json", diag)
report["diagnostic_delivery"] = diag
save()

hourly, hourly_meta = gh(
    "repos/Hexalith/Hexalith.CiCd/actions/workflows/deliver.yml/runs"
    "?branch=main&event=schedule&per_page=20")
hourly_rows = []
for item in hourly.get("workflow_runs") or []:
    if item.get("created_at", "") >= run["created_at"]:
        hourly_rows.append({key: item.get(key) for key in (
            "id", "event", "path", "head_sha", "status", "conclusion", "run_attempt",
            "html_url", "created_at")})
write_json("scheduled-20261117-hourly-delivery.json",
           {"headers": hourly_meta["headers"], "runs": hourly_rows[:10]})
report["hourly_delivery_after_night"] = hourly_rows[:10]
save()

failed_jobs = [job for job in jobs if job.get("conclusion") not in {None, "success", "skipped"}]
report["failed_parent_jobs"] = [job["name"] for job in failed_jobs]
for job in failed_jobs:
    log_path = Path(os.environ["TMPDIR"]) / f"parent-{job['id']}.zip"
    try:
        gh_file(f"repos/Hexalith/Hexalith.CiCd/actions/jobs/{job['id']}/logs", log_path)
        excerpts = []
        with zipfile.ZipFile(log_path) as archive:
            for info in archive.infolist():
                if info.file_size > 4 * 1024 * 1024:
                    continue
                text = archive.read(info).decode("utf-8", "replace")
                lines = [line for line in text.splitlines()
                         if any(token in line.lower() for token in (
                             "error", "fail", "denied", "403", "404", "refused", "verdict",
                             "eligibility", "outcome", "codeql", "scan"))
                         and "debug" not in line.lower()]
                if lines:
                    excerpts.append({"member": info.filename, "lines": lines[-60:]})
        write_json(f"scheduled-20261117-failed-job-{job['id']}.json",
                   {"id": job["id"], "name": job["name"], "conclusion": job.get("conclusion"),
                    "excerpts": excerpts[:8]})
    except Exception as error:
        note("parent job log " + job["name"] + ": " + str(error))

sibling_targets = {name: {key: item.get(key) for key in (
    "eligibility", "dispatch", "verdict", "reason", "runId", "conclusion", "outcome")}
    for name, item in targets.items() if name not in PILOTS and name != "Hexalith.Builds"}
report["sibling_targets"] = sibling_targets

criteria = {
    "genuine_schedule_event": run["event"] == "schedule" and run["created_at"] >= "2026-11-17T02:17:00Z",
    "attempt_1": run["run_attempt"] == 1,
    "source_descends_from_fix_and_policy": True,
    "parent_conclusion": run.get("conclusion"),
    "both_pilots_present": all(pilot_targets[name].get("present") for name in PILOTS),
    "both_pilot_outcomes_validated": all(
        isinstance((pilot_targets[name].get("validated_outcome") or {}).get("outcome"), str)
        for name in PILOTS),
    "both_pilot_codeql_jobs_success": all(
        bool(pilot_targets[name].get("codeql_jobs"))
        and all(job.get("conclusion") == "success" for job in pilot_targets[name].get("codeql_jobs") or [])
        for name in PILOTS),
    "both_pilot_codeql_gate_proved": all(
        any(job.get("processed_findings_gate") for job in pilot_targets[name].get("codeql_jobs") or [])
        for name in PILOTS),
    "scan_covers_both_pilots": bool(scan_row.get("covers_both_pilots")),
    "scan_result": scan_row.get("result"),
    "builds_outcome_validated": isinstance((report.get("builds_target") or {}).get("validated_outcome"), dict),
    "bump_present": bump_row.get("present"),
    "bump_result": bump_row.get("result"),
    "keepalive_result": keepalive_row.get("result"),
    "direct_codeql_inventory": "unverified" if any(
        "403" in json.dumps(item) for item in inventory_refusals) else "see inventory file",
    "no_later_run_substituted": not report["run"]["later_same_day_schedule_runs"],
}
report["criteria"] = criteria
blocking = []
if run.get("conclusion") != "success":
    blocking.append("scheduled parent conclusion is " + str(run.get("conclusion")))
if not criteria["both_pilot_outcomes_validated"]:
    blocking.append("pilot publication outcomes are incomplete")
if not criteria["both_pilot_codeql_gate_proved"]:
    blocking.append("CodeQL processed-findings gate is unproved")
if scan_row.get("result") != "pass" or not scan_row.get("covers_both_pilots"):
    blocking.append("duplicate scan did not pass covering both pilots")
if not criteria["builds_outcome_validated"]:
    blocking.append("Builds publication outcome is unvalidated")
if bump_row.get("result") not in {"no-change", "candidate"}:
    blocking.append("Builds bump report is not an accepted no-change or candidate")
if keepalive_row.get("result") != "pass":
    blocking.append("keepalive did not pass")
report["blocking"] = blocking
report["result"] = "pass" if not blocking and not report["errors"] else "failed-or-incomplete"
report["acceptance"] = "not accepted" if blocking or report["errors"] else "criteria satisfied pending spec/review close"
report["completed_at"] = now()
save()
print(json.dumps({"result": report["result"], "run": selected_id, "conclusion": run.get("conclusion"),
                  "blocking": blocking, "errors": len(report["errors"])}, indent=2))
raise SystemExit(0 if report["result"] == "pass" else 1)
