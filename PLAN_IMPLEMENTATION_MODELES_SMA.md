# Cahier des charges — implémentation, entraînement et évaluation du projet SMA

Date : 8 octobre 2026. Destinataire : agent Codex Sol 6.1, effort Ultra, dans ce même projet.

## 1. Mission et résultat attendu

Implémenter puis exécuter un pipeline complet, reproductible et compréhensible pour les températures extrêmes annuelles de Brest. Construire les références statistiques, entraîner les modèles génératifs et leurs variantes, comparer les résultats, exporter les prédictions compatibles avec le kit, produire les rapports, figures et notebooks exécutés. Le travail demandé inclut les expériences réelles ; fournir uniquement des scripts non exécutés ne suffit pas.

Objectif pédagogique : comprendre ce que chaque composante apporte, expliquer les méthodes mathématiquement et discuter leurs limites physiques. Une amélioration de score ou une « note maximale » ne peut pas être garantie. Une référence simple peut gagner ; le rapport doit le dire si les résultats le montrent.

Les choix de départ sont fixés ci-dessous. Résoudre les choix ordinaires d'implémentation sans demander une confirmation à chaque étape. Si une contrainte réelle impose une adaptation, la justifier et la consigner. Ne pas annoncer comme entraîné ou validé un modèle seulement codé.

### Périmètre

- Partie principale : modèles probabilistes des maxima et minima annuels, compétition interne du groupe, ablations, projections sous trois scénarios CO₂.
- Livrables pour le projet : code modulaire, configurations, scripts Windows et portables, checkpoints, données de résultats, rapport en français, figures et notebook explicatif/exécuté.
- Phase finale : réentraînement sur 1940–2025, projections annuelles 2026–2100 et intégration des deux parties du sujet dans le notebook, y compris l'analyse des vagues de chaleur.
- Aucun envoi, publication ou dépôt sur Moodle n'est demandé. Préparer les fichiers localement pour relecture et partage par l'équipe.

## 2. Sources, emplacement et environnement vérifié

### Emplacements actuels

Workspace où créer le code et les livrables :

```text
C:/Users/edlas/OneDrive/Documents/ChatGPT/Mini projet stochastique
```

Dossier contenant le kit, les données de compétition et les PDF :

```text
C:/Users/edlas/OneDrive/Bureau/MCE/Stochastique/Projet SMA
```

Fichiers du kit : `kit.py`, `exemple.py`, `LISEZMOI.md`, `CONTEXTE_POUR_LLM.md`, `GUIDE.pdf`, `miniprojet_MCE_SMA_2026.pdf`, `data/`.

Sources originales du professeur déjà disponibles dans le workspace :

```text
tmp/pdfs/miniprojet_starter.ipynb
tmp/pdfs/data_temp_brest.zip
```

L'archive contient `daily_temp_brest.csv`, `yearly_temp_brest.csv`, `yearly_future_co2.csv` et une entrée `/`. Ignorer cette entrée et extraire seulement les noms autorisés dans un dossier dédié ; vérifier que les destinations restent dans ce dossier.

Prévoir `--kit-dir` et des chemins relatifs configurables. Ne pas disperser des chemins absolus dans les modules. Conserver les originaux intacts. S'ils sont copiés pour rendre le projet portable, conserver leurs empreintes SHA-256 et séparer les données d'entraînement de la vérité de test.

### Environnement local observé

| Élément | Valeur vérifiée |
|---|---|
| Système | Windows, PowerShell |
| Python de travail | `C:/Users/edlas/AppData/Local/Programs/Python/Python312/python.exe` |
| Python | 3.12.10 |
| GPU | NVIDIA GeForce GTX 1660 Ti, 6 Go |
| Pilote NVIDIA | 555.97 |
| PyTorch | 2.5.1+cu121 |
| CUDA de PyTorch | 12.1 ; GPU disponible et calcul avec gradient testé |
| NumPy / pandas / SciPy | 2.3.5 / 2.3.3 / 1.16.3 |
| matplotlib / nbformat / scikit-learn | 3.10.8 / 5.11.1 / 1.9.1 |

Utiliser cet environnement s'il reste fonctionnel. Éviter une mise à jour globale de CUDA ou de PyTorch sans raison. Créer un environnement isolé si des dépendances supplémentaires sont nécessaires ; enregistrer les versions réellement utilisées.

Un microbenchmark synthétique avec un MLP de 1 217 paramètres a mesuré environ 2,0 secondes pour 500 étapes sur ce GPU. Ce résultat démontre la capacité matérielle, pas la durée du pipeline complet. Mesurer les temps réels de chaque expérience. Une RTX 3090 n'est pas nécessaire pour le périmètre principal.

## 3. Sujet du professeur et protocole du groupe : les distinguer

Le professeur demande une étude des vagues de chaleur, des prévisions probabilistes conditionnées au CO₂, une méthode récente de machine learning expliquée en LaTeX, les distributions futures et une analyse des minima. Les quatre axes de notation sont : code clair, sorties correctes avec unités, explication mathématique, discussion physique.

Le CRPS, la coupure en 2000, le classement interne et les trois contrôles de cohérence sont des choix du groupe. Le CRPS n'est pas explicitement demandé dans le sujet. La comparaison du groupe est prévue le 23 octobre 2026, le notebook final le 30 octobre 2026.

### Données de compétition

| Fichier | Contenu | Taille / période |
|---|---|---|
| `yearly_temp_brest_train.csv` | `valid_time,max,min,co2` | 61 années, 1940–2000 |
| `daily_temp_brest_train.csv` | `valid_time,mean` | 22 281 jours, 1940–2000 |
| `test_inputs.csv` | `valid_time,co2` | 25 années, 2001–2025 ; aucune température |
| `yearly_future_co2.csv` | `valid_time,ssp1-2.6,ssp2-4.5,ssp5-8.5` | 75 années, 2026–2100 |
| `verite_2001_2025.csv` | `annee,max,min` | réservé à l'évaluation finale |

