# Projet final : réentraînement et projections 2026–2100


Ce rapport est généré à partir des artefacts présents. Un résultat absent n'est pas considéré exécuté.

Candidat verrouillé : **Tmax C0_direct_crps / Tmin D1_ddm_crps**, **admissible**. CRPS test : **1.748986 °C** pour Tmax, **1.031040 °C** pour Tmin. Cette paire reste celle choisie avant lecture du test.

Sur 11 exports préenregistrés, **10 sont admissibles**. Les ablations ne remplacent pas le candidat après lecture du test.

La référence R0 exacte obtient **1.698885 / 1.064129 °C** (Tmax/Tmin). Elle gagne face au participant pour Tmax ; le participant améliore Tmin. La diffusion n'apporte donc pas un gain global garanti.

**DDPM D0 est éliminé** : 19152 valeurs de Tmin sortent de [−30,20] °C ; le minimum simulé atteint **-1933.216 °C**. Son CRPS Tmin brut est **2.619998 °C** et le kit retourne None. Un bon score de validation ne rend donc pas cette configuration admissible.

Détails : [diagnostic_echec_ddpm.md](diagnostic_echec_ddpm.md), fondé sur le NPZ et les checkpoints figés.

Après réentraînement 1940–2025, les fréquences simulées **Tmax > 40 °C en 2100** sont : ssp1-2.6 : **0/10000 = 0.000 %**; ssp2-4.5 : **2/10000 = 0.020 %**; ssp5-8.5 : **29/10000 = 0.290 %**. Elles sont conditionnelles au modèle et ne valident pas la queue physique.

L'étude descriptive 1940–2025 détecte **421 événements d'au moins 3 jours** (798 avec 2 jours), avec une durée maximale de **14 jours**.


Le participant présente les diagnostics suivants :

| variable | bias | coverage80 | width80 | brier |
| --- | --- | --- | --- | --- |
| max | -1.4109 | 0.64 | 5.01962 | 0.346021 |
| min | -0.785235 | 0.84 | 5.67908 | 0.121736 |


Le biais négatif et la couverture 80 % de 64 % des maxima (16/25 ans) montrent des chaleurs sous-estimées et une sous-couverture sur ce test. Les minima ont une couverture de 84 % (21/25) et conservent un biais froid malgré le gain de CRPS face à R0. Ces fréquences restent imprécises avec 25 années.


Les CRPS, twCRPS, biais et largeurs sont en °C ; couvertures, Brier et probabilités sont sans unité.


## Coûts réellement mesurés des entraînements


| variable | model_id | fold | seed | steps | best_step | training_seconds | gpu_memory_allocated_peak_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max | C0_direct_crps | final | 0 | 2750 | 2750 | 24.1203 | 19298304 |
| max | C0_direct_crps | final | 1 | 2750 | 2750 | 23.2055 | 19298304 |
| max | C0_direct_crps | final | 2 | 2750 | 2750 | 21.9636 | 19298304 |
| min | D1_ddm_crps | final | 0 | 1500 | 1500 | 13.6103 | 19298304 |
| min | D1_ddm_crps | final | 1 | 1500 | 1500 | 13.6311 | 19298304 |
| min | D1_ddm_crps | final | 2 | 1500 | 1500 | 12.06 | 19298304 |


Source complète : [run_costs.csv](../artifacts/full_project/run_costs.csv).


## Paramètres ajustés, support GEV et réutilisation des checkpoints


| variable | model | b_C_per_logppm | b_OLS_C_per_logppm | sigma_C | tail_lambda | neural_parent_reused |
| --- | --- | --- | --- | --- | --- | --- |
| max | C0_direct_crps | 7.40579 | 7.40579 | 2.18688 | 0 | False |
| min | D1_ddm_crps | 3.0088 | 3.0088 | 1.91011 | 0 | False |


Source complète : [fitted_models_summary.csv](../artifacts/full_project/fitted_models_summary.csv).


## Lois résiduelles : quantiles et dispersion des tirages de diagnostic


| variable | model | mean_C | std_C | minimum_C | q50_C | maximum_C | fraction_outside_central_window |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max | C0_direct_crps | 0.0343687 | 2.20411 | -5.59279 | -0.259497 | 11.5922 | 0.0017 |
| min | D1_ddm_crps | -0.00606405 | 2.23889 | -8.77629 | 0.171072 | 5.99319 | 0.0237 |


Source complète : [residual_law_diagnostics.csv](../artifacts/full_project/residual_law_diagnostics.csv).


## Projections : distributions annuelles


