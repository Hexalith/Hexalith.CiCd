"""Closed, pre-adoption Projects catalog correction; no module code is executed.

The committed manifest binds the complete input/output trees and proposal bytes.
Only the network transport is replaceable by real-Git qualification fixtures.
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

_SPEC = importlib.util.spec_from_file_location("_g6_delivery_runtime", Path(__file__).with_name("delivery_runtime.py"))
rt = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = rt
_SPEC.loader.exec_module(rt)

PROJECTS = "Hexalith.Projects"
MANIFEST = "docs/proposals/projects-g6-catalog.json"
PATCH = "docs/proposals/projects-g6-catalog.patch"
WORKFLOW = ".github/workflows/ci.yml"
ACTION = ".github/actions/prepare-g6-catalog/"
PATHS = (WORKFLOW, ACTION + "action.yml", ACTION + "prepare.py")
SOURCES = ("tools/deliver_g6_catalog.py", "tools/delivery_runtime.py", MANIFEST, PATCH,
           ACTION + "action.yml", ACTION + "prepare.py")


class Git(rt.Git):
    """Keep bounded combined push diagnostics without changing the shared runtime."""
    def run(self, *args, **options):
        if not args or args[0] != "push":
            return super().run(*args, **options)
        token = options.get("token")
        require(token, "scoped Projects App token unavailable")
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
        require(not self.push_diagnostics["timed_out"], "Git push timed out; remote outcome is ambiguous")
        require(len(data) <= rt.MAX_GIT, "Git push diagnostics exceed 16 MiB limit; remote outcome is ambiguous")
        return process.returncode, data


def require(condition, message):
    if not condition:
        raise rt.DeliveryError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def manifest(data):
    value = rt.json_read(data)
    require(isinstance(value, dict) and set(value) == {
        "schema", "repository", "base_commit", "base_tree", "patch_sha256", "result_tree", "before", "after", "pre_push_gate"},
        "invalid closed catalog delivery manifest")
    require(value["schema"] == "hexalith.projects-g6-catalog.v1" and value["repository"] == PROJECTS,
            "catalog delivery repository/schema mismatch")
    require(value["pre_push_gate"] in {"pending-owner-decision", "reviewed-tree-owner-authorized"},
            "invalid closed pre-push owner gate")
    for key in ("base_commit", "base_tree", "result_tree"):
        rt.sha(value[key])
    require(isinstance(value["patch_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", value["patch_sha256"]),
            "invalid proposal SHA256")
    for key in ("before", "after"):
        require(isinstance(value[key], dict) and set(value[key]) == set(PATHS), "unexpected manifest path")
        for path, item in value[key].items():
            if key == "before" and path != WORKFLOW:
                require(item is None, "catalog action must be absent at reviewed base")
            else:
                require(isinstance(item, list) and len(item) == 3 and item[:2] == ["100644", "blob"],
                        "catalog delivery requires regular nonexecutable blobs")
                rt.sha(item[2])
    return value


def entries(git, revision, expected):
    actual = git.items(revision)
    for path, item in expected.items():
        require(actual.get(path) == (tuple(item) if item else None), "unexpected catalog source blob/mode: " + path)
    return actual


def proposal(owner, source, target, value):
    patch = owner.blob(source, PATCH)
    require(digest(patch) == value["patch_sha256"], "reviewed proposal SHA256 mismatch")
    base = value["base_commit"]
    require(target.resolve(base + "^{tree}") == value["base_tree"], "reviewed base tree mismatch")
    before = entries(target, base, value["before"])
    target.run("read-tree", value["base_tree"])
    target.run("apply", "--cached", "--whitespace=nowarn", data=patch)
    tree = target.resolve(target.run("write-tree", "--missing-ok").decode().strip())
    require(tree == value["result_tree"], "complete proposal output tree mismatch")
    after = entries(target, tree, value["after"])
    changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
    require(changed == set(PATHS), "proposal changed paths outside the three-path correction")
    for path in PATHS[1:]:
        require(target.blob(tree, path) == owner.blob(source, path), "catalog action differs from owner payload")
    return tree


def plan(source, value, manifest_bytes, live):
    return {"schema": "hexalith.projects-g6-catalog-plan.v1", "owner_source": source,
            "manifest_sha256": digest(manifest_bytes), "patch_sha256": value["patch_sha256"],
            "pre_push_gate": value["pre_push_gate"],
            "base_commit": value["base_commit"], "base_tree": value["base_tree"],
            "result_tree": value["result_tree"], "observed_main": live}


def parents(git, revision):
    header = git.run("cat-file", "commit", revision).split(b"\n\n", 1)[0]
    return [line[7:].decode("ascii") for line in header.splitlines() if line.startswith(b"parent ")]


def exclude_full_writer(owner, source, transport, receipt, phase):
    """Prove this unregistered target is absent from both full-writer selectors."""
    proof = {"phase": phase, "owner_source": source, "registry_absent": None, "accepted_ref_absent": None,
             "advertised_main": None, "owner_main_matches_source": None}
    receipt["full_writer_exclusion"].append(proof)
    receipt["failed_operation"] = "verify Projects registry absence during " + phase
    registry = rt.registry(owner, source)
    registered = [name for name in registry if name.casefold() == PROJECTS.casefold()]
    proof.update(registry_count=len(registry), registry_sha256=digest(json.dumps(registry, separators=(",", ":")).encode()),
                 registry_absent=not registered, matching_registry_entries=registered[:32])
    require(proof["registry_absent"], "Projects is present in the exact committed full-delivery registry")
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
    require(proof["advertised_main"] is not None, "missing live owner main advertisement")
    proof["owner_main_matches_source"] = proof["advertised_main"] == source
    require(proof["owner_main_matches_source"], "advertised owner main differs from reviewed source")
    matches = [reference for reference, (name, _) in refs.items() if name.casefold() == PROJECTS.casefold()]
    proof.update(accepted_ref_count=len(refs), accepted_refs_sha256=digest(json.dumps(refs, sort_keys=True).encode()),
                 accepted_ref_absent=not matches, matching_accepted_refs=matches[:32])
    require(proof["accepted_ref_absent"], "Projects has a live full-delivery accepted ref")


def execute(operation, context, report_path, *, transport=None, token="", scratch=None, local_root=None):
    """Qualify or deliver using private objects/index, retaining bounded failure receipts."""
    rt._SECRETS.extend([token] if token else [])
    receipt = {"schema": "hexalith.projects-g6-catalog-delivery.v1", "operation": operation,
               "repository": PROJECTS, "owner_source": None,
               "status": "failed", "failed_operation": "authorize owner invocation", "reason": None,
               "observed_main": None, "delivered_sha": None, "delivered_tree": None,
               "candidate_sha": None, "candidate_tree": None, "push_attempted": False, "plan": None,
               "full_writer_exclusion": []}
    try:
        receipt["failed_operation"] = "verify secret-free behavioral suites"
        require(context.get("G6_BEHAVIORAL_RESULT", "success") == "success", "secret-free behavioral qualification failed or was skipped")
        receipt["failed_operation"] = "authorize owner invocation"
        require(context.get("GITHUB_REPOSITORY") == "Hexalith/Hexalith.CiCd" and
                context.get("GITHUB_REF") == "refs/heads/main" and
                context.get("GITHUB_EVENT_NAME") == "workflow_dispatch", "ineligible narrow owner invocation")
        source = rt.sha(context.get("G6_OWNER_SOURCE"))
        receipt["owner_source"] = source
        require(source == context.get("GITHUB_SHA"), "owner source differs from dispatch source")
        if operation == "deliver":
            receipt["failed_operation"] = "verify successful secret-free qualification"
            require(context.get("G6_QUALIFICATION") == "success", "secret-free qualification did not succeed")
            receipt["failed_operation"] = "read qualified plan"
            qualified = rt.json_read(context.get("G6_PLAN", ""))
            receipt["failed_operation"] = "require scoped Projects App token"
            require(token, "scoped Projects App token unavailable")
        budget = rt.Budget()
        transport = transport or rt.Transport(budget)
        with tempfile.TemporaryDirectory(prefix="g6-owner-", dir=scratch) as temporary:
            root = Path(temporary)
            owner = rt.Git(root / "owner.git", budget)
            owner.init()
            receipt["failed_operation"] = "fetch exact CiCd main"
            require(transport.module(owner, rt.CICD) == source, "owner source is not current exact CiCd main")
            receipt["failed_operation"] = "verify committed owner source and manifest"
            source_root = Path(local_root) if local_root else Path(__file__).resolve().parents[1]
            for path in SOURCES:
                require((source_root / path).is_file() and not (source_root / path).is_symlink() and
                        (source_root / path).read_bytes() == owner.blob(source, path),
                        "local owner payload differs from exact committed source: " + path)
            raw = owner.blob(source, MANIFEST)
            value = manifest(raw)
            receipt["failed_operation"] = "verify source-bound pre-push owner gate"
            require(value["pre_push_gate"] == "reviewed-tree-owner-authorized", "pre-push gate is pending owner decision")
            exclude_full_writer(owner, source, transport, receipt, "qualification" if operation == "qualify" else "delivery source verification")
            target = Git(root / "projects.git", budget, index=root / "private-index")
            target.init()
            receipt["failed_operation"] = "fetch exact Projects main"
            live = transport.module(target, PROJECTS)
            receipt["observed_main"] = live
            # The base is fetched by exact object id when main is already the
            # delivered child. No checkout, submodule or module command runs.
            if live != value["base_commit"]:
                receipt["failed_operation"] = "verify already delivered exact tree and direct parent"
                require(target.resolve(live + "^{tree}") == value["result_tree"] and
                        parents(target, live) == [value["base_commit"]], "Projects main differs from reviewed base/result")
                target.run("fetch", "--depth=1", "--no-tags", "--no-recurse-submodules",
                           transport.remote(PROJECTS), value["base_commit"])
            receipt["failed_operation"] = "construct exact reviewed proposal"
            tree = proposal(owner, source, target, value)
            binding = plan(source, value, raw, live)
            receipt["plan"] = binding
            if operation == "deliver":
                receipt["failed_operation"] = "verify qualified source/proposal/main binding"
                require(qualified == binding, "qualified source/proposal/main binding mismatch")
            if operation == "qualify":
                receipt["status"] = "qualified"
            elif live != value["base_commit"]:
                receipt["failed_operation"] = "reread exact CiCd main before unchanged confirmation"
                require(transport.module(owner, rt.CICD) == source, "CiCd main advanced before unchanged confirmation")
                receipt["failed_operation"] = "reread exact Projects main before unchanged confirmation"
                require(transport.module(target, PROJECTS) == live, "Projects main advanced before unchanged confirmation")
                exclude_full_writer(owner, source, transport, receipt, "unchanged confirmation")
                receipt["failed_operation"] = "reread exact Projects main after unchanged exclusion"
                require(transport.module(target, PROJECTS) == live, "Projects main advanced during unchanged exclusion")
                receipt.update(status="unchanged", delivered_sha=live, delivered_tree=tree)
            else:
                receipt["failed_operation"] = "create direct child commit"
                commit = rt.sha(target.run("commit-tree", tree, "-p", live,
                    data=b"build(cicd): acquire reviewed Projects G-6 catalog\n").decode().strip())
                require(parents(target, commit) == [live], "delivery commit parent mismatch")
                receipt.update(candidate_sha=commit, candidate_tree=tree)
                receipt["failed_operation"] = "reread exact CiCd main before push"
                require(transport.module(owner, rt.CICD) == source, "CiCd main advanced before push")
                receipt["failed_operation"] = "reread exact Projects main before push"
                require(transport.module(target, PROJECTS) == live, "Projects main advanced before push")
                exclude_full_writer(owner, source, transport, receipt, "push")
                receipt["failed_operation"] = "reread exact Projects main after push exclusion"
                require(transport.module(target, PROJECTS) == live, "Projects main advanced during push exclusion")
                receipt["failed_operation"] = "git push " + commit + ":refs/heads/main"
                receipt["push_attempted"] = True
                try:
                    code, output = transport.push(target, PROJECTS, commit, token)
                    receipt["push_result"] = {"exit_code": code, "output": rt.clean(output.decode("utf-8", "replace"))}
                    require(code == 0, "non-forced Projects push failed; remote outcome may be ambiguous; no retry or reapply")
                except Exception:
                    if "push_result" not in receipt and hasattr(target, "push_diagnostics"):
                        receipt["push_result"] = target.push_diagnostics
                    try:
                        observed = transport.module(target, PROJECTS)
                        observed_tree = target.resolve(observed + "^{tree}")
                        receipt["observed_main"] = observed
                        receipt["reconciliation"] = {"status": "observed", "main": observed, "tree": observed_tree}
                        if observed == commit and observed_tree == tree:
                            receipt.update(delivered_sha=commit, delivered_tree=tree)
                    except Exception as error:
                        receipt["reconciliation"] = {"status": "unavailable", "reason": rt.clean(error)
                            if isinstance(error, rt.DeliveryError) else type(error).__name__}
                    raise
                receipt["failed_operation"] = "reread Projects main after push"
                observed = transport.module(target, PROJECTS)
                receipt["observed_main"] = observed
                require(observed == commit and target.resolve(observed + "^{tree}") == tree,
                        "Projects main changed after push")
                receipt.update(status="delivered", delivered_sha=commit, delivered_tree=tree)
            receipt["failed_operation"] = None
    except Exception as error:
        receipt["reason"] = rt.clean(error) if isinstance(error, rt.DeliveryError) else "catalog owner operation failed: " + type(error).__name__
    rt.atomic(Path(report_path), receipt)
    return receipt


def main(argv=None, *, transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("qualify", "deliver"))
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    context = os.environ.copy()
    tokens = rt.sanitize()
    result = execute(args.operation, context, args.report, transport=transport,
                     token=tokens["MODULE_TOKEN"], scratch=context.get("TMPDIR"))
    if args.operation == "qualify" and result["status"] == "qualified" and context.get("GITHUB_OUTPUT"):
        with open(context["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write("plan=" + json.dumps(result["plan"], separators=(",", ":")) + "\n")
    return 0 if result["status"] in {"qualified", "unchanged", "delivered"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
