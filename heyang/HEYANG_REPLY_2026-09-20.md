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
| 1 — paper package (1.1–1.5) | DONE | 1.1/1.2/1.3: [ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md](evidence/ENV_RECON_AND_MANUSCRIPT_FIX_2026-09-21.md); 1.2: `Heyang-paper/manuscript.tex` 19 prose fixes + README 6 fixes; 1.3: `make_tables.py --check` and `recompare_per_metric.py --check` both exit 0; 375 total = 5 seeds x 3 doses x 5 quantities x 5 methods; 1.5: commits `d140b71` (CLAIM_EVIDENCE ledger + regenerated tables/PDF), `04fb541` (COMPLETION_CHECKLIST), 6-page PDF rebuilt | 1.4 owner-only metadata (author order / affiliations / ORCIDs / corresponding author / CRediT / declarations) not yet provided; 5 `\todo{}` remain, all owner-decision fields; branch ready for final author review, not pushed | after owner metadata reply |
| 2 — Windows CT + agent receipt | IN PROGRESS | [WINDOWS_COMPAT_RECEIPT_2026-09-21.md](evidence/WINDOWS_COMPAT_RECEIPT_2026-09-21.md); CT commands run natively on Windows 11 (26100), PowerShell 5.1, versions recorded | `ldct_agent` all entry points (unittest + CLI) BLOCKED at import (`ImportError: needs shared core 'research-agents'`), exit 1, no business logic executed; core head unrecordable; needs authorized core checkout + `RESEARCH_CORE` | after shared core path is provided |
| 3 — publication-state UI/CLI | DONE | [RELEASE_STATUS_VISIBILITY_2026-09-21.md](evidence/RELEASE_STATUS_VISIBILITY_2026-09-21.md); commit `9448610`: `WS-4_leaderboard/scoring/verifier.py`, `cli.py`, `leaderboard.py`, `web/app.js|index.html|style.css`, `tests/test_publication_status.py` (23 assertions) + 8-state fixtures; Windows pytest 312 passed/10 skipped; hard constraint: no skipped/pending case labeled published/verified | none (agent repo out of scope for this task) | 2026-09-21 |
| 4 — evaluator-bound provenance | DONE | [PROVENANCE_BINDING_2026-09-21.md](evidence/PROVENANCE_BINDING_2026-09-21.md); commit `9448610`: new `WS-4_leaderboard/scoring/binding.py`, `tests/test_input_binding.py` (19 cases), edits to `verify.py` / `leaderboard.py` / `cli.py` / `__init__.py`; three binding loops close at runtime (model bytes, asset manifest, patient mapping); direct-save bypass rejected | live S3 runtime and authorized data source not ready — no source-data authentication claimed (post-local scope in the assignment) | 2026-09-21 (local fixtures); live S3 separate |
| 5a — BANDER diagnostics | IN PROGRESS | [BANDER_DIAG_AUDIT_2026-09-21.md](evidence/BANDER_DIAG_AUDIT_2026-09-21.md); 9-14 evidence inventory COMPLETE (D1/D2 session-only items declared unrecoverable); BANDER-6 COMPLETE with PARTIAL sub-item; driver/params/checkpoints/per-patient output recoverable from `freq_aapm_real_r025_*.json` + `ckpt_hashes.txt` | BANDER-2 (five controls on real slices, R3-matched ROIs) needs new computation, awaits authorization to run `bander/control-matrix` `a42ad27` `scripts/bander_controls.py` on the authorized image machine; BANDER-6 matched-control values incomplete on the control side | after owner authorization for BANDER-2 run |
| 5b — copy/deposit receipt | DONE | [COPIES_DEPOSIT_RECEIPT_2026-09-21.md](evidence/COPIES_DEPOSIT_RECEIPT_2026-09-21.md); V1–V5 PASS: substrate 364/364 hash match, checkpoint 5/5 match; redacted manifest + file counts + checksums (`checksums_substrate_364`, `checksums_ct_key_artifacts`, `checksums_ldct_agent`, all measured 2026-09-21); receipt itself COMPLETE | off-machine copy NOT on disk: no v0.5 substrate found under local OneDrive; needs OneDrive/Teams shared-folder access; share token kept out of the repository | copy action after OneDrive access |

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

## 2026-09-22 status (task book steps 3-4)

- **CT head**: `5b3659c` (task book step 3 paper package; pushed to
  `origin/heyang` 2026-09-22, fast-forward, 0/0 divergence).
- **Task 3 - corrected paper package**: DONE, commit `5b3659c`.
  - `Heyang-paper/manuscript.tex`: environment table `tab:env` (L123-149);
    README retrospective paragraph; no unsupported causal/universal claims
    (re-scan 0 hits); remaining `\todo{}` all owner-decision fields.
  - Re-run and recorded: `make_tables.py`, `make_tables.py --check`,
    `recompare_per_metric.py --check` - all exit 0 (5 methods PASS, outside
    declared 0, overall PASS, committed verdict matches).
  - `Heyang-paper/manuscript.pdf` rebuilt: 7 pages, 198,198 B; no undefined
    citation/reference; tables current.
  - `Heyang-paper/CLAIM_EVIDENCE.md`: manuscript line refs re-synced after the
    environment-table insertion (0 stale refs).
- **Task 4 - completion receipt**: DONE.
  - [COMPLETION_CHECKLIST.md](Heyang-paper/COMPLETION_CHECKLIST.md): source
    commit, artifact hashes, verification/build results, remaining TODO owners,
    compact owner decision list (8 items), code/data availability language
    (code availability does not grant image/checkpoint redistribution).
  - Paper package pushed: `origin/heyang` = `5b3659c`.
  - Paper PR: **#30** <https://github.com/integritynoble/low_dose_CT/pull/30>
    (base `main` <- head `heyang`, open, ready for owner review; no submission
    until authors approve).
- **Owner decision list (compact, see checklist section 9)**: author order /
  affiliations / ORCIDs / corresponding author; CRediT; per-author
  declarations; third-environment choice; artifact release decision. Blocks
  manuscript L22 / L289 / L305 / L310 / L313.
- **Not committed**: `WS-2_framework/pwm_dose_equivalence/reproducibility/
  reproducible_manifest.json` (line-ending noise only, non-task content) left
  as-is.
