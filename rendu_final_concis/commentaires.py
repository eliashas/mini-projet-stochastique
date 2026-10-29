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

C['comparaison'] = r'''
**Commentaire.** On retrouve les scores du tableau : 1,57 °C pour Tmax et 0,98 °C pour Tmin, contre 1,70 et 1,14 °C
pour le modèle de référence.
'''

C['proj'] = r'''
**Commentaire.** Les trois scénarios partent du même niveau en 2026 (médiane d'environ 27 °C) puis s'écartent. Avec
SSP1-2.6, le CO2 redescend à 400 ppm et la médiane reste à 26,5 °C en 2100. Avec SSP2-4.5, elle atteint 28,5 °C, et avec
SSP5-8.5 (946 ppm) 32,8 °C : une année normale de 2100 serait alors aussi chaude que les années les plus chaudes
observées jusqu'ici. Les bandes 5-95 % sont larges (environ 7 °C en 2026, 11 °C en 2100 pour SSP5-8.5) : Tmax varie
beaucoup d'une année à l'autre, et l'incertitude sur la pente compte de plus en plus quand le CO2 augmente.
'''

C['dist'] = r'''
**Réponse.** Probabilité de dépasser 40 °C à Brest :

| Scénario | Médiane 2100 | P(Tmax 2100 > 40 °C) | P(au moins une année > 40 °C entre 2026 et 2100) |
|---|---|---|---|
| SSP1-2.6 | 26,5 °C | ≈ 0 | ≈ 0 |
| SSP2-4.5 | 28,5 °C | ≈ 0 | ≈ 0 |
| SSP5-8.5 | 32,8 °C | 1,5 % | 7,8 % |

**Commentaire.** Dépasser 40 °C reste rare pour une année donnée, même en 2100 avec SSP5-8.5 (1,5 %). Sur 75 ans, le
risque s'accumule : dans ce scénario, environ 1 trajectoire sur 13 dépasse 40 °C au moins une fois. Avec 10 000
tirages, « 0 » veut seulement dire moins d'environ 1 chance sur 10 000, pas que c'est impossible.

Il faut prendre ces chiffres avec prudence : 40 °C est loin de tout ce qu'on a observé (34,2 °C au maximum), et on
extrapole jusqu'à 946 ppm alors qu'on n'a vu que 310 à 428 ppm. Le CO2 est aussi la seule entrée du modèle.
'''

C['minima'] = r'''
**Approche.** On refait la même étude avec la même régression bayésienne : sur le test 2001-2025, elle a aussi
le meilleur CRPS pour Tmin (0,98 °C), pratiquement à égalité avec la GEV et la diffusion d'Elias (voir la question 3). Le prof ne donne pas de seuil pour Tmin :
on prend **0 °C**, le seuil du gel. Sur 1940-2025, le minimum annuel a été négatif 52 années sur 86.

**Commentaire.** Tmin varie de −6,6 °C (1987) à 2,6 °C (2019). Contrairement à Tmax, la moyenne sur 11 ans ne montre
pas de tendance nette jusqu'en 2000 : la moyenne vaut −0,7 °C sur 1940-1979 comme sur 1980-2025, avec des hivers très
froids au milieu des années 1980 (−5,5 °C en 1985, −6,6 °C en 1987). Elle remonte seulement depuis 2000, jusqu'à
environ +0,3 °C autour de 2020. Le lien avec le CO2 est donc encore plus faible que pour Tmax ($r=0{,}15$).

Dans les projections, les minima remontent avec le CO2 : la médiane 2100 vaut −0,4 °C (SSP1-2.6), 0,5 °C (SSP2-4.5)
et 2,5 °C (SSP5-8.5). La probabilité que le minimum de 2100 soit sous 0 °C passe de 58 % à 17 %. Il gèlera encore au
moins une fois entre 2026 et 2100 dans tous les scénarios (100 % des tirages), mais les hivers sans gel deviennent
fréquents avec SSP5-8.5. Sur l'histogramme, la loi de 2100 se décale vers la droite et s'élargit quand le CO2
augmente, comme pour Tmax. Comme le lien avec le CO2 est faible sur le passé, ces projections sont moins sûres que
celles de Tmax.
'''

C['conclusion'] = r'''
# Conclusion

- **Le passé.** À Brest, l'écart entre l'hiver et l'été est faible (environ 9 °C). Les vagues de chaleur sont devenues
  bien plus fréquentes : environ 3 par an dans les années 1960-1970, 12 par an sur 2020-2025. La plus intense est
  celle de juillet 2022.
- **Le futur.** Le lien entre les extrêmes annuels et le CO2 est faible d'une année à l'autre, mais net sur la
  tendance. Parmi les modèles du groupe, la régression bayésienne a le meilleur CRPS sur 2001-2025 (1,57 °C contre
  1,70 °C pour la référence). En 2100, la médiane du maximum annuel va de 26,5 °C (SSP1-2.6) à 32,8 °C (SSP5-8.5).
  Dépasser 40 °C reste rare une année donnée (1,5 % en 2100 avec SSP5-8.5), mais atteint 7,8 % sur l'ensemble
  2026-2100 dans ce scénario. Pour les minima, le gel devient moins fréquent sans disparaître.
- **Limites.** 86 années, c'est peu pour connaître les valeurs extrêmes. Le CO2 est notre seule variable explicative,
  et les scénarios nous font extrapoler bien au-delà des concentrations observées.
'''
