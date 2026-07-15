"""Prove the extractors are correct on a synthetic fixture, before the real data lands.

The fixture values are chosen so every expected number is hand-verifiable. In
particular the inter-rater case demonstrates the arithmetic-consistency fix: 5 consensus
nodules over 2 annotated patients is exactly 2.5 per patient -- a division the extractor
computes, so the manuscript can never again print a per-patient mean that disagrees with
its own nodule/patient counts.

Run:  python -m pytest test_extractors.py -q     (from this directory)
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_tables import build
from extract_acquisition import compute_acquisition
from extract_demographics import compute_demographics
from extract_inter_rater import compute_inter_rater

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
META = os.path.join(FIX, "metadata")
MV = os.path.join(FIX, "annotations", "lidc_majority_vote")


def _load():
    from common import load_series_metadata
    return load_series_metadata(META)


def test_demographics_aggregate_and_per_source():
    d = compute_demographics(_load())
    agg = d["aggregate"]
    assert agg["n_patients"] == 4                        # unique canonical keys
    assert math.isclose(agg["age"]["median"], 62.0)      # [60,62,70]
    assert math.isclose(agg["age"]["q1"], 61.0)
    assert math.isclose(agg["age"]["q3"], 66.0)
    assert (agg["age"]["min"], agg["age"]["max"]) == (60.0, 70.0)
    assert (agg["sex"]["M"], agg["sex"]["F"]) == (2, 1)
    assert math.isclose(agg["sex"]["pct_known"], 75.0)   # 3 of 4 known

    lidc = d["by_source"]["lidc"]
    assert lidc["n_patients"] == 2
    assert math.isclose(lidc["age"]["median"], 65.0)     # [60,70]
    assert (lidc["sex"]["M"], lidc["sex"]["F"]) == (1, 1)
    # AAPM demographics are fully stripped -> age unknown, not fabricated
    assert d["by_source"]["aapm"]["age"]["n"] == 0


def test_acquisition_manufacturer_and_kvp():
    a = compute_acquisition(_load())
    assert a["lidc"]["manufacturer"] == {"GE": 1, "Siemens": 1}
    assert a["lidc"]["kvp_typical"] == 120
    assert math.isclose(a["lidc"]["exposure_mas"]["median"], 215.0)   # [200,230]
    assert (a["lidc"]["slice_thickness_mm"]["min"],
            a["lidc"]["slice_thickness_mm"]["max"]) == (1.25, 2.0)
    assert a["aapm"]["manufacturer"] == {"Siemens": 1}
    assert a["mayo"]["kvp_typical"] == 100


def test_inter_rater_is_arithmetically_consistent():
    t = compute_inter_rater(MV)
    assert t["consensus_nodules"] == 5
    assert t["patients_with_consensus_nodule"] == 2
    assert t["max_nodules_per_patient"] == 3
    # the fix: mean-per-patient is a computed division, always == nodules / patients
    assert math.isclose(t["mean_nodules_per_annotated_patient"], 2.5)
    assert math.isclose(t["mean_nodules_per_annotated_patient"],
                        t["consensus_nodules"] / t["patients_with_consensus_nodule"])
    # contributing readers: {4:3, 3:2} -> mean 3.6, agreement 0.9
    assert t["contributing_distribution"] == {"3": 2, "4": 3}
    assert math.isclose(t["mean_contributing_readers"], 3.6)
    assert math.isclose(t["reader_agreement_fraction"], 0.9)
    # pairwise: 3 nodules at C(4,2)/6=1.0 + 2 at C(3,2)/6=0.5 -> (3+1)/5 = 0.8
    assert math.isclose(t["pairwise_agreement"], 0.8)


def test_build_tables_end_to_end(tmp_path):
    out = str(tmp_path / "tables")
    res = build(FIX, out, n_patients_total=1010)
    for stem in ("demographics", "acquisition", "inter_rater"):
        assert os.path.exists(os.path.join(out, f"{stem}.json"))
        assert os.path.exists(os.path.join(out, f"{stem}.tex"))
    # provenance pins the exact inputs consumed (4 metadata + 3 majority-vote = 7)
    assert res["provenance"]["n_files"] == 7
    assert len(res["provenance"]["combined_sha256"]) == 64
    # the LaTeX self-check comment carries the consistent mean
    with open(os.path.join(out, "inter_rater.tex"), encoding="utf-8") as fh:
        assert "2.50 per patient" in fh.read()
    assert res["inter_rater"]["patients_total"] == 1010