Ces quatre fichiers d'entrée ont été vérifiés sans valeurs manquantes. Réauditer dates, doublons, colonnes, unités et positivité du CO₂ au démarrage.

Règles de compétition à appliquer :

1. Apprentissage et réglages uniquement à partir de 1940–2000.
2. Pour 2001–2025 et les projections, seules les entrées CO₂ fournies sont utilisables.
3. Aucune donnée extérieure : autre station, sortie de modèle climatique, température supplémentaire, information sur une canicule de test.
4. Les températures de test ne servent ni aux hyperparamètres, ni au choix d'une graine, ni au traitement des tirages.
5. Les connaissances générales de statistique et les articles méthodologiques sont utilisables. Ils ne fournissent pas de nouvelles observations d'apprentissage.
6. Les moyennes journalières ne sont pas des maxima ou minima horaires : leur maximum ne remplace pas le maximum annuel du fichier annuel.

Le groupe autorise plusieurs appels au benchmark, mais interdit le réglage sur la vérité. Notre pipeline applique une séparation plus stricte : verrouiller les configurations et les prédictions avant d'ouvrir la vérité de test.

Ne pas importer `exemple.py` pendant le développement : il appelle le benchmark à son niveau principal. Importer `kit.py` est possible, mais n'appeler `kit.benchmark` que dans la phase d'évaluation finale.

## 4. Hypothèse principale et ancre

Pour chaque variable, apprendre une loi de résidus annuels après retrait d'une tendance :

$$
Y_i=\mu(C_i)+R_i,\qquad \mu(C)=a+b\log(C).
$$

Le réseau principal apprend une distribution scalaire des résidus, sans entrée CO₂ supplémentaire. L'ancre fournit le conditionnement au CO₂ et l'extrapolation. C'est une hypothèse de stabilité de la loi résiduelle ; elle doit être vérifiée sur les données disponibles et explicitée dans le rapport.

Les modèles ne prédisent pas une météo quotidienne ni une trajectoire temporelle apprise. Ajouter du bruit pendant l'entraînement ne crée pas de nouvelles années indépendantes. Les 22 281 jours ne deviennent pas 22 281 exemples de maxima annuels.

### Ajustement de l'ancre

Reproduire la méthode du kit :

```python
b_ols, _ = np.polyfit(np.log(co2_train), y_train, 1)
b = max(b_ols, 0.0)
a = np.mean(y_train - b * np.log(co2_train))
r = y_train - (a + b * np.log(co2_train))
sigma = np.std(r, ddof=2)
z = r / sigma
```

Faire cet ajustement séparément pour `max` et `min`, et dans chaque découpage uniquement sur son entraînement. Centrer `log(C)` en interne est permis pour la stabilité numérique, en conservant une représentation équivalente et le centre utilisé. Enregistrer les paramètres et les pentes brutes avant contrainte.

Prévoir le cas d'une échelle quasi nulle avec un plancher numérique documenté ; ne pas présenter une distribution dégénérée comme un succès. Revenir en °C pour les prédictions et les métriques.

L'ancre est fournie dans l'exemple, mais n'est pas imposée à tous les membres du groupe. Elle est commune à nos ablations pour isoler les changements. Ne pas lancer d'emblée une recherche supplémentaire sur de nombreuses formes de tendance.

## 5. Modèles et variantes à implémenter

### Matrice principale obligatoire

| ID | Modèle | Objectif / variante | Comparaison utile |
|---|---|---|---|
| `R0_gaussian` | Ancre + résidus gaussiens | reproduction de l'exemple | niveau de référence |
| `R1_gev` | Ancre + loi GEV résiduelle | ajustement statistique | intérêt d'une loi adaptée aux extrêmes |
| `D0_ddpm` | Diffusion scalaire classique | prédiction du bruit par MSE | intérêt d'un générateur appris |
| `D1_ddm_crps` | Débruiteur stochastique distributionnel | score CRPS à plusieurs niveaux de bruit | apprentissage probabiliste direct |
| `D2_ddm_tail` | Même modèle que D1 | CRPS + pondération de la queue | attention aux fortes températures / extrêmes froids |
| `D3_ddm_anchor` | Réseau de D1 | ajout de l'incertitude de l'ancre | effet de l'incertitude d'estimation |
| `D4_ddm_tail_anchor` | Réseau de D2 | pondération + ancre incertaine | combinaison des deux ajouts |

Construire les variantes pour les maxima et les minima. D3 réutilise exactement les checkpoints de D1 ; D4 réutilise ceux de D2. Le bootstrap de l'ancre ne nécessite pas des centaines d'entraînements neuronaux.

### Deux contrôles supplémentaires légers

- `R2_empirical` : rééchantillonner les résidus d'entraînement. Ce contrôle mesure l'intérêt du réseau par rapport au simple réemploi de la distribution empirique.
- `C0_direct_crps` : petit générateur direct à entrée aléatoire, entraîné au même score que D1, sans tâches auxiliaires de débruitage. Il permet d'isoler leur effet. Pour conserver une architecture comparable, utiliser le même MLP avec `z_t=0`, `t=1` pendant l'entraînement et l'inférence, et le latent indépendant habituel.

Ces contrôles doivent figurer dans la validation et dans le rapport. Ils ne nécessitent ni grosses architectures, ni nouvelles données.

### R0 — référence exacte

