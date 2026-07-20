import numpy as np

from pwm_ldct_loader import LowDoseCTDataset
from pwm_ldct_loader.schema import SAMPLE_KEYS


def test_len_and_required_keys(fixture_root):
    ds = LowDoseCTDataset(root=fixture_root, split="train", backend="numpy")
    assert len(ds) == 4  # 2 series x 2 slices
    sample = ds[0]
    for k in SAMPLE_KEYS:
        assert k in sample, f"missing sample key {k}"


def test_shapes_and_types(fixture_root):
    ds = LowDoseCTDataset(root=fixture_root, split="train", backend="numpy")
    for i in range(len(ds)):
        s = ds[i]
        assert isinstance(s["full_dose"], np.ndarray)
        assert s["full_dose"].shape == (8, 8)
        assert s["full_dose"].dtype == np.float32
        assert s["low_dose"].shape == (8, 8)
        assert s["source"] in ("lidc", "aapm", "mayo")
        assert s["low_dose_kind"] in ("real", "sim")
        assert isinstance(s["slice_index"], int)
        assert isinstance(s["annotations"], dict)
        assert isinstance(s["metadata"], dict)


def test_real_vs_sim_and_projection_presence(fixture_root):
    ds = LowDoseCTDataset(root=fixture_root, split="train", backend="numpy")
    by_source = {}
    for i in range(len(ds)):
        s = ds[i]
        by_source.setdefault(s["source"], []).append(s)
    # sinogram is always None at the slice level; projections are series-level
    assert all(s["sinogram"] is None for vs in by_source.values() for s in vs)
    # LIDC: simulated low-dose, no projections
    assert all(s["low_dose_kind"] == "sim" and not s["has_projections"] for s in by_source["lidc"])
    # AAPM: real low-dose preferred, projections present
    assert all(s["low_dose_kind"] == "real" and s["has_projections"] for s in by_source["aapm"])
    assert by_source["aapm"][0]["dose_ratio"] == 0.25


def test_series_level_projections(fixture_root):
    ds = LowDoseCTDataset(root=fixture_root, split="train", backend="numpy")
    sid = next(ds[i]["series_id"] for i in range(len(ds)) if ds[i]["source"] == "aapm")
    proj = ds.get_series_projections(sid)
    assert proj is not None
    assert proj["full_dose"].shape == (5, 12, 4)         # native [V, C, R]
    assert proj["geometry"]["vendor"] == "SIEMENS"
    assert proj["geometry"]["n_det_channels"] == 12
    # LIDC series have no projections
    lsid = next(ds[i]["series_id"] for i in range(len(ds)) if ds[i]["source"] == "lidc")
    assert ds.get_series_projections(lsid) is None


def test_sources_filter(fixture_root):
    ds = LowDoseCTDataset(root=fixture_root, split="train", sources=["aapm"], backend="numpy")
    assert {ds[i]["source"] for i in range(len(ds))} == {"aapm"}


def test_prefer_real_false_uses_sim(fixture_root):
    ds = LowDoseCTDataset(root=fixture_root, split="train", sources=["aapm"],
                          prefer_real_ld=False, dose_ratio=0.10, backend="numpy")
    assert all(ds[i]["low_dose_kind"] == "sim" for i in range(len(ds)))


def test_resample_changes_inplane_shape(fixture_root):
    ds = LowDoseCTDataset(root=fixture_root, split="train", resample_spacing=0.35, backend="numpy")
    s = ds[0]
    # native 0.7 mm -> 0.35 mm doubles each in-plane dimension (8 -> 16)
    assert s["full_dose"].shape == (16, 16)


def test_annotations_attached_to_correct_slice(fixture_root):
    ds = LowDoseCTDataset(root=fixture_root, split="train", sources=["lidc"], backend="numpy")
    slice0 = [ds[i] for i in range(len(ds)) if ds[i]["slice_index"] == 0][0]
    slice1 = [ds[i] for i in range(len(ds)) if ds[i]["slice_index"] == 1][0]
    assert len(slice0["annotations"]["nodules"]) == 1
    assert len(slice1["annotations"]["nodules"]) == 0


def test_per_source_roots_signature(fixture_root):
    # the manuscript Usage Notes signature
    ds = LowDoseCTDataset(root_lidc=fixture_root, split="train", sources=["lidc"], backend="numpy")
    assert len(ds) == 2
    assert {ds[i]["source"] for i in range(len(ds))} == {"lidc"}