| variable | scenario | year | co2 | q05 | q50 | q95 | event_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max | ssp1-2.6 | 2026 | 420.78 | 23.7658 | 26.6304 | 30.9581 | 0.2916 |
| max | ssp1-2.6 | 2027 | 421.559 | 23.7795 | 26.6441 | 30.9718 | 0.2944 |
| max | ssp1-2.6 | 2028 | 422.333 | 23.7931 | 26.6577 | 30.9854 | 0.2966 |
| max | ssp1-2.6 | 2029 | 423.103 | 23.8066 | 26.6712 | 30.9989 | 0.2984 |
| max | ssp1-2.6 | 2030 | 423.864 | 23.8199 | 26.6845 | 31.0122 | 0.3002 |
| max | ssp1-2.6 | 2031 | 424.617 | 23.8331 | 26.6976 | 31.0253 | 0.3016 |
| max | ssp1-2.6 | 2032 | 425.359 | 23.846 | 26.7106 | 31.0383 | 0.3035 |
| max | ssp1-2.6 | 2033 | 426.088 | 23.8587 | 26.7232 | 31.051 | 0.305 |
| max | ssp1-2.6 | 2034 | 426.803 | 23.8711 | 26.7357 | 31.0634 | 0.3066 |
| max | ssp1-2.6 | 2035 | 427.502 | 23.8832 | 26.7478 | 31.0755 | 0.3085 |
| max | ssp1-2.6 | 2036 | 428.183 | 23.895 | 26.7596 | 31.0873 | 0.3098 |
| max | ssp1-2.6 | 2037 | 428.844 | 23.9064 | 26.771 | 31.0987 | 0.3118 |
| max | ssp1-2.6 | 2038 | 429.484 | 23.9175 | 26.782 | 31.1097 | 0.3133 |
| max | ssp1-2.6 | 2039 | 430.101 | 23.9281 | 26.7927 | 31.1204 | 0.3146 |
| max | ssp1-2.6 | 2040 | 430.695 | 23.9383 | 26.8029 | 31.1306 | 0.3161 |
| max | ssp1-2.6 | 2041 | 431.262 | 23.9481 | 26.8126 | 31.1403 | 0.3174 |
| max | ssp1-2.6 | 2042 | 431.802 | 23.9573 | 26.8219 | 31.1496 | 0.3184 |
| max | ssp1-2.6 | 2043 | 432.314 | 23.9661 | 26.8307 | 31.1584 | 0.3198 |
| max | ssp1-2.6 | 2044 | 432.795 | 23.9743 | 26.8389 | 31.1666 | 0.3209 |
| max | ssp1-2.6 | 2045 | 433.245 | 23.982 | 26.8466 | 31.1743 | 0.3221 |
| max | ssp1-2.6 | 2046 | 433.663 | 23.9892 | 26.8537 | 31.1815 | 0.3237 |
| max | ssp1-2.6 | 2047 | 434.047 | 23.9957 | 26.8603 | 31.188 | 0.3245 |
| max | ssp1-2.6 | 2048 | 434.395 | 24.0017 | 26.8662 | 31.194 | 0.3253 |
| max | ssp1-2.6 | 2049 | 434.708 | 24.007 | 26.8716 | 31.1993 | 0.3261 |
| max | ssp1-2.6 | 2050 | 434.984 | 24.0117 | 26.8763 | 31.204 | 0.3266 |
| max | ssp1-2.6 | 2051 | 435.222 | 24.0157 | 26.8803 | 31.208 | 0.327 |
| max | ssp1-2.6 | 2052 | 435.421 | 24.0191 | 26.8837 | 31.2114 | 0.3276 |
| max | ssp1-2.6 | 2053 | 435.58 | 24.0218 | 26.8864 | 31.2141 | 0.3278 |
| max | ssp1-2.6 | 2054 | 435.699 | 24.0239 | 26.8884 | 31.2161 | 0.3282 |
| max | ssp1-2.6 | 2055 | 435.776 | 24.0252 | 26.8897 | 31.2175 | 0.3282 |
| max | ssp1-2.6 | 2056 | 435.812 | 24.0258 | 26.8904 | 31.2181 | 0.3282 |
| max | ssp1-2.6 | 2057 | 435.806 | 24.0257 | 26.8903 | 31.218 | 0.3282 |
| max | ssp1-2.6 | 2058 | 435.757 | 24.0248 | 26.8894 | 31.2171 | 0.3282 |
| max | ssp1-2.6 | 2059 | 435.665 | 24.0233 | 26.8879 | 31.2156 | 0.3281 |
| max | ssp1-2.6 | 2060 | 435.53 | 24.021 | 26.8856 | 31.2133 | 0.3278 |
| max | ssp1-2.6 | 2061 | 435.351 | 24.0179 | 26.8825 | 31.2102 | 0.3275 |
| max | ssp1-2.6 | 2062 | 435.128 | 24.0141 | 26.8787 | 31.2064 | 0.3269 |
| max | ssp1-2.6 | 2063 | 434.861 | 24.0096 | 26.8742 | 31.2019 | 0.3263 |
| max | ssp1-2.6 | 2064 | 434.551 | 24.0043 | 26.8689 | 31.1966 | 0.3257 |
| max | ssp1-2.6 | 2065 | 434.196 | 23.9983 | 26.8628 | 31.1906 | 0.3248 |

450 lignes au total ; le CSV conserve toutes les lignes.


Source complète : [projection_summary.csv](../artifacts/full_project/projection_summary.csv).


## Dépassement de 40 °C : simulations et précision


| scenario | k | n | probability | ci_lower | ci_upper | resolution |
| --- | --- | --- | --- | --- | --- | --- |
| ssp1-2.6 | 0 | 10000 | 0 | 0 | 0.00036882 | 0.0001 |
| ssp2-4.5 | 2 | 10000 | 0.0002 | 2.42218e-05 | 0.00072228 | 0.0001 |
| ssp5-8.5 | 29 | 10000 | 0.0029 | 0.00194301 | 0.00416225 | 0.0001 |


Source complète : [probability_40.csv](../artifacts/full_project/probability_40.csv).


## Dépassement durant 2026–2100 : hypothèse temporelle


| scenario | k | n | probability | ci_lower | ci_upper |
| --- | --- | --- | --- | --- | --- |
| ssp1-2.6 | 0 | 10000 | 0 | 0 | 0.00036882 |
| ssp2-4.5 | 2 | 10000 | 0.0002 | 2.42218e-05 | 0.00072228 |
| ssp5-8.5 | 455 | 10000 | 0.0455 | 0.0414984 | 0.0497689 |


Source complète : [trajectory_probability_40.csv](../artifacts/full_project/trajectory_probability_40.csv).


## Sélection verrouillée


```json
{
  "selected_models": {
    "max": "C0_direct_crps",
    "min": "D1_ddm_crps"
  },
  "selected_tail_lambda": {
    "max": 0.5,
    "min": 0.5
  },
  "final_steps": {
    "max": {
      "C0_direct_crps": 2750,
      "D0_ddpm": 2750,
      "D1_ddm_crps": 1250,
      "D2_ddm_tail_lambda0.5": 750,
      "D2_ddm_tail_lambda1": 750,
      "D2_ddm_tail_lambda2": 750
    },
    "min": {
      "C0_direct_crps": 2500,
      "D0_ddpm": 1250,
      "D1_ddm_crps": 1500,
      "D2_ddm_tail_lambda0.5": 1250,
      "D2_ddm_tail_lambda1": 1000,
      "D2_ddm_tail_lambda2": 1000
    }
  }
}
```


