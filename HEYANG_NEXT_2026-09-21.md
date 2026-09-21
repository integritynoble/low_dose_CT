# Review and next steps — Heyang, 21 September 2026

**Immediate assignment: deliver the corrected Heyang-paper package for author
review as soon as possible.** This page narrows the next work session into
concrete deliverables. It takes priority over the broader
[20 September backlog](HEYANG_NEXT_2026-09-20.md); that backlog remains open.

## What the latest check found

Fresh fetch on 21 September found:

| Source | Exact head |
|---|---|
| main | `efafdb29d85398f7e1591d511b4ac2f9d570e0fe` |
| heyang | `d515825f577c155f03ed91977ac364f8765dbc7c` |
| bander/control-matrix | `a42ad2703594b4c3a4cd6a02396d1ae444f64dac` |

`heyang` has **zero commits unique to it and is ten commits behind main**.
Your published work is already merged through PR #26, and the detailed new
assignment is on main through PR #27. The remote heyang branch does not yet
contain that handoff or the subsequent integration fixes. No
`HEYANG_REPLY_2026-09-20.md` was found on the checked branch. This describes
remote evidence only; it does not imply you have done no local work.

Open PRs #20 (WS-2 prose) and #1/#2 (dependencies) were checked; none is a new
Heyang paper delivery. The earlier [integration review](INTEGRATION_STATUS_2026-09-20.md)
records verification and its limits. No new tests or image experiments were
run for this status-only check, and yesterday's test counts are not new results.

## What to do next, in order

### 1. Sync and return your status first

Preserve any uncommitted work, fetch origin and merge `origin/main` into your
working branch without rewriting history. Read this page and the 20 September
assignment. If local changes already address an item, publish/link those changes
instead of implementing it again.

Update **`HEYANG_REPLY_2026-09-20.md`**, keeping the same reply index rather than
creating another competing status file. Add a dated 21 September section with:

- Your current CT and agent heads and any local work not yet pushed.
- Your expected delivery date/time for the paper package.
- A short list of missing owner inputs, each with the exact field it blocks.

**Done when:** the reply is committed and visible on your branch. An ETA is yours
to state; this handoff does not claim you have acknowledged or agreed to one.

### 2. New concrete deliverable — a paper claim-to-evidence ledger

Create `Heyang-paper/CLAIM_EVIDENCE.md` as a compact review table. For each key
abstract/result/conclusion claim, name the manuscript location, supporting
artifact and field, relevant command, permitted interpretation and limitation.
Cover at least:

1. The original absolute-criterion failure and the preserved failed results.
2. What the same-side deterministic rerun measured; it does not uniquely
   identify the cause of the reference mismatch.
3. The tested tolerance ladder; do not generalize it to “no absolute tolerance
   can work.”
4. The amended per-metric PASS, explicitly dated and retrospective.
5. The comparison count, derived using methods, seeds, doses and metrics rather
   than the inconsistent current TODO multiplication.
6. Both computing environments, with log sources for known fields and explicit
   unknowns for missing reference-machine details.

Use committed artifacts or recoverable source logs. Distinguish recorded facts
from operator recollection. Keep original failures and later amendments; do not
change an artifact or threshold to fit the prose.

**Done when:** a reviewer can trace every central claim to its evidence and see
which conclusions the evidence cannot support. Missing evidence is marked
UNRESOLVED, not inferred. The ledger supports writing; it must not become a
reason to postpone correcting the manuscript.

### 3. Correct the paper and regenerate one matching package

Apply the ledger to `manuscript.tex` and README: remove unsupported causal and
universal-tolerance claims, label the tolerance amendment retrospective, and use
“original declared criterion” unless timestamped preregistration evidence exists.
Add the environment table, retain honest limitations, and reconcile the counts
through `make_tables.py` where needed. Complete all author-independent TODOs.

From the repository root, run and record:

```text
python Heyang-paper/make_tables.py
python Heyang-paper/make_tables.py --check
python -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check
```

Build `Heyang-paper/manuscript.pdf` with your available TeX toolchain. Inspect
layout, citations, references and generated tables. Commit the source, generated
tables, bibliography, matching PDF and evidence ledger together. Record the
actual tool versions, commands and results. A PDF build does not validate the
scientific interpretation, and a log comparison is not fresh inference.

**Done when:** one reviewable branch contains consistent text/tables/PDF and the
ledger, with no unresolved technical/writing TODO silently passed off as an
owner decision. Missing author metadata can be listed explicitly for final
approval; finish the rest now.

### 4. Return a short completion receipt and owner decision list

Create `Heyang-paper/COMPLETION_CHECKLIST.md` with source commit, artifact hashes,
verification/build results, remaining TODOs and their owners. Request author
order, affiliations, ORCIDs, corresponding author, CRediT and declarations in one
compact list. Prepare accurate code/data availability language using existing
rights; code availability does not grant image or checkpoint redistribution.

Link the package and checklist from the existing reply index and open a paper
PR against main. If unable to open a PR, push the branch and provide its head.

**Done when:** the owner can review the paper immediately and see the precise
remaining decisions. Do not submit to a journal until the authors approve it.

## After the paper delivery

Resume tasks 2–5 in the [20 September list](HEYANG_NEXT_2026-09-20.md): native
Windows CT + agent receipt, publication-state reporting, evaluator-bound
provenance, and separate BANDER/backup evidence. Do not duplicate the already
merged agent fixes. New UI features, a third-environment GPU study and broader
framework work must not displace the paper delivery.

## Reporting rule

Report each task as IN PROGRESS, DONE or BLOCKED with a commit/artifact, next
action and ETA. If the source evidence contradicts an instruction, cite it and
propose the correction. Keep technical verification, scientific support,
data-copy receipts and external adoption separate. This is a repository
assignment; no personal-message delivery or acknowledgement is claimed.
