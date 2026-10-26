"""Load trusted local checkpoints and draw unbounded standardized residuals.

Checkpoint contents include optimizer/RNG state and are consequently loaded
with weights_only=False. Only load files produced locally by this pipeline.
The supplied seed and explicit torch Generator do not change global RNG state.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from .models.ddm import ScalarDDM
from .models.ddpm import ScalarDDPM


def resolve_device(device: str = "auto") -> torch.device:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    resolved = torch.device(device)
    if resolved.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable; use device='auto' or 'cpu'")
    return resolved


def build_network(model_id: str, config: dict[str, Any]) -> torch.nn.Module:
    hidden = config.get("hidden_dims", [32, 32])
    if model_id == "D0_ddpm":
        if config.get("ddpm_schedule", "cosine") != "cosine":
            raise ValueError("Only the prescribed cosine DDPM schedule is supported")
        return ScalarDDPM(hidden, steps=int(config.get("ddpm_steps", 100)),
                          cosine_s=float(config.get("ddpm_cosine_s", 0.008)))
    if model_id in {"C0_direct_crps", "D1_ddm_crps", "D2_ddm_tail"}:
        return ScalarDDM(hidden, direct=model_id == "C0_direct_crps")
    raise ValueError(f"Not a trainable neural model: {model_id}. D3/D4 reuse their D1/D2 parents.")


def load_network(checkpoint: str | Path, device: str = "auto"
                 ) -> tuple[torch.nn.Module, dict[str, Any]]:
    resolved = resolve_device(device)
    payload = torch.load(Path(checkpoint), map_location="cpu", weights_only=False)
    # Module initialization draws random weights. Preserve caller CPU RNG;
    # these weights are immediately replaced by the checkpoint state anyway.
    with torch.random.fork_rng(devices=[]):
        model = build_network(payload["model_id"], payload["config"])
    model.load_state_dict(payload["model_state"])
    model.to(resolved).eval()
    return model, payload


def sample_network(checkpoint: str | Path, n: int, seed: int, device: str = "auto",
                   batch_size: int = 4096) -> np.ndarray:
    model, _ = load_network(checkpoint, device)
    generator = torch.Generator(device=next(model.parameters()).device)
    generator.manual_seed(int(seed))
    samples = model.sample(int(n), generator=generator, batch_size=int(batch_size))
    result = samples.detach().cpu().numpy().astype(np.float64)
    if not np.isfinite(result).all():
        raise FloatingPointError("Non-finite raw neural residual draws; no clipping or replacement applied")
    return result
