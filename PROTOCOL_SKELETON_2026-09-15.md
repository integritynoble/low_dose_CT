---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_fdf66e15b23b11f1ab3f52540024e231
    ReservedCode1: P6QwkCmLF8s+H29IyzcRaZgwt2licc72uI/IObf+SeXCAYEX34FjWDLzVY1hAkscg+1TE2t9QOx6h4+d6ws8FpSuxpz0ABKzJu9jBeN4UAkKRLDTNddY/g0nw7i7eH7AaecPD4eMb80BlT7WFRiW7wAQ3Sw2wZ3iK+mNafwbnEOaLl8r8+m+b3/kPac=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_fdf66e15b23b11f1ab3f52540024e231
    ReservedCode2: P6QwkCmLF8s+H29IyzcRaZgwt2licc72uI/IObf+SeXCAYEX34FjWDLzVY1hAkscg+1TE2t9QOx6h4+d6ws8FpSuxpz0ABKzJu9jBeN4UAkKRLDTNddY/g0nw7i7eH7AaecPD4eMb80BlT7WFRiW7wAQ3Sw2wZ3iK+mNafwbnEOaLl8r8+m+b3/kPac=
---

# Versioned Dose–Task Protocol Skeleton — 2026-09-15

- Protocol version: **0.1.0-draft** (this file is a skeleton; a frozen protocol is `[UNRESOLVED: owner=Physicist+radiologists+statistician+Heyang, decision_needed=frozen version number and publication-grade wording, date=2026-09-17]`)
- Status (five-state, separate): implementation=`draft-skeleton`, technically verified=`not-yet`, scientifically supported=`not-yet`, externally used=`not-yet`, owner accepted=`not-yet`. Each field below carries its own status when applicable.
- Scope of this document: a claim-level checklist for collaborators to adopt field by field. Nothing here is a scientific, clinical, dataset-rights, or owner decision (see HEYANG_NEXT_2026-09-15.md §5).

> **No dose-reduction / dose-benefit claim is made or implied anywhere in this protocol.** The only claim template permitted is a **detectability-retention** claim, measured on the declared task below.

---

## 1. Claim (detectability-retention template)

Template (to be completed only after collaborators decide margins; see §7):

> On [population, decided by radiologists], under [dose level(s) / acquisition settings, decided by physicists], the [method name + version + commit] detection method retains detectability on the declared task (`TASK_LABEL` below) within [UNRESOLVED: owner=statistician, decision_needed=retention margin (e.g. one-sided lower bound on primary endpoint ratio vs adequate reference), date=2026-09-17] of the [adequate reference, decided by physicists], as measured by [primary endpoint, decided by statistician; candidate: `bander_roi`], at [confidence level, decided by statistician], over the required vendor strata (§5).

Claim wiring (from the merged scoring gate, §2 of HEYANG_NEXT):
- Gate C binds every published claim to a gate-passing receipt with `publication=pending`; claims must reference the receipt id before `externally used` can be marked.
- Gate D requires claim-bound provenance and rejects unknown `patient_id`; every number in the claim must trace to a provenance record with hashes (§4).
- Claim scope limited to detectability retention. **Dose reduction / dose benefit is out of scope and must not be claimed.**

Status: implementation=`skeleton`, technically verified=`not-yet`, scientifically supported=`not-yet`, externally used=`not-yet`, owner accepted=`not-yet`.

## 2. Task and population

