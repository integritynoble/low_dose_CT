---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_a4b4eb3eb40a11f1b3c552540024e231
    ReservedCode1: TfSma1ueQPK8TGxE5hV4yUxpXyV6FOnm21njsGJSZBZmy+7Fq5VYJPiJfHayH22aEWam4XurYdLXzOhQlLaef+h4bf08QjwtRnV3K8gzEL/SPlXyCBSaEndwUDJlmNxxStmip7VM1+VzFQX96av55+gpveoFiWbLZhERVqwKcYYJr25xh4+KQ1YmrN4=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_a4b4eb3eb40a11f1b3c552540024e231
    ReservedCode2: TfSma1ueQPK8TGxE5hV4yUxpXyV6FOnm21njsGJSZBZmy+7Fq5VYJPiJfHayH22aEWam4XurYdLXzOhQlLaef+h4bf08QjwtRnV3K8gzEL/SPlXyCBSaEndwUDJlmNxxStmip7VM1+VzFQX96av55+gpveoFiWbLZhERVqwKcYYJr25xh4+KQ1YmrN4=
---

# WS-4 Submission Contract

- **Status:** `draft` — Phase 1 task 1.4 (README). Specifies what a RunBundle must contain, per L2 + L3 specs (`../pwm_integration/l2_spec.md`, `../pwm_integration/l3_spec.md`) and the merged scoring gates already implemented in `scoring/`.
- Date: 2026-09-19
- Repo baseline: `low_dose_CT-heyang` @ `3823498` (no commit / push / rebase)
- Versioned protocol reference: `../PROTOCOL_SKELETON_2026-09-15.md` (draft; frozen version number `[UNRESOLVED]`).
- ⚠️ Where this document conflicts with the L3 spec, **L3 is authoritative**; this contract is the WS-4-side executable transcription.

---

## 1. RunBundle directory contract

A submission is a directory named `<method>-<version>/` (the RunBundle) with this shape:

```
runbundle/
├── method.json                          # REQUIRED: name, version, paper, license
├── eval.py                              # REQUIRED: entry point (docker run ... eval --dataset X --out Y)
├── results.json                         # REQUIRED: produced by eval against the L3 benchmark
├── Dockerfile                           # OPTIONAL for schema check; REQUIRED for S3 sandbox mode
├── dose_equivalence_credentials.json    # L2 5-tuple credential (at least one clinical task)
└── checkpoint/                          # model weights, or pointer to HF / IPFS
```

- `method.json` MUST declare `name` and `version` as non-empty strings; `paper` and `license` are required for publication.
- `eval.py` MUST be executable as the container entry point with `--dataset` and `--out` arguments (L3).
- `results.json` MUST be the file that `eval.py` produced for the L3 benchmark; its layout is §2.

## 2. `results.json` layout and field whitelist

Two layouts are accepted (both read by `verify.extract_paired_methods`):

1. WS-3 RunBundle layout: `validation.paired_methods.<name>` with per-method `psnr_db` / `ssim` / `detectability{...}`.
2. Flat metrics dict at the top level or under `validation`.

**Field whitelist per method block** (everything else is rejected by S1):

| Group | Fields | Gate role |
|---|---|---|
| Fidelity | `psnr_db`, `ssim` | §4 paired: at least one required |
| Discriminating detectability | `bander_roi` | **required** (Rung 1; `detectability-freq-v1` ROI BandER) |
| Transparency (never sufficient alone) | `cnr_mean`, `cho_auc_mean`, `npwe_mean` | reported for transparency only |
| Frequency supplementary | `bander_full`, `roi_tm_auc` | not gate criteria |
| Task identity | `task` | MUST equal `TASK_LABEL` (`SKE-Gaussian20HU-s2px`) |

Rules: every number must be a finite numeric value (never boolean/string); a fidelity number without a detectability number (or vice versa) is not publishable (§4 both-or-neither).

## 3. Claim block (five required fields) and evidence binding

Every `results.json` MUST carry a `claim` object with **all five** fields (missing/empty ⇒ reject, `verify.check_claim_bound_provenance`):

