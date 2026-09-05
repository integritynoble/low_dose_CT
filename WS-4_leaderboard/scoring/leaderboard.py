"""WS-4 leaderboard model: seed entries, paired submissions, permanent blur trap.

The leaderboard is *detectability-first* (Rung 1): entries sort by the declared
discriminating index (``task_spec.DISCRIMINATING_FIELDS``, i.e. ROI BandER),
then by the transparency observers CNR and CHO-AUC, then PSNR. A submission
without detectability never reaches the board
(:func:`pwm_ldct_recon.verify.check_paired_submission` gate).

Ranking led with CNR until 2026-09-05. That was the same defect as the gate's
missing discriminating field, one layer up: Rung 1 records CNR as
non-discriminative on real anatomy, and on the simulated arm the permanent blur
trap's CNR *exceeds* RED-CNN, CoreDiff and CTformer at every dose. A CNR-led
board therefore displayed the trap above real methods while every gate passed.

The **permanent Gaussian blur trap** (Rung 1.3 / §4) is a seed entry marked
``permanent=True``: it can never be removed or overwritten, every new submission is
ranked against it, and the listing always shows each entry's gap vs the blur trap.
Its purpose is to keep the board honest, so the board records where the trap
actually sits: :func:`trap_rank_report` is computed on every mutation and stored
under ``board["trap_rank"]``, so the verdict lives in the artifact rather than in
prose. :func:`assert_trap_ranks_last` is the hard gate for a publishing path.
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .task_spec import BLUR_SPEC, DISCRIMINATING_FIELDS, SCHEMA_VERSION, TASK_SPEC
from .verify import check_paired_submission, extract_paired_methods

BLUR_ENTRY_ID = "seed-blur"
REFERENCE_ENTRY_ID = "seed-ws3-reference"

#: Verdicts for the trap-rank gate. INDETERMINATE is distinct from FAIL on
#: purpose: "the board cannot be checked" must never be recorded as "the board
#: is sound", or omitting the trap's number becomes the way to evade the gate.
TRAP_RANK_PASS = "PASS"
TRAP_RANK_FAIL = "FAIL"
TRAP_RANK_INDETERMINATE = "INDETERMINATE"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_blur_entry() -> Dict:
    """The permanent blur seed (placeholder numbers until WS-3's real run).

    Values below mirror the WS-3 self-test structure (synthetic; ``placeholder=True``
    marks them as non-scientific). The key structural property already holds: PSNR is
    high relative to a reference while CNR is far below the Rose criterion of 3.
    Vendor/dose are deliberately left None: a trap is a method-level construct, not a
    vendor/dose-specific measurement.
    """
    return {
        "id": BLUR_ENTRY_ID,
        "method": "gaussian-blur",
        "kind": "seed-trap",
        "permanent": True,
        "trap": True,
        "placeholder": True,
        "vendor": None,
        "dose": None,
        "config": dict(BLUR_SPEC),
        "metrics": {
            "psnr_db": 20.808,
            "ssim": 0.6635,
            "cnr_mean": 0.0115,
            "cho_auc_mean": 1.0,
            "npwe_mean": 44229.6,
            "task": TASK_SPEC["label"],
        },
        "submitted_at": _utcnow(),
        "notes": ("Permanent Gaussian blur trap (sigma=1.0 px, 5x5). Placeholder numbers "
                  "from WS-3 self-test structure; refresh from WS-3 emit before launch. "
                  "PSNR high, CNR < Rose(3): high fidelity does not imply detectability."),
    }


def seed_reference_entry() -> Dict:
    """WS-3 reference method v1 seed (placeholder numbers until WS-3's real run)."""
    return {
        "id": REFERENCE_ENTRY_ID,
        "method": "WS-3 reference (unrolled + deep-ensemble)",
        "kind": "seed-reference",
        "permanent": False,
        "trap": False,
        "placeholder": True,
        "vendor": None,
        "dose": None,
        "metrics": {
            "psnr_db": 8.495,
            "ssim": 5.1e-05,
            "cnr_mean": None,       # undefined on synthetic noise-free patches
            "cho_auc_mean": 0.5,
            "npwe_mean": 0.0,
            "task": TASK_SPEC["label"],
        },
        "submitted_at": _utcnow(),
        "notes": ("Seed entry from WS-3 reference method v1. Placeholder numbers from "
                  "WS-3 self-test; refresh from the pinned RunBundle before launch."),
    }


def new_leaderboard() -> Dict:
    """Initialise the leaderboard with both seed entries (blur trap is permanent)."""
    entries = [seed_blur_entry(), seed_reference_entry()]
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_SPEC,
        "entries": entries,
        "trap_rank": trap_rank_report(entries),
        "spread": {},
    }


def _cnr_sort_key(entry: Dict) -> float:
    cnr = entry.get("metrics", {}).get("cnr_mean")
    return cnr if isinstance(cnr, (int, float)) else float("-inf")


def discriminating_value(entry: Dict) -> Optional[float]:
    """The entry's value on the declared discriminating index, or None.

    Reads ``task_spec.DISCRIMINATING_FIELDS`` in order rather than naming a
    metric here, so that changing what counts as discriminating is a single
    edit to the task specification and not a search through the leaderboard.
    """
    metrics = entry.get("metrics", {})
    for field in DISCRIMINATING_FIELDS:
        value = metrics.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def sort_entries(entries: List[Dict]) -> List[Dict]:
    """Detectability-first ranking: discriminating index desc, then CNR, CHO-AUC, PSNR.

    The discriminating index leads. An entry that does not report it sorts below
    every entry that does, rather than being silently ranked on a transparency
    observer the blur trap can win.
    """
    def key(e: Dict):
        m = e.get("metrics", {})
        disc = discriminating_value(e)
        auc = m.get("cho_auc_mean")
        psnr = m.get("psnr_db")
        return (disc if disc is not None else float("-inf"),
                _cnr_sort_key(e),
                auc if isinstance(auc, (int, float)) else float("-inf"),
                psnr if isinstance(psnr, (int, float)) else float("-inf"))
    return sorted(entries, key=key, reverse=True)


def blur_entry(entries: List[Dict]) -> Optional[Dict]:
    for e in entries:
        if e.get("id") == BLUR_ENTRY_ID:
            return e
    return None


def assert_trap_present(entries: List[Dict]) -> None:
    """The blur trap must always be on the board (Rung 1.3: it never leaves)."""
    if not any(e.get("id") == BLUR_ENTRY_ID and e.get("permanent") for e in entries):
        raise ValueError("permanent Gaussian blur trap missing from leaderboard")


def trap_rank_report(entries: List[Dict], *, min_ratio: Optional[float] = None) -> Dict:
    """Where the permanent blur trap sits on the declared discriminating index.

    The trap is a deliberate cheat: it destroys the high-frequency anatomy the
    detectability protocol measures while scoring the highest SSIM on the board.
    Rung 1, 3, 5 and 6 all rest on it ranking **last** on the discriminating
    index (measured 8.9-19.0x separation, blur last 4/4 in every vendor group).
    If it does not, one of two things is true, and neither may be published: an
    entry smooths harder than a plain Gaussian blur, or the index has stopped
    discriminating on this board. Which of the two it is, is a judgement for a
    person; that the board is not publishable as it stands, is not.

    Placeholder entries are excluded from the comparison: they carry
    ``placeholder=True`` and are marked non-scientific at the point of creation.

    Returns a verdict block; it never raises. ``verdict`` is one of PASS, FAIL,
    INDETERMINATE. INDETERMINATE means the board could not be checked, which is
    reported as its own state so that a missing trap number cannot be mistaken
    for a sound board.
    """
    index = DISCRIMINATING_FIELDS[0] if DISCRIMINATING_FIELDS else None
    report: Dict[str, Any] = {
        "index": index,
        "verdict": TRAP_RANK_PASS,
        "trap_value": None,
        "n_compared": 0,
        "min_ratio_required": min_ratio,
        "min_ratio_observed": None,
        "ranked": [],
        "violations": [],
        "note": "",
        "checked_at": _utcnow(),
    }
    if index is None:
        report["verdict"] = TRAP_RANK_INDETERMINATE
        report["violations"].append(
            "no discriminating index is declared in task_spec.DISCRIMINATING_FIELDS; "
            "the trap cannot be ranked")
        return report

    trap = blur_entry(entries)
    if trap is None or not trap.get("permanent"):
        report["verdict"] = TRAP_RANK_FAIL
        report["violations"].append("permanent Gaussian blur trap missing from leaderboard")
        return report

    comparable = []
    for e in entries:
        if e.get("id") == BLUR_ENTRY_ID or e.get("trap") or e.get("placeholder"):
            continue
        value = discriminating_value(e)
        if value is not None:
            comparable.append((e, value))

    trap_value = discriminating_value(trap)
    report["trap_value"] = trap_value
    report["n_compared"] = len(comparable)
    report["ranked"] = [{"id": e.get("id"), "method": e.get("method"), index: v}
                        for e, v in sorted(comparable, key=lambda p: p[1])]

    if not comparable:
        report["note"] = ("no non-placeholder entry reports %s; there is nothing to rank "
                          "the trap against and the board makes no detectability claim" % index)
        return report

    if trap_value is None:
        report["verdict"] = TRAP_RANK_INDETERMINATE
        report["violations"].append(
            "the permanent blur trap reports no %s while %d entr%s do; the board cannot be "
            "checked. Refresh the trap's numbers from the WS-3 run before publishing: a trap "
            "with no discriminating number would otherwise let any board pass."
            % (index, len(comparable), "y does" if len(comparable) == 1 else "ies do"))
        return report

    offenders = [(e, v) for e, v in comparable if v <= trap_value]
    for e, v in sorted(offenders, key=lambda p: p[1]):
        report["violations"].append(
            "entry '%s' scores %s=%.6g, at or below the permanent blur trap (%.6g), so the "
            "trap is not last. Either that entry smooths beyond a plain Gaussian blur, or %s "
            "has stopped discriminating on this board; the board is not publishable either way."
            % (e.get("id"), index, v, trap_value, index))
    if offenders:
        report["verdict"] = TRAP_RANK_FAIL

    if trap_value > 0:
        report["min_ratio_observed"] = min(v / trap_value for _, v in comparable)
    else:
        report["note"] = ("trap %s is %.6g, so no separation ratio is defined; rank is still "
                          "checked" % (index, trap_value))

    if min_ratio is not None and report["min_ratio_observed"] is not None:
        if report["min_ratio_observed"] < min_ratio:
            report["verdict"] = TRAP_RANK_FAIL
            report["violations"].append(
                "smallest trap separation is %.3gx, below the required %.3gx (Rung 5/6 uses "
                "3x); the trap is not separated widely enough to certify the index"
                % (report["min_ratio_observed"], min_ratio))
    return report


def check_trap_rank(entries: List[Dict], *, min_ratio: Optional[float] = None) -> List[str]:
    """Violations of the trap-rank gate; an empty list means the board is sound."""
    return list(trap_rank_report(entries, min_ratio=min_ratio)["violations"])


def assert_trap_ranks_last(entries: List[Dict], *, min_ratio: Optional[float] = None) -> None:
    """Hard gate: raise unless the permanent trap ranks last on the discriminating index.

    Use this on a publishing path. Ordinary mutation records the verdict on the
    board instead of raising, so that a board which fails this check is still
    written down with its failure attached rather than discarded.
    """
    violations = check_trap_rank(entries, min_ratio=min_ratio)
    if violations:
        raise ValueError("trap-rank gate: " + "; ".join(violations))


def add_submission(leaderboard: Dict, result: Dict, method: str,
                   submitted_at: Optional[str] = None,
                   vendor: Optional[str] = None,
                   dose: Optional[str] = None) -> List[Dict]:
    """Gate a submission and append it to the leaderboard.

    Returns the list of created entries (one per paired method block in ``result``).
    Raises ``ValueError`` for the submission as a whole if it carries no paired block,
    or for a specific method if that method's block violates the §4 paired rule
    (fidelity without detectability is not publishable).

    ``vendor`` / ``dose`` are the measurement context of the submission; they are kept
    per-entry so rankings can report spread without averaging across vendors (Rung 6).
    """
    methods = extract_paired_methods(result)
    if not methods:
        raise ValueError("submission contains no paired fidelity+detectability block")

    created: List[Dict] = []
    now = submitted_at or _utcnow()
    for name, m in methods.items():
        violations = check_paired_submission(m)
        if violations:
            raise ValueError(f"method '{name}' not publishable: {'; '.join(violations)}")
        metrics = {k: m[k] for k in ("psnr_db", "ssim", "cnr_mean", "cho_auc_mean",
                                     "npwe_mean", "task") if k in m}
        # frequency-domain detectability (detectability-freq-v1) is carried when
        # present; on real anatomy it is the discriminative dimension (R3/R5)
        for k in ("bander_roi", "bander_full", "roi_tm_auc"):
            if k in m:
                metrics[k] = m[k]
        entry = {
            "id": f"sub-{len(leaderboard['entries']) + 1}-{name}",
            "method": method if len(methods) == 1 else f"{method} [{name}]",
            "kind": "submission",
            "permanent": False,
            "trap": False,
            "placeholder": False,
            "vendor": vendor,
            "dose": dose,
            "metrics": metrics,
            "submitted_at": now,
            "notes": "Paired submission accepted by WS-4 gate (§4 both-or-neither).",
        }
        leaderboard["entries"].append(entry)
        created.append(entry)

    leaderboard["entries"] = sort_entries(leaderboard["entries"])
    leaderboard["spread"] = compute_spread(leaderboard["entries"])
    # The trap-rank verdict is recorded, not raised: a board on which the trap is
    # not last is evidence, and discarding it would let the board hide a failure
    # of its own index. `assert_trap_ranks_last` is the gate for publishing.
    leaderboard["trap_rank"] = trap_rank_report(leaderboard["entries"])
    return created


def _numeric(values: List[Any]) -> List[float]:
    return [v for v in values if isinstance(v, (int, float)) and v is not None]


def _span_std(name: str, values: List[Any]) -> Dict:
    nums = _numeric(values)
    block: Dict[str, Any] = {"n": len(nums)}
    if nums:
        block[f"{name}_span"] = max(nums) - min(nums)
        if len(nums) > 1:
            block[f"{name}_std"] = statistics.pstdev(nums)
    return block


def compute_spread(entries: List[Dict], by: str = "vendor") -> Dict:
    """Per-group dual-metric spread (Rung 5/6: never average across vendors/doses).

    R5 method adjustment (2026-08-22): the original R5 design required **external
    multi-vendor submissions** on the board before spread could be computed. No
    external multi-vendor submissions exist, so the project's own held-out
    AAPM/LIDC multi-vendor + multi-dose results are treated as the on-board
    submission set (proxy for external submissions; see WS-1
    ``output/aapm_per_dose_spread.json`` + ``_summary.md``). Constraints
    unchanged: per-vendor / per-dose grouping, never average across groups, and
    the permanent blur trap must separate in every group (checked by the R5/R6
    gate, not by this report function).

    Groups entries by the given context key (``vendor`` or ``dose``) and reports the
    span/std of fidelity (psnr_db), detectability (bander_roi when present --
    frequency-domain detectability-freq-v1 ROI BandER, the discriminative
    dimension on real anatomy) and transparency (cnr_mean) within each group.
    Groups with no measured value are reported as empty. Returns
    ``{group: {n, psnr_db_span, psnr_db_std?, bander_roi_span?, bander_roi_std?,
    cnr_mean_span, cnr_mean_std?}}``.
    """
    groups: Dict[str, List[Dict]] = {}
    for e in entries:
        key = e.get(by)
        if key is None or not isinstance(key, str):
            continue
        groups.setdefault(key, []).append(e)

    spread: Dict[str, Any] = {}
    for key in sorted(groups):
        members = groups[key]
        psnr = [m.get("metrics", {}).get("psnr_db") for m in members]
        ber = [m.get("metrics", {}).get("bander_roi") for m in members]
        cnr = [m.get("metrics", {}).get("cnr_mean") for m in members]
        block = _span_std("psnr_db", psnr)
        block.update(_span_std("bander_roi", ber))  # detectability (freq-v1) if present
        block.update(_span_std("cnr_mean", cnr))
        block["n_entries"] = len(members)
        spread[key] = block
    return spread


def load(path: str | Path) -> Dict:
    with open(path, encoding="utf-8") as f:
        board = json.load(f)
    assert_trap_present(board.get("entries", []))
    return board


def save(board: Dict, path: str | Path) -> None:
    assert_trap_present(board.get("entries", []))
    # Refresh the trap-rank verdict so no board is written without one. This
    # records a FAIL rather than refusing to write it: the failure is the finding.
    board["trap_rank"] = trap_rank_report(board.get("entries", []))
    Path(path).write_text(json.dumps(board, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
