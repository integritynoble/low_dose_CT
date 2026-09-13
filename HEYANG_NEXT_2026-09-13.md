# heyang — next steps, 13 September 2026

Supersedes [`HEYANG_NEXT_2026-09-08.md`](HEYANG_NEXT_2026-09-08.md). Written against `main` @ `72ba063`.

> **Please read this file rather than GitHub issues.** Six issues (#3, #4, #5, #22, #23, #24) were
> opened and assigned to the `BeiTa9` account between 4 and 13 September. That account has shown no
> activity since June, so the assignments almost certainly never reached you. Everything actionable
> from all six is reproduced here. That was our mistake in channel, not yours — the file convention
> this project has always used is the one that works, and we left it.

---

## 1. Two failing tests block the merge — fix these first

On `heyang` @ `2b5e379`: **2 failed, 124 passed, 10 skipped**.

```
scoring/tests/test_trap_numbers.py::test_trap_metrics_still_match_their_source_run
scoring/tests/test_trap_numbers.py::test_vendor_trap_metrics_still_match_their_source_run
```

**The data is completely fine.** We diffed both source runs between `main` and `heyang`: every
measured value, `updated_at` and key set is identical, and the parsed JSON compares equal. Nothing
about the trap moved. This is a line-ending trap, not a science problem:

| file | LF (Linux/CI) | CRLF (your Windows checkout) |
|---|---|---|
| `aapm_r3_roi_detectability.json` | `9987864a…` | **`49dddf9d…`** ← the constant in `leaderboard.py` |
| `aapm_lidc_cross_vendor_spread.json` | `c4364074…` | **`5b67f1f9…`** ← same |

Both constants are the **CRLF** hashes. Git converted line endings on checkout, the hash was taken
of the on-disk bytes, and those constants can now never match on any LF machine. The root cause is
that there is **no `.gitattributes` at the repo root**, so a byte-level hash of a text file is
platform-dependent and this will recur on the next provenance hash anyone adds.

Three parts, all needed:

1. Repo-root `.gitattributes`:
   ```
   *.json    -text
   *.sha256  -text
   ```
2. Restore the **LF** hashes in `leaderboard.TRAP_SOURCE` and `VENDOR_TRAP_SOURCE`
   (`9987864a…`, `c4364074…`).
3. Make the check line-ending-proof — normalise `\r\n` → `\n` before hashing, or hash the
   recanonicalised JSON rather than raw bytes. Part 1 stops it happening; part 3 stops it mattering.

**Done when** `python3 -m pytest scoring/tests` is green from the same commit on **both** your
Windows checkout and a Linux one. Please confirm both — a one-sided pass is what produced this.

The test did its job here. It refused to let the board's trap drift away from the run that produced
it; the failure is the mechanism working, not misfiring.

---

## 2. Rebase onto `main` in the same pass

`heyang` is **19 ahead** of a `main` that has moved **10+** since your merge base (`dd8e395`) — the
exact count keeps rising, so check it rather than trusting this line:

```bash
git fetch origin && git rev-list --left-right --count origin/main...origin/heyang
```

Four files conflict, all R6:

```
DIRECTOR_DECISIONS.md
WS-1_dataset/R6_recalc/R6_recalc_report.md
WS-1_dataset/R6_recalc/results/comparison_full764.json
WS-1_dataset/R6_recalc/R6独立复算操作指南.md
```

### ⚠️ `comparison_full764.json` — take `main`'s version, not yours

| | `main` | `heyang` |
|---|---|---|
| `overall` | **PASS** | FAIL |
| per-model | all five PASS | red_cnn / ctformer / corediff FAIL |
| criterion | per-metric, superseded state recorded | `tolerance_kind: absolute`, 1e-6 |

`main` carries the route (b) outcome the Director decided (`b472707`): the per-metric relative
criterion, verdict flipped to PASS and **derived rather than asserted**. Your branch still holds the
superseded absolute-1e-6 FAIL. **Keeping your side would silently revert that decision.**

Your ~48 GPU-hours are not lost by taking `main` — `routeA_rerun_evidence` and
`per_metric_declaration` are both preserved in it. That is deliberate: the route (a) finding is what
justified route (b), so it was carried forward.

During a rebase `--ours` means `main` and `--theirs` means your own commits — inverted from normal
usage, which is exactly how people take the wrong side without noticing. So verify rather than trust
the flag:

```bash
git checkout --ours WS-1_dataset/R6_recalc/results/comparison_full764.json
python3 -c "import json;d=json.load(open('WS-1_dataset/R6_recalc/results/comparison_full764.json'));print(d['overall'],'|','routeA_rerun_evidence' in d)"
# expect: PASS | True        (if it prints FAIL, you took the wrong side)
```

Better still, **regenerate** rather than hand-merge — an 800-line generated JSON should not be
reconciled by hand. Note the two sides carry different generators, and after the rebase you will have
both:

| script | on | role |
|---|---|---|
| `compare_full764.py` | `heyang` only | the original absolute-tolerance comparator |
| `recompare_per_metric.py` | `main` only | **produced the PASS verdict** under the per-metric criterion |

So regenerate with **`recompare_per_metric.py`** — it is the one whose output `main` carries. Running
`compare_full764.py` would reproduce the superseded absolute-1e-6 FAIL, which is the same wrong
outcome as keeping your side of the file.

### The other three

Prose — merge them, do not pick a side. `main` has the route (b) amendment, yours has the route (a)
run detail, and the argument is the *sequence*: pre-registered criterion failed → route (a) tested
why → determinism ruled out → cross-environment offset → per-metric criterion. Dropping either half
breaks it. `DIRECTOR_DECISIONS.md` is the Director's file: take `main` and raise disagreements rather
than editing it inside a rebase.

### Before pushing

- [ ] Suite green on **Linux**, not only Windows
- [ ] `overall` is `PASS` and `routeA_rerun_evidence` present
- [ ] `git rev-list --objects heyang | grep -c test_img/L506` → `0`
- [ ] `main` is at **108 passed / 10 skipped**; yours should be that plus your additions

Force-pushing your own branch after a rebase is expected and fine. Do not force-push `main`.

---

## 3. Two questions only you can answer — a comment is enough, no runs

We found the discriminating index is gameable from **both** ends:

- **Current direction (higher better):** a pure noise injector scores ~183 at +20 HU and ~1598 at
  +60 HU — beating every real method by 100–1000× — and passes the trap-rank gate, because the blur
  still ranks last.
- **Symmetric (`|log BandER|`):** the ranking *inverts* and the blur trap becomes the **best** entry
  on AAPM held-out, because 0.432 is closer to the reference than CTformer's 6.735. In 2 of 5 vendor
  groups the trap stops ranking last too.

Your gate is not at fault — `trap_rank_by_group` answers its question correctly, in both directions,
per group. The problem is one level down, in the index.

**(a)** All four learned methods sit **3.9–6.7× above** the full-dose reference, and 23 of 36
measured values across vendors exceed 2×. Is that mostly residual low-dose noise the denoiser did not
remove, sharpening, or texture the 1-px high-pass band happens to respond to? You have seen the
output images; a one-line impression is worth more than another statistic.

**(b)** In `detectability-freq-v1` **as you designed it**, was "higher ROI BandER is better" intended,
or was *closer to the full-dose reference* the intent, with the trap merely sitting at the low end?
The leaderboard's descending sort is not yours — that is `leaderboard.py`, written elsewhere. If the
intent was the second, the leaderboard has been reading your index backwards since it was wired in.

**"I don't remember, it wasn't a deliberate choice" is a perfectly good answer** — better than a
reconstructed rationale. Either answer saves the RTX5090 operator from testing hypotheses you can
rule out in a sentence. Reply in a commit message, a file, or however suits you.

---

## 3b. Two measurements only your machine can do — BANDER-2 and BANDER-6

**Added 13 September, after the RTX 5090 handed this back.** The assignment originally went there on
the assumption that the AAPM and LIDC trees were on that workstation. They are not — the R3
artifact's own `tree` field and all 25 lines of `WS-1_dataset/R6_recalc/hashes/aapm_hashes.txt` point
at `D:\ZHY\low_dose_CT-heyang\WS-1_dataset\pipelines\_runtime\aapm_tree_v1`, which is **your
machine**. That was our error, caught by the operator. So these two land with you, because the data
is with you.

Both are **CPU work** — deterministic image operations and a few lines of numpy. If you find yourself
waiting on a GPU, something is mis-scoped.

### Start from the branch — do not rewrite it

```bash
git fetch origin && git checkout bander/control-matrix    # a42ad27, off main @ 72ba063
```

`scripts/bander_controls.py` already implements the five controls as pure functions of the full-dose
image — blur, additive Gaussian noise at a fixed seed, unsharp oversharpening, truncated-frequency
ringing, and lesion erasure inside a disc — with 10 passing unit tests. **BANDER-1 is done. Do not
redo it.**

### BANDER-2 — the controls on the real slices

Compute ROI BandER for every control on the **same slices and the same tissue ROIs** the committed R3
artifact used, with the protocol code unmodified. The point is a table of control-vs-BandER that is
directly comparable to the committed real-method values. Then repeat on the LIDC four-vendor slices
(that part is BANDER-4) so the answer is not one cohort.

**What is already known, on a phantom rather than your slices:** no scalar function of whole-ROI
BandER separates all five controls. Raw descending *rewards* every noise arm and oversharpening;
`|log B|` and `|B-1|` catch everything **except lesion erasure**, which scores 0.999 against an ideal
of 1.000. The diagnosis is sharper than the negative — lesion erasure is 317 px of 65,536, **0.48% of
the slice**, so the failure is in the **spatial aggregation**, not the transform. The same statistic
measured *inside* the lesion moves from 0.9992 to 0.0997.

Your job is to confirm or refute that on real anatomy. A negative result is the expected outcome and
is fully acceptable work.

### BANDER-6 — is the excess high-frequency energy a simulator artefact?

This one may matter more, and it came out of a question about why CTformer's PSNR is lower than
everyone else's. PSNR at dose ratio 0.25, in-domain versus out-of-domain:

| method | LIDC simulated | AAPM real | drop | BandER on AAPM |
|---|---:|---:|---:|---:|
| **blur (the trap)** | 41.65 | 41.63 | **0.02 dB** | 0.432 |
| RED-CNN | 53.65 | 41.20 | **12.45 dB** | 3.876 |
| LEARN | 57.06 | 41.61 | **15.45 dB** | 3.854 |
| CTformer | 55.32 | 39.59 | **15.73 dB** | 6.735 |

**The blur trap is the only method that transfers.** It loses 0.02 dB going from simulated to real,
because it learned nothing there was anything to lose. Every learned method loses 12–16 dB, and the
one that loses most is also the one furthest above the reference on BandER.

That is consistent with the learned methods having fitted **the release's own projection-domain
simulator** and emitting simulator-shaped texture on real data. If so, the excess high-frequency
energy is neither "residual noise" nor "sharpening" — it is in-domain behaviour applied
out-of-domain, and no rescoring of BandER would identify it.

**Measure BandER per method on LIDC-simulated and AAPM-real slices side by side, one protocol.** If
the excess is a transfer effect it should be small or absent in-domain and large out-of-domain. If
BandER is similarly elevated on LIDC too, the hypothesis is wrong and one of the other explanations
stands.

Report it either way. **Concluding that the benchmark's large cohort largely measures the simulator
rather than the reconstruction problem is within what this work should be willing to say** — it would
be a significant finding, not a failure.

### Rules

Do **not** tune a control until it fails, drop one because it is inconvenient, or search over scores
until one passes and report only that. And separation from a cheat is not evidence the index tracks
diagnostic content — BandER has still never been checked against a reader.

**Do not change any scoring rule, gate, tolerance or registry status.** This produces evidence for a
decision the Director has not taken. Code belongs on the branch; keep raw logs, images and data on
your machine.

**This is lower priority than §1 and §2.** The merge comes first.

---

## 4. The deposit exists on one machine — please make a copy

`deposit_procedure.md` said to pull the built records from `gs://low-dose-ct/pwm_ldct_v0_5`. **That
path does not exist**; the whole bucket is 96.8 KiB. None of the three visible buckets holds
`annotations/`, `sim_lowdose/lidc/`, `metadata/`, `splits/` or `deident_audit.jsonl`.

So the v0.5 dataset appears to exist **only on your workstation**. A disk failure there loses the
release and the dataset paper's substrate with it. **An off-machine copy is the cheapest insurance in
the project** — not the formal deposit, just a copy that is not on that one disk.

When convenient, also run:

```bash
python3 WS-1_dataset/physionet_listing/stage_deposit.py \
    --source <root holding annotations/ sim_lowdose/ metadata/ splits/ deident_audit.jsonl> \
    --out pwm_ldct_v0_5_deposit --dry-run
```

It copies nothing in dry-run mode and lists every expected part it cannot find, which tells us whether
the deposit is assemblable before a submission date is promised. If it finds DICOM, `LNNN_*.npy/npz`
or harmonized AAPM/Mayo HDF5 it **refuses and stages nothing** — deliberate, so a DUA breach cannot
pass silently.

---

## 5. Things that changed under you

- **The repository is public** as of 13 September. If you have a clone from before **5 September**,
  please **re-clone rather than pull**: eight Mayo-derived `L506_*.npy` files were removed from git
  history entirely on the 5th, and a hard reset does not delete objects a clone already holds. See
  [`HEYANG_RECLONE_2026-09-05.md`](HEYANG_RECLONE_2026-09-05.md).
- **CoreDiff is un-vendored.** Upstream carries no licence, so publishing a copy was not ours to do.
  `vendor/CoreDiff/fetch.sh` retrieves it. `corediff_wrapper.py` raises a message naming the script if
  it is missing. Every other baseline is unaffected.
- **R6 is settled at PASS** under the per-metric criterion (route (b)) — see §2.
- **WS-2 prose reconciliation** (#4) is still open and still needs no new experiments; the two false
  claims in it (the PET data claim, the PyPI/readthedocs URLs) were already fixed on `main`.

---

## What was good

The route (a) re-run was the right piece of work and you reported it straight. The finding that
determinism made no difference on the recalc side — `n_diffs = 0` — is what ruled out cuDNN and
established the residual as a cross-environment offset. That negative result is what let the criterion
be changed *on evidence* rather than post-hoc, which is the difference between a defensible PASS and a
convenient one. It cost ~48 GPU-hours to find out the prediction was wrong, and that was worth paying.

The patient-level bootstrap refusing on files without a `patient_id` vector, rather than silently
falling back, is the same instinct and equally right.
