"""Contrôles des formules et du conditionnement du notebook concis."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
import torch


RACINE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cellules_diffusion', RACINE / 'rendu_final_concis' / 'diffusion.py')
cellules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cellules)


class DiffusionConcisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = {'np': np, 'pd': pd, 'torch': torch, 'N': 100}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(cellules.CODE_MODELE, cls.ns)
        cls.ns['device'] = torch.device('cpu')

    def test_score_avec_la_formule_par_paires_et_gradient(self):
        X = torch.tensor([[2., -1., 3., 0.], [1., 4., 2., -2.]], requires_grad=True)
        y = torch.tensor([1., 3.])
        for alpha in (0., .95, 1.):
            M = X.shape[1]
            distance = torch.abs(X[:, :, None] - X[:, None, :]).sum((1, 2)) / 2
            attendu = ((X - y[:, None]).abs().mean(1)
                       - distance * (alpha / (M * (M - 1)) + (1 - alpha) / M**2)).mean()
            valeur = self.ns['crps_entrainement'](X, y, alpha)
            torch.testing.assert_close(valeur, attendu)
        valeur.backward()
        self.assertTrue(torch.isfinite(X.grad).all())

    def test_normalisation_sur_les_seules_donnees_entrainees(self):
        x = np.linspace(5.7, 6., 12)
        t = 4. + 3. * x + np.sin(np.arange(12))
        m = self.ns['entrainer_diffusion'](x, t, 2)
        ab = self.ns['ancre'](x, t)
        np.testing.assert_allclose(m['ancre'], ab)
        self.assertAlmostEqual(m['e'], np.std(t - ab[0] - ab[1] * x, ddof=2))
        self.assertAlmostEqual(m['seuil'], np.quantile(t, .8))
        self.assertTrue(all(p.device.type == 'cpu' for p in m['reseau'].parameters()))

    def test_une_droite_par_trajectoire_et_tirage_reproductible(self):
        g = self.ns['Debruiteur']()
        for p in g.parameters():
            torch.nn.init.zeros_(p)
        m = {'reseau': g, 'e': 2., 'ancre': np.array([1., 3.])}
        suite = {'membres': [m, m, m], 'droites': np.array([[2., 1.], [-5., 4.], [3., 2.]])}
        x = np.array([5., 6., 7.])
        tirer = self.ns['tirer_diffusion']
        fixe = tirer(suite, x, bootstrap=False)
        np.testing.assert_allclose(fixe, np.broadcast_to(1. + 3. * x, fixe.shape))
        variable = tirer(suite, x, bootstrap=True)
        # Une droite garde le même incrément entre les deux intervalles de CO2.
        np.testing.assert_allclose(variable[:, 2] - variable[:, 1], variable[:, 1] - variable[:, 0])
        np.testing.assert_array_equal(variable, tirer(suite, x, bootstrap=True))
        self.assertGreater(np.std(variable[:, 0]), 0.)

    def test_tables_incluses_correspondent_aux_archives(self):
        ns = {'pd': pd, 'io': io}
        source = cellules.cellule_archives(RACINE).split('ordre =')[0]
        exec(source, ns)
        for phase in ['validation', 'test']:
            original = pd.read_csv(RACINE / 'rendu_final' / 'resultats' / (phase + '.csv'))
            inclus = ns[phase + '_reference']
            original = original[original['model'].isin(inclus['model'])][inclus.columns].reset_index(drop=True)
            pd.testing.assert_frame_equal(inclus, original)


if __name__ == '__main__':
    unittest.main()
