"""Ready-publication cases imported by the locked nightly controller suite."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import delivery_runtime
import nightly_runtime as runtime
import nightly_publish as publisher
from nightly_support import Opener, RELEASE as BUILDS_SOURCE, TAG as BUILDS_TAG


def git(root, *arguments, data=None):
    result = subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                             "-c", "core.hooksPath=/dev/null", "-C", str(root), *map(str, arguments)],
                            input=data, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr.decode(errors="replace"))
    return result.stdout


def tagged_helpers(destination):
    """Read immutable tagged objects, never execute the submodule checkout."""
    source = ROOT / "references/Hexalith.Builds"
    paths = git(source, "ls-tree", "-r", "--name-only", BUILDS_TAG, "--", "Github/lib", "schemas").decode().splitlines()
    for path in paths:
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git(source, "show", BUILDS_TAG + ":" + path))
    helpers = runtime.load_helpers(destination)
    helpers.source = git(source, "rev-parse", BUILDS_TAG + "^{commit}").decode().strip()
    if helpers.source != BUILDS_SOURCE:
        raise AssertionError("publication fixture tag does not match its immutable commit")
    return helpers


class PublicationFixture:
    repository = "Hexalith.Alpha"
    workflow = ".github/workflows/release.yml"
    token = "inert-nightly-publication-token"

    def __init__(self, root, helpers):
        self.root, self.helpers = root, helpers
        self.source = root / "module-source"
        self.source.mkdir(parents=True)
        git(self.source, "init", "--quiet", "--initial-branch=main")
        git(self.source, "config", "uploadpack.allowFilter", "true")
        (self.source / "product.txt").write_text("first release\n")
        git(self.source, "add", ".")
        git(self.source, "commit", "--quiet", "-m", "Initial")
        self.base = git(self.source, "rev-parse", "HEAD").decode().strip()
        git(self.source, "tag", "v1.0.0")
        (self.source / "product.txt").write_text("ready release\n")
        workflow = self.source / self.workflow
        workflow.parent.mkdir(parents=True)
        workflow.write_text("old workflow\n")
        (self.source / ".gitattributes").write_text("* filter=poison\n")
        (self.source / "setup.py").write_text("raise RuntimeError('module code must never execute')\n")
        git(self.source, "add", ".")
        git(self.source, "commit", "--quiet", "-m", "Release")
        self.sha = git(self.source, "rev-parse", "HEAD").decode().strip()
        workflow.write_text("changed workflow on newer main\n")
        git(self.source, "add", ".")
        git(self.source, "commit", "--quiet", "-m", "Bump")
        self.head = git(self.source, "rev-parse", "HEAD").decode().strip()
        self.live = {"id": 88, "author": {"login": "github-actions[bot]"}, "draft": True,
                     "prerelease": False, "tag_name": "v1.1.0", "target_commitish": self.sha}
        self.producer = {"id": 10, "path": self.workflow, "event": "workflow_dispatch", "head_branch": "main",
                         "head_sha": self.sha, "repository": {"full_name": "Hexalith/" + self.repository}}
        self.metadata = {"id": 20, "name": "release", "expired": False,
                         "expires_at": "2100-01-01T00:00:00Z", "workflow_run": {"id": 10, "head_sha": self.sha}}
        self.set_original_inventory()
        self.run = {"repository": self.repository, "workflow": self.workflow, "deliveredSha": "b" * 40,
                    "dispatchHead": self.head, "runId": 99, "runAttempt": 1,
                    "link": "https://github.com/Hexalith/" + self.repository + "/actions/runs/99",
                    "eligibility": "eligible", "dispatch": "dispatched", "status": "completed", "conclusion": "success",
                    "outcome": {"schema": "hexalith.release-outcome.v1", "sha": self.sha, "version": "1.1.0",
                                "outcome": "ready", "draftId": 88, "lastTag": "v1.0.0"},
                    "outcomeError": "", "publication": "pending", "verdict": "pending", "reason": ""}
        self.current = {"id": 99, "path": self.workflow, "event": "workflow_dispatch", "head_branch": "main",
                        "head_sha": self.head, "repository": {"full_name": "Hexalith/" + self.repository},
                        "html_url": self.run["link"], "run_attempt": 1, "status": "completed", "conclusion": "success"}
        self.current_change_on_repeat = None
        self.current_gets = 0
        self.tags = []
        self.requests, self.writes = [], []
        self.extra_draft = None
        self.change_body = False
        self.gets = 0
        self.patch_error = None
        self.patch_response = None
        self.wrong_tag = False
        self.api = self
        self.budget = runtime.Budget(1000, 3300, token_epoch=1000, clock=lambda: 1001)
        delivery_runtime._SECRETS.append(self.token)

    def set_original_inventory(self, packages=(), *, image=None):
        publication = self.helpers.publish.publication
        repository = "Hexalith/" + self.repository
        manifest = {"sha": self.sha, "version": "1.1.0", "packages": [], "containers": []}
        archive, records = io.BytesIO(), []
        with zipfile.ZipFile(archive, "w") as output:
            for package_id in sorted(packages):
                path = "packages/" + package_id + ".nupkg"
                package = io.BytesIO()
                with zipfile.ZipFile(package, "w") as nupkg:
                    nupkg.writestr(package_id + ".nuspec", f"<package><metadata><id>{package_id}</id>"
                        f"<version>1.1.0</version><repository commit='{self.sha}'/></metadata></package>")
                data = package.getvalue()
                output.writestr(path, data)
                manifest["packages"].append({"id": package_id, "path": path})
                records.append(publication.record(package_id, data, publication.payload_map(data)))
            if image is not None:
                path = "containers/image.tar"
                output.writestr(path, image)
                manifest["containers"].append({"name": "product/image", "path": path})
            output.writestr("release-manifest.json", json.dumps(manifest))
        self.build_archive = archive.getvalue()
        self.digest = "sha256:" + hashlib.sha256(self.build_archive).hexdigest()
        self.metadata.update(digest=self.digest, size_in_bytes=len(self.build_archive))
        inventory = self.helpers.draft.artifact_inventory(self.build_archive, sha=self.sha,
            version="1.1.0", digest=self.digest, repository=repository)
        self.live["body"] = self.helpers.draft.release_body("Release notes", sha=self.sha, run_id=10,
            artifact_id=20, digest=self.digest, inventory=inventory)
        self.set_publication(publication.serialize({"schema": publication.SCHEMA, "repository": repository,
            "sha": self.sha, "version": "1.1.0", "artifactRun": 10, "artifactId": 20,
            "artifactDigest": self.digest, "packages": records}))

    def set_publication(self, data):
        self.publication = data
        self.assets = [{"id": 90, "name": self.helpers.publish.publication.ASSET_NAME, "state": "uploaded",
                        "size": len(data), "digest": "sha256:" + hashlib.sha256(data).hexdigest()}]

    def remote(self, repository):
        if repository != self.repository:
            raise AssertionError("foreign repository requested")
        return self.source.as_uri()

    def configure(self, objects, repository):
        self.remote(repository)
        # The only test-only protocol change substitutes the local Git server.
        for index in range(int(objects.env["GIT_CONFIG_COUNT"])):
            if objects.env["GIT_CONFIG_KEY_" + str(index)] == "protocol.file.allow":
                objects.env["GIT_CONFIG_VALUE_" + str(index)] = "always"

    def get(self, path, token=None, *, deadline=None):
        if token != self.token:
            raise AssertionError("wrong publication token")
        self.requests.append(path)
        prefix = "/repos/Hexalith/" + self.repository
        if path == prefix + "/releases/88":
            self.gets += 1
            value = deepcopy(self.live)
            if self.change_body and self.gets > 1:
                value["body"] += "\nchanged notes"
            return value
        if path == prefix + "/actions/runs/10":
            return deepcopy(self.producer)
        if path == prefix + "/actions/runs/99":
            self.current_gets += 1
            value = deepcopy(self.current)
            if self.current_change_on_repeat and self.current_gets > 1:
                value.update(self.current_change_on_repeat)
            return value
        if path == prefix + "/actions/artifacts/20":
            return deepcopy(self.metadata)
        if path == prefix + "/git/matching-refs/tags/v1.1.0":
            return deepcopy(self.tags)
        raise AssertionError("unexpected authenticated GET: " + path)

    def pages(self, path, token=None, *, field=None, deadline=None):
        if token != self.token:
            raise AssertionError("unexpected publication listing")
        self.requests.append(path)
        if path == "/repos/Hexalith/" + self.repository + "/releases/88/assets":
            return deepcopy(self.assets)
        if path != "/repos/Hexalith/" + self.repository + "/releases":
            raise AssertionError("unexpected publication listing")
        return [deepcopy(self.live), *([deepcopy(self.extra_draft)] if self.extra_draft else [])]

    def publication_bytes(self, repository, identity, token):
        if (repository, identity, token) != (self.repository, 90, self.token):
            raise AssertionError("wrong package publication identity")
        self.requests.append("releases/assets/90")
        return self.publication

    def artifact_bytes(self, repository, metadata, token):
        if (repository, metadata, token) != (self.repository, self.metadata, self.token):
            raise AssertionError("wrong original build artifact")
        self.requests.append("actions/artifacts/20/zip")
        return self.build_archive

    def release_manifest(self, repository, metadata, token, scratch):
        if (repository, metadata, token) != (self.repository, self.metadata, self.token):
            raise AssertionError("wrong original build artifact")
        self.requests.append("actions/artifacts/20/release-manifest")
        api = runtime.API(self.budget, repositories=(self.repository,), opener=Opener([self.build_archive]))
        return api.release_manifest(repository, metadata, token, scratch)

    def publish_draft(self, repository, identity, document, token):
        if repository != self.repository or identity != 88 or token != self.token:
            raise AssertionError("unexpected publication identity")
        self.writes.append(deepcopy(document))
        if document != {"tag_name": "v1.1.0", "target_commitish": self.sha, "draft": False}:
            raise AssertionError("publication changed extra release fields")
        self.live["draft"] = False
        self.live["immutable"] = True
        self.tags = [{"ref": "refs/tags/v1.1.0", "object": {
            "type": "commit", "sha": self.base if self.wrong_tag else self.sha}}]
        if self.patch_error:
            raise RuntimeError(self.patch_error)
        return deepcopy(self.patch_response or self.live)

    def publish(self):
        return publisher.publish_target(self.run, self.helpers, self, self.root / "scratch", self.budget, self.token)


class BuildsPublicationFixture(PublicationFixture):
    repository = "Hexalith.Builds"
    workflow = ".github/workflows/builds-release.yml"


class TestNightlyPublication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper_temp = tempfile.TemporaryDirectory()
        cls.helpers = tagged_helpers(Path(cls.helper_temp.name))

    @classmethod
    def tearDownClass(cls):
        cls.helper_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = PublicationFixture(Path(self.temp.name), self.helpers)

    def test_complete_mode_publishes_exact_draft_without_tree_comparison(self):
        fixture = self.fixture
        self.assertNotEqual(fixture.run["dispatchHead"], fixture.run["outcome"]["sha"])
        self.assertTrue(fixture.publish(), fixture.run)
        self.assertEqual(fixture.run["publication"], "published")
        self.assertEqual(len(fixture.writes), 1)
        self.assertIn("actions/artifacts/20/zip", fixture.requests)
        self.assertIn("releases/assets/90", fixture.requests)
        self.assertFalse((fixture.root / "scratch").joinpath("product.txt").exists())

    def test_builds_packages_are_finalized_from_the_correlated_run_asset(self):
        fixture = BuildsPublicationFixture(Path(self.temp.name) / "builds", self.helpers)
        fixture.set_original_inventory(("Fixture.Two", "Fixture.One"))
        with patch.object(self.helpers.publish, "verify_packages", side_effect=AssertionError("unexpected feed read")):
            self.assertTrue(fixture.publish(), fixture.run)
        self.assertEqual(fixture.run["publication"], "published")
        self.assertEqual(len(fixture.writes), 1)
        self.assertIn("/repos/Hexalith/Hexalith.Builds/actions/artifacts/20", fixture.requests)
        self.assertIn("actions/artifacts/20/release-manifest", fixture.requests)
        self.assertIn("releases/assets/90", fixture.requests)
        self.assertNotIn("actions/artifacts/20/zip", fixture.requests)

    def test_container_only_draft_uses_the_existing_empty_publication_asset(self):
        fixture = self.fixture
        fixture_path = self.helpers.root / "Github/lib/tests/test_release_oci.py"
        spec = importlib.util.spec_from_file_location("_nightly_oci_fixture", fixture_path)
        oci_fixture = importlib.util.module_from_spec(spec)
        with patch.object(sys, "path", sys.path.copy()):
            spec.loader.exec_module(oci_fixture)
        sources = []
        repository = "Hexalith/" + fixture.repository
        with patch.object(oci_fixture, "SHA", fixture.sha), patch.object(oci_fixture, "REPOSITORY", repository):
            for architecture in ("amd64", "arm64"):
                source = fixture.root / (architecture + ".tar")
                oci_fixture.sdk_archive(source, architecture, version="1.1.0")
                sources.append((source, {"os": "linux", "architecture": architecture}))
        image = fixture.root / "image.tar"
        oci_fixture.oci.combine_archives(sources, image, revision=fixture.sha, version="1.1.0",
                                         repository=repository, name="product/image")
        fixture.set_original_inventory(image=image.read_bytes())
        self.assertTrue(fixture.publish(), fixture.run)
        self.assertEqual(len(fixture.writes), 1)
        self.assertIn("actions/artifacts/20/release-manifest", fixture.requests)
        self.assertIn("releases/assets/90", fixture.requests)
        self.assertNotIn("actions/artifacts/20/zip", fixture.requests)

    def test_nonempty_publication_refuses_missing_or_conflicting_evidence_before_patch(self):
        contract = self.helpers.publish.publication
        identity = "package publication asset differs from the original artifact identity or inventory"
        cases = {"missing": "expected exactly one existing package publication asset",
                 "duplicate": "expected exactly one existing package publication asset",
                 "state": "package publication asset metadata is invalid",
                 "malformed": "invalid package publication fields/schema",
                 "canonical": "package publication asset is not in canonical v1 form",
                 "body": "draft changed during publication", "artifact": "artifact ID/name/run/digest/source identity mismatch",
                 "attempt": "correlated completion run changed", "files": "invalid package publication payload map",
                 "repository": identity, "sha": identity, "version": identity, "artifactRun": identity,
                 "artifactId": identity, "artifactDigest": identity, "packages": identity}
        for change, expected in cases.items():
            with self.subTest(change=change), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                fixture = PublicationFixture(Path(directory), self.helpers)
                fixture.set_original_inventory(("Fixture.Package",))
                document = contract.read(fixture.publication)
                if change == "missing":
                    fixture.assets.clear()
                elif change == "duplicate":
                    fixture.assets.append(fixture.assets[0] | {"id": 91})
                elif change == "state":
                    fixture.assets[0]["state"] = "new"
                elif change == "malformed":
                    fixture.set_publication(b"{}")
                elif change == "canonical":
                    fixture.set_publication(json.dumps(document).encode())
                elif change == "body":
                    fixture.change_body = True
                elif change == "artifact":
                    fixture.metadata["digest"] = "sha256:" + "c" * 64
                elif change == "attempt":
                    fixture.current_change_on_repeat = {"run_attempt": 2}
                elif change == "files":
                    document["packages"][0]["files"] = {"../unsafe": "d" * 64}
                    fixture.set_publication((json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode())
                else:
                    values = {"repository": "Hexalith/Other", "sha": "f" * 40, "version": "1.2.0",
                              "artifactRun": 11, "artifactId": 21, "artifactDigest": "sha256:" + "c" * 64,
                              "packages": [document["packages"][0] | {"id": "fixture.Package"}]}
                    fixture.set_publication(contract.serialize(document | {change: values[change]}))
                self.assertFalse(fixture.publish(), fixture.run)
                self.assertEqual(fixture.writes, [])
                self.assertIn(expected, fixture.run["reason"])

    def test_draft_and_publication_asset_cannot_agree_on_a_different_inventory(self):
        fixture = self.fixture
        fixture.set_original_inventory(("Fixture.Package",))
        fixture.live["body"] = fixture.live["body"].replace("Fixture.Package", "Fixture.Other")
        contract = self.helpers.publish.publication
        document = contract.read(fixture.publication)
        document["packages"][0]["id"] = "Fixture.Other"
        fixture.set_publication(contract.serialize(document))
        self.assertFalse(fixture.publish(), fixture.run)
        self.assertIn("original artifact inventory differs from draft release trailers", fixture.run["reason"])
        self.assertEqual(fixture.writes, [])

    def test_original_manifest_source_version_and_container_inventory_are_checked(self):
        cases = ({"sha": "c" * 40}, {"version": "1.2.0"}, {"containers": [{"name": "product/other"}]})
        for changed in cases:
            with self.subTest(changed=changed), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                fixture = PublicationFixture(Path(directory), self.helpers)
                fixture.set_original_inventory(("Fixture.Package",))
                manifest = {"sha": fixture.sha, "version": "1.1.0", "packages": [{"id": "Fixture.Package"}],
                            "containers": []} | changed
                with patch.object(fixture, "release_manifest", return_value=manifest):
                    self.assertFalse(fixture.publish(), fixture.run)
                self.assertIn("inventory differs" if "containers" in changed else "manifest source or version mismatch",
                              fixture.run["reason"])
                self.assertEqual(fixture.writes, [])

    def test_github_only_publication_requires_the_original_empty_asset(self):
        for change in ("missing", "duplicate", "metadata", "bytes", "build-archive"):
            with self.subTest(change=change), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                fixture = PublicationFixture(Path(directory), self.helpers)
                if change == "missing":
                    fixture.assets.clear()
                elif change == "duplicate":
                    fixture.assets.append(fixture.assets[0] | {"id": 91})
                elif change == "metadata":
                    fixture.assets[0]["digest"] = "sha256:" + "b" * 64
                elif change == "bytes":
                    fixture.publication = self.helpers.publish.publication.serialize(
                        self.helpers.publish.publication.read(fixture.publication) | {"artifactRun": 11})
                elif change == "build-archive":
                    fixture.build_archive = b"wrong bytes"
                self.assertFalse(fixture.publish(), fixture.run)
                self.assertEqual(fixture.writes, [])

    def test_authenticated_nonempty_build_cannot_use_an_empty_draft_inventory(self):
        fixture = self.fixture
        body, old_digest = fixture.live["body"], fixture.digest
        fixture.set_original_inventory(("Fixture.Package",))
        fixture.live["body"] = body.replace(old_digest, fixture.digest)
        self.assertFalse(fixture.publish(), fixture.run)
        self.assertIn("original artifact inventory differs", fixture.run["reason"])
        self.assertEqual(fixture.writes, [])

    def test_completion_rerun_during_package_publication_read_prevents_patch(self):
        fixture = self.fixture
        read = fixture.publication_bytes

        def rerun(*args):
            data = read(*args)
            fixture.current.update(run_attempt=2, status="in_progress", conclusion=None)
            return data

        fixture.publication_bytes = rerun
        self.assertFalse(fixture.publish(), fixture.run)
        self.assertIn("correlated completion run changed", fixture.run["reason"])
        self.assertEqual(fixture.writes, [])

    def test_replaced_asset_after_finalizer_read_prevents_patch(self):
        fixture = self.fixture
        fixture.set_original_inventory(("Fixture.Package",))
        read = fixture.publication_bytes

        def replace(*args):
            data = read(*args)
            if fixture.requests.count("releases/assets/90") == 2:
                fixture.assets[0]["id"] = 91
            return data

        fixture.publication_bytes = replace
        self.assertFalse(fixture.publish(), fixture.run)
        self.assertIn("asset changed before publication", fixture.run["reason"])
        self.assertEqual(fixture.writes, [])

    def test_late_draft_or_tag_change_prevents_patch(self):
        for change in ("draft", "tag"):
            with self.subTest(change=change), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                fixture = PublicationFixture(Path(directory), self.helpers)
                fixture.set_original_inventory(("Fixture.Package",))
                read = fixture.publication_bytes

                def replace(*args):
                    data = read(*args)
                    if fixture.requests.count("releases/assets/90") == 2:
                        if change == "draft":
                            fixture.live["body"] += "\nchanged notes"
                        else:
                            fixture.tags = [{"ref": "refs/tags/v1.1.0", "object": {"type": "commit", "sha": fixture.base}}]
                    return data

                fixture.publication_bytes = replace
                self.assertFalse(fixture.publish(), fixture.run)
                self.assertIn("draft changed during publication" if change == "draft" else "does not point at the built commit",
                              fixture.run["reason"])
                self.assertEqual(fixture.writes, [])

    def test_asset_replaced_during_final_completion_lookup_prevents_patch(self):
        fixture = self.fixture
        fixture.set_original_inventory(("Fixture.Package",))
        get = fixture.get

        def replace(path, *args, **kwargs):
            data = get(path, *args, **kwargs)
            if path.endswith("/actions/runs/99") and fixture.current_gets == 2:
                fixture.assets[0]["id"] = 91
            return data

        fixture.get = replace
        self.assertFalse(fixture.publish(), fixture.run)
        self.assertIn("asset changed before publication", fixture.run["reason"])
        self.assertEqual(fixture.writes, [])

    def test_replaced_asset_after_patch_prevents_a_verified_publication(self):
        for field, value in (("id", 91), ("size", 1), ("digest", "sha256:" + "1" * 64)):
            with self.subTest(field=field), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                fixture = PublicationFixture(Path(directory), self.helpers)
                fixture.set_original_inventory(("Fixture.Package",))
                publish = fixture.publish_draft

                def replace(*args):
                    release = publish(*args)
                    fixture.assets[0][field] = value
                    return release

                fixture.publish_draft = replace
                self.assertFalse(fixture.publish(), fixture.run)
                self.assertIn("does not retain the verified package publication asset", fixture.run["reason"])
                self.assertEqual(len(fixture.writes), 1)
                self.assertFalse(fixture.publish(), fixture.run)
                self.assertEqual(len(fixture.writes), 1)

    def test_source_must_be_an_ancestor_of_dispatched_head(self):
        fixture = self.fixture
        fixture.current["head_sha"] = fixture.run["dispatchHead"] = fixture.base
        self.assertFalse(fixture.publish(), fixture.run)
        self.assertIn("ancestor of the dispatch head", fixture.run["reason"])
        self.assertEqual(fixture.writes, [])

    def test_helper_pagination_preserves_its_deadline(self):
        fixture = self.fixture
        calls = []
        class Pages:
            def pages(self, path, token, *, deadline=None):
                calls.append((path, token, deadline))
                return []
        api = publisher._ReleaseApi(Pages(), fixture.repository, fixture.token, fixture.budget, fixture.run)
        self.assertEqual(api.pages("/repos/Hexalith/" + fixture.repository + "/releases?per_page=100", deadline=1030), [])
        self.assertEqual(calls, [("/repos/Hexalith/" + fixture.repository + "/releases", fixture.token, 1030)])

    def test_unverified_existing_publication_does_not_pass(self):
        self.fixture.live["draft"] = False
        self.assertFalse(self.fixture.publish())
        self.assertEqual(self.fixture.writes, [])
        self.assertEqual(self.fixture.run["publication"], "failed")

    def test_verified_record_can_resume_without_a_second_write(self):
        self.assertTrue(self.fixture.publish())
        self.assertTrue(self.fixture.publish())
        self.assertEqual(len(self.fixture.writes), 1)

    def test_original_producer_identity_failures_precede_publication(self):
        cases = (("path", ".github/workflows/ci.yml"), ("event", "push"),
                 ("head_branch", "other"), ("head_sha", "c" * 40),
                 ("id", 11), ("repository", {"full_name": "Hexalith/Other"}))
        for key, value in cases:
            with self.subTest(field=key), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                fixture = PublicationFixture(Path(directory), self.helpers)
                fixture.producer[key] = value
                self.assertFalse(fixture.publish())
                self.assertEqual(fixture.writes, [])

    def test_stale_completion_rerun_before_or_during_publication_cannot_publish(self):
        cases = ({"run_attempt": 2, "status": "in_progress", "conclusion": None},
                 {"run_attempt": 2, "status": "completed", "conclusion": "success"},
                 {"status": "completed", "conclusion": "failure"}, {"head_sha": "c" * 40},
                 {"path": ".github/workflows/ci.yml"})
        for timing in ("before", "during"):
            for changed in cases:
                with self.subTest(timing=timing, changed=changed), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                    fixture = PublicationFixture(Path(directory), self.helpers)
                    if timing == "before":
                        fixture.current.update(changed)
                    else:
                        fixture.current_change_on_repeat = changed
                    self.assertFalse(fixture.publish())
                    self.assertEqual(fixture.writes, [])

    def test_original_artifact_metadata_failures_precede_publication(self):
        cases = (("digest", "sha256:" + "b" * 64), ("name", "other"), ("expired", True),
                 ("expires_at", "2000-01-01T00:00:00Z"), ("id", 21),
                 ("workflow_run", {"id": 11, "head_sha": self.fixture.sha}))
        for key, value in cases:
            with self.subTest(field=key), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                fixture = PublicationFixture(Path(directory), self.helpers)
                fixture.metadata[key] = value
                self.assertFalse(fixture.publish())
                self.assertEqual(fixture.writes, [])

    def test_bad_marking_unique_draft_changed_body_and_conflicting_tag_are_rejected(self):
        for kind in ("duplicate", "body", "trailer", "tag", "base", "author"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                fixture = PublicationFixture(Path(directory), self.helpers)
                if kind == "duplicate":
                    fixture.extra_draft = deepcopy(fixture.live) | {"id": 89}
                elif kind == "body":
                    fixture.change_body = True
                elif kind == "trailer":
                    fixture.live["body"] += "\nhexalith-release-run: 100\n"
                elif kind == "tag":
                    fixture.tags = [{"ref": "refs/tags/v1.1.0", "object": {"type": "commit", "sha": fixture.base}}]
                elif kind == "base":
                    fixture.run["outcome"]["lastTag"] = "v9.0.0"
                else:
                    fixture.live["author"]["login"] = "human"
                self.assertFalse(fixture.publish())
                self.assertEqual(fixture.writes, [])

    def test_returned_release_and_postpublication_tag_are_independent_checks(self):
        for kind in ("response", "immutable", "tag"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(dir=self.temp.name) as directory:
                fixture = PublicationFixture(Path(directory), self.helpers)
                if kind == "response":
                    fixture.patch_response = deepcopy(fixture.live) | {
                        "draft": False, "immutable": True, "target_commitish": fixture.base}
                elif kind == "immutable":
                    fixture.patch_response = deepcopy(fixture.live) | {"draft": False, "immutable": False}
                else:
                    fixture.wrong_tag = True
                self.assertFalse(fixture.publish())
                self.assertEqual(len(fixture.writes), 1)
                self.assertEqual(fixture.run["publication"], "failed")

    def test_uncertain_patch_is_not_retried_or_accepted_from_preexisting_publication(self):
        fixture = self.fixture
        fixture.patch_error = "transport lost " + fixture.token
        self.assertFalse(fixture.publish())
        self.assertEqual(len(fixture.writes), 1)
        self.assertNotIn(fixture.token, fixture.run["reason"])
        fixture.patch_error = None
        self.assertFalse(fixture.publish())
        self.assertEqual(len(fixture.writes), 1)

    def test_mixed_verdicts_keep_all_links_and_write_summary_before_failure(self):
        original = self.fixture.run
        rows = []
        for index, outcome in enumerate(("published", "nothing", "disabled", "ready", "failed"), 1):
            row = deepcopy(original)
            row["repository"] = "Hexalith.Target" + str(index)
            row["runId"] = index
            row["link"] = "https://github.com/Hexalith/" + row["repository"] + "/actions/runs/" + str(index)
            row["outcome"]["outcome"] = outcome
            if outcome == "ready":
                row["publication"] = "published"
            rows.append(row)
        rows.extend((deepcopy(original) | {"conclusion": "cancelled"},
                     deepcopy(original) | {"status": "in_progress", "conclusion": ""},
                     deepcopy(original) | {"outcome": None, "outcomeError": "missing artifact"},
                     deepcopy(original) | {"eligibility": "failed", "dispatch": "failed", "reason": "mint failed"},
                     deepcopy(original) | {"eligibility": "not-adopted", "dispatch": "skipped", "runId": 0, "link": ""}))
        state = {"targets": rows, "errors": [], "phase": "wait", "result": "pending"}
        summary = Path(self.temp.name) / "summary.md"
        self.assertTrue(publisher.reduce_report(state, summary))
        self.assertEqual([row["verdict"] for row in rows], ["pass"] * 4 + ["fail"] * 5 + ["skip"])
        self.assertEqual(state["result"], "fail")
        text = summary.read_text()
        for index in range(1, 6):
            self.assertIn("[run " + str(index) + "]", text)
        self.assertEqual(text.count("| Hexalith."), len(rows))

    def test_nonsuccess_conclusions_override_every_otherwise_passing_outcome(self):
        original = self.fixture.run
        for outcome in ("published", "nothing", "disabled", "ready"):
            row = deepcopy(original)
            if outcome != "ready":
                row["outcome"] = self.helpers.outcome.outcome_document(self.fixture.sha, outcome, "1.1.0")
            row["publication"] = "published" if outcome == "ready" else "pending"
            control = {"targets": [deepcopy(row)], "errors": [], "phase": "wait", "result": "pending"}
            self.assertFalse(publisher.reduce_report(control), outcome)
            self.assertEqual(control["targets"][0]["verdict"], "pass")
            for conclusion in ("failure", "neutral", "cancelled", "skipped", "timed_out", "action_required",
                               "stale", "startup_failure", ""):
                with self.subTest(outcome=outcome, conclusion=conclusion):
                    failed = deepcopy(row)
                    failed["conclusion"] = conclusion
                    state = {"targets": [failed], "errors": [], "phase": "wait", "result": "pending"}
                    self.assertTrue(publisher.reduce_report(state))
                    self.assertEqual(failed["verdict"], "fail")
                    self.assertEqual(state["result"], "fail")
                    self.assertIn("concluded", failed["reason"])

    def test_missing_state_and_orchestration_errors_cannot_be_green(self):
        state = {"targets": [], "errors": [], "phase": "wait"}
        self.assertTrue(publisher.reduce_report(state))
        self.assertEqual(state["result"], "fail")
        state = {"targets": [deepcopy(self.fixture.run) | {"publication": "published"}],
                 "errors": ["wait state download failed"], "phase": "wait"}
        self.assertTrue(publisher.reduce_report(state))
        self.assertEqual(state["targets"][0]["verdict"], "pass")

    def test_malformed_handoff_outcome_is_revalidated_before_reduction(self):
        spec = importlib.util.spec_from_file_location("_publication_handoff_controller", ROOT / "tools/nightly.py")
        controller = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(controller)
        project = Path(self.temp.name) / "cicd"
        project.mkdir()
        git(project, "init", "--quiet", "--initial-branch=main")
        (project / "setup").mkdir()
        (project / "setup/Hexalith.Alpha.yml").write_text("{}\n")
        (project / "builds-version").write_text(BUILDS_TAG + "\n")
        git(project, "add", ".")
        git(project, "commit", "--quiet", "-m", "Fixture")
        expected = {"runId": 100, "attempt": 2, "source": git(project, "rev-parse", "HEAD").decode().strip()}
        handoff = controller.initial(expected, ["Hexalith.Alpha"])
        handoff.update(phase="wait", wait={"started": 1000, "deadline": 19000})
        handoff["builds"] = {"tag": BUILDS_TAG, "sha": self.helpers.source}
        for index, row in enumerate(handoff["targets"]):
            row.update(eligibility="eligible", dispatch="dispatched", status="completed", conclusion="success",
                       runId=90 + index, runAttempt=1, dispatchHead=self.fixture.head,
                       link="https://github.com/Hexalith/" + row["repository"] + "/actions/runs/" + str(90 + index),
                       outcome={"schema": "hexalith.release-outcome.v1", "sha": self.fixture.sha,
                                "outcome": "published"})
        handoff["targets"][0]["outcome"] = {"outcome": "published", "hostile": True}
        class HandoffApi:
            def get(self, path, token):
                return {"id": 123, "name": "hexalith-nightly-wait-2", "expired": False,
                        "workflow_run": {"id": 100}}

            def artifact_member(self, repository, metadata, member, token):
                return deepcopy(handoff)
        class HandoffTransport:
            api = HandoffApi()

            def helpers(_self, tag, directory, *, token):
                self.assertEqual(token, "inert")
                return self.helpers
        directory = Path(self.temp.name) / "handoff"
        controller.initialize("publish-ready", directory, project, expected, {"NIGHTLY_ARTIFACT_ID": "123"},
                              HandoffTransport(), {"HANDOFF_TOKEN": "inert"}, lambda: 1001)
        state = runtime.json_read((directory / "nightly.json").read_bytes())
        self.assertIsNone(state["targets"][0]["outcome"])
        self.assertTrue(state["targets"][0]["outcomeError"])
        self.assertTrue(publisher.reduce_report(state))
        self.assertEqual([row["verdict"] for row in state["targets"]], ["fail", "pass"])
