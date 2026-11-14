"""Nonexecuting, bounded contracts for nightly Builds bumps.

The candidate is a JSON Git object envelope, never a patch or executable
archive. The writer trusts its own main/tag/schema observations only.
"""
from __future__ import annotations

import base64
import copy
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nightly_runtime as rt
from delivery_runtime import object_identity

SCHEMA = "hexalith.nightly-bump.v1"
KEYS = {"schema", "identity", "base", "candidate", "old", "new", "objects"}
MAX_OBJECTS = 4096
SUBJECT = re.compile(r"build\(cicd\): bump Builds to (v[0-9]+\.[0-9]+\.[0-9]+)\Z")
NIGHT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


def version(tag):
    if not isinstance(tag, str) or not rt.TAG.fullmatch(tag) or len(tag) > 100:
        raise rt.NightlyError("expected exact stable Builds tag: " + rt.clean(tag))
    return tuple(map(int, tag[1:].split(".")))


def skip_policy(data):
    try:
        text = data.decode("utf-8")
    except UnicodeError:
        raise rt.NightlyError("builds-skip: invalid UTF-8") from None
    result = set()
    for line, tag in enumerate(text.splitlines(), 1):
        if not tag:
            continue
        try:
            version(tag)
        except ValueError:
            raise rt.NightlyError(f"builds-skip:{line}: expected one stable tag per line") from None
        if tag in result:
            raise rt.NightlyError(f"builds-skip:{line}: duplicate tag {tag}")
        result.add(tag)
    return result


def policy(git, base):
    tag = git.blob(base, "builds-version").decode("utf-8").removesuffix("\n")
    version(tag)
    entries = git.items(base, "builds-skip")
    skipped = skip_policy(git.blob(base, "builds-skip")) if "builds-skip" in entries else set()
    return tag, skipped


