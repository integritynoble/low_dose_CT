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

**The owner decision was labelled inconsistently.** The 23 September reply index
defined option A as *rewrite the text to drop the cross-environment tension*
and option B as *keep the cross-environment narrative*. The 25 September entry
says "owner 拍板方案 A" but implements the cross-environment narrative, and
`env_diff_record` calls that same route "方案 B".

**Owner decision, 25 September 2026 (Claude Code session on the Linux
workstation, relayed in this page):** "keep the cross-environment framing".
The Linux run is the paper's recomputation. Copy this quote, with its date and
source, into the reply index and `CLAIM_EVIDENCE.md` §8 as the basis for the
task-1 row, and refer to it as *cross-environment kept*, not by letter.

That makes the attribution defect a results task, not a wording task:

- Every reported number must come from Linux vs the *reference* results. Rerun
  `recompare_per_metric.py` (or its equivalent) for the Linux outputs against
  the reference at the declared absolute $10^{-6}$ criterion, regenerate
  `agreement.tex` from that, and rewrite the Results, the ladder section and
  the conclusion to whatever those numbers show — including the possibility
  that the original criterion now passes for some or all methods, which
  changes the paper's argument. Do not carry a Windows-side number into a
  sentence that the Methods attribute to the Linux run.
- If the Linux run was compared only against the Windows *recomputation*, not
  the reference, the committed 375/375 PASS is not the paper's comparison; say
  which it was and redo it against the reference.
- The Linux per-model outputs (`*_det_full764.json`) and logs move into the
  repository (closes U10); a paper cannot rest its results on files that exist
  only in `~/r6_recalc_linux/`.
- The Windows recomputation, its deterministic-kernel rerun (route (a)) and the
  tolerance ladder are real, preserved evidence. Keep them in the repository
  and the ledger. If the paper still cites them, label them as the earlier
  same-OS run in the text; do not delete them and do not present them as the
  Linux run.
- If the Linux numbers remove the failure the paper is built around, stop after
  the re-comparison and report the numbers before rewriting; the owner decides
  how the argument changes.

Also: drop "driver" from the list of differing builds; add the decision,
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

### 5. Prepare the third environment (owner decision: yes)

**Owner decision, 25 September 2026 (relayed in this page):** add a third
environment, run on the owner's native-Linux RTX 5090 workstation. Quote it in
the reply index and `CLAIM_EVIDENCE.md` §8.

Why this machine: the Linux run shares the host, the two RTX 4090s, driver
591.86 and PyTorch 2.3.0+cu121 with the Windows side. A reviewer can fairly
call that one machine booted two ways. The 5090 workstation differs on every
axis the abstract names. Recorded 2026-09-25: Ubuntu 26.04 LTS (native, not
WSL), RTX 5090 (Blackwell), driver 595.71.05, CUDA 13.2 driver runtime.
PyTorch 2.3.0 has no kernels for this GPU generation, so the framework version
necessarily differs as well.

**Order:** start this only after task 1's re-comparison is reported. If task 1
stops on the owner's call, this waits with it.

Your part is to make the run executable by someone other than you, not to run
it. The run happens on the owner's workstation.

- **Run book** — `heyang/evidence/THIRD_ENV_RUNBOOK_2026-09-25.md`: the exact
  commands from a clean checkout at a named commit to the five
  `*_det_full764.json` outputs, the expected runtime per model (the Linux run
  took about 30 h end to end), and the comparison command against the
  **reference** results at both the declared absolute $10^{-6}$ and relative
  $10^{-4}$ criteria, with the reference files named by hash.
- **Environment** — pin the newest PyTorch with Blackwell (sm_120) support you
  can justify, and list every code change the old pipeline needs to run on it.
  Make the changes on a branch, with tests, and do not change any metric
  definition. A change that alters a number is a finding; report it rather
  than tuning it away.
