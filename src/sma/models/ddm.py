"""Stochastic scalar denoiser scored with an ensemble proper-score estimate.

Unlike DDPM, the output is a clean residual draw with an independent latent.
An ensemble shares corruption u and time t, but has M independent latents.
Future inference always uses t=1; no future target is an input.
"""
from __future__ import annotations

from typing import Sequence

import torch
from torch import nn

from .ddpm import scalar_mlp


class ScalarDDM(nn.Module):
    def __init__(self, hidden_dims: Sequence[int] = (32, 32), direct: bool = False):
        super().__init__()
        self.hidden_dims = tuple(int(v) for v in hidden_dims)
        self.direct = bool(direct)
        self.network = scalar_mlp(3, self.hidden_dims)

    def forward(self, u: torch.Tensor, t: torch.Tensor, latent: torch.Tensor) -> torch.Tensor:
        return self.network(torch.stack((u, t, latent), dim=-1)).squeeze(-1)

    def ensemble_inputs(self, z: torch.Tensor, members: int, generator: torch.Generator
                        ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        if z.ndim != 1 or members < 2:
            raise ValueError("Expected z of shape (B,) and at least two ensemble members")
        count = z.shape[0]
        if self.direct:
            u = torch.zeros_like(z)
            t = torch.ones_like(z)
        else:
            t = torch.rand(count, device=z.device, generator=generator)
            corruption = torch.randn(count, device=z.device, generator=generator)
            u = (1.0 - t) * z + t * corruption
        latent = torch.randn(count, members, device=z.device, generator=generator)
        return u[:, None].expand(-1, members), t[:, None].expand(-1, members), latent

    def training_ensemble(self, z: torch.Tensor, members: int,
                          generator: torch.Generator) -> torch.Tensor:
        return self(*self.ensemble_inputs(z, members, generator))

    @torch.no_grad()
    def sample(self, n: int, generator: torch.Generator, batch_size: int = 4096) -> torch.Tensor:
        if n < 0 or batch_size < 1:
            raise ValueError("n must be nonnegative and batch_size positive")
        device = next(self.parameters()).device
        chunks = []
        for start in range(0, n, batch_size):
            count = min(batch_size, n - start)
            u = (torch.zeros(count, device=device) if self.direct else
                 torch.randn(count, device=device, generator=generator))
            latent = torch.randn(count, device=device, generator=generator)
            chunks.append(self(u, torch.ones(count, device=device), latent))
        return torch.cat(chunks) if chunks else torch.empty(0, device=device)


DDM = ScalarDDM
