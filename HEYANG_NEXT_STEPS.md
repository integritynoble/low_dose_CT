# What to do next — heyang

_Written: 2026-09-04 · against `main` @ `b557f8c` · Checklist synced to `f704da8` (2026-09-07 checkpoint) on 2026-09-08._
_Diagnosis: [`REVIEW_FOR_HEYANG.md`](REVIEW_FOR_HEYANG.md) · Director's decisions: [`DIRECTOR_DECISIONS.md`](DIRECTOR_DECISIONS.md)_

This page is **execution work only**. Anything needing a decision, a signature, or institutional access is on the Director's list, not here.

**Where things stand.** Your `heyang` branch is merged to `main`. WS-1's manuscript is at **zero `\todo`** — it went from scaffolding to a filled paper backed by a real GPU run and your independent recalculation. Two defects found in review are already fixed and pushed.

The R6 recalculation is the strongest research-integrity artifact in this repository: independent venv, independent toolchain, byte-level source verification, and it reported **its own** two errors — the cached LIDC low-dose tree and the checkpoint/guide mismatch — rather than quietly fixing them. Both defects found in review were findable *because* of that discipline. Keep it.

---

## Blocked on the Director — do not start these

| Waiting on | What you'll do once decided |
|---|---|
| **Tolerance route (a) or (b)** | §A below — the re-run |
| **PhysioNet / Zenodo DOIs** | fill them into `manuscript.tex` + `physionet_listing/listing.md` |
| **Authors / ORCID / CRediT / IRB no.** | fill the manuscript header and declarations |
| **Vendor licensing + Mayo `.npy` decision** | remove or repoint the vendored files |
| **WS-3 venue** | revive or retire `manuscript_method_miccai.tex` |

---

## What each task needs — check before you start

Verified against a clean checkout on 2026-09-04.

| Task | Runs from a clean clone? | Needs |
|---|---|---|
| **A.** R6 re-run | ❌ | **Your machine only.** Checkpoints are gitignored (`*.pt`), and the LIDC/AAPM trees live on your `D:\ZHY\...` paths. Nobody else can reproduce this without your assets — which is exactly why `ASSET_MANIFEST.md` matters. |
| **B.** Patient-level bootstrap | ⚠️ code done (2026-09-06) | Code complete: `PairedSlices` carries `patient_id`, `eval.py` per_slice emits it, `bootstrap_lidc_sim.py --unit patient` does block bootstrap (slice behaviour unchanged; `.bak` kept). Remaining: re-run `eval.py` on your machine to regenerate the 5 `*_det_full764.json` with `patient_id`, then bootstrap reports both units. |
| **C.** Trap-rank gate | ✅ | **Done 2026-09-06.** `assert_trap_ranks_last` (trap last on `bander_roi` in every vendor group, ≥3× separation) + 12 bidirectional tests; enforced at `save()`. `scoring/tests` → **77 passed**. |
| **D.** Consistency items | ✅ | Repo only. All five items done as of 2026-09-07 (see checkboxes); the 5-vs-8 dose-track question was resolved by restating the recalc scope rather than recalculating the second dose track. |
| **E.** WS-2 prose | ✅ | LaTeX (`compile_manuscript.bat` is already in the repo). Done 2026-09-04/07 (`cc8766a` + `f704da8`). |

**You have `write` access and `main` is unprotected**, so you can push directly — no PR needed unless you want review.

---

## A. The R6 re-run — **as soon as the route is picked**

**DONE — closed 2026-09-06 via route (b).**

- [x] Route (a) run to completion for `red_cnn` / `corediff` / `ctformer` with deterministic kernels. Verdict: re-runs are **bit-identical to the earlier recalc** (SHA-256 unchanged), so determinism does NOT remove the differences vs on-board → route (a) cannot close the absolute-1e-6 FAIL.
- [x] Route (b) selected by heyang. Dated guide amendment written into `R6独立复算操作指南.md` (2026-09-06): GPU inference paths compare at **per-metric RELATIVE 1e-4**, with the *why* recorded (cross-environment float bias, worst reldiff 6.4e-5; an absolute 1e-6 is ~1e-12 relative on `npwe_mean` and is not reproducible across GPU environments).
- [x] Comparator fixed to declare agreement **per metric in that metric's own units**: `compare_full764.py` now judges on relative 1e-4 (blur/learn remain bit-identical).
- [x] Regenerated `comparison_full764.json` → `overall: PASS`, all five models PASS.
- [x] Re-ran `python3 R6_recalc/tolerance_audit.py --write`; the audit block was rewritten to record the route-b criterion, the route-a SHA evidence chain and the resolution.
- [x] `compare_full764.py` committed with this change (it was previously uncommitted — an artifact whose generator is missing cannot be re-derived).
- [x] Before submission: state the amended criterion + SHA evidence chain in the manuscript — **done 2026-09-07 (`f704da8`)**; `manuscript.tex` §Reproducing the baseline results now states the per-metric RELATIVE 1e-4 criterion (dated amendment 2026-09-06), the determinism-kernel rerun SHA chain, worst reldiff 6.4e-5, and the machine verdict `overall: PASS` (report §4/§8 tables and the §9 close-out were already updated).

