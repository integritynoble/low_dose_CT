# Review and next steps — Heyang, 22 September 2026

The 21 September task book is **merged**. `heyang` (`0afa8a5`) went into `main`
as merge commit `c765d1b`; PR #30 closes with it. This page is the review of
that delivery and the next assignment. It takes priority over the
[20 September backlog](HEYANG_NEXT_2026-09-20.md), whose tasks 2, 5a and 5b
remain open and blocked on owner inputs.

## What was checked, and how

Every claim below was re-run on the Linux workstation against the merged tree,
not read off your report. Python 3.11.13, pytest 9.1.1, NumPy 2.4.6.

| Check | Your record | Re-run result |
|---|---|---|
| `WS-4_leaderboard` scoring suite | 312 passed / 10 skipped | 312 passed / 10 skipped — exact match |
| `python Heyang-paper/make_tables.py` | exit 0 | exit 0, regenerated files byte-identical to the committed ones |
| `python Heyang-paper/make_tables.py --check` | `all tables current`, exit 0 | same |
| `python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check` | 5 methods PASS, outside declared 0, overall PASS, exit 0 | same, including the worst-case values you quote |
| `Heyang-paper/manuscript.pdf` | 7 pages, 198,198 B, SHA-256 `6096826A…` | matches exactly |
| `CLAIM_EVIDENCE.md` manuscript line refs | "0 stale refs" | spot-checked L22, L34-50, L88-89, L105-120, L190-191, L213-217, L223-230, L244-247, L271-277, L287-290, L296-313 — all accurate |

The ledger is the strongest part of the delivery: the R / M / UNRESOLVED
typing is used honestly, §2 states plainly what the same-side rerun does *not*
establish, §3 refuses to generalise the ladder, and §8 lists the nine
UNRESOLVED items instead of inferring them. `binding.py` and the publication
states are conservative in the right direction — UNVERIFIED rather than
certified whenever a runtime fact is unavailable, referee evidence required
before anything reads as published, and the save-time recompute that replaces a
hand-edited snapshot is the right shape for a direct-save bypass.

Three defects survived. None of them was a reason to hold the merge; all three
are yours to close now.

## What to do next, in order

### 1. The environment table contradicts the paper's central claim — highest priority

`manuscript.tex` now says both of these:

- Abstract (L35-37): the recomputation ran "in a separate environment
  **differing in operating system, CUDA build, and deep-learning framework
  version**"; L118-120 rests the paper's point on "a different library stack";
  the title (L20), L216-217 and L300 call the residual a
  "cross-environment offset".
- The new Table `tab:env` (L123-149) and L110-117: the reference environment
  *is* the local run environment, and **one** project-runtime record covers
  both — same OS, same 2× RTX 4090, same driver 591.86, same Python 3.12.10,
  same PyTorch 2.3.0+cu121, same NumPy 1.26.4.

As committed, the paper asserts an environment difference that no artifact in
the repository records, and your own ledger marks the reference side's
independent record UNRESOLVED (U1). The environment table did not create the
problem — the owner's "reference = local run environment" ruling did — but
inserting the table put the contradiction on the same page as the claim.

Resolve it in the text, not by weakening the table:

- If a real difference exists (the author's original run used a different OS /
  CUDA / framework build), the abstract's three named axes need a source. The
  only candidate on record is the *nominal* container tag
  `pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime`, which your ledger §6.2 types
  as M, not R. A nominal tag cannot support "differing in operating system".
- If no such record can be produced, the abstract, L118-120, L216-217 and L300
  must say what is actually known: the two sides are separate operator /
  checkout / venv / output-tree runs whose recorded stacks are identical, the
  residual is an **unexplained offset between two runs**, and its attribution
  to a cross-environment difference is UNRESOLVED. The title claim
  "cross-environment reproduction" has to be reconsidered under that reading.

Add a row to `CLAIM_EVIDENCE.md` §8 for whichever way it resolves, and state in
§7 which of C1/C4/C10/C12 the change touches.

**Done when:** no sentence in the manuscript asserts an environment difference
the repository cannot evidence, and the ledger records the decision and its
basis. Do not delete the environment table, and do not restore a
pre-registration framing.

### 2. Make `COMPLETION_CHECKLIST.md` §7 verifiable

The hash table does not verify against the repository. Of nine entries only
`manuscript.pdf` reproduces. All eight text-file hashes were computed over
CRLF working-copy bytes; the committed bytes are LF, so `sha256sum` on a fresh
checkout matches none of them. Six of the eight match after CRLF conversion —
and `CLAIM_EVIDENCE.md` (`E9E971A3…`) and `README.md` (`24D6E7D4…`) match
**neither** form of **any** committed version, so those two were recorded
before the final edit and are stale.

