---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_a417f307b40a11f1b3c552540024e231
    ReservedCode1: kAKmqyfxMq9czJvAfB46TTlYCYpbKIfwrdqlGNw3WclUrE+7aJOSJLSqg0HsvrnTfDbTMT1Fkz5m0ndFGCVUkhyqQFilrG++nxbnq+iW8Xl5H4pqXU251PPRXxjvAlFxDaVKrusywln8wyAC16mcxEr3kNV/RS/MvcQlLpTjOae9fRy4GZ2dlEPTYnc=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_a417f307b40a11f1b3c552540024e231
    ReservedCode2: kAKmqyfxMq9czJvAfB46TTlYCYpbKIfwrdqlGNw3WclUrE+7aJOSJLSqg0HsvrnTfDbTMT1Fkz5m0ndFGCVUkhyqQFilrG++nxbnq+iW8Xl5H4pqXU251PPRXxjvAlFxDaVKrusywln8wyAC16mcxEr3kNV/RS/MvcQlLpTjOae9fRy4GZ2dlEPTYnc=
---

# WS-4 Containerized Scoring Service Specification

- **Status:** `draft` — Phase 1 task 1.1. **This document fixes the S0–S4 definitions the rest of Phase 1 builds on, but the S1–S4 semantics proposed below are `[DRAFT]` and MUST be reviewed and confirmed by the Director / protocol owner before they are treated as normative.**
- Date: 2026-09-19
- Repo baseline: `low_dose_CT-heyang` @ `3823498` (no commit / push / rebase)
- Scope: README Phase 1 task 1.1 — *"Containerized scoring service spec — takes a RunBundle, executes in sandbox, verifies published vs live `results.json`"*.

---

## 1. Purpose

The scoring service is the **referee** for the WS-4 leaderboard. A community submission is a **RunBundle** (contract in [`../submission_contract.md`](../submission_contract.md)). The service must:

1. take a RunBundle,
2. execute it in a **sandboxed container** against a fixed dataset split,
3. **verify the published `results.json` against the live execution** (a submitter must not be able to post numbers it did not actually produce),
4. run the S0–S4 verification pipeline, and
5. post only verified scores to the leaderboard (via `leaderboard.save()`, whose gate chain is §2-C).

The scoring package already implements the metric and provenance gates (`verify.py`, `gates.py`, `heldout.py`, `leaderboard.py`, `rung_registry.py`); the pipeline in [`verifier.py`](./verifier.py) composes them. This spec defines the *semantics* of that composition and of the sandbox.

## 2. Architecture

```
RunBundle (submission_contract.md)
   │
   ▼
S1  structure / schema validation            verifier.check_runbundle_structure
   │
   ▼
S2  task identity + claim provenance + rung evidence gates
   │   verify.check_submission_result / check_claim_bound_provenance
   │   heldout.check_submission_cannot_write_back
   │   gates.check_pairing_validation / check_roi_protocol / check_dose_curve (WS-1 artifacts)
   ▼
S3  sandbox re-execution: published vs live results.json
   │   container runtime (Docker) + data machine; verifier.verify_published_vs_live
   ▼
S4  board publish eligibility                 verifier.check_publish_eligibility
   │   trap-rank gate + per-stratum separation (reuses leaderboard exports)
   │   final write goes through leaderboard.save()  (§2-C full gate chain + receipt)
   ▼
leaderboard.json  (publication status stays `pending`; a receipt is NOT a publication)
```

- **Referee, not contestant:** the service never imports the submitting method's package; it executes the RunBundle as an opaque unit and compares numbers.
- **No write path:** the submitter hands over a `SubmissionEnvelope`; `heldout.assert_no_write_path` / `check_submission_cannot_write_back` guarantee the envelope cannot reference `leaderboard.json` / `heldout.json` or expose a write surface.

## 3. S0 – metric gate (numerical gate; already implemented, NOT part of this phase's new work)

- **Semantics:** §4 both-or-neither paired rule + Rung 1 discriminating index.
- **Implementation:** `verify.check_paired_submission` (fidelity `psnr_db`/`ssim` AND detectability including `bander_roi`; insertion-based indices `cnr_mean`/`cho_auc_mean`/`npwe_mean` are transparency-only) + §2-A task identity (`task == TASK_LABEL`).
- **Status:** implemented (`verify.py`); this phase only wires it into the pipeline as S0.

## 4. S1 – RunBundle structure / schema validation

