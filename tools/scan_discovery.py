"""Static action/script reachability. No module text is ever evaluated.

Coverage model. Recognized calls (interpreters, wrappers, sourcing, imports and
process APIs) refine resolution: they supply the exact working directory,
import roots and language. They never bound coverage:

1. Every literal (a shell word after quote removal, a Python string constant
   or an action YAML scalar) that names a tracked shell, PowerShell or Python
   script is included and traversed, resolved against every candidate base,
   whatever consumes it. So is every local Python module that a literal `-m`
   operand names or a literal `-c` operand imports.
2. Indirection that the model does not resolve fails with a source diagnostic.
"""
from __future__ import annotations

import ast
from collections import deque
from fnmatch import fnmatchcase
from functools import lru_cache
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shlex
import subprocess
import sys
import tomllib

import yaml

from delivery_runtime import DeliveryError, clean

FORMATS = {".yml": "yaml", ".yaml": "yaml", ".sh": "bash", ".bash": "bash",
           ".ps1": "powershell", ".psm1": "powershell", ".py": "python",
           ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
           ".ts": "typescript", ".mts": "typescript", ".cts": "typescript",
           ".jsx": "javascript", ".tsx": "typescript"}
SCRIPTS = {"bash", "powershell", "python", "javascript", "typescript"}
MAX_FILES = 2000
MAX_BYTES = 32 * 1024 * 1024
MAX_LITERAL = 4096
MAX_PYTHON_PROOF_NODES = 4096
# Environment variables that change which local Python sources are imported,
# an environment-file selector that can set them, and the PowerShell module and
# shell cd search paths, which redirect name-based module and directory lookup.
RESOLUTION = {"PYTHONPATH", "PYTHONHOME", "PYTHONSAFEPATH", "PYTHONUSERBASE", "UV_ENV_FILE", "PSMODULEPATH",
              "CDPATH", "NODE_PATH", "NODE_OPTIONS", "NPM_CONFIG_SCRIPT_SHELL", "NPM_CONFIG_NODE_OPTIONS",
              "NPM_CONFIG_USERCONFIG", "NPM_CONFIG_GLOBALCONFIG", "NPM_CONFIG_PREFIX", "NPM_CONFIG_WORKSPACE",
              "HEXALITH_CI_PYTHON"}
ENVIRON = {"os.environ", "os.environb"}
ENVIRON_WRITES = {"setdefault", "update", "__setitem__", "__ior__"}
MODULE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")
# Python modules that run tracked module files by convention: test discovery.
TEST_RUNNERS = {"pytest": "pytest", "py.test": "pytest", "unittest": "unittest", "nose2": "nose2"}
# Commands that execute their operand after this many fixed positional values.
WRAPPERS = {"env": 0, "exec": 0, "command": 0, "builtin": 0, "coproc": 0, "time": 0, "nohup": 0, "nice": 0,
            "sudo": 0, "doas": 0, "setsid": 0, "stdbuf": 0, "ionice": 0, "unbuffer": 0, "xargs": 0,
            "timeout": 0, "flock": 1, "chrt": 1}
TIMEOUT_DURATION = r"[0-9]+(?:\.[0-9]+)?[smhd]?"
DOTNET_BUILD_OPERATIONS = ("build", "pack", "restore", "msbuild")
# These Docker forms manage image data and stopped containers without running
# a container. Match the literal operation and option positions in argv.
DOCKER_DATA_OPERATIONS = (
    ("docker", "pull", "--platform", "linux/amd64", None),
    ("docker", "create", "--network", "none", None, "/bin/true"),
    ("docker", "cp", None, None),
    ("docker", "rm", None),
)
SIMPLE_SHELL_PARAMETER = r"\$(?:\{[A-Za-z_]\w*\}|[A-Za-z_]\w*)"
BASH_ENUM_ARGUMENT_GUARD = (
    r'(?P<option>[a-z][a-z0-9_]*)="\$\{1-[A-Za-z0-9_-]+\}"\n'
    r'if \(\( \$# > 1 \)\) \|\| \[\[ "\$(?P=option)" != [A-Za-z0-9_-]+'
    r' && "\$(?P=option)" != [A-Za-z0-9_-]+ \]\]; then\n'
    r'[ \t]+echo "[A-Za-z0-9_./: |\[\]-]+" >&2\n'
    r'[ \t]+exit [1-9][0-9]?\nfi\n'
)
SOURCE_RELATIVE_PROLOGUE = re.compile(
    r'\A#!/usr/bin/env bash\nset -euo pipefail\n(?:[ \t]*(?:#[^\n]*)?\n)*'
    rf'(?:(?P<guard>{BASH_ENUM_ARGUMENT_GUARD})(?:[ \t]*(?:#[^\n]*)?\n)*)?'
    r'(?P<assignment>(?P<root>[a-z][a-z0-9_]*)="\$\(cd "\$\(dirname "\$\{BASH_SOURCE\[0\]\}"\)'
    r'(?P<parents>(?:/\.\.){1,8})" && pwd\)")\n'
    r'(?P<scratch>[a-z][a-z0-9_]*)="\$\(mktemp -d\)"\n'
    r'''trap 'rm -rf "\$(?P=scratch)"' EXIT\ncd "\$(?P=root)"$''', re.M)
BASH_LITERAL_ARRAY_START = re.compile(r"[ \t]*(?P<name>[a-z][a-z0-9_]*)=\(")
BASH_LITERAL_ARRAY_LINE = re.compile(r"[A-Za-z0-9_./ \t-]*(?P<close>\)[ \t]*)?")
# After the stdin marker Python treats these words as arguments to the body.
# Quoted parameter expansion cannot add shell words or redirect the input.
PYTHON_HEREDOC = re.compile(
    r"""[ \t]*python(?:3(?:\.\d+)?)?[ \t]+-"""
    rf"""(?:[ \t]+(?:[A-Za-z0-9_./-]+|"{SIMPLE_SHELL_PARAMETER}"))*"""
    r"""[ \t]+<<[ \t]*(?P<quote>['"])[A-Za-z_]\w*(?P=quote)[ \t]*""")
# Words that only introduce the next command of a list, condition or block.
KEYWORDS = {"then", "do", "else", "if", "elif", "while", "until", "!", "&", "{", "}", "try", "catch", "finally"}
SHELLS = {"bash": "bash", "sh": "bash", "dash": "bash", "zsh": "bash", "ksh": "bash",
          "pwsh": "powershell", "powershell": "powershell"}
OTHER_LANGUAGES = {".rb", ".pl", ".pm", ".php"}
COMMAND_APIS = {"subprocess.run", "subprocess.call", "subprocess.Popen", "subprocess.check_call",
                "subprocess.check_output", "subprocess.getoutput", "subprocess.getstatusoutput",
                "os.system", "os.popen", "runpy.run_path", "runpy.run_module"}
UNSUPPORTED_PREFIXES = ("os.exec", "os.spawn", "os.posix_spawn", "asyncio.create_subprocess_",
                        "asyncio.subprocess.create_subprocess_", "pty.spawn")
UNSUPPORTED_CALLS = {"importlib.util.spec_from_file_location", "importlib.machinery.SourceFileLoader",
                     "importlib.machinery.SourcelessFileLoader", "exec", "eval", "compile"}
PROCESS_MODULES = {"subprocess", "os", "runpy", "importlib", "importlib.util", "importlib.machinery",
                   "asyncio", "pty", "contextlib", "functools", "builtins", "__builtins__"}
# Calls that change the working directory, environment or import path.
MUTATORS = {"os.chdir", "os.fchdir", "contextlib.chdir", "os.putenv", "site.addsitedir", "dotenv.load_dotenv",
            *(environ + "." + write for environ in ENVIRON for write in ENVIRON_WRITES)}
# Builtins that inspect a process/import API without invoking it.
BENIGN = {"hasattr", "isinstance", "issubclass", "callable", "print", "repr", "str", "id", "type", "dir", "len",
          "bool"}
# uv run options, so that an option value never becomes the child command.
UV_FLAGS = {"--locked", "--frozen", "--no-sync", "--isolated", "--no-project", "--script", "-s", "--gui-script",
            "--quiet", "-q", "--verbose", "-v", "--offline", "--no-cache", "-n", "--native-tls", "--all-extras",
            "--no-dev", "--dev", "--active", "--no-active", "--exact", "--inexact", "--no-env-file",
            "--no-editable", "--all-packages", "--all-groups", "--no-default-groups", "--only-dev",
            "--compile-bytecode", "--refresh", "--reinstall", "--upgrade", "-U", "--no-build-isolation",
            "--no-build", "--no-binary", "--no-config", "--no-python-downloads", "--managed-python",
            "--no-managed-python", "--preview", "--no-preview", "--no-progress", "--show-resolution",
            "--no-sources", "--no-index", "--system-certs"}
UV_VALUES = {"--python", "-p", "--project", "--with", "-w", "--with-editable", "--with-requirements", "--extra",
             "--group", "--no-group", "--only-group", "--package", "--index", "--default-index", "--index-url",
             "-i", "--extra-index-url", "--find-links", "-f", "--index-strategy", "--keyring-provider",
             "--resolution", "--prerelease", "--fork-strategy", "--exclude-newer", "--exclude-newer-package",
             "--link-mode", "--cache-dir", "--config-file", "--color", "--refresh-package",
             "--reinstall-package", "--no-build-package", "--no-binary-package", "--upgrade-package", "-P",
             "--python-platform", "--allow-insecure-host", "--no-sources-package"}
# Task runners whose recipes, when tracked, are module files outside this model.
RECIPES = {"make": ("Makefile", "makefile", "GNUmakefile"), "gmake": ("Makefile", "makefile", "GNUmakefile"),
           "just": ("justfile", "Justfile", ".justfile", "JUSTFILE"),
           "task": ("Taskfile.yml", "Taskfile.yaml", "taskfile.yml", "taskfile.yaml"),
           "invoke": ("tasks.py",), "inv": ("tasks.py",), "nox": ("noxfile.py",), "tox": ("tox.ini",),
           "poe": ("pyproject.toml",), "rake": ("Rakefile", "rakefile"),
           "pre-commit": (".pre-commit-config.yaml", ".pre-commit-config.yml")}
RECIPE_LOCATIONS = {"-f", "--file", "--makefile", "-C", "--directory", "--justfile", "--working-directory", "-d",
                    "--dir", "--taskfile", "-t", "--prefix", "--cwd", "--rakefile", "-c", "--noxfile",
                    "--project", "--project-dir"}
NODE_RUNNERS = {"npm", "pnpm", "yarn", "bun"}
NODE_SAFE = {"view", "info", "show", "config", "ls", "list", "outdated", "help", "whoami", "ping",
             "--version", "-v", "--help", "-h"}
NODE_FLAGS = {"--ignore-scripts", "--offline", "--foreground-scripts", "--silent", "--quiet", "--verbose",
              "--json", "--no-audit", "--no-fund", "--global", "-g"}
PYTHON_RUNNERS = {"uv", "poetry", "pipenv", "pdm", "hatch"}
REDIRECTION = re.compile(r"(\d*|&|\*)(>>|>\||>&|>|<<<|<<-|<<|<>|<&|<)(.*)", re.S)

# These committed sources prove the computed checkouts used by the registered
# Works parity job. A changed materializer must establish provenance again.
WORKS_PLATFORM_WORKFLOW = ".github/workflows/ci.yml"
WORKS_PLATFORM_ACTION = ".github/actions/platform-parity/action.yml"
WORKS_PLATFORM_ROOT = "references/Hexalith.Platform"
WORKS_PLATFORM_PREPARE = "scripts/prepare-platform-builds.py"
WORKS_PLATFORM_COORDINATOR = "scripts/verify-platform-parity-ci.py"
WORKS_PLATFORM_INPUTS = {
    # The reviewed v6.8.1 rendering (SHA-256 489af315...) with each immutable
    # Builds release tag masked; see works_fingerprint.
    WORKS_PLATFORM_WORKFLOW: "528c2bb1cafa7a77df61731089671981b4e791fb7b02bafed0341f0cc485502e",
    WORKS_PLATFORM_ACTION: "83b29524bf654025ce4260f0ab1917272b406750621a9212dfb7c2c559fcf8a2",
    WORKS_PLATFORM_PREPARE: "5fa6f5012381e6d64154c10999396a35a2f21a96d6cce0245d8b19f82d01cddf",
    WORKS_PLATFORM_COORDINATOR: "4e84e8280841785b694c3d22cb951a0e492e08e25a846a2d52d165bd0f34f127",
}
# The coordinator loads this standard-library-only Platform implementation
# from the initialized checkout and executes its sealed export. The proof
# assumes, rather than traces, that the export reproduces the committed
# bytes, so it binds these reviewed bytes (Git blob 52dfe0ea...) in the tree
# of whatever commit the Works gitlink records, not a list of Platform commits.
WORKS_PLATFORM_EXPORT = {
    "eng/works_host_snapshot.py": "a80fb6fa9be866236fed99bd337eeee716440ea5f36ee5615033e0e5260a8a77",
}
# A Builds reference at an immutable vX.Y.Z release tag. Builds releases are
# delivered and qualified through CiCd, so only these tags may vary.
BUILDS_RELEASE = re.compile(rb"(?<![A-Za-z0-9_./-])(Hexalith/Hexalith\.Builds(?:/[A-Za-z0-9_.-]+)*@)"
                            rb"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?![A-Za-z0-9_.+/-])")
BUILDS_RELEASE_MASK = b"vX.Y.Z"
NATIVE_PYTHON_EXPANSION = '"${HEXALITH_CI_PYTHON:?Shared prepared Python is required}"'
NATIVE_PYTHON_COMMAND = re.compile(
    rf'[ \t]*(?P<timeout>timeout --signal=TERM --kill-after={TIMEOUT_DURATION} {TIMEOUT_DURATION} )'
    rf'{re.escape(NATIVE_PYTHON_EXPANSION)}(?P<arguments> [A-Za-z0-9_./-]+\.py(?: [A-Za-z0-9_./-]+)*)[ \t]*\n?')
NATIVE_PYTHON_HOOK = ".github/actions/after-unit-tests"
# The immutable v6 Builds contract prepares the venv before this hook from
# v6.2.0 onward. A new major release needs explicit qualification.
NATIVE_PYTHON_RELEASE = re.compile(r"v6\.(?:[2-9]|[1-9][0-9]+)\.(?:0|[1-9][0-9]*)")
WORKS_PLATFORM_ENTRIES = {
    (WORKS_PLATFORM_PREPARE, 52, "subprocess.run"): ("eng/bound_builds.py", "python"),
    (WORKS_PLATFORM_PREPARE, 55, "subprocess.check_output"): ("eng/prepare_builds_artifacts.py", "python"),
    (WORKS_PLATFORM_COORDINATOR, 69, "importlib.util.spec_from_file_location"): ("eng/works_host_snapshot.py", "python"),
    (WORKS_PLATFORM_COORDINATOR, 201, "subprocess.run"): ("eng/verify-works-host.sh", "bash"),
}
# These fixed Git calls read metadata/archives or materialize a local checkout.
# Their arguments are data from the review-bound files above: paths rooted in
# the job and revision data from Git or the stable numeric SDK version.
WORKS_PLATFORM_GIT_CALLS = {
    (WORKS_PLATFORM_PREPARE, 48, "subprocess.run"),  # clone local Platform owner
    (WORKS_PLATFORM_PREPARE, 50, "subprocess.run"),  # detach at the recorded HEAD
    (WORKS_PLATFORM_COORDINATOR, 44, "subprocess.check_output"),  # SDK archive/show with verified revision
    (WORKS_PLATFORM_COORDINATOR, 118, "subprocess.run"),  # clone local Platform owner
    (WORKS_PLATFORM_COORDINATOR, 119, "subprocess.run"),  # detach at the snapshot's revision
}
GIT_READ_FLAGS = {
    "rev-parse": {"--verify", "-q", "--quiet", "--show-toplevel", "--show-prefix", "--show-cdup", "--git-dir",
                  "--absolute-git-dir", "--is-inside-work-tree", "--is-bare-repository", "--short", "--end-of-options",
                  "--show-superproject-working-tree"},
    "ls-files": {"-v", "-z", "-c", "-o", "-s", "-t", "--cached", "--others", "--stage", "--exclude-standard",
                 "--full-name", "--error-unmatch", "--modified", "--deleted", "--directory"},
    "ls-tree": {"-r", "-t", "-d", "-z", "-l", "--name-only", "--name-status", "--full-name", "--full-tree"},
    "status": {"-s", "-b", "-z", "--short", "--branch", "--porcelain", "--untracked-files", "--ignore-submodules"},
    "cat-file": {"-t", "-s", "-e", "-p", "--batch-check"},
    "diff": {"-z", "--exit-code", "--quiet", "--name-only", "--name-status", "--stat", "--raw", "--cached",
             "--staged", "--no-index", "--no-ext-diff", "--no-textconv", "--end-of-options"},
    "show": {"-s", "--no-patch", "--format=", "--pretty=", "--no-ext-diff", "--no-textconv", "--name-only",
             "--name-status", "--end-of-options"},
    "archive": {"--format=tar", "--format=zip", "--prefix=", "--worktree-attributes"},
    "remote": {"--all", "--push"},
}
GIT_LOCAL_FLAGS = {
    "clone": {"-q", "--quiet", "--shared", "--local", "--no-hardlinks", "--no-checkout", "--no-tags"},
    "fetch": {"-q", "--quiet", "--depth", "--no-auto-maintenance", "--no-recurse-submodules", "--no-tags",
              "--no-write-fetch-head", "--refmap"},
    "checkout": {"-q", "--quiet", "--detach", "--no-recurse-submodules"},
}
GIT_ENV_PREFIXES = ("GIT_", "LD_", "DYLD_")


def works_fingerprint(path, data):
    """SHA-256 of a reviewed Works proof input.

    Only the workflow masks its Builds release tags. Input that already holds
    the mask is never proved, so the mask cannot stand in for a tag.
    """
    if path == WORKS_PLATFORM_WORKFLOW:
        if BUILDS_RELEASE_MASK in data:
            return None
        data = BUILDS_RELEASE.sub(rb"\1" + BUILDS_RELEASE_MASK, data)
    return hashlib.sha256(data).hexdigest()


def environment_names(word):
    return re.search(r"(?<![A-Za-z0-9_])GITHUB_ENV(?![A-Za-z0-9_])", word) is not None


def path_names(word):
    return re.search(r"(?<![A-Za-z0-9_])GITHUB_PATH(?![A-Za-z0-9_])", word) is not None


def path_component(component):
    """A PATH entry may add only absolute literal or home directories."""
    if component in {"$PATH", "${PATH}"}:
        return True
    for home in ("$HOME", "${HOME}", "~"):
        if component == home or component.startswith(home + "/"):
            return not re.search(r"[$`*?]|(?:^|/)\.\.(?:/|$)", component[len(home):])
    if component.startswith("/") or re.match(r"[A-Za-z]:[\\/]", component):
        return not re.search(r"[$`*?%]", component)
    return False


def check_path(value, *, append=False, message="unsupported PATH change affecting script resolution"):
    """Reject relative, workspace, action-path and computed PATH entries."""
    value = re.sub(r"(?i)\$\{?env:(\w+)\}?", lambda match: "$" + match[1].upper(), value.strip().strip("\"'"))
    value = value.replace("${PATH}", "$PATH").replace("${HOME}", "$HOME")
    tokens = re.split(r"[;:]", value)
    parts = []
    for token in tokens:
        # Rejoin a Windows drive letter that the separator split.
        if parts and re.fullmatch(r"[A-Za-z]", parts[-1]) and token[:1] in {"\\", "/"}:
            parts[-1] += ":" + token
        else:
            parts.append(token)
    if append and parts and parts[0] == "":
        parts = parts[1:]
    if not parts or not all(path_component(part) for part in parts):
        raise DeliveryError(message)


def assignment(word):
    """Return whether a shell word is NAME=value or NAME+=value.

    Import-path overrides fail; a PATH value must pass check_path.
    """
    match = re.match(r"([A-Za-z_]\w*)(\+?)=(.*)", word, re.S)
    if not match:
        return False
    if match[1].upper() in RESOLUTION:
        raise DeliveryError("unsupported environment assignment affecting script resolution")
    if match[1] == "PATH":
        check_path(match[3], append=bool(match[2]))
    return True


def executes(name):
    return (name in COMMAND_APIS or name in UNSUPPORTED_CALLS or name.startswith(UNSUPPORTED_PREFIXES)
            or name in {"importlib.import_module", "__import__"})


def reflective_api(name):
    return executes(name) or name in MUTATORS


def literal_key(node):
    return (isinstance(node, ast.Constant) and isinstance(node.value, str)
            and node.value.upper() not in RESOLUTION | {"PATH"})


def tool(word):
    """An absolute wrapper or runner path names the same tool."""
    return PurePosixPath(word).name if word.startswith("/") else word


def shebang(first):
    if not first.startswith(b"#!"):
        return None
    return "python" if b"python" in first else "powershell" if b"pwsh" in first else (
        "bash" if re.search(rb"\b(?:ba)?sh\b", first) else None)


