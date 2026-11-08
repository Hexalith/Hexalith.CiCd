# Baseline and targets

The success targets, the 2026-11-07 baseline they are measured from, and the measurement method. Serves the Success signal.

## Method

- Run `gh run list` for each repository over its last 200 runs. For most repositories that covers 2–5 days.
- Failure rate = failed runs ÷ completed runs. Skipped and canceled runs are excluded.
- Re-measure the targets the same way.

## Targets

| Measure | Baseline (2026-11-07) | Target |
|---|---|---|
| Main CI success rate | 0–40% in 9 repos | ≥ 95% in every repo |
| Main CI duration, 90th percentile, standard module | up to 65 min | ≤ 10 min |
| CI and release patterns in use | 2 CI flavors, 4 release patterns | 1 of each |
| Builds version spread across modules | 7–946 commits behind | all on the same version within one night of a Builds release, except a new major, a tag in `builds-skip`, or a tag that isn't acceptable. A module skipped by its own checks stays behind, reported by the red delivery run. |
| Local workflow YAML in modules | 218–3,116 lines | only the rendered `ci.yml` and `release.yml` |
| Custom-action code common to two or more modules | not measured | none |
| CI/CD changes from outside this repo that persist | frequent: 84 workflow commits in Tenants since 2026-10-01 | none; the next CI run undoes each one. The next delivery (≤ 1 h), which also reaches skipped modules, undoes what restore skips: workflow-file edits; the Builds pin and its `.gitmodules` section while the delivered Builds tag differs from the running one; and `hexalith-ci.json` until the module's workflows equal the delivered render |
| Releases | dispatched by hand | every module with releasable changes and no blocking finding is released overnight: its own run pushes the packages and containers, and the GitHub release is published by that run or by this repo's nightly run; a failure shows as a failed run in that repo and turns this repo's nightly run red |

## Run-history baseline

Overall: 2,939 completed runs, 700 failed (24%).

| Repo | CI runs | CI fail % | CI median (min) | CI p90 (min) | Notes |
|---|---|---|---|---|---|
| ChatBot | 88 | 100% | 18.8 | 36.5 | `release` runs on every push: 88 runs, 100% failed |
| Works | 56 | 100% | 6.7 | 21.5 | |
| Conversations | 46 | 91% | 7.9 | 24.6 | CodeQL median 21 min |
| Parties | 39 | 90% | 14.4 | 25.2 | |
| Folders | 26 | 88% | 15.6 | 29.3 | `contract-spine-gates` fails 74%; CodeQL median 24 min |
| Projects | 66 | 82% | 12.7 | 38.7 | |
| Agents | 57 | 70% | 11.6 | 23.4 | CodeQL median 16 min |
| McpCli | 26 | 65% | 39.3 | 65.0 | |
| Timesheets | 47 | 60% | 36.2 | 48.4 | |
| Tenants | 15 | 27% | 32.4 | 35.5 | |
| Memories | 35 | 26% | 22.2 | 55.4 | `Release` fails 29% |
| FrontComposer | 27 | 19% | 8.5 | 24.8 | `Quality` fails 55%, median 27 min |
| PolymorphicSerializations | 53 | 19% | 1.1 | 1.6 | `Commitlint` fails 91% |
| Builds | 52 | 17% | 21.3 | 30.0 | `Release` fails 30%, median 38 min |
| Commons | 79 | 13% | 1.6 | 1.8 | Fastest; shows that a 2-minute CI is achievable |

Repositories with no row:
- **AI.Tools:** no workflow runs.
- **EventStore:** its 200-run sample covers 2 days, and its CI isn't among its five most frequent workflows. Overall failure rate 8%.
- **Platform:** no workflow named CI. Its "Platform tuple CI preflight" fails 22% of the time, with a median of 11.4 min.

## Where CI fails today

Most failures come from checks on the CI itself, not from compile errors:
1. **Bespoke policy, evidence, and governance gates.** These are the most common, and each is local to one repository (`gate-classification.md`).
2. **Setup and import preparation** (`module-inventory.md`).
3. **Real test failures, reported late** by an aggregate step at the end of the run.
