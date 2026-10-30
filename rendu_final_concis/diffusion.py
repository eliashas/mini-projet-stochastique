"""Cellules de l'étude de diffusion, insérées dans le notebook par build.py.

Le notebook reçoit le code des cellules : aucune importation de ce fichier
n'est nécessaire pour l'exécuter dans Colab.
"""

INTRO = r'''
## La diffusion : apprendre la distribution des fluctuations

Une température annuelle dépend d'une tendance climatique et des conditions météo de l'année. On conserve
une tendance simple et on confie au réseau la distribution des écarts à cette tendance :

$$T_t=a+b\ln C_t+e\,z_t,\qquad
z_t=\frac{T_t-a-b\ln C_t}{e}.$$

$C_t$ est la concentration en CO₂ (ppm), $T_t$ la température (°C) et $e$ l'écart-type des résidus (°C).
L'ancre $(a,b)$ est ajustée par moindres carrés, avec $b\geq0$. L'échelle $e$ est calculée sur les mêmes années.
Le résidu réduit $z_t$ est sans unité. **Le CO₂ agit par l'ancre** ; le réseau ne reçoit pas directement le CO₂.
On suppose donc que la forme de la distribution des fluctuations reste stable dans le futur. C'est une
hypothèse forte, particulièrement pour les extrêmes.

### Du résidu bruité à une distribution

Pendant l'entraînement, on choisit un résidu historique $z$ et on le mélange avec un bruit indépendant :

$$s\sim\mathcal U(0,1),\quad \varepsilon\sim\mathcal N(0,1),\qquad
u=(1-s)z+s\varepsilon.$$

À $s=0$, le réseau voit le vrai résidu ; à $s=1$, il ne voit que du bruit. Pour chaque couple $(u,s)$,
il propose $M=32$ résidus à l'aide de 32 variables aléatoires indépendantes :

$$\widehat z_m=g_\phi(u,s,\zeta_m),\qquad \zeta_m\overset{\mathrm{iid}}\sim\mathcal N(0,1).$$

Les 32 propositions partagent **le même résidu bruité et le même niveau de bruit**. On évalue leur distribution
face au vrai résidu. Une régression quadratique apprendrait surtout une moyenne conditionnelle ; le CRPS
permet d'apprendre aussi la dispersion. L'architecture est un petit MLP :

$$ (u,s,\zeta)\longrightarrow 32\ \mathrm{SiLU}\longrightarrow32\ \mathrm{SiLU}\longrightarrow\widehat z.$$

Cela représente **1 217 paramètres**. Pour générer une année future, on utilise $s=1$ : le vrai résidu n'est
plus une entrée. Un passage dans le réseau donne un tirage, puis on revient aux degrés Celsius avec l'ancre.

Cette adaptation reprend l'idée des **diffusions distributionnelles** de
[De Bortoli et al. (ICML, 2025)](https://proceedings.mlr.press/v267/de-bortoli25b.html), et l'entraînement
avec tâches de débruitage de [Park et al. (2026, prépublication)](https://arxiv.org/abs/2609.38632).
Elle conserve une génération en un passage au niveau de bruit maximal. Le DDPM classique apprend un bruit
et déroule une chaîne de débruitage ; c'est une autre variante, étudiée au début du projet.

### Fonction de coût et variante pour les extrêmes

Pour $M$ propositions de température $X_1,\ldots,X_M$ et une observation $y$, on utilise à l'entraînement :

$$\widehat S_\alpha(X,y)=\frac1M\sum_m|X_m-y|
-\left(\frac{\alpha}{M(M-1)}+\frac{1-\alpha}{M^2}\right)
\sum_{i<j}|X_i-X_j|,\qquad \alpha=0{,}95.$$

Ce mélange des estimateurs *fair* et empirique, appelé *almost fair CRPS*, limite l'effet du petit ensemble
d'entraînement. Il est utilisé dans [AIFS-CRPS (Lang et al., 2024)](https://arxiv.org/abs/2412.15832).
Pour évaluer les modèles, on garde le CRPS empirique usuel avec 10 000 tirages.

La variante pondérée ajoute un score sur la queue de distribution :

$$\mathcal L=\widehat S_{0.95}(X,T)+\lambda\widehat S_{0.95}(v(X),v(T)),\qquad
v(x)=\begin{cases}\max(x,h)&\text{pour Tmax},\\\min(x,h)&\text{pour Tmin}.\end{cases}$$

Le seuil $h$ est le quantile 80 % de Tmax, ou 20 % de Tmin, **calculé sur l'entraînement seulement**.
Le second terme est un *threshold-weighted CRPS* (twCRPS). Toutes les années contribuent, même celles qui
ne dépassent pas le seuil. Le poids $\lambda=0{,}5$ vient de la validation du projet ; il ne dépend pas du test.
Ce score répond à une question plus ciblée que le CRPS global : il n'est pas une meilleure métrique dans l'absolu.
La transformation par seuil est décrite dans la [documentation des scores pondérés](https://scoringrules.readthedocs.io/en/latest/weighted_scores.html).

### Incertitude de l'ancre

Pour les variantes avec ancre incertaine, on rééchantillonne les résidus historiques par blocs circulaires
de trois années, à CO₂ fixé, puis on réajuste 500 droites. Une température simulée devient :

$$T_t^{(k)}=a^{(k)}+b^{(k)}\ln C_t+e\,\widehat z_t^{(k)}.$$

La droite varie entre les trajectoires. Elle reste la même au fil des années d'une trajectoire.
Le réseau et l'échelle $e$ ne sont pas réajustés pour chaque droite : ce bootstrap représente l'incertitude
de la tendance, sans représenter toute l'incertitude sur les paramètres du réseau.
'''

