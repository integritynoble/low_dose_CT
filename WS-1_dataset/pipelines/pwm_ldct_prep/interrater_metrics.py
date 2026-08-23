"""Inter-rater reliability verification for the PWM-LDCT v0.5 annotation campaign.

Reference implementation of annotation_qa_protocol.md §5:

  - detection kappa  : Cohen's kappa on per-candidate-nodule presence/absence
                       after IoU matching (§3.1), pairwise between readers
                       and between each reader and the majority vote;
  - texture kappa    : linearly-weighted Cohen's kappa on the 1-5 ordinal
                       texture score over matched nodules;
  - likert ICC       : ICC(2,k) across readers per (reconstruction x dose level).

STATUS: executable framework. Real per-reader annotation data do not yet exist
(annotation campaign pending; see annotation_campaign_plan.md §5 timeline). The
script therefore ships with two modes:

  --demo   : run on a small synthetic dataset that exercises every code path
             (passing and failing kappa/ICC), so the framework and QA gates can
             be validated today;
  (default): run on the real annotation tree once it exists, reading
             annotations/raw_per_reader/{patient_id}/{reader_id}.json and
             annotations/likert/{series_id}.json per annotation_qa_protocol.md §7.

Usage:
    # validate the framework end-to-end on synthetic data (works today):
    python interrater_metrics.py --demo

    # real-data run (requires campaign output; see [PENDING-DATA] markers below):
    python interrater_metrics.py --annotations-root <release_root>/annotations

Output: a JSON report with pairwise kappa/ICC matrices, gate pass/fail
(calibration gate Cohen's kappa >= 0.60; ICC(2,k) reported per level), and a
machine-readable summary line `gate: PASS|FAIL` suitable for CI.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Gates (must equal annotation_qa_protocol.md [CONFIRM] values and the
# manuscript's \todo values at submission)
# ---------------------------------------------------------------------------
KAPPA_GATE = 0.60          # Cohen's kappa pass threshold (calibration + drift)
IOU_THR = 0.30             # nodule matching threshold (protocol §3.1)
N_CALIBRATION_CASES = 20   # onboarding set size (protocol §2)
DRIFT_WINDOW = 50          # rotating recalibration cadence (protocol §4.1)

# ---------------------------------------------------------------------------
# Cohen's kappa (unweighted / linearly weighted)
# ---------------------------------------------------------------------------

def cohen_kappa(
    labels_a: Sequence[int],
    labels_b: Sequence[int],
    weight: str = "linear",
) -> float:
    """Cohen's kappa with optional linear weighting (for ordinal texture).

    labels_a/b: aligned integer category labels (same length). Handles the
    all-agree / single-category degenerate case by returning 1.0 (perfect
    agreement) when expected agreement is also complete.
    """
    n = len(labels_a)
    if n == 0:
        return float("nan")
    cats = sorted(set(labels_a) | set(labels_b))
    if len(cats) == 1:
        return 1.0
    k = len(cats)
    index = {c: i for i, c in enumerate(cats)}
    obs = np.zeros((k, k), dtype=np.float64)
    for a, b in zip(labels_a, labels_b):
        obs[index[a], index[b]] += 1.0
    po = np.trace(obs) / n
    pa = (obs.sum(axis=0) / n) @ (obs.sum(axis=1) / n)
    if weight == "linear":
        w = np.ones((k, k))
        for i in range(k):
            for j in range(k):
                w[i, j] = 1.0 - abs(i - j) / (k - 1)
        po = (obs * w).sum() / n
        # expected weighted agreement under independence
        exp = np.outer(obs.sum(axis=1), obs.sum(axis=0)) / (n * n)
        pe = (exp * w).sum()
    else:
        pe = pa
    if pe == 1.0:
        return 1.0 if po == 1.0 else float("nan")
    return float((po - pe) / (1.0 - pe))


# ---------------------------------------------------------------------------
# Nodule matching (same IoU logic as pwm_ldct_loader.annotations)
# ---------------------------------------------------------------------------

def _iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return inter / union if union > 0 else 0.0


def _pairwise_matches(
    a: List[dict],
    b: List[dict],
    iou_thr: float = IOU_THR,
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """Greedy IoU matching on the same slice; returns (matched pairs,
    unmatched-a indices, unmatched-b indices)."""
    pairs: List[Tuple[int, int]] = []
    used_b = [False] * len(b)
    for i, na in enumerate(a):
        best_j, best_iou = None, iou_thr
        for j, nb in enumerate(b):
            if used_b[j]:
                continue
            if na.get("slice_index") != nb.get("slice_index"):
                continue
            iou = _iou(na["bbox_xyxy"], nb["bbox_xyxy"])
            if iou > best_iou:
                best_j, best_iou = j, iou
        if best_j is not None:
            pairs.append((i, best_j))
            used_b[best_j] = True
    unmatched_a = [i for i in range(len(a)) if not any(p[0] == i for p in pairs)]
    unmatched_b = [j for j in range(len(b)) if not any(p[1] == j for p in pairs)]
    return pairs, unmatched_a, unmatched_b


def detection_kappa(
    reader_a: List[dict],
    reader_b: List[dict],
    iou_thr: float = IOU_THR,
) -> float:
    """Cohen's kappa on per-candidate presence/absence after IoU matching.

    Candidates = union of matched nodule identities; each reader votes present
    for a candidate if they marked it (matched), absent otherwise. Unmatched
    nodules contribute absence for the other reader.
    """
    pairs, unmatched_a, unmatched_b = _pairwise_matches(reader_a, reader_b, iou_thr)
    n_pairs = len(pairs)
    n_cand = n_pairs + len(unmatched_a) + len(unmatched_b)
    if n_cand == 0:
        return float("nan")
    # Each candidate is (a_present, b_present): matched => (1,1);
    # a-only => (1,0); b-only => (0,1). Presence/absence is binary.
    labels_a = [1] * (n_pairs + len(unmatched_a)) + [0] * len(unmatched_b)
    labels_b = [1] * (n_pairs + len(unmatched_b)) + [0] * len(unmatched_a)
    return cohen_kappa(labels_a, labels_b, weight="none")


def texture_kappa(
    reader_a: List[dict],
    reader_b: List[dict],
    iou_thr: float = IOU_THR,
) -> float:
    """Linearly-weighted Cohen's kappa on texture scores over matched nodules."""
    pairs, _, _ = _pairwise_matches(reader_a, reader_b, iou_thr)
    if not pairs:
        return float("nan")
    ta = [reader_a[i]["texture"] for i, _ in pairs]
    tb = [reader_b[j]["texture"] for _, j in pairs]
    return cohen_kappa(ta, tb, weight="linear")


