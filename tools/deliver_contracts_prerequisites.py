"""Deliver three fixed, reviewed contracts prerequisites without executing target code.

Only a transport supplied at the Python invocation boundary is replaceable for
offline real-Git tests. No environment or proposal can supply remotes or paths.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

_SPEC = importlib.util.spec_from_file_location("_contracts_delivery_runtime", Path(__file__).with_name("delivery_runtime.py"))
rt = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = rt
_SPEC.loader.exec_module(rt)

PROFILES = ("eventstore-publisher", "projects-publisher", "projects-pins", "projects-prerequisite-policy")
WORKFLOW = ".github/workflows/deliver-contracts-prerequisites.yml"
CHECKS = frozenset({"scope-preservation", "behavioral-controls", "actionlint", "package-qualification"})
SCHEMA = "hexalith.contracts-prerequisites.v1"
VALIDATION_SCHEMA = "hexalith.contracts-prerequisites-validation.v1"
PLAN_SCHEMA = "hexalith.contracts-prerequisites-plan.v1"
RECEIPT_SCHEMA = "hexalith.contracts-prerequisites-delivery.v1"
# Copy of the approved publisher FIXED coordinates; never load publisher/module
# code in this credentialed controller. The public archives carry NuGet's added
# repository signature, so their signed hashes are bound by committed receipts.
PUBLICATIONS = (
    ("Hexalith.EventStore.Contracts", "5.3.0", "0be0c922883d4ea61b18e843e24472162261d934",
     "1c3bdabc4778467d74b468a47f0413f5f85272539d9969891036c8865f6949c3"),
    ("Hexalith.Projects.Contracts", "2.0.0-story66.3", "5b4bdeacde318a1d948db7ef76843df0c548f084",
     "349f938db77dd83ff45e200997b1cba97147c46b1855ec58fd6e2a4b0572eff5"),
)


def public_url(fixed):
    package, version = fixed[:2]
    return "https://api.nuget.org/v3-flatcontainer/" + package.lower() + "/" + version + "/" + package.lower() + "." + version + ".nupkg"


def fetch_public(url):
    """Secret-free fixed-origin GET, without redirects, proxies or subprocesses."""
    require(url in {public_url(fixed) for fixed in PUBLICATIONS}, "unexpected public prerequisite URL")
    try:
        request = Request(url, headers={"User-Agent": "Hexalith-CiCd-contracts-prerequisites"})
        with build_opener(ProxyHandler({}), rt.NoRedirect()).open(request, timeout=30) as response:
            require(response.status == 200, "public prerequisite returned an unexpected HTTP status")
            data = response.read(rt.MAX_JSON + 1)
            require(len(data) <= rt.MAX_JSON, "public prerequisite body exceeds 2 MiB limit")
            return data
    except HTTPError as error:
        error.close()
        raise rt.DeliveryError("public prerequisite unavailable: HTTP " + str(error.code)) from None
    except (URLError, OSError, rt.http.client.HTTPException):
        raise rt.DeliveryError("public prerequisite transport unavailable") from None


def require(condition, message):
    if not condition:
        raise rt.DeliveryError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def configuration(profile):
    """The complete closed perimeter; callers choose only a fixed profile."""
    require(profile in PROFILES, "unknown closed contracts prerequisite profile")
    prefix = "docs/proposals/contracts-prerequisites/" + profile
    manifest_path, patch_path, validation_path = prefix + ".json", prefix + ".patch", prefix + "-validation.json"
    logs = {check: prefix + "-" + check + ".log" for check in sorted(CHECKS)}
    return {"repository": "Hexalith.EventStore" if profile == "eventstore-publisher" else "Hexalith.Projects",
            "paths": ("Directory.Packages.props", "tools/release-packages.json") if profile == "projects-pins"
                     else ("tests/tools/run-ci-workflow-gates.ps1", "tests/tools/test_run_ci_workflow_gates.py")
                     if profile == "projects-prerequisite-policy" else (".github/workflows/release.yml",),
            "manifest": manifest_path, "patch": patch_path, "validation": validation_path, "logs": logs,
            "sources": ("tools/deliver_contracts_prerequisites.py", "tools/delivery_runtime.py", WORKFLOW,
                        "tools/tests/test_deliver_contracts_prerequisites.py", manifest_path, patch_path, validation_path,
                        *logs.values()),
            "message": ("build(cicd): deliver approved contracts prerequisite " + profile + "\n").encode()}


def sha256(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "invalid SHA256 identity")
    return value


def manifest(data, profile):
    config = configuration(profile)
    value = rt.json_read(data)
    require(isinstance(value, dict) and set(value) == {
        "schema", "repository", "base_commit", "base_tree", "result_tree", "patch_sha256",
        "before", "after", "validation_sha256", "pre_push_gate"}, "invalid closed prerequisite manifest")
    require(value["schema"] == SCHEMA and value["repository"] == config["repository"],
            "prerequisite repository/schema mismatch")
    require(value["pre_push_gate"] == "reviewed-tree-owner-authorized", "pre-push owner gate is not authorized")
    for field in ("base_commit", "base_tree", "result_tree"):
        rt.sha(value[field])
    for field in ("patch_sha256", "validation_sha256"):
        sha256(value[field])
    for field in ("before", "after"):
        require(isinstance(value[field], dict) and set(value[field]) == set(config["paths"]),
                "unexpected prerequisite manifest path")
        for item in value[field].values():
            require(isinstance(item, list) and len(item) == 3 and item[:2] == ["100644", "blob"],
                    "prerequisite requires existing regular 100644 blobs")
            rt.sha(item[2])
    return value


def validation(data, value, logs):
    """Bind passed independent named checks to the exact complete target tree."""
    require(digest(data) == value["validation_sha256"], "reviewed validation SHA256 mismatch")
    proof = rt.json_read(data)
    require(isinstance(proof, dict) and set(proof) == {
        "schema", "status", "base_commit", "base_tree", "result_tree", "patch_sha256", "checks"},
        "invalid closed prerequisite validation proof")
    require(proof["schema"] == VALIDATION_SCHEMA and proof["status"] == "passed", "reviewed validation did not pass")
    for field in ("base_commit", "base_tree", "result_tree", "patch_sha256"):
        require(proof[field] == value[field], "reviewed validation source/proposal mismatch: " + field)
    require(isinstance(proof["checks"], dict) and set(proof["checks"]) == CHECKS,
            "reviewed validation required checks differ")
    for name, check in proof["checks"].items():
        require(isinstance(check, dict) and set(check) == {"status", "log_sha256"}
                and check["status"] == "passed", "reviewed validation check did not pass: " + name)
        sha256(check["log_sha256"])
        require(digest(logs[name]) == check["log_sha256"], "committed validation log SHA256 mismatch: " + name)
    return proof


def public_prerequisites(data, public_fetch):
    """Require both successful publisher receipts and their current public bytes."""
    log = rt.json_read(data)
    require(isinstance(log, dict) and set(log) == {"publications"} and isinstance(log["publications"], list)
            and len(log["publications"]) == len(PUBLICATIONS), "exact two public publication receipts required")
    remaining = list(log["publications"])
    reviewed = []
    for fixed in PUBLICATIONS:
        package, version, source, unsigned = fixed
        matches = [item for item in remaining if isinstance(item, dict) and item.get("package_id") == package]
        require(len(matches) == 1, "missing or duplicate fixed public publication receipt: " + package)
        item = matches[0]
        remaining.remove(item)
        require(item.get("status") == "published-verified" and item.get("version") == version
                and item.get("producer_source") == source and item.get("archive_sha256") == unsigned
                and item.get("payload_entries_verified") is True, "public publication receipt differs from approved prerequisite: " + package)
        signed = sha256(item.get("public_archive_sha256"))
        reviewed.append((fixed, signed))
    require(not remaining, "unexpected public publication receipt")
    observations = []
    for fixed, signed in reviewed:
        public = public_fetch(public_url(fixed))
        require(isinstance(public, bytes) and len(public) <= rt.MAX_JSON,
                "public prerequisite unavailable or exceeds 2 MiB limit: " + fixed[0])
        require(digest(public) == signed, "current public prerequisite archive SHA256 mismatch: " + fixed[0])
        observations.append({"package_id": fixed[0], "version": fixed[1], "producer_source": fixed[2],
                             "archive_sha256": fixed[3], "public_archive_sha256": signed})
    return observations


def entries(git, revision, expected):
    actual = git.items(revision)
    for path, item in expected.items():
        require(actual.get(path) == tuple(item), "unexpected prerequisite blob/mode: " + path)
    return actual


def proposal(owner, source, target, value, config):
    patch = owner.blob(source, config["patch"])
    require(digest(patch) == value["patch_sha256"], "reviewed patch SHA256 mismatch")
    require(target.resolve(value["base_commit"] + "^{tree}") == value["base_tree"], "reviewed base tree mismatch")
    before = entries(target, value["base_commit"], value["before"])
    target.run("read-tree", value["base_tree"])
    target.run("apply", "--cached", "--whitespace=nowarn", data=patch)
    tree = rt.sha(target.run("write-tree", "--missing-ok").decode().strip())
    require(tree == value["result_tree"], "complete prerequisite output tree mismatch")
    after = entries(target, tree, value["after"])
    changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
    require(changed == set(config["paths"]), "patch changed paths outside the exact prerequisite perimeter")
    return tree


def parents(git, revision):
    header = git.run("cat-file", "commit", revision).split(b"\n\n", 1)[0]
    return [line[7:].decode("ascii") for line in header.splitlines() if line.startswith(b"parent ")]


def plan(profile, source, raw, value, live):
    return {"schema": PLAN_SCHEMA, "profile": profile, "repository": value["repository"],
            "owner_source": source, "manifest_sha256": digest(raw), "patch_sha256": value["patch_sha256"],
            "validation_sha256": value["validation_sha256"], "pre_push_gate": value["pre_push_gate"],
            "base_commit": value["base_commit"], "base_tree": value["base_tree"],
            "result_tree": value["result_tree"], "observed_main": live}


def token_scope(transport, repository, token):
    """Read only the existing installation token's exact repository inventory."""
    require(token, "scoped prerequisite App token unavailable")
    repositories = transport.api.pages("/installation/repositories", token, field="repositories")
    require(len(repositories) == 1 and isinstance(repositories[0], dict)
            and repositories[0].get("full_name") == "Hexalith/" + repository,
            "App token repository scope is not exactly the fixed prerequisite repository")
    metadata = transport.api.get("/repos/Hexalith/" + repository, token)
    require(isinstance(metadata, dict) and metadata.get("full_name") == "Hexalith/" + repository
            and metadata.get("default_branch") == "main", "App repository/main identity mismatch")


