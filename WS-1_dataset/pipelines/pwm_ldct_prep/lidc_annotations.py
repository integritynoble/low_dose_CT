"""LIDC-IDRI nodule XML -> harmonized per-slice annotations (annotation_qa_protocol.md §7).

Parses the four-radiologist ``LidcReadMessage`` XML (namespace-agnostic), extracts per-reader,
per-slice nodule boxes + texture, and maps each ROI's ``imageZposition`` to the reconstructed
slice index. Majority-vote consolidation is delegated to
``pwm_ldct_loader.annotations.consolidate_readers`` (the QA-protocol §3 reference implementation).

NOTE: the LIDC annotation XMLs are distributed separately from the CT image objects (e.g. via the
NBIA Data Retriever download or TCIA's LIDC-XML set); they are NOT part of an image-only API pull.
The converter activates when an ``*.xml`` is found alongside a patient's DICOMs; otherwise the
patient is emitted without annotations.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, List, Sequence


def _ln(tag: str) -> str:
    """Local element name without the XML namespace."""
    return tag.split("}")[-1]


def _children(el, name: str):
    return [c for c in el if _ln(c.tag) == name]


def _first(el, name: str):
    for c in el:
        if _ln(c.tag) == name:
            return c
    return None


def _text(el, name: str, default=None):
    c = _first(el, name)
    return c.text.strip() if (c is not None and c.text) else default


def parse_lidc_xml(xml_path: str) -> Dict[str, List[dict]]:
    """Return ``{reader_id: [roi_record, ...]}`` from a LIDC reading XML.

    One record per (nodule, slice-ROI): ``{nodule_id, reader_id, z_mm, sop_uid, bbox_xyxy_px,
    texture, n_points, inclusion}``. Sub-3mm nodules have a single edge point -> degenerate box.
    """
    root = ET.parse(xml_path).getroot()
    out: Dict[str, List[dict]] = {}
    for si, sess in enumerate(_children(root, "readingSession")):
        rid = _text(sess, "servicingRadiologistID") or f"reader{si + 1}"
        base, k = rid, 1
        while rid in out:                      # disambiguate blank/duplicate reader ids
            k += 1
            rid = f"{base}_{k}"
        records: List[dict] = []
        for nod in _children(sess, "unblindedReadNodule"):
            nid = _text(nod, "noduleID") or ""
            chars = _first(nod, "characteristics")
            texture = None
            if chars is not None:
                t = _text(chars, "texture")
                texture = int(t) if (t and t.isdigit()) else None
            for roi in _children(nod, "roi"):
                z = _text(roi, "imageZposition")
                inclusion = (_text(roi, "inclusion") or "TRUE").upper() == "TRUE"
                xs, ys = [], []
                for em in _children(roi, "edgeMap"):
                    xv, yv = _text(em, "xCoord"), _text(em, "yCoord")
                    if xv is not None and yv is not None:
                        xs.append(float(xv))
                        ys.append(float(yv))
                if not xs:
                    continue
                records.append({
                    "nodule_id": nid,
                    "reader_id": rid,
                    "z_mm": float(z) if z else None,
                    "sop_uid": _text(roi, "imageSOP_UID"),
                    "bbox_xyxy_px": [min(xs), min(ys), max(xs), max(ys)],
                    "texture": texture,
                    "n_points": len(xs),
                    "inclusion": inclusion,
                })
        out[rid] = records
    return out


def _nearest_slice(z_mm: float, slice_positions: Sequence) -> int:
    zs = [p[2] for p in slice_positions]
    return min(range(len(zs)), key=lambda i: abs(zs[i] - z_mm))


def to_harmonized(parsed: Dict[str, List[dict]], slice_positions, pixel_spacing) -> Dict[str, List[dict]]:
    """Map raw ROIs to per-reader harmonized nodule dicts (raw_per_reader format).

    Maps ``z_mm`` to the nearest reconstructed slice and converts the in-plane bbox extent to mm.
    """
    row_sp, col_sp = float(pixel_spacing[0]), float(pixel_spacing[1])
    per_reader: Dict[str, List[dict]] = {}
    for rid, records in parsed.items():
        items: List[dict] = []
        for r in records:
            if r["z_mm"] is None or not slice_positions:
                continue
            x0, y0, x1, y1 = r["bbox_xyxy_px"]
            items.append({
                "nodule_id": r["nodule_id"],
                "slice_index": _nearest_slice(r["z_mm"], slice_positions),
                "bbox_xyxy": [x0, y0, x1, y1],
                "diameter_mm": round(max((x1 - x0) * col_sp, (y1 - y0) * row_sp), 3),
                "texture": r["texture"] if r["texture"] is not None else 3,
                "inclusion": r["inclusion"],
            })
        per_reader[rid] = items
    return per_reader
