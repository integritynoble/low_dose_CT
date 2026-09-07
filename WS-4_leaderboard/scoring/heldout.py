"""WS-4 held-out split architecture (low-dose-ct.md §6 / §7.2, P1-3).

The leaderboard is the **referee**, not a contestant: the held-out split must be
independent of any submitting method name (``W_name``) and must expose **no write
path** back to the ranking or to the held-out data. This module makes that a
structural property:

* :class:`HeldOutSet` is a frozen, read-only container. It exposes iteration and
  metadata only -- no ``write`` / ``save`` / ``append`` / ``update`` surface, so no
  downstream code can mutate the held-out data through it.
* :func:`assert_no_write_path` inspects an object's attributes and refuses any
  container that exposes a write surface.
* :class:`SubmissionEnvelope` carries a submitted result together with its declaring
  method name. It is the **only** object a submitter hands over; it cannot reference
  the leaderboard file or the held-out file.
* :func:`authorize_write` is the single gate for *any* mutation of the held-out split
  or the leaderboard file: only the OWN principal (the referee) may write. A
  submission object can never pass this gate because it carries no owner identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# The only principal allowed to authorise writes (OWN = referee).
OWN_PRINCIPAL = "OWN"

# A submitter's result must not contain a path pointing at these referee-owned files.
LEADERBOARD_FILE_NAME = "leaderboard.json"
HELDOUT_FILE_NAME = "heldout.json"

_WRITE_SURFACE = ("write", "save", "append", "extend", "remove", "pop", "update",
                  "delete", "add", "insert", "clear", "sort", "unlink", "rename",
                  "write_text", "write_bytes", "mkdir")


@dataclass(frozen=True)
class HeldOutSet:
    """Read-only held-out split for the referee.

    ``records`` is a tuple of immutable items; the class is frozen and exposes no
    write method. It is keyed by an opaque id, **not** by any submitting method name,
    so no ``W_name`` can influence which data is scored.
    """

    id: str
    records: Tuple[Any, ...]
    provenance: str = "held-out"
    authorized_by: str = OWN_PRINCIPAL

    def __iter__(self):
        return iter(self.records)

    def __len__(self) -> int:
        return len(self.records)


@dataclass(frozen=True)
class SubmissionEnvelope:
    """What a submitter hands over: a result dict + declaring method name.

    Deliberately minimal: it carries no reference to the leaderboard file, the
    held-out file, or any write surface. Gate code must verify this by calling
    :func:`assert_no_write_path` and :func:`assert_no_referee_paths`.
    """

    method_name: str
    result: Dict[str, Any]


def make_heldout_set(id: str, records: Iterable[Any],
                     provenance: str = "held-out") -> HeldOutSet:
    """Build a read-only held-out set. Only the referee (OWN) is recorded."""
    return HeldOutSet(id=id, records=tuple(records), provenance=provenance,
                      authorized_by=OWN_PRINCIPAL)


def assert_no_write_path(obj: Any) -> List[str]:
    """Return write-surface attribute names found on ``obj`` (empty = read-only).

    Built-in containers (dict / list / tuple / str / numbers) are excluded: their
    ``pop`` / ``clear`` / ``update`` methods operate on the in-memory object, not on
    the filesystem, so they cannot write back to the ranking or held-out data. Only
    *non-container* objects carrying a callable write/save/append/... attribute (e.g.
    a ``Path``, a custom handle) are reported.
    """
    if isinstance(obj, (dict, list, tuple, str, int, float, bool, type(None))):
        return []
    found: List[str] = []
    for name in _WRITE_SURFACE:
        try:
            attr = getattr(obj, name)
        except Exception:
            continue
        if callable(attr):
            found.append(name)
    return found


def assert_no_referee_paths(obj: Any) -> List[str]:
    """Return referee-owned path strings found inside a submission object.

    Scans strings recursively for the leaderboard / held-out file names so a
    submitter cannot smuggle a write-back path into the envelope. Dict **keys**
    are scanned as well as values: a key is submitter-controlled data too, so a
    values-only walk lets ``{"../data/leaderboard.json": 1}`` through.
    """
    found: List[str] = []
    targets = (LEADERBOARD_FILE_NAME, HELDOUT_FILE_NAME)
    stack = [obj]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            for t in targets:
                if t in item:
                    found.append(item)
        elif isinstance(item, dict):
            stack.extend(item.keys())
            stack.extend(item.values())
        elif isinstance(item, (list, tuple)):
            stack.extend(item)
    return found


def authorize_write(principal: str) -> bool:
    """Only the OWN principal may authorise writes to held-out data / ranking."""
    return principal == OWN_PRINCIPAL


def referee_append(heldout: HeldOutSet, records: Iterable[Any],
                   authorized_by: str) -> HeldOutSet:
    """Append to a held-out set under OWN authorisation.

    Returns a *new* HeldOutSet (immutability) or raises ``PermissionError`` if the
    caller is not OWN. Submissions can never pass here because their envelope does
    not carry the OWN principal.
    """
    if not authorize_write(authorized_by):
        raise PermissionError(
            f"write to held-out split requires OWN principal; got '{authorized_by}'")
    return HeldOutSet(
        id=heldout.id,
        records=tuple(heldout.records) + tuple(records),
        provenance=heldout.provenance,
        authorized_by=OWN_PRINCIPAL)


def check_submission_cannot_write_back(submission: SubmissionEnvelope) -> List[str]:
    """Gate: a submission envelope must not expose any write path.

    Returns a list of violations; empty list = the submission is structurally unable
    to modify the ranking or the held-out data.

    The scan is **recursive**: a submitter can hide a ``write`` / ``save`` /
    ``append`` attribute or a referee-owned path string anywhere inside the result
    dict, so both the envelope itself and every nested key and value are inspected.
    ``method_name`` is submitter-controlled and is recorded verbatim on the board,
    so it is scanned for referee-owned paths too, not just the payload.
    """
    violations: List[str] = []
    write_surface = assert_no_write_path(submission)
    nested = _find_nested_write_surface(submission.result)
    if write_surface or nested:
        violations.append(
            f"submission exposes write surface attributes: "
            f"{sorted(set(write_surface + nested))}")
    referee_paths = assert_no_referee_paths(submission.result)
    if referee_paths:
        violations.append(
            f"submission references referee-owned files: {referee_paths}")
    name_paths = assert_no_referee_paths(submission.method_name)
    if name_paths:
        violations.append(
            f"submission method name references referee-owned files: {name_paths}")
    return violations


def _find_nested_write_surface(obj: Any, _seen: set | None = None) -> List[str]:
    """Recursively find write-surface attribute names in nested values.

    Dict / list / tuple nodes are traversed without being flagged (their native
    methods are not filesystem-write capable); every *non-container* leaf is checked
    for callable write/save/append/... attributes. Dict **keys** are traversed as
    well as values, or a smuggled handle used as a key escapes the scan.
    """
    if _seen is None:
        _seen = set()
    found: List[str] = []
    stack = [obj]
    while stack:
        item = stack.pop()
        if id(item) in _seen:
            continue
        _seen.add(id(item))
        if isinstance(item, dict):
            stack.extend(item.keys())
            stack.extend(item.values())
        elif isinstance(item, (list, tuple)):
            stack.extend(item)
        else:
            found.extend(assert_no_write_path(item))
    return found
