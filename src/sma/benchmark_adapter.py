import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
from .utils import ROOT,sha256,read_json,write_json,event,fingerprint
from .scores import crps_rows

KEYS=('test_max','test_min','proj_max','proj_min')


def check_predictions(arrays):
    result={'admissible':True,'variables':{},'errors':[]}
    for v,lo,hi in [('max',0,50),('min',-30,20)]:
        t=np.asarray(arrays['test_'+v]); p=np.asarray(arrays['proj_'+v])
        if t.shape!=(25,10000) or p.shape!=(3,10000) or not np.isfinite(t).all() or not np.isfinite(p).all():
            result['admissible']=False; result['errors'].append(f'{v}: forme/finitude'); continue
        med=np.median(p,axis=1); width=np.diff(np.quantile(t,[.1,.9],axis=1),axis=0).mean(); future_width=float(np.diff(np.quantile(p[2],[.1,.9]))[0])
        monotonic=bool(med[0]<=med[1]+.1 and med[1]<=med[2]+.1)
        wide=bool(future_width>=.95*width)
        bounds=bool(min(t.min(),p.min())>=lo and max(t.max(),p.max())<=hi)
        metrics={'monotonic':monotonic,'width_ok':wide,'bounds_ok':bounds,'test_width80':float(width),'future_width80':future_width,'projection_medians':med.tolist(),'smallest':float(min(t.min(),p.min())),'largest':float(max(t.max(),p.max())),'outside_bounds':int(((t<lo)|(t>hi)).sum()+((p<lo)|(p>hi)).sum()),'non_degenerate':bool(np.std(t,axis=1).min()>1e-6)}
        result['variables'][v]=metrics
        if not(monotonic and wide and bounds): result['admissible']=False; result['errors'].append(f'{v}: '+', '.join(k for k,val in [('monotonie',monotonic),('largeur',wide),('bornes',bounds)] if not val))
    return result


def load_kit(path):
    spec=importlib.util.spec_from_file_location('sma_original_kit',Path(path)/'kit.py')
    kit=importlib.util.module_from_spec(spec); spec.loader.exec_module(kit)
    return kit


def run_benchmarks(config,manifest_path):
    """Unique entrée qui ouvre la vérité, après vérification des prédictions verrouillées."""
    manifest=read_json(manifest_path)
    out=ROOT/'artifacts'/'competition'
    if sha256(out/'selection.json')!=manifest['selection_sha256']: raise ValueError('Sélection modifiée après verrouillage')
    if sha256(out/'locked_source.zip')!=manifest['locked_source_sha256']: raise ValueError('Source archivée modifiée après verrouillage')
    if fingerprint(config)!=manifest['config_sha256']: raise ValueError('Configuration modifiée après verrouillage')
    from .data import input_hashes
    if input_hashes(config)!=manifest['input_hashes']: raise ValueError('Entrées modifiées après verrouillage')
    for row in manifest['predictions']:
        if sha256(ROOT/row['path'])!=row['sha256']: raise ValueError('Prédiction modifiée après verrouillage')
    for cp,h in manifest['checkpoint_hashes'].items():
        if sha256(ROOT/cp)!=h: raise ValueError('Checkpoint modifié après verrouillage')
    kitpath=Path(config['original_kit_dir'])
    if sha256(kitpath/'kit.py')!=manifest['kit_sha256']: raise ValueError('Kit original modifié')
    # Aucun modèle n'est ajusté ou choisi dans cette fonction.
    kit=load_kit(kitpath)
    write_json(out/'test_truth_opened.json',{'manifest_sha256':sha256(manifest_path),'phase':'test_truth_opening','never_unlock_after_partial_failure':True})
    event('competition','test_truth_opened',manifest_sha256=sha256(manifest_path))
    truth=pd.read_csv(kit.DATA/'verite_2001_2025.csv')
    if truth.annee.tolist()!=list(range(2001,2026)): raise ValueError('Vérité: ordre des années invalide')
    results=[]; diagnostics=[]; yearly=[]
    from .diagnostics import evaluate
    for row in manifest['predictions']:
        with np.load(ROOT/row['path']) as f: arrays={k:f[k] for k in KEYS}
        stdout=io.StringIO(); ret=None; error=None
        try:
            with contextlib.redirect_stdout(stdout): ret=kit.benchmark(**arrays)
        except Exception as exc: error=f'{type(exc).__name__}: {exc}'
        (out/'benchmark_stdout').mkdir(exist_ok=True)
        (out/'benchmark_stdout'/f"{row['id']}.txt").write_text(stdout.getvalue(),encoding='utf-8')
        scores={v:float(kit.crps(arrays['test_'+v],truth[v])) for v in ('max','min')}
        for v in ('max','min'):
            if not np.isclose(scores[v],crps_rows(arrays['test_'+v],truth[v]).mean(),atol=1e-12,rtol=0): raise AssertionError('CRPS local divergent du kit')
        checks=check_predictions(arrays)
        result={'id':row['id'],'scores':scores,'score_max':scores['max'],'score_min':scores['min'],'return':ret,'admissible':ret is not None,'status':'admissible' if ret is not None else 'elimine','checks':checks,'error':error,'stdout':stdout.getvalue(),'prediction_sha256':row['sha256']}
        results.append(result)
        for v in ('max','min'):
            metric=evaluate(arrays['test_'+v],truth[v].to_numpy(),manifest['thresholds'][v],v,truth.annee.to_numpy())
            summary={'model':row['id'],'variable':v,**metric['summary']}; diagnostics.append(summary)
            per=metric['per_year'].copy(); per['model']=row['id']; per['variable']=v; yearly.append(per)
    # Exécution réelle du script de référence original, seulement maintenant.
    original=subprocess.run([sys.executable,str(kitpath/'exemple.py')],cwd=kitpath,capture_output=True,text=True,encoding='utf-8',env={**__import__('os').environ,'PYTHONIOENCODING':'utf-8'})
    (out/'benchmark_stdout'/'exemple_original.txt').write_text(original.stdout+original.stderr,encoding='utf-8')
    results_blob={'manifest_sha256':sha256(manifest_path),'candidate':manifest['candidate'],'results':results,'original_example':{'exit_code':original.returncode,'stdout':original.stdout,'stderr':original.stderr},'truth_sha256':sha256(kit.DATA/'verite_2001_2025.csv'),'selection_unchanged':True}
    write_json(out/'benchmark_results.json',results_blob)
    pd.DataFrame(diagnostics).to_csv(out/'test_diagnostics.csv',index=False)
    pd.concat(yearly).to_csv(out/'test_per_year.csv',index=False)
    pd.DataFrame([{'model':r['id'],'crps_max':r['scores']['max'],'crps_min':r['scores']['min'],'admissible':r['admissible'],'errors':'; '.join(r['checks']['errors'])} for r in results]).to_csv(out/'benchmark_scores.csv',index=False)
    return results_blob
