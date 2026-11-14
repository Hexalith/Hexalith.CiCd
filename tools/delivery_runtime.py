"""Bounded, nonexecuting Git/HTTP boundary for the AD-6 delivery writer.

Production has no configurable remotes. Tests substitute transport objects at
the invocation boundary; neither committed data nor environment supplies URLs.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import http.client
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

MAX_JSON = 2 * 1024 * 1024
MAX_GIT = 16 * 1024 * 1024
MAX_PAGES = 20
CAPACITY = 17
SHA = re.compile(r"[0-9a-f]{40}\Z")
NAME = re.compile(r"[A-Za-z0-9_.-]{1,100}\Z")
TAG = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
CICD = "Hexalith.CiCd"
BUILDS = "Hexalith.Builds"
_SECRETS: list[str] = []


class DeliveryError(ValueError):
    """Only sanitized diagnostics may cross the transport boundary."""


def clean(value) -> str:
    value = str(value)
    for secret in _SECRETS:
        if secret:
            value = value.replace(secret, "[redacted]")
    return "".join(f"\\u{ord(c):04x}" if ord(c) < 32 or 127 <= ord(c) <= 159
                   or 0xD800 <= ord(c) <= 0xDFFF else c for c in value)[:2000]


def name(value, *, module=True) -> str:
    if (not isinstance(value, str) or not NAME.fullmatch(value) or value in {".", ".."}
            or (module and value.casefold() == BUILDS.casefold())):
        raise DeliveryError("invalid module repository identity")
    return value


def sha(value) -> str:
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise DeliveryError("invalid full Git commit identity")
    return value


def json_read(data: bytes | str):
    if len(data) > MAX_JSON:
        raise DeliveryError("JSON exceeds 2 MiB limit")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise DeliveryError("duplicate JSON key")
            result[key] = value
        return result
    def constant(_):
        raise DeliveryError("non-JSON constant")
    try:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise DeliveryError("invalid JSON: " + clean(error)) from None


def read_state(path: Path) -> dict:
    with path.open("rb") as stream:
        value = json_read(stream.read(MAX_JSON + 1))
    if not isinstance(value, dict):
        raise DeliveryError("state must be a JSON object")
    return value


def atomic(path: Path, value) -> None:
    data = (json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_JSON:
        raise DeliveryError("state exceeds 2 MiB limit")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".delivery-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def environment() -> dict[str, str]:
    # The tagged engine constructs its own plain Git instances. This process
    # environment, including process-local Git config, hardens those too.
    config = {"core.hooksPath": os.devnull, "core.attributesFile": os.devnull,
              "credential.helper": "", "http.extraHeader": "", "http.followRedirects": "false",
              "protocol.allow": "never", "protocol.https.allow": "always",
              "protocol.file.allow": "never", "protocol.ext.allow": "never",
              "submodule.recurse": "false", "fetch.recurseSubmodules": "false",
              "filter.lfs.smudge": "", "filter.lfs.process": "", "filter.lfs.required": "false",
              "commit.gpgsign": "false", "user.name": "github-actions[bot]",
              "user.email": "41898282+github-actions[bot]@users.noreply.github.com"}
    result = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
              "HOME": "/nonexistent", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
              "GIT_TERMINAL_PROMPT": "0", "GIT_LFS_SKIP_SMUDGE": "1", "GIT_LITERAL_PATHSPECS": "1",
              "GIT_CONFIG_COUNT": str(len(config)), "PYTHONDONTWRITEBYTECODE": "1"}
    for i, (key, value) in enumerate(config.items()):
        result[f"GIT_CONFIG_KEY_{i}"] = key
        result[f"GIT_CONFIG_VALUE_{i}"] = value
    return result


def sanitize() -> dict[str, str]:
    tokens = {key: os.environ.get(key, "") for key in ("CICD_TOKEN", "MODULE_TOKEN")}
    _SECRETS.extend(value for value in tokens.values() if value)
    os.environ.clear()
    os.environ.update(environment())
    sys.dont_write_bytecode = True
    return tokens


class Budget:
    def __init__(self, started=None, *, clock=time.monotonic):
        self.clock = clock
        self.started = clock() if started is None else started

    def check(self, *, token=False):
        age = self.clock() - self.started
        if age < 0 or age > (50 * 60 if token else 36 * 60):
            raise DeliveryError("token age limit exceeded" if token else "delivery soft deadline exceeded")

    def timeout(self):
        self.check()
        return max(1, min(120, 36 * 60 - (self.clock() - self.started)))


class Git:
    def __init__(self, root: Path | str, budget=None, *, index=None):
        self.root = Path(root).resolve()
        self.budget = budget or Budget()
        self.env = environment()
        if index is not None:
            self.env["GIT_INDEX_FILE"] = str(Path(index).resolve())

    def run(self, *args, data=None, check=True, token=None, environment=None):
        env = self.env.copy()
        if environment is not None:
            for key in ("GIT_INDEX_FILE", "GIT_ATTR_SOURCE"):
                if key in environment:
                    env[key] = environment[key]
        if token is not None:
            if not token:
                raise DeliveryError("scoped App token unavailable")
            self.budget.check(token=True)
            i = int(env["GIT_CONFIG_COUNT"])
            env.update({"GIT_CONFIG_COUNT": str(i + 1), f"GIT_CONFIG_KEY_{i}": "http.https://github.com/.extraheader",
                        f"GIT_CONFIG_VALUE_{i}": "AUTHORIZATION: basic " +
                        base64.b64encode(("x-access-token:" + token).encode()).decode()})
        # Temporary output streams bound memory even for a hostile remote.
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            try:
                process = subprocess.run(["git", "-C", str(self.root), *map(str, args)], input=data,
                                         stdout=out, stderr=err, env=env, timeout=self.budget.timeout())
            except (OSError, subprocess.TimeoutExpired):
                raise DeliveryError("Git operation failed or timed out: " + clean(args[0])) from None
            out.seek(0)
            output = out.read(MAX_GIT + 1)
            if len(output) > MAX_GIT:
                raise DeliveryError("Git output exceeds 16 MiB limit")
            if check and process.returncode:
                raise DeliveryError("Git operation failed: " + clean(args[0]))
            return output if check else (process.returncode, output)

    def init(self):
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.run("init", "--bare", "--quiet", "--template=", "--initial-branch=main")

    def resolve(self, reference):
        return sha(self.run("rev-parse", "--verify", reference).decode().strip())

    def ancestor(self, older, newer):
        code, _ = self.run("merge-base", "--is-ancestor", sha(older), sha(newer), check=False)
        if code not in (0, 1):
            raise DeliveryError("Git ancestry could not be verified")
        return code == 0

    def items(self, revision, prefix=""):
        records = self.run("ls-tree", "-r", "-z", "--full-tree", sha(revision), *(["--", prefix] if prefix else []))
        result = {}
        for row in records.split(b"\0"):
            if not row:
                continue
            header, raw_path = row.split(b"\t", 1)
            mode, kind, oid = header.decode("ascii").split()
            path = raw_path.decode("utf-8")
            result[path] = (mode, kind, sha(oid))
            if len(result) > 100000:
                raise DeliveryError("Git tree entry limit exceeded")
        return result

    def blob(self, revision, path):
        item = self.items(revision, path).get(path)
        if item is None or item[:2] not in (("100644", "blob"), ("100755", "blob")):
            raise DeliveryError("missing regular committed source: " + clean(path))
        if int(self.run("cat-file", "-s", item[2])) > MAX_JSON:
            raise DeliveryError("source blob exceeds 2 MiB limit")
        return self.run("cat-file", "blob", item[2])

    def export(self, revision, prefix, destination):
        total = 0
        for path, (mode, kind, oid) in self.items(revision, prefix).items():
            relative = PurePosixPath(path)
            if (mode not in ("100644", "100755") or kind != "blob"
                    or any(p in (".", "..", ".git") for p in relative.parts)):
                raise DeliveryError("trusted source is not a regular blob")
            data = self.blob(revision, path)
            total += len(data)
            if total > 32 * MAX_JSON:
                raise DeliveryError("trusted source export limit exceeded")
            target = Path(destination).joinpath(*relative.parts)
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            target.write_bytes(data)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise DeliveryError("GitHub API redirect refused")


class API:
    def __init__(self, budget=None, opener=None):
        self.budget = budget or Budget()
        self.opener = opener or build_opener(ProxyHandler({}), NoRedirect())

    def get(self, path, token=None, *, absent=False):
        if (not isinstance(path, str) or not path.startswith(("/repos/Hexalith/", "/installation/repositories"))
                or any(c in path for c in ("\r", "\n", "#", "\\"))
                or any(segment in {".", ".."} for segment in path.split("?", 1)[0].split("/"))):
            raise DeliveryError("noncanonical GitHub API path")
        if absent and not path.endswith("/automated-security-fixes"):
            raise DeliveryError("absence is permitted only for Dependabot security updates")
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2026-03-10",
                   "User-Agent": "Hexalith-CiCd-delivery"}
        if token is not None:
            if not token:
                raise DeliveryError("scoped App token unavailable")
            self.budget.check(token=True)
            headers["Authorization"] = "Bearer " + token
        try:
            with self.opener.open(Request("https://api.github.com" + path, headers=headers),
                                  timeout=min(30, self.budget.timeout())) as response:
                if response.status != 200:
                    raise DeliveryError("GitHub API unexpected status")
                return json_read(response.read(MAX_JSON + 1))
        except HTTPError as error:
            error.close()
            if absent and error.code == 404:
                return None
            raise DeliveryError(f"GitHub API {path.split('?')[0]}: HTTP {error.code}") from None
        except (URLError, OSError, http.client.HTTPException):
            raise DeliveryError("GitHub API transport failed") from None

    def pages(self, path, token=None, *, field=None):
        result = []
        total = None
        for page in range(1, MAX_PAGES + 1):
            value = self.get(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}", token)
            if field is not None:
                if (not isinstance(value, dict) or type(value.get("total_count")) is not int
                        or value["total_count"] < 0):
                    raise DeliveryError("malformed paginated API object")
                if total is not None and total != value["total_count"]:
                    raise DeliveryError("paginated API inventory changed")
                total = value["total_count"]
                value = value.get(field)
            if not isinstance(value, list):
                raise DeliveryError("malformed paginated API list")
            result.extend(value)
            if len(value) < 100:
                if total is not None and len(result) != total:
                    raise DeliveryError("incomplete paginated API inventory")
                return result
        raise DeliveryError("GitHub API pagination limit exceeded")


def object_identity(value):
    obj = value.get("object") if isinstance(value, dict) else None
    if not isinstance(obj, dict) or obj.get("type") not in {"commit", "tag"}:
        raise DeliveryError("malformed GitHub Git object")
    return obj["type"], sha(obj.get("sha"))


def timestamp(value):
    if not isinstance(value, str):
        raise DeliveryError("invalid UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError()
        return parsed
    except ValueError:
        raise DeliveryError("invalid UTC timestamp") from None


class Transport:
    def __init__(self, budget=None, api=None):
        self.budget = budget or Budget()
        self.api = api or API(self.budget)

    def remote(self, repository):
        return "https://github.com/Hexalith/" + name(repository, module=False) + ".git"

    def configure(self, git, repository):
        git.run("config", "remote.origin.url", self.remote(repository))
        git.run("config", "remote.origin.promisor", "true")
        git.run("config", "remote.origin.partialclonefilter", "blob:none")

    def cicd(self, git):
        self.configure(git, CICD)
        git.run("fetch", "--filter=blob:none", "--no-tags", "--no-recurse-submodules", self.remote(CICD),
                "+refs/heads/main:refs/heads/main", "+refs/heads/delivered/*:refs/heads/delivered/*")

    def accepted(self, git, repository):
        # Fetch all refs so deletion cannot leave a stale local accepted target.
        self.cicd(git)
        output = git.run("ls-remote", "--heads", self.remote(CICD), "refs/heads/delivered/" + name(repository))
        if not output:
            return None
        records = output.decode().splitlines()
        if len(records) != 1:
            raise DeliveryError("ambiguous accepted ref identity")
        oid, ref = records[0].split("\t")
        if ref != "refs/heads/delivered/" + repository:
            raise DeliveryError("accepted ref identity mismatch")
        oid = sha(oid)
        if not git.ancestor(oid, git.resolve("refs/heads/main^{commit}")):
            raise DeliveryError("accepted ref is not ancestral to current CiCd main: " + oid)
        return oid

    def advance(self, git, repository, candidate, token):
        return git.run("push", "--porcelain", "--no-verify", "--no-recurse-submodules", self.remote(CICD),
                       sha(candidate) + ":refs/heads/delivered/" + name(repository), token=token, check=False)

    def module(self, git, repository):
        self.configure(git, name(repository))
        git.run("fetch", "--depth=1", "--filter=blob:none", "--no-tags", "--no-recurse-submodules",
                self.remote(name(repository)), "+refs/heads/main:refs/heads/main")
        return git.resolve("refs/heads/main^{commit}")

    def push(self, git, repository, commit, token):
        return git.run("push", "--porcelain", "--no-verify", "--no-recurse-submodules", self.remote(name(repository)),
                       sha(commit) + ":refs/heads/main", token=token, check=False)

    def builds(self, tag, destination):
        try:
            return self._builds(tag, destination)
        except Exception as error:
            raise DeliveryError(f"Builds {clean(tag)}: {clean(error)}") from None

    def _builds(self, tag, destination):
        if not TAG.fullmatch(tag):
            raise DeliveryError("Builds version is not an exact stable tag")
        path = "/repos/Hexalith/Hexalith.Builds/"
        release = self.api.get(path + "releases/tags/" + tag)
        if (not isinstance(release, dict) or release.get("tag_name") != tag
                or release.get("draft") is not False or release.get("immutable") is not True
                or not isinstance(release.get("author"), dict)
                or release["author"].get("login") != "github-actions[bot]"):
            raise DeliveryError("Builds release must be published, immutable and authored by github-actions[bot]")
        timestamp(release.get("published_at"))
        reference = self.api.get(path + "git/ref/tags/" + tag)
        if not isinstance(reference, dict) or reference.get("ref") != "refs/tags/" + tag:
            raise DeliveryError("Builds tag ref identity mismatch")
        kind, raw = object_identity(reference)
        source, seen = raw, set()
        while kind == "tag":
            if source in seen or len(seen) >= 16:
                raise DeliveryError("Builds annotated tag cycle/depth limit")
            seen.add(source)
            value = self.api.get(path + "git/tags/" + source)
            if not isinstance(value, dict) or value.get("sha") != source:
                raise DeliveryError(f"Builds annotated tag identity mismatch: expected {source}, received {value.get('sha') if isinstance(value, dict) else None}")
            kind, source = object_identity(value)
        main = self.api.get(path + "git/ref/heads/main")
        if not isinstance(main, dict) or main.get("ref") != "refs/heads/main":
            raise DeliveryError("Builds main identity mismatch")
        main_kind, main_sha = object_identity(main)
        comparison = self.api.get(path + f"compare/{source}...{main_sha}?per_page=1&page=2")
        base = comparison.get("base_commit") if isinstance(comparison, dict) else None
        merge_base = comparison.get("merge_base_commit") if isinstance(comparison, dict) else None
        base_sha = base.get("sha") if isinstance(base, dict) else base
        merge_base_sha = merge_base.get("sha") if isinstance(merge_base, dict) else merge_base
        if (main_kind != "commit" or not isinstance(comparison, dict)
                or comparison.get("status") not in {"ahead", "identical"}
                or not isinstance(comparison.get("base_commit"), dict)
                or comparison["base_commit"].get("sha") != source
                or not isinstance(comparison.get("merge_base_commit"), dict)
                or comparison["merge_base_commit"].get("sha") != source):
            raise DeliveryError(f"Builds release {source} is not ancestral to live main {main_sha}: "
                                f"returned base_commit {clean(base_sha)}, merge_base_commit {clean(merge_base_sha)}")
        # Verify capability from authenticated-by-identity committed objects
        # before exporting or executing even one byte of this release.
        git = Git(Path(destination) / "objects", self.budget)
        git.init()
        self.configure(git, BUILDS)
        git.run("fetch", "--depth=1", "--filter=blob:none", "--no-tags", "--no-recurse-submodules",
                self.remote(BUILDS), f"refs/tags/{tag}:refs/tags/{tag}")
        acquired_raw = git.resolve("refs/tags/" + tag)
        acquired_source = git.resolve("refs/tags/" + tag + "^{commit}")
        if acquired_raw != raw or acquired_source != source:
            raise DeliveryError(f"Builds acquired tag/source identity mismatch: expected {raw}/{source}, acquired {acquired_raw}/{acquired_source}")
        for required in ("Github/lib/perimeter.py", "Github/lib/perimeter_config.py", "schemas/hexalith.perimeter.v1.json"):
            git.blob(source, required)
        exported = Path(destination) / "source"
        git.export(source, "Github/lib", exported)
        git.export(source, "schemas", exported)
        return git, exported


def load_library(root, budget=None):
    spec = importlib.util.spec_from_file_location("_delivery_tagged_perimeter", Path(root) / "Github/lib/perimeter.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    base = module.Git
    class BoundedGit(base):
        def __init__(self, repository, *, index_file=None):
            super().__init__(repository, index_file=index_file)
            self.adapter = Git(repository, budget, index=index_file)

        def run(self, *args, data=None, environment=None, check=True):
            result = self.adapter.run(*args, data=data, environment=self.environment if environment is None else environment,
                                      check=check)
            if check:
                return result
            code, output = result
            return output if code == 0 else b""

        def blob(self, oid):
            if int(self.run("cat-file", "-s", oid)) > MAX_JSON:
                raise DeliveryError("ownership blob exceeds 2 MiB limit")
            return super().blob(oid)
    module.Git = BoundedGit
    return module


def registry(git, revision):
    result, seen = [], set()
    for path, (mode, kind, _) in git.items(revision, "setup").items():
        if not path.startswith("setup/") or "/" in path[len("setup/"):] or not path.endswith(".yml"):
            continue
        value = name(path[len("setup/"):-4])
        if mode not in {"100644", "100755"} or kind != "blob" or value.casefold() in seen:
            raise DeliveryError("invalid or case-colliding committed registry")
        result.append(value)
        seen.add(value.casefold())
    return sorted(result)