PROTOCOLE = r'''
### Les variantes et leur validation

| Nom | Distribution des fluctuations | Ancre |
|:--|:--|:--|
| C0 | Générateur au CRPS, sans tâches de débruitage | Fixe |
| D0 | DDPM classique, 100 pas de débruitage | Fixe |
| D1 | Débruiteur stochastique au CRPS | Fixe |
| D2 | D1 avec le score supplémentaire sur les extrêmes | Fixe |
| D3 | Même réseau que D1 | Bootstrap |
| D4 | Même réseau que D2 | Bootstrap |

C0 sert à isoler l'apport des tâches de débruitage. D1/D2 isolent l'effet de la pondération des extrêmes ;
D1/D3 et D2/D4 isolent celui de l'ancre incertaine. D3 et D4 ne nécessitent pas de nouveau réseau.

Les expériences du projet utilisent trois découpages chronologiques :

| Entraînement | Validation |
|:--|:--|
| 1940–1970 | 1971–1980 |
| 1940–1980 | 1981–1990 |
| 1940–1990 | 1991–2000 |

À chaque découpage, l'ancre, l'échelle, les seuils et le bootstrap sont calculés uniquement sur l'entraînement.
Le score de validation est calculé **en mode génération**, à $s=1$, sans résidu de l'année à prédire.
Trois graines (0, 1, 2) sont utilisées, puis leurs tirages sont réunis dans un ensemble de 10 000 membres.
Les mêmes blocs de validation ont servi à régler les modèles et à les comparer : ce n'est pas une validation imbriquée.

Les tableaux suivants reprennent les expériences communes enregistrées dans le dépôt. Le test 2001–2025
avait déjà été consulté pendant le projet ; ses résultats sont donc une comparaison rétrospective.
La sélection enregistrée repose sur la validation : **D3 pour Tmax, D1 pour Tmin**.
Bayes obtient ensuite le meilleur CRPS global observé sur le test parmi ces méthodes.
'''

ARCHIVES_COMMENTAIRE = r'''
**Lecture des résultats.** Pour Tmax, ajouter l'incertitude de l'ancre à D1 fait passer le CRPS test d'environ
1,70 à 1,65 °C. L'amélioration apparaît aussi en validation. L'ajout du score sur les extrêmes change peu
les résultats : D4 et D3 sont très proches, et le twCRPS test de D4 est même légèrement moins bon.
Une pondération plus ciblée pendant l'apprentissage ne garantit donc pas un meilleur score sur d'autres années.

Sur Tmax, Bayes a le meilleur CRPS global test (1,58 °C), tandis que D3 a un twCRPS plus faible
(0,681 contre 0,693 °C). Son intervalle à 90 % contient 22 observations sur 25, contre 20 pour Bayes,
mais il est plus large. Avec 25 années, ces couvertures sont très incertaines : elles ne prouvent pas que
les modèles sont calibrés dans le futur. Pour Tmin, les variantes avec bootstrap ont un meilleur CRPS test,
alors que D1 était préférable en validation. On conserve cette distinction au lieu de choisir après coup.

**Le DDPM essayé n'a pas été retenu.** Dans la configuration testée, il a généré des Tmin allant jusqu'à
−1 933 °C. Ces tirages ont été conservés dans le diagnostic et le modèle a été écarté. Cet échec concerne
notre entraînement et notre configuration ; il ne démontre pas que les DDPM sont inadaptés à toute étude climatique.
'''

