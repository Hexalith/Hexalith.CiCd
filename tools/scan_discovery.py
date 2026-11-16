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
from functools import lru_cache
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shlex
import subprocess
import tomllib

import yaml

from delivery_runtime import DeliveryError, clean

FORMATS = {".yml": "yaml", ".yaml": "yaml", ".sh": "bash", ".bash": "bash",
           ".ps1": "powershell", ".psm1": "powershell", ".py": "python"}
SCRIPTS = {"bash", "powershell", "python"}
MAX_FILES = 2000
MAX_BYTES = 32 * 1024 * 1024
MAX_LITERAL = 4096
# Environment variables that change which local Python sources are imported,
# an environment-file selector that can set them, and the PowerShell module and
# shell cd search paths, which redirect name-based module and directory lookup.
RESOLUTION = {"PYTHONPATH", "PYTHONHOME", "PYTHONSAFEPATH", "PYTHONUSERBASE", "UV_ENV_FILE", "PSMODULEPATH",
              "CDPATH"}
ENVIRON = {"os.environ", "os.environb"}
ENVIRON_WRITES = {"setdefault", "update", "__setitem__", "__ior__"}
MODULE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")
# Python modules that run tracked module files by convention: test discovery.
TEST_RUNNERS = {"pytest": "pytest", "py.test": "pytest", "unittest": "unittest", "nose2": "nose2"}
# Commands that execute their operand after this many fixed positional values.
WRAPPERS = {"env": 0, "exec": 0, "command": 0, "builtin": 0, "coproc": 0, "time": 0, "nohup": 0, "nice": 0,
            "sudo": 0, "doas": 0, "setsid": 0, "stdbuf": 0, "ionice": 0, "unbuffer": 0, "xargs": 0,
            "timeout": 1, "flock": 1, "chrt": 1}
# Words that only introduce the next command of a list, condition or block.
KEYWORDS = {"then", "do", "else", "if", "elif", "while", "until", "!", "&", "{", "}", "try", "catch", "finally"}
SHELLS = {"bash": "bash", "sh": "bash", "dash": "bash", "zsh": "bash", "ksh": "bash",
          "pwsh": "powershell", "powershell": "powershell"}
