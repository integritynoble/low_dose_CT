# What to do next — heyang

> **SUPERSEDED, 8 September 2026.** The current list is
> [`HEYANG_NEXT_2026-09-08.md`](HEYANG_NEXT_2026-09-08.md). This page is kept because the later one cites it,
> and because its diagnosis and its "what each task needs" table are still good. Its ordering is not: several
> items are done, and its note on the R6 re-run has been corrected there. Do not work from this page alone.


> **2026-09-05, read first:** the repository's history was rewritten to remove DUA-restricted L506 pixel arrays. Your clone must be replaced, not pulled. See [`HEYANG_RECLONE_2026-09-05.md`](HEYANG_RECLONE_2026-09-05.md) for the steps and the old-to-new commit hash table.


_Date: 2026-09-04 · against `main` @ `86cce03`_
_Diagnosis: [`REVIEW_FOR_HEYANG.md`](REVIEW_FOR_HEYANG.md) · Director's decisions: [`DIRECTOR_DECISIONS.md`](DIRECTOR_DECISIONS.md)_

This page is **execution work only**. Anything needing a decision, a signature, or institutional access is on the Director's list, not here.

**Where things stand.** Your `heyang` branch is merged to `main`. WS-1's manuscript is at **zero `\todo`** — it went from scaffolding to a filled paper backed by a real GPU run and your independent recalculation. Two defects found in review are already fixed and pushed.

The R6 recalculation is the strongest research-integrity artifact in this repository: independent venv, independent toolchain, byte-level source verification, and it reported **its own** two errors — the cached LIDC low-dose tree and the checkpoint/guide mismatch — rather than quietly fixing them. Both defects found in review were findable *because* of that discipline. Keep it.

---

## Blocked on the Director — do not start these

| Waiting on | What you'll do once decided |
|---|---|
| ~~Tolerance route (a) or (b)~~ **decided: (a)** | §A below — the re-run, now unblocked (issue #5) |
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

## A. The R6 re-run — **route (a) DECIDED 2026-09-04, tracked in issue #5**

Route **(a)** was chosen. Run:

```python
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
torch.use_deterministic_algorithms(True)
```

- [ ] Re-run step 4 for `red_cnn`, `corediff`, `ctformer` (blur and learn are already bit-identical)
- [ ] Regenerate `comparison_full764.json` — expect `absdiff == 0` and `overall: PASS`
- [ ] Re-run `python3 R6_recalc/tolerance_audit.py --write` so the audit block reflects the new run

If **route (b)**: write the dated guide amendment first, then re-run the comparison against the declared relative criterion.

**Either way** — fix the comparator to declare agreement **per metric in that metric's own units**. One absolute 1e-6 is ~2e-7 relative on `cnr_mean` and ~1e-12 on `npwe_mean`; it will misfire again on the next submission even under perfect determinism.

> `compare_full764.py` is **not committed** — only its output is. Please commit it with this change, the same way `analysis/bootstrap_lidc_sim.py` now is. An artifact whose generator is missing cannot be re-derived.

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
