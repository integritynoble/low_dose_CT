# Director's list — decisions and institutional access

_Date: 2026-09-04 · against `main` @ `b557f8c` · counterpart: [`HEYANG_NEXT_STEPS.md`](HEYANG_NEXT_STEPS.md)_

Everything here needs a decision, a signature, or an institutional relationship. None of it can be delegated to heyang, and most of it is what the rest of the project is waiting on.

> **The headline: the critical path is yours, not heyang's.**
> WS-1's manuscript is at zero `\todo` and the last statistics defect is fixed and pushed. What still blocks submission is almost entirely on this page. heyang's remaining work is real, but none of it gates the submission date.

---

## 1. Gating the submission date — start now

### 1.1 🔴 PhysioNet deposit

*Scientific Data* requires data deposited **at submission**, not at acceptance. Needs your account and institutional signatory.

**This has the longest lead time of anything in the project and nothing else can absorb the delay.** Every other task below can finish in days once decided; a deposit queue cannot be compressed.

- [ ] Open the submission, reserve the accession / DOI
- [ ] Zenodo mirror for code + derived artifacts
- [ ] Hand the identifiers to heyang to fill into `manuscript.tex` and `physionet_listing/listing.md`

### 1.2 🔴 IRB determination number

Obtain the letter and cite the number. Needs your institutional standing.

Do **not** let the manuscript assert a determination whose number is not in hand — `manuscript.tex` currently carries `\todo{IRB determination no.}`, which is the honest state. Attach the actual letter.

### 1.3 🔴 Authorship

`manuscript.tex` still reads **"Authors to be confirmed."** Only you can settle this.

- [ ] Author list and order
- [ ] Affiliations and ORCIDs
- [ ] Corresponding author
- [ ] CRediT contribution statement (follows from the above)

### 1.4 🔴 Per-author competing interests

**This one is about your own position specifically:** PWM Protocol Foundation equity, tokens, consulting, board seat.

Currently a `\todo`. At a medical venue an undisclosed financial interest in an entity the work promotes is the kind of thing that gets a paper **retracted rather than rejected**. It costs nothing to disclose and is not negotiable.

Related: WS-4's prize pool is funded "in PWM tokens" from the "PWM Protocol Foundation Reserve" by organizers who benefit from token appreciation driven by challenge publicity. That is a genuine competing interest and the COI section does not currently disclose it. Decide the real funding instrument, then disclose it.

### 1.5 Funding / grant numbers

For the Acknowledgements and the PhysioNet listing.

---

## 2. Decisions heyang is blocked on

### 2.1 ✅ The R6 comparison verdict — **DECIDED 2026-09-04: route (a)**

`R6_recalc/results/comparison_full764.json` ships `"overall": "FAIL"`; `R6_recalc_report.md` §8 says `PASS*`. The repo contains a machine-readable FAIL that only prose overrides. It was deliberately left unresolved rather than fixed by loosening the threshold, which would have moved the prose `PASS*` into a script constant — the same post-hoc adjudication in a less visible place. **Now resolved by decision, not by adjustment.**

| Route | What it costs | What it asks of a reviewer |
|---|---|---|
| **(a) Deterministic re-run** ← **CHOSEN** | one GPU re-run of 3 models | nothing — the pre-registered rule passes as written |
| (b) Amend the guide | a dated amendment + re-run | accept a changed *kind* of test |

Route (a) works because the differences are **non-deterministic kernel selection, not float64 limits** — a 764-term reduction accumulates ~1e-8 absolute at `npwe_mean` ≈ 9.7e5, two orders inside the 1e-6 budget. With determinism on, the runs should be bit-identical and your existing criterion passes untouched. If they come back *not* bit-identical, that is informative — heyang has been told to report it rather than loosen the threshold.

- [x] **Decided: route (a), the deterministic re-run.** Communicated to heyang in issue #5. No amendment to the guide is needed; the pre-registered absolute 1e-6 stands.