Classements et règles complets : [selection.json](../artifacts/competition/selection.json).


## Transition historique 2025 / scénarios 2026


```json
{
  "historical_2025_co2": 428.5017353613867,
  "scenario_2026_co2": {
    "ssp1-2.6": 420.78022467656336,
    "ssp2-4.5": 420.18854219474224,
    "ssp5-8.5": 421.1216772259265
  },
  "difference_ppm": {
    "ssp1-2.6": -7.721510684823329,
    "ssp2-4.5": -8.313193166644453,
    "ssp5-8.5": -7.380058135460217
  },
  "scenario_2100_co2": {
    "ssp1-2.6": 400.0,
    "ssp2-4.5": 526.9873843407519,
    "ssp5-8.5": 946.2221518449436
  },
  "trajectories_changed": false,
  "interpretation": "CO₂ fourni de tendance, non une observation causale locale complète; rupture conservée telle quelle."
}
```


Les trajectoires CO₂ sont utilisées telles que fournies ; toute rupture apparaît ici sans correction silencieuse.


## Probabilités marginales en 2100 : seuils historiques de la phase finale


Ces probabilités utilisent Tmax > q80 ou Tmin < q20 de l'historique **1940–2025**, avec les seuils déjà ajustés dans fit_full.json. Elles sont calculées sur les mêmes ensembles annuels stockés, sans nouvelle simulation. Ce sont des événements distincts de Tmax > 40 °C. Les seuils descriptifs de la phase finale diffèrent des seuils propres aux trains des folds et du seuil de test 1940–2000 ; leurs probabilités ne remplacent pas les scores de validation ou de test.

| variable | model | scenario | event_threshold_C | event_probability | event_definition | n |
| --- | --- | --- | --- | --- | --- | --- |
| max | C0_direct_crps | ssp1-2.6 | 27.8844 | 0.2439 | Tmax > quantile 80% historique 1940–2025 | 10000 |
| max | C0_direct_crps | ssp2-4.5 | 27.8844 | 0.578 | Tmax > quantile 80% historique 1940–2025 | 10000 |
| max | C0_direct_crps | ssp5-8.5 | 27.8844 | 0.9991 | Tmax > quantile 80% historique 1940–2025 | 10000 |
| min | D1_ddm_crps | ssp1-2.6 | -1.8588 | 0.2501 | Tmin < quantile 20% historique 1940–2025 | 10000 |
| min | D1_ddm_crps | ssp2-4.5 | -1.8588 | 0.1594 | Tmin < quantile 20% historique 1940–2025 | 10000 |
| min | D1_ddm_crps | ssp5-8.5 | -1.8588 | 0.0502 | Tmin < quantile 20% historique 1940–2025 | 10000 |


Le CSV `artifacts/full_project/projection_summary.csv` conserve ces probabilités pour chacune des années 2026–2100.


Les ajustements finaux utilisent 1940–2025, après le benchmark verrouillé. Leurs prédictions 2001–2025 ne constituent donc pas un score hors échantillon. Les SSP sont les covariables CO₂ fournies ; ils ne constituent pas des observations de température.


Pour 40 °C, k/N est une estimation conditionnelle au modèle ajusté. Une absence de dépassement simulé n'est pas une probabilité physique nulle. Un intervalle binomial exige un tirage indépendant de l'indice de réseau pour chaque simulation ; les quotas fixes du benchmark sont stratifiés.


## Analyse annuelle descriptive


```json
{
  "phase": "full_project",
  "years_start": 1940,
  "years_end": 2025,
  "n_years": 86,
  "anchor": {
    "max": {
      "a": -17.90458623186814,
      "b": 7.405790925722071,
      "b_raw": 7.405790925722071,
      "sigma": 2.18688131320709,
      "sigma_raw": 2.18688131320709,
      "scale_floor_active": false,
      "n": 86,
      "log_co2_center": 5.895713966151757,
      "constraint_active": false
    },
    "min": {
      "a": -18.450285112377134,
      "b": 3.008799785977186,
      "b_raw": 3.008799785977186,
      "sigma": 1.9101088092391612,
      "sigma_raw": 1.9101088092391612,
      "scale_floor_active": false,
      "n": 86,
      "log_co2_center": 5.895713966151757,
      "constraint_active": false
    }
  },
  "interpretation": "descriptive fitted in supplied period; not validation predictions"
}
```

Ancre Tmax : pente OLS **7.405791 °C par unité de log(CO₂)**, pente retenue **7.405791**, σ résiduel **2.186881 °C**. La contrainte de pente positive n'est pas active sur cette période.

Ancre Tmin : pente OLS **3.008800 °C par unité de log(CO₂)**, pente retenue **3.008800**, σ résiduel **1.910109 °C**. La contrainte de pente positive n'est pas active sur cette période.


## Vagues de chaleur


```json
{
  "phase": "full_project",
  "reference_start": "1940-01-01",
  "reference_end": "2025-12-31",
  "daily_rows": 31412,
  "missing_dates": 0,
  "feb29_days": 22,
  "climatology_days": 365,
  "smoothing_window_days": 31,
  "events_min3": 421,
  "events_min2": 798,
  "maximum_duration_min3_days": 14,
  "mean_intensity_min3_C": 3.587129639474805,
  "mean_excess_q90_min3_C": 1.1839315092731477,
  "units": "°C; duration in days",
  "event_definition": "maximal consecutive runs mean > smoothed q90",
  "intensity_definition": "event mean(mean temperature - smoothed q50)",
  "excess_definition": "event mean(mean temperature - smoothed q90)",
  "feb29_rule": "excluded from quantiles; thresholds interpolate February 28 / March 1",
  "interpretation": "descriptive climatology over supplied reference period; not out-of-sample prediction"
}
```

