"""Nos commentaires (cellules markdown) du notebook, lus par build.py.
Les chiffres cités viennent des sorties du notebook : les revérifier si on change le code."""

C = {}

C['membres'] = '''
The five students are:
- Elias Hasnaou
- Christian Trandafir
- Reda El Mekkaoui
- Mohamed Yazid Samrani
- Sefyani Diae

**Utilisation de l’IA.** Comme le proposait le sujet, nous avons utilisé des assistants d’IA (ChatGPT, Claude) pour nous aider à concevoir et écrire le code, explorer des méthodes de prévision et relire le notebook. Nous avons exécuté, vérifié et compris tous les calculs, et les choix de méthode, les résultats et leur interprétation sont les nôtres.
'''

C['saison'] = r'''
**Commentaire.** Les trois courbes ont la même forme. La température est la plus basse vers le 19 février (quantile 50 %
à 7,8 °C) et la plus haute vers le 7 août (16,5 °C), donc environ 9 °C d'écart seulement entre l'hiver et l'été.

On pourrait s'attendre à ce que les jours les plus chauds soient autour du 21 juin, le jour où il y a le plus de soleil.
Pourtant le pic arrive vers le 7 août, environ 7 semaines plus tard, et le creux vers le 19 février au lieu du
21 décembre. On pense que c'est dû à la mer autour de Brest : elle se réchauffe et se refroidit lentement, donc l'air
suit le soleil avec du retard.

L'écart entre les quantiles 10 % et 90 % (entre la courbe bleue et la rouge) change selon la saison : environ 7,5 °C vers
le 10 janvier contre 3,4 °C fin juillet. Un même jour d'hiver peut donc être très doux ou très froid selon les années,
alors qu'en été les températures varient moins. La courbe à 90 % servira de seuil pour les vagues de chaleur.
'''

C['vagues'] = r'''
Un jour $d$ est **chaud** si $T_d>q_{90}(j_d)$, où $q_{90}(j)$ est le quantile 90 % lissé du jour de l'année $j$.
Une **vague de chaleur** est une suite de jours chauds consécutifs. Le sujet parle de « plusieurs jours », on a choisi
d'en garder au moins 3. Pour une vague $W$ :

$$\text{durée}=|W|\ \text{jours},\qquad \text{intensité}=\frac1{|W|}\sum_{d\in W}\big(T_d-q_{50}(j_d)\big)\ \text{en °C}.$$

L'intensité dit donc de combien de degrés la vague est, en moyenne, au-dessus de la normale de la date (le quantile 50 %).

**Commentaire.** On trouve 421 vagues en 86 ans, soit environ 5 par an. Les plus longues durent 14 jours (août 1955 et
août 1976). La plus intense est celle de **juillet 2022** : pendant 3 jours, il a fait en moyenne 7,7 °C de plus que la
normale pour cette date.

Une vague n'est pas forcément en été. Le seuil (le quantile 90 %) change avec la date : environ 11 °C en janvier et
18,5 °C en août. Par exemple, du 11 au 20 avril 1945, il a fait entre 12,6 et 17,4 °C pendant 10 jours : c'est très chaud
pour un mois d'avril, alors qu'en août ce seraient des jours plutôt frais.
'''

C['nuage'] = r'''
**Commentaire.** La plupart des vagues sont courtes : environ 8 sur 10 durent 3 à 5 jours, et presque toutes ont une
intensité entre 2,5 et 5 °C. Le lien entre durée et intensité est faible : une vague longue n'est pas forcément plus
intense. Les vagues les plus intenses (plus de 5 °C) sont réparties sur toute la période, on ne voit pas de tendance
nette sur l'intensité.

Ce qui change vraiment, c'est le nombre de vagues (deuxième graphique) : environ 3 par an dans les années 1960-1970,
6 dans les années 2000, et 12 par an sur 2020-2025. Le seuil de 90 % est le même pour toutes les années, donc s'il y a
plus de vagues aujourd'hui, c'est que les températures ont augmenté.
'''

C['tmax'] = r'''
**Commentaire.** Le maximum annuel varie beaucoup d'une année à l'autre : de 21,7 °C (1958 et 2007) à 34,2 °C (2022).
C'est normal, car il ne dépend que des quelques jours les plus chauds de l'année.

La moyenne sur 11 ans montre mieux la tendance. Elle baisse un peu entre les années 1940 et 1960 (de 26 à environ
24,5 °C), remonte vers 26 °C dans les années 1980, reste à peu près stable jusqu'en 2010, puis monte nettement jusqu'à
environ 28,4 °C autour de 2020. En moyenne, le maximum annuel vaut 25,1 °C sur 1940-1979 et 26,3 °C sur 1980-2025.
Le record de 2022 (34,2 °C) dépasse de plus de 3 °C le deuxième plus chaud (31,0 °C en 2003).
'''

C['correl'] = r'''
**Commentaire.** La corrélation entre Tmax et le CO2 est faible ($r = 0{,}31$) : d'une année à l'autre, Tmax varie
beaucoup, et le CO2 n'explique qu'une petite partie de ces variations.

Transformer les variables (ln, carré) ne change presque rien (entre 0,30 et 0,32). C'est logique : sur des intervalles
aussi petits (310 à 428 ppm, 21 à 34 °C), ces fonctions sont presque des droites.

Par contre, lisser la température augmente beaucoup la corrélation : 0,49 sur 5 ans, 0,61 sur 11 ans, 0,83 sur 21 ans.
La tendance de Tmax suit donc bien le CO2, mais pas la valeur d'une année précise. C'est pour ça qu'il faut des
prédictions probabilistes, et pas une seule valeur par année.
'''

