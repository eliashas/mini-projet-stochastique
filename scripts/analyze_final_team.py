"""Figures, incertitudes et synthèse mesurées du rendu commun."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import beta, norm
from sma.heatwaves import analyze_heatwaves
from sma.final_models import predictive_sample, write_json, SCENARIOS
from sma.diagnostics import evaluate

OUT=ROOT/'rendu_final/resultats'
FIG=ROOT/'reports/final'
FIG.mkdir(parents=True,exist_ok=True)


def save(fig,name):
    fig.tight_layout()
    for ext in ('png','svg'):
        fig.savefig(FIG/f'{name}.{ext}',dpi=140,bbox_inches='tight')
    plt.close(fig)


def table(frame):
    # Pas de dépendance à tabulate pour les environnements neufs.
    d=frame.copy()
    for c in d.select_dtypes('number'):
        d[c]=d[c].map(lambda v:f'{v:.4f}')
    return '| '+' | '.join(d.columns)+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in d.itertuples(index=False,name=None))


def main():
    tick=time.perf_counter()
    train=pd.read_csv(ROOT/'rendu_final/data/yearly_temp_brest_train.csv')
    yearly=pd.read_csv(ROOT/'rendu_final/data/yearly_temp_brest.csv',parse_dates=['valid_time'])
    yearly['year']=yearly.valid_time.dt.year
    daily=pd.read_csv(ROOT/'rendu_final/data/daily_temp_brest.csv',parse_dates=['valid_time'])
    heat=analyze_heatwaves(daily,ROOT/'tmp/final_analysis/partie1','rendu_commun')
    for name in ['heatwave_climatology.csv','heatwave_events_min3.csv','heatwave_events_min2.csv','heatwave_counts_year.csv','heatwave_summary.json']:
        (OUT/name).write_bytes((ROOT/'tmp/final_analysis/partie1'/name).read_bytes())
    for name in ['heatwave_seasonal_cycle','heatwave_duration_intensity','heatwave_counts']:
        for ext in ['png','svg']:
            (FIG/f'{name}.{ext}').write_bytes((ROOT/'tmp/final_analysis/partie1'/f'{name}.{ext}').read_bytes())
    correlations=[]
    for period,frame in [('1940-2000',yearly[yearly.year<=2000]),('1940-2025',yearly)]:
        for v in ['max','min']:
            for method,y in [('T',frame[v]),('T_lisse_5ans',frame[v].rolling(5,center=True).mean()),('T_lisse_11ans',frame[v].rolling(11,center=True).mean()),('T_lisse_21ans',frame[v].rolling(21,center=True).mean())]:
                for name,x in [('CO2',frame.co2),('log_CO2',np.log(frame.co2)),('sqrt_CO2',np.sqrt(frame.co2))]:
                    correlations.append(dict(period=period,variable=v,temperature=method,co2=name,r=y.corr(x),n=int((y.notna()&x.notna()).sum())))
    pd.DataFrame(correlations).to_csv(OUT/'correlations.csv',index=False)
    selection=json.loads((OUT/'selection.json').read_text())
    val,test,years,checks=[pd.read_csv(OUT/f'{name}.csv') for name in ['validation','test','test_par_annee','controles_kit']]
    summary=val.merge(test,on=['variable','model'],suffixes=('_validation','_test'))
    summary=summary.merge(checks[['model','variable','monotonic','width_ok','bounds_ok']],on=['model','variable'])
    summary['admissible']=summary[['monotonic','width_ok','bounds_ok']].all(axis=1)
    for phase in ['validation','test']:
        for metric in ['crps','twcrps']:
            summary[f'rang_{metric}_{phase}']=summary.groupby('variable')[f'{metric}_{phase}'].rank(method='min')
    summary.to_csv(OUT/'comparaison_commune.csv',index=False)
    write_json(OUT/'comparaison_commune.json',summary.to_dict('records'))
    # Bootstrap apparié circulaire par blocs, sans supposer les années indépendantes.
    uncertainty=[]
    for var,first,second in [('max','D3','Bayes'),('max','D3','R_log'),('max','H1','Bayes'),('min','D1','Bayes')]:
        wide=years[(years.variable==var)&years.model.isin([first,second])].pivot(index='year',columns='model',values='crps')
        d=(wide[first]-wide[second]).to_numpy(); n=len(d)
        rng=np.random.default_rng(74102)
        starts=rng.integers(n,size=(4000,int(np.ceil(n/3))))
        indices=((starts[:,:,None]+np.arange(3))%n).reshape(4000,-1)[:,:n]
        means=d[indices].mean(1)
        uncertainty.append(dict(variable=var,model=first,reference=second,difference_C=d.mean(),
                                lower95_C=np.quantile(means,.025),upper95_C=np.quantile(means,.975),n_years=n,blocks=3,replicates=4000))
    pd.DataFrame(uncertainty).to_csv(OUT/'incertitude_ecarts_crps.csv',index=False)
    # Couverture : intervalle binomial indicatif, qui ignore la dépendance temporelle.
    coverage=[]
    for var in ['max','min']:
        for model in [selection['selected'][var],'Bayes']:
            s=years[(years.variable==var)&(years.model==model)]
            k=int(s.coverage80.sum()); n=len(s)
            low=0 if k==0 else beta.ppf(.025,k,n-k+1)
            high=1 if k==n else beta.ppf(.975,k+1,n-k)
            coverage.append(dict(variable=var,model=model,hits=k,n=n,coverage=k/n,lower95=low,upper95=high))
    pd.DataFrame(coverage).to_csv(OUT/'incertitude_couvertures.csv',index=False)
    probability=pd.read_csv(OUT/'probabilites.csv')
    probability['mc_lower95']=probability.apply(lambda r:0. if r.hits_2100==0 else beta.ppf(.025,r.hits_2100,r.n-r.hits_2100+1),axis=1)
    probability['mc_upper95']=probability.apply(lambda r:1. if r.hits_2100==r.n else beta.ppf(.975,r.hits_2100+1,r.n-r.hits_2100),axis=1)
    probability.to_csv(OUT/'probabilites_avec_mc.csv',index=False)
    # Incertitude purement numérique des CRPS, sans réentraînement ni sélection.
    mc=[]
    inputs=pd.read_csv(ROOT/'rendu_final/data/test_inputs.csv')
    truth=pd.read_csv(ROOT/'rendu_final/data/verite_2001_2025.csv')
    for var in ['max','min']:
        suite=json.loads((ROOT/f'rendu_final/modeles/historique/{var}/suite.json').read_text())
        for model in ['Bayes','D1','D3','H1']:
            for seed in range(94100,94105):
                samples=predictive_sample(suite,model,inputs.co2,root=ROOT,seed=seed)
                s=evaluate(samples,truth[var],suite['threshold'],var)['summary']
                mc.append(dict(variable=var,model=model,seed=seed,crps=s['crps'],twcrps=s['twcrps']))
    pd.DataFrame(mc).to_csv(OUT/'sensibilite_monte_carlo.csv',index=False)
    # Coûts : le temps historique attribué n'est pas un nouveau temps d'entraînement.
    costs=[]
    for path in (ROOT/'rendu_final/modeles').rglob('seed*.json'):
        record=json.loads(path.read_text()); costs.append(dict(**record['identity'],reused_historical=record['reused_historical'],
            training_seconds=record['training_seconds'],additional_seconds=record['additional_seconds'],device=record['device'],parameters=record['parameters']))
    costs=pd.DataFrame(costs);costs.to_csv(OUT/'couts_reseaux.csv',index=False)
    suite_rows=[]
    for path in (ROOT/'rendu_final/modeles').rglob('suite.json'):
        s=json.loads(path.read_text()); suite_rows.append(dict(phase=path.parents[1].name,variable=s['variable'],fit_wall_seconds=s['fit_wall_seconds'],
            h1_mean=s['h1_moments']['mean'],h1_std=s['h1_moments']['std'],gev_seconds=s.get('gev',{}).get('fit_seconds',0),
            gev_support=s.get('gev',{}).get('min_training_support'),gev_refused=s.get('gev',{}).get('rejected_updates',0)))
    pd.DataFrame(suite_rows).to_csv(OUT/'couts_et_normalisations.csv',index=False)
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    names=['R_log','R_linear','Bayes','Bayes0','GEV','Reda_min','QR_1','C0','D1','D2','D3','D4','H1']
    for i,var in enumerate(['max','min']):
        sub=summary[(summary.variable==var)&summary.model.isin(names)].sort_values('crps_validation')
        axes[i,0].plot(sub.crps_validation,sub.model,'o-',label='Validation 1971–2000')
        axes[i,0].plot(sub.crps_test,sub.model,'s-',label='Test 2001–2025 déjà consulté')
        axes[i,0].set(xlabel='CRPS global (°C)',title=f'{var.upper()} : mêmes distributions, mêmes années')
        axes[i,0].legend(fontsize=8);axes[i,0].grid(alpha=.2)
        axes[i,1].scatter(sub.crps_test,sub.twcrps_test)
        for r in sub.itertuples():axes[i,1].annotate(r.model,(r.crps_test,r.twcrps_test),xytext=(3,3),textcoords='offset points',fontsize=8)
        axes[i,1].set(xlabel='CRPS global test (°C)',ylabel='twCRPS test (°C)',title='La qualité globale et celle de la queue diffèrent')
        axes[i,1].grid(alpha=.2)
    save(fig,'comparaison_scores')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,var in zip(axes,['max','min']):
        sub=val[(val.variable==var)&val.model.str.startswith('H0_')].copy()
        sub['weight']=sub.model.str.split('_').str[-1].astype(float);sub=sub.sort_values('weight')
        ax.plot(sub.weight,sub.crps,'o-',label='CRPS global')
        ax.plot(sub.weight,sub.twcrps,'s-',label='twCRPS')
        ax.set(xlabel='Poids de Bayes dans H0',ylabel='Score validation (°C)',title=f'{var.upper()} : mélange des lois complètes')
        ax.legend();ax.grid(alpha=.2)
    save(fig,'melange_h0')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,var in zip(axes,['max','min']):
        for model in list(dict.fromkeys([selection['selected'][var],'Bayes','H1','QR_1'])):
            s=years[(years.variable==var)&(years.model==model)]
            ax.hist(s.pit,bins=np.linspace(0,1,6),histtype='step',label=model)
        ax.axhline(5,color='grey',ls='--');ax.set(xlabel='PIT',ylabel="Nombre d'années",title=f'{var.upper()}, 25 années : calibration indicative')
        ax.legend();ax.grid(alpha=.2)
    save(fig,'calibration_pit')
    fig,axes=plt.subplots(2,1,figsize=(11,7))
    projections=pd.read_csv(OUT/'projections.csv')
    colors=['#1b9e77','#d98b00','#c83e4d']
    for ax,var in zip(axes,['max','min']):
        ax.plot(yearly.year,yearly[var],'.-',color='#303030',lw=.8,ms=3,label='Historique fourni')
        for sc,color in zip(SCENARIOS,colors):
            s=projections[(projections.variable==var)&(projections.scenario==sc)]
            ax.plot(s.year,s.q50_C,color=color,label=sc.upper())
            ax.fill_between(s.year,s.q05_C,s.q95_C,color=color,alpha=.15)
        ax.set(xlabel='Année',ylabel='Température (°C)',title=f'{var.upper()} : {selection["selected"][var]}, médiane et intervalle 90 %')
        ax.legend(fontsize=8,ncol=2);ax.grid(alpha=.2)
    save(fig,'projections')
    # Les tableaux ci-dessous alimentent aussi les commentaires du notebook.
    selected_test=test[test.apply(lambda r:r.model==selection['selected'][r.variable],axis=1)]
    selected_probability=probability[probability.apply(lambda r:r.model==selection['selected'][r.variable],axis=1)]
    run=json.loads((OUT/'execution.json').read_text())
    report=f'''# Expériences complémentaires réellement exécutées

Le test 2001–2025 avait déjà été consulté avant cette intégration. Les résultats
ci-dessous sont exploratoires. Tous les réglages nouveaux ont utilisé les
validations 1971–2000 et les contrôles sans températures test.

## Décision et résultats

La validation retient **{selection['selected']['max']} pour Tmax** et
**{selection['selected']['min']} pour Tmin**. Aucun repli n'a été nécessaire après
les contrôles. Le benchmark original a renvoyé un résultat admissible :

{table(selected_test[['variable','model','crps','twcrps','coverage80','width80','bias']])}

Sur la validation, H0 préfère un poids bayésien de **0 pour les deux variables**.
Les composants choisis sont {selection['h0_components']}. Il n'y a donc pas de
gain du mélange retenu ; annoncer une fusion gagnante serait trompeur.
H1 est une combinaison modulaire, sans double comptage de l'échelle ou du bruit.

{table(summary[summary.model.isin(['Bayes','D1','D3','H1','GEV','Reda_min','QR_1','R_log','R_linear'])][['variable','model','crps_validation','twcrps_validation','crps_test','twcrps_test','admissible']])}

Bayes est meilleur en CRPS global test sur les maxima, alors que D3 est meilleur
en validation. D3 obtient un twCRPS Tmax inférieur à celui de Bayes sur ce test :
le classement dépend de la question évaluée. La sélection reste celle de la
validation. Les faibles écarts doivent être lus avec leur incertitude :

{table(pd.DataFrame(uncertainty))}

L'intervalle est un bootstrap apparié par blocs sur seulement 25 années ; il
ne corrige ni le choix de modèles après consultation historique du test ni
l'extrapolation en 2100. Le fichier `sensibilite_monte_carlo.csv` sépare la
variation des scores due aux tirages de cette incertitude d'échantillonnage.

## Ce que montrent les ablations

L'ancre linéaire en CO₂ ne dépasse pas l'ancre logarithmique sur les validations
Tmax (voir tableau), même si son test est légèrement meilleur. Cette observation
ne justifie pas un changement de tendance après test. Les QR peu pénalisées
extrapolent mal pour Tmin ; certaines perdent la monotonie et QR_0.01 sort des
bornes. Le bootstrap Tmin à pente libre de Reda échoue aussi en monotonie.
Les échecs sont dans `controles_kit.csv`, sans troncature des températures.

La GEV adaptée obtient un CRPS Tmax test différent du 1,66 °C annoncé par Reda.
L'estimation est recentrée et le support de vraisemblance est contrôlé ; les
tirages utilisent la graine commune. Les deux valeurs sont distinguées, sans
attribuer cet écart à une amélioration générale. Tous les supports finaux sont
positifs ; les mises à jour refusées sont tracées.

## Projections réajustées sur 1940–2025

{table(selected_probability[['variable','model','scenario','p_2100','hits_2100','mc_lower95','mc_upper95','p_at_least_one']])}

Pour Tmax la probabilité concerne 40 °C ; pour Tmin elle concerne le passage
sous 0 °C. Les bornes MC sont binomiales, conditionnelles à la loi simulée.
Un zéro sur 10 000 membres ne prouve pas une impossibilité. Le risque cumulé
suppose des innovations indépendantes conditionnellement aux paramètres, ces
paramètres restant communs aux 75 ans. Changer cette dépendance changerait le
risque cumulé sans nécessairement changer les probabilités annuelles.

`sensibilite_projections.csv` conserve Bayes, D1, D3, H1, l'ancre linéaire et
GEV/Reda_min. Les différences de loi et de tendance dominent souvent le petit
bruit Monte-Carlo. Les trois scénarios sont conditionnels : aucune probabilité
n'est attribuée au choix d'un SSP.

## Partie descriptive et coûts

La chronologie réelle donne {heat['events_min3']} épisodes d'au moins trois jours,
contre {heat['events_min2']} d'au moins deux jours. Durée maximale :
{heat['maximum_duration_min3_days']} jours ; intensité moyenne à q50 :
{heat['mean_intensity_min3_C']:.3f} °C. Le 29 février est conservé dans les séries
continues avec seuil interpolé. La climatologie complète sert à la description,
pas au choix des modèles annuels.

Durée de l'intégration numérique : {run['wall_seconds']:.1f} s sur
{run['gpu']}. Réseaux réutilisés : {int(costs.reused_historical.sum())} ;
nouveaux entraînements : {int((~costs.reused_historical).sum())}.
Les temps des checkpoints historiques sont des coûts attribués, pas des temps
à additionner une deuxième fois à l'exécution actuelle. Les réseaux D3/D4/H1
partagent D1/D2 et H0 partage ses composants. Les coûts par run, la GEV et les
normalisations H1 sont exportés séparément.

Le mode rapide recharge ces états et recalcule la description, les tirages,
les métriques de la sélection et les figures essentielles. Le mode réentraînement
reconstruit les familles et validations dans un autre dossier. Son résultat ne
remplace pas les résultats remis ; des versions ou matériels différents peuvent
modifier un arrêt précoce et de très faibles écarts de sélection.
'''
    controle_complet=OUT/'controle_projections_completes.csv'
    if controle_complet.exists():
        hors_bornes=pd.read_csv(controle_complet).query('outside_kit_bounds > 0')
        report+='\n## Contrôle après réajustement complet\n\n'+table(hors_bornes)+'\n\n'
        report+=("La GEV SSP5-8.5 comporte un tirage à 50,901 °C parmi 750 000 tirages annuels. "
                 "Il est conservé. Le contrôle historique sur 1940–2000 ne garantissait pas le comportement "
                 "après réajustement sur 1940–2025. Une borne GEV par composante n'est pas une borne physique à 50 °C. "
                 "Les ensembles complets D3/D1 retenus ne montrent aucune sortie de bornes.\n")
    (ROOT/'reports/experiences_complementaires.md').write_text(report,encoding='utf-8')
    write_json(OUT/'analyse_execution.json',dict(status='completed',seconds=time.perf_counter()-tick,heatwaves=heat,
                  reused_networks=int(costs.reused_historical.sum()),new_networks=int((~costs.reused_historical).sum())))
    print('Analyse, figures et rapport terminés',flush=True)


if __name__=='__main__':main()
