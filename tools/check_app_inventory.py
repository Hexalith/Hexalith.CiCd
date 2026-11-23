#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Offline review boundary for every parent workflow using the CiCd App.

The policy is reviewed source, never regenerated or accepted by this checker.
Token inputs are readable allowlist entries. Semantic digests bind the remaining
selector context and trusted controllers, so unchanged expressions cannot conceal
changed producers. This proves source inventory, not hosted settings or grants.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys

sys.dont_write_bytecode = True
_SPEC = importlib.util.spec_from_file_location("_app_inventory_renderer", Path(__file__).with_name("render.py"))
renderer = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = renderer
_SPEC.loader.exec_module(renderer)
InventoryError = renderer.RenderError
ROOT = Path(__file__).resolve().parents[1]
POLICY = "tools/app-workflow-policy.json"
KEY = "HEXALITH_CICD_APP_PRIVATE_KEY"
ENVIRONMENT = "cicd-app"
MAX_BYTES = 2 * 1024 * 1024
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def require(condition, source, message):
    if not condition:
        raise InventoryError(f"{source}: {message}")


def read(project, relative):
    relative_path = PurePosixPath(relative)
    require(not relative_path.is_absolute() and ".." not in relative_path.parts
            and relative_path.as_posix() == relative, relative, "expected a canonical repository-relative path")
    path = renderer.safe_path(project, relative)
    require(path.is_file() and not path.is_symlink(), relative, "expected a regular file")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    require(len(data) <= MAX_BYTES, relative, "input exceeds 2 MiB")
    return data


def semantic_digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def contains(value, signal):
    # GitHub environment and secret names are case-insensitive. Discovery must
    # be at least as broad; exact reviewed spelling is still compared below.
    signal = signal.casefold()
    if isinstance(value, dict):
        return any(signal in key.casefold() or contains(item, signal) for key, item in value.items())
    if isinstance(value, list):
        return any(contains(item, signal) for item in value)
    return isinstance(value, str) and signal in value.casefold()


def consumer(job):
    environment = job.get("environment")
    environment_name = environment.get("name") if isinstance(environment, dict) else environment
    # An unreviewed dynamic name could select cicd-app without naming it.
    return ((isinstance(environment_name, str)
             and (environment_name.casefold() == ENVIRONMENT or "${{" in environment_name))
            or contains(job, KEY) or computed_secret_index(job))


def computed_secret_index(value):
    """An unresolved secrets[index] might select the App key at runtime.

    Literal unrelated secret names remain harmless. GitHub expression strings
    use single quotes, escaping an embedded quote as two consecutive quotes.
    """
    if isinstance(value, dict):
        return any(computed_secret_index(key) or computed_secret_index(item) for key, item in value.items())
    if isinstance(value, list):
        return any(computed_secret_index(item) for item in value)
    if not isinstance(value, str):
        return False
    for match in re.finditer(r"\bsecrets\s*\[\s*", value, re.IGNORECASE):
        if re.match(r"'(?:[^']|'')*'\s*\]", value[match.end():]) is None:
            return True
    return False


def fields(value, expected, source):
    require(isinstance(value, dict) and set(value) == set(expected), source,
            "expected fields " + ", ".join(expected))


