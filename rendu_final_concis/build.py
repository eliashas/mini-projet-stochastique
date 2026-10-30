"""Construit le notebook final à partir du notebook du prof : ses cellules sont gardées, les `### TO DO ###`
sont remplacées par notre code et nos commentaires (fichier commentaires.py).

    python build.py      # écrit rendu_final_groupe.ipynb (non exécuté)
"""
import hashlib
import json
from pathlib import Path

ICI = Path(__file__).parent
PROF = ICI / 'sujet_prof.ipynb'   # notebook fourni par le prof
SORTIE = ICI / 'rendu_final_groupe.ipynb'
from commentaires import C
import diffusion as diffusion_etude

md = lambda s: {'cell_type': 'markdown', 'metadata': {}, 'source': s.strip()}
code = lambda s: {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': s.strip()}
com = lambda k: md(C.get(k, f'_(commentaire à écrire : {k})_'))

EMPREINTES_CSV = {
    'daily_temp_brest.csv': '0eb44f9adcf0e876d3ad017f4efbd540f24d40c1aaf2562c4f9648447ab16613',
    'yearly_temp_brest.csv': 'dc99cbcf4d7e485ab55f5a99cdd13e10ef7afb79230c4389240f759c84f8eb1f',
    'yearly_future_co2.csv': 'c39c3402b505eddbca00a00f50ae64c258c3b6e872ae8313db896d7233e8a0b5',
}
for nom, empreinte in EMPREINTES_CSV.items():
    contenu = (ICI / nom).read_bytes().replace(b'\r\n', b'\n')
    if hashlib.sha256(contenu).hexdigest() != empreinte:
        raise ValueError('Données du sujet modifiées : ' + nom)

IMPORTS = r"""
%matplotlib inline
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
from IPython.display import display

rng = np.random.default_rng(0)
plt.rcParams.update({'figure.figsize': (11, 4), 'axes.grid': True, 'grid.alpha': .3})
"""

# ------------------------------------------------------------------ partie 1
SAISON = r'''
# on enlève les 29 février pour avoir 365 jours chaque année
d = daily_temp_brest.copy()
d['date'] = pd.to_datetime(d['valid_time'])
d = d[d['date'].dt.strftime('%m-%d') != '02-29']
d['jour'] = d.groupby(d['date'].dt.year).cumcount() + 1   # numéro du jour dans l'année (1 à 365)

# quantiles 10 %, 50 % et 90 % de la température pour chaque jour de l'année
q = pd.DataFrame({'q10': d.groupby('jour')['mean'].quantile(0.1),
                  'q50': d.groupby('jour')['mean'].quantile(0.5),
                  'q90': d.groupby('jour')['mean'].quantile(0.9)})

# moyenne glissante sur 31 jours ; comme l'année est un cycle, on colle fin décembre
# avant janvier et début janvier après décembre pour lisser aussi les bords
q_etendu = pd.concat([q.tail(15), q, q.head(15)])
qs = q_etendu.rolling(31, center=True).mean().iloc[15:-15]

# en fin : quantiles bruts ; en épais : quantiles lissés
for nom, couleur in [('q10', 'tab:blue'), ('q50', 'black'), ('q90', 'tab:red')]:
    plt.plot(q[nom], color=couleur, lw=0.6, alpha=0.35)
    plt.plot(qs[nom], color=couleur, lw=2, label=f'quantile {nom[1:]} % (lissé)')
plt.xlim(1, 365)
plt.xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335],
           ['janv', 'févr', 'mars', 'avr', 'mai', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc'])
plt.yticks(range(2, 21))   # une graduation par °C pour lire les écarts entre courbes
plt.xlabel("Jour de l'année")
plt.ylabel('Température moyenne journalière (°C)')
plt.title('Cycle saisonnier à Brest (ERA5, 1940-2025)')
plt.legend()
plt.show()
'''

VAGUES = r'''
DUREE_MIN = 3   # on garde les vagues d'au moins 3 jours chauds consécutifs

d = d.join(qs, on='jour')                # on ajoute à chaque jour les quantiles lissés de sa date
d['chaud'] = d['mean'] > d['q90']        # jour plus chaud que le quantile 90 % de sa date
d['anomalie'] = d['mean'] - d['q50']     # écart au quantile 50 % de sa date (°C)

# on numérote les suites de jours consécutifs : le numéro change à chaque passage chaud <-> pas chaud
d['suite'] = (d['chaud'] != d['chaud'].shift()).cumsum()

# chaque suite de jours chauds est une vague : durée = nombre de jours, intensité = anomalie moyenne
vagues = d[d['chaud']].groupby('suite').agg(debut=('date', 'first'),
                                            duree=('chaud', 'size'),
                                            intensite=('anomalie', 'mean'))
vagues = vagues[vagues['duree'] >= DUREE_MIN]
vagues['annee'] = vagues['debut'].dt.year

print(len(vagues), 'vagues de chaleur de 1940 à 2025')
print('\nLes plus longues :\n', vagues.nlargest(4, 'duree').round({'intensite': 2}).to_string(index=False))
print('\nLes plus intenses :\n', vagues.nlargest(4, 'intensite').round({'intensite': 2}).to_string(index=False))
'''

NUAGE = r'''
plt.figure(figsize=(8, 5))
plt.scatter(vagues['duree'], vagues['intensite'], c=vagues['annee'], cmap='plasma', s=25, edgecolor='k', lw=0.3)
plt.colorbar(label='Année')
plt.xlabel('Durée (jours)')
plt.ylabel('Intensité : anomalie moyenne (°C)')
plt.title('Vagues de chaleur à Brest (1940-2025)')
plt.show()

# nombre moyen de vagues par an dans chaque décennie (la décennie 2020 ne compte que 6 ans, de 2020 à 2025)
par_decennie = vagues.groupby(vagues['annee'] // 10 * 10).size()
nb_annees = pd.Series(10, index=par_decennie.index)
nb_annees[2020] = 6
(par_decennie / nb_annees).plot.bar(rot=0, color='tab:red', figsize=(8, 3.5))
plt.xlabel('Décennie')
plt.ylabel('Vagues par an')
plt.title('Nombre de vagues de chaleur par an')
plt.show()
'''

# ------------------------------------------------------------------ partie 2
TMAX = r'''
y = yearly_temp_brest.copy()
y['annee'] = pd.to_datetime(y['valid_time']).dt.year

plt.plot(y['annee'], y['max'], 'o-', ms=3, lw=1, color='tab:red', label='Maximum annuel')
# moyenne glissante sur 11 ans pour voir la tendance sans les variations d'une année à l'autre
plt.plot(y['annee'], y['max'].rolling(11, center=True).mean(), lw=2.5, color='k', label='Moyenne glissante sur 11 ans')
plt.xlabel('Année')
plt.ylabel('Température (°C)')
plt.title('Température maximale annuelle à Brest (1940-2025)')
plt.legend()
plt.show()

print('Moyenne 1940-1979 :', round(y.loc[y['annee'] < 1980, 'max'].mean(), 1), '°C')
print('Moyenne 1980-2025 :', round(y.loc[y['annee'] >= 1980, 'max'].mean(), 1), '°C')
'''

CORREL = r'''
# transformations testées pour la température et pour le CO2
T = {'T': y['max'],
     'ln(T)': np.log(y['max']),
     'T lissée 5 ans': y['max'].rolling(5, center=True).mean(),
     'T lissée 11 ans': y['max'].rolling(11, center=True).mean(),
     'T lissée 21 ans': y['max'].rolling(21, center=True).mean()}
CO2 = {'CO2': y['co2'], 'ln(CO2)': np.log(y['co2']), 'CO2²': y['co2']**2}

# coefficient de corrélation linéaire pour chaque couple (température, CO2)
tableau = pd.DataFrame({c: {t: T[t].corr(CO2[c]) for t in T} for c in CO2})
print('Corrélation linéaire entre Tmax et CO2 (1940-2025) :')
print(tableau.round(2))
'''

METHODE = r'''
## Notre démarche

Nous développons deux approches de prévision probabiliste : la **régression bayésienne** de Christian et la
**diffusion distributionnelle** d'Elias. La première représente l'incertitude sur la tendance et sur la
variabilité annuelle avec un modèle paramétrique. La seconde apprend la distribution des fluctuations
avec un réseau de neurones. On présente leurs équations, leur code et leurs projections sous les trois
scénarios, puis on discute leurs différences. Les autres propositions du groupe complètent la comparaison.

### Contributions et protocole

- **Christian** : régression bayésienne en logarithme du CO₂ ; l'incertitude porte sur la droite et le bruit annuel.
- **Elias** : DDPM, débruiteur stochastique au CRPS, pondération des extrêmes et bootstrap de l'ancre.
- **Reda** : loi GEV, adaptée aux maxima ; pour les minima, on applique la méthode aux températures opposées.
- **Yazid** : régression quantile, avec 99 quantiles et correction de leur ordre.
- **Diae** : réseau donnant les poids, moyennes et écarts-types d'un mélange de trois gaussiennes.

Le protocole commun utilise des validations chronologiques à l'intérieur de 1940–2000, puis un réajustement
sur 1940–2000 pour comparer les prédictions aux 25 années 2001–2025. L'ancre, la normalisation et les seuils
sont ajustés sur l'entraînement. La section diffusion détaille les trois découpages et les variantes.
Les résultats archivés du protocole commun sont les suivants :

| Méthode | CRPS validation Tmax | CRPS test Tmax | CRPS validation Tmin | CRPS test Tmin |
|:--|--:|--:|--:|--:|
| Référence : ancre log + gaussienne | 1,176 | 1,708 | 1,219 | 1,064 |
| Régression bayésienne | 1,169 | **1,580** | 1,217 | **0,980** |
| Diffusion D1, ancre fixe | 1,123 | 1,701 | **1,168** | 1,036 |
| Diffusion D3, ancre bootstrap | **1,114** | 1,650 | 1,174 | 0,989 |
| GEV (maxima / minima opposés) | 1,165 | 1,680 | 1,241 | 1,100 |
| Régression quantile régularisée | 1,137 | 1,799 | 1,196 | 1,030 |

Les scores sont en °C ; plus ils sont faibles, mieux c'est. Les réseaux de Diae ont été étudiés dans sa
contribution (CRPS test annoncé : 1,85 / 1,18 °C), mais n'ont pas été réévalués sur ces trois validations.
Ils ne participent donc pas au choix sur validation de ce tableau.

**D3 pour Tmax et D1 pour Tmin sont retenus sur validation.** Bayes a le meilleur CRPS observé sur le test
parmi ces méthodes, sans que cela justifie de refaire le choix après lecture du test. Le test avait déjà été
consulté dans le groupe : sa comparaison est rétrospective. Les petites différences ne suffisent pas à prouver
qu'un modèle sera meilleur sur de nouvelles années.

### Pourquoi le CRPS ?

Une prévision probabiliste donne une distribution $F$, et non une valeur unique. Le CRPS la compare à
l'observation $y$ :

$$\mathrm{CRPS}(F,y)=\mathbb E|X-y|-\frac12\mathbb E|X-X'|,$$

où $X$ et $X'$ sont deux tirages indépendants de $F$. Le premier terme pénalise l'éloignement à l'observation ;
le second tient compte de la dispersion. L'ensemble du score encourage une distribution correctement placée
et dispersée. On calcule ce score pour chaque année, puis on prend la moyenne. Il est en °C.
Une prévision déterministe redonne l'erreur absolue. Les 10 000 tirages décrivent la loi prédite ; ils ne
remplacent pas les 25 années de test. On complète le CRPS par un score de queue et la couverture des intervalles.

## La régression bayésienne

**Notations.** $T_t$ est le Tmax de l'année $t$ (°C), $x_t=\ln(C_t)$ où $C_t$ est le CO2 de l'année (ppm), et
$T=(T_{1940},\dots,T_{2025})$ la liste des $n=86$ valeurs observées. Le signe « $\mid$ » se lit « sachant » et
« $\sim$ » se lit « suit la loi ».

**Le modèle.** Tmax est une droite en $\ln(\mathrm{CO_2})$ plus un bruit, qui représente la météo de l'année :
$$T_t=a+b\,x_t+\sigma\,\varepsilon_t,\qquad \varepsilon_t\sim\mathcal N(0,1)\ \text{indépendants}.$$
$a$ est la hauteur de la droite, $b$ sa pente, et $\sigma$ l'écart-type du bruit (de combien une année s'écarte en
général de la droite).

**Pourquoi $\ln(\mathrm{CO_2})$ ?** À la question précédente, CO2, $\ln(\mathrm{CO_2})$ et CO2² avaient la même corrélation
(0,30 à 0,32). Mais en 2100 avec SSP5-8.5 (946 ppm), une simple droite donne un Tmax moyen d'environ 33 °C avec
$\ln(\mathrm{CO_2})$, 38 °C avec CO2 et 48 °C avec CO2². On garde $\ln(\mathrm{CO_2})$ : l'effet du CO2 sur la température
est souvent représenté par un forçage radiatif logarithmique. Cela motive cette ancre parcimonieuse,
mais ne démontre pas que les extrêmes locaux suivent exactement cette loi. La sensibilité au choix de l'ancre
est une limite des projections.

**Pourquoi bayésien ?** Avec 86 années, on ne connaît pas $a$, $b$ et $\sigma$ exactement : la pente estimée vaut
environ $7{,}4 \pm 2{,}5$. Sur les CO2 observés, ça change peu de chose, mais à 946 ppm une petite erreur sur la pente
devient une grosse erreur sur la température. Au lieu de garder une seule droite (celle des moindres carrés), on met
une **loi de probabilité sur les paramètres**, qui dit quelles valeurs de $(a,b,\sigma)$ sont plausibles, et on en
tire **beaucoup**. On part d'un a priori non informatif, avec une seule contrainte : plus de CO2 ne refroidit pas.
$$p(a,b,\sigma^2)\propto\sigma^{-2}\,\mathbf 1_{b\ge0}.$$

**La loi a posteriori** (ce qu'on sait des paramètres après avoir vu les données). On note $X$ le tableau des données
(une colonne de 1 et une colonne $x_t$), $\hat\beta=(\hat a,\hat b)=(X^\top X)^{-1}X^\top T$ la droite des moindres carrés,
et $\mathrm{MSE}=\frac1n\sum_t(T_t-\hat a-\hat b\,x_t)^2$ l'erreur quadratique moyenne de cette droite. Avant le rejet des pentes négatives,
on utilise le résultat classique du modèle linéaire gaussien :
$$\sigma^2\mid T\sim\frac{n\cdot\mathrm{MSE}}{\chi^2_{n-2}},\qquad (a,b)\mid\sigma^2,T\sim\mathcal N\big(\hat\beta,\ \sigma^2(X^\top X)^{-1}\big).$$
Le $\chi^2_{n-2}$ vient du fait que la somme des carrés des écarts, divisée par $\sigma^2$, est une somme de carrés de
lois normales ($n-2$ car on a estimé deux paramètres, $a$ et $b$). Pour tirer $(a,b,\sigma)$ ensemble, on tire d'abord
$\sigma^2$, puis $(a,b)$ sachant ce $\sigma^2$ : c'est la règle $p(a,b,\sigma^2)=p(\sigma^2)\,p(a,b\mid\sigma^2)$. Enfin,
on rejette les tirages où $b<0$.

**Prédiction par Monte-Carlo.** Pour une année future de CO2 $C$, on tire $N=10\,000$ jeux $(a^{(k)},b^{(k)},\sigma^{(k)})$
et, pour chacun, **une** température :
$$T^{(k)}=a^{(k)}+b^{(k)}\ln C+\sigma^{(k)}z^{(k)},\qquad z^{(k)}\sim\mathcal N(0,1).$$
Exemple avec trois vrais tirages pour 2100 et SSP5-8.5 ($\ln C = 6{,}85$) :

| $k$ | $\sigma$ | $a$ | $b$ | droite en 2100 | bruit $z$ | Tmax 2100 |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | 1,89 | −12,5 | 6,47 | 31,8 °C | −0,45 | 31,0 °C |
| 2 | 2,23 | −21,4 | 7,97 | 33,2 °C | +3,32 | 40,6 °C |
| 3 | 2,16 | −22,1 | 8,08 | 33,3 °C | −1,06 | 31,1 °C |

Les 10 000 valeurs de la dernière colonne forment la loi de Tmax en 2100, et $P(\text{Tmax}>40\,°\text{C})$ est la part
de tirages au-dessus de 40 °C. La loi contient deux hasards : la météo de l'année ($\sigma z$), et notre incertitude sur
la droite, qui change à chaque tirage grâce au bayésien. Sans le bayésien, la droite en 2100 vaudrait toujours
32,8 °C, la loi serait plus étroite et la probabilité de dépasser 40 °C tomberait d'environ 1,6 % à 0,05 %.
'''

MODELES = r'''
N = 10_000                          # nombre de tirages Monte-Carlo par année
x = np.log(y['co2'].to_numpy())     # variable explicative : ln(CO2)

def ajuster(x, t):
    # tout ce qu'il faut pour tirer dans la loi a posteriori de (a, b, sigma)
    X = np.c_[np.ones_like(x), x]
    V = np.linalg.inv(X.T @ X)
    beta = V @ X.T @ t                       # moindres carrés
    mse = np.mean((t - X @ beta) ** 2)        # erreur quadratique moyenne de la droite
    return beta, V, mse, len(t)

def tirer(modele, x_futur, n=N, seed=0):
    rng = np.random.default_rng(seed)
    # n tirages de la température pour chaque valeur de x_futur : tableau (n, nombre d'années)
    beta, V, mse, n_annees = modele
    params = np.empty((0, 3))
    while len(params) < n:                   # on tire jusqu'à avoir n jeux de paramètres avec b >= 0
        s = np.sqrt(n_annees * mse / rng.chisquare(n_annees - 2, n))      # sigma (loi du chi2)
        ab = beta + s[:, None] * rng.standard_normal((n, 2)) @ np.linalg.cholesky(V).T   # (a, b) sachant sigma
        garder = ab[:, 1] >= 0               # rejet : plus de CO2 ne refroidit pas
        params = np.vstack([params, np.c_[ab[garder], s[garder]]])
    a, b, s = params[:n].T
    return a[:, None] + b[:, None] * x_futur + s[:, None] * rng.standard_normal((n, len(x_futur)))

def crps(tirages, obs):
    # CRPS moyen (°C) entre les tirages (n, nombre d'années) et les valeurs observées
    s = np.sort(tirages, axis=0)
    n = len(s)
    w = (2 * np.arange(1, n + 1) - n - 1) / n**2
    return np.mean(np.abs(s - obs).mean(axis=0) - w @ s)
'''

COMPARAISON = r'''
# on refait le test du groupe : appris sur 1940-2000, noté sur 2001-2025
avant, apres = (y['annee'] <= 2000).to_numpy(), (y['annee'] > 2000).to_numpy()
for var in ['max', 'min']:
    m = ajuster(x[avant], y[var].to_numpy()[avant])
    print(f'CRPS T{var} 2001-2025 : {crps(tirer(m, x[apres]), y[var].to_numpy()[apres]):.2f} °C')
'''

DIFFUSION_MD = diffusion_etude.INTRO
DIFFUSION = diffusion_etude.CODE_MODELE
PROJ_MD = diffusion_etude.PROJECTION_MD
PROJ = diffusion_etude.CODE_PROJECTION
DIST = diffusion_etude.CODE_DISTRIBUTION

MINIMA = diffusion_etude.CODE_MINIMA

# ------------------------------------------------------------------ assemblage
prof = json.loads(PROF.read_text(encoding='utf-8'))
todo = iter([
    [code(SAISON), com('saison')],
    [code(VAGUES), com('vagues')],
    [code(NUAGE), com('nuage')],
    [code(TMAX), com('tmax')],
    [code(CORREL), com('correl')],
    [md(METHODE), code(MODELES), code(COMPARAISON), com('comparaison'),
     md(DIFFUSION_MD + '\n\n' + diffusion_etude.PROTOCOLE + '\n\n' + diffusion_etude.EXECUTION_MD),
     code(DIFFUSION), code(diffusion_etude.CODE_EXECUTION),
     md(diffusion_etude.EXECUTION_COMMENTAIRE), md(PROJ_MD), code(PROJ), com('proj')],
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
    elif c['cell_type'] == 'code':
        cells.append(code(src))
    else:
        cells.append(c)
nb = {**prof, 'nbformat': 4, 'nbformat_minor': 5, 'cells': cells,
      'metadata': {'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'},
                   'donnees_locales': {'fichiers': list(EMPREINTES_CSV), 'sha256_lf': EMPREINTES_CSV},
                   'language_info': {'name': 'python'}}}
for i, cellule in enumerate(cells):
    cellule['id'] = f'cellule-{i:03d}'
SORTIE.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding='utf-8')
print('écrit :', SORTIE)
