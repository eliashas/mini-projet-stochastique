"""Construit le notebook final à partir du notebook du prof : ses cellules sont gardées, les `### TO DO ###`
sont remplacées par notre code et nos commentaires (fichier commentaires.py).

    python build.py      # écrit rendu_final_groupe.ipynb (non exécuté)
"""
import json
from pathlib import Path

ICI = Path(__file__).parent
PROF = ICI / 'sujet_prof.ipynb'   # notebook fourni par le prof
SORTIE = ICI / 'rendu_final_groupe.ipynb'
from commentaires import C

md = lambda s: {'cell_type': 'markdown', 'metadata': {}, 'source': s.strip()}
code = lambda s: {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': s.strip()}
com = lambda k: md(C.get(k, f'_(commentaire à écrire : {k})_'))

IMPORTS = r'''
%matplotlib inline
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
from sklearn.linear_model import QuantileRegressor

# Si les CSV ne sont pas à côté du notebook (Colab par exemple), on les télécharge depuis notre dépôt
URL = 'https://raw.githubusercontent.com/eliashas/mini-projet-stochastique/final/rendu_final_concis/'
for f in ['daily_temp_brest.csv', 'yearly_temp_brest.csv', 'yearly_future_co2.csv']:
    if not Path(f).exists():
        urllib.request.urlretrieve(URL + f, f)

rng = np.random.default_rng(0)   # graines fixées : mêmes résultats à chaque exécution
torch.manual_seed(0)
plt.rcParams.update({'figure.figsize': (11, 4), 'axes.grid': True, 'grid.alpha': .3})
'''

# ------------------------------------------------------------------ partie 1
SAISON = r'''
d = daily_temp_brest.assign(date=pd.to_datetime(daily_temp_brest.valid_time))
d = d[~((d.date.dt.month == 2) & (d.date.dt.day == 29))].copy()   # on enlève les 29 février : 365 jours par an
d['jour'] = d.groupby(d.date.dt.year).cumcount() + 1

q = d.groupby('jour')['mean'].quantile([.1, .5, .9]).unstack()
q.columns = ['q10', 'q50', 'q90']
# moyenne glissante sur 31 jours, circulaire (le 31 décembre est suivi du 1er janvier)
lisse = lambda s: pd.concat([s.iloc[-15:], s, s.iloc[:15]]).rolling(31, center=True).mean().iloc[15:-15]
qs = q.apply(lisse)

fig, ax = plt.subplots()
for c, col in zip(qs, ['tab:blue', 'k', 'tab:red']):
    ax.plot(q.index, q[c], color=col, lw=.6, alpha=.35)
    ax.plot(qs.index, qs[c], color=col, lw=2, label=f'quantile {c[1:]} % (lissé)')
ax.set(xlabel='Jour de l\'année', ylabel='Température moyenne journalière (°C)', xlim=(1, 365),
       title='Cycle saisonnier à Brest (ERA5, 1940-2025)')
ax.legend()
plt.show()
print(qs.agg(['min', 'idxmin', 'max', 'idxmax']).round(1))
'''

VAGUES = r'''
DUREE_MIN = 3   # une vague = au moins 3 jours chauds consécutifs

d = d.join(qs, on='jour')
d['chaud'] = d['mean'] > d.q90                    # jour plus chaud que le quantile 90 % de son jour de l'année
d['anomalie'] = d['mean'] - d.q50                 # écart à la médiane du jour (°C)
d['bloc'] = (d.chaud != d.chaud.shift()).cumsum()  # même numéro pour des jours consécutifs de même statut

vagues = (d[d.chaud].groupby('bloc')
          .agg(debut=('date', 'first'), duree=('chaud', 'size'), intensite=('anomalie', 'mean'))
          .query('duree >= @DUREE_MIN')
          .assign(annee=lambda v: v.debut.dt.year)
          .reset_index(drop=True))

print(f'{len(vagues)} vagues de chaleur de 1940 à 2025')
print('\nLes plus longues :\n', vagues.nlargest(4, 'duree').round({'intensite': 2}).to_string(index=False))
print('\nLes plus intenses :\n', vagues.nlargest(4, 'intensite').round({'intensite': 2}).to_string(index=False))
'''

NUAGE = r'''
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.5), gridspec_kw={'width_ratios': [1.6, 1]})
sc = a1.scatter(vagues.duree, vagues.intensite, c=vagues.annee, cmap='plasma', s=25, edgecolor='k', lw=.3)
fig.colorbar(sc, ax=a1, label='Année')
a1.set(xlabel='Durée (jours)', ylabel='Intensité : anomalie moyenne (°C)', title='Vagues de chaleur à Brest')

decennie = vagues.annee // 10 * 10
nb_annees = pd.Series(range(1940, 2026)).floordiv(10).mul(10).value_counts()   # la décennie 2020 n'a que 6 ans
(decennie.value_counts() / nb_annees).sort_index().plot.bar(ax=a2, rot=0, color='tab:red')
a2.set(xlabel='Décennie', ylabel='Vagues par an', title='Fréquence des vagues')
plt.tight_layout()
plt.show()
'''

# ------------------------------------------------------------------ partie 2
TMAX = r'''
y = yearly_temp_brest.assign(annee=pd.to_datetime(yearly_temp_brest.valid_time).dt.year)

fig, ax = plt.subplots()
ax.plot(y.annee, y['max'], 'o-', ms=3, lw=1, color='tab:red', label='Maximum annuel')
ax.plot(y.annee, y['max'].rolling(11, center=True).mean(), lw=2.5, color='k', label='Moyenne glissante sur 11 ans')
ax.set(xlabel='Année', ylabel='Température (°C)', title='Température maximale annuelle à Brest')
ax.legend()
plt.show()
for a, b in [(1940, 1979), (1980, 2025)]:
    s = y.loc[y.annee.between(a, b), 'max']
    print(f'{a}-{b} : moyenne {s.mean():.1f} °C, écart-type {s.std():.1f} °C')
'''

CORREL = r'''
T = {'T brute': y['max']} | {f'T lissée {w} ans': y['max'].rolling(w, center=True).mean() for w in (5, 11, 21)}
CO2 = {'CO2': y.co2, 'ln(CO2)': np.log(y.co2), 'CO2²': y.co2**2}
print('Corrélation de Pearson entre Tmax annuelle et CO2 (1940-2025) :')
print(pd.DataFrame({c: {t: T[t].corr(CO2[c]) for t in T} for c in CO2}).round(2))
'''

METHODE = r'''
## Notre approche

On modélise la loi de la température extrême de l'année $t$ sachant le CO2 $C_t$ (ppm), avec la variable
$x_t=\ln(C_t/280)$ (l'effet de serre du CO2 est logarithmique, 280 ppm = niveau préindustriel).
Chaque modèle donne une **loi**, qu'on représente par $N=10\,000$ tirages Monte-Carlo par année.
On compare cinq modèles, chacun proposé par un membre du groupe :

1. **Référence** : $T_t=a+b\,x_t+\sigma\varepsilon_t$, $\varepsilon_t\sim\mathcal N(0,1)$, ajusté par moindres carrés.
2. **Régression bayésienne** (Christian) : même modèle, avec un a priori $p(a,b,\sigma^2)\propto\sigma^{-2}\mathbf 1_{b\ge0}$.
   On tire $\sigma^2\sim \mathrm{RSS}/\chi^2_{n-2}$ puis $(a,b)\mid\sigma^2\sim\mathcal N\big(\hat\beta,\sigma^2(X^\top X)^{-1}\big)$,
   en rejetant les tirages avec $b<0$. Chaque tirage de paramètres sert ensuite à tirer une année. L'incertitude sur
   la pente est ainsi prise en compte, ce qui compte beaucoup quand on extrapole jusqu'à 946 ppm.
3. **Régression quantile** (Yazid) : pour $\tau=0{,}01,\dots,0{,}99$, une droite $q_\tau(x)=a_\tau+b_\tau x$ minimise la
   perte pinball $\sum_i\rho_\tau(T_i-a_\tau-b_\tau x_i)+\alpha|b_\tau|$, avec $\rho_\tau(u)=u(\tau-\mathbf 1_{u<0})$.
   On trie les 99 quantiles (pour éviter qu'ils se croisent) puis on tire $U\sim\mathcal U(0,1)$ et $T=q_U(x)$ par interpolation.
4. **GEV non stationnaire** (Reda, pour les maxima) : la théorie des valeurs extrêmes dit que le maximum de nombreuses
   valeurs suit une loi GEV,
   $$F(t)=\exp\Big\{-\big[1+\xi\tfrac{t-\mu_t}{\sigma}\big]^{-1/\xi}\Big\},\qquad \mu_t=\beta_0+\beta_1x_t .$$
   Les paramètres $(\beta_0,\beta_1,\log\sigma,\xi)$ minimisent la log-vraisemblance négative avec PyTorch (Adam),
   avec $\beta_1\ge0$ et $\xi\in[-0{,}5;-0{,}01]$ (queue bornée, classique pour des températures). On entraîne
   200 modèles sur des rééchantillonnages bootstrap des années pour avoir l'incertitude sur les paramètres, puis on
   tire par inversion : $T=\mu+\frac\sigma\xi\big[(-\ln U)^{-\xi}-1\big]$.
   Pour les minima, Reda utilise plutôt un **bootstrap des résidus** de la droite (aucune loi supposée).
5. **Générateur neuronal entraîné au CRPS** (Elias) : $T_t=a+b\,x_t+s\,g_\phi(\eta)$, où $g_\phi$ est un petit réseau
   (2 couches de 32 neurones) qui transforme un bruit $\eta\sim\mathcal N(0,I_2)$ en résidu. Il est entraîné en
   minimisant le CRPS de ses tirages (32 tirages par année observée) :
   $$\mathcal L=\frac1M\sum_m|\hat T_m-T|-\frac{1}{2M(M-1)}\sum_{m\ne l}|\hat T_m-\hat T_l| .$$
   Le réseau apprend donc la forme des résidus sans hypothèse de loi. La droite $(a,b)$ est rééchantillonnée par
   bootstrap pour garder l'incertitude sur la tendance.

**Score.** On compare les modèles avec le CRPS (en °C, plus c'est bas mieux c'est), qui mesure l'écart entre toute la
loi prédite $F$ et la valeur observée $y$ :
$$\mathrm{CRPS}(F,y)=\mathbb E|X-y|-\tfrac12\mathbb E|X-X'|,\qquad X,X'\sim F\ \text{indépendants}.$$

**Choix du modèle.** On découpe 1971–2000 en trois blocs de 10 ans ; chaque bloc est prédit par le modèle ajusté sur
toutes les années d'avant (**validation**), et on retient le modèle qui a le meilleur CRPS moyen. Si plusieurs
modèles sont à moins de 0,01 °C du meilleur, on prend le plus simple (dans l'ordre de la liste ci-dessus) : un
écart aussi petit change d'une graine aléatoire à l'autre, il ne veut rien dire. Pour vérifier ce choix, on ajuste ensuite sur 1940–2000 et on note sur 2001–2025
(**test**, des années plus riches en CO2 que tout l'entraînement). Les projections jusqu'en 2100 utilisent enfin le
modèle retenu, réajusté sur 1940–2025.
'''

MODELES = r'''
C0, N = 280, 10_000

def fit_ref(x, t):
    b, a = np.polyfit(x, t, 1)
    return a, b, np.std(t - a - b * x, ddof=2)

def tirer_ref(m, x, n=N):
    a, b, s = m
    return a + b * x + s * rng.standard_normal((n, len(x)))

def fit_bayes(x, t):                               # Christian
    X = np.c_[np.ones_like(x), x]
    V = np.linalg.inv(X.T @ X)
    beta = V @ X.T @ t
    return beta, V, np.sum((t - X @ beta) ** 2), len(t) - 2

def tirer_bayes(m, x, n=N):
    beta, V, rss, ddl = m
    tirs = []
    while sum(len(v) for v in tirs) < n:
        s = np.sqrt(rss / rng.chisquare(ddl, n))
        ab = beta + s[:, None] * rng.standard_normal((n, 2)) @ np.linalg.cholesky(V).T
        tirs.append(np.c_[ab, s][ab[:, 1] >= 0])  # rejet des pentes négatives
    a, b, s = np.concatenate(tirs)[:n].T[:, :, None]
    return a + b * x + s * rng.standard_normal((n, len(x)))

TAU = np.arange(1, 100) / 100
def fit_qr(x, t, alpha=0):                         # Yazid
    xm, xs = x.mean(), x.std()                     # x centré-réduit pour que la pénalité ait du sens
    f = [QuantileRegressor(quantile=q, alpha=alpha, solver='highs').fit(((x - xm) / xs)[:, None], t) for q in TAU]
    return xm, xs, np.array([r.intercept_ for r in f]), np.array([r.coef_[0] for r in f])

def tirer_qr(m, x, n=N):
    xm, xs, a, b = m
    q = np.sort(a + np.outer((x - xm) / xs, b), axis=1)   # tri : les quantiles ne se croisent plus
    u = rng.random((n, len(x)))
    return np.stack([np.interp(u[:, i], TAU, q[i]) for i in range(len(x))], axis=1)

def fit_gev(x, t, B=200, pas=3000):                # Reda
    x, t = torch.tensor(x), torch.tensor(t)
    i = torch.randint(len(t), (B, len(t)))
    i[0] = torch.arange(len(t))                    # le modèle 0 est ajusté sur les vraies données
    xb, tb = x[i], t[i]
    theta = torch.tensor([t.mean().item(), 0., t.std().log().item(), -.1], dtype=torch.float64).repeat(B, 1)
    theta.requires_grad_()
    opt = torch.optim.Adam([theta], lr=.02)
    for _ in range(pas):
        b0, b1, log_s, xi = theta.T[:, :, None]
        z = (1 + xi * (tb - b0 - b1 * xb) / log_s.exp()).clamp_min(1e-6)
        nll = (log_s + (1 + 1 / xi) * z.log() + z ** (-1 / xi)).sum()
        opt.zero_grad(); nll.backward(); opt.step()
        with torch.no_grad():
            theta[:, 1].clamp_(min=0)              # plus de CO2 ne refroidit pas
            theta[:, 3].clamp_(-.5, -.01)
    return theta.detach().numpy()

def tirer_gev(theta, x, n=N):
    b0, b1, log_s, xi = theta[rng.integers(len(theta), size=n)].T[:, :, None]
    return b0 + b1 * x + np.exp(log_s) / xi * ((-np.log(rng.random((n, len(x))))) ** (-xi) - 1)

def bootstrap_droites(x, t, B=200):
    i = [np.arange(len(t))] + [rng.integers(len(t), size=len(t)) for _ in range(B - 1)]
    return [np.polyfit(x[j], t[j], 1)[::-1] for j in i] , i

def fit_residus(x, t):                             # Reda (minima)
    droites, i = bootstrap_droites(x, t)
    return [(a, b, t[j] - a - b * x[j]) for (a, b), j in zip(droites, i)]

def tirer_residus(m, x, n=N):
    out = np.empty((n, len(x)))
    for k, j in enumerate(rng.integers(len(m), size=n)):
        a, b, r = m[j]
        out[k] = a + b * x + rng.choice(r, size=len(x))
    return out

def crps_torch(X, y):
    M = X.shape[1]
    return ((X - y[:, None]).abs().mean()
            - (X[:, :, None] - X[:, None, :]).abs().sum((1, 2)).mean() / (2 * M * (M - 1)))

def fit_nn(x, t, pas=1500):                        # Elias
    a, b, s = fit_ref(x, t)
    z = torch.tensor((t - a - b * x) / s, dtype=torch.float32)   # résidus réduits
    torch.manual_seed(0)
    g = torch.nn.Sequential(torch.nn.Linear(2, 32), torch.nn.SiLU(), torch.nn.Linear(32, 32), torch.nn.SiLU(),
                            torch.nn.Linear(32, 1))
    opt = torch.optim.Adam(g.parameters(), lr=1e-3)
    for _ in range(pas):
        zb = z[torch.randint(len(z), (64,))]
        perte = crps_torch(g(torch.randn(64, 32, 2)).squeeze(-1), zb)
        opt.zero_grad(); perte.backward(); opt.step()
    return g, s, np.array(bootstrap_droites(x, t)[0])

def tirer_nn(m, x, n=N):
    g, s, droites = m
    with torch.no_grad():
        z = g(torch.randn(n, len(x), 2)).squeeze(-1).numpy()
    a, b = droites[rng.integers(len(droites), size=n)].T
    return a[:, None] + b[:, None] * x + s * z

def crps(tirages, obs):
    """CRPS moyen (°C) ; tirages (n, nb_années), obs (nb_années,)."""
    s = np.sort(tirages, axis=0)
    n = len(s)
    w = (2 * np.arange(1, n + 1) - n - 1) / n**2
    return np.mean(np.abs(s - obs).mean(axis=0) - w @ s)

MODELES = {'max': {'Référence': (fit_ref, tirer_ref), 'Bayes': (fit_bayes, tirer_bayes), 'Quantiles': (fit_qr, tirer_qr),
                   'GEV': (fit_gev, tirer_gev), 'Neuronal': (fit_nn, tirer_nn)}}
# pour les minima, le bootstrap des résidus de Reda remplace la GEV (ordre = du plus simple au plus complexe)
MODELES['min'] = {k: v for k, v in MODELES['max'].items() if k != 'GEV'}
MODELES['min'] = {**dict(list(MODELES['min'].items())[:3]), 'Bootstrap résidus': (fit_residus, tirer_residus),
                  'Neuronal': (fit_nn, tirer_nn)}
'''

COMPARAISON = r'''
x = np.log(y.co2.to_numpy() / C0)
# validation : 3 blocs de 10 ans, chacun prédit avec les années d'avant ; test : 2001-2025 appris sur 1940-2000
blocs = [(y.annee < a, y.annee.between(a, a + 9)) for a in (1971, 1981, 1991)]
test = (y.annee <= 2000, y.annee > 2000)

def comparer(var):
    t = y[var].to_numpy()
    score = lambda fit, tirer, a, b: crps(tirer(fit(x[a], t[a]), x[b]), t[b])
    res = pd.DataFrame({nom: {'validation 1971-2000': np.mean([score(f, g, a, b) for a, b in blocs]),
                              'test 2001-2025': score(f, g, *test)}
                        for nom, (f, g) in MODELES[var].items()}).T.sort_values('validation 1971-2000')
    # écart < 0,01 °C = pas significatif (ça change d'une graine à l'autre) : on garde alors le plus simple
    meilleur = res['validation 1971-2000'].min()
    choix = next(nom for nom in MODELES[var] if res.loc[nom, 'validation 1971-2000'] < meilleur + 0.01)
    print(f'CRPS (°C) pour T{var} :\n{res.round(3)}\n=> modèle retenu : {choix}')
    return choix

choix_max = comparer('max')
'''

PROJ = r'''
futur = yearly_future_co2.assign(annee=pd.to_datetime(yearly_future_co2.valid_time).dt.year)
SSP = {'ssp1-2.6': 'tab:green', 'ssp2-4.5': 'tab:orange', 'ssp5-8.5': 'tab:red'}

def projeter(var, nom):
    """Réajuste le modèle sur 1940-2025 et tire 10 000 trajectoires 2026-2100 par scénario."""
    fit, tirer = MODELES[var][nom]
    m = fit(x, y[var].to_numpy())
    return {s: tirer(m, np.log(futur[s].to_numpy() / C0)) for s in SSP}

def tracer(var, sims, seuil):
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(y.annee, y[var], 'k.-', lw=.8, ms=4, label='ERA5 1940-2025')
    for s, col in SSP.items():
        q5, q50, q95 = np.percentile(sims[s], [5, 50, 95], axis=0)
        ax.fill_between(futur.annee, q5, q95, color=col, alpha=.15)
        ax.plot(futur.annee, q50, color=col, lw=2, label=f'{s.upper()} : médiane et intervalle 5-95 %')
    ax.axhline(seuil, color='grey', ls='--', lw=1)
    ax.set(xlabel='Année', ylabel=f'T{var} annuelle (°C)', title=f'Projections de la T{var} annuelle à Brest')
    ax.legend(loc='upper left', fontsize=8)
    plt.show()

sims_max = projeter('max', choix_max)
tracer('max', sims_max, 40)
'''

DIST = r'''
def resume_2100(sims, seuil, au_dessus=True):
    lignes = {}
    for s, t in sims.items():
        ev = t > seuil if au_dessus else t < seuil
        lignes[s.upper()] = {'CO2 2100 (ppm)': futur[s].iloc[-1],
                             **{f'q{p} 2100 (°C)': np.percentile(t[:, -1], p) for p in (5, 50, 95)},
                             f'P(T 2100 {">" if au_dessus else "<"} {seuil} °C)': ev[:, -1].mean(),
                             'P(au moins une fois 2026-2100)': ev.any(axis=1).mean()}
    return pd.DataFrame(lignes).T

fig, ax = plt.subplots(figsize=(9, 4))
for s, col in SSP.items():
    ax.hist(sims_max[s][:, -1], np.arange(18, 46, .25), density=True, histtype='stepfilled', alpha=.35,
            color=col, label=s.upper())
ax.axvline(40, color='grey', ls='--', label='40 °C')
ax.set(xlabel='Tmax annuelle en 2100 (°C)', ylabel='Densité de probabilité (1/°C)',
       title=f'Loi de la Tmax en 2100 ({choix_max}, 10 000 tirages)')
ax.legend()
plt.show()
print(resume_2100(sims_max, 40).round(4).to_string())

def selon_modele(var, seuil, au_dessus=True):
    """Même calcul avec les autres modèles, pour voir à quel point le résultat en dépend."""
    lignes = {}
    for nom in MODELES[var]:
        t = projeter(var, nom)['ssp5-8.5'][:, -1]
        lignes[nom] = {'médiane 2100 SSP5-8.5 (°C)': np.median(t),
                       f'P(T 2100 {">" if au_dessus else "<"} {seuil} °C), SSP5-8.5': np.mean(t > seuil if au_dessus else t < seuil)}
    print(pd.DataFrame(lignes).T.round(3).to_string())

print()
selon_modele('max', 40)
'''

MINIMA = r'''
print(f"Corrélation Tmin / ln(CO2) : {y['min'].corr(np.log(y.co2)):.2f}\n")
choix_min = comparer('min')
sims_min = projeter('min', choix_min)
tracer('min', sims_min, 0)
print(resume_2100(sims_min, 0, au_dessus=False).round(3).to_string())
print()
selon_modele('min', 0, au_dessus=False)
'''

# ------------------------------------------------------------------ assemblage
prof = json.loads(PROF.read_text())
todo = iter([
    [code(SAISON), com('saison')],
    [code(VAGUES), com('vagues')],
    [code(NUAGE), com('nuage')],
    [code(TMAX), com('tmax')],
    [code(CORREL), com('correl')],
    [md(METHODE), code(MODELES), code(COMPARAISON), com('comparaison'), code(PROJ), com('proj')],
    [code(DIST), com('dist')],
    [code(MINIMA), com('minima'), com('conclusion')],
])
cells = []
for c in prof['cells']:
    src = ''.join(c['source'])
    if src.strip() == '### TO DO ###':
        cells += next(todo)
    elif '%pylab' in src:
        cells.append(code(IMPORTS))
    elif src.startswith('The five students are'):
        cells.append(md(C['membres']))
    else:
        cells.append({**c, 'outputs': [], 'execution_count': None} if c['cell_type'] == 'code' else c)
nb = {**prof, 'cells': cells,
      'metadata': {'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'},
                   'language_info': {'name': 'python'}}}
SORTIE.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print('écrit :', SORTIE)
