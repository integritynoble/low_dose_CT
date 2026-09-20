"""Patient clustering must retain multiplicity and the pairing of observations."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest


SPEC = importlib.util.spec_from_file_location(
    "bootstrap_lidc_sim", Path(__file__).resolve().parents[1] / "bootstrap_lidc_sim.py"
)
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class RepeatedPatientDraw:
    """Force A twice, B once, C zero times; all are valid replacement draws."""

    def __init__(self):
        self.calls = 0

    def choice(self, patients, size, replace):
        np.testing.assert_array_equal(patients, ["A", "B", "C"])
        assert size == 3 and replace is True
        self.calls += 1
        return np.array(["A", "B", "A"])


def model_doc(name="red_cnn", values=(0.0, 2.0, 10.0, 100.0), ids=("A", "A", "B", "C")):
    return {
        "model": name,
        "per_seed": {
            seed: {"per_dose": {
                dose: {"detectability": {"per_slice": {
                    "cnr": list(values), "patient_id": list(ids)
                }}}
                for dose in bootstrap.DOSES
            }}
            for seed in ("42", "7")
        },
    }


def test_repeated_patient_draw_repeats_every_slice_in_the_cluster():
    ids = np.array(["A", "A", "B", "C"])
    idx = bootstrap._patient_indices(ids, RepeatedPatientDraw())
    np.testing.assert_array_equal(idx, [0, 1, 2, 0, 1])
    # Unequal block sizes are intentional: preserve the pooled-slice estimand.
    assert bootstrap._resample_rep(
        np.array([0.0, 2.0, 10.0, 100.0]), ids, False, RepeatedPatientDraw(), "patient"
    ) == pytest.approx(2.8)


def test_patient_draw_is_shared_across_doses(monkeypatch):
    doc = model_doc()
    for seed in doc["per_seed"].values():
        for scale, dose in enumerate(bootstrap.DOSES, 1):
            seed["per_dose"][dose]["detectability"]["per_slice"]["cnr"] = [
                scale * x for x in (0.0, 2.0, 10.0, 100.0)
            ]
    seen = []

    def capture_knee(rep):
        seen.append(dict(rep))
        return None, "not_reached"

    monkeypatch.setattr(bootstrap, "knee", capture_knee)
    rng = RepeatedPatientDraw()
    result = bootstrap.bootstrap_model(doc, "distinct", 2, rng, unit="patient")
    assert rng.calls == 2  # one cluster draw per replicate, not one per dose
    assert result["n_patients"] == 3
    for rep in seen[1:]:
        assert list(rep.values()) == pytest.approx([2.8, 5.6, 8.4])


def test_paired_method_ratio_uses_the_same_repeated_blocks():
    docs = {
        "blur": model_doc("blur"),
        "red_cnn": model_doc(values=(2.0, 4.0, 5.0, 100.0)),
    }
    result = bootstrap.bootstrap_separation(
        docs, "distinct", 2, RepeatedPatientDraw(), unit="patient"
    )
    for row in result["blur_vs_red_cnn"].values():
        assert row["ci95"] == pytest.approx([2.8 / 3.4, 2.8 / 3.4])
        assert row["n_patients"] == 3


@pytest.mark.parametrize("ids", [[], ["A"], ["A", "A", None, "C"],
                                 ["A", "A", " ", "C"], ["A", "A", 3, "C"]])
def test_malformed_patient_map_is_rejected(ids):
    with pytest.raises(SystemExit, match="patient_id"):
        bootstrap.patient_ids_for(model_doc(ids=ids), "42", bootstrap.DOSES[0])


def test_missing_patient_map_is_rejected():
    doc = model_doc()
    del doc["per_seed"]["42"]["per_dose"][bootstrap.DOSES[0]]["detectability"]["per_slice"]["patient_id"]
    with pytest.raises(SystemExit, match="no per_slice.patient_id"):
        bootstrap.bootstrap_model(doc, "distinct", 1, RepeatedPatientDraw(), unit="patient")


def test_scalar_patient_map_is_rejected():
    doc = model_doc()
    doc["per_seed"]["42"]["per_dose"][bootstrap.DOSES[0]]["detectability"]["per_slice"]["patient_id"] = "AABC"
    with pytest.raises(SystemExit, match="must be a JSON list"):
        bootstrap.patient_ids_for(doc, "42", bootstrap.DOSES[0])


@pytest.mark.parametrize("dimension", ["seed", "dose"])
def test_differing_maps_cannot_authorize_paired_draws(dimension):
    doc = model_doc()
    changed_seed = "7" if dimension == "seed" else "42"
    changed_dose = bootstrap.DOSES[0] if dimension == "seed" else bootstrap.DOSES[1]
    doc["per_seed"][changed_seed]["per_dose"][changed_dose]["detectability"]["per_slice"]["patient_id"] = [
        "A", "B", "B", "C"
    ]
    if dimension == "dose":
        doc["per_seed"]["7"]["per_dose"][changed_dose]["detectability"]["per_slice"]["patient_id"] = [
            "A", "B", "B", "C"
        ]
    with pytest.raises(SystemExit, match=f"differ between {dimension}s"):
        bootstrap.bootstrap_model(doc, "distinct", 1, RepeatedPatientDraw(), unit="patient")


def test_unequal_paired_pools_are_rejected_instead_of_truncated():
    docs = {"blur": model_doc("blur"),
            "red_cnn": model_doc(values=(1.0, 2.0, 3.0), ids=("A", "A", "B"))}
    with pytest.raises(SystemExit, match="different lengths"):
        bootstrap.bootstrap_separation(docs, "distinct", 1, RepeatedPatientDraw(), unit="patient")


def test_differing_patient_maps_between_methods_are_rejected():
    docs = {"blur": model_doc("blur"),
            "red_cnn": model_doc(ids=("A", "B", "B", "C"))}
    with pytest.raises(SystemExit, match="differ between paired models"):
        bootstrap.bootstrap_separation(docs, "distinct", 1, RepeatedPatientDraw(), unit="patient")


def test_patient_mode_rejects_seed_pooled_replicates():
    with pytest.raises(SystemExit, match="requires --pooling distinct"):
        bootstrap.bootstrap_model(model_doc(), "seed_pooled", 1, RepeatedPatientDraw(), unit="patient")


class ForcedPatientDraws:
    def __init__(self, labels):
        self.labels = iter(labels)

    def choice(self, patients, size, replace):
        assert size == len(patients) and replace
        return np.repeat(next(self.labels), size)


def dose_curve_doc(rows):
    doc = model_doc(ids=("A", "B", "C"), values=rows[0])
    for seed in doc["per_seed"].values():
        for dose, values in zip(bootstrap.DOSES, rows):
            seed["per_dose"][dose]["detectability"]["per_slice"]["cnr"] = list(values)
    return doc


def test_observed_left_boundary_does_not_collapse_replacement_interval():
    # Full sample crosses at/below 0.1; all-A draws instead cross at 0.175.
    doc = dose_curve_doc([(1.0, 4.0, 5.0), (5.0, 6.0, 7.0), (9.0, 10.0, 11.0)])
    result = bootstrap.bootstrap_model(
        doc, "distinct", 4, ForcedPatientDraws(["A", "A", "B", "B"]), unit="patient"
    )
    assert result["observed_kind"] == "below_r010"
    assert result["knee_95ci"] == pytest.approx([0.1, 0.175])
    assert result["knee_95ci_status"] == "percentile_with_left_censoring"
    assert result["knee_left_censoring"] == {
        "lowest_tested_dose": 0.1, "observed": True, "n_draws": 2
    }


def test_all_left_censored_draws_are_labeled_instead_of_exact_minimum():
    result = bootstrap.bootstrap_model(
        model_doc(values=(4.0, 4.0, 5.0, 6.0)), "distinct", 2,
        RepeatedPatientDraw(), unit="patient"
    )
    assert result["knee_95ci"] == [0.1, 0.1]
    assert result["knee_95ci_status"] == "percentile_with_left_censoring"
    assert result["knee_left_censoring"]["n_draws"] == 2


@pytest.mark.parametrize("bad", ["not_reached", "nan"])
def test_incomplete_knee_draws_withhold_interval_instead_of_dropping_draws(bad):
    low = float("nan") if bad == "nan" else 1.0
    doc = dose_curve_doc([(low, 4.0, 5.0), (low, 6.0, 7.0), (low, 9.0, 10.0)])
    result = bootstrap.bootstrap_model(
        doc, "distinct", 2, ForcedPatientDraws(["A", "B"]), unit="patient"
    )
    assert result["knee_95ci"] is None
    assert result["knee_95ci_status"] == "unavailable_incomplete_draws"
    assert result["draw_kinds"][bad] == 1
    assert result["draw_kinds"]["below_r010"] == 1


def test_nonfinite_later_dose_does_not_hide_behind_early_boundary_crossing():
    doc = dose_curve_doc([(4.0, 4.0, 5.0), (float("nan"), 6.0, 7.0), (9.0, 9.0, 10.0)])
    result = bootstrap.bootstrap_model(
        doc, "distinct", 2, ForcedPatientDraws(["A", "B"]), unit="patient"
    )
    assert result["knee_95ci"] is None
    assert result["draw_kinds"]["nan"] == 1


def test_zero_patient_draws_have_no_knee_interval():
    result = bootstrap.bootstrap_model(model_doc(), "distinct", 0, RepeatedPatientDraw(), unit="patient")
    assert result["knee_95ci"] is None
    assert result["knee_95ci_status"] == "unavailable_no_draws"