Résidus normaux de moyenne zéro et écart-type `sigma` défini ci-dessus. Pour reproduire les résultats de `exemple.py`, respecter `np.random.default_rng(0)` et l'ordre des appels : `test_max`, `test_min`, `proj_max`, `proj_min`.

Une exécution de l'exemple original a reproduit les scores affichés de 1,70 °C pour les maxima et 1,06 °C pour les minima, avec les contrôles réussis. Archiver les scores non arrondis et la sortie originale lors de l'évaluation finale. Garder cette reproduction distincte de nos variantes utilisant d'autres conventions de graines.

### R1 — GEV

Ajuster une GEV aux résidus des maxima. Pour les minima, ajuster une GEV à `-r_min`, puis inverser le signe des tirages. Utiliser SciPy, documenter la convention `genextreme.c = -xi`.

Enregistrer localisation, échelle, forme, convergence, support et éventuelle borne de queue. Vérifier échelle positive et support valide. Signaler les ajustements instables ; ne pas remplacer silencieusement un échec par une autre loi. Les résidus ne sont pas automatiquement GEV : ce modèle est une référence empirique à évaluer. Les 61 observations identifient faiblement la queue.

### D0 — diffusion classique DDPM

Sur les résidus standardisés :

$$
z_k=\sqrt{\bar\alpha_k}\,z+\sqrt{1-\bar\alpha_k}\,\epsilon,
\quad \epsilon\sim\mathcal N(0,1),
\quad L=\mathbb E[(\epsilon-\epsilon_\phi(z_k,k/K))^2].
$$

Valeurs initiales : `K=100`, calendrier cosinus avec paramètre `s=0.008`, `beta <= 0.999`, petit MLP `[32,32]`, activations SiLU et sortie linéaire scalaire.

Vérifier que le bruit terminal est effectivement dominant (`alpha_bar[K] < 1e-3`). Ne pas associer 100 étapes au calendrier linéaire 1e-4 → 0.02 : le signal terminal resterait important. Le calendrier doit être stocké avec le checkpoint.

Échantillonnage ancestral à partir de `z_K ~ N(0,1)` :

$$
z_{k-1}=\frac{1}{\sqrt{\alpha_k}}
\left(z_k-\frac{\beta_k}{\sqrt{1-\bar\alpha_k}}\epsilon_\phi(z_k,k/K)\right)
+\sqrt{\tilde\beta_k}\,\eta,
\quad \tilde\beta_k=\beta_k\frac{1-\bar\alpha_{k-1}}{1-\bar\alpha_k}.
$$

Au dernier pas, ne plus ajouter de bruit. Ne pas écrêter arbitrairement les résidus standardisés à `[-1,1]`. Une implémentation inspirée d'images doit être adaptée aux scalaires et aux températures.

### D1 — diffusion distributionnelle avec score probabiliste

Ce modèle a un mécanisme différent de D0. Une MSE remplacée naïvement par CRPS dans un débruiteur déterministe ne suffit pas.

Corruption et générations :

$$
u=(1-t)z+t\epsilon,\quad \hat z_m=g_\phi(u,t,\zeta_m),
\quad \epsilon,\zeta_m\sim\mathcal N(0,1).
$$

Pour une observation et son ensemble de M sorties, garder le même `u` et le même `t` ; tirer M latents `zeta_m` indépendants, distincts du bruit de corruption. Utiliser un MLP avec entrées `[u,t,zeta]`, deux couches de 32 neurones, SiLU et sortie linéaire.

Départ : `t ~ Uniform(0,1)`, `M=32`. En inférence, `t=1`, `u` est un bruit indépendant et aucune température future n'est fournie. Un passage du réseau produit un tirage. Évaluer les checkpoints exclusivement avec ce mode d'inférence, pas avec des cibles de validation partiellement bruitées.

Ce mécanisme adapte une prépublication météo à une loi résiduelle scalaire stationnaire. Il n'a pas été validé par cet article sur notre petit jeu de données. Le contrôle C0 sert à mesurer l'effet des tâches auxiliaires.

### D2 — pondération de la queue

Maxima : seuil `s_hot = quantile(y_train, 0.80)`, transformation `h(x)=max(x,s_hot)`.

Minima : extrêmes froids, seuil `s_cold = quantile(y_train,0.20)`, transformation `h(x)=min(x,s_cold)`.

Objectif :

$$
L=L_{CRPS}(\hat Y,Y)+\lambda_{tail}L_{CRPS}(h(\hat Y),h(Y)),
\qquad \hat Y=\mu(C_i)+\sigma\hat z.
$$

La pondération porte sur les températures reconstruites en °C, pas directement sur `z`. Le seuil est recalculé sur l'entraînement de chaque découpage, identique pour tous les modèles évalués sur ce découpage.

Petite grille prévue : `lambda_tail in [0.5,1.0,2.0]`. Fixer le meilleur coefficient par validation globale, séparément pour maxima et minima. `lambda_tail=0` correspond au contrôle D1 et ne demande pas un entraînement dupliqué. Le poids effectif des seuils au-delà de la coupure vaut `1+lambda_tail`, contre 1 ailleurs.

### D3 / D4 — incertitude de l'ancre

Bootstrap résiduel à CO₂ fixé, `B=500` par ajustement :

1. Ajuster l'ancre sur le train et centrer les résidus.
2. Rééchantillonner ces résidus ; former `y_star_i = mu_hat(C_i) + r_star_i`.
3. Réajuster l'ancre sur ces réponses, avec la même contrainte `b>=0`.
4. Enregistrer les B couples de paramètres, les pentes brutes et la proportion de contraintes actives.
5. Pour un tirage futur, tirer un couple d'ancre et un résidu du réseau déjà entraîné, puis les additionner.

