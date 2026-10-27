# Ce que nous retenons pour le rendu commun

Nous avons réuni les quatre contributions disponibles en gardant leurs idées
propres. Elias apporte les modèles neuronaux et le protocole expérimental,
Christian l'incertitude bayésienne des paramètres, Reda la GEV non stationnaire
et une analyse descriptive complète, Yazid la régression quantile. Les erreurs
de calendrier, d'échantillon et de sélection sont corrigées dans l'intégration ;
les sources originales et les résultats défavorables sont conservés.

La première partie décrit 421 épisodes d'au moins trois jours au-dessus du
q90 saisonnier lissé, ou 798 avec deux jours. L'intensité moyenne est de
3,587 °C au-dessus de la médiane saisonnière et la durée maximale de 14 jours.
La climatologie a 365 jours ; le 29 février reste dans la chronologie des
épisodes avec un seuil interpolé. Cette définition relative détecte aussi des
épisodes doux hors été. Une fréquence par année permet de comparer la période
2020–2025, qui ne contient que six ans, aux décennies complètes.

La validation chronologique retient D3 pour les maxima et D1 pour les minima.
Le kit original accepte leurs tirages et donne 1,649991 °C et 1,036056 °C de
CRPS sur 2001–2025. Bayes obtient le meilleur CRPS Tmax observé après test,
1,580191 °C, mais ne remplace pas le choix de validation. D3 est légèrement
meilleur en twCRPS Tmax sur ce test : le classement dépend de la région de la
distribution évaluée. Les intervalles d'écart de score restent larges avec
25 années ; nous ne présentons pas une petite différence comme une certitude.

Les expériences Bayes–débruiteur ne donnent pas un gain général. H0 préfère un
poids bayésien nul sur validation, pour les deux variables. H1, qui remplace
l'innovation normale de Bayes par une forme neuronale recentrée/réduite,
n'améliore pas les meilleurs modèles de validation. Ce montage est modulaire :
le posterior initial reste calculé sous vraisemblance normale. La comparaison
log(CO₂)/CO₂ avec bruit gaussien identique ne justifie pas de changer la tendance
après lecture du test. Le DDPM classique est éliminé pour ses minima extrêmes ;
les QR peu pénalisées et le bootstrap Tmin libre de Reda ont aussi des échecs
de cohérence, qui restent visibles.

Après ajustement distinct sur 1940–2025, D3 projette sous SSP5-8.5 une médiane
Tmax de 32,546 °C en 2100, avec intervalle central 90 % [26,704 ; 39,017] °C.
La proportion de membres dépassant 40 °C vaut 3,01 % cette année-là. La part
des trajectoires ayant au moins un dépassement entre 2026 et 2100 vaut 17,26 %,
avec paramètres partagés et innovations annuelles conditionnellement indépendantes.
Sous les scénarios plus bas, zéro dépassement sur 10 000 membres en 2100 ne
signifie pas un risque physique nul. Les minima D1 deviennent plus doux,
mais la probabilité simulée de passer sous 0 °C reste de 16,66 % en 2100
sous SSP5-8.5, pour la variable fournie.

Les autres méthodes montrent une sensibilité importante : sous SSP5-8.5, la
probabilité annuelle de 40 °C va d'environ 0,65 % avec D1 ou GEV à 17,42 %
avec l'ancre linéaire en CO₂. Cet écart est beaucoup plus important que le
bruit de simulation. Le CO₂ seul, les formes de queues, la stabilité des
résidus et l'absence de mémoire océanique limitent les projections. La série
fournie ne se confond pas avec les observations d'une station.

**Le test historique avait déjà été consulté** : les expériences complémentaires
sont exploratoires. Nous séparons les validations, le test et le réajustement
complet, mais cette discipline ne rend pas le test neuf. Le notebook unique
embarque réellement ses ressources. Il a été exécuté, sorties initiales
effacées, dans un environnement virtuel neuf et un dossier vide. Le mode
réentraînement est fourni séparément du mode rapide, avec code essentiel
visible, équations et interprétations en français.

Le réentraînement intégral a ensuite été exécuté jusqu'au bout (90 réseaux,
41,2 min sur GTX 1660 Ti) et retrouve exactement les résultats remis.
Le contrôle des 75 années réajustées révèle un membre GEV à 50,901 °C sous
SSP5-8.5 ; il reste dans les résultats et souligne que la borne GEV n'est
pas une borne physique à 50 °C. Aucun membre D3/D1 retenu ne sort des bornes
dans les ensembles complets vérifiés.
