# Review and next steps — Heyang, 25 September 2026

This page reviews the four commits on `heyang` since the 22 September
assignment (`21fd395`, `b0686eb`, `3fbf5bf`, `716cd96`) and sets the next work.
It takes priority over the [22 September page](HEYANG_NEXT_2026-09-22.md). The
[20 September backlog](HEYANG_NEXT_2026-09-20.md) tasks 2, 5a and 5b stay open
and blocked on owner inputs, as before.

`heyang` (`716cd96`) is four commits ahead of `main` (`01e7672`) and zero
behind. **It is not merged.** It merges after task 1 below is closed.

## What was checked, and how

Re-run on the Linux workstation against a clean checkout of `origin/heyang` at
`716cd96`, not read off your report. Python 3.11, pytest 9.1.1, NumPy 2.4.6.

| Check | Your record | Re-run result |
|---|---|---|
| `WS-4_leaderboard` scoring suite | 312 passed / 10 skipped | 312 passed / 10 skipped — exact match |
| `python Heyang-paper/make_tables.py --check` | passes | `all tables current`, exit 0 |
| `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check` | passes | `overall: PASS`, committed verdict matches, exit 0 |
| `COMPLETION_CHECKLIST.md` §7 at `21fd395` | 9/9 reproduce | 9/9 SHA-256 and blob ids reproduce at `21fd395` |
| §7 at the branch head (`3fbf5bf` / `716cd96`) | — | 6/9 — `manuscript.tex`, `manuscript.pdf`, `CLAIM_EVIDENCE.md` changed in `3fbf5bf` and were not re-hashed |
| Evidence links in the reply index and `CLAIM_EVIDENCE.md` | all repository-relative | 3 do not resolve (task 3 below) |
| `leaderboard.py` `Set` import; `verifier.py` unused `missing` | fixed | both fixed |

Tasks 2 and 4 of the 22 September page are substantially done and well
executed: the LF / `git show HEAD:<file> | sha256sum` convention is the right
one, and the evidence documents are now in the repository with no tokens or
credentials in them. Task 1 is not done — see below. It is the only thing
holding the merge.

## What to do next, in order

### 1. The paper now describes a recomputation that did not produce its results — highest priority

`3fbf5bf` rewrote the abstract (L34-37), Methods (L108-112, L121-125) and
`tab:env` (L127-157) so that **the recomputation is the 23/24 September Linux (WSL2) run**.
But every result the paper reports still comes from the **earlier Windows
recomputation**:

- `tables/agreement.tex` is byte-identical to `21fd395`. It reports, at the
  declared absolute $10^{-6}$ criterion, 25 / 45 / 45 differing values for
  CTformer / RED-CNN / CoreDiff, RED-CNN worst relative difference
  $6.36\times10^{-5}$.
- The Linux comparison you committed
  (`heyang/evidence/linux_vs_windows_full764_comparison.json`) has **RED-CNN
  bit-identical** (max abs diff 0.0 on all five metrics), and it was never
  evaluated at the $10^{-6}$ absolute criterion at all — only at relative
  $10^{-4}$.
- The failed-criterion count, the deterministic-kernel rerun (route (a)) and
  the tolerance ladder all come from the Windows side.

Your own ledger says this (`CLAIM_EVIDENCE.md` L184, limitation ①: "abstract
Results 的失败计数不归属 Linux 复算侧"), but the manuscript does not. As
committed, a reader is told the Linux run failed the $10^{-6}$ criterion and was
then investigated, and neither is true of the Linux run.

Two further defects in the same edit:

- The abstract says "platform-specific CUDA/cuDNN/**driver** builds". The
  driver is the same 591.86 on both sides — `tab:env` and your
  `env_diff_record` §2 ("与 Windows 共享") both say so. Only the OS and the
  cuDNN / wheel packaging differ; PyTorch is the same 2.3.0+cu121.
- The comparison JSON does not name its baseline. "linux_vs_windows" could
  mean the original reference results or the Windows recomputation, and the two
  differ (that difference is the paper). Record which file set, with hashes.

**The owner decision is not recorded clearly.** The 23 September reply index
defined option A as *rewrite the text to drop the cross-environment tension*
and option B as *keep the cross-environment narrative*. The 25 September entry
says "owner 拍板方案 A" but implements the cross-environment narrative, and
`env_diff_record` calls that same route "方案 B". The owner is confirming which
was meant. **Do not start the rewrite below until the owner's choice is
written into the reply index in the owner's own words (quote the message, with
its date and channel).**

Then resolve it one of two ways. The attribution defect must be fixed either
way.

- **If the Linux run is the paper's recomputation (cross-environment kept):**
  every reported number must come from Linux vs the *reference* results. Rerun
  `recompare_per_metric.py` (or its equivalent) for the Linux outputs against
  the reference at the declared absolute $10^{-6}$ criterion, regenerate
  `agreement.tex` from that, and rewrite the Results, the ladder section and the
  conclusion to whatever those numbers show — including the possibility that
  the original criterion now passes for some or all methods, which changes the
  paper's argument. The Linux per-model outputs (`*_det_full764.json`) and logs
  move into the repository (closes U10); a paper cannot rest its results on
  files that exist only in `~/r6_recalc_linux/`.