Option principale : blocs résiduels circulaires de longueur 3 pour préserver une dépendance locale éventuelle. Sensibilité légère : longueur 1, sans recherche sur le test. Consigner l'hypothèse de dépendance et l'incertitude liée au peu d'années. Ne pas utiliser un bootstrap naïf de paires qui modifie aussi la couverture du CO₂.

L'échelle et le réseau résiduel restent ceux de D1 ou D2 : c'est une approximation qui ajoute l'incertitude de l'ancre seulement. Elle ne quantifie pas toute l'incertitude des paramètres du générateur, de la forme de tendance ou du climat futur. Ce n'est pas un posterior bayésien.

Pour les trois scénarios à une année donnée, utiliser les mêmes tirages `(ancre,residu)` entre scénarios. Avec `b>=0`, cela garantit la monotonie de ce modèle et réduit le bruit de comparaison. Ne pas changer les graines après un résultat défavorable.

## 6. Scores : entraînement et évaluation

### CRPS d'évaluation, conforme au kit

Pour N tirages :

$$
CRPS_N=\frac1N\sum_i|x_i-y|-\frac1{2N^2}\sum_{i,j}|x_i-x_j|.
$$

Calculer par tri, en float64 pour les rapports, avec la même convention que `kit.crps`. Ne jamais construire une matrice 10 000 × 10 000 pour chaque année. Conserver les scores par année et leur moyenne.

### Score d'apprentissage avec un petit ensemble

Le score empirique avec dénominateur M² a un biais de taille d'ensemble. Pour M=32, implémenter aussi le score corrigé :

$$
fCRPS_M=\frac1M\sum_m|\hat y_m-y|
-\frac1{2M(M-1)}\sum_{m\ne n}|\hat y_m-\hat y_n|.
$$

Choix initial commun à C0/D1/D2 :

$$
afCRPS=0.95\,fCRPS+0.05\,CRPS_{emp}.
$$

Cette variante « almost fair » stabilise l'apprentissage mais introduit un petit biais ; ne pas la présenter comme identique au score propre de population. Garder la même convention et M entre variantes. Enregistrer dispersion et quantiles pour détecter un effondrement de la distribution. En cas d'instabilité, la diagnostiquer sur train/validation ; documenter toute modification commune avant le test.

L'évaluation officielle conserve le CRPS empirique original avec 10 000 tirages, sans cette correction.

### twCRPS d'évaluation

$$
twCRPS_{haut}(F,y;s)=CRPS(\max(X,s),\max(y,s)).
$$

Pour les extrêmes froids, remplacer `max` par `min`. Cette transformation ne modifie que le calcul du score ; elle n'est pas un bornage des prédictions. Toutes les années sont incluses, y compris pour pénaliser les fausses alertes.

Les seuils de test sont fixés sur 1940–2000 avant d'ouvrir la vérité, communs aux modèles. Les tableaux gardent séparément CRPS global et twCRPS. Le classement officiel n'est pas remplacé par un score combiné.

### Diagnostics complémentaires obligatoires

- Couverture et largeur moyenne des intervalles centraux 50 %, 80 %, 90 %.
- Biais moyen de prévision et MAE de la médiane, comme diagnostics de localisation.
- PIT / rang de l'observation dans l'ensemble ; traitement des égalités documenté, notamment pour R2.
- Brier de dépassement du seuil chaud, ou de passage sous le seuil froid, fixé sur l'entraînement ; indiquer le nombre d'événements observés.
- Résidus selon année et CO₂, quantiles, asymétrie et autocorrélation descriptive.
- Temps d'entraînement, d'inférence, nombre d'étapes et mémoire GPU mesurés.
- Pour les modèles bootstrap : dispersion des pentes et distribution des ancres à CO₂ historique et futur.

Les 10 000 tirages ne sont pas 10 000 observations climatiques réelles. L'incertitude des différences de scores vient notamment du nombre d'années. Ne pas certifier une calibration sur la seule apparence d'un PIT avec 25 points.

## 7. Validation, sélection et verrouillage

### Découpages fixés

| Fold | Entraînement | Validation |
|---|---|---|
| `F1` | 1940–1970 : 31 années | 1971–1980 : 10 années |
| `F2` | 1940–1980 : 41 années | 1981–1990 : 10 années |
| `F3` | 1940–1990 : 51 années | 1991–2000 : 10 années |

Ajuster à chaque fold l'ancre, sigma, la loi résiduelle, les seuils et les bootstraps sur le train uniquement. Interdire les résidus calculés avec une ancre ajustée sur 1940–2000 dans F1/F2/F3. Les dates de validation n'entrent pas dans l'ajustement des prétraitements.

### Réglages initiaux communs

```yaml
seed_train: [0, 1, 2]
device: auto
dtype_train: float32
amp: false
hidden_dims: [32, 32]
activation: silu
optimizer: adamw
learning_rate: 0.001
weight_decay: 0.0001
batch_size: 64
max_steps: 10000
min_steps: 1000
eval_every: 250
patience_evaluations: 8
gradient_clip_norm: 1.0
crps_training_members: 32
almost_fair_alpha: 0.95
samples_early_stopping: 4096
samples_comparison: 10000
sampling_batch_size: 4096
ddpm_steps: 100
ddpm_schedule: cosine
tail_lambda_grid: [0.5, 1.0, 2.0]
anchor_bootstrap_replicates: 500
anchor_bootstrap_block_length: 3
```

Les mini-batches peuvent rééchantillonner des années d'entraînement, puisque le nombre d'années est inférieur à 64. Cela ne change pas le nombre d'observations indépendantes. Ajuster la taille de lot seulement si une contrainte mesurée le justifie. Pas de recherche exhaustive sur des dizaines d'architectures.

