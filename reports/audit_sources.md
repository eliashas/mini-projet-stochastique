# Audit des sources et des conventions

Audit effectué le 8 octobre 2026, heure de Paris. Il porte sur les documents du projet et les références méthodologiques de la section 14 du cahier des charges. Les articles apportent des méthodes, aucune nouvelle observation climatique.

## Documents du projet lus

| Document | Lecture effectuée | Rôle et précision |
|---|---|---|
| `PLAN_IMPLEMENTATION_MODELES_SMA.md` | Texte complet, 14 sections | Cahier des charges exécutif : matrice d'expériences, scores, validation et séparation des phases. |
| `GUIDE.pdf` | Texte des 3 pages et rendu des 3 pages | Règles du groupe et résumé du sujet. |
| `miniprojet_MCE_SMA_2026.pdf` | Texte des 9 pages ; rendu des pages 2, 7, 8 et 9 | Sujet du professeur, objectifs, deux parties, axes d'évaluation et échéance. Les graphiques illustratifs ne sont pas exploités comme observations. |
| `CONTEXTE_POUR_LLM.md` | Texte complet | Détails du protocole du groupe ; le cahier des charges prime pour les choix méthodologiques demandés. |
| `tmp/pdfs/miniprojet_starter.ipynb` | Sources des 32 cellules, sans lecture de leurs outputs ni exécution du starter | Les titres, questions et deux parties sont identifiés. Les cellules d'import/lecture ne sont pas exécutées. |
| `kit.py` original | Texte source | Vérification des formes, du CRPS et des contrôles ; aucun appel au benchmark pendant cet audit. |

`exemple.py` n'a pas été importé. Aucun CSV de températures 2001–2025 ni CSV historique complet de l'archive n'a été ouvert par cet audit. Les tests d'extraction portent exclusivement sur des archives synthétiques.

Le professeur demande une prévision probabiliste conditionnée au CO₂, une méthode récente expliquée en LaTeX, les distributions futures, les minima et les vagues de chaleur. Le CRPS officiel, la coupure en 2000, le classement et les contrôles éliminatoires appartiennent au protocole du groupe. Le notebook annonce « 3 main components » mais en énumère quatre ; les quatre axes sont bien code, unités/sorties, mathématiques et discussion physique. Les échéances documentaires sont le 23 octobre 2026 pour la comparaison du groupe et le 30 octobre pour le notebook.

Le score de référence annoncé dans les documents (1,70 °C / 1,06 °C) est une valeur documentaire. Sa reproduction effective et les valeurs non arrondies sont du ressort de la phase benchmark verrouillée.

## Références de la section 14

Toutes les consultations ci-dessous utilisent des sources primaires ou leur documentation officielle. Les résultats publiés sur images, météo globale ou Europe ne sont pas présentés comme des résultats sur Brest.

### 1. DDPM

