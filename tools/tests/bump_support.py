"""Real disposable Git boundaries for the nightly bump producer and writer."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_support import ROOT, git, load

sys.path.insert(0, str(ROOT / "tools"))
import bump_runtime as br
import bump as producer
import bump_push as writer
rt = br.rt

IDENTITY = {"runId": 101, "attempt": 1, "source": "a" * 40, "night": "2026-11-14"}
OriginalGit = rt.Git


class FixtureGit(OriginalGit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for index in range(int(self.env["GIT_CONFIG_COUNT"])):
            if self.env[f"GIT_CONFIG_KEY_{index}"] == "protocol.file.allow":
                self.env[f"GIT_CONFIG_VALUE_{index}"] = "always"


class API:
    def __init__(self, workspace):
        self.workspace = workspace
        self.dispatched = 0
        self.budget = workspace.budget
        self.builds_tokens = []

    def pages(self, path, token=None, *, field=None):
        if "/Hexalith.Builds/" in path:
            self.builds_tokens.append(token)
        if path == "/repos/Hexalith/Hexalith.CiCd/actions/runs/101/artifacts":
            return [{"id": 9, "name": "hexalith-nightly-bump-1", "digest": "sha256:" + "a" * 64,
                     "workflow_run": {"id": 101, "head_sha": "a" * 40}}]
        if path != "/repos/Hexalith/Hexalith.Builds/releases":
            raise AssertionError(path)
        return list(self.workspace.releases)

    def get(self, path, token=None):
        if "/Hexalith.Builds/" in path:
            self.builds_tokens.append(token)
        if path == "/repos/Hexalith/Hexalith.CiCd/actions/runs/101":
            return {"id": 101, "run_attempt": 1, "head_sha": "a" * 40, "head_branch": "main",
                    "path": ".github/workflows/nightly.yml", "event": "schedule",
                    "repository": {"full_name": "Hexalith/Hexalith.CiCd"}, "created_at": "2026-11-14T02:17:00Z"}
        prefix = "/repos/Hexalith/Hexalith.Builds/git/ref/"
        if path.startswith(prefix):
            ref = "refs/" + path.removeprefix(prefix)
            sha = git(self.workspace.builds, "rev-parse", ref)
            return {"ref": ref, "object": {"type": git(self.workspace.builds, "cat-file", "-t", sha), "sha": sha}}
        if path.startswith("/repos/Hexalith/Hexalith.Builds/git/tags/"):
            oid = path.rsplit("/", 1)[1]
            raw = git(self.workspace.builds, "cat-file", "tag", oid)
            target = raw.splitlines()[0].removeprefix("object ")
            kind = raw.splitlines()[1].removeprefix("type ")
            return {"sha": oid, "object": {"type": kind, "sha": target}}
        raise AssertionError(path)

    def dispatch_delivery(self, token):
        if not token:
            raise rt.NightlyError("missing token")
        self.dispatched += 1

    def artifact_member(self, repository, metadata, member, token):
        assert repository == rt.CICD and member == "candidate.json"
        return rt.json_read((self.workspace.directory / "candidate.json").read_bytes())


class Transport(br.Transport):
    def __init__(self, workspace):
        super().__init__(workspace.budget, API(workspace))
        self.workspace = workspace
        self.main_calls = 0

    def remote(self, repository):
        if repository == rt.CICD:
            return str(self.workspace.cicd)
        if repository == rt.BUILDS:
            return str(self.workspace.builds)
        raise AssertionError(repository)

    def main(self, store):
        self.main_calls += 1
        hook = self.workspace.main_hooks.get(self.main_calls)
        if hook:
            hook()
        return super().main(store)


class Workspace:
    def __init__(self, root):
        self.root = Path(root)
        self.budget = rt.Budget(token_epoch=__import__("time").time())
        self.builds = self.root / "builds"
        self.cicd = self.root / "cicd"
        self.directory = self.root / "state"
        self.directory.mkdir()
        self.releases = []
        self.main_hooks = {}
        for path in (self.builds, self.cicd):
            path.mkdir()
            git(path, "init", "--quiet", "--initial-branch=main")
        self.old = self.release("v5.1.0")
        self.new = self.release("v5.2.0")
        (self.cicd / "builds-version").write_text("v5.1.0\n")
        (self.cicd / "builds-skip").write_text("")
        (self.cicd / "setup").mkdir()
        (self.cicd / "setup/Hexalith.Alpha.yml").write_text("{}\n")
        (self.cicd / "product.txt").write_text("preserved\n")
        ci = self.cicd / "rendered/Hexalith.Alpha/.github/hexalith-ci.json"
        ci.parent.mkdir(parents=True)
        ci.write_text(json.dumps({"schema": "hexalith.ci.v1", "buildsTag": "v5.1.0", "tests": {"integration": []}}) + "\n")
        workflow = ci.parent / "workflows/ci.yml"
        workflow.parent.mkdir()
        workflow.write_text("uses: Hexalith/Hexalith.Builds/.github/workflows/ci.yml@v5.1.0\n# " + self.old["commit"] + "\n")
        self.base = self.commit()
        git(self.cicd, "config", "receive.denyCurrentBranch", "ignore")
        self.transport = Transport(self)

    def commit(self, subject="Fixture main"):
        git(self.cicd, "add", ".")
        git(self.cicd, "commit", "--quiet", "-m", subject)
        self.base = git(self.cicd, "rev-parse", "HEAD")
        return self.base

    def release(self, tag, *, schema=None, annotated=False):
        schemas = self.builds / "schemas"
        schemas.mkdir(exist_ok=True)
        (schemas / "hexalith.ci.v1.json").write_text(json.dumps(schema or {
            "properties": {"schema": {"const": "hexalith.ci.v1"}, "tests": {
                "properties": {"integration": {"default": []}}}}}) + "\n")
        (self.builds / "release").write_text(tag + "\n")
        git(self.builds, "add", ".")
        git(self.builds, "commit", "--quiet", "-m", "Release " + tag)
        if annotated:
            git(self.builds, "tag", "-a", tag, "-m", tag)
        else:
            git(self.builds, "tag", tag)
        self.releases.append({"id": len(self.releases) + 1, "tag_name": tag, "draft": False,
                              "immutable": True, "published_at": "2026-11-14T01:00:00Z",
                              "author": {"login": "github-actions[bot]"}})
        return {"tag": tag, "object": git(self.builds, "rev-parse", tag),
                "commit": git(self.builds, "rev-parse", tag + "^{commit}")}

    def render(self, project):
        tag = (project / "builds-version").read_text().strip()
        current = git(project, "show", "HEAD:builds-version")
        previous_commit = git(self.builds, "rev-parse", current + "^{commit}")
        commit = git(self.builds, "rev-parse", tag + "^{commit}")
        for path in (project / "rendered").rglob("*"):
            if path.is_file():
                path.write_bytes(path.read_bytes().replace(current.encode(), tag.encode()).replace(previous_commit.encode(), commit.encode()))

    def produce(self, *, identity=None, render=None, check=None):
        with mock.patch.object(rt, "Git", FixtureGit):
            return producer.produce(self.transport, self.directory, identity or IDENTITY,
                                    render=render or self.render, check=check or (lambda project: True))

    def value(self):
        return rt.json_read((self.directory / "candidate.json").read_bytes())

    def push(self, value=None, *, identity=None, mode="github-token"):
        with mock.patch.object(rt, "Git", FixtureGit):
            return writer.push(self.transport, self.directory, identity or IDENTITY, value or self.value(), "inert", mode=mode)

    def mutate(self, value, change):
        # Reconstruct, change a real Git index/tree and sign the resulting new
        # object envelope, so malformed diff tests are not just corrupt hashes.
        store = self.root / "mutate"
        store.mkdir(exist_ok=True)
        local = FixtureGit(store, self.budget, index=store / "index")
        local.init()
        self.transport.main(local)
        br.reconstruct(local, value, IDENTITY)
        local.run("read-tree", value["candidate"])
        change(local)
        tree = local.run("write-tree").decode().strip()
        candidate = local.run("commit-tree", tree, "-p", value["base"],
                              data=br.message(value["new"]["tag"], IDENTITY["night"])).decode().strip()
        return br.envelope(local, IDENTITY, value["base"], candidate, value["old"], value["new"])

    def config(self):
        return {"root": str(self.root), "builds": str(self.builds), "cicd": str(self.cicd),
                "directory": str(self.directory), "releases": self.releases, "old": self.old}


if __name__ == "__main__":
    config = json.loads(Path(sys.argv[1]).read_bytes())
    w = object.__new__(Workspace)
    for key, value in config.items():
        setattr(w, key, Path(value) if key in {"root", "builds", "cicd", "directory"} else value)
    w.budget = rt.Budget(token_epoch=time.time())
    w.main_hooks = {}
    w.transport = Transport(w)
    with mock.patch.object(rt, "Git", FixtureGit):
        if sys.argv[2] == "produce":
            actual = producer.produce
            # Stub the global suite at its invocation boundary: this acceptance
            # fixture must never rediscover/recursively run the outer tool suite.
            with mock.patch.object(producer, "produce", side_effect=lambda t, d, i: actual(t, d, i, render=w.render, check=lambda p: True)):
                raise SystemExit(producer.main(transport=w.transport))
        raise SystemExit(writer.main([], transport=w.transport))
