# PWM-PET-IQ 1.0 — paper draft

Nature **Scientific Data** Data Descriptor for the NEMA NU-2 image-quality phantom
PET dataset (paired full- and reduced-count acquisitions for reduced-activity
reconstruction benchmarking).

This is the **Data Descriptor sibling** of the WS-2 signal-equivalence framework
paper. WS-2 (`../../WS-2_framework/`) contributes a *method* and targets Nature
Methods; Scientific Data does not publish methods, so the *dataset* is carved out
here as its own paper, and the `pwm_dose_equivalence` framework appears only as a
Usage-Notes consumer.

## Status: SKELETON

Every measurement is a wired `\todo{}` anchor. **No number is asserted from a
committed artifact yet** — the dataset must be acquired and deposited before
submission. See `../SUBMISSION_CHECKLIST.md`, which maps each `\todo{}` to the
acquisition / analysis / deposit step that fills it.

**Scope (P1-1):** this descriptor validates a **dose-reduction (digital-twin)
model** via phantom data — it is *not* a CT detectability benchmark and makes no
detectability claim (no AUC / channelized-observer / reader endpoint). See the
"Scope and positioning" section in `manuscript.tex` and
`../analysis/TASK_DEFINITION.md` / `../analysis/task_spec.json` for the locked
task and observer plan.

**Embodied acquisition (P1-2):** before any scanning, `../ACQUISITION_AUTHORIZATION.md`
must be read and signed — it names the irreversible act, the grant, and the
raw-data hosting lineage (SUBMISSION_CHECKLIST §1b).

## Build

```
pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript
```

## Why this can be a Scientific Data paper (and WS-2 cannot)

- The **central object is a deposited, reusable dataset** (phantom PET series),
  not a method.
- **Physical ground truth** (known sphere sizes / fill concentrations) means every
  Technical-Validation endpoint is objective — no reader panel.
- **No PHI** (phantom) → clean open release, no DUA, no IRB.
- The paired **decayed-vs-thinned** design gives a genuine, measurable validation
  question (does list-mode thinning reproduce true reduced activity?).