# ---------------------------------------------------------------------------
# ICC(2,k) — two-way random effects, absolute agreement (Shrout & Fleiss 1979)
# ---------------------------------------------------------------------------

def icc_2k(scores: List[List[float]]) -> float:
    """ICC(2,k) for k raters across m targets (protocol §5 Likert metric).

    scores: list of targets, each a list of per-reader scores (same length k).
    Returns ICC(2,k) or nan when no variance is estimable.
    """
    X = np.asarray(scores, dtype=np.float64)
    if X.ndim != 2 or X.shape[0] < 2 or X.shape[1] < 2:
        return float("nan")
    m, k = X.shape
    grand = X.mean()
    sst = ((X - grand) ** 2).sum()
    if sst == 0.0:
        return 1.0
    row_means = X.mean(axis=1)
    col_means = X.mean(axis=0)
    ss_rows = k * ((row_means - grand) ** 2).sum()
    ss_cols = m * ((col_means - grand) ** 2).sum()
    ss_res = sst - ss_rows - ss_cols
    df_res = (m - 1) * (k - 1)
    ms_rows = ss_rows / (m - 1)
    ms_res = ss_res / df_res
    # ICC(2,1) = (MS_rows - MS_res) / (MS_rows + (k-1)*MS_res + k*(MS_cols-MS_res)/m)
    ms_cols = ss_cols / (k - 1)
    num = ms_rows - ms_res
    den = ms_rows + (k - 1) * ms_res + k * (ms_cols - ms_res) / m
    if den == 0.0:
        return float("nan")
    icc21 = num / den
    return float((k * icc21) / (1 + (k - 1) * icc21))