Utiliser un générateur aléatoire distinct pour l'évaluation : le calcul du CRPS de validation ne doit pas perturber la suite de bruit d'entraînement. Early stopping sur CRPS global de validation, en mode d'inférence futur approprié. Conserver le meilleur checkpoint et aussi le dernier pour reprise.

Comparer finalement tous les checkpoints retenus avec 10 000 tirages par année et des graines d'évaluation fixées. Enregistrer chaque fold/seed et l'agrégation. Si un réseau reste manifestement sous-entraîné, une adaptation justifiée sur la validation peut être faite avant verrouillage, sans ouvrir le test ; journaliser ce changement.

### Sélection interne

1. Critère principal : CRPS global du mélange des trois réseaux, moyen sur les 30 années de validation. Construire ce mélange dans chaque fold avec 3 334 / 3 333 / 3 333 tirages. La moyenne des scores des réseaux individuels n'est pas le score du mélange ; conserver les scores individuels et leur dispersion comme diagnostics.
2. Examiner aussi F3, le twCRPS et les couvertures pour expliquer les compromis ; ne pas remplacer discrètement le critère principal.
3. Avec un écart de CRPS inférieur à 0,05 °C, traiter le résultat comme proche et privilégier la solution la moins complexe, puis la moins coûteuse, selon une règle écrite dans la configuration avant la sélection. Cette règle interne est distincte du départage officiel entre membres par CRPS des minima.
4. Choisir l'objectif pondéré et les réglages des minima sur leur propre validation ; ne pas copier aveuglément le lambda des maxima.
5. Établir un classement de candidats sur validation, puis retenir le meilleur admissible après les contrôles sans vérité décrits ci-dessous. Verrouiller ce candidat participant et ses choix max/min avant la lecture du test. Le rapport peut montrer les ablations de test préenregistrées, sans sélectionner a posteriori une nouvelle variante.

Pour chaque réseau retenu, réentraîner sur les 61 années complètes. Le nombre d'étapes final vient, par exemple, de la médiane des meilleurs nombres d'étapes des folds pour cette configuration ; fixer cette règle dans le manifeste, sans early stopping sur le test. Les années utilisées en validation sont alors réintégrées.

Convention de modèle final : mélange à poids égaux des trois réseaux entraînés avec les graines 0/1/2. Pour 10 000 tirages, utiliser 3 334 / 3 333 / 3 333 tirages et enregistrer cette convention. Produire aussi les diagnostics des graines individuelles, sans choisir la meilleure graine après le test. R0 exact garde sa convention propre.

Créer `selection.json` puis `evaluation_manifest.json` avec configurations résolues, checkpoints, empreintes, seuils, étapes, graines, modèles à évaluer et candidat désigné. Produire les NPZ et vérifier les contrôles calculables sans vérité avant l'appel au benchmark. La politique prédéfinie permet d'exclure un candidat qui échoue et de retenir le meilleur candidat déjà validé et admissible, selon le classement de validation. Ne pas changer les graines, écrêter les tirages ou modifier la configuration pour forcer l'admissibilité. Si aucun candidat ne passe, le signaler.

Une révision méthodologique avant ouverture du test doit générer un nouveau manifeste et repasser la validation concernée. Une fois la vérité ouverte, les variantes et le candidat participant restent figés.

## 8. Benchmark officiel et formes de sortie

Exporter un NPZ par configuration finale, contenant exactement :

| Clé | Forme | Ordre |
|---|---|---|
| `test_max` | `(25,10000)` | années 2001 → 2025 |
| `test_min` | `(25,10000)` | années 2001 → 2025 |
| `proj_max` | `(3,10000)` | SSP1-2.6, SSP2-4.5, SSP5-8.5 en 2100 |
| `proj_min` | `(3,10000)` | même ordre |

Valeurs finies, unités °C, métadonnées années/scénarios dans un fichier séparé. Le kit compare les lignes sans réalignement automatique ; vérifier leur ordre explicitement.

Appeler le `kit.benchmark` original, intact. Capturer stdout, retour, scores exacts, diagnostics et statut admissible/éliminé. Sa valeur de retour vaut `None` en cas d'échec, même si des scores sont affichés.

### Contrôles éliminatoires du groupe, pour chaque variable

1. Médianes : `SSP1 <= SSP2 + 0.1` et `SSP2 <= SSP5 + 0.1`.
2. Largeur `q90-q10` en 2100/SSP5 au moins égale à 0,95 fois la largeur moyenne des 25 années de test.
3. Tous les tirages de test et de projection dans `[0,50]` pour les maxima, `[-30,20]` pour les minima.

Ces bornes et contrôles sont des conventions du groupe. Ne pas leur attribuer une validation physique universelle. Un modèle déterministe peut passer le contrôle de largeur puisque `0 >= 0` : ajouter un diagnostic de non-dégénérescence, distinct des règles officielles.

Le groupe documente un départage par CRPS des minima quand les CRPS des maxima diffèrent de moins de 0,05 °C. Cette règle n'est pas codée dans `kit.benchmark` : l'expliquer dans le rapport sans modifier le kit. Pour un tableau comportant plus de deux modèles, annoncer la règle de regroupement autour du meilleur CRPS admissible ; ne pas masquer la proximité des scores.

### Tirages hors bornes

Conserver et évaluer les prédictions brutes. Pas de clipping silencieux, de sélection de graines, de rejet opportuniste ou d'élargissement des intervalles après examen du test.

Si une loi bornée/tronquée est scientifiquement nécessaire, la définir comme variante explicite avant l'ouverture du test, l'appliquer dans toute sa validation, conserver les sorties brutes et documenter taux de rejet et effet sur la distribution. Le clipping crée des masses aux limites. Un modèle qui échoue doit être indiqué comme éliminé ; un score bas ne suffit pas à le rendre admissible.

