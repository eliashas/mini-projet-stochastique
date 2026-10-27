### Matrice de conformité au sujet original

| Source | Exigence | Cellules du rendu | Réponse vérifiée |
|---|---|---|---|
| Starter 0–5 | Membres, objectif et quatre axes | introduction | Attribution réelle, deux parties, transparence du test |
| Starter 8,12,20,26 | Imports et accès aux trois jeux | installation,imports | Installation explicite, ressources embarquées, unités et assertions |
| Starter 13–14 | q10/q50/q90 et lissage mensuel | p1-cycle,calcul-cycle | 365 mois/jours, fenêtre circulaire 31 jours, 29 février interpolé |
| Starter 15–16 | Durée et intensité des épisodes | p1-evenements,calcul-vagues | Suites maximales, chronologie réelle, intensité à q50, sensibilité 2/3 jours |
| Starter 17–18 | Diagramme durée/intensité coloré par année | calcul-vagues | Axes en jours/°C, couleur et interprétation |
| Starter 21–22 | Tmax annuel 1940–2025 | p2-historique,series-historiques | Série, lissage descriptif et commentaire physique |
| Starter 23–24 | Corrélation et transformations | correlations | Pearson, log/racine CO₂, lissages T, limites |
| Starter 25–27 | Prévisions probabilistes récentes, trois SSP, équations | denoiseur,code-denoiseur,code-entrainement,calcul-projections | PyTorch, mini-entraînement réel, D1/D3, lois annuelles 2026–2100 |
| Starter 28–29 | Distribution 2100 et P(>40°C) | distribution-probabilites,risque-cumule | Trois distributions, probabilités annuelles/cumulées, bornes MC |
| Starter 30–31 | Même étude pour Tmin | series-historiques,correlations,tableau-validation,calcul-projections,distribution-probabilites | Historique, corrélations, scores, projections et gel |
| Critère 1 | Qualité du code | calcul-cycle,calcul-vagues,code-scores,code-bayes,code-quantiles,code-gev,code-denoiseur | Fonctions courtes commentées ; matrice séparée |
| Critère 2 | Qualité des sorties et unités | tableau-validation,tableau-test,calcul-projections,distribution-probabilites | °C, ppm, jours, densité 1/°C et probabilités sans unité |
| Critère 3 | Méthode mathématique en LaTeX | metriques,modeles-statistiques,quantiles,gev,denoiseur,hybrides | Hypothèses, objectifs, génération et normalisation |
| Critère 4 | Discussion physique | donnees,correlations,incertitudes,discussion | Saisonnalité, causalité, inertie, sous-couverture et extrapolation |
| Mission équipe | CRPS/twCRPS, H0/H1, ancres et échecs | metriques,hybrides,ablation-hybrides,test-exploratoire,echecs,tableau-sensibilites | Résultats favorables/défavorables et méthodes complètes distingués |
| Mission équipe | Reproductibilité et séparation des phases | ressources,validation,controles-recalcules | Noyau propre, manifestes, assertions et kit original réexécuté |