OTHER_LANGUAGES = {".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".rb", ".pl", ".pm", ".php"}
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
    def __init__(self, git, revision):
        self.git, self.revision = git, revision
        self.items = git.items(revision)
        self.directories = set()
        for item in self.items:
            parts = item.split("/")
            self.directories.update("/".join(parts[:index]) for index in range(1, len(parts)))
        self.files, self.errors, self.queue, self.visited = {}, [], deque(), set()
        self.headers, self.recipes = {}, {}
        self.total = 0

    def error(self, path, line, message):
        self.errors.append(f"{clean(path)}:{line}: {clean(message)}")

    def regular(self, path):
        item = self.items.get(path)
        return item is not None and item[:2] in (("100644", "blob"), ("100755", "blob"))

    def header(self, path):
        if path not in self.headers:
            self.headers[path] = shebang(self.git.blob(self.revision, path).split(b"\n", 1)[0])
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
        if fmt not in {"yaml", "bash", "powershell", "python"}:
            raise DeliveryError("unsupported local-script language: " + clean(path))
        if path not in self.files:
            if len(self.files) >= MAX_FILES:
                raise DeliveryError("module selected-file limit exceeded")
            raw = self.git.blob(self.revision, path)
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
                if not traversed:
                    raise DeliveryError("source path escapes module")
                traversed.pop()
            else:
                traversed.append(component)
                prefix = "/".join(traversed)
                if index < len(components) - 1 and prefix in self.items:
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
        matches = [] if anchored else self.candidates(expanded, bases)
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

    @staticmethod
    def bases(path, action, cwds):
        return list(dict.fromkeys([".", str(PurePosixPath(path).parent), *([action] if action else []), *cwds]))

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
                        data = tomllib.loads(self.git.blob(self.revision, candidate).decode("utf-8"))
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
                project = tomllib.loads(self.git.blob(self.revision, candidate).decode("utf-8"))
            except (ValueError, UnicodeError):
                raise DeliveryError("unreadable task runner recipe: " + clean(candidate)) from None
            if "build-system" in project or self.recipe(("setup.py", "setup.cfg"), bases):
                raise DeliveryError("unsupported local project preparation with tracked build backend: " + name)

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
        literals, cwds = [(1, item) for key, item in value.items() if key != "runs" for item in scalars(item)], ["."]
        # Each step is discovered independently and anchored at its own line.
        for step in value["runs"]["steps"]:
            line = getattr(step, "line", 1)
            try:
                if not isinstance(step, dict):
                    raise DeliveryError("invalid action step")
                literals += [(line, item) for item in scalars(step, ("run", "shell"))]
                if "uses" in step:
                    target = step["uses"]
                    if not isinstance(target, str):
                        raise DeliveryError("invalid action target")
                    if target.startswith("./"):
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
                    if "env" in step:
                        if not isinstance(step["env"], dict):
                            raise DeliveryError("unsupported computed step environment affecting script resolution")
                        for key, setting in step["env"].items():
                            if str(key).upper() in RESOLUTION:
                                raise DeliveryError("unsupported step environment affecting script resolution")
                            if str(key).upper() == "PATH":
                                check_path(str(setting),
                                           message="unsupported step PATH environment affecting script resolution")
                    cwd = "."
                    if "working-directory" in step:
                        cwd = self.resolve(step["working-directory"], path=path, cwd=".", action=parent, allow_root=True)
                        cwds.append(cwd)
                    run = step.locations.get("run", line)
                    interpreter = shell.split()[0]
                    if interpreter in {"python", "python3"}:
                        self.python(path, command, cwd, parent, roots=(cwd,), offset=run - 1)
                    elif interpreter in {"bash", "sh", "pwsh", "powershell"}:
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

    def logical(self, text, offset, powershell, path):
        """Yield (first physical line number, logical line, data lines).

        Lines split only on LF with a trailing CR dropped. The continuation
        character is a backslash in shell and a backtick in PowerShell, and a
        logical line keeps its first physical line number. Heredoc and
        PowerShell here-string bodies are data lines, never commands.
        """
        physical = [line.removesuffix("\r") for line in text.split("\n")]
        continuation = "`" if powershell else "\\"
        index = 0
        while index < len(physical):
            number, line, data = index + 1 + offset, physical[index], []
            index += 1
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
                            break
                        data.append((body_number, body, expands))
            yield number, line, data

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
        cwds, literals, modules = [cwd], [], []
        for number, line, data in self.logical(text, offset, powershell, path):
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
            if prefix in self.items:
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

        literals, modules, bases, cwds = [], [], [cwd, *roots], [cwd]
        for node in nodes:
            for sequence in sequences(node):
                modules.extend((getattr(node, "lineno", 1) + offset, module)
                               for module in self.references(sequence, path, getattr(node, "lineno", 1) + offset))
            try:
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    literals.append((getattr(node, "lineno", 1) + offset, node.value))
                    if node.value in {"GITHUB_ENV", "GITHUB_PATH"}:
                        raise DeliveryError("unsupported Python access to " + node.value + "; coverage unsupported")
                elif isinstance(node, (ast.Name, ast.Attribute)) and isinstance(node.ctx, ast.Load):
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
                    if any(candidate.rsplit(".", 1)[-1] in mutators and search_path(candidate.rsplit(".", 1)[0])
                           for candidate in calls) or "site.addsitedir" in calls:
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
                        self.python_call(call, node, path, cwd, action, roots, offset, names)
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

    def python_call(self, call, node, path, cwd, action, roots, offset, names):
        if call.startswith(UNSUPPORTED_PREFIXES) or call in UNSUPPORTED_CALLS:
            raise DeliveryError("unsupported Python process/import API: " + clean(call))
        if call in {"importlib.import_module", "__import__"}:
            if not node.args or not isinstance(node.args[0], ast.Constant):
                raise DeliveryError("unresolved computed Python import")
            self.import_module(node.args[0].value, path, cwd, action, roots=roots)
        if call in COMMAND_APIS:
            target_cwd = cwd
            if call.startswith("subprocess."):
                if len(node.args) > 1 or any(keyword.arg is None for keyword in node.keywords):
                    raise DeliveryError("unresolved subprocess positional/options expansion")
                for keyword in node.keywords:
                    if keyword.arg not in {"cwd", "executable", "shell", "env"}:
                        continue
                    try:
                        option = ast.literal_eval(keyword.value)
                    except (ValueError, TypeError):
                        raise DeliveryError("unresolved computed subprocess " + keyword.arg) from None
                    if keyword.arg == "cwd" and option is not None:
                        if not isinstance(option, str):
                            raise DeliveryError("unresolved subprocess cwd")
                        try:
                            target_cwd = self.resolve(option, path=path, cwd=cwd, action=action, allow_root=True)
                        except DeliveryError as error:
                            raise DeliveryError("unsafe subprocess cwd: " + clean(error)) from None
                        for component in (PurePosixPath(target_cwd), *PurePosixPath(target_cwd).parents):
                            if str(component) in self.items:
                                raise DeliveryError("unsafe subprocess working directory: " + clean(option))
                        if target_cwd != "." and target_cwd not in self.directories:
                            raise DeliveryError("missing committed subprocess working directory: " + clean(option))
                    elif keyword.arg == "executable" and option is not None:
                        raise DeliveryError("unsupported alternate subprocess executable")
                    elif keyword.arg == "env" and option is not None:
                        if (not isinstance(option, dict) or any(not isinstance(key, str) or not isinstance(value, str)
                                                              for key, value in option.items())
                                or any(key.upper() in RESOLUTION | {"PATH"} for key in option)):
                            raise DeliveryError("unsupported subprocess environment affecting resolution")
                    elif keyword.arg == "shell" and option not in (None, False, True):
                        raise DeliveryError("unresolved subprocess shell option")
            if not node.args:
                raise DeliveryError("unresolved Python script invocation")
            first = node.args[0]
            try:
                if (isinstance(first, (ast.List, ast.Tuple)) and first.elts
                        and "sys.executable" in names(ast.unparse(first.elts[0]))):
                    # sys.executable, or an alias of it, is the Python interpreter.
                    value = ["python", *(ast.literal_eval(element) for element in first.elts[1:])]
                else:
                    value = ast.literal_eval(first)
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
                    elif self.git.blob(self.revision, path).split(b"\n", 1)[0].startswith(b"#!"):
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
                elif item["format"] in {"bash", "powershell"}:
                    self.commands(path, item["text"], cwd, action, powershell=item["format"] == "powershell", sourced=sourced)
            except (ValueError, UnicodeError, RecursionError) as error:
                self.error(path, 1, "discovery failed: " + clean(error))
        return self.files, sorted(set(self.errors))