## 9. Phase finale du projet : 1940–2025 et 2026–2100

Après les évaluations verrouillées, utiliser les fichiers complets fournis par le professeur, dans une phase distincte. Réentraîner le candidat retenu sur 1940–2025 avec ses choix fixés. Ces modèles ne doivent jamais être présentés comme ayant un score hors échantillon sur 2001–2025.

Produire les distributions annuelles pour 2026–2100 sous les trois scénarios, pour maxima et minima. Stocker années, scénarios, médianes, moyennes, quantiles et probabilités ; éventuellement les ensembles complets dans un NPZ compressé. Les ensembles `(3,75,10000)` restent raisonnables en mémoire, mais la génération doit pouvoir se faire par lots.

Le CO₂ 2100 fourni vaut environ 400 / 527 / 946 ppm selon les scénarios. Lire les valeurs exactes dans le CSV. Vérifier et signaler l'éventuelle rupture entre le CO₂ historique 2025 et les scénarios 2026 ; ne pas modifier les trajectoires silencieusement.

### Corrélations et transformations demandées dans le sujet

Calculer les corrélations de Pearson entre maxima annuels et CO₂, puis entre minima annuels et CO₂. Comparer au minimum CO₂ brut et `log(CO₂)`. Si d'autres transformations ou moyennes glissantes sont étudiées, justifier leur sens physique, les fenêtres et le traitement des bords. Distinguer une analyse descriptive d'une variable effectivement utilisée par le modèle ; ne pas employer une moyenne glissante centrée utilisant des températures futures comme entrée de prévision.

Produire les tableaux et nuages de points sur 1940–2000 pendant le développement, puis sur 1940–2025 dans l'étude finale. Une meilleure corrélation descriptive ne prouve ni un lien causal complet, ni une meilleure extrapolation. Si une référence statistique gagne, conserver l'étude et l'explication du meilleur modèle neuronal dans le notebook pour documenter la méthode récente et ce qu'elle apporte ou n'apporte pas.

### Dépassement de 40 °C

- Résultat principal : `P(Tmax_2100 > 40)` pour chaque scénario.
- Rapporter `k/N`, N, k et un intervalle d'incertitude Monte-Carlo conditionnel au modèle ajusté. Pour employer un intervalle binomial, générer un ensemble supplémentaire où l'indice du réseau est tiré indépendamment avec probabilité 1/3 à chaque simulation, ainsi que l'ancre bootstrap et le résidu. Les quotas fixes 3 334 / 3 333 / 3 333 du benchmark constituent un échantillonnage stratifié ; une autre possibilité est de calculer explicitement une incertitude stratifiée. Ne pas confondre les deux conventions.
- Avec zéro dépassement sur 10 000 tirages : écrire « aucun dépassement simulé » et donner la résolution / une borne Monte-Carlo, pas « probabilité physique nulle ».
- Cette erreur Monte-Carlo ne représente pas l'incertitude de validité du modèle ou de la queue.
- Si une simulation supplémentaire est utile pour la précision numérique, augmenter N par lots et l'annoncer ; elle ne crée pas de données historiques nouvelles.

Résultat complémentaire : probabilité d'au moins un dépassement entre 2026 et 2100. Il demande une hypothèse temporelle explicite. Sous indépendance conditionnelle des résidus, simuler une nouvelle fluctuation pour chaque année. Pour D3/D4, garder le même tirage d'ancre sur toute une trajectoire : la tendance incertaine crée une dépendance entre années.

La formule `1-product(1-p_t)` avec des probabilités marginales suppose l'indépendance des années. Avec une ancre aléatoire partagée, intégrer plutôt les probabilités conditionnelles à chaque ancre ou simuler les trajectoires. Les tirages communs utilisés pour comparer les distributions marginales des scénarios ne constituent pas, à eux seuls, une trajectoire temporelle valide.

### Partie 1 du notebook : vagues de chaleur

Utiliser les températures moyennes journalières du fichier approprié à la phase : 1940–2000 pour un aperçu sans vérité de test ; 1940–2025 pour l'étude descriptive finale.

1. Construire un calendrier climatologique de 365 jours à partir du mois/jour, sans décalage après février dans les années bissextiles.
2. Calculer q10/q50/q90 par jour calendaire, puis lisser par moyenne mobile circulaire de 31 jours.
3. Exclure le 29 février du calcul des quantiles climatologiques ; interpoler son seuil entre le 28 février et le 1er mars pour la détection des événements. Conserver les dates réelles et leur continuité.
4. Détecter les suites maximales de jours dont la moyenne dépasse q90 lissé. Départ : durée minimale 3 jours, avec sensibilité descriptive à 2 jours.
5. Intensité principale : moyenne de `T_mean - q50_lissé` pendant l'événement, en °C. Donner également l'excès moyen au-dessus de q90 et définir clairement les deux grandeurs.
6. Tracer le cycle saisonnier et le diagramme durée–intensité coloré par année ; exporter un tableau des événements avec début, fin, durée, intensités, année de début.
7. Décrire la période de référence climatologique et expliquer qu'une analyse descriptive sur toute la période n'est pas une prévision hors échantillon.

Conserver la structure des deux parties du notebook du professeur et ses questions. Identifier la provenance exacte des données ; ne pas reprendre sans vérification une résolution « ERA5 9 km », qui peut correspondre à ERA5-Land plutôt qu'à ERA5.

## 10. Architecture logicielle et commandes

Organisation indicative, adaptable sans modifier les objectifs :

