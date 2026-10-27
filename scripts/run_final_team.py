"""Exécuter l'intégration de l'équipe sans modifier les résultats historiques.

Usage : python scripts/run_final_team.py [--retrain] [--output CHEMIN]
--retrain reconstruit les ajustements ; sans ce drapeau les checkpoints
compatibles sont réutilisés après vérification des empreintes du train.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
import numpy as np
import pandas as pd
import torch

from sma.final_models import (ALPHAS, WEIGHTS, FOLDS, SCENARIOS, available_models,
    array_digest, bayes_fit, fit_linear, gev_fit, jsonable, neural_sample,
    predictive_sample, quantile_fit, reda_min_fit, write_json, mixture_sample)
from sma.anchor import fit_anchor, predict_anchor, bootstrap_anchor
from sma.diagnostics import evaluate
from sma.benchmark_adapter import check_predictions
from sma.training import train_network


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_neural(train, var, phase, suite, output, retrain):
    """D1/D2/C0 utilisent les mêmes résidus et les mêmes trois graines qu'Elias."""
    from sma.training import DEFAULTS
    config = dict(DEFAULTS, device="auto", tail_lambda=.5)
    ids = {"C0": "C0_direct_crps", "D1": "D1_ddm_crps", "D2": "D2_ddm_tail"}
    steps_final = {"max": {"C0": 2750, "D1": 1250, "D2": 750},
                   "min": {"C0": 2500, "D1": 1500, "D2": 1250}}
    for parent, model_id in ids.items():
        weights, records = [], []
        for seed in (0, 1, 2):
            dest = output/"modeles"/phase/var/parent/f"seed{seed}.npz"
            metadata = dest.with_suffix(".json")
            # L'identité dépend seulement du train, de la validation et du modèle.
            is_fold = phase in FOLDS
            hist_model = model_id+("_lambda0.5" if parent=="D2" else "")
            if is_fold:
                hist = ROOT/"artifacts/competition/validation/runs"/var/phase/hist_model/f"seed{seed}/best.pt"
            else:
                hist = ROOT/"artifacts"/("competition" if phase=="historique" else "full_project")/"final"/var/model_id/f"seed{seed}/best.pt"
            identity = {"train_y": array_digest(train[var]), "train_z": array_digest(suite["anchor"]["z"]),
                        "model": parent, "phase": phase, "seed": seed}
            if dest.exists() and metadata.exists() and not retrain:
                record = read(metadata)
                if record["identity"] != identity:
                    raise ValueError(f"État incompatible : {metadata}")
                weights.append(dest.relative_to(ROOT).as_posix()); records.append(record)
                continue
            started = time.perf_counter()
            reused = hist.exists() and not retrain
            if reused:
                payload = torch.load(hist, map_location="cpu", weights_only=False)
                expected = {"z": array_digest(suite["anchor"]["z"]),
                            "mu": array_digest(predict_anchor(suite["anchor"], train.co2)),
                            "y": array_digest(train[var])}
                if payload["training_fingerprints"] != expected:
                    raise AssertionError(f"Checkpoint incompatible avec les données : {hist}")
                if is_fold:
                    _, start, end = FOLDS[phase]
                    val = train.attrs["validation"]
                    v_expected = {"y": array_digest(val[var]), "mu": array_digest(predict_anchor(suite["anchor"], val.co2)), "co2": array_digest(val.co2)}
                    assert payload["validation_fingerprints"] == v_expected
                hist_meta = read(hist.parent/"metadata.json")
            else:
                validation = None
                if is_fold:
                    val = train.attrs["validation"]
                    validation = dict(y=val[var].to_numpy(), mu=predict_anchor(suite["anchor"], val.co2), co2=val.co2.to_numpy())
                run = ROOT/"artifacts/final_team_training"/output.name/phase/var/parent/f"seed{seed}"
                hist_meta = train_network(model_id, suite["anchor"]["z"], predict_anchor(suite["anchor"], train.co2),
                    train[var], suite["anchor"]["sigma"], suite["threshold"], var, config, seed, run,
                    validation=validation, fixed_steps=None if is_fold else steps_final[var][parent])
                hist = ROOT/hist_meta["checkpoint"]
                payload = torch.load(hist, map_location="cpu", weights_only=False)
            dest.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(dest, **{k: v.detach().cpu().numpy() for k, v in payload["model_state"].items()})
            record = {"identity": identity, "reused_historical": reused, "source_checkpoint": hist.relative_to(ROOT).as_posix(),
                      "source_sha256": sha(hist), "weights_sha256": sha(dest), "best_step": payload["best_step"],
                      "training_seconds": hist_meta["training_seconds"], "additional_seconds": time.perf_counter()-started,
                      "device": hist_meta["device"], "parameters": hist_meta["parameters"]}
            write_json(metadata, record)
            weights.append(dest.relative_to(ROOT).as_posix()); records.append(record)
            print(f"RÉSEAU {phase} {var} {parent} graine {seed} : {'réutilisé' if reused else 'entraîné'}, {record['best_step']} pas", flush=True)
        suite["neural"][parent] = {"weights": weights, "records": records}


