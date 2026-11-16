#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Behavioral qualification of explicit catalog acquisition using real Git objects."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/actions/prepare-g6-catalog/prepare.py"
spec = importlib.util.spec_from_file_location("g6_catalog", SCRIPT)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def command(root, *args, check=True):
    environment = os.environ.copy()
    for key in tuple(environment):
        if key.startswith("GIT_"):
            environment.pop(key)
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                       GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
    return subprocess.run(["git", "-C", str(root), *map(str, args)], env=environment,
                          capture_output=True, check=check)


def initialize(path):
    path.mkdir(parents=True)
    command(path, "init", "--quiet")
    command(path, "config", "core.hooksPath", os.devnull)
    command(path, "config", "commit.gpgsign", "false")


def commit(path):
    command(path, "add", "--all", "--", ".", ":(exclude)references")
    command(path, "commit", "--quiet", "-m", "test: fixture")
    return command(path, "rev-parse", "HEAD").stdout.decode().strip()


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.scratch.cleanup)
        self.base = Path(self.scratch.name)
        self.origin = self.base / "origin"
        initialize(self.origin)
        props = self.origin / catalog.CATALOG
        props.parent.mkdir()
        self.bytes = b'<Project>\r\n  <PropertyGroup />\r\n</Project>\r\n'
        props.write_bytes(self.bytes)
        self.pin = commit(self.origin)
        (self.origin / "later").write_text("fixture\n")
        self.builds_head = commit(self.origin)
        self.root = self.base / "workspace"
        initialize(self.root)
        self.builds = self.root / catalog.BUILDS
        self.builds.parent.mkdir()
        command(self.base, "clone", "--quiet", "--depth=1", self.origin.as_uri(), self.builds)
        command(self.builds, "remote", "set-url", "origin", catalog.ORIGIN)
        self.platform = self.root / catalog.PLATFORM
        initialize(self.platform)
        (self.platform / "hexalith-platform.json").write_text('{"fixture":true}\n')
        command(self.platform, "update-index", "--add", "--cacheinfo", "160000", self.pin, catalog.BUILDS)
        self.reviewed = commit(self.platform)
        (self.root / ".gitmodules").write_text(
            '[submodule "Builds"]\npath = ' + catalog.BUILDS + '\nurl = ' + catalog.ORIGIN +
            '\n[submodule "Platform"]\npath = ' + catalog.PLATFORM +
            '\nurl = https://github.com/Hexalith/Hexalith.Platform.git\n')
        command(self.root, "update-index", "--add", "--cacheinfo", "160000", self.builds_head, catalog.BUILDS)
        command(self.root, "update-index", "--add", "--cacheinfo", "160000", self.reviewed, catalog.PLATFORM)
        commit(self.root)
        self.real_git = catalog.git
        self.fetches = []

    def local_git(self, root, *args, **kwargs):
        # Only the transport is substituted. Acquisition uses a real depth-one
        # fetch and named origin (including its configured refspecs). The URL
        # rewrite exists only for the actual fetch subprocess, after approval.
        if args and args[0] == "fetch":
            self.fetches.append(args)
            real_popen = catalog.subprocess.Popen

            def transport(arguments, **options):
                translated = [arguments[0], "-c", "url." + self.origin.as_uri() + ".insteadOf=" + catalog.ORIGIN,
                              *arguments[1:]]
                return real_popen(translated, **options)

            with mock.patch.object(catalog.subprocess, "Popen", side_effect=transport):
                return self.real_git(root, *args, **kwargs)
        return self.real_git(root, *args, **kwargs)

    def prepare(self):
        with mock.patch.object(catalog, "git", side_effect=self.local_git):
            return catalog.prepare(self.root, self.reviewed)

    def test_missing_catalog_then_exact_acquisition_and_idempotence(self):
        self.assertEqual(command(self.builds, "rev-parse", "--is-shallow-repository").stdout, b"true\n")
        self.assertNotEqual(command(self.builds, "show", self.pin + ":" + catalog.CATALOG, check=False).returncode, 0)
        before = {str(path): catalog.snapshot(path) for path in (self.root, self.builds, self.platform)}
        refs = command(self.builds, "show-ref").stdout
        result = self.prepare()
        self.assertTrue(result["acquired"])
        self.assertEqual(result["catalog_commit"], self.pin)
        self.assertEqual(command(self.builds, "show", self.pin + ":" + catalog.CATALOG).stdout, self.bytes)
        self.assertEqual(result["catalog_sha256"], catalog.hashlib.sha256(self.bytes).hexdigest())
        self.assertEqual(before, {str(path): catalog.snapshot(path) for path in (self.root, self.builds, self.platform)})
        self.assertEqual(command(self.builds, "show-ref").stdout, refs)
        self.assertEqual(self.fetches, [("fetch", "--no-recurse-submodules", "--no-tags", "--depth=1",
                                        "--no-write-fetch-head", "--refmap=", "--no-auto-maintenance", "origin", self.pin)])
        self.assertFalse(self.prepare()["acquired"])
        self.assertEqual(len(self.fetches), 1)
        self.assertFalse((self.platform / catalog.BUILDS / ".git").exists())

    def test_unapproved_declared_origin_fails_without_fetching(self):
        text = (self.root / ".gitmodules").read_text().replace(catalog.ORIGIN, "https://example.invalid/Builds.git")
        (self.root / ".gitmodules").write_text(text)
        commit(self.root)
        with self.assertRaisesRegex(catalog.PreparationError, "Root Builds origin"):
            self.prepare()
        self.assertEqual(self.fetches, [])

    def test_unapproved_effective_origin_and_multiple_urls_fail_without_fetching(self):
        for key, value in (("remote.origin.url", "https://example.invalid/Builds.git"),
                           ("url.https://example.invalid/.insteadOf", "https://github.com/")):
            with self.subTest(key=key):
                command(self.builds, "config", key, value)
                with self.assertRaisesRegex(catalog.PreparationError, "origin is not approved"):
                    self.prepare()
                command(self.builds, "config", "--unset-all", key)
                command(self.builds, "config", "remote.origin.url", catalog.ORIGIN)
        command(self.builds, "config", "--add", "remote.origin.url", catalog.ORIGIN)
        with self.assertRaises(catalog.PreparationError):
            self.prepare()
        self.assertEqual(self.fetches, [])

    def test_remote_helper_override_fails_before_acquisition(self):
        command(self.builds, "config", "remote.origin.vcs", "unapproved-fixture-helper")
        with self.assertRaisesRegex(catalog.PreparationError, "standard Git HTTPS transport"):
            self.prepare()
        self.assertEqual(self.fetches, [])

    def test_inherited_alternate_store_does_not_substitute_for_acquisition(self):
        with mock.patch.dict(os.environ, {"GIT_ALTERNATE_OBJECT_DIRECTORIES": str(self.origin / ".git/objects")}):
            self.assertTrue(self.prepare()["acquired"])
        self.assertEqual(command(self.builds, "show", self.pin + ":" + catalog.CATALOG).stdout, self.bytes)

    def test_symlinked_reference_parent_fails_before_acquisition(self):
        (self.root / "references").rename(self.base / "borrowed")
        (self.root / "references").symlink_to(self.base / "borrowed", target_is_directory=True)
        with self.assertRaisesRegex(catalog.PreparationError, "must not traverse a symlink"):
            self.prepare()
        self.assertEqual(self.fetches, [])

    def test_configured_fetch_refmap_does_not_create_or_update_refs(self):
        command(self.builds, "config", "remote.origin.fetch", "+" + self.pin + ":refs/heads/unwanted")
        before = command(self.builds, "show-ref").stdout
        self.assertTrue(self.prepare()["acquired"])
        self.assertEqual(command(self.builds, "show-ref").stdout, before)

    def test_named_remote_refmap_fixture_detects_unsafe_fetch(self):
        command(self.builds, "config", "remote.origin.fetch", "+" + self.pin + ":refs/heads/unwanted")

        def unsafe(root, *args, **kwargs):
            return self.local_git(root, *(value for value in args if value != "--refmap="), **kwargs)

        with mock.patch.object(catalog, "git", side_effect=unsafe):
            with self.assertRaisesRegex(catalog.PreparationError, "refs or gitlinks changed"):
                catalog.prepare(self.root, self.reviewed)
        self.assertEqual(command(self.builds, "rev-parse", "refs/heads/unwanted").stdout.decode().strip(), self.pin)

    def test_corrupt_existing_catalog_commit_fails_without_fetching(self):
        loose = self.builds / ".git/objects" / self.pin[:2] / self.pin[2:]
        loose.parent.mkdir(exist_ok=True)
        loose.write_bytes(b"corrupt-object-fixture\n")
        with self.assertRaises(catalog.PreparationError):
            self.prepare()
        self.assertEqual(self.fetches, [])

    def test_index_flag_mutation_is_detected(self):
        def mutate(root, *args, **kwargs):
            result = self.local_git(root, *args, **kwargs)
            if args[0] == "fetch":
                command(self.builds, "update-index", "--assume-unchanged", "later")
            return result
        with mock.patch.object(catalog, "git", side_effect=mutate):
            with self.assertRaisesRegex(catalog.PreparationError, "index, refs or gitlinks changed"):
                catalog.prepare(self.root, self.reviewed)

    def test_wrong_reviewed_revision_and_changed_gitlinks_fail_before_fetching(self):
        for value in ("main", "-" + "a" * 40, "a" * 39, "a" * 40):
            with self.subTest(value=value), self.assertRaises(catalog.PreparationError):
                catalog.prepare(self.root, value)
        command(self.root, "update-index", "--cacheinfo", "160000", "a" * 40, catalog.BUILDS)
        with self.assertRaisesRegex(catalog.PreparationError, "Staged direct gitlinks"):
            self.prepare()
        self.assertEqual(self.fetches, [])

    def test_modified_declarations_and_uninitialized_direct_checkout_fail(self):
        (self.root / ".gitmodules").write_text("unreviewed\n")
        with self.assertRaisesRegex(catalog.PreparationError, "declarations differ"):
            self.prepare()
        (self.platform / ".git").rename(self.base / "platform-git")
        with self.assertRaisesRegex(catalog.PreparationError, "direct checkout"):
            self.prepare()
        self.assertEqual(self.fetches, [])

    def test_missing_catalog_file_and_wrong_object_type_fail_closed(self):
        for pin in (self.reviewed, command(self.origin, "rev-parse", "HEAD:later").stdout.decode().strip()):
            with self.subTest(pin=pin):
                command(self.platform, "update-index", "--cacheinfo", "160000", pin, catalog.BUILDS)
                self.reviewed = commit(self.platform)
                command(self.root, "update-index", "--cacheinfo", "160000", self.reviewed, catalog.PLATFORM)
                commit(self.root)
                # Ensure the wrong object is already present: it must not trigger a fetch.
                source = self.platform if pin == catalog.head(self.platform) else self.origin
                # The initial Platform revision remains reachable in its repository.
                if command(self.platform, "cat-file", "-e", pin, check=False).returncode == 0:
                    source = self.platform
                command(self.builds, "fetch", "--quiet", "--no-tags", source, pin)
                with self.assertRaises(catalog.PreparationError):
                    self.prepare()
        self.assertEqual(self.fetches, [])

    def test_fetch_failure_preserves_source(self):
        before = catalog.snapshot(self.builds)
        with mock.patch.object(catalog, "git", side_effect=lambda root, *args, **kwargs:
                               (_ for _ in ()).throw(catalog.PreparationError("G6CAT001", "Git preparation command failed"))
                               if args[0] == "fetch" else self.real_git(root, *args, **kwargs)):
            with self.assertRaisesRegex(catalog.PreparationError, "Git preparation command failed"):
                catalog.prepare(self.root, self.reviewed)
        self.assertEqual(before, catalog.snapshot(self.builds))

    def test_failed_git_process_stderr_is_not_echoed_by_cli(self):
        binaries = self.base / "bin"
        binaries.mkdir()
        fake = binaries / "git"
        fake.write_text(f"#!{sys.executable}\nimport sys\nsys.stderr.write('private-stderr-sentinel')\nraise SystemExit(42)\n")
        fake.chmod(0o755)
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--workspace", str(self.root),
                                 "--platform-revision", self.reviewed], capture_output=True,
                                env=dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"]))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["rule"], "G6CAT001")
        self.assertNotIn(b"private-stderr-sentinel", result.stdout + result.stderr)

    def test_timed_out_git_children_are_stopped_before_returning(self):
        binaries = self.base / "bin"
        binaries.mkdir()
        started, late = self.base / "started", self.base / "late"
        child = f"from pathlib import Path; import time; Path({str(started)!r}).touch(); time.sleep(0.5); Path({str(late)!r}).touch()"
        fake = binaries / "git"
        fake.write_text(f"#!{sys.executable}\nimport subprocess, sys, time\nsubprocess.Popen([sys.executable, '-c', {child!r}])\ntime.sleep(30)\n")
        fake.chmod(0o755)
        with mock.patch.dict(os.environ, {"PATH": str(binaries) + os.pathsep + os.environ["PATH"]}), \
                mock.patch.object(catalog, "GIT_TIMEOUT_SECONDS", 0.3):
            with self.assertRaisesRegex(catalog.PreparationError, "timed out"):
                catalog.git(self.root, "fixture")
        self.assertTrue(started.exists())
        time.sleep(0.7)
        self.assertFalse(late.exists())

    def test_cli_failure_is_bounded_json(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--workspace", str(self.root),
                                 "--platform-revision", "private-control\nvalue"], capture_output=True)
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(data["rule"], "G6CAT002")
        self.assertNotIn(b"private-control", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
