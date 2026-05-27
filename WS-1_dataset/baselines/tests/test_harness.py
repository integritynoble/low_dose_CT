"""Harness tests: model registry, metrics, and a real train-step -> eval -> results.json cycle."""
import json
import os

import pytest
import torch

from pwm_ldct_baselines import evaluate_to_json, get_model, train
from pwm_ldct_baselines import metrics as M
from pwm_ldct_baselines.models import REDCNN


def test_registry():
    assert isinstance(get_model("red_cnn"), REDCNN)
    with pytest.raises(NotImplementedError):
        get_model("diffusion")


def test_redcnn_preserves_shape():
    x = torch.rand(1, 1, 40, 40)
    assert get_model("red_cnn")(x).shape == x.shape


def test_metrics():
    a = torch.rand(1, 1, 32, 32)
    assert M.psnr(a, a.clone()) == float("inf")
    assert M.ssim(a, a.clone()) > 0.999
    b = a + 0.5
    assert M.psnr(b, a) < 50.0
    assert M.lpips(a, a.clone()) is None or isinstance(M.lpips(a, a.clone()), float)


def test_train_eval_cycle(dataset_root, tmp_path):
    ckpt = str(tmp_path / "red_cnn.pt")
    train(dataset_root, ckpt, model_name="red_cnn", split="train", max_steps=2, seed=42, device="cpu")
    assert os.path.exists(ckpt)

    out = str(tmp_path / "results.json")
    res = evaluate_to_json(dataset_root, ckpt, out, split="test", seed=42, device="cpu")
    assert os.path.exists(out)
    assert res["model"] == "red_cnn"
    pd = res["per_dose"]
    for key in ("sim_r010", "sim_r025", "sim_r050", "real"):
        assert key in pd, key
    # simulated dose levels have slices; metrics are real floats
    assert pd["sim_r025"]["n"] > 0
    assert isinstance(pd["sim_r025"]["psnr"], float)
    assert -1.0 <= pd["sim_r025"]["ssim"] <= 1.0
    # the test patient (mayo) has a real low-dose series -> 'real' branch populated
    assert pd["real"]["n"] > 0


def test_results_json_is_serializable(dataset_root, tmp_path):
    ckpt = str(tmp_path / "m.pt")
    train(dataset_root, ckpt, max_steps=1, seed=1, device="cpu")
    out = str(tmp_path / "r.json")
    evaluate_to_json(dataset_root, ckpt, out, split="test", device="cpu")
    json.load(open(out))  # must parse
