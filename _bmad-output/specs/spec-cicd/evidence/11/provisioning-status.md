# Pilot provisioning checkpoint — 2026-11-16

Provisioning is complete. Neither pilot is adopted. The first story execution
checkbox is complete. Shared publication is now complete as `v6.0.6`;
preparation main publication and actual pilot acceptance remain open. The human subsequently approved the narrow
pre-adoption verification path recorded in the frozen story; its exact-input
checks must pass before any product-preparation push.

| AD-21 step | Current result | Evidence |
| --- | --- | --- |
| App repository selection | Saved, then verified after an actual browser reload: exactly Builds, CiCd, Commons and PolymorphicSerializations under **Only select repositories**. Existing selections retained. | `app-selection-{before,save,after}.json`, `app-selection-readback.{py,json}` |
| Incomplete legacy release state | No drafts; deleted only Commons `v2.30.2` and Poly `v1.19.0`/`v1.19.4`, after rechecking the exact refs and absence of published releases. Published releases/packages and module main refs are unchanged. | `provisioning-before.json`, `stale-tag-assessment.json`, `provision-cleanup*.{json,log}` |
| Stale CodeQL configuration | Removed the legacy `.github/workflows/codeql.yml:analyze` configuration's 218 analyses. Poly's SonarCloud analyses are preserved. Subsequent CodeQL inventories are empty. | `provision-cleanup-initial.json` (60 deletions), `provision-cleanup.json` (158 deletions), `provisioning-after.json` |
| Exact rulesets | Commons IDs `27356310`/`27356311`; Poly IDs `27356312`/`27356313`. Active `refs/heads/main` deletion/non-fast-forward and `refs/tags/v*` update/deletion rules, with no bypass actors or extra conditions. | `provision-rulesets.{json,log}`, `provisioning-after.json` |
| Main-only release environments | Both `hexalith-release` environments have exactly one branch policy, `main`, without required reviewers or wait timers. Both own registry-secret pairs are installed. | `provision-environments.{json,log}`, `provision-registry.json`, `provisioning-after.json` |
| Own Zot identities | Distinct `hexalith-commons-publish` and `hexalith-polymorphicserializations-publish`, scoped respectively to `commons`/`commons/**` and `polymorphicserializations`/`polymorphicserializations/**`, with read/create/update and no administrator/delete grant. | `provision-registry.{py,json,log}` |
| Scoped NuGet policy beside each legacy policy | After human authentication, created and verified Active policies `27048` (Commons) and `27049` (Poly), exact owner/repository IDs, workflow `release.yml`, environment `hexalith-release`, respective package-prefix globs, and push packages/versions only. All existing policy IDs remain. | `nuget-policy-verification.json`, `nuget-commons-readback-6.json` |
| Later settings and org grants | Completed after both policies. Existing default setup/security updates remain disabled, retention is 90 days, kill switches remain exactly `true`; Actions and Dependabot pull-secret grants and the NuGet variable select Builds and both pilots. | `provision-settings-grants.{json,log}` |

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

The saved Commons policy has owner `Hexalith`, workflow `release.yml`,
environment `hexalith-release`, package glob `Hexalith.Commons*`, and only push
of packages/versions. These fields follow the
[NuGet policy setup](https://learn.microsoft.com/en-us/nuget/nuget-org/trusted-publishing).
The original generic creation error followed by an expired session did not
establish a duplicate-name, definition or permission constraint, nor prove the
internal cause of that error. After the human authenticated, fresh inventory
showed no new policy. A subsequent Commons readback showed the new policy with
extra Stage/Unlist scopes; only that new policy was narrowed, and a real reload
confirmed the push-only result. The explicit later submit guard found the
already closed form and therefore does not establish how the original create
was submitted. The helper now selects the native owner control without Enter,
and Poly's separately guarded explicit submission produced the correct scopes.
Both legacy policies and every other existing policy ID are preserved.

The existing main workflows can produce new legacy CodeQL analyses while
product preparation is pending. Recheck stale configuration state before
adoption; do not disable or weaken those scans to keep an inventory empty.

The human separately and explicitly approved the limited pre-adoption
verification path in `pre-adoption-check-resolution.md`. Authentication alone
was not treated as that decision. The approved exact-input checks remain
required before module pushes. No nested submodule, owned-file bootstrap,
alternative credential or direct module-owned change was used.

The current execution state is in `implementation-readiness.md`: both full
released-pin product verification sets pass; Commons PR #52 and Poly PR #19 are
open and unmerged, with exact protected-token pre-push checks recorded. Product
retirement commits and registration/render/pin inputs are prepared locally.
Neither preparation main nor a delivery-triggering CiCd candidate was pushed.

Adoption still requires this exact identity answer: identify any remaining
legacy Zot automation principal and its pilot scope, or attest that the global
admins `jpiquot` and `jpiquot@itaneo.com` are maintainer-only and no legacy pilot
publisher remains. Neither pilot currently receives a legacy GitHub secret/key
grant, but that inventory does not establish a Zot principal mapping. Namespace
edits cannot revoke global admins. All concrete immediate cleanup targets are
saved in `post-adoption-cleanup-plan.md`; no legacy credential or shared admin
was removed before actual adoption.