Sur 1940-01-01–2025-12-31, le seuil saisonnier détecte **421 événements** d'au moins trois jours, contre **798** avec deux jours. La durée maximale est **14 jours**. L'intensité moyenne des événements est **3.587 °C** au-dessus de q50 lissé ; l'excès moyen à q90 est **1.184 °C**. Chaque événement a le même poids dans ces moyennes. Un seuil relatif saisonnier peut détecter des épisodes doux en hiver ; ce ne sont pas exclusivement des canicules estivales à seuil sanitaire.


## Corrélations descriptives : CO₂ brut et log(CO₂)


| phase | variable | transformation | n | pearson_r | p_descriptive |
| --- | --- | --- | --- | --- | --- |
| full_project | max | CO2 | 86 | 0.314326 | 0.00320482 |
| full_project | max | log(CO2) | 86 | 0.303713 | 0.00447209 |
| full_project | min | CO2 | 86 | 0.150344 | 0.167063 |
| full_project | min | log(CO2) | 86 | 0.146671 | 0.177796 |


Ces corrélations ne démontrent ni causalité complète ni qualité d'extrapolation. Les p-values descriptives supposent des observations indépendantes et ne corrigent pas l'autocorrélation temporelle.


## Résidus : quantiles, asymétrie et dépendance temporelle descriptive


| variable | n | skewness | autocorrelation_lag1 | autocorrelation_lag2 | autocorrelation_lag3 | q05_C | q50_C | q95_C |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| max | 86 | 0.585127 | 0.15269 | 0.115651 | 0.000495529 | -3.05922 | -0.443665 | 3.502 |
| min | 86 | -0.817345 | 0.0935734 | -0.0122668 | -0.173522 | -3.63823 | 0.19037 | 2.65257 |

Tmax (86 années) : asymétrie descriptive **+0.585**, quantiles q05/q50/q95 **-3.059 / -0.444 / 3.502 °C**, autocorrélations aux retards 1/2/3 ans **+0.153 / +0.116 / +0.000**. L'asymétrie positive décrit une queue empirique plus étendue vers les résidus chauds.

Tmin (86 années) : asymétrie descriptive **-0.817**, quantiles q05/q50/q95 **-3.638 / 0.190 / 2.653 °C**, autocorrélations aux retards 1/2/3 ans **+0.094 / -0.012 / -0.174**. L'asymétrie négative décrit une queue empirique plus étendue vers les résidus froids.

Ces valeurs concernent les résidus de l'ancre ajustée sur la période descriptive indiquée, et non des erreurs de validation calculées avec une ancre commune à tous les folds. Les autocorrélations décrivent une dépendance locale possible ; avec peu d'années, elles ne certifient ni indépendance, ni stationnarité, ni validité d'une queue GEV. Le bootstrap principal en blocs de trois ans conserve une partie de cette dépendance possible ; la comparaison avec des blocs d'un an est une sensibilité fixée avant le test.


Source : `artifacts/full_project/annual_analysis/residual_descriptive.csv`.


## Sensibilité du bootstrap : blocs de 1 an contre blocs de 3 ans


Cette comparaison utilise uniquement les validations F1/F2/F3, avec les mêmes réseaux résiduels, seuils et observations. Chaque ligne conserve le modèle et son λ ; les variantes à λ différents ne sont pas agrégées ensemble. Les ensembles ont 10 000 membres. Un delta négatif favorise les blocs d'un an. Les blocs de trois ans restent le protocole principal fixé ; ces résultats ne déclenchent aucun choix sur le test.

| variable | model | tail_lambda | folds | delta_crps_block1_minus3_C | delta_twcrps_block1_minus3_C | folds_global_block1_better | folds_tail_block1_better |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max | D3_ddm_anchor | 0 | 3 | 0.00475858 | 0.00169312 | 1 | 1 |
| max | D4_ddm_tail_anchor_lambda0.5 | 0.5 | 3 | 0.0046677 | 0.00162602 | 1 | 1 |
| max | D4_ddm_tail_anchor_lambda1 | 1 | 3 | 0.00447591 | 0.00162717 | 1 | 1 |
| max | D4_ddm_tail_anchor_lambda2 | 2 | 3 | 0.00462479 | 0.0018813 | 1 | 1 |
| min | D3_ddm_anchor | 0 | 3 | -0.00811013 | 1.67277e-05 | 2 | 1 |
| min | D4_ddm_tail_anchor_lambda0.5 | 0.5 | 3 | -0.00979821 | -0.000127217 | 2 | 1 |
| min | D4_ddm_tail_anchor_lambda1 | 1 | 3 | -0.00992328 | -0.000213655 | 2 | 1 |
| min | D4_ddm_tail_anchor_lambda2 | 2 | 3 | -0.0100708 | 5.15374e-05 | 2 | 1 |

