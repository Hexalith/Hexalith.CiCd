# Prerequisite discovered during story 21: native build reuse

The approved Parties migration requires every retained native scenario and
forbids repeated hook builds. The shipped native runner cannot currently satisfy
both conditions. This records an implementation blocker; it does not change the
approved package boundary or claim that shared support has shipped.

## Exact inspected interfaces

The cached `Hexalith.Builds.Module.Cli` 5.2.2 nuspec names source
`02ed624aa19781cac75d2c9112940e9bd830441a`. Parties' unchanged Builds gitlink
`73e60af8a1fcdf3f06726d5d1b6e1199cce778ee` is v6.0.4; CiCd's selected v6.0.6
is `fdda17c0a4538b0f7c99f813c20ca24b49006530`. Exact file hashes and relevant
source lines for all three are recorded in
`../specs/spec-cicd/evidence/21/runner-build-reuse.json`.

- `NativeTestExecutor.CreateArguments` emits `dotnet test --project` for MTP
  without `--no-build` or `--no-restore`. Each selected execution adds a new
  private `test-builds` artifact root.
- `PlatformManifestCommand` compiles the Platform model into each run workspace.
- `PlatformManifestValidator` permits a Python entry only in source mode;
  package-mode native profiles require their declared .NET project entry.

The native fixture consumes the runner-issued descriptor and credential/control
channels. Launching its DLL without those channels cannot replace the real
scenario. Changing the profile to source mode, providing an unvalidated shim,
or repinning old CI receipts would violate the approved boundary.

## Required shared capability

Add an explicit, validated way to consume the original audited Release test and
composition artifacts without restoring or compiling them in a hook. Keep
existing consumers' default behavior. Bind reused artifacts to the selected
source, package cohort, target framework, configuration and composition model;
reject missing, stale, foreign or changed bytes.

Preserve private credential issuance, descriptor ownership, authenticated
endpoints, persisted-state observation, cancellation, attachment expiry,
termination and cleanup, and native TRX validation. Preserve every declared
Parties native scenario. Tests must demonstrate reuse across profiles without
compiler invocations and reject mismatches through the same production boundary.

Ship and qualify this capability through the authorized shared release process
before enabling package-mode native hooks for Parties. The frozen-created
prerequisite remains separate. Neither prerequisite authorizes adoption,
registration, a credential change, publication or a bypass in this local phase.
