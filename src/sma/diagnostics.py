"""Probabilistic diagnostics using empirical ensembles, in degrees Celsius."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .scores import crps_rows


def evaluate(samples, observations, threshold: float, variable: str, years=None) -> dict:
    """Return metrics per row and aggregate them, keeping every observation.

    PIT is (number of members < y + half number == y)/N. This deterministic
    mid-rank convention handles repeated empirical-residual forecasts explicitly.
    The Brier event uses strict > threshold for maxima and < for minima.
    """
    samples = np.asarray(samples, dtype=np.float64)
    observations = np.asarray(observations, dtype=np.float64).reshape(-1)
    if samples.ndim != 2 or samples.shape[0] != len(observations) or samples.shape[1] < 1:
        raise ValueError("Expected samples (number of years, ensemble size) and one observation per row.")
    if variable not in {"max", "min"}:
        raise ValueError("variable must be 'max' or 'min'")
    if not np.isfinite(samples).all() or not np.isfinite(observations).all() or not np.isfinite(threshold):
        raise ValueError("Diagnostics require finite samples, observations and threshold.")
    years = np.arange(len(observations)) if years is None else np.asarray(years)
    if len(years) != len(observations):
        raise ValueError("years must have one entry per row")
    mean = samples.mean(axis=1)
    quantiles = np.quantile(samples, [.05, .10, .25, .50, .75, .90, .95], axis=1)
    frame = pd.DataFrame({"year": years, "observation": observations, "mean": mean,
                          "std": samples.std(axis=1), "bias": mean - observations,
                          "median_ae": np.abs(quantiles[3] - observations)})
    for q, values in zip(("q05", "q10", "q25", "q50", "q75", "q90", "q95"), quantiles):
        frame[q] = values
    frame["crps"] = crps_rows(samples, observations)
    transform = np.maximum if variable == "max" else np.minimum
    frame["twcrps"] = crps_rows(transform(samples, threshold), transform(observations, threshold))
    frame["pit"] = ((samples < observations[:, None]).sum(axis=1)
                    + .5 * (samples == observations[:, None]).sum(axis=1)) / samples.shape[1]
    events = samples > threshold if variable == "max" else samples < threshold
    observed_events = observations > threshold if variable == "max" else observations < threshold
    frame["event_probability"] = events.mean(axis=1)
    frame["event_observed"] = observed_events.astype(int)
    frame["brier"] = (frame.event_probability - frame.event_observed) ** 2
    for level, lower, upper in ((50, "q25", "q75"), (80, "q10", "q90"), (90, "q05", "q95")):
        frame[f"coverage{level}"] = ((observations >= frame[lower]) & (observations <= frame[upper])).astype(int)
        frame[f"width{level}"] = frame[upper] - frame[lower]
    summary = {
        "variable": variable, "n_years": len(observations), "n_members": samples.shape[1],
        "threshold_C": float(threshold), "crps": float(frame.crps.mean()),
        "twcrps": float(frame.twcrps.mean()), "bias": float(frame.bias.mean()),
        "median_mae": float(frame.median_ae.mean()), "brier": float(frame.brier.mean()),
        "event_count": int(observed_events.sum()), "pit_mean": float(frame.pit.mean()),
        "ensemble_std_mean": float(frame["std"].mean()),
        "pit_convention": "(# members < observation + 0.5 # equal)/N; deterministic mid-rank",
        "units": "CRPS, twCRPS, bias, MAE and widths in °C; other metrics dimensionless",
    }
    for level in (50, 80, 90):
        summary[f"coverage{level}"] = float(frame[f"coverage{level}"].mean())
        summary[f"width{level}"] = float(frame[f"width{level}"].mean())
    return {"summary": summary, "per_year": frame}
