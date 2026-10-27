# Audit des quatre contributions disponibles

Audit du 27 octobre 2026, à partir des branches distantes, du sujet original
(9 diapositives), du starter (32 cellules), du GUIDE (3 pages), du contexte,
de LISEZMOI, de `kit.py` et de `exemple.py`. Le sujet demande un notebook unique,
les deux parties et quatre critères : code, unités, équations, interprétation.
Le benchmark et sa coupure en 2000 sont des choix du groupe.

## Provenance et attribution

| Personne | Branche et SHA audités | Contribution propre |
|---|---|---|
| Elias | Elias, `833e5ff81148ad68df7e0efa9388e59ccb6b617f` | Pipeline, références OLS/GEV résiduelle/empirique, C0, DDPM, débruiteur D1, pondération D2, bootstrap D3/D4, validation et diagnostic d'échec |
| Christian | Christian, `ce8796243eeace8c3c8e2206610306b454b2c5fd` | `notebooks/methode_bayes_contrainte.ipynb`, posterior normal à pente positive et variante sans pente |
| Reda | Reda, `22c3821e96b3a9f5684a0605e09c05c3ac0c3eab` | Analyse descriptive, GEV non stationnaire estimée en PyTorch, bootstrap, traitement distinct des minima et explication LaTeX/PDF |
| Yazid | Yazid, `216c1a1aeb80e29c0f7b6dc395432fb07dffaf5e` | Analyse descriptive, transformations, régressions quantiles linéaires en CO₂ |

L'auteur Git du commit Christian est Elias Hasnaou ; l'attribution scientifique
à Christian vient de la branche, du fichier et de la mission confirmée par
l'utilisateur. Les commits Reda et Yazid portent leurs identifiants respectifs.
Le cinquième membre n'a pas remis de contribution à cette date. Aucun modèle ni
travail de relecture ne lui est attribué. Les noms complets ne sont pas inventés.
Les fichiers hérités d'Elias dans les autres branches ne sont pas comptés deux
fois. Les notebooks originaux sont archivés sous `rendu_final/sources`, avec
leurs sorties ; ils ne sont pas le notebook destiné à la remise.

## Elias

Cibles : maxima et minima annuels en °C. Train 1940–2000, validations
chronologiques F1/F2/F3, test 2001–2025, puis réajustement 1940–2025 distinct.
L'ancre est OLS en logarithme du CO₂, pente négative écrêtée à zéro et intercept
recalculé. L'échelle des résidus, les seuils et les bootstraps utilisent le train.
C0 apprend directement une loi résiduelle ; D1 apprend des tâches de débruitage
distributionnel avec corruption linéaire et latent indépendant ; D2 ajoute le
score de queue, D3/D4 une incertitude bootstrap sur l'ancre.

Trois réseaux de 1 217 paramètres par objectif. AdamW 0,001, poids 0,0001,
batch 64, ensembles de 32, almost fair CRPS α=0,95. Les trois lois sont mélangées,
et le CRPS du mélange est calculé. Arrêt sur validation, puis nombre de pas final
fixé par médiane historique. L'usage des mêmes folds pour arrêter et comparer
limite l'indépendance de la validation et est indiqué dans le protocole.

La sélection historique utilisait un filtre de simplicité à 0,05 °C ; ce n'est
pas une exigence du professeur. Elle reste archivée, avec son candidat C0/D1,
ses scores et le manifeste. L'intégration adopte le minimum de CRPS non arrondi.

**Échec conservé** : le DDPM classique produit des minima jusqu'à −1 933,216 °C,
19 152 valeurs hors bornes, CRPS Tmin 2,619998 °C. Il est éliminé par le kit.
D1 ne comporte pas la chaîne inverse DDPM et ne doit pas être présenté comme
le même modèle. Le diagnostic, les graines et les sorties défavorables restent
dans l'historique. Les anciens notebooks dépendaient d'artefacts ignorés par Git ;
le notebook commun embarque réellement ses petites dépendances.

## Christian

Cibles : maxima/minima annuels. Régression normale en log(CO₂), prior
`p(a,b,sigma²) ∝ 1/sigma² 1(b≥0)`. Tirage conjoint normal–inverse-χ², puis rejet
des pentes négatives. Ce posterior tronqué ne coïncide pas avec un bootstrap
dont les pentes sont écrêtées. La prédiction ajoute les fluctuations annuelles,
pas seulement l'incertitude de la moyenne. Coût essentiellement analytique.

