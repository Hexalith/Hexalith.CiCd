#!/usr/bin/env python3
"""Qualify the evidence entry point with real commits and shallow transport."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "check_evidence.py"
EVIDENCE = "_bmad-" + "output/"


def git(repository, *arguments, **options):
    return subprocess.run(
        ["git", "-C", str(repository), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         *map(str, arguments)],
        capture_output=True, check=options.pop("check", True), **options,
    )


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.source = self.root / "source"
        self.source.mkdir()
        git(self.source, "init", "--quiet", "--initial-branch=main")
        (self.source / "tools").mkdir()
        shutil.copyfile(CHECKER, self.source / "tools/check_evidence.py")
        self.write(EVIDENCE + "unchanged.log", b"old log")
        self.write(EVIDENCE + "deleted.patch", b"old patch")
        self.write(EVIDENCE + "unchanged-oversized.md", b"x" * 262145)
        self.write(EVIDENCE + "mode.md", b"mode change")
        self.write(EVIDENCE + "modified.md", b"ordinary small file")
        self.write("outside.log", b"raw outside the policy")
        self.baseline = self.commit()

    def write(self, path, content):
        destination = self.source / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    def commit(self):
        git(self.source, "add", "--all")
        git(self.source, "commit", "--quiet", "-m", "Fixture")
        return self.rev(self.source, "HEAD")

    @staticmethod
    def rev(repository, ref):
        return git(repository, "rev-parse", ref).stdout.decode().strip()

    def checkout(self):
        remote = self.root / "remote.git"
        clone = self.root / "candidate"
        git(self.root, "clone", "--quiet", "--bare", self.source, remote)
        git(remote, "config", "uploadpack.allowFilter", "true")
        git(remote, "config", "uploadpack.allowAnySHA1InWant", "true")
        clone.mkdir()
        git(clone, "init", "--quiet")
        git(clone, "remote", "add", "origin", remote.as_uri())
        git(clone, "fetch", "--quiet", "--no-tags", "--depth=1", "--filter=blob:none",
            "origin", "+refs/heads/main:refs/remotes/origin/main")
        git(clone, "sparse-checkout", "set", "--no-cone", "/tools/check_evidence.py")
        git(clone, "checkout", "--quiet", "--detach", "origin/main")
        self.assertFalse((clone / EVIDENCE).exists())
        self.assertEqual("true", self.rev(clone, "--is-shallow-repository"))
        return clone

    def run_check(self, repository, event="push", **variables):
        env = os.environ | {"GITHUB_EVENT_NAME": event, "GITHUB_SHA": self.rev(repository, "HEAD"),
                            "EVIDENCE_PR_BASE": self.baseline, "EVIDENCE_PUSH_BEFORE": self.baseline} | variables
        return subprocess.run([sys.executable, "-I", str(repository / "tools/check_evidence.py")],
                              env=env, capture_output=True, text=True)

    def test_compact_receipt_and_exact_limit_pass_without_loading_unchanged_blobs(self):
        self.write(EVIDENCE + "receipt.md", b"result: passed\n")
        self.write(EVIDENCE + "limit.md", b"a" * 262144)
        (self.source / (EVIDENCE + "deleted.patch")).unlink()
        self.write("outside.log", b"changed outside the evidence root")
        candidate = self.commit()
        clone = self.checkout()
        excluded = self.rev(self.source, candidate + ":" + EVIDENCE + "unchanged-oversized.md")
        changed = self.rev(self.source, candidate + ":" + EVIDENCE + "limit.md")
        # Local-only probes must leave the baseline and blobs absent before the check.
        probe_env = os.environ | {"GIT_NO_LAZY_FETCH": "1"}
        fetch_head = clone / ".git/FETCH_HEAD"
        previous_fetch_head = fetch_head.read_bytes() if fetch_head.exists() else None
        for oid in (self.baseline, excluded, changed):
            self.assertNotEqual(0, git(clone, "cat-file", "-e", oid, check=False, env=probe_env).returncode)
        (clone / EVIDENCE).mkdir()
        (clone / (EVIDENCE + "untracked.sh")).write_text("ignored worktree file")
        result = self.run_check(clone, event="pull_request", EVIDENCE_PUSH_BEFORE="ignored")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(f"{self.baseline}..{candidate}", result.stdout)
        self.assertEqual(0, git(clone, "cat-file", "-e", self.baseline, env=probe_env).returncode)
        self.assertNotEqual(0, git(clone, "cat-file", "-e", excluded, check=False, env=probe_env).returncode)
        self.assertNotIn(self.baseline, git(clone, "for-each-ref", "--format=%(objectname)").stdout.decode())
        self.assertEqual(previous_fetch_head, fetch_head.read_bytes() if fetch_head.exists() else None)

    def test_push_previous_sha_covers_intermediate_commits_and_renames_into_scope(self):
        git(self.source, "mv", "outside.log", EVIDENCE + "renamed.log")
        intermediate = self.commit()
        self.write(EVIDENCE + "receipt.md", b"result: passed\n")
        self.commit()
        clone = self.checkout()
        result = self.run_check(clone, EVIDENCE_PR_BASE="ignored")
        self.assertEqual(1, result.returncode)
        self.assertIn(f"{EVIDENCE}renamed.log': raw output or executable file extension", result.stderr)
        self.assertNotIn("unchanged.log", result.stderr)
        self.assertNotEqual(0, git(clone, "cat-file", "-e", intermediate, check=False,
                                   env=os.environ | {"GIT_NO_LAZY_FETCH": "1"}).returncode)

    def test_all_blocked_suffixes_and_existing_file_modification(self):
        suffixes = ("log", "jsonl", "patch", "diff", "nupkg", "snupkg", "trx", "binlog", "zip",
                    "gz", "tar", "py", "js", "mjs", "ps1", "sh", "LOG")
        for suffix in suffixes:
            self.write(EVIDENCE + f"new.{suffix}", b"raw")
        self.write(EVIDENCE + "unchanged.log", b"modified old raw output")
        self.commit()
        result = self.run_check(self.checkout())
        self.assertEqual(1, result.returncode)
        for suffix in suffixes:
            with self.subTest(suffix=suffix):
                self.assertIn(f"{EVIDENCE}new.{suffix}': raw output or executable file extension", result.stderr)
        self.assertIn(f"{EVIDENCE}unchanged.log': raw output or executable file extension", result.stderr)

    def test_rejects_large_blob_and_reports_each_path_for_duplicate_blobs(self):
        self.write(EVIDENCE + "000-receipt.md", b"small receipt\n")
        for path in ("modified.md", "added.md"):
            self.write(EVIDENCE + path, b"a" * 262145)
        candidate = self.commit()
        clone = self.checkout()
        git(clone, "config", "protocol.version", "2")
        packet_trace = self.root / "packets"
        result = self.run_check(clone, GIT_TRACE_PACKET=str(packet_trace))
        self.assertEqual(1, result.returncode)
        for path in ("modified.md", "added.md"):
            self.assertIn(f"{EVIDENCE}{path}': 262145 bytes exceeds the 262144 byte limit", result.stderr)
        small = self.rev(self.source, candidate + ":" + EVIDENCE + "000-receipt.md")
        large = self.rev(self.source, candidate + ":" + EVIDENCE + "added.md")
        packets = packet_trace.read_text().splitlines()
        wants = [line.partition("fetch> want ")[2] for line in packets if "fetch> want " in line]
        self.assertEqual(2, sum(line.endswith("fetch> command=fetch") for line in packets))
        self.assertCountEqual([self.baseline, small, large], wants)

    def test_rejects_mode_only_change_symlink_type_change_and_gitlink(self):
        (self.source / (EVIDENCE + "mode.md")).chmod(0o755)
        (self.source / (EVIDENCE + "modified.md")).unlink()
        (self.source / (EVIDENCE + "modified.md")).symlink_to("../outside.log")
        git(self.source, "add", "--all")
        git(self.source, "update-index", "--add", "--cacheinfo", "160000," + self.baseline + "," + EVIDENCE + "gitlink")
        git(self.source, "commit", "--quiet", "-m", "Non-regular entries")
        result = self.run_check(self.checkout())
        self.assertEqual(1, result.returncode)
        self.assertIn(f"{EVIDENCE}mode.md': executable Git mode 100755", result.stderr)
        self.assertIn(f"{EVIDENCE}modified.md': non-regular Git mode 120000", result.stderr)
        self.assertIn(f"{EVIDENCE}gitlink': non-regular Git mode 160000", result.stderr)

    def test_new_ref_compares_to_the_empty_tree(self):
        clone = self.checkout()
        result = self.run_check(clone, EVIDENCE_PUSH_BEFORE="0" * 40)
        self.assertEqual(1, result.returncode)
        self.assertIn(f"{EVIDENCE}unchanged.log': raw output or executable file extension", result.stderr)
        self.assertIn(f"{EVIDENCE}deleted.patch': raw output or executable file extension", result.stderr)

    def test_missing_malformed_and_unreadable_baselines_fail_closed(self):
        clone = self.checkout()
        for baseline in ("", "HEAD^", "0" * 40, "f" * 40):
            with self.subTest(baseline=baseline):
                result = self.run_check(clone, event="pull_request", EVIDENCE_PR_BASE=baseline)
                self.assertEqual(1, result.returncode)
                self.assertIn("baseline", result.stderr)
        result = self.run_check(clone, GITHUB_SHA="f" * 40)
        self.assertEqual(1, result.returncode)
        self.assertIn("HEAD does not match the exact event SHA", result.stderr)

    def test_unusual_paths_are_reported_without_emitting_runner_commands(self):
        self.write(EVIDENCE + "line\n::warning::diagnostic.log", b"raw")
        self.commit()
        result = self.run_check(self.checkout())
        self.assertEqual(1, result.returncode)
        self.assertIn(rf"{EVIDENCE}line\n::warning::diagnostic.log", result.stderr)
        self.assertEqual(1, len(result.stderr.splitlines()))


if __name__ == "__main__":
    unittest.main()
