# PWM-PET-IQ 1.0 — embodied acquisition authorization & raw-data hosting

> **Status: v0.1 (2026-08-21)** · P1-2 · Maps to low-dose-ct.md *embodied rules*
> (grant / irreversible act) and WS-2 `theory/proofs/twin_validity_domain.md`
> (the PET thinning domain is empirically verified by this acquisition).
>
> This file must be **read and signed before any phantom scan begins** (gates
> SUBMISSION_CHECKLIST §2 Phase C). It names the act, the grant that authorizes
> it, and the raw-data hosting lineage that turns an irreversible physical
> acquisition into a verifiable deposit.

## 1. The act, named

This acquisition is **"PWM-PET-IQ 1.0 phantom acquisition: one NEMA NU-2 IQ
phantom fill, full-count reference + decayed reduced-activity series at
`r ∈ {1.0, 0.50, 0.25, 0.10}`, on the designated scanner, with the count-level
plan locked by the design freeze (SUBMISSION_CHECKLIST Phase A)".**

The act is **irreversible in two senses**:

1. **Physical irreversibility**: a single phantom fill yields the decayed
   sequence exactly once; missed decay timepoints cannot be re-acquired from the
   same fill, and a refill returns to the Phase A count-level plan (new fill
   activity, new decay schedule).
2. **Deposit irreversibility**: once the SHA-256 content manifest is minted and
   the PhysioNet DOI is assigned, the released records define the dataset;
   MAJOR.MINOR.PATCH semantics govern later corrections, but the release content
   hash is fixed.

Per the embodied-rule discipline, an irreversible act is performed **only under a
named grant**.

## 2. The grant

- **Grantor**: the imaging-site PI / radiation-safety office (named in the site
  agreement) and the PWM Protocol Foundation data-deposit owner.
- **Granted act**: exactly the act named in §1 — the phantom fill, the reference
  scan, and the sequential decayed acquisitions on the booked scanner window, at
  the locked count levels, with the radiation-safety authorization number
  recorded in the manuscript (`\todo{radiation-safety authorization no.}`).
- **Grant scope limits**: the grant covers *this* fill and *this* decay sequence
  only. Any change to the count-level plan, the scanner, the phantom fill
  contents, or the addition of further acquisitions requires a **new grant
  amendment** recorded in this file.
- **No human/animal subjects**: phantom-only, no PHI, no IRB; the grant is
  radiation-safety + site-access authorization, not ethics approval.
- **Signature record**: [PI name] / [date] / [radiation-safety no.]. (Fill at
  grant time; placeholder until the site partnership is signed.)

## 3. Raw-data hosting lineage

The raw acquisition records are handled as **hosted-by-default** (embodied rule):
from the moment of acquisition they must never exist only on a scanner disk.

| Stage | Location | Action |
|---|---|---|
| C0. Acquisition | Scanner + local secured scratch storage | Raw list-mode / DICOM + `metadata.json` staged to secured scratch immediately post-scan |
| C1. Working copy | `WS-2b_pet_phantom/pipelines/` container + analysis scratch | Thinning `seed_recipe.json`, recon, ROI extraction run here; **raw files never leave the hosting lineage** |
| C2. Deposit staging | PhysioNet submission staging | Full records (list-mode where license permits, else sinograms + seeds) + `ground_truth.json` + `manifest.sha256` |
| C3. Public deposit | PhysioNet DOI + Zenodo mirror | Both records public at submission (zero embargo; phantom has no DUA) |

- **Backup rule**: two independent copies exist before any thinning/recon
  processing mutates working copies; the raw acquisition files are
  **read-only** after C0 (releases are reproduced from them, never by editing
  them).
- **Provenance rule**: every released artifact resolves to a raw C0 record via
  the committed pipeline; no released number is hand-transcribed from a scanner
  console.
- **Access control**: the C0 scratch is restricted to the grantor-named team;
  access is revoked at grant expiry.

## 4. What is deliberately NOT in this file

- Not a patient-consent or IRB protocol (no human subjects).
- Not the experimental design (that is `SUBMISSION_CHECKLIST.md` Phase A + this
  repository's `analysis/task_spec.json`).
- Not the count-level / physics decisions (those are in
  `analysis/TASK_DEFINITION.md` §Low-activity-to-dose mapping and the WS-2 PET
  `T_r` spec).

## 5. Solved-when

- [ ] §2 signature block filled before Phase C scanning begins.
- [ ] C0 raw records staged to secured scratch with two copies, verified by
      hash, before any processing.
- [ ] Manuscript §Ethics cites this file and the radiation-safety authorization
      number is recorded.
