"""Invalid CNR values must not become table numbers or nonstandard JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import extract_baselines_tables as tables


INVALID = [float("nan"), float("inf"), float("-inf"), True, False]
INVALID_IDS = ["NaN", "positive-infinity", "negative-infinity", "true", "false"]


@pytest.fixture
def collect_one(tmp_path, monkeypatch):
    """Exercise the real collector with one model/dose and controlled source data."""
    monkeypatch.setattr(tables, "MODELS", ["red_cnn"])
    monkeypatch.setattr(tables, "DOSES", ["sim_r010"])

    def run(mean, median=None, seed_medians=None):
        doc = {
            "aggregate": {"sim_r010": {
                "psnr": {"mean": 40.0, "n_seeds": 2},
                "ssim": {"mean": 0.95},
                "lpips": {"mean": 0.02},
                "cho_auc_mean": {"mean": 0.9},
                "cnr_mean": {"mean": mean},
                "cnr_median": {"mean": median},
            }},
            "per_seed": {
                str(seed): {"per_dose": {"sim_r010": {
                    "detectability": {"cnr_median": value},
                }}}
                for seed, value in enumerate(seed_medians or [])
            },
        }
        source = tmp_path / "red_cnn_results_det_full764.json"
        # Python's parser accepts NaN/Infinity from historical result files;
        # validation must reject them as CNR or use the declared finite fallback.
        source.write_text(json.dumps(doc), encoding="utf-8")
        result = tables.collect(str(tmp_path))
        return result["per_model"]["red_cnn"]["per_dose"]["sim_r010"]

    return run


@pytest.mark.parametrize("value", INVALID + [None, "2.5"],
                         ids=INVALID_IDS + ["missing", "numeric-string"])
def test_non_numeric_or_nonfinite_values_are_not_finite(value):
    assert not tables._finite(value)


@pytest.mark.parametrize("value", [0, 2, -3, 0.0, 2.5, -0.5, 1e308])
def test_finite_values_are_preserved(collect_one, value):
    assert tables._finite(value)
    row = collect_one(value, median=99.0)
    assert row["cnr"] == value
    assert row["cnr_statistic"] == "slice_mean"


@pytest.mark.parametrize("mean", INVALID, ids=INVALID_IDS)
def test_invalid_mean_uses_finite_aggregate_median(collect_one, mean):
    row = collect_one(mean, median=2.5)
    assert row["cnr"] == 2.5
    assert row["cnr_statistic"] == "slice_median"


@pytest.mark.parametrize("mean", INVALID, ids=INVALID_IDS)
@pytest.mark.parametrize("median", INVALID + [None], ids=INVALID_IDS + ["missing"])
def test_invalid_mean_and_invalid_fallback_are_rejected(collect_one, mean, median):
    with pytest.raises(SystemExit, match="no finite CNR statistic available"):
        collect_one(mean, median=median)


def test_finite_seed_medians_keep_the_declared_average(collect_one):
    row = collect_one(float("inf"), seed_medians=[2.0, 4.0])
    assert row["cnr"] == 3.0
    assert row["cnr_statistic"] == "slice_median"


@pytest.mark.parametrize("value", INVALID, ids=INVALID_IDS)
def test_invalid_seed_median_is_not_converted_or_silently_dropped(collect_one, value):
    with pytest.raises(SystemExit, match="no finite CNR statistic available"):
        collect_one(float("nan"), seed_medians=[2.0, value])


def test_sanitized_nonfinite_values_produce_standard_json():
    value = {"mean": float("nan"), "nested": [float("inf"), float("-inf"), 2.5],
             "flag": True}
    sanitized = tables._sanitize(value)
    assert sanitized == {"mean": None, "nested": [None, None, 2.5], "flag": True}
    assert json.loads(json.dumps(sanitized, allow_nan=False)) == sanitized