CODE_MODELE = r'''
import time

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
torch.set_num_threads(1)
print('Calcul sur :', torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU')
print('PyTorch :', torch.__version__)

def ancre(x, t):
    b = max(float(np.polyfit(x, t, 1)[0]), 0.0)
    return np.array([np.mean(t - b * x), b])

def bootstrap_ancre(x, t, seed=7100, B=500):
    ab = ancre(x, t)
    mu = ab[0] + ab[1] * x
    r = t - mu
    r = r - r.mean()
    hasard = np.random.default_rng(seed)
    n = len(t)
    droites = []
    for _ in range(B):
        debuts = hasard.integers(0, n, size=int(np.ceil(n / 3)))
        ix = ((debuts[:, None] + np.arange(3)) % n).ravel()[:n]
        droites.append(ancre(x, mu + r[ix]))
    return np.array(droites)

class Debruiteur(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.reseau = torch.nn.Sequential(
            torch.nn.Linear(3, 32), torch.nn.SiLU(),
            torch.nn.Linear(32, 32), torch.nn.SiLU(), torch.nn.Linear(32, 1))

    def forward(self, u, s, zeta):
        return self.reseau(torch.stack([u, s, zeta], dim=-1)).squeeze(-1)

def crps_entrainement(X, y, alpha=0.95):
    M = X.shape[1]
    X = X.sort(dim=1).values
    w = 2 * torch.arange(1, M + 1, device=X.device) - M - 1
    dispersion = (X * w).sum(1)
    return ((X - y[:, None]).abs().mean(1)
            - dispersion * (alpha / (M * (M - 1)) + (1 - alpha) / M**2)).mean()

@torch.no_grad()
def residus(g, n, seed):
    # Le découpage en lots limite la mémoire, même pour 75 années et 10 000 trajectoires.
    hasard = torch.Generator(device=device).manual_seed(seed)
    morceaux = []
    for debut in range(0, n, 4096):
        k = min(4096, n - debut)
        u = torch.randn(k, generator=hasard, device=device)
        zeta = torch.randn(k, generator=hasard, device=device)
        morceaux.append(g(u, torch.ones_like(u), zeta).cpu().numpy())
    return np.concatenate(morceaux).astype(np.float64)

def entrainer_diffusion(x, t, pas, variable='max', penalite=0.0, seed=0, validation=None):
    ab = ancre(x, t)
    mu = ab[0] + ab[1] * x
    e = max(float(np.std(t - mu, ddof=2)), 1e-6)
    seuil = float(np.quantile(t, 0.8 if variable == 'max' else 0.2))
    z = torch.tensor((t - mu) / e, dtype=torch.float32, device=device)
    mu_t = torch.tensor(mu, dtype=torch.float32, device=device)
    cible = torch.tensor(t, dtype=torch.float32, device=device)
    torch.manual_seed(seed)
    g = Debruiteur().to(device)
    opt = torch.optim.AdamW(g.parameters(), lr=1e-3, weight_decay=1e-4)
    hasard = torch.Generator(device=device).manual_seed(seed + 100003)
    historique, pertes = [], []
    debut = time.perf_counter()
    for etape in range(1, pas + 1):
        ix = torch.randint(len(z), (64,), generator=hasard, device=device)
        zb = z[ix]
        s = torch.rand(64, generator=hasard, device=device)
        bruit = torch.randn(64, generator=hasard, device=device)
        u = (1 - s) * zb + s * bruit
        zeta = torch.randn(64, 32, generator=hasard, device=device)
        propositions = g(u[:, None].expand(-1, 32), s[:, None].expand(-1, 32), zeta)
        X = mu_t[ix, None] + e * propositions   # coût en °C, comme dans les expériences originales
        perte = crps_entrainement(X, cible[ix])
        if penalite:
            v = torch.clamp_min if variable == 'max' else torch.clamp_max
            perte = perte + penalite * crps_entrainement(v(X, seuil), v(cible[ix], seuil))
        if not torch.isfinite(perte):
            raise FloatingPointError('Fonction de coût non finie')
        opt.zero_grad(set_to_none=True)
        perte.backward()
        torch.nn.utils.clip_grad_norm_(g.parameters(), 1.0, error_if_nonfinite=True)
        opt.step()
        pertes.append(float(perte.detach().cpu()))
        if etape % 250 == 0 or etape == pas:
            ligne = {'pas': etape, 'coût entraînement (°C)': np.mean(pertes)}
            if validation is not None:
                xv, tv = validation
                Z = residus(g, 4096, seed + 900001)
                tirages = ab[0] + ab[1] * xv + e * Z[:, None]
                ligne['CRPS validation (°C)'] = crps(tirages, tv)
            historique.append(ligne)
            pertes = []
    if device.type == 'cuda':
        torch.cuda.synchronize()
    return {'reseau': g.eval(), 'ancre': ab, 'e': e, 'seuil': seuil,
            'historique': pd.DataFrame(historique), 'secondes': time.perf_counter() - debut}

def entrainer_suite(x, t, pas, variable='max', penalite=0.0):
    membres = [entrainer_diffusion(x, t, pas, variable, penalite, seed) for seed in (0, 1, 2)]
    print(f'T{variable}, poids extrêmes {penalite:g} : 3 réseaux, '
          f'{sum(m["secondes"] for m in membres):.1f} s', flush=True)
    return {'membres': membres, 'droites': bootstrap_ancre(x, t)}

def tirer_diffusion(suite, x_futur, n=N, bootstrap=True, seed=8200):
    # Un réseau et une droite par trajectoire ; une innovation indépendante par année.
    ny = len(x_futur)
    effectifs = [n // 3 + (k < n % 3) for k in range(3)]
    fluctuations = np.concatenate([
        m['e'] * residus(m['reseau'], k * ny, seed + j).reshape(k, ny)
        for j, (m, k) in enumerate(zip(suite['membres'], effectifs))])
    if bootstrap:
        ix = np.random.default_rng(seed + 7100).integers(len(suite['droites']), size=n)
        a, b = suite['droites'][ix].T
    else:
        a, b = suite['membres'][0]['ancre']
    tirages = np.asarray(a).reshape(-1, 1) + np.asarray(b).reshape(-1, 1) * x_futur + fluctuations
    if not np.isfinite(tirages).all():
        raise FloatingPointError('Température simulée non finie')
    return tirages
'''

