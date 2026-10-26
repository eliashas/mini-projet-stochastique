"""Tests ciblés: conventions de scores, fuite temporelle et contrôles officiels.

Toutes les observations utilisées ici sont synthétiques. Aucun fichier de
températures de test n'est ouvert, et exemple.py n'est jamais importé.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sma.anchor import bootstrap_anchor, fit_anchor, predict_anchor
from sma.scores import crps_rows, torch_crps, twcrps_rows
from sma.splits import temporal_folds


def brute_score(x, y, fair=False):
    """Formule O(M²), exclusivement pour de très petits ensembles de test."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = x.shape[1]
    denominator = m * (m - 1) if fair else m * m
    return np.abs(x - y[:, None]).mean(axis=1) - np.abs(
        x[:, :, None] - x[:, None, :]
    ).sum(axis=(1, 2)) / (2 * denominator)


class ScoreTests(unittest.TestCase):
    def test_sorted_crps_matches_raw_pairs_with_ties(self):
        x = np.array([[2., -1., 2., 5.], [-8., -2., 0., 3.]])
        y = np.array([1., -3.])
        np.testing.assert_allclose(crps_rows(x, y), brute_score(x, y), atol=1e-12)
        self.assertEqual(crps_rows(x.astype(np.float32), y).dtype, np.float64)

    def test_deterministic_forecast_is_absolute_error(self):
        x = np.repeat(np.array([2., -4., 0.])[:, None], 9, axis=1)
        y = np.array([4., -4., -3.])
        np.testing.assert_allclose(crps_rows(x, y), [2., 0., 3.], atol=1e-12)

    def test_empirical_fair_almost_fair_denominators(self):
        x = np.array([[-3., 1., 2., 7.], [1., 2., 3., 4.]])
        y = np.array([0., 2.5])
        empirical, fair = brute_score(x, y), brute_score(x, y, fair=True)
        self.assertTrue(np.all(fair < empirical))
        for alpha in [0., 0.95, 1.]:
            score = torch_crps(torch.tensor(x), torch.tensor(y), alpha=alpha)
            self.assertAlmostEqual(score.item(), np.mean(alpha * fair + (1-alpha) * empirical), places=12)

    def test_two_member_fair_convention_and_degeneracy(self):
        # One member at y makes fair score zero regardless of the other member;
        # almost fair leaves a positive penalty. This catches M versus M-1.
        x, y = torch.tensor([[0., 8.]], dtype=torch.float64), torch.tensor([0.])
        self.assertAlmostEqual(torch_crps(x, y, alpha=1.).item(), 0.)
        self.assertAlmostEqual(torch_crps(x, y, alpha=0.).item(), 2.)
        self.assertAlmostEqual(torch_crps(x, y, alpha=.95).item(), .1)
        with self.assertRaises(ValueError):
            torch_crps(x[:, :1], y)

    def test_almost_fair_gradients_are_finite(self):
        x = torch.tensor([[-2., .5, 2., 8.], [0., 1., 1., 3.]], dtype=torch.float64, requires_grad=True)
        y = torch.tensor([.3, 1.2], dtype=torch.float64)
        value = torch_crps(x, y)
        value.backward()
        self.assertTrue(torch.isfinite(value).item())
        self.assertTrue(torch.isfinite(x.grad).all().item())
        self.assertGreater(x.grad.abs().sum().item(), 0.)

    def test_tail_transform_and_false_alarm_for_both_orientations(self):
        x = np.array([[0., 4., 12.], [7., 8., 10.]])
        y = np.array([3., 11.])
        for variable, transform, threshold in [("max", np.maximum, 6.), ("min", np.minimum, 4.)]:
            expected = crps_rows(transform(x, threshold), transform(y, threshold))
            np.testing.assert_allclose(twcrps_rows(x, y, threshold, variable), expected)
        hot = twcrps_rows(np.array([[14., 14.]]), np.array([3.]), 10., "max")
        cold = twcrps_rows(np.array([[-12., -12.]]), np.array([3.]), -8., "min")
        np.testing.assert_allclose(hot, [4.])
        np.testing.assert_allclose(cold, [4.])
        np.testing.assert_allclose(twcrps_rows(np.array([[0., 2.]]), np.array([3.]), 10., "max"), [0.])


