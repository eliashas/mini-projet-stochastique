# Rendu commun SMA

Le fichier à remettre est **`notebooks/rendu_final_equipe.ipynb`**. Il couvre
les deux parties du sujet et contient ses données, ses petits modèles et ses
résultats de référence. Il peut être téléchargé seul puis ouvert dans Colab,
sans accès au dépôt ni chemin personnel. Un seul notebook maître doit être
partagé pour la relecture du groupe ; les noyaux Colab restent individuels.

[Ouvrir le notebook dans Colab](https://colab.research.google.com/github/eliashas/mini-projet-stochastique/blob/final/notebooks/rendu_final_equipe.ipynb).
Le téléchargement du fichier puis son ouverture manuelle dans Colab fonctionne
également : l'exécution ne télécharge aucune ressource du dépôt.

## Mode rapide

Dans Colab ou Jupyter, laisser `MODE="rapide"`, puis redémarrer le noyau et
exécuter toutes les cellules. Les dépendances absentes sont installées
explicitement. L'archive embarquée est vérifiée par SHA-256, décompressée dans
un dossier temporaire neuf, puis les calculs essentiels sont exécutés.
Les tableaux de la grande matrice sont rechargés ; les vagues, les prévisions
de la sélection, le benchmark original et les projections sont recalculés.
Un petit entraînement pédagogique de 250 pas est aussi exécuté.

Vérification mesurée : environnement virtuel Python 3.12.10 neuf, PyTorch
2.5.1 CPU, seul notebook copié dans un dossier vide, sorties effacées avant
exécution ; 23 cellules de code terminées sans erreur en **21 à 30 s** lors des
deux vérifications, selon la charge de la machine.
Les preuves détaillées sont sous `reports/final/execution_notebook_propre.json`.
L'installation initiale des bibliothèques n'est pas incluse dans ce temps.

## Mode réentraînement

Choisir `MODE="reentrainement"`, puis exécuter toutes les cellules. Dans Colab,
activer un GPU. Cette option reconstruit les familles statistiques, les réseaux,
les trois validations, le test exploratoire et les projections dans un dossier
distinct ; elle ne remplace pas les résultats remis. Le calcul est plus long
que le mode rapide. Les nombres peuvent légèrement varier selon le matériel,
les versions et les arrêts précoces. Le code et les graines sont fournis.

Depuis un clone, Python 3.12 et un PyTorch adapté au matériel :

```bash
python -m pip install -r requirements-final.txt
python scripts/run_final_team.py --retrain --output rendu_reentraine
python -m pytest -q
```

Pour refaire l'exécution propre du notebook, lancer avec l'interpréteur voulu :

```bash
python scripts/execute_final_notebook.py --notebook notebooks/rendu_final_equipe.ipynb --output notebook_verifie.ipynb --proof verification.json
```

Sans `--retrain`, le script d'expériences réutilise les états présents après
vérification de leurs données. Pendant l'intégration, 78 checkpoints compatibles
ont été réutilisés et 12 réseaux complémentaires ont été entraînés. La matrice
complétée, les nouveaux ajustements et les projections ont pris **343,5 s**
sur GTX 1660 Ti. Le temps historique des réseaux réutilisés est distingué du
coût supplémentaire. La GEV utilise 500 réplications et 3 000 pas.

## Résultats et limites

Le choix sur validation est **D3 pour Tmax et D1 pour Tmin**. Le kit original
est admissible : **CRPS test 1,649991 / 1,036056 °C**. Bayes obtient un meilleur
CRPS Tmax observé sur ce test (1,580191 °C), sans remplacer le choix de validation.
Le meilleur mélange H0 conserve un poids bayésien nul. H1 n'améliore pas les
meilleurs modèles de validation. Le DDPM historique et les méthodes éliminées
restent documentés.

**Le test 2001–2025 avait déjà été consulté** : les compléments sont exploratoires.
Les projections sont réajustées sur 1940–2025. Sous SSP5-8.5, D3 donne environ
32,55 °C de médiane Tmax en 2100 et 3,01 % de probabilité annuelle de dépasser
40 °C. La probabilité d'au moins un dépassement entre 2026 et 2100 vaut 17,26 %
sous l'hypothèse temporelle explicitée dans le notebook. Ce sont des résultats
conditionnels au modèle, pas des probabilités climatiques validées pour Brest.
Les autres méthodes donnent des valeurs différentes ; cette sensibilité est
présentée, ainsi que l'incertitude Monte-Carlo et la sous-couverture historique.

## Où retrouver les éléments

- `reports/audit_contributions.md` et `reports/inventaire_contributions.csv` :
  attribution, branches, SHA, sources propres et corrections.
- `reports/protocole_commun.md` : données, validations, métriques et sélection.
- `reports/experiences_complementaires.md` : essais terminés, scores et limites.
- `reports/matrice_conformite.md` et `.csv` : chaque question du starter et les
  quatre critères du professeur, avec les identifiants des cellules concernées.
- `rendu_final/resultats/` : tableaux CSV/JSON, incertitudes, contrôles et coûts.
- `reports/final/` : figures PNG/SVG et preuves d'exécution.
- `rendu_final/modeles/` : paramètres et poids NPZ sans pickle.
- `rendu_final/data/` : données réellement livrées, sans observation extérieure.
- `rendu_final/provenance_donnees.json` : empreintes et vérification des découpages.
- `rendu_final/sources/` et `rendu_final/historique/` : sources originales et
  résultats antérieurs conservés ; ils ne constituent pas un second rendu.
- `rendu_final/ressources_notebook.zip` : copie inspectable de l'archive embarquée.

Les branches individuelles ne sont pas modifiées. Le cinquième membre n'avait
pas de contribution au moment de l'intégration ; aucun apport n'est inventé.
Après relecture humaine du notebook maître, l'éditer directement. Le script de
construction refuse de le remplacer sans `--overwrite` et ne doit pas servir
à écraser les corrections de l'équipe.