| variable | model | fold | tail_lambda | delta_crps_block1_minus3_C | delta_twcrps_block1_minus3_C |
| --- | --- | --- | --- | --- | --- |
| max | D3_ddm_anchor | F1 | 0 | -0.00165267 | -4.06288e-05 |
| max | D4_ddm_tail_anchor_lambda0.5 | F1 | 0.5 | -0.00173452 | -0.000120282 |
| max | D4_ddm_tail_anchor_lambda1 | F1 | 1 | -0.00245643 | -0.000130211 |
| max | D4_ddm_tail_anchor_lambda2 | F1 | 2 | -0.00260829 | -0.00021571 |
| max | D3_ddm_anchor | F2 | 0 | 0.00605246 | 0.00410812 |
| max | D4_ddm_tail_anchor_lambda0.5 | F2 | 0.5 | 0.00592645 | 0.00397251 |
| max | D4_ddm_tail_anchor_lambda1 | F2 | 1 | 0.00609533 | 0.00397286 |
| max | D4_ddm_tail_anchor_lambda2 | F2 | 2 | 0.00761767 | 0.00463832 |
| max | D3_ddm_anchor | F3 | 0 | 0.00987597 | 0.00101186 |
| max | D4_ddm_tail_anchor_lambda0.5 | F3 | 0.5 | 0.00981116 | 0.00102583 |
| max | D4_ddm_tail_anchor_lambda1 | F3 | 1 | 0.00978881 | 0.00103885 |
| max | D4_ddm_tail_anchor_lambda2 | F3 | 2 | 0.00886498 | 0.0012213 |
| min | D3_ddm_anchor | F1 | 0 | 0.00664949 | 0.000214826 |
| min | D4_ddm_tail_anchor_lambda0.5 | F1 | 0.5 | 0.00649329 | 0.000244131 |
| min | D4_ddm_tail_anchor_lambda1 | F1 | 1 | 0.00639362 | 0.000268719 |
| min | D4_ddm_tail_anchor_lambda2 | F1 | 2 | 0.00533466 | 0.000607413 |
| min | D3_ddm_anchor | F2 | 0 | -0.000579548 | 0.000810949 |
| min | D4_ddm_tail_anchor_lambda0.5 | F2 | 0.5 | -0.000413936 | 0.00115434 |
| min | D4_ddm_tail_anchor_lambda1 | F2 | 1 | -0.000817694 | 0.000804045 |
| min | D4_ddm_tail_anchor_lambda2 | F2 | 2 | -0.000745297 | 0.000885238 |
| min | D3_ddm_anchor | F3 | 0 | -0.0304003 | -0.000975591 |
| min | D4_ddm_tail_anchor_lambda0.5 | F3 | 0.5 | -0.035474 | -0.00178012 |
| min | D4_ddm_tail_anchor_lambda1 | F3 | 1 | -0.0353458 | -0.00171373 |
| min | D4_ddm_tail_anchor_lambda2 | F3 | 2 | -0.0348017 | -0.00133804 |


Les moyennes agrègent les folds disponibles, chacun ayant 10 années. Le nombre de folds et d'années est indiqué ; il ne faut pas présenter une ligne partielle comme trois folds terminés. La différence mesure une sensibilité descriptive à la dépendance supposée des résidus, avec 500 ancres et une loi neuronale fixe, plutôt qu'une validation complète de cette hypothèse.


Sources : `artifacts/competition/bootstrap_block_sensitivity_summary.csv` et `artifacts/competition/bootstrap_block_sensitivity_by_fold.csv` ; les sources JSON par fold figurent dans la dernière colonne.


## Apport des modèles : résultats de validation


Pour Tmax, le CRPS de validation le plus faible est celui de D0_ddpm (1.097160 °C). Ce classement provient des folds, avant le test.

Les modèles à moins de 0,05 °C de ce score sont : D0_ddpm, D3_ddm_anchor, D4_ddm_tail_anchor_lambda0.5, D4_ddm_tail_anchor_lambda1, D1_ddm_crps, D2_ddm_tail_lambda0.5, D2_ddm_tail_lambda1, D4_ddm_tail_anchor_lambda2, D2_ddm_tail_lambda2, C0_direct_crps. La règle de simplicité/cout du manifeste détermine la sélection parmi les scores proches.

La variante neuronale au meilleur CRPS de validation est **D0_ddpm** (1.097160 °C), soit un écart de **+0.000000 °C** par rapport au meilleur score de toutes les familles. Sa méthode reste décrite dans le notebook La règle de complexité fixée s'applique aux scores proches, quelle que soit la famille retenue.

| variable | comparison | common_folds | delta_crps_C | folds_D1_better |
| --- | --- | --- | --- | --- |
| max | D1 − R1_gev | 3 | -0.0554544 | 3 |
| max | D1 − R2_empirical | 3 | -0.0418505 | 2 |
| max | D1 − C0_direct_crps | 3 | -0.0218777 | 1 |

Pour Tmin, le CRPS de validation le plus faible est celui de D0_ddpm (1.143005 °C). Ce classement provient des folds, avant le test.

Les modèles à moins de 0,05 °C de ce score sont : D0_ddpm, D1_ddm_crps, D3_ddm_anchor, D2_ddm_tail_lambda0.5, D2_ddm_tail_lambda1, D4_ddm_tail_anchor_lambda0.5, D2_ddm_tail_lambda2, D4_ddm_tail_anchor_lambda1. La règle de simplicité/cout du manifeste détermine la sélection parmi les scores proches.

La variante neuronale au meilleur CRPS de validation est **D0_ddpm** (1.143005 °C), soit un écart de **+0.000000 °C** par rapport au meilleur score de toutes les familles. Sa méthode reste décrite dans le notebook La règle de complexité fixée s'applique aux scores proches, quelle que soit la famille retenue.

| variable | comparison | common_folds | delta_crps_C | folds_D1_better |
| --- | --- | --- | --- | --- |
| min | D1 − R1_gev | 3 | -0.0666979 | 3 |
| min | D1 − R2_empirical | 3 | -0.0816254 | 3 |
| min | D1 − C0_direct_crps | 3 | -0.0339465 | 3 |

Un delta négatif favorise D1. Les scores par fold, par graine et les twCRPS permettent d'évaluer la constance et le coût d'une amélioration ; un gain moyen isolé ne démontre pas une amélioration des queues. Les variantes D3/D4 réutilisent les mêmes réseaux et isolent l'ajout de dispersion par l'ancre.


Comparaisons ciblées : un delta négatif favorise le premier modèle. Les λ de D2/D4 sont ceux fixés par validation pour la variable. La dispersion donnée est celle des deltas moyens par graine (écart-type descriptif ddof=0), distincte de la performance du mélange.

