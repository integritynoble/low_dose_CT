"""Training loop for a baseline reconstruction model (low-dose -> full-dose, MSE/Adam)."""
from __future__ import annotations

from typing import Optional, Sequence

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from pwm_ldct_loader import seed_everything

from .data import PairedSlices
from .models import get_model


def _device(name: Optional[str]) -> str:
    return name or ("cuda" if torch.cuda.is_available() else "cpu")


def train(root: str, out_ckpt: str, model_name: str = "red_cnn", split: str = "train",
          epochs: int = 1, lr: float = 1e-4, batch_size: int = 1, seed: int = 42,
          max_steps: Optional[int] = None, sources: Optional[Sequence[str]] = None,
          device: Optional[str] = None, num_workers: int = 0) -> str:
    seed_everything(seed)
    dev = _device(device)
    model = get_model(model_name).to(dev)
    loader = DataLoader(PairedSlices(root, split, seed=seed, sources=sources),
                        batch_size=batch_size, shuffle=True, num_workers=num_workers,
                        persistent_workers=num_workers > 0)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    model.train()
    step = 0
    for ep in range(epochs):
        for low, full, *_ in loader:
            low, full = low.to(dev), full.to(dev)
            opt.zero_grad()
            loss = loss_fn(model(low), full)
            loss.backward()
            opt.step()
            step += 1
            if step % 50 == 0:
                print(f"epoch {ep} step {step}  loss={loss.item():.6f}", flush=True)
            if max_steps and step >= max_steps:
                break
        if max_steps and step >= max_steps:
            break
    torch.save({"model": model_name, "state_dict": model.state_dict(), "seed": seed,
                "steps": step}, out_ckpt)
    print(f"saved checkpoint -> {out_ckpt} ({step} steps)", flush=True)
    return out_ckpt
