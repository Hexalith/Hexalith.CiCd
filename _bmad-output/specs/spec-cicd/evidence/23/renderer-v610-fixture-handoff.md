# Story 23 released renderer fixture correction

The one-file correction is in `cicd-story-23-v610/tools/tests/test_render.py`,
based on `d37a20a3318daba15066faa28f651730a7e9939e`. No production renderer,
validation code, lock, template, pin or rendered file changed. No commit or
remote write occurred. The actual repository index remains unchanged.

`renderer-v610-fixture-binding.json` binds the exact diff and proposed tree
`01b0f74ffaebb5b9eb73f2341564c64ef69b89cc`. The retained patch is
`renderer-v610-fixture-correction.patch`; source SHA-256 is
`9a9b14173cd97a503b7d6269d299d454fdbf0a00764b6364fdb5215b4b9d9d0c`.

Historical refusal/absence fixtures now explicitly select actual `v6.0.6`
(`fdda17c0a4538b0f7c99f813c20ca24b49006530`). Generic fixtures retain the
production selector, currently actual `v6.1.0`
(`a1e0c310b1f1a50d78e6132890fae6bcba769f6d`). Timeout transitions select those
real objects instead of text-splicing the old loader. Manual/platform fixtures
also consume the selected release rather than copying mutable Builds worktree
bytes. Complete current default documents and caller jobs remain exactly
asserted, including added test defaults, timeout, Windows authority arguments,
job dependencies and action environment. A separate complete legacy document
and caller check preserves the old shape. The original legacy Linux-runner
refusal remains; the current generic runner-negative case uses an unsupported
runner because the new contract deliberately allows hosted Linux jobs.

Fresh red runs each executed 46 tests with the same 11 failures. The first
correction runs each executed 47 tests with one remaining exact Windows job
expectation failure; that expectation was corrected and its focused case passed.
A later concurrent uv cached-environment attempt failed before tests because
Jinja2 was absent. All these failed attempts remain in their original logs and
are not accepted final qualification.

Accepted final qualification ran sequentially, each under `run-with-temp` with
its own `UV_CACHE_DIR` beneath that job's `TMPDIR`. Python 3.12.13 and 3.14.4 each
passed all 47 renderer tests, zero failures and zero skips. Exact interpreter
versions, base executable SHA-256, installed dependency versions, source/lock
hashes, commands and log hashes are in `renderer-v610-fixture-correction.json`
and `renderer-v610-qualified-python{312,314}.json`. The accepted final logs are
`renderer-v610-qualified-python{312,314}.log`. `git diff --check` passed.

All child work has finished and private verification workspaces have closed.
The parent still owns inspection, commits, the unchanged complete `validate.py`
rerun and remote decisions. This focused result does not establish a successful
full global validation, publication of the pin, Tenants product qualification,
registration, adoption, legacy revocation or scheduled-nightly acceptance.
