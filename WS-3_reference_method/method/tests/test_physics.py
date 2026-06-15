import torch

from pwm_ldct_recon.physics import RadonTransform


def _radon(size=16, views=30):
    return RadonTransform(n_views=views, n_dets=size, img_size=size, filter_name="ramp")


def test_forward_shape_and_finiteness():
    R = _radon()
    x = torch.rand(2, 1, 16, 16)
    sino = R.forward(x)
    assert sino.shape == (2, 1, 30, 16)
    assert torch.isfinite(sino).all()


def test_forward_is_linear():
    R = _radon()
    x1, x2 = torch.rand(1, 1, 16, 16), torch.rand(1, 1, 16, 16)
    lhs = R.forward(3.0 * x1 + 2.0 * x2)
    rhs = 3.0 * R.forward(x1) + 2.0 * R.forward(x2)
    assert torch.allclose(lhs, rhs, atol=1e-4)


def test_fbp_warm_start_recovers_structure():
    # The model uses the exact autograd adjoint for data consistency; backproject/FBP is only
    # the warm start, so what matters is that FBP(forward(x)) is positively correlated with x.
    R = RadonTransform(n_views=120, n_dets=32, img_size=32, filter_name="ramp")
    yy, xx = torch.meshgrid(torch.linspace(-1, 1, 32), torch.linspace(-1, 1, 32), indexing="ij")
    x = ((xx ** 2 + yy ** 2) < 0.3).float()[None, None]      # a disk phantom
    recon = R.fbp(R.forward(x)).flatten()
    xf = x.flatten()
    corr = torch.corrcoef(torch.stack([recon, xf]))[0, 1]
    assert corr > 0.5, corr


def test_fbp_runs_and_is_differentiable():
    R = _radon()
    x = torch.rand(1, 1, 16, 16, requires_grad=True)
    recon = R.fbp(R.forward(x))
    assert recon.shape == x.shape and torch.isfinite(recon).all()
    recon.sum().backward()
    assert x.grad is not None and torch.isfinite(x.grad).all()


def test_opnorm_positive():
    assert _radon().opnorm_sq() > 0
