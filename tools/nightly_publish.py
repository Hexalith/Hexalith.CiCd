"""Publish authenticated ready drafts and reduce nightly verdicts; stdlib only.

The release helpers are supplied by the runtime only after independently
authenticating the committed Builds release. Module repositories supply Git
objects and JSON data, never executable code.
"""
from __future__ import annotations

import hashlib
import html
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace

from nightly_runtime import DIGEST, MAX_PUBLICATION, Git, NightlyError, clean, name, run_identity

PACKAGE_PUBLICATION = "hexalith-package-publication.v1.json"


class _ReleaseApi:
    """Adapt the bounded nightly API to the tagged release helper interface."""

    def __init__(self, api, repository, token, budget, row):
        self.api = api
        self.repository = "Hexalith/" + name(repository, module=False)
        self.token = token
        self.clock = budget.clock
        self.row = row
        self.publication_asset = None
        self.recheck_draft = None

    def _path(self, path):
        if not isinstance(path, str) or not path.startswith("/repos/" + self.repository + "/"):
            raise NightlyError("release helper request escaped the target repository")
        return path

    def get(self, path, *, deadline=None):
        path = self._path(path)
        value = self.api.get(path, self.token, deadline=deadline)
        if re.fullmatch(r"/repos/" + re.escape(self.repository) + r"/actions/runs/[1-9][0-9]*", path):
            repository = value.get("repository") if isinstance(value, dict) else None
            if (not isinstance(repository, dict)
                    or repository.get("full_name") != self.repository):
                raise NightlyError("original producer repository identity mismatch")
        return value

    def pages(self, path, *, deadline=None):
        path = self._path(path)
        # The nightly API owns bounded pagination and adds its own page size.
        path = path.removesuffix("?per_page=100")
        return self.api.pages(path, self.token, deadline=deadline)

    def publish_draft(self, identity, document):
        if self.recheck_draft is None:
            raise NightlyError("live draft verification unavailable")
        self.recheck_draft()
        _current_completion(self, self.row)
        if self._publication_metadata(identity) != self.publication_asset:
            raise NightlyError("package publication asset changed before publication")
        released = self.api.publish_draft(self.repository.split("/", 1)[1], identity, document, self.token)
        if not isinstance(released, dict) or released.get("immutable") is not True:
            raise NightlyError("published release was not verified as immutable")
        if self._publication_metadata(identity) != self.publication_asset:
            raise NightlyError("immutable release does not retain the verified package publication asset")
        return released

    def _publication_metadata(self, draft_id):
        assets = self.pages(f"/repos/{self.repository}/releases/{draft_id}/assets", deadline=self.clock() + 120)
        matches = [asset for asset in assets if asset.get("name") == PACKAGE_PUBLICATION]
        if len(matches) != 1:
            raise NightlyError("expected exactly one existing package publication asset")
        asset = matches[0]
        if (asset.get("state") != "uploaded" or type(asset.get("id")) is not int or asset["id"] < 1
                or type(asset.get("size")) is not int or not 1 <= asset["size"] <= MAX_PUBLICATION
                or not isinstance(asset.get("digest"), str) or not DIGEST.fullmatch(asset["digest"])):
            raise NightlyError("package publication asset metadata is invalid")
        return {key: asset[key] for key in ("id", "size", "digest")}

    def read_publication(self, values, contract):
        self.publication_asset = self._publication_metadata(values["draft-id"])
        data = self.publication_bytes(self.publication_asset["id"])
        document = contract.read(data)
        if contract.serialize(document) != data:
            raise NightlyError("package publication asset is not in canonical v1 form")
        expected = {"repository": self.repository, "sha": values["sha"], "version": values["version"],
                    "artifactRun": int(values["artifact-run"]), "artifactId": int(values["artifact-id"]),
                    "artifactDigest": values["artifact-digest"]}
        if (any(document[key] != value for key, value in expected.items())
                or [item["id"] for item in document["packages"]] != values["inventory"]["packages"]):
            raise NightlyError("package publication asset differs from the original artifact identity or inventory")
        return document

    def publication_bytes(self, identity):
        if self.publication_asset is None or identity != self.publication_asset["id"]:
            raise NightlyError("package publication asset changed before publication")
        data = self.api.publication_bytes(self.repository.split("/", 1)[1], identity, self.token)
        if (len(data) != self.publication_asset["size"]
                or "sha256:" + hashlib.sha256(data).hexdigest() != self.publication_asset["digest"]):
            raise NightlyError("package publication asset bytes do not match verified metadata")
        return data

    def upload_publication(self, identity, data):
        raise NightlyError("existing package publication asset is missing")