def fit_suite(train, var, phase, output, retrain=False):
    destination = output/"modeles"/phase/var/"suite.json"
    identity = {"years": train.year.tolist(), "co2_sha256": array_digest(train.co2), "y_sha256": array_digest(train[var])}
    if destination.exists() and not retrain:
        suite = read(destination)
        assert suite["identity"] == identity
        return suite
    tick = time.perf_counter()
    a = fit_anchor(train.co2, train[var])
    suite = {"identity": identity, "variable": var, "anchor": a,
             "threshold": float(train[var].quantile(.8 if var=="max" else .2)),
             "linear": fit_linear(train.co2, train[var]),
             "bayes": bayes_fit(train.co2, train[var]), "bayes0": bayes_fit(train.co2, train[var], False),
             "quantiles": {}, "neural": {}}
    for alpha in ALPHAS:
        suite["quantiles"][f"{alpha:g}"] = quantile_fit(train.co2, train[var], alpha)
    if var == "max":
        gt = time.perf_counter()
        suite["gev"] = gev_fit(train.co2, train[var], device="cuda" if torch.cuda.is_available() else "cpu")
        suite["gev"]["fit_seconds"] = time.perf_counter()-gt
        print(f"GEV {phase} {var} : support min {suite['gev']['min_training_support']:.4g}, {suite['gev']['rejected_updates']} mises à jour refusées", flush=True)
    else:
        suite["reda_min"] = reda_min_fit(train.co2, train[var])
    suite["bootstrap"] = bootstrap_anchor(train.co2, train[var], B=500, block_length=3,
                   seed=7100+(100 if var=="min" else 0)+int(train.year.max()))
    get_neural(train, var, phase, suite, output, retrain)
    # Moments simulés fixés avant le test, indépendants de ses observations.
    z = neural_sample(suite, "D1", 100000, np.random.default_rng(63210), ROOT)
    suite["h1_moments"] = {"mean": float(z.mean()), "std": float(z.std()), "n": len(z), "seed": 63210,
                           "units_before_and_after": "résidu standardisé, sans unité"}
    suite["fit_wall_seconds"] = time.perf_counter()-tick
    write_json(destination, suite)
    return jsonable(suite)


def metrics(pred, val, var, threshold, model, phase, seconds):
    diag = evaluate(pred, val[var].to_numpy(), threshold, var, val.year.to_numpy())
    row = {"model": model, "variable": var, "phase": phase, "inference_seconds": seconds, **diag["summary"]}
    per = diag["per_year"].assign(model=model, variable=var, phase=phase, threshold_C=threshold)
    return row, per


