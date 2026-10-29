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
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch

rng = np.random.default_rng(0)   # graine fixée pour retrouver les mêmes résultats
plt.rcParams.update({'figure.figsize': (11, 4), 'axes.grid': True, 'grid.alpha': .3})
'''

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

Pour cette partie, nous avons organisé une petite compétition au sein du groupe : chaque membre a proposé et codé sa
propre méthode de prédiction probabiliste, puis toutes les méthodes ont été évaluées selon le même protocole. Seule la
meilleure selon ce protocole est présentée en détail dans la suite ; les autres sont résumées ci-dessous avec leur
score.

Le protocole est le suivant :

- entraînement sur les années **1940-2000** uniquement ;
- prédiction de chaque année **2001-2025** à partir de son CO2 (10 000 tirages par année) ;
- comparaison avec les températures observées à l'aide du **score CRPS** (défini plus bas).

Les années 2001-2025 ont des concentrations de CO2 plus élevées que toutes celles de l'entraînement. Ce test reproduit
donc, à petite échelle, la difficulté de 2100 : prédire pour un CO2 jamais observé.

### Les méthodes proposées

- **Référence** (point de comparaison) : une droite en fonction de $\ln(\mathrm{CO_2})$, plus un bruit gaussien.
- **Régression bayésienne** (Christian) : la même droite, mais au lieu d'une seule pente, on tire des milliers de
  pentes possibles. La prédiction devient donc plus incertaine quand on s'éloigne des données.
- **Loi des valeurs extrêmes, GEV** (Reda) : la loi que donne la théorie pour le maximum d'un grand nombre de valeurs
  (ici, le maximum de toutes les températures de l'année). Le centre de la loi dépend du CO2. Pour Tmin, on applique la même
  méthode à $-T_{\min}$, car le minimum est le maximum des valeurs opposées.
- **Modèles de diffusion** (Elias) : le type de réseau suggéré par le sujet. Une droite en $\ln(\mathrm{CO_2})$ sert
  d'« ancre », et un réseau de neurones génère les écarts à cette droite par diffusion : il part d'un bruit pur et le
  « débruite » pour obtenir un tirage. Elias a testé plusieurs versions : un DDPM classique (abandonné, car il
  produisait des valeurs absurdes pour Tmin, jusqu'à −1 933 °C), une diffusion entraînée au CRPS, et la même avec une
  ancre incertaine (la droite elle-même est tirée au hasard).
- **Régression quantile** (Yazid) : au lieu de supposer une loi, on ajuste 99 droites, une par quantile (1 %, 2 %, …,
  99 %).
- **Réseau à mélange de gaussiennes** (Diae) : un réseau de neurones qui donne, pour chaque valeur du CO2, un mélange
  de 3 lois normales (leurs poids, moyennes et écarts-types).

### Le score : le CRPS

Nos méthodes ne donnent pas une valeur mais une loi, donc l'erreur habituelle $|\text{prédiction} - \text{observation}|$
ne suffit pas. Le CRPS compare toute la loi prédite $F$ à la valeur observée $y$ :
$$\mathrm{CRPS}(F,y)=\mathbb E|X-y|-\tfrac12\,\mathbb E|X-X'|$$
où $X$ et $X'$ sont deux tirages faits au hasard dans notre loi prédite, l'un indépendamment de l'autre.

- Le premier terme est la distance moyenne entre nos tirages et la réalité : il est petit si la loi est bien centrée.
- Le second terme mesure la largeur de notre loi. Sans lui, le meilleur choix serait de toujours prédire une seule
  valeur ; avec lui, une loi qui a la bonne largeur est récompensée.

On calcule le CRPS pour chacune des 25 années de 2001-2025, puis on fait la moyenne : c'est ce score moyen qui
figure dans le tableau. Il est en °C et plus il est petit, mieux c'est. Pour une prédiction à une seule valeur, il
redonne l'erreur absolue.

### Résultats sur 2001-2025

| Méthode | Proposée par | CRPS Tmax (°C) | CRPS Tmin (°C) |
|:--|:--|:-:|:-:|
| **Régression bayésienne** | Christian | **1,57** | **0,98** |
| Diffusion avec ancre incertaine | Elias | 1,65 | 0,99 |
| Loi des valeurs extrêmes (GEV) | Reda | 1,68 | 0,99 |
| Référence | — | 1,70 | 1,14 |
| Diffusion entraînée au CRPS | Elias | 1,70 | 1,03 |
| Régression quantile | Yazid | 1,81 | 1,07 |
| Réseau à mélange de gaussiennes | Diae | 1,85 | 1,18 |

Les scores d'Elias viennent de son propre code (entraîné sur GPU) ; les autres ont été recalculés avec le même
protocole. Ils dépendent un peu du tirage aléatoire (environ ±0,03 °C d'une exécution à l'autre). La régression
bayésienne a le meilleur CRPS pour Tmax. Pour Tmin, elle est pratiquement à égalité avec la GEV et la diffusion avec
ancre (0,98 à 0,99) : on garde alors la régression bayésienne, plus simple, ce qui permet aussi d'utiliser le même
modèle pour Tmax et Tmin. Avec seulement 61 années pour apprendre, les réseaux de neurones ne font donc pas mieux
qu'une méthode simple. On remarque aussi que la meilleure version de la diffusion est celle où la droite est
incertaine : c'est la même idée que la régression bayésienne, et c'est ce qui l'améliore le plus.

Attention, « meilleur » veut dire ici meilleur CRPS sur 2001-2025, pas meilleur modèle dans l'absolu. Le CRPS juge
toute la loi, mais surtout son centre : il dit peu de chose sur la queue de la loi, qui compte pour la question des
40 °C, et 25 années de test, c'est peu. C'est donc le critère qui nous paraît le plus raisonnable pour choisir, mais
d'autres choix restaient défendables (par exemple la GEV, faite pour les extrêmes, et très proche pour Tmin).

**Ce que donnent les méthodes en 2100.** Pour vérifier ce choix autrement qu'avec le CRPS, on a aussi regardé ce que
chaque méthode prédit pour Tmax en 2100 avec SSP5-8.5 (946 ppm), une fois réentraînée sur 1940-2025 :

| Méthode | Médiane (°C) | Intervalle 5-95 % (°C) | P(Tmax 2100 > 40 °C) | Problème |
|:--|:-:|:-:|:-:|:--|
| **Régression bayésienne** | 32,8 | 27,4 – 38,2 | 1,5 % | — |
| Diffusion avec ancre incertaine (Elias) | 32,5 | 26,7 – 39,0 | 3,0 % | — |
| Diffusion entraînée au CRPS (Elias) | 32,6 | 28,7 – 37,3 | 0,6 % | — |
| GEV (Reda) | 31,4 | 26,2 – 37,1 | 0,8 % | — |
| Référence | 32,8 | 29,2 – 36,4 | 0,01 % | trop sûre d'elle : une seule pente |
| Régression quantile (Yazid) | 31,7 | 26,6 – 44,0 | 6,8 % | les 99 droites s'écartent |
| Réseau à mélange (Diae) | 29,1 | 23,8 – 34,7 | 0,06 % | ne suit plus le CO2 |

Les modèles de diffusion d'Elias et la GEV donnent des projections proches de la nôtre (médiane de 31,4 à 32,8 °C).
Trois méthodes posent en revanche problème quand on extrapole. La régression quantile diverge : ses 99 droites ont
des pentes différentes et s'écartent loin des données, ce qui donne un quantile 95 % à 44 °C en 2100, 88 % de
chances de dépasser 40 °C au moins une fois d'ici 2100, et des Tmin jusqu'à −19 °C (le record est de −6,6 °C). Le
réseau de Diae sature : sa médiane reste bloquée vers 29 °C dès 2050, alors que le CO2 continue d'augmenter, car un
réseau de neurones ne sait pas extrapoler en dehors de ce qu'il a vu. Le DDPM d'Elias donnait, lui, des valeurs
absurdes pour Tmin. Enfin, la référence ne diverge pas, mais elle est trop confiante : avec une seule pente, elle
donne 0,01 % au lieu de 1,5 %. Le choix de la régression bayésienne est donc cohérent avec ce que les méthodes
prédisent pour 2100, et pas seulement avec le CRPS.

C'est la régression bayésienne qu'on développe dans la suite.

Une fois la méthode choisie, on la **réentraîne sur toutes les années 1940-2025** pour faire les prédictions jusqu'en
2100 : le test sur 2001-2025 servait seulement à choisir la méthode, et il vaut mieux utiliser toutes les données
disponibles pour prédire le futur.

## Le modèle retenu : régression bayésienne

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
est connu pour être logarithmique (chaque doublement du CO2 réchauffe d'à peu près la même quantité), et c'est le seul
choix qui reste réaliste en 2100.

**Pourquoi bayésien ?** Avec 86 années, on ne connaît pas $a$, $b$ et $\sigma$ exactement : la pente estimée vaut
environ $7{,}4 \pm 2{,}5$. Sur les CO2 observés, ça change peu de chose, mais à 946 ppm une petite erreur sur la pente
devient une grosse erreur sur la température. Au lieu de garder une seule droite (celle des moindres carrés), on met
une **loi de probabilité sur les paramètres**, qui dit quelles valeurs de $(a,b,\sigma)$ sont plausibles, et on en
tire **beaucoup**. On part d'un a priori non informatif, avec une seule contrainte : plus de CO2 ne refroidit pas.
$$p(a,b,\sigma^2)\propto\sigma^{-2}\,\mathbf 1_{b\ge0}.$$

**La loi a posteriori** (ce qu'on sait des paramètres après avoir vu les données). On note $X$ le tableau des données
(une colonne de 1 et une colonne $x_t$), $\hat\beta=(\hat a,\hat b)=(X^\top X)^{-1}X^\top T$ la droite des moindres carrés,
et $\mathrm{MSE}=\frac1n\sum_t(T_t-\hat a-\hat b\,x_t)^2$ l'erreur quadratique moyenne de cette droite. Pour ce modèle,
le résultat est classique :
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

def tirer(modele, x_futur, n=N):
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

PROJ = r'''
futur = yearly_future_co2.copy()
futur['annee'] = pd.to_datetime(futur['valid_time']).dt.year
SSP = {'ssp1-2.6': 'tab:green', 'ssp2-4.5': 'tab:orange', 'ssp5-8.5': 'tab:red'}

