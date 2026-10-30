> **Rendu commun de l’équipe (branche `final`)** : ouvrir [le notebook à remettre](rendu_final_concis/rendu_final_groupe.ipynb), [son lien Colab](https://colab.research.google.com/github/eliashas/mini-projet-stochastique/blob/final/rendu_final_concis/rendu_final_groupe.ipynb) et [ses instructions](rendu_final_concis/README.md). La section diffusion comprend l’entraînement PyTorch sur GPU, les variantes et les projections comparées à Bayes. La [version détaillée](notebooks/rendu_final_equipe.ipynb) conserve la grande matrice d’expériences. Les sections ci-dessous décrivent le pipeline historique d’Elias, conservé comme provenance.

# Projet SMA — extrêmes annuels et vagues de chaleur à Brest

Implémentation et expériences du [cahier des charges](PLAN_IMPLEMENTATION_MODELES_SMA.md). Les températures sont en °C et le CO₂ en ppm. Les références gaussienne, GEV et empirique sont comparées à DDPM, au générateur direct CRPS, au débruiteur stochastique CRPS et aux ablations de queue et d'incertitude de l'ancre.

## Installation et données

Python 3.12. L'environnement déjà présent dispose de PyTorch 2.5.1+cu121 et d'un GPU GTX 1660 Ti. Aucune mise à jour CUDA n'est nécessaire. Pour un autre environnement, installer PyTorch adapté au matériel puis `python -m pip install -e . pytest`. Les versions réellement exécutées figurent dans `artifacts/competition/environment.json`.

Les quatre entrées de compétition sont copiées sous `data/kit/data`, avec SHA-256 dans `data/provenance_competition.json`. La vérité reste dans le kit original jusqu'au benchmark. Les originaux ne sont jamais modifiés. Le chemin local du kit est défini uniquement dans `configs/base.yaml`, ou remplacé par `--kit-dir "chemin avec espaces"`. L'archive du professeur est `tmp/pdfs/data_temp_brest.zip`; ses trois fichiers autorisés sont extraits sous `data/full_project` seulement après le benchmark. Pour partager le projet, transmettre également les données locales et l'archive originale.

## Commandes exécutables

Depuis ce dossier, sous PowerShell ou un terminal portable :

```powershell
python -m pytest -q
python scripts/run_pipeline.py audit-data --config configs/experiments.yaml
python scripts/run_pipeline.py smoke --config configs/experiments.yaml
python scripts/run_pipeline.py validate --config configs/experiments.yaml
python scripts/run_pipeline.py select --config configs/experiments.yaml
python scripts/run_pipeline.py fit-final --selection artifacts/competition/selection.json
python scripts/run_pipeline.py predict --selection artifacts/competition/selection.json
python scripts/run_pipeline.py benchmark --manifest artifacts/competition/evaluation_manifest.json
python scripts/run_pipeline.py report --phase competition
python scripts/run_pipeline.py refit-full --selection artifacts/competition/selection.json
python scripts/run_pipeline.py project-full --phase full_project
python scripts/run_pipeline.py report --phase full_project
python scripts/run_pipeline.py notebooks
```

`python scripts/run_pipeline.py all` réalise les phases dans l'ordre. Les scripts PowerShell `scripts/run_competition.ps1` et `scripts/run_full_project.ps1` acceptent `-Python` et `-KitDir`. Les entraînements sont sérialisés sur l'unique GPU. Un retour non nul arrête le script et reste dans le journal.

## Reprise et verrouillage

Les réseaux sauvegardent `best.pt`, `last.pt`, l'optimiseur AdamW, les états RNG et l'historique. Relancer une validation interrompue avec exactement la même configuration réutilise les runs terminés et reprend les autres au checkpoint sauvegardé. Une configuration ou des données différentes refusent la réutilisation d'un même dossier. La reprise CPU a été vérifiée bit à bit contre un entraînement continu. Une reprise CUDA exige le même type de dispositif; elle reste soumise aux opérations CUDA potentiellement non déterministes.

Les variantes D3 et D4 réutilisent les réseaux D1 et D2; elles ajoutent seulement le bootstrap de l'ancre. La sélection utilise les mélanges de trois graines sur les 30 années de validation. Le lambda de queue est choisi séparément pour maxima et minima. Avec un écart inférieur à 0,05 °C, l'ordre de complexité écrit dans la configuration départage les candidats. Les durées finales sont les médianes des meilleurs nombres d'étapes des folds. Les bornes du kit sont contrôlées sur les tirages bruts : aucun clipping ni changement de graine ne corrige un échec.

Avant la vérité, `selection.json`, les NPZ et `evaluation_manifest.json` sont figés. Le benchmark vérifie les empreintes des sorties, checkpoints et kit original. `locked_source.zip` conserve le code exécuté. Une fois le test ouvert, les commandes de validation, sélection, ajustement et prédiction de compétition refusent de remplacer ces expériences. `all` réutilise le benchmark existant et poursuit la phase complète. Pour refaire une compétition indépendante, utiliser un nouveau dossier de projet; ne pas effacer un résultat défavorable.

## Livrables

Les rapports en français sont `reports/rapport_competition.md`, `reports/rapport_projections.md`, `reports/synthese_equipe.md`, avec sources vérifiées dans `reports/audit_sources.md`. Les notebooks exécutés sont sous `notebooks/`; ils lisent les artefacts sans réentraîner. Les figures PNG/SVG sont sous `reports/figures` et `artifacts/*/{annual_analysis,heatwaves}`. Les NPZ compatibles contiennent exactement les quatre clés attendues par le kit; années, scénarios et unités sont dans un JSON séparé. Les projections complètes et leurs tableaux sont sous `artifacts/full_project`.

Le journal `artifacts/execution_journal.jsonl`, les fichiers `failures.json`, les sorties originales du benchmark et les rapports consignent les expériences effectuées, leurs durées et leurs éventuels échecs. `artifacts/smoke/summary.json` contient les huit essais F1 et les contrôles synthétiques réellement entraînés. Les 10 000 simulations ne sont pas de nouvelles observations historiques et leurs intervalles Monte-Carlo ne valident pas le modèle climatique.

## Résultats mesurés

Exécution terminée le 8 octobre 2026 sur GTX 1660 Ti, en float32 sans AMP : 108 entraînements de validation, 24 entraînements finaux de compétition et 6 réentraînements sur 1940–2025. D3/D4 réutilisent les checkpoints parents. Les 12 entraînements de smoke (8 climatiques et 4 synthétiques) ont aussi été exécutés. Les 38 tests ciblés et 4 sous-tests passent. Les deux notebooks comportent chacun 14 cellules de code exécutées sans erreur ; 30 figures sont exportées en PNG et SVG. Le contrôle final est enregistré dans `artifacts/completion_audit.json`.

La sélection fixée avant le test retient **C0_direct_crps pour Tmax** et **D1_ddm_crps pour Tmin**, avec λ = 0,5 pour les ablations de queue des deux variables. Sur les 25 années de test, le participant est admissible : **CRPS Tmax = 1,748986 °C**, **CRPS Tmin = 1,031040 °C**. La reproduction exacte de la référence donne respectivement 1,698885 et 1,064129 °C : le candidat améliore les minima, mais son score des maxima est moins bon. Les résultats test n'ont pas changé la sélection.

**Échec scientifique réel : DDPM est éliminé pour les bornes des minima**, malgré son meilleur CRPS moyen en validation. La graine 2 produit 684 tirages de Tmin par ligne sous −30 °C, avec un minimum de −1 933,216 °C ; les 28 lignes donnent 19 152 occurrences hors bornes. Son CRPS brut Tmin de 2,619998 °C reste diagnostique. Les tirages et trois graines sont conservés. Le [diagnostic détaillé](reports/diagnostic_echec_ddpm.md) examine les historiques et checkpoints figés, sans nouvelle simulation ni ajustement. Les 10 autres exports sont admissibles. Aucun échec technique de validation ou de fit n'a été enregistré.

Après réentraînement sur les 86 années complètes, la médiane Tmax en 2100 sous SSP5-8.5 est **32,632 °C**, avec un intervalle central à 90 % de **[29,767 ; 36,960] °C**. Les probabilités simulées de Tmax > 40 °C en 2100 sont **0/10 000** sous SSP1-2.6, **2/10 000** sous SSP2-4.5 et **29/10 000** sous SSP5-8.5. Pour le premier cas, la borne supérieure binomiale exacte à 95 % vaut 0,0369 %, et ne signifie pas une impossibilité physique. Sous SSP5-8.5, la probabilité simulée d'au moins un dépassement sur 2026–2100 vaut **4,55 %**, sous l'hypothèse d'indépendance conditionnelle annuelle. Ces intervalles mesurent seulement l'erreur Monte-Carlo conditionnelle au modèle.

L'analyse descriptive complète détecte **421 événements d'au moins 3 jours** et **798 d'au moins 2 jours** au-dessus du quantile saisonnier 90 % lissé. Pour les événements d'au moins 3 jours, la durée maximale est 14 jours et l'intensité moyenne au-dessus de la médiane saisonnière est 3,587 °C. La climatologie complète diffère de celle de la phase compétition ; ces nombres ne servent pas à régler les modèles annuels.

Durées mesurées des premières exécutions, sans additionner deux fois les évaluations internes : smoke initial **79,27 s** ; matrice de validation **4 221,29 s (70,35 min)** ; commande `fit-final` **387,62 s** ; `predict` **18,15 s** ; benchmark original **12,49 s** ; `refit-full` **123,57 s** ; `project-full` **14,51 s**. La relecture des checkpoints smoke a pris 19,69 s et n'est pas un nouvel entraînement. Les autres durées, les régénérations de rapports/notebooks et la mémoire GPU figurent dans le journal et les métadonnées.

Lecture conseillée : [synthèse équipe](reports/synthese_equipe.md), [rapport compétition](reports/rapport_competition.md), [rapport projections](reports/rapport_projections.md), [notebook du projet](notebooks/rendu_projet.ipynb) et [notebook d'expériences](notebooks/experiences_execute.ipynb). Les CSV complets, NPZ, historiques, checkpoints et manifestes sont conservés sous `artifacts`.
