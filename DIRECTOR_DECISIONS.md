# Director's list — decisions and institutional access

_Date: 2026-09-04 · against `main` @ `86cce03` · counterpart: [`HEYANG_NEXT_STEPS.md`](HEYANG_NEXT_STEPS.md)_

Everything here needs a decision, a signature, or an institutional relationship. None of it can be delegated to heyang, and most of it is what the rest of the project is waiting on.

> **The headline: the critical path is yours, not heyang's.**
> WS-1's manuscript is at zero `\todo` and the last statistics defect is fixed and pushed. What still blocks submission is almost entirely on this page. heyang's remaining work is real, but none of it gates the submission date.

---

## 1. Gating the submission date — start now

### 1.1 🔴 PhysioNet deposit

*Scientific Data* requires data deposited **at submission**, not at acceptance. Needs your account and institutional signatory.

**This has the longest lead time of anything in the project and nothing else can absorb the delay.** Every other task below can finish in days once decided; a deposit queue cannot be compressed.

- [ ] **Get an off-machine copy of the v0.5 records first — see the finding below.**
- [ ] Open the submission, reserve the accession / DOI
- [ ] Zenodo mirror for code + derived artifacts
- [ ] Hand the identifiers to heyang to fill into `manuscript.tex` and `physionet_listing/listing.md`

> ### 🔴 Finding, 2026-09-11: the deposit exists on one machine and nowhere else
>
> `deposit_procedure.md` named `gs://low-dose-ct/pwm_ldct_v0_5` as the source of the built records.
> **That path does not exist.** The entire `gs://low-dose-ct/` bucket is 96.8 KiB — one `.dcm` file.
> I checked all three visible buckets (`low-dose-ct`, `pwm-benchmark-datasets`, `pwm-backups`): none
> holds `annotations/`, `sim_lowdose/lidc/`, `metadata/`, `splits/` or `deident_audit.jsonl`.
>
> The v0.5 records exist only on the workstation that built them (`D:\ZHY\...`). **A disk failure
> there loses the release**, and with it the dataset paper's entire substrate. That risk is
> currently larger than any of the submission blockers on this page, and it is cheap to remove.
>
> Procedure corrected to point at the real location and to use `stage_deposit.py`. heyang asked to
> run a dry run and report the counts, which also tells us whether the deposit is assemblable at all
> before a submission date is promised.
>
> Separately: the lone `.dcm` sitting in `gs://low-dose-ct/` is DUA-restricted AAPM/Mayo pixel data
> and should not be there — same class as the L506 files, different location. Worth deleting once
> you confirm it is not the sole copy of something.


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

### 2.1 ✅ The R6 comparison verdict — **DECIDED 2026-09-11: route (b)**, on evidence from route (a)

**Decision: amend the operator guide to a per-metric relative criterion (1e-4 for GPU inference paths), dated, and re-run the comparison under it.**

This reverses the 2026-09-04 decision, and the reason matters more than the outcome.

**What route (a) established.** Route (a) was chosen on 2026-09-04 on the reasoning that the residual differences were cuDNN kernel non-determinism, and that determinism would therefore give `absdiff == 0`. heyang ran it properly — `cudnn.deterministic=True`, `benchmark=False`, `use_deterministic_algorithms(True)`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, ~48 GPU-hours across red_cnn / ctformer / corediff. The prediction failed:

> deterministic re-run vs non-deterministic re-run of the **same side**: `n_diffs = 0` — bit-identical.

The eval path was never sensitive to cuDNN non-determinism in that environment. The residual against the onboard reference is a **systematic cross-environment float offset** — independent recalc venv versus the onboard environment, different driver and library builds. Route (a) as scoped cannot close it, because re-running the recalc side deterministically does not change the recalc side at all.

**Why that makes route (b) legitimate rather than expedient.** A cross-environment offset is exactly the case the guide's existing hardware-differs clause was written for. Before route (a), cuDNN and environment were confounded and the clause could not honestly be invoked — relaxing then would have been adjudicating after seeing the result. Now the cause is isolated, named and logged, so the amendment records a finding rather than a convenience.

**The amendment must state that chain**, in this order, or it reads as exactly the thing it is not:

1. the pre-registered criterion was absolute 1e-6;
2. it failed, and route (a) was run to test why;
3. determinism made no difference on the recalc side (`n_diffs = 0`), ruling out kernel non-determinism;
4. the residual is therefore cross-environment, which the hardware-differs clause covers;
5. agreement is henceforth declared **per metric in that metric's own units**, at relative 1e-4 for GPU inference paths.

- [x] **Decided: route (b).** Communicated to heyang in issue #5.
- Keep `routeA_rerun_evidence` and `per_metric_declaration` in `comparison_full764.json` **exactly as they are** — they are what makes the amendment defensible. Do not overwrite the route (a) record when the verdict flips to PASS.

> The per-metric point is now settled with it: one absolute 1e-6 across metrics spanning five orders of magnitude (~2e-7 relative on `cnr_mean`, ~1e-12 on `npwe_mean`) was always going to misfire. The new criterion is per-metric by construction. `compare_full764.py` is now committed, so the verdict can be re-derived.

### 2.2 ⚠️ Rung statuses — gates now written; one question left

Rung 1 is marked **done**, and its named gate is `scoring/verify.py::check_paired_submission`. Until 2026-09-04 that gate did not enforce what Rung 1 claims — it accepted a submission on a metric the blur trap *wins*. The gate now matches the claim.

So the status is arguably *more* true than before. But a rung that sat at "done" against an unenforced gate is a fact about the ladder, not about one metric. The registry is a **public assertion about what has been verified**.

**Resolved in code on 2026-09-05, except one question.** The audit found three of six rungs marked `done` with no gate that could be exercised. Executable gates have since been written for all three, and I verified each one independently — every gate accepts the real WS-1 artifact and **catches a deliberately broken copy**, so none is vacuous:

| Rung | Gate | Verified both ways |
|---|---|---|
| 1 | `verify.py::check_paired_submission` + trap gates | ✅ |
| 2 | `gates.py::check_pairing_validation` | ✅ catches a 0.97 correlation against the 0.99 target |
| 3 | `gates.py::check_roi_protocol` | ✅ catches a trap that is not last on ROI BandER |
| 4 | `gates.py::check_dose_curve` | ✅ catches a trap whose knee is reported as reached |
| 5 | `compute_spread`; `trap_rank_by_group` | ✅ |
| 6 | `trap_rank_by_group` | ✅ |

All six now name an executable gate in the registry, and the suite is **96 passed / 10 skipped**. Each gate also ships accept/reject probes, so any gate added later is audited automatically rather than by hand.

**What is still yours to decide** — one question, much narrower than before:

- [ ] **Rung 1 (and by extension 2, 3, 4): re-close with a dated note, or leave the status?** These rungs were marked `done` while their gates were unenforced or unwritten. The gates now match the claims, so the statuses are more true than when they were set — but they were set before the evidence existed. Either re-close them with a dated note recording the 2026-09-05 alignment, or leave them and record why.

Both are defensible. **Silence is not** — the registry is a public assertion about what has been verified. This is cheap now and expensive to explain if someone audits the ladder later.

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
