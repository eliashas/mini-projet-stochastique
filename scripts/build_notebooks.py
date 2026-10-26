"""Build the two reviewable notebooks from completed pipeline artifacts.

No training or benchmark is performed by these notebooks. --execute runs the
reader cells with nbclient only after the final project artifacts are available.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sma.reporting import METHODS, REFERENCES


SETUP = '''from pathlib import Path
import json
import numpy as np
import pandas as pd
from IPython.display import display, Image, Markdown

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "PLAN_IMPLEMENTATION_MODELES_SMA.md").exists())
COMP = ROOT / "artifacts" / "competition"
FULL = ROOT / "artifacts" / "full_project"

def show_csv(path, rows=30):
    path = Path(path)
    if not path.exists():
        display(Markdown(f"**Artefact absent :** `{path.relative_to(ROOT)}`. Aucun résultat n'est revendiqué."))
        return pd.DataFrame()
    try:
        frame = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        frame = pd.DataFrame()
    columns_by_name = {
        "validation_summary.csv": ["variable", "model", "crps", "twcrps", "coverage80", "width80", "bias", "brier", "fold_count"],
        "validation_mixture.csv": ["variable", "fold", "model", "tail_lambda", "crps", "twcrps"],
        "validation_individual.csv": ["variable", "fold", "model", "seed", "crps", "twcrps"],
        "test_diagnostics.csv": ["variable", "model", "crps", "twcrps", "coverage80", "width80", "bias", "brier"],
        "run_costs.csv": ["variable", "model_id", "fold", "seed", "steps", "best_step", "training_seconds", "gpu_memory_allocated_peak_bytes"],
        "residual_descriptive.csv": ["variable", "n", "skewness", "autocorrelation_lag1", "autocorrelation_lag2", "autocorrelation_lag3", "q05_C", "q50_C", "q95_C"],
        "bootstrap_dispersion.csv": ["variable", "model", "co2_ppm", "anchor_std_C", "generator_residual_std_C", "anchor_variance_fraction", "anchor_mean_shift_C"],
        "residual_law_diagnostics.csv": ["variable", "model", "mean_C", "std_C", "minimum_C", "q50_C", "maximum_C", "fraction_outside_central_window"],
        "bootstrap_block_sensitivity_summary.csv": ["variable", "model", "tail_lambda", "folds", "delta_crps_block1_minus3_C", "delta_twcrps_block1_minus3_C", "folds_global_block1_better", "folds_tail_block1_better"],
        "bootstrap_block_sensitivity_by_fold.csv": ["variable", "model", "fold", "tail_lambda", "delta_crps_block1_minus3_C", "delta_twcrps_block1_minus3_C"],
        "projection_summary.csv": ["variable", "scenario", "year", "co2", "q05", "q50", "q95", "event_probability"],
        "probability_40.csv": ["scenario", "k", "n", "probability", "ci_lower", "ci_upper", "resolution"],
        "trajectory_probability_40.csv": ["scenario", "k", "n", "probability", "ci_lower", "ci_upper"],
    }
    columns = [c for c in columns_by_name.get(path.name, frame.columns) if c in frame]
    display(frame[columns].head(rows).fillna("—"))
    display(Markdown(f"CSV complet : `{path.relative_to(ROOT)}`. Scores et largeurs en °C ; probabilités et couvertures sans unité."))
    if len(frame) > rows:
        display(Markdown(f"{len(frame)} lignes conservées dans le CSV complet."))
    return frame

def show_json(path):
    path = Path(path)
    if not path.exists():
        display(Markdown(f"**Artefact absent :** `{path.relative_to(ROOT)}`."))
        return {}
    record = json.loads(path.read_text(encoding="utf-8"))
    compact = record
    if path.name == "selection.json":
        compact = {key: record[key] for key in ("selected_models", "selected_tail_lambda", "final_steps") if key in record}
    elif path.name == "benchmark_results.json":
        compact = {"candidate": record.get("candidate"), "admissible_count": sum(bool(r.get("admissible")) for r in record.get("results", [])),
                   "results": [{"id": r.get("id"), "scores": r.get("scores"), "admissible": r.get("admissible"),
                                "errors": r.get("checks", {}).get("errors", [])} for r in record.get("results", [])]}
    display(Markdown("```json\\n" + json.dumps(compact, ensure_ascii=False, indent=2) + "\\n```"))
    display(Markdown(f"JSON complet : `{path.relative_to(ROOT)}`."))
    return record

def show_png(path):
    path = Path(path)
    if path.exists():
        display(Image(filename=str(path), width=1000))
    else:
        display(Markdown(f"**Figure absente :** `{path.relative_to(ROOT)}`."))

def show_figures(phase, names):
    for name in names:
        show_png(ROOT / "reports" / "figures" / phase / (name + ".png"))

def show_residuals(phase):
    display(Markdown(f"**Diagnostics résiduels descriptifs : phase {phase}.**"))
    frame = show_csv(ROOT / "artifacts" / phase / "annual_analysis" / "residual_descriptive.csv")
    if not frame.empty:
        import sys
        if str(ROOT / "src") not in sys.path:
            sys.path.insert(0, str(ROOT / "src"))
        from sma.reporting import residual_interpretation
        display(Markdown(residual_interpretation(frame)))
    return frame

def show_ddpm_failure():
    import sys
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    from sma.reporting import ddpm_failure_interpretation
    text = ddpm_failure_interpretation(ROOT)
    if text:
        text = text.replace("(diagnostic_echec_ddpm.md)", "(<" + (ROOT / "reports" / "diagnostic_echec_ddpm.md").as_posix() + ">)")
        display(Markdown(text))

def show_projected_events():
    path = FULL / "projection_summary.csv"
    if not path.exists():
        return show_csv(path)
    projected = pd.read_csv(path)
    columns = ["variable", "model", "scenario", "event_threshold_C", "event_probability", "event_definition", "n"]
    if {"year", *columns}.issubset(projected.columns):
        display(Markdown("**Probabilités marginales en 2100 :** Tmax > q80 ou Tmin < q20 de l’historique "
                         "1940–2025. Ces seuils descriptifs de la phase finale diffèrent des seuils de validation "
                         "et de test ajustés sur leurs trains. Les fréquences viennent des mêmes ensembles annuels "
                         "stockés, sans nouvelle simulation ; l’événement Tmax > 40 °C est présenté séparément."))
        display(projected.loc[projected.year == 2100, columns])
    return projected
'''


def markdown(text):
    return nbformat.v4.new_markdown_cell(text)


def code(text):
    return nbformat.v4.new_code_cell(text)


def metadata():
    return {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
            "sma_artifacts": {"retrain_on_open": False, "source": "executed CSV/JSON/PNG artifacts"}}


def build_experiments():
    cells = [markdown("# Expériences SMA — Brest\n\nValidation 1940–2000, test verrouillé 2001–2025, puis étude finale 1940–2025. "
                      "Ce notebook relit les résultats sauvegardés ; il n'entraîne aucun réseau et n'appelle pas le benchmark."),
             code(SETUP), markdown("## Audit, environnement et vérifications"),
             code("audit = show_json(COMP / 'data_audit.json')\nenvironment = show_json(COMP / 'environment.json')\ntests = show_json(ROOT / 'artifacts' / 'test_results.json')"),
             markdown("## Entraînements de contrôle réellement exécutés\n\nLes smokes détectent les erreurs d'implémentation ; leurs scores ne sont pas les résultats définitifs de la compétition."),
             code("smoke = show_json(ROOT / 'artifacts' / 'smoke' / 'summary.json')"),
             markdown(METHODS), markdown("## Validation temporelle et ablations\n\nLe CRPS du mélange de graines est calculé directement sur ses tirages. "
                                       "La moyenne des CRPS individuels n'est pas ce score. Les seuils et ancres sont ajustés sur le train de chaque fold."),
             code("validation = show_csv(COMP / 'validation_summary.csv')\nfolds = show_csv(COMP / 'validation_mixture.csv', 60)\nseeds = show_csv(COMP / 'validation_individual.csv', 30)"),
             code("if not validation.empty:\n    for variable in ['max', 'min']:\n        view = validation[validation.variable == variable].sort_values('crps')\n        neural = view[view.model.astype(str).str.startswith(('D', 'C0'))]\n        if not view.empty and not neural.empty:\n            best = neural.iloc[0]\n            display(Markdown(f'Pour T{variable}, la meilleure variante neuronale en validation est **{best.model}**, CRPS {best.crps:.6f} °C ; écart au meilleur score toutes familles {best.crps - view.iloc[0].crps:+.6f} °C. La méthode reste expliquée même si une référence statistique est retenue.'))"),
             code("show_figures('competition', ['learning_curves_max', 'learning_curves_min', 'validation_ablation_max', 'validation_ablation_min', 'validation_seed_dispersion'])"),
             markdown("## Choix enregistré avant lecture du test\n\nLe critère principal est le CRPS moyen des trois folds. Avec un écart inférieur à 0,05 °C, "
                      "la règle fixée de simplicité et coût s'applique. Le benchmark ne conduit pas à régler à nouveau ces choix."),
             code("selection = show_json(COMP / 'selection.json')\nprechecks = show_json(COMP / 'prechecks.json')"),
             markdown("## Benchmark original : résultats et échecs\n\nLes NPZ bruts sont conservés. Un modèle avec un bon CRPS qui échoue aux contrôles reste éliminé ; "
                      "la valeur de retour du kit et ses sorties sont consignées. La reproduction de l'exemple R0 conserve ses appels RNG dans l'ordre exact."),
             code("benchmark = show_csv(COMP / 'benchmark_scores.csv')\nbenchmark_record = show_json(COMP / 'benchmark_results.json')\nshow_ddpm_failure()"),
             markdown("## Calibration, localisation et événements\n\nLa couverture et la largeur complètent le CRPS. "
                      "Le PIT est un diagnostic descriptif avec 25 points par modèle ; le Brier inclut les non-événements."),
             code("diagnostics = show_csv(COMP / 'test_diagnostics.csv')\nshow_figures('competition', ['coverage_width', 'pit_max', 'pit_min', 'event_probabilities'])"),
             markdown("## Lois résiduelles et incertitude de l'ancre\n\nLes tirages utilisés pour ces figures ont une graine de diagnostic séparée. "
                      "Ils ne remplacent aucun NPZ officiel. L'ancre bootstrap varie ; l'échelle et les réseaux parents restent fixes."),
             code("residuals_competition = show_residuals('competition')\nlaws = show_csv(COMP / 'residual_law_diagnostics.csv')\nbootstrap = show_csv(COMP / 'bootstrap_dispersion.csv')\nshow_figures('competition', ['residual_laws_max', 'residual_laws_min', 'bootstrap_anchor_max', 'bootstrap_anchor_min'])"),
             markdown("## Sensibilité fixée du bootstrap : blocs de 1 ou 3 ans\n\nLes deux traitements conservent les mêmes réseaux résiduels, seuils, folds et années de validation. "
                      "Les résultats restent séparés par modèle, λ et fold. Un delta blocs1 − blocs3 négatif favorise les blocs d'un an. "
                      "Les blocs de trois ans restent le protocole principal ; cette sensibilité ne sélectionne rien sur le test. "
                      "Les 500 ancres et 10 000 membres numériques n'augmentent pas le nombre d'années historiques."),
             code("block_sensitivity = show_csv(COMP / 'bootstrap_block_sensitivity_summary.csv')\nblock_folds = show_csv(COMP / 'bootstrap_block_sensitivity_by_fold.csv', 40)"),
             markdown("## Temps et mémoire mesurés\n\nLe temps de la boucle inclut ses évaluations : le temps d'inférence de validation est déjà inclus et ne doit pas lui être ajouté."),
             code("costs = show_csv(COMP / 'run_costs.csv', 50)"),
             markdown("## Phase finale et probabilités extrêmes\n\nLes modèles réentraînés sur 1940–2025 n'ont pas un score hors échantillon sur 2001–2025. "
                      "Les intervalles Monte-Carlo sont conditionnels au modèle ; ils ne mesurent pas l'erreur de validité de la queue."),
             code("residuals_full = show_residuals('full_project')\nprojections = show_csv(FULL / 'projection_summary.csv', 12)\nshow_projected_events()\nprobability_40 = show_csv(FULL / 'probability_40.csv')\ntrajectory_40 = show_csv(FULL / 'trajectory_probability_40.csv')\ntransition = show_json(FULL / 'co2_transition.json')\nshow_figures('full_project', ['projection_trajectories', 'projection_distributions_2100', 'projection_probability_40_annual'])"),
             markdown("## Journal et discussion des résultats réellement obtenus"),
             code("for report in ['rapport_competition.md', 'rapport_projections.md', 'synthese_equipe.md']:\n    path = ROOT / 'reports' / report\n    if path.exists():\n        display(Markdown(f'Rapport complet : `{path.relative_to(ROOT)}`'))\n        if report == 'synthese_equipe.md':\n            display(Markdown(path.read_text(encoding='utf-8')))"),
             markdown(REFERENCES)]
    return nbformat.v4.new_notebook(cells=cells, metadata=metadata())


def build_project():
    original = nbformat.read(ROOT / "tmp" / "pdfs" / "miniprojet_starter.ipynb", as_version=4)
    replacements = {
        8: SETUP,
        12: "heatwaves = show_json(FULL / 'heatwaves' / 'heatwave_summary.json')\nshow_csv(FULL / 'heatwaves' / 'heatwave_daily_thresholds.csv', 5)",
        14: "climatology = show_csv(FULL / 'heatwaves' / 'heatwave_climatology.csv', 5)\nshow_png(FULL / 'heatwaves' / 'heatwave_seasonal_cycle.png')\nif not climatology.empty:\n    peak = climatology.loc[climatology.q50_smooth.idxmax()]\n    trough = climatology.loc[climatology.q50_smooth.idxmin()]\n    display(Markdown(f'La médiane saisonnière lissée varie de {trough.q50_smooth:.2f} °C à {peak.q50_smooth:.2f} °C, avec un maximum vers {peak.month_day}.'))",
        16: "events = show_csv(FULL / 'heatwaves' / 'heatwave_events_min3.csv', 15)\nsensitivity = show_csv(FULL / 'heatwaves' / 'heatwave_events_min2.csv', 5)\ncounts = show_csv(FULL / 'heatwaves' / 'heatwave_counts_year.csv', 10)\nif not events.empty:\n    display(Markdown(f'{len(events)} événements de durée minimale 3 jours ; durée maximale {events.duration_days.max()} jours. Anomalie moyenne des événements à q50 : {events.intensity_q50_C.mean():.3f} °C ; excès moyen à q90 : {events.excess_q90_C.mean():.3f} °C. Ces moyennes donnent le même poids à chaque événement.'))",
        18: "show_png(FULL / 'heatwaves' / 'heatwave_duration_intensity.png')\nshow_png(FULL / 'heatwaves' / 'heatwave_counts.png')\ndisplay(Markdown('La couleur indique l’année de début, la durée le nombre de jours calendaires consécutifs. Les seuils sont saisonniers : un épisode hivernal doux peut être détecté. Le diagramme décrit la variabilité et ne démontre pas une causalité ou une calibration prédictive.'))",
        20: "annual = show_csv(FULL / 'annual_analysis' / 'annual_descriptive.csv', 8)\nannual_summary = show_json(FULL / 'annual_analysis' / 'annual_summary.json')",
        22: "show_png(FULL / 'annual_analysis' / 'annual_observations_anchor.png')\nif not annual.empty:\n    display(Markdown(f'Les maxima annuels observés vont de {annual[\"max\"].min():.2f} à {annual[\"max\"].max():.2f} °C. L’ancre représente une tendance en fonction du CO₂ ; les fluctuations annuelles restent importantes.'))",
        24: "correlations = show_csv(FULL / 'annual_analysis' / 'correlations.csv')\nshow_png(FULL / 'annual_analysis' / 'annual_correlations.png')\ndisplay(Markdown('Nous comparons CO₂ brut et log(CO₂), sans transformer la cible thermique. La transformation logarithmique correspond à l’ancre retenue ; une meilleure corrélation descriptive ne prouve ni une causalité locale complète, ni une meilleure extrapolation. Aucune moyenne mobile centrée de températures futures n’entre dans la prévision.'))",
        26: "projection_path = FULL / 'projections.npz'\nif projection_path.exists():\n    with np.load(projection_path, allow_pickle=False) as projected:\n        display(Markdown(f'Ensembles disponibles : Tmax {projected[\"max\"].shape}, Tmin {projected[\"min\"].shape}. Années {projected[\"years\"][0]}–{projected[\"years\"][-1]}.'))\n        if 'co2' in projected:\n            display(pd.DataFrame({'scenario': projected['scenarios'], 'co2_2026_ppm': projected['co2'][:, 0], 'co2_2100_ppm': projected['co2'][:, -1]}))\ntransition = show_json(FULL / 'co2_transition.json')",
        27: "selection = show_json(COMP / 'selection.json')\nvalidation = show_csv(COMP / 'validation_summary.csv')\nif not validation.empty:\n    for variable in ['max', 'min']:\n        view = validation[validation.variable == variable].sort_values('crps')\n        neural = view[view.model.astype(str).str.startswith(('D', 'C0'))]\n        if not neural.empty:\n            best = neural.iloc[0]\n            display(Markdown(f'Meilleure variante neuronale pour T{variable} en validation : **{best.model}**, CRPS {best.crps:.6f} °C. La règle fixée de complexité s’applique aux scores proches ; l’admissibilité est contrôlée ensuite sans température de test.'))\nshow_csv(FULL / 'projection_summary.csv', 9)\nshow_figures('full_project', ['projection_trajectories'])",
        29: "show_figures('full_project', ['projection_distributions_2100', 'projection_probability_40_annual'])\nshow_projected_events()\nprobabilities = show_csv(FULL / 'probability_40.csv')\ntrajectories = show_csv(FULL / 'trajectory_probability_40.csv')\ndisplay(Markdown('k/N mesure une fréquence simulée conditionnelle au modèle. Avec k=0, il faut écrire « aucun dépassement simulé », et non une probabilité physique nulle. La résolution et l’intervalle Monte-Carlo du CSV sont numériques ; l’incertitude de la queue et l’erreur de modèle demeurent. La probabilité durant 2026–2100 suppose des résidus indépendants conditionnellement à une ancre commune sur la trajectoire.'))",
        31: "residuals_full = show_residuals('full_project')\nshow_png(FULL / 'annual_analysis' / 'annual_residual_diagnostics.png')\nshow_figures('full_project', ['residual_laws_min', 'projection_trajectories', 'projection_distributions_2100'])\nshow_csv(FULL / 'projection_summary.csv', 6)\ndisplay(Markdown('Pour les minima, la GEV est ajustée à l’opposé des résidus ; la queue froide utilise h(x)=min(x,s). Les températures restent en °C. La contrainte b≥0 peut être active ; sa fréquence bootstrap indique l’importance de cette hypothèse. Le même protocole de validation précède l’ajustement final.'))",
    }
    additions = {
        1: "Les noms n'ont pas été fournis : les cinq champs du starter restent à compléter par l'équipe.",
        10: "**Provenance contrôlée.** Le CSV et ses empreintes sont conservés dans `data/provenance_competition.json` et les audits. "
            "La mention 9 km du texte original n'est pas certifiée par ces fichiers. Il ne faut pas la présenter comme une résolution ERA5 vérifiée : "
            "ERA5-Land est un produit distinct. Aucune observation extérieure n'entre dans l'apprentissage.",
        13: "Calendrier de 365 jours par mois/jour ; 29 février exclu des quantiles. Moyenne circulaire de 31 jours "
            "(15 jours avant/après) ; seuil du 29 février interpolé entre 28 février et 1er mars. La référence finale 1940–2025 "
            "est descriptive ; sa version 1940–2000 a été utilisée durant le développement.",
        15: r"L'événement est une suite **maximale** de jours où $T_{mean}>q_{90,lissé}$. La durée principale minimale est 3 jours ; "
            r"une sensibilité à 2 jours est sauvegardée. L'intensité est $\overline{T_{mean}-q_{50,lissé}}$ (°C) ; "
            r"l'excès moyen au-dessus du seuil est $\overline{T_{mean}-q_{90,lissé}}$ (°C). La continuité utilise les dates réelles, y compris le 29 février.",
        25: METHODS + "\n\nLes fichiers fournis contiennent des **concentrations** annuelles de CO₂ en ppm. "
            "Elles servent de covariable ; il ne s'agit pas d'un flux annuel d'émissions. "
            "Le meilleur modèle statistique peut gagner. La méthode neuronale reste expliquée et évaluée pour répondre au volet récent de machine learning ; aucun gain n'est garanti.",
        28: "Le résultat principal concerne **Tmax en 2100**. La probabilité d'au moins un dépassement durant 2026–2100 "
            "est un résultat distinct qui exige une hypothèse temporelle. Les quotas fixes du mélange officiel sont stratifiés ; "
            "un calcul binomial utilise un ensemble supplémentaire avec l'indice de réseau tiré indépendamment à chaque simulation.",
    }
    cells = [markdown("# Projet SMA — notebook de rendu\n\nLes deux parties et toutes les questions du starter sont conservées. "
                      "Les réponses relisent les analyses et modèles réellement exécutés. Aucun entraînement n'est relancé à l'ouverture.")]
    for index, cell in enumerate(original.cells):
        if cell.cell_type == "markdown":
            text = cell.source
            if index == 10:
                text = "**Paragraphe original du starter, provenance et résolution à vérifier :**\n\n> " + text.replace("\n", "\n> ")
            cells.append(markdown(text))
        elif index in replacements:
            cells.append(code(replacements[index]))
        if index in additions:
            cells.append(markdown(additions[index]))
    cells += [markdown("## Compétition interne : distinguer train, validation et test"),
              code("show_csv(COMP / 'benchmark_scores.csv')\nshow_ddpm_failure()\nshow_csv(COMP / 'test_diagnostics.csv')\nshow_csv(COMP / 'bootstrap_block_sensitivity_summary.csv')\nshow_csv(COMP / 'bootstrap_block_sensitivity_by_fold.csv', 40)"),
              markdown("La sensibilité du bootstrap compare blocs de 1 et 3 ans sur les folds de validation 1940–2000, "
                       "séparément pour chaque variable et λ. Un delta négatif favorise les blocs d'un an. "
                       "Les blocs de trois ans restent la convention principale fixée avant le test. "
                       "Les diagnostics des résidus 1940–2025 ci-dessus sont descriptifs et ne constituent pas ces scores de validation."),
              markdown("## Discussion et partage de l'équipe\n\nLes simulations ne créent pas de nouvelles années d'observations. "
                       "L'extrapolation suppose une loi résiduelle stationnaire et une ancre log-linéaire. Le littoral et la variabilité "
                       "atmosphérique/océanique ne sont pas modélisés explicitement. La queue à 40 °C reste fragile, même avec un bon CRPS historique."),
              code("path = ROOT / 'reports' / 'synthese_equipe.md'\nif path.exists():\n    display(Markdown(path.read_text(encoding='utf-8')))"),
              markdown(REFERENCES)]
    return nbformat.v4.new_notebook(cells=cells, metadata=metadata())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--kernel", default="python3")
    args = parser.parse_args(argv)
    directory = ROOT / "notebooks"
    directory.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name, notebook in (("experiences_execute.ipynb", build_experiments()), ("rendu_projet.ipynb", build_project())):
        path = directory / name
        if args.execute:
            required = [ROOT / "artifacts" / "competition" / "benchmark_results.json",
                        ROOT / "artifacts" / "full_project" / "projections.npz",
                        ROOT / "artifacts" / "full_project" / "heatwaves" / "heatwave_summary.json"]
            missing = [str(p) for p in required if not p.exists()]
            if missing:
                raise RuntimeError("Execution requires completed phases; missing: " + ", ".join(missing))
            from nbclient import NotebookClient
            client = NotebookClient(notebook, timeout=180, kernel_name=args.kernel,
                                    resources={"metadata": {"path": str(ROOT)}})
            try:
                client.execute()
            except Exception:
                nbformat.write(notebook, path)
                raise
        nbformat.write(notebook, path)
        outputs.append({"path": str(path), "executed": args.execute, "cells": len(notebook.cells),
                        "code_cells": sum(c.cell_type == "code" for c in notebook.cells)})
    result = {"notebooks": outputs, "no_training": True}
    (directory / "execution_status.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
