"""Matrice fixée de validation, ajustements finaux et prédictions avant vérité."""
from pathlib import Path
import time
import traceback
import numpy as np
import pandas as pd
from .utils import ROOT,write_json,read_json,fingerprint,sha256,event,environment,code_hash
from .data import load_competition,input_hashes,SCENARIOS
from .splits import temporal_folds
from .anchor import fit_anchor,predict_anchor,bootstrap_anchor
from .models import gaussian,empirical,gev
from .training import train_network
from .sampling import sample_network
from .diagnostics import evaluate

BASE_MODELS=['R0_gaussian','R1_gev','R2_empirical','D0_ddpm','C0_direct_crps','D1_ddm_crps','D2_ddm_tail','D3_ddm_anchor','D4_ddm_tail_anchor']
NEURAL_BASE=['D0_ddpm','C0_direct_crps','D1_ddm_crps']


def config_id(model,lam=None):
    return f'{model}_lambda{lam:g}' if model in ('D2_ddm_tail','D4_ddm_tail_anchor') else model


def parent_model(model):
    return {'D3_ddm_anchor':'D1_ddm_crps','D4_ddm_tail_anchor':'D2_ddm_tail'}.get(model,model)


def fit_statistical(model,train,var,config,out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    a=fit_anchor(train.co2,train[var]); threshold=float(train[var].quantile(.8 if var=='max' else .2))
    bundle={'model':model,'variable':var,'anchor':a,'threshold':threshold,'input_years':train.valid_time.dt.year.tolist()}
    if model=='R1_gev': bundle['gev']=gev.fit(a['residuals'],var)
    if model in ('D3_ddm_anchor','D4_ddm_tail_anchor'):
        bundle['bootstrap']=bootstrap_anchor(train.co2,train[var],B=config['anchor_bootstrap_replicates'],block_length=config['anchor_bootstrap_block_length'],seed=config['seed_bootstrap']+(0 if var=='max' else 100)+int(train.valid_time.dt.year.max()))
        bundle['bootstrap_sensitivity']=bootstrap_anchor(train.co2,train[var],B=config['anchor_bootstrap_replicates'],block_length=1,seed=config['seed_bootstrap']+10000+(0 if var=='max' else 100)+int(train.valid_time.dt.year.max()))
    write_json(out/'fit.json',bundle)
    return bundle


def draw_residuals(model,bundle,n,seed,checkpoint=None,config=None):
    rng=np.random.default_rng(seed)
    if model=='R0_gaussian': return gaussian.sample(bundle['anchor'],n,rng)
    if model=='R1_gev': return gev.sample(bundle['gev'],n,rng)
    if model=='R2_empirical': return empirical.sample(bundle['anchor'],n,rng)
    return bundle['anchor']['sigma']*sample_network(checkpoint,n,seed,device=config['device'],batch_size=config['sampling_batch_size'])


def reconstruct(bundle,co2,residuals,seed,bootstrap_length=3):
    co2=np.asarray(co2,dtype=float)
    if bundle['model'] in ('D3_ddm_anchor','D4_ddm_tail_anchor'):
        boot=bundle['bootstrap'] if bootstrap_length==3 else bundle['bootstrap_sensitivity']
        rng=np.random.default_rng(seed); idx=rng.integers(0,len(boot['a']),size=len(residuals))
        mu=np.asarray(boot['a'])[idx][None,:]+np.log(co2)[:,None]*np.asarray(boot['b'])[idx][None,:]
    else: mu=predict_anchor(bundle['anchor'],co2)[:,None]
    return mu+residuals[None,:]


def validation(config):
    out=ROOT/'artifacts'/'competition'; out.mkdir(parents=True,exist_ok=True)
    if (out/'test_truth_opened.json').exists() or (out/'benchmark_results.json').exists(): raise RuntimeError('Validation interdite après ouverture du test: créer une nouvelle étude indépendante')
    yearly=load_competition(config)['yearly_temp_brest_train']
    individual=[]; mixtures=[]; per_year=[]; run_records=[]; failures=[]; start=time.perf_counter()
    for fold,train,val in temporal_folds(yearly):
        for var in ('max','min'):
            anchor=fit_anchor(train.co2,train[var]); threshold=float(train[var].quantile(.8 if var=='max' else .2))
            fitdir=out/'validation'/'fits'/var/fold
            bundles={}
            for m in BASE_MODELS:
                try: bundles[m]=fit_statistical(m,train,var,config,fitdir/m)
                except Exception as exc:
                    failure={'phase':'validation','fold':fold,'variable':var,'model':m,'error':repr(exc),'traceback':traceback.format_exc()}; failures.append(failure); event('validation','failure',**{k:v for k,v in failure.items() if k!='phase'})
            trained={}
            for m,lam in [(m,None) for m in NEURAL_BASE]+[('D2_ddm_tail',l) for l in config['tail_lambda_grid']]:
                cid=config_id(m,lam); trained[cid]={}
                for seed in config['seed_train']:
                    run=out/'validation'/'runs'/var/fold/cid/f'seed{seed}'
                    c=dict(config,tail_lambda=lam or 0.)
                    try:
                        summary=train_network(m,anchor['z'],predict_anchor(anchor,train.co2),train[var].to_numpy(),anchor['sigma'],threshold,var,c,seed,run,validation={'co2':val.co2.to_numpy(),'y':val[var].to_numpy(),'mu':predict_anchor(anchor,val.co2)})
                        trained[cid][seed]=summary['checkpoint']
                        run_records.append({'fold':fold,'variable':var,'model':cid,'seed':seed,**summary})
                        event('validation','network_complete',fold=fold,variable=var,model=cid,seed=seed,best_step=summary['best_step'],training_seconds=summary['training_seconds'])
                        print(f"VALIDATE {fold} {var} {cid} seed{seed}: best_step={summary['best_step']} time={summary['training_seconds']:.1f}s",flush=True)
                    except Exception as exc:
                        failures.append({'phase':'validation','fold':fold,'variable':var,'model':cid,'seed':seed,'error':repr(exc),'traceback':traceback.format_exc()}); print(f'FAIL {fold} {var} {cid} seed{seed}: {exc}',flush=True)
            for m in BASE_MODELS:
                if m not in bundles: continue
                for lam in (config['tail_lambda_grid'] if m in ('D2_ddm_tail','D4_ddm_tail_anchor') else [None]):
                    cid=config_id(m,lam); parent=config_id(parent_model(m),lam)
                    bundle=bundles[m]; neural=not m.startswith('R')
                    seeds=config['seed_train'] if neural else ['stat']
                    samples=[]
                    for i,seed in enumerate(seeds):
                        if neural and seed not in trained.get(parent,{}): continue
                        tick=time.perf_counter(); inferseed=config['seed_inference']+int(fold[1:])*100+1000*(var=='min')+(i if neural else 0)
                        res=draw_residuals(m,bundle,10000,inferseed,trained[parent][seed] if neural else None,config)
                        pred=reconstruct(bundle,val.co2,res,inferseed+30000)
                        diag=evaluate(pred,val[var].to_numpy(),threshold,var,val.valid_time.dt.year.to_numpy())
                        row={'model':cid,'variable':var,'fold':fold,'seed':seed,'tail_lambda':lam or 0.,'inference_seconds':time.perf_counter()-tick,**diag['summary']}
                        individual.append(row); samples.append(res)
                    if len(samples)!=len(seeds): continue
                    combined=np.concatenate([s[:n] for s,n in zip(samples,config['mixture_counts'])]) if neural else samples[0]
                    pred=reconstruct(bundle,val.co2,combined,config['seed_inference']+int(fold[1:])*100+1000*(var=='min')+30000)
                    diag=evaluate(pred,val[var].to_numpy(),threshold,var,val.valid_time.dt.year.to_numpy())
                    mixtures.append({'model':cid,'variable':var,'fold':fold,'seed':'mixture' if neural else 'stat','tail_lambda':lam or 0.,**diag['summary']})
                    df=diag['per_year'].copy(); df['model']=cid; df['variable']=var; df['fold']=fold; per_year.append(df)
                    if m in ('D3_ddm_anchor','D4_ddm_tail_anchor'):
                        sensitivity=reconstruct(bundle,val.co2,combined,config['seed_inference']+int(fold[1:])*100+1000*(var=='min')+30000,1)
                        sm=evaluate(sensitivity,val[var].to_numpy(),threshold,var,val.valid_time.dt.year.to_numpy())
                        write_json(fitdir/cid/'block1_validation.json',sm['summary'])
            pd.DataFrame(individual).to_csv(out/'validation_individual.csv',index=False)
            pd.DataFrame(mixtures).to_csv(out/'validation_mixture.csv',index=False)
            pd.concat(per_year).to_csv(out/'validation_per_year.csv',index=False)
            write_json(out/'validation_runs.json',run_records); write_json(out/'failures.json',failures)
    metrics=[c for c in ('crps','twcrps','coverage50','coverage80','coverage90','width50','width80','width90','bias','median_mae','brier') if c in pd.DataFrame(mixtures)]
    df=pd.DataFrame(mixtures); summary=df.groupby(['variable','model'],as_index=False)[metrics].mean()
    counts=df.groupby(['variable','model']).fold.nunique().rename('fold_count').reset_index(); summary=summary.merge(counts,on=['variable','model'])
    summary.to_csv(out/'validation_summary.csv',index=False)
    write_json(out/'validation_timing.json',{'wall_seconds':time.perf_counter()-start,'neural_runs':len(run_records),'failures':len(failures),'config':config,'config_sha256':fingerprint(config),'inputs':input_hashes(config),'code_sha256':code_hash()})
    return summary


def select(config):
    out=ROOT/'artifacts'/'competition'
    if (out/'test_truth_opened.json').exists() or (out/'benchmark_results.json').exists(): raise RuntimeError('Sélection interdite après ouverture du test')
    summary=pd.read_csv(out/'validation_summary.csv'); runs=read_json(out/'validation_runs.json')
    result={'selected_models':{},'selected_tail_lambda':{},'final_steps':{},'ranking':{},'configuration':config,'configuration_sha256':fingerprint(config),'selection_criterion':'CRPS mélange 3 graines, 30 années; proximité <0.05 °C -> ordre de complexité prédéfini','truth_used':False,'input_hashes':input_hashes(config),'mixture_counts':config['mixture_counts'],'final_steps_rule':config['final_steps_rule'],'final_steps_aggregation':'Médiane des neuf best_step (3 folds × 3 graines) par objectif et variable; durée commune aux trois graines finales.'}
    for var in ('max','min'):
        sub=summary[(summary.variable==var)&(summary.fold_count==3)].copy()
        tail=sub[sub.model.str.startswith('D2_ddm_tail')].sort_values('crps')
        bestlambda=float(tail.iloc[0].model.split('lambda')[1]) if len(tail) else config['tail_lambda_grid'][0]
        result['selected_tail_lambda'][var]=bestlambda
        sub=sub[~sub.model.str.startswith(('D2_ddm_tail','D4_ddm_tail_anchor')) | sub.model.str.endswith(f'lambda{bestlambda:g}')]
        sub['base']=sub.model.str.split('_lambda').str[0]
        sub['complexity']=sub.base.map({m:i for i,m in enumerate(config['complexity_order'])})
        ordered=[]
        while len(sub):
            best=float(sub.crps.min()); group=sub[sub.crps<best+config['selection_tolerance']].sort_values(['complexity','crps'])
            ordered.extend(group.to_dict('records')); sub=sub.drop(group.index)
        result['ranking'][var]=ordered; result['selected_models'][var]=ordered[0]['base']; result['final_steps'][var]={}
        for cid in sorted(set(r['model'] for r in runs if r['variable']==var)):
            steps=[r['best_step'] for r in runs if r['variable']==var and r['model']==cid]
            result['final_steps'][var][cid]=int(np.median(steps))
    write_json(out/'selection.json',result); write_json(out/'selection_validation.json',result)
    event('competition','selection_locked',selection_sha256=sha256(out/'selection.json'),models=result['selected_models'])
    return result


def final_fit(config,selection,full=False):
    if not full and any((ROOT/'artifacts'/'competition'/name).exists() for name in ('test_truth_opened.json','benchmark_results.json')): raise RuntimeError('Ajustement compétition verrouillé après ouverture du test')
    if full:
        from .data import load_full
        train=load_full(config)['yearly_temp_brest']; phase='full_project'
    else: train=load_competition(config)['yearly_temp_brest_train']; phase='competition'
    out=ROOT/'artifacts'/phase; out.mkdir(parents=True,exist_ok=True)
    fitfile=out/('fit_full.json' if full else 'fit_final.json')
    if full: models=sorted(set(selection['selected_models'].values()))
    else: models=BASE_MODELS
    result={'phase':phase,'models':{},'thresholds':{},'training_years':train.valid_time.dt.year.tolist(),'selection_sha256':sha256(ROOT/'artifacts'/'competition'/'selection.json'),'failures':[]}
    for var in ('max','min'):
        result['models'][var]={}; result['thresholds'][var]=float(train[var].quantile(.8 if var=='max' else .2))
        needed=[selection['selected_models'][var]] if full else models
        for m in needed:
            lam=selection['selected_tail_lambda'][var] if m in ('D2_ddm_tail','D4_ddm_tail_anchor') else None
            dest=out/'final'/var/m; parent=parent_model(m)
            try:
                bundle=fit_statistical(m,train,var,config,dest)
                bundle['tail_lambda']=lam or 0.; bundle['checkpoints']=[]; bundle['runs']=[]
                if not m.startswith('R'):
                    cid=config_id(parent,lam); steps=selection['final_steps'][var][cid]
                    for seed in config['seed_train']:
                        run=out/'final'/var/parent/f'seed{seed}'
                        c=dict(config,tail_lambda=lam or 0.)
                        summary=train_network(parent,bundle['anchor']['z'],predict_anchor(bundle['anchor'],train.co2),train[var].to_numpy(),bundle['anchor']['sigma'],bundle['threshold'],var,c,seed,run,fixed_steps=steps)
                        bundle['checkpoints'].append(summary['checkpoint']); bundle['runs'].append(summary)
                        print(f'FIT {phase} {var} {m} seed{seed} {steps} steps',flush=True)
                result['models'][var][m]=bundle
            except Exception as exc:
                result['failures'].append({'model':m,'variable':var,'error':repr(exc),'traceback':traceback.format_exc()})
                event(phase,'final_fit_failure',model=m,variable=var,error=repr(exc))
            write_json(fitfile,result)
    return result


def ensemble_residuals(bundle,config,seed,n=10000,iid_mixture=False):
    model=bundle['model']
    if model.startswith('R'): return draw_residuals(model,bundle,n,seed,config=config)
    counts=config['mixture_counts'] if n==10000 and not iid_mixture else [n//3+(i<n%3) for i in range(3)]
    if iid_mixture:
        indices=np.random.default_rng(seed+9000).integers(0,3,size=n); result=np.empty(n)
        for i,checkpoint in enumerate(bundle['checkpoints']):
            ix=np.flatnonzero(indices==i)
            result[ix]=draw_residuals(model,bundle,len(ix),seed+i,checkpoint,config)
        return result
    return np.concatenate([draw_residuals(model,bundle,count,seed+i,checkpoint,config) for i,(checkpoint,count) in enumerate(zip(bundle['checkpoints'],counts))])


def predict_competition(config,selection):
    from .benchmark_adapter import check_predictions
    out=ROOT/'artifacts'/'competition'; fits=read_json(out/'fit_final.json'); data=load_competition(config)
    if (out/'test_truth_opened.json').exists() or (out/'benchmark_results.json').exists(): raise RuntimeError('Prédictions compétition verrouillées après ouverture du test')
    test=data['test_inputs']; future=data['yearly_future_co2']; co2=future.loc[future.valid_time.dt.year==2100,list(SCENARIOS)].to_numpy().ravel()
    pred_dir=out/'predictions'; pred_dir.mkdir(exist_ok=True)
    predictions=[]; checks={}; caches={}; timing=[]; phase_start=time.perf_counter()
    for var in ('max','min'):
        caches[var]={}
        for m,bundle in fits['models'][var].items():
            sample_start=time.perf_counter()
            import torch
            if torch.cuda.is_available() and config['device']!='cpu': torch.cuda.reset_peak_memory_stats()
            seed=config['seed_inference']+1000*(var=='min')
            res=ensemble_residuals(bundle,config,seed)
            caches[var][m]={'test':reconstruct(bundle,test.co2,res,seed+30000),'proj':reconstruct(bundle,co2,res,seed+30000)}
            timing.append({'variable':var,'model':m,'sample_and_reconstruction_seconds':time.perf_counter()-sample_start,'residual_samples':len(res),'test_rows':25,'projection_rows':3,'gpu_allocated_peak_bytes':torch.cuda.max_memory_allocated() if torch.cuda.is_available() and config['device']!='cpu' else 0,'gpu_reserved_peak_bytes':torch.cuda.max_memory_reserved() if torch.cuda.is_available() and config['device']!='cpu' else 0})
    # Reproduction EXACTE de l'exemple, 4 appels RNG ordonnés.
    rng=np.random.default_rng(0); exact={}
    for key,var,inputs in [('test_max','max',test.co2),('test_min','min',test.co2),('proj_max','max',co2),('proj_min','min',co2)]:
        anchor=fits['models'][var]['R0_gaussian']['anchor']
        exact[key]=predict_anchor(anchor,inputs)[:,None]+anchor['sigma']*rng.standard_normal((len(inputs),10000))
    def save(identifier,arrays,model_max,model_min):
        path=pred_dir/(identifier+'.npz'); np.savez_compressed(path,**arrays)
        chk=check_predictions(arrays); checks[identifier]=chk
        row={'id':identifier,'path':str(path.relative_to(ROOT)),'sha256':sha256(path),'models':{'max':model_max,'min':model_min},'checks':chk}
        predictions.append(row); return chk
    save('R0_exact',exact,'R0_gaussian','R0_gaussian')
    for m in BASE_MODELS:
        if not all(m in caches[v] for v in ('max','min')): continue
        arrays={'test_'+v:caches[v][m]['test'] for v in ('max','min')}|{'proj_'+v:caches[v][m]['proj'] for v in ('max','min')}
        save(m,arrays,m,m)
    # Fallback selon validation uniquement et contrôles sans vérité, séparément par variable.
    candidate_models={}
    for var in ('max','min'):
        for row in selection['ranking'][var]:
            m=row['base']
            if m not in caches[var]: continue
            arrays={'test_max':caches[var][m]['test'] if var=='max' else caches['max']['R0_gaussian']['test'],'proj_max':caches[var][m]['proj'] if var=='max' else caches['max']['R0_gaussian']['proj'],'test_min':caches[var][m]['test'] if var=='min' else caches['min']['R0_gaussian']['test'],'proj_min':caches[var][m]['proj'] if var=='min' else caches['min']['R0_gaussian']['proj']}
            check=check_predictions(arrays)['variables'][var]
            if check['monotonic'] and check['width_ok'] and check['bounds_ok']:
                candidate_models[var]=m; break
    if len(candidate_models)==2:
        arrays={'test_'+v:caches[v][candidate_models[v]]['test'] for v in ('max','min')}|{'proj_'+v:caches[v][candidate_models[v]]['proj'] for v in ('max','min')}
        save('participant',arrays,candidate_models['max'],candidate_models['min'])
        candidate='participant'; selection['validation_initial_models']=selection['selected_models']; selection['selected_models']=candidate_models
    else: candidate=None
    selection['candidate']=candidate; selection['prechecks_applied']=True
    write_json(out/'selection.json',selection); write_json(out/'prechecks.json',checks)
    hashes={}
    for var in fits['models'].values():
        for bundle in var.values():
            for cp in bundle['checkpoints']:
                path=(ROOT/Path(cp)).resolve(); hashes[str(path.relative_to(ROOT))]=sha256(path)
    manifest={'candidate':candidate,'selected_models':candidate_models,'predictions':predictions,'checkpoint_hashes':hashes,'selection_sha256':sha256(out/'selection.json'),'config':config,'config_sha256':fingerprint(config),'code_sha256':code_hash(),'thresholds':fits['thresholds'],'kit_sha256':sha256(Path(config['original_kit_dir'])/'kit.py'),'input_hashes':input_hashes(config),'test_years':test.valid_time.dt.year.tolist(),'scenarios':list(SCENARIOS),'units':'°C','test_truth_opened':False,'mixture_counts':config['mixture_counts'],'locked':True}
    write_json(out/'evaluation_manifest.json',manifest)
    # Snapshot exact du code exécuté, même sans historique Git initial.
    import zipfile
    with zipfile.ZipFile(out/'locked_source.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for folder in ('src','scripts','configs','tests'):
            for p in sorted((ROOT/folder).rglob('*')):
                if p.is_file() and p.suffix in ('.py','.yaml','.ps1'): z.write(p,p.relative_to(ROOT))
        for name in ('README.md','requirements.txt','pyproject.toml','PLAN_IMPLEMENTATION_MODELES_SMA.md'):
            z.write(ROOT/name,name)
    manifest['locked_source_sha256']=sha256(out/'locked_source.zip')
    manifest['selection_validation_sha256']=sha256(out/'selection_validation.json')
    write_json(out/'evaluation_manifest.json',manifest)
    write_json(pred_dir/'metadata.json',{'years':list(range(2001,2026)),'projection_year':2100,'scenarios':list(SCENARIOS),'co2_2100_ppm':dict(zip(SCENARIOS,co2.tolist())),'units':'°C','shared_draws_between_scenarios_by_export':{r['id']:r['id']!='R0_exact' for r in predictions},'R0_exact_draw_policy':'Quatre appels RNG indépendants dans l’ordre de l’exemple original ; résidus distincts entre scénarios.','other_exports_draw_policy':'Résidus et ancre bootstrap communs entre scénarios pour comparer les marginales.','shared_marginal_draws_are_not_trajectories':True})
    write_json(out/'prediction_timing.json',{'wall_seconds':time.perf_counter()-phase_start,'runs':timing,'includes_raw_npz_export_and_prechecks':True})
    event('competition','predictions_locked',manifest_sha256=sha256(out/'evaluation_manifest.json'),candidate=candidate,models=candidate_models)
    return manifest
