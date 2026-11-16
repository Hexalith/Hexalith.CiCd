# Disposable local live qualification proposal

This plan has not run. It supplies local product evidence only; it cannot
establish App adoption, an acceptable Builds release or a genuine scheduled
nightly outcome. Preserve the retained host `dapr_redis` and other sessions.

Read-only capability and image metadata are in
`local-isolated-runtime-capability.json` and `isolation-image-readback.json`.
The host has no standalone `dockerd`/rootlesskit, but Docker works and the SDK
image is already cached.

Use only these identified image inputs, rechecking their identities at launch:

- SDK: `mcr.microsoft.com/dotnet/sdk@sha256:65f3c7c6a25a239ab3e6719f2896147e7b68242ff2d8818dd70498bde6ef8bea`, Linux amd64, SDK tag `11.0.100`.
- Official Docker DinD Linux amd64 manifest: `docker.io/library/docker@sha256:9d337aaf171682751be04d67c15d880d6a95c6fd44cb8e12043f605012e5e654`.

Docker's [official image instructions](https://hub.docker.com/_/docker) describe
DinD's privileged container requirement. Its [container run reference](https://docs.docker.com/reference/cli/docker/container/run/)
documents sharing a container's network namespace. Create two task-named
containers only: one fresh daemon, then one SDK worker sharing that daemon's
network namespace and an own temporary Unix socket. Publish no host ports and
never mount the host Docker socket, home directories or credentials into either
container. The SDK worker's `localhost:6379` will belong to this private job.
Record and compare the inner/outer daemon identities before setup.

Run the orchestrator through `run-with-temp`. Put daemon data, source projections,
socket, private receipts, logs and all outputs below its `TMPDIR`. Git projections
must carry their own objects, without alternates referring outside the mounted
job workspace. Preserve exact root candidate and direct gitlink identities;
initialize no nested submodules. Wait for all work and remove only the two
recorded container IDs and their own scratch files in a `finally` block.

Use one source-bound shared Builds candidate for the entire local job. Candidate
`cbd13a1e93015182439112918cae4216b953f9bf` supports the proposed setup; its
source-only status and exact prerequisites are recorded separately. Build the
Release package graph once, run the classified units, then perform shared setup
once and execute the product hooks and remaining classified projects. Local job
identity inputs must be labelled synthetic local qualification inputs. Generate
receipts through the actual shared initializer from newly observed Docker state;
do not manufacture a receipt or call this an authenticated hosted job. Do not
write a delivered configuration or claim that candidate source is published.

Collect actual failures, count/skip policy, exact coverage scopes, runtime tuple
and duration. The locally invoked nightly product hook is a workload test, not
the required next scheduled central nightly. Retain the separate released
`v6.0.6` bootstrap proof; a candidate-only local job does not satisfy the released
prerequisite for registration.

GHA `::add-mask::` output does not mask an ordinary local process. Keep raw output
private inside `TMPDIR`; consume mask commands and redact their values before
retaining any log outside scratch. Retain only established support-safe result
shapes and sanitized diagnostics. Never persist private custody, environment
files, generated key material or raw topology logs. Await topology/daemon exit
before deleting their temporary data, and independently confirm the retained
host backend was not replaced or restarted by this work.