def exclude_full_writer(owner, source, transport, repository, receipt, phase):
    """Require absence in both selectors without altering either full writer."""
    proof = {"phase": phase, "owner_source": source, "registry_absent": None,
             "accepted_ref_absent": None, "advertised_main": None}
    receipt["full_writer_exclusion"].append(proof)
    receipt["failed_operation"] = "verify target registry absence during " + phase
    registry = rt.registry(owner, source)
    matches = [name for name in registry if name.casefold() == repository.casefold()]
    proof.update(registry_count=len(registry), registry_sha256=digest(json.dumps(registry).encode()),
                 registry_absent=not matches, matching_registry_entries=matches[:32])
    require(not matches, repository + " is present in the exact committed full-delivery registry; coordinator requalification required")
    receipt["failed_operation"] = "verify atomic owner-main/accepted-ref advertisement during " + phase
    output = owner.run("ls-remote", "--heads", transport.remote(rt.CICD), "refs/heads/main", "refs/heads/delivered/*")
    proof.update(advertisement_sha256=digest(output), advertisement_bytes=len(output))
    refs = {}
    for row in output.decode("utf-8").splitlines():
        parts = row.split("\t")
        require(len(parts) == 2, "invalid live owner/ref advertisement row")
        revision, reference = parts
        revision = rt.sha(revision)
        if reference == "refs/heads/main":
            require(proof["advertised_main"] is None, "duplicate live owner main advertisement")
            proof["advertised_main"] = revision
            continue
        require(reference.startswith("refs/heads/delivered/"), "unexpected live owner/ref advertisement")
        name = rt.name(reference.removeprefix("refs/heads/delivered/"))
        require(reference not in refs, "duplicate live accepted ref")
        refs[reference] = (name, revision)
    require(proof["advertised_main"] == source, "advertised owner main differs from reviewed source")
    matches = [reference for reference, (name, _) in refs.items() if name.casefold() == repository.casefold()]
    proof.update(accepted_ref_count=len(refs), accepted_refs_sha256=digest(json.dumps(refs, sort_keys=True).encode()),
                 accepted_ref_absent=not matches, matching_accepted_refs=matches[:32])
    require(not matches, repository + " has a live full-delivery accepted ref; coordinator requalification required")


