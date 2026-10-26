"""Construit le notebook rendu à partir du notebook du prof : les cellules du prof sont gardées telles quelles,
les cellules `### TO DO ###` sont remplacées par notre code, et on ajoute nos explications et commentaires.

    python build_notebook.py            # écrit miniprojet_MCE_SMA_2026_groupe.ipynb (non exécuté)
"""
import json
from pathlib import Path

ICI = Path(__file__).parent
PROF = ICI.parent / 'sujet_prof' / 'miniprojet_MCE_SMA_2026_students.ipynb'
SORTIE = ICI / 'miniprojet_MCE_SMA_2026_groupe.ipynb'
COMMENTS = json.loads((ICI / 'comments.json').read_text()) if (ICI / 'comments.json').exists() else {}

md = lambda s: {'cell_type': 'markdown', 'metadata': {}, 'source': s.strip()}
code = lambda s: {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': s.strip()}
comment = lambda key: md(COMMENTS.get(key, f'**Comment.** _(à rédiger : {key})_'))

# ---------------------------------------------------------------- imports
IMPORTS = r'''
%matplotlib inline
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import torch

torch.manual_seed(0)
rng = np.random.default_rng(0)  # fixed seeds: the notebook gives the same numbers at every run
plt.rcParams.update({'figure.figsize': (11, 4), 'axes.grid': True, 'grid.alpha': .3})
'''

# ---------------------------------------------------------------- part 1
SEASONAL = r'''
d = daily_temp_brest.assign(date=pd.to_datetime(daily_temp_brest.valid_time))
d = d[~((d.date.dt.month == 2) & (d.date.dt.day == 29))].copy()  # drop 29 February -> 365 days every year
d['doy'] = d.groupby(d.date.dt.year).cumcount() + 1               # day of year, from 1 to 365

# quantiles at 10%, 50%, 90% of the 86 values (1940-2025) available for each day of the year
q = d.groupby('doy')['mean'].quantile([.1, .5, .9]).unstack()
q.columns = ['q10', 'q50', 'q90']

# 1-month (31-day) centred rolling mean, made circular: 31 December is followed by 1 January
smooth = lambda s: pd.concat([s.iloc[-15:], s, s.iloc[:15]]).rolling(31, center=True).mean().iloc[15:-15]
qs = q.apply(smooth)

fig, ax = plt.subplots()
for c, col in zip(['q10', 'q50', 'q90'], ['tab:blue', 'k', 'tab:red']):
    ax.plot(q.index, q[c], color=col, lw=.6, alpha=.4)
    ax.plot(qs.index, qs[c], color=col, lw=2, label=f'{c[1:]}% quantile (smoothed)')
ax.fill_between(qs.index, qs.q10, qs.q90, color='grey', alpha=.15)
ax.set(xlabel='Day of the year', ylabel='Daily mean temperature (°C)', xlim=(1, 365),
       title='Seasonal cycle of the daily mean temperature in Brest (ERA5, 1940-2025)')
ax.legend()
plt.show()
print(qs.agg(['min', 'idxmin', 'max', 'idxmax']).round(1))
'''

HEATWAVES = r'''
MIN_DURATION = 3  # a heat wave = at least 3 consecutive hot days

d = d.join(qs, on='doy')
d['hot'] = d['mean'] > d.q90                      # hot day: above the smoothed 90% quantile of its day
d['anomaly'] = d['mean'] - d.q50                  # anomaly w.r.t. the "normal" day (smoothed median), in °C
d['run'] = (d.hot != d.hot.shift()).cumsum()      # same label for consecutive days with the same status

waves = (d[d.hot].groupby('run')
         .agg(start=('date', 'first'), duration=('hot', 'size'), intensity=('anomaly', 'mean'))
         .query('duration >= @MIN_DURATION')
         .assign(year=lambda w: w.start.dt.year, month=lambda w: w.start.dt.month)
         .reset_index(drop=True))

print(f'{len(waves)} heat waves of at least {MIN_DURATION} days between 1940 and 2025')
print('\nLongest:\n', waves.nlargest(5, 'duration').round({'intensity': 2}).to_string(index=False))
print('\nMost intense:\n', waves.nlargest(5, 'intensity').round({'intensity': 2}).to_string(index=False))
'''

SCATTER = r'''
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.5), gridspec_kw={'width_ratios': [1.6, 1]})
sc = a1.scatter(waves.duration, waves.intensity, c=waves.year, cmap='plasma', s=25 + 4 * waves.duration,
                edgecolor='k', lw=.3)
fig.colorbar(sc, ax=a1, label='Year of appearance')
a1.set(xlabel='Duration (days)', ylabel='Intensity: mean anomaly (°C)', title='Heat waves in Brest, 1940-2025')

decade = (waves.year // 10) * 10
summer = waves.month.between(5, 9)
pd.crosstab(decade, summer.map({True: 'May-Sept.', False: 'Oct.-April'})).plot.bar(stacked=True, ax=a2, rot=0)
a2.legend(title=None)
a2.set(xlabel='Decade (2020s = 2020-2025 only)', ylabel='Number of heat waves', title='Heat waves per decade')
plt.tight_layout()
plt.show()
print(waves.groupby(decade)[['duration', 'intensity']].mean().round(2).T)
'''

# ---------------------------------------------------------------- part 2
YEARLY_PLOT = r'''
y = yearly_temp_brest.assign(year=pd.to_datetime(yearly_temp_brest.valid_time).dt.year)

fig, ax = plt.subplots()
ax.plot(y.year, y['max'], 'o-', ms=3, lw=1, color='tab:red', label='Annual maximum')
ax.plot(y.year, y['max'].rolling(11, center=True).mean(), lw=2.5, color='k', label='11-year rolling mean')
for _, r in y.nlargest(3, 'max').iterrows():
    ax.annotate(f"{r.year:.0f}: {r['max']:.1f} °C", (r.year, r['max']), xytext=(-70, -4), textcoords='offset points')
ax.set(xlabel='Year', ylabel='Temperature (°C)', title='Annual maximum temperature in Brest (ERA5)')
ax.legend()
plt.show()
for p in [(1940, 1979), (1980, 2025)]:
    s = y[y.year.between(*p)]
    print(f"{p[0]}-{p[1]}: mean {s['max'].mean():.2f} °C, std {s['max'].std():.2f} °C")
'''

CORRELATION = r'''
T_transforms = {'T': lambda s: s, **{f'T, {w}-yr rolling mean': (lambda w: lambda s: s.rolling(w, center=True).mean())(w)
                                       for w in (5, 11, 21)}}
C_transforms = {'CO2': y.co2, 'ln(CO2)': np.log(y.co2), 'ln(CO2/280)': np.log(y.co2 / 280)}

corr = pd.DataFrame({cn: {tn: f(y['max']).corr(c) for tn, f in T_transforms.items()}
                     for cn, c in C_transforms.items()})
print('Pearson correlation between annual max temperature and CO2 (1940-2025):')
print(corr.round(3))

fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(np.log(y.co2), y['max'], c=y.year, cmap='viridis', s=18, label='T')
ax.plot(np.log(y.co2), y['max'].rolling(11, center=True).mean(), 'k', lw=2, label='11-yr rolling mean of T')
ax.set(xlabel='ln(CO2 / 1 ppm)', ylabel='Annual maximum (°C)')
ax.legend()
plt.show()
'''

METHOD = r'''
## Our approach: a non-stationary GEV model, trained with PyTorch, with bootstrap Monte-Carlo

**Why a GEV distribution?** We want the distribution of an *annual maximum*, i.e. the maximum of 365 daily values.
The Fisher–Tippett–Gnedenko theorem (the "central limit theorem of extremes") states that, after normalisation,
the maximum of many random variables can only converge to one family of distributions: the
**Generalised Extreme Value** (GEV) law. Its cumulative distribution function is

$$
F(t;\mu,\sigma,\xi)=\exp\left\{-\left[1+\xi\,\frac{t-\mu}{\sigma}\right]^{-1/\xi}\right\},
\qquad 1+\xi\frac{t-\mu}{\sigma}>0,
$$

with a location $\mu$ (°C), a scale $\sigma>0$ (°C) and a shape $\xi$ (no unit). For temperature maxima, $\xi<0$:
the distribution has a finite upper bound $t_{\max}=\mu-\sigma/\xi$ (the atmosphere cannot heat up indefinitely).

**Conditioning on CO2.** The climate changes, so the law of year $t$ depends on the CO2 concentration $C_t$ (ppm).
The greenhouse effect of CO2 is logarithmic (the radiative forcing is $\Delta F \approx 5.35\,\ln(C/C_0)$ W/m²),
so the location moves linearly with $x_t=\ln(C_t/C_0)$, with $C_0=280$ ppm (pre-industrial level):

$$
T_t \mid C_t \sim \mathrm{GEV}\big(\mu_t,\ \sigma,\ \xi\big),\qquad \mu_t=\beta_0+\beta_1\,x_t,
\qquad \theta=(\beta_0,\beta_1,\log\sigma,\xi).
$$

$\beta_1$ (°C per unit of $\ln$ CO2) is the sensitivity of Brest's hottest day to CO2.

**Training (PyTorch).** The parameters minimise the negative log-likelihood on the observed years,
by gradient descent (Adam optimiser, automatic differentiation):

$$
\mathcal{L}(\theta)=\sum_{t}\left[\log\sigma+\left(1+\frac1\xi\right)\log z_t+z_t^{-1/\xi}\right],
\qquad z_t=1+\xi\,\frac{T_t-\mu_t}{\sigma},
$$

under two physical constraints, imposed at each gradient step: $\beta_1\ge 0$ (more CO2 cannot make the climate
colder) and $\xi\in[-0.5,-0.01]$ (bounded upper tail, as is standard for temperatures).

**Uncertainty on the parameters (bootstrap).** With only 86 years, $\theta$ is uncertain, and this uncertainty grows
when we extrapolate to 946 ppm. We therefore train $B=500$ models in parallel, each on a bootstrap sample of the years
(drawn with replacement), which gives $\theta^{(1)},\dots,\theta^{(B)}$. The predictive distribution is the mixture

$$
p(T\mid C)\approx\frac1B\sum_{b=1}^{B}\mathrm{GEV}\big(T;\ \beta_0^{(b)}+\beta_1^{(b)}\ln(C/C_0),\ \sigma^{(b)},\ \xi^{(b)}\big).
$$

**Monte-Carlo forecasts.** For each scenario we draw $N=10\,000$ trajectories 2026–2100: each trajectory picks one
model $b$ at random, then draws every year by inverting the CDF, with $U\sim\mathcal U(0,1)$:

$$
T=\mu+\frac{\sigma}{\xi}\Big[(-\ln U)^{-\xi}-1\Big].
$$

The output is not one value per year but an **ensemble of 10 000 possible futures**: any probability
(e.g. of exceeding 40 °C) is simply the fraction of members where the event happens.

**Why not a diffusion model or a deep network?** With 86 data points, a neural network with thousands of parameters would
overfit, and nothing guarantees a sensible behaviour at 946 ppm, far outside the training range. Our model keeps
the generative and Monte-Carlo spirit of modern probabilistic ML (PyTorch, gradient training, ensembles,
sampling) while having 4 parameters with a physical meaning and a form justified by extreme-value theory.

**Validation (out-of-sample).** Before using the model, we check it honestly: we train it on 1940–2000 only and predict
2001–2025 (a period with more CO2 than anything seen in training). The score is the CRPS
(Continuous Ranked Probability Score, in °C, lower is better), which compares a whole predicted distribution
to the observed value: $\mathrm{CRPS}(F,y)=\int\big(F(u)-\mathbf 1\{u\ge y\}\big)^2du
=\mathbb E|X-y|-\tfrac12\mathbb E|X-X'|$ with $X,X'\sim F$ independent.
'''

MODEL = r'''
C0 = 280.0  # pre-industrial CO2 (ppm)

def fit_gev(x, t, B=500, steps=3000):
    """Fit B GEV models (mu = b0 + b1 x) in parallel, each on a bootstrap sample of the years. Returns (B, 4)."""
    x, t = torch.tensor(x), torch.tensor(t)
    idx = torch.randint(len(t), (B, len(t)), generator=torch.Generator().manual_seed(0))
    idx[0] = torch.arange(len(t))                                     # model 0 = fit on the original data
    xb, tb = x[idx], t[idx]
    theta = torch.tensor([t.mean().item(), 0., t.std().log().item(), -.1], dtype=torch.float64).repeat(B, 1)
    theta.requires_grad_()
    opt = torch.optim.Adam([theta], lr=.02)
    for _ in range(steps):
        b0, b1, log_s, xi = theta.T[:, :, None]
        z = (1 + xi * (tb - b0 - b1 * xb) / log_s.exp()).clamp_min(1e-6)
        nll = (log_s + (1 + 1 / xi) * z.log() + z ** (-1 / xi)).sum()  # negative log-likelihood, all B models
        opt.zero_grad(); nll.backward(); opt.step()
        with torch.no_grad():
            theta[:, 1].clamp_(min=0)                                 # more CO2 cannot cool (b1 >= 0)
            theta[:, 3].clamp_(-.5, -.01)                             # bounded upper tail
    return theta.detach().numpy()

def sample_gev(theta, x, n=10_000):
    """n Monte-Carlo trajectories over the years x = ln(CO2/C0): each draws one bootstrap model. Returns (n, len(x))."""
    b0, b1, log_s, xi = theta[rng.integers(len(theta), size=n)].T[:, :, None]
    u = rng.random((n, len(x)))
    return b0 + b1 * x + np.exp(log_s) / xi * ((-np.log(u)) ** (-xi) - 1)

def crps(samples, obs):
    """Mean CRPS (°C): samples (n, n_years), obs (n_years,)."""
    s = np.sort(samples, axis=0)
    n = len(s)
    w = (2 * np.arange(1, n + 1) - n - 1) / n**2
    return np.mean(np.abs(s - obs).mean(axis=0) - w @ s)

# out-of-sample validation: train on 1940-2000, predict 2001-2025
x_all = np.log(y.co2.to_numpy() / C0)
train, test = y.year <= 2000, y.year > 2000
theta_val = fit_gev(x_all[train], y['max'][train].to_numpy())
b1, b0 = np.polyfit(x_all[train], y['max'][train], 1)              # baseline: linear trend + Gaussian noise
sd = np.std(y['max'][train] - b0 - b1 * x_all[train], ddof=2)
gauss = b0 + b1 * x_all[test] + sd * rng.standard_normal((10_000, test.sum()))
print(f"CRPS 2001-2025, GEV + bootstrap : {crps(sample_gev(theta_val, x_all[test]), y['max'][test].to_numpy()):.2f} °C")
print(f"CRPS 2001-2025, Gaussian linear : {crps(gauss, y['max'][test].to_numpy()):.2f} °C")
print(f"CRPS 2001-2025, constant 1940-2000 climatology: {crps(y['max'][train].to_numpy()[:, None], y['max'][test].to_numpy()):.2f} °C")

# final model: trained on all the data, 1940-2025
theta = fit_gev(x_all, y['max'].to_numpy())
print('\nFinal model (fit on 1940-2025): b0 = {:.2f} °C, b1 = {:.2f} °C, sigma = {:.2f} °C, xi = {:.2f}'
      .format(theta[0, 0], theta[0, 1], np.exp(theta[0, 2]), theta[0, 3]))
print('b1, 90% bootstrap interval: [{:.2f}, {:.2f}] °C per unit of ln(CO2)'.format(*np.percentile(theta[:, 1], [5, 95])))
'''

PROJECTION = r'''
future = yearly_future_co2.assign(year=pd.to_datetime(yearly_future_co2.valid_time).dt.year)
SSP = {'ssp1-2.6': 'tab:green', 'ssp2-4.5': 'tab:orange', 'ssp5-8.5': 'tab:red'}
sims_max = {s: sample_gev(theta, np.log(future[s].to_numpy() / C0)) for s in SSP}   # (10 000, 75) per scenario

fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 4.5), gridspec_kw={'width_ratios': [1.8, 1]})
a1.plot(y.year, y['max'], 'k.-', lw=.8, ms=4, label='ERA5 1940-2025')
for s, col in SSP.items():
    q5, q50, q95 = np.percentile(sims_max[s], [5, 50, 95], axis=0)
    a1.fill_between(future.year, q5, q95, color=col, alpha=.15)
    a1.plot(future.year, q50, color=col, lw=2, label=f'{s.upper()}: median and 5-95%')
    a2.plot(future.year, future[s], color=col, lw=2, label=s.upper())
a2.plot(y.year, y.co2, 'k', lw=2, label='observed')
a1.axhline(40, color='grey', ls='--', lw=1)
a1.set(xlabel='Year', ylabel='Annual maximum (°C)', title='Probabilistic projections of the annual maximum in Brest')
a2.set(xlabel='Year', ylabel='CO2 (ppm)', title='CO2 scenarios')
a1.legend(loc='upper left', fontsize=8); a2.legend(fontsize=8)
plt.tight_layout()
plt.show()
'''

DIST2100 = r'''
def summary_2100(sims, threshold, above=True):
    """Table of the 2100 distribution + probabilities of crossing a threshold (°C), for every scenario."""
    rows = {}
    for s, x in sims.items():
        hit = x > threshold if above else x < threshold
        rows[s.upper()] = {'CO2 2100 (ppm)': future[s].iloc[-1],
                           **{f'{p}% (°C)': np.percentile(x[:, -1], p) for p in (5, 50, 95)},
                           f'P(year 2100 {">" if above else "<"} {threshold} °C)': hit[:, -1].mean(),
                           'P(at least once in 2026-2100)': hit.any(axis=1).mean()}
    return pd.DataFrame(rows).T

fig, ax = plt.subplots(figsize=(9, 4))
bins = np.arange(20, 42, .25)
for s, col in SSP.items():
    ax.hist(sims_max[s][:, -1], bins, density=True, histtype='stepfilled', alpha=.35, color=col, label=s.upper())
ax.axvline(y['max'].max(), color='k', ls=':', label=f"record 1940-2025 ({y['max'].max():.1f} °C)")
ax.axvline(40, color='grey', ls='--', label='40 °C')
ax.set(xlabel='Annual maximum temperature in 2100 (°C)', ylabel='Probability density (1/°C)',
       title='Distribution of the annual maximum in 2100 (10 000 Monte-Carlo members)')
ax.legend()
plt.show()

x2100 = np.log(future[list(SSP)].iloc[-1].to_numpy() / C0)
upper_bound = theta[:, :1] + theta[:, 1:2] * x2100 - np.exp(theta[:, 2:3]) / theta[:, 3:4]  # mu - sigma/xi, (B, 3)
print(summary_2100(sims_max, 40).round(4).to_string())
print('\nMedian upper bound of the GEV in 2100 (°C):', dict(zip(SSP, np.median(upper_bound, axis=0).round(1))))
'''

MINIMA = r'''
# Different approach for the minima: linear trend in ln(CO2) + non-parametric Monte-Carlo
# (residuals resampled from the observed years, regression refitted on bootstrap samples of the years)
def fit_resample(x, t, B=500):
    fits = []
    for b in range(B):
        i = rng.integers(len(t), size=len(t)) if b else np.arange(len(t))
        slope, icpt = np.polyfit(x[i], t[i], 1)
        fits.append((icpt, slope, t[i] - icpt - slope * x[i]))
    return fits

def sample_resample(fits, x, n=10_000):
    out = np.empty((n, len(x)))
    for k, b in enumerate(rng.integers(len(fits), size=n)):
        icpt, slope, res = fits[b]
        out[k] = icpt + slope * x + rng.choice(res, size=len(x))
    return out

val = fit_resample(x_all[train], y['min'][train].to_numpy())
print(f"CRPS 2001-2025 (min), trained on 1940-2000: {crps(sample_resample(val, x_all[test]), y['min'][test].to_numpy()):.2f} °C")
fits_min = fit_resample(x_all, y['min'].to_numpy())
sims_min = {s: sample_resample(fits_min, np.log(future[s].to_numpy() / C0)) for s in SSP}

fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 4.5), gridspec_kw={'width_ratios': [1.8, 1]})
a1.plot(y.year, y['min'], 'k.-', lw=.8, ms=4, label='ERA5 1940-2025')
for s, col in SSP.items():
    q5, q50, q95 = np.percentile(sims_min[s], [5, 50, 95], axis=0)
    a1.fill_between(future.year, q5, q95, color=col, alpha=.15)
    a1.plot(future.year, q50, color=col, lw=2, label=f'{s.upper()}: median and 5-95%')
    a2.hist(sims_min[s][:, -1], np.arange(-10, 9, .5), density=True, histtype='stepfilled', alpha=.35, color=col,
            label=s.upper())
a1.axhline(0, color='grey', ls='--', lw=1)
a2.axvline(0, color='grey', ls='--', lw=1)
a1.set(xlabel='Year', ylabel='Annual minimum (°C)', title='Probabilistic projections of the annual minimum in Brest')
a2.set(xlabel='Annual minimum in 2100 (°C)', ylabel='Probability density (1/°C)', title='Distribution in 2100')
a1.legend(loc='upper left', fontsize=8); a2.legend(fontsize=8)
plt.tight_layout()
plt.show()

print('Pearson correlation of the annual minimum with ln(CO2): {:.2f}'.format(y['min'].corr(np.log(y.co2))))
print(f"Observed: {(y['min'] < 0).mean():.0%} of the years 1940-2025 had a minimum below 0 °C")
print(summary_2100(sims_min, 0, above=False).round(3).to_string())
'''

# ---------------------------------------------------------------- assemble
prof = json.loads(PROF.read_text())
cells = []
todo = iter([
    [code(SEASONAL), comment('seasonal')],
    [code(HEATWAVES), comment('heatwaves_def')],
    [code(SCATTER), comment('scatter')],
    [code(YEARLY_PLOT), comment('yearly')],
    [code(CORRELATION), comment('correlation')],
    [md(METHOD), code(MODEL), comment('model'), code(PROJECTION), comment('projection')],
    [code(DIST2100), comment('dist2100')],
    [code(MINIMA), comment('minima'), comment('conclusion')],
])
for c in prof['cells']:
    src = ''.join(c['source'])
    if src.strip() == '### TO DO ###':
        cells += next(todo)
    elif c['cell_type'] == 'code' and '%pylab' in src:
        cells.append(code(IMPORTS))
    elif src.startswith('The five students are'):
        cells.append(md(COMMENTS.get('students', src)))
    else:
        cells.append({**c, 'outputs': [], 'execution_count': None} if c['cell_type'] == 'code' else c)
nb = {**prof, 'cells': cells}
nb['metadata'] = {'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'},
                  'language_info': {'name': 'python'}}
SORTIE.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print('écrit :', SORTIE)
