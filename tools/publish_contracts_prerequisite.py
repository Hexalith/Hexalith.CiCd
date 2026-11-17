"""Publish only the two owner-approved, immutable prerequisite archives.

This program never packs or executes module source. Full application releases
continue through their existing jobs. Network and process boundaries are
replaceable only by Python callers in offline tests, never by dispatch inputs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import zipfile

FIXED = {
    "eventstore": ("Hexalith/Hexalith.EventStore", "Hexalith.EventStore.Contracts", "5.3.0",
                   "0be0c922883d4ea61b18e843e24472162261d934",
                   "1c3bdabc4778467d74b468a47f0413f5f85272539d9969891036c8865f6949c3"),
    "projects": ("Hexalith/Hexalith.Projects", "Hexalith.Projects.Contracts", "2.0.0-story66.3",
                 "5b4bdeacde318a1d948db7ef76843df0c548f084",
                 "349f938db77dd83ff45e200997b1cba97147c46b1855ec58fd6e2a4b0572eff5"),
}
FEED = "https://api.nuget.org/v3/index.json"
LIMIT = 2 * 1024 * 1024


def require(test, message):
    if not test:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(data):
    require(len(data) <= 2 * LIMIT, "JSON size limit")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs)


def payload(data, expected, signed=False):
    require(len(data) <= LIMIT, "package size limit")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate ZIP entry")
        require(set(names) == set(expected) | ({".signature.p7s"} if signed else set()),
                "package entry set differs from approved payload")
        for item in archive.infolist():
            require(item.file_size <= LIMIT, "ZIP entry size limit")
        require(sum(i.file_size for i in archive.infolist()) <= 8 * LIMIT, "ZIP expansion limit")
        for name, value in expected.items():
            require(digest(archive.read(name)) == value, "package payload differs: " + name)
        if signed:
            require(len(archive.read(".signature.p7s")) > 0, "empty repository signature")


def qualification(root, profile):
    directory = root / "docs/contracts-prerequisites"
    value = load((directory / "manifest.json").read_bytes())
    require(value["schema"] == "hexalith.fixed-contracts-prerequisites.v1", "manifest schema")
    require(set(value["packages"]) == set(FIXED), "fixed package set differs")
    package = value["packages"][profile]
    require(tuple(package[k] for k in ("repository", "id", "version", "source", "sha256")) == FIXED[profile],
            "unapproved coordinate/source/archive")
    require(package["archive"] == package["id"] + "." + package["version"] + ".nupkg", "archive path")
    path = directory / package["archive"]
    require(path.is_file() and not path.is_symlink(), "archive must be a regular file")
    data = path.read_bytes()
    require(digest(data) == package["sha256"], "approved archive hash differs")
    payload(data, package["entries"])
    required = {"approval.json", "eventstore-tests.json", "eventstore-api.json.gz", "projects-tests.json",
                "mcp.json", "mcp-discovery.json", "projects-source.json", "projects-payload.json", "approver.json",
                "eventstore-access.json", "projects-access.json"}
    require(set(value["proof_sha256"]) == required, "required qualification proof set differs")
    proofs = {}
    for name, expected in value["proof_sha256"].items():
        data = (directory / name).read_bytes()
        require(digest(data) == expected, "qualification proof bytes differ: " + name)
        if name == "eventstore-api.json.gz":
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                data = stream.read(2 * LIMIT + 1)
            require(digest(data) == value["api_uncompressed_receipt_sha256"], "original API receipt hash differs")
        proofs[name.removesuffix(".gz")] = load(data)
    approval = proofs["approval.json"]
    require(approval["status"] == "approved" and approval["user_response"] == "*yes", "approval absent")
    require({(p["id"], p["version"], p["source"], p["archive_sha256"]) for p in approval["coordinates"]} ==
            {(v[1], v[2], v[3], v[4]) for v in FIXED.values()}, "approval package scope differs")
    tests = proofs["eventstore-tests.json"]
    require(tests["source"] == FIXED["eventstore"][3], "producer source differs")
    counts = tests["full_contracts_tests"]
    require(counts["total"] == counts["passed"] == 1704 and
            all(counts[k] == 0 for k in ("failed", "skipped", "errors", "not-run")), "producer suite did not pass")
    api = proofs["eventstore-api.json"]
    require(api["status"] == "pass" and api["candidateSource"] == FIXED["eventstore"][3] and
            len(api["packages"]) == 14, "14-family API gate did not pass")
    consumer = proofs["projects-tests.json"]
    require(consumer["focusedContractsPassed"] is True and consumer["restoredCandidateSha256"] == FIXED["eventstore"][4],
            "exact archive consumer did not pass")
    runs = [c for c in consumer["commands"] if c["label"] == "candidate-contract-tests-run"]
    require(len(runs) == 1 and runs[0]["exitCode"] == 0 and runs[0]["tests"]["total"] == 207 and
            all(runs[0]["tests"][k] == 0 for k in ("errors", "failed", "skipped", "notRun")), "207 consumer cases required")
    mcp = proofs["mcp.json"]
    require(mcp["candidateSha256"] == FIXED["projects"][4] and mcp["allRequestedCommandsPassed"] is True and
            mcp["sources"]["Hexalith.McpCli"]["revision"] == "5008de388c5e37257ca78e48d8afe899cf7aaa2a" and
            len(mcp["commands"]) == 3 and all(c["exitCode"] == 0 for c in mcp["commands"]), "pinned Mcp proof required")
    discovery = proofs["mcp-discovery.json"]
    require(discovery["module"] == "projects" and
            {item["name"] for item in discovery["operations"]} == {
                "projects.describe", "projects.list", "projects.trace-attachments", "projects.trace-conversation"} and
            len(discovery["operations"]) == 4 and all(item["kind"] == "read" for item in discovery["operations"]),
            "four strict Projects operation identities required")
    require(digest((directory / "mcp-discovery.json").read_bytes()) == mcp["commands"][2]["logSha256"],
            "strict discovery output differs from executed command")
    source = proofs["projects-source.json"]
    require(source["claimedRevision"] == FIXED["projects"][3] and source["matches"] ==
            source["contractAndBuildFilesChecked"] == 119 and source["mismatches"] == [], "119-file provenance required")
    equivalent = proofs["projects-payload.json"]
    require(equivalent["retainedArchiveSha256"] == FIXED["projects"][4] and
            all(equivalent[k] is True for k in ("identicalClrMetadataAndMethodBodies", "nuspecIdentical", "readmeIdentical")),
            "historical archive equivalence required")
    approver = proofs["approver.json"]
    require(approver["authenticatedGitHubUser"]["login"] == "jpiquot" and
            approver["authenticatedGitHubUser"]["id"] == 6775094 and
            approver["organizationMembership"] == {"state": "active", "role": "admin"}, "named approver capacity required")
    for name in FIXED:
        access = proofs[name + "-access.json"]
        require(access["status"] == "qualified" and access["repository"] == FIXED[name][0] and
                access["installation_id"] == "179966090" and access["app_slug"] == "hexalith-cicd", "owner App proof required")
    return package, path, digest((directory / "manifest.json").read_bytes())


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("HTTP redirect refused")


def get(url, token="", absent=False):
    require(url.startswith(("https://api.nuget.org/v3-flatcontainer/", "https://api.github.com/repos/Hexalith/")),
            "unapproved HTTP origin")
    headers = {"User-Agent": "Hexalith-fixed-contracts-prerequisite"}
    if token:
        require(url.startswith("https://api.github.com/"), "credential origin mismatch")
        headers["Authorization"] = "Bearer " + token
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(Request(url, headers=headers), timeout=30) as response:
            require(response.status == 200, "unexpected HTTP status")
            data = response.read(LIMIT + 1)
            require(len(data) <= LIMIT, "HTTP body size limit")
            return data
    except HTTPError as error:
        error.close()
        if error.code == 404 and absent:
            return None
        raise ValueError("HTTP status " + str(error.code)) from None


def command(args, *, key="", environment=None, timeout=180):
    env = (environment or os.environ).copy()
    for name in ("NUGET_API_KEY", "GH_TOKEN", "GITHUB_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        env.pop(name, None)
    if key:
        env["NUGET_API_KEY"] = key
    # Never print command arguments: an upload's temporary credential is an argument.
    with tempfile.TemporaryFile() as out:
        try:
            process = subprocess.run(args, stdout=out, stderr=subprocess.STDOUT, env=env, timeout=timeout)
            code = process.returncode
        except subprocess.TimeoutExpired:
            code = 124
        except OSError:
            code = 127
        out.seek(0)
        data = out.read(LIMIT + 1).decode("utf-8", "replace")
    require(len(data) <= LIMIT, "command output limit")
    if key:
        data = data.replace(key, "[redacted]")
    return code, data


def authorize(context, profile, root, *, fetch=get, run=command, publishing=True):
    repository = FIXED[profile][0]
    require(context.get("GITHUB_REPOSITORY") == repository and context.get("GITHUB_REF") == "refs/heads/main" and
            context.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and
            context.get("GITHUB_WORKFLOW_REF") == repository + "/.github/workflows/release.yml@refs/heads/main",
            "ineligible owner release invocation")
    revision = context.get("GITHUB_SHA", "")
    owner = context.get("PREREQUISITE_OWNER_SOURCE", "")
    require(re.fullmatch("[0-9a-f]{40}", revision) and re.fullmatch("[0-9a-f]{40}", owner), "exact source required")
    code, head = run(["git", "-C", str(root), "rev-parse", "HEAD"])
    require(code == 0 and head.strip() == owner, "executing CiCd source differs")
    live = load(fetch("https://api.github.com/repos/" + repository + "/git/ref/heads/main", context.get("GH_TOKEN", "")))
    require(live["object"]["type"] == "commit" and live["object"]["sha"] == revision, "owner release main advanced")
    if publishing:
        require(context.get("HEXALITH_RELEASE_PUBLISH_ENABLED") == "true", "publication is frozen")
    return {"repository": repository, "dispatch_source": revision, "owner_source": owner}


def persist(report, receipt):
    """Checkpoint side-effect intent before external upload; replace atomically."""
    report.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".prerequisite-", dir=report.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, report)
    finally:
        Path(temporary).unlink(missing_ok=True)


def execute(operation, profile, root, report, context, *, fetch=get, run=command, pause=time.sleep):
    receipt = {"schema": "hexalith.fixed-contracts-publication.v1", "status": "failed", "operation": operation,
               "profile": profile, "push_attempted": False, "upload_count": 0,
               "run_url": "https://github.com/" + context.get("GITHUB_REPOSITORY", "") + "/actions/runs/" + context.get("GITHUB_RUN_ID", ""),
               "run_attempt": context.get("GITHUB_RUN_ATTEMPT"), "observed_at": datetime.now(timezone.utc).isoformat(),
               "failed_operation": "qualification", "reason": None}
    try:
        require(profile in FIXED and operation in {"qualify", "publish", "verify"}, "closed operation/profile required")
        package, path, manifest = qualification(root, profile)
        receipt.update(package_id=package["id"], version=package["version"], producer_source=package["source"],
                       archive_sha256=package["sha256"], manifest_sha256=manifest)
        receipt["failed_operation"] = "authorize exact source"
        binding = authorize(context, profile, root, fetch=fetch, run=run, publishing=operation != "verify")
        receipt.update(binding)
        url = ("https://api.nuget.org/v3-flatcontainer/" + package["id"].lower() + "/" + package["version"] + "/" +
               package["archive"].lower())
        receipt["failed_operation"] = "read approved coordinate"
        public = fetch(url, absent=True)
        plan = dict(binding, manifest_sha256=manifest, archive_sha256=package["sha256"])
        receipt["plan"] = plan
        if operation == "qualify":
            if public is not None:
                payload(public, package["entries"], signed=True)
            receipt["status"] = "qualified"
            return receipt
        if operation == "publish":
            require(context.get("PREREQUISITE_QUALIFICATION") == "success" and
                    load(context.get("PREREQUISITE_PLAN", "")) == plan, "qualified plan differs or qualification failed")
            if public is None:
                require(context.get("NUGET_API_KEY"), "temporary OIDC NuGet key unavailable")
                receipt["failed_operation"] = "revalidate before single upload"
                authorize(context, profile, root, fetch=fetch, run=run)
                require(fetch(url, absent=True) is None, "coordinate became occupied; require a fresh verification run")
                require(digest(path.read_bytes()) == package["sha256"], "archive changed before upload")
                receipt.update(push_attempted=True, upload_count=1)
                receipt["failed_operation"] = "upload exact archive once"
                persist(report, receipt)
                key = context["NUGET_API_KEY"]
                code, output = run(["dotnet", "nuget", "push", str(path), "--source", FEED,
                                    "--api-key", key, "--no-symbols", "--timeout", "120"], key=key)
                receipt["upload_exit_code"] = code
                receipt["upload_output"] = output.replace(key, "[redacted]")[:4000]
                # An error may have committed remotely. Observe; never retry an upload.
                for attempt in range(12):
                    try:
                        public = fetch(url, absent=True)
                    except Exception as error:
                        receipt.setdefault("observation_errors", []).append({"attempt": attempt + 1,
                            "type": type(error).__name__, "reason": str(error)[:1000]})
                        public = None
                    if public is not None:
                        break
                    if attempt < 11:
                        pause(10)
                require(public is not None, "archive not public; retain ambiguous upload and verify without reupload")
        require(public is not None, "coordinate is not published")
        receipt["failed_operation"] = "verify signed public payload"
        payload(public, package["entries"], signed=True)
        with tempfile.TemporaryDirectory(prefix="prerequisite-public-") as temporary:
            signed = Path(temporary) / package["archive"]
            signed.write_bytes(public)
            code, output = run(["dotnet", "nuget", "verify", str(signed), "--all", "--verbosity", "normal"])
            receipt["signature_output"] = output[:8000]
            require(code == 0 and "Signature type: Repository" in output and "https://api.nuget.org/v3/index.json" in output,
                    "nuget.org repository signature verification required")
        receipt.update(status="published-verified", public_archive_sha256=digest(public), payload_entries_verified=True)
    except Exception as error:
        message = str(error)
        for name in ("NUGET_API_KEY", "GH_TOKEN"):
            secret = context.get(name, "")
            if secret:
                message = message.replace(secret, "[redacted]")
        receipt["reason"] = message[:2000]
    finally:
        if receipt["status"] != "failed":
            receipt["failed_operation"] = None
        persist(report, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("qualify", "publish", "verify"))
    parser.add_argument("--profile", required=True, choices=tuple(FIXED))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = execute(args.operation, args.profile, Path(__file__).resolve().parents[1], args.report, dict(os.environ))
    if result["status"] == "qualified" and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            stream.write("plan=" + json.dumps(result["plan"], separators=(",", ":")) + "\n")
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
