"""Nos commentaires (cellules markdown) du notebook, lus par build.py.
Les chiffres cités viennent des sorties du notebook : les revérifier si on change le code."""

C = {}

C['membres'] = '''
The five students are:
- Elias Hasnaou
- Christian [nom à compléter]
- Reda El Mekkaoui
- Yazid [nom à compléter]
- [à compléter]
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
**Commentaire.** Le maximum annuel varie beaucoup d'une année à l'autre (de 21,7 à 34,2 °C), car il dépend de la
météo de quelques jours. La moyenne sur 11 ans est à peu près plate jusqu'aux années 1980, puis elle monte : 25,1 °C
en moyenne sur 1940-1979 contre 26,3 °C sur 1980-2025. Les années récentes sont aussi plus variables (écart-type
de 1,9 à 2,4 °C). Le record est 2022 avec 34,2 °C, bien au-dessus des autres années.
'''

C['correl'] = r'''
**Commentaire.** La corrélation brute est faible ($r\approx0{,}31$) : une année donnée, la météo compte plus que le CO2.
Transformer le CO2 change peu de chose ($\ln$ CO2 : 0,30, CO2² : 0,32), car le CO2 ne va que de 310 à 428 ppm et sur
un si petit intervalle ces fonctions sont presque linéaires. Par contre, lisser la température augmente beaucoup la
corrélation (0,49 sur 5 ans, 0,61 sur 11 ans, 0,83 sur 21 ans) : on enlève le bruit d'une année à l'autre et il reste
la tendance, qui suit le CO2. Cela ne veut pas dire qu'on peut prédire le maximum d'une année précise : c'est pour ça
qu'on fait ensuite des prédictions probabilistes. On garde $\ln$ CO2 dans les modèles car c'est la forme physique
de l'effet de serre (le forçage radiatif est proportionnel à $\ln(C/C_0)$), même si ici les scores sont proches.
'''

C['comparaison'] = r'''
**Commentaire.** En validation, Bayes et la GEV sont à égalité (1,166 et 1,168 °C) : on retient **Bayes**, le plus
simple des deux. Le test sur 2001-2025 confirme ce choix : Bayes y a le meilleur score (1,57 °C), devant la GEV
(1,66 °C) et la référence (1,70 °C). Ce qui aide Bayes, c'est la prise en compte de l'incertitude sur la pente :
les intervalles s'élargissent quand le CO2 sort de ce qu'on a vu à l'entraînement, ce qui est le cas sur 2001-2025.

Le réseau de neurones ne fait pas mieux que la référence : avec seulement 30 à 60 années pour apprendre, il ne
trouve rien de plus qu'une loi proche d'une gaussienne. La régression quantile est la moins bonne : ajuster 99 droites
sur si peu de points rend les quantiles extrêmes instables.
'''

C['proj'] = r'''
**Commentaire.** Les trois scénarios partent du même niveau en 2026 (médiane d'environ 27 °C) puis s'écartent. Avec
SSP1-2.6 le CO2 redescend à 400 ppm et la médiane revient à 26,5 °C en 2100. Avec SSP2-4.5 elle atteint 28,6 °C et
avec SSP5-8.5 (946 ppm) 32,8 °C : une année normale de 2100 serait alors aussi chaude que les années les plus chaudes
observées jusqu'ici. Les bandes 5-95 % sont larges (environ 7 °C en 2026, 11 °C en 2100 pour SSP5-8.5) : la météo d'une
année reste très variable, et l'incertitude sur la pente pèse de plus en plus quand le CO2 augmente.
'''

