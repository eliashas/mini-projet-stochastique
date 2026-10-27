# Protocole de l'intégration commune

Cette étude complète les travaux disponibles le 27 octobre 2026. **Le test
2001–2025 a déjà été consulté.** Les nouvelles comparaisons sont exploratoires :
leur sélection sur validation ne recrée pas un test indépendant. Les sorties
historiques d'Elias et les notebooks individuels sont conservés sans modification.

## Trois phases séparées

| Phase | Ajustement | Évaluation et rôle |
|---|---|---|
| F1 | 1940–1970 | 1971–1980 |
| F2 | 1940–1980 | 1981–1990 |
| F3 | 1940–1990 | 1991–2000 |
| Historique | 1940–2000 | 2001–2025, complément exploratoire |
| Projection | 1940–2025 | 2026–2100, sans vérité future |

Chaque ajustement reçoit seulement les CO₂ et les températures de son train.
Les données journalières complètes ne servent qu'à la description des vagues de
chaleur. Maxima et minima annuels proviennent de leur fichier propre : ce ne
sont pas les extrêmes des moyennes journalières.

Les normalisations du CO₂, les résidus, les seuils q80/q20, les moments servant à
H1 et les réplications bootstrap sont tous estimés par train. Les réseaux
historiques sont réutilisés seulement après comparaison des empreintes des
cibles, résidus, ancres et données de validation. Les fichiers historiques ne
sont jamais réécrits. Les états portables contiennent uniquement les poids NPZ.

## Modèles et sélection

- Elias : C0, D1, D2 (λ=0,5), D3 et D4 ; trois réseaux de 1 217 paramètres.
  D3/D4 réutilisent D1/D2, avec bootstrap de l'ancre par blocs de trois ans.
- Christian : prédiction bayésienne normale avec rejet conjoint de la pente
  négative, et variante sans pente. La référence est réellement reconstruite si
  elle gagne. Le rejet conserve la dépendance entre pente, intercept et variance.
- Reda : GEV non stationnaire pour les maxima, 500 réplications, 3 000 pas Adam.
  Les mises à jour sortant du support sont refusées. La contrainte ξ<0 est une
  hypothèse de cette méthode. Pour les minima, conserver son bootstrap de paires
  à pente libre afin d'en voir aussi les limites.
- Yazid : 99 régressions quantiles sur le CO₂ brut centré/réduit sur le train.
  α∈{0;0,01;0,1;1}, réarrangement monotone et interpolation en probabilité.
  Prolongement linéaire des segments extrêmes jusqu'à p=0 et p=1 : queues
  bornées explicites, sans hypothèse gaussienne cachée ni assimilation des 99
  quantiles à des observations indépendantes. Même α pour graphiques et scores.
- Ancre : comparer logarithme et CO₂ linéaire avec le même bruit gaussien.
  Cette ablation isole la forme de tendance ; les autres comparaisons concernent
  des méthodes complètes. Ne pas multiplier les variantes de pondération
  temporelle ou de variance sans diagnostic le justifiant.
- H0 : composante D1 ou D3 choisie sur validation, puis poids bayésien constant
  dans {0;0,25;0,5;0,75;1}. Échantillonnage stratifié du mélange des distributions
  complètes. Les extrémités restituent exactement leurs composants.
- H1 : paramètres conjoints de Bayes et résidus D1 recentrés/réduits avec 100 000
  simulations fixées par train. Aucun deuxième bruit annuel ni ancre bootstrap
  n'est ajouté. C'est une combinaison modulaire approximative, car le posterior
  de départ reste calculé sous vraisemblance normale.

La décision utilise le **CRPS global de validation non arrondi**, avec le score
du mélange effectif des trois graines. Il n'y a pas de filtre de simplicité à
0,05 °C. Le choix d'α et de H0 se fait sur ces mêmes validations : les scores
gagnants sont donc optimistes et ne constituent pas une validation imbriquée.
Les checkpoints neuronaux ont aussi été arrêtés sur ces validations.

Après sélection, les trois contrôles du kit sont mesurés sur les prédictions
1940–2000, sans températures de test : monotonie des médianes à 0,1 °C près,
ratio de largeur 80 % ≥0,95, tous les tirages dans [0;50] °C pour Tmax et
[−30;20] °C pour Tmin. Un échec conduit au candidat suivant du classement de
validation. Aucun clipping, changement de graine ou réglage sur test.

Le benchmark historique départageait deux équipes à moins de 0,05 °C sur Tmax
par le CRPS Tmin. Ici, les modèles peuvent être différents pour Tmax et Tmin,
comme le permet le sujet. Les classements des deux variables restent visibles.

## Mesures

10 000 tirages par année ; CRPS empirique M², identique à `kit.crps`, float64.
Le twCRPS haut est le CRPS de max(X,s) et max(y,s), s=q80 du train.
Le twCRPS froid remplace max par min, s=q20 du train. Toutes les années
participent, fausses alertes comprises. Le twCRPS répond à une autre question
que le CRPS global et ne le remplace pas. λ=0,5 dans D2/D4 est un poids
d'apprentissage ; w dans H0 est un poids de mélange ; aucun n'est le seuil s.

Couvertures et largeurs des intervalles 80/90 %, biais, PIT, Brier, nombres
d'événements, coûts et contrôles sont exportés. Les intervalles de différence
de CRPS utilisent un bootstrap apparié par blocs de trois années et ne sont
pas des garanties de généralisation. Les intervalles de probabilités simulées
mesurent l'erreur Monte-Carlo conditionnelle au modèle, pas son erreur climatique.

Les trajectoires gardent les paramètres communs à une réalisation et renouvellent
les innovations annuelles conditionnellement à ces paramètres. Pour H0, la
composante est commune à la trajectoire. Cette convention est explicitée pour
P(au moins un dépassement). Les maxima et minima sont des marges séparées :
aucune loi jointe quotidienne ou contrainte de trajectoire max/min n'est apprise.