---

## B. Patient-level bootstrap — a reviewer *will* ask

The corrected slice-level bootstrap covers **slice-sampling uncertainty only**. Slices within a patient are correlated, so even the corrected CI is optimistic about inter-patient heterogeneity. The blocker is that the committed result JSONs carry no slice → patient map.

- [x] Emit `patient_id` per slice in `eval.py` alongside the existing `per_slice` arrays — code done 2026-09-06; JSON regeneration pending data-machine rerun
- [x] Add `--unit patient` to `WS-1_dataset/analysis/bootstrap_lidc_sim.py` — done 2026-09-06 (slice mode byte-identical to previous)
- [x] Report both units; the AAPM arm already has its patient-level bootstrap — **done 2026-09-08**: `corediff_results_det_full764.json` regenerated with `patient_id` (2-GPU seed-shard parallel, merged; aggregate/per-seed bit-identical to the 2026-08-30 version, only per_slice gained `patient_id`, len 764 across 5 seeds); all five models now carry `patient_id`; `bootstrap_lidc_sim.py --unit patient --pooling distinct` run → `output/lidc_simulated_bootstrap_stats_full764_patient.json` (B=4000). Slice-unit stats remain at `lidc_simulated_bootstrap_stats_full764.json`.

Cheapest remaining strengthening of the simulated arm.

---

## C. Write the trap-rank gate — the trap is *reported*, never *enforced*

Requiring `bander_roi` fixed **which numbers** a submission must carry. It did not add any check that the blur actually comes **last** on that index. Verified against the current tree:

- `leaderboard.py::assert_trap_present` only asserts the trap is **on the board**, not where it ranks
- `observer_sensitivity.py` *reports* trap position (`above_trap_primary`, `trap_flip`) but gates nothing
- `compute_spread`'s own docstring says separation is "checked by the R5/R6 gate, **not** by this report function" — and no such gate exists in code

So a board where the blur outranks a real method on BandER is accepted silently today.

- [x] `assert_trap_ranks_last(entries, metric="bander_roi", by=vendor|dose)` — refuse a board where the trap is not last in **every** group
- [x] Enforce the declared separation ratio (the ≥3× used throughout Rungs 5/6)
- [x] Test in **both** directions: a compliant board passes, a board with the trap ranked above a method is refused

> A gate that only ever refuses passes its own test suite and fails the project. Prove it opens.

**DONE 2026-09-06.** `scoring/leaderboard.py` now has `assert_trap_ranks_last` + `TRAP_MIN_SEPARATION = 3.0`; `save()` refuses a persisted board whose trap is not last (or cannot prove it is last) on `bander_roi` within any vendor group. `scoring/tests/test_trap_rank_gate.py` adds 12 bidirectional cases (pass: clean groups / no groups; refuse: trap above a method, <3× separation, unrefreshed trap, missing member metric, per-dose grouping). `scoring/tests` → **77 passed**.

---

## D. Consistency items

- [x] **WS-1 loader tests: not a bug — an install step.** `pytest pwm_ldct_loader` fails to collect with `No module named pwm_ldct_loader.schema`, but there is nothing to fix. It is a `src/`-layout package that is simply not installed, and the outer `pwm_ldct_loader/` directory shadows it as a namespace package. Verified: `PYTHONPATH=pwm_ldct_loader/src python3 -m pytest pwm_ldct_loader` gives **25 passed**. The real fix is `pip install -e WS-1_dataset/pwm_ldct_loader` in the dev environment; worth adding to the dev-setup docs so the next person does not treat it as a defect. — **done 2026-09-07** (`fb1fb35` corrected the item; `pwm_ldct_loader/README.md` lines 66–70 now carry the editable-install command and the 25-passed verification; `f704da8` added two more lines).
- [x] **The recalculation verified 5 groups, not 8.** Claim ① says "8 groups (4 vendors × 2 dose tracks)" but `aapm_lidc_cross_vendor_spread.json` has 5 (four LIDC vendors at sim r=0.25, plus AAPM-Siemens real). Recalculate the second dose track, or restate the claim as 5. — **done via restate (2026-09-06/07)**; the second dose track was not recalculated. The runbook claim ① and `R6_recalc_report.md` §7 statement ① now state the recalculated scope explicitly (vendor dimension: 5 groups, measured 8.93–18.83×; the 23.1× upper bound is attributed to the cross-dose AAPM-Siemens real-QD level). No "8 groups (4 vendors × 2 dose tracks)" wording remains. If the second dose track must be covered numerically, schedule a separate data-machine rerun.
- [x] **Three separation ranges appear in the text** — 8.9–15.6× (`manuscript.tex:481,485,495`), 9.17–15.59× (`:636`), 8.9–23.1× (R6 runbook), against a measured 8.93–18.83×. Plausibly different scopes; label each with its scope so a reviewer doesn't read them as one number. — **done**; every occurrence is now scope-labelled: manuscript table captions and results text state the vendor-dimension 5-group scope (measured 8.93–18.83×) and cite `9.17–15.59×` as a patient-level bootstrap CI; the runbook claim ① carries its recalc scope (see previous item). The four numbers are no longer presented as interchangeable.
- [x] **`R6_recalc_report.md` feedback item ① is stale** — the guide's ctformer command was already fixed (`R6独立复算操作指南.md` lines 120–133 use `ctformer_small_retrain.pt`). — **done**; the report's recommendation ① now carries the explicit "已采纳：指南已更新为 ctformer_small_retrain.pt" annotation, so the stale-recommendation reading is gone.
- [x] **Rebuild WS-4's `manuscript.pdf`** — the committed PDF predates the blockchain de-emphasis, so it still shows crypto-promotional text the `.tex` already removed. — **done 2026-09-07** (`f704da8` rebuilt `WS-4_leaderboard/paper_draft/manuscript.pdf`; `.tex` and `.pdf` timestamps now match at 2026-09-07 13:27).