def lexical(line, powershell):
    """Return the comment cut, quote-blanked structure and substitution flag."""
    single, double, escaped, syntax, cut, substitution = False, False, False, [], len(line), False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            syntax.append(" ")
            continue
        # A comment starts only at a word boundary: $#, ${#x} and a#b are words.
        if char == "#" and not single and not double and (index == 0 or line[index - 1] in " \t;&|()<>"):
            cut = index
            break
        if char == ("`" if powershell else "\\") and not single:
            escaped = True
            syntax.append(" ")
            continue
        if char == "'" and not double:
            single = not single
        elif char == '"' and not single:
            double = not double
        elif not single and (line[index:index + 2] == "$(" or (char == "`" and not powershell)):
            substitution = True
        syntax.append(char if not single and not double and char not in "'\"" else " ")
    return cut, "".join(syntax), substitution


def shell_words(text, powershell):
    """Shell words after quote removal; tolerant, because literals are data."""
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=";&|()")
        if powershell:
            lex.escape = ""
        lex.whitespace_split, lex.commenters = True, ""
        return [word for word in lex if word and not set(word) <= set(";&|()")]
    except ValueError:
        return [word.strip("'\"") for word in text.split()]


@lru_cache(maxsize=128)
def powershell_ast(text):
    """Use the language parser, with source only on stdin, never as code."""
    try:
        result = subprocess.run(
            ["pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", "-File",
             str(Path(__file__).with_name("scan_powershell.ps1"))],
            input=text, text=True, encoding="utf-8", capture_output=True, timeout=30,
            cwd=Path(__file__).resolve().parent)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DeliveryError("PowerShell parser unavailable: " + clean(error)) from None
    if result.returncode:
        raise DeliveryError("PowerShell parser failed: " + clean(result.stderr))
    try:
        events = json.loads(result.stdout)["events"]
        if not isinstance(events, list):
            raise ValueError("invalid event list")
        for event in events:
            if (not isinstance(event, dict) or type(event.get("line")) is not int or event["line"] < 1
                    or event.get("kind") not in {"error", "command", "literal", "assignment", "member",
                                                 "module", "here-expansion", "sequence", "unsupported"}):
                raise ValueError("invalid parser event")
            if event["kind"] == "sequence":
                if not isinstance(event.get("values"), list) or not all(isinstance(v, str) for v in event["values"]):
                    raise ValueError("invalid literal sequence")
                continue
            if not isinstance(event.get("text"), str):
                raise ValueError("invalid parser text")
            if event["kind"] == "command":
                if (event.get("invocation") not in {"Unknown", "Ampersand", "Dot"}
                        or not isinstance(event.get("words"), list) or not event["words"]
                        or any(not isinstance(w, dict) or not isinstance(w.get("type"), str)
                               or not isinstance(w.get("value"), str) or type(w.get("splatted")) is not bool
                               or type(w.get("computed")) is not bool
                               for w in event["words"])
                        or not isinstance(event.get("redirects"), list)
                        or not all(isinstance(r, str) for r in event["redirects"])):
                    raise ValueError("invalid command event")
            if event["kind"] == "assignment" and (
                    type(event.get("simple")) is not bool or type(event.get("increment")) is not bool
                    or not isinstance(event.get("operator"), str)
                    or not isinstance(event.get("variables"), list)
                    or not all(isinstance(v, str) for v in event["variables"])):
                raise ValueError("invalid assignment event")
        return events
    except (KeyError, ValueError, TypeError):
        raise DeliveryError("invalid PowerShell parser output") from None


def powershell_comments(text):
    """Blank actual block comments, preserving quotes, positions and lines."""
    result, quote, here, comment, index = [], None, None, False, 0
    newline = re.compile(r"[ \t]*\r?\n")
    while index < len(text):
        char, pair = text[index], text[index:index + 2]
        if here:
            if (index == 0 or text[index - 1] == "\n") and pair == here + "@":
                result.extend(pair)
                here, index = None, index + 2
                continue
            result.append(char)
        elif comment:
            if pair == "#>":
                result.extend("  ")
                comment, index = False, index + 2
                continue
            result.append("\n" if char == "\n" else " ")
        elif quote:
            result.append(char)
            if char == "`" and quote == '"' and index + 1 < len(text):
                index += 1
                result.append(text[index])
            elif char == quote:
                if quote == "'" and index + 1 < len(text) and text[index + 1] == "'":
                    index += 1
                    result.append(text[index])
                else:
                    quote = None
        elif char == "`" and index + 1 < len(text):
            result.extend(text[index:index + 2])
            index += 1
        elif char == "@" and len(pair) == 2 and pair[1] in "'\"" and newline.match(text, index + 2):
            result.extend(pair)
            here, index = pair[1], index + 2
            continue
        elif char in "'\"":
            result.append(char)
            quote = char
        elif pair == "<#":
            result.extend("  ")
            comment, index = True, index + 2
            continue
        elif char == "#":
            # A line comment's quotes and delimiters are all inert.
            end = text.find("\n", index)
            end = len(text) if end < 0 else end
            result.extend(text[index:end])
            index = end
            continue
        else:
            result.append(char)
        index += 1
    return "".join(result)


def tokens(value):
    """A literal and the path-shaped pieces of a word or Python string."""
    if not isinstance(value, str) or not value or len(value) > MAX_LITERAL:
        return set()
    return {value, *(part for part in re.split(r"[\s;&|()<>`'\",=\[\]]+", value) if part)}


def module_references(words, depth=0):
    """Python modules that a literal -m operand names or a -c operand imports.

    The words are one literal sequence: a line's shell words, a container's
    elements or a call's arguments. A word holding whitespace is tokenized
    again, so command strings and nested shell or interpreter calls count too.
    """
    found = set()
    for index, word in enumerate(words):
        if not isinstance(word, str) or not word:
            continue
        option = (re.fullmatch(r"-[bBdEhiIOPqRsSuvVx]*([mc])(.*)", word, re.S)
                  or re.fullmatch(r"--(module)(?:=(.*))?", word, re.S))
        if option:
            value = option[2] or (words[index + 1] if index + 1 < len(words) else None)
            if isinstance(value, str) and len(value) > MAX_LITERAL:
                raise DeliveryError("execution literal coverage limit exceeded")
            if isinstance(value, str) and option[1] == "c":
                found |= imported(value, depth)
            elif isinstance(value, str) and MODULE.fullmatch(value):
                found.add(value)
        if len(word) > MAX_LITERAL:
            # Search the entire already-bounded source literal with constant
            # parser state. Never feed an oversized string to shlex, or let a
            # harmless prefix conceal an execution-bearing suffix.
            interpreter = re.search(r"(?<![\w.])(?:(?:python|pypy)(?:\d+(?:\.\d+)*)?|py|"
                                    + "|".join(map(re.escape, sorted(SHELLS))) +
                                    r")(?:\.exe)?(?=[\s'\";&|()]|$)", word, re.I)
            option = re.compile(r"(?:^|[\s'\";&|()])(?:-[bBdEhiIOPqRsSuvVx]*[cm]|(?i:-command))")
            if interpreter and option.search(word, interpreter.end()):
                raise DeliveryError("execution literal coverage limit exceeded")
            continue
        if depth < 3 and re.search(r"\s", word):
            found |= module_references(shell_words(word, False), depth + 1)
    return found


def sequences(node):
    """The literal word sequences of one Python node."""
    def word(item):
        return item.value if isinstance(item, ast.Constant) and isinstance(item.value, str) else None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [[node.value]]
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [[word(item) for item in node.elts]]
    if isinstance(node, ast.Call):
        return [[word(item) for item in node.args]]
    return []


def imported(code, depth):
    """Modules that literal Python code imports, never failing on other text."""
    if depth >= 3 or len(code) > MAX_LITERAL:
        raise DeliveryError("execution literal coverage limit exceeded")
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, RecursionError):
        return set()
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(item.name for item in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.add(node.module)
            found.update(node.module + "." + item.name for item in node.names if item.name != "*")
        elif (isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant)
              and isinstance(node.args[0].value, str)
              and getattr(node.func, "attr", getattr(node.func, "id", None)) in {"import_module", "__import__",
                                                                                 "run_module"}):
            found.add(node.args[0].value)
        for sequence in sequences(node):
            found |= module_references(sequence, depth + 1)
    return {name for name in found if MODULE.fullmatch(name)}


def redirections(words):
    """Remove redirection operators and their targets.

    Return the remaining words and whether stdin is a heredoc or other input.
    """
    result, stdin, skip = [], None, False
    for word in words:
        if skip:
            skip = False
            continue
        match = REDIRECTION.fullmatch(word)
        if match and not (match[1] == "*" and match[2] not in {">", ">>"}):
            if match[2] in {"<<", "<<-"}:
                stdin = "heredoc"
            elif match[2] in {"<<<", "<", "<>", "<&"} and stdin is None:
                stdin = "stdin"
            skip = not match[3]
            continue
        result.append(word)
    return result, stdin


def heredoc_word(text, start):
    """Quote-remove the complete delimiter word, including mixed E'OF' forms."""
    result, quote, quoted, index = [], None, False, start
    while index < len(text):
        char = text[index]
        if quote:
            if char == quote:
                quote = None
            elif char == "\\" and quote == '"':
                raise DeliveryError("unsupported heredoc delimiter syntax")
            else:
                result.append(char)
        elif char in " \t;&|<>()":
            break
        elif char == "$" and text[index + 1:index + 2] in {"'", '"'}:
            raise DeliveryError("unsupported heredoc delimiter syntax: ANSI/locale quoting")
        elif char in "'\"":
            quote, quoted = char, True
        elif char == "\\":
            quoted, index = True, index + 1
            if index >= len(text):
                raise DeliveryError("unsupported heredoc delimiter syntax")
            result.append(text[index])
        else:
            result.append(char)
        index += 1
    if quote or index == start:
        raise DeliveryError("unsupported heredoc delimiter syntax")
    return "".join(result), not quoted


class ActionLoader(yaml.SafeLoader):
    """Ambiguous YAML keys cannot silently replace a script invocation."""


class ActionMap(dict):
    pass


def mapping(loader, node):
    value = ActionMap()
    value.locations = {}
    value.line = node.start_mark.line + 1
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str) or key in value:
            raise DeliveryError("invalid or duplicate action mapping key")
        value[key] = loader.construct_object(value_node, deep=True)
        value.locations[key] = value_node.start_mark.line + 1 + int(getattr(value_node, "style", None) in {"|", ">"})
    return value


ActionLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def safe_path(value):
    if (not isinstance(value, str) or not value or value.startswith("/") or "\\" in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or any(p in {"", ".", "..", ".git"} for p in value.split("/"))):
        raise DeliveryError("unsafe source path: " + clean(value))
    return value


def scalars(value, skip=()):
    if isinstance(value, dict):
        for key, item in value.items():
            if key not in skip:
                yield from scalars(item, skip)
    elif isinstance(value, list):
        for item in value:
            yield from scalars(item, skip)
    elif isinstance(value, str):
        yield value


