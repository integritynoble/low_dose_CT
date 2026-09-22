---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_50be9eb4b5a611f19286525400638852
    ReservedCode1: wYvLR+GBiV555OxnniuvT6vG+Ls2bXPgop/FqW0oIyKJfQ0f+MwiwFSPKYWQNKp7AxjdSPnjgxn2RillpjNU8g/iDVHfKdcRl3DwKXcI3PJPdFv6vTLtCnJVXWDOG3dKQ/yUWV3ovNMHLQ0Eu6fpfHXMQmLbVeVeFOwXyJG0CQ8skkk38GjnJwG4E6E=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_50be9eb4b5a611f19286525400638852
    ReservedCode2: wYvLR+GBiV555OxnniuvT6vG+Ls2bXPgop/FqW0oIyKJfQ0f+MwiwFSPKYWQNKp7AxjdSPnjgxn2RillpjNU8g/iDVHfKdcRl3DwKXcI3PJPdFv6vTLtCnJVXWDOG3dKQ/yUWV3ovNMHLQ0Eu6fpfHXMQmLbVeVeFOwXyJG0CQ8skkk38GjnJwG4E6E=
---

# Heyang progress reply — 20 September 2026

This file is the single progress index for
[HEYANG_NEXT_2026-09-20.md](HEYANG_NEXT_2026-09-20.md). Status values are
restricted to IN PROGRESS / DONE / BLOCKED; evidence entries name real files,
commit hashes and measured results only.

- **CT checkout**: `D:\ZHY\low_dose_CT-heyang` branch `heyang`, HEAD
  `3472815abcfa7c6faf2679a75f27e5c9cf250e83` (merge origin/main, sync 2026-09-20)
- **Agent checkout**: `D:\ZHY\ldct_agent-main` branch `heyang`, HEAD `c2a75c5`
- **Shared core**: `pillcam_agent` (research-agents) — no checkout on this
  machine; core head/version cannot be recorded until an authorized checkout is
  shared (blocker for task 2).
- **Worktree**: 15 pre-existing uncommitted changes (Heyang-paper prose + WS-4
  scoring/web development) are intentionally NOT included in this commit.

## Progress index

| Task | Status | Commit / evidence | Remaining blocker | ETA |
|---|---|---|---|---|
| 0 — sync and acknowledgement | DONE | CT `heyang` HEAD `3472815` (merge origin/main, no history rewrite); agent branch HEAD `c2a75c5`; this file is the acknowledgement | Shared core `pillcam_agent` checkout/path not yet shared (no local checkout, core head unrecordable) | 2026-09-21 |
| 1 — paper package (1.1–1.5) | DONE | 1.1/1.2/1.3: [ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md](C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_5848855f38b4411189d7a61a80701333\output\ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md); 1.2: `Heyang-paper/manuscript.tex` 19 prose fixes + README 6 fixes; 1.3: `make_tables.py --check` and `recompare_per_metric.py --check` both exit 0; 375 total = 5 seeds x 3 doses x 5 quantities x 5 methods; 1.5: commits `d140b71` (CLAIM_EVIDENCE ledger + regenerated tables/PDF), `04fb541` (COMPLETION_CHECKLIST), 6-page PDF rebuilt | 1.4 owner-only metadata (author order / affiliations / ORCIDs / corresponding author / CRediT / declarations) not yet provided; 5 `\todo{}` remain, all owner-decision fields; branch ready for final author review, not pushed | after owner metadata reply |
| 2 — Windows CT + agent receipt | IN PROGRESS | [WINDOWS_COMPAT_RECEIPT_2026-09-21.md](C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_5848855f38b4411189d7a61a80701333\output\WINDOWS_COMPAT_RECEIPT_2026-09-21.md); CT commands run natively on Windows 11 (26100), PowerShell 5.1, versions recorded | `ldct_agent` all entry points (unittest + CLI) BLOCKED at import (`ImportError: needs shared core 'research-agents'`), exit 1, no business logic executed; core head unrecordable; needs authorized core checkout + `RESEARCH_CORE` | after shared core path is provided |
| 3 — publication-state UI/CLI | DONE | [RELEASE_STATUS_VISIBILITY_2026-09-21.md](C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_5848855f38b4411189d7a61a80701333\output\RELEASE_STATUS_VISIBILITY_2026-09-21.md); commit `9448610`: `WS-4_leaderboard/scoring/verifier.py`, `cli.py`, `leaderboard.py`, `web/app.js|index.html|style.css`, `tests/test_publication_status.py` (23 assertions) + 8-state fixtures; Windows pytest 312 passed/10 skipped; hard constraint: no skipped/pending case labeled published/verified | none (agent repo out of scope for this task) | 2026-09-21 |
| 4 — evaluator-bound provenance | DONE | [PROVENANCE_BINDING_2026-09-21.md](C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_5848855f38b4411189d7a61a80701333\output\PROVENANCE_BINDING_2026-09-21.md); commit `9448610`: new `WS-4_leaderboard/scoring/binding.py`, `tests/test_input_binding.py` (19 cases), edits to `verify.py` / `leaderboard.py` / `cli.py` / `__init__.py`; three binding loops close at runtime (model bytes, asset manifest, patient mapping); direct-save bypass rejected | live S3 runtime and authorized data source not ready — no source-data authentication claimed (post-local scope in the assignment) | 2026-09-21 (local fixtures); live S3 separate |
| 5a — BANDER diagnostics | IN PROGRESS | [BANDER_DIAG_AUDIT_2026-09-21.md](C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_5848855f38b4411189d7a61a80701333\output\BANDER_DIAG_AUDIT_2026-09-21.md); 9-14 evidence inventory COMPLETE (D1/D2 session-only items declared unrecoverable); BANDER-6 COMPLETE with PARTIAL sub-item; driver/params/checkpoints/per-patient output recoverable from `freq_aapm_real_r025_*.json` + `ckpt_hashes.txt` | BANDER-2 (five controls on real slices, R3-matched ROIs) needs new computation, awaits authorization to run `bander/control-matrix` `a42ad27` `scripts/bander_controls.py` on the authorized image machine; BANDER-6 matched-control values incomplete on the control side | after owner authorization for BANDER-2 run |
| 5b — copy/deposit receipt | DONE | [COPIES_DEPOSIT_RECEIPT_2026-09-21.md](C:\Users\ufl\AppData\Roaming\Tencent\Marvis\User\oAN1i2UYfvOcqvWo-7R7BX4MGNvY\workspace\conv_5848855f38b4411189d7a61a80701333\output\COPIES_DEPOSIT_RECEIPT_2026-09-21.md); V1–V5 PASS: substrate 364/364 hash match, checkpoint 5/5 match; redacted manifest + file counts + checksums (`checksums_substrate_364`, `checksums_ct_key_artifacts`, `checksums_ldct_agent`, all measured 2026-09-21); receipt itself COMPLETE | off-machine copy NOT on disk: no v0.5 substrate found under local OneDrive; needs OneDrive/Teams shared-folder access; share token kept out of the repository | copy action after OneDrive access |

