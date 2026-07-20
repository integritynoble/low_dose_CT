"""RED-CNN (Chen et al., "Low-Dose CT with a Residual Encoder-Decoder CNN", IEEE TMI 2017).

Faithful architecture: 5 conv (encoder) + 5 transposed-conv (decoder), 96 channels, 5x5 valid
kernels, ReLU, with three residual shortcuts (input, after conv2, after conv4). Size-preserving
overall (the symmetric valid conv/deconv pair restores the spatial dimensions).
"""
from __future__ import annotations

import torch
import torch.nn as nn


class REDCNN(nn.Module):
    def __init__(self, channels: int = 96, kernel: int = 5):
        super().__init__()
        c, k = channels, kernel
        self.conv1 = nn.Conv2d(1, c, k)
        self.conv2 = nn.Conv2d(c, c, k)
        self.conv3 = nn.Conv2d(c, c, k)
        self.conv4 = nn.Conv2d(c, c, k)
        self.conv5 = nn.Conv2d(c, c, k)
        self.tconv1 = nn.ConvTranspose2d(c, c, k)
        self.tconv2 = nn.ConvTranspose2d(c, c, k)
        self.tconv3 = nn.ConvTranspose2d(c, c, k)
        self.tconv4 = nn.ConvTranspose2d(c, c, k)
        self.tconv5 = nn.ConvTranspose2d(c, 1, k)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual_1 = x
        out = self.relu(self.conv1(x))
        out = self.relu(self.conv2(out))
        residual_2 = out
        out = self.relu(self.conv3(out))
        out = self.relu(self.conv4(out))
        residual_3 = out
        out = self.relu(self.conv5(out))
        out = self.tconv1(out)
        out = self.relu(out + residual_3)
        out = self.relu(self.tconv2(out))
        out = self.tconv3(out)
        out = self.relu(out + residual_2)
        out = self.relu(self.tconv4(out))
        out = self.tconv5(out)
        out = self.relu(out + residual_1)
        return out