- Task label (declared, frozen in `WS-4_leaderboard/scoring/task_spec.py`): `TASK_LABEL = "SKE-Gaussian20HU-s2px"`.
- Signal: Gaussian lesion, sigma = 2.0 px, peak contrast = 20 HU, location known = True, inserted into a tissue ROI with noise ROI HU band [10, 120].
- Observers: CNR with Rose criterion >= 3; CHO with DOG-4 channels; NPWE with eye filter `rho*exp(-rho/0.2)`. These mirror `WS-1_dataset/baselines/src/pwm_ldct_baselines/observers.py` (`PAIRED_TASK`) and `WS-3_reference_method/method/src/pwm_ldct_recon/evaluation.py` (`task_config`).
- Discriminating index (gate-required, `DISCRIMINATING_FIELDS`): `bander_roi` — frequency-domain detectability-freq-v1 ROI BandER. At least one discriminating field is required for publishability.
- Transparency fields (reported alongside, never sufficient alone): `cnr_mean`, `cho_auc_mean`, `npwe_mean`.
- Supplementary frequency fields (not gate criteria): `bander_full`, `roi_tm_auc`.
- Intended population: `[UNRESOLVED: owner=radiologists, decision_needed=target population / inclusion criteria / imaging context, date=2026-09-17]`.
- Clinical margin / adequacy floors: `[UNRESOLVED: owner=statistician, decision_needed=adequacy floors and retention margin, date=2026-09-17]`.

## 3. Dose quantity and generation

- Dose level(s): `[UNRESOLVED: owner=physicist, decision_needed=which dose levels / r values are protocol-endorsed (candidates in repo: r025 / r050 / r010 simulated arms, real-quarter-dose AAPM-Siemens-real as reference group), date=2026-09-17]`.
- Dose generation provenance: generation scripts and checkpoints `[UNRESOLVED: owner=physicist, decision_needed=pin generation code and checkpoint versions; note §3 of HEYANG_NEXT assigns BANDER-2/BANDER-6 measurements to Heyang, pending authorized imaging assets]`.
- Adequate reference: `[UNRESOLVED: owner=physicist, decision_needed=adequate reference method (candidate: real-quarter-dose group or declared baseline), date=2026-09-17]`.
- Strong comparators: `[UNRESOLVED: owner=statistician+physicist, decision_needed=final comparator list; repo candidate set: blur trap (permanent, Rung 1.3), RED-CNN, CTformer, learned/other methods present in comparison_full764.json], date=2026-09-17]`.
- **No dose-reduction claim**: the protocol records dose quantity only to define the task grid; it does not assert a clinical dose benefit.

## 4. Data manifest hashes

Every claim block must record (all fields are placeholders — fill from the actual frozen artifacts):

| Field | Value / placeholder |
|---|---|
| protocol file hash | `[UNRESOLVED: owner=Heyang, decision_needed=sha256 of frozen protocol, date=2026-09-17]` |
| data manifest hash (inputs) | `[UNRESOLVED: owner=Heyang, decision_needed=sha256 of input manifest (slices + dose grid), date=2026-09-17]` |
| model/code hash | `[UNRESOLVED: owner=Heyang, decision_needed=sha256 of method source tree at claimed commit, date=2026-09-17]` |
| registry/board hash | `[UNRESOLVED: owner=Heyang, decision_needed=sha256 of leaderboard.json entry or receipt, date=2026-09-17]` |
| provenance record id | `[UNRESOLVED: owner=Heyang, decision_needed=receipt id from gate C; must bind claim -> provenance and reject unknown patient_id per gate D, date=2026-09-17]` |

Reference material currently in repo (not a frozen manifest):
- `WS-1_dataset/R6_recalc/results/comparison_full764.json` (764-entry comparison; tolerance 1e-06; per-model statuses e.g. blur PASS 75/75 with 0 diffs, red_cnn PASS 75 checked / 45 diffs within tolerance).
- `WS-1_dataset/R6_recalc/freq_detectability_recalc.py` and `WS-1_dataset/R6_recalc/results/freq_*.json` (frequency detectability recalc).
- `WS-1_dataset/output/aapm_dose_detectability.json` and summary artifacts.

## 5. Commands (reproduction template)

Placeholders — exact frozen commands `[UNRESOLVED: owner=Heyang, decision_needed=freeze per-command flags and env, date=2026-09-17]`.

- Scoring suite (from WS-4_leaderboard):
  `python -m pytest scoring/tests -q -rs -p no:cacheprovider`
- Frequency detectability recalc (WS-1):
  `python WS-1_dataset/R6_recalc/freq_detectability_recalc.py ...`
- Board by-vendor trap-rank report (read-only):
  `python -c "import scoring.leaderboard as L; L.trap_rank_report(...)"` from `WS-4_leaderboard` with `PYTHONPATH=WS-4_leaderboard`.
