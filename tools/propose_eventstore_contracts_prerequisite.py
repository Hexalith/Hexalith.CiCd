"""Propose one reviewed EventStore workflow on a fixed branch, respecting main policy.

No target source is checked out or executed. The optional PR operation uses a
separate same-App token and cannot merge, dispatch, upload or write main.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request

_SPEC = importlib.util.spec_from_file_location("_eventstore_proposal_core", Path(__file__).with_name("deliver_contracts_prerequisites.py"))
core = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = core
_SPEC.loader.exec_module(core)
rt = core.rt
require = core.require
REPOSITORY = "Hexalith.EventStore"
PROFILE = "eventstore-publisher"
BRANCH = "cicd/contracts-prerequisite-eventstore"
TARGET_REF = "refs/heads/" + BRANCH
WORKFLOW = ".github/workflows/propose-eventstore-contracts-prerequisite.yml"
EXTRA_SOURCES = ("tools/propose_eventstore_contracts_prerequisite.py", WORKFLOW,
                 "tools/tests/test_propose_eventstore_contracts_prerequisite.py")
COMPARE = "https://github.com/Hexalith/Hexalith.EventStore/compare/main...cicd/contracts-prerequisite-eventstore?expand=1"
TITLE = "build(cicd): propose approved Contracts prerequisite publisher"
BODY = """Propose only the reviewed release.yml prerequisite publisher while preserving all normal full-release jobs and required main checks.

The approved package is Hexalith.EventStore.Contracts 5.3.0, producer source 0be0c922883d4ea61b18e843e24472162261d934, unsigned archive SHA256 1c3bdabc4778467d74b468a47f0413f5f85272539d9969891036c8865f6949c3. The retained package-only qualifications bind the exact approved source and archive; they do not replace the full-release gates.

The fixed publisher implementation is CiCd source 264e5de34341187a0ad4724dd6a39248b9cb9b58. Packet: https://github.com/Hexalith/Hexalith.CiCd/tree/264e5de34341187a0ad4724dd6a39248b9cb9b58/docs/contracts-prerequisites . Reviewed proposal: https://github.com/Hexalith/Hexalith.CiCd/blob/cc4b8cc46f4e254e20518c46726fc5a57ed1164f/docs/proposals/contracts-prerequisites/eventstore-publisher.json .