class TemporalAnchorTests(unittest.TestCase):
    def setUp(self):
        self.co2 = np.linspace(300., 390., 61)
        self.y = 6. + 3. * np.log(self.co2) + .4 * np.sin(np.arange(61))

    def test_anchor_reproduces_kit_equations_and_negative_constraint(self):
        fit = fit_anchor(self.co2, self.y)
        b_raw, _ = np.polyfit(np.log(self.co2), self.y, 1)
        b = max(b_raw, 0.)
        a = np.mean(self.y - b*np.log(self.co2))
        residuals = self.y - (a+b*np.log(self.co2))
        np.testing.assert_allclose([fit["a"], fit["b"], fit["b_raw"], fit["sigma"]],
                                   [a, b, b_raw, np.std(residuals, ddof=2)])
        np.testing.assert_allclose(fit["residuals"], residuals)
        np.testing.assert_allclose(fit["z"], residuals / fit["sigma"])
        negative = fit_anchor(self.co2, -self.y)
        self.assertLess(negative["b_raw"], 0.)
        self.assertEqual(negative["b"], 0.)
        self.assertAlmostEqual(negative["a"], np.mean(-self.y))
        np.testing.assert_allclose(predict_anchor(negative, [300., 950.]), [negative["a"]]*2)

    def test_scale_floor_is_explicit_and_does_not_hide_degeneracy(self):
        fit = fit_anchor(self.co2, np.full(61, 20.))
        self.assertTrue(fit["scale_floor_active"])
        self.assertGreater(fit["sigma"], 0.)
        self.assertLess(fit["sigma_raw"], 1e-6)

    def test_chronological_folds_and_train_only_anchor(self):
        df = pd.DataFrame({"valid_time": pd.to_datetime([f"{year}-01-01" for year in range(1940, 2026)]),
                           "co2": np.linspace(300., 430., 86), "max": np.arange(86, dtype=float)})
        expected = [("F1",1970,1971,1980,31),("F2",1980,1981,1990,41),("F3",1990,1991,2000,51)]
        for (name, train, val), (identifier,end,lo,hi,n) in zip(temporal_folds(df), expected, strict=True):
            self.assertEqual(name, identifier)
            self.assertEqual(len(train), n)
            self.assertEqual(len(val), 10)
            self.assertEqual(list(train.valid_time.dt.year), list(range(1940, end+1)))
            self.assertEqual(list(val.valid_time.dt.year), list(range(lo, hi+1)))
            fit_before = fit_anchor(train.co2, train["max"])
            mutated = df.copy()
            mutated.loc[mutated.valid_time.dt.year > end, "max"] += 9999.
            changed_train = list(temporal_folds(mutated))[int(name[-1])-1][1]
            fit_after = fit_anchor(changed_train.co2, changed_train["max"])
            self.assertEqual(fit_before["a"], fit_after["a"])
            self.assertEqual(fit_before["b"], fit_after["b"])
            self.assertFalse(set(train.index) & set(val.index))

    def test_residual_bootstrap_fixed_covariate_and_reproducibility(self):
        original = self.co2.copy()
        result = bootstrap_anchor(self.co2, self.y, B=29, block_length=3, seed=777)
        repeated = bootstrap_anchor(self.co2, self.y, B=29, block_length=3, seed=777)
        np.testing.assert_array_equal(self.co2, original)
        self.assertTrue(result["fixed_co2"])
        self.assertEqual(result["co2_sha256"], hashlib.sha256(self.co2.tobytes()).hexdigest())
        for key in ["a", "b", "b_raw"]:
            self.assertEqual(np.asarray(result[key]).shape, (29,))
            np.testing.assert_array_equal(result[key], repeated[key])
        self.assertTrue(np.all(result["b"] >= 0.))
        self.assertAlmostEqual(result["constraint_fraction"], np.mean(result["b_raw"] < 0.))
        # Shared anchor and residual across scenarios guarantees ordered draws.
        residual = np.random.default_rng(90).normal(size=29)
        predicted = result["a"][:, None] + result["b"][:, None]*np.log([400., 527., 946.]) + residual[:, None]
        self.assertTrue(np.all(np.diff(predicted, axis=1) >= -1e-12))

    def test_bootstrap_circular_blocks_match_explicit_refit(self):
        fitted = fit_anchor(self.co2, self.y)
        centered = fitted["residuals"] - fitted["residuals"].mean()
        rng = np.random.default_rng(321)
        starts = rng.integers(0, 61, size=21)
        indices = ((starts[:, None] + np.arange(3)) % 61).ravel()[:61]
        manual = fit_anchor(self.co2, predict_anchor(fitted, self.co2) + centered[indices])
        boot = bootstrap_anchor(self.co2, self.y, B=1, block_length=3, seed=321)
        for key in ["a", "b", "b_raw"]:
            self.assertAlmostEqual(boot[key][0], manual[key], places=12)