class Git(rt.Git):
    """Retain bounded combined push diagnostics, including ambiguous timeouts."""
    def run(self, *args, **options):
        if not args or args[0] != "push":
            return super().run(*args, **options)
        token = options.get("token")
        require(token, "scoped prerequisite App token unavailable")
        self.budget.check(token=True)
        env = self.env.copy()
        header = base64.b64encode(("x-access-token:" + token).encode()).decode()
        rt._SECRETS.extend((token, header))
        index = int(env["GIT_CONFIG_COUNT"])
        env.update({"GIT_CONFIG_COUNT": str(index + 1), f"GIT_CONFIG_KEY_{index}": "http.https://github.com/.extraheader",
                    f"GIT_CONFIG_VALUE_{index}": "AUTHORIZATION: basic " + header})
        self.push_diagnostics = {"exit_code": None, "output": "", "timed_out": False}
        timeout = self.budget.timeout()
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(["git", "-C", str(self.root), *map(str, args)],
                                       stdout=output, stderr=subprocess.STDOUT, env=env, start_new_session=True)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.push_diagnostics["timed_out"] = True
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            output.seek(0)
            data = output.read(rt.MAX_GIT + 1)
        self.push_diagnostics.update(exit_code=process.returncode,
                                     output=rt.clean(data[:rt.MAX_GIT].decode("utf-8", "replace")))
        require(not self.push_diagnostics["timed_out"], "Git push timed out; remote outcome is ambiguous; no retry")
        require(len(data) <= rt.MAX_GIT, "Git push diagnostics exceed limit; remote outcome is ambiguous; no retry")
        return process.returncode, data