EXECUTION_MD = r'''
### Réexécution dans ce notebook

Le code suivant réentraîne D1 et D2 avec trois graines pour Tmax et Tmin. D3 et D4 utilisent ensuite les mêmes
réseaux avec le bootstrap. Les durées sont fixées à partir de la validation du projet : 1 250 / 750 mises à jour
pour D1 / D2 de Tmax, 1 500 / 1 250 pour Tmin. AdamW utilise un taux de $10^{-3}$, une pénalité sur les poids
de $10^{-4}$, des lots de 64 années rééchantillonnées et un gradient limité à une norme de 1.

La courbe ci-dessous est une réexécution sur le dernier découpage (1940–1990 / 1991–2000), avec une seule graine.
Elle sert à observer l'apprentissage ; elle ne change pas les réglages retenus. Le coût d'entraînement utilise
des résidus partiellement connus, tandis que la validation part d'un bruit pur : leurs valeurs ne se comparent
pas directement. Les scores de la réexécution peuvent varier avec le matériel, PyTorch et les tirages Monte-Carlo.
'''

CODE_EXECUTION = r'''
PAS = {'max': {'D1': 1250, 'D2': 750}, 'min': {'D1': 1500, 'D2': 1250}}

# Observation de l'apprentissage, sans utiliser les températures 2001–2025.
train_courbe = (y['annee'] <= 1990).to_numpy()
val_courbe = y['annee'].between(1991, 2000).to_numpy()
exemple = entrainer_diffusion(x[train_courbe], y['max'].to_numpy()[train_courbe], 2500,
                            validation=(x[val_courbe], y['max'].to_numpy()[val_courbe]))
h = exemple['historique']
fig, axes = plt.subplots(1, 2, figsize=(11, 3.4))
for ax, colonne in zip(axes, ['coût entraînement (°C)', 'CRPS validation (°C)']):
    ax.plot(h['pas'], h[colonne], 'o-', ms=3)
    ax.set(xlabel='Mises à jour', ylabel=colonne)
fig.suptitle('Tmax : entraînement 1940–1990, validation 1991–2000 (graine 0)')
plt.tight_layout()
plt.show()

# Réajustements sur 1940–2000, avec les durées déjà fixées.
suites_test = {}
for var in ['max', 'min']:
    for nom, poids in [('D1', 0.0), ('D2', 0.5)]:
        suites_test[var, nom] = entrainer_suite(x[avant], y[var].to_numpy()[avant], PAS[var][nom], var, poids)

def indicateurs(tirages, obs, seuil, variable):
    v = np.maximum if variable == 'max' else np.minimum
    q5, q95 = np.percentile(tirages, [5, 95], axis=0)
    return {'CRPS (°C)': crps(tirages, obs),
            'twCRPS (°C)': crps(v(tirages, seuil), v(obs, seuil)),
            'Couverture 90 %': np.mean((obs >= q5) & (obs <= q95)),
            'Largeur 90 % (°C)': np.mean(q95 - q5)}

predictions_test, lignes = {}, []
for var in ['max', 'min']:
    obs = y[var].to_numpy()[apres]
    seuil = np.quantile(y[var].to_numpy()[avant], 0.8 if var == 'max' else 0.2)
    for nom, parent, boot in [('D1', 'D1', False), ('D2', 'D2', False),
                              ('D3', 'D1', True), ('D4', 'D2', True)]:
        tirages = tirer_diffusion(suites_test[var, parent], x[apres], bootstrap=boot)
        predictions_test[var, nom] = tirages
        lignes.append({'Variable': 'T' + var, 'Modèle': nom, **indicateurs(tirages, obs, seuil, var)})
    bayes = tirer(ajuster(x[avant], y[var].to_numpy()[avant]), x[apres])
    predictions_test[var, 'Bayes'] = bayes
    lignes.append({'Variable': 'T' + var, 'Modèle': 'Bayes', **indicateurs(bayes, obs, seuil, var)})

scores_execution = pd.DataFrame(lignes).set_index(['Variable', 'Modèle'])
display(scores_execution.round(3))
'''

