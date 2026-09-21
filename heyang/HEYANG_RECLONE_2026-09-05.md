# Heyang: please re-clone this repository (history was rewritten on 2026-09-05)

_From the owner. Counterpart of `DIRECTOR_DECISIONS.md` §2; see also `heyang/HEYANG_NEXT_STEPS.md`._

## What happened

Eight Mayo-derived pixel arrays were tracked in this repository:

    WS-1_dataset/baselines/vendor/ctformer/test_img/L506_{18,88,167,176}_{input,target}.npy   (17 MB)

They are derivatives of AAPM/Mayo patient L506, which sits under the data-use
agreement. `WS-1_dataset/physionet_listing/deposit_procedure.md` excludes
exactly that class from the release, and its step 6 makes this repository
public at submission. Those two facts could not both stand, so on
2026-09-05 the owner had the files removed from **every commit on every
branch** with `git filter-repo`, and the rewritten branches were
force-pushed. Nothing else was changed: 234 commits, four branches, every
file that was not one of the eight is byte-identical to before.

A `.gitignore` rule now refuses `L###_*.npy`, `L###_*.npz` and that
directory, so they cannot come back by accident (`ee8f06c`).

## What you must do

Your existing clone still contains the eight arrays in its object store. A
`git pull` will not work (the histories no longer share the commits after
`4875338`), and a hard reset does **not** remove objects a clone already
holds. So:

1. Save any work you have not pushed:

        cd <your clone>
        git diff > ~/heyang-uncommitted.patch          # uncommitted changes
        git log --oneline origin/main..HEAD             # unpushed commits: note them
        git format-patch origin/main -o ~/heyang-unpushed/   # if there are any

2. Clone fresh, somewhere new:

        git clone git@github.com:integritynoble/low_dose_CT.git low_dose_CT
        cd low_dose_CT

3. Re-apply your work onto the new history:

        git am ~/heyang-unpushed/*.patch     # unpushed commits, if any
        git apply ~/heyang-uncommitted.patch # uncommitted changes, if any

4. **Delete the old clone**, and any zip or backup of it made after the
   `heyang` sync of 2026-07. The arrays are inside it. This is the step that
   actually satisfies the agreement.

Please do not push from the old clone under any circumstances; it would put
the arrays back into public history.

## Commit hashes changed

Every commit from `4875338` onward has a new hash. If you recorded any of
these in notes, issues, the manuscript or `DIRECTOR_DECISIONS.md`, use the
right-hand column now.

| before | after | what |
|---|---|---|
| `4875338` | `54c58ca` | sync: full local project state onto heyang (this is where the files entered) |
| `be9576f` | `300f3b6` | R6 recalc PASS deliverables (tip of `heyang`) |
| `92fbe4a` | `5bb0eb3` | Merge branch 'heyang' into main (round 4) |
| `f93f887` | `0bffdf8` | WS-1: correct bootstrap n; audit R6 tolerance |
| `3e5f575` | `091209f` | WS-4: paired gate requires the discriminating index |
| `fe02dcc` | `2cae28f` | Record the R6 decision: route (a), deterministic re-run |
| `4bf1b99` | `1281404` | WS-4: trap-rank gate |
| `f42ebfc` | `209f655` | WS-4: refresh the permanent trap from its measured run |
| `aca7085` | `c18aa00` | WS-4: per-vendor trap measurements |
| `6dcbeaa` | `955de37` | DIRECTOR_DECISIONS 2.2: three of six rungs |
| `8e0efb1` | `d62b4fa` | WS-4: executable gates for Rungs 2, 3 and 4 |
| `a3d4cc2` | `4137c67` | DIRECTOR_DECISIONS 2.2: narrow to the re-close question |

Branch tips now: `main` → `ee8f06c` (the gitignore commit on top of
`4137c67`), `heyang` → `300f3b6`.

## Two limits, stated plainly

- GitHub keeps unreachable objects until its own garbage collection, and
  cached views or pull-request references may hold the old commits for a
  while. If the agreement needs a guarantee rather than a best effort, the
  owner will ask GitHub support to purge them.
- The rewrite reaches the remote and any clone made after it. It cannot
  reach a clone made before. That is why step 4 above is not optional.

## Nothing else changed for you

`test_img/` held only those eight files; no code or test in the repository
reads them (the CTformer vendor code takes `--test_patient L506` as a name
and reads from a data directory, not from the repository). The scoring
suite passes on the rewritten history: 96 passed, 10 skipped.