---

## E. Then the other workstreams

| Order | WS | What it needs | Blocked by |
|---|---|---|---|
| 1 | **WS-2** | Prose reconciliation only — no new experiments. Make Results/Methods tense match what was actually run; fix the false PET data claim (`manuscript.tex:530` says PET data was acquired and released — it is WS-2b and does not exist); resolve the PyPI/Zenodo release claim. | **done 2026-09-04/07** — worked-example tense corrected to planned/scheduled wording (`f704da8`); false PET claim retracted in Data availability (`cc8766a`); PyPI / docs / Zenodo release claims made conditional on acceptance (`cc8766a`, `f704da8`). Remaining are submission-time `\todo`s (author declarations, acknowledgments), which belong to the Director's list. |
| 2 | **WS-3** | The Phase-3 GPU run. Wire the real LUNA16 detector (`detector.py` still raises `NotImplementedError`; the pipeline only runs via `DeterministicStubDetector`). Fix the forward-model provenance claim: Methods says the Radon operator comes from upstream `pwm_core`, but `physics.py` is a self-contained re-implementation and its own docstring says so. | WS-1 data; venue decision |
| 3 | **WS-2b** | The physical NEMA phantom scan. Nothing moves until it is acquired. | Director resourcing |
| 4 | **WS-4** | Terminal. Do **not** "finish" it by inventing cohort numbers — the past-tense scaffolding makes that temptation structural. | WS-1/2/3 + a real competition cycle |

**With WS-2's prose reconciliation done, no unblocked non-GPU repo work remains on this list.** The open items are §B (patient-level bootstrap report — blocked on the data machine until `corediff` finishes and all five JSONs are regenerated with `patient_id`) and the items on the Director's list (physio/IRB/authorship/vendor licensing). WS-3 remains the next science workstream once the venue decision lands.

---

## Submission-package note

When assembling the *v0.5* package: **`manuscript.tex` + `refs.bib` + referenced figures only.**

`manuscript_v1.tex`/`.pdf` (v1.0 target, D9+365–540) and `manuscript_tex_pre_ctformer_retrain.tex` (pre-retrain archive) are **deliberately preserved — do not delete them** (`paper_draft/README.md:93`). They simply don't ship in v0.5. An earlier review called them "stray"; that was wrong and is retracted.

---

## Already fixed — no action needed

- ✅ **Bootstrap `n` corrected.** The 5-seed grid `{42, 2023, 7, 12345, 999}` produces **byte-identical** per-slice vectors, so the "3,820 pooled slices" were five exact copies of 764 — `n` inflated 5×, every CI narrowed by ≈√5. Now resamples the 764 distinct slices; CIs 1.7–2.4× wider; CTformer knee `0.131 [0.128,0.135]` → `[0.123,0.139]`. **No conclusion flips**, point estimates unchanged. Generator committed at `analysis/bootstrap_lidc_sim.py`; `--pooling seed_pooled` reproduces the old numbers exactly.
- ✅ **The seed gate reworded** — it now says the seed set certifies determinism rather than quantifying variance, which is what it actually does.
- ✅ **`bander_roi` required by the paired gate**, plus the silent extraction bug that made the leaderboard carry-through dead code and the Rung 5 spread block fidelity+CNR only.
- ✅ **`ASSET_MANIFEST` A2 filled** — no placeholders remain.

> ⚠️ **Leaderboard migration:** a submission reporting only CNR/CHO-AUC/NPWE is now **rejected**. Add `detectability.bander_roi` (protocol `detectability-freq-v1`). Stored seed entries are unaffected — the gate runs on incoming submissions only.
