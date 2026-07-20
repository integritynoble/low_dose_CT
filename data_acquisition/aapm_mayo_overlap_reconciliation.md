# Reconciling the AAPM 2016 ∩ Mayo LDCT-PD patient overlap

**Goal.** Determine, authoritatively, which AAPM 2016 Low-Dose CT Grand Challenge patients are also
in the Mayo LDCT-and-Projection-Data cohort, so the v0.5 union count and cross-source de-duplication
are exact. The two are the same institution (Mayo) and share the `L###`/`C###` ID scheme, so overlap
is likely; an ID-only spot-check was inconclusive (3 of 11 candidate AAPM IDs matched our Mayo cohort;
candidate list uncertain; LDCT-PD re-anonymizes, so IDs are necessary-not-sufficient evidence).

**Why it matters.** If AAPM patients are also in Mayo, treating them as distinct double-counts the
union (LIDC 1,018 + AAPM 10 + Mayo 199) and risks train/test leakage. The de-dup machinery is already
in place (`canonical_patient_key` = salted hash of the native ID → shared key ⇒ one split, counted
once); this procedure supplies the *facts* it needs.

---

## Step 1 — Obtain the authoritative AAPM 2016 patient manifest
Get the definitive challenge patient IDs (do not rely on the literature's commonly-cited list). In
order of authority:
- **Moen et al. 2021** (LDCT-and-Projection-Data data descriptor, *Med Phys* 48(2):902-911) and the
  **TCIA LDCT-PD page / data dictionary** — these should state how the 299 LDCT-PD subjects relate to
  the 2016 challenge cases (often: the challenge cases are a labelled subset of LDCT-PD).
- **McCollough et al. 2017** (2016 Low-Dose CT Grand Challenge results, *Med Phys* 44(10):e339-e352)
  and the AAPM Grand Challenge documentation — the challenge cohort definition.
- If still ambiguous, the AAPM access materials (see [`aapm_2016_request.md`](aapm_2016_request.md))
  ship a patient list / DUA enumerating the cases.

Record the exact IDs + their source in this file when obtained.

## Step 2 — Cross-reference against the Mayo cohort (by native ID)
We have every public Mayo native PatientID in `~/ldct_resume/mayo_patient_folders.json`:
```python
import json
pf = json.load(open("/home/heyang/ldct_resume/mayo_patient_folders.json"))
mayo = set(pf)
aapm = [...]                      # the authoritative IDs from Step 1
inside  = [p for p in aapm if p in mayo]   # confirmed overlap (shared native ID)
outside = [p for p in aapm if p not in mayo]
print("in Mayo:", inside, "\nnot in Mayo:", outside)
```

## Step 3 — Confirm matches, resolve non-matches
- **Same native ID in both** ⇒ almost certainly the same physical patient (shared Mayo scheme). If
  the AAPM DICOM is in hand, corroborate via acquisition metadata (StudyDate, scanner model, kVp,
  slice count) — these should match the Mayo series for that ID.
- **In the authoritative AAPM list but absent from our Mayo cohort** — either (a) genuinely a
  separate patient (AAPM case not in the public LDCT-PD; e.g. could be a head/restricted or
  challenge-test case), or (b) **re-anonymized** under a different ID in LDCT-PD. Resolve (b) by
  matching DICOM acquisition metadata across the two sources, or accept the documentary mapping from
  Step 1 if it states the correspondence explicitly.

## Step 4 — Encode the resolution
- **Shared native IDs (the common case):** nothing to do — `canonical_patient_key(native_id)` in
  `WS-1_dataset/pipelines/pwm_ldct_prep/adapters/base.py` already gives AAPM-`L143` and Mayo-`L143`
  the same key, so the patient is de-duplicated and assigned one split automatically.
- **Same patient, different native IDs across sources:** add a small **canonical-alias map**
  (native_id → shared canonical key) consulted by `canonical_patient_key` so the two collapse. (This
  alias map does not exist yet; add it only if Step 3 finds differing-ID duplicates.)

## Step 5 — Update the manuscript
- **Union count:** `LIDC (1,018) + AAPM (10) + Mayo (199) − |overlap|`. If AAPM ⊆ Mayo entirely, AAPM
  contributes 0 distinct patients ⇒ union = **1,217** (and "AAPM 2016" becomes a labelled subset of
  Mayo, not a separate count). Update Table 1, the demographics N row, and the abstract/Background.
- **Limitation:** replace the "possible overlap … upper bound" wording (Methods §Splits + Limitations)
  with the reconciled statement once the overlap is known.

## Step 6 — Verify
- Re-run `prep` + `finalize` (or just `write_splits`) and confirm each overlapping physical patient
  appears **once** in `splits/*.txt` and in a single split (the de-dup test `tests/test_dedup.py`
  covers the mechanism).
- Confirm the union total in the manuscript matches the de-duplicated `splits/*.txt` count.

---

## Decision-tree summary
| Step-1/3 finding | Resolution | Manuscript |
|---|---|---|
| AAPM ⊆ Mayo (all 10 in LDCT-PD, shared IDs) | auto de-dup (shared canonical key); no code change | union = 1,217; AAPM = labelled subset |
| Partial overlap (k of 10 shared) | auto de-dup the k; keep 10−k as distinct | union = 1,227 − k |
| Same patients, different IDs | add canonical-alias map | subtract confirmed dups |
| Disjoint (no overlap) | none | union = 1,227 as written |
