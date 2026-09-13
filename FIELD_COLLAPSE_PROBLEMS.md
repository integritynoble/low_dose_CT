# What the low-dose CT field needs solved before it can collapse

_Date: 2026-09-13 · checked against `main` @ `b472707` · companion to [`DIRECTOR_DECISIONS.md`](DIRECTOR_DECISIONS.md)_

The charter's five-year goal is a claim about collapse:

> *"If your low-dose CT reconstruction method is not on the PWM Low-Dose CT Challenge leaderboard, it is not state-of-the-art."*

A field collapses when proposing a new method stops being a way to make an argument — when a method's worth is settled by a measurement nobody can dispute or game, and the only remaining work is engineering. This page lists what stands between [`ldct_agent`](https://github.com/integritynoble/ldct_agent) and that, ranked by how load-bearing each problem is.

Every claim below is checked against artifacts in this repository, with the command that reproduces it. Nothing here is aspirational.

---

## 1. The scoring problem — a score no smoother can win

**Status: open. This is the whole game.**

On the AAPM held-out test (4 patients, real full-dose/quarter-dose pairing), the permanent Gaussian-blur trap — a deliberate cheat that does nothing but smooth — ranks **first on three of the four indices a reader reaches for first**:

| method | PSNR | SSIM | CNR | ROI BandER |
|---|---|---|---|---|
| **Gaussian blur (trap)** | **41.63** ① | **0.9653** ① | **0.1706** ① | 0.4315 ④ |
| learn | 41.61 | 0.9358 | 0.1036 | 3.8539 (8.93×) |
| red_cnn | 41.20 | 0.9340 | 0.1036 | 3.8762 (8.98×) |
| ctformer | 39.59 | 0.9120 | 0.0863 | 6.7352 (15.61×) |

_Source: `WS-1_dataset/output/aapm_r3_roi_detectability.json`._

While that table is true, **"state of the art" is unfalsifiable**: any method can be made to win by choosing the index that suits it. Fidelity and detectability are decoupled, and the decoupling favours the cheat.

Only ROI BandER separates the trap, and it does so cleanly (8.9–15.6× here, 8.9–19.0× across vendors, trap last 4/4 in every group). The gate now requires it (`scoring/task_spec.py::DISCRIMINATING_FIELDS`) and refuses a board where the trap does not rank last (`leaderboard.py::trap_rank_by_group`).

**What remains:** BandER has never been validated against a human reader. The agent can enforce that the discriminating index is reported and that the trap loses on it. It cannot yet establish that the index measures diagnostic content rather than a different artefact the trap happens to fail. Until it does, the field has a gameable score replaced by an unvalidated one.

---

## 2. The clinical anchor problem — nobody has said what "better" means

**Status: open. This is the true blocker.**

```
$ python3 -m ldct_agent.cli compare ctformer red_cnn
  mean_delta   2.8590      spread     1.2553      n  4
  p            0.0198      wilcoxon_p 0.1003
  ci95         [1.8841, 4.0913]        mde80  2.6116
  agreement    4/4 positive
  bander_roi: +2.8590 against a patient spread of 1.2553 over 4 patients.
  Not demonstrated: the smallest worthwhile effect has not been set by a
  clinician; no corrected test was reported.
```

Every number favours CTformer. The verdict is still **not demonstrated**, and correctly so: no radiologist has said how much BandER improvement is worth having.

**A field cannot close while it cannot say what counts as an improvement.** Every comparison downstream of this is arithmetic without a unit. This is the one problem on this page that no amount of engineering solves — it needs a clinician to commit to a number, prospectively, before results are seen.

Until then the agent's honest output is a refusal, which is right and also terminal.

---

## 3. The generalization problem — no single number is legitimate

**Status: established; the agent enforces it.**

The trap's own band energy spans **9.5× across vendors** — GE 0.0452 to AAPM-Siemens 0.4315. The consequence, asserted in `test_the_global_check_would_wrongly_fail_a_low_band_energy_vendor`:

> GE's weakest real model (0.4377) clears **its own** GE trap by 9.67×, and the AAPM trap by only 1.014×.

A single global threshold therefore **fails an entry that is fine in its own group**. There is no valid scalar leaderboard — only a per-group object. Cross-vendor averaging is not conservative, it is wrong.

The trap turns out to be the cleanest demonstration of why Rung 6 forbids the cross-group comparison. `trap_rank_by_group` checks inside each group and never across.

