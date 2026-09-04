# What to do next — heyang

_Date: 2026-09-04 · against `main` @ `572fcaa` · companion to [`REVIEW_FOR_HEYANG.md`](REVIEW_FOR_HEYANG.md)_

That review is the diagnosis. This is the task list, in the order I would do it.

**Where things stand.** Your branch is merged to `main`. WS-1's manuscript is at **zero `\todo`** — it went from scaffolding to a filled paper backed by a real GPU run and an independent recalculation. Two defects found in review are already fixed and pushed. **WS-1 is now the closest workstream to submission, not WS-2**, and what remains is mostly paperwork with one long lead time in it.

Everything below is either a decision only you can make, or work that needs your machine, your data, or your institution.

---

## Do these in parallel, starting today

### ⏱️ A. Start the PhysioNet deposit — **longest lead time, start first**

*Scientific Data* requires the data deposited **at submission**, not at acceptance. Every other WS-1 task can finish in a week; this one cannot. Nothing else on this list gates it, so there is no reason to wait.

- [ ] Open the PhysioNet submission and get the accession / DOI reserved
- [ ] Zenodo mirror for the code + derived artifacts
- [ ] Fill the DOIs into `WS-1_dataset/paper_draft/manuscript.tex` and `physionet_listing/listing.md`

> If the deposit turns out to have a long queue, say so early — it changes the submission date and nothing else on this list can absorb that delay.

### 🔴 B. Resolve the vendored third-party content — **blocks making the repo public**

Code Availability points readers at this repository, so this must be settled before it goes public. Item 3 is the urgent one: it is a data-use question, not a licensing preference.

- [ ] **`vendor/ctformer/test_img/*.npy` are Mayo-derived slices** (`L506_*`). These are DUA-restricted and are currently redistributed in-repo. Remove them, or confirm in writing that redistribution is permitted.
- [ ] **CoreDiff ships no license file.** LEARN has Apache-2.0, CTformer has a LICENSE, CoreDiff has neither. Get the upstream license or drop the vendored copy and pin by commit + SHA instead.
- [ ] **Third-party pretrained weights** are redistributed (`ctformer/model_pretrained/T2T_vit_530000iter.ckpt`, `LEARN/examples/.../LEARN_MODEL.mat`, the 85 MB `proMatrix_64.mat`). Check each upstream license permits it; otherwise move to a Zenodo record and pin by SHA.

### 📋 C. Clear WS-1's four administrative blockers

All four 🔴 sections of `WS-1_dataset/SUBMISSION_CHECKLIST.md`. None of this is research — it is forms, and it is the only thing between WS-1 and a submission.

- [ ] **Authors, affiliations, ORCIDs, corresponding author** — `manuscript.tex` title block still says "Authors to be confirmed"
- [ ] **CRediT contribution statement**
- [ ] **Per-author competing interests.** The PWM Protocol Foundation equity/token disclosure is **not optional at a medical venue** and is currently a `\todo`. Undisclosed, it is the kind of thing that gets a paper retracted rather than rejected.
- [ ] **IRB determination number** — obtain the letter, cite the number. Do not assert a determination whose number you do not have.
- [ ] **Funding / grant numbers**, cover letter, reporting summary
- [ ] **Assemble the submission package from `manuscript.tex` only** — plus `refs.bib` and the figures it actually references.

> ⚠️ `manuscript_v1.tex` (v1.0 target, D9+365–540 window) and `manuscript_tex_pre_ctformer_retrain.tex` (pre-retrain archive) are **deliberately preserved — do not delete them** (`paper_draft/README.md:93`). They simply do not go in the v0.5 package. The two manuscripts coexist; do not conflate them. An earlier review of this repo advised stripping them as "stray", which was wrong — the submission-hygiene issue is what goes *into the package*, not what exists in the repo.

---

## One decision I deliberately left to you

### ⚠️ D. The R6 comparison verdict

