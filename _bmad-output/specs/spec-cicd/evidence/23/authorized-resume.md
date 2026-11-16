# Story 23 authorized remote execution

The human answered **yes** to continuing remote story work, starting with the
prepared AD-21 preflight. The historical local-only Build restriction is
superseded for this story. Keep the existing credential boundaries and all
AD-21, product, release and adoption gates.

## Verified reads and source correction

- `maintainer-preflight-authorized-resume.json` retains the first refresh.
  Maintainer profile `/home/administrator/.config/gh`, no inherited token
  overrides, account `jpiquot`, repository ID `1174267565`. The App repository
  list returned HTTP 403 and explicitly requested `read:user`; account admin
  metadata did not establish that scope. No scope or credential was changed.
- The first refresh exposed CodeQL pagination through the numeric repository
  route. The reader now admits only the metadata-verified Tenants analyses
  alias. Fourteen offline tests passed on Python 3.12 and 3.14; the first packet
  remains unchanged. `maintainer-preflight-authorized-paginated.json` completed
  nine CodeQL pages with 875 legacy analyses.
- The attended installation settings initially had six saved selections, then
  concurrent work added more repositories. This session preserved the unsaved
  form and did not click Save. `app-selection-persisted-readback.json` verifies
  Tenants among 19 saved selections after an actual browser reload; all initial
  selections remain. The earlier asynchronous form-coordination question no
  longer needs a response.

## Legacy assessment and execution

`legacy-release-authorized-inventory.json` contains complete lists of 83 tags,
46 published releases and no drafts. Thirty-seven tags lack a GitHub release.
The package version readbacks, historical package/project inspection and
authenticated registry tag inventory preserve 12 of those tags with published
artifacts. `legacy-tag-cleanup-assessment.json` identifies 25 assessed incomplete
legacy tags. `provision-cleanup-tags.json` now records their exact deletion
revisions and confirms that published and unrelated tags are preserved.

Registry reads used the existing intended management context and the existing
Docker credential for the exact registry. Credentials stayed in memory; none
were printed or persisted. Anonymous HTTP 401 and the distroless container's
missing `cat` executable are retained as failed inspection attempts, not proof
that images are absent.

`legacy-registry-key-metadata.json` now records a successful authenticated GET
of key metadata under `jpiquot@itaneo.com`. There are three active unscoped keys:
`JPIQ PC`, `Github Actions Hexalith`, and `GITHUB`. Only public metadata/UUIDs
were retained; no key value was retrieved or printed. The account is a global
registry administrator. The two GitHub-labelled keys' labels do not by
themselves establish their mapping to the encrypted legacy organization secret.
Tenants publishes containers and receives the legacy Zot pair; the pilots'
package-only no-op cannot apply. Establish a concrete Tenants revocation plan
before adoption while preserving the other legacy-selected modules and
maintainer access; do not revoke a global administrator or unrelated key.

`cleanup-legacy-codeql.py` is restricted to the exact legacy CodeQL analysis
key and fresh per-analysis identity/deletability checks. Its first packet
records four acknowledged deletions and a later GET 404 for an analysis that
disappeared. A resumed worker was stopped to reduce repeated inventories;
its packet preserves the acknowledged operations. The next worker records
102 additional deletions, 30 prior acknowledged deletions, and an HTTP 500
(`unexpected end of JSON input`) on a subsequent DELETE. None of those packets
establishes complete cleanup.

`latest-codeql-cleanup.txt` now names
`legacy-codeql-cleanup-verification.json`. Parent inspection audited all 876
acknowledged DELETE receipts against fresh exact-repository, legacy-key, CodeQL
and deletability checks. No other configuration was deleted. The final filtered
and unfiltered API reads returned HTTP 404 with `no analysis found`; those
packets remain classified as not-found-or-inaccessible. Independent fresh
navigation to the exact GitHub security page showed `Code scanning is not
enabled`. The combined receipts and canonical UI evidence establish absence of
the legacy configuration; the API 404 alone did not. Default setup was unchanged.
All cleanup workers have exited; all partial and failed packets remain unchanged.

