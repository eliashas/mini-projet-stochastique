# Vérification du rendu avec la section diffusion

Vérification du 30 octobre 2026. Base de travail : branche `final`, commit
`a58bce9465964dc6c7d5aed1b9d0834f75572eff`. Le notebook à remettre est
`rendu_final_concis/rendu_final_groupe.ipynb`.

## Exécution

Commande :

```powershell
python -X utf8 rendu_final_concis/executer.py --dossier tmp/verification_csv_locaux_20261030 --sans-reseau
```

- Noyau neuf, dossier isolé contenant seulement les trois CSV : lecture directe avec Pandas, sans téléchargement.
- PyTorch 2.5.1+cu121 ; GPU NVIDIA GeForce GTX 1660 Ti.
- 16 cellules de code exécutées sur 16 ; aucune sortie d'erreur.
- Durée totale : 199,3 s, lecture des données et production des figures comprises.
- 19 réseaux réellement entraînés : un pour la courbe diagnostique, douze pour D1/D2
  sur 1940–2000 (deux variables, deux objectifs, trois graines), six réajustés sur 1940–2025.
- Les 10 figures sont extraites à côté de ce rapport. Les cinq figures d'apprentissage,
  de projections et de distributions comparées ont été relues visuellement.

Un appel Pandas à `Series.corr` avec un tableau NumPy a été corrigé après une première
exécution interrompue dans la cellule Tmin. La vérification ci-dessus est une nouvelle
exécution complète, après correction. Cette version homogénéisée a été réexécutée intégralement. Le texte, le code et les résultats
de Bayes ont ensuite été comparés à la base de travail et sont identiques.

L'empreinte du notebook, celle de son code et les sorties texte sont dans `execution.json`.

## Contrôles ciblés

```powershell
python -X utf8 -m unittest discover -s tests -p test_diffusion_concis.py -v
```

Quatre tests réussis :

1. estimateur almost fair CRPS comparé à la somme brute des distances par paires,
   avec vérification de gradients finis ;
2. ancre, normalisation et seuil calculés sur les seules données entraînées, et
   entraînement court sur CPU ;
3. une seule ancre par trajectoire, et reproductibilité des tirages à graine fixée ;
4. correspondance des tableaux de référence de l’utilitaire avec les CSV archivés.

## Résultats de cette réexécution

Les résultats archivés et ceux de la réexécution sont explicitement séparés dans le notebook.
Les graines du bootstrap et des prévisions de cette version diffèrent de celles de la grande matrice.
Les scores ne servent pas à changer les réglages après consultation du test.

| Variable | Modèle | CRPS test (°C) | twCRPS test (°C) | Couverture 90 % |
|:--|:--|--:|--:|--:|
| Tmax | D1 | 1,701 | 0,696 | 84 % |
| Tmax | D2 | 1,707 | 0,700 | 80 % |
| Tmax | D3 | 1,646 | 0,684 | 88 % |
| Tmax | D4 | 1,652 | 0,687 | 88 % |
| Tmax | Bayes | 1,574 | 0,692 | 80 % |
| Tmin | D1 | 1,042 | 0,167 | 96 % |
| Tmin | D2 | 1,025 | 0,163 | 96 % |
| Tmin | D3 | 0,992 | 0,154 | 100 % |
| Tmin | D4 | 0,983 | 0,151 | 100 % |
| Tmin | Bayes | 0,972 | 0,138 | 96 % |

Sous SSP5-8.5, D3 donne une médiane Tmax en 2100 de 32,55 °C, 261 dépassements
de 40 °C parmi 10 000 tirages (2,61 %) et un risque cumulé simulé de 17,22 %.
Bayes donne 32,82 °C, 153 dépassements (1,53 %) et 8,14 % sur 2026–2100.
Le partage des paramètres entre années et les innovations annuelles conditionnellement
indépendantes sont précisés dans le notebook. Ces probabilités ne sont pas validées
par les 25 observations de test.

Pour Tmin sous SSP5-8.5, le risque de gel en 2100 est de 17,78 % avec D1 et
17,14 % avec Bayes. Le notebook souligne que D1 n'inclut pas l'incertitude de l'ancre.

Les projections brutes vérifiées ne contiennent aucune valeur non finie ou hors des
plages de contrôle du groupe : [0, 50] °C pour Tmax et [−30, 20] °C pour Tmin.
Aucun écrêtage des températures n'est effectué. Ces contrôles numériques ne constituent
pas une validation physique des distributions extrapolées.

## Portée

