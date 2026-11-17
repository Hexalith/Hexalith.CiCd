"""Real disposable Git snapshots and external-I/O doubles for nightly tests."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

from delivery_support import (ROOT, RELEASE, TAG, Workspace as DeliveryWorkspace,
                              filtered_remote, git, load)

NOW = 1_795_000_000.0
STAMP = "2026-11-14T02:17:00Z"


def zip_document(member, document):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        # Listing and download reconstruct one immutable artifact. Real wall
        # time must not change its ZIP header and authenticated digest.
        entry = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = (0o40775 << 16) | 0x10 if entry.is_dir() else 0o600 << 16
        archive.writestr(entry, document if isinstance(document, bytes) else json.dumps(document).encode())
    return stream.getvalue()


def metadata(identity, name, payload, run_id, head, *, created=STAMP):
    return {"id": identity, "name": name, "size_in_bytes": len(payload), "expired": False,
            "digest": "sha256:" + hashlib.sha256(payload).hexdigest(), "created_at": created,
            "expires_at": "2099-01-01T00:00:00Z",
            "workflow_run": {"id": run_id, "head_sha": head, "head_branch": "main"}}


class Clock:
    def __init__(self, value=NOW):
        self.value = value
        self.sleeps = []

    def __call__(self):
        return self.value

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.value += seconds


class Response(io.BytesIO):
    def __init__(self, data, status=200):
        super().__init__(data if isinstance(data, bytes) else json.dumps(data).encode())
        self.status = status
        self.headers = {}


class Opener:
    """Ordered wire responses, with every original Request available to tests."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if not self.responses:
            raise AssertionError("unexpected HTTP request: " + request.full_url)
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        if isinstance(value, tuple):
            status, data, *headers = value
            if status not in {200, 204}:
                raise HTTPError(request.full_url, status, "fixture", headers[0] if headers else {}, io.BytesIO(b"private body"))
            return Response(data, status=status)
        return Response(value)


