# Travail de Reda : notebook complet (partie 1 + partie 2)

| Fichier | Rôle |
|---|---|
| `miniprojet_MCE_SMA_2026_groupe.ipynb` | Le notebook exécuté, avec la partie 1 (cycle saisonnier, vagues de chaleur, diagramme intensité–durée) et la partie 2 (modèle) |
| `EXPLICATION_PROJET.pdf` | Explication pédagogique de la méthode et des résultats |
| `build_notebook.py`, `comments.py`, `comments.json` | Scripts qui génèrent le notebook à partir de celui du prof |
| `explication/` | Source LaTeX du PDF et figures |
| `*.csv` | Données ERA5 de Brest et scénarios de CO2 fournis par le prof |

**Modèle de la partie 2 :** une loi GEV non stationnaire dont la position dépend de ln(CO2/280), entraînée en PyTorch, avec un bootstrap de 500 modèles et des tirages Monte-Carlo. Entraînement sur 1940–2000, test sur 2001–2025 : CRPS Tmax = 1,66 °C (référence gaussienne : 1,70 °C). Pour Tmin, bootstrap des résidus : CRPS = 1,09 °C (référence : 1,06 °C).