**What remains:** "the leaderboard", as normally imagined — one ranked list — cannot exist. The agent must keep refusing aggregate claims rather than computing them, and the competition design has to present a per-vendor, per-dose object that a reader can still act on.

---

## 4. The power problem — the real evidence base is ten patients

**Status: open. No agent can solve this.**

Every real paired-dose result rests on **AAPM 2016: 10 patients, 4 held out**. The `mde80` of 2.61 against an observed 2.86 means the study can only detect effects roughly the size of the largest one present.

LIDC supplies 1,010 patients, but its low-dose is **simulated** by the release's own forward model, and the simulation-versus-real validation figure the argument leans on does not exist. So the large cohort is not independent evidence of the thing being claimed.

**What remains:** orders of magnitude more genuinely paired acquisitions, or a validated simulator. Both are acquisition problems. The agent's role is to keep refusing to let simulated scale be quoted as real evidence — which it does by reporting the two sources separately and never averaging them.

---

## 5. The reproduction problem — bit-identical is unattainable, and now proven

**Status: solved in principle; the criterion is settled.**

The R6 recalculation ran the deterministic re-run over ~48 GPU-hours with `cudnn.deterministic=True`, `use_deterministic_algorithms(True)`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`. The finding:

> deterministic vs non-deterministic re-run of the **same side**: `n_diffs = 0` — bit-identical.

So the eval path was never cuDNN-sensitive, and the residual against the reference is a **systematic cross-environment float offset** (different venv, driver, library build). No amount of determinism closes it.

The conclusion generalises past this project: **an independent recalculation in a different environment cannot be required to match bit-for-bit.** Agreement must be declared **per metric, in that metric's own units, in advance** — the repository's shipped criterion applied one absolute 1e-6 to metrics spanning five orders of magnitude, which was ~2e-7 relative on `cnr_mean` and ~1e-12 on `npwe_mean`, and could never have been met.

A related failure kept recurring: **generators were missing while their outputs were committed** — `compare_full764.py` and `bootstrap_lidc_sim.py` both. An artifact whose generator is absent cannot be re-derived by anyone, including its author later.

---

## 6. The verification problem — gates that were only claims

**Status: closed for rungs 1–6; must stay closed for rungs nobody has written yet.**

Every one of these was a rule the project believed it already had:

| defect | what it meant |
|---|---|
| 3 of 6 rungs marked `done` with no executable gate | the ladder asserted verification that could not be run |
| `DETECTABILITY_FIELDS` omitted `bander_roi` | the gate required metrics the trap **wins** |
| `bander_roi` dropped in `extract_paired_methods` | the leaderboard carry-through was dead code; Rung 5 spread was fidelity+CNR only |
| `sort_entries` ranked by `cnr_mean` first | the board's displayed order led with the metric the trap wins |
| `assert_no_referee_paths` walked values, never keys | a referee-owned path in a key reached the board |
| the trap was reported, never enforced | a board where the trap ranked first passed every gate |

The pattern is one thing: **a rule that is stated is not a rule that is enforced.** Rung 7 — every gate executable and exercised in both directions — is the correct generalisation, and `PROBES` makes it apply to gates written later by anyone.

**What remains:** keeping it true as the ladder grows. A gate that ships without probes silently re-opens this.

---

## 7. The incentive problem — nothing yet makes it costly to skip

**Status: open. A decision, not a research problem.**

Even with 1–6 solved, a researcher can publish on PSNR alone in a venue that asks no more. Collapse requires the benchmark to be the **cheapest credible route to a claim**: reproduction so automatic that declining to use it reads as evasion.

Today the repository is **private**. No outsider can obtain the five-gate demonstration, run the suite, or reproduce a single number. The gates work; they are not gettable. A benchmark nobody can run cannot become the thing a field is measured against.

---

## The honest ranking

| # | problem | who can solve it |
|---|---|---|
| **2** | clinical anchor | **a radiologist, prospectively** — nothing else works |
| 1 | trap-proof, validated score | agent + reader study |
| 4 | statistical power | data acquisition |
| 7 | incentive / reach | **a decision by the Director** |
| 3 | per-group scoring | agent — largely done |
| 5 | reproduction criterion | settled |
| 6 | executable gates | agent — closest to closed |

**#2 is the blocker.** #6 is where the agent is strongest and nearly finished. #4 is beyond any agent. **#7 is the cheapest of all of them and is not a research problem at all** — it is a decision about whether the repository becomes public.

The uncomfortable summary: the project has built a good referee for a field that has not yet agreed what winning means. Solving #6 well, as it has, does not substitute for #2.