[Ho, Jain et Abbeel, *Denoising Diffusion Probabilistic Models*](https://arxiv.org/html/2006.11239v2), texte HTML complet accessible ; [notice arXiv](https://arxiv.org/abs/2006.11239) consultée. Les équations 4, 7, 11 et 14 et l'algorithme d'échantillonnage sont les éléments utilisés : corruption gaussienne à variance connue, prédiction du bruit, moyenne inverse paramétrée et variance postérieure. Le dernier pas n'ajoute pas de bruit.

Adaptation : un scalaire standardisé annuel, MLP `[32,32]` et aucun clipping des résidus. Les performances d'images et l'architecture convolutionnelle du papier ne sont pas transférées. La chaîne inverse relève du modèle D0 et ne doit pas être confondue avec le débruiteur stochastique D1.

### 2. Calendrier cosinus

[Nichol et Dhariwal, *Improved Denoising Diffusion Probabilistic Models*](https://arxiv.org/html/2102.09672v1), texte HTML accessible ; [notice](https://arxiv.org/abs/2102.09672) consultée. La section 3.2, équation 17, définit la courbe cos² normalisée ; les beta sont limités à 0,999 et l'article utilise `s=0.008`.

Adaptation : 100 pas et variance inverse fixée à la variance postérieure, sans variance apprise ni objectif hybride. La valeur 0,008 provenait dans l'article d'une considération de quantification des pixels ; ici elle est conservée comme paramètre initial imposé. La somme des étapes et la limite beta sont enregistrées dans le checkpoint. `alpha_bar` doit être recalculé après la limite beta pour que corruption et génération utilisent le même calendrier. Le bruit terminal est contrôlé, pas supposé.

### 3. Diffusion distributionnelle à score probabiliste

[Park et al., *Proper Scoring Rule-based Diffusion for Probabilistic Weather Forecasting*](https://arxiv.org/html/2609.38632v1), HTML accessible et date du 29 septembre 2026 vérifiée. Les équations 4 et 6–9, algorithme 1 et annexe B.1 sont consultés : corruption linéaire, score sur une distribution conditionnelle, même entrée corrompue et même niveau pour les membres d'apprentissage, latents indépendants du bruit de corruption. L'inférence en un passage utilise `t=1`, avec bruit de corruption et latent indépendants pour chaque membre.

Adaptation : aucun contexte météo global ; le conditionnement CO₂ est pris en charge par l'ancre et le réseau apprend une loi résiduelle scalaire supposée stable. Aucun objectif autoregressif, champ spatial, pondération latitude ou calendrier harmonique n'est repris. L'estimateur fair du papier est remplacé par l'almost fair fixé dans le cahier des charges. C0 utilise `u=0,t=1` pour mesurer l'apport des tâches auxiliaires. La prépublication ne valide pas cette adaptation sur 61 années ; les résultats locaux doivent la départager.

### 4. Almost fair CRPS

[Lang et al., *AIFS-CRPS*](https://arxiv.org/html/2412.15832v1), section 2.2 et équations 1–3 accessibles. L'estimateur fair remplace M² par M(M−1) dans le terme de dispersion ; l'almost fair mélange les estimateurs fair et empirique. Le papier explique une dégénérescence fair lorsque tous les membres sauf un égalent la cible et utilise `alpha=0.95`.

Adaptation : M=32, float32 sans AMP et architecture scalaire, plutôt que le système météo global. C0, D1 et D2 gardent la même convention. L'almost fair introduit un petit biais et n'est pas identifié au CRPS propre de population. Le benchmark garde l'estimateur empirique M².

### 5. Estimateurs CRPS

[Documentation officielle `scoringrules`, *Ensemble forecasts*](https://scoringrules.readthedocs.io/en/latest/crps_estimators.html), accessible. Les formes énergétiques empirique et fair et l'hypothèse de tirages indépendants confirment les dénominateurs M² et M(M−1). Le tri permet la même somme de distances sans matrice quadratique.

Choix local : float64 pour les scores rapportés ; correction fair/almost fair seulement pour l'apprentissage. Les 10 000 membres simulés n'augmentent pas le nombre d'années observées. La comparaison des mélanges doit calculer le score du mélange et ne pas moyenner les scores individuels.

### 6. Scores pondérés

[Documentation officielle `scoringrules`, *Weighted scoring rules*](https://scoringrules.readthedocs.io/en/latest/weighted_scores.html), accessible. La pondération par seuil correspond à un CRPS après transformation de la prévision et de l'observation ; `max(x,s)` cible la queue haute et `min(x,s)` la queue basse. Toutes les observations contribuent, y compris les non-événements.

Choix local : seuils q80 maxima et q20 minima ajustés sur le train de chaque fold ; reconstruction en °C avant la transformation d'apprentissage. L'objectif D2 additionne le score global et le score de queue. La transformation du score ne borne pas les prédictions exportées. Un pronostic de dépassement en absence d'événement reste pénalisé.

### 7. Gneiting et Ranjan

[University of Washington, *Comparing Density Forecasts Using Threshold and Quantile Weighted Scoring Rules*](https://stat.uw.edu/research/tech-reports/comparing-density-forecasts-using-threshold-and-quantile-weighted-scoring-rules), notice primaire et résumé accessibles via le moteur de recherche. La notice date le rapport technique du 1er avril 2008 ; la bibliographie `scoringrules` renvoie à la publication de 2011. Le résumé confirme l'intérêt des versions pondérées du CRPS pour mettre l'accent sur queues/centre en conservant la propriété du score.

Limitation réelle : l'ouverture directe de la notice a échoué deux fois, dont un timeout HTTP 400 ; la page primaire de rapports techniques a également expiré. Des liens PDF historiques tentés n'ont pas été accessibles (dont HTTP 502), et le DOI `10.1198/jbes.2010.08110` n'a pas pu être ouvert par l'outil. Le texte complet de cette référence n'est donc pas prétendu lu. Les formules effectivement codées sont vérifiées dans la documentation primaire accessible `scoringrules`, section précédente.

### 8. GEV et CO₂

[Changements de distribution des maxima annuels en Europe, ASCMO 9, 45–61 (2023)](https://ascmo.copernicus.org/articles/9/45/2023/), texte accessible, section méthodologique sur la GEV et le covariable `log(CO₂/280)` consultée. L'article étudie notamment une dépendance des paramètres GEV et des effets spatiaux, avec plusieurs modèles.

Adaptation : R1 ajuste une GEV aux résidus d'une ancre commune OLS à pente positive ; elle ne reproduit pas le modèle spatial ou l'estimation jointe GEV de l'article. La constante 280 dans le logarithme pourrait être absorbée par l'interception de l'ancre ; elle n'est pas une observation supplémentaire. Pour les minima, ajustement sur les résidus inversés puis retour au signe initial. Aucune donnée de l'article n'est téléchargée ou incorporée. La loi des résidus n'est pas garantie GEV, et la queue reste peu identifiée.

### 9. Validation temporelle

[Hyndman et Athanasopoulos, *Forecasting: Principles and Practice*, section 5.10](https://otexts.com/fpp3/tscv.html), accessible. La validation en origine glissante utilise uniquement des observations antérieures à chaque période évaluée.

Adaptation : trois blocs fixes de dix années, F1 1971–1980, F2 1981–1990 et F3 1991–2000, avec entraînement croissant commençant en 1940. L'ancre, l'échelle, les seuils, les références et le bootstrap sont réajustés dans le train de chaque fold. Le test 2001–2025 n'est pas une quatrième validation pour sélectionner un modèle.

## Vérifications primaires complémentaires

[Documentation officielle SciPy 1.16.2 de `genextreme`](https://docs.scipy.org/doc/scipy-1.16.2/reference/generated/scipy.stats.genextreme.html), consultée pour la convention de forme et le support. SciPy utilise `c=-xi` dans la convention GEV usuelle. Pour un résidu standardisé par localisation/échelle, le support dépend du signe de c ; une borne finie n'est pas nécessairement une borne plausible de température. La documentation en ligne latest est aussi accessible mais correspond à 1.18.0 ; elle ne remplace pas la version réellement utilisée localement.

[ECMWF : référence spatiale ERA5](https://confluence.ecmwf.int/pages/viewpage.action?navigatingVersions=true&pageId=78296807) et [ECMWF : ERA5-Land](https://www.ecmwf.int/en/era5-land), consultées uniquement pour la provenance générale. La première documente environ 31 km pour la résolution native ERA5 HRES ; la seconde environ 9 km pour ERA5-Land. Le starter et le contexte écrivent « ERA5 9 km » mais les CSV ne fournissent pas de métadonnées prouvant le produit exact, la maille ou l'interpolation. Le rapport doit identifier les fichiers fournis par le professeur et signaler cette incertitude de provenance, sans annoncer une résolution certifiée. Aucune donnée ECMWF supplémentaire n'est utilisée.

## Contrôle indépendant du kit

Le code original confirme des formes strictes `(25,10000)` et `(3,10000)`, dans l'ordre fourni. Les trois contrôles sont séparés pour maxima/minima : tolérance de médiane 0,1 °C, ratio de largeur q90−q10 ≥ 0,95, bornes inclusives `[0,50]` / `[-30,20]`. L'échec conduit à un retour `None` même si des scores sont affichés. Les formes incorrectes ou valeurs non finies déclenchent une assertion. Le départage à 0,05 °C décrit par le groupe n'est pas codé dans `kit.benchmark`.

Un ensemble déterministe peut passer la règle de largeur (`0 >= 0`) ; le diagnostic `non_degenerate` reste donc distinct de l'admissibilité officielle. La loi gaussienne et la GEV peuvent produire un tirage hors des bornes : il faut conserver le tirage et le statut d'élimination, sans changer les graines ni le couper.

## Tests exécutés pendant cet audit

Commande réelle :

```powershell
& 'C:/Users/edlas/AppData/Local/Programs/Python/Python312/python.exe' -m unittest discover -s tests -p test_core.py -v
```

Le premier passage exécuté a réussi 20 tests en 1,477 s (temps rapporté par unittest, hors démarrage Python/import PyTorch). Le fichier a ensuite reçu un contrôle supplémentaire du chargeur de compétition ainsi que des assertions précisant la cause des échecs et le diagnostic de dégénérescence. Le passage final a réussi **21 tests en 0,638 s**, avec le statut `OK` et un code de sortie 0. Aucun échec des tests de base n'a été observé.

Les fixtures sont synthétiques : formule brute O(M²) sur petits ensembles, cas déterministe, fair/almost fair et gradients finis, fausses alertes chaudes/froides, exactitude de l'ancre, contrainte de pente et plancher explicite, folds sans chevauchement et prétraitement insensible aux cibles futures, bootstrap résiduel circulaire vérifié contre un réajustement explicite à CO₂ fixé, ordre des projections avec tirages d'ancre partagés, contrôles du kit et conservation des sorties brutes, extraction stricte et refus de phase complète avant benchmark. Les tests neuronaux et de reprise sont confiés au module de tests spécialisé.

## Incidents et adaptations de lecture

- L'extraction texte PDF initiale a rencontré une `UnicodeEncodeError` cp1252 sur une ligature ; reprise avec `sys.stdout.reconfigure(encoding='utf-8')`, extraction réussie. Les sources sont restées intactes.
- Les PDF ont été lus avec `pypdf` et rendus avec le Poppler fourni par Codex. Les rendus intermédiaires sont dans `tmp/pdfs/source_review/`.
- Accès partiel à Gneiting–Ranjan, avec les échecs documentés ci-dessus. Aucune formule n'est attribuée à un texte inaccessible comme si elle y avait été vérifiée.

## Revue du pipeline avant le benchmark

Revue du code de `experiments.py`, `projections.py`, `benchmark_adapter.py`, `data.py` et de la CLI, sans lecture de la vérité ni chargement d'un checkpoint neuronal.

- La séparation train/validation est conservée : tous les ajustements statistiques utilisent le train du fold ; les cibles de validation ne sont employées que pour les scores et l'arrêt anticipé. Les scores de sélection sont ceux du mélange effectif à quotas fixes, pas la moyenne des scores individuels.
- D3/D4 reconstruisent les tirages à partir des checkpoints parents D1/D2. Les indices d'ancre et résidus sont communs entre scénarios ; les trajectoires utilisent une ancre commune et une nouvelle fluctuation à chaque année. Le calcul binomial à 2100 utilise un ensemble additionnel avec indices de réseau iid.
- La règle de proximité utilise un écart **strictement inférieur** à 0,05 °C, puis l'ordre de complexité fixé. Les cas synthétiques 0,04999 / 0,05 / 0,05001 °C vérifient cette frontière.
- Un risque réel de reprise après ouverture partielle du benchmark a été signalé : vérifier uniquement l'existence de `benchmark_results.json` pouvait autoriser un nouvel ajustement après une interruption du benchmark. Correction apportée avant toute ouverture réelle : sentinelle atomique `test_truth_opened.json` créée avant la lecture, gardes dans validation/sélection/ajustement/prédiction et reprise CLI réservée au même benchmark.
- Les empreintes de sélection finale, archive du code, configuration et entrées sont désormais vérifiées avant le chargement du kit et l'ouverture de la vérité, en complément des prédictions, checkpoints et kit déjà contrôlés. `selection_validation.json` conserve la sélection initiale sur validation ; `selection.json` conserve le candidat après les contrôles sans vérité. Le manifeste enregistre les deux empreintes et celle de `locked_source.zip`.
- L'audit de la phase complète compare désormais les trajectoires CO₂ de l'archive avec le fichier futur autorisé ; il contrôle leurs colonnes, années 2026–2100 et positivité avant les projections.

Après ces corrections, **26 tests de base réussissent en 3,765 s**, puis le nouveau passage avec l'empreinte de l'archive du code réussit également **26 tests en 3,618 s**, codes de sortie 0. Les nouveaux tests simulent intégralement la lecture du benchmark avec mocks : ils n'ouvrent aucun fichier réel de vérité. Ils vérifient la persistance du verrouillage si la lecture simulée échoue, le refus des quatre mutations de compétition en l'absence de résultats, le rejet des métadonnées modifiées avant lecture et la frontière de proximité. Les étapes d'entraînement et les tests neuronaux restent à la charge du pipeline principal et du module spécialisé.

## Empreintes SHA-256 des sources locales

| Source | SHA-256 |
|---|---|
| Plan | `204AC3D1B461C0A95BA06BFDF2CA5A8C0F30660BB04A33EEB018C305B02C86DC` |
| GUIDE.pdf | `713E5948768AFFEF650F9237ED36E04BED1127432E65B9B4274C7FAB6A6DAD2C` |
| Sujet PDF | `32E0FA2844456ED6E715C4CBCDDBA9AEA3DCDB6F47C712078EAE0BD43FC6FDBB` |
| CONTEXTE_POUR_LLM.md | `3978A1D6C89270B4A5D65B2FE5232402C8EC490007AEBDC99C0368646AAEB88B` |
| Starter | `3CEFDFB29FBD08238B31C3DCCBFDF1938C510CB61D3D7B20C9F27BFF1F56CD2F` |
| kit.py | `0997AC0DB31EE461F032469C376D100B54ED76FE6CBF67734EC52F46445C2EAF` |
