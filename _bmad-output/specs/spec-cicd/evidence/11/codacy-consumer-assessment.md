# Commons consumer subprocess finding

The current probe check reports one subprocess-input warning at
`scripts/validate-consumer-package-references.py:159`. Its exact status and
annotation are preserved in `legacy-commons-codacy-check.json`. The external
check remains `action_required`; no ignore, suppression, threshold change,
rerun or external setting change has been made.

## Source assessment

The original main already invoked `subprocess.run(["dotnet", *args], ...)`.
The preparation change retains that list-based invocation and does not enable
a shell. Its two callers supply fixed restore/build argument lists for the
generated `Consumer.csproj`. The added arguments are fixed package-mode,
audit-off and trusted-config flags; the config path is constructed inside the
script's private temporary directory. The user-supplied package directory is
not appended to the process argument list. The SDK pin is copied unchanged,
and package/consumer behavior passed the real isolated checks.

This source inspection does not identify a new shell/argument injection path
introduced by the change. It is a candidate false-positive/differential
finding, rather than an established security waiver. The check summary reports
one solved and one added issue, but that summary alone does not prove how
Codacy matched the old and new locations.

The warning text matches Bandit's B603 wording. The engine/rule ID is not
included in the GitHub annotation, so that association is an inference.
[Bandit's primary documentation](https://bandit.readthedocs.io/en/latest/plugins/b603_subprocess_without_shell_equals_true.html)
describes a low-severity input-inspection warning for shell-free subprocess
launches, including fixed argument lists. Its warning is a request to inspect
inputs; a matching message alone does not establish an exploit.

## Remaining disposition

Keep the finding visible and resolve its Codacy triage before claiming green
quality checks or accepting the pilot checkpoint. Do not move the call to hide
it, add a suppression, weaken the zero-new-issue threshold, or treat successful
C# tests/CodeQL as disposing of this separate finding.