> Still open regardless: the comparator applies **one absolute 1e-6 across metrics spanning five orders of magnitude** (~2e-7 relative on `cnr_mean`, ~1e-12 on `npwe_mean`). It will misfire again on the next submission even under perfect determinism. heyang has been asked to make it declare agreement per metric, and to commit `compare_full764.py`, which is not in the repo.

### 2.2 ⚠️ Rung 1's status in the registry

Rung 1 is marked **done**, and its named gate is `scoring/verify.py::check_paired_submission`. Until 2026-09-04 that gate did not enforce what Rung 1 claims — it accepted a submission on a metric the blur trap *wins*. The gate now matches the claim.

So the status is arguably *more* true than before. But a rung that sat at "done" against an unenforced gate is a fact about the ladder, not about one metric. The registry is a **public assertion about what has been verified**.

- [ ] **Either** re-close Rung 1 with a dated note recording the 2026-09-04 alignment
- [ ] **Or** leave it and record why that is right

Both are defensible. **Silence is not.** Same question applies to Rungs 5 and 6, whose `bander_roi` spread block could never populate from a submission.

### 2.3 🔴 Vendored third-party content — legal, not engineering

**This blocks making the repo public**, and Code Availability points readers at it.

- [ ] **`vendor/ctformer/test_img/*.npy` are Mayo-derived** (`L506_*`) — **DUA-restricted data, currently redistributed in-repo.** This is the urgent one: a data-use question, not a licensing preference.
- [ ] **CoreDiff ships no license file** (LEARN has Apache-2.0, CTformer has a LICENSE, CoreDiff has neither)
- [ ] **Third-party pretrained weights** redistributed — `T2T_vit_530000iter.ckpt`, `LEARN_MODEL.mat`, the 85 MB `proMatrix_64.mat`

### 2.4 When the repo goes public

Follows from 2.3. Code Availability URLs 404 until it does, and *Scientific Data* will check them.

### 2.5 WS-3's venue — pick one

The two-manuscript problem is unresolved. `manuscript_method_miccai.tex` is stale relative to the cleaned main track: it still foregrounds blockchain/IPFS/registry framing and carries liver-lesion content the main track deliberately removed.

- [ ] Revive it (strip that framing, apply double-blind anonymization), **or** retire it so it stops reintroducing inconsistencies

---

## 3. Resourcing decisions

### 3.1 WS-2b is dead until a phantom is physically scanned

Nothing in WS-2b can move until the NEMA NU-2 IQ phantom is filled, scanned across decay, thinned and reconstructed. `analysis/extract_roi_means.py` raises `NotImplementedError` because the VOI placement "cannot exist until the scans do" — which is the honest state.

- [ ] Schedule the scan, **or** formally park WS-2b so it stops appearing as active

### 3.2 WS-4 must not be "finished"

It is a protocol template for an annual review of a competition that does not exist until ~2028. Its abstract and results are pre-written in past tense with blanks. **That structure invites fabrication.** Do not let it be "completed" by inventing cohort numbers.

Worth doing now anyway: rebuild the stale `manuscript.pdf` (the committed PDF predates the blockchain de-emphasis, so it still shows crypto-promotional text the `.tex` already removed).

---

## If you do only three things this week

1. **Open the PhysioNet deposit** — the only item that cannot be compressed later.
2. **Settle authorship + COI** — pure decisions, cost only your time, unblock the whole manuscript header.
3. ~~Pick route (a) on the tolerance~~ ✅ **done 2026-09-04** — issue #5. Next-most-useful: **Rung 1's status** (§2.2) and the **vendored-content decision** (§2.3), which blocks going public.

---

## What you are *not* blocked on

These are already fixed and pushed; no decision needed:

- Bootstrap `n` corrected (the 5-seed grid was five identical copies; CIs were ≈√5 too narrow). **No conclusion flipped**, point estimates unchanged.
- The seed gate reworded to say what it actually does — certify determinism, not quantify variance.
- `bander_roi` required by the paired gate, plus the silent extraction bug that made the leaderboard carry-through dead code.
- `ASSET_MANIFEST` A2 filled; no placeholders remain.