class OfficialControlFixtures(unittest.TestCase):
    @staticmethod
    def fixture():
        members = np.linspace(-2., 2., 10000)
        return {"test_max": np.repeat((25.+members)[None],25,axis=0),
                "test_min": np.repeat((-3.+members)[None],25,axis=0),
                "proj_max": np.array([27.,30.,35.])[:,None]+members,
                "proj_min": np.array([-2.,0.,4.])[:,None]+members}

    def check(self, arrays):
        from sma.benchmark_adapter import check_predictions
        return check_predictions(arrays)

    def test_all_official_controls_pass(self):
        result = self.check(self.fixture())
        self.assertTrue(result["admissible"])

    def test_monotonicity_fail_for_each_variable(self):
        for variable in ["max", "min"]:
            arrays = self.fixture()
            arrays[f"proj_{variable}"] = arrays[f"proj_{variable}"][::-1]
            result = self.check(arrays)
            self.assertFalse(result["admissible"])
            self.assertFalse(result["variables"][variable]["monotonic"])
            self.assertTrue(result["variables"][variable]["width_ok"])
            self.assertTrue(result["variables"][variable]["bounds_ok"])

    def test_width_fail_for_each_variable(self):
        for variable in ["max", "min"]:
            arrays = self.fixture()
            arrays[f"proj_{variable}"][2,:] = np.median(arrays[f"proj_{variable}"][2])
            result = self.check(arrays)
            self.assertFalse(result["admissible"])
            self.assertFalse(result["variables"][variable]["width_ok"])
            self.assertTrue(result["variables"][variable]["monotonic"])

    def test_bounds_fail_preserves_raw_prediction(self):
        for key, bad in [("test_max",50.01),("proj_max",-.01),("test_min",-30.01),("proj_min",20.01)]:
            arrays = self.fixture()
            arrays[key][0,0] = bad
            self.assertFalse(self.check(arrays)["admissible"])
            self.assertEqual(arrays[key][0,0], bad)

    def test_deterministic_case_passes_width_officially(self):
        arrays = self.fixture()
        for key, values in arrays.items():
            arrays[key] = np.repeat(np.median(values, axis=1)[:,None],10000,axis=1)
        result = self.check(arrays)
        self.assertTrue(result["admissible"])
        self.assertFalse(result["variables"]["max"]["non_degenerate"])
        self.assertFalse(result["variables"]["min"]["non_degenerate"])

    def test_nonfinite_and_wrong_shape_are_rejected(self):
        for malformed in ["nonfinite", "shape"]:
            arrays = self.fixture()
            if malformed == "nonfinite":
                arrays["test_max"][0,0] = np.inf
            else:
                arrays["proj_max"] = arrays["proj_max"][:2]
            try:
                result = self.check(arrays)
            except (ValueError, AssertionError):
                continue
            self.assertFalse(result["admissible"])


