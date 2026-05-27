"""In-repo projection-domain low-dose simulator (manuscript Eq. 1)."""
import numpy as np

from pwm_ldct_prep import lowdose_sim


def _phantom(n=48):
    ys, xs = np.mgrid[0:n, 0:n]
    c = (n - 1) / 2.0
    img = np.full((1, n, n), -1000.0, np.float32)             # air
    img[0][(xs - c) ** 2 + (ys - c) ** 2 <= (n / 3) ** 2] = 40.0   # soft-tissue disk (~40 HU)
    return img


def test_model_name_is_inrepo_when_pwm_core_absent():
    # pwm_core is not installed in this environment -> the in-repo Eq.1 model is used
    assert lowdose_sim.model_name() == "pwm_ldct_prep.lowdose_sim:projection_domain_v1"


def test_shape_finite_and_noise_scales_with_dose():
    vol = _phantom(48)
    low25 = lowdose_sim.simulate(vol, 0.25, seed=42)
    low10 = lowdose_sim.simulate(vol, 0.10, seed=42)
    assert low25.shape == vol.shape and low25.dtype == np.float32
    assert np.isfinite(low25).all() and np.isfinite(low10).all()
    # projection-domain Poisson noise: lower dose -> more inserted noise
    n25 = float(np.std(low25 - vol))
    n10 = float(np.std(low10 - vol))
    assert n10 > n25 > 0.0, (n10, n25)


def test_deterministic_given_seed():
    vol = _phantom(40)
    a = lowdose_sim.simulate(vol, 0.25, seed=7)
    b = lowdose_sim.simulate(vol, 0.25, seed=7)
    assert np.array_equal(a, b)
