# Hexalith.CiCd
Maintain harmonized Hexalith CI/CD workflows threw all modules

BMAD Loop worktrees initialize the direct submodules declared in `.gitmodules`
at their pinned commits. Nested submodules stay uninitialized, even when Git's
`submodule.recurse` setting is enabled. Initialization failures stop that unit
before its coding session starts.

After setting up BMAD Loop on a new machine, enable the project hook:

```bash
bmad-loop plugins enable direct-submodules
```

The hook runs when worktree isolation is selected (`[scm] isolation = "worktree"`
in `.bmad-loop/policy.toml`).