def checks_variable(test, proj, var):
    # Le même contrôleur que le kit, avec l'autre variable remplacée par un
    # témoin admissible indépendant. Chaque variable conserve ses contrôles.
    other = "min" if var=="max" else "max"
    dummy_test = np.tile(np.linspace(-1, 1, 10000), (25, 1))+(0 if other=="min" else 25)
    dummy_proj = np.tile(np.linspace(-2, 2, 10000), (3, 1))+(0 if other=="min" else 25)
    result = check_predictions({f"test_{var}": test, f"proj_{var}": proj,
                                f"test_{other}": dummy_test, f"proj_{other}": dummy_proj})
    return result["variables"][var]


def run(output, retrain=False):
    start = time.perf_counter()
    torch.set_num_threads(1)
    output = Path(output).resolve()
    output.relative_to(ROOT)  # Toutes les écritures restent dans le workspace.
    result = output/"resultats"; result.mkdir(parents=True, exist_ok=True)
    data = ROOT/"rendu_final/data"
    # La phase train ne lit que le CSV train séparé. Le CSV complet intervient
    # après le gel de la sélection, pour la description et les projections.
    yearly = pd.read_csv(data/"yearly_temp_brest_train.csv", parse_dates=["valid_time"])
    yearly["year"] = yearly.valid_time.dt.year
    future = pd.read_csv(data/"yearly_future_co2.csv", parse_dates=["valid_time"])
    inputs = pd.read_csv(data/"test_inputs.csv", parse_dates=["valid_time"])
    inputs["year"] = inputs.valid_time.dt.year
    assert yearly.year.tolist() == list(range(1940, 2001))
    assert inputs.year.tolist() == list(range(2001, 2026))
    c2100 = future.loc[future.valid_time.dt.year==2100, list(SCENARIOS)].to_numpy().ravel()
    prereg = dict(folds=FOLDS, n_samples=10000, alpha_grid=ALPHAS, weight_grid=WEIGHTS,
                 h0_components=["D1", "D3"], h1_residual="D1", lambda_tail=.5,
                 main_metric="CRPS global", test_previously_consulted=True,
                 decision="minimum non arrondi en validation, puis contrôles sans températures test ; aucun filtre de simplicité à 0.05")
    write_json(result/"configuration_gelee.json", prereg)
    fold_rows, yearly_rows, predictions, suites = [], [], {}, {}
    for fold, (end_train, start_val, end_val) in FOLDS.items():
        train = yearly.loc[yearly.year<=end_train].copy()
        val = yearly.loc[yearly.year.between(start_val, end_val)].copy()
        train.attrs["validation"] = val
        for var in ("max", "min"):
            suite = fit_suite(train, var, fold, output, retrain)
            suites[fold, var] = suite
            predictions[fold, var] = {}
            for model in available_models(var):
                tick = time.perf_counter()
                pred = predictive_sample(suite, model, val.co2, root=ROOT, seed=8300+100*int(fold[-1])+1000*(var=="min"))
                predictions[fold, var][model] = pred
                row, per = metrics(pred, val, var, suite["threshold"], model, fold, time.perf_counter()-tick)
                fold_rows.append(row); yearly_rows.append(per)
            print(f"VALIDATION {fold} {var} terminée", flush=True)
    # Fixer la composante diffusion d'H0 sur ses seuls scores de validation.
    preliminary = pd.DataFrame(fold_rows).groupby(["variable", "model"]).crps.mean()
    components = {var: min(["D1", "D3"], key=lambda model: preliminary.loc[var, model]) for var in ("max", "min")}
    for fold in FOLDS:
        _, start_val, end_val = FOLDS[fold]
        val = yearly.loc[yearly.year.between(start_val, end_val)]
        for var in ("max", "min"):
            for weight in WEIGHTS:
                model = f"H0_{components[var]}_{weight:g}"
                pred = mixture_sample(predictions[fold, var]["Bayes"], predictions[fold, var][components[var]], weight)
                row, per = metrics(pred, val, var, suites[fold,var]["threshold"], model, fold, 0.)
                fold_rows.append(row); yearly_rows.append(per)
    folds = pd.DataFrame(fold_rows)
    folds.to_csv(result/"validation_folds.csv", index=False)
    pd.concat(yearly_rows).to_csv(result/"validation_par_annee.csv", index=False)
    cols = ["crps", "twcrps", "coverage80", "width80", "coverage90", "width90", "bias", "brier", "inference_seconds"]
    summary = folds.groupby(["variable", "model"], as_index=False)[cols].mean()
    summary["n_years"] = 30
    summary.to_csv(result/"validation.csv", index=False)
    decisions = {"h0_components": components, "quantiles": {}, "h0": {}, "validation_first": {}, "selected": {},
                 "test_previously_consulted": True, "test_used_for_selection": False, "rankings": {}}
    for var in ("max", "min"):
        sub = summary.loc[summary.variable==var].sort_values(["crps", "model"])
        decisions["quantiles"][var] = sub.loc[sub.model.str.startswith("QR_")].iloc[0].model
        decisions["h0"][var] = sub.loc[sub.model.str.startswith("H0_")].iloc[0].model
        # Éviter de compter les contrôles extrêmes H0 comme de nouveaux modèles.
        candidates = sub.loc[(~sub.model.str.startswith("QR_") | (sub.model==decisions["quantiles"][var])) &
                             (~sub.model.str.startswith("H0_") | (sub.model==decisions["h0"][var]))]
        decisions["rankings"][var] = candidates.model.tolist()
        decisions["validation_first"][var] = candidates.iloc[0].model
    write_json(result/"selection_avant_controles.json", decisions)
    # Ajustement 1940–2000 et contrôles de projection AVANT les observations test.
    historical, exports, controls = {}, {}, []
    for var in ("max", "min"):
        suite = fit_suite(yearly, var, "historique", output, retrain)
        historical[var] = suite
        names = available_models(var)+[f"H0_{components[var]}_{w:g}" for w in WEIGHTS]
        exports[var] = {}
        for name in names:
            tick = time.perf_counter()
            test = predictive_sample(suite, name, inputs.co2, root=ROOT, seed=8200+1000*(var=="min"))
            proj = predictive_sample(suite, name, c2100, root=ROOT, seed=8200+1000*(var=="min"))
            check = checks_variable(test, proj, var)
            controls.append(dict(model=name, variable=var, **check))
            exports[var][name] = (test, proj, time.perf_counter()-tick)
        valid = {r["model"] for r in controls if r["variable"]==var and r["monotonic"] and r["width_ok"] and r["bounds_ok"]}
        decisions["selected"][var] = next(m for m in decisions["rankings"][var] if m in valid)
    pd.DataFrame(controls).to_csv(result/"controles_kit.csv", index=False)
    write_json(result/"selection.json", decisions)
    selection_sha = sha(result/"selection.json")
    print("SÉLECTION FIGÉE", decisions["selected"], flush=True)
    # La vérité n'est ouverte qu'après ce point ; les exports ne sont plus ajustés.
    truth = pd.read_csv(data/"verite_2001_2025.csv").rename(columns={"annee": "year"})
    assert truth.year.tolist() == inputs.year.tolist()
    test_rows, test_years = [], []
    for var in ("max", "min"):
        for name, (samples, proj, seconds) in exports[var].items():
            row, per = metrics(samples, truth, var, historical[var]["threshold"], name, "test_exploratoire", seconds)
            test_rows.append(row); test_years.append(per)
    pd.DataFrame(test_rows).to_csv(result/"test.csv", index=False)
    pd.concat(test_years).to_csv(result/"test_par_annee.csv", index=False)
    arrays = {key+"_"+var: exports[var][decisions["selected"][var]][i]
              for var in ("max", "min") for i, key in enumerate(("test", "proj"))}
    selected_file = ROOT/"artifacts/final_team_predictions/selection.npz"
    selected_file.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(selected_file, **arrays)
    spec = importlib.util.spec_from_file_location("kit_original_final", ROOT/"rendu_final/sources/kit.py")
    kit = importlib.util.module_from_spec(spec); spec.loader.exec_module(kit); kit.DATA=data
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        score = kit.benchmark(**arrays)
    assert score is not None, stdout.getvalue()
    (result/"benchmark_original.txt").write_text(stdout.getvalue(), encoding="utf-8")
    assert sha(result/"selection.json")==selection_sha
    # Phase distincte : l'ensemble 1940–2025 devient autorisé pour les projections.
    full = pd.read_csv(data/"yearly_temp_brest.csv", parse_dates=["valid_time"])
    full["year"] = full.valid_time.dt.year
    projection_rows, sensitivity, trajectory_rows = [], [], []
    for var in ("max", "min"):
        suite = fit_suite(full, var, "complet", output, retrain)
        candidates = list(dict.fromkeys([decisions["selected"][var], "Bayes", "D1", "D3", "H1", "R_linear", "GEV" if var=="max" else "Reda_min"]))
        for model in candidates:
            for j, scenario in enumerate(SCENARIOS):
                co2 = future[scenario].to_numpy()
                tick = time.perf_counter()
                # Un jeu de paramètres par trajectoire, innovations indépendantes
                # conditionnellement à ce jeu. Le CO2 est la seule entrée future.
                draws = predictive_sample(suite, model, co2, root=ROOT, seed=42000+j+100*(var=="min"), independent_years=True)
                q = np.quantile(draws, [.05,.1,.5,.9,.95], axis=1)
                p = (draws>40).mean(axis=1) if var=="max" else (draws<0).mean(axis=1)
                for i, year in enumerate(future.valid_time.dt.year):
                    sensitivity.append(dict(variable=var, model=model, scenario=scenario, year=int(year), co2_ppm=co2[i],
                        q05_C=q[0,i], q10_C=q[1,i], q50_C=q[2,i], q90_C=q[3,i], q95_C=q[4,i], probability=p[i], n=10000))
                if model==decisions["selected"][var]:
                    projection_rows.extend(sensitivity[-len(co2):])
                hit = draws>40 if var=="max" else draws<0
                trajectory_rows.append(dict(variable=var, model=model, scenario=scenario, p_2100=float(p[-1]),
                    hits_2100=int(hit[-1].sum()), p_at_least_one=float(hit.any(axis=0).mean()), n=10000,
                    minimum_C=float(draws.min()), maximum_C=float(draws.max()),
                    outside_kit_bounds=int(((draws<(0 if var=='max' else -30))|(draws>(50 if var=='max' else 20))).sum()),
                    inference_seconds=time.perf_counter()-tick,
                    assumption="paramètres communs, innovations annuelles indépendantes conditionnellement aux paramètres ; choix H0 commun par trajectoire"))
                print(f"PROJECTION {var} {model} {scenario} : médiane 2100 {q[2,-1]:.2f} °C, p={p[-1]:.4g}", flush=True)
    pd.DataFrame(projection_rows).to_csv(result/"projections.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(result/"sensibilite_projections.csv", index=False)
    pd.DataFrame(trajectory_rows).to_csv(result/"probabilites.csv", index=False)
    run = dict(status="completed", wall_seconds=time.perf_counter()-start, selected=decisions["selected"],
               score_max=score[0], score_min=score[1], selection_sha256=selection_sha,
               python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, torch=torch.__version__,
               gpu=torch.cuda.get_device_name() if torch.cuda.is_available() else None,
               configuration_sha256=sha(result/"configuration_gelee.json"), test_previously_consulted=True,
               predictions_sha256=sha(selected_file), retrain=retrain)
    write_json(result/"execution.json", run)
    print("TERMINÉ", json.dumps(run, ensure_ascii=False), flush=True)
    return run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrain", action="store_true")
    parser.add_argument("--output", default=str(ROOT/"rendu_final"))
    args = parser.parse_args()
    run(args.output, args.retrain)