class Workspace(DeliveryWorkspace):
    def __init__(self, root, modules=("Hexalith.Alpha",)):
        super().__init__(root, modules)
        for repository in modules:
            rendered = self.candidate / "rendered" / repository / ".github"
            (rendered / "workflows/release.yml").write_text("name: Release fixture\n")
            source = self.root / (repository + "-source")
            shutil.rmtree(source / ".github/workflows")
            shutil.copytree(rendered / "workflows", source / ".github/workflows")
            shutil.copyfile(rendered / "hexalith-ci.json", source / ".github/hexalith-ci.json")
            git(source, "add", ".")
            git(source, "commit", "--quiet", "-m", "Adopt fixture")
            git(source, "push", "--quiet", self.remotes[repository], "HEAD:refs/heads/main")
        if modules:
            self.commit()
        self.accepted = self.sha
        self.directory = self.root / "nightly-dispatch"
        git(self.builds, "update-ref", "refs/heads/main", RELEASE)
        self.config.update(responses={}, dispatch_fail=[], status_fail=[], pending=[], outcomes={},
                           ready_releases={}, original_runs={}, original_artifacts={}, publication_fail=[],
                           publications=str(self.root / "publications.jsonl"),
                           handoffs={}, run_attempts={}, run_started={}, clock=NOW, cancelled=False,
                           dispatches=str(self.root / "dispatches.jsonl"), scopes=str(self.root / "scopes.jsonl"))
        self.clock_path = self.root / "clock.json"
        self.clock_path.write_text(json.dumps(NOW))

    def env(self, **extra):
        return os.environ | {"NIGHTLY_DIRECTORY": str(self.directory), "GITHUB_OUTPUT": str(self.outputs),
            "GITHUB_STEP_SUMMARY": str(self.root / "summary.md"), "GITHUB_WORKSPACE": str(self.candidate),
            "GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd", "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": self.sha,
            "GITHUB_RUN_ID": "101", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_EVENT_NAME": "workflow_dispatch",
            "CICD_TOKEN": "inert-cicd-token", "TARGET_TOKEN": "inert-target-token", "POLL_TOKEN": "inert-poll-token",
            "HANDOFF_TOKEN": "inert-handoff-token", "NIGHTLY_MINT_EPOCH": str(self.clock()), **extra}

    def clock(self):
        return json.loads(self.clock_path.read_bytes())

    def advance(self, seconds):
        self.clock_path.write_text(json.dumps(self.clock() + seconds))

    def call(self, operation, *, phase="dispatch", slot=None, env=None, **extra):
        self.config_path.write_text(json.dumps(self.config))
        args = [operation, "--phase", phase]
        if slot is not None:
            args += ["--slot", str(slot)]
        command = [sys.executable, "-I", str(Path(__file__).resolve()), "driver", str(self.config_path), *args]
        result = subprocess.run(command, env=env or self.env(**extra), capture_output=True)
        self.last = result
        if result.stdout or result.stderr:
            raise AssertionError("controller emitted unexpected output: " + repr(result.stdout + result.stderr))
        return result.returncode

    def state(self, phase="dispatch"):
        directory = self.root / ("nightly-" + phase)
        return json.loads((directory / (("nightly" if phase == "publish-ready" else phase) + ".json")).read_bytes())

    def artifact(self, phase, identity=None):
        identity = identity or (7001 if phase == "dispatch" else 7002)
        directory = self.root / ("nightly-" + phase)
        path = directory / (phase + ".json")
        payload = zip_document(phase + ".json", json.loads(path.read_bytes()))
        archive = self.root / (phase + ".zip")
        archive.write_bytes(payload)
        self.config["handoffs"][str(identity)] = {"path": str(archive), "metadata": metadata(
            identity, "hexalith-nightly-" + phase + "-1", payload, 101, self.sha)}
        return str(identity)

    def ready(self, repository, *, sha=None, last_tag="", version="1.0.0", release_id=880,
              producer_id=10, artifact_id=20):
        """Create an authentic original ready draft without executing module code."""
        remote = self.builds if repository == "Hexalith.Builds" else Path(self.remotes[repository])
        sha = sha or git(remote, "rev-parse", "refs/heads/main")
        if repository == "Hexalith.Builds" and (remote / "shallow").exists():
            git(remote, "fetch", "--quiet", "--unshallow", ROOT / "references/Hexalith.Builds",
                f"refs/tags/{TAG}:refs/tags/{TAG}")
        if repository == "Hexalith.Builds" and version == "1.0.0" and not last_tag:
            version, last_tag = "5.2.0", TAG
        digest = "sha256:" + "a" * 64
        body = ("Fixture release notes\n\n" + "\n".join((
            "hexalith-release: " + sha, "hexalith-release-run: " + str(producer_id),
            "hexalith-release-artifact: " + str(artifact_id) + " " + digest,
            "hexalith-release-packages: ", "hexalith-release-containers: ")) + "\n")
        live = {"id": release_id, "author": {"login": "github-actions[bot]"}, "draft": True,
                "prerelease": False, "tag_name": "v" + version, "target_commitish": sha, "body": body}
        self.config["ready_releases"][repository] = [live]
        self.config["original_runs"].setdefault(repository, {})[str(producer_id)] = {
            "id": producer_id, "path": ".github/workflows/" + (
                "builds-release.yml" if repository == "Hexalith.Builds" else "release.yml"),
            "event": "workflow_dispatch", "head_branch": "main", "head_sha": sha,
            "repository": {"full_name": "Hexalith/" + repository}}
        self.config["original_artifacts"].setdefault(repository, {})[str(artifact_id)] = {
            "id": artifact_id, "name": "release", "expired": False, "digest": digest,
            "expires_at": "2099-01-01T00:00:00Z", "workflow_run": {"id": producer_id, "head_sha": sha}}
        self.config["outcomes"][repository] = {"schema": "hexalith.release-outcome.v1", "sha": sha,
            "version": version, "outcome": "ready", "draftId": release_id, "lastTag": last_tag}
        return live

    def next_phase(self, phase, artifact_id):
        self.directory = self.root / ("nightly-" + phase)
        return self.call("initialize", phase=phase, NIGHTLY_ARTIFACT_ID=artifact_id)


