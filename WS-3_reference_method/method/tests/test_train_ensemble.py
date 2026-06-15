import torch

from pwm_ldct_recon.config import EnsembleConfig, ReconConfig
from pwm_ldct_recon.data import SyntheticPairs
from pwm_ldct_recon.ensemble import (ensemble_infer, load_ensemble, save_ensemble,
                                     train_ensemble)
from pwm_ldct_recon.train import train_member


def _cfg(**kw):
    base = dict(n_views=24, n_dets=32, slice_size=32, iterations=2, unet_channels=(8, 16),
                batch_size=2, peak_lr=1e-3)
    base.update(kw)
    return ReconConfig(**base)


def test_train_member_runs_and_is_finite():
    ds = SyntheticPairs(n=6, size=32, seed=0)
    res = train_member(_cfg(seed=42), ds, max_steps=4, estimate_step=False)
    assert res.steps == 4
    assert res.final_loss == res.final_loss  # not NaN


def test_train_member_is_deterministic_given_seed():
    ds = SyntheticPairs(n=6, size=32, seed=0)
    a = train_member(_cfg(seed=42), ds, max_steps=3, estimate_step=False).final_loss
    b = train_member(_cfg(seed=42), ds, max_steps=3, estimate_step=False).final_loss
    assert abs(a - b) < 1e-6


def test_ensemble_infer_shapes_and_sigma_nonneg():
    ds = SyntheticPairs(n=6, size=32, seed=0)
    cfg = EnsembleConfig(members=3, seeds=(42, 43, 44), base=_cfg())
    models = train_ensemble(cfg, ds, max_steps=2, estimate_step=False)
    y = torch.rand(2, 1, 24, 32)
    res = ensemble_infer(models, y)
    assert res.mean.shape == (2, 1, 32, 32)
    assert res.sigma.shape == (2, 1, 32, 32)
    assert (res.sigma >= 0).all()
    assert res.members.shape == (3, 2, 1, 32, 32)


def test_single_member_sigma_is_zero():
    ds = SyntheticPairs(n=4, size=32, seed=0)
    cfg = EnsembleConfig(members=1, seeds=(42,), base=_cfg())
    models = train_ensemble(cfg, ds, max_steps=1, estimate_step=False)
    res = ensemble_infer(models, torch.rand(1, 1, 24, 32))
    assert torch.allclose(res.sigma, torch.zeros_like(res.sigma))


def test_save_load_roundtrip(tmp_path):
    ds = SyntheticPairs(n=4, size=32, seed=0)
    cfg = EnsembleConfig(members=2, seeds=(42, 43), base=_cfg())
    models = train_ensemble(cfg, ds, max_steps=1, estimate_step=False)
    p = tmp_path / "ens.pt"
    save_ensemble(models, str(p))
    loaded = load_ensemble(cfg, str(p), estimate_step=False)
    y = torch.rand(1, 1, 24, 32)
    a = ensemble_infer(models, y).mean
    b = ensemble_infer(loaded, y).mean
    assert torch.allclose(a, b, atol=1e-5)
