# Pilot provisioning checkpoint — 2026-11-16

Provisioning is partly complete. Neither pilot is adopted. The first story
execution checkbox remains open because scoped NuGet policies and the later
org grants are not complete. No module product push or shared release has
occurred, and no pre-adoption verification exception has been assumed.

| AD-21 step | Current result | Evidence |
| --- | --- | --- |
| App repository selection | Saved, then verified after an actual browser reload: exactly Builds, CiCd, Commons and PolymorphicSerializations under **Only select repositories**. Existing selections retained. | `app-selection-{before,save,after}.json`, `app-selection-readback.{py,json}` |
| Incomplete legacy release state | No drafts; deleted only Commons `v2.30.2` and Poly `v1.19.0`/`v1.19.4`, after rechecking the exact refs and absence of published releases. Published releases/packages and module main refs are unchanged. | `provisioning-before.json`, `stale-tag-assessment.json`, `provision-cleanup*.{json,log}` |
| Stale CodeQL configuration | Removed the legacy `.github/workflows/codeql.yml:analyze` configuration's 218 analyses. Poly's SonarCloud analyses are preserved. Subsequent CodeQL inventories are empty. | `provision-cleanup-initial.json` (60 deletions), `provision-cleanup.json` (158 deletions), `provisioning-after.json` |
| Exact rulesets | Commons IDs `27356310`/`27356311`; Poly IDs `27356312`/`27356313`. Active `refs/heads/main` deletion/non-fast-forward and `refs/tags/v*` update/deletion rules, with no bypass actors or extra conditions. | `provision-rulesets.{json,log}`, `provisioning-after.json` |
| Main-only release environments | Both `hexalith-release` environments have exactly one branch policy, `main`, without required reviewers or wait timers. Both own registry-secret pairs are installed. | `provision-environments.{json,log}`, `provision-registry.json`, `provisioning-after.json` |
| Own Zot identities | Distinct `hexalith-commons-publish` and `hexalith-polymorphicserializations-publish`, scoped respectively to `commons`/`commons/**` and `polymorphicserializations`/`polymorphicserializations/**`, with read/create/update and no administrator/delete grant. | `provision-registry.{py,json,log}` |
| Scoped NuGet policy beside each legacy policy | **Incomplete.** The first Commons submission showed a generic creation error; no new card appeared. Refresh redirected to NuGet Sign In. Ordinary Microsoft sign-in reached the human face/fingerprint/PIN/security-key boundary for `jpiquot@itaneo.com`. No credentials entered. | `nuget-commons-{proposed,submit,readback}.json`, `nuget-session-expired.json`, `nuget-signin-result.json` |
| Later settings and org grants | Deferred until both NuGet policies exist, preserving AD-21 order. Read-only checks record the existing disabled default setup/security updates, 90-day retention, kill switches and org grant selection. | `provisioning-after.json` |

The CodeQL operation used GitHub's documented newest-to-oldest analysis
deletion, restricted to the previously assessed legacy CodeQL configuration.
It did not disable a workflow or change a product scan gate.
[GitHub's deletion documentation](https://docs.github.com/en/rest/code-scanning/code-scanning?apiVersion=2026-03-10#delete-a-code-scanning-analysis-from-a-repository)
describes that administrative operation. The first bounded cleanup stopped
after 30 sets; its complete results and error are retained. The resumed cleanup
used a larger finite set bound and the same exact configuration restrictions.

Zot credentials were generated in memory and sent through stdin to GitHub and
Kubernetes; no credential value or hash was printed or saved locally. Existing
htpasswd rows remain byte-identical and pre-existing configuration/grants are
unchanged. One registry rollout completed, with availability restored. Both
new credentials authenticate with HTTP 200 and receive HTTP 403 when attempting
upload creation in the other pilot's or an unrelated namespace. Own namespace
grants are confirmed by the preserved live ACL and restarted workload; no
package, image or upload was created as a qualification fixture.

The prepared Commons policy has owner `Hexalith`, workflow `release.yml`,
environment `hexalith-release`, package glob `Hexalith.Commons*`, and only push
of packages/versions. These fields follow the
[NuGet policy setup](https://learn.microsoft.com/en-us/nuget/nuget-org/trusted-publishing).
No successful policy creation is claimed. The generic creation error followed
by an expired session does not establish a duplicate-name, definition or
permission constraint, nor prove the internal cause of the original error.
After human authentication, refresh the policy inventory before retrying so a
successful concurrent creation cannot be duplicated. Preserve all legacy
policies until actual adoption.

The existing main workflows can produce new legacy CodeQL analyses while
product preparation is pending. Recheck stale configuration state before
adoption; do not disable or weaken those scans to keep an inventory empty.

The independent mandatory pre-push gap remains as documented in
`pre-adoption-check-resolution.md`. Human authentication does not select or
approve that proposed verification path. No nested submodule, owned-file
bootstrap, alternative credential or direct module-owned change was used.