| variable | comparison | selected_tail_lambda | delta_crps_C | delta_twcrps_C | folds_global_improved | folds_tail_improved | seed_delta_crps_std_C |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max | D2_ddm_tail − D1_ddm_crps | 0.5 | 0.00121798 | -0.000601963 | 1 | 2 | 0.00131948 |
| max | D3_ddm_anchor − D1_ddm_crps | — | -0.00945606 | -0.00820297 | 1 | 2 | 0.00286166 |
| max | D4_ddm_tail_anchor − D2_ddm_tail | 0.5 | -0.00997945 | -0.00812951 | 1 | 2 | 0.00283448 |
| max | D1_ddm_crps − R1_gev | — | -0.0554544 | -0.0344957 | 3 | 3 | 0.00994667 |
| max | D1_ddm_crps − R2_empirical | — | -0.0418505 | -0.0228128 | 2 | 3 | 0.00994667 |
| max | D1_ddm_crps − C0_direct_crps | — | -0.0218777 | -0.0168432 | 1 | 2 | 0.00792872 |
| max | D0_ddpm − R0_gaussian | — | -0.0798202 | -0.0279997 | 3 | 3 | 0.0140214 |
| max | D0_ddpm − R1_gev | — | -0.0786808 | -0.0317648 | 3 | 3 | 0.0140214 |
| max | D0_ddpm − R2_empirical | — | -0.0650769 | -0.0200818 | 2 | 2 | 0.0140214 |
| min | D2_ddm_tail − D1_ddm_crps | 0.5 | 0.0101177 | 0.00238413 | 0 | 0 | 0.00707747 |
| min | D3_ddm_anchor − D1_ddm_crps | — | 0.00628938 | -0.00221496 | 1 | 2 | 0.00723655 |
| min | D4_ddm_tail_anchor − D2_ddm_tail | 0.5 | 0.00946908 | -0.00194913 | 1 | 2 | 0.0079182 |
| min | D1_ddm_crps − R1_gev | — | -0.0666979 | -0.0155202 | 3 | 2 | 0.00415972 |
| min | D1_ddm_crps − R2_empirical | — | -0.0816254 | -0.0182706 | 3 | 3 | 0.00415972 |
| min | D1_ddm_crps − C0_direct_crps | — | -0.0339465 | -0.0080844 | 3 | 2 | 0.00638194 |
| min | D0_ddpm − R0_gaussian | — | -0.0780432 | -0.0268582 | 3 | 3 | 0.00849122 |
| min | D0_ddpm − R1_gev | — | -0.0906284 | -0.0232811 | 3 | 3 | 0.00849122 |
| min | D0_ddpm − R2_empirical | — | -0.105556 | -0.0260315 | 3 | 3 | 0.00849122 |


Comparaisons complètes : [ablation_comparisons.csv](../artifacts/competition/ablation_comparisons.csv).


## Méthodes et conventions mathématiques

L'ancre est ajustée séparément pour Tmax et Tmin : $Y=a+b\log(C)+R$, avec $b=\max(b_{OLS},0)$,
$a=\overline{Y-b\log(C)}$, $\sigma=\mathrm{sd}(R,ddof=2)$ et $Z=R/\sigma$. Le CO₂ est exprimé
en ppm et les résultats en °C. La contrainte traduit ici une hypothèse de tendance locale monotone.
Elle ne démontre pas une réponse physique universelle. La loi résiduelle est supposée stationnaire.

R0 utilise $R\sim\mathcal N(0,\sigma^2)$ ; R1 ajuste une GEV à R pour Tmax, à −R pour Tmin,
avec la convention SciPy $c=-\xi$. R2 rééchantillonne les résidus. Le support GEV et les échecs
d'admissibilité doivent être examinés même si le score moyen semble favorable.
La reproduction exacte R0_exact suit les quatre appels RNG originaux
(test_max, test_min, proj_max, proj_min) : ses résidus sont indépendants entre scénarios.
Les autres exports réutilisent les mêmes résidus et, lorsqu'elle varie, la même ancre entre scénarios.

Le DDPM D0 apprend le bruit dans $Z_k=\sqrt{\bar\alpha_k}Z+\sqrt{1-\bar\alpha_k}\epsilon$ par MSE,
avec 100 pas et un calendrier cosinus. Sa génération suit le processus ancestral inverse. D1 produit
$\hat Z_m=g_\phi(u,t,\zeta_m)$ avec $u=(1-t)Z+t\epsilon$. Dans un ensemble d'entraînement,
u et t sont communs, les latents $\zeta_m$ indépendants ; l'inférence utilise t=1, sans observation
future. C0 emploie le même générateur avec u=0, t=1, pour mesurer l'apport du débruitage auxiliaire.
Il s'agit d'une adaptation scalaire d'une méthode météorologique récente, et non d'une validation
de cette publication sur Brest.

Pour D0, $L_{MSE}=\mathbb E[(\epsilon-\epsilon_\phi(Z_k,k/K))^2]$. En génération :

$$
Z_{k-1}=\frac{1}{\sqrt{\alpha_k}}\left(Z_k-
\frac{\beta_k}{\sqrt{1-\bar\alpha_k}}\epsilon_\phi(Z_k,k/K)\right)
+\sqrt{\tilde\beta_k}\eta,\qquad
\tilde\beta_k=\beta_k\frac{1-\bar\alpha_{k-1}}{1-\bar\alpha_k}.
$$

Le dernier pas ne rajoute aucun bruit. Le calendrier cosinus utilise s=0,008, beta ≤ 0,999,
et son alpha_bar terminal est inférieur à 10⁻³. Les calendriers sont dans les checkpoints.

