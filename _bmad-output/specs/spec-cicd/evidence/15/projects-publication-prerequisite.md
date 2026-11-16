# Projects publication prerequisite

McpCli's production package-mode restore at source
`e2e3db7ba2d45d61feacc39c41b3051310fbc57f` requires
`Hexalith.Projects.Contracts` `2.0.0-story66.3`. The public NuGet index still
lists versions through `1.2.4`; the required preview is absent. The introducing
McpCli commits and required candidate source are bound in
`projects-dependency-investigation.json`.

Public `1.2.4` is not a behavior-preserving substitute: it lacks the required
query decoration and brings the excluded UI/runtime dependency closure.
`projects-public-attributes.json` and the public nuspec preserve that inspection.
Do not replace the package with a fabricated/local feed, remove enrollment,
weaken dependency policy or count source-mode checks as package-mode proof.

Read-only GitHub observations during this continuation show the latest Projects
release is `v1.2.4` (published 2026-11-12), while Projects main is
`981ceef13a1abc88219925e73c51a23eb9ac50c2` with the message
`docs: mark story 6.7 in progress`. No Projects files, settings, tags or releases
were changed by this session.

The owning Projects work must make a compatible Contracts package publicly
restorable through its authorized release process. If it publishes a different
version, assess its real metadata/API/dependency closure before changing the
McpCli dependency pin, then run the complete required package-mode build,
product and consumer checks against those actual bytes. No safe substitute has
yet been established. The human's coordination question remains pending;
unrelated Projects implementation/publication is outside story 15's frozen
scope until explicitly renegotiated.

After the dependency is available, resume McpCli preparation from its recorded
baseline, freshly fetch main and verify the exact owned bytes/modes/gitlink
comparison and all approved pre-push checks. Adoption also waits for the
acceptable shared Builds release from central nightly and the remaining
registration, delivery, cleanup, platform/live and genuine nightly evidence.
