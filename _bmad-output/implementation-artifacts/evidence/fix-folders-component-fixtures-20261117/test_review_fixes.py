"""Focused regression probes for the qualification driver and provider JDK selection."""
import contextlib
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location("fixture_qualification", HERE / "qualify.py")
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)


class QualificationReviewTests(unittest.TestCase):
    def test_snapshot_hashes_tested_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, destination = root / "source", root / "destination"
            source.mkdir(); destination.mkdir()
            (source / "file.py").write_text("later source bytes")
            (destination / "file.py").write_text("tested destination bytes")
            def git(repo, *args):
                if args == ("diff", "--binary", "HEAD"): return b"product delta"
                if args == ("diff", "--name-only", "HEAD"): return b"file.py\n"
                if args == ("rev-parse", "HEAD"): return b"source-base" if repo == source else b"destination-base"
                return b""
            with patch.object(qualification, "git", side_effect=git), patch.object(qualification.subprocess, "run"):
                qualification.clone(source, destination, "destination-base", changes=True)
            result = qualification.report["repositories"][source.name]
            self.assertEqual(result["files"]["file.py"], hashlib.sha256((destination / "file.py").read_bytes()).hexdigest())
            self.assertEqual(result["sourcePatchBase"], "source-base")
            self.assertEqual(result["destinationBase"], "destination-base")

    def test_timeout_unwinds_fixture_and_reaps_escaped_child(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pid_file, private_file = root / "pid", root / "private"
            module = ROOT / "references/Hexalith.Platform/infrastructure/keycloak-workload-binding"
            script = (
                "import subprocess,sys,time; from pathlib import Path; from component_fixture import ComponentFixture\n"
                "with ComponentFixture('timeout-probe', lambda *args: '') as fixture:\n"
                f" Path({str(private_file)!r}).write_text(str(fixture.directory))\n"
                " child=subprocess.Popen([sys.executable,'-c','import signal,time; signal.signal(signal.SIGINT,signal.SIG_IGN); time.sleep(60)'],start_new_session=True)\n"
                f" Path({str(pid_file)!r}).write_text(str(child.pid))\n"
                " time.sleep(60)\n"
            )
            control = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
            try:
                started = time.monotonic()
                with patch.object(qualification, "OUT", root), contextlib.redirect_stdout(io.StringIO()):
                    code = qualification.job("timeout-probe", [sys.executable, "-B", "-c", script], root,
                                             env={"PYTHONPATH": str(module)}, timeout=1, shutdown_timeout=0.5)
                self.assertEqual(code, 124)
                self.assertLess(time.monotonic() - started, 5)
                self.assertFalse(Path("/proc", pid_file.read_text()).exists())
                self.assertFalse(Path(private_file.read_text()).exists())
                self.assertIn('"observedRemainingTemporaryPaths": 0', (root / "timeout-probe.log").read_text())
                self.assertIsNone(control.poll())
            finally:
                control.terminate(); control.wait()

    def test_provider_jdk_selection_and_clear_old_compiler_failure(self):
        source = (ROOT / "references/Hexalith.Folders/scripts/prepare-ci-topology-projects.sh").read_text()
        block = source[source.index("# Provisioning consumes only"):]
        for preferred, default, expected in ((21, 17, 0), (None, 22, 0), (None, 17, 1)):
            with self.subTest(preferred=preferred, default=default), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                provider = root / "platform/infrastructure/keycloak-workload-binding"
                provider.mkdir(parents=True)
                (provider / "pom.xml").touch(); (provider / "component_fixture.py").touch()
                for major in set([default] + ([preferred] if preferred else [])):
                    binary = root / str(major) / "bin"
                    binary.mkdir(parents=True)
                    for name, response in (("javac", f"javac {major}.0.1"), ("java", f'openjdk version "{major}.0.1"')):
                        file = binary / name
                        file.write_text("#!/bin/sh\nprintf '%s\\n' '" + response + "' >&2\n")
                        file.chmod(0o755)
                tools = root / "tools"; tools.mkdir()
                mvn = tools / "mvn"
                mvn.write_text('#!/bin/sh\nprintf "%s" "$JAVA_HOME" > "$SELECTED_JDK"\nmkdir -p "$PROVIDER_MODULE/infrastructure/keycloak-workload-binding/target"\ntouch "$PROVIDER_MODULE/infrastructure/keycloak-workload-binding/target/keycloak-workload-binding-1.0.0-SNAPSHOT.jar"\n')
                mvn.chmod(0o755)
                env = dict(os.environ, JAVA_HOME=str(root / str(default)), PATH=str(tools) + ":" + os.environ["PATH"],
                           PROVIDER_MODULE=str(root / "platform"), SELECTED_JDK=str(root / "selected"))
                env.pop("JAVA_HOME_21_X64", None)
                if preferred: env["JAVA_HOME_21_X64"] = str(root / str(preferred))
                script = 'set -euo pipefail\nfail() { echo "$1" >&2; exit 1; }\nmodule_path="$PROVIDER_MODULE"\n' + block
                result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, expected, result.stderr)
                if expected:
                    self.assertIn("Java 21 or newer compiler", result.stderr)
                    self.assertFalse((root / "selected").exists())
                else:
                    self.assertEqual((root / "selected").read_text(), str(root / str(preferred or default)))


if __name__ == "__main__":
    unittest.main()