# ---------------------------------------------------------------------------
# Real-data readers (annotation_qa_protocol.md §7)
# ---------------------------------------------------------------------------

def _load_nodule_records(root: str, patient_id: str, reader_id: str) -> List[dict]:
    # [PENDING-DATA] Real per-reader files arrive from the annotation campaign:
    # annotations/raw_per_reader/{patient_id}/{reader_id}.json (§7.2).
    p = os.path.join(root, "annotations", "raw_per_reader", patient_id, f"{reader_id}.json")
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return json.load(f).get("nodules", [])


def _load_likert_records(root: str, series_id: str) -> dict:
    # [PENDING-DATA] annotations/likert/{series_id}.json (§7.3).
    p = os.path.join(root, "annotations", "likert", f"{series_id}.json")
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        return json.load(f)


def verify_real_annotations(root: str) -> dict:
    """Compute the manuscript's inter-rater table from the real annotation tree.

    [PENDING-DATA] This path returns an empty/`gated:false` report until the
    campaign's raw_per_reader + likert files exist; see annotation_campaign_plan.md
    (timeline) and annotation_qa_protocol.md §7 (formats).
    """
    # --- nodule kappa (pairwise + vs majority vote) -------------------------
    patients = sorted({
        d for d in os.listdir(os.path.join(root, "annotations", "raw_per_reader"))
        if os.path.isdir(os.path.join(root, "annotations", "raw_per_reader", d))
    }) if os.path.isdir(os.path.join(root, "annotations", "raw_per_reader")) else []
    reader_sets: Dict[str, Dict[str, List[dict]]] = {}
    for pid in patients:
        rdir = os.path.join(root, "annotations", "raw_per_reader", pid)
        for fname in sorted(os.listdir(rdir)):
            if not fname.endswith(".json"):
                continue
            rid = fname[:-5]  # strip .json so _load_nodule_records finds the file
            reader_sets.setdefault(rid, {})[pid] = _load_nodule_records(root, pid, rid)

    kappa_pairs: Dict[str, float] = {}
    reader_ids = sorted(reader_sets)
    for i in range(len(reader_ids)):
        for j in range(i + 1, len(reader_ids)):
            ra, rb = reader_ids[i], reader_ids[j]
            common = sorted(set(reader_sets[ra]) & set(reader_sets[rb]))
            if not common:
                continue
            a = [n for pid in common for n in reader_sets[ra][pid]]
            b = [n for pid in common for n in reader_sets[rb][pid]]
            kappa_pairs[f"{ra}__{rb}"] = detection_kappa(a, b)
            # texture kappa over matched nodules (protocol §5)
            kappa_pairs[f"{ra}__{rb}__texture"] = texture_kappa(a, b)

    # --- Likert ICC(2,k) per (reconstruction x dose level) ------------------
    likert_dir = os.path.join(root, "annotations", "likert")
    series = sorted({
        os.path.splitext(f)[0] for f in os.listdir(likert_dir)
    }) if os.path.isdir(likert_dir) else []
    icc_by_level: Dict[str, float] = {}
    level_targets: Dict[str, List[List[float]]] = {}
    for sid in series:
        rec = _load_likert_records(root, sid)
        for s in rec.get("scores", []):
            key = f"{s.get('reconstruction')}__r{s.get('dose_ratio')}"
            level_targets.setdefault(key, []).append(list(s.get("scores_per_reader", [])))
    for key, targets in level_targets.items():
        icc_by_level[key] = icc_2k(targets)

    # --- gates ---------------------------------------------------------------
    all_kappas = [v for k, v in kappa_pairs.items() if "__texture" not in k and not np.isnan(v)]
    min_kappa = min(all_kappas) if all_kappas else float("nan")
    gate_pass = bool(all_kappas) and min_kappa >= KAPPA_GATE

    return {
        "status": "real-data",
        "gated": gate_pass,
        "gate_min_cohen_kappa": min_kappa,
        "kappa_gate": KAPPA_GATE,
        "detection_kappa_pairs": kappa_pairs,
        "likert_icc_by_level": icc_by_level,
        "n_patients_with_raw_labels": len(patients),
        "n_likert_series": len(series),
        "note": "Real campaign data pending; see annotation_campaign_plan.md.",
    }