- **`[DRAFT]` semantics — ⚠️ 待 Director 复核确认.** Validates the RunBundle directory shape and the `results.json` schema before any numeric claim is considered.
- Required files: `method.json`, `eval.py`, `results.json` (contract §1 of `submission_contract.md`).
- Optional (sandbox-mode dependent): `Dockerfile`, `dose_equivalence_credentials.json` (L2 5-tuple), `checkpoint/` or HF/IPFS pointer.
- `results.json` field whitelist: `FIDELITY_FIELDS + DETECTABILITY_FIELDS + FREQ_SUPPLEMENTARY_FIELDS + task` per method block, plus the `claim` / `evidence` blocks (contract §2–§3). Unknown metric fields are rejected rather than silently ignored.
- Implementation: `verifier.check_runbundle_structure` (new in Phase 1; schema check only — no numeric logic).

## 5. S2 – task identity + claim-bound provenance + rung evidence gates

- **`[DRAFT]` semantics — ⚠️ 待 Director 复核确认.** Composes the existing gates; none are re-implemented:
  - §2-A task identity + §4 paired rule: `verify.check_submission_result`.
  - §2-D claim-bound provenance: `verify.check_claim_bound_provenance` — claim MUST carry the five required fields (`task_id`, `protocol_id`, `data_manifest_sha256`, `model_sha256`, `evaluator_version`) and bind to `evidence.data_manifest` / `evidence.model_weights` hashes (`provenance_sha256`).
  - P1-3 no-write-path envelope: `heldout.check_submission_cannot_write_back`.
  - Rung evidence gates (when the WS-1 artifacts are present beside the repo): `gates.check_pairing_validation` (Rung 2), `gates.check_roi_protocol` (Rung 3), `gates.check_dose_curve` (Rung 4). Missing WS-1 artifacts are reported as `skipped`, never as passed.
- Implementation: `verifier.check_claim_and_provenance` (composition only).

## 6. S3 – sandbox re-execution: published vs live `results.json`

- **`[DRAFT]` semantics — ⚠️ 待 Director 复核确认.**
- The service executes the RunBundle in a sandboxed container against the fixed held-out split (`heldout.HeldOutSet`), producing a **live** `results.json`.
- **Verification:** the published `results.json` must match the live execution. Comparison is done on the canonicalised-provenance footing: `verify.provenance_sha256` for structure-bearing fields, and **1e-06 absolute tolerance** for numeric metric fields (R6 recalc criterion, `WS-1_dataset/R6_recalc`).
- A mismatch of any numeric field beyond tolerance, or any structural difference, rejects the submission (`REJECT`); a service that cannot obtain a live result (no container runtime / no data machine) reports `S3: SKIPPED (runtime dependency)` and does **not** fabricate a pass.
- Implementation: `verifier.verify_published_vs_live(published, live)` (numeric/structure comparison, executable locally) + a `[UNRESOLVED]` live-execution wiring point (container runtime + data machine are external Phase-1 dependencies; not available on the authoring machine).

## 7. S4 – board publish eligibility

- **`[DRAFT]` semantics — ⚠️ 待 Director 复核确认.**
- The verified submission is eligible for the board only when the *resulting board* passes the publication gates:
  - trap-rank gate (permanent blur trap is last; `leaderboard.check_trap_rank`),
  - per-required-stratum separation (every `REQUIRED_VENDOR_GROUPS` group covered; `leaderboard.assert_trap_separates_in_every_group`),
  - `save()` full gate chain (§2-C): entry-level paired check + task identity + trap-rank + strata, then a receipt is attached and `publication.status` stays `pending`.
- **A receipt is not a publication.** The receipt only proves the gates ran; external publication is a separate decision.
- Implementation: `verifier.check_publish_eligibility` (pre-check reusing `leaderboard` exports; does NOT re-implement the gate chain), final write MUST go through `leaderboard.save()`.

## 8. Pipeline contract

`verifier.verify_runbundle(path) -> Verdict` runs S1 → S2 → S3 → S4 and returns a `Verdict` with per-stage violations plus a receipt reference (`ws4-save-receipt/v1` style). Stage order is fixed; a hard `REJECT` at an earlier stage is reported without pretending later stages ran. CLI: `python -m scoring.cli verify-bundle --bundle <path>`.

## 9. Red lines

- The pipeline must not weaken any existing gate to make S3 runnable without a sandbox; missing runtime dependency ⇒ `SKIPPED`, never a fabricated pass.
- `task_id` / `protocol_id` / metric direction / clinical thresholds / R6 tolerance / registry statuses are red-line fields; nothing in this phase modifies them.
- No commit / push / rebase (baseline `3823498`); WS-4 is not to be marked "done".
*（内容由AI生成，仅供参考）*
