"""Meaningful neural tests: RNG isolation and exact resumed AdamW trajectory.

All arrays below are synthetic and no file containing test truth is opened.
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sma.sampling import load_network, sample_network
from sma.training import train_network
from sma.models.ddm import ScalarDDM
from sma.models.ddpm import ScalarDDPM, cosine_schedule


class DiffusionContractTests(unittest.TestCase):
    def test_ddpm_schedule_terminal_noise_and_posterior(self):
        schedule = cosine_schedule(100)
        beta, alpha, abar, variance = [schedule[k] for k in ["beta", "alpha", "alpha_bar", "posterior_variance"]]
        self.assertEqual(beta.shape, (101,))
        self.assertEqual(abar[0].item(), 1.)
        self.assertLess(abar[-1].item(), 1e-3)
        self.assertTrue(torch.all((beta[1:] > 0.) & (beta[1:] <= .999)).item())
        torch.testing.assert_close(abar, torch.cumprod(alpha, dim=0))
        torch.testing.assert_close(variance[1:], beta[1:]*(1-abar[:-1])/(1-abar[1:]))
        self.assertEqual(variance[1].item(), 0.)
        self.assertTrue(torch.all(variance >= 0.).item())

    def test_ddpm_final_transition_has_no_noise_and_formula_is_exact(self):
        model = ScalarDDPM()
        for param in model.parameters():
            torch.nn.init.zeros_(param)
        z = torch.tensor([-2., .3, 3.])
        torch.testing.assert_close(model.reverse_step(z, 1, torch.full_like(z, 1000.)), z/model.alpha[1].sqrt())
        torch.testing.assert_close(model.reverse_step(z, 2, torch.ones_like(z)),
                                   z/model.alpha[2].sqrt()+model.posterior_variance[2].sqrt())

    def test_ddm_shared_corruption_independent_latents_and_future_endpoint(self):
        model = ScalarDDM()
        generator = torch.Generator().manual_seed(66)
        u, t, latent = model.ensemble_inputs(torch.tensor([1., -2., .5]), 32, generator)
        torch.testing.assert_close(u, u[:, :1].expand_as(u))
        torch.testing.assert_close(t, t[:, :1].expand_as(t))
        self.assertTrue(torch.all(latent.std(dim=1) > .1).item())
        captured = []
        handle = model.network.register_forward_pre_hook(lambda module, args: captured.append(args[0].detach().clone()))
        draws = model.sample(128, torch.Generator().manual_seed(4), batch_size=64)
        handle.remove()
        self.assertEqual(draws.shape, (128,))
        self.assertTrue(torch.isfinite(draws).all().item())
        self.assertGreater(draws.std().item(), 1e-8)
        for inputs in captured:
            torch.testing.assert_close(inputs[:, 1], torch.ones_like(inputs[:, 1]))
        direct = ScalarDDM(direct=True)
        du, dt, _ = direct.ensemble_inputs(torch.tensor([1., -2.]), 32, generator)
        torch.testing.assert_close(du, torch.zeros_like(du))
        torch.testing.assert_close(dt, torch.ones_like(dt))


class TrainingResumeTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        self.z = np.linspace(-1.7, 1.7, 31)
        self.mu = np.linspace(22., 23., 31)
        self.sigma = 2.1
        self.y = self.mu + self.sigma * self.z
        self.config = {"device": "cpu", "max_steps": 24, "min_steps": 10,
                       "eval_every": 8, "samples_early_stopping": 128,
                       "sampling_batch_size": 64, "crps_training_members": 8,
                       "batch_size": 16}

    def fit(self, directory, steps, model="D1_ddm_crps", validation=None):
        return train_network(model, self.z, self.mu, self.y, self.sigma,
                             float(np.quantile(self.y, .8)), "max", self.config, 7,
                             Path(directory), validation=validation, fixed_steps=steps)

    def test_resumed_training_matches_uninterrupted_parameters_and_rng(self):
        with tempfile.TemporaryDirectory() as temp:
            full_dir, resume_dir = Path(temp) / "full", Path(temp) / "resumed"
            self.fit(full_dir, 24)
            self.fit(resume_dir, 11)
            result = self.fit(resume_dir, 24)
            self.assertEqual(result["resume_from_step"], 11)
            full = torch.load(full_dir / "last.pt", weights_only=False)
            resumed = torch.load(resume_dir / "last.pt", weights_only=False)
            for key, value in full["model_state"].items():
                torch.testing.assert_close(value, resumed["model_state"][key], rtol=0, atol=0)
            torch.testing.assert_close(full["rng_states"]["training_generator"],
                                       resumed["rng_states"]["training_generator"], rtol=0, atol=0)
            for key in full["optimizer_state"]["state"]:
                for item in ["step", "exp_avg", "exp_avg_sq"]:
                    torch.testing.assert_close(full["optimizer_state"]["state"][key][item],
                                               resumed["optimizer_state"]["state"][key][item],
                                               rtol=0, atol=0)
            np.testing.assert_array_equal(sample_network(full_dir / "best.pt", 256, 44, "cpu"),
                                          sample_network(resume_dir / "best.pt", 256, 44, "cpu"))
            self.assertTrue(self.fit(resume_dir, 24)["reused"])

    def test_sampling_preserves_global_rng_and_uses_reproducible_explicit_seed(self):
        with tempfile.TemporaryDirectory() as temp:
            self.fit(temp, 4)
            torch.manual_seed(456)
            initial = torch.get_rng_state().clone()
            one = sample_network(Path(temp) / "best.pt", 100, 22, "cpu", 64)
            torch.testing.assert_close(initial, torch.get_rng_state(), rtol=0, atol=0)
            two = sample_network(Path(temp) / "best.pt", 100, 22, "cpu", 64)
            three = sample_network(Path(temp) / "best.pt", 100, 23, "cpu", 64)
            np.testing.assert_array_equal(one, two)
            self.assertGreater(np.std(one), 1e-8)
            self.assertFalse(np.array_equal(one, three))

    def test_validation_does_not_consume_training_noise_stream(self):
        validation = {"mu": np.array([23.1, 23.2]), "y": np.array([22., 25.]),
                      "co2": np.array([360., 361.])}
        with tempfile.TemporaryDirectory() as temp:
            self.fit(Path(temp) / "no_val", 24)
            self.fit(Path(temp) / "val", 24, validation=validation)
            plain = torch.load(Path(temp) / "no_val" / "last.pt", weights_only=False)
            scored = torch.load(Path(temp) / "val" / "last.pt", weights_only=False)
            for key in plain["model_state"]:
                torch.testing.assert_close(plain["model_state"][key], scored["model_state"][key], rtol=0, atol=0)
            self.assertIsNotNone(scored["history"][-1]["validation_crps"])

    def test_conflicting_input_and_config_resume_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            self.fit(temp, 4)
            altered = self.config | {"learning_rate": .002}
            with self.assertRaisesRegex(ValueError, "conflicting"):
                train_network("D1_ddm_crps", self.z, self.mu, self.y, self.sigma,
                              float(np.quantile(self.y, .8)), "max", altered, 7,
                              Path(temp), fixed_steps=8)
            with self.assertRaisesRegex(ValueError, "conflicting"):
                train_network("D1_ddm_crps", self.z + .1, self.mu, self.y + .21,
                              self.sigma, float(np.quantile(self.y, .8)), "max",
                              self.config, 7, Path(temp), fixed_steps=8)

    def test_mid_update_interrupt_resumes_from_last_coherent_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "interrupted"
            full_dir = Path(temp) / "full"
            original_step = torch.optim.AdamW.step
            calls = 0

            def interrupted_step(optimizer, *args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 15:
                    # Emulate CTRL+C after random training inputs and backward,
                    # before the update completes. Saving this state would skip
                    # a partially completed step on resume.
                    raise KeyboardInterrupt("synthetic mid-update interruption")
                return original_step(optimizer, *args, **kwargs)

            with mock.patch.object(torch.optim.AdamW, "step", interrupted_step):
                with self.assertRaises(KeyboardInterrupt):
                    self.fit(directory, 24)
            saved = torch.load(directory / "last.pt", weights_only=False)
            self.assertEqual(saved["step"], 8)
            self.assertTrue((directory / "error.json").exists())
            resumed_result = self.fit(directory, 24)
            self.assertEqual(resumed_result["resume_from_step"], 8)
            self.fit(full_dir, 24)
            resumed = torch.load(directory / "last.pt", weights_only=False)
            full = torch.load(full_dir / "last.pt", weights_only=False)
            for key in full["model_state"]:
                torch.testing.assert_close(full["model_state"][key], resumed["model_state"][key], rtol=0, atol=0)

    def test_all_families_train_checkpoint_and_sample_finite(self):
        with tempfile.TemporaryDirectory() as temp:
            for model in ["D0_ddpm", "C0_direct_crps", "D1_ddm_crps", "D2_ddm_tail"]:
                with self.subTest(model=model):
                    directory = Path(temp) / model
                    result = self.fit(directory, 4, model)
                    self.assertEqual(result["steps"], 4)
                    self.assertTrue((directory / "history.csv").is_file())
                    loaded, payload = load_network(directory / "best.pt", "cpu")
                    self.assertIn("optimizer_state", payload)
                    self.assertIn("rng_states", payload)
                    draws = sample_network(directory / "best.pt", 100, 1, "cpu")
                    self.assertTrue(np.isfinite(draws).all())


if __name__ == "__main__":
    unittest.main()
