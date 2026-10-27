"""Modèles du rendu commun : chaque famille conserve ses propres hypothèses.

Les fonctions d'ajustement reçoivent seulement les données autorisées du train.
Les états JSON et les poids NPZ permettent une inférence portable, sans pickle.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import QuantileRegressor

from .anchor import fit_anchor, predict_anchor, bootstrap_anchor
from .models.ddm import ScalarDDM

SCENARIOS = ("ssp1-2.6", "ssp2-4.5", "ssp5-8.5")
ALPHAS = (0.0, 0.01, 0.1, 1.0)
WEIGHTS = (0., .25, .5, .75, 1.)
FOLDS = {"F1": (1970, 1971, 1980), "F2": (1980, 1981, 1990), "F3": (1990, 1991, 2000)}


def jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(value), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def array_digest(values):
    array = np.ascontiguousarray(values, dtype=np.float64)
    h = hashlib.sha256(str(array.shape).encode("ascii"))
    h.update(array.tobytes())
    return h.hexdigest()


def bayes_fit(co2, y, slope=True):
    """Statistiques suffisantes de la loi normale et du prior 1/sigma², b>=0."""
    co2, y = np.asarray(co2), np.asarray(y)
    center = np.log(co2).mean()
    X = np.c_[np.ones(len(y)), np.log(co2) - center][:, :1 + int(slope)]
    V = np.linalg.inv(X.T @ X)
    beta = V @ X.T @ y
    return dict(center=center, beta=beta, V=V, rss=np.sum((y-X@beta)**2),
                df=len(y)-X.shape[1], slope=slope, n=len(y))


def bayes_parameters(state, n, rng):
    """Rejet JOINT : sigma et beta acceptés ensemble, sans écrêtage de b."""
    beta, V = np.asarray(state["beta"]), np.asarray(state["V"])
    accepted, scales, total, count = [], [], 0, 0
    while count < n:
        batch = max(2*(n-count), 1024)
        sigma = np.sqrt(state["rss"] / rng.chisquare(state["df"], batch))
        theta = beta + sigma[:, None] * rng.normal(size=(batch, len(beta))) @ np.linalg.cholesky(V).T
        keep = theta[:, 1] >= 0 if state["slope"] else np.ones(batch, dtype=bool)
        accepted.append(theta[keep]); scales.append(sigma[keep])
        count += int(keep.sum()); total += batch
        if total > 1000*n:
            raise RuntimeError("Taux de rejet bayésien excessif : aucun remplacement silencieux")
    theta, sigma = np.concatenate(accepted)[:n], np.concatenate(scales)[:n]
    return theta[:, 0], theta[:, 1] if state["slope"] else np.zeros(n), sigma


def quantile_fit(co2, y, alpha):
    """99 quantiles, CO2 brut centré/réduit sur le train pour pénaliser la pente."""
    center, scale = np.mean(co2), np.std(co2)
    X = ((np.asarray(co2)-center)/scale)[:, None]
    tau = np.arange(1, 100)/100
    fits = [QuantileRegressor(quantile=q, alpha=alpha, solver="highs").fit(X, y) for q in tau]
    return dict(center=center, scale=scale, alpha=alpha, tau=tau,
                intercept=[f.intercept_ for f in fits], slope=[f.coef_[0] for f in fits])


def quantile_sample(state, co2, uniforms):
    """Réarrangement monotone, interpolation et prolongements linéaires jusqu'à 0 et 1.

    Ce choix impose des queues bornées. Il ne valide pas le risque rarissime de 40°C.
    Aucune masse n'est ajoutée artificiellement aux quantiles 1% et 99%.
    """
    x = (np.asarray(co2)-state["center"])/state["scale"]
    raw = np.asarray(state["intercept"])[None, :] + x[:, None]*np.asarray(state["slope"])
    q = np.sort(raw, axis=1)
    knots = np.c_[2*q[:, 0]-q[:, 1], q, 2*q[:, -1]-q[:, -2]]
    levels = np.r_[0., np.asarray(state["tau"]), 1.]
    return np.stack([np.interp(u, levels, row) for row, u in zip(knots, uniforms)])


def gev_fit(co2, y, B=500, steps=3000, seed=0, device="cpu"):
    """GEV non stationnaire de Reda, avec contrôle explicite du support.

    L'optimisation vectorise les B réplications. Une mise à jour qui quitte le
    support est refusée pour la réplication concernée : les données impossibles
    ne reçoivent jamais une vraisemblance obtenue en écrêtant z.
    """
    torch.set_num_threads(1)
    x = np.log(np.asarray(co2))
    center = x.mean()
    x = torch.tensor(x-center, dtype=torch.float64, device=device)
    t = torch.tensor(np.asarray(y), dtype=torch.float64, device=device)
    gen = torch.Generator(device=device).manual_seed(seed)
    idx = torch.randint(len(t), (B, len(t)), generator=gen, device=device)
    idx[0] = torch.arange(len(t), device=device)
    xb, tb = x[idx], t[idx]
    theta = torch.tensor([t.mean().item(), 0., t.std().log().item(), -.1],
                         dtype=torch.float64, device=device).repeat(B, 1).requires_grad_()
    opt = torch.optim.Adam([theta], lr=.02)
    refused = 0
    for _ in range(steps):
        b0, b1, log_s, xi = theta.T[:, :, None]
        z = 1 + xi*(tb-b0-b1*xb)/log_s.exp()
        assert bool((z > 0).all()), "État GEV hors support avant optimisation"
        loss = (log_s+(1+1/xi)*z.log()+z.pow(-1/xi)).sum()
        if not torch.isfinite(loss):
            raise FloatingPointError("Vraisemblance GEV non finie")
        before = theta.detach().clone()
        opt.zero_grad(); loss.backward(); opt.step()
        with torch.no_grad():
            theta[:, 1].clamp_(min=0)
            theta[:, 3].clamp_(-.5, -.01)
            b0, b1, log_s, xi = theta.T[:, :, None]
            support = 1+xi*(tb-b0-b1*xb)/log_s.exp()
            invalid = (~torch.isfinite(support).all(1)) | (support.min(1).values <= 0) | (~torch.isfinite(theta).all(1))
            refused += int(invalid.sum())
            theta[invalid] = before[invalid]
            # Effacer l'élan des seules réplications refusées évite de répéter
            # mécaniquement la même sortie du support au pas suivant.
            for key in ("exp_avg", "exp_avg_sq"):
                opt.state[theta][key][invalid] = 0
    with torch.no_grad():
        b0, b1, log_s, xi = theta.T[:, :, None]
        z = 1+xi*(tb-b0-b1*xb)/log_s.exp()
    return dict(theta=theta.detach().cpu().numpy(), center=center, B=B, steps=steps,
                rejected_updates=refused, min_training_support=float(z.min()),
                device=device, seed=seed, shape_constraint=[-.5, -.01])


def reda_min_fit(co2, y, B=500, seed=0):
    """Bootstrap de paires et résidus de Reda, pente libre conservée pour l'audit."""
    rng = np.random.default_rng(seed)
    x, y = np.log(np.asarray(co2)), np.asarray(y)
    slopes, intercepts, residuals = [], [], []
    for b in range(B):
        idx = rng.integers(len(y), size=len(y)) if b else np.arange(len(y))
        slope, intercept = np.polyfit(x[idx], y[idx], 1)
        slopes.append(slope); intercepts.append(intercept)
        residuals.append(y[idx]-intercept-slope*x[idx])
    return dict(a=intercepts, b=slopes, residuals=residuals)


