# What to do next — heyang

_Date: 2026-09-04 · against `main` @ `b557f8c`_
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
| **B.** Patient-level bootstrap | ⚠️ partly | The bootstrap script itself runs anywhere (numpy + the 5 committed `*_det_full764.json`). But emitting `patient_id` means re-running `eval.py` over the data → your machine. |
| **C.** Trap-rank gate | ✅ | Nothing. `WS-4_leaderboard/scoring/` is **stdlib-only** (no numpy, no torch). `python3 -m pytest scoring/tests` → 55 passed / 10 skipped. |
| **D.** Consistency items | ✅ | Repo only, except the 5-vs-8 dose-track recalculation, which needs your data. |
| **E.** WS-2 prose | ✅ | LaTeX (`compile_manuscript.bat` is already in the repo). |

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
- [ ] Before submission: state the amended criterion + SHA evidence chain in the manuscript (report §4/§8 tables and the §9 close-out are already updated).

---

## B. Patient-level bootstrap — a reviewer *will* ask

The corrected slice-level bootstrap covers **slice-sampling uncertainty only**. Slices within a patient are correlated, so even the corrected CI is optimistic about inter-patient heterogeneity. The blocker is that the committed result JSONs carry no slice → patient map.

- [ ] Emit `patient_id` per slice in `eval.py` alongside the existing `per_slice` arrays
- [ ] Add `--unit patient` to `WS-1_dataset/analysis/bootstrap_lidc_sim.py`
- [ ] Report both units; the AAPM arm already has its patient-level bootstrap

Cheapest remaining strengthening of the simulated arm.

---

## C. Write the trap-rank gate — the trap is *reported*, never *enforced*

Requiring `bander_roi` fixed **which numbers** a submission must carry. It did not add any check that the blur actually comes **last** on that index. Verified against the current tree:

- `leaderboard.py::assert_trap_present` only asserts the trap is **on the board**, not where it ranks
- `observer_sensitivity.py` *reports* trap position (`above_trap_primary`, `trap_flip`) but gates nothing
- `compute_spread`'s own docstring says separation is "checked by the R5/R6 gate, **not** by this report function" — and no such gate exists in code

So a board where the blur outranks a real method on BandER is accepted silently today.

- [ ] `assert_trap_ranks_last(entries, metric="bander_roi", by=vendor|dose)` — refuse a board where the trap is not last in **every** group
- [ ] Enforce the declared separation ratio (the ≥3× used throughout Rungs 5/6)
- [ ] Test in **both** directions: a compliant board passes, a board with the trap ranked above a method is refused

> A gate that only ever refuses passes its own test suite and fails the project. Prove it opens.

---

## D. Consistency items

- [ ] **WS-1 loader tests: not a bug — an install step.** `pytest pwm_ldct_loader` fails to collect with `No module named pwm_ldct_loader.schema`, but there is nothing to fix. It is a `src/`-layout package that is simply not installed, and the outer `pwm_ldct_loader/` directory shadows it as a namespace package. Verified: `PYTHONPATH=pwm_ldct_loader/src python3 -m pytest pwm_ldct_loader` gives **25 passed**. The real fix is `pip install -e WS-1_dataset/pwm_ldct_loader` in the dev environment; worth adding to the dev-setup docs so the next person does not treat it as a defect.
- [ ] **The recalculation verified 5 groups, not 8.** Claim ① says "8 groups (4 vendors × 2 dose tracks)" but `aapm_lidc_cross_vendor_spread.json` has 5 (four LIDC vendors at sim r=0.25, plus AAPM-Siemens real). Recalculate the second dose track, or restate the claim as 5.
- [ ] **Three separation ranges appear in the text** — 8.9–15.6× (`manuscript.tex:481,485,495`), 9.17–15.59× (`:636`), 8.9–23.1× (R6 runbook), against a measured 8.93–18.83×. Plausibly different scopes; label each with its scope so a reviewer doesn't read them as one number.
- [ ] **`R6_recalc_report.md` feedback item ① is stale** — the guide's ctformer command was already fixed (`R6独立复算操作指南.md` lines 120–133 use `ctformer_small_retrain.pt`).
- [ ] **Rebuild WS-4's `manuscript.pdf`** — the committed PDF predates the blockchain de-emphasis, so it still shows crypto-promotional text the `.tex` already removed.

---

## E. Then the other workstreams

| Order | WS | What it needs | Blocked by |
|---|---|---|---|
| 1 | **WS-2** | Prose reconciliation only — no new experiments. Make Results/Methods tense match what was actually run; fix the false PET data claim (`manuscript.tex:530` says PET data was acquired and released — it is WS-2b and does not exist); resolve the PyPI/Zenodo release claim. | nothing — **start any time** |
| 2 | **WS-3** | The Phase-3 GPU run. Wire the real LUNA16 detector (`detector.py` still raises `NotImplementedError`; the pipeline only runs via `DeterministicStubDetector`). Fix the forward-model provenance claim: Methods says the Radon operator comes from upstream `pwm_core`, but `physics.py` is a self-contained re-implementation and its own docstring says so. | WS-1 data; venue decision |
| 3 | **WS-2b** | The physical NEMA phantom scan. Nothing moves until it is acquired. | Director resourcing |
| 4 | **WS-4** | Terminal. Do **not** "finish" it by inventing cohort numbers — the past-tense scaffolding makes that temptation structural. | WS-1/2/3 + a real competition cycle |

**WS-2 is the one you can start today without waiting on anyone.**

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
