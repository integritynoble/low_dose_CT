#!/usr/bin/env python3
"""Unit tests for the BandER control set (BANDER-1). Pure CPU, no data needed."""
import numpy as np
import pytest

import bander_controls as bc


@pytest.fixture(scope="module")
def fd():
    img, c, r = bc.synthetic_patch()
    return img, c, r


def test_phantom_is_hu_scale_and_deterministic():
    a, ca, ra = bc.synthetic_patch()
    b, cb, rb = bc.synthetic_patch()
    assert np.array_equal(a, b) and ca == cb and ra == rb
    assert -100 < a.min() < 200 and 200 < a.max() < 500   # plausible HU range


def test_bander_of_reference_against_itself_is_one(fd):
    img, _, _ = fd
    assert bc.band_energy_ratio(img, img) == pytest.approx(1.0, rel=1e-9)


@pytest.mark.parametrize("name,fn", [
    ("blur",        lambda x: bc.ctrl_blur(x, 1.0)),
    ("noise",       lambda x: bc.ctrl_noise(x, 20.0, seed=7)),
    ("oversharpen", lambda x: bc.ctrl_oversharpen(x, 1.0)),
    ("ringing",     lambda x: bc.ctrl_ringing(x, 0.25)),
])
def test_controls_are_deterministic_and_shape_preserving(fd, name, fn):
    img, _, _ = fd
    a, b = fn(img), fn(img)
    assert np.array_equal(a, b), f"{name} is not deterministic"
    assert a.shape == img.shape and np.isfinite(a).all()


def test_lesion_erase_is_deterministic_and_local(fd):
    img, c, r = fd
    a = bc.ctrl_lesion_erase(img, c, r)
    b = bc.ctrl_lesion_erase(img, c, r)
    assert np.array_equal(a, b)
    changed = ~np.isclose(a, img)
    frac = changed.mean()
    assert frac < 0.01, f"erasure touched {frac:.3%} of the slice, expected <1%"
    yy, xx = np.ogrid[:img.shape[0], :img.shape[1]]
    disc = (yy - c[0]) ** 2 + (xx - c[1]) ** 2 <= r ** 2
    assert not changed[~disc].any(), "erasure leaked outside the lesion disc"


def test_noise_seed_changes_the_realisation_but_not_the_statistics(fd):
    img, _, _ = fd
    a, b = bc.ctrl_noise(img, 20.0, seed=1), bc.ctrl_noise(img, 20.0, seed=2)
    assert not np.array_equal(a, b)
    assert abs(np.std(a - img) - np.std(b - img)) < 1.0


def test_blur_loses_band_energy_and_noise_adds_it(fd):
    img, _, _ = fd
    assert bc.band_energy_ratio(bc.ctrl_blur(img, 1.0), img) < 1.0
    assert bc.band_energy_ratio(bc.ctrl_noise(img, 20.0, seed=7), img) > 1.0


def test_noise_bander_grows_with_sigma(fd):
    img, _, _ = fd
    vals = [bc.band_energy_ratio(bc.ctrl_noise(img, s, seed=7), img)
            for s in (5.0, 20.0, 60.0)]
    assert vals == sorted(vals), f"not monotone in sigma: {vals}"
