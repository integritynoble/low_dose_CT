import torch

from pwm_ldct_recon.config import ReconConfig
from pwm_ldct_recon.models import UNetDenoiser, UnrolledRecon
from pwm_ldct_recon.physics import RadonTransform


def test_unet_shape_preserving_and_residual():
    net = UNetDenoiser(channels=(8, 16, 32))
    x = torch.rand(2, 1, 32, 32)
    out = net(x)
    assert out.shape == x.shape and torch.isfinite(out).all()


def test_unet_param_count_reasonable():
    # full S1 config (32,64,128,256) should be on the order of a few million params.
    net = UNetDenoiser(channels=(32, 64, 128, 256))
    n = sum(p.numel() for p in net.parameters())
    assert 1_000_000 < n < 12_000_000, n


def test_unrolled_forward_shape():
    cfg = ReconConfig(n_views=24, n_dets=32, slice_size=32, iterations=3, unet_channels=(8, 16))
    R = RadonTransform(n_views=cfg.n_views, n_dets=cfg.n_dets, img_size=cfg.slice_size)
    model = UnrolledRecon(R, cfg=cfg, estimate_step=False)
    y = torch.rand(2, 1, 24, 32)
    recon = model(y)
    assert recon.shape == (2, 1, 32, 32) and torch.isfinite(recon).all()


def test_tau_is_positive_and_grad_flows():
    cfg = ReconConfig(n_views=24, n_dets=32, slice_size=32, iterations=2, unet_channels=(8, 16))
    R = RadonTransform(n_views=cfg.n_views, n_dets=cfg.n_dets, img_size=cfg.slice_size)
    model = UnrolledRecon(R, cfg=cfg, estimate_step=False)
    assert float(model.tau.detach()) > 0
    y = torch.rand(1, 1, 24, 32)
    model.train()
    loss = model(y).pow(2).mean()
    loss.backward()
    # gradient must reach both the denoiser and the learned step size (unrolling works).
    assert model.log_tau.grad is not None and torch.isfinite(model.log_tau.grad).all()
    assert any(p.grad is not None for p in model.denoiser.parameters())