def fixture_transport(rt, config):
    class FixtureOpener:
        def open(self, request, timeout):
            parsed = urlsplit(request.full_url)
            path = parsed.path
            exact = path + ("?" + parsed.query if parsed.query else "")
            method = request.get_method()
            delay = config.get("delays", {}).get(method + " " + exact, 0)
            clock_path = Path(config["requests"]).parent / "clock.json"
            at = json.loads(clock_path.read_bytes())
            if delay:
                clock_path.write_text(json.dumps(at + delay))
            authorization = request.get_header("Authorization")
            with Path(config["requests"]).open("a") as stream:
                stream.write(json.dumps({"path": exact, "method": method, "at": at,
                    "authorization": authorization}) + "\n")
            scopes = config.get("token_scopes")
            if scopes is not None and authorization is not None:
                # Workflow tests give every mint a distinct token: a token used
                # outside its minted repository is refused as GitHub would.
                repository = path.split("/")[3] if path.startswith("/repos/Hexalith/") else ""
                if repository not in scopes.get(authorization.removeprefix("Bearer "), ()):
                    raise HTTPError(request.full_url, 404, "fixture", {}, io.BytesIO(b"private response"))
            override = config.get("responses", {}).get(method + " " + exact,
                config.get("responses", {}).get(exact, config.get("responses", {}).get(path)))
            if override is not None:
                if isinstance(override, list):
                    override = override.pop(0) if len(override) > 1 else override[0]
                if isinstance(override, dict) and set(override) >= {"status", "body"}:
                    status, value = override["status"], override["body"]
                else:
                    status, value = 200, override
            else:
                status, value = self.default(request, parsed)
            if status != 200:
                raise HTTPError(request.full_url, status, "fixture", {}, io.BytesIO(b"private response"))
            return Response(value)

        def default(self, request, parsed):
            parts = parsed.path.split("/")
            repository = parts[3]
            suffix = "/".join(parts[4:])
            query = parse_qs(parsed.query)
            method = request.get_method()
            identity = 1001 + ([*config["modules"], rt.BUILDS].index(repository)) if repository in [*config["modules"], rt.BUILDS] else 101
            source = git(Path(config["builds"] if repository == rt.BUILDS else config["modules"].get(repository, config["cicd"])),
                         "rev-parse", "refs/tags/" + TAG + "^{commit}" if repository == rt.BUILDS else "refs/heads/main")
            if repository == rt.BUILDS:
                if suffix == "releases/tags/" + TAG:
                    return 200, {"tag_name": TAG, "draft": False, "immutable": not config["bad_release"],
                                 "published_at": STAMP, "author": {"login": "github-actions[bot]"}}
                if suffix in {"git/ref/tags/" + TAG, "git/ref/heads/main"}:
                    return 200, {"ref": "refs/tags/" + TAG if "/tags/" in suffix else "refs/heads/main",
                                 "object": {"type": "commit", "sha": config["release"]}}
                if suffix.startswith("compare/"):
                    return 200, {"status": "identical", "base_commit": {"sha": config["release"]},
                                 "merge_base_commit": {"sha": config["release"]}}
            releases = config.get("ready_releases", {}).get(repository, [])
            releases = [releases] if isinstance(releases, dict) else releases
            if suffix == "releases":
                size, page = int(query.get("per_page", [100])[0]), int(query.get("page", [1])[0])
                return 200, releases[(page - 1) * size:page * size]
            if suffix.startswith("releases/") and suffix.split("/")[-1].isdigit():
                selected = [item for item in releases if item["id"] == int(suffix.split("/")[-1])]
                if len(selected) != 1:
                    return 404, {}
                if method == "PATCH":
                    document = json.loads(request.data)
                    with Path(config["publications"]).open("a") as stream:
                        stream.write(json.dumps({"repository": repository, "release_id": selected[0]["id"],
                                                 "document": document}) + "\n")
                    if repository in config.get("publication_fail", []):
                        return 403, {}
                    remote = Path(config["builds"] if repository == rt.BUILDS else config["modules"][repository])
                    tag = "refs/tags/" + document["tag_name"]
                    previous = git(remote, "rev-parse", "--verify", tag, check=False)
                    if previous and previous != document["target_commitish"]:
                        return 422, {}
                    git(remote, "update-ref", tag, document["target_commitish"])
                    selected[0].update(document)
                return 200, selected[0]
            if suffix.startswith("actions/runs/") and suffix.split("/")[-1].isdigit():
                original = config.get("original_runs", {}).get(repository, {}).get(suffix.split("/")[-1])
                if original is not None:
                    return 200, original
            if suffix.startswith("actions/artifacts/") and suffix.split("/")[-1].isdigit():
                original = config.get("original_artifacts", {}).get(repository, {}).get(suffix.split("/")[-1])
                if original is not None:
                    return 200, original
            if suffix.startswith("git/matching-refs/tags/"):
                tag = suffix.removeprefix("git/matching-refs/tags/")
                remote = Path(config["builds"] if repository == rt.BUILDS else config["modules"][repository])
                refs = git(remote, "for-each-ref", "--format=%(refname) %(objecttype) %(objectname)", "refs/tags/" + tag)
                return 200, [{"ref": reference, "object": {"type": kind, "sha": oid}}
                             for reference, kind, oid in (line.split() for line in refs.splitlines())]
            if suffix.startswith("git/tags/"):
                oid = suffix.removeprefix("git/tags/")
                remote = Path(config["builds"] if repository == rt.BUILDS else config["modules"][repository])
                raw = git(remote, "cat-file", "tag", oid)
                headers = dict(line.split(" ", 1) for line in raw.split("\n\n", 1)[0].splitlines())
                return 200, {"sha": oid, "object": {"type": headers["type"], "sha": headers["object"]}}
            if suffix == "immutable-releases":
                return 200, {"enabled": repository not in config.get("fail_app", [])}
            if suffix == "actions/workflows/deliver.yml/runs":
                if config.get("barrier_transition"):
                    clock_path = Path(config["requests"]).parent / "clock.json"
                    elapsed = json.loads(clock_path.read_bytes()) - config["clock"]
                    status = config.setdefault("delivery_status", "queued") if elapsed < 120 else "completed"
                    selected = query.get("status", [""])[0]
                    if selected == "in_progress" and status == "queued":
                        config["delivery_status"] = "in_progress"
                        return 200, {"total_count": 0, "workflow_runs": []}
                    runs = [{"id": 123, "head_branch": "main", "path": ".github/workflows/deliver.yml",
                             "status": status}] if selected == status else []
                    return 200, {"total_count": len(runs), "workflow_runs": runs}
                return 200, {"total_count": 0, "workflow_runs": []}
            if method == "POST" and suffix.endswith("/dispatches"):
                with Path(config["dispatches"]).open("a") as stream:
                    stream.write(json.dumps({"repository": repository, "document": json.loads(request.data)}) + "\n")
                if repository in config["dispatch_fail"]:
                    return 403, {}
                return 200, {"workflow_run_id": identity,
                    "run_url": f"https://api.github.com/repos/Hexalith/{repository}/actions/runs/{identity}",
                    "html_url": rt.run_link(repository, identity)}
            if suffix == "actions/runs/" + str(identity):
                if repository in config["status_fail"]:
                    return 403, {}
                status = "in_progress" if repository in config["pending"] else "completed"
                return 200, {"id": identity, "repository": {"full_name": "Hexalith/" + repository},
                    "path": ".github/workflows/" + ("builds-release.yml" if repository == rt.BUILDS else "release.yml"),
                    "event": "workflow_dispatch", "head_branch": "main", "head_sha": source,
                    "html_url": rt.run_link(repository, identity), "run_attempt": config["run_attempts"].get(repository, 1),
                    "run_started_at": config["run_started"].get(repository, STAMP), "status": status,
                    "conclusion": None if status != "completed" else config.get("conclusions", {}).get(repository, "success")}
            document = config["outcomes"].get(repository, {"schema": "hexalith.release-outcome.v1", "sha": source, "outcome": "nothing"})
            payload = zip_document("outcome.json", document)
            info = metadata(identity + 2000, "hexalith-release-outcome", payload, identity, source)
            if suffix == f"actions/runs/{identity}/artifacts":
                return 200, {"total_count": 1, "artifacts": [info]}
            if suffix == f"actions/artifacts/{identity + 2000}/zip":
                rerun = config.get("rerun_on_download", {}).get(repository)
                if rerun:
                    config["run_attempts"][repository] = 2
                    if rerun == "unreadable":
                        config["status_fail"].append(repository)
                    elif repository not in config["pending"]:
                        config["pending"].append(repository)
                return 200, payload
            if suffix.startswith("actions/artifacts/"):
                artifact_id = suffix.split("/")[2]
                item = config.get("handoffs", {}).get(artifact_id)
                if item:
                    return 200, Path(item["path"]).read_bytes() if suffix.endswith("/zip") else item["metadata"]
            raise rt.NightlyError("unmocked nightly HTTP boundary: " + method + " " + parsed.path)

    class Transport(rt.Transport):
        def __init__(self, budget=None):
            super().__init__(budget, rt.API(budget, repositories=(rt.CICD, rt.BUILDS, *config["modules"]), opener=FixtureOpener(), sleep=lambda _: None))

        def remote(self, repository):
            path = config["cicd"] if repository == rt.CICD else config["builds"] if repository == rt.BUILDS else config["modules"][repository]
            return Path(path).as_uri()

        def module(self, git, repository):
            # A stalled anonymous module fetch spends fake wall-clock time.
            stall = config.get("slow_modules", {}).get(repository, 0)
            if stall:
                clock_path = Path(config["requests"]).parent / "clock.json"
                clock_path.write_text(json.dumps(json.loads(clock_path.read_bytes()) + stall))
            return super().module(git, repository)

    return Transport


