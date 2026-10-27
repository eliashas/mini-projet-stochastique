"""Modèle de référence, fait par nous (pas par le prof) : T = a + b ln(CO2) + bruit gaussien. À battre !"""
import numpy as np
import kit

rng = np.random.default_rng(0)
jour, an, test, futur = kit.charger()


def modele(co2):
    """Renvoie une fonction : variable -> tirages (len(co2), N_TIRAGES) en °C. Entraîné sur 1940-2000."""
    x = np.log(an.co2.to_numpy())
    def tirer(v):
        b, a = np.polyfit(x, an[v], 1)
        b = max(b, 0)  # plus de CO2 ne doit pas refroidir (test de cohérence)
        a = np.mean(an[v] - b * x)
        sigma = np.std(an[v] - (a + b * x), ddof=2)
        return (a + b * np.log(co2))[:, None] + sigma * rng.standard_normal((len(co2), kit.N_TIRAGES))
    return tirer


# Prédire 2001-2025 et 2100 (3 scénarios), puis lancer le benchmark
co2_2100 = futur.loc[futur.valid_time.dt.year == 2100, list(kit.SCENARIOS)].to_numpy().ravel()
t_test, t_2100 = modele(test.co2.to_numpy()), modele(co2_2100)
kit.benchmark(t_test('max'), t_test('min'), t_2100('max'), t_2100('min'))