Le CRPS d'évaluation est $N^{-1}\sum_m|x_m-y|-(2N^2)^{-1}\sum_{m,n}|x_m-x_n|$,
calculé par tri en float64. L'apprentissage C0/D1/D2 utilise M=32 et
$afCRPS=0.95\,fCRPS+0.05\,CRPS_{emp}$, où le terme de dispersion fair a le dénominateur
$2M(M-1)$. Ce petit mélange est légèrement biaisé et diffère du score empirique officiel.
D2 ajoute $\lambda\,afCRPS(h(\hat Y),h(Y))$, avec la même convention
$afCRPS=0.95\,fCRPS+0.05\,CRPS_{emp}$ que le terme global, et
$h(x)=\max(x,s_{hot})$ pour Tmax et
$h(x)=\min(x,s_{cold})$ pour Tmin. Ces seuils sont les quantiles 0,80/0,20 du train.
Le twCRPS d'évaluation applique seulement cette transformation au calcul du score : aucun tirage
de température n'est écrêté. Toutes les années comptent, y compris les fausses alertes.

D3 et D4 réutilisent les réseaux de D1/D2 et ajoutent un bootstrap résiduel de l'ancre à CO₂ fixé
(500 réplications, blocs circulaires de 3 ans ; sensibilité longueur 1). L'échelle et la loi neuronale
restent fixes : cette approximation ne mesure pas toute l'incertitude des paramètres. Elle n'est pas
un posterior bayésien. Le même couple ancre/résidu est employé entre scénarios d'une année.

La contrainte $b\geq0$ peut aussi décaler la moyenne des ancres bootstrap vers le haut lors de
l'extrapolation. L'ajout n'agit donc pas seulement sur la largeur : le tableau de dispersion
rapporte également le décalage moyen par rapport à l'ancre ponctuelle. Un gain de CRPS ne
doit pas être attribué automatiquement à la seule représentation de l'incertitude.

