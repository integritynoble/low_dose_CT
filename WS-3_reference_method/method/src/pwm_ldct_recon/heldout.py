"""Held-out split isolation (low-dose-ct.md §6 may-not / §7.2 split-by-patient).

The WS-3 reference method must **never** train on, or even read, the held-out split that
WS-4 will score against. This module makes that a structural property rather than a
process promise:

  * :class:`HeldOutSet` is a **read-only** data container: it carries records and
    provenance but exposes no write / append / save method, so nothing downstream can
    mutate the held-out data through it.
  * :func:`assert_no_write_path` inspects an object's attributes and refuses any object
    that exposes a write surface (``write`` / ``save`` / ``append`` / ``remove`` ...).
  * :func:`check_eval_train_imports` statically scans the evaluation entrypoint modules
    to confirm they do **not** import the training path (``data`` / ``train``), so the
    validation code cannot accidentally reach into the training data contract.
  * :func:`check_heldout_isolation` verifies that a validation block declares its
    data provenance (held-out / authorised source) before it can be accepted as
    publishable evidence.

Design rule (mirrors WS-4's referee-side ``heldout`` module): the evaluation code and the
held-out data live in *separate* modules; the eval path receives data only as ordinary
value arguments, never by reading the held-out split itself.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# Marker written into validation blocks produced from the held-out split.
HELDOUT_PROVENANCE = "heldout-split"
TRAIN_PROVENANCE = "training-split"

# The only principal allowed to authorise writes to the held-out split (OWN / referee).
OWN_AUTHORIZED = "OWN"

# Write-surface attribute names that would make a container mutable.
_WRITE_SURFACE = ("write", "save", "append", "extend", "remove", "pop", "update",
                  "delete", "add", "insert", "clear", "sort")

# Evaluation entrypoints that must stay train-free (static scan targets).
_EVAL_MODULES = (
    Path(__file__).resolve().parent / "evaluation.py",
    Path(__file__).resolve().parent.parent.parent.parent / "runbundle" / "run.py",
)


@dataclass(frozen=True)
class HeldOutSet:
    """Read-only holder for held-out slices.

    ``records`` is a tuple of immutable items; the class is frozen and exposes **no**
    write method. Use :func:`assert_no_write_path` on instances in tests / gates to make
    the property explicit.
    """

    records: Tuple[Any, ...]
    provenance: str = HELDOUT_PROVENANCE
    authorized_by: str = OWN_AUTHORIZED

    def __iter__(self):
        return iter(self.records)

    def __len__(self) -> int:
        return len(self.records)


def make_heldout_set(records: Iterable[Any], provenance: str = HELDOUT_PROVENANCE,
                     authorized_by: str = OWN_AUTHORIZED) -> HeldOutSet:
    """Build a read-only held-out set from an iterable of records."""
    return HeldOutSet(tuple(records), provenance=provenance, authorized_by=authorized_by)


def assert_no_write_path(obj: Any) -> List[str]:
    """Return the list of write-surface attribute names found on ``obj``.

    Empty list means the object is (structurally) read-only. Call this on held-out data
    containers in tests and at the evaluation gate; any non-empty result is a violation.
    """
    found: List[str] = []
    for name in _WRITE_SURFACE:
        if hasattr(obj, name) and callable(getattr(obj, name)):
            found.append(name)
    return found


def check_eval_train_imports() -> List[str]:
    """Statically verify the eval entrypoints do not import the training path.

    Scans ``evaluation.py`` and ``runbundle/run.py`` source for imports of the training
    modules (``.train`` / ``from .data import``). Returns the list of offending lines;
    empty list = clean.
    """
    offenders: List[str] = []
    banned = re.compile(r"(^|\s)(from\s+\.?(data|train)\s+import|import\s+\.?(data|train)"
                        r"|\bpwm_ldct_recon\.(data|train)\b)")
    for path in _EVAL_MODULES:
        if not path.exists():
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(source.splitlines(), 1):
            if banned.search(line):
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")
    return offenders


def check_heldout_isolation(validation: Dict) -> List[str]:
    """Verify a validation block is declared held-out before it is publishable.

    Checks:
      1. The block (or its ``data_provenance`` field) declares the held-out split.
      2. If the block claims training provenance, it is rejected as publishable
         evidence (training numbers cannot be used to score the held-out split).
    """
    errors: List[str] = []
    if not isinstance(validation, dict):
        return ["validation is not an object"]
    prov = validation.get("data_provenance")
    if prov is None:
        errors.append("validation block does not declare data provenance; "
                      "held-out isolation cannot be confirmed")
    elif str(prov).lower() == TRAIN_PROVENANCE:
        errors.append("validation block declares training-split provenance; "
                      "training numbers are not publishable evidence for the held-out split")
    elif str(prov).lower() != HELDOUT_PROVENANCE:
        errors.append(f"unknown data provenance '{prov}'; expected '{HELDOUT_PROVENANCE}'")
    return errors


def heldout_isolation_gate(validation: Dict, *, mode: str) -> List[str]:
    """Full held-out isolation gate for the RunBundle.

    In ``self-test`` mode only the static import check runs (the demo uses synthetic
    pairs and is explicitly non-scientific); in ``emit`` (real reproduction) mode the
    validation block must additionally declare held-out provenance.
    """
    errors = check_eval_train_imports()
    if mode == "emit":
        errors += check_heldout_isolation(validation)
    return errors