This draft does not merge itself, dispatch publication, or bypass PR review or any of the eight required status checks. Full-release gates remain unchanged.
"""
PULLS = "/repos/Hexalith/Hexalith.EventStore/pulls"
QUERY = PULLS + "?state=open&head=Hexalith%3Acicd%2Fcontracts-prerequisite-eventstore&base=main"
REPORTS = {"qualify": "eventstore-proposal-qualification.json", "propose": "eventstore-proposal-branch.json",
           "pull-request": "eventstore-proposal-pr.json"}


class API(rt.API):
    def create(self, token):
        """One fixed draft-PR POST. Reads still use the bounded runtime API."""
        require(token, "scoped same-App PR token unavailable")
        self.budget.check(token=True)
        body = json.dumps({"title": TITLE, "body": BODY, "head": BRANCH, "base": "main", "draft": True,
                           "maintainer_can_modify": False}, separators=(",", ":")).encode()
        headers = {"Accept": "application/vnd.github+json", "Content-Type": "application/json",
                   "X-GitHub-Api-Version": "2026-03-10", "User-Agent": "Hexalith-CiCd-EventStore-proposal",
                   "Authorization": "Bearer " + token}
        request = Request("https://api.github.com" + PULLS, data=body, headers=headers, method="POST")
        try:
            with self.opener.open(request, timeout=min(30, self.budget.timeout())) as response:
                require(response.status == 201, "draft PR POST returned an unexpected status; outcome may be ambiguous")
                return rt.json_read(response.read(rt.MAX_JSON + 1))
        except HTTPError as error:
            error.close()
            raise rt.DeliveryError("draft PR POST refused: HTTP " + str(error.code) + "; no retry or permission expansion") from None
        except (URLError, OSError, rt.http.client.HTTPException):
            raise rt.DeliveryError("draft PR POST transport failed; outcome is ambiguous; no retry") from None


class Transport(rt.Transport):
    def __init__(self, budget=None, api=None):
        budget = budget or rt.Budget()
        super().__init__(budget, api or API(budget))

    def branch(self, git):
        output = git.run("ls-remote", "--heads", self.remote(REPOSITORY), TARGET_REF)
        if not output:
            return None
        rows = output.decode("ascii").splitlines()
        require(len(rows) == 1, "ambiguous fixed proposal branch advertisement")
        parts = rows[0].split("\t")
        require(len(parts) == 2 and parts[1] == TARGET_REF, "unexpected proposal branch advertisement")
        advertised = rt.sha(parts[0])
        git.run("fetch", "--depth=1", "--filter=blob:none", "--no-tags", "--no-recurse-submodules",
                self.remote(REPOSITORY), "+" + TARGET_REF + ":" + TARGET_REF)
        require(git.resolve(TARGET_REF + "^{commit}") == advertised, "proposal branch changed during acquisition")
        return advertised

    def push_branch(self, git, candidate, token):
        # An empty expected-ref lease is an atomic create-only condition. It
        # rejects every existing ref, including one at an ancestor of candidate;
        # no nonempty lease or force-overwrite operation is ever constructed.
        return git.run("push", "--porcelain", "--no-verify", "--no-recurse-submodules",
                       "--force-with-lease=" + TARGET_REF + ":", self.remote(REPOSITORY),
                       rt.sha(candidate) + ":" + TARGET_REF, token=token, check=False)


def authorize(context):
    require(context.get("GITHUB_REPOSITORY") == "Hexalith/Hexalith.CiCd"
            and context.get("GITHUB_REF") == "refs/heads/main" and context.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
            and context.get("GITHUB_WORKFLOW_REF") == "Hexalith/Hexalith.CiCd/" + WORKFLOW + "@refs/heads/main",
            "ineligible fixed EventStore proposal invocation")
    source = rt.sha(context.get("PREREQUISITE_OWNER_SOURCE"))
    require(source == context.get("GITHUB_SHA") == context.get("GITHUB_WORKFLOW_SHA"), "proposal owner/workflow source differs")
    require(context.get("PREREQUISITE_BEHAVIORAL_RESULT") == "success", "proposal behavioral qualification failed or skipped")
    return source


def verified_state(root, transport, source, receipt, local_root):
    config = core.configuration(PROFILE)
    owner = rt.Git(root / "owner.git", transport.budget)
    owner.init()
    receipt["failed_operation"] = "fetch exact current CiCd source"
    require(transport.module(owner, rt.CICD) == source, "proposal owner is not current exact CiCd main")
    receipt["failed_operation"] = "verify committed trusted proposal source"
    source_root = Path(local_root) if local_root else Path(__file__).resolve().parents[1]
    for path in (*config["sources"], *EXTRA_SOURCES):
        local = source_root / path
        require(local.is_file() and not local.is_symlink() and local.stat().st_size <= rt.MAX_JSON,
                "trusted proposal source missing/nonregular/oversized: " + path)
        with local.open("rb") as stream:
            data = stream.read(rt.MAX_JSON + 1)
        require(data == owner.blob(source, path), "trusted proposal source differs from committed owner: " + path)
    receipt["failed_operation"] = "verify exact reviewed EventStore manifest and committed logs"
    raw = owner.blob(source, config["manifest"])
    value = core.manifest(raw, PROFILE)
    logs = {name: owner.blob(source, path) for name, path in config["logs"].items()}
    core.validation(owner.blob(source, config["validation"]), value, logs)
    core.exclude_full_writer(owner, source, transport, REPOSITORY, receipt, "proposal verification")
    target = core.Git(root / "eventstore.git", transport.budget, index=root / "private-index")
    target.init()
    receipt["failed_operation"] = "require exact reviewed EventStore main"
    main = transport.module(target, REPOSITORY)
    require(main == value["base_commit"], "EventStore main advanced; coordinator requalification required")
    receipt.update(observed_main=main, base_commit=main, approved_tree=value["result_tree"])
    receipt["failed_operation"] = "construct complete reviewed EventStore proposal tree"
    tree = core.proposal(owner, source, target, value, config)
    binding = core.plan(PROFILE, source, raw, value, main)
    binding.update(schema="hexalith.eventstore-prerequisite-proposal-plan.v1", target_ref=TARGET_REF)
    receipt["plan"] = binding
    return owner, target, value, tree, binding


def exact_branch(target, revision, value):
    require(revision is not None and target.resolve(revision + "^{tree}") == value["result_tree"]
            and core.parents(target, revision) == [value["base_commit"]],
            "fixed proposal branch differs from reviewed tree/direct parent; never overwrite")


def reread(owner, target, source, value, branch, transport, receipt):
    receipt["failed_operation"] = "reread current owner/main/proposal branch"
    require(transport.module(owner, rt.CICD) == source, "CiCd main advanced before proposal write")
    require(transport.module(target, REPOSITORY) == value["base_commit"], "EventStore main advanced before proposal write")
    core.exclude_full_writer(owner, source, transport, REPOSITORY, receipt, "before proposal write")
    require(transport.branch(target) == branch, "proposal branch changed before write; never overwrite")
    require(transport.module(target, REPOSITORY) == value["base_commit"], "EventStore main advanced during proposal exclusion")


def exact_pr(value, branch, base):
    require(isinstance(value, dict) and type(value.get("number")) is int and value["number"] > 0, "malformed fixed draft PR identity")
    require(value.get("state") == "open" and value.get("draft") is True and value.get("title") == TITLE
            and value.get("body") == BODY, "existing PR differs from the fixed draft proposal")
    for field, ref, sha in (("head", BRANCH, branch), ("base", "main", base)):
        item = value.get(field)
        require(isinstance(item, dict) and item.get("ref") == ref and item.get("sha") == sha
                and isinstance(item.get("repo"), dict) and item["repo"].get("full_name") == "Hexalith/" + REPOSITORY,
                "fixed draft PR repository/ref/source mismatch: " + field)
    url = "https://github.com/Hexalith/Hexalith.EventStore/pull/" + str(value["number"])
    require(value.get("html_url") == url, "fixed draft PR URL differs")
    return {"number": value["number"], "url": url, "head_sha": branch, "base_sha": base, "draft": True}


def existing_pr(transport, token, branch, base):
    values = transport.api.pages(QUERY, token)
    require(isinstance(values, list) and len(values) <= rt.MAX_PAGES * 100, "fixed PR inventory exceeds bound")
    require(len(values) <= 1, "multiple fixed-head/base PRs; coordinator decision required")
    return exact_pr(values[0], branch, base) if values else None


def allow_new_write(receipt, previous, attempted_field):
    """Fresh runners cannot turn initializer placeholders into retry authority."""
    if receipt["run_attempt"] == 1:
        return
    fields = ("schema", "operation", "repository", "target_ref", "owner_source", "plan", "run_id")
    valid = (previous.get("write_checkpoint_origin_attempt") == 1
             and all(previous.get(field) == receipt[field] for field in fields)
             and previous.get(attempted_field) is False)
    require(valid, "Actions rerun has no valid preserved pre-write checkpoint; new write refused; observe existing branch/PR only")
    receipt["write_checkpoint_origin_attempt"] = 1


def execute(operation, context, *, transport=None, token="", scratch=None, local_root=None):
    require(operation in REPORTS, "unsupported fixed proposal operation")
    report_path = Path(REPORTS[operation])
    previous = {}
    rt._SECRETS.extend([token] if token else [])
    receipt = {"schema": "hexalith.eventstore-prerequisite-proposal.v1", "operation": operation,
               "repository": REPOSITORY, "target_ref": TARGET_REF, "owner_source": None, "status": "failed",
               "failed_operation": "authorize exact owner proposal invocation", "reason": None, "plan": None,
               "observed_main": None, "candidate_sha": None, "candidate_tree": None,
               "delivered_sha": None, "delivered_tree": None, "push_attempted": False, "post_attempted": False,
               "run_id": context.get("GITHUB_RUN_ID"), "run_attempt": None, "write_checkpoint_origin_attempt": None,
               "branch_success": False, "pr": None, "comparison_url": COMPARE, "full_writer_exclusion": []}
    try:
        if operation in {"propose", "pull-request"} and report_path.exists():
            # Preserve an uncertain POST across repeated invocations even when
            # no matching PR can yet be observed. Never erase its checkpoint.
            if operation == "pull-request":
                receipt["post_attempted"] = True
            previous = rt.read_state(report_path)
            if operation == "pull-request":
                receipt["post_attempted"] = bool(previous.get("post_attempted"))
        source = authorize(context)
        receipt["owner_source"] = source
        attempt = context.get("GITHUB_RUN_ATTEMPT", "1")
        require(isinstance(attempt, str) and attempt.isascii() and attempt.isdigit()
                and len(attempt) <= 6 and not attempt.startswith("0"), "invalid Actions run attempt")
        receipt["run_attempt"] = int(attempt)
        if receipt["run_attempt"] == 1:
            receipt["write_checkpoint_origin_attempt"] = 1
        if operation != "qualify":
            require(context.get("PREREQUISITE_QUALIFICATION") == "success", "secret-free proposal qualification did not succeed")
            qualified = rt.json_read(context.get("PREREQUISITE_PLAN", ""))
        if operation == "pull-request":
            receipt["failed_operation"] = "verify retained branch success"
            published = rt.read_state(Path(REPORTS["propose"]))
            require(published.get("status") in {"proposed", "unchanged"} and published.get("branch_success") is True
                    and published.get("owner_source") == source and published.get("repository") == REPOSITORY
                    and published.get("target_ref") == TARGET_REF and published.get("plan") == qualified,
                    "exact successful branch proof unavailable; PR not attempted")
            receipt.update(branch_success=True, delivered_sha=rt.sha(published.get("delivered_sha")),
                           delivered_tree=rt.sha(published.get("delivered_tree")))
        if operation != "qualify":
            receipt["failed_operation"] = "require scoped same-App " + ("PR" if operation == "pull-request" else "branch") + " token"
            require(token, "scoped same-App " + ("PR" if operation == "pull-request" else "branch") + " token unavailable; branch and comparison URL retained")
        transport = transport or Transport()
        with tempfile.TemporaryDirectory(prefix="eventstore-proposal-", dir=scratch) as temporary:
            owner, target, value, tree, binding = verified_state(Path(temporary), transport, source, receipt, local_root)
            if operation != "qualify":
                receipt["failed_operation"] = "verify exact qualified proposal plan and token scope"
                require(qualified == binding, "qualified proposal source/main/tree binding mismatch")
                core.token_scope(transport, REPOSITORY, token)
            receipt["failed_operation"] = "observe fixed proposal branch"
            branch = transport.branch(target)
            if branch is not None:
                exact_branch(target, branch, value)
            if operation == "qualify":
                receipt["status"] = "qualified"
            elif operation == "propose":
                if branch is None:
                    allow_new_write(receipt, previous, "push_attempted")
                    receipt["failed_operation"] = "create reviewed single-parent proposal commit"
                    candidate = rt.sha(target.run("commit-tree", tree, "-p", value["base_commit"],
                                                 data=core.configuration(PROFILE)["message"]).decode().strip())
                    exact_branch(target, candidate, value)
                    receipt.update(candidate_sha=candidate, candidate_tree=tree)
                reread(owner, target, source, value, branch, transport, receipt)
                if branch is not None:
                    receipt.update(status="unchanged", branch_success=True, delivered_sha=branch, delivered_tree=tree)
                else:
                    receipt.update(push_attempted=True, failed_operation="push only " + TARGET_REF)
                    rt.atomic(report_path, receipt)
                    try:
                        code, output = transport.push_branch(target, candidate, token)
                        receipt["push_result"] = {"exit_code": code, "output": rt.clean(output.decode("utf-8", "replace"))}
                        require(code == 0, "create-only fixed branch push failed; outcome may be ambiguous; no retry")
                    except Exception:
                        if "push_result" not in receipt and hasattr(target, "push_diagnostics"):
                            receipt["push_result"] = target.push_diagnostics
                        try:
                            observed = transport.branch(target)
                            exact_branch(target, observed, value)
                            receipt["reconciliation"] = {"status": "observed", "branch_sha": observed, "tree": tree}
                            if observed == candidate:
                                receipt.update(branch_success=True, delivered_sha=observed, delivered_tree=tree)
                        except Exception as error:
                            receipt["reconciliation"] = {"status": "unavailable", "reason": rt.clean(error)
                                if isinstance(error, rt.DeliveryError) else type(error).__name__}
                        raise
                    receipt["failed_operation"] = "prove published branch and unchanged main"
                    observed = transport.branch(target)
                    exact_branch(target, observed, value)
                    require(observed == candidate and transport.module(target, REPOSITORY) == value["base_commit"],
                            "proposal branch/main changed after push; no retry")
                    receipt.update(status="proposed", branch_success=True, delivered_sha=observed, delivered_tree=tree)
            else:
                require(branch == receipt["delivered_sha"] and tree == receipt["delivered_tree"], "live proposal differs from retained branch proof")
                reread(owner, target, source, value, branch, transport, receipt)
                receipt["failed_operation"] = "read exact existing fixed-head/main draft PR"
                found = existing_pr(transport, token, branch, value["base_commit"])
                if found:
                    receipt.update(status="pr-existing", pr=found)
                else:
                    require(not previous.get("post_attempted"), "a previous PR POST is unconfirmed; never automatically repeat")
                    allow_new_write(receipt, previous, "post_attempted")
                    reread(owner, target, source, value, branch, transport, receipt)
                    receipt.update(post_attempted=True, failed_operation="create fixed draft PR once")
                    rt.atomic(report_path, receipt)
                    try:
                        created = transport.api.create(token)
                        receipt["pr"] = exact_pr(created, branch, value["base_commit"])
                    except Exception:
                        try:
                            receipt["pr"] = existing_pr(transport, token, branch, value["base_commit"])
                            receipt["pr_reconciliation"] = "observed" if receipt["pr"] else "not observed"
                        except Exception as error:
                            receipt["pr_reconciliation"] = rt.clean(error) if isinstance(error, rt.DeliveryError) else type(error).__name__
                        raise
                    receipt["status"] = "pr-created"
            receipt["failed_operation"] = None
    except Exception as error:
        receipt["reason"] = rt.clean(error) if isinstance(error, rt.DeliveryError) else "fixed proposal operation failed: " + type(error).__name__
        if operation == "pull-request" and receipt["branch_success"]:
            receipt["status"] = "pr-blocked"
    rt.atomic(report_path, receipt)
    return receipt


def main(argv=None, *, transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=tuple(REPORTS))
    args = parser.parse_args(argv)
    context = os.environ.copy()
    tokens = rt.sanitize()
    result = execute(args.operation, context, transport=transport, token=tokens["MODULE_TOKEN"], scratch=context.get("TMPDIR"))
    if context.get("GITHUB_OUTPUT"):
        with open(context["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            if result["status"] == "qualified":
                stream.write("plan=" + json.dumps(result["plan"], separators=(",", ":")) + "\n")
            if result["status"] in {"proposed", "unchanged"}:
                stream.write("branch-success=true\n")
    return 0 if result["status"] in {"qualified", "proposed", "unchanged", "pr-created", "pr-existing"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