C['comparaison'] = r"""
Ces scores sont recalculés avec de nouveaux tirages. Les derniers centièmes peuvent différer des résultats archivés.
On garde les deux tableaux distincts : la validation a servi aux choix ; le test décrit les performances observées
sur 2001–2025, après ces choix.

Sur 2001–2025, l’intervalle prédictif à 90 % de Bayes contient Tmax pour 20 années sur 25 (80 %),
ce qui suggère des intervalles un peu trop étroits sur cette période.
"""

C['proj'] = r"""
**Commentaire.** Les deux méthodes donnent des médianes qui montent avec le CO₂ et des trajectoires proches pour
un même scénario. Les trois scénarios se séparent progressivement : la concentration redescend à 400 ppm avec
SSP1-2.6, atteint 527 ppm avec SSP2-4.5 et 946 ppm avec SSP5-8.5 en 2100. Les valeurs historiques ne dépassaient
pas 428 ppm : le dernier scénario demande donc une forte extrapolation.

Les bandes de D3 incluent la variabilité annuelle apprise et l'incertitude sur la droite. Celles de Bayes incluent
la variabilité gaussienne et l'incertitude sur ses paramètres. Leur largeur ne mesure pas les erreurs possibles
sur les hypothèses communes : ancre logarithmique, rôle du seul CO₂ et distribution résiduelle stable.
"""

C['dist'] = r"""
**Commentaire.** Sous SSP5-8.5, les médianes de D3 et Bayes sont proches : environ 32,6 et 32,8 °C dans cette
exécution. Pourtant, la probabilité de dépasser 40 °C en 2100 vaut environ 2,6 % avec D3 et 1,5 % avec Bayes.
Ce seuil se situe dans la queue droite : une différence de dispersion ou de forme de la loi peut beaucoup
changer la proportion de dépassements. La comparaison permet de voir cette sensibilité au modèle.

Le risque en 2100 concerne **une année**. Le risque « au moins une fois » concerne **75 années** : il est calculé
sur des trajectoires où les paramètres sont partagés dans le temps et les innovations annuelles sont indépendantes
conditionnellement à ces paramètres. Une autre dépendance entre années pourrait changer ce risque cumulé.
Sous SSP5-8.5, ce risque cumulé vaut environ 17,2 % avec D3 et 8,1 % avec Bayes dans cette exécution.

Un résultat de zéro dépassement n'est pas une probabilité physique nulle. Avec 10 000 tirages indépendants,
la borne binomiale supérieure à 95 % est d'environ 0,03 % pour le modèle simulé. Elle mesure seulement l'erreur
Monte-Carlo. L'incertitude liée au modèle et à l'extrapolation est beaucoup plus difficile à quantifier.
On n'a observé aucun Tmax supérieur à 34,2 °C dans ces données : le test historique ne valide pas directement
la queue à 40 °C en 2100.
"""

C['minima'] = r"""
**Approche et commentaire.** On reprend les étapes pour Tmin avec D1, retenu sur validation, et Bayes comme
comparaison. Le seuil choisi est **0 °C**, pour décrire les années avec gel. Il ne s'agit pas du nombre de jours
de gel : une seule journée négative suffit à rendre le minimum annuel négatif.

Sur 1940–2025, le minimum annuel est négatif 52 années sur 86. Il varie de −6,6 °C en 1987 à 2,6 °C en 2019.
Le lien avec le CO₂ est plus faible que pour Tmax, avec une corrélation d'environ 0,15. La moyenne sur 11 ans
reste proche de −0,7 °C jusque vers 2000, puis remonte. Les différences entre années sont importantes.

Dans les projections, les minima remontent avec le CO₂ et la probabilité de gel en 2100 diminue. Un résultat
proche de 100 % dans la colonne « au moins une fois » signifie que presque toutes les trajectoires simulées
contiennent une année avec gel entre 2026 et 2100 ; il ne signifie pas qu'il gèlera chaque année.
La faible relation historique et les hypothèses sur l'évolution de la dispersion limitent ces projections.

Sous SSP5-8.5, D1 et Bayes donnent une probabilité de gel en 2100 d'environ 18 % et 17 %. Leurs intervalles
diffèrent toutefois : D1 conserve une ancre fixe et une dispersion résiduelle stable, donc sa bande garde une
largeur presque constante. Bayes inclut l'incertitude sur la pente et sa bande s'élargit. D1 était préférable
sur la validation historique ; cela ne garantit pas qu'il représente toute l'incertitude d'une extrapolation à 2100.
"""

C['conclusion'] = r"""
# Conclusion

On identifie **421 vagues de chaleur** d'au moins trois jours entre 1940 et 2025, avec une fréquence
plus élevée sur les dernières décennies. La plus intense est celle de juillet 2022.

**Modèles retenus sur validation : D3 pour Tmax et D1 pour Tmin.** En 2100 sous SSP5-8.5, D3 donne une
médiane de Tmax d'environ **32,6 °C**, une probabilité de dépasser 40 °C de **2,6 % dans l'année** et de
**17 % au moins une fois entre 2026 et 2100**. Bayes donne, en comparaison, environ **1,5 %** et **8 %**
pour ces deux risques. Pour Tmin, la probabilité de gel en 2100 est d'environ **18 % avec D1**, contre
**17 % avec Bayes**, dans le même scénario.

Ces probabilités restent sensibles à l'extrapolation au-delà des CO₂ observés, à la loi des fluctuations
et à l'hypothèse de dépendance entre les années.
"""