def execute(operation, context, report_path, *, profile, transport=None, token="", scratch=None, local_root=None, public_fetch=None):
    """Qualify or deliver with private bare objects/index and durable receipts."""
    rt._SECRETS.extend([token] if token else [])
    receipt = {"schema": RECEIPT_SCHEMA, "operation": operation, "profile": profile, "repository": None,
               "owner_source": None, "status": "failed", "failed_operation": "authorize owner invocation", "reason": None,
               "observed_main": None, "candidate_sha": None, "candidate_tree": None,
               "delivered_sha": None, "delivered_tree": None, "push_attempted": False,
               "plan": None, "full_writer_exclusion": [], "public_prerequisites": []}
    try:
        config = configuration(profile)
        repository = config["repository"]
        receipt["repository"] = repository
        require(operation in {"qualify", "deliver"}, "unsupported closed prerequisite operation")
        require(context.get("PREREQUISITE_PROFILE") == profile, "prerequisite profile differs from invocation")
        require(context.get("GITHUB_REPOSITORY") == "Hexalith/Hexalith.CiCd"
                and context.get("GITHUB_REF") == "refs/heads/main"
                and context.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
                and context.get("GITHUB_WORKFLOW_REF") == "Hexalith/Hexalith.CiCd/" + WORKFLOW + "@refs/heads/main",
                "ineligible closed prerequisite owner invocation")
        source = rt.sha(context.get("PREREQUISITE_OWNER_SOURCE"))
        receipt["owner_source"] = source
        require(source == context.get("GITHUB_SHA") and source == context.get("GITHUB_WORKFLOW_SHA"),
                "owner source differs from exact dispatch/workflow source")
        receipt["failed_operation"] = "verify secret-free behavioral suites"
        require(context.get("PREREQUISITE_BEHAVIORAL_RESULT") == "success",
                "secret-free behavioral qualification failed or was skipped")
        if operation == "deliver":
            receipt["failed_operation"] = "verify successful secret-free qualification"
            require(context.get("PREREQUISITE_QUALIFICATION") == "success", "secret-free qualification did not succeed")
            receipt["failed_operation"] = "read exact qualified plan"
            qualified = rt.json_read(context.get("PREREQUISITE_PLAN", ""))
            receipt["failed_operation"] = "require scoped prerequisite App token"
            require(token, "scoped prerequisite App token unavailable")
        budget = rt.Budget()
        transport = transport or rt.Transport(budget)
        public_fetch = public_fetch or fetch_public
        with tempfile.TemporaryDirectory(prefix="contracts-owner-", dir=scratch) as temporary:
            root = Path(temporary)
            owner = rt.Git(root / "owner.git", budget)
            owner.init()
            receipt["failed_operation"] = "fetch exact CiCd main"
            require(transport.module(owner, rt.CICD) == source, "owner source is not current exact CiCd main")
            receipt["failed_operation"] = "verify exact committed trusted owner source"
            source_root = Path(local_root) if local_root else Path(__file__).resolve().parents[1]
            for path in config["sources"]:
                local = source_root / path
                require(local.is_file() and not local.is_symlink() and local.stat().st_size <= rt.MAX_JSON,
                        "local owner payload missing, nonregular or exceeds source size limit: " + path)
                with local.open("rb") as stream:
                    local_bytes = stream.read(rt.MAX_JSON + 1)
                require(local_bytes == owner.blob(source, path),
                        "local owner payload differs from exact committed source: " + path)
            raw = owner.blob(source, config["manifest"])
            value = manifest(raw, profile)
            receipt["failed_operation"] = "verify exact reviewed validation proof"
            logs = {name: owner.blob(source, path) for name, path in config["logs"].items()}
            validation(owner.blob(source, config["validation"]), value, logs)
            exclude_full_writer(owner, source, transport, repository, receipt,
                                "qualification" if operation == "qualify" else "delivery source verification")
            target = Git(root / "target.git", budget, index=root / "private-index")
            target.init()
            receipt["failed_operation"] = "fetch exact target main"
            live = transport.module(target, repository)
            receipt["observed_main"] = live
            if live != value["base_commit"]:
                receipt["failed_operation"] = "verify already delivered exact tree and direct parent"
                require(target.resolve(live + "^{tree}") == value["result_tree"]
                        and parents(target, live) == [value["base_commit"]],
                        "target main differs from reviewed base/direct child; coordinator requalification required")
                target.run("fetch", "--depth=1", "--no-tags", "--no-recurse-submodules",
                           transport.remote(repository), value["base_commit"])
            receipt["failed_operation"] = "construct exact reviewed prerequisite proposal"
            tree = proposal(owner, source, target, value, config)
            binding = plan(profile, source, raw, value, live)
            receipt["plan"] = binding
            if operation == "deliver":
                receipt["failed_operation"] = "verify qualified source/proposal/main binding"
                require(qualified == binding, "qualified source/proposal/main binding mismatch; coordinator requalification required")
                receipt["failed_operation"] = "verify exact App token repository scope"
                token_scope(transport, repository, token)
            if operation == "qualify":
                if profile == "projects-pins":
                    receipt["failed_operation"] = "verify both current public prerequisite archives during qualification"
                    receipt["public_prerequisites"].append({"phase": "qualification", "publications":
                        public_prerequisites(logs["package-qualification"], public_fetch)})
                receipt["status"] = "qualified"
            else:
                if live == value["base_commit"]:
                    receipt["failed_operation"] = "create exact direct child commit"
                    commit = rt.sha(target.run("commit-tree", tree, "-p", live, data=config["message"]).decode().strip())
                    require(parents(target, commit) == [live] and target.resolve(commit + "^{tree}") == tree,
                            "candidate tree/direct parent mismatch")
                    receipt.update(candidate_sha=commit, candidate_tree=tree)
                if profile == "projects-pins":
                    receipt["failed_operation"] = "verify both current public prerequisite archives before push/confirmation"
                    receipt["public_prerequisites"].append({"phase": "before push/confirmation", "publications":
                        public_prerequisites(logs["package-qualification"], public_fetch)})
                receipt["failed_operation"] = "reread exact CiCd main before push/unchanged confirmation"
                require(transport.module(owner, rt.CICD) == source, "CiCd main advanced; coordinator requalification required")
                receipt["failed_operation"] = "reread exact target main before push/unchanged confirmation"
                require(transport.module(target, repository) == live, "target main advanced; coordinator requalification required")
                exclude_full_writer(owner, source, transport, repository, receipt, "push" if live == value["base_commit"] else "unchanged confirmation")
                receipt["failed_operation"] = "reread exact target main after full-writer exclusion"
                require(transport.module(target, repository) == live, "target main advanced during exclusion; coordinator requalification required")
                if live != value["base_commit"]:
                    receipt.update(status="unchanged", delivered_sha=live, delivered_tree=tree)
                else:
                    receipt["failed_operation"] = "git push " + commit + ":refs/heads/main"
                    receipt["push_attempted"] = True
                    rt.atomic(Path(report_path), receipt)
                    try:
                        code, output = transport.push(target, repository, commit, token)
                        receipt["push_result"] = {"exit_code": code, "output": rt.clean(output.decode("utf-8", "replace"))}
                        require(code == 0, "non-forced prerequisite push failed; remote outcome may be ambiguous; no retry or reapply")
                    except Exception:
                        if "push_result" not in receipt and hasattr(target, "push_diagnostics"):
                            receipt["push_result"] = target.push_diagnostics
                        try:
                            observed = transport.module(target, repository)
                            observed_tree = target.resolve(observed + "^{tree}")
                            observed_parents = parents(target, observed)
                            receipt["observed_main"] = observed
                            receipt["reconciliation"] = {"status": "observed", "main": observed,
                                                         "tree": observed_tree, "parents": observed_parents}
                            if observed == commit and observed_tree == tree and observed_parents == [live]:
                                receipt.update(delivered_sha=commit, delivered_tree=tree)
                        except Exception as error:
                            receipt["reconciliation"] = {"status": "unavailable", "reason": rt.clean(error)
                                if isinstance(error, rt.DeliveryError) else type(error).__name__}
                        raise
                    receipt["failed_operation"] = "reread exact published target tree/direct parent"
                    observed = transport.module(target, repository)
                    receipt["observed_main"] = observed
                    require(observed == commit and target.resolve(observed + "^{tree}") == tree
                            and parents(target, observed) == [live], "target main changed after push; no retry")
                    receipt.update(status="delivered", delivered_sha=commit, delivered_tree=tree)
            receipt["failed_operation"] = None
    except Exception as error:
        receipt["reason"] = rt.clean(error) if isinstance(error, rt.DeliveryError) else "prerequisite owner operation failed: " + type(error).__name__
    rt.atomic(Path(report_path), receipt)
    return receipt


def main(argv=None, *, transport=None, public_fetch=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("qualify", "deliver"))
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    context = os.environ.copy()
    tokens = rt.sanitize()
    result = execute(args.operation, context, args.report, profile=args.profile, transport=transport,
                     token=tokens["MODULE_TOKEN"], scratch=context.get("TMPDIR"), public_fetch=public_fetch)
    if args.operation == "qualify" and result["status"] == "qualified" and context.get("GITHUB_OUTPUT"):
        with open(context["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write("plan=" + json.dumps(result["plan"], separators=(",", ":")) + "\n")
    return 0 if result["status"] in {"qualified", "unchanged", "delivered"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