def driver():
    config_path, *args = sys.argv[2:]
    config = json.loads(Path(config_path).read_bytes())
    controller = load(ROOT / "tools/nightly.py", "_nightly_isolated_controller")
    rt = controller.rt
    base_environment = rt.environment
    def fixture_environment():
        result = base_environment()
        result["TMPDIR"] = str(Path(config_path).parent)
        index = int(result["GIT_CONFIG_COUNT"])
        result.update(GIT_CONFIG_COUNT=str(index + 1))
        result[f"GIT_CONFIG_KEY_{index}"] = "protocol.file.allow"
        result[f"GIT_CONFIG_VALUE_{index}"] = "always"
        return result
    rt.environment = fixture_environment
    rt.delivery.environment = fixture_environment
    clock_path = Path(config_path).parent / "clock.json"
    def clock():
        return json.loads(clock_path.read_bytes())
    def sleep(seconds):
        clock_path.write_text(json.dumps(clock() + seconds))
    Transport = fixture_transport(rt, config)
    try:
        code = controller.main(args, transport=Transport(), clock=clock, sleep=sleep)
    except Exception as error:
        # Isolated scripts return errors through state, never leak private wire bodies.
        print(type(error).__name__ + ": " + rt.clean(error), file=sys.stderr)
        code = 2
    raise SystemExit(code)


if __name__ == "__main__" and sys.argv[1:2] == ["driver"]:
    driver()
