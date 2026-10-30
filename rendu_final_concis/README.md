# Rendu final du groupe (version concise)

Le fichier à rendre est **`rendu_final_groupe.ipynb`**, déjà exécuté.

- **[Ouvrir dans Colab](https://colab.research.google.com/github/eliashas/mini-projet-stochastique/blob/final/rendu_final_concis/rendu_final_groupe.ipynb)**.
- **Relancer** : choisir un GPU dans *Exécution > Modifier le type d'exécution*, puis *Tout exécuter*.
  Le notebook entraîne réellement les réseaux ; prévoir quelques minutes. Il fonctionne aussi sur CPU.
  Les trois CSV sont lus localement ou téléchargés automatiquement depuis une version fixe du dépôt.
- **Travailler à plusieurs** : enregistrer une seule copie dans Drive et la partager avec les membres comme éditeurs.
  Les modifications dans Drive ne sont pas automatiquement reportées sur GitHub.

Pour modifier le notebook : changer le code dans `build.py` ou les commentaires dans `commentaires.py`, puis
`python rendu_final_concis/build.py` depuis la racine du dépôt, puis
`python rendu_final_concis/executer.py`. Le constructeur remplace le notebook : intégrer les modifications des
cellules dans les sources avant de le relancer. Les chiffres cités dans les commentaires doivent correspondre aux sorties.

La section diffusion comprend les équations, les références, les variantes C0/D0/D1–D4, les validations
chronologiques, les CRPS et twCRPS, la couverture des intervalles, une courbe d'apprentissage et les projections
des deux méthodes. D1/D2 sont réentraînés pour trois graines ; D3/D4 réutilisent ces réseaux avec un bootstrap de l'ancre.
La sélection enregistrée sur validation est D3 pour Tmax, D1 pour Tmin. Bayes obtient le meilleur CRPS global
observé sur le test parmi les méthodes principales comparées. Le test a déjà été consulté : la comparaison est rétrospective.

Les tableaux de référence sont extraits de `rendu_final/resultats/validation.csv` et `test.csv`, avec leurs empreintes
dans le code du notebook. Les tableaux de la nouvelle exécution sont présentés séparément.
Les tirages ne sont pas coupés pour les faire entrer dans un intervalle physique.

| Fichier | Rôle |
|---|---|
| `rendu_final_groupe.ipynb` | Le notebook à rendre |
| `build.py`, `commentaires.py` | Construisent le notebook à partir de celui du prof (`sujet_prof.ipynb`) |
| `diffusion.py` | Sources des cellules de diffusion, copiées dans le notebook lors de sa construction |
| `executer.py` | Exécute le notebook, conserve ses sorties et extrait les figures pour vérification |
| `*.csv` | Les données du prof |

Le notebook s'exécute seul dans Colab : il n'importe pas les scripts du dépôt.