| Field | Meaning |
|---|---|
| `claim.task_id` | MUST equal `TASK_LABEL` |
| `claim.protocol_id` | MUST equal `detectability-freq-v1` (`verify.PROTOCOL_ID`) |
| `claim.data_manifest_sha256` | SHA-256 of `evidence.data_manifest` (canonical JSON, `provenance_sha256`) |
| `claim.model_sha256` | SHA-256 of `evidence.model_weights` (canonical JSON) |
| `claim.evaluator_version` | non-empty string naming the evaluator version |

The hashes MUST actually match the shipped `evidence`; a claim naming a different task / protocol, or a hash mismatch, is refused rather than silently recorded. A claim requesting patient-level bootstrap (`claim.bootstrap_level == "patient"` or `claim.aggregation == "patient-level"`) MUST carry `patient_id` evidence anywhere in the result (slices of one patient must not count as independent patients).

## 4. `vendor` / `dose` labels

- `vendor`: one of the required vendor strata from `task_spec.REQUIRED_VENDOR_GROUPS` — **GE, Philips, Siemens, Toshiba** — or the reference group `AAPM-Siemens-real`. Recorded verbatim as a board group key (spread / per-group trap rank).
- `dose`: a protocol dose-grid level (candidates: `r010` / `r025` / `r050` simulated arms; real-quarter-dose `AAPM-Siemens-real` reference; exact protocol-endorsed grid `[UNRESOLVED: owner=physicist, per PROTOCOL_SKELETON §3]`).
- Both are submitter-controlled metadata: like `method_name`, they are scanned for referee-owned paths (`leaderboard.json` / `heldout.json`) by `heldout.check_submission_cannot_write_back` and must not smuggle a write path.

## 5. Status system (five-state, per PROTOCOL_SKELETON §0)

Every claim / result row uses the five-state separation, tracked independently:

| State | Meaning |
|---|---|
| `implementation` | the code / artifact exists (this phase's deliverables) |
| `technically verified` | S0–S4 gates passed; `verify-bundle` verdict green |
| `scientifically supported` | independent check recorded (PROTOCOL_SKELETON §8–§9); owner acceptance |
| `externally used` | claimed for external use only after a gate-passing receipt is referenced |
| `owner accepted` | frozen protocol version assigned; all `[UNRESOLVED]` fields resolved |

Results table header (mandatory columns, PROTOCOL_SKELETON §6):

| claim_id | protocol_version | method | commit_hash | data_manifest_hash | dose_level | stratum(vendor) | primary_endpoint | endpoint_value | n_samples | uncertainty(CI) | receipt_id | status | decision/date |

## 6. Gate reference table

| Stage | What it enforces | Implementation | Outcome on violation |
|---|---|---|---|
| S0 | §4 paired + Rung 1 discriminating index | `verify.check_paired_submission` | REJECT |
| S1 | RunBundle structure + `results.json` whitelist | `verifier.check_runbundle_structure` | REJECT |
| S2 | task identity + claim provenance + no-write-path + rung evidence | `verifier.check_claim_and_provenance` (composes `verify` / `heldout` / `gates`) | REJECT (missing WS-1 artifacts ⇒ skipped, not passed) |
| S3 | published vs live `results.json` (1e-06 tolerance) | `verifier.verify_published_vs_live` (+ sandbox runtime) | REJECT on drift; SKIPPED without runtime |
| S4 | board publish eligibility (trap-rank + strata) → final write | `verifier.check_publish_eligibility` + `leaderboard.save()` (§2-C chain) | REJECT blocks the write |

**A receipt is not a publication.** `leaderboard.save()` attaches a receipt (`ws4-save-receipt/v1` style) with `publication.status = pending`; external publication is a separate decision outside this contract.

## 7. Red lines

- No claim of dose reduction / dose benefit is made or implied (PROTOCOL_SKELETON §0; only detectability-retention claims are permitted).
- Metric direction / clinical thresholds / R6 tolerance / registry statuses are red-line fields; this contract does not alter them.
- No commit / push / rebase (baseline `3823498`); WS-4 is not to be marked "done".
*（内容由AI生成，仅供参考）*
