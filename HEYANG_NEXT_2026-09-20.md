# Heyang — finish the reproduction paper first (20 September 2026)

**Owner instruction, 20 September:** finish `Heyang-paper/` as soon as possible.
This is your top priority after syncing the integrated branch. It supersedes
execution priorities in the 13/15 September handoffs. Use this repository file
as the assignment channel; no delivery through the previously unconfirmed
`BeiTa9` issue account is assumed. Read this file before starting more WS-4 UI,
new framework work, or additional GPU experiments.

## Immediate deliverable: complete paper for author review

Work in `Heyang-paper/` from current `origin/main`; merge main into your branch
without rewriting history. First return a short acknowledgement with your
expected completion date and the specific information you still need. Proceed
with all unblocked writing now; do not wait for the broader benchmark project.

1. **Close the environment/provenance gap.** Record both reference and rerun OS,
   GPU, driver, CUDA/cuDNN, Python, PyTorch, NumPy, code/checkpoint/data-manifest
   hashes and commands from original logs. Distinguish recorded facts from
   recollection; if reference details cannot be recovered, state that limitation
   in Methods and notify the owner. Do not invent an environment or claim a new
   independent reproduction from a comparison of existing logs.
2. **Correct the central interpretation throughout the abstract, Results,
   Discussion, conclusion and README.** A bit-identical same-side deterministic
   rerun establishes repeatability in that tested configuration; it does not
   uniquely identify the cause of the reference mismatch or rule out all GPU
   kernel effects. The absolute criteria tested failed; this does not prove
   that no absolute tolerance could pass. The per-metric amendment followed
   observation of the mismatch: label it retrospective, preserve the original
   failure, and do not claim independent/prospective tolerance validation.
   Use “original declared criterion” unless timestamped preregistration evidence
   is actually available. A third environment is optional follow-up, not a
   prerequisite for finishing this bounded Technical Note.
3. **Reconcile every number with the artifact.** Check the comparison count
   using all axes (methods, seeds, doses, metrics): the current TODO's written
   multiplication is inconsistent with its per-method label. Extend the table
   generator where necessary; keep the source artifact and tolerances unchanged.
   Run `python3 Heyang-paper/make_tables.py --check` and
   `python3 -B WS-1_dataset/R6_recalc/recompare_per_metric.py --check`.
4. **Close submission metadata with the owner.** Request the author order,
   affiliations, ORCIDs, corresponding author, CRediT and declarations in one
   compact message. Prepare accurate code/data availability text: public code
   does not imply unrestricted image/checkpoint redistribution. The target
   recorded in the repository is Medical Physics, Technical Note; check the
   journal's current instructions when preparing the submission package.
5. **Deliver one consistent package.** Commit manuscript.tex, references.bib,
   generated tables, rebuilt manuscript.pdf, README and a short completion
   checklist with the exact commit, build command and remaining author decisions.
   Remove all resolvable TODOs, check citations/links and PDF layout, and report
   unresolved author-only fields explicitly. Do not submit to a journal until
   the authors approve the final package.

**Done means:** scientifically bounded text, reproducible tables, matching PDF,
complete metadata or a clearly enumerated owner-only blocker list, and a branch
ready for final author review. Software tests alone are not scientific approval.

## After the paper package is delivered

- Run native Windows checks of the integrated scoring/bootstrap code and return
  exact commit, versions, commands, counts and skip reasons. The Linux review
  includes corrected patient replacement sampling and verifier skip reporting;
  do not restore the legacy patient-bootstrap output as valid evidence.
- Continue WS-4 provenance/publication hardening: submitted JSON manifest hashes
  are not independent verification of actual model/data bytes; patient labels
  are not proof of slice-to-patient mapping. Keep the web interface a prototype,
  receipts pending and S3 live execution unresolved until evidence exists.
- BANDER controls, authorized backup/deposit receipts and the dose–task protocol's
  clinical/statistical fields remain open. No new threshold, clinical study,
  license/rights decision or external adoption is approved by this merge.

The 20 September pending-decision list is a historical workstation snapshot:
its A-1/A-2 changes are already committed and pushed as `d515825`. Its draft
semantics and confirmation markers are not automatically ratified by merging.