Les intervalles sont centraux, à 50/80/90 %, avec couverture inclusive et largeur en °C.
Le PIT est $(\#\{x_m<y\}+0.5\#\{x_m=y\})/N$, un rang médian déterministe adapté aux égalités
de R2. Le Brier utilise les événements stricts Tmax>s ou Tmin<s. Le biais est la moyenne de
$E_F(Y)-y$, la MAE celle de la médiane. Un PIT de 25 points ne certifie pas une calibration.

## Portée physique et limites

Les températures moyennes journalières servent aux vagues de chaleur ; leurs maxima ne remplacent
pas les extrêmes horaires du fichier annuel. Les 61 puis 86 années restent le nombre d'observations
annuelles : le bruit d'entraînement et 10 000 simulations n'ajoutent aucune observation climatique.
Le CO₂ décrit une tendance mondiale et ne suffit pas à établir une causalité locale complète :
variabilité atmosphérique et océanique, autres forçages et état local ne sont pas explicitement modélisés.

Un bon CRPS sur 25 années évalue surtout la loi dans la région observée. Il ne valide pas la queue
à 40 °C, ni l'extrapolation jusqu'à un CO₂ très supérieur au domaine historique. Les paramètres GEV,
la stationnarité résiduelle et la forme log-linéaire sont fragiles avec ce petit échantillon. Les bornes
du kit et ses tests de monotonie/largeur sont des conventions du groupe, pas des lois physiques.

Il faut distinguer : erreur Monte-Carlo (nombre fini de simulations, conditionnel au modèle ajusté),
incertitude d'estimation (ancre et poids appris) et erreur de modèle (tendance, queue, dynamique).
Le bootstrap d'ancre ne traite que la première composante paramétrique de la tendance.
Une probabilité d'au moins un dépassement durant 2026–2100 exige une hypothèse de dépendance :
résidus indépendants conditionnellement à l'ancre, avec la même ancre conservée sur la trajectoire.
La formule $1-\prod_t(1-p_t)$ pour des marges n'est pas valide avec une ancre aléatoire partagée.



## Exécutions, adaptations et échecs


Le manifeste d'ajustement final ne signale aucun échec technique. Cela ne garantit ni l'admissibilité du benchmark ni la stabilité scientifique des extrapolations.

6 entrées de journal concernent cette phase et les contrôles préparatoires. Les reprises, adaptations, durées et erreurs sont conservées dans [execution_journal.jsonl](../artifacts/execution_journal.jsonl).


La durée `training_seconds` inclut les évaluations et les sauvegardes dans la boucle. `inference_seconds` est le temps de ces évaluations, déjà inclus ; leur somme serait un double comptage. Les temps de prédiction définitifs sont consignés dans les métadonnées de la phase.


Les lois résiduelles utilisent un zoom central dont l'histogramme est normalisé par le N total. La masse hors fenêtre figure dans chaque légende et le CSV. Le DDPM possède des panneaux de queue complète ; toutes les valeurs hors fenêtre sont conservées dans [residual_diagnostic_tail_values.csv](../artifacts/full_project/residual_diagnostic_tail_values.csv). Ces tirages de diagnostic ont leurs propres graines et ne sont pas les ensembles officiels.


## Figures exportées


![annual_correlations](../artifacts/full_project/annual_analysis/annual_correlations.png)

![annual_observations_anchor](../artifacts/full_project/annual_analysis/annual_observations_anchor.png)

![annual_residual_diagnostics](../artifacts/full_project/annual_analysis/annual_residual_diagnostics.png)

![heatwave_counts](../artifacts/full_project/heatwaves/heatwave_counts.png)

![heatwave_duration_intensity](../artifacts/full_project/heatwaves/heatwave_duration_intensity.png)

![heatwave_seasonal_cycle](../artifacts/full_project/heatwaves/heatwave_seasonal_cycle.png)

![projection_distributions_2100](figures/full_project/projection_distributions_2100.png)

![projection_probability_40_annual](figures/full_project/projection_probability_40_annual.png)

![projection_trajectories](figures/full_project/projection_trajectories.png)

![residual_laws_max](figures/full_project/residual_laws_max.png)

![residual_laws_min](figures/full_project/residual_laws_min.png)


## Références méthodologiques

- [DDPM](https://arxiv.org/abs/2006.11239) et [calendrier cosinus](https://arxiv.org/abs/2102.09672).
- [Diffusion et scores probabilistes météo, prépublication](https://arxiv.org/html/2609.38632v1) ; adaptation scalaire explicitée ci-dessus.
- [AIFS-CRPS](https://arxiv.org/html/2412.15832v1) et [estimateurs CRPS](https://scoringrules.readthedocs.io/en/latest/crps_estimators.html).
- [Scores pondérés](https://scoringrules.readthedocs.io/en/latest/weighted_scores.html).
- [GEV et covariable CO₂](https://ascmo.copernicus.org/articles/9/45/2023/).
- [Validation chronologique](https://otexts.com/fpp3/tscv.html).

Ces références méthodologiques ne fournissent aucune observation supplémentaire au modèle.

La provenance exacte des CSV n'est pas certifiée par leurs métadonnées. La documentation ECMWF
décrit [ERA5 HRES à environ 31 km](https://confluence.ecmwf.int/pages/viewpage.action?navigatingVersions=true&pageId=78296807)
et [ERA5-Land à environ 9 km](https://www.ecmwf.int/en/era5-land). La mention 9 km du starter
ne suffit donc pas à identifier le produit fourni. Les consultations et leurs limites figurent dans `reports/audit_sources.md`.



## Inventaire de traçabilité


- `artifacts/full_project/annual_analysis/anchor_descriptive.json`
- `artifacts/full_project/annual_analysis/annual_correlations.png`
- `artifacts/full_project/annual_analysis/annual_correlations.svg`
- `artifacts/full_project/annual_analysis/annual_descriptive.csv`
- `artifacts/full_project/annual_analysis/annual_observations_anchor.png`
- `artifacts/full_project/annual_analysis/annual_observations_anchor.svg`
- `artifacts/full_project/annual_analysis/annual_residual_diagnostics.png`
- `artifacts/full_project/annual_analysis/annual_residual_diagnostics.svg`
- `artifacts/full_project/annual_analysis/annual_summary.json`
- `artifacts/full_project/annual_analysis/correlations.csv`
- `artifacts/full_project/annual_analysis/residual_descriptive.csv`
- `artifacts/full_project/co2_transition.json`
- `artifacts/full_project/final/max/C0_direct_crps/fit.json`
- `artifacts/full_project/final/max/C0_direct_crps/seed0/best.pt`
- `artifacts/full_project/final/max/C0_direct_crps/seed0/history.csv`
- `artifacts/full_project/final/max/C0_direct_crps/seed0/last.pt`
- `artifacts/full_project/final/max/C0_direct_crps/seed0/metadata.json`
- `artifacts/full_project/final/max/C0_direct_crps/seed1/best.pt`
- `artifacts/full_project/final/max/C0_direct_crps/seed1/history.csv`
- `artifacts/full_project/final/max/C0_direct_crps/seed1/last.pt`
- `artifacts/full_project/final/max/C0_direct_crps/seed1/metadata.json`
- `artifacts/full_project/final/max/C0_direct_crps/seed2/best.pt`
- `artifacts/full_project/final/max/C0_direct_crps/seed2/history.csv`
- `artifacts/full_project/final/max/C0_direct_crps/seed2/last.pt`
- `artifacts/full_project/final/max/C0_direct_crps/seed2/metadata.json`
- `artifacts/full_project/final/min/D1_ddm_crps/fit.json`
- `artifacts/full_project/final/min/D1_ddm_crps/seed0/best.pt`
- `artifacts/full_project/final/min/D1_ddm_crps/seed0/history.csv`
- `artifacts/full_project/final/min/D1_ddm_crps/seed0/last.pt`
- `artifacts/full_project/final/min/D1_ddm_crps/seed0/metadata.json`
- `artifacts/full_project/final/min/D1_ddm_crps/seed1/best.pt`
- `artifacts/full_project/final/min/D1_ddm_crps/seed1/history.csv`
- `artifacts/full_project/final/min/D1_ddm_crps/seed1/last.pt`
- `artifacts/full_project/final/min/D1_ddm_crps/seed1/metadata.json`
- `artifacts/full_project/final/min/D1_ddm_crps/seed2/best.pt`
- `artifacts/full_project/final/min/D1_ddm_crps/seed2/history.csv`
- `artifacts/full_project/final/min/D1_ddm_crps/seed2/last.pt`
- `artifacts/full_project/final/min/D1_ddm_crps/seed2/metadata.json`
- `artifacts/full_project/fit_full.json`
- `artifacts/full_project/fitted_models_summary.csv`
- `artifacts/full_project/heatwaves/heatwave_climatology.csv`
- `artifacts/full_project/heatwaves/heatwave_counts.png`
- `artifacts/full_project/heatwaves/heatwave_counts.svg`
- `artifacts/full_project/heatwaves/heatwave_counts_year.csv`
- `artifacts/full_project/heatwaves/heatwave_daily_thresholds.csv`
- `artifacts/full_project/heatwaves/heatwave_duration_intensity.png`
- `artifacts/full_project/heatwaves/heatwave_duration_intensity.svg`
- `artifacts/full_project/heatwaves/heatwave_events_min2.csv`
- `artifacts/full_project/heatwaves/heatwave_events_min3.csv`
- `artifacts/full_project/heatwaves/heatwave_seasonal_cycle.png`
- `artifacts/full_project/heatwaves/heatwave_seasonal_cycle.svg`
- `artifacts/full_project/heatwaves/heatwave_summary.json`
- `artifacts/full_project/probability_40.csv`
- `artifacts/full_project/projection_manifest.json`
- `artifacts/full_project/projection_summary.csv`
- `artifacts/full_project/projections.npz`
- `artifacts/full_project/residual_diagnostic_tail_values.csv`
- `artifacts/full_project/residual_law_diagnostics.csv`
- `artifacts/full_project/run_costs.csv`
- `artifacts/full_project/trajectory_probability_40.csv`