# Synthèse équipe


Candidat verrouillé : Tmax **C0_direct_crps**, Tmin **D1_ddm_crps**. Les choix sont fixés sur validation 1940–2000 avant ouverture du test.


Résultats réels du benchmark (°C pour les CRPS) :


| model | crps_max | crps_min | admissible | errors |
| --- | --- | --- | --- | --- |
| R0_exact | 1.69889 | 1.06413 | True | — |
| R0_gaussian | 1.70769 | 1.06449 | True | — |
| R1_gev | 1.7278 | 1.03603 | True | — |
| R2_empirical | 1.735 | 1.03015 | True | — |
| D0_ddpm | 1.75006 | 2.62 | False | min: bornes |
| C0_direct_crps | 1.74899 | 1.02704 | True | — |
| D1_ddm_crps | 1.70071 | 1.03104 | True | — |
| D2_ddm_tail | 1.70691 | 1.01464 | True | — |
| D3_ddm_anchor | 1.64919 | 0.987842 | True | — |
| D4_ddm_tail_anchor | 1.65476 | 0.978821 | True | — |
| participant | 1.74899 | 1.03104 | True | — |


Participant **participant** : CRPS Tmax **1.748986 °C**, Tmin **1.031040 °C** ; statut **admissible**.

**DDPM D0 est éliminé** : 19152 valeurs de Tmin sortent de [−30,20] °C ; le minimum simulé atteint **-1933.216 °C**. Son CRPS Tmin brut est **2.619998 °C** et le kit retourne None. Un bon score de validation ne rend donc pas cette configuration admissible.

Détails : [diagnostic_echec_ddpm.md](diagnostic_echec_ddpm.md), fondé sur le NPZ et les checkpoints figés.


Tmax > 40 °C en 2100, conditionnellement au modèle : ssp1-2.6 **0/10000 (0.000 %)**; ssp2-4.5 **2/10000 (0.020 %)**; ssp5-8.5 **29/10000 (0.290 %)**. Avec zéro tirage dépassant 40 °C, aucun dépassement n'est simulé ; la borne Monte-Carlo à 95 % est 0,000369, pas une probabilité physique nulle.


Vagues de chaleur descriptives 1940–2025 : **421 événements ≥ 3 jours**, **798 ≥ 2 jours** ; durée maximale **14 jours**.


Les 25 années de test et les 61 années d'apprentissage limitent la précision des conclusions. Le CO₂ sert de covariable de tendance ; la stabilité des résidus et l'extrapolation jusqu'à 2100 restent des hypothèses. La simulation de 40 °C ne valide pas la queue physique.


À partager localement : les deux rapports, les notebooks exécutés, les PNG/SVG, les CSV/JSON et les NPZ officiels ; conserver configs, checkpoints et empreintes pour reproduction.