## Owner input needed (one compact list)

1. Paper metadata (task 1.4): author order, affiliations, ORCIDs, corresponding
   author, CRediT, declarations.
2. Reference-environment records, if held (task 1.1): OS version, GPU model/count,
   driver, CUDA/cuDNN, Python/PyTorch/NumPy versions, original run commands
   (pip freeze / nvidia-smi archive / confirmed container tag), or accept the
   stated Methods limitation.
3. Shared core access (task 2 / task 0): authorized `pillcam_agent`
   (research-agents) checkout or path to set `RESEARCH_CORE`.
4. Authorization to run BANDER-2 (task 5a): `bander/control-matrix` `a42ad27`
   `scripts/bander_controls.py` on the authorized image machine (CPU
   deterministic; no expensive inference rerun).
5. OneDrive/Teams shared-folder access for the off-machine substrate copy
   (task 5b).

## Not pushed

This file and the worktree changes are committed on `heyang` only; nothing has
been pushed. The 15 pre-existing uncommitted changes remain uncommitted local
work awaiting their own review.

## 2026-09-21 status (HEYANG_NEXT_2026-09-21.md step 1)

- **CT head**: `82bf1397` (merge origin/main `1b1fdca`, 2026-09-21). Re-fetched
  origin on 2026-09-21: no new remote commits (`origin/main` still `1b1fdca`),
  `.git/MERGE_HEAD` clean — no further merge needed.
- **Agent head**: `c2a75c5` (`ldct_agent-main`, branch `heyang`).
- **Local work not yet pushed**: (a) progress-index commits `cadc2d7`, `7a9dd15`, `d140b71`, `04fb541`, `9448610`; (b) merge `82bf1397`; (c) remaining worktree changes: `Heyang-paper/` 4 files carry framework-injected AIGC frontmatter/notice (not task content, kept out of commits), `reproducible_manifest.json` (line-ending only, noise), `Heyang-paper/manuscript.tex` + README prose fixes already covered by `d140b71`.
- **Paper package ETA**: 2026-09-23, subject to owner confirmation (adjustable).

### Owner input — 2026-09-21 (compact)

1. Author order / affiliations / ORCIDs / corresponding author / CRediT /
   competing interests → blocks manuscript author block and task 1.4.
2. Data/code availability decision (existing rights; code availability does not
   grant image/checkpoint redistribution) → blocks `data availability` paragraph.
3. Journal target confirmation (MP Tech Note vs Sci Rep) → blocks journal-target
   declaration.
4. Third-environment GPU study decision → blocks upgrade options in the paper.
5. Reference-environment records, if held (OS/GPU/driver/CUDA/PyTorch/NumPy/
   original commands) → blocks task 1.1 methods-limitation statement.
6. Shared core access (`pillcam_agent` checkout / `RESEARCH_CORE`) → blocks
   tasks 2 and 0.
7. BANDER-2 authorization → blocks task 5a.
8. OneDrive/Teams shared-folder access → blocks task 5b off-machine copy.
*（内容由AI生成，仅供参考）*
