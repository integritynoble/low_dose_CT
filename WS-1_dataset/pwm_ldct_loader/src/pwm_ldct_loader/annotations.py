"""Annotation loading and majority-vote consolidation (annotation_qa_protocol.md).

The consolidation here is the reference implementation of §3 of the QA protocol
(IoU matching + majority inclusion + median attribute fusion). The released consolidated
files are regenerable from the deposited per-reader raw labels via ``consolidate_readers``.
"""
from __future__ import annotations

import json
import os
import statistics as st
from typing import Dict, List, Sequence

NODULE_DIRS = ("lidc_majority_vote", "topup_aapm", "topup_mayo")


def _iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return inter / union if union > 0 else 0.0


def load_series_nodules(root: str, patient_id: str) -> List[dict]:
    """Load a patient's consolidated nodules from whichever annotation dir holds them."""
    for d in NODULE_DIRS:
        p = os.path.join(root, "annotations", d, f"{patient_id}.json")
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f).get("nodules", [])
    return []


def load_series_likert(root: str, series_id: str) -> dict:
    p = os.path.join(root, "annotations", "likert", f"{series_id}.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {}


def nodules_for_slice(nodules: List[dict], z: int) -> List[dict]:
    return [n for n in nodules if n.get("slice_index") == z]


def consolidate_readers(
    per_reader: Dict[str, List[dict]],
    iou_thr: float = 0.3,
    min_fraction: float = 0.5,
) -> List[dict]:
    """Majority-vote consolidation (annotation_qa_protocol.md §3).

    Matches nodules across readers by IoU on the same slice, includes a candidate when more
    than ``min_fraction`` of readers marked it, and fuses attributes by median.
    """
    items = [(rid, n) for rid, ns in per_reader.items() for n in ns]
    used = [False] * len(items)
    n_readers = max(1, len(per_reader))
    out: List[dict] = []
    for i, (ri, ni) in enumerate(items):
        if used[i]:
            continue
        group = [(ri, ni)]
        used[i] = True
        for j in range(i + 1, len(items)):
            rj, nj = items[j]
            if used[j]:
                continue
            if nj.get("slice_index") == ni.get("slice_index") and _iou(ni["bbox_xyxy"], nj["bbox_xyxy"]) >= iou_thr:
                group.append((rj, nj))
                used[j] = True
        readers = {r for r, _ in group}
        if len(readers) > min_fraction * n_readers:
            boxes = [g[1]["bbox_xyxy"] for g in group]
            out.append({
                "bbox_xyxy": [st.median(c) for c in zip(*boxes)],
                "slice_index": ni.get("slice_index"),
                "diameter_mm": st.median([g[1].get("diameter_mm", 0.0) for g in group]),
                "texture": int(st.median([g[1].get("texture", 3) for g in group])),
                "ground_truth": "majority_vote",
                "n_contributing_readers": len(readers),
            })
    return out