def projeter(var):
    # modèle réajusté sur 1940-2025, puis 10 000 tirages pour chaque année 2026-2100 et chaque scénario
    m = ajuster(x, y[var].to_numpy())
    return {s: tirer(m, np.log(futur[s].to_numpy())) for s in SSP}

def tracer(var, sims, seuil):
    plt.figure(figsize=(12, 4.5))
    plt.plot(y['annee'], y[var], 'k.-', lw=0.8, ms=4, label='Observations 1940-2025')
    for s, couleur in SSP.items():
        q5, q50, q95 = np.percentile(sims[s], [5, 50, 95], axis=0)
        plt.fill_between(futur['annee'], q5, q95, color=couleur, alpha=0.15)
        plt.plot(futur['annee'], q50, color=couleur, lw=2, label=f'{s.upper()} : médiane et intervalle 5-95 %')
    plt.axhline(seuil, color='grey', ls='--', lw=1)
    plt.xlabel('Année')
    plt.ylabel(f'T{var} annuelle (°C)')
    plt.title(f'Projections de la T{var} annuelle à Brest')
    plt.legend(loc='upper left', fontsize=8)
    plt.show()

sims_max = projeter('max')
tracer('max', sims_max, 40)
'''

DIST = r'''
def resume_2100(sims, seuil, au_dessus=True):
    lignes = {}
    for s, t in sims.items():
        depasse = t > seuil if au_dessus else t < seuil
        lignes[s.upper()] = {'CO2 2100 (ppm)': futur[s].iloc[-1],
                             **{f'q{p} 2100 (°C)': np.percentile(t[:, -1], p) for p in (5, 50, 95)},
                             f'P(T 2100 {">" if au_dessus else "<"} {seuil} °C)': depasse[:, -1].mean(),
                             'P(au moins une fois 2026-2100)': depasse.any(axis=1).mean()}
    return pd.DataFrame(lignes).T

