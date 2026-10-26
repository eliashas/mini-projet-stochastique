import time
import numpy as np
import pandas as pd
from scipy.stats import beta
from .utils import ROOT,read_json,write_json,sha256,event
from .data import load_full,SCENARIOS
from .anchor import predict_anchor
from .experiments import ensemble_residuals,reconstruct


def binomial_interval(k,n,level=.95):
    alpha=1-level
    return [0. if k==0 else float(beta.ppf(alpha/2,k,n-k+1)),1. if k==n else float(beta.ppf(1-alpha/2,k+1,n-k))]


def project_full(config):
    tick=time.perf_counter(); out=ROOT/'artifacts'/'full_project'
    fits=read_json(out/'fit_full.json'); frames=load_full(config)
    years=frames['yearly_future_co2'].valid_time.dt.year.to_numpy(); future=frames['yearly_future_co2'][list(SCENARIOS)].to_numpy().T
    ensembles={}; rows=[]; probs=[]; trajectories=[]
    for var in ('max','min'):
        bundle=next(iter(fits['models'][var].values())); seed=config['seed_inference']+40000+1000*(var=='min')
        res=ensemble_residuals(bundle,config,seed,n=config['projection_samples'])
        # Tirages communs entre scénarios pour comparer les lois marginales.
        pred=reconstruct(bundle,future.ravel(),res,seed+30000).reshape(3,75,len(res)); ensembles[var]=pred
        for s,scenario in enumerate(SCENARIOS):
            for i,year in enumerate(years):
                vals=pred[s,i]; q=np.quantile(vals,[.05,.1,.25,.5,.75,.9,.95])
                threshold=fits['thresholds'][var]
                event_probability=float(np.mean(vals>threshold) if var=='max' else np.mean(vals<threshold))
                rows.append({'variable':var,'model':bundle['model'],'scenario':scenario,'year':year,'co2':future[s,i],'mean':float(vals.mean()),'std':float(vals.std()),'q05':q[0],'q10':q[1],'q25':q[2],'q50':q[3],'q75':q[4],'q90':q[5],'q95':q[6],'p_above40':float(np.mean(vals>40)) if var=='max' else None,'event_threshold_C':threshold,'event_probability':event_probability,'event_definition':'Tmax > quantile 80% historique 1940–2025' if var=='max' else 'Tmin < quantile 20% historique 1940–2025','n':len(vals)})
        if var!='max': continue
        n=config['probability_mc_samples']; iid=ensemble_residuals(bundle,config,seed+100000,n=n,iid_mixture=True)
        vals=reconstruct(bundle,future[:,-1],iid,seed+110000)
        for s,scenario in enumerate(SCENARIOS):
            k=int(np.sum(vals[s]>40)); ci=binomial_interval(k,n)
            probs.append({'model':bundle['model'],'scenario':scenario,'year':2100,'k':k,'n':n,'probability':k/n,'ci_lower':ci[0],'ci_upper':ci[1],'resolution':1/n,'interpretation':'aucun dépassement simulé' if k==0 else 'fréquence simulée conditionnelle au modèle','mixture_index_iid':True})
        n=config['trajectory_mc_samples']; rng=np.random.default_rng(seed+120000)
        if 'bootstrap' in bundle:
            boot=bundle['bootstrap']; idx=rng.integers(0,len(boot['a']),size=n)
            av=np.asarray(boot['a'])[idx]; bv=np.asarray(boot['b'])[idx]
        else:
            av=np.full(n,bundle['anchor']['a']); bv=np.full(n,bundle['anchor']['b'])
        ever=np.zeros((3,n),dtype=bool)
        for i,year in enumerate(years):
            # NOUVEAU résidu chaque année; indice réseau iid par simulation/année.
            residual=ensemble_residuals(bundle,config,seed+130000+int(i)*100,n=n,iid_mixture=True)
            annual=av[None,:]+bv[None,:]*np.log(future[:,i])[:,None]+residual[None,:]
            ever|=annual>40
        for s,scenario in enumerate(SCENARIOS):
            k=int(ever[s].sum()); ci=binomial_interval(k,n)
            trajectories.append({'model':bundle['model'],'scenario':scenario,'start_year':2026,'end_year':2100,'k':k,'n':n,'probability':k/n,'ci_lower':ci[0],'ci_upper':ci[1],'residual_assumption':'indépendance conditionnelle entre années','anchor_shared_over_trajectory':True})
    out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'projections.npz',**ensembles,years=years,scenarios=np.asarray(SCENARIOS),co2=future)
    pd.DataFrame(rows).to_csv(out/'projection_summary.csv',index=False)
    pd.DataFrame(probs).to_csv(out/'probability_40.csv',index=False)
    pd.DataFrame(trajectories).to_csv(out/'trajectory_probability_40.csv',index=False)
    last=float(frames['yearly_temp_brest'].iloc[-1].co2)
    transition={'historical_2025_co2':last,'scenario_2026_co2':dict(zip(SCENARIOS,future[:,0].tolist())),'difference_ppm':dict(zip(SCENARIOS,(future[:,0]-last).tolist())),'scenario_2100_co2':dict(zip(SCENARIOS,future[:,-1].tolist())),'trajectories_changed':False,'interpretation':'CO₂ fourni de tendance, non une observation causale locale complète; rupture conservée telle quelle.'}
    write_json(out/'co2_transition.json',transition)
    write_json(out/'projection_manifest.json',{'training_years':fits['training_years'],'models':{v:next(iter(fits['models'][v])) for v in ('max','min')},'ensembles_sha256':sha256(out/'projections.npz'),'units':'°C','samples':config['projection_samples'],'mc_samples':config['probability_mc_samples'],'trajectory_samples':config['trajectory_mc_samples'],'mixture_iid_for_binomial':True,'conditional_mc_uncertainty_only':True,'seed':config['seed_inference']+40000,'wall_seconds':time.perf_counter()-tick})
    event('full_project','projections_complete',wall_seconds=time.perf_counter()-tick,models={v:next(iter(fits['models'][v])) for v in ('max','min')})
    return rows