EXECUTION_COMMENTAIRE = r'''
Sur le dernier découpage, le coût d'entraînement descend d'environ 0,91 à 0,73 °C. Le CRPS de validation
atteint son minimum vers 500 mises à jour, puis remonte et fluctue. Continuer à réduire le coût d'entraînement
n'améliore donc pas forcément les prédictions. La durée de 1 250 mises à jour retenue pour Tmax vient de
l'ensemble des validations du projet, et non du seul minimum de cette courbe.

Les tableaux distinguent les résultats archivés de la réexécution qui vient d'être faite. Les modèles ont la même
architecture et les mêmes réglages, mais les derniers millièmes ne sont pas un objectif à reproduire sur tous les GPU.
L'apport du bootstrap et le classement des variantes se lisent avec la variabilité de l'apprentissage et les
25 observations disponibles. Un petit écart ne suffit pas à établir une supériorité générale.

La simplicité de Bayes est un avantage avec peu d'observations. Le nombre d'années peut contribuer à expliquer
l'écart avec les réseaux, mais cette expérience ne permet pas d'en isoler la cause. La diffusion reste utile ici
pour relâcher l'hypothèse de fluctuations gaussiennes et étudier la sensibilité des queues de distribution.
'''

PROJECTION_MD = r'''
## Projections jusqu'en 2100 : diffusion et régression bayésienne

On réajuste les modèles sur **1940–2025**, avec les réglages conservés : D3 pour Tmax et D1 pour Tmin.
On garde Bayes comme comparaison. Pour chaque scénario, on génère 10 000 trajectoires de 2026 à 2100.
Les traits montrent les médianes et les bandes les quantiles 5 % et 95 % des températures annuelles.

Dans une trajectoire de diffusion, on conserve le même réseau et, pour D3, la même droite ; les innovations
annuelles sont indépendantes. Pour Bayes, on conserve le même triplet $(a,b,\sigma)$ et on renouvelle le bruit
chaque année. Le risque cumulé « au moins une fois » dépend de cette hypothèse de dépendance temporelle.
Les bandes sont des intervalles prédictifs annuels : ce ne sont pas des intervalles sur la seule tendance moyenne.
'''

