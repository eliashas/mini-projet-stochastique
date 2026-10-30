"""Cellules de l'étude de diffusion, insérées dans le notebook par build.py.

Le notebook reçoit le code des cellules : aucune importation de ce fichier
n'est nécessaire pour l'exécuter dans Colab.
"""

INTRO = r'''
## La diffusion distributionnelle

**Notations.** On reprend $T_t$ (température annuelle, °C) et $C_t$ (CO₂, ppm). L'échelle $e$ est
l'écart-type des résidus de la droite, calculé sur l'entraînement. Le résidu réduit $z_t$ est sans unité.

**Le modèle.** On conserve la même tendance logarithmique, mais le réseau apprend la distribution des fluctuations :

$$T_t=a+b\ln C_t+e\,z_t,\qquad z_t=\frac{T_t-a-b\ln C_t}{e}.$$

Le CO₂ agit par l'ancre $(a,b)$, ajustée avec $b\geq0$. Le réseau ne reçoit pas directement le CO₂ :
on suppose que la distribution des fluctuations reste stable dans le futur.

**Pourquoi une diffusion ?** Une régression quadratique apprend surtout une moyenne. Ici, on cherche à générer
une distribution, dont la forme n'est pas imposée gaussienne. On entraîne un débruiteur stochastique à différents
niveaux de bruit, suivant les diffusions distributionnelles de
[De Bortoli et al. (2025)](https://proceedings.mlr.press/v267/de-bortoli25b.html) et
[Park et al. (2026, prépublication)](https://arxiv.org/abs/2609.38632).

**L'apprentissage.** Un résidu historique $z$ est mélangé à un bruit indépendant :

$$u=(1-s)z+s\varepsilon,\qquad s\sim\mathcal U(0,1),\quad\varepsilon\sim\mathcal N(0,1).$$

Le réseau propose $M=32$ résidus $\widehat z_m=g_\phi(u,s,\zeta_m)$, avec des $\zeta_m\sim\mathcal N(0,1)$
indépendants. Les propositions partagent le même $(u,s)$. On minimise leur CRPS face au vrai résidu,
après retour aux °C. L'estimateur d'entraînement mélange 95 % de CRPS *fair* et 5 % de CRPS empirique
(*almost fair*, [Lang et al., 2024](https://arxiv.org/abs/2412.15832)). L'architecture est un MLP
$3\to32\to32\to1$, avec activations SiLU, soit **1 217 paramètres**.

**Prédiction par Monte-Carlo.** Pour prédire, on prend $s=1$ : le réseau reçoit du bruit pur et produit un résidu
en un passage. La variante D3 ajoute l'incertitude de l'ancre : on rééchantillonne les résidus par blocs de trois
années, à CO₂ fixé, puis on réajuste 500 droites. Un tirage s'écrit :

$$T_t^{(k)}=a^{(k)}+b^{(k)}\ln C_t+e\,g_\phi(\varepsilon_t^{(k)},1,\zeta_t^{(k)}).$$

Une trajectoire conserve sa droite et son réseau, avec de nouveaux bruits chaque année. Le bootstrap ne
réajuste pas le réseau : il représente seulement l'incertitude sur la tendance.

**Variantes.** On compare quatre versions du même débruiteur :

| Variante | Coût d'apprentissage | Ancre |
|:--|:--|:--|
| D1 | CRPS | Fixe |
| D2 | CRPS + $0{,}5\,\mathrm{twCRPS}$ | Fixe |
| D3 | CRPS | Bootstrap |
| D4 | CRPS + $0{,}5\,\mathrm{twCRPS}$ | Bootstrap |

Le twCRPS est le CRPS après transformation $v(x)=\max(x,h)$ pour Tmax, ou $\min(x,h)$ pour Tmin.
Le seuil $h$ est le quantile 80 % / 20 % calculé sur l'entraînement. Toutes les années contribuent.
Cette pondération cible les extrêmes ; le CRPS global reste le critère principal.
'''

PROTOCOLE = r'''
**Validation.** On entraîne jusqu'en 1970, 1980 et 1990, puis on valide sur les dix années suivantes,
avec trois graines (0, 1, 2). L'ancre, l'échelle et les seuils sont réajustés dans chaque entraînement.
La sélection enregistrée est D3 pour Tmax et D1 pour Tmin ; les résultats communs figurent dans le tableau précédent.

Deux essais supplémentaires sont conservés dans les expériences détaillées : C0, générateur sans débruitage,
et un DDPM classique. Ce dernier a été écarté après des Tmin allant jusqu'à −1 933 °C dans la configuration testée.
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
**Entraînement.** Le code utilise PyTorch sur GPU si disponible, AdamW ($10^{-3}$), des lots de 64 et
32 propositions par observation. Les durées sont fixées par la validation : D1/D2, 1 250/750 mises à jour
pour Tmax et 1 500/1 250 pour Tmin. La courbe du dernier découpage sert uniquement de diagnostic.
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
**Commentaire.** Le coût d'entraînement baisse, mais le CRPS de validation remonte après environ
500 mises à jour : entraîner plus longtemps n'améliore pas forcément les prédictions. Ces deux scores
correspondent à des tâches différentes, débruitage et génération depuis un bruit pur.

Pour Tmax, le bootstrap améliore le CRPS d'environ 1,70 à 1,65 °C. La pondération des extrêmes apporte peu
ici. Bayes garde le meilleur CRPS global test ; les écarts restent à interpréter avec seulement 25 années.
'''

PROJECTION_MD = r'''
## Projections jusqu'en 2100 : régression bayésienne et diffusion

La régression bayésienne et la diffusion sont réajustées sur **1940–2025**. Pour la diffusion, on conserve
les variantes retenues sur validation : D3 pour Tmax et D1 pour Tmin. Chaque méthode génère
10 000 trajectoires de 2026 à 2100 pour chacun des trois scénarios.
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
