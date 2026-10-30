# Vérification du rendu avec la section diffusion

Vérification du 30 octobre 2026. Base de travail : branche `final`, commit
`2f6cc7147dbc6e2f16c7814b398e4eb35d6cddd0`. Le notebook à remettre est
`rendu_final_concis/rendu_final_groupe.ipynb`.

## Exécution

Commande :

```powershell
python -X utf8 rendu_final_concis/executer.py --dossier tmp/verification_homogeneite_20261030
```

- Noyau neuf, dossier sans données locales : les trois CSV sont téléchargés et vérifiés.
- PyTorch 2.5.1+cu121 ; GPU NVIDIA GeForce GTX 1660 Ti.
- 16 cellules de code exécutées sur 16 ; aucune sortie d'erreur.
- Durée totale : 220,2 s, chargement des données et production des figures compris.
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
restantes sont identiques. Les comparaisons sont consignées dans `homogeneite.json`.
