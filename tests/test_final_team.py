"""Contrôles scientifiques ciblés du rendu commun."""
import numpy as np
from numpy.testing import assert_allclose
from scipy.stats import t

from sma.final_models import bayes_fit, bayes_parameters, mixture_sample, quantile_sample
from sma.scores import crps_rows, twcrps_rows


def test_crps_matches_pairwise_definition_and_degenerate_case():
    x = np.array([[1., 2., 5.], [3., 3., 3.]])
    y = np.array([2., 5.])
    exact = abs(x-y[:, None]).mean(1)-.5*abs(x[:, :, None]-x[:, None, :]).mean((1,2))
    assert_allclose(crps_rows(x,y), exact, atol=1e-14)
    assert crps_rows(x,y)[1] == 2


def test_tail_score_penalizes_false_alarms_too():
    # Une observation froide n'annule pas le coût d'une prévision trop chaude.
    assert twcrps_rows([[10., 10.]], [0.], 5., "max")[0] == 5.
    assert twcrps_rows([[-10., -10.]], [0.], -5., "min")[0] == 5.


def test_mixture_is_not_an_average_and_endpoints_are_exact():
    a, b = np.full((2,100), -2.), np.full((2,100), 2.)
    mixed = mixture_sample(a,b,.25)
    assert_allclose((mixed==-2).mean(1), .25)
    assert set(np.unique(mixed)) == {-2.,2.}
    assert_allclose(mixture_sample(a,b,0),b)
    assert_allclose(mixture_sample(a,b,1),a)


def test_bayes_joint_rejection_matches_truncated_student_marginal():
    rng = np.random.default_rng(42)
    co2 = np.linspace(310,390,61)
    y = 25+.2*(np.log(co2)-np.log(co2).mean())+rng.normal(size=61)
    state=bayes_fit(co2,y)
    _,b,sig=bayes_parameters(state,120000,np.random.default_rng(3))
    assert np.min(b)>=0
    beta,V=np.asarray(state['beta']),np.asarray(state['V'])
    scale=np.sqrt(state['rss']/state['df']*V[1,1])
    p0=t.cdf(-beta[1]/scale,state['df'])
    expected=beta[1]+scale*t.ppf(p0+np.array([.1,.5,.9])*(1-p0),state['df'])
    assert_allclose(np.quantile(b,[.1,.5,.9]),expected,atol=.05)
    assert np.isfinite(sig).all() and (sig>0).all()


def test_quantile_interpolation_is_monotone_and_announces_tails():
    state=dict(center=350,scale=10,tau=[.01,.5,.99],intercept=[2.,0.,1.],slope=[0.,0.,0.])
    uniforms=np.array([[0,.01,.5,.99,1.]])
    samples=quantile_sample(state,[350],uniforms)
    assert_allclose(samples,[[-1.,0.,1.,2.,3.]])
    assert np.all(np.diff(samples)>=0)