plt.figure(figsize=(9, 4))
for s, couleur in SSP.items():
    plt.hist(sims_max[s][:, -1], np.arange(18, 46, 0.25), density=True, histtype='stepfilled', alpha=0.35,
             color=couleur, label=s.upper())
plt.axvline(40, color='grey', ls='--', label='40 °C')
plt.xlabel('Tmax annuelle en 2100 (°C)')
plt.ylabel('Densité de probabilité (1/°C)')
plt.title('Loi de la Tmax en 2100 (10 000 tirages)')
plt.legend()
plt.show()
print(resume_2100(sims_max, 40).round(4).to_string())
'''

MINIMA = r'''
# même étude que pour Tmax : d'abord les observations 1940-2025
plt.plot(y['annee'], y['min'], 'o-', ms=3, lw=1, color='tab:blue', label='Minimum annuel')
plt.plot(y['annee'], y['min'].rolling(11, center=True).mean(), lw=2.5, color='k', label='Moyenne glissante sur 11 ans')
plt.xlabel('Année')
plt.ylabel('Température (°C)')
plt.title('Température minimale annuelle à Brest (1940-2025)')
plt.legend()
plt.show()
print('Corrélation Tmin / ln(CO2) :', round(y['min'].corr(np.log(y['co2'])), 2))

# projections avec le même modèle, et seuil de 0 °C (le gel) au lieu de 40 °C
sims_min = projeter('min')
tracer('min', sims_min, 0)

plt.figure(figsize=(9, 4))
for s, couleur in SSP.items():
    plt.hist(sims_min[s][:, -1], np.arange(-10, 14, 0.25), density=True, histtype='stepfilled', alpha=0.35,
             color=couleur, label=s.upper())
plt.axvline(0, color='grey', ls='--', label='0 °C')
plt.xlabel('Tmin annuelle en 2100 (°C)')
plt.ylabel('Densité de probabilité (1/°C)')
plt.title('Loi de la Tmin en 2100 (10 000 tirages)')
plt.legend()
plt.show()
print(resume_2100(sims_min, 0, au_dessus=False).round(3).to_string())
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