A completion receipt whose hashes a reviewer cannot reproduce is worse than no
hash table. Fix it by recording the bytes git actually stores:

```bash
git rev-parse HEAD
git ls-files -s Heyang-paper | awk '{print $2, $4}'    # blob sha1 as git stores it
# and, for a reviewer with a checkout:
sha256sum Heyang-paper/manuscript.{tex,pdf} Heyang-paper/{README,CLAIM_EVIDENCE,COMPLETION_CHECKLIST}.md \
          Heyang-paper/make_tables.py Heyang-paper/references.bib Heyang-paper/tables/*.tex
```

Record the commit the hashes belong to, state the line-ending convention
explicitly, and say which command reproduces them. If you keep SHA-256, compute
it on Linux-normalised (LF) content or on `git cat-file blob` output, not on the
Windows working copy.

**Done when:** a reviewer on a clean checkout can run one named command and get
every value in §7, and §7 names the commit it was measured at.

### 3. Bring the cited evidence documents into the repository

Six of the seven rows in `heyang/HEYANG_REPLY_2026-09-20.md` cite their evidence
as `C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\…\output\…md` —
`ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21`, `WINDOWS_COMPAT_RECEIPT_2026-09-21`,
`RELEASE_STATUS_VISIBILITY_2026-09-21`, `PROVENANCE_BINDING_2026-09-21`,
`BANDER_DIAG_AUDIT_2026-09-21`, `COPIES_DEPOSIT_RECEIPT_2026-09-21`. None is in
the repository, and none is reachable by anyone but you. `CLAIM_EVIDENCE.md` §4
and §5 lean on the first of them ("ENV_RECON §3 M1/M4/M8-M10/M15/M17/M19") as
the record of *what was changed in the manuscript and why* — which is exactly
the document a reviewer needs and cannot open.

Commit them under `heyang/evidence/` with their dates in the filenames, redact
anything that carries PHI, credentials or share tokens, and replace the local
paths in the reply index with repository-relative links. Where a document
cannot be published, say so in the row and name what it contains; a row whose
evidence is "on my machine" is BLOCKED, not DONE.

**Done when:** every evidence link in the reply index and in `CLAIM_EVIDENCE.md`
resolves inside the repository, or is explicitly marked unpublishable with a
reason.

### 4. Two code cleanups in WS-4

Both are in the merged code and neither is caught by CI (the matrix only lints
`WS-2_framework`):

- `WS-4_leaderboard/scoring/leaderboard.py:667` annotates
  `snap_patient_ids: Set[str]`, but `Set` is not imported from `typing` (the
  line is only harmless because `from __future__ import annotations` stops the
  annotation being evaluated). Add `Set` to the import.
- `WS-4_leaderboard/scoring/verifier.py` — in `board_publication_status`, the
  MISSING_STRATUM branch computes
  `missing = [g for g in strata.get("groups", {}) if g not in ()]` and never
  uses it. Either put the group names in the `detail` string or drop the line.

While you are there: consider whether `check_patient_mapping_binding` returning
UNVERIFIED for every result that simply does not declare patient-level
bootstrap is the state you want. It is safe — nothing is over-certified — but
it means an ordinary slice-level submission can never reach a clean PASS on all
four binding checks. If that is intended, say so in the docstring; if not,
distinguish "not applicable" from "claimed but unbound".

**Done when:** both fixed with a test or a lint run recorded, and the
patient-mapping question answered either way in the code.

### 5. Then resume the 20 September backlog

Tasks 2 (native Windows CT + agent receipt), 5a (BANDER-2) and 5b (off-machine
copy) stay blocked on the owner inputs you listed. Do not re-implement around
those blocks. Task 3 and task 4 are merged and closed.

## Owner inputs — status

Your eight-item list is received. Nothing on it has been answered yet; items 1-4
and 8 (author metadata, availability language, journal target, third
environment, artifact release) are the owner's, and items 5-8 of the earlier
list (reference-environment records, shared core access, BANDER-2
authorisation, OneDrive access) remain open. Item 5 — reference-environment
records — is now the blocking input for task 1 above, and is the one worth
chasing first: if no such record exists, task 1 resolves the other way, and
that is a decision the owner should make explicitly rather than by silence.

## Reporting rule

Report each task as IN PROGRESS, DONE or BLOCKED with a commit or artifact, the
next action and an ETA, in the existing reply index — do not open a competing
status file. Keep technical verification, scientific support and evidence-copy
receipts separate. If this review's reading of the evidence is wrong, cite the
artifact and say so; a correction with a source is worth more than a completed
task.