Corrections apportées :

- Sous contrainte, la marginale de sigma² est repondérée par
  `P(b≥0 | sigma²,y)` ; l'inverse-χ² non contrainte seule n'est plus sa marginale.
- La formule de variance sans contrainte ne prouve pas la largeur après rejet.
  Les largeurs sont mesurées pour chaque export.
- Les validations chevauchantes jusqu'en 2000 sont remplacées par F1/F2/F3.
  La sélection utilise les scores non arrondis.
- La reconstruction emploie vraiment la famille choisie : la référence ne
  devient pas silencieusement un Bayes sans pente.

Le notebook annonce 1,58 °C pour Tmax et 1,06 °C pour Tmin. Ces valeurs sont
étiquetées historiques ; les scores de l'intégration viennent des nouveaux
exports. Pour les trajectoires, les paramètres sont partagés mais les bruits
annuels sont renouvelés, contrairement aux aléas communs du graphique marginal.

## Reda

Cible maxima : `GEV(mu(C),sigma,xi)` avec mu affine en log(CO₂/280), sigma
constant, pente positive, xi dans [−0,5;−0,01]. Estimation jointe de quatre
paramètres par Adam, 500 réplications de paires et 3 000 pas. Cette méthode
diffère de la GEV ajustée après l'ancre OLS d'Elias. Le score annoncé 1,66 °C
provient bien d'un ajustement 1940–2000 et d'une évaluation 2001–2025 ; il doit
être distingué de la reproduction adaptée au protocole commun.

Le code original remplace z=1+xi(T−mu)/sigma négatif par 10⁻⁶ dans la
vraisemblance. Cela peut attribuer une densité à une observation hors support.
L'intégration conserve la famille, mais centre log(CO₂) sur le train et refuse
les mises à jour qui sortent du support. Le nombre de refus et le support minimal
sont enregistrés. Une forme négative est un choix, pas une conséquence générale
du théorème des extrêmes ni une preuve de borne physique exacte.

Pour Tmin, bootstrap de paires OLS à pente libre et résidus propres à chaque
réplication. La pente libre peut échouer au contrôle de monotonie : cet échec
est conservé au lieu de transformer la méthode pour gagner le benchmark.

Partie 1 : la suppression du 29 février pouvait joindre deux dates séparées.
Le cycle de référence conserve 365 jours, mais le seuil du 29 février est
interpolé et les événements suivent la chronologie réelle. Les fréquences par
décennie sont rapportées par année, car 2020–2025 ne contient que six ans.
L'intensité est l'anomalie à la médiane saisonnière ; l'excès au seuil q90 est
aussi exporté. Le seuil relatif détecte des épisodes doux en hiver.

## Yazid

Cible effectivement modélisée : Tmax annuel, régression quantile sur CO₂ brut.
Le code ajuste les quantiles sur 1940–2025, puis évalue 2001–2025 : ce score est
**dans l'échantillon**. Il n'est pas comparé comme score hors échantillon.
Les graphiques q10/q50/q90 avaient α=0 et les 99 quantiles α=1 ; le mélange des
réglages empêchait d'interpréter graphiques et score comme une seule méthode.

L'adaptation ajuste exclusivement le train de chaque fold, centre/réduit le CO₂
avec ce train, choisit α sur validation et conserve la configuration partout.
Elle génère une loi par inversion de quantiles monotones interpolés, avec
prolongements linéaires explicites de 0 à 1 % et de 99 à 100 %. Les queues sont
donc bornées : le risque de 40 °C reste très sensible à ce choix. Le tri garantit
l'ordre, pas une couverture de 80 %. La couverture réelle est mesurée.

La partie 1 fondée sur `dayofyear<=365` désalignait les jours après février des
années bissextiles et supprimait leur 31 décembre. Le calcul commun utilise le
mois/jour. La partie minima était vide dans le notebook d'origine ; son
application aux minima dans l'intégration est signalée comme extension.

## Vérifiabilité

L'inventaire CSV inclut les branches, SHA, fichiers et auteurs Git. Les données
livrées sont celles du professeur et du kit, sans observation externe. Les
modèles ne reçoivent que le CO₂ pour le futur. Les métriques exécutées, temps,
contrôles et distinctions entre résultats annoncés et reproduits sont dans
`rendu_final/resultats` et `reports/experiences_complementaires.md`.
