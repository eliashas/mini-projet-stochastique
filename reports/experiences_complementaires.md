# Expériences complémentaires réellement exécutées

Le test 2001–2025 avait déjà été consulté avant cette intégration. Les résultats
ci-dessous sont exploratoires. Tous les réglages nouveaux ont utilisé les
validations 1971–2000 et les contrôles sans températures test.

## Décision et résultats

La validation retient **D3 pour Tmax** et
**D1 pour Tmin**. Aucun repli n'a été nécessaire après
les contrôles. Le benchmark original a renvoyé un résultat admissible :

| variable | model | crps | twcrps | coverage80 | width80 | bias |
| --- | --- | --- | --- | --- | --- | --- |
| max | D3 | 1.6500 | 0.6814 | 0.7600 | 6.1603 | -1.2878 |
| min | D1 | 1.0361 | 0.1650 | 0.8400 | 5.7674 | -0.8090 |

Sur la validation, H0 préfère un poids bayésien de **0 pour les deux variables**.
Les composants choisis sont {'max': 'D3', 'min': 'D1'}. Il n'y a donc pas de
gain du mélange retenu ; annoncer une fusion gagnante serait trompeur.
H1 est une combinaison modulaire, sans double comptage de l'échelle ou du bruit.

| variable | model | crps_validation | twcrps_validation | crps_test | twcrps_test | admissible |
| --- | --- | --- | --- | --- | --- | --- |
| max | Bayes | 1.1690 | 0.3989 | 1.5802 | 0.6932 | True |
| max | D1 | 1.1231 | 0.3867 | 1.7013 | 0.6932 | True |
| max | D3 | 1.1142 | 0.3787 | 1.6500 | 0.6814 | True |
| max | GEV | 1.1653 | 0.4171 | 1.6798 | 0.7150 | True |
| max | H1 | 1.1610 | 0.3998 | 1.5951 | 0.6891 | True |
| max | QR_1 | 1.1369 | 0.3995 | 1.7994 | 0.7121 | True |
| max | R_linear | 1.1820 | 0.4189 | 1.6954 | 0.7272 | True |
| max | R_log | 1.1764 | 0.4184 | 1.7077 | 0.7296 | True |
| min | Bayes | 1.2166 | 0.4276 | 0.9800 | 0.1381 | True |
| min | D1 | 1.1681 | 0.4094 | 1.0361 | 0.1650 | True |
| min | D3 | 1.1737 | 0.4069 | 0.9893 | 0.1527 | True |
| min | H1 | 1.2408 | 0.4231 | 0.9693 | 0.1406 | True |
| min | QR_1 | 1.1957 | 0.4137 | 1.0302 | 0.1537 | True |
| min | R_linear | 1.2219 | 0.4295 | 1.0645 | 0.1523 | True |
| min | R_log | 1.2195 | 0.4290 | 1.0645 | 0.1523 | True |
| min | Reda_min | 1.2415 | 0.4243 | 1.0997 | 0.1684 | False |

Bayes est meilleur en CRPS global test sur les maxima, alors que D3 est meilleur
en validation. D3 obtient un twCRPS Tmax inférieur à celui de Bayes sur ce test :
le classement dépend de la question évaluée. La sélection reste celle de la
validation. Les faibles écarts doivent être lus avec leur incertitude :

| variable | model | reference | difference_C | lower95_C | upper95_C | n_years | blocks | replicates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| max | D3 | Bayes | 0.0698 | -0.0218 | 0.1483 | 25.0000 | 3.0000 | 4000.0000 |
| max | D3 | R_log | -0.0577 | -0.1206 | 0.0006 | 25.0000 | 3.0000 | 4000.0000 |
| max | H1 | Bayes | 0.0149 | -0.0092 | 0.0366 | 25.0000 | 3.0000 | 4000.0000 |
| min | D1 | Bayes | 0.0560 | 0.0137 | 0.0933 | 25.0000 | 3.0000 | 4000.0000 |

L'intervalle est un bootstrap apparié par blocs sur seulement 25 années ; il
ne corrige ni le choix de modèles après consultation historique du test ni
l'extrapolation en 2100. Le fichier `sensibilite_monte_carlo.csv` sépare la
variation des scores due aux tirages de cette incertitude d'échantillonnage.

## Ce que montrent les ablations

L'ancre linéaire en CO₂ ne dépasse pas l'ancre logarithmique sur les validations
Tmax (voir tableau), même si son test est légèrement meilleur. Cette observation
ne justifie pas un changement de tendance après test. Les QR peu pénalisées
extrapolent mal pour Tmin ; certaines perdent la monotonie et QR_0.01 sort des
bornes. Le bootstrap Tmin à pente libre de Reda échoue aussi en monotonie.
Les échecs sont dans `controles_kit.csv`, sans troncature des températures.