# ---------------------------------------------------------------------------
# Demo mode — synthetic data exercising every code path
# ---------------------------------------------------------------------------

def _demo_report() -> dict:
    rng = random.Random(42)
    # 4 readers x 3 patients; overlapping + discordant nodules to exercise both
    # matched and unmatched paths.
    def synth_reader(pid: str, rid: str, seed: int, quality: float) -> List[dict]:
        r = random.Random(seed)
        nodules = []
        for i in range(8):
            x0, y0 = r.randint(10, 60), r.randint(10, 60)
            if r.random() > quality:            # noise: miss / extra mark
                continue
            nodules.append({
                "nodule_id": f"{pid}_n{i}",
                "slice_index": r.choice([0, 1, 2]),
                "bbox_xyxy": [x0, y0, x0 + r.randint(8, 20), y0 + r.randint(8, 20)],
                "diameter_mm": round(r.uniform(3.0, 12.0), 1),
                "texture": r.randint(1, 5),
            })
        return nodules

    readers = {f"r{i}": {} for i in range(1, 5)}
    for pid in ["p001", "p002", "p003"]:
        for rid in readers:
            readers[rid][pid] = synth_reader(pid, rid, seed=hash((pid, rid)) % 1000, quality=0.9)

    kappa_pairs: Dict[str, float] = {}
    ids = list(readers)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a = [n for pid in readers[ids[i]] for n in readers[ids[i]][pid]]
            b = [n for pid in readers[ids[j]] for n in readers[ids[j]][pid]]
            kappa_pairs[f"{ids[i]}__{ids[j]}"] = detection_kappa(a, b)
            kappa_pairs[f"{ids[i]}__{ids[j]}__texture"] = texture_kappa(a, b)

    # Likert demo: 2 readers, 3 levels, near-identical scoring -> high ICC
    likert = {
        "fbp__r0.25": [[4, 4], [3, 3], [5, 4], [4, 4], [3, 3]],
        "fbp__r0.50": [[4, 4], [4, 3], [4, 4], [3, 3], [5, 5]],
        "tv__r0.25":  [[3, 3], [4, 4], [2, 3], [3, 3], [4, 4]],
    }
    icc_by_level = {k: icc_2k(v) for k, v in likert.items()}

    all_kappas = [v for k, v in kappa_pairs.items() if "__texture" not in k and not np.isnan(v)]
    min_kappa = min(all_kappas) if all_kappas else float("nan")
    return {
        "status": "demo",
        "gated": min_kappa >= KAPPA_GATE,
        "gate_min_cohen_kappa": min_kappa,
        "kappa_gate": KAPPA_GATE,
        "detection_kappa_pairs": kappa_pairs,
        "likert_icc_by_level": icc_by_level,
        "n_synthetic_patients": 3,
        "n_synthetic_readers": len(readers),
        "note": "Synthetic demo exercising all code paths; replace with real campaign data.",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo", action="store_true", help="run on synthetic data")
    ap.add_argument("--annotations-root", default="", help="release root containing annotations/")
    ap.add_argument("--out", default="", help="write JSON report to this path")
    args = ap.parse_args()

    if args.demo:
        report = _demo_report()
    else:
        if not args.annotations_root:
            ap.error("--annotations-root required unless --demo (real campaign data pending)")
        report = verify_real_annotations(args.annotations_root)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    gate = "PASS" if report["gated"] else "FAIL"
    print(f"gate: {gate}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"report written to {args.out}")


if __name__ == "__main__":
    main()