- **If the Windows recomputation stays the paper's recomputation:** restore the
  Methods and `tab:env` to the Windows recomputation record, and state what is
  known — two separate runs on the same recorded stack, residual offset
  unexplained, attribution to an environment difference UNRESOLVED (the
  22 September wording). The Linux run may then be added as a clearly labelled
  **additional** cross-OS check, with its own numbers and its own criterion
  (relative $10^{-4}$, with baseline named), never as the source of the
  reported results.

Either way: drop "driver" from the list of differing builds; add the decision,
its quoted source and its basis to `CLAIM_EVIDENCE.md` §8; mark in §7 which of
C1 / C4 / C10 / C12 changed.

**Done when:** every number in the manuscript is attributable to the run the
Methods says produced it, the environment differences named in the abstract
match `tab:env`, and the owner's decision is quoted in the reply index.

### 2. Re-hash §7 at the commit that closes task 1

§7 verifies at `21fd395` but not at the branch head, because `3fbf5bf` changed
three of its nine files. After task 1:

- Recompute all nine entries with the command already written in §7.
- Replace "基线 = 本清单所在提交" with the literal commit id the hashes were
  measured at. A checklist cannot name its own commit, so hash at the task-1
  commit and name that commit in the next one.
- Update §9 line references: after `3fbf5bf` the TODOs sit at L22, L296, L312,
  L317 and L320, not L289 / L305 / L310 / L313.

**Done when:** `git show <named commit>:<file> | sha256sum` reproduces all nine
entries.

### 3. Fix three broken evidence links and one watermark

Links are resolved relative to the file that contains them:

| File | Link as written | Resolves to | Should be |
|---|---|---|---|
| `heyang/HEYANG_REPLY_2026-09-20.md` | `Heyang-paper/CLAIM_EVIDENCE.md` | `heyang/Heyang-paper/…` (missing) | `../Heyang-paper/CLAIM_EVIDENCE.md` |
| `heyang/HEYANG_REPLY_2026-09-20.md` | `Heyang-paper/COMPLETION_CHECKLIST.md` | `heyang/Heyang-paper/…` (missing) | `../Heyang-paper/COMPLETION_CHECKLIST.md` |
| `Heyang-paper/CLAIM_EVIDENCE.md` | `evidence/ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md` | `Heyang-paper/evidence/…` (missing) | `../heyang/evidence/ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md` |

The `ENV_RECON` link is the one the ledger leans on for *what was changed in the
manuscript and why*; it is the most important of the three. Check every other
relative link in both files the same way before committing.

`heyang/evidence/env_diff_record_Linux_recalc_2026-09-25.md` still carries the
AIGC frontmatter block and the "内容由AI生成，仅供参考" footer. Strip them, as
you did for the 21 September documents.

**Done when:** a script that resolves every relative link in the reply index and
`CLAIM_EVIDENCE.md` reports none missing, and `grep -rlE 'AIGC|ReservedCode|内容由AI生成' heyang Heyang-paper`
returns nothing.

### 4. Put the patient-mapping answer in the code

The 22 September page asked for the `check_patient_mapping_binding` question to
be "answered either way **in the code**". Your answer (UNVERIFIED for an
undeclared patient-level bootstrap is intentional and conservative) is good,
but it is only in the reply index. Add it to the docstring in
`WS-4_leaderboard/scoring/binding.py:368`, in one or two sentences, so the next
reader of the code sees it.

Optional while there: `pyflakes` also reports `hashlib` unused in
`leaderboard.py:25` and `TASK_LABEL` unused in `verifier.py:34`.

**Done when:** the docstring states the intended state for a result that does
not declare patient-level bootstrap.

### 5. Then the 20 September backlog

Tasks 2 (native Windows CT + agent receipt), 5a (BANDER-2) and 5b (off-machine
copy) stay blocked on the owner inputs you listed. Do not re-implement around
those blocks.

## Is the paper done?

No. After the tasks above it is still blocked on owner inputs, not on you: five
`\todo{}` remain (author list / affiliations / ORCIDs / corresponding author at
L22, third environment at L296, artifact release at L312, CRediT at L317,
declarations at L320), and the eight items in `COMPLETION_CHECKLIST.md` §9 are
unanswered. Keep that list current; do not fill any of those fields yourself.

## Reporting rule

Report each task as IN PROGRESS, DONE or BLOCKED with a commit or artifact, the
next action and an ETA, in the existing reply index — do not open a competing
status file. Keep technical verification, scientific support and evidence-copy
receipts separate. If this review's reading of the evidence is wrong, cite the
artifact and say so; a correction with a source is worth more than a completed
task.
