"""Kit du benchmark : chargement des données et benchmark.

    import kit
    jour, an, test, futur = kit.charger()
    ...
    kit.benchmark(test_max, test_min, proj_max, proj_min)
"""
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).parent / 'data'
N_TIRAGES = 10_000
ANNEES_TEST = list(range(2001, 2026))
SCENARIOS = ('ssp1-2.6', 'ssp2-4.5', 'ssp5-8.5')
BORNES = {'max': (0, 50), 'min': (-30, 20)}  # valeurs physiquement plausibles à Brest (°C)
TOLERANCE = 0.1                              # °C, absorbe le bruit des tirages sur les médianes
REFERENCE = {'max': 1.70, 'min': 1.06}       # scores du modèle de référence (exemple.py), en °C


def charger():
    """Les 4 fichiers pour construire son modèle : journalier et annuel 1940-2000, CO2 2001-2025, CO2 futur (SSP)."""
    lire = lambda nom: pd.read_csv(DATA / nom, parse_dates=['valid_time'])
    return (lire('daily_temp_brest_train.csv'), lire('yearly_temp_brest_train.csv'),
            lire('test_inputs.csv'), lire('yearly_future_co2.csv'))


def crps(tirages, obs):
    """CRPS moyen (°C) : tirages (n_annees, n_tirages), obs (n_annees,). Plus bas = mieux."""
    x = np.sort(np.asarray(tirages, dtype=float), axis=1)
    n = x.shape[1]
    poids = (2 * np.arange(1, n + 1) - n - 1) / n**2
    return (np.abs(x - np.asarray(obs, dtype=float)[:, None]).mean(axis=1) - x @ poids).mean()


def _verifier(nom, t, forme):
    t = np.asarray(t, dtype=float)
    assert t.shape == forme, f'{nom} : forme {t.shape}, attendu {forme}'
    assert np.isfinite(t).all(), f'{nom} : valeurs non finies'
    return t


def benchmark(test_max, test_min, proj_max, proj_min):
    """Lance le benchmark et affiche le résultat.

    test_* : (25, N_TIRAGES) pour 2001-2025 ; proj_* : (3, N_TIRAGES) pour 2100, dans l'ordre de SCENARIOS. En °C.
    Renvoie (score final, score de départage), ou None si un test de cohérence échoue.
    """
    verite = pd.read_csv(DATA / 'verite_2001_2025.csv')
    scores, problemes = {}, []
    for v, test, proj in (('max', test_max, proj_max), ('min', test_min, proj_min)):
        t = _verifier(f'test_{v}', test, (len(ANNEES_TEST), N_TIRAGES))
        p = _verifier(f'proj_{v}', proj, (len(SCENARIOS), N_TIRAGES))
        scores[v] = crps(t, verite[v])
        med = np.median(p, axis=1)
        if not (med[0] <= med[1] + TOLERANCE and med[1] <= med[2] + TOLERANCE):
            problemes.append(f'{v} : plus de CO2 donne plus froid en 2100 (médianes SSP1, SSP2, SSP5 = {med.round(2).tolist()} °C)')
        q10, q90 = np.quantile(t, [.1, .9], axis=1)
        if np.subtract(*np.quantile(p[2], [.9, .1])) < 0.95 * np.mean(q90 - q10):
            problemes.append(f'{v} : incertitude 2100 (SSP5-8.5) plus étroite que sur 2001-2025')
        lo, hi = BORNES[v]
        if min(t.min(), p.min()) < lo or max(t.max(), p.max()) > hi:
            problemes.append(f'{v} : valeurs hors de [{lo}, {hi}] °C')
    print('Tests de cohérence : ' + ('OK' if not problemes else 'ÉCHEC -> ÉLIMINÉ' + ''.join(f'\n  - {p}' for p in problemes)))
    print(f"SCORE FINAL (CRPS du max, 2001-2025) : {scores['max']:.2f} °C   (référence à battre : {REFERENCE['max']:.2f})")
    print(f"Départage   (CRPS du min, 2001-2025) : {scores['min']:.2f} °C   (référence : {REFERENCE['min']:.2f})")
    return None if problemes else (scores['max'], scores['min'])