La validation chronologique et les essais C0/DDPM proviennent des expériences précédentes
du dépôt. Ce notebook ne réexécute pas toute la matrice de validation. Il inclut le code
de l'entraînement et réentraîne les variantes présentées avec les réglages déjà retenus.
La version détaillée et ses expériences complètes restent accessibles dans
`notebooks/rendu_final_equipe.ipynb`.


## Version homogénéisée

La diffusion a été ramenée de 1437 à 606 mots/éléments (équations comprises),
contre 650 pour Bayes. Les deux sections suivent la même structure. Le tableau
archivé détaillé et son graphique ont été retirés de cette version courte ; le tableau commun
et le tableau recalculé sont conservés. Les contenus hors diffusion, les résultats de Bayes
et les tableaux de projections sont identiques à la version précédente. Les dix figures
restantes sont identiques. Les comparaisons de cette révision sont consignées dans `homogeneite.json` (version antérieure à l’intégration des données).


## Données intégrées et autonomie

Les trois CSV fournis avec le sujet sont empaquetés dans une archive ZIP compressée
intégrée à la cellule d’initialisation repliée. Ils sont décompressés en mémoire et
leurs empreintes sont vérifiées avant lecture. Il n’y a plus de chemin vers le dépôt,
de chargement local conditionnel ou de téléchargement de données. Les bibliothèques
Python restent nécessaires. Les références scientifiques sont conservées.

Le noyau a été exécuté dans un dossier sans CSV, avec résolution DNS et connexions
Python externes bloquées (boucle locale autorisée pour Jupyter). La protection était
active et aucun appel externe n’a été tenté. Le fonctionnement du garde a également
été vérifié séparément par interception d’un nom de domaine de test avant résolution.
Les cellules hors initialisation, les résultats de Bayes, les tableaux de projections
et les dix figures sont identiques à la version précédente. Preuves : `autonomie.json`.


## Simplification proposée par Christian

La cellule du débruiteur passe de 125 à 108 lignes. Les contrôles de l’échelle,
de la perte, des gradients et des tirages non finis sont conservés, ainsi que
l’affichage du GPU et le mode évaluation du réseau. Le chronométrage par réseau
et les historiques inutilisés sans validation sont retirés.

Huit comparaisons sur CPU et CUDA (Tmax/Tmin, poids des extrêmes 0/0,5)
retrouvent exactement les mêmes poids appris, résidus générés et trajectoires
avec ou sans bootstrap, sans tolérance numérique. Les courbes de validation
sont également identiques dans les cas testés. Les pertes et tirages NaN
sont interceptés et une échelle nulle est protégée. Les quatre tests ciblés
sont réussis.

La nouvelle exécution complète conserve les tableaux de scores, les projections
et les dix figures à l’identique. La partie Bayes et toutes les cellules hors
modèle sont inchangées. Les données restent intégrées, sans appel réseau externe.
Preuve détaillée : `equivalence_christian.json`. Les preuves antérieures restent
archivées avec l’empreinte du notebook auquel elles se rapportent.


## Version finale avec CSV à côté du notebook

Le bloc encodé de la cellule d’initialisation a été retiré. Les trois fichiers
sont lus directement avec `pd.read_csv` dans le dossier de travail. Les tables
obtenues (valeurs et types) sont strictement identiques à celles de l’ancienne
archive intégrée. Les deux parties méthodologiques, les résultats, les tableaux
et les dix figures sont inchangés. Une exécution complète avec les trois CSV
copiés dans un dossier isolé et les connexions externes bloquées a réussi,
sans aucun appel réseau.

Le script `rendu_final_concis/preparer_rendu.py` crée le livrable à transmettre :
`tmp/livrable_sma/rendu_final_groupe.zip`, contenant exactement le notebook
exécuté et les trois CSV. Il faut décompresser les quatre fichiers dans le même
dossier ; dans Colab, les CSV doivent être déposés dans l’onglet Fichiers.
Le notebook seul ne contient donc plus les données. Le ZIP final a été vérifié
par CRC et comparaison exacte des quatre fichiers. Preuve : `csv_locaux.json`.
Les sections et preuves précédentes décrivent l’historique des versions.


## Conclusion et couverture Bayes

Trois cellules de texte ont été retouchées : conclusion chiffrée, retrait de la
phrase sur le test déjà consulté et commentaire de la couverture à 90 % de Bayes
pour Tmax (20 années sur 25). Le code, les sorties exécutées, les figures et les
formules bayésiennes sont strictement inchangés. Les chiffres sont arrondis à
partir des sorties existantes ; aucun entraînement supplémentaire n’a été lancé.
Le ZIP a été régénéré et ses quatre fichiers vérifiés. Preuve :
`edition_conclusion.json`.