def policy_document(project):
    value = renderer.json_document(read(project, POLICY), POLICY)
    fields(value, ("schema", "reviewed_revision", "selector_sources", "workflows"), POLICY)
    require(value["schema"] == "hexalith.cicd-app-inventory.v1", POLICY, "unsupported schema")
    require(isinstance(value["reviewed_revision"], str)
            and re.fullmatch(r"[0-9a-f]{40}", value["reviewed_revision"]), POLICY, "invalid reviewed revision")
    require(isinstance(value["selector_sources"], dict) and value["selector_sources"], POLICY,
            "expected trusted selector sources")
    for path, entry in value["selector_sources"].items():
        fields(entry, ("sha256", "bound"), f"{POLICY}/{path}")
        require(path.startswith("tools/") and PurePosixPath(path).suffix == ".py", POLICY,
                "selector source must be a tools Python file")
        require(isinstance(entry["sha256"], str) and DIGEST.fullmatch(entry["sha256"])
                and isinstance(entry["bound"], str) and entry["bound"], path, "invalid selector boundary")
    require(isinstance(value["workflows"], dict) and value["workflows"], POLICY, "expected workflow allowlist")
    for path, workflow in value["workflows"].items():
        require(path.startswith(".github/workflows/") and len(PurePosixPath(path).parts) == 3
                and PurePosixPath(path).suffix in (".yml", ".yaml"), POLICY, "invalid workflow path")
        fields(workflow, ("context", "context_jobs", "jobs"), f"{POLICY}/{path}")
        require(isinstance(workflow["context"], dict) and "jobs" not in workflow["context"], path,
                "expected workflow context without jobs")
        require(isinstance(workflow["context_jobs"], dict), path, "expected dependency job digests")
        for name, digest in workflow["context_jobs"].items():
            require(isinstance(digest, str) and DIGEST.fullmatch(digest), f"{path}/{name}", "invalid dependency digest")
        require(isinstance(workflow["jobs"], dict) and workflow["jobs"], path, "expected privileged jobs")
        for name, job in workflow["jobs"].items():
            location = f"{POLICY}/{path}/{name}"
            fields(job, ("boundary", "tokens", "context_steps"), location)
            require(isinstance(job["boundary"], dict) and job["boundary"].get("environment") == ENVIRONMENT
                    and "steps" not in job["boundary"], location, "expected cicd-app job boundary")
            require(isinstance(job["tokens"], list) and job["tokens"], location, "expected token allowlist")
            require(isinstance(job["context_steps"], list), location, "expected selector step context")
            indices, identities = set(), set()
            for kind, entries in (("token", job["tokens"]), ("context", job["context_steps"])):
                for entry in entries:
                    fields(entry, ("index", "step") if kind == "token" else ("index", "identity", "sha256"), location)
                    index = entry["index"]
                    require(type(index) is int and index >= 0 and index not in indices, location,
                            "step indices must be unique nonnegative integers")
                    indices.add(index)
                    if kind == "token":
                        step = entry["step"]
                        require(isinstance(step, dict) and isinstance(step.get("id"), str)
                                and step["id"] and step["id"] not in identities, location, "invalid token step identity")
                        identities.add(step["id"])
                        inputs = step.get("with")
                        require(isinstance(inputs, dict) and inputs.get("owner") == "Hexalith"
                                and isinstance(inputs.get("repositories"), str) and inputs["repositories"]
                                and inputs.get("private-key") == "${{ secrets." + KEY + " }}"
                                and str(step.get("uses", "")).startswith("actions/create-github-app-token@")
                                and any(key.startswith("permission-") for key in inputs), location,
                                "token must have explicit owner, repositories, key and permissions")
                    else:
                        require(isinstance(entry["identity"], str) and isinstance(entry["sha256"], str)
                                and DIGEST.fullmatch(entry["sha256"]), location, "invalid context step digest")
            require(indices == set(range(len(indices))), location, "step allowlist must be contiguous")
    return value


def compare(actual, expected, source):
    """Report the first changed boundary without printing any input value."""
    if type(actual) is not type(expected):
        raise InventoryError(f"{source}: differs from reviewed policy (type)")
    if isinstance(expected, dict):
        for key in sorted(actual.keys() | expected.keys()):
            require(key in actual and key in expected, f"{source}/{key}", "differs from reviewed policy (field)")
            compare(actual[key], expected[key], f"{source}/{key}")
    elif isinstance(expected, list):
        require(len(actual) == len(expected), source, "differs from reviewed policy (length)")
        for index, (item, reviewed) in enumerate(zip(actual, expected)):
            compare(item, reviewed, f"{source}/{index}")
    else:
        require(actual == expected, source, "differs from reviewed policy")