class PhaseAndExtractionTests(unittest.TestCase):
    def test_truth_opening_marker_survives_interrupted_read_without_actual_truth(self):
        from sma.benchmark_adapter import run_benchmarks
        from sma.utils import fingerprint
        config = {"original_kit_dir": "unused-synthetic-kit"}
        manifest = {"selection_sha256": "locked-hash", "locked_source_sha256": "locked-hash", "config_sha256": fingerprint(config),
                    "input_hashes": {}, "predictions": [], "checkpoint_hashes": {}, "kit_sha256": "locked-hash"}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            marker = root / "artifacts" / "competition" / "test_truth_opened.json"
            def interrupted_read(*args, **kwargs):
                self.assertTrue(marker.exists())
                raise RuntimeError("simulated read failure; no file is opened")
            with mock.patch("sma.benchmark_adapter.ROOT", root), mock.patch("sma.benchmark_adapter.read_json", return_value=manifest), mock.patch("sma.benchmark_adapter.sha256", return_value="locked-hash"), mock.patch("sma.data.input_hashes", return_value={}), mock.patch("sma.benchmark_adapter.load_kit", return_value=SimpleNamespace(DATA=root / "synthetic")), mock.patch("sma.benchmark_adapter.event"), mock.patch("sma.benchmark_adapter.pd.read_csv", side_effect=interrupted_read):
                with self.assertRaisesRegex(RuntimeError, "simulated read failure"):
                    run_benchmarks(config, root / "synthetic_manifest.json")
            self.assertTrue(marker.exists())
            self.assertFalse((root / "artifacts" / "competition" / "benchmark_results.json").exists())

    def test_competition_mutations_blocked_by_truth_marker_without_results(self):
        from sma import experiments
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            marker = root / "artifacts" / "competition" / "test_truth_opened.json"
            marker.parent.mkdir(parents=True)
            marker.write_text("{}", encoding="utf-8")
            with mock.patch("sma.experiments.ROOT", root), mock.patch("sma.experiments.read_json", return_value={}), mock.patch("sma.experiments.load_competition", return_value={}), mock.patch("sma.experiments.train_network") as trainer:
                for action in [lambda: experiments.validation({}), lambda: experiments.select({}),
                               lambda: experiments.final_fit({}, {}), lambda: experiments.predict_competition({}, {})]:
                    with self.assertRaises(RuntimeError):
                        action()
                trainer.assert_not_called()

    def test_modified_selection_rejected_before_kit_or_csv_read(self):
        from sma.benchmark_adapter import run_benchmarks
        with mock.patch("sma.benchmark_adapter.read_json", return_value={"selection_sha256": "old"}), mock.patch("sma.benchmark_adapter.sha256", return_value="modified"), mock.patch("sma.benchmark_adapter.load_kit") as loader, mock.patch("sma.benchmark_adapter.pd.read_csv") as reader:
            with self.assertRaises(ValueError):
                run_benchmarks({}, "synthetic_manifest.json")
            loader.assert_not_called()
            reader.assert_not_called()

    def test_modified_config_or_inputs_rejected_before_kit_or_csv_read(self):
        from sma.benchmark_adapter import run_benchmarks
        from sma.utils import fingerprint
        config = {"original_kit_dir": "unused-synthetic-kit"}
        for change in ["config", "inputs"]:
            manifest = {"selection_sha256": "locked-hash", "locked_source_sha256": "locked-hash", "config_sha256": fingerprint(config), "input_hashes": {}}
            if change == "config":
                manifest["config_sha256"] = "old-config"
            else:
                manifest["input_hashes"] = {"synthetic.csv": "old-input"}
            with mock.patch("sma.benchmark_adapter.read_json", return_value=manifest), mock.patch("sma.benchmark_adapter.sha256", return_value="locked-hash"), mock.patch("sma.data.input_hashes", return_value={}), mock.patch("sma.benchmark_adapter.load_kit") as loader, mock.patch("sma.benchmark_adapter.pd.read_csv") as reader:
                with self.assertRaises(ValueError):
                    run_benchmarks(config, "synthetic_manifest.json")
                loader.assert_not_called()
                reader.assert_not_called()

    def test_selection_proximity_is_strict_at_point_zero_five(self):
        from sma.experiments import select
        config = {"tail_lambda_grid": [.5], "complexity_order": ["R0_gaussian", "D1_ddm_crps"],
                  "selection_tolerance": .05, "mixture_counts": [3334,3333,3333], "final_steps_rule": "median_best_steps_folds"}
        with tempfile.TemporaryDirectory() as folder:
            for gap, expected in [(.04999,"R0_gaussian"),(.05,"D1_ddm_crps"),(.05001,"D1_ddm_crps")]:
                records = [{"variable":variable,"model":model,"fold_count":3,"crps":score}
                           for variable in ["max","min"] for model,score in [("D1_ddm_crps",1.),("R0_gaussian",1.+gap)]]
                with mock.patch("sma.experiments.ROOT", Path(folder)), mock.patch("sma.experiments.pd.read_csv", return_value=pd.DataFrame(records)), mock.patch("sma.experiments.read_json", return_value=[]), mock.patch("sma.experiments.input_hashes", return_value={}), mock.patch("sma.experiments.write_json"), mock.patch("sma.experiments.sha256", return_value="synthetic-hash"), mock.patch("sma.experiments.event"):
                    selected = select(config)
                self.assertEqual(selected["selected_models"], {"max":expected,"min":expected})

    def test_competition_loader_reads_only_four_authorized_inputs(self):
        from sma.data import INPUTS, load_competition
        with mock.patch("sma.data.pd.read_csv", return_value=object()) as reader:
            result = load_competition({"kit_dir": "unused-synthetic-kit"})
        self.assertEqual(set(result), {name.removesuffix(".csv") for name in INPUTS})
        self.assertEqual({call.args[0].name for call in reader.call_args_list}, set(INPUTS))
        self.assertEqual(reader.call_count, 4)

    def test_whitelist_extraction_never_writes_outside_destination(self):
        from sma.data import FULL_NAMES, safe_extract
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive, destination = root / "synthetic.zip", root / "output"
            with zipfile.ZipFile(archive, "w") as zipped:
                for name in FULL_NAMES:
                    zipped.writestr(name, "synthetic content; no real observations\n")
                for name in ["/", "../escaped.csv", "nested/yearly_temp_brest.csv", "C:/escaped.csv", "verite_2001_2025.csv"]:
                    zipped.writestr(name, "forbidden entry")
            checksums = safe_extract(archive, destination)
            self.assertEqual(set(checksums), FULL_NAMES)
            self.assertEqual({file.name for file in destination.iterdir()}, FULL_NAMES)
            self.assertFalse((root / "escaped.csv").exists())
            for path in destination.iterdir():
                self.assertEqual(path.resolve().parent, destination.resolve())

    def test_incomplete_archive_fails_explicitly(self):
        from sma.data import safe_extract
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "synthetic.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("yearly_temp_brest.csv", "synthetic")
            with self.assertRaises(ValueError):
                safe_extract(archive, Path(folder) / "output")

    def test_full_data_guard_blocks_before_any_csv_or_archive_read(self):
        from sma.data import load_full
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch("sma.data.ROOT", Path(folder)), mock.patch("sma.data.pd.read_csv") as reader, mock.patch("sma.data.safe_extract") as extractor:
                with self.assertRaises(RuntimeError):
                    load_full({"full_archive": "never-open.zip"})
                reader.assert_not_called()
                extractor.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
