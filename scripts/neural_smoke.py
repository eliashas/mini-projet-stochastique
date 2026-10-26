"""Execute inexpensive neural climate smokes and a known-normal learning check."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

import numpy as np
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sma.anchor import fit_anchor, predict_anchor
from sma.data import load_competition, prepare_kit
from sma.sampling import sample_network
from sma.scores import crps_rows
from sma.splits import temporal_folds
from sma.training import train_network


def run_smoke(base_config=None):
    config = base_config or yaml.safe_load((ROOT / "configs" / "base.yaml").read_text(encoding="utf-8"))
    start = time.perf_counter()
    destination = ROOT / "artifacts" / "smoke"
    destination.mkdir(parents=True, exist_ok=True)
    prepare_kit(config)
    _, train, validation = next(temporal_folds(load_competition(config)["yearly_temp_brest_train"]))
    model_ids = ["D0_ddpm", "C0_direct_crps", "D1_ddm_crps", "D2_ddm_tail"]
    climate = []
    smoke_config = {**config, "max_steps": 100, "min_steps": 100,
                    "eval_every": 50, "samples_early_stopping": 512,
                    "patience_evaluations": 8, "cpu_num_threads": 1}
    for variable in ["max", "min"]:
        anchor = fit_anchor(train.co2.to_numpy(), train[variable].to_numpy())
        mu = predict_anchor(anchor, train.co2.to_numpy())
        validation_mu = predict_anchor(anchor, validation.co2.to_numpy())
        threshold = float(np.quantile(train[variable], .8 if variable == "max" else .2))
        for model_id in model_ids:
            directory = destination / "F1" / variable / model_id
            summary = train_network(model_id, anchor["z"], mu, train[variable].to_numpy(),
                                    anchor["sigma"], threshold, variable, smoke_config, 0, directory,
                                    validation={"y": validation[variable].to_numpy(),
                                                "mu": validation_mu,
                                                "co2": validation.co2.to_numpy()})
            draws = sample_network(directory / "best.pt", 1000, 991, "auto")
            predictions = validation_mu[:, None] + anchor["sigma"] * draws[None, :]
            np.savez_compressed(directory / "smoke_predictions.npz", validation=predictions,
                                years=validation.valid_time.dt.year.to_numpy(), residuals=draws)
            row = {"model_id": model_id, "variable": variable, "fold": "F1",
                   "steps": summary["steps"], "best_step": summary["best_step"],
                   "validation_crps": float(crps_rows(predictions, validation[variable].to_numpy()).mean()),
                   "residual_mean": float(np.mean(draws)), "residual_std": float(np.std(draws)),
                   "training_seconds": summary["training_seconds"], "device": summary["device"],
                   "finite": bool(np.isfinite(predictions).all())}
            climate.append(row)
            print(json.dumps(row), flush=True)
    synthetic = []
    rng = np.random.default_rng(480)
    z = rng.normal(size=2048)
    observed = rng.normal(size=1024)
    synthetic_config = {"device": "auto", "max_steps": 1500, "min_steps": 1500,
                        "eval_every": 250, "samples_early_stopping": 1024,
                        "patience_evaluations": 8, "cpu_num_threads": 1,
                        "tail_lambda": 1.0}
    oracle = rng.normal(size=10000)
    oracle_crps = float(crps_rows(np.broadcast_to(oracle, (observed.size, oracle.size)), observed).mean())
    collapsed_crps = float(np.mean(np.abs(observed)))
    for model_id in model_ids:
        directory = destination / "synthetic_normal" / model_id
        summary = train_network(model_id, z, np.zeros_like(z), z, 1., .8416212335729143,
                                "max", synthetic_config, 0, directory,
                                fixed_steps=1500)
        infer_start = time.perf_counter()
        draws = sample_network(directory / "best.pt", 10000, 401, "auto")
        inference_seconds = time.perf_counter() - infer_start
        score = float(crps_rows(np.broadcast_to(draws, (observed.size, draws.size)), observed).mean())
        # Distribution recovery is a diagnostic, not a claim of calibration
        # on Brest. The limits catch collapsed or grossly divergent samplers.
        passed = bool(np.isfinite(draws).all() and abs(draws.mean()) < .4
                      and .5 < draws.std() < 1.5 and score < collapsed_crps)
        row = {"model_id": model_id, "distribution": "N(0,1)", "training_n": len(z),
               "independent_evaluation_n": len(observed), "steps": summary["steps"],
               "sample_n": len(draws), "mean": float(draws.mean()), "std": float(draws.std()),
               "q01": float(np.quantile(draws, .01)), "q99": float(np.quantile(draws, .99)),
               "evaluation_crps": score, "oracle_mc_crps": oracle_crps,
               "collapsed_zero_crps": collapsed_crps, "recovery_diagnostic_passed": passed,
               "training_seconds": summary["training_seconds"], "inference_seconds": inference_seconds,
               "device": summary["device"]}
        np.savez_compressed(directory / "synthetic_predictions.npz", samples=draws, observations=observed)
        synthetic.append(row)
        print(json.dumps(row), flush=True)
    report = {"status": "completed", "climate": climate, "synthetic": synthetic,
              "elapsed_seconds": time.perf_counter() - start,
              "gpu": torch.cuda.get_device_name() if torch.cuda.is_available() else None,
              "interpretation": "100-step climate runs test execution only; known-normal runs diagnose ability to learn and ancestral/endpoint sampling. These are not climate validation results.",
              "failures": [r["model_id"] for r in synthetic if not r["recovery_diagnostic_passed"]]}
    (destination / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    run_smoke()