class _ReleaseGit:
    """Give trusted release helpers their stdout-shaped hardened Git interface."""

    def __init__(self, git):
        self.git = git

    def run(self, *args, check=True):
        result = self.git.run(*args, check=check)
        if check:
            return SimpleNamespace(stdout=result, returncode=0)
        code, output = result
        return SimpleNamespace(stdout=output, returncode=code)

    def ancestor(self, older, newer):
        return self.git.ancestor(self.git.resolve(str(older) + "^{commit}"),
                                 self.git.resolve(str(newer) + "^{commit}"))


def _refresh(git, transport, repository):
    # Keep complete commit/tag ancestry, while avoiding module blobs, checkout,
    # hooks, attributes, submodules, filters and authenticated Git operations.
    git.run("fetch", "--filter=blob:none", "--no-tags", "--prune", "--no-recurse-submodules",
            transport.remote(repository), "+refs/heads/main:refs/heads/main",
            "+refs/tags/*:refs/tags/*")


def _current_completion(api, row):
    """Do not publish a ready result from an earlier, now rerunning attempt."""
    run = api.get("/repos/" + api.repository + "/actions/runs/" + str(row["runId"]),
                  deadline=api.clock() + 120)
    run_identity(run, row["repository"], row["workflow"], row["runId"])
    if (run["run_attempt"] != row["runAttempt"] or run["head_sha"] != row["dispatchHead"]
            or run["status"] != "completed" or run["conclusion"] != "success"):
        raise NightlyError("correlated completion run changed or is no longer successful")


def _manifest_inventory(manifest, values):
    if (not isinstance(manifest, dict) or set(manifest) != {"sha", "version", "packages", "containers"}
            or manifest["sha"] != values["sha"] or manifest["version"] != values["version"]):
        raise NightlyError("original release manifest source or version mismatch")
    inventory = {}
    for kind, key in (("packages", "id"), ("containers", "name")):
        items = manifest[kind]
        if not isinstance(items, list) or any(not isinstance(item, dict) or not isinstance(item.get(key), str)
                                              for item in items):
            raise NightlyError("original release manifest inventory is malformed")
        inventory[kind] = sorted(item[key] for item in items)
    return inventory


def publish_target(row, helpers, transport, scratch, budget, token):
    """Publish one ready row, retaining a failed row on every uncertain check.

    A persisted ``published`` record is meaningful only in the validated current
    nightly state. A fresh ready row must authenticate a live draft; discovering
    a pre-existing published release cannot manufacture that verified record.
    """
    if row.get("publication") == "published":
        return True
    try:
        outcome = helpers.outcome.validate_outcome(row.get("outcome"))
        if (row.get("eligibility") != "eligible" or row.get("dispatch") != "dispatched"
                or row.get("status") != "completed" or row.get("conclusion") != "success"
                or row.get("outcomeError") or outcome["outcome"] != "ready"):
            raise NightlyError("target has no successful validated ready result")
        if not token:
            raise NightlyError("scoped publication App token unavailable")
        budget.check(token=True)
        repository = name(row["repository"], module=False)
        workflow = ".github/workflows/" + ("builds-release.yml" if repository == "Hexalith.Builds" else "release.yml")
        if row.get("workflow") != workflow:
            raise NightlyError("publication caller workflow identity mismatch")
        api = _ReleaseApi(transport.api, repository, token, budget, row)
        _current_completion(api, row)
        values = {"sha": outcome["sha"], "version": outcome["version"],
                  "draft-id": str(int(outcome["draftId"])), "last-tag": outcome["lastTag"]}
        scratch = Path(scratch)
        scratch.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="publish-", dir=scratch) as directory:
            objects = Git(Path(directory) / "objects", budget)
            objects.init()
            transport.configure(objects, repository)
            _refresh(objects, transport, repository)
            git = _ReleaseGit(objects)
            live = helpers.complete.selected_draft(git, api, values)
            # The selected live draft supplies all five original trailers. The
            # producer may precede the current completion run and its head SHA.
            helpers.publish.producer(api, values, "Hexalith/" + repository + "/" + workflow + "@refs/heads/main")
            metadata = api.get("/repos/" + api.repository + "/actions/artifacts/" + values["artifact-id"],
                               deadline=api.clock() + 120)
            helpers.draft.artifact_metadata(metadata, artifact_id=int(values["artifact-id"]),
                run_id=int(values["artifact-run"]), digest=values["artifact-digest"], sha=values["sha"])
            if values["inventory"] == {"packages": [], "containers": []}:
                payload = transport.api.artifact_bytes(repository, metadata, token)
                inventory = helpers.draft.artifact_inventory(payload, sha=values["sha"],
                    version=values["version"], digest=values["artifact-digest"], repository=api.repository)
            else:
                manifest = transport.api.release_manifest(repository, metadata, token, directory)
                inventory = _manifest_inventory(manifest, values)
            if inventory != values["inventory"]:
                raise NightlyError("original artifact inventory differs from draft release trailers")
            values["package-publication"] = api.read_publication(values, helpers.publish.publication)
            values["body"] = live["body"]
            _refresh(objects, transport, repository)
            if not git.ancestor(values["sha"], row["dispatchHead"]):
                raise NightlyError("release source is not an ancestor of the dispatch head")

            def recheck_draft():
                helpers.complete.selected_draft(git, api, values, body=values["body"])
                helpers.publish.version_tag(api, values)

            api.recheck_draft = recheck_draft
            document = helpers.publish.finalize_release(git, api, values, refresh=lambda *_args: True)
            helpers.outcome.validate_outcome(document)
            if (document.get("outcome") != "published" or document.get("sha") != values["sha"]
                    or document.get("version") != values["version"]):
                raise NightlyError("release helper did not verify completed publication")
        row["publication"] = "published"
        row["reason"] = "GitHub publication verified"
        return True
    except Exception as error:
        # No retries follow an uncertain PATCH. Its draft/tag may now exist,
        # but that alone cannot turn this invocation's unverified row green.
        row["publication"] = "failed"
        row["reason"] = "publication failed: " + clean(error)
        return False