```text
README.md
requirements.txt ou pyproject.toml
configs/
  base.yaml
  experiments.yaml
src/sma/
  data.py, splits.py, anchor.py, bootstrap.py
  models/gaussian.py, gev.py, empirical.py, ddpm.py, ddm.py
  scores.py, diagnostics.py, training.py, sampling.py
  benchmark_adapter.py, selection.py, reporting.py, heatwaves.py
scripts/
  run_pipeline.py
  run_competition.ps1
  run_full_project.ps1
tests/
notebooks/
reports/
artifacts/competition/
artifacts/full_project/
```

Prévoir une CLI avec commandes séparées. Exemples à rendre effectivement exécutables ou remplacer par des équivalents documentés :

```powershell
python scripts/run_pipeline.py audit-data --config configs/base.yaml
python scripts/run_pipeline.py smoke --config configs/base.yaml
python scripts/run_pipeline.py validate --config configs/experiments.yaml
python scripts/run_pipeline.py select --config configs/experiments.yaml
python scripts/run_pipeline.py fit-final --selection artifacts/competition/selection.json
python scripts/run_pipeline.py predict --selection artifacts/competition/selection.json
python scripts/run_pipeline.py benchmark --manifest artifacts/competition/evaluation_manifest.json
python scripts/run_pipeline.py report --phase competition
python scripts/run_pipeline.py refit-full --selection artifacts/competition/selection.json
python scripts/run_pipeline.py project-full --phase full_project
python scripts/run_pipeline.py report --phase full_project
```

Les scripts doivent traiter les chemins contenant des espaces, reprendre une expérience interrompue et éviter de réentraîner des modèles dont les checkpoints/configurations sont identiques. Les entrées D3/D4 référencent les checkpoints parents et ajoutent leurs propres artefacts bootstrap.

### Journalisation minimale de chaque run

- Identifiant, modèle, variable, phase, fold, configuration résolue et empreinte.
- Empreintes des entrées autorisées, version du code / commit si Git disponible.
- Versions Python/packages, GPU, CUDA, dtype et dispositif.
- Graines Python/NumPy/PyTorch ; graines distinctes de bootstrap, apprentissage et inférence.
- Ancre, échelle, seuils, paramètres GEV ou calendrier de diffusion.
- Étapes, meilleur checkpoint, historique de loss et métriques de validation.
- Temps mesurés, mémoire GPU allouée et réservée, erreurs et motifs d'échec.
- État de l'optimiseur et des générateurs aléatoires pour reprise fidèle.
- Traçabilité configuration → checkpoint → prédictions → scores → rapport.

Utiliser du logging local ; aucun service externe de suivi n'est nécessaire. En mode CUDA, float32 et AMP désactivé au départ. CPU en repli documenté. Sérialiser les gros entraînements sur l'unique GPU ; les ajustements statistiques et certaines analyses peuvent se faire sur CPU.

## 11. Vérifications nécessaires avant les longues expériences

Écrire des tests ciblés sur les risques réels, puis les exécuter :

1. CRPS par tri égal à la formule brute sur un petit ensemble ; cas déterministe égal à l'erreur absolue.
2. Score fair/almost fair et gradients finis ; test de la convention M versus M−1.
3. twCRPS égal au score des valeurs transformées ; cas de fausse alerte pénalisé ; orientation correcte pour minima.
4. Dates et indices des folds, prétraitements ajustés sur train uniquement, aucun accès à la vérité dans entraînement/prédiction.
5. DDPM : cohérence du calendrier, bruit terminal, variance postérieure et dernier pas.
6. DDM : même conditionnement dans un ensemble d'apprentissage, latents indépendants, inférence t=1 sans cible ; sortie non dégénérée.
7. Bootstrap : CO₂ inchangé, contraintes appliquées, ancre partagée entre scénarios et le long des trajectoires appropriées.
8. Exports : dimensions, années, scénarios, unités, finitude et conservation des échecs de bornes.
9. Fixtures synthétiques pour les trois contrôles du kit, avec cas qui réussissent et cas qui échouent.
10. Sauvegarde/reprise d'un checkpoint avec états RNG et optimiseur.

Le smoke doit réellement entraîner chaque famille neuronale quelques étapes sur un fold interne, produire un checkpoint, des prédictions et des métriques. Vérifier également la capacité à apprendre une petite distribution synthétique connue, à coût limité, pour détecter une erreur d'échantillonnage avant les expériences climatiques.

Ne pas élargir les tests sans risque identifié. Une fois les vérifications utiles passées, lancer la matrice d'expériences plutôt que rester indéfiniment en préparation.

## 12. Rapports, figures et livrables

### Fichiers obligatoires

- `README.md` : installation, commandes, ordre des phases, reprise, durée réellement mesurée, emplacement des données.
- Configurations de toutes les expériences et manifeste verrouillé.
- Code et scripts exécutables, tests ciblés et résultat de leur exécution.
- Checkpoints et paramètres statistiques, historiques et statistiques bootstrap.
- CSV/JSON de validation par fold/seed/variable, résumé agrégé et sélection.
- NPZ officiels et rapport du benchmark original avec statuts admissibles/éliminés.
- `reports/rapport_competition.md`, `reports/rapport_projections.md`, `reports/synthese_equipe.md`.
- Un notebook d'expériences exécuté et un notebook de rendu du projet avec les deux parties, équations et interprétations en français. Réutiliser les artefacts pour éviter de longs réentraînements à chaque ouverture.
- Exports des figures en PNG et SVG ou PDF, avec légendes et unités.
- Journal clair de ce qui a été exécuté, de ce qui a échoué et des adaptations faites.

### Figures et tableaux attendus