def check(project: Path):
    project = project.resolve()
    policy = policy_document(project)
    directory = renderer.safe_path(project, ".github/workflows")
    require(directory.is_dir(), ".github/workflows", "workflow directory missing")
    observed, token_count = set(), 0
    for path in sorted(directory.iterdir()):
        if path.suffix.casefold() not in (".yml", ".yaml"):
            continue
        source = path.relative_to(project).as_posix()
        document = renderer.yaml_document(read(project, source), source)
        require(isinstance(document, dict) and isinstance(document.get("jobs"), dict)
                and document["jobs"], source, "expected workflow and jobs mapping")
        jobs = document["jobs"]
        context = {key: value for key, value in document.items() if key != "jobs"}
        require(not contains(context, KEY) and not computed_secret_index(context), source,
                "App key reference or computed secret index outside a reviewed job")
        selected = {}
        for name, job in jobs.items():
            require(isinstance(job, dict), f"{source}/{name}", "expected job mapping")
            if "uses" in job:
                # A callee can select its own cicd-app environment even without
                # inherited secrets. Only an explicitly reviewed dependency
                # context can authorize such a call; the present inventory has none.
                approved_digest = policy["workflows"].get(source, {}).get("context_jobs", {}).get(name)
                require(approved_digest == semantic_digest(job), f"{source}/{name}",
                        "unreviewed reusable workflow call may select the App environment")
            if consumer(job):
                selected[name] = job
        if not selected:
            require(source not in policy["workflows"], source, "reviewed App consumers missing")
            continue
        require(source in policy["workflows"], source, "unreviewed App consumer workflow")
        reviewed = policy["workflows"][source]
        observed.add(source)
        compare(context, reviewed["context"], source + "/context")
        for name in sorted(selected.keys() | reviewed["jobs"].keys()):
            location = f"{source}/{name}"
            require(name in selected and name in reviewed["jobs"], location, "unreviewed or missing App consumer job")
            job, approved = selected[name], reviewed["jobs"][name]
            compare({key: value for key, value in job.items() if key != "steps"}, approved["boundary"], location)
            steps = job.get("steps")
            require(isinstance(steps, list), location, "expected explicit steps")
            require(len(steps) == len(approved["tokens"]) + len(approved["context_steps"]), location,
                    "step inventory differs from reviewed policy")
            ids = [step.get("id") for step in steps if isinstance(step, dict) and "id" in step]
            require(all(isinstance(item, str) and item for item in ids) and len(ids) == len(set(ids)), location,
                    "duplicate or invalid step identity")
            for entry in approved["tokens"]:
                identity = entry["step"]["id"]
                compare(steps[entry["index"]], entry["step"], f"{location}/{identity}")
                token_count += 1
            for entry in approved["context_steps"]:
                step = steps[entry["index"]]
                require(isinstance(step, dict) and semantic_digest(step) == entry["sha256"],
                        f"{location}/{entry['identity']}", "selector/consumer context differs from reviewed policy")
        for name, digest in reviewed["context_jobs"].items():
            require(name in jobs and semantic_digest(jobs[name]) == digest, f"{source}/{name}",
                    "dependency job context differs from reviewed policy")
        # A consumer condition or selector can read any transitive dependency's
        # outputs, so a renewal must bind the complete needs closure.
        bound, pending, visited = set(reviewed["jobs"]) | set(reviewed["context_jobs"]), list(reviewed["jobs"]), set()
        while pending:
            name = pending.pop()
            if name in visited:
                continue
            visited.add(name)
            dependencies = jobs[name].get("needs", [])
            dependencies = [dependencies] if isinstance(dependencies, str) else dependencies
            require(isinstance(dependencies, list) and all(isinstance(item, str) for item in dependencies),
                    f"{source}/{name}/needs", "expected job dependency names")
            for dependency in dependencies:
                require(dependency in bound, f"{source}/{dependency}",
                        "dependency of an App consumer is not bound by reviewed policy")
                pending.append(dependency)
    compare(sorted(observed), sorted(policy["workflows"]), "workflow inventory")
    for path, entry in policy["selector_sources"].items():
        require(hashlib.sha256(read(project, path)).hexdigest() == entry["sha256"], path,
                "trusted selector source differs from reviewed policy")
    return {"workflows": len(observed), "jobs": sum(len(item["jobs"]) for item in policy["workflows"].values()),
            "tokens": token_count}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        counts = check(args.project_root)
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        print(renderer.diagnostic(f"App inventory: {error}"), file=sys.stderr)
        return 1
    print("App inventory: " + ", ".join(f"{number} {kind}" for kind, number in counts.items()) + " reviewed; hosted state unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