CODE_PROJECTION = r'''
futur = yearly_future_co2.copy()
futur['annee'] = pd.to_datetime(futur['valid_time']).dt.year
SSP = {'ssp1-2.6': 'tab:green', 'ssp2-4.5': 'tab:orange', 'ssp5-8.5': 'tab:red'}

# Les 3 réseaux de chaque variable sont réellement réentraînés sur les 86 années.
suites_futur = {var: entrainer_suite(x, y[var].to_numpy(), PAS[var]['D1'], var) for var in ['max', 'min']}

def projeter(var):
    m = ajuster(x, y[var].to_numpy())
    return {s: tirer(m, np.log(futur[s].to_numpy())) for s in SSP}

def projeter_diffusion(var):
    # Une même graine entre scénarios garde les mêmes hasards : seul le CO₂ change.
    return {s: tirer_diffusion(suites_futur[var], np.log(futur[s].to_numpy()), bootstrap=(var == 'max'))
            for s in SSP}

def tracer(var, comparaisons, seuil):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4), sharey=True)
    for ax, (nom, sims) in zip(axes, comparaisons.items()):
        ax.plot(y['annee'], y[var], 'k.', ms=3, label='Observations')
        for s, couleur in SSP.items():
            q5, q50, q95 = np.percentile(sims[s], [5, 50, 95], axis=0)
            ax.fill_between(futur['annee'], q5, q95, color=couleur, alpha=0.15)
            ax.plot(futur['annee'], q50, color=couleur, label=s.upper())
        ax.axhline(seuil, color='grey', ls='--', lw=1, label=f'{seuil} °C')
        ax.set(title=nom, xlabel='Année', ylabel=f'T{var} annuelle (°C)')
        ax.legend(fontsize=8)
    fig.suptitle(f'T{var} à Brest : médianes et intervalles prédictifs 5–95 %')
    plt.tight_layout()
    plt.show()

sims_max = projeter('max')
sims_diffusion = projeter_diffusion('max')
tracer('max', {'Diffusion D3': sims_diffusion, 'Bayes': sims_max}, 40)
'''

CODE_DISTRIBUTION = r'''
def resume_2100(comparaisons, seuil, au_dessus=True):
    lignes = []
    for nom, sims in comparaisons.items():
        for s, t in sims.items():
            depasse = t > seuil if au_dessus else t < seuil
            n = len(t)
            k_an, k_cum = int(depasse[:, -1].sum()), int(depasse.any(axis=1).sum())
            q5, med, q95 = np.percentile(t[:, -1], [5, 50, 95])
            lignes.append({'Modèle': nom, 'Scénario': s.upper(),
                           'q5 (°C)': q5, 'Médiane (°C)': med, 'q95 (°C)': q95,
                           'P en 2100 (%)': 100 * k_an / n,
                           'P au moins une fois (%)': 100 * k_cum / n,
                           'Tirages en 2100 / 10 000': k_an})
    return pd.DataFrame(lignes).set_index(['Modèle', 'Scénario'])

def comparer_distributions(var, comparaisons, seuil):
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.5), sharey=True)
    for ax, s in zip(axes, SSP):
        valeurs = np.concatenate([sims[s][:, -1] for sims in comparaisons.values()])
        bins = np.linspace(valeurs.min(), valeurs.max(), 65)
        for nom, sims in comparaisons.items():
            ax.hist(sims[s][:, -1], bins=bins, density=True, histtype='step', lw=1.7, label=nom)
        ax.axvline(seuil, color='grey', ls='--', label=f'{seuil} °C')
        ax.set(title=s.upper(), xlabel=f'T{var} annuelle en 2100 (°C)', ylabel='Densité (1/°C)')
        ax.legend(fontsize=8)
    plt.tight_layout()
    plt.show()

comparaisons_max = {'Diffusion D3': sims_diffusion, 'Bayes': sims_max}
comparer_distributions('max', comparaisons_max, 40)
resume_max = resume_2100(comparaisons_max, 40)
display(resume_max.round(3))

# À zéro dépassement, borne binomiale supérieure unilatérale à 95 % (erreur Monte-Carlo seule).
print(f'0 dépassement / {N:,} tirages : borne supérieure Monte-Carlo à 95 % ≈ '
      f'{100 * (1 - 0.05**(1 / N)):.3f} %, pour ce modèle.')
'''