def _verdict(row):
    reason = clean(row.get("reason", ""))
    if row.get("eligibility") == "not-adopted" and row.get("dispatch") == "skipped":
        return "skip", reason or "not adopted"
    if row.get("eligibility") != "eligible":
        return "fail", reason or "release eligibility was not established"
    if row.get("dispatch") != "dispatched" or type(row.get("runId")) is not int or row["runId"] < 1:
        return "fail", reason or "release dispatch was not established"
    if row.get("status") != "completed":
        return "fail", reason or "release run did not complete before the wait deadline"
    if row.get("conclusion") != "success":
        return "fail", "release run concluded " + clean(row.get("conclusion") or "without a conclusion")
    if row.get("outcomeError"):
        return "fail", "release outcome unreadable: " + clean(row["outcomeError"])
    outcome = row.get("outcome")
    if not isinstance(outcome, dict):
        return "fail", "release outcome is missing"
    result = outcome.get("outcome")
    if result in {"published", "nothing", "disabled"}:
        return "pass", "release workflow succeeded"
    if result == "ready" and row.get("publication") == "published":
        return "pass", "GitHub publication verified"
    if result == "ready":
        return "fail", reason or "ready draft publication was not verified"
    return "fail", reason or "release workflow reported a failed outcome"


def _cell(value):
    return html.escape(clean(value), quote=False).replace("|", "&#124;")


def reduce_report(state, summary_path=None):
    """Retain all target rows, write the summary, and return aggregate failure."""
    state["phase"] = "nightly"
    failed = bool(state.get("errors"))
    rows = state.get("targets", [])
    if not rows:
        failed = True
        message = "nightly state has no target results"
        if message not in state.setdefault("errors", []):
            state["errors"].append(message)
    for row in rows:
        row["verdict"], row["reason"] = _verdict(row)
        failed = failed or row["verdict"] == "fail"
    state["result"] = "fail" if failed else "pass"
    lines = ["# Nightly releases: " + state["result"].upper(), "",
             "| Repository | Verdict | Run | Reason |", "| --- | --- | --- | --- |"]
    for row in rows:
        run = "—"
        repository = row.get("repository", "")
        identity = row.get("runId", 0)
        expected = "https://github.com/Hexalith/" + repository + "/actions/runs/" + str(identity)
        if type(identity) is int and identity > 0 and row.get("link") == expected:
            run = "[run " + str(identity) + "](" + expected + ")"
        lines.append("| " + " | ".join((_cell(repository), row["verdict"], run,
                                         _cell(row["reason"]))) + " |")
    if state.get("errors"):
        lines.extend(("", "Orchestration failures:"))
        lines.extend("- " + _cell(error) for error in state["errors"])
    lines.extend(("", "Release details remain in each target's linked run.", ""))
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("\n".join(lines))
    return failed
