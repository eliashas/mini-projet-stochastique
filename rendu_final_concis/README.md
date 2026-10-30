# Rendu final du groupe (version concise)

Le fichier à rendre est **`rendu_final_groupe.ipynb`**, déjà exécuté.

- **Ouvrir dans Colab** : importer le fichier `rendu_final_groupe.ipynb` depuis l'ordinateur.
- **Relancer** : choisir un GPU dans *Exécution > Modifier le type d'exécution*, puis *Tout exécuter*.
  Le notebook entraîne réellement les réseaux ; prévoir quelques minutes. Il fonctionne aussi sur CPU.
  Les trois CSV sont intégrés dans une archive compressée à l'intérieur du notebook.
  Aucun téléchargement de données et aucun autre fichier ne sont nécessaires.
- **Travailler à plusieurs** : enregistrer une seule copie dans Drive et la partager avec les membres comme éditeurs.
  Garder une seule copie commune pour la relecture et le rendu.

Pour modifier le notebook : changer le code dans `build.py` ou les commentaires dans `commentaires.py`, puis
`python rendu_final_concis/build.py` depuis la racine du dépôt, puis
`python rendu_final_concis/executer.py`. Le constructeur remplace le notebook : intégrer les modifications des
cellules dans les sources avant de le relancer. Les chiffres cités dans les commentaires doivent correspondre aux sorties.

Pour vérifier son autonomie dans un dossier vide :

```powershell
python rendu_final_concis/executer.py --dossier tmp/verification_autonome --sans-reseau
```

La cellule d'initialisation contient les données et s'affiche repliée. Elle les décompresse en mémoire et vérifie
leurs empreintes avant lecture. Les bibliothèques Python, dont PyTorch, doivent être installées ; elles sont
habituellement présentes dans Colab. L'exécution ne fait aucun appel réseau pour récupérer des données ou du code.

Les sections Bayes et diffusion suivent la même structure : explication mathématique, deux cellules de code,
puis commentaire. Leurs textes explicatifs ont une longueur voisine. Les équations et le code de Bayes sont conservés.
La section diffusion garde les variantes D1–D4, le CRPS et le twCRPS, la couverture des intervalles et une courbe
d'apprentissage. Les validations et les essais C0/DDPM sont résumés ; leurs résultats complets restent dans la
version détaillée. D1/D2 sont réentraînés pour trois graines ; D3/D4 utilisent ces réseaux avec le bootstrap de l'ancre.
La sélection enregistrée sur validation est D3 pour Tmax, D1 pour Tmin. Bayes obtient le meilleur CRPS global
observé sur le test parmi les méthodes principales comparées. Le test a déjà été consulté : la comparaison est rétrospective.

Le tableau commun reprend les résultats de `rendu_final/resultats/validation.csv` et `test.csv`.
Le tableau détaillé de la diffusion est recalculé à l'exécution. Les résultats archivés et recalculés sont distingués.
Les tirages ne sont pas coupés pour les faire entrer dans un intervalle physique.

| Fichier | Rôle |
|---|---|
| `rendu_final_groupe.ipynb` | Le notebook à rendre |
| `build.py`, `commentaires.py` | Construisent le notebook à partir de celui du prof (`sujet_prof.ipynb`) |
| `diffusion.py` | Sources des cellules de diffusion, copiées dans le notebook lors de sa construction |
| `executer.py` | Exécute le notebook, conserve ses sorties et extrait les figures pour vérification |
| `*.csv` | Les données du prof |

Le notebook s'exécute seul dans Colab : il n'importe pas les scripts du dépôt.
