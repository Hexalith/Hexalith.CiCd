# Pre-adoption check gap

The 2026-11-16 read-only refresh in `resume-prerequisites.json` confirms that
the required command exits 2 in both pilot roots:

```text
python3 references/Hexalith.Builds/check.py
```

This is a pipeline bootstrap defect, not a product failure. Both committed
Builds gitlinks point to `9f5d751f7ab0b7a621dcd18b589bf061fabac6ec`.
`git ls-tree` succeeds for that commit but returns no `check.py` or
`Github/lib/local_check.py`. Initializing the legacy checkout would therefore
not provide the command, even if nested initialization were permitted.

The current checker is not a drop-in bootstrap. At Builds revision
`73e60af8a1fcdf3f06726d5d1b6e1199cce778ee`, its source requires:

- A clean, separate Builds checkout matching the module's committed gitlink,
  then a committed `.github/hexalith-ci.json` naming its exact tag
  (`Github/lib/local_check.py:checkout` and `run`). Neither pilot has that
  adopted configuration.
- An accepted `delivered/<Repo>` state and its rendered perimeter
  (`Github/lib/guard.py:run` and
  `Github/lib/expected_state.py:acquire_expected`). That state belongs to actual
  App delivery; a prospective configuration cannot supply it.

The frozen story requires the Commons product hook on live main before
adoption, while its inherited policy requires this command before any module
push. Only delivery/restore may change the Builds pointer and owned
configuration. A symlink, checker copy, pointer edit, prospective owned-file
overlay, accepted-ref fixture or alternate credential would not satisfy these
combined requirements.

The smallest scope for a human resolution is a pre-adoption-only verification
decision for the product-preparation commits. It could explicitly select the
already executed package-mode product build/test/consumer checks, add policy
and commit validation plus a byte/mode/gitlink comparison proving all owned
content unchanged from freshly fetched main, and require the normal shared
command after App adoption. This is a proposed decision boundary, **not an
approved substitute or completed verification**. It requires renegotiating
the frozen pre-push requirement; no ownership exception or nested
initialization would otherwise be needed. No such substitution was made.

Keeping the literal checker requirement instead requires an approved change
to bootstrap sequencing/design that can establish genuine delivered state
before product preparation without dropping the product checks. That is a
larger change to the current AD-21 order and this story's frozen approach.

No remaining local source task requires bypassing this gap: delivery
compatibility, shared feed verification and the Commons hook are prepared
and have recorded passing regressions. Publication, module product pushes,
legacy verifier removal, production registration/render and pilot acceptance
remain incomplete. Shared publication and adoption checkboxes stay open.