- Full §4 agent audit (Linux only; see readiness note):
  `PYTHONPATH=<pillcam_agent>:<ldct_agent checkout> LDCT_REPO=<this repo> python -m unittest discover -s tests -p 'test_ldct_*.py'`
  > `pillcam_agent` 为 15 日工作站共享核心目录（/home/S248103/pwm/pillcam_agent），非独立 GitHub 仓库；本机无此目录，§4 完整审计需在该工作站执行，或由 Director 提供可达路径。

Each reported command must be followed by its stdout/stderr + exit code in results.

## 6. Results table header (mandatory columns)

| claim_id | protocol_version | method | commit_hash | data_manifest_hash | dose_level | stratum(vendor) | primary_endpoint | endpoint_value | n_samples | uncertainty(CI) | receipt_id | status | decision/date |

Notes:
- `endpoint_value` and `uncertainty(CI)`: fill only from verified runs; leave blank until then. `[UNRESOLVED: owner=statistician, decision_needed=CI method (bootstrap/jackknife) and confidence level, date=2026-09-17]`.
- `status` uses the five-state separation of §0; a row is `scientifically supported` only after independent check (§8) and owner acceptance (§10).
- Empty coverage must not be reported as PASS (gate E semantics; §2-E).

## 7. Uncertainty reporting requirements

- Report per-stratum (per vendor group) uncertainty, not pooled-only.
- Required: point estimate + interval for `bander_roi` (primary), plus transparency fields when claimed.
- `[UNRESOLVED: owner=statistician, decision_needed=confidence level, CI method, multiplicity control across strata, date=2026-09-17]`.
- Uncertainties on `[UNRESOLVED: owner=radiologist, decision_needed=reader/annotation variability treatment, date=2026-09-17]`.

## 8. Stratum (vendor group) requirements

- Required vendor strata (from task_spec.py `REQUIRED_VENDOR_GROUPS`): **GE, Philips, Siemens, Toshiba** (authoritative cross-vendor run `aapm_lidc_cross_vendor_spread.json`, schema `aapm-lidc-cross-vendor-spread/v1`, LIDC lowdose_sim r=0.25).
- `AAPM-Siemens-real` is the real-quarter-dose **reference group**, not a required submission stratum.
- A claim of per-vendor trap separation/spread is only allowed when every required group is covered (gate B).
- Current board state (read-only check 2026-09-17): verdict `NO_CLAIM`, `n_compared = 0` in every vendor group — by-vendor result is vacuous and must not be used as evidence until real entries exist (§4 baseline agrees).

## 9. Independent check requirements

- Independent re-execution of §5 commands by a party not authoring the claim.
- Independent re-derivation of at least the primary endpoint on a held-out or independently prepared slice subset.
- `[UNRESOLVED: owner=statistician+Heyang, decision_needed=who performs independent check, what minimum re-run set, sign-off gate, date=2026-09-17]`.
- No claim may move from `technically verified` to `scientifically supported` without a recorded independent check note.

## 10. Decision / date block (one per unresolved field)

Each `[UNRESOLVED]` above is a task item. On resolution, append:

```
- RESOLVED: owner=<name>, decision=<value + rationale>, date=<YYYY-MM-DD>, replaces <UNRESOLVED tag date=2026-09-17>
```

Frozen protocol status: owner accepted = `not-yet` until all `[UNRESOLVED]` fields carry a RESOLVED record and the frozen version number is assigned (see §0).

---

## Limitations

1. This skeleton is a checklist; it is not a frozen protocol and makes no scientific claim.
2. All numeric/margin/endpoint values are explicitly unresolved — none are invented.
3. No dose-reduction claim is made; only detectability-retention on the declared task is in scope.
4. Board by-vendor results are currently vacuous (`NO_CLAIM`, 0 comparable entries per group).
5. Full §4 agent audit requires Linux + `pillcam_agent` shared core（15 日工作站共享核心目录，非独立 GitHub 仓库；本机不可用）。
6. BANDER-2/BANDER-6 measurements await authorized imaging assets (owner: Heyang).
*（内容由AI生成，仅供参考）*