1. Températures annuelles, CO₂, transformations, tableaux de corrélations Pearson et ancre ajustée, distinguant les phases de données.
2. Lois résiduelles des références et générateurs ; histogrammes/quantiles observés, paramètres et supports GEV.
3. Courbes d'apprentissage et validation des réseaux.
4. CRPS global et twCRPS par fold, graines et variante ; tableau des ablations.
5. Couverture versus largeur des intervalles, PIT/rangs et probabilités des événements observables.
6. Résultats officiels : scores, statut des contrôles, proximité des modèles et coût de calcul.
7. Distribution des pentes bootstrap et des ancres projetées.
8. Projections 2026–2100 : médianes et intervalles par scénario et variable.
9. Distributions en 2100 avec le seuil 40 °C, probabilités annuelles et précision Monte-Carlo.
10. Cycle saisonnier, événements et diagramme durée–intensité des vagues de chaleur.

### Discussion obligatoire

- Quel ajout améliore réellement le CRPS ? Le gain existe-t-il sur plusieurs folds et graines ?
- Que coûte l'amélioration éventuelle des extrêmes en score global ou en complexité ?
- La diffusion apporte-t-elle plus que GEV, résidus empiriques ou générateur direct ?
- Quelle part de dispersion provient de la fluctuation annuelle et de l'ancre incertaine ?
- Quelles hypothèses assurent l'extrapolation, et lesquelles ne peuvent pas être vérifiées ?
- Pourquoi un bon CRPS sur 25 années ne valide pas la queue à 40 °C en 2100 ?
- Pourquoi CO₂ est un covariable de tendance, sans démonstration causale locale complète ?
- Quelle différence entre incertitude Monte-Carlo, incertitude d'estimation et erreur de modèle ?
- Quels résultats restent fragiles avec 61 puis 86 observations annuelles ?

La synthèse équipe doit être courte, présenter le candidat proposé, les résultats mesurés, les limites et les fichiers à partager. Les rapports détaillés doivent permettre de reproduire et comprendre chaque conclusion.

## 13. Ordre d'exécution et critères de fin

### Ordre

1. Lire les sources, auditer les données autorisées et l'environnement ; créer l'organisation du projet.
2. Implémenter scores, splits, ancre, références et contrôles ; vérifier les points critiques.
3. Implémenter D0, C0, D1 et D2 ; faire les smokes.
4. Implémenter le bootstrap, D3/D4 et les diagnostics, avec réutilisation des réseaux parents.
5. Lancer les validations prévues pour maxima et minima ; produire les tableaux et choisir les réglages.
6. Verrouiller la sélection ; réentraîner 1940–2000 ; générer, précontrôler et figer les sorties.
7. Exécuter le benchmark officiel et produire le rapport de compétition sans modifier les modèles en réponse aux scores.
8. Réentraîner le candidat retenu sur 1940–2025 ; produire les projections et l'analyse descriptive finale.
9. Exécuter les notebooks, vérifier les figures, écrire les rapports et la synthèse équipe.

### Critères de fin

- Toutes les familles et variantes principales ont été exécutées ou leur échec technique/scientifique est documenté avec un diagnostic réel.
- Références reproductibles, seeds et règles de sélection enregistrées ; aucune sélection opportuniste sur le test.
- Scores et unités corrects, métriques de validation et de test clairement séparées.
- Sorties compatibles avec le kit et statuts honnêtes des contrôles.
- Checkpoints, scripts, configurations, manifests, rapports et figures sauvegardés dans le workspace.
- Notebook exécuté, explication mathématique et discussion physique présentes ; les deux parties du sujet sont couvertes.
- Commandes de reproduction essayées, chemins portables et reprise vérifiée.
- Aucun gain, score, temps ou résultat présenté comme mesuré sans exécution correspondante.

Le travail est terminé quand ces artefacts et expériences existent, pas lorsque le code est simplement écrit. Si un obstacle empêche une phase, conserver les sorties déjà réalisées et expliquer précisément le blocage, sans inventer les résultats manquants.

## 14. Références méthodologiques à consulter

Ces sources expliquent les méthodes ; elles ne constituent pas des données climatiques supplémentaires et leurs performances publiées ne se transfèrent pas automatiquement à Brest.

- [DDPM — Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) : corruption et génération classique.
- [Improved DDPM](https://arxiv.org/abs/2102.09672) : calendrier cosinus.
- [Proper Scoring Rule-based Diffusion for Probabilistic Weather Forecasting](https://arxiv.org/html/2609.38632v1) : prépublication du 29 septembre 2026 ; débruiteur stochastique, tâches à plusieurs niveaux de bruit et inférence à t=1. Notre adaptation est scalaire et ne reprend pas le contexte météo global.
- [AIFS-CRPS](https://arxiv.org/html/2412.15832v1) : apprentissage d'ensembles avec score probabiliste et variante almost fair.
- [Documentation officielle scoringrules : estimateurs du CRPS](https://scoringrules.readthedocs.io/en/latest/crps_estimators.html) : score empirique et corrigé.
- [Documentation officielle scoringrules : scores pondérés](https://scoringrules.readthedocs.io/en/latest/weighted_scores.html) : pondération par seuil et transformation max/min.
- [Gneiting et Ranjan : scores pondérés](https://stat.uw.edu/research/tech-reports/comparing-density-forecasts-using-threshold-and-quantile-weighted-scoring-rules) : fondement statistique.
- [Changes in the distribution of annual maximum temperatures in Europe](https://ascmo.copernicus.org/articles/9/45/2023/) : exemple de modélisation GEV et covariable CO₂ ; ne pas importer les données de l'article.
- [Forecasting: Principles and Practice — validation temporelle](https://otexts.com/fpp3/tscv.html) : validation chronologique.

Vérifier les conventions mathématiques dans les articles et la documentation utilisée pour coder. En cas de différence avec une publication, annoncer l'adaptation précisément dans le rapport.