The deletion procedure follows GitHub's
[documented analysis-set order](https://docs.github.com/en/rest/code-scanning/code-scanning?apiVersion=2026-03-10#delete-a-code-scanning-analysis-from-a-repository).

## Ordered provisioning checkpoint

1. Legacy CodeQL and assessed tag cleanup passed, with the retained independent
   verification and tag-preservation packets.
2. `provision-rulesets.json` and `provision-environment.json` passed. The two
   exact active rulesets and main-only release environment are verified;
   foreign environments are preserved.
3. `provision-registry.json` passed after its environment gate. The one
   Tenants-only identity covers `tenants`, `tenants/**`, `tenants-api`, and
   `tenants-api/**`. Existing ACL and htpasswd rows are preserved, resource-version
   checks and rollout passed, both repository reads return HTTP 200, and foreign
   upload attempts return HTTP 403. The own read/create/update grant is verified
   from the live ACL; no package, image or upload was published as a probe.
4. NuGet sign-in is restored. `nuget-tenants-readback-1.json` records the existing
   Active Tenants policy, ID `18796`, targeting `release.yml` in `production`,
   and all 20 existing policy IDs. It remains untouched. This session entered
   no credentials and selected no Microsoft account. The earlier asynchronous
   sign-in request no longer needs a response. The prepared `nuget-policy-ui.py`
   restricts writes to the exact additive Tenants policy and requires completed
   registry provisioning. `nuget-policy-verification.json` now passes: new Active
   policy `27252`, owner `Hexalith`, repository ID `1174267565`, `release.yml`,
   environment `hexalith-release`, glob `Hexalith.Tenants*`, push of new packages
   and versions only. Guarded submission and a real reload are retained; all
   prior policy IDs and legacy policy `18796` are preserved. Empty readback 7
   was observed during loading and was not treated as policy absence; readback 8
   is complete. The helper now waits for the known retained baseline card.
5. GitHub settings/grants passed in `provision-settings-grants-resumed.json`.
   The initial packet preserves the retention field-name error after creating
   the exact-true publish switch; the resumed phase verifies the actual `days: 90`
   response and adds only the five required organization grants. All previous
   selections and legacy access remain. `verify-ad21.py` qualifies the complete
   current per-repository readbacks in `ad21-verification.json`; its run passed.

## Product preparation

`product-workspace.json` records isolated workspace
`/home/administrator/projects/hexalith/tenants-story-23-product`, branch
`story/23-tenants-product`, from freshly fetched main
`0e0e85fd646da904c5528854e271b71a2b0b9066`. The original module checkout remains
at `292dbf164f26bcf376ef86d749b149b075f8b502`, unchanged, and no nested submodule
was initialized. The current implementation handoff covers product edits and
local qualification there. The parent will inspect the result before a product
write. No registration, delivery or adoption is permitted until the compatible
released contract and concrete legacy publisher cleanup are verified.

The latest acceptable Builds release remains `v6.0.6`, targeting
`fdda17c0a4538b0f7c99f813c20ca24b49006530`. The infrastructure release/pin is
still outstanding; `shared-release-authorized-readback.json` records newer
Builds main `c751d23aa4e73e8f7d74579db26a9fcf1df4c8e5` with queued CI. Use the
central release process; this session has dispatched no release, published no
package/image, changed no Builds pin, and made no Tenants product change.

The post-provision refresh, `shared-release-post-provision-readback.json`, still
finds only `v6.0.6` as the latest published release. Builds main has advanced to
`27e8fba9736a4825d44c40c638c5e6f9b65ab81e`; newer CI is in progress. This is an
external infrastructure-release gate, not permission to qualify unreleased
source as a published contract.

Full story acceptance, matrix qualification and final review remain incomplete.
