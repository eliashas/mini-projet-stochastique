# Diagnostic de l'échec DDPM — prédictions verrouillées

Le DDPM est éliminé par les bornes des minima. Le benchmark original conserve
un CRPS de **2,619998 °C pour les minima** et 1,750060 °C pour les maxima,
mais retourne `None` car le modèle n'est pas admissible. Son CRPS moyen de
validation des minima était 1,143005 °C. Cet écart concerne des réseaux
réentraînés, des périodes et des procédures de sélection de checkpoints
différents ; le score de validation ne garantit pas la stabilité du refit.

Ce diagnostic lit seulement le NPZ, les métadonnées, les historiques et les
checkpoints figés. Aucune nouvelle simulation, évaluation du réseau,
modification, correction, sélection de graine ou réestimation n'a été faite.
Les empreintes SHA-256 du NPZ et des six checkpoints concordent avec le
manifeste verrouillé. Les nombres exacts figurent dans
`artifacts/competition/ddpm_failure_diagnostic.json`.

## La composante seed 2 porte toutes les valeurs hors bornes

Les colonnes de chaque ligne sont concaténées dans l'ordre seed 0, seed 1,
seed 2, avec 3 334 / 3 333 / 3 333 membres. La lecture de ces tranches dans le
NPZ donne, pour les minima :

| Composante | Membres par ligne | Moyenne (°C) | Médiane (°C) | q01 (°C) | q10 (°C) | Minimum (°C) | Sous −30 °C par ligne |
|---|---:|---:|---:|---:|---:|---:|---:|
| Seed 0 | 3 334 | −1,177 | −0,717 | −7,906 | −4,217 | −13,143 | 0 |
| Seed 1 | 3 333 | −1,209 | −0,824 | −6,379 | −4,290 | −8,278 | 0 |
| Seed 2 | 3 333 | −109,345 | −1,332 | −1 336,009 | −455,050 | −1 933,216 | 684 |
| Mélange | 10 000 | −37,240 | −0,932 | −964,759 | −5,819 | −1 933,216 | 684 |

La seed 2 a un écart-type de 276,058 °C, contre 2,169 et 2,050 °C pour les
deux autres composantes. Ses 684 valeurs inadmissibles représentent **20,522 %
de sa composante**, et **6,84 % du mélange**. Aucune valeur ne dépasse 20 °C.

Les minima ont une ancre constante : a=−0,961620 °C, b=0, sigma=1,983422 °C,
après contrainte de la pente brute −1,375579. Les mêmes résidus ont été
réutilisés pour les 25 années et les trois scénarios. Ainsi les 28 lignes
sont identiques et les 19 152 valeurs hors bornes sont **684 valeurs répétées
28 fois**, et non 19 152 fluctuations indépendantes. Le problème vient du
générateur de résidus ; une extrapolation de la tendance en CO₂ ne peut pas
expliquer cet échec puisque b=0.

Le mélange garde une médiane presque ordinaire, alors que sa moyenne et sa
queue froide sont absurdes. Une inspection limitée à la médiane ou à
l'intervalle 10–90 % aurait été insuffisante. Les maxima des trois composantes
respectent les bornes du kit ; leur minimum global vaut 20,476 °C et leur
maximum global 33,381 °C sur test et projections.

## Les historiques finaux révélaient déjà l'instabilité

Les trois réseaux des minima ont été réentraînés pendant 1 250 étapes fixées,
sans utiliser les températures de test. La règle enregistrée prend la médiane
des neuf meilleurs nombres d'étapes de validation. Pour la seed 2, les
checkpoints retenus des folds se situaient à 2 750, 2 000 et 4 250 étapes.
La durée commune 1 250 est donc plus courte que les trois durées retenues
pour cette seed. Cela suggère une sensibilité au budget de réentraînement,
sans prouver qu'un entraînement prolongé aurait corrigé la queue : les
données et l'ancre des folds diffèrent aussi du refit sur 61 années.

Le dernier contrôle de 4 096 résidus enregistré pendant le refit affichait :

| Seed | MSE moyenne du dernier segment | Moyenne z | Écart-type z | q01 z | Médiane z | q99 z |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 0,469291 | −0,151 | 1,141 | −3,871 | 0,101 | 1,582 |
| 1 | 0,469280 | −0,124 | 1,021 | −2,707 | 0,021 | 1,671 |
| 2 | 0,475871 | −60,492 | 148,810 | −641,137 | −0,213 | 1,671 |

La MSE seed 2 est proche des deux autres alors que ses tirages sont déjà
pathologiques. L'anomalie apparaît dès 250 étapes de son historique final
et reste présente aux contrôles suivants. Elle existait avant le benchmark
et les contrôles des sorties l'ont conservée et éliminée honnêtement.

## Mécanisme plausible : extrapolation du débruiteur dans la chaîne inverse

Le calendrier et les tenseurs des checkpoints sont finis. K=100, calendrier
cosinus, beta terminal=0,999, alpha terminal≈0,001 et alpha-bar
terminal≈2,42857×10⁻⁷. L'échantillonnage ancestral divise donc son terme
déterministe au premier pas inverse par sqrt(alpha), soit un facteur proche
de 31,62. La stabilité dépend de la qualité de la compensation par le bruit
prédit. Une erreur du débruiteur peut envoyer une trajectoire vers des états
rarement vus pendant l'apprentissage, puis être amplifiée aux pas suivants.

Le petit MLP n'a pas de contrainte sur son comportement à l'infini. Ses poids
permettent de calculer algébriquement les pentes asymptotiques, sans le faire
tourner. Dans la queue négative, la seed 2 a une pente limite
epsilon_hat(z,t)/z≈−0,031462. Le facteur limite du premier pas inverse est
alors environ **32,62** : le réseau ne compense pas le terme z dans cette
limite. Les seeds 0 et 1 ont des pentes positives 0,472422 et 0,693732 ; leurs
facteurs limites sont 16,70 et 9,71.

Ces limites ne reconstituent pas les trajectoires effectivement simulées.
Les seeds 0 et 1 ont également des facteurs asymptotiques supérieurs à un,
tout en restant dans les bornes dans le NPZ. La région où l'approximation
asymptotique s'applique et la dynamique aux états finis comptent aussi. Le
diagnostic est donc cohérent avec une extrapolation instable du débruiteur,
mais ne démontre pas quel pas a créé chaque valeur extrême.

La MSE porte sur des corruptions de résidus historiques, ici compris entre
−2,845 et 1,592 avant corruption ; elle ne borne ni le réseau ni les états de
la chaîne inverse. Son faible niveau ne garantit pas la stabilité numérique
et distributive des queues générées. Les autres règles officielles de
monotonie et de largeur ont passé, ce qui montre pourquoi les contrôles de
bounds et les diagnostics de queue restent nécessaires.

Le modèle, ses trois graines, son mélange et les valeurs brutes restent
inchangés. Retirer la seed 2 ou borner les sorties après ouverture du test
changerait l'expérience préenregistrée. Le statut final est **éliminé**.
