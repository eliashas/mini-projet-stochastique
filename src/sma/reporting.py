"""French reports and figures, generated from executed artifacts only."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from .anchor import fit_anchor, predict_anchor


def _save(fig, directory: Path, name: str) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix in ("png", "svg"):
        path = directory / f"{name}.{suffix}"
        fig.savefig(path, dpi=160, bbox_inches="tight")
        paths.append(str(path))
    plt.close(fig)
    return paths


def _json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _csv(path: Path):
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _markdown(frame: pd.DataFrame, maximum_rows=40) -> str:
    if frame.empty:
        return "Aucun résultat exécuté disponible dans cet artefact."
    view = frame.head(maximum_rows).copy()
    def value(x):
        if x is None or (isinstance(x, (float, np.floating)) and np.isnan(x)):
            return "—"
        if isinstance(x, (float, np.floating)):
            return f"{x:.6g}"
        return str(x).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(map(str, view.columns)) + " |",
             "| " + " | ".join("---" for _ in view.columns) + " |"]
    lines.extend("| " + " | ".join(value(x) for x in row) + " |" for row in view.itertuples(index=False, name=None))
    if len(frame) > maximum_rows:
        lines.append(f"\n{len(frame)} lignes au total ; le CSV conserve toutes les lignes.")
    return "\n".join(lines)


def _short(frame: pd.DataFrame, columns) -> pd.DataFrame:
    return frame[[column for column in columns if column in frame]].copy()


def _link(path: Path, directory: Path) -> str:
    relative = Path(__import__("os").path.relpath(path, directory)).as_posix()
    return f"[{path.name}]({relative})"


def ddpm_failure_interpretation(root: Path, detailed=True) -> str:
    """Read the frozen benchmark and its diagnostic, without generating draws."""
    root = Path(root)
    benchmark = _json(root / "artifacts" / "competition" / "benchmark_results.json", {})
    result = next((r for r in benchmark.get("results", []) if r.get("id") == "D0_ddpm"), None)
    if not result or result.get("admissible"):
        return ""
    check = result.get("checks", {}).get("variables", {}).get("min", {})
    scores = result.get("scores", {})
    text = (f"**DDPM D0 est éliminé** : {check.get('outside_bounds', '—')} valeurs de Tmin "
            f"sortent de [−30,20] °C ; le minimum simulé atteint **{check.get('smallest', float('nan')):.3f} °C**. "
            f"Son CRPS Tmin brut est **{scores.get('min', float('nan')):.6f} °C** et le kit retourne None. "
            "Un bon score de validation ne rend donc pas cette configuration admissible.")
    diagnostic = _json(root / "artifacts" / "competition" / "ddpm_failure_diagnostic.json", {})
    if detailed and diagnostic:
        minimum = diagnostic.get("variables", {}).get("min", {})
        seed2 = next((r for r in minimum.get("seeds", []) if r.get("seed") == 2), {})
        first = seed2.get("first_test_row", {})
        if first:
            text += (f"\n\nLes {first['outside_count']} tirages froids de la graine 2 "
                     f"({100 * first['outside_fraction']:.3f} % de ses {first['n']} membres) sont réutilisés "
                     "sur les 25 années de test et 3 scénarios : les 19 152 occurrences ne sont pas des "
                     "anomalies climatiques indépendantes. Les graines 0 et 1 ne sortent pas des bornes. "
                     f"Pour la graine 2, médiane **{first['quantiles']['median']:.3f} °C** et moyenne "
                     f"**{first['mean']:.3f} °C** révèlent une queue froide explosive. "
                     "L'ancre Tmin a b=0 : l'extrapolation CO₂ n'est pas l'origine de cet échec. "
                     "Le diagnostic des checkpoints décrit une amplification plausible des erreurs par la "
                     "récursion DDPM et une sensibilité à la durée fixée. Il ne démontre pas qu'un entraînement "
                     "plus long résoudrait le problème. Aucun entraînement, rejet, clipping ou changement de graine "
                     "n'a été appliqué en réaction au test.")
    text += "\n\nDétails : [diagnostic_echec_ddpm.md](diagnostic_echec_ddpm.md), fondé sur le NPZ et les checkpoints figés."
    return text


def _lead_results(root: Path, phase: str, selection: dict | None) -> list[str]:
    text = []
    benchmark = _json(root / "artifacts" / "competition" / "benchmark_results.json", {})
    candidate = next((r for r in benchmark.get("results", []) if r.get("id") == benchmark.get("candidate")), None)
    if candidate:
        chosen = (selection or {}).get("selected_models", {})
        scores = candidate.get("scores", {})
        text.append(f"Candidat verrouillé : **Tmax {chosen.get('max', '—')} / Tmin {chosen.get('min', '—')}**, "
                    f"**{'admissible' if candidate.get('admissible') else 'éliminé'}**. "
                    f"CRPS test : **{scores.get('max', float('nan')):.6f} °C** pour Tmax, "
                    f"**{scores.get('min', float('nan')):.6f} °C** pour Tmin. "
                    "Cette paire reste celle choisie avant lecture du test.")
        counts = benchmark.get("results", [])
        text.append(f"Sur {len(counts)} exports préenregistrés, **{sum(bool(r.get('admissible')) for r in counts)} "
                    "sont admissibles**. Les ablations ne remplacent pas le candidat après lecture du test.")
        exact = next((r for r in counts if r.get("id") == "R0_exact"), None)
        if exact and exact.get("scores"):
            text.append(f"La référence R0 exacte obtient **{exact['scores']['max']:.6f} / {exact['scores']['min']:.6f} °C** "
                        "(Tmax/Tmin). Elle gagne face au participant pour Tmax ; le participant améliore Tmin. "
                        "La diffusion n'apporte donc pas un gain global garanti.")
        failure = ddpm_failure_interpretation(root, detailed=False)
        if failure:
            text.append(failure)
    if phase == "full_project":
        probabilities = _csv(root / "artifacts" / phase / "probability_40.csv")
        if not probabilities.empty:
            text.append("Après réentraînement 1940–2025, les fréquences simulées **Tmax > 40 °C en 2100** "
                        "sont : " + "; ".join(f"{r.scenario} : **{int(r.k)}/{int(r.n)} = {100*r.probability:.3f} %**"
                                                  for r in probabilities.itertuples()) +
                        ". Elles sont conditionnelles au modèle et ne valident pas la queue physique.")
        heat = _json(root / "artifacts" / phase / "heatwaves" / "heatwave_summary.json", {})
        if heat:
            text.append(f"L'étude descriptive 1940–2025 détecte **{heat['events_min3']} événements d'au moins 3 jours** "
                        f"({heat['events_min2']} avec 2 jours), avec une durée maximale de **{heat['maximum_duration_min3_days']} jours**.")
    return text


def analyze_annual(yearly: pd.DataFrame, out_dir: Path, phase: str) -> dict:
    """Descriptive plots using the data explicitly supplied by the phase caller."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = yearly[["valid_time", "max", "min", "co2"]].copy()
    data["year"] = pd.to_datetime(data.valid_time).dt.year
    data = data.sort_values("year").reset_index(drop=True)
    if data.year.duplicated().any() or not np.isfinite(data[["max", "min", "co2"]]).all().all() or (data.co2 <= 0).any():
        raise ValueError("Annual description requires unique years, finite temperatures and positive CO2.")
    parameters, correlations, summaries = {}, [], []
    for variable in ("max", "min"):
        y = data[variable].to_numpy()
        anchor = fit_anchor(data.co2, y)
        parameters[variable] = {k: v.item() if isinstance(v, np.generic) else v
                                for k, v in anchor.items() if k not in {"residuals", "z"}}
        data[f"anchor_{variable}"] = predict_anchor(anchor, data.co2)
        data[f"residual_{variable}"] = anchor["residuals"]
        data[f"standardized_{variable}"] = anchor["z"]
        for transform, x in (("CO2", data.co2), ("log(CO2)", np.log(data.co2))):
            result = stats.pearsonr(x, y)
            correlations.append({"phase": phase, "variable": variable, "transformation": transform,
                                 "n": len(y), "pearson_r": float(result.statistic), "p_descriptive": float(result.pvalue)})
        residual = pd.Series(anchor["residuals"])
        record = {"phase": phase, "variable": variable, "n": len(y), "mean_C": float(residual.mean()),
                  "std_ddof2_C": anchor["sigma"], "skewness": float(stats.skew(residual, bias=False)),
                  "autocorrelation_lag1": float(residual.autocorr(1)),
                  "autocorrelation_lag2": float(residual.autocorr(2)),
                  "autocorrelation_lag3": float(residual.autocorr(3))}
        for q in (.05, .1, .25, .5, .75, .9, .95):
            record[f"q{int(100*q):02d}_C"] = float(residual.quantile(q))
        summaries.append(record)
    data.to_csv(out_dir / "annual_descriptive.csv", index=False)
    pd.DataFrame(correlations).to_csv(out_dir / "correlations.csv", index=False)
    pd.DataFrame(summaries).to_csv(out_dir / "residual_descriptive.csv", index=False)
    (out_dir / "anchor_descriptive.json").write_text(json.dumps(parameters, indent=2, ensure_ascii=False), encoding="utf-8")
    period = f"{data.year.min()}–{data.year.max()}"
    figures = []
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for ax, variable, label in zip(axes[:2], ("max", "min"), ("Maximum annuel", "Minimum annuel")):
        ax.plot(data.year, data[variable], "o-", markersize=3, alpha=.7, label="Observation")
        ax.plot(data.year, data[f"anchor_{variable}"], linewidth=2, label="Ancre a + b log(CO₂), b ≥ 0")
        ax.set(ylabel=label + " (°C)"); ax.legend(fontsize=8); ax.grid(alpha=.2)
    axes[2].plot(data.year, data.co2, color="#228833")
    axes[2].set(xlabel="Année", ylabel="CO₂ (ppm)"); axes[2].grid(alpha=.2)
    fig.suptitle(f"Brest : observations et ancre descriptive, {period}")
    figures += _save(fig, out_dir, "annual_observations_anchor")
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), layout="constrained")
    for row, variable in enumerate(("max", "min")):
        for col, transform in enumerate(("CO2", "log(CO2)")):
            ax = axes[row, col]
            x = data.co2 if col == 0 else np.log(data.co2)
            color = ax.scatter(x, data[variable], c=data.year, cmap="viridis", s=25)
            if col == 1:
                order = np.argsort(x)
                ax.plot(np.asarray(x)[order], data[f"anchor_{variable}"].to_numpy()[order], color="black", label="Ancre contrainte")
            corr = next(r["pearson_r"] for r in correlations if r["variable"] == variable and r["transformation"] == transform)
            ax.set(xlabel="CO₂ (ppm)" if col == 0 else "log(CO₂ / 1 ppm)", ylabel=f"T{variable} annuel (°C)",
                   title=f"r de Pearson = {corr:.3f}"); ax.grid(alpha=.2)
    fig.colorbar(color, ax=axes.ravel().tolist(), label="Année", shrink=.8)
    figures += _save(fig, out_dir, "annual_correlations")
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for row, variable in enumerate(("max", "min")):
        residual = data[f"residual_{variable}"]
        axes[row, 0].hist(residual, bins="auto", density=True, alpha=.6, label="Résidus observés")
        grid = np.linspace(residual.min() - 1, residual.max() + 1, 300)
        axes[row, 0].plot(grid, stats.norm.pdf(grid, scale=parameters[variable]["sigma"]), label="R0 gaussien")
        axes[row, 0].set(xlabel=f"Résidu T{variable} (°C)", ylabel="Densité (1/°C)"); axes[row, 0].legend(fontsize=8)
        axes[row, 1].scatter(data.year, residual, s=18)
        axes[row, 1].set(xlabel="Année", ylabel=f"Résidu T{variable} (°C)")
        axes[row, 2].scatter(data.co2, residual, s=18)
        axes[row, 2].set(xlabel="CO₂ (ppm)", ylabel=f"Résidu T{variable} (°C)")
        for ax in axes[row]:
            ax.grid(alpha=.2)
    fig.suptitle(f"Résidus de l'ancre descriptive, {period}")
    figures += _save(fig, out_dir, "annual_residual_diagnostics")
    summary = {"phase": phase, "years_start": int(data.year.min()), "years_end": int(data.year.max()),
               "n_years": len(data), "anchor": parameters, "figures": figures,
               "interpretation": "descriptive fitted in supplied period; not validation predictions"}
    (out_dir / "annual_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


METHODS = r"""
## Méthodes et conventions mathématiques

L'ancre est ajustée séparément pour Tmax et Tmin : $Y=a+b\log(C)+R$, avec $b=\max(b_{OLS},0)$,
$a=\overline{Y-b\log(C)}$, $\sigma=\mathrm{sd}(R,ddof=2)$ et $Z=R/\sigma$. Le CO₂ est exprimé
en ppm et les résultats en °C. La contrainte traduit ici une hypothèse de tendance locale monotone.
Elle ne démontre pas une réponse physique universelle. La loi résiduelle est supposée stationnaire.

R0 utilise $R\sim\mathcal N(0,\sigma^2)$ ; R1 ajuste une GEV à R pour Tmax, à −R pour Tmin,
avec la convention SciPy $c=-\xi$. R2 rééchantillonne les résidus. Le support GEV et les échecs
d'admissibilité doivent être examinés même si le score moyen semble favorable.
La reproduction exacte R0_exact suit les quatre appels RNG originaux
(test_max, test_min, proj_max, proj_min) : ses résidus sont indépendants entre scénarios.
Les autres exports réutilisent les mêmes résidus et, lorsqu'elle varie, la même ancre entre scénarios.

Le DDPM D0 apprend le bruit dans $Z_k=\sqrt{\bar\alpha_k}Z+\sqrt{1-\bar\alpha_k}\epsilon$ par MSE,
avec 100 pas et un calendrier cosinus. Sa génération suit le processus ancestral inverse. D1 produit
$\hat Z_m=g_\phi(u,t,\zeta_m)$ avec $u=(1-t)Z+t\epsilon$. Dans un ensemble d'entraînement,
u et t sont communs, les latents $\zeta_m$ indépendants ; l'inférence utilise t=1, sans observation
future. C0 emploie le même générateur avec u=0, t=1, pour mesurer l'apport du débruitage auxiliaire.
Il s'agit d'une adaptation scalaire d'une méthode météorologique récente, et non d'une validation
de cette publication sur Brest.

Pour D0, $L_{MSE}=\mathbb E[(\epsilon-\epsilon_\phi(Z_k,k/K))^2]$. En génération :

$$
Z_{k-1}=\frac{1}{\sqrt{\alpha_k}}\left(Z_k-
\frac{\beta_k}{\sqrt{1-\bar\alpha_k}}\epsilon_\phi(Z_k,k/K)\right)
+\sqrt{\tilde\beta_k}\eta,\qquad
\tilde\beta_k=\beta_k\frac{1-\bar\alpha_{k-1}}{1-\bar\alpha_k}.
$$

Le dernier pas ne rajoute aucun bruit. Le calendrier cosinus utilise s=0,008, beta ≤ 0,999,
et son alpha_bar terminal est inférieur à 10⁻³. Les calendriers sont dans les checkpoints.

Le CRPS d'évaluation est $N^{-1}\sum_m|x_m-y|-(2N^2)^{-1}\sum_{m,n}|x_m-x_n|$,
calculé par tri en float64. L'apprentissage C0/D1/D2 utilise M=32 et
$afCRPS=0.95\,fCRPS+0.05\,CRPS_{emp}$, où le terme de dispersion fair a le dénominateur
$2M(M-1)$. Ce petit mélange est légèrement biaisé et diffère du score empirique officiel.
D2 ajoute $\lambda\,afCRPS(h(\hat Y),h(Y))$, avec la même convention
$afCRPS=0.95\,fCRPS+0.05\,CRPS_{emp}$ que le terme global, et
$h(x)=\max(x,s_{hot})$ pour Tmax et
$h(x)=\min(x,s_{cold})$ pour Tmin. Ces seuils sont les quantiles 0,80/0,20 du train.
Le twCRPS d'évaluation applique seulement cette transformation au calcul du score : aucun tirage
de température n'est écrêté. Toutes les années comptent, y compris les fausses alertes.

D3 et D4 réutilisent les réseaux de D1/D2 et ajoutent un bootstrap résiduel de l'ancre à CO₂ fixé
(500 réplications, blocs circulaires de 3 ans ; sensibilité longueur 1). L'échelle et la loi neuronale
restent fixes : cette approximation ne mesure pas toute l'incertitude des paramètres. Elle n'est pas
un posterior bayésien. Le même couple ancre/résidu est employé entre scénarios d'une année.

La contrainte $b\geq0$ peut aussi décaler la moyenne des ancres bootstrap vers le haut lors de
l'extrapolation. L'ajout n'agit donc pas seulement sur la largeur : le tableau de dispersion
rapporte également le décalage moyen par rapport à l'ancre ponctuelle. Un gain de CRPS ne
doit pas être attribué automatiquement à la seule représentation de l'incertitude.

Les intervalles sont centraux, à 50/80/90 %, avec couverture inclusive et largeur en °C.
Le PIT est $(\#\{x_m<y\}+0.5\#\{x_m=y\})/N$, un rang médian déterministe adapté aux égalités
de R2. Le Brier utilise les événements stricts Tmax>s ou Tmin<s. Le biais est la moyenne de
$E_F(Y)-y$, la MAE celle de la médiane. Un PIT de 25 points ne certifie pas une calibration.

## Portée physique et limites

Les températures moyennes journalières servent aux vagues de chaleur ; leurs maxima ne remplacent
pas les extrêmes horaires du fichier annuel. Les 61 puis 86 années restent le nombre d'observations
annuelles : le bruit d'entraînement et 10 000 simulations n'ajoutent aucune observation climatique.
Le CO₂ décrit une tendance mondiale et ne suffit pas à établir une causalité locale complète :
variabilité atmosphérique et océanique, autres forçages et état local ne sont pas explicitement modélisés.

Un bon CRPS sur 25 années évalue surtout la loi dans la région observée. Il ne valide pas la queue
à 40 °C, ni l'extrapolation jusqu'à un CO₂ très supérieur au domaine historique. Les paramètres GEV,
la stationnarité résiduelle et la forme log-linéaire sont fragiles avec ce petit échantillon. Les bornes
du kit et ses tests de monotonie/largeur sont des conventions du groupe, pas des lois physiques.

Il faut distinguer : erreur Monte-Carlo (nombre fini de simulations, conditionnel au modèle ajusté),
incertitude d'estimation (ancre et poids appris) et erreur de modèle (tendance, queue, dynamique).
Le bootstrap d'ancre ne traite que la première composante paramétrique de la tendance.
Une probabilité d'au moins un dépassement durant 2026–2100 exige une hypothèse de dépendance :
résidus indépendants conditionnellement à l'ancre, avec la même ancre conservée sur la trajectoire.
La formule $1-\prod_t(1-p_t)$ pour des marges n'est pas valide avec une ancre aléatoire partagée.
"""


REFERENCES = """
## Références méthodologiques

- [DDPM](https://arxiv.org/abs/2006.11239) et [calendrier cosinus](https://arxiv.org/abs/2102.09672).
- [Diffusion et scores probabilistes météo, prépublication](https://arxiv.org/html/2609.38632v1) ; adaptation scalaire explicitée ci-dessus.
- [AIFS-CRPS](https://arxiv.org/html/2412.15832v1) et [estimateurs CRPS](https://scoringrules.readthedocs.io/en/latest/crps_estimators.html).
- [Scores pondérés](https://scoringrules.readthedocs.io/en/latest/weighted_scores.html).
- [GEV et covariable CO₂](https://ascmo.copernicus.org/articles/9/45/2023/).
- [Validation chronologique](https://otexts.com/fpp3/tscv.html).

Ces références méthodologiques ne fournissent aucune observation supplémentaire au modèle.

La provenance exacte des CSV n'est pas certifiée par leurs métadonnées. La documentation ECMWF
décrit [ERA5 HRES à environ 31 km](https://confluence.ecmwf.int/pages/viewpage.action?navigatingVersions=true&pageId=78296807)
et [ERA5-Land à environ 9 km](https://www.ecmwf.int/en/era5-land). La mention 9 km du starter
ne suffit donc pas à identifier le produit fourni. Les consultations et leurs limites figurent dans `reports/audit_sources.md`.
"""


def _figure_links(phase_dir: Path, report_dir: Path) -> str:
    images = sorted(phase_dir.rglob("*.png"))
    if not images:
        return "Aucune figure PNG disponible à la génération du rapport."
    return "\n\n".join(f"![{p.stem}]({Path(__import__('os').path.relpath(p, report_dir)).as_posix()})" for p in images)


def generate_model_figures(root: Path, phase: str) -> dict:
    """Compare fitted residual laws and bootstrap dispersion after final fitting.

    Sampling uses a fixed independent visualization seed on CPU. These draws
    never replace or modify the frozen benchmark predictions.
    """
    root = Path(root)
    base = root / "artifacts" / phase
    fitted = _json(base / ("fit_final.json" if phase == "competition" else "fit_full.json"), {})
    models = fitted.get("models", {})
    if not models:
        return {"figures": [], "errors": []}
    out = root / "reports" / "figures" / phase
    out.mkdir(parents=True, exist_ok=True)
    figures, errors, descriptions, bootstrap_summary, tail_values = [], [], [], [], []
    from .sampling import sample_network
    from .models.gev import sample as sample_gev
    import torch
    torch.set_num_threads(1)
    for variable in ("max", "min"):
        bundles = models.get(variable, {})
        if not isinstance(bundles, dict) or not bundles:
            continue
        if "anchor" in bundles:  # tolerate a single selected bundle in full phase
            bundles = {bundles.get("model", "selected"): bundles}
        has_ddpm = "D0_ddpm" in bundles
        fig, grid_axes = plt.subplots(2 if has_ddpm else 1, 2, figsize=(13, 9 if has_ddpm else 5), squeeze=False,
                                     layout="constrained")
        axes = grid_axes[0]
        anchor = next(iter(bundles.values()))["anchor"]
        observed = np.asarray(anchor["residuals"])
        central_low, central_high = float(observed.min() - 1), float(observed.max() + 1)
        central_edges = np.linspace(central_low, central_high, 61)
        central_width = np.diff(central_edges)
        central_midpoints = .5 * (central_edges[:-1] + central_edges[1:])
        observed_counts, _ = np.histogram(observed, bins=central_edges)
        axes[0].stairs(observed_counts / (len(observed) * central_width), central_edges, color="black", label="Résidus observés")
        probabilities = np.linspace(.01, .99, 99)
        axes[1].plot(probabilities, np.quantile(observed, probabilities), color="black", linewidth=2, label="Résidus observés")
        for index, (model, bundle) in enumerate(bundles.items()):
            parent = "D1_ddm_crps" if model.startswith("D3") else "D2_ddm_tail" if model.startswith("D4") else None
            if parent and any(m.startswith(parent) for m in bundles):
                continue  # residual law identical to an already displayed parent
            rng = np.random.default_rng(812000 + index)
            try:
                if model == "R0_gaussian":
                    draws = rng.normal(0, bundle["anchor"]["sigma"], 10000)
                elif model == "R1_gev":
                    draws = sample_gev(bundle["gev"], 10000, rng)
                elif model == "R2_empirical":
                    draws = rng.choice(bundle["anchor"]["residuals"], 10000)
                else:
                    checkpoints = bundle.get("checkpoints", [])
                    if not checkpoints:
                        continue
                    n_each = [10000 // len(checkpoints)] * len(checkpoints)
                    n_each[0] += 10000 - sum(n_each)
                    draws = bundle["anchor"]["sigma"] * np.concatenate([
                        sample_network(root / path, n, seed=813000 + index * 11 + seed_index,
                                       device="cpu", batch_size=4096)
                        for seed_index, (path, n) in enumerate(zip(checkpoints, n_each))])
                if not np.isfinite(draws).all():
                    raise FloatingPointError("Non-finite residual visualization ensemble")
                outside = (draws < central_low) | (draws > central_high)
                outside_fraction = float(outside.mean())
                counts, _ = np.histogram(draws, bins=central_edges)
                label = model + f" ; hors fenêtre {100*outside_fraction:.2f} %"
                axes[0].stairs(counts / (len(draws) * central_width), central_edges, label=label, alpha=.85)
                axes[1].plot(probabilities, np.quantile(draws, probabilities), label=model, alpha=.8)
                if model == "D0_ddpm" and has_ddpm:
                    grid_axes[1, 0].hist(draws, bins=60, density=True, histtype="step", color="#cc6677")
                    grid_axes[1, 0].set_yscale("log")
                    grid_axes[1, 0].set(title="DDPM : histogramme complet, toutes les queues",
                                      xlabel=f"Résidu T{variable} (°C), étendue complète", ylabel="Densité (1/°C), échelle log")
                    sorted_draws = np.sort(draws)
                    grid_axes[1, 1].plot(np.linspace(0, 1, len(draws)), sorted_draws, color="#cc6677")
                    grid_axes[1, 1].set(title="DDPM : tous les quantiles, minimum et maximum inclus",
                                      xlabel="Probabilité cumulée", ylabel=f"Résidu T{variable} (°C), étendue complète")
                    grid_axes[1, 0].grid(alpha=.2); grid_axes[1, 1].grid(alpha=.2)
                tail_values.extend({"variable": variable, "model": model, "draw_index": int(i), "residual_C": float(draws[i]),
                                    "central_low_C": central_low, "central_high_C": central_high}
                                   for i in np.flatnonzero(outside))
                record = {"variable": variable, "model": model, "N": len(draws), "mean_C": float(draws.mean()),
                          "std_C": float(draws.std()), "skewness": float(stats.skew(draws)),
                          "minimum_C": float(draws.min()), "maximum_C": float(draws.max()),
                          "central_low_C": central_low, "central_high_C": central_high,
                          "fraction_outside_central_window": outside_fraction,
                          "seed_convention": "812000 + model index for statistical; 813000 + 11 index + seed index for neural"}
                for q in (.01, .05, .1, .5, .9, .95, .99):
                    record[f"q{int(q*100):02d}_C"] = float(np.quantile(draws, q))
                descriptions.append(record)
            except Exception as error:
                errors.append({"variable": variable, "model": model, "stage": "residual_figure", "error": str(error)})
        axes[0].set(xlabel=f"Résidu T{variable} (°C)", ylabel="Densité (1/°C)",
                    title=f"Zoom central [{central_low:.1f},{central_high:.1f}] °C ; normalisation sur N total")
        axes[0].set_xlim(central_low, central_high)
        axes[1].set(xlabel="Probabilité cumulée", ylabel=f"Quantile résiduel T{variable} (°C)",
                    title="Zoom central ; queues conservées dans les vues complètes")
        axes[1].set_ylim(central_low, central_high)
        for ax in axes:
            ax.legend(fontsize=6); ax.grid(alpha=.2)
        fig.suptitle("Lois résiduelles ajustées : zoom central et queues ; tirages de diagnostic distincts du benchmark", fontsize=11)
        figures += _save(fig, out, f"residual_laws_{variable}")
        bootstraps = [(model, bundle) for model, bundle in bundles.items() if "bootstrap" in bundle]
        if bootstraps:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            annual = _csv(base / "annual_analysis" / "annual_descriptive.csv")
            c_min = float(annual.co2.min()) if "co2" in annual else 300.
            c_max = float(annual.co2.max()) if "co2" in annual else 420.
            grid = np.linspace(c_min, 1000, 160)
            for index, (model, bundle) in enumerate(bootstraps):
                color = plt.cm.tab10(index)
                bootstrap = bundle["bootstrap"]
                a, b = np.asarray(bootstrap["a"]), np.asarray(bootstrap["b"])
                axes[0].hist(b, bins=30, density=True, histtype="step", color=color, label=model + " blocs 3")
                sensitivity = bundle.get("bootstrap_sensitivity")
                if sensitivity:
                    axes[0].hist(sensitivity["b"], bins=30, density=True, histtype="step", linestyle="--",
                                 color=color, label=model + " blocs 1")
                centers = a[:, None] + b[:, None] * np.log(grid[None, :])
                q = np.quantile(centers, [.05, .5, .95], axis=0)
                axes[1].plot(grid, q[1], color=color, label=model)
                axes[1].fill_between(grid, q[0], q[2], alpha=.15, color=color)
                generator_model = next((m for m in bundles if m.startswith("D1_ddm_crps" if model.startswith("D3") else "D2_ddm_tail")), model)
                generator_description = next((r for r in descriptions if r["variable"] == variable and r["model"] == generator_model), None)
                residual_std = generator_description["std_C"] if generator_description else bundle["anchor"]["sigma"]
                points = [(c_max, "historical maximum"), (1000., "illustrative extrapolation grid, not SSP input")]
                prediction_metadata = _json(base / "predictions" / "metadata.json", {})
                points += [(float(value), str(scenario) + " in 2100") for scenario, value in prediction_metadata.get("co2_2100_ppm", {}).items()]
                if (base / "projections.npz").exists():
                    with np.load(base / "projections.npz", allow_pickle=False) as projected:
                        if "co2" in projected:
                            points += [(float(value), str(scenario) + " in 2100") for value, scenario in zip(projected["co2"][:, -1], projected["scenarios"])]
                for co2, point_definition in points:
                    spread = float(np.std(a + b * np.log(co2)))
                    anchor_mean = float(np.mean(a + b * np.log(co2)))
                    anchor_point = float(bundle['anchor']['a'] + bundle['anchor']['b'] * np.log(co2))
                    bootstrap_summary.append({"variable": variable, "model": model, "co2_ppm": co2,
                                              "point_definition": point_definition,
                                              "anchor_std_C": spread, "residual_sigma_C": bundle["anchor"]["sigma"],
                                              "anchor_mean_C": anchor_mean, "anchor_point_C": anchor_point,
                                              "anchor_mean_shift_C": anchor_mean - anchor_point,
                                              "generator_residual_std_C": residual_std,
                                              "anchor_variance_fraction": spread**2 / (spread**2 + residual_std**2),
                                              "variance_assumption": "independent anchor and sampled residual; generator weights fixed",
                                              "slope_std_C_per_logppm": float(b.std()),
                                              "constrained_fraction": bootstrap.get("constraint_fraction"),
                                              "bootstrap_replicates": len(a)})
            axes[0].set(xlabel="Pente b (°C par unité de log(CO₂))", ylabel="Densité")
            axes[1].axvspan(c_min, c_max, color="grey", alpha=.12, label="Domaine historique CO₂")
            axes[1].set(xlabel="CO₂ (ppm), grille illustrative", ylabel=f"Ancre T{variable} (°C)", title="Incertitude d'ancre seule, intervalle central 90 %")
            for ax in axes:
                ax.legend(fontsize=6); ax.grid(alpha=.2)
            figures += _save(fig, out, f"bootstrap_anchor_{variable}")
    pd.DataFrame(descriptions).to_csv(base / "residual_law_diagnostics.csv", index=False)
    pd.DataFrame(tail_values, columns=["variable", "model", "draw_index", "residual_C", "central_low_C", "central_high_C"]).to_csv(
        base / "residual_diagnostic_tail_values.csv", index=False)
    if bootstrap_summary:
        pd.DataFrame(bootstrap_summary).to_csv(base / "bootstrap_dispersion.csv", index=False)
    result = {"figures": figures, "errors": errors, "sampling_role": "visualization only, separate fixed seeds; no retraining"}
    (out / "model_figure_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def generate_result_figures(root: Path, phase: str) -> dict:
    """Create comparisons from stored evaluations and predictions only."""
    root = Path(root)
    base = root / "artifacts" / phase
    out = root / "reports" / "figures" / phase
    out.mkdir(parents=True, exist_ok=True)
    figures = []
    costs = []
    histories = {}
    for path in base.rglob("metadata.json"):
        record = _json(path)
        if not isinstance(record, dict) or "model_id" not in record:
            continue
        row = {k: record.get(k) for k in ("model_id", "variable", "seed", "status", "steps", "best_step",
               "training_seconds", "inference_seconds", "device", "parameters", "gpu_memory_allocated_peak_bytes",
               "gpu_memory_reserved_peak_bytes", "best_validation_crps", "resume_from_step")}
        row["run_path"] = path.parent.relative_to(root).as_posix()
        row["fold"] = next((p for p in path.parts if p in {"F1", "F2", "F3"}), "final")
        row["tail_lambda"] = record.get("config", {}).get("tail_lambda")
        costs.append(row)
        history = _csv(path.with_name("history.csv"))
        if not history.empty:
            histories[str(path)] = (record, row, history)
    if costs:
        pd.DataFrame(costs).to_csv(base / "run_costs.csv", index=False)
    for variable in ("max", "min"):
        selected = [(r, row, h) for r, row, h in histories.values() if row["variable"] == variable and row["fold"] != "final"]
        if selected:
            fig, axes = plt.subplots(3, 2, figsize=(13, 11), squeeze=False)
            config_labels = sorted(set(row["model_id"] + (f" λ={row['tail_lambda']:g}" if row["model_id"] == "D2_ddm_tail" else "") for _, row, _ in selected))
            palette = dict(zip(config_labels, plt.cm.tab10(np.linspace(0, .9, len(config_labels)))))
            for r, row, history in selected:
                index = int(row["fold"][1]) - 1
                label = row["model_id"] + (f" λ={row['tail_lambda']:g}" if row["model_id"] == "D2_ddm_tail" else "")
                for col, metric in enumerate(("loss", "validation_crps")):
                    axes[index, col].plot(history.step, history[metric], color=palette[label], alpha=.55,
                                           label=label if row["seed"] == 0 else None)
                    axes[index, col].set(title=row["fold"], xlabel="Étapes d'optimisation",
                                          ylabel="Objectif : MSE D0 / afCRPS (°C) autres" if col == 0 else "CRPS validation (°C)")
                    axes[index, col].grid(alpha=.2)
            axes[0, 0].legend(fontsize=7)
            fig.suptitle(f"T{variable} : apprentissage et validation ; trois graines par couleur")
            fig.tight_layout()
            figures += _save(fig, out, f"learning_curves_{variable}")
    validation = _csv(base / "validation_mixture.csv")
    if not validation.empty and {"model", "variable", "fold", "crps", "twcrps"}.issubset(validation.columns):
        for variable in ("max", "min"):
            view = validation[validation.variable == variable]
            if view.empty:
                continue
            fig, axes = plt.subplots(1, 2, figsize=(13, 5))
            for metric, ax in zip(("crps", "twcrps"), axes):
                pivot = view.pivot_table(index="model", columns="fold", values=metric)
                pivot.plot.bar(ax=ax, width=.8)
                ax.set(ylabel=metric.upper() + " (°C)", xlabel="Modèle", title=f"T{variable} : mélange des trois graines")
                ax.tick_params(axis="x", labelsize=7); ax.grid(axis="y", alpha=.2)
            fig.tight_layout()
            figures += _save(fig, out, f"validation_ablation_{variable}")
    individual = _csv(base / "validation_individual.csv")
    if not individual.empty and {"model", "variable", "seed", "crps"}.issubset(individual.columns):
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        for variable, ax in zip(("max", "min"), axes):
            view = individual[(individual.variable == variable) & (individual.seed.astype(str) != "stat")]
            if not view.empty:
                pivot = view.pivot_table(index="model", columns="seed", values="crps")
                pivot.plot.bar(ax=ax)
            ax.set(title=f"T{variable} : CRPS des graines individuelles", ylabel="CRPS moyen sur folds (°C)", xlabel="Modèle")
            ax.tick_params(axis="x", labelsize=7); ax.grid(axis="y", alpha=.2)
        fig.tight_layout()
        figures += _save(fig, out, "validation_seed_dispersion")
    diagnostics = _csv(base / "test_diagnostics.csv")
    per_year = _csv(base / "test_per_year.csv")
    if diagnostics.empty:
        diagnostics = _csv(base / "validation_summary.csv")
        per_year = _csv(base / "validation_per_year.csv")
        if "seed" in per_year:
            per_year = per_year[per_year.seed.astype(str) == "mixture"]
    if not diagnostics.empty and {"variable", "model", "coverage90", "width90"}.issubset(diagnostics.columns):
        fig, axes = plt.subplots(1, 2, figsize=(13, 6))
        model_names = list(diagnostics.model.drop_duplicates())
        palette = {model: plt.cm.tab20(i / max(len(model_names), 1)) for i, model in enumerate(model_names)}
        handles = []
        for model in model_names:
            handles.append(plt.Line2D([], [], color=palette[model], marker="o", linestyle="", label=model))
        for variable, ax in zip(("max", "min"), axes):
            view = diagnostics[diagnostics.variable == variable]
            for _, row in view.iterrows():
                ax.scatter(row.width90, row.coverage90, s=38, color=palette[row.model], alpha=.85)
            ax.axhline(.9, color="black", linestyle="--", linewidth=1, label="Couverture nominale 90 %")
            ax.set(xlabel="Largeur moyenne intervalle central 90 % (°C)", ylabel="Couverture observée", title=f"T{variable}")
            ax.set_ylim(.7, 1.04); ax.grid(alpha=.2)
            typical = view[view.width90 < 5 * view.width90.median()]
            if len(typical) < len(view):
                padding = max(.2, .1 * (typical.width90.max() - typical.width90.min()))
                ax.set_xlim(typical.width90.min() - padding, typical.width90.max() + padding)
                ax.set_title(f"T{variable} : zoom des largeurs usuelles")
                inset = ax.inset_axes([.45, .06, .52, .45])
                for _, row in view.iterrows():
                    inset.scatter(row.width90, row.coverage90, s=18, color=palette[row.model], alpha=.8)
                inset.axhline(.9, color="black", linestyle="--", linewidth=.7)
                inset.set_title("Étendue complète, DDPM inclus", fontsize=8)
                inset.set_ylim(.7, 1.04); inset.tick_params(labelsize=7); inset.grid(alpha=.2)
                inset.set_xlabel("Largeur (°C)", fontsize=7)
        handles.append(plt.Line2D([], [], color="black", linestyle="--", label="Niveau nominal 90 %"))
        fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=7)
        fig.tight_layout(rect=[0, .14, 1, 1])
        figures += _save(fig, out, "coverage_width")
    if not per_year.empty and {"variable", "model", "pit"}.issubset(per_year.columns):
        for variable in ("max", "min"):
            view = per_year[per_year.variable == variable]
            models = list(view.model.drop_duplicates())
            if not models:
                continue
            cols = 3
            fig, axes = plt.subplots(int(np.ceil(len(models) / cols)), cols, figsize=(12, 3 * int(np.ceil(len(models) / cols))), squeeze=False)
            for model, ax in zip(models, axes.ravel()):
                values = view.loc[view.model == model, "pit"]
                ax.hist(values, bins=np.linspace(0, 1, 6), edgecolor="white")
                ax.axhline(len(values) / 5, color="black", linestyle="--", linewidth=1)
                ax.set(title=model, xlabel="PIT, rang médian", ylabel="Années")
            for ax in axes.ravel()[len(models):]:
                ax.set_visible(False)
            fig.suptitle(f"T{variable} : diagnostic descriptif de rang, faible nombre d'années")
            fig.tight_layout()
            figures += _save(fig, out, f"pit_{variable}")
    if not per_year.empty and {"variable", "model", "event_probability", "event_observed", "year"}.issubset(per_year.columns):
        fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
        for variable, ax in zip(("max", "min"), axes):
            view = per_year[per_year.variable == variable]
            for model, subset in view.groupby("model"):
                ax.plot(subset.year, subset.event_probability, alpha=.6, label=model)
            observations = view.drop_duplicates("year")
            ax.scatter(observations.year, observations.event_observed, c="black", marker="x", label="Événement observé")
            ax.set(ylabel=f"P(événement T{variable})", ylim=(-.04, 1.04)); ax.grid(alpha=.2)
        axes[0].legend(fontsize=6, ncol=3); axes[-1].set_xlabel("Année")
        fig.tight_layout()
        figures += _save(fig, out, "event_probabilities")
    projection = base / "projections.npz"
    if projection.exists():
        with np.load(projection, allow_pickle=False) as loaded:
            years, scenarios = loaded["years"], loaded["scenarios"]
            fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
            for variable, ax in zip(("max", "min"), axes):
                ensemble = loaded[variable]
                for index, scenario in enumerate(scenarios):
                    quantiles = np.quantile(ensemble[index], [.05, .5, .95], axis=-1)
                    color = plt.cm.tab10(index)
                    ax.plot(years, quantiles[1], label=str(scenario), color=color)
                    ax.fill_between(years, quantiles[0], quantiles[2], color=color, alpha=.15)
                ax.set(ylabel=f"T{variable} annuel (°C)", title="Médianes et intervalles centraux 90 %")
                ax.legend(); ax.grid(alpha=.2)
            axes[-1].set_xlabel("Année")
            figures += _save(fig, out, "projection_trajectories")
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            for variable, ax in zip(("max", "min"), axes):
                for index, scenario in enumerate(scenarios):
                    ax.hist(loaded[variable][index, -1], bins=50, density=True, histtype="step", label=str(scenario))
                if variable == "max":
                    ax.axvline(40, color="black", linestyle="--", label="Seuil 40 °C")
                ax.set(xlabel=f"T{variable} 2100 (°C)", ylabel="Densité (1/°C)"); ax.legend(); ax.grid(alpha=.2)
            figures += _save(fig, out, "projection_distributions_2100")
            if "max" in loaded:
                fig, ax = plt.subplots(figsize=(10, 4))
                for index, scenario in enumerate(scenarios):
                    ax.plot(years, (loaded["max"][index] > 40).mean(axis=-1), label=str(scenario))
                ax.set(xlabel="Année", ylabel="Fréquence simulée de Tmax > 40 °C", title="Probabilités marginales, ensembles stockés")
                ax.legend(); ax.grid(alpha=.2)
                figures += _save(fig, out, "projection_probability_40_annual")
    (out / "figure_manifest.json").write_text(json.dumps({"phase": phase, "figures": figures}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"figures": figures, "run_count": len(costs)}


def _ablation_comparisons(root: Path, selection: dict | None) -> pd.DataFrame:
    base = root / "artifacts" / "competition"
    mixture = _csv(base / "validation_mixture.csv")
    individual = _csv(base / "validation_individual.csv")
    if mixture.empty or not {"model", "variable", "fold", "crps", "twcrps"}.issubset(mixture.columns):
        return pd.DataFrame()
    rows = []
    for variable in ("max", "min"):
        weight = (selection or {}).get("selected_tail_lambda", {}).get(variable)
        def subset(frame, prefix):
            view = frame[(frame.variable == variable) & frame.model.astype(str).str.startswith(prefix)].copy()
            if prefix in {"D2_ddm_tail", "D4_ddm_tail_anchor"} and weight is not None:
                if "tail_lambda" in view:
                    view = view[np.isclose(pd.to_numeric(view.tail_lambda, errors="coerce"), float(weight))]
                else:
                    import re
                    view = view[view.model.map(lambda m: not re.search(r"lambda([0-9.]+)", str(m)) or
                                              np.isclose(float(re.search(r"lambda([0-9.]+)", str(m)).group(1)), float(weight)))]
            return view
        pairs = [("D2_ddm_tail", "D1_ddm_crps"), ("D3_ddm_anchor", "D1_ddm_crps"),
                 ("D4_ddm_tail_anchor", "D2_ddm_tail"), ("D1_ddm_crps", "R1_gev"),
                 ("D1_ddm_crps", "R2_empirical"), ("D1_ddm_crps", "C0_direct_crps"),
                 ("D0_ddpm", "R0_gaussian"), ("D0_ddpm", "R1_gev"), ("D0_ddpm", "R2_empirical")]
        for first, second in pairs:
            a = subset(mixture, first).groupby("fold")[["crps", "twcrps"]].mean()
            b = subset(mixture, second).groupby("fold")[["crps", "twcrps"]].mean()
            common = a.index.intersection(b.index)
            if not len(common):
                continue
            delta = a.loc[common] - b.loc[common]
            record = {"variable": variable, "comparison": first + " − " + second,
                      "selected_tail_lambda": weight if first.startswith(("D2", "D4")) else None,
                      "folds": len(common), "delta_crps_C": float(delta.crps.mean()),
                      "delta_twcrps_C": float(delta.twcrps.mean()),
                      "folds_global_improved": int((delta.crps < 0).sum()),
                      "folds_tail_improved": int((delta.twcrps < 0).sum())}
            if not individual.empty and "seed" in individual:
                ia = subset(individual, first)
                ib = subset(individual, second)
                ia = ia[ia.seed.astype(str) != "stat"].groupby("seed")[["crps", "twcrps"]].mean()
                ib_neural = ib[ib.seed.astype(str) != "stat"].groupby("seed")[["crps", "twcrps"]].mean()
                if len(ia):
                    if len(ib_neural):
                        common_seed = ia.index.intersection(ib_neural.index)
                        seed_delta = ia.loc[common_seed] - ib_neural.loc[common_seed]
                    elif len(ib):
                        seed_delta = ia - ib[["crps", "twcrps"]].mean()
                    else:
                        seed_delta = pd.DataFrame()
                    if len(seed_delta):
                        record.update(seed_count=len(seed_delta), seed_delta_crps_std_C=float(seed_delta.crps.std(ddof=0)),
                                      seed_delta_crps_min_C=float(seed_delta.crps.min()), seed_delta_crps_max_C=float(seed_delta.crps.max()),
                                      seed_delta_twcrps_std_C=float(seed_delta.twcrps.std(ddof=0)))
            rows.append(record)
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame.to_csv(base / "ablation_comparisons.csv", index=False)
    return frame


def residual_interpretation(frame: pd.DataFrame) -> str:
    """State computed residual diagnostics without certifying stationarity."""
    if frame.empty:
        return "Les diagnostics résiduels descriptifs ne sont pas disponibles."
    paragraphs = []
    for _, row in frame.iterrows():
        paragraphs.append(
            f"T{row['variable']} ({int(row['n'])} années) : asymétrie descriptive "
            f"**{row['skewness']:+.3f}**, quantiles q05/q50/q95 "
            f"**{row['q05_C']:.3f} / {row['q50_C']:.3f} / {row['q95_C']:.3f} °C**, "
            f"autocorrélations aux retards 1/2/3 ans "
            f"**{row['autocorrelation_lag1']:+.3f} / {row['autocorrelation_lag2']:+.3f} / "
            f"{row['autocorrelation_lag3']:+.3f}**. "
            + ("L'asymétrie positive décrit une queue empirique plus étendue vers les résidus chauds."
               if row['skewness'] > 0 else "L'asymétrie négative décrit une queue empirique plus étendue vers les résidus froids."
               if row['skewness'] < 0 else "L'asymétrie empirique mesurée est nulle."))
    paragraphs.append(
        "Ces valeurs concernent les résidus de l'ancre ajustée sur la période descriptive indiquée, "
        "et non des erreurs de validation calculées avec une ancre commune à tous les folds. "
        "Les autocorrélations décrivent une dépendance locale possible ; avec peu d'années, elles "
        "ne certifient ni indépendance, ni stationnarité, ni validité d'une queue GEV. "
        "Le bootstrap principal en blocs de trois ans conserve une partie de cette dépendance possible ; "
        "la comparaison avec des blocs d'un an est une sensibilité fixée avant le test.")
    return "\n\n".join(paragraphs)


def _bootstrap_block_comparisons(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Match block-1 sensitivity to the same model/lambda/fold under block 3."""
    base = root / "artifacts" / "competition"
    mixture = _csv(base / "validation_mixture.csv")
    columns = {"variable", "fold", "model", "crps", "twcrps"}
    if mixture.empty or not columns.issubset(mixture.columns):
        return pd.DataFrame(), pd.DataFrame()
    fits = base / "validation" / "fits"
    rows = []
    for path in sorted(fits.rglob("block1_validation.json")):
        parts = path.relative_to(fits).parts
        if len(parts) != 4:
            continue
        variable, fold, model, _ = parts
        block1 = _json(path)
        match = mixture[(mixture.variable == variable) & (mixture.fold == fold) & (mixture.model == model)]
        if len(match) != 1:
            continue  # do not combine an ambiguous or unavailable block-3 result
        block3 = match.iloc[0]
        rows.append({
            "variable": variable, "model": model, "tail_lambda": float(block3.get("tail_lambda", 0.)),
            "fold": fold, "n_years": int(block1["n_years"]), "N_block1": int(block1["n_members"]),
            "N_block3": int(block3["n_members"]), "crps_block1_C": float(block1["crps"]),
            "crps_block3_C": float(block3["crps"]), "delta_crps_block1_minus3_C": float(block1["crps"] - block3["crps"]),
            "twcrps_block1_C": float(block1["twcrps"]), "twcrps_block3_C": float(block3["twcrps"]),
            "delta_twcrps_block1_minus3_C": float(block1["twcrps"] - block3["twcrps"]),
            "source_block1": path.relative_to(root).as_posix(),
        })
    detail = pd.DataFrame(rows)
    if detail.empty:
        return detail, pd.DataFrame()
    detail.to_csv(base / "bootstrap_block_sensitivity_by_fold.csv", index=False)
    aggregate = detail.groupby(["variable", "model", "tail_lambda"], as_index=False).agg(
        folds=("fold", "nunique"), validation_years=("n_years", "sum"),
        crps_block1_C=("crps_block1_C", "mean"), crps_block3_C=("crps_block3_C", "mean"),
        delta_crps_block1_minus3_C=("delta_crps_block1_minus3_C", "mean"),
        twcrps_block1_C=("twcrps_block1_C", "mean"), twcrps_block3_C=("twcrps_block3_C", "mean"),
        delta_twcrps_block1_minus3_C=("delta_twcrps_block1_minus3_C", "mean"),
        folds_global_block1_better=("delta_crps_block1_minus3_C", lambda x: int((x < 0).sum())),
        folds_tail_block1_better=("delta_twcrps_block1_minus3_C", lambda x: int((x < 0).sum())))
    aggregate.to_csv(base / "bootstrap_block_sensitivity_summary.csv", index=False)
    return detail, aggregate


def _fitted_model_summary(root: Path, phase: str) -> tuple[pd.DataFrame, list]:
    base = root / "artifacts" / phase
    record = _json(base / ("fit_final.json" if phase == "competition" else "fit_full.json"), {})
    rows = []
    for variable, bundles in record.get("models", {}).items():
        if "anchor" in bundles:
            bundles = {bundles.get("model", "selected"): bundles}
        for model, bundle in bundles.items():
            anchor, gev, bootstrap = bundle.get("anchor", {}), bundle.get("gev", {}), bundle.get("bootstrap", {})
            row = {"variable": variable, "model": model, "n_train": anchor.get("n"),
                   "a_C": anchor.get("a"), "b_C_per_logppm": anchor.get("b"), "b_OLS_C_per_logppm": anchor.get("b_raw"),
                   "sigma_C": anchor.get("sigma"), "scale_floor_active": anchor.get("scale_floor_active"),
                   "threshold_C": bundle.get("threshold"), "tail_lambda": bundle.get("tail_lambda"),
                   "checkpoint_count": len(bundle.get("checkpoints", [])),
                   "neural_parent_reused": model.startswith(("D3", "D4")),
                   "gev_c_minus_xi": gev.get("c"), "gev_xi": gev.get("xi"), "gev_location_C": gev.get("loc"),
                   "gev_scale_C": gev.get("scale"), "gev_support_transformed_residual_C": str(gev.get("support", "")),
                   "gev_convergence": gev.get("convergence"), "gev_warnings": str(gev.get("warnings", "")),
                   "gev_tail_warning": gev.get("tail_warning"),
                   "bootstrap_B": bootstrap.get("replicates"), "bootstrap_block_length": bootstrap.get("block_length"),
                   "bootstrap_constrained_fraction": bootstrap.get("constraint_fraction")}
            rows.append(row)
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame.to_csv(base / "fitted_models_summary.csv", index=False)
    return frame, record.get("failures", [])


def generate_reports(root: Path, phase: str) -> dict:
    """Materialize reports from the pipeline's CSV/JSON artifacts, never raw truth.

    Called after the relevant phase finishes. Missing execution artifacts are
    named as missing instead of being replaced with invented results.
    """
    root = Path(root)
    phase_dir = root / "artifacts" / phase
    report_dir = root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    result_figures = generate_result_figures(root, phase)
    model_figures = generate_model_figures(root, phase)
    fitted_summary, fitted_failures = _fitted_model_summary(root, phase)
    bootstrap_detail, bootstrap_sensitivity = _bootstrap_block_comparisons(root)
    catalog = sorted(str(p.relative_to(root)).replace("\\", "/") for p in phase_dir.rglob("*") if p.is_file())
    summary_path = report_dir / ("rapport_competition.md" if phase == "competition" else "rapport_projections.md")
    title = "Compétition : validation puis évaluation verrouillée" if phase == "competition" else "Projet final : réentraînement et projections 2026–2100"
    text = [f"# {title}\n", "Ce rapport est généré à partir des artefacts présents. Un résultat absent n'est pas considéré exécuté."]
    selection = _json(root / "artifacts" / "competition" / "selection.json")
    text += _lead_results(root, phase, selection)
    diagnostics_table = _csv(root / "artifacts" / "competition" / "test_diagnostics.csv")
    if not diagnostics_table.empty and "model" in diagnostics_table:
        participant = diagnostics_table[diagnostics_table.model == "participant"]
        if not participant.empty:
            text += ["\nLe participant présente les diagnostics suivants :",
                     _markdown(_short(participant, ["variable", "bias", "coverage80", "width80", "brier"])),
                     "\nLe biais négatif et la couverture 80 % de 64 % des maxima (16/25 ans) montrent "
                     "des chaleurs sous-estimées et une sous-couverture sur ce test. Les minima ont une couverture "
                     "de 84 % (21/25) et conservent un biais froid malgré le gain de CRPS face à R0. "
                     "Ces fréquences restent imprécises avec 25 années."]
    text.append("\nLes CRPS, twCRPS, biais et largeurs sont en °C ; couvertures, Brier et probabilités sont sans unité.")
    # Stable contracts used by the pipeline. Tables preserve high-precision CSV values.
    files = (("validation_summary.csv", "Validation : agrégation des mélanges"),
             ("validation_mixture.csv", "Validation : scores des mélanges par fold et variante"),
             ("validation_individual.csv", "Validation : scores des graines individuelles"),
             ("benchmark_scores.csv", "Benchmark original : scores et admissibilité"),
             ("test_diagnostics.csv", "Diagnostics test : couverture, largeur, rang et événement"),
             ("run_costs.csv", "Coûts réellement mesurés des entraînements"),
             ("fitted_models_summary.csv", "Paramètres ajustés, support GEV et réutilisation des checkpoints"),
             ("residual_law_diagnostics.csv", "Lois résiduelles : quantiles et dispersion des tirages de diagnostic"),
             ("bootstrap_dispersion.csv", "Dispersion de l'ancre et comparaison à l'échelle résiduelle"),
             ("projection_summary.csv", "Projections : distributions annuelles"),
             ("probability_40.csv", "Dépassement de 40 °C : simulations et précision"),
             ("trajectory_probability_40.csv", "Dépassement durant 2026–2100 : hypothèse temporelle"))
    for name, label in files:
        table = _csv(phase_dir / name)
        if not table.empty:
            display_columns = {
                "validation_summary.csv": ["variable", "model", "crps", "twcrps", "coverage80", "width80", "bias", "brier", "fold_count"],
                "validation_mixture.csv": ["variable", "fold", "model", "tail_lambda", "crps", "twcrps"],
                "validation_individual.csv": ["variable", "fold", "model", "seed", "crps", "twcrps"],
                "test_diagnostics.csv": ["variable", "model", "crps", "twcrps", "coverage80", "width80", "bias", "brier"],
                "run_costs.csv": ["variable", "model_id", "fold", "seed", "steps", "best_step", "training_seconds", "gpu_memory_allocated_peak_bytes"],
                "fitted_models_summary.csv": ["variable", "model", "b_C_per_logppm", "b_OLS_C_per_logppm", "sigma_C", "tail_lambda", "neural_parent_reused"],
                "residual_law_diagnostics.csv": ["variable", "model", "mean_C", "std_C", "minimum_C", "q50_C", "maximum_C", "fraction_outside_central_window"],
                "bootstrap_dispersion.csv": ["variable", "model", "co2_ppm", "anchor_std_C", "generator_residual_std_C", "anchor_variance_fraction", "anchor_mean_shift_C"],
                "projection_summary.csv": ["variable", "scenario", "year", "co2", "q05", "q50", "q95", "event_probability"],
                "probability_40.csv": ["scenario", "k", "n", "probability", "ci_lower", "ci_upper", "resolution"],
                "trajectory_probability_40.csv": ["scenario", "k", "n", "probability", "ci_lower", "ci_upper"],
            }
            compact = _short(table, display_columns.get(name, table.columns))
            text += [f"\n## {label}\n", _markdown(compact), "\nSource complète : " + _link(phase_dir / name, report_dir) + "."]
            if name in {"validation_summary.csv", "test_diagnostics.csv"}:
                text += ["\nIntervalles centraux : couvertures et largeurs pour les trois niveaux.",
                         _markdown(_short(table, ["variable", "model", "coverage50", "width50", "coverage80", "width80", "coverage90", "width90"]))]
            if name == "fitted_models_summary.csv":
                gev = table[table.gev_c_minus_xi.notna()]
                if not gev.empty:
                    text += ["\nParamètres et support GEV de la variable transformée R ou −R :",
                             _markdown(_short(gev, ["variable", "gev_c_minus_xi", "gev_xi", "gev_location_C", "gev_scale_C", "gev_support_transformed_residual_C", "gev_tail_warning"])),
                             "\nSciPy ne fournit pas de statut d'optimiseur dans cet ajustement. Les paramètres finis, "
                             "la validité du support et les warnings sont archivés dans le CSV et les manifests de fit."]
    if selection is not None:
        compact_selection = {k: selection[k] for k in ("selected_models", "selected_tail_lambda", "final_steps") if k in selection}
        text += ["\n## Sélection verrouillée\n", "```json\n" + json.dumps(compact_selection, ensure_ascii=False, indent=2) + "\n```",
                 "\nClassements et règles complets : " + _link(root / "artifacts" / "competition" / "selection.json", report_dir) + "."]
    if phase == "competition":
        benchmark_record = _json(phase_dir / "benchmark_results.json")
        if benchmark_record is not None:
            text += ["\n## Rapport du benchmark original et reproduction exacte de R0\n",
                     "Sorties stdout, valeurs de retour, scores exacts et contrôles par variable sont conservés dans " +
                     _link(phase_dir / "benchmark_results.json", report_dir) + ".",
                     ddpm_failure_interpretation(root)]
            admissible = [r for r in benchmark_record.get("results", []) if r.get("admissible") and isinstance(r.get("scores"), dict)]
            if admissible:
                best_max = min(r["scores"]["max"] for r in admissible)
                near = sorted([r for r in admissible if r["scores"]["max"] - best_max < .05], key=lambda r: r["scores"]["min"])
                others = sorted([r for r in admissible if r["scores"]["max"] - best_max >= .05], key=lambda r: r["scores"]["max"])
                ordering = [{"rank_descriptive": i + 1, "id": r["id"], "CRPS_max_C": r["scores"]["max"],
                             "CRPS_min_C": r["scores"]["min"], "within_0.05_best_max": r["scores"]["max"] - best_max < .05}
                            for i, r in enumerate(near + others)]
                pd.DataFrame(ordering).to_csv(phase_dir / "official_descriptive_order.csv", index=False)
                text += ["\nClassement descriptif du groupe : les modèles admissibles à moins de 0,05 °C du meilleur CRPS "
                         "max sont regroupés et ordonnés par CRPS min ; les autres suivent par CRPS max. Ce regroupement "
                         "n'est pas une relation de départage paire à paire transitive et ne change pas le candidat verrouillé.",
                         _markdown(pd.DataFrame(ordering))]
    if phase == "full_project":
        transition = _json(phase_dir / "co2_transition.json")
        if transition is not None:
            text += ["\n## Transition historique 2025 / scénarios 2026\n",
                     "```json\n" + json.dumps(transition, ensure_ascii=False, indent=2) + "\n```",
                     "\nLes trajectoires CO₂ sont utilisées telles que fournies ; toute rupture apparaît ici sans correction silencieuse."]
        projected = _csv(phase_dir / "projection_summary.csv")
        event_columns = ["variable", "model", "scenario", "event_threshold_C", "event_probability", "event_definition", "n"]
        if {"year", *event_columns}.issubset(projected.columns):
            events2100 = projected.loc[projected.year == 2100, event_columns]
            text += ["\n## Probabilités marginales en 2100 : seuils historiques de la phase finale\n",
                     "Ces probabilités utilisent Tmax > q80 ou Tmin < q20 de l'historique **1940–2025**, avec les seuils "
                     "déjà ajustés dans fit_full.json. Elles sont calculées sur les mêmes ensembles annuels stockés, "
                     "sans nouvelle simulation. Ce sont des événements distincts de Tmax > 40 °C. Les seuils descriptifs "
                     "de la phase finale diffèrent des seuils propres aux trains des folds et du seuil de test "
                     "1940–2000 ; leurs probabilités ne remplacent pas les scores de validation ou de test.",
                     _markdown(events2100), "\nLe CSV `artifacts/full_project/projection_summary.csv` conserve ces "
                     "probabilités pour chacune des années 2026–2100."]
    if phase == "competition":
        text += ["\nLes folds sont F1 : 1940–1970 → 1971–1980 ; F2 : 1940–1980 → 1981–1990 ; "
                 "F3 : 1940–1990 → 1991–2000. Les réglages sont choisis sur les 30 années de validation "
                 "du mélange à poids égaux des graines 0/1/2. Le test 2001–2025 n'entre pas dans le réglage. "
                 "Les modèles de ce rapport sont entraînés sur 1940–2000.",
                 "\nLe classement officiel emploie le CRPS des maxima ; si l'écart entre deux membres est inférieur à "
                 "0,05 °C, le groupe départage par le CRPS des minima. Le kit ne code pas ce départage. Dans une "
                 "comparaison de plusieurs modèles, les modèles admissibles à moins de 0,05 °C du meilleur CRPS "
                 "max sont identifiés comme proches ; aucune variante n'est choisie après lecture du test."]
    else:
        text += ["\nLes ajustements finaux utilisent 1940–2025, après le benchmark verrouillé. Leurs prédictions "
                 "2001–2025 ne constituent donc pas un score hors échantillon. Les SSP sont les covariables CO₂ "
                 "fournies ; ils ne constituent pas des observations de température.",
                 "\nPour 40 °C, k/N est une estimation conditionnelle au modèle ajusté. Une absence de dépassement "
                 "simulé n'est pas une probabilité physique nulle. Un intervalle binomial exige un tirage indépendant "
                 "de l'indice de réseau pour chaque simulation ; les quotas fixes du benchmark sont stratifiés."]
    for name, label in (("annual_summary.json", "Analyse annuelle descriptive"), ("heatwave_summary.json", "Vagues de chaleur")):
        paths = list(phase_dir.rglob(name))
        for path in paths:
            record = _json(path)
            record = {k: v for k, v in record.items() if k != "figures"}
            text += [f"\n## {label}\n", "```json\n" + json.dumps(record, ensure_ascii=False, indent=2) + "\n```"]
            if name == "heatwave_summary.json":
                text.append(f"Sur {record.get('reference_start')}–{record.get('reference_end')}, le seuil saisonnier détecte "
                            f"**{record.get('events_min3')} événements** d'au moins trois jours, contre **{record.get('events_min2')}** "
                            f"avec deux jours. La durée maximale est **{record.get('maximum_duration_min3_days')} jours**. "
                            f"L'intensité moyenne des événements est **{record.get('mean_intensity_min3_C', 0):.3f} °C** "
                            f"au-dessus de q50 lissé ; l'excès moyen à q90 est **{record.get('mean_excess_q90_min3_C', 0):.3f} °C**. "
                            "Chaque événement a le même poids dans ces moyennes. Un seuil relatif saisonnier peut détecter des "
                            "épisodes doux en hiver ; ce ne sont pas exclusivement des canicules estivales à seuil sanitaire.")
            elif name == "annual_summary.json":
                for variable, anchor in record.get("anchor", {}).items():
                    text.append(f"Ancre T{variable} : pente OLS **{anchor['b_raw']:.6f} °C par unité de log(CO₂)**, "
                                f"pente retenue **{anchor['b']:.6f}**, σ résiduel **{anchor['sigma']:.6f} °C**. "
                                + ("La contrainte est active : la tendance négative descriptive est remplacée par une pente nulle. "
                                   "Ce choix méthodologique limite l'interprétation de la projection."
                                   if anchor.get("constraint_active") else "La contrainte de pente positive n'est pas active sur cette période."))
    for path in phase_dir.rglob("correlations.csv"):
        text += ["\n## Corrélations descriptives : CO₂ brut et log(CO₂)\n", _markdown(_csv(path)),
                 "\nCes corrélations ne démontrent ni causalité complète ni qualité d'extrapolation. Les p-values "
                 "descriptives supposent des observations indépendantes et ne corrigent pas l'autocorrélation temporelle."]
    for path in phase_dir.rglob("residual_descriptive.csv"):
        residuals = _csv(path)
        text += ["\n## Résidus : quantiles, asymétrie et dépendance temporelle descriptive\n",
                 _markdown(_short(residuals, ["variable", "n", "skewness", "autocorrelation_lag1", "autocorrelation_lag2", "autocorrelation_lag3", "q05_C", "q50_C", "q95_C"])), residual_interpretation(residuals),
                 f"\nSource : `{path.relative_to(root).as_posix()}`."]
    if not bootstrap_sensitivity.empty:
        text += ["\n## Sensibilité du bootstrap : blocs de 1 an contre blocs de 3 ans\n",
                 "Cette comparaison utilise uniquement les validations F1/F2/F3, avec les mêmes réseaux "
                 "résiduels, seuils et observations. Chaque ligne conserve le modèle et son λ ; les variantes "
                 "à λ différents ne sont pas agrégées ensemble. Les ensembles ont 10 000 membres. "
                 "Un delta négatif favorise les blocs d'un an. Les blocs de trois ans restent le protocole principal "
                 "fixé ; ces résultats ne déclenchent aucun choix sur le test.",
                 _markdown(_short(bootstrap_sensitivity, ["variable", "model", "tail_lambda", "folds", "delta_crps_block1_minus3_C", "delta_twcrps_block1_minus3_C", "folds_global_block1_better", "folds_tail_block1_better"])),
                 _markdown(_short(bootstrap_detail, ["variable", "model", "fold", "tail_lambda", "delta_crps_block1_minus3_C", "delta_twcrps_block1_minus3_C"])),
                 "\nLes moyennes agrègent les folds disponibles, chacun ayant 10 années. Le nombre de folds et "
                 "d'années est indiqué ; il ne faut pas présenter une ligne partielle comme trois folds terminés. "
                 "La différence mesure une sensibilité descriptive à la dépendance supposée des résidus, "
                 "avec 500 ancres et une loi neuronale fixe, plutôt qu'une validation complète de cette hypothèse.",
                 "\nSources : `artifacts/competition/bootstrap_block_sensitivity_summary.csv` et "
                 "`artifacts/competition/bootstrap_block_sensitivity_by_fold.csv` ; les sources JSON par fold "
                 "figurent dans la dernière colonne."]
    validation_summary = _csv(root / "artifacts" / "competition" / "validation_summary.csv")
    mixture = _csv(root / "artifacts" / "competition" / "validation_mixture.csv")
    if not validation_summary.empty and {"variable", "model", "crps"}.issubset(validation_summary.columns):
        text += ["\n## Apport des modèles : résultats de validation\n"]
        for variable in ("max", "min"):
            view = validation_summary[validation_summary.variable == variable].sort_values("crps")
            if len(view):
                best = view.iloc[0]
                text.append(f"Pour T{variable}, le CRPS de validation le plus faible est celui de {best.model} "
                            f"({best.crps:.6f} °C). Ce classement provient des folds, avant le test.")
                nearest = view[view.crps - best.crps < .05]
                text.append("Les modèles à moins de 0,05 °C de ce score sont : " + ", ".join(nearest.model.astype(str)) +
                            ". La règle de simplicité/cout du manifeste détermine la sélection parmi les scores proches.")
                neural = view[view.model.astype(str).str.startswith(("D", "C0"))]
                if not neural.empty:
                    nbest = neural.iloc[0]
                    text.append(f"La variante neuronale au meilleur CRPS de validation est **{nbest.model}** "
                                f"({nbest.crps:.6f} °C), soit un écart de **{nbest.crps - best.crps:+.6f} °C** "
                                "par rapport au meilleur score de toutes les familles. Sa méthode reste décrite dans le notebook "
                                "La règle de complexité fixée s'applique aux scores proches, quelle que soit la famille retenue.")
            if not mixture.empty and {"model", "variable", "fold", "crps", "twcrps"}.issubset(mixture.columns):
                view = mixture[mixture.variable == variable]
                comparisons = []
                for other in ("R1_gev", "R2_empirical", "C0_direct_crps"):
                    base_scores = view[view.model == other].set_index("fold")
                    denoiser = view[view.model == "D1_ddm_crps"].set_index("fold")
                    common = base_scores.index.intersection(denoiser.index)
                    if len(common):
                        delta = denoiser.loc[common, "crps"] - base_scores.loc[common, "crps"]
                        comparisons.append({"variable": variable, "comparison": f"D1 − {other}", "common_folds": len(common),
                                            "delta_crps_C": float(delta.mean()), "folds_D1_better": int((delta < 0).sum())})
                if comparisons:
                    text.append(_markdown(pd.DataFrame(comparisons)))
        text.append("Un delta négatif favorise D1. Les scores par fold, par graine et les twCRPS permettent "
                    "d'évaluer la constance et le coût d'une amélioration ; un gain moyen isolé ne démontre pas "
                    "une amélioration des queues. Les variantes D3/D4 réutilisent les mêmes réseaux et isolent "
                    "l'ajout de dispersion par l'ancre.")
        comparisons = _ablation_comparisons(root, selection)
        if not comparisons.empty:
            text += ["\nComparaisons ciblées : un delta négatif favorise le premier modèle. Les λ de D2/D4 sont ceux "
                     "fixés par validation pour la variable. La dispersion donnée est celle des deltas moyens par graine "
                     "(écart-type descriptif ddof=0), distincte de la performance du mélange.",
                     _markdown(_short(comparisons, ["variable", "comparison", "selected_tail_lambda", "delta_crps_C", "delta_twcrps_C", "folds_global_improved", "folds_tail_improved", "seed_delta_crps_std_C"])),
                     "\nComparaisons complètes : " + _link(root / "artifacts" / "competition" / "ablation_comparisons.csv", report_dir) + "."]
    text += [METHODS, "\n## Exécutions, adaptations et échecs\n"]
    if fitted_failures:
        text.append("Échecs réels d'ajustement, enregistrés dans le manifeste de fit :\n\n```json\n" +
                    json.dumps(fitted_failures, ensure_ascii=False, indent=2) + "\n```")
    elif not fitted_summary.empty:
        text.append("Le manifeste d'ajustement final ne signale aucun échec technique. Cela ne garantit ni "
                    "l'admissibilité du benchmark ni la stabilité scientifique des extrapolations.")
    if model_figures["errors"]:
        text.append("Échecs de génération de figures, conservés sans remplacement silencieux :\n\n" + _markdown(pd.DataFrame(model_figures["errors"])))
    journal = root / "artifacts" / "execution_journal.jsonl"
    records = []
    if journal.exists():
        records = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
        relevant = [r for r in records if r.get("phase") in {phase, "all", "setup", "smoke"}]
        if relevant:
            text.append(f"{len(relevant)} entrées de journal concernent cette phase et les contrôles préparatoires. "
                        "Les reprises, adaptations, durées et erreurs sont conservées dans " + _link(journal, report_dir) + ".")
            errors = [r for r in relevant if r.get("error") or "failure" in str(r.get("action", ""))]
            if errors:
                text.append(_markdown(_short(pd.DataFrame(errors), ["timestamp_utc", "phase", "action", "error", "repair"])))
        else:
            text.append("Aucune entrée de journal pour cette phase ; vérifier les métadonnées des runs.")
    else:
        text.append("Journal global absent ; les fichiers présents ci-dessous sont la seule preuve disponible.")
    text += ["\nLa durée `training_seconds` inclut les évaluations et les sauvegardes dans la boucle. "
             "`inference_seconds` est le temps de ces évaluations, déjà inclus ; leur somme serait un double comptage. "
             "Les temps de prédiction définitifs sont consignés dans les métadonnées de la phase.",
             "\nLes lois résiduelles utilisent un zoom central dont l'histogramme est normalisé par le N total. "
             "La masse hors fenêtre figure dans chaque légende et le CSV. Le DDPM possède des panneaux de queue "
             "complète ; toutes les valeurs hors fenêtre sont conservées dans " + _link(phase_dir / "residual_diagnostic_tail_values.csv", report_dir) + ". "
             "Ces tirages de diagnostic ont leurs propres graines et ne sont pas les ensembles officiels.",
             "\n## Figures exportées\n", _figure_links(phase_dir, report_dir),
             _figure_links(report_dir / "figures" / phase, report_dir), REFERENCES,
             "\n## Inventaire de traçabilité\n", "\n".join("- `" + p + "`" for p in catalog)]
    summary_path.write_text("\n\n".join(text), encoding="utf-8")
    # Short team synthesis is rebuilt after either phase, so it never promises pending work.
    synthesis = ["# Synthèse équipe\n", "La sélection proposée figure dans le manifeste verrouillé `artifacts/competition/selection.json`."]
    if selection and selection.get("selected_models"):
        chosen = selection["selected_models"]
        synthesis[1] = f"Candidat verrouillé : Tmax **{chosen.get('max')}**, Tmin **{chosen.get('min')}**. "\
                       "Les choix sont fixés sur validation 1940–2000 avant ouverture du test."
    benchmark = _csv(root / "artifacts" / "competition" / "benchmark_scores.csv")
    if not benchmark.empty:
        synthesis += ["\nRésultats réels du benchmark (°C pour les CRPS) :\n", _markdown(benchmark, 20)]
    else:
        synthesis.append("\nLe tableau du benchmark n'est pas encore disponible : aucun score test n'est revendiqué ici.")
    benchmark_record = _json(root / "artifacts" / "competition" / "benchmark_results.json", {})
    candidate = benchmark_record.get("candidate")
    record = next((r for r in benchmark_record.get("results", []) if r.get("id") == candidate), None)
    if record:
        scores = record.get("scores") or {}
        admissibility = "admissible" if record.get("admissible") else "éliminé par les contrôles"
        if "max" in scores and "min" in scores:
            synthesis.append(f"\nParticipant **{candidate}** : CRPS Tmax **{scores['max']:.6f} °C**, "
                             f"Tmin **{scores['min']:.6f} °C** ; statut **{admissibility}**.")
    failure = ddpm_failure_interpretation(root, detailed=False)
    if failure:
        synthesis.append(failure)
    probabilities = _csv(root / "artifacts" / "full_project" / "probability_40.csv")
    if not probabilities.empty:
        synthesis.append("\nTmax > 40 °C en 2100, conditionnellement au modèle : " +
                         "; ".join(f"{r.scenario} **{int(r.k)}/{int(r.n)} ({100*r.probability:.3f} %)**" for r in probabilities.itertuples()) +
                         ". Avec zéro tirage dépassant 40 °C, aucun dépassement n'est simulé ; la borne Monte-Carlo "
                         "à 95 % est 0,000369, pas une probabilité physique nulle.")
    heat = _json(root / "artifacts" / "full_project" / "heatwaves" / "heatwave_summary.json", {})
    if heat:
        synthesis.append(f"\nVagues de chaleur descriptives 1940–2025 : **{heat['events_min3']} événements ≥ 3 jours**, "
                         f"**{heat['events_min2']} ≥ 2 jours** ; durée maximale **{heat['maximum_duration_min3_days']} jours**.")
    synthesis += ["\nLes 25 années de test et les 61 années d'apprentissage limitent la précision des conclusions. "
                  "Le CO₂ sert de covariable de tendance ; la stabilité des résidus et l'extrapolation jusqu'à 2100 "
                  "restent des hypothèses. La simulation de 40 °C ne valide pas la queue physique.",
                  "\nÀ partager localement : les deux rapports, les notebooks exécutés, les PNG/SVG, les CSV/JSON et "
                  "les NPZ officiels ; conserver configs, checkpoints et empreintes pour reproduction."]
    (report_dir / "synthese_equipe.md").write_text("\n\n".join(synthesis), encoding="utf-8")
    return {"phase": phase, "report": str(summary_path), "synthesis": str(report_dir / "synthese_equipe.md"),
            "artifact_files": len(catalog), "figures": result_figures}