def identity(environment, api, token=None):
    if environment.get("NIGHTLY_CANCELLED") == "true":
        raise rt.NightlyError("nightly cancelled; bump operations suppressed")
    if environment.get("GITHUB_REPOSITORY") != "Hexalith/" + rt.CICD or environment.get("GITHUB_REF") != "refs/heads/main":
        raise rt.NightlyError("nightly bump requires CiCd main")
    source = rt.sha(environment.get("GITHUB_SHA"))
    try:
        run_id, attempt = (rt.positive(int(environment[key])) for key in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT"))
    except (KeyError, ValueError):
        raise rt.NightlyError("nightly bump run identity unavailable") from None
    run = api.get(f"/repos/Hexalith/{rt.CICD}/actions/runs/{run_id}", token)
    if (not isinstance(run, dict) or type(run.get("id")) is not int or run.get("id") != run_id
            or type(run.get("run_attempt")) is not int or run.get("run_attempt") != attempt
            or run.get("head_sha") != source or run.get("head_branch") != "main"
            or run.get("path") != ".github/workflows/nightly.yml"
            or run.get("event") not in {"schedule", "workflow_dispatch"}
            or run.get("repository", {}).get("full_name") != "Hexalith/" + rt.CICD):
        raise rt.NightlyError("nightly bump run/attempt/controller source mismatch")
    night = rt.timestamp(run.get("created_at")).date().isoformat()
    return {"runId": run_id, "attempt": attempt, "source": source, "night": night}


def validate_identity(value):
    if not isinstance(value, dict) or set(value) != {"runId", "attempt", "source", "night"}:
        raise rt.NightlyError("bump identity fields mismatch")
    rt.positive(value["runId"])
    rt.positive(value["attempt"])
    rt.sha(value["source"])
    if not isinstance(value["night"], str) or not NIGHT.fullmatch(value["night"]):
        raise rt.NightlyError("bump UTC night malformed")
    try:
        datetime.strptime(value["night"], "%Y-%m-%d")
    except ValueError:
        raise rt.NightlyError("bump UTC night malformed") from None


def message(tag, night):
    version(tag)
    validate_identity({"runId": 1, "attempt": 1, "source": "0" * 40, "night": night})
    return f"build(cicd): bump Builds to {tag}\n\nhexalith-nightly-bump: {night}\n".encode()


def already_bumped(git, base, night):
    # Parse actual commit objects, so a body containing delimiters cannot make
    # an unreadable history look like absence of the durable nightly marker.
    ids = git.run("rev-list", "--max-count=100001", rt.sha(base)).decode().splitlines()
    if len(ids) > 100000:
        raise rt.NightlyError("nightly bump history verification limit exceeded")
    payload = git.run("cat-file", "--batch", data="".join(rt.sha(oid) + "\n" for oid in ids).encode())
    import io
    stream = io.BytesIO(payload)
    found = False
    for oid in ids:
        header = stream.readline().decode("ascii").split()
        if len(header) != 3 or header[:2] != [oid, "commit"] or not header[2].isdigit():
            raise rt.NightlyError("nightly bump history is unreadable")
        raw = stream.read(int(header[2]))
        if len(raw) != int(header[2]) or stream.read(1) != b"\n" or b"\n\n" not in raw:
            raise rt.NightlyError("nightly bump history is incomplete")
        body = raw.split(b"\n\n", 1)[1]
        lines = body.decode("utf-8", "strict").splitlines()
        if lines and SUBJECT.fullmatch(lines[0]) and "hexalith-nightly-bump: " + night in lines[1:]:
            found = True
    if stream.read(1):
        raise rt.NightlyError("nightly bump history framing mismatch")
    return found


class Transport(rt.Transport):
    def main(self, git):
        git.run("fetch", "--no-tags", "--no-recurse-submodules", self.remote(rt.CICD),
                "+refs/heads/main:refs/remotes/origin/main")
        return git.resolve("refs/remotes/origin/main^{commit}")

    def tag(self, git, tag):
        version(tag)
        path = f"/repos/Hexalith/{rt.BUILDS}/"
        ref = self.api.get(path + "git/ref/tags/" + tag)
        if not isinstance(ref, dict) or ref.get("ref") != "refs/tags/" + tag:
            raise rt.NightlyError(f"Builds {tag}: remote tag identity mismatch")
        kind, raw = object_identity(ref)
        source, seen = raw, set()
        while kind == "tag":
            if source in seen or len(seen) >= 16:
                raise rt.NightlyError(f"Builds {tag}: annotated tag cycle/depth")
            seen.add(source)
            obj = self.api.get(path + "git/tags/" + source)
            if not isinstance(obj, dict) or obj.get("sha") != source:
                raise rt.NightlyError(f"Builds {tag}: annotated tag identity mismatch")
            kind, source = object_identity(obj)
        git.run("fetch", "--no-tags", "--no-recurse-submodules", self.remote(rt.BUILDS),
                "+refs/heads/main:refs/remotes/origin/main", f"+refs/tags/{tag}:refs/tags/{tag}")
        if git.resolve("refs/tags/" + tag) != raw or git.resolve("refs/tags/" + tag + "^{commit}") != source:
            raise rt.NightlyError(f"Builds {tag}: remote/local tag or peeled commit mismatch")
        return {"tag": tag, "object": raw, "commit": source}

    def select(self, git, current, skipped):
        major = version(current)[0]
        releases = self.api.pages(f"/repos/Hexalith/{rt.BUILDS}/releases")
        candidates, seen = [], set()
        for release in releases:
            if not isinstance(release, dict):
                raise rt.NightlyError("Builds release inventory contains nonobject")
            release_id = rt.positive(release.get("id"))
            if release_id in seen:
                raise rt.NightlyError("Builds release inventory contains duplicate identity")
            seen.add(release_id)
            tag = release.get("tag_name")
            if not isinstance(tag, str) or not rt.TAG.fullmatch(tag):
                continue
            if version(tag)[0] != major or tag in skipped:
                continue
            if (release.get("draft") is not False or release.get("immutable") is not True
                    or release.get("author", {}).get("login") != "github-actions[bot]"):
                continue
            rt.timestamp(release.get("published_at"))
            if tag in [item[0] for item in candidates]:
                raise rt.NightlyError(f"Builds {tag}: ambiguous published release inventory")
            candidates.append((tag, release))
        for tag, _ in sorted(candidates, key=lambda item: version(item[0]), reverse=True):
            selected = self.tag(git, tag)
            main = self.api.get(f"/repos/Hexalith/{rt.BUILDS}/git/ref/heads/main")
            if not isinstance(main, dict) or main.get("ref") != "refs/heads/main":
                raise rt.NightlyError("Builds main remote identity mismatch")
            kind, main_sha = object_identity(main)
            if kind != "commit" or git.resolve("refs/remotes/origin/main^{commit}") != main_sha:
                raise rt.NightlyError(f"Builds {tag}: local/remote main verification raced")
            if git.ancestor(selected["commit"], main_sha):
                return selected
        raise rt.NightlyError("no acceptable unskipped Builds tag in current major")


def object_id(kind, data):
    return hashlib.sha1(kind.encode("ascii") + b" " + str(len(data)).encode() + b"\0" + data,
                        usedforsecurity=False).hexdigest()


def canonical_tree(data):
    """Git's reader tolerates duplicate tree names; envelopes must not."""
    offset, names, ordering = 0, set(), []
    while offset < len(data):
        space, nul = data.find(b" ", offset), data.find(b"\0", offset)
        if space <= offset or nul <= space or nul + 21 > len(data):
            raise rt.NightlyError("candidate Git tree framing invalid")
        mode, name = data[offset:space], data[space + 1:nul]
        if (mode not in {b"40000", b"100644", b"100755", b"120000", b"160000"}
                or name in names or name in {b"", b".", b".."} or name.lower() == b".git" or b"/" in name):
            raise rt.NightlyError("candidate Git tree duplicate or noncanonical entry")
        names.add(name)
        ordering.append(name + (b"/" if mode == b"40000" else b""))
        offset = nul + 21
    if ordering != sorted(ordering):
        raise rt.NightlyError("candidate Git tree entry order is noncanonical")


def envelope(git, expected, base, candidate, old, new):
    ids = git.run("rev-list", "--objects", "--no-object-names", rt.sha(candidate), "^" + rt.sha(base)).decode().splitlines()
    if len(ids) > MAX_OBJECTS:
        raise rt.NightlyError("candidate Git object count limit exceeded")
    objects = []
    for oid in ids:
        kind = git.run("cat-file", "-t", rt.sha(oid)).decode().strip()
        if kind not in {"commit", "tree", "blob"}:
            raise rt.NightlyError("candidate contains unsupported Git object")
        raw = git.run("cat-file", kind, oid)
        if any(secret.encode() in raw for secret in rt.delivery._SECRETS if secret):
            raise rt.NightlyError("candidate object contains credential material")
        objects.append({"id": oid, "type": kind, "data": base64.b64encode(raw).decode("ascii")})
    result = {"schema": SCHEMA, "identity": expected, "base": base, "candidate": candidate,
              "old": old, "new": new, "objects": objects}
    validate_envelope(result, expected)
    # Same bound as the artifact's exact JSON member and persisted state.
    import json
    if len(json.dumps(result).encode()) > rt.MAX_JSON:
        raise rt.NightlyError("candidate Git object envelope exceeds JSON limit")
    return result


def validate_envelope(value, expected=None):
    if not isinstance(value, dict) or set(value) != KEYS or value["schema"] != SCHEMA:
        raise rt.NightlyError("unsupported bump candidate handoff")
    validate_identity(value["identity"])
    if expected is not None and value["identity"] != expected:
        raise rt.NightlyError("bump candidate run/attempt/controller identity mismatch")
    for key in ("base", "candidate"):
        rt.sha(value[key])
    for key in ("old", "new"):
        item = value[key]
        if not isinstance(item, dict) or set(item) != {"tag", "object", "commit"}:
            raise rt.NightlyError("bump Builds identity fields mismatch")
        version(item["tag"])
        rt.sha(item["object"])
        rt.sha(item["commit"])
    if (version(value["old"]["tag"])[0] != version(value["new"]["tag"])[0]
            or version(value["new"]["tag"]) <= version(value["old"]["tag"])):
        raise rt.NightlyError("bump must advance within the current major")
    objects = value["objects"]
    if not isinstance(objects, list) or not 1 <= len(objects) <= MAX_OBJECTS:
        raise rt.NightlyError("candidate Git object count limit exceeded")
    seen = set()
    for item in objects:
        if not isinstance(item, dict) or set(item) != {"id", "type", "data"}:
            raise rt.NightlyError("candidate Git object fields mismatch")
        oid = rt.sha(item["id"])
        if oid in seen or item["type"] not in {"commit", "tree", "blob"} or not isinstance(item["data"], str):
            raise rt.NightlyError("candidate duplicate or unsupported Git object")
        seen.add(oid)
        try:
            data = base64.b64decode(item["data"], validate=True)
        except (ValueError, TypeError):
            raise rt.NightlyError("candidate Git object base64 invalid") from None
        if base64.b64encode(data).decode() != item["data"] or object_id(item["type"], data) != oid:
            raise rt.NightlyError("candidate Git object hash mismatch")
        if item["type"] == "tree":
            canonical_tree(data)
    if value["candidate"] not in seen:
        raise rt.NightlyError("candidate commit is absent from Git object envelope")
    return value


def reconstruct(git, value, expected):
    validate_envelope(value, expected)
    for item in value["objects"]:
        raw = base64.b64decode(item["data"], validate=True)
        actual = git.run("hash-object", "-w", "-t", item["type"], "--stdin", data=raw).decode().strip()
        if actual != item["id"]:
            raise rt.NightlyError("reconstructed candidate Git identity mismatch")
    candidate = value["candidate"]
    if git.resolve(candidate + "^{commit}") != candidate:
        raise rt.NightlyError("candidate must be a commit object")
    raw = git.run("cat-file", "commit", candidate)
    headers, body = raw.split(b"\n\n", 1)
    if [line.split(b" ", 1)[0] for line in headers.splitlines()] != [b"tree", b"parent", b"author", b"committer"]:
        raise rt.NightlyError("candidate commit headers are noncanonical")
    parents = [line[7:].decode("ascii") for line in headers.splitlines() if line.startswith(b"parent ")]
    if parents != [value["base"]] or body != message(value["new"]["tag"], expected["night"]):
        raise rt.NightlyError("candidate parent/subject/night marker mismatch")
    if git.run("rev-list", "--count", candidate, "^" + value["base"]).strip() != b"1":
        raise rt.NightlyError("candidate must contain exactly one commit")
    return candidate


def local_reference(root, reference, seen):
    if not isinstance(reference, str) or not reference.startswith("#/") or reference in seen:
        raise rt.NightlyError("unsupported or recursive schema default reference")
    target = root
    try:
        for key in reference[2:].split("/"):
            target = target[key.replace("~1", "/").replace("~0", "~")]
    except (KeyError, TypeError):
        raise rt.NightlyError("unresolved schema default reference") from None
    if not isinstance(target, dict):
        raise rt.NightlyError("schema default reference must select an object")
    return target


def condition(value, schema, root, seen=()):
    """A deliberately bounded subset for renderer default branch selection.

    Unsupported predicates fail closed rather than guessing which default the
    renderer's full JSON Schema validator would choose.
    """
    if not isinstance(schema, dict) or set(schema) - {"$ref", "type", "const", "enum", "properties", "required", "allOf", "anyOf", "oneOf", "not"}:
        raise rt.NightlyError("unsupported schema default condition")
    if len(seen) > 64:
        raise rt.NightlyError("schema default condition depth exceeded")
    checks = []
    if "$ref" in schema:
        ref = schema["$ref"]
        checks.append(condition(value, local_reference(root, ref, seen), root, (*seen, ref)))
    if "type" in schema:
        kinds = {"object": type(value) is dict, "array": type(value) is list,
                 "string": type(value) is str, "boolean": type(value) is bool,
                 "integer": type(value) is int, "number": type(value) in {int, float}, "null": value is None}
        if schema["type"] not in kinds:
            raise rt.NightlyError("unsupported schema default condition type")
        checks.append(kinds[schema["type"]])
    if "const" in schema:
        checks.append(schema_equal(value, schema["const"]))
    if "enum" in schema:
        checks.append(any(schema_equal(value, item) for item in schema["enum"]))
    if "required" in schema and isinstance(value, dict):
        checks.append(all(key in value for key in schema["required"]))
    if "properties" in schema and isinstance(value, dict):
        checks.extend(condition(value[key], subschema, root, seen) for key, subschema in schema["properties"].items() if key in value)
    for key in ("allOf", "anyOf", "oneOf"):
        if key in schema:
            results = [condition(value, item, root, seen) for item in schema[key]]
            checks.append(all(results) if key == "allOf" else any(results) if key == "anyOf" else sum(results) == 1)
    if "not" in schema:
        checks.append(not condition(value, schema["not"], root, seen))
    return all(checks)


def schema_equal(left, right):
    # JSON Schema treats numbers mathematically, while booleans are distinct
    # even inside object/array constants (Python's native equality does not).
    if type(left) in {int, float} and type(right) in {int, float}:
        import math
        if not math.isfinite(left) or not math.isfinite(right):
            raise rt.NightlyError("nonfinite schema default condition")
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(schema_equal(child, right[key]) for key, child in left.items())
    if isinstance(left, list):
        return len(left) == len(right) and all(schema_equal(a, b) for a, b in zip(left, right))
    return left == right


def add_defaults(value, schema, root, seen=(), depth=0):
    """Verify the renderer's property-local default traversal as data only.

    This follows render.defaults' traversal/order; it does not validate configs
    or invent defaults for required properties, unions or container types.
    """
    if depth > 64 or not isinstance(schema, dict):
        raise rt.NightlyError("unsupported/deep schema default expression")
    if "$dynamicRef" in schema:
        raise rt.NightlyError("unsupported dynamic schema default reference")
    if "$ref" in schema:
        ref = schema["$ref"]
        add_defaults(value, local_reference(root, ref, seen), root, (*seen, ref), depth + 1)
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise rt.NightlyError("schema properties must be an object")
        for key, child in properties.items():
            source, refs = child, seen
            while "default" not in source and "$ref" in source:
                ref = source["$ref"]
                source = local_reference(root, ref, refs)
                refs = (*refs, ref)
            if key not in value and "default" in source:
                value[key] = copy.deepcopy(source["default"])
            if key in value:
                add_defaults(value[key], child, root, seen, depth + 1)
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            for key in value.keys() - properties.keys():
                add_defaults(value[key], additional, root, seen, depth + 1)
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for item in value:
            add_defaults(item, schema["items"], root, seen, depth + 1)
    for child in schema.get("allOf", []):
        add_defaults(value, child, root, seen, depth + 1)
    if "if" in schema:
        branch = "then" if condition(value, schema["if"], root) else "else"
        add_defaults(value, schema.get(branch, {}), root, seen, depth + 1)
    return value


def same_json(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_json(child, right[key]) for key, child in left.items())
    if isinstance(left, list):
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right


def verify_diff(git, value, builds):
    base, candidate = value["base"], value["candidate"]
    before, after = git.items(base), git.items(candidate)
    if before.keys() != after.keys():
        raise rt.NightlyError("candidate adds or removes committed paths")
    old, new = value["old"], value["new"]
    if git.blob(base, "builds-version") != (old["tag"] + "\n").encode():
        raise rt.NightlyError("builds-version: parent tag mismatch")
    if git.blob(candidate, "builds-version") != (new["tag"] + "\n").encode():
        raise rt.NightlyError("builds-version: candidate tag mismatch")
    schema = None
    for path, old_item in before.items():
        new_item = after[path]
        if old_item == new_item and not path.startswith("rendered/"):
            continue
        if old_item[:2] != new_item[:2] or old_item[:2] not in {("100644", "blob"), ("100755", "blob")}:
            raise rt.NightlyError(path + ": mode or object kind changed")
        if path == "builds-version":
            continue
        if not path.startswith("rendered/") or old_item[0] != "100644":
            raise rt.NightlyError(path + ": path outside existing regular rendered files")
        previous = git.blob(base, path).replace(old["tag"].encode(), new["tag"].encode()).replace(
            old["commit"].encode(), new["commit"].encode())
        actual = git.blob(candidate, path)
        if actual == previous:
            continue
        if not re.fullmatch(r"rendered/[A-Za-z0-9_.-]+/\.github/hexalith-ci\.json", path):
            raise rt.NightlyError(path + ": bytes differ beyond Builds tag/commit substitution")
        if schema is None:
            schemas = [key for key in builds.items(new["commit"], "schemas")
                       if re.fullmatch(r"schemas/hexalith\.ci\.v[0-9]+\.json", key)]
            if len(schemas) != 1:
                raise rt.NightlyError("new Builds tag must contain exactly one CI schema")
            schema = rt.json_read(builds.blob(new["commit"], schemas[0]))
        original, result = rt.json_read(previous), rt.json_read(actual)
        expected = add_defaults(copy.deepcopy(original), schema, schema)
        if not same_json(result, expected) or type(result) is not dict or same_json(result, original):
            raise rt.NightlyError(path + ": additions differ from tagged schema defaults")
        # Existing scalar types/values and array entries must remain exact.
        def retained(left, right):
            if type(left) is not type(right):
                return False
            if isinstance(left, dict):
                return all(key in right and retained(child, right[key]) for key, child in left.items())
            if isinstance(left, list):
                return len(left) == len(right) and all(retained(a, b) for a, b in zip(left, right))
            return left == right
        if not retained(original, result):
            raise rt.NightlyError(path + ": existing JSON values changed")


def output(path, values):
    if path:
        with Path(path).open("a", encoding="utf-8") as stream:
            for key, value in values.items():
                stream.write(key + "=" + str(value) + "\n")


def scratch(directory):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(directory), TMP=str(directory), TEMP=str(directory))
    tempfile.tempdir = str(directory)
