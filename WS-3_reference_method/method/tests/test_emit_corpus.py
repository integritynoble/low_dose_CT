import numpy as np

from pwm_ldct_recon import emit_corpus as ec
from pwm_ldct_recon.config import EnsembleConfig, ReconConfig
from pwm_ldct_recon.data import SyntheticPairs, denormalize
from pwm_ldct_recon.detector import DeterministicStubDetector
from pwm_ldct_recon.ensemble import train_ensemble


def _tiny_models(size=16):
    base = ReconConfig(n_views=18, n_dets=size, slice_size=size, iterations=2,
                       unet_channels=(8, 16), batch_size=2)
    cfg = EnsembleConfig(members=2, seeds=(42, 43), base=base)
    ds = SyntheticPairs(n=4, size=size, seed=0)
    return cfg, train_ensemble(cfg, ds, max_steps=2, estimate_step=False), ds


def _scans(ds, size=16):
    rng = np.random.default_rng(1)
    scans = []
    for vi, vendor in enumerate(("Siemens", "GE")):
        ref = denormalize(ds.full[vi]).astype("f4")[None]
        low = {r: denormalize(np.clip(ds.full[vi] + rng.normal(0, 0.05 / r, ds.full[vi].shape),
                                      0, 1)).astype("f4")[None] for r in (0.10, 0.25, 0.50)}
        scans.append(ec.ScanInput(scan_id=f"scan_{vendor.lower()}_chest", vendor=vendor,
                                  patient_id=f"p{vi+1:03d}", full_dose=ref, low_dose=low))
    return scans


def _scores_fn(vendor, anatomy, r):
    from emit_credentials import AucScores  # sibling tool, path-loaded by emit_corpus.run

    rng = np.random.default_rng(hash((vendor, round(r, 2))) % (2**32))
    n = 60
    return AucScores(a_pos=rng.normal(0.65, 0.18, n), a_neg=rng.normal(0.35, 0.18, n),
                     b_pos=rng.normal(0.65, 0.18, n), b_neg=rng.normal(0.35, 0.18, n))


def test_emit_corpus_end_to_end(tmp_path):
    cfg, models, ds = _tiny_models()
    report = ec.run(tmp_path / "corpus", _scans(ds), models, DeterministicStubDetector(),
                    _scores_fn, cfg=cfg)
    assert report["credentials_ok"], report
    assert report["manifest_ok"], report
    assert report["error_maps_ok"], report
    assert report["n_error_maps_checked"] > 0
    assert not report["schema_errors"], report


def _baseline_scores_fn(method, vendor, anatomy, r):
    from emit_credentials import AucScores

    rng = np.random.default_rng(hash((method, vendor, round(r, 2))) % (2**32))
    n = 60
    return AucScores(a_pos=rng.normal(0.60, 0.18, n), a_neg=rng.normal(0.40, 0.18, n),
                     b_pos=rng.normal(0.65, 0.18, n), b_neg=rng.normal(0.35, 0.18, n))


def test_emit_corpus_with_baselines(tmp_path):
    cfg, models, ds = _tiny_models()
    root = tmp_path / "corpus"
    fbp = ec.FBPBaseline(models[0].physics)
    report = ec.run(root, _scans(ds), models, DeterministicStubDetector(), _scores_fn,
                    cfg=cfg, baselines=[fbp], baseline_scores_fn=_baseline_scores_fn)
    assert report["credentials_ok"] and report["manifest_ok"] and report["error_maps_ok"], report
    assert report["n_baseline_methods"] == 1
    # baseline records exist with the baseline layout: recon.nii.gz, no uncertainty/scan_meta.
    bdir = root / "baselines" / "fbp" / "Siemens" / "scan_siemens_chest" / "r025"
    assert (bdir / "recon.nii.gz").exists()
    assert (bdir / "error_abs.nii.gz").exists()
    assert (bdir / "task_nodule_score.nii.gz").exists()
    assert not (bdir / "uncertainty_sigma.nii.gz").exists()   # single-model baseline (D4)
    assert not (bdir / "recon_mean.nii.gz").exists()
    # baseline credential emitted alongside the reference credential at the same stratum.
    assert (root / "credentials" / "lung_nodule_5mm" / "r025" / "fbp__Siemens.json").exists()
    assert (root / "credentials" / "lung_nodule_5mm" / "r025" / "pwm_ref_v1__Siemens.json").exists()


def test_emit_corpus_baselines_require_scores_fn(tmp_path):
    import pytest

    cfg, models, ds = _tiny_models()
    with pytest.raises(ValueError):
        ec.run(tmp_path / "c", _scans(ds), models, DeterministicStubDetector(), _scores_fn,
               cfg=cfg, baselines=[ec.FBPBaseline(models[0].physics)])


def test_emit_corpus_writes_all_record_maps(tmp_path):
    cfg, models, ds = _tiny_models()
    root = tmp_path / "corpus"
    ec.run(root, _scans(ds), models, DeterministicStubDetector(), _scores_fn, cfg=cfg)
    scan = root / "reconstructions" / "Siemens" / "scan_siemens_chest"
    assert (scan / "r100" / "recon_mean.nii.gz").exists()
    for r in ("r010", "r025", "r050"):
        for m in ("recon_mean", "uncertainty_sigma", "error_abs", "task_nodule_score"):
            assert (scan / r / f"{m}.nii.gz").exists(), (r, m)
    # r=1.00 reference carries no error/task map (manuscript M4).
    assert not (scan / "r100" / "error_abs.nii.gz").exists()
