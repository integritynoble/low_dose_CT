---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_cd7108249d5511f1a54f525400f8a581
    ReservedCode1: kjg0P/hf7+0Bt+reNjxP1pQw6aLqvCkx6YzA8uDQj3lgnyephjv3svOXl+42ktx38ux9MHndFsOjHv/hE/otOmSJHI+OJ2KsYJK8aot3NgeNHWeXGYOUJWz0R+N4OE9amHfHKRnh6AGRfCLV7xXpBzQ435Hec8zKrS9o1nmogYojgZLyXzYaPyn+qxo=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_cd7108249d5511f1a54f525400f8a581
    ReservedCode2: kjg0P/hf7+0Bt+reNjxP1pQw6aLqvCkx6YzA8uDQj3lgnyephjv3svOXl+42ktx38ux9MHndFsOjHv/hE/otOmSJHI+OJ2KsYJK8aot3NgeNHWeXGYOUJWz0R+N4OE9amHfHKRnh6AGRfCLV7xXpBzQ435Hec8zKrS9o1nmogYojgZLyXzYaPyn+qxo=
---

# AAPM 2016 R2 Pilot — FD+QD Geometric Pairing Validation

Generated: 2026-08-21 19:36:43

Method: `WS-1_dataset/baselines/src/pwm_ldct_baselines/dicom_pairing.py` (pair by ImagePositionPatient projected onto series normal; target Pearson > 0.99; tol 0.5 mm).

Overall: **10/10 patients passed** (ALL PASSED)

| Patient | FD slices | QD slices | Paired | Unpaired FD | Unpaired QD | Pearson r | Violations | Passed | Reason |
|---|---|---|---|---|---|---|---|---|---|
| L067 | 560 | 560 | 560 | 0 | 0 | 1.0 | 0 | YES | OK |
| L096 | 823 | 823 | 823 | 0 | 0 | 1.0 | 0 | YES | OK |
| L109 | 318 | 318 | 318 | 0 | 0 | 1.0 | 0 | YES | OK |
| L143 | 585 | 585 | 585 | 0 | 0 | 1.0 | 0 | YES | OK |
| L192 | 600 | 600 | 600 | 0 | 0 | 1.0 | 0 | YES | OK |
| L286 | 525 | 525 | 525 | 0 | 0 | 1.0 | 0 | YES | OK |
| L291 | 856 | 856 | 856 | 0 | 0 | 1.0 | 0 | YES | OK |
| L310 | 533 | 533 | 533 | 0 | 0 | 1.0 | 0 | YES | OK |
| L333 | 610 | 610 | 610 | 0 | 0 | 1.0 | 0 | YES | OK |
| L506 | 526 | 526 | 526 | 0 | 0 | 1.0 | 0 | YES | OK |

## Notes

- Data source: AAPM 2016 Low-Dose CT Grand Challenge, 10 training patients, 1mm B30 kernel, staged at `E:\AAPM_staged\`.
- Pairing is geometric only (never file-name / InstanceNumber order); unpaired counts should be 0 and violations 0 for a clean pass.
- Full JSON: `aapm_pairing_validation.json` (same directory).
*（内容由AI生成，仅供参考）*