La GEV adaptée obtient un CRPS Tmax test différent du 1,66 °C annoncé par Reda.
L'estimation est recentrée et le support de vraisemblance est contrôlé ; les
tirages utilisent la graine commune. Les deux valeurs sont distinguées, sans
attribuer cet écart à une amélioration générale. Tous les supports finaux sont
positifs ; les mises à jour refusées sont tracées.

## Projections réajustées sur 1940–2025

| variable | model | scenario | p_2100 | hits_2100 | mc_lower95 | mc_upper95 | p_at_least_one |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max | D3 | ssp1-2.6 | 0.0000 | 0.0000 | 0.0000 | 0.0004 | 0.0001 |
| max | D3 | ssp2-4.5 | 0.0000 | 0.0000 | 0.0000 | 0.0004 | 0.0022 |
| max | D3 | ssp5-8.5 | 0.0301 | 301.0000 | 0.0268 | 0.0336 | 0.1726 |
| min | D1 | ssp1-2.6 | 0.5473 | 5473.0000 | 0.5375 | 0.5571 | 1.0000 |
| min | D1 | ssp2-4.5 | 0.4063 | 4063.0000 | 0.3967 | 0.4160 | 1.0000 |
| min | D1 | ssp5-8.5 | 0.1666 | 1666.0000 | 0.1593 | 0.1741 | 1.0000 |

Pour Tmax la probabilité concerne 40 °C ; pour Tmin elle concerne le passage
sous 0 °C. Les bornes MC sont binomiales, conditionnelles à la loi simulée.
Un zéro sur 10 000 membres ne prouve pas une impossibilité. Le risque cumulé
suppose des innovations indépendantes conditionnellement aux paramètres, ces
paramètres restant communs aux 75 ans. Changer cette dépendance changerait le
risque cumulé sans nécessairement changer les probabilités annuelles.

`sensibilite_projections.csv` conserve Bayes, D1, D3, H1, l'ancre linéaire et
GEV/Reda_min. Les différences de loi et de tendance dominent souvent le petit
bruit Monte-Carlo. Les trois scénarios sont conditionnels : aucune probabilité
n'est attribuée au choix d'un SSP.

## Partie descriptive et coûts

La chronologie réelle donne 421 épisodes d'au moins trois jours,
contre 798 d'au moins deux jours. Durée maximale :
14 jours ; intensité moyenne à q50 :
3.587 °C. Le 29 février est conservé dans les séries
continues avec seuil interpolé. La climatologie complète sert à la description,
pas au choix des modèles annuels.

Durée de l'intégration numérique : 343.5 s sur
NVIDIA GeForce GTX 1660 Ti. Réseaux réutilisés : 78 ;
nouveaux entraînements : 12.
Les temps des checkpoints historiques sont des coûts attribués, pas des temps
à additionner une deuxième fois à l'exécution actuelle. Les réseaux D3/D4/H1
partagent D1/D2 et H0 partage ses composants. Les coûts par run, la GEV et les
normalisations H1 sont exportés séparément.

Le mode rapide recharge ces états et recalcule la description, les tirages,
les métriques de la sélection et les figures essentielles. Le mode réentraînement
reconstruit les familles et validations dans un autre dossier. Son résultat ne
remplace pas les résultats remis ; des versions ou matériels différents peuvent
modifier un arrêt précoce et de très faibles écarts de sélection.

## Contrôle supplémentaire après réajustement complet

Le réentraînement intégral confirme exactement les résultats de référence
(90 réseaux, poids identiques). Les tirages des 75 années ont aussi été
contrôlés après l'ajustement 1940–2025. La GEV sous SSP5-8.5 produit **un
tirage à 50,901 °C**, parmi 750 000 tirages annuels de cette méthode et de ce
scénario, donc au-delà du garde-fou de 50 °C. Il est conservé et comptabilisé.
Le contrôle historique de la GEV ajustée sur 1940–2000 était admissible : il
ne garantissait pas la conformité du modèle réajusté sur une autre période.
Une forme négative donne une borne mathématique par composante, pas une borne
physique assurée à 50 °C. Les tirages D3/D1 retenus restent dans les bornes sur
les six ensembles complets vérifiés ; cela ne prouve pas que toute leur loi
est bornée. Le tableau détaillé est `controle_projections_completes.csv`.