def neural_sample(suite, parent, n, rng, root, device="cpu"):
    """Mélange équipondéré des trois réseaux, avec nouveaux latents indépendants."""
    asset = suite["neural"][parent]
    counts = [n//3 + (i < n % 3) for i in range(3)]
    draws = []
    for path, count in zip(asset["weights"], counts):
        with np.load(Path(root)/path) as w:
            state = {k: torch.tensor(w[k]) for k in w.files}
        with torch.random.fork_rng(devices=[]):
            model = ScalarDDM((32, 32), direct=parent=="C0")
        model.load_state_dict(state); model.to(device).eval()
        generator = torch.Generator(device=device).manual_seed(int(rng.integers(0, 2**31-1)))
        with torch.no_grad():
            draws.append(model.sample(count, generator, batch_size=8192).cpu().numpy().astype(float))
    # Le mélange ne doit pas attribuer chaque période à une seule graine.
    out = np.concatenate(draws)
    rng.shuffle(out)
    return out


def predictive_sample(suite, model, co2, n=10000, seed=8200, root=".", independent_years=False, device="cpu"):
    """Lignes = CO2, colonnes = membres. Paramètres communs par trajectoire.

    independent_years=False emploie des aléas communs entre lignes pour réduire
    le bruit des comparaisons marginales. True renouvelle l'innovation annuelle.
    """
    rng = np.random.default_rng(seed)
    co2 = np.asarray(co2, dtype=float)
    rows = len(co2)
    shape = (rows, n) if independent_years else (1, n)
    a = suite["anchor"]
    if model.startswith("H0_"):
        _, component, weight = model.split("_")
        weight = float(weight)
        bayes = predictive_sample(suite, "Bayes", co2, n, seed, root, independent_years, device)
        diffusion = predictive_sample(suite, component, co2, n, seed, root, independent_years, device)
        return mixture_sample(bayes, diffusion, weight)
    if model in ("Bayes", "Bayes0", "H1"):
        state = suite["bayes0" if model=="Bayes0" else "bayes"]
        aa, bb, sig = bayes_parameters(state, n, rng)
        if model == "H1":
            z = neural_sample(suite, "D1", int(np.prod(shape)), rng, root, device).reshape(shape)
            moments = suite["h1_moments"]
            z = (z-moments["mean"])/moments["std"]
        else:
            z = rng.normal(size=shape)
        return aa+bb*(np.log(co2)[:, None]-state["center"])+sig*z
    if model.startswith("QR_"):
        u = np.broadcast_to(rng.random(shape), (rows, n))
        return quantile_sample(suite["quantiles"][model[3:]], co2, u)
    if model == "GEV":
        state = suite["gev"]
        theta = np.asarray(state["theta"])[rng.integers(state["B"], size=n)]
        b0, b1, ls, xi = theta.T
        # Le générateur uniforme exclut 0 et 1 : aucun écrêtage de température.
        u = rng.uniform(np.nextafter(0., 1.), 1., size=shape)
        return b0+b1*(np.log(co2)[:, None]-state["center"])+np.exp(ls)/xi*((-np.log(u))**(-xi)-1)
    if model == "Reda_min":
        s = suite["reda_min"]
        idx = rng.integers(len(s["a"]), size=n)
        residuals = np.asarray(s["residuals"])
        ix = rng.integers(residuals.shape[1], size=shape)
        return (np.asarray(s["a"])[idx]+np.asarray(s["b"])[idx]*np.log(co2)[:, None]
                +residuals[idx[None, :], ix])
    if model in ("R_log", "R_linear"):
        anchor = suite["linear"] if model=="R_linear" else a
        x = co2 if model=="R_linear" else np.log(co2)
        return anchor["a"]+anchor["b"]*x[:, None]+anchor["sigma"]*rng.normal(size=shape)
    parent = {"D3": "D1", "D4": "D2"}.get(model, model)
    z = neural_sample(suite, parent, int(np.prod(shape)), rng, root, device).reshape(shape)
    if model in ("D3", "D4"):
        boot = suite["bootstrap"]
        idx = rng.integers(len(boot["a"]), size=n)
        mu = np.asarray(boot["a"])[idx]+np.log(co2)[:, None]*np.asarray(boot["b"])[idx]
    else:
        mu = a["a"]+a["b"]*np.log(co2)[:, None]
    return mu+a["sigma"]*z


def mixture_sample(bayes, diffusion, weight):
    """Échantillonnage stratifié d'un mélange de LOIS, sans moyenner leurs valeurs."""
    if weight == 1:
        return bayes.copy()
    if weight == 0:
        return diffusion.copy()
    n = bayes.shape[1]
    nb = int(round(n*weight))
    return np.concatenate([bayes[:, :nb], diffusion[:, nb:]], axis=1)


def available_models(variable):
    return (["R_log", "R_linear", "Bayes", "Bayes0", "C0", "D1", "D2", "D3", "D4", "H1"]
            +[f"QR_{alpha:g}" for alpha in ALPHAS]+["GEV" if variable=="max" else "Reda_min"])


def fit_linear(co2, y):
    slope = max(float(np.polyfit(co2, y, 1)[0]), 0.)
    intercept = float(np.mean(y-slope*np.asarray(co2)))
    return dict(a=intercept, b=slope, sigma=float(np.std(y-intercept-slope*np.asarray(co2), ddof=2)))
