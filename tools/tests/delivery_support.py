"""Disposable real Git/HTTP boundary used by delivery entrypoint qualification."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
TAG = "v5.1.0"
RELEASE = "9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4"


def git(root, *args, data=None, check=True):
    result = subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                             "-c", "core.hooksPath=/dev/null", "-C", str(root), *map(str, args)],
                            input=data, capture_output=True)
    if check and result.returncode:
        raise AssertionError(result.stderr.decode(errors="replace"))
    return result.stdout.decode().strip()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Workspace:
    def __init__(self, root, modules=("Hexalith.Alpha",)):
        self.root = Path(root)
        self.root.mkdir()
        self.candidate = self.root / "candidate"
        self.candidate.mkdir()
        git(self.candidate, "init", "--quiet", "--initial-branch=main")
        shutil.copytree(ROOT / "tools", self.candidate / "tools", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (self.candidate / "setup").mkdir()
        (self.candidate / "builds-version").write_text(TAG + "\n")
        self.remotes = {}
        self.modules = list(modules)
        for module in modules:
            self.module(module)
        self.commit()
        self.accepted = self.sha
        self.remote = self.root / "cicd.git"
        git(self.root, "clone", "--quiet", "--bare", self.candidate, self.remote)
        # Exact released objects, not current Builds HEAD or a fake engine.
        self.builds = self.root / "builds.git"
        self.builds.mkdir()
        git(self.builds, "init", "--bare", "--quiet")
        git(self.builds, "fetch", "--quiet", "--depth=1", ROOT / "references/Hexalith.Builds", f"refs/tags/{TAG}:refs/tags/{TAG}")
        self.config = {"cicd": str(self.remote), "builds": str(self.builds), "modules": self.remotes,
                       "release": RELEASE, "fail_app": [], "mint_fail": [], "push_fail": [], "races": {},
                       "ref_races": {}, "api": {}, "bad_release": False}
        self.config_path = self.root / "config.json"
        self.directory = self.root / "delivery"
        self.outputs = self.root / "outputs"

    def module(self, module):
        path = self.root / (module + "-source")
        path.mkdir()
        git(path, "init", "--quiet", "--initial-branch=main")
        (path / "product.txt").write_text("foreign product\n")
        (path / "AGENTS.md").write_text("foreign instructions\n")
        (path / ".gitattributes").write_text("* filter=poison\n")
        settings = path / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_text('{"permissions":{"allow":["foreign"],"deny":["foreign"]},"foreign":true}\n')
        (path / ".gitmodules").write_text('[submodule "foreign"]\n path = references/Foreign\n url = https://example.invalid/foreign.git\n')
        (path / "package.json").write_text('{"name":"foreign","scripts":{"release":"semantic-release","keep":"echo ok"},"devDependencies":{"semantic-release":"1","foreign":"2"}}\n')
        (path / ".releaserc.json").write_text("{broken whole obsolete\n")
        (path / "Directory.Build.rsp").write_text("obsolete\n")
        hook = path / ".husky/commit-msg"
        hook.parent.mkdir()
        hook.write_text("keep foreign\nnpx commitlint --edit\n")
        workflow = path / ".github/workflows/old.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("{malformed whole file\n")
        git(path, "add", ".")
        git(path, "commit", "--quiet", "-m", "Product")
        remote = self.root / (module + ".git")
        git(self.root, "clone", "--quiet", "--bare", path, remote)
        self.remotes[module] = str(remote)
        (self.candidate / "setup" / (module + ".yml")).write_text("{}\n")
        rendered = self.candidate / "rendered" / module
        (rendered / ".github/workflows").mkdir(parents=True)
        (rendered / ".github/workflows/ci.yml").write_text("name: Fixture\n")
        os.chmod(rendered / ".github/workflows/ci.yml", 0o755)
        (rendered / ".github/hexalith-ci.json").write_text('{"accepted":true}\n')
        entries = [
            {"kind": "whole-dir", "path": ".github/workflows"},
            {"kind": "whole", "path": ".github/hexalith-ci.json"},
            {"kind": "gitlink", "path": "references/Hexalith.Builds", "buildsTag": TAG},
            {"kind": "gitmodules-section", "path": ".gitmodules", "submodulePath": "references/Hexalith.Builds", "url": "https://github.com/Hexalith/Hexalith.Builds.git"},
            {"kind": "json-superset", "path": ".claude/settings.json", "pointer": "/permissions/deny", "values": ["owned"]},
            {"kind": "marker-block", "path": "AGENTS.md", "text": "owned instructions\n"},
            {"kind": "absent-glob", "pattern": ".releaserc*"},
            {"kind": "absent-glob", "pattern": "**/Directory.Build.rsp"},
            {"kind": "absent-json", "path": "package.json", "selectors": [["scripts", "release"], ["devDependencies", "semantic-release"]]},
            {"kind": "absent-line", "path": ".husky/commit-msg", "pattern": "\\bcommitlint\\b"}]
        (self.candidate / "rendered" / (module + ".perimeter.json")).write_text(json.dumps({"schema": "hexalith.perimeter.v1", "entries": entries}) + "\n")

    def commit(self):
        git(self.candidate, "add", ".")
        git(self.candidate, "commit", "--quiet", "-m", "Candidate")
        self.sha = git(self.candidate, "rev-parse", "HEAD")
        if hasattr(self, "remote"):
            git(self.candidate, "push", "--quiet", self.remote, "HEAD:refs/heads/main")
        return self.sha

    def ref(self, module, revision=None):
        git(self.remote, "update-ref", "refs/heads/delivered/" + module, revision or self.accepted)

    def env(self, verdict=None, **extra):
        return os.environ | {"DELIVERY_DIRECTORY": str(self.directory), "GITHUB_OUTPUT": str(self.outputs),
            "GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd", "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": self.sha,
            "GITHUB_RUN_ID": "101", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_EVENT_NAME": "push",
            "DELIVERY_VERDICT": json.dumps(verdict if verdict is not None else {"global": True, "modules": sorted(self.modules)}),
            "CICD_TOKEN": "inert-cicd-token", "MODULE_TOKEN": "inert-module-token", **extra}

    def call(self, script, args, *, env=None):
        self.config_path.write_text(json.dumps(self.config))
        command = [sys.executable, "-I", str(Path(__file__).resolve()), "driver", str(ROOT / "tools" / script),
                   str(self.config_path), *args]
        result = subprocess.run(command, env=env or self.env(), capture_output=True)
        if result.stdout or result.stderr:
            raise AssertionError("entrypoint leaked output: " + repr(result.stdout + result.stderr))
        return result.returncode

    def select(self, verdict=None, **extra):
        return self.call("delivery_bootstrap.py", ["select"], env=self.env(verdict, **extra))

    def operation(self, operation, slot=None, **extra):
        args = [operation, "--state", str(self.directory / "state.json")]
        if slot is not None:
            args += ["--slot", str(slot)]
        selected = self.directory / "selected/tools/deliver.py"
        return self.call(str(selected) if selected.exists() else "deliver.py", args, env=self.env(**extra))

    def report(self):
        return json.loads((self.directory / "report/delivery.json").read_bytes())

    def deliver(self, verdict=None, **extra):
        self.select(verdict, **extra)
        self.operation("initialize", **extra)
        state = json.loads((self.directory / "state.json").read_bytes())
        for slot in range(1, len(state["slots"]) + 1):
            self.operation("module", slot, **extra)
        return self.operation("finalize", **extra)


def fixture_transport(rt, config):
    class API:
        def __init__(self):
            self.calls = []

        def get(self, path, token=None, *, absent=False):
            self.calls.append(path)
            if path in config["api"]:
                value = config["api"][path]
                if isinstance(value, dict) and "error" in value:
                    raise rt.DeliveryError(value["error"])
                return value
            if path.startswith("/repos/Hexalith/Hexalith.Builds/"):
                tail = path.split("Hexalith.Builds/", 1)[1]
                if tail.startswith("releases/tags/"):
                    return {"tag_name": TAG, "draft": False, "immutable": not config["bad_release"],
                            "published_at": "2026-11-01T00:00:00Z", "author": {"login": "github-actions[bot]"}}
                if tail == "git/ref/tags/" + TAG:
                    return {"ref": "refs/tags/" + TAG, "object": {"type": "commit", "sha": config["release"]}}
                if tail == "git/ref/heads/main":
                    return {"ref": "refs/heads/main", "object": {"type": "commit", "sha": config["release"]}}
                if tail.startswith("compare/"):
                    return {"status": "identical", "base_commit": {"sha": config["release"]}, "merge_base_commit": {"sha": config["release"]}}
            for repository in config["modules"]:
                prefix = "/repos/Hexalith/" + repository
                if path.startswith(prefix):
                    if repository in config["fail_app"]:
                        raise rt.DeliveryError("fixture App administration denied")
                    tail = path[len(prefix):]
                    if not tail:
                        return {"full_name": "Hexalith/" + repository, "default_branch": "main"}
                    if tail.startswith("/rulesets/"):
                        branch = tail.endswith("/1")
                        return {"id": 1 if branch else 2, "target": "branch" if branch else "tag", "enforcement": "active",
                                "conditions": {"ref_name": {"include": ["refs/heads/main" if branch else "refs/tags/v*"], "exclude": []}},
                                "rules": [{"type": "deletion"}, {"type": "non_fast_forward" if branch else "update"}],
                                "bypass_actors": [{"fixture": "ignored"}]}
                    if tail == "/actions/permissions/artifact-and-log-retention":
                        return {"days": 90}
                    if tail == "/code-scanning/default-setup":
                        return {"state": "not-configured"}
                    if tail == "/automated-security-fixes" and absent:
                        return None
            raise rt.DeliveryError("unmocked HTTP boundary: " + path)

        def pages(self, path, token=None, *, field=None):
            if path in config["api"]:
                return self.get(path, token)
            if path == "/installation/repositories":
                return [{"full_name": "Hexalith/" + r} for r in config["modules"]]
            if path.endswith("/rulesets?includes_parents=true"):
                return [{"id": 2}, {"id": 1}]
            if path.endswith("actions/workflows") or path.endswith("actions/runs?branch=main"):
                return []
            raise rt.DeliveryError("unmocked paginated HTTP boundary")

    class Transport(rt.Transport):
        def __init__(self, budget=None):
            super().__init__(budget, API())
            self.count = {}

        def remote(self, repository):
            return Path(config["cicd"] if repository == rt.CICD else config["builds"] if repository == rt.BUILDS
                        else config["modules"][repository]).as_uri()

        def push(self, target, repository, commit, token):
            count = self.count.get(repository, 0)
            self.count[repository] = count + 1
            if repository in config["push_fail"]:
                return 128, b""
            if count < config["races"].get(repository, 0):
                remote = Path(config["modules"][repository])
                previous = git(remote, "rev-parse", "refs/heads/main")
                tree = git(remote, "rev-parse", previous + "^{tree}")
                newer = git(remote, "commit-tree", tree, "-p", previous, data=f"Concurrent product {count}\n".encode())
                git(remote, "update-ref", "refs/heads/main", newer)
            return super().push(target, repository, commit, token)

        def advance(self, target, repository, candidate, token):
            if repository in config["ref_races"]:
                git(Path(config["cicd"]), "update-ref", "refs/heads/delivered/" + repository, config["ref_races"][repository])
                return 1, b"!\tref:ref\t[rejected] (non-fast-forward)\n"
            return super().advance(target, repository, candidate, token)

    return Transport


def driver():
    script, configuration, *args = sys.argv[2:]
    config = json.loads(Path(configuration).read_bytes())
    module = load(Path(script), "_delivery_executed_entrypoint")
    rt = module.rt
    original = rt.environment
    def fixture_environment():
        env = original()
        index = int(env["GIT_CONFIG_COUNT"])
        env.update(GIT_CONFIG_COUNT=str(index + 1))
        env[f"GIT_CONFIG_KEY_{index}"] = "protocol.file.allow"
        env[f"GIT_CONFIG_VALUE_{index}"] = "always"
        return env
    rt.environment = fixture_environment
    Transport = fixture_transport(rt, config)
    rt.Transport = Transport
    if Path(script).name == "delivery_bootstrap.py":
        original_run = subprocess.run
        def nested(command, *positional, **keywords):
            if (isinstance(command, list) and len(command) > 2 and
                    str(command[2]).endswith("/selected/tools/deliver.py")):
                command = [sys.executable, "-I", str(Path(__file__).resolve()), "driver", command[2], configuration, *command[3:]]
            return original_run(command, *positional, **keywords)
        module.subprocess.run = nested
    try:
        if Path(script).name == "delivery_bootstrap.py":
            result = module.main(args, transport=Transport())
        else:
            result = module.main(args, transport=Transport())
    except Exception:
        result = 2
    raise SystemExit(result)


if __name__ == "__main__" and sys.argv[1:2] == ["driver"]:
    driver()