- **Data** — LIDC-IDRI is public on TCIA, so the 364 input files are downloaded
  on the workstation, not copied: give the download manifest and the check
  against `hashes/data_hashes.txt`. Confirm the licence of the collection
  version the manifest points at.
- **Checkpoints** — the five checkpoints are the only files that must move.
  Write down who trained them, on what data, and under which baseline-code
  licence, and state whether the use agreement permits the transfer. The owner
  authorises the transfer; do not send them before that.
- **Operator** — the run should be done by someone other than you (a third
  operator strengthens the independence claim). Say what they need from you.

**Done when:** the run book, environment branch and checkpoint-provenance note
are committed, and the owner has what is needed to authorise the transfer and
start the run. The paper's Limitations `\todo` (L296) is then replaced with the
planned third environment; its results go in only after the run.

### 6. Draft the availability statement and release package (owner decision: curated release)

**Owner decision, 25 September 2026 (relayed in this page):** publish a
curated release with a DOI, not the whole repository; do not redistribute
images; release checkpoints only if the rights are confirmed, otherwise hashes
only. Quote it in the reply index and `CLAIM_EVIDENCE.md` §8.

The repository itself stays private. It carries internal task pages, working
notes and evidence documents that are not publication material.

- **Package manifest** — `Heyang-paper/RELEASE_MANIFEST.md`: every file that
  goes into the release, why, and its SHA-256. At minimum the evaluation code,
  the re-derivation script (`recompare_per_metric.py`), the table generator
  (`make_tables.py`), the per-slice result JSONs and comparison JSONs the
  paper's numbers come from, and the hash manifests (`data_hashes.txt`,
  `aapm_hashes.txt`, `ckpt_hashes.txt`). Nothing with PHI, credentials, local
  paths, AIGC watermarks or share tokens.
- **Rights check** for each item: code licence (there is no top-level
  licence; `WS-1_dataset/baselines`, `WS-1_dataset/pwm_ldct_loader` and
  `WS-2_framework/pwm_dose_equivalence` carry their own `LICENSE` files — record
  which licence covers each released file, and flag any file no licence covers;
  choosing one is the owner's call),
  dataset terms for LIDC-IDRI and the AAPM/Mayo data, and the checkpoint
  question from task 5. Anything uncertain is listed as uncertain, not
  assumed.
- **Statement text** — replace the `\todo` at L312 with a draft built on
  `COMPLETION_CHECKLIST.md` §10: code and derived results at a DOI (leave the
  DOI as a marked placeholder), images available from TCIA / AAPM under their
  own terms and verifiable against the listed hashes, checkpoints by hash
  unless released. Medical Physics (the primary target) requires this
  statement.
- **Do not** create the Zenodo record, a public repository or a release tag.
  The owner does that after reviewing the manifest.

**Done when:** the manifest, the rights table and the drafted statement are
committed, and every file in the manifest exists in the repository and
reproduces its listed hash.

### 7. Then the 20 September backlog

Tasks 2 (native Windows CT + agent receipt), 5a (BANDER-2) and 5b (off-machine
copy) stay blocked on the owner inputs you listed. Do not re-implement around
those blocks.

## Is the paper done?

No. The third-environment and release decisions are now made (tasks 5 and 6).
After the tasks above the paper is still blocked on owner inputs, not on you:
the author list / affiliations / ORCIDs / corresponding author (L22), the CRediT
statement (L317) and per-author declarations (L320), plus the final Zenodo
record and code licence. Keep `COMPLETION_CHECKLIST.md` §9 current — mark items
7 (third environment) and 8 (artifact release) as decided on 25 September — and
do not fill the owner fields yourself.

## Reporting rule

Report each task as IN PROGRESS, DONE or BLOCKED with a commit or artifact, the
next action and an ETA, in the existing reply index — do not open a competing
status file. Keep technical verification, scientific support and evidence-copy
receipts separate. If this review's reading of the evidence is wrong, cite the
artifact and say so; a correction with a source is worth more than a completed
task.
