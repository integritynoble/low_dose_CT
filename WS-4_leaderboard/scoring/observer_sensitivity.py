"""WS-4 observer-channel publication & ranking sensitivity (low-dose-ct.md Rung 1.2, P2-5).

The leaderboard's primary observer is the **CNR + CHO(DOG-4) + NPWE** stack published
in :mod:`task_spec`. This module publishes the full observer channel configuration --
including each observer's **internal noise** parameters -- and provides the
``report_observer_sensitivity`` entry point that answers the question:

    *"If the referee scored the same submissions with a second observer, how much
    would the ranking change?"*

It reports per-entry rank shifts, the rank correlation (Spearman) between the two
observer rankings, and the relative position of every entry **vs the permanent blur
trap** (a submission that flips from above to below the trap is the most dangerous
kind of ranking instability).

Note on data: actual re-scoring with observer B requires re-running the WS-3
RunBundle on the held-out split. Until that run exists, the sensitivity report runs on
a **synthetic perturbation** (fixed seed) of the primary observer's numbers, clearly
marked ``synthetic=True`` -- this validates the plumbing, not the physics.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List

from .leaderboard import BLUR_ENTRY_ID, blur_entry, sort_entries
from .task_spec import DETECTABILITY_FIELDS, TASK_SPEC

# --------------------------------------------------------------------------- #
# Published observer channels (Rung 1.2: "stated observer")
# --------------------------------------------------------------------------- #

OBSERVER_A = {
    "name": "CNR+CHO(DOG-4)+NPWE",
    "role": "primary",
    "cnr": {"rose_criterion": TASK_SPEC["observer"]["cnr"]["rose_criterion"]},
    "cho": {
        "channels": TASK_SPEC["observer"]["cho"]["channels"],
        "n_channels": TASK_SPEC["observer"]["cho"]["n_channels"],
    },
    "npwe": {"eye_filter": TASK_SPEC["observer"]["npwe"]["eye_filter"]},
    "internal_noise": {
        # Additive white internal noise on the observer decision variable.
        "model": "additive-white",
        "sigma": 0.05,
        "unit": "decision-variable std",
    },
    "reference": "task_spec.TASK_SPEC.observer (shared with WS-1/WS-3)",
}

# Second observer: wider channel set + more aggressive eye filter + higher internal
# noise. This is a *published alternative*, deliberately different from A so the
# sensitivity report is informative, not tautological.
OBSERVER_B = {
    "name": "CNR+CHO(DOG-6)+NPWE(beta)",
    "role": "secondary",
    "cnr": {"rose_criterion": TASK_SPEC["observer"]["cnr"]["rose_criterion"]},
    "cho": {
        "channels": "dog",
        "n_channels": 6,
    },
    "npwe": {"eye_filter": "rho^2*exp(-rho/0.25)"},
    "internal_noise": {
        "model": "additive-white",
        "sigma": 0.08,
        "unit": "decision-variable std",
    },
    "reference": "published by WS-4 (P2-5); no WS-3 run yet",
}

OBSERVER_CHANNELS = [OBSERVER_A, OBSERVER_B]


def publish_observer_channels() -> Dict[str, Any]:
    """Return the full published observer-channel document (A + B)."""
    return {
        "task": TASK_SPEC["label"],
        "detectability_fields": list(DETECTABILITY_FIELDS),
        "observers": OBSERVER_CHANNELS,
        "note": ("Every submission's detectability numbers must state which observer "
                 "channel (A/B) and internal-noise settings were used; the leaderboard "
                 "ranks by the primary observer by default."),
    }


# --------------------------------------------------------------------------- #
# Sensitivity computation (synthetic until WS-3 re-run exists)
# --------------------------------------------------------------------------- #

def _observer_b_metrics(entry: Dict, rng: random.Random) -> Dict[str, float]:
    """Synthetic observer-B numbers for one entry (fixed-seed perturbation).

    Primary CNR is shifted by a small multiplicative noise; CHO-AUC is nudged so the
    ranking *can* flip near ties. Marked synthetic downstream.
    """
    m = entry.get("metrics", {})
    cnr = m.get("cnr_mean")
    auc = m.get("cho_auc_mean")
    out: Dict[str, float] = {}
    if isinstance(cnr, (int, float)):
        out["cnr_mean"] = cnr * (1.0 + rng.uniform(-0.15, 0.15))
    if isinstance(auc, (int, float)):
        out["cho_auc_mean"] = min(1.0, max(0.0, auc + rng.uniform(-0.05, 0.05)))
    return out


def _rank_ids(entries: List[Dict]) -> Dict[str, int]:
    return {e["id"]: i for i, e in enumerate(sort_entries(entries), 1)}


def rank_shift_report(entries: List[Dict], seed: int = 20260821) -> Dict[str, Any]:
    """Compare primary (A) vs synthetic second-observer (B) rankings.

    Returns per-entry rank shifts, Spearman rho, Kendall tau, and every entry's
    position relative to the permanent blur trap under both observers.
    """
    rng = random.Random(seed)
    rank_a = _rank_ids(entries)

    shifted: List[Dict] = []
    for e in entries:
        b = _observer_b_metrics(e, rng)
        e_b = {**e, "metrics": {**e.get("metrics", {}), **b}}
        shifted.append(e_b)
    rank_b = _rank_ids(shifted)

    blur_id = BLUR_ENTRY_ID
    blur_pos_a = rank_a.get(blur_id)
    blur_pos_b = rank_b.get(blur_id)

    per_entry: List[Dict] = []
    ids = [e["id"] for e in entries]
    for eid in ids:
        per_entry.append({
            "id": eid,
            "rank_primary": rank_a[eid],
            "rank_secondary": rank_b[eid],
            "rank_shift": rank_b[eid] - rank_a[eid],
            "above_trap_primary": rank_a[eid] < blur_pos_a,
            "above_trap_secondary": rank_b[eid] < blur_pos_b,
            "trap_flip": (rank_a[eid] < blur_pos_a) != (rank_b[eid] < blur_pos_b),
        })

    # Rank correlation (Spearman) between the two orderings.
    n = len(ids)
    if n > 1:
        d_sq = sum((rank_a[i] - rank_b[i]) ** 2 for i in ids)
        spearman = 1.0 - (6.0 * d_sq) / (n * (n * n - 1))
    else:
        spearman = 1.0

    return {
        "synthetic": True,
        "seed": seed,
        "observer_primary": OBSERVER_A["name"],
        "observer_secondary": OBSERVER_B["name"],
        "spearman_rho": spearman,
        "entries": per_entry,
        "blur_trap_position": {"primary": blur_pos_a, "secondary": blur_pos_b},
        "note": ("Synthetic perturbation of primary numbers until the WS-3 "
                 "observer-B re-run exists; validates the reporting pipeline only."),
    }


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "## Observer sensitivity (P2-5)",
        "",
        f"- Primary observer: `{report['observer_primary']}`",
        f"- Second observer: `{report['observer_secondary']}`",
        f"- Spearman rho (rank correlation): {report['spearman_rho']:.3f}",
        f"- Blur-trap position: primary #{report['blur_trap_position']['primary']} / "
        f"secondary #{report['blur_trap_position']['secondary']}",
        f"- synthetic={report['synthetic']} (seed {report['seed']})",
        "",
        "| id | rank A | rank B | shift | above trap A | above trap B | trap flip |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in report["entries"]:
        lines.append(
            f"| {e['id']} | {e['rank_primary']} | {e['rank_secondary']} | "
            f"{e['rank_shift']:+d} | {e['above_trap_primary']} | "
            f"{e['above_trap_secondary']} | {e['trap_flip']} |")
    lines.append("")
    lines.append(f"> {report['note']}")
    return "\n".join(lines)


def report_observer_sensitivity(entries: List[Dict], seed: int = 20260821,
                                markdown: bool = False) -> str:
    """Public entry point: produce the observer-sensitivity report (text or MD)."""
    report = rank_shift_report(entries, seed=seed)
    if markdown:
        return render_markdown(report)
    return _render_text(report)


def _render_text(report: Dict[str, Any]) -> str:
    lines = [
        f"Observer sensitivity: {report['observer_primary']} -> "
        f"{report['observer_secondary']} (synthetic seed {report['seed']})",
        f"Spearman rho = {report['spearman_rho']:.3f}",
        f"Blur trap position: primary #{report['blur_trap_position']['primary']}, "
        f"secondary #{report['blur_trap_position']['secondary']}",
    ]
    for e in report["entries"]:
        lines.append(
            f"  {e['id']:<28} rank {e['rank_primary']}->{e['rank_secondary']} "
            f"(shift {e['rank_shift']:+d})  above_trap "
            f"{e['above_trap_primary']}->{e['above_trap_secondary']} "
            f"flip={e['trap_flip']}")
    return "\n".join(lines)
