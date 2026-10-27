# Contexte complet du projet SMA, à donner à un LLM

**Mode d'emploi pour l'étudiant :** donne ce fichier en entier à ton LLM (ChatGPT, Claude, Gemini…) au début de la conversation, avec `kit.py` et `exemple.py` si tu veux qu'il écrive du code. Il aura alors toutes les informations du projet et de la compétition.

**Consigne pour le LLM qui lit ce fichier :** tu assistes un étudiant sur ce projet. Ce document décrit les faits : le sujet, les données, les règles, le calcul du score, le fonctionnement du code fourni. Appuie-toi dessus pour répondre. Il ne recommande volontairement **aucune méthode de modélisation** : le choix du modèle appartient à l'étudiant, et c'est l'objet de la compétition. Si une information manque ici, dis-le au lieu de la supposer. Respecte les règles de la section 6, en particulier : n'utilise et ne cite aucune connaissance sur les températures réellement observées à Brest de 2001 à 2025.

---

## 1. Le projet du professeur

- **Cours :** « Stochastic Processes for Environmental Data », projet SMA, TAF MCE, IMT Atlantique, 2026. Sujet proposé par Pierre Tandeo.
- **Thème :** les vagues de chaleur et les températures extrêmes à Brest. Le passé (1940–2025) est étudié avec des méthodes statistiques, le futur (jusqu'en 2100) avec des méthodes de machine learning, sous plusieurs scénarios d'émissions de CO2.
- **Rendu :** un seul notebook Jupyter par groupe, à compléter à partir du notebook fourni par le professeur (cellules `### TO DO ###`), déposé sur Moodle au plus tard le **vendredi 30 octobre 2026**.
- **Outils :** travail partagé sur Google Colab. Les slides recommandent PyTorch et le GPU, et encouragent l'usage d'outils d'IA.
- **Les deux parties sont obligatoires.**

### Ce que le professeur note

1. La qualité du code : concis et bien écrit, les commentaires sont bienvenus.
2. La qualité des sorties : ce sont des grandeurs physiques, toujours avec leurs unités (°C, ppm).
3. L'explication de la méthode : décrite mathématiquement, en LaTeX, directement dans le notebook.
4. La discussion des résultats : ils doivent avoir un sens physique et être commentés.

### Partie 1 : analyse statistique des vagues de chaleur

Elle utilise la température moyenne de chaque jour, de 1940 à 2025.

1. **Le cycle saisonnier.** Pour chaque jour de l'année (1 à 365), rassembler les températures de ce jour sur toutes les années et calculer les quantiles à 10 %, 50 % et 90 %. Lisser les trois courbes par une moyenne glissante d'un mois. Tracer et commenter.
2. **Les vagues de chaleur.** Un jour est « chaud » si sa température dépasse le quantile à 90 % lissé de son jour de l'année. Une vague de chaleur est une suite maximale de jours chauds consécutifs. Pour chaque vague : sa durée (nombre de jours), son intensité (anomalie moyenne de température pendant la vague, en °C), son année d'apparition.
3. **Le diagramme intensité–durée.** Un nuage de points, une vague par point : durée en abscisse, intensité en ordonnée, couleur selon l'année. Commenter.

Points que le sujet laisse ouverts, à trancher et à justifier dans le notebook :
- le traitement du 29 février (le sujet demande des jours de 1 à 365) ;
- la taille exacte de la fenêtre de lissage, et son traitement en début et fin d'année (le cycle est périodique) ;
- la « normale » servant à calculer l'anomalie : la médiane lissée ou le seuil à 90 % ;
- la durée minimale pour parler de vague (les slides disent « several consecutive days ») ;
- la saison : le seuil dépend du jour de l'année, donc la définition détecte aussi des épisodes doux en hiver.

### Partie 2 : modélisation stochastique des extrêmes futurs

Elle utilise, pour chaque année, la température maximale, la température minimale et le CO2 mondial.

1. Tracer et commenter la température maximale annuelle de 1940 à 2025.
2. Calculer la corrélation (coefficient de Pearson) entre la température maximale annuelle et le CO2. Tester plusieurs transformations des deux variables pour l'augmenter ; le sujet cite par exemple un logarithme ou une moyenne glissante.
3. Produire des prévisions **probabilistes** (le notebook précise « not deterministic ») de la température maximale annuelle jusqu'en 2100, conditionnellement aux trois scénarios de CO2, avec une méthode récente de machine learning. La méthode doit être présentée mathématiquement et le choix justifié. Les slides évoquent par exemple les modèles de diffusion, les méthodes de Monte-Carlo ou les méthodes paramétriques.
4. Donner la distribution de la température maximale en 2100 sous chaque scénario, et la **probabilité de dépasser 40 °C**.
5. Refaire l'étude pour les minima annuels. Ici, le sujet autorise une autre approche, sans formulation mathématique.

**Une ambiguïté du sujet.** « La probabilité de dépasser 40 °C d'ici 2100 » peut se lire de deux façons : la probabilité que l'année 2100 dépasse 40 °C, ou la probabilité qu'au moins une année d'ici 2100 dépasse 40 °C. La seconde est plus grande que la première. Le groupe a prévu de donner les deux en le disant clairement.

---

## 2. La compétition du groupe

Elle est organisée par le groupe, pas par le professeur. Elle ne concerne que les points 3 et 5 de la partie 2.

- Chaque membre propose son propre modèle de prévision probabiliste.
- Tous les modèles sont comparés sur le même benchmark, décrit ci-dessous.
- Le meilleur modèle devient celui du notebook rendu au professeur.
- **Chacun lance le benchmark lui-même**, autant de fois qu'il veut. Il n'y a rien à envoyer à personne.
- Les scores sont comparés le **vendredi 23 octobre 2026**. Le notebook est ensuite écrit ensemble, du 23 au 30 octobre.

### Le principe

On se place comme si on était fin 2000. Le modèle apprend sur les années 1940 à 2000, puis prédit les années 2001 à 2025 en ne connaissant que leur CO2. Le benchmark compare ces prédictions aux vraies températures.

| Période | Rôle | Ce que le modèle peut utiliser |
|---|---|---|
| 1940–2000 (61 ans) | Entraînement | Températures et CO2 |
| 2001–2025 (25 ans) | Test : c'est là qu'on est noté | Le CO2 uniquement |
| 2100, 3 scénarios | Tests de cohérence, pas de note | Le CO2 uniquement |

### Ce que le modèle doit produire

Une prévision probabiliste est donnée sous forme de **tirages** : 10 000 valeurs plausibles de la température, en °C. Il faut exactement quatre tableaux :

| Tableau | Taille | Contenu |
|---|---|---|
| `test_max` | 25 × 10 000 | maximum annuel ; une ligne par année, de 2001 à 2025, dans l'ordre |
| `test_min` | 25 × 10 000 | minimum annuel ; même organisation |
| `proj_max` | 3 × 10 000 | maximum de l'année 2100 ; une ligne par scénario, dans l'ordre SSP1-2.6, SSP2-4.5, SSP5-8.5 |
| `proj_min` | 3 × 10 000 | minimum de l'année 2100 ; même organisation |

Si un modèle produit une loi (par exemple des paramètres) plutôt que des tirages, il faut en tirer 10 000 valeurs par ligne. Si un modèle produit une seule valeur par année, les 10 000 tirages sont tous égaux à cette valeur ; c'est accepté par le format, mais voir le test de cohérence n° 2.

---

## 3. Les données

Tout est dans le dossier `data/`. Les températures viennent de la réanalyse **ERA5** du centre européen ECMWF : une reconstruction de l'atmosphère passée, qui combine un modèle météo et les observations, sur une maille d'environ 9 km. Les lignes sont identiques à celles des fichiers du professeur ; seules les années 2001–2025 ont été séparées.

| Fichier | Colonnes | Lignes | Contenu |
|---|---|---|---|
| `yearly_temp_brest_train.csv` | `valid_time`, `max`, `min`, `co2` | 61 | Pour chaque année de 1940 à 2000 : température maximale et minimale de l'année (°C), CO2 mondial (ppm) |
| `daily_temp_brest_train.csv` | `valid_time`, `mean` | 22 281 | Température **moyenne** de chaque jour (°C), du 1er janvier 1940 au 31 décembre 2000 |
| `test_inputs.csv` | `valid_time`, `co2` | 25 | CO2 (ppm) de chaque année de 2001 à 2025 |
| `yearly_future_co2.csv` | `valid_time`, `ssp1-2.6`, `ssp2-4.5`, `ssp5-8.5` | 75 | CO2 (ppm) de chaque année de 2026 à 2100, sous trois scénarios |
| `verite_2001_2025.csv` | `annee`, `max`, `min` | 25 | Les vraies températures maximale et minimale de 2001 à 2025. **Réservé au calcul du score** |

Précisions :
- Dans les fichiers annuels, `valid_time` est le 1er janvier de l'année (par exemple `1940-01-01`).
- **Le maximum annuel n'est pas le maximum des moyennes journalières.** Le maximum annuel est la température la plus haute atteinte dans l'année. Le fichier journalier contient des moyennes sur 24 heures, qui lissent le pic de l'après-midi : la plus grande moyenne journalière d'une année est nettement inférieure au maximum annuel. Même remarque pour le minimum.
- **ppm** : parties par million, l'unité de concentration du CO2.
- Le CO2 va de 310,0 ppm (1940) à 388,1 ppm (2000) dans l'entraînement, et de 389,5 ppm (2001) à 428,5 ppm (2025) dans le test. Le test demande donc de prédire pour un CO2 supérieur à tout ce que le modèle a vu.

### Les scénarios SSP

Les *Shared Socioeconomic Pathways* sont les scénarios d'évolution de la société utilisés par le GIEC. Le nombre après le tiret est le forçage radiatif atteint en 2100, en W/m² : le surplus d'énergie reçu par la Terre à cause des gaz à effet de serre. Ce n'est pas une unité de CO2.

| Scénario | Description | CO2 en 2100 |
|---|---|---|
| SSP1-2.6 | monde sobre | 400,0 ppm |
| SSP2-4.5 | intermédiaire | 527,0 ppm |
| SSP5-8.5 | monde très fossile | 946,2 ppm |

---

## 4. Le classement

Il se fait en trois étapes, dans cet ordre.

### Étape 1 : les trois tests de cohérence (éliminatoires)

Le benchmark ne peut noter que 2001–2025. Or le projet porte sur 2100, avec un CO2 qui peut atteindre 946 ppm. Les tests écartent les modèles qui seraient bons sur 2001–2025 mais absurdes en 2100. Ils s'appliquent **séparément au maximum et au minimum**. Échouer à un seul test, pour l'une des deux variables, élimine le modèle.

1. **Plus de CO2 ne refroidit pas.** On calcule la médiane des 10 000 tirages de 2100 pour chaque scénario. Il faut : médiane(SSP1-2.6) ≤ médiane(SSP2-4.5) + 0,1 °C, et médiane(SSP2-4.5) ≤ médiane(SSP5-8.5) + 0,1 °C. La tolérance de 0,1 °C absorbe le bruit des tirages.
2. **L'incertitude ne rétrécit pas.** La « largeur » d'un jeu de tirages est l'écart entre son quantile à 90 % et son quantile à 10 %. Il faut : largeur des tirages de 2100 sous SSP5-8.5 ≥ 0,95 × la moyenne des largeurs des 25 années de test.
3. **Pas de valeur absurde.** Tous les tirages, test et 2100, doivent être entre 0 et 50 °C pour le maximum, entre −30 et 20 °C pour le minimum.

### Étape 2 : le score final

**Le score final est le CRPS de la température maximale annuelle, moyenné sur les 25 années 2001–2025. Il est en °C. Le plus bas gagne.**

Le CRPS (*Continuous Ranked Probability Score*) mesure l'écart entre une loi prédite et la valeur observée. Pour une année, avec les tirages x₁, …, x_N et la vraie valeur y :

CRPS = moyenne des |xᵢ − y| − ½ × moyenne des |xᵢ − xⱼ|

où la seconde moyenne porte sur toutes les paires de tirages (i, j).

- Le premier terme est la distance moyenne entre les tirages et la vraie valeur.
- Le second terme mesure l'étalement des tirages ; il est soustrait.
- Il est en °C parce que c'est une distance entre températures.
- Si tous les tirages sont égaux à une même valeur a, le second terme est nul et le CRPS vaut |a − y| : l'erreur absolue. Le CRPS généralise l'erreur absolue aux prévisions probabilistes.
- Il vaut 0 seulement pour une prévision certaine et exacte.
- Définition équivalente, avec F la fonction de répartition prédite : CRPS(F, y) = ∫ (F(u) − 1{u ≥ y})² du.
- C'est un **score propre** : si la vraie valeur suit une loi G, aucune prévision n'obtient en moyenne un meilleur CRPS que G elle-même. Annoncer une loi plus large ou plus étroite que ce qu'on croit vraiment ne fait pas gagner en moyenne.

Le score final est la moyenne des 25 CRPS annuels. Comme les tirages sont aléatoires, le score varie un peu d'un lancement à l'autre : d'environ 0,003 °C avec 10 000 tirages (mesuré sur le modèle de référence).

### Étape 3 : l'égalité

Le score est une moyenne sur 25 années seulement, donc deux modèles proches peuvent être départagés par la chance. Si deux scores finaux sont à moins de **0,05 °C** l'un de l'autre, il y a égalité : le gagnant est celui qui a le plus petit **CRPS de la température minimale annuelle**, calculé de la même façon sur 2001–2025.

---

## 5. Le code fourni

Dépendances : Python, `numpy`, `pandas`. Rien d'autre.

### `kit.py`

| Élément | Rôle |
|---|---|
| `kit.charger()` | Renvoie quatre tableaux pandas, dans cet ordre : journalier 1940–2000, annuel 1940–2000, CO2 de 2001–2025, CO2 futur. La colonne `valid_time` est convertie en date. Ne renvoie pas les vraies valeurs de 2001–2025 |
| `kit.benchmark(test_max, test_min, proj_max, proj_min)` | Lance le benchmark sur les quatre tableaux de la section 2 et affiche le résultat |
| `kit.crps(tirages, obs)` | CRPS moyen en °C. `tirages` de taille (nombre d'années, nombre de tirages), `obs` de taille (nombre d'années) |
| `kit.N_TIRAGES` | 10 000 |
| `kit.ANNEES_TEST` | la liste des années 2001 à 2025 |
| `kit.SCENARIOS` | `('ssp1-2.6', 'ssp2-4.5', 'ssp5-8.5')`, l'ordre attendu des lignes pour 2100 |

`kit.crps` calcule exactement la formule de la section 4, en triant les tirages pour éviter de parcourir toutes les paires.

### Lancer le benchmark et lire sa sortie

```python
import kit
jour, an, test, futur = kit.charger()

# ... le modèle de l'étudiant construit ici les quatre tableaux ...

kit.benchmark(test_max, test_min, proj_max, proj_min)
```

Le CO2 des années de test est `test.co2`. Le CO2 de 2100 pour les trois scénarios, dans le bon ordre, s'obtient ainsi :

```python
co2_2100 = futur.loc[futur.valid_time.dt.year == 2100, list(kit.SCENARIOS)].to_numpy().ravel()
```

Sortie quand tout va bien :

```
Tests de cohérence : OK
SCORE FINAL (CRPS du max, 2001-2025) : 1.70 °C   (référence à battre : 1.70)
Départage   (CRPS du min, 2001-2025) : 1.06 °C   (référence : 1.06)
```

Sortie quand un test échoue (les scores sont affichés quand même, mais le modèle est éliminé) :

```
Tests de cohérence : ÉCHEC -> ÉLIMINÉ
  - max : plus de CO2 donne plus froid en 2100 (médianes SSP1, SSP2, SSP5 = [27.0, 26.0, 25.0] °C)
```

`kit.benchmark` renvoie le couple (score final, score de départage), ou `None` si un test échoue. Il s'arrête avec un message d'erreur si un tableau n'a pas la bonne taille ou contient des valeurs non finies (NaN, infini).

### `exemple.py` : le modèle de référence

Il a été écrit **par le groupe**, pas par le professeur ni par l'école. Il sert d'exemple de bout en bout et de score à battre. Le lancer suffit à vérifier que l'installation fonctionne.

Ce qu'il fait, pour le maximum puis pour le minimum :
- il ajuste par moindres carrés une droite T = a + b · ln(CO2) sur les 61 années d'entraînement ;
- si la pente b est négative, il la remplace par 0 et recalcule a ;
- il estime l'écart-type σ des résidus ;
- pour chaque année à prédire, il tire 10 000 valeurs dans la loi normale de moyenne a + b · ln(CO2) et d'écart-type σ.

Ses scores : **1,70 °C** pour le maximum (score final) et **1,06 °C** pour le minimum. Il passe les trois tests de cohérence.

### Sur Google Colab

Télécharge le dossier depuis le Drive (Google le fournit en un fichier zip), envoie ce zip dans Colab avec le panneau « Fichiers », puis lance `!unzip -o nom_du_fichier.zip` dans une cellule. Si les fichiers se retrouvent dans un sous-dossier, lance `%cd nom_du_sous_dossier` avant `import kit`. Le dossier `data/` doit rester à côté de `kit.py`.

---

## 6. Les règles

1. **Le modèle n'apprend que sur 1940–2000.** Les deux fichiers d'entraînement, journalier et annuel, sont autorisés en entier.
2. **Pour 2001–2025 et pour 2100, la seule entrée est le CO2** (`test_inputs.csv` et `yearly_future_co2.csv`). Les trajectoires de CO2 de 2026 à 2100 sont utilisables.
3. **`verite_2001_2025.csv` ne sert qu'au calcul du score.** Il ne doit jamais entrer dans un modèle, ni pour l'entraîner ni pour le régler à la main. Les fichiers complets du professeur (1940–2025) sont interdits pour la compétition pour la même raison.
4. **Aucune donnée extérieure** : pas d'autre station, pas d'autre variable, pas de sortie de modèle climatique.
5. **Aucune connaissance extérieure sur la période de test** : pas d'ajustement fondé sur ce qu'on sait des années 2001–2025 (par exemple une canicule connue). Les connaissances générales de statistique, de machine learning et de physique sont évidemment permises.
6. **Le score annoncé doit être reproductible** : les autres doivent pouvoir relancer le modèle et retrouver le score, au bruit des tirages près. Fixer la graine aléatoire aide.
7. Ces règles reposent sur la confiance : les vraies valeurs sont dans le kit pour que chacun puisse calculer son score.

---

## 7. Pourquoi le benchmark est fait ainsi

- **Un bloc d'années final, pas des années au hasard.** Avec des années de test tirées au hasard, le modèle connaîtrait les années voisines et n'aurait qu'à interpoler. Avec un bloc final, il doit prévoir un futur jamais vu, avec un CO2 plus élevé que tout ce qu'il a vu. C'est la situation du projet (prévoir 2100), en plus modéré.
- **Coupure en 2000.** Un compromis : 25 années de test pour que le score soit assez fiable, 61 années d'entraînement pour apprendre.
- **Les données journalières sont coupées en 2000 aussi.** Les journées d'une année sont très liées à son maximum annuel ; les laisser reviendrait à donner une partie de la réponse.
- **Le CRPS.** Il juge la loi entière et pas une seule valeur, il est en °C, et c'est un score propre. Un score sur une seule valeur prédite ignorerait l'incertitude, qui est au cœur du projet.
- **Le maximum comme score final.** La question centrale du projet porte sur les fortes chaleurs. Le minimum sert à départager.
- **Les tests de cohérence.** Le benchmark ne voit pas 2100 ; ils excluent les modèles qui donneraient des conclusions absurdes à cet horizon.

## 8. Les limites à garder en tête

- **25 années, c'est peu.** Le score distingue un bon modèle d'un mauvais, mais deux bons modèles peuvent être à égalité.
- **Chacun peut relancer le benchmark autant qu'il veut.** Un modèle réglé à force d'essais sur 2001–2025 peut avoir un score flatteur, qui ne se retrouverait pas sur d'autres années.
- **Le benchmark ne mesure pas la qualité en 2100.** Les tests de cohérence sont un garde-fou minimal. La réponse à la question des 40 °C reste à justifier dans le notebook.
- **Pour le notebook final**, le professeur fournit les données jusqu'en 2025. Le modèle retenu pourra y être ré-entraîné sur toute la période ; la coupure en 2000 ne sert qu'à la compétition.

## 9. Questions fréquentes

**Qui a fait le benchmark et le modèle d'exemple ?** Le groupe. Le professeur a fourni le sujet, le notebook à compléter et les données complètes.

**Le score est en °C, pourquoi ?** Parce que le CRPS est une distance entre des températures prédites et une température observée. Un score de 1,70 °C veut dire, en gros, que la prévision se trompe de 1,70 °C en moyenne, en tenant compte de son incertitude.

**Peut-on lancer le benchmark plusieurs fois ?** Oui, autant qu'on veut. Voir la deuxième limite de la section 8.

**Faut-il envoyer un fichier ?** Non. Chacun annonce son score le 23 octobre et doit pouvoir le reproduire.

**Peut-on utiliser les données journalières ?** Oui, celles de 1940–2000.

**Peut-on utiliser un modèle différent pour le maximum et pour le minimum ?** Oui. Le sujet du professeur l'autorise explicitement pour les minima.

**Peut-on utiliser n'importe quelle bibliothèque ?** Oui. Le sujet recommande PyTorch, sans l'imposer.

**Le modèle doit-il prédire les années 2026 à 2099 ?** Pas pour le benchmark, qui ne demande que 2001–2025 et 2100. Le notebook final, lui, demande des prévisions jusqu'en 2100.

**Que se passe-t-il si un test de cohérence échoue ?** Le modèle est éliminé, quel que soit son score. Le message du benchmark dit quel test a échoué, pour quelle variable, avec les valeurs en cause.

**Mon score change un peu à chaque lancement, c'est normal ?** Oui, les tirages sont aléatoires : environ 0,003 °C d'écart avec 10 000 tirages. Fixer la graine aléatoire rend le score identique d'un lancement à l'autre.

**Pourquoi 10 000 tirages ?** Pour que ce bruit soit petit devant les écarts entre modèles.

**Que gagne le vainqueur ?** Son modèle devient celui du notebook rendu au professeur. Le reste de l'organisation est dans le message envoyé au groupe.