class Discovery:
    def __init__(self, git, revision, *, javascript_parser=None, pinned_source=None, module=None):
        self.git, self.revision = git, revision
        self.module = module
        self.items = git.items(revision)
        self.directories = set()
        self.index_directories(self.items)
        self.pinned_source = pinned_source
        self.pins, self.pin_errors = {}, {}
        self.files, self.errors, self.queue, self.visited = {}, [], deque(), set()
        self.headers, self.recipes = {}, {}
        self.total = 0
        self.javascript_parser = javascript_parser
        self.npm_seen = set()
        self.npm_roots = set()
        self.works_platform_targets = None

    def index_directories(self, paths):
        for item in paths:
            parts = item.split("/")
            self.directories.update("/".join(parts[:index]) for index in range(1, len(parts)))

    def acquire(self, path):
        if path in self.pins:
            return
        if path in self.pin_errors:
            raise DeliveryError(self.pin_errors[path])
        try:
            mode, kind, revision = self.items[path]
            if self.pinned_source is None or (mode, kind) != ("160000", "commit"):
                raise DeliveryError("unsafe non-directory source path component: " + clean(path))
            source = self.pinned_source(path, revision)
            entries = {path + "/" + safe_path(item): value for item, value in source.items(revision).items()}
            self.items.update(entries)
            self.index_directories(entries)
            self.directories.add(path)
            self.pins[path] = (source, revision)
        except (ValueError, UnicodeError) as error:
            self.pin_errors[path] = str(error)
            raise

    def source_root(self, path):
        return next((root for root in self.pins if path == root or path.startswith(root + "/")), None)

    def blob(self, path):
        root = self.source_root(path)
        if root is not None:
            git, revision = self.pins[root]
            return git.blob(revision, path.removeprefix(root + "/"))
        return self.git.blob(self.revision, path)

    def error(self, path, line, message):
        self.errors.append(f"{clean(path)}:{line}: {clean(message)}")

    def regular(self, path):
        item = self.items.get(path)
        return item is not None and item[:2] in (("100644", "blob"), ("100755", "blob"))

    def header(self, path):
        if path not in self.headers:
            self.headers[path] = shebang(self.blob(path).split(b"\n", 1)[0])
        return self.headers[path]

    def script_format(self, path):
        """A tracked script by suffix, or an extensionless file with a supported shebang."""
        suffix = PurePosixPath(path).suffix.lower()
        if suffix:
            return FORMATS.get(suffix)
        return self.header(path)

    def add(self, path, fmt=None, cwd=".", action=None, *, python_roots=None, sourced=False):
        path = safe_path(path)
        if not self.regular(path):
            raise DeliveryError("missing or unsafe regular script/action: " + clean(path))
        fmt = fmt or FORMATS.get(PurePosixPath(path).suffix.lower()) or self.header(path)
        if fmt not in set(FORMATS.values()):
            raise DeliveryError("unsupported local-script language: " + clean(path))
        if path not in self.files:
            if len(self.files) >= MAX_FILES:
                raise DeliveryError("module selected-file limit exceeded")
            raw = self.blob(path)
            self.total += len(raw)
            if self.total > MAX_BYTES:
                raise DeliveryError("module selected-source byte limit exceeded")
            try:
                text = raw.decode("utf-8")
            except UnicodeError:
                raise DeliveryError("source is not UTF-8: " + clean(path)) from None
            if "\0" in text:
                raise DeliveryError("source contains NUL: " + clean(path))
            self.files[path] = {"format": fmt, "text": text}
        elif self.files[path]["format"] != fmt:
            raise DeliveryError("ambiguous script language: " + clean(path))
        key = (path, cwd, action, python_roots, sourced)
        if key not in self.visited:
            self.visited.add(key)
            if len(self.visited) > 4 * MAX_FILES:
                raise DeliveryError("script traversal limit exceeded")
            self.queue.append(key)

    def expand(self, value, path, action):
        """Replace workspace, action and script-root anchors; report anchoring."""
        value = value.replace("\\", "/")
        parent = str(PurePosixPath(path).parent)
        markers = [("${{ github.workspace }}", "."), ("${GITHUB_WORKSPACE}", "."), ("$GITHUB_WORKSPACE", "."),
                   ("$env:GITHUB_WORKSPACE", "."), ("${env:GITHUB_WORKSPACE}", "."),
                   ("$PSScriptRoot", parent), ("${PSScriptRoot}", parent)]
        if action:
            markers += [(marker, action) for marker in (
                "${{ github.action_path }}", "${GITHUB_ACTION_PATH}", "$GITHUB_ACTION_PATH",
                "$env:GITHUB_ACTION_PATH", "${env:GITHUB_ACTION_PATH}")]
        anchored = False
        for marker, replacement in sorted(markers, key=lambda pair: len(pair[0]), reverse=True):
            # $GITHUB_WORKSPACE_TOOLS is another variable, not an anchor.
            pattern = re.escape(marker) + ("(?![A-Za-z0-9_])" if marker[-1].isalnum() else "")
            anchored |= re.match(pattern, value) is not None
            value = re.sub(pattern, lambda _: replacement, value)
        return value, anchored

    def resolve(self, value, *, path, cwd, action, allow_root=False):
        if not isinstance(value, str):
            raise DeliveryError("unresolved local-script target")
        value, anchored = self.expand(value, path, action)
        if any(c in value for c in ("$", "`", "*", "?", "{", "}", "~")):
            raise DeliveryError("unresolved local-script target: " + clean(value))
        joined = posixpath.join("." if anchored else cwd, value)
        components, traversed = joined.split("/"), []
        for index, component in enumerate(components):
            if component in {"", "."}:
                continue
            if component == "..":
                if not traversed or "/".join(traversed) in self.pins:
                    raise DeliveryError("source path escapes module")
                traversed.pop()
            else:
                traversed.append(component)
                prefix = "/".join(traversed)
                item = self.items.get(prefix)
                if item is None:
                    continue
                remaining = components[index + 1:]
                if (item[:2] == ("160000", "commit") and self.pinned_source is not None and (remaining or allow_root)
                        and prefix.startswith("references/") and prefix.count("/") == 1):
                    if any(item in {"", ".", "..", ".git"} for item in remaining):
                        raise DeliveryError("unsafe source path within pinned source: " + clean(value))
                    self.acquire(prefix)
                elif remaining:
                    raise DeliveryError("unsafe non-directory source path component: " + clean(prefix))
        value = posixpath.normpath(joined)
        if allow_root and value == ".":
            return value
        return safe_path(value)

    def candidates(self, value, bases):
        """Tracked regular blobs that an expanded relative literal names from each base."""
        matches = []
        for base in bases:
            joined = posixpath.normpath(posixpath.join(base, value))
            if (joined not in matches and not joined.startswith(("../", "/")) and joined != ".."
                    and ".git" not in joined.split("/") and self.regular(joined)):
                matches.append(joined)
        return matches

    def targets(self, value, *, path, cwd, action, bases):
        """Resolve an execution-position literal; fail only when no base names it."""
        precise = self.resolve(value, path=path, cwd=cwd, action=action)
        if precise in self.items:
            return [precise]
        expanded, anchored = self.expand(value, path, action)
        matches = [] if anchored or self.source_root(precise) else self.candidates(expanded, bases)
        if not matches:
            raise DeliveryError("missing or unsafe regular script/action: " + clean(precise))
        return matches

    def locate(self, value, path, action, bases):
        """Rule 1: the tracked scripts that a data literal names, never failing."""
        if not isinstance(value, str) or "\n" in value or "\0" in value:
            return []
        expanded, anchored = self.expand(value, path, action)
        if not expanded or expanded.startswith("/") or any(c in expanded for c in "$`*?{}~"):
            return []
        result = []
        for match in self.candidates(expanded, ["."] if anchored else bases):
            try:
                fmt = self.files[match]["format"] if match in self.files else self.script_format(match)
            except (ValueError, UnicodeError):
                # add() reports the same bounded-read failure at the literal.
                result.append((match, None))
                continue
            if fmt in SCRIPTS:
                result.append((match, fmt))
        return result

    def bases(self, path, action, cwds):
        root = self.source_root(path)
        return list(dict.fromkeys([".", str(PurePosixPath(path).parent), *([root] if root else []),
                                   *([action] if action else []), *cwds]))

    def include(self, literals, path, cwd, action, bases):
        """Traverse literal references in every supplied invocation context."""
        for number, value in literals:
            for candidate in sorted(tokens(value)):
                for match, fmt in self.locate(candidate, path, action, bases):
                    try:
                        self.add(match, fmt, cwd=cwd, action=action)
                    except (ValueError, UnicodeError) as error:
                        self.error(path, number, "local-script discovery: " + clean(error))

    def references(self, words, path, number):
        """Every literal-sequence entry point preserves coverage-limit errors."""
        try:
            return module_references(words)
        except (ValueError, RecursionError) as error:
            self.error(path, number, "local-script discovery: " + clean(error))
            return set()

    def include_modules(self, modules, path, cwd, action, bases):
        """Rule 1 for module names: include every local module a -m/-c literal names.

        A module resolves from every base as an import root; its file, package
        initializer and __main__.py, and every enclosing __init__.py, are
        included and traversed under each invocation context.
        """
        for number, module in sorted(set(modules)):
            for root in bases:
                stem = posixpath.normpath(posixpath.join(root, module.replace(".", "/")))
                if stem == ".." or stem.startswith("../") or ".git" in stem.split("/"):
                    continue
                try:
                    self.import_path(stem)
                    files = [candidate for candidate in (stem + ".py", stem + "/__init__.py", stem + "/__main__.py")
                             if candidate in self.items]
                    if not files and stem not in self.directories:
                        continue
                    # Namespace packages also execute every regular ancestor
                    # initializer, and unsafe initializers must fail visibly.
                    for target in files or [stem + "/__init__.py"]:
                        self.add_module(target, cwd, action, (root,))
                except (ValueError, UnicodeError) as error:
                    self.error(path, number, "local-script discovery: " + clean(error))

    def language(self, path, fmt):
        """An execution-position target in another script language fails coverage."""
        if not self.regular(path):
            return
        suffix = PurePosixPath(path).suffix.lower()
        own = FORMATS.get(suffix) if suffix else self.header(path)
        if fmt is None:
            # Direct execution follows the shebang, which must agree with the suffix.
            if own in SCRIPTS and self.header(path) not in {None, own}:
                raise DeliveryError("ambiguous script language: " + clean(path))
        elif own is not None and own != fmt:
            raise DeliveryError("unsupported cross-language script invocation: " + clean(path))

    def tests(self):
        """Whether tracked Python files match conventional test discovery."""
        return any(self.regular(item) and re.fullmatch(r"conftest\.py|test.*\.py|.*_test\.py", PurePosixPath(item).name)
                   for item in self.items)

    def task_runner(self, name, args, bases):
        """Fail a recognized runner that executes tracked module recipes or tests."""
        if name in RECIPES and any(argument.split("=", 1)[0] in RECIPE_LOCATIONS or (
                argument[:1] == "-" and argument[1:2] != "-" and argument[:2] in RECIPE_LOCATIONS)
                for argument in args):
            raise DeliveryError("unsupported task runner recipe location: " + clean(name))
        if name in TEST_RUNNERS and self.tests():
            raise DeliveryError("unsupported test runner with tracked module tests: " + clean(TEST_RUNNERS[name]))
        if name in RECIPES and self.recipe(RECIPES[name], bases):
            raise DeliveryError("unsupported task runner with tracked module recipes: " + clean(name))

    def unittest_discovery(self, args, path, cwd, action):
        """Follow unittest discover with an explicit directory and a literal filename pattern."""
        options, index = {}, 1
        while index < len(args):
            argument = args[index]
            index += 1
            if argument in {"-v", "--verbose", "-q", "--quiet"}:
                continue
            key = {"-s": "start", "--start-directory": "start", "-p": "pattern", "--pattern": "pattern"}.get(argument)
            if key is None or key in options or index >= len(args) or args[index].startswith("-"):
                raise DeliveryError("unsupported unittest discovery options")
            options[key] = args[index]
            index += 1
        if "start" not in options:
            raise DeliveryError("unsupported test runner with tracked module tests: unittest")
        pattern = options.get("pattern", "test*.py")
        if not re.fullmatch(r"[A-Za-z0-9_*?]+\.py", pattern):
            raise DeliveryError("unresolved unittest discovery filename pattern")
        start = self.resolve(options["start"], path=path, cwd=cwd, action=action, allow_root=True)
        if start != "." and start not in self.directories:
            raise DeliveryError("missing committed unittest discovery directory: " + clean(start))
        prefix = start + "/" if start != "." else ""
        for item in sorted(self.items):
            if item.startswith(prefix):
                if not self.regular(item) or PurePosixPath(item).suffix.lower() in {".pyc", ".pyo", ".pyd", ".so"}:
                    raise DeliveryError("unsafe unittest discovery source: " + clean(item))
                name = posixpath.basename(item).lower()
                # Include initializers for load_tests and every filename
                # matching the pattern on either Windows or POSIX.
                if name == "__init__.py" or fnmatchcase(name, pattern.lower()):
                    self.add_module(item, cwd, action, (start,))

    def recipe(self, names, bases):
        for base in bases:
            for name in names:
                candidate = posixpath.normpath(posixpath.join(base, name))
                if candidate in self.items:
                    return candidate
        return None

    def recipe_names(self, bases):
        """Script names that Python project runners resolve from tracked recipe files."""
        names = set()
        for base in bases:
            for name in ("pyproject.toml", "Pipfile", "hatch.toml"):
                candidate = posixpath.normpath(posixpath.join(base, name))
                if candidate not in self.items:
                    continue
                if candidate not in self.recipes:
                    try:
                        data = tomllib.loads(self.blob(candidate).decode("utf-8"))
                    except (ValueError, UnicodeError):
                        raise DeliveryError("unreadable task runner recipe: " + clean(candidate)) from None
                    found = set()
                    def table(value, *keys):
                        for key in keys:
                            value = value.get(key) if isinstance(value, dict) else None
                        if isinstance(value, dict):
                            found.update(map(str, value))
                    table(data, "project", "scripts")
                    table(data, "project", "gui-scripts")
                    table(data, "tool", "poetry", "scripts")
                    table(data, "tool", "pdm", "scripts")
                    table(data, "tool", "poe", "tasks")
                    table(data, "scripts")
                    hatch = data.get("tool", {}).get("hatch") if isinstance(data.get("tool"), dict) else None
                    for environments in (hatch.get("envs") if isinstance(hatch, dict) else None, data.get("envs")):
                        if isinstance(environments, dict):
                            for environment in environments.values():
                                table(environment, "scripts")
                    self.recipes[candidate] = found
                names |= self.recipes[candidate]
        return names

    def project_preparation(self, name, words, bases):
        """Project synchronization may execute a tracked backend before a child."""
        if name == "uv":
            remaining, flags = list(words), set()
            # Global and run options end at the visible child, whose arguments
            # cannot disable preparation already performed by uv.
            for _ in range(2):
                while remaining and remaining[0].startswith("-"):
                    key, equals, value = remaining.pop(0).partition("=")
                    if key == "--":
                        break
                    flags.add(key)
                    if key in UV_VALUES and not equals and remaining:
                        value = remaining.pop(0)
                    if key in {"--with", "-w", "--with-editable", "--with-requirements"}:
                        local = (key in {"--with-editable", "--with-requirements"}
                                 or re.search(r"[$`]|(?:^|[ @])(?:[./~]|file:)", value)
                                 or any(posixpath.normpath(posixpath.join(base, value)) in self.items
                                        or posixpath.normpath(posixpath.join(base, value)) in self.directories
                                        for base in bases))
                        if local:
                            raise DeliveryError("unsupported local dependency preparation: " + name)
                    if key in {"-m", "--module"}:
                        break
                if remaining[:1] != ["run"]:
                    break
                remaining.pop(0)
            if flags & {"--no-project", "--no-sync"}:
                return
        for base in bases:
            candidate = posixpath.normpath(posixpath.join(base, "pyproject.toml"))
            if candidate not in self.items:
                continue
            try:
                project = tomllib.loads(self.blob(candidate).decode("utf-8"))
            except (ValueError, UnicodeError):
                raise DeliveryError("unreadable task runner recipe: " + clean(candidate)) from None
            if "build-system" in project or self.recipe(("setup.py", "setup.cfg"), bases):
                raise DeliveryError("unsupported local project preparation with tracked build backend: " + name)

    def discover_works_platform(self, path, action):
        """Traverse the known checkout/export from its committed Platform tree.

        The action initializes the recorded direct gitlink and supplies no
        Works/SDK root overrides. The preparation clone detaches at that
        checkout's HEAD, then calls the two fixed preparation scripts. The
        coordinator loads the snapshot module from the initialized checkout,
        copies ordinary source bytes from that checkout into the detached
        clone, and uses the pinned snapshot implementation to export them.
        Its shell verifier runs from those exported source bytes. Any
        committed gitlink commit is acceptable when its tree holds the
        reviewed export implementation. Resolve each executable within the
        committed source; the Python callsites enter ordinary discovery so
        unresolved descendants still fail.
        """
        for source, digest in WORKS_PLATFORM_INPUTS.items():
            if not self.regular(source) or works_fingerprint(source, self.blob(source)) != digest:
                raise DeliveryError("unproved computed Platform source: " + clean(source))
        import_roots = {"", *(posixpath.dirname(source) for source in WORKS_PLATFORM_INPUTS
                              if source.endswith(".py"))}
        protected_imports = sys.stdlib_module_names | {"sitecustomize", "usercustomize"}
        for candidate in sorted(self.items.keys() | self.directories):
            parent, name = posixpath.split(candidate)
            if parent in import_roots and name.split(".", 1)[0] in protected_imports and (
                    "." not in name or name.endswith((".py", ".pyc", ".so", ".pyd"))):
                raise DeliveryError("unproved computed Platform import shadow: " + clean(candidate))
        if self.items.get(WORKS_PLATFORM_ROOT, (None, None))[:2] != ("160000", "commit"):
            raise DeliveryError("unproved Platform gitlink for computed checkout/export: " + WORKS_PLATFORM_ROOT)
        self.acquire(WORKS_PLATFORM_ROOT)
        for source, digest in WORKS_PLATFORM_EXPORT.items():
            source = WORKS_PLATFORM_ROOT + "/" + source
            if not self.regular(source) or hashlib.sha256(self.blob(source)).hexdigest() != digest:
                raise DeliveryError("unproved computed Platform source: " + clean(source))
            # The loader may run committed bytecode for this module instead of
            # the reviewed source, including through a non-directory cache.
            directory, name = posixpath.split(source)
            cache, stem = directory + "/__pycache__", posixpath.splitext(name)[0] + "."
            for item in sorted(self.items):
                if item == cache or (item.startswith(cache + "/")
                                     and item[len(cache) + 1:].split("/", 1)[0].startswith(stem)):
                    raise DeliveryError("unproved computed Platform source: " + clean(item))
        targets = {}
        for callsite, (entry, language) in WORKS_PLATFORM_ENTRIES.items():
            target = self.resolve("$GITHUB_WORKSPACE/" + WORKS_PLATFORM_ROOT + "/" + entry,
                                  path=path, cwd=".", action=action)
            if not self.regular(target):
                raise DeliveryError("missing or unsafe regular script/action: " + clean(target))
            self.language(target, language)
            targets[callsite] = (target, language)
        self.works_platform_targets = targets

    def works_platform_context(self, path, cwd, action, offset):
        # Both locked steps run from the default workspace without path overrides.
        return (self.works_platform_targets is not None and path in WORKS_PLATFORM_INPUTS and cwd == "." and offset == 0
                and action == posixpath.dirname(WORKS_PLATFORM_ACTION))

    def native_python_command(self, command, path, cwd):
        """Bind the shared CI's prepared venv in its default Linux hook."""
        match = NATIVE_PYTHON_COMMAND.fullmatch(command)
        if match is None or cwd != "." or path not in {
            NATIVE_PYTHON_HOOK + "/action.yml", NATIVE_PYTHON_HOOK + "/action.yaml"
        }:
            return command
        config = self.json(".github/hexalith-ci.json")
        hooks = config.get("hooks")
        if config.get("aspire") is not True or not isinstance(hooks, list) or hooks.count("after-unit-tests") != 1:
            raise DeliveryError("shared prepared Python requires the enabled native CI hook")
        workflow = ".github/workflows/ci.yml"
        if not self.regular(workflow):
            raise DeliveryError("shared prepared Python requires the committed managed CI workflow")
        try:
            # The renderer emits a literal GitHub Actions 'on' key. PyYAML's
            # YAML 1.1 resolver would treat that plain key as a boolean.
            source = re.sub(rb"^on:", b"'on':", self.blob(workflow), count=1, flags=re.M)
            value = yaml.load(source, Loader=ActionLoader)
            caller = value["jobs"]["ci"]
            release = config.get("buildsTag")
            arguments = caller.get("with", {})
            if (not isinstance(release, str) or not NATIVE_PYTHON_RELEASE.fullmatch(release)
                    or caller["uses"] != "Hexalith/Hexalith.Builds/.github/workflows/ci.yml@" + release
                    or "env" in value or set(caller) - {"uses", "permissions", "secrets", "with"}
                    or not isinstance(arguments, dict)
                    or set(arguments) - {"job-timeout-minutes", "additional-sdk-version"}):
                raise ValueError
        except (KeyError, AttributeError, TypeError, ValueError, yaml.YAMLError, RecursionError):
            raise DeliveryError("shared prepared Python requires the committed managed CI workflow") from None
        return match["timeout"] + "python" + match["arguments"]

    def action(self, path, text):
        try:
            value = yaml.load(text, Loader=ActionLoader)
            if (not isinstance(value, dict) or not isinstance(value.get("runs"), dict)
                    or value["runs"].get("using") != "composite"
                    or not isinstance(value["runs"].get("steps"), list)):
                raise DeliveryError("invalid composite action")
            if len(value["runs"]["steps"]) > 1000:
                raise DeliveryError("action step limit exceeded")
        except (yaml.YAMLError, RecursionError, TypeError, ValueError) as error:
            self.error(path, 1, "invalid action/discovery: " + clean(error))
            return
        parent = str(PurePosixPath(path).parent)
        if self.module == "Hexalith.Works" and path == WORKS_PLATFORM_ACTION:
            try:
                self.discover_works_platform(path, parent)
            except (ValueError, UnicodeError) as error:
                self.error(path, 1, "local-script discovery: " + clean(error))
        literals, cwds = [(1, item) for key, item in value.items() if key != "runs" for item in scalars(item)], ["."]
        # Each step is discovered independently and anchored at its own line.
        for step in value["runs"]["steps"]:
            line = getattr(step, "line", 1)
            try:
                if not isinstance(step, dict):
                    raise DeliveryError("invalid action step")
                literals += [(line, item) for item in scalars(step, ("run", "shell"))]
                target = step.get("uses")
                local_uses = isinstance(target, str) and target.startswith("./")
                if "env" in step and ("run" in step or local_uses):
                    if not isinstance(step["env"], dict):
                        raise DeliveryError("unsupported computed step environment affecting script resolution")
                    for key, setting in step["env"].items():
                        if str(key).upper() in RESOLUTION:
                            raise DeliveryError("unsupported step environment affecting script resolution")
                        if str(key).upper() == "PATH":
                            check_path(str(setting),
                                       message="unsupported step PATH environment affecting script resolution")
                if "uses" in step:
                    if not isinstance(target, str):
                        raise DeliveryError("invalid action target")
                    if local_uses:
                        directory = self.resolve(target, path=path, cwd=".", action=parent)
                        candidates = [directory + "/" + name for name in ("action.yml", "action.yaml")
                                      if directory + "/" + name in self.items]
                        if not directory.startswith(".github/actions/") or len(candidates) != 1:
                            raise DeliveryError("missing/ambiguous local action: " + clean(target))
                        self.add(candidates[0], "yaml", action=directory)
                    elif not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-fA-F]{40}", target):
                        raise DeliveryError("unresolved or unpinned action target: " + clean(target))
                elif "run" in step:
                    command, shell = step["run"], step.get("shell")
                    if not isinstance(command, str) or not isinstance(shell, str) or not shell.split():
                        raise DeliveryError("action run requires literal command and shell")
                    cwd = "."
                    if "working-directory" in step:
                        cwd = self.resolve(step["working-directory"], path=path, cwd=".", action=parent, allow_root=True)
                        cwds.append(cwd)
                    run = step.locations.get("run", line)
                    interpreter = shell.split()[0]
                    if interpreter in {"python", "python3"}:
                        self.python(path, command, cwd, parent, roots=(cwd,), offset=run - 1)
                    elif interpreter in {"bash", "sh", "pwsh", "powershell"}:
                        if shell == "bash":
                            command = self.native_python_command(command, path, cwd)
                        self.commands(path, command, cwd, parent, offset=run - 1,
                                      powershell=interpreter in {"pwsh", "powershell"})
                    else:
                        raise DeliveryError("unsupported action shell: " + clean(shell))
                else:
                    raise DeliveryError("action step has no run/uses")
            except (RecursionError, TypeError, ValueError) as error:
                self.error(path, line, "invalid action/discovery: " + clean(error))
        bases = self.bases(path, parent, cwds)
        for candidate_cwd in dict.fromkeys(cwds):
            self.include(literals, path, candidate_cwd, parent, bases)
            self.include_modules([(number, module) for number, item in literals
                                  for module in self.references([item], path, number)], path, candidate_cwd, parent, bases)

    @staticmethod
    def literal_bash_array(physical, start):
        """Return the end of a plain literal array assignment, if present."""
        opening = BASH_LITERAL_ARRAY_START.match(physical[start])
        if not opening or opening["name"] in {"auto_resume", "histchars"}:
            return None
        size = opening.end()
        for index in range(start, min(start + 128, len(physical))):
            line = physical[index][opening.end():] if index == start else physical[index]
            size += len(line) + 1
            if size > MAX_LITERAL:
                return None
            item = BASH_LITERAL_ARRAY_LINE.fullmatch(line)
            if not item:
                return None
            if item["close"]:
                return index + 1
        return None

    def logical(self, text, offset, powershell, path):
        """Yield logical commands and data, including closed literal forms.

        Lines split only on LF with a trailing CR dropped. The continuation
        character is a backslash in shell and a backtick in PowerShell, and a
        logical line keeps its first physical line number. Heredoc and
        PowerShell here-string bodies are data lines, never commands.
        """
        physical = [line.removesuffix("\r") for line in text.split("\n")]
        continuation = "`" if powershell else "\\"
        bash_literal_arrays = not powershell and "\r" not in text
        index = 0
        while index < len(physical):
            number, line, data = index + 1 + offset, physical[index], []
            literal_heredoc_closed = False
            if bash_literal_arrays:
                end = self.literal_bash_array(physical, index)
                if end is not None:
                    yield number, "\n".join(physical[index:end]), data, False, True
                    index = end
                    continue
            index += 1
            first_body_index = index
            while (line.endswith(continuation) and (len(line) - len(line.rstrip(continuation))) % 2
                   and index < len(physical)):
                line = line[:-1] + " " + physical[index]
                index += 1
            if powershell:
                opener = re.search(r"@([\"'])\s*$", line)
                if opener:
                    line = line[:opener.start()] + "@HERESTRING"
                    while index < len(physical):
                        body, index = physical[index], index + 1
                        if body.startswith(opener[1] + "@"):
                            line += " " + body[2:]
                            break
                        data.append((index + offset, body, opener[1] == '"'))
            else:
                single_line_opener = index == first_body_index
                cut, structure, _ = lexical(line, powershell)
                for match in re.finditer(r"<<(-?)[ \t]*", line[:cut]):
                    start = match.start()
                    if (structure[start:start + 2] != "<<" or line[start + 2:start + 3] == "<"
                            or line[start - 1:start] == "<"):
                        continue
                    try:
                        delimiter, expands = heredoc_word(line[:cut], match.end())
                    except DeliveryError as error:
                        self.error(path, number, "local-script discovery: " + clean(error))
                        break
                    while index < len(physical):
                        body_number, body, index = index + 1 + offset, physical[index], index + 1
                        # Expanding heredocs remove backslash-newline before
                        # delimiter recognition and substitution expansion.
                        while (expands and body.endswith("\\") and (len(body) - len(body.rstrip("\\"))) % 2
                               and index < len(physical)):
                            body, index = body[:-1] + physical[index], index + 1
                        if (body.lstrip("\t") if match[1] else body) == delimiter:
                            literal_heredoc_closed = single_line_opener and not expands
                            break
                        data.append((body_number, body, expands))
            yield number, line, data, literal_heredoc_closed, False

    def source_relative_launcher(self, path, text, cwd, action):
        """Follow a standalone Bash launcher that derives its child from BASH_SOURCE."""
        if not text.startswith("#!/usr/bin/env bash\n"):
            return False
        lines = [(number, line.strip(" \t")) for number, line in enumerate(text.split("\n"), 1)
                 if line.strip(" \t") and not line.lstrip(" \t").startswith("#")]
        if not lines or lines[0][1] != "set -euo pipefail":
            return False
        body = "\n".join(line for _, line in lines[1:])
        timed = re.fullmatch(
            r'cd -- "\$\(dirname -- "\$\{BASH_SOURCE\[0\]\}"\)(?P<parents>(?:/\.\.)+)"'
            r'\n(?P<command>exec timeout --signal=TERM --kill-after=30s [0-9]+ python3 '
            r'(?P<child>[A-Za-z0-9_./-]+\.py) [A-Za-z0-9_-]+)', body)
        if timed:
            source = self.source_root(path) or "."
            parent = PurePosixPath(path).parent
            number, target_cwd = lines[-1][0], cwd
            try:
                for _ in range(timed["parents"].count("/")):
                    if str(parent) == source:
                        raise DeliveryError("source-relative launcher escapes its source root")
                    parent = parent.parent
                target_cwd = str(parent)
                target = self.resolve(str(parent / safe_path(timed["child"])), path=path, cwd=".", action=None)
                self.language(target, "python")
                self.add(target, "python", cwd=target_cwd, action=action)
            except DeliveryError as error:
                self.error(path, number, "local-script discovery: " + clean(error))
            self.include([(number, timed["command"])], path, target_cwd, action,
                         self.bases(path, action, [cwd, target_cwd]))
            return True
        root = re.fullmatch(
            r'(?P<anchor>root|ROOT)="\$\(cd "\$\(dirname "\$\{BASH_SOURCE\[0\]\}"\)/\.\." && pwd\)"'
            r'\nexec python3 "\$(?P=anchor)/(?P<child>[A-Za-z0-9_./-]+\.py)"'
            r'(?: --works-root "\$(?P=anchor)")?(?: "\$@")?', body)
        sibling = re.fullmatch(
            r'script="\$\{BASH_SOURCE\[0\]\}"\nif \[\[ "\$script" != \*/\* \]\]; then'
            r'\nscript="\./\$script"\nfi\nexec python3 -- "\$\{script%/\*\}/(?P<child>[A-Za-z0-9_.-]+\.py)"'
            r'(?: --works-root "\$\{script%/\*\}/\.\.")?(?: "\$@")?', body)
        basename = re.fullmatch(
            r'script="\$\{BASH_SOURCE\[0\]\}"\nif \[\[ "\$script" == \*/\* \]\]; then'
            r'\nexec python3 -- "\$\{script%/\*\}/(?P<child>[A-Za-z0-9_.-]+\.py)"\nfi'
            r'\nexec python3 \./(?P=child)', body)
        match = root or sibling or basename
        if match is None:
            return False
        try:
            child = safe_path(match["child"])
            parent = PurePosixPath(path).parent
            if root:
                if str(parent) == "." or str(parent) in self.pins:
                    raise DeliveryError("source-relative launcher escapes its source root")
                parent = parent.parent
            target = self.resolve(str(parent / child), path=path, cwd=".", action=None)
            self.language(target, "python")
            self.add(target, "python", cwd=cwd, action=action)
        except DeliveryError as error:
            self.error(path, lines[-1][0], "local-script discovery: " + clean(error))
        return True

    def commands(self, path, text, cwd, action, *, offset=0, powershell=False, sourced=False):
        # Recognized calls carry the literal working directory. Literal words
        # naming tracked scripts are included afterwards from every base.
        text = text.removeprefix("\ufeff")
        # Replace spaced Actions expressions before shell tokenization.
        text = re.sub(r"\$\{\{\s*github\.(workspace|action_path)\s*\}\}",
                      lambda m: "$GITHUB_WORKSPACE" if m[1] == "workspace" else "$GITHUB_ACTION_PATH", text)
        if powershell:
            self.powershell(path, text, cwd, action, offset=offset, sourced=sourced)
            return
        prologue, first, guard_lines = None, None, range(0)
        if not sourced and not offset and self.files.get(path, {}).get("text") == text:
            if self.source_relative_launcher(path, text, cwd, action):
                return
            prologue = SOURCE_RELATIVE_PROLOGUE.match(text)
            if prologue and prologue["root"] != prologue["scratch"]:
                first = text.count("\n", 0, prologue.start("assignment")) + 1
                if prologue["guard"]:
                    guard_start = text.count("\n", 0, prologue.start("guard")) + 1
                    guard_lines = range(guard_start, guard_start + prologue["guard"].count("\n"))
        # The shell treats CR as part of the delimiter. Do not use the
        # normalized logical lines to prove the boundary in mixed input.
        literal_heredoc = "\r" not in text
        cwds, literals, modules = [cwd], [], []
        source_directory_set = False
        for number, line, data, literal_heredoc_closed, literal_array in self.logical(text, offset, powershell, path):
            for body_number, body, expands in data:
                words = shell_words(body, powershell)
                literals.extend((body_number, word) for word in words)
                modules.extend((body_number, module) for module in self.references(words, path, body_number))
                if expands and re.search(r"\$\(|`", body):
                    self.error(path, body_number, "local-script discovery: unsupported expanding heredoc execution")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            cut, structure, substitution = lexical(line, powershell)
            words = shell_words(line[:cut], powershell)
            literals.extend((number, word) for word in words)
            modules.extend((number, module) for module in self.references(words, path, number))
            try:
                if literal_array or number in guard_lines:
                    continue
                if first == number and line == prologue["assignment"]:
                    # The contiguous prologue assigns the fixed source-relative
                    # directory before a prior cd can change what a relative
                    # BASH_SOURCE means. It allocates scratch and installs cleanup.
                    source_directory_set = True
                    continue
                if source_directory_set and number in (first + 1, first + 2):
                    continue
                if (source_directory_set and number == first + 3
                        and line == prologue[0].rsplit("\n", 1)[1]):
                    parent = PurePosixPath(path).parent
                    source = self.source_root(path) or "."
                    for _ in range(prologue["parents"].count("/")):
                        if str(parent) == source:
                            raise DeliveryError("source-relative launcher escapes its source root")
                        parent = parent.parent
                    cwd = self.segment(["cd", "$GITHUB_WORKSPACE/" + str(parent)],
                                       path, cwd, action, cwds, number, False, False)
                    continue
                if literal_heredoc and literal_heredoc_closed and PYTHON_HEREDOC.fullmatch(line[:cut]):
                    # Every candidate cwd can also be a Python import root.
                    body = "\n".join(word for _, word, _ in data)
                    if len(body) > MAX_LITERAL:
                        raise DeliveryError("execution literal coverage limit exceeded")
                    body_offset = data[0][0] - 1 if data else number
                    for candidate in dict.fromkeys(cwds):
                        self.python(path, body, candidate, action, roots=(candidate,), offset=body_offset)
                    continue
                # Reject execution syntax outside literal quotes before shlex
                # can discard its structure and certify the wrong scope.
                if substitution:
                    raise DeliveryError("unsupported shell command substitution")
                if ("(" in structure or ")" in structure
                        or re.search(r"(?:^|[;&|])\s*\{|(?:^|[;&|])\s*function\b", structure)):
                    raise DeliveryError("unsupported shell compound/subshell execution")
                lex = shlex.shlex(line[:cut], posix=True, punctuation_chars=";&|()")
                if powershell:
                    lex.escape = ""
                lex.whitespace_split, lex.commenters = True, ""
                segments, words = [], []
                for word in lex:
                    if word and set(word) <= set(";&|()"):
                        if words:
                            segments.append(words)
                            words = []
                    else:
                        words.append(word)
                if words:
                    segments.append(words)
                self.environment(segments, line[:cut], powershell)
                for words in segments:
                    cwd = self.segment(words, path, cwd, action, cwds, number, powershell, sourced)
            except (ValueError, RecursionError) as error:
                self.error(path, number, "local-script discovery: " + clean(error))
        for candidate_cwd in dict.fromkeys(cwds):
            self.include(literals, path, candidate_cwd, action, self.bases(path, action, cwds))
            self.include_modules(modules, path, candidate_cwd, action, self.bases(path, action, cwds))

    def powershell(self, path, text, cwd, action, *, offset, sourced):
        """Traverse AST commands inside all branches, functions and expressions.

        Declarations, assignments and data expressions are not command words.
        Literal fallback remains independent of invocation recognition.
        """
        try:
            events = powershell_ast(text)
        except DeliveryError as error:
            self.error(path, offset + 1, "local-script discovery: " + clean(error))
            return
        cwds, literals, modules = [cwd], [], []
        for event in events:
            number, kind = event["line"] + offset, event["kind"]
            if kind == "literal":
                words = [event["text"], *shell_words(event["text"], True)]
                literals.extend((number, word) for word in words)
                modules.extend((number, module) for module in self.references(words, path, number))
                continue
            try:
                if kind == "error":
                    raise DeliveryError("invalid PowerShell syntax: " + event["text"])
                if kind == "unsupported":
                    raise DeliveryError(event["text"])
                if kind == "here-expansion":
                    raise DeliveryError("unsupported expanding heredoc execution")
                if kind == "member":
                    raise DeliveryError("unsupported PowerShell method invocation: " + event["text"])
                if kind == "assignment":
                    for variable in event["variables"]:
                        if variable.lower().startswith("env:"):
                            name = variable[4:].upper()
                            if (name in RESOLUTION or (name == "PATH" and (
                                    not event["simple"] or event["operator"] not in {"Equals", "PlusEquals"}))
                                    or re.search(r"[$`*?]", name)):
                                raise DeliveryError("unsupported environment assignment affecting script resolution")
                        if (variable.lower().startswith(("function:", "alias:"))
                                or variable.split(":")[-1].upper() in {
                                    "PSDEFAULTPARAMETERVALUES", "PSMODULEAUTOLOADINGPREFERENCE", "EXECUTIONCONTEXT"}):
                            raise DeliveryError("unsupported PowerShell assignment affecting command resolution")
                    if not event["simple"]:
                        raise DeliveryError("unsupported PowerShell assignment target")
                    self.environment([], event["text"], True)
                elif kind == "sequence":
                    modules.extend((number, module) for module in self.references(event["values"], path, number))
                elif kind == "module":
                    self.segment(["using", "module", event["text"]], path, cwd, action, cwds, number, True, sourced)
                elif kind == "command":
                    words = [word["value"] for word in event["words"]]
                    modules.extend((number, module) for module in self.references(words, path, number))
                    # A computed command and a script-block invocation must not
                    # become a harmless bare command after token removal.
                    first = event["words"][0]
                    if first["type"] == "ScriptBlockExpressionAst":
                        raise DeliveryError("unsupported shell compound/subshell execution")
                    if first["type"] not in {"StringConstantExpressionAst", "ExpandableStringExpressionAst"}:
                        raise DeliveryError("unresolved computed command: " + words[0])
                    if any(word["splatted"] for word in event["words"]):
                        raise DeliveryError("unresolved PowerShell argument splatting")
                    name = PurePosixPath(words[0]).name.lower().removesuffix(".exe")
                    if name in {"set-alias", "sal", "new-alias", "nal", "import-alias", "ipal", "remove-alias",
                                "new-psdrive", "ndr", "remove-psdrive", "rdr"}:
                        raise DeliveryError("unsupported PowerShell alias mutation affecting command resolution")
                    mutates_provider = (name.partition("-")[0] in {"set", "new", "remove", "clear", "copy",
                                                                  "move", "rename", "add"}
                                        or name in {"si", "ni", "sc", "ri", "cli", "clc", "ac", "cpi", "cp", "copy",
                                                    "mi", "mv", "move", "rni", "ren", "sp", "cpp", "mp", "rnp",
                                                    "rp", "clp", "sv", "rv", "clv"})
                    if (mutates_provider
                            and any(re.match(r"(?i)(?:-\w+:)?(?:alias|function):", word) for word in words[1:])):
                        raise DeliveryError("unsupported PowerShell provider mutation affecting command resolution")
                    if (name not in {"echo", "write-output", "write-host", "cat", "get-content"}
                            and any(word["computed"] for word in event["words"][1:])):
                        raise DeliveryError("unresolved computed PowerShell command operand: " + name)
                    code_words = []
                    if name in {"invoke-expression", "iex", "eval"}:
                        code_words = event["words"][1:]
                    elif name in SHELLS:
                        mode, remaining = self.shell_options(words[1:], SHELLS[name] == "powershell")
                        if mode == "inline" and remaining:
                            code_words = event["words"][-len(remaining):]
                    if any(word["computed"] or word["type"] not in {"StringConstantExpressionAst", "CommandParameterAst"}
                           for word in code_words):
                        raise DeliveryError("unresolved computed command: execution text")
                    redirects = [word for value in event["redirects"] for word in shell_words(value, True)]
                    self.environment([words + redirects], event["text"], True)
                    if event["invocation"] == "Dot":
                        words = [".", *words]
                    cwd = self.segment(words + redirects, path, cwd, action, cwds, number, True, sourced)
            except (ValueError, RecursionError) as error:
                self.error(path, number, "local-script discovery: " + clean(error))
        for candidate_cwd in dict.fromkeys(cwds):
            self.include(literals, path, candidate_cwd, action, self.bases(path, action, cwds))
            self.include_modules(modules, path, candidate_cwd, action, self.bases(path, action, cwds))

    @staticmethod
    def environment_output(words, *, marker="GITHUB_ENV", powershell=False):
        """Understand a small literal producer, or fail the complete write.

        Only a redirection's exact target is a destination. Marker substrings
        inside emitted arguments are ordinary output, including computed data.
        No shell, printf implementation or module code is run to derive bytes.
        """
        destination = re.compile(r"\$(?:" + marker + r"|\{" + marker + r"\}|env:" + marker +
                                 r"|\{env:" + marker + r"\})\Z", re.I)
        label = "$" + marker
        output, remaining, found, index = [], [], False, 0
        while index < len(words):
            word = words[index]
            match = REDIRECTION.fullmatch(word)
            if match and match[2] in {">", ">>", ">|"}:
                target = match[3]
                if not target and index + 1 < len(words):
                    index += 1
                    target = words[index]
                if destination.fullmatch(target):
                    found = True
                elif (environment_names if marker == "GITHUB_ENV" else path_names)(target):
                    raise DeliveryError(f"unresolved {label} write: computed destination")
            else:
                remaining.append(word)
            index += 1
        if not found:
            raise DeliveryError(f"unresolved {label} write: unsupported destination or producer")
        while remaining and assignment(remaining[0]):
            remaining = remaining[1:]
        remaining, stdin = redirections(remaining)
        if not remaining or stdin:
            raise DeliveryError(f"unsupported {label} write output producer")
        name, args = tool(remaining[0]).lower(), remaining[1:]
        for word in args:
            if marker == "GITHUB_ENV" and word.startswith("PATH="):
                check_path(word[5:], message="unsupported $GITHUB_ENV PATH write affecting script resolution")
            candidate = re.sub(r"\$\{?(?:PATH|HOME)\}?", "", word) if word.startswith("PATH=") else word
            if marker == "GITHUB_PATH":
                candidate = re.sub(r"\$(?:HOME(?![A-Za-z0-9_])|\{HOME\})", "", word)
            if "$" in candidate or "`" in candidate:
                raise DeliveryError(f"unresolved {label} write: computed environment name or output")
        if name in {"echo", "write-output", "write-host"}:
            if any(word.startswith("-") or "\\" in word for word in args):
                raise DeliveryError(f"unsupported {label} formatted output")
            separator = "\n" if powershell and name in {"echo", "write-output"} else " "
            result = separator.join(args) + "\n"
            if len(result) > MAX_LITERAL:
                raise DeliveryError("environment output coverage limit exceeded")
            return result
        if name != "printf" or not args:
            raise DeliveryError(f"unsupported {label} write output producer")
        format_string, values = args[0], args[1:]
        # Reject expansion modes, octal/hex escapes, widths and other formatting
        # instead of certifying environment keys by their source spelling.
        if re.search(r"\\(?![ntr\\])|%(?![%s])", format_string):
            raise DeliveryError(f"unsupported {label} formatted output")
        format_string = re.sub(r"\\([ntr\\])", lambda match: {"n": "\n", "t": "\t", "r": "\r", "\\": "\\"}[match[1]],
                               format_string)
        substitutions = list(re.finditer(r"%[%s]", format_string))
        count = sum(match[0] == "%s" for match in substitutions)
        if values and not count:
            raise DeliveryError(f"unsupported {label} formatted output")
        while True:
            cursor = 0
            for match in substitutions:
                output.append(format_string[cursor:match.start()])
                output.append("%" if match[0] == "%%" else (values.pop(0) if values else ""))
                cursor = match.end()
            output.append(format_string[cursor:])
            if sum(map(len, output)) > MAX_LITERAL:
                raise DeliveryError("environment output coverage limit exceeded")
            if not values:
                return "".join(output)

    @staticmethod
    def environment(segments, text, powershell):
        """Unmodeled environment writes that change script or import resolution fail."""
        flat = [word for words in segments for word in words]
        if any(environment_names(word) for word in flat):
            outputs = [Discovery.environment_output(words, powershell=powershell) for words in segments
                       if any(environment_names(word) for word in words)]
            keys = []
            for output in outputs:
                for part in output.split("\n"):
                    if not part:
                        continue
                    match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)(\+?=|<<)(.*)", part, re.S)
                    if match:
                        keys.append((match[1], match[3]))
                    else:
                        raise DeliveryError("unresolved $GITHUB_ENV write: computed environment name or output")
            if not keys:
                raise DeliveryError("unresolved $GITHUB_ENV write: computed environment name")
            for name, value in keys:
                if name.upper() in RESOLUTION:
                    raise DeliveryError("unsupported $GITHUB_ENV write affecting script resolution")
                if name.upper() == "PATH":
                    check_path(value, message="unsupported $GITHUB_ENV PATH write affecting script resolution")
        if any(path_names(word) for word in flat):
            try:
                outputs = [Discovery.environment_output(words, marker="GITHUB_PATH", powershell=powershell)
                           for words in segments if any(path_names(word) for word in words)]
                # AddPathFileCommand uses File.ReadAllLines, whose records
                # split on CRLF, lone CR and LF. GITHUB_ENV and source offsets
                # retain their separate LF-based parsing contracts.
                values = [value for output in outputs for value in re.split(r"\r\n|\r|\n", output) if value]
                if not values or not all(path_component(value.rstrip("/\\") or value) for value in values):
                    raise DeliveryError("unmodeled emitted path output")
            except DeliveryError as error:
                raise DeliveryError("unsupported $GITHUB_PATH change affecting script resolution: " + clean(error)) from None
        if powershell:
            for match in re.finditer(r"(?i)\$\{?env:([A-Za-z_]\w*)\}?\s*(\+?)=(?!=)(.*)", text):
                if match[1].upper() in RESOLUTION:
                    raise DeliveryError("unsupported environment assignment affecting script resolution")
                if match[1].upper() == "PATH":
                    check_path(match[3], append=bool(match[2]))
            for words in segments:
                if words and words[0].lower() in {"set-item", "si", "new-item", "ni", "set-content", "sc",
                                                  "add-content", "ac"}:
                    for word in words[1:]:
                        match = re.fullmatch(r"(?i)(?:-\w+:)?env:([A-Za-z_]\w*)", word)
                        if match and match[1].upper() in RESOLUTION | {"PATH"}:
                            raise DeliveryError("unsupported environment assignment affecting script resolution")

    @staticmethod
    def timeout_command(words):
        """Take a literal GNU timeout duration and its following command."""
        index = 0
        for word in words:
            if word == "--":
                index += 1
                break
            if not word.startswith("-"):
                break
            if not (word in {"--foreground", "--preserve-status", "--verbose"}
                    or re.fullmatch(r"--signal=[A-Z0-9]+", word)
                    or re.fullmatch(r"--kill-after=" + TIMEOUT_DURATION, word)):
                raise DeliveryError("unsupported timeout options")
            index += 1
        if index >= len(words) or not re.fullmatch(TIMEOUT_DURATION, words[index]):
            raise DeliveryError("unresolved timeout duration")
        return words[index + 1:]

    def segment(self, words, path, cwd, action, cwds, number, powershell, sourced):
        """Discover one simple command; return the working directory after it."""
        words, stdin = redirections(words)
        while words and (words[0] in KEYWORDS or assignment(words[0])):
            words = words[1:]
        if not words:
            return cwd
        bases, runner = self.bases(path, action, [*cwds, cwd]), None
        while words and (tool(words[0]) in WRAPPERS or tool(words[0]) in PYTHON_RUNNERS):
            name = tool(words[0])
            words = words[1:]
            if name in PYTHON_RUNNERS:
                runner = name
                if words[:1] and words[0] in {"--version", "-V", "--help", "-h", "help", "version"}:
                    return cwd
                project_words = self.uv_options(words) if name == "uv" else words
                if name != "uv":
                    self.runner_location(words)
                if (project_words[:1] != ["run"] and project_words
                        and project_words[0] not in {"--version", "-V", "--help", "-h", "help", "version"}
                        and self.recipe(("pyproject.toml", "Pipfile", "hatch.toml"), bases)):
                    raise DeliveryError("unsupported project runner with tracked module build/recipes: " + name)
                if project_words[:1] == ["run"]:
                    self.project_preparation(name, words, bases)
                words = self.uv(words) if name == "uv" else self.runner(words)
                if words is None:
                    return cwd
                continue
            if name == "command" and words[:1] in (["-v"], ["-V"]):
                # A non-executing lookup probe.
                return cwd
            if name == "timeout":
                words = self.timeout_command(words)
                continue
            if words and words[0].startswith("-"):
                raise DeliveryError("unsupported shell wrapper options")
            words = words[WRAPPERS[name]:]
            while words and assignment(words[0]):
                words = words[1:]
        if not words:
            raise DeliveryError("unresolved wrapped script invocation")
        cmd, args = words[0], words[1:]
        builtin = cmd.lower()
        base = PurePosixPath(cmd).name.lower().removesuffix(".exe")
        if runner and cmd.split(":")[-1] in self.recipe_names(bases):
            raise DeliveryError("unsupported task runner with tracked module recipes: " + clean(runner))
        if (builtin in {"pushd", "popd", "push-location", "pop-location", "set-location", "sl", "chdir"}
                or (powershell and builtin == "cd")):
            raise DeliveryError("unsupported shell working-directory command")
        if builtin == "start-process":
            raise DeliveryError("unsupported PowerShell process invocation")
        if builtin in {"invoke-command", "icm"}:
            raise DeliveryError("unsupported PowerShell Invoke-Command execution")
        if builtin == "read" and not powershell:
            operands, remaining = [], list(args)
            while remaining:
                value = remaining.pop(0)
                if value == "--":
                    operands += remaining
                    break
                if value.startswith("-"):
                    if re.search(r"[$`]", value):
                        raise DeliveryError("unsupported read environment mutation affecting script resolution")
                    for index, option in enumerate(value[1:], 1):
                        if option not in "adinNptu":
                            continue
                        argument = value[index + 1:] or (remaining.pop(0) if remaining else "")
                        if option == "a":
                            operands.append(argument)
                        break
                    continue
                operands.append(value)
            if any(re.search(r"[$`]", value) or value.split("[", 1)[0].upper() in RESOLUTION | {"PATH"}
                   for value in operands):
                raise DeliveryError("unsupported read environment mutation affecting script resolution")
            return cwd
        if builtin == "printf" and not powershell and args and args[0].startswith("-v"):
            destination = args[0][2:] or (args[1] if len(args) > 1 else "")
            if (not re.fullmatch(r"[A-Za-z_]\w*(?:\[-?\d+\])?", destination)
                    or destination.split("[", 1)[0].upper() in RESOLUTION | {"PATH"}):
                raise DeliveryError("unsupported printf variable write affecting script resolution")
        if builtin in {"export", "declare", "typeset", "readonly", "local"}:
            for argument in args:
                if argument == "--":
                    break
                if builtin in {"declare", "typeset", "local"} and argument.startswith("-") and "n" in argument[1:]:
                    raise DeliveryError("unsupported shell nameref declaration affecting script resolution")
            for argument in args:
                if argument.startswith(("-", "+")):
                    continue
                name, equals, value = argument.partition("=")
                if any(c in name for c in "$`"):
                    raise DeliveryError("unresolved computed environment name")
                if name.removesuffix("+").upper() in RESOLUTION:
                    raise DeliveryError("unsupported environment assignment affecting script resolution")
                if name.removesuffix("+") == "PATH" and equals:
                    check_path(value, append=name.endswith("+"))
            return cwd
        if builtin in {"eval", "invoke-expression", "iex"}:
            if args[:1] and args[0].lower() == "-command":
                args = args[1:]
            if powershell and not args:
                raise DeliveryError("unresolved computed command: missing execution text or pipeline-fed evaluation")
            # Evaluated text runs in this shell, so a directory change inside
            # it fails rather than leaving a stale caller cwd.
            self.commands(path, " ".join(args), cwd, action, offset=number - 1, powershell=powershell, sourced=True)
            return cwd
        if builtin == "trap" and not powershell:
            if args[:1] == ["--"]:
                args = args[1:]
            if args and args[0] != "-" and not args[0].startswith("-"):
                self.commands(path, args[0], cwd, action, offset=number - 1, sourced=True)
            return cwd
        if builtin == "find":
            for index, argument in enumerate(args):
                if argument in {"-execdir", "-okdir"}:
                    raise DeliveryError("unsupported find -execdir working directory")
                if argument in {"-exec", "-ok"}:
                    inner = []
                    for word in args[index + 1:]:
                        if word in {"-exec", "-ok", "-execdir", "-okdir"}:
                            break
                        inner.append(word)
                    if not inner or inner[0] == "{}":
                        raise DeliveryError("unresolved computed find -exec command")
                    self.commands(path, shlex.join(inner), cwd, action, offset=number - 1)
            return cwd
        if base in RECIPES or base in TEST_RUNNERS:
            self.task_runner(base, args, bases)
            return cwd
        if base in NODE_RUNNERS:
            if base == "npm":
                self.npm(args, path, number, cwd, action)
                return cwd
            if base == "bun":
                self.other_language(args, path, cwd, action)
            if any(argument.split("=", 1)[0] in RECIPE_LOCATIONS | {"--workspace", "--workspaces", "-w"} or (
                    argument[:1] == "-" and argument[1:2] != "-" and argument[:2] in RECIPE_LOCATIONS)
                   for argument in args):
                raise DeliveryError("unsupported task runner recipe location: " + clean(base))
            remaining = list(args)
            while remaining and remaining[0].startswith("-"):
                option = remaining.pop(0)
                if option == "--":
                    break
                if option in NODE_SAFE:
                    return cwd
                if option not in NODE_FLAGS:
                    raise DeliveryError("unsupported task runner leading option: " + clean(base))
            subcommand = remaining[0] if remaining else None
            if subcommand == "audit":
                if any(not argument.startswith("-") and argument != "signatures" for argument in remaining[1:]):
                    raise DeliveryError("unsupported mutating npm audit operation")
                return cwd
            if subcommand in NODE_SAFE or (
                    subcommand is None and set(args) & NODE_SAFE):
                return cwd
            if "--ignore-scripts" in args and subcommand in {"install", "ci", "add", "remove", "uninstall"}:
                return cwd
            if self.recipe(("package.json",), bases):
                raise DeliveryError("unsupported task runner with tracked module recipes: " + clean(base))
            raise DeliveryError("unsupported JavaScript task runner execution: " + clean(base))
        if base in {"node", "nodejs", "tsx", "ts-node"}:
            if args in (["--version"], ["-v"], ["--help"]):
                return cwd
            if not args or args[0].startswith("-"):
                raise DeliveryError("unsupported JavaScript interpreter options")
            target = self.resolve(args[0], path=path, cwd=cwd, action=action)
            for suffix in ("node_modules/@playwright/test/cli.js", "node_modules/playwright/cli.js"):
                if target == suffix or target.endswith("/" + suffix):
                    directory = target[:-len(suffix)].rstrip("/") or "."
                    self.npm_workspace(directory, path, number, action)
                    self.playwright(args[1:], path, number, directory, action)
                    return cwd
            fmt = FORMATS.get(PurePosixPath(target).suffix.lower())
            if fmt not in {"javascript", "typescript"}:
                raise DeliveryError("unsupported JavaScript interpreter target")
            self.add(target, fmt, cwd, action)
            return cwd
        if base == "playwright":
            self.npm_workspace(cwd, path, number, action)
            self.playwright(args, path, number, cwd, action)
            return cwd
        if cmd == "cd":
            if sourced:
                raise DeliveryError("sourced script changes caller working directory; coverage unsupported")
            if len(args) != 1 or args[0] == "-":
                raise DeliveryError("unresolved local working directory")
            # A preceding conditional cd may or may not have run. Extend
            # every prior candidate, and keep the before/after contexts.
            established = [self.resolve(args[0], path=path, cwd=base, action=action, allow_root=True)
                           for base in dict.fromkeys([*cwds, cwd])]
            for directory in established:
                if directory not in cwds:
                    if len(cwds) >= 4 * MAX_FILES:
                        raise DeliveryError("working-directory coverage limit exceeded")
                    cwds.append(directory)
            cwd = established[-1]
            return cwd
        fmt, target = None, None
        if re.fullmatch(r"(?:python|pypy)(?:\d+(?:\.\d+)*)?|py", base):
            fmt = "python"
            mode, value, remaining = self.python_options(args)
            if isinstance(value, str) and len(value) > MAX_LITERAL:
                raise DeliveryError("execution literal coverage limit exceeded")
            if mode == "m":
                if not self.import_module(value, path, cwd, action, roots=(cwd,), required=True, execute=True):
                    # An installed runner can still execute tracked recipes or tests.
                    name = value.split(".", 1)[0].replace("_", "-")
                    if name in PYTHON_RUNNERS:
                        self.segment([name, *remaining], path, cwd, action, cwds, number, powershell, sourced)
                    elif (value == "unittest" and remaining[:1] == ["discover"]
                          and {"-s", "--start-directory"}.intersection(remaining[1:])):
                        self.unittest_discovery(remaining, path, cwd, action)
                    else:
                        self.task_runner(name, remaining, bases)
                return cwd
            if mode == "c":
                self.python(path, value, cwd, action, roots=(cwd,), offset=number - 1)
                return cwd
            target = remaining[0] if remaining else None
            if target in {None, "-"}:
                raise DeliveryError("unsupported " + (stdin or "stdin") + "-fed interpreter; coverage unsupported")
        elif base in SHELLS:
            fmt = SHELLS[base]
            mode, remaining = self.shell_options(args, fmt == "powershell")
            if mode == "inline":
                inline = " ".join(remaining) if fmt == "powershell" else (remaining[0] if remaining else None)
                if not inline:
                    raise DeliveryError("unresolved shell command")
                if inline.strip() == "-":
                    raise DeliveryError("unsupported stdin-fed interpreter; coverage unsupported")
                if len(inline) > MAX_LITERAL:
                    raise DeliveryError("execution literal coverage limit exceeded")
                self.commands(path, inline, cwd, action, offset=number - 1, powershell=fmt == "powershell")
                return cwd
            target = remaining[0] if remaining and mode != "stdin" else None
            if target in {None, "-"}:
                raise DeliveryError("unsupported " + (stdin or "stdin") + "-fed interpreter; coverage unsupported")
        elif base in {"node", "nodejs", "deno", "ruby", "perl", "php"}:
            self.other_language(args, path, cwd, action)
        elif powershell and builtin == "using":
            if len(args) >= 2 and args[0].lower() == "module" and (
                    args[1].lower().endswith(".psm1") or any(c in args[1] for c in "/\\$")):
                target, fmt = args[1], "powershell"
        elif cmd in {".", "source"}:
            # Sourcing runs the target in the current shell's language.
            target, fmt = (args[0] if args else None), ("powershell" if powershell else "bash")
        elif cmd.lower() == "import-module":
            if args and args[0].lower() == "-name":
                args = args[1:]
            if not args or args[0].startswith("-"):
                raise DeliveryError("unresolved PowerShell module parameter form")
            if args[0].lower().endswith(".psm1") or any(c in args[0] for c in "/\\$"):
                target, fmt = args[0], "powershell"
        elif FORMATS.get(PurePosixPath(cmd).suffix.lower()) in SCRIPTS:
            target = cmd
        elif cmd.startswith(("./", "../", ".\\", "..\\")) or ("/" in cmd and not cmd.startswith("/")):
            target = cmd
        elif "$" in cmd or "`" in cmd:
            raise DeliveryError("unresolved computed command: " + clean(cmd))
        elif not powershell and cmd == "dotnet" and args and args[0] in DOTNET_BUILD_OPERATIONS:
            # The shell already rejected substitutions. Allow only simple
            # parameter expansion in fixed SDK operations' data arguments.
            for word in args:
                remaining = re.sub(SIMPLE_SHELL_PARAMETER, "", word)
                if "$" in remaining or "`" in remaining:
                    raise DeliveryError("unsupported .NET shell substitution or computed operand")
        elif not powershell and cmd in {"mkdir", "grep"}:
            # These fixed utilities consume file/regex data. Simple parameter
            # expansion cannot make an operand a program or a shell command.
            for word in args:
                if cmd == "mkdir" and word.startswith("-") and word not in {"-p", "--parents", "-v", "--verbose", "--"}:
                    raise DeliveryError("unsupported mkdir option")
                expanded, _ = self.expand(word, path, action)
                remaining = re.sub(SIMPLE_SHELL_PARAMETER, "", expanded)
                if cmd == "grep" and remaining.endswith("$") and not remaining.endswith("$$"):
                    remaining = remaining[:-1]
                if any(value in remaining for value in ("$", "`", "<(", ">(")):
                    raise DeliveryError(f"unsupported {cmd} shell substitution or computed operand")
        elif builtin not in {"echo", "printf", "write-output", "write-host", "cat", "get-content", "[", "[[", "test"}:
            # An unknown consumer cannot certify an unresolved operand as
            # nonexecuting data. Follow a visible execution tool through the
            # precise layer; otherwise fail computed operands conservatively.
            for index, word in enumerate(args):
                name = PurePosixPath(word).name.lower().removesuffix(".exe")
                if (name in SHELLS or name in WRAPPERS or name in PYTHON_RUNNERS or name in {"source", "."}
                        or re.fullmatch(r"(?:python|pypy)(?:\d+(?:\.\d+)*)?|py", name)):
                    self.segment(args[index:], path, cwd, action, cwds, number, powershell, sourced)
                    return cwd
            for word in args:
                expanded, _ = self.expand(word, path, action)
                if "$" in expanded or "`" in expanded:
                    raise DeliveryError("unresolved computed operand of unknown command: " + clean(cmd))
        if target is not None:
            for resolved in self.targets(target, path=path, cwd=cwd, action=action, bases=bases):
                self.language(resolved, fmt)
                self.add(resolved, fmt, cwd=cwd, action=action, sourced=cmd in {".", "source"})
        elif cmd in {".", "source"}:
            raise DeliveryError("unresolved sourced script")
        return cwd

    def other_language(self, args, path, cwd, action):
        for argument in args:
            if PurePosixPath(argument).suffix.lower() in OTHER_LANGUAGES:
                try:
                    resolved = self.resolve(argument, path=path, cwd=cwd, action=action)
                except DeliveryError:
                    continue
                if resolved in self.items:
                    raise DeliveryError("unsupported local-script language: " + clean(resolved))

    def json(self, path):
        """Read regular committed JSON with duplicate keys rejected."""
        path = safe_path(posixpath.normpath(path))
        if not self.regular(path):
            raise DeliveryError("missing or unsafe npm/config input: " + clean(path))
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise DeliveryError("duplicate npm/config JSON key: " + clean(path))
                result[key] = value
            return result
        return json.loads(self.blob(path), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(DeliveryError("non-JSON constant")))

    def npm_workspace(self, directory, path, number, action):
        """Include every tracked JS/TS source in the selected literal workspace."""
        manifest = posixpath.join(directory, "package.json")
        for parent in (PurePosixPath(directory), *PurePosixPath(directory).parents):
            if posixpath.normpath(posixpath.join(str(parent), ".npmrc")) in self.items:
                raise DeliveryError("unsupported tracked npm configuration affecting execution")
        package = self.json(manifest)
        lock = self.json(posixpath.join(directory, "package-lock.json"))
        if (not isinstance(package, dict) or not isinstance(lock, dict)
                or lock.get("lockfileVersion") not in (2, 3) or not isinstance(lock.get("packages"), dict)):
            raise DeliveryError("npm workspace requires a manifest and committed lock")
        self.npm_roots.add(directory)
        prefix = "" if directory == "." else directory + "/"
        for source in sorted(self.items):
            if source.startswith(prefix) and FORMATS.get(PurePosixPath(source).suffix.lower()) in {"javascript", "typescript"}:
                self.add(source, cwd=directory, action=action)
        return package

    def playwright(self, args, path, number, directory, action):
        """Validate fixed installed invocation and follow explicit config overrides."""
        if not args or args[0] not in {"test", "install", "show-report"}:
            raise DeliveryError("unsupported Playwright invocation")
        if any(any(character in argument for character in "$`") for argument in args):
            raise DeliveryError("unresolved computed Playwright invocation")
        args = list(args[1:])
        while args:
            option = args.pop(0)
            key, equal, operand = option.partition("=")
            if key in {"--config", "-c", "--tsconfig", "--reporter"}:
                if not equal:
                    if not args:
                        raise DeliveryError("missing Playwright configuration operand")
                    operand = args.pop(0)
                if key == "--reporter" and not operand.startswith(".") and "/" not in operand:
                    continue
                target = self.resolve(operand, path=path, cwd=directory, action=action)
                if key == "--tsconfig":
                    self.json(target)
                else:
                    self.add(target, cwd=directory, action=action)

    def npm(self, args, path, number, cwd, action):
        """Follow literal npm --prefix/workspace run recipes without executing them."""
        ignore_scripts = "--ignore-scripts" in args
        args, directory, workspace = list(args), cwd, None
        remaining = []
        while args:
            value = args.pop(0)
            if value == "--":
                remaining.extend([value, *args])
                break
            key, equal, operand = value.partition("=")
            if key == "--ignore-scripts" and equal and operand != "true":
                raise DeliveryError("unsupported npm lifecycle-enabling option: " + key)
            if key in {"--prefix", "--workspace", "-w"}:
                if not equal:
                    if not args:
                        raise DeliveryError("unresolved npm workspace directory")
                    operand = args.pop(0)
                if key == "--prefix":
                    directory = self.resolve(operand, path=path, cwd=cwd, action=action, allow_root=True)
                else:
                    workspace = operand
            elif key in {"--workspaces", "--if-present", "--script-shell", "--ignore-scripts=false"}:
                raise DeliveryError("unsupported npm execution option: " + key)
            else:
                remaining.append(value)
        if workspace is not None:
            root = self.json(posixpath.join(directory, "package.json"))
            declared = root.get("workspaces") if isinstance(root, dict) else None
            if not isinstance(declared, list) or any(not isinstance(item, str) or any(c in item for c in "*?{}") for item in declared):
                raise DeliveryError("npm workspace selection requires literal workspace paths")
            if workspace not in declared:
                raise DeliveryError("npm workspace must name a declared literal path")
            directory = self.resolve(workspace, path=path, cwd=directory, action=action)
        while remaining and remaining[0].startswith("-"):
            option = remaining.pop(0)
            if option in NODE_SAFE:
                return
            if option not in NODE_FLAGS:
                raise DeliveryError("unsupported task runner leading option: npm")
        subcommand = remaining.pop(0) if remaining else None
        if subcommand == "audit":
            if any(not argument.startswith("-") and argument != "signatures" for argument in remaining):
                raise DeliveryError("unsupported mutating npm audit operation")
            return
        if subcommand in NODE_SAFE:
            if subcommand == "config" and (not remaining or remaining[0] not in {"get", "list", "ls"}):
                raise DeliveryError("unsupported mutating npm configuration")
            return
        if subcommand in {"install", "ci", "add", "remove", "uninstall"} and ignore_scripts:
            return
        if subcommand not in {"run", "run-script", "test", "start", "stop", "restart"}:
            if self.recipe(("package.json",), [directory]):
                raise DeliveryError("unsupported task runner with tracked module recipes: npm")
            raise DeliveryError("unsupported npm execution without a literal recipe")
        recipe = remaining.pop(0) if subcommand in {"run", "run-script"} and remaining else subcommand
        if not recipe or recipe.startswith("-"):
            raise DeliveryError("unresolved npm recipe")
        package = self.npm_workspace(directory, path, number, action)
        scripts = package.get("scripts", {})
        if not isinstance(scripts, dict) or not isinstance(scripts.get(recipe), str):
            raise DeliveryError("missing or computed npm recipe: " + clean(str(recipe)))
        for selected in ("pre" + recipe, recipe, "post" + recipe):
            if selected not in scripts:
                continue
            if not isinstance(scripts[selected], str):
                raise DeliveryError("unresolved npm lifecycle recipe")
            key = (directory, selected)
            if key in self.npm_seen:
                continue
            self.npm_seen.add(key)
            command = scripts[selected]
            if selected == recipe and remaining:
                command += " " + shlex.join(remaining[1:] if remaining[0] == "--" else remaining)
            self.commands(posixpath.join(directory, "package.json"), command, directory, action)

    def javascript(self, path, text, cwd, action):
        """Resolve parser-proven imports and execution literals; indirection fails."""
        if self.javascript_parser is None:
            raise DeliveryError("trusted TypeScript 6.0.3 parser is unavailable")
        parsed = self.javascript_parser(path, text)
        for number, message in parsed["errors"]:
            self.error(path, number, message)
        bases = self.bases(path, action, [cwd])
        self.include(parsed["literals"], path, cwd, action, bases)
        parent = str(PurePosixPath(path).parent)
        roots = sorted((root for root in self.npm_roots if root == "." or path.startswith(root + "/")), key=len, reverse=True)
        root = roots[0] if roots else parent
        config = posixpath.join(root, "tsconfig.json")
        aliases, base = {}, root
        if config in self.items:
            document = self.json(config)
            if not isinstance(document, dict) or "extends" in document or "references" in document:
                raise DeliveryError("unsupported indirect TypeScript configuration")
            options = document.get("compilerOptions", {})
            if not isinstance(options, dict):
                raise DeliveryError("unsupported TypeScript compilerOptions")
            if "baseUrl" in options:
                base = self.resolve(options["baseUrl"], path=path, cwd=root, action=action, allow_root=True)
            aliases = options.get("paths", {})
            if not isinstance(aliases, dict):
                raise DeliveryError("unsupported TypeScript path aliases")
        for number, imported in parsed["imports"]:
            try:
                targets = []
                if imported.startswith("."):
                    targets = [self.resolve(imported, path=path, cwd=parent, action=action)]
                elif imported.startswith(("/", "\\")) or re.match(r"[A-Za-z]:", imported):
                    raise DeliveryError("unsafe JavaScript import path")
                else:
                    for pattern, replacements in aliases.items():
                        if not isinstance(pattern, str) or pattern.count("*") > 1 or not isinstance(replacements, list):
                            raise DeliveryError("unsupported TypeScript alias")
                        match = re.fullmatch(re.escape(pattern).replace(r"\*", "(.*)"), imported)
                        if match:
                            for replacement in replacements:
                                if not isinstance(replacement, str) or replacement.count("*") > 1:
                                    raise DeliveryError("unsupported TypeScript alias target")
                                targets.append(self.resolve(replacement.replace("*", match[1] if match.lastindex else ""),
                                                            path=path, cwd=base, action=action))
                    if not targets:
                        # Bare imports must come from the locked workspace or Node's builtins.
                        if imported.startswith("node:") or imported in {"fs", "path", "url", "os", "util", "crypto", "assert", "child_process", "process"}:
                            continue
                        package = "/".join(imported.split("/")[:2]) if imported.startswith("@") else imported.split("/")[0]
                        lock = self.json(posixpath.join(root, "package-lock.json"))
                        if "node_modules/" + package not in lock.get("packages", {}):
                            raise DeliveryError("unresolved unlocked JavaScript import: " + clean(imported))
                        continue
                found = False
                for target in targets:
                    stem, suffix = posixpath.splitext(target)
                    candidates = [target, *([stem + extension for extension in (".ts", ".mts", ".cts")] if suffix in {".js", ".mjs", ".cjs"} else []),
                                  *(target + extension for extension in (".ts", ".js", ".mts", ".mjs", ".cts", ".cjs")),
                                  posixpath.join(target, "index.ts"), posixpath.join(target, "index.js")]
                    for candidate in candidates:
                        if candidate in self.items:
                            fmt = FORMATS.get(PurePosixPath(candidate).suffix.lower())
                            if fmt not in {"javascript", "typescript"}:
                                if PurePosixPath(candidate).suffix == ".json":
                                    self.json(candidate)
                                    found = True
                                    continue
                                raise DeliveryError("unsupported local JavaScript import language")
                            self.add(candidate, fmt, cwd, action)
                            found = True
                if not found:
                    raise DeliveryError("missing JavaScript import: " + clean(imported))
            except (ValueError, UnicodeError) as error:
                self.error(path, number, str(error))
        for command in parsed["commands"]:
            directory = self.resolve(command["cwd"], path=path, cwd=cwd, action=action, allow_root=True) if "cwd" in command else cwd
            self.commands(path, command.get("command", shlex.join(command.get("argv", []))), directory, action, offset=command["line"] - 1)

    @staticmethod
    def uv_options(words, run=False):
        """Consume uv options so that an option value never becomes the command.

        For uv run, --script and --gui-script make the target a Python script.
        """
        words, script = list(words), False
        while words and words[0].startswith("-"):
            option = words.pop(0)
            if option == "--":
                break
            key, equals, value = option.partition("=")
            if key in {"--directory", "-C"}:
                raise DeliveryError("unsupported uv working-directory option")
            if key == "--project":
                raise DeliveryError("unsupported uv project recipe-root option")
            if key == "--env-file":
                raise DeliveryError("unsupported uv env file affecting script resolution")
            if key in {"-m", "--module"}:
                module = value if equals else (words.pop(0) if words else None)
                if not module:
                    raise DeliveryError("unresolved python -m target")
                return ["python", "-m", module, *words]
            if key in UV_VALUES:
                if not equals:
                    if not words:
                        raise DeliveryError("unresolved uv option value")
                    words.pop(0)
            elif key not in UV_FLAGS:
                raise DeliveryError("unsupported uv option: " + clean(option))
            script |= run and key in {"--script", "-s", "--gui-script"}
        return ["python", *words] if script else words

    @classmethod
    def uv(cls, words):
        """The command uv run executes, after the caller guards project operations."""
        words = cls.uv_options(words)
        if words[:1] != ["run"]:
            return None
        return cls.uv_options(words[1:], run=True)

    @staticmethod
    def runner_location(words):
        """Check runner selectors before their operands can become subcommands."""
        for word in words:
            if word == "run":
                break
            if (word.split("=", 1)[0] in RECIPE_LOCATIONS or (
                    word[:1] == "-" and word[1:2] != "-" and word[:2] in RECIPE_LOCATIONS)):
                raise DeliveryError("unsupported task runner recipe location")
        if words and words[0].startswith("-") and words[0] not in {"--version", "-V", "--help", "-h"}:
            raise DeliveryError("unsupported task runner option: " + clean(words[0]))

    @staticmethod
    def runner(words):
        """The child command of poetry/pipenv/pdm/hatch run."""
        if words[:1] != ["run"]:
            return None
        words = words[1:]
        if words[:1] == ["--"]:
            words = words[1:]
        if words and words[0].startswith("-"):
            raise DeliveryError("unsupported task runner option: " + clean(words[0]))
        return words

    @staticmethod
    def python_options(args):
        """Parse interpreter options before the script; later words are its arguments."""
        remaining = list(args)
        while remaining and remaining[0].startswith("-") and remaining[0] != "-":
            option = remaining.pop(0)
            if option == "--":
                break
            if option.startswith("--") or re.fullmatch(r"-\d+(?:\.\d+)*(?:-\d+)?", option):
                if option == "--check-hash-based-pycs" and remaining:
                    remaining.pop(0)
                continue
            if option[1] in "WX":
                if len(option) == 2 and remaining:
                    remaining.pop(0)
                continue
            short = re.fullmatch(r"-[bBdEhiIOPqRsSuvVx]*([cm]?)(.*)", option, re.S)
            if not short or (short[2] and not short[1]):
                raise DeliveryError("unsupported Python interpreter option")
            if short[1]:
                value = short[2] or (remaining.pop(0) if remaining else None)
                if value is None:
                    raise DeliveryError("unresolved python -m target" if short[1] == "m" else "unresolved inline Python")
                return short[1], value, remaining
        return None, None, remaining

    @staticmethod
    def shell_options(args, powershell):
        """Parse shell options before the operand; return (None|inline|stdin, remaining)."""
        remaining = list(args)
        while remaining and remaining[0][:1] in {"-", "+"} and remaining[0] not in {"-", "+"}:
            option = remaining.pop(0)
            lower = option.lower()
            if not powershell:
                if option == "--":
                    break
                if option.split("=", 1)[0] in {"--rcfile", "--init-file"}:
                    raise DeliveryError("unsupported shell startup source option")
                elif option.startswith("--"):
                    continue
                elif "c" in option[1:] and option[0] == "-":
                    return "inline", remaining
                elif "s" in option[1:] and option[0] == "-":
                    return "stdin", remaining
                elif option[-1] in "oO":
                    remaining = remaining[1:]
                continue
            # PowerShell parameters are case-insensitive unambiguous prefixes.
            if lower == "-c" or (len(lower) > 4 and "-command".startswith(lower)):
                return "inline", remaining
            if lower in {"-e", "-ec", "-cwa", "-commandwithargs"} or (len(lower) > 2 and "-encodedcommand".startswith(lower)):
                raise DeliveryError("unsupported PowerShell encoded or argument command")
            if lower == "-wd" or (len(lower) > 2 and "-workingdirectory".startswith(lower)):
                raise DeliveryError("unsupported PowerShell working-directory option")
            if lower == "-f" or (len(lower) > 2 and "-file".startswith(lower)):
                break
            if (lower in {"-ep", "-if", "-inputformat", "-of", "-o", "-outputformat", "-v", "-version", "-config",
                          "-configurationname", "-settingsfile", "-w", "-windowstyle"}
                    or (len(lower) > 2 and "-executionpolicy".startswith(lower))):
                remaining = remaining[1:]
        return None, remaining

    def import_path(self, path):
        """A known import component must be a directory, never a git blob/link."""
        parts = path.split("/")
        for index in range(1, len(parts) + 1):
            prefix = "/".join(parts[:index])
            if prefix in self.items and prefix not in self.pins:
                raise DeliveryError("unsafe non-directory Python import path component: " + clean(prefix))

    def add_module(self, target, cwd, action, roots):
        """Importing a module executes every enclosing package initializer."""
        self.import_path(str(PurePosixPath(target).parent))
        if target in self.items:
            self.add(target, "python", cwd=cwd, action=action, python_roots=roots)
        for parent in PurePosixPath(target).parents:
            init = str(parent / "__init__.py")
            if init != target and init in self.items:
                self.add(init, "python", cwd=cwd, action=action, python_roots=roots)

    def import_module(self, module, path, cwd, action, *, roots=None, required=False, relative=0, execute=False):
        if not isinstance(module, str) or not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", module):
            raise DeliveryError("unresolved local Python module")
        parent = str(PurePosixPath(path).parent)
        import_roots = roots if roots is not None else (parent,)
        if relative:
            for _ in range(relative - 1):
                parent = str(PurePosixPath(parent).parent)
            search_roots = (parent,)
        else:
            # Every candidate root: invocation roots, the importer's directory,
            # the working directory and the workspace root. All matches count.
            search_roots = tuple(dict.fromkeys((*import_roots, parent, cwd, ".")))
        selected, executable = [], False
        for root in search_roots:
            stem = posixpath.normpath(posixpath.join(root, module.replace(".", "/")))
            if stem == ".." or stem.startswith("../"):
                continue
            self.import_path(stem)
            candidates = [p for p in (stem + ".py", stem + "/__init__.py") if p in self.items]
            namespace = not candidates and stem not in self.items and stem in self.directories
            if not candidates and not namespace:
                continue
            selected.append(stem)
            for target in candidates:
                self.add_module(target, cwd, action, import_roots)
            if namespace:
                self.add_module(stem + "/__init__.py", cwd, action, import_roots)
            if execute:
                if stem + ".py" in candidates:
                    executable = True
                elif self.regular(stem + "/__main__.py"):
                    self.add(stem + "/__main__.py", "python", cwd=cwd, action=action, python_roots=import_roots)
                    executable = True
        if selected:
            if execute and not executable:
                raise DeliveryError("missing or unsafe regular script/action: " + clean(selected[0] + "/__main__.py"))
            return selected
        if relative:
            raise DeliveryError("missing local Python module: " + clean(module))
        if required:
            # A missing child of a local package is a missing local call; a
            # name without a local top-level package is an installed tool.
            top = module.split(".", 1)[0]
            for root in search_roots:
                stem = posixpath.normpath(posixpath.join(root, top))
                if stem + ".py" in self.items or stem in self.directories:
                    raise DeliveryError("missing local Python module: " + clean(module))
        return None

    def python(self, path, text, cwd, action, *, roots=None, offset=0):
        roots = roots if roots is not None else (str(PurePosixPath(path).parent),)
        try:
            tree = ast.parse(text.removeprefix("\ufeff"))
        except (SyntaxError, ValueError, RecursionError) as error:
            self.error(path, getattr(error, "lineno", 1) + offset, "invalid Python source")
            return
        nodes, parents = [], {}
        for index, node in enumerate(ast.walk(tree)):
            if index > 100000:
                self.error(path, 1, "Python discovery node limit exceeded")
                return
            nodes.append(node)
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        # Imports can occur in functions, classes, conditionals and exception
        # handlers. Retain every static binding rather than letting another
        # scope's reused alias erase an invocation edge. Ambiguous bindings are
        # deliberately conservative: all recognized possibilities are examined.
        aliases = {}
        for node in nodes:
            if isinstance(node, ast.Import):
                for item in node.names:
                    aliases.setdefault(item.asname or item.name, set()).add(item.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                for item in node.names:
                    aliases.setdefault(item.asname or item.name, set()).add(node.module + "." + item.name)

        def names(expression):
            head, dot, tail = expression.partition(".")
            # Subscript writes such as sys.path[:] and an alias[:] have no dot
            # after an aliased list name, so preserve that suffix separately.
            if "[" in head:
                head, bracket, subscript = head.partition("[")
                suffix = bracket + subscript + (dot + tail if dot else "")
            else:
                suffix = dot + tail if dot else ""
            resolved = {target + suffix for target in aliases.get(head, {head})}
            # A literal sys.modules lookup names the same known namespace.
            # Normalize after aliases, preserving precise literal subprocess
            # calls and their computed-target failures.
            for target in tuple(resolved):
                match = re.match(r"sys\.modules\[(['\"])([^'\"]+)\1\](.*)\Z", target)
                if match and match[2] in PROCESS_MODULES:
                    resolved.add(match[2] + match[3])
                match = re.match(r"sys\.modules\.get\((['\"])([^'\"]+)\1\)(.*)\Z", target)
                if match and match[2] in PROCESS_MODULES:
                    resolved.add(match[2] + match[3])
                match = re.match(r"(?:(?:builtins\.)?__import__|importlib\.import_module)"
                                 r"\((['\"])([^'\"]+)\1\)(.*)\Z", target)
                if match and match[2] in PROCESS_MODULES:
                    resolved.add(match[2] + match[3])
            # Keep the namespace identity for reflection checks; also expose
            # direct builtin calls under their ordinary supported spelling.
            return resolved | {target.removeprefix("builtins.") for target in resolved}

        assignments = [node for node in nodes if isinstance(node, (ast.Assign, ast.AnnAssign))]
        for _ in range(8):
            changed = False
            for node in assignments:
                if node.value is None or not isinstance(node.value, (ast.Name, ast.Attribute)):
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                resolved = {candidate for candidate in names(ast.unparse(node.value))
                            if candidate.split(".", 1)[0] in {"subprocess", "importlib", "runpy", "sys", "site", "os",
                                                              "asyncio", "pty", "contextlib", "functools",
                                                              "builtins", "__builtins__"}}
                if not resolved:
                    continue
                for target in targets:
                    if isinstance(target, ast.Name):
                        binding = aliases.setdefault(target.id, set())
                        previous = len(binding)
                        binding.update(resolved)
                        changed |= len(binding) != previous
                        if len(binding) > 100:
                            self.error(path, node.lineno + offset, "Python alias-resolution limit exceeded")
                            return
            if not changed:
                break
        else:
            self.error(path, 1, "Python alias-resolution depth limit exceeded")
            return

        def search_path(expression):
            return any(expression == root or expression.startswith(root + "[")
                       for root in ("sys.path", "sys.meta_path", "sys.path_hooks"))

        # Establish finite source-relative additions before visiting any import.
        # All imports are traversed in all proven roots, including imports that
        # precede the insertion or live in a different branch. This deliberately
        # overapproximates order rather than allowing a path change to hide code.
        def path_value(expression, visible=nodes):
            return self.python_source_path(expression, path, cwd, action, visible, parents, roots=roots)

        proven_paths = set()

        def path_preamble(call):
            """Bound an early top-level insertion to statements already executed."""
            statement = parents.get(call)
            if not isinstance(statement, ast.Expr) or parents.get(statement) is not tree:
                return nodes
            prefix = [tree]
            for entry in tree.body:
                for node in ast.walk(entry):
                    if len(prefix) >= MAX_PYTHON_PROOF_NODES:
                        return nodes
                    prefix.append(node)
                if entry is statement:
                    return prefix
                if isinstance(entry, (ast.Import, ast.ImportFrom)):
                    continue
                if isinstance(entry, ast.Expr) and (entry.value in proven_paths
                        or isinstance(entry.value, ast.Constant) and isinstance(entry.value.value, str)):
                    continue
                if (isinstance(entry, ast.Assign) and len(entry.targets) == 1
                        and isinstance(entry.targets[0], ast.Name)):
                    try:
                        path_value(entry.value, prefix)
                    except (ValueError, TypeError):
                        return nodes
                    continue
                return nodes
            return nodes

        for node in nodes:
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and names(ast.unparse(node.func.value)) == {"sys.path"}
                    and node.func.attr in {"insert", "append"} and not node.keywords):
                arguments = node.args
                if node.func.attr == "insert":
                    if len(arguments) != 2 or not isinstance(arguments[0], ast.Constant) or type(arguments[0].value) is not int:
                        continue
                    arguments = arguments[1:]
                if len(arguments) != 1:
                    continue
                try:
                    visible = path_preamble(node)
                    directory = path_value(arguments[0], visible)
                    self.import_path(directory)
                    if directory != "." and directory not in self.directories:
                        continue
                    if not isinstance(node.func.value, ast.Attribute):
                        continue
                    root = node.func.value.value
                    if not isinstance(root, ast.Name) or not self.proof_import(root.id, "sys", visible, parents):
                        continue
                except (ValueError, TypeError):
                    continue
                proven_paths.add(node)
                roots = tuple(dict.fromkeys((*roots, directory)))

        # A finite composed source path is also useful when it is data to an
        # unknown consumer. Include it without using that consumer to limit
        # reachability, just as we do for ordinary script string literals.
        for node in nodes:
            if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
                continue
            try:
                value = path_value(node)
            except (ValueError, TypeError):
                continue
            self.include([(node.lineno + offset, "$GITHUB_WORKSPACE/" + value)], path, cwd, action,
                         self.bases(path, action, [cwd, *roots]))

        literals, modules, bases, cwds = [], [], [cwd, *roots], [cwd]
        for node in nodes:
            for sequence in sequences(node):
                modules.extend((getattr(node, "lineno", 1) + offset, module)
                               for module in self.references(sequence, path, getattr(node, "lineno", 1) + offset))
            try:
                if (isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) >= 4
                        and "sys.executable" in names(ast.unparse(node.elts[0]))):
                    command, = sequences(node)
                    if command[1:4] == ["-m", "unittest", "discover"]:
                        consumer = parents.get(node)
                        direct = (isinstance(consumer, ast.Call) and consumer.args and consumer.args[0] is node
                                  and names(ast.unparse(consumer.func)) & COMMAND_APIS)
                        if not direct:
                            # Keep test coverage even when a wrapper receives the argv.
                            if any(word is None for word in command[4:]):
                                raise DeliveryError("unresolved unittest discovery arguments")
                            self.unittest_discovery(command[3:], path, cwd, action)
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    literals.append((getattr(node, "lineno", 1) + offset, node.value))
                    # The pinned writer exports one fixed variable and rejects
                    # CR/LF before writing its verified tool-directory value.
                    platform_export = (node.value == "GITHUB_ENV" and path == WORKS_PLATFORM_PREPARE
                                       and node.lineno == 65 and self.works_platform_context(path, cwd, action, offset))
                    if node.value in {"GITHUB_ENV", "GITHUB_PATH"} and not platform_export:
                        raise DeliveryError("unsupported Python access to " + node.value + "; coverage unsupported")
                elif isinstance(node, (ast.Name, ast.Attribute)) and isinstance(node.ctx, ast.Load):
                    if proven_paths and any(search_path(candidate) for candidate in names(ast.unparse(node))):
                        consumer = parents.get(node)
                        if not (isinstance(consumer, ast.Attribute) and consumer.value is node
                                and parents.get(consumer) in proven_paths):
                            raise DeliveryError("unsupported Python search-path mutation or escape")
                    self.reflective(node, parents, names)
                elif isinstance(node, ast.Import):
                    for item in node.names:
                        self.import_module(item.name, path, cwd, action, roots=roots)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if not node.level and module in PROCESS_MODULES and any(item.name == "*" for item in node.names):
                        raise DeliveryError("unsupported star import of a process/import API")
                    resolved = None
                    if module:
                        resolved = self.import_module(module, path, cwd, action, roots=roots, relative=node.level)
                    for item in node.names:
                        if item.name != "*":
                            if resolved:
                                # A from-import can name a package's attribute;
                                # add its submodule only when that file exists.
                                for location in resolved:
                                    stem = location + "/" + item.name
                                    self.import_path(stem)
                                    for candidate in (stem + ".py", stem + "/__init__.py"):
                                        if candidate in self.items:
                                            self.add_module(candidate, cwd, action, roots)
                            elif not module:
                                # Only "from . import name" imports a module by that
                                # name; names from a non-local module are its own.
                                self.import_module(item.name, path, cwd, action, roots=roots, relative=node.level)
                elif (isinstance(node, (ast.Attribute, ast.Subscript))
                      and isinstance(node.ctx, (ast.Store, ast.Del))
                      and any(search_path(candidate) for candidate in names(ast.unparse(node)))):
                    raise DeliveryError("unsupported Python search-path mutation")
                elif (isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del))
                      and names(ast.unparse(node.value)) & ENVIRON and not literal_key(node.slice)):
                    raise DeliveryError("unsupported Python environment mutation affecting resolution")
                elif (isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and any(
                        names(ast.unparse(target)) & ENVIRON
                        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
                        # Rebinding a plain alias name leaves the process environment unchanged.
                        if isinstance(node, ast.AugAssign) or not isinstance(target, ast.Name))):
                    # Replacing or merging into the mapping can set any variable.
                    raise DeliveryError("unsupported Python environment mutation affecting resolution")
                elif isinstance(node, ast.Call):
                    calls = names(ast.unparse(node.func))
                    receiver = parents.get(node)
                    direct_namespace_call = (isinstance(receiver, ast.Attribute)
                                             and isinstance(parents.get(receiver), ast.Call)
                                             and parents[receiver].func is receiver
                                             and any(reflective_api(name) for name in names(ast.unparse(receiver))))
                    if (calls & {"__import__", "builtins.__import__", "importlib.import_module", "sys.modules.get"}
                            and node.args and isinstance(node.args[0], ast.Constant)
                            and node.args[0].value in PROCESS_MODULES
                            and not isinstance(receiver, ast.Expr) and not direct_namespace_call):
                        raise DeliveryError("unsupported reflective use of an imported process/import namespace")
                    for keyword in node.keywords:
                        # A literal subprocess cwd establishes a working directory.
                        if keyword.arg == "cwd" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                            try:
                                directory = self.resolve(keyword.value.value, path=path, cwd=cwd, action=action,
                                                         allow_root=True)
                                bases.append(directory)
                                cwds.append(directory)
                            except DeliveryError:
                                pass
                    mutators = {"append", "insert", "extend", "remove", "pop", "clear", "reverse", "sort",
                                "__setitem__", "__delitem__", "__iadd__", "__imul__"}
                    if (any(candidate.rsplit(".", 1)[-1] in mutators and search_path(candidate.rsplit(".", 1)[0])
                            for candidate in calls) and node not in proven_paths or "site.addsitedir" in calls):
                        raise DeliveryError("unsupported Python search-path mutation")
                    if calls & {"os.chdir", "os.fchdir", "contextlib.chdir"}:
                        raise DeliveryError("unsupported Python working-directory mutation")
                    if calls & {"dotenv.load_dotenv", "dotenv.main.load_dotenv"}:
                        raise DeliveryError("unsupported Python env file affecting script resolution")
                    environment = {call for call in calls if call == "os.putenv" or (
                        call.rsplit(".", 1)[0] in ENVIRON and call.rsplit(".", 1)[-1] in ENVIRON_WRITES)}
                    if environment:
                        if any(call.endswith((".update", ".__ior__")) for call in environment):
                            source = node.args[0] if node.args else ast.Dict(keys=[], values=[])
                            keys = [*source.keys] if isinstance(source, ast.Dict) else [None]
                            keys += [ast.Constant(keyword.arg) if keyword.arg else None for keyword in node.keywords]
                        else:
                            keys = node.args[:1] or [None]
                        if not all(literal_key(key) for key in keys):
                            raise DeliveryError("unsupported Python environment mutation affecting resolution")
                    if "functools.partial" in calls and node.args and any(
                            executes(candidate) for candidate in names(ast.unparse(node.args[0]))):
                        raise DeliveryError("unsupported partial application of a process/import API")
                    for call in sorted(calls):
                        self.python_call(call, node, path, cwd, action, roots, offset, names, parents, nodes)
            except (ValueError, RecursionError) as error:
                self.error(path, getattr(node, "lineno", 1) + offset, "local-script discovery: " + clean(error))
        for candidate_cwd in dict.fromkeys(cwds):
            self.include(literals, path, candidate_cwd, action, self.bases(path, action, bases))
            self.include_modules(modules, path, candidate_cwd, action, self.bases(path, action, bases))

    @staticmethod
    def annotation(node, parents):
        """Whether a reference is (inside) a type annotation."""
        child, parent = node, parents.get(node)
        while isinstance(parent, (ast.Subscript, ast.Tuple, ast.BinOp, ast.Attribute)):
            child, parent = parent, parents.get(parent)
        return ((isinstance(parent, ast.arg) and parent.annotation is child)
                or (isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)) and parent.returns is child)
                or (isinstance(parent, ast.AnnAssign) and parent.annotation is child))

    def python_source_path(self, expression, path, cwd, action, nodes, parents, *, roots=None):
        """Resolve immutable pathlib paths anchored to this committed source.

        No cwd(), ambient environment, arbitrary factory, function return or
        mutable/ambiguous binding is a source anchor. The proof examines every
        scope for shadowing and reflection and never imports the module's code.
        """
        if not self.proof_namespace_safe(nodes):
            raise ValueError("unsupported source-path namespace or proof limit")
        if any(isinstance(entry, ast.Attribute) and entry.attr in {"__class__", "__mro__", "__subclasses__"}
               or isinstance(entry, ast.Call) and isinstance(entry.func, ast.Name) and entry.func.id == "type"
               for entry in nodes):
            raise ValueError("unsupported source-path class reflection")
        if self.script_format(path) != "python" or self.proof_bindings("__file__", nodes):
            raise ValueError("untrusted Python source anchor")

        def factory(node):
            if isinstance(node, ast.Name):
                bindings = self.proof_bindings(node.id, nodes)
                if len(bindings) != 1 or not isinstance(bindings[0], ast.alias):
                    return False
                declaration = parents.get(bindings[0])
                if (not isinstance(declaration, ast.ImportFrom) or declaration.module != "pathlib"
                        or declaration.level or bindings[0].name != "Path"
                        or not isinstance(parents.get(declaration), ast.Module)):
                    return False
                # A class object that escapes can have its methods replaced.
                for entry in nodes:
                    if isinstance(entry, ast.Name) and isinstance(entry.ctx, ast.Load) and entry.id == node.id:
                        consumer = parents.get(entry)
                        if not (isinstance(consumer, ast.Call) and consumer.func is entry or self.annotation(entry, parents)):
                            return False
                return not self.import_module("pathlib", path, cwd, action, roots=roots)
            if (isinstance(node, ast.Attribute) and node.attr == "Path" and isinstance(node.value, ast.Name)
                    and self.proof_import(node.value.id, "pathlib", nodes, parents)):
                # Reject aliases or escapes of the class, including method writes.
                for entry in nodes:
                    if (isinstance(entry, ast.Attribute) and entry.attr == "Path"
                            and isinstance(entry.value, ast.Name) and entry.value.id == node.value.id):
                        consumer = parents.get(entry)
                        if not (isinstance(consumer, ast.Call) and consumer.func is entry or self.annotation(entry, parents)):
                            return False
                return not self.import_module("pathlib", path, cwd, action, roots=roots)
            return False

        def native_str(node):
            return isinstance(node, ast.Name) and node.id == "str" and not self.proof_bindings("str", nodes)

        def literal_path(value, base):
            # pathlib does not expand shell or Actions anchors, nor does POSIX
            # pathlib interpret backslashes as separators. Do not reuse those
            # conveniences from shell resolution for Python path components.
            if "\\" in value or any(character in value for character in "$`*?{}~"):
                raise ValueError("unsupported source-path component")
            return self.resolve(value, path=path, cwd=base, action=None, allow_root=True)

        def source_parent(value):
            if value == "." or value in self.pins:
                raise ValueError("source path escapes its committed root")
            return str(PurePosixPath(value).parent)

        def resolve(node, stack=()):
            if len(stack) > 8:
                raise ValueError("source-path expansion limit exceeded")
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) <= MAX_LITERAL:
                return literal_path(node.value, cwd), False
            if isinstance(node, ast.Name):
                if node.id == "__file__":
                    return path, True
                if node.id in stack:
                    raise ValueError("recursive source-path binding")
                bindings = self.proof_bindings(node.id, nodes)
                if len(bindings) != 1 or not isinstance(bindings[0], ast.Name):
                    raise ValueError("ambiguous source-path binding")
                definition = parents.get(bindings[0])
                if (not isinstance(definition, (ast.Assign, ast.AnnAssign)) or definition.value is None
                        or not isinstance(parents.get(definition), ast.Module)
                        or isinstance(definition, ast.Assign) and len(definition.targets) != 1
                        or definition.lineno >= getattr(expression, "lineno", 0)):
                    raise ValueError("unsupported source-path binding")
                # The immutable path may be consumed, but not rebound via an
                # attribute/subscript write through the selected name.
                for entry in nodes:
                    if isinstance(entry, (ast.Attribute, ast.Subscript)) and isinstance(entry.ctx, (ast.Store, ast.Del)):
                        base = entry.value
                        while isinstance(base, (ast.Attribute, ast.Subscript)):
                            base = base.value
                        if isinstance(base, ast.Name) and base.id == node.id:
                            raise ValueError("mutated source-path binding")
                return resolve(definition.value, (*stack, node.id))
            if isinstance(node, ast.Call) and not node.keywords:
                if len(node.args) == 1 and (factory(node.func) or native_str(node.func)):
                    return resolve(node.args[0], stack)
                if (not node.args and isinstance(node.func, ast.Attribute) and node.func.attr == "resolve"):
                    value, anchored = resolve(node.func.value, stack)
                    if anchored:
                        if value in self.items and value not in self.pins and not self.regular(value):
                            raise ValueError("unsafe resolved source-path component")
                        return value, True
            if isinstance(node, ast.Attribute) and node.attr == "parent":
                value, anchored = resolve(node.value, stack)
                if anchored and value != ".":
                    return source_parent(value), True
            if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "parents"
                    and isinstance(node.slice, ast.Constant) and type(node.slice.value) is int and 0 <= node.slice.value <= 8):
                value, anchored = resolve(node.value.value, stack)
                if anchored:
                    for _ in range(node.slice.value + 1):
                        value = source_parent(value)
                    return value, True
            if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
                    and isinstance(node.right, ast.Constant) and isinstance(node.right.value, str)
                    and len(node.right.value) <= MAX_LITERAL):
                value, anchored = resolve(node.left, stack)
                if anchored:
                    return literal_path(node.right.value, value), True
            raise ValueError("unresolved source-relative Python path")

        value, anchored = resolve(expression)
        if not anchored:
            raise ValueError("Python path lacks a committed source anchor")
        # Callers distinguish scripts from working/import directories and check
        # the final component; literal_path already checked traversed prefixes.
        return value

    def reflective(self, node, parents, names):
        """A process/import API reached other than by a direct call is unmodeled."""
        parent = parents.get(node)
        candidates = names(ast.unparse(node))
        if (isinstance(parent, ast.Call) and parent.func is node
                and candidates & {"__import__", "builtins.__import__"}):
            return
        if any(".__" in candidate and (candidate.split(".__", 1)[0] in PROCESS_MODULES
                                       or reflective_api(candidate.split(".__", 1)[0]))
               for candidate in candidates):
            raise DeliveryError("unsupported reflective use of a process/import API")
        if isinstance(parent, ast.Attribute) and parent.value is node:
            return
        if not any(reflective_api(c) or c in PROCESS_MODULES for c in candidates):
            return
        if isinstance(parent, ast.Call) and parent.func is node:
            return
        if isinstance(parent, (ast.Expr, ast.Compare)) or self.annotation(node, parents):
            return
        if isinstance(parent, (ast.Assign, ast.AnnAssign)) and parent.value is node:
            # A plain name alias is resolved statically; an attribute,
            # class-body, tuple or other store is not.
            targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
            if all(isinstance(target, ast.Name) for target in targets) and not isinstance(
                    parents.get(parent), ast.ClassDef):
                return
        if isinstance(parent, ast.Call) and node in parent.args:
            callee = names(ast.unparse(parent.func))
            if callee & BENIGN:
                return
            if "getattr" in callee and parent.args[0] is node:
                attribute = parent.args[1] if len(parent.args) > 1 else None
                if (isinstance(attribute, ast.Constant) and isinstance(attribute.value, str)
                        and not attribute.value.startswith("__")
                        and not any(reflective_api(c + "." + attribute.value) or c + "." + attribute.value
                                    in PROCESS_MODULES for c in candidates)):
                    return
                raise DeliveryError("unsupported reflective getattr of a process/import API")
        raise DeliveryError("unsupported reflective use of a process/import API: " + clean(sorted(candidates)[0]))

    @staticmethod
    def copied_environment(value, invocation, parents, all_nodes, names, *, protected_process_prefixes=()):
        """Prove an unaliased local environment copy leaves interpreter lookup unchanged."""
        if not isinstance(value, ast.Name) or len(all_nodes) > 4096:
            return False
        scope = parents.get(invocation)
        while scope is not None and not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            scope = parents.get(scope)
        if scope is None:
            return False
        nodes = list(ast.walk(scope))
        if len(nodes) > 4096:
            return False
        definitions = [entry for entry in scope.body if isinstance(entry, ast.Assign)
                       and len(entry.targets) == 1 and isinstance(entry.targets[0], ast.Name)
                       and entry.targets[0].id == value.id]
        if len(definitions) != 1:
            return False
        definition = definitions[0]
        if Discovery.proof_bindings(value.id, nodes) != [definition.targets[0]]:
            return False
        copy = definition.value
        if (not isinstance(copy, ast.Call) or copy.args or copy.keywords
                or not isinstance(copy.func, ast.Attribute) or copy.func.attr != "copy"
                or names(ast.unparse(copy.func.value)) != {"os.environ"}):
            return False
        source = copy.func.value
        while isinstance(source, ast.Attribute):
            source = source.value
        if not isinstance(source, ast.Name):
            return False
        source_name = source.id
        if len(Discovery.proof_bindings(source_name, all_nodes)) != 1:
            return False
        imported = False
        for entry in all_nodes:
            if isinstance(entry, ast.Import):
                for item in entry.names:
                    if (item.asname or item.name) == source_name:
                        if item.name != "os":
                            return False
                        imported = True
            elif isinstance(entry, ast.ImportFrom):
                for item in entry.names:
                    if (item.asname or item.name) == source_name:
                        if entry.module != "os" or item.name != "environ" or entry.level:
                            return False
                        imported = True
            elif ((isinstance(entry, ast.Name) and isinstance(entry.ctx, (ast.Store, ast.Del)) and entry.id == source_name)
                  or (isinstance(entry, ast.arg) and entry.arg == source_name)
                  or (isinstance(entry, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and entry.name == source_name)):
                return False
            elif isinstance(entry, (ast.Attribute, ast.Subscript)) and isinstance(entry.ctx, (ast.Store, ast.Del)):
                if any(candidate == "os.environ" or candidate.startswith("os.environ.")
                       or candidate.startswith("os.environ[")
                       or candidate == "os.devnull" for candidate in names(ast.unparse(entry))):
                    return False
            elif isinstance(entry, (ast.Name, ast.Attribute)) and isinstance(entry.ctx, ast.Load):
                if names(ast.unparse(entry)) == {"os.environ"}:
                    access = parents.get(entry)
                    access_call = parents.get(access)
                    if (not isinstance(access, ast.Attribute) or access.attr not in {"copy", "get"}
                            or not isinstance(access_call, ast.Call) or access_call.func is not access):
                        return False
            elif isinstance(entry, ast.Call):
                # Neither the source module nor its mutable mapping may escape
                # into an unknown callback before the supposedly honest copy.
                if (names(ast.unparse(entry.func)) & {"globals", "locals", "vars", "setattr", "delattr"}
                        or any(names(ast.unparse(argument)) & {"os", "os.environ"}
                               for argument in [*entry.args, *(keyword.value for keyword in entry.keywords)])):
                    return False
        if not imported:
            return False
        container = invocation
        while parents.get(container) is not scope:
            container = parents.get(container)
            if container is None:
                return False
        if scope.body.index(definition) >= scope.body.index(container):
            return False

        protected = RESOLUTION | {"PATH", "BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS", "ZDOTDIR", "FPATH"}
        protected_prefixes = ("PYTHON", "NODE", "NPM_CONFIG_", "PS", "POWERSHELL", *protected_process_prefixes)
        def safe_key(key):
            return isinstance(key, str) and key.upper() not in protected and not key.upper().startswith(protected_prefixes)
        def safe_prefix(prefix):
            return (isinstance(prefix, str) and bool(prefix) and safe_key(prefix)
                    and not any(key.startswith(prefix.upper()) for key in protected)
                    and not any(key.startswith(prefix.upper()) or prefix.upper().startswith(key) for key in protected_prefixes))
        def data(expression):
            return (isinstance(expression, ast.Constant) and isinstance(expression.value, str)
                    or isinstance(expression, ast.Attribute) and names(ast.unparse(expression)) == {"os.devnull"}
                    and isinstance(expression.value, ast.Name) and expression.value.id == source_name)
        def receiver(call, method):
            return (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name) and call.func.value.id == value.id and call.func.attr == method)
        allowed = {definition.targets[0], value}
        for entry in nodes:
            if isinstance(entry, ast.Call) and names(ast.unparse(entry.func)) <= COMMAND_APIS:
                allowed.update(keyword.value for keyword in entry.keywords if keyword.arg == "env"
                               and isinstance(keyword.value, ast.Name) and keyword.value.id == value.id)
        for statement in scope.body[scope.body.index(definition) + 1:scope.body.index(container)]:
            valid = False
            if isinstance(statement, ast.Expr) and receiver(statement.value, "update"):
                update = statement.value
                values = []
                if not update.args:
                    values = [(item.arg, item.value) for item in update.keywords]
                elif len(update.args) == 1 and not update.keywords and isinstance(update.args[0], ast.Dict):
                    values = [(key.value if isinstance(key, ast.Constant) else None, item)
                              for key, item in zip(update.args[0].keys, update.args[0].values)]
                valid = bool(values) and all(safe_key(key) and data(item) for key, item in values)
            elif isinstance(statement, ast.For) and isinstance(statement.target, ast.Name) and not statement.orelse:
                iterate = statement.iter
                if (isinstance(iterate, ast.Call) and isinstance(iterate.func, ast.Name) and iterate.func.id == "tuple"
                        and len(iterate.args) == 1 and not iterate.keywords and isinstance(iterate.args[0], ast.Name)
                        and iterate.args[0].id == value.id and len(statement.body) == 1
                        and isinstance(statement.body[0], ast.If) and not statement.body[0].orelse):
                    branch = statement.body[0]
                    test = branch.test
                    pop = branch.body[0].value if len(branch.body) == 1 and isinstance(branch.body[0], ast.Expr) else None
                    valid = (isinstance(test, ast.Call) and isinstance(test.func, ast.Attribute)
                             and isinstance(test.func.value, ast.Name) and test.func.value.id == statement.target.id
                             and test.func.attr == "startswith" and len(test.args) == 1 and not test.keywords
                             and isinstance(test.args[0], ast.Constant) and safe_prefix(test.args[0].value)
                             and receiver(pop, "pop") and len(pop.args) == 1 and not pop.keywords
                             and isinstance(pop.args[0], ast.Name) and pop.args[0].id == statement.target.id)
                    # A shadowed iteration helper can mutate the copy itself.
                    if Discovery.proof_bindings("tuple", all_nodes):
                        valid = False
            if valid:
                allowed.update(item for item in ast.walk(statement) if isinstance(item, ast.Name) and item.id == value.id)
        return all(entry in allowed for entry in nodes if isinstance(entry, ast.Name) and entry.id == value.id)

    @staticmethod
    def proof_bindings(name, nodes):
        """All syntactic bindings, including forms that have no Name(Store) node."""
        result = []
        for entry in nodes:
            if (isinstance(entry, ast.Name) and isinstance(entry.ctx, (ast.Store, ast.Del)) and entry.id == name
                    or isinstance(entry, ast.arg) and entry.arg == name
                    or isinstance(entry, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and entry.name == name
                    or isinstance(entry, ast.ExceptHandler) and entry.name == name
                    or isinstance(entry, (ast.MatchAs, ast.MatchStar)) and entry.name == name
                    or isinstance(entry, ast.MatchMapping) and entry.rest == name
                    or isinstance(entry, (ast.Global, ast.Nonlocal)) and name in entry.names):
                result.append(entry)
            elif isinstance(entry, ast.Import):
                result.extend(item for item in entry.names if (item.asname or item.name.split(".")[0]) == name)
            elif isinstance(entry, ast.ImportFrom):
                result.extend(item for item in entry.names if (item.asname or item.name) == name)
        return result

    @staticmethod
    def proof_namespace_safe(nodes):
        """Reflection can replace bindings without a visible assignment; refuse that subset."""
        reflective = {"globals", "locals", "vars", "getattr", "setattr", "delattr", "exec", "eval", "__import__"}
        attributes = reflective | {"__dict__", "__globals__", "__code__", "__closure__", "__setattr__", "f_globals", "f_locals", "modules"}
        return len(nodes) <= MAX_PYTHON_PROOF_NODES and not any(
            isinstance(entry, ast.Call) and isinstance(entry.func, ast.Name) and entry.func.id in reflective
            or isinstance(entry, ast.Attribute) and entry.attr in attributes
            or isinstance(entry, ast.ImportFrom) and any(item.name == "*" or entry.module == "builtins"
                                                       and item.name in reflective for item in entry.names)
            for entry in nodes)

    @staticmethod
    def proof_function(name, nodes, parents, *, nested=False):
        bindings = Discovery.proof_bindings(name, nodes)
        if (len(bindings) != 1 or not isinstance(bindings[0], ast.FunctionDef) or bindings[0].decorator_list
                or not isinstance(parents.get(bindings[0]), (ast.Module, ast.FunctionDef) if nested else ast.Module)):
            return None
        if any(isinstance(entry, ast.Name) and isinstance(entry.ctx, ast.Load) and entry.id == name
               and (not isinstance(parents.get(entry), ast.Call) or parents[entry].func is not entry) for entry in nodes):
            return None
        return bindings[0]

    @staticmethod
    def proof_import(name, module, nodes, parents):
        bindings = Discovery.proof_bindings(name, nodes)
        if len(bindings) != 1 or not isinstance(bindings[0], ast.alias):
            return False
        declaration = parents.get(bindings[0])
        if (not isinstance(declaration, ast.Import) or bindings[0].name != module
                or not isinstance(parents.get(declaration), ast.Module)):
            return False
        def base(entry):
            while isinstance(entry, (ast.Attribute, ast.Subscript)):
                entry = entry.value
            return entry.id if isinstance(entry, ast.Name) else None
        return not any(
            isinstance(entry, (ast.Attribute, ast.Subscript)) and isinstance(entry.ctx, (ast.Store, ast.Del)) and base(entry) == name
            or isinstance(entry, ast.Name) and isinstance(entry.ctx, ast.Load) and entry.id == name
            and (not isinstance(parents.get(entry), ast.Attribute) or parents[entry].value is not entry)
            for entry in nodes)

    @staticmethod
    def forwarded_argv(expression, invocation, parents, nodes):
        """Expand only direct immutable *args forwarding and finite literal tuple loops."""
        if not Discovery.proof_namespace_safe(nodes):
            raise ValueError("unsafe forwarded namespace or proof limit")
        functions = {}
        for entry in nodes:
            if isinstance(entry, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.setdefault(entry.name, []).append(entry)
        def owner(entry):
            while entry is not None and not isinstance(entry, (ast.FunctionDef, ast.AsyncFunctionDef)):
                entry = parents.get(entry)
            return entry
        def sequence(items, at, stack):
            if len(stack) > 8 or len(items) > 256:
                raise ValueError("forwarded argv expansion limit exceeded")
            choices = [[]]
            for item in items:
                alternatives = variable(item.value, at, stack) if isinstance(item, ast.Starred) else [[item]]
                if len(choices) * len(alternatives) > 128:
                    raise ValueError("forwarded argv expansion limit exceeded")
                choices = [left + right for left in choices for right in alternatives]
                if len(choices) > 128 or any(len(choice) > 256 for choice in choices):
                    raise ValueError("forwarded argv expansion limit exceeded")
            return choices
        def variable(item, at, stack):
            if (isinstance(item, ast.Tuple) and len(item.elts) <= 256
                    and all(isinstance(value, ast.Constant) and isinstance(value.value, str) for value in item.elts)):
                return [item.elts]
            if not isinstance(item, ast.Name):
                raise ValueError("unresolved forwarded argv")
            bindings = Discovery.proof_bindings(item.id, nodes)
            if len(bindings) == 1 and isinstance(bindings[0], ast.Name):
                definition = parents.get(bindings[0])
                if (isinstance(definition, ast.Assign) and len(definition.targets) == 1
                        and isinstance(parents.get(definition), ast.Module)
                        and isinstance(definition.value, ast.Tuple)):
                    return variable(definition.value, at, stack)
            scope = owner(at)
            cursor = at
            while cursor is not None and cursor is not scope:
                if (isinstance(cursor, ast.For) and isinstance(cursor.target, ast.Name)
                        and cursor.target.id == item.id and not cursor.orelse):
                    literal = ast.literal_eval(cursor.iter)
                    if (not isinstance(literal, (tuple, list)) or not literal or len(literal) > 128
                            or any(not isinstance(row, tuple) or len(row) > 256
                                   or any(not isinstance(value, str) for value in row) for row in literal)
                            or Discovery.proof_bindings(item.id, list(ast.walk(cursor))) != [cursor.target]):
                        raise ValueError("unresolved forwarded tuple loop")
                    return [[ast.Constant(value) for value in row] for row in literal]
                cursor = parents.get(cursor)
            if (scope is None or scope.decorator_list or scope.args.vararg is None or scope.args.vararg.arg != item.id
                    or len(functions.get(scope.name, [])) != 1 or scope.name in stack
                    or Discovery.proof_function(scope.name, nodes, parents, nested=True) is not scope
                    or Discovery.proof_bindings(item.id, list(ast.walk(scope))) != [scope.args.vararg]):
                raise ValueError("unresolved forwarded argv")
            # A wrapper alias, callback, shadowed callable or **kwargs cannot
            # silently introduce callers outside this finite direct-call graph.
            if any(isinstance(entry, ast.Name) and entry.id == scope.name
                   and (not isinstance(entry.ctx, ast.Load) or not isinstance(parents.get(entry), ast.Call)
                        or parents[entry].func is not entry) for entry in nodes):
                raise ValueError("unsafe forwarded wrapper indirection")
            if any(isinstance(entry, ast.arg) and entry.arg == scope.name for entry in nodes):
                raise ValueError("shadowed forwarded wrapper")
            calls = [entry for entry in nodes if isinstance(entry, ast.Call)
                     and isinstance(entry.func, ast.Name) and entry.func.id == scope.name]
            if not calls or len(calls) > 128:
                raise ValueError("unresolved forwarded wrapper callers")
            result = []
            fixed = len(scope.args.posonlyargs) + len(scope.args.args)
            for caller in calls:
                if any(keyword.arg is None for keyword in caller.keywords) or len(caller.args) < fixed:
                    raise ValueError("unresolved forwarded wrapper options")
                result.extend(sequence(caller.args[fixed:], caller, (*stack, scope.name)))
                if len(result) > 128:
                    raise ValueError("forwarded argv expansion limit exceeded")
            return result
        if isinstance(expression, (ast.List, ast.Tuple)):
            return sequence(expression.elts, invocation, ())
        return variable(expression, invocation, ())

    @staticmethod
    def git_data_argv(arguments):
        """Prove the Git operation and its option boundaries without running Git."""
        literal = lambda item: item.value if isinstance(item, ast.Constant) and isinstance(item.value, str) else None
        if not arguments or literal(arguments[0]) != "git":
            return False
        index = 1
        while index + 1 < len(arguments) and literal(arguments[index]) == "-C":
            index += 2
        if index >= len(arguments):
            return False
        verb = literal(arguments[index])
        flags = GIT_READ_FLAGS.get(verb, GIT_LOCAL_FLAGS.get(verb))
        if flags is None:
            return False
        words = [literal(item) for item in arguments[index + 1:]]
        if verb == "remote":
            if words[:1] != ["get-url"]:
                return False
            words = words[1:]
        separator = "--" in words
        stop = words.index("--") if separator else len(words)
        before, after = words[:stop], words[stop + 1:]
        before_flags = [word for word in before if word is not None and word.startswith("-")]
        if any(word not in flags and word.split("=", 1)[0] not in flags
               and not any(option.endswith("=") and word.startswith(option) for option in flags)
               for word in before_flags):
            return False
        if verb in GIT_LOCAL_FLAGS:
            if not separator or None in before:
                return False
            if verb == "checkout":
                return "--detach" in before_flags and len(before) == len(before_flags) + 1 and not after
            if len(before) != len(before_flags) or not after or not after[0]:
                return False
            if not re.fullmatch(r"(?:\./|\.\./|/(?!/))[^:\\]+", after[0]):
                return False
            if verb == "clone":
                return "--no-checkout" in before_flags and len(after) == 2
            return ({"--no-auto-maintenance", "--no-recurse-submodules"} <= set(before_flags)
                    and len(after) >= 2)
        # These modes can interpret an opaque revision as an option. An
        # explicit terminator keeps it in the operand portion of the argv.
        if verb in {"diff", "show"} and "--end-of-options" in before:
            before = before[:before.index("--end-of-options")]
        if verb in {"archive", "diff", "show"} and None in before:
            return False
        if verb == "cat-file" and None in before:
            return (len(before) == 2 and before[0] in {"-t", "-s", "-e", "-p", "blob", "tree", "commit", "tag"}
                    and before[1] is None)
        return True

    @staticmethod
    def conditional_env_keywords(keywords):
        """Expand conditional mappings that supply only the subprocess env keyword."""
        result = []
        for keyword in keywords:
            if keyword.arg is not None:
                result.append(keyword)
                continue
            if not isinstance(keyword.value, ast.IfExp):
                raise DeliveryError("unresolved subprocess positional/options expansion")
            for branch in (keyword.value.body, keyword.value.orelse):
                if not isinstance(branch, ast.Dict) or (branch.keys and (
                        len(branch.keys) != 1 or not isinstance(branch.keys[0], ast.Constant)
                        or branch.keys[0].value != "env")):
                    raise DeliveryError("unresolved subprocess positional/options expansion")
                result.extend(ast.keyword(arg="env", value=value) for value in branch.values)
        return result

    def git_subprocess_argv(self, first, node, call, path, cwd, action, roots, parents, nodes):
        """Return the finite argv forms of a literal subprocess Git operation."""
        if call in {"subprocess.getoutput", "subprocess.getstatusoutput"}:
            return ()
        sequence = isinstance(first, (ast.List, ast.Tuple))
        if sequence and (not first.elts or isinstance(first.elts[0], ast.Constant)
                         and first.elts[0].value != "git"):
            return ()
        expanded = sequence and any(isinstance(item, ast.Starred) for item in first.elts)
        if not isinstance(first, ast.Name) and not expanded and (
                not sequence or not isinstance(first.elts[0], ast.Constant)):
            return ()
        standard_api = (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                        and self.proof_import(node.func.value.id, "subprocess", nodes, parents))
        if isinstance(node.func, ast.Name):
            bindings = self.proof_bindings(node.func.id, nodes)
            declaration = parents.get(bindings[0]) if len(bindings) == 1 else None
            standard_api = (isinstance(declaration, ast.ImportFrom) and declaration.module == "subprocess"
                            and declaration.level == 0 and isinstance(parents.get(declaration), ast.Module))
        if sequence and not expanded:
            variants = [first.elts]
        else:
            if not standard_api:
                return ()
            try:
                variants = self.forwarded_argv(first, node, parents, nodes)
            except (ValueError, TypeError, SyntaxError):
                return ()
        if not any(variant and isinstance(variant[0], ast.Constant) and variant[0].value == "git"
                   for variant in variants):
            return ()
        if not standard_api or self.import_module("subprocess", path, cwd, action, roots=roots):
            raise DeliveryError("unproved subprocess API for Git discovery")
        if any(posixpath.basename(item).lower() in {"git", "git.exe", "git.cmd", "git.bat", "git.com"}
               for item in self.items):
            raise DeliveryError("unproved Git executable: tracked Git command")
        if not all(self.git_data_argv(variant) for variant in variants):
            raise DeliveryError("unsupported Git mode or unresolved Git options")
        return variants

    def include_git_operands(self, variants, path, cwd, action, line):
        """Include ordinary literal references below proved literal Git directories."""
        for variant in variants:
            words = [item.value if isinstance(item, ast.Constant) and isinstance(item.value, str) else None
                     for item in variant]
            index, directory = 1, cwd
            while words[index:index + 1] == ["-C"] and words[index + 1] is not None:
                if words[index + 1]:
                    operand = words[index + 1]
                    expanded, anchored = self.expand(operand, path, action)
                    candidate = posixpath.normpath(posixpath.join("." if anchored else directory, expanded))
                    if (candidate == ".." or candidate.startswith(("/", "../"))
                            or re.match(r"^[A-Za-z]:/", candidate) or any(char in expanded for char in "$`*?{}~")):
                        break
                    try:
                        directory = self.resolve(operand, path=path, cwd=directory, action=action, allow_root=True)
                    except DeliveryError as error:
                        raise DeliveryError("unsafe Git -C working directory: " + clean(error)) from None
                    if directory in self.items and directory not in self.pins:
                        raise DeliveryError("unsafe Git -C working directory: " + clean(directory))
                index += 2
            self.include([(line, word) for word in words if word is not None], path, directory, action,
                         self.bases(path, action, [cwd, directory]))

    def python_call(self, call, node, path, cwd, action, roots, offset, names, parents, nodes):
        if self.works_platform_context(path, cwd, action, offset):
            callsite = (path, node.lineno, call)
            target = self.works_platform_targets.get(callsite)
            if target is not None:
                source, language = target
                self.add(source, language, cwd, action)
                return
            if callsite in WORKS_PLATFORM_GIT_CALLS:
                return
        if call.startswith(UNSUPPORTED_PREFIXES) or call in UNSUPPORTED_CALLS:
            raise DeliveryError("unsupported Python process/import API: " + clean(call))
        if call in {"importlib.import_module", "__import__"}:
            if not node.args or not isinstance(node.args[0], ast.Constant):
                raise DeliveryError("unresolved computed Python import")
            self.import_module(node.args[0].value, path, cwd, action, roots=roots)
        if call in COMMAND_APIS:
            if not node.args:
                raise DeliveryError("unresolved Python script invocation")
            first = node.args[0]
            git_argv = ()
            target_cwd = cwd
            if call.startswith("subprocess."):
                if len(node.args) > 1:
                    raise DeliveryError("unresolved subprocess positional/options expansion")
                git_argv = self.git_subprocess_argv(first, node, call, path, cwd, action, roots, parents, nodes)
                keywords = self.conditional_env_keywords(node.keywords) if git_argv else node.keywords
                if any(keyword.arg is None for keyword in keywords):
                    raise DeliveryError("unresolved subprocess positional/options expansion")
                for keyword in keywords:
                    if keyword.arg not in {"cwd", "executable", "shell", "env"}:
                        continue
                    if keyword.arg == "env":
                        if git_argv and self.works_platform_context(path, cwd, action, offset):
                            # The reviewed materializers preserve the job's executable lookup.
                            continue
                        if self.copied_environment(keyword.value, node, parents, nodes, names,
                                                   protected_process_prefixes=GIT_ENV_PREFIXES if git_argv else ()):
                            continue
                    try:
                        option = ast.literal_eval(keyword.value)
                    except (ValueError, TypeError):
                        try:
                            if keyword.arg != "cwd":
                                raise ValueError("not a source-relative directory")
                            option = "$GITHUB_WORKSPACE/" + self.python_source_path(
                                keyword.value, path, cwd, action, nodes, parents, roots=roots)
                        except (ValueError, TypeError):
                            if git_argv and keyword.arg == "cwd":
                                continue
                            raise DeliveryError("unresolved computed subprocess " + keyword.arg) from None
                    if keyword.arg == "cwd" and option is not None:
                        if not isinstance(option, str):
                            raise DeliveryError("unresolved subprocess cwd")
                        try:
                            target_cwd = self.resolve(option, path=path, cwd=cwd, action=action, allow_root=True)
                        except DeliveryError as error:
                            raise DeliveryError("unsafe subprocess cwd: " + clean(error)) from None
                        for component in (PurePosixPath(target_cwd), *PurePosixPath(target_cwd).parents):
                            if str(component) in self.items and str(component) not in self.pins:
                                raise DeliveryError("unsafe subprocess working directory: " + clean(option))
                        if target_cwd != "." and target_cwd not in self.directories:
                            raise DeliveryError("missing committed subprocess working directory: " + clean(option))
                    elif keyword.arg == "executable" and option is not None:
                        raise DeliveryError("unsupported alternate subprocess executable")
                    elif keyword.arg == "env" and option is not None:
                        if (not isinstance(option, dict) or any(not isinstance(key, str) or not isinstance(value, str)
                                                              for key, value in option.items())
                                or any(key.upper() in RESOLUTION | {"PATH"} or
                                       git_argv and key.upper().startswith(GIT_ENV_PREFIXES)
                                       for key in option)):
                            raise DeliveryError("unsupported subprocess environment affecting resolution")
                    elif keyword.arg == "shell" and option not in (None, False, True):
                        raise DeliveryError("unresolved subprocess shell option")
                if git_argv:
                    if any(keyword.arg == "shell" and not (isinstance(keyword.value, ast.Constant)
                           and keyword.value.value in (None, False)) for keyword in keywords):
                        raise DeliveryError("unsupported shell execution of a Git operation")
                    if any(keyword.arg == "preexec_fn" and not (isinstance(keyword.value, ast.Constant)
                           and keyword.value.value is None) for keyword in keywords):
                        raise DeliveryError("unsupported subprocess pre-execution callback")
                    self.include_git_operands(git_argv, path, target_cwd, action, node.lineno + offset)
                    return
            if (isinstance(first, ast.Name) or isinstance(first, (ast.List, ast.Tuple))
                    and any(isinstance(item, ast.Starred) for item in first.elts)):
                try:
                    if (not call.startswith("subprocess.") or not isinstance(node.func, ast.Attribute)
                            or not isinstance(node.func.value, ast.Name)
                            or not self.proof_import(node.func.value.id, "subprocess", nodes, parents)
                            or self.import_module("subprocess", path, cwd, action, roots=roots)):
                        raise ValueError("untrusted forwarded subprocess namespace")
                    if any(keyword.arg == "shell" and not (isinstance(keyword.value, ast.Constant)
                            and keyword.value.value in (None, False)) for keyword in node.keywords):
                        raise ValueError("unsupported forwarded shell option")
                    variants = self.forwarded_argv(first, node, parents, nodes)
                    for variant in variants:
                        if variant and isinstance(variant[0], ast.Constant) and variant[0].value == "git":
                            raise ValueError("unsupported forwarded Git mode or operands")
                        command = [ast.literal_eval(item) for item in variant]
                        if not command or not all(isinstance(item, str) for item in command):
                            raise ValueError("unresolved forwarded executable or argument")
                        self.commands(path, shlex.join(command), target_cwd, action, offset=node.lineno - 1 + offset)
                    return
                except (ValueError, TypeError, SyntaxError):
                    raise DeliveryError("unresolved computed Python script invocation; unsafe or unresolved forwarding") from None
            if isinstance(first, (ast.List, ast.Tuple)) and not any(isinstance(item, ast.Starred) for item in first.elts):
                fixed = [item.value if isinstance(item, ast.Constant) else None for item in first.elts]
                # The C#/MSBuild graph is outside this source-language perimeter.
                compiler = (fixed[:1] == ["dotnet"] and len(fixed) > 1 and (
                    fixed[1] in DOTNET_BUILD_OPERATIONS
                    or (fixed[1:3] == ["tool", "run"] and len(fixed) > 3 and isinstance(fixed[3], str))))
                docker_data = fixed[:1] == ["docker"] and any(
                    len(fixed) == len(pattern) and all(word is None or actual == word
                                                       for actual, word in zip(fixed, pattern))
                    for pattern in DOCKER_DATA_OPERATIONS)
                if compiler or docker_data:
                    if any(keyword.arg == "shell" and not (
                            isinstance(keyword.value, ast.Constant) and keyword.value.value in (False, None))
                           for keyword in node.keywords):
                        raise DeliveryError("unsupported shell execution of a fixed tool operation")
                    if docker_data:
                        if call in {"subprocess.getoutput", "subprocess.getstatusoutput"}:
                            raise DeliveryError("unsupported shell execution of a fixed tool operation")
                        if (not isinstance(node.func, ast.Attribute) or not isinstance(node.func.value, ast.Name)
                                or not self.proof_import(node.func.value.id, "subprocess", nodes, parents)
                                or self.import_module("subprocess", path, cwd, action, roots=roots)):
                            raise DeliveryError("unproved subprocess API for Docker discovery")
                        if any(posixpath.basename(item).lower() in {"docker", "docker.exe", "docker.cmd", "docker.bat", "docker.com"}
                               for item in self.items):
                            raise DeliveryError("unproved Docker executable: tracked Docker command")
                        if any(keyword.arg == "preexec_fn" and not (
                                isinstance(keyword.value, ast.Constant) and keyword.value.value is None)
                               for keyword in node.keywords):
                            raise DeliveryError("unsupported subprocess pre-execution callback")
                    return
            try:
                if (isinstance(first, (ast.List, ast.Tuple)) and first.elts
                        and "sys.executable" in names(ast.unparse(first.elts[0]))):
                    # sys.executable, or an alias of it, is the Python interpreter.
                    value = ["python", *(ast.literal_eval(element) for element in first.elts[1:])]
                else:
                    value = ast.literal_eval(first)
            except (ValueError, TypeError, SyntaxError):
                # A native immutable pathlib operand can name a tracked script
                # without being a single Python string literal. Preserve its
                # workspace anchor when the subprocess has a different cwd.
                try:
                    def operand(element):
                        try:
                            return ast.literal_eval(element)
                        except (ValueError, TypeError):
                            target = self.python_source_path(element, path, cwd, action, nodes, parents, roots=roots)
                            if not self.regular(target) or self.script_format(target) not in SCRIPTS:
                                raise ValueError("computed operand is not a committed script")
                            return "$GITHUB_WORKSPACE/" + target

                    if isinstance(first, (ast.List, ast.Tuple)):
                        value = []
                        for index, element in enumerate(first.elts):
                            if index == 0 and "sys.executable" in names(ast.unparse(element)):
                                if (not isinstance(element, ast.Attribute) or not isinstance(element.value, ast.Name)
                                        or not self.proof_import(element.value.id, "sys", nodes, parents)):
                                    raise ValueError("untrusted Python interpreter binding")
                                value.append("python")
                            else:
                                value.append(operand(element))
                    elif call == "runpy.run_path":
                        value = operand(first)
                    else:
                        raise ValueError("unsupported computed invocation")
                except (ValueError, TypeError, SyntaxError):
                    raise DeliveryError("unresolved computed Python script invocation") from None
            if call == "runpy.run_module":
                self.import_module(value, path, cwd, action, roots=roots, required=True, execute=True)
            elif call == "runpy.run_path":
                bases = self.bases(path, action, [cwd, *roots])
                for resolved in self.targets(value, path=path, cwd=cwd, action=action, bases=bases):
                    self.language(resolved, "python")
                    self.add(resolved, "python", cwd, action, python_roots=roots)
            elif isinstance(value, str):
                self.commands(path, value, target_cwd, action, offset=node.lineno - 1 + offset)
            elif isinstance(value, (list, tuple)) and all(isinstance(v, str) for v in value):
                self.commands(path, shlex.join(value), target_cwd, action, offset=node.lineno - 1 + offset)
            else:
                raise DeliveryError("unresolved Python subprocess target")

    def owner(self, path):
        """A dormant file's action context is its nearest ancestor holding an action."""
        for parent in PurePosixPath(path).parents:
            directory = str(parent)
            if not (directory + "/").startswith(".github/actions/"):
                break
            if directory + "/action.yml" in self.items or directory + "/action.yaml" in self.items:
                return directory
        return str(PurePosixPath(path).parent)

    def discover(self):
        for root in (".github", ".github/actions"):
            # ls-tree -r returns this exact name only for a blob or gitlink,
            # never a directory. A substituted scope root is not empty scope.
            if root in self.items:
                self.error(root, 1, "unsafe action directory (blob/symlink/gitlink)")
        for path in sorted(self.items):
            if path.startswith(".github/actions/"):
                try:
                    safe_path(path)
                    if not self.regular(path):
                        raise DeliveryError("unsafe action source (symlink/gitlink)")
                    fmt = FORMATS.get(PurePosixPath(path).suffix.lower())
                    if fmt:
                        self.add(path, fmt, action=self.owner(path))
                    elif self.blob(path).split(b"\n", 1)[0].startswith(b"#!"):
                        self.add(path, action=self.owner(path))
                except (ValueError, UnicodeError) as error:
                    self.error(path, 1, str(error))
        while self.queue:
            path, cwd, action, python_roots, sourced = self.queue.popleft()
            try:
                item = self.files[path]
                if PurePosixPath(path).name in {"action.yml", "action.yaml"}:
                    self.action(path, item["text"])
                elif item["format"] == "python":
                    self.python(path, item["text"], cwd, action, roots=python_roots)
                elif item["format"] in {"javascript", "typescript"}:
                    self.javascript(path, item["text"], cwd, action)
                elif item["format"] in {"bash", "powershell"}:
                    self.commands(path, item["text"], cwd, action, powershell=item["format"] == "powershell", sourced=sourced)
            except (ValueError, UnicodeError, RecursionError) as error:
                self.error(path, 1, "discovery failed: " + clean(error))
        return self.files, sorted(set(self.errors))