`R6_recalc/results/comparison_full764.json` says `"overall": "FAIL"`; `R6_recalc_report.md` §8 says `PASS*`. The repo currently ships a machine-readable FAIL that only prose overrides. I did **not** resolve this, because quietly relaxing the threshold would just relocate the prose `PASS*` into a script constant. `R6_recalc/tolerance_audit.py` characterises it; the original `status`/`overall` fields are untouched.

Two routes, and they are **not** equal:

**Route (a) — deterministic re-run. Recommended.**

The differences are non-deterministic kernel selection, not float64 limits — a 764-term reduction accumulates ~1e-8 absolute at `npwe_mean` ≈ 9.7e5, two orders inside the 1e-6 budget. So with determinism on, the runs should be **bit-identical** and the existing criterion passes **as written**, with no amendment and no change to the kind of test. This is the only route that leaves the pre-registered rule untouched.

```python
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
torch.use_deterministic_algorithms(True)
```
Then re-run step 4 for `red_cnn`, `corediff`, `ctformer` and regenerate the comparison. Expect `absdiff == 0`.

**Route (b) — amend the guide.** Write a dated amendment stating that GPU inference paths compare at **relative** 1e-4, and say why; then re-run. This changes the *kind* of test, which is a larger thing to ask a reviewer to accept.

> Whichever you pick: the comparator should declare agreement **per metric in that metric's own units**. One absolute 1e-6 is ~2e-7 relative on `cnr_mean` and ~1e-12 on `npwe_mean` — it will misfire again on the next submission even under perfect determinism.

Run `python3 WS-1_dataset/R6_recalc/tolerance_audit.py` to see the full ladder.

### ⚠️ E. Rung 1's status — re-close it, or record why not

Rung 1 is marked **done**, and its named gate is `scoring/verify.py::check_paired_submission`. Until 2026-09-04 that gate did not enforce what Rung 1 claims — it accepted a submission on a metric the blur trap wins. The gate now matches the claim, so the status is arguably *more* true than it was. But a rung that sat at "done" for its whole life against an unenforced gate is a fact about the ladder, not about one metric.

Both of these are defensible; **silence is not**, because the registry is a public assertion about what has been verified.

- [ ] **Either** re-close Rung 1 with a dated note recording that the gate was aligned on 2026-09-04
- [ ] **Or** leave the status and record why that is the right call

Same question applies to Rungs 5 and 6, whose `bander_roi` spread block could never populate from a submission (see "Already done" below).

---

## Then, in order

### F. Strengthen the simulated arm — patient-level bootstrap

The corrected slice-level bootstrap covers slice-sampling uncertainty only. Slices within a patient are correlated, so even the corrected CI is optimistic about inter-patient heterogeneity. The fix needs a **slice → patient map** persisted into the result JSONs, which the current ones do not carry.

- [ ] Emit `patient_id` per slice in `eval.py` alongside `per_slice`
- [ ] Add a `--unit patient` mode to `WS-1_dataset/analysis/bootstrap_lidc_sim.py`
- [ ] Report both; the AAPM arm already has its patient-level bootstrap

This is the single cheapest remaining strengthening of the simulated arm, and a reviewer *will* ask.

### G. Write the trap-rank gate — the trap is still only *reported*, never *enforced*

Requiring `bander_roi` fixed which numbers a submission must carry. It did **not** add a check that the blur actually comes last on that index. Verified against the current tree:

- `leaderboard.py::assert_trap_present` only asserts the trap is **on the board**, not where it ranks.
- `observer_sensitivity.py` *reports* trap position (`above_trap_primary`, `trap_flip`) but gates nothing.
- `compute_spread`'s own docstring says separation is "checked by the R5/R6 gate, **not** by this report function" — and no such gate exists in code.

So today a board on which the blur trap outranks a real method on BandER would be accepted silently. That is the check which turns the trap from something a person notices into something the bench enforces.