CODE_MINIMA = r'''
plt.plot(y['annee'], y['min'], 'o-', ms=3, lw=1, color='tab:blue', label='Minimum annuel')
plt.plot(y['annee'], y['min'].rolling(11, center=True).mean(), lw=2.5, color='k',
         label='Moyenne glissante sur 11 ans')
plt.xlabel('Année')
plt.ylabel('Température (°C)')
plt.title('Température minimale annuelle à Brest (1940–2025)')
plt.legend()
plt.show()
print('Corrélation Tmin / ln(CO₂) :', round(np.corrcoef(y['min'], x)[0, 1], 2))

sims_min = projeter('min')
sims_min_diffusion = projeter_diffusion('min')
comparaisons_min = {'Diffusion D1': sims_min_diffusion, 'Bayes': sims_min}
tracer('min', comparaisons_min, 0)
comparer_distributions('min', comparaisons_min, 0)
resume_min = resume_2100(comparaisons_min, 0, au_dessus=False)
display(resume_min.round(3))

# Contrôle des tirages bruts, avant toute interprétation des probabilités.
controles = []
for variable, comparaisons, bornes in [('Tmax', comparaisons_max, (0, 50)),
                                      ('Tmin', comparaisons_min, (-30, 20))]:
    for nom, sims in comparaisons.items():
        t = np.concatenate(list(sims.values()), axis=1)
        assert np.isfinite(t).all(), 'Température simulée non finie'
        controles.append({'Variable': variable, 'Modèle': nom, 'Minimum brut (°C)': t.min(),
                          'Maximum brut (°C)': t.max(),
                          'Hors bornes de contrôle': int(((t < bornes[0]) | (t > bornes[1])).sum())})
print('Contrôle numérique des projections (bornes larges du protocole du groupe) :')
display(pd.DataFrame(controles).round(2))
'''


def cellule_archives(racine):
    """Petits tableaux inclus dans le notebook ; les 90 entraînements restent archivés."""
    import hashlib
    import pandas as pd

    noms = ['C0', 'D1', 'D2', 'D3', 'D4', 'Bayes']
    colonnes = ['variable', 'model', 'crps', 'twcrps', 'coverage90', 'width90']
    morceaux = []
    for phase in ['validation', 'test']:
        chemin = racine / 'rendu_final' / 'resultats' / (phase + '.csv')
        table = pd.read_csv(chemin)
        table = table[table['model'].isin(noms)][colonnes]
        csv = table.to_csv(index=False, lineterminator='\n')
        empreinte = hashlib.sha256(chemin.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        morceaux.append(f"# Source : rendu_final/resultats/{phase}.csv ; SHA-256 (LF) : {empreinte}\n"
                        f"{phase}_reference = pd.read_csv(io.StringIO('''{csv}'''))")
    morceaux.append(r'''
ordre = ['C0', 'D1', 'D2', 'D3', 'D4', 'Bayes']
for variable in ['max', 'min']:
    v = validation_reference.query('variable == @variable').set_index('model')
    t = test_reference.query('variable == @variable').set_index('model')
    tableau = pd.DataFrame({'CRPS validation (°C)': v['crps'], 'CRPS test (°C)': t['crps'],
                            'twCRPS test (°C)': t['twcrps'], 'Couverture 90 % test': t['coverage90'],
                            'Largeur 90 % test (°C)': t['width90']}).reindex(ordre)
    print('T' + variable + ' — expériences communes archivées')
    display(tableau.round(3))

# Chaque score est une moyenne sur des années, pas sur 10 000 observations indépendantes.
tmax = test_reference.query('variable == "max"').set_index('model').reindex(ordre)
fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
for ax, colonne, titre in zip(axes, ['crps', 'twcrps', 'coverage90'],
                             ['CRPS Tmax (°C)', 'twCRPS Tmax (°C)', 'Couverture de l’intervalle à 90 %']):
    ax.bar(ordre, tmax[colonne], color=['grey', 'tab:blue', 'tab:blue', 'tab:orange', 'tab:orange', 'tab:green'])
    ax.set_title(titre, fontsize=10)
    ax.set_xlabel('Modèle')
    if colonne == 'coverage90':
        ax.axhline(0.9, color='black', ls='--', lw=1)
        ax.set_ylim(0, 1.05)
    else:
        ax.set_ylabel('°C')
fig.suptitle('Test 2001–2025 : précision globale, queue chaude et couverture')
plt.tight_layout()
plt.show()
''')
    return '\n\n'.join(morceaux)
