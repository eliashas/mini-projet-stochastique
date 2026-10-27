# Projet SMA : températures extrêmes à Brest

| Fichier | Rôle |
|---|---|
| `GUIDE.pdf` | **À lire en premier** (3 pages) : l'objectif, le score, les règles |
| `CONTEXTE_POUR_LLM.md` | Toutes les informations du projet, en détail. À donner à ton LLM pour qu'il réponde à tes questions |
| `exemple.py` | Le modèle de référence, fait par nous (pas par le prof). Score à battre : 1,70 °C |
| `kit.py` | Charge les données et lance le benchmark |
| `data/` | Températures 1940–2000, CO2 de 2001–2025, CO2 futur. `verite_2001_2025.csv` sert au benchmark : interdit de l'utiliser dans un modèle |

Pour lancer le benchmark : lance `exemple.py`. Pour tester ton modèle, remplace la fonction `modele` par la tienne.