- [ ] `assert_trap_ranks_last(entries, metric="bander_roi", by=vendor|dose)` — refuse a board where the trap is not last on the discriminating index in **every** group
- [ ] Enforce the declared separation ratio (the ≥3× used throughout Rungs 5/6)
- [ ] Test in **both** directions: a compliant board passes, a board with the trap ranked above a method is refused

### H. Small consistency items

- [ ] **WS-1 loader tests do not collect** — `No module named pwm_ldct_loader.schema`. Packaging, not logic; the 25/25 suite should run again.
- [ ] **The recalculation verified 5 groups, not 8.** Claim ① says "8 groups (4 vendors × 2 dose tracks)" but `aapm_lidc_cross_vendor_spread.json` has 5 (four LIDC vendors at sim r=0.25, plus AAPM-Siemens real). Either recalculate the second dose track or restate the claim as 5.
- [ ] **Three separation ranges appear in the text**: 8.9–15.6× (`manuscript.tex:481,485,495`), 9.17–15.59× (`:636`), 8.9–23.1× (R6 runbook), against a measured 8.93–18.83×. Plausibly different scopes — label each with its scope so a reviewer does not read them as one number.
- [ ] Update `R6_recalc_report.md`'s "feedback to author" item ①: the guide's ctformer command **was already fixed**; that recommendation is stale.

### I. Then the other workstreams

| Order | WS | What it needs | Blocked by |
|---|---|---|---|
| 1 | **WS-2** | Prose reconciliation only — no new experiments. Make the Results/Methods tense match what was actually run, fix the false PET data claim, resolve the PyPI/Zenodo release claim. | nothing |
| 2 | **WS-3** | The Phase-3 GPU run; wire the real LUNA16 detector (`detector.py` still raises `NotImplementedError`); pick **one** venue. | WS-1 data |
| 3 | **WS-2b** | The physical NEMA phantom scan. Nothing moves until it is acquired. | scanner access |
| 4 | **WS-4** | Terminal. Do **not** "finish" it by inventing cohort numbers — the past-tense scaffolding makes that temptation structural. | WS-1/2/3 + a real competition cycle |

---

## Already done — no action needed

- ✅ **Bootstrap *n* corrected.** The 5-seed grid was five byte-identical copies of 764 slices, inflating *n* 5× and narrowing every CI by ≈√5. `analysis/bootstrap_lidc_sim.py` is now committed (the generator was previously missing — only its outputs were in the repo) and resamples the 764 distinct slices. CIs are 1.7–2.4× wider; CTformer knee `0.131 [0.128,0.135]` → `[0.123,0.139]`. **No conclusion flips** and point estimates are unchanged.
- ✅ **The seed gate reworded.** It now says the seed set certifies determinism rather than quantifying variance — which is what it actually does.
- ✅ **`bander_roi` added to the paired gate.** It required only CNR/CHO-AUC/NPWE, so a submission could pass on a metric the blur trap *wins*. Also repaired a silent second bug: `bander_roi` was dropped in extraction, making the leaderboard carry-through dead code and the Rung 5 spread block fidelity+CNR only.
- ✅ **`ASSET_MANIFEST` A2 filled.** No placeholders remain.

> ⚠️ **Migration note for the leaderboard:** a submission reporting only CNR/CHO-AUC/NPWE is now **rejected**. Add `detectability.bander_roi` (protocol `detectability-freq-v1`). Stored seed entries are unaffected — the gate runs on incoming submissions only.

---

## What not to lose

The R6 recalculation is the strongest research-integrity artifact in this repository — independent venv, independent toolchain, byte-level source verification, and it reported **its own** two errors (the cached LIDC low-dose tree, the checkpoint/guide mismatch) rather than quietly fixing them. That habit is why both defects found in this review were findable at all. Keep it.

Same for the blur trap. It is doing exactly its job: it is precisely what exposed the gate defect in the section above.
