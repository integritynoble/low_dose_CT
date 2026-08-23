"""WS-4 Rung 1-6 status registry (low-dose-ct.md problem queue, P3-6).

The leaderboard page keeps a living registry of where each Rung stands
(done / partial / blocked + reason + which data it supports). The rule from the
spec: **a Rung is closed by the registry, not by an agent** -- the registry file is
the single source of truth for 'what is supported and what is still missing'.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "data" / "rung_registry.json"

STATUS_VALUES = ("done", "partial", "blocked")


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        reg = json.load(f)
    validate_registry(reg)
    return reg


def validate_registry(reg: Dict[str, Any]) -> List[str]:
    """Structural checks: rungs 1..6 present, statuses in the allowed set."""
    errors: List[str] = []
    rungs = reg.get("rungs", [])
    seen = {r.get("rung") for r in rungs}
    for expected in range(1, 7):
        if expected not in seen:
            errors.append(f"missing rung {expected}")
    for r in rungs:
        status = r.get("status")
        if status not in STATUS_VALUES:
            errors.append(f"rung {r.get('rung')}: bad status '{status}'")
        if not r.get("gate"):
            errors.append(f"rung {r.get('rung')}: missing gate")
    return errors


def render_markdown(reg: Dict[str, Any]) -> str:
    lines = [
        "# WS-4 Rung 1-6 Registry",
        "",
        f"> Maintained by WS-4 leaderboard. Updated {reg.get('updated_at', 'unknown')}.",
        f"> Rule: a Rung is closed by this registry, not by an agent.",
        "",
        "| Rung | Title | Status | Supported data | Reason | Gate |",
        "|---|---|---|---|---|---|",
    ]
    for r in reg["rungs"]:
        data = "; ".join(r.get("supported_data", []))
        lines.append(
            f"| {r['rung']} | {r['title']} | **{r['status']}** | {data} | "
            f"{r.get('reason', '')} | `{r.get('gate', '')}` |")
    return "\n".join(lines) + "\n"


def update_status(reg: Dict[str, Any], rung: int, status: str,
                  reason: str | None = None) -> Dict[str, Any]:
    """Update one Rung's status (validated); returns the registry."""
    if status not in STATUS_VALUES:
        raise ValueError(f"invalid status '{status}'")
    for r in reg["rungs"]:
        if r["rung"] == rung:
            r["status"] = status
            if reason:
                r["reason"] = reason
            return reg
    raise ValueError(f"rung {rung} not found")


def save_registry(reg: Dict[str, Any], path: str | Path = DEFAULT_REGISTRY) -> None:
    validate_registry(reg)
    Path(path).write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
