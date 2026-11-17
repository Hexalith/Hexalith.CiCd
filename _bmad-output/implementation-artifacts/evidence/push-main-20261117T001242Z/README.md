# Prepared push candidates

All existing module commits are available on remote main. Only Folders and Platform contain pending module content.

- Folders: seven changed files applied without conflict to fresh main `3ff01eeab6f6dfe7cff83e4ef3e1ff403c50c245`; owned tree, released audit/actions and exact message checks pass.
- Platform: three changed files on main `8ccb479e391564ce982309f106504cf8329c0a43`; owned tree, released actions and exact message checks pass. Released audit rejects the historical `shared-restore-import-closure/graph-export-imports.xml` for forbidden audit/test declarations.
- CiCd: pending content applies without conflict to current main. Released audit/actions and exact message checks pass. Parent publication remains dependent on module publication.

The latest retained Platform workload-binding suite ran 51 tests with one error in `test_real_provider_supports_non_1000_caller_with_private_host_files`. Complete exact-input module preparation qualification is unfinished. Existing successful focused checks do not replace it.

See [prepared source identities and results](prepared-candidates.json), the repository patches and message files, and [authenticated release proof](released-policy-proof.json). Policy came from immutable Builds v6.0.6 (`fdda17c0a4538b0f7c99f813c20ca24b49006530`), with locked installation and npm signature verification.

No live index, branch or worktree was changed by preparation. No commits or pushes were performed by this session. Disposable jobs finished and their workspaces were removed. An explicit user decision about overriding the required qualification is pending; [the existing procedure](../../../../docs/pre-adoption-publication.md) otherwise blocks module and parent publication. Revalidate current source and bases before acting on a decision.
