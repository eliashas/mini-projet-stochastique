"""Scalar DDPM: cosine corruption and unbounded ancestral residual draws.

The network predicts Gaussian noise, not a future temperature. Indices 1..K
refer to noisy states; index 0 in the stored schedule is the clean state.
"""
from __future__ import annotations

import math
from typing import Sequence

import torch
from torch import nn


def scalar_mlp(inputs: int, hidden_dims: Sequence[int] = (32, 32)) -> nn.Sequential:
    layers: list[nn.Module] = []
    previous = inputs
    for hidden in hidden_dims:
        if int(hidden) < 1:
            raise ValueError("All hidden dimensions must be positive")
        layers.extend((nn.Linear(previous, int(hidden)), nn.SiLU()))
        previous = int(hidden)
    layers.append(nn.Linear(previous, 1))
    return nn.Sequential(*layers)


def cosine_schedule(steps: int = 100, s: float = 0.008) -> dict[str, torch.Tensor]:
    """Return padded DDPM arrays in float64; beta is capped at 0.999.

    After clipping beta, alpha_bar is recomputed by cumulative multiplication,
    so forward and backward transitions use exactly the same schedule.
    """
    if steps < 2 or s < 0:
        raise ValueError("The cosine schedule requires steps >= 2 and s >= 0")
    time = torch.arange(steps + 1, dtype=torch.float64) / steps
    target = torch.cos((time + s) / (1.0 + s) * math.pi / 2).square()
    target = target / target[0]
    beta = torch.zeros(steps + 1, dtype=torch.float64)
    beta[1:] = (1.0 - target[1:] / target[:-1]).clamp(0.0, 0.999)
    alpha = 1.0 - beta
    alpha_bar = torch.cumprod(alpha, dim=0)
    posterior_variance = torch.zeros_like(beta)
    posterior_variance[1:] = beta[1:] * (1.0 - alpha_bar[:-1]) / (1.0 - alpha_bar[1:])
    if alpha_bar[-1].item() >= 1e-3:
        raise ValueError("Cosine schedule did not reach a noise-dominant endpoint")
    return {"beta": beta, "alpha": alpha, "alpha_bar": alpha_bar,
            "posterior_variance": posterior_variance}


class ScalarDDPM(nn.Module):
    def __init__(self, hidden_dims: Sequence[int] = (32, 32), steps: int = 100,
                 cosine_s: float = 0.008):
        super().__init__()
        self.steps = int(steps)
        self.hidden_dims = tuple(int(v) for v in hidden_dims)
        self.cosine_s = float(cosine_s)
        self.network = scalar_mlp(2, self.hidden_dims)
        for name, value in cosine_schedule(self.steps, self.cosine_s).items():
            self.register_buffer(name, value.to(dtype=torch.float32))

    def forward(self, z_noisy: torch.Tensor, normalized_time: torch.Tensor) -> torch.Tensor:
        return self.network(torch.stack((z_noisy, normalized_time), dim=-1)).squeeze(-1)

    def corrupt(self, z: torch.Tensor, k: torch.Tensor, noise: torch.Tensor) -> torch.Tensor:
        return self.alpha_bar[k].sqrt() * z + (1.0 - self.alpha_bar[k]).sqrt() * noise

    def reverse_step(self, z: torch.Tensor, k: int, noise: torch.Tensor | None = None) -> torch.Tensor:
        if not 1 <= k <= self.steps:
            raise ValueError("Reverse step index must be between 1 and K")
        t = torch.full_like(z, float(k) / self.steps)
        epsilon_hat = self(z, t)
        mean = (z - self.beta[k] / (1.0 - self.alpha_bar[k]).sqrt() * epsilon_hat) / self.alpha[k].sqrt()
        if k == 1:
            return mean  # no random noise in the final transition
        if noise is None:
            raise ValueError("An explicit noise tensor is required for k > 1")
        return mean + self.posterior_variance[k].sqrt() * noise

    @torch.no_grad()
    def sample(self, n: int, generator: torch.Generator, batch_size: int = 4096) -> torch.Tensor:
        if n < 0 or batch_size < 1:
            raise ValueError("n must be nonnegative and batch_size positive")
        device = self.beta.device
        chunks = []
        for start in range(0, n, batch_size):
            count = min(batch_size, n - start)
            z = torch.randn(count, device=device, generator=generator)
            for k in range(self.steps, 0, -1):
                noise = (torch.randn(count, device=device, generator=generator) if k > 1 else None)
                z = self.reverse_step(z, k, noise)
            chunks.append(z)
        return torch.cat(chunks) if chunks else torch.empty(0, device=device)


DDPM = ScalarDDPM