C['dist'] = r'''
**Réponse.** Avec Bayes, la probabilité de dépasser 40 °C à Brest :

| Scénario | Médiane 2100 | P(Tmax 2100 > 40 °C) | P(au moins une année > 40 °C entre 2026 et 2100) |
|---|---|---|---|
| SSP1-2.6 | 26,5 °C | ≈ 0 | ≈ 0 |
| SSP2-4.5 | 28,6 °C | ≈ 0 | ≈ 0,02 % |
| SSP5-8.5 | 32,8 °C | 1,5 % | 7,7 % |

**Commentaire.** Dépasser 40 °C reste rare pour une année donnée, même en 2100 avec SSP5-8.5 (1,5 %). Sur 75 ans, le
risque s'accumule : dans ce scénario, environ 1 trajectoire sur 13 dépasse 40 °C au moins une fois. Avec 10 000
tirages, « 0 » veut seulement dire moins d'environ 1 chance sur 10 000, pas que c'est impossible.

Le deuxième tableau montre que ce chiffre dépend beaucoup du modèle : la médiane 2100 bouge peu (31,4 à 32,9 °C),
mais la probabilité de dépasser 40 °C va de 0,1 % (référence, qui ignore l'incertitude sur la pente) à 5,9 %
(quantiles). C'est logique : 40 °C est loin de tout ce qui a été observé (34,2 °C au maximum), donc le résultat dépend
surtout de la forme de la queue de la loi, que 86 années ne suffisent pas à bien connaître. Il faut aussi garder en
tête que le CO2 est la seule entrée du modèle (pas de circulation atmosphérique, ni d'océan) et qu'on extrapole
jusqu'à 946 ppm alors qu'on n'a observé que 310 à 428 ppm.
'''

C['minima'] = r'''
**Approche.** On reprend les mêmes modèles, mais la GEV, faite pour les maxima, est remplacée par le **bootstrap des
résidus** de Reda : on ajuste la droite sur un rééchantillonnage des années, puis on ajoute un résidu tiré parmi les
résidus observés, sans supposer de loi.

**Commentaire.** Le minimum annuel est encore moins lié au CO2 que le maximum ($r=0{,}15$) : il dépend surtout de
quelques vagues de froid (−6,6 °C en 1987). En validation, la référence, Bayes et le bootstrap des résidus sont à
moins de 0,01 °C les uns des autres, donc on garde la **référence**, le plus simple. Sur le test, c'est cette fois Bayes
qui fait le mieux (0,98 °C contre 1,14 °C) : la validation ne pouvait pas le voir, les écarts sur 1971-2000 étaient trop
petits.

Les minima remontent avec le CO2 : la médiane 2100 vaut −0,4 °C (SSP1-2.6), 0,4 °C (SSP2-4.5) et 2,2 °C (SSP5-8.5).
La probabilité que le minimum de 2100 soit sous 0 °C passe de 59 % à 13 %. Il gèlera encore au moins une fois d'ici
2100 dans tous les scénarios (100 % des trajectoires), mais les hivers sans gel deviennent fréquents avec SSP5-8.5.
Les autres modèles donnent des résultats proches (médiane de 2,2 à 3,1 °C, P(< 0 °C) de 13 % à 28 % pour SSP5-8.5).
'''

C['conclusion'] = r'''
# Conclusion

- **Le passé.** Brest a un cycle saisonnier doux, typique d'un climat océanique. Les vagues de chaleur (au-dessus du
  quantile 90 % de la saison) sont devenues bien plus fréquentes depuis les années 1980, et la plus intense est celle
  de juillet 2022.
- **Le futur.** Le lien entre les extrêmes annuels et le CO2 est faible d'une année à l'autre, mais net sur la
  tendance. Parmi nos cinq modèles, la régression bayésienne est retenue pour les maxima : elle est la meilleure en
  validation et sur 2001-2025 (CRPS 1,57 °C contre 1,70 °C pour la référence). En 2100, la médiane du maximum annuel
  va de 26,5 °C (SSP1-2.6) à 32,8 °C (SSP5-8.5). Dépasser 40 °C reste rare une année donnée (1,5 % en 2100 avec
  SSP5-8.5), mais atteint 7,7 % sur l'ensemble 2026-2100 dans ce scénario. Pour les minima, le gel devient moins
  fréquent sans disparaître.
- **Limites.** 86 années, c'est peu pour connaître la queue de la loi : la probabilité de 40 °C en 2100 (SSP5-8.5)
  va de 0,1 % à 5,9 % selon le modèle. Le CO2 est notre seule variable explicative, et les scénarios nous font extrapoler bien au-delà
  des concentrations observées.
'